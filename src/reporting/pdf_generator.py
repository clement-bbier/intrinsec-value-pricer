"""
src/reporting/pdf_generator.py

PITCHBOOK PDF GENERATOR — ST-5.2

Version : V1.0 — Sprint 5
Pattern : Builder + Template
Style : Numpy docstrings
Dépendance : fpdf2 >= 2.7.0

ST-5.2 : REPORTING PREMIUM PDF
==============================
Génère un Pitchbook professionnel de 3 pages :
1. Résumé exécutif avec prix cible et score d'audit
2. Preuves de calcul détaillées avec formules
3. Analyse de sensibilité et distribution Monte Carlo

Performance cible : Export < 5 secondes

Usage:
    from src.reporting.pdf_generator import generate_pitchbook_pdf
    from src.domain.models.pitchbook import PitchbookData
    
    data = PitchbookData.from_valuation_result(result)
    pdf_bytes = generate_pitchbook_pdf(data)
    
    # Sauvegarder
    with open("pitchbook_AAPL.pdf", "wb") as f:
        f.write(pdf_bytes)

Financial Impact:
    Le Pitchbook est le livrable final présenté aux investisseurs.
    La qualité du PDF reflète le professionnalisme de l'analyse.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    FPDF = None

from src.domain.models.pitchbook import PitchbookData
from src.utilities.formatting import format_smart_number

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DE STYLE
# ============================================================================

# Couleurs (R, G, B)
COLOR_PRIMARY = (27, 94, 32)      # Vert foncé institutionnel
COLOR_SECONDARY = (21, 101, 192)  # Bleu professionnel
COLOR_ACCENT = (198, 40, 40)      # Rouge alerte
COLOR_GRAY = (97, 97, 97)         # Gris texte
COLOR_LIGHT_GRAY = (245, 245, 245)  # Fond clair
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# Marges et dimensions
MARGIN_LEFT = 15
MARGIN_TOP = 15
PAGE_WIDTH = 210  # A4
PAGE_HEIGHT = 297
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_LEFT


class PitchbookPDFGenerator:
    """
    Générateur de Pitchbook PDF professionnel.
    
    Utilise fpdf2 pour créer un rapport de 3 pages
    avec un design institutionnel standardisé.
    
    Attributes
    ----------
    data : PitchbookData
        Données du Pitchbook.
    pdf : FPDF
        Instance du générateur PDF.
    
    Examples
    --------
    >>> generator = PitchbookPDFGenerator(data)
    >>> pdf_bytes = generator.generate()
    """
    
    def __init__(self, data: PitchbookData):
        """
        Initialise le générateur.
        
        Parameters
        ----------
        data : PitchbookData
            Données du Pitchbook.
        
        Raises
        ------
        ImportError
            Si fpdf2 n'est pas installé.
        """
        if not FPDF_AVAILABLE:
            raise ImportError(
                "fpdf2 is required for PDF generation. "
                "Install it with: pip install fpdf2"
            )
        
        self.data = data
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
    
    def generate(self) -> bytes:
        """
        Génère le PDF complet.
        
        Returns
        -------
        bytes
            Contenu binaire du PDF.
        """
        start_time = datetime.now()
        
        # Page 1 : Résumé exécutif
        self._render_executive_summary()
        
        # Page 2 : Preuves de calcul
        self._render_calculation_proof()
        
        # Page 3 : Analyse de risque
        self._render_risk_analysis()
        
        # Générer le PDF
        pdf_bytes = self.pdf.output()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[PDFGenerator] Pitchbook generated in {duration:.2f}s")
        
        return bytes(pdf_bytes)
    
    # ========================================================================
    # PAGE 1 : RÉSUMÉ EXÉCUTIF
    # ========================================================================
    
    def _render_executive_summary(self) -> None:
        """Génère la page 1 : Résumé exécutif."""
        self.pdf.add_page()
        exec_data = self.data.executive_summary
        
        # Header
        self._render_header(
            f"VALUATION REPORT",
            f"{exec_data.get('ticker', 'N/A')} - {exec_data.get('company_name', '')}"
        )
        
        # Section : Valorisation
        self.pdf.set_y(50)
        self._render_section_title("VALORISATION")
        
        # KPIs principaux
        self.pdf.set_y(60)
        
        # Tableau 2x2 des KPIs
        currency = exec_data.get('currency', '')
        kpi_data = [
            ("Valeur Intrinsèque", format_smart_number(exec_data.get('intrinsic_value', 0), currency)),
            ("Prix de Marché", format_smart_number(exec_data.get('market_price', 0), currency)),
            ("Potentiel", format_smart_number(exec_data.get('upside_pct', 0), "", True)),
            ("Recommandation", exec_data.get('recommendation', 'N/A')),
        ]
        
        self._render_kpi_grid(kpi_data)
        
        # Section : Score d'Audit
        self.pdf.set_y(120)
        self._render_section_title("SCORE D'AUDIT")
        
        audit_score = exec_data.get('audit_score', 0)
        audit_grade = exec_data.get('audit_grade', 'N/A')
        
        self.pdf.set_y(130)
        self.pdf.set_font("Helvetica", "B", 36)
        self.pdf.set_text_color(*COLOR_PRIMARY)
        self.pdf.cell(50, 20, f"{audit_score:.0f}%", ln=False)
        
        self.pdf.set_font("Helvetica", "B", 24)
        self.pdf.set_text_color(*COLOR_SECONDARY)
        self.pdf.cell(30, 20, f"({audit_grade})", ln=True)
        
        # Section : Hypothèses clés
        self.pdf.set_y(160)
        self._render_section_title("HYPOTHÈSES CLÉS")
        
        key_metrics = exec_data.get('key_metrics', {})
        assumptions = [
            ("WACC", format_smart_number(key_metrics.get('wacc', 0), "", True) if key_metrics.get('wacc') else "N/A"),
            ("Croissance perpétuelle", format_smart_number(key_metrics.get('perpetual_growth', 0), "", True) if key_metrics.get('perpetual_growth') else "N/A"),
            ("Valeur d'Entreprise", format_smart_number(key_metrics.get('enterprise_value', 0), "") if key_metrics.get('enterprise_value') else "N/A"),
        ]
        
        self._render_assumptions_table(assumptions)
        
        # Footer
        self._render_footer(f"Mode: {exec_data.get('valuation_mode', 'N/A')}")
    
    # ========================================================================
    # PAGE 2 : PREUVES DE CALCUL
    # ========================================================================
    
    def _render_calculation_proof(self) -> None:
        """Génère la page 2 : Preuves de calcul."""
        self.pdf.add_page()
        calc_data = self.data.calculation_proof
        
        # Header
        self._render_header("PREUVE DE CALCUL", "Traçabilité Glass Box")
        
        # Section : Composantes DCF
        self.pdf.set_y(50)
        self._render_section_title("DÉCOMPOSITION DE LA VALEUR")
        
        dcf = calc_data.get('dcf_components', {})
        components = [
            ("Valeur Actualisée des Flux", format_smart_number(dcf.get('pv_explicit_flows', 0), "")),
            ("Valeur Terminale", format_smart_number(dcf.get('terminal_value', 0), "")),
            ("Valeur d'Entreprise", format_smart_number(dcf.get('enterprise_value', 0), "")),
            ("Valeur des Capitaux Propres", format_smart_number(dcf.get('equity_value', 0), "")),
        ]
        
        self._render_waterfall_text(components)
        
        # Section : Hypothèses
        self.pdf.set_y(130)
        self._render_section_title("PARAMÈTRES D'ENTRÉE")
        
        assumptions = calc_data.get('key_assumptions', {})
        params = [
            ("Taux sans risque (Rf)", format_smart_number(assumptions.get('risk_free_rate', 0), "", True) if assumptions.get('risk_free_rate') else "N/A"),
            ("Prime de risque marché", format_smart_number(assumptions.get('market_risk_premium', 0), "", True) if assumptions.get('market_risk_premium') else "N/A"),
            ("Bêta", format_smart_number(assumptions.get('beta', 0), "") if assumptions.get('beta') else "N/A"),
            ("Coût de la dette", format_smart_number(assumptions.get('cost_of_debt', 0), "", True) if assumptions.get('cost_of_debt') else "N/A"),
            ("Taux d'imposition", format_smart_number(assumptions.get('tax_rate', 0), "", True) if assumptions.get('tax_rate') else "N/A"),
        ]
        
        self._render_assumptions_table(params)
        
        # Footer
        self._render_footer("Données certifiées Yahoo Finance")
    
    # ========================================================================
    # PAGE 3 : ANALYSE DE RISQUE
    # ========================================================================
    
    def _render_risk_analysis(self) -> None:
        """Génère la page 3 : Analyse de risque."""
        self.pdf.add_page()
        risk_data = self.data.risk_analysis
        
        # Header
        self._render_header("ANALYSE DE RISQUE", "Sensibilité & Distribution")
        
        # Section : Monte Carlo
        mc_stats = risk_data.get('monte_carlo_stats')
        if mc_stats:
            self.pdf.set_y(50)
            self._render_section_title("DISTRIBUTION MONTE CARLO")
            
            mc_info = [
                ("Nombre de simulations", format_smart_number(mc_stats.get('count', 0), "")),
                ("Médiane (P50)", format_smart_number(mc_stats.get('median', 0), "")),
                ("Percentile 10", format_smart_number(mc_stats.get('p10', 0), "")),
                ("Percentile 90", format_smart_number(mc_stats.get('p90', 0), "")),
                ("Écart-type", format_smart_number(mc_stats.get('std', 0), "")),
            ]
            
            self._render_assumptions_table(mc_info)
        
        # Section : Scénarios
        scenarios = risk_data.get('scenario_results')
        if scenarios:
            self.pdf.set_y(130 if mc_stats else 50)
            self._render_section_title("ANALYSE DE SCÉNARIOS")
            
            scenario_list = [
                (label, format_smart_number(value, ""))
                for label, value in scenarios.items()
            ]
            
            self._render_assumptions_table(scenario_list)
        
        # Section : Facteurs de risque
        risk_factors = risk_data.get('risk_factors', [])
        if risk_factors:
            current_y = 200 if scenarios else (130 if mc_stats else 50)
            self.pdf.set_y(current_y)
            self._render_section_title("FACTEURS DE RISQUE IDENTIFIÉS")
            
            self.pdf.set_font("Helvetica", "", 10)
            self.pdf.set_text_color(*COLOR_GRAY)
            for factor in risk_factors[:5]:
                self.pdf.cell(0, 8, f"• {factor}", ln=True)
        
        # Footer
        self._render_footer("Analyse de sensibilité WACC/g")
    
    # ========================================================================
    # COMPOSANTS RÉUTILISABLES
    # ========================================================================
    
    def _render_header(self, title: str, subtitle: str) -> None:
        """Génère le header d'une page."""
        # Barre de couleur en haut
        self.pdf.set_fill_color(*COLOR_PRIMARY)
        self.pdf.rect(0, 0, PAGE_WIDTH, 8, "F")
        
        # Titre
        self.pdf.set_y(15)
        self.pdf.set_font("Helvetica", "B", 18)
        self.pdf.set_text_color(*COLOR_BLACK)
        self.pdf.cell(0, 10, title, ln=True)
        
        # Sous-titre
        self.pdf.set_font("Helvetica", "", 12)
        self.pdf.set_text_color(*COLOR_GRAY)
        self.pdf.cell(0, 6, subtitle, ln=True)
        
        # Ligne de séparation
        self.pdf.set_draw_color(*COLOR_PRIMARY)
        self.pdf.set_line_width(0.5)
        self.pdf.line(MARGIN_LEFT, 38, PAGE_WIDTH - MARGIN_LEFT, 38)
    
    def _render_footer(self, text: str) -> None:
        """Génère le footer d'une page."""
        self.pdf.set_y(-25)
        self.pdf.set_font("Helvetica", "I", 8)
        self.pdf.set_text_color(*COLOR_GRAY)
        
        # Ligne
        self.pdf.set_draw_color(*COLOR_GRAY)
        self.pdf.set_line_width(0.3)
        self.pdf.line(MARGIN_LEFT, PAGE_HEIGHT - 25, PAGE_WIDTH - MARGIN_LEFT, PAGE_HEIGHT - 25)
        
        # Texte
        self.pdf.set_y(-20)
        self.pdf.cell(0, 5, f"Intrinsic Value Pricer | {text} | Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")
    
    def _render_section_title(self, title: str) -> None:
        """Génère un titre de section."""
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(*COLOR_SECONDARY)
        self.pdf.cell(0, 8, title, ln=True)
        self.pdf.ln(2)
    
    def _render_kpi_grid(self, kpis: list) -> None:
        """Génère une grille de KPIs."""
        col_width = CONTENT_WIDTH / 2
        row_height = 25
        
        for i, (label, value) in enumerate(kpis):
            x = MARGIN_LEFT + (i % 2) * col_width
            y = self.pdf.get_y() + (i // 2) * row_height
            
            self.pdf.set_xy(x, y)
            
            # Label
            self.pdf.set_font("Helvetica", "", 10)
            self.pdf.set_text_color(*COLOR_GRAY)
            self.pdf.cell(col_width, 5, label, ln=True)
            
            # Valeur
            self.pdf.set_x(x)
            self.pdf.set_font("Helvetica", "B", 14)
            self.pdf.set_text_color(*COLOR_BLACK)
            self.pdf.cell(col_width, 8, value)
    
    def _render_assumptions_table(self, items: list) -> None:
        """Génère un tableau d'hypothèses."""
        self.pdf.set_font("Helvetica", "", 10)
        
        for label, value in items:
            # Label
            self.pdf.set_text_color(*COLOR_GRAY)
            self.pdf.cell(80, 7, label, border=0)
            
            # Valeur
            self.pdf.set_text_color(*COLOR_BLACK)
            self.pdf.cell(60, 7, value, border=0, ln=True)
    
    def _render_waterfall_text(self, items: list) -> None:
        """Génère une représentation textuelle de la cascade."""
        self.pdf.set_font("Helvetica", "", 11)
        
        for i, (label, value) in enumerate(items):
            prefix = "+" if i > 0 and i < len(items) - 1 else "="
            if i == 0:
                prefix = " "
            
            self.pdf.set_text_color(*COLOR_GRAY)
            self.pdf.cell(10, 8, prefix)
            self.pdf.cell(100, 8, label)
            
            self.pdf.set_text_color(*COLOR_BLACK)
            self.pdf.set_font("Helvetica", "B", 11)
            self.pdf.cell(50, 8, value, ln=True)
            self.pdf.set_font("Helvetica", "", 11)


def generate_pitchbook_pdf(data: PitchbookData) -> bytes:
    """
    Fonction raccourcie pour générer un Pitchbook PDF.
    
    Parameters
    ----------
    data : PitchbookData
        Données du Pitchbook.
    
    Returns
    -------
    bytes
        Contenu binaire du PDF.
    
    Raises
    ------
    ImportError
        Si fpdf2 n'est pas installé.
    
    Examples
    --------
    >>> from src.domain.models.pitchbook import PitchbookData
    >>> data = PitchbookData.from_valuation_result(result)
    >>> pdf_bytes = generate_pitchbook_pdf(data)
    >>> with open("report.pdf", "wb") as f:
    ...     f.write(pdf_bytes)
    """
    generator = PitchbookPDFGenerator(data)
    return generator.generate()
