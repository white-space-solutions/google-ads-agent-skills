"""Restore negative lists and campaign-level negatives from a backup. DRY RUN by default.

Recreates every enabled list with its terms, reattaches it to the same (still existing) campaigns,
and re-adds missing campaign-level negatives. A list whose name already exists is reused.

  python scripts/negatives_restore.py --client clients/acme.yaml --backup work/acme/backups/negatives-YYYYMMDD-HHMMSS
  APPLY_ENABLED=1 python scripts/negatives_restore.py --client ... --backup ... --execute
"""
import json
from pathlib import Path

from gads import arg_parser, client, g, guard_write, load_config, log_change, run

ap = arg_parser("Restore negatives from a backup")
ap.add_argument("--backup", required=True)
ap.add_argument("--execute", action="store_true")
a = ap.parse_args()
cfg = load_config(a.client)
cid = cfg["customer_id"]
b = json.loads((Path(a.backup) / "backup.json").read_text())
if b["customer_id"] != cid:
    raise SystemExit(f"Backup is for {b['customer_id']}, client config is {cid}.")
VO = not a.execute
print("MODE:", "DRY RUN (validate_only)" if VO else "EXECUTE")
c = client(cfg); ga = c.get_service("GoogleAdsService"); MT = c.enums.KeywordMatchTypeEnum
ss, sc, css, cc = (c.get_service(s) for s in ("SharedSetService", "SharedCriterionService", "CampaignSharedSetService", "CampaignCriterionService"))
existing = {g(r, "shared_set", "name"): g(r, "shared_set", "resource_name") for r in run(ga, cid,
            "SELECT shared_set.name, shared_set.resource_name FROM shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND shared_set.status = 'ENABLED'")}
live = {g(r, "campaign", "id") for r in run(ga, cid, "SELECT campaign.id FROM campaign WHERE campaign.status != 'REMOVED'")}
lists = {g(l, "shared_set", "id"): g(l, "shared_set", "name") for l in b["lists"]
         if g(l, "shared_set", "status") == "ENABLED" and g(l, "shared_set", "type") == "NEGATIVE_KEYWORDS"}
plan = []
for sid, name in lists.items():
    terms = [(g(t, "shared_criterion", "keyword", "text"), g(t, "shared_criterion", "keyword", "match_type")) for t in b["list_terms"] if g(t, "shared_set", "id") == sid]
    camps = [g(x, "campaign", "id") for x in b["attachments"] if g(x, "shared_set", "id") == sid
             and g(x, "campaign_shared_set", "status") == "ENABLED" and g(x, "campaign", "id") in live]
    plan.append((name, terms, camps))
cur = {(g(r, "campaign", "id"), g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type")) for r in run(ga, cid,
       "SELECT campaign.id, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type FROM campaign_criterion "
       "WHERE campaign_criterion.type = 'KEYWORD' AND campaign_criterion.negative = TRUE")}
missing = [(g(r, "campaign", "id"), g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type"))
           for r in b["campaign_negatives"] if g(r, "campaign", "id") in live]
missing = [m for m in missing if m not in cur]
ops_total = sum(len(t) + len(cps) + 1 for _, t, cps in plan) + len(missing)
guard_write(cfg, cid, ops_total, executing=not VO)
for name, terms, camps in plan:
    print(f"{name}: {len(terms)} terms, attach to {len(camps)} campaigns" + (" (exists, reuse)" if name in existing else ""))
print(f"campaign-level negatives missing vs backup: {len(missing)}")
if VO:
    print("Dry run only. Nothing changed."); raise SystemExit(0)
for name, terms, camps in plan:
    rn = existing.get(name)
    if not rn:
        op = c.get_type("SharedSetOperation"); op.create.name = name; op.create.type_ = c.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS
        rn = ss.mutate_shared_sets(request={"customer_id": cid, "operations": [op]}).results[0].resource_name
        ops = []
        for t, m in terms:
            op = c.get_type("SharedCriterionOperation"); op.create.shared_set = rn; op.create.keyword.text = t
            op.create.keyword.match_type = getattr(MT, m); ops.append(op)
        for i in range(0, len(ops), 1000):
            sc.mutate_shared_criteria(request={"customer_id": cid, "operations": ops[i:i + 1000]})
    ops = []
    for camp_id in camps:
        op = c.get_type("CampaignSharedSetOperation"); op.create.campaign = ga.campaign_path(cid, camp_id); op.create.shared_set = rn; ops.append(op)
    if ops:
        try:
            css.mutate_campaign_shared_sets(request={"customer_id": cid, "operations": ops, "partial_failure": True})
        except Exception as e:
            print("  attach skipped (likely already attached):", str(e)[:150])
if missing:
    ops = []
    for camp_id, t, m in missing:
        op = c.get_type("CampaignCriterionOperation"); op.create.campaign = ga.campaign_path(cid, camp_id)
        op.create.negative = True; op.create.keyword.text = t; op.create.keyword.match_type = getattr(MT, m); ops.append(op)
    cc.mutate_campaign_criteria(request={"customer_id": cid, "operations": ops})
log_change(cfg, "negatives_restore", {"backup": str(a.backup), "lists": len(plan), "campaign_negatives": len(missing)})
print("Restored.")
