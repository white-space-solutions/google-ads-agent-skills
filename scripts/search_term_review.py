"""Weekly search term review. Read-only: pulls the last N days live and reports.

  1. Leaks          served search terms that match a live negative on their campaign (should be 0)
  2. Wrongly blocked customer-intent searches that a live negative blocks somewhere in the account
                    (from the history pull, if present)
  3. Junk candidates clicked, zero conversions, sorted by spend, with a suggested phrase root
                    and a check against converting history and the allow-list
  4. New winners    converting search terms that are not keywords yet
  5. Structure      which negative lists each enabled search campaign has

Writes work/<slug>/reviews/search-terms-<date>.md and .json. The agent turns that into the
weekly note; nothing is added until a person approves (then negatives_apply.py --add-terms).

  python scripts/search_term_review.py --client clients/acme.yaml --days 7
"""
import collections
import datetime as dt
import json
import re

import yaml

from gads import arg_parser, blocks, client, g, load, load_config, money, niche_dir, norm, role_of, run, work_dir

ap = arg_parser("Weekly search term review")
ap.add_argument("--days", type=int, default=7)
a = ap.parse_args()
cfg = load_config(a.client)
cid = cfg["customer_id"]
end = dt.date.today(); start = end - dt.timedelta(days=a.days)
ga = client(cfg).get_service("GoogleAdsService")
st = run(ga, cid, "SELECT campaign.name, search_term_view.search_term, search_term_view.status, segments.keyword.info.text, "
                  "metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM search_term_view "
                  f"WHERE segments.date BETWEEN '{start}' AND '{end}'")
terms = run(ga, cid, "SELECT shared_set.name, shared_criterion.keyword.text, shared_criterion.keyword.match_type FROM shared_criterion "
                     "WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND shared_set.status = 'ENABLED'")
att = run(ga, cid, "SELECT campaign.name, shared_set.name FROM campaign_shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS' "
                   "AND campaign_shared_set.status = 'ENABLED' AND campaign.status != 'REMOVED'")
cn = run(ga, cid, "SELECT campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type FROM campaign_criterion "
                  "WHERE campaign_criterion.negative = TRUE AND campaign_criterion.type = 'KEYWORD' AND campaign.status != 'REMOVED'")
camps = [g(r, "campaign", "name") for r in run(ga, cid, "SELECT campaign.name FROM campaign WHERE campaign.status = 'ENABLED' "
                                                       "AND campaign.advertising_channel_type = 'SEARCH'")]
kws = {norm(g(r, "ad_group_criterion", "keyword", "text")) for r in run(ga, cid,
       "SELECT ad_group_criterion.keyword.text FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD' "
       "AND ad_group_criterion.negative = FALSE AND ad_group_criterion.status = 'ENABLED'")}

lists = collections.defaultdict(list)
for r in terms:
    lists[g(r, "shared_set", "name")].append((g(r, "shared_criterion", "keyword", "text"), g(r, "shared_criterion", "keyword", "match_type")))
on = collections.defaultdict(set)
for r in att:
    on[g(r, "campaign", "name")].add(g(r, "shared_set", "name"))
neg = collections.defaultdict(list)
for c, sets in on.items():
    for s in sets:
        neg[c] += [(t, m, s) for t, m in lists[s]]
for r in cn:
    neg[g(r, "campaign", "name")].append((g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type"), "campaign level"))

agg = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, set()])
for r in st:
    k = (g(r, "campaign", "name"), norm(g(r, "search_term_view", "search_term", default=""))); x = agg[k]; m = r.get("metrics", {})
    x[0] += int(m.get("impressions", 0)); x[1] += int(m.get("clicks", 0)); x[2] += money(m.get("cost_micros")); x[3] += float(m.get("conversions", 0))
    x[4].add(g(r, "segments", "keyword", "info", "text", default=""))

