"""
core/valuation/sotp_engine.py
MOTEUR DE SOMMATION PAR SEGMENTS (SOTP) — VERSION V13.1
Sprint 6 : Valorisation des conglomérats.
Rôle : Consolidation des EV et application de l'Equity Bridge global.
Standards : SOLID, Glass Box, i18n Secured.
"""

from typing import List, Tuple
from src.domain.models import SOTPParameters, CompanyFinancials, CalculationStep, TraceHypothesis
# DT-001/002: Import depuis core.i18n
from src.i18n import SOTPTexts, RegistryTexts, KPITexts


def run_sotp_valuation(
    params: SOTPParameters,
    financials: CompanyFinancials
) -> Tuple[float, List[CalculationStep]]:
    """
    Orchestre la valorisation complète SOTP :
    1. Sommation des segments et décote (EV)
    2. Passage à la valeur actionnariale (Equity Bridge).
    """
    steps = []

    # --- ÉTAPE 1 : CONSOLIDATION DE L'EV ---
    if not params.enabled or not params.segments:
        return 0.0, []

    raw_ev_sum = sum(seg.enterprise_value for seg in params.segments)
    discount_factor = (1.0 - params.conglomerate_discount)
    consolidated_ev = raw_ev_sum * discount_factor

    ev_step = CalculationStep(
        step_id=1,
        step_key="SOTP_EV_CONSOLIDATION",
        label=SOTPTexts.STEP_LABEL_CONSOLIDATION,
        theoretical_formula=r"EV_{Total} = \left( \sum EV_{segments} \right) \times (1 - \text{Discount})",
        hypotheses=[
            TraceHypothesis(name=SOTPTexts.LBL_SEGMENT_COUNT, value=len(params.segments), source="Expert"),
            TraceHypothesis(name=SOTPTexts.LBL_RAW_EV_SUM, value=raw_ev_sum, unit="currency"),
            TraceHypothesis(name=SOTPTexts.LBL_DISCOUNT, value=params.conglomerate_discount, unit="%")
        ],
        numerical_substitution=f"{raw_ev_sum:,.2f} × (1 - {params.conglomerate_discount:.2%})",
        result=consolidated_ev,
        unit="currency",
        interpretation=SOTPTexts.INTERP_CONSOLIDATION.format(count=len(params.segments))
    )
    steps.append(ev_step)

    # --- ÉTAPE 2 : EQUITY BRIDGE CONSOLIDÉ (ST 2.3) ---
    # On récupère les ajustements globaux du bilan consolidé
    debt = financials.total_debt
    cash = financials.cash_and_equivalents
    minorities = financials.minority_interests
    pensions = financials.pension_provisions

    # Formule : Equity Value = EV - Dette + Cash - Minoritaires - Pensions
    equity_value = consolidated_ev - debt + cash - minorities - pensions

    bridge_step = CalculationStep(
        step_id=2,
        step_key="SOTP_EQUITY_BRIDGE",
        label=RegistryTexts.DCF_BRIDGE_L, # Réutilisation du label standard pour la cohérence
        theoretical_formula=r"Equity Value = EV - Debt + Cash - Minorities - Pensions",
        hypotheses=[
            TraceHypothesis(name=KPITexts.LABEL_DEBT, value=debt, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_CASH, value=cash, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_MINORITIES, value=minorities, unit="currency", source="Yahoo"),
            TraceHypothesis(name=KPITexts.LABEL_PENSIONS, value=pensions, unit="currency", source="Yahoo")
        ],
        numerical_substitution=(
            f"{consolidated_ev:,.2f} - {debt:,.2f} + {cash:,.2f} "
            f"- {minorities:,.2f} - {pensions:,.2f}"
        ),
        result=equity_value,
        unit="currency",
        interpretation=RegistryTexts.DCF_BRIDGE_D # Note pédagogique sur l'ajustement structurel
    )
    steps.append(bridge_step)

    return equity_value, steps
