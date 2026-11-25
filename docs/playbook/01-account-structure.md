# 01 Account structure

## Campaigns by intent, not by keyword count

Split campaigns where the budget decision differs, not where the keywords differ. A typical lead generation account:

| Campaign | Role | Why it is separate |
|---|---|---|
| Generic intent (the core service) | generic | Most volume. Gets most of the budget. |
| Situation or sub-service | generic | Different landing pages, often better leads, lower volume. |
| Competitors | competitors | Higher CPC, different success bar, needs its own budget so it cannot starve the core. |
| Brand | brand | Cheap, protects your name. Target impression share with a CPC cap. |
| Test (for example valuation) | valuation or other | New idea with a fixed budget and an end date. |
| Performance Max | other | Runs alongside Search. See chapter 07. |

Ad groups: one theme each, 5 to 20 tightly related keywords, one landing page that matches the theme.

## Campaign roles in this repo

The client yaml maps campaign name prefixes to roles. Scripts use roles to decide which negative lists attach where and how to read search terms:

```yaml
campaign_roles:
  generic: ["Sell House Fast", "Situations"]
  competitors: ["Competitors"]
  brand: ["Branded"]
```

Name campaigns so the prefix is stable. Renaming a campaign changes its role.

## Settings that quietly waste money

| Setting | Use | Why |
|---|---|---|
| Location option | Presence | "Presence or interest" shows ads to people outside your area who searched about it. |
| Networks on Search | Google Search only to start | Display inside a Search campaign burns budget at low intent. Test search partners separately. |
| Auto-tagging | On | Without GCLIDs, offline conversion uploads cannot match clicks. |
| Ad schedule | Hours someone answers the phone, if calls matter | A missed call is the most expensive click in the account. |
| Auto-applied recommendations | Off | They add broad match keywords and change bids without review. |

## Budgets

- Each Search campaign should be able to buy at least 10 to 15 clicks a day at current CPCs. Below that it cannot learn.
- If a campaign loses more than 50% of impression share to budget for two weeks, fund it or fold it.
- Target CPA or target ROAS only after 30 or more conversions in 30 days on the action it optimizes for. Before that, Maximize Conversions with a sensible budget, or Manual CPC on small accounts.
