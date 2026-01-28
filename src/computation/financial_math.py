"""
src/computation/financial_math.py

ATOMIC FINANCIAL MATHEMATICAL CALCULATIONS
===========================================
Role: Core implementation of fundamental financial formulas used in valuations.
Scope: WACC, Cost of Capital, Terminal Values, Discounting, and Dilution Adjustments.
Standards: McKinsey/Damodaran institutional frameworks.
"""

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# DT-001/002: Internal i18n imports for UI-facing error messages
from src.i18n import CalculationErrors, StrategySources
from src.exceptions import CalculationError
from src.models import CompanyFinancials, DCFParameters
from src.config.constants import ValuationEngineDefaults, TechnicalDefaults, MacroDefaults

logger = logging.getLogger(__name__)

# ==============================================================================
# REFERENCE TABLES (DAMODARAN SYNTHETIC RATINGS)
# ==============================================================================

SPREADS_LARGE_CAP = ValuationEngineDefaults.SPREADS_LARGE_CAP
SPREADS_SMALL_MID_CAP = ValuationEngineDefaults.SPREADS_SMALL_MID_CAP

@dataclass
class WACCBreakdown:
    r"""
    Detailed decomposition of the Weighted Average Cost of Capital.

    Attributes
    ----------
    cost_of_equity : float
        Calculated Ke (Cost of Equity).
    cost_of_debt_pre_tax : float
        Gross cost of debt (Kd).
    cost_of_debt_after_tax : float
        Net cost of debt after tax shield: $K_d \times (1 - T)$.
    weight_equity : float
        Proportion of Equity in the capital structure ($w_e$).
    weight_debt : float
        Proportion of Debt in the capital structure ($w_d$).
    wacc : float
        Final Weighted Average Cost of Capital.
    method : str
        Source or method description for audit traceability.
    beta_used : float, default 1.0
        The specific Beta coefficient applied to the Ke calculation.
    beta_adjusted : bool, default False
        Indicates if Hamada re-levering was applied to the Beta.
    """
    cost_of_equity: float
    cost_of_debt_pre_tax: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float
    method: str
    beta_used: float = 1.0
    beta_adjusted: bool = False

# ==============================================================================
# 1. TIME VALUE OF MONEY & TERMINAL VALUES
# ==============================================================================

def calculate_discount_factors(rate: float, years: int) -> List[float]:
    r"""
    Generates discount factors for a specific horizon.

    $$DF = \frac{1}{(1 + r)^t}$$

    Parameters
    ----------
    rate : float
        The discount rate (r).
    years : int
        The number of years (n) to project.

    Returns
    -------
    List[float]
        A list of discount factors from year 1 to n.

    Raises
    ------
    CalculationError
        If the discount rate is $\leq -100\%$.
    """
    if rate <= -1.0:
        raise CalculationError(CalculationErrors.INVALID_DISCOUNT_RATE.format(rate=rate))
    return [1.0 / ((1.0 + rate) ** t) for t in range(1, years + 1)]

def calculate_npv(flows: List[float], rate: float) -> float:
    r"""
    Calculates the Net Present Value (NPV) of a series of cash flows.

    $$NPV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^t}$$

    Parameters
    ----------
    flows : List[float]
        Projected cash flows (CF1, CF2, ..., CFn).
    rate : float
        The discount rate (r).

    Returns
    -------
    float
        The sum of discounted cash flows.
    """
    factors = calculate_discount_factors(rate, len(flows))
    return sum(f * d for f, d in zip(flows, factors))

def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float) -> float:
    r"""
    Estimates Terminal Value using the Gordon Growth Model (Perpetuity).

    $$TV = \frac{CF_n \times (1 + g)}{r - g}$$

    Parameters
    ----------
    final_flow : float
        The last projected cash flow ($CF_n$).
    rate : float
        The discount rate (r), usually WACC or Ke.
    g_perp : float
        The perpetual growth rate (g).

    Returns
    -------
    float
        The estimated terminal value at year n.

    Raises
    ------
    CalculationError
        If the rate is $\leq$ growth rate, preventing model convergence.
    """
    if rate <= g_perp:
        raise CalculationError(CalculationErrors.CONVERGENCE_IMPOSSIBLE.format(rate=rate, g=g_perp))
    return (final_flow * (1.0 + g_perp)) / (rate - g_perp)

