"""
tests/unit/test_streamlit_adapters.py
Suite de tests pour les adaptateurs UI (Streamlit).
Couverture cible : 100%
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.adapters.streamlit_adapters import (
    StreamlitProgressHandler,
    StreamlitResultRenderer
)
from src.models import ValuationResult

# Cible de patch pour Streamlit
ST_PATCH = 'app.adapters.streamlit_adapters.st'

class TestStreamlitProgressHandler:
    """Tests pour le gestionnaire de progression (st.status)."""

    @patch(ST_PATCH)
    def test_progress_lifecycle_nominal(self, mock_st):
        """Vérifie le cycle complet : Start -> Update -> Complete."""
        mock_container = MagicMock()
        mock_st.status.return_value = mock_container

        handler = StreamlitProgressHandler()
        handler.start_status("Initialisation")
        handler.update_status("Calcul en cours...")
        handler.complete_status("Succès", state="complete")

        # Vérifications
        mock_st.status.assert_called_once_with("Initialisation", expanded=True)
        mock_container.write.assert_called_with("Calcul en cours...")
        mock_container.update.assert_called_with(
            label="Succès", state="complete", expanded=False
        )

    @patch(ST_PATCH)
    def test_progress_error_branch(self, mock_st):
        """Vérifie le passage en mode erreur du statut."""
        mock_container = MagicMock()
        mock_st.status.return_value = mock_container

        handler = StreamlitProgressHandler()
        handler.start_status("Run")
        handler.error_status("Crash")

        mock_container.update.assert_called_with(
            label="Crash", state="error", expanded=True
        )

    @patch(ST_PATCH)
    def test_context_manager_exception(self, mock_st):
        """Vérifie que le __exit__ capture les erreurs et met à jour le statut."""
        mock_container = MagicMock()
        mock_st.status.return_value = mock_container

        handler = StreamlitProgressHandler()

        # On simule un crash à l'intérieur du bloc 'with'
        with pytest.raises(RuntimeError):
            with handler.start_status("Test Context"):
                raise RuntimeError("Boom")

        # Vérifie que le mode erreur a été déclenché automatiquement
        mock_container.update.assert_called()
        args, kwargs = mock_container.update.call_args
        assert kwargs['state'] == "error"


class TestStreamlitResultRenderer:
    """Tests pour le moteur de rendu des résultats."""

    @patch(ST_PATCH)
    @patch('app.ui.results.orchestrator.ResultTabOrchestrator')
    def test_render_results_delegation(self, mock_orch_cls, mock_st):
        """Vérifie la délégation à l'orchestrateur (Lazy Loading)."""
        renderer = StreamlitResultRenderer()
        mock_result = Mock(spec=ValuationResult)

        renderer.render_results(mock_result)

        mock_orch_cls.assert_called_once()
        mock_orch_cls.return_value.render.assert_called_once_with(mock_result)

    @patch(ST_PATCH)
    def test_display_error_with_details(self, mock_st):
        """Vérifie l'affichage d'erreur avec l'expander technique."""
        renderer = StreamlitResultRenderer()

        # Mock de l'expander pour tester le bloc 'with'
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__.return_value = mock_expander

        renderer.display_error("Message", details="Stacktrace")

        mock_st.error.assert_called_with("Message")
        mock_st.expander.assert_called_once()
        mock_st.code.assert_called_with("Stacktrace", language="text")

    @patch(ST_PATCH)
    def test_display_error_no_details(self, mock_st):
        """Vérifie que l'expander n'est pas créé si details est None."""
        renderer = StreamlitResultRenderer()
        renderer.display_error("Message simple", details=None)

        mock_st.error.assert_called_with("Message simple")
        mock_st.expander.assert_not_called()

    @patch.object(StreamlitResultRenderer, 'render_results')
    def test_deprecated_aliases_coverage(self, mock_render):
        """Couverture des méthodes dépréciées pour assurer le 100%."""
        renderer = StreamlitResultRenderer()
        mock_res = Mock()

        renderer.render_executive_summary(mock_res)
        renderer.display_valuation_details(mock_res, provider=None)

        assert mock_render.call_count == 2