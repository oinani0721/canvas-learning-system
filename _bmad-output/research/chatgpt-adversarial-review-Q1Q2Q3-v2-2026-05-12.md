# Canvas Learning System — ChatGPT Q1+Q2+Q3 hotfix 审查 v2 (强约束 prompt)

> **用法**: 复制本文件**全文**到 ChatGPT (推荐 GPT-5 thinking / o1 / 模型选最强 reasoning),作为唯一输入。
> **目标**: 拿到 Q1/Q2/Q3 each 一个 **PASS / CONDITIONAL PASS / FAIL** verdict + remaining risk + suggested follow-ups。

---

## 📍 必读资源 (你**必须**先 fetch 完所有 URL 再开始 review)

### 仓库定位
- **GitHub Repo**: https://github.com/oinani0721/canvas-learning-system
- **审查目标分支**: `worktree-feature-obsidian-hybrid-dev` (不是 main!)
- **审查目标 commit**: `de0b4a7` (Q1+Q2+Q3 P0 hotfix,2026-05-12)
- **baseline commit** (修复前状态,用于对比 diff): `549d5f0` (T3+T5 with original 5 P0s)
- **commit diff 直接看这里**: https://github.com/oinani0721/canvas-learning-system/commit/de0b4a7

### Q1 (RAG 精度 5 P0 + chunk filter) — 6 file
- 实现:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/services/supplementary_reranker.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/services/supplementary_search_service.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/api/v1/endpoints/chat.py
- 测试:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_supplementary_reranker.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_supplementary_search_service.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_chat_endpoint.py

### Q2 (Multi-vault 隔离 2 P0) — 4 file
- 实现:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/services/wikilink_graph_service.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/services/background_task_manager.py
- 测试:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_wikilink_graph_service.py
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_background_task_manager.py

### Q3 (Skill 全局搜索 plugin 入口 + multi-seed BFS) — 6 file
- Backend 实现:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/app/services/wikilink_context_service.py
  - (chat.py 已在 Q1 列出)
- Backend 测试:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/backend/tests/unit/test_wikilink_context_service.py
- Frontend 实现:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/frontend/obsidian-plugin/src/main.ts
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/frontend/obsidian-plugin/src/global-search.ts
- Frontend 测试:
  - https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/frontend/obsidian-plugin/tests/global-search.test.ts

### Story spec + 3 UAT 验收单 (DoD-3 双段铁律评估,Cross-cutting 部分要用)
- Story spec (整 story 的 7 AC + 7 Tasks): https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/_bmad-output/implementation-artifacts/epic-2/2-2-and-2-9-merged-rerank-evidence.md
- UAT Q1: https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/_bmad-output/%E9%AA%8C%E6%94%B6%E5%8D%95/Story-2.2%2B2.9-Q1-rerank-hotfix-2026-05-12.md
- UAT Q2: https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/_bmad-output/%E9%AA%8C%E6%94%B6%E5%8D%95/Story-2.5.Y-Q2-multi-vault-hardening-2026-05-12.md
- UAT Q3: https://github.com/oinani0721/canvas-learning-system/blob/de0b4a7/_bmad-output/%E9%AA%8C%E6%94%B6%E5%8D%95/Story-2.2%2B2.9-Q3-global-search-2026-05-12.md

### 如果你的工具无法 fetch GitHub blob URL
- 改 fetch raw 形式:把 `github.com/<user>/<repo>/blob/<sha>/<path>` 换成 `raw.githubusercontent.com/<user>/<repo>/<sha>/<path>`
- 例: https://raw.githubusercontent.com/oinani0721/canvas-learning-system/de0b4a7/backend/app/services/supplementary_reranker.py
- 如果还不行,本 prompt **下半部分内联了所有关键代码 snippet** (~150 行) 作为 fallback 证据

