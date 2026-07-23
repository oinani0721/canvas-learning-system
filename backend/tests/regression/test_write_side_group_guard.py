"""批次1'① 写入层 group_id 强校验回归 (MEM-FLYWHEEL-2026-07-22)。

数据治理三层防线第一层 (ChatGPT R1 裁决): 线上主路径不得把缺失 group_id
静默回落到 DEFAULT_GROUP_ID (vault:default 污染桶) — 必须推导当前 vault 组
(与 P15 已生效的 MCP 工具模式一致), 「缺失回落 default 桶」只准存在于
离线迁移工具。
"""

from unittest.mock import patch

from app.api.v1.endpoints.memory import _resolve_vault_group_id


def test_missing_vault_and_group_derives_current_vault(monkeypatch):
    """双缺失 → 推导当前 vault 组, 不落 vault:default。"""
    with patch(
        "app.core.subject_config.default_vault_group_id",
        return_value="vault:canvas_vault",
    ) as mock_derive:
        derived = _resolve_vault_group_id(vault_id=None, legacy_group_id=None)
    assert mock_derive.called
    assert derived == "vault:canvas_vault"
    assert derived != "vault:default"


def test_explicit_vault_id_still_wins():
    derived = _resolve_vault_group_id(vault_id="cs_61b")
    assert derived == "vault:cs_61b"


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
