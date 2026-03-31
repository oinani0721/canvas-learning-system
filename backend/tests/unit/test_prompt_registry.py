# Story 7.3: PromptRegistry Unit Tests
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
Unit tests for the PromptRegistry service.

Tests cover:
  - Loading prompt templates from directory
  - Getting templates by name and version
  - Metadata parsing from file headers
  - Content hash computation (SHA-256)
  - Version listing and rollback
  - Error handling (PromptLoadError)
"""

import hashlib
from pathlib import Path

import pytest
from app.core.exceptions import PromptLoadError
from app.services.prompt_registry import PromptRegistry, PromptTemplate

# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset PromptRegistry singleton before each test."""
    PromptRegistry.reset_instance()
    yield
    PromptRegistry.reset_instance()


@pytest.fixture
def sample_prompt_dir(tmp_path: Path) -> Path:
    """Create a temp directory with sample prompt files."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # v1 prompt
    v1_content = (
        "<!-- prompts/sample_v1.md -->\n"
        "<!-- \u5f15\u7528\u65b9: services/sample.py:SampleService.run() -->\n"
        "<!-- \u7248\u672c: v1 | \u521b\u5efa: 2026-03-16 -->\n"
        "<!-- \u53d8\u66f4\u65f6: 1.\u521b\u5efa\u65b0\u7248\u672c\u6587\u4ef6 2.\u66f4\u65b0service\u5f15\u7528 3.\u8dd1tests/regression/ -->\n"
        "\n"
        "# Sample Prompt v1\n"
        "\n"
        "This is the v1 sample prompt content.\n"
        "It has multiple lines.\n"
    )
    (prompts_dir / "sample_v1.md").write_text(v1_content, encoding="utf-8")

    # v2 prompt (same name, different version)
    v2_content = (
        "<!-- prompts/sample_v2.md -->\n"
        "<!-- \u5f15\u7528\u65b9: services/sample.py:SampleService.run() -->\n"
        "<!-- \u7248\u672c: v2 | \u521b\u5efa: 2026-03-17 -->\n"
        "<!-- \u53d8\u66f4\u65f6: 1.\u521b\u5efa\u65b0\u7248\u672c\u6587\u4ef6 2.\u66f4\u65b0service\u5f15\u7528 3.\u8dd1tests/regression/ -->\n"
        "\n"
        "# Sample Prompt v2\n"
        "\n"
        "This is the v2 sample prompt with improvements.\n"
        "Added new instructions.\n"
    )
    (prompts_dir / "sample_v2.md").write_text(v2_content, encoding="utf-8")

    # Another prompt (different name)
    other_content = (
        "<!-- prompts/other_v1.md -->\n"
        "<!-- \u5f15\u7528\u65b9: services/other.py:OtherService.process() -->\n"
        "<!-- \u7248\u672c: v1 | \u521b\u5efa: 2026-03-16 -->\n"
        "<!-- \u53d8\u66f4\u65f6: 1.\u521b\u5efa\u65b0\u7248\u672c\u6587\u4ef6 -->\n"
        "\n"
        "# Other Prompt v1\n"
        "\n"
        "Content for the other prompt.\n"
    )
    (prompts_dir / "other_v1.md").write_text(other_content, encoding="utf-8")

    return prompts_dir


@pytest.fixture
def loaded_registry(sample_prompt_dir: Path) -> PromptRegistry:
    """Return a PromptRegistry that has been loaded from sample data."""
    registry = PromptRegistry(prompts_dir=sample_prompt_dir)
    registry.load_all()
    return registry


# ─── Test: Loading ────────────────────────────────────────────────────────


class TestPromptRegistryLoading:
    """Tests for load_all() and directory scanning."""

    def test_load_all_returns_count(self, sample_prompt_dir: Path):
        """load_all() returns the number of templates loaded."""
        registry = PromptRegistry(prompts_dir=sample_prompt_dir)
        count = registry.load_all()
        assert count == 3  # sample_v1, sample_v2, other_v1

    def test_load_all_sets_loaded_flag(self, loaded_registry: PromptRegistry):
        """is_loaded is True after successful load_all()."""
        assert loaded_registry.is_loaded is True

    def test_load_all_nonexistent_dir_raises(self, tmp_path: Path):
        """load_all() raises PromptLoadError for missing directory."""
        registry = PromptRegistry(prompts_dir=tmp_path / "nonexistent")
        with pytest.raises(PromptLoadError, match="does not exist"):
            registry.load_all()

    def test_load_all_empty_dir(self, tmp_path: Path):
        """load_all() handles empty directory (returns 0)."""
        empty_dir = tmp_path / "empty_prompts"
        empty_dir.mkdir()
        registry = PromptRegistry(prompts_dir=empty_dir)
        count = registry.load_all()
        assert count == 0

    def test_load_all_skips_non_matching_files(self, tmp_path: Path):
        """Files not matching {name}_v{N}.md pattern are skipped."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        # Non-matching files
        (prompts_dir / "README.md").write_text("readme", encoding="utf-8")
        (prompts_dir / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
        registry = PromptRegistry(prompts_dir=prompts_dir)
        count = registry.load_all()
        assert count == 0

    def test_load_empty_file_raises(self, tmp_path: Path):
        """Empty prompt file raises PromptLoadError."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "empty_v1.md").write_text("", encoding="utf-8")
        registry = PromptRegistry(prompts_dir=prompts_dir)
        with pytest.raises(PromptLoadError, match="empty"):
            registry.load_all()

    def test_load_missing_metadata_raises(self, tmp_path: Path):
        """File without required metadata raises PromptLoadError."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "bad_v1.md").write_text(
            "# No metadata\nJust content.", encoding="utf-8"
        )
        registry = PromptRegistry(prompts_dir=prompts_dir)
        with pytest.raises(PromptLoadError, match="Missing metadata"):
            registry.load_all()


