"""Deterministic account audit. Reads work/<slug>/data/*.json (run pull.py first).

Produces:
  work/<slug>/audit/findings.json   every check, with severity, evidence and dollars where known
  work/<slug>/audit/facts.md        a fact sheet the agent turns into the written audit

The script finds and measures. The agent (skills/google-ads-audit) decides what
matters, ranks it, and writes the report. No API calls, no changes.

  python scripts/audit.py --client clients/acme.yaml
"""
import collections
import json
import re
from pathlib import Path

from gads import arg_parser, blocks, g, load, load_config, money, niche_dir, norm, role_of, work_dir

ap = arg_parser("Deterministic Google Ads audit from pulled data")
a = ap.parse_args()
cfg = load_config(a.client)
L = lambda name: load(cfg, name, [])
F = []  # findings


def find(area, sev, title, evidence, dollars=None, fix=None):
    F.append({"area": area, "severity": sev, "title": title, "evidence": evidence,
              "dollars": round(dollars) if dollars else None, "suggested_fix": fix})


# ------------------------------------------------------------------ snapshot
cust = (L("customer") or [{}])[0].get("customer", {})
perf = L("campaign_perf")
camp_rows = []
tot = collections.Counter()
for r in perf:
    m = r.get("metrics", {})
    cost, conv = money(m.get("cost_micros")), float(m.get("conversions", 0))
    tot["cost"] += cost; tot["conv"] += conv; tot["clicks"] += int(m.get("clicks", 0))
    camp_rows.append({"campaign": g(r, "campaign", "name"), "type": g(r, "campaign", "advertising_channel_type"),
                      "status": g(r, "campaign", "status"), "role": role_of(cfg, g(r, "campaign", "name", default="")),
                      "cost": round(cost), "conv": round(conv, 1), "cpa": round(cost / conv) if conv else None,
                      "clicks": int(m.get("clicks", 0)),
                      "is": m.get("search_impression_share"), "lost_budget": m.get("search_budget_lost_impression_share"),
                      "lost_rank": m.get("search_rank_lost_impression_share")})
camp_rows.sort(key=lambda x: -x["cost"])
acct_cpa = tot["cost"] / tot["conv"] if tot["conv"] else None
waste_floor = max(150.0, 2 * acct_cpa) if acct_cpa else 300.0   # spend with zero conversions that is worth calling out

# ------------------------------------------------------------------ account settings
if cust and not cust.get("auto_tagging_enabled"):
    find("tracking", "high", "Auto-tagging is off", "customer.auto_tagging_enabled = false. GCLIDs are not appended, so offline conversion uploads cannot match clicks.",
         fix="Turn on auto-tagging in Account settings.")

# ------------------------------------------------------------------ campaign settings
for r in L("campaigns"):
    c = r.get("campaign", {})
    name, ch = c.get("name"), c.get("advertising_channel_type")
    if c.get("status") != "ENABLED":
        continue
    pos = g(c, "geo_target_type_setting", "positive_geo_target_type")
    if pos == "PRESENCE_OR_INTEREST":
        find("targeting", "high", f"{name}: location option is 'Presence or interest'",
             "Ads can show to people outside the service area who searched about it. Local service businesses should use 'Presence'.",
             fix="Campaign settings > Locations > Location options > Presence: people in or regularly in your included locations.")
    if ch == "SEARCH" and g(c, "network_settings", "target_content_network"):
        find("targeting", "high", f"{name}: Search campaign also runs on the Display Network",
             "Display placements usually burn budget at low intent inside a Search campaign.", fix="Uncheck Display Network in campaign settings.")
    if ch == "SEARCH" and g(c, "network_settings", "target_search_network"):
        find("targeting", "low", f"{name}: Search partners on", "Check search partner performance segment before keeping it.",
             fix="Segment by network; turn off partners if CPA is worse.")

