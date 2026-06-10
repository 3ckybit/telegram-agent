"""
Rate limiter — protects Pro subscription from overuse.
No dollar billing. Tracks requests/hour in Redis.
"""
import redis as redis_lib
from datetime import datetime
from config import REDIS_URL, REDIS_TOKEN

MAX_REQUESTS_PER_HOUR = int(30)   # Claude Pro has usage limits
WARN_AT = int(20)                  # warn at 20 req/hr


def _get_redis():
    return redis_lib.from_url(REDIS_URL, password=REDIS_TOKEN)


def _hour_key() -> str:
    return f"telegram:rate:{datetime.now().strftime('%Y-%m-%dT%H')}"


def get_requests_this_hour() -> int:
    try:
        r = _get_redis()
        val = r.get(_hour_key())
        return int(val) if val else 0
    except Exception:
        return 0


def log_request():
    try:
        r = _get_redis()
        key = _hour_key()
        r.incr(key)
        r.expire(key, 7200)
    except Exception:
        pass


def check_rate_limit() -> str:
    """Returns '' (ok), warning message, or 'BLOCKED'."""
    count = get_requests_this_hour()
    if count >= MAX_REQUESTS_PER_HOUR:
        return "BLOCKED"
    if count >= WARN_AT:
        return f"⚠️ {count}/{MAX_REQUESTS_PER_HOUR} requests this hour"
    return ""


def get_budget_status_message() -> str:
    count = get_requests_this_hour()
    return f"📊 {count}/{MAX_REQUESTS_PER_HOUR} requests this hour"


# Kept for router compatibility — always allowed since no dollar cost
def is_deep_allowed() -> bool:
    return get_requests_this_hour() < MAX_REQUESTS_PER_HOUR


def is_sonnet_allowed() -> bool:
    return get_requests_this_hour() < MAX_REQUESTS_PER_HOUR
