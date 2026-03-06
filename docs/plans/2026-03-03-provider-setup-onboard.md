# Provider Setup During `/cto onboard` Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive provider key-collection flow to `cmd_cto_onboard()` in `main.py` that asks the user which AI providers to activate and collects their API keys, saving them to `.env`.

**Architecture:** A `setup_providers()` function is added to `main.py` and called at the start of `cmd_cto_onboard()`. Two pure helper functions (`_mask_key`, `_write_env_key`) handle display and `.env` file writes. All provider metadata lives in a `PROVIDERS` list at module level. Tests cover the two pure helpers only (the interactive flow is tested manually).

**Tech Stack:** Python 3.12, Rich (already in deps for console/Prompt), python-dotenv (already in deps for dotenv_values), pytest (add to dev deps)

---

## Context

- **Entry point:** `main.py` — the cxostack CLI
- **Relevant function:** `cmd_cto_onboard()` at line 52
- **Key deps:** `Rich` (console, Prompt, Table), `python-dotenv` (dotenv_values)
- **`.env.example`:** template for environment variables — update to add optional provider slots
- **Design doc:** `docs/plans/2026-03-03-provider-setup-onboard-design.md`
- **Run tests with:** `uv run pytest --tb=short`
- **Lint/format:** `uv run ruff format . && uv run ruff check .`

---

### Task 1: Add pytest to dev dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add pytest to dev group**

In `pyproject.toml`, update `[dependency-groups]` to:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.15.2",
]
```

**Step 2: Sync dependencies**

```bash
uv sync
```

Expected: resolves and installs pytest.

**Step 3: Create tests directory with empty init**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 4: Verify pytest runs (no tests yet, that's fine)**

```bash
uv run pytest --tb=short
```

Expected output: `no tests ran` or `0 passed` — not an error.

**Step 5: Commit**

```bash
git add pyproject.toml tests/__init__.py
git commit -m "chore: add pytest to dev deps and create tests/"
```

---

### Task 2: Add `_mask_key` helper with tests

**Files:**
- Modify: `main.py` (add `_mask_key` function after the `BANNER` constant)
- Create: `tests/test_main.py`

**Step 1: Write the failing tests first**

Create `tests/test_main.py`:

```python
"""Tests for pure helper functions in main.py."""

from main import _mask_key


def test_mask_key_long_key():
    result = _mask_key("sk-ant-api03-abc123xyz")
    assert result == "sk-ant***yz"


def test_mask_key_short_key():
    result = _mask_key("abc123")
    assert result == "***"


def test_mask_key_exactly_8_chars():
    result = _mask_key("12345678")
    assert result == "***"


def test_mask_key_9_chars():
    result = _mask_key("123456789")
    assert result == "123456***89"
```

**Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_main.py -v
```

Expected: `ImportError: cannot import name '_mask_key' from 'main'`

**Step 3: Add `_mask_key` to `main.py`**

Insert after line 14 (after `console = Console()`), before the `BANNER` constant:

```python
def _mask_key(value: str) -> str:
    """Return a masked display string for an API key."""
    if len(value) <= 8:
        return "***"
    return value[:6] + "***" + value[-2:]
```

**Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_main.py::test_mask_key_long_key tests/test_main.py::test_mask_key_short_key tests/test_main.py::test_mask_key_exactly_8_chars tests/test_main.py::test_mask_key_9_chars -v
```

Expected: 4 PASSED

**Step 5: Lint**

```bash
uv run ruff format main.py && uv run ruff check main.py
```

Expected: no errors.

**Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add _mask_key helper for API key display"
```

---

### Task 3: Add `_write_env_key` helper with tests

**Files:**
- Modify: `main.py` (add `_write_env_key` after `_mask_key`)
- Modify: `tests/test_main.py` (add tests)

**Step 1: Add failing tests to `tests/test_main.py`**

Append to the existing file:

```python
import os
import tempfile
from pathlib import Path

from main import _write_env_key


def test_write_env_key_creates_file_if_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        _write_env_key("FOO", "bar123", env_path=env_path)
        assert env_path.read_text() == "FOO=bar123\n"


def test_write_env_key_appends_new_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("EXISTING=value\n")
        _write_env_key("NEW_KEY", "newval", env_path=env_path)
        content = env_path.read_text()
        assert "EXISTING=value\n" in content
        assert "NEW_KEY=newval\n" in content


def test_write_env_key_updates_existing_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("ANTHROPIC_API_KEY=old-value\nOTHER=keep\n")
        _write_env_key("ANTHROPIC_API_KEY", "new-value", env_path=env_path)
        content = env_path.read_text()
        assert "ANTHROPIC_API_KEY=new-value\n" in content
        assert "old-value" not in content
        assert "OTHER=keep\n" in content


def test_write_env_key_preserves_comments():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("# Required\nANTHROPIC_API_KEY=old\n")
        _write_env_key("ANTHROPIC_API_KEY", "updated", env_path=env_path)
        content = env_path.read_text()
        assert "# Required\n" in content
        assert "ANTHROPIC_API_KEY=updated\n" in content
```

**Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_main.py -k "write_env" -v
```

Expected: `ImportError: cannot import name '_write_env_key' from 'main'`

**Step 3: Add `_write_env_key` to `main.py`**

Insert after `_mask_key`:

```python
def _write_env_key(key: str, value: str, env_path: Path = Path(".env")) -> None:
    """Write or update a key=value line in the .env file."""
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        return

    lines = env_path.read_text().splitlines(keepends=True)
    updated = False
    result = []
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            result.append(f"{key}={value}\n")
            updated = True
        else:
            result.append(line)

    if not updated:
        result.append(f"{key}={value}\n")

    env_path.write_text("".join(result))
```

**Step 4: Run all tests**

```bash
uv run pytest tests/test_main.py -v
```

Expected: all PASSED (4 mask tests + 4 write_env tests = 8 total)

**Step 5: Lint**

```bash
uv run ruff format main.py && uv run ruff check main.py
```

**Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add _write_env_key helper for .env file updates"
```

---

### Task 4: Add `PROVIDERS` list and `setup_providers()` function

**Files:**
- Modify: `main.py`

**Step 1: Add `PROVIDERS` list to `main.py`**

Insert after the `BANNER` constant (after line 23), before `run_claude_agent`:

```python
PROVIDERS: list[dict] = [
    # Required — always prompted
    {
        "name": "Anthropic",
        "key": "ANTHROPIC_API_KEY",
        "required": True,
        "models": "claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5",
    },
    {
        "name": "GitHub",
        "key": "GITHUB_TOKEN",
        "required": True,
        "models": "repo management via gh CLI",
    },
    # Optional — user selects
    {
        "name": "OpenAI",
        "key": "OPENAI_API_KEY",
        "required": False,
        "models": "gpt-4o, gpt-4o-mini",
    },
    {
        "name": "Groq",
        "key": "GROQ_API_KEY",
        "required": False,
        "models": "llama-3.1-8b-instant (fast, free tier)",
    },
    {
        "name": "Mistral",
        "key": "MISTRAL_API_KEY",
        "required": False,
        "models": "mistral-large-latest",
    },
    {
        "name": "Together.ai",
        "key": "TOGETHER_API_KEY",
        "required": False,
        "models": "open-source model catalog",
    },
    {
        "name": "Google",
        "key": "GOOGLE_API_KEY",
        "required": False,
        "models": "gemini-1.5-pro, gemini-flash",
    },
    {
        "name": "Cohere",
        "key": "COHERE_API_KEY",
        "required": False,
        "models": "command-r-plus",
    },
]
```

**Step 2: Add `setup_providers()` function**

Insert after the `PROVIDERS` list, before `run_claude_agent`:

```python
def setup_providers() -> None:
    """Interactive provider key-collection flow. Called at the start of /cto onboard."""
    from dotenv import dotenv_values
    from rich.table import Table

    existing = dotenv_values(".env")
    required = [p for p in PROVIDERS if p["required"]]
    optional = [p for p in PROVIDERS if not p["required"]]

    # ── Step 1: Required providers ────────────────────────────────────────────
    console.print("\n[bold]── Step 1: Required providers ──[/]")

    for provider in required:
        key_name = provider["key"]
        current = existing.get(key_name, "")

        if current:
            console.print(
                f"  [dim]{key_name}[/] [green][{_mask_key(current)} — already set][/]"
            )
            new_val = Prompt.ask(
                "  Press Enter to keep, or type a new key",
                password=True,
                default="",
            )
            if new_val.strip():
                _write_env_key(key_name, new_val.strip())
        else:
            while True:
                val = Prompt.ask(f"  {key_name}", password=True)
                if val.strip():
                    _write_env_key(key_name, val.strip())
                    break
                console.print(f"  [red]{key_name} is required — please enter a value.[/]")

    # ── Step 2: Optional providers ────────────────────────────────────────────
    console.print("\n[bold]── Step 2: Optional providers ──[/]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, provider in enumerate(optional, 1):
        already = "[green]✓[/] " if existing.get(provider["key"]) else "  "
        table.add_row(
            f"[dim]{i}[/]",
            f"{already}[bold]{provider['name']}[/]",
            f"[dim]{provider['models']}[/]",
        )
    console.print(table)

    raw = Prompt.ask(
        "\n  Select providers to activate (comma-separated, Enter to skip)",
        default="",
    )

    if raw.strip():
        selections: list[dict] = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(optional):
                    selections.append(optional[idx])

        for provider in selections:
            key_name = provider["key"]
            current = existing.get(key_name, "")

            if current:
                console.print(
                    f"  [dim]{key_name}[/] [green][{_mask_key(current)} — already set][/]"
                )
                new_val = Prompt.ask(
                    "  Press Enter to keep, or type a new key",
                    password=True,
                    default="",
                )
                if new_val.strip():
                    _write_env_key(key_name, new_val.strip())
            else:
                val = Prompt.ask(f"  {key_name}", password=True)
                if val.strip():
                    _write_env_key(key_name, val.strip())

    console.print("\n[green]Keys saved to .env ✓[/]\n")
```

