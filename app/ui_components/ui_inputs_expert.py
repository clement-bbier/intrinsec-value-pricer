"""
app/ui_components/ui_inputs_expert.py
ARCHITECTURE SEGMENTÉE — TERMINAL PROFESSIONNEL RÉACTIF (V6.3)
Souveraineté totale : Formules LaTeX, Réactivité Monte Carlo et Clarté Décimale.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod
)

# ==============================================================================
# 0. RÉFÉRENTIEL DES NOMS UNIFIÉS ET HELPER DE SÉCURITÉ
# ==============================================================================

VALUATION_DISPLAY_NAMES = {
    ValuationMode.FCFF_TWO_STAGE: "FCFF Standard",
    ValuationMode.FCFF_NORMALIZED: "FCFF Fundamental",
    ValuationMode.FCFF_REVENUE_DRIVEN: "FCFF Growth",
    ValuationMode.RESIDUAL_INCOME_MODEL: "RIM",
    ValuationMode.GRAHAM_1974_REVISED: "Graham"
}

def safe_factory_params(all_data: Dict[str, Any]) -> DCFParameters:
    """Filtre uniquement les champs reconnus par le modèle DCFParameters."""
    # Liste stricte des champs attendus par le moteur core/models.py
    allowed = {
        "risk_free_rate", "market_risk_premium", "corporate_aaa_yield",
        "tax_rate", "cost_of_debt", "fcf_growth_rate", "target_fcf_margin",
        "perpetual_growth_rate", "exit_multiple_value", "projection_years",
        "manual_beta", "manual_total_debt", "manual_cash",
        "manual_shares_outstanding", "manual_book_value", "manual_fcf_base",
        "enable_monte_carlo", "num_simulations", "beta_volatility",
        "growth_volatility", "terminal_growth_volatility"
    }
    # On ne garde que ce qui est autorisé et différent de 0 (pour l'Auto Yahoo)
    clean_data = {k: v for k, v in all_data.items() if k in allowed and v != 0 and v is not None}
    return DCFParameters(**clean_data)

# ==============================================================================
# 1. LES ATOMES PROFESSIONNELS (STANDARD DÉCIMAL CLAIR)
# ==============================================================================

def atom_macro_rates_pro():
    c1, c2 = st.columns(2)
    rf = c1.number_input("Taux sans risque $R_f$ (décimal, ex: 0.042 pour 4.2%)", 0.0, 0.20, 0.042, 0.001, format="%.3f")
    mrp = c2.number_input("Prime de risque marché $MRP$ (décimal, ex: 0.055 pour 5.5%)", 0.0, 0.20, 0.055, 0.001, format="%.3f")
    return {"risk_free_rate": rf, "market_risk_premium": mrp}

def atom_beta_control_pro():
    beta = st.number_input("Coefficient Beta $\\beta$ (ex: 1.10)", 0.0, 5.0, 1.0, 0.05,
                           help="Mesure de volatilité relative. Saisir 0.0 pour utiliser le calcul automatique.")
    return {"manual_beta": beta}

def atom_tax_and_debt_pro(mode: ValuationMode):
    c1, c2 = st.columns(2)
    tax = c1.number_input("Taux d'imposition effectif (décimal, ex: 0.25 pour 25%)", 0.0, 0.60, 0.25, 0.01, format="%.2f")
    if mode == ValuationMode.GRAHAM_1974_REVISED:
        yield_aaa = c2.number_input("Rendement Obligations AAA $Y$ (décimal, ex: 0.045 pour 4.5%)", 0.0, 0.20, 0.045, 0.001, format="%.3f")
        return {"tax_rate": tax, "corporate_aaa_yield": yield_aaa}
    else:
        kd = c2.number_input("Coût de la dette brut $K_d$ (décimal, ex: 0.05 pour 5%)", 0.0, 0.20, 0.05, 0.001, format="%.3f")
        return {"tax_rate": tax, "cost_of_debt": kd}


def atom_terminal_strategy_pro():
    """Phase 4 : Choix de la méthode de sortie avec formules dynamiques affichées en amont."""

    # Affichage des formules de référence dès le début de la section
    st.latex(
        r"TV_{Gordon} = \frac{FCF_n \times (1 + g_n)}{WACC - g_n} \quad | \quad TV_{Exit} = FCF_n \times \text{Multiple}")

    method = st.radio(
        "Sélection du modèle de sortie",
        options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
        format_func=lambda
            x: "Croissance Perpétuelle (Gordon)" if x == TerminalValueMethod.GORDON_GROWTH else "Multiple de Sortie",
        horizontal=True
    )

    c1, _ = st.columns(2)

    if method == TerminalValueMethod.GORDON_GROWTH:
        gn = c1.number_input(
            "Taux de croissance à l'infini gn (décimal, ex: 0.02 pour 2%)",
            0.0, 0.05, 0.02, 0.001, format="%.3f"
        )
        return {"terminal_method": method, "perpetual_growth_rate": gn, "exit_multiple_value": 0.0}
    else:
        exit_m = c1.number_input(
            "Multiple de sortie (facteur x, ex: 12.0)",
            1.0, 50.0, 12.0, 0.5
        )
        return {"terminal_method": method, "exit_multiple_value": exit_m, "perpetual_growth_rate": 0.0}

def atom_equity_bridge_pro():
    st.caption("Ajustements Bilanciels (Unités monétaires en $, 0 = Auto)")
    c1, c2, c3 = st.columns(3)
    debt = c1.number_input("Dette Totale ($)", value=0.0, step=1e6, format="%.0f")
    cash = c2.number_input("Trésorerie ($)", value=0.0, step=1e6, format="%.0f")
    shares = c3.number_input("Actions (#)", value=0.0, step=1e5, format="%.0f")
    return {"manual_total_debt": debt, "manual_cash": cash, "manual_shares_outstanding": shares}

def atom_monte_carlo_pro():
    """Phase 6 : Simulation Probabiliste avec distinctions claires sur les volatilités."""
    st.markdown("#### 6. Simulation Probabiliste (Analyse d'Incertitude)")
    enable = st.toggle("Activer Monte Carlo", value=False)
    if enable:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            sims = c1.select_slider("Nombre d'itérations (entier)", options=[1000, 5000, 10000, 20000], value=5000)
            st.caption("Calibration des Volatilités (Décimales, ex: 0.02 pour 2%) :")
            v1, v2, v3 = st.columns(3)
            # Volatilité sur le Beta (Phase 3)
            vb = v1.number_input("Vol. β", 0.0, 1.0, 0.10, 0.01, format="%.3f")
            # Volatilité sur la croissance explicite g (Phase 2)
            vg = v2.number_input("Vol. g", 0.0, 0.20, 0.02, 0.005, format="%.3f")
            # Volatilité sur la croissance terminale gn (Phase 4)
            vgn = v3.number_input("Vol. gn", 0.0, 0.05, 0.005, 0.001, format="%.3f")
            return {
                "enable_monte_carlo": True,
                "num_simulations": sims,
                "beta_volatility": vb,
                "growth_volatility": vg,
                "terminal_growth_volatility": vgn
            }
    return {"enable_monte_carlo": False}

# ==============================================================================
# 2. FACTORY
# ==============================================================================

def factory_pydantic_params(raw_data: Dict[str, Any]) -> DCFParameters:
    processed = raw_data.copy()
    sovereign_fields = ["manual_total_debt", "manual_cash", "manual_shares_outstanding", "manual_fcf_base", "manual_book_value", "manual_beta"]
    for field in sovereign_fields:
        if processed.get(field) == 0:
            processed[field] = None
    return DCFParameters(**processed)

# ==============================================================================
# 3. TERMINAUX EXPERTS (VUES RÉACTIVES)
# ==============================================================================

def render_expert_fcff_standard(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : Discounted Cash Flow - FCFF Standard."""
    st.subheader(f"⚙️ Terminal Expert : FCFF Standard")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    devise = "devise de l'entreprise"

    # --- 1. FLUX DE BASE ---
    st.markdown("#### 1. Flux de trésorerie de base (FCF₀)")
    fcf_base = st.number_input(
        f"Dernier flux de trésorerie disponible (TTM en {devise}, 0 = Auto Yahoo)",
        value=0.0, format="%.0f"
    )
    st.divider()

    # --- 2. CROISSANCE ---
    st.markdown(f"#### 2. Phase de croissance explicite (t années)")
    st.latex(r"FCF_t = FCF_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années de projection (t)", 3, 15, 5)
    g_rate = c2.number_input(
        "Croissance moyenne attendue annualisée g (décimal, ex: 0.05 pour 5%)",
        -0.50, 1.0, 0.05, 0.005, format="%.3f"
    )
    st.divider()

    # --- 3. WACC ---
    st.markdown("#### 3. Coût Moyen Pondéré du Capital (WACC)")
    st.latex(r"k_e = R_f + \beta \times MRP \quad | \quad WACC = w_e k_e + w_d k_d (1 - \tau)")

    # Surcharge du prix pour déterminer l'Equity (E) dans les poids we/wd
    manual_price = st.number_input(
        "Prix de l'action (0 = Auto YahooFinance)",
        0.0, 10000.0, 0.0, 0.01, format="%.2f"
    )

    col_a, col_b = st.columns(2)
    # Ordre rigoureux : Rf -> Beta -> MRP -> kd -> tau
    rf = col_a.number_input("Taux sans risque Rf (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.04, 0.001, format="%.3f")
    beta = col_b.number_input("Coefficient Beta β (facteur x, 0 = Auto Yahoo)", 0.0, 5.0, 1.1, 0.05, format="%.2f")

    mrp = col_a.number_input("Prime de risque marché MRP (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.055, 0.001,
                             format="%.3f")
    kd = col_b.number_input("Coût de la dette brut kd (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.05, 0.001, format="%.3f")

    tau = col_a.number_input("Taux d'imposition effectif τ (décimal, 0 = Auto Yahoo)", 0.0, 0.60, 0.25, 0.01,
                             format="%.2f")
    st.divider()

    # --- 4. SORTIE ---
    st.markdown("#### 4. Valeur de continuation (Sortie)")
    terminal_data = atom_terminal_strategy_pro()
    st.divider()

    # --- 5. BRIDGE ---
    st.markdown("#### 5. Ajustements de structure (Equity Bridge)")
    st.latex(r"P = \frac{\text{Enterprise Value} - \text{Dette} + \text{Trésorerie}}{\text{Actions}}")

    c1, c2, c3 = st.columns(3)
    debt = c1.number_input("Dette Totale (0 = Auto Yahoo)", value=0.0, step=1e6, format="%.0f")
    cash = c2.number_input("Trésorerie (0 = Auto Yahoo)", value=0.0, step=1e6, format="%.0f")
    shares = c3.number_input("Actions en circulation (entier, 0 = Auto Yahoo)", value=0.0, step=1e5, format="%.0f")
    st.divider()

    # --- 6. MONTE CARLO ---
    mc_data = atom_monte_carlo_pro()

    if st.button(f"Établir la valorisation {ticker}", type="primary", use_container_width=True):
        bridge_data = {"manual_total_debt": debt, "manual_cash": cash, "manual_shares_outstanding": shares}

        # Collecte de toutes les données saisies
        all_data = {
            "manual_fcf_base": fcf_base,
            "projection_years": n_years,
            "fcf_growth_rate": g_rate,
            "risk_free_rate": rf,
            "manual_beta": beta,
            "market_risk_premium": mrp,
            "cost_of_debt": kd,
            "tax_rate": tau,
            "manual_stock_price": manual_price if manual_price > 0 else None,
            **terminal_data,
            **bridge_data,
            **mc_data
        }

        # Utilisation du helper pour filtrer avant d'envoyer à DCFParameters
        return ValuationRequest(
            ticker=ticker,
            projection_years=n_years,
            mode=ValuationMode.FCFF_TWO_STAGE,
            input_source=InputSource.MANUAL,
            manual_params=safe_factory_params(all_data)
        )
    return None

def render_expert_fcff_fundamental(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFF Fundamental (Flux normalisés de cycle)."""
    st.subheader(f"⚙️ Terminal Expert : FCFF Fundamental")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{FCF_{normalisé} \times (1+g)^t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    devise = "devise de l'entreprise"

    # --- 1. FLUX NORMALISÉ ---
    st.markdown("#### 1. Flux normalisé de base (FCF_normalisé)")
    fcf_base = st.number_input(
        f"Flux lissé de cycle FCF_normalisé (TTM en {devise}, 0 = Auto Yahoo)",
        value=0.0, format="%.0f"
    )
    st.divider()

    # --- 2. CROISSANCE DE CYCLE ---
    st.markdown("#### 2. Croissance moyenne de cycle (t années)")
    st.latex(r"FCF_t = FCF_{normalisé} \times (1+g)^t")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années du cycle (t)", 3, 15, 5)
    g_rate = c2.number_input(
        "Croissance moyenne attendue g (décimal, 0 = Auto Yahoo)",
        -0.20, 0.30, 0.03, 0.005, format="%.3f"
    )
    st.divider()

    # --- 3. WACC ---
    st.markdown("#### 3. Coût Moyen Pondéré du Capital (WACC)")
    st.latex(r"k_e = R_f + \beta \times MRP \quad | \quad WACC = w_e k_e + w_d k_d (1 - \tau)")

    manual_price = st.number_input(
        "Prix de l'action pour calcul des poids we/wd (0 = Auto Yahoo)",
        0.0, 10000.0, 0.0, 0.01, format="%.2f"
    )

    col_a, col_b = st.columns(2)
    rf = col_a.number_input("Taux sans risque Rf (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.04, 0.001, format="%.3f")
    beta = col_b.number_input("Coefficient Beta β (facteur x, 0 = Auto Yahoo)", 0.0, 5.0, 1.1, 0.05, format="%.2f")
    mrp = col_a.number_input("Prime de risque marché MRP (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.055, 0.001,
                             format="%.3f")
    kd = col_b.number_input("Coût de la dette brut kd (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.05, 0.001, format="%.3f")
    tau = col_a.number_input("Taux d'imposition effectif τ (décimal, 0 = Auto Yahoo)", 0.0, 0.60, 0.25, 0.01,
                             format="%.2f")
    st.divider()

    # --- 4. SORTIE & 5. BRIDGE ---
    st.markdown("#### 4. Valeur de continuation (Sortie)");
    terminal_data = atom_terminal_strategy_pro();
    st.divider()
    st.markdown("#### 5. Ajustements de structure (Equity Bridge)");
    bridge_data = atom_equity_bridge_pro();
    st.divider()
    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation Fondamentale ({ticker})", type="primary", use_container_width=True):
        all_data = {
            "manual_fcf_base": fcf_base, "projection_years": n_years, "fcf_growth_rate": g_rate,
            "risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "cost_of_debt": kd, "tax_rate": tau,
            "manual_stock_price": manual_price if manual_price > 0 else None,
            **terminal_data, **bridge_data, **mc_data
        }
        return ValuationRequest(
            ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_NORMALIZED,
            input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data)
        )
    return None


def render_expert_fcff_growth(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : FCFF Growth (Convergence des marges)."""
    st.subheader(f"⚙️ Terminal Expert : FCFF Growth")
    st.latex(r"V_0 = \sum_{t=1}^{n} \frac{Rev_0(1+g_{rev})^t \times Margin_t}{(1+WACC)^t} + \frac{TV_n}{(1+WACC)^n}")

    devise = "devise de l'entreprise"

    # --- 1. CHIFFRE D'AFFAIRES ---
    st.markdown("#### 1. Chiffre d'Affaires de base (Rev₀)")
    rev_base = st.number_input(f"Chiffre d'affaires TTM Rev₀ (en {devise}, 0 = Auto Yahoo)", value=0.0, format="%.0f")
    st.divider()

    # --- 2. CONVERGENCE DES MARGES ---
    st.markdown("#### 2. Horizon & Convergence des Marges (Marginₜ)")
    st.latex(r"Margin_t = \text{Marge progressive vers la cible}")
    c1, c2, c3 = st.columns(3)
    n_years = c1.slider("Années de projection (t)", 3, 15, 5)
    g_rev = c2.number_input("Croissance CA attendue g_rev (décimal, 0 = Auto Yahoo)", 0.0, 1.0, 0.15, 0.005,
                            format="%.3f")
    m_target = c3.number_input("Marge FCF cible Marginₜ (décimal, 0 = Auto Yahoo)", 0.0, 0.80, 0.20, 0.01,
                               format="%.2f")
    st.divider()

    # --- 3. WACC ---
    st.markdown("#### 3. Coût Moyen Pondéré du Capital (WACC)")
    # Double formule simultanée pour la clarté CAPM + WACC
    st.latex(r"k_e = R_f + \beta \times MRP \quad | \quad WACC = w_e k_e + w_d k_d (1 - \tau)")

    manual_price = st.number_input("Prix de l'action pour calcul des poids we/wd (0 = Auto Yahoo)", 0.0, 10000.0, 0.0,
                                   0.01, format="%.2f")

    col_a, col_b = st.columns(2)
    rf = col_a.number_input("Taux sans risque Rf (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.04, 0.001, format="%.3f")
    beta = col_b.number_input("Coefficient Beta β (facteur x, 0 = Auto Yahoo)", 0.0, 5.0, 1.1, 0.05, format="%.2f")
    mrp = col_a.number_input("Prime de risque marché MRP (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.055, 0.001,
                             format="%.3f")
    kd = col_b.number_input("Coût de la dette brut kd (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.05, 0.001, format="%.3f")
    tau = col_a.number_input("Taux d'imposition effectif τ (décimal, 0 = Auto Yahoo)", 0.0, 0.60, 0.25, 0.01,
                             format="%.2f")
    st.divider()

    # --- 4. SORTIE ---
    st.markdown("#### 4. Valeur de continuation (Sortie)")
    terminal_data = atom_terminal_strategy_pro()
    st.divider()

    # --- 5. BRIDGE ---
    st.markdown("#### 5. Ajustements de structure (Equity Bridge)")
    st.latex(r"P = \frac{\text{Enterprise Value} - \text{Dette} + \text{Trésorerie}}{\text{Actions}}")
    bridge_data = atom_equity_bridge_pro()
    st.divider()

    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation Growth ({ticker})", type="primary", use_container_width=True):
        all_data = {
            "manual_fcf_base": rev_base, "projection_years": n_years,
            "fcf_growth_rate": g_rev, "target_fcf_margin": m_target,
            "manual_stock_price": manual_price if manual_price > 0 else None,
            "risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp, "cost_of_debt": kd, "tax_rate": tau,
            **terminal_data, **bridge_data, **mc_data
        }
        return ValuationRequest(
            ticker=ticker, projection_years=n_years, mode=ValuationMode.FCFF_REVENUE_DRIVEN,
            input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data)
        )
    return None

def render_expert_rim(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : RIM (Modèle Actif Net/Profits)."""
    st.subheader(f"⚙️ Terminal Expert : RIM")
    st.latex(r"V_0 = BV_0 + \sum_{t=1}^{n} \frac{NI_t - (k_e \times BV_{t-1})}{(1+k_e)^t} + \frac{TV_{RI}}{(1+k_e)^n}")

    devise = "devise locale"

    # --- 1. VALEUR COMPTABLE & PROFITS ---
    st.markdown("#### 1. Valeur Comptable (BV₀) & Profits (NIₜ)")
    c1, c2 = st.columns(2)
    bv = c1.number_input(f"Valeur comptable initiale BV₀ (en {devise}, 0 = Auto Yahoo)", value=0.0, format="%.0f")
    ni = c2.number_input(f"Résultat Net TTM NIₜ (en {devise}, 0 = Auto Yahoo)", value=0.0, format="%.0f")
    st.divider()

    # --- 2. CROISSANCE ---
    st.markdown("#### 2. Horizon & Croissance des profits (g)")
    st.latex(r"NI_t = NI_{t-1} \times (1 + g)")
    c1, c2 = st.columns(2)
    n_years = c1.slider("Années de projection (t)", 3, 15, 5)
    g_ni = c2.number_input("Croissance moyenne attendue g (décimal, 0 = Auto Yahoo)", 0.0, 0.50, 0.05, 0.005,
                           format="%.3f")
    st.divider()

    # --- 3. COÛT DES FONDS PROPRES (ke) ---
    st.markdown("#### 3. Coût des Fonds Propres (ke)")
    st.latex(r"k_e = R_f + \beta \times MRP")

    col_a, col_b = st.columns(2)
    rf = col_a.number_input("Taux sans risque Rf (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.04, 0.001, format="%.3f")
    beta = col_b.number_input("Coefficient Beta β (facteur x, 0 = Auto Yahoo)", 0.0, 5.0, 1.0, 0.05, format="%.2f")
    mrp = col_a.number_input("Prime de risque marché MRP (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.055, 0.001,
                             format="%.3f")
    st.divider()

    # --- 4. SORTIE & 5. BRIDGE ---
    st.markdown("#### 4. Valeur de continuation");
    terminal_data = atom_terminal_strategy_pro();
    st.divider()
    st.markdown("#### 5. Passage à la Valeur Actionnaire (Bridge)");
    bridge_data = atom_equity_bridge_pro();
    st.divider()
    mc_data = atom_monte_carlo_pro()

    if st.button(f"Lancer la valorisation RIM ({ticker})", type="primary", use_container_width=True):
        all_data = {
            "manual_book_value": bv, "manual_fcf_base": ni, "projection_years": n_years, "fcf_growth_rate": g_ni,
            "risk_free_rate": rf, "manual_beta": beta, "market_risk_premium": mrp,
            **terminal_data, **bridge_data, **mc_data
        }
        return ValuationRequest(
            ticker=ticker, projection_years=n_years, mode=ValuationMode.RESIDUAL_INCOME_MODEL,
            input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data)
        )
    return None

def render_expert_graham(ticker: str) -> Optional[ValuationRequest]:
    """Terminal Expert : Modèle de Graham (Value)."""
    st.subheader(f"⚙️ Terminal Expert : Graham")
    st.latex(r"V_0 = \frac{EPS \times (8.5 + 2g) \times 4.4}{Y}")

    devise = "devise de l'entreprise"

    # --- 1. CAPACITÉ BÉNÉFICIAIRE ---
    st.markdown("#### 1. Capacité Bénéficiaire (EPS) & Croissance (g)")
    c1, c2 = st.columns(2)
    eps = c1.number_input(f"BPA normalisé EPS (en {devise}, 0 = Auto Yahoo)", value=0.0, format="%.2f")
    g_lt = c2.number_input("Croissance moyenne attendue g (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.05, 0.005, format="%.3f")
    st.divider()

    # --- 2. CONDITIONS DE MARCHÉ AAA ---
    st.markdown("#### 2. Conditions de Marché AAA (Y) & Fiscalité (τ)")
    c1, c2 = st.columns(2)
    yield_aaa = c1.number_input("Rendement Obligations AAA Y (décimal, 0 = Auto Yahoo)", 0.0, 0.20, 0.045, 0.001, format="%.3f")
    tau = c2.number_input("Taux d'imposition τ (décimal, 0 = Auto Yahoo)", 0.0, 0.60, 0.25, 0.01, format="%.2f")
    st.divider()

    if st.button(f"Calculer la valeur Graham ({ticker})", type="primary", use_container_width=True):
        all_data = {
            "manual_fcf_base": eps, "fcf_growth_rate": g_lt, "corporate_aaa_yield": yield_aaa, "tax_rate": tau,
            "projection_years": 1, "perpetual_growth_rate": 0.0, "risk_free_rate": 0.0, "market_risk_premium": 0.0,
            "enable_monte_carlo": False
        }
        return ValuationRequest(
            ticker=ticker, projection_years=1, mode=ValuationMode.GRAHAM_1974_REVISED,
            input_source=InputSource.MANUAL, manual_params=safe_factory_params(all_data)
        )
    return None