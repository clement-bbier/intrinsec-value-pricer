"""
core/valuation/sotp_engine.py
MOTEUR DE SOMMATION PAR SEGMENTS (SOTP) — VERSION V13.0
Sprint 6 : Valorisation des conglomérats.
Rôle : Consolidation des Enterprise Values (EV) par Business Unit et application de la décote.
Standards : SOLID, Glass Box, i18n Secured.
"""

from typing import List, Tuple
from core.models import SOTPParameters, CalculationStep, TraceHypothesis
from app.ui_components.ui_texts import SOTPTexts


def run_sotp_valuation(params: SOTPParameters) -> Tuple[float, List[CalculationStep]]:
    """
    Calcule la Valeur d'Entreprise (EV) totale par sommation des segments (ST 2.2).
    Utilise exclusivement ui_texts.py pour la transparence Glass Box.
    """
    # 1. Clause de garde : Retour immédiat si le mode est désactivé ou vide
    if not params.enabled or not params.segments:
        return 0.0, []

    # 2. Sommation brute des Enterprise Values des segments
    raw_ev_sum = sum(seg.enterprise_value for seg in params.segments)

    # 3. Application de la décote de conglomérat
    # Formule institutionnelle : EV_final = Sum(EV_i) * (1 - Décote)
    discount_factor = (1.0 - params.conglomerate_discount)
    final_ev = raw_ev_sum * discount_factor

    # 4. Génération de la Preuve de Calcul (Glass Box)
    step = CalculationStep(
        step_id=1,
        step_key="SOTP_CONSOLIDATION",
        label=SOTPTexts.STEP_LABEL_CONSOLIDATION,
        theoretical_formula=r"EV_{Total} = \left( \sum_{i=1}^{n} EV_{segment, i} \right) \times (1 - \text{Discount})",
        hypotheses=[
            TraceHypothesis(
                name=SOTPTexts.LBL_SEGMENT_COUNT,
                value=len(params.segments),
                source="Expert"
            ),
            TraceHypothesis(
                name=SOTPTexts.LBL_RAW_EV_SUM,
                value=raw_ev_sum,
                unit="currency"
            ),
            TraceHypothesis(
                name=SOTPTexts.LBL_DISCOUNT,
                value=params.conglomerate_discount,
                unit="%"
            )
        ],
        numerical_substitution=f"{raw_ev_sum:,.2f} × (1 - {params.conglomerate_discount:.2%})",
        result=final_ev,
        unit="currency",
        interpretation=SOTPTexts.INTERP_CONSOLIDATION.format(count=len(params.segments))
    )

    return final_ev, [step]