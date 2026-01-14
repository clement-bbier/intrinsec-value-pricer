"""
core/computation/financial_math.py

MOTEUR MATHÉMATIQUE FINANCIER — VERSION V9.0 (i18n Secured)
Architecture : Souveraineté Analyste avec isolation des segments Rates & Growth.
Rôle : Calculs financiers atomiques et déterminations du coût du capital.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from app.ui_components.ui_texts import CalculationErrors, StrategySources
from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters

logger = logging.getLogger(__name__)

# ==============================================================================
# TABLES DE RÉFÉRENCE (DAMODARAN)
# ==============================================================================

SPREADS_LARGE_CAP = [
    (8.5, 0.0045), (6.5, 0.0060), (5.5, 0.0077), (4.25, 0.0085),
    (3.0, 0.0095), (2.5, 0.0120), (2.25, 0.0155), (2.0, 0.0183),
    (1.75, 0.0261), (1.5, 0.0300), (1.25, 0.0442), (0.8, 0.0728),
    (0.65, 0.1010), (0.2, 0.1550), (-999, 0.1900)
]

SPREADS_SMALL_MID_CAP = [
    (12.5, 0.0045), (9.5, 0.0060), (7.5, 0.0077), (6.0, 0.0085),
    (4.5, 0.0095), (4.0, 0.0120), (3.5, 0.0155), (3.0, 0.0183),
    (2.5, 0.0261), (2.0, 0.0300), (1.5, 0.0442), (1.25, 0.0728),
    (0.8, 0.1010), (0.5, 0.1550), (-999, 0.1900)
]

@dataclass
class WACCBreakdown:
    cost_of_equity: float
    cost_of_debt_pre_tax: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    method: str

# ==============================================================================
# 1. VALEUR TEMPORELLE DE L'ARGENT (TIME VALUE OF MONEY)
# ==============================================================================

def calculate_discount_factors(rate: float, years: int) -> List[float]:
    """Génère les facteurs d'actualisation 1/(1+r)^t."""
    if rate <= -1.0:
        raise CalculationError(CalculationErrors.INVALID_DISCOUNT_RATE.format(rate=rate))
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, years + 1)]

def calculate_npv(flows: List[float], rate: float) -> float:
    """Calcule la Valeur Actuelle Nette (NPV) d'une série de flux."""
    factors = calculate_discount_factors(rate, len(flows))
    return sum(f * d for f, d in zip(flows, factors))

def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float) -> float:
    """Modèle de croissance perpétuelle (Gordon Growth)."""
    if rate <= g_perp:
        raise CalculationError(CalculationErrors.CONVERGENCE_IMPOSSIBLE.format(rate=rate, g=g_perp))
    return (final_flow * (1.0 + g_perp)) / (rate - g_perp)

def calculate_terminal_value_exit_multiple(final_metric: float, multiple: float) -> float:
    """Modèle de sortie par multiple (ex: EV/EBITDA final)."""
    if multiple < 0:
        raise CalculationError(CalculationErrors.NEGATIVE_EXIT_MULTIPLE)
    return final_metric * multiple

# ==============================================================================
# 2. COÛT DU CAPITAL (WACC / CAPM)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    """Modèle CAPM : Ke = Rf + Beta * MRP."""
    return rf + (beta * mrp)


def calculate_synthetic_cost_of_debt(
        rf: float,
        ebit: Optional[float],
        interest_expense: Optional[float],  # Renommé ici (était 'interest' ou 'interest_expense')
        market_cap: float
) -> float:
    """Estime le coût de la dette basé sur l'ICR (Synthetic Rating)."""
    safe_ebit = ebit if ebit is not None else 0.0
    safe_int = interest_expense if interest_expense is not None else 0.0  # Mise à jour ici

    if safe_int <= 0 or safe_ebit <= 0:
        return rf + 0.0107  # Spread par défaut A-rated proxy

    icr = safe_ebit / safe_int
    table = SPREADS_LARGE_CAP if market_cap >= 5_000_000_000 else SPREADS_SMALL_MID_CAP

    selected_spread = 0.20
    for threshold, spread in table:
        if icr >= threshold:
            selected_spread = spread
            break
    return rf + selected_spread

