"""
core/computation/financial_math.py

MOTEUR MATHÉMATIQUE FINANCIER
Version : V3.1 — Souveraineté Analyste (None=Auto Logic)

Standardisation :
- Gestion stricte du paradigm "None = Delegation" vs "0.0 = Value".
- Suppression des opérateurs 'or' sur les types numériques.
- Protocoles de secours (Fallbacks) pour le WACC et la fiscalité.
- Lève des CalculationError explicites en cas d'aberration.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from core.exceptions import CalculationError
from core.models import CompanyFinancials, DCFParameters

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTES & TABLES DE RÉFÉRENCE (DAMODARAN)
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
    """Génère le vecteur d'actualisation : [1/(1+r)^1, ..., 1/(1+r)^N]."""
    if rate <= -1.0:
        raise CalculationError(f"Taux d'actualisation invalide : {rate:.2%}")
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, years + 1)]


def calculate_npv(flows: List[float], rate: float) -> float:
    """Calcule la Valeur Actuelle Nette (NPV)."""
    factors = calculate_discount_factors(rate, len(flows))
    return sum(f * d for f, d in zip(flows, factors))


def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float) -> float:
    """Modèle de Gordon-Shapiro. Invariant : rate > g_perp."""

    if rate <= g_perp:
        raise CalculationError(
            f"Convergence impossible : Taux ({rate:.2%}) <= Croissance ({g_perp:.2%})."
        )
    return (final_flow * (1.0 + g_perp)) / (rate - g_perp)


def calculate_terminal_value_exit_multiple(final_metric: float, multiple: float) -> float:
    """Modèle de Sortie par Multiple."""
    if multiple < 0:
        raise CalculationError("Le multiple de sortie ne peut pas être négatif.")
    return final_metric * multiple


def calculate_equity_value_bridge(enterprise_value: float, total_debt: float, cash: float, minorities: float = 0.0, pensions: float = 0.0) -> float:
    """Passage de l'Enterprise Value (EV) à l'Equity Value."""
    return enterprise_value - total_debt + cash - minorities - pensions


# ==============================================================================
# 2. COÛT DU CAPITAL (WACC / CAPM)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    """Modèle CAPM : Ke = Rf + Beta * MRP"""
    return rf + (beta * mrp)


def calculate_synthetic_cost_of_debt(
        rf: float,
        ebit: Optional[float],
        interest_expense: Optional[float],
        market_cap: float
) -> float:
    """
    Estime le coût de la dette (Rf + Spread) basé sur l'ICR.
    Sécurisé pour gérer les données manquantes (None-Safe).
    """
    # 1. Normalisation des entrées (None -> 0.0 pour les tests logiques)
    safe_ebit = ebit if ebit is not None else 0.0
    safe_interest = interest_expense if interest_expense is not None else 0.0

    # 2. Cas de défaut : Pas d'intérêt ou pas d'EBIT (Incapacité de calcul ICR)
    if safe_interest <= 0 or safe_ebit <= 0:
        # On applique un spread prudent (A-rated proxy)
        return rf + 0.0107

    # 3. Calcul de l'Interest Coverage Ratio (ICR)
    icr = safe_ebit / safe_interest

    # 4. Sélection de la table de spread selon la capitalisation
    is_large = market_cap >= 5_000_000_000
    table = SPREADS_LARGE_CAP if is_large else SPREADS_SMALL_MID_CAP

    # 5. Recherche du spread par paliers (Waterfall lookup)
    selected_spread = 0.20  # Défaut Junk/Caa
    for threshold, spread_value in table:
        if icr >= threshold:
            selected_spread = spread_value
            break

    return rf + selected_spread


