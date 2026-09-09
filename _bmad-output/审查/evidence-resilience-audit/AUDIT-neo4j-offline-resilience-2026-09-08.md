# 架构审计 — 「Neo4j 离线时数据不丢」这一能力的完整性

> 日期 2026-09-08 · 树 `card-u11-red-c` @ `5139428d` · 全程只读（未跑测试、未启服务、未连 7691/7687）
> 起因：CARD-RED-C1（U11-A）把两条测试判为「数据面回归」移交 U5-C，项目负责人要求独立裁定该判断。
> **本审计发生在 U11-A 的两轮 Codex 代码复核之后，不属于那两轮，也不改变其结论（代码树未动）。**

---

## §0 ⚠️ 先读这一节：本审计做到了什么、没做到什么

| 环节 | 计划 | 实际 |
|---|---|---|
| 视角 A `writers`（穷举写侧） | 独立追踪 | ✅ **2026-09-09 19:xx 补跑完成**（11 缺口） |
| 视角 B `replayers`（穷举重放侧） | 独立追踪 | ✅ 完成（16 路径 / 9 缺口） |
| 视角 C `replacement`（替代者本体） | 独立追踪 | ✅ 完成（20 路径 / 11 缺口） |
| 视角 D `startup`（启动期恢复动作） | 独立追踪 | ✅ 完成（23 路径 / 9 缺口） |
| 对抗性反驳（每视角 ×2，共 8 个） | 主动推翻各视角结论 | ✅ **8/8 完成**（2026-09-09 补跑）——**6 条判 `refuted=true`**，实质改写了下方多条结论，见 §0.2 |
| 合并裁定 | 汇总 + 标注争议 | ✅ **完成**（13 agent / 0 error）——产出五链模型 + 10 条争议逐条并列，见 §0.2 与 §1 |
| 本 session 复验 | 抽验最高严重度条目 | ✅ 完成（4 条，见 §2） |
| 视角 C/D 重测 | （非计划，意外获得） | ✅ 11:1x 补跑时缓存未命中、真跑第二遍 ⇒ 获得**重测信度**观察（见 §0.1） |

### ⛔ 一个必须写明的判据陷阱（**2026-09-09 已解除，保留原文供追溯**）

**原文（2026-09-08 写下时的状态）**：

> workflow 的返回摘要里每个视角都是 `refutedCount: 0`。**这不表示「经反驳未被推翻」，而表示「反驳轮根本没跑」** —— 8 个反驳 agent 全部因配额失败，计数器自然是 0。
> 若不写明，后人读到 `refutedCount: 0` 会以为这些结论已通过对抗性检验。**它们没有。**

**2026-09-09 更新**：反驳轮已跑完，`refutedCount` 现在是**真值**：
`writers 1 / replayers 2 / replacement 2 / startup 1`（8 条反驳里 **6 条判 `refuted=true`**）。

⇒ 本文件结论的强度已升级为「四视角 + 8 条对抗性反驳 + 合并裁定 + 本 session 抽验」。
**但方向与 2026-09-08 的预期相反**：反驳不是确认了原结论，而是**推翻了其中几条最响亮的**（见 §0.2）。

### §0.1 重测信度（2026-09-08 第二次补跑意外获得）

补跑未命中缓存，`replacement` 与 `startup` 两视角**真跑了第二遍**（缺口数 11→12 / 9→8）：

- **语义层高度稳定**：两轮各自独立命中同一批核心主张（队列纯内存 / 死信无重放 / 死信默认无正文 /
  failed_writes 写活读死 / 告警被删 / 先删后确认），审计 §1 的结论在两轮里都成立。
- **条目层零重叠（措辞级）**：两轮的缺口清单措辞完全不同、数量有出入 ⇒
  **任何一轮的条目清单都是采样不是普查**，应视为缺口集合的**下界**。
  （第 3 跑 startup 还给出一条第 2 跑没有的事实，已吸收进 §1.1 的修正。）
