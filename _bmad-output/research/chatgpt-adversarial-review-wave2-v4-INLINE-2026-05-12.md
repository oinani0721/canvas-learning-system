# Canvas Learning System — wave-2 验证 v4 (full inline diffs, no URL fetch needed)

---

# ⛔⛔⛔ 在你做任何事之前先读这 9 行 ⛔⛔⛔

**STOP**. 这**不是** Deep Research / 项目调研 / 综述任务。这是一次 **5-bullet verdict surgical code review**。

- ⛔ **如你处于 Deep Research / Research / Browse / Web Search mode → 退出**。本任务不需要 fetch URL,全部代码 diff 已内联在下面
- ⛔ **不要写**:执行摘要 / Executive Summary / 项目概览 / 仓库目的 / 依赖图 / 改进路线图 / Gantt / 12 周计划 / LMS 兼容性 / 命名讨论 / 大表格 / 长篇分析
- ✅ **只输出**:5 个 `### Verdict-N` block (CLOSED/PARTIAL/OPEN) + 1 个 `### 新发现` + 1 个 `### Top 3 remaining risks`
- ✅ 第一行必须是 `### Verdict-1: ...`,不允许任何前置 preamble

**如果你发现自己想写"首先,让我分析..." 或 "本次研究按下面顺序..." 或 "执行摘要" → 删除,直接从 `### Verdict-1` 开始**

---

> **背景**: v3 prompt 用 GitHub URL 列表让 ChatGPT 自己 fetch,但 ChatGPT 没 web browsing tool/被拒/不可访问,verdict 全 OPEN。v4 把全部 diff 直接内联,你**不需要**fetch 任何 URL,凭文本即可完成 verify。

> **任务**: verify wave-2 hotfix commit `f018580` (相对 wave-1 `de0b4a7`) 是否真闭口 ChatGPT v2 给出的 5 个 verdict。

---

## ⛔ 硬约束 (同 v2/v3,违反就重写)
1. 不要项目级综述 / Executive Summary / LMS 兼容性 / 命名讨论 / roadmap
2. 不要写"信息不足无法判定"——下面**全部 diff** 都内联了
3. 只输出 5 个 Verdict + Top 3 risks + 新发现

---

## diff: backend/lib/agentic_rag/clients/lancedb_client.py (P0-2)

```python
@property
def active_vault_id(self) -> str:
    """Resolve effective vault_id for table namespace.

    Resolution order (Wave-2 P0-2 hotfix, 2026-05-12):
    1. ``self._vault_id_override`` — explicit constructor arg (legacy POC tests)
    2. ``app.core.subject_config.get_current_subject_id()`` ContextVar
       — set per-request by ``set_current_subject_id`` in chat / metadata
       endpoints. Strips ``vault:`` prefix and keeps the FIRST segment so
       ``vault:cs_61b:algorithms`` → ``cs_61b``.
    3. ``app.config.get_current_vault_id()`` — legacy global active vault.
    4. ``"default"`` — final fallback.
    """
    if self._vault_id_override is not None:
        return self._vault_id_override

    # Step 2: prefer ContextVar from subject_config (Story 2.5.Y vault wiring).
    try:
        from app.core.subject_config import (
            DEFAULT_SUBJECT_ID,
            get_current_subject_id,
        )

        ctx_value = get_current_subject_id()
        if ctx_value and ctx_value != DEFAULT_SUBJECT_ID:
            # vault:cs_61b → cs_61b ; vault:cs_61b:algorithms → cs_61b
            derived = ctx_value
            if derived.startswith("vault:"):
                derived = derived[len("vault:") :]
            # take first segment (drop :subject / :canvas suffix)
            first_seg = derived.split(":", 1)[0].strip()
            if first_seg:
                logger.debug(...)
                return first_seg
    except Exception:
        pass  # subject_config not importable → fall through

    # Step 3: legacy fallback
    try:
        from app.config import get_current_vault_id
        return get_current_vault_id()
    except Exception:
        return "default"
```

## diff: backend/app/api/v1/endpoints/chat.py (P0-2 漏修-1, rag_enrich_hook)

