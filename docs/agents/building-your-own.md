# Building Your Own CxO Agent

cxostack is designed to be extended. Adding a new CxO agent (CPO, CFO, COO, CLO, etc.) is straightforward.

## What a CxO agent needs

1. **Agent definition** — `.claude/agents/{cxo}.md` with frontmatter and full prompt
2. **Human docs** — `docs/agents/{cxo}.md` explaining what it does and when to use it
3. **Memory template** — `memory/{cxo}-memory.template.md` for the agent's persistent memory
4. **CLI command** — add the `/cxo` handler to `main.py`

## Agent frontmatter

```yaml
---
name: cpo
description: Chief Product Officer. [One sentence: what it does and when to invoke it.]
model: claude-sonnet-4-6
tools: Read, Write, Edit, Bash, Task
color: purple
---
```

## Prompt structure

Follow the pattern from existing agents:
1. **Session start protocol** — read founder-profile.md and your memory file
2. **Commands** — each slash command with step-by-step instructions
3. **Output format** — exactly what files get written and with what structure
4. **Memory updates** — when and what to update
5. **Rules** — behavioral constraints

## Before submitting

- Open a GitHub issue using the `new_cxo_agent.md` template first
- Test your agent with a real invocation and include the output in your PR
- Make sure it doesn't overlap with an existing agent's scope
- Keep it focused: one CxO, one domain
