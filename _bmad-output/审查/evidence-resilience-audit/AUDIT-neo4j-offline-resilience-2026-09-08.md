# 架构审计 — 「Neo4j 离线时数据不丢」这一能力的完整性

> 日期 2026-09-08 · 树 `card-u11-red-c` @ `5139428d` · 全程只读（未跑测试、未启服务、未连 7691/7687）
> 起因：CARD-RED-C1（U11-A）把两条测试判为「数据面回归」移交 U5-C，项目负责人要求独立裁定该判断。
> **本审计发生在 U11-A 的两轮 Codex 代码复核之后，不属于那两轮，也不改变其结论（代码树未动）。**

---

## §0 ⚠️ 先读这一节：本审计做到了什么、没做到什么

| 环节 | 计划 | 实际 |
|---|---|---|
| 视角 A `writers`（穷举写侧） | 独立追踪 | ❌ **未跑成**（配额：`session limit · resets 10:50 Asia/Shanghai`） |
| 视角 B `replayers`（穷举重放侧） | 独立追踪 | ✅ 完成（16 路径 / 9 缺口） |
| 视角 C `replacement`（替代者本体） | 独立追踪 | ✅ 完成（20 路径 / 11 缺口） |
| 视角 D `startup`（启动期恢复动作） | 独立追踪 | ✅ 完成（23 路径 / 9 缺口） |
| 对抗性反驳（每视角 ×2，共 8 个） | 主动推翻各视角结论 | ❌ **两次补跑均未成**（先 session 配额、后 **weekly 配额**，重置 Sep 9 19:00 Asia/Shanghai） |
| 合并裁定 | 汇总 + 标注争议 | ❌ **未跑成**（同上） |
| 本 session 复验 | 抽验最高严重度条目 | ✅ 完成（4 条，见 §2） |
| 视角 C/D 重测 | （非计划，意外获得） | ✅ 11:1x 补跑时缓存未命中、真跑第二遍 ⇒ 获得**重测信度**观察（见 §0.1） |

### ⛔ 一个必须写明的判据陷阱

workflow 的返回摘要里每个视角都是 `refutedCount: 0`。**这不表示「经反驳未被推翻」，而表示「反驳轮根本没跑」** —— 8 个反驳 agent 全部因配额失败，计数器自然是 0。

若不写明，后人读到 `refutedCount: 0` 会以为这些结论已通过对抗性检验。**它们没有。**
这正是同日写入 `reference_gate_design_pitfalls`（第八个陷阱）的形态：**空输出流进下游比较器，被一个看起来正常的绿色结果掩盖**。

⇒ **本文件全部结论的强度 = 「三个独立视角收敛 + 本 session 抽验四条最要命的」，不含对抗性验证。**

### §0.1 重测信度（2026-09-08 第二次补跑意外获得）

补跑未命中缓存，`replacement` 与 `startup` 两视角**真跑了第二遍**（缺口数 11→12 / 9→8）：

- **语义层高度稳定**：两轮各自独立命中同一批核心主张（队列纯内存 / 死信无重放 / 死信默认无正文 /
  failed_writes 写活读死 / 告警被删 / 先删后确认），审计 §1 的结论在两轮里都成立。
- **条目层零重叠（措辞级）**：两轮的缺口清单措辞完全不同、数量有出入 ⇒
  **任何一轮的条目清单都是采样不是普查**，应视为缺口集合的**下界**。
  （第 3 跑 startup 还给出一条第 2 跑没有的事实，已吸收进 §1.1 的修正。）
- 这进一步支持本审计的定位：**方向可信、清单不穷尽**——正是「没有对抗性验证」时应有的表述。

---

## §1 三视角收敛的核心结论

三个视角各自独立追踪、互不可见，在下面这几条上收敛：

### 1.1 存在「有人写、没人读」的暂存面 —— 不止一处

| 暂存面 | 写侧 | 重放侧 |
|---|---|---|
| `backend/data/failed_writes.jsonl` | **活**（2 个生产写入方） | **零个在跑** |
| `backend/app/data/canvas_events_fallback.json` | **默认态停**（6 个写点全被 `ENABLE_GRAPHITI_JSON_DUAL_WRITE` 门住，`canvas_service.py:267/:360/:440/:457/:986/:995`；默认 False ⇒ 不写）| orphaned ⇒ **双向断裂**（第 3 跑 startup 视角修正；初版误写「活」） |
| `backend/data/learning_memories.json` | 活 | orphaned |
| `backend/data/neo4j_memory.json` | 活（`neo4j_client.py:55/:422/:476`） | **从来就不在任何重放器的覆盖面内** |