### ⛔ 不要读这些 (会污染你的判断)
- main 分支(因为 audit 目标在 worktree 分支,不在 main)
- 之前 commits 的 README / sprint-status / C4 文档 (那是项目级综述,你这次不做综述)
- 任何 `_archive/` 或 `_decisions/` 历史目录
- `canvas-progress-tracker/` (旧路径已废弃)

---

## ⚠️ 这是一次 SURGICAL CODE REVIEW,不是 project audit

我已经在前一次 Deep Research 里得到过项目级宏观分析(命名/LMS 兼容性/文档漂移/测试债)。这些**不是**本次任务。

本次任务**只**评估:在 worktree 分支 `worktree-feature-obsidian-hybrid-dev` 的 commit `de0b4a7` 中,3 组 P0 hotfix 是否真实落地、是否还有暗病。

### ⛔ 禁止行为 (违反任一 = 输出作废)

1. 不要分析"Canvas Learning System"项目名是否与 Instructure Canvas LMS 混淆
2. 不要建议 LTI / SIS / OAuth2 / Gradebook / Accessibility 兼容性补全
3. 不要讨论项目定位 / 重新命名 / Bus factor / 文档漂移 / 版本号不一致
4. 不要推 roadmap / 维护负担 / 产品分叉
5. 不要写 "执行摘要" / "Executive Summary" / "项目概览" / "总体判断"

### ✅ 仅允许 3 种输出

- Q1 verdict + evidence
- Q2 verdict + evidence
- Q3 verdict + evidence
- Cross-cutting verdict (DD-12 scope / DD-03 no-mock / DD-14 trace / DoD-3)
- Top 3 remaining risks

---

## 上下文 (压缩到 50 字)

Canvas Learning System = Obsidian Canvas 上的 AI 学习工作台,**不是** Canvas LMS。FastAPI + LanceDB + Neo4j + Obsidian plugin (TypeScript)。本次评估 commit `de0b4a7` 的 22 文件 / 2735 insertions。

---

## Q1 — RAG 精度 5 P0 hotfix + chunk filter

### 用户痛点
之前的 rerank engine (commit `549d5f0`) 有 5 个 P0 让它 silently no-op。本次 hotfix 全修。

### 修复证据 (逐 P0 给代码,你不必爬 GitHub,只读这里)

#### P0-A: TYPE_WEIGHTS 扩过渡映射 (修 indexer 错位)

File: `backend/app/services/supplementary_reranker.py:44-62`

```python
TYPE_WEIGHTS: dict[str, float] = {
    # PRD §4.1.1 frozen 2026-05-11 (forward compat for indexer 升级)
    "lecture_notes": 1.0,
    "discussion": 0.9,
    "exam_review": 0.85,
    "wiki_concepts": 0.8,
    "chat_session": 0.7,
    "raw_notes": 0.6,
    # P0-A 过渡 (indexer 升级到 PRD 6 档前的实际命中映射, 2026-05-12 hotfix):
    "video_transcript": 0.9,  # 视频 transcript → 近 discussion 价值
    "note": 0.7,              # 普通 vault 笔记 → 近 chat_session 中档
    "image_ocr": 0.6,         # OCR 出来的图片文字 → 同 raw_notes 低档
}
DEFAULT_TYPE_WEIGHT: float = 0.5
```

LanceDB indexer (`backend/app/services/lancedb_client.py:1444 + 1644`) 实际写入 `source_type ∈ {note, video_transcript, image_ocr}`。

#### P0-B: rerank() min_keep filter floor (修 0.42 阈值 silently 全删)

File: `backend/app/services/supplementary_reranker.py:184-217`

```python
# P0-B (2026-05-12 hotfix): 过滤 floor 兜底.
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
        logger.warning(
            "[Rerank] filter_floor_triggered",
            pre=n_pre, post=n_post,
            threshold=round(min_score_threshold, 3),
            min_keep=min_keep,
        )
        if materials:
            materials[0]["filter_floor_triggered"] = True
    else:
        materials = kept

if top_k is not None and top_k >= 0:
    return materials[:top_k]
return materials
```

