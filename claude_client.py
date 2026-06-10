import anthropic
from config import ANTHROPIC_API_KEY, MODEL_HAIKU
from budget import log_spend, get_budget_status_message, get_threshold_level, get_today_spend, DAILY_BUDGET_USD
from router import route
from context import get_cached_context

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def chat(message: str, conversation_history: list = None) -> tuple[str, str, str]:
    """Returns (response_text, model_used, budget_alert_or_empty)."""
    model, reason = route(message)
    system_prompt = get_cached_context()
    messages = (conversation_history or []) + [{"role": "user", "content": message}]

    response = _get_client().messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )

    text = response.content[0].text
    total, level = log_spend(model, response.usage.input_tokens, response.usage.output_tokens)

    alert = ""
    if level == "warning":
        alert = f"⚠️ Budget at 50%: {get_budget_status_message()}"
    elif level == "alert":
        alert = f"🟠 Budget at 80%! {get_budget_status_message()}"
    elif level == "critical":
        alert = f"🔴 Budget at 90%! Fable 5 disabled. {get_budget_status_message()}"
    elif level == "lockdown":
        alert = f"🚨 BUDGET LOCKDOWN (95%)! Haiku only. {get_budget_status_message()}"

    return text, model, alert


def chat_scheduled(prompt: str, max_tokens: int = 512) -> str:
    """For scheduled tasks — always Haiku, minimal tokens."""
    system_prompt = get_cached_context()
    response = _get_client().messages.create(
        model=MODEL_HAIKU,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )
    log_spend(MODEL_HAIKU, response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text
