# CHANGELOG

All notable changes to the Intrinsic Value Pricer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - Golden Rule of Terminal Value
- **Golden Rule Implementation**: Normalization of terminal flow to ensure consistency between perpetual growth and required reinvestment based on stable-state ROIC
  - `normalize_terminal_flow_for_stable_state()` function in `src/computation/financial_math.py`
  - Calculates normative reinvestment rate: `Reinvestment = gn / ROICstable`
  - Adjusts terminal flow: `FCF_adjusted = FCF_n × (1 - reinvestment_rate)`
  - Includes comprehensive NumPy-style docstrings
  - Prevents division by zero with conservative fallback when ROIC is None, zero, or negative

- **DCF Library Integration**: Enhanced `compute_terminal_value()` in `src/valuation/library/dcf.py`
  - Applies Golden Rule normalization before Gordon-Shapiro formula
  - Adds detailed calculation steps showing reinvestment adjustment
  - Maintains full backward compatibility (roic_stable=None preserves existing behavior)
  - Enriched calculation proof with Golden Rule variables and explanations

- **Parameter Model Updates**:
  - Added `roic_stable` field to `TerminalValueParameters` (optional, default=None)
  - Added `ROIC_STABLE` UI key to constants
  - No breaking changes to existing Pydantic types

- **Internationalization (i18n)**:
  - French translation strings in `src/i18n/fr/ui/terminals.py`
  - Input label: `INP_ROIC_STABLE` - "ROIC en État Stable (%)"
  - Help text: `HELP_ROIC_STABLE` explaining the Golden Rule concept
  - Golden Rule section with explanatory texts for calculation proofs:
    - `GOLDEN_RULE_TITLE`, `GOLDEN_RULE_EXPLANATION`
    - `GOLDEN_RULE_FORMULA_SHORT`, `GOLDEN_RULE_DETAIL`
    - `GOLDEN_RULE_NOT_APPLIED`

- **Comprehensive Testing**:
  - 12 unit tests for `normalize_terminal_flow_for_stable_state()` covering:
    - Normal cases with various growth/ROIC combinations
    - Edge cases: zero growth, negative growth, None/zero/negative ROIC
    - Boundary conditions: growth equals ROIC, growth exceeds ROIC
  - 5 integration tests for DCF library:
    - Terminal value calculation with/without Golden Rule
    - Zero ROIC handling, high ROIC scenarios
    - Full workflow integration test
  - All 113 existing tests pass without regressions

### Technical Details
The Golden Rule addresses a fundamental valuation principle: **perpetual growth requires proportional reinvestment**. Without this adjustment, DCF models implicitly assume companies can grow indefinitely without reinvesting capital, which violates economic principles. This implementation:

1. **Mathematically rigorous**: Calculates exact reinvestment requirements based on ROIC
2. **Conservative by default**: No adjustment when ROIC data is unavailable
3. **Division-by-zero safe**: Explicit guards against invalid ROIC values
4. **Audit-friendly**: Full traceability in calculation proofs with detailed variables
5. **Backward compatible**: Existing models continue to work unchanged

This enhancement aligns the codebase with institutional best practices from Damodaran and McKinsey frameworks for terminal value estimation.

---

## [1.0.0] - 2026-02-11

### Sprint Overview: Production-Ready Release

This release marks the first production-ready version of the Intrinsic Value Pricer, 
featuring comprehensive valuation methodologies, institutional-grade architecture, 
and complete CI/CD pipeline integration.

---

## PR5: CI/CD & Streamlit Cloud Deploy

### Added
- **GitHub Actions CI/CD Pipeline**: Complete automated workflow with ruff → mypy → pytest (95% coverage) → pip-audit
- **GitHub Templates**: Pull Request template and CODEOWNERS file (@clement-bbier)
- **Python Version Management**: `.python-version` file specifying Python 3.12
- **Dependency Management**: Fully pinned dependencies in `pyproject.toml` and `requirements.txt`
  - `numpy==1.26.4`, `pandas==2.3.3`, `streamlit==1.54.0`, etc.
- **Streamlit Configuration**: Institutional theme with professional color palette
- **Application Footer**: Version display (v1.0.0) with CI badge and coverage indicator

### Changed
- **pytest.ini**: Added `--cov-fail-under=95` to enforce 95% test coverage threshold
- **CI Workflow**: Removed `continue-on-error` from mypy to enforce type safety
- **Coverage Upload**: Changed from Python 3.11 to 3.12 for coverage reporting

