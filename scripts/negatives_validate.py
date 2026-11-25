"""Validate a proposed negative keyword structure against the account's real history.

Reads work/<slug>/data (pull.py) and work/<slug>/negatives/proposed.yaml.
Writes work/<slug>/negatives/validation.xlsx and validation.json.

Gates. All four must be 0 before anything is applied:
  G1  a proposed negative blocks a search term that converted (any campaign, whole history window)
  G2  a proposed negative blocks a live keyword in a campaign the negative is attached to
  G3  a proposed negative blocks a search on the allow-list (niche allow-list + work/<slug>/allow-list.txt)
  G4  a proposed negative blocks a real search term that matches the niche's customer-intent pattern
      (lists marked exempt_from_intent_gate and groups in a list's exempt_groups_from_intent_gate are skipped:
      out-of-area, routing and "assets we do not buy" block those sellers on purpose)

Review tabs (decide each row, they do not block):
  Current conflicts  live negatives today that block converting or allow-listed searches
  Gap n-grams/terms  zero-conversion spend the proposed lists would still let through
  Impact             historical spend each negative would have blocked, split by whether a
                     currently enabled keyword triggered it (the honest number)

  python scripts/negatives_validate.py --client clients/acme.yaml
"""
import collections
import json
import re
import sys

import yaml

from gads import arg_parser, blocks, g, load, load_config, money, niche_dir, norm, role_of, work_dir, write_xlsx

ap = arg_parser("Validate proposed negatives")
a = ap.parse_args()
cfg = load_config(a.client)
P = yaml.safe_load((work_dir(cfg, "negatives") / "proposed.yaml").read_text())
accepted = {norm(k): v for k, v in (P.get("accepted_exceptions") or {}).items()}
exempt = set(P.get("exempt_from_intent_gate") or [])
exempt_groups = {(l["name"], grp) for l in P["lists"] for grp in (l.get("exempt_groups_from_intent_gate") or [])}

proposed = []  # (list, group, term, match, roles)
for l in P["lists"]:
    for grp, terms in (l.get("groups") or {}).items():
        for t in terms or []:
            proposed.append((l["name"], grp, norm(t), l.get("match", "PHRASE"), set(l.get("attach_to", []))))
for c in P.get("campaign_level") or []:
    proposed.append(("Campaign level", "Campaign level", norm(c["term"]), c.get("match", "PHRASE"), set(c.get("attach_to", []))))

# duplicates and redundancy inside the proposal
seen, dupes = {}, []
for ln, grp, t, m, roles in proposed:
    if (t, m) in seen and seen[(t, m)] != ln:
        dupes.append([t, seen[(t, m)], ln])
    seen[(t, m)] = ln

# enabled keywords now: (campaign, text, match)
live_kw = {(g(r, "campaign", "name"), norm(g(r, "ad_group_criterion", "keyword", "text")), g(r, "ad_group_criterion", "keyword", "match_type"))
           for r in load(cfg, "keywords") if g(r, "campaign", "status") == "ENABLED" and g(r, "ad_group", "status") == "ENABLED"
           and g(r, "ad_group_criterion", "status") == "ENABLED"}

st = collections.defaultdict(lambda: {"impr": 0, "clicks": 0, "cost": 0.0, "conv": 0.0, "roles": set(), "camps": set(), "eligible_cost": 0.0})
for r in load(cfg, "search_terms"):
    q = norm(g(r, "search_term_view", "search_term", default="")); m = r.get("metrics", {})
    camp = g(r, "campaign", "name", default="")
    x = st[q]
    cost = money(m.get("cost_micros"))
    x["impr"] += int(m.get("impressions", 0)); x["clicks"] += int(m.get("clicks", 0)); x["cost"] += cost
    x["conv"] += float(m.get("conversions", 0)); x["roles"].add(role_of(cfg, camp)); x["camps"].add(camp)
    trig = (camp, norm(g(r, "segments", "keyword", "info", "text", default="")), g(r, "segments", "keyword", "info", "match_type"))
    if trig in live_kw:
        x["eligible_cost"] += cost
