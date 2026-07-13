"""T1 group_id 读写格式统一 (2026-07-10 交接任务书) — 物理边界转换单元测试.

覆盖:
- sanitize_group_id_for_graphiti: D16 冒号 → 物理 __ (P0-5 既有行为不回归)
- desanitize_group_id_from_graphiti: 物理 __ → D16 冒号 (往返无损)
- to_physical_group_id: 唯一物理边界入口 (canonical 归一 + sanitize 组合)
  - 幂等防御: 已物理化输入原样返回 (双重调用不产生 vault__vault__x 损坏)
  - deprecated 值 (cs188) 经 canonical 映射到 vault__default

背景: 写侧 (episode_worker/structured_writer) 在 Graphiti 边界 sanitize 为
__ 格式, 但部分读侧 (fulltext Tier 2 等) 用冒号直查 → 恒空。T1 把物理层
统一为 __ 并让所有 Cypher 边界过 to_physical_group_id。
"""

from __future__ import annotations

from app.graphiti.group_id_compat import (
    desanitize_group_id_from_graphiti,
    sanitize_group_id_for_graphiti,
    to_physical_group_id,
)

# ════════════════════════════════════════════════════════════════════
# sanitize / desanitize — P0-5 既有行为不回归
# ════════════════════════════════════════════════════════════════════


def test_sanitize_single_level_vault():
    assert sanitize_group_id_for_graphiti("vault:cs_61b") == "vault__cs_61b"


def test_sanitize_two_level_vault_subject():
    assert (
        sanitize_group_id_for_graphiti("vault:cs_61b:algorithms")
        == "vault__cs_61b__algorithms"
    )


def test_sanitize_legacy_no_colon_unchanged():
    assert sanitize_group_id_for_graphiti("cs188") == "cs188"


def test_sanitize_empty_passthrough():
    assert sanitize_group_id_for_graphiti("") == ""


def test_desanitize_roundtrip():
    original = "vault:canvas_vault"
    assert (
        desanitize_group_id_from_graphiti(sanitize_group_id_for_graphiti(original))
        == original
    )


def test_desanitize_two_level_roundtrip():
    original = "vault:cs_61b:algorithms"
    assert (
        desanitize_group_id_from_graphiti(sanitize_group_id_for_graphiti(original))
        == original
    )


# ════════════════════════════════════════════════════════════════════
# to_physical_group_id — T1 唯一物理边界入口
# ════════════════════════════════════════════════════════════════════


def test_physical_from_d16_colon():
    assert to_physical_group_id("vault:canvas_vault") == "vault__canvas_vault"


def test_physical_from_two_level_d16():
    assert (
        to_physical_group_id("vault:cs_61b:algorithms") == "vault__cs_61b__algorithms"
    )


def test_physical_idempotent_on_already_physical():
    """幂等防御: 已物理化输入原样返回.

    没有这层防御, canonical_group_id 会把 vault__x 回旋成
    vault:vault__x → sanitize → vault__vault__x (数据损坏)。
    """
    assert to_physical_group_id("vault__canvas_vault") == "vault__canvas_vault"


def test_physical_double_call_safe():
    once = to_physical_group_id("vault:canvas_vault")
    twice = to_physical_group_id(once)
    assert once == twice == "vault__canvas_vault"


def test_physical_deprecated_cs188_maps_to_default():
    """cs188 经 canonical_group_id 映射到 vault:default → 物理 vault__default."""
    assert to_physical_group_id("cs188") == "vault__default"


def test_physical_raw_vault_name_normalized():
    """未规范原始名 (含空格大写) 经 canonical sanitize 后物理化."""
    assert to_physical_group_id("CS 61B") == "vault__cs_61b"


def test_physical_empty_passthrough():
    assert to_physical_group_id("") == ""


def test_physical_then_desanitize_returns_canonical_d16():
    """读回方向: 物理格式 desanitize 后 == canonical D16 (API 对外一致)."""
    physical = to_physical_group_id("vault:canvas_vault")
    assert desanitize_group_id_from_graphiti(physical) == "vault:canvas_vault"


# ════════════════════════════════════════════════════════════════════
# semantic_group_id — M2 双图隔离 (2026-07-13 路线图 v2)
# ════════════════════════════════════════════════════════════════════

from app.graphiti.group_id_compat import semantic_group_id


def test_semantic_from_logical_d16():
    assert semantic_group_id("vault:canvas_vault") == "vault:canvas_vault:semantic"


def test_semantic_from_physical_form():
    """物理形态输入 → 物理形态影子 (分隔符跟随输入)."""
    assert semantic_group_id("vault__canvas_vault") == "vault__canvas_vault__semantic"


def test_semantic_idempotent():
    once = semantic_group_id("vault:canvas_vault")
    assert semantic_group_id(once) == once


def test_semantic_idempotent_physical():
    once = semantic_group_id("vault__canvas_vault")
    assert semantic_group_id(once) == once


def test_semantic_roundtrip_with_physical():
    """影子逻辑 group 经 to_physical 后 == 物理主 group 的影子 (通路一致)."""
    logical_shadow = semantic_group_id("vault:canvas_vault")
    assert to_physical_group_id(logical_shadow) == "vault__canvas_vault__semantic"


def test_semantic_empty_passthrough():
    assert semantic_group_id("") == ""


# ════════════════════════════════════════════════════════════════════
# M1-E2E (2026-07-13) — 中文白板名段 punycode 编码 (graphiti validator 合规)
# ════════════════════════════════════════════════════════════════════

import re as _re

from app.graphiti.group_id_compat import semantic_group_id

_GRAPHITI_ALPHABET = _re.compile(r"^[A-Za-z0-9_-]+$")
_CN = "vault:canvas_vault:特征值与特征向量"


def test_sanitize_chinese_segment_is_validator_safe():
    out = sanitize_group_id_for_graphiti(_CN)
    assert _GRAPHITI_ALPHABET.match(out), out
    assert out.startswith("vault__canvas_vault__xn--")


def test_sanitize_chinese_roundtrip_lossless():
    assert desanitize_group_id_from_graphiti(sanitize_group_id_for_graphiti(_CN)) == _CN


def test_sanitize_chinese_idempotent():
    once = sanitize_group_id_for_graphiti(_CN)
    assert sanitize_group_id_for_graphiti(once) == once


def test_sanitize_physical_chinese_input_normalized():
    # 已物理化但含中文段 (结构化直写历史形态) → 同样收敛到 punycode 形态
    physical_cn = "vault__canvas_vault__特征值与特征向量"
    assert sanitize_group_id_for_graphiti(
        physical_cn
    ) == sanitize_group_id_for_graphiti(_CN)


def test_semantic_of_sanitized_chinese_is_validator_safe():
    # episode_worker 实际组合链: semantic_group_id(sanitize(gid))
    out = semantic_group_id(sanitize_group_id_for_graphiti(_CN))
    assert _GRAPHITI_ALPHABET.match(out), out
    assert out.endswith("__semantic")


def test_semantic_legacy_bare_group_stays_validator_safe():
    # legacy 裸值无冒号 → 视为物理形态, 拼 __semantic 而非 :semantic
    assert semantic_group_id("cs188") == "cs188__semantic"


def test_desanitize_semantic_chinese_roundtrip():
    phys = semantic_group_id(sanitize_group_id_for_graphiti(_CN))
    assert desanitize_group_id_from_graphiti(phys) == f"{_CN}:semantic"
