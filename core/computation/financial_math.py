"""
core/computation/financial_math.py

MOTEUR MATHÉMATIQUE FINANCIER — VERSION V10.0 (i18n Secured)
Sprint 3 : Expansion Analytique (DDM & FCFE)
Rôle : Calculs financiers atomiques, WACC, Ke et flux actionnaires.
Sources : Damodaran (Investment Valuation), McKinsey (Valuation).
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
# 2. COÛT DU CAPITAL (WACC / CAPM / Ke)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    """Modèle CAPM standard : Ke = Rf + Beta * MRP."""
    return rf + (beta * mrp)

def calculate_cost_of_equity(financials: CompanyFinancials, params: DCFParameters) -> float:
    """
    Isole le calcul du Ke (Cost of Equity) via les segments Rates.
    Utilisé pour DDM et FCFE.
    """
    r = params.rates
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
    beta = r.manual_beta if r.manual_beta is not None else financials.beta

    if r.manual_cost_of_equity is not None:
        return r.manual_cost_of_equity

    return calculate_cost_of_equity_capm(rf, beta, mrp)

def calculate_synthetic_cost_of_debt(
        rf: float,
        ebit: Optional[float],
        interest_expense: Optional[float],
        market_cap: float
) -> float:
    """Estime le coût de la dette basé sur l'ICR (Synthetic Rating Damodaran)."""
    safe_ebit = ebit if ebit is not None else 0.0
    safe_int = interest_expense if interest_expense is not None else 0.0

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
    """Calcul centralisé du WACC (Approach Firm Value)."""
    r, g = params.rates, params.growth

    # 1. Résolution Ke
    ke = calculate_cost_of_equity(financials, params)

    # 2. Résolution Kd
    tax = r.tax_rate if r.tax_rate is not None else 0.25
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    kd_gross = r.cost_of_debt if r.cost_of_debt is not None else \
               calculate_synthetic_cost_of_debt(rf, financials.ebit_ttm, financials.interest_expense, financials.market_cap)
    kd_net = kd_gross * (1.0 - tax)

    # 3. Structure de Capital
    debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
    shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
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
# 3. MODÈLES ACTIONNAIRES
# ==============================================================================

def calculate_fcfe_base(fcff: float, interest: float, tax_rate: float, net_borrowing: float) -> float:
    """
    Formule rigoureuse du FCFE (Free Cash Flow to Equity).
    Source : Damodaran.
    FCFE = FCFF - Intérêts * (1 - Taux_Imposition) + Variation_Nette_Dette
    """
    tax_adj_interest = interest * (1.0 - tax_rate)
    return fcff - tax_adj_interest + net_borrowing

def calculate_sustainable_growth(roe: float, payout_ratio: float) -> float:
    """
    Calcule le taux de croissance soutenable (Sustainable Growth Rate).
    Source : CFA Institute / McKinsey.
    g = ROE * Retention_Ratio (où Retention_Ratio = 1 - Payout)
    """
    retention_ratio = 1.0 - payout_ratio
    return roe * retention_ratio

# ==============================================================================
# 4. MODÈLES SPÉCIFIQUES (RIM & GRAHAM)
# ==============================================================================

def calculate_graham_1974_value(eps: float, growth_rate: float, aaa_yield: float) -> float:
    """Formule Révisée de Benjamin Graham (1974)."""
    yield_val = aaa_yield if (aaa_yield and aaa_yield > 0) else 0.044
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
    """Génère les vecteurs de Profit Résiduel (RI) et de Book Value (BV)."""
    book_values = []
    residual_incomes = []
    prev_bv = current_book_value

    for earnings in projected_earnings:
        equity_charge = prev_bv * cost_of_equity
        ri = earnings - equity_charge
        dividend = earnings * (payout_ratio if payout_ratio is not None else 0.0)
        new_bv = prev_bv + earnings - dividend
        residual_incomes.append(ri)
        book_values.append(new_bv)
        prev_bv = new_bv

    return residual_incomes, book_values

def compute_proportions(*values: Optional[float], fallback_index: int = 0) -> List[float]:
    """Calcule des proportions normalisées (somme = 1.0)."""
    clean_values = [v or 0.0 for v in values]
    total = sum(clean_values)
    if total <= 0:
        result = [0.0] * len(clean_values)
        result[fallback_index] = 1.0
        return result
    return [v / total for v in clean_values]