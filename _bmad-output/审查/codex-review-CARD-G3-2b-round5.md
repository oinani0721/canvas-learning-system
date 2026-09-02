结论：需整改

### 20 条规则逐条判断

以下行号与实跑结果锚定复核开始时的 `HEAD e2252a905875…`，`SKILL.md` blob=`314917efb6b0…`。

| 规则 | 结论 | 依据（file:line + 你实际跑出来的观测值） |
|---|---|---|
| 1 | PASS | `SKILL.md:734-745` 独立构造固定 candidate，durable 侧只排除两个环境键；对应 envelope 反例门在 39 项实跑中通过。 |
| 2 | FAIL | `SKILL.md:273-282,628-640` 的乱序分支仍先 `.strip()` 再提前 `continue`。带空白时刻实际为 validator `rc=1`、writer `rc=0`、账本增至 3 行。 |
| 3 | FAIL | `SKILL.md:711-733,824-851` 的期望值漏计 §6.3 历史行。实跑合法 `[review/1 E1, legacy L]`、attempts=`[1,2]`、validator `rc=0`，原样重跑 E1 却 `rc=1 envelope 冲突`。 |
| 4 | PASS | `SKILL.md:428-466,907-1048` 共用 durable 分数和时刻。A3 bump 后正常/恢复产物 SHA 同为 `5296e87039ec…`，`review_time=2026-12-01T10:00:01Z`。 |
| 5 | PARTIAL | 普通适用行在 `SKILL.md:647-661` 拒缺失、非法或不自洽评分；但乱序行在 `:628-640` 提前跳过，未经过这些门。 |
| 6 | PASS | 裁决已写入 `docs/learning-events-schema-v1.md:184-207`；对应文档门实跑通过。 |
| 7 | PASS | `SKILL.md:374-405` 以最后非空字节行为界。现有行为门观测：坏末行带 LF `rc=1`；去掉 LF 后作为截断隔离并可续写。 |
| 8 | PASS | `SKILL.md:628-640` 只接受 `out_of_order is True` 且时刻不晚于 W；未来行及 `false/"true"/1` 均在实跑门中拒绝。字面洗值另计规则 2/20。 |
| 9 | PARTIAL | 字节切行、逐行 UTF-8、截断多字节尾行均实现于 `SKILL.md:363-405`；但首行 BOM、非标准 JSON 的容忍与 validator 分叉。 |
| 10 | PASS | `SKILL.md:291-302,394-399` 拒重复键；重复 `grade_norm` 实跑 `rc=1`，节点无 FSRS 写入。 |
| 11 | FAIL（规则文字错误） | `SKILL.md:781-903` 会顺序恢复任意数量的纯 foreign pending。实跑两条时第一轮恢复、第二轮成功，最终 attempts=`[1,2,3]`。这符合 schema A2/A9；应改规则 11，不应据此改代码为“一概停下”。 |
| 12 | PASS | `TEST:1231-1292` 六格前置状态均经独立探针确认，逐格结果见下节；但这六格没有覆盖完整键别名和 §6.3 夹层。 |
| 13 | PASS | `SKILL.md:575-590` 对不可路由顶层或非字符串 `node_id` fail-closed；相关输入实跑均 `rc=1`。合法 foreign v2 的误拒另计规则 20。 |
| 14 | FAIL | `SKILL.md:783-856` 确实复放 mastery/time/calibration/attempt，但裸键碰撞会令 `_already_=True`，从而跳过其中三项。 |
| 15 | FAIL | `SKILL.md:817-829` 用校准记录避免 degraded 双吃的思路正确，但键不是完整 event_id，存在“标记为真、实际是另一个事件”的情况。 |
| 16 | FAIL | `SKILL.md:774-779` 同样按剥前缀后的键判定；别名事件可被误认已应用，实际复现出三条评分只计两次。 |
| 17 | PASS | 本次输入 eid 的首尾空白在 `SKILL.md:208-214` 原样拒绝，不做归一化；对应行为门通过。 |
| 18 | PASS | `SKILL.md:622-627` 在乱序分流前检查事件类型、concept、vault；篡改形态实跑均拒绝。 |
| 19 | PARTIAL | review marker 非法能在 `SKILL.md:591-610` 停下；但该门没有限定评分事件，会误伤合法 `session_archived + payload.vault_id`：validator `rc=0`、writer `rc=1`。 |
| 20 | FAIL | 完整校验在 `SKILL.md:653-661`，位置太晚且未传 golden manifest，也不覆盖 strict JSON 和新构造记录。实跑至少有：乱序空白、控制字符包裹、合法 identity 形状但错误真值三类 writer `rc=0` / validator `rc=1`；另有合法 foreign v2 和合法非评分行 writer `rc=1` / validator `rc=0`。 |

