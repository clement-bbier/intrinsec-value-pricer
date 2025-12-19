"""
core/valuation/strategies/monte_carlo.py

EXTENSION PROBABILISTE — MONTE CARLO
Version : V2.0 — Chapitre 7 conforme (Glass Box Extension)

STATUT NORMATIF
---------------
Monte Carlo est une EXTENSION PROBABILISTE appliquée exclusivement
aux paramètres d’entrée d’un modèle de valorisation déterministe.

Principes NON NÉGOCIABLES :
- Monte Carlo n’est PAS une méthode de valorisation
- La logique financière reste strictement déterministe
- Chaque simulation = exécution complète du moteur déterministe
- Le scénario pivot (P50) est calculé sans stochasticité
- Aucune donnée comptable historique n’est modifiée

Références :
- CFA Institute — Model Risk & Sensitivity Analysis
- Damodaran — Narrative & Probabilistic Valuation
"""

from __future__ import annotations

import logging
from typing import List, Dict
from dataclasses import replace

import numpy as np

from core.exceptions import CalculationError
from core.models import (
    CompanyFinancials,
    DCFParameters,
    DCFValuationResult,
    TraceHypothesis
)

from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_standard import StandardFCFFStrategy

from core.computation.statistics import (
    generate_multivariate_samples,
    generate_independent_samples
)

logger = logging.getLogger(__name__)


# ============================================================================
# STRATÉGIE — EXTENSION MONTE CARLO
# ============================================================================

