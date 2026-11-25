---
name: landing-page-check
description: Check every Google Ads landing page for broken links, redirects, speed, a visible form or phone number, and match with the ads that point to it. Use before turning ad spend on, after a website change, when conversion rate drops, or as part of an audit.
---

# Landing page check

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Steps

1. `scripts/pull.py --client ... --only landing_pages ads`
2. `scripts/landing_pages.py --client ...` writes `work/<slug>/reviews/landing-pages.md`.
3. For every flagged URL, open it and confirm: the status, where it redirects, whether the form or phone is above the fold on mobile, and whether the headline matches the ad group's pinned headline.
4. Check tracking: submit a test lead with `?gclid=TEST123` on the URL and confirm the CRM record stores the GCLID and UTMs (ask the person to check the CRM if you cannot).
5. Read `docs/playbook/06-landing-pages.md` and list fixes, most spend first.

## Approval

Read-only. Website changes go to whoever owns the site.
