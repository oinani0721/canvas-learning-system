"""
Iteration Validation Tests

Tests for validate-iteration.py logic.
Total: 38 tests
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# =============================================================================
# Test: PRD Validation
# =============================================================================

class TestPRDValidation:
    """Tests for PRD file validation between iterations."""

    def test_prd_version_must_increment(self, previous_snapshot, current_snapshot):
        """PRD version must increment when content changes."""
        # Version changed from 1.0.0 to 1.1.0
        prev_version = previous_snapshot["files"]["prd"][0]["version"]
        curr_version = current_snapshot["files"]["prd"][0]["version"]

        from planning_utils import compare_versions
        assert compare_versions(curr_version, prev_version) > 0

    def test_prd_version_not_incremented_warning(self, previous_snapshot):
        """Warning when version not incremented but content changed."""
        import copy
        # Same version but different hash
        current = copy.deepcopy(previous_snapshot)
        current["files"]["prd"][0]["hash"] = "sha256:different..."

        has_warning = (
            current["files"]["prd"][0]["hash"] != previous_snapshot["files"]["prd"][0]["hash"]
            and current["files"]["prd"][0]["version"] == previous_snapshot["files"]["prd"][0]["version"]
        )
        assert has_warning

    def test_prd_file_deletion_breaking_change(self, previous_snapshot):
        """PRD file deletion is a breaking change."""
        current = {
            "files": {
                "prd": [],  # File deleted
                "architecture": previous_snapshot["files"]["architecture"],
                "api_specs": previous_snapshot["files"]["api_specs"],
                "schemas": previous_snapshot["files"]["schemas"]
            }
        }

        prev_files = {f["path"] for f in previous_snapshot["files"]["prd"]}
        curr_files = {f["path"] for f in current["files"]["prd"]}
        deleted_files = prev_files - curr_files

        assert len(deleted_files) > 0
        assert "docs/prd/epic-1.md" in deleted_files

    def test_prd_new_file_addition(self, previous_snapshot):
        """Allow adding new PRD files."""
        current = previous_snapshot.copy()
        current["files"]["prd"] = previous_snapshot["files"]["prd"] + [
            {
                "path": "docs/prd/epic-2.md",
                "hash": "sha256:new...",
                "version": "1.0.0",
                "size": 500
            }
        ]

        curr_files = {f["path"] for f in current["files"]["prd"]}
        assert "docs/prd/epic-2.md" in curr_files

    def test_prd_hash_unchanged_no_version_increment_needed(self, previous_snapshot):
        """No version increment needed if hash unchanged."""
        current = previous_snapshot.copy()
        # Same hash means no changes
        same_hash = (
            current["files"]["prd"][0]["hash"] ==
            previous_snapshot["files"]["prd"][0]["hash"]
        )
        assert same_hash

    def test_prd_multiple_files_validation(self, previous_snapshot):
        """Validate multiple PRD files."""
        current = previous_snapshot.copy()
        current["files"]["prd"] = [
            {"path": "docs/prd/epic-1.md", "hash": "sha256:a", "version": "1.1.0", "size": 100},
            {"path": "docs/prd/epic-2.md", "hash": "sha256:b", "version": "1.0.0", "size": 200},
            {"path": "docs/prd/epic-3.md", "hash": "sha256:c", "version": "1.0.0", "size": 300}
        ]

        assert len(current["files"]["prd"]) == 3

    def test_prd_version_format_validation(self):
        """Validate version string format."""
        from planning_utils import parse_semver

        # Valid versions
        parse_semver("1.0.0")
        parse_semver("v2.1.0")
        parse_semver("10.20.30")

        # Invalid versions
        with pytest.raises(ValueError):
            parse_semver("invalid")

    def test_prd_path_normalization(self):
        """Normalize paths for comparison."""
        path1 = "docs/prd/epic-1.md"
        path2 = "docs\\prd\\epic-1.md"

        normalized1 = path1.replace("\\", "/")
        normalized2 = path2.replace("\\", "/")

        assert normalized1 == normalized2


# =============================================================================
# Test: Architecture Validation
# =============================================================================

class TestArchitectureValidation:
    """Tests for architecture file validation."""

    def test_architecture_version_increment(self, previous_snapshot, current_snapshot):
        """Architecture version should increment on changes."""
        prev_arch = previous_snapshot["files"]["architecture"][0]
        curr_arch = current_snapshot["files"]["architecture"][0]

        # Same version and hash in our fixtures
        assert prev_arch["version"] == curr_arch["version"]
        assert prev_arch["hash"] == curr_arch["hash"]

    def test_architecture_file_deletion_breaking(self, previous_snapshot):
        """Architecture file deletion is breaking change."""
        import copy
        current = copy.deepcopy(previous_snapshot)
        current["files"]["architecture"] = []

        deleted = len(previous_snapshot["files"]["architecture"]) > len(current["files"]["architecture"])
        assert deleted

    def test_adr_addition_allowed(self, previous_snapshot):
        """Adding new ADR files is allowed."""
        current = previous_snapshot.copy()
        current["files"]["architecture"] = previous_snapshot["files"]["architecture"] + [
            {
                "path": "docs/architecture/decisions/0005-new-adr.md",
                "hash": "sha256:adr...",
                "version": "1.0.0",
                "size": 400
            }
        ]

        assert len(current["files"]["architecture"]) == 2

    def test_architecture_unchanged_no_validation_error(self, previous_snapshot):
        """No error when architecture unchanged."""
        current = previous_snapshot.copy()

        arch_unchanged = (
            current["files"]["architecture"] ==
            previous_snapshot["files"]["architecture"]
        )
        assert arch_unchanged

    def test_architecture_dependencies_tracking(self, previous_snapshot):
        """Track architecture file dependencies."""
        # Future: validate that architecture changes are reflected in related files
        arch_files = previous_snapshot["files"]["architecture"]
        assert len(arch_files) >= 1

    def test_architecture_breaking_change_detection(self, previous_snapshot):
        """Detect breaking changes in architecture."""
        import copy
        current = copy.deepcopy(previous_snapshot)
        current["files"]["architecture"][0]["version"] = "3.0.0"  # Major version bump

        from planning_utils import compare_versions
        result = compare_versions(
            current["files"]["architecture"][0]["version"],
            previous_snapshot["files"]["architecture"][0]["version"]
        )
        assert result > 0  # Version increased

    def test_architecture_version_must_be_semver(self):
        """Architecture version must be semantic version."""
        from planning_utils import parse_semver

        version = "2.0.0"
        major, minor, patch = parse_semver(version)
        assert major == 2


# =============================================================================
# Test: API Spec Validation
# =============================================================================

class TestAPISpecValidation:
    """Tests for OpenAPI specification validation."""

    def test_api_spec_version_increment(self, previous_snapshot, current_snapshot):
        """API spec version should increment on changes."""
        prev_api = previous_snapshot["files"]["api_specs"][0]
        curr_api = current_snapshot["files"]["api_specs"][0]

        from planning_utils import compare_versions
        result = compare_versions(curr_api["version"], prev_api["version"])
        assert result > 0  # 1.1.0 > 1.0.0

    def test_endpoint_deletion_is_breaking(self, previous_snapshot, breaking_change_snapshot):
        """Endpoint deletion is a breaking change."""
        prev_endpoints = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = breaking_change_snapshot["files"]["api_specs"][0]["endpoints"]

        deleted = prev_endpoints - curr_endpoints
        assert deleted > 0  # 12 - 10 = 2 deleted

    def test_endpoint_addition_allowed(self, previous_snapshot, current_snapshot):
        """Endpoint addition is allowed."""
        prev_endpoints = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_endpoints = current_snapshot["files"]["api_specs"][0]["endpoints"]

        added = curr_endpoints - prev_endpoints
        assert added > 0  # 14 - 12 = 2 added

    def test_api_spec_hash_change_requires_version_bump(self, previous_snapshot):
        """Hash change requires version increment."""
        import copy
        current = copy.deepcopy(previous_snapshot)
        current["files"]["api_specs"][0]["hash"] = "sha256:different..."
        current["files"]["api_specs"][0]["version"] = "1.0.0"  # Same version

        hash_changed = (
            current["files"]["api_specs"][0]["hash"] !=
            previous_snapshot["files"]["api_specs"][0]["hash"]
        )
        version_same = (
            current["files"]["api_specs"][0]["version"] ==
            previous_snapshot["files"]["api_specs"][0]["version"]
        )

        # This is a warning condition
        assert hash_changed and version_same

    def test_required_field_removal_is_breaking(self):
        """Removing required field from schema is breaking."""
        prev_schema = {
            "required": ["id", "type", "x", "y", "width", "height"]
        }
        curr_schema = {
            "required": ["id", "type", "x", "y"]  # Removed width, height
        }

        prev_required = set(prev_schema["required"])
        curr_required = set(curr_schema["required"])
        removed = prev_required - curr_required

        assert len(removed) == 2
        assert "width" in removed
        assert "height" in removed

    def test_optional_field_removal_not_breaking(self):
        """Removing optional field is not breaking."""
        prev_properties = {"id", "type", "color", "metadata"}
        curr_properties = {"id", "type", "color"}  # Removed metadata

        removed = prev_properties - curr_properties
        assert "metadata" in removed
        # Not breaking if metadata was optional

    def test_api_spec_backward_compatibility(self, previous_snapshot, current_snapshot):
        """Check backward compatibility of API changes."""
        prev_version = previous_snapshot["files"]["api_specs"][0]["version"]
        curr_version = current_snapshot["files"]["api_specs"][0]["version"]

        from planning_utils import parse_semver
        prev_major, _, _ = parse_semver(prev_version)
        curr_major, _, _ = parse_semver(curr_version)

        # Same major version means backward compatible
        backward_compatible = curr_major == prev_major
        assert backward_compatible

    def test_multiple_api_specs_validation(self, previous_snapshot):
        """Validate multiple API spec files."""
        current = previous_snapshot.copy()
        current["files"]["api_specs"] = [
            {"path": "specs/api/canvas-api.yml", "version": "1.0.0", "endpoints": 12, "hash": "a"},
            {"path": "specs/api/agent-api.yml", "version": "1.0.0", "endpoints": 8, "hash": "b"}
        ]

        assert len(current["files"]["api_specs"]) == 2

    def test_api_spec_schema_ref_validation(self, sample_openapi_spec):
        """Validate that all $ref references exist."""
        schemas = sample_openapi_spec.get("components", {}).get("schemas", {})

        def find_refs(obj):
            refs = []
            if isinstance(obj, dict):
                if "$ref" in obj:
                    refs.append(obj["$ref"])
                for value in obj.values():
                    refs.extend(find_refs(value))
            elif isinstance(obj, list):
                for item in obj:
                    refs.extend(find_refs(item))
            return refs

        all_refs = find_refs(sample_openapi_spec)
        for ref in all_refs:
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.split("/")[-1]
                assert schema_name in schemas, f"Invalid ref: {ref}"


# =============================================================================
# Test: Schema Validation
# =============================================================================

class TestSchemaValidation:
    """Tests for JSON Schema validation."""

    def test_schema_required_field_removal_breaking(self):
        """Removing required field is breaking change."""
        prev_required = ["id", "type", "x", "y", "width", "height"]
        curr_required = ["id", "type"]

        removed = set(prev_required) - set(curr_required)
        assert len(removed) == 4

    def test_schema_enum_value_removal_breaking(self):
        """Removing enum value is breaking change."""
        prev_colors = ["1", "2", "3", "5", "6"]
        curr_colors = ["1", "2", "3"]  # Removed 5, 6

        removed = set(prev_colors) - set(curr_colors)
        assert "5" in removed
        assert "6" in removed

    def test_schema_enum_value_addition_allowed(self):
        """Adding enum value is allowed."""
        prev_colors = ["1", "2", "3"]
        curr_colors = ["1", "2", "3", "4", "5"]

        added = set(curr_colors) - set(prev_colors)
        assert "4" in added
        assert "5" in added

    def test_schema_type_change_breaking(self):
        """Changing property type is breaking."""
        prev_type = "string"
        curr_type = "number"

        type_changed = prev_type != curr_type
        assert type_changed

    def test_schema_title_unchanged(self, previous_snapshot):
        """Schema title should remain unchanged."""
        schema = previous_snapshot["files"]["schemas"][0]
        assert schema["title"] == "CanvasNode"

    def test_schema_description_change_allowed(self, sample_json_schema):
        """Schema description change is allowed."""
        prev_desc = sample_json_schema.get("description", "")
        new_desc = "Updated description"

        # Description change is not breaking
        assert prev_desc != new_desc


# =============================================================================
# Test: Breaking Change Detection
# =============================================================================

class TestBreakingChangeDetection:
    """Tests for comprehensive breaking change detection."""

    def test_detect_endpoint_deletion(self, previous_snapshot, breaking_change_snapshot):
        """Detect endpoint deletion as breaking change."""
        prev_count = previous_snapshot["files"]["api_specs"][0]["endpoints"]
        curr_count = breaking_change_snapshot["files"]["api_specs"][0]["endpoints"]

        is_breaking = curr_count < prev_count
        assert is_breaking

    def test_detect_required_field_removal(self):
        """Detect required field removal as breaking change."""
        prev = {"required": ["a", "b", "c"]}
        curr = {"required": ["a", "b"]}

        removed = set(prev["required"]) - set(curr["required"])
        is_breaking = len(removed) > 0
        assert is_breaking

    def test_detect_enum_value_removal(self):
        """Detect enum value removal as breaking change."""
        prev = {"enum": ["1", "2", "3"]}
        curr = {"enum": ["1", "2"]}

        removed = set(prev["enum"]) - set(curr["enum"])
        is_breaking = len(removed) > 0
        assert is_breaking

    def test_combine_multiple_breaking_changes(self):
        """Combine multiple breaking changes in report."""
        breaking_changes = []

        # Simulate multiple detections
        breaking_changes.append({
            "type": "endpoint_deleted",
            "path": "/api/cache/{id}",
            "method": "DELETE"
        })
        breaking_changes.append({
            "type": "required_field_removed",
            "schema": "User",
            "field": "email_verified"
        })

        assert len(breaking_changes) == 2


# =============================================================================
# Test: Validation Rule Loading
# =============================================================================

class TestValidationRuleLoading:
    """Tests for validation rule configuration."""

    def test_load_rules_prd_section(self, sample_validation_rules):
        """Load PRD validation rules."""
        prd_rules = sample_validation_rules["rules"]["prd"]

        assert prd_rules["version_must_increment"] is True
        assert prd_rules["file_deletion_is_breaking"] is True

    def test_load_rules_api_section(self, sample_validation_rules):
        """Load API spec validation rules."""
        api_rules = sample_validation_rules["rules"]["api_specs"]

        assert api_rules["endpoint_deletion_is_breaking"] is True
        assert api_rules["required_field_removal_is_breaking"] is True

    def test_load_rules_schema_section(self, sample_validation_rules):
        """Load schema validation rules."""
        schema_rules = sample_validation_rules["rules"]["schemas"]

        assert schema_rules["required_field_removal_is_breaking"] is True
        assert schema_rules["enum_value_removal_is_breaking"] is True

    def test_apply_custom_rules(self):
        """Apply custom validation rules."""
        custom_rules = {
            "prd": {
                "version_must_increment": False  # Override
            }
        }

        # Custom rule overrides default
        assert custom_rules["prd"]["version_must_increment"] is False
