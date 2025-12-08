import logging
from typing import Optional

from core.models import CompanyFinancials, DCFParameters
# On importe le moteur de base pour faire tourner les simulations
from core.dcf.basic_engine import run_dcf_simple_fcff

logger = logging.getLogger(__name__)


def run_reverse_dcf(
        financials: CompanyFinancials,
        params: DCFParameters,
        market_price: float,
        tolerance: float = 0.05,  # Précision (5 centimes)
        max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le "Taux de Croissance Implicite" (Implied Growth Rate).

    Répond à la question : "Quelle croissance le marché attend-il pour justifier le prix actuel ?"

    Méthode : Recherche Dichotomique (Binary Search).
    On fait varier 'g' (fcf_growth_rate) jusqu'à ce que la Valeur Intrinsèque == Prix Marché.

    Returns:
        float: Le taux de croissance implicite (ex: 0.12 pour 12%).
        None: Si aucune solution n'est trouvée (ex: Prix irrationnel).
    """
    logger.info(f"[ReverseDCF] Recherche du 'g' implicite pour un prix cible de {market_price:.2f}...")

    if market_price <= 0:
        return None

    # Bornes de recherche réalistes (-50% à +100%)
    low = -0.50
    high = 1.00

    best_guess = None

    for i in range(max_iterations):
        mid = (low + high) / 2.0

        # On crée des paramètres temporaires pour tester ce taux 'mid'
        # On suppose que le marché applique ce taux en croissance initiale
        test_params = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=mid,  # <--- VARIABLE D'AJUSTEMENT
            perpetual_growth_rate=params.perpetual_growth_rate,
            projection_years=params.projection_years
        )

        try:
            # On lance le moteur simple (Méthode 1) car c'est celui que le marché utilise souvent mentalement
            result = run_dcf_simple_fcff(financials, test_params)
            iv = result.intrinsic_value_per_share
        except Exception:
            iv = -999.0  # Cas d'erreur (WACC < g, etc.)

        diff = iv - market_price

        # Si on est assez proche
        if abs(diff) < tolerance:
            logger.info(f"[ReverseDCF] Trouvé ! g = {mid:.2%} (IV={iv:.2f} vs Price={market_price:.2f})")
            return mid

        # Ajustement des bornes
        if iv > market_price:
            # Notre IV est trop haute => la croissance testée est trop forte
            high = mid
        else:
            # Notre IV est trop basse => la croissance testée est trop faible
            low = mid

        best_guess = mid

    logger.warning("[ReverseDCF] Convergence non parfaite. Retour de la meilleure estimation.")
    return best_guess