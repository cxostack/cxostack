# cxostack

> An open-source AI executive suite for solopreneurs.

cxostack gives solo founders a full CxO team and engineering squad they can invoke from the terminal. One command starts a complete pipeline: requirements gathering → system design → phased development → deployment.

## What you get

- **CTO** — research, spec, architecture, and full build pipeline
- **CMO** — go-to-market strategy, content plans, campaigns
- **CISO** — security audits and red team testing (on-demand)
- **SRE** — infra design, load testing, incident triage (on-demand)
- **Engineering team** — architect, planner, team leader, developers, QA, code reviewer, DevOps

All agents are Claude Code subagents. They communicate, hand off work, and maintain memory between sessions.

## Quick start

### 1. Prerequisites

- [Claude Code CLI](https://claude.ai/code) with an active subscription or API key
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- `gh` CLI authenticated with GitHub
- Docker Desktop (for deployment)

### 2. Install

```bash
git clone https://github.com/your-org/cxostack.git
cd cxostack
uv sync
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Bootstrap skills

```bash
./skills.sh bootstrap
```

### 4. Onboard

```bash
uv run python main.py
cxostack> /cto onboard
```

This runs a short interview and writes `~/.cxostack/founder-profile.md` — the shared memory all agents read before acting.

### 5. Start your first project

```bash
cxostack> /cto "Build a SaaS tool for freelance invoicing"
```

The CTO agent will ask clarifying questions, write a spec, design the architecture (with review loop), create a phased plan, and hand off to the team leader to start building.

## Commands

```
/cto <idea>              Start full pipeline for a new project
/cto onboard             First-run founder interview
/cto continue <phase>    Resume a specific phase
/cto status              Current project state
/cmo <project>           Go-to-market strategy
/tl review pr: <url>     Isolated PR review
/status                  Phase, budget, paused tasks
/mode best|avg|cheap     Switch model tier
/help                    All commands
```

## Model tiers

| Tier | Best for | Cost |
|------|----------|------|
| `best` | Critical decisions, architecture | Higher |
| `avg` | Daily development (default) | Balanced |
| `cheap` | Bulk generation, exploration | Lower |

## Memory

Persistent memory lives in `~/.cxostack/` — outside the repo, never committed:

```
~/.cxostack/
├── founder-profile.md    # read by all agents
├── cto-memory.md         # tech preferences, past projects
└── cmo-memory.md         # brand voice, channel history
```

Templates for these files are in `memory/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the three ways to contribute: new CxO agents, agent improvements, and new skills.

## License

MIT — see [LICENSE](LICENSE).
