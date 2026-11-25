---
name: negative-keyword-audit
description: Audit, rebuild or extend a Google Ads negative keyword structure without blocking real customers, using gates tested against the account's own search term history. Use when someone asks to clean up, consolidate, add or review negative keywords or negative lists, when search terms show wasted spend, or when an audit finds negatives blocking converting searches.
---

# Negative keyword audit

Rebuild or extend negatives so they cut waste and never block a customer. Read `docs/playbook/04-negative-keywords.md` first; it is the spec.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Inputs

- Client yaml with `campaign_roles`, `brand_terms`, `competitors`, `service_area.include_terms` (places served) and `service_area.exclude_terms` (places not served), and `niche`.
- Client-specific customer searches for the allow-list: add them to `work/<slug>/allow-list.txt` (one per line, for example "sell my house fast <their city>").

## Steps

1. `scripts/pull.py --client clients/<slug>.yaml --history-days 540` (18 months of search terms).
2. `scripts/negatives_init.py --client ...` seeds `work/<slug>/negatives/proposed.yaml` from the niche pack.
3. `scripts/negatives_validate.py --client ...` writes `validation.xlsx` and `validation.json`.
4. Loop until gates G1 to G4 are all 0:
   - For each gate hit, **narrow the negative** (a longer, more specific phrase) rather than delete it. Delete only if no narrower phrase works.
   - A hit that is intentional (competitor routing, brand routing) goes in `accepted_exceptions` with a one-line reason.
   - Rerun validate after every edit.
5. Work the review tabs:
   - **Current conflicts**: live negatives blocking converting or allow-listed searches today. List each with its fix. Removals go in a CSV for `negatives_apply.py --remove` (columns: scope,container,text,match).
   - **Gap n-grams**: propose roots only where "Converting terms containing it" is 0 and the root is clearly off-intent. Skip addresses and one-off names.
   - **Impact**: note the spend under live keywords, not the all-history number.
6. Write `work/<slug>/negatives/summary.md`: gate results, every change you made to the proposal and why, proposed additions with spend, current negatives to remove, location settings to change, accepted exceptions.
7. Show the summary to a person. Stop here until they approve.
8. After approval, follow the apply-google-ads-changes skill:
   - `scripts/negatives_apply.py --client ...` (dry run)
   - `APPLY_ENABLED=1 scripts/negatives_apply.py --client ... --execute`
   - `APPLY_ENABLED=1 scripts/negatives_apply.py --client ... --remove removals.csv --execute` (dry run it first)
   - After checking attachments in the UI: `--retire-old` (dry run, then execute). Old lists are detached, not deleted.
9. Schedule the search-term-review skill weekly. Delete the old lists in the UI only after two clean weeks.

## Validate

- Gates all 0 in the latest `validation.json`, newer than `proposed.yaml` (the apply script refuses otherwise).
- After applying: run `search_term_review.py --days 7` a week later. Leaks must be 0.

## Never

- Add a bare word that real customers use (see the niche README's "words that look like junk").
- Negate a term because one click did not convert. Look for repeated spend and zero conversions across history.
- Delete lists from the API. Detach; delete later by hand.
