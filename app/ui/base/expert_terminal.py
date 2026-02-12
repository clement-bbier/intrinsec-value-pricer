"""
app/ui/base/expert_terminal.py

CLASSE ABSTRAITE — Terminal Expert de Saisie

Version : V2.0 — ST-3.1 Logical Path Resolution
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

from src.domain.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod,
    ScenarioParameters,
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
        self._projection_years: int = 5  # Default, overridden by sidebar

        logger.debug(
            "Terminal %s initialized for ticker=%s",
            self.__class__.__name__,
            ticker
        )

    def set_projection_years(self, years: int) -> None:
        """
        Set the projection years from the common sidebar slider.

        Parameters
        ----------
        years : int
            Number of projection years from the sidebar.
        """
        self._projection_years = years

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
        # SECTION 6 : EXTENSIONS (Monte Carlo, Scénarios, SOTP)
        # Analyses complémentaires optionnelles
        # ══════════════════════════════════════════════════════════════════
        self._render_optional_features()

        # ══════════════════════════════════════════════════════════════════
        # SECTION 7 : SUBMIT
        # Lancement de la valorisation
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
            widget_sotp,
            build_dcf_parameters,
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
        Bouton de soumission.

        Returns
        -------
        Optional[ValuationRequest]
            La requête si le bouton est cliqué, None sinon.
        """
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

        # Inject sidebar projection_years into collected data before building params
        self._collected_data["projection_years"] = self._projection_years

        params = build_dcf_parameters(self._collected_data)

        # Injection des scénarios si configurés
        if self._scenarios is not None:
            params.scenarios = self._scenarios

        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=self._projection_years,
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
