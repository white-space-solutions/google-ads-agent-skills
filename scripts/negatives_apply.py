"""Apply negative keyword changes. DRY RUN by default: every operation is sent with validate_only,
so Google checks it and nothing changes.

Executing needs all of: --execute, APPLY_ENABLED=1 in the environment, the customer ID on the
client's safety allowlist, an op count under safety.max_ops_per_run, and (for the structure
mode) a validation run with every gate at 0 that is newer than proposed.yaml. A fresh backup is
taken automatically before any write. Every write is appended to work/<slug>/changes.log.jsonl.

Modes
  (default)        create the lists in proposed.yaml, add missing terms, attach them by campaign role,
                   add campaign-level negatives. Safe to rerun: existing lists/attachments are reused.
  --retire-old     detach every negative list that is not in proposed.yaml (refuses unless all proposed
                   lists are attached). Lists are detached, never deleted: delete them in the UI after
                   two clean weeks.
  --add-terms F    add the terms in file F (one per line) to --list NAME. Each term is checked against
                   converting search terms and the allow-list first; conflicts are refused.
  --remove F       remove live negatives listed in CSV F with columns scope,container,text,match
                   (scope = list | campaign | adgroup; container = list name, campaign name, or
                   "campaign / ad group").

  python scripts/negatives_apply.py --client clients/acme.yaml                       # dry run
  APPLY_ENABLED=1 python scripts/negatives_apply.py --client clients/acme.yaml --execute
"""
import csv
import json
import sys
from pathlib import Path

import yaml

from gads import (arg_parser, blocks, client, g, guard_write, latest_backup, load, load_config, log_change,
                  niche_dir, norm, role_of, run, work_dir)
from negatives_backup import backup

ap = arg_parser("Apply negative keyword changes (dry run by default)")
ap.add_argument("--execute", action="store_true")
ap.add_argument("--retire-old", action="store_true")
ap.add_argument("--add-terms")
ap.add_argument("--list")
ap.add_argument("--match", default="PHRASE", choices=["PHRASE", "EXACT", "BROAD"])
ap.add_argument("--remove")
a = ap.parse_args()
cfg = load_config(a.client)
cid = cfg["customer_id"]
VO = not a.execute
print("MODE:", "DRY RUN (validate_only, nothing changes)" if VO else "EXECUTE")

c = client(cfg)
ga = c.get_service("GoogleAdsService")
MT = c.enums.KeywordMatchTypeEnum
ss, sc, css, cc, agc = (c.get_service(s) for s in ("SharedSetService", "SharedCriterionService", "CampaignSharedSetService",
                                                     "CampaignCriterionService", "AdGroupCriterionService"))
camps = {g(r, "campaign", "name"): g(r, "campaign", "id") for r in run(ga, cid,
         "SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status != 'REMOVED' AND campaign.advertising_channel_type = 'SEARCH'")}
lists = {g(r, "shared_set", "name"): g(r, "shared_set", "resource_name") for r in run(ga, cid,
         "SELECT shared_set.name, shared_set.resource_name FROM shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND shared_set.status = 'ENABLED'")}
attached = {(g(r, "shared_set", "name"), g(r, "campaign", "name")) for r in run(ga, cid,
            "SELECT campaign.name, shared_set.name FROM campaign_shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS' "
            "AND campaign_shared_set.status = 'ENABLED' AND campaign.status != 'REMOVED'")}


TOTAL = [0]


def mutate(svc_method, ops, label):
    if not ops:
        return []
    TOTAL[0] += len(ops)
    guard_write(cfg, cid, TOTAL[0], executing=not VO)   # cap counts every op in this run
    results = []
    for i in range(0, len(ops), 1000):
        # request= form on purpose: the kwargs form silently ignores validate_only
        res = svc_method(request={"customer_id": cid, "operations": ops[i:i + 1000], "validate_only": VO})
        results += list(res.results)
    print(f"  {'OK would' if VO else 'DONE'} {label}: {len(ops)} ops")
    if not VO:
        log_change(cfg, label, {"ops": len(ops)})
    return results


def ensure_backup():
    if VO:
        return
    b = latest_backup(cfg, 24)
    print(f"Backup: {b}" if b else "No backup in the last 24 hours, taking one now.")
    if not b:
        backup(cfg)


