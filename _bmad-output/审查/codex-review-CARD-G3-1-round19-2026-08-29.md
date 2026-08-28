终裁：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

HEAD 确认为 `9d9858227abb1a20b281389d847a2a8c80aa4672`。tracked/cached diff 均为空；仅有审阅前已存在的未跟踪 round19 草稿，我未读取或修改。

## 1. 十八轮 HIGH

**CONFIRMED-CLOSED（针对 v1 合规账本）**

重放：

```text
L1: vault=a, review_time=t2，正常 review/1
L2: vault=b, review_time=t1<t2, out_of_order=true
proof: vault=a, cursor=L1
```

两行均为完整、主体合规事件。实测：

```text
validate_file.violations = []
scan.applicable = [L1]
scan.vault_ids = {'a', 'b'}
scan.review_ext_lines = [1, 2]
proof problems = ["vault_id 与账本事件不符 ... ['a', 'b']"]
```

实现确实在乱序 `continue` 前收集 vault：[validator:531](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:531)、[validator:540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:540)。

同一输入把 L2 改成 `vault=a`，以及令 `review_time == W`，主体均零违规，proof 均返回 `[]`。普通 v1 单-vault 合法输入没有被本次修法误拒。

**NEW-FINDING / MEDIUM：未知版本合法行被误当 v1 扫描**

配置 `vault=a`，L1 为合法 v1/vault=a；L2 为：

```json
{
  "event_id": "future:e2",
  "event_version": 2,
  "node_id": "n",
  "payload": {
    "schema_ext": "review/1",
    "vault_id": "b",
    "review_time": "t1",
    "out_of_order": true
  }
}
```

主体按前向兼容规则仅 WARN、零违规，但 scanner 得到 `vault_ids={'a','b'}`，导致 proof vault=a 被假阳性拒绝。

主体明确跳过未知版本：[validator:1549](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1549)；scanner 在解析后没有版本分流便收集 v1 字段：[validator:513](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:513)。这是合法输入误拒，不是安全绕过。

## 2. proof 门更新

| proof 门 | 结论 |
|---|---|
| 12 个顶层必填字段 | **CONFIRMED-CLOSED**，[validator:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:367) |
| cursor/E/event_id/review_time/时间域 | **CONFIRMED-CLOSED**，[validator:673](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:673) |
| node_id、链上身份 | **CONFIRMED-CLOSED** |
| vault_id 绑定 | 十八轮 v1 HIGH **CONFIRMED-CLOSED**；整体 **PARTIAL**，存在上述 v2 误拒 |
| prefix 精确 bytes、LF | **CONFIRMED-CLOSED**，[validator:685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:685) |
| algorithm/version/hash/config | 实现 **CONFIRMED-CLOSED**；回归承重 **STILL-OPEN**，见 manifest survivor |
| reducer 结构 | **CONFIRMED-CLOSED**；仅判结构，真实折叠仍属 G3-2 |
| snapshot canonical hash、键集、类型、数值域 | **CONFIRMED-CLOSED** |
| snapshot 三等式 | **CONFIRMED-CLOSED** |
| 区间、层内/跨层单调 | **CONFIRMED-CLOSED** |
| 链终止、递减、防循环/深度 | **CONFIRMED-CLOSED**；仅丢递归 `ledger_vault_id` 时专门测试唯一变红 |
| genesis | **CONFIRMED-CLOSED** |
| top-level 尾部覆盖 | **CONFIRMED-CLOSED** |
| degraded 区间哨兵 | **CONFIRMED-CLOSED** |

限制：`verify_degraded_proof()` 仍没有仓内非测试调用方；这些结论是参考 verifier 行为，不代表生产解冻链已经接入。

## 3. mutation 与测试有效性

| mutation | 结果 | 裁定 |
|---|---:|---|
| 忠实把 vault 收集移到真乱序 `continue` 后 | 仅 HIGH 测试与 exact-watermark 测试红 | 承重，但前者仍由 partial 门 fail-closed，并非危险放行 |
| `>` 改 `>=` | 仅 exact-watermark 红 | **CONFIRMED-CLOSED** |
| 禁用 config mismatch | 4 个相关 nodeid 红，无无关失败 | **CONFIRMED-CLOSED** |
| 递归仅丢 `ledger_vault_id` | 仅专门递归测试红 | **CONFIRMED-CLOSED** |
| 从 `_SCHEDULER_CONFIG_KEYS` 删除 `parameters` | `165 passed, 1 skipped` | **STILL-OPEN / MEDIUM** |
| `review_ext_lines/vault_id_lines` 完整退回旧 applicable 分子/分母 | `166 passed, 1 skipped` | **NEW-FINDING / MEDIUM** |
| 同文改一个字或标点 | 仅同文门红 | 承重 |
| ``ledger_path`` 改为 ``ledger_ path`` | 同文门仍绿 | **PARTIAL / MEDIUM** |

manifest 测试在 [contract:2091](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2091) 直接从被测常量生成参数。删掉生产常量的 `parameters` 后，该用例也从收集面消失；缺 `parameters` 的 manifest/proof 实测错误返回 `[]`。十八轮点名的原 survivor 实际未闭合。

