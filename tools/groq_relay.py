#!/usr/bin/env python3
"""Groq relay — pure text generation for cheap dev agent tasks.

Groq agents have no tool access. This module calls the Groq API and returns
raw text. The orchestrator is responsible for all file writes and formatting.
"""

import os

from groq import Groq


def call_groq(prompt: str, model: str = "llama-3.1-8b-instant", system: str = "") -> str:
    """Call Groq API and return raw text output.

    Args:
        prompt: The user message to send.
        model: Groq model ID. Defaults to llama-3.1-8b-instant.
        system: Optional system prompt.

    Returns:
        Raw text response from the model.

    Raises:
        Exception: On API error or missing GROQ_API_KEY.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
