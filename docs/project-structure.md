# OpenCXO — Project Structure
> Open source repo structure. Name TBD.

```
{repo-root}/
│
├── README.md                        # what it is, 60-second demo, quickstart
├── LICENSE                          # MIT
├── CONTRIBUTING.md                  # how to contribute agents, skills, fixes
├── CHANGELOG.md                     # version history
├── CODE_OF_CONDUCT.md               # standard contributor covenant
│
├── docs/
│   ├── getting-started.md           # install → onboard → first /cto run
│   ├── agents/
│   │   ├── cto.md                   # how CTO agent works, all commands
│   │   ├── cmo.md                   # how CMO agent works
│   │   ├── ciso.md                  # how CISO agent works
│   │   ├── sre.md                   # how SRE agent works
│   │   └── building-your-own.md     # how to contribute a new CxO agent
│   ├── cxostack/
│   │   ├── architecture.md          # full system design
│   │   ├── model-routing.md         # best/avg/cheap explained
│   │   ├── skills.md                # skill registry, find-skills, bootstrap
│   │   ├── memory.md                # founder-profile, cxo-memory files
│   │   └── budget-pause-resume.md   # token budget system
│   ├── community-vs-ultimate.md     # what's free vs paid (when ultimate exists)
│   └── faq.md
│
├── .claude/
│   └── agents/                      # all CxO + dev team agent definitions
│       ├── cto.md                   ← CTO agent (ships with repo)
│       ├── cmo.md                   ← CMO agent
│       ├── ciso.md                  ← CISO agent (optional, on-demand)
│       ├── sre.md                   ← SRE agent (optional, on-demand)
│       ├── architect.md
│       ├── arch-reviewer.md
│       ├── planner.md
│       ├── team-leader.md
│       ├── backend-developer.md
│       ├── frontend-developer.md
│       ├── qa.md
│       ├── code-reviewer.md
│       └── devops.md
│
├── skills/                          # custom skills built for this project
│   └── cxo-context/
│       └── SKILL.md                 # teaches agents how to read memory files
│                                      (publishable to skills.sh later)
│
├── main.py                          # CLI entry point
├── orchestrator.py                  # agent lifecycle, budget, pause/resume
├── model_router.py                  # mode matrix (best/avg/cheap)
├── skill_registry.py                # TL skill lookup + assignment
│
├── tools/
│   ├── ask_user.py                  # terminal I/O bridge
│   ├── file_ops.py                  # read/write + ruff format
│   ├── git_ops.py                   # worktrees, branches, PRs
│   ├── docker_ops.py                # staging/prod deploy
│   ├── skill_ops.py                 # skills.sh wrapper + registry update
│   └── groq_relay.py               # non-CC model relay
│
├── skills.sh                        # skill bootstrap + thin npx wrapper
├── skill-registry.json              # seed registry (ships with repo)
│
├── templates/                       # what gets copied per new project
│   ├── spec.md
│   ├── RESEARCH.md
│   ├── DECISIONS.md
│   ├── GTM.md
│   └── CROSSTEAM.md
│
├── memory/                          # template files only — never real data
│   ├── founder-profile.template.md  # user fills this on onboard
│   ├── cto-memory.template.md
│   └── cmo-memory.template.md
│
├── pyproject.toml                   # uv managed
├── .python-version                  # 3.12
├── .env.example                     # ANTHROPIC_API_KEY, GROQ_API_KEY etc
├── .gitignore                       # .env, state/, projects/, ~/.cxostack/
│
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── agent_improvement.md     # specific template for agent prompt PRs
    │   └── new_cxo_agent.md         # template for proposing a new CxO
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        ├── ci.yml                   # ruff lint + pytest on every PR
        └── release.yml              # tag → changelog → GitHub release
```

---

## What Ships vs What Stays Private

```
SHIPS IN REPO (public)                    STAYS LOCAL (never committed)
──────────────────────────────────────    ──────────────────────────────
.claude/agents/*.md    agent prompts      ~/.cxostack/founder-profile.md
templates/*.md         blank templates    ~/.cxostack/cto-memory.md
memory/*.template.md   empty templates    ~/.cxostack/cmo-memory.md
main.py + tools        orchestrator       projects/         your projects
skill-registry.json    seed only          state/session.json
skills.sh                                 .env
docs/                                     state/budget.json
```

`.gitignore` enforces this hard — `projects/`, `state/`, `.env`,
and `~/.cxostack/` are never touched by git.

---

## Community Contribution Surface

The three things community can contribute cleanly:

```
1. New CxO agents          → .claude/agents/{cxo}.md + docs/agents/{cxo}.md
   (CPO, CFO, COO, CLO, etc)

2. Agent improvements      → PR against existing .claude/agents/*.md
   (better prompts, new commands, research patterns)

3. New skills              → skills/ directory + publish to skills.sh
   (custom skills that benefit all cxostack users)
```

Anything else (core Python, orchestrator, model router) is maintainer territory
to keep the surface area manageable early on.

---

## Ultimate Edition Boundary (future)

Community tier (this repo, always free):
  - All CxO agents
  - All dev team agents
  - Local memory files
  - Full CLI
  - skills.sh integration

Ultimate tier (future, hosted):
  - Cloud-synced memory across machines
  - Team sharing (multiple founders, same CxO suite)
  - Web UI alongside CLI
  - Pre-warmed research (CxOs research your industry before you ask)
  - Priority model access
  - SLA + support
```
