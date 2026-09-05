"""批次1'① 写入层 group_id 强校验回归 (MEM-FLYWHEEL-2026-07-22)。

数据治理三层防线第一层 (ChatGPT R1 裁决): 线上主路径不得把缺失 group_id
静默回落到 DEFAULT_GROUP_ID (vault:default 污染桶) — 必须推导当前 vault 组
(与 P15 已生效的 MCP 工具模式一致), 「缺失回落 default 桶」只准存在于
离线迁移工具。
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.api.v1.endpoints.memory import _resolve_vault_group_id
from fastapi import HTTPException

# CARD-REDBASE-R1 (BATCH-2026-09-05-第十一批): active vault 一律用哨兵值 +
# patch 注入, 不硬编码仓内 vault 字面量 (环境无关)。
_PROBE_ACTIVE_VAULT = "probe_active_vault"


# ⛔ Codex round-1 M2 整改: 只 patch get_current_vault_id **不够** ——
# vault_scope.active_vault_aliases() (vault_scope.py:120-134) 还会读真实
# settings 的 ACTIVE_VAULT 与 CANVAS_BASE_PATH basename 扩别名。实测
# `ACTIVE_VAULT=some_other_vault pytest …::test_explicit_foreign_vault_id_raises_409`
# → `DID NOT RAISE` (实现按合法别名放行是**正确**的, 误红来自测试没固定输入)。
# 故涉及别名集的用例必须把 settings 侧的两个输入一起固定。
def _pinned_settings(active_vault: str, base_dir_name: str) -> SimpleNamespace:
    """给 active_vault_aliases() 用的最小 settings 替身 (只含它读的两个字段)。"""
    return SimpleNamespace(ACTIVE_VAULT=active_vault, CANVAS_BASE_PATH=f"/tmp/{base_dir_name}")


@pytest.fixture(autouse=True)
def _subject_contextvar_hygiene():
    """本文件的解析调用会经 vault_scope._inject 写 ContextVar — 逐条隔离, 防跨用例污染。"""
    from app.core.subject_config import _current_subject_id

    token = _current_subject_id.set(_current_subject_id.get())
    try:
        yield
    finally:
        _current_subject_id.reset(token)


def test_missing_vault_and_group_derives_current_vault():
    """双缺失 → 推导当前 vault 组, 不落 vault:default (契约 3 语义不变)。

    CARD-REDBASE-R1 翻新: 原实现 patch
    ``app.core.subject_config.default_vault_group_id`` 并断言 ``.called`` ——
    CARD-G2-2 把解析收敛进 ``app.core.vault_scope`` 之后, 双缺失分支直接调
    ``build_vault_group_id(active_vault, ...)`` (vault_scope.py:199-201),
    **从不经过** ``default_vault_group_id``, 于是断言的是一条已被取代的
    实现细节 (零实现回归的假红)。
    改法依据 = CARD-G2-2 先例 (patch ``app.config.get_current_vault_id``, 见
    tests/unit/test_lancedb_vault_isolation.py:155-163): 断言**行为**
    (推导结果 = active vault 组, 且不是 vault:default 污染桶), 不再断言调用链。
    """
    with patch("app.config.get_current_vault_id", return_value=_PROBE_ACTIVE_VAULT):
        derived = _resolve_vault_group_id(vault_id=None, legacy_group_id=None)
    assert derived == f"vault:{_PROBE_ACTIVE_VAULT}"
    assert derived != "vault:default"


def test_explicit_vault_id_still_wins():
    """显式 vault_id 优先于 deprecated legacy group_id (原意图不变)。

    CARD-REDBASE-R1 翻新: 原实现传 ``vault_id="cs_61b"`` 而进程 active vault
    是仓内挂载的 vault —— CARD-G2-2 契约 2 起这属「请求 vault ≠ active vault」
    → ``HTTPException(409)`` (vault_scope.py:162-176), 不再返回 vault:cs_61b。
    「显式优先」这一层语义仍然成立, 且可环境无关地证明: 固定 active vault 后
    **同时**传 vault_id 与 legacy_group_id, 结果必须来自 vault_id 一侧。

    ⛔ Codex round-1 5a 整改: 初版让稳定 ID 与 sanitize 后的请求值恰好相等
    ("CS 61B" → "cs_61b" = 稳定 ID), 于是「命中别名后归一到稳定 ID」这一步
    无法与「请求值直接落库」区分。本版把稳定 ID 设成与目录名**不同**的
    ``cs61b_stable``, 请求传目录名 "CS 61B"。

    ⚠️ 鉴别力边界 (Codex round-2 LOW): 这**排除了「直接采用 sanitize 后的请求值」**
    这一类实现 (变异实测: 把 :177-181 的 ``active_vault`` 换成 ``requested``
    → 得 ``vault:cs_61b``, 本条断言红)。它**不能**排除「把两个参数都丢掉、
    走双缺失分支 (:191-202)」—— 那条分支同样返回 ``vault:<active_vault>``,
    本条断言照样绿 (Codex round-2 内存变异实测 PASS)。
    「显式优先于 legacy」这一层由 legacy 值与结果不同来保证; 「显式参数确实被
    消费」则由本文件的 409 用例 (跨 vault 显式值必须触发 409, 双缺失分支不会)
    与 tests/unit/test_vault_scope_409.py:95 共同兜底。
    原用例「跨 vault 显式 id 直接采用」那一半已失效, 由下面的
    test_explicit_foreign_vault_id_raises_409 取代; 环境无关的既有覆盖另见
    tests/unit/test_vault_scope_409.py:77 / :95 / :118 / :126。
    """
    stable_id = "cs61b_stable"
    with (
        patch("app.config.get_current_vault_id", return_value=stable_id),
        patch("app.config.get_settings", return_value=_pinned_settings("CS 61B", "CS 61B")),
    ):
        derived = _resolve_vault_group_id(vault_id="CS 61B", legacy_group_id="vault:some_other_group")
    # 归一到稳定 ID, 不是请求里的目录名 —— 证明别名归一化确实发生了。
    assert derived == f"vault:{stable_id}"
    assert derived != "vault:cs_61b"


def test_explicit_foreign_vault_id_raises_409():
    """CARD-G2-2 契约 2: 请求 vault ≠ 进程 active vault → 409 fail-closed。

    CARD-REDBASE-R1 新增 —— 取代原 test_explicit_vault_id_still_wins 里已失效的
    「跨 vault 显式 id 直接采用」断言 (改写而非直删: 语义拆成 match/mismatch
    两条)。与 tests/unit/test_vault_scope_409.py:77 同契约, 此处从**写侧入口**
    (memory.py 的 ``_resolve_vault_group_id``) 再证一次, 保证写侧不绕过 409。

    ⛔ Codex round-1 M2 整改: 别名集的**三个**输入必须一起固定, 否则真实
    ``ACTIVE_VAULT`` / ``CANVAS_BASE_PATH`` basename 可能恰好等于本用例选的
    foreign 名, 于是实现正确放行而测试误红 (实测 `ACTIVE_VAULT=some_other_vault`
    → `DID NOT RAISE`)。
    """
    with (
        patch("app.config.get_current_vault_id", return_value="cs_61b"),
        patch("app.config.get_settings", return_value=_pinned_settings("cs_61b", "cs_61b")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            _resolve_vault_group_id(vault_id="some_other_vault")
    assert exc_info.value.status_code == 409


def test_legacy_group_id_still_honored():
    derived = _resolve_vault_group_id(vault_id=None, legacy_group_id="vault:cs_61b")
    assert derived == "vault:cs_61b"


def test_no_default_group_id_fallback_in_write_paths():
    """静态守卫: memory.py / MCP 写工具源码不再引用 DEFAULT_GROUP_ID 回落。

    (注释里提及不算; 只拦 `= DEFAULT_GROUP_ID` 赋值与 import 后实际使用)
    """
    import inspect

    from app.api.v1.endpoints import memory as memory_ep
    from app.mcp.tools import conversation_tools, memory_tools

    for mod in (memory_ep, memory_tools, conversation_tools):
        src = inspect.getsource(mod)
        offending = [
            ln.strip()
            for ln in src.splitlines()
            if "= DEFAULT_GROUP_ID" in ln and not ln.strip().startswith("#")
        ]
        assert offending == [], (
            f"{mod.__name__} 仍有 DEFAULT_GROUP_ID 回落: {offending}"
        )
