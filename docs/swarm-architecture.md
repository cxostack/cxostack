# Agent CXOtack — Final Architecture
> All decisions locked. Ready to build.

---

## 1. Core Decisions (Locked)

| Decision | Choice |
|---|---|
| Runtime | Claude Code CLI only (plug-and-play later) |
| Interface | Terminal / CLI Python script |
| Staging | Docker-based |
| QA Scope | Unit + Integration + E2E (Playwright) |
| External models | Groq (when available). Pure text tasks → Groq API + Python writes file |
| Code formatting | ruff for all Python |
| Slack | Skip. CLI only |
| Skill management | TL-managed, skills.sh discovery, skill-registry.json |

---

## 2. Model Mode System

Three modes selectable at runtime: `--mode best | avg | cheap`

```
┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Agent           │ best             │ avg              │ cheap            │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ CTO             │ claude-opus-4    │ claude-sonnet-4.6│ claude-sonnet-4.6│
│ Architect       │ claude-opus-4    │ claude-sonnet-4.6│ claude-sonnet-4.6│
│ Arch-Reviewer   │ claude-sonnet-4.6│ claude-sonnet-4.6│ claude-haiku-4.5 │
│ Planner         │ claude-sonnet-4.6│ claude-sonnet-4.6│ claude-haiku-4.5 │
│ Team-Leader     │ claude-sonnet-4.6│ claude-sonnet-4.6│ claude-haiku-4.5 │
│ Backend Dev     │ claude-sonnet-4.6│ claude-haiku-4.5 │ groq/llama-4     │
│ Frontend Dev    │ claude-sonnet-4.6│ claude-haiku-4.5 │ groq/llama-4     │
│ QA              │ claude-sonnet-4.6│ claude-haiku-4.5 │ groq/llama-4     │
│ Code-Reviewer   │ claude-sonnet-4.6│ claude-haiku-4.5 │ groq/llama-4     │
│ DevOps          │ claude-haiku-4.5 │ claude-haiku-4.5 │ groq/llama-4     │
└─────────────────┴──────────────────┴──────────────────┴──────────────────┘

Note: Groq models = pure text generation only.
      Python layer handles all file writes, git ops, ruff formatting.
      CC handles execution for Claude-based agents.
```

### Model-capability contract
```python
MODEL_CAPS = {
    "claude-*":   {"tool_use": True,  "file_rw": True,  "exec": True},
    "groq/*":     {"tool_use": False, "file_rw": False, "exec": False},
}
# If tool_use=False → orchestrator.py handles all I/O on model's behalf
# If file_rw=False  → write output to disk via Python, then run ruff
```

---

## 3. Repository Structure

```
cxostack/
├── main.py                        # CLI entry: /cto, /tl, /resume, /status
├── orchestrator.py                # Agent lifecycle, budget, pause/resume
├── model_router.py                # Mode-based model selection
├── skill_registry.py              # TL skill lookup + assignment
│
├── agents/                        # System prompts + agent logic
│   ├── cto.md
│   ├── architect.md
│   ├── arch_reviewer.md
│   ├── planner.md
│   ├── team_leader.md
│   ├── developer_backend.md
│   ├── developer_frontend.md
│   ├── qa.md
│   ├── code_reviewer.md
│   └── devops.md
│
├── tools/                         # Tool implementations
│   ├── ask_user.py                # Terminal I/O bridge
│   ├── file_ops.py                # Read/write + ruff format
│   ├── git_ops.py                 # Worktrees, branches, PRs
│   ├── docker_ops.py              # Staging env management
│   ├── skill_ops.py               # skills.sh wrapper, registry update
│   └── groq_relay.py             # Groq API call + Python applies output
│
├── state/
│   ├── session.json               # Active session history (resumable)
│   ├── budget.json                # Per-model token usage
│   ├── paused_tasks.json          # Tasks awaiting credit/resume
│   └── tl_checkpoint_phase_{n}.json
│
├── skill-registry.json            # Known skills, per-role assignments
│
└── projects/
    └── {project-slug}/
        ├── spec.md
        ├── architecture.md
        ├── phase-plan.md
        ├── phases/
        │   └── phase-{n}.md       # QA bug reports
        ├── usecases/
        │   └── {usecase}.md       # Per-dev context file
        └── .worktrees/
            └── {usecase}/         # Git worktree per developer
```

---

## 4. CLI Commands

```bash
python main.py                         # starts interactive session

cxostack> /cto "Build invoice SaaS"       # full pipeline
cxostack> /cto "..." --mode cheap         # use cheap model tier
cxostack> /cto continue phase-2           # CTO spawns new TL for phase 2
cxostack> /tl review pr: https://...      # isolated PR review session
cxostack> /status                         # current phase, tasks, budget
cxostack> /resume                         # retry all paused tasks
cxostack> /budget                         # show per-model usage + limits
cxostack> /skills list                    # show skill-registry.json
cxostack> /skills find react              # TL searches for react skill
```

