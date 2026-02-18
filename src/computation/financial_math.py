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
from dataclasses import dataclass

from src.config.constants import MacroDefaults, ModelDefaults, ValuationEngineDefaults
from src.core.diagnostics import DiagnosticRegistry
from src.core.exceptions import CalculationError

# DT-001/002: Internal i18n imports for UI-facing error messages
from src.i18n import CalculationErrors, StrategySources
from src.models import Company, Parameters

logger = logging.getLogger(__name__)

# ==============================================================================
# REFERENCE TABLES (DAMODARAN SYNTHETIC RATINGS)
# ==============================================================================

# Imported from config/constants.py to respect SSOT
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
    diagnostics : list, default empty
        Diagnostic events related to WACC calculation (e.g., beta adjustment skipped).
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
    diagnostics: list = None  # Will be list[DiagnosticEvent] but avoiding circular import
    
    def __post_init__(self):
        """Initialize diagnostics list if None."""
        if self.diagnostics is None:
            self.diagnostics = []


# ==============================================================================
# 1. TIME VALUE OF MONEY & TERMINAL VALUES
# ==============================================================================


def calculate_discount_factors(rate: float, years: int) -> list[float]:
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


def calculate_npv(flows: list[float], rate: float) -> float:
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


def calculate_terminal_value_gordon(final_flow: float, rate: float, g_perp: float, tax_adjustment_factor: float = 1.0) -> float:
    r"""
    Estimates Terminal Value using the Gordon Growth Model (Perpetuity).

    $$TV = \frac{CF_n \times (1 + g) \times \text{tax\_adj}}{r - g}$$

    Parameters
    ----------
    final_flow : float
        The last projected cash flow ($CF_n$).
    rate : float
        The discount rate (r), usually WACC or Ke.
    g_perp : float
        The perpetual growth rate (g).
    tax_adjustment_factor : float, default 1.0
        Adjustment factor to account for tax rate changes between explicit period and perpetuity.
        When marginal tax rate differs from effective tax rate, this adjusts the operating 
        profit component of FCF. Factor > 1 when marginal rate < effective rate (tax increase).

    Returns
    -------
    float
        The estimated terminal value at year n.

    Raises
    ------
    CalculationError
        If the rate is $\leq$ growth rate, preventing model convergence.
        
    Notes
    -----
    The tax adjustment factor corrects for the fact that FCF_n was calculated using the
    effective tax rate during the explicit period, but the terminal value should reflect
    the marginal tax rate. This ensures rigorous consistency between the discount rate
    and the cash flow assumptions in perpetuity.
    """
    if rate <= g_perp:
        raise CalculationError(CalculationErrors.CONVERGENCE_IMPOSSIBLE.format(rate=rate, g=g_perp))
    return (final_flow * (1.0 + g_perp) * tax_adjustment_factor) / (rate - g_perp)


