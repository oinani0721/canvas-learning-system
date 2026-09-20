# UAT — CARD-REPLAY-REWRITE

> 批次: `BATCH-2026-09-18-第十五批` · 车道 `card-p2-outbox`（分支 `card/p2-outbox`）· 本车道第 **3/3** 张（末卡）
> `PREV` = `a05fa643`（本卡起点；起点锚 `d2ebf694` 容忍判据 §零.6 成立 —— `d2ebf694..a05fa643` 只含 `_bmad-output` 归档 commit，代码面零改动）
> `B15_BASE` = `9c4e7e82`（`git merge-base --is-ancestor 9c4e7e82 HEAD` → rc=0）
> 终态（收工重算）：最终代码 SHA **`47ebbc21`**（其后 commit 只动 `_bmad-output`）· 本卡代码 commit 数 **2**（`3d0c4fce` 主实现 + `47ebbc21` r1 整改）· Codex 轮次 **2**（r1 绑 `3d0c4fce`：B0 / H2 / M2 / L1；r2 绑 `47ebbc21`：**B0 / H0 / M2 / L2** ⇒ 绑最终 HEAD 的一轮 **B/H = 0 达成**）· evidence `evidence-replay-rewrite/` **70 份**（含 jev 分诊 2 份；被取代的开发迭代档均就地注记「作废/取代」）
> 存档：`codex-review-CARD-REPLAY-REWRITE.md` / `-r2.md`（首部 §2.4 齐：模型/reasoning_effort/codex/命令/审查绑定/会话头三行括注行号）；prompt 两份（r1 无后缀 + `-r2`）；`*.stderr*` 不入库（两 commit 逐文件核 0 条）

## 〇 一句话

`failed_writes.jsonl` 回灌链从「位置游标 + 快照长度比较 + 试过即成功」重写为「**稳定记录身份 +
来源 vault 落盘 + 写完读回执才算成功 + 身份日志崩溃恢复幂等 + `.overflow.*` 代际扫回**」；
三个写者落盘条目带 `record_id/vault_id/group_id/recorded_at/schema_version=2` 身份戳；
`main.py` 零改动；7692 真库门先红后绿；Codex 两轮后绑最终 HEAD 的 B/H=0。

## 一 §〇 事实复核 —— 卡文 → 实测（漂移表，`47ebbc21` 上）

| 卡文 | 实测 | 判定 |
|---|---|---|
| `main.py` 启动门 `:387/:420/:423/:463` | `:387`（门体）/`:420`/`:423`/`:463` 逐条相同 | ✅ 零改动（本卡不碰 main.py） |
| `fallback_sync_service._sync_failed_writes` `:273–427` | **全段重写**：新算法起 `:339`（符号名定位；旧游标/finalize 长度比较已退场） | 重写面（预期） |
| `_replay_scoring_entry_to_neo4j` `:599–691` | 重写后 `:869` 起（+ 两分支 helper） | 重写面（预期） |
| `_build_group_id_from_canvas` `:977–1014` | `:1377` 起（一行未改；P2-A/P2-B 之后行号漂移） | ✅ 符号一致 |
| `_PROGRESS_VERSION` `:67` | `:88`，值改 `"identity-v2"`（P2-C 换值，旧标记一律忽略） | 换值（预期） |
| `failed_writes_constants._replay_in_flight` `:36–85` | `:48–191`（P2-B 已扩写三态；本卡未动其契约） | ✅ |
| `_invalidate_replay_checkpoint` `:88–189` | `:194–295`（本卡未动） | ✅ |
| `append_failed_writes_bounded` `:192–284` | `:356` 起（P2-B 已扩；本卡未动） | ✅ |
| `memory_service._record_structured_outbox` `:502–522` | `:502–527`（本卡只换序列化调用 + 局部 import） | ✅ 段内 |
| `_flush_pending_failed_writes` `:2855–2886` | `:2868–2953`（P2-B 后漂移；本卡只换序列化调用 + 局部 import） | ✅ 函数体内 |
| `agent_service._record_failed_write` `:98–136` | `:102–149`（写者段只换序列化调用 + 局部 import） | ✅ |
| `episode_worker.DeadLetterStore` `:199–274` / `.count` `:270–274` | `:201–312` / `:288`（P2-B 后漂移；本卡零改动） | ✅ |
| `traces.py` 端点 `:466/:489` | `:469` / 依赖行（本卡零改动） | ✅ |
| `neo4j_client` 四函数 `:351–374/:376–419/:536–578/:1722–1806` | 逐条相同（AST 门 + 验伪锚落档） | ✅ 只新增 |
| `failure_counters.overflow_siblings` `:107–113` / `_unique_overflow_target` `:116–150` / `rotate_if_over_limit` `:177–231` | `:118` / `:138` / `:208`（P2-B 后漂移；本卡零改动，只 import `overflow_siblings`） | ✅ |
| 既有 38.8 单测 30 条 | 30 → 30（数据/断言对齐新契约） | ✅ |
| unit 红基线 33 | `grep -vc '^#'` = 33（开工自证） | ✅ |
| 卡文 (b)③「record_id/vault_id 0 行」 | 实测 6 行（均为既有 `_build_group_id_from_canvas` 的 `vault_id` 变量；`record_id` 单锚 0 行） | ⚠️ 卡文低估；先红以 `record_id` 单锚成立（0 → 20/4/12 三文件） |

