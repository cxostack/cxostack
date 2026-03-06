#!/usr/bin/env python3
"""CXOStack CLI — entry point. Usage: python main.py"""

import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv()
console = Console()
_ENV_PATH = Path(__file__).parent / ".env"


def _mask_key(value: str) -> str:
    """Return a masked display string for an API key."""
    if len(value) <= 8:
        return "***"
    return value[:6] + "***" + value[-2:]


def _write_env_key(key: str, value: str, env_path: Path = _ENV_PATH) -> None:
    """Write or update a key=value line in the .env file."""
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        return

    lines = env_path.read_text().splitlines(keepends=True)
    updated = False
    result = []
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            result.append(f"{key}={value}\n")
            updated = True
        else:
            result.append(line)

    if not updated:
        if result and not result[-1].endswith("\n"):
            result[-1] += "\n"
        result.append(f"{key}={value}\n")

    env_path.write_text("".join(result))


BANNER = """
[bold #a1a1a1] ██████╗ ██╗   ██╗ ██████╗  ███████╗████████╗ █████╗  ██████╗██╗  ██╗[/]
[bold #a1a1a1]██╔════╝ ╚██╗ ██╔╝██╔═══██╗ ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝[/]
[bold #a1a1a1]██║        ╚███╔╝ ██║   ██║ ███████╗   ██║   ███████║██║     █████╔╝ [/]
[bold #a1a1a1]██║        ██╔██╗ ██║   ██║ ╚════██║   ██║   ██╔══██║██║     ██╔═██╗ [/]
[bold #a1a1a1]╚██████╗ ██╔╝ ║██╗ ██████║  ███████║   ██║   ██║  ██║╚██████╗██║  ██╗[/]
[bold #a1a1a1] ╚═════╝ ╚═╝   ╚═╝ ╚════╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝[/]
"""

PROVIDERS: list[dict] = [
    # Required — always prompted
    {
        "name": "GitHub",
        "key": "GITHUB_TOKEN",
        "required": True,
        "models": "repo management via gh CLI",
    },
    # Optional — user selects
    {
        "name": "OpenAI",
        "key": "OPENAI_API_KEY",
        "required": False,
        "models": "gpt-4o, gpt-4o-mini",
    },
    {
        "name": "Groq",
        "key": "GROQ_API_KEY",
        "required": False,
        "models": "llama-3.1-8b-instant (fast, free tier)",
    },
    {
        "name": "Mistral",
        "key": "MISTRAL_API_KEY",
        "required": False,
        "models": "mistral-large-latest",
    },
    {
        "name": "Together.ai",
        "key": "TOGETHER_API_KEY",
        "required": False,
        "models": "open-source model catalog",
    },
    {
        "name": "Google",
        "key": "GOOGLE_API_KEY",
        "required": False,
        "models": "gemini-1.5-pro, gemini-flash",
    },
    {
        "name": "Cohere",
        "key": "COHERE_API_KEY",
        "required": False,
        "models": "command-r-plus",
    },
]


def _ensure_auth() -> None:
    """Verify Claude CLI and GitHub CLI are authenticated. Prompt login if not."""
    # Claude CLI
    result = subprocess.run(
        ["claude", "auth", "status"], capture_output=True, text=True
    )
    if result.returncode != 0:
        console.print(
            "[yellow]Claude CLI not logged in — launching claude auth login...[/]"
        )
        subprocess.run(["claude", "auth", "login"])
    else:
        console.print("[green]✓[/] Claude CLI authenticated")

    # GitHub CLI
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        console.print(
            "[yellow]GitHub CLI not logged in — launching gh auth login...[/]"
        )
        subprocess.run(["gh", "auth", "login"])
    else:
        console.print("[green]✓[/] GitHub CLI authenticated")


