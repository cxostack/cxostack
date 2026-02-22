# Changelog

All notable changes to cxostack are documented here.

## [0.1.0] — 2025-01-01

### Added
- Sprint 1: Full CLI entry point (`main.py`) with REPL loop and all commands
- Sprint 1: `orchestrator.py` — agent lifecycle, budget tracking, session state, pause/resume skeleton
- Sprint 1: `model_router.py` — best/avg/cheap mode matrix for all 11 agent roles
- Sprint 1: `tools/ask_user.py` — terminal I/O bridge (ask, confirm, ask_choice)
- Sprint 1: `tools/file_ops.py` — file read/write, ruff format, template copy
- Sprint 1: `templates/` — blank project scaffolds (spec, RESEARCH, DECISIONS, GTM, etc.)
- Sprint 1: `memory/` — founder-profile, cto-memory, cmo-memory templates
- Sprint 2: Refined CTO agent prompt — onboard flow, memory reading, arch loop (max 3×), planner
- Sprint 2: Refined Architect agent — full 10-section architecture.md output
- Sprint 2: Refined Arch-Reviewer agent — checklist-driven review with APPROVED/NEEDS REVISION decision
- Sprint 2: CISO and SRE agent stubs
- Sprint 2: `docs/agents/` — human-readable docs for all CxO agents
- All `.claude/agents/` definitions for the full engineering team
