"""
core/valuation/engines.py

Moteur d'exécution central — Version V1.1 (Chapitre 3 conforme)

Responsabilités :
- Orchestrer une valorisation déterministe
- Appliquer strictement le contrat de sortie Chapitre 3
- Refuser toute sortie invalide ou incomplète

Principe clé :
- Le moteur ne fait confiance à personne
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
# REGISTRE NORMATIF DES STRATÉGIES
# ============================================================

STRATEGY_REGISTRY: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.FCFF_TWO_STAGE: StandardFCFFStrategy,
    ValuationMode.FCFF_NORMALIZED: FundamentalFCFFStrategy,
    ValuationMode.FCFF_REVENUE_DRIVEN: RevenueBasedStrategy,
    ValuationMode.RESIDUAL_INCOME_MODEL: RIMBankingStrategy,
    ValuationMode.GRAHAM_1974_REVISED: GrahamNumberStrategy,
}


# ============================================================
# POINT D’ENTRÉE PRINCIPAL — VALORISATION
# ============================================================

def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    params: DCFParameters
) -> ValuationResult:
    """
    Exécute une valorisation conforme au référentiel V1
    et au contrat de sortie Chapitre 3.
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
            f"Mode de valorisation non autorisé : {request.mode}"
        )

    # --- 2. Exécution déterministe ---
    try:
        strategy = strategy_cls()
        result = strategy.execute(financials, params)

        # Injection requête (traçabilité)
        object.__setattr__(result, "request", request)

        # --- 3. Vérification CONTRACTUELLE (OBLIGATOIRE) ---
        contract = result.build_output_contract()
        if not contract.is_valid():
            raise CalculationError(
                f"Contrat de sortie violé pour {request.mode.value} : {contract}"
            )

        # --- 4. Extension probabiliste (optionnelle, non normative) ---
        if request.options.get("enable_monte_carlo", False):
            logger.info("[Engine] Monte Carlo extension enabled")

            mc_runner = MonteCarloDCFStrategy()
            mc_result = mc_runner.execute(financials, params)

            # Revalidation contractuelle après extension
            mc_contract = mc_result.build_output_contract()
            if not mc_contract.is_valid():
                raise CalculationError(
                    "Monte Carlo a produit une sortie invalide"
                )

            object.__setattr__(mc_result, "request", request)
            result = mc_result

        return result

    except CalculationError:
        raise

    except Exception as e:
        logger.error(
            "[Engine] Unexpected failure | mode=%s",
            request.mode.value,
            exc_info=True
        )
        raise CalculationError(
            f"Erreur interne du moteur de valorisation : {e}"
        )


# ============================================================
# OUTIL AVANCÉ — REVERSE DCF (HORS CONTRAT DE SORTIE)
# ============================================================

def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    max_iterations: int = 50
) -> Optional[float]:
    """
    Analyse de marché (Reverse DCF).

    ⚠️ Hors périmètre Chapitre 3 :
    - ce n’est PAS une sortie de valorisation
    - aucun contrat de sortie n’est exigé ici
    """

    if market_price <= 0:
        return None

    low, high = -0.20, 0.50
    strategy = FundamentalFCFFStrategy()

    from dataclasses import replace

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
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
            high = mid

    return None
