"""
infra/macro/default_macro_provider.py
"""

from infra.ref_data.country_matrix import get_country_context
from src.models.company import CompanySnapshot

from .base_macro_provider import MacroDataProvider


class DefaultMacroProvider(MacroDataProvider):
    """
    Standard implementation using the local Country Matrix and Yahoo rates.
    """

    def hydrate_macro_data(self, snapshot: CompanySnapshot) -> CompanySnapshot:
        # 1. Resolve country context using the local matrix
        context = get_country_context(snapshot.country)

        # 2. Direct injection into the Snapshot (No calculation here)
        snapshot.risk_free_rate = context.get("risk_free_rate")
        snapshot.market_risk_premium = context.get("market_risk_premium")
        snapshot.tax_rate = context.get("tax_rate")
        snapshot.perpetual_growth_rate = context.get("inflation_rate")

        return snapshot
