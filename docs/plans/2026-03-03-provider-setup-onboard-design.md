# Design: Provider Setup During `/cto onboard`

**Date:** 2026-03-03
**Status:** Approved
**Scope:** `main.py` only — onboard key-collection flow. Routing changes (model_router.py) are a separate task. Secrets backend (SQLite) is a future task.

---

## Problem

`/cto onboard` currently delegates immediately to the CTO agent without verifying which AI providers the user wants to use or collecting their API keys. Keys must be manually edited in `.env` before first use.

---
``
## Solution

Add a `setup_providers()` function in `main.py` that runs at the start of `cmd_cto_onboard`. It collects required and optional provider keys interactively and writes them to `.env`.

---

## Provider List

| # | Provider    | Env var              | Required | Models                           |
|---|-------------|----------------------|----------|----------------------------------|
| — | Anthropic   | `ANTHROPIC_API_KEY`  | Yes      | claude-opus-4-6, sonnet, haiku   |
| — | GitHub      | `GITHUB_TOKEN`       | Yes      | (repo management via gh CLI)     |
| 1 | OpenAI      | `OPENAI_API_KEY`     | Optional | gpt-4o, gpt-4o-mini              |
| 2 | Groq        | `GROQ_API_KEY`       | Optional | llama-3.1-8b-instant (free tier) |
| 3 | Mistral     | `MISTRAL_API_KEY`    | Optional | mistral-large-latest             |
| 4 | Together.ai | `TOGETHER_API_KEY`   | Optional | Open-source model catalog        |
| 5 | Google      | `GOOGLE_API_KEY`     | Optional | gemini-1.5-pro, gemini-flash     |
| 6 | Cohere      | `COHERE_API_KEY`     | Optional | command-r-plus                   |

---

## UX Flow

```
── Step 1: Required providers ──────────────────────────
  ANTHROPIC_API_KEY [sk-ant-***already set***] (Enter to keep):
  GITHUB_TOKEN: ●●●●●●●●

── Step 2: Optional providers ──────────────────────────
  1  OpenAI       GPT-4o, GPT-4o-mini
  2  Groq         Llama-3.1-8b-instant (fast, free tier)
  3  Mistral      mistral-large-latest
  4  Together.ai  Open-source model catalog
  5  Google       gemini-1.5-pro
  6  Cohere       command-r-plus

  Select providers to activate (comma-separated, Enter to skip): 2,5

  GROQ_API_KEY: ●●●●●●●●
  GOOGLE_API_KEY: ●●●●●●●●

Keys saved to .env ✓
```

---

## Implementation Details

### Data structure

```python
PROVIDERS = [
    # Required
    {"name": "Anthropic", "key": "ANTHROPIC_API_KEY", "required": True,
     "models": "claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5"},
    {"name": "GitHub",    "key": "GITHUB_TOKEN",      "required": True,
     "models": "repo management via gh CLI"},
    # Optional
    {"name": "OpenAI",      "key": "OPENAI_API_KEY",   "required": False, "models": "gpt-4o, gpt-4o-mini"},
    {"name": "Groq",        "key": "GROQ_API_KEY",      "required": False, "models": "llama-3.1-8b-instant"},
    {"name": "Mistral",     "key": "MISTRAL_API_KEY",   "required": False, "models": "mistral-large-latest"},
    {"name": "Together.ai", "key": "TOGETHER_API_KEY",  "required": False, "models": "open-source catalog"},
    {"name": "Google",      "key": "GOOGLE_API_KEY",    "required": False, "models": "gemini-1.5-pro"},
    {"name": "Cohere",      "key": "COHERE_API_KEY",    "required": False, "models": "command-r-plus"},
]
```

### Key masking for existing values

```python
def _mask_key(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return value[:6] + "***" + value[-2:]
```

### Reading/writing `.env`

- Read current `.env` with `python-dotenv`'s `dotenv_values()` to get existing values
- After collection, update `.env` file by reading lines and replacing/appending key=value pairs
- Never overwrite keys the user chose to skip (pressed Enter on existing)

### Input collection

- Use `Rich`'s `Prompt.ask(password=True)` for masked input (no extra deps)
- Empty input on an already-set key = keep existing value
- Empty input on a new required key = re-prompt with error

### `.env.example` update

Add all 8 key slots (Anthropic + GitHub already there; add 6 optional ones with comments).

---

## Files Changed

| File | Change |
|------|--------|
| `main.py` | Add `PROVIDERS` list, `_mask_key()`, `_write_env_key()`, `setup_providers()`, update `cmd_cto_onboard()` |
| `.env.example` | Add optional provider key slots with comments |

---

## Future

- Secrets will be migrated to SQLite (instead of `.env`) in a later sprint.
- `model_router.py` will be updated separately to use the role→provider mapping configured here.
