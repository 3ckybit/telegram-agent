from unittest.mock import patch, mock_open
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_compile_context_returns_string():
    from context import compile_context
    with patch("context._get_vault_summary", return_value="## Projects\n- Taxi Drama\n"), \
         patch("context._get_active_projects", return_value=["Taxi Drama", "Etsy"]), \
         patch("context._get_memory_facts", return_value="Alex is in Seville."):
        result = compile_context()
        assert isinstance(result, str)
        assert "Taxi Drama" in result
        assert "Alex" in result


def test_vault_summary_reads_memory_md():
    from context import _get_vault_summary
    fake_memory = "# Memory Index\n- [Alex](user_alex.md) — profile\n"
    with patch("builtins.open", mock_open(read_data=fake_memory)), \
         patch("os.path.exists", return_value=True):
        result = _get_vault_summary()
        assert "Memory Index" in result


def test_get_active_projects_parses_memory():
    from context import _get_active_projects
    fake_memory = "## Active Projects\n- [Taxi Drama](p.md) — live\n- [Etsy](e.md) — running\n\n## Paused"
    with patch("builtins.open", mock_open(read_data=fake_memory)), \
         patch("os.path.exists", return_value=True):
        projects = _get_active_projects()
        assert "Taxi Drama" in projects
        assert "Etsy" in projects