`min_keep` 参数 default = 3。

#### P0-C: chat.py 改 lazy await

File: `backend/app/api/v1/endpoints/chat.py:333`

```python
# Before: lancedb_client = _supp_lancedb_singleton  (直读 race condition)
# After:
lancedb_client = await _get_supp_lancedb_client(init_timeout=5.0)
```

⚠️ **注意**: chat.py:744 在 `rag_enrich_hook` endpoint 内**仍然**直读 `_supp_lancedb_singleton`。是否需要也改?

#### P0-D: tier-2 legacy fallback degraded 顶层传播

File: `backend/app/services/supplementary_search_service.py:205-225`

```python
# P0-D (2026-05-12 hotfix): tier-2 legacy fallback 命中时, 行级
# is_legacy_fallback=True 但顶层 dict 仍 degraded=False, 下游观测拿不到旗帜.
legacy_hit = any(m.get("is_legacy_fallback") for m in materials)
if legacy_hit:
    prior_reason = None if materials else "all_filtered_below_threshold"
    new_reason = "tier2_legacy_unprefixed"
    merged_reason = f"{prior_reason}; {new_reason}" if prior_reason else new_reason
    logger.warning(
        "[SupplementarySearch] degraded 顶层标志: tier-2 legacy fallback 命中",
        materials=len(materials),
        query=query[:60],
    )
    return {
        "materials": materials,
        "degraded": True,
        "reason": merged_reason,
    }
```

⚠️ **注意**: `prior_reason = None if materials else "all_filtered_below_threshold"` — 这个三元在 `materials` 非空时 prior_reason=None,如有 tier-2 + materials 非空场景,prior reason 信息丢失。是否 bug?

#### P0-E: prompt injection guard fail-closed on RuntimeError

File: `backend/app/services/supplementary_search_service.py:325-345`

```python
try:
    from app.middleware.prompt_injection_guard import check_input
    result = check_input(snippet)
    if result.is_blocked:
        return {"taint": "quarantine", "risk_score": result.risk_score}
    if result.risk_score >= 0.45:
        return {"taint": "review", "risk_score": result.risk_score}
    return {"taint": "clean", "risk_score": result.risk_score}
except ImportError as e:
    # 模块未安装/开发环境 — 标志 clean (与 PhaseA0.5-P 原行为一致)
    logger.debug(...)
    return {"taint": "clean", "risk_score": 0.0}
except RuntimeError as e:
    # P0-E: fail-closed (不能因 guard 故障绕过)
    logger.warning(...)
    return {"taint": "review", "risk_score": 0.5}
```

#### Bonus: chunk-link-list filter

File: `backend/app/services/supplementary_search_service.py:423-443`

```python
def _is_link_list_chunk(content: str, threshold: float = 0.6) -> bool:
    """检测内容是否以 wikilink 列表为主 (MOC/index chunk 标志).

    算 wikilink_count / max(non_link_token_count, 1) > threshold 即标 link-list.
    """
    if not content:
        return False
    wikilink_count = len(_WIKILINK_RE.findall(content))
    if wikilink_count == 0:
        return False
    stripped = _WIKILINK_RE.sub(" ", content)
    non_link_tokens = [tok for tok in stripped.split() if tok.strip()]
    ratio = wikilink_count / max(len(non_link_tokens), 1)
    return ratio > threshold
```

⚠️ **注意**: 默认 threshold=0.6,但 docstring 写 `"[[A]] [[B]] [[C]]" → 3/1 = 3.0`。是否真的 vault 里大量 MOC 都 wikilink_count / non_link_tokens > 0.6? 阈值有调优过吗?

### Q1 测试证据

