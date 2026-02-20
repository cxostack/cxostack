#!/usr/bin/env python3
"""
CXOStack CLI — entry point
Usage: python main.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path
# from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# load_dotenv()
console = Console()

BANNER = """
[bold red] ██████╗[/][bold yellow]██╗  ██╗[/][bold green] ██████╗ [/][bold blue]███████╗[/][bold magenta]████████╗[/][bold cyan] █████╗ [/][bold white] ██████╗██╗  ██╗[/]
[bold red]██╔════╝[/][bold yellow]╚██╗██╔╝[/][bold green]██╔═══██╗[/][bold blue]██╔════╝[/][bold magenta]╚══██╔══╝[/][bold cyan]██╔══██╗[/][bold white]██╔════╝██║ ██╔╝[/]
[bold red]██║      [/][bold yellow] ╚███╔╝ [/][bold green]██║   ██║[/][bold blue]███████╗[/][bold magenta]   ██║   [/][bold cyan]███████║[/][bold white]██║     █████╔╝ [/]
[bold red]██║      [/][bold yellow] ██╔██╗ [/][bold green]██║   ██║[/][bold blue]╚════██║[/][bold magenta]   ██║   [/][bold cyan]██╔══██║[/][bold white]██║     ██╔═██╗ [/]
[bold red]╚██████╗[/][bold yellow]██╔╝ ██╗[/][bold green]╚██████╔╝[/][bold blue]███████║[/][bold magenta]   ██║   [/][bold cyan]██║  ██║[/][bold white]╚██████╗██║  ██╗[/]
[bold red] ╚═════╝[/][bold yellow]╚═╝  ╚═╝[/][bold green] ╚═════╝ [/][bold blue]╚══════╝[/][bold magenta]   ╚═╝   [/][bold cyan]╚═╝  ╚═╝[/][bold white] ╚═════╝╚═╝  ╚═╝[/]
"""

# def run_claude_agent(agent_name: str, prompt: str, mode: str = "avg") -> str:
#     """Spawn a CC subagent and return its output."""
#     model_map = {
#         "best": "claude-sonnet-4-6",
#         "avg":  "claude-haiku-4-5",
#         "cheap": "claude-haiku-4-5",
#     }
#     model = model_map.get(mode, "claude-haiku-4-5")

#     result = subprocess.run(
#         ["claude", "--agent", agent_name, "--model", model, "--print", "-p", prompt],
#         capture_output=True,
#         text=True,
#         cwd=Path.cwd()
#     )
#     if result.returncode != 0:
#         console.print(f"[red]Agent {agent_name} error:[/] {result.stderr}")
#         return ""
#     return result.stdout.strip()


# def cmd_cto(idea: str, mode: str = "avg"):
#     console.print(f"\n[bold red][CTO][/] Starting project: [italic]{idea}[/]\n")
#     output = run_claude_agent("cto", f"New project idea: {idea}", mode=mode)
#     console.print(output)


# def cmd_tl_review(pr_url: str, mode: str = "avg"):
#     console.print(f"\n[bold purple][TL][/] Reviewing PR: {pr_url}\n")
#     prompt = f"Review this PR: {pr_url}. Load the usecase.md from the PR description for context."
#     output = run_claude_agent("team-leader", prompt, mode=mode)
#     console.print(output)


# def cmd_status():
#     budget = json.loads(Path("state/budget.json").read_text())
#     session = json.loads(Path("state/session.json").read_text())
#     paused = json.loads(Path("state/paused_tasks.json").read_text())

#     console.print("\n[bold]── Budget ──[/]")
#     for model, data in budget.items():
#         pct = (data["used"] / data["limit"] * 100) if data["limit"] else 0
#         console.print(f"  {model}: {data['used']:,} / {data['limit']:,} ({pct:.1f}%)")

#     console.print(f"\n[bold]── Session ──[/]")
#     console.print(f"  Phase: {session.get('phase', 'none')}")
#     console.print(f"  Mode:  {session.get('mode', 'avg')}")

#     console.print(f"\n[bold]── Paused Tasks ──[/]")
#     if paused:
#         for t in paused:
#             console.print(f"  {t['task_id']} — {t['reason']}")
#     else:
#         console.print("  (none)")


# def cmd_skills(args: list):
#     sub = args[0] if args else "list"
#     query = args[1] if len(args) > 1 else ""
#     subprocess.run(["./skills.sh", sub, query])


def main():
    console.print(BANNER)
    console.print("[dim]Type /cto <idea> to start · /help for commands[/]\n")

    mode = os.getenv("DEFAULT_MODE", "avg")

#     while True:
#         try:
#             raw = Prompt.ask("[bold green]cxostack>[/]").strip()
#         except (KeyboardInterrupt, EOFError):
#             console.print("\n[dim]Bye.[/]")
#             break

#         if not raw:
#             continue

#         parts = raw.split(" ", 1)
#         cmd = parts[0]
#         rest = parts[1] if len(parts) > 1 else ""

#         if cmd == "/cto":
#             if not rest:
#                 console.print("[red]Usage:[/] /cto <idea> [--mode best|avg|cheap]")
#                 continue
#             # parse optional --mode flag
#             if "--mode" in rest:
#                 idea, _, m = rest.partition("--mode")
#                 mode = m.strip()
#                 idea = idea.strip()
#             else:
#                 idea = rest
#             cmd_cto(idea, mode)

#         elif cmd == "/tl":
#             if "review pr:" in rest:
#                 url = rest.split("pr:")[1].strip()
#                 cmd_tl_review(url, mode)
#             else:
#                 console.print("[red]Usage:[/] /tl review pr: <url>")

#         elif cmd == "/status":
#             cmd_status()

#         elif cmd == "/resume":
#             console.print("[yellow]Resuming paused tasks...[/]")
#             output = run_claude_agent("cto", "Resume all paused tasks from state/paused_tasks.json", mode=mode)
#             console.print(output)

#         elif cmd == "/budget":
#             cmd_status()

#         elif cmd == "/skills":
#             cmd_skills(rest.split())

#         elif cmd == "/mode":
#             if rest in ("best", "avg", "cheap"):
#                 mode = rest
#                 console.print(f"[green]Mode set to:[/] {mode}")
#             else:
#                 console.print("[red]Usage:[/] /mode best|avg|cheap")

#         elif cmd == "/help":
#             console.print("""
# [bold]Commands:[/]
#   /cto <idea> [--mode best|avg|cheap]   Start new project pipeline
#   /cto continue phase-N                 Resume next phase
#   /tl review pr: <url>                  Review a PR
#   /status                               Show phase, budget, paused tasks
#   /resume                               Retry paused tasks
#   /budget                               Show token usage per model
#   /skills list                          Show installed skills
#   /skills search <query>                Find a skill
#   /mode best|avg|cheap                  Switch model tier
#   /help                                 This message
#             """)

#         else:
#             console.print(f"[red]Unknown command:[/] {cmd} — try /help")


if __name__ == "__main__":
    main()
