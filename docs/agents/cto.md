# CTO Agent

The CTO is the founder's primary interface to cxostack. It orchestrates the entire build pipeline.

## Commands

| Command | What it does |
|---------|-------------|
| `/cto onboard` | 5-question founder interview, writes `~/.cxostack/founder-profile.md` |
| `/cto <idea>` | Full pipeline: spec → architecture → planning → handoff |
| `/cto continue <phase>` | Spawns team-leader for the next phase |
| `/cto status` | Shows current project, phase, budget, paused tasks |

## What the CTO does on /cto <idea>

1. Generates a project slug and creates `projects/{slug}/`
2. Copies blank templates (spec, RESEARCH, DECISIONS, GTM, CROSSTEAM)
3. Asks 5 requirements questions one at a time
4. Spawns Architect → Arch-Reviewer loop (max 3 iterations)
5. Spawns Planner → writes phase-plan.md
6. Hands off to founder to run `/cto continue phase-1`

## Memory

Reads `~/.cxostack/founder-profile.md` and `~/.cxostack/cto-memory.md` at session start.
Updates `cto-memory.md` after each completed project pipeline.

## Model

Uses `claude-sonnet-4-6` by default. Switch to `claude-opus-4-6` with `/mode best`.
