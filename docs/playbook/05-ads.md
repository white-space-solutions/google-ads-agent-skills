# 05 Ads

The full specs live in [ads-rsa-spec.md](ads-rsa-spec.md) (responsive search ads: structure, headline patterns, pinning, editorial rules, Quality Score) and [ads-assets-spec.md](ads-assets-spec.md) (sitelinks, callouts, structured snippets, business name and logo). The generate-ads skill reads both and validates drafts with `scripts/validate_ad.py`.

The short version:

- 15 headlines, 4 descriptions per RSA. Pin only slot 1, with three keyword variants.
- Cover at least five angles: keyword, offer, trust, speed or guarantee, call to action.
- Two to three RSAs per ad group, each testing a different angle, same landing page.
- Every claim (ratings, years, counts, guarantees) must be true and on the landing page. Never invent proof.
- Talk about the customer, not "we".
- Layer assets: 6 to 8 sitelinks, 8 to 12 callouts, 2 structured snippet headers. Together they add 20% or more CTR at no extra cost.
- Judge ads on conversion rate and cost per qualified lead, not Ad Strength. Ad Strength is a hint.