---

## PR6: Documentation & Polish

### Added
- **CHANGELOG.md**: Complete sprint history and PR summary
- **Version Management**: `__version__ = "1.0.0"` in `src/__init__.py`
- **Academic References**: Documentation includes citations from:
  - Damodaran, A. (2012). *Investment Valuation*
  - McKinsey & Company (2020). *Valuation: Measuring and Managing the Value of Companies*
  - Ohlson, J. (1995). *Earnings, Book Values, and Dividends in Equity Valuation*
  - Graham, B. & Dodd, D. (1974). *Security Analysis*
  - Hamada, R. (1972). *The Effect of the Firm's Capital Structure on the Systematic Risk of Common Stocks*

### Changed
- **README.md**: Restructured with Architecture → Models → Formulas → Install → References
- **Documentation Structure**: Enhanced methodology documentation with formula alignment
- **Architecture Documentation**: Complete flow and structure diagrams

---

## Core Features (Pre-Release Development)

### Valuation Methods Implemented
1. **DCF Models (5 variants)**
   - FCFF Standard: For mature companies with stable cash flows
   - FCFF Fundamental: Normalized flows for cyclical businesses
   - FCFF Growth: Margin convergence for growth companies
   - FCFE: Direct equity valuation
   - DDM: Dividend Discount Model

2. **Residual Income Model (RIM)**
   - Bank and insurance company valuation
   - Book value-based approach

3. **Benjamin Graham Formula**
   - Rapid screening methodology
   - Conservative value estimation

4. **Market Multiples**
   - Sector-based relative valuation
   - Peer comparison analysis

5. **Monte Carlo Simulation**
   - Probabilistic risk analysis
   - Distribution-based valuation ranges

### Architecture Principles
- **Strict Separation**: `app/` (UI layer) completely independent from `src/` (quantitative core)
- **Dependency Injection**: Centralized configuration registry
- **Contract Testing**: Systematic interface validation
- **Glass Box Transparency**: Full traceability of calculations and assumptions

### Quality Assurance
- **Test Coverage**: 72%+ (target: 95%+)
- **Linting**: Ruff with institutional code standards
- **Type Safety**: mypy strict type checking
- **Security**: pip-audit for vulnerability scanning

### Infrastructure
- **Data Providers**: Yahoo Finance integration with automatic fallback
- **Auditing System**: Systematic quality assessment of data and assumptions
- **Reference Data**: Country risk matrices and sector multiples
- **Internationalization**: Full French support (English forthcoming)

---

## Known Limitations

### Coverage Gap
- Current test coverage: ~72%
- Target coverage: 95%
- Gap primarily in UI layer (`app/`) and some infrastructure modules
- Core valuation logic (`src/valuation/`) has excellent coverage (95%+)

### Future Enhancements
- Expand test coverage for UI components
- Add English language support
- Implement additional data providers
- Enhanced backtesting capabilities

---

## Breaking Changes

None. This is the initial 1.0.0 release.

---

## Migration Guide

Not applicable for initial release.

---

## Contributors

- **@clement-bbier**: Project maintainer and lead developer

---

## References

### Academic Sources
1. Damodaran, A. (2012). *Investment Valuation: Tools and Techniques for Determining the Value of Any Asset*. 3rd Edition. Wiley Finance.

2. McKinsey & Company, Koller, T., Goedhart, M., & Wessels, D. (2020). *Valuation: Measuring and Managing the Value of Companies*. 7th Edition. Wiley.

3. Ohlson, J. A. (1995). *Earnings, Book Values, and Dividends in Equity Valuation*. Contemporary Accounting Research, 11(2), 661-687.

4. Graham, B., & Dodd, D. (1974). *Security Analysis: Principles and Technique*. 4th Edition. McGraw-Hill.

5. Hamada, R. S. (1972). *The Effect of the Firm's Capital Structure on the Systematic Risk of Common Stocks*. The Journal of Finance, 27(2), 435-452.

### Industry Standards
- CFA Institute: *Equity Asset Valuation* (2015)
- IASB: International Financial Reporting Standards
- French AMF: Market best practices for financial analysis

---

[Unreleased]: https://github.com/clement-bbier/intrinsec-value-pricer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/clement-bbier/intrinsec-value-pricer/releases/tag/v1.0.0
