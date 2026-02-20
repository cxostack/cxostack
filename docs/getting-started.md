# CXOStack Build Guide
> macOS · uv · Claude Code CLI · Sprint-by-sprint execution

---

## Prerequisites

### 1. Install Claude Code CLI

Anthropic now offers native installers as the recommended method — no Node.js required.

```bash
# Native installer (recommended)
curl -fsSL https://claude.ai/install.sh | sh

# Verify
claude --version
```

Then authenticate:
```bash
claude auth
# Opens browser → log in with your Anthropic account (Pro/Max/API)
```

If you want to use API key instead of subscription (gives you 1M context window):
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to ~/.zshrc to persist
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # or restart terminal
uv --version
```

### 3. Other tools needed

```bash
# Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Git (likely already installed)
git --version

# Docker Desktop
brew install --cask docker
# Then open Docker Desktop app and let it start

# GitHub CLI (for PR management)
brew install gh
gh auth login

# ruff (Python formatter/linter)
brew install ruff
```

---

## Step 1 — Scaffold the CXOStack Repo

Run these commands exactly. This creates every directory and placeholder file the architecture requires.

```bash
# 1. Create and enter the project
mkdir -p ~/cxostack && cd ~/cxostack
git init

# 2. Python project with uv
uv init --no-readme
uv python pin 3.12

# 3. Core source directories
mkdir -p agents tools state projects

# 4. Claude Code config directories (project-level)
mkdir -p .claude/agents .claude/skills .claude/commands

# 5. Placeholder files
touch main.py orchestrator.py model_router.py skill_registry.py
touch tools/ask_user.py tools/file_ops.py tools/git_ops.py
touch tools/docker_ops.py tools/skill_ops.py tools/groq_relay.py
touch state/session.json state/budget.json state/paused_tasks.json
touch skill-registry.json

# 6. Initialize state files
echo '{"history": [], "phase": null, "mode": "avg"}' > state/session.json
echo '{"claude-opus-4": {"limit": 500000, "used": 0}, "claude-sonnet-4-6": {"limit": 2000000, "used": 0}, "claude-haiku-4-5": {"limit": 5000000, "used": 0}, "groq": {"limit": 10000000, "used": 0}}' > state/budget.json
echo '[]' > state/paused_tasks.json
echo '{"known_skills": [], "agent_skills": {}, "missing_log": []}' > skill-registry.json

# 7. Python dependencies
uv add anthropic groq gitpython rich prompt_toolkit python-dotenv

# 8. .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
GROQ_API_KEY=gsk_your-key-here
GITHUB_TOKEN=ghp_your-token-here
DEFAULT_MODE=avg
EOF

# 9. .gitignore
cat > .gitignore << 'EOF'
.env
__pycache__/
.venv/
state/session.json
*.pyc
EOF

echo "✓ Scaffold complete"
```

---

## Step 2 — Install Skills at User Level

```bash
# Create user-level skills directory (available across ALL projects)
mkdir -p ~/.claude/skills

cd ~/cxostack && ./skills.sh bootstrap


# Verify
ls ~/.claude/skills/
# → frontend-design   docx

```

For your cxostack's project-level skills (symlink so they stay in sync):
```bash
# From inside ~/cxostack
ln -s ~/.claude/skills/frontend-design .claude/skills/frontend-design
```

---

## Step 3 — Create Agent Definition Files

Subagents are defined in Markdown files with YAML frontmatter. You can create them manually or use the `/agents` command.

Create each agent in `.claude/agents/`. These are the actual subagents CC will spawn.

### CTO Agent
```bash
cat > .claude/agents/cto.md << 'EOF'
---
name: cto
description: Chief Technical Officer. Invoke with /cto <idea>. Orchestrates the full pipeline from requirements gathering through architecture, planning, and phase execution. Use for starting any new project.
model: claude-sonnet-4-6
tools: Read, Write, Edit, Bash, Task
color: red
---

You are the CTO of this engineering team. You orchestrate the entire development pipeline.

When given a project idea:
1. Gather requirements by asking the user targeted questions (use ask_user pattern — print question, wait for input)
2. Write spec.md to projects/{slug}/spec.md
3. Spawn the architect subagent to design the system
4. Govern the architect + arch-reviewer loop (max 3 iterations)
5. Finalise architecture.md and present summary to user
6. Spawn planner subagent
7. Govern planner + team-leader review loop (max 3 iterations)
8. Spawn team-leader for phase 1