## 一.5 「扫回 vs 明确丢弃」对比段（manifest.defaults.overflow：默认扫回；**交用户裁**）

| 维度 | 扫回（当前实现，默认） | 明确丢弃（对照） |
|---|---|---|
| 数据面 | `.overflow.*` 代际条目**全部回灌**（不丢；最老代际若已被 `_prune_overflow` 删除则不在集合内 —— 有界队列固有取舍） | 代际条目**永不回灌**（永久丢；活动文件轮转出的那批即出队） |
| 隐私面 | 旧死信内容进入图（与活动文件同口径） | 死信内容只留在本地 `.overflow`/`.synced`（30 天后删） |
| 磁盘面 | 全确认代际 ⇒ `.synced.<ts>`，沿 30 天 retention 删 | 同（写侧照常轮转/prune） |
| 与保留上限交互 | 扫回只覆盖**仍存在**的代际；写侧 prune 不受影响 | 无交互 |
| 回滚成本 | 去掉回灌集合中的 `overflow_siblings()` 纳入即可 | 加回即可 |

⛔ 未裁前按扫回实现（已实现 + 门 ③ 锁定）；若用户裁「丢弃」，改动点 = `_sync_failed_writes` 的 generations 集合。

## 二 DoD-3 段 4-A：裁判证据（逐条，文件均在 `evidence-replay-rewrite/`）

### (a) 第 0 分钟
`pwd`=card-p2-outbox / 分支 card/p2-outbox / 锚 `d2ebf694` rc=0 / `status` 空 / `BASE`=33 / pyright `test -x` / venv+env OK；`prev-sha.txt`=a05fa643。

### (b)(g) 先红 → 后绿（成对）
- **7692 门**：`red-gate-20260919T233145.txt` → **6 failed / 1 passed**（collected 7；三条钦定用例「崩溃恢复 / overflow 代际 / 来源 vault」全 FAILED 于图内断言）；`green-gate-20260919T234351.txt` → **7 passed**；整改后 `r1fix-gate-*.txt` → **7 passed**（含强化后的 ⑥）。
- **新单测**：`red-unit-20260919T233145.txt` → **10 failed**（全行为断言）；`green-unit-20260919T234351.txt` → **10 passed**；整改后 `r1fix-unit-*.txt` → **13 passed**。
- 收集数核对：`passed` 数 = AST `test_` 数（13 / 7）；无 `rc=5`、无 `0 selected`。

### (f) 结构判据成对 + AST 门 + 验伪锚
- `red-struct-*.txt` → `overflow_siblings`=**0**、`contiguous_end`=**11**（>0）、`record_id` 三文件 **0 行**；
  `struct-after-*.txt` → **3 / 0 / 20·4·12（各 ≥1）**。
- AST 门 `ast-neo4j-client-*.txt`：四函数（`record_score_history`/`initialize`/`_initialize_neo4j_driver`/`run_query`）
  `ast.dump` 与 `9c4e7e82` 版逐字符相同 = True×4；新函数在 = True；**验伪锚**（`_sync_failed_writes` 必须报不同）= True；`AST-GATE-PASS`。