- 这进一步支持本审计的定位：**方向可信、清单不穷尽**——正是「没有对抗性验证」时应有的表述。

---

### §0.2 ⚠️ 对抗性反驳推翻了什么（本节是本文件最重要的更正）

四个视角**共同**犯了同一个错：把搜索面划成 `backend/app/**` 下的 JSON 暂存文件，
于是把「学习数据」等同于「**进 Neo4j 的那份拷贝**」。被整层漏掉的是：

| 被漏掉的机制 | 位置 | 后果 |
|---|---|---|
| vault markdown **frontmatter**（项目自陈的真相源） | `memory_service.py:506-507`、`review_service.py:110-116` 原文 | 链 B/D 的持久性**本来就不经 Neo4j** |
| `<vault>/learning_events.jsonl` 账本 | `learning_event_log.py:151-155`（append-only + fcntl 跨进程锁 + 幂等 + 短写校验） | 学习过程可回放、图可重建 |
| EventBus **持久 outbox + 启动重放器** | `event_bus.py:343/369` ← `main.py:216` | **直接证伪「全仓没有任何活重放器」** |
| `failed_writes.jsonl` 的**活读侧** | `load_failed_scores`(`:2785`) ← `get_learning_history`(`:799`) | 不是「没人读」，是「**没人回灌**」 |
| `neo4j_memory.json` 每次降级都**读回内存** | `_initialize_json_fallback`(`:436-465`) | 原判「只写不读」是窄 grep 假阴性 |

> ⚠️ **四个「独立」视角同时划窄了同一刀，所以它们的「收敛」不构成佐证。**
> 共同盲区不会因为视角多而暴露，只会被互相印证成「共识」——这正是需要对抗轮的原因。

## §1 核心结论（**2026-09-09 经对抗轮改写**）

> 原标题是「三视角收敛的核心结论」。**「收敛」这个词现在不能用了** —— 四个视角划窄了同一刀，
> 收敛的是共同盲区（§0.2）。本节按合并裁定重写；被推翻的原文以引用块保留，不删。

**学习数据不是一条链，是五条互不相通的链。Phase 2 的「取代」只发生在其中一条上。**

| 链 | 内容 | 持久性 | Neo4j 离线时 |
|---|---|---|---|
| **A** 评分 / 学习事件 | 结构化半边 + 语义 episode | 分叉：一条断、一条堵 | 语义 episode **零落盘**；结构化半边落 JSON 但**无回灌** |
| **B** 结构化知识实体（callout/relation/error） | frontmatter 为主 + outbox 兜底 | **活**（真相源在 vault md） | 启动回填被 `main.py:386` 门住 ⇒ 停机期零覆盖 |
| **C** Canvas 事件 / 边 | 前端 IndexedDB outbox + vault md 重建 | **活**（但载荷不含评分/episode） | 白板结构不丢；边死信只写不读 |
| **D** FSRS 复习调度 | frontmatter + `learning_events.jsonl` 账本 | **完整，且完全不经 Neo4j** | **不受影响** |
| **E** EventBus outbox | 落盘 + 启动重放 | **唯一活着的「暂存↔重放」闭环** | 覆盖仅 Tier-2；`SCORE_SUBMITTED` 是 Tier-1，**结构上永不进 outbox** |

### 1.1 存在「有人写、没人**回灌**」的暂存面 —— 不止一处

> **⚠️ 本节标题与内容已更正。** 原文写的是「有人写、**没人读**」，被反驳实测推翻：
> 其中两处有活读侧。差别是实质的 —— **UI 照常显示，反而掩盖了断裂**。