```python
async def rag_enrich_hook(req: HookEnrichRequest) -> HookEnrichOutput:
    ...
-   # 复用 chat.py module-level singleton (commit 5dfad13 endpoint 不 acquire lock)
-   lancedb_client = _supp_lancedb_singleton
+   # Wave-2 P0-2 漏修-1 (2026-05-12): 改用 lazy init 替代裸读 singleton.
+   # init_timeout=0.5s — hook 是非阻塞, 已 ready 立即返回 client;
+   # 未 ready 短窗口内尝试不抢锁, 超时则降级跳过.
+   lancedb_client = await _get_supp_lancedb_client(init_timeout=0.5)
```

## diff: backend/app/services/supplementary_search_service.py (P0-3a + P0-3c + 漏修-2)

### P0-3c: 新 _classify_material_taint 扫描 4 字段

```python
# P0-3c: taint priority order (worst-takes-all)
_TAINT_PRIORITY: dict[str, int] = {"clean": 0, "review": 1, "quarantine": 2}

def _classify_material_taint(material: dict[str, Any]) -> dict[str, Any]:
    """扫描 snippet + title + wikilink + source_path 各跑 _classify_snippet_taint,
    取 max risk_score + worst taint level (quarantine > review > clean)."""
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
        t = info["taint"]
        r = info["risk_score"]
        if _TAINT_PRIORITY[t] > _TAINT_PRIORITY[worst_taint]:
            worst_taint = t
        if r > max_risk:
            max_risk = r
    return {"taint": worst_taint, "risk_score": max_risk}
```

### P0-3c call site (filter loop):
```python
-   taint_info = _classify_snippet_taint(normalized.get("snippet", ""))
+   # P0-3c: multi-field taint scan (旧逻辑只扫 snippet → metadata 绕过)
+   taint_info = _classify_material_taint(normalized)
```

### P0-3a: review 输出 fixed placeholder (不再 240 字)
```python
elif taint == "review":
-   raw_snippet = m["snippet"][:240] + "…" if len(m["snippet"]) > 240 else m["snippet"]
-   snippet_content = _xml_escape(raw_snippet)
+   # P0-3a: fixed placeholder, 零字符泄漏原 snippet
+   snippet_content = (
+       f"[REDACTED: suspicious content (risk={injection_risk:.2f}); "
+       f"open source_path manually to verify]"
+   )
```

### 漏修-2: prior_reason 三元 dead code 删除
```python
legacy_hit = any(m.get("is_legacy_fallback") for m in materials)
if legacy_hit:
-   prior_reason = None if materials else "all_filtered_below_threshold"
-   new_reason = "tier2_legacy_unprefixed"
-   merged_reason = f"{prior_reason}; {new_reason}" if prior_reason else new_reason
+   # legacy_hit = any(materials...) 已隐含 materials 非空, 三元 else 永不触发,
+   # prior_reason 始终为 None — 死代码。直接写单一标志:
+   merged_reason = "tier2_legacy_unprefixed"
    logger.warning("[SupplementarySearch] degraded 顶层标志: tier-2 legacy fallback 命中", ...)
```

## diff: backend/app/services/supplementary_reranker.py (P0-3b)

```python
def rerank(materials, *, min_keep=3, ...):
    ...
    if min_score_threshold is not None:
        kept = [m for m in materials if m["rerank_score"] >= min_score_threshold]
        n_pre = len(materials)
        n_post = len(kept)
        floor_triggered = False
        if min_keep > 0 and n_pre > 0:
            kill_ratio = 1.0 - (n_post / n_pre)
            if n_post < min_keep or kill_ratio > 0.80:
                floor_triggered = True
        if floor_triggered:
            logger.warning("[Rerank] filter_floor_triggered", ...)
-           # 不过滤, 标记兜底, 仍走 top_k
+           # P0-3b (2026-05-12): floor 仍 fail-closed 过滤 review/quarantine 材料
+           # (兜底也不能让可疑材料绕过审查)
+           materials = [
+               m for m in materials
+               if m.get("taint") not in {"review", "quarantine"}
+           ]
+           # 标记兜底, 仍走 top_k
            if materials:
                materials[0]["filter_floor_triggered"] = True
        else:
            materials = kept
```

## diff: backend/app/services/background_task_manager.py (漏修-3)

