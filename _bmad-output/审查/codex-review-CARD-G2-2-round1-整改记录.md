# CARD-G2-2 Codex round-1 整改记录

> **审查存档**: `codex-review-CARD-G2-2.md`（gpt-5.6-sol / ultra / read-only）
> **round-1 裁定**: 需整改，不可合并（FAIL）— 6 BLOCKER + 5 HIGH + 3 MEDIUM
> **整改日期**: 2026-08-28

## 处置总表

| # | 级别 | 问题 | 处置 | 证据 |
|---|------|------|------|------|
| 1 | BLOCKER | `chat.py` `/enrich-context`(:289) 与 `/post-turn-extract`(:661) 自建 sanitize/build/set 克隆，完全绕过 409；非 hook-cwd 例外 | **已修** — 两处改调 `resolve_vault_scope()`；`/post-turn-extract` 原实现连 sanitize 都没做，一并修正 | `test_chat_enrich_context_mismatch_409`、`test_chat_post_turn_extract_mismatch_409` |
| 2 | BLOCKER | `tips.py` 四处：GET 409 被宽捕获吞成 200 空列表；save/relation 409→500；batch 每 item 解析两次且幂等键写在 gate 前；callout-direct 先落幂等事件再 409 | **已修** — 全部端点解析提到 try / 早返 / 幂等写之前，batch 循环外解析一次 | `test_tips_get_mismatch_409_not_empty_200`、`test_tips_save_mismatch_409_not_500`、`test_tips_batch_mismatch_409_not_item_failure`、`test_tips_callout_direct_409_before_idempotency_write`（含纠正 vault 后重试仍可受理的正向断言） |
| 3 | BLOCKER | `/archive/session`：<4 条消息零解析早返；`request.group_id or resolver()` 让 deprecated group 覆盖必填 vault 并绕过 409；409 被吞成 200 `status=error`（SessionEnd hook 把 2xx 当成功 → 丢档） | **已修** — 解析先于早返与 try；`group_id` 改作 `legacy_group_id` 传入（显式 vault 优先） | `test_memory_archive_session_409_not_200_error`、`..._409_before_trivial_early_return`、`..._deprecated_group_cannot_override_vault` |
| 4 | BLOCKER | `extract-conversation` 第 10 份克隆且 canvas_path 分支用 **legacy** `build_group_id(subject, canvas)`（无 vault 段，多 vault 塌同桶）；`/episodes/batch` 零解析（缓存 episode 无 group → 跨存储 split-brain） | **已修** — 两端点改走唯一解析点；两个请求模型加 `vault_id`（推荐）并把旧 `group_id` 标 deprecated | `test_memory_episodes_batch_mismatch_409` |
| 5 | BLOCKER | 读侧仍可全局查询：`memory_service:592/903` 的 `group_id=None` 分支、concept history 无 group 参数、`learning_context._fetch_tips_and_errors` 不接收 group；score-history 查询与缓存键不含 vault | **部分修 + 移交** — 缓存键已加 vault 段（跨 vault 缓存串读，本卡修）；`group_id=None` 直通与 `_fetch_tips_and_errors` 传参属 **CARD-G4-1「禁 group_id=None 读侧全组封堵」** 明文范围（总账 v2 逐字点名 `memory_service.py:593/905` 两处 else 分支），本卡不越界，见下方移交条款 | 缓存键：`get_concept_score_history` `cache_key = f"{current_vault_id()}:..."` |
| 6 | BLOCKER（提交态） | `vault_scope.py` / `test_vault_scope_409.py` 为 untracked，按当前 diff 提交会让 tracked 文件 import 不存在的模块 | **已修** — 两文件（及 G4-2 的三个新文件）已 `git add` 入 index | `git status --short` 显示 `A` |
| 7 | HIGH | `conversation_inheritance` 邻居查询 helper 不接收 group，Cypher 仅按 node_id/name 查 → 暴露他 vault 邻居名与 edge label | **移交 G4-1** — 属读侧 Cypher 封堵范围（本卡铁律：不改读侧 Cypher 过滤逻辑） | 见移交条款 |
| 8 | HIGH | `errors.py:233` rebuild-graphiti 与 `inheritance.py:38` 把 raw group 直通写链（"legacy 不做 409"只豁免一致性检查，不豁免 canonicalize/inject） | **已修** — 两端点加 `vault_id`（走 409 门），旧 group 降级为 `legacy_group_id` 输入并标 deprecated | `test_errors_rebuild_graphiti_mismatch_409`、`test_inheritance_distill_mismatch_409` |
| 9 | HIGH | FSRS/BKT 派生事件 payload 不带 origin group；失败 outbox 只存 payload，startup replay 不恢复 ContextVar → vault A 的失败事件重启后写进 B | **半修 + 移交 G4-6** — 事件创建时物化 `group_id=current_group_id()` 进 payload（本卡）；outbox 重放对**历史无 scope 条目**的隔离/报错属 G4-6「持久 outbox」范围 | `event_handlers.py` 两处 publish |
| 10 | HIGH | 稳定 ID（`.canvas-config.yaml`）与目录名/display name 不等时，合法请求被全量误 409；hook-cwd 免 409 又会生成目录名 group 与稳定 ID 分裂 | **已修** — 新增 `active_vault_aliases()`（稳定 ID / ACTIVE_VAULT / 挂载目录 basename 三候选），命中任一放行且**归一到稳定 ID**；hook cwd 命中别名同样归一 | `TestVaultAliasTolerance` 三条（含"真他 vault 仍 409"反向断言） |
| 11 | HIGH | metadata batch 解析 1 次后每 item 调 HTTP handler 又解析 → 总 1+N，违反"每请求恰一次" | **已修** — 索引本体下沉 `_index_canvas_impl()`（不解析 scope），HTTP handler 解析一次后调 impl，batch 循环外解析一次调 impl | `test_metadata_batch_index_mismatch_409` |
| 12 | MEDIUM | 新增 `subject_id` 只在 SaveTip 写侧生效，GET 无对应参数 → 写 `vault:<id>:<subject>` 后永远回读不到 | **已修（撤回暴露）** — `_resolve_tips_group_id` 不再接 subject_id；字段保留（旧契约测试依赖）但不参与构组，docstring 写明贯通需读写端点成对改造 = 后续卡 | `tips.py:_resolve_tips_group_id` docstring |
| 13 | MEDIUM | `profile.py` 显式 `" "` 是 truthy，绕过 fallback 并在下游 canonicalize 成 `vault:default` | **已修** — 四处改 `group_id if group_id and group_id.strip() else current_group_id()` | `profile.py` 四端点 |
| 14 | MEDIUM | 409 裁判只覆盖 5 个 endpoint，未覆盖实际失守面；无"解析次数/零副作用"断言 | **已修** — 新增 `TestCodexRound1RectifiedEndpoints`（13 条，覆盖 chat×2 / tips×4 / archive×3 / episodes-batch / metadata-batch / distill / rebuild-graphiti）+ `TestVaultAliasTolerance`（3 条）；callout-direct 用例含"409 后纠正 vault 重试仍被受理"的副作用断言 | `test_vault_scope_409.py` 37 passed |

