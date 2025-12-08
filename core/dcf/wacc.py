import logging
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)

# ==============================================================================
# TABLES DE SPREAD DAMODARAN (Mise à jour 2024/2025)
# Source: Damodaran Online (Ratings & Spreads)
# ==============================================================================

# TABLE 1 : Pour les LARGE CAPS (Capitalisation > 5 Milliards $)
# Les grandes entreprises sont jugées moins sévèrement pour un même ratio.
SPREADS_LARGE_CAP = [
    (8.5, 0.0069),  # Aaa/AAA
    (6.5, 0.0085),  # Aa2/AA
    (5.5, 0.0107),  # A1/A+
    (4.25, 0.0118),  # A2/A
    (3.0, 0.0133),  # A3/A-
    (2.5, 0.0171),  # Baa2/BBB
    (2.25, 0.0213),  # Ba1/BB+
    (2.0, 0.0277),  # Ba2/BB
    (1.75, 0.0384),  # B1/B+
    (1.5, 0.0490),  # B2/B
    (1.25, 0.0597),  # B3/B-
    (0.8, 0.0756),  # Caa/CCC
    (0.65, 0.1060),  # Ca2/CC
    (0.2, 0.1500),  # C2/C
    (-999, 0.2000)  # D2/D
]

# TABLE 2 : Pour les SMALL/MID CAPS (Capitalisation < 5 Milliards $)
# Les seuils sont plus stricts : il faut un meilleur ICR pour avoir la même note.
SPREADS_SMALL_MID_CAP = [
    (12.5, 0.0069),  # Aaa/AAA (Il faut 12.5x de couverture vs 8.5x pour une Large Cap)
    (9.5, 0.0085),  # Aa2/AA
    (7.5, 0.0107),  # A1/A+
    (6.0, 0.0118),  # A2/A
    (4.5, 0.0133),  # A3/A-
    (4.0, 0.0171),  # Baa2/BBB
    (3.5, 0.0213),  # Ba1/BB+
    (3.0, 0.0277),  # Ba2/BB
    (2.5, 0.0384),  # B1/B+
    (2.0, 0.0490),  # B2/B
    (1.5, 0.0597),  # B3/B-
    (1.25, 0.0756),  # Caa/CCC
    (0.8, 0.1060),  # Ca2/CC
    (0.5, 0.1500),  # C2/C
    (-999, 0.2000)  # D2/D
]


def _get_spread_from_table(icr: float, table: list) -> float:
    """Parcourt la table donnée et retourne le spread correspondant."""
    for threshold, spread in table:
        if icr >= threshold:
            return spread
    return 0.20  # Fallback Default


def compute_cost_of_equity(risk_free_rate: float, beta: float, market_risk_premium: float) -> float:
    """CAPM classique."""
    re = risk_free_rate + beta * market_risk_premium
    logger.info("[WACC] Cost of Equity (CAPM) = %.2f%% + %.2f * %.2f%% = %.2f%%",
                risk_free_rate * 100, beta, market_risk_premium * 100, re * 100)
    return re


def compute_synthetic_cost_of_debt(
        risk_free_rate: float,
        ebit: float,
        interest_expense: float,
        equity_value_market: float  # NOUVEAU : Nécessaire pour déterminer la taille
) -> float:
    """
    Calcule un Coût de la Dette Synthétique (Rd) en utilisant les tables de Damodaran
    adaptées à la taille de l'entreprise (Large vs Small/Mid Cap).
    """

    # 1. Gestion des cas limites (Dette nulle ou Intérêts négatifs/nuls)
    if interest_expense <= 0:
        logger.info("[WACC] Pas de charges d'intérêts significatives. Spread par défaut (A+).")
        return risk_free_rate + 0.0107

    # 2. Calcul du Ratio de Couverture (ICR)
    icr = ebit / interest_expense

    # 3. Choix de la table selon la capitalisation boursière (Seuil ~5 Milliards USD)
    # Note: On compare equity_value_market (qui est convertie dans la devise de l'analyse).
    # Si la devise n'est pas USD, le seuil 5e9 est approximatif mais reste pertinent pour l'ordre de grandeur.
    IS_LARGE_CAP = equity_value_market >= 5_000_000_000

    if IS_LARGE_CAP:
        spread = _get_spread_from_table(icr, SPREADS_LARGE_CAP)
        cap_type = "Large Cap"
    else:
        spread = _get_spread_from_table(icr, SPREADS_SMALL_MID_CAP)
        cap_type = "Small/Mid Cap"

    rd = risk_free_rate + spread

    logger.info(
        "[WACC] Rd Synthétique (%s): EBIT=%.0f / Int=%.0f -> ICR=%.2f -> Spread=%.2f%% -> Rd=%.2f%%",
        cap_type, ebit, interest_expense, icr, spread * 100, rd * 100
    )
    return rd


def compute_wacc(
        equity_value: float,
        debt_value: float,
        cost_of_equity: float,
        cost_of_debt: float,
        tax_rate: float,
) -> tuple[float, float]:
    total_value = equity_value + debt_value
    if total_value <= 0:
        raise CalculationError("Capital total (E + D) doit être positif.")

    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    after_tax_cost_of_debt = cost_of_debt * (1.0 - tax_rate)
    wacc = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt

    logger.info("[WACC] WACC Final: %.2f%% (We=%.2f, Wd=%.2f, Rd_net=%.2f%%)",
                wacc * 100, weight_equity, weight_debt, after_tax_cost_of_debt * 100)
    return wacc, after_tax_cost_of_debt