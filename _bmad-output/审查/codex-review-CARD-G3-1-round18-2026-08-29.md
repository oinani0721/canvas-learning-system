终裁：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

HEAD 确认为 `17b9191771091a401bd5d152d53b0c136e008044`。tracked/cached diff 均为零；审阅前已有的 untracked round18 草稿未读取、未修改。

## 1. 十七轮三条 HIGH 重放

| 输入 | 实测 | 裁定 |
|---|---|---|
| manifest `scheduler_config` 只含 `desired_retention` | 报“scheduler_config 残缺…fail-closed” | **CONFIRMED-CLOSED** |
| manifest 缺整个 `scheduler_config`，proof 六键全 0 | 同上 | **CONFIRMED-CLOSED** |
| manifest `scheduler_config="not-an-object"` | 同上 | **CONFIRMED-CLOSED** |
| L1=`t1`，L2=`t2>t1,out_of_order:true` | 主体 0 违规；proof 同时报“伪装成乱序后继”及“尾部 [2] 未覆盖” | **CONFIRMED-CLOSED** |
| L1=`t1`，L2=`t0<t1,out_of_order:true` | 主体 0 违规；proof `[]` | **CONFIRMED-CLOSED，无误拒** |
| 两行全缺事件 vault、无 config | 主体两行违规；proof 报“纯属自报” | **CONFIRMED-CLOSED**，但属于违反主体前置条件的纵深防御 |
| 第一行带 vault、第二行缺、无 config | 主体第二行违规；proof 报“仅 1/2…不可证” | **CONFIRMED-CLOSED**，同上 |
| proof `vault_id=[]` | 返回两条字符串类型违规，无异常 | **CONFIRMED-CLOSED** |

实现锚点：[manifest 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:832)、[`_manifest_config_usable`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:935)、[`out_of_order` 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:530)、[vault/type 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:695)。

## 2. NEW-FINDING / HIGH：真正乱序可隐藏另一 vault

无 `.canvas-config.yaml`，构造两条主体字段完整的记录：

```text
L1: node=n, vault_id=A, review_time=t2, 正常 review/1
L2: node=n, vault_id=B, review_time=t1<t2, out_of_order=true
proof: vault_id=A, cursor=L1, prefix 到 L1
```

实测：

```text
validate_file violations = []
warnings = [L1 vault未绑定, L2 vault未绑定]
scan.applicable = [L1]
scan.vault_ids = {'A'}
verify_degraded_proof = []
```

根因是确认真正乱序后在 [validator:552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:552) 提前 `continue`，早于 [vault 收集](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:564)。因此 L2 的 `vault=B` 完全不可见。

这不是违反前置条件的输入：主体是 PASS，仅有 WARN。它与十七轮 mixed-vault HIGH 同类，说明具体“全缺/部分缺”虽闭合，**vault proof 门整体仍是 STILL-OPEN**。schema 声称 scanner 抽取 vault 集合，[schema:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)，但实现悄悄缩成仅适用集。

## 3. proof 逐门更新

| proof 门 | 本轮结论 |
|---|---|
| 12 个顶层必填字段 | **CONFIRMED-CLOSED** |
| cursor/E/event_id/review_time/时间域 | **CONFIRMED-CLOSED** |
| node_id、链上身份 | **CONFIRMED-CLOSED** |
| vault_id 绑定 | **STILL-OPEN / HIGH**：上述 out-of-order × 跨-vault 绕过 |
| prefix 精确 bytes、LF | **CONFIRMED-CLOSED** |
| algorithm/version/hash/config | 当前实现 **CONFIRMED-CLOSED**；回归承重仍 PARTIAL |
| reducer 结构 | **CONFIRMED-CLOSED** |
| snapshot canonical hash、键集、类型、数值域 | **CONFIRMED-CLOSED** |
| snapshot 三等式 | **CONFIRMED-CLOSED** |
| 区间、层内/跨层单调 | **CONFIRMED-CLOSED** |
| 链终止、递减、防循环/深度 | 实现 **CONFIRMED-CLOSED**；递归共享测试 PARTIAL |
| genesis | **CONFIRMED-CLOSED** |
| top-level 尾部覆盖 | **CONFIRMED-CLOSED** |
| degraded 区间哨兵 | **CONFIRMED-CLOSED** |

对应主体入口在 [validate_file](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1496)；proof 目前没有仓内非测试调用方，是参考 verifier，不能冒充已接入生产。

## 4. 误拒与规范落文

真正更早及 `review_time == W` 的乱序事件，当前实现均通过；带真实 `.canvas-config.yaml`、完整合法事件的普通 proof 也返回 `[]`。现网主体校验没有受 proof 新门影响。

三处范围声明都确实列了六条：

- [schema §6.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:204)
- [模块注释](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:335)
- [函数 docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1102)

