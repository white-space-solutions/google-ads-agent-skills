# Scripts

Every script takes `--client clients/<slug>.yaml` and writes under `work/<slug>/`. Read-only unless marked.

| Script | Does | Writes to Google Ads |
|---|---|---|
| `gads.py` | Shared helpers: credentials, config, GAQL, matching rules, write guard | - |
| `check_connection.py` | Checks credentials and which login customer ID works | No |
| `get_refresh_token.py` | One-time OAuth to create the refresh token | No |
| `pull.py` | All read-only pulls to `work/<slug>/data/*.json` | No |
| `audit.py` | Deterministic checks to `audit/facts.md` and `findings.json` | No |
| `conversion_health.py` | Conversion actions, uploads, values, goals | No |
| `search_term_review.py` | Weekly search term report | No |
| `landing_pages.py` | HTTP checks on every landing page with clicks | No |
| `keyword_ideas.py` | Keyword Planner ideas for the service area | No |
| `negatives_init.py` | Seeds `negatives/proposed.yaml` from the niche pack | No |
| `negatives_validate.py` | Gates G1 to G4 and review tabs to `validation.xlsx` | No |
| `negatives_backup.py` | Full backup of every negative | No |
| `negatives_apply.py` | Create, attach, add, remove, retire. Dry run by default | Yes, gated |
| `negatives_restore.py` | Restore from a backup. Dry run by default | Yes, gated |
| `validate_ad.py` | Checks a draft RSA and assets against editorial rules | No |
| `package_skills.py` | Builds `dist/*.skill` | No |
