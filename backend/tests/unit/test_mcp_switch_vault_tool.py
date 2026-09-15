"""CARD-T-SWITCHVAULT 行为门 — switch_vault MCP 工具必须透传真实隔离原因。

真缺陷 (B14_BASE `08100483` 实测): ``app.mcp.tools.infra_tools.switch_vault``
直接读 ``result.vault_name`` / ``result.vault_id``, 而 ``_switch`` 注解并实际
返回 ``JSONResponse`` —— 它没有这两个属性 ⇒ 运行期 ``AttributeError`` 被本函数
的 ``except Exception`` 吞成
``{'success': False, 'error': "'JSONResponse' object has no attribute 'vault_name'"}``。
调用方看到的是一句与真实原因无关的内部类型错误, 而真实原因是: 该端点被 P0-3
写侧隔离, 恒返回 410, 改 vault 要在部署配置里改。

本文件锁死修复后的行为:

- ① (承重, 先红后绿) 工具返回的 ``error`` **不再**是属性错误文案, 而且**逐字等于**
  端点真实 body 的 ``detail[:200]``;
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
- ① 末尾那条**逐字**比对是 Codex round-1 LOW-4 的整改: 只做 token 匹配时, 把文案
  硬编码成 ``error="quarantined"`` 也能全绿; 逐字比对把「透传」本身锁住, 并且让
  ①② 之间产生真实数据依赖 —— 否则②只证明端点契约, 证明不了①调用了该端点。

⚠️ **本文件不证明什么** (Codex round-1 ⑥ 逐条核对后如实登记):
1. 不证明该工具在 live MCP 路由上可达 —— ``switch_vault`` ∈
   ``server.py::QUARANTINED_MCP_TOOLS``, ``/mcp/tools/switch_vault`` 是 410 stub,
   本函数未注册 live 路由 (测试与显式 Python 调用仍能执行本体, 不等于运行期可达);
2. 不证明端点将来解除隔离后 success 分支正确 —— 隔离态下该分支**永不执行**,
   属门未覆盖的路径, 本文件对它**没有任何**约束力;
3. 不锁 ``isinstance(payload, dict)`` 守卫 —— 端点恒返回 dict body, 删掉该守卫
   两条测试仍全绿 (那条路径当前不可达);
4. 不锁成功分支的字段映射 (``vault_name`` / ``vault_id`` 取值) —— 同上, 不可达;
5. **不锁 ``bytes(result.body)`` 转换** (负控 D 实测: 删掉它两条测试仍全绿)。
   实测 ``JSONResponse.body`` 的**运行期**类型恒为 ``bytes``, ``bytes()`` 是 no-op;
   它存在纯粹是为静态类型 —— typeshed 把 ``Response.body`` 标成
   ``bytes | memoryview[int]`` 而 ``json.loads`` 不收 memoryview。⇒ **它由 pyright
   门守, 不由本文件守**。(本条曾一度被写成「能被①的逐字比对间接锁住」, 负控 D 当场
   证伪并更正 —— 关于证据的断言必须先跑一遍再写。)
6. 不锁外层 ``except`` 的文案形态 (负控 E 实测: 退回 ``str(e)[:200]`` 两条仍全绿) ——
   那条路径要靠端点抛异常才显形, 而端点恒正常返回 410。

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

    # ⛔ 承重断言(交叉比对): error 必须**逐字**等于端点真实 body 的 detail(截断到 200),
    # 而不只是「碰巧含某个 token」—— 后者挡不住把文案硬编码成 "quarantined" 的写法
    # (负控 C 实测: token 断言对该变异是绿的, 只有这条逐字比对会红)。这条把「透传」
    # 本身锁住, 并且同时证明上面那次调用确实走到了下面这个端点 —— 两条测试之间因此
    # 有真实数据依赖, 而非各说各话。
    endpoint_resp = asyncio.run(_switch(VaultSwitchRequest(vault_path=_TARGET_VAULT_PATH)))
    endpoint_detail = json.loads(bytes(endpoint_resp.body))["detail"]
    assert res["error"] == endpoint_detail[:200], (
        "error 不是端点 detail 的逐字透传 —— 可能是硬编码文案或落进了兜底分支; "
        f"实测 error={res['error']!r}\n期望 = detail[:200] = {endpoint_detail[:200]!r}"
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
