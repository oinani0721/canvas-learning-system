"""CARD-G4-1a 读侧作用域单元门 (BATCH-2026-08-29-第六批).

契约: .claude/rules/cypher-read-contract.md R1 / R4
被测: app.core.vault_scope.{require_read_group, read_scope_params,
      read_group_filter, group_in_read_scope}

本文件是**不依赖 Neo4j** 的那一半门 —— 前缀语义的真值表、fail-closed 的触发
边界、以及"fail-closed 不会误伤正常读"的反向断言。真库行为门在
tests/integration/test_cypher_contract_gate.py 的门 6 (需 7692 容器)。

两类门缺一不可:
  - 泄漏门 (他 vault 不可见) 单独存在时, "把过滤写死成永远返回空"也能全绿;
  - 保召回门 (本 vault 子组仍可见) 单独存在时, 不过滤也能全绿。
"""

from __future__ import annotations

import pytest

from app.core.subject_config import _current_subject_id
from app.core.vault_scope import (
    VaultScopeUnresolved,
    allow_cross_vault,
    group_in_read_scope,
    read_group_filter,
    read_scope_params,
    require_read_group,
)

VAULT_A = "vault:g41a_alpha"
VAULT_B = "vault:g41a_beta"


@pytest.fixture
def scope_a():
    """把 per-request 作用域钉在 vault A (ContextVar 分支)。"""
    token = _current_subject_id.set(VAULT_A)
    try:
        yield VAULT_A
    finally:
        _current_subject_id.reset(token)


# ---------------------------------------------------------------------------
# require_read_group — 三级解析链
# ---------------------------------------------------------------------------


def test_explicit_group_wins_over_contextvar(scope_a):
    """分支 1: 显式值优先, 不被 ContextVar 覆盖."""
    assert require_read_group(VAULT_B, context="t") == VAULT_B


def test_falls_back_to_contextvar(scope_a):
    """分支 2: 不传时取 per-request ContextVar."""
    assert require_read_group(context="t") == VAULT_A


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_explicit_is_fail_closed(scope_a, blank):
    """显式空白串 = 调用方 bug, **不得**静默改用 ContextVar 的作用域。

    与写侧 `neo4j_client._resolve_physical_group_id` 的 C1 口径统一 (Codex
    G2-3 round-2/3): 调用方以为自己传了作用域, 悄悄换成另一个比报错危险。
    想走推导链请显式传 None。
    """
    with pytest.raises(VaultScopeUnresolved):
        require_read_group(blank, context="t")


def test_physical_format_input_is_not_corrupted():
    """物理格式入参必须原样往返 —— canonical_group_id 认不出 `vault__x`,
    直接喂给它会腐化成 vault:vault_x (再物理化 = vault__vault_x 数据损坏)。"""
    assert require_read_group("vault__g41a_alpha", context="t") == VAULT_A


def test_punycode_subgroup_round_trips_to_same_physical():
    """现网存量组形态: 中文白板 punycode 子组必须往返不漂移."""
    phys = "vault__canvas_vault__xn--jhqx6ce6ettpca6420ada2925d"
    assert read_scope_params(phys, context="t")["group_id"] == phys


def test_fail_closed_when_no_scope_resolvable(monkeypatch):
    """分支 3: 连 active vault 都推导不出 → 显式抛错, **不**回落
    DEFAULT_GROUP_ID, 也不返回 None 让下游变成全库扫描。

    ⚠️ Codex round-1 H-1 整改: 不能直接把 getter patch 成空串 —— 那绕开了真实
    的 ``sanitize_vault_id``, 而它对空 ``ACTIVE_VAULT`` 返回的是 ``"default"``
    (不是空)。本用例先**实证**这条链, 再用它的真实产物做输入。
    """
    from app.config import sanitize_vault_id

    # 实证: 配置坏掉时 sanitizer 给出的不是空, 而是 "default"
    assert sanitize_vault_id("") == "default"

    monkeypatch.setattr(
        "app.config.get_current_vault_id", lambda: sanitize_vault_id("")
    )
    token = _current_subject_id.set("general")  # ContextVar 处于默认值
    try:
        with pytest.raises(VaultScopeUnresolved) as exc:
            require_read_group(context="unit.no_vault")
    finally:
        _current_subject_id.reset(token)
    # 异常必须带调用点上下文 (出事时能直接定位是谁没有作用域)
    assert "unit.no_vault" in str(exc.value)


@pytest.mark.parametrize("malformed", ["vault:", "vault__", "vault:a:", "vault: "])
def test_malformed_scope_is_rejected(scope_a, malformed):
    """M-4: 形状非法的显式作用域必须抛, 不能当成有效作用域。

    ``canonical_group_id("vault:")`` 原样返回, 物理化成 ``"vault__"``, 前缀锚
    变 ``"vault____"`` —— 不会全库扫描, 但会把非法配置伪装成正常空结果。
    """
    with pytest.raises(VaultScopeUnresolved):
        require_read_group(malformed, context="unit.malformed")


def test_derived_default_bucket_is_rejected(monkeypatch):
    """H-1: **推导**出 vault:default 污染桶 = 配置断裂, 必须 fail-closed。

    它与写侧 active vault 组异组, 召回恒空 (UAT D2 实测根因) —— 读它等于
    "查询成功、一条没有"的假空。
    """
    monkeypatch.setattr("app.config.get_current_vault_id", lambda: "default")
    token = _current_subject_id.set("general")
    try:
        with pytest.raises(VaultScopeUnresolved, match="pollution"):
            require_read_group(context="unit.derived_default")
    finally:
        _current_subject_id.reset(token)