for c in camp_rows:
    lb = c["lost_budget"]
    if c["status"] == "ENABLED" and lb and float(lb) >= 0.3 and c["cost"] > 0:
        find("budget", "high" if float(lb) >= 0.6 else "medium",
             f"{c['campaign']}: loses {float(lb):.0%} of impression share to budget",
             f"Spend {c['cost']:,}, conv {c['conv']}, CPA {c['cpa']}. The campaign is capped, so bidding cannot learn and you miss most eligible searches.",
             fix="Fund it (raise budget or lower target) or fold its keywords into a campaign that is funded.")

# ------------------------------------------------------------------ conversions
acts = [r["conversion_action"] for r in L("conversion_actions") if r.get("conversion_action")]
enabled = [x for x in acts if x.get("status") == "ENABLED"]
primary = [x for x in enabled if x.get("primary_for_goal")]
if len(enabled) > 12:
    find("conversions", "medium", f"{len(enabled)} enabled conversion actions",
         "Too many actions make it hard to tell what bidding optimizes toward and invite double counting.",
         fix="Keep one primary action per funnel stage; set the rest to secondary or remove them.")


def base(n):
    n = norm(n)
    n = re.sub(r"\b(all|secondary|primary|copy|new|old|v\d+|\d+)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


groups = collections.defaultdict(list)
for x in enabled:
    groups[base(x["name"])].append(x["name"])
for k, names in groups.items():
    if len(names) > 1:
        find("conversions", "medium", f"Near-duplicate conversion actions: {', '.join(names)}",
             "Similar actions often double count the same lead.", fix="Pick one per stage and set the others to secondary.")

# value drift per action (weekly value per conversion)
wk = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0]))
for r in L("conversions_by_action_week"):
    n, w = g(r, "segments", "conversion_action_name"), g(r, "segments", "week")
    m = r.get("metrics", {})
    wk[n][w][0] += float(m.get("all_conversions", 0)); wk[n][w][1] += float(m.get("all_conversions_value", 0))
for n, weeks in wk.items():
    vals = [(w, v / c) for w, (c, v) in sorted(weeks.items()) if c >= 1 and v > 0]
    if len(vals) >= 4:
        lo, hi = min(v for _, v in vals), max(v for _, v in vals)
        if lo > 0 and hi / lo >= 1.75:
            find("conversions", "high", f"Conversion value for '{n}' moved {hi / lo:.1f}x in 6 months",
                 f"Value per conversion ranged ${lo:,.0f} to ${hi:,.0f} across weeks ({vals[0][0]} to {vals[-1][0]}). "
                 "Value-based bidding re-learns every time this moves.",
                 fix="Set one value per stage from close rate x average profit, document it, change it at most once a quarter.")

# primary actions gone quiet
days = collections.defaultdict(dict)
for r in L("conversions_by_action_day"):
    days[g(r, "segments", "conversion_action_name")][g(r, "segments", "date")] = float(g(r, "metrics", "all_conversions", default=0))
for x in primary:
    d = days.get(x["name"], {})
    hits = sorted(k for k, v in d.items() if v > 0)
    if not hits:
        find("conversions", "high", f"Primary action '{x['name']}' recorded nothing in 90 days",
             "Bidding is told to optimize toward an action that never fires.", fix="Fix the tag/upload, or set it to secondary.")
for r in L("offline_upload_summary"):
    s = r.get("offline_conversion_upload_client_summary", {})
    status, rate = s.get("status"), s.get("success_rate")
    if status and status not in ("EXCELLENT", "GOOD"):
        find("conversions", "high", f"Offline upload client {s.get('client')} status {status}",
             f"Last upload {s.get('last_upload_date_time')}, success rate {rate}.", fix="Check the upload job and failed rows in Diagnostics.")
writers = collections.defaultdict(set)
for r in L("offline_upload_by_action"):
    s = r.get("offline_conversion_upload_conversion_action_summary", {})
    if s.get("conversion_action_name"):
        writers[s["conversion_action_name"]].add(s.get("client"))
for n, cl in writers.items():
    if len(cl) > 1:
        find("conversions", "high", f"'{n}' is written by {len(cl)} upload clients ({', '.join(sorted(map(str, cl)))})",
             "Two pipelines writing the same action risks double counting and conflicting values.",
             fix="Give each conversion action exactly one upload owner and document it.")

