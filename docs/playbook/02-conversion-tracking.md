# 02 Conversion tracking

Smart bidding is only as good as the conversions you report. In the accounts we audit, a broken or shifting conversion signal is the single most common cause of rising cost per lead, and it is invisible from the campaign view.

## What good looks like

1. **One primary action per funnel stage.** Lead, qualified lead, appointment, contract. Everything else is secondary (observed, not bid on).
2. **Bid on the deepest stage with enough volume.** Usually qualified lead. Raw form fills reward junk.
3. **CRM outcomes come back as offline conversion uploads,** matched by GCLID (and hashed email/phone with enhanced conversions for leads).
4. **One upload owner per action.** One pipeline (your CRM integration, Zapier, n8n, a script) writes to each action. Two writers double count and send conflicting values.
5. **Stable values.** Set each stage's value from your own numbers (stage-to-close rate x average profit), write it down, and change it at most once a quarter.
6. **A daily heartbeat.** Something checks every day that each primary action recorded conversions in its normal window and that uploads succeeded.

## Why value drift hurts

Value-based bidding (Maximize Conversion Value, tROAS, and Performance Max by default) chases the value you report. If "qualified lead" is worth $225 one month and $1,100 two months later, the system re-learns what to buy each time, and the relationship between stages flips (an appointment can become worth less than two qualified leads). See the [conversion value drift case study](../case-studies/conversion-value-drift.md).

## Audit checklist

Run `scripts/conversion_health.py`, then check:

- [ ] Auto-tagging on; enhanced conversions for leads on if you upload offline conversions.
- [ ] Every primary action recorded conversions in the last 7 days (or its normal cadence).
- [ ] No action has two or more upload clients.
- [ ] Upload success rate above 90%; failed rows explained.
- [ ] Value per conversion stable week to week; changes are documented decisions.
- [ ] No near-duplicate actions ("Qualified Lead" and "All Qualified Leads") both counting.
- [ ] Each campaign bids toward the goal you think it does (campaign conversion goals).
- [ ] Phone calls: one call action per source (call asset, website calls, GA4), not three counting the same call.
- [ ] Lookback windows match your sales cycle (seller leads often qualify days after the click).

## Qualification lag

Leads get marked qualified days or weeks after the click. The last two weeks always look worse than they will end up. Compare like-for-like windows, or judge recent weeks on leads and older weeks on qualified leads.
