# Canvas Learning System — ChatGPT wave-2 hotfix verification v3 prompt

> **本 prompt 用于 verify 你上次 v2 审查找到的 5 个问题是否真被 wave-2 commit `f018580` 闭口。**
> 复制本文件**全文**到 ChatGPT (推荐 GPT-5 thinking / o1)。

---

## 📍 必读资源 (你**必须**先 fetch 完所有 URL 再开始 verify)

### 仓库定位
- **GitHub Repo**: https://github.com/oinani0721/canvas-learning-system
- **Branch**: `worktree-feature-obsidian-hybrid-dev`
- **Wave-2 hotfix commit (verify 目标)**: `f018580`
- **Wave-1 commit (你上次审查过的)**: `de0b4a7`
- **Diff 看这里**: https://github.com/oinani0721/canvas-learning-system/compare/de0b4a7...f018580

### Wave-2 改动的 16 文件 blob URL

#### P0-1 Frontend X-CLS-Internal-Key header
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/frontend/obsidian-plugin/src/main.ts (buildBackendHeaders helper + 5 fetch site + settings UI)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/frontend/obsidian-plugin/tests/auth-headers.test.ts (13 新测试)

#### P0-2 LanceDB active_vault_id ContextVar wiring
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/lib/agentic_rag/clients/lancedb_client.py (line 383-440: 4 级 fallback)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/app/api/v1/endpoints/chat.py (line 743 rag_enrich_hook 漏修-1 lazy await)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/app/services/supplementary_search_service.py (line 209-232: 漏修-2 prior_reason)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/unit/test_lancedb_vault_isolation.py (9 新测试)

#### P0-3 Supplementary 真 fail-closed
- (chat.py 已列出)
- (supplementary_search_service.py 已列出, line 296-303 review placeholder + line 370-403 _classify_material_taint)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/app/services/supplementary_reranker.py (line 201-221: floor 排除 taint review/quarantine)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/unit/test_supplementary_reranker.py
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/unit/test_supplementary_search_service.py

#### 漏修-3 cleanup_loop create_task copy_context
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/app/services/background_task_manager.py (line 353)

#### 4 个 security regression tests (新文件夹)
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/security/test_global_search_auth.py
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/security/test_cross_vault_global_search.py
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/security/test_supplementary_review_floor.py
- https://github.com/oinani0721/canvas-learning-system/blob/f018580/backend/tests/security/test_supplementary_metadata_fuzz.py

---

## ⛔ 同 v2 prompt 的硬约束 (不要重复 v1 错误)

1. ⛔ 不要分析"Canvas Learning System" 项目名 vs Canvas LMS
2. ⛔ 不要建议 LTI / SIS / OAuth2 / Gradebook
3. ⛔ 不要讨论项目定位 / 重新命名 / 文档漂移 / 版本号
4. ⛔ 不要写 "Executive Summary" / "项目概览"
5. ⛔ 不要 fetch main 分支 / 旧 README / archive 目录

---

## 你的任务: 逐项 verify v2 verdict 是否被 wave-2 真闭口

你上次 (v2) 在 commit `de0b4a7` 发现的问题列表:

### Verdict-1: P0 `/api/v1/chat/global-search` 未鉴权 / frontend 缺 X-CLS-Internal-Key

**Wave-2 claim**: `main.ts` 加 `buildBackendHeaders()` helper,所有 4 个 backend POST handler (chatWithContext / studyQuestion / globalSearch / 共享 callBackend + postErrorCandidateAction) 全部用 helper 注入 `X-CLS-Internal-Key`。Settings 加 `internalApiKey` 字段 + UI。

**你需 verify**:
1. `main.ts:~349` `buildBackendHeaders()` 是否真的 conditional 注入 (key 空时不加,prod mode 必加)?
2. 5 个 fetch site (列出 line numbers) 是否真的都用了 helper,有没有漏的?
3. Backend `chat_router` 顶层 `Depends(require_internal_api_key)` 是否真覆盖 `/global-search`?
4. `auth-headers.test.ts` 13 个测试是否真覆盖所有 prod / dev 矩阵?