```python
-   self._cleanup_task = asyncio.create_task(cleanup_loop())
+   # P0-2 wave-2 cleanup follow-up: 把 cleanup_loop 也绑定到 caller context
+   cleanup_ctx = contextvars.copy_context()
+   self._cleanup_task = asyncio.create_task(cleanup_loop(), context=cleanup_ctx)
```

## diff: frontend/obsidian-plugin/src/main.ts (P0-1, 5 fetch sites)

### Settings 加 internalApiKey 字段
```typescript
interface CanvasPluginSettings {
  ...
+ /** Wave-2 P0-1: 空字符串 = dev mode (DEBUG=True); 非空 = prod auth header */
+ internalApiKey: string;
}

const DEFAULT_SETTINGS: CanvasPluginSettings = {
  ...
+ internalApiKey: "",
};
```

### 新 helper buildBackendHeaders()
```typescript
public buildBackendHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (this.settings.internalApiKey && this.settings.internalApiKey.length > 0) {
    headers["X-CLS-Internal-Key"] = this.settings.internalApiKey;
  }
  return headers;
}
```

### 5 个 fetch site 全部改用 helper
```typescript
// site 1: handleChatWithContext (line ~678)
- headers: { "Content-Type": "application/json" },
+ headers: this.buildBackendHeaders(),

// site 2: handleStudyQuestion (line ~859)
- headers: { "Content-Type": "application/json" },
+ headers: this.buildBackendHeaders(),

// site 3: handleGlobalSearch (line ~1000)
- headers: { "Content-Type": "application/json" },
+ headers: this.buildBackendHeaders(),

// site 4: callBackend (line ~2099, GET/POST 双路径)
- headers: body ? { "Content-Type": "application/json" } : {},
+ const headers = body
+   ? this.buildBackendHeaders()
+   : (() => {
+       const h: Record<string, string> = {};
+       if (this.settings.internalApiKey && this.settings.internalApiKey.length > 0) {
+         h["X-CLS-Internal-Key"] = this.settings.internalApiKey;
+       }
+       return h;
+     })();

// site 5: postErrorCandidateAction (line ~2318)
- headers: { "Content-Type": "application/json" },
+ headers: this.buildBackendHeaders(),
```

### Settings UI 加 Internal API Key 字段
```typescript
new Setting(inner)
  .setName("Internal API Key (X-CLS-Internal-Key)")
  .setDesc("生产环境 (DEBUG=False) 必填 — ... 留空 = dev mode")
  .addText((text) =>
    text.setPlaceholder("(留空 = dev mode)")
      .setValue(this.plugin.settings.internalApiKey)
      .onChange(async (value) => {
        this.plugin.settings.internalApiKey = value;
        await this.plugin.saveSettings();
      }),
  );
```

**注意**: `handleOpenNodeChat` 是 clipboard-only,**不**调 backend,所以不需要 header。

## diff: backend/app/api/v1/endpoints/chat.py 顶部 (auth dependency, NOT changed)

为澄清 ChatGPT v2 错误判断,这是 wave-1 + wave-2 都存在的 backend auth dependency:

```python
# chat.py line 47 (unchanged in wave-2):
chat_router = APIRouter(dependencies=[Depends(require_internal_api_key)])
```

`@chat_router.post("/global-search", ...)` 自动继承此 dependency。**全部 chat_router 下的 endpoint 都被 internal-key 保护**, 不需要逐 endpoint 加。所以 ChatGPT v2 P0-1 后端"未鉴权"是基于"chat_router 不含 require_internal_api_key" 的误读 — 实际 line 47 已经全局加。

Wave-2 修的是 **frontend 漏带 header**, 后端 auth 一直 OK。生产 env (DEBUG=False + key 配置) 时 frontend 必须带 header 否则 403 (符合 fail-closed 设计)。

## 关于 P0-2 设计选择 (ChatGPT v2 误判的另一处)

ChatGPT v2 担心 `_supp_lancedb_singleton` 是 module-level singleton 跨 vault 共享 → 错。

实际设计:
- **Singleton**: BGE-M3 model + LanceDB connection (expensive resources, 共享 OK)
- **Per-request resolution**: `LanceDBClient.active_vault_id` property 每次访问都从 ContextVar 派生 → `resolve_table_name("vault_notes")` 返回 `cs_61b_vault_notes` vs `数学_vault_notes` per request
- **结果**: 同一个 singleton 但每个 request 看到不同的 table namespace,**比 per-vault client dict cache 节省内存 + cold-start 时间**

