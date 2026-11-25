---
name: search-term-review
description: Weekly Google Ads search term review that finds leaks, junk to block, customers being blocked, and converting searches to add as keywords. Use for the weekly PPC check, when someone asks what people searched, what to add as negatives this week, or to confirm a negative keyword change is working.
---

# Search term review

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Steps

1. `scripts/search_term_review.py --client clients/<slug>.yaml --days 7` writes `work/<slug>/reviews/search-terms-<date>.md` and `.json`. For better checks, refresh the history first: `scripts/pull.py --client ... --only search_terms --history-days 540`.
2. Read the report. For each section:
   - **Leaks** (should be none): a served term matching a live negative usually means the list is not attached to that campaign. Check attachments.
   - **Converting customer searches now blocked**: fix immediately; remove or narrow the negative.
   - **Clicked, no conversion**: decide per term. Add only repeated junk with a clear off-intent root. The script suggests a root that never appears in converting history or the allow-list; still read it. Anything marked "customer intent" is probably a real customer having a bad week: leave it.
   - **Converting terms not yet keywords**: propose as phrase or exact keywords in the matching ad group.
3. Write the weekly note (template below).
4. After a person approves additions: write the terms to a file and run `scripts/negatives_apply.py --client ... --add-terms terms.txt --list "<list name>"` (dry run), then with `APPLY_ENABLED=1 ... --execute`. The script refuses any term that blocks a converting search or the allow-list.

## Weekly note template

```markdown
# <Client>: weekly negative keyword check, <date>
Window: <start> to <end>. <terms> search terms, <clicks> clicks, $<spend>, <conv> conversions.

## 1. Leaks
## 2. Customer searches getting through that the old setup blocked (and what they did)
## 3. Junk worth adding
| Search term | Spend | Suggested phrase negative | List |
## 4. Looked at, not adding (and why)
## 5. Keywords to add
## 6. Structure
```

## Approval

Read-only until a person approves the additions. Never auto-add.
