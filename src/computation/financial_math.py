"""
src/computation/financial_math.py

MOTEUR MATHÉMATIQUE FINANCIER — VERSION V12.0 (Institutional Grade)

Sprint 4 : Finalisation Triangulation & Localisation Macro
Rôle : Calculs financiers atomiques, WACC, Ke et moteur de synthèse hybride.
Sources : Damodaran (Investment Valuation), McKinsey (Valuation).

Pattern : Pure Functions (Stateless)
Style : Numpy Style docstrings

RISQUES FINANCIERS:
- Point critique : erreur de formule = valorisation incorrecte
- Toute modification doit être validée contre le Golden Dataset

DEPENDANCES CRITIQUES:
- Aucune dépendance externe (mathématiques pures)
"""

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# DT-001/002: Import depuis core.i18n
from src.i18n import CalculationErrors, StrategySources
from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters
from src.config.constants import ValuationEngineDefaults, TechnicalDefaults, MacroDefaults

logger = logging.getLogger(__name__)

# ==============================================================================
# TABLES DE RÉFÉRENCE (DAMODARAN SYNTHETIC RATINGS)
# ==============================================================================

SPREADS_LARGE_CAP = ValuationEngineDefaults.SPREADS_LARGE_CAP
SPREADS_SMALL_MID_CAP = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

@dataclass
class WACCBreakdown:
    cost_of_equity: float
    cost_of_debt_pre_tax: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    method: str
    beta_used: float = 1.0  # Bêta utilisé pour le calcul du Ke
    beta_adjusted: bool = False  # Indique si le bêta a été réendetté

# ==============================================================================
# 1. TIME VALUE OF MONEY & TERMINAL VALUES
# ==============================================================================

def calculate_discount_factors(rate: float, years: int) -> List[float]:
    """Génère les facteurs d'actualisation $1/(1+r)^t$."""
    if rate <= -1.0:
        raise CalculationError(CalculationErrors.INVALID_DISCOUNT_RATE.format(rate=rate))
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, years + 1)]

def calculate_npv(flows: List[float], rate: float) -> float:
    """Valeur Actuelle Nette (NPV) d'une série de flux."""
    factors = calculate_discount_factors(rate, len(flows))
    return sum(f * d for f, d in zip(flows, factors))

def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float) -> float:
    """Modèle de croissance perpétuelle (Gordon Growth)."""
    if rate <= g_perp:
        raise CalculationError(CalculationErrors.CONVERGENCE_IMPOSSIBLE.format(rate=rate, g=g_perp))
    return (final_flow * (1.0 + g_perp)) / (rate - g_perp)

def calculate_terminal_value_exit_multiple(final_metric: float, multiple: float) -> float:
    """Modèle de sortie par multiple (EBITDA ou Revenus)."""
    if multiple < 0:
        raise CalculationError(CalculationErrors.NEGATIVE_EXIT_MULTIPLE)
    return final_metric * multiple

def calculate_terminal_value_pe(final_net_income: float, pe_multiple: float) -> float:
    """Valeur terminale Equity : Applique un multiple P/E au résultat net terminal."""
    if pe_multiple <= 0:
        raise CalculationError("Le multiple P/E doit être strictement positif.")
    return final_net_income * pe_multiple

def calculate_dilution_factor(annual_rate: Optional[float], years: int) -> float:
    """
    Calcule le facteur de dilution cumulé sur la période de projection.

    Si une entreprise émet 2% d'actions nouvelles par an (SBC) pendant 5 ans,
    la part des actionnaires actuels est divisée par (1 + 0.02)^5.

    Parameters
    ----------
    annual_rate : float, optional
        Taux de dilution annuel (ex: 0.02 pour 2%).
    years : int
        Nombre d'années de projection.

    Returns
    -------
    float
        Le multiplicateur de shares à appliquer au dénominateur (défaut: 1.0).
    """
    if annual_rate is None or annual_rate <= 0:
        return 1.0
    return (1.0 + annual_rate) ** years


def apply_dilution_to_price(price: float, dilution_factor: float) -> float:
    """Applique le facteur de dilution au prix par action final."""
    if dilution_factor <= 1.0:
        return price
    return price / dilution_factor

