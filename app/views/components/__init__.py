"""
app/views/components/__init__.py
Exposition des composants atomiques de l'interface.
"""

from .step_renderer import render_calculation_step
from .ui_charts import (
    display_backtest_convergence_chart,
    display_football_field,
    display_scenario_comparison_chart,
    display_sector_comparison_chart,
    display_simulation_chart,
    display_sotp_waterfall,
)
from .ui_kpis import atom_benchmark_card, atom_kpi_metric

__all__ = [
    "atom_kpi_metric",
    "atom_benchmark_card",
    "display_football_field",
    "display_simulation_chart",
    "display_sector_comparison_chart",
    "display_sotp_waterfall",
    "display_backtest_convergence_chart",
    "display_scenario_comparison_chart",
    "render_calculation_step",
]