def calculate_terminal_value_exit_multiple(final_metric: float, multiple: float) -> float:
    r"""
    Estimates Terminal Value based on an exit multiple approach.

    $$TV = Metric_n \times Multiple$$

    Parameters
    ----------
    final_metric : float
        The terminal value of the metric (e.g., EBITDA or Revenue).
    multiple : float
        The valuation multiple to apply.

    Returns
    -------
    float
        The estimated terminal value.

    Raises
    ------
    CalculationError
        If the multiple is negative.
    """
    if multiple < 0:
        raise CalculationError(CalculationErrors.NEGATIVE_EXIT_MULTIPLE)
    return final_metric * multiple

def calculate_terminal_value_pe(final_net_income: float, pe_multiple: float) -> float:
    r"""
    Estimates Equity Terminal Value using a target P/E ratio.

    $$TV = NI_n \times P/E$$

    Parameters
    ----------
    final_net_income : float
        The projected net income for the final year.
    pe_multiple : float
        The Price-to-Earnings multiple applied.

    Returns
    -------
    float
        The estimated terminal value for equity.

    Raises
    ------
    CalculationError
        If the P/E ratio is not strictly positive.
    """
    if pe_multiple <= 0:
        raise CalculationError(CalculationErrors.NEGATIVE_PE_RATIO)
    return final_net_income * pe_multiple

# ==============================================================================
# 2. STRUCTURE ADJUSTMENTS & DILUTION
# ==============================================================================

def calculate_historical_share_growth(shares_series: List[float]) -> float:
    r"""
    Calculates the historical CAGR of shares outstanding to estimate dilution.

    $$CAGR = \left( \frac{Shares_{final}}{Shares_{initial}} \right)^{\frac{1}{n}} - 1$$

    Parameters
    ----------
    shares_series : List[float]
        Historical share counts (ordered from oldest to newest).

    Returns
    -------
    float
        The average annual share growth rate, capped at 10% for prudence.
    """
    if len(shares_series) < 2:
        return 0.0

    start_val = shares_series[0]
    end_val = shares_series[-1]

    if start_val <= 0 or end_val <= 0:
        return 0.0

    n_periods = len(shares_series) - 1
    cagr = (end_val / start_val) ** (1.0 / n_periods) - 1.0

    # Prudence logic: Ignore buybacks (negative growth) for dilution risk assessment.
    return max(0.0, min(TechnicalDefaults.MAX_DILUTION_CLAMPING, cagr))


def calculate_dilution_factor(annual_rate: Optional[float], years: int) -> float:
    r"""
    Calculates the cumulative dilution factor over the projection horizon.

    $$Factor = (1 + d)^t$$

    Parameters
    ----------
    annual_rate : float, optional
        The expected annual dilution rate (e.g., 0.02 for 2%).
    years : int
        The number of projection years.

    Returns
    -------
    float
        The cumulative multiplier (e.g., 1.104 for 2% over 5 years).
    """
    if annual_rate is None or annual_rate <= 0:
        return 1.0
    return (1.0 + annual_rate) ** years


def compute_diluted_shares(current_shares: float, annual_rate: Optional[float], years: int) -> float:
    r"""
    Computes the projected total share count after n years of dilution.

    Parameters
    ----------
    current_shares : float
        The current number of shares outstanding.
    annual_rate : float, optional
        The annual expected dilution rate.
    years : int
        The projection horizon.

    Returns
    -------
    float
        The total projected shares.
    """
    factor = calculate_dilution_factor(annual_rate, years)
    return current_shares * factor


def apply_dilution_adjustment(price : float, dilution_factor: float) -> float:
    r"""
    Adjusts the final intrinsic price per share for expected dilution.

    $$Price_{diluted} = \frac{Price_{initial}}{Factor}$$

    Parameters
    ----------
    price : float
        The initial non-diluted intrinsic value per share.
    dilution_factor : float
        The cumulative factor obtained via calculate_dilution_factor.

    Returns
    -------
    float
        The dilution-adjusted price per share.
    """
    if dilution_factor <= 1.0:
        return price
    return price / dilution_factor

