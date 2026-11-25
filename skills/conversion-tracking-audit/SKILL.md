---
name: conversion-tracking-audit
description: Check that Google Ads conversion tracking and offline conversion uploads are healthy, stable and pointed at the right goals. Use when cost per lead or ROAS shifts without an obvious cause, before changing bids or bidding strategy, when setting up CRM offline conversion imports, or as a daily heartbeat.
---

# Conversion tracking audit

Smart bidding optimizes toward what you report. This skill finds out whether what you report is true, complete and stable.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Steps

1. `scripts/conversion_health.py --client clients/<slug>.yaml` writes `work/<slug>/reviews/conversion-health-<date>.md`.
2. If you need history: `scripts/pull.py --client ... --only conversion_actions conversions_by_action_week conversions_by_action_day campaign_goals offline_upload_summary offline_upload_by_action campaign_conv_by_action`
3. Work the checklist in `docs/playbook/02-conversion-tracking.md`, and the niche pack's `conversion-setup.md` if it has one (stage definitions, value worksheet, CRM upload options, call tracking).
4. Ask the business: which stage does each action represent, who or what uploads it, and how values are set. Write the answers down.

## Output

A short report: the alerts, a table of actions (stage, primary or secondary, upload owner, value, last conversion), and the fixes. The most common fixes:
- Set one value per stage from close rate x average profit; change it at most quarterly.
- One upload owner per action; turn off the extra pipelines.
- Set near-duplicates and micro-actions to secondary.
- Turn on auto-tagging and enhanced conversions for leads.

## Daily heartbeat

Schedule `conversion_health.py` daily. Alert a person when a primary action goes quiet past its normal gap, an upload client stops or fails, or a value moves more than 50%.

## Approval

Read-only. Changing conversion actions, values or goals resets bidding: a person makes those changes in the UI after reading the report.
