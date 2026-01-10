"""
core/valuation/engines. py

ROUTEUR CENTRAL DES MOTEURS DE VALORISATION
Version : V8.1 — Clean Architecture & Centralized Logic
Responsabilités :  Orchestration, Routage et Sécurisation du contrat de sortie.
"""

from __future__ import annotations

import logging
import traceback
from typing import Dict, Type, Optional

from core.exceptions import (
    ValuationException,
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    CalculationError
)
from core.models import (
    ValuationRequest,
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    ValuationResult
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core. valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.rim_banks import RIMBankingStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy
from core.valuation.strategies.monte_carlo import MonteCarloGenericStrategy

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. REGISTRE DES STRATÉGIES (FACTORY MAP)
# ==============================================================================

STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.FCFF_TWO_STAGE:  StandardFCFFStrategy,
    ValuationMode.FCFF_NORMALIZED: FundamentalFCFFStrategy,
    ValuationMode.FCFF_REVENUE_DRIVEN: RevenueBasedStrategy,
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,
}


# ==============================================================================
# 2. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute une valorisation et déclenche instantanément l'audit de fiabilité.
    Architecture V8.1 : Injection Request -> Calcul -> Audit -> Certification.
    """
    logger.info(f"[Engine] Initialisation {request.mode.value} pour {request.ticker}")

    # =========================================================================
    # A. RÉCUPÉRATION DE LA STRATÉGIE
    # =========================================================================
    strategy_cls = STRATEGY_REGISTRY.get(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # =========================================================================
    # B. WRAPPER MONTE CARLO (Optionnel)
    # =========================================================================
    use_mc = params.enable_monte_carlo and request.mode.supports_monte_carlo
    if use_mc:
        strategy = MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
    else:
        strategy = strategy_cls()

    # =========================================================================
    # C. EXÉCUTION, AUDIT ET VALIDATION
    # =========================================================================
    try:
        # 1. Calcul mathématique de la valeur intrinsèque
        result = strategy.execute(financials, params)

        # 2. INJECTION DE LA REQUÊTE (AVANT l'audit)
        _inject_request_safely(result, request)

        # 3. APPEL DU MOTEUR D'AUDIT
        from infra.auditing.audit_engine import AuditEngine
        result.audit_report = AuditEngine.compute_audit(result)

        # 4. Validation du contrat de sortie
        strategy.verify_output_contract(result)

        logger.info(f"[Engine] Valorisation terminée avec succès. Score Audit: {result.audit_report.global_score:.1f}")
        return result

    except ValuationException:
        raise
    except CalculationError as ce:
        raise _handle_calculation_error(ce)
    except Exception as e:
        logger.error(f"Erreur critique moteur : {str(e)}")
        raise _handle_system_crash(e)


# ==============================================================================
# 3. HELPERS DE MAINTENANCE
# ==============================================================================

def _inject_request_safely(result: ValuationResult, request: ValuationRequest) -> None:
    """Gère l'injection de la requête même si l'objet est 'frozen'."""
    try:
        result.request = request
    except Exception:
        object.__setattr__(result, "request", request)


def _raise_unknown_strategy(mode: ValuationMode) -> ValuationException:
    """Lève une exception pour une stratégie non enregistrée."""
    return ValuationException(DiagnosticEvent(
        code="UNKNOWN_STRATEGY",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain. SYSTEM,
        message=f"La stratégie pour {mode} n'est pas enregistrée.",
        remediation_hint="Vérifiez le dictionnaire STRATEGY_REGISTRY dans engines. py."
    ))


def _handle_calculation_error(ce:  CalculationError) -> ValuationException:
    """Transforme une erreur de calcul en exception de valorisation."""
    return ValuationException(DiagnosticEvent(
        code="CALCULATION_ERROR",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.MODEL,
        message=str(ce),
        remediation_hint="Vérifiez la cohérence de vos inputs financiers."
    ))


def _handle_system_crash(e: Exception) -> ValuationException:
    """Gère les erreurs système critiques."""
    return ValuationException(DiagnosticEvent(
        code="STRATEGY_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=f"Échec critique du moteur : {str(e)}",
        technical_detail=traceback.format_exc(),
        remediation_hint="Redémarrez l'analyse ou contactez le support technique."
    ))


# ==============================================================================
# 4. REVERSE DCF
# ==============================================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """Calcul du taux de croissance implicite par dichotomie."""
    if market_price <= 0:
        return None

    low, high = -0.20, 0.50
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        test_params = params.model_copy(update={"fcf_growth_rate": mid})

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            if abs(iv - market_price) < 0.5:
                return mid
            if iv < market_price:
                low = mid
            else:
                high = mid
        except Exception:
            high = mid

    return None