但它们**不是同文**：模块第③/④信息量不同，docstring 第⑤省略 scanner 字段清单。因此“六条”是 **CONFIRMED**，“三处同文/措辞一致”是 **STILL-OPEN / MEDIUM**。

主体校验前置条件已三处落文；PyYAML + golden manifest 强依赖也已落文，[schema:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:209)、[schema:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:211)。canonical JSON 类型冻结已在 [schema:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:212)。

另有注释漂移：[_check_proof_identity docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:832) 仍写 manifest 不可达时“降级形状校验”，实际已 fail-closed；[六键常量注释](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:390) 同样过期。

## 5. mutation 与 survivor

隔离副本中：

| 破坏 | 结果 |
|---|---|
| 禁用 manifest 残缺门 | 仅对应测试 `1F` |
| 禁用 out-of-order 语义门 | 伪后继 `1F`；真正更早用例仍 `1P` |
| 禁用“双锚全缺”门 | `[none] 1F`；`[partial] 1P`，后者由独立分支保护 |
| 禁用 vault 类型门 | 四个非字符串参数全部红 |
| 递归同时丢 scan/raw/vault | 仅递归行为门 `1F` |

但仍有四个 full-suite survivor，均保持 `155 passed, 1 skipped`：

- 从 `_SCHEDULER_CONFIG_KEYS` 删除 `parameters`：只缺该键的 manifest/proof 从 fail-closed 变成 `[]`。
- 把 [乱序比较 `>`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:547) 改成 `>=`：合法 `review_time == W` 被误拒。
- 禁用 [config mismatch 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:707)：对应锚无独立行为门。
- 递归只丢 `ledger_vault_id`，[validator:1028](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1028)：合法两层 proof 出现 ancestor 假阳性，仍全绿。

因此新增测试承重性只能判 **PARTIAL / MEDIUM**。

## 6. 负验证脚本

A–P 十六个 Perl 模式按脚本相同的 `s///g` 计数复算，**全部恰好命中 1 处**。

以下加固有效：[命中计数不可证即失败](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:43)、[检查 Perl rc](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:54)、[逐个 expected 名检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:91)、[中间 restore 检查 rc](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:34)。

仍是 **STILL-OPEN / MEDIUM**：

- 预期测试内 `1/0` 等运行时异常仍被 pytest 记作 `FAILED`、RC=1，脚本会误判为承重。
- 参数化测试只写基名时，一个参数红即可；O 实际就是 `[none]` 红、`[partial]` 绿。
- manifest 三形态在同一测试循环，首个断言失败后其余形态没有执行。
- [EXIT trap](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:29) 的 `cp` 仍不检查返回码，异常退出恢复保证不完整。

未执行会修改 tracked 文件的原脚本；mutation 仅在隔离临时副本进行。

## 7. 回归、账本与 G3-4

指定解释器实跑：

- contract：`155 passed, 1 skipped`
- contract + golden + 既有账本：`180 passed, 1 skipped`
- golden：其中 `19 passed`
- `test_learning_event_log.py`：其中 `6 passed`
- `test_fsrs_manager.py`：`37 passed`

现网 MAIN 账本：

- `23` 行，`review/1=0`、payload `vault_id=0`、`group_id=7`
- CLI：`RESULT: PASS`
- 前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`

G3-4：

- `a3ec2da1..HEAD` 对 generator/manifest/vectors 零 diff。
- `generate()` 内存 manifest/vectors 与仓库 JSON 均逐字节相同；20 vectors、3 retrievability points。
- 锁定 blob：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`

两份 UAT 与 CURRENT_TASK 的测试数字一致；[CURRENT_TASK:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5)“第十九笔已提交”和 [CURRENT_TASK:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:32)“下一步十八轮复核”时态正确。

仍有两条 LOW 文档漂移：[G3-1 UAT:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:40) 的无 baseline diff 描述过期；[UAT:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:336) 仍笼统写“现网带的是 group_id”，与同单后文声称已改成精确 `7/23` 矛盾。

## 残留清单

- **BLOCKER：0**
- **HIGH：1**
  - genuine `out_of_order` 行可隐藏另一 vault 的主体合规事件，vault proof 门仍可返回空。
- **MEDIUM：3**
  - 四个全绿 survivor，新增测试机械充分性不足。
  - 负验证仍可把运行时异常/单个参数实例误认作承重。
  - 六条语义已落，但“三处同文”不成立。
- **LOW：3**
  - EXIT trap 恢复返回码未检查。
  - proof identity/六键常量注释仍写旧的降级口径。
  - G3-1 UAT 两处历史措辞未同步。

最终：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

限制：本会话没有 `graphiti-canvas/search_memory_facts` 工具，因此未伪造 Graphiti 查询或记录；以上均为当前本地 checkout、公开校验入口及隔离 mutation 的复算结果，不冒充远端 CI。


