import subprocess
from router import route
from context import get_cached_context
from budget import check_rate_limit, log_request


def _build_prompt(message: str, history: list, system: str) -> str:
    parts = [f"<system>\n{system}\n</system>\n"]
    if history:
        parts.append("<conversation>")
        for turn in history[-10:]:  # last 5 turns
            role = "User" if turn["role"] == "user" else "Assistant"
            parts.append(f"{role}: {turn['content']}")
        parts.append("</conversation>\n")
    parts.append(f"User: {message}")
    return "\n".join(parts)


def chat(message: str, conversation_history: list = None) -> tuple[str, str, str]:
    """Returns (response_text, model_used, alert_or_empty)."""
    model, reason = route(message)
    alert = check_rate_limit()
    if alert == "BLOCKED":
        return "⏸️ Rate limit reached — δοκίμασε σε λίγο.", model, ""

    system = get_cached_context()
    prompt = _build_prompt(message, conversation_history or [], system)

    result = subprocess.run(
        ["claude", "--print", prompt, "--model", model],
        capture_output=True, text=True, timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr or "claude CLI error")

    log_request()
    return result.stdout.strip(), model, alert if alert else ""


def chat_scheduled(prompt: str, max_tokens: int = 512) -> str:
    """For scheduled tasks — always Haiku via CLI."""
    from config import MODEL_HAIKU
    system = get_cached_context()
    full_prompt = f"<system>\n{system}\n</system>\n\nUser: {prompt}"

    result = subprocess.run(
        ["claude", "--print", full_prompt, "--model", MODEL_HAIKU],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr or "claude CLI error")

    log_request()
    return result.stdout.strip()
