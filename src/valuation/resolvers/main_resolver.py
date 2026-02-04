"""
src/valuation/resolvers/main_resolver.py

VALUATION RESOLVER — The Intelligence Layer
===========================================
Role: Resolves data conflicts and hydrates the Parameters ghost object.
Responsibility: Implements the 'USER > PROVIDER > FALLBACK' priority sequence.

Architecture: Orchestrator Pattern with Static Utility Mappers.
Style: Numpy docstrings.
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from src.models.parameters.base_parameter import Parameters
from src.models.company import Company, CompanySnapshot
from src.models.parameters.strategies import (
    FCFFStandardParameters, DDMParameters, RIMParameters,
    FCFEParameters, GrahamParameters
)

logger = logging.getLogger(__name__)


class ValuationResolver:
    """
    Coordinates the hydration of the valuation input bundle.

    This class ensures that the Calculation Engine receives a 100% complete
    Parameters object by merging UI overrides with raw API data.
    """

    def resolve(self, ghost: Parameters, snapshot: CompanySnapshot) -> Parameters:
        """
        Main entry point for parameter resolution.

        Parameters
        ----------
        ghost : Parameters
            The input bundle partially filled by the UI.
        snapshot : CompanySnapshot
            The raw data bag from the Provider.

        Returns
        -------
        Parameters
            A fully hydrated Parameters object ready for the Engine.
        """
        # 1. Resolve Identity (Pillar 1)
        ghost.structure = self._resolve_identity(ghost.structure, snapshot)

        # 2. Resolve Common Levers (Pillar 2)
        self._resolve_common(ghost, snapshot)

        # 3. Resolve Strategy Anchors (Pillar 3)
        self._resolve_strategy(ghost, snapshot)

        return ghost

    @staticmethod
    def _resolve_identity(identity: Company, snap: CompanySnapshot) -> Company:
        """
        Hydrates Pillar 1 descriptive metadata using a 'User First' approach.

        Parameters
        ----------
        identity : Company
            The existing identity object (likely containing only the Ticker).
        snap : CompanySnapshot
            The fresh data from the provider.

        Returns
        -------
        Company
            A completed Company identity object.
        """
        return Company(
            ticker=identity.ticker,
            name=identity.name or snap.name,
            sector=identity.sector or snap.sector,
            industry=identity.industry or snap.industry,
            country=identity.country or snap.country,
            currency=identity.currency or snap.currency,
            current_price=identity.current_price or snap.current_price
        )

    def _resolve_common(self, params: Parameters, snap: CompanySnapshot) -> None:
        """
        Resolves Pillar 2: Shared financial levers (Rates & Capital).

        Maps data to FinancialRatesParameters and CapitalStructureParameters.
        """
        # --- Capital Structure ---
        cap = params.common.capital
        cap.total_debt = self._pick(cap.total_debt, snap.total_debt, 0.0)
        cap.cash_and_equivalents = self._pick(cap.cash_and_equivalents, snap.cash_and_equivalents, 0.0)
        cap.minority_interests = self._pick(cap.minority_interests, snap.minority_interests, 0.0)
        cap.pension_provisions = self._pick(cap.pension_provisions, snap.pension_provisions, 0.0)
        cap.shares_outstanding = self._pick(cap.shares_outstanding, snap.shares_outstanding, 1.0)

        # --- Rates & Risk ---
        rates = params.common.rates
        rates.risk_free_rate = self._pick(rates.risk_free_rate, snap.risk_free_rate, 0.04)
        rates.market_risk_premium = self._pick(rates.market_risk_premium, snap.market_risk_premium, 0.05)
        rates.beta = self._pick(rates.beta, snap.beta, 1.0)
        rates.tax_rate = self._pick(rates.tax_rate, snap.tax_rate, 0.25)
        rates.corporate_aaa_yield = self._pick(rates.corporate_aaa_yield, snap.corporate_aaa_yield, 0.05)

        # Resolve Synthetic Cost of Debt if missing
        if rates.cost_of_debt is None:
            rates.cost_of_debt = self._calculate_synthetic_kd(snap)

    def _resolve_strategy(self, params: Parameters, snap: CompanySnapshot) -> None:
        """
        Resolves Pillar 3: Model-specific anchors based on the active strategy.

        Only hydrates the fields relevant to the selected Methodology.
        """
        strat = params.strategy

        if isinstance(strat, FCFFStandardParameters):
            strat.fcf_anchor = self._pick(strat.fcf_anchor, snap.fcf_ttm, 0.0)

        elif isinstance(strat, DDMParameters):
            strat.dividend_per_share = self._pick(strat.dividend_per_share, snap.dividend_share, 0.0)

        elif isinstance(strat, RIMParameters):
            strat.book_value_anchor = self._pick(strat.book_value_anchor, snap.book_value_ps, 0.0)

        elif isinstance(strat, FCFEParameters):
            strat.fcfe_anchor = self._pick(strat.fcfe_anchor, snap.net_income_ttm, 0.0)

        elif isinstance(strat, GrahamParameters):
            strat.eps_normalized = self._pick(strat.eps_normalized, snap.eps_ttm, 0.0)

    @staticmethod
    def _pick(user_val: Optional[Any], provider_val: Optional[Any], fallback: Any) -> Any:
        """Enforces the 'USER > PROVIDER > FALLBACK' priority chain."""
        if user_val is not None:
            return user_val
        return provider_val if provider_val is not None else fallback

    @staticmethod
    def _calculate_synthetic_kd(snap: CompanySnapshot) -> float:
        """Calculates an implied cost of debt (Kd) based on interest coverage."""
        if snap.total_debt and snap.total_debt > 0 and snap.interest_expense:
            return abs(snap.interest_expense) / snap.total_debt
        return (snap.risk_free_rate or 0.04) + 0.02