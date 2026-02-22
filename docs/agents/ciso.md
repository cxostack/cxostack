# CISO Agent

The CISO is an on-demand security agent. It is never invoked automatically — only when the founder asks for a security review or red team exercise.

## Commands

| Command | What it does |
|---------|-------------|
| `/ciso audit <project>` | OWASP Top 10 audit of a deployed project |
| `/ciso attack <project>` | Active red team against your staging environment |

## When to use

- After deploying a new phase to staging or production
- Before a public launch
- After any significant change to auth or data handling
- Periodically as a health check

## Output

- `projects/{project}/SECURITY.md` — findings with severity, reproduction steps, and fixes

## Important

The CISO only audits or attacks systems you own. It will always confirm before running active tests.