### (h) pyright 成对
`pyright-open-*.txt` → `0 errors, 80 warnings`（PREV 态，还原窗口内实测 + sha 还原核验）；
`pyright-close-*.txt` / `pyright-close2-*.txt` → `0 errors, 82 warnings`。**零新增 ignore**；+2 warnings 为新增防御式
`isinstance`（`reportUnnecessaryIsInstance`，与基线 80 条大量同型）。**未用 `LEFTHOOK_EXCLUDE=python-typecheck`**。

### (o) ruff + F821 锚 + 格式
`ruff-*.txt`：13 文件 `All checks passed!` rc=0；`ruff-f821-anchor-*.txt`：F821 + rc=1，探针即删（`probe-clean=0`）。
`ruff-format-changed-lines-*.txt`（最终版）：五文件「改动行 ∩ 将重排行」= **0/0/0/0/0 ALL-PASS**（agent_service 的
497 行重排面全为 B15_BASE 既有漂移，不在改动集内）。提交用 `LEFTHOOK_EXCLUDE=python-lint`（同 P2-A/P2-B 口径，待裁 §五.9）。

### (i) 既有套件 + 目录级 + W4
- 点名套件 close：`suite-close-*.txt` **138 passed / 3 skipped** rc=0；t6b：`adapt-t6b-after-*.txt` **6 passed**；
  整改后 `suite-close2-*.txt` **138 passed** + `t6b-close2-*.txt` **6 passed**。
- `tests/regression` 目录级：open `regression-open-*.txt` **1913 passed**；close `regression-close-*.txt` **1913 passed**；
  整改后 `regression-close2-*.txt` **1913 passed** —— 三者逐字同。
- `tests/unit` 目录级：open **32F / 5762P**（diff 只 `<`）；close **32F / 5772P**；整改后 **32F / 5775P** ——
  nodeid 对基线 diff **只 `<`**（唯一 `<` = 基线头标注的 flaky 转绿）；W4：`blocked=0`、7691 目标 0。
- t6b「开工」态：还原窗口内 `t6b-open-*.txt` **6 passed**（PREV 态）；还原核验 `prev-window-*`：**SHA-IDENTICAL**。

### (k) 负控 4 段（各只拆一层；commit 后跑；`git show HEAD` 还原 + sha 逐字同）
| 段 | 变异 | 指定断言必红（失败正文） | 证据 |
|---|---|---|---|
| ① | 回执比对短路为恒 True | `test_receipt_mismatch_keeps_pending` + `test_receipt_conflict_requires_graph_newer` 双红 | `negctl-1-*.txt`（2 failed）|
| ①b | no-ts 分支现值保护拆掉（`r.timestamp IS NULL`→恒 true） | gate ⑥ `test_missing_timestamp_does_not_overwrite_newer_score` 红（分数被覆盖） | `negctl-1b-*.txt`（1 failed）|
| ② | 确认日志「先记日志」拆掉（finalize 才记≈不记） | `test_confirmed_log_crash_between_log_and_rewrite` 红 | `negctl-2-*.txt`（1 failed）|
| ③ | overflow 代际扫回拆掉 | gate ③ `test_overflow_generation_swept` 红 | `negctl-3-*.txt`（1 failed）|

四段均 `RESTORE_VERIFIED=yes`（before==after sha 逐字同）；段① 与 ③ 曾因脚本锚点漂移产出作废档，**已就地注记「取代」**
并由重跑覆盖（`negctl-1-sha-…03121` / `negctl-3-…010008` 注记在案）。

