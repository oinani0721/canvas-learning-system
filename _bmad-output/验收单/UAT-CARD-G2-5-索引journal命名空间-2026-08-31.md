# 验收单 — CARD-G2-5 索引 journal 与后端残余状态命名空间化

> **批次**: BATCH-2026-08-29-第七批 · 车道 V5 第二卡
> **日期**: 2026-08-31
> **worktree**: `.claude/worktrees/card-v5-lance`（未 push）
> **卡文锚点**: 总账 v2 §G2-5（计划书 L265 / L115「pending journal 无 vault 维度」；
> 实证锚点 `vault_index_orchestrator.py:11,100-101,201-260` 与 `lancedb_index_service.py:60,182`）

---

## 一、这张卡给你带来什么（用户可感说明）

### 「切了 vault 之后，上一个 vault 没做完的事被算到这个 vault 头上」

后端有两条**索引待办清单**（技术上叫 pending journal），记录"这些文件还没索引完"
或"这些文件要从索引里删掉"。它们过去写在**一个固定的文件名**里，条目只记相对路径
（比如 `节点/递归.md`），**不记这是哪个 vault 的**。

于是会发生这种事：

1. 你在 vault A 里改了几个笔记、删了一个笔记，后端还没来得及处理，你关掉了；
2. 你切到 vault B 打开后端；
3. 后端读那份清单，把 A 的相对路径**当成 B 的文件**去处理 —— 要么索引一批 B 里
   根本不存在的路径，要么按 A 的删除意图去删 B 的索引行；
4. 等你再切回 A，那批待办已经被 B "消费"掉了，A 自己的反而丢了。

现在：清单文件按 vault 分开（`vault_index_pending__<vault>.jsonl`），
**A 的清单 B 读不到，B 也碰不到 A 的文件**。切回 A，A 的待办原样还在。

### 升级前留下的那份"旧清单"怎么处理

旧清单里的条目无从判断属于哪个 vault，所以后端**不再加载它**，而是把它改名成
`….pre-g25.bak` 存着（不删，你随时能翻）。

**代价（如实说，且第一版我说错过一次）**：如果那份旧清单里有"删除"意图，这次不会
被执行 —— 也就是"文件你已经删了，但搜索里可能还能搜到它"。

我第一版写的是"后端每 60 秒自己补上"。**这个说法不准确**，两条清单的兜底根本不同：

- **笔记索引那条**（orchestrator）确实有每 60 秒一次的全量比对，会自己发现"磁盘上
  没了但索引里还在"的行并补删 —— 但那趟比对**只看当前打开的这个 vault**。所以
  准确说法是"**等你再打开那个 vault**、它跑起来之后才补上"；如果那个 vault 你以后
  再没打开过，就一直不会补。
- **Canvas 索引那条**（lancedb）**根本没有周期比对**，它只在对应 canvas 再被改动时
  才重新排队。隔离之后如果那个 canvas 不再动，就需要人工重建一次索引。

**现网实测**：容器里那份旧清单是 **0 字节** —— 也就是说这次隔离，实际损失
**0 条意图**。

---

## 二、完成条件逐条对账

| 卡文条款 | 状态 | 证据 |
|---|---|---|
| (a) 两处 journal 按 vault key 命名空间 | ✅ | `app/core/vault_state_paths.py` + `vault_index_orchestrator.py` / `lancedb_index_service.py` 构造处 |
| (a) key 取 `settings.vault_id` 部署期值，**禁用 ContextVar 源** | ✅ | `deployment_vault_key()` 只读 `settings.vault_id`；`test_deployment_key_ignores_request_contextvar` 注入 `set_current_subject_id("vault:some_other_vault")` 后断言 key 纹丝不动 |
| (a) legacy 无维度旧 journal → `.pre-g25.bak` + warning，不加载 | ✅ | `quarantine_legacy_state_file()`；`test_legacy_dimensionless_journal_is_quarantined_not_loaded`（断言 recover()==0 + 改名 + 内容 sha 逐字节保留 + warning 文案） |
| (b) 行为测试：A 写 pending（含 delete）→ 以 B 重建 → recover()=0、A journal 字节不动、A 再激活 recover()=N | ✅ | `test_vault_a_pending_is_not_replayed_under_vault_b`（两条 delete 意图，B recover 0，A 文件 sha 不变，切回 A recover 2 且 op 仍是 delete） |
| (b) `lancedb_index_service` 同型 | ✅ | `test_index_service_pending_is_not_replayed_under_vault_b` |
| (c) delete 意图 quarantine 的语义损失写盘点文档 | ✅（口径已修正） | 盘点文档 §二。⚠️ 卡文写的"60s 反熵窗口"**只对 orchestrator 那条成立且仅限该 vault 再次运行时**；lancedb 那条**没有周期反熵**。两条已分开写明 |
| (c) 后端剩余全局状态文件逐一裁定 | ✅ | 同文档 §三：**A 2 / B 9 / C 14**（三类口径 + 先定 B 的准入标准，见下 §三.2） |
| (c) `fsrs_card_states` 不吸收 C1b，登记即可 | ✅ | 盘点表内标 **C（明示登记不改）**，注明让渡给 G3 切片 |
| (d) dry-run 迁移器 | ✅ | `backend/scripts/migrate_index_journals_g25.py`；本地 dry-run `pending=1 / exit 2`，目录逐字节零写入（测试断言） |
| (d) 裁判全绿 | ✅ | `test_g25_journal_namespace.py` **16 passed**（含 Codex round-1 的 6 条回归锁 + 1 条自查锁）；机械变异实证门是活的（见 §四） |