converting = {q: x for q, x in st.items() if x["conv"] > 0}
print(f"search terms {len(st):,}  converting {len(converting):,}  proposed negatives {len(proposed):,}")

# allow-list and intent pattern
allow = []
nd = niche_dir(cfg)
for p in ([nd / "allow-list.txt"] if nd else []) + [work_dir(cfg) / "allow-list.txt"]:
    if p.exists():
        allow += [norm(l) for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
intent = yaml.safe_load((nd / "intent.yaml").read_text()) if nd and (nd / "intent.yaml").exists() else {}
INTENT = re.compile(intent["customer_intent"]) if intent.get("customer_intent") else None
NOT_INTENT = re.compile(intent["not_customer"]) if intent.get("not_customer") else None
brand = [norm(b) for b in cfg.get("brand_terms", [])]

g1, acc, g2, g3, g4, impact = [], [], [], [], [], []
for ln, grp, t, m, roles in proposed:
    hit = [(q, x) for q, x in st.items() if blocks(t, m, q)]
    for q, x in hit:
        if x["conv"] > 0:
            row = [ln, t, q, round(x["conv"], 1), round(x["cost"]), ", ".join(sorted(x["camps"]))]
            (acc if t in accepted else g1).append(row + ([accepted[t]] if t in accepted else []))
    impact.append([ln, grp, t, len(hit), sum(x["clicks"] for _, x in hit), round(sum(x["cost"] for _, x in hit)),
                   round(sum(x["eligible_cost"] for _, x in hit)), round(sum(x["conv"] for _, x in hit), 1)])
    for camp, kw, mt in live_kw:
        if role_of(cfg, camp) in roles and blocks(t, m, kw):
            g2.append([ln, t, camp, kw, mt])
    for q in allow:
        if blocks(t, m, q) and not (ln == "Campaign level" or any(b in q for b in brand) and t in brand):
            g3.append([ln, t, q])
    if INTENT and ln not in exempt and (ln, grp) not in exempt_groups and ln != "Campaign level":
        for q, x in st.items():
            if INTENT.search(q) and not (NOT_INTENT and NOT_INTENT.search(q)) and blocks(t, m, q) and t not in accepted:
                g4.append([ln, grp, t, q, round(x["cost"]), round(x["conv"], 1)])

# current negatives that hurt today
attach = collections.defaultdict(list)
for r in load(cfg, "list_attachments"):
    if g(r, "campaign_shared_set", "status") == "ENABLED":
        attach[g(r, "shared_set", "name")].append(g(r, "campaign", "name"))
cur = [(f"List: {g(r, 'shared_set', 'name')}", g(r, "shared_criterion", "keyword", "text"), g(r, "shared_criterion", "keyword", "match_type"),
        attach.get(g(r, "shared_set", "name"), [])) for r in load(cfg, "shared_criteria")]
cur += [(f"Campaign: {g(r, 'campaign', 'name')}", g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type"),
         [g(r, "campaign", "name")]) for r in load(cfg, "campaign_negatives")]
cur += [(f"Ad group: {g(r, 'campaign', 'name')} / {g(r, 'ad_group', 'name')}", g(r, "ad_group_criterion", "keyword", "text"),
         g(r, "ad_group_criterion", "keyword", "match_type"), [g(r, "campaign", "name")]) for r in load(cfg, "adgroup_negatives")]
conflicts = []
for src, t, m, camps in cur:
    for q, x in converting.items():
        if blocks(t, m, q):
            conflicts.append([src, t, m, ", ".join(sorted(set(camps))) or "(not attached)", q, round(x["conv"], 1)])
    for q in allow:
        if blocks(t, m, q) and camps:
            conflicts.append([src, t, m, ", ".join(sorted(set(camps))), q + "  (allow-list)", 0])

# gaps
conv_text = list(converting)
waste = collections.defaultdict(lambda: [0.0, 0, set()])
gap_terms = []
for q, x in st.items():
    if x["conv"] > 0 or x["cost"] <= 0:
        continue
    if any(blocks(t, m, q) and (roles & x["roles"]) for _, _, t, m, roles in proposed):
        continue
    gap_terms.append([q, x["clicks"], round(x["cost"], 2), round(x["eligible_cost"], 2), ", ".join(sorted(x["camps"]))])
    w = q.split()
    for gram in {" ".join(w[i:i + n]) for n in (1, 2, 3) for i in range(len(w) - n + 1)}:
        y = waste[gram]; y[0] += x["cost"]; y[1] += 1; y[2].add(q)
ngrams = []
for gram, (cost, n, qs) in waste.items():
    if cost >= 50 and n >= 2:
        conv_with = sum(1 for q in conv_text if f" {gram} " in f" {q} ")
        ngrams.append([gram, round(cost), n, conv_with, "safe to test" if conv_with == 0 else "appears in converting terms: use a longer phrase",
                       "; ".join(sorted(qs)[:5])])
ngrams.sort(key=lambda r: -r[1]); gap_terms.sort(key=lambda r: -r[2])

out = work_dir(cfg, "negatives")
gates = {"G1_converting_blocked": len(g1), "G2_live_keyword_blocked": len(g2), "G3_allow_list_blocked": len(g3),
         "G4_customer_intent_blocked": len(g4)}
write_xlsx(out / "validation.xlsx", [
    ("Gates", ["Gate", "Count", "Must be"], [[k, v, 0] for k, v in gates.items()]
     + [["Current negatives in conflict", len(conflicts), "review"], ["Gap terms (zero-conv spend not blocked)", len(gap_terms), "review"],
        ["Duplicate terms across lists", len(dupes), "review"]]),
    ("G1 Converting blocked", ["List", "Negative", "Search term", "Conv", "Cost", "Campaigns"], g1),
    ("Accepted exceptions", ["List", "Negative", "Search term", "Conv", "Cost", "Campaigns", "Reason"], acc),
    ("G2 Live keyword blocked", ["List", "Negative", "Campaign", "Keyword", "Match"], g2),
    ("G3 Allow-list blocked", ["List", "Negative", "Allow-list search"], g3),
    ("G4 Intent blocked", ["List", "Group", "Negative", "Search term", "Cost", "Conv"], g4),
    ("Current conflicts", ["Where", "Negative", "Match", "Campaigns", "Blocks", "Conv"], conflicts),
    ("Impact", ["List", "Group", "Negative", "Terms", "Clicks", "Cost blocked", "Cost blocked (live keywords only)", "Conv blocked"],
     sorted(impact, key=lambda r: -r[5])),
    ("Gap n-grams", ["N-gram", "Wasted cost", "Terms", "Converting terms containing it", "Advice", "Examples"], ngrams[:500]),
    ("Gap terms", ["Search term", "Clicks", "Cost", "Cost via live keywords", "Campaigns"], gap_terms[:3000]),
    ("Duplicates", ["Term", "First list", "Also in"], dupes),
])
summary = {"gates": gates, "accepted_exceptions": len(acc), "current_conflicts": len(conflicts), "gap_terms": len(gap_terms),
           "proposed_terms": len(proposed), "blocked_cost_all": round(sum(r[5] for r in impact)),
           "blocked_cost_live_keywords": round(sum(r[6] for r in impact)),
           "top_gap_ngrams": ngrams[:15]}
(out / "validation.json").write_text(json.dumps(summary, indent=1))
print("  ".join(f"{k.split('_')[0]} {v}" for k, v in gates.items()),
      f"| accepted {len(acc)} | current conflicts {len(conflicts)} | gap terms {len(gap_terms)} | dupes {len(dupes)}")
print(f"Wrote {out / 'validation.xlsx'}")
sys.exit(1 if any(gates.values()) else 0)
