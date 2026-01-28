"""
core/i18n/fr/backend/errors.py
Messages d'erreurs et diagnostics.
"""


class DiagnosticTexts:
    """Messages du registre de diagnostic et des exceptions."""

    # Divergence Gordon
    RISK_SBC_RECOMMENDATION = (
        "Appliquer le CAGR historique des actions en circulation sur les 3-5 dernières "
        "années ou utiliser une estimation normative sectorielle (typiquement 1% à 3%)."
    )
    RISK_SBC_STAT_RISK = (
        "L'omission de la croissance structurelle du nombre d'actions dans le secteur "
        r"{sector} (SBC) ignore la dilution future des actionnaires actuels. Cela conduit "
        "systématiquement à une surestimation de la valeur intrinsèque par action."
    )
    PARAM_SBC_LABEL = r"Facteur de Dilution SBC ({sector})"
    MODEL_G_DIV_MSG = r"ERREUR DE CONVERGENCE : Le taux de croissance g ({g:.2%}) est >= au Ke/WACC ({wacc:.2%})."
    MODEL_G_DIV_HINT = "Une entreprise ne peut croitre plus vite que son cout du capital a l'infini."

    # Instabilite Monte Carlo
    MODEL_MC_INST_MSG = "INSTABILITE CRITIQUE : Seuls {valid_ratio:.1%} des scenarios sont valides."
    MODEL_MC_INST_HINT = r"Le modele diverge trop souvent. Diminuez la Vol. gn."

    # Metriques manquantes
    DATA_MISSING_CORE_MSG = "Metrique critique manquante : {metric_name}."
    DATA_MISSING_CORE_HINT = "Utilisez le mode Expert pour saisir manuellement cette donnee."
    DATA_PEER_SKIP_MSG = r"Pair '{ticker}' ignore : Multiples aberrants ou donnees incompletes."

    # Risques
    RISK_EXCESSIVE_GROWTH_MSG = "Croissance projetee aggressive ({g:.2%})."
    RISK_EXCESSIVE_GROWTH_HINT = "Verifiez si ce taux est soutenable face a la moyenne du secteur."
    DATA_NEGATIVE_BETA_MSG = "Beta atypique detecte ({beta:.2f})."
    DATA_NEGATIVE_BETA_HINT = "Un Beta negatif est rare ; verifiez la source."

    # Erreurs Systeme
    SYSTEM_CRASH_MSG = "Une defaillance technique inattendue a ete detectee."
    SYSTEM_CRASH_HINT = "Verifiez votre connexion internet ou tentez une requete simplifiee."

    # Exceptions Ticker
    TICKER_NOT_FOUND_MSG = "Le ticker '{ticker}' est introuvable sur Yahoo Finance."
    TICKER_NOT_FOUND_HINT = "Verifiez l'orthographe (ex: AIR.PA pour Airbus)."

    DATA_FIELD_MISSING_YEAR = "Donnee manquante pour {ticker} : '{field}' pour l'annee {year}."
    DATA_FIELD_MISSING_GENERIC = "Donnee fondamentale manquante pour {ticker} : '{field}' est vide ou invalide."
    DATA_FIELD_HINT = "Cette entreprise ne publie peut-etre pas cette donnee."

    # Infrastructure
    PROVIDER_FAIL_MSG = "Echec de connexion au fournisseur {provider}."
    PROVIDER_FAIL_HINT = "Verifiez votre connexion internet."

    # Logique Modele
    MODEL_LOGIC_MSG = "Incoherence dans le modele {model} : {issue}"
    MODEL_LOGIC_HINT = "Verifiez vos hypotheses de croissance ou de taux d'actualisation."
    CALC_GENERIC_HINT = "Verifiez les donnees d'entree dans le Terminal Expert."

    UNKNOWN_STRATEGY_MSG = "La strategie pour {mode} n'est pas enregistree."
    UNKNOWN_STRATEGY_HINT = "Verifiez le registre des strategies."
    STRATEGY_CRASH_MSG = "Echec critique du moteur : {error}"
    STRATEGY_CRASH_HINT = "Redemarrez l'analyse ou contactez le support technique."

    # FCFE & DDM
    FCFE_NEGATIVE_MSG = "FLUX ACTIONNAIRE NEGATIF ({val:,.0f}) : Modele inapplicable."
    FCFE_NEGATIVE_HINT = "Le remboursement de la dette excede la generation de cash."
    DDM_PAYOUT_MSG = "DECAPITALISATION : Le taux de distribution ({payout:.1%}) depasse 100%."
    DDM_PAYOUT_HINT = "L'entreprise distribue plus que ses benefices."
    MODEL_SGR_DIV_MSG = r"CROISSANCE INSOUTENABLE : g ({g:.1%}) > SGR ({sgr:.1%})."
    MODEL_SGR_DIV_HINT = "La croissance depasse la capacite d'autofinancement."

    # SBC / Dilution Diagnostics
    RISK_MISSING_SBC_MSG = "Absence de dilution SBC pour le secteur {sector}."
    RISK_MISSING_SBC_HINT = "Les entreprises Tech rémunèrent massivement en actions. Envisagez un taux de 1.5% à 3%."
    RISK_MISSING_SBC_RISK = (
        "Ignorer la dilution SBC surévalue artificiellement le prix par action cible "
        "en ignorant l'augmentation future du nombre de parts (Share Count)."
    )
    RISK_MISSING_SBC_RECO = "Appliquer le taux historique ou la moyenne sectorielle pour {sector}."

    # Paramètre labels pour le FinancialContext
    LBL_ANNUAL_DILUTION = "Taux de dilution annuel (SBC)"