# ==============================================================================
# 3. COST OF CAPITAL (WACC / Ke / SYNTHETIC DEBT)
# ==============================================================================

def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    r"""
    Standard Capital Asset Pricing Model (CAPM).

    $$k_e = R_f + \beta \times MRP$$

    Parameters
    ----------
    rf : float
        Risk-free rate.
    beta : float
        Systemic risk coefficient.
    mrp : float
        Market Risk Premium (Equity Risk Premium).

    Returns
    -------
    float
        The calculated cost of equity.
    """
    return rf + (beta * mrp)

def unlever_beta(beta_levered: float, tax_rate: float, debt_equity_ratio: float) -> float:
    r"""
    Unlevers a beta coefficient using the Hamada formula.

    $$\beta_U = \frac{\beta_L}{1 + (1 - T) \times \frac{D}{E}}$$

    Parameters
    ----------
    beta_levered : float
        The observed market beta.
    tax_rate : float
        Effective corporate tax rate.
    debt_equity_ratio : float
        The current Debt-to-Equity ratio.

    Returns
    -------
    float
        The unlevered (asset) beta.
    """
    if debt_equity_ratio <= 0:
        return beta_levered
    return beta_levered / (1.0 + (1.0 - tax_rate) * debt_equity_ratio)

def relever_beta(beta_unlevered: float, tax_rate: float, target_debt_equity_ratio: float) -> float:
    r"""
    Relevers a beta coefficient to a target capital structure.

    $$\beta_L = \beta_U \times [1 + (1 - T) \times \frac{D}{E}]$$

    Parameters
    ----------
    beta_unlevered : float
        The unlevered asset beta.
    tax_rate : float
        Target effective corporate tax rate.
    target_debt_equity_ratio : float
        The target Debt-to-Equity ratio.

    Returns
    -------
    float
        The levered beta reflecting the target structure.
    """
    if target_debt_equity_ratio <= 0:
        return beta_unlevered
    return beta_unlevered * (1.0 + (1.0 - tax_rate) * target_debt_equity_ratio)

def calculate_cost_of_equity(financials: CompanyFinancials, params: DCFParameters) -> float:
    r"""
    Calculates Ke for Direct Equity approaches, prioritizing manual overrides.

    Parameters
    ----------
    financials : CompanyFinancials
        Company historical data.
    params : DCFParameters
        User-defined or automated parameters.

    Returns
    -------
    float
        The resolved cost of equity.
    """
    r = params.rates
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
    beta = r.manual_beta if r.manual_beta is not None else (financials.beta or 1.0)

    if r.manual_cost_of_equity is not None:
        return r.manual_cost_of_equity

    return calculate_cost_of_equity_capm(rf, beta, mrp)

def calculate_synthetic_cost_of_debt(rf: float, ebit: Optional[float],
                                     interest_expense: Optional[float], market_cap: float) -> float:
    r"""
    Estimates pre-tax cost of debt using the Interest Coverage Ratio (ICR).

    Parameters
    ----------
    rf : float
        Risk-free rate.
    ebit : float, optional
        Operating profit (TTM).
    interest_expense : float, optional
        Annual interest charges.
    market_cap : float
        Current market capitalization for cap-size weighting.

    Returns
    -------
    float
        Estimated pre-tax Kd (Risk-Free + Spread).
    """
    safe_ebit, safe_int = ebit or 0.0, interest_expense or 0.0

    if safe_int <= 0 or safe_ebit <= 0:
        return rf + 0.0107  # Proxy A-rated spread

    icr = safe_ebit / safe_int
    table = SPREADS_LARGE_CAP if market_cap >= MacroDefaults.LARGE_CAP_THRESHOLD else SPREADS_SMALL_MID_CAP

    for threshold, spread in table:
        if icr >= threshold:
            return rf + spread
    return rf + 0.1900

