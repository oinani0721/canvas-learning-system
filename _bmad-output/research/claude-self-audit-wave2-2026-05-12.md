# Claude Self-Audit: Wave-2 hotfix (f018580) verification

> 这是 Claude 作为 second-pair-of-eyes 对 wave-2 hotfix 的独立 audit,生成时点 ChatGPT v4 verdict 尚未回来。用户可拿这份与 ChatGPT v4 verdict 交叉比对。
>
> Audit 心态:不假设 wave-2 一定正确,从 ChatGPT v2 的 5 个 verdict 出发逐项验证代码真相。
>
> 证据获取方式:直接读 worktree 文件(commit `0cf6d3b` 状态),grep + targeted read。

---

## Verdict-1 (frontend X-CLS-Internal-Key): **CLOSED ✅**

**Evidence**:
- `main.ts:146` `internalApiKey: string` 字段加入 `CanvasPluginSettings`
- `main.ts:153` `DEFAULT_SETTINGS` 默认空串 (dev mode 兼容)
- `main.ts:373-381` `buildBackendHeaders()` helper:
  - 始终含 `Content-Type: application/json`
  - 仅当 `internalApiKey` 非空 + 长度 > 0 时加 `X-CLS-Internal-Key` (conditional 注入正确)
- 5 fetch sites 全部用 helper:
  - line 685 (handleChatWithContext) ✓
  - line 865 (handleStudyQuestion) ✓
  - line 1006 (handleGlobalSearch) ✓
  - line 2105 (callBackend POST 路径) ✓
  - line 2324 (postErrorCandidateAction) ✓
- `callBackend` GET 路径独立 inline 逻辑 (line 2105-2112),仅注入 `X-CLS-Internal-Key` 不加 `Content-Type` (正确,GET 无 body)
- Settings UI line 2587-2598 加 "Internal API Key" 字段 + 描述
- `handleOpenNodeChat` (line 1086) 不调 backend (clipboard-only),故不需要 header

**测试**: 13 个新测试 (`tests/auth-headers.test.ts`) + 186/186 frontend tests pass

**潜在 edge case (P2 微)**: `internalApiKey === " "` (空白字符串) 会过 `length > 0` 检查 → 发送空白 key 触发 backend 403。可加 `.trim()` 强化,但属 P2 美化。

---

## Verdict-2 (LanceDB vault wiring): **CLOSED ✅**

**Evidence** (`lancedb_client.py:384-440`):
- Property `active_vault_id` 实现 4 级 fallback:
  1. Line 400-401: `_vault_id_override` (constructor 显式参数,test 用) ✓
  2. Line 410-432: `get_current_subject_id()` ContextVar
     - Strip `vault:` prefix (line 421): `vault:cs_61b:algorithms` → `cs_61b:algorithms`
     - Take first segment (line 423): `derived.split(":", 1)[0]` → `cs_61b`
     - 验证 3 种 group_id 格式: `vault:X` → `X` / `vault:X:subject` → `X` / `vault:X:subject:canvas` → `X` 全部正确
  3. Line 435-438: `app.config.get_current_vault_id()` legacy fallback
  4. Line 440 (implicit else): `return "default"` ✓
- Line 450 `resolve_table_name` 使用 `active_vault_id` property → 每次访问 dynamic 派生 (符合 per-request 隔离契约)

**设计选择验证**: 维持 `_supp_lancedb_singleton` 单 instance + per-request `active_vault_id` 动态解析,而非 per-vault dict cache:
- 优势 1: BGE-M3 model (~3GB / 60s cold-start) 只加载一次
- 优势 2: 5 vault 并发零额外 cold-start
- 必要条件: 所有 endpoint 入口必须调 `set_current_subject_id(...)` 注入 ContextVar — wave-1 已经在 chat_router 三个 endpoint (enrich-context + post-turn-extract + global-search) 顶部加入,契约成立 ✓

**测试**: 9 个新测试 (`test_lancedb_vault_isolation.py::TestActiveVaultIdReadsSubjectContextVar` + Fallback) + chat.py 3 个集成测试