Always communicate blockers or decisions back to the user before proceeding.
Read state/session.json to resume interrupted sessions.
Track model usage in state/budget.json after every agent invocation.
EOF
```

### Architect Agent
```bash
cat > .claude/agents/architect.md << 'EOF'
---
name: architect
description: System architect. Designs complete system architecture including backend, frontend, database, auth, security, testing, and deployment. Invoked by CTO only.
model: claude-sonnet-4-6
tools: Read, Write, Edit
color: blue
---

You are a senior system architect. Given spec.md, design a complete production-grade system.

Cover: backend stack, frontend stack, database design, auth strategy, security, testing approach, deployment topology, third-party services.

Ask the CTO (not the user directly) if you need decisions like: payment gateway, primary database choice, cloud provider.

Write your output to projects/{slug}/architecture.md with clear sections.
Be opinionated — recommend the best tool for each job, justify your choices.
EOF
```

### Arch-Reviewer Agent
```bash
cat > .claude/agents/arch-reviewer.md << 'EOF'
---
name: arch-reviewer
description: Architecture reviewer. Reviews architecture.md for gaps, risks, and improvements. Invoked by CTO only.
model: claude-haiku-4-5
tools: Read, Write
color: yellow
---

You are a senior architect reviewer. Read architecture.md and review it critically.

Check for: missing components, security gaps, scalability issues, over-engineering, wrong tool choices, unclear boundaries, missing error handling strategy, no observability plan.

Write your review as inline comments appended to architecture.md under a ## Review section.
Be specific — "auth is missing refresh token rotation" not "auth needs work".
EOF
```

### Planner Agent
```bash
cat > .claude/agents/planner.md << 'EOF'
---
name: planner
description: Project planner. Creates phase-plan.md with phased task breakdown from architecture.md. Invoked by CTO only.
model: claude-haiku-4-5
tools: Read, Write
color: green
---

You are a senior engineering project planner.

Read spec.md and architecture.md. Break the work into phases where:
- Each phase delivers a shippable increment
- Tasks within a phase can run in parallel where possible
- Each task maps to one usecase owned by one developer
- Tasks have clear acceptance criteria

Write to projects/{slug}/phase-plan.md with structure:
Phase 1: [name]
  Task-01: [usecase] - backend/frontend - estimated complexity: low/med/high
  Task-02: ...
Phase 2: ...
EOF
```

### Team Leader Agent
```bash
cat > .claude/agents/team-leader.md << 'EOF'
---
name: team-leader
description: Team leader for a single phase. Assigns tasks to developers, tracks progress, manages the dev-qa-review cycle, deploys phase. Invoked by CTO per phase.
model: claude-sonnet-4-6
tools: Read, Write, Edit, Bash, Task
color: purple
---

You are the team leader for this phase. You own phase execution end to end.

Responsibilities:
1. Read phase-plan.md — identify all tasks for your assigned phase
2. For each task: check skill-registry.json, find/load missing skills via skill_ops
3. Spawn developer agents (max 10: 5 backend, 5 frontend) with task JSON + usecase.md path
4. Track all developer reports in state/tl_checkpoint_phase_{n}.json
5. After all tasks done: spawn phase-level QA sweep
6. Read phases/phase-{n}.md bug report, spawn bug-fix developers
7. Spawn devops agent for staging + prod deploy
8. Report phase completion to terminal

Never spawn more than 10 developers at once.
Always checkpoint state before spawning new agents.
Read skill-registry.json before assigning any task.
EOF
```

### Backend Developer Agent
```bash
cat > .claude/agents/backend-developer.md << 'EOF'
---
name: backend-developer
description: Backend developer. Implements server-side features, APIs, database models. Invoked by team-leader with a task JSON and usecase.md path.
model: claude-haiku-4-5
tools: Read, Write, Edit, Bash
skills:
  - backend-api
color: cyan
---

You are a senior backend developer. You receive a task via usecase.md.

Workflow:
1. Read usecase.md — understand requirements, acceptance criteria, skills loaded
2. Create git worktree: git worktree add .worktrees/{usecase} -b feature/{usecase}
3. Implement the feature in the worktree
4. Write unit tests alongside the code
5. Run tests: if failing, fix before proceeding
6. Commit all changes with clear messages
7. Push branch and create PR via gh CLI
8. Update usecase.md with branch, PR URL, commit list
9. Report completion JSON to team-leader