def calculate_fcf_tax_adjustment_factor(
    effective_tax_rate: float, 
    marginal_tax_rate: float, 
    financials: Company | None = None,
    return_diagnostics: bool = False
) -> float | tuple[float, list]:
    r"""
    Calculates the adjustment factor to convert FCF from effective to marginal tax rate.
    
    $$\text{factor} \approx 1 + OM \times (\tau_{eff} - \tau_{marg})$$
    
    Parameters
    ----------
    effective_tax_rate : float
        The effective tax rate used during the explicit projection period (decimal).
    marginal_tax_rate : float
        The marginal legal tax rate for perpetuity (decimal).
    financials : Company, optional
        Company financials to extract real operating margin.
        If provided, uses EBIT_TTM / Revenue_TTM for precise calculation.
        If None or data unavailable, falls back to conservative 15% estimate.
    return_diagnostics : bool, default False
        If True, returns tuple (factor, diagnostics_list).
        If False, returns just the factor for backward compatibility.
    
    Returns
    -------
    float or tuple[float, list]
        If return_diagnostics is False: Tax adjustment factor.
        If return_diagnostics is True: (factor, list of DiagnosticEvent objects).
        
        Factor interpretation:
        - Factor = 1.0 when rates are equal (no adjustment needed)
        - Factor < 1.0 when marginal > effective (tax goes up, FCF goes down)
        - Factor > 1.0 when marginal < effective (tax goes down, FCF goes up)
    
    Notes
    -----
    FCF = NOPAT + DA - CapEx - ΔNWC where NOPAT = EBIT × (1 - τ).
    
    When tax rate changes, only NOPAT is affected, not non-cash items.
    The operating margin represents what portion of FCF is tax-sensitive.
    
    Operating Margin Calculation Priority:
    1. Real margin from financials: EBIT_TTM / Revenue_TTM
    2. Fallback: 15% (conservative estimate for mature companies)
    
    A diagnostic warning is generated when fallback is used, indicating that
    real company data was unavailable from the data provider.
    
    Example:
    - Effective rate: 15% (with temporary credits)
    - Marginal rate: 25% (legal rate)
    - Operating margin: 18% (calculated from financials)
    - Factor ≈ 1 + 0.18 × (0.15 - 0.25) = 1 - 0.018 = 0.982 (1.8% reduction)
    
    The real margin provides more accurate adjustments than the previous
    fixed 20% assumption. Users should still consider inputting normalized
    FCF that already reflects the marginal tax rate for maximum precision.
    """
    if effective_tax_rate == marginal_tax_rate:
        if return_diagnostics:
            return 1.0, []
        return 1.0
    
    # Calculate real operating margin from financials if available
    operating_margin = 0.15  # Default fallback: conservative 15%
    diagnostics_list = []
    used_fallback = False
    ebit_available = False
    revenue_available = False
    
    if financials is not None:
        ebit_ttm = getattr(financials, "ebit_ttm", None)
        revenue_ttm = getattr(financials, "revenue_ttm", None)
        
        ebit_available = ebit_ttm is not None and ebit_ttm != 0
        revenue_available = revenue_ttm is not None and revenue_ttm != 0
        
        if ebit_available and revenue_available and revenue_ttm > 0:
            # Use real operating margin
            operating_margin = ebit_ttm / revenue_ttm
            # Clamp to reasonable bounds (0-50%)
            operating_margin = max(0.0, min(0.50, operating_margin))
        else:
            # Missing data - use fallback and create diagnostic
            used_fallback = True
    else:
        # No financials provided - use fallback
        used_fallback = True
    
    # Create diagnostic if fallback was used
    if used_fallback:
        diagnostics_list.append(
            DiagnosticRegistry.operating_margin_fallback_used(
                fallback_margin=operating_margin,
                ebit_available=ebit_available,
                revenue_available=revenue_available,
            )
        )
    
    # Calculate adjustment factor
    tax_delta = effective_tax_rate - marginal_tax_rate
    adjustment = 1.0 + (operating_margin * tax_delta)
    
    # Clamp to reasonable bounds (±50% adjustment maximum)
    final_factor = max(0.5, min(1.5, adjustment))
    
    if return_diagnostics:
        return final_factor, diagnostics_list
    return final_factor


# ==============================================================================


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


def calculate_historical_share_growth(shares_series: list[float]) -> float:
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
    return max(0.0, min(ValuationEngineDefaults.MAX_DILUTION_CLAMPING, cagr))


def calculate_dilution_factor(annual_rate: float | None, years: int) -> float:
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


def compute_diluted_shares(current_shares: float, annual_rate: float | None, years: int) -> float:
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


def apply_dilution_adjustment(price: float, dilution_factor: float) -> float:
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


def convert_de_to_dcap(debt_equity_ratio: float) -> tuple[float, float]:
    r"""
    Converts Debt-to-Equity ratio (D/E) to capital structure weights.
    
    $$w_e = \frac{1}{1 + D/E}, \quad w_d = \frac{D/E}{1 + D/E}$$
    
    Parameters
    ----------
    debt_equity_ratio : float
        Debt-to-Equity ratio (D/E). Must be non-negative.
        
    Returns
    -------
    tuple[float, float]
        (weight_equity, weight_debt) where weights sum to 1.0
        
    Examples
    --------
    >>> convert_de_to_dcap(0.5)  # 50% debt / 100% equity
    (0.6667, 0.3333)  # 66.7% equity, 33.3% debt in capital
    
    >>> convert_de_to_dcap(1.0)  # 100% debt / 100% equity
    (0.5, 0.5)  # 50% equity, 50% debt in capital
    
    >>> convert_de_to_dcap(0.25)  # 25% debt / 100% equity
    (0.8, 0.2)  # 80% equity, 20% debt in capital
    """
    if debt_equity_ratio < 0:
        raise ValueError(f"D/E ratio must be non-negative, got {debt_equity_ratio}")
    
    we = 1.0 / (1.0 + debt_equity_ratio)
    wd = debt_equity_ratio / (1.0 + debt_equity_ratio)
    return we, wd


