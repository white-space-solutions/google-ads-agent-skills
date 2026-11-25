# Case study: a negative keyword rebuild that let sellers back in

**Account:** a cash home buyer in a high-cost metro, about $20k a month on Search. Names and figures rounded; client anonymized.

## What we found

- **20 shared negative lists, 6,094 terms**, built up over years by different people and tools. Nobody could say what each list was for.
- Twelve of the lists were attached across five campaigns. One list was account-level and also hit Performance Max.
- **42 campaign-level negatives blocked real sellers**: bankruptcy, tax, zillow, realtor, real estate agent, owner, redfin, rent, rental, apartment, address, and an exact [sell]. Each one looks like junk. Each one blocks searches like "sell house during bankruptcy", "sell house behind on property taxes", "sell house without realtor", "sell rental property".
- An ad group negative [house worth] blocked a valuation search the campaign was built to catch.
- Competitor review keywords had spent about $10,500 on people researching other companies.

## What we did

1. Pulled 18 months of search terms, every list, attachment, campaign and ad group negative through the API.
2. Wrote a five-list structure: Master, Out of Area, Platforms & Brokerages, Cash Buyer Competitors, Research & Reviews. 375 phrase roots.
3. Ran every proposed negative through four gates: no converting search term blocked, no live keyword blocked, no hand-written seller search blocked, no real seller search blocked. Iterated until all four were 0. Seven deliberate exceptions (competitor routing) were written down with reasons.
4. Coverage check: tested every old-list term against the new structure on 18 months of searches. Added 14 gap terms; accepted about $230 of low-spend gaps.
5. Backed up everything, created and attached the new lists, removed the 42 seller-blocking negatives, added the brand name as a negative on non-brand campaigns, detached the old lists (kept as backup).

## What happened

- **First week on the new lists: zero leaks** (no served search matched a live negative).
- **Both conversions in the generic campaign that week came from search terms the old lists would have blocked**: "we buy houses for cash" and "opendoor competitors".
- About 80 seller searches that the old lists had blocked started showing.
- The honest backtest: under current keywords, the old lists had blocked about 2 conversions and $2,161; the new lists newly blocked $379 of junk. The raw backtest across all history claimed +19 conversions, because most of those searches came from a broad match era the current keywords no longer trigger. Always backtest against what live keywords can trigger.

## Lessons

- The biggest win was removing bad negatives, not adding new ones.
- Comparison shoppers (iBuyer and "zillow cash offer" searches) converted at well below the account's average cost. Do not block iBuyer names.
- Keep a hand-written allow-list of customer searches and test every change against it.
- Weekly search term review is what keeps the structure clean. Old lists were deleted only after two clean weeks.
