# Canvas Learning System - Story 30.19 Tests
# SubjectResolver 单元测试
"""
Story 30.19 - SubjectMapping 学科映射配置 UI 验证与测试补全

Task 1: SubjectResolver unit tests
- 4-level priority resolution
- Glob pattern matching
- CRUD operations (add/remove mapping)
- YAML config persistence roundtrip
- Chinese character sanitization

[Source: docs/epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md]
"""

from unittest.mock import patch

import pytest
import yaml
from app.models.metadata_models import (
    MetadataSource,
    SubjectMappingConfig,
    SubjectMappingRule,
)
from app.services.subject_resolver import SubjectResolver

# CARD-REDBASE-R1 (BATCH-2026-09-05-第十一批): group_id 断言里的 vault 段用
# 独立哨兵值 + patch 注入, 既不硬编码仓内 vault 字面量, 也不靠「两侧都调
# get_current_vault_id()」自证 —— 期望值来源与被测实现无关。
_PROBE_VAULT = "probe_vault_id"

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_config_yaml(tmp_path):
    """Create a temporary YAML config file for testing."""
    config_data = {
        "mappings": [
            {"pattern": "Math 54/**", "subject": "math54", "category": "math"},
            {"pattern": "Physics 7A/**", "subject": "physics7a", "category": "physics"},
            {"pattern": "CS 189/*", "subject": "cs189", "category": "cs"},
        ],
        "category_rules": {
            "math": ["math*", "数学*"],
            "physics": ["physics*", "物理*"],
            "cs": ["cs*", "计算机*"],
        },
        "defaults": {
            "subject": "general",
            "category": "general",
        },
        "skip_directories": [".obsidian", ".git", "templates"],
    }
    config_path = tmp_path / "subject_mapping.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
    return str(config_path)


@pytest.fixture
def resolver(sample_config_yaml):
    """Create a SubjectResolver with test config."""
    return SubjectResolver(config_path=sample_config_yaml)


@pytest.fixture
def empty_resolver(tmp_path):
    """Create a SubjectResolver with empty config."""
    config_path = tmp_path / "empty_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump({}, f)
    return SubjectResolver(config_path=str(config_path))


# =============================================================================
# Task 1.1: 4-Level Priority Resolution
# =============================================================================


