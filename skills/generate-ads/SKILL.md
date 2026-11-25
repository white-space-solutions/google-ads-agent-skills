---
name: generate-ads
description: Write high-performing Google Ads responsive search ads (15 headlines, 4 descriptions, paths) and campaign assets (sitelinks, callouts, structured snippets) that pass Google's editorial rules. Use when someone wants ad copy, RSAs, new ads for a campaign or ad group, ad refreshes, or campaign assets.
---

# Generate ads

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Read first (the spec and the rubric)

1. `docs/playbook/ads-rsa-spec.md`: RSA structure, the 6 headline patterns, pinning, editorial policy, Quality Score, self-review checklist.
2. `docs/playbook/ads-assets-spec.md`: sitelinks, callouts, structured snippets, business name and logo.
3. The niche pack's `ad-copy.md`: angles, proof rules and compliance for the industry.

Do not write from memory.

## Inputs (ask, never invent)

- The ad group and its keywords. Pull them if unsure: `scripts/pull.py --client ... --only keywords ads`.
- The exact landing page. Its H1 should match the pinned headline; flag a mismatch.
- Verified business facts: ratings, review counts, years in business, guarantees, response times, prices. **Never fabricate these.** If a number cannot be verified, use a claim that needs no proof ("No Fees", "Any Condition").

## Steps

1. 15 headlines: 3 keyword variants pinned to slot 1, 12 unpinned covering at least 5 angles (offer, trust, speed or guarantee, situation, CTA). Pin slot 1 only.
2. 4 descriptions, each a distinct angle, 61 to 90 characters.
3. path1 and path2, 15 characters each at most, matching the page.
4. For a full ad group: 3 RSAs, each testing a different lead angle, same final URL.
5. Assets unless told otherwise: 6 to 8 sitelinks (titles 12 to 15 characters, real distinct URLs), 8 to 12 callouts, 2 structured snippet headers with 4 to 10 values each.
6. Save `draft.json` in the validator format (see the header of `scripts/validate_ad.py`) and run `.venv/bin/python scripts/validate_ad.py draft.json`. Fix every ERROR; judge every WARNING.
7. Run the human-judgment checklist from both spec docs (angle coverage, page match, distinct meanings).

## Output

Tables of headlines (text, characters, pin, angle) and descriptions, paths, assets, and a "Facts used" list with where each came from. Plus `draft.json`.

## Approval

Never publish. A person reviews and adds the ads in the UI or Editor.