# ─── Test: Get API ────────────────────────────────────────────────────────


class TestPromptRegistryGet:
    """Tests for get() and get_template()."""

    def test_get_latest_version(self, loaded_registry: PromptRegistry):
        """get(name) returns latest version content."""
        content = loaded_registry.get("sample")
        assert "v2" in content  # v2 is latest

    def test_get_specific_version(self, loaded_registry: PromptRegistry):
        """get(name, version=1) returns v1 content."""
        content = loaded_registry.get("sample", version=1)
        assert "v1" in content

    def test_get_nonexistent_name_raises(self, loaded_registry: PromptRegistry):
        """get() with unknown name raises PromptLoadError."""
        with pytest.raises(PromptLoadError, match="No template found"):
            loaded_registry.get("nonexistent")

    def test_get_nonexistent_version_raises(self, loaded_registry: PromptRegistry):
        """get() with unknown version raises PromptLoadError."""
        with pytest.raises(PromptLoadError, match="Version v99 not found"):
            loaded_registry.get("sample", version=99)

    def test_get_template_returns_dataclass(self, loaded_registry: PromptRegistry):
        """get_template() returns PromptTemplate instance."""
        template = loaded_registry.get_template("sample")
        assert isinstance(template, PromptTemplate)
        assert template.name == "sample"
        assert template.version == 2  # latest


# ─── Test: Metadata ──────────────────────────────────────────────────────


class TestPromptRegistryMetadata:
    """Tests for metadata parsing and retrieval."""

    def test_metadata_service_ref(self, loaded_registry: PromptRegistry):
        """Metadata correctly parses service reference."""
        metadata = loaded_registry.get_metadata("sample")
        assert "services/sample.py" in metadata["service_ref"]

    def test_metadata_created_at(self, loaded_registry: PromptRegistry):
        """Metadata correctly parses creation date."""
        metadata = loaded_registry.get_metadata("sample", version=1)
        assert metadata["created_at"] == "2026-03-16"

    def test_metadata_content_hash(self, loaded_registry: PromptRegistry):
        """Content hash is valid SHA-256."""
        metadata = loaded_registry.get_metadata("sample")
        assert len(metadata["content_hash"]) == 64
        # Verify it's hex
        int(metadata["content_hash"], 16)


# ─── Test: Hash ───────────────────────────────────────────────────────────


class TestPromptRegistryHash:
    """Tests for content hash computation."""

    def test_hash_consistency(self, loaded_registry: PromptRegistry):
        """Same content produces same hash."""
        hash1 = loaded_registry.get_hash("sample", version=1)
        hash2 = loaded_registry.get_hash("sample", version=1)
        assert hash1 == hash2

    def test_hash_differs_between_versions(self, loaded_registry: PromptRegistry):
        """Different versions have different hashes."""
        hash1 = loaded_registry.get_hash("sample", version=1)
        hash2 = loaded_registry.get_hash("sample", version=2)
        assert hash1 != hash2

    def test_hash_matches_manual_sha256(self, sample_prompt_dir: Path):
        """Hash matches manually computed SHA-256."""
        registry = PromptRegistry(prompts_dir=sample_prompt_dir)
        registry.load_all()

        # PromptRegistry reads with read_text(encoding="utf-8") then encodes,
        # so we do the same to get a matching hash (avoids CRLF/LF differences).
        file_text = (sample_prompt_dir / "sample_v1.md").read_text(encoding="utf-8")
        expected_hash = hashlib.sha256(file_text.encode("utf-8")).hexdigest()
        actual_hash = registry.get_hash("sample", version=1)
        assert actual_hash == expected_hash