此外，HIGH 与 equality 测试使用的 `_event()` 只构造 scanner 最小字段，不满足完整主体 §6.1；本次独立完整事件重放证明当前实现正确，但仓内门自身没有锁住“主体先 PASS”的前提。

## 4. 三处同文与负验证

三处六条当前经过正规化后相同：

- schema：[schema:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:204)
- 模块注释：[validator:335](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:335)
- docstring：[validator:1112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1112)

但正规化在 [contract:2147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2147) 删除所有空白，包括反引号代码内的空白。因此标点差异会红，一个字变化会红，但 ``ledger_path`` 与实质不同的 ``ledger_ path`` 被判相同。它不是可靠的“逐字同文”门。

负验证原脚本未执行；在 `/tmp` 等价副本中：

- A–T 二十个 Perl 模式均恰命中一处；
- 脚本 exit 0、最终 `166 passed + 1 skipped`、`cmp` 一致；
- O/T 的 `[none]`、`[partial]` 是完整参数 id。

仍为 **STILL-OPEN / MEDIUM**：

- G 只写参数 id 前缀，[脚本:189](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:189)；
- L 仍只写参数化基名，[脚本:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:224)；
- Q 实际删除全部 vault 收集，并非移到 `continue` 后，[脚本:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:257)。mutant 仍以“无证据”方式保守拒绝，只因测试期待另一诊断而被脚本算作承重。
- 运行时异常边界声明准确，但不完整：同一 nodeid 因另一条错误断言或替代 fail-closed 路径失败，也会被误算承重。

`cleanup()` 的恢复失败告警已落实，原 LOW 可判闭合。

## 5. 文档与现网账本

**NEW-FINDING / HIGH（外部现网完整性警报，归因不可证）**

主仓现网账本当前实测：

```text
22 records
review/1 = 0
payload.vault_id = 0
payload.group_id = 7
before SHA = 2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6
validator = PASS
after SHA  = 同上
```

但当前 HEAD 内的 SHA-bound 证据记录此前是 `23` 条、SHA `f78b99f307…`：[live evidence:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/g3-1-live-ledger-validation.txt:8)、[round18:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/codex-review-CARD-G3-1-round18-2026-08-29.md:127)。

当前文件的 birth/mtime/ctime 均为 `2026-08-29 06:11:47 +0800`，晚于 HEAD 提交约 58 秒，并精确回到早期 22 条快照的 SHA。D0 又明确冻结其为 append-only 唯一审计/幂等/重放来源：[D0:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/fsrs-truth-source-d0-revision.md:11)。

账本本身未纳入 Git，因此无法从 Git 确认缺失事件内容、责任方或恢复方法；这些均为 **UNVERIFIABLE**。validator PASS 只证明当前 22 条结构合法，不能证明历史连续性。

另有未修 LOW：

- scanner docstring 仍把 `vault_ids` 写成“适用事件”集合，[validator:488](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:488)；纯自报诊断也仍写“适用事件”，[validator:725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:725)。
- G3-1 UAT 的“23 条当前事件”、旧 diff 描述及笼统 group_id 说法仍失真：[UAT:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:8)、[UAT:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:40)、[UAT:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:336)。
- CURRENT_TASK 的“第二十笔已提交、待十九轮复核”时态正确；UAT 的“二十轮负验证”应是“二十变体/第二十笔”。

## 6. 回归与 G3-4

实跑：

- contract：`166 passed, 1 skipped`
- contract + golden + existing ledger：`191 passed, 1 skipped`
- golden：`19 passed`
- `test_fsrs_manager.py`：`37 passed`
- 其余 UAT 列出的 FSRS 族：`191 passed`

G3-4：

- `17b91917..HEAD` 对 generator/manifest/vectors 零改动；
- `generate()` 内存 manifest/vectors 与仓库 JSON 逐字节相同；
- 20 vectors、3 retrievability points；
- manifest SHA `82eaaffa…`，vectors SHA `df60dbc6…`；
- `learning_event_log.py` blob：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`；
- `fsrs_manager.py` blob：`980b3758758b1d78d6795451c76270c10713cc60`。

因此 **CARD-G3-4 没有回退，仍保持可验收**。

## 残留清单

- **BLOCKER：0**
- **HIGH：1**
  - MAIN 现网 append-only 账本从已存证的 23 条状态回到旧 22 条快照；原因与缺失内容不可证。
- **MEDIUM：5**
  - 未知 `event_version=2` 合法行被 proof scanner 当 v1 解释并误拒。
  - manifest 六键参数来自被测常量，原 survivor 仍全绿。
  - `review_ext_lines` 旧 applicable 口径完整回退仍全绿。
  - 三处同文正规化吞掉代码标识符内部空白。
  - 负验证的参数 id、Q mutation 语义及失败归因边界仍不可靠。
- **LOW：2**
  - scanner/docstring/诊断仍残留旧“适用事件”口径。
  - UAT/CURRENT_TASK 中 live 数字、历史 diff、group_id 与“二十轮”措辞漂移。

最终：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

限制：未执行原地负验证脚本；未验证远端 CI；当前会话没有 `graphiti-canvas`，未伪造 Graphiti 查询或记录。


