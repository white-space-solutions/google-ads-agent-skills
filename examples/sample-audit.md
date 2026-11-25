# Example output: Google Ads audit

*Fictional business, real patterns. This is what the google-ads-audit skill produces.*

# Desert Cash Home Buyers: Google Ads audit
Oct 28, 2026 · account 000-000-0000

## Summary

Qualified leads fell from 67 in July to 42 in October while spend held at about $18k a month, and cost per qualified lead roughly doubled in both non-brand Search campaigns. The account is well built in places (custom bidding goals, CRM uploads, clean negative routing), so the fixes are about signal stability and where the budget goes, not a rebuild.

Top fixes, ranked by expected impact:

1. **Lock the conversion value model.** Qualified Lead value moved from $225 to $1,119 since mid-August. Performance Max bids on value, so its target keeps moving.
2. **Give each conversion action one upload owner.** Three systems write to the same actions; one backfill had 301 failed rows.
3. **Rebuild Competitors off its single broad keyword.** It drifts into listings, rentals and Zillow searches.
4. **Fund or fold the starved search campaigns.** Two campaigns lose about 90% of impression share to budget at roughly $53 a click.
5. **Fix negatives that block real sellers.** "mortgage" and "realtor" block pre-foreclosure and FSBO searches in Performance Max.
6. **Test a valuation campaign.** "How much is my house worth" searches produced 10 qualified leads for $490 over the year, and no campaign owns them.

Nothing in the account was changed for this audit.

## Account snapshot (last 90 days)

| Campaign | Bidding | Budget/day | Spend | Qualified leads | Cost per QL | IS lost to budget |
|---|---|---|---|---|---|---|
| Performance Max | Max conv. value | $370 | $35,652 | 133.5 | $267 | 22% |
| Competitors | Max conv., tCPA $450 | $125 | $11,583 | 20.7 | $560 | 90% |
| Sell House Fast | Max conv., tCPA $450 | $110 | $5,969 | 9.5 | $628 | 88% |
| Branded | Target IS, $25 cap | $100 | $3,291 | 8.0 | $411 | 1% |

## Conversion data

| Action | Jun to mid-Aug | Late Aug to Sep | October |
|---|---|---|---|
| Qualified Lead | $225 flat | $405 to $617 | $890 to $1,119 |
| All Appointments (secondary) | $4,000 | $2,700 to $4,000 | $1,600 |

In October an appointment became worth less than two qualified leads, the reverse of July. Recommendation: set one value per stage from close rate x average assignment fee, write it down, change it at most once a quarter.

*(The full report continues with search terms and negatives, budget and structure, ads and landing pages, opportunities and next steps.)*
