"""
core/valuation/engines.py

Moteur d'exécution central — Version V1 Normative

Responsabilités :
- Router une ValuationRequest vers une stratégie déterministe valide
- Garantir l’alignement académique (CFA / Damodaran)
- Préparer les extensions (Monte Carlo) sans les ériger en méthodes

Règle fondamentale :
- Une ValuationMode = une méthode académique déterministe
"""

import logging
from typing import Dict, Type, Optional

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,
    ValuationMode,
    ValuationRequest
)
from core.valuation.strategies.abstract import ValuationStrategy

# ============================================================
# IMPORT DES STRATÉGIES DÉTERMINISTES (V1)
# ============================================================

from core.valuation.strategies.dcf_standard import StandardFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_growth import RevenueBasedStrategy
from core.valuation.strategies.rim_banks import RIMBankingStrategy
from core.valuation.strategies.graham_value import GrahamNumberStrategy

# Extension probabiliste (NON NORMATIVE)
from core.valuation.strategies.monte_carlo import MonteCarloDCFStrategy

logger = logging.getLogger(__name__)


# ============================================================
# REGISTRE NORMATIF DES STRATÉGIES (V1)
# ============================================================

STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.FCFF_TWO_STAGE: StandardFCFFStrategy,
    ValuationMode.FCFF_NORMALIZED: FundamentalFCFFStrategy,
    ValuationMode.FCFF_REVENUE_DRIVEN: RevenueBasedStrategy,
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,
}


# ============================================================
# POINT D’ENTRÉE PRINCIPAL
# ============================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute une valorisation déterministe conforme au référentiel V1.

    Étapes :
    1. Sélection de la stratégie académique
    2. Exécution du modèle déterministe
    3. Application optionnelle d’extensions (ex: Monte Carlo)
    """

    logger.info(
        "[Engine] Valuation requested | ticker=%s | mode=%s",
        request.ticker,
        request.mode.value
    )

    # --- 1. Sélection de la stratégie ---
    strategy_cls = STRATEGY_REGISTRY.get(request.mode)

    if not strategy_cls:
        raise CalculationError(
            f"Mode de valorisation non reconnu ou non autorisé (V1) : {request.mode}"
        )

    try:
        # --- 2. Exécution déterministe ---
        strategy = strategy_cls()
        result = strategy.execute(financials, params)

        # Injection de la requête pour la traçabilité UI / Audit
        object.__setattr__(result, "request", request)

        # --- 3. Extension probabiliste (OPTIONNELLE) ---
        if request.options.get("enable_monte_carlo", False):
            logger.info("[Engine] Monte Carlo extension enabled")

            mc_runner = MonteCarloDCFStrategy()
            result = mc_runner.execute(financials, params)

            # On conserve la requête originale
            object.__setattr__(result, "request", request)

        return result

    except CalculationError as e:
        logger.error(
            "[Engine] Calculation error | mode=%s | error=%s",
            request.mode.value,
            e
        )
        raise e

    except Exception as e:
        logger.error(
            "[Engine] Unexpected error | mode=%s",
            request.mode.value,
            exc_info=True
        )
        raise CalculationError(
            f"Erreur interne du moteur de valorisation : {str(e)}"
        )


# ============================================================
# OUTIL AVANCÉ — REVERSE DCF (ANALYSE DE MARCHÉ)
# ============================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le taux de croissance implicite du marché
    tel que IV ≈ Prix de marché.

    Méthode :
    - Dichotomie sur g
    - Basée sur un DCF Fondamental (normalisé)
    """

    if market_price <= 0:
        return None

    low, high = -0.20, 0.50
    strategy = FundamentalFCFFStrategy()

    for _ in range(max_iterations):
        mid = (low + high) / 2.0

        from dataclasses import replace
        test_params = replace(params, fcf_growth_rate=mid)

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
            # En cas de non-convergence (WACC <= g, etc.)
            high = mid

    return None