def calculate_wacc(financials: CompanyFinancials, params: DCFParameters) -> WACCBreakdown:
    """Calcul centralisé du WACC avec respect du paradigme None=Auto."""


    # 1. Résolution des taux de base (Fallbacks normatifs si None)
    rf = params.risk_free_rate if params.risk_free_rate is not None else 0.04
    mrp = params.market_risk_premium if params.market_risk_premium is not None else 0.05
    tax_to_use = params.tax_rate if params.tax_rate is not None else 0.25

    # 2. Détermination des composantes structurelles
    debt_to_use = params.manual_total_debt if params.manual_total_debt is not None else financials.total_debt
    shares_to_use = params.manual_shares_outstanding if params.manual_shares_outstanding is not None else financials.shares_outstanding

    # A. Cost of Equity (Ke)
    if params.manual_cost_of_equity is not None:
        ke = params.manual_cost_of_equity
    else:
        beta_to_use = params.manual_beta if params.manual_beta is not None else financials.beta
        ke = calculate_cost_of_equity_capm(rf, beta_to_use, mrp)

    # B. Cost of Debt (Kd)
    if params.cost_of_debt is not None:
        kd_gross = params.cost_of_debt
    else:
        # Délégation au modèle synthétique si Kd n'est pas fourni
        kd_gross = calculate_synthetic_cost_of_debt(
            rf=rf,
            ebit=financials.ebit_ttm if financials.ebit_ttm is not None else 0.0,
            interest_expense=financials.interest_expense if financials.interest_expense is not None else 0.0,
            market_cap=financials.market_cap
        )

    kd_net = kd_gross * (1.0 - tax_to_use)

    # C. Poids de la structure de capital
    market_equity = financials.current_price * shares_to_use

    if params.target_equity_weight > 0 and params.target_debt_weight > 0:
        we = params.target_equity_weight
        wd = params.target_debt_weight
        method = "TARGET"
    else:
        total_cap = market_equity + debt_to_use
        if total_cap <= 0:
            we, wd = 1.0, 0.0
            method = "FALLBACK_EQUITY"
        else:
            we = market_equity / total_cap
            wd = debt_to_use / total_cap
            method = "MARKET"

    wacc_raw = (we * ke) + (wd * kd_net)

    # D. Surcharge finale
    if params.wacc_override is not None:
        wacc_final = params.wacc_override
        method = "MANUAL_OVERRIDE"
    else:
        wacc_final = wacc_raw

    return WACCBreakdown(
        cost_of_equity=ke,
        cost_of_debt_pre_tax=kd_gross,
        cost_of_debt_after_tax=kd_net,
        weight_equity=we,
        weight_debt=wd,
        wacc=wacc_final,
        method=method
    )


# ==============================================================================
# 3. MODÈLES SPÉCIFIQUES
# ==============================================================================

def calculate_graham_1974_value(eps: float, growth_rate: float, aaa_yield: float) -> float:
    """Formule Révisée de Benjamin Graham (1974)."""
    if aaa_yield is None or aaa_yield <= 0:
        # Fallback institutionnel si le rendement AAA est manquant
        aaa_yield = 0.044

    # Conversion stricte pour le modèle (8.5 + 2g)
    g_scaled = (growth_rate if growth_rate is not None else 0.0) * 100.0
    y_scaled = aaa_yield * 100.0

    growth_multiplier = 8.5 + 2.0 * g_scaled
    rate_adjustment = 4.4 / y_scaled

    return eps * growth_multiplier * rate_adjustment


def calculate_rim_vectors(
        current_book_value: float,
        cost_of_equity: float,
        projected_earnings: List[float],
        payout_ratio: float
) -> Tuple[List[float], List[float]]:
    """Residual Income Model Vectors."""
    book_values = []
    residual_incomes = []
    prev_bv = current_book_value

    for earnings in projected_earnings:
        dividend = earnings * (payout_ratio if payout_ratio is not None else 0.0)
        equity_charge = prev_bv * cost_of_equity
        ri = earnings - equity_charge
        new_bv = prev_bv + earnings - dividend

        residual_incomes.append(ri)
        book_values.append(new_bv)
        prev_bv = new_bv

    return residual_incomes, book_values