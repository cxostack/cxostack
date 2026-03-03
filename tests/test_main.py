"""Tests for pure helper functions in main.py."""

import tempfile
from pathlib import Path

from main import _mask_key, _write_env_key


def test_mask_key_long_key():
    result = _mask_key("sk-ant-api03-abc123xyz")
    assert result == "sk-ant***yz"


def test_mask_key_short_key():
    result = _mask_key("abc123")
    assert result == "***"


def test_mask_key_exactly_8_chars():
    result = _mask_key("12345678")
    assert result == "***"


def test_mask_key_9_chars():
    result = _mask_key("123456789")
    assert result == "123456***89"


def test_write_env_key_creates_file_if_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        _write_env_key("FOO", "bar123", env_path=env_path)
        assert env_path.read_text() == "FOO=bar123\n"


def test_write_env_key_appends_new_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("EXISTING=value\n")
        _write_env_key("NEW_KEY", "newval", env_path=env_path)
        content = env_path.read_text()
        assert "EXISTING=value\n" in content
        assert "NEW_KEY=newval\n" in content


def test_write_env_key_updates_existing_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("ANTHROPIC_API_KEY=old-value\nOTHER=keep\n")
        _write_env_key("ANTHROPIC_API_KEY", "new-value", env_path=env_path)
        content = env_path.read_text()
        assert "ANTHROPIC_API_KEY=new-value\n" in content
        assert "old-value" not in content
        assert "OTHER=keep\n" in content


def test_write_env_key_preserves_comments():
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        env_path.write_text("# Required\nANTHROPIC_API_KEY=old\n")
        _write_env_key("ANTHROPIC_API_KEY", "updated", env_path=env_path)
        content = env_path.read_text()
        assert "# Required\n" in content
        assert "ANTHROPIC_API_KEY=updated\n" in content
