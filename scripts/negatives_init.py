"""Start a proposed negative keyword structure for a client from its niche pack.

Writes work/<slug>/negatives/proposed.yaml. Edit that file; it is the single
source of truth that negatives_validate.py and negatives_apply.py read.

  python scripts/negatives_init.py --client clients/acme.yaml [--force]
"""
import sys

import yaml

from gads import arg_parser, load_config, niche_dir, norm, work_dir

ap = arg_parser("Seed proposed negative lists from the niche pack")
ap.add_argument("--force", action="store_true", help="Overwrite an existing proposed.yaml")
a = ap.parse_args()
cfg = load_config(a.client)
out = work_dir(cfg, "negatives") / "proposed.yaml"
if out.exists() and not a.force:
    sys.exit(f"{out} exists. Edit it, or pass --force to start over.")
nd = niche_dir(cfg)
src = nd / "negatives.yaml" if nd else None
if not src or not src.exists():
    sys.exit("Client has no niche pack with negatives.yaml. Set 'niche' in the client yaml, or write proposed.yaml by hand "
             "(see docs/playbook/04-negative-keywords.md for the format).")
tpl = yaml.safe_load(src.read_text())
prefix = cfg.get("list_prefix") or cfg["slug"].upper()[:6]
lists = []
for l in tpl["lists"]:
    l = dict(l)
    l["name"] = l["name"].replace("{prefix}", prefix)
    groups = dict(l.get("groups", {}))
    key = l.get("fill_from")
    if key == "competitors" and cfg.get("competitors"):
        groups["Client competitors"] = [norm(c) for c in cfg["competitors"]]
    if key == "out_of_area":
        ex = cfg.get("service_area", {}).get("exclude_terms", [])
        if ex:
            groups["Client out-of-area places"] = [norm(x) for x in ex]
        own = {norm(x) for x in cfg.get("service_area", {}).get("include_terms", [])}
        for gname, terms in list(groups.items()):   # never negate a place the client serves
            groups[gname] = [t for t in terms if norm(t) not in own]
    l["groups"] = groups
    l.pop("fill_from", None)
    lists.append(l)
camp = [{"term": norm(b), "match": "PHRASE", "attach_to": ["generic", "competitors"]} for b in cfg.get("brand_terms", [])]
doc = {
    "prefix": prefix,
    "lists": lists,
    "campaign_level": camp,
    "accepted_exceptions": {},
    "exempt_from_intent_gate": [l["name"] for l in lists if l.get("exempt_from_intent_gate")],
}
out.write_text(f"# Proposed negatives for {cfg['slug']}. Seeded from niches/{cfg['niche']}/negatives.yaml.\n"
               "# attach_to uses campaign roles from the client yaml (campaign_roles).\n"
               "# Edit freely, then run negatives_validate.py until every gate is 0.\n"
               + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=140))
n = sum(len(t) for l in lists for t in l["groups"].values())
print(f"Wrote {out}: {len(lists)} lists, {n} terms, {len(camp)} campaign-level brand negatives.")