| 暂存面 | 写侧 | 读侧 | 回灌侧 |
|---|---|---|---|
| `backend/data/failed_writes.jsonl`（实测 78 行） | **活**（3 个写入方） | **活** —— `load_failed_scores`(`:2785`) ← `get_learning_history`(`:799`)，并进用户可见历史 | **零个** |
| `backend/data/neo4j_memory.json`（实测 8 行） | **活**（掉线时自动接管） | **活** —— 每次降级 `_initialize_json_fallback`(`:436-465`) 读回内存 | **从未存在**（不在任何重放器覆盖面内） |
| `backend/data/failed_edge_syncs.jsonl`（实测 80 行，仍在增长） | 活 | — | 零 |
| `backend/data/learning_memories.json`（实测 6 行） | 活（DI 装配，**不受开关门控**） | 活（`review_service`/`rag_service`） | orphaned |
| `backend/app/data/canvas_events_fallback.json` | **取决于部署**（见 §4 争议 4.3） | — | orphaned |
| `data/dead_letter_episodes.jsonl` | 活（但本树不存在） | 只读消费者 3 个 | 零；且默认只存 200 字符残片 |

> **原文（已被推翻的部分）**：
> > `failed_writes.jsonl` … 重放侧「零个在跑」；`neo4j_memory.json` … 「从来就不在任何重放器的覆盖面内」（前半「零个**在跑**」若指回灌仍成立，但表头写的是「重放侧」且被读作「没人读」）

三个重放器都挂在 `FallbackSyncService` 上，而它自 `59586af1` 起零生产调用方 —— **这一条未被推翻**。
⚠️ 但反驳补出一条要紧的：**`FallbackSyncService` 本身不安全，不能直接接回**（见 §5）。

### 1.2 比 1.1 更靠前的一层：最典型场景**语义 episode 连暂存都没有**

> **⚠️ 已收窄。** 原文写「学习事件零暂存、零死信」，反驳实测指出**过强**：
> 评分的**结构化半边仍落** `neo4j_memory.json`。准确表述见下。

**Neo4j 在启动期离线**时（S1，最贴题的场景）：

- **语义 episode（链 A-2）**：`is_ready` 恒 False ⇒ `_enqueue_episode` 提前 return；
  调用方 `memory_service.py:632` **不接返回值**、照常 `return episode_id`
  ⇒ **零落盘、零告警、调用方拿到成功返回**。这一条成立。
- **结构化半边（链 A-1）**：落 `neo4j_memory.json`（**没丢盘**），但**没人回灌**。
- **链 B**：落 `failed_writes.jsonl`（status 诚实标 `degraded`）。

代码可达路径：`initialize_graphiti` 返 False → `episode_worker.py:377-378` `self._graphiti=None; return False`
→ `main.py:282-288` else 分支只打 warning、不调 `start()` → `is_ready`(`:527`) 恒 False。

⚠️ 仍然是**代码可达性**证明，**不是运行期观测** —— 合并裁定把这条列为「证据不足」第 1 项（§5）。

### 1.3 替代者本身不提供持久性

- 队列是纯内存 `asyncio.Queue(maxsize=100)`，单消费者、顺序处理（`episode_worker.py:288-289` 的 docstring 自己画了这张图）。
- `enqueue` 不做任何持久化 ⇒ 进程重启 / 崩溃 / 容器重建 ⇒ 队列内全部 episode **无声消失**，无 offset、无 WAL、无 replay 起点。
- 死信文件 `data/dead_letter_episodes.jsonl` **没有任何重放器**（详见 §2.3）。
- 死信**默认有损**：`EpisodeTask.to_dict()` 把 `episode_body` 截到 200 字符（`:108`），全文只在 `DEAD_LETTER_STORE_FULL_BODY` 显式开启时才落盘（`:231/:254`）。
- `stop()` 排空超时（默认 30s）后 force cancel，剩余队列与在途任务被丢弃且**不写死信**，只有一行 WARNING（`:485-487`）。

### 1.4 告警被同一次改动一并删除

`59586af1` 从 `main.py` 删掉的行里包含：

```
-        logger.warning("JSON fallback is disabled. Neo4j outage will cause data loss.")
```

⇒ 缺口发生时**没有任何运行期信号**会喊出来。

### 1.5 门抓到了，但一直只登记未处置

