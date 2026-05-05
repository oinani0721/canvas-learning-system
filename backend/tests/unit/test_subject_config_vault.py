"""Story 2.5.Y Task 1 — build_vault_group_id 单元测试.

覆盖 AC #2:
- vault_id 必填 (空 → ValueError)
- vault: 前缀强制
- subject_id 优先于 canvas_path (互斥)
- canvas_path 提取 stem (复用 extract_canvas_name)
- Unicode vault_id (中文)
- sanitize 处理特殊字符
- is_vault_group_id 辅助检测

Story trace: _bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md
"""

from __future__ import annotations

import pytest

from app.core.subject_config import (
    build_group_id,
    build_vault_group_id,
    is_vault_group_id,
)


# ════════════════════════════════════════════════════════════════════
# vault_id 必填校验 (AC #2)
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_empty_vault_id_raises():
    with pytest.raises(ValueError, match="vault_id is required"):
        build_vault_group_id("")


def test_build_vault_group_id_whitespace_vault_id_raises():
    with pytest.raises(ValueError, match="vault_id is required"):
        build_vault_group_id("   ")


def test_build_vault_group_id_none_raises():
    with pytest.raises(ValueError):
        build_vault_group_id(None)  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════
# 基础组合 (vault_id 单独)
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_minimal():
    """仅 vault_id → vault:<vault_id>."""
    assert build_vault_group_id("cs_61b") == "vault:cs_61b"


def test_build_vault_group_id_chinese_vault_id():
    """中文 vault_id 保留 unicode."""
    assert build_vault_group_id("数学") == "vault:数学"


def test_build_vault_group_id_sanitizes_special_chars():
    """vault_id 含特殊字符 → underscore 替换."""
    assert build_vault_group_id("CS 61B!") == "vault:cs_61b"


def test_build_vault_group_id_lowercase_normalization():
    """ASCII 大写自动小写."""
    assert build_vault_group_id("MathCS") == "vault:mathcs"


# ════════════════════════════════════════════════════════════════════
# subject_id 二级隔离
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_with_subject_id():
    """vault_id + subject_id → vault:<vault>:<subject>."""
    assert (
        build_vault_group_id("cs_61b", subject_id="algorithms")
        == "vault:cs_61b:algorithms"
    )


def test_build_vault_group_id_subject_id_chinese():
    assert (
        build_vault_group_id("cs_61b", subject_id="数据结构")
        == "vault:cs_61b:数据结构"
    )


# ════════════════════════════════════════════════════════════════════
# canvas_path 二级隔离
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_with_canvas_path_extracts_stem():
    """canvas_path 完整路径 → 提取 stem."""
    assert (
        build_vault_group_id("cs_61b", canvas_path="节点/admissibility.md")
        == "vault:cs_61b:admissibility"
    )


def test_build_vault_group_id_with_canvas_path_simple():
    """canvas_path 仅文件名."""
    assert (
        build_vault_group_id("cs_61b", canvas_path="admissibility")
        == "vault:cs_61b:admissibility"
    )


def test_build_vault_group_id_canvas_path_canvas_extension():
    assert (
        build_vault_group_id("数学", canvas_path="离散数学.canvas")
        == "vault:数学:离散数学"
    )


# ════════════════════════════════════════════════════════════════════
# 互斥性: subject_id 优先于 canvas_path
# ════════════════════════════════════════════════════════════════════


def test_build_vault_group_id_subject_id_takes_priority_over_canvas_path():
    """同时传 subject_id 和 canvas_path → 仅 subject_id 生效."""
    result = build_vault_group_id(
        "cs_61b", subject_id="algorithms", canvas_path="admissibility.md"
    )
    assert result == "vault:cs_61b:algorithms"


def test_build_vault_group_id_canvas_path_used_when_subject_id_none():
    """subject_id=None + canvas_path 给定 → canvas_name 生效."""
    result = build_vault_group_id(
        "cs_61b", subject_id=None, canvas_path="admissibility.md"
    )
    assert result == "vault:cs_61b:admissibility"


def test_build_vault_group_id_canvas_path_empty_string_fallback():
    """canvas_path 空 stem → 仅 vault: 前缀, 不加二级."""
    result = build_vault_group_id("cs_61b", canvas_path="")
    assert result == "vault:cs_61b"


def test_build_vault_group_id_canvas_path_untitled_fallback():
    """canvas_path 解析为 untitled → 不加二级."""
    result = build_vault_group_id("cs_61b", canvas_path=".canvas")
    assert result == "vault:cs_61b"


# ════════════════════════════════════════════════════════════════════
# 与旧 build_group_id 对比 (向后兼容验证)
# ════════════════════════════════════════════════════════════════════


def test_legacy_build_group_id_still_works():
    """Story 1.9 build_group_id 不破坏 (向后兼容)."""
    assert build_group_id("math") == "math"
    assert build_group_id("math", "calc") == "math:calc"


def test_legacy_vs_new_format_distinguishable():
    """旧格式与新格式可区分 (vault: 前缀)."""
    legacy = build_group_id("cs_61b", "admissibility")
    new = build_vault_group_id("cs_61b", canvas_path="admissibility")

    assert legacy == "cs_61b:admissibility"
    assert new == "vault:cs_61b:admissibility"
    assert legacy != new


# ════════════════════════════════════════════════════════════════════
# is_vault_group_id 辅助函数
# ════════════════════════════════════════════════════════════════════


def test_is_vault_group_id_recognizes_new_format():
    assert is_vault_group_id("vault:cs_61b") is True
    assert is_vault_group_id("vault:cs_61b:algorithms") is True
    assert is_vault_group_id("vault:数学") is True


def test_is_vault_group_id_rejects_legacy():
    assert is_vault_group_id("cs_61b") is False
    assert is_vault_group_id("cs188") is False
    assert is_vault_group_id("canvas-dev") is False
    assert is_vault_group_id("math:calc") is False


def test_is_vault_group_id_rejects_invalid_input():
    assert is_vault_group_id("") is False
    assert is_vault_group_id(None) is False  # type: ignore[arg-type]
    assert is_vault_group_id(123) is False  # type: ignore[arg-type]
