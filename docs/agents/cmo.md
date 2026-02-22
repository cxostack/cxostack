# CMO Agent

The CMO handles go-to-market strategy, content planning, and campaign management.

## Commands

| Command | What it does |
|---------|-------------|
| `/cmo <project>` | Full GTM strategy for a project |
| `/cmo onboard` | Marketing-focused founder interview |
| `/cmo campaign <goal>` | Plan a specific campaign |
| `/cmo review` | Audit current marketing performance |

## What the CMO produces

- `projects/{project}/GTM.md` — go-to-market strategy
- `projects/{project}/CONTENT-PLAN.md` — content calendar and templates
- `projects/{project}/MARKETING-DECISIONS.md` — marketing decisions log
- `projects/{project}/campaigns/{goal}-{date}.md` — campaign plans

## Memory

Reads `~/.cxostack/founder-profile.md` and `~/.cxostack/cmo-memory.md` at session start.
Updates `cmo-memory.md` with channel history and audience learnings after each engagement.