**潜在 P1 残余风险**: 如果未来某个 backend service 直接构造 `LanceDBClient()` 而不通过 endpoint(没 ContextVar 入口),会 silent 落 Level 3 → `app.config.get_current_vault_id()` 当前全局值 = 第一个 vault。后续 audit 应 grep `LanceDBClient(` 直接实例化位置看是否都通过 endpoint 入口。

---

## Verdict-3 (review fail-closed): **CLOSED ✅**

**Evidence**:

### P0-3a: review placeholder (零字符泄漏)
`supplementary_search_service.py:307-313`:
```python
elif taint == "review":
    snippet_content = (
        f"[REDACTED: suspicious content (risk={injection_risk:.2f}); "
        f"open source_path manually to verify]"
    )
```
- placeholder 字符串完全不含 `m["snippet"]` 任何字节 ✓
- 仅暴露 `injection_risk` 数值 (0-1 浮点) — 这是元数据非原内容,可接受

### P0-3b: floor 排除 review/quarantine
`supplementary_reranker.py:206-220`:
```python
if floor_triggered:
    logger.warning(...)
    materials = [
        m for m in materials if m.get("taint") not in {"review", "quarantine"}
    ]
    if materials:
        materials[0]["filter_floor_triggered"] = True
```
- 顺序正确: floor 触发 → 排除 taint → 注入 floor_triggered marker
- `m.get("taint")` 缺字段返回 None,not in {review, quarantine} → 保留 ✓ (向后兼容旧 clean material)

### P0-3c: 多字段 taint scan
`supplementary_search_service.py:375-403`:
```python
_TAINT_PRIORITY: dict[str, int] = {"clean": 0, "review": 1, "quarantine": 2}

def _classify_material_taint(material):
    fields = (
        material.get("snippet", "") or "",
        material.get("title", "") or "",
        material.get("wikilink", "") or "",
        material.get("source_path", "") or "",
    )
    worst_taint = "clean"
    max_risk = 0.0
    for field in fields:
        if not field:
            continue
        info = _classify_snippet_taint(field)
        # worst-takes-all 取最高优先级
        if _TAINT_PRIORITY[info["taint"]] > _TAINT_PRIORITY[worst_taint]:
            worst_taint = info["taint"]
        if info["risk_score"] > max_risk:
            max_risk = info["risk_score"]
    return {"taint": worst_taint, "risk_score": max_risk}
```
- 4 字段全扫: snippet + title + wikilink + source_path ✓
- worst-takes-all 通过 `_TAINT_PRIORITY` 字典严格定义优先级 ✓
- Call site (line 158): `taint_info = _classify_material_taint(normalized)` 替代旧 `_classify_snippet_taint(snippet)` ✓

**测试**: 12 个新测试覆盖 placeholder 格式 / multi-field detection / floor 排除 + 4 个 security tests

**潜在 P2 残余面**: `raw["content"]` 字段 (LanceDB chunk 原文) 未在 `_classify_material_taint` 扫描内 — 但 raw content 不直接进 prompt(snippet 是其 derived 摘要),不构成 prompt injection 路径。

---

## Verdict-4 (__default__ fallback bucket): **PARTIAL ⚠️**

**Evidence**:
- `wikilink_graph_service.py:325-349` `_DEFAULT_VAULT_KEY = "__default__"`,`_resolve_vault_key()` 在 ContextVar None/empty/exception 时 silent 返回 `__default__`
- `lancedb_client.py:440` 在 Level 2 + 3 都失败时 silent 返回 `"default"`

**判断**: PARTIAL 而非 CLOSED — fallback bucket 仍存在 silent 串库风险(legacy caller 漏调 `set_current_subject_id` 会 share `__default__` 桶)。

**Trade-off 分析**:
- 删 fallback → fail-fast → 安全但可能 break test/CLI/standalone 用法
- 留 fallback + 加 logger.warning → 可观测但仍 silent 共享
- 留 fallback 不警告(当前) → 向后兼容但 invisible 风险

**建议**: 加 `logger.warning` once-per-process(用 set 记录已警告的 caller stack location),既保兼容又给 ops 可见性。这是 P1 follow-up,非 wave-2 必修。

---

