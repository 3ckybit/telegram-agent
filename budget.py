import redis as redis_lib
from datetime import date
from config import (
    REDIS_URL, REDIS_TOKEN, REDIS_BUDGET_KEY, DAILY_BUDGET_USD,
    MODEL_HAIKU, MODEL_SONNET, MODEL_FABLE
)

MODEL_PRICING = {
    MODEL_HAIKU:  (0.0008,  0.004),
    MODEL_SONNET: (0.003,   0.015),
    MODEL_FABLE:  (0.015,   0.075),
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = MODEL_PRICING.get(model, (0.003, 0.015))
    return (input_tokens * input_price + output_tokens * output_price) / 1000


def get_threshold_level(spent: float, budget: float) -> str:
    ratio = spent / budget
    if ratio >= 0.95:
        return "lockdown"
    if ratio >= 0.90:
        return "critical"
    if ratio >= 0.80:
        return "alert"
    if ratio >= 0.50:
        return "warning"
    return "ok"


def _get_redis():
    return redis_lib.from_url(REDIS_URL, password=REDIS_TOKEN)


def get_today_spend() -> float:
    key = REDIS_BUDGET_KEY.format(date=date.today().isoformat())
    try:
        r = _get_redis()
        val = r.get(key)
        return float(val) if val else 0.0
    except Exception:
        return 0.0


def log_spend(model: str, input_tokens: int, output_tokens: int) -> tuple[float, str]:
    cost = calculate_cost(model, input_tokens, output_tokens)
    key = REDIS_BUDGET_KEY.format(date=date.today().isoformat())
    try:
        r = _get_redis()
        r.incrbyfloat(key, cost)
        r.expire(key, 86400 * 2)
    except Exception:
        pass
    total = get_today_spend()
    level = get_threshold_level(total, DAILY_BUDGET_USD)
    return total, level


def is_deep_allowed() -> bool:
    return get_threshold_level(get_today_spend(), DAILY_BUDGET_USD) not in ("critical", "lockdown")


def is_sonnet_allowed() -> bool:
    return get_threshold_level(get_today_spend(), DAILY_BUDGET_USD) != "lockdown"


def get_budget_status_message() -> str:
    spent = get_today_spend()
    level = get_threshold_level(spent, DAILY_BUDGET_USD)
    pct = int(spent / DAILY_BUDGET_USD * 100)
    return f"💰 Budget: ${spent:.3f} / ${DAILY_BUDGET_USD:.2f} ({pct}%) — {level.upper()}"
