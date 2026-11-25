---
name: apply-google-ads-changes
description: The safety protocol for making any change to a live Google Ads account - dry run, human approval, backup, execute, verify, log, and how to roll back. Use whenever an approved change is about to be written to Google Ads, or when someone asks to undo or restore a change.
---

# Apply Google Ads changes

Read `docs/playbook/09-safe-changes.md`. These rules are not optional.

## Requires

This skill runs the scripts in the [google-ads-agent-skills](https://github.com/white-space-solutions/google-ads-agent-skills) repo. If `scripts/gads.py` is not in the working directory, clone the repo and work from its root. Credentials: `.env` (see `docs/setup.md`). Client config: `clients/<name>.yaml`. Python: `.venv/bin/python` after `pip install -r requirements.txt`.

## Protocol

1. **Dry run.** Run the write script without `--execute`. Every operation goes to Google with `validate_only`; nothing changes. Show the person the full output.
2. **Get an explicit yes** for exactly what the dry run showed. A yes to "add negatives" is not a yes to "retire old lists".
3. **Backup.** `negatives_apply.py` takes one automatically if none exists in the last 24 hours. For other changes, run `scripts/negatives_backup.py` or export the affected settings first.
4. **Execute** with the kill switch set for that one command only:
   `APPLY_ENABLED=1 .venv/bin/python scripts/negatives_apply.py --client <yaml> --execute`
   Never export `APPLY_ENABLED` into the shell profile or a scheduled job.
5. **Verify.** Re-pull and confirm the change is live (lists attached, terms present). Check the UI if the person wants.
6. **Log.** Scripts append to `work/<slug>/changes.log.jsonl`. Add one line to the weekly note: what changed, why, what we expect to see.
7. **Watch.** Run search-term-review after 7 days.

## New campaigns

Use the build-campaign skill. It follows this protocol and adds two rules: the campaign is created paused, and enabling it is a second approval (`campaign_build.py --enable`).

## Roll back

- Negatives: `scripts/negatives_restore.py --client <yaml> --backup work/<slug>/backups/negatives-<stamp>` (dry run), then with `APPLY_ENABLED=1 ... --execute`.
- Detached lists: reattach in the UI or rerun restore.
- A new campaign: it was created paused; remove it in the UI. `work/<slug>/build/<campaign>.applied.json` lists what was created.

## Refusals are features

If a script refuses (customer ID not on the allowlist, op cap, gates not 0, validation older than the proposal), fix the cause. Do not edit the safety settings to get past it without the person's say-so.

## Quota

Explorer-level developer tokens have a low daily mutate quota. If writes fail on quota, stop, report what was applied (changes.log.jsonl), and finish the rest the next day or in the UI.