# ------------------------------------------------------------------ keywords
kw = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
for r in L("keyword_perf"):
    k = (g(r, "campaign", "name"), g(r, "ad_group", "name"), g(r, "ad_group_criterion", "keyword", "text"),
         g(r, "ad_group_criterion", "keyword", "match_type"))
    m = r.get("metrics", {})
    x = kw[k]; x[0] += int(m.get("impressions", 0)); x[1] += int(m.get("clicks", 0)); x[2] += money(m.get("cost_micros")); x[3] += float(m.get("conversions", 0))
dead = sorted([(k, v) for k, v in kw.items() if v[3] == 0 and v[2] >= waste_floor], key=lambda kv: -kv[1][2])
if dead:
    find("keywords", "high", f"{len(dead)} keywords spent ${sum(v[2] for _, v in dead):,.0f} with zero conversions",
         "; ".join(f"[{k[3]}] {k[2]} (${v[2]:,.0f}, {v[1]} clicks, {k[0]})" for k, v in dead[:12]),
         dollars=sum(v[2] for _, v in dead), fix="Pause, or move to a tighter match type; check the search terms each one triggered first.")
by_match = collections.Counter()
for k, v in kw.items():
    by_match[k[3]] += v[2]
spend_kw = sum(by_match.values())
if spend_kw and by_match.get("BROAD", 0) / spend_kw > 0.4:
    find("keywords", "medium", f"Broad match carries {by_match['BROAD'] / spend_kw:.0%} of keyword spend",
         "Broad match drifts into listings, rentals and research searches unless negatives and conversion signal are very strong.",
         fix="Move proven themes to phrase/exact; keep broad only where conversion data is strong and negatives are tight.")
lowqs = [r for r in L("keywords") if (g(r, "ad_group_criterion", "quality_info", "quality_score") or 10) <= 4
         and g(r, "ad_group_criterion", "status") == "ENABLED"]
if lowqs:
    find("keywords", "low", f"{len(lowqs)} enabled keywords with Quality Score 4 or lower",
         "; ".join(sorted({g(r, 'ad_group_criterion', 'keyword', 'text') for r in lowqs})[:15]),
         fix="Check ad relevance and landing page match for these ad groups.")
roles = collections.defaultdict(list)
for r in L("keywords"):
    if g(r, "campaign", "status") == "ENABLED" and g(r, "ad_group_criterion", "status") == "ENABLED":
        roles[g(r, "campaign", "name")].append(g(r, "ad_group_criterion", "keyword", "match_type"))
for camp, mts in roles.items():
    if len(mts) == 1 and mts[0] == "BROAD":
        find("keywords", "high", f"{camp}: a single broad keyword carries the campaign",
             "One broad keyword gives Google full control over which searches qualify.", fix="Rebuild with themed phrase/exact keywords.")

# ------------------------------------------------------------------ search terms
st = collections.defaultdict(lambda: {"clicks": 0, "cost": 0.0, "conv": 0.0, "camps": set(), "cost_by_role": collections.Counter()})
for r in L("search_terms"):
    q = norm(g(r, "search_term_view", "search_term", default="")); m = r.get("metrics", {})
    x = st[q]; x["clicks"] += int(m.get("clicks", 0)); x["cost"] += money(m.get("cost_micros")); x["conv"] += float(m.get("conversions", 0))
    x["camps"].add(g(r, "campaign", "name")); x["cost_by_role"][role_of(cfg, g(r, "campaign", "name", default=""))] += money(m.get("cost_micros"))
hist_days = json.loads((work_dir(cfg, "data") / "_pull.json").read_text()).get("history_days", "?") if (work_dir(cfg, "data") / "_pull.json").exists() else "?"
st_cost = sum(x["cost"] for x in st.values())
st_waste = sum(x["cost"] for x in st.values() if x["conv"] == 0)
if st_cost:
    top = sorted(((q, x) for q, x in st.items() if x["conv"] == 0), key=lambda i: -i[1]["cost"])[:15]
    find("search_terms", "high" if st_waste / st_cost > 0.35 else "medium",
         f"{st_waste / st_cost:.0%} of search term spend (${st_waste:,.0f} of ${st_cost:,.0f}, last {hist_days} days) produced no conversion",
         "Top: " + "; ".join(f"{q} (${x['cost']:,.0f})" for q, x in top), dollars=st_waste,
         fix="Run the negative-keyword-audit skill. Do not negate a term that converted elsewhere.")
