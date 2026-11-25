"""Read-only backup of every negative keyword in the account, fresh from the API.

Writes work/<slug>/backups/negatives-<timestamp>/backup.json (restore reads this) and an xlsx for people.
negatives_apply.py --execute takes one automatically if none exists from the last 24 hours.

  python scripts/negatives_backup.py --client clients/acme.yaml
"""
import datetime as dt
import json

from gads import arg_parser, client, g, load_config, run, work_dir, write_xlsx

Q = {
    "lists": "SELECT shared_set.id, shared_set.name, shared_set.type, shared_set.status, shared_set.member_count, shared_set.reference_count "
             "FROM shared_set WHERE shared_set.type IN ('NEGATIVE_KEYWORDS','ACCOUNT_LEVEL_NEGATIVE_KEYWORDS')",
    "list_terms": "SELECT shared_set.id, shared_set.name, shared_set.status, shared_criterion.criterion_id, shared_criterion.keyword.text, "
                  "shared_criterion.keyword.match_type FROM shared_criterion WHERE shared_set.type IN ('NEGATIVE_KEYWORDS','ACCOUNT_LEVEL_NEGATIVE_KEYWORDS')",
    "attachments": "SELECT campaign.id, campaign.name, campaign.status, shared_set.id, shared_set.name, campaign_shared_set.status "
                   "FROM campaign_shared_set WHERE shared_set.type = 'NEGATIVE_KEYWORDS'",
    "campaign_negatives": "SELECT campaign.id, campaign.name, campaign.status, campaign_criterion.criterion_id, campaign_criterion.keyword.text, "
                          "campaign_criterion.keyword.match_type FROM campaign_criterion WHERE campaign_criterion.type = 'KEYWORD' "
                          "AND campaign_criterion.negative = TRUE",
    "adgroup_negatives": "SELECT campaign.name, ad_group.id, ad_group.name, ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, "
                         "ad_group_criterion.keyword.match_type FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD' "
                         "AND ad_group_criterion.negative = TRUE",
}


def backup(cfg) -> "Path":
    cid = cfg["customer_id"]
    ga = client(cfg).get_service("GoogleAdsService")
    data = {k: run(ga, cid, q) for k, q in Q.items()}
    data["taken_at"] = dt.datetime.now().isoformat(timespec="seconds")
    data["customer_id"] = cid
    d = work_dir(cfg, "backups", "negatives-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    (d / "backup.json").write_text(json.dumps(data, indent=1))
    write_xlsx(d / "negatives-backup.xlsx", [
        ("Lists", ["List ID", "List", "Type", "Status", "Terms", "Campaigns"],
         [[g(r, "shared_set", "id"), g(r, "shared_set", "name"), g(r, "shared_set", "type"), g(r, "shared_set", "status"),
           g(r, "shared_set", "member_count"), g(r, "shared_set", "reference_count")] for r in data["lists"]]),
        ("List terms", ["List", "Keyword", "Match"],
         [[g(r, "shared_set", "name"), g(r, "shared_criterion", "keyword", "text"), g(r, "shared_criterion", "keyword", "match_type")] for r in data["list_terms"]]),
        ("Attachments", ["Campaign", "Campaign status", "List", "Status"],
         [[g(r, "campaign", "name"), g(r, "campaign", "status"), g(r, "shared_set", "name"), g(r, "campaign_shared_set", "status")] for r in data["attachments"]]),
        ("Campaign negatives", ["Campaign", "Keyword", "Match"],
         [[g(r, "campaign", "name"), g(r, "campaign_criterion", "keyword", "text"), g(r, "campaign_criterion", "keyword", "match_type")] for r in data["campaign_negatives"]]),
        ("Ad group negatives", ["Campaign", "Ad group", "Keyword", "Match"],
         [[g(r, "campaign", "name"), g(r, "ad_group", "name"), g(r, "ad_group_criterion", "keyword", "text"), g(r, "ad_group_criterion", "keyword", "match_type")]
          for r in data["adgroup_negatives"]]),
    ])
    print(f"Backup: {d}  lists {len(data['lists'])}  list terms {len(data['list_terms'])}  attachments {len(data['attachments'])}  "
          f"campaign negatives {len(data['campaign_negatives'])}  ad group negatives {len(data['adgroup_negatives'])}")
    return d


if __name__ == "__main__":
    a = arg_parser("Back up all negatives").parse_args()
    backup(load_config(a.client))
