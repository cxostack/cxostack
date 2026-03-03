"""Tests for pure helper functions in main.py."""

from main import _mask_key


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