comp_words = [norm(c) for c in cfg.get("competitors", [])]
if comp_words:
    leak = [(q, x["cost_by_role"]["generic"]) for q, x in st.items()
            if x["cost_by_role"]["generic"] > 0 and any(f" {w} " in f" {q} " for w in comp_words)]
    if leak:
        cost = sum(c for _, c in leak)
        find("search_terms", "medium", f"Competitor searches spent ${cost:,.0f} in generic campaigns (last {hist_days} days)",
             "; ".join(f"{q} (${c:,.0f})" for q, c in sorted(leak, key=lambda i: -i[1])[:10]), dollars=cost,
             fix="Add competitor names as negatives on generic campaigns so they route to the competitor campaign (or stop).")

# ------------------------------------------------------------------ negatives
converting = {q: x for q, x in st.items() if x["conv"] > 0}
attach = collections.defaultdict(list)
for r in L("list_attachments"):
    if g(r, "campaign_shared_set", "status") == "ENABLED" and g(r, "campaign", "status") == "ENABLED":
        attach[g(r, "shared_set", "name")].append(g(r, "campaign", "name"))
allow = []
nd = niche_dir(cfg)
for p_ in ([nd / "allow-list.txt"] if nd else []) + [work_dir(cfg) / "allow-list.txt"]:
    if p_.exists():
        allow += [norm(l) for l in p_.read_text().splitlines() if l.strip() and not l.startswith("#")]
enabled_camps = {g(r, "campaign", "name") for r in L("campaigns") if g(r, "campaign", "status") == "ENABLED"}
neg_by_camp = collections.defaultdict(list)   # campaign -> [(text, match, source)]
for r in L("shared_criteria"):
    if g(r, "shared_set", "type") == "NEGATIVE_KEYWORDS":
        for c in attach.get(g(r, "shared_set", "name"), []):
            neg_by_camp[c].append((g(r, "shared_criterion", "keyword", "text"), g(r, "shared_criterion", "keyword", "match_type"),
                                   f"list '{g(r, 'shared_set', 'name')}'"))
for r in L("campaign_negatives"):
    neg_by_camp[g(r, "campaign", "name")].append((g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type"),
                                                 "campaign negative"))
bad = []
for q, x in converting.items():
    served = (x["camps"] & enabled_camps)
    if not served:
        continue
    blockers = {c: [f"{t} [{m}] ({src})" for t, m, src in neg_by_camp.get(c, []) if blocks(t, m, q)] for c in served}
    if all(blockers.values()):   # every enabled campaign that ever served this converting search now blocks it
        bad.append((q, x["conv"], sorted({b for v in blockers.values() for b in v})[:3]))
if bad:
    find("negatives", "high", f"{len(bad)} searches that converted can no longer show in any campaign that served them",
         "; ".join(f"'{q}' ({conv:.1f} conv) blocked by {', '.join(b)}" for q, conv, b in sorted(bad, key=lambda i: -i[1])[:12]),
         fix="Remove or narrow these negatives (negative-keyword-audit skill). Routing a search to another campaign is fine; blocking it everywhere is not.")
gen_enabled = [c for c in enabled_camps if role_of(cfg, c) == "generic"]
al_bad = collections.defaultdict(set)
for q in allow:
    for c in gen_enabled:
        for t, m, src in neg_by_camp.get(c, []):
            if blocks(t, m, q):
                al_bad[f"{t} [{m}] ({src})"].add(q)
for r in L("adgroup_negatives"):
    if g(r, "campaign", "status") == "ENABLED" and role_of(cfg, g(r, "campaign", "name", default="")) == "generic":
        t, m = g(r, "ad_group_criterion", "keyword", "text"), g(r, "ad_group_criterion", "keyword", "match_type")
        for q in allow:
            if blocks(t, m, q):
                al_bad[f"{t} [{m}] (ad group {g(r, 'ad_group', 'name')})"].add(q)
