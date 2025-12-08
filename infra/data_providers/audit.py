from dataclasses import dataclass, field
from typing import List, Dict
import math

from core.models import CompanyFinancials, DCFParameters, ValuationMode


@dataclass
class AuditResult:
    score: float
    rating: str
    ui_details: List[Dict]  # Pour le tableau UI
    terminal_logs: List[str]  # Pour les logs console


def audit_valuation_model(
        financials: CompanyFinancials,
        params: DCFParameters,
        mode: ValuationMode = ValuationMode.SIMPLE_FCFF  # On prend en compte le mode
) -> AuditResult:
    """
    AUDIT 2.0 : Moteur d'analyse dynamique des risques.
    Gère la magnitude des écarts, les bonus (Green Flags) et le contexte de la méthode.
    """
    score = 100.0
    ui_details = []
    terminal_logs = []
    warnings = financials.warnings

    # --- Helpers internes pour la gestion des points ---

    def add_entry(points: int, category: str, reason: str, context: str = "", severity: str = "medium"):
        """Ajoute une entrée (Bonus ou Malus) au rapport."""
        nonlocal score
        score += points  # points peut être négatif (malus) ou positif (bonus)

        # UI Structure
        ui_details.append({
            "category": category,
            "penalty": points,  # On garde le signe pour l'affichage (+5 ou -10)
            "reason": reason,
            "context": context,
            "severity": severity
        })

        # Log Structure
        icon = "✅" if points >= 0 else "🔻"
        sign = "+" if points >= 0 else ""
        log_msg = f"   {icon} [{sign}{points} pts] [{category.upper()}] {reason}"
        if context:
            log_msg += f" ({context})"
        terminal_logs.append(log_msg)

    # =========================================================================
    # 1. ANALYSE DE LA QUALITÉ DES DONNÉES (INPUTS)
    # =========================================================================

    # --- A. Source du Cash Flow (Critique pour Méthode 1 & 2) ---
    if any("FCF Source : TTM" in w for w in warnings):
        add_entry(0, "Données", "Flux de trésorerie récents (TTM)", "Donnée < 3 mois")
    elif any("FCF Source : Moyenne Pondérée" in w for w in warnings):
        # Moins grave pour la méthode 2 car c'est le but, mais on note le lissage
        if mode == ValuationMode.FUNDAMENTAL_FCFF:
            add_entry(-5, "Données", "Lissage historique actif", "Normalisation sur 5 ans")
        else:
            add_entry(-10, "Données", "Utilisation de flux lissés/reconstitués", "Moins précis que TTM")
    elif any("FCF Source : Dernier Bilan Annuel" in w for w in warnings):
        add_entry(-20, "Données", "Flux basés sur un bilan annuel daté", "Risque d'obsolescence (> 12 mois)")
    else:
        add_entry(-50, "Données", "Aucun flux fiable trouvé", "Estimation Pure - Modèle Invalide", severity="high")

    # --- B. Source de la Croissance (Le Levier) ---
    if any("Croissance : Basée sur estimations analystes" in w for w in warnings):
        add_entry(5, "Croissance", "Consensus Analystes", f"Taux: {params.fcf_growth_rate:.1%}")
    elif any("Croissance : Basée sur l'historique" in w for w in warnings):
        add_entry(-10, "Croissance", "Basée sur le passé (CAGR)", "Ne garantit pas le futur")
    elif any("Croissance : Basée sur les fondamentaux" in w for w in warnings):
        add_entry(-15, "Croissance", "Estimation théorique (ROE x Rétention)", "Hypothèse comptable")
    else:
        add_entry(-25, "Croissance", "Fallback Macro (PIB)", "Aucune donnée spécifique", severity="high")

    # --- C. Structure Financière (Dette) ---
    if any("Coût dette : Utilisation de la moyenne sectorielle" in w for w in warnings):
        add_entry(-5, "Structure", "Coût de la dette générique", f"Secteur: {financials.sector}")
    else:
        # Bonus si on a calculé un vrai coût de la dette cohérent
        if financials.interest_expense > 0 and financials.total_debt > 0:
            add_entry(2, "Structure", "Coût de la dette réel vérifié", f"Taux: {params.cost_of_debt:.1%}")

    # =========================================================================
    # 2. ANALYSE DE LA COHÉRENCE (SANITY CHECKS DYNAMIQUES)
    # =========================================================================

    # --- A. Cohérence Bilan ---
    if financials.interest_expense > 10_000_000 and financials.total_debt < 1_000_000:
        add_entry(-20, "Cohérence", "Intérêts payés élevés sans dette au bilan", "Donnée douteuse", severity="high")

    # --- B. Reverse DCF (Le Reality Check Dynamique) ---
    # On pondère la pénalité selon l'énormité de l'écart
    if financials.implied_growth_rate is not None:
        spread = financials.implied_growth_rate - params.fcf_growth_rate
        abs_spread = abs(spread)

        market_view = f"Marché {financials.implied_growth_rate:.1%} vs Modèle {params.fcf_growth_rate:.1%}"

        if abs_spread < 0.02:  # Écart < 2%
            add_entry(10, "Réalité", "Modèle parfaitement aligné avec le marché", "Consensus fort")
        elif abs_spread < 0.05:  # Écart < 5%
            add_entry(5, "Réalité", "Modèle cohérent avec le prix", "Écart mineur")
        elif abs_spread > 0.20:  # Écart > 20% (Enorme)
            add_entry(-30, "Réalité", "Déconnexion critique avec le prix", market_view, severity="high")
        elif abs_spread > 0.10:  # Écart > 10%
            add_entry(-15, "Réalité", "Désaccord significatif avec le marché", market_view)
        # Entre 5% et 10%, zone grise, pas de point

    # =========================================================================
    # 3. PROFIL DE RISQUE DE L'ENTREPRISE (STABILITÉ)
    # =========================================================================

    # Volatilité (Beta)
    if financials.beta > 2.0:
        add_entry(-20, "Stabilité", "Volatilité extrême", f"Beta: {financials.beta:.2f}", severity="high")
    elif financials.beta > 1.5:
        add_entry(-10, "Stabilité", "Volatilité élevée", f"Beta: {financials.beta:.2f}")
    elif financials.beta < 0.8:
        add_entry(5, "Stabilité", "Action défensive / Peu volatile", f"Beta: {financials.beta:.2f}")

    # =========================================================================
    # 4. RATIO D'HYPOTHÈSES (ASSUMPTION DENSITY)
    # =========================================================================
    # On compte combien de fois on a utilisé un fallback majeur
    fallback_count = 0
    if any("sectorielle" in w for w in warnings): fallback_count += 1
    if any("Fallback" in w for w in warnings): fallback_count += 1
    if any("Annuel" in w for w in warnings): fallback_count += 1

    if fallback_count == 0:
        add_entry(5, "Fiabilité", "100% Données Spécifiques", "Aucune moyenne sectorielle utilisée")
    elif fallback_count >= 2:
        add_entry(-5 * fallback_count, "Fiabilité", "Forte dépendance aux estimations génériques",
                  f"{fallback_count} variables estimées")

    # --- FINALISATION ---
    final_score = max(0.0, min(100.0, score))  # Bornage 0-100

    rating = "INCONNU"
    if final_score >= 90:
        rating = "EXCELLENT (A+)"
    elif final_score >= 80:
        rating = "TRÈS FIABLE (A)"
    elif final_score >= 60:
        rating = "MODÉRÉ (B)"
    elif final_score >= 40:
        rating = "SPÉCULATIF (C)"
    else:
        rating = "DANGEREUX (D)"

    return AuditResult(
        score=final_score,
        rating=rating,
        ui_details=ui_details,
        terminal_logs=terminal_logs
    )