class CalculationErrors:
    """Messages d'erreurs leves lors des phases de calcul."""
    CONTRACT_VIOLATION = "Le contrat de sortie n'est pas respecte pour {cls}."
    INVALID_SHARES = "Nombre d'actions en circulation invalide (<= 0)."
    MISSING_BV = "Book Value par action requise et > 0."
    MISSING_EPS_RIM = "EPS requis pour projeter les profits residuels."
    MISSING_REV = "Chiffre d'affaires (Revenue) requis pour ce modele."
    INVALID_SHARES_SIMPLE = "Nombre d'actions invalide."
    MISSING_FCF_NORM = "FCF normalise indisponible (fcf_fundamental_smoothed manquant)."
    NEGATIVE_FCF_NORM = "Flux normalise negatif : l'entreprise ne genere pas de valeur sur son cycle."
    MISSING_EPS_GRAHAM = "EPS strictement positif requis pour le modele de Graham."
    INVALID_AAA = "Le rendement obligataire AAA (Y) doit etre > 0."
    MISSING_FCF_STD = "FCF de base indisponible (fcf_last manquant ou nul)."
    INVALID_DISCOUNT_RATE = "Taux d'actualisation invalide : {rate:.2%}"
    CONVERGENCE_IMPOSSIBLE = "Convergence impossible : Taux ({rate:.2%}) <= Croissance ({g:.2%})"
    MANUAL_OVERRIDE_LABEL = "Surcharge manuelle : {wacc:.2%}"
    NEGATIVE_EXIT_MULTIPLE = "Le multiple de sortie ne peut pas etre negatif."
    NEGATIVE_FCFE = "Le flux FCFE est negatif. Le modele est inapplicable."
    MISSING_NET_BORROWING = "Donnee de variation de dette (Net Borrowing) manquante."
    INVALID_DIVIDEND = "Dividende de base nul ou invalide pour le modele DDM."
    NEGATIVE_FLUX_AUTO = "Impossible de valoriser via {model} en mode Auto : le flux de base est negatif ou nul ({val:.2f}). Veuillez utiliser un modele alternatif (RIM, Multiples) ou saisir un flux normatif en mode Expert."
    RIM_NEGATIVE_BV = "Le modele RIM necessite une valeur comptable positive pour calculer le revenu residuel."
    NEGATIVE_PE_RATIO = "Le multiple P/E doit être strictement positif."
