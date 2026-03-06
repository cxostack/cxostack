# tests/test_orchestrator_dispatch.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import orchestrator
from orchestrator import dispatch


def test_dispatch_cheap_calls_groq(tmp_path):
    """cheap mode routes to groq_relay, writes output at the given line."""
    target = tmp_path / "out.py"
    target.write_text("# placeholder\n# line 2\n")

    with (
        patch("model_router.get_model", return_value="groq/llama-3.1-8b-instant"),
        patch(
            "tools.groq_relay.call_groq", return_value="def foo(): pass"
        ) as mock_groq,
        patch("orchestrator._ruff_format"),
    ):
        dispatch(
            agent="backend-developer",
            task="write foo function",
            mode="cheap",
            file=str(target),
            line=1,
        )

    mock_groq.assert_called_once()
    content = target.read_text()
    assert "def foo" in content


def test_dispatch_avg_calls_claude():
    """avg mode routes to claude subprocess with --dangerously-skip-permissions."""
    with (
        patch("model_router.get_model", return_value="claude-sonnet-4-6"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        dispatch(agent="backend-developer", task="write foo", mode="avg")

    cmd = mock_run.call_args[0][0]
    assert "claude" in cmd
    assert "--dangerously-skip-permissions" in cmd


def test_dispatch_cheap_no_file_prints_output(capsys):
    """cheap mode with no --file prints output to stdout."""
    with (
        patch("model_router.get_model", return_value="groq/llama-3.1-8b-instant"),
        patch("tools.groq_relay.call_groq", return_value="hello"),
    ):
        dispatch(agent="qa", task="write test", mode="cheap")

    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_write_at_line_invalid_line(tmp_path):
    """_write_at_line raises ValueError for line < 1."""
    import pytest

    f = tmp_path / "f.py"
    f.write_text("x\n")
    with pytest.raises(ValueError, match="line must be >= 1"):
        orchestrator._write_at_line(str(f), 0, "content")


def test_write_at_line_missing_file(tmp_path):
    """_write_at_line raises FileNotFoundError for missing file."""
    import pytest

    with pytest.raises(FileNotFoundError):
        orchestrator._write_at_line(str(tmp_path / "missing.py"), 1, "content")
