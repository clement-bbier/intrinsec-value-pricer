# Yahoo Finance – Reference Snapshot (AAPL)

This document summarizes the main fields available via `yfinance.Ticker("AAPL")`
based on an actual snapshot.  
Goal: use the **correct labels** (capitalization, spacing) when mapping Yahoo
data → our `CompanyFinancials` and DCF engine.

---

## 1. `Ticker.info` – Available Keys

Object type:

- `type(yt.info) = dict`

Sorted list of keys observed for AAPL:

- `52WeekChange`
- `SandP52WeekChange`
- `address1`
- `allTimeHigh`
- `allTimeLow`
- `ask`
- `askSize`
- `auditRisk`
- `averageAnalystRating`
- `averageDailyVolume10Day`
- `averageDailyVolume3Month`
- `averageVolume`
- `averageVolume10days`
- `beta`
- `bid`
- `bidSize`
- `boardRisk`
- `bookValue`
- `city`
- `companyOfficers`
- `compensationAsOfEpochDate`
- `compensationRisk`
- `corporateActions`
- `country`
- `cryptoTradeable`
- `currency`
- `currentPrice`
- `currentRatio`
- `customPriceAlertConfidence`
- `dateShortInterest`
- `dayHigh`
- `dayLow`
- `debtToEquity`
- `displayName`
- `dividendDate`
- `dividendRate`
- `dividendYield`
- `earningsCallTimestampEnd`
- `earningsCallTimestampStart`
- `earningsGrowth`
- `earningsQuarterlyGrowth`
- `earningsTimestamp`
- `earningsTimestampEnd`
- `earningsTimestampStart`
- `ebitda`
- `ebitdaMargins`
- `enterpriseToEbitda`
- `enterpriseToRevenue`
- `enterpriseValue`
- `epsCurrentYear`
- `epsForward`
- `epsTrailingTwelveMonths`
- `esgPopulated`
- `exDividendDate`
- `exchange`
- `exchangeDataDelayedBy`
- `exchangeTimezoneName`
- `exchangeTimezoneShortName`
- `executiveTeam`
- `fiftyDayAverage`
- `fiftyDayAverageChange`
- `fiftyDayAverageChangePercent`
- `fiftyTwoWeekChangePercent`
- `fiftyTwoWeekHigh`
- `fiftyTwoWeekHighChange`
- `fiftyTwoWeekHighChangePercent`
- `fiftyTwoWeekLow`
- `fiftyTwoWeekLowChange`
- `fiftyTwoWeekLowChangePercent`
- `fiftyTwoWeekRange`
- `financialCurrency`
- `firstTradeDateMilliseconds`
- `fiveYearAvgDividendYield`
- `floatShares`
- `forwardEps`
- `forwardPE`
- `freeCashflow`
- `fullExchangeName`
- `fullTimeEmployees`
- `gmtOffSetMilliseconds`
- `governanceEpochDate`
- `grossMargins`
- `grossProfits`
- `hasPrePostMarketData`
- `heldPercentInsiders`
- `heldPercentInstitutions`
- `impliedSharesOutstanding`
- `industry`
- `industryDisp`
- `industryKey`
- `irWebsite`
- `isEarningsDateEstimate`
- `language`
- `lastDividendDate`
- `lastDividendValue`
- `lastFiscalYearEnd`
- `lastSplitDate`
- `lastSplitFactor`
- `longBusinessSummary`
- `longName`
- `market`
- `marketCap`
- `marketState`
- `maxAge`
- `messageBoardId`
- `mostRecentQuarter`
- `netIncomeToCommon`
- `nextFiscalYearEnd`
- `numberOfAnalystOpinions`
- `open`
- `operatingCashflow`
- `operatingMargins`
- `overallRisk`
- `payoutRatio`
- `phone`
- `postMarketChange`
- `postMarketChangePercent`
- `postMarketPrice`
- `postMarketTime`
- `previousClose`
- `priceEpsCurrentYear`
- `priceHint`
- `priceToBook`
- `priceToSalesTrailing12Months`
- `profitMargins`
- `quickRatio`
- `quoteSourceName`
- `quoteType`
- `recommendationKey`
- `recommendationMean`
- `region`
- `regularMarketChange`
- `regularMarketChangePercent`
- `regularMarketDayHigh`
- `regularMarketDayLow`
- `regularMarketDayRange`
- `regularMarketOpen`
- `regularMarketPreviousClose`
- `regularMarketPrice`
- `regularMarketTime`
- `regularMarketVolume`
- `returnOnAssets`
- `returnOnEquity`
- `revenueGrowth`
- `revenuePerShare`
- `sector`
- `sectorDisp`
- `sectorKey`
- `shareHolderRightsRisk`
- `sharesOutstanding`
- `sharesPercentSharesOut`
- `sharesShort`
- `sharesShortPreviousMonthDate`
- `sharesShortPriorMonth`
- `shortName`
- `shortPercentOfFloat`
- `shortRatio`
- `sourceInterval`
- `state`
- `symbol`
- `targetHighPrice`
- `targetLowPrice`
- `targetMeanPrice`
- `targetMedianPrice`
- `totalCash`
- `totalCashPerShare`
- `totalDebt`
- `totalRevenue`
- `tradeable`
- `trailingAnnualDividendRate`
- `trailingAnnualDividendYield`
- `trailingEps`
- `trailingPE`
- `trailingPegRatio`
- `triggerable`
- `twoHundredDayAverage`
- `twoHundredDayAverageChange`
- `twoHundredDayAverageChangePercent`
- `typeDisp`
- `volume`
- `website`
- `zip`

