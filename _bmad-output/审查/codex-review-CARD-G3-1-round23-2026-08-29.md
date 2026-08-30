# CARD-G3-1 第二十三轮规范符合性复核报告

## 结论

- **CARD-G3-1：可验收。** BLOCKER 0、HIGH 0。残留 2 组 MEDIUM、8 组 LOW；按本批停轮规则登记结案，不再开轮。
- **CARD-G3-4：可验收。** 锁定 blob、generator、manifest、vectors 均未漂移，目标测试全绿。
- 十九轮账本 HIGH：**CONFIRMED-CLOSED**。缺失内容和唯一删除行均已可证，并结合用户本轮明确确认，足以认定为已授权探针清理。

当前 HEAD 精确为 `9014f313e106df6fd4dce0b7231490c01a1ef515`。`validate_learning_events.py` 在父提交、本提交及 HEAD 的 blob 均为 `4e1ee585…`，确认本 commit **零改动**。测试文件确为 `+62` 行。

## 1. 九形态参数化：承重，但存在有意重叠

参数及断言位于 [contract.py:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:238)，实现判定位于 [validator.py:1591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1591) 和 [validator.py:1611](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1611)。

以未修改源码的内存 mutation 跑完整 195 项契约：

| mutation | 完整套件结果 | 精确红集 |
|---|---:|---|
| 删除整个信封循环 | 9 failed, 185 passed, 1 skipped | 九实例全部红 |
| event/node 同时 presence-only | 5 failed, 189 passed, 1 skipped | 5 个 value-shape |
| 仅 event_id presence-only | 2 failed, 192 passed, 1 skipped | 空串、整数 |
| 仅 node_id presence-only | 3 failed, 191 passed, 1 skipped | float、null、bool |
| 未知版本只识别 v2 | 2 failed, 192 passed, 1 skipped | 99、-1 |
| scanner 错误接受 float | 2 failed, 192 passed, 1 skipped | 1.5、0.0 |

裁决：

- 九实例没有恒真式，删除实现门时确实 9/9 红。
- 空串与整数 `event_id` 共享 event-id 形状谓词；float/null/bool 共享 node-id 类型谓词。
- 99/-1 共享“任意未知整数版本”谓词，但分别覆盖正、负整数范围。
- main validator 的 float 形态和 proof scanner 的 float 门目标是不同入口，不算无效重复。

## 2. 误拒反面门：双向成立，两个形态已有旧门重叠

新门位于 [contract.py:2382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2382)。

- `event_id` 错误收窄为长度大于 1：单字符实例红，完整套件 `1 failed`。
- `node_id` 错误要求非空：空串实例红；旧门 `test_unknown_event_version_warns_not_fails` 也红。
- 未知版本错误禁止信封外顶层字段：新增字段实例红；旧的前向兼容门同样会红。

若删除整个新反面门：

- 单字符 `event_id` 方向没有其他门，`len > 1` survivor 会重新全绿。
- 空串 `node_id` 仍由 [contract.py:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:204) 保护。
- 新增字段/新 payload 形状仍由 [contract.py:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:219) 保护。

因此该门真正补上的独占面是单字符 `event_id`；另两形态属于合理的重复防线。

## 3. MEDIUM：`expect_red` 逐实例整改实际未生效

实例计数来自另一次完整文件收集，而非 mutation pytest 的同一次 `-k` 选择集：[脚本:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:118)。

当前 [pytest.ini:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/pytest.ini:19) 固定 `-v`，所以 `--collect-only -q` 输出：

```text
<Function test_main_validator_enforces_routing_envelope[...]>
```

不包含脚本 grep 的 `::test_name`。原样复算：

```text
test_main_validator_enforces_routing_envelope = 0
test_non_string_node_id_is_unroutable       = 0
test_float_node_id_is_unroutable            = 0
```

而 [脚本:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:124) 只在 `want > 0` 时比较，故 `0` 直接空真放行；第二次 collect-only 的退出码和 stderr 也未检查。

另一个绕过是变体 W 在 [脚本:327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:327) 使用含 `[` 的宽 regex，按第 119 行逻辑会直接跳过实例计数，仅 2/9 实例红也可满足当前判据。

这属于验证工装归因不完整；当前 9 个契约实例经独立 mutation 已确认承重，因此定为 **MEDIUM，不升 HIGH**。

## 4. MEDIUM：变体 Q 完整套件仍是三红

**车道更正不成立。**

按 [脚本:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:278) 的两个精确 Q 替换做内存注入，完整 195 项结果：

```text
3 failed, 191 passed, 1 skipped
```

三个红项是：

1. `test_genuine_out_of_order_cannot_hide_another_vault`
2. `test_scanner_collects_vault_from_out_of_order_rows`
3. `test_out_of_order_at_exactly_watermark_is_not_misrejected`

覆盖率门 [contract.py:2290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2290) 确实不红，因为它的乱序行原本就不带 `vault_id`。第三红实际是等水位线门 [contract.py:2128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2128)：Q 令第二行在收集 vault 前 `continue`，从而产生 `1/2` 覆盖率误拒。

二十二轮原报告 [round22:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/codex-review-CARD-G3-1-round22-2026-08-29.md:48) 原本点名的就是等水位线门，并未声称 coverage 门。当前脚本、UAT、CURRENT_TASK 对旧结论的转述有误；当前 `-k` 又未选择等水位线门，因而只显示两红。

这是精确红集和文档归因问题，当前实现基线正确，定为 **MEDIUM**。

## 5. 二十二轮八组 LOW 状态

