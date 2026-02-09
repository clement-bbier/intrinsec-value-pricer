"""
app/views/results/pillars/__init__.py

EXPOSITION DES PILIERS DE VALUATION
===================================
Ce fichier centralise et exporte les fonctions de rendu pour les six piliers
du tableau de bord de résultats.
"""

from .executive_summary import render_dashboard
from .inputs_summary import render_detailed_inputs
from .calculation_proof import render_glass_box
from .benchmark_report import render_benchmark_view
from .risk_engineering import render_risk_analysis
from .market_analysis import render_market_context

__all__ = [
    "render_dashboard",       # Pilier 0
    "render_detailed_inputs", # Pilier 1
    "render_glass_box",       # Pilier 2
    "render_benchmark_view",  # Pilier 3
    "render_risk_analysis",   # Pilier 4
    "render_market_context"   # Pilier 5
]