def calculate_wacc(financials: CompanyFinancials, params: DCFParameters) -> WACCBreakdown:
    r"""
    Computes the Weighted Average Cost of Capital (WACC).

    $$WACC = w_e \times k_e + w_d \times k_d \times (1 - T)$$

    Parameters
    ----------
    financials : CompanyFinancials
        Financial snapshots.
    params : DCFParameters
        Projection parameters.

    Returns
    -------
    WACCBreakdown
        Full technical decomposition for audit and rendering.
    """
    r, g = params.rates, params.growth
    ke = calculate_cost_of_equity(financials, params)

    tax = r.tax_rate if r.tax_rate is not None else 0.25
    rf = r.risk_free_rate if r.risk_free_rate is not None else 0.04
    kd_gross = r.cost_of_debt if r.cost_of_debt is not None else calculate_synthetic_cost_of_debt(
        rf, financials.ebit_ttm, financials.interest_expense, financials.market_cap
    )
    kd_net = kd_gross * (1.0 - tax)

    debt = g.manual_total_debt if g.manual_total_debt is not None else financials.total_debt
    shares = g.manual_shares_outstanding if g.manual_shares_outstanding is not None else financials.shares_outstanding
    market_equity = financials.current_price * shares

    total_cap = market_equity + debt
    we, wd = (market_equity / total_cap, debt / total_cap) if total_cap > 0 else (1.0, 0.0)

    # Initial Beta
    beta_original = r.manual_beta if r.manual_beta is not None else (financials.beta or 1.0)
    beta_used = beta_original
    beta_adjusted = False

    # Hamada re-levering logic for target capital structures
    if g.target_equity_weight is not None and g.target_debt_weight is not None and g.target_equity_weight > 0:
        target_debt_equity_ratio = g.target_debt_weight / g.target_equity_weight

        # Unlever observed beta
        beta_unlevered = unlever_beta(beta_original, tax, debt / market_equity if market_equity > 0 else 0.0)

        # Relever to target structure
        beta_used = relever_beta(beta_unlevered, tax, target_debt_equity_ratio)
        beta_adjusted = True

        # Recalculate Ke with adjusted beta
        mrp = r.market_risk_premium if r.market_risk_premium is not None else 0.05
        ke = calculate_cost_of_equity_capm(rf, beta_used, mrp)

    wacc_raw = (we * ke) + (wd * kd_net)
    return WACCBreakdown(
        ke, kd_gross, kd_net, we, wd, r.wacc_override or wacc_raw, StrategySources.WACC_MARKET,
        beta_used, beta_adjusted
    )

# ==============================================================================
# 4. SHAREHOLDER MODELS (FCFE & DDM)
# ==============================================================================

def calculate_fcfe_reconstruction(ni: float, adjustments: float, net_borrowing: float) -> float:
    r"""
    Reconstructs Free Cash Flow to Equity (FCFE) via the NI walk.

    $$FCFE = Net Income + NonCashAdj - Capex - \Delta WCR + \Delta Net Borrowing$$
    """
    return ni + adjustments + net_borrowing

def calculate_fcfe_base(fcff: float, interest: float, tax_rate: float, net_borrowing: float) -> float:
    r"""
    Derives FCFE from the calculated FCFF.

    $$FCFE = FCFF - Interest \times (1 - T) + Net Borrowing$$

    Parameters
    ----------
    fcff : float
        Free Cash Flow to the Firm.
    interest : float
        Interest expense.
    tax_rate : float
        Effective tax rate.
    net_borrowing : float
        Net change in debt principal.

    Returns
    -------
    float
        Free Cash Flow to Equity.
    """
    return fcff - (interest * (1.0 - tax_rate)) + net_borrowing

def calculate_sustainable_growth(roe: float, payout_ratio: float) -> float:
    r"""
    Calculates the Sustainable Growth Rate (SGR) based on Gordon's retention.

    $$g = ROE \times (1 - Payout Ratio)$$

    Parameters
    ----------
    roe : float
        Return on Equity.
    payout_ratio : float
        Dividend payout ratio.

    Returns
    -------
    float
        The sustainable growth rate.
    """
    return roe * (1.0 - (payout_ratio or 0.0))

# ==============================================================================
# 5. SPECIFIC MODELS (RIM & GRAHAM)
# ==============================================================================

def calculate_graham_1974_value(eps: float, growth_rate: float, aaa_yield: float) -> float:
    r"""
    Applies the Revised Graham Formula (1974).

    $$V = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}$$

    Parameters
    ----------
    eps : float
        Earnings Per Share (normalized).
    growth_rate : float
        Expected annual growth rate (decimal).
    aaa_yield : float
        Current yield on AAA-rated corporate bonds (decimal).

    Returns
    -------
    float
        Graham's intrinsic value.
    """
    y = aaa_yield if (aaa_yield and aaa_yield > 0) else TechnicalDefaults.DEFAULT_AAA_YIELD
    return (eps * (8.5 + 2.0 * (growth_rate * 100)) * 4.4) / (y * 100)

