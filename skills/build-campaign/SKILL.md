---
name: build-campaign
description: Build a complete Google Ads Search campaign from a reviewed plan - budget, bidding, locations, schedule, negative lists, sitelinks, callouts, snippets, ad groups, keywords and responsive search ads - in one atomic request, created paused, dry run first. Use when someone wants to launch, create, set up or build a new campaign or a new city or service campaign, or turn a keyword plan and ad copy into a live campaign.
---

# Build a campaign

Turns a keyword plan and validated ad copy into a real Search campaign. The campaign is created **paused**, in one all-or-nothing request, and only after a person approves the dry run. Turning it on is a separate approval.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml` with `safety.allowed_customer_ids`, `safety.max_ops_per_run` and `safety.max_daily_budget`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Read first

1. `docs/playbook/01-account-structure.md` and `03-keywords.md`.
2. The niche pack's `launch-plan.md` (budget, launch order, bidding) and `campaign-template.yaml` (a working spec to copy).
3. `docs/playbook/09-safe-changes.md`.

## Before you build (stop if any is missing)

- **Tracking works**: a test lead reaches the CRM with the GCLID (conversion-tracking-audit; niche `conversion-setup.md`). A campaign that cannot see conversions cannot be judged or bid.
- **Landing pages exist** for every ad group and pass `scripts/landing_pages.py` (landing-page-check).
- **Negative lists exist** in the account (negative-keyword-audit). A campaign without negatives buys junk from day one.
- **Keyword plan** from keyword-research and **ad copy** from generate-ads, both reviewed by the person.
- **Verified facts** for every claim in the ads. Never invent ratings, years, counts or close times.
- **Budget and market** confirmed by the person: daily budget, locations (geo target IDs), hours someone answers the phone.

## Steps

1. Copy `niches/<niche>/campaign-template.yaml` to `work/<slug>/build/<campaign>.yaml`. Fill it from the plan: campaign name, daily budget, bidding, locations, schedule, the exact names of the negative lists, assets with real URLs, one ad group per theme with its own landing page, keywords (`[x]` exact, `"x"` phrase, plain = the ad group's `default_match`), up to 3 RSAs per ad group.
2. Static check, no API: `.venv/bin/python scripts/campaign_build.py --client clients/<slug>.yaml --spec work/<slug>/build/<campaign>.yaml --check-only`. Fix every ERROR. Judge every WARNING; most are copy rules from `validate_ad.py`.
3. Dry run: the same command without `--check-only`. It checks the name is not taken, the negative lists exist, no keyword is blocked by the negatives it will carry, then sends the whole campaign to Google with `validate_only`. Google checks every field and runs the ads through policy. Nothing is created.
4. Show the person the dry run summary line and the spec: budget, bidding, locations, schedule, ad groups, keyword count, every headline and description, the lists attached. Get an explicit yes for exactly that.
5. Execute, with the kill switch on that one command only:
   `APPLY_ENABLED=1 .venv/bin/python scripts/campaign_build.py --client clients/<slug>.yaml --spec work/<slug>/build/<campaign>.yaml --execute`
   The created resource names are saved to `<campaign>.applied.json` and the change is logged in `work/<slug>/changes.log.jsonl`.
6. Verify: `scripts/pull.py --client ... --only campaigns keywords ads assets_campaign locations`. Ask the person to review it in the Google Ads UI (ad strength, policy status, locations, schedule).
7. Enable only on a second explicit yes: `--enable "<campaign name>"` (dry run), then with `APPLY_ENABLED=1 ... --execute`.
8. Watch: conversion heartbeat daily, search-term-review twice a week for the first month (launch-plan.md, First 90 days).

## Refusals are features

The script refuses when the account is not on the allowlist, the op count is over `max_ops_per_run`, the budget is over `max_daily_budget`, the name already exists, a negative list is missing, a keyword would be born blocked, an ad has a copy ERROR, or Google rejects any operation. Fix the cause. Never raise a safety limit without the person's say-so.

## What it does not do

- Performance Max, Display, Video or Demand Gen campaigns. Search only.
- Edit a live campaign. Rerunning with the same name is refused; change live campaigns in the UI or with the targeted scripts.
- Conversion goals. The campaign uses the account's default goals; set campaign-specific goals in the UI if needed (conversion-tracking-audit).

## Undo

The campaign is created paused, so nothing spends until it is enabled. To undo, remove the campaign in the UI (`<campaign>.applied.json` lists everything that was created). Removing is permanent; pausing is not.
