import os
import sys
import logging
from pathlib import Path

# --- Ensure project root is on sys.path ---
ROOT = Path(__file__).resolve().parents[1]  # "intrinsec-value-pricer" folder
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import altair as alt

from core.models import DCFParameters, ValuationMode
from core.dcf.valuation_service import run_valuation
from core.exceptions import CalculationError, DataProviderError
from infra.data_providers.yahoo_provider import YahooFinanceProvider


# -------------------------------------------------
# Logging configuration (granular & structured)
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Silence yfinance logs
logging.getLogger("yfinance").setLevel(logging.ERROR)


# -------------------------------------------------
# Valuation modes – labels shown to the end-user
# -------------------------------------------------
MODE_LABELS = {
    ValuationMode.SIMPLE_FCFF: (
        "Method 1 – Simple DCF "
        "(enterprise value from operating cash flow and CAPEX)"
    ),
    ValuationMode.FUNDAMENTAL_FCFF: (
        "Method 2 – Detailed DCF "
        "(FCFF built from income statement, balance sheet, and cash flow statement)"
    ),
    ValuationMode.MARKET_MULTIPLES: (
        "Method 3 – Market comparables "
        "(valuation using trading multiples: P/E, EV/EBITDA, etc.)"
    ),
    ValuationMode.ADVANCED_SIMULATION: (
        "Method 4 – Scenario and simulation models "
        "(stress tests, Monte Carlo, LBO-style models)"
    ),
}

LABEL_TO_MODE = {v: k for k, v in MODE_LABELS.items()}


