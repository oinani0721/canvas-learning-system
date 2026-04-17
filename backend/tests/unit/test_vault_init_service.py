"""Story 1.1 Task 1: Vault directory initialization tests.

Verifies VaultInitService creates the correct directory structure,
.gitkeep files, and CLAUDE.md skeleton. All operations must be idempotent.
"""

from pathlib import Path

import pytest


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "test-vault"


class TestInitializeVault:
    """Task 1: Vault directory initialization."""

    def test_creates_required_directories(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc.initialize_vault(str(vault_dir))

        expected_dirs = [
            "raw",
            "wiki/concepts",
            "wiki/canvases",
            "outputs/exam_boards",
        ]
        for d in expected_dirs:
            assert (vault_dir / d).is_dir(), f"Directory {d} must exist"

    def test_creates_gitkeep_files(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc.initialize_vault(str(vault_dir))

        leaf_dirs = [
            "raw",
            "wiki/concepts",
            "wiki/canvases",
            "outputs/exam_boards",
        ]
        for d in leaf_dirs:
            gitkeep = vault_dir / d / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep must exist in {d}"

    def test_creates_claude_md(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc.initialize_vault(str(vault_dir))

        claude_md = vault_dir / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md must exist in vault root"
        content = claude_md.read_text()
        assert "Canvas Learning System" in content

    def test_idempotent_no_error(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        svc = VaultInitService()
        svc.initialize_vault(str(vault_dir))
        svc.initialize_vault(str(vault_dir))

    def test_does_not_overwrite_existing_claude_md(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        vault_dir.mkdir(parents=True)
        custom = vault_dir / "CLAUDE.md"
        custom.write_text("user custom content")

        svc = VaultInitService()
        svc.initialize_vault(str(vault_dir))

        assert custom.read_text() == "user custom content"


class TestCheckRequiredPlugins:
    """Task 3: Plugin detection logic."""

    def test_all_plugins_installed(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        vault_dir.mkdir(parents=True)
        obsidian_dir = vault_dir / ".obsidian"
        obsidian_dir.mkdir()

        import json

        community = [
            "dataview",
            "templater-obsidian",
            "quickadd",
            "obsidian-meta-bind-plugin",
        ]
        (obsidian_dir / "community-plugins.json").write_text(json.dumps(community))
        (obsidian_dir / "core-plugins.json").write_text(json.dumps(["bases"]))

        svc = VaultInitService()
        results = svc.check_required_plugins(str(vault_dir))

        for r in results:
            assert r.installed, f"Plugin {r.plugin_id} should be detected as installed"

    def test_missing_plugins_detected(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        vault_dir.mkdir(parents=True)
        obsidian_dir = vault_dir / ".obsidian"
        obsidian_dir.mkdir()

        import json

        (obsidian_dir / "community-plugins.json").write_text(json.dumps(["dataview"]))
        (obsidian_dir / "core-plugins.json").write_text(json.dumps([]))

        svc = VaultInitService()
        results = svc.check_required_plugins(str(vault_dir))

        missing = [r for r in results if not r.installed]
        assert len(missing) >= 3, "At least 3 plugins should be missing"

    def test_no_obsidian_dir(self, vault_dir: Path):
        from app.services.vault_init_service import VaultInitService

        vault_dir.mkdir(parents=True)

        svc = VaultInitService()
        results = svc.check_required_plugins(str(vault_dir))

        assert all(not r.installed for r in results), (
            "All should be missing without .obsidian"
        )
