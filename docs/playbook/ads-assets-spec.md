# Ad assets: the CTR multipliers (2026)

Best practices for **sitelinks, callouts, structured snippets, business name and business logo**: the assets that wrap your RSAs and lift CTR 10-25% without adding cost. Sourced from 30+ PPC blogs, agency benchmarks and Google's asset documentation.

**Use this as the spec the agent reads before generating campaign assets, and as the rubric a person reviews against before publishing.**

---

## 1. Why assets matter

Assets are the extras that show below or beside your ad. They:

- **Cost nothing per impression**: only clicks cost money
- **Cost the same per click**: a sitelink click costs the same as a headline click
- **Take more screen**: ads with assets cover 2-3x the space
- **Push competitors below the fold**, especially on mobile

| Asset | Typical CTR lift | Source |
|---|---|---|
| Sitelinks (4+) | +10-15% | SearchScientists 2026 |
| Callouts (6+) | +5-15% | AdNabu 2026 |
| Structured snippets | +3-8% | StoreGrowers 2026 |
| Business name + logo | +2-5% (brand trust) | Google 2026 |
| **All layered together** | **+20-25%** | Multiple 2026 sources |

Each asset adds a few percent; layered, they compound.

---

## 2. The five assets every service business should have

In priority order. Skip assets that don't apply; never invent data to fill them.

### 2.1 Sitelinks (must have: biggest single lift)

Two to six extra clickable links below the ad, each to a specific page.

| Field | Limit | Best practice |
|---|---|---|
| Title | 25 chars (15 visible on mobile) | **Aim for 12-15 chars** |
| Description line 1 | 35 chars | Recommended |
| Description line 2 | 35 chars | Recommended |
| Quantity per campaign | up to 20 | **Add 6-8**; Google rotates the best |
| Minimum to show any | 2 | Fewer and none appear |

Rules:

- Each sitelink points to a **distinct page** that matches its title.
- No generic labels (`Learn More`, `Contact`, `About Us` alone). They kill CTR.
- Match the campaign theme.
- Use ad-group-level sitelinks when sub-services differ.

### 2.2 Callouts (must have)

Short, non-clickable text shown inline with the ad.

| Field | Limit | Best practice |
|---|---|---|
| Text | 25 chars | **Aim for 10-20 chars** |
| Quantity | up to 20 per level | **Add 8-12**; Google shows 4-10 |
| Minimum to show any | 2 | Fewer and none appear |

Rules:

- **Differentiate**: "24/7 Support" is wasted if every competitor says it.
- **Don't repeat** headline or description claims; assets layer, they don't substitute.
- **One claim per callout.**
- **Cover angles**: speed, trust, price, guarantee.

### 2.3 Structured snippets (should have)

A header from Google's list plus 3-10 values. Non-clickable.

| Field | Limit | Best practice |
|---|---|---|
| Header | Google's list (Services, Types, Brands, Neighborhoods, etc.) | **Services** or **Types** for service businesses |
| Each value | 25 chars | **Aim for 8-15 chars** |
| Values per header | 3 minimum | Add 4-10 |
| Headers | Several allowed | **Add 2** with different groupings |

Rules:

- Don't duplicate sitelink categories.
- Every value must be something you actually offer and mention on the landing page.

### 2.4 Business name (must have: quick win)

- Up to 25 characters.
- Must match the domain or the verified legal entity name.
- Required for the logo to show.
- Don't stuff keywords into it; Google rejects that.

### 2.5 Business logo (should have)

| Format | Dimensions | Notes |
|---|---|---|
| Square (1:1) | 1200×1200 recommended, 128×128 minimum | Primary slot |
| Horizontal (4:1) | 1200×300 recommended, 512×128 minimum | Optional |
| File type | PNG (transparent background preferred) or JPG | 5120 KB max |

No text overlays, no inverted or single-color logos, and the logo must also appear on the landing page.

---

## 3. Assets to skip for most service businesses

