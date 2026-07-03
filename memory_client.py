"""
memory_client.py — Universal Shared Memory (Redis/Upstash)
~/telegram-agent/memory_client.py

Multi-agent shared memory. Any agent (Telegram bot, Claude Code sessions,
future agents) can write/read facts here. Redis handles concurrency —
no git merge conflicts.

Schema:
  memory:facts:{uuid}      → JSON {source, timestamp, category, content}
  memory:pending_sync      → SET of fact UUIDs not yet written to vault/git
  memory:synced            → SET of fact UUIDs already in vault

Sync flow:
  1. Bot (or any agent) calls remember() → writes to memory:facts:{uuid},
     adds uuid to memory:pending_sync
  2. Claude (Mac, nightly session) calls get_pending_facts() → reads them,
     writes into vault markdown, calls mark_synced(uuid) for each
  3. git commit + push happens on the Mac side only (see sync_to_vault.py)

Usage:
  from memory_client import remember, recall, get_pending_facts
  remember("Alex prefers NVIDIA free models for routine bot replies", category="preference")
"""
import os
import json
import uuid as uuid_lib
import logging
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

AGENT_NAME = os.environ.get("AGENT_NAME", "telegram-bot")  # identifies the writer

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
            raise ValueError(
                "UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN not set. "
                "Get them from the Upstash console (communal-chow-143616 instance) "
                "and add to ~/telegram-agent/.env"
            )
        # Must be a redis:// or rediss:// TCP connection string — NOT the Upstash
        # REST API URL (https://...). Get it from the Upstash console's "Connect"
        # tab (redis-cli / ioredis snippet), not the REST API tab.
        _client = redis.from_url(
            UPSTASH_REDIS_REST_URL, password=UPSTASH_REDIS_REST_TOKEN
        )
    return _client


# ── Write ─────────────────────────────────────────────────────────────────────
def remember(content: str, category: str = "general", source: str | None = None) -> str:
    """
    Write a fact to shared memory. Returns the fact UUID.

    category: "preference" | "project_update" | "decision" | "general"
    source: defaults to AGENT_NAME env var (e.g. "telegram-bot")
    """
    r = get_redis()
    fact_id = str(uuid_lib.uuid4())
    fact = {
        "source": source or AGENT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "content": content,
    }
    r.set(f"memory:facts:{fact_id}", json.dumps(fact))
    r.sadd("memory:pending_sync", fact_id)
    logger.info(f"Remembered fact {fact_id} ({category}): {content[:60]}")
    return fact_id


# ── Read ──────────────────────────────────────────────────────────────────────
def recall(fact_id: str) -> dict | None:
    """Read a single fact by UUID."""
    r = get_redis()
    raw = r.get(f"memory:facts:{fact_id}")
    return json.loads(raw) if raw else None


def get_pending_facts() -> list[dict]:
    """
    Get all facts not yet synced to the vault/git.
    Called by Claude (Mac) during nightly sync.
    Returns list of {id, source, timestamp, category, content}.
    """
    r = get_redis()
    pending_ids = r.smembers("memory:pending_sync")
    facts = []
    for fid in pending_ids:
        fid = fid.decode() if isinstance(fid, bytes) else fid
        fact = recall(fid)
        if fact:
            fact["id"] = fid
            facts.append(fact)
    facts.sort(key=lambda f: f["timestamp"])
    return facts


def mark_synced(fact_id: str) -> None:
    """Mark a fact as written to vault/git. Moves it out of the pending queue."""
    r = get_redis()
    r.srem("memory:pending_sync", fact_id)
    r.sadd("memory:synced", fact_id)


def get_recent_facts(limit: int = 20, category: str | None = None) -> list[dict]:
    """
    Get recent facts across both pending and synced (for the bot to use as context).
    Not efficient at scale — fine for personal use volume.
    """
    r = get_redis()
    all_ids = list(r.smembers("memory:pending_sync")) + list(r.smembers("memory:synced"))
    facts = []
    for fid in all_ids:
        fid = fid.decode() if isinstance(fid, bytes) else fid
        fact = recall(fid)
        if fact and (category is None or fact["category"] == category):
            fact["id"] = fid
            facts.append(fact)
    facts.sort(key=lambda f: f["timestamp"], reverse=True)
    return facts[:limit]


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing shared memory connection...")
    fid = remember("Test fact from CLI — universal memory system online", category="general")
    print(f"✅ Wrote fact: {fid}")

    fact = recall(fid)
    print(f"✅ Read back: {fact}")

    pending = get_pending_facts()
    print(f"✅ Pending sync queue: {len(pending)} fact(s)")

    print("\n✅ memory_client.py working — ready for bot.py integration")