**Fields used in the DCF engine (V1):**

- `regularMarketPrice` or `currentPrice` → current stock price
- `sharesOutstanding` → number of shares
- `beta` → equity beta
- `currency` → reporting currency
- optionally `operatingCashflow`, `totalDebt`, `totalCash` as fallbacks

---

## 2. Annual Balance Sheet (`yt.balance_sheet`)

Shape: 69 rows × 5 columns  
Columns (dates):

- `2025-09-30`
- `2024-09-30`
- `2023-09-30`
- `2022-09-30`
- `2021-09-30`

Index (rows):

- `Treasury Shares Number`
- `Ordinary Shares Number`
- `Share Issued`
- `Net Debt`
- `Total Debt` ⭐
- `Tangible Book Value`
- `Invested Capital`
- `Working Capital`
- `Net Tangible Assets`
- `Capital Lease Obligations`
- `Common Stock Equity`
- `Total Capitalization`
- `Total Equity Gross Minority Interest`
- `Stockholders Equity`
- `Gains Losses Not Affecting Retained Earnings`
- `Other Equity Adjustments`
- `Retained Earnings`
- `Capital Stock`
- `Common Stock`
- `Total Liabilities Net Minority Interest`
- `Total Non Current Liabilities Net Minority Interest`
- `Other Non Current Liabilities`
- `Tradeand Other Payables Non Current`
- `Long Term Debt And Capital Lease Obligation`
- `Long Term Capital Lease Obligation`
- `Long Term Debt`
- `Current Liabilities`
- `Other Current Liabilities`
- `Current Deferred Liabilities`
- `Current Deferred Revenue`
- `Current Debt And Capital Lease Obligation`
- `Current Capital Lease Obligation`
- `Current Debt`
- `Other Current Borrowings`
- `Commercial Paper`
- `Payables And Accrued Expenses`
- `Current Accrued Expenses`
- `Payables`
- `Total Tax Payable`
- `Income Tax Payable`
- `Accounts Payable`
- `Total Assets`
- `Total Non Current Assets`
- `Other Non Current Assets`
- `Non Current Deferred Assets`
- `Non Current Deferred Taxes Assets`
- `Investments And Advances`
- `Other Investments`
- `Investmentin Financial Assets`
- `Available For Sale Securities`
- `Net PPE`
- `Accumulated Depreciation`
- `Gross PPE`
- `Leases`
- `Other Properties`
- `Machinery Furniture Equipment`
- `Land And Improvements`
- `Properties`
- `Current Assets`
- `Other Current Assets`
- `Inventory`
- `Receivables`
- `Other Receivables`
- `Accounts Receivable`
- `Cash Cash Equivalents And Short Term Investments`
- `Other Short Term Investments`
- `Cash And Cash Equivalents` ⭐
- `Cash Equivalents`
- `Cash Financial`

**Fields used in the DCF engine (V1):**

- `Total Debt` → `total_debt`
- `Cash And Cash Equivalents` (fallback: possibly `Cash Cash Equivalents And Short Term Investments`) → `cash_and_equivalents`

---

## 3. Annual Cash Flow Statement (`yt.cashflow`)

Shape: many rows × 5 columns  
Columns (dates):