### 判据命令与结果

```
$ pytest tests/unit/test_g25_journal_namespace.py                        → 16 passed
$ python scripts/migrate_index_journals_g25.py                           → pending=1, exit 2 (本地 worktree)
$ pytest tests/integration/test_story_38_7_ac{3,5}*.py tests/unit/test_story_38_8_fallback_sync.py
      → 5 failed / 与 G2-4 提交 (9c366d27) 基线**逐条相同**, 零新增
$ ruff check（5 个改动/新增 py 文件）                                     → All checks passed
```

---

## 三、设计决定

### 1. key 为什么必须是部署期值而不是 ContextVar

journal 是**进程级**资源：`_worker_loop` / `_scan_loop` 在**请求边界之外**读写它。
若 key 取 per-request ContextVar，同一个进程里的同一份待办会随着当前请求换文件名 ——
那不是隔离，是随机分桶（写进 A 桶的条目下一次可能从 B 桶去找）。
`settings.vault_id` 与 LanceDB 表前缀同源，且已由 `sanitize_vault_id` 保证
只含 `\w`、长度 ≤200，直接做文件名安全。

**已知边界（如实）**：两个不同的 vault 目录名可能 sanitize 成同一个 key
（`CS 61B` 与 `cs-61b`）→ 共用同一份 journal。这与 LanceDB 表前缀、Neo4j group_id
的碰撞面**完全同源**，不在本卡单独收敛。

### 2. 盘点用三类口径，而不是硬塞进"命名空间化/豁免"两类