def term_conflicts(terms, match):
    st = load(cfg, "search_terms", [])
    conv = {norm(g(r, "search_term_view", "search_term", default="")) for r in st if float(g(r, "metrics", "conversions", default=0)) > 0}
    allow = []
    nd = niche_dir(cfg)
    for p in ([nd / "allow-list.txt"] if nd else []) + [work_dir(cfg) / "allow-list.txt"]:
        if p.exists():
            allow += [norm(l) for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
    out = []
    for t in terms:
        hits = [q for q in conv if blocks(t, match, q)] + [q + " (allow-list)" for q in allow if blocks(t, match, q)]
        if hits:
            out.append((t, hits[:5]))
    return out


# ------------------------------------------------------------- add terms to one list
if a.add_terms:
    if not a.list or a.list not in lists:
        sys.exit(f"--list must name an existing enabled negative list. Found: {sorted(lists)}")
    terms = [norm(l) for l in Path(a.add_terms).read_text().splitlines() if l.strip() and not l.startswith("#")]
    have = {norm(g(r, "shared_criterion", "keyword", "text")) for r in run(ga, cid,
            f"SELECT shared_criterion.keyword.text FROM shared_criterion WHERE shared_set.resource_name = '{lists[a.list]}'")}
    terms = [t for t in dict.fromkeys(terms) if t not in have]
    bad = term_conflicts(terms, a.match)
    if bad:
        for t, h in bad:
            print(f"  REFUSED '{t}': blocks {h}")
        sys.exit("Fix or drop the refused terms (use a longer, more specific phrase), then rerun.")
    ensure_backup()
    ops = []
    for t in terms:
        op = c.get_type("SharedCriterionOperation"); op.create.shared_set = lists[a.list]
        op.create.keyword.text = t; op.create.keyword.match_type = getattr(MT, a.match); ops.append(op)
    mutate(sc.mutate_shared_criteria, ops, f"add {len(ops)} terms to {a.list}")
    sys.exit(0)

# ------------------------------------------------------------- remove listed negatives
if a.remove:
    rows = list(csv.DictReader(Path(a.remove).open()))
    live_list = run(ga, cid, "SELECT shared_set.name, shared_criterion.resource_name, shared_criterion.keyword.text, shared_criterion.keyword.match_type "
                             "FROM shared_criterion WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND shared_set.status = 'ENABLED'")
    live_camp = run(ga, cid, "SELECT campaign.name, campaign_criterion.resource_name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type "
                             "FROM campaign_criterion WHERE campaign_criterion.type = 'KEYWORD' AND campaign_criterion.negative = TRUE AND campaign.status != 'REMOVED'")
    live_ag = run(ga, cid, "SELECT campaign.name, ad_group.name, ad_group_criterion.resource_name, ad_group_criterion.keyword.text, "
                           "ad_group_criterion.keyword.match_type FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD' "
                           "AND ad_group_criterion.negative = TRUE AND campaign.status != 'REMOVED'")
    idx = {}
    for r in live_list:
        idx[("list", g(r, "shared_set", "name"), norm(g(r, "shared_criterion", "keyword", "text")), g(r, "shared_criterion", "keyword", "match_type"))] = ("sc", g(r, "shared_criterion", "resource_name"))
    for r in live_camp:
        idx[("campaign", g(r, "campaign", "name"), norm(g(r, "campaign_criterion", "keyword", "text")), g(r, "campaign_criterion", "keyword", "match_type"))] = ("cc", g(r, "campaign_criterion", "resource_name"))
    for r in live_ag:
        idx[("adgroup", f"{g(r, 'campaign', 'name')} / {g(r, 'ad_group', 'name')}", norm(g(r, "ad_group_criterion", "keyword", "text")),
             g(r, "ad_group_criterion", "keyword", "match_type"))] = ("agc", g(r, "ad_group_criterion", "resource_name"))
    by = {"sc": [], "cc": [], "agc": []}
    for row in rows:
        k = (row["scope"].strip().lower(), row["container"].strip(), norm(row["text"]), row["match"].strip().upper())
        if k not in idx:
            print(f"  NOT FOUND {k}"); continue
        kind, rn = idx[k]; by[kind].append(rn); print(f"  remove {k}")
    ensure_backup()
    for kind, svc, typ, meth in (("sc", sc, "SharedCriterionOperation", sc.mutate_shared_criteria),
                                 ("cc", cc, "CampaignCriterionOperation", cc.mutate_campaign_criteria),
                                 ("agc", agc, "AdGroupCriterionOperation", agc.mutate_ad_group_criteria)):
        ops = []
        for rn in by[kind]:
            op = c.get_type(typ); op.remove = rn; ops.append(op)
        mutate(meth, ops, f"remove {kind} negatives")
    sys.exit(0)

# ------------------------------------------------------------- structure from proposed.yaml
P = yaml.safe_load((work_dir(cfg, "negatives") / "proposed.yaml").read_text())
names = [l["name"] for l in P["lists"]]


def camps_for(roles):
    return sorted((n, i) for n, i in camps.items() if role_of(cfg, n) in set(roles))


if a.retire_old:
    missing = [n for n in names if not any(l == n for l, _ in attached)]
    if missing:
        sys.exit(f"Refusing to retire: these proposed lists are not attached yet: {missing}")
    rows = run(ga, cid, "SELECT campaign.name, shared_set.name, campaign_shared_set.resource_name FROM campaign_shared_set "
                        "WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND campaign_shared_set.status = 'ENABLED' AND campaign.status != 'REMOVED'")
    ops = []
    for r in rows:
        if g(r, "shared_set", "name") not in names:
            op = c.get_type("CampaignSharedSetOperation"); op.remove = g(r, "campaign_shared_set", "resource_name"); ops.append(op)
            print(f"  detach '{g(r, 'shared_set', 'name')}' from {g(r, 'campaign', 'name')}")
    ensure_backup()
    mutate(css.mutate_campaign_shared_sets, ops, "detach old lists")
    print("Old lists are detached, not deleted. Delete them in the UI after two clean weekly search term reviews.")
    sys.exit(0)

if not VO:
    v = work_dir(cfg, "negatives") / "validation.json"
    p = work_dir(cfg, "negatives") / "proposed.yaml"
    if not v.exists() or v.stat().st_mtime < p.stat().st_mtime:
        sys.exit("Refusing: run negatives_validate.py after your last edit to proposed.yaml.")
    gates = json.loads(v.read_text())["gates"]
    if any(gates.values()):
        sys.exit(f"Refusing: gates are not all 0: {gates}")
ensure_backup()
for l in P["lists"]:
    name = l["name"]; match = l.get("match", "PHRASE")
    terms = list(dict.fromkeys(norm(t) for ts in (l.get("groups") or {}).values() for t in ts or []))
    targets = camps_for(l.get("attach_to", []))
    if not targets:
        sys.exit(f"{name}: no campaigns match roles {l.get('attach_to')}. Check campaign_roles in the client yaml.")
    print(f"{name}: {len(terms)} terms -> {[n for n, _ in targets]}")
    rn = lists.get(name)
    if not rn:
        op = c.get_type("SharedSetOperation"); op.create.name = name; op.create.type_ = c.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS
        res = mutate(ss.mutate_shared_sets, [op], f"create list {name}")
        if VO:
            print(f"  (dry run: {len(terms)} terms and {len(targets)} attachments are validated after the list exists)")
            continue
        rn = res[0].resource_name
        have = set()
    else:
        have = {(norm(g(r, "shared_criterion", "keyword", "text")), g(r, "shared_criterion", "keyword", "match_type")) for r in run(ga, cid,
                f"SELECT shared_criterion.keyword.text, shared_criterion.keyword.match_type FROM shared_criterion WHERE shared_set.resource_name = '{rn}'")}
    ops = []
    for t in terms:
        if (t, match) in have:
            continue
        op = c.get_type("SharedCriterionOperation"); op.create.shared_set = rn
        op.create.keyword.text = t; op.create.keyword.match_type = getattr(MT, match); ops.append(op)
    mutate(sc.mutate_shared_criteria, ops, f"add terms to {name}")
    ops = []
    for n, i in targets:
        if (name, n) in attached:
            continue
        op = c.get_type("CampaignSharedSetOperation"); op.create.campaign = ga.campaign_path(cid, i); op.create.shared_set = rn; ops.append(op)
    mutate(css.mutate_campaign_shared_sets, ops, f"attach {name}")

have_cc = {(g(r, "campaign", "name"), norm(g(r, "campaign_criterion", "keyword", "text")), g(r, "campaign_criterion", "keyword", "match_type")) for r in run(ga, cid,
           "SELECT campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type FROM campaign_criterion "
           "WHERE campaign_criterion.type = 'KEYWORD' AND campaign_criterion.negative = TRUE AND campaign.status != 'REMOVED'")}
ops = []
for x in P.get("campaign_level") or []:
    t, m = norm(x["term"]), x.get("match", "PHRASE")
    for n, i in camps_for(x.get("attach_to", [])):
        if (n, t, m) in have_cc:
            continue
        op = c.get_type("CampaignCriterionOperation"); op.create.campaign = ga.campaign_path(cid, i)
        op.create.negative = True; op.create.keyword.text = t; op.create.keyword.match_type = getattr(MT, m); ops.append(op)
mutate(cc.mutate_campaign_criteria, ops, "add campaign-level negatives")
print("Dry run complete. Nothing changed." if VO else "Applied. Next: --retire-old once you have checked the attachments in the UI.")
