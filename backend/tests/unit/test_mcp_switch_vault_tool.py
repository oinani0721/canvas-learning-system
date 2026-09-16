"""CARD-T-SWITCHVAULT 行为门 — switch_vault MCP 工具必须透传真实隔离原因。

真缺陷 (B14_BASE `08100483` 实测): ``app.mcp.tools.infra_tools.switch_vault``
直接读 ``result.vault_name`` / ``result.vault_id``, 而 ``_switch`` 注解并实际
返回 ``JSONResponse`` —— 它没有这两个属性 ⇒ 运行期 ``AttributeError`` 被本函数
的 ``except Exception`` 吞成
``{'success': False, 'error': "'JSONResponse' object has no attribute 'vault_name'"}``。
调用方看到的是一句与真实原因无关的内部类型错误, 而真实原因是: 该端点被 P0-3
写侧隔离, 恒返回 410, 改 vault 要在部署配置里改。

⚠️ **证据类型标注** —— 本卡被独立复核连续抓到同一类失分: 把源码推导写成实测、
把局部结论写成全称。因此下面每条声明都标了它的证据类型:

  【实测-负控 X】有对应变异组的 pytest / pyright 记录
  【实测-探针】  有对应的一次性探针记录
  【源码推导】   读代码得出, **没有**跑过对应变异

证据目录 ``_bmad-output/审查/evidence-switchvault/``; 完整证据链见验收单
``_bmad-output/验收单/UAT-CARD-T-SWITCHVAULT-2026-09-16.md``。
⛔ 没有标注的句子不得被当作实测结论引用。

═══════════════════════════════════════════════════════════════════════
本文件锁住什么
═══════════════════════════════════════════════════════════════════════
① ``test_switch_vault_surfaces_quarantine_not_attribute_error`` (承重, 先红后绿):
   工具返回的 ``error`` 不再是属性错误文案, 且**逐字等于**端点 body 的 ``detail[:200]``。
   已实测锁住的回归:
   - 【实测-负控 A】退回 ``result.vault_name`` ⇒ 红在「has no attribute」断言;
   - 【实测-负控 B】删掉 410/error 失败分支 ⇒ 红在 success 断言(该变异下工具返回
     ``success=True``, 即**谎报切换成功**);
   - 【实测-负控 C】把 error 硬编码成短常量 ``"quarantined"`` ⇒ 红在逐字比对断言。
     ⚠️ C 组的实测事实是「该变异下 token 断言**不**红(计数 0)、只有逐字比对红,
     整文件 1 failed / 1 passed」;「若门只剩 token 匹配则该变异全绿」是由此**推出的
     反事实**, 那个形态从未单独跑过。
   - 【实测-负控 K】照原设计稿改回去(删失败分支 + 直接索引 ``payload["vault_name"]``)
     ⇒ 红在 **token 断言**(1 failed / 1 passed)。⇒ 拦住「照设计稿改回去」的是①, 不是②。
   - 【实测-负控 L】删掉失败分支的 ``reason[:200]`` 截断 ⇒ 红在逐字比对断言
     (端点 detail 实测 216 字符 > 200, 【实测-探针】被截掉的尾巴是 ``to change vault.``)。

② ``test_switch_vault_hits_real_quarantine_endpoint`` (端点契约锚, 改前改后都绿):
   证明**本文件直接调用的那个 ``_switch`` 是真实 P0-3 隔离端点** —— 恒 410、body 含
   ``error == "gone"`` 与非空 ``detail``、且**不含** ``vault_name`` / ``vault_id``
   这两个具名键(断言的是这两个具名键缺席, **不是**键集排他)。作用是让①的期望值来源可信。
   它同时把卡文 §〇「口径更正」固化成断言: 设计稿原以为「解析 body 取 vault_name」,
   而端点常量 body 只有 ``{"error", "detail"}``(【源码推导】读 ``vault.py`` 的 410
   常量; evidence 目录**没有**打印过该 body 键集的存档)。
   ⚠️ **归属**: ②约束的是**端点**(端点哪天真加上这两个字段会红)。若后人把**工具**改回
   原设计稿, ②仍绿 —— 变红的是①(【实测-负控 K】)。
   ⚠️ 它**不**证明①那次调用走到了该端点 ——【实测-负控 H】把工具改成跳过端点、直接
   硬编码完整 ``detail[:200]``, 两条测试仍 2 passed。调用链由源码保证
   (``infra_tools.switch_vault`` 函数体内直接 ``await _switch(...)``, 无替换、无 mock)。

⛔ **不 mock、不 monkeypatch ``_switch``** (DD-03): 两条测试都直接 ``await`` 真协程。
   为什么不 mock ——【实测-探针 N】对五种假返回值形状实跑:
   - 同时具备 ``.body`` 与 ``.status_code`` 的假响应(含 body 为坏 JSON 的) ⇒ ①**绿**,
     门形同虚设(此时②也只是在测这个 mock);
   - 缺 ``.body``(如直接返回 dict / SimpleNamespace) 或 缺 ``.status_code`` ⇒ 在
     ``infra_tools`` 读 ``result.body`` / ``result.status_code`` 时抛 AttributeError,
     落进外层 ``except``, error 里反而带上 "has no attribute" ⇒ ①**红**。
   ⇒ ①的真假由 mock 的形状决定、与端点真实行为无关。**不能**说「mock 后①在任何假
   返回值上都恒真」——那是全称断言, 上面第二类形状(三种)就是反例。

═══════════════════════════════════════════════════════════════════════
本文件**不**证明什么
═══════════════════════════════════════════════════════════════════════
1. 不证明该工具在 live MCP 路由上可达。【源码推导】依据是 **MCP 注册面**:
   ``switch_vault`` ∈ ``server.py::QUARANTINED_MCP_TOOLS``,
   ``/mcp/tools/switch_vault`` 注册为 410 stub, 本函数未注册 live 路由。
   ⚠️ 此依据与下面第 2-4、9-10 条的「端点恒 410」**是两回事**, 不可混引。
   准确表述: **当前 MCP 路由不可达**; 测试与显式 Python 调用仍能执行本体。
2. 不证明端点将来解除隔离后 success 分支正确。【源码推导】端点恒 410 ⇒ 该分支永不
   执行, 两条测试对它**没有任何**约束力。
3. 不锁 ``isinstance(payload, dict)`` 守卫。【源码推导】端点恒返回 dict body。
4. 不锁成功分支的字段映射(``vault_name`` / ``vault_id`` 取值)。【源码推导】同上。
5. 不锁 ``bytes(result.body)`` 转换。【实测-负控 D】删掉它两条测试仍 2 passed。
   ⚠️ 证据边界: 负控 D 证明的是「这条路径上 ``json.loads`` 直接接受了 ``result.body``」,
   它推不出「body 恒为 bytes」这个类型断言。【实测-探针】一次观测到
   ``type(resp.body) is bytes``;【源码推导】``JSONResponse.render`` 返回编码后的 bytes,
   故在**当前端点正常返回、body 未被中间层替换**的路径上 ``bytes()`` 是 no-op。
   它存在是为**静态类型**: Starlette ``Response.body`` 的推导类型是
   ``bytes | memoryview[int]``, 而 ``json.loads`` 的签名只收 ``str | bytes | bytearray``。
   ⇒ 本文件不守它, 它由 **pyright 门**守 ——【实测-负控 M】删掉 ``bytes()`` 后
   ``pyright app/mcp/tools/infra_tools.py`` 从 ``0 errors`` 变 ``1 error``, 报在
   ``infra_tools.py:66`` 的 ``json.loads`` 实参上(对照组同一命令 0 errors)。
6. 不锁外层 ``except Exception`` —— **既不锁文案形态, 也不锁它的存在与捕获宽度**。
   【实测-负控 E】把文案退回 ``str(e)[:200]`` 后 2 passed。
   【源码推导】删掉整个 ``try/except`` 或改窄成不匹配的异常类型, 两条测试同样不红 ——
   当前路径上根本不抛异常(端点恒返回常量 410 ``JSONResponse``, 解析与各守卫逐步皆不抛)。
   ⚠️ 触发条件**不是**「必须端点抛异常」: 返回对象缺 ``body``、``status_code`` 不可与
   int 比较等契约外形态同样会落进外层(【实测-探针 N】M1/M2/M3 即此类)。
   ⚠️ 负控 A 的杀伤力**依赖这个 handler 仍在** —— 它正是把原始 AttributeError 吞成
   误导文案的那个机制。
7. 不锁调用链本身。【实测-负控 H】见②的说明。
8. 不锁失败判据的**两侧**。【实测-负控 F】删掉 ``result.status_code >= 400`` 一侧
   → 2 passed;【实测-负控 I】删掉 ``"error" in payload`` 一侧 → 2 passed;
   【实测-负控 G】把 ``or`` 改成 ``and`` → 2 passed。当前端点同时满足两侧(410 且 body
   有 ``error`` 键), 故任一侧单独失效都不显形。
9. 不锁内层异常兜底(``except (TypeError, ValueError)``)。【源码推导】依据是**端点 body
   恒为合法 JSON 字节**(常量 dict 经 ``JSONResponse.render`` 编码), ``json.loads`` 不会
   抛 —— 与 ``detail`` 是否非空**无关**。
10. 不锁 ``detail`` 缺失时的回退链(``detail`` → ``error`` → HTTP 文案)。【源码推导】
   依据才是「当前 body 恒有非空 ``detail``」。第 9、10 条依据不同, 分开登记。
11. 不锁 ``str(detail)`` 类型转换(``infra_tools.py`` 失败分支)。【实测-负控 J】删掉它
   两条测试仍 2 passed。当前 ``detail`` 恒为 str, 该转换是 no-op; 它只在将来 ``detail``
   为非字符串(如 ``7``)时才承重(届时 ``[:200]`` 会抛 TypeError)。

═══════════════════════════════════════════════════════════════════════
运行面
═══════════════════════════════════════════════════════════════════════
本文件只 ``await`` 协程, 不起 TestClient。
【实测】门 1 的 Neo4j live 端口守卫计数 ``NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0``
(blocked=0 / advisory=0 / unaccounted=0) ⇒ 未连现网 Neo4j 端口。
【源码推导】其余端口**无对应计数器**: 被调端点只做一次 ``logger.warning`` 后返回常量
``JSONResponse``; LanceDB 是文件式、本就无端口。
⚠️ 上述计数只覆盖**测试体**; 模块 import 面会加载 RAGService / LangGraph / jieba 等
(见 ``body-runtime-type-probe-*.txt`` 的 import 期日志), 那一面不在该计数器的主张范围内。
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
    # 【实测-负控 K】照原设计稿直接索引 payload["vault_name"] 时, 红的正是这一条。
    lowered = res["error"].lower()
    assert any(token in lowered for token in ("quarantin", "p0-3", "active_vault")), (
        f"error 未透传 P0-3 隔离原因 (期望含 quarantin / p0-3 / active_vault 之一); 实测 res={res!r}"
    )

    # ⛔ 承重断言(交叉比对): error 必须**逐字**等于端点 body 的 detail(截断到 200),
    # 而不只是「碰巧含某个 token」——【实测-负控 C】把文案硬编码成 "quarantined" 时,
    # token 断言不红(计数 0), 只有这一条红。【实测-负控 L】删掉 [:200] 截断时也是这一条红。
    # ⚠️ **边界**(【实测-负控 H】): 这条断言**不能**证明上面那次调用真的走到了下面这个
    # 端点 —— 把工具改成跳过端点、直接硬编码完整 detail[:200], 两条测试仍 2 passed。
    # 它锁住的只是「文案与端点当前 body 逐字一致」; 调用链由源码保证, 不由本断言保证。
    endpoint_resp = asyncio.run(_switch(VaultSwitchRequest(vault_path=_TARGET_VAULT_PATH)))
    endpoint_detail = json.loads(bytes(endpoint_resp.body))["detail"]
    assert res["error"] == endpoint_detail[:200], (
        "error 不是端点 detail 的逐字透传 —— 可能是硬编码文案或落进了兜底分支; "
        f"实测 error={res['error']!r}\n期望 = detail[:200] = {endpoint_detail[:200]!r}"
    )


def test_switch_vault_hits_real_quarantine_endpoint():
    """端点契约锚: **本文件直接调用的**就是真实 P0-3 隔离端点, 不是 mock。改前改后都应绿。

    ⚠️ 本条约束的是端点自身的契约, **不**证明上一条测试走到了这个端点
    (见模块 docstring §「本文件不证明什么」第 7 条 /【实测-负控 H】)。
    """
    resp = asyncio.run(_switch(VaultSwitchRequest(vault_path=_TARGET_VAULT_PATH)))

    assert resp.status_code == 410, (
        f"vault.switch_vault 应恒返回 410 (P0-3 写侧隔离); 实测 status_code={resp.status_code}"
    )

    payload = json.loads(bytes(resp.body))
    assert isinstance(payload, dict), f"隔离响应 body 应为 JSON 对象; 实测 {payload!r}"
    assert payload.get("error") == "gone", f"隔离响应 body 应含 error=gone; 实测 {payload!r}"
    assert payload.get("detail"), f"隔离响应 body 应含非空 detail; 实测 {payload!r}"

    # 卡文 §〇「口径更正」的门: body 里**没有** vault_name / vault_id 这两个具名键
    # (断言的是这两个键缺席, 不是键集排他) —— 所以正确修法是透传 detail。
    # ⚠️ 归属: 这两条约束的是**端点**; 若后人把**工具**改回原设计稿, 红的是①的 token
    # 断言而非本条(【实测-负控 K】)。
    assert "vault_name" not in payload, f"隔离响应 body 不应含 vault_name; 实测 {payload!r}"
    assert "vault_id" not in payload, f"隔离响应 body 不应含 vault_id; 实测 {payload!r}"
