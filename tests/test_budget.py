from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_get_requests_returns_int():
    from budget import get_requests_today
    with patch("budget._get_redis") as mock_redis:
        mock_redis.return_value.get.return_value = b"5"
        assert get_requests_today() == 5


def test_get_requests_returns_zero_when_empty():
    from budget import get_requests_today
    with patch("budget._get_redis") as mock_redis:
        mock_redis.return_value.get.return_value = None
        assert get_requests_today() == 0


def test_check_rate_limit_ok():
    from budget import check_rate_limit
    with patch("budget.get_requests_today", return_value=5):
        assert check_rate_limit() == ""


def test_check_rate_limit_warning():
    from budget import check_rate_limit
    with patch("budget.get_requests_today", return_value=42):
        result = check_rate_limit()
        assert "42" in result


def test_check_rate_limit_blocked():
    from budget import check_rate_limit
    with patch("budget.get_requests_today", return_value=50):
        assert check_rate_limit() == "BLOCKED"


def test_is_deep_allowed_when_under_limit():
    from budget import is_deep_allowed
    with patch("budget.get_requests_today", return_value=10):
        assert is_deep_allowed() is True


def test_is_deep_allowed_blocked_at_limit():
    from budget import is_deep_allowed
    with patch("budget.get_requests_today", return_value=50):
        assert is_deep_allowed() is False
