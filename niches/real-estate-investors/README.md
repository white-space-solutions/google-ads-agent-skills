# Niche pack: real estate investors buying direct from sellers

For home buyers, wholesalers and "we buy houses" companies that run Google Ads to reach homeowners who want to sell. Everything here was learned running and auditing these accounts in 2026: seller-intent search, Performance Max, competitor conquesting, CRM-qualified conversions.

Set `niche: real-estate-investors` in the client yaml and the scripts pick up:

| File | Used by | What it is |
|---|---|---|
| `negatives.yaml` | `negatives_init.py` | Five themed starter lists (about 370 phrase terms) and where each attaches |
| `allow-list.txt` | gates G3, audit, search term review | Seller searches that must never be blocked |
| `intent.yaml` | gate G4, search term review | Regex that recognises a real seller search |
| `seed-keywords.txt` | `keyword_ideas.py --seeds-from-niche` | Seeds for Keyword Planner |
| `keyword-themes.md` | keyword-research skill | Campaign and ad group architecture by intent |
| `ad-copy.md` | generate-ads skill | Angles, proof points and compliance notes for seller ads |
| `benchmarks.md` | audit skill | What "good" looks like for CPC, cost per lead, cost per qualified lead |

## How sellers search

Intent tiers, highest to lowest value:

1. **Direct cash-sale intent.** "sell my house fast", "we buy houses", "cash home buyers near me", "cash offer for my house". The core of every account.
2. **Situation searches.** Inherited, probate, divorce, foreclosure, behind on taxes, tenants, needs repairs, hoarder, fire damage. Lower volume, often the best leads, because the problem forces a sale.
3. **Comparison shoppers.** "opendoor vs offerpad", "how does opendoor work", "zillow cash offer", "we buy houses reviews". Sellers weighing options. Do not block iBuyer names: in one account these searches converted at about 40% below the account's average cost per conversion.
4. **Valuation.** "how much is my house worth". Mostly browsers, but in one account these produced 10 qualified leads for $490 over a year with no campaign owning them. Worth a small, separate test campaign with its own landing page.
5. **Competitor names.** Other cash buyers. Works only as its own campaign with exact and phrase match keywords on each name. Never on a single broad keyword.

## Words that look like junk but are sellers

These get blocked by mistake in almost every account we open. Blocking them cost real conversions:

- **realtor, real estate agent, redfin, zillow**: FSBO sellers and sellers comparing listing vs cash ("sell house without realtor", "redfin agent fee").
- **mortgage, bankruptcy, tax, lien**: pre-foreclosure and distressed sellers ("sell house with mortgage", "sell house behind on property taxes").
- **rent, rental, tenant, landlord, owner**: tired landlords ("sell rental property", "sell house with tenants").
- **address**: used by sellers too. Block "office address" and "headquarters", not "address".

Block the browsing form instead: "for sale", "for rent", "mortgage rates", "realtor near me".

## Campaign roles

The scripts map campaigns to roles by name prefix (`campaign_roles` in the client yaml):

| Role | Typical campaigns | Lists attached |
|---|---|---|
| generic | Sell House Fast, Cash Buyers, Situations | Master, Out of Area, Platforms, Cash Buyer Competitors, Research |
| competitors | Competitors | Master, Out of Area, Platforms |
| brand | Branded | Master, Out of Area, Platforms, Cash Buyer Competitors |
| valuation | Home Value | Master, Out of Area, Platforms, Cash Buyer Competitors, Research |

Plus the client's own brand as a phrase negative on generic and competitor campaigns, so brand searches go to the brand campaign at brand CPCs.

Performance Max cannot take shared negative lists the same way. Use the account-level negative keyword list for the worst offenders, brand exclusions, and the search term categories report (`pmax_search_categories.json`) to see where it spends.
