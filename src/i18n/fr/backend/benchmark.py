"""
src/i18n/fr/backend/audit.py

Messages du système d'audit.
Localization for the institutional audit engine.
"""


class AuditCategories:
    """Categories de logs d'audit."""
    DATA = "Données"
    MACRO = "Macro"
    SYSTEM = "Système"
    MODEL = "Modèle"


class AuditMessages:
    """Verdicts et diagnostics générés par l'auditeur institutionnel."""

    # ══════════════════════════════════════════════════════════════════════════
    # BASE AUDITOR — Transversal Data Quality
    # ══════════════════════════════════════════════════════════════════════════

    # Beta Validation
    BETA_MISSING = "Beta manquant."
    BETA_ATYPICAL = r"Beta atypique ({beta:.2f})"
    BETA_EXTREME = r"Le Beta ({beta:.2f}) est statistiquement extrême et peut fausser le coût du capital."
    BETA_EXTREME_HINT = "Envisager un Beta sectoriel ou ajuster manuellement."

    # Data Freshness
    DATA_STALE = r"États financiers obsolètes : dernière mise à jour il y a {months} mois."
    DATA_STALE_HINT = "Les projections s'appuient sur des données qui peuvent ne plus refléter la situation actuelle."

    # Provider Confidence
    PROVIDER_DEGRADED = r"Mode dégradé activé : score de confiance du fournisseur à {score:.0%}."
    PROVIDER_FALLBACK = "Le fournisseur {provider} n'a pas répondu. Utilisation des données de secours."
    PROVIDER_FALLBACK_HINT = "Les données de fallback sectoriel sont utilisées automatiquement."

    # SBC and Solvency
    SBC_DILUTION_MISSING = r"Cohérence Sectorielle : Dilution SBC manquante ou négligeable pour le secteur {sector}."
    SOLVENCY_FRAGILE = r"Solvabilité fragile (ICR: {icr:.2f} < 1.5)"

    # Market Structure
    NET_NET_ANOMALY = "Anomalie : Trésorerie > Capitalisation (Situation Net-Net)"
    LIQUIDITY_SMALL_CAP = "Segment Small-Cap : Risque de liquidité et volatilité."

    # Macro Coherence
    MACRO_G_RF_DIV = r"Divergence macro : g perpétuel ({g:.1%}) > Taux sans risque ({rf:.1%})."
    MACRO_RF_FLOOR = "Paramétrage Rf < 1% : Risque de survalorisation mécanique."

    # ══════════════════════════════════════════════════════════════════════════
    # DCF AUDITOR — Cash Flow Model Validation
    # ══════════════════════════════════════════════════════════════════════════

    # Mathematical Stability
    DCF_WACC_G_SPREAD = r"Spread WACC-g insuffisant ({spread:.2%}) : risque de divergence mathématique."
    DCF_WACC_FLOOR = r"Taux d'actualisation WACC ({wacc:.1%}) excessivement bas."
    DCF_MATH_INSTABILITY = "Instabilité mathématique : Taux g >= WACC."
    DCF_TV_CONCENTRATION = r"Concentration de valeur critique : {weight:.1%} repose sur la TV."

    # Solvency and Leverage
    DCF_LEVERAGE_EXCESSIVE = "Levier financier excessif (> 4x EBIT)."
    DCF_ICR_WARNING = r"Couverture des intérêts insuffisante (ICR: {icr:.2f}x < {threshold}x)."

    # Reinvestment and Growth
    DCF_REINVESTMENT_DEFICIT = r"Déficit de réinvestissement : CapEx à {ratio:.0%} des amortissements."
    DCF_REINVESTMENT_HINT = "Un ratio < 100% suggère un sous-investissement dans l'outil de production."
    DCF_GROWTH_OUTSIDE_NORMS = r"Taux de croissance g ({g:.1%}) hors normes normatives."
    DCF_GROWTH_INCONSISTENT = r"Incohérence de croissance : Phase 1 ({g1:.1%}) est {ratio:.1f}x supérieure à gn ({gn:.1%})."
    DCF_GROWTH_VS_CAGR = r"Croissance projetée ({g:.1%}) significativement supérieure au CAGR historique ({cagr:.1%})."

    # ══════════════════════════════════════════════════════════════════════════
    # DDM AUDITOR — Dividend Sustainability
    # ══════════════════════════════════════════════════════════════════════════

    DDM_PAYOUT_UNSUSTAINABLE = r"Alerte : Le Payout Ratio ({payout:.0%}) > 90% indique un dividende potentiellement non soutenable."
    DDM_PAYOUT_CRITICAL = r"Payout Ratio critique ({payout:.0%}) : distribution supérieure aux bénéfices."

    # ══════════════════════════════════════════════════════════════════════════
    # FCFE AUDITOR — Equity Model Specific
    # ══════════════════════════════════════════════════════════════════════════

    FCFE_HIGH_BORROWING = "Attention : La valorisation repose sur un fort endettement net."

    # ══════════════════════════════════════════════════════════════════════════
    # RIM AUDITOR — Bank Valuation Specific
    # ══════════════════════════════════════════════════════════════════════════

    # Value Creation
    RIM_SPREAD_ROE_KE_NULL = "Spread ROE-Ke quasi nul : absence de création de richesse."
    RIM_SPREAD_ROE_KE_NEGATIVE = r"Spread ROE-Ke négatif ({spread:.1%}) : destruction de valeur actionnariale."
    RIM_SPREAD_ROE_KE_HINT = "Une banque avec ROE < Ke ne crée pas de valeur pour ses actionnaires."

    # Persistence Factor (Omega)
    RIM_OMEGA_OUT_OF_BOUNDS = r"Facteur de persistance ω ({omega:.2f}) hors limites prudentielles [{min:.1f}, {max:.1f}]."
    RIM_OMEGA_EXTREME_HIGH = "ω proche de 1.0 implique un avantage compétitif perpétuel (irréaliste)."
    RIM_OMEGA_EXTREME_LOW = "ω proche de 0 implique une érosion immédiate des surprofits."

    # Asset Quality
    RIM_ASSET_QUALITY_WARNING = "Qualité des actifs à surveiller : volatilité du résultat net élevée."
    RIM_LTD_RATIO_HIGH = r"Ratio Prêts/Dépôts ({ratio:.1%}) élevé : risque de liquidité structurel."

    # Other RIM Messages
    RIM_CASH_SECTOR_NOTE = "Note sectorielle : Trésorerie élevée (Standard Bancaire)."
    RIM_PERSISTENCE_EXTREME = "Hypothèse de persistance des surprofits statistiquement extrême."
    RIM_PAYOUT_EROSION = r"Payout Ratio ({payout:.1%}) > 100% : risque d'érosion des fonds propres."
    RIM_PB_RATIO_HIGH = r"Ratio P/B élevé ({pb:.1f}x) : le modèle RIM perd en pertinence."

    # ══════════════════════════════════════════════════════════════════════════
    # GRAHAM AUDITOR — Defensive Value Specific
    # ══════════════════════════════════════════════════════════════════════════

    # Margin of Safety
    GRAHAM_YIELD_GAP_INSUFFICIENT = r"Écart de rendement insuffisant : E/P ({ep:.1%}) vs AAA ({aaa:.1%})."
    GRAHAM_YIELD_GAP_HINT = "Graham recommande une marge de sécurité significative vs obligations."

    # Graham Multiplier Rule
    GRAHAM_MULTIPLIER_EXCEEDED = r"Multiplicateur Graham (PE×PB = {mult:.1f}) > 22.5 : titre potentiellement surévalué."
    GRAHAM_MULTIPLIER_HINT = "Règle d'or : PE × PB ≤ 22.5 pour un investissement défensif."

    # Growth Prudence
    GRAHAM_GROWTH_PRUDENCE = r"Taux de croissance g Graham ({g:.1%}) hors périmètre de prudence."
    GRAHAM_GROWTH_OPTIMISTIC = r"Croissance ({g:.1%}) > 10% : optimisme excessif pour une approche défensive."
    GRAHAM_GROWTH_HINT = "Benjamin Graham préconisait une prudence absolue sur les projections de croissance."

    # ══════════════════════════════════════════════════════════════════════════
    # MULTIPLES AUDITOR — Relative Valuation Specific
    # ══════════════════════════════════════════════════════════════════════════

    # Cohort Quality
    MULTIPLES_HIGH_DISPERSION = r"Dispersion élevée des multiples (CV: {cv:.0%}) : médiane peu fiable."
    MULTIPLES_HIGH_DISPERSION_HINT = "Un coefficient de variation > 50% indique un groupe de pairs hétérogène."

    # Outlier Detection
    MULTIPLES_OUTLIER_DETECTED = r"Pair aberrant détecté : {ticker} avec {multiple_name} = {value:.1f}x."
    MULTIPLES_OUTLIER_EXCLUDED = r"{count} pairs exclus pour multiples extrêmes (>{threshold}x)."
    MULTIPLES_OUTLIER_HINT = "Les valeurs extrêmes peuvent fausser significativement la triangulation."

    # Cohort Size
    MULTIPLES_COHORT_SMALL = r"Cohorte de pairs réduite ({count} entreprises) : représentativité limitée."
    MULTIPLES_COHORT_HINT = "Un minimum de 5 pairs comparables est recommandé."

    # ══════════════════════════════════════════════════════════════════════════
    # SOTP AUDITOR — Sum of the Parts
    # ══════════════════════════════════════════════════════════════════════════

    SOTP_REVENUE_MISMATCH = r"Incohérence SOTP : écart de {gap:.1%} entre revenus segments et consolidé."
    SOTP_DISCOUNT_AGGRESSIVE = r"Décote de conglomérat ({val:.0%}) hors limites prudentielles (> 25%)."


class AuditEngineTexts:
    """Messages techniques et fallbacks du moteur d'audit."""
    NO_REQUEST_WARNING = "[AuditEngine] ValuationResult sans requête, utilisation du fallback."
    ENGINE_FAILURE_PREFIX = r"Audit Engine Failure: {error}"
    AGGREGATION_FORMULA = "Somme(Score * Poids) * Couverture"
    FALLBACK_RATING = "Erreur"