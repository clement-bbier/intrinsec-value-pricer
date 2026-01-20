"""
core/i18n/fr/backend/audit.py
Messages du systeme d'audit.
"""


class AuditCategories:
    """Categories de logs d'audit."""
    DATA = "Donnees"
    MACRO = "Macro"
    SYSTEM = "Systeme"
    MODEL = "Modele"


class AuditMessages:
    """Verdicts et diagnostics generes par l'auditeur institutionnel."""
    
    # Base Auditor (Data & Macro)
    BETA_MISSING = "Beta manquant."
    BETA_ATYPICAL = "Beta atypique ({beta:.2f})"
    SOLVENCY_FRAGILE = "Solvabilite fragile (ICR: {icr:.2f} < 1.5)"
    NET_NET_ANOMALY = "Anomalie : Tresorerie > Capitalisation (Situation Net-Net)"
    LIQUIDITY_SMALL_CAP = "Segment Small-Cap : Risque de liquidite et volatilite."
    MACRO_G_RF_DIV = "Divergence macro : g perpetuel ({g:.1%}) > Taux sans risque ({rf:.1%})."
    MACRO_RF_FLOOR = "Parametrage Rf < 1% : Risque de survalorisation mecanique."

    # DCF Auditor
    DCF_LEVERAGE_EXCESSIVE = "Levier financier excessif (> 4x EBIT)."
    DCF_REINVESTMENT_DEFICIT = "Deficit de reinvestissement : Capex < 80% des dotations."
    DCF_GROWTH_OUTSIDE_NORMS = "Taux de croissance g ({g:.1%}) hors normes normatives."

    # Diagnostic Events
    RISK_EXTREME_BETA_MSG = "Le Beta ({beta:.2f}) est statistiquement extrême et peut fausser le coût du capital."
    RISK_EXTREME_BETA_HINT = "Envisager un Beta sectoriel ou ajuster manuellement."
    PROVIDER_API_FAILURE_MSG = "Le fournisseur {provider} n'a pas répondu. Utilisation des données de secours."
    PROVIDER_API_FAILURE_HINT = "Les données de fallback sectoriel sont utilisées automatiquement."
    DCF_WACC_FLOOR = "Taux d'actualisation WACC ({wacc:.1%}) excessivement bas."
    DCF_TV_CONCENTRATION = "Concentration de valeur critique : {weight:.1%} repose sur la TV."
    DCF_MATH_INSTABILITY = "Instabilite mathematique : Taux g >= WACC."

    # RIM Auditor
    RIM_CASH_SECTOR_NOTE = "Note sectorielle : Tresorerie elevee (Standard Bancaire)."
    RIM_PERSISTENCE_EXTREME = "Hypothese de persistance des surprofits statistiquement extreme."
    RIM_PAYOUT_EROSION = "Payout Ratio ({payout:.1%}) > 100% : risque d'erosion des fonds propres."
    RIM_SPREAD_ROE_KE_NULL = "Spread ROE-Ke quasi nul : absence de creation de richesse."
    RIM_PB_RATIO_HIGH = "Ratio P/B eleve ({pb:.1f}x) : le modele RIM perd en pertinence."

    # Graham Auditor
    GRAHAM_GROWTH_PRUDENCE = "Taux de croissance g Graham ({g:.1%}) hors perimetre de prudence."

    # Sprint 3
    FCFE_HIGH_BORROWING = "Attention : La valorisation repose sur un fort endettement."
    DDM_PAYOUT_UNSUSTAINABLE = "Alerte : Le Payout Ratio > 100% indique un dividende non soutenable."

    # SOTP
    SOTP_REVENUE_MISMATCH = "Incoherence SOTP : ecart de {gap:.1%} entre revenus segments et consolide."
    SOTP_DISCOUNT_AGGRESSIVE = "Decote de conglomerat ({val:.0%}) hors limites prudentielles (> 25%)."


class AuditEngineTexts:
    """Messages techniques et fallbacks du moteur d'audit."""
    NO_REQUEST_WARNING = "[AuditEngine] ValuationResult sans requete, utilisation du fallback."
    ENGINE_FAILURE_PREFIX = "Audit Engine Failure: {error}"
    AGGREGATION_FORMULA = "Somme(Score * Poids) * Couverture"
    FALLBACK_RATING = "Erreur"