```
$ cd backend && .venv/bin/pytest tests/unit/test_supplementary_reranker.py tests/unit/test_supplementary_search_service.py tests/unit/test_chat_endpoint.py -q
104 passed (新增 27, baseline 77, 零回归)

新测试 class:
- TestTypeWeightsIndexerTransition (5 tests)
- TestFilterFloor (5 tests)
- TestTopLevelDegradedFromLegacyFallback (2 tests)
- TestClassifySnippetTaintFailClosed (2 tests)
- TestIsLinkListChunk (6 tests)
- TestFormatSupplementaryXmlLinkListAttr (2 tests)
- test_enrich_context_answer_mode_uses_lazy_init_path
- test_enrich_context_preload_mode_skips_supplementary
```

### Q1 需要你回答

1. P0-A 解法 (扩 TYPE_WEIGHTS 加 3 indexer 实际 keys) 是 forward-compatible 修法,还是 anti-pattern (应该让 indexer 改写 PRD 概念词)?
2. P0-B `kill_ratio > 0.80` 阈值是否合理? `min_keep=3` 是否足够? 用户原话"把有用的都给我"是否被尊重?
3. P0-C **chat.py:744 仍直读 singleton** — 是否漏修?
4. P0-D `prior_reason = None if materials else "all_filtered..."` 三元逻辑是否丢失非空 materials 场景的 prior reason?
5. P0-E `RuntimeError → review` vs `ImportError → clean` 区分是否合理? 是否漏掉其他 exception (BaseException / OSError / asyncio.CancelledError)?
6. Bonus `_is_link_list_chunk` threshold=0.6 是否有 false positive 风险? 比如代码块里的 markdown link 数量?

**Q1 输出格式 (严格):**

```
### Q1 verdict: <PASS | CONDITIONAL PASS | FAIL>

**已修真问题**:
- [bullet 1]
- [bullet 2]
...

**遗留风险 / 未验证 claim**:
- [bullet + file:line evidence]
...

**Suggested follow-ups (按严重度排序)**:
1. P0/P1/P2 + 1 句话
2. ...
```

---

## Q2 — Multi-vault 隔离 2 P0 hotfix

### 用户痛点
Story 2.5.Y claim 10/10 done,但前次 audit 发现 2 个 P0 仍漏:WikilinkGraphService 单例不分 vault + BackgroundTaskManager 丢 ContextVar。

### 修复证据

#### P0-1: WikilinkGraphService 单例 → per-vault dict

File: `backend/app/services/wikilink_graph_service.py:325-365`

```python
_wikilink_graph_services: dict[str, WikilinkGraphService] = {}
_DEFAULT_VAULT_KEY = "__default__"


def _resolve_vault_key() -> str:
    """从 ContextVar 派生 sanitized vault key (P0-1 修复)."""
    try:
        from app.core.subject_config import (
            get_current_subject_id,
            sanitize_subject_name,
        )

        raw = get_current_subject_id()
        if not raw or not isinstance(raw, str) or not raw.strip():
            return _DEFAULT_VAULT_KEY
        sanitized = sanitize_subject_name(raw)
        return sanitized or _DEFAULT_VAULT_KEY
    except Exception:
        return _DEFAULT_VAULT_KEY


def get_wikilink_graph_service() -> WikilinkGraphService:
    """Per-vault WikilinkGraphService 获取入口 (P0-1)."""
    key = _resolve_vault_key()
    svc = _wikilink_graph_services.get(key)
    if svc is None:
        svc = WikilinkGraphService()
        _wikilink_graph_services[key] = svc
    return svc
```

新增 helpers: `clear_cache_for_vault(vault_key) / clear_all_caches() / get_cache_stats()`。

#### P0-2: BackgroundTaskManager copy_context

File: `backend/app/services/background_task_manager.py:202-208`

```python
# P0-2 multi-vault hotfix (2026-05-11):
# 旧实现 asyncio.create_task(coro) 不继承 ContextVar,导致 background task
# 内 get_current_subject_id() 返回默认值 → 跨 vault 串库泄漏.
# 修复:snapshot 当前 contextvars.Context,Python 3.11+ asyncio.create_task
# 原生支持 context= 参数,把 wrapped_task 绑定到 snapshot 上下文.
ctx = contextvars.copy_context()
future = asyncio.create_task(wrapped_task(), context=ctx)
self._running_futures[task_id] = future
```

