import json
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_remember_writes_fact_and_returns_uuid():
    from memory_client import remember
    with patch("memory_client.get_redis") as mock_redis:
        r = MagicMock()
        mock_redis.return_value = r
        fact_id = remember("Alex prefers NVIDIA free models", category="preference")
        assert isinstance(fact_id, str) and len(fact_id) == 36
        r.set.assert_called_once()
        key, payload = r.set.call_args[0]
        assert key == f"memory:facts:{fact_id}"
        data = json.loads(payload)
        assert data["content"] == "Alex prefers NVIDIA free models"
        assert data["category"] == "preference"
        r.sadd.assert_called_once_with("memory:pending_sync", fact_id)


def test_recall_returns_none_when_missing():
    from memory_client import recall
    with patch("memory_client.get_redis") as mock_redis:
        mock_redis.return_value.get.return_value = None
        assert recall("nonexistent") is None


def test_recall_returns_parsed_fact():
    from memory_client import recall
    fact = {"source": "telegram-bot", "timestamp": "2026-07-02T10:00:00+00:00",
             "category": "general", "content": "hello"}
    with patch("memory_client.get_redis") as mock_redis:
        mock_redis.return_value.get.return_value = json.dumps(fact).encode()
        assert recall("abc") == fact


def test_get_pending_facts_sorts_by_timestamp():
    from memory_client import get_pending_facts
    fact_old = {"source": "a", "timestamp": "2026-07-01T00:00:00+00:00",
                "category": "general", "content": "old"}
    fact_new = {"source": "a", "timestamp": "2026-07-02T00:00:00+00:00",
                "category": "general", "content": "new"}
    with patch("memory_client.get_redis") as mock_redis:
        r = MagicMock()
        r.smembers.return_value = {b"id-new", b"id-old"}
        def fake_get(key):
            return json.dumps(fact_new if "id-new" in key else fact_old).encode()
        r.get.side_effect = fake_get
        mock_redis.return_value = r
        facts = get_pending_facts()
        assert [f["content"] for f in facts] == ["old", "new"]


def test_mark_synced_moves_between_sets():
    from memory_client import mark_synced
    with patch("memory_client.get_redis") as mock_redis:
        r = MagicMock()
        mock_redis.return_value = r
        mark_synced("fact-1")
        r.srem.assert_called_once_with("memory:pending_sync", "fact-1")
        r.sadd.assert_called_once_with("memory:synced", "fact-1")


def test_get_recent_facts_filters_by_category():
    from memory_client import get_recent_facts
    fact_pref = {"source": "a", "timestamp": "2026-07-02T00:00:00+00:00",
                 "category": "preference", "content": "pref"}
    fact_gen = {"source": "a", "timestamp": "2026-07-02T00:01:00+00:00",
                "category": "general", "content": "gen"}
    with patch("memory_client.get_redis") as mock_redis:
        r = MagicMock()
        r.smembers.side_effect = [{b"id-pref"}, {b"id-gen"}]
        def fake_get(key):
            return json.dumps(fact_pref if "id-pref" in key else fact_gen).encode()
        r.get.side_effect = fake_get
        mock_redis.return_value = r
        facts = get_recent_facts(category="preference")
        assert len(facts) == 1
        assert facts[0]["content"] == "pref"
