# SBC Treatment - User Guide

## What is Stock-Based Compensation (SBC)?

Stock-Based Compensation (SBC) is when companies compensate employees with stock options, RSUs, or equity grants instead of (or in addition to) cash. This is especially common in tech companies.

### The Valuation Challenge

SBC creates two potential impacts on valuation:
1. **Dilution**: More shares are issued, reducing the per-share value
2. **Cash Flow**: SBC is a real economic cost that reduces available cash

The question is: **How should we account for SBC in our DCF valuation?**

## Two Treatment Methods

### Method 1: DILUTION (Traditional Approach)

**What it does:**
- Assumes SBC is already reflected in historical free cash flows
- Adjusts the final per-share value downward to account for future share dilution
- Formula: `Intrinsic Value per Share = (Equity Value / Shares) / (1 + dilution_rate)^years`

**When to use:**
- ✅ SBC is a small percentage of expenses (< 1-2%)
- ✅ Historical FCF already includes SBC as part of operating expenses
- ✅ You want to be consistent with traditional DCF methodology

**Example:**
- Company has $1B equity value, 100M shares
- Annual dilution rate: 2%
- Years: 5
- **Without SBC**: $10.00 per share
- **With DILUTION**: $10.00 / (1.02)^5 = $9.06 per share
- **Impact**: -9.4% reduction

### Method 2: EXPENSE (Conservative Approach)

**What it does:**
- Treats SBC as a real operating expense
- Subtracts the annual SBC amount from each year's projected cash flows
- Does NOT apply dilution adjustment (to avoid double counting)
- Formula: `FCF_adjusted = FCF_projected - SBC_annual_amount`

**When to use:**
- ✅ Tech companies with high SBC (> 5% of revenue)
- ✅ You want a more conservative valuation
- ✅ Historical FCF does NOT properly reflect SBC cost
- ✅ You're concerned about actual cash impact

**Example:**
- Same company, $1B base FCF
- Annual SBC expense: $50M
- Years: 5
- **Without SBC**: All flows unchanged
- **With EXPENSE**: Each flow reduced by $50M
- **Impact**: Larger reduction (present value of $50M × 5 years)

## How to Use in the App

### Step-by-Step Instructions

1. **Navigate to Step 5: Bridge de Valeur**
   - This is in the main expert input terminal
   - After defining your cost of capital and terminal value

2. **Find the SBC Section**
   - Look for: "**Traitement de la rémunération en actions (SBC)**"
   - You'll see two radio button options

3. **Choose Your Treatment Method**

   **Option A: Dilution**
   - Select: "Dilution (Ajustement du nombre d'actions)"
   - Input field appears: "Taux de dilution annuelle attendu (%)"
   - Enter the annual dilution rate (e.g., 2.0 for 2%)
   - This is the current/default behavior

   **Option B: Dépense**
   - Select: "Dépense Cash-flow (Charge réelle)"
   - ⚠️ Warning appears: "Mode DÉPENSE actif : L'ajustement de dilution final est désactivé..."
   - Input field appears: "Montant annuel estimé de la SBC (Millions)"
   - Enter annual SBC expense (e.g., 50 for $50M/year)

4. **Run the Valuation**
   - Click "Générer le Dossier de Valorisation"
   - The calculation automatically applies your chosen treatment
   - Check the Glass Box trace to see SBC impact

### Finding SBC Information

**Where to get SBC data:**
1. **Annual Report (10-K)**:
   - Look in "Consolidated Statements of Operations"
   - Line item: "Stock-based compensation" or "Share-based payments"
   - Usually broken out separately or in footnotes

2. **Cash Flow Statement**:
   - Under "Operating Activities"
   - "Stock-based compensation" is added back (non-cash expense)

3. **Financial Data Providers**:
   - Yahoo Finance: "Financials" → "Cash Flow" → "Stock Based Compensation"
   - Bloomberg Terminal: EQTY → Stock Compensation Expense
   - FactSet, CapIQ, etc.

**Example - Apple Inc. (2023)**:
- Revenue: ~$383B
- SBC: ~$11B
- SBC as % of Revenue: ~2.9%
- → Significant enough to consider EXPENSE treatment

## Comparing the Two Methods

### Quick Decision Matrix

| Company Type | SBC % of Revenue | Recommended Method | Why? |
|-------------|------------------|-------------------|------|
| Traditional Bank | < 1% | DILUTION | SBC is minimal |
| Mature Tech (Apple) | 2-3% | Either | Material but manageable |
| Growth Tech (Palantir) | > 10% | EXPENSE | SBC is a major cost |
| Startup (pre-IPO) | > 20% | EXPENSE | Cash flow impact is huge |

### Impact Comparison

For a company with:
- Current FCF: $1,000M
- Growth rate: 8%
- Years: 5
- WACC: 10%
- Shares: 100M

**Scenario 1: SBC = $30M/year (3% of FCF)**
- DILUTION method: ~$48.50/share
- EXPENSE method: ~$47.20/share
- Difference: -2.7%

**Scenario 2: SBC = $100M/year (10% of FCF)**
- DILUTION method: ~$48.50/share
- EXPENSE method: ~$43.80/share
- Difference: -9.7%

**Key Insight**: The higher the SBC relative to FCF, the bigger the difference between methods.

## Best Practices

### 1. Be Consistent
- Use the same method for peer comparisons
- Document which method you're using in your analysis

### 2. Validate Your Assumptions
- **DILUTION**: Check historical dilution rates (shares outstanding over time)
- **EXPENSE**: Verify SBC amount from financial statements

### 3. Sensitivity Analysis
- Run the valuation with both methods
- Understand the range of potential intrinsic values
- Use this to inform your margin of safety

### 4. Consider the Context
- **Mature companies**: DILUTION is usually fine
- **High-growth tech**: EXPENSE is more conservative
- **When in doubt**: Use EXPENSE (more conservative)

### 5. Watch for Red Flags
- ⚠️ SBC > 5% of revenue: Requires careful consideration
- ⚠️ Rapidly increasing SBC: May indicate unsustainable growth
- ⚠️ SBC >> Net Income: Company may be "spending" equity value

## Frequently Asked Questions

**Q: Which method is "correct"?**
A: Both are valid. DILUTION is traditional, EXPENSE is more conservative. Choose based on your analysis goals and company characteristics.

**Q: Can I use both?**
A: No - that would be double counting. The app prevents this by disabling dilution when EXPENSE mode is active.

**Q: What if I don't know the SBC amount?**
A: Check the company's cash flow statement or annual report. Most public companies disclose this clearly.

**Q: Should I always use EXPENSE for tech stocks?**
A: Not always. Mature tech companies (Apple, Microsoft) with moderate SBC (2-3%) can use either. High-growth companies with SBC > 5% should use EXPENSE.

**Q: Does SBC affect the Glass Box trace?**
A: Yes! When using EXPENSE mode, you'll see "SBC" as a variable in the calculation steps showing the deduction amount.

**Q: What's the default behavior?**
A: DILUTION - this maintains backward compatibility with previous valuations.

## Summary

The SBC treatment option gives you control over how to model one of the most significant expenses in modern companies, especially in technology. By understanding both methods and their implications, you can create more accurate and defensible valuations.

**Remember:**
- 🟢 **DILUTION**: Traditional, assumes SBC in historical FCF
- 🔴 **EXPENSE**: Conservative, treats SBC as real cash cost
- ⚠️ **Never double count**: The app prevents this automatically

Choose the method that best fits your company, industry, and analysis goals.