**Step 3: Lint and format**

```bash
uv run ruff format main.py && uv run ruff check main.py
```

Expected: no errors.

**Step 4: Run tests to verify nothing broke**

```bash
uv run pytest --tb=short
```

Expected: 8 PASSED

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: add PROVIDERS list and setup_providers() for onboard key collection"
```

---

### Task 5: Wire `setup_providers()` into `cmd_cto_onboard()`

**Files:**
- Modify: `main.py` — `cmd_cto_onboard()` function at line 52

**Step 1: Update `cmd_cto_onboard`**

Replace the current function body:

```python
def cmd_cto_onboard(mode: str):
    console.print("\n[bold red][CTO][/] Running founder onboarding...\n")
    output = run_claude_agent(
        "cto",
        "Run onboard: interview the founder and write ~/.cxostack/founder-profile.md",
        mode=mode,
    )
    console.print(output)
```

With:

```python
def cmd_cto_onboard(mode: str):
    console.print("\n[bold red][CTO][/] Running founder onboarding...\n")
    setup_providers()
    output = run_claude_agent(
        "cto",
        "Run onboard: interview the founder and write ~/.cxostack/founder-profile.md",
        mode=mode,
    )
    console.print(output)
```

**Step 2: Lint**

```bash
uv run ruff format main.py && uv run ruff check main.py
```

**Step 3: Run full test suite**

```bash
uv run pytest --tb=short
```

Expected: 8 PASSED

**Step 4: Manual smoke test — verify the UI renders**

```bash
python main.py
```

Then type `/cto onboard` and verify:
- Step 1 header prints
- Anthropic and GitHub key prompts appear (masked input)
- Step 2 header prints with a numbered table of 6 optional providers
- Selection prompt appears
- After selection, key prompts appear for chosen providers
- "Keys saved to .env ✓" prints
- CTO agent interview begins after

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: run setup_providers() at start of /cto onboard"
```

---

### Task 6: Update `.env.example` with all provider slots

**Files:**
- Modify: `.env.example`

**Step 1: Update `.env.example`**

Replace the current content with:

```dotenv
# cxostack environment variables
# Copy this file to .env and fill in your values.
# Never commit .env — it is gitignored.

# ── Required ────────────────────────────────────────────────────────────────

# Claude API access (powers all CTO, CMO, Architect, TL agents)
ANTHROPIC_API_KEY=

# GitHub token for PR creation and repo management via gh CLI
GITHUB_TOKEN=

# ── Optional providers ───────────────────────────────────────────────────────
# Activate during /cto onboard — keys are collected interactively.
# Only providers you configure will be used by the model router.

# OpenAI: gpt-4o, gpt-4o-mini
OPENAI_API_KEY=

# Groq: llama-3.1-8b-instant (fast, free tier — used in cheap mode)
GROQ_API_KEY=

# Mistral: mistral-large-latest
MISTRAL_API_KEY=

# Together.ai: open-source model catalog
TOGETHER_API_KEY=

# Google: gemini-1.5-pro, gemini-flash
GOOGLE_API_KEY=

# Cohere: command-r-plus
COHERE_API_KEY=

# ── Settings ─────────────────────────────────────────────────────────────────

# Default model tier: best | avg | cheap  (default: avg)
DEFAULT_MODE=avg
```

**Step 2: Run full test suite one last time**

```bash
uv run pytest --tb=short
```

Expected: 8 PASSED

**Step 3: Lint everything**

```bash
uv run ruff format . && uv run ruff check .
```

**Step 4: Commit**

```bash
git add .env.example
git commit -m "chore: update .env.example with all provider key slots"
```

---

## Summary

| Task | What it does |
|------|-------------|
| 1 | Add pytest to dev deps, create `tests/` |
| 2 | `_mask_key()` helper + tests |
| 3 | `_write_env_key()` helper + tests |
| 4 | `PROVIDERS` list + `setup_providers()` function |
| 5 | Wire `setup_providers()` into `cmd_cto_onboard()` |
| 6 | Update `.env.example` |

**Total commits:** 6
**Tests added:** 8 (covers the two pure helpers completely)
**Files changed:** `main.py`, `pyproject.toml`, `tests/__init__.py`, `tests/test_main.py`, `.env.example`

> **Note:** Secrets will be migrated from `.env` to SQLite in a future sprint. The `_write_env_key()` helper is intentionally minimal for now — the SQLite migration will replace it.
