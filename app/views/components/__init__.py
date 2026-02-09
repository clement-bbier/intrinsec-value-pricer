"""
app/views/components/__init__.py
UI COMPONENTS LIBRARY
=====================
Role: Exposes atomic UI components, charts, and renderers for the application.
Facilitates clean imports in view controllers.
"""

from .ui_kpis import (
    atom_kpi_metric,
    render_score_gauge,
    atom_benchmark_card
)

from .ui_charts import (
    display_price_chart,
    display_simulation_chart,
    display_football_field,
    display_sensitivity_heatmap,
    display_sotp_waterfall,
    display_backtest_convergence_chart
)

from .step_renderer import render_calculation_step

from .ui_glass_box_registry import get_step_metadata

__all__ = [
    # KPIs & Cards
    "atom_kpi_metric",
    "render_score_gauge",
    "atom_benchmark_card",

    # Charts & Visualizations
    "display_price_chart",
    "display_simulation_chart",
    "display_football_field",
    "display_sensitivity_heatmap",
    "display_sotp_waterfall",
    "display_backtest_convergence_chart",

    # Glass Box Rendering
    "render_calculation_step",
    "get_step_metadata",
]