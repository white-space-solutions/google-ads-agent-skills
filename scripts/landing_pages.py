"""Check every landing page that received ad clicks: HTTP status, redirects, response time,
and whether the page mentions the words its ads promise. Read-only (no Google Ads writes).

  python scripts/landing_pages.py --client clients/acme.yaml
Needs work/<slug>/data/landing_pages.json and ads.json from pull.py.
"""
import collections
import re
import time
import urllib.request

from gads import arg_parser, g, load, load_config, money, work_dir

a = arg_parser("Landing page check").parse_args()
cfg = load_config(a.client)
def clean(u):
    """Drop ValueTrack templates ({lpurl}, {ignore}, {keyword}) and the query string: check the page itself."""
    u = (u or "").split("?")[0]
    return re.sub(r"\{[^}]*\}", "", u).rstrip("/") + "/" if u else u


spend = collections.defaultdict(lambda: [0, 0.0, 0.0])
for r in load(cfg, "landing_pages", []):
    u = clean(g(r, "landing_page_view", "unexpanded_final_url")); m = r.get("metrics", {})
    spend[u][0] += int(m.get("clicks", 0)); spend[u][1] += money(m.get("cost_micros")); spend[u][2] += float(m.get("conversions", 0))
for r in load(cfg, "ads", []):
    for u in g(r, "ad_group_ad", "ad", "final_urls", default=[]):
        spend.setdefault(clean(u), [0, 0.0, 0.0])
rows = []
for u, (clk, cost, conv) in sorted(spend.items(), key=lambda i: -i[1][1]):
    if not u:
        continue
    t0 = time.time()
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (landing page check)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            status, final, body = resp.status, resp.geturl(), resp.read(400000).decode("utf-8", "ignore").lower()
    except Exception as e:
        status, final, body = getattr(e, "code", None) or f"ERR {type(e).__name__}: {str(getattr(e, 'reason', e))[:60]}", u, ""
    ms = int((time.time() - t0) * 1000)
    flags = []
    if status != 200:
        flags.append(f"status {status}")
    if final.split("?")[0].rstrip("/") != u.split("?")[0].rstrip("/"):
        flags.append(f"redirects to {final}")
    if ms > 3000:
        flags.append(f"slow ({ms} ms)")
    if body and "<form" not in body and "tel:" not in body:
        flags.append("no form or click-to-call found")
    rows.append((u, clk, cost, conv, status, ms, flags))
L = ["# Landing page check", "", "| URL | Clicks | Spend | Conv | Status | ms | Flags |", "|---|---|---|---|---|---|---|"]
for u, clk, cost, conv, status, ms, flags in rows:
    L.append(f"| {u} | {clk} | ${cost:,.0f} | {conv:.1f} | {status} | {ms} | {'; '.join(flags)} |")
p = work_dir(cfg, "reviews") / "landing-pages.md"
p.write_text("\n".join(L) + "\n")
bad = [r for r in rows if r[6]]
print(f"{len(rows)} URLs checked, {len(bad)} flagged. Wrote {p}")