class TestPriorityResolution:
    """AC-30.19.1: 4-level priority resolution (manual > config > inferred > default)."""

    def test_manual_override_highest_priority(self, resolver):
        """Manual override should take highest priority."""
        result = resolver.resolve(
            "Math 54/离散数学.canvas",
            manual_subject="custom-subject",
            manual_category="custom-category",
        )
        assert result.source == MetadataSource.MANUAL
        assert result.subject == "custom-subject"
        assert result.category == "custom-category"
        # CARD-REDBASE-R1: D16 构造器 build_vault_group_id 对 subject 段做
        # sanitize_subject_name (连字符 → 下划线), 断言归一化后的形态。
        # 原断言 `"custom-subject" in group_id` 是前 D16 的裸格式遗留。
        assert ":custom_subject:" in result.group_id

    def test_config_match_when_no_manual(self, resolver):
        """Config mapping should be used when no manual override."""
        result = resolver.resolve("Math 54/离散数学.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"
        assert result.category == "math"

    def test_inferred_when_no_config_match(self, resolver):
        """Path inference should be used when no config match."""
        result = resolver.resolve("数学分析/微积分.canvas")
        assert result.source == MetadataSource.INFERRED
        assert result.category == "math"

    def test_default_when_nothing_matches(self, resolver):
        """Default should be used when nothing else matches."""
        result = resolver.resolve("random_stuff.canvas")
        assert result.source == MetadataSource.DEFAULT
        assert result.subject == "general"
        assert result.category == "general"

    def test_manual_subject_alone_defaults_category_to_subject(self, resolver):
        """Story 1.9: 单独给 manual_subject 即生效, category 缺省取 subject。

        CARD-REDBASE-R1 翻新 (原名 test_manual_requires_both_subject_and_category):
        原用例断言「只给 subject → 不走 manual, 落回 config」, 那是 Story 1.9
        **之前**的契约; 实现已改为接受单独 manual_subject —— 见
        subject_resolver.py:208-210 「Story 1.9: Accept manual_subject alone
        (category defaults to subject)」。测试未同步 → 基线即红, 零实现回归。
        按 DD-13 名实一致, 函数名一并改到实际契约。
        """
        result = resolver.resolve(
            "Math 54/离散数学.canvas",
            manual_subject="custom",
        )
        assert result.source == MetadataSource.MANUAL
        assert result.subject == "custom"
        assert result.category == "custom"  # category 缺省 = subject

    def test_config_takes_priority_over_inferred(self, resolver):
        """Config match should win over path inference."""
        # "Math 54/**" matches config, even though "Math 54" could be inferred
        result = resolver.resolve("Math 54/线性代数.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"

    def test_inferred_from_directory_with_category_rule(self, resolver):
        """Inferred should use category rules for directory matching."""
        result = resolver.resolve("物理实验/热力学.canvas")
        assert result.source == MetadataSource.INFERRED
        assert result.category == "physics"


# =============================================================================
# Task 1.2: Glob Pattern Matching
# =============================================================================


class TestGlobPatternMatching:
    """AC-30.19.1: Glob pattern matching for ** and * patterns."""

    def test_double_star_recursive_match(self, resolver):
        """** should match recursively across directories."""
        result = resolver.resolve("Math 54/chapter1/exercise.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"

    def test_double_star_direct_child(self, resolver):
        """** should match direct children too."""
        result = resolver.resolve("Math 54/离散数学.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"

    def test_single_star_single_level(self, resolver):
        """* should match single level only."""
        result = resolver.resolve("CS 189/homework.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "cs189"

    def test_single_star_matches_nested_via_fnmatch(self, resolver):
        """* in fnmatch matches across directories (Python fnmatch behavior)."""
        result = resolver.resolve("CS 189/assignments/hw1.canvas")
        # fnmatch.fnmatch treats * as matching everything including /
        # This is the actual implementation behavior
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "cs189"

    def test_case_insensitive_matching(self, resolver):
        """Pattern matching should be case-insensitive."""
        result = resolver.resolve("math 54/test.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"

    def test_backslash_normalized_to_forward_slash(self, resolver):
        """Windows backslashes should be normalized."""
        result = resolver.resolve("Math 54\\离散数学.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "math54"


# =============================================================================
# Task 1.3: CRUD Operations (add_mapping / remove_mapping)
# =============================================================================


class TestCRUDOperations:
    """AC-30.19.1: add_mapping / remove_mapping CRUD operations."""

    def test_add_new_mapping(self, resolver):
        """Adding a new mapping should persist and be resolvable."""
        success = resolver.add_mapping("Biology 101/**", "bio101", "biology")
        assert success is True

        result = resolver.resolve("Biology 101/genetics.canvas")
        assert result.source == MetadataSource.CONFIG
        assert result.subject == "bio101"
        assert result.category == "biology"

    def test_add_duplicate_pattern_updates_existing(self, resolver):
        """Adding a duplicate pattern should update the existing rule."""
        # Original: Math 54/** → math54, math
        success = resolver.add_mapping("Math 54/**", "math54-updated", "math-new")
        assert success is True

        result = resolver.resolve("Math 54/test.canvas")
        assert result.subject == "math54-updated"
        assert result.category == "math-new"

    def test_remove_existing_mapping(self, resolver):
        """Removing an existing mapping should succeed."""
        success = resolver.remove_mapping("Physics 7A/**")
        assert success is True

        # Should no longer match config
        result = resolver.resolve("Physics 7A/test.canvas")
        assert result.source != MetadataSource.CONFIG or result.subject != "physics7a"

    def test_remove_nonexistent_mapping(self, resolver):
        """Removing a non-existent mapping should return False."""
        success = resolver.remove_mapping("NonExistent/**")
        assert success is False

    def test_remove_case_insensitive(self, resolver):
        """Remove should be case-insensitive on pattern."""
        success = resolver.remove_mapping("math 54/**")
        assert success is True

    def test_add_mapping_persists_to_file(self, resolver, sample_config_yaml):
        """Added mapping should be persisted to YAML file."""
        resolver.add_mapping("History/**", "history", "humanities")

        # Re-read the file
        with open(sample_config_yaml, "r", encoding="utf-8") as f:
            saved_config = yaml.safe_load(f)

        patterns = [m["pattern"] for m in saved_config.get("mappings", [])]
        assert "History/**" in patterns


# =============================================================================
# Task 1.4: YAML Config Persistence Roundtrip
# =============================================================================


class TestConfigPersistence:
    """AC-30.19.3: YAML config persistence roundtrip consistency."""

    def test_update_config_roundtrip(self, resolver, sample_config_yaml):
        """update_config → load_config should produce identical config."""
        original_config = resolver.get_config()

        # Modify and save
        new_config = SubjectMappingConfig(
            mappings=[
                SubjectMappingRule(pattern="Test/**", subject="test", category="test"),
            ],
            category_rules={"test": ["test*"]},
            defaults={"subject": "default-sub", "category": "default-cat"},
        )
        success = resolver.update_config(new_config)
        assert success is True

        # Reload from file
        resolver2 = SubjectResolver(config_path=sample_config_yaml)
        loaded_config = resolver2.get_config()

        assert len(loaded_config.mappings) == 1
        assert loaded_config.mappings[0].pattern == "Test/**"
        assert loaded_config.mappings[0].subject == "test"
        assert loaded_config.defaults.get("subject") == "default-sub"

    def test_load_nonexistent_config_returns_defaults(self, tmp_path):
        """Loading a non-existent config should return defaults."""
        resolver = SubjectResolver(
            config_path=str(tmp_path / "nonexistent.yaml"),
            auto_load=True,
        )
        config = resolver.get_config()
        assert config.defaults.get("subject") == "general"
        assert len(config.mappings) == 0

    def test_load_empty_config_returns_defaults(self, tmp_path):
        """Loading an empty YAML should return defaults."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("", encoding="utf-8")

        resolver = SubjectResolver(config_path=str(config_path))
        config = resolver.get_config()
        assert config.defaults.get("subject") == "general"

    def test_chinese_characters_preserved_in_yaml(self, resolver, sample_config_yaml):
        """Chinese characters should be preserved through save/load cycle."""
        resolver.add_mapping("数学/**", "shuxue", "math")

        # Reload
        resolver2 = SubjectResolver(config_path=sample_config_yaml)
        config = resolver2.get_config()

        chinese_patterns = [m.pattern for m in config.mappings if "数学" in m.pattern]
        assert len(chinese_patterns) > 0

    def test_skip_directories_preserved(self, resolver, sample_config_yaml):
        """Skip directories should be preserved through save/load."""
        # Trigger a save
        resolver.add_mapping("NewPattern/**", "new", "new")

        with open(sample_config_yaml, "r", encoding="utf-8") as f:
            saved = yaml.safe_load(f)

        skip_dirs = saved.get("skip_directories", [])
        assert ".obsidian" in skip_dirs
        assert ".git" in skip_dirs


# =============================================================================
# Task 1.5: sanitize_subject_name Chinese/Special Characters
# =============================================================================


class TestSanitizeSubjectName:
    """AC-30.19.1: _normalize_subject_name handles Chinese and special chars."""

    def test_lowercase_conversion(self, resolver):
        """English names should be lowercased."""
        result = resolver._normalize_subject_name("Math54")
        assert result == "math54"

    def test_spaces_to_hyphens(self, resolver):
        """Spaces should become hyphens."""
        result = resolver._normalize_subject_name("Math 54")
        assert result == "math-54"

    def test_underscores_to_hyphens(self, resolver):
        """Underscores should become hyphens."""
        result = resolver._normalize_subject_name("math_54")
        assert result == "math-54"

    def test_chinese_characters_preserved(self, resolver):
        """Chinese characters should be preserved."""
        result = resolver._normalize_subject_name("数学分析")
        assert "数学分析" in result

    def test_special_characters_removed(self, resolver):
        """Special characters (non-alphanum, non-Chinese) should be removed."""
        result = resolver._normalize_subject_name("Math@54#!")
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result
        assert "math54" in result

    def test_consecutive_hyphens_collapsed(self, resolver):
        """Multiple consecutive hyphens should be collapsed to one."""
        result = resolver._normalize_subject_name("Math   54")
        assert "--" not in result

    def test_empty_string_returns_unknown(self, resolver):
        """Empty input should return 'unknown'."""
        result = resolver._normalize_subject_name("")
        assert result == "unknown"

    def test_only_special_chars_returns_unknown(self, resolver):
        """Only special characters should return 'unknown'."""
        result = resolver._normalize_subject_name("@#$%")
        assert result == "unknown"


# =============================================================================
# Additional: group_id Format
# =============================================================================


class TestGroupIdFormat:
    """Verify group_id format across resolution sources.

    CARD-REDBASE-R1 翻新 (三条基线即红, 零实现回归): 本类原先期望裸
    ``<subject>:<canvas>`` 格式, 那是 ``vault:`` 前缀落地 (def3a27a
    2026-05-05 / ecf16f2c 2026-05-10) **之前**的形态。``vault:`` 前缀的
    规约出处是 D16 (根 CLAUDE.md「Graphiti group_id 命名规约 (Story 2.5.Y
    D16 锁定 2026-05-05)」)。

    ⚠️ 出处精确化 (Codex round-1 L1): D16 原文只列 ``vault:<vault_id>`` /
    ``:<subject_id>`` / ``:<canvas_name>`` 三种形态, 且 ``build_vault_group_id``
    里 subject_id 与 canvas_path **互斥** (subject_config.py:255-262)。本类
    断言的四段是 ``subject_resolver._make_group_id`` (:201-206) 在 D16 三段
    base 之后再拼 canvas 的**组合形态**, 依据是 Phase A0.5-N
    (``_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:77``
    把 ``vault:<vault_id>:<subject>:<canvas>`` 明列为「✅ Phase A0.5-N ship」)。

    vault 段一律用 patch 注入的 ``_PROBE_VAULT`` 哨兵动态组装, 禁硬编码
    仓内 vault 字面量。
    """

    def test_group_id_format_config(self, resolver):
        """Config-resolved group_id = vault:<vault>:<subject>:<canvas>."""
        with patch("app.config.get_current_vault_id", return_value=_PROBE_VAULT):
            result = resolver.resolve("Math 54/离散数学.canvas")
        assert result.group_id == f"vault:{_PROBE_VAULT}:math54:离散数学"

    def test_group_id_format_manual(self, resolver):
        """Manual group_id = vault:<vault>:<manual_subject>:<canvas>."""
        with patch("app.config.get_current_vault_id", return_value=_PROBE_VAULT):
            result = resolver.resolve(
                "any/path.canvas",
                manual_subject="custom",
                manual_category="cat",
            )
        assert result.group_id == f"vault:{_PROBE_VAULT}:custom:path"

    def test_group_id_format_default(self, resolver):
        """Default group_id = vault:<vault>:general:<canvas>."""
        with patch("app.config.get_current_vault_id", return_value=_PROBE_VAULT):
            result = resolver.resolve("random.canvas")
        assert result.group_id == f"vault:{_PROBE_VAULT}:general:random"

    def test_canvas_extension_stripped(self, resolver):
        """Canvas name in group_id should not include .canvas extension."""
        result = resolver.resolve("Math 54/测试.canvas")
        assert ".canvas" not in result.group_id


# =============================================================================
# Additional: extract_canvas_name
# =============================================================================


class TestExtractCanvasName:
    """Verify Canvas name extraction."""

    def test_simple_filename(self, resolver):
        """Simple filename should extract correctly."""
        name = resolver._extract_canvas_name("离散数学.canvas")
        assert name == "离散数学"

    def test_nested_path(self, resolver):
        """Nested path should extract only filename."""
        name = resolver._extract_canvas_name("Math 54/chapter1/离散数学.canvas")
        assert name == "离散数学"

    def test_no_extension(self, resolver):
        """Path without .canvas should return as-is."""
        name = resolver._extract_canvas_name("Math 54/readme.md")
        assert name == "readme.md"