if al_bad:
    find("negatives", "high", f"{len(al_bad)} negatives on generic campaigns block searches on the customer allow-list",
         "; ".join(f"{k} blocks {', '.join(sorted(v)[:3])}" for k, v in list(al_bad.items())[:12]),
         fix="Remove or narrow them. These are searches real customers type.")
unattached = [r for r in L("shared_sets") if g(r, "shared_set", "type") == "NEGATIVE_KEYWORDS" and not attach.get(g(r, "shared_set", "name"))]
if unattached:
    find("negatives", "low", f"{len(unattached)} negative lists are not attached to any campaign",
         ", ".join(g(r, "shared_set", "name") for r in unattached), fix="Attach them or delete them.")
n_lists = len([r for r in L("shared_sets") if g(r, "shared_set", "type") == "NEGATIVE_KEYWORDS"])
if n_lists > 8:
    find("negatives", "medium", f"{n_lists} negative keyword lists",
         "List sprawl hides conflicts. Five to seven themed lists are easier to audit.", fix="Consolidate (negative-keyword-audit skill).")
brand = [norm(b) for b in cfg.get("brand_terms", [])]
if brand:
    gen_camps = {g(r, "campaign", "name") for r in L("campaigns") if g(r, "campaign", "status") == "ENABLED"
                 and role_of(cfg, g(r, "campaign", "name", default="")) in ("generic", "competitors")}
    covered = {c for c, ns in neg_by_camp.items() if any(norm(t) == b for t, m, src in ns for b in brand)}
    for c in sorted(gen_camps - covered):
        find("negatives", "low", f"{c}: own brand is not a negative", "Brand searches can be bought at generic CPCs.",
             fix="Add brand terms as phrase negatives on non-brand campaigns.")

# ------------------------------------------------------------------ ads and assets
ads = L("ads")
per_ag = collections.Counter((g(r, "campaign", "name"), g(r, "ad_group", "name")) for r in ads
                             if g(r, "ad_group_ad", "status") == "ENABLED" and g(r, "ad_group_ad", "ad", "type") == "RESPONSIVE_SEARCH_AD")
weak = [r for r in ads if g(r, "ad_group_ad", "status") == "ENABLED" and g(r, "ad_group_ad", "ad_strength") in ("POOR", "AVERAGE")]
if weak:
    find("ads", "medium", f"{len(weak)} enabled RSAs rated Poor or Average",
         "; ".join(sorted({f"{g(r, 'campaign', 'name')} / {g(r, 'ad_group', 'name')}" for r in weak})[:10]),
         fix="Run the generate-ads skill for these ad groups.")
for status, sev, note in (("DISAPPROVED", "high", "These ads do not run."),
                          ("APPROVED_LIMITED", "low", "Limited ads still run, but not everywhere. On competitor campaigns this is usually trademark limits and expected.")):
    rows_ = [r for r in ads if g(r, "ad_group_ad", "status") == "ENABLED" and g(r, "ad_group_ad", "policy_summary", "approval_status") == status]
    if rows_:
        find("ads", sev, f"{len(rows_)} enabled ads {status.lower().replace('_', ' ')}", note + " " + "; ".join(
            sorted({f"{g(r, 'campaign', 'name')} / {g(r, 'ad_group', 'name')}" for r in rows_})[:10]), fix="Open Policy manager and fix what is fixable.")
asset_counts = collections.Counter()
for r in L("assets_campaign") + L("assets_customer"):
    st_ = g(r, "campaign_asset", "status") or g(r, "customer_asset", "status")
    if st_ == "ENABLED":
        asset_counts[g(r, "campaign_asset", "field_type") or g(r, "customer_asset", "field_type")] += 1
for ft, need in (("SITELINK", 4), ("CALLOUT", 4), ("STRUCTURED_SNIPPET", 1), ("CALL", 1)):
    if asset_counts.get(ft, 0) < need:
        find("ads", "medium" if ft in ("SITELINK", "CALLOUT") else "low", f"Only {asset_counts.get(ft, 0)} {ft.lower()} assets",
             "Assets add CTR at no extra cost.", fix=f"Add at least {need} (generate-ads skill writes them).")

