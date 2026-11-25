"""Read-only pull of everything the audit, negative keyword and search term skills need.

Writes one JSON file per query to work/<slug>/data/. Changes nothing in the account.

  python scripts/pull.py --client clients/acme.yaml
  python scripts/pull.py --client clients/acme.yaml --history-days 540   # 18 months of search terms
  python scripts/pull.py --client clients/acme.yaml --only search_terms keywords
"""
import datetime as dt
import json

from gads import api_error, arg_parser, client, date_range, g, load_config, run, save, work_dir

ap = arg_parser("Read-only Google Ads pull")
ap.add_argument("--days", type=int, default=90, help="Recent performance window (default 90)")
ap.add_argument("--history-days", type=int, default=365,
                help="Search term and keyword history window used for negative keyword gates (default 365; 540 = 18 months)")
ap.add_argument("--only", nargs="*", default=[], help="Only these query names")
a = ap.parse_args()
cfg = load_config(a.client)
cid = cfg["customer_id"]
R, H = date_range(a.days), date_range(a.history_days)
end = dt.date.today()

Q = {
    # ---- account and settings
    "customer": "SELECT customer.descriptive_name, customer.currency_code, customer.time_zone, customer.auto_tagging_enabled, "
                "customer.conversion_tracking_setting.conversion_tracking_status, "
                "customer.conversion_tracking_setting.accepted_customer_data_terms, customer.optimization_score FROM customer",
    "campaigns": "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign.advertising_channel_sub_type, "
                 "campaign.bidding_strategy_type, campaign.target_cpa.target_cpa_micros, campaign.maximize_conversions.target_cpa_micros, "
                 "campaign.maximize_conversion_value.target_roas, campaign.target_spend.cpc_bid_ceiling_micros, "
                 "campaign.network_settings.target_google_search, campaign.network_settings.target_search_network, "
                 "campaign.network_settings.target_content_network, campaign.geo_target_type_setting.positive_geo_target_type, "
                 "campaign.geo_target_type_setting.negative_geo_target_type, campaign_budget.amount_micros, "
                 "campaign.serving_status, campaign.primary_status FROM campaign WHERE campaign.status != 'REMOVED'",
    "campaign_goals": "SELECT campaign.name, campaign_conversion_goal.category, campaign_conversion_goal.origin, "
                      "campaign_conversion_goal.biddable FROM campaign_conversion_goal WHERE campaign.status != 'REMOVED'",
    # ---- performance
    "campaign_perf": f"SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, metrics.impressions, metrics.clicks, "
                     f"metrics.cost_micros, metrics.conversions, metrics.all_conversions, metrics.conversions_value, "
                     f"metrics.search_impression_share, metrics.search_budget_lost_impression_share, "
                     f"metrics.search_rank_lost_impression_share, metrics.search_absolute_top_impression_share "
                     f"FROM campaign WHERE {R} AND campaign.status != 'REMOVED'",
    "campaign_month": f"SELECT campaign.name, segments.month, metrics.impressions, metrics.clicks, metrics.cost_micros, "
                      f"metrics.conversions, metrics.conversions_value FROM campaign WHERE {date_range(365)}",
    "device": f"SELECT campaign.name, segments.device, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions "
              f"FROM campaign WHERE {R}",
    # ---- conversions
    "conversion_actions": "SELECT conversion_action.id, conversion_action.name, conversion_action.status, conversion_action.type, "
                          "conversion_action.category, conversion_action.primary_for_goal, conversion_action.include_in_conversions_metric, "
                          "conversion_action.counting_type, conversion_action.click_through_lookback_window_days, "
                          "conversion_action.value_settings.default_value, conversion_action.value_settings.always_use_default_value, "
                          "conversion_action.origin FROM conversion_action WHERE conversion_action.status != 'REMOVED'",
    "conversions_by_action_week": f"SELECT segments.conversion_action_name, segments.week, metrics.all_conversions, "
                                  f"metrics.all_conversions_value FROM customer WHERE {date_range(180)}",
    "conversions_by_action_day": f"SELECT segments.conversion_action_name, segments.date, metrics.all_conversions "
                                 f"FROM customer WHERE {date_range(90)}",
    "campaign_conv_by_action": f"SELECT campaign.name, segments.conversion_action_name, metrics.conversions, metrics.all_conversions "
                               f"FROM campaign WHERE {R}",
    "offline_upload_summary": "SELECT offline_conversion_upload_client_summary.client, offline_conversion_upload_client_summary.status, "
                              "offline_conversion_upload_client_summary.total_event_count, "
                              "offline_conversion_upload_client_summary.successful_event_count, "
                              "offline_conversion_upload_client_summary.last_upload_date_time, "
                              "offline_conversion_upload_client_summary.success_rate FROM offline_conversion_upload_client_summary",
    "offline_upload_by_action": "SELECT offline_conversion_upload_conversion_action_summary.conversion_action_name, "
                                "offline_conversion_upload_conversion_action_summary.client, "
                                "offline_conversion_upload_conversion_action_summary.status, "
                                "offline_conversion_upload_conversion_action_summary.total_event_count, "
                                "offline_conversion_upload_conversion_action_summary.successful_event_count, "
                                "offline_conversion_upload_conversion_action_summary.last_upload_date_time "
                                "FROM offline_conversion_upload_conversion_action_summary",
    # ---- structure
    "ad_groups": "SELECT campaign.name, campaign.status, ad_group.id, ad_group.name, ad_group.status FROM ad_group "
                 "WHERE campaign.status != 'REMOVED' AND ad_group.status != 'REMOVED'",
    "keywords": "SELECT campaign.name, campaign.status, ad_group.name, ad_group.status, ad_group_criterion.criterion_id, "
                "ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.status, "
                "ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.creative_quality_score, "
                "ad_group_criterion.quality_info.post_click_quality_score, ad_group_criterion.quality_info.search_predicted_ctr "
                "FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD' AND ad_group_criterion.negative = FALSE "
                "AND ad_group_criterion.status != 'REMOVED' AND campaign.status != 'REMOVED'",
    "keyword_perf": f"SELECT campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, "
                    f"metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM keyword_view WHERE {H}",
    "search_terms": f"SELECT campaign.name, campaign.status, ad_group.name, search_term_view.search_term, search_term_view.status, "
                    f"segments.keyword.info.text, segments.keyword.info.match_type, metrics.impressions, metrics.clicks, "
                    f"metrics.cost_micros, metrics.conversions, metrics.all_conversions FROM search_term_view WHERE {H}",
    "pmax_search_categories": f"SELECT campaign.name, campaign_search_term_insight.category_label, metrics.impressions, metrics.clicks, "
                              f"metrics.conversions FROM campaign_search_term_insight WHERE {R} "
                              f"AND campaign_search_term_insight.campaign_id = '{{pmax_id}}'",
    # ---- negatives
    "shared_sets": "SELECT shared_set.id, shared_set.name, shared_set.type, shared_set.status, shared_set.member_count, "
                   "shared_set.reference_count FROM shared_set WHERE shared_set.type IN ('NEGATIVE_KEYWORDS','ACCOUNT_LEVEL_NEGATIVE_KEYWORDS') "
                   "AND shared_set.status = 'ENABLED'",
    "shared_criteria": "SELECT shared_set.id, shared_set.name, shared_set.type, shared_criterion.criterion_id, shared_criterion.keyword.text, "
                       "shared_criterion.keyword.match_type FROM shared_criterion "
                       "WHERE shared_set.type IN ('NEGATIVE_KEYWORDS','ACCOUNT_LEVEL_NEGATIVE_KEYWORDS') AND shared_set.status = 'ENABLED'",
    "list_attachments": "SELECT campaign.id, campaign.name, campaign.status, shared_set.id, shared_set.name, campaign_shared_set.status "
                        "FROM campaign_shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS' AND campaign.status != 'REMOVED'",
    "campaign_negatives": "SELECT campaign.id, campaign.name, campaign.status, campaign_criterion.criterion_id, campaign_criterion.keyword.text, "
                          "campaign_criterion.keyword.match_type FROM campaign_criterion "
                          "WHERE campaign_criterion.type = 'KEYWORD' AND campaign_criterion.negative = TRUE AND campaign.status != 'REMOVED'",
    "adgroup_negatives": "SELECT campaign.name, campaign.status, ad_group.name, ad_group.status, ad_group_criterion.criterion_id, "
                         "ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type FROM ad_group_criterion "
                         "WHERE ad_group_criterion.type = 'KEYWORD' AND ad_group_criterion.negative = TRUE AND campaign.status != 'REMOVED'",
    "account_negative_links": "SELECT customer_negative_criterion.type, customer_negative_criterion.negative_keyword_list.shared_set "
                              "FROM customer_negative_criterion",
    # ---- geo
    "locations": "SELECT campaign.name, campaign.status, campaign_criterion.type, campaign_criterion.negative, "
                 "campaign_criterion.location.geo_target_constant, campaign_criterion.proximity.radius, "
                 "campaign_criterion.proximity.radius_units, campaign_criterion.bid_modifier FROM campaign_criterion "
                 "WHERE campaign_criterion.type IN ('LOCATION', 'PROXIMITY') AND campaign.status != 'REMOVED'",
    "user_locations": f"SELECT campaign.name, user_location_view.targeting_location, segments.geo_target_city, metrics.impressions, "
                      f"metrics.clicks, metrics.cost_micros, metrics.conversions FROM user_location_view WHERE {R}",
    # ---- ads, assets, landing pages
    "ads": "SELECT campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.status, ad_group_ad.ad_strength, "
           "ad_group_ad.ad.final_urls, ad_group_ad.ad.responsive_search_ad.headlines, ad_group_ad.ad.responsive_search_ad.descriptions, "
           "ad_group_ad.ad.responsive_search_ad.path1, ad_group_ad.ad.responsive_search_ad.path2, "
           "ad_group_ad.policy_summary.approval_status FROM ad_group_ad WHERE campaign.status != 'REMOVED' AND ad_group_ad.status != 'REMOVED'",
    "ad_perf": f"SELECT campaign.name, ad_group.name, ad_group_ad.ad.id, metrics.impressions, metrics.clicks, metrics.cost_micros, "
               f"metrics.conversions FROM ad_group_ad WHERE {R}",
    "assets_campaign": "SELECT campaign.name, campaign.status, campaign_asset.field_type, campaign_asset.status, asset.type, "
                       "asset.sitelink_asset.link_text, asset.callout_asset.callout_text, asset.call_asset.phone_number "
                       "FROM campaign_asset WHERE campaign.status != 'REMOVED'",
    "assets_customer": "SELECT customer_asset.field_type, customer_asset.status, asset.type, asset.sitelink_asset.link_text, "
                       "asset.callout_asset.callout_text, asset.call_asset.phone_number FROM customer_asset",
    "landing_pages": f"SELECT landing_page_view.unexpanded_final_url, metrics.impressions, metrics.clicks, metrics.cost_micros, "
                     f"metrics.conversions, metrics.mobile_friendly_clicks_percentage FROM landing_page_view WHERE {R}",
    # ---- history
    "change_history": "SELECT change_event.change_date_time, change_event.user_email, change_event.change_resource_type, "
                      "change_event.resource_change_operation, change_event.client_type, campaign.name FROM change_event "
                      f"WHERE change_event.change_date_time >= '{end - dt.timedelta(days=29)}' "
                      f"AND change_event.change_date_time <= '{end + dt.timedelta(days=1)}' "
                      "ORDER BY change_event.change_date_time DESC LIMIT 500",
}

