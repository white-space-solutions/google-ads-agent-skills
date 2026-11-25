# 06 Landing pages

The ad gets the click; the page gets the lead. Most "Google Ads is not working" accounts have a page problem hiding behind a bidding problem.

## Before spend goes on

Run `scripts/landing_pages.py`. It checks every URL that received clicks or sits in an enabled ad:

- [ ] Returns 200, no redirect chains, loads in under 3 seconds
- [ ] Has a form or click-to-call above the fold
- [ ] The headline matches the ad group's pinned headline
- [ ] Tracking parameters survive redirects (GCLID must reach the form)

Paused campaigns pointing at 404 pages are common. Fixing them is free while spend is off and expensive after.

## One page per theme

A page per ad group theme converts better than one homepage for everything. Situation searches (inherited house, foreclosure, divorce) convert noticeably better on a page that speaks to the situation in the first screen.

## What belongs on a lead gen page

- The promise from the ad, in the headline.
- A short form (name, phone, address or the one field that qualifies) and a phone number.
- Proof: reviews, a real photo, how it works in three steps.
- No navigation that leads away from the form.
- The hidden fields your CRM needs for offline conversions: GCLID, UTM source/medium/campaign, landing page variant.
