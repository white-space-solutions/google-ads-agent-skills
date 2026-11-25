"""Build a complete Search campaign from a YAML spec. DRY RUN by default.

One spec file describes one campaign: budget, bidding, locations, languages, schedule, negative
lists to attach, campaign assets (sitelinks, callouts, structured snippets, call), ad groups,
keywords and responsive search ads. See niches/real-estate-investors/campaign-template.yaml.

Everything goes to Google in ONE atomic request (temporary IDs link the pieces), so either the
whole campaign is created or nothing is. The dry run sends that request with validate_only:
Google checks every field and every ad against policy, and nothing changes.

Safety, on top of gads.guard_write (allowlist, op cap, APPLY_ENABLED=1 + --execute):
  - The campaign is always created PAUSED. Turning it on is a separate, deliberate step (--enable).
  - Refuses if a campaign with the same name exists (no duplicates on a rerun).
  - Refuses if the daily budget is above safety.max_daily_budget in the client yaml.
  - Every RSA and asset must pass scripts/validate_ad.py with 0 errors.
  - Refuses if a keyword would be blocked by a negative list it is attached to (born blocked),
    and warns when a keyword matches the niche negatives or names a competitor.
  - Writes are logged to work/<slug>/changes.log.jsonl; the created resource names are saved
    next to the spec as <spec>.applied.json.

  python scripts/campaign_build.py --client clients/acme.yaml --spec work/acme/build/sell-fast.yaml
  APPLY_ENABLED=1 python scripts/campaign_build.py --client clients/acme.yaml --spec ... --execute
  # after reviewing it in the UI:
  python scripts/campaign_build.py --client clients/acme.yaml --enable "Sell House Fast - Springfield"            # dry run
  APPLY_ENABLED=1 python scripts/campaign_build.py --client clients/acme.yaml --enable "..." --execute
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from gads import (api_error, arg_parser, blocks, client, g, guard_write, load_config, log_change, niche_dir, norm,
                  run, work_dir)
from validate_ad import validate

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
MATCHES = {"EXACT", "PHRASE", "BROAD"}


# ------------------------------------------------------------------ spec parsing (no API)

def parse_keyword(k, default_match="PHRASE"):
    """'[text]' = exact, '"text"' = phrase, plain = the ad group's default_match.
    A dict {text, match} also works."""
    if isinstance(k, dict):
        return norm(k["text"]), str(k.get("match", default_match)).upper()
    k = str(k).strip()
    if k.startswith("[") and k.endswith("]"):
        return norm(k[1:-1]), "EXACT"
    if len(k) > 1 and k[0] == k[-1] == '"':
        return norm(k[1:-1]), "PHRASE"
    return norm(k), default_match.upper()


def check_spec(spec: dict, cfg: dict) -> tuple[list[str], list[str]]:
    """Static checks. Returns (errors, warnings)."""
    E, W = [], []
    c = spec.get("campaign") or {}
    if not c.get("name"):
        E.append("campaign.name is required")
    try:
        budget = float(c.get("daily_budget", 0))
    except (TypeError, ValueError):
        budget = 0
    if budget <= 0:
        E.append("campaign.daily_budget must be a positive number (account currency per day)")
    cap = cfg["safety"].get("max_daily_budget")
    if cap is None:
        W.append("safety.max_daily_budget is not set in the client yaml; budget is unchecked")
    elif budget > float(cap):
        E.append(f"daily_budget {budget} is above safety.max_daily_budget {cap}")
    bidding = str(c.get("bidding", "maximize_conversions")).lower()
    if bidding not in {"maximize_conversions", "manual_cpc", "maximize_clicks"}:
        E.append(f"campaign.bidding '{bidding}' must be maximize_conversions, manual_cpc or maximize_clicks")
    if not c.get("locations"):
        E.append("campaign.locations needs at least one geo target constant ID (see docs/playbook/01-account-structure.md)")
    if str(c.get("location_option", "presence")).lower() not in {"presence", "presence_or_interest"}:
        E.append("campaign.location_option must be presence or presence_or_interest")
    for s in c.get("ad_schedule") or []:
        for d in s.get("days", []):
            if str(d).upper() not in DAYS:
                E.append(f"ad_schedule day '{d}' is not a weekday name")
        if not (0 <= int(s.get("start_hour", 0)) < int(s.get("end_hour", 24)) <= 24):
            E.append(f"ad_schedule hours must satisfy 0 <= start_hour < end_hour <= 24: {s}")

    assets = spec.get("assets") or {}
    a_check = {"headlines": [{"text": "x"}] * 3, "descriptions": ["x" * 65] * 2,
               "sitelinks": assets.get("sitelinks") or [], "callouts": assets.get("callouts") or [],
               "structured_snippets": assets.get("structured_snippets") or []}
    for lvl, msg in validate(a_check):
        if "headline" in msg or "description" in msg.split(":")[0]:
            continue
        (E if lvl == "ERROR" else W).append(f"assets: {msg}")
    for s in assets.get("sitelinks") or []:
        if not str(s.get("final_url", "")).startswith("https://"):
            E.append(f"sitelink '{s.get('title')}' needs an https final_url")

    ags = spec.get("ad_groups") or []
    if not ags:
        E.append("at least one ad group is required")
    names = set()
    for ag in ags:
        n = ag.get("name")
        if not n:
            E.append("every ad group needs a name"); continue
        if n in names:
            E.append(f"duplicate ad group name '{n}'")
        names.add(n)
        if bidding == "manual_cpc" and not ag.get("cpc_bid"):
            E.append(f"{n}: manual_cpc needs cpc_bid on every ad group")
        kws = [parse_keyword(k, ag.get("default_match", "PHRASE")) for k in ag.get("keywords") or []]
        if not kws:
            E.append(f"{n}: no keywords")
        for t, m in kws:
            if m not in MATCHES:
                E.append(f"{n}: keyword '{t}' has match type {m}")
            if len(t) > 80 or len(t.split()) > 10:
                E.append(f"{n}: keyword '{t}' is over 80 characters or 10 words")
        if len(set(kws)) != len(kws):
            W.append(f"{n}: duplicate keywords will be skipped")
        ads = ag.get("ads") or []
        if not ads:
            E.append(f"{n}: no ads")
        if len(ads) > 3:
            E.append(f"{n}: {len(ads)} RSAs; Google allows 3 enabled RSAs per ad group")
        for i, ad in enumerate(ads, 1):
            url = ad.get("final_url") or ag.get("final_url")
            if not str(url or "").startswith("https://"):
                E.append(f"{n} ad {i}: needs an https final_url (on the ad or the ad group)")
            for lvl, msg in validate(ad):
                (E if lvl == "ERROR" else W).append(f"{n} ad {i}: {msg}")
    return E, W


def niche_negatives(cfg: dict) -> list[tuple[str, str]]:
    nd = niche_dir(cfg)
    p = nd / "negatives.yaml" if nd else None
    if not p or not p.exists():
        return []
    out = []
    for l in (yaml.safe_load(p.read_text()) or {}).get("lists", []):
        for ts in (l.get("groups") or {}).values():
            out += [(norm(t), l.get("match", "PHRASE")) for t in ts or []]
    return out


def keyword_conflicts(spec, cfg, list_terms):
    """list_terms: {(text, match)} from the negative lists this campaign will attach.
    Returns (errors, warnings)."""
    E, W = [], []
    niche = niche_negatives(cfg)
    comps = [norm(x) for x in cfg.get("competitors", [])]
    camp_negs = [(norm(x["term"] if isinstance(x, dict) else x), (x.get("match", "PHRASE") if isinstance(x, dict) else "PHRASE"))
                 for x in (spec["campaign"].get("negative_keywords") or [])]
    for ag in spec.get("ad_groups") or []:
        for k in ag.get("keywords") or []:
            t, _ = parse_keyword(k, ag.get("default_match", "PHRASE"))
            hit = [f"{n} ({m})" for n, m in list(list_terms) + camp_negs if blocks(n, m, t)]
            if hit:
                E.append(f"{ag['name']}: keyword '{t}' is blocked by negatives {hit[:3]}")
            nh = [n for n, m in niche if blocks(n, m, t)]
            if nh:
                W.append(f"{ag['name']}: keyword '{t}' matches niche negatives {nh[:3]}; check it is intended")
            ch = [x for x in comps if x and f" {x} " in f" {t} "]
            if ch:
                W.append(f"{ag['name']}: keyword '{t}' names a competitor {ch}; keep it in a Competitors campaign")
    return E, W


# ------------------------------------------------------------------ operations

def build_ops(c, cid: str, spec: dict, lists: dict[str, str]) -> tuple[list, dict]:
    """Return (MutateOperations, summary). Temporary IDs (negative numbers) link new objects."""
    ga = c.get_service("GoogleAdsService")
    E = c.enums
    cs = spec["campaign"]
    ops, summary = [], {"ad_groups": 0, "keywords": 0, "ads": 0, "assets": 0, "criteria": 0}
    tmp = iter(range(-1, -100000, -1))

    def op():
        o = c.get_type("MutateOperation"); ops.append(o); return o

    budget_rn = ga.campaign_budget_path(cid, next(tmp))
    o = op(); b = o.campaign_budget_operation.create
    b.resource_name = budget_rn
    b.name = f"{cs['name']} budget"
    b.amount_micros = int(round(float(cs["daily_budget"]) * 1e6))
    b.delivery_method = E.BudgetDeliveryMethodEnum.STANDARD
    b.explicitly_shared = False

    camp_rn = ga.campaign_path(cid, next(tmp))
    o = op(); k = o.campaign_operation.create
    k.resource_name = camp_rn
    k.name = cs["name"]
    k.status = E.CampaignStatusEnum.PAUSED
    k.advertising_channel_type = E.AdvertisingChannelTypeEnum.SEARCH
    k.campaign_budget = budget_rn
    k.network_settings.target_google_search = True
    k.network_settings.target_search_network = bool(cs.get("search_partners", False))
    k.network_settings.target_content_network = False
    k.network_settings.target_partner_search_network = False
    k.geo_target_type_setting.positive_geo_target_type = (
        E.PositiveGeoTargetTypeEnum.PRESENCE if str(cs.get("location_option", "presence")).lower() == "presence"
        else E.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST)
    k.geo_target_type_setting.negative_geo_target_type = E.NegativeGeoTargetTypeEnum.PRESENCE
    try:
        k.contains_eu_political_advertising = E.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
    except AttributeError:
        pass
    if cs.get("final_url_suffix"):
        k.final_url_suffix = cs["final_url_suffix"]
    bidding = str(cs.get("bidding", "maximize_conversions")).lower()
    # Assign whole messages: setting only default values (0, False) would leave the bidding oneof unset.
    if bidding == "manual_cpc":
        k.manual_cpc = c.get_type("ManualCpc")
    elif bidding == "maximize_clicks":
        ts = c.get_type("TargetSpend")
        if cs.get("max_cpc"):
            ts.cpc_bid_ceiling_micros = int(round(float(cs["max_cpc"]) * 1e6))
        k.target_spend = ts
    else:
        mc = c.get_type("MaximizeConversions")
        if cs.get("target_cpa"):
            mc.target_cpa_micros = int(round(float(cs["target_cpa"]) * 1e6))
        k.maximize_conversions = mc

    def crit():
        o = op(); x = o.campaign_criterion_operation.create; x.campaign = camp_rn
        summary["criteria"] += 1
        return x
    for gid in cs.get("locations") or []:
        crit().location.geo_target_constant = f"geoTargetConstants/{int(gid)}"
    for gid in cs.get("excluded_locations") or []:
        x = crit(); x.negative = True; x.location.geo_target_constant = f"geoTargetConstants/{int(gid)}"
    for lid in cs.get("languages") or [1000]:
        crit().language.language_constant = f"languageConstants/{int(lid)}"
    for s in cs.get("ad_schedule") or []:
        for d in s["days"]:
            x = crit()
            x.ad_schedule.day_of_week = getattr(E.DayOfWeekEnum, str(d).upper())
            x.ad_schedule.start_hour = int(s.get("start_hour", 0))
            x.ad_schedule.end_hour = int(s.get("end_hour", 24))
            x.ad_schedule.start_minute = E.MinuteOfHourEnum.ZERO
            x.ad_schedule.end_minute = E.MinuteOfHourEnum.ZERO
    for neg in cs.get("negative_keywords") or []:
        t, m = (neg["term"], neg.get("match", "PHRASE")) if isinstance(neg, dict) else (neg, "PHRASE")
        x = crit(); x.negative = True
        x.keyword.text = norm(t); x.keyword.match_type = getattr(E.KeywordMatchTypeEnum, m.upper())
    for ln in cs.get("negative_lists") or []:
        o = op(); x = o.campaign_shared_set_operation.create
        x.campaign = camp_rn; x.shared_set = lists[ln]

    # campaign assets
    assets = spec.get("assets") or {}
    FT = E.AssetFieldTypeEnum

    def asset(field_type):
        rn = ga.asset_path(cid, next(tmp))
        o = op(); a = o.asset_operation.create; a.resource_name = rn
        o2 = op(); l = o2.campaign_asset_operation.create
        l.campaign = camp_rn; l.asset = rn; l.field_type = field_type
        summary["assets"] += 1
        return a
    for s in assets.get("sitelinks") or []:
        a = asset(FT.SITELINK)
        a.sitelink_asset.link_text = s["title"]
        if s.get("description_1"):
            a.sitelink_asset.description1 = s["description_1"]
        if s.get("description_2"):
            a.sitelink_asset.description2 = s["description_2"]
        a.final_urls.append(s["final_url"])
    for t in assets.get("callouts") or []:
        asset(FT.CALLOUT).callout_asset.callout_text = t
    for s in assets.get("structured_snippets") or []:
        a = asset(FT.STRUCTURED_SNIPPET)
        a.structured_snippet_asset.header = s["header"]
        a.structured_snippet_asset.values.extend(s["values"])
    call = assets.get("call")
    if call and call.get("phone_number"):
        a = asset(FT.CALL)
        a.call_asset.phone_number = str(call["phone_number"])
        a.call_asset.country_code = str(call.get("country_code", "US"))

    # ad groups, keywords, ads
    for ag in spec["ad_groups"]:
        ag_rn = ga.ad_group_path(cid, next(tmp))
        o = op(); x = o.ad_group_operation.create
        x.resource_name = ag_rn; x.name = ag["name"]; x.campaign = camp_rn
        x.status = E.AdGroupStatusEnum.ENABLED
        x.type_ = E.AdGroupTypeEnum.SEARCH_STANDARD
        if ag.get("cpc_bid"):
            x.cpc_bid_micros = int(round(float(ag["cpc_bid"]) * 1e6))
        summary["ad_groups"] += 1
        for t, m in dict.fromkeys(parse_keyword(k, ag.get("default_match", "PHRASE")) for k in ag["keywords"]):
            o = op(); y = o.ad_group_criterion_operation.create
            y.ad_group = ag_rn; y.status = E.AdGroupCriterionStatusEnum.ENABLED
            y.keyword.text = t; y.keyword.match_type = getattr(E.KeywordMatchTypeEnum, m)
            summary["keywords"] += 1
        for neg in ag.get("negative_keywords") or []:
            t, m = (neg["term"], neg.get("match", "PHRASE")) if isinstance(neg, dict) else (neg, "PHRASE")
            o = op(); y = o.ad_group_criterion_operation.create
            y.ad_group = ag_rn; y.negative = True
            y.keyword.text = norm(t); y.keyword.match_type = getattr(E.KeywordMatchTypeEnum, m.upper())
        for ad in ag["ads"]:
            o = op(); z = o.ad_group_ad_operation.create
            z.ad_group = ag_rn; z.status = E.AdGroupAdStatusEnum.ENABLED
            z.ad.final_urls.append(ad.get("final_url") or ag["final_url"])
            r = z.ad.responsive_search_ad
            for h in ad["headlines"]:
                t = c.get_type("AdTextAsset"); t.text = h["text"]
                if h.get("pin"):
                    t.pinned_field = getattr(E.ServedAssetFieldTypeEnum, f"HEADLINE_{int(h['pin'])}")
                r.headlines.append(t)
            for d in ad["descriptions"]:
                t = c.get_type("AdTextAsset"); t.text = d if isinstance(d, str) else d["text"]
                r.descriptions.append(t)
            if ad.get("path1"):
                r.path1 = ad["path1"]
            if ad.get("path2"):
                r.path2 = ad["path2"]
            summary["ads"] += 1
    return ops, summary


# ------------------------------------------------------------------ main

def main():
    ap = arg_parser("Build a Search campaign from a YAML spec (dry run by default)")
    ap.add_argument("--spec", help="Path to the campaign spec YAML")
    ap.add_argument("--enable", metavar="CAMPAIGN_NAME", help="Turn on a paused campaign this tool built")
    ap.add_argument("--check-only", action="store_true", help="Static checks only, no API calls")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    cfg = load_config(a.client)
    cid = cfg["customer_id"]
    VO = not a.execute

    if a.enable:
        print("MODE:", "DRY RUN (validate_only, nothing changes)" if VO else "EXECUTE")
        c = client(cfg); ga = c.get_service("GoogleAdsService")
        rows = run(ga, cid, "SELECT campaign.resource_name, campaign.name, campaign.status FROM campaign "
                            f"WHERE campaign.name = '{a.enable.replace(chr(39), chr(92) + chr(39))}' AND campaign.status != 'REMOVED'")
        if len(rows) != 1:
            sys.exit(f"Expected exactly one campaign named '{a.enable}', found {len(rows)}.")
        guard_write(cfg, cid, 1, executing=not VO)
        o = c.get_type("CampaignOperation"); o.update.resource_name = g(rows[0], "campaign", "resource_name")
        o.update.status = c.enums.CampaignStatusEnum.ENABLED
        from google.api_core import protobuf_helpers
        c.copy_from(o.update_mask, protobuf_helpers.field_mask(None, o.update._pb))
        c.get_service("CampaignService").mutate_campaigns(request={"customer_id": cid, "operations": [o], "validate_only": VO})
        print(("OK would enable" if VO else "ENABLED") + f" '{a.enable}'")
        if not VO:
            log_change(cfg, "enable campaign", {"campaign": a.enable})
        return

    if not a.spec:
        sys.exit("--spec is required (or use --enable).")
    spec_path = Path(a.spec)
    spec = yaml.safe_load(spec_path.read_text()) or {}
    errs, warns = check_spec(spec, cfg)
    if errs:
        for m in errs:
            print("ERROR:", m)
        for m in warns:
            print("WARNING:", m)
        sys.exit(f"{len(errs)} error(s) in {spec_path}. Fix them and rerun.")
    if a.check_only:
        for m in warns:
            print("WARNING:", m)
        print(f"Spec OK: {len(warns)} warning(s). Rerun without --check-only for Google's dry run.")
        return

    print("MODE:", "DRY RUN (validate_only, nothing changes)" if VO else "EXECUTE")
    c = client(cfg)
    ga = c.get_service("GoogleAdsService")
    cs = spec["campaign"]
    existing = run(ga, cid, "SELECT campaign.name FROM campaign WHERE campaign.status != 'REMOVED'")
    if any(g(r, "campaign", "name") == cs["name"] for r in existing):
        sys.exit(f"Refusing: a campaign named '{cs['name']}' already exists. Rename it in the spec or edit the live one in the UI.")
    lists = {g(r, "shared_set", "name"): g(r, "shared_set", "resource_name") for r in run(ga, cid,
             "SELECT shared_set.name, shared_set.resource_name FROM shared_set "
             "WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND shared_set.status = 'ENABLED'")}
    missing = [n for n in cs.get("negative_lists") or [] if n not in lists]
    if missing:
        sys.exit(f"Negative lists not found in the account: {missing}. Found: {sorted(lists)}")
    terms = set()
    for n in cs.get("negative_lists") or []:
        terms |= {(norm(g(r, "shared_criterion", "keyword", "text")), g(r, "shared_criterion", "keyword", "match_type"))
                  for r in run(ga, cid, "SELECT shared_criterion.keyword.text, shared_criterion.keyword.match_type "
                                        f"FROM shared_criterion WHERE shared_set.resource_name = '{lists[n]}'")}
    if not cs.get("negative_lists"):
        warns.append("no negative_lists attached; a new campaign without negatives buys junk from day one")
    kerr, kwarn = keyword_conflicts(spec, cfg, terms)
    warns += kwarn
    for m in warns:
        print("WARNING:", m)
    if kerr:
        for m in kerr:
            print("ERROR:", m)
        sys.exit("Keywords would be born blocked. Remove them or narrow the negative, then rerun.")

    ops, summary = build_ops(c, cid, spec, lists)
    guard_write(cfg, cid, len(ops), executing=not VO)
    print(f"Campaign '{cs['name']}' (PAUSED): budget {cs['daily_budget']}/day, {cs.get('bidding', 'maximize_conversions')}, "
          f"{summary['ad_groups']} ad groups, {summary['keywords']} keywords, {summary['ads']} RSAs, "
          f"{summary['assets']} assets, {summary['criteria']} targeting criteria, "
          f"{len(cs.get('negative_lists') or [])} negative lists. {len(ops)} operations, one atomic request.")
    try:
        # request= form on purpose: the kwargs form silently ignores validate_only
        res = ga.mutate(request={"customer_id": cid, "mutate_operations": ops, "validate_only": VO})
    except Exception as e:  # GoogleAdsException carries one error per failing field
        errs = getattr(getattr(e, "failure", None), "errors", None)
        if errs:
            for er in errs:
                path = ".".join(f"{p.field_name}[{p.index}]" if p._pb.HasField("index") else p.field_name
                                for p in er.location.field_path_elements)
                print(f"  GOOGLE ERROR {path}: {er.message}")
                pf = getattr(er.details, "policy_finding_details", None)
                for entry in (pf.policy_topic_entries if pf else []):
                    print(f"     policy: {entry.topic} ({entry.type_.name})")
        else:
            print("  GOOGLE ERROR:", api_error(e))
        sys.exit("Google rejected the request. Nothing was created.")
    if VO:
        print("Dry run complete. Google accepted every operation. Nothing changed.")
        return
    created = [r for r in (getattr(x, x._pb.WhichOneof("response")) for x in res.mutate_operation_responses)]
    names = [getattr(r, "resource_name", "") for r in created]
    out = spec_path.with_suffix(".applied.json")
    out.write_text(json.dumps({"campaign": cs["name"], "customer_id": cid, "resource_names": names}, indent=1))
    log_change(cfg, "build campaign", {"campaign": cs["name"], "ops": len(ops), **summary, "record": str(out)})
    print(f"CREATED '{cs['name']}' PAUSED. Resource names saved to {out}.")
    print("Next: review it in the Google Ads UI, then --enable it.")


if __name__ == "__main__":
    main()
