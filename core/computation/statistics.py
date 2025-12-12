import numpy as np
from typing import Tuple, List

def generate_multivariate_samples(
    mu_beta: float,
    sigma_beta: float,
    mu_growth: float,
    sigma_growth: float,
    rho: float,
    num_simulations: int,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère des tirages corrélés pour le Beta et la Croissance.
    
    Args:
        rho: Coefficient de corrélation (ex: -0.4).
        
    Returns:
        Tuple (betas, growths) sous forme de tableaux numpy.
    """
    np.random.seed(seed)
    
    # 1. Matrice de Covariance
    # Cov(X,Y) = rho * sigma_X * sigma_Y
    covariance = rho * sigma_beta * sigma_growth
    
    cov_matrix = [
        [sigma_beta ** 2, covariance],
        [covariance, sigma_growth ** 2]
    ]
    mean_vector = [mu_beta, mu_growth]
    
    # 2. Tirage Multivarié
    draws = np.random.multivariate_normal(mean_vector, cov_matrix, num_simulations)
    
    betas = draws[:, 0]
    growths = draws[:, 1]
    
    return betas, growths

def generate_independent_samples(
    mean: float,
    sigma: float,
    num_simulations: int,
    clip_min: float = None, # type: ignore
    clip_max: float = None # type: ignore
) -> np.ndarray:
    """Génère des tirages selon une loi normale indépendante avec bornes optionnelles."""
    draws = np.random.normal(loc=mean, scale=sigma, size=num_simulations)
    
    if clip_min is not None or clip_max is not None:
        # np.clip gère None comme infini si besoin, ou on check explicitement
        c_min = clip_min if clip_min is not None else -np.inf
        c_max = clip_max if clip_max is not None else np.inf
        draws = np.clip(draws, c_min, c_max)
        
    return draws