def calculate_wacc(financials: CompanyFinancials, params: DCFParameters) -> WACCBreakdown:
    """
    Calcul centralisé du WACC via segmentation V9.
    Intègre les surcharges Rates et Growth.
    """
    r, g = params.rates, params.growth

    # 1. Résolution des taux (Segment Rates)
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
    tax = r.tax_rate if r.tax_rate is not None else 0.25

    # 2. Résolution structurelle (Segment Growth pour surcharges)
    debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
    shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding

    # A. Coût des Fonds Propres (Ke)
    ke = r.manual_cost_of_equity if r.manual_cost_of_equity is not None else \
         calculate_cost_of_equity_capm(rf, r.manual_beta if r.manual_beta is not None else financials.beta, mrp)

    # B. Coût de la Dette (Kd)
    kd_gross = r.cost_of_debt if r.cost_of_debt is not None else \
               calculate_synthetic_cost_of_debt(rf, financials.ebit_ttm, financials.interest_expense, financials.market_cap)
    kd_net = kd_gross * (1.0 - tax)

    # C. Structure de Capital
    market_equity = financials.current_price * shares
    if g.target_equity_weight > 0 and g.target_debt_weight > 0:
        we, wd = g.target_equity_weight, g.target_debt_weight
        method = StrategySources.WACC_TARGET
    else:
        total_cap = market_equity + debt
        we, wd = (market_equity / total_cap, debt / total_cap) if total_cap > 0 else (1.0, 0.0)
        method = StrategySources.WACC_MARKET if total_cap > 0 else StrategySources.WACC_FALLBACK

    wacc_raw = (we * ke) + (wd * kd_net)
    wacc_final = r.wacc_override if r.wacc_override is not None else wacc_raw

    return WACCBreakdown(ke, kd_gross, kd_net, we, wd, wacc_final, method)

# ==============================================================================
# 3. MODÈLES SPÉCIFIQUES (INDISPENSABLES POUR RIM ET GRAHAM)
# ==============================================================================

def calculate_graham_1974_value(eps: float, growth_rate: float, aaa_yield: float) -> float:
    """Formule Révisée de Benjamin Graham (1974)."""
    # Rendement AAA par défaut si non fourni
    yield_val = aaa_yield if (aaa_yield and aaa_yield > 0) else 0.044

    # Conversion en points de base pour la formule (8.5 + 2g)
    g_scaled = (growth_rate if growth_rate is not None else 0.0) * 100.0
    y_scaled = yield_val * 100.0

    growth_multiplier = 8.5 + 2.0 * g_scaled
    rate_adjustment = 4.4 / y_scaled

    return eps * growth_multiplier * rate_adjustment

def calculate_rim_vectors(
    current_book_value: float,
    cost_of_equity: float,
    projected_earnings: List[float],
    payout_ratio: float
) -> Tuple[List[float], List[float]]:
    """
    Génère les vecteurs de Profit Résiduel (RI) et de Book Value (BV).
    Formule : RI_t = NI_t - (k_e * BV_{t-1})
    """
    book_values = []
    residual_incomes = []
    prev_bv = current_book_value

    for earnings in projected_earnings:
        # RI = Revenu Net - Charge du Capital
        equity_charge = prev_bv * cost_of_equity
        ri = earnings - equity_charge

        # Mise à jour de la Book Value (NI - Dividendes)
        dividend = earnings * (payout_ratio if payout_ratio is not None else 0.0)
        new_bv = prev_bv + earnings - dividend

        residual_incomes.append(ri)
        book_values.append(new_bv)
        prev_bv = new_bv

    return residual_incomes, book_values