# ------------------------------------------------------------------ device and trend
dev = collections.defaultdict(lambda: [0.0, 0.0])
for r in L("device"):
    d = g(r, "segments", "device"); m = r.get("metrics", {})
    dev[d][0] += money(m.get("cost_micros")); dev[d][1] += float(m.get("conversions", 0))
month = collections.defaultdict(lambda: [0.0, 0.0])
for r in L("campaign_month"):
    mo = g(r, "segments", "month"); m = r.get("metrics", {})
    month[mo][0] += money(m.get("cost_micros")); month[mo][1] += float(m.get("conversions", 0))
ch = collections.Counter((g(r, "change_event", "user_email") or "?", g(r, "change_event", "client_type")) for r in L("change_history"))

# ------------------------------------------------------------------ write
out = work_dir(cfg, "audit")
order = {"high": 0, "medium": 1, "low": 2}
F.sort(key=lambda f: (order[f["severity"]], -(f["dollars"] or 0)))
(out / "findings.json").write_text(json.dumps({"account_cpa": acct_cpa, "totals": dict(tot), "campaigns": camp_rows, "findings": F}, indent=1, default=str))
lines = [f"# Audit fact sheet: {cust.get('descriptive_name', cfg['slug'])}", "",
         f"Recent window spend ${tot['cost']:,.0f}, conversions {tot['conv']:.1f}, CPA "
         + (f"${acct_cpa:,.0f}" if acct_cpa else "n/a") + f". Zero-conversion spend threshold used: ${waste_floor:,.0f}.", "",
         "## Campaigns", "", "| Campaign | Role | Type | Spend | Conv | CPA | IS | Lost to budget |", "|---|---|---|---|---|---|---|---|"]
for c in camp_rows:
    if c["cost"] == 0 and c["status"] != "ENABLED":
        continue
    pct = lambda v: f"{float(v):.0%}" if v not in (None, "") else ""
    lines.append(f"| {c['campaign']} | {c['role']} | {c['type']} | ${c['cost']:,} | {c['conv']} | {('$' + format(c['cpa'], ',')) if c['cpa'] else ''} | {pct(c['is'])} | {pct(c['lost_budget'])} |")
lines += ["", "## Monthly trend", "", "| Month | Spend | Conv | CPA |", "|---|---|---|---|"]
for mo, (cost, conv) in sorted(month.items())[-12:]:
    lines.append(f"| {mo} | ${cost:,.0f} | {conv:.1f} | {('$' + format(cost / conv, ',.0f')) if conv else ''} |")
lines += ["", "## Device", "", "| Device | Spend | Conv | CPA |", "|---|---|---|---|"]
for d, (cost, conv) in sorted(dev.items(), key=lambda i: -i[1][0]):
    lines.append(f"| {d} | ${cost:,.0f} | {conv:.1f} | {('$' + format(cost / conv, ',.0f')) if conv else ''} |")
lines += ["", "## Conversion actions (enabled)", "", "| Action | Category | Origin | Primary | Default value |", "|---|---|---|---|---|"]
for x in enabled:
    lines.append(f"| {x.get('name')} | {x.get('category')} | {x.get('origin')} | {'yes' if x.get('primary_for_goal') else ''} | {g(x, 'value_settings', 'default_value', default='')} |")
lines += ["", "## Who changed the account (last 30 days)", ""] + [f"- {u} via {c}: {n} changes" for (u, c), n in ch.most_common(8)]
lines += ["", f"## Findings ({len(F)})", ""]
for f in F:
    lines.append(f"- **[{f['severity']}] {f['area']}: {f['title']}**" + (f" (${f['dollars']:,})" if f["dollars"] else ""))
    lines.append(f"  - Evidence: {f['evidence']}")
    if f["suggested_fix"]:
        lines.append(f"  - Fix: {f['suggested_fix']}")
(out / "facts.md").write_text("\n".join(lines) + "\n")
print(f"{len(F)} findings ({sum(1 for f in F if f['severity'] == 'high')} high). Wrote {out / 'facts.md'} and findings.json")