- `2025-09-30`
- `2024-09-30`
- `2023-09-30`
- `2022-09-30`
- `2021-09-30`

Index (rows):

- `Free Cash Flow`
- `Repurchase Of Capital Stock`
- `Repayment Of Debt`
- `Issuance Of Debt`
- `Issuance Of Capital Stock`
- `Capital Expenditure` ⭐
- `Interest Paid Supplemental Data`
- `Income Tax Paid Supplemental Data`
- `End Cash Position`
- `Beginning Cash Position`
- `Changes In Cash`
- `Financing Cash Flow`
- `Cash Flow From Continuing Financing Activities`
- `Net Other Financing Charges`
- `Cash Dividends Paid`
- `Common Stock Dividend Paid`
- `Net Common Stock Issuance`
- `Common Stock Payments`
- `Common Stock Issuance`
- `Net Issuance Payments Of Debt`
- `Net Short Term Debt Issuance`
- `Net Long Term Debt Issuance`
- `Long Term Debt Payments`
- `Long Term Debt Issuance`
- `Investing Cash Flow`
- `Cash Flow From Continuing Investing Activities`
- `Net Other Investing Changes`
- `Net Investment Purchase And Sale`
- `Sale Of Investment`
- `Purchase Of Investment`
- `Net Business Purchase And Sale`
- `Purchase Of Business`
- `Net PPE Purchase And Sale`
- `Purchase Of PPE`
- `Operating Cash Flow` ⭐
- `Cash Flow From Continuing Operating Activities`
- `Change In Working Capital`
- `Change In Other Working Capital`
- `Change In Other Current Liabilities`
- `Change In Other Current Assets`
- `Change In Payables And Accrued Expense`
- `Change In Payable`
- `Change In Account Payable`
- `Change In Inventory`
- `Change In Receivables`
- `Changes In Account Receivables`
- `Other Non Cash Items`
- `Stock Based Compensation`
- `Deferred Tax`
- `Deferred Income Tax`
- `Depreciation Amortization Depletion`
- `Depreciation And Amortization`
- `Net Income From Continuing Operations`

**Fields used in the DCF engine (V1):**

- CFO candidates:
  - `Operating Cash Flow`
  - `Cash Flow From Continuing Operating Activities`
  - (fallback: `operatingCashflow` from `info`)
- Capex candidates:
  - `Capital Expenditure`
  - `Net PPE Purchase And Sale`
  - `Purchase Of PPE`

Then:

- `FCF_last_year ≈ Operating Cash Flow + Capital Expenditure`
  (Capex is typically negative → addition ≈ CFO − |Capex|)

---

## 4. Annual Income Statement (`yt.financials`)

Index (rows):

- `Tax Effect Of Unusual Items`
- `Tax Rate For Calcs`
- `Normalized EBITDA`
- `Net Income From Continuing Operation Net Minority Interest`
- `Reconciled Depreciation`
- `Reconciled Cost Of Revenue`
- `EBITDA`
- `EBIT`
- `Net Interest Income`
- `Interest Expense`
- `Interest Income`
- `Normalized Income`
- `Net Income From Continuing And Discontinued Operation`
- `Total Expenses`
- `Total Operating Income As Reported`
- `Diluted Average Shares`
- `Basic Average Shares`
- `Diluted EPS`
- `Basic EPS`
- `Diluted NI Availto Com Stockholders`
- `Net Income Common Stockholders`
- `Net Income`
- `Net Income Including Noncontrolling Interests`
- `Net Income Continuous Operations`
- `Tax Provision`
- `Pretax Income`
- `Other Income Expense`
- `Other Non Operating Income Expenses`
- `Net Non Operating Interest Income Expense`
- `Interest Expense Non Operating`
- `Interest Income Non Operating`
- `Operating Income`
- `Operating Expense`
- `Research And Development`
- `Selling General And Administration`
- `Gross Profit`
- `Cost Of Revenue`
- `Total Revenue`
- `Operating Revenue`

**Not used yet in DCF V1**, but useful later for:

- margins
- tax rate (`Tax Rate For Calcs`)
- EBIT/EBITDA-based models
- FCF bridge from EBIT

---

## 5. Quarterly Statements

Yahoo Finance also provides the quarterly versions of the three annual statements:

- `yt.quarterly_balance_sheet`
- `yt.quarterly_cashflow`
- `yt.quarterly_financials`

