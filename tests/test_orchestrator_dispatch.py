# tests/test_orchestrator_dispatch.py
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_dispatch_cheap_calls_groq(tmp_path):
    """cheap mode routes to groq_relay, not claude."""
    target = tmp_path / "out.py"
    target.write_text("# placeholder\n")

    with patch("orchestrator.call_groq", return_value="def foo(): pass"):
        from orchestrator import dispatch
        dispatch(
            agent="backend-developer",
            task="write foo function",
            mode="cheap",
            file=str(target),
            line=1,
        )

    assert "def foo(): pass" in target.read_text()


def test_dispatch_avg_calls_claude():
    """avg mode routes to claude subprocess with --dangerously-skip-permissions."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        from orchestrator import dispatch
        dispatch(agent="backend-developer", task="write foo", mode="avg")

    cmd = mock_run.call_args[0][0]
    assert "claude" in cmd
    assert "--dangerously-skip-permissions" in cmd


def test_dispatch_cheap_no_file_prints_output(capsys):
    """cheap mode with no --file prints output to stdout."""
    with patch("orchestrator.call_groq", return_value="hello"):
        from orchestrator import dispatch
        dispatch(agent="qa", task="write test", mode="cheap")

    captured = capsys.readouterr()
    assert "hello" in captured.out
