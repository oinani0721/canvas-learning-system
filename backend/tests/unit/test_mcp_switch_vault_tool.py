"""CARD-T-SWITCHVAULT 行为门 — switch_vault MCP 工具必须透传真实隔离原因。

真缺陷 (B14_BASE `08100483` 实测): ``app.mcp.tools.infra_tools.switch_vault``
直接读 ``result.vault_name`` / ``result.vault_id``, 而 ``_switch`` 注解并实际
返回 ``JSONResponse`` —— 它没有这两个属性 ⇒ 运行期 ``AttributeError`` 被本函数
的 ``except Exception`` 吞成
``{'success': False, 'error': "'JSONResponse' object has no attribute 'vault_name'"}``。
调用方看到的是一句与真实原因无关的内部类型错误, 而真实原因是: 该端点被 P0-3
写侧隔离, 恒返回 410, 改 vault 要在部署配置里改。

本文件锁死修复后的行为:

- ① (承重, 先红后绿) 工具返回的 ``error`` **不再**是属性错误文案, 而含真实
  隔离原因 (quarantin / P0-3 / ACTIVE_VAULT 任一);
- ② (验伪锚, 改前改后都绿) 被调端点确实是**真实**的 P0-3 隔离端点 ——
  ``status_code == 410`` 且 body 里**没有** vault_name / vault_id。

⚠️ 门设计说明 (防假绿):
- ⛔ **不 mock、不 monkeypatch ``_switch``** (DD-03): 两条测试都直接 ``await``
  真协程。若 mock 掉端点, ①「不含属性错误」在任何假返回值上都恒真, 门等于没有。
- ② 是 ① 的**无 mock 自证**: 它独立证明「①打到的是真实隔离端点」。没有它,
  ①绿也可能只是因为被换成了一个凑巧合意的返回值。
- ② 同时锁住卡文 §〇 的「口径更正」: 设计稿原以为「解析 body 取 vault_name」,
  实测 body 只有 ``{"error", "detail"}``。这条断言防后人照原设计稿改回去。
- ⛔ ① **不得**弱化成「只断言 success is False」—— 改前改后都成立, 锁不住修复。

⚠️ **本文件不证明什么**: 不证明该工具在 live MCP 路由上可达
(``switch_vault`` ∈ ``server.py::QUARANTINED_MCP_TOOLS``, ``/mcp/tools/switch_vault``
是 410 stub, 本函数未注册 live 路由); 不证明端点将来解除隔离后 success 分支
正确 (隔离态下该分支永不执行, 无真实成功响应可测)。

本文件只 ``await`` 协程, 不起 TestClient、不连 Neo4j / LanceDB / 任何端口 ——
被调端点只做一次 ``logger.warning`` 后返回常量 ``JSONResponse``。
"""

from __future__ import annotations

import asyncio
import json

from app.api.v1.endpoints.vault import VaultSwitchRequest
from app.api.v1.endpoints.vault import switch_vault as _switch
from app.mcp.tools.infra_tools import SwitchVaultInput, switch_vault

# 不存在的目录; 隔离端点在 410 早返回前从不触碰文件系统, 该值只作为字符串
# 进 logger.warning 的结构化字段。
_TARGET_VAULT_PATH = "/tmp/nonexistent-vault-t5c"


def test_switch_vault_surfaces_quarantine_not_attribute_error():
    """工具必须把 410 的真实原因透传给调用方, 而不是内部属性错误文案。"""
    res = asyncio.run(switch_vault(SwitchVaultInput(vault_path=_TARGET_VAULT_PATH)))

    # 隔离态下工具必然失败 —— 改前改后都成立, 单独不足以锁住修复, 只作前置。
    assert res["success"] is False, f"隔离端点恒 410, 工具不应报成功; 实测 res={res!r}"

    # ⛔ 承重断言: 改前这里必红 (error 恒为 AttributeError 的字符串化)。
    assert "has no attribute" not in res["error"], (
        "switch_vault 仍把 result.vault_name 的 AttributeError 吞成 error —— "
        f"调用方看到的是内部类型错误而非真实原因; 实测 res={res!r}"
    )

    # ⛔ 承重断言: 必须是**隔离原因**本身, 而不只是「某个别的错误」。
    lowered = res["error"].lower()
    assert any(token in lowered for token in ("quarantin", "p0-3", "active_vault")), (
        f"error 未透传 P0-3 隔离原因 (期望含 quarantin / p0-3 / active_vault 之一); 实测 res={res!r}"
    )


def test_switch_vault_hits_real_quarantine_endpoint():
    """验伪锚: 上一条打的是真实 P0-3 隔离端点, 不是 mock。改前改后都应绿。"""
    resp = asyncio.run(_switch(VaultSwitchRequest(vault_path=_TARGET_VAULT_PATH)))

    assert resp.status_code == 410, (
        f"vault.switch_vault 应恒返回 410 (P0-3 写侧隔离); 实测 status_code={resp.status_code}"
    )

    payload = json.loads(bytes(resp.body))
    assert isinstance(payload, dict), f"隔离响应 body 应为 JSON 对象; 实测 {payload!r}"
    assert payload.get("error") == "gone", f"隔离响应 body 应含 error=gone; 实测 {payload!r}"
    assert payload.get("detail"), f"隔离响应 body 应含非空 detail; 实测 {payload!r}"

    # 卡文 §〇「口径更正」的门: body 里**没有** vault_name / vault_id ——
    # 所以正确修法是透传 detail, 不是去取这两个不存在的字段。
    assert "vault_name" not in payload, f"隔离响应 body 不应含 vault_name; 实测 {payload!r}"
    assert "vault_id" not in payload, f"隔离响应 body 不应含 vault_id; 实测 {payload!r}"
