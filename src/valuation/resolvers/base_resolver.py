"""
src/valuation/resolvers/base_resolver.py

CENTRAL DATA RESOLVER — THE GHOST HYDRATOR
==========================================
Role: Orchestrates the 'USER > PROVIDER > SYSTEM' priority sequence.
Responsibility: Transforms a sparse Parameters object (Ghost) into a complete,
                calculation-ready object (Solid).
Architecture: Pillar-based Orchestration (SRP).
Style: Numpy docstrings.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config.constants import MacroDefaults, ModelDefaults
from src.models.company import Company, CompanySnapshot
from src.models.parameters.base_parameter import Parameters
from src.models.parameters.strategies import (
    DDMParameters,
    FCFEParameters,
    FCFFGrowthParameters,
    FCFFNormalizedParameters,
    FCFFStandardParameters,
    GrahamParameters,
    RIMParameters,
)

logger = logging.getLogger(__name__)

class Resolver:
    """
    Coordinates the hydration of the valuation input bundle.

    Ensures that the Calculation Engine receives 0% None values by
    arbitrating between UI overrides, Provider data, and System defaults.
    """

    def resolve(self, ghost: Parameters, snap: CompanySnapshot) -> Parameters:
        """
        Main entry point for parameter resolution.

        Parameters
        ----------
        ghost : Parameters
            The input bundle partially filled by the UI (contains Nones).
        snap : CompanySnapshot
            The raw data bag from the Provider (Market/Accounting data).

        Returns
        -------
        Parameters
            A fully hydrated Parameters object ready for calculations.
        """
        logger.debug(f"[Resolver] Starting hydration for {ghost.structure.ticker}")

        # 1. Resolve Identity (Pillar 1)
        ghost.structure = self._resolve_identity(ghost.structure, snap)

        # 2. Resolve Common Levers (Pillar 2: Rates & Capital)
        self._resolve_common(ghost, snap)

        # 3. Resolve Strategy Anchors (Pillar 3: Model Specifics)
        self._resolve_strategy(ghost, snap)

        logger.info(f"[Resolver] Hydration complete for {ghost.structure.ticker}")
        return ghost

    @staticmethod
    def _resolve_identity(identity: Company, snap: CompanySnapshot) -> Company:
        """
        Hydrates Pillar 1 descriptive metadata using User-First logic.

        Note: Identity is immutable during calculation, but vital for reporting.
        """
        return Company(
            ticker=identity.ticker,
            name=identity.name or snap.name or "Unknown Entity",
            sector=identity.sector or snap.sector or "Unknown Sector",
            industry=identity.industry or snap.industry or "Unknown Industry",
            country=identity.country or snap.country or "Unknown",
            currency=identity.currency or snap.currency or "USD",
            current_price=identity.current_price or snap.current_price
        )

    def _resolve_common(self, params: Parameters, snap: CompanySnapshot) -> None:
        """
        Resolves Pillar 2: Universal financial levers (Rates & Capital).
        Modifies params in-place.
        """
        cap = params.common.capital
        rates = params.common.rates

        # --- Capital Structure (Pick Logic) ---
        cap.total_debt = self._pick(cap.total_debt, snap.total_debt, ModelDefaults.DEFAULT_TOTAL_DEBT)
        cap.cash_and_equivalents = self._pick(
            cap.cash_and_equivalents, snap.cash_and_equivalents,
            ModelDefaults.DEFAULT_CASH_EQUIVALENTS,
        )
        cap.minority_interests = self._pick(
            cap.minority_interests, snap.minority_interests,
            ModelDefaults.DEFAULT_MINORITY_INTERESTS,
        )
        cap.pension_provisions = self._pick(
            cap.pension_provisions, snap.pension_provisions,
            ModelDefaults.DEFAULT_PENSION_PROVISIONS,
        )
        cap.shares_outstanding = self._pick(
            cap.shares_outstanding, snap.shares_outstanding,
            ModelDefaults.DEFAULT_SHARES_OUTSTANDING,
        )

        # Dilution is rarely in provider data, usually a System Default or User Override
        cap.annual_dilution_rate = self._pick(
            cap.annual_dilution_rate, None,
            ModelDefaults.DEFAULT_ANNUAL_DILUTION_RATE,
        )

        # --- Rates & Risk ---
        rates.risk_free_rate = self._pick(
            rates.risk_free_rate, snap.risk_free_rate,
            MacroDefaults.DEFAULT_RISK_FREE_RATE,
        )
        rates.market_risk_premium = self._pick(
            rates.market_risk_premium, snap.market_risk_premium,
            MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM,
        )
        rates.beta = self._pick(rates.beta, snap.beta, ModelDefaults.DEFAULT_BETA)
        rates.tax_rate = self._pick(rates.tax_rate, snap.tax_rate, MacroDefaults.DEFAULT_TAX_RATE)

        # AAA Yield logic (Specific to Graham, but stored in common rates for consistency)
        rates.corporate_aaa_yield = self._pick(
            rates.corporate_aaa_yield, snap.corporate_aaa_yield,
            MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD,
        )

        # Implied Cost of Debt (Kd) calculation if not provided by User
        if rates.cost_of_debt is None:
            rates.cost_of_debt = self._calculate_synthetic_kd(snap, rates.risk_free_rate)

    def _resolve_strategy(self, params: Parameters, snap: CompanySnapshot) -> None:
        """
        Injects model-specific anchors (TTM data) for Pillar 3.
        Auto-detects the strategy type to apply the correct logic.
        """
        strat = params.strategy

        # --- FCFF STANDARD ---
        if isinstance(strat, FCFFStandardParameters):
            # Le FCFF Standard a besoin du FCF TTM comme point de départ
            strat.fcf_anchor = self._pick(strat.fcf_anchor, snap.fcf_ttm, ModelDefaults.DEFAULT_FCF_TTM)
            # Il n'utilise PAS ebit_ttm ni capex_ttm directement dans les paramètres de la stratégie
            # (Ces données servent au WACC qui est déjà résolu dans _resolve_common)

        # --- FCFF NORMALIZED ---
        elif isinstance(strat, FCFFNormalizedParameters):
            # Besoin du FCF lissé (ou TTM par défaut)
            strat.fcf_norm = self._pick(strat.fcf_norm, snap.fcf_ttm, ModelDefaults.DEFAULT_FCF_TTM)
            # Idem, pas d'EBIT norm ici

        # --- FCFF GROWTH (Top-Down) ---
        elif isinstance(strat, FCFFGrowthParameters):
            # Lui a besoin du CA pour projeter les marges
            strat.revenue_ttm = self._pick(strat.revenue_ttm, snap.revenue_ttm, 0.0)
            # Et de l'EBITDA/EBIT pour la marge initiale
            if hasattr(strat, 'ebit_ttm'):
                 strat.ebit_ttm = self._pick(strat.ebit_ttm, snap.ebit_ttm, 0.0)

        # --- DDM ---
        elif isinstance(strat, DDMParameters):
            strat.dividend_per_share = self._pick(
                strat.dividend_per_share, snap.dividend_share,
                ModelDefaults.DEFAULT_DIVIDEND_PS,
            )
            strat.net_income_ttm = self._pick(strat.net_income_ttm, snap.net_income_ttm, 0.0)

        # --- RIM (Banks) ---
        elif isinstance(strat, RIMParameters):
            strat.book_value_anchor = self._pick(
                strat.book_value_anchor, snap.book_value_ps,
                ModelDefaults.DEFAULT_BOOK_VALUE_PS,
            )
            strat.net_income_norm = self._pick(strat.net_income_norm, snap.net_income_ttm, 0.0)
            strat.persistence_factor = self._pick(
                strat.persistence_factor, None,
                ModelDefaults.DEFAULT_PERSISTENCE_FACTOR,
            )

        # --- FCFE ---
        elif isinstance(strat, FCFEParameters):
            strat.fcfe_anchor = self._pick(strat.fcfe_anchor, snap.net_income_ttm, ModelDefaults.DEFAULT_NET_INCOME_TTM)
            strat.net_income_ttm = self._pick(strat.net_income_ttm, snap.net_income_ttm, 0.0)

        # --- GRAHAM ---
        elif isinstance(strat, GrahamParameters):
            strat.eps_normalized = self._pick(strat.eps_normalized, snap.eps_ttm, ModelDefaults.DEFAULT_EPS_TTM)

    @staticmethod
    def _pick(user_val: Any | None, provider_val: Any | None, fallback: Any) -> Any:
        """
        Enforces the 'USER > PROVIDER > SYSTEM' priority chain.

        Returns
        -------
        Any
            The first non-None value found in the chain.
        """
        if user_val is not None:
            return user_val
        return provider_val if provider_val is not None else fallback

    @staticmethod
    def _calculate_synthetic_kd(snap: CompanySnapshot, rf: float) -> float:
        """
        Calculates an implied cost of debt (Kd).

        Logic: Interest Expense / Total Debt.
        Fallback: Risk Free Rate + 200bps spread if data is missing or invalid.
        """
        # Safety check against zero division or missing data
        if snap.total_debt and snap.total_debt > 0 and snap.interest_expense:
            implied_kd = abs(snap.interest_expense) / snap.total_debt
            # Cap realistic boundaries (e.g., Kd shouldn't be 50% or 0.1%)
            if 0.01 < implied_kd < 0.20:
                return implied_kd

        # Fallback spread
        return rf + 0.02
