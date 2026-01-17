"""
app/ui/result_tabs/components/
Composants UI réutilisables pour les onglets.
"""

from app.ui.result_tabs.components.step_renderer import render_calculation_step
from app.ui.result_tabs.components.kpi_cards import format_smart_number, render_kpi_metric

__all__ = [
    "render_calculation_step",
    "format_smart_number",
    "render_kpi_metric",
]
