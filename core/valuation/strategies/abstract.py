import logging
from typing import List
from abc import ABC, abstractmethod
import numpy as np

# --- Imports des modules de calcul (Mis à jour pour Chapitre 5) ---
# Import du nouveau WACC intelligent et des fonctions standard
from core.computation.discounting import calculate_wacc_full_context, calculate_discount_factors, \
    calculate_terminal_value, calculate_equity_value_bridge
# Import du module de projection (votre module existant 'growth.py' est utilisé)
from core.computation.growth import project_flows

from core.models import CompanyFinancials, DCFParameters, DCFResult
from core.exceptions import CalculationError

logger = logging.getLogger(__name__)


class ValuationStrategy(ABC):
    """
    CLASSE ABSTRAITE : SQUELETTE DU MODÈLE DCF.

    Cette classe utilise désormais le WACC Hybride (Gestion des inputs Manuels/Cibles)
    et le modèle de projection Fade-Down.
    """

    @abstractmethod
    def execute(self, financials: CompanyFinancials, params: DCFParameters) -> DCFResult:
        """Exécute la valorisation et retourne le résultat complet."""
        pass

    def _compute_standard_dcf(
            self,
            fcf_start: float,
            financials: CompanyFinancials,
            params: DCFParameters
    ) -> DCFResult:
        """
        Moteur de calcul DCF déterministe standardisé.

        Intègre : WACC Hybride, Projection Fade-Down, Actualisation, Valeur Terminale.
        """
        N = params.projection_years

        # --- ÉTAPE 1 : LE COÛT DU RISQUE (WACC) - UTILISATION DU CONTEXTE COMPLET ---
        try:
            # Utilisation du WACC intelligent qui gère le Ke Manuel et les Poids Cibles
            wacc_context = calculate_wacc_full_context(financials, params)
            wacc = wacc_context.wacc

            # Vérification de la convergence, déjà faite dans MethodConfig, mais réaffirmée ici
            if wacc <= params.perpetual_growth_rate:
                raise CalculationError(
                    f"Échec de convergence Mathématique : WACC ({wacc:.2%}) <= Croissance Terminale ({params.perpetual_growth_rate:.2%})"
                )

        except ValueError as e:
            logger.error(f"Erreur calcul WACC : {e}")
            raise CalculationError(f"Erreur critique lors du calcul du WACC: {e}")

        # --- ÉTAPE 2 : PROJECTION DES FLUX (Fade-Down/Plateau) ---

        projected_fcfs = project_flows(
            base_flow=fcf_start,
            years=N,
            g_start=params.fcf_growth_rate,
            g_term=params.perpetual_growth_rate,
            high_growth_years=params.high_growth_years
        )

        if not projected_fcfs or len(projected_fcfs) != N:
            raise CalculationError("Erreur dans la projection des flux. Nombre d'années projetées incohérent.")

        # --- ÉTAPE 3 : ACTUALISATION ---

        factors = calculate_discount_factors(wacc, N)
        discounted_fcfs = [f * d for f, d in zip(projected_fcfs, factors)]
        sum_discounted = float(np.sum(discounted_fcfs))

        # --- ÉTAPE 4 : VALEUR TERMINALE (TV) ---

        tv = calculate_terminal_value(projected_fcfs[-1], wacc, params.perpetual_growth_rate)
        discounted_tv = tv * factors[-1]

        # --- ÉTAPE 5 : BRIDGE EV -> EQUITY ---

        ev = sum_discounted + discounted_tv
        eq_val = calculate_equity_value_bridge(
            enterprise_value=ev,
            total_debt=financials.total_debt,
            cash=financials.cash_and_equivalents
        )

        # --- ÉTAPE 6 : RESULTAT PAR ACTION ---

        if financials.shares_outstanding <= 0:
            raise CalculationError("Nombre d'actions invalide (<= 0).")

        iv_share = eq_val / financials.shares_outstanding

        # --- ÉTAPE 7 : CONSTRUCTION DU RÉSULTAT ---

        return DCFResult(
            wacc=wacc,
            # Utilisation des résultats du contexte WACC complet pour l'audit/affichage
            cost_of_equity=wacc_context.cost_of_equity,
            after_tax_cost_of_debt=wacc_context.cost_of_debt_after_tax,
            projected_fcfs=projected_fcfs,
            discount_factors=factors,
            sum_discounted_fcf=sum_discounted,
            terminal_value=tv,
            discounted_terminal_value=discounted_tv,
            enterprise_value=ev,
            equity_value=eq_val,
            intrinsic_value_per_share=iv_share
        )