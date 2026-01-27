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
    SOTPParameters
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
        Orchestre le rendu complet selon la séquence de réflexion de l'analyste.
        Ordre : Opérationnel -> Risque -> Sortie -> Structure -> Ingénierie.
        """
        # 1. HEADER (Identité du modèle)
        self._render_header()

        # 2. ÉTAPE OPÉRATIONNELLE (Ancrage & Croissance spécifique au modèle)
        model_data = self.render_model_inputs()
        self._collected_data.update(model_data or {})

        # 3. ÉTAPE RISQUE & CAPITAL (Actualisation / WACC / Ke)
        if self.SHOW_DISCOUNT_SECTION:
            self._render_step_header(SharedTexts.SEC_3_CAPITAL, SharedTexts.SEC_3_DESC)
            from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
            self._collected_data.update(widget_cost_of_capital(self.MODE) or {})

        # 4. ÉTAPE VALEUR DE SORTIE (Valeur Terminale / Horizon)
        if self.SHOW_TERMINAL_SECTION:
            from app.ui.expert.terminals.shared_widgets import widget_terminal_value_dcf
            # On passe le préfixe du mode pour éviter les collisions session_state
            self._collected_data.update(widget_terminal_value_dcf(key_prefix=self.MODE.name) or {})

        # 5. ÉTAPE STRUCTURE & AJUSTEMENTS (Equity Bridge / SBC / Dette)
        if self.SHOW_BRIDGE_SECTION:
            self._collected_data.update(self._render_equity_bridge() or {})

        # 6 à 9. ÉTAPES D'INGÉNIERIE (Extensions Optionnelles)
        # Cette méthode coordonne l'affichage de MC, Scénarios, SOTP et Peers
        self._render_optional_features()

        # 10. BOUTON D'EXÉCUTION
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

    def _render_equity_bridge(self) -> Dict[str, Any]:
        """
        Section 5 : Ajustements de structure (Equity Bridge).
        Adapte la formule LaTeX et la complexité selon le type de modèle.
        """
        from app.ui.expert.terminals.shared_widgets import widget_equity_bridge

        # LOGIQUE DE PERTINENCE :
        # Si Direct Equity (DDM, RIM, FCFE), on affiche une formule simplifiée
        if self.MODE.is_direct_equity:
            # Formule pour les modèles valorisant directement les capitaux propres
            formula = SharedTexts.FORMULA_BRIDGE_SIMPLE
        else:
            # Formule complète EV -> Equity (FCFF)
            formula = self.BRIDGE_FORMULA

        return widget_equity_bridge(formula, self.MODE)

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
            temp_params = build_dcf_parameters(self._collected_data)
            widget_sotp(temp_params, is_conglomerate=False)
            self._collected_data["sotp"] = temp_params.sotp

    def get_custom_monte_carlo_vols(self) -> Optional[Dict[str, str]]:
        """
        Dynamise les entrées de Monte Carlo selon la méthodologie choisie (ST-4.2).

        Cette méthode implémente la logique expert : adapter les paramètres de
        dispersion aux variables critiques de chaque modèle (g, ω, ou EPS).

        Returns
        -------
        Optional[Dict[str, str]]
            Dictionnaire de correspondance {clé_technique: label_i18n}.
        """
        # 1. Modèles de flux (FCFF/FCFE/DDM) : Focus sur la croissance g
        if self.MODE in [
            ValuationMode.FCFF_STANDARD,
            ValuationMode.FCFF_NORMALIZED,
            ValuationMode.FCFF_GROWTH,
            ValuationMode.FCFE,
            ValuationMode.DDM
        ]:
            return {"growth_volatility": SharedTexts.MC_VOL_G}

        # 2. Modèle RIM : Focus sur la persistance des profits résiduels omega
        if self.MODE == ValuationMode.RIM:
            return {"terminal_growth_volatility": SharedTexts.LBL_VOL_OMEGA}

        # 3. Modèle Graham : Focus sur le bénéfice par action (EPS) et la croissance LT
        if self.MODE == ValuationMode.GRAHAM:
            # On utilise base_flow_volatility pour l'incertitude sur l'EPS
            return {
                "base_flow_volatility": SharedTexts.MC_VOL_BASE_FLOW,
                "growth_volatility": SharedTexts.MC_VOL_G
            }

        return None

    def _render_submit(self) -> Optional[ValuationRequest]:
        """Bouton de soumission final."""
        if not self.SHOW_SUBMIT_BUTTON:
            return None
        st.divider()
        if st.button(SharedTexts.BTN_VALUATE_STD.format(ticker=self.ticker), type="primary", width="stretch"):
            return self.build_request()
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # EXTRACTION DES DONNÉES (SessionState)
    # ══════════════════════════════════════════════════════════════════════════

    def build_request(self) -> Optional[ValuationRequest]:
        """
        Construit la ValuationRequest finale.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        key_prefix = self.MODE.name
        collected_data = {"projection_years": st.session_state.get(f"{key_prefix}_years", 5)}

        # Extraction par blocs universels
        collected_data.update(self._extract_discount_data(key_prefix))
        if self.SHOW_TERMINAL_SECTION:
            collected_data.update(self._extract_terminal_data(key_prefix))
        if self.SHOW_BRIDGE_SECTION:
            collected_data.update(self._extract_bridge_data(key_prefix))
        if self.SHOW_MONTE_CARLO:
            collected_data.update(self._extract_monte_carlo_data(key_prefix))
        if self.SHOW_PEER_TRIANGULATION:
            collected_data.update(self._extract_peer_triangulation_data(key_prefix))

        # Données spécifiques (Ancrage & Croissance harmonisés)
        collected_data.update(self._extract_model_inputs_data(key_prefix))

        # Construction de l'objet métier
        params = build_dcf_parameters(collected_data)

        # Scénarios et SOTP (Vérification de pertinence)
        if self.SHOW_SCENARIOS:
            params.scenarios = self._extract_scenarios_data(key_prefix)

        if self.SHOW_SOTP:
            # Extraction sécurisée via le buffer instance
            params.sotp = self._extract_sotp_data()

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=collected_data.get("projection_years", 5),
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(),
        )

    def _extract_sotp_data(self) -> Optional[SOTPParameters]:
        """
        Récupère les segments SOTP stockés lors du rendu de l'Étape 9.
        """
        return self._collected_data.get("sotp")

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
        """
        Extrait la config Monte Carlo avec sécurité de présence des clés.
        """
        p = "mc"  # Préfixe harmonisé avec shared_widgets.py

        # Vérification robuste de l'activation
        if not st.session_state.get(f"{p}_enable", False):
            return {"enable_monte_carlo": False}

        # Dictionnaire d'extraction sécurisé (.get() systématique)
        return {
            "enable_monte_carlo": True,
            "num_simulations": st.session_state.get(f"{p}_sims", 5000),
            "base_flow_volatility": st.session_state.get(f"{p}_vol_flow"),
            "beta_volatility": st.session_state.get(f"{p}_vol_beta"),
            "growth_volatility": st.session_state.get(f"{p}_vol_growth"),
            "exit_multiple_volatility": st.session_state.get(f"{p}_vol_exit_m")
        }

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

    def _extract_terminal_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les paramètres de la Valeur Terminale (Gordon ou Multiples).

        Récupère dynamiquement le taux de croissance perpétuelle (gn) ou
        le multiple de sortie selon le choix de l'utilisateur.
        """
        data = {}
        method_key = f"{key_prefix}_method"

        if method_key in st.session_state:
            method = st.session_state[method_key]
            data["terminal_method"] = method

            # Extraction conditionnelle selon la méthode de sortie
            if method == TerminalValueMethod.GORDON_GROWTH:
                data["perpetual_growth_rate"] = st.session_state.get(f"{key_prefix}_gn")
            else:
                data["exit_multiple_value"] = st.session_state.get(f"{key_prefix}_exit_mult")

        return data