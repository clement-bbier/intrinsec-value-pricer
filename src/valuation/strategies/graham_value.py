"""
src/valuation/strategies/graham_value.py

GRAHAM INTRINSIC VALUE STRATEGY
===============================
Role: Value Investing Engine based on Benjamin Graham's Revised Formula (1974).
Academic Reference: The Intelligent Investor / Security Analysis.
Economic Domain: Defensive / Passive Investors / Mature Firms.
Logic: Calculates Intrinsic Value using normalized EPS and AAA Bond Yields.
Architecture: IValuationRunner implementation.

Standard: Institutional Grade (Glass Box, i18n, Type-Safe).
"""

from __future__ import annotations

import numpy as np

# Config & i18n
from src.config.constants import MacroDefaults, ModelDefaults
from src.models.company import Company
from src.models.enums import ValuationMethodology
from src.models.glass_box import CalculationStep
from src.models.parameters.base_parameter import Parameters
from src.models.results.base_result import Results
from src.models.results.common import CommonResults, ResolvedCapital, ResolvedRates
from src.models.results.options import ExtensionBundleResults
from src.models.results.strategies import GrahamResults

# Models Results (Nested Architecture)
from src.models.valuation import ValuationRequest, ValuationResult

# Libraries (DRY Logic)
from src.valuation.library.graham import GrahamLibrary

# CORRECTIF 1: On utilise IValuationRunner pour la cohérence avec standard_fcff.py
from src.valuation.strategies.interface import IValuationRunner


