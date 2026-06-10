from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_cost_calculation_haiku():
    from budget import calculate_cost
    cost = calculate_cost("claude-haiku-4-5-20251001", input_tokens=1000, output_tokens=500)
    assert abs(cost - (1000 * 0.0008 + 500 * 0.004) / 1000) < 0.0001


def test_cost_calculation_sonnet():
    from budget import calculate_cost
    cost = calculate_cost("claude-sonnet-4-6", input_tokens=1000, output_tokens=500)
    assert abs(cost - (1000 * 0.003 + 500 * 0.015) / 1000) < 0.0001


def test_cost_calculation_fable():
    from budget import calculate_cost
    cost = calculate_cost("claude-fable-5", input_tokens=1000, output_tokens=500)
    assert abs(cost - (1000 * 0.015 + 500 * 0.075) / 1000) < 0.0001


def test_budget_threshold_levels():
    from budget import get_threshold_level
    assert get_threshold_level(0.4, 2.0) == "ok"
    assert get_threshold_level(1.1, 2.0) == "warning"
    assert get_threshold_level(1.65, 2.0) == "alert"
    assert get_threshold_level(1.82, 2.0) == "critical"
    assert get_threshold_level(1.95, 2.0) == "lockdown"


def test_is_deep_allowed_blocks_at_critical():
    from budget import is_deep_allowed, is_sonnet_allowed
    with patch("budget.get_today_spend", return_value=1.85), \
         patch("budget.DAILY_BUDGET_USD", 2.0):
        assert is_deep_allowed() == False
        assert is_sonnet_allowed() == True


def test_is_lockdown_blocks_sonnet():
    from budget import is_sonnet_allowed
    with patch("budget.get_today_spend", return_value=1.96), \
         patch("budget.DAILY_BUDGET_USD", 2.0):
        assert is_sonnet_allowed() == False
