"""
Thin client wrapper around the LlmServer Modal class.

All agents call `call_llm(...)` instead of interacting with the server directly.
Handles retries, JSON parsing, and error recovery.
"""

from __future__ import annotations

import json
import time
import re
from typing import Any


def _get_server():
    """Lazy import to avoid circular dependency at module load time."""
    from llm.server import LlmServer
    return LlmServer()


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    json_mode: bool = False,
    retries: int = 5,
) -> str:
    """
    Call the Qwen model via Modal RPC to LlmServer.

    Args:
        prompt: The user message.
        system_prompt: System instruction.
        temperature: Sampling temperature.
        max_tokens: Max generation length.
        json_mode: Append JSON-only instruction to system prompt.
        retries: Number of retry attempts on failure.

    Returns:
        Generated text response (string).
    """
    server = _get_server()
    last_error = None

    for attempt in range(retries):
        try:
            result = server.generate.remote(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
            return result
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait_time = 10 * (attempt + 1)  # backoff: 10s, 20s, 30s (cold start can be slow)
                print(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")


def call_llm_json(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    retries: int = 3,
) -> dict[str, Any] | list:
    """
    Call vLLM and parse the response as JSON.

    Returns:
        Parsed JSON object or array.

    Raises:
        json.JSONDecodeError if parsing fails after retries.
    """
    last_error = None
    raw_text = None

    for attempt in range(retries):
        try:
            raw_text = call_llm(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=True,
                retries=1,  # inner retry handled by outer loop
            )
            return _extract_json(raw_text)
        except json.JSONDecodeError as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(1)

    raise RuntimeError(
        f"Failed to parse LLM JSON after {retries} attempts: {last_error}\n"
        f"Last raw output: {raw_text[:500] if raw_text else 'None'}"
    )


def _extract_json(text: str) -> dict[str, Any] | list:
    """
    Extract JSON from LLM output, handling common issues like
    markdown code fences or trailing text.
    """
    # Strip markdown code fences if present
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find [ ... ] block
    bracket_match = re.search(r"\[.*\]", text, re.DOTALL)
    if bracket_match:
        try:
            return json.loads(bracket_match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No JSON object found in LLM output", text, 0)
