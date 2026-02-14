"""
app/views/inputs/strategies/__init__.py
Index of valuation strategy views.
"""

from .ddm_view import DDMView
from .fcfe_view import FCFEView
from .fcff_growth_view import FCFFGrowthView
from .fcff_normalized_view import FCFFNormalizedView
from .fcff_standard_view import FCFFStandardView
from .graham_value_view import GrahamValueView
from .rim_bank_view import RIMBankView

# Mapping for the factory
STRATEGY_VIEW_MAP = {
    "DDM": DDMView,
    "FCFE": FCFEView,
    "FCFF_STANDARD": FCFFStandardView,
    "FCFF_GROWTH": FCFFGrowthView,
    "FCFF_NORMALIZED": FCFFNormalizedView,
    "RIM_BANK": RIMBankView,
    "GRAHAM": GrahamValueView,
}
