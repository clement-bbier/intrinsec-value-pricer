"""
core/computation/growth.py
MOTEUR DE PROJECTION DES FLUX — VERSION V4.0 (Sprint 2 : Pipeline Unifié)
Rôle : Calcul des trajectoires de croissance multi-phases avec support Glass Box.
Architecture : SOLID Projectors (Simple & Margin Convergence).
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel

# Import depuis core.i18n
from src.i18n import StrategyInterpretations, StrategyFormulas, KPITexts, RegistryTexts
from src.utilities.formatting import format_smart_number
from src.config.constants import GrowthCalculationDefaults

if TYPE_CHECKING:
    from src.domain.models import CompanyFinancials, DCFParameters

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. MODÈLES DE SORTIE (CONTRACTS)
# ==============================================================================

class ProjectionOutput(BaseModel):
    """Contrat de données pour les résultats de projection (Glass Box Ready)."""
    flows: List[float]
    method_label: str = ""
    theoretical_formula: str = ""
    numerical_substitution: str = ""
    interpretation: str = ""

# ==============================================================================
# 2. INTERFACE ABSTRAITE (SOLID)
# ==============================================================================

class FlowProjector(ABC):
    """Interface pour les stratégies de projection de flux (Pattern Strategy)."""

    @abstractmethod
    def project(
        self,
        base_value: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        """Exécute la projection et retourne les flux ainsi que la trace de calcul."""
        pass

# ==============================================================================
# 3. IMPLÉMENTATIONS CONCRÈTES
# ==============================================================================

class SimpleFlowProjector(FlowProjector):
    """
    Projection standard FCF x (1+g)^t.
    Gère le fade-down linéaire vers gn (croissance terminale).
    Adapté aux modèles Standard et Fundamental.
    """

    def project(
        self,
        base_value: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        g = params.growth

        # Utilisation de la logique atomique de project_flows
        flows = project_flows(
            base_flow=base_value,
            years=g.projection_years,
            g_start=g.fcf_growth_rate or 0.0,
            g_term=g.perpetual_growth_rate or 0.0,
            high_growth_years=g.high_growth_years
        )

        # Génération de la trace Glass Box
        # Utilisation des clés i18n centralisées
        formula = StrategyFormulas.FCF_PROJECTION
        base_formatted = format_smart_number(base_value)
        growth_rate = g.fcf_growth_rate or 0.0
        sub = f"{base_formatted} × (1 + {growth_rate:.1%})^{g.projection_years}"
        interp = StrategyInterpretations.PROJ.format(
            years=g.projection_years,
            g=g.fcf_growth_rate or 0
        )

        return ProjectionOutput(
            flows=flows,
            method_label=RegistryTexts.DCF_PROJ_L,
            theoretical_formula=formula,
            numerical_substitution=sub,
            interpretation=interp
        )


class MarginConvergenceProjector(FlowProjector):
    """
    Projection Revenue-Driven avec convergence linéaire des marges.
    Utilisé pour les entreprises à forte croissance (Tech / Growth).
    """

    def project(
        self,
        base_value: float,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ProjectionOutput:
        g = params.growth
        rev_base = base_value

        # Calcul des marges courante et cible
        curr_margin = 0.0
        if financials.fcf_last and rev_base > 0:
            curr_margin = financials.fcf_last / rev_base

        # Marge cible (segment growth)
        target_margin = g.target_fcf_margin if g.target_fcf_margin is not None else GrowthCalculationDefaults.DEFAULT_FCF_MARGIN_TARGET

        # Projection du Chiffre d'Affaires et des FCF (Convergence)
        projected_fcfs = []
        curr_rev = rev_base
        for y in range(1, g.projection_years + 1):
            curr_rev *= (1.0 + (g.fcf_growth_rate or 0.0))
            applied_margin = curr_margin + (target_margin - curr_margin) * (y / g.projection_years)
            projected_fcfs.append(curr_rev * applied_margin)

        # Trace Glass Box spécifique
        formula = r"FCF_t = Rev_t \times [Margin_0 + (Margin_n - Margin_0) \times \frac{t}{n}]"
        sub = KPITexts.SUB_MARGIN_CONV.format(
            curr=curr_margin,
            target=target_margin,
            years=g.projection_years
        )
        interp = StrategyInterpretations.GROWTH_MARGIN

        return ProjectionOutput(
            flows=projected_fcfs,
            method_label=RegistryTexts.GROWTH_MARGIN_L,
            theoretical_formula=formula,
            numerical_substitution=sub,
            interpretation=interp
        )

# ==============================================================================
# 4. LOGIQUE DE CALCUL ATOMIQUE (RÉSILIENTE)
# ==============================================================================

def project_flows(
        base_flow: float,
        years: int,
        g_start: float,
        g_term: float,
        high_growth_years: Optional[int] = 0
) -> List[float]:
    """
    Logiciel de base pour projeter des flux financiers.
    Gère le Plateau (High Growth) puis le Fade-Down linéaire.
    """
    if years <= 0:
        return []

    flows: List[float] = []
    current_flow = base_flow

    safe_high_growth = high_growth_years if high_growth_years is not None else 0
    n_high = max(0, min(safe_high_growth, years))

    gs = g_start if g_start is not None else 0.0
    gt = g_term if g_term is not None else 0.0

    for t in range(1, years + 1):
        if t <= n_high:
            current_g = gs
        else:
            years_remaining = years - n_high
            if years_remaining > 0:
                step_in_fade = t - n_high
                alpha = step_in_fade / years_remaining
                current_g = gs * (1 - alpha) + gt * alpha
            else:
                current_g = gt

        current_flow = current_flow * (1.0 + current_g)
        flows.append(current_flow)

    return flows
