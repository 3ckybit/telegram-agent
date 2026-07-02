import os
import re
import subprocess
import redis as redis_lib
from datetime import datetime
from config import (
    VAULT_MIRROR_PATH, VAULT_GITHUB_REPO,
    REDIS_URL, REDIS_TOKEN, REDIS_VAULT_CACHE_KEY, VAULT_CACHE_TTL
)


def _get_redis():
    return redis_lib.from_url(REDIS_URL, password=REDIS_TOKEN)


def _get_vault_git_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", VAULT_MIRROR_PATH, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _refresh_vault_mirror():
    if not os.path.exists(VAULT_MIRROR_PATH):
        subprocess.run(
            ["git", "clone", "--depth=1", VAULT_GITHUB_REPO, VAULT_MIRROR_PATH],
            capture_output=True, stdin=subprocess.DEVNULL, timeout=60
        )
    else:
        subprocess.run(
            ["git", "-C", VAULT_MIRROR_PATH, "pull", "--ff-only"],
            capture_output=True, stdin=subprocess.DEVNULL, timeout=30
        )


def _read_vault_file(relative_path: str) -> str:
    full = os.path.join(VAULT_MIRROR_PATH, relative_path)
    if not os.path.exists(full):
        return ""
    with open(full, encoding="utf-8") as f:
        return f.read()


def _get_vault_summary() -> str:
    for path in ["memory/MEMORY.md", "MEMORY.md"]:
        content = _read_vault_file(path)
        if content:
            return content
    return ""


def _get_active_projects() -> list[str]:
    memory = _get_vault_summary()
    in_active = False
    projects = []
    for line in memory.splitlines():
        if "## Active Projects" in line:
            in_active = True
            continue
        if in_active and line.startswith("## "):
            break
        if in_active and line.startswith("- ["):
            match = re.search(r"\[([^\]]+)\]", line)
            if match:
                projects.append(match.group(1))
    return projects


def _get_memory_facts() -> str:
    return _read_vault_file("memory/user_alex.md")[:1500]


def compile_context() -> str:
    vault_summary = _get_vault_summary()
    active_projects = _get_active_projects()
    memory_facts = _get_memory_facts()
    today = datetime.now().strftime("%A, %Y-%m-%d %H:%M")

    return f"""You are Alex's personal AI agent. Alex Vlachos, based in Seville, Spain.

Today: {today}

## Alex's Profile
{memory_facts}

## Active Projects
{chr(10).join(f'- {p}' for p in active_projects)}

## Full Memory Index
{vault_summary[:3000]}

## Instructions
- You are a Telegram bot. Keep replies SHORT — 2-4 sentences max unless Alex asks for more.
- Plain text only. No markdown, no bullet points, no headers, no bold, no asterisks.
- Be direct and conversational, like texting a smart friend.
- Language: Greek if Alex writes Greek, English if English.
- Spot problems Alex hasn't mentioned. Be opinionated.
- If asked for a list or detail, then expand — otherwise stay tight.
"""


def get_cached_context() -> str:
    _refresh_vault_mirror()
    git_hash = _get_vault_git_hash()
    cache_key = REDIS_VAULT_CACHE_KEY.format(git_hash=git_hash)
    try:
        r = _get_redis()
        cached = r.get(cache_key)
        if cached:
            return cached.decode()
        context = compile_context()
        r.setex(cache_key, VAULT_CACHE_TTL, context)
        return context
    except Exception:
        return compile_context()
