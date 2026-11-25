# Launch plan: a new Google Ads account for a home buyer or wholesaler

For an account starting from zero, or one being rebuilt. Read with `keyword-themes.md`, `conversion-setup.md` and `landing-pages.md`.

## Before spending a dollar

1. **Tracking works end to end** (`conversion-setup.md`): a test form lead and a test call show up in the CRM with the GCLID, and the CRM can send qualified leads back to Google.
2. **Landing pages exist** for each theme you launch (`landing-pages.md`) and pass `scripts/landing_pages.py`.
3. **Someone answers the phone** during ad hours, or the call asset is off. Speed to lead matters more than bids: call back web leads within 5 minutes.
4. **Negative lists are attached** from day one (negative-keyword-audit skill; seed from `negatives.yaml`, with your cities in `service_area.include_terms` so you never negate your own market).
5. **Locations**: your counties or cities, location option **Presence**. Exclude places you will not buy.

## Budget

- Each Search campaign needs to buy 10 to 15 clicks a day to learn. At $30 to $60 per click (see `benchmarks.md`) that is roughly $300 to $900 a day per campaign in a competitive metro, less in smaller markets.
- If the total budget cannot fund that, launch **one** campaign, not three starved ones.
- Plan for 60 to 90 days before judging cost per contract. Judge weeks 1 to 4 on cost per lead and lead quality, then on cost per qualified lead.

## Order of launch

| Phase | Campaign | Why first |
|---|---|---|
| Week 1 | Sell House Fast (generic): sell house fast, cash buyers, as is | Highest volume of ready sellers |
| Week 1 | Branded (small budget, CPC cap) | Cheap, protects your name |
| Month 2 | Situations: inherited, foreclosure, landlords, divorce | Better leads once the core is learning |
| Month 2-3 | Competitors (if budget allows) | Higher CPC; needs its own budget |
| Month 3+ | Performance Max | Only after 30+ qualified leads a month are flowing back from the CRM |
| Test | Home Value | Small fixed budget, own page, 60-day test |

## Bidding

- Start with **Maximize Conversions** (or Manual CPC on very small budgets), optimizing toward a **lead** action.
- Switch the goal to **qualified lead** once the CRM uploads are reliable and you see 15 to 30 qualified leads a month.
- Add a target CPA only after about 30 conversions in 30 days on the goal you bid toward.
- Value-based bidding (Maximize Conversion Value, PMax) only once stage values are set and stable.

## First 90 days

| When | Do | Skill |
|---|---|---|
| Daily | Conversion heartbeat | conversion-tracking-audit |
| Twice a week, first month | Search term review; add junk, protect sellers | search-term-review |
| Weekly | Pacing, one test at a time, change log | ppc-weekly-routine |
| Day 30 | First audit | google-ads-audit |
| Day 30 to 60 | Expand to situation themes from converting search terms | keyword-research |
| Day 60 to 90 | Refresh ads; test a second landing page | generate-ads, landing-page-check |
