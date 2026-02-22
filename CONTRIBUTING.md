# Contributing to cxostack

Thank you for contributing. There are three clean ways to help:

## 1. New CxO agent

Add a peer to CTO, CMO, CISO, or SRE (e.g. CPO, CFO, COO, CLO).

**Steps:**
1. Open an issue using the `new_cxo_agent.md` template
2. Create `.claude/agents/{cxo}.md` with frontmatter + full prompt
3. Create `docs/agents/{cxo}.md` with human-readable explanation
4. Add memory template to `memory/{cxo}-memory.template.md`
5. Add the command to `main.py`
6. Submit PR with the issue linked

## 2. Agent improvement

Improve an existing agent's prompt for better output quality.

**Steps:**
1. Open an issue using the `agent_improvement.md` template — describe current behaviour vs. desired behaviour with an example
2. Edit `.claude/agents/{agent}.md`
3. Test with a real invocation and include the output in your PR

**Rules:**
- One improvement per PR
- Include before/after output examples
- Don't change an agent's fundamental scope — that's a new issue

## 3. New skill

Add a skill that benefits all cxostack users.

**Steps:**
1. Create the skill in `skills/` directory
2. Test it manually in a real project
3. Optionally publish to [skills.sh](https://skills.sh) for the wider community
4. Submit PR with the skill directory included

## What not to contribute (yet)

Core Python (`main.py`, `orchestrator.py`, `tools/`) is maintainer territory
while the project is in early development. Open an issue first if you have ideas here.

## Code standards

- Python 3.12+, formatted with `ruff format`, linted with `ruff check`
- Agent `.md` files use the Claude Code frontmatter format
- No real project data, API keys, or personal information in any committed file

## Questions?

Open an issue or start a discussion.
