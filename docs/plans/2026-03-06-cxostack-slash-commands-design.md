# Design: /cxostack slash commands + agent dispatch

**Date:** 2026-03-06
**Branch:** feat/provider-setup-onboard
**Status:** Approved

---

## Problem

Developers working in Claude Code IDE or Claude CLI have no direct entry point into the cxostack pipeline. They must run `python main.py` as a REPL. There is also no mechanism to dispatch grunt work (code generation) to cheap models — `tools/groq_relay.py` is an empty stub and `orchestrator.py` only routes to Claude models.

---

## Principle

**Claude is the brain, not the contributor.**

- CTO / Architect / Planner / TL = Claude (Sonnet/Opus) — plan, decide, review
- Developers / QA / DevOps in cheap mode = Groq/Haiku — generate code as text
- Python orchestrator = hands — writes files, runs linter, manages state

---

## Entry Points

```
.claude/commands/cxostack/
  cto.md       →  /cxostack:cto <idea>
  onboard.md   →  /cxostack:onboard
  cmo.md       →  /cxostack:cmo <project>
  status.md    →  /cxostack:status
```

Each command file instructs the current Claude Code session to become that CxO agent inline. It reads the corresponding `.claude/agents/*.md` definition and `~/.cxostack/` memory files before acting.

`main.py` REPL is preserved for terminal-only users. `main.py` also gains a CLI arg mode so `python main.py cto "idea"` works for scripting.

---

## Permissions

Sub-agents spawned via `orchestrator.py` run with `--dangerously-skip-permissions`. Working directory for all sub-agents is `projects/{slug}/`. Tool-specific and deployment access will be scoped in a later sprint.

---

## Dispatch Flow

```
/cxostack:cto "SaaS invoicing tool"
        │
        ▼
  Claude Code = CTO (inline, current session)
  reads ~/.cxostack/founder-profile.md + cto-memory.md
  runs interview → spec.md → architecture loop → phase-plan.md
        │
        ▼  Task tool (Claude sub-agent)
  Architect → architecture.md
  Arch-Reviewer → review loop (max 3)
        │
        ▼  Task tool (Claude sub-agent)
  Planner → phase-plan.md
        │
        ▼  Task tool (Claude sub-agent, per phase)
  Team Leader → reads phase-plan.md, dispatches tasks
        │
        ▼  Bash: python orchestrator.py dispatch ...
  orchestrator routes by mode:
    best/avg  →  claude --dangerously-skip-permissions --agent <role> --print -p "..."
    cheap     →  groq_relay.py → Groq API → raw text
                 orchestrator writes to exact file location
                 ruff format
```

---

## Files Changed

| File | Action | Description |
|---|---|---|
| `.claude/commands/cxostack/cto.md` | Create | Slash command — inline CTO |
| `.claude/commands/cxostack/onboard.md` | Create | Slash command — inline onboard |
| `.claude/commands/cxostack/cmo.md` | Create | Slash command — inline CMO |
| `.claude/commands/cxostack/status.md` | Create | Slash command — inline status |
| `orchestrator.py` | Update | Add `--dangerously-skip-permissions`, add `dispatch` CLI subcommand, route cheap agents to `groq_relay.py` |
| `tools/groq_relay.py` | Implement | Groq API caller — takes role/prompt/model, returns raw text |
| `main.py` | Update | Add CLI arg mode alongside existing REPL |

---

## groq_relay.py Contract

```python
def call_groq(prompt: str, model: str, system: str = "") -> str:
    """Call Groq API. Returns raw text output. Raises on error."""
```

- Input: prompt string, model ID (e.g. `llama-3.1-8b-instant`), optional system prompt
- Output: raw text (code, prose, whatever the agent requested)
- No file I/O — orchestrator handles all writes
- Requires `GROQ_API_KEY` in `.env`

---

## orchestrator.py dispatch subcommand

```bash
python orchestrator.py dispatch \
  --agent backend-developer \
  --task "implement user auth endpoint in src/routes/auth.py" \
  --file src/routes/auth.py \
  --line 42 \
  --mode cheap
```

- `--mode cheap` → calls `groq_relay.py`, writes output at `--file:--line`, runs `ruff format`
- `--mode avg/best` → calls `claude --dangerously-skip-permissions --agent <role> --print -p ...`
- Writes result to `state/session.json` (task completed marker)

---

## main.py CLI arg mode

```bash
# existing REPL (unchanged)
python main.py

# new CLI mode
python main.py cto "build a SaaS invoicing tool"
python main.py cto onboard
python main.py cmo "my-project"
python main.py status
```

Detection: if `sys.argv[1:]` is non-empty, run CLI mode and exit. Otherwise start REPL.

---

## Out of Scope (this sprint)

- Deployment-specific tool permissions (Docker, cloud CLIs)
- GLM / other non-Groq model providers
- Budget enforcement for Groq calls (tracked but not enforced yet)
- `/cxostack:ciso` and `/cxostack:sre` commands (stubs only)
