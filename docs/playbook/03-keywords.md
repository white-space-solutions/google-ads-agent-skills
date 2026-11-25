# 03 Keywords

## Match types

| Match | Use for | Watch out |
|---|---|---|
| Exact | Proven money terms, competitor names, brand | Still matches close variants and same-meaning queries |
| Phrase | The default for building themes | Covers word-order variants of the theme |
| Broad | Only themes that already convert, with strong conversion data and tight negatives | Drifts into listings, rentals, jobs and research searches |

If broad match carries more than 40% of keyword spend, check its search terms before anything else. Never run a campaign on a single broad keyword: Google then decides which searches qualify.

## Building a theme

1. Start from the niche pack's `keyword-themes.md` and `seed-keywords.txt`.
2. Run `scripts/keyword_ideas.py --seeds-from-niche` for volume and bid ranges in the client's area.
3. Check the client's own search terms (`search_terms.json`): converting terms that are not keywords yet are the best additions you will find (`search_term_review.py` section 4).
4. Group by intent and landing page, not by volume.
5. Before adding, check no live negative blocks the new keyword (the negative-keyword-audit gates do this).

## Pruning

- Keywords with spend over about 2x the account's cost per conversion and zero conversions over 90+ days: check the search terms they triggered, then pause or tighten.
- Quality Score 4 or lower with real spend: fix ad relevance and the landing page before raising bids.
- Do not pause a keyword because its own conversions are low if it feeds converting search terms in another ad group. Look at search terms, not just the keyword row.