class GrahamNumberStrategy(IValuationRunner):
    """
    Graham Strategy (Revised 1974 Formula).

    A conservative valuation model that anchors on Normalized Earnings (EPS)
    and adjusts for the current Corporate AAA Bond Yield environment.

    Formula: IV = (EPS * (8.5 + 2*g) * 4.4) / Y
    """

    def __init__(self) -> None:
        self._glass_box: bool = True

    @property
    def glass_box_enabled(self) -> bool:
        return self._glass_box

    @glass_box_enabled.setter
    def glass_box_enabled(self, value: bool) -> None:
        self._glass_box = value

    def execute(self, financials: Company, params: Parameters) -> ValuationResult:
        """
        Executes the Graham valuation sequence.
        """
        steps: list[CalculationStep] = []

        # --- STEP 1: Intrinsic Value Calculation ---
        # Delegate pure math to the Library
        iv_per_share, step_graham = GrahamLibrary.compute_intrinsic_value(params)

        if self._glass_box:
            steps.append(step_graham)

        # --- RESULT RECONSTRUCTION ---
        # We need to extract the inputs used to populate the Audit/Results object.

        # Shortcuts for readability
        s = params.strategy
        r = params.common.rates

        # CORRECTIF 2: Suppression de 'g_param = params.growth' qui n'existe PAS.
        # La croissance est gérée via la stratégie ou les defaults.

        # 1. Inputs Extraction (for Audit Traceability)
        # Note: We fallback to defaults to ensure safety if params are partial
        eps_used = s.eps_normalized or financials.eps_ttm or 0.0

        # Growth: Graham uses a specific growth estimate or the generic one
        # CORRECTIF 3: Accès direct propre sans passer par un objet 'growth' inexistant
        growth_used = s.growth_estimate if s.growth_estimate is not None else ModelDefaults.DEFAULT_GROWTH_RATE

        # Yield: Critical part of the 1974 formula
        aaa_yield = r.corporate_aaa_yield or MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD

        # 2. Multiplier Calculation (M = 8.5 + 2*g)
        # Computed here for the "Graham Multiplier" audit KPI
        # Formula uses growth as an integer (e.g. 10 for 10%), so we multiply decimal by 100
        graham_multiplier = 8.5 + 2.0 * (growth_used * 100.0)

        # --- OUTPUT PACKAGING ---

        # A. Rates
        # Graham doesn't use WACC. The discount mechanism is the AAA Yield.
        res_rates = ResolvedRates(
            cost_of_equity=aaa_yield, # Proxy for opportunity cost
            cost_of_debt_after_tax=0.0,
            wacc=aaa_yield, # Proxy
            corporate_aaa_yield=aaa_yield
        )

        # B. Capital
        # Graham is an Equity-Per-Share model. We reconstruct Total Equity and Implied EV.
        shares = params.common.capital.shares_outstanding or ModelDefaults.DEFAULT_SHARES_OUTSTANDING
        equity_value_total = iv_per_share * shares

        # Reconstruct EV = Equity + Net Debt
        debt = params.common.capital.total_debt or 0.0
        cash = params.common.capital.cash_and_equivalents or 0.0
        net_debt = debt - cash

        res_capital = ResolvedCapital(
            market_cap=shares * (financials.current_price or 0.0),
            enterprise_value=equity_value_total + net_debt, # Implied EV
            net_debt_resolved=net_debt,
            equity_value_total=equity_value_total
        )

        # C. Common Results
        common_res = CommonResults(
            rates=res_rates,
            capital=res_capital,
            intrinsic_value_per_share=iv_per_share, # CORRECTIF 4: Pydantic recevra bien la valeur ici
            upside_pct=((iv_per_share - (financials.current_price or 0.0)) / (financials.current_price or 1.0)) if financials.current_price else 0.0,
            bridge_trace=steps if self._glass_box else []
        )

        # D. Strategy Specific Results (Graham)
        strategy_res = GrahamResults(
            eps_used=eps_used,
            growth_estimate=growth_used,
            aaa_yield_used=aaa_yield,
            graham_multiplier=graham_multiplier,
            strategy_trace=[] # Main logic is in bridge_trace
        )

        return ValuationResult(
            request=ValuationRequest(
                mode=ValuationMethodology.GRAHAM,
                parameters=params
            ),
            results=Results(
                common=common_res,
                strategy=strategy_res, # Polymorphic slot
                extensions=ExtensionBundleResults()
            )
        )

    @staticmethod
    def execute_stochastic(_financials: Company, params: Parameters, vectors: dict[str, np.ndarray]) -> np.ndarray:
        """
        Vectorized Graham Formula Execution for Monte Carlo.

        Formula: IV = (EPS * (8.5 + 2g) * 4.4) / AAA_Yield

        Parameters
        ----------
        _financials : Company
            Static financial data (Unused, prefix '_' for linter compliance).
        params : Parameters
            Static parameters (AAA yield).
        vectors : Dict[str, np.ndarray]
            Dictionary containing stochastic arrays:
            - 'base_flow': EPS vector (Earnings Power).
            - 'growth': Growth rate vector (decimal).

        Returns
        -------
        np.ndarray
            Array of Intrinsic Values per Share.
        """
        # 1. Unpack Vectors
        eps_vec = vectors['base_flow'] # Maps to EPS in MC engine logic
        g_vec = vectors['growth']      # Maps to growth_estimate

        # Graham uses AAA Yield, not WACC/Ke.
        # Ideally MC should shock AAA yield too, but usually it shocks Beta/MRP.
        # We'll take the static AAA yield from params or fallback to vectors['wacc'] if you want it dynamic.
        # Let's use the static parameter for consistency unless you explicitely shock yield.
        aaa_yield = params.common.rates.corporate_aaa_yield or MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD

        # Guardrail against division by zero
        if aaa_yield <= 0.001:
            aaa_yield = 0.044

        # 2. Formula Vectorized
        # IV = (EPS * (8.5 + 2g) * 4.4) / Y
        # Note: g is entered as decimal (0.05) but Graham formula expects integer (5) -> multiply by 100.

        multiplier = 8.5 + 2.0 * (g_vec * 100.0)

        # The 4.4 factor is the base AAA yield normalizer.
        # Y is typically entered as percent (e.g. 4.4), so we multiply yield decimal by 100

        intrinsic_values = (eps_vec * multiplier * 4.4) / (aaa_yield * 100.0)

        return intrinsic_values
