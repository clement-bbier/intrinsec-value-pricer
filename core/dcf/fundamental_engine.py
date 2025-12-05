import logging
from typing import List

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.exceptions import CalculationError
from core.dcf.wacc import compute_cost_of_equity, compute_wacc

logger = logging.getLogger(__name__)


def run_dcf_fundamental_fcff(
    financials: CompanyFinancials,
    params: DCFParameters,
) -> DCFResult:
    """
    Méthode 2 – DCF Fondamental (3-Statement Light)

    FCFF_0 est basé sur un FCFF fondamental construit à partir de :
        NOPAT + D&A - Capex - ΔNWC
    puis lissé sur plusieurs années (calculé côté infra et stocké dans
    CompanyFinancials.fcf_fundamental_smoothed).

    Ici, on ne fait *que* :
    - utiliser ce FCFF_0 comme point de départ,
    - projeter les FCFF,
    - calculer WACC, TV, EV, Equity et VI par action.

    Toute la complexité “3-états financiers” est encapsulée dans l’infra.
    """

    # ----------------------------------------------------------------------
    # 0. Vérifications préalables
    # ----------------------------------------------------------------------
    if financials.fcf_fundamental_smoothed is None:
        msg = (
            "Impossible de calculer la Méthode 2 (DCF fondamental) : "
            "fcf_fundamental_smoothed est None. "
            "Les données historiques nécessaires (NOPAT, Capex, ΔNWC sur plusieurs années) "
            "sont insuffisantes ou incomplètes pour ce ticker."
        )
        logger.error("[FundamentalDCF] %s", msg)
        raise CalculationError(msg)

    if financials.shares_outstanding is None or financials.shares_outstanding <= 0:
        msg = (
            "Nombre d'actions en circulation invalide ou nul pour le ticker "
            f"{financials.ticker}."
        )
        logger.error("[FundamentalDCF] %s", msg)
        raise CalculationError(msg)

    fcff0 = float(financials.fcf_fundamental_smoothed)
    n = int(params.projection_years)
    g = float(params.fcf_growth_rate)
    g_inf = float(params.perpetual_growth_rate)

    if n <= 0:
        msg = "Le nombre d'années de projection doit être strictement positif."
        logger.error("[FundamentalDCF] %s", msg)
        raise CalculationError(msg)

    # ----------------------------------------------------------------------
    # 1. WACC (même logique que la Méthode 1)
    # ----------------------------------------------------------------------
    # 1) Valeur de marché des fonds propres
    equity_value_market = financials.current_price * financials.shares_outstanding
    logger.info(
        "[FundamentalDCF][1] Market Equity Value E = Price * Shares = %.2f * %.0f = %.2f",
        financials.current_price,
        financials.shares_outstanding,
        equity_value_market,
    )

    # 2) Coût des fonds propres (CAPM)
    cost_of_equity = compute_cost_of_equity(
        risk_free_rate=params.risk_free_rate,
        beta=financials.beta,
        market_risk_premium=params.market_risk_premium,
    )

    logger.info(
        "[FundamentalDCF][2] Cost of equity (CAPM) Re = Rf + beta * MRP = %.4f + %.4f * %.4f = %.4f",
        params.risk_free_rate,
        financials.beta,
        params.market_risk_premium,
        cost_of_equity,
    )

    # 3) WACC
    try:
        wacc, after_tax_cost_of_debt = compute_wacc(
            equity_value=equity_value_market,
            debt_value=financials.total_debt,
            cost_of_equity=cost_of_equity,
            cost_of_debt=params.cost_of_debt,
            tax_rate=params.tax_rate,
        )
    except Exception as e:
        msg = f"Erreur lors du calcul du WACC pour {financials.ticker}: {e}"
        logger.error("[FundamentalDCF] %s", msg)
        raise CalculationError(msg)

    logger.info(
        "[FundamentalDCF][3] WACC = (E/(E+D))*Re + (D/(E+D))*Rd(1-T) = %.6f",
        wacc,
    )
    logger.info(
        "[FundamentalDCF][3] After-tax cost of debt Rd(1-T) = %.6f",
        after_tax_cost_of_debt,
    )

    if wacc <= g_inf:
        msg = (
            f"La croissance perpétuelle g∞ ({g_inf:.4%}) est supérieure ou égale au WACC "
            f"({wacc:.4%}). Le modèle de Gordon-Shapiro ne converge pas."
        )
        logger.error("[FundamentalDCF] %s", msg)
        raise CalculationError(msg)

    logger.info(
        "[FundamentalDCF] Démarrage du DCF fondamental pour %s – FCFF0=%.2f, g=%.2f%%, g∞=%.2f%%, WACC=%.2f%%",
        financials.ticker,
        fcff0,
        g * 100,
        g_inf * 100,
        wacc * 100,
    )

    # ----------------------------------------------------------------------
    # 2. Projection des FCFF (phase explicite)
    # ----------------------------------------------------------------------
    projected_fcfs: List[float] = []
    discount_factors: List[float] = []

    for t in range(1, n + 1):
        # FCFF_t = FCFF_0 * (1 + g)^t
        fcf_t = fcff0 * (1.0 + g) ** t
        df_t = 1.0 / (1.0 + wacc) ** t

        projected_fcfs.append(fcf_t)
        discount_factors.append(df_t)

    discounted_fcfs = [fcf * df for fcf, df in zip(projected_fcfs, discount_factors)]
    sum_discounted_fcf = float(sum(discounted_fcfs))

    # ----------------------------------------------------------------------
    # 3. Valeur Terminale (Gordon-Shapiro)
    # ----------------------------------------------------------------------
    fcf_n = projected_fcfs[-1]
    fcf_n_plus_1 = fcf_n * (1.0 + g_inf)

    terminal_value = fcf_n_plus_1 / (wacc - g_inf)
    discounted_terminal_value = terminal_value / ((1.0 + wacc) ** n)

    logger.info(
        "[FundamentalDCF][6] FCF_terminal = FCFF_n * (1+g∞) = %.2f * (1 + %.4f) = %.2f",
        fcf_n,
        g_inf,
        fcf_n_plus_1,
    )
    logger.info(
        "[FundamentalDCF][6] Terminal Value TV = FCF_{n+1} / (WACC - g∞) = %.2f / (%.6f - %.6f) = %.2f",
        fcf_n_plus_1,
        wacc,
        g_inf,
        terminal_value,
    )
    logger.info(
        "[FundamentalDCF][6] Discounted TV = TV / (1+WACC)^n = %.2f / (1+%.6f)^%d = %.2f",
        terminal_value,
        wacc,
        n,
        discounted_terminal_value,
    )

    # ----------------------------------------------------------------------
    # 4. Valeur d'Entreprise (EV), Equity et VI par action
    # ----------------------------------------------------------------------
    enterprise_value = sum_discounted_fcf + discounted_terminal_value

    equity_value = (
        enterprise_value
        - float(financials.total_debt)
        + float(financials.cash_and_equivalents)
    )

    intrinsic_value_per_share = equity_value / float(financials.shares_outstanding)

    logger.info(
        "[FundamentalDCF] Résultat pour %s – EV=%.2f, Equity=%.2f, IV/Share=%.2f",
        financials.ticker,
        enterprise_value,
        equity_value,
        intrinsic_value_per_share,
    )

    return DCFResult(
        wacc=wacc,
        cost_of_equity=cost_of_equity,
        after_tax_cost_of_debt=after_tax_cost_of_debt,
        projected_fcfs=projected_fcfs,
        discount_factors=discount_factors,
        sum_discounted_fcf=sum_discounted_fcf,
        terminal_value=terminal_value,
        discounted_terminal_value=discounted_terminal_value,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        intrinsic_value_per_share=intrinsic_value_per_share,
    )
