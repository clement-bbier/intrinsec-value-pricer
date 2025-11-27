Intrinsic Value Pricer (DCF)
============================

This project provides an educational and transparent interface to estimate the intrinsic value of a publicly listed company using a Discounted Cash Flow (DCF) valuation model.

It is not intended to predict future stock prices, but to illustrate how valuation frameworks work and how assumptions (growth, discount rates, margins, risk) influence results.

------------------------------------------------------------

What Is Intrinsic Value?
------------------------

Intrinsic value represents the estimated economic worth of a business based on its ability to generate cash flows over time. It differs from:

- Market price: reflects supply, demand, sentiment, and short-term trading noise.
- Book value: accounting-based.
- Speculative value: driven by hype, narratives, or temporary market distortions.

Intrinsic value is always a model-based estimate, not a certainty.

------------------------------------------------------------

Common Valuation Methods
------------------------

Several frameworks are widely used in corporate finance and equity research:

1. Discounted Cash Flow (DCF)
   Projects future free cash flows and discounts them to present value using WACC.

2. Multiples / Relative Valuation
   Compares companies based on ratios (P/E, EV/EBITDA, P/S, etc.).

3. Dividend Discount Model (DDM)
   DCF variant for firms with predictable dividends.

4. Residual Income Models
   Values economic profit over cost of capital.

5. Asset-Based Valuation
   Useful for financial institutions or liquidation cases.

------------------------------------------------------------

Why This Project Uses DCF
-------------------------

DCF is rigorous because it focuses on cash generation, not accounting rules.

It:
- Makes assumptions explicit.
- Forces users to think about risk, growth, and the cost of capital.
- Is widely used in investment banking, equity research, and corporate finance.

However, DCF models are sensitive: small changes in WACC or long-term growth can materially impact the result.

This project uses a simplified version for educational purposes.

------------------------------------------------------------

Features
--------

- Retrieve financial statements and market data from Yahoo Finance (yfinance)
- Compute Free Cash Flow to the Firm (FCFF)
- Multi-year DCF valuation with terminal value
- Built-in WACC computation (CAPM + cost of debt)
- Compare market price vs. intrinsic value
- Streamlit-based interactive UI
- Central configuration via config/settings.yaml

------------------------------------------------------------

Project Structure
-----------------

intrinsic-value-pricer/
├── app/
│   └── main.py                  # Streamlit UI
├── core/
│   ├── models.py                # Domain models (dataclasses)
│   ├── exceptions.py            # Custom error types
│   ├── dcf/                     # Financial logic
│   │   ├── fcf.py
│   │   ├── wacc.py
│   │   └── valuation.py
│   └── services/
│       └── pricing_service.py   # Orchestration layer
├── infra/
│   └── data_providers/
│       ├── base_provider.py
│       └── yahoo_provider.py    # Fetches and maps Yahoo Finance data
├── tests/
│   └── test_calculator.py       # TDD tests for core financial logic
├── config/
│   └── settings.yaml            # Valuation parameters
├── docs/
│   └── architecture.md
├── README.md
├── requirements.txt
└── .gitignore

------------------------------------------------------------

How the DCF Model Works (Simplified)
------------------------------------

1. Retrieve financial data (price, beta, debt, cash, financial statements).
2. Compute FCFF (CFO - Capex).
3. Project FCFF over n years.
4. Compute WACC using CAPM + cost of debt.
5. Discount projected cash flows.
6. Compute terminal value using perpetual growth.
7. Combine results to compute enterprise value.
8. Convert enterprise value to equity value.
9. Compute intrinsic value per share.

------------------------------------------------------------

Installation
------------

git clone <your-repo-url>
cd intrinsic-value-pricer

python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

pip install -r requirements.txt

------------------------------------------------------------

Run the Application
-------------------

streamlit run app/main.py

------------------------------------------------------------

Configuration
-------------

Default assumptions (risk-free rate, market risk premium, tax rate, FCF growth, etc.) are stored in:

config/settings.yaml

Adjust them carefully based on your valuation scenario.

------------------------------------------------------------

Roadmap
-------

- Sensitivity analysis (bull / base / bear)
- Monte Carlo simulation for DCF
- Relative valuation (P/E, EV/EBITDA)
- Live market beta & risk-free rate fetching
- PDF valuation reports
- Batch multi-ticker valuation

------------------------------------------------------------

Disclaimer
----------

This project is for educational purposes only.
Nothing here constitutes financial advice or investment recommendations.
