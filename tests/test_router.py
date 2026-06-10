from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_fable_trigger_slash_deep():
    from router import route
    model, reason = route("/deep explain the meaning of life")
    assert model == "claude-fable-5"
    assert "deep" in reason


def test_fable_trigger_slash_plan():
    from router import route
    model, reason = route("/plan build a landing page")
    assert model == "claude-fable-5"


def test_haiku_trigger_calendar():
    from router import route
    model, reason = route("τι έχω στο calendar αύριο;")
    assert model == "claude-haiku-4-5-20251001"


def test_haiku_trigger_quick():
    from router import route
    model, reason = route("γρήγορα — τι ώρα είναι η συνάντηση;")
    assert model == "claude-haiku-4-5-20251001"


def test_sonnet_default():
    from router import route
    model, reason = route("βοήθησέ με να γράψω ένα email στον πελάτη")
    assert model == "claude-sonnet-4-6"


def test_budget_lockdown_forces_haiku():
    from router import route
    with patch("router.is_deep_allowed", return_value=False), \
         patch("router.is_sonnet_allowed", return_value=False):
        model, reason = route("/deep analyze everything")
        assert model == "claude-haiku-4-5-20251001"
        assert "budget" in reason.lower()


def test_budget_critical_blocks_fable_allows_sonnet():
    from router import route
    with patch("router.is_deep_allowed", return_value=False), \
         patch("router.is_sonnet_allowed", return_value=True):
        model, reason = route("/deep analyze everything")
        assert model == "claude-sonnet-4-6"
