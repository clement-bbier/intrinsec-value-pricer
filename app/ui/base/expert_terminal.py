"""
app/ui/base/expert_terminal.py

CLASSE ABSTRAITE — Terminal Expert de Saisie

Classe abstraite - Expert Terminal
Pattern : Template Method (GoF)
Style : Numpy docstrings
Principes : SOLID (Single Responsibility, Open/Closed)

SÉQUENÇAGE "LOGICAL PATH" (ST-3.1 — McKinsey/Damodaran):
=========================================================
Le rendu suit strictement l'ordre de construction d'un modèle financier professionnel :

    1. HEADER              - Titre + description du modèle
    2. OPÉRATIONNEL        - CA, Marges, Flux de base (render_model_inputs)
    3. RISQUE & CAPITAL    - Bêta, Kd, WACC/Ke (render_discount_rate)
    4. VALEUR DE SORTIE    - Taux g, Multiples (render_terminal_value)
    5. EQUITY BRIDGE       - Passage EV → Equity (render_equity_bridge)
    6. EXTENSIONS          - Monte Carlo, Scénarios, SOTP
    7. SUBMIT              - Bouton de lancement

Financial Impact:
    L'ordre séquentiel guide l'analyste dans une réflexion structurée.
    Chaque section dépend logiquement des précédentes pour la cohérence
    des hypothèses de valorisation.

Note : Chaque terminal hérite de cette classe et implémente uniquement
       les parties spécifiques à son modèle de valorisation via les hooks.
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
)
from src.i18n import ExpertTerminalTexts

logger = logging.getLogger(__name__)


class ExpertTerminalBase(ABC):
    """
    Classe abstraite définissant le squelette d'un terminal expert.

    Cette classe implémente le pattern Template Method pour standardiser
    le workflow de saisie tout en permettant la personnalisation par modèle.

    Attributes
    ----------
    MODE : ValuationMode
        Le mode de valorisation (à définir dans chaque sous-classe).
    DISPLAY_NAME : str
        Nom affiché dans l'UI pour ce modèle.
    DESCRIPTION : str
        Description courte du modèle et de son cas d'usage.
    ICON : str
        Icône (vide par défaut, style sobre institutionnel).

    Class Attributes (Configuration)
    ---------------------------------
    SHOW_DISCOUNT_SECTION : bool
        Afficher la section coût du capital (default: True).
    SHOW_TERMINAL_SECTION : bool
        Afficher la section valeur terminale (default: True).
    SHOW_BRIDGE_SECTION : bool
        Afficher la section equity bridge (default: True).
    SHOW_MONTE_CARLO : bool
        Afficher l'option Monte Carlo (default: True).
    SHOW_SCENARIOS : bool
        Afficher l'option scénarios (default: True).
    SHOW_SOTP : bool
        Afficher l'option Sum-of-the-Parts (default: False).
    SHOW_PEER_TRIANGULATION : bool
        Afficher l'option triangulation par peers (default: True).

    Examples
    --------
    >>> class DDMTerminal(ExpertTerminalBase):
    ...     MODE = ValuationMode.DDM
    ...     DISPLAY_NAME = "Dividend Discount Model"
    ...     DESCRIPTION = "Valorisation par les dividendes futurs actualisés"
    ...
    ...     def render_model_inputs(self) -> Dict[str, Any]:
    ...         dividend = st.number_input("Dividende annuel D0")
    ...         return {"manual_dividend_base": dividend}
    """

    # ══════════════════════════════════════════════════════════════════════════
    # ATTRIBUTS DE CLASSE — À surcharger dans chaque terminal
    # ══════════════════════════════════════════════════════════════════════════

    MODE: ValuationMode = None
    DISPLAY_NAME: str = "Terminal Expert"
    DESCRIPTION: str = ""
    ICON: str = ""  # Style institutionnel sobre

    # Options de rendu (peuvent être surchargées par sous-classe)
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_BRIDGE_SECTION: bool = True
    SHOW_MONTE_CARLO: bool = True
    SHOW_SCENARIOS: bool = True
    SHOW_SOTP: bool = False
    SHOW_PEER_TRIANGULATION: bool = True
    SHOW_SBC_SECTION: bool = True
    SHOW_SUBMIT_BUTTON: bool = False

    # Formules LaTeX par défaut (peuvent être surchargées)
    TERMINAL_VALUE_FORMULA: str = r"TV_n = f(FCF_n, g_n, WACC)"
    BRIDGE_FORMULA: str = r"P = \dfrac{V_0 - \text{Debt} + \text{Cash}}{\text{Actions}}"

    def __init__(self, ticker: str):
        """
        Initialise le terminal expert.

        Parameters
        ----------
        ticker : str
            Le symbole boursier de l'entreprise cible.
        """
        self.ticker = ticker
        self._collected_data: Dict[str, Any] = {}
        self._scenarios: Optional[ScenarioParameters] = None
        self._manual_peers: Optional[List[str]] = None

        logger.debug(
            "Terminal %s initialized for ticker=%s",
            self.__class__.__name__,
            ticker
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — Point d'entrée principal
    # ══════════════════════════════════════════════════════════════════════════

    def render(self) -> Optional[ValuationRequest]:
        """
        Exécute le rendu complet du terminal (Template Method).

        Cette méthode orchestre l'ensemble du workflow de saisie en appelant
        les différentes étapes dans l'ordre strict du "Logical Path" (ST-3.1).

        Séquençage McKinsey/Damodaran:
        1. Header → 2. Opérationnel → 3. Risque & Capital →
        4. Valeur de Sortie → 5. Equity Bridge → 6. Extensions → 7. Submit

        Returns
        -------
        Optional[ValuationRequest]
            La requête de valorisation si le formulaire est soumis,
            None sinon (l'utilisateur n'a pas cliqué sur le bouton).

        Financial Impact
        ----------------
        L'ordre séquentiel guide l'analyste dans une réflexion structurée.
        Ne pas modifier l'ordre sans impact sur l'UX professionnelle.
        """
        # ══════════════════════════════════════════════════════════════════
        # SECTION 1 : HEADER
        # ══════════════════════════════════════════════════════════════════
        self._render_header()

        # ══════════════════════════════════════════════════════════════════
        # SECTION 2 : OPÉRATIONNEL (CA, Marges, Flux de base)
        # Point d'entrée du modèle — Données fondamentales
        # ══════════════════════════════════════════════════════════════════
        model_data = self.render_model_inputs()
        self._collected_data.update(model_data or {})

        # ══════════════════════════════════════════════════════════════════
        # SECTION 3 : RISQUE & CAPITAL (Bêta, Kd, WACC/Ke)
        # Coût du capital — Détermine le taux d'actualisation
        # ══════════════════════════════════════════════════════════════════
        if self.SHOW_DISCOUNT_SECTION:
            discount_data = self._render_discount_rate()
            self._collected_data.update(discount_data or {})

        # ══════════════════════════════════════════════════════════════════
        # SECTION 4 : VALEUR DE SORTIE (Taux g, Multiples)
        # Hypothèses de sortie — Impact majeur sur la valorisation
        # ══════════════════════════════════════════════════════════════════
        if self.SHOW_TERMINAL_SECTION:
            terminal_data = self._render_terminal_value()
            self._collected_data.update(terminal_data or {})

        # ══════════════════════════════════════════════════════════════════
        # SECTION 5 : EQUITY BRIDGE (EV → Equity)
        # Passage de la valeur d'entreprise à la valeur par action
        # ══════════════════════════════════════════════════════════════════
        if self.SHOW_BRIDGE_SECTION:
            bridge_data = self._render_equity_bridge()
            self._collected_data.update(bridge_data or {})

        # ══════════════════════════════════════════════════════════════════
        # SECTION 5.5 : SBC DILUTION (Stock-Based Compensation)
        # Ajustement pour la dilution des actionnaires historiques
        # ══════════════════════════════════════════════════════════════════
        if self.SHOW_SBC_SECTION:
            sbc_data = self._render_sbc_dilution()
            self._collected_data.update(sbc_data or {})

        # ══════════════════════════════════════════════════════════════════
        # SECTION 6 : EXTENSIONS (Monte Carlo, Scénarios, SOTP)
        # Analyses complémentaires optionnelles
        # ══════════════════════════════════════════════════════════════════
        self._render_optional_features()

        # ══════════════════════════════════════════════════════════════════
        # SECTION 7 : SUBMIT (conditionnel)
        # Lancement de la valorisation (seulement si bouton activé)
        # ══════════════════════════════════════════════════════════════════
        return self._render_submit()

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES CONCRÈTES — Comportement par défaut (peuvent être surchargées)
    # ══════════════════════════════════════════════════════════════════════════

    def _render_header(self) -> None:
        """
        Affiche le header du terminal.

        Inclut le titre du modèle, l'icône optionnelle, et une description.
        """
        title = f"{self.ICON} {self.DISPLAY_NAME}" if self.ICON else self.DISPLAY_NAME
        st.subheader(title)

        if self.DESCRIPTION:
            st.caption(self.DESCRIPTION)

        st.divider()

    def _render_discount_rate(self) -> Dict[str, Any]:
        """
        Section : Coût du capital.

        Utilise le widget partagé pour collecter les taux.

        Returns
        -------
        Dict[str, Any]
            Paramètres de taux collectés.
        """
        from app.ui.expert.terminals.shared_widgets import widget_cost_of_capital
        return widget_cost_of_capital(self.MODE)

    def _render_terminal_value(self) -> Dict[str, Any]:
        """
        Section : Valeur terminale.

        Affiche le widget approprié selon le type de modèle.

        Returns
        -------
        Dict[str, Any]
            Paramètres de valeur terminale.
        """
        from app.ui.expert.terminals.shared_widgets import widget_terminal_value_dcf
        return widget_terminal_value_dcf(self.TERMINAL_VALUE_FORMULA)

    def _render_equity_bridge(self) -> Dict[str, Any]:
        """
        Section : Ajustements de structure (Equity Bridge).

        Returns
        -------
        Dict[str, Any]
            Paramètres de bridge (dette, cash, actions, etc.)
        """
        from app.ui.expert.terminals.shared_widgets import widget_equity_bridge
        return widget_equity_bridge(self.BRIDGE_FORMULA, self.MODE)

    def _render_sbc_dilution(self) -> Dict[str, Any]:
        """
        Section : Dilution SBC (Stock-Based Compensation).

        Returns
        -------
        Dict[str, Any]
            Taux de dilution annuel SBC.
        """
        from app.ui.expert.terminals.shared_widgets import widget_sbc_dilution

        # Valeur par défaut du mode Auto (calculée automatiquement)
        default_sbc = self._collected_data.get("auto_sbc_rate")

        dilution_rate = widget_sbc_dilution(default_val=default_sbc)
        return {"annual_dilution_rate": dilution_rate}

    def _render_optional_features(self) -> None:
        """
        Section : Fonctionnalités optionnelles.

        Affiche les expanders pour Monte Carlo, Scénarios, Peers, SOTP.
        Met à jour les attributs internes (_scenarios, _manual_peers, etc.)
        """
        from app.ui.expert.terminals.shared_widgets import (
            widget_monte_carlo,
            widget_scenarios,
            widget_peer_triangulation,
        )

        # Monte Carlo
        if self.SHOW_MONTE_CARLO:
            terminal_method = self._collected_data.get("terminal_method")
            mc_data = widget_monte_carlo(self.MODE, terminal_method)
            self._collected_data.update(mc_data)

        # Peer Triangulation
        if self.SHOW_PEER_TRIANGULATION:
            peer_data = widget_peer_triangulation()
            self._collected_data.update(peer_data)
            self._manual_peers = peer_data.get("manual_peers")

        # Scénarios
        if self.SHOW_SCENARIOS:
            self._scenarios = widget_scenarios(self.MODE)

        # SOTP (modification in-place des paramètres)
        if self.SHOW_SOTP:
            # SOTP requiert un objet DCFParameters existant
            # On le créera au moment de la construction de la requête
            pass

    def _render_submit(self) -> Optional[ValuationRequest]:
        """
        Bouton de soumission (conditionnel).

        Le bouton n'est affiché que si SHOW_SUBMIT_BUTTON est True.
        Dans le nouveau mode centralisé, les terminaux n'affichent plus
        leur bouton interne.

        Returns
        -------
        Optional[ValuationRequest]
            La requête si le bouton est cliqué, None sinon.
        """
        if not self.SHOW_SUBMIT_BUTTON:
            return None

        st.divider()

        button_label = ExpertTerminalTexts.BTN_VALUATE_STD.format(ticker=self.ticker)

        if st.button(button_label, type="primary", width='stretch'):
            logger.info(
                "Valuation request submitted: ticker=%s, mode=%s",
                self.ticker,
                self.MODE.value if self.MODE else "N/A"
            )
            return self._build_request()

        return None

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODE ABSTRAITE — À implémenter par chaque terminal
    # ══════════════════════════════════════════════════════════════════════════

    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Section : Inputs spécifiques au modèle.

        Cette méthode DOIT être implémentée par chaque terminal.
        Elle contient les widgets propres au type de valorisation
        (flux de base, paramètres spécifiques, etc.)

        Returns
        -------
        Dict[str, Any]
            Données collectées spécifiques au modèle.

        Notes
        -----
        Les clés retournées doivent correspondre aux attributs attendus
        par DCFParameters.from_legacy() ou être gérées par le terminal.
        """
        pass

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION DE LA REQUÊTE
    # ══════════════════════════════════════════════════════════════════════════

    def _build_request(self) -> ValuationRequest:
        """
        Construit la ValuationRequest finale.

        Assemble les données collectées, construit les paramètres DCF,
        et crée la requête pour le moteur de valorisation.

        Returns
        -------
        ValuationRequest
            Requête complète prête pour l'exécution.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        params = build_dcf_parameters(self._collected_data)

        # Injection des scénarios si configurés
        if self._scenarios is not None:
            params.scenarios = self._scenarios

        projection_years = self._collected_data.get("projection_years", 5)

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=projection_years,
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(),
        )

    def _build_options(self) -> Dict[str, Any]:
        """
        Construit les options additionnelles pour la requête.

        Returns
        -------
        Dict[str, Any]
            Options incluant peers, enable flags, etc.
        """
        return {
            "manual_peers": self._manual_peers,
            "enable_peer_multiples": self._collected_data.get(
                "enable_peer_multiples", True
            ),
        }

    def build_request(self) -> Optional[ValuationRequest]:
        """
        Construit une ValuationRequest en lisant depuis st.session_state.

        Cette méthode ne doit appeler aucun widget Streamlit (pas de st.*).
        Elle lit directement les valeurs depuis st.session_state en utilisant
        les clés définies lors du rendu de l'UI.

        Returns
        -------
        Optional[ValuationRequest]
            La requête de valorisation si les données sont valides, None sinon.

        Notes
        -----
        Cette méthode est le pendant extractif de render() : elle lit ce que
        render() a affiché et stocké dans st.session_state.
        """
        from app.ui.expert.terminals.shared_widgets import build_dcf_parameters

        # Collecte des données depuis st.session_state avec les clés définies
        collected_data = {}

        # Clés générales (communes à tous les terminaux)
        key_prefix = self.MODE.name

        # 1. Projection years
        projection_key = f"{key_prefix}_years"
        if projection_key in st.session_state:
            collected_data["projection_years"] = st.session_state[projection_key]

        # 2. Coût du capital (toujours présent)
        collected_data.update(self._extract_discount_data(key_prefix))

        # 3. Valeur terminale (si activée)
        if self.SHOW_TERMINAL_SECTION:
            collected_data.update(self._extract_terminal_data(key_prefix))

        # 4. Equity Bridge (si activé)
        if self.SHOW_BRIDGE_SECTION:
            collected_data.update(self._extract_bridge_data(key_prefix))

        # 5. SBC Dilution (si activée)
        if self.SHOW_SBC_SECTION:
            sbc_key = f"{key_prefix}_sbc_dilution"
            if sbc_key in st.session_state:
                collected_data["annual_dilution_rate"] = st.session_state[sbc_key]

        # 6. Monte Carlo (si activé)
        if self.SHOW_MONTE_CARLO:
            collected_data.update(self._extract_monte_carlo_data(key_prefix))

        # 7. Peer Triangulation (si activée)
        if self.SHOW_PEER_TRIANGULATION:
            collected_data.update(self._extract_peer_triangulation_data(key_prefix))

        # 8. Scénarios (si activés)
        if self.SHOW_SCENARIOS:
            try:
                self._scenarios = self._extract_scenarios_data(key_prefix)
            except Exception as e:
                logger.warning(f"Error during scenario extraction: {e}")
                self._scenarios = None

        # 9. Données spécifiques au modèle (appel aux sous-classes)
        model_data = self._extract_model_inputs_data(key_prefix)
        collected_data.update(model_data)

        # Validation basique : au moins quelques champs remplis
        if not any(v is not None for v in collected_data.values() if v is not None):
            return None

        # Construction des paramètres DCF
        params = build_dcf_parameters(collected_data)

        # Injection des scénarios si configurés
        if self._scenarios is not None:
            params.scenarios = self._scenarios

        # SOTP si activé (traitement spécial car modifie params in-place)
        if self.SHOW_SOTP and hasattr(params, 'sotp'):
            # Pour SOTP, on doit créer un objet temporaire et le modifier
            # Cette partie peut nécessiter une adaptation selon l'implémentation actuelle
            pass

        projection_years = collected_data.get("projection_years", 5)

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=projection_years,
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options(),
        )

    def _extract_discount_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les données du coût du capital depuis st.session_state."""
        data = {}
        base_keys = [f"{key_prefix}_rf", f"{key_prefix}_beta", f"{key_prefix}_mrp", f"{key_prefix}_price"]

        # Clés de base (toujours présentes)
        for key in base_keys:
            if key in st.session_state and st.session_state[key] is not None:
                if "_rf" in key:
                    data["risk_free_rate"] = st.session_state[key]
                elif "_beta" in key:
                    data["manual_beta"] = st.session_state[key]
                elif "_mrp" in key:
                    data["market_risk_premium"] = st.session_state[key]
                elif "_price" in key:
                    data["manual_stock_price"] = st.session_state[key]

        # Clés WACC (si pas Direct Equity)
        if not self.MODE.is_direct_equity:
            wacc_keys = [f"{key_prefix}_kd", f"{key_prefix}_tax"]
            for key in wacc_keys:
                if key in st.session_state and st.session_state[key] is not None:
                    if "_kd" in key:
                        data["cost_of_debt"] = st.session_state[key]
                    elif "_tax" in key:
                        data["tax_rate"] = st.session_state[key]

        return data

    def _extract_terminal_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les données de valeur terminale depuis st.session_state."""
        data = {}

        # Méthode terminale
        method_key = f"{key_prefix}_method"
        if method_key in st.session_state:
            terminal_method = st.session_state[method_key]
            data["terminal_method"] = terminal_method

            # Selon la méthode, extraire les paramètres appropriés
            if terminal_method == TerminalValueMethod.GORDON_GROWTH:
                gn_key = f"{key_prefix}_gn"
                if gn_key in st.session_state:
                    data["perpetual_growth_rate"] = st.session_state[gn_key]
            else:  # EXIT_MULTIPLE
                mult_key = f"{key_prefix}_exit_mult"
                if mult_key in st.session_state:
                    data["exit_multiple_value"] = st.session_state[mult_key]

        return data

    def _extract_bridge_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les données d'equity bridge depuis st.session_state."""
        data = {}
        bridge_prefix = f"bridge_{key_prefix}"

        bridge_keys = [
            f"{bridge_prefix}_debt", f"{bridge_prefix}_cash",
            f"{bridge_prefix}_min", f"{bridge_prefix}_pen", f"{bridge_prefix}_shares"
        ]

        for key in bridge_keys:
            if key in st.session_state and st.session_state[key] is not None:
                if "_debt" in key:
                    data["manual_total_debt"] = st.session_state[key]
                elif "_cash" in key:
                    data["manual_cash"] = st.session_state[key]
                elif "_min" in key:
                    data["manual_minority_interests"] = st.session_state[key]
                elif "_pen" in key:
                    data["manual_pension_provisions"] = st.session_state[key]
                elif "_shares" in key:
                    data["manual_shares_outstanding"] = st.session_state[key]

        return data

    def _extract_monte_carlo_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les données Monte Carlo depuis st.session_state."""
        data = {}
        mc_prefix = f"{key_prefix}_mc" if f"{key_prefix}_mc_enable" in st.session_state else "mc"

        # Enable
        enable_key = f"{mc_prefix}_enable"
        if enable_key in st.session_state and st.session_state[enable_key]:
            data["enable_monte_carlo"] = True

            # Simulations
            sims_key = f"{mc_prefix}_sims"
            if sims_key in st.session_state:
                data["num_simulations"] = st.session_state[sims_key]

            # Volatilités
            vol_keys = [f"{mc_prefix}_vol_flow", f"{mc_prefix}_vol_beta", f"{mc_prefix}_vol_growth"]
            for key in vol_keys:
                if key in st.session_state:
                    if "_vol_flow" in key:
                        data["base_flow_volatility"] = st.session_state[key]
                    elif "_vol_beta" in key:
                        data["beta_volatility"] = st.session_state[key]
                    elif "_vol_growth" in key:
                        data["growth_volatility"] = st.session_state[key]

            # Volatilité terminale conditionnelle
            if self.MODE == ValuationMode.RIM:
                omega_key = f"{mc_prefix}_vol_omega"
                if omega_key in st.session_state:
                    data["terminal_growth_volatility"] = st.session_state[omega_key]
            elif self._collected_data.get("terminal_method") == "GORDON_GROWTH":
                gn_key = f"{mc_prefix}_vol_gn"
                if gn_key in st.session_state:
                    data["terminal_growth_volatility"] = st.session_state[gn_key]

        return data

    def _extract_peer_triangulation_data(self, key_prefix: str) -> Dict[str, Any]:
        """Extrait les données de peer triangulation depuis st.session_state."""
        data = {}

        # Enable peer multiples
        enable_key = f"{key_prefix}_peer_enable"
        if enable_key in st.session_state and st.session_state[enable_key]:
            data["enable_peer_multiples"] = True

        # Manual peers
        input_key = f"{key_prefix}_input"
        if input_key in st.session_state and st.session_state[input_key]:
            raw_input = st.session_state[input_key]
            if raw_input.strip():
                peers_list = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
                if peers_list:
                    data["manual_peers"] = peers_list

        return data

    def _extract_scenarios_data(self, key_prefix: str) -> Optional[ScenarioParameters]:
        """Extrait les données de scénarios depuis st.session_state."""
        from src.models import ScenarioParameters, ScenarioVariant

        # Vérifier si les scénarios sont activés
        enable_key = f"{key_prefix}_scenario_enable"
        if not (enable_key in st.session_state and st.session_state[enable_key]):
            return ScenarioParameters(enabled=False)

        # Extraire les probabilités
        p_bull_key = f"{key_prefix}_p_bull"
        p_base_key = f"{key_prefix}_p_base"
        p_bear_key = f"{key_prefix}_p_bear"

        if not all(k in st.session_state for k in [p_bull_key, p_base_key, p_bear_key]):
            return ScenarioParameters(enabled=False)

        p_bull = st.session_state[p_bull_key]
        p_base = st.session_state[p_base_key]
        p_bear = st.session_state[p_bear_key]

        # Validation des probabilités
        total_proba = round(p_bull + p_base + p_bear, 2)
        if total_proba != 1.0:
            return ScenarioParameters(enabled=False)

        # Extraire les autres paramètres
        g_bull_key = f"{key_prefix}_g_bull"
        g_base_key = f"{key_prefix}_g_base"
        g_bear_key = f"{key_prefix}_g_bear"

        g_bull = st.session_state.get(g_bull_key)
        g_base = st.session_state.get(g_base_key)
        g_bear = st.session_state.get(g_bear_key)

        # Marges pour FCFF_GROWTH
        m_bull = m_base = m_bear = None
        if self.MODE == ValuationMode.FCFF_GROWTH:
            m_bull_key = f"{key_prefix}_m_bull"
            m_base_key = f"{key_prefix}_m_base"
            m_bear_key = f"{key_prefix}_m_bear"

            m_bull = st.session_state.get(m_bull_key)
            m_base = st.session_state.get(m_base_key)
            m_bear = st.session_state.get(m_bear_key)

        # Construction sécurisée
        try:
            return ScenarioParameters(
                enabled=True,
                bull=ScenarioVariant(
                    label=ExpertTerminalTexts.LBL_BULL,
                    growth_rate=g_bull,
                    target_fcf_margin=m_bull,
                    probability=p_bull
                ),
                base=ScenarioVariant(
                    label=ExpertTerminalTexts.LBL_BASE,
                    growth_rate=g_base,
                    target_fcf_margin=m_base,
                    probability=p_base
                ),
                bear=ScenarioVariant(
                    label=ExpertTerminalTexts.LBL_BEAR,
                    growth_rate=g_bear,
                    target_fcf_margin=m_bear,
                    probability=p_bear
                ),
            )
        except Exception:
            return ScenarioParameters(enabled=False)

    def _extract_model_inputs_data(self, key_prefix: str) -> Dict[str, Any]:
        """
        Extrait les données spécifiques au modèle depuis st.session_state.

        Cette méthode doit être implémentée par chaque sous-classe pour
        extraire les données propres à son modèle (FCF, dividendes, etc.).

        Parameters
        ----------
        key_prefix : str
            Préfixe de clé basé sur le mode.

        Returns
        -------
        Dict[str, Any]
            Données spécifiques au modèle.
        """
        # Méthode abstraite à implémenter par les sous-classes
        return {}
