# CLAUDE.md — cxostack

This file is read by Claude Code at the start of every session.
It defines the project, conventions, agent responsibilities, and rules
that govern all work done in this repo.

---

## What is cxostack

cxostack is an open-source AI executive suite for solopreneurs.
It provides a set of CxO agents (CTO, CMO, CISO, SRE) and a full
engineering team (Architect, Planner, Team Leader, Developers, QA,
DevOps) that a solo founder can invoke from their terminal to research,
plan, build, secure, and ship products.

The CLI entry point is `main.py`. Agents live in `.claude/agents/`.
Persistent founder memory lives in `~/.cxostack/` and never enters git.

---

## Repo Structure (Canonical)

```
cxostack/
│
├── CLAUDE.md                        ← you are here
├── README.md                        ← project intro, quickstart
├── LICENSE                          ← MIT
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
│
├── docs/
│   ├── getting-started.md           ← install → onboard → first /cto run
│   ├── swarm-architecture.md        ← full system design
│   ├── project-convention.md        ← file conventions per project
│   ├── project-structure.md         ← OSS repo structure explanation
│   ├── agents/
│   │   ├── cto.md
│   │   ├── cmo.md
│   │   ├── ciso.md
│   │   ├── sre.md
│   │   └── building-your-own.md
│   └── swarm/
│       ├── model-routing.md
│       ├── skills.md
│       ├── memory.md
│       └── budget-pause-resume.md
│
├── .claude/
│   └── agents/                      ← all agent definitions (CC reads these)
│       ├── cto.md                   ← CxO agents
│       ├── cmo.md
│       ├── ciso.md                  ← stub, to be built
│       ├── sre.md                   ← stub, to be built
│       ├── architect.md             ← engineering team
│       ├── arch-reviewer.md
│       ├── planner.md
│       ├── team-leader.md
│       ├── backend-developer.md
│       ├── frontend-developer.md
│       ├── qa.md
│       ├── code-reviewer.md
│       └── devops.md
│
├── main.py                          ← CLI entry: /cto /cmo /tl /status etc
├── orchestrator.py                  ← agent lifecycle, budget, pause/resume
├── model_router.py                  ← best/avg/cheap mode matrix
├── skill_registry.py                ← TL skill lookup + assignment
│
├── tools/
│   ├── ask_user.py                  ← terminal I/O bridge
│   ├── file_ops.py                  ← read/write + ruff format
│   ├── git_ops.py                   ← worktrees, branches, PRs via gh
│   ├── docker_ops.py                ← staging/prod deploy
│   ├── skill_ops.py                 ← skills.sh wrapper + registry update
│   └── groq_relay.py               ← non-CC model relay (Groq)
│
├── templates/                       ← blank templates copied per new project
│   ├── spec.md
│   ├── RESEARCH.md
│   ├── DECISIONS.md
│   ├── GTM.md
│   ├── MARKETING-DECISIONS.md
│   └── CROSSTEAM.md
│
├── memory/                          ← templates only, never real data
│   ├── founder-profile.template.md
│   ├── cto-memory.template.md
│   └── cmo-memory.template.md
│
├── skills.sh                        ← skill bootstrap + npx skills wrapper
├── skill-registry.json              ← seed registry
├── pyproject.toml                   ← uv managed, Python 3.12
├── .python-version                  ← 3.12
├── .env.example                     ← key names only, no values
├── .gitignore
│
├── state/                           ← runtime state, never committed
│   ├── session.json
│   ├── budget.json
│   └── paused_tasks.json
│
├── projects/                        ← generated per /cto run, never committed
│
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── agent_improvement.md
    │   └── new_cxo_agent.md
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        ├── ci.yml                   ← ruff + pytest on every PR
        └── release.yml              ← tag → changelog → GitHub release
```

---

## What Is Committed vs What Stays Local

```
COMMITTED (public)                    LOCAL ONLY (never committed)
────────────────────────────────────  ────────────────────────────
.claude/agents/*.md                   ~/.cxostack/founder-profile.md
templates/*.md                        ~/.cxostack/cto-memory.md
memory/*.template.md                  ~/.cxostack/cmo-memory.md
main.py, orchestrator.py, tools/      projects/
skill-registry.json (seed only)       state/session.json
skills.sh                             state/budget.json
docs/                                 state/paused_tasks.json
.env.example                          .env
```

`.gitignore` enforces this. Never commit `projects/`, `state/`, `.env`,
or anything under `~/.cxostack/`.

---

## Agent Responsibilities

