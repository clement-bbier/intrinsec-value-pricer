"""
src/i18n/fr/backend/models.py
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelValidationTexts:
    SCENARIO_PROBABILITIES_SUM_ERROR: str = (
        "La somme des probabilités (Bull+Base+Bear) doit être égale à 1.0."
    )

MODEL_VALIDATION_TEXTS = ModelValidationTexts()

class ModelTexts:
    DEFAULT_NAME = "Entité Inconnue"

class KPITexts:
    LABEL_DEBT = "Dette Totale"
    LABEL_CASH = "Trésorerie & Équivalents"
    LABEL_MINORITIES = "Intérêts Minoritaires"
    LABEL_PENSIONS = "Provisions pour Retraites"
    LABEL_EQUITY = "Valeur des Capitaux Propres"

class SOTPTexts:
    """Textes spécifiques à la méthode Somme des Parties."""
    TITLE = "Analyse Somme des Parties (SOTP)"
    SEGMENT_VALUATION = "Valorisation par Segment"
    IMPLIED_EV = "Valeur d'Entreprise Implicite"
    CONGLOMERATE_DISCOUNT = "Décote de Conglomérat"
    SUM_OF_PARTS = "Somme des Parties"

    # Champs complétés pour le Glass Box
    FORMULA_BRIDGE = "Equity = Σ(Segments) - Dette Nette - Décote"
    INTERP_CONSOLIDATION = "Agrégation des valorisations individuelles par Business Unit."
    FORMULA_CONSOLIDATION = r"EV_{SOTP} = (\sum V_{segment}) \times (1 - \text{Discount})"
    STEP_LABEL_CONSOLIDATION = "Consolidation des Parties"
    LBL_DISCOUNT = "Décote de Holding"
    LBL_RAW_EV_SUM = "Somme Brute des Segments"