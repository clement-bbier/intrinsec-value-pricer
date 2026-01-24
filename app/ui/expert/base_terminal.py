"""
app/ui/expert/base_terminal.py

CLASSE ABSTRAITE — Terminal Expert de Saisie (V15 - Flux Continu)
=================================================================
Le rendu suit strictement l'ordre de construction professionnel :
1. Header → 2. Opérationnel (Hook) → 3. Risque (WACC) → 4. Sortie (TV)
→ 5. Bridge (inc. SBC) → 6. Monte Carlo → 7. Peers → 8. Scénarios → 9. SOTP

Pattern : Template Method (GoF)
Style : Numpy docstrings
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

import streamlit as st

from src.models import (
    InputSource,
    ValuationMode,
    ValuationRequest,
    ScenarioParameters,
    TerminalValueMethod,
    DCFParameters
)
from src.i18n import SharedTexts

logger = logging.getLogger(__name__)


class ExpertTerminalBase(ABC):
    """
    Classe abstraite définissant le workflow de saisie expert.
    """

    # --- Configuration par défaut (Surchargée par les terminaux concrets) ---
    MODE: ValuationMode = None
    DISPLAY_NAME: str = "Terminal Expert"
    DESCRIPTION: str = ""
    ICON: str = ""

    # Options de rendu
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True
    SHOW_MONTE_CARLO: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = True
    SHOW_PEER_TRIANGULATION: bool = True
    SHOW_SUBMIT_BUTTON: bool = False

    # Formules LaTeX
    TERMINAL_VALUE_FORMULA: str = r"TV_n = f(FCF_n, g_n, WACC)"
    BRIDGE_FORMULA: str = SharedTexts.FORMULA_BRIDGE

    def __init__(self, ticker: str):
        """Initialise le terminal expert."""
        self.ticker = ticker
        self._collected_data: Dict[str, Any] = {}
        self._scenarios: Optional[ScenarioParameters] = None
        self._manual_peers: Optional[List[str]] = None

    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — Rendu UI
    # ══════════════════════════════════════════════════════════════════════════

    def render(self) -> Optional[ValuationRequest]:
        """
        Orchestre le rendu complet selon le Logical Path (ST-3.1).
        """
        # 1. HEADER
        self._render_header()

        # 2. OPÉRATIONNEL (Surchargé par les enfants)
        model_data = self.render_model_inputs()
        self._collected_data.update(model_data or {})

        # 3. RISQUE & CAPITAL (Actualisation)
        if self.SHOW_DISCOUNT_SECTION:
            self._render_step_header(SharedTexts.SEC_3_CAPITAL, SharedTexts.SEC_3_DESC)
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            self._collected_data.update(widget_cost_of_capital(self.MODE) or {})

        # 4. VALEUR DE SORTIE (Continuation)
        if self.SHOW_TERMINAL_SECTION:
            from app.ui.expert.terminals.shared_widgets import widget_terminal_value_dcf
            # Le widget gère son propre en-tête pour la dynamique LaTeX
            self._collected_data.update(widget_terminal_value_dcf(key_prefix=self.MODE.name) or {})

        # 5. EQUITY BRIDGE (inc. SBC)
        if self.SHOW_BRIDGE_SECTION:
            from app.ui.expert.terminals.shared_widgets import widget_equity_bridge
            # Widget unifié : Titre, Formule et SBC intégrés
            self._collected_data.update(widget_equity_bridge(self.BRIDGE_FORMULA, self.MODE) or {})

        # 6 à 9. EXTENSIONS OPTIONNELLES
        self._render_optional_features()

        # 10. SUBMIT
        return self._render_submit()

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES DE RENDU INTERNES
    # ══════════════════════════════════════════════════════════════════════════

    def _render_step_header(self, title: str, description: str) -> None:
        """Affiche un en-tête d'étape standardisé sans bordures."""
        st.markdown(title)
        st.info(description)

    def _render_header(self) -> None:
        """Affiche le titre principal du terminal."""
        title = f"{self.ICON} {self.DISPLAY_NAME}" if self.ICON else self.DISPLAY_NAME
        st.subheader(title)
        if self.DESCRIPTION:
            st.caption(self.DESCRIPTION)
        st.divider()

    def _render_optional_features(self) -> None:
        """Coordination des analyses complémentaires (Étapes 6 à 9)."""
        from app.ui.expert.terminals.shared_widgets import (
            widget_monte_carlo, widget_scenarios, widget_peer_triangulation, widget_sotp
        )

        # 6. Monte Carlo (Flexible)
        if self.SHOW_MONTE_CARLO:
            terminal_method = self._collected_data.get("terminal_method")
            mc_data = widget_monte_carlo(
                self.MODE,
                terminal_method,
                custom_vols=self.get_custom_monte_carlo_vols()
            )
            self._collected_data.update(mc_data or {})

        # 7. Peers (Triangulation)
        if self.SHOW_PEER_TRIANGULATION:
            peer_data = widget_peer_triangulation()
            self._collected_data.update(peer_data or {})
            self._manual_peers = peer_data.get("manual_peers")

        # 8. Scénarios (Convictions)
        if self.SHOW_SCENARIOS:
            self._scenarios = widget_scenarios(self.MODE)

        # 9. SOTP (Segmentation Finale)
        if self.SHOW_SOTP:
            from app.ui.expert.terminals.shared_widgets import build_dcf_parameters
            # Utilisation d'un buffer pour persister les saisies SOTP
            temp_params = build_dcf_parameters(self._collected_data)
            widget_sotp(temp_params)
            self._collected_data["sotp"] = temp_params.sotp

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """Hook pour les volatilités spécifiques au modèle (ex: ω pour RIM)."""
        return None

    def _render_submit(self) -> Optional[ValuationRequest]:
        """Bouton de soumission final."""
        if not self.SHOW_SUBMIT_BUTTON:
            return None
        st.divider()
        if st.button(SharedTexts.BTN_VALUATE_STD.format(ticker=self.ticker), type="primary", use_container_width=True):
            return self.build_request()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # EXTRACTION DES DONNÉES (SessionState)
    # ══════════════════════════════════════════════════════════════════════════

    def build_request(self) -> Optional[ValuationRequest]:
        """Construit la ValuationRequest en lisant le session_state."""
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        key_prefix = self.MODE.name
        collected_data = {"projection_years": st.session_state.get(f"{key_prefix}_years", 5)}

        # Extraction par blocs
        collected_data.update(self._extract_discount_data(key_prefix))
        if self.SHOW_TERMINAL_SECTION:
            collected_data.update(self._extract_terminal_data(key_prefix))
        if self.SHOW_BRIDGE_SECTION:
            collected_data.update(self._extract_bridge_data(key_prefix))
        if self.SHOW_MONTE_CARLO:
            collected_data.update(self._extract_monte_carlo_data(key_prefix))
        if self.SHOW_PEER_TRIANGULATION:
            collected_data.update(self._extract_peer_triangulation_data(key_prefix))

        # Données spécifiques au modèle
        collected_data.update(self._extract_model_inputs_data(key_prefix))

        params = build_dcf_parameters(collected_data)

        if self.SHOW_SCENARIOS:
            params.scenarios = self._extract_scenarios_data(key_prefix)

        if self.SHOW_SOTP and "sotp" in self._collected_data:
            params.sotp = self._collected_data["sotp"]

        return ValuationRequest(
            ticker=self.ticker, mode=self.MODE,
            projection_years=collected_data.get("projection_years", 5),
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES D'EXTRACTION PRIVÉES (Mapping technique)
    # ══════════════════════════════════════════════════════════════════════════

    def _extract_discount_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait Rf, Beta, MRP, Price, Kd, Tax."""
        data = {}
        mapping = {
            f"{key_prefix}_rf": "risk_free_rate", f"{key_prefix}_beta": "manual_beta",
            f"{key_prefix}_mrp": "market_risk_premium", f"{key_prefix}_price": "manual_stock_price",
            f"{key_prefix}_kd": "cost_of_debt", f"{key_prefix}_tax": "tax_rate"
        }
        for key, field in mapping.items():
            if key in st.session_state: data[field] = st.session_state[key]
        return data

    def _extract_bridge_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait la structure du bilan et le SBC."""
        data = {}
        p = f"bridge_{key_prefix}"
        mapping = {
            f"{p}_debt": "manual_total_debt", f"{p}_cash": "manual_cash",
            f"{p}_min": "manual_minority_interests", f"{p}_pen": "manual_pension_provisions",
            f"{p}_shares": "manual_shares_outstanding", f"{p}_shares_direct": "manual_shares_outstanding",
            f"{p}_sbc_rate": "stock_based_compensation_rate"
        }
        for k, f in mapping.items():
            if k in st.session_state: data[f] = st.session_state[k]
        return data

    def _extract_monte_carlo_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait la config MC avec volatilité terminale contextuelle."""
        data = {}
        if st.session_state.get("mc_enable"):
            data["enable_monte_carlo"] = True
            data["num_simulations"] = st.session_state.get("mc_sims")
            data["base_flow_volatility"] = st.session_state.get("mc_vol_flow")
            data["beta_volatility"] = st.session_state.get("mc_vol_beta")
            data["growth_volatility"] = st.session_state.get("mc_vol_growth")
            # Vol terminale : omega pour RIM, gn sinon
            field = "mc_vol_omega" if self.MODE == ValuationMode.RIM else "mc_vol_gn"
            data["terminal_growth_volatility"] = st.session_state.get(field)
        return data

    def _extract_peer_triangulation_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les comparables."""
        data = {}
        if st.session_state.get("peer_peer_enable"):
            data["enable_peer_multiples"] = True
            raw = st.session_state.get("peer_input", "")
            if raw: data["manual_peers"] = [p.strip().upper() for p in raw.split(",") if p.strip()]
        return data

    def _extract_scenarios_data(self, key_prefix: str) -> Optional[ScenarioParameters]:
        """Extrait Bull/Base/Bear."""
        from src.models import ScenarioVariant
        p = "scenario"
        if not st.session_state.get(f"{p}_scenario_enable"): return ScenarioParameters(enabled=False)
        try:
            return ScenarioParameters(
                enabled=True,
                bull=ScenarioVariant(label=SharedTexts.LBL_BULL, probability=st.session_state[f"{p}_p_bull"], growth_rate=st.session_state.get(f"{p}_g_bull"), target_fcf_margin=st.session_state.get(f"{p}_m_bull")),
                base=ScenarioVariant(label=SharedTexts.LBL_BASE, probability=st.session_state[f"{p}_p_base"], growth_rate=st.session_state.get(f"{p}_g_base"), target_fcf_margin=st.session_state.get(f"{p}_m_base")),
                bear=ScenarioVariant(label=SharedTexts.LBL_BEAR, probability=st.session_state[f"{p}_p_bear"], growth_rate=st.session_state.get(f"{p}_g_bear"), target_fcf_margin=st.session_state.get(f"{p}_m_bear"))
            )
        except (KeyError, Exception): return ScenarioParameters(enabled=False)

    def _build_options(self) -> Dict[str, Any]:
        """Options décochées par défaut pour un terminal propre."""
        return {
            "manual_peers": self._manual_peers,
            "enable_peer_multiples": self._collected_data.get("enable_peer_multiples", False),
        }

    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]: pass
    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]: return {}