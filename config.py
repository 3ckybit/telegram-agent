import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_ALLOWED_USER_ID = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])

# NVIDIA NIM — free, OpenAI-compatible
NVIDIA_API_KEY  = os.environ.get("NVIDIA_API_KEY", "PASTE_KEY_HERE")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Model tiers — all free via NVIDIA NIM (confirmed working 2026-06-29)
MODEL_FAST   = "meta/llama-3.1-8b-instruct"               # quick / routing ✓
MODEL_MAIN   = "nvidia/llama-3.3-nemotron-super-49b-v1"   # default responses ✓
MODEL_LARGE  = "qwen/qwen3.5-122b-a10b"                   # deep / complex ✓

# Aliases so existing code keeps working
MODEL_HAIKU  = MODEL_FAST
MODEL_SONNET = MODEL_MAIN
MODEL_FABLE  = MODEL_LARGE

# Upstash Redis
REDIS_URL = os.environ["UPSTASH_REDIS_REST_URL"]
REDIS_TOKEN = os.environ["UPSTASH_REDIS_REST_TOKEN"]

# Vault mirror
VAULT_MIRROR_PATH = os.path.expanduser("~/vault-mirror")
VAULT_GITHUB_REPO = "https://github.com/3ckybit/topvault.git"

# Timezone
TZ = os.getenv("TZ", "Europe/Madrid")

# Redis keys
REDIS_VAULT_CACHE_KEY = "telegram:vault_context:{git_hash}"
REDIS_RESEARCH_CURSOR_KEY = "telegram:research_cursor"
VAULT_CACHE_TTL = 1800  # 30 minutes