### Verdict-2: P0 LanceDB `_supp_lancedb_singleton` 跨 vault 漏读

**Wave-2 claim**: `LanceDBClient.active_vault_id` (line 383-440) 改 4 级 fallback:
- Level 1: explicit `_vault_id_override` (test 用)
- Level 2: `app.core.subject_config.get_current_subject_id()` ContextVar — strip `vault:` prefix + first segment
- Level 3: 旧 `app.config.get_current_vault_id()` (向后兼容)
- Level 4: `"default"` (last resort)

**你需 verify**:
1. Level 2 strip 逻辑是否正确处理 `vault:cs_61b:algorithms` → `cs_61b` (不是 `cs_61b:algorithms` 或 `vault`)?
2. Level 2 在 endpoint `set_current_subject_id(group_id)` 写 ContextVar 后,LanceDB **真的**读到正确 vault_id?
3. `_supp_lancedb_singleton` 是否还是 module-level singleton(没改 dict cache)?如果仍是 singleton,P0-2 修法是否充分?是不是应该改 `dict[vault_id]`?
4. `test_cross_vault_global_search.py::test_global_search_must_follow_request_vault_id` 是否真验证了端到端 wiring?

### Verdict-3: Medium `review`/`min_keep` fail-open (not fail-closed)

**Wave-2 claim**:
- P0-3a: `format_supplementary_xml` 内 review 分支输出固定 placeholder `[REDACTED: suspicious content (risk=X.XX); open source_path manually to verify]`,**不暴露**原 snippet 任何字符
- P0-3b: `rerank()` floor 兜底前过滤掉 `taint in {review, quarantine}` (兜底不豁免 taint)
- P0-3c: 新 `_classify_material_taint()` 扫描 snippet + title + wikilink + source_path 取 worst taint

**你需 verify**:
1. Placeholder 字符串是否真不含原 snippet 任何字节 (即使 1 字符泄漏也不行)?
2. `test_review_taint_outputs_placeholder_not_truncated_snippet` 是否真验证了 "原 snippet 全字符不在 XML 中"?
3. P0-3b floor 排除是否在 placeholder 已注入之前还是之后?顺序对吗?
4. `_classify_material_taint` 多字段 worst-takes-all 是否真实施(如 title clean / source_path quarantine → 整条 quarantine)?
5. 是否还有其他元数据字段没被 scan (e.g., raw metadata_json / canvas_file / heading)?

### Verdict-4: `general/__default__` fallback bucket 弱化隔离

**Wave-2 状态**: 仍保留 (向后兼容 caller without ContextVar)

**你需 verify**: 这个 fallback 是否仍能 silent 串库?是否应该改 fail-fast?或者加 logger.warning 至少让 ops 看见?

### Verdict-5: 我埋的 3 个雷 wave-2 catch 率

Wave-1 我故意埋的:
- chat.py:744 rag_enrich_hook 仍读 singleton
- supplementary_search_service.py:208 prior_reason 三元 dead code
- background_task_manager.py:353 cleanup_loop 漏 context=

**你需 verify**: 这 3 个 wave-2 是否都修了?(grep 一下 `_supp_lancedb_singleton` + `prior_reason` + `cleanup_loop` 配 `context=`)

---

## 终极输出格式 (严格,与 v2 一致)

```
### Verdict-1 (frontend X-CLS-Internal-Key): <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-2 (LanceDB vault wiring): <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-3 (review fail-closed): <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-4 (__default__ fallback): <CLOSED | PARTIAL | OPEN>
[evidence]

### Verdict-5 (3 wave-1 leaks): <3/3 CLOSED | 2/3 | 1/3 | 0/3>
[evidence per leak]

### 新发现 (wave-2 引入或漏掉的)
1. [若有]
2. [若有]

### Top 3 remaining risks (按严重度排序)
1. [P0/P1/P2] [1 句话 + file:line]
2. ...
3. ...
```

⚠️ 不要写其他内容。如违反禁令,我打回重写。
