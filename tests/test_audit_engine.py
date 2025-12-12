from infra.auditing.audit_engine import AuditEngine
from core.models import InputSource


def test_audit_critical_wacc_g_proximity(sample_financials, sample_params):
    """L'audit doit signaler un risque critique si WACC est trop proche de g."""

    # Setup pour provoquer un spread < 1%
    # Ke = 4% + 1.2 * 5% = 10%
    # On met g à 9.5% -> Spread = 0.5% (< 1%)
    sample_params.perpetual_growth_rate = 0.095

    report = AuditEngine.compute_audit(sample_financials, sample_params)

    # 1. Vérification du log critique
    critical_logs = [
        l for l in report.logs
        if l.category == "Cohérence" and l.severity in ["critical", "high"]
    ]
    assert len(critical_logs) > 0, "Aucun log critique trouvé"

    # 2. Vérification de la sanction sur la catégorie Cohérence
    # Le score de cohérence doit avoir pris -50 points (donc être <= 50)
    coherence_score = report.breakdown["Cohérence"]
    assert coherence_score <= 50.0, f"Le score de cohérence ({coherence_score}) n'a pas été assez sanctionné"


def test_audit_manual_mode_trust(sample_financials, sample_params):
    """En mode Manuel, la qualité des données (source) est ignorée (validée par expert)."""
    # On simule une source de données "pourrie" (ex: macro)
    sample_financials.source_growth = "macro"

    # Mais on est en mode MANUEL
    report = AuditEngine.compute_audit(
        sample_financials, sample_params,
        input_source=InputSource.MANUAL
    )

    # Le score Données doit être parfait (100) car l'expert a la main
    data_score = report.breakdown["Données"]
    assert data_score == 100.0

    # Le log "Inputs validés" doit être présent
    assert any("validés" in l.message for l in report.logs)