import os

# Set dummy env vars before any module imports config.py
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("TELEGRAM_ALLOWED_USER_ID", "12345")
os.environ.setdefault("ANTHROPIC_API_KEY", "test_key")
os.environ.setdefault("UPSTASH_REDIS_REST_URL", "redis://localhost:6379")
os.environ.setdefault("UPSTASH_REDIS_REST_TOKEN", "test_redis_token")
os.environ.setdefault("DAILY_BUDGET_USD", "2.00")
