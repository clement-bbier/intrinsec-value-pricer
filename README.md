# Intrinsic Value Pricer (DCF & More)

This project provides an educational and transparent interface to estimate the intrinsic value of a publicly listed company.

The goal is not to predict short-term stock prices, but to:

- Show how different valuation frameworks work.
- Make assumptions explicit (growth, discount rates, margins, risk).
- Help users understand how sensitive intrinsic value is to these assumptions.
- Offer several valuation methods within the same app, with a common interface.

This project is for learning and experimentation only.  
It is not investment advice or a recommendation to buy or sell any security.

## What Is Intrinsic Value?

Intrinsic value is an estimate of what a business is economically worth, based on its ability to generate cash flows over time.

It is different from:

- Market price: current stock price, driven by supply/demand, sentiment, news.
- Book value: accounting equity, not necessarily economic value.
- Speculative value: driven by narratives, momentum, liquidity.

There is no unique “true” intrinsic value.  
Every model is a set of assumptions; intrinsic value is always an estimate.

## Common Valuation Families in Practice

In corporate finance, equity research, and M&A, several major families coexist:

1. Discounted Cash Flow (DCF)
2. Multiples / Relative Valuation
3. Dividend Discount Models (DDM)
4. Residual Income / Economic Profit
5. Asset-Based Valuation

This project aims to expose several of these ideas inside a single, consistent tool.

## Valuation Methods in This Project

The app supports multiple valuation engines, each with its own assumptions and use cases.

### Method 1 – Simple DCF (FCFF ≈ CFO – Capex)

Status: Implemented

Approximates Free Cash Flow to the Firm (FCFF) as:

FCFF ≈ CFO + Capex

Then:

1. Projects FCFF over n years.
2. Computes the discount rate (WACC).
3. Discounts projected FCFs.
4. Computes terminal value.
5. Computes enterprise value.
6. Computes equity value.
7. Computes intrinsic value per share.

Useful for stable, cash-generative businesses.  
Robust and easy to understand.

### Method 2 – Fundamental DCF (Full FCFF Construction)

Status: Planned

Builds FCFF rigorously from financial statements:

- EBIT → NOPAT
- Add back depreciation
- Subtract change in working capital
- Subtract Capex

Used in M&A, private equity, equity research.

### Method 3 – Relative Valuation (Market Multiples)

Status: Planned

Compares valuation to peers using multiples:

- P/E
- EV/EBITDA
- EV/EBIT
- EV/Sales

Used for fast market-relative valuation.

### Method 4 – Scenarios & Simulations (Monte Carlo, LBO)

Status: Planned

Explicitly models uncertainty:

- Scenario-based DCF
- Monte Carlo simulation of growth and discount rates
- LBO-style leveraged models

Useful when uncertainty is high.

## Why Start with DCF (Method 1)?

It is conceptually rigorous and transparent.  
All assumptions are explicit: growth, discount rate, reinvestment, terminal value.  
However, small changes in assumptions can significantly affect results.

This project embraces that by:

- Logging every calculation.
- Displaying all intermediate steps.
- Allowing comparisons across methods (future versions).

## Current Features (MVP)

- Fetches market and financial data from Yahoo Finance.
- Computes FCFF using CFO and Capex.
- Multi-year DCF valuation with terminal value.
- Computes WACC using CAPM and cost of debt.
- Displays market price vs intrinsic value.
- Provides detailed logging.
- Central configuration via settings.yaml.
- Architecture already supports multiple valuation modes.

## Project Structure

```
intrinsec-value-pricer/
├── app/
│   └── main.py
├── core/
│   ├── models.py
│   ├── exceptions.py
│   └── dcf/
│       ├── fcf.py
│       ├── wacc.py
│       ├── basic_engine.py
│       ├── valuation_service.py
│       └── valuation.py
├── infra/
│   └── data_providers/
│       ├── base_provider.py
│       └── yahoo_provider.py
├── tests/
│   ├── test_calculator.py
│   └── test_yahoo_provider_integration.py
├── config/
│   └── settings.yaml
├── docs/
│   ├── evolution_plan_for_dcf_calculation.md
│   └── yfinance_references.md
├── README.md
├── requirements.txt
└── pytest.ini
```

## Installation

```
pip install -r requirements.txt
```

## Run the Application

```
streamlit run app/main.py
```

## Configuration

Default assumptions are in:

```
config/settings.yaml
```

## Roadmap

- Fundamental DCF (Method 2)
- Market multiples (Method 3)
- Simulations and scenario analysis (Method 4)
- Sensitivity analysis
- Better charts and visualisations
- Export to PDF/HTML
- Batch valuation for multiple tickers

## Disclaimer

This project is for educational purposes only.  
It does not provide investment advice.