# ==============================================================================
# 2. COÛT DU CAPITAL (WACC / Ke / SYNTETHIC DEBT)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    """Modèle CAPM standard : $k_e = R_f + \beta \times MRP$."""
    return rf + (beta * mrp)

def unlever_beta(beta_levered: float, tax_rate: float, debt_equity_ratio: float) -> float:
    """
    Désendettement du bêta selon la formule de Hamada.
    βU = βL / [1 + (1 - T) × (D/E)]
    """
    if debt_equity_ratio <= 0:
        return beta_levered  # Si pas d'endettement, bêta inchangé
    return beta_levered / (1.0 + (1.0 - tax_rate) * debt_equity_ratio)

def relever_beta(beta_unlevered: float, tax_rate: float, target_debt_equity_ratio: float) -> float:
    """
    Réendettement du bêta selon la formule de Hamada.
    βL = βU × [1 + (1 - T) × (D/E)]
    """
    if target_debt_equity_ratio <= 0:
        return beta_unlevered  # Si pas d'endettement cible, bêta inchangé
    return beta_unlevered * (1.0 + (1.0 - tax_rate) * target_debt_equity_ratio)

def calculate_cost_of_equity(financials: CompanyFinancials, params: DCFParameters) -> float:
    """Isole le calcul du Ke pour les modèles Direct Equity."""
    r = params.rates
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
    beta = r.manual_beta if r.manual_beta is not None else (financials.beta or 1.0)

    if r.manual_cost_of_equity is not None:
        return r.manual_cost_of_equity

    return calculate_cost_of_equity_capm(rf, beta, mrp)

def calculate_synthetic_cost_of_debt(rf: float, ebit: Optional[float], interest_expense: Optional[float], market_cap: float) -> float:
    """Estime le coût de la dette basé sur l'ICR (Synthetic Rating)."""
    safe_ebit, safe_int = ebit or 0.0, interest_expense or 0.0

    if safe_int <= 0 or safe_ebit <= 0:
        return rf + 0.0107  # Proxy spread A-rated

    icr = safe_ebit / safe_int
    table = SPREADS_LARGE_CAP if market_cap >= MacroDefaults.LARGE_CAP_THRESHOLD else SPREADS_SMALL_MID_CAP

    for threshold, spread in table:
        if icr >= threshold:
            return rf + spread
    return rf + 0.1900

def calculate_wacc(financials: CompanyFinancials, params: DCFParameters) -> WACCBreakdown:
    """Calcul centralisé du WACC (Firm Value Approach)."""
    r, g = params.rates, params.growth
    ke = calculate_cost_of_equity(financials, params)

    tax = r.tax_rate if r.tax_rate is not None else 0.25
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    kd_gross = r.cost_of_debt if r.cost_of_debt is not None else calculate_synthetic_cost_of_debt(rf, financials.ebit_ttm, financials.interest_expense, financials.market_cap)
    kd_net = kd_gross * (1.0 - tax)

    debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
    shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
    market_equity = financials.current_price * shares

    total_cap = market_equity + debt
    we, wd = (market_equity / total_cap, debt / total_cap) if total_cap > 0 else (1.0, 0.0)

    # Bêta utilisé pour le calcul (avant ajustement potentiel)
    beta_original = r.manual_beta if r.manual_beta is not None else (financials.beta or 1.0)
    beta_used = beta_original
    beta_adjusted = False

    # Logique de réendettement du bêta (formule de Hamada)
    if g.target_equity_weight is not None and g.target_debt_weight is not None and g.target_equity_weight > 0:
        target_debt_equity_ratio = g.target_debt_weight / g.target_equity_weight

        # Désendetter le bêta observé vers un bêta sans dette
        beta_unlevered = unlever_beta(beta_original, tax, debt / market_equity if market_equity > 0 else 0.0)

        # Réendetter vers la structure cible
        beta_used = relever_beta(beta_unlevered, tax, target_debt_equity_ratio)
        beta_adjusted = True

        # Recalculer le Ke avec le bêta ajusté
        mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
        ke = calculate_cost_of_equity_capm(rf, beta_used, mrp)

    wacc_raw = (we * ke) + (wd * kd_net)
    return WACCBreakdown(
        ke, kd_gross, kd_net, we, wd, r.wacc_override or wacc_raw, StrategySources.WACC_MARKET,
        beta_used, beta_adjusted
    )

