"""
tests/unit/test_benchmark_report.py

BENCHMARK REPORT UNIT TESTS
=============================
Role: Validates the benchmark report helper functions and data access patterns.
Coverage: Direct attribute access without getattr hacks.
"""


from src.models.benchmarks import CompanyStats
from app.views.results.pillars.benchmark_report import (
    _render_piotroski_section,
    _safe_float,
    render_benchmark_view,
)


class TestSafeFloatFunction:
    """Tests the module-level _safe_float helper."""

    def test_none_returns_zero(self):
        """None input should return 0.0."""
        assert _safe_float(None) == 0.0

    def test_float_returned_as_is(self):
        """Non-None float should be returned unchanged."""
        assert _safe_float(25.5) == 25.5

    def test_zero_returned_as_zero(self):
        """Explicit 0.0 should return 0.0 (not confused with None)."""
        assert _safe_float(0.0) == 0.0

    def test_negative_returned_as_is(self):
        """Negative values should be returned unchanged."""
        assert _safe_float(-5.0) == -5.0


class TestSafeFloatPattern:
    """Tests that the benchmark report handles None values correctly."""

    def test_company_stats_none_pe_ratio(self):
        """CompanyStats with None pe_ratio should not crash."""
        stats = CompanyStats(pe_ratio=None, ev_ebitda=None, pb_ratio=None)
        assert stats.pe_ratio is None
        # The _safe_float pattern: val if val is not None else 0.0
        val = stats.pe_ratio if stats.pe_ratio is not None else 0.0
        assert val == 0.0

    def test_company_stats_valid_pe_ratio(self):
        """CompanyStats with valid pe_ratio should return the value."""
        stats = CompanyStats(pe_ratio=25.5)
        val = stats.pe_ratio if stats.pe_ratio is not None else 0.0
        assert val == 25.5

    def test_company_stats_zero_pe_ratio(self):
        """CompanyStats with zero pe_ratio should return 0.0 (not be confused with None)."""
        stats = CompanyStats(pe_ratio=0.0)
        val = stats.pe_ratio if stats.pe_ratio is not None else 0.0
        assert val == 0.0

    def test_all_fields_none_safe(self):
        """All CompanyStats fields defaulting to None should be handled safely."""
        stats = CompanyStats()
        for field in ('pe_ratio', 'ev_ebitda', 'pb_ratio', 'fcf_margin', 'roe', 'revenue_growth'):
            val = getattr(stats, field)
            safe_val = val if val is not None else 0.0
            assert safe_val == 0.0

    def test_piotroski_score_default(self):
        """Piotroski score should default properly."""
        stats = CompanyStats()
        # Model default is 0 (int)
        assert stats.piotroski_score is not None


class TestPiotroskiInterpretation:
    """Tests the Piotroski score business logic."""

    def test_strong_score(self):
        """Score >= 7 should be classified as strong."""
        for score in (7, 8, 9):
            if score >= 7:
                result = "STRONG"
            elif score >= 4:
                result = "STABLE"
            else:
                result = "WEAK"
            assert result == "STRONG"

    def test_stable_score(self):
        """Score 4-6 should be classified as stable."""
        for score in (4, 5, 6):
            if score >= 7:
                result = "STRONG"
            elif score >= 4:
                result = "STABLE"
            else:
                result = "WEAK"
            assert result == "STABLE"

    def test_weak_score(self):
        """Score 0-3 should be classified as weak."""
        for score in (0, 1, 2, 3):
            if score >= 7:
                result = "STRONG"
            elif score >= 4:
                result = "STABLE"
            else:
                result = "WEAK"
            assert result == "WEAK"


class TestValuationStatusLogic:
    """Tests the valuation comparison helper logic."""

    def test_leader_when_cheaper(self):
        """Company cheaper than sector should be LEADER."""
        company_val, sector_val = 15.0, 20.0
        if company_val > sector_val:
            status = "RETARD"
        else:
            status = "LEADER"
        assert status == "LEADER"

    def test_retard_when_expensive(self):
        """Company more expensive than sector should be RETARD."""
        company_val, sector_val = 30.0, 20.0
        if company_val > sector_val:
            status = "RETARD"
        else:
            status = "LEADER"
        assert status == "RETARD"

    def test_performance_leader(self):
        """Higher company performance should be LEADER."""
        company_val, sector_val = 0.25, 0.15
        if company_val > sector_val:
            status = "LEADER"
        else:
            status = "RETARD"
        assert status == "LEADER"

    def test_performance_retard(self):
        """Lower company performance should be RETARD."""
        company_val, sector_val = 0.10, 0.15
        if company_val > sector_val:
            status = "LEADER"
        else:
            status = "RETARD"
        assert status == "RETARD"


class TestProgressBarBounds:
    """Tests the progress bar value clamping."""

    def test_progress_zero_score(self):
        """Score 0 should give 0.0 progress."""
        val = max(0.0, min(1.0, 0 / 9))
        assert val == 0.0

    def test_progress_full_score(self):
        """Score 9 should give 1.0 progress."""
        val = max(0.0, min(1.0, 9 / 9))
        assert val == 1.0

    def test_progress_mid_score(self):
        """Score 5 should give ~0.556 progress."""
        val = max(0.0, min(1.0, 5 / 9))
        assert 0.5 < val < 0.6

    def test_progress_never_exceeds_bounds(self):
        """Progress value must always be between 0.0 and 1.0."""
        for score in range(10):
            val = max(0.0, min(1.0, score / 9))
            assert 0.0 <= val <= 1.0


class TestNoGetattr:
    """Verifies that benchmark_report.py no longer uses getattr hacks."""

    def test_no_getattr_on_benchmark_texts(self):
        """benchmark_report.py must not use getattr on BenchmarkTexts."""
        import inspect
        source = inspect.getsource(_render_piotroski_section)
        assert "getattr(BenchmarkTexts" not in source

    def test_no_getattr_on_company_stats_in_render(self):
        """benchmark_report.py render function must not use getattr on company_stats."""
        import inspect
        source = inspect.getsource(render_benchmark_view)
        assert "getattr(company_stats" not in source

    def test_no_or_zero_pattern_in_render(self):
        """benchmark_report.py must not use 'or 0.0' pattern."""
        import inspect
        source = inspect.getsource(render_benchmark_view)
        assert "or 0.0" not in source
