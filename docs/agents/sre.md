# SRE Agent

The SRE is an on-demand infrastructure agent for planning, load testing, and incident triage.

## Commands

| Command | What it does |
|---------|-------------|
| `/sre plan <project>` | Cloud infra design with cost estimates at 100/1K/10K users |
| `/sre stress <project>` | Load test against staging, finds bottlenecks |
| `/sre incident <description>` | Triage a production incident, immediate mitigation steps |

## When to use

- Before choosing a cloud provider or instance size
- After a phase deploy, before going to production
- When you see performance degradation or an outage

## Output

- `projects/{project}/INFRA.md` — infra design and cost estimates
- `projects/{project}/STRESS-REPORT.md` — load test results
- `projects/{project}/incidents/{date}-incident.md` — incident reports
