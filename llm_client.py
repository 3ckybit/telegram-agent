"""LLM client — NVIDIA NIM (free, OpenAI-compatible)."""

import os
from openai import OpenAI
from context import get_cached_context
from budget import check_rate_limit, log_request
from config import NVIDIA_API_KEY, NVIDIA_BASE_URL, MODEL_FAST, MODEL_MAIN, MODEL_LARGE

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    return _client


def _build_messages(system: str, history: list, message: str) -> list:
    return [{"role": "system", "content": system}] + (history or []) + [{"role": "user", "content": message}]


def chat(message: str, conversation_history: list = None, model: str = None) -> tuple[str, str, str]:
    alert = check_rate_limit()
    if alert == "BLOCKED":
        return "⏸️ Daily limit reached — δοκίμασε αύριο.", MODEL_FAST, ""

    use_model = model or MODEL_MAIN
    system = get_cached_context()
    messages = _build_messages(system, conversation_history, message)

    response = _get_client().chat.completions.create(
        model=use_model,
        max_tokens=512,
        temperature=0.3,
        messages=messages,
    )

    reply = response.choices[0].message.content
    log_request()  # free — just counting requests
    return reply, use_model, alert if alert else ""


def chat_scheduled(prompt: str, max_tokens: int = 400) -> str:
    system = get_cached_context()
    messages = _build_messages(system, [], prompt)
    response = _get_client().chat.completions.create(
        model=MODEL_FAST,
        max_tokens=max_tokens,
        messages=messages,
    )
    log_request()
    return response.choices[0].message.content
