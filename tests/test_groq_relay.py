# tests/test_groq_relay.py
from unittest.mock import MagicMock, patch


def test_call_groq_basic():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "def hello(): pass"

    with patch("tools.groq_relay.Groq") as MockGroq:
        MockGroq.return_value.chat.completions.create.return_value = mock_response
        from tools.groq_relay import call_groq
        result = call_groq("write a hello function", "llama-3.1-8b-instant")

    assert result == "def hello(): pass"


def test_call_groq_with_system_prompt():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "result"

    with patch("tools.groq_relay.Groq") as MockGroq:
        instance = MockGroq.return_value
        instance.chat.completions.create.return_value = mock_response
        from tools.groq_relay import call_groq
        call_groq("prompt", "llama-3.1-8b-instant", system="you are a dev")

    call_args = instance.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "you are a dev"}
    assert messages[1] == {"role": "user", "content": "prompt"}


def test_call_groq_missing_key_raises():
    import os
    import pytest
    env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with patch("tools.groq_relay.Groq", side_effect=Exception("no key")):
            from tools.groq_relay import call_groq
            with pytest.raises(Exception):
                call_groq("prompt", "llama-3.1-8b-instant")