They contain *the same row labels* as the annual versions, but with **quarterly dates** as columns  
(e.g., `2025-09-30`, `2025-06-30`, `2025-03-31`, `2024-12-31`, …).

Use cases:

- rolling-window models  
- quarterly FCF reconstruction  
- seasonality analysis  
- detecting inflection points in margins, working capital, etc.

## 6. Price History (`yt.history` / `yf.download`)

Yahoo Finance provides daily OHLCV data.

Example columns (AAPL):

- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `Dividends`
- `Stock Splits`

Typical usage:

```python
hist = yf.download("AAPL", period="5y")
hist[["Close"]]
```

## 7. Summary of Fields Used in DCF Engine (V1)

The current DCF engine (version 1) relies only on core financial primitives that exist for nearly all large-cap companies on Yahoo Finance.

### From `.info`
* `regularMarketPrice` → current market price
* `sharesOutstanding` → number of shares
* `beta` → CAPM beta used for WACC
* `currency` → reporting currency (e.g., USD)

### From Annual Balance Sheet (`yt.balance_sheet`)
* `Total Debt`
* `Cash And Cash Equivalents`
    * *fallback* → `Cash`
* *Used to compute net debt and equity value.*

### From Annual Cashflow (`yt.cashflow`)
Free Cash Flow is approximated via:
1.  **Operating Cash Flow** (CFO)
2.  **Capital Expenditure** (Capex, usually negative)

**FCF formula (simple version):**
$$FCF = \text{Operating Cash Flow} + \text{Capital Expenditure}$$

> **Note:** These names must match exactly the Yahoo labels; this document exists to avoid typos like "Capital Expenditures" (wrong).

---

## 8. Why a Label Reference Matters

Yahoo Finance is not a formal API. Fields:
* change depending on ticker
* may appear or disappear
* differ between US/European tickers
* have inconsistent naming patterns (spacing, capitalization, abbreviations, slashes, plurals)

### Example pitfalls

| Correct Yahoo Label | Wrong label (common mistake) |
| :--- | :--- |
| `Operating Cash Flow` | `OperatingCashFlow` |
| `Capital Expenditure` | `Capital Expenditures` |
| `Total Debt` | `Total Debts` |
| `Cash And Cash Equivalents` | `Cash And Equivalents` |

Your provider must always use the **canonical names** shown in this document. And `_safe_get_first()` protects against missing rows or format inconsistencies.

---

## 9. Robustness Recommendations (for V2+)

To make future versions resistant to Yahoo quirks:

### Create alias lists

Example:

```python
CFO_KEYS = [
    "Operating Cash Flow",
    "Cash Flow From Continuing Operating Activities",
    "Cash Flow From Operating Activities",
]
```

Same for Capex:

```python
CAPEX_KEYS = [
    "Capital Expenditure",
    "Net PPE Purchase And Sale",
    "Purchase Of PPE",
]
```

### Add explicit fallback from .info

Use keys like operatingCashflow, totalDebt, and totalCash if the DataFrame lookup fails.

### Add warnings in logs when fields are missing

(you already do it for debt and cash).

### Test multiple tickers in CI

Test against Big Caps, Banks, Energy, EU stocks, Chinese ADRs, and ETFs to ensure stability.

## 10. Regenerating This Reference Automatically

If Yahoo changes something in the future, you can regenerate the entire dataset reference with:

```python
import yfinance as yf

yt = yf.Ticker("AAPL")

print("INFO:", sorted(yt.info.keys()))
print("BALANCE SHEET:", yt.balance_sheet.index.tolist())
print("CASHFLOW:", yt.cashflow.index.tolist())
print("FINANCIALS:", yt.financials.index.tolist())
print("HISTORY:", yt.history(period="1y").columns.tolist())
print("Q-BALANCE SHEET:", yt.quarterly_balance_sheet.index.tolist())
print("Q-CASHFLOW:", yt.quarterly_cashflow.index.tolist())
print("Q-FINANCIALS:", yt.quarterly_financials.index.tolist())
```

This keeps your reference document always aligned with Yahoo's backend.

## 11. Conclusion

This file now includes:

- all major Yahoo Finance field names, extracted directly from a real snapshot
- annual and quarterly balance sheet / cashflow / income statement rows
- price history fields
- detailed explanations of which fields your DCF engine uses
- best practices for avoiding naming errors
- robustness guidelines for future expansions (Monte Carlo, multi-segment, etc.)

It is now a complete and reliable reference for designing any data provider logic in your project.