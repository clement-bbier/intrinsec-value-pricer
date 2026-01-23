"""
core/valuation/pipelines.py
PIPELINE DE CALCUL UNIFIÉ (DRY ARCHITECTURE)

Moteur universel pour les modèles de flux actualisés (FCFF, FCFE, DDM).
Gère l'orchestration bifurquée Firm-Level (EV) vs Equity-Level (IV)
en intégrant systématiquement l'ajustement de dilution SBC.

Standard de documentation : NumPy style.
"""

from __future__ import annotations
import logging
from typing import List, Optional, Tuple, Dict

from src.models import (
    CalculationStep, CompanyFinancials, DCFParameters,
    ValuationResult, DCFValuationResult, EquityDCFValuationResult,
    TerminalValueMethod, TraceHypothesis, ValuationMode
)
from src.computation.financial_math import (
    calculate_discount_factors,
    calculate_terminal_value_exit_multiple,
    calculate_terminal_value_gordon,
    calculate_wacc,
    calculate_cost_of_equity,
    calculate_dilution_factor,
    apply_dilution_adjustment
)
from src.computation.growth import FlowProjector, ProjectionOutput
from src.exceptions import CalculationError, ModelDivergenceError
from src.i18n import (
    RegistryTexts, StrategyInterpretations, StrategyFormulas,
    CalculationErrors, KPITexts, StrategySources
)
from src.utilities.formatting import format_smart_number

logger = logging.getLogger(__name__)


