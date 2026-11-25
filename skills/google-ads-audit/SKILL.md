---
name: google-ads-audit
description: Full Google Ads account audit for a lead generation business with a ranked, evidence-backed list of fixes. Use when someone asks to audit, review, diagnose or health-check a Google Ads or PPC account, asks why cost per lead went up, or is onboarding a new ad account.
---

# Google Ads audit

Read-only. Produces a written audit with the fixes ranked by expected impact, each with the evidence behind it.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Inputs

- `clients/<slug>.yaml` with `campaign_roles`, `brand_terms`, `competitors` and `niche` filled in (google-ads-setup skill).
- What the business counts as a good lead and roughly what one is worth. Ask if unknown; it changes the conclusions.

## Steps

1. `scripts/pull.py --client clients/<slug>.yaml --history-days 365`
2. `scripts/conversion_health.py --client clients/<slug>.yaml`
3. `scripts/audit.py --client clients/<slug>.yaml` writes `work/<slug>/audit/facts.md` and `findings.json`.
4. `scripts/landing_pages.py --client clients/<slug>.yaml`
5. Read `docs/playbook/README.md`, chapter 02 (conversions) and the niche pack README. Read `benchmarks.md` in the niche pack.
6. Read the fact sheet, conversion health report and landing page report. Open the raw JSON in `work/<slug>/data/` to confirm anything surprising before you write it down. The script flags; you verify.
7. Write the audit (template below) to `work/<slug>/audit/audit-<date>.md`.

## How to rank

Order fixes by expected impact on cost per qualified lead, in this priority unless the data says otherwise:
1. Conversion signal problems (wrong goals, value drift, broken or duplicate uploads). They poison everything else.
2. Money going to the wrong searches (bad negatives blocking customers, junk search terms, broad match drift, competitor leaks).
3. Budget allocation (starved campaigns, campaigns to fund or fold).
4. Structure and settings (location option, networks, single broad keyword campaigns).
5. Ads, assets and landing pages.
6. New opportunities (themes no campaign owns).

## Template

```markdown
# <Business>: Google Ads audit
<date> · account <id>

## Summary
<2-3 sentences: what is happening to results and why.>
Top fixes, ranked by expected impact:
1. **<fix>.** <one-line why, with the number>
...
Nothing in the account was changed for this audit.

## Account snapshot
<campaign table: bidding, budget, spend, conversions, cost per qualified lead, impression share lost to budget>

## Conversion data
## Search terms and negatives
## Budget and structure
## Ads, assets and landing pages
## Opportunities
## Next steps
<what to approve, in order, and which skill does each>
```

## Writing rules

- Every claim carries its number and window ("$7,658 on 34 keywords with zero conversions, last 365 days").
- Plain words. No hype. Say what is well built too.
- Separate fact from judgment ("Value per conversion moved 4x" is a fact; "this likely drove the drop" is a judgment; label it).
- Account for qualification lag before calling a recent drop.

## Approval

Read-only. Recommend changes; do not make them. Hand approved fixes to the negative-keyword-audit or apply-google-ads-changes skills.
