"""
core/computation/statistics.py

OUTILS STATISTIQUES — EXTENSION MONTE CARLO
Version : V2.0 — Chapitre 7 conforme

STATUT
------
Ce module fournit exclusivement des OUTILS STATISTIQUES GÉNÉRIQUES
destinés à la génération de scénarios probabilistes.

Principes non négociables :
- AUCUNE logique financière ici
- AUCUNE dépendance à un modèle de valorisation
- Fonctions pures, déterministes à seed fixé
- Monte Carlo agit uniquement sur les INPUTS

Ce module est volontairement :
- simple
- testable
- audit-friendly
- réutilisable

Références :
- CFA Institute — Sensitivity & Scenario Analysis
- Glasserman — Monte Carlo Methods in Financial Engineering
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

    Utilisation typique :
    - corrélation négative risque ↔ croissance
    - propagation cohérente de l’incertitude

    Paramètres
    ----------
    mu_beta : float
        Espérance du beta.
    sigma_beta : float
        Volatilité du beta (> 0).
    mu_growth : float
        Espérance de la croissance.
    sigma_growth : float
        Volatilité de la croissance (> 0).
    rho : float
        Coefficient de corrélation [-1 ; 1].
    num_simulations : int
        Nombre de scénarios Monte Carlo.
    seed : int | None
        Seed aléatoire pour reproductibilité.

    Retour
    ------
    betas : np.ndarray
    growths : np.ndarray
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations doit être strictement positif.")

    if not (-1.0 <= rho <= 1.0):
        raise ValueError("Le coefficient de corrélation rho doit être dans [-1, 1].")

    if sigma_beta < 0 or sigma_growth < 0:
        raise ValueError("Les volatilités doivent être positives ou nulles.")

    # Seed pour reproductibilité (audit / tests)
    if seed is not None:
        np.random.seed(seed)

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
    draws = np.random.multivariate_normal(
        mean=mean_vector,
        cov=cov_matrix,
        size=num_simulations
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

    Cas d’usage typique :
    - croissance terminale
    - multiples
    - paramètres faiblement corrélés

    Paramètres
    ----------
    mean : float
        Espérance de la distribution.
    sigma : float
        Volatilité (> 0).
    num_simulations : int
        Nombre de tirages.
    clip_min : float | None
        Borne inférieure optionnelle.
    clip_max : float | None
        Borne supérieure optionnelle.
    seed : int | None
        Seed aléatoire optionnelle.

    Retour
    ------
    draws : np.ndarray
    """

    if num_simulations <= 0:
        raise ValueError("num_simulations doit être strictement positif.")

    if sigma < 0:
        raise ValueError("sigma doit être positif ou nul.")

    if seed is not None:
        np.random.seed(seed)

    # ------------------------------------------------------------------
    # TIRAGE NORMAL
    # ------------------------------------------------------------------
    draws = np.random.normal(
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
