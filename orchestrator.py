#!/usr/bin/env python3
"""CXOStack Orchestrator — agent lifecycle, budget tracking, session state, pause/resume."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console

console = Console()

STATE_DIR = Path(__file__).parent / "state"
BUDGET_FILE = STATE_DIR / "budget.json"
SESSION_FILE = STATE_DIR / "session.json"
PAUSED_FILE = STATE_DIR / "paused_tasks.json"


class Orchestrator:
    """Manages agent invocation, token budgets, session state, and pause/resume."""

    def run_agent(self, agent_name: str, prompt: str, mode: str = "avg") -> str:
        """Spawn a Claude Code subagent and return its stdout output.

        Args:
            agent_name: Name of the .claude/agents/ definition to invoke.
            prompt: The prompt to pass to the agent via -p flag.
            mode: Model tier — "best", "avg", or "cheap".

        Returns:
            Agent stdout as string, or empty string on error.
        """
        from model_router import get_model

        model = get_model(agent_name, mode)
        result = subprocess.run(
            [
                "claude",
                "--agent",
                agent_name,
                "--model",
                model,
                "--print",
                "-p",
                prompt,
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.returncode != 0:
            console.print(f"[red]Agent {agent_name} error:[/] {result.stderr}")
            return ""
        return result.stdout.strip()

    def track_budget(self, model: str, tokens_used: int) -> None:
        """Add tokens_used to the running total for model in state/budget.json.

        Args:
            model: Model ID string (e.g. "claude-sonnet-4-6").
            tokens_used: Number of tokens consumed in this invocation.
        """
        try:
            budget = json.loads(BUDGET_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            budget = {}

        if model not in budget:
            budget[model] = {"limit": 0, "used": 0}
        budget[model]["used"] = budget[model].get("used", 0) + tokens_used

        BUDGET_FILE.write_text(json.dumps(budget, indent=2))

    def get_session(self) -> dict:
        """Read and return state/session.json as a dict. Returns {} on error."""
        try:
            return json.loads(SESSION_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def update_session(self, updates: dict) -> None:
        """Patch state/session.json with the provided key-value pairs.

        Args:
            updates: Dict of keys to set/update in session.json.
        """
        session = self.get_session()
        session.update(updates)
        SESSION_FILE.write_text(json.dumps(session, indent=2))

    def pause_task(self, task_id: str, context: dict, reason: str) -> None:
        """Append a task to state/paused_tasks.json for later resumption.

        Args:
            task_id: Unique identifier for the task (e.g. "cto-arch-loop-phase-1").
            context: Dict of context needed to resume (agent, prompt, mode, etc.).
            reason: Human-readable reason for pausing (e.g. "budget exhausted").

        Note: Full implementation in Sprint 6.
        """
        try:
            paused = json.loads(PAUSED_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            paused = []

        paused.append(
            {
                "task_id": task_id,
                "reason": reason,
                "context": context,
                "paused_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        PAUSED_FILE.write_text(json.dumps(paused, indent=2))

    def resume_all(self) -> list[dict]:
        """Return all paused tasks and clear state/paused_tasks.json.

        Returns:
            List of paused task dicts (each has task_id, reason, context, paused_at).

        Note: Full retry execution in Sprint 6. Currently returns the list for
        the caller to handle.
        """
        try:
            paused = json.loads(PAUSED_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        PAUSED_FILE.write_text("[]")
        return paused
