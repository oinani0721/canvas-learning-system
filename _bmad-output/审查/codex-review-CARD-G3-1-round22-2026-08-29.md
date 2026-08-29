结论先行：**CARD-G3-1 需再一轮**。二十一轮的两个 MEDIUM 在“当前实现行为”上已闭合，但本轮新门仍存在 2 组可全绿逃逸的 MEDIUM 级测试/负验证缺口。**CARD-G3-4 仍保持可验收**。

审阅终态：HEAD 精确为 `eb329149624b081f5462694e0a8f919c7def0a74`；无 tracked 改动，仅保留审阅开始前已有的 untracked round22 审查稿。未执行会原地修改文件的负验证脚本；mutation 均在进程内或 `/tmp` 隔离副本完成。live 与 backup 前后哈希未变。

## 1. 二十一轮两个 MEDIUM

### CONFIRMED-CLOSED — 主体入口执行信封义务

实现位于 [validate_learning_events.py:1591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1591)，未知整数版本仅跳过 v1 形状，随后在 1611–1620 独立检查 `event_id` 与 `node_id`。

实测真实 `main()`：

```json
{"event_id":"future:missing-node","event_version":2,"payload_v2":{}}
```

→ exit 1，唯一 FAIL 点名 `node_id`。

```json
{"event_version":2,"node_id":"n","payload_v2":{}}
```

→ exit 1，唯一 FAIL 点名 `event_id`。

门位于 [test_learning_events_schema_contract.py:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:238)。分别删除两个判定时，各自恰好只有对应参数实例变红；整个循环删除时恰好两红。

### CONFIRMED-CLOSED — 前向兼容当前行为未被破坏

正向门位于 [test_learning_events_schema_contract.py:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:204) 和 [同文件:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:219)。

以下合法形状均 exit 0、仅 WARN：

- 最小三键信封，`event_id="x"`、`node_id=""`；
- 删除全部 v1 非信封字段；
- 新增任意字段，`payload_v2` 为数组、null 或不存在；
- 改造 `event_type/recorded_at/effective_at/payload` 类型；
- `event_version=3`、`999` 等任意未知整数版本。

### CONFIRMED-CLOSED（窄义）/ NEW-FINDING — MEDIUM（完整归因）

精确 Q mutation 确实只把 vault 收集块从 `continue` 前搬到后。新增 scanner 门 [test_learning_events_schema_contract.py:2100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2100) 在 Q 下首先红于 2112：

- `vault_ids` 从 `{"a","b"}` 退化为 `{"a"}`；
- `vault_id_lines` 从 `{1,2}` 退化为 `{1}`。

所以精确 Q 的直接因果已落到收集次序上。

但完整 182 项在 Q 下实际有 **3 红**，脚本只筛入/期望 2 红：

1. `test_genuine_out_of_order_cannot_hide_another_vault`
2. `test_scanner_collects_vault_from_out_of_order_rows`
3. [test_out_of_order_at_exactly_watermark_is_not_misrejected:2117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2117)

脚本 [negverify_round14_proof_gates.sh:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:268) 的 `-k` 隐藏了第三红项。因此“完整契约恰好只有 expected 红”仍不成立。

此外，该“纯 scanner 门”实际有第三条 `applicable == [1]` 断言（2114），并非文档声称的只断言两项收集事实；其“失败只可能因收集次序”表述过强。

## 2. 误伤面

### CONFIRMED-CLOSED — 当前实现未发现合法输入误拒

- live：22 行、7232 bytes、SHA-256  
  `2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6`，CLI exit 0。
- backup：23 行、7492 bytes、SHA-256  
  `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`，CLI exit 0。
- 两者运行前后哈希一致。

### NEW-FINDING — MEDIUM：误拒方向未被测试锁死

将任意未知版本判定从 `version != 1` 错误收窄为 `version == 2` 后，完整契约仍为 **181 passed + 1 skipped**。此时合法输入：

```json
{"event_id":"future:3","event_version":3,"node_id":"n","payload_v3":[]}
```

会被错误按 v1 校验并拒绝。所有现有前向兼容门只用了 v2。

另将非空 `event_id` 错误收窄为长度大于 1 后，合法 `event_id:"x"` 也会被误拒，而完整契约仍全绿。

## 3. 二十一轮七组 LOW

1. **CONFIRMED-CLOSED — 三处六条当前逐字同文。**  
   独立提取，仅去载体前缀和物理折行，未复用测试正规化函数。三份逻辑文本 SHA-256 均为：

   `f46e8f695bd5ed65af0ae17dd215fc965cd2f9511d15076e6e1a378a3ef9fe2e`

   锚点：[模块 335–349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:335)、[docstring 1151–1164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1151)、[schema 207–214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:207)。新增说明在 353、1168、216，均明确处于六条区间外。

   **NEW-FINDING — LOW：**同文门 [contract:2233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2233) 不覆盖区间外的新说明；删除或改写说明仍全绿。

2. **STILL-OPEN — LOW：测试仍使用主体不合规基线。**  
   `_event()` 位于 [contract:1584](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1584)，其 `review/1` payload 缺 `rating/concept_id/grade_norm/fsrs_library_version/fsrs_params_hash`。路由门 2314 与非字符串门 2361 仍复用它；2315 还把缺信封键的 v2 称作“合法 v2”。

3. **STILL-OPEN — LOW：schema 成文门仍过弱。**  
   [contract:2353](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2353) 只检查后续 400 字符内出现三个键名。反转“必须保留”为“可删除/改名”并删除优先级语义后，四项断言仍全过。

