#!/usr/bin/env python3
"""CXOStack file operations — read, write, ruff-format, and template copying."""

import subprocess
import shutil
from pathlib import Path

# Templates directory relative to this file's parent (project root)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def read_file(path: str | Path) -> str:
    """Read and return the contents of a file as a string.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: With a helpful message if the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"File not found: {p}\n"
            f"  Tip: check that the project directory was initialised correctly."
        )
    return p.read_text(encoding="utf-8")


def write_file(path: str | Path, content: str, mkdir: bool = True) -> None:
    """Write content to a file, optionally creating parent directories.

    Args:
        path: Destination file path.
        content: String content to write.
        mkdir: If True (default), create parent directories as needed.
    """
    p = Path(path)
    if mkdir:
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def ruff_format(path: str | Path) -> bool:
    """Run `ruff format` on a Python file.

    Args:
        path: Path to the .py file to format.

    Returns:
        True if ruff exited with code 0, False otherwise.
    """
    result = subprocess.run(
        ["ruff", "format", str(path)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def copy_template(template_name: str, dest_path: str | Path) -> None:
    """Copy a blank template from templates/ to the destination path.

    Args:
        template_name: Filename inside the templates/ directory (e.g. "spec.md").
        dest_path: Destination path where the template copy will be written.

    Raises:
        FileNotFoundError: If the template does not exist in templates/.
    """
    src = TEMPLATES_DIR / template_name
    if not src.exists():
        raise FileNotFoundError(
            f"Template not found: {src}\n"
            f"  Available templates: {[f.name for f in TEMPLATES_DIR.iterdir()] if TEMPLATES_DIR.exists() else '(templates/ dir missing)'}"
        )
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
