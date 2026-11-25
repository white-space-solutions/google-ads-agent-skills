---
name: keyword-research
description: Find and organize Google Ads keywords by intent into ad group themes with volume and bid data, using Keyword Planner and the account's own converting search terms. Use when building a new campaign or ad group, expanding into a new city or service, or when someone asks what keywords to target.
---

# Keyword research

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Steps

1. Read the niche pack's `keyword-themes.md` and `docs/playbook/03-keywords.md`.
2. Set `service_area.geo_target_ids` in the client yaml (Google geo target constant IDs for the cities or metro).
3. `scripts/keyword_ideas.py --client ... --seeds-from-niche` and/or `--seeds "<seed>" ...`. Output: `work/<slug>/research/keyword-ideas.csv`.
4. If the account has history: `scripts/pull.py --client ... --only search_terms keywords` and pull converting search terms that are not keywords yet. These beat any planner idea.
5. Group into themes: one intent, one landing page per ad group. Drop anything that matches the niche's negative lists or is research or job intent.
6. For each theme give: keywords (phrase and exact), monthly volume, top-of-page bid range, landing page, and the reason it exists.
7. Check every proposed keyword against live negatives so nothing new is born blocked (negatives_validate.py gate G2 catches this once keywords exist).

## Output

`work/<slug>/research/keyword-plan.md`: a table per campaign and ad group, plus a short note on budget needed to buy 10 to 15 clicks a day per campaign at the bid range.

## Approval

Research only. Creating campaigns and keywords is done by a person in the UI or Google Ads Editor from the plan.