## Verdict-5 (3 wave-1 埋雷): **3/3 CLOSED ✅**

| 雷 | 状态 | 证据 |
|---|---|---|
| chat.py:744 `rag_enrich_hook` 仍读 singleton | **CLOSED** | `chat.py:749` 现 `await _get_supp_lancedb_client(init_timeout=0.5)` (lazy + 0.5s 非阻塞) |
| supplementary_search_service.py:208 `prior_reason` 三元 dead code | **CLOSED** | `supplementary_search_service.py:222` 直接 `merged_reason = "tier2_legacy_unprefixed"`,三元 + dead branch 删除 |
| background_task_manager.py:353 cleanup_loop create_task 漏 context= | **CLOSED** | `background_task_manager.py:357-358` `cleanup_ctx = contextvars.copy_context()` + `asyncio.create_task(cleanup_loop(), context=cleanup_ctx)` |

**结论**: 3/3 真闭口,埋雷协议作为 wave-2 internal audit trail 有效。

---

## 新发现 (wave-2 引入或仍漏的)

### F1 [P2 微]: `internalApiKey === " "` 空白字符串过 length 检查
- File: `main.ts:377-378`
- Repro: settings 误填 `"  "` (空白) → buildBackendHeaders 注入 header value `"  "` → backend `require_internal_api_key` 比对失败 → 403
- 修法: `internalApiKey.trim().length > 0` 强化检查

### F2 [P1]: LanceDBClient direct instantiation 绕过 ContextVar 入口
- 当前所有 endpoint 都通过 `_get_supp_lancedb_client()` singleton,但未来如有 service 直接 `LanceDBClient()` 实例化 + 不调 `set_current_subject_id`,会 silent 落 Level 3 全局 active vault
- 修法: 在 `LanceDBClient.__init__` 加 `assert get_current_subject_id() is not None or _vault_id_override is not None or DEBUG`,生产 fail-fast
- 但 wave-2 当前所有 caller 都正确,这是预防性建议非现存 bug

### F3 [P2 仍未补]: `__default__` fallback 静默
- ChatGPT v2 已识别此点,wave-2 保留向后兼容,留 P1 follow-up
- 见 Verdict-4

---

## Top 3 remaining risks (按严重度排序)

1. **[P1] LanceDBClient ContextVar 入口契约不强制** — 当前所有 caller 都对,但缺 fail-fast 防御。如 future code 直接构造 client 不调 endpoint 入口,silent 串库回归。修法: assert 检查或 LanceDBClient.__init__ 主动 set_current_subject_id

2. **[P1] `__default__` / `"default"` fallback 仍静默** — ChatGPT v2 已识别,wave-2 trade-off 选保留向后兼容。每次 fallback 至少加 logger.warning 让 ops 看见 silent 共享发生

3. **[P2] frontend internalApiKey 空白字符串边缘** — trim() 一行修法,非阻断但美化

---

## 评估总结

| Verdict | 状态 | 行号证据 |
|---|---|---|
| V1 frontend X-CLS-Internal-Key | CLOSED ✅ | main.ts:373-381 helper + 685/865/1006/2105/2324 5 sites + 2587 settings UI |
| V2 LanceDB vault wiring | CLOSED ✅ | lancedb_client.py:384-440 4-level + line 450 use site |
| V3 review fail-closed | CLOSED ✅ | search_service.py:307 placeholder + reranker.py:206-220 floor exclude + search_service.py:375 multi-field |
| V4 __default__ fallback | PARTIAL ⚠️ | wikilink_graph_service.py:325-349 + lancedb_client.py:440 (向后兼容 trade-off) |
| V5 3 wave-1 leaks | 3/3 CLOSED ✅ | chat.py:749 + search_service.py:222 + task_manager.py:357-358 |

**Overall**: wave-2 hotfix **基本闭口** (4 CLOSED + 1 PARTIAL trade-off)。3 个新发现都是 P1/P2 增量改进,非阻断 production deploy。

建议:F1+F3 在下次 hotfix 顺手清,F2 作为 LanceDBClient 入口 hardening 列入下个 sprint。

---

*Generated 2026-05-12 by Claude autonomous loop tick 4. PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17*