视角 D 指出：两条本应报红的守门测试确实在红基线里 —— **正是 U11-A 移交 U5-C 的那两条**
（`test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::{test_main_imports_fallback_sync, test_fallback_sync_called_in_lifespan}`）。

⇒ 防线一直在响，只是一直被当成「待处置的既有红」登记，没人追到底。

---

## §2 本 session 对最高严重度条目的独立复验（4/4 属实）

三视角是 AI agent 的静态追踪，本 session 对其中四条最要命的做了独立复验：

### 2.1 ⛔「入队成功即删除持久记录」—— 属实，且这是最危险的一条

`memory_service.py:2740-2762` 实测：

```python
enqueued = self._enqueue_episode(...)
if enqueued:
    recovered += 1          # ← 不进 still_pending
else:
    still_pending.append(line)
...
# Rewrite file with only still-pending entries under lock
```

`_enqueue_episode` 成功 = 数据**仅存在于内存队列**。此时该行被从持久文件中**删除**。进程在队列排空前死亡 ⇒ **两边都没了**。

**但注意**：`recover_failed_writes` 目前**零生产调用方**，所以这条路径在生产中**不会被走到**。它是**潜在**危险，不是正在发生的损失。

⇒ **这决定了修法**：最自然的「把这个恢复功能重新挂回启动流程」会**引入**一条数据丢失路径。修之前必须先改这个先删后确认的顺序。

### 2.2 队列是内存的 —— 属实
`episode_worker.py:288-289` docstring 原文：
`API handler --put_nowait--> asyncio.Queue --get--> Worker --await--> graphiti.add_episode()` / `(maxsize=100)  (single task)  (sequential, 5-30s each)`

### 2.3 死信无重放器 —— 属实
`dead_letter_episodes` 的全仓命中：写侧在 `episode_worker.py`；读侧只有
`traces.py:23`（按 request_id 查询的只读端点）、`scripts/census_dead_letter_episodes.py`（**有一条回归测试 `test_census_dead_letter_readonly_contract.py` 专门锁它只读**）、`generate_regression_tests.py`（生成测试用）。
**没有任何一个是重放器。**

### 2.4 告警被删 —— 属实
见 §1.4，`git show 59586af1 -- backend/app/main.py` 实测。

---

## §3 ⚠️ 关键校准：目前**不知道**实际丢了多少

视角 D 实测：`backend/data/failed_writes.jsonl` 当前 28 行内容**全是** `test.canvas` / `node-001` / `"error_reason": "Database connection failed"` 形态 —— 是 **TestClient lifespan 污染真 data 目录**造成的测试残留，**不是生产数据**。

（与 U11-A 的独立发现一致：该文件被 `backend/data/.gitignore:5 *.jsonl` 覆盖，工作树状态恒绿，看不见这类污染。）

⇒ **「写侧活着、读侧全断」是代码事实；「现网正在丢真实学习数据」是尚未证明的推论。**
两者不能混为一谈。本审计只证明了前者。

其它未证明项（三视角自报，原样保留在 `raw-lens-results.json` 的 `uncertain` 字段）：
- 全部 alive/orphaned 判定均为**静态调用图**结论，无运行期观测；
- worker 在真实运行期 Neo4j 中途掉线的实际表现（退避实测时长、队满触发点、死信实际条数）未验证；
- 现网死信文件内容无法在本树核实（`dead_letter_episodes.jsonl` 在本 worktree 不存在）；
- 不排除运维侧靠重启进程恢复——若如此，重启前滞留内存的队列内容去向未知。

---

## §4 对 U11-A 两个开放判断的裁定

### 判断一：(e) 两条判「数据面回归」并移交 U5-C —— **成立，且原判偏保守**

U11-A 给的 8 条源码证据全部被三视角独立复现。且三视角发现缺口**比 U11-A 认定的更宽**：
不只 `failed_writes.jsonl` 一个暂存面，还有另外三个；且最典型场景（启动期离线）连暂存都没有。