Never skip tests. Never push broken code.
Update usecase.md at every stage — it's the source of truth for QA and reviewer.
EOF
```

### Frontend Developer Agent
```bash
cat > .claude/agents/frontend-developer.md << 'EOF'
---
name: frontend-developer
description: Frontend developer. Implements UI features, React components, styling. Invoked by team-leader with a task JSON and usecase.md path.
model: claude-haiku-4-5
tools: Read, Write, Edit, Bash
skills:
  - frontend-design
color: orange
---

You are a senior frontend developer specialising in React.

Workflow:
1. Read usecase.md — understand requirements, acceptance criteria, loaded skills
2. Read frontend-design SKILL.md to apply correct patterns
3. Create git worktree: git worktree add .worktrees/{usecase} -b feature/{usecase}
4. Implement components, pages, styles
5. Write component unit tests (vitest + testing-library)
6. Run tests and linter before committing
7. Commit, push, create PR via gh CLI
8. Update usecase.md with branch, PR URL
9. Report completion JSON to team-leader

Apply frontend-design guidelines strictly.
Every component must have a test file alongside it.
EOF
```

### QA Agent
```bash
cat > .claude/agents/qa.md << 'EOF'
---
name: qa
description: QA engineer. Runs unit, integration, and E2E tests against a feature branch or full phase. Invoked by developer or team-leader. Reads usecase.md for context.
model: claude-haiku-4-5
tools: Read, Write, Edit, Bash
color: pink
---

You are a senior QA engineer. You test features thoroughly.

For feature-level QA (invoked by developer):
1. Read usecase.md — understand requirements and acceptance criteria
2. Run existing unit tests, report coverage
3. Start docker-compose test environment
4. Run integration tests against API endpoints
5. Run Playwright E2E tests for user flows
6. Write results to usecase.md QA section
7. If all pass: approve. If any fail: list specific failures with reproduction steps

For phase-level QA (invoked by team-leader):
1. Run full test suite against staging environment
2. Write bug report to projects/{slug}/phases/phase-{n}.md
3. Each bug: description, reproduction steps, severity, affected file

Never approve if any acceptance criteria are unmet.
EOF
```

### Code Reviewer Agent
```bash
cat > .claude/agents/code-reviewer.md << 'EOF'
---
name: code-reviewer
description: Code reviewer. Reviews PR diffs for quality, security, and correctness. Invoked by developer after QA approval. Read-only access.
model: claude-haiku-4-5
tools: Read, Bash, Grep, Glob
color: gray
---

You are a senior code reviewer. You review PRs before they merge.

1. Read usecase.md — understand what was built and why
2. Fetch PR diff: gh pr diff {PR_NUMBER}
3. Review for: correctness, security vulnerabilities, performance issues, code style, missing error handling, test quality
4. Write review to usecase.md Review section
5. If approved: state "APPROVED — no blocking issues"
6. If changes needed: list each issue with file:line and specific fix required

Be precise. "Missing input validation on POST /auth/login line 42" not "needs validation".
Only request changes for real issues, not style preferences.
EOF
```

### DevOps Agent
```bash
cat > .claude/agents/devops.md << 'EOF'
---
name: devops
description: DevOps engineer. Creates repos, manages git setup, builds Docker environments, deploys to staging and production. Invoked by team-leader.
model: claude-haiku-4-5
tools: Read, Write, Edit, Bash
color: white
---

You are a senior DevOps engineer.

For initial setup (invoked once by CTO):
1. Create GitHub repo via gh CLI
2. Set remote origin
3. Commit spec.md, architecture.md, phase-plan.md
4. Push main branch

For phase deploy (invoked by team-leader):
1. Build Docker staging image
2. Run docker-compose up for staging
3. Run smoke tests against staging
4. If passing: deploy to prod (docker-compose -f docker-compose.prod.yml up -d)
5. Report deploy status and prod URL to team-leader

Always tag releases: git tag phase-{n}-release
EOF
```

---

## Step 4 — Install skills.sh

This is the script TL calls to discover and install skills.

```bash
cat > skills.sh << 'EOF'
#!/bin/bash
# skills.sh — skill discovery and installation for cxostack agents
# Usage: ./skills.sh search <query> | install <name> | list

SKILLS_PUBLIC="/mnt/skills/public"
SKILLS_USER="$HOME/.claude/skills"
SKILLS_PROJECT=".claude/skills"