### CxO Agents (invoked by founder directly)

| Agent | Command | Purpose |
|---|---|---|
| CTO | `/cto <idea> [--research deep\|quick]` | Research → spec → architecture → build pipeline |
| CTO | `/cto onboard` | First-run founder interview, builds memory |
| CTO | `/cto continue phase-N` | Spawns TL for next phase |
| CTO | `/cto status` | Current project state |
| CMO | `/cmo <project> [--research deep\|quick]` | GTM strategy, content plan |
| CMO | `/cmo onboard` | First-run marketing interview |
| CMO | `/cmo campaign <goal>` | Plan a specific campaign |
| CMO | `/cmo review` | Audit current marketing performance |
| CISO | `/ciso audit <project>` | Post-deploy security audit |
| CISO | `/ciso attack <project>` | Red team / active probing |
| SRE | `/sre plan <project>` | Cloud infra design + cost estimate |
| SRE | `/sre stress <project>` | Load testing against staging |
| SRE | `/sre incident <description>` | Triage a prod incident |

### Engineering Team (invoked by CTO/TL, not founder directly)

| Agent | Invoked by | Purpose |
|---|---|---|
| Architect | CTO | System design → architecture.md |
| Arch-Reviewer | CTO | Reviews architecture.md (loop ×3) |
| Planner | CTO | Phases + tasks → phase-plan.md |
| Team Leader | CTO (per phase) | Owns phase execution end to end |
| Backend Developer | TL (max 5) | Feature implementation + unit tests |
| Frontend Developer | TL (max 5) | UI implementation + component tests |
| QA | TL | Unit + integration + E2E (Playwright) |
| Code Reviewer | TL | PR diff review |
| DevOps | TL | Git setup, Docker, staging + prod deploy |

---

## Memory System

All persistent memory lives in `~/.cxostack/` — outside the repo, never committed.

```
~/.cxostack/
├── founder-profile.md    ← shared by ALL CxOs, read first every session
├── cto-memory.md         ← tech preferences, stack defaults, past projects
└── cmo-memory.md         ← channel history, brand voice, audience knowledge
```

**Rules:**
- Every agent reads `~/.cxostack/founder-profile.md` before acting
- Never ask the founder for information already in memory
- Update memory at the end of every session
- CTO auto-updates `cto-memory.md` when a project's `.completed` marker is found
- Templates for these files are in `memory/*.template.md`

---

## Project File Convention

Every project generated by `/cto` follows this structure:

```
projects/{slug}/
├── spec.md                  ← CTO: what we're building and why
├── RESEARCH.md              ← CTO: market + technical research
├── architecture.md          ← Architect: full system design
├── DECISIONS.md             ← CTO: every non-trivial decision recorded
├── phase-plan.md            ← Planner: phased task breakdown
├── GTM.md                   ← CMO: go-to-market strategy
├── CONTENT-PLAN.md          ← CMO: content calendar + templates
├── MARKETING-DECISIONS.md   ← CMO: marketing decisions
├── CROSSTEAM.md             ← Any CxO: flags for other CxOs
├── SECURITY.md              ← CISO: audit findings (when run)
├── STRESS-REPORT.md         ← SRE: load test results (when run)
├── phases/
│   └── phase-{n}.md         ← QA: bug reports per phase
├── usecases/
│   └── {usecase}.md         ← Dev: per-feature context file
└── campaigns/
    └── {goal}-{date}.md     ← CMO: campaign plans
```

---

## Skills

Skills are installed globally via `npx skills add` and live in `~/.claude/skills/`.

Currently installed:
- `find-skills` — TL uses this to discover skills on skills.sh at runtime
- `subagent-driven-development` — swarm operation patterns
- `dispatching-parallel-agents` — parallel dev patterns
- `using-git-worktrees` — worktree workflow
- `finishing-a-development-branch` — branch completion flow
- `requesting-code-review` — code review patterns
- `verification-before-completion` — QA verification patterns
- `frontend-design` — UI/component patterns
- `ui-ux-pro-max` — advanced UI/UX patterns
- `vercel-react-best-practices` — React patterns
- `nodejs-backend-patterns` — backend patterns
- `supabase-postgres-best-practices` — database patterns
- `better-auth-best-practices` — auth patterns
- `webapp-testing` — testing patterns
- `e2e-testing-patterns` — E2E testing
- `code-review-excellence` — review standards

To add new skills: `./skills.sh install <owner/repo/skill>`
To find skills: `./skills.sh find <query>` or TL uses find-skills autonomously