⇒ 移交动作正确。移交说明应据此**升级**（见 `evidence-red-c1/c1-verdicts.md` §2 的补记）。

### 判断二：`ENABLE_GRAPHITI_JSON_DUAL_WRITE` 翻成 `False` 的前提 —— **分成两句才准确（2026-09-09 改写）**

> **⚠️ 原文过粗。** 原文只写「前提不成立」，被反驳指出：系统自己的架构声明是
> 「vault markdown = 真相源，Neo4j = 派生投影」，在链 B/D 上这个替代**是兑现的**。
> 合并裁定给出的准确形态是两句，不是一句：

> - 「已被 **worker** 取代」 → **不成立**
> - 「已被 **vault frontmatter + 启动回填** 取代」 → 对链 **B / D 成立**，对链 **A / C 不成立**
> - 而**翻默认值时写在配置里的理由是前者，不是后者**。

「已被 worker 取代」不成立的四条独立依据：

| # | 维度 | 依据 |
|---|---|---|
| a | **覆盖面** | worker 只接 `add_episode` 一路语义 episode；Canvas 6 写点 / 边死信 / `LearningMemoryClient` JSON 库 / `neo4j_client` 降级 JSON —— 四条通道从来不在覆盖面内。被翻掉的开关管的恰是其中一条（Canvas），**两者不是同一个面** |
| b | **耐久性（决定性）** | 被取代者是「落本地文件 + 启动重放」= 跨进程存活、**与 Neo4j 独立故障域**；worker 是纯内存有界队列，且主路径与兜底路径**终点是同一个 Neo4j** ⇒ Neo4j 一挂两条同时失效。**在故障域这一维上这是降级，不是等价** |
| c | **时间窗** | worker 韧性窗 ≈ 14 秒；被取代者的窗是「直到下一次成功重放」。真实停机以分钟/小时计（MEMORY.md 记录过 2026-09-05 复习链停摆整天） |
| d | **替代承诺的重放端被同批删掉** | 写侧关（`daa9fd37`）+ 重放摘 + 告警删（`59586af1`），同日完成，至今无人补 |

**打回 `True` 同样不是修复**（此条未被推翻）：dual-write 写的 `learning_memories.json`，
其回灌器 `_sync_learning_memories` 同样挂在零调用方的 `FallbackSyncService` 上。

⇒ **这个开关不是修复点。** U11-A 把 3 条测试翻成断言 `default is False` 是对的
（锁的是「当前默认关闭」这一**事实**，该事实为真且经内存态变异验证承重 KILLED 3/3）。
错的是当初翻转它时给出的**理由**，不是测试。

⚠️ 新增争议（反驳提出，本审计无法证）：开关的**生产实际取值未知**。
`config.py:477` default=False、`backend/.env:85` 是注释态，但 **`.env.example:226` 是未注释的生效赋值 `=true`**，
而 README 部署步骤是 `cp .env.example .env`。⇒ 关 = 连暂存都没有；开 = 写活读死的无界坟场。**方向相反。**

## §4.5 合并裁定列出的 10 条争议（**原样转录，不强行统一**）