def convert_dcap_to_de(weight_debt: float) -> float:
    r"""
    Converts capital structure weight (D/Cap) to Debt-to-Equity ratio (D/E).
    
    $$D/E = \frac{w_d}{1 - w_d}$$
    
    Parameters
    ----------
    weight_debt : float
        Proportion of debt in capital structure. Must be in [0, 1).
        
    Returns
    -------
    float
        Debt-to-Equity ratio (D/E)
        
    Examples
    --------
    >>> convert_dcap_to_de(0.3333)  # 33.3% debt in capital
    0.5  # D/E = 0.5 (50% debt / 100% equity)
    
    >>> convert_dcap_to_de(0.5)  # 50% debt in capital
    1.0  # D/E = 1.0 (100% debt / 100% equity)
    
    >>> convert_dcap_to_de(0.2)  # 20% debt in capital
    0.25  # D/E = 0.25 (25% debt / 100% equity)
    """
    if weight_debt < 0 or weight_debt >= 1.0:
        raise ValueError(f"Debt weight must be in [0, 1), got {weight_debt}")
    
    return weight_debt / (1.0 - weight_debt)


def calculate_cost_of_equity_capm(rf: float, beta: float, mrp: float) -> float:
    r"""
    Calculates Cost of Equity using the Capital Asset Pricing Model (CAPM).

    $$K_e = R_f + \beta \times MRP$$

    Parameters
    ----------
    rf : float
        Risk-free rate.
    beta : float
        Equity beta coefficient.
    mrp : float
        Market risk premium.

    Returns
    -------
    float
        The cost of equity.
    """
    return rf + beta * mrp


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


def calculate_cost_of_equity(params: Parameters) -> float:
    r"""
    Calculates Ke for Direct Equity approaches, prioritizing manual overrides.

    Parameters
    ----------
    params : Parameters
        User-defined or automated parameters.

    Returns
    -------
    float
        The resolved cost of equity.
    """
    r = params.common.rates
    rf = r.risk_free_rate if r.risk_free_rate is not None else MacroDefaults.DEFAULT_RISK_FREE_RATE
    mrp = r.market_risk_premium if r.market_risk_premium is not None else MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM
    beta = r.beta if r.beta is not None else ModelDefaults.DEFAULT_BETA

    return calculate_cost_of_equity_capm(rf, beta, mrp)


def calculate_synthetic_cost_of_debt(
    rf: float, ebit: float | None, interest_expense: float | None, market_cap: float
) -> float:
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

    # Determine which table to use based on Market Cap Threshold
    if market_cap >= MacroDefaults.LARGE_CAP_THRESHOLD:
        table = SPREADS_LARGE_CAP
    else:
        table = SPREADS_SMALL_MID_CAP

    for threshold, spread in table:
        if icr >= threshold:
            return rf + spread

    # Default (Junk/Distressed) if no threshold matched
    return rf + 0.1900


def calculate_wacc(financials: Company, params: Parameters) -> WACCBreakdown:
    r"""
    Computes the Weighted Average Cost of Capital (WACC).

    $$WACC = w_e \times k_e + w_d \times k_d \times (1 - T)$$

    Parameters
    ----------
    financials : Company
        Financial snapshots.
    params : Parameters
        Projection parameters.

    Returns
    -------
    WACCBreakdown
        Full technical decomposition for audit and rendering.

    Notes
    -----
    If params.common.rates.wacc is provided (manual override), it bypasses
    the CAPM calculation and uses the override value directly. This is used
    in sensitivity analysis to test valuation response to discount rate changes.
    """
    return _calculate_wacc_internal(financials, params, use_marginal_tax=False)


def calculate_wacc_for_terminal_value(financials: Company, params: Parameters) -> WACCBreakdown:
    r"""
    Computes the WACC for Terminal Value calculation using marginal tax rate.

    Parameters
    ----------
    financials : Company
        Financial snapshots.
    params : Parameters
        Projection parameters.

    Returns
    -------
    WACCBreakdown
        Full technical decomposition using marginal tax rate for TV calculations.

    Notes
    -----
    Temporary tax benefits are not perpetual. This function ensures the terminal
    value uses the long-term marginal legal tax rate instead of the effective rate
    from the growth period.
    """
    return _calculate_wacc_internal(financials, params, use_marginal_tax=True)


