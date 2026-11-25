"""Check credentials and access. Lists every account these credentials can reach, then
confirms the client's customer ID answers with the configured login_customer_id.

  python scripts/check_connection.py --client clients/acme.yaml
"""
from gads import api_error, arg_parser, client, load_config, run

a = arg_parser("Test Google Ads API access").parse_args()
cfg = load_config(a.client)
c = client(cfg)
try:
    res = c.get_service("CustomerService").list_accessible_customers()
    ids = [r.split("/")[-1] for r in res.resource_names]
    print(f"Credentials work. Directly accessible accounts: {', '.join(ids)}")
except Exception as e:
    raise SystemExit(f"Credentials failed: {api_error(e)}\nSee docs/setup.md 'Common errors'.")
ga = c.get_service("GoogleAdsService")
for login in dict.fromkeys([cfg["login_customer_id"], cfg["customer_id"]]):
    try:
        row = run(client(cfg, login).get_service("GoogleAdsService"), cfg["customer_id"],
                  "SELECT customer.descriptive_name, customer.currency_code, customer.time_zone FROM customer")[0]["customer"]
        print(f"OK  {cfg['customer_id']} ({row['descriptive_name']}, {row['currency_code']}) with login_customer_id {login}")
        if login != cfg["login_customer_id"]:
            print(f"    Set login_customer_id: '{login}' in {cfg['_path']}.")
        break
    except Exception as e:
        print(f"FAIL {cfg['customer_id']} with login_customer_id {login}: {api_error(e)}")
