终裁：

- `CARD-G3-1`：**需再一轮**。十四轮那个具体 `[]` 反例已窄义关闭，但 proof verifier 仍存在 3 组可返回 `[]` 的 HIGH 级规范缺口。
- `CARD-G3-4`：**可验收**。重复键 HIGH 与枚举类型问题均真实闭合，仅余 LOW 级测试/文档质量债。
- `BLOCKER = 0`。全程只读，最终工作树 clean。

## 1. G3-1 proof 逐门对照

规范锚点见 [schema §6.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:196)，实现见 [validator:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:503)。

| proof 门 | 结论 | 实测/偏差 |
|---|---|---|
| 12 个顶层必填字段 | `CONFIRMED-CLOSED`（仅存在性） | `_PROOF_REQUIRED_KEYS` 与逐项缺失门已实现，[validator:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:357)、[535](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:535)。 |
| cursor、E、event_id、review_time 绑定 | `STILL-OPEN` | event_id/行号绑定已闭合；但 proof 时间只用宽松 `fromisoformat`，[575-580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:575)。naive 时间和 `9999-12-31T23:59:59Z` 均返回 `[]`；naive/aware 混排抛未捕获 `TypeError`。 |
| vault/node 身份 | `STILL-OPEN` | node 用于筛选，vault 仅验非空。账本事件 `payload.vault_id="real_vault"`、proof 写 `"different_vault"` 时仍返回 `[]`，[545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:545)、[561-564](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:561)。 |
| prefix 精确 bytes、LF 规则 | `CONFIRMED-CLOSED`（稳定快照下） | 起点、终止 LF、无尾 LF 均按规范实现，[482-500](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:482)。并发双读例外见第 3 点。 |
| 算法身份、完整 scheduler config、reducer | `STILL-OPEN / HIGH` | 规范要求与 G3-4 manifest 同源并含完整配置，[schema:214-215](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:214)；实现只验非空字符串/dict。以下输入实测 `[]`：`library_version="garbage"`、`params_hash="degraded:x"`、`scheduler_config={}`、`reducer={}`。 |
| result_hash | `CONFIRMED-CLOSED`（声明范围内） | 只验 64 hex，不复算；schema 和 docstring 已如实声明 reducer 后续复算，[schema:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)、[validator:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:521)。 |
| canonical state 键集/类型/hash | `STILL-OPEN` | 键集、UTC-Z、int/float 已闭合，但数值域未查。`stability=-1.0,difficulty=99.0` 可生成无违规 hash，而同文件 `classify_card_state()` 判 degraded。 |
| snapshot 三等式 | `CONFIRMED-CLOSED` | 三式均在位，等式 3 已按绝对瞬间，[647-675](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:647)。 |
| 左开右闭、行序、层内/跨层单调 | `CONFIRMED-CLOSED`（合法 aware 时间前提下） | [692-713](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:692)。 |
| 链终止、同身份、严格递减、防循环 | `CONFIRMED-CLOSED` | 128 层限制已同时写入实现与 schema，公开入口能把 `RecursionError` 转为违规。 |
| genesis 真锚 | `STILL-OPEN / HIGH` | 见下列三个确定性反例。 |
| 最外层覆盖尾部 | `STILL-OPEN` | 稳定 bytes 下正确；双读竞态可漏尾。公开 API 还允许显式 `is_top_level=False`，cursor 1 后有 L2 时可返回 `[]`。 |
| degraded 事件不得入链 | `STILL-OPEN / HIGH` | 只拒 proof 顶层的 `fsrs_library_version` 哨兵；不拒 `fsrs_params_hash` 哨兵，也不读取区间事件的两项算法字段，[568-569](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:568)。 |

Genesis 三个关键反例：

```yaml
"fsrs_state": 2
```

这是合法顶层 YAML key，hash 自洽时 verifier 返回 `[]`；正则只识别未加引号的行首 key，[validator:627](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:627)。

```text
L1: node=n 的历史 answer_scored，无 review/1
L2: node=n 的 review/1 事件
proof.first_event_line=2
```

直读模式返回 `[]`。实现取“最早适用行”，但规范要求“该节点最早一条事件”，并明定存在无扩展历史复习行时不得走 new_card，[schema:247-249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:247)、[validator:639-644](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:639)。

此外，所附原文仅与自报 hash 自洽，没有与真实节点文件 bytes 绑定。

## 2. 十四轮两个 HIGH 重放

### G3-1：`CONFIRMED-CLOSED`（窄义）

十四轮原 proof 对象改用当前三元 applicable 接口：

```python
[(1, t1, "e1"), (2, t2, "e2")]
```

现报 9 条违规：缺四字段、两个 proof hash 形状错、genesis hash 错、原文含 FSRS、first line 错位。

但严格照十四轮旧调用 `[(1,t1),(2,t2)]` 会在 [validator:584-585](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:584) 抛 `ValueError`，不是返回违规列表。这是 LOW 级 API fail-closed 缺口。

### G3-4：`CONFIRMED-CLOSED`