⚠️ **注意**: 同文件 line 353 仍有 `self._cleanup_task = asyncio.create_task(cleanup_loop())` 未加 context= 参数。`cleanup_loop` 是否需要 vault-aware?

### Q2 测试证据

```
$ cd backend && .venv/bin/pytest tests/unit/test_wikilink_graph_service.py tests/unit/test_background_task_manager.py -q
96 passed (新增 6, baseline 90, 零回归)

新测试 class / functions:
- TestMultiVaultIsolation:
  - test_per_vault_isolation
  - test_no_contextvar_uses_default_key
  - test_clear_cache_for_vault
- test_create_task_inherits_contextvar
- test_create_task_with_different_contextvars
- test_default_contextvar_propagates
```

### Q2 需要你回答

1. `_resolve_vault_key()` 的 `except Exception: return _DEFAULT_VAULT_KEY` — 太宽? 是否应该只 catch ImportError + AttributeError? 全 except 会吞掉真正的 subject_config bug
2. `_wikilink_graph_services: dict[str, ...]` 无 eviction / size limit — 长期跑 1000 vault 会内存爆,需要 LRU 吗?
3. `_DEFAULT_VAULT_KEY = "__default__"` — 多 vault 但 ContextVar 漏设的 caller 会都掉到 default 桶,跨 vault 串库 fallback 风险。是否应该 raise 而不是 silent fall through?
4. **chat.py:744 rag_enrich_hook** 是 fire-and-forget? 是否经过 BackgroundTaskManager? 如果是裸 `asyncio.create_task`,P0-2 修法没覆盖
5. cleanup_loop (line 353) 是否需要 context= 参数? cleanup 应该 vault-agnostic 还是 vault-aware?
6. 是否有 OTHER service-level singletons 仍跨 vault 共享 (e.g. mastery_store / agent_service / react_agent)?

**Q2 输出格式同 Q1。**

---

## Q3 — Skill 全局搜索 plugin 入口 + multi-seed BFS

### 用户痛点
之前 3 个 plugin hotkey (`Cmd+Shift+E`, `Cmd+P deep`, `Cmd+Shift+C`) 都强守门 `isNodePath`,Dashboard / 空白视图无法触发全局搜索。"我都不知道该开哪个节点" 的场景没有入口。

### 修复证据

#### 新 backend endpoint POST /api/v1/chat/global-search

File: `backend/app/api/v1/endpoints/chat.py:842-1020`

```python
class GlobalSearchRequest(BaseModel):
    user_question: str = Field(..., min_length=1, max_length=2000)
    vault_id: str = Field(..., min_length=1)
    subject_id: str | None = None
    top_k_max: int = Field(default=30, ge=5, le=50)
    hard_cap: int = Field(default=20, ge=3, le=30)


class GlobalSearchResponse(BaseModel):
    enriched_context: str
    supplementary_count: int
    supplementary_degraded: bool
    supplementary_reason: str | None
    elapsed_ms: float


@chat_router.post("/global-search", response_model=GlobalSearchResponse, ...)
async def global_search(req: GlobalSearchRequest) -> GlobalSearchResponse:
    # Multi-vault 隔离 (与 enrich-context 同款契约)
    sanitized_vault_id = sanitize_vault_id(req.vault_id)
    derived_group_id = build_vault_group_id(
        sanitized_vault_id,
        subject_id=req.subject_id,
        canvas_path=None,  # 全局搜索无 canvas 上下文
    )
    set_current_subject_id(derived_group_id)

    try:
        # 复用 P0-C lazy init
        lancedb_client = await _get_supp_lancedb_client(init_timeout=5.0)

        supp_result = await search_supplementary(
            query=req.user_question,
            lancedb_client=lancedb_client,
            top_k_max=req.top_k_max,
            min_relevance=0.30,
            elbow_drop_threshold=0.05,
            hard_cap=req.hard_cap,
        )

        from app.services.supplementary_reranker import (
            get_filter_threshold, rerank,
        )

        supp_result["materials"] = rerank(
            supp_result.get("materials", []),
            query=req.user_question,
            median_degree=0.0,  # 全局搜索无 graph context
            min_score_threshold=get_filter_threshold(),
            top_k=5,
        )
        # ... format_supplementary_xml + manifest 构造 ...
```