4. **PARTIAL / STILL-OPEN — LOW：非字符串与诊断组。**  
   五形态 `123/null/array/object/true` 当前均正确不可路由；删除判定时五实例全红。但遗漏 JSON float：让 [validator:539](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:539) 错误接受 float 后，`node_id:1.5` 被漏过且完整契约仍全绿。  
   [validator:764](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:764) 的无证据诊断当前正确，但 [contract:2008](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2008) 未锁其精确事实措辞。

5. **STILL-OPEN — LOW：`COLLECTED` 仍漏计。**  
   [脚本:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:82) 只统计 passed/failed/deselected；`181 passed + 1 skipped` 会报 181 而非 182，也漏 xfailed/xpassed/error。

6. **STILL-OPEN — LOW：UAT/CURRENT 数字漂移。**  
   [G3-1 UAT:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:8) 和 36 仍称当前 23 行，实为 22；[UAT:475](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:475) 与 [CURRENT_TASK.md:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:19) 写提交数 22，实算 `37387a86..HEAD` 为 **23**。测试数字和送审前时态则一致。

7. **STILL-OPEN — LOW：备份持久性边界未披露。**  
   22 行 live 确为 23 行 backup 的字节前缀，清理授权/探针定性有外部存证；但 live 与 backup 均为 untracked，本单仍把它表述为“完整恢复、非阻塞”，未说明仅当前本机可恢复、没有版本化持久保证。

## 4–6. Survivor、测试有效性与负验证脚本

### NEW-FINDING — MEDIUM：主体 value-shape 可退化且全绿

把 1612–1613 错误弱化为“键存在即可”，完整契约仍为 **181 passed + 1 skipped**。以下输入会从当前正确拒绝退化为零违规：

```json
{"event_id":"","event_version":2,"node_id":"n","payload_v2":{}}
{"event_id":123,"event_version":2,"node_id":"n","payload_v2":{}}
{"event_id":"future:x","event_version":2,"node_id":1.5,"payload_v2":{}}
```

新增主门只锁“缺键”，没有锁非空字符串/字符串形状。

### mutation 红集

- 删除 `event_id` 判定：对应参数恰 1 红。
- 删除 `node_id` 判定：对应参数恰 1 红。
- 删除整个主体循环：恰 2 红。
- 精确 Q：完整套件 3 红，不是脚本声称的 2 红。
- 删除 scanner 非字符串收集：实际 6 红，即旧语义门 + 五个参数实例。
- 接受 float、presence-only 信封、仅识别 v2、拒绝单字符 event ID：各自完整契约全绿。

新增断言没有恒真式，scanner/node 期望值是测试内常量，不来自被测实现。但存在断言面过窄、额外断言与文档不符、以及不合法 fixture 污染基线等问题。

### 负验证脚本

- 静态复核与 `/tmp` 隔离副本均确认：23 变体、Q 两步，共 24 次文本替换，每次模式恰命中源码一处；副本最终逐字恢复、脚本 PASS。
- 未运行会修改 tracked 文件的仓内脚本。
- Q 的 expected/filter 隐藏第三红项。
- U 在 [脚本:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:297) 只写参数化基名；[expect_red:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:109) 只要求任一实例匹配，不能机械证明五实例全部红。
- 其余变体在各自 `-k` 选择集内归因与当前存证一致。

## 7. 文档诚实性

- **STILL-OPEN：**G3-1 的 live 行数、提交数错误；“纯 scanner 门只断言收集事实”的描述与实际第三断言不符。
- **CONFIRMED：**第二处“门抓住自己人”有 [counterexamples:90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/g3-round22-counterexamples.txt:90) 及 109–115 的六红/五额外失败记录，且当前 U mutation 可复现。
- **无法独立确认：**第一处“同文门当场抓住插错位置”没有中间运行日志或对象；只能证明门现在会抓该类漂移，不能证明历史事件确实当场发生。
- [G3-4 UAT:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:25) 的 19、191 与当前实测一致。

## 8. 回归与 G3-4

| 范围 | 实测 |
|---|---:|
| G3-1 契约 | 181 passed + 1 skipped |
| 契约 + golden + 既有账本 | 206 passed + 1 skipped |
| golden + `test_fsrs_manager.py` | 56 passed |
| FSRS 全族 11 文件 | 191 passed |

`9a71eb8c..HEAD` 的 generator/manifest/vectors 零改动：

- generator blob `9d6ab4f63b326dc3f604cb794ce9fd9e42de792e`
- manifest blob `b59f331d9a1f57e5778fd82399ef12b61eb0c967`
- vectors blob `33c601995d5274f7702a4d0ce501d2b81311d688`

锁定 blob 精确匹配：

- `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`

## 残留清单与裁定

- BLOCKER：0
- HIGH：0
- MEDIUM：2 组
  1. Q/U 负验证 expected 集合不能证明完整、精确红集。
  2. 主体信封 value-shape、任意未知整数版本及合法最短边界仍有完整套件全绿 survivor。
- LOW：8 组
  1. 区间外新增说明未受门保护。
  2. 路由测试复用主体不合规 fixture。
  3. schema 成文门过弱。
  4. float `node_id` 与诊断措辞未锁。
  5. `COLLECTED` 漏计。
  6. UAT/CURRENT 数字漂移。
  7. backup 持久性边界未披露。
  8. “纯 scanner/门抓自己人”部分叙述超出可证明证据。

最终裁定：

- **CARD-G3-1：需再一轮**
- **CARD-G3-4：仍保持可验收**