### (l) 地盘门
`territory-*.txt`：9 文件 = {fallback_sync_service / failed_writes_constants / memory_service（hunk 全落声明函数体内：
`-U0` 头 `@@ +515,5` `+523` `+2902,4` `+2912`）/ agent_service（写者段）/ neo4j_client（只新增，AST 门证）/
两份新测试 / test_story_38_8（越界登记）/ t6b（越界 #2 登记）}；⛔ 无 main.py / episode_worker / failure_counters / traces / conftest。
**验伪锚**：去掉 exclude 多出 `_bmad-output` 路径 **38** 条。

### (m) 现网只读核
`live-readonly-*.txt`：改动文件对 `fsrs_bridge/decay_beta` **0 命中**；`7691/7687` 命中全为拒连文案/端口解析断言/既有注释（逐行在档）；
验伪锚 `canvas-vault/.claude/scripts/` 命中 fsrs_bridge = **1**（≥1）。新测试连接面：7692 或 `tmp_path`（两测试文件全文可核）。

### Codex 两轮（§六 详表）
r1（绑 `3d0c4fce`）：B0 / H2 / M2 / L1；r2（绑 `47ebbc21`）：**B0 / H0 / M2 / L2**。存档首部 §2.4 齐；`.stderr` 不入库；0 字节档 0 份。

word-scan 留档：prompt 两份撰写段 **0/0/0/0**；存档正文各 **1 处「构造」**（复核者描述输入取值的自述用语 = 被引产出、非请求性措辞，只读不可改写）；本 UAT 0/0/0/0。

## 三 末态裁判汇总（绑 `47ebbc21`）

| 裁判 | 结果 | 存档 |
|---|---|---|
| 7692 门（7 条） | **7 passed**（真库） | `r1fix-gate-*` |
| 新单测（13 条） | **13 passed** | `r1fix-unit-*` |
| 结构判据 | 0→3 / >0→0 / 三文件 ≥1 | `struct-after-*` |
| AST 门 | 四函数逐字符同 + 验伪锚 | `ast-neo4j-client-*` |
| pyright | 0 errors（80→82 warnings） | `pyright-open/close/close2-*` |
| ruff + F821 锚 | rc=0 / rc=1 | `ruff-*` |
| 改动行零格式漂移 | ALL-PASS | `ruff-format-changed-lines-*` |
| 点名套件 | 138 passed | `suite-close2-*` |
| t6b 门 | 6 passed | `t6b-close2-*` |
| regression 目录级 | 1913 passed（open/close/整改后逐字同） | `regression-*-*` |
| unit 目录级 | 32F/5775P，diff 只 `<`，blocked=0 | `unit-close2-*` |
| 负控 4 段 | 各红在指定断言 + RESTORE_VERIFIED | `negctl-*-*` |
| 地盘门 / 现网核 | ⊆ 白名单 / 0 写者命中 | `territory-*` / `live-readonly-*` |
| Codex | r2 绑最终 HEAD B/H=0 | `codex-review-…-r2.md` |

## 四 本卡未证明什么（≥4）

1. **未证明**现网 `backend/data/failed_writes.jsonl` 的历史无身份条目在真实 vault 上的归属（隔离默认 + fixture；迁移属 G4-6 且需用户当次授权）。
2. **未证明** `_sync_canvas_events` / `_sync_learning_memories` 两链的新算法面（本卡只让游标退场；`_event_fingerprint` 同内容合并面未收口）。
3. **未证明**跨进程（多 worker / 双进程共享 `backend/data`）下的身份日志与 finalize 一致性 —— 已登记部署边界（r2 降级；单进程证据见 §六）。
4. **未证明**无 7692 容器机器上的门行为（不可达即整文件 skip；本次全程可达实测）。
5. **未证明** legacy `sha256` 合并「内容相同但语义独立」条目可接受（已裁为 legacy-only 取舍，待用户知悉）。
6. **未证明** overflow 扫回与 `_prune_overflow` 在回灌进行中被挤掉最老代际的竞态（P2-B 守卫超时后窗口内仍可能）。
7. **未证明** `.synced.*` 30 天 retention 适用于扫回后的 overflow 代际（隐私面待裁）。
8. **r2 MEDIUM-1 登记**：`timestamp` 非 ISO 可解析输入仍可逃出窄异常捕获、中断整代（确定性坏输入残余；生产写侧不产此类）。
9. **r2 MEDIUM-2 登记**：`score` 巨大 int（超 64 位）/字符串数字/浮点小数的类型-范围面未闭环（正常主路径为 int）。
10. **r2 LOW 登记**：空图上 no-ts+score 条目每轮重复第一次 LEARNED 写（幂等、无门覆盖）；overflow 全确认后 rotate→clear 间崩溃 ⇒ 日志 key 残留（不丢数据、审计面）。
11. **未证明**多进程并发同 `record_id` MERGE 的图侧去重（无 DB 唯一约束兜底）。
12. **未证明** `sync_confirmed_ids.json` 的跨代累积清理（仅按代际清除；被 rotate 换名的代可能残留 key，见 §四.10）。

## 五 台账待登记条目（≥4）

1. **修复 sha + 证据**：`3d0c4fce`（主实现）/ `47ebbc21`（r1 整改）；结构判据 0→3 / >0→0；7692 门 nodeid 7 条；负控 4 段（含 ①b 新增段）。
2. **越界登记**：`test_story_38_8_fallback_sync.py`（只改数据/断言，30=30，逐 hunk 在案）+ **`test_neo4j_replay_wire_t6b.py`（越界 #2：seed 补 record_id/vault_id 对齐新契约）**；新单测 `test_replay_rewrite_identity.py` 不在 manifest NEW 清单 —— 请主 session 补登地盘。
3. **`_PROGRESS_VERSION` 换值** ⇒ 现网 `sync_checkpoint.json` 旧游标被忽略（预期、不丢数据）；`_sync_learning_memories` 位置游标一并退场（文件级判据；重放幂等、不写回不轮转 ⇒ 安全方向）。
4. **「扫回 vs 明确丢弃」对比段待用户裁** + `CLS_REPLAY_LEGACY_NOSCOPE_VAULT` 产品口径待裁（全局开关：混合来源一键归属风险，r2 §②）。
5. **canvas/learning 两链重写与 `_event_fingerprint` 面移交**（候补卡）。
6. **现网 90 条历史条目迁移 → G4-6**（用户当次授权）。
7. **Codex 两轮**存档路径、绑定 SHA、B/H/M/L 计数（r1 `3d0c4fce` B0/H2/M2/L1；r2 `47ebbc21` B0/H0/M2/L2）。
8. **卡文 :X → 实测 :Y 漂移表**（§一，14 行）。
9. **`LEFTHOOK_EXCLUDE=python-lint` 口径待统一裁**（B15_BASE 既有 dirty 集；改动行零漂移 PASS 自证；P2-A/P2-B 同款）。
10. **pyright warnings 80→82**（+2 防御式 isinstance，与基线同型）。
11. **r2 两条 MEDIUM + 两条 LOW 登记**（修复或缩小输入契约，交下批/主 session；见 §四.8–10）。
12. **多进程部署形态禁用清单**（`uvicorn --workers` / backend 与 sidecar 同跑 replay / 双容器共享 `backend/data`；r2 §④）。

## 六 Codex 复核

| 轮 | 绑定 | B / H / M / L | 存档 | 处置 |
|---|---|---|---|---|
| r1 | `3d0c4fce` | 0 / **2** / 2 / 1 | `codex-review-CARD-REPLAY-REWRITE.md` | H1 → **已修**（缺 ts+score 整条留待）；H2 → **提请重分类**（单进程部署证据）；M1/M2 → **已修**；L1 → 接受为 legacy-only |
| r2 | `47ebbc21` | 0 / **0** / 2 / 2 | `codex-review-CARD-REPLAY-REWRITE-r2.md` | 总裁定：「单进程、单 uvicorn 部署模型下 r1 两 HIGH 不再阻断；HIGH-1 实质修复、HIGH-2 降级为登记边界」；r2 新增 2 MEDIUM + 2 LOW **登记不阻断**（§四.8–10） |

**HIGH-2 部署证据**：`backend/Dockerfile:28` CMD `uvicorn app.main:app --host 0.0.0.0 --port 8001`（无 `--workers`）；
`docker inspect` Cmd 同；`docker top canvas-learning-system-backend` 实测**恰 1 个 uvicorn 进程**；
`_sync_all_lock` docstring 自登记「进程内；多 worker / 多进程未覆盖」。

## 七 DoD-3 段 4-B：用户侧（零技术词）

> 后端连不上知识库那阵子攒下的学习记录，现在每一条都有自己的身份证和出生地——补回去时不会张冠李戴到别的课程库、
> 断电重来也不会补两遍或漏一条、连早前被挤到备份里的那批也会一起补回，我感觉记录终于不会悄悄丢或悄悄错。

**felt-sense**：以前一想到「攒着等恢复」这四个字心里是虚的 —— 攒的东西到底还在不在、补回去会不会串门、断一次电会不会乱，
全是问号。这轮做完再想这件事，是实的：每条记录有身份、有出处，补的过程断了就重来、重的不会重、该补的一条不落；
连最早被挤出去的那几批，也终于有人管了。