# -------------------------------------------------
# Global config (MVP)
# -------------------------------------------------
DEFAULT_PROJECTION_YEARS = 5
PROVIDER = YahooFinanceProvider()


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def format_number(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def format_currency(x: float, currency: str) -> str:
    return f"{x:,.2f} {currency}".replace(",", " ")


# -------------------------------------------------
# Core workflow
# -------------------------------------------------
def run_workflow_and_display(
    ticker: str,
    projection_years: int,
    mode: ValuationMode,
) -> None:
    """
    Full workflow:
    - Fetch financial data
    - Build DCF assumptions
    - Run valuation engine (depending on mode)
    - Display outputs and chart
    """

    logger.info("=== NEW VALUATION REQUEST ===")
    logger.info(
        "Ticker=%s | Projection years=%d | Mode=%s",
        ticker,
        projection_years,
        mode.value,
    )

    try:
        # ---------------------------------------------------------
        # 1) Load data + DCF parameters
        # ---------------------------------------------------------
        logger.info("[1] Fetching financial data for %s...", ticker)
        with st.spinner(f"Fetching financial data and assumptions for {ticker}..."):
            financials, params = PROVIDER.get_company_financials_and_parameters(
                ticker=ticker,
                projection_years=projection_years,
            )

        logger.info(
            "[1] Financials for %s | Price=%.2f %s | Shares=%.0f | Debt=%.0f | Cash=%.0f | FCFF_last=%.2f | Beta=%.2f",
            financials.ticker,
            financials.current_price,
            financials.currency,
            financials.shares_outstanding,
            financials.total_debt,
            financials.cash_and_equivalents,
            financials.fcf_last,
            financials.beta,
        )

        logger.info(
            "[1] Assumptions | Rf=%.2f%% | MRP=%.2f%% | Rd=%.2f%% | Tax=%.2f%% | g_FCF=%.2f%% | g∞=%.2f%% | n=%d",
            params.risk_free_rate * 100,
            params.market_risk_premium * 100,
            params.cost_of_debt * 100,
            params.tax_rate * 100,
            params.fcf_growth_rate * 100,
            params.perpetual_growth_rate * 100,
            params.projection_years,
        )

        # ---------------------------------------------------------
        # 2) Run valuation engine (depending on mode)
        # ---------------------------------------------------------
        logger.info("[2] Running valuation engine (mode=%s)…", mode.value)
        with st.spinner("Running valuation model..."):
            dcf_result = run_valuation(financials, params, mode)

        logger.info("[2] Valuation completed successfully for %s", ticker)
        logger.info(
            "[2] Intrinsic value per share = %.2f %s | WACC=%.2f%%",
            dcf_result.intrinsic_value_per_share,
            financials.currency,
            dcf_result.wacc * 100,
        )

        # ---------------------------------------------------------
        # 3) Display everything in the UI
        # ---------------------------------------------------------
        display_results(financials, params, dcf_result, mode)
        display_price_chart(
            ticker=ticker,
            intrinsic_value=dcf_result.intrinsic_value_per_share,
            currency=financials.currency,
        )

    except DataProviderError as e:
        logger.error("[ERROR] DataProviderError for %s: %s", ticker, e)
        st.error(f"Data error: could not fetch required financial data for {ticker}.")
        st.caption(f"Details: {e}")

    except CalculationError as e:
        logger.error("[ERROR] CalculationError for %s: %s", ticker, e)
        st.error("Calculation error: the valuation model could not be solved.")
        st.caption(f"Details: {e}")

    except NotImplementedError as e:
        logger.warning(
            "[ERROR] Valuation mode %s not implemented yet for %s: %s",
            mode.value,
            ticker,
            e,
        )
        st.error("This valuation method is not implemented in the application yet.")
        st.caption("For now, only Method 1 – Simple DCF is fully implemented.")

    except Exception as e:
        logger.exception("[ERROR] Unexpected exception during valuation for %s", ticker)
        st.exception(f"Unexpected error: {e}")


# -------------------------------------------------
# Display functions
# -------------------------------------------------
def display_results(
    financials,
    params: DCFParameters,
    result,
    mode: ValuationMode,
) -> None:
    """Display KPIs, model assumptions and (for now) the Method 1 formula."""
    st.subheader(f"Intrinsic Valuation – {financials.ticker}")

    # --- Top KPIs ---
    col_price, col_iv, col_delta = st.columns(3)

    market_price = financials.current_price
    intrinsic_value = result.intrinsic_value_per_share
    currency = financials.currency

    price_label = f"Market Price ({currency})"
    iv_label = f"Intrinsic Value ({currency})"

    delta_abs = intrinsic_value - market_price
    delta_pct = (delta_abs / market_price) * 100 if market_price > 0 else 0.0

    with col_price:
        st.metric(
            label=price_label,
            value=format_currency(market_price, currency),
        )

    with col_iv:
        st.metric(
            label=iv_label,
            value=format_currency(intrinsic_value, currency),
        )

    with col_delta:
        delta_prefix = "Undervalued" if delta_abs > 0 else "Overvalued"
        st.metric(
            label="Upside / Downside",
            value=f"{delta_prefix} {delta_abs:,.2f} {currency}".replace(",", " "),
            delta=f"{delta_pct:.2f}%",
        )

    st.markdown("---")

    # --- Detailed assumptions and balance sheet snapshot ---
    c1, c2, c3 = st.columns(3)

    # Market & risk inputs
    with c1:
        st.caption("Market and risk inputs")
        df_market = pd.DataFrame(
            {
                "Parameter": [
                    "Risk-free rate (Rf)",
                    "Market risk premium (MRP)",
                    "Cost of debt (Rd)",
                    "Tax rate",
                    "WACC",
                ],
                "Value": [
                    format_pct(params.risk_free_rate),
                    format_pct(params.market_risk_premium),
                    format_pct(params.cost_of_debt),
                    format_pct(params.tax_rate),
                    format_pct(result.wacc),
                ],
            }
        )
        df_market.index = [""] * len(df_market)
        st.table(df_market)

    # DCF growth assumptions
    with c2:
        st.caption("DCF growth assumptions")
        df_growth = pd.DataFrame(
            {
                "Parameter": [
                    "Last FCFF",
                    "FCFF growth (stage 1)",
                    "Perpetual growth (g∞)",
                    "Projection years",
                ],
                "Value": [
                    format_currency(financials.fcf_last, currency),
                    format_pct(params.fcf_growth_rate),
                    format_pct(params.perpetual_growth_rate),
                    params.projection_years,
                ],
            }
        )
        df_growth.index = [""] * len(df_growth)
        st.table(df_growth)

    # Balance sheet snapshot
    with c3:
        st.caption("Balance sheet snapshot")
        to_m = lambda v: f"{v / 1e6:.2f} M"
        df_bs = pd.DataFrame(
            {
                "Parameter": [
                    "Shares outstanding",
                    "Total debt",
                    "Cash and equivalents",
                ],
                "Value": [
                    to_m(financials.shares_outstanding),
                    to_m(financials.total_debt),
                    to_m(financials.cash_and_equivalents),
                ],
            }
        )
        df_bs.index = [""] * len(df_bs)
        st.table(df_bs)

    # --- Valuation formula section (currently for Method 1 only) ---
    if mode == ValuationMode.SIMPLE_FCFF:
        display_simple_dcf_formula()


def display_simple_dcf_formula() -> None:
    """
    Show the symbolic formula used in Method 1 – Simple DCF,
    using parameter names consistent with the tables above.
    """
    st.markdown("---")
    st.subheader("Valuation formula – Method 1 (Simple DCF)")

    st.markdown("**Step 1 – Project Free Cash Flow to the Firm (FCFF)**")
    st.latex(
        r"FCFF_0 = \text{Last FCFF}"
    )
    st.latex(
        r"FCFF_t = FCFF_{t-1} \times (1 + g_{\text{FCF}})"
        r"\quad\text{for } t = 1,\dots,n"
    )
    st.markdown(
        "- `Last FCFF` comes from operating cash flow minus CAPEX.\n"
        "- `g_FCF` corresponds to **FCFF growth (stage 1)**.\n"
        "- `n` corresponds to **Projection years**."
    )

    st.markdown("**Step 2 – Discount projected FCFF and terminal value**")
    st.latex(
        r"EV = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + WACC)^t}"
        r" + \frac{TV}{(1 + WACC)^n}"
    )
    st.latex(
        r"TV = \frac{FCFF_{n+1}}{WACC - g_{\infty}}"
        r"\quad\text{with}\quad FCFF_{n+1} = FCFF_n \times (1 + g_{\infty})"
    )
    st.markdown(
        "- `WACC` is computed from **Risk-free rate (Rf)**, "
        "**Market risk premium (MRP)**, **Cost of debt (Rd)** and **Tax rate**.\n"
        "- `g_∞` corresponds to **Perpetual growth (g∞)**."
    )

    st.markdown("**Step 3 – From enterprise value to equity value**")
    st.latex(
        r"Equity\ Value = EV - \text{Total debt} + \text{Cash and equivalents}"
    )

    st.markdown("**Step 4 – Intrinsic value per share**")
    st.latex(
        r"\text{Intrinsic value per share} = "
        r"\frac{Equity\ Value}{\text{Shares outstanding}}"
    )
    st.caption(
        "The intrinsic value used in the KPI section above is the result of these steps "
        "applied to the parameters shown in the three tables."
    )


def display_price_chart(ticker: str, intrinsic_value: float, currency: str) -> None:
    """
    Display a 5-year chart comparing:
    - Market price (daily)
    - Intrinsic value (points every 6 months, connected by a line)

    For now, intrinsic_value is the current DCF estimate reused at each point.
    Later this can be replaced by a true historical DCF recomputation.
    """
    try:
        logger.info("[Chart] Loading price history for %s...", ticker)

        hist = PROVIDER.get_price_history(ticker, period="5y")
        if hist is None or hist.empty:
            logger.warning("[Chart] No price history for %s", ticker)
            st.warning("No price history available to build the chart.")
            return

        # 1) Clean historical data
        hist = hist.reset_index()

        # Normalize date column name
        if "Date" not in hist.columns:
            date_cols = [c for c in hist.columns if "date" in c.lower()]
            if not date_cols:
                raise ValueError("No date column found in price history dataframe.")
            hist = hist.rename(columns={date_cols[0]: "Date"})

        # Normalize close column
        if "close" not in hist.columns:
            raise ValueError("Expected 'close' column in price history dataframe.")

        # Ensure proper types
        hist["Date"] = pd.to_datetime(hist["Date"])
        hist = hist.sort_values("Date")

        # Ensure "close" is 1-dimensional
        close_values = hist["close"].to_numpy().reshape(-1).astype(float)

        # DataFrame for daily market price
        df_price = pd.DataFrame(
            {
                "Date": hist["Date"],
                "Market Price": close_values,
            }
        )

        # 2) Points every 6 months for intrinsic value
        # Use "6ME" (6-month end) to avoid FutureWarning
        tmp = df_price.set_index("Date").resample("6ME").first().dropna().reset_index()

        if tmp.empty:
            logger.warning("[Chart] Not enough data to resample 6ME for %s", ticker)
            st.warning("Not enough historical data to build the intrinsic value timeline.")
            return

        df_intrinsic = pd.DataFrame(
            {
                "Date": tmp["Date"],
                "Intrinsic Value": float(intrinsic_value),
            }
        )

        # 3) Build Altair chart
        price_line = (
            alt.Chart(df_price)
            .mark_line()
            .encode(
                x="Date:T",
                y=alt.Y("Market Price:Q", title=f"Price / Intrinsic Value ({currency})"),
                tooltip=[
                    alt.Tooltip("Date:T", title="Date"),
                    alt.Tooltip("Market Price:Q", title="Market price", format=".2f"),
                ],
            )
        )

        # Intrinsic value line in red with points
        intrinsic_line = (
            alt.Chart(df_intrinsic)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y="Intrinsic Value:Q",
                color=alt.value("red"),
                tooltip=[
                    alt.Tooltip("Date:T", title="Date"),
                    alt.Tooltip(
                        "Intrinsic Value:Q",
                        title="Intrinsic value",
                        format=".2f",
                    ),
                ],
            )
        )

        chart = (price_line + intrinsic_line).properties(
            title=(
                f"Market price vs intrinsic value "
                f"(Method 1 – Simple DCF) for {ticker}"
            ),
            height=400,
        )

        st.subheader("Market price vs intrinsic value (last 5 years)")
        st.altair_chart(chart, width="stretch")
        st.caption(
            "Intrinsic value points are currently based on the latest DCF estimate, "
            "repeated every 6 months. In a later version, each point will be recomputed "
            "at each date using historical financials and the selected valuation method."
        )

    except Exception as e:
        logger.error("[Chart] Failed to build chart for %s: %s", ticker, e)
        st.warning(f"Could not build price vs intrinsic value chart. Details: {e}")


