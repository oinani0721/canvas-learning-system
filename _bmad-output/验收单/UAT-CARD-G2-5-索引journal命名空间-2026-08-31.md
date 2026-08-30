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
