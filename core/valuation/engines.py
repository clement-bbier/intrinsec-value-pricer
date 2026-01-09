"""
core/valuation/engines.py

ROUTEUR CENTRAL DES MOTEURS DE VALORISATION
Version : V3.0 — Clean Architecture & Centralized Logic
Responsabilités : Orchestration, Routage et Sécurisation du contrat de sortie.
"""

import logging
import traceback
from typing import Dict, Type, Optional

# SYSTÈME DE DIAGNOSTIC ET EXCEPTIONS
from core.exceptions import ValuationException, DiagnosticEvent, SeverityLevel, DiagnosticDomain, CalculationError
from core.models import (
    ValuationRequest,
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    ValuationResult
)

# STRATÉGIES CONCRÈTES
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.rim_banks import RIMBankingStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy
from core.valuation.strategies.monte_carlo import MonteCarloGenericStrategy

logger = logging.getLogger(__name__)

# ============================================================
# 1. REGISTRE DES STRATÉGIES (FACTORY MAP)
# ============================================================
STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.FCFF_TWO_STAGE: StandardFCFFStrategy,
    ValuationMode.FCFF_NORMALIZED: FundamentalFCFFStrategy,
    ValuationMode.FCFF_REVENUE_DRIVEN: RevenueBasedStrategy,
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,
}

# ============================================================
# 2. POINT D’ENTRÉE PRINCIPAL
# ============================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute une valorisation via le registre des stratégies.
    Gère dynamiquement l'encapsulation Monte Carlo.
    """
    logger.info(f"[Engine] Starting {request.mode.value} for {request.ticker}")

    # A. RÉCUPÉRATION DE LA STRATÉGIE DE BASE
    strategy_cls = STRATEGY_REGISTRY.get(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # B. DÉTERMINATION DU WRAPPER (MONTE CARLO VS STANDARD)
    # On utilise la propriété supports_monte_carlo centralisée dans l'Enum
    use_monte_carlo = params.enable_monte_carlo and request.mode.supports_monte_carlo

    if use_monte_carlo:
        logger.info(f"Wrapper Monte Carlo activé pour {request.mode.value}")
        strategy = MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
    else:
        if params.enable_monte_carlo:
            logger.warning(f"Monte Carlo ignoré : {request.mode.value} est déterministe par nature.")
        strategy = strategy_cls()

    # C. EXÉCUTION ET SÉCURISATION
    try:
        result = strategy.execute(financials, params)

        # Injection de la requête pour traçabilité (Gestion immuabilité)
        _inject_request_safely(result, request)

        # Validation contractuelle (Garantie de qualité V2.2)
        strategy.verify_output_contract(result)

        return result

    except ValuationException:
        raise # On laisse remonter les erreurs métier déjà formatées
    except CalculationError as ce:
        raise _handle_calculation_error(ce)
    except Exception as e:
        raise _handle_system_crash(e)

# ============================================================
# 3. HELPERS DE MAINTENANCE (CLEAN CODE)
# ============================================================

def _inject_request_safely(result: ValuationResult, request: ValuationRequest):
    """Gère l'injection de la requête même si l'objet est 'frozen'."""
    try:
        result.request = request
    except Exception:
        object.__setattr__(result, "request", request)

def _raise_unknown_strategy(mode: ValuationMode) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="UNKNOWN_STRATEGY",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=f"La stratégie pour {mode} n'est pas enregistrée.",
        remediation_hint="Vérifiez le dictionnaire STRATEGY_REGISTRY dans engines.py."
    ))

def _handle_calculation_error(ce: CalculationError) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="CALCULATION_ERROR",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.MODEL,
        message=str(ce),
        remediation_hint="Vérifiez la cohérence de vos inputs financiers."
    ))

def _handle_system_crash(e: Exception) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="STRATEGY_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=f"Échec critique du moteur : {str(e)}",
        technical_detail=traceback.format_exc(),
        remediation_hint="Redémarrez l'analyse ou contactez le support technique."
    ))

# ============================================================
# 4. REVERSE DCF (CONSERVÉ)
# ============================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """Calcul du taux de croissance implicite par dichotomie."""
    if market_price <= 0: return None

    low, high = -0.20, 0.50
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        test_params = params.model_copy(update={"fcf_growth_rate": mid})

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share
            if abs(iv - market_price) < 0.5: return mid
            if iv < market_price: low = mid
            else: high = mid
        except Exception:
            high = mid
    return None