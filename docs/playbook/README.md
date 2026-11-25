# The Google Ads playbook

How we run Google Ads for lead generation businesses with AI agents doing the analysis and people approving the changes. The rules here come from auditing and rebuilding real accounts in 2026. The niche packs (`niches/`) add industry specifics on top.

## Principles

1. **Fix the signal before the bids.** Smart bidding optimizes toward whatever you report as a conversion. If the conversion data is wrong, late, double counted or keeps changing value, no keyword or bid change will hold. Audit conversions first, every time.
2. **Measure qualified leads, not form fills.** Feed CRM outcomes (qualified, appointment, contract) back to Google with offline conversion uploads, and judge campaigns on cost per qualified lead.
3. **Never block a customer to save a click.** Most accounts we open lose more to bad negatives than they save. Every negative keyword is tested against what actually converted before it goes live.
4. **Fund it or fold it.** A campaign that loses most of its impression share to budget cannot learn. Give it the budget or merge its keywords into one that has it.
5. **Change one thing, then watch it.** Big simultaneous changes make results impossible to read. Log every change with the reason.
6. **The agent proposes, a person approves.** Reads are free. Every write is a dry run first, backed up, logged, and needs a human yes.

## Chapters

| # | Chapter | Read before |
|---|---|---|
| 01 | [Account structure](01-account-structure.md) | Building or restructuring campaigns |
| 02 | [Conversion tracking](02-conversion-tracking.md) | Any audit; any bidding change |
| 03 | [Keywords](03-keywords.md) | Adding keywords, match type changes |
| 04 | [Negative keywords](04-negative-keywords.md) | Any negative keyword change |
| 05 | [Ads](05-ads.md), with the [RSA spec](ads-rsa-spec.md) and [assets spec](ads-assets-spec.md) | Writing ads or assets |
| 06 | [Landing pages](06-landing-pages.md) | Turning spend on, new ad groups |
| 07 | [Performance Max](07-performance-max.md) | Running PMax next to Search |
| 08 | [Weekly operating rhythm](08-weekly-rhythm.md) | Setting up ongoing management |
| 09 | [Making changes safely](09-safe-changes.md) | Running any write script |

Case studies: [negative keyword rebuild](../case-studies/negative-keyword-rebuild.md), [conversion value drift](../case-studies/conversion-value-drift.md).
