# Sprint 3 Design — Planning + Skill Management
> Date: 2026-02-23 | Status: Approved

## What we're building

Four small pieces of glue that let the CTO pipeline go all the way through to phase execution.

## Items

### A. `planner.md` (medium spec addition)
Add the exact output format the planner must write. No structural rewrite — just add:
- Exact `phase-plan.md` section/task format
- Task JSON fields: usecase, type (backend/frontend), complexity, acceptance_criteria
- Rule: each task must map to exactly one usecase file path

### B. `team-leader.md` (full rewrite — ~40 lines)
Clear numbered execution protocol:
1. Read phase-plan.md for assigned phase
2. Check skill-registry.json for each agent role
3. Spawn developers in parallel (max 10) with task prompt + usecase.md path
4. Checkpoint state to `state/tl_checkpoint_phase_{n}.json`
5. After all tasks: spawn QA sweep
6. Read bug report, spawn bug-fix devs if needed
7. Spawn devops for staging + prod deploy
8. Report done

### C. `skill_registry.py` (~30 lines)
Simple functions, no class needed:
- `get_skills(agent_role: str) -> list[str]` — reads skill-registry.json
- `log_missing(agent_role: str, skill_name: str)` — appends to missing_log

### D. `tools/skill_ops.py` (~25 lines)
Thin subprocess wrapper around skills.sh:
- `search(query: str) -> str`
- `install(name: str, scope: str = "user") -> bool`
- `list_installed() -> str`

## Execution

Parallel tracks:
- Track A (Python): skill_registry.py + tools/skill_ops.py
- Track B (Agents): planner.md + team-leader.md

Validation: `uv run ruff check` passes on all Python files.
