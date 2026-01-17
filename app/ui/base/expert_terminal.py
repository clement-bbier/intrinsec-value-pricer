"""
app/ui/base/expert_terminal.py
CLASSE ABSTRAITE — Terminal Expert de Saisie

Pattern : Template Method (GoF)

Chaque terminal expert hérite de cette classe et implémente
uniquement les parties spécifiques à son modèle de valorisation.

Workflow du Template :
┌─────────────────────────────────────────────────┐
│  1. render_header()      - Titre + description  │
│  2. render_model_inputs() - SPÉCIFIQUE (abstract)│
│  3. render_discount_rate() - WACC ou Ke         │
│  4. render_growth_assumptions() - Croissance    │
│  5. render_terminal_value() - Sortie            │
│  6. render_optional_features() - Monte Carlo... │
│  7. render_submit() - Bouton de lancement       │
└─────────────────────────────────────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import streamlit as st

from core.models import (
    DCFParameters,
    InputSource,
    ValuationMode,
    ValuationRequest,
    TerminalValueMethod,
)
from core.i18n import ExpertTerminalTexts


class ExpertTerminalBase(ABC):
    """
    Classe abstraite définissant le squelette d'un terminal expert.
    
    Attributes
    ----------
    MODE : ValuationMode
        Le mode de valorisation (à définir dans chaque sous-classe).
    DISPLAY_NAME : str
        Nom affiché dans l'UI.
    DESCRIPTION : str
        Description courte du modèle.
    ICON : str
        Emoji représentant le modèle.
    
    Example
    -------
    >>> class DDMTerminal(ExpertTerminalBase):
    ...     MODE = ValuationMode.DDM
    ...     DISPLAY_NAME = "Dividend Discount Model"
    ...     DESCRIPTION = "Valorisation par les dividendes futurs"
    ...     ICON = "💰"
    """
    
    # ══════════════════════════════════════════════════════════════════════════
    # ATTRIBUTS DE CLASSE — À surcharger dans chaque terminal
    # ══════════════════════════════════════════════════════════════════════════
    
    MODE: ValuationMode = None
    DISPLAY_NAME: str = "Terminal Expert"
    DESCRIPTION: str = ""
    ICON: str = ""  # Style sobre, pas d'emojis
    
    # Options de rendu (peuvent être surchargées)
    SHOW_DISCOUNT_SECTION: bool = True
    SHOW_GROWTH_SECTION: bool = True
    SHOW_TERMINAL_SECTION: bool = True
    SHOW_MONTE_CARLO: bool = True
    SHOW_SCENARIOS: bool = False
    
    def __init__(self, ticker: str):
        """
        Initialise le terminal.
        
        Parameters
        ----------
        ticker : str
            Le symbole boursier de l'entreprise cible.
        """
        self.ticker = ticker
        self._collected_data: Dict[str, Any] = {}
    
    # ══════════════════════════════════════════════════════════════════════════
    # TEMPLATE METHOD — Point d'entrée principal
    # ══════════════════════════════════════════════════════════════════════════
    
    def render(self) -> Optional[ValuationRequest]:
        """
        Exécute le rendu complet du terminal (Template Method).
        
        Returns
        -------
        Optional[ValuationRequest]
            La requête si le formulaire est soumis, None sinon.
        """
        # Étape 1 : Header
        self._render_header()
        
        # Étape 2 : Inputs spécifiques au modèle (ABSTRACT)
        model_data = self.render_model_inputs()
        self._collected_data.update(model_data or {})
        
        # Étape 3 : Coût du capital (optionnel selon le modèle)
        if self.SHOW_DISCOUNT_SECTION:
            discount_data = self.render_discount_rate()
            self._collected_data.update(discount_data or {})
        
        # Étape 4 : Croissance (optionnel)
        if self.SHOW_GROWTH_SECTION:
            growth_data = self.render_growth_assumptions()
            self._collected_data.update(growth_data or {})
        
        # Étape 5 : Valeur terminale (optionnel)
        if self.SHOW_TERMINAL_SECTION:
            terminal_data = self.render_terminal_value()
            self._collected_data.update(terminal_data or {})
        
        # Étape 6 : Fonctionnalités optionnelles
        optional_data = self.render_optional_features()
        self._collected_data.update(optional_data or {})
        
        # Étape 7 : Soumission
        return self._render_submit()
    
    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODES CONCRÈTES — Comportement par défaut
    # ══════════════════════════════════════════════════════════════════════════
    
    def _render_header(self) -> None:
        """Affiche le header du terminal."""
        st.markdown(f"### {self.ICON} {self.DISPLAY_NAME}")
        if self.DESCRIPTION:
            st.caption(self.DESCRIPTION)
        st.divider()
    
    def render_discount_rate(self) -> Dict[str, Any]:
        """
        Section 3 : Coût du capital.
        
        Affiche WACC (Firm-Level) ou Ke (Equity-Level) selon le modèle.
        """
        st.markdown(f"**{ExpertTerminalTexts.SEC_3_CAPITAL}**")
        
        is_equity = self.MODE.is_direct_equity if self.MODE else False
        
        if is_equity:
            st.latex(r"k_e = R_f + \beta \times ERP")
        else:
            st.latex(r"WACC = \frac{E}{V} k_e + \frac{D}{V} k_d (1-\tau)")
        
        col1, col2 = st.columns(2)
        
        rf = col1.number_input(
            ExpertTerminalTexts.INP_RF,
            min_value=0.0, max_value=0.20, value=None,
            format="%.3f", help="Taux sans risque (ex: OAT 10 ans)"
        )
        beta = col2.number_input(
            ExpertTerminalTexts.INP_BETA,
            min_value=0.0, max_value=5.0, value=None,
            format="%.2f", help="Beta levered"
        )
        mrp = col1.number_input(
            ExpertTerminalTexts.INP_MRP,
            min_value=0.0, max_value=0.15, value=None,
            format="%.3f", help="Prime de risque marché"
        )
        
        result = {
            "risk_free_rate": rf,
            "manual_beta": beta,
            "market_risk_premium": mrp,
        }
        
        # Paramètres WACC supplémentaires
        if not is_equity:
            kd = col2.number_input(
                ExpertTerminalTexts.INP_KD,
                min_value=0.0, max_value=0.20, value=None,
                format="%.3f", help="Coût de la dette avant impôt"
            )
            tax = col1.number_input(
                ExpertTerminalTexts.INP_TAX,
                min_value=0.0, max_value=0.50, value=None,
                format="%.2f", help="Taux d'imposition effectif"
            )
            result.update({"cost_of_debt": kd, "tax_rate": tax})
        
        st.divider()
        return result
    
    def render_growth_assumptions(self) -> Dict[str, Any]:
        """Section 4 : Hypothèses de croissance."""
        st.markdown(f"**{ExpertTerminalTexts.SEC_4_GROWTH}**")
        
        col1, col2 = st.columns(2)
        
        growth = col1.number_input(
            ExpertTerminalTexts.INP_FCF_GROWTH,
            min_value=-0.30, max_value=0.50, value=None,
            format="%.3f", help="Croissance phase 1"
        )
        perpetual = col2.number_input(
            ExpertTerminalTexts.INP_PERP_G,
            min_value=0.0, max_value=0.04, value=0.02,
            format="%.3f", help="Croissance perpétuelle (≤ inflation LT)"
        )
        
        st.divider()
        return {"fcf_growth_rate": growth, "perpetual_growth_rate": perpetual}
    
    def render_terminal_value(self) -> Dict[str, Any]:
        """Section 5 : Valeur terminale."""
        st.markdown(f"**{ExpertTerminalTexts.SEC_5_TERMINAL}**")
        
        method = st.radio(
            ExpertTerminalTexts.LBL_TV_METHOD,
            options=[TerminalValueMethod.GORDON_GROWTH, TerminalValueMethod.EXIT_MULTIPLE],
            format_func=lambda x: "Gordon Growth Model" if x == TerminalValueMethod.GORDON_GROWTH else "Exit Multiple",
            horizontal=True
        )
        
        exit_mult = None
        if method == TerminalValueMethod.EXIT_MULTIPLE:
            exit_mult = st.number_input(
                ExpertTerminalTexts.INP_EXIT_MULT,
                min_value=3.0, max_value=25.0, value=10.0,
                format="%.1f", help="Multiple EV/EBITDA de sortie"
            )
        
        st.divider()
        return {"terminal_method": method, "exit_multiple": exit_mult}
    
    def render_optional_features(self) -> Dict[str, Any]:
        """Section 6 : Monte Carlo, Scénarios, etc."""
        result = {}
        
        if self.SHOW_MONTE_CARLO:
            from app.ui.expert_terminals.shared_widgets import widget_monte_carlo
            result.update(widget_monte_carlo())
        
        if self.SHOW_SCENARIOS:
            from app.ui.expert_terminals.shared_widgets import widget_scenarios
            result.update(widget_scenarios())
        
        return result
    
    def _render_submit(self) -> Optional[ValuationRequest]:
        """Bouton de soumission."""
        st.markdown("---")
        
        if st.button(
            ExpertTerminalTexts.BTN_CALCULATE,
            type="primary",
            use_container_width=True
        ):
            return self._build_request()
        
        return None
    
    # ══════════════════════════════════════════════════════════════════════════
    # MÉTHODE ABSTRAITE — À implémenter par chaque terminal
    # ══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    def render_model_inputs(self) -> Dict[str, Any]:
        """
        Section 2 : Inputs spécifiques au modèle.
        
        Cette méthode DOIT être implémentée par chaque terminal.
        Elle contient les widgets propres au type de valorisation.
        
        Returns
        -------
        Dict[str, Any]
            Données collectées spécifiques au modèle.
        """
        pass
    
    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION DE LA REQUÊTE
    # ══════════════════════════════════════════════════════════════════════════
    
    def _build_request(self) -> ValuationRequest:
        """Construit la ValuationRequest finale."""
        from app.ui.expert_terminals.shared_widgets import build_dcf_parameters
        
        params = build_dcf_parameters(self._collected_data)
        
        return ValuationRequest(
            ticker=self.ticker,
            mode=self.MODE,
            projection_years=self._collected_data.get("projection_years", 5),
            input_source=InputSource.MANUAL,
            manual_params=params,
            options=self._build_options()
        )
    
    def _build_options(self) -> Dict[str, Any]:
        """Options additionnelles pour la requête."""
        return {
            "enable_peer_multiples": self._collected_data.get("enable_peer_multiples", True),
        }