case "$1" in
  search)
    QUERY="$2"
    echo "=== User Skills ==="
    find "$SKILLS_USER" -name "SKILL.md" | while read f; do
      DIR=$(dirname "$f")
      NAME=$(basename "$DIR")
      DESC=$(grep -m1 "^description:" "$f" 2>/dev/null | sed 's/description: //')
      echo "  $NAME — $DESC"
    done | grep -i "$QUERY" 2>/dev/null || echo "  (none matching)"

    echo "=== Public Skills ==="
    find "$SKILLS_PUBLIC" -name "SKILL.md" | while read f; do
      DIR=$(dirname "$f")
      NAME=$(basename "$DIR")
      DESC=$(grep -m1 "^description:" "$f" 2>/dev/null | sed 's/description: //')
      echo "  $NAME — $DESC"
    done | grep -i "$QUERY" 2>/dev/null || echo "  (none matching)"
    ;;

  install)
    NAME="$2"
    SCOPE="${3:-user}"  # user | project

    # Find the skill
    SRC=""
    [ -d "$SKILLS_USER/$NAME" ] && SRC="$SKILLS_USER/$NAME"
    [ -d "$SKILLS_PUBLIC/$NAME" ] && SRC="$SKILLS_PUBLIC/$NAME"

    if [ -z "$SRC" ]; then
      echo "ERROR: skill '$NAME' not found"
      exit 1
    fi

    if [ "$SCOPE" = "project" ]; then
      cp -r "$SRC" "$SKILLS_PROJECT/$NAME"
      echo "✓ Installed '$NAME' to project skills"
    else
      cp -r "$SRC" "$SKILLS_USER/$NAME"
      echo "✓ Installed '$NAME' to user skills"
    fi
    ;;

  list)
    echo "=== Installed User Skills ==="
    ls "$SKILLS_USER" 2>/dev/null || echo "  (none)"
    echo "=== Installed Project Skills ==="
    ls "$SKILLS_PROJECT" 2>/dev/null || echo "  (none)"
    ;;

  *)
    echo "Usage: ./skills.sh search <query> | install <name> [user|project] | list"
    ;;
esac
EOF

chmod +x skills.sh
echo "✓ skills.sh ready"
```

---

## Step 5 — Seed skill-registry.json

```bash
cat > skill-registry.json << 'EOF'
{
  "known_skills": [
    "frontend-design"
  ],
  "agent_skills": {
    "frontend-developer": ["frontend-design"],
    "backend-developer": [],
    "qa": [],
    "devops": [],
    "code-reviewer": []
  },
  "missing_log": []
}
EOF
```

---

## Step 6 — Sprint 1: Wire main.py

The minimal main.py to get `/cto "idea"` running end to end:

```bash
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
CXOStack CLI — entry point
Usage: python main.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv()
console = Console()

BANNER = """
[bold red] ██████╗[/][bold yellow]██╗  ██╗[/][bold green] ██████╗ [/][bold blue]███████╗[/][bold magenta]████████╗[/][bold cyan] █████╗ [/][bold white] ██████╗██╗  ██╗[/]
[bold red]██╔════╝[/][bold yellow]╚██╗██╔╝[/][bold green]██╔═══██╗[/][bold blue]██╔════╝[/][bold magenta]╚══██╔══╝[/][bold cyan]██╔══██╗[/][bold white]██╔════╝██║ ██╔╝[/]
[bold red]██║      [/][bold yellow] ╚███╔╝ [/][bold green]██║   ██║[/][bold blue]███████╗[/][bold magenta]   ██║   [/][bold cyan]███████║[/][bold white]██║     █████╔╝ [/]
[bold red]██║      [/][bold yellow] ██╔██╗ [/][bold green]██║   ██║[/][bold blue]╚════██║[/][bold magenta]   ██║   [/][bold cyan]██╔══██║[/][bold white]██║     ██╔═██╗ [/]
[bold red]╚██████╗[/][bold yellow]██╔╝ ██╗[/][bold green]╚██████╔╝[/][bold blue]███████║[/][bold magenta]   ██║   [/][bold cyan]██║  ██║[/][bold white]╚██████╗██║  ██╗[/]
[bold red] ╚═════╝[/][bold yellow]╚═╝  ╚═╝[/][bold green] ╚═════╝ [/][bold blue]╚══════╝[/][bold magenta]   ╚═╝   [/][bold cyan]╚═╝  ╚═╝[/][bold white] ╚═════╝╚═╝  ╚═╝[/]
"""