| Asset | Why |
|---|---|
| Images | Mixed results unless you have real photos of the work (not stock) |
| Prices | Bad fit for variable-quote services |
| Promotions | Only for a real limited-time offer; never fake urgency |
| Messages | Rarely used by these audiences |
| Lead form | Only once a real landing page exists |
| Call asset | Only if a person answers during ad hours; missed calls are the most expensive clicks |

---

## 4. Where to attach each asset

| Level | Best for | Example |
|---|---|---|
| Account | Claims true everywhere | "Licensed & Insured", "Family-Owned" |
| Campaign | Theme-specific claims | Emergency campaign: "60-Min Response" |
| Ad group | Keyword-specific links | "Hot Water" ad group sitelinks to hot water pages |

Lower levels override higher ones. Start at campaign level; move universal claims to account level as you add campaigns.

---

## 5. Self-review checklist

Sitelinks

- [ ] 4-8 sitelinks, titles 12-15 chars
- [ ] Each to a distinct, real URL; no generic titles
- [ ] Descriptions added (35 chars each)

Callouts

- [ ] 8-12 callouts, each ≤ 25 chars
- [ ] Differentiated, no repeats of headline claims, 4+ angles

Structured snippets

- [ ] 2 headers, 4-10 values each, each ≤ 25 chars
- [ ] Every value is offered and on the landing page

Business name and logo

- [ ] Name ≤ 25 chars and matches domain or legal entity
- [ ] Square logo 1200×1200, not a solid color, also on the landing page

---

## 6. Example asset config (fictional plumber)

```yaml
business_name: "Acme Plumbing"
business_logo: "/path/to/acme-logo-1200.png"  # square 1:1

sitelinks:
 - title: "Blocked Drains"
   description_1: "Same-day camera inspection"
   description_2: "No callout fee weekdays"
   final_url: "https://acmeplumbing.example/blocked-drains"
 - title: "Hot Water Repair"
   description_1: "All brands · 10-yr warranty"
   description_2: "Same-day install available"
   final_url: "https://acmeplumbing.example/hot-water"
 - title: "Free Quote"
   description_1: "Written estimate in 2 minutes"
   description_2: "No obligation"
   final_url: "https://acmeplumbing.example/quote"

callouts: ["24/7 Service", "$0 Callout Fee", "Licensed & Insured", "10-Year Warranty", "On-Site in 60 Min",
           "Family-Owned", "Upfront Pricing", "No Hidden Fees", "Same-Day Service"]

structured_snippets:
 - header: "Services"
   values: ["Drains", "Hot Water", "Gas Fitting", "Toilets", "Pipe Repair"]
 - header: "Types"
   values: ["Emergency", "Same-Day", "Routine", "Inspection"]
```

For seller-direct real estate examples, see `niches/real-estate-investors/ad-copy.md`.

---

## Sources

- [Google Ads Help · About business information](https://support.google.com/google-ads/answer/12497613)
- [Google Ads Help · Business information requirements](https://support.google.com/adspolicy/answer/12499303)
- [Google Ads Help · About structured snippet assets](https://support.google.com/google-ads/answer/6280012)
- [Google Ads Help · Ad formats, sizes, and best practices](https://support.google.com/google-ads/answer/13676244)
- [SearchScientists · 25+ Sitelinks That Convert](https://www.searchscientists.com/adwords-help-sitelink-extensions/)
- [AdNabu · Google Ads Callout Extensions Guide 2026](https://blog.adnabu.com/google-ads/google-ads-callouts/)
- [Store Growers · Structured Snippet Extensions](https://www.storegrowers.com/structured-snippet-extensions/)
- [SearchEngineLand · Callouts vs Structured Snippets](https://searchengineland.com/google-ads-callouts-structured-snippets-460029)
- [TwoTreesPPC · Complete Guide To Google's Ad Extensions 2026](https://twotreesppc.com/resources/complete-guide-to-google-ad-extensions)

*Re-validate quarterly; Google's asset options change often.*
