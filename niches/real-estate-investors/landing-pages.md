# Landing pages for seller leads

Read with `docs/playbook/06-landing-pages.md`. Run `scripts/landing_pages.py` before spend goes on.

## One page per theme

| Ad group theme | Page headline idea | First-screen promise |
|---|---|---|
| Sell house fast | Sell Your House Fast in {City} | Cash offer in 24 hours, close on your date |
| Cash buyers | We Buy Houses in {City} for Cash | No fees, no commissions, no repairs |
| As is | Sell Your House As-Is | No cleaning, no showings, no repairs |
| Inherited / probate | Inherited a House in {City}? | We handle the paperwork and the cleanout |
| Foreclosure / behind on payments | Behind on Payments? Sell Before It Gets Worse | Talk to a local buyer this week (no legal or foreclosure relief claims) |
| Landlords | Sell Your Rental, Tenants and All | No need to wait for a vacancy |
| Home value | What Is Your House Worth? | Instant range, then a cash offer if you want one |

## Above the fold

- Headline that repeats the ad's promise and the city.
- A short form: name, phone, property address. Email optional. Every extra field costs leads.
- A clickable phone number on mobile.
- One line of proof you can back up: years buying locally, houses bought, a review rating.

## Below the fold

- How it works in three steps (call or form, see the house, pick a closing date).
- Situations you handle (inherited, tenants, repairs, behind on payments, divorce).
- Real reviews with first names and neighborhoods, if you have them.
- A comparison: listing with an agent vs selling to you (fees, repairs, time to close).
- FAQ: Is this a real offer? Do I pay anything? How fast can you close? What if I owe more than it's worth?

## Technical must-haves

- Loads in under 3 seconds on mobile; no pop-ups covering the form.
- Hidden fields for `gclid`, `gbraid`, `wbraid`, UTMs and page variant, saved to the CRM (`conversion-setup.md`).
- Thank-you state that fires the Google Ads lead conversion once, not on every page view.
- No navigation menu that leads away from the form. Keep a footer with your business name, address and privacy policy (Google checks).
- Business name and logo match the ad's business name asset.

## Compliance

- Do not imply you are a lender, a government program, or a foreclosure rescue service.
- Do not promise a price or a close date you cannot keep.
- Say clearly you are a buyer, not the seller's agent.
- Follow your state's rules on wholesaling disclosures and on contacting sellers.