---

## 5. Agent Flow (Detailed)

### Step 1 — /cto triggers CTO agent
```
CTO system prompt loaded from agents/cto.md
Tools available: ask_user, write_file, invoke_agent, read_file

CTO loop:
  → ask_user (N questions via terminal bridge)
  → write_file("projects/{slug}/spec.md")
  → invoke_agent("architect")
```

### Step 2 — Architecture loop (max 3 iterations, CTO governs)
```
CTO spawns Architect (new CC subprocess, own history)
  Architect reads spec.md → designs system → writes architecture.md
  CTO spawns Arch-Reviewer
  Arch-Reviewer reads architecture.md → writes review comments
  CTO reads both outputs → decides: approve or loop (max 3×)
  CTO may ask_user if blocking decisions needed (payment gw, db choice, etc.)
  CTO finalises → prints architecture.md summary to terminal
```

### Step 3 — Planning loop (max 3 iterations)
```
CTO spawns Planner
  Planner reads spec.md + architecture.md → writes phase-plan.md
  CTO spawns Team-Leader (reviewer role here)
  TL reads phase-plan.md → writes feedback
  Loop max 3× → finalised phase-plan.md
```

### Step 4 — Development (per phase)
```
CTO spawns Team-Leader (execution role, phase-scoped)

TL:
  reads phase-plan.md → identifies tasks for this phase
  for each task:
    → checks skill-registry.json for required skills
    → if skill missing: runs skill_ops.find() → updates registry
    → assigns task + skills to developer agent

TL spawns developer agents (max 10: 5 backend, 5 frontend)
  each developer:
    → receives task as JSON + usecase.md path
    → creates git worktree (.worktrees/{usecase})
    → creates branch (feature/{usecase} or bug/phase-{n}/{name})
    → codes → commits → pushes → raises PR
    → spawns QA agent (passes usecase.md)
    → spawns Code-Reviewer agent (passes usecase.md + PR diff)

QA agent:
    → reads usecase.md (requirements, acceptance criteria)
    → writes unit tests → runs via CC bash tool
    → spins up docker-compose for integration tests
    → runs Playwright for E2E
    → writes results to usecase.md (QA section)
    → approves or returns bugs to developer

Code-Reviewer:
    → reads usecase.md + git diff
    → reviews for: correctness, security, perf, style
    → writes review to usecase.md (Review section)
    → approves or returns improvements

Developer:
    → fixes QA bugs / reviewer comments → re-triggers QA+Review
    → once both approve → notifies TL
    → TL merges PR → closes developer + QA + reviewer sessions

TL after all tasks complete:
    → spawns phase-level QA sweep
    → QA writes bugs to phases/phase-{n}.md
    → TL spawns bug-fix developers (branch: bug/phase-{n}/{task})
    → same dev cycle per bug
    → spawns DevOps → docker build → staging deploy
    → runs E2E on staging
    → DevOps → prod deploy
    → prints "Phase {n} live on prod" to terminal
    → TL closes itself
```

### Step 5 — Human verification
```
You review prod.
cxostack> /cto continue phase-2
CTO spawns new Team-Leader for phase 2.
```

---

## 6. usecase.md Structure

Every developer creates and owns this file. QA and Reviewer both read and append to it.

```markdown
# Usecase: {name}

## Task Details
- Task IDs: TASK-12, TASK-13
- Phase: 1
- Assigned to: backend-dev-2
- Model: claude-haiku-4.5 (avg mode)

## Branch & Worktree
- Branch: feature/user-auth
- Worktree: .worktrees/user-auth
- PR: https://github.com/org/repo/pull/12

## Requirements (from TL)
- Implement JWT auth with refresh tokens
- POST /auth/login, POST /auth/refresh, POST /auth/logout
- Store sessions in Redis, user records in Postgres

## Skills Loaded
- supabase (auth patterns)
- backend-api (REST conventions)

## Acceptance Criteria
- [ ] Login returns access + refresh token
- [ ] Refresh rotates tokens
- [ ] Invalid tokens return 401
- [ ] Unit test coverage >80%

## QA Results
### Unit Tests
- Status: PASSED (24/24)
- Coverage: 87%
### Integration Tests
- Status: PASSED
### E2E Tests
- Status: PASSED (login flow, session expiry)

## Code Review
- Reviewer: code-reviewer (claude-haiku-4.5)
- Status: APPROVED
- Notes: Suggested rate limiting on /login — implemented in TASK-14

## Status
- [x] Development complete
- [x] QA approved
- [x] Code review approved
- [x] PR merged
```

---

## 7. Skill Management Flow

