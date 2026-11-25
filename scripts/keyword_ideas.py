"""Keyword Planner ideas for seed terms in the client's area. Read-only.

  python scripts/keyword_ideas.py --client clients/acme.yaml --seeds "sell my house fast" "cash home buyers"
  python scripts/keyword_ideas.py --client clients/acme.yaml --seeds-from-niche
Location IDs: service_area.geo_target_ids in the client yaml (Google geo target constants, e.g. 1014221).
Defaults to the United States. Writes work/<slug>/research/keyword-ideas.csv
"""
import csv

from gads import arg_parser, client, load_config, niche_dir, norm, work_dir

ap = arg_parser("Keyword Planner ideas")
ap.add_argument("--seeds", nargs="*", default=[])
ap.add_argument("--seeds-from-niche", action="store_true")
ap.add_argument("--limit", type=int, default=400)
a = ap.parse_args()
cfg = load_config(a.client)
seeds = list(a.seeds)
if a.seeds_from_niche:
    p = niche_dir(cfg) / "seed-keywords.txt"
    seeds += [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
if not seeds:
    raise SystemExit("Give --seeds or --seeds-from-niche.")
c = client(cfg)
svc = c.get_service("KeywordPlanIdeaService")
geos = cfg.get("service_area", {}).get("geo_target_ids") or [2840]
rows = {}
for i in range(0, len(seeds), 20):   # the API takes up to 20 seeds per request
    req = c.get_type("GenerateKeywordIdeasRequest")
    req.customer_id = cfg["customer_id"]
    req.language = "languageConstants/1000"
    for gid in geos:
        req.geo_target_constants.append(f"geoTargetConstants/{gid}")
    req.include_adult_keywords = False
    req.keyword_seed.keywords.extend(seeds[i:i + 20])
    for idea in svc.generate_keyword_ideas(request=req):
        m = idea.keyword_idea_metrics
        rows[norm(idea.text)] = [idea.text, m.avg_monthly_searches or 0, m.competition.name,
                                 round((m.low_top_of_page_bid_micros or 0) / 1e6, 2), round((m.high_top_of_page_bid_micros or 0) / 1e6, 2)]
out = sorted(rows.values(), key=lambda r: -r[1])[:a.limit]
p = work_dir(cfg, "research") / "keyword-ideas.csv"
with p.open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["keyword", "avg_monthly_searches", "competition", "top_of_page_bid_low", "top_of_page_bid_high"]); w.writerows(out)
print(f"{len(out)} ideas. Wrote {p}")