def run_claude_agent(agent_name: str, prompt: str, mode: str = "avg") -> str:
    """Spawn a CC subagent and return its output."""
    model_map = {
        "best": "claude-sonnet-4-6",
        "avg":  "claude-haiku-4-5",
        "cheap": "claude-haiku-4-5",
    }
    model = model_map.get(mode, "claude-haiku-4-5")

    result = subprocess.run(
        ["claude", "--agent", agent_name, "--model", model, "--print", "-p", prompt],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    if result.returncode != 0:
        console.print(f"[red]Agent {agent_name} error:[/] {result.stderr}")
        return ""
    return result.stdout.strip()


def cmd_cto(idea: str, mode: str = "avg"):
    console.print(f"\n[bold red][CTO][/] Starting project: [italic]{idea}[/]\n")
    output = run_claude_agent("cto", f"New project idea: {idea}", mode=mode)
    console.print(output)


def cmd_tl_review(pr_url: str, mode: str = "avg"):
    console.print(f"\n[bold purple][TL][/] Reviewing PR: {pr_url}\n")
    prompt = f"Review this PR: {pr_url}. Load the usecase.md from the PR description for context."
    output = run_claude_agent("team-leader", prompt, mode=mode)
    console.print(output)


def cmd_status():
    budget = json.loads(Path("state/budget.json").read_text())
    session = json.loads(Path("state/session.json").read_text())
    paused = json.loads(Path("state/paused_tasks.json").read_text())

    console.print("\n[bold]── Budget ──[/]")
    for model, data in budget.items():
        pct = (data["used"] / data["limit"] * 100) if data["limit"] else 0
        console.print(f"  {model}: {data['used']:,} / {data['limit']:,} ({pct:.1f}%)")

    console.print(f"\n[bold]── Session ──[/]")
    console.print(f"  Phase: {session.get('phase', 'none')}")
    console.print(f"  Mode:  {session.get('mode', 'avg')}")

    console.print(f"\n[bold]── Paused Tasks ──[/]")
    if paused:
        for t in paused:
            console.print(f"  {t['task_id']} — {t['reason']}")
    else:
        console.print("  (none)")


def cmd_skills(args: list):
    sub = args[0] if args else "list"
    query = args[1] if len(args) > 1 else ""
    subprocess.run(["./skills.sh", sub, query])


def main():
    console.print(BANNER)
    console.print("[dim]Type /cto <idea> to start · /help for commands[/]\n")

    mode = os.getenv("DEFAULT_MODE", "avg")

    while True:
        try:
            raw = Prompt.ask("[bold green]cxostack>[/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye.[/]")
            break

        if not raw:
            continue

        parts = raw.split(" ", 1)
        cmd = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if cmd == "/cto":
            if not rest:
                console.print("[red]Usage:[/] /cto <idea> [--mode best|avg|cheap]")
                continue
            # parse optional --mode flag
            if "--mode" in rest:
                idea, _, m = rest.partition("--mode")
                mode = m.strip()
                idea = idea.strip()
            else:
                idea = rest
            cmd_cto(idea, mode)

        elif cmd == "/tl":
            if "review pr:" in rest:
                url = rest.split("pr:")[1].strip()
                cmd_tl_review(url, mode)
            else:
                console.print("[red]Usage:[/] /tl review pr: <url>")

        elif cmd == "/status":
            cmd_status()

        elif cmd == "/resume":
            console.print("[yellow]Resuming paused tasks...[/]")
            output = run_claude_agent("cto", "Resume all paused tasks from state/paused_tasks.json", mode=mode)
            console.print(output)

        elif cmd == "/budget":
            cmd_status()

        elif cmd == "/skills":
            cmd_skills(rest.split())

        elif cmd == "/mode":
            if rest in ("best", "avg", "cheap"):
                mode = rest
                console.print(f"[green]Mode set to:[/] {mode}")
            else:
                console.print("[red]Usage:[/] /mode best|avg|cheap")

        elif cmd == "/help":
            console.print("""
[bold]Commands:[/]
  /cto <idea> [--mode best|avg|cheap]   Start new project pipeline
  /cto continue phase-N                 Resume next phase
  /tl review pr: <url>                  Review a PR
  /status                               Show phase, budget, paused tasks
  /resume                               Retry paused tasks
  /budget                               Show token usage per model
  /skills list                          Show installed skills
  /skills search <query>                Find a skill
  /mode best|avg|cheap                  Switch model tier
  /help                                 This message
            """)

        else:
            console.print(f"[red]Unknown command:[/] {cmd} — try /help")


if __name__ == "__main__":
    main()
EOF

chmod +x main.py
echo "✓ main.py ready"
```

---

## Step 7 — First Run

```bash
# From ~/cxostack
uv run python main.py
```

You should see the banner and `cxostack>` prompt.

Test it:
```bash
cxostack> /status          # should show empty budget, no phase
cxostack> /skills list     # should show frontend-design
cxostack> /cto "Build a simple todo app" --mode avg
```

---

## Step 8 — Verify CC Agent Spawning

Before running a real project, verify CC can see your agents:

```bash
# In a separate terminal, start CC directly
cd ~/cxostack
claude

# Inside CC session:
> /agents
# Should list: cto, architect, arch-reviewer, planner,
#              team-leader, backend-developer, frontend-developer,
#              qa, code-reviewer, devops
```

If agents don't appear: check `.claude/agents/` has the .md files with correct frontmatter.

---

## Directory State After Setup

```
~/cxostack/
├── main.py                    ✓
├── orchestrator.py            (stub — Sprint 2)
├── model_router.py            (stub — Sprint 2)
├── skill_registry.py          (stub — Sprint 3)
├── skills.sh                  ✓
├── skill-registry.json        ✓
├── pyproject.toml             ✓ (uv generated)
├── .env                       ✓ (fill in keys)
├── .gitignore                 ✓
│
├── .claude/
│   ├── agents/
│   │   ├── cto.md             ✓
│   │   ├── architect.md       ✓
│   │   ├── arch-reviewer.md   ✓
│   │   ├── planner.md         ✓
│   │   ├── team-leader.md     ✓
│   │   ├── backend-developer.md ✓
│   │   ├── frontend-developer.md ✓
│   │   ├── qa.md              ✓
│   │   ├── code-reviewer.md   ✓
│   │   └── devops.md          ✓
│   └── skills/
│       └── frontend-design -> ~/.claude/skills/frontend-design ✓
│
├── agents/                    (stub prompts — Sprint 2 refines)
├── tools/                     (stubs — Sprint 2+)
├── state/
│   ├── session.json           ✓
│   ├── budget.json            ✓
│   └── paused_tasks.json      ✓
│
└── projects/                  (generated per /cto run)
```

---

## Sprint Checklist

```
Sprint 1 — Foundation                        STATUS
  ✓ Repo scaffold + uv setup
  ✓ All .claude/agents/ definitions
  ✓ skills.sh + user-level skill install
  ✓ skill-registry.json seed
  ✓ main.py CLI loop + /cto /tl /status
  □ orchestrator.py skeleton
  □ model_router.py (mode matrix)
  □ tools/ask_user.py (terminal bridge)
  □ tools/file_ops.py (read/write + ruff)

Sprint 2 — CTO + Architecture pipeline
  □ Refine agents/cto.md prompt (full spec)
  □ Refine agents/architect.md
  □ Refine agents/arch-reviewer.md
  □ CTO→Arch→Arch-Reviewer loop working
  □ spec.md + architecture.md generating correctly

Sprint 3 — Planning + Skill Management
  □ agents/planner.md refinement
  □ agents/team-leader.md (reviewer role)
  □ skill_registry.py — TL lookup logic
  □ tools/skill_ops.py — skills.sh wrapper + registry update
  □ phase-plan.md generating correctly

Sprint 4 — Dev Loop
  □ tools/git_ops.py (worktrees, branches, PRs via gh)
  □ usecase.md lifecycle
  □ QA agent — pytest + docker + Playwright
  □ Code-reviewer agent — gh pr diff
  □ PR approval + merge flow

Sprint 5 — DevOps + Docker
  □ tools/docker_ops.py
  □ Staging deploy + smoke tests
  □ Prod deploy
  □ Phase-level QA sweep

Sprint 6 — Resilience
  □ Pause/resume system
  □ Session persistence
  □ Groq relay (groq_relay.py)
  □ /budget tracking live
```

---

## Key Notes

**One important CC constraint:** Subagents cannot spawn other subagents — this prevents infinite nesting. This means your CTO agent uses the `Task` tool to invoke architect/planner, and team-leader uses `Task` to invoke developers — but developers cannot themselves spawn QA or reviewer as sub-subagents. Instead, developers report back to TL, and TL spawns QA and reviewer directly.

**Cost tip:** Using Haiku for exploration subagents and Sonnet for implementation typically reduces costs 40–50% compared to using Sonnet for everything. Your `avg` mode already follows this — Haiku for developers and reviewers, Sonnet for CTO and TL.

**Model override per agent:** Any agent's model can be overridden by editing its frontmatter `model:` field. Use `model: inherit` to match whatever your main CC session is using.