ga = client(cfg).get_service("GoogleAdsService")
print(f"Account {cid}  recent window {a.days}d  history window {a.history_days}d")
summary = {}
for name, q in Q.items():
    if a.only and name not in a.only:
        continue
    if "{pmax_id}" in q:
        continue  # handled below, needs campaign IDs
    try:
        rows = run(ga, cid, q)
        save(cfg, name, rows)
        summary[name] = len(rows)
        print(f"  {name:28s} {len(rows):>7,} rows")
    except Exception as e:  # keep going: one unsupported field should not stop the pull
        summary[name] = f"ERROR {api_error(e)}"
        print(f"  {name:28s} ERROR {api_error(e)}")

# Performance Max search categories (PMax hides search terms; categories are the closest view)
if not a.only or "pmax_search_categories" in a.only:
    try:
        camps = run(ga, cid, "SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status = 'ENABLED' "
                             "AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'")
        rows = []
        for c in camps:
            rows += run(ga, cid, Q["pmax_search_categories"].replace("{pmax_id}", str(g(c, "campaign", "id"))))
        save(cfg, "pmax_search_categories", rows)
        summary["pmax_search_categories"] = len(rows)
        print(f"  {'pmax_search_categories':28s} {len(rows):>7,} rows")
    except Exception as e:
        print(f"  pmax_search_categories       skipped ({api_error(e)})")

# Resolve location IDs to names
if not a.only or "locations" in a.only:
    from gads import load
    rns = sorted({g(r, "campaign_criterion", "location", "geo_target_constant") for r in load(cfg, "locations", [])} - {None})
    if rns:
        inlist = ", ".join(f"'{r}'" for r in rns)
        rows = run(ga, cid, "SELECT geo_target_constant.resource_name, geo_target_constant.canonical_name, "
                            f"geo_target_constant.target_type FROM geo_target_constant WHERE geo_target_constant.resource_name IN ({inlist})")
        save(cfg, "geo_names", rows)
        print(f"  {'geo_names':28s} {len(rows):>7,} rows")

meta = {"pulled_at": dt.datetime.now().isoformat(timespec="seconds"), "customer_id": cid,
        "days": a.days, "history_days": a.history_days, "counts": summary}
if not a.only:   # partial pulls keep the metadata of the last full pull
    (work_dir(cfg, "data") / "_pull.json").write_text(json.dumps(meta, indent=1))
print(f"Done. Raw data in {work_dir(cfg, 'data')}")
