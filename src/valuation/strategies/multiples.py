"""
core/valuation/strategies/multiples.py
STRATÉGIE DE VALORISATION PAR MULTIPLES — VERSION V2.0 (Sprint 4)
Rôle : Application des médianes sectorielles aux fondamentaux de l'entreprise.
"""

from typing import Dict, Optional
from src.valuation.strategies.abstract import ValuationStrategy
from src.utilities.formatting import format_smart_number
from src.domain.models import (
    CompanyFinancials, DCFParameters, MultiplesValuationResult,
    MultiplesData, TraceHypothesis
)
from src.computation.financial_math import (
    calculate_price_from_pe_multiple,
    calculate_price_from_ev_multiple,
    calculate_triangulated_price
)
# Import depuis core.i18n
from src.i18n import StrategyInterpretations, StrategyFormulas

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
        ni_formatted = format_smart_number(f.net_income_ttm)
        shares_formatted = f"{f.shares_outstanding:,.0f}"
        sub_pe = f"({ni_formatted} × {m.median_pe:.1f}) / {shares_formatted}"

        self.add_step(
            step_key="RELATIVE_PE", result=signals["P/E"],
            label="Multiples P/E", theoretical_formula=r"P/E = \frac{Price}{EPS}",
            numerical_substitution=sub_pe,
            interpretation=StrategyInterpretations.RELATIVE_PE.format(val=m.median_pe)
        )
        ebitda_formatted = format_smart_number(f.ebitda_ttm)
        ev_ebitda_formatted = f"{m.median_ev_ebitda:.1f}"
        sub_ebitda = f"({ebitda_formatted} × {ev_ebitda_formatted}) / {f.shares_outstanding:,.0f}"

        self.add_step(
            step_key="RELATIVE_EBITDA", result=signals["EV/EBITDA"],
            label="Multiples EV/EBITDA", theoretical_formula=r"EV/EBITDA = \frac{Enterprise\ Value}{EBITDA}",
            numerical_substitution=sub_ebitda,
            interpretation=StrategyInterpretations.RELATIVE_EBITDA.format(val=m.median_ev_ebitda)
        )
        valid_signals = [s for s in signals.values() if s > 0]
        num_signals = len(valid_signals)
        sub_triangulation = StrategyInterpretations.TRIANGULATION_SUB.format(count=num_signals)

        self.add_step(
            step_key="TRIANGULATION", result=final_iv,
            label="Synthèse Triangulée", theoretical_formula=r"IV = \frac{\sum Signals}{N}",
            numerical_substitution=sub_triangulation,
            interpretation=StrategyInterpretations.TRIANGULATION_FINAL,
            hypotheses=[TraceHypothesis(name="Peers", value=", ".join([p.ticker for p in m.peers]), source="Yahoo")]
        )
