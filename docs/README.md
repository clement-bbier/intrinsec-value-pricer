# Documentation — Intrinsic Value Pricer

**Version** : 4.0 — February 2026
**Architecture** : SSOT (Single Source of Truth) with UIKeys Registry
**Branch** : `ui` — Production-Ready

This documentation is the **financial, technical, and user reference**
for the *Intrinsic Value Pricer* project.

It is designed to enable:
- **understanding** of valuation methodologies,
- **verification** of calculations and assumptions,
- **learning** the underlying financial logic,
- **traceability** via the Glass Box system.

The documentation is strictly aligned with:
- the computation engine (`src/valuation/`),
- the user interface (`app/views/`),
- the SSOT architecture via UIKeys metadata (`src/config/constants.py`),
- the **Glass Box** transparency principles.

---

## Project Architecture

```
intrinsec-value-pricer/
├── src/                       # Pure business logic (Zero Streamlit)
│   ├── models/                # Pydantic V2 models with UIKey annotations
│   │   └── parameters/        # Input metadata (UIKey → session state binding)
│   ├── valuation/             # Calculation engine (7 strategies)
│   ├── computation/           # Mathematical functions
│   ├── config/constants.py    # UIKeys registry (SSOT for all session keys)
│   ├── i18n/                  # Internationalization (FR classes)
│   └── core/                  # Formatting, exceptions, logging
│
├── app/                       # Presentation layer (Streamlit)
│   ├── controllers/           # InputFactory (UI → Backend bridge)
│   ├── views/inputs/          # Expert terminals (7 strategies + shared widgets)
│   ├── views/results/         # Orchestrator + 5 Pillar views
│   ├── views/components/      # Reusable UI atoms (charts, KPIs)
│   ├── assets/                # CSS Design System (Institutional theme)
│   └── state/                 # Session state management
│
├── infra/                     # External infrastructure
│   ├── data_providers/        # Yahoo Finance + Fallback
│   └── ref_data/              # Sectoral multiples
│
└── tests/                     # Contract, unit, integration tests
```

---

## Key Architecture: SSOT via UIKeys

The `UIKeys` registry in `src/config/constants.py` serves as the **Single Source
of Truth** for all UI-to-backend bindings:

1. **Widget** (`app/views/inputs/`) renders a `st.number_input` with `key=UIKeys.XXX`
2. **InputFactory** (`app/controllers/`) introspects Pydantic models for `UIKey` metadata
3. **Ghost Pattern**: `None` / `0` values are excluded — backend uses Provider data instead
4. **Model** (`src/models/parameters/`) uses `Annotated[float, UIKey(UIKeys.RF, scale="pct")]`

---

## How to navigate the documentation

The documentation is organized in distinct layers:

### Methodology (`docs/methodology/`)
- Financial theory (DCF, RIM, Graham)
- 7 documented valuation methods
- LaTeX formulas and usage limits
- Monte Carlo extension

### Technical (`docs/technical/`)
- Layered architecture with strict boundaries
- Design Patterns (Factory, Template, Mediator)
- Glass Box with source traceability
- Degraded Mode and resilience

### Usage (`docs/usage/`)
- AUTO mode (normative assumptions)
- EXPERT mode (full control, 7 terminals)
- Results interpretation

### References (`docs/references/`)
- Yahoo Finance (data and limitations)
- Damodaran (sectoral multiples)
- Macro-financial assumptions

---

## Key Features

| Feature | Description |
|---------|-------------|
| **SSOT UIKeys** | Single registry for all UI-backend bindings |
| **Ghost Pattern** | Neutral values (None/0) defer to Provider data |
| **Glass Box** | Complete traceability with source badges |
| **Degraded Mode** | Automatic fallback on sectoral multiples |
| **InputFactory** | Metadata-driven UI → Pydantic model bridge |
| **5 Result Pillars** | Configuration, Proof, Benchmark, Risk, Market |

---

## Key Principles

1. **Architectural Isolation**
   `src/` never depends on `app/` or Streamlit.

2. **Strict Typing**
   `from __future__ import annotations` in all files.

3. **Glass Box**
   Every displayed value is traceable to its source.

4. **Resilience**
   No API failure blocks the valuation (sectoral fallback).

---

## Recommended entry points

| Profile | Document |
|---------|----------|
| New user | `usage/README.md` |
| Financial analyst | `methodology/README.md` |
| Developer | `technical/README.md` |
| Contributor | `../CONTRIBUTING.md` |
