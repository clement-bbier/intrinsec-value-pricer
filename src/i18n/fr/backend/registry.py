"""
core/i18n/fr/backend/registry.py
Labels et descriptions du registre Glass Box.
"""


class RegistryTexts:
    """Labels et descriptions pedagogiques du registre Glass Box."""

    # DCF (Approche Entite - FCFF)
    FCFE_EQUITY_VALUE = "Valeur Totale des Capitaux Propres"
    AUDIT_TECH_DETAIL_D = "Détail technique du calcul spécifique au modèle."
    VALUE_PER_SHARE_L = "Valeur par action"
    DATE_LABEL = "Date"
    REAL_PRICE_L = "Prix réel"
    HISTORICAL_IV_L = "IV historique"
    DCF_EV_LA = "Valeur d'entreprise"
    DCF_IV_LA = "Valeur intrinsèque"
    FCFF_STANDARD_L = "DCF Standard (FCFF)"
    FCFF_GROWTH_L = "DCF Growth (Revenue-Driven)"
    FCFF_NORM_L = "DCF Fondamental (Normalisé)"
    FCFE_L = "DCF Equity (FCFE)"
    DDM_L = "Modèle Gordon-Shapiro (DDM)"

    SBC_LABEL = "Ajustement Dilution (SBC)"
    DCF_FCF_BASE_L = "Ancrage du Flux d'Exploitation (FCF0)"
    DCF_FCF_BASE_D = "Flux de tresorerie disponible pour l'entreprise avant service de la dette."

    DCF_FCF_NORM_L = "Ancrage du Flux Normalise"
    DCF_FCF_NORM_D = "Flux lisse sur un cycle complet pour neutraliser la volatilite operationnelle."

    DCF_STABILITY_L = "Controle de Viabilite Financiere"
    DCF_STABILITY_D = "Validation de la capacite de l'actif economique a generer des flux positifs."

    DCF_WACC_L = "Cout Moyen Pondere du Capital (WACC)"
    DCF_WACC_D = "Taux d'actualisation refletant le cout global du capital."

    DCF_KE_L = "Cout des Fonds Propres (Ke)"
    DCF_KE_D = "Taux de rendement exige par les actionnaires, calcule via le modele CAPM."

    DCF_PROJ_L = "Projection des Flux Futurs"
    DCF_PROJ_D = "Modelisation de la croissance des flux sur l'horizon explicite."

    DCF_TV_GORDON_L = "Valeur Terminale (Gordon Growth)"
    DCF_TV_GORDON_D = r"Estimation de la valeur de perpetuite basee sur un taux de croissance stable."

    DCF_TV_MULT_L = "Valeur Terminale (Multiple de Sortie)"
    DCF_TV_MULT_D = "Estimation de la valeur de revente theorique basee sur un multiple."

    DCF_EV_L = "Valeur de l'Outil de Production (EV)"
    DCF_EV_D = "Somme actualisee des flux d'exploitation et de la valeur terminale."

    DCF_BRIDGE_L = "Pont de Valeur (Equity Bridge)"
    DCF_BRIDGE_D = "Passage de la Valeur d'Entreprise a la Valeur Actionnariale."

    DCF_IV_L = "Valeur Intrinseque par Action"
    DCF_IV_D = "Prix theorique final estime pour un titre ordinaire."

    # FCFE
    FCFE_BASE_L = "Reconstruction du Flux Actionnaire (FCFE0)"
    FCFE_BASE_D = "Calcul du flux residuel : Resultat Net + Amortissements - CapEx - BFR + Net Borrowing."
    FCFE_DEBT_ADJ_L = "Audit du Levier Actionnaire"
    FCFE_DEBT_ADJ_D = "Analyse de la contribution de l'endettement net."

    # DDM
    DDM_BASE_L = r"Ancrage du Dividende de Reference (D0)"
    DDM_BASE_D = "Somme des dividendes verses sur les 12 derniers mois."
    DDM_GROWTH_L = "Dynamique de Distribution"
    DDM_GROWTH_D = "Modelisation de la croissance des dividendes."

    # GROWTH
    GROWTH_REV_BASE_L = "Chiffre d'Affaires d'Ancrage"
    GROWTH_REV_BASE_D = "Revenu TTM utilise comme socle pour la projection."
    GROWTH_MARGIN_L = "Convergence des Marges Operationnelles"
    GROWTH_MARGIN_D = "Simulation de l'evolution des marges vers un profil normatif."

    # RIM
    RIM_BV_L = "Actif Net Comptable d'Ouverture"
    RIM_BV_D = "Valeur des capitaux propres au bilan au depart du modele."
    RIM_KE_L = "Cout d'Opportunite des Fonds Propres"
    RIM_KE_D = "Seuil de rentabilite minimum pour justifier la creation de valeur."
    RIM_RI_L = "Calcul du Profit Residuel (Surprofit)"
    RIM_RI_D = r"Richesse creee au-dela du cout du capital immobilise."
    RIM_TV_L = "Valeur Terminale de Persistance"
    RIM_TV_D = "Estimation de la vitesse de degradation du surprofit."
    RIM_IV_L = "Valeur Intrinseque RIM (Ohlson)"
    RIM_IV_D = "Somme de la Valeur Comptable et de la valeur actuelle des surprofits futurs."
    RIM_PAYOUT_L = "Politique de Retention des Profits"
    RIM_PAYOUT_D = "Impact de la distribution sur la croissance future."
    RIM_EPS_PROJ_L = "Projection des Benefices Net (NI)"
    RIM_EPS_PROJ_D = "Trajectoire attendue du resultat net par action."

    # GRAHAM
    GRAHAM_EPS_L = "Capacite Beneficiaire Normalisee (EPS)"
    GRAHAM_EPS_D = "Benefice par action ajuste pour refleter la rentabilite recurrente."
    GRAHAM_MULT_L = "Multiplicateur de Croissance Graham"
    GRAHAM_MULT_D = "Prime de croissance theorique basee sur la formule revisee de 1974."
    GRAHAM_IV_L = "Valeur Graham AAA"
    GRAHAM_IV_D = "Prix de reference ajuste par le rendement des obligations AAA."

    # Monte Carlo
    MC_INIT_L = "Initialisation & Lois de Probabilite"
    MC_INIT_D = r"Parametrage des distributions normales pour les variables critiques."
    MC_SAMP_L = "Simulation Multivariee (Cholesky)"
    MC_SAMP_D = "Generation de scenarios correles pour respecter la coherence economique."
    MC_FILT_L = "Controle de Convergence Statistique"
    MC_FILT_D = r"Filtrage des scenarios mathematiquement divergents."
    MC_MED_L = "Valeur Centrale Probabiliste (P50)"
    MC_MED_D = "Point median de la distribution des valeurs intrinseques simulees."
    MC_SENS_L = "Analyse de Correlation des Risques"
    MC_SENS_D = "Mesure de la sensibilite de la valeur au couple Risque/Croissance."
    MC_STRESS_L = "Test de Resistance (Stress Test)"
    MC_STRESS_D = "Scenario extreme simulant une rupture de croissance."
    MC_Y0_UNCERTAINTY_L = r"Incertitude sur le Flux d'Ancrage (Y0)"
    MC_Y0_UNCERTAINTY_D = "Integration de l'erreur type sur le dernier flux reporte."

    # AUDIT
    AUDIT_BETA_L = "Validation du Risque Systematique (Beta)"
    AUDIT_BETA_D = "Verifie que le Beta utilise est coherent avec le profil sectoriel."
    AUDIT_ICR_L = "Couverture des Interets (Solvabilite)"
    AUDIT_ICR_D = "Capacite de l'entreprise a honorer sa dette via son resultat operationnel."
    AUDIT_CASH_L = "Position Net-Net"
    AUDIT_CASH_D = "Alerte si la tresorerie nette depasse la valeur de marche."
    AUDIT_LIQ_L = "Risque de Liquidite de Marche"
    AUDIT_LIQ_D = "Analyse de la profondeur de marche pour les petites capitalisations."
    AUDIT_LEV_L = "Intensite du Levier Financier"
    AUDIT_LEV_D = "Evaluation du poids de la dette par rapport a la capacite de remboursement."
    AUDIT_MACRO_L = "Alignement Macro-economique"
    AUDIT_MACRO_D = "Verifie que la croissance perpetuelle ne depasse pas le PIB nominal attendu."
    AUDIT_RF_L = "Coherence du Taux Sans Risque (Rf)"
    AUDIT_RF_D = "Alerte si le taux sans risque est deconnecte des realites monetaires."
    AUDIT_REINV_L = "Taux de Reinvestissement Industriel"
    AUDIT_REINV_D = "Verifie si le CapEx est suffisant pour maintenir l'outil de production."
    AUDIT_GLIM_L = "Plafond de Croissance soutenable"
    AUDIT_GLIM_D = "Alerte sur les hypotheses de croissance depassant les standards."
    AUDIT_PAY_L = "Soutenabilite du Dividende"
    AUDIT_PAY_D = "Verifie que le Payout Ratio ne compromet pas le reinvestissement."
    AUDIT_WACC_L = "Validation du Plancher d'Actualisation"
    AUDIT_WACC_D = "Alerte si le cout du capital est anormalement bas."
    AUDIT_TVC_L = "Poids de la Valeur Terminale"
    AUDIT_TVC_D = "Mesure la dependance de la valorisation a l'hypothese d'eternite."
    AUDIT_G_WACC_L = "Divergence Gordon-Shapiro"
    AUDIT_G_WACC_D = "Verifie la condition critique d'existence du modele (r > g)."
    AUDIT_SPREAD_L = "Spread de Creation de Valeur (ROE - ke)"
    AUDIT_SPREAD_D = "Mesure l'ecart de rentabilite par rapport au cout d'opportunite."
    AUDIT_PB_L = "Pertinence du Modele RIM (P/B Ratio)"
    AUDIT_PB_D = "Analyse si la valeur boursiere est trop deconnectee de la valeur comptable."
    AUDIT_UNK_L = "Test de Fiabilite Specifique"
    AUDIT_UNK_D = "Diagnostic technique non reference dans le catalogue standard."

    # AJOUTS POUR HARMONISATION
    HAMADA_L = "Ajustement du Bêta (Hamada)"
    HAMADA_D = "Réendettement du bêta selon la structure cible de l'entreprise."

    SBC_L = "Ajustement Dilution SBC"
    SBC_D = "Impact de la rémunération en actions sur la valeur par action future."

    EQUITY_DIRECT_D = "Valeur directe des fonds propres issue de l'actualisation."

    PE_LABEL = "Multiples P/E"
    EBITDA_LABEL = "Multiples EV/EBITDA"
    TRIANG_LABEL = "Synthèse Triangulée"
    PEERS_HYP_LABEL = "Panel de Comparables"