三个重放器都挂在 `FallbackSyncService` 上，而它自 `59586af1` 起零生产调用方。

### 1.2 比 1.1 更靠前的一层：最典型场景**连暂存都没有**

视角 B / C 一致指出：**Neo4j 在启动期离线**时，学习事件（`record_learning_event` / `record_batch_learning_events` / `record_canvas_temporal_event`）**零暂存、零死信**，只落一行 `logger.debug` 后丢弃。

代码可达路径（视角 B 给出）：`initialize_graphiti` 返 False → `main.py:286` 走 else → 不调 `start()` → `is_ready` 为 False → `_enqueue_episode` 提前 return。

⚠️ 视角 B 自己声明：这是**代码可达路径**的证明，**不是运行期观测** —— 它没拿到一条真实日志里 `Episode worker not ready, skipping enqueue` 的出现记录。（该视角主动引用了本项目记忆 `reference_code_mechanism_vs_observed_failure`：代码**能**那样失败 ≠ 它**就是**那样失败的。）

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

### 判断二：`ENABLE_GRAPHITI_JSON_DUAL_WRITE` 翻成 `False` 的前提 —— **不成立；但把它打回 True 也不是修复**

- 翻转理由「已被 GraphitiEpisodeWorker 取代」**不成立**：worker 对 `failed_writes` / `outbox` 零引用，未接管任何一个暂存面（§1.1 / §1.3）。
- **但**打回 `True` 同样不解决问题：dual-write 写的是 `learning_memories.json`，而**它的重放器也在同一个零调用方的 `FallbackSyncService` 上**。开关打开只会往另一本没人读的记事本里多写一份。
- ⇒ **这个开关不是修复点。** U11-A 把 3 条测试翻成断言 `default is False` 是对的（它们锁住的是「当前默认关闭」这一**事实**，而该事实为真，且已由内存态变异验证承重 KILLED 3/3）。错的是当初翻转它时给出的**理由**，不是测试。

---

## §5 建议（给项目负责人）

**排卡，但第一张卡的内容是「量」不是「修」。**

理由：§3 表明「有多少真实数据在丢」目前**没有证据**——现有那本记事本里全是测试残留。先量清楚，才知道是「历史上漏过几条」还是「一直在漏」，两者的处置优先级差很远。

⛔ **不要直接把恢复功能挂回启动流程** —— §2.1 表明那样会引入一条新的数据丢失路径（先删持久记录、再靠内存队列）。

建议的卡序：
1. **量** — 现网各暂存面的真实条数、时间分布、是否涉及在用学习数据（只读，不改代码）
2. **止血**（若 1 证明确有损失）— 先修 §2.1 的先删后确认顺序，再谈恢复调用
3. **补告警** — §1.4 删掉的那条警告应以某种形式回来，否则下次仍然无人知晓

---

## §6 证据文件

| 文件 | 内容 |
|---|---|
| `raw-lens-results.json` | 三视角完整结构化输出（paths / gaps / uncertain 原样） |
| 本文件 | 汇总裁定 + 本 session 复验 |
| `../evidence-red-c1/c1-verdicts.md` §2 | U11-A 原始 8 条移交证据（本审计复现了全部） |

workflow 运行记录：`wf_69753b68-0aa`，共三次：
1. 首发：5 agent 全败于鉴权抖动（403）；
2. 重跑：11 agent 中 3 成功（replayers / replacement / startup）8 败于 session 配额；
3. 补跑（配额重置后）：9 agent 中 2 成功（replacement / startup 第二遍，见 §0.1）7 败于 **weekly 配额**（重置 Sep 9 19:00 Asia/Shanghai）。
journal 共 5 份结构化 result，全部导出于 `raw-lens-results.json`（该文件为第 2 跑的 3 份；第 3 跑两份见 journal 或本文件 §0.1）。
补跑命令（Sep 9 19:00 后可用）：`Workflow({scriptPath: '…/resilience-gap-audit-wf_69753b68-0aa.js', resumeFromRunId: 'wf_69753b68-0aa'})`。