def _calculate_wacc_internal(financials: Company, params: Parameters, use_marginal_tax: bool = False) -> WACCBreakdown:
    r"""
    Internal implementation for WACC calculation with Hamada beta adjustment and marginal tax support.

    Parameters
    ----------
    financials : Company
        Financial snapshots.
    params : Parameters
        Projection parameters.
    use_marginal_tax : bool, default False
        If True, uses marginal_tax_rate for terminal value calculation.
        If False, uses standard tax_rate for explicit period.

    Returns
    -------
    WACCBreakdown
        Full technical decomposition for audit and rendering.
        
    Notes
    -----
    This function integrates two advanced features:
    
    1. **Hamada Beta Adjustment**: When `target_debt_equity_ratio` is specified,
       the function unlevers the observed beta to asset beta, then relevers it
       to the target capital structure using the Hamada formula.
       
    2. **Marginal Tax Convergence**: When `use_marginal_tax=True`, applies the
       long-term marginal tax rate instead of effective tax rate, ensuring
       terminal value assumptions reflect normalized perpetuity conditions.
       
    The combination ensures that terminal value calculations use both the target
    capital structure (financial risk) and marginal tax rate (fiscal convergence).
    """
    r = params.common.rates
    c = params.common.capital

    # 0. Check for WACC override (used in sensitivity analysis)
    if r.wacc is not None:
        # When WACC is manually overridden, we still need to decompose it
        # but we use the override value as the final WACC.
        # Note: Ke and Kd calculations are required for UI display and audit trails.

        # Calculate Ke for display/audit purposes
        ke = r.cost_of_equity if r.cost_of_equity is not None else calculate_cost_of_equity(params)

        # Calculate Kd for display purposes
        if use_marginal_tax and r.marginal_tax_rate is not None:
            tax = r.marginal_tax_rate
        else:
            tax = r.tax_rate if r.tax_rate is not None else MacroDefaults.DEFAULT_TAX_RATE
        
        rf = r.risk_free_rate if r.risk_free_rate is not None else MacroDefaults.DEFAULT_RISK_FREE_RATE

        if r.cost_of_debt is not None:
            kd_gross = r.cost_of_debt
        else:
            mcap = financials.current_price * (c.shares_outstanding or 1.0)
            ebit = getattr(financials, "ebit_ttm", None) or 0.0
            interest = getattr(financials, "interest_expense", None) or 0.0
            kd_gross = calculate_synthetic_cost_of_debt(rf, ebit, interest, mcap)

        kd_net = kd_gross * (1.0 - tax)

        # Calculate weights for display
        debt = c.total_debt if c.total_debt is not None else 0.0
        shares = c.shares_outstanding if c.shares_outstanding is not None else 1.0
        market_equity = financials.current_price * shares

        total_cap = market_equity + debt
        we, wd = (market_equity / total_cap, debt / total_cap) if total_cap > 0 else (1.0, 0.0)

        return WACCBreakdown(
            cost_of_equity=ke,
            cost_of_debt_pre_tax=kd_gross,
            cost_of_debt_after_tax=kd_net,
            weight_equity=we,
            weight_debt=wd,
            wacc=r.wacc,  # Use the override value
            method=StrategySources.MANUAL_OVERRIDE,
            beta_used=r.beta if r.beta else ModelDefaults.DEFAULT_BETA,
            beta_adjusted=False,
        )

    # 1. Determine tax rate (marginal for TV, effective for explicit period)
    if use_marginal_tax and r.marginal_tax_rate is not None:
        tax = r.marginal_tax_rate
    else:
        tax = r.tax_rate if r.tax_rate is not None else MacroDefaults.DEFAULT_TAX_RATE
    
    # 2. Hamada Beta Adjustment (if target structure specified)
    beta_input = r.beta if r.beta is not None else ModelDefaults.DEFAULT_BETA
    beta_adjusted_flag = False
    beta_used = beta_input
    diagnostics_list = []
    
    target_de_ratio = c.target_debt_equity_ratio if c.target_debt_equity_ratio is not None else None
    
    if target_de_ratio is not None and target_de_ratio > 0:
        # Apply Hamada adjustment: unlever observed beta, then relever to target
        debt = c.total_debt if c.total_debt is not None else 0.0
        shares = c.shares_outstanding if c.shares_outstanding is not None else 1.0
        market_equity = financials.current_price * shares
        
        # Current D/E ratio
        current_de_ratio = (debt / market_equity) if market_equity > 0 else 0.0
        
        # Only adjust if target differs meaningfully from current
        # Threshold prevents noise from minor differences (e.g., 0.249 vs 0.251)
        threshold = ModelDefaults.BETA_ADJUSTMENT_THRESHOLD  # 5% difference
        if abs(target_de_ratio - current_de_ratio) > threshold:
            # Unlever to asset beta using current structure and tax rate
            beta_unlevered = unlever_beta(beta_input, tax, current_de_ratio)
            # Relever to target structure using tax rate (marginal for TV, effective for explicit)
            beta_used = relever_beta(beta_unlevered, tax, target_de_ratio)
            beta_adjusted_flag = True
        else:
            # Threshold not met - create diagnostic to inform user
            diagnostics_list.append(
                DiagnosticRegistry.beta_adjustment_skipped_threshold(
                    current_de=current_de_ratio,
                    target_de=target_de_ratio,
                    threshold=threshold
                )
            )

    # 3. Calculate Ke with (possibly adjusted) beta
    rf = r.risk_free_rate if r.risk_free_rate is not None else MacroDefaults.DEFAULT_RISK_FREE_RATE
    mrp = r.market_risk_premium if r.market_risk_premium is not None else MacroDefaults.DEFAULT_MARKET_RISK_PREMIUM
    ke = calculate_cost_of_equity_capm(rf, beta_used, mrp)

    # 4. Calculate Kd with appropriate tax rate
    if r.cost_of_debt is not None:
        kd_gross = r.cost_of_debt
    else:
        # Need market cap for table selection
        mcap = financials.current_price * (c.shares_outstanding or 1.0)

        # Extract EBIT and Interest from the Company identity if available
        # Fallback to 0.0 triggers the A-rated proxy spread (safe default)
        ebit = getattr(financials, "ebit_ttm", None) or 0.0
        interest = getattr(financials, "interest_expense", None) or 0.0

        kd_gross = calculate_synthetic_cost_of_debt(rf, ebit, interest, mcap)

    kd_net = kd_gross * (1.0 - tax)

    # 5. Capital Structure Weights (use target if specified, else market)
    debt = c.total_debt if c.total_debt is not None else 0.0
    shares = c.shares_outstanding if c.shares_outstanding is not None else 1.0
    market_equity = financials.current_price * shares

    if target_de_ratio is not None and target_de_ratio > 0:
        # Use target structure for weights
        # Convert D/E ratio to capital structure weights
        # Example: D/E = 0.5 → we = 1/(1+0.5) = 0.667, wd = 0.5/(1+0.5) = 0.333
        we, wd = convert_de_to_dcap(target_de_ratio)
        method = StrategySources.WACC_TARGET
    else:
        # Use market structure (actual observed D and E)
        total_cap = market_equity + debt
        we, wd = (market_equity / total_cap, debt / total_cap) if total_cap > 0 else (1.0, 0.0)
        method = StrategySources.WACC_MARKET

    wacc_raw = (we * ke) + (wd * kd_net)

    return WACCBreakdown(
        cost_of_equity=ke,
        cost_of_debt_pre_tax=kd_gross,
        cost_of_debt_after_tax=kd_net,
        weight_equity=we,
        weight_debt=wd,
        wacc=wacc_raw,
        method=method,
        beta_used=beta_used,
        beta_adjusted=beta_adjusted_flag,
        diagnostics=diagnostics_list,
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

    $$V = \frac{EPS \times (8.5 + 2*g) \times 4.4}{Y}$$

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
    y = aaa_yield if (aaa_yield and aaa_yield > 0) else MacroDefaults.DEFAULT_CORPORATE_AAA_YIELD
    # Growth rate expected as decimal (0.05) but formula often uses integer (5) or decimal scaling
    # Standard interpretation: 8.5 + 2 * (growth_rate * 100)
    return (eps * (8.5 + 2.0 * (growth_rate * 100)) * 4.4) / (y * 100)


def calculate_rim_vectors(
    current_bv: float, ke: float, earnings: list[float], payout: float
) -> tuple[list[float], list[float]]:
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


def compute_proportions(*values: float | None, fallback_index: int = 0) -> list[float]:
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
        res = [0.0] * len(clean_values)
        res[fallback_index] = 1.0
        return res
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
    pensions: float = 0.0,
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


def calculate_triangulated_price(valuation_signals: dict[str, float], weights: dict[str, float] | None = None) -> float:
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
