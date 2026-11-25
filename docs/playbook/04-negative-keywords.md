# 04 Negative keywords

Negatives are the highest-leverage and highest-risk lever in a lead gen account. Done right they cut a third or more of wasted spend. Done wrong they silently block your best customers, and nothing in the interface tells you.

## The rules

1. **Few themed lists.** Five to seven shared lists, each with one job, beat twenty lists nobody can audit. In one rebuild we went from 20 lists and 6,094 terms to 5 lists and 375 phrase roots, and blocked more waste.
2. **Phrase match roots.** A phrase negative blocks the words together and in order. Use the shortest root that never appears in a converting search. Negatives never expand to plurals or misspellings, so add those you need.
3. **Every negative passes the gates before it goes live:**
   - **G1** it does not block any search term that converted (whole history window, any campaign)
   - **G2** it does not block a live keyword in a campaign it attaches to
   - **G3** it does not block any search on the allow-list (hand-written customer searches)
   - **G4** it does not block any real search term that matches the customer-intent pattern
   A negative that must block a converting term on purpose (for example routing competitor names to the competitor campaign) goes in `accepted_exceptions` with a written reason.
4. **Route, do not just block.** Competitor names are negatives on generic campaigns so they run in the competitor campaign. Your brand is a negative on non-brand campaigns so it runs at brand CPCs. Review searches are negatives on generic campaigns only.
5. **Locations twice.** Cities you do not serve go in location exclusions (campaign settings) and in the out-of-area negative list, because people type a city while located elsewhere.
6. **Backtest honestly.** When you measure what a negative would have blocked, count only search terms your current keywords can still trigger. History from an old broad match era inflates the result. In one account the raw backtest said "+19 conversions"; under current keywords it was about 2.
7. **Back up, detach, then delete.** Take a backup, attach the new lists, detach the old ones, and delete the old lists only after two clean weekly reviews.

## Words that look like junk but are customers

Every niche has them. For seller-direct real estate: realtor, zillow, redfin, mortgage, tax, bankruptcy, rent, tenant, owner, address. Block the browsing phrase ("for rent", "mortgage rates", "realtor near me"), never the bare word. Check the niche pack's README for yours.

## The workflow (negative-keyword-audit skill)

```
pull.py --history-days 540          # 18 months of search terms
negatives_init.py                   # seed proposed.yaml from the niche pack
(edit proposed.yaml)
negatives_validate.py               # gates + review tabs -> validation.xlsx
(repeat edit/validate until G1-G4 are 0 and every review row has a decision)
negatives_apply.py                  # dry run
APPLY_ENABLED=1 negatives_apply.py --execute      # after a person approves
APPLY_ENABLED=1 negatives_apply.py --execute --retire-old   # after checking attachments
```

## proposed.yaml format

```yaml
prefix: ACME
lists:
  - name: "ACME | Master Negatives"
    match: PHRASE
    attach_to: [generic, competitors, brand]     # campaign roles from the client yaml
    groups:
      Jobs and education: [jobs, careers, salary]
  - name: "ACME | Brands - Competitors"
    match: PHRASE
    attach_to: [generic, brand]                  # NOT competitors
    groups:
      Competitors: [other company name]
campaign_level:
  - {term: acme home buyers, match: PHRASE, attach_to: [generic, competitors]}
accepted_exceptions:
  other company name: "Routed to the competitor campaign, which bids on it."
exempt_from_intent_gate: ["ACME | Brands - Competitors"]
```

## Reading validation.xlsx

| Tab | What to do |
|---|---|
| Gates | All four must be 0. |
| G1 to G4 | Narrow the negative (longer phrase) or remove it. Narrow beats delete. |
| Accepted exceptions | Confirm each reason still holds. |
| Current conflicts | Live negatives hurting you today. These are often the biggest win: remove them. |
| Impact | Spend each negative would have blocked, total and under live keywords only. A negative that blocks nothing is fine as protection if deliberate. |
| Gap n-grams | Zero-conversion spend the lists still let through. Add a root only if "Converting terms containing it" is 0. Ignore addresses and one-off names. |
