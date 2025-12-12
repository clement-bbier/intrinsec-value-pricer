import logging
import numpy as np
from typing import List
from dataclasses import replace

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.valuation.strategies.abstract import ValuationStrategy
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


class MonteCarloDCFStrategy(ValuationStrategy):
    """
    STRATÉGIE 3 : DCF PROBABILISTE (MONTE CARLO).

    PHILOSOPHIE :
    Le futur est incertain. Au lieu de projeter une seule valeur ("Single Point Estimate"),
    nous simulons des milliers de scénarios possibles en faisant varier les inputs clés
    (Beta, Croissance, etc.) selon des lois de probabilité.

    MÉTHODOLOGIE :
    1. Définition des lois de distribution pour le Beta (Impact WACC) et la Croissance (Impact FCF).
    2. Tirage aléatoire de N scénarios (ex: 2000 itérations).
    3. Calcul du DCF pour chaque scénario.
    4. Agrégation statistique (Moyenne, Médiane, Percentiles).

    CONTRAINTES :
    - Nécessite des volatilités définies dans `params` (beta_volatility, growth_volatility).
    - Validation préalable par `MonteCarloDCFConfig`.
    """

    # Nombre d'itérations par défaut (compromis précision/performance pour l'UI)
    N_SIMULATIONS = 5000

    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        logger.info(f"[Strategy] Mode Monte Carlo sélectionné. Lancement de {self.N_SIMULATIONS} simulations...")

        # 1. Sélection du point de départ (On privilégie le lissé s'il existe, sinon le TTM)
        base_fcf = financials.fcf_fundamental_smoothed
        if base_fcf is None or base_fcf == 0:
            base_fcf = financials.fcf_last
            logger.info("[MonteCarlo] Fallback sur FCF TTM car FCF Lissé indisponible.")

        if base_fcf is None:
            raise CalculationError("Donnée manquante : Aucun FCF (ni TTM ni Lissé) disponible pour la simulation.")

        # 2. Préparation des vecteurs aléatoires (Vectorisation NumPy pour la performance)
        np.random.seed(42)  # Seed fixe pour reproductibilité (Optionnel, utile pour tests)

        # A. Simulation du Beta (Distribution Normale tronquée à 0.4 pour éviter les absurdités)
        # Le Beta impacte directement le Coût des fonds propres (Ke) -> WACC
        beta_mean = financials.beta
        beta_std = params.beta_volatility if params.beta_volatility > 0 else 0.1  # Fallback safe
        betas = np.random.normal(beta_mean, beta_std, self.N_SIMULATIONS)
        betas = np.maximum(betas, 0.4)  # Floor de sécurité

        # B. Simulation de la Croissance (Distribution Normale)
        # Impacte la projection des FCF
        g_mean = params.fcf_growth_rate
        g_std = params.growth_volatility if params.growth_volatility > 0 else 0.02  # Fallback safe
        growth_rates = np.random.normal(g_mean, g_std, self.N_SIMULATIONS)

        # C. Simulation de la Croissance Terminale (Distribution Normale, très sensible)
        # On limite g_perp pour qu'il soit toujours < WACC (contrôlé lors du calcul itératif)
        g_perp_mean = params.perpetual_growth_rate
        g_perp_std = params.terminal_growth_volatility if params.terminal_growth_volatility > 0 else 0.005
        perpetual_rates = np.random.normal(g_perp_mean, g_perp_std, self.N_SIMULATIONS)

        simulated_values: List[float] = []

        # 3. Boucle de Simulation (Optimisée)
        # Note : Pour une performance extrême, on pourrait vectoriser tout le DCF,
        # mais ici on boucle pour réutiliser la logique métier robuste de _compute_standard_dcf
        # ou appeler une version light du moteur.

        # Pour l'instant, on fait une boucle simple qui instancie des paramètres temporaires.
        # C'est suffisant pour 2000 itérations en Python moderne (~0.5s).

        for i in range(self.N_SIMULATIONS):
            # Création d'un contexte "Scénario i"
            # On clone params et financials (copie superficielle suffisante ici)
            scenario_beta = betas[i]
            scenario_g = growth_rates[i]
            scenario_g_perp = perpetual_rates[i]

            # Copie mutable temporaire des paramètres pour ce run
            # On utilise replace() de dataclasses pour faire ça proprement
            scenario_params = replace(
                params,
                fcf_growth_rate=scenario_g,
                perpetual_growth_rate=scenario_g_perp
            )

            # On injecte le beta simulé dans une copie des financials
            scenario_financials = replace(financials, beta=scenario_beta)

            try:
                # Exécution du DCF Standard pour ce scénario
                # Attention : le moteur standard peut lever une erreur si g_perp > WACC (simulé)
                # On capture ces cas limites pour ne pas crasher la simulation entière.
                result = self._compute_standard_dcf(
                    fcf_start=base_fcf,
                    financials=scenario_financials,
                    params=scenario_params
                )
                simulated_values.append(result.intrinsic_value_per_share)

            except (ValueError, CalculationError):
                # Si un scénario est mathématiquement impossible (ex: WACC < g), on l'ignore.
                continue

        # 4. Synthèse des résultats
        if not simulated_values:
            raise CalculationError(
                "La simulation Monte Carlo n'a produit aucun scénario valide (vérifiez la cohérence WACC/Croissance).")

        values_array = np.array(simulated_values)

        # Calcul de la valeur centrale (Médiane P50 est plus robuste que la Moyenne en finance)
        intrinsic_value_p50 = float(np.median(values_array))

        # On retourne un résultat structuré
        # Pour l'objet DCFResult principal, on renvoie le scénario "Central" (P50)
        # Mais on attache la liste complète des résultats pour l'histogramme UI

        # Pour avoir un objet DCFResult complet et cohérent, on relance un calcul
        # avec les paramètres médians exacts.
        final_result = self._compute_standard_dcf(
            fcf_start=base_fcf,
            financials=financials,
            params=params
        )

        # Surcharge avec les résultats de la simulation
        final_result.intrinsic_value_per_share = intrinsic_value_p50
        final_result.simulation_results = simulated_values  # La distribution complète

        logger.info(
            f"[MonteCarlo] Terminé. Médiane: {intrinsic_value_p50:.2f}. Scénarios valides: {len(simulated_values)}/{self.N_SIMULATIONS}")

        return final_result