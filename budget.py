"""
Rate + cost limiter for Haiku-only Telegram bot.
Hard cap: 50 requests/day. Cost tracking in Redis.
At ~300 tokens/msg with Haiku: $0.15/month max.
"""
import redis as redis_lib
from datetime import date
from config import REDIS_URL, REDIS_TOKEN

DAILY_REQUEST_LIMIT = 50
WARN_AT = 40

# Haiku pricing per 1K tokens
HAIKU_INPUT_PRICE  = 0.0008
HAIKU_OUTPUT_PRICE = 0.004


def _get_redis():
    return redis_lib.from_url(REDIS_URL, password=REDIS_TOKEN)


def _day_key(suffix: str) -> str:
    return f"telegram:{suffix}:{date.today().isoformat()}"


def get_requests_today() -> int:
    try:
        val = _get_redis().get(_day_key("requests"))
        return int(val) if val else 0
    except Exception:
        return 0


def get_cost_today() -> float:
    try:
        val = _get_redis().get(_day_key("cost"))
        return float(val) if val else 0.0
    except Exception:
        return 0.0


def log_request(input_tokens: int = 0, output_tokens: int = 0):
    cost = (input_tokens * HAIKU_INPUT_PRICE + output_tokens * HAIKU_OUTPUT_PRICE) / 1000
    try:
        r = _get_redis()
        r.incr(_day_key("requests"))
        r.expire(_day_key("requests"), 86400 * 2)
        r.incrbyfloat(_day_key("cost"), cost)
        r.expire(_day_key("cost"), 86400 * 2)
    except Exception:
        pass


def check_rate_limit() -> str:
    count = get_requests_today()
    if count >= DAILY_REQUEST_LIMIT:
        return "BLOCKED"
    if count >= WARN_AT:
        return f"⚠️ {count}/{DAILY_REQUEST_LIMIT} requests today"
    return ""


def get_budget_status_message() -> str:
    count = get_requests_today()
    cost = get_cost_today()
    return f"📊 {count}/{DAILY_REQUEST_LIMIT} requests today — ${cost:.4f} spent"


def is_deep_allowed() -> bool:
    return get_requests_today() < DAILY_REQUEST_LIMIT


def is_sonnet_allowed() -> bool:
    return get_requests_today() < DAILY_REQUEST_LIMIT