精确插入：

```json
{
  "library_version": "999.0.0",
  ...
  "library_version": "6.3.1"
}
```

结果：

```text
tampered SHA256 = 4b5cbd6c212c4269605e02659fdb1d4d19834730e32ef12bf4e43dd218a2dfbc
宽松解析对象不变，last-wins = 6.3.1
严格解析 = _NonStandardGoldenJSON，点名 library_version
```

严格入口与回归门见 [golden test:60-88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:60)、[481-497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:481)。

## 3. 账本直读模式

`NEW-FINDING / HIGH`：直读不是单一快照。`extract_applicable()` 和 `ledger_prefix()` 各自调用一次 `read_bytes()`，[451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:451)、[489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:489)。

复现：

```text
第一次 read_bytes -> L1
第二次 read_bytes -> L1 + 新追加的 L2
proof.cursor_line = 1
结果 -> []
```

适用集来自旧快照，看不到 L2；第二次计算 cursor 1 的 prefix 仍只覆盖 L1。因此最外层尾部门可在真实追加竞态下失效。

筛选口径方面：

- 它实现的是 proof 所需的“全部适用事件”：node 相同、`review/1`、未出现 `out_of_order`。
- 它**不是 pending 集合**：没有 W，未检查 `review_time > W`，也不按 `(绝对时刻, 行序)` 排序。docstring 引用 pending 定义不准确。
- 非 UTF-8/非法 JSON 行 `continue` 后，后续物理行号不会压缩，但无法判断坏行是否本应适用；三行账本“合法 L1 / 截断 L2 / 合法 L3”可令 cursor 3 proof 返回 `[]`。所以“从根上消除信任边界”表述过强。

四种指定字节输入在**单一稳定快照**下，行号同域：

| 输入 | extract 行号 | prefix |
|---|---:|---|
| CRLF 两行 | `[1,2]` | hash 包含 `\r\n`，无尾标志 |
| 含空行 | `[2,4]` | 空行仍计物理行并进入 prefix |
| 前置非 UTF-8 行 | `[2]` | 非法 bytes 仍进入 prefix |
| 两行、末行无 LF | `[1,2]` | hash 到 EOF，`prefix_ends_without_lf=True` |

## 4. 误拒风险

`NEW-FINDING`：

- 合法 frontmatter block scalar：

  ```yaml
  description: |
    fsrs_state: documentation only
  ```

  没有顶层 `fsrs_*` 字段，却被正则误拒。

- 空 frontmatter 原文 `""` 合法且 hash 可复验；规范未要求非空，实现私加“非空字符串”门，[621-623](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:621)。
- 128 层是已成文的保守拒绝；全仓无生产 caller，现实影响目前为零。未来单节点累计超过 128 次 repair snapshot 会被拒。
- G3-4 当前 Rating/State 全部确为 Python `int`；`type(v) is int` 不会误拒当前合法金标。
- 重复 JSON key 与 NaN/Infinity 对冻结金标不是合法输入，严格拒绝正确。

## 5. 测试有效性

`CONFIRMED-CLOSED`：

- `4f26831a…` 已用 shell 独立复算：

  ```text
  4f26831a0f4e60998f463ca6ed5091831e5ad7cba9e242789ad23acccc1e3b57
  ```

  与 [测试常量](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1070) 完全一致，不来自被测函数。

- 必填字段、三等式、tail、单调门多数检查具体违规 marker，不是“只要 problems 非空”。
- G3-4 重复键测试同时锁宽松解析前提与具体异常，断言有效。

`STILL-OPEN / NEW-FINDING`：

- genesis 测试未覆盖 quoted YAML key、block scalar、空 frontmatter，也没有覆盖“合法 64 hex 但与原文不一致”；还把错误的“最早适用行”写成期望，[test:1270-1283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1270)。
- degraded 测试只改 proof 的 library version，没测 params sentinel 或账本事件 sentinel，[1293-1297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1293)。
- prefix 多个正例先调用被测 `ledger_prefix()` 生成期望，再交给 verifier，存在同源 oracle；裸 CR 最后一行用独立 `hashlib` 覆盖了一种全文件情形，但没覆盖中间 cursor。
- [test_enum_bool_drift_is_rejected](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:500) 只证明 `True == 1` 与 `type(True) is not int`，不调用实际主门，也没覆盖 State；删除真正循环后这条仍会绿。实际主门 [209-216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:209) 本身有效。
- `_load_golden` 的 NaN/Infinity 拒绝实现正确，但缺专门回归。

## 6. 负验证脚本

脚本见 [negverify:17-122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:17)。

`mutate()`：

- 当前五个表达式均能命中目标；没有 `/g`，最多改第一处。
- 前后 SHA 只证明“某些 bytes 变了”，不能证明原模式恰出现一次、只改了预期语义，也忽略 Perl 非零但已部分改写的情形。
- 因此当前五例窄义可用，但不是可靠的通用命中计数器。

`expect_red()`：`STILL-OPEN / MEDIUM`