def test_explicit_deprecated_group_still_allowed(scope_a, caplog):
    """反向: 调用方**显式**传 deprecated 值仍放行 (G2-2 契约 4 兼容层不由本卡
    推翻), 但必须告警 —— 区别在于"推导落桶"是故障, "显式指定"是调用方选择。"""
    assert require_read_group("cs188", context="unit.deprecated") == "vault:default"


def test_fail_closed_does_not_fire_on_normal_read(monkeypatch):
    """反向断言 (Codex 审查点: "fail-closed 是否会静默断读"):
    ContextVar 未注入的**正常**后台/CLI 路径不得抛错 —— 应推导 active vault。"""
    monkeypatch.setattr("app.config.get_current_vault_id", lambda: "g41a_alpha")
    token = _current_subject_id.set("general")
    try:
        assert require_read_group(context="unit.background") == VAULT_A
    finally:
        _current_subject_id.reset(token)


# ---------------------------------------------------------------------------
# read_scope_params / read_group_filter — Cypher 绑定面
# ---------------------------------------------------------------------------


def test_scope_params_are_physical_with_separator_anchor(scope_a):
    params = read_scope_params(context="t")
    assert params == {
        "group_id": "vault__g41a_alpha",
        "group_prefix": "vault__g41a_alpha__",
    }
    # 锚点必须带 `__`: 裸前缀会让 vault__a 误配 vault__ab
    assert params["group_prefix"].endswith("__")


def test_group_filter_fragment_shape():
    assert read_group_filter("n") == (
        "(n.group_id = $group_id OR n.group_id STARTS WITH $group_prefix)"
    )


def test_group_filter_null_tolerance_is_opt_in():
    """默认严格 (NULL 不可见); allow_null 必须显式开启."""
    assert "IS NULL" not in read_group_filter("n")
    assert read_group_filter("r", allow_null=True) == (
        "(r.group_id IS NULL OR r.group_id = $group_id "
        "OR r.group_id STARTS WITH $group_prefix)"
    )


# ---------------------------------------------------------------------------
# group_in_read_scope — 内存侧真值表 (与 Cypher 片段逐字同语义)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "candidate,scope,visible,why",
    [
        # ── 保召回: vault 根组读, 三类二级子组全部可见 ──────────────────
        ("vault:g41a_alpha", VAULT_A, True, "根组自身"),
        ("vault:g41a_alpha:board_x", VAULT_A, True, "canvas 子组"),
        ("vault__g41a_alpha__semantic", VAULT_A, True, "semantic 影子组"),
        (
            "vault__g41a_alpha__xn--jhqx6ce6ettpca6420ada2925d",
            VAULT_A,
            True,
            "punycode 中文白板子组 (现网存量数据的实际落点)",
        ),
        # ── 零泄漏: 他 vault 一律不可见 ────────────────────────────────
        ("vault:g41a_beta", VAULT_A, False, "他 vault 根组"),
        ("vault:g41a_beta:board_x", VAULT_A, False, "他 vault 子组"),
        # ── 前缀不得跨 vault 误配 (`__` 定界符的作用) ──────────────────
        ("vault:g41a_alphaX", VAULT_A, False, "同前缀不同 vault"),
        ("vault__g41a_alphabet", VAULT_A, False, "更长的同前缀 vault"),
        # ── 保隔离: canvas 级读仍只见自己 (前缀语义不得放宽成 vault 级) ──
        (
            "vault:g41a_alpha:board_x",
            "vault:g41a_alpha:board_x",
            True,
            "自身",
        ),
        (
            "vault:g41a_alpha:board_x:semantic",
            "vault:g41a_alpha:board_x",
            True,
            "自身的影子子组",
        ),
        (
            "vault:g41a_alpha:board_y",
            "vault:g41a_alpha:board_x",
            False,
            "兄弟白板 — 这条红了说明隔离被放宽成 vault 级",
        ),
        (
            "vault:g41a_alpha",
            "vault:g41a_alpha:board_x",
            False,
            "父组 — 子组读不得反向看到全 vault",
        ),
        # ── 无归属 / 无作用域 一律 fail-closed ─────────────────────────
        ("", VAULT_A, False, "无 group 的记录不属于任何 vault 可见面"),
        (None, VAULT_A, False, "同上 (None)"),
        ("vault:g41a_alpha", "", False, "无作用域不放行任何东西"),
        ("vault:g41a_alpha", None, False, "同上 (None)"),
    ],
)
def test_group_in_read_scope_truth_table(candidate, scope, visible, why):
    assert group_in_read_scope(candidate, scope) is visible, why


def test_logical_and_physical_forms_are_interchangeable():
    """内存 episode 存逻辑格式、库内存物理格式 —— 混比不得静默失配 (T1 原坑)."""
    assert group_in_read_scope("vault:g41a_alpha:board_x", "vault__g41a_alpha")
    assert group_in_read_scope("vault__g41a_alpha__board_x", "vault:g41a_alpha")


# ---------------------------------------------------------------------------
# allow_cross_vault — 显式豁免装饰器 (census / 管理端)
# ---------------------------------------------------------------------------


def test_allow_cross_vault_reexported_is_the_same_object():
    """必须是 cypher_helpers 那一个, 不是同名副本 —— 两个装饰器会让静态审计
    与 lefthook lint 只认其中一个。"""
    from app.utils import cypher_helpers

    assert allow_cross_vault is cypher_helpers.allow_cross_vault


def test_allow_cross_vault_marks_function():
    @allow_cross_vault(reason="unit: census scans all vaults")
    def scan_all():
        return 1

    assert scan_all._allow_cross_vault_reason == "unit: census scans all vaults"