```
TL receives task: "implement React dashboard with recharts"

1. TL reads task requirements
2. TL checks skill-registry.json:
   → frontend-developer role has: ["css", "html", "vanilla-js"]
   → missing: react, recharts

3. TL calls skill_ops.find("react"):
   → runs: bash skills.sh search react
   → finds: /mnt/skills/public/frontend-design/SKILL.md (partial match)
   → finds: no dedicated react skill

4. TL decision:
   → frontend-design skill covers component patterns → load it
   → no recharts skill → TL notes in registry as "not found, used frontend-design"

5. TL updates skill-registry.json:
   {
     "task": "TASK-22",
     "usecase": "dashboard",
     "skills_loaded": ["frontend-design"],
     "skills_missing": ["react-specific", "recharts"],
     "fallback_used": "frontend-design",
     "timestamp": "2026-02-19T10:00:00Z"
   }

6. TL passes skills to developer agent context:
   → developer's system prompt prepended with contents of loaded SKILL.md files
```

---

## 8. Groq Relay Pattern (for cheap mode)

When a non-CC model (Groq) is selected, Python orchestrator wraps it:

```python
# groq_relay.py
def run_groq_task(task: dict, model: str) -> dict:
    # 1. Build prompt from task
    prompt = build_prompt(task)
    
    # 2. Call Groq API (text in, text out)
    response = groq_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    raw_output = response.choices[0].message.content
    
    # 3. Parse structured output (model must return JSON)
    parsed = json.loads(extract_json(raw_output))
    
    # 4. Python applies the output
    for file_op in parsed.get("files", []):
        write_file(file_op["path"], file_op["content"])
        if file_op["path"].endswith(".py"):
            subprocess.run(["ruff", "format", file_op["path"]])
            subprocess.run(["ruff", "check", "--fix", file_op["path"]])
    
    # 5. Run any commands
    for cmd in parsed.get("commands", []):
        subprocess.run(cmd, shell=True)
    
    return {"status": "done", "files_written": [...], "output": parsed}
```

Groq models are prompted to always return:
```json
{
  "reasoning": "...",
  "files": [{"path": "src/auth.py", "content": "..."}],
  "commands": ["pytest src/tests/test_auth.py"],
  "summary": "Implemented JWT auth with refresh tokens"
}
```

---

## 9. Pause / Resume System

```python
# orchestrator.py — budget enforcement
def select_model_for_task(task, mode):
    preferred = MODEL_MATRIX[task.agent_type][mode]
    budget = load_budget()
    
    for model in preferred:  # tries in priority order
        remaining = budget[model]["limit"] - budget[model]["used"]
        if remaining > task.estimated_tokens:
            return model
    
    # No model has enough budget
    pause_task(task)
    return None

def pause_task(task):
    paused = load_json("state/paused_tasks.json")
    paused.append({
        "task_id": task.id,
        "agent": task.agent_type,
        "estimated_tokens": task.estimated_tokens,
        "context_checkpoint": task.history,   # save full history
        "paused_at": datetime.utcnow().isoformat(),
        "reason": "budget_exhausted"
    })
    save_json("state/paused_tasks.json", paused)
    print(f"\n[CXOSTACK] Task {task.id} paused — insufficient budget.")
    print(f"        Run /resume when credits are available.\n")

def resume_tasks():
    paused = load_json("state/paused_tasks.json")
    resumed = []
    for task in paused:
        model = select_model_for_task(task, current_mode)
        if model:
            # restore history checkpoint → continue agent loop
            restart_agent(task, model)
            resumed.append(task["task_id"])
    print(f"[CXOSTACK] Resumed: {resumed}")
```

---

## 10. Build Sequence

```
Sprint 1 — Foundation
  □ main.py (CLI loop, command parser)
  □ orchestrator.py (agent lifecycle skeleton)
  □ model_router.py (mode matrix, budget tracker)
  □ tools/ask_user.py (terminal bridge)
  □ tools/file_ops.py (read/write/ruff)

Sprint 2 — CTO + Architecture pipeline
  □ agents/cto.md (system prompt)
  □ agents/architect.md
  □ agents/arch_reviewer.md
  □ CTO → Arch → Arch-Reviewer loop with ask_user bridge
  □ spec.md + architecture.md generation

Sprint 3 — Planning + Team Leader
  □ agents/planner.md
  □ agents/team_leader.md
  □ skill_registry.py + tools/skill_ops.py
  □ phase-plan.md generation

Sprint 4 — Dev Loop
  □ agents/developer_backend.md + developer_frontend.md
  □ tools/git_ops.py (worktrees, branches, PRs)
  □ usecase.md lifecycle
  □ QA agent + Playwright integration
  □ Code-Reviewer agent
  □ PR approval + merge flow

Sprint 5 — DevOps + Docker
  □ agents/devops.md
  □ tools/docker_ops.py (staging, prod deploy)
  □ Phase-level QA sweep
  □ Bug fix cycle

Sprint 6 — Resilience
  □ Pause/resume system
  □ Session persistence (session.json)
  □ Groq relay (groq_relay.py)
  □ /status, /budget, /resume commands
```