def calculate_rim_vectors(current_bv: float, ke: float,
                          earnings: List[float], payout: float) -> Tuple[List[float], List[float]]:
    r"""
    Generates Residual Income (RI) and Book Value (BV) time series.

    $$RI_t = Net Income_t - (BV_{t-1} \times k_e)$$

    Parameters
    ----------
    current_bv : float
        Opening Book Value (Equity).
    ke : float
        Cost of equity.
    earnings : List[float]
        Projected net income series.
    payout : float
        Dividend payout ratio.

    Returns
    -------
    Tuple[List[float], List[float]]
        Vectored residual incomes and book values.
    """
    book_values, residual_incomes = [], []
    prev_bv = current_bv
    for ni in earnings:
        ri = ni - (prev_bv * ke)
        new_bv = prev_bv + ni - (ni * payout)
        residual_incomes.append(ri)
        book_values.append(new_bv)
        prev_bv = new_bv
    return residual_incomes, book_values

def compute_proportions(*values: Optional[float], fallback_index: int = 0) -> List[float]:
    r"""
    Normalizes a list of values into weights that sum to 100%.

    Parameters
    ----------
    *values : Optional[float]
        Arbitrary sequence of financial amounts.
    fallback_index : int, default 0
        Index to assign 100% weight if all values are zero.

    Returns
    -------
    List[float]
        Weight proportions.
    """
    clean_values = [v or 0.0 for v in values]
    total = sum(clean_values)
    if total <= 0:
        res = [0.0] * len(clean_values); res[fallback_index] = 1.0; return res
    return [v / total for v in clean_values]

# ==============================================================================
# 6. MULTIPLES & TRIANGULATION (RELATIVE VALUATION)
# ==============================================================================

def calculate_price_from_pe_multiple(net_income: float, median_pe: float, shares: float) -> float:
    r"""
    Derives Equity Price from a P/E multiple.

    $$P = \frac{NI \times P/E}{Shares}$$

    Parameters
    ----------
    net_income : float
        Total Net Income.
    median_pe : float
        Peer group median P/E ratio.
    shares : float
        Total shares outstanding.

    Returns
    -------
    float
        Implied price per share.
    """
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
    r"""
    Derives Price per Share from an Enterprise Value multiple (Equity Bridge).

    $$Price = \frac{EV - NetDebt - Minorities - Pensions}{Shares}$$

    Parameters
    ----------
    metric_value : float
        The base metric (EBITDA or Revenue).
    median_ev_multiple : float
        The median EV/Metric from the peers.
    net_debt : float
        Total gross debt minus cash.
    shares : float
        Total shares outstanding.
    minorities : float, default 0.0
        Non-controlling interests.
    pensions : float, default 0.0
        Pension liability provisions.

    Returns
    -------
    float
        Implied price per share.
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
    r"""
    Performs weighted synthesis of multiple valuation price signals.

    Filters out invalid (non-positive) results to maintain model integrity.

    Parameters
    ----------
    valuation_signals : Dict[str, float]
        Dictionary of method names and their calculated share prices.
    weights : Dict[str, float], optional
        Relative weighting for each method. Defaults to simple average.

    Returns
    -------
    float
        The triangulated consensus price.
    """
    # 1. Honest Data extraction: Filter valid positive signals
    valid_signals = {k: v for k, v in valuation_signals.items() if v > 0}
    if not valid_signals:
        return 0.0

    # 2. Simple average if no specific weights provided
    if not weights:
        return sum(valid_signals.values()) / len(valid_signals)

    # 3. Weighted average calculation
    active_weights = {k: weights[k] for k in valid_signals if k in weights}
    total_weight = sum(active_weights.values())

    if total_weight <= 0:
        return sum(valid_signals.values()) / len(valid_signals)

    weighted_sum = sum(valid_signals[k] * active_weights[k] for k in active_weights)
    return weighted_sum / total_weight