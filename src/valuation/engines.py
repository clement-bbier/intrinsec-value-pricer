"""
src/valuation/engines.py
MOTEUR DE VALORISATION UNIFIÉ — ROUTEUR DE STRATÉGIES
====================================================
Rôle : Orchestration des stratégies, injection Monte Carlo et audit.
Architecture : Grade-A (SOLID), Résilience aux erreurs mathématiques.
"""

from __future__ import annotations
import logging
import traceback
from typing import Dict, Type, Optional

from src.i18n import DiagnosticTexts
from src.config.constants import TechnicalDefaults
from src.exceptions import (
    ValuationException,
    DiagnosticEvent,
    SeverityLevel,
    DiagnosticDomain,
    CalculationError,
    ModelDivergenceError
)
from src.models import (
    ValuationRequest,
    ValuationMode,
    CompanyFinancials,
    DCFParameters,
    ValuationResult
)
from src.valuation.strategies.abstract import ValuationStrategy
from src.valuation.strategies.monte_carlo import MonteCarloGenericStrategy
from src.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy

# Registry and Logging
from src.valuation.registry import get_strategy, StrategyRegistry
from src.quant_logger import QuantLogger, LogDomain

logger = logging.getLogger(__name__)

# Définition des erreurs mathématiques ciblées (ST-1.4)
VALUATION_ERRORS = (
    CalculationError,
    ModelDivergenceError,
    ValueError,
    ZeroDivisionError
)

# ==============================================================================
# 1. INTERFACE DU REGISTRE
# ==============================================================================

def _build_legacy_registry() -> Dict[ValuationMode, Type[ValuationStrategy]]:
    """Construit la table de correspondance pour la compatibilité descendante."""
    return {
        mode: meta.strategy_cls
        for mode, meta in StrategyRegistry.get_all_modes().items()
    }

STRATEGY_REGISTRY = _build_legacy_registry()

# ==============================================================================
# 2. MOTEUR D'EXÉCUTION PRINCIPAL
# ==============================================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute le moteur de valorisation unifié et déclenche l'audit institutionnel.
    """
    logger.info(f"[Engine] Initialisation {request.mode.value} pour {request.ticker}")

    # A. Sélection de la stratégie
    strategy_cls = get_strategy(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # B. Décoration Monte Carlo (Si activé et supporté)
    use_mc = params.monte_carlo.enable_monte_carlo and request.mode.supports_monte_carlo
    strategy = (
        MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
        if use_mc else strategy_cls()
    )

    try:
        # C. Exécution de l'algorithme financier
        result = strategy.execute(financials, params)

        # D. Traçabilité : Injection du contexte et de la requête
        _inject_context(result, request)

        # E. Analyze relative : Triangulation par multiples
        _apply_triangulation(result, request, financials, params)

        # F. Audit de conformité (Lazy import pour éviter les cycles)
        from infra.auditing.audit_engine import AuditEngine
        result.audit_report = AuditEngine.compute_audit(result)

        # G. Validation du contrat SOLID
        strategy.verify_output_contract(result)

        _log_final_status(request, result)

        return result

    except CalculationError as ce:
        # Erreur métier identifiée (ex: division par zéro dans le modèle)
        raise _handle_calculation_error(ce)
    except ValuationException:
        # Propagation des erreurs déjà typées
        raise
    except Exception as e:
        # Capture des crashs système imprévus
        logger.error(f"[Engine] Erreur critique système : {str(e)}")
        QuantLogger.log_error(ticker=request.ticker, error=str(e), domain=LogDomain.VALUATION)
        raise _handle_system_crash(e)

# ==============================================================================
# 3. ANALYSE INVERSE (REVERSE DCF)
# ==============================================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le taux de croissance implicite (g) via la méthode de bissection.
    """
    if market_price <= 0:
        return None

    low = TechnicalDefaults.REVERSE_DCF_LOW_BOUND
    high = TechnicalDefaults.REVERSE_DCF_HIGH_BOUND
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        test_params = params.model_copy(deep=True)
        test_params.growth.fcf_growth_rate = mid

        try:
            res = strategy.execute(financials, test_params)
            iv = res.intrinsic_value_per_share

            if abs(iv - market_price) < TechnicalDefaults.VALUATION_CONVERGENCE_THRESHOLD:
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except VALUATION_ERRORS:
            # En cas d'instabilité mathématique sur une borne, on resserre
            high = mid

    return None

# ==============================================================================
# 4. HELPERS PRIVÉS
# ==============================================================================

def _inject_context(result: ValuationResult, request: ValuationRequest) -> None:
    """Injecte la requête dans le résultat pour la traçabilité i18n et l'audit."""
    try:
        result.request = request
    except (AttributeError, TypeError):
        object.__setattr__(result, "request", request)

def _apply_triangulation(
    result: ValuationResult,
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> None:
    """Gère la triangulation optionnelle par les comparables de marché."""
    multiples_data = request.options.get("multiples_data")

    if multiples_data and hasattr(multiples_data, "peers") and len(multiples_data.peers) > 0:
        try:
            from src.valuation.strategies.multiples import MarketMultiplesStrategy
            rel_strategy = MarketMultiplesStrategy(multiples_data=multiples_data)
            result.multiples_triangulation = rel_strategy.execute(financials, params)
            logger.info(f"[Engine] Triangulation terminée | n={len(multiples_data.peers)}")
        except VALUATION_ERRORS as e:
            logger.warning(f"[Engine] Échec triangulation (non-critique) : {str(e)}")
            result.multiples_triangulation = None

def _log_final_status(request: ValuationRequest, result: ValuationResult) -> None:
    """Journalise le succès et le score d'audit dans le QuantLogger."""
    score = result.audit_report.global_score if result.audit_report else 0.0
    logger.info(f"[Engine] Valuation terminée | audit_score={score:.1f}")

    QuantLogger.log_success(
        ticker=request.ticker,
        mode=request.mode.value,
        iv=result.intrinsic_value_per_share,
        audit_score=score,
        market_price=result.market_price
    )

def _raise_unknown_strategy(mode: ValuationMode) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="UNKNOWN_STRATEGY",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.UNKNOWN_STRATEGY_MSG.format(mode=mode),
        remediation_hint=DiagnosticTexts.UNKNOWN_STRATEGY_HINT
    ))

def _handle_calculation_error(ce: CalculationError) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="CALCULATION_ERROR",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.MODEL,
        message=str(ce),
        remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
    ))

def _handle_system_crash(e: Exception) -> ValuationException:
    return ValuationException(DiagnosticEvent(
        code="STRATEGY_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.STRATEGY_CRASH_MSG.format(error=str(e)),
        technical_detail=traceback.format_exc(),
        remediation_hint=DiagnosticTexts.STRATEGY_CRASH_HINT
    ))