def setup_providers() -> None:
    """Interactive provider key-collection flow. Called at the start of /cto onboard."""
    from dotenv import dotenv_values
    from rich.table import Table

    _ensure_auth()
    existing = dotenv_values(_ENV_PATH)
    required = [p for p in PROVIDERS if p["required"]]
    optional = [p for p in PROVIDERS if not p["required"]]

    # ── Step 1: Required providers ────────────────────────────────────────────
    console.print("\n[bold]── Step 1: Required providers ──[/]")

    for provider in required:
        key_name = provider["key"]
        current = existing.get(key_name, "")

        if current:
            console.print(
                f"  [dim]{key_name}[/] [green][{_mask_key(current)} — already set][/]"
            )
            new_val = Prompt.ask(
                "  Press Enter to keep, or type a new key",
                password=True,
                default="",
            )
            if new_val.strip():
                _write_env_key(key_name, new_val.strip())
        else:
            while True:
                val = Prompt.ask(f"  {key_name}", password=True)
                if val.strip():
                    _write_env_key(key_name, val.strip())
                    break
                console.print(
                    f"  [red]{key_name} is required — please enter a value.[/]"
                )

    # reload after Step 1 writes to capture any updated keys
    existing = dotenv_values(_ENV_PATH)

    # ── Step 2: Optional providers ────────────────────────────────────────────
    console.print("\n[bold]── Step 2: Optional providers ──[/]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, provider in enumerate(optional, 1):
        already = "[green]✓[/] " if existing.get(provider["key"]) else "  "
        table.add_row(
            f"[dim]{i}[/]",
            f"{already}[bold]{provider['name']}[/]",
            f"[dim]{provider['models']}[/]",
        )
    console.print(table)

    raw = Prompt.ask(
        "\n  Select providers to activate (comma-separated, Enter to skip)",
        default="",
    )

    if raw.strip():
        selections: list[dict] = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(optional):
                    selections.append(optional[idx])

        for provider in selections:
            key_name = provider["key"]
            current = existing.get(key_name, "")

            if current:
                console.print(
                    f"  [dim]{key_name}[/] [green][{_mask_key(current)} — already set][/]"
                )
                new_val = Prompt.ask(
                    "  Press Enter to keep, or type a new key",
                    password=True,
                    default="",
                )
                if new_val.strip():
                    _write_env_key(key_name, new_val.strip())
            else:
                val = Prompt.ask(f"  {key_name}", password=True)
                if val.strip():
                    _write_env_key(key_name, val.strip())

    console.print("\n[green]Keys saved to .env ✓[/]\n")


def run_claude_agent(agent_name: str, prompt: str, mode: str = "avg") -> str:
    model_map = {
        "best": "claude-opus-4-6",
        "avg": "claude-sonnet-4-6",
        "cheap": "claude-haiku-4-5-20251001",
    }
    model = model_map.get(mode, "claude-sonnet-4-6")
    result = subprocess.run(
        ["claude", "--agent", agent_name, "--model", model, "-p", prompt],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.returncode != 0:
        console.print(f"[red]Agent {agent_name} error:[/] {result.stdout}")
        return ""
    return result.stdout.strip()


def cmd_cto(idea: str, mode: str = "avg"):
    console.print(f"\n[bold red][CTO][/] Starting project: [italic]{idea}[/]\n")
    output = run_claude_agent("cto", f"New project idea: {idea}", mode=mode)
    console.print(output)


_ONBOARD_QUESTIONS = [
    "What's your name, and what's your background? (industry, previous roles, how technical are you?)",
    "What are you building, or what's the product you're working on now?",
    "What tech stack do you prefer? Any languages, frameworks, or cloud providers you want to stick with — or avoid?",
    "How do you like to work? Fast rough drafts you iterate on, or thorough output the first time?",
    "Anything else I should know before I start working for you?",
]


def cmd_cto_onboard(mode: str):
    console.print("\n[bold red][CTO][/] Running founder onboarding...\n")
    setup_providers()

    answers: list[str] = []
    total = len(_ONBOARD_QUESTIONS)
    for i, question in enumerate(_ONBOARD_QUESTIONS, 1):
        console.print(f"\n[bold]Question {i} of {total}[/]")
        console.print(question)
        answer = Prompt.ask("  You")
        answers.append(answer)
        if i < total:
            console.print("[dim]Got it.[/]")

    transcript = "\n".join(
        f"Q{i}: {q}\nA{i}: {a}"
        for i, (q, a) in enumerate(zip(_ONBOARD_QUESTIONS, answers), 1)
    )
    prompt = (
        "A founder onboarding interview just completed. "
        "Using memory/founder-profile.template.md as structure, write ~/.cxostack/founder-profile.md. "
        "Using memory/cto-memory.template.md as structure, write ~/.cxostack/cto-memory.md "
        "(fill in stack preferences from the answers). "
        "Create ~/.cxostack/ if it does not exist.\n\n"
        f"Interview transcript:\n{transcript}"
    )
    output = run_claude_agent("cto", prompt, mode=mode)
    console.print(output)
    console.print(
        '\n[green]Profile saved. You\'re ready.[/] Try: [bold]/cto "your project idea"[/]'
    )


def cmd_cto_continue(phase: str, mode: str):
    console.print(f"\n[bold red][CTO][/] Continuing phase-{phase}...\n")
    output = run_claude_agent(
        "cto",
        f"Continue phase-{phase}: spawn team-leader for this phase. Read projects/ for context.",
        mode=mode,
    )
    console.print(output)


def cmd_cto_status():
    console.print("\n[bold red][CTO][/] Fetching project status...\n")
    output = run_claude_agent(
        "cto",
        "Report current project status from state/session.json",
        mode="avg",
    )
    console.print(output)


def cmd_cmo(project: str, mode: str):
    console.print(
        f"\n[bold #a1a1a1][CMO][/] Building GTM strategy for: [italic]{project}[/]\n"
    )
    output = run_claude_agent("cmo", f"GTM strategy for project: {project}", mode=mode)
    console.print(output)


def cmd_tl_review(pr_url: str, mode: str):
    console.print(f"\n[bold purple][TL][/] Reviewing PR: {pr_url}\n")
    output = run_claude_agent(
        "team-leader",
        f"Review this PR: {pr_url}. Load the usecase.md from the PR description for context.",
        mode=mode,
    )
    console.print(output)


def cmd_status():
    try:
        budget = json.loads(Path("state/budget.json").read_text())
        session = json.loads(Path("state/session.json").read_text())
        paused = json.loads(Path("state/paused_tasks.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as exc:
        console.print(f"[white]Warning: could not read state — {exc}[/]")
        return

    console.print("\n[bold]── Budget ──[/]")
    for model, data in budget.items():
        used = data.get("used", 0)
        limit = data.get("limit", 0)
        pct = (used / limit * 100) if limit else 0
        console.print(f"  {model}: {used:,} / {limit:,} ({pct:.1f}%)")

    console.print("\n[bold]── Session ──[/]")
    console.print(f"  Phase: {session.get('phase', 'none')}")
    console.print(f"  Mode:  {session.get('mode', 'avg')}")

    console.print("\n[bold]── Paused Tasks ──[/]")
    if paused:
        for t in paused:
            console.print(f"  {t['task_id']} — {t['reason']}")
    else:
        console.print("  (none)")


def cmd_skills(args: list):
    skills_path = Path(__file__).parent / "skills.sh"
    result = subprocess.run([str(skills_path)] + args, cwd=Path(__file__).parent)
    if result.returncode != 0:
        console.print(f"[red]skills.sh failed with exit code {result.returncode}[/]")


def _cli_mode() -> None:
    """Handle CLI invocation: python main.py [--mode best|avg|cheap] <command> [args]"""
    import argparse

    parser = argparse.ArgumentParser(prog="cxostack")
    parser.add_argument(
        "--mode",
        default=os.getenv("DEFAULT_MODE", "avg"),
        choices=["best", "avg", "cheap"],
    )
    subparsers = parser.add_subparsers(dest="command")

    cto_p = subparsers.add_parser("cto")
    cto_sub = cto_p.add_subparsers(dest="cto_command")
    cto_idea_p = cto_sub.add_parser("idea")
    cto_idea_p.add_argument("text")
    cto_sub.add_parser("onboard")
    cto_sub.add_parser("status")
    cto_continue_p = cto_sub.add_parser("continue")
    cto_continue_p.add_argument("phase")

    cmo_p = subparsers.add_parser("cmo")
    cmo_p.add_argument("project")

    subparsers.add_parser("status")

    args = parser.parse_args()

    if args.command == "cto":
        cto_cmd = getattr(args, "cto_command", None)
        if cto_cmd == "idea":
            cmd_cto(args.text, args.mode)
        elif cto_cmd == "onboard":
            cmd_cto_onboard(args.mode)
        elif cto_cmd == "continue":
            cmd_cto_continue(args.phase, args.mode)
        elif cto_cmd == "status":
            cmd_cto_status()
        else:
            console.print(
                "[red]Usage:[/] cxostack cto <idea <text>|onboard|continue <phase>|status>"
            )

    elif args.command == "cmo":
        cmd_cmo(args.project, args.mode)

    elif args.command == "status":
        cmd_status()

    else:
        parser.print_help()


def main():
    console.print(BANNER)
    console.print("[dim]Type /cto <idea> to start · /help for commands[/]\n")

    mode = os.getenv("DEFAULT_MODE", "avg")

    while True:
        try:
            raw = Prompt.ask("[bold #a1a1a1]cxostack>[/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye.[/]")
            break

        if not raw:
            continue
        parts = raw.split(" ", 1)
        cmd = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if cmd == "/cto":
            if rest.startswith("onboard"):
                cmd_cto_onboard(mode)
            elif rest.startswith("continue"):
                tokens = rest.split()
                if len(tokens) < 2:
                    console.print("[red]Usage:[/] /cto continue <phase>")
                else:
                    cmd_cto_continue(tokens[1], mode)
            elif rest == "status":
                cmd_cto_status()
            elif not rest:
                console.print("[red]Usage:[/] /cto <idea> [--mode best|avg|cheap]")
            else:
                idea, _, m = rest.partition("--mode")
                mode_override = m.strip() if m.strip() else None
                cmd_cto(idea.strip(), mode_override or mode)

        elif cmd == "/cmo":
            if rest:
                cmd_cmo(rest, mode)
            else:
                console.print("[red]Usage:[/] /cmo <project>")

        elif cmd == "/ciso":
            console.print(
                "[white]CISO agent: coming in a future sprint. See docs/agents/ciso.md[/]"
            )

        elif cmd == "/sre":
            console.print(
                "[white]SRE agent: coming in a future sprint. See docs/agents/sre.md[/]"
            )

        elif cmd == "/tl":
            if "review pr:" in rest:
                url = rest.split("pr:")[1].strip()
                if not url.startswith("https://github.com/"):
                    console.print(
                        "[red]Error:[/] URL must be a GitHub PR URL (https://github.com/...)"
                    )
                else:
                    cmd_tl_review(url, mode)
            else:
                console.print("[red]Usage:[/] /tl review pr: <url>")

        elif cmd == "/status":
            cmd_status()

        elif cmd == "/resume":
            console.print("[white]Resuming paused tasks...[/]")
            output = run_claude_agent(
                "cto",
                "Resume all paused tasks from state/paused_tasks.json",
                mode=mode,
            )
            console.print(output)

        elif cmd == "/budget":
            cmd_status()

        elif cmd == "/skills":
            cmd_skills(rest.split() if rest else ["list"])

        elif cmd == "/mode":
            if rest in ("best", "avg", "cheap"):
                mode = rest
                console.print(f"[white]Mode set to:[/] {mode}")
            else:
                console.print("[red]Usage:[/] /mode best|avg|cheap")

        elif cmd == "/help":
            console.print(
                """
[bold]Commands:[/]
  /cto <idea> [--mode best|avg|cheap]   Start new project pipeline
  /cto onboard                          Interview the founder and write profile
  /cto continue <phase>                 Resume a specific phase (e.g. phase-2)
  /cto status                           Report current project status
  /cmo <project>                        Generate GTM strategy for a project
  /ciso                                 CISO agent (coming soon)
  /sre                                  SRE agent (coming soon)
  /tl review pr: <url>                  Review a PR
  /status                               Show phase, budget, paused tasks
  /resume                               Retry paused tasks
  /budget                               Show token usage per model
  /skills list                          Show installed skills
  /skills search <query>                Find a skill
  /mode best|avg|cheap                  Switch model tier
  /help                                 This message
            """
            )

        else:
            console.print(f"[red]Unknown command:[/] {cmd} — try /help")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        _cli_mode()
    else:
        main()