class MonteCarloDCFStrategy(ValuationStrategy):
    """
    Extension Monte Carlo autour d’un DCF FCFF déterministe valide.

    Cette classe :
    - n’introduit AUCUNE logique financière nouvelle
    - n’altère AUCUNE formule de valorisation
    - mesure exclusivement l’incertitude des hypothèses
    """

    academic_reference = "CFA Institute / Damodaran"
    economic_domain = "Uncertainty & Risk Quantification"
    financial_invariants = [
        "Deterministic model invariance",
        "Monte Carlo applied to inputs only",
        "Scenario pivot must remain deterministic",
    ]

    # --- Paramètres par défaut (repères, non normatifs)
    DEFAULT_SIMULATIONS = 2_000
    MIN_VALID_RATIO = 0.50

    # ------------------------------------------------------------------------
    # EXECUTION PRINCIPALE
    # ------------------------------------------------------------------------

    def execute(
        self,
        financials: CompanyFinancials,
        params: DCFParameters
    ) -> DCFValuationResult:
        """
        Exécute une analyse Monte Carlo autour d’un DCF déterministe valide.

        Retour :
        - un DCFValuationResult
        - enrichi de distributions, quantiles et métriques d’incertitude
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
            "[Monte Carlo] Enabled | ticker=%s | simulations=%d",
            financials.ticker,
            num_simulations
        )

        if num_simulations < 500:
            raise CalculationError(
                "Nombre de simulations insuffisant pour une analyse robuste."
            )

        # ==============================================================
        # 1. PARAMÉTRAGE DES INCERTITUDES (GLASS BOX)
        # ==============================================================

        sigma_beta = params.beta_volatility or 0.10
        sigma_growth = params.growth_volatility or 0.015
        sigma_terminal = params.terminal_growth_volatility or 0.005

        # Corrélation économique standard :
        # hausse du risque → pression sur la croissance
        rho_beta_growth = -0.30

        self.add_step(
            label="Paramétrage des incertitudes Monte Carlo",
            theoretical_formula="σ, ρ",
            hypotheses=[
                TraceHypothesis("Beta volatility", sigma_beta, "%"),
                TraceHypothesis("Growth volatility", sigma_growth, "%"),
                TraceHypothesis("Terminal growth volatility", sigma_terminal, "%"),
                TraceHypothesis("Correlation (beta, growth)", rho_beta_growth)
            ],
            numerical_substitution="Définition des paramètres statistiques",
            result=1.0,
            unit="configuration",
            interpretation=(
                "Paramétrage des distributions probabilistes appliquées "
                "aux hypothèses exogènes du modèle."
            )
        )

        # ==============================================================
        # 2. GÉNÉRATION DES SCÉNARIOS STOCHASTIQUES
        # ==============================================================

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
            clip_max=0.04
        )

        self.add_step(
            label="Génération des scénarios Monte Carlo",
            theoretical_formula="Sampling multivarié corrélé",
            hypotheses=[
                TraceHypothesis("Simulations", num_simulations),
                TraceHypothesis("Distributions", "Normal / Corrélées")
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
        # 3. BOUCLE DE SIMULATION — MODÈLE DÉTERMINISTE INVARIANT
        # ==============================================================

        base_strategy = StandardFCFFStrategy()
        simulated_values: List[float] = []

        valid_runs = 0

        for i in range(num_simulations):

            sim_financials = replace(
                financials,
                beta=float(betas[i])
            )

            sim_params = replace(
                params,
                fcf_growth_rate=float(growths[i]),
                perpetual_growth_rate=float(terminal_growths[i])
            )

            try:
                result = base_strategy.execute(sim_financials, sim_params)
                iv = result.intrinsic_value_per_share

                # Filtre économique conservateur
                if 0.0 < iv < 50_000:
                    simulated_values.append(iv)
                    valid_runs += 1

            except Exception:
                # Un scénario instable est simplement rejeté
                continue

        valid_ratio = valid_runs / num_simulations

        self.add_step(
            label="Filtrage des scénarios valides",
            theoretical_formula="Valid / Total",
            hypotheses=[
                TraceHypothesis("Valid runs", valid_runs),
                TraceHypothesis("Total runs", num_simulations)
            ],
            numerical_substitution=f"{valid_runs} / {num_simulations}",
            result=valid_ratio,
            unit="ratio",
            interpretation=(
                "Élimination des scénarios économiquement aberrants "
                "ou numériquement instables."
            )
        )

        if valid_ratio < self.MIN_VALID_RATIO:
            raise CalculationError(
                "Trop peu de scénarios Monte Carlo valides. "
                "Analyse d’incertitude non fiable."
            )

        # ==============================================================
        # 4. SCÉNARIO PIVOT — DÉTERMINISTE PUR
        # ==============================================================

        final_result = base_strategy.execute(financials, params)

        self.add_step(
            label="Scénario pivot déterministe (P50)",
            theoretical_formula="DCF déterministe",
            hypotheses=[
                TraceHypothesis("Model", "Standard FCFF DCF"),
                TraceHypothesis("Nature", "Deterministic reference")
            ],
            numerical_substitution="Exécution sans stochasticité",
            result=final_result.intrinsic_value_per_share,
            unit=financials.currency,
            interpretation=(
                "Scénario central de référence, servant d’ancrage "
                "à l’analyse probabiliste."
            )
        )

        # ==============================================================
        # 5. ANALYSE STATISTIQUE DES SORTIES
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

        # La valeur centrale reste la médiane (robustesse)
        final_result.intrinsic_value_per_share = p50
        final_result.simulation_results = simulated_values
        final_result.quantiles = quantiles

        if final_result.market_price > 0:
            final_result.upside_pct = (
                p50 / final_result.market_price
            ) - 1.0

        self.add_step(
            label="Sélection de la valeur centrale",
            theoretical_formula="Median(simulations)",
            hypotheses=[
                TraceHypothesis("P10", p10, financials.currency),
                TraceHypothesis("P50", p50, financials.currency),
                TraceHypothesis("P90", p90, financials.currency),
                TraceHypothesis("Std dev", std, financials.currency)
            ],
            numerical_substitution="P50 retenu comme estimation centrale",
            result=p50,
            unit=financials.currency,
            interpretation=(
                "La médiane est privilégiée pour sa robustesse "
                "face aux distributions asymétriques."
            )
        )

        # ==============================================================
        # FINALISATION — TRACE GLASS BOX
        # ==============================================================

        final_result.calculation_trace.extend(self.trace)
        return final_result