| # | 状态 | 复核结果 |
|---:|---|---|
| 1 | **STILL-OPEN（部分处置）** | 新门 [contract.py:2415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2415) 能抓 marker 删除，但只数 marker 并检查两个关键词；保留关键词、反转其余语义仍可绿，不是真正三处同文门。 |
| 2 | **STILL-OPEN** | `_event()` [contract.py:1595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1595) 的 `review/1` payload 仍不满足主体完整扩展形状，路由与 float 门继续复用。 |
| 3 | **STILL-OPEN** | schema 门 [contract.py:2364](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2364) 仍只查 400 字符内三个键名；反写 [schema:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:14) 的义务但保留键名仍可绿。 |
| 4 | **STILL-OPEN（float 子项 CLOSED）** | `1.5/0.0` 门已闭合；但 vault 无证据测试 [contract.py:2018](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2018) 仍只锁泛化词，未锁实现 [validator.py:762](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:762) 的准确事实诊断。 |
| 5 | **STILL-OPEN** | `COLLECTED` [脚本:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:84) 仍漏 skipped/xfailed/xpassed/error。 |
| 6 | **STILL-OPEN（部分回填）** | 测试数字已更新，但 live/提交数仍漂移，详见下节。 |
| 7 | **STILL-OPEN** | UAT [436–437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:436) 仍称“可完整恢复”，未限定为当前本机、未版本化备份。仅保留为持久性 LOW，不重开账本 HIGH。 |
| 8 | **STILL-OPEN** | “纯 scanner 门”实际还有第三个 `applicable` 断言 [contract.py:2125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2125)；UAT 的“门当场抓自己人”仍无一手中间运行记录。 |

新增 LOW：0 组。

## 6. 文档诚实性与独立测试

| 项目 | 独立实测 | 裁决 |
|---|---:|---|
| 契约单文件 | 194 passed + 1 skipped | 一致 |
| 契约 + golden + learning_event_log | 219 passed + 1 skipped | 一致 |
| golden | 19 passed | 一致 |
| `test_fsrs_manager.py` | 37 passed | 一致 |
| live | 22 行 / 7232 bytes / `2a18023e…` | UAT 部分位置错误 |
| backup | 23 行 / 7492 bytes / `f78b99f3…` | 一致 |
| `37387a86..HEAD` 提交数 | 24 | 未正确回填 |

具体文档问题：

- UAT [第 8 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:8) 和 [第 36 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:36) 仍明确写“当前 23 行”，实为 22。
- UAT [第 475 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:475) 写提交数 22；该段对应前一 HEAD 时已经是 23，当前为 24。
- CURRENT_TASK [18–21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:18) 的测试数字正确，但未明确回填 live 22 和当前提交数。
- “逐实例判据、全部承重”及“Q 完整套件只有两红”属于上述两项 MEDIUM 的过强表述。

## 7. 十九轮账本 HIGH：闭合成立

独立复算：

- [backup](/Users/Heishing/Desktop/canvas/canvas-learning-system/backups/learning_events.jsonl.pre-s1-cleanup-20260829-061014)：23 行、7492 bytes、SHA-256 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`
- [live](/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/learning_events.jsonl)：22 行、7232 bytes、SHA-256 `2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6`
- backup 前 7232 bytes 的 SHA 与 live 完全相同。
- `diff` 唯一差异是末尾第 23 行 `callout:c-409-guard`。
- 两文件经当前 validator 均 exit 0。

文件字节本身证明了缺失内容及唯一删除范围；授权性不能仅由 bytes 推导，但用户本轮已明确确认其为已授权探针清理，且 UAT [第 436 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:436) 有同向记录。因此该 HIGH 足以关闭，不缺额外证据。

## 8. CARD-G3-4 保持可验收

`9a71eb8c..HEAD` 对 generator、manifest、vectors、`learning_event_log.py`、`fsrs_manager.py` 均零 diff。

当前 blobs：

- generator `9d6ab4f63b326dc3f604cb794ce9fd9e42de792e`
- manifest `b59f331d9a1f57e5778fd82399ef12b61eb0c967`
- vectors `33c601995d5274f7702a4d0ce501d2b81311d688`
- `learning_event_log.py` `28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py` `980b3758758b1d78d6795451c76270c10713cc60`

`generate()` 内存序列化与仓内 JSON 逐字节相同：manifest SHA `82eaaffa…`、vectors SHA `df60dbc6…`；20 vectors、3 个 retrievability 点、FSRS 6.3.1。golden 19 + fsrs_manager 37 = **56 passed**。

## 验证边界

- 未执行会原地修改 tracked validator 的负验证脚本；Q 与路由 mutation 均以内存加载方式复现。
- 未验证远端 CI；也未把 FSRS 全族 11 文件的历史 `191 passed` 当作本轮独立结果。
- 本会话未提供 `graphiti-canvas` MCP，故未执行 Graphiti 查询。
- 测试后 `git diff` 与 staged diff 均为空；审阅前已有的一份 untracked round23 报告未读取、未触碰、未纳入证据。

## 残留清单

- **BLOCKER：0**
- **HIGH：0**
- **MEDIUM：2**
  1. `expect_red` 实例计数稳定得到 0 且 fail-open；W regex 另可跳过计数。
  2. 变体 Q 完整套件实际三红，当前选择集和文档隐藏/误述第三红。
- **LOW：8**
  1. 区间外说明门仍只锁 presence/关键词。
  2. 路由测试继续复用主体不合规 fixture。
  3. schema 成文门过弱。
  4. float 已闭合，但准确诊断事实仍未锁。
  5. `COLLECTED` 漏计。
  6. live/提交数字漂移。
  7. backup 长期持久性边界未披露。
  8. “纯 scanner/门抓自己人”叙述仍过强。