#### Multi-seed BFS

File: `backend/app/services/wikilink_context_service.py:376-615`

```python
async def enrich_from_wikilink_graph(
    node_path: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    graph_service: WikilinkGraphService | None = None,
    additional_seeds: list[str] | None = None,
) -> EnrichmentResult:
    ...
    if additional_seeds:
        all_seed_slugs = {target_slug}
        for s in additional_seeds:
            all_seed_slugs.add(_normalize_target_slug(s))

        for seed in additional_seeds:
            if not seed or not seed.strip():
                continue
            try:
                # 递归调用 (additional_seeds=None 防无限)
                sub_result = await enrich_from_wikilink_graph(
                    node_path=seed,
                    max_hops=max_hops,
                    timeout_ms=timeout_ms,
                    graph_service=graph_service,
                    additional_seeds=None,
                )
            except Exception as e:
                logger.warning(
                    "wikilink_context.additional_seed_failed",
                    seed=seed, error=str(e)[:120],
                )
                continue
            if sub_result.degraded:
                continue
            for sub_n in sub_result.neighbors:
                if sub_n.slug in seen_slugs:
                    continue
                if (sub_n.slug in all_seed_slugs
                    and sub_n.slug != _normalize_target_slug(seed)):
                    # 跨 seed 自循环跳过
                    continue
                seen_slugs.add(sub_n.slug)
                contexts.append(sub_n)
            # merge sub_result.trace.included 时标 seed_origin=seed
            if sub_result.trace is not None:
                for sub_item in sub_result.trace.included:
                    trace_items.append(
                        TraceItem(
                            ...,
                            seed_origin=seed,
                        )
                    )
```

TraceItem 加 `seed_origin: str | None = None` 字段。

#### Frontend plugin

File: `frontend/obsidian-plugin/src/main.ts:531-533` 命令注册

```typescript
{
    id: "canvas:global-search",
    name: "全局搜索教学笔记 (Global Search,任意视图可触发)",
    callback: () => this.handleGlobalSearch(),
}
```

无 `isNodePath` 守门,任意视图可触发。

File: `frontend/obsidian-plugin/src/global-search.ts` (新文件) — pure helpers:
- `buildGlobalSearchPayload`
- `classifyFetchFailure`
- `buildSuccessNoticeMessage`
- `buildFailureNoticeMessage`
- `GLOBAL_SEARCH_TIMEOUT_MS = 8000`

File: `frontend/obsidian-plugin/src/main.ts:935-1027` `handleGlobalSearch()`:
- UserQuestionModal → 空 question silently abort
- POST /api/v1/chat/global-search with AbortController 8s timeout
- 失败分类: backend_timeout (AbortError) / backend_unreachable (TypeError) / backend_error / non_json_response
- 成功: 剪贴板 + 切 Claudian + Notice

### Q3 测试证据

```
backend: 61 pass (含 6 新增: test_enrich_multi_seed_dedup / test_enrich_additional_seeds_none_preserves_behavior / test_enrich_multi_seed_skips_degraded_sub_seed / test_global_search_endpoint_returns_xml / test_global_search_endpoint_rejects_empty_question / test_global_search_endpoint_degrades_on_lancedb_none)

frontend: 173 pass (含 19 新增 across 5 describe blocks)
- register_global_search_command_no_node_guard (2 tests)
- handle_global_search_empty_question_no_fetch (2 tests)
- handle_global_search_success_writes_clipboard (5 tests)
- handle_global_search_backend_unreachable_degrades (6 tests)
- GLOBAL_SEARCH_TIMEOUT_MS (2 tests)
```

