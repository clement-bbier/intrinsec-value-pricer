import os
import sys
import logging
from pathlib import Path

# --- Ensure project root is on sys.path ---
ROOT = Path(__file__).resolve().parents[1]  # dossier "intrinsec-value-pricer"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from core.models import DCFParameters
from core.dcf.valuation import run_dcf
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
# Global config (MVP)
# -------------------------------------------------
DEFAULT_PROJECTION_YEARS = 5
PROVIDER = YahooFinanceProvider()


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def run_workflow_and_display(ticker: str, projection_years: int) -> None:
    """
    Full workflow:
    - Fetch financial data
    - Build DCF assumptions
    - Run DCF model
    - Display outputs
    """

    logger.info("=== NEW VALUATION REQUEST ===")
    logger.info("Ticker=%s | Projection years=%d", ticker, projection_years)

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
        # 2) Run DCF engine
        # ---------------------------------------------------------
        logger.info("[2] Running DCF valuation engine…")
        with st.spinner("Running DCF valuation..."):
            dcf_result = run_dcf(financials, params)

        logger.info("[2] DCF completed successfully for %s", ticker)
        logger.info(
            "[2] Intrinsic Value per share = %.2f %s | WACC=%.2f%%",
            dcf_result.intrinsic_value_per_share,
            financials.currency,
            dcf_result.wacc * 100,
        )

        # ---------------------------------------------------------
        # 3) Display everything in the UI
        # ---------------------------------------------------------
        display_results(financials, params, dcf_result)
        display_price_chart(ticker, dcf_result.intrinsic_value_per_share)

    except DataProviderError as e:
        logger.error("[ERROR] DataProviderError for %s: %s", ticker, e)
        st.error(f"Data error: could not fetch required financial data for {ticker}.")
        st.caption(f"Details: {e}")

    except CalculationError as e:
        logger.error("[ERROR] CalculationError for %s: %s", ticker, e)
        st.error("Calculation error: the DCF model could not be solved.")
        st.caption(f"Details: {e}")

    except Exception as e:
        logger.exception("[ERROR] Unexpected exception during valuation for %s", ticker)
        st.exception(f"Unexpected error: {e}")


def display_results(financials, params: DCFParameters, result) -> None:
    """Display KPIs and model assumptions."""
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
        st.metric(label=price_label, value=f"{market_price:.2f}")

    with col_iv:
        st.metric(label=iv_label, value=f"{intrinsic_value:.2f}")

    with col_delta:
        direction = "UNDERVALUED" if delta_pct > 0 else "OVERVALUED"
        st.metric(
            label="Upside / Downside",
            value=f"{delta_pct:+.2f} %",
            delta=direction,
        )

    st.markdown("---")

    # --- Model assumptions ---
    st.subheader("Model assumptions")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.caption("Discount rates")
        st.json(
            {
                "Risk-free rate": format_pct(params.risk_free_rate),
                "Market risk premium": format_pct(params.market_risk_premium),
                "WACC": format_pct(result.wacc),
                "Cost of equity (CAPM)": format_pct(result.cost_of_equity),
                "After-tax cost of debt": format_pct(result.after_tax_cost_of_debt),
            }
        )

    with c2:
        st.caption("Growth assumptions")
        st.json(
            {
                "FCF growth (stage 1)": format_pct(params.fcf_growth_rate),
                "Perpetual growth (g)": format_pct(params.perpetual_growth_rate),
                "Projection years": params.projection_years,
            }
        )

    with c3:
        st.caption("Balance sheet snapshot")
        to_m = lambda v: f"{v / 1e6:.2f} M"
        st.json(
            {
                "Shares outstanding": to_m(financials.shares_outstanding),
                "Total debt": to_m(financials.total_debt),
                "Cash & equivalents": to_m(financials.cash_and_equivalents),
                "Last FCF": to_m(financials.fcf_last),
            }
        )


def display_price_chart(ticker: str, intrinsic_value: float) -> None:
    """
    Historical Market Price vs Intrinsic Value (5Y).
    Fixes MultiIndex chart error.
    """
    try:
        logger.info("[Chart] Loading price history for %s...", ticker)

        hist = PROVIDER.get_price_history(ticker, period="5y")
        if hist.empty:
            logger.warning("[Chart] No price history for %s", ticker)
            st.warning("No price history available to build the chart.")
            return

        # --- FIX 1: Reset index to avoid Streamlit MultiIndex issues ---
        hist = hist.reset_index()

        # --- FIX 2: Guarantee clean column names ---
        df = pd.DataFrame({
            "Date": hist["Date"],
            "Market Price": hist["close"].astype(float),
            "Intrinsic Value": float(intrinsic_value),
        })

        # --- FIX 3: Streamlit needs the Date as index ---
        df = df.set_index("Date")

        st.subheader("Historical Market Price vs Intrinsic Value (5Y)")
        st.line_chart(df)

        st.caption("Intrinsic value is a static estimate based on current DCF assumptions.")

    except Exception as e:
        logger.error("[Chart] Failed to build chart for %s: %s", ticker, e)
        st.warning(f"Could not load price history for charting. Details: {e}")


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
    )

    st.sidebar.markdown("---")
    run_button = st.sidebar.button("Calculate", type="primary")

    if run_button:
        if not ticker:
            st.error("Please enter a ticker symbol.")
        else:
            run_workflow_and_display(ticker, int(projection_years))
    else:
        st.info("👈 Enter a ticker and projection horizon, then click **Calculate**.")


if __name__ == "__main__":
    main()
