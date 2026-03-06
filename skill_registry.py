"""skill_registry.py — TL skill lookup and missing-skill logger."""

import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "skill-registry.json"


def _load() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"known_skills": [], "agent_skills": {}, "missing_log": []}


def _save(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2))


def get_skills(agent_role: str) -> list[str]:
    """Return list of skill names assigned to agent_role."""
    return _load()["agent_skills"].get(agent_role, [])


def log_missing(agent_role: str, skill_name: str) -> None:
    """Append a missing-skill entry to missing_log."""
    data = _load()
    data["missing_log"].append({"agent": agent_role, "skill": skill_name})
    _save(data)