### Q3 需要你回答

1. multi-seed BFS **递归实现** (函数自己调自己 with `additional_seeds=None`) — 是否有 stack overflow / 无限递归风险? 如 additional_seeds 列表巨长 (50+) 是否会爆? timeout/性能保护够吗?
2. **跨 seed 自循环过滤逻辑**:
   ```python
   if sub_n.slug in all_seed_slugs and sub_n.slug != _normalize_target_slug(seed):
       continue
   ```
   是否会漏掉合法邻居? 比如 seed=[X, Y],Z 是 X 的邻居也是 Y 的邻居,Z 被保留;但如果 Y 是 X 的真实 1-hop 邻居,会被跳过。这是 feature 还是 bug?
3. global-search endpoint **不带 query expansion / intent classification** — 直接把 `user_question` 当 LanceDB query 用,是否够? 还是应该先做 query intent → 多 sub-query 拆解 (像 Khoj / Smart Connections 做的)?
4. global-search **没有 wikilink graph 邻居装载** — 只走 supplementary。如果用户问 "Bellman optimality" 而 vault 里有 `节点/Bellman optimality.md`,该节点的 1-hop 邻居不会被装载。这是 by design 还是漏掉?
5. frontend `getInternalApiKey()` 是否存在? `chat_router` 全局加了 `require_internal_api_key` dependency,但 main.ts 的 fetch 调用是否传 `X-CLS-Internal-Key` header? 如果未传,在 DEBUG=False 环境会 403
6. `manifest` 段 (XML 注释 `<!-- ... -->`) 是否会被 Claude 误读为指令? prompt injection 风险?

**Q3 输出格式同 Q1。**

---

## Cross-cutting verdict (必填,在 Q3 之后)

请评估 4 项工程规约是否符合:

1. **DD-12 scope boundary**: backend agent 只改 backend, frontend agent 只改 frontend。所有 22 文件中是否有越界?
2. **DD-03 no mock**: 是否在新增代码里发现 TODO / mock data / 空函数 stub?
3. **DD-14 traceability**: commit `de0b4a7` message 是否含 PLAN-ID + Story trace?
4. **DoD-3 UAT sheets**: `_bmad-output/验收单/Story-2.2+2.9-Q1-rerank-hotfix-2026-05-12.md` + `Story-2.5.Y-Q2-multi-vault-hardening-2026-05-12.md` + `Story-2.2+2.9-Q3-global-search-2026-05-12.md` — each 7 段 + 段 4-B "👤 你来验" 0 tech 禁词 (curl/docker/HTTP/JSON/.env/endpoint/...)?

(如无法访问 worktree 文件直接判断,标 "无法验证")

---

## 终极输出格式 (你的整个回复结构)

```
### Q1 verdict: <PASS | CONDITIONAL PASS | FAIL>
[evidence]

### Q2 verdict: <PASS | CONDITIONAL PASS | FAIL>
[evidence]

### Q3 verdict: <PASS | CONDITIONAL PASS | FAIL>
[evidence]

### Cross-cutting verdict
- DD-12 scope: [PASS/FAIL/无法验证]
- DD-03 no mock: [PASS/FAIL/无法验证]
- DD-14 traceability: [PASS/FAIL/无法验证]
- DoD-3 UAT sheets: [PASS/FAIL/无法验证]

### Top 3 remaining risks (按严重度排序)
1. [P0/P1/P2] [1 句话]
2. ...
3. ...
```

⚠️ 不要写其他内容。不要写 Executive Summary。不要写 Recommendations。不要写 Project Overview。不要写 Roadmap。

如果你违反任一禁令,我会把你的回复打回重写。