| # | 争议 | 甲方依据 | 乙方依据 | 本次裁定 |
|---|---|---|---|---|
| 4.1 | `failed_writes.jsonl` 是否「零读侧」 | writers/replayers/startup 三视角：只 grep 了两个重放器名 | 反驳：`load_failed_scores`（`:2785`）被 `:799` 实调 | **乙方成立（实测）**。「没人回灌」为真，「没人读」为假。差别是实质的：UI 看得见反而掩盖断裂 |
| 4.2 | `neo4j_memory.json` 是否「只写不读」 | writers/startup：`grep "neo4j_memory"` 只命中路径常量 | 反驳：`_initialize_json_fallback`（`:436-465`）每次降级都把文件读回 `self._data` | **乙方成立（实测）**。原判是窄 grep 假阴性（读走 `self._storage_path`）。但「**回灌器**不存在」双方一致，仍成立 |
| 4.3 | 开关生产实际取值 | 四视角均判「恒 False」（据 `config.py:477` + `.env:85` 注释） | 反驳：`.env.example:226` 是**未注释生效赋值 `=true`**，README 部署步骤是 `cp .env.example .env` | **有争议，且取决于部署**。实测三处文本均属实。取值不同结论方向不同：关 = 连暂存都没有；开 = 写活读死的无界坟场。**线上真实取值本次无法证**（见 §5.2） |
| 4.4 | `learning_events.jsonl` 有无重放器 | writers/replayers：「无任何生产重放器」 | 反驳：quiz-answer 技能 A2「追加前重放至空」 | **各对一半（实测）**。A2 存在且活，但它重放进 **frontmatter**，不是 Neo4j。原判在 Neo4j 轴上成立；作为整体判断是搜索面只划到 `backend/**/*.py` 造成的假阴性（vault 侧 python 内嵌在 SKILL.md 里） |
| 4.5 | `migrate_neo4j_data.py` 是否人工回灌通道 | writers：「须人工跑脚本回灌」 | 反驳 + replayers：该脚本无 driver/bolt/Cypher，是 JSON→JSON Unicode 清洗 | **乙方成立（二手，两个独立视角一致）**。「须人工跑脚本」是**不成立的安慰** |
| 4.6 | 死信 685 条 / 2026-04-07 | replacement 视角引为实证 | 反驳：该数字来自另一棵树（`feature-obsidian-hybrid-dev`）的快照 | **本树无法核实**（实测该文件不存在）。不进结论数字，只作旁证 |
| 4.7 | `backfill_vault` 该记缺陷还是记正常 | replacement/startup：「恰在需要它的场景里不执行」 | 反驳：「重放器在目标恢复后才跑正是重放器的定义」 | **各对一半**。作为**恢复器**它正常；作为**停机期兜底**它零覆盖 —— 而翻开关所需要的恰是后者。且覆盖面只到写进 md 的东西 |
| 4.8 | 「Neo4j 离线 ⇒ 每一条学习 episode 直接消失」 | writers gap#1 | 反驳：评分的结构化半边仍落 `neo4j_memory.json` | **原判过强（实测确认反驳）**。准确表述：语义 episode 这一份消失（零落盘）；结构化半边落 JSON 但无回灌 |
| 4.9 | `create_learning_relationship` 的 group_id fail-closed 是否算一条独立丢失面 | 反驳提出：`:1005-1016` 在 `run_query` 前 `return False`，连 JSON 都进不去，上游不检查返回值 | 无人反对，但也无人给出触发证据 | **机制成立（实测代码属实）**，但触发条件是 group_id 解析失败、**与 Neo4j 是否在线无关**；真实流量中是否发生过，**证据不足** |
| 4.10 | 前端 IndexedDB outbox 算不算「该能力已有覆盖」 | startup/replayers：判为「同名易混淆项，非后端启动恢复」 | 两条反驳：它正是 Neo4j 掉线时白板写入不丢的实现 | **各对一半**。它确实活着且覆盖链 C 的白板结构写入；但载荷只有 node/edge/board，**不含评分、episode、学习事件** ⇒ 不能计入被审能力的主面 |

---

---

## §4.6 合并裁定列出的「证据不足」（**原样转录**）