## 移交条款（本卡铁律外，不越界）

### → CARD-G4-1「禁 group_id=None 读侧全组封堵」

Codex BLOCKER-5 的主体（读侧全组查询）与 HIGH-7（邻居查询无 group 过滤）落在 G4-1 的明文范围内——总账 v2 G4-1 卡文逐字点名 `memory_service.py:593/905 两处 else 分支落 None`，并写明"封堵 service 层 group_id=None 直通 Neo4j 搜全组的路径…Neo4j client 读方法的 group_id 改必填或显式哨兵"。具体待办：

1. `memory_service.get_learning_history` / `get_review_suggestions`：无 `subject/canvas_path` 时 `group_id=None` → Neo4j 与内存回退均取消组过滤；
2. `memory_service.get_concept_history`：完全没有 group 参数；
3. `learning_context_service:290`：已算出 group 却调用不接收 group 的 `_fetch_tips_and_errors()`，其内部 `search_memories(group_id=None)` 三层皆无组过滤；
4. `conversation_inheritance._fetch_neighbor_records_for_inheritance`：Cypher 仅按 `node_id/name` 匹配，需对源节点与邻居双侧加物理 group 过滤（并遵守 G2-1 读契约 R1 的"每个 alias 逐一过滤"）。

**本卡已做的相邻修复**：score-history 缓存键加 vault 段（缓存层跨 vault 串读是缓存键设计问题，不属读侧 Cypher 封堵）。

### → CARD-G4-6「Graphiti 写入假成功封堵 + 持久 outbox」

Codex HIGH-9 后半：失败事件 outbox 的 **replay 路径**不恢复原 scope。本卡已在事件创建处物化 `group_id`，但历史遗留的无 scope 条目应在重放时**隔离/报错，不得猜当前 active vault**——该逻辑属 outbox 重放工具范围。

### → 插件 / hook / skill 侧（非 backend 卡）

Codex HIGH-10 建议调用方统一用 `/vault/current` 或配置里的 canonical ID。后端侧已用别名集合兜住（不会误 409 且归一到稳定 ID），但**调用方改造仍值得做**：现状依赖后端做别名消解，多一层隐式约定。

### 未触碰（全批禁改）

`exam_service.py` / `verification_service.py`（G5-12 地盘）、`review.py` / `review_service.py`（D3+D4 in-flight 锁定，L1 收尾 micro-patch 移交）。

## 全量回归口径

`tests/unit` 全量存在**大量既有失败**（基线 HEAD `37387a86` 同样失败）。已用同 venv 在 `HEAD` 基线 worktree 跑对照：本卡触及的 `test_memory_service_*` / `test_qa_38_4_*` / `test_difficulty_canvas_integration` 四文件失败集合与基线**逐条完全一致**（`comm -13` 与 `comm -23` 双向空集），零新增。
