---
name: google-ads-setup
description: Connect an AI agent to a Google Ads account through the official API and create the client config. Use when someone wants to connect Google Ads, set up API access, get a developer token or refresh token, add a new client account, or when any Google Ads script fails on credentials or access.
---

# Google Ads setup

Get from nothing to a passing `check_connection.py` for one ad account.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Inputs (ask, never guess)

- Does the person (or their agency) already have a Google Ads developer token and an OAuth client? If yes, skip to step 4.
- The ad account's customer ID (123-456-7890 format) and, if they use one, the manager (MCC) ID.
- The business niche (for example `real-estate-investors`), brand name(s), main competitors, cities served and not served.

## Steps

1. Walk them through `docs/setup.md` Steps 1 to 6 (MCC, link, developer token application, Cloud project, consent screen, OAuth client). Do the clicking guidance one step at a time; the token review takes 24 to 48 hours.
2. `cp .env.example .env` and have them paste the client ID and secret. Never ask them to paste secrets into chat; they edit the file.
3. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then `.venv/bin/python scripts/get_refresh_token.py`.
4. `cp clients/example.yaml clients/<slug>.yaml` and fill it in with them: `slug`, `customer_id`, `login_customer_id`, `niche`, `brand_terms`, `competitors`, `service_area`, `campaign_roles`. Get campaign names from the account (step 5 lists them) before writing `campaign_roles`.
5. `.venv/bin/python scripts/check_connection.py --client clients/<slug>.yaml`. If it says to change `login_customer_id`, do it and rerun.
6. Run `scripts/pull.py --client clients/<slug>.yaml --only campaigns` and show the campaign list so roles can be mapped by name prefix.

## Validate

- `check_connection.py` prints `OK` for the account.
- `.env` is listed in `.gitignore` and `git status` does not show it.
- Every enabled campaign maps to a role (anything left as `other` is a conscious choice).

## Errors

See the table in `docs/setup.md` "Common errors". "Developer token is not approved" means the token is still in Test access: wait for Google's email.

## Approval

Nothing here writes to the ad account. Do not run any write script during setup.
