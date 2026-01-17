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

from core.i18n import DiagnosticTexts
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
    ValuationResult,
    MultiplesData
)
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.monte_carlo import MonteCarloGenericStrategy

# Import du registre centralisé (DT-007)
from core.valuation.registry import get_strategy, StrategyRegistry

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
    Exécute une valorisation complète et déclenche l'audit institutionnel.
    Supporte nativement le mode Monte Carlo et la triangulation hybride automatique (Phase 5).
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
                from core.valuation.strategies.multiples import MarketMultiplesStrategy

                # Exécution de la stratégie de multiples (Calcul de la valeur de marché)
                rel_strategy = MarketMultiplesStrategy(multiples_data=multiples_data)
                result.multiples_triangulation = rel_strategy.execute(financials, params)

                logger.info(f"[Engine] Triangulation sectorielle finalisée avec {len(multiples_data.peers)} pairs.")
            except Exception as e:
                # Sécurité "Honest Data" : l'échec des pairs ne doit pas bloquer l'analyse principale
                logger.warning(f"[Engine] Échec non critique de la triangulation : {str(e)}")
                result.multiples_triangulation = None
        else:
            result.multiples_triangulation = None
        # =====================================================================

        # 3. APPEL DU MOTEUR D'AUDIT (Calcul du Reliability Score)
        from infra.auditing.audit_engine import AuditEngine
        result.audit_report = AuditEngine.compute_audit(result)

        # 4. Validation du contrat de sortie (SOLID)
        strategy.verify_output_contract(result)

        logger.info(f"[Engine] Valorisation terminée. Score Audit: {result.audit_report.global_score:.1f}")
        return result

    except ValuationException:
        # Propagation des exceptions métier déjà formatées
        raise
    except CalculationError as ce:
        # Transformation des erreurs de calcul en événements de diagnostic
        raise _handle_calculation_error(ce)
    except Exception as e:
        # Capture des défaillances imprévues (Système)
        logger.error(f"Erreur critique moteur : {str(e)}")
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

    # Bornes économiques standards pour la recherche
    low, high = -0.20, 0.50
    strategy = FundamentalFCFFStrategy(glass_box_enabled=False)

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        # Isolation des paramètres pour la simulation de recherche
        test_params = params.model_copy(deep=True)
        test_params.growth.fcf_growth_rate = mid

        try:
            result = strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share

            # Seuil de convergence (0.5 unité monétaire)
            if abs(iv - market_price) < 0.5:
                return mid

            if iv < market_price:
                low = mid
            else:
                high = mid
        except Exception:
            # En cas d'instabilité mathématique sur un point, on réduit la fenêtre
            high = mid

    return None