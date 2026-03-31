"""
Test: Feature 2.1 — Verify cross_canvas_service.py and all references are removed.

Acceptance Criteria:
- File backend/app/services/cross_canvas_service.py does not exist
- File backend/app/api/v1/endpoints/cross_canvas.py does not exist
- grep -r "cross_canvas" backend/app/ returns zero results (excluding tests/docs)
- Backend starts successfully (dependencies.py imports cleanly)
- ContextEnrichmentService can be instantiated without cross_canvas_service param
- VerificationService can be instantiated without cross_canvas_service param
"""

import importlib
from pathlib import Path

# Resolve backend/app root
_BACKEND_APP = Path(__file__).resolve().parents[2] / "app"


class TestCrossCanvasFileRemoval:
    """Verify the cross_canvas source files no longer exist."""

    def test_cross_canvas_service_file_deleted(self):
        path = _BACKEND_APP / "services" / "cross_canvas_service.py"
        assert not path.exists(), f"File should be deleted: {path}"

    def test_cross_canvas_endpoint_file_deleted(self):
        path = _BACKEND_APP / "api" / "v1" / "endpoints" / "cross_canvas.py"
        assert not path.exists(), f"File should be deleted: {path}"


class TestDependenciesImportClean:
    """Verify dependencies.py imports without cross_canvas references."""

    def test_dependencies_module_imports(self):
        """dependencies.py should import without errors after removal."""
        import app.dependencies

        importlib.reload(app.dependencies)
        # If we get here, the module imported successfully

    def test_no_cross_canvas_in_dependencies_all(self):
        """__all__ should not contain cross_canvas entries."""
        import app.dependencies

        all_exports = getattr(app.dependencies, "__all__", [])
        cross_refs = [name for name in all_exports if "cross_canvas" in name.lower()]
        assert cross_refs == [], (
            f"__all__ still contains cross_canvas refs: {cross_refs}"
        )


class TestServiceInstantiation:
    """Verify services work without cross_canvas_service parameter."""

    def test_context_enrichment_service_no_cross_canvas(self):
        """ContextEnrichmentService should instantiate without cross_canvas_service."""
        from app.services.context_enrichment_service import ContextEnrichmentService

        # Should work with just canvas_service (mock-free: pass None)
        service = ContextEnrichmentService(canvas_service=None)
        assert service is not None
        # Should NOT have _cross_canvas_service attribute
        assert not hasattr(service, "_cross_canvas_service"), (
            "ContextEnrichmentService should no longer have _cross_canvas_service"
        )

    def test_verification_service_no_cross_canvas(self):
        """VerificationService should instantiate without cross_canvas_service."""
        from app.services.verification_service import VerificationService

        service = VerificationService()
        assert service is not None
        assert not hasattr(service, "_cross_canvas_service"), (
            "VerificationService should no longer have _cross_canvas_service"
        )


class TestNoResidualReferences:
    """Scan backend/app/ for any remaining cross_canvas references."""

    def test_no_cross_canvas_in_app_source(self):
        """No .py file under backend/app/ should contain 'cross_canvas' as a standalone term.

        Note: 'find_node_across_canvases' is a CanvasService method unrelated
        to the removed CrossCanvasService -- it is excluded from this check.
        """
        violations = []
        for py_file in _BACKEND_APP.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                lower = line.lower()
                if "cross_canvas" in lower:
                    # Exclude 'across_canvases' which is an unrelated CanvasService method
                    if "across_canvases" in lower:
                        continue
                    violations.append(
                        f"{py_file.relative_to(_BACKEND_APP)}:{i}: {line.strip()}"
                    )

        assert violations == [], (
            f"Found {len(violations)} residual cross_canvas references:\n"
            + "\n".join(violations[:20])
        )
