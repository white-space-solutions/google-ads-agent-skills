"""Read-only conversion signal check. Run daily or before any audit.

Answers: is every conversion pipe firing, who writes to each action, did values move,
and is bidding pointed at the right actions?

  python scripts/conversion_health.py --client clients/acme.yaml
Writes work/<slug>/reviews/conversion-health-<date>.md
"""
import collections
import datetime as dt

from gads import arg_parser, api_error, client, g, load_config, run, work_dir

a = arg_parser("Conversion signal health").parse_args()
cfg = load_config(a.client)
cid = cfg["customer_id"]
ga = client(cfg).get_service("GoogleAdsService")
today = dt.date.today()
L = [f"# Conversion health {today}", ""]


def q(query):
    try:
        return run(ga, cid, query)
    except Exception as e:
        L.append(f"(query failed: {api_error(e)})")
        return []


cust = (q("SELECT customer.descriptive_name, customer.auto_tagging_enabled, customer.conversion_tracking_setting.conversion_tracking_status FROM customer") or [{}])[0].get("customer", {})
L += [f"Account: {cust.get('descriptive_name')}. Auto-tagging: {cust.get('auto_tagging_enabled')}. "
      f"Conversion tracking: {g(cust, 'conversion_tracking_setting', 'conversion_tracking_status')}. "
      "Check enhanced conversions for leads in Goals > Settings (the API does not expose it on the customer).", ""]

meta = {g(r, "conversion_action", "name"): r["conversion_action"] for r in q(
    "SELECT conversion_action.name, conversion_action.status, conversion_action.category, conversion_action.type, conversion_action.origin, "
    "conversion_action.primary_for_goal, conversion_action.value_settings.default_value FROM conversion_action WHERE conversion_action.status = 'ENABLED'")}
daily = collections.defaultdict(dict)
for r in q(f"SELECT segments.conversion_action_name, segments.date, metrics.all_conversions, metrics.all_conversions_value FROM customer "
           f"WHERE segments.date BETWEEN '{today - dt.timedelta(days=90)}' AND '{today}'"):
    m = r.get("metrics", {})
    daily[g(r, "segments", "conversion_action_name")][g(r, "segments", "date")] = (float(m.get("all_conversions", 0)), float(m.get("all_conversions_value", 0)))

L += ["## Actions", "", "| | Action | Primary | Last conversion | 90d conv | Value/conv last 30d | Value/conv prior 60d | Category / origin |", "|---|---|---|---|---|---|---|---|"]
alerts = []
for name, x in sorted(meta.items(), key=lambda kv: -sum(v[0] for v in daily.get(kv[0], {}).values())):
    d = daily.get(name, {})
    hits = sorted(k for k, v in d.items() if v[0] > 0)
    last = hits[-1] if hits else None
    age = (today - dt.date.fromisoformat(last)).days if last else None
    conv90 = sum(v[0] for v in d.values())
    cut = str(today - dt.timedelta(days=30))
    rc = sum(v[0] for k, v in d.items() if k >= cut); rv = sum(v[1] for k, v in d.items() if k >= cut)
    pc = sum(v[0] for k, v in d.items() if k < cut); pv = sum(v[1] for k, v in d.items() if k < cut)
    vr = rv / rc if rc else None; vp = pv / pc if pc else None
    active_days = len(hits)
    normal_gap = max(7, 2 * 90 / active_days) if active_days else 7   # low-volume actions convert less often; judge against their own cadence
    mark = "OK" if age is not None and age <= normal_gap else ("WATCH" if age is not None and age <= max(30, 3 * normal_gap) else "DEAD")
    if x.get("primary_for_goal") and mark != "OK":
        alerts.append(f"Primary action '{name}' last converted {last or 'never in 90 days'} (normal gap about {normal_gap:.0f} days).")
    if vr and vp and (vr / vp > 1.5 or vp / vr > 1.5):
        alerts.append(f"'{name}' value per conversion moved from ${vp:,.0f} to ${vr:,.0f}.")
    L.append(f"| {mark} | {name} | {'yes' if x.get('primary_for_goal') else ''} | {last or '-'} | {conv90:.1f} | "
             f"{('$' + format(vr, ',.0f')) if vr else '-'} | {('$' + format(vp, ',.0f')) if vp else '-'} | {x.get('category')} / {x.get('origin')} |")

L += ["", "## Offline upload pipelines", ""]
writers = collections.defaultdict(set)
for r in q("SELECT offline_conversion_upload_conversion_action_summary.conversion_action_name, offline_conversion_upload_conversion_action_summary.client, "
           "offline_conversion_upload_conversion_action_summary.status, offline_conversion_upload_conversion_action_summary.total_event_count, "
           "offline_conversion_upload_conversion_action_summary.successful_event_count, "
           "offline_conversion_upload_conversion_action_summary.last_upload_date_time FROM offline_conversion_upload_conversion_action_summary"):
    s = r["offline_conversion_upload_conversion_action_summary"]
    writers[s.get("conversion_action_name")].add(s.get("client"))
    tot, ok = int(s.get("total_event_count", 0)), int(s.get("successful_event_count", 0))
    L.append(f"- {s.get('conversion_action_name')}: client {s.get('client')}, status {s.get('status')}, last upload {s.get('last_upload_date_time')}, "
             f"{ok}/{tot} events ok")
    if tot and ok / tot < 0.9:
        alerts.append(f"Uploads to '{s.get('conversion_action_name')}' via {s.get('client')}: only {ok}/{tot} events succeeded.")
for n, cl in writers.items():
    if len(cl) > 1:
        alerts.append(f"'{n}' has {len(cl)} upload clients ({', '.join(sorted(map(str, cl)))}). One owner per action.")
if not writers:
    L.append("No offline uploads in the last 90 days.")

L += ["", "## What each campaign bids toward", ""]
goals = collections.defaultdict(list)
for r in q("SELECT campaign.name, campaign_conversion_goal.category, campaign_conversion_goal.origin, campaign_conversion_goal.biddable "
           "FROM campaign_conversion_goal WHERE campaign.status = 'ENABLED'"):
    if g(r, "campaign_conversion_goal", "biddable"):
        goals[g(r, "campaign", "name")].append(f"{g(r, 'campaign_conversion_goal', 'category')}/{g(r, 'campaign_conversion_goal', 'origin')}")
L += [f"- {c}: {', '.join(sorted(v))}" for c, v in sorted(goals.items())] or ["(no goal data)"]
if cust and not cust.get("auto_tagging_enabled"):
    alerts.append("Auto-tagging is off: uploads cannot match GCLIDs.")
L[2:2] = ["## Alerts", ""] + ([f"- {x}" for x in alerts] or ["- None."]) + [""]
p = work_dir(cfg, "reviews") / f"conversion-health-{today}.md"
p.write_text("\n".join(L) + "\n")
print(f"{len(alerts)} alerts. Wrote {p}")
