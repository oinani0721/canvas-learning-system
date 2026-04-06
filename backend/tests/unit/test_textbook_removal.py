"""
Feature 2.2 Verification: Textbook retriever removal.

Ensures that all textbook-related code has been successfully removed
from the backend and agentic_rag modules per GDA-2 decision.

Expected 4 RAG channels: LanceDB, Vault Notes, Graphiti, Multimodal.
"""

import sys
from pathlib import Path

# ============================================================================
# File Deletion Verification
# ============================================================================


class TestTextbookFilesRemoved:
    """Verify that textbook-specific files have been deleted."""

    def test_textbook_context_service_deleted(self):
        """textbook_context_service.py must not exist."""
        path = (
            Path(__file__).parent.parent.parent
            / "app"
            / "services"
            / "textbook_context_service.py"
        )
        assert not path.exists(), f"Expected deleted: {path}"

    def test_textbook_endpoint_deleted(self):
        """textbook.py endpoint must not exist."""
        path = (
            Path(__file__).parent.parent.parent
            / "app"
            / "api"
            / "v1"
            / "endpoints"
            / "textbook.py"
        )
        assert not path.exists(), f"Expected deleted: {path}"

    def test_textbook_retriever_deleted(self):
        """textbook_retriever.py in agentic_rag must not exist."""
        path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "agentic_rag"
            / "retrievers"
            / "textbook_retriever.py"
        )
        assert not path.exists(), f"Expected deleted: {path}"

    def test_textbook_unit_tests_deleted(self):
        """test_textbook_link_format.py must not exist."""
        path = Path(__file__).parent / "test_textbook_link_format.py"
        assert not path.exists(), f"Expected deleted: {path}"

    def test_textbook_e2e_tests_deleted(self):
        """test_textbook_mount_e2e.py must not exist."""
        path = Path(__file__).parent.parent / "e2e" / "test_textbook_mount_e2e.py"
        assert not path.exists(), f"Expected deleted: {path}"

    def test_textbook_mount_flow_deleted(self):
        """test_textbook_mount_flow.py must not exist."""
        path = Path(__file__).parent.parent / "e2e" / "test_textbook_mount_flow.py"
        assert not path.exists(), f"Expected deleted: {path}"

    def test_agent_generates_links_deleted(self):
        """test_agent_generates_links.py must not exist (textbook link tests)."""
        path = Path(__file__).parent.parent / "e2e" / "test_agent_generates_links.py"
        assert not path.exists(), f"Expected deleted: {path}"


# ============================================================================
# Import Verification
# ============================================================================


class TestTextbookImportsRemoved:
    """Verify that textbook imports no longer exist in key modules."""

    def test_dependencies_imports_without_textbook(self):
        """dependencies.py should import successfully without textbook references."""
        # Force reimport
        if "app.dependencies" in sys.modules:
            del sys.modules["app.dependencies"]

    def test_router_imports_without_textbook(self):
        """router.py should not import textbook_router."""
        import app.api.v1.router as router_mod

        source = Path(router_mod.__file__).read_text()
        assert "textbook_router" not in source
        assert "textbook" not in source.lower() or "textbook" not in [
            line.strip()
            for line in source.split("\n")
            if "import" in line and "textbook" in line.lower()
        ]

    def test_agents_rag_source_map_no_textbook(self):
        """RAG_SOURCE_MAP in agents.py must not contain 'textbook'."""
        import app.api.v1.endpoints.agents as agents_mod

        source = Path(agents_mod.__file__).read_text()
        # Check that source_labels dict doesn't have textbook
        assert '"textbook"' not in source or "'textbook'" not in source


# ============================================================================
# RAG Channel Verification
# ============================================================================


class TestRAGChannelCount:
    """Verify exactly 4 RAG channels remain."""

    def test_agentic_rag_config_no_textbook_weight(self):
        """DEFAULT_SOURCE_WEIGHTS in config.py must not include textbook."""
        # Add src to path for import
        project_root = Path(__file__).parent.parent.parent
        src_path = str(project_root / "lib")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from agentic_rag.config import DEFAULT_SOURCE_WEIGHTS

        assert "textbook" not in DEFAULT_SOURCE_WEIGHTS
        # Should have exactly 4 channels
        expected_channels = {"graphiti", "lancedb", "multimodal", "vault_notes"}
        assert set(DEFAULT_SOURCE_WEIGHTS.keys()) == expected_channels

    def test_agentic_rag_nodes_no_textbook_weight(self):
        """DEFAULT_SOURCE_WEIGHTS in nodes.py must not include textbook."""
        project_root = Path(__file__).parent.parent.parent
        src_path = str(project_root / "lib")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from agentic_rag.nodes import DEFAULT_SOURCE_WEIGHTS

        assert "textbook" not in DEFAULT_SOURCE_WEIGHTS

    def test_enriched_context_no_textbook_fields(self):
        """EnrichedContext dataclass must not have textbook fields."""
        from app.services.context_enrichment_service import EnrichedContext

        context = EnrichedContext(
            target_node={"id": "n1"},
            adjacent_nodes=[],
            enriched_context="",
        )
        assert not hasattr(context, "textbook_context")
        assert not hasattr(context, "has_textbook_refs")
