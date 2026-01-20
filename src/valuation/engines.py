"""
core/valuation/engines.py

ROUTEUR CENTRAL DES MOTEURS DE VALORISATION — VERSION V11.0 (DT-007 Resolution)
Responsabilités : Orchestration, Routage, Wrapper Monte Carlo et Reverse DCF.
Architecture : Grade-A avec support intégral FCFF (Firm) et Direct Equity (Actionnaire).
Standards : SOLID, Pydantic, Audit-Integrated, i18n, Centralized Registry.

Note DT-007: Le registre manuel STRATEGY_REGISTRY a été remplacé par
le registre centralisé dans core/valuation/registry.py
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
    CalculationError
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

# Import du registre centralisé (DT-007)
from src.valuation.registry import get_strategy, StrategyRegistry

# Import du logger institutionnel (ST-4.2)
from src.quant_logger import QuantLogger, LogDomain

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. REGISTRE DES STRATÉGIES (FACADE VERS REGISTRE CENTRALISÉ)
# ==============================================================================

# Backward compatibility: STRATEGY_REGISTRY pointe vers le registre centralisé
# Note: Ce dict est généré dynamiquement depuis le registre centralisé
def _build_legacy_registry() -> Dict[ValuationMode, Type[ValuationStrategy]]:
    """Construit le registre legacy depuis le registre centralisé."""
    return {
        mode: meta.strategy_cls 
        for mode, meta in StrategyRegistry.get_all_modes().items()
    }

STRATEGY_REGISTRY = _build_legacy_registry()


# ==============================================================================
# 2. POINT D'ENTRÉE PRINCIPAL
# ==============================================================================

def run_valuation(
        request: ValuationRequest,
        financials: CompanyFinancials,
        params: DCFParameters
) -> ValuationResult:
    """
    Exécute le moteur de valorisation unifié et lance l'audit institutionnel.

    Point d'entrée principal du système de valorisation. Orchestre l'exécution
    de la stratégie appropriée, gère le wrapper Monte Carlo optionnel, et
    déclenche la triangulation par multiples si des données de pairs sont disponibles.

    Args
    ----
    request : ValuationRequest
        Contrat de requête immuable contenant le ticker, le mode de valorisation
        et les options (dont les données de multiples pour triangulation).
    financials : CompanyFinancials
        Données financières normalisées (TTM - Trailing Twelve Months).
        Doivent être validées et sanitizées avant appel.
    params : DCFParameters
        Hypothèses d'entrée : taux (WACC, Ke), croissance, configuration
        Monte Carlo et scénarios optionnels.

    Returns
    -------
    ValuationResult
        Objet riche incluant :
        - intrinsic_value_per_share : Valeur intrinsèque par action
        - calculation_trace : Liste des CalculationStep (Glass Box)
        - audit_report : Score de fiabilité et alertes
        - multiples_triangulation : Valorisation par comparables (si disponible)

    Raises
    ------
    ValuationException
        Si le mode de valorisation n'est pas supporté (UNKNOWN_STRATEGY).
    CalculationError
        Si une erreur mathématique survient pendant le calcul.

    Financial Impact
    ----------------
    Point d'entrée critique. Une défaillance ici invalide l'intégralité du
    Pitchbook. Toute modification doit être validée contre le Golden Dataset
    (50 tickers de référence) pour garantir la non-régression des calculs.

    Examples
    --------
    >>> from src.domain.models import ValuationRequest, ValuationMode, InputSource
    >>> request = ValuationRequest(
    ...     ticker="AAPL",
    ...     projection_years=5,
    ...     mode=ValuationMode.FCFF_STANDARD,
    ...     input_source=InputSource.AUTO
    ... )
    >>> result = run_valuation(request, financials, params)
    >>> print(f"Valeur intrinsèque: ${result.intrinsic_value_per_share:.2f}")

    See Also
    --------
    run_reverse_dcf : Calcul du taux de croissance implicite par dichotomie.
    """
    logger.info(f"[Engine] Initialisation {request.mode.value} pour {request.ticker}")

    # =========================================================================
    # A. RÉCUPÉRATION DE LA STRATÉGIE PRINCIPALE (via registre centralisé)
    # =========================================================================
    strategy_cls = get_strategy(request.mode)
    if not strategy_cls:
        raise _raise_unknown_strategy(request.mode)

    # =========================================================================
    # B. WRAPPER MONTE CARLO
    # =========================================================================
    # Détermine si la simulation stochastique doit être appliquée
    use_mc = params.monte_carlo.enable_monte_carlo and request.mode.supports_monte_carlo

    if use_mc:
        strategy = MonteCarloGenericStrategy(strategy_cls=strategy_cls, glass_box_enabled=True)
    else:
        strategy = strategy_cls()

    # =========================================================================
    # C. EXÉCUTION DU MODÈLE INTRINSÈQUE
    # =========================================================================
    try:
        # 1. Calcul mathématique de la valeur intrinsèque (Délégation)
        result = strategy.execute(financials, params)

        # 2. Injection de la requête (Nécessaire pour le contexte d'audit)
        _inject_request_safely(result, request)

        # =====================================================================
        # NOUVEAUTÉ PHASE 5 : DÉCLENCHEMENT DE LA TRIANGULATION (HYBRIDE)
        # =====================================================================
        # On vérifie la présence de données de cohorte dans les options de la requête
        multiples_data = request.options.get("multiples_data")

        if multiples_data and hasattr(multiples_data, "peers") and len(multiples_data.peers) > 0:
            try:
                from src.valuation.strategies.multiples import MarketMultiplesStrategy

                # Exécution de la stratégie de multiples (Calcul de la valeur de marché)
                rel_strategy = MarketMultiplesStrategy(multiples_data=multiples_data)
                result.multiples_triangulation = rel_strategy.execute(financials, params)

                logger.info(f"[Engine] Peer triangulation completed | peers_count={len(multiples_data.peers)}")
            except Exception as e:
                # Sécurité "Honest Data" : l'échec des pairs ne doit pas bloquer l'analyse principale
                logger.warning(f"[Engine] Non-critical peer triangulation failure | error={str(e)}")
                result.multiples_triangulation = None
        else:
            result.multiples_triangulation = None
        # =====================================================================

        # 3. APPEL DU MOTEUR D'AUDIT (Calcul du Reliability Score)
        from infra.auditing.audit_engine import AuditEngine
        result.audit_report = AuditEngine.compute_audit(result)

        # 4. Validation du contrat de sortie (SOLID)
        strategy.verify_output_contract(result)

        logger.info(f"[Engine] Valuation completed | audit_score={result.audit_report.global_score:.1f}")
        
        # 5. Log institutionnel (ST-4.2)
        QuantLogger.log_success(
            ticker=request.ticker,
            mode=request.mode.value,
            iv=result.intrinsic_value_per_share,
            audit_score=result.audit_report.global_score if result.audit_report else None,
            market_price=result.market_price
        )
        
        return result

    except ValuationException:
        # Propagation des exceptions métier déjà formatées
        raise
    except CalculationError as ce:
        # Transformation des erreurs de calcul en événements de diagnostic
        raise _handle_calculation_error(ce)
    except Exception as e:
        # Capture des défaillances imprévues (Système)
        logger.error(f"[Engine] Critical engine error | error={str(e)}")
        QuantLogger.log_error(
            ticker=request.ticker,
            error=str(e),
            domain=LogDomain.VALUATION
        )
        raise _handle_system_crash(e)

# ==============================================================================
# 3. HELPERS DE MAINTENANCE (AUDIT & DIAGNOSTIC)
# ==============================================================================

def _inject_request_safely(result: ValuationResult, request: ValuationRequest) -> None:
    """Gère l'injection de la requête sur l'objet résultat de manière résiliente."""
    try:
        result.request = request
    except Exception:
        # Fallback pour les objets immuables ou protégés
        object.__setattr__(result, "request", request)


def _raise_unknown_strategy(mode: ValuationMode) -> ValuationException:
    """Lève une exception système via ui_texts lorsqu'un mode n'est pas mappé."""
    return ValuationException(DiagnosticEvent(
        code="UNKNOWN_STRATEGY",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.UNKNOWN_STRATEGY_MSG.format(mode=mode),
        remediation_hint=DiagnosticTexts.UNKNOWN_STRATEGY_HINT
    ))


def _handle_calculation_error(ce: CalculationError) -> ValuationException:
    """Formate une erreur de calcul brute en rapport de diagnostic UI."""
    return ValuationException(DiagnosticEvent(
        code="CALCULATION_ERROR",
        severity=SeverityLevel.ERROR,
        domain=DiagnosticDomain.MODEL,
        message=str(ce),
        remediation_hint=DiagnosticTexts.CALC_GENERIC_HINT
    ))


def _handle_system_crash(e: Exception) -> ValuationException:
    """Gère les crashs techniques inattendus avec trace technique complète."""
    return ValuationException(DiagnosticEvent(
        code="STRATEGY_CRASH",
        severity=SeverityLevel.CRITICAL,
        domain=DiagnosticDomain.SYSTEM,
        message=DiagnosticTexts.STRATEGY_CRASH_MSG.format(error=str(e)),
        technical_detail=traceback.format_exc(),
        remediation_hint=DiagnosticTexts.STRATEGY_CRASH_HINT
    ))


# ==============================================================================
# 4. REVERSE DCF (Version Segmentée)
# ==============================================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le taux de croissance implicite (g) par dichotomie.
    Utilise la stratégie fondamentale comme socle de référence pour le marché.
    """
    if market_price <= 0:
        return None

    # Bornes économiques standards pour la recherche (centralisées ST-2.3)
    low = TechnicalDefaults.REVERSE_DCF_LOW_BOUND
    high = TechnicalDefaults.REVERSE_DCF_HIGH_BOUND
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # Isolation des paramètres pour la simulation de recherche
        test_params = params.model_copy(deep=True)
        test_params.growth.fcf_growth_rate = mid

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            # Seuil de convergence (TechnicalDefaults.VALUATION_CONVERGENCE_THRESHOLD unité monétaire)
            if abs(iv - market_price) < TechnicalDefaults.VALUATION_CONVERGENCE_THRESHOLD:
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except Exception:
            # En cas d'instabilité mathématique sur un point, on réduit la fenêtre
            high = mid

    return None
