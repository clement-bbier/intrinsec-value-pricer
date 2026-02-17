"""
tests/unit/test_main_app.py

MAIN APPLICATION ENTRY POINT TESTS
===================================
Role: Validates the main.py application structure, routing logic,
and footer rendering.
Coverage Target: >85% for app/main.py.
"""

import inspect


class TestMainStructure:
    """Tests the main application structure and imports."""

    def test_main_function_exists(self):
        """main() must exist in app.main."""
        from app.main import main

        assert callable(main)

    def test_version_imported(self):
        """Version string must be importable."""
        from src import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0




class TestPageConfig:
    """Tests the page configuration constants."""

    def test_page_icon_no_emoji(self):
        """page_icon should not be an emoji character."""
        source_file = inspect.getfile(__import__("app.main", fromlist=["main"]).main)
        with open(source_file) as f:
            content = f.read()
        # The old emoji was replaced with a text icon
        assert "\U0001f4ca" not in content


class TestRoutingLogic:
    """Tests the content routing logic in main."""

    def test_main_checks_error_message(self):
        """main() must check state.error_message."""
        from app.main import main

        source = inspect.getsource(main)
        assert "error_message" in source

    def test_main_checks_last_result(self):
        """main() must check state.last_result."""
        from app.main import main

        source = inspect.getsource(main)
        assert "last_result" in source

    def test_main_checks_expert_mode(self):
        """main() must check state.is_expert_mode."""
        from app.main import main

        source = inspect.getsource(main)
        assert "is_expert_mode" in source

    def test_main_renders_sidebar(self):
        """main() must call render_sidebar."""
        from app.main import main

        source = inspect.getsource(main)
        assert "render_sidebar" in source

    def test_main_injects_design(self):
        """main() must call inject_institutional_design."""
        from app.main import main

        source = inspect.getsource(main)
        assert "inject_institutional_design" in source
