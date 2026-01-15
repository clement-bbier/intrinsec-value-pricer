"""
core/valuation/strategies/multiples.py
STRATÉGIE DE VALORISATION PAR MULTIPLES — VERSION V2.0 (Sprint 4)
Rôle : Application des médianes sectorielles aux fondamentaux de l'entreprise.
"""

from typing import Dict, Optional
from core.valuation.strategies.abstract import ValuationStrategy
from core.models import (
    CompanyFinancials, DCFParameters, MultiplesValuationResult,
    MultiplesData, TraceHypothesis
)
from core.computation.financial_math import (
    calculate_price_from_pe_multiple,
    calculate_price_from_ev_multiple,
    calculate_triangulated_price
)
from app.ui_components.ui_texts import StrategyInterpretations

class MarketMultiplesStrategy(ValuationStrategy):
    """Implémente la triangulation par multiples comparables."""

    def __init__(self, multiples_data: MultiplesData, glass_box_enabled: bool = True):
        super().__init__(glass_box_enabled)
        self.multiples_data = multiples_data

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> MultiplesValuationResult:
        m = self.multiples_data
        f = financials

        # 1. Signaux de prix individuels (Utilisant les formules atomiques)
        price_pe = calculate_price_from_pe_multiple(f.net_income_ttm or 0.0, m.median_pe, f.shares_outstanding)
        price_ebitda = calculate_price_from_ev_multiple(
            f.ebitda_ttm or 0.0, m.median_ev_ebitda, f.net_debt, f.shares_outstanding,
            f.minority_interests, f.pension_provisions
        )
        price_rev = calculate_price_from_ev_multiple(f.revenue_ttm or 0.0, m.median_ev_rev, f.net_debt, f.shares_outstanding)

        # 2. Triangulation finale (Moyenne des signaux valides)
        signals = {"P/E": price_pe, "EV/EBITDA": price_ebitda, "EV/Revenue": price_rev}
        final_iv = calculate_triangulated_price(signals)

        # 3. Tracabilité Glass Box (Utilisation stricte de ui_texts)
        self._record_steps(f, m, signals, final_iv)

        result = MultiplesValuationResult(
            financials=f, params=params,
            intrinsic_value_per_share=final_iv,
            market_price=f.current_price,
            pe_based_price=price_pe, ebitda_based_price=price_ebitda, rev_based_price=price_rev,
            multiples_data=m,
            calculation_trace=self.calculation_trace
        )

        self.verify_output_contract(result) # Respect du contrat SOLID
        return result

    def _record_steps(self, f, m, signals, final_iv):
        """Enregistre les étapes avec les clés de traduction."""
        self.add_step(
            step_key="RELATIVE_PE", result=signals["P/E"],
            label="Multiples P/E", theoretical_formula="P = (NI * P/E) / Shares",
            numerical_substitution=f"({f.net_income_ttm:,.0f} * {m.median_pe:.1f}) / {f.shares_outstanding:,.0f}",
            interpretation=StrategyInterpretations.RELATIVE_PE.format(val=m.median_pe)
        )
        self.add_step(
            step_key="RELATIVE_EBITDA", result=signals["EV/EBITDA"],
            label="Multiples EV/EBITDA", theoretical_formula="P = (EV_bridge) / Shares",
            numerical_substitution=f"({f.ebitda_ttm:,.0f} * {m.median_ev_ebitda:.1f} - ...) / ...",
            interpretation=StrategyInterpretations.RELATIVE_EBITDA.format(val=m.median_ev_ebitda)
        )
        self.add_step(
            step_key="TRIANGULATION", result=final_iv,
            label="Synthèse Triangulée", theoretical_formula="Average(Signals)",
            numerical_substitution=f"Mean of {len([s for s in signals.values() if s > 0])} valid signals",
            interpretation=StrategyInterpretations.TRIANGULATION_FINAL,
            hypotheses=[TraceHypothesis(name="Peers", value=", ".join([p.ticker for p in m.peers]), source="Yahoo")]
        )