### 六种状态

| 状态 | 结论 | 实际前置与结果 |
|---|---|---|
| `dup=无, F1=假` | PASS | `W=None`、只有 foreign pending。第一轮 `rc=1` 恢复并保留 payload；第二轮 `rc=0`，账本 2 行，W=`2026-08-02T10:00:00Z`。 |
| `dup=无, F1=真` | PASS | 前次 cell 留下校准/W，但删除本次账本行。`rc=0` 命中“旧写序”，节点 SHA 和账本行数不变。 |
| `dup=有, F1=真, applied=真` | PASS | 完整成功后重跑，`rc=0` 幂等跳过，节点 SHA 不变，账本仍 1 行。 |
| `dup=有, F1=假, applied=真` | PASS | 只删除 calibration，FSRS 仍在。`rc=1` 要求人工核对，节点零写。 |
| `dup=有, F1=真, applied=假` | PASS | degraded 已写 EMA/attempt/calibration、无 W。恢复 `rc=0`，只补 FSRS，四个 EMA/attempt 行逐字不变。 |
| `dup=有, F1=假, applied=假` | PASS | 崩溃窗口①。恢复 `rc=0`，节点与直接路径逐字节相同，账本仍 1 行。 |

六格没有承担核心结论的恒真断言，但测试强度有两个缺口：

- `TEST:1247,1256,1264` 所谓“零写”只比较节点 SHA 和账本行数，没有比较账本内容哈希。
- 六格前置三元组只写在注释里，没有显式断言；格 5 也未直接断言 calibration 条目没有重复。

### 问题清单

[BLOCKER] `canvas-vault/.claude/skills/quiz-answer/SKILL.md:420,523-535,777-829` — 校准记录仍存/查裸 eid，两个不同的完整 event_id 会别名并漏算一次评分。  
依据: 预置 schema 合法的 `event_id="same-key-q1"`，validator `rc=0`；settled 写 B 后，再提交本地事件 `quiz:same-key-q1`。writer `rc=0` 却报“已完整应用、旧写序”，最终账本只有 `["same-key-q1","quiz:B-q1"]`、attempts=`[1,2]`，第三次评分没有入账。validator 前后均 `rc=0`。  
建议: calibration 一律存、查完整 ledger event_id；正常路径应存 `evid`，foreign 路径原样存 `record["event_id"]`。旧裸键兼容必须先证明映射唯一，存在 `K`/`quiz:K` 歧义时停下。

[HIGH] `SKILL.md:591-611,711-733` — 序数回推漏计规格永久允许的 §6.3 历史评分行，误拒合法 duplicate。  
依据: 用生产入口成功写 E1、L，再仅把 L payload 转成合法历史形态；validator `rc=0`、账本 attempts=`[1,2]`、笔记 attempt=2。原样重跑 E1 得 `rc=1 envelope 冲突`，节点 SHA 不变。  
建议: 序数边界必须计入所有会推进 attempt 的同节点历史评分行；若账本历史不足以证明，则不要伪造期望值，改为明确的不可证分支并补 legacy 夹层回归测试。

[HIGH] `SKILL.md:273-282,628-640,653-671` — `out_of_order` 分支在完整校验前退出，字面坏值仍能被洗过并放行。  
依据: 先建立 W，再追加 `out_of_order=true`、`review_time/effective_at=' 2026-07-01T10:00:00Z '`。validator `rc=1`；writer 写下一评分却 `rc=0`、节点改变、账本由 2 行增到 3 行。  
建议: 本节点所有 `review/1` 行先调用完整 validator，再做乱序语义分流；`_durable_instant` 不得 `.strip()`。

[HIGH] `SKILL.md:228,659` — 调用 `validate_record_full()` 时未传 golden manifest，实际没有执行算法身份真值绑定。  
依据: `fsrs_library_version="999.999"`、hash 为 64 个零时 validator CLI `rc=1`，writer settled `rc=0` 并追加第二行，之后 validator 仍 `rc=1`。  
建议: 导入并传入 `_golden_manifest()`；manifest 真正不可达时才按规格降级为形状检查和 WARN。

