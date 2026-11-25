---
name: ppc-weekly-routine
description: Run the weekly Google Ads management routine for one client or a whole roster - conversion heartbeat, search term review, budget pacing, and a short approval list. Use for the weekly PPC check-in, "what needs attention in the ad accounts", or when setting up scheduled PPC management.
---

# Weekly PPC routine

Orchestrates the other skills. Follow `docs/playbook/08-weekly-rhythm.md`.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## For each client yaml in `clients/` (skip `example.yaml`)

1. `scripts/conversion_health.py --client <yaml>`. Any primary action quiet, upload failing or value moved: put it at the top of the note.
2. `scripts/pull.py --client <yaml> --days 30 --only campaign_perf campaign_month search_terms keywords`
3. Search-term-review skill (7 days).
4. Pacing: from `campaign_perf.json`, list campaigns losing over 30% impression share to budget and campaigns spending under 70% of budget.
5. Compare with last week's note in `work/<slug>/reviews/`: did last week's changes do what we expected?

## Output

One note per client, then a roster summary:

```markdown
# PPC weekly: <date>
| Client | Spend 7d | Conv 7d | Cost/conv | vs prior 4 wks | Alerts | Approvals needed |
## <Client>
- Alerts:
- Approve: (numbered, each with evidence and the command that applies it)
- Watching:
```

## Approval

The routine is read-only. Approved items are applied through the apply-google-ads-changes skill.
