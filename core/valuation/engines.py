import logging
from typing import Dict, Type, List, Optional, Tuple

from core.computation.statistics import generate_multivariate_samples, generate_independent_samples
from core.exceptions import CalculationError, WorkflowError
from core.models import CompanyFinancials, DCFParameters, DCFResult, InputSource, ValuationMode, ValuationRequest
from core.valuation.strategies.abstract import ValuationStrategy
from core.valuation.strategies.dcf_fundamental import FundamentalFCFFStrategy
from core.valuation.strategies.dcf_simple import SimpleFCFFStrategy

logger = logging.getLogger(__name__)

STRATEGY_MAP: Dict[ValuationMode, Type[ValuationStrategy]] = {
    ValuationMode.SIMPLE_FCFF: SimpleFCFFStrategy,
    ValuationMode.FUNDAMENTAL_FCFF: FundamentalFCFFStrategy,
}


def run_deterministic_dcf(financials: CompanyFinancials, params: DCFParameters, mode: ValuationMode) -> DCFResult:
    """
    Deterministic dispatcher for officially supported deterministic strategies.
    """
    strategy_cls = STRATEGY_MAP.get(mode)
    if not strategy_cls:
        raise CalculationError(f"Unsupported deterministic mode: {mode.value}")

    logger.info(
        "[Engine] Deterministic run | ticker=%s | mode=%s",
        financials.ticker,
        mode.value,
    )
    return strategy_cls().execute(financials, params)


def run_reverse_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    market_price: float,
    tolerance: float = 0.01,
    max_iterations: int = 50,
) -> Optional[float]:
    """
    Reverse DCF (binary search on fcf_growth_rate) using FundamentalFCFFStrategy.
    Returns implied growth rate, or None if input invalid.
    """
    if market_price <= 0:
        return None

    low = -0.10
    high = 0.30

    fundamental_strategy = FundamentalFCFFStrategy()

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        if abs(high - low) < 1e-5:
            return mid

        test_params = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=mid,
            perpetual_growth_rate=params.perpetual_growth_rate,
            projection_years=params.projection_years,
            high_growth_years=params.high_growth_years,
            beta_volatility=params.beta_volatility,
            growth_volatility=params.growth_volatility,
            terminal_growth_volatility=params.terminal_growth_volatility,
            target_equity_weight=params.target_equity_weight,
            target_debt_weight=params.target_debt_weight,
            manual_cost_of_equity=params.manual_cost_of_equity,
            wacc_override=params.wacc_override,
        )
        test_params.normalize_weights()

        try:
            result = fundamental_strategy.execute(financials, test_params)
            iv = result.intrinsic_value_per_share
        except CalculationError:
            iv = float("inf")
        except Exception:
            iv = -999.0

        diff = iv - market_price
        if abs(diff) < tolerance:
            return mid

        if diff > 0:
            high = mid
        else:
            low = mid

    return (low + high) / 2.0


def run_monte_carlo_dcf(
    financials: CompanyFinancials,
    params: DCFParameters,
    num_simulations: int = 2000,
) -> DCFResult:
    """
    Monte Carlo wrapper:
    - draws beta and growth scenarios,
    - runs an inner deterministic engine for each scenario,
    - returns a deterministic DCFResult with simulation distribution attached.

    Note:
    - The inner engine currently uses SimpleFCFFStrategy by design (performance + stable inputs).
    - This is why SimpleFCFFStrategy logs must remain neutral.
    """
    if num_simulations <= 0:
        raise CalculationError("num_simulations must be > 0")

    logger.info(
        "[Engine] Monte Carlo run | ticker=%s | sims=%s | inner_engine=%s",
        financials.ticker,
        num_simulations,
        "SimpleFCFFStrategy",
    )

    beta_mu = float(financials.beta)
    sigma_beta = float(params.beta_volatility) * abs(beta_mu)

    # Ensure well-defined sampling even if volatility is zero.
    # (generate_multivariate_samples might still work, but we keep behavior stable and explicit.)
    betas, growths = generate_multivariate_samples(
        mu_beta=beta_mu,
        sigma_beta=sigma_beta,
        mu_growth=float(params.fcf_growth_rate),
        sigma_growth=float(params.growth_volatility),
        rho=-0.4,
        num_simulations=num_simulations,
    )

    g_inf_draws = generate_independent_samples(
        mean=float(params.perpetual_growth_rate),
        sigma=float(params.terminal_growth_volatility),
        num_simulations=num_simulations,
        clip_min=0.0,
        clip_max=0.04,
    )

    simulated_ivs: List[float] = []
    base_strategy = SimpleFCFFStrategy()
    original_beta = float(financials.beta)

    valid_runs = 0

    for i in range(num_simulations):
        financials.beta = float(betas[i])

        sim_params = DCFParameters(
            risk_free_rate=params.risk_free_rate,
            market_risk_premium=params.market_risk_premium,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
            fcf_growth_rate=float(growths[i]),
            perpetual_growth_rate=float(g_inf_draws[i]),
            projection_years=params.projection_years,
            high_growth_years=params.high_growth_years,
            beta_volatility=params.beta_volatility,
            growth_volatility=params.growth_volatility,
            terminal_growth_volatility=params.terminal_growth_volatility,
            target_equity_weight=params.target_equity_weight,
            target_debt_weight=params.target_debt_weight,
            manual_cost_of_equity=params.manual_cost_of_equity,
            wacc_override=params.wacc_override,
        )
        sim_params.normalize_weights()

        try:
            result_i = base_strategy.execute(financials, sim_params)
            simulated_ivs.append(float(result_i.intrinsic_value_per_share))
            valid_runs += 1
        except CalculationError:
            # skip invalid draw (ex: WACC <= g∞ or other constraints enforced downstream)
            pass
        finally:
            financials.beta = original_beta

    final_result = base_strategy.execute(financials, params)
    if valid_runs > 0:
        final_result.simulation_results = simulated_ivs

    logger.info(
        "[Engine] Monte Carlo completed | ticker=%s | valid_runs=%s/%s",
        financials.ticker,
        valid_runs,
        num_simulations,
    )
    return final_result


def run_valuation(
    request: ValuationRequest,
    financials: CompanyFinancials,
    auto_params: DCFParameters,
) -> Tuple[DCFParameters, DCFResult]:
    """
    Strict typed entry-point: Request + data => (effective_params, result).
    Does not render UI.
    """
    if request.input_source == InputSource.MANUAL:
        if request.manual_params is None:
            raise WorkflowError("manual_params is required when input_source=MANUAL")

        params = request.manual_params

        if request.manual_beta is not None:
            financials.beta = float(request.manual_beta)

        # Preserve stochastic controls from AUTO (risk model continuity).
        params.beta_volatility = auto_params.beta_volatility
        params.growth_volatility = auto_params.growth_volatility
        params.terminal_growth_volatility = auto_params.terminal_growth_volatility
    else:
        params = auto_params

    params.projection_years = int(request.projection_years)
    params.normalize_weights()

    logger.info(
        "[Engine] run_valuation | ticker=%s | mode=%s | source=%s | years=%s",
        request.ticker,
        request.mode.value,
        request.input_source.value,
        request.projection_years,
    )

    if request.mode == ValuationMode.MONTE_CARLO:
        n = int(request.options.get("num_simulations", 2000))
        return params, run_monte_carlo_dcf(financials, params, num_simulations=n)

    return params, run_deterministic_dcf(financials, params, request.mode)
