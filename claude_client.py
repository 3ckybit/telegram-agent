import anthropic
from context import get_cached_context
from budget import check_rate_limit, log_request
from config import ANTHROPIC_API_KEY, MODEL_HAIKU

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def chat(message: str, conversation_history: list = None) -> tuple[str, str, str]:
    """All Telegram messages → Haiku. Sonnet/Fable5 are terminal-only."""
    alert = check_rate_limit()
    if alert == "BLOCKED":
        return "⏸️ Daily limit reached — δοκίμασε αύριο.", MODEL_HAIKU, ""

    system = get_cached_context()
    messages = (conversation_history or []) + [{"role": "user", "content": message}]

    response = _get_client().messages.create(
        model=MODEL_HAIKU,
        max_tokens=1024,
        system=system,
        messages=messages,
    )

    log_request(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text, MODEL_HAIKU, alert if alert else ""


def chat_scheduled(prompt: str, max_tokens: int = 400) -> str:
    """Scheduled tasks — Haiku, minimal tokens."""
    system = get_cached_context()
    response = _get_client().messages.create(
        model=MODEL_HAIKU,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    log_request(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text