1. **无任何运行期观测。** 全部结论来自静态只读追踪。核心那条链（离线 → worker 不就绪 → episode 静默丢）是三点串成的**代码可达性**（`episode_worker.py:377-378` + `main.py:282-288` + `:527`），**没有一条真实离线启动的日志**。缺：一次断网启动 + 日志中 `[Phase 2] GraphitiEpisodeWorker in degraded mode` 与 `Episode worker not ready, skipping enqueue` 的实际出现记录，以及同期 `dead_letter` / `failed_writes` 是否新增。
2. **线上 `backend/.env` 的开关实际取值未知**（gitignored，本次只读了本 worktree）。缺：线上部署树该行的实测。这直接决定 §4.3 的方向。
3. **`backend/data` 现存 78 / 80 行的来源。** 与 MEMORY.md 记录的「TestClient lifespan 污染真 data」形态一致（`Simulated Neo4j failure`、`partial.canvas` 等）。⇒ 它们证明「写者有效 + 无人回灌」，**不证明生产已丢 78 条**。缺：生产日志的 `episodes_dropped_queue_full` / drain timeout 计数，才能给出真实丢失量。
4. **死信实际落盘位置。** 相对 CWD（`episode_worker.py:225`）。Docker 下可从 `WORKDIR /app` 推出；宿主机直跑 uvicorn 时取决于启动目录，未实跑验证。同一 CWD 依赖也影响 `SettingsConfigDict(env_file=".env")` 的加载（二手）。
5. **`DEAD_LETTER_STORE_FULL_BODY` 是否被外部注入。** 只能证明它不在 `.env` / `.env.example` / `docker-compose.yml`，无法证明 shell / launchd 层没有设。
6. **canvas-vault 侧其余写者未穷举**（`start-exam-board` / `ai-linked-doc` 等技能是否各有独立暂存/重试文件）。
7. **A2 重放器「线上就是这一版」未证。** `daily-review-wrapper.sh` 的逐字节 `cmp` 门只覆盖 `fsrs_bridge.py` / `decay_beta.py`，**不覆盖 SKILL.md**（二手）。
8. **`FallbackSyncService` 三个 `_sync_*` 的正确性未验。** 它零调用，验它不影响本裁定；但若要把它挂回启动流程，必须先审两个已知坑：(i) `recover_failed_writes` 是**先删后确认** —— `memory_service.py:2746-2755` 里 `_enqueue_episode` 返 True（仅进内存队列）即从持久文件删除该行，`:2760-2778` 重写文件（二手，机制描述与我读到的 `:2746` 调用点一致）；(ii) 其兜底 `except` 只收 `(RuntimeError, ConnectionError, TimeoutError)`，不覆盖 neo4j 驱动真抛的 `ServiceUnavailable` 与 tenacity `RetryError`（**二手**，引自本树 `_bmad-output/审查/evidence-red-c2/familyD-tail-evidence.json:133`，本次未复验）。⇒ **「自然修法」本身不安全，不能直接接回。**

---

---

## §4.7 给非技术负责人的白话结论（合并裁定产出，原样转录）

有没有东西在悄悄丢：有，但不是全部。每天的复习进度、错题和批注写在笔记文件里，图数据库停了也照样能用，这部分是安全的。会丢的是「这次学习发生了什么」的那份摘要——图数据库一停，它连草稿都不留，系统还照常回报「已保存」。另外几份写在硬盘上的失败记录，眼下只进不出：写的人还在写，但当初负责把它们送回数据库的那个搬运工，今年三月连同一句「关掉兜底会丢数据」的提醒一起被删掉了，至今没人补。

什么时候能被发现：几乎发现不了。查历史时，界面会把硬盘上那份失败记录一并显示出来，看着分数都在；只有依赖图谱的功能——复习推荐、掌握度、出题选材——会悄悄少料。硬盘上那两份记录现在各有七八十条，仍在增加，但里面不少是测试留下的，真实用户到底丢了多少，现在查不出来。

建议你做两个决定：第一，把那个搬运工重新接回开机流程，但接之前必须先修它「还没送到就先把底稿删掉」的毛病，否则修完更糟。第二，先在测试机上断开图数据库启动一次，用日志把真实丢失量测出来，再决定要不要把那个默认开关改回去——现在两边都只有推理，没有实测。

---

## §5 建议（给项目负责人）（**2026-09-09 按合并裁定更新**）

**排卡，第一张卡的内容是「量」不是「修」** —— 此条未被推翻，且反驳给了更强的理由。

⛔ **不要直接把 `FallbackSyncService` 挂回启动流程。** 原文只列了一个坑，裁定补到两个：

