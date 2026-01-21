#!/usr/bin/env python3
"""
Script de test pour valider la capture des données dans st.session_state
avant de commiter la refactorisation.

Usage:
    python test_session_state.py

Ce script simule l'état du session_state après avoir rempli un formulaire
et vérifie que build_request() peut extraire correctement les données.
"""

import sys
from pathlib import Path

# Configuration du path
FILE_PATH = Path(__file__).resolve()
ROOT_PATH = FILE_PATH.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

import streamlit as st
from src.models import ValuationMode, TerminalValueMethod
from app.ui.expert.factory import create_expert_terminal

def simulate_session_state():
    """
    Simule un état de session_state après saisie utilisateur pour FCFF_STANDARD.
    """
    # Simuler les données saisies pour un modèle FCFF_STANDARD
    st.session_state.update({
        # Coût du capital
        "FCFF_STANDARD_rf": 0.025,
        "FCFF_STANDARD_beta": 1.1,
        "FCFF_STANDARD_mrp": 0.055,
        "FCFF_STANDARD_price": 100.0,
        "FCFF_STANDARD_kd": 0.04,
        "FCFF_STANDARD_tax": 0.25,

        # Valeur terminale
        "FCFF_STANDARD_method": TerminalValueMethod.GORDON_GROWTH,
        "FCFF_STANDARD_gn": 0.015,

        # Equity Bridge
        "bridge_FCFF_STANDARD_debt": 500.0,
        "bridge_FCFF_STANDARD_cash": 200.0,
        "bridge_FCFF_STANDARD_min": 0.0,
        "bridge_FCFF_STANDARD_pen": 0.0,
        "bridge_FCFF_STANDARD_shares": 100.0,

        # Données spécifiques au modèle
        "FCFF_STANDARD_fcf_base": 50.0,
        "FCFF_STANDARD_years": 5,
        "FCFF_STANDARD_growth_rate": 0.03,
    })

    print("Session state simule pour FCFF_STANDARD")

def test_extraction():
    """
    Teste l'extraction des données via build_request().
    """
    try:
        # Créer un terminal FCFF_STANDARD
        terminal = create_expert_terminal(ValuationMode.FCFF_STANDARD, "AAPL")

        # Tester build_request()
        request = terminal.build_request()

        if request:
            print("build_request() a reussi")
            print(f"   Ticker: {request.ticker}")
            print(f"   Mode: {request.mode}")
            print(f"   Input source: {request.input_source}")

            # Vérifier quelques paramètres clés
            params = request.manual_params
            if hasattr(params, 'rates') and params.rates:
                print("   Parametres de taux extraits")
            if hasattr(params, 'terminal_method'):
                print(f"   Methode terminale: {params.terminal_method}")

            return True
        else:
            print("build_request() a retourne None")
            return False

    except Exception as e:
        print(f"Erreur lors du test: {e}")
        return False

def main():
    """
    Fonction principale du test.
    """
    print("Test de validation de la refactorisation session_state")
    print("=" * 60)

    # Simuler l'état du session state
    simulate_session_state()

    # Tester l'extraction
    success = test_extraction()

    print("=" * 60)
    if success:
        print("SUCCES: Test reussi ! La refactorisation fonctionne correctement.")
        print("   Vous pouvez maintenant commiter les changements.")
    else:
        print("ECHEC: Test echoue. Veuillez corriger les problemes avant de commiter.")

    return success

if __name__ == "__main__":
    main()