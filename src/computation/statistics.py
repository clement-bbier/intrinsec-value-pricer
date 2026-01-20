"""
Outils statistiques pour les simulations Monte Carlo.

Ce module fournit les fonctions de génération de tirages aléatoires
utilisées dans les analyses de sensibilité probabilistes.
"""

from __future__ import annotations

from typing import Tuple, Optional
import numpy as np


# ============================================================================
# GÉNÉRATION DE TIRAGES CORRÉLÉS
# ============================================================================

def generate_multivariate_samples(
    *,
    mu_beta: float,
    sigma_beta: float,
    mu_growth: float,
    sigma_growth: float,
    rho: float,
    num_simulations: int,
    seed: Optional[int] = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère des tirages corrélés pour deux variables continues
    (ex : Beta et Croissance).

    Supporte les volatilités à 0.0 (scénario déterministe).
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations doit être strictement positif.")

    if not (-1.0 <= rho <= 1.0):
        raise ValueError("Le coefficient de corrélation rho doit être dans [-1, 1].")

    if sigma_beta < 0 or sigma_growth < 0:
        raise ValueError("Les volatilités doivent être positives ou nulles.")

    # INITIALISATION DU GÉNÉRATEUR (MODERN NUMPY 2026)
    # L'utilisation de default_rng évite de polluer l'état global np.random
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # MATRICE DE COVARIANCE
    # ------------------------------------------------------------------
    # Cov(X, Y) = rho × σ_X × σ_Y
    covariance = rho * sigma_beta * sigma_growth

    cov_matrix = np.array([
        [sigma_beta ** 2, covariance],
        [covariance, sigma_growth ** 2]
    ])

    mean_vector = np.array([mu_beta, mu_growth])

    # ------------------------------------------------------------------
    # TIRAGE MULTIVARIÉ
    # ------------------------------------------------------------------
    # method='svd' est plus robuste pour les matrices semi-définies positives
    # (cas où sigma_beta ou sigma_growth valent 0.0)
    draws = rng.multivariate_normal(
        mean=mean_vector,
        cov=cov_matrix,
        size=num_simulations,
        method='svd'
    )

    betas = draws[:, 0]
    growths = draws[:, 1]

    return betas, growths


# ============================================================================
# GÉNÉRATION DE TIRAGES INDÉPENDANTS
# ============================================================================

def generate_independent_samples(
    *,
    mean: float,
    sigma: float,
    num_simulations: int,
    clip_min: Optional[float] = None,
    clip_max: Optional[float] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Génère des tirages indépendants suivant une loi normale,
    avec bornes optionnelles.
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations doit être strictement positif.")

    if sigma < 0:
        raise ValueError("sigma doit être positif ou nul.")

    # INITIALISATION DU GÉNÉRATEUR LOCAL
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # TIRAGE NORMAL
    # ------------------------------------------------------------------
    draws = rng.normal(
        loc=mean,
        scale=sigma,
        size=num_simulations
    )

    # ------------------------------------------------------------------
    # CLIPPING ÉCONOMIQUE (OPTIONNEL)
    # ------------------------------------------------------------------
    if clip_min is not None or clip_max is not None:
        c_min = clip_min if clip_min is not None else -np.inf
        c_max = clip_max if clip_max is not None else np.inf

        if c_min > c_max:
            raise ValueError("clip_min ne peut pas être supérieur à clip_max.")

        draws = np.clip(draws, c_min, c_max)

    return draws
