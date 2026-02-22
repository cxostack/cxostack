#!/usr/bin/env python3
"""CXOStack Model Router — maps agent roles to model IDs by mode tier."""

# Model tier matrix: role → mode → model ID
# Matches CLAUDE.md specification.
ROLE_MATRIX: dict[str, dict[str, str]] = {
    # CxO agents — Opus for best, Sonnet for avg/cheap
    "cto": {
        "best": "claude-opus-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-sonnet-4-6",
    },
    "cmo": {
        "best": "claude-opus-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-sonnet-4-6",
    },
    "architect": {
        "best": "claude-opus-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-sonnet-4-6",
    },
    # Mid-tier: Sonnet for best/avg, Haiku for cheap
    "team-leader": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-haiku-4-5-20251001",
    },
    "planner": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-haiku-4-5-20251001",
    },
    "arch-reviewer": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-haiku-4-5-20251001",
    },
    "code-reviewer": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-haiku-4-5-20251001",
    },
    # Dev agents: Sonnet for best, Haiku for avg, Groq for cheap
    "backend-developer": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-haiku-4-5-20251001",
        "cheap": "groq/llama-3.1-8b-instant",
    },
    "frontend-developer": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-haiku-4-5-20251001",
        "cheap": "groq/llama-3.1-8b-instant",
    },
    "qa": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-haiku-4-5-20251001",
        "cheap": "groq/llama-3.1-8b-instant",
    },
    "devops": {
        "best": "claude-sonnet-4-6",
        "avg": "claude-haiku-4-5-20251001",
        "cheap": "groq/llama-3.1-8b-instant",
    },
}

_DEFAULT_MODELS: dict[str, str] = {
    "best": "claude-opus-4-6",
    "avg": "claude-sonnet-4-6",
    "cheap": "claude-haiku-4-5-20251001",
}


def get_model(agent_role: str, mode: str = "avg") -> str:
    """Return the model ID for agent_role at the given mode tier.

    Args:
        agent_role: Agent name matching a key in ROLE_MATRIX (e.g. "cto", "qa").
        mode: Tier — "best", "avg", or "cheap". Defaults to "avg".

    Returns:
        Model ID string. Falls back to _DEFAULT_MODELS[mode] if role is unknown,
        then to "claude-sonnet-4-6" if mode is also unknown.

    Examples:
        >>> get_model("cto", "best")
        'claude-opus-4-6'
        >>> get_model("qa", "cheap")
        'groq/llama-3.1-8b-instant'
        >>> get_model("unknown-agent", "avg")
        'claude-sonnet-4-6'
    """
    role_entry = ROLE_MATRIX.get(agent_role, {})
    return role_entry.get(mode) or _DEFAULT_MODELS.get(mode, "claude-sonnet-4-6")
