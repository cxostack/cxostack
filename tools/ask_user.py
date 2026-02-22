#!/usr/bin/env python3
"""CXOStack terminal I/O bridge — functions agents use to interact with the founder."""

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def ask(question: str, default: str = "") -> str:
    """Print a styled question and return the founder's text input.

    Args:
        question: The question to display. Displayed in bold cyan.
        default: Default value shown in the prompt (empty string = no default).

    Returns:
        The founder's input as a stripped string.
    """
    return Prompt.ask(f"[bold cyan]{question}[/]", default=default).strip()


def confirm(question: str, default: bool = True) -> bool:
    """Display a yes/no prompt and return the boolean result.

    Args:
        question: The question to display. Displayed in bold yellow.
        default: Default selection shown if the founder presses Enter (True = yes).

    Returns:
        True if the founder answers yes, False otherwise.
    """
    return Confirm.ask(f"[bold yellow]{question}[/]", default=default)


def ask_choice(question: str, choices: list[str]) -> str:
    """Display a numbered list of choices and return the selected item.

    Args:
        question: The question to display above the choices.
        choices: List of option strings to present (1-indexed for display).

    Returns:
        The selected choice string (not the number).

    Raises:
        ValueError: If choices is empty.
    """
    if not choices:
        raise ValueError("ask_choice requires at least one choice")

    console.print(f"\n[bold cyan]{question}[/]")
    for i, choice in enumerate(choices, start=1):
        console.print(f"  [bold]{i}.[/] {choice}")

    while True:
        raw = Prompt.ask(
            f"[dim]Enter number (1–{len(choices)})[/]",
            default="1",
        ).strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        console.print(f"[red]Please enter a number between 1 and {len(choices)}[/]")
