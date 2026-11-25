# 08 Weekly operating rhythm

The rhythm an agent can run every week, with a person approving the output. Each step names the skill that does it.

## Daily (5 minutes, automated)

- Conversion heartbeat: `conversion_health.py`. Alert when a primary action goes quiet, an upload fails, or values move.

## Weekly (30 minutes of human review)

1. **Pull** recent data: `pull.py --days 30`.
2. **Search term review** (search-term-review skill): leaks, junk to add, customer searches being blocked, converting terms to add as keywords.
3. **Approve** additions; apply with `negatives_apply.py --add-terms` after the dry run.
4. **Budget and pacing**: campaigns capped by budget, campaigns underspending.
5. **One test at a time**: new ad, new landing page, new theme. Note the start date.
6. **Log** every change and why (the scripts write `work/<client>/changes.log.jsonl`; add the reason in your weekly note).

## Monthly

- Full audit (google-ads-audit skill) and compare to last month's findings.
- Landing page check.
- Keyword expansion from converting search terms.
- Review conversion values against actual close rates.

## Quarterly

- Re-set conversion values from real numbers.
- Review account structure: campaigns to fund, fold or split.
- Refresh ads and assets.
