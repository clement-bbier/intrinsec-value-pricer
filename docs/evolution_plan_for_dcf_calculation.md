# Evolution Plan -- Intrinsic Value Pricer (DCF)

## Overview

This document outlines the evolution of the Intrinsic Value Pricer app
from a simple DCF engine to an institutional-grade valuation framework.
It covers financial theory, formulas, required data, technical
architecture, and limitations at each sophistication level.

## 0. Current Version (V1 -- Basic DCF)

### What V1 Implements

-   FCFF = CFO -- Capex
-   Constant growth rate for FCF projections
-   CAPM for Re and simplified WACC
-   Gordon-Shapiro Terminal Value
-   Equity Value = EV -- Debt + Cash
-   Intrinsic Value per share
-   Data from Yahoo Finance via yfinance
-   Streamlit UI (planned)
-   Modular architecture with core/ infra/ app/

## 1. Evolution Funnel (from simple → advanced)

  ----------------------------------------------------------------------------------
  Level     Name          Features         Code Complexity      Data Complexity
  --------- ------------- ---------------- -------------------- --------------------
  V1        Basic DCF     FCFF simple      ★☆☆                  ★☆☆

  PRO 1     3-Statement   EBIT→NOPAT,      ★★☆                  ★★☆
            Light         ΔNWC, scenarios                       

  PRO 2     M&A/IB Level  Multi-segment,   ★★★                  ★★★
                          TV multiples,                         
                          target D/E                            

  EXPERT    Hedge Fund /  Monte Carlo,     ★★★★                 ★★★★
            PE            unlevered beta,                       
                          APIs, LBO                             
  ----------------------------------------------------------------------------------

## 2. V1 Details -- Formulas and Data

### 2.1 FCFF Basic

FCFF = CFO -- Capex

### 2.2 WACC

Re = Rf + β × MRP\
WACC = (E/(E+D))Re + (D/(E+D))Rd(1-T)

### 2.3 Terminal Value

TV = FCF(n+1) / (WACC -- g)

### 2.4 Data Required (available on Yahoo)

-   Price
-   Shares Outstanding
-   Beta
-   Total Debt
-   Cash & Equivalents
-   Cash Flow from Operations
-   Capex
-   Currency
-   Historical prices

## 3. PRO LEVEL 1 -- "3-Statement Light"

### 3.1 Professional FCF

NOPAT = EBIT × (1 -- tax)\
FCF = NOPAT + D&A -- Capex -- ΔNWC

### 3.2 Added Data Required

From income statement: - Revenue - Operating Income (EBIT) -
Depreciation

From balance sheet: - Accounts Receivable - Inventory - Accounts Payable

### 3.3 ΔNWC Calculation

NWC = AR + Inventory -- AP\
ΔNWC = NWC(t) -- NWC(t-1)

### 3.4 Scenarios (Base / Bull / Bear)

Different: - Growth - WACC - g

## 4. PRO LEVEL 2 -- Investment Banking / M&A Models

### 4.1 Multi-Segment Modeling

Break down: - Revenues - Margins - Capex - NWC

⚠️ Hard: segment data rarely available via Yahoo → requires PDF/XBRL
extraction or paid APIs.

### 4.2 Terminal Value via Multiples

TV = EBITDA_final × EV/EBITDA multiple\
Source of multiple: comparables or transactions.

### 4.3 Target Capital Structure and Beta Unlevering

β_u = β / (1 + (1-T)D/E)\
β_r = β_u × (1 + (1-T)D_target/E_target)

Requires: - Peer betas - Peer D/E

## 5. EXPERT LEVEL -- Hedge Funds / PE

### 5.1 Monte Carlo Simulation

Simulate: - WACC - FCF growth - Margins - Terminal g

Outputs: - Distribution of intrinsic values - Probability IV \> Market
Price

### 5.2 Beta From Peer Set

Download betas of comp set → unlever → relever target beta.

### 5.3 Real Financial APIs

Use: - FRED - ECB - RiskFreeRate API - Corporate bond spreads

### 5.4 S-Curve Revenue Forecasting

Logistic growth curve for: - Tech - SaaS - New products

### 5.5 LBO Modeling (IRR-driven)

Project: - Leverage level - Debt amortization - Exit multiple - Compute
IRR equity

## 6. Practical Data Limitations

### What Yahoo Gives Easily

-   CFO
-   Capex
-   EBIT
-   Revenue
-   D&A
-   Some NWC items

### What Is Hard

-   Segment reporting
-   Capex by segment
-   Leases (IFRS 16)
-   Off-balance sheet liabilities
-   SBC (stock comp)
-   Exceptional items

### Requires Multimodal Extraction

-   Annual reports (PDF)
-   10-K / 20-F (HTML/XBRL)
-   Peers datasets

## 7. Architecture for Future Expansion

### core/

-   run_dcf_basic()
-   run_dcf_pro()
-   run_dcf_institutional()

### infra/

-   YahooProviderBasic
-   YahooProviderPro
-   EdgarProvider (optional)
-   PaidAPIProvider (optional)

### app/

-   UI stays simple, selects mode (Basic, Pro, Expert)

## 8. Final Roadmap

### Phase 1 -- Complete V1

-   Yahoo data basic
-   Streamlit UI
-   Pricing service
-   Chart & KPIs

### Phase 2 -- PRO 1

-   EBIT → FCF
-   ΔNWC
-   Scenarios

### Phase 3 -- PRO 2

-   Multi-segment
-   TV multiples
-   Target D/E

### Phase 4 -- EXPERT

-   Monte Carlo
-   Beta peers
-   APIs
-   LBO

## Conclusion

Your current architecture is perfect to absorb these evolutions. The
model can grow from educational to professional without breaking
structure.
