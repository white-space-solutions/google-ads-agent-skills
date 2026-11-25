"""End to end on fixture data, no API: negatives_init -> negatives_validate -> audit."""
import json
import shutil
import uuid
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SLUG = f"pytest-{uuid.uuid4().hex[:8]}"


def m(cost, conv=0, clicks=3, impr=20):
    return {"cost_micros": str(int(cost * 1e6)), "conversions": conv, "clicks": str(clicks), "impressions": str(impr), "all_conversions": conv}


def st(term, camp, kw, cost, conv=0):
    return {"campaign": {"name": camp, "status": "ENABLED"}, "search_term_view": {"search_term": term},
            "segments": {"keyword": {"info": {"text": kw, "match_type": "PHRASE"}}}, "metrics": m(cost, conv)}


@pytest.fixture()
def client_yaml(tmp_path):
    work = REPO / "work" / SLUG
    shutil.rmtree(work, ignore_errors=True)
    data = work / "data"
    data.mkdir(parents=True, exist_ok=True)
    G, C = "Sell House Fast", "Competitors"
    fixtures = {
        "search_terms": [
            st("sell my house fast", G, "sell my house fast", 300, 2),
            st("sell house without realtor", G, "sell house", 120, 1),
            st("houses for rent near me", G, "sell house", 90),
            st("houses for rent near me", G, "sell house", 60),
            st("real estate jobs", G, "sell house", 80),
            st("rival home buyers", G, "sell house", 150),
            st("rival home buyers reviews", C, "rival home buyers", 70),
        ],
        "keywords": [{"campaign": {"name": G, "status": "ENABLED"}, "ad_group": {"name": "Core", "status": "ENABLED"},
                      "ad_group_criterion": {"keyword": {"text": t, "match_type": "PHRASE"}, "status": "ENABLED"}}
                     for t in ("sell my house fast", "sell house")]
                    + [{"campaign": {"name": C, "status": "ENABLED"}, "ad_group": {"name": "Rival", "status": "ENABLED"},
                        "ad_group_criterion": {"keyword": {"text": "rival home buyers", "match_type": "PHRASE"}, "status": "ENABLED"}}],
        "campaign_negatives": [{"campaign": {"name": G, "status": "ENABLED"},
                                "campaign_criterion": {"keyword": {"text": "realtor", "match_type": "PHRASE"}}}],
        "shared_criteria": [], "list_attachments": [], "adgroup_negatives": [], "shared_sets": [],
        "campaign_perf": [{"campaign": {"name": G, "status": "ENABLED", "advertising_channel_type": "SEARCH"},
                           "metrics": {**m(870, 3), "search_budget_lost_impression_share": 0.7}}],
        "campaigns": [{"campaign": {"name": G, "status": "ENABLED", "advertising_channel_type": "SEARCH",
                                    "geo_target_type_setting": {"positive_geo_target_type": "PRESENCE_OR_INTEREST"}}}],
        "customer": [{"customer": {"descriptive_name": "Fixture", "auto_tagging_enabled": True}}],
    }
    for k, v in fixtures.items():
        (data / f"{k}.json").write_text(json.dumps(v))
    cfg = {"slug": SLUG, "customer_id": "1234567890", "niche": "real-estate-investors", "brand_terms": ["acme home buyers"],
           "competitors": ["rival home buyers"], "list_prefix": "FIX",
           "campaign_roles": {"generic": ["Sell House"], "competitors": ["Competitors"], "brand": ["Brand"]}}
    p = tmp_path / "client.yaml"
    p.write_text(yaml.safe_dump(cfg))
    yield p
    shutil.rmtree(work, ignore_errors=True)


def run(script, cfg, *args):
    return subprocess.run([sys.executable, str(REPO / "scripts" / script), "--client", str(cfg), *args],
                          capture_output=True, text=True, cwd=REPO)


def test_pipeline(client_yaml):
    r = run("negatives_init.py", client_yaml)
    assert r.returncode == 0, r.stderr
    r = run("negatives_validate.py", client_yaml)
    v = json.loads((REPO / "work" / SLUG / "negatives" / "validation.json").read_text())
    assert v["gates"]["G1_converting_blocked"] == 0, r.stdout
    assert v["current_conflicts"] >= 1            # the live "realtor" negative blocks a converting seller search

    # a bad proposal must trip G1 and G3
    p = REPO / "work" / SLUG / "negatives" / "proposed.yaml"
    doc = yaml.safe_load(p.read_text())
    doc["lists"][0]["groups"]["Bad"] = ["realtor"]
    p.write_text(yaml.safe_dump(doc))
    r = run("negatives_validate.py", client_yaml)
    v = json.loads((REPO / "work" / SLUG / "negatives" / "validation.json").read_text())
    assert v["gates"]["G1_converting_blocked"] >= 1 and v["gates"]["G3_allow_list_blocked"] >= 1
    assert r.returncode == 1

    r = run("audit.py", client_yaml)
    assert r.returncode == 0, r.stderr
    f = json.loads((REPO / "work" / SLUG / "audit" / "findings.json").read_text())
    titles = " ".join(x["title"] for x in f["findings"])
    assert "Presence or interest" in titles
    assert "impression share to budget" in titles
    assert "can no longer show" in titles or "allow-list" in titles