卡文要求"逐一裁定命名空间化/豁免+理由"。实际盘下来有一批文件既不是已命名空间化，
也不该说成"豁免"——它们**确实应该收敛**，只是属于别的卡的文件面（Neo4j 写侧
JSON 镜像族 → G2-3/G2-9/G4-1b；fsrs 域 → G3）。把它们标成"豁免"等于给一个假的
已完成信号。所以用 A/B/**C** 三类，C = 应收敛但不在本卡射程 + 明确去向。

### 3. `.gitignore` 必须同步改（差点漏掉的配套项）

`.gitignore:249-251` 原本用**字面文件名**忽略这两个 journal。文件名一改，
新名字就不再被忽略 —— 后果不是"多一个文件"，是**运行期状态被 `git add` 带进仓库**。
已改成 glob 并覆盖 `.tmp` 与 `.pre-g25.bak`；三个新形态都用 `git check-ignore -v`
逐一验证过。

---

## 四、门是活的（机械变异实证）

把 `namespaced_state_path()` 改回不带 key 的旧形态（即"没做这张卡"的状态）：

```
MUTATED RUN: 4 failed, 11 passed
还原逐字节相同: True
```

变红的正是跨 vault 不重放那组（整改后从 3 条增到 4 条）。变异脚本单次原地改 + 立即还原 + sha256 比对
（记忆 `reference_mutation_script_serial_only` 的纪律）。

---

## 五、变更清单

**新增**
- `backend/app/core/vault_state_paths.py` — 命名空间 + 隔离原语
- `backend/scripts/migrate_index_journals_g25.py` — 存量隔离器（默认只读）
- `backend/tests/unit/test_g25_journal_namespace.py` — 行为门 **16 条**（含 Codex round-1 的 6 条回归锁 + 1 条自查锁）
- `_bmad-output/审查/G2-5-后端全局状态文件盘点-2026-08-31.md` — 盘点 + 语义损失说明

**改动**
- `backend/app/services/vault_index_orchestrator.py` — journal 命名空间 + recover 时隔离旧件 + 可注入 `state_dir` + legacy 路径改为派生
- `backend/app/services/lancedb_index_service.py` — 同上
- `.gitignore` — 字面文件名 → glob（含 `.pre-g25.bak`）

---

## 六、待你裁决

> 两卡的裁决点已集中到 `_bmad-output/验收单/裁决点汇总-车道V5-G2-4与G2-5-2026-08-31.md`（编号 D1-D7），
> 该文件同时写明「为什么这些必须由你决定、我不自行执行」。下面是本卡这一半的原文。

1. **C 类 14 项要不要现在排卡**：其中 `canvas_events_fallback.json` / `outbox/events.jsonl` /
   `learning_memories.json` / `neo4j_memory.json` / `sync_checkpoint.json` / `failed_writes.jsonl` /
   `failed_edge_syncs.jsonl` / `dead_letter_episodes.jsonl` 都属 Neo4j 写侧回放/死信面，
   且 `fallback_sync_service` 的 docstring 里作者**已经登记过同一条移交**（原本给 G2-2）。
   建议整体并进 G2-9 隔离 canary。`qa_metrics.db`（Story 7.4 难度匹配滑窗）与
   `backend/logs/` 三件（audit / memory-system / alerts）是另外两组。
2. **日志治理要不要单开一张卡**：`audit.jsonl` 含 `node_id` + 自由 `details`，
   `memory-system-*.log` 是记忆系统 DEBUG 输出，两者都无 vault 字段、无保留期策略。
   本卡只登记为 C。
3. **现网那份 0 字节旧 journal** 要不要我在部署时顺手隔离（`--apply`），
   还是等后端自己在下次 recover 时做（两者行为相同）。
4. **MEDIUM-5 懒隔离**：隔离只在 `recover*()` 触发。若服务被禁用、或直接实例化后先
   `persist` 再 `recover`，旧文件会原地多留一会儿（**仍不会被加载**）。
   要不要把它升级成启动期的独立迁移门（`--apply` 作为升级硬门）？我判断当前形态
   已满足卡文的"不加载"，故只登记。

---

## 七、Codex 审查与整改

存档：`_bmad-output/审查/codex-review-CARD-G2-5.md`。
Round 1 判 **FAIL**（0 BLOCKER / 4 HIGH / 6 MEDIUM / 2 LOW）。逐条**实证复核**后
全部属实，其中三条推翻了我写进文档的结论。

| 级别 | 问题 | 复核 | 整改 | 回归锁 |
|---|---|---|---|---|
| HIGH-1 | 隔离件会覆盖同一秒的时间戳备份（旧 delete 意图不可逆丢失） | 属实：旧实现只查基础名存在性，不查时间戳名 | 改为 `O_CREAT\|O_EXCL` **抢占唯一名**再 `os.replace`（并发下只有一个进程能占住），失败则清掉占位并拒绝 | `test_quarantine_never_clobbers_any_existing_backup`（连隔离 3 轮，断言每一份内容都还在） |
| HIGH-2 | 既有恢复测试会改名**真实** `backend/app/data` journal | 属实：那些测试只重定位 `_pending_file`，而 legacy 路径是构造期固定的绝对路径 | `_legacy_pending_file` 改为**由 `_pending_file.parent` 派生的 property**；两个服务加可选 `state_dir` 注入口 | 新测试用 `state_dir` 注入；`_assert_production_state_dir` 先断言未注入时确实落在 `app/data`（LOW-11） |
| HIGH-3 | 长 CJK vault key 让 basename 达 631 字节 > Linux `NAME_MAX`，落盘静默失败而 `enqueue` 仍返回 accepted | 属实（实测 200 汉字 → 631 字节） | 新增 `fs_safe_key()`：按 **UTF-8 字节**预算（含最长的 `.jsonl.tmp` 派生名），超预算则"可读前缀 + sha256 前 12 位" | `test_filename_stays_within_linux_name_max`（含"不压缩确实超 255"的正向对照 + 短 key 原样保留 + 不同长 key 不撞） |
| HIGH-4 | "约 60 秒必收敛"不实 | 属实：lancedb journal **没有**周期反熵；orchestrator 的扫描也只覆盖当前 vault | 代码 docstring / 迁移器 / 盘点文档 / 本验收单四处口径全部改成分列两条 | — |
| MEDIUM-5 | 隔离仅在 `recover*()` 懒触发 | 属实 | 不改（当前形态已满足"不加载"），登记为裁决点 4 | — |
| MEDIUM-6 | 三个死门：ContextVar 只测 helper／legacy 只测 orchestrator／Lance 恢复只看计数 | 属实（Codex 给了三个"改掉功能仍 10 passed"的复现） | 三条全部加强：hostile ContextVar **存续期间构造两个真实服务**并断言文件名；补 lancedb legacy 入口测试；Lance 恢复断言调用参数、次数与 journal 被删除 | 3 条 |
| MEDIUM-7 | census 漏掉无维度 `.jsonl.tmp` 崩溃残留 | 属实（`_persist_sync` 走 tmp+replace，且被 .gitignore 藏住） | census 把 `<stem>.jsonl.tmp` 也判成 legacy | `test_migrator_flags_legacy_tmp_crash_residue` |
| MEDIUM-8 | 盘点漏了 `backend/logs/` 三件与可写 yaml | 属实 | 补入盘点，逐条给裁定 | — |
| MEDIUM-9 | `bug_log` / `dead_letter_episodes` 的 B 豁免不成立 | 属实：前者存 `request_params`，后者存 episode 正文 | 两条改判 **C**；并**先定 B 的准入标准**（配置/天然随 vault/可证不含 vault 内容）再逐条套 | — |
| MEDIUM-10 | 盘点含事实错误（`review_data.db`、outbox 路径、C 计数） | 属实 | 三条全改：`review_data.db` 只存在于**测试夹具**、容器里没有（我把宿主主仓目录当成了现网）；outbox 在 `backend/data/outbox`；计数重算为 A2/B9/C14 | — |
| LOW-11 | 测试没锁生产目录 | 属实 | `_assert_production_state_dir` | 每个 helper 都过 |
| LOW-12 | census 匹配过宽、stat 异常静默 | 属实 | 限定 stem + 非空 key + `unclassified` 单列；stat 失败改 `logger.error` | `test_migrator_census_is_not_over_broad` |

### 整改自己又带出一个缺陷（自查抓到，记在这里）

修完 HIGH-2（legacy 路径改由 `_pending_file.parent` 派生）之后，我跑相邻套件，
**当场多出 2 条失败**：`test_lancedb_recover_pending_with_partial_failure` 与
`test_lancedb_pending_recovery_on_restart`。

根因：那些测试把工作 journal 直接命名成**无维度的老名字**
（`svc._pending_file = tmp/"lancedb_pending_index.jsonl"`）。派生之后，legacy 路径
与工作路径**重合**，于是 `recover_pending()` 先把自己马上要读的那个文件隔离走，
再返回 `recovered=0`。

修法：`quarantine_legacy_state_file(..., active_path=...)` —— 两条路径重合就跳过。
生产不可能重合（命名空间名恒带 `__key`），但这条守卫保护的是"别把自己正在读的文件
搬走"这个更基本的性质。锁在 `test_quarantine_never_eats_the_active_journal`
（含"路径不重合时照常隔离"的正向对照，防止守卫退化成永远跳过）。

**这条的意义**：HIGH-2 的修法本身是对的，但它把一个隐含前提（legacy ≠ active）
从"构造期固定所以恒成立"变成了"依赖调用方怎么命名"。改防御性代码时新增的前提，
必须自己去撞一遍 —— 这次是相邻套件替我撞出来的。

**这一轮我自己先发现、Codex 也独立发现的**：HIGH-2（等审查期间记在 scratchpad 的 SF-1）。
**这一轮 Codex 发现而我完全没想到的**：HIGH-3（字节 vs 字符）、HIGH-1（同秒覆盖）、
HIGH-4（我把两条 journal 的兜底混为一谈）、MEDIUM-10（把宿主目录当现网）。

---

## 八、第八批 round-3 整改（HIGH-3 / HIGH-4）[BATCH-2026-09-01-第八批 / CARD-G2-5]

> round-2 存档（`_bmad-output/审查/codex-review-CARD-G2-4-G2-5-round2.md`）判 HIGH-3
> （失败反馈半边未修：`_persist_sync` 吞异常仍返回 accepted / Lance 同型 + HIGH-4 回归锁
> 为「—」）双 STILL-OPEN。本节为第八批收口记录；证据在 `_bmad-output/审查/evidence-g24/`。

### 8.1 修法（卡文 (a)(b)(c)）

- **orchestrator**（`vault_index_orchestrator.py`）：新增 `PendingPersistError(RuntimeError)`；
  `_persist_sync()` 失败 = 计数 + `_last_durable_error` + ERROR + 抛类型化异常；
  `enqueue` 捕获后**新条目弹回内存返回 `persist_failed` / 已有条目保留内存变更返回
  `persist_failed`**（两种都置 `_durable_degraded` 且照常 `_wake.set()`——内存 worker
  尽力而为，对外不报成功）；process_batch/reconcile/shutdown 三处批末调用捕获+计数，
  worker 循环不死（process_batch 只包 persist 一行，FTS 重建照常）；watcher 事件路径
  补 persist_failed WARNING（勘探发现的最后盲区）；`freshness()` 加性三键。
- **API**（`endpoints/index.py`）：`PathRefreshStatus` 注释枚举加 `persist_failed`；
  `RefreshChangedResponse` 加性 `persist_failed=0`/`durable=True`；任一路径失败 →
  `JSONResponse(503, resp.model_dump())`（完整 body）；成功路径保持 pydantic 模型返回
  （三个既有直调测试取 `.accepted` 属性——故意不改恒返 JSONResponse，防防回潮门
  `not hasattr(resp,"scheduled")` 退化成恒真空转）。
- **Lance service**（`lancedb_index_service.py`）：`_persist_pending()` 返回 bool（捕获面
  维持 OSError/TypeError/ValueError 不加宽，异常逃逸洞如实登记见 8.6）；`_debounced_index`
  False 时 ERROR「intent lost」含 canvas 名（与既有 WARNING 区分，ac2 的 any 断言不受影响）；
  重写段抽 `_rewrite_journal(entries)->bool`（tmp+os.replace 原子化；**调用方持锁、helper
  不再 acquire**——threading.Lock 非可重入自死锁防线写进 docstring；tmp 名 = `<journal>.tmp`
  与字节预算后缀一致、与 `.pre-g25.bak[.N]` 命名空间逐字不同且隔离器无 glob）；失败时
  原 journal 逐字节不动 + 清 tmp 残片；返回 dict 加性 `persist_failed: 0|1`；
  新增只读 `durable_status()`（不接端点，移交）。
- **`.gitignore`**：补 `backend/app/data/lancedb_pending_index*.jsonl.tmp`（本卡首次让
  Lance 侧写 tmp，orchestrator 侧 :251 有而 Lance 侧缺——合同点归本车道，勘探实测缺口）。
- **vault_state_paths.py 文案微调**（禁改面只动措辞，见 8.3 门③ 自洽所需）：
  docstring 粗体位置前移使「只覆盖当前部署」逐字连续；warning 追加两短语
  （orchestrator 侧「只覆盖当前部署的这个 vault」/ lancedb 侧「没有周期反熵」）——
  warning 原文是指路型文案（「收敛条件见 docstring」），卡文 (e)③ 要求对 warning 全文
  跑判据，故两短语必须在 warning 正文逐字存在。逻辑零改动。

### 8.2 回归锁（(d) 七条 + (e) 三条，`test_g25_journal_namespace.py` 16→26）

先红证据由 (f) 变异矩阵承担（M1-M6 每条变异杀指定门，见 8.4）；绿态
`pytest tests/unit/test_g25_journal_namespace.py -q` → **26 passed**（基线 16 + 新增 10）。

| # | 测试 | 锁什么 |
|---|---|---|
| ① | `test_orchestrator_enqueue_reports_persist_failed_when_state_dir_is_a_file` | 坏 state_dir → `persist_failed` + 弹回 + freshness 三键；正向对照好目录 accepted |
| ② | `test_orchestrator_coalesce_path_also_reports_persist_failed` | coalesced 路径同样报失败 + 保留内存变更 |
| ③ | `test_refresh_changed_endpoint_returns_503_when_journal_unwritable` | 真实 handler 直调（patch orchestrator 模块的 get_——端点内局部 import）→ 503 + 完整 body + durable=False；正向对照 200 语义模型 |
| ④ | `test_lance_persist_pending_returns_false_when_state_dir_is_a_file` | `_persist_pending` False + `durable_status` 计数；正向对照 True |
| ⑤ | `test_lance_debounced_index_logs_intent_lost_when_persist_fails` | ERROR「intent lost」含 canvas 名（替身抛 + 真实坏 state_dir） |
| ⑥ | `test_lance_recover_pending_keeps_journal_when_rewrite_fails` | 两半门：helper 半（坏 state_dir 下 `_rewrite_journal` False + 无残片）+ 传递半（`_rewrite_journal` 强制 False 走完整 recover → `persist_failed=1` + 原 journal 逐字节不动）。⚠️ 卡文字面「坏 state_dir 下 recover 走到重写」不可达（坏路径下 `exists()` False → recover 早返回），两半各证一半，**合起来仍不证明端到端 OS 失败链** |
| ⑦ | `test_long_cjk_key_accepted_through_real_orchestrator_enqueue` | 沿用既有 filename 锁场景，200 汉字 key 走**真实 orchestrator** enqueue → accepted + 文件真落盘 |
| e① | `test_convergence_wording_facts_are_bound_to_code` | `reconcile`/`_scan_loop` 存在 + `Settings.model_fields["VAULT_INDEX_SCAN_INTERVAL_S"].default==60`（**只锁声明默认值，不锁运行期 env 覆盖**——docstring 声明）+ Lance `dir()` 无 `reconcile\|scan\|anti_entropy\|_loop` |
| e② | `test_lance_quarantined_intent_has_no_automatic_reentry` | 隔离后事件循环跑 ≥3×debounce 替身调用恒 0；正向对照 schedule_index **恰 1 次**（`==1`，≥0 会把开关关闭的空转放行）；debounce 用**实例属性 patch**（`reload_settings` 对按值 import 的模块是静默 no-op——勘探实锤） |
| e③ | `test_convergence_wording_has_no_unqualified_60s_claim` | helper 对三段真实文本（quarantine docstring / migrator 模块 docstring（ast 零副作用加载，不用 importlib——防 __pycache__ 写入）/ caplog 隔离 warning 全文）断言两短语 + 60s 正则否定词；**篡改门×3**：无否定 60s 段 / 「有没有周期反熵」疑问句段（lookbehind 排除——朴素 in 会被疑问句骗过，盘点文档 :48 即此形态）/ 缺另一短语段 必须 AssertionError |

### 8.3 4-A Claude 已代验 —— 全部裁判输出

```
① 探针（裁判 #2，改码前 HEAD 输出 accepted False）:
  $ o=VaultIndexOrchestrator(vault_path=d, state_dir=<普通文件>); print(o.enqueue("upsert","节点/a.md"), o._pending_file.exists())
  → persist_failed False                                    （06:25 实跑）

② (d)(e) 裁判: pytest tests/unit/test_g25_journal_namespace.py -q → 26 passed（≥25 ✓）

③ (f) 变异 M1-M6（串行、还原逐字节比对；evidence-g24/g25-mutations.txt）:
  M1 enqueue 两路径恢复无条件 accepted（保留抛异常）→ ①②③ 红（3 failed）✓
     （首版只变异新条目路径 → ② 未红 —— 变异覆盖面也要对齐卡文，修正后重跑）
  M2 _persist_sync 恢复吞异常            → ①②③ 红（3 failed）✓
  M3 _persist_pending 恢复无返回值+调用点不判定（=改前原状）→ ④⑤ 红（2 failed）✓
     （纯 None 形态下 ⑤ 不红——None falsy 仍误发 ERROR；取调用点不判定的改前原状）
  M4 _rewrite_journal 恒 True           → ⑥ 红 ✓   M5 加空 reconcile → e① 红 ✓
  M6 docstring 加「约 60 秒必收敛」        → e③ 红 ✓
  RESTORE-IDENTICAL = True（三文件 sha256 前后逐字一致）

④ (g) 存量: 六文件 66 collected = 60 passed + 6 failed（comm 双向差集 0）⚠️ 卡文
  「66 全绿」在当前 HEAD 字面不可达——6 条失败为 HEAD 存量（逐条：review_fixes
  TestDoIndexCoverage×2 = `await client.initialize()` 对 MagicMock 替身抛 TypeError
  （远古 commit 14f0412d 引入 await 形态、测试替身未同步）；story_38_7_ac5×4 同文件
  存量红）。非本批引入，未适配（不属断言适配可修复面），如实登记。
  全 -k 套件（lancedb/supplementary/orchestrator/journal/g24/g25/index）:
  HEAD 基线（detached worktree + 同 venv 实跑）19 failed/267 passed ↔ 改后
  19 failed/277 passed（+10=新增锁），comm 新增 0 / 消失 0。
  断言适配 4 处（ac3:46 + g25:178/198/254）：整 dict 精确相等 → 逐键断言
  （persist_failed 加性键打红，卡文 (g) 允许适配断言；原语义逐键保留）。

⑤ 裁判 #7 真实 journal 未被触碰 —— ⚠️ 本卡期间抓到并修复一个**既有测试污染面**：
  全 -k 新口径第一次把 `test_vault_scope_409.py`（module 级 TestClient）拉进来，
  lifespan 起真单例 → start()/recover() 把真实 `vault_index_pending.jsonl`（10435B
  用户意图）隔离成 `.pre-g25.bak.1` + shutdown() 写出 0 字节命名空间 journal
  （HIGH-2 同型：第七批只修了当时 -k 面内的文件）。当场取证（mtime/ctime/inode/
  内容比对：_reserve_unique 无覆盖、零数据损失、artifact 移出至 scratchpad），
  修复 = vault_scope_409 + wave5 两文件加 `_no_real_index_orchestrator` 隔离 fixture
  （409 必须 module-scope——function-scope 的 patch 在 module 级 client 的 lifespan
  之后才生效，第一次实装当场复现抓到）；修复后全集跑 data 目录前后一致
  （2 文件不变，计数与开工基线一致），git status --short backend/app/data 为空。

⑥ grep 判据: grep -rn "persist_failed" endpoints/index.py vault_index_orchestrator.py | wc -l → 18（≥4 ✓；round-4 整改后重计，8.3 初版的「6」为当时计数）
```

### 8.4 (f) 变异与 shasum

见 8.3 ③。三文件 shasum 变异前=变异后（`g25-mutations.txt` 首尾段逐字相同）。

### 8.5 4-B 你来验

**索引失败不再假报成功** —— 你在软件里点「刷新索引」后，如果底层写不进记录，你会
**明确看到失败提示**，而不是看到「成功」然后发现新内容其实没被记住。其余一切照旧。

### 8.6 本卡未证明什么（必填，如实）

- Lance 侧 `schedule_index` 是 fire-and-forget：失败只落 ERROR 日志 + `durable_status()`
  计数，**没有接到 HTTP 状态面**（卡文明确的移交项）。
- `_persist_pending` 捕获面维持三类异常：其它异常会逃逸到 fire-and-forget 任务边界
  （Task exception 未检索日志），该洞如实保留、未静默加宽。
- (d)⑥ 两半门各证一半（失败识别 / 返回值传递），合起来仍不证明端到端 OS 失败链
  （卡文同款声明）。
- fsync/断电窗口不在证明范围（round-2 已声明，维持）。
- `durable_degraded`/`durable_write_failures` 目前只有 metadata 状态端点透传，无告警/UI
  消费方——「可观测」止步于可查询，不等于有人会看（移交）。
- e① 只锁 `VAULT_INDEX_SCAN_INTERVAL_S` 声明默认值；env/.env 覆盖后的运行期取值
  不在门内。

### 8.7 待你裁决（按第七批 §三 建议默认执行，均为默认值、**待你裁决**，未裁定）

| # | 事项 | 建议默认 | 本轮执行 |
|---|---|---|---|
| D4 | `_bmad-output` 从库列表排除 | 延后（第七批 §三） | 未动 |
| D5 | 刷新执行库内 decay_beta.py → 迁后端 | 延后（登记 CARD-G6-1b） | 未动 |
| D6 | md/json 配对原子性 + 跨进程互斥 | 延后（LOW 排卡） | 未动 |
| D7 | 懒隔离升级启动硬门 | 维持懒隔离（升级会重开 HIGH-2） | 维持 |
| 新1 | `persist_failed` → HTTP 503 + 完整 body 契约 | 503（全仓无活消费方实查） | 按默认落地 |
| 新2 | 内存回滚语义（新条目弹回 / 已有条目保留） | 按卡文 | 按默认落地 |
| 新3 | Lance `durable_status()` 是否接状态端点 | 不接（移交） | 未接 |

### 8.8 本节批次标记

历史 commit（9c366d27/4da0116d/a94caa3d/b2bf2e52）的批次日期误写 08-29 已在 G2-4
验收单 §8.5 登记；本卡 commit 使用正确标记 `[BATCH-2026-09-01-第八批 / CARD-G2-5]`。

### 8.9 Codex round-3

见 `_bmad-output/审查/codex-review-CARD-G2-5-round3.md`。

---

## 九、round-4 整改（Codex round-3 判决回应）[BATCH-2026-09-01-第八批 / CARD-G2-5]

Codex round-3（`codex-review-CARD-G2-5-round3.md`）判**清零=否**：HIGH-3 抓到一条真
**竞态**（recover 锁外重放期间并发 append 的意图被旧快照 rewrite/unlink 静默删除，
`/tmp` 实测复现）+ HIGH-4 三道口径锁各给出全绿绕过 + (d)②③⑥ 三死门 + 2 MEDIUM；
round-1/2 已 CLOSED 的 HIGH-1（隔离件不覆盖）/HIGH-2（真 data 不被测试碰）确认未重开。
本节为 round-4 整改记录。

### 9.1 竞态修复（HIGH-3 收口）

`recover_pending()` 重写分支改为**锁内合并语义**：重读当前 journal，只取**不在旧快照
行集合里**的行（= 重放窗口内新 append 的条目；旧行无论已消费与否都是残影，由
still_pending/unlink 语义接管），与 still_pending 按 canvas_name 取 timestamp 最新者
合并后再原子写。append 与 rewrite 同锁互斥、「重读→replace」是连续同步代码——竞态
窗口消除。副作用已验证：全部恢复成功 + 无并发 append 时仍走 unlink（三条「journal
应被删除」断言保持绿）；恢复失败条目 (still_pending) 照常保留。

**新回归锁** `test_lance_recover_preserves_concurrent_appends`：替身在恢复 canvas-a
时真实调 `_persist_pending("canvas-new")`（模拟窗口内并发 append 成功）→ 断言
canvas-new 在终态 journal 中 + 已恢复条目被消费 + 失败条目保留。变异 B1（合并分支
短路=恢复旧快照 rewrite）→ 该锁红（见 9.3）。

### 9.2 口径门与死门堵口（HIGH-4 + (d)②③⑥）

| Codex 绕过 | 堵口 | 验证变异 |
|---|---|---|
| e①：`_scan_loop` 空壳仍绿 | 加**行为探针**：真跑 `_scan_loop` 两个周期（interval patch 20ms、reconcile 替身计数）→ 必须 ≥2 次调用。首次用 `getsource` 检测被「return 短路+留死代码」变异骗过（自查发现）——getsource 只能抓删 body，抓不住死代码 | B4（空壳）红 ✓ |
| e②：0.20s 延迟重入逃过 0.04s 窗口 | 观察窗延长 **1.0s**（覆盖默认 0.5s debounce 两个周期）+ 断言 `svc._pending_tasks == {}`（「无自动重入」的本质：隔离不得调度任何 task） | e② 断言即窗口本身；Codex round-4 复核 |
| e③：lookbehind 可绕 / 60s 宽否定词误放 / 等价措辞漏判 | helper 重写：「没有周期反熵」改**所在句疑问标记检查**（？?吗呢是否有没有——旧 lookbehind 只挡「有没有」）；收敛断言正则扩 `一分钟/必然收敛`；语境判据收紧为**引用-否定**（旧文案/原文案/原文/旧说法/曾写/原话 + 不成立/是错的/错误/不对/不实/错的——裸「不是」可被「不是偶尔，而是…」误用）；篡改门 3→**6** 条（含专测 60s 语境半、等价措辞、肯定性修辞各一） | M6 红 ✓；篡改门内建 |
| d②：失败回滚字段仍绿 | 第二次 enqueue 改用不同 op（upsert→delete）+ 断言失败后 `_pending[p].op=="delete"`（内存变更保留是卡文写死语义） | B2（回滚变异）红 ✓ |
| d③：503 body 删四字段仍绿 | 断言 body 键集合**恰为七字段契约** + 四聚合值逐键 | B3（删字段变异）红 ✓ |
| d⑥：好目录假 True 零写仍绿 | 加正向对照段：真实 `_rewrite_journal` 在好目录必须**真的写**——journal 收缩为 still-pending 条目（内容逐键断言） | B5（假 True 零写）红 ✓；M4（恒 True）红 ✓ |
| MEDIUM：批处理末次写失败后 `durable_degraded` 仍 False | `_durable_degraded=True` 置位从 enqueue 移入 `_persist_sync` 统一（覆盖 enqueue/process_batch/reconcile/shutdown 全部路径） | M2 变异（吞异常）同时打掉计数与置位 → ①②③ 红 ✓ |
| LOW：metadata.py 过期注释「前端走 refresh-changed」 | 就地更正（复核实查无活消费方） | — |

### 9.3 round-5 变异矩阵（重绑定当前 bytes；`evidence-g24/g25-mutations-round5.txt`）

M1-M6 重生成（Codex 指出旧摘要 720feac… 与格式化后 bytes 脱钩）+ B1-B5 五个绕过
堵口验证，共 **11 个变异全部按指定门变红**，RESTORE-IDENTICAL=True（四文件 sha256
前后逐字一致：orchestrator `c2fa7e62…` / lance `83b5ab37…` / index.py `3fcc78a3…` /
vault_state_paths `3d4f2204…`——格式化前态，终态见 commit）。

### 9.4 终态裁判

- `test_g25_journal_namespace.py` → **27 passed**（26 + 竞态锁；format 后复跑）
- 六文件 66 collected = 60 passed + 6 存量失败（与 8.3 相同清单），comm 双向 0
- 全 -k 套件 19 failed（HEAD 存量）/ 278 passed（+1=竞态锁），与 HEAD 基线 comm 零新增
- `backend/app/data/` 全程 2 文件不变（原件 + 第七批隔离件），git status 干净
- grep 判据 18（≥4）

### 9.5 本节未证明什么

- 竞态修复的「重读→replace 锁内连续同步」论证依赖 CPython 单线程事件循环 +
  threading.Lock 互斥——多进程并发写同一 journal（当前不存在此部署形态）不在证明范围。
- e② 的 1.0s 窗口是经验窗（覆盖默认 debounce 两周期），不排除 >1s 延迟的假设性
  重入路径；`_pending_tasks=={}` 断言才是本质约束。
- 篡改门×6 是当前已知误放形态的封闭集，不是「任意误放文本必红」的全称证明。

### 9.6 round-4 首发被 cyber 拦截：stderr 抢救 + 三个新绕过堵口（重发前修复）

round-4 审查首次发出被内容过滤器拦截（`codex-review-CARD-G2-5-round4.md` 0 字节，
stderr 214KB 含审查过程可抢救正文——记忆 `reference_codex_exec_gotchas` 的处置路径）。
抢救出的**实测实锤**：e③ 旧 6 条篡改样本全部 REJECT（round-4 堵口生效），但 Codex
构造出 **3 个新绕过样本全部 ACCEPT**：

1. **反问句**：「难道 lancedb 没有周期反熵。」——句级疑问标记漏「难道」（反问
   语义 = 质疑「没有」）；
2. **中文数字 + 同义断言**：「最多六十秒保证达到一致。」——claim 正则只认阿拉伯
   数字与「必收敛」；
3. **引用语境伪造**：「旧文案错误已澄清；新结论：约60秒内必然收敛。」——引用与
   否定标记都被伪装彩翼，但「新结论」暴露这是活断言。

**堵口**（`_assert_convergence_wording`）：

- 疑问标记表 +「难道/岂/怎能/怎么会」；
- claim 正则族扩三支：中文数字「六十秒」入正则、「保证/确保…一致」收编为收敛
  断言形态、`一分钟…必然收敛` 独立分支（⚠️ 首版正则 `|` 优先级写丢收敛尾巴，
  本地复现三样本时发现并修正——变异/样本验证永远本地先跑）；
- 新增**活断言引导词**检查：命中断言 ±30 字符内含「新结论/结论是/因此/所以/
  现在可以确认」→ 一律拒绝（引用语境的合法形态不会有这些词）；
- 三个抢救样本**逐字固化**为篡改门（篡改门 6→9 条），全部 REJECT 本地验证 ✓。

抢救正文无最终判决（被拦在报告输出前）；按卡文「缩小读取范围重发一次（计入
轮次）」处置，重发版提示词限定读取范围并明示以文字描述绕过（不再构造可执行
攻击脚本，降低再次触发过滤器的面）。

### 9.7 round-4b 判决与 round-5 整改（最后一轮）

**round-4b 判决**（`codex-review-CARD-G2-5-round4b.md`）：HIGH-3 竞态主路径
**CONFIRMED-CLOSED**（残余降 MEDIUM）；e①②/d②③⑥ 全部 CONFIRMED-CLOSED；唯一
残留 **HIGH = e③ 的方向性死门**——helper 未断言「没有周期反熵」存在，缺它时
finditer 零次循环静默放行，且旧「缺另一短语」篡改门测的是缺第一短语的反方向。
另列 MEDIUM×6 / LOW×1。

**round-5 修复**：

| 项 | 级别 | 修复 |
|---|---|---|
| e③ 缺第二短语零次循环放行 | **HIGH** | helper 加独立存在性断言「没有周期反熵 in text」+ 新增**反方向**篡改门（样本刻意满足引用-否定语境，唯一能拒它的是存在性断言——本地验证 REJECT 原因恰为「缺事实断言」） |
| 锁内重读 OSError 被当空文件仍 rewrite/unlink | MEDIUM | fail-closed：读失败 → 不写不删 + 计数 + persist_failed=1 |
| 并发 fresh 条目未计入返回 pending | MEDIUM | `pending = len(still_pending) + len(fresh)` |
| d③ 缺混合成功/失败场景 | MEDIUM | 加混合锁：1 excluded + 1 persist_failed → 仍 503 + durable=False |
| d⑥「逐键断言」文案不符（实际只比 canvas_name） | MEDIUM | 断言加强为完整 dict 相等 |
| docstring 篡改门计数漂移（×4→×10） | LOW | 更正 |
| 相同行 multiplicity（并发 append 与旧行逐字同） | MEDIUM | **登记不修**：正常写入含时间戳字节必不同；触发需「字节全同 + 特定时序」，且同内容条目幂等——真发生等价于同意图重复登记，损失为零差。登记 9.8 |
| e① 扫描根/周期仍是源码+声明级绑定 | MEDIUM | **登记不修**：行为化需跑真 os.walk/长周期等待，成本远超风险（§9.5 已声明） |

修复后 `test_g25_journal_namespace.py` → **27 passed**；format/lint 过。

### 9.8 round-5 未证明什么（追加登记）

- 相同行 multiplicity：`orig_lines` 集合化使「与旧快照逐字相同的新 append」被当残影。
  真实写入恒带 ISO 时间戳 → 字节级重复要求毫秒内同 canvas 同 error 同内容，且该场景
  语义上等价于同意图重复登记（幂等无害）。**接受为已披露残余**，不设防。
- e① 行为探针证明「_scan_loop 周期调 reconcile」，未证明它使用**配置**周期
  （`self._scan_interval` 的绑定属源码级）。
- 篡改门 ×10 是已知误放形态的封闭集；正则/窗口法对任意 paraphrase 不可穷举，
  口径的最终兜底是三段受控真实文本 + 人工复核（盘点文档 md 不进测试）。
