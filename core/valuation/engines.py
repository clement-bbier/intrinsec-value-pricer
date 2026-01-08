"""
core/valuation/engines.py

ROUTEUR CENTRAL DES MOTEURS DE VALORISATION
Version : V2.5 — Monte Carlo Universel (DCF + RIM) & Fix Pydantic

Responsabilités :
- Orchestrer une valorisation déterministe ou stochastique
- Appliquer strictement le contrat de sortie
- Gérer les erreurs via le système de Diagnostic V3
- Fournir le registre des stratégies pour l'historique
"""

import logging
import traceback
from typing import Dict, Type, Optional

# NOUVEAU SYSTÈME D'ERREUR (V3)
from core.exceptions import ValuationException, DiagnosticEvent, SeverityLevel, DiagnosticDomain
# ANCIEN SYSTÈME (Pour compatibilité interne si besoin, mais on va wrapper)
from core.exceptions import CalculationError

from core.models import (
    ValuationRequest,
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    ValuationResult
)

# Import des stratégies concrètes
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.rim_banks import RIMBankingStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy

# Nouvelle stratégie générique
from core.valuation.strategies.monte_carlo import MonteCarloGenericStrategy

logger = logging.getLogger(__name__)


# ============================================================
# 1. REGISTRE NORMATIF (CRITIQUE POUR HISTORICAL.PY)
# ============================================================
# Ce dictionnaire permet à d'autres modules (historical.py) de trouver
# dynamiquement la classe à utiliser sans faire de if/else géant.

STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.FCFF_TWO_STAGE: StandardFCFFStrategy,
    ValuationMode.FCFF_NORMALIZED: FundamentalFCFFStrategy,
    ValuationMode.FCFF_REVENUE_DRIVEN: RevenueBasedStrategy,
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,
}


# ============================================================
# 2. POINT D’ENTRÉE PRINCIPAL (COMPATIBLE V3)
# ============================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute une valorisation en utilisant le registre et le nouveau système d'erreurs.
    """

    logger.info(
        "[Engine] Valuation requested | ticker=%s | mode=%s",
        request.ticker,
        request.mode.value
    )

    # A. Sélection de la Stratégie via le Registry (Plus robuste que if/elif)
    strategy_cls = STRATEGY_REGISTRY.get(request.mode)

    if not strategy_cls:
        # Erreur riche (V3)
        raise ValuationException(DiagnosticEvent(
            code="UNKNOWN_STRATEGY",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM,
            message=f"Le mode de valorisation '{request.mode}' n'est pas enregistré dans le moteur.",
            remediation_hint="Contactez le support, c'est une erreur de configuration interne."
        ))

    # B. Instanciation de la stratégie
    # Gestion du Monte Carlo (Décorateur / Wrapper)
    strategy = None

    if params.enable_monte_carlo:
        logger.info(
            "[Engine] Monte Carlo flag = %s | mode=%s",
            params.enable_monte_carlo,
            request.mode.value
        )
        # Liste blanche des modes compatibles Monte Carlo
        SUPPORTED_MC_MODES = [
            ValuationMode.FCFF_TWO_STAGE,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.FCFF_REVENUE_DRIVEN,
            ValuationMode.RESIDUAL_INCOME_MODEL,
        ]

        if request.mode in SUPPORTED_MC_MODES:
            logger.info("Activation Monte Carlo pour %s", request.mode.value)
            # On injecte la classe cible dans le wrapper générique
            # Monte Carlo devient la stratégie principale, elle pilotera les calculs sous-jacents
            strategy = MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
        else:
            logger.warning(f"Monte Carlo ignoré pour le mode {request.mode} (non supporté)")
            strategy = strategy_cls()
    else:
        strategy = strategy_cls()

    # C. Exécution avec Filet de Sécurité (Try/Catch V3)
    try:
        result = strategy.execute(financials, params)

        # Injection requête (traçabilité)
        # On utilise setattr pour contourner le frozen si nécessaire, ou l'attribut direct
        if hasattr(result, "request"):
            try:
                result.request = request
            except Exception:
                # Si dataclass frozen, on utilise le hack standard
                object.__setattr__(result, "request", request)

        # D. Vérification Contractuelle (V2.2)
        strategy.verify_output_contract(result)

        return result

    except ValuationException:
        # On laisse passer les erreurs déjà formatées (Venant des Stratégies)
        raise

    except CalculationError as ce:
        # On convertit les vieilles erreurs CalculationError en DiagnosticEvent
        raise ValuationException(DiagnosticEvent(
            code="CALCULATION_ERROR",
            severity=SeverityLevel.ERROR,
            domain=DiagnosticDomain.MODEL,
            message=str(ce),
            remediation_hint="Vérifiez les données d'entrée financières."
        ))

    except Exception as e:
        # Catch-all pour les bugs imprévus
        raise ValuationException(DiagnosticEvent(
            code="STRATEGY_CRASH",
            severity=SeverityLevel.CRITICAL,
            domain=DiagnosticDomain.SYSTEM,
            message=f"Crash inattendu du moteur : {str(e)}",
            technical_detail=traceback.format_exc(),
            remediation_hint="Erreur technique."
        ))


# ============================================================
# 3. OUTIL AVANCÉ — REVERSE DCF (CONSERVÉ & CORRIGÉ)
# ============================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Analyse de marché (Reverse DCF).
    Calcule le taux de croissance implicite pour justifier le prix actuel.

    Conservé pour usages futurs (Dashboard avancé).
    """

    if market_price <= 0:
        return None

    low, high = -0.20, 0.50

    # On utilise la stratégie fondamentale par défaut pour le Reverse DCF
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    # [CORRECTIF V2.5] : Suppression de dataclasses.replace
    # Pydantic nécessite .model_copy(update={...})

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # On clone les params pour ne pas modifier l'objet original (Version Pydantic)
        test_params = params.model_copy(update={"fcf_growth_rate": mid})

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            if abs(iv - market_price) < 0.5: # Convergence à 50 centimes près
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid

        except Exception:
            # Si le calcul plante (ex: croissance infinie), on réduit la fourchette haute
            high = mid

    return None