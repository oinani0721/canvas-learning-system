# 阶段 2 收工测试出现 1 条新红 — W4 哨兵调查

## 事实（未加解释）

| 轮次 | 代码态 | 末行 | nodeid 数 | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` |
|---|---|---|---|---|
| run1 `unit-open-phase2-20260911T0850` | 纯净 merge 态（基线） | 36 failed, 5188 passed, 29 errors, 393.62s | 65 | **0** |
| run2 `unit-close-phase2-20260911T0900` | 基线 + 阶段 2 修改 | 37 failed, 5187 passed, 29 errors, 449.24s | 66 | **1** (blocked=1) |
| run3 `unit-control-run2-basecode-20260911T0905` | **回到基线代码**，但状态已被 run1/run2 累积 | 36 failed, 5188 passed, 29 errors, 333.73s | 65 | **0** |
| run4 `unit-run4-phase2code-20260911T0907` | 阶段 2 代码，第 4 轮 | （见该文件） | — | — |

差集（run1→run2）只有一条 `>`：
```
FAILED tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422
```

失败原因是 **W4 哨兵**：该用例期间有 1 次到现网 Neo4j(7691) 的连接尝试被拦下，哨兵把它转成用例失败
（否则连接异常会被 `app/main.py` lifespan 的 try/except 吞掉，门就什么都证明不了）。

调用链（从捕获日志读出，非推断）：
`accept_candidate` → `error_writer.graphiti_written` → `memory_service` 单例**惰性初始化** → `neo4j_client` 健康检查 → 连 7691 被拦 → 回落 JSON 模式。

## 为什么需要对照组 run3

run1 与 run2 之间**代码不是唯一变量**：
- `backend/data/` 会被测试写入（实测 mtime：`outbox/` = 08:45 即 run1 期间；`outbox/events.jsonl` = 08:53 即 run2 期间；`failed_writes.jsonl` = 08:55）。
- 两轮耗时差 14%（393s → 449s），机器负载不同（run2 期间本 session 另跑了对抗审查 agents）。

run3 = **同样的累积状态 + 基线代码**。若 run3 也出现该哨兵 ⇒ 归因于「跑第二轮 / 累积状态」，非本卡代码。

## ⚠️ 一个不成立的旁证（如实记录，不要引用）

曾想用「`MemoryService singleton initialized` 在两份存档里的出现次数（0 vs 2）」佐证，**该判据不成立**：
pytest 只为 **FAILED** 用例打印 captured stdout/log，所以 run1 计数为 0 只说明「没有失败用例带这段输出」，
**不等于**该初始化没发生。唯一可用的信号是进程级计数行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=`。

## 既有性佐证

同型哨兵失败在本项目并非首次：`_bmad-output/审查/evidence-b12-integ/dir-tests-unit-20260906T203713.txt:1454` 等处
（第十二批集成期）已记录多次 `live Neo4j port connect attempted`，归因是 unit 测试触及真实依赖的既有设计问题。

## 与本卡改动面的关系

本卡阶段 2 只改了 `api/v1/endpoints/review.py`、`api/v1/system.py`、`services/exam_service.py`（整文件 crossover）。
`candidate_service` / `error_writer` / `memory_service` / `neo4j_client` **均不在改动面内**，
且三处改动皆为类型层（注释/ignore/注解/关键字默认）或运行期不执行的 `if TYPE_CHECKING` 块。
`git --no-pager diff --no-color --stat -- . ':(exclude)_bmad-output'` 全程只列这 3 个文件。

## run3 结论：「累积状态」假说被证伪

run3 与 run2 处在**同样的累积状态**（`backend/data/` 已被 run1、run2 写过），但代码回到基线：

- `run1 → run3` nodeid 差集 **完全相同**（diff-rc=0，都是 65 条），`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`
- `run2 → run3` 差集只有那一条 `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`

⇒ 「跑第二轮 / `backend/data/` 累积状态」**不足以**解释 run2 的哨兵触发。

## 剩余两个候选解释 → run4

1. **代码**：但三处改动（`review.py` 注释+ignore+海象、`system.py` 注解+ignore+关键字默认、
   `exam_service.py` 整文件 crossover）**都不触及** `candidate_service` / `error_writer` / `memory_service` / `neo4j_client`；
   crossover 的副作用 import 行经核对只加了注释（`git show card/u1-pyright-svc:…` vs `git show :…` 实测），运行期不变。
   即：**找不到机制**。
2. **偶发 / 机器负载**：run2 是三轮里最慢的（449s vs 393s / 333s），且 run2 全程与本 session 的对抗审查 agents 并发
   （项目既有教训「⛔ 并发 agent 写入毒化变异基线」的同族现象）。

**run4 = 阶段 2 代码 + 再跑一轮**，用于分辨「可复现（⇒ 代码）」与「不可复现（⇒ 偶发）」。结论待 run4 落地后补。
