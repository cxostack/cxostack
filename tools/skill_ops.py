"""tools/skill_ops.py — thin subprocess wrapper around skills.sh."""

import subprocess
from pathlib import Path

_SKILLS_SH = Path(__file__).parent.parent / "skills.sh"


def _run(*args: str) -> str:
    result = subprocess.run(
        [str(_SKILLS_SH), *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def search(query: str) -> str:
    """Search installed skills matching query. Returns multi-line string."""
    return _run("search", query)


def install(name: str, scope: str = "user") -> bool:
    """Install a skill by name. scope is 'user' or 'project'. Returns True on success."""
    result = subprocess.run(
        [str(_SKILLS_SH), "install", name, scope],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def list_installed() -> str:
    """List all installed user and project skills. Returns multi-line string."""
    return _run("list")