[HIGH] `SKILL.md:374-405` — 账本解析不是 validator 的 strict JSON 口径。  
依据: 用 U+000C 包裹一条完整 JSON 行，validator `rc=1`；writer 因 `_line.strip()` 洗掉控制字符而 settled `rc=0`，并生成第二条事件。默认 `json.loads` 还接受 `NaN/Infinity`，而 `VALIDATOR:124-127` 明确拒绝。  
建议: 复用 strict loader；保留“仅最后坏行且无 LF”截断分支，但不要把非标准常量、控制字符或完整坏行当截断。

[HIGH] `fsrs_bridge.py:69-80`、`SKILL.md:955-1015` — 新构造记录没有在 durable append 前自校验，bridge 仍会洗当前输入时刻。  
依据: `ts=' 2026-08-01T10:00:00Z '` 时 writer `rc=0`，事件的 `recorded_at` 原样含空白；紧接着 validator `rc=1`。  
建议: 在调用 bridge 前按规格字面校验输入，并在 append 前对最终 `rec` 调与 CLI 同口径的完整校验。

[MEDIUM] `SKILL.md:577-610` — 路由顺序与 marker 检查过度收紧，误拒合法非目标记录。  
依据: 合法 foreign v2 `{event_version:2,node_id:"other",payload:[]}` 为 validator `rc=0`、writer `rc=1`；合法同节点 `session_archived + payload.vault_id` 同样是 validator `rc=0`、writer `rc=1`。  
建议: 先验证跨版本路由信封，再立即跳过 foreign；`_looks_like_review_ext()` 只对两种评分事件生效。

[MEDIUM] `SKILL.md:868-876` — current pending 与 foreign pending 共存时，错误提示给出的“分别重跑白板”路径不会收敛。  
依据: 跑 A 得 `rc=1 同处待恢复队列`；改跑 B 得 `rc=1 存在一个更早 pending`；再跑 A 仍相同，节点与账本哈希全程不变。只有第三个非 pending 事件或人工恢复才能推进。  
建议: 提供独立 recovery-only 路径，或把提示改成真实可执行的人工处置步骤；不要声称重跑任一涉事白板即可恢复。

[LOW] `SKILL.md:618-671`、`SCHEMA:195-201` — 8 处等价重复检查本身不是 exactly-once 缺陷，但当前顺序和 A8 措辞不一致。  
依据: `_instant_only().strip()` 对普通适用行确实不可达：完整 validator 会先拒空白；真正漏网的是更早的乱序分支。`TEST:2258-2263` 也承认删除手写门的变异会存活。  
建议: 保留 A8 的“先 validator”不变，把重复检查删除或改成校验后的 assertion。若产品明确要求纵深重复检查，再把措辞改成“等价复核及更严检查”，但不能用改措辞掩盖提前 `continue`。

### 测试复核

按精确五文件口径实跑：

```text
269 collected
268 passed
1 skipped
10 warnings
exit 0
45.07s
```

单独行为文件：

```text
39 collected
39 passed
10 warnings
exit 0
41.82s
```

与自报数字一致。唯一 skip 是 `test_learning_events_schema_contract.py:1100-1107`：worktree 中没有 live `learning_events.jsonl`。

但绿色测试没有覆盖：

- 完整 ID `K` 与 `quiz:K` 的别名；
- `review/1 → §6.3 legacy → review/1` 的序数组合；
- out-of-order 在 validator 前提前退出；
- golden manifest 真值形状合法但内容错误；
- strict JSON 控制字符/NaN 与新记录 `recorded_at` 字面口径；
- current+foreign 两 pending 按错误提示重跑能否收敛。

### 验证限制

- 被复核快照：`HEAD e2252a905875f7dab525db520e5ad65607de420d`，原始 `SKILL.md` blob=`314917efb6b0…`、测试 blob=`eb180dca84ee…`。
- 审计中途有未知外部进程反复修改 `SKILL.md`、测试及 `g32b_mutation_gates.py`；本复核没有写工作树，也没有运行 mutation gates。后出现的未提交脏态不计入上述测试或结论，不能据此宣称已修复。
- 临时 fixture 仅写入 `/tmp/codex-g32b-r3-pytest/`；没有访问 live vault、数据库、网络或凭据。
- 未做真实掉电实验；fsync 顺序仅由代码与行为 spy 验证。
- 当前环境没有可用的 Graphiti 连接器，因此未执行项目约定的 Graphiti 查询。
- 按要求未把并发锁缺失列为问题；所有 BLOCKER 反例均在单进程串行条件下成立。

VERDICT: 需整改


