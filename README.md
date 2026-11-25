# Google Ads Agent Skills

**Open-source Google Ads skills for AI agents.** Point Claude Code, Claude Cowork, Codex, a Grok bot or any agent that can run Python at a Google Ads account, and it can audit the account, check conversion tracking, rebuild negative keywords without blocking real customers, run the weekly search term review, research keywords, write ads and check landing pages. Every change is a dry run first and needs a person's approval.

Built by [White Space Solutions](https://whitespacesolutions.ai) from audits and rebuilds of real lead generation accounts in 2026. Ships with a niche pack for **real estate investors: home buyers and wholesalers** who buy direct from sellers.

## What's inside

| Skill | What it does | Writes to the account? |
|---|---|---|
| [google-ads-setup](skills/google-ads-setup/SKILL.md) | API access, refresh token, client config, connection test | No |
| [google-ads-audit](skills/google-ads-audit/SKILL.md) | Full account audit with fixes ranked by impact and the evidence behind each | No |
| [conversion-tracking-audit](skills/conversion-tracking-audit/SKILL.md) | Offline upload health, value drift, duplicate actions, bidding goals, daily heartbeat | No |
| [negative-keyword-audit](skills/negative-keyword-audit/SKILL.md) | Themed negative lists tested against 18 months of search terms through four safety gates | After approval |
| [search-term-review](skills/search-term-review/SKILL.md) | Weekly: leaks, junk to block, customers being blocked, converting terms to add | After approval |
| [keyword-research](skills/keyword-research/SKILL.md) | Keyword Planner volume and bids plus the account's own converting searches, grouped by intent | No |
| [generate-ads](skills/generate-ads/SKILL.md) | Responsive search ads and assets that pass Google's editorial rules, validated by script | No |
| [landing-page-check](skills/landing-page-check/SKILL.md) | Broken pages, redirects, speed, form visibility, GCLID capture | No |
| [ppc-weekly-routine](skills/ppc-weekly-routine/SKILL.md) | The weekly management loop for one client or a roster | No |
| [apply-google-ads-changes](skills/apply-google-ads-changes/SKILL.md) | The protocol for any live change: dry run, approval, backup, execute, verify, roll back | Yes, gated |

Plus:

- **[The playbook](docs/playbook/README.md)**: account structure, conversion tracking, keywords, negative keywords, ads, landing pages, Performance Max, weekly rhythm, safe changes.
- **[Niche pack: real estate investors](niches/real-estate-investors/README.md)**: a launch plan for new accounts, conversion setup (lead stages, values, CRM uploads, calls), seller landing pages, starter negative lists (about 370 phrase terms), a seller allow-list, keyword themes, ad copy angles and 2026 benchmarks.
- **[Case studies](docs/case-studies/)**: a negative keyword rebuild that let sellers back in, and how conversion value drift slowed Performance Max.
- **[Scripts](scripts/)**: read-only GAQL pulls, a deterministic audit, gate validation, gated apply with backup and restore.

## Quick start

```bash
git clone https://github.com/white-space-solutions/google-ads-agent-skills.git
cd google-ads-agent-skills
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                       # add API credentials (docs/setup.md)
cp clients/example.yaml clients/acme.yaml  # add the account ID, brand, competitors, campaign roles
.venv/bin/python scripts/check_connection.py --client clients/acme.yaml
.venv/bin/python scripts/pull.py --client clients/acme.yaml
.venv/bin/python scripts/audit.py --client clients/acme.yaml
```

Or just tell your agent: *"Read AGENTS.md in this repo and audit my Google Ads account."*

## Install the skills in your agent

| Agent | How |
|---|---|
| Claude Code | `/plugin marketplace add white-space-solutions/google-ads-agent-skills` then `/plugin install google-ads-agent-skills`. Or clone the repo and work inside it: the skills load from `skills/`. |
| Claude Cowork / claude.ai | Upload the `.skill` files from [`dist/`](dist/) in Settings > Capabilities > Skills, and connect the folder where you cloned the repo. |
| Codex, Cursor, other agents | Clone the repo and start the agent in it. `AGENTS.md` tells it where everything is. |
| Grok bot | Add each `skills/*/SKILL.md` as a bot skill (the description is the trigger, the body is the procedure). Run the scripts from a connected machine or sandbox. |

Full details: [docs/install.md](docs/install.md).

## Safety model

Reads are free. Writes are not. Every write script:

1. sends every operation with `validate_only` unless you pass `--execute`,
2. refuses to execute without `APPLY_ENABLED=1` set for that command,
3. refuses customer IDs not on the client's allowlist, and runs over the per-run op cap,
4. refuses structural negative changes unless every gate is 0 on a fresh validation,
5. takes a backup first and logs every change; `negatives_restore.py` rolls back.

Search terms are typed by strangers, so the gates are plain code, not model judgment. Read [docs/playbook/09-safe-changes.md](docs/playbook/09-safe-changes.md).

## FAQ

**What are negative keywords for real estate investors?**
Terms that stop "we buy houses" ads from showing to home shoppers, renters, agents, job seekers and other investors. The trap is blocking real sellers: words like realtor, zillow, mortgage, tax and rent show up in seller searches ("sell house without realtor", "sell house behind on property taxes"). The niche pack's lists block the browsing phrases and pass four gates against your own search history. See [04-negative-keywords.md](docs/playbook/04-negative-keywords.md).

**Can Claude manage Google Ads?**
Yes, through the Google Ads API. These skills let Claude (or another agent) pull account data, find problems, and stage changes. A person approves every write.

**Does this work for businesses that are not real estate investors?**
The core skills, scripts and playbook are niche-agnostic. The niche pack adds industry lists and benchmarks. Copy `niches/real-estate-investors/` as a starting point for another niche.

**Does it change my account without asking?**
No. Read-only by default; writes need `--execute` plus `APPLY_ENABLED=1` after a person approves the dry run.

**What does it cost?**
Free and MIT licensed. You need your own Google Ads API developer token (free from Google).

**Can someone run this for us?**
White Space Solutions runs a hosted command center for agencies that manage many accounts: scheduled audits, a daily conversion heartbeat, and an approval queue for every change across your client roster. [whitespacesolutions.ai](https://whitespacesolutions.ai)

## Contributing

New niche packs, checks and fixes are welcome. Keep client data out: no account IDs, names or spend figures from real accounts unless anonymized. Run `pytest` before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
