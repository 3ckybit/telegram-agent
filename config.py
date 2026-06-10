import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])

# Claude API
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Models
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_FABLE = "claude-fable-5"

# Upstash Redis
REDIS_URL = os.environ["UPSTASH_REDIS_REST_URL"]
REDIS_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

# Budget
DAILY_BUDGET_USD = float(os.getenv("DAILY_BUDGET_USD", "2.00"))

# Vault mirror
VAULT_MIRROR_PATH = os.path.expanduser("~/vault-mirror")
VAULT_GITHUB_REPO = "https://github.com/3ckybit/topvault.git"

# Timezone
TZ = os.getenv("TZ", "Europe/Madrid")

# Redis keys
REDIS_BUDGET_KEY = "telegram:daily_budget:{date}"
REDIS_VAULT_CACHE_KEY = "telegram:vault_context:{git_hash}"
REDIS_RESEARCH_CURSOR_KEY = "telegram:research_cursor"
VAULT_CACHE_TTL = 1800  # 30 minutes