# ==============================================================================
# 3. MODÈLES ACTIONNAIRES (FCFE & DDM)
# ==============================================================================

def calculate_fcfe_reconstruction(ni: float, adjustments: float, net_borrowing: float) -> float:
    """Reconstruction du FCFE (Clean Walk) : NI + Adj + Net Borrowing."""
    return ni + adjustments + net_borrowing

def calculate_fcfe_base(fcff: float, interest: float, tax_rate: float, net_borrowing: float) -> float:
    """Formule classique du FCFE dérivée du FCFF."""
    return fcff - (interest * (1.0 - tax_rate)) + net_borrowing

def calculate_sustainable_growth(roe: float, payout_ratio: float) -> float:
    """$g = ROE \times (1 - Payout)$"""
    return roe * (1.0 - (payout_ratio or 0.0))

# ==============================================================================
# 4. MODÈLES SPÉCIFIQUES (RIM & GRAHAM)
# ==============================================================================

def calculate_graham_1974_value(eps: float, growth_rate: float, aaa_yield: float) -> float:
    """Formule Révisée de Graham (1974)."""
    y = aaa_yield if (aaa_yield and aaa_yield > 0) else TechnicalDefaults.DEFAULT_AAA_YIELD
    return (eps * (8.5 + 2.0 * (growth_rate * 100)) * 4.4) / (y * 100)

def calculate_rim_vectors(current_bv: float, ke: float, earnings: List[float], payout: float) -> Tuple[List[float], List[float]]:
    """Génère les vecteurs de Profit Résiduel et de Book Value."""
    book_values, residual_incomes = [], []
    prev_bv = current_bv
    for ni in earnings:
        ri = ni - (prev_bv * ke)
        new_bv = prev_bv + ni - (ni * payout)
        residual_incomes.append(ri); book_values.append(new_bv)
        prev_bv = new_bv
    return residual_incomes, book_values

def compute_proportions(*values: Optional[float], fallback_index: int = 0) -> List[float]:
    """Helper pour normaliser des poids de structure financière."""
    clean_values = [v or 0.0 for v in values]
    total = sum(clean_values)
    if total <= 0:
        res = [0.0] * len(clean_values); res[fallback_index] = 1.0; return res
    return [v / total for v in clean_values]

# ==============================================================================
# 5. MULTIPLES & TRIANGULATION (RELATIVE VALUATION)
# ==============================================================================

def calculate_price_from_pe_multiple(net_income: float, median_pe: float, shares: float) -> float:
    """Calcule le prix théorique via le multiple P/E : $P = (NI \times P/E) / Shares$."""
    if shares <= 0 or median_pe <= 0:
        return 0.0
    return (net_income * median_pe) / shares

def calculate_price_from_ev_multiple(
    metric_value: float,
    median_ev_multiple: float,
    net_debt: float,
    shares: float,
    minorities: float = 0.0,
    pensions: float = 0.0
) -> float:
    """
    Conversion d'un multiple d'Enterprise Value en Prix par Action (Equity Bridge).
    Standard McKinsey : (EV - DetteNette - Minoritaires - Pensions) / Actions
    """
    if shares <= 0 or median_ev_multiple <= 0:
        return 0.0

    enterprise_value = metric_value * median_ev_multiple
    equity_value = enterprise_value - net_debt - minorities - pensions
    return max(0.0, equity_value / shares)

def calculate_triangulated_price(
    valuation_signals: Dict[str, float],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Réalise la synthèse de plusieurs signaux de prix (Triangulation).
    Filtre les signaux invalides et applique une pondération.
    """
    # 1. Extraction des signaux valides (Honest Data)
    valid_signals = {k: v for k, v in valuation_signals.items() if v > 0}
    if not valid_signals:
        return 0.0

    # 2. Cas sans poids explicites : Moyenne simple
    if not weights:
        return sum(valid_signals.values()) / len(valid_signals)

    # 3. Moyenne pondérée sur les signaux disponibles
    active_weights = {k: weights[k] for k in valid_signals if k in weights}
    total_weight = sum(active_weights.values())

    if total_weight <= 0:
        return sum(valid_signals.values()) / len(valid_signals)

    weighted_sum = sum(valid_signals[k] * active_weights[k] for k in active_weights)
    return weighted_sum / total_weight
