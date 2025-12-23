"""
core/valuation/strategies/monte_carlo.py

EXTENSION PROBABILISTE — MONTE CARLO UNIVERSEL (V2.6 — Pydantic Compatible)
Supporte désormais DCF (Standard/Growth/Fundamental) ET RIM (Banques).

Cette extension s'applique comme un 'Wrapper' autour d'une stratégie déterministe
pour en tester la robustesse face à la volatilité des hypothèses clés (Beta, Croissance).
"""

from __future__ import annotations

import logging
from typing import List, Dict, Type

import numpy as np

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    ValuationResult,  # <--- Type générique parent (vs DCFValuationResult)
    TraceHypothesis
)

from core.valuation.strategies.abstract import ValuationStrategy

from core.computation.statistics import (
    generate_multivariate_samples,
    generate_independent_samples
)

logger = logging.getLogger(__name__)


# ============================================================================
# STRATÉGIE — EXTENSION MONTE CARLO GÉNÉRIQUE
# ============================================================================

class MonteCarloGenericStrategy(ValuationStrategy):
    """
    Wrapper Monte Carlo capable de simuler n'importe quelle stratégie déterministe
    (DCF ou RIM) en perturbant ses inputs (Beta, Croissance).
    """

    academic_reference = "CFA Institute / Damodaran (Probabilistic)"
    economic_domain = "Uncertainty & Risk Quantification"

    def __init__(self, strategy_cls: Type[ValuationStrategy]):
        """
        Initialise le wrapper avec la stratégie cible à simuler.

        Args:
            strategy_cls: La classe de la stratégie (ex: RIMBankingStrategy, StandardFCFFStrategy)
        """
        super().__init__()
        self.strategy_cls = strategy_cls  # Injection de dépendance (Factory)

    # --- Paramètres par défaut (Norme V2.2) ---
    DEFAULT_SIMULATIONS = 5_000
    MIN_VALID_RATIO = 0.50

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> ValuationResult:
        """
        Exécute une analyse Monte Carlo autour de la stratégie injectée.
        """

        # ==============================================================
        # 0. PARAMÉTRAGE GLOBAL
        # ==============================================================

        num_simulations = (
            params.num_simulations
            if params.num_simulations
            else self.DEFAULT_SIMULATIONS
        )

        logger.info(
            "[Monte Carlo] Enabled | ticker=%s | simulations=%d | underlying=%s",
            financials.ticker,
            num_simulations,
            self.strategy_cls.__name__
        )

        if num_simulations < 500:
            raise CalculationError(
                "Nombre de simulations insuffisant (<500) pour une analyse robuste."
            )

        # ==============================================================
        # 1. PARAMÉTRAGE DES INCERTITUDES (GLASS BOX - TRACE VISIBLE)
        # ==============================================================

        # Récupération des volatilités (avec valeurs par défaut si non fournies)
        sigma_beta = params.beta_volatility or 0.10
        sigma_growth = params.growth_volatility or 0.015
        sigma_terminal = params.terminal_growth_volatility or 0.005

        # Corrélation empirique standard entre Beta (Risque) et Croissance
        rho_beta_growth = -0.30

        # [CORRECTIF PYDANTIC] Arguments nommés obligatoires
        self.add_step(
            label="Paramétrage des incertitudes Monte Carlo",
            theoretical_formula="σ, ρ",
            hypotheses=[
                TraceHypothesis(name="Simulations", value=num_simulations, unit="runs"),
                TraceHypothesis(name="Underlying Strategy", value=self.strategy_cls.__name__, unit=""),
                TraceHypothesis(name="Beta volatility", value=sigma_beta, unit="%"),
                TraceHypothesis(name="Growth volatility", value=sigma_growth, unit="%"),
                TraceHypothesis(name="Correlation (beta, growth)", value=rho_beta_growth, unit="")
            ],
            numerical_substitution="Définition des paramètres statistiques",
            result=1.0,
            unit="setup",
            interpretation=(
                f"Paramétrage des distributions probabilistes sur {num_simulations} scénarios "
                f"pour le modèle {self.strategy_cls.__name__}."
            )
        )

        # ==============================================================
        # 2. GÉNÉRATION DES SCÉNARIOS STOCHASTIQUES
        # ==============================================================

        # Note : Cette génération est compatible RIM car RIM utilise aussi 'beta' (pour Ke) et 'growth'
        betas, growths = generate_multivariate_samples(
            mu_beta=financials.beta,
            sigma_beta=sigma_beta,
            mu_growth=params.fcf_growth_rate,
            sigma_growth=sigma_growth,
            rho=rho_beta_growth,
            num_simulations=num_simulations
        )

        terminal_growths = generate_independent_samples(
            mean=params.perpetual_growth_rate,
            sigma=sigma_terminal,
            num_simulations=num_simulations,
            clip_min=0.0,
            clip_max=0.04  # Cap hardcoded pour éviter les explosions terminales
        )

        # [CORRECTIF PYDANTIC] Arguments nommés obligatoires
        self.add_step(
            label="Génération des scénarios Monte Carlo",
            theoretical_formula="Sampling multivarié corrélé",
            hypotheses=[
                TraceHypothesis(name="Simulations", value=num_simulations, unit="#"),
                TraceHypothesis(name="Distributions", value="Normal / Corrélées", unit="")
            ],
            numerical_substitution="Sampling stochastique des hypothèses",
            result=num_simulations,
            unit="runs",
            interpretation=(
                "Création d’un ensemble de scénarios économiquement cohérents "
                "pour mesurer la dispersion de la valeur intrinsèque."
            )
        )

        # ==============================================================
        # 3. BOUCLE DE SIMULATION (SILENT MODE)
        # ==============================================================

        # On instancie la stratégie "Ouvrière" sans Glass Box pour aller vite
        worker_strategy = self.strategy_cls(glass_box_enabled=False)

        simulated_values: List[float] = []
        valid_runs = 0

        # Boucle critique de performance
        for i in range(num_simulations):

            # [CORRECTIF CRITIQUE] : Utilisation de model_copy pour Pydantic V2
            # Au lieu de dataclasses.replace() qui ferait crasher l'application
            sim_financials = financials.model_copy(update={
                "beta": float(betas[i])
            })

            sim_params = params.model_copy(update={
                "fcf_growth_rate": float(growths[i]),
                "perpetual_growth_rate": float(terminal_growths[i])
            })

            try:
                # Exécution sans trace (Rapide)
                result = worker_strategy.execute(sim_financials, sim_params)
                iv = result.intrinsic_value_per_share

                # Filtre économique conservateur pour éviter les valeurs aberrantes
                # (Ex: RIM peut donner des résultats négatifs si Ke est extrême, on filtre ici)
                if -500.0 < iv < 50_000.0:
                    simulated_values.append(iv)
                    valid_runs += 1

            except Exception:
                # On ignore silencieusement les crashes de simulation individuelle (ex: Ke < 0)
                continue

        valid_ratio = valid_runs / num_simulations

        # [CORRECTIF PYDANTIC] Arguments nommés obligatoires
        self.add_step(
            label="Filtrage des scénarios valides",
            theoretical_formula="Valid / Total",
            hypotheses=[
                TraceHypothesis(name="Valid runs", value=valid_runs, unit="#"),
                TraceHypothesis(name="Total runs", value=num_simulations, unit="#")
            ],
            numerical_substitution=f"{valid_runs} / {num_simulations}",
            result=valid_ratio,
            unit="ratio",
            interpretation=(
                f"Taux de succès de {valid_ratio:.1%}. "
                "Élimination des scénarios économiquement aberrants ou instables."
            )
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise CalculationError(
                f"Trop peu de scénarios Monte Carlo valides ({valid_ratio:.1%}). "
                "Le modèle est trop instable mathématiquement pour une analyse probabiliste."
            )

        # ==============================================================
        # 4. SCÉNARIO PIVOT — DÉTERMINISTE PUR (GLASS BOX ACTIVE)
        # ==============================================================

        # On ré-exécute une dernière fois avec les vrais paramètres et la Glass Box activée
        # Cela permet d'avoir la trace détaillée du cas central
        reference_strategy = self.strategy_cls(glass_box_enabled=True)
        final_result = reference_strategy.execute(financials, params)

        # [CORRECTIF PYDANTIC] Arguments nommés obligatoires
        self.add_step(
            label="Scénario pivot déterministe (P50 Référence)",
            theoretical_formula="Modèle Déterministe",
            hypotheses=[
                TraceHypothesis(name="Model", value=self.strategy_cls.__name__, unit=""),
                TraceHypothesis(name="Nature", value="Deterministic reference", unit="")
            ],
            numerical_substitution="Exécution sans stochasticité (Glass Box)",
            result=final_result.intrinsic_value_per_share,
            unit=financials.currency,
            interpretation=(
                "Scénario central de référence, servant d’ancrage à l’analyse probabiliste."
            )
        )

        # ==============================================================
        # 5. ANALYSE STATISTIQUE DES SORTIES & FUSION
        # ==============================================================

        values = np.array(simulated_values)

        p10 = float(np.percentile(values, 10))
        p50 = float(np.percentile(values, 50))
        p90 = float(np.percentile(values, 90))
        mean = float(np.mean(values))
        std = float(np.std(values))

        quantiles: Dict[str, float] = {
            "P10": p10,
            "P50": p50,
            "P90": p90,
            "Mean": mean,
            "Std": std
        }

        # La valeur finale affichée est la médiane des simulations (Approche Hedge Fund standard)
        final_result.intrinsic_value_per_share = p50
        final_result.simulation_results = simulated_values
        final_result.quantiles = quantiles

        if final_result.market_price > 0:
            final_result.upside_pct = (
                p50 / final_result.market_price
            ) - 1.0

        # [CORRECTIF PYDANTIC] Arguments nommés obligatoires
        self.add_step(
            label="Sélection de la valeur centrale (Synthèse)",
            theoretical_formula="Median(simulations)",
            hypotheses=[
                TraceHypothesis(name="P10 (Pessimiste)", value=p10, unit=financials.currency),
                TraceHypothesis(name="P50 (Central)", value=p50, unit=financials.currency),
                TraceHypothesis(name="P90 (Optimiste)", value=p90, unit=financials.currency),
                TraceHypothesis(name="Std dev", value=std, unit=financials.currency)
            ],
            numerical_substitution="P50 retenu comme estimation centrale",
            result=p50,
            unit=financials.currency,
            interpretation=(
                "La médiane des simulations est privilégiée à la valeur statique "
                "pour sa robustesse face aux asymétries de risque."
            )
        )

        # Fusion des traces Glass Box : On ajoute les étapes Monte Carlo AVANT les étapes du modèle pivot
        final_result.calculation_trace = self.calculation_trace + final_result.calculation_trace

        return final_result