Skill assignments per agent role are tracked in `skill-registry.json`.
TL auto-discovers and loads missing skills before assigning tasks.

---

## Model Routing

Three modes selectable at runtime: `--mode best | avg | cheap`

Set default in `.env`: `DEFAULT_MODE=avg`

| Agent | best | avg | cheap |
|---|---|---|---|
| CTO, CMO, Architect | claude-opus-4 | claude-sonnet-4-6 | claude-sonnet-4-6 |
| TL, Planner, Reviewers | claude-sonnet-4-6 | claude-sonnet-4-6 | claude-haiku-4-5 |
| Developers, QA, DevOps | claude-sonnet-4-6 | claude-haiku-4-5 | groq/* |

Groq models: pure text generation only. Python orchestrator handles
all file writes, git ops, and command execution on their behalf.
Output is always ruff-formatted before writing to disk.

Budget is tracked in `state/budget.json`. When a model's budget is
exhausted, the task is paused to `state/paused_tasks.json` with full
context checkpoint. Resume with `/resume` command.

---

## Git Workflow

```
main
└── phase-{n}/                    ← phase branch, TL-managed
     ├── feature/{usecase}        ← developer worktree
     └── bug/phase-{n}/{name}     ← bug fix branch
```

- Each developer gets a git worktree in `.worktrees/{usecase}`
- Developer: code → commit → push → raise PR via `gh` CLI
- PR requires: QA approval + Code-Reviewer approval
- TL merges all PRs at end of task batch
- DevOps tags each phase release: `git tag phase-{n}-release`

---

## CLI Commands

```bash
python main.py               # start session

/cto <idea>                  # start full pipeline
/cto <idea> --research deep  # with deep market + technical research
/cto onboard                 # first-run founder interview
/cto continue phase-N        # spawn TL for next phase
/cto status                  # current project, phase, tasks

/cmo <project>               # go-to-market strategy
/cmo onboard                 # first-run marketing interview
/cmo campaign <goal>         # plan a specific campaign
/cmo review                  # audit current marketing

/ciso audit <project>        # post-deploy security audit (on-demand)
/ciso attack <project>       # red team (on-demand)

/sre plan <project>          # infra design + cost estimate (on-demand)
/sre stress <project>        # load testing (on-demand)
/sre incident <description>  # triage prod incident (on-demand)

/tl review pr: <url>         # isolated PR review session

/status                      # phase, tasks, budget, paused
/resume                      # retry all paused tasks
/budget                      # per-model token usage
/skills list                 # installed skills
/skills find <query>         # search skills.sh registry
/mode best|avg|cheap         # switch model tier
```

---

## Development Rules

**For agents working in this repo:**

1. Never modify `~/.cxostack/` files directly — those belong to the founder
2. Never commit `projects/`, `state/`, or `.env`
3. All Python files must pass `ruff format` and `ruff check` before commit
4. Agent `.md` files in `.claude/agents/` are the source of truth —
   corresponding docs in `docs/agents/` are human-readable explanations,
   not duplicates
5. `skill-registry.json` in the repo is a seed only — runtime updates
   happen to the local copy, never committed
6. When adding a new CxO agent: add `.claude/agents/{cxo}.md`,
   add docs in `docs/agents/{cxo}.md`, add command to `main.py`,
   add memory template to `memory/{cxo}-memory.template.md`
7. `templates/` files are blank scaffolds — never put real project
   data in them
8. CISO and SRE are on-demand only — never wired into the dev pipeline
   as automatic gates

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=    # required — Claude API access
GROQ_API_KEY=         # optional — cheap mode developer agents
GITHUB_TOKEN=         # required — PR creation, repo management via gh CLI
DEFAULT_MODE=avg      # best | avg | cheap
```

Copy `.env.example` to `.env` and fill in values.
Never commit `.env`.

---

## Contributing

Three ways to contribute:

1. **New CxO agent** — `.claude/agents/{cxo}.md` + `docs/agents/{cxo}.md`
   + memory template. Use `new_cxo_agent.md` issue template first.

2. **Agent improvement** — PR against `.claude/agents/*.md` with
   specific prompt improvements. Use `agent_improvement.md` issue template.

3. **New skill** — add to `skills/` directory and optionally publish
   to skills.sh. Skills should be generic enough to benefit all users.

Core Python (`main.py`, `orchestrator.py`, `tools/`) is maintainer
territory while the project is in early development.

See `CONTRIBUTING.md` for full guidelines.