class DCFCalculationPipeline:
    """
    Moteur d'exécution universel pour les valorisations par flux.

    Attributes
    ----------
    projector : FlowProjector
        Moteur de projection des flux (Simple, Convergence, etc.).
    mode : ValuationMode
        Mode de valorisation déterminant la branche logique (Entité vs Equity).
    glass_box_enabled : bool
        Active ou désactive la génération de la trace mathématique détaillée.
    """

    def __init__(self, projector: FlowProjector, mode: ValuationMode, glass_box_enabled: bool = True):
        self.projector = projector
        self.mode = mode
        self.glass_box_enabled = glass_box_enabled
        self.calculation_trace: List[CalculationStep] = []

    def run(
            self,
            base_value: float,
            financials: CompanyFinancials,
            params: DCFParameters,
            wacc_override: Optional[float] = None
    ) -> ValuationResult:
        """
        Exécute la chaîne complète de valorisation.

        Parameters
        ----------
        base_value : float
            Valeur d'ancrage du flux (FCF, Dividende, Revenu).
        financials : CompanyFinancials
            Données financières de l'entreprise.
        params : DCFParameters
            Hypothèses de calcul (taux, croissance, dilution).
        wacc_override : float, optional
            Force l'usage d'un WACC spécifique si fourni.

        Returns
        -------
        ValuationResult
            Résultat riche (DCF ou Equity) incluant la trace Glass Box.
        """
        # 1. Détermination du taux d'actualisation (r)
        is_equity_level = self.mode.is_direct_equity
        discount_rate, wacc_ctx = self._resolve_discount_rate(financials, params, is_equity_level, wacc_override)

        # 2. Phase de Projection des flux futurs (FCF_PROJ)
        proj_output = self.projector.project(base_value, financials, params)
        self._add_projection_step(proj_output)
        flows = proj_output.flows

        # 3. Calcul de la Valeur Terminale (TV_GORDON / TV_MULTIPLE)
        tv, _ = self._compute_terminal_value(flows, discount_rate, params)

        # 4. Actualisation et Valeur Totale (NPV_CALC)
        factors, sum_pv, pv_tv, final_value = self._compute_npv_logic(flows, tv, discount_rate, params)

        # 5. Pont vers les fonds propres (EQUITY_BRIDGE / EQUITY_DIRECT)
        equity_val, bridge_shares = self._compute_bridge_by_level(final_value, financials, params, is_equity_level)

        # 6. Calcul final par action avec ajustement Dilution SBC (VALUE_PER_SHARE)
        iv_share = self._compute_value_per_share(equity_val, bridge_shares, financials, params)

        # 7. Collecte des métriques d'audit
        audit_metrics = self._extract_audit_metrics(financials, pv_tv, final_value)

        # 8. Dispatch du contrat de résultat final
        if is_equity_level:
            return EquityDCFValuationResult(
                financials=financials, params=params, intrinsic_value_per_share=iv_share,
                market_price=financials.current_price, cost_of_equity=discount_rate,
                projected_equity_flows=flows, equity_value=equity_val,
                discounted_terminal_value=pv_tv, calculation_trace=self.calculation_trace
            )

        return DCFValuationResult(
            financials=financials, params=params, intrinsic_value_per_share=iv_share,
            market_price=financials.current_price, wacc=discount_rate,
            cost_of_equity=wacc_ctx.cost_of_equity, cost_of_debt_after_tax=wacc_ctx.cost_of_debt_after_tax,
            projected_fcfs=flows, discount_factors=factors, sum_discounted_fcf=sum_pv,
            terminal_value=tv, discounted_terminal_value=pv_tv, enterprise_value=final_value,
            equity_value=equity_val, calculation_trace=self.calculation_trace,
            icr_observed=audit_metrics["icr"], capex_to_da_ratio=audit_metrics["capex_ratio"],
            terminal_value_weight=audit_metrics["tv_weight"], payout_ratio_observed=audit_metrics["payout"],
            leverage_observed=audit_metrics["leverage"]
        )

    # ==========================================================================
    # MÉTHODES DE CALCUL ATOMIQUES (SOLID)
    # ==========================================================================

    def _resolve_discount_rate(self, financials, params, is_equity, override) -> Tuple[float, Optional[object]]:
        """Détermine le taux d'actualisation et enregistre les étapes de trace."""
        if is_equity:
            rate = calculate_cost_of_equity(financials, params)
            r = params.rates
            rf, beta, mrp = (r.risk_free_rate or 0.04), (r.manual_beta or financials.beta or 1.0), (r.market_risk_premium or 0.05)
            sub = StrategySources.MANUAL_OVERRIDE.format(wacc=rate) if r.manual_cost_of_equity else f"{rf:.1%} + {beta:.2f} × {mrp:.1%}"
            self._add_step("KE_CALC", rate, sub, label=RegistryTexts.DCF_KE_L, theoretical_formula=StrategyFormulas.CAPM)
            return rate, None

        wacc_ctx = calculate_wacc(financials, params)
        rate = override if override is not None else wacc_ctx.wacc
        sub = StrategySources.MANUAL_OVERRIDE.format(wacc=rate) if override else \
              f"{wacc_ctx.weight_equity:.1%} × {wacc_ctx.cost_of_equity:.1%} + {wacc_ctx.weight_debt:.1%} × {wacc_ctx.cost_of_debt_after_tax:.1%}"

        self._add_step("WACC_CALC", rate, sub, label=RegistryTexts.DCF_WACC_L, theoretical_formula=StrategyFormulas.WACC)

        if wacc_ctx.beta_adjusted:
            self._add_step(
                "BETA_HAMADA_ADJUSTMENT", wacc_ctx.beta_used, KPITexts.SUB_HAMADA.format(beta=wacc_ctx.beta_used),
                label=StrategyInterpretations.HAMADA_ADJUSTMENT_L, theoretical_formula=StrategyFormulas.HAMADA,
                interpretation=StrategyInterpretations.HAMADA_ADJUSTMENT_D
            )
        return rate, wacc_ctx

    def _compute_value_per_share(self, equity_val: float, shares: float, financials: CompanyFinancials, params: DCFParameters) -> float:
        """Calcule l'IV par action en intégrant l'ajustement de dilution SBC."""
        if shares <= 0:
            raise CalculationError(CalculationErrors.INVALID_SHARES)

        base_iv = equity_val / shares
        rate, years = params.growth.annual_dilution_rate, params.growth.projection_years
        dilution_factor = calculate_dilution_factor(rate, years)
        final_iv = apply_dilution_adjustment(base_iv, dilution_factor)

        if self.glass_box_enabled and dilution_factor > 1.0:
            sub = f"{base_iv:.2f} / (1 + {rate:.2%})^{years}"
            self._add_step(
                "SBC_DILUTION_ADJUSTMENT", final_iv, sub, label="Ajustement Dilution (SBC)",
                theoretical_formula=r"IV_{diluted} = \frac{IV_{initial}}{(1 + d)^t}",
                interpretation=f"La rémunération en actions (SBC) de {rate:.1%} par an réduit la part des actionnaires actuels de {(1 - 1/dilution_factor):.1%} sur l'horizon."
            )
        else:
            sub = f"{format_smart_number(equity_val)} / {shares:,.0f}"
            self._add_step("VALUE_PER_SHARE", final_iv, sub, label=RegistryTexts.DCF_IV_L,
                           theoretical_formula=StrategyFormulas.VALUE_PER_SHARE,
                           interpretation=StrategyInterpretations.IV.format(ticker=financials.ticker))
        return final_iv

    # ==========================================================================
    # HELPERS DE TRACE ET MAPPING (SYNC RÉGISTRE)
    # ==========================================================================

    def _add_step(self, step_key, result, numerical_substitution, label="", theoretical_formula="", interpretation="", hypotheses=None) -> None:
        """Enregistre une étape dans la trace Glass Box."""
        if not self.glass_box_enabled: return
        self.calculation_trace.append(CalculationStep(
            step_id=len(self.calculation_trace) + 1, step_key=step_key, label=label or step_key,
            theoretical_formula=theoretical_formula, hypotheses=hypotheses or [],
            numerical_substitution=numerical_substitution, result=result, interpretation=interpretation
        ))

    def _add_projection_step(self, output: ProjectionOutput) -> None:
        """Trace spécifique pour la phase de projection des flux (FCF_PROJ)."""
        self._add_step("FCF_PROJ", sum(output.flows), output.numerical_substitution,
                       label=output.method_label, theoretical_formula=output.theoretical_formula, interpretation=output.interpretation)

    def _compute_terminal_value(self, flows, discount_rate, params) -> Tuple[float, str]:
        """Gère la TV par Gordon Growth ou Exit Multiple."""
        g = params.growth
        if g.terminal_method == TerminalValueMethod.GORDON_GROWTH:
            p_growth = g.perpetual_growth_rate or 0.0
            if p_growth >= discount_rate: raise ModelDivergenceError(p_growth, discount_rate)
            tv = calculate_terminal_value_gordon(flows[-1], discount_rate, p_growth)
            key, label, formula = "TV_GORDON", RegistryTexts.DCF_TV_GORDON_L, StrategyFormulas.GORDON
            sub = f"({format_smart_number(flows[-1])} × (1 + {p_growth:.1%})) / ({discount_rate:.1%} - {p_growth:.1%})"
        else:
            exit_m = g.exit_multiple_value or 12.0
            tv = calculate_terminal_value_exit_multiple(flows[-1], exit_m)
            key, label, formula = "TV_MULTIPLE", RegistryTexts.DCF_TV_MULT_L, StrategyFormulas.TERMINAL_MULTIPLE
            sub = f"{format_smart_number(flows[-1])} × {exit_m:.1f}"

        self._add_step(key, tv, sub, label, theoretical_formula=formula, interpretation=StrategyInterpretations.TV)
        return tv, key

    def _compute_npv_logic(self, flows, tv, rate, params) -> tuple:
        """Calcule la NPV des flux et de la TV (NPV_CALC)."""
        factors = calculate_discount_factors(rate, params.growth.projection_years)
        sum_pv, pv_tv = sum(f * d for f, d in zip(flows, factors)), (tv * factors[-1])
        final_value = sum_pv + pv_tv
        label = RegistryTexts.DCF_EV_L if not self.mode.is_direct_equity else "Total Equity Value"
        self._add_step("NPV_CALC", final_value, f"{format_smart_number(sum_pv)} + {format_smart_number(pv_tv)}",
                       label=label, theoretical_formula=StrategyFormulas.NPV)
        return factors, sum_pv, pv_tv, final_value

    def _compute_bridge_by_level(self, val, financials, params, is_equity) -> Tuple[float, float]:
        """Bascule entre calcul EV-Bridge ou passage direct Equity."""
        shares = params.growth.manual_shares_outstanding or financials.shares_outstanding
        if is_equity:
            self._add_step("EQUITY_DIRECT", val, f"NPV Directe = {format_smart_number(val)}", label=RegistryTexts.DCF_BRIDGE_L)
            return val, shares

        g = params.growth
        debt, cash = (g.manual_total_debt or financials.total_debt), (g.manual_cash or financials.cash_and_equivalents)
        min_int, pens = (g.manual_minority_interests or financials.minority_interests), (g.manual_pension_provisions or financials.pension_provisions)
        equity_val = val - debt + cash - min_int - pens
        sub = f"{format_smart_number(val)} - {format_smart_number(debt)} + {format_smart_number(cash)}..."
        self._add_step("EQUITY_BRIDGE", equity_val, sub, label=RegistryTexts.DCF_BRIDGE_L,
                       theoretical_formula=StrategyFormulas.EQUITY_BRIDGE, interpretation=StrategyInterpretations.BRIDGE)
        return equity_val, shares

    def _extract_audit_metrics(self, financials, pv_tv, ev) -> Dict[str, Optional[float]]:
        """Génère les métriques pour l'Audit Reliability Score."""
        return {
            "icr": financials.ebit_ttm / financials.interest_expense if financials.interest_expense > 0 else None,
            "capex_ratio": abs(financials.capex / financials.depreciation_and_amortization) if financials.depreciation_and_amortization else None,
            "tv_weight": pv_tv / ev if ev > 0 else None,
            "payout": financials.dividends_total_calculated / financials.net_income_ttm if financials.net_income_ttm else None,
            "leverage": financials.total_debt / financials.ebit_ttm if financials.ebit_ttm else None
        }