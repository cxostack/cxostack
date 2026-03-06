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
  Budget: <model>: <used>/<limit> (<pct>%) per model
  Paused: <task_id> — <reason>  (or "none")