# ─── Test: Version Listing ────────────────────────────────────────────────


class TestPromptRegistryVersions:
    """Tests for list_versions() and list_names()."""

    def test_list_versions(self, loaded_registry: PromptRegistry):
        """list_versions returns sorted version numbers."""
        versions = loaded_registry.list_versions("sample")
        assert versions == [1, 2]

    def test_list_versions_single(self, loaded_registry: PromptRegistry):
        """list_versions works for single-version templates."""
        versions = loaded_registry.list_versions("other")
        assert versions == [1]

    def test_list_versions_nonexistent_raises(self, loaded_registry: PromptRegistry):
        """list_versions for unknown name raises PromptLoadError."""
        with pytest.raises(PromptLoadError):
            loaded_registry.list_versions("nonexistent")

    def test_list_names(self, loaded_registry: PromptRegistry):
        """list_names returns sorted template names."""
        names = loaded_registry.list_names()
        assert names == ["other", "sample"]


# ─── Test: Version Rollback ──────────────────────────────────────────────


class TestPromptRegistryRollback:
    """Tests for version pinning and rollback."""

    def test_set_active_version(self, loaded_registry: PromptRegistry):
        """Pinning active version changes what get() returns."""
        # Default: latest (v2)
        assert "v2" in loaded_registry.get("sample")

        # Pin to v1
        loaded_registry.set_active_version("sample", 1)
        assert "v1" in loaded_registry.get("sample")

    def test_clear_active_version(self, loaded_registry: PromptRegistry):
        """Clearing pin reverts to latest."""
        loaded_registry.set_active_version("sample", 1)
        loaded_registry.clear_active_version("sample")
        assert "v2" in loaded_registry.get("sample")

    def test_get_active_version(self, loaded_registry: PromptRegistry):
        """get_active_version returns pinned version or None."""
        assert loaded_registry.get_active_version("sample") is None
        loaded_registry.set_active_version("sample", 1)
        assert loaded_registry.get_active_version("sample") == 1

    def test_set_active_nonexistent_version_raises(
        self, loaded_registry: PromptRegistry
    ):
        """Pinning nonexistent version raises PromptLoadError."""
        with pytest.raises(PromptLoadError, match="Cannot set active version"):
            loaded_registry.set_active_version("sample", 99)

    def test_set_active_nonexistent_name_raises(self, loaded_registry: PromptRegistry):
        """Pinning version for unknown name raises PromptLoadError."""
        with pytest.raises(PromptLoadError, match="No template found"):
            loaded_registry.set_active_version("nonexistent", 1)


# ─── Test: Singleton ─────────────────────────────────────────────────────


class TestPromptRegistrySingleton:
    """Tests for singleton pattern."""

    def test_get_instance_returns_same_object(self):
        """get_instance() returns the same object on repeated calls."""
        inst1 = PromptRegistry.get_instance()
        inst2 = PromptRegistry.get_instance()
        assert inst1 is inst2

    def test_reset_instance_clears_singleton(self):
        """reset_instance() allows creating a fresh instance."""
        inst1 = PromptRegistry.get_instance()
        PromptRegistry.reset_instance()
        inst2 = PromptRegistry.get_instance()
        assert inst1 is not inst2


# ─── Test: Real Prompts ──────────────────────────────────────────────────


class TestRealPrompts:
    """Integration tests using actual prompt files from the project."""

    @pytest.fixture
    def real_registry(self) -> PromptRegistry:
        """Load the real prompts directory."""
        real_dir = Path(__file__).parent.parent.parent / "app" / "prompts"
        if not real_dir.exists():
            pytest.skip("Real prompts directory not found")
        registry = PromptRegistry(prompts_dir=real_dir)
        registry.load_all()
        return registry

    def test_real_prompts_load(self, real_registry: PromptRegistry):
        """All real prompt templates load successfully."""
        names = real_registry.list_names()
        assert len(names) >= 3, "Expected at least 3 prompt templates"
        expected_names = {"autoscore", "question_gen", "context_extract"}
        assert expected_names.issubset(set(names))

    def test_real_autoscore_structure(self, real_registry: PromptRegistry):
        """Real autoscore prompt has required structure."""
        content = real_registry.get("autoscore")
        assert "AutoSCORE" in content
        assert "SOLO" in content
        assert len(content) > 500

    def test_real_question_gen_structure(self, real_registry: PromptRegistry):
        """Real question_gen prompt has 5-layer structure."""
        content = real_registry.get("question_gen")
        assert "Bloom" in content
        assert len(content) > 500

    def test_real_context_extract_structure(self, real_registry: PromptRegistry):
        """Real context_extract prompt has extraction categories."""
        content = real_registry.get("context_extract")
        assert "evidence" in content.lower()
        assert len(content) > 500
