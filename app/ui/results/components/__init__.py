"""
app/ui/result_tabs/components/
Composants UI réutilisables pour les onglets.
"""

from app.ui.results.components.step_renderer import render_calculation_step
from app.ui.results.components.kpi_cards import render_kpi_metric
from src.utilities.formatting import format_smart_number

__all__ = [
    "render_calculation_step",
    "format_smart_number",
    "render_kpi_metric",
]
