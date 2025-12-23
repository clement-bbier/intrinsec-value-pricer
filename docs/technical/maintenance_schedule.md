# 📅 Calendrier de Maintenance & Mise à Jour des Constantes

Ce document recense l'ensemble des paramètres financiers "hardcodés" (constantes) qui nécessitent une surveillance périodique pour garantir la fiabilité des valorisations en **Mode Auto** et la pertinence des suggestions en **Mode Expert**.

> **Note :** En cas de crise majeure (krach > -10%, changement de taux directeur surprise), une mise à jour immédiate hors calendrier est requise.

---

## 🚨 Fréquence : MENSUELLE (Chaque 1er du mois)
**Temps estimé : 5 min**

### 1. Taux Sans Risque (Risk-Free Rate)
* **Fichier Cible :** `app/ui_components/ui_inputs_expert.py`
* **Variable :** `DEFAULT_RF`
* **Source de Vérité :** [Yahoo Finance - Treasury Yield 10 Years (^TNX)](https://finance.yahoo.com/quote/%5ETNX)
* **Procédure :**
    1.  Relever le dernier cours de clôture (ex: 4.25).
    2.  Convertir en décimale (ex: 0.0425).
    3.  Mettre à jour la variable.
* **Seuil de déclenchement :** Écart > 0.10% (10 bps) par rapport à la valeur actuelle.

### 2. Taux Sans Risque Zone Euro (Fallback)
* **Fichier Cible :** `infra/macro/yahoo_macro_provider.py`
* **Variable :** Valeur de fallback dans `get_macro_context` (ex: `0.030`).
* **Source de Vérité :** [Trading Economics - Germany 10Y Bond Yield](https://tradingeconomics.com/germany/government-bond-yield)
* **Procédure :** Si le taux allemand s'écarte de plus de 0.5% du fallback, mettre à jour pour éviter des WACC absurdes en cas de panne Yahoo.

---

## 📅 Fréquence : SEMESTRIELLE (Janvier & Juillet)
**Temps estimé : 15 min**

### 3. Prime de Risque Marché (Equity Risk Premium)
* **Fichier Cible :** `app/ui_components/ui_inputs_expert.py`
* **Variable :** `DEFAULT_MRP`
* **Source de Vérité :** [Damodaran Online - Implied ERP](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html)
* **Procédure :**
    1.  Chercher "Implied Equity Risk Premium (US)".
    2.  Arrondir à 0.25% près (ex: 4.62% -> 4.75%).
    3.  Mettre à jour.

### 4. Spreads de Crédit (Coût de la Dette)
* **Fichier Cible :** `app/ui_components/ui_inputs_expert.py`
* **Variable :** `DEFAULT_COST_DEBT`
* **Source de Vérité :** [FRED - Moody's Seasoned Baa Corporate Bond Yield](https://fred.stlouisfed.org/series/DBAA)
* **Procédure :** Relever le taux Baa. S'il est très différent de `RF + 1.5%`, mettre à jour.

### 5. Risques Pays (Country Risk Premiums)
* **Fichier Cible :** `infra/ref_data/country_matrix.py`
* **Variable :** `COUNTRY_CONTEXT["France"]["market_risk_premium"]`, etc.
* **Source de Vérité :** [Damodaran - Country Risk Premiums](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html)
* **Procédure :** Vérifier uniquement les pays majeurs (US, France, Allemagne, Chine, Japon).

---

## 🏛️ Fréquence : ANNUELLE (Janvier)
**Temps estimé : 20 min**

### 6. Fiscalité (Tax Rates)
* **Fichiers Cibles :**
    * `app/ui_components/ui_inputs_expert.py` (`DEFAULT_TAX`)
    * `infra/ref_data/country_matrix.py` (Dictionnaire des pays)
* **Source de Vérité :** [KPMG Corporate Tax Rates Table](https://home.kpmg/xx/en/home/services/tax/tax-tools-and-resources/tax-rates-online/corporate-tax-rates-table.html)
* **Procédure :** Vérifier si les taux légaux ont changé (Loi de Finances) pour les US (Fed + State ~25%) et la France.

### 7. Cibles d'Inflation (Croissance Perpétuelle)
* **Fichier Cible :** `app/ui_components/ui_inputs_expert.py`
* **Variable :** `DEFAULT_PERP`
* **Source de Vérité :** Communiqués de la FED et de la BCE.
* **Procédure :** Maintenir à 2.0% sauf changement de paradigme économique majeur (ex: acceptation officielle d'une inflation à 3%).

---

## ⚠️ Fréquence : ÉVÉNEMENTIELLE (3-5 ans)

### 8. Tables de Spreads Synthétiques
* **Fichier Cible :** `core/computation/financial_math.py`
* **Variables :** `SPREADS_LARGE_CAP`, `SPREADS_SMALL_MID_CAP`
* **Source de Vérité :** [Damodaran - Ratings, Spreads and Interest Coverage Ratios](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.htm)
* **Procédure :** Ces tables changent rarement. Vérifier si les seuils de ratio de couverture (Interest Coverage Ratio) ont été redéfinis par les agences de notation.

### 9. Pondération de l'Audit
* **Fichier Cible :** `infra/auditing/audit_engine.py`
* **Variable :** `MODE_WEIGHTS`
* **Procédure :** Réviser uniquement si la philosophie de risque de l'application change (ex: devenir plus tolérant sur la qualité des données).s