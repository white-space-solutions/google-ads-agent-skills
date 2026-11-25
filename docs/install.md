# Installing the skills

The skills are plain `SKILL.md` files (the open Agent Skills format: YAML frontmatter with `name` and `description`, then the procedure). Every skill runs the scripts in this repo, so the agent needs the repo on a machine where it can run Python.

## Claude Code

```
/plugin marketplace add white-space-solutions/google-ads-agent-skills
/plugin install google-ads-agent-skills
```

Then clone the repo (for the scripts) and start Claude Code in it. Or skip the plugin: clone, `cd` in, start Claude Code. `CLAUDE.md` points it to `AGENTS.md`.

## Claude Cowork and claude.ai

1. Download the `.skill` files you want from [`dist/`](../dist/).
2. Settings > Capabilities > Skills > upload each one.
3. In Cowork, connect the folder where you cloned this repo so the agent can run the scripts there.
4. Ask: "Set up Google Ads access for <client>" (google-ads-setup), then "Audit the account".

## Codex, Cursor, Windsurf, Gemini CLI and other coding agents

Clone the repo and start the agent in it. `AGENTS.md` is the entry point. Skills are in `skills/`.

## Grok bots

Grok bot skills want: when to use, inputs, steps, validation, output and what needs approval. Each `SKILL.md` already has those sections.

1. Create one bot skill per `skills/*/SKILL.md`. Use the frontmatter `description` as the skill's "when to use" and the body as the procedure.
2. Put the business facts (accounts, brand, competitors, cities served) in the bot's shared knowledge, mirroring `clients/<slug>.yaml`.
3. Give the bot a machine or sandbox with this repo and `.env` to run the scripts.
4. Add the approval line to the bot's standing instructions: anything that changes the ad account needs a person's approval. Reversible reads run alone.

Never put `.env` contents into shared knowledge or a public template.

## Any agent that can read a URL

Point it at `llms.txt` in the repo root. It lists every file with a one-line description.

## Building the .skill files

`python scripts/package_skills.py` zips each skill folder into `dist/<name>.skill`.