# -------------------------------------------------
# Streamlit main
# -------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Intrinsic Value Pricer (DCF)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Intrinsic Value Calculator (DCF)")

    # Sidebar inputs
    st.sidebar.header("Inputs")

    ticker = st.sidebar.text_input(
        "Ticker symbol",
        value="AAPL",
        help="Example: AAPL, MSFT, TSLA",
    ).upper().strip()

    projection_years = st.sidebar.number_input(
        "Projection years (n)",
        min_value=3,
        max_value=10,
        value=DEFAULT_PROJECTION_YEARS,
        step=1,
        help="DCF projection horizon (in years).",
    )

    # Valuation mode selectbox
    mode_label = st.sidebar.selectbox(
        "Valuation method",
        options=list(MODE_LABELS.values()),
        index=0,
        help="Choose the method used to compute intrinsic value.",
    )
    mode = LABEL_TO_MODE[mode_label]
    logger.info("Valuation mode selected in UI: %s", mode.value)

    st.sidebar.markdown("---")
    run_button = st.sidebar.button("Calculate", type="primary")

    if run_button:
        if not ticker:
            st.error("Please enter a ticker symbol.")
        else:
            run_workflow_and_display(ticker, int(projection_years), mode)
    else:
        st.info(
            "Enter a ticker and a projection horizon on the left, "
            "then click Calculate."
        )


if __name__ == "__main__":
    main()
