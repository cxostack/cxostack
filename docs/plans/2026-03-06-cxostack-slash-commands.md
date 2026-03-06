# cxostack Slash Commands + Agent Dispatch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/cxostack:cto <idea>` and sibling slash commands to Claude Code IDE/CLI, implement Groq relay for cheap dev agent tasks, and wire `orchestrator.py` to dispatch non-Claude models.

**Architecture:** Slash commands in `.claude/commands/cxostack/` make Claude Code become the CTO brain inline. When TL dispatches developer tasks, `orchestrator.py dispatch` routes cheap tasks to `groq_relay.py` (Groq API, text-only) and avg/best tasks to `claude --dangerously-skip-permissions`. `main.py` gains CLI arg mode for terminal-only users.

**Tech Stack:** Python 3.12, `groq>=1.0.0` (already in pyproject.toml), `ruff` for formatting, Claude Code slash command markdown files.

---

### Task 1: Implement `tools/groq_relay.py`

**Files:**
- Modify: `tools/groq_relay.py` (currently empty stub)
- Create: `tests/test_groq_relay.py`

**Step 1: Write the failing test**

```python
# tests/test_groq_relay.py
from unittest.mock import MagicMock, patch


def test_call_groq_basic():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "def hello(): pass"

    with patch("tools.groq_relay.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = mock_response
        from tools.groq_relay import call_groq
        result = call_groq("write a hello function", "llama-3.1-8b-instant")

    assert result == "def hello(): pass"


def test_call_groq_with_system_prompt():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "result"

    with patch("tools.groq_relay.Groq") as MockGroq:
        instance = MockGroq.return_value
        instance.chat.completions.create.return_value = mock_response
        from tools.groq_relay import call_groq
        call_groq("prompt", "llama-3.1-8b-instant", system="you are a dev")

    call_args = instance.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "you are a dev"}
    assert messages[1] == {"role": "user", "content": "prompt"}


def test_call_groq_missing_key_raises():
    import os
    import pytest
    env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with patch("tools.groq_relay.Groq", side_effect=Exception("no key")):
            from tools.groq_relay import call_groq
            with pytest.raises(Exception):
                call_groq("prompt", "llama-3.1-8b-instant")
```

**Step 2: Run to confirm it fails**

```bash
uv run pytest tests/test_groq_relay.py -v
```

Expected: `ImportError` or `FAILED` — `call_groq` not yet defined.

**Step 3: Implement `tools/groq_relay.py`**

```python
#!/usr/bin/env python3
"""Groq relay — pure text generation for cheap dev agent tasks.

Groq agents have no tool access. This module calls the Groq API and returns
raw text. The orchestrator is responsible for all file writes and formatting.
"""

import os

from groq import Groq


def call_groq(prompt: str, model: str = "llama-3.1-8b-instant", system: str = "") -> str:
    """Call Groq API and return raw text output.

    Args:
        prompt: The user message to send.
        model: Groq model ID. Defaults to llama-3.1-8b-instant.
        system: Optional system prompt.

    Returns:
        Raw text response from the model.

    Raises:
        Exception: On API error or missing GROQ_API_KEY.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_groq_relay.py -v
```

Expected: 3 PASSED.

**Step 5: Commit**

```bash
git add tools/groq_relay.py tests/test_groq_relay.py
git commit -m "feat: implement groq_relay.py — Groq API caller for cheap dev agents"
```

---

### Task 2: Add `dispatch` subcommand to `orchestrator.py`

**Files:**
- Modify: `orchestrator.py`
- Create: `tests/test_orchestrator_dispatch.py`

**Step 1: Write the failing tests**

