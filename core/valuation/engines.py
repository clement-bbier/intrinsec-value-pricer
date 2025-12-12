import logging
import numpy as np
from typing import Dict, Type, List, Optional, Any

from core.models import CompanyFinancials, DCFParameters, DCFResult, ValuationMode
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_simple import SimpleFCFFStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.computation.statistics import generate_multivariate_samples, generate_independent_samples
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)

# REGISTRE DES STRATÉGIES
STRATEGY_MAP: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.SIMPLE_FCFF: SimpleFCFFStrategy,
    ValuationMode.FUNDAMENTAL_FCFF: FundamentalFCFFStrategy,
}


def run_deterministic_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    mode: ValuationMode
) -> DCFResult:
    """
    EXÉCUTION DÉTERMINISTE (MÉTHODES 1 & 2). Calcul unique basé sur des inputs fixes.
    """
    strategy_cls = STRATEGY_MAP.get(mode)
    
    if not strategy_cls:
        raise ValueError(f"Mode de valorisation non supporté en déterministe : {mode}")
    
    strategy = strategy_cls()
    
    return strategy.execute(financials, params)


def run_reverse_dcf(
        financials: CompanyFinancials,
        params: DCFParameters,
        market_price: float,
        tolerance: float = 0.01,  # Précision (1 centime)
        max_iterations: int = 50
) -> Optional[float]:
    """
    Calcule le "Taux de Croissance Implicite" (Implied Growth Rate) via Recherche Dichotomique.
    Utilise la STRATÉGIE FONDAMENTALE (Lissage normatif) pour éliminer le biais de simplification.
    """
    logger.info(f"[ReverseDCF] Démarrage recherche 'g' implicite pour un prix cible de {market_price:.2f}...")

    if market_price <= 0:
        logger.warning("[ReverseDCF] Prix de marché invalide.")
        return None

    low = -0.10  
    high = 0.30  

    # Instanciation de la stratégie FONDAMENTALE (Robuste)
    fundamental_strategy = FundamentalFCFFStrategy()

    for i in range(max_iterations):
        mid = (low + high) / 2.0
        
        if abs(high - low) < 0.00001:
            logger.warning("[ReverseDCF] Précision max atteinte. Arrêt.")
            return mid

        # Création des paramètres temporaires avec le taux de test (mid)
        # On passe les Target Weights (même s'ils sont 0.0) au cas où l'utilisateur les aurait définis dans params.
        test_params = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=mid,  # <-- VARIABLE D'AJUSTEMENT
            perpetual_growth_rate=params.perpetual_growth_rate,
            projection_years=params.projection_years,
            target_equity_weight=params.target_equity_weight, # Transmis
            target_debt_weight=params.target_debt_weight,     # Transmis
        )

        try:
            result = fundamental_strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share
        except CalculationError:
            iv = float('inf') 
        except Exception:
            logger.debug("[ReverseDCF] Erreur d'exécution pour g=%.2f%%. Ajustement.", mid*100)
            iv = -999.0 

        diff = iv - market_price

        if abs(diff) < tolerance:
            logger.info(f"[ReverseDCF] Trouvé ! g = {mid:.2%} (IV={iv:.2f} vs Price={market_price:.2f})")
            return mid

        if diff > 0:
            high = mid
        else:
            low = mid

    final_g = (low + high) / 2.0
    logger.warning(f"[ReverseDCF] Non convergence après {max_iterations} itérations. Retour meilleure estimation ({final_g:.2%}).")
    return final_g


def run_monte_carlo_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    num_simulations: int = 2000
) -> DCFResult:
    """
    EXÉCUTION STOCHASTIQUE (MÉTHODE 3 - MONTE CARLO).
    """
    logger.info("=== Starting Monte Carlo Simulation (%d runs) ===", num_simulations)
    
    # --- ÉTAPE 1 : GÉNÉRATION DES SCÉNARIOS ---
    
    betas, growths = generate_multivariate_samples(
        mu_beta=financials.beta,
        sigma_beta=params.beta_volatility * abs(financials.beta), 
        mu_growth=params.fcf_growth_rate,
        sigma_growth=params.growth_volatility,
        rho=-0.4, # Corrélation Négative
        num_simulations=num_simulations
    )
    
    g_inf_draws = generate_independent_samples(
        mean=params.perpetual_growth_rate,
        sigma=params.terminal_growth_volatility,
        num_simulations=num_simulations,
        clip_min=0.0,
        clip_max=0.04 
    )
    
    simulated_ivs: List[float] = []
    valid_runs = 0
    base_strategy = SimpleFCFFStrategy()
    
    # --- ÉTAPE 2 : BOUCLE DE SIMULATION ---
    for i in range(num_simulations):
        
        original_beta = financials.beta
        
        financials.beta = betas[i]
        
        # Transmission des Target Weights pour stabiliser le WACC dans la simulation
        sim_params = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=growths[i], 
            perpetual_growth_rate=g_inf_draws[i], 
            projection_years=params.projection_years,
            high_growth_years=params.high_growth_years,
            beta_volatility=params.beta_volatility,
            growth_volatility=params.growth_volatility,
            terminal_growth_volatility=params.terminal_growth_volatility,
            target_equity_weight=params.target_equity_weight, # Transmis
            target_debt_weight=params.target_debt_weight,     # Transmis
        )
        
        try:
            result_i = base_strategy.execute(financials, sim_params)
            simulated_ivs.append(result_i.intrinsic_value_per_share)
            valid_runs += 1
            
        except CalculationError:
            pass
            
        finally:
            financials.beta = original_beta

    # --- ÉTAPE 3 : RÉSULTAT FINAL ---
    final_result = base_strategy.execute(financials, params)
    
    if valid_runs > 0:
        final_result.simulation_results = simulated_ivs
        
        p10 = np.percentile(simulated_ivs, 10)
        p50 = np.median(simulated_ivs)
        p90 = np.percentile(simulated_ivs, 90)
        logger.info("[MonteCarlo] Success: %d/%d | P10: %.2f | Median: %.2f | P90: %.2f", 
                    valid_runs, num_simulations, p10, p50, p90)
    else:
        logger.error("[MonteCarlo] Échec total : 100% des scénarios ont échoué.")
    
    return final_result