hist = load(cfg, "search_terms", [])
conv_hist = {norm(g(r, "search_term_view", "search_term", default="")) for r in hist if float(g(r, "metrics", "conversions", default=0)) > 0}
allow = []
nd = niche_dir(cfg)
for p in ([nd / "allow-list.txt"] if nd else []) + [work_dir(cfg) / "allow-list.txt"]:
    if p.exists():
        allow += [norm(l) for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
intent = yaml.safe_load((nd / "intent.yaml").read_text()) if nd and (nd / "intent.yaml").exists() else {}
INTENT = re.compile(intent["customer_intent"]) if intent.get("customer_intent") else None
STOP = set((intent.get("stopwords") or "a an the to for my of in on is i me do how can near").split())

tot = [sum(x[i] for x in agg.values()) for i in range(4)]
leaks = [(c, q, [n[2] for n in neg[c] if blocks(n[0], n[1], q)]) for (c, q) in agg if any(blocks(n[0], n[1], q) for n in neg[c])]
all_negs = [(t, m, s) for s, v in lists.items() for t, m in v]
wrong = []
if INTENT:
    seen = set()
    for r in hist:
        q = norm(g(r, "search_term_view", "search_term", default=""))
        if q in seen or not INTENT.search(q):
            continue
        seen.add(q)
        hits = [s for t, m, s in all_negs if blocks(t, m, q)]
        if hits and float(g(r, "metrics", "conversions", default=0)) > 0:
            wrong.append((q, hits[0]))


def root(q):
    """Shortest distinctive phrase in the term that never appears in a converting search or the allow-list.
    A suggestion, not a decision: the person reviewing still judges it."""
    words = q.split()
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            gram = " ".join(words[i:i + n])
            parts = gram.split()
            if parts[0] in STOP or parts[-1] in STOP or (n == 1 and len(gram) < 5):
                continue
            if INTENT and INTENT.search(gram):
                continue
            if not any(f" {gram} " in f" {c} " for c in conv_hist) and not any(f" {gram} " in f" {al} " for al in allow):
                return gram
    return None


junk = []
for (c, q), x in sorted(agg.items(), key=lambda i: -i[1][2]):
    if x[1] > 0 and x[3] == 0:
        role = role_of(cfg, c)
        is_intent = bool(INTENT and INTENT.search(q))
        # On competitor and brand campaigns, names are the point: review the keyword, not negatives.
        r_ = None if is_intent or role in ("competitors", "brand") else root(q)
        junk.append({"campaign": c, "role": role, "term": q, "clicks": x[1], "cost": round(x[2], 2),
                     "triggered_by": sorted(x[4]), "suggested_phrase_negative": r_,
                     "intent_match": is_intent, "in_allow_list": q in allow})
winners = [{"campaign": c, "term": q, "conv": round(x[3], 1), "cost": round(x[2], 2)} for (c, q), x in agg.items() if x[3] > 0 and q not in kws]

out = work_dir(cfg, "reviews")
stamp = end.isoformat()
L = [f"# Search term review {start} to {end}", "",
     f"{len(agg)} search terms, {tot[0]:,} impressions, {tot[1]:,} clicks, ${tot[2]:,.0f}, {tot[3]:.1f} conversions.", "",
     "## 1. Leaks (should be none)", ""]
L += [f"- {c}: {q} matches {s}" for c, q, s in leaks] or ["None."]
L += ["", "## 2. Converting customer searches a live negative now blocks", ""]
L += [f"- {q}  (blocked by {s})" for q, s in wrong[:30]] or ["None."]
L += ["", "## 3. Clicked, no conversion (review; do not auto-add)", "",
      "| Campaign | Search term | Clicks | Spend | Triggered by | Suggested phrase negative | Customer intent? |", "|---|---|---|---|---|---|---|"]
for j in junk[:60]:
    L.append(f"| {j['campaign'][:40]} | {j['term']} | {j['clicks']} | ${j['cost']:,.0f} | {', '.join(j['triggered_by'])[:40]} | "
             f"{j['suggested_phrase_negative'] or ('(competitor/brand campaign)' if j['role'] in ('competitors', 'brand') else '(none: leave it)')} | "
             f"{'YES, likely a real customer' if j['intent_match'] else ''} |")
L += ["", "## 4. Converting terms that are not keywords yet", ""]
L += [f"- {w['term']} ({w['campaign']}, {w['conv']} conv, ${w['cost']:,.0f})" for w in winners] or ["None."]
L += ["", "## 5. Negative lists per enabled search campaign", ""]
L += [f"- {c}: {', '.join(sorted(on.get(c, []))) or 'NO LISTS'}" for c in camps]
(out / f"search-terms-{stamp}.md").write_text("\n".join(L) + "\n")
(out / f"search-terms-{stamp}.json").write_text(json.dumps({"window": [str(start), str(end)], "totals": tot, "leaks": leaks,
                                                            "wrongly_blocked": wrong, "junk": junk, "winners": winners}, indent=1, default=list))
print(f"leaks {len(leaks)}  wrongly blocked {len(wrong)}  junk candidates {len(junk)}  winners {len(winners)}")
print(f"Wrote {out / f'search-terms-{stamp}.md'}")