- 不检查 pytest exit code。
- 不核对具体失败 marker/原因；参数化测试的无关 case 失败也可能满足。
- 基线和最终只查 `^FAILED`；collection error、internal error、0 collected 都可能被当“全绿”。[script:61-68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:61)、[107-114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:107)。

恢复：

- 正常退出由 `EXIT` trap 复制备份恢复。
- `SIGKILL`、掉电、宿主崩溃无法恢复。
- 初始备份和恢复 `cp` 均未检查；trap 即使恢复失败仍删除备份。
- 因脚本会原地修改 tracked verifier，本轮遵守只读约束，没有执行它。

## 7. 范围声明

`STILL-OPEN`：

- schema、模块注释与函数 docstring 对三项“不做”基本一致：不折叠 FSRS、不复算 result hash、无 ledger_path 时信任 applicable。
- 但它们声称的“算法身份与真实绑定”“genesis 真锚”“ledger_path 消除信任边界”强于实际实现，未披露非法行前置验证和双读竞态。
- G3-1 UAT 仍写“只判结构与分层”，没有同步当前“真实绑定”范围，也未完整列出三项不做，[UAT:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:267)。

## 8. 回归、现网与 Git 一致性

全部指定测试通过：

```text
契约 + golden + 既有账本：121 passed, 1 skipped
  = 契约 100 passed, 1 skipped
  + golden 15 passed
  + test_learning_event_log.py 6 passed

test_fsrs_manager.py：37 passed
其余 FSRS 族 10 文件：154 passed
FSRS 非 golden 全族：191 passed
```

现网仓根账本：

```text
23 行
validator exit 0，RESULT: PASS
前 SHA = f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de
后 SHA = f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de
```

Git 对象：

```text
HEAD = 425f8564231aea3152934ab348a4669694f642e2
learning_event_log.py = 28cdaa18602b72670c0f2e57b3cba6a7c1453dd0
fsrs_manager.py       = 980b3758758b1d78d6795451c76270c10713cc60
```

G3-4 三文件从 `e013102f..HEAD` 零改动，且 `generate()` 内存结果逐字节等于仓库文件：

```text
generator blob = 9d6ab4f63b326dc3f604cb794ce9fd9e42de792e
manifest blob  = b59f331d9a1f57e5778fd82399ef12b61eb0c967
vectors blob   = 33c601995d5274f7702a4d0ce501d2b81311d688

manifest SHA256 = 82eaaffa2a064064140916a272e8b4d4256fe4bd58cdb4914c4793646af3cb09
vectors SHA256  = df60dbc6192c499ad21da6533f35ed2e0e316f5d4bc52fb45b711d4cae6f49a3
```

文档数字/时态不一致：

- G3-1 UAT 顶部仍为 `69+1 / 88+1`，[UAT:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:32)，底部才是当前 `100+1 / 121+1`。
- G3-4 UAT 顶部/交付清单仍写 `13 passed/十门`，[UAT:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:25)，尾部才写 15。
- `CURRENT_TASK` 仍写“十五轮整改待提交”“十六笔提交待办”，但 `2483441f`、`425f8564` 均已提交；还同时保留旧 `1024/95/116/179` 与新 `128/100/121/191` 现实冲突。[CURRENT_TASK:5-40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5)
- 已提交的 round15 审查文件是 0 字节，不能作为正式十五轮结论。

## 残留清单

- BLOCKER：0

- HIGH — CARD-G3-1

  - 算法身份/config/reducer 仍为空门；params sentinel 与 degraded 账本事件可入自动证明链。
  - genesis quoted-key 与历史无扩展事件仍可伪装 new_card；`first_event_line` 与 schema 定义不一致。
  - ledger_path 两次独立读取；并发追加可令最外层尾部事件逃逸。

- MEDIUM — CARD-G3-1

  - proof review_time 未落实 aware/整秒/A7，混合 naive/aware 会抛 `TypeError`；snapshot 数值域未查。
  - vault 未绑定、非法账本行静默跳过，直读范围声明过强。
  - genesis/degraded/prefix 测试存在错误期望、覆盖缺口或同源 oracle。
  - 负验证不检查 pytest exit/collection error/具体失败原因。
  - CURRENT_TASK 与验收单的数字、提交时态和恢复锚点失真。

- LOW — CARD-G3-1

  - block scalar、空 frontmatter 被误拒；128 层是有意保守限制。
  - 旧二元 applicable 抛异常；公开 `is_top_level=False` 是尾部门脚枪。
  - 负验证在 SIGKILL/掉电或恢复 `cp` 失败时不能保证还原。

- LOW — CARD-G3-4

  - 专门 bool 负例不承重，NaN/Infinity 缺直接回归。
  - UAT 与测试 docstring 仍写 13/十门，与实测 15 不一致。

最终判定：**CARD-G3-1 需再一轮；CARD-G3-4 可验收。**

环境未暴露 `graphiti-canvas`，故项目规则要求的 Graphiti 本轮搜索为 `UNVERIFIABLE`；其余审阅、测试、现网与 Git 核验均已完成。
