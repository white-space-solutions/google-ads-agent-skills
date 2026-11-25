"""campaign_build.py offline: spec checks, keyword parsing, born-blocked detection. No API calls."""
import copy
from pathlib import Path

import yaml

import campaign_build as cb

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = yaml.safe_load((REPO / "niches/real-estate-investors/campaign-template.yaml").read_text())
CFG = {"customer_id": "1234567890", "niche": "real-estate-investors", "competitors": ["rival home buyers"],
       "safety": {"allowed_customer_ids": ["1234567890"], "max_ops_per_run": 500, "max_daily_budget": 300}}


def test_template_passes_with_no_errors_or_warnings():
    errs, warns = cb.check_spec(copy.deepcopy(TEMPLATE), CFG)
    assert errs == [] and warns == []


def test_parse_keyword_notation():
    assert cb.parse_keyword("[sell my house fast]") == ("sell my house fast", "EXACT")
    assert cb.parse_keyword('"sell house"') == ("sell house", "PHRASE")
    assert cb.parse_keyword("cash home buyers", "BROAD") == ("cash home buyers", "BROAD")
    assert cb.parse_keyword({"text": "We Buy Houses", "match": "exact"}) == ("we buy houses", "EXACT")


def test_budget_cap_and_missing_pieces_are_errors():
    s = copy.deepcopy(TEMPLATE)
    s["campaign"]["daily_budget"] = 1000
    s["campaign"]["locations"] = []
    s["ad_groups"][0]["ads"][0]["headlines"][3]["text"] = "Best Cash Offer In Town Guaranteed"
    errs, _ = cb.check_spec(s, CFG)
    joined = " ".join(errs)
    assert "max_daily_budget" in joined and "locations" in joined and "max 30" in joined


def test_manual_cpc_needs_bids_and_four_ads_rejected():
    s = copy.deepcopy(TEMPLATE)
    s["campaign"]["bidding"] = "manual_cpc"
    s["ad_groups"][0]["ads"] *= 4
    errs, _ = cb.check_spec(s, CFG)
    assert any("cpc_bid" in e for e in errs) and any("3 enabled RSAs" in e for e in errs)


def test_keyword_blocked_by_attached_negatives_is_an_error():
    s = copy.deepcopy(TEMPLATE)
    errs, _ = cb.keyword_conflicts(s, CFG, {("as is", "PHRASE")})
    assert any("sell house as is" in e for e in errs)
    errs, _ = cb.keyword_conflicts(s, CFG, set())
    assert errs == []


def test_competitor_keyword_warns():
    s = copy.deepcopy(TEMPLATE)
    s["ad_groups"][0]["keywords"].append("rival home buyers reviews")
    _, warns = cb.keyword_conflicts(s, CFG, set())
    assert any("competitor" in w for w in warns)
