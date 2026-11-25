# Case study: conversion value drift and a slipping Performance Max

**Account:** a cash home buyer in a mid-size market, about $18k a month, Performance Max plus three Search campaigns, CRM outcomes uploaded as offline conversions. Client anonymized.

## The symptom

Qualified leads fell from 67 in July to 42 in October while spend held. Cost per qualified lead roughly doubled in both non-brand Search campaigns. Performance Max, which carried 62% of spend and most of the qualified leads, got steadily more expensive month over month.

## What the audit found

1. **The value model kept moving.** "Qualified Lead" went from a flat $225 to $405-617 to $890-1,119 in about ten weeks. Appointment values moved the other way. Performance Max bid on value across both, so its target kept shifting, and by October an appointment was worth less than two qualified leads: the reverse of July.
2. **Three upload pipelines wrote to the same actions.** The API integration, an automation tool, and a stopped data connector. One backfill sent 449 qualified lead rows and 301 failed. "Qualified Lead" had two writers: double counting risk across different clicks from the same lead.
3. **29 enabled conversion actions,** including near-duplicate pairs (Qualified Lead / All Qualified Leads, Under Contract / All Under Contract) and three click-to-call actions.
4. **Two search campaigns lost about 90% of impression share to budget** at roughly $53 a click. They could not learn and cost $600 to $1,100 per qualified lead.
5. **A competitor campaign ran on one broad keyword** that drifted into listings, rentals and Zillow searches.
6. **Negatives "mortgage" and "realtor" blocked pre-foreclosure and FSBO sellers** in Performance Max, while 31% of one search campaign's recent spend went to competitor and platform searches.
7. **Valuation searches** ("how much is my house worth") had produced 10 qualified leads for $490 in a year, with no campaign owning them.

## Recommendations, ranked

1. Lock the value model: one value per stage from close rate x average assignment fee, documented, changed at most quarterly.
2. One upload owner per action, with a daily silent-day check.
3. Rebuild the competitor campaign on exact and phrase keywords per name.
4. Fund or fold the starved search campaigns.
5. Fix the seller-blocking negatives and plug the competitor leaks.
6. Test a valuation campaign with its own page.

## Lessons

- Look at conversion values by week before touching a single bid.
- "Who writes to this action?" is a question every audit should answer in writing.
- The account was well built in places. The fix was signal stability and budget allocation, not a rebuild.