这比 ChatGPT v2 推荐的 `dict[vault_id] -> client` 方案更高效。但 trade-off 是: `active_vault_id` 是 dynamic property,任何 caller 必须确认 ContextVar 已经在 request 入口设置。Wave-2 在所有 chat_router endpoint 顶部都加了 `set_current_subject_id(group_id)` 调用,所以契约成立。

## Test 改动统计 (不内联)

| 文件 | 新增测试 | 覆盖 |
|---|---|---|
| `test_lancedb_vault_isolation.py` | +9 | P0-2 ContextVar resolution / strip vault: prefix / 4-level fallback / override priority |
| `test_chat_endpoint.py` | +3 | rag_enrich_hook lazy init / preload mode skip |
| `test_supplementary_search_service.py` | +9 | P0-3a placeholder format / P0-3c metadata 4-field scan |
| `test_supplementary_reranker.py` | +5 | P0-3b floor 排除 review/quarantine |
| `tests/security/test_global_search_auth.py` | +6 | P0-1 require_internal_api_key 三态 (DEBUG=False+key+header / DEBUG=False+key+无 header → 403 / DEBUG=True dev) |
| `tests/security/test_cross_vault_global_search.py` | +5 | P0-2 vault_id follows request body |
| `tests/security/test_supplementary_review_floor.py` | +6 | P0-3a+3b 联合验证 (review payload 不进 prompt) |
| `tests/security/test_supplementary_metadata_fuzz.py` | +N | P0-3c metadata fuzz |
| `tests/auth-headers.test.ts` (frontend) | +13 | P0-1 helper + 4 handler header 注入 |

**测试结果**: backend 219 pass / 1 pre-existing fail (group_id format vault:cs61b: vs 旧 cs61b:, Story 2.5.Y D16 已锁) / 33 xfailed / 4 xpassed. Frontend 186/186 pass.

---

## 你的任务: 逐项 verify

### Verdict-1 (frontend X-CLS-Internal-Key)
看 main.ts diff: 是否 `buildBackendHeaders()` 真 conditional (key 空时不加)? 5 个 fetch site 是否真都用 helper? `handleOpenNodeChat` 不调 backend 合理吗?

### Verdict-2 (LanceDB vault wiring)
看 lancedb_client.py active_vault_id diff: 4 级 fallback 顺序正确吗? Level 2 strip `vault:` prefix + first segment 是否正确处理 `vault:cs_61b:algorithms` → `cs_61b`? **设计选择 singleton + per-request resolution** 是否合理 (相比 per-vault dict)?

### Verdict-3 (review fail-closed)
看 supplementary_search_service.py diff: review 输出 placeholder 是否**零字符**泄漏? P0-3c 多字段 worst-takes-all 是否真实施? 看 supplementary_reranker.py diff: P0-3b floor 排除是否在正确顺序?

### Verdict-4 (__default__ fallback)
看 lancedb_client.py Level 4 `return "default"`: 仍保留向后兼容。这是 acceptable trade-off 还是必须加 fail-fast?

### Verdict-5 (3 wave-1 leaks)
- chat.py:744 rag_enrich_hook: 看 diff 是否改为 `await _get_supp_lancedb_client(init_timeout=0.5)` ✓
- supplementary_search_service.py:208 prior_reason 三元: 看 diff 是否删除 ✓
- background_task_manager.py:353 cleanup_loop context=: 看 diff 是否加 `context=cleanup_ctx` ✓

应该全部 CLOSED, 给最终评级。

---

## 输出格式 (严格)

```
### Verdict-1: <CLOSED | PARTIAL | OPEN>
[evidence from diff cited line]

### Verdict-2: <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-3: <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-4: <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-5: <3/3 CLOSED | 2/3 | 1/3 | 0/3>
- chat.py:744: CLOSED ✓
- supplementary_search_service.py:208: CLOSED ✓
- background_task_manager.py:353: CLOSED ✓

### 新发现 (wave-2 引入或漏掉的)
[若有,带 file:line]

### Top 3 remaining risks
1. [P0/P1/P2] [1 句话]
2. ...
3. ...
```