1. **先删后确认**（§2.1）：`memory_service.py:2746-2755` 里 `_enqueue_episode` 返 True
   （仅进**内存**队列）即从持久文件删除该行 ⇒ 接回反而新增一条丢失路径。
2. **兜底 except 收不住真实异常**：其 `except` 只收 `(RuntimeError, ConnectionError, TimeoutError)`，
   **不覆盖** neo4j 驱动真抛的 `ServiceUnavailable` 与 tenacity `RetryError`
   （二手，引自 `evidence-red-c2/familyD-tail-evidence.json:133`，本次未复验）。

建议卡序：

1. **量** — 断网启动一次，用日志把真实丢失量测出来（`[Phase 2] GraphitiEpisodeWorker in degraded mode`
   / `Episode worker not ready, skipping enqueue` 的实际出现 + 同期 `dead_letter`/`failed_writes` 增量）。
   ⚠️ 现存 78/80 行**多为测试残留**，不能当生产丢失量。
2. **查线上开关真值** — `backend/.env` 是 gitignored，本次只读了本 worktree；
   它决定链 C 是「连暂存都没有」还是「无界坟场」，**方向相反**（§4 争议 4.3）。
3. **止血**（若 1 证明确有损失）— 先修上述两个坑，再谈接回。
4. **补告警** — `59586af1` 删掉的那条警告应以某种形式回来。
5. **补一条 Tier-1 的持久面** — `SCORE_SUBMITTED` 是 `TIER_1_CRITICAL`，
   而 `_write_outbox` 只在 Tier-2 路径上被调 ⇒ **评分事件结构上永不进 outbox**（`canvas_events.py:211`）。

## §6 证据文件

| 文件 | 内容 |
|---|---|
| `raw-lens-results.json` | 前两跑三视角的结构化输出（paths / gaps / uncertain 原样）。⚠️ **不含** 2026-09-09 补跑的 writers 视角与 8 条反驳 |
| `journal.jsonl` | 完整 18 条 result（13 个去重 key）。**新旧区分**：`2fe63739a4591` / `39201d118df31` / `e554a5eedb66b` 三个 key 是 09-08 缓存复用，其余 10 个为 09-09 新产生 |
| 本文件 | 汇总裁定 + 本 session 复验 + **09-09 对抗轮后的结论更正** |
| `../evidence-red-c1/c1-verdicts.md` §2 | U11-A 原始 8 条移交证据 |

### workflow 运行记录（`wf_69753b68-0aa`，共四跑）

1. 首发：5 agent 全败于鉴权抖动（403）；
2. 重跑：11 agent 中 3 成功（replayers / replacement / startup），8 败于 session 配额；
3. 补跑：9 agent 中 2 成功（replacement / startup 第二遍，见 §0.1），7 败于 **weekly 配额**；
4. **2026-09-09 19:xx 补跑（weekly 配额重置后）：13 agent / 0 error 全部完成** —— 
   3 份缓存复用 + 10 份新产生（writers 视角 + 8 条反驳 + 合并裁定）。
   耗时 ≈ 28.8 min，subagent token ≈ 196 万，tool_uses 584。

⚠️ **resume 的一个坑（本次实测）**：`resumeFromRunId` 找的是**当前 session** 目录下的
`subagents/workflows/<runId>/journal.jsonl`，而该 run 属于旧 session（`4a464adb…`），
直接 resume 报「journal 不在盘上」。把整个 run 目录（journal + 各 agent jsonl）
拷进当前 session 的同名路径后，resume 正常接上并复用了那 3 份缓存。
⇒ 「找不到」不等于「不存在」，而是「没在它找的那个位置」。

⚠️ **3 条 safety classifier 不可用的告警**（`refute:replacement:A/B`、`refute:replayers:A`）：
分类器 server error / overloaded，非 agent 本身失败。这三条的输出本审计**已逐条读过并采信其中的实测引用**，
但「未经分类器复核」这一事实如实登记。