```python
# tests/test_orchestrator_dispatch.py
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch


def test_dispatch_cheap_calls_groq(tmp_path):
    """cheap mode routes to groq_relay, not claude."""
    target = tmp_path / "out.py"
    target.write_text("# placeholder\n")

    with patch("orchestrator.call_groq", return_value="def foo(): pass") as mock_groq:
        from orchestrator import dispatch

        dispatch(
            agent="backend-developer",
            task="write foo function",
            mode="cheap",
            file=str(target),
            line=1,
        )

    mock_groq.assert_called_once()
    assert "def foo(): pass" in target.read_text()


def test_dispatch_avg_calls_claude():
    """avg mode routes to claude subprocess."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        from orchestrator import dispatch

        dispatch(agent="backend-developer", task="write foo", mode="avg")

    cmd = mock_run.call_args[0][0]
    assert "claude" in cmd
    assert "--dangerously-skip-permissions" in cmd


def test_dispatch_cheap_no_file_prints_output(capsys):
    """cheap mode with no --file prints output to stdout."""
    with patch("orchestrator.call_groq", return_value="hello"):
        from orchestrator import dispatch

        dispatch(agent="qa", task="write test", mode="cheap")

    captured = capsys.readouterr()
    assert "hello" in captured.out
```

**Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_orchestrator_dispatch.py -v
```

Expected: `ImportError` — `dispatch` not yet defined.

**Step 3: Add `dispatch` function and CLI entry to `orchestrator.py`**

At the bottom of `orchestrator.py`, add the `dispatch` function and `__main__` block:

```python
def dispatch(
    agent: str,
    task: str,
    mode: str = "avg",
    file: str | None = None,
    line: int | None = None,
) -> None:
    """Route a task to the appropriate model based on mode.

    cheap mode  → Groq API via groq_relay.call_groq; orchestrator writes file
    avg/best    → claude --dangerously-skip-permissions --agent <role> --print -p

    Args:
        agent: Agent role name matching model_router.ROLE_MATRIX key.
        task: Full task prompt to send to the model.
        mode: Tier — "best", "avg", or "cheap".
        file: Optional file path to write output into.
        line: Optional line number to insert output at (1-indexed).
    """
    from model_router import get_model

    model = get_model(agent, mode)

    if model.startswith("groq/"):
        from tools.groq_relay import call_groq

        groq_model = model.split("/", 1)[1]
        output = call_groq(task, groq_model)

        if file and line is not None:
            _write_at_line(file, line, output)
            _ruff_format(file)
        else:
            print(output)
    else:
        result = subprocess.run(
            [
                "claude",
                "--dangerously-skip-permissions",
                "--agent",
                agent,
                "--model",
                model,
                "--print",
                "-p",
                task,
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.returncode != 0:
            console.print(f"[red]Agent {agent} error:[/] {result.stderr}")
        else:
            console.print(result.stdout)


def _write_at_line(file_path: str, line: int, content: str) -> None:
    """Insert content at line number in file_path (1-indexed, replaces that line)."""
    path = Path(file_path)
    lines = path.read_text().splitlines(keepends=True)
    idx = line - 1
    lines.insert(idx, content + "\n")
    path.write_text("".join(lines))


def _ruff_format(file_path: str) -> None:
    """Run ruff format on file_path. Silently skips if ruff not available."""
    subprocess.run(["ruff", "format", file_path], capture_output=True)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    d = subparsers.add_parser("dispatch", help="Route a task to the right model")
    d.add_argument("--agent", required=True)
    d.add_argument("--task", required=True)
    d.add_argument("--mode", default="avg")
    d.add_argument("--file", default=None)
    d.add_argument("--line", type=int, default=None)

    args = parser.parse_args()

    if args.command == "dispatch":
        dispatch(
            agent=args.agent,
            task=args.task,
            mode=args.mode,
            file=args.file,
            line=args.line,
        )
    else:
        parser.print_help()
        sys.exit(1)
```

Also update the existing `run_agent` method in the `Orchestrator` class to add `--dangerously-skip-permissions`:

```python
# In Orchestrator.run_agent(), update the subprocess.run call:
result = subprocess.run(
    [
        "claude",
        "--dangerously-skip-permissions",  # ADD THIS
        "--agent",
        agent_name,
        "--model",
        model,
        "--print",
        "-p",
        prompt,
    ],
    ...
)
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_orchestrator_dispatch.py -v
```

Expected: 3 PASSED.

**Step 5: Commit**

```bash
git add orchestrator.py tests/test_orchestrator_dispatch.py
git commit -m "feat: add orchestrator dispatch — routes cheap tasks to Groq, adds --dangerously-skip-permissions"
```

---

### Task 3: Add CLI arg mode to `main.py`

**Files:**
- Modify: `main.py`
- Create: `tests/test_main_cli.py`

**Step 1: Write the failing tests**

```python
# tests/test_main_cli.py
import sys
from unittest.mock import patch


def test_cli_cto_calls_cmd_cto():
    with patch("sys.argv", ["main.py", "cto", "my saas idea"]):
        with patch("main.cmd_cto") as mock:
            from main import _cli_mode
            _cli_mode()
    mock.assert_called_once_with("my saas idea", "avg")


def test_cli_cto_onboard_calls_cmd_onboard():
    with patch("sys.argv", ["main.py", "cto", "onboard"]):
        with patch("main.cmd_cto_onboard") as mock:
            from main import _cli_mode
            _cli_mode()
    mock.assert_called_once()


def test_cli_status_calls_cmd_status():
    with patch("sys.argv", ["main.py", "status"]):
        with patch("main.cmd_status") as mock:
            from main import _cli_mode
            _cli_mode()
    mock.assert_called_once()


def test_cli_mode_respected():
    with patch("sys.argv", ["main.py", "cto", "my idea", "--mode", "best"]):
        with patch("main.cmd_cto") as mock:
            from main import _cli_mode
            _cli_mode()
    mock.assert_called_once_with("my idea", "best")
```

**Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_main_cli.py -v
```

Expected: `ImportError` — `_cli_mode` not defined.

**Step 3: Add `_cli_mode` and update `__main__` block in `main.py`**

Add `import sys` at the top of `main.py` (after existing imports).

Add this function before the `main()` function:

```python
def _cli_mode() -> None:
    """Handle CLI invocation: python main.py <command> [args] [--mode best|avg|cheap]"""
    import argparse

    parser = argparse.ArgumentParser(prog="cxostack")
    parser.add_argument("--mode", default=os.getenv("DEFAULT_MODE", "avg"),
                        choices=["best", "avg", "cheap"])
    subparsers = parser.add_subparsers(dest="command")

    cto_p = subparsers.add_parser("cto")
    cto_p.add_argument("subcommand_or_idea", nargs="?", default="")

    cmo_p = subparsers.add_parser("cmo")
    cmo_p.add_argument("project")

    subparsers.add_parser("status")

    args = parser.parse_args()

    if args.command == "cto":
        sub = args.subcommand_or_idea
        if sub == "onboard":
            cmd_cto_onboard(args.mode)
        elif sub.startswith("continue"):
            tokens = sub.split()
            if len(tokens) < 2:
                console.print("[red]Usage:[/] cxostack cto continue <phase>")
            else:
                cmd_cto_continue(tokens[1], args.mode)
        elif sub == "status":
            cmd_cto_status()
        elif sub:
            cmd_cto(sub, args.mode)
        else:
            console.print("[red]Usage:[/] cxostack cto <idea|onboard|continue <phase>|status>")

    elif args.command == "cmo":
        cmd_cmo(args.project, args.mode)

    elif args.command == "status":
        cmd_status()

    else:
        parser.print_help()
```

Update `__main__` block at the bottom of `main.py`:

```python
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        _cli_mode()
    else:
        main()
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_main_cli.py -v
```

Expected: 4 PASSED.

**Step 5: Commit**

```bash
git add main.py tests/test_main_cli.py
git commit -m "feat: add CLI arg mode to main.py — python main.py cto <idea>"
```

---

### Task 4: Create `.claude/commands/cxostack/` slash commands

**Files:**
- Create: `.claude/commands/cxostack/cto.md`
- Create: `.claude/commands/cxostack/onboard.md`
- Create: `.claude/commands/cxostack/cmo.md`
- Create: `.claude/commands/cxostack/status.md`

No tests — these are markdown instruction files for Claude Code. Verify manually.

**Step 1: Create `.claude/commands/cxostack/cto.md`**

```markdown
---
description: Run the CTO pipeline for a new project idea. Usage: /cxostack:cto <idea>
---

You are the CTO of this engineering team. Follow the instructions in `.claude/agents/cto.md` exactly.

Before doing anything:
1. Read `~/.cxostack/founder-profile.md` if it exists — never ask for info already there.
2. Read `~/.cxostack/cto-memory.md` if it exists.
3. If founder-profile.md is missing or empty, tell the founder to run `/cxostack:onboard` first.

The founder's request: $ARGUMENTS

If $ARGUMENTS is empty, print usage:
  /cxostack:cto <idea>            — start full pipeline
  /cxostack:cto onboard           — run founder interview
  /cxostack:cto continue phase-N  — spawn TL for phase N
  /cxostack:cto status            — show current project state

When spawning sub-agents (architect, planner, team-leader), use the Task tool.
When team-leader needs to dispatch developer tasks, instruct it to call:
  python orchestrator.py dispatch --agent <role> --task "..." --mode <mode> [--file <path> --line <n>]
```

**Step 2: Create `.claude/commands/cxostack/onboard.md`**

```markdown
---
description: Run the CTO founder onboarding interview. Writes ~/.cxostack/founder-profile.md
---

You are the CTO of this engineering team. Run the founder onboarding interview.

Follow the `/cto onboard` section in `.claude/agents/cto.md` exactly:
- Ask the 5 questions one at a time, not all at once
- Acknowledge each answer before asking the next
- After all 5 answers, write ~/.cxostack/founder-profile.md and ~/.cxostack/cto-memory.md
- Use memory/founder-profile.template.md and memory/cto-memory.template.md as structure
- Create ~/.cxostack/ if it does not exist

Do not ask the founder for information you already have.
```

**Step 3: Create `.claude/commands/cxostack/cmo.md`**

```markdown
---
description: Run the CMO GTM pipeline for a project. Usage: /cxostack:cmo <project>
---

You are the CMO of this company. Follow the instructions in `.claude/agents/cmo.md` exactly.

Before doing anything:
1. Read `~/.cxostack/founder-profile.md` if it exists.
2. Read `~/.cxostack/cmo-memory.md` if it exists.

The founder's request: $ARGUMENTS

If $ARGUMENTS is empty, print usage:
  /cxostack:cmo <project>          — build GTM strategy
  /cxostack:cmo onboard            — run CMO founder interview
  /cxostack:cmo campaign <goal>    — plan a specific campaign
  /cxostack:cmo review             — audit current marketing
```

**Step 4: Create `.claude/commands/cxostack/status.md`**

```markdown
---
description: Show current project status, phase, budget, and paused tasks.
---

Read the following files and report their contents in a clean summary:
- `state/session.json` — current project slug, phase, mode
- `state/budget.json` — token usage per model (used / limit / %)
- `state/paused_tasks.json` — any paused tasks with their reasons

If any file is missing or unreadable, note it and continue with the rest.

Format the output as:
  Project: <slug>  Phase: <n>  Mode: <mode>
  Budget: <model>: <used>/<limit> (<pct>%) ...
  Paused: <task_id> — <reason>  (or "none")
```

**Step 5: Verify slash commands work**

In Claude Code IDE, type:
```
/cxostack:onboard
```
Expected: Claude asks the first onboarding question.

```
/cxostack:status
```
Expected: Claude reads state files and reports project status.

**Step 6: Commit**

```bash
git add .claude/commands/cxostack/
git commit -m "feat: add /cxostack:cto, onboard, cmo, status slash commands"
```

---

### Task 5: Full integration smoke test

**Step 1: Run all new tests together**

```bash
uv run pytest tests/test_groq_relay.py tests/test_orchestrator_dispatch.py tests/test_main_cli.py -v
```

Expected: 10 PASSED, 0 FAILED.

**Step 2: Verify ruff**

```bash
uv run ruff check tools/groq_relay.py orchestrator.py main.py
uv run ruff format --check tools/groq_relay.py orchestrator.py main.py
```

Expected: no errors.

**Step 3: Smoke test CLI mode**

```bash
# Should print help, not start REPL
python main.py --help

# Should start REPL (no args)
python main.py
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: smoke test pass — slash commands + groq relay + CLI mode complete"
```
