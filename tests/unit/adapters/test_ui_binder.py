import streamlit as st
from app.adapters.ui_binder import UIBinder
from src.models.parameters.strategies import DDMParameters


def test_ui_binder_extraction(monkeypatch):
    """Vérifie que le Binder trouve les clés avec le bon préfixe."""
    mock_state = {
        "DDM_div_base": 2.5,
        "DDM_growth_rate": 3.0,
        "DDM_years": 5
    }
    monkeypatch.setattr(st, "session_state", mock_state)

    # Extraction pour le mode DDM
    extracted = UIBinder.pull(DDMParameters, prefix="DDM")

    assert extracted["dividend_per_share"] == 2.5
    assert extracted["dividend_growth_rate"] == 3.0
    assert extracted["projection_years"] == 5