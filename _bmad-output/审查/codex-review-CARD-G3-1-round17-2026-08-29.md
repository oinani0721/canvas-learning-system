结论：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

HEAD 已确认是 `a3ec2da16517299d0a0572454e8c644d640791d3`。全程只读，tracked diff 为零；仅保留审阅前已存在、未读取的 untracked round17 草稿。

## 1. 十六轮四条 HIGH 重放

| 输入 | 实际结果 | 裁定 |
|---|---|---|
| `enable_fuzzing: 0` | 报具体差异键 `enable_fuzzing` | **CONFIRMED-CLOSED** |
| `learning_steps_minutes=[true,10]` | 报具体差异键 `learning_steps_minutes` | **CONFIRMED-CLOSED** |
| manifest 不可达 + 六键全 `0` | proof 报“无法证明算法身份…fail-closed”；主体仍只发两条 WARN | **CONFIRMED-CLOSED**，且不与主体独立运行冲突 |
| L2 `out_of_order:false`、proof cursor=L1 | 同时报“形态非法”和“尾部仍有事件 [2]” | **CONFIRMED-CLOSED** |
| 无 PyYAML + 普通/转义 `fsrs_state` | 均发 PyYAML 不可达 fail-closed；普通键另报正则命中 | **CONFIRMED-CLOSED** |
| L1 vault=A、L2 vault=B、proof=A | 报事件 vault 集合不是单一值 | **CONFIRMED-CLOSED** |
| 全部事件缺 `vault_id`、无 config、proof 任填 A/B | A、B 都返回 `[]` | **STILL-OPEN** |
| 一行带 claimed、一行缺 `vault_id` | 仍返回 `[]` | **STILL-OPEN** |

实现锚点见 [canonical 比较](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:832)、[out_of_order 扫描](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:518)、[vault 集合门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:664)、[genesis 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:895)。

## 2. proof 逐门更新

| proof 门 | 结论 |
|---|---|
| 12 个顶层必填字段 | **CONFIRMED-CLOSED** |
| cursor/E/event_id/review_time 及时间域 | **CONFIRMED-CLOSED** |
| node_id、链上身份 | **CONFIRMED-CLOSED** |
| vault_id 绑定 | **STILL-OPEN**：全缺/部分缺且无配置仍可自报 |
| prefix 精确 bytes、LF | **CONFIRMED-CLOSED** |
| algorithm/version/hash/config | **STILL-OPEN**：可达但部分损坏的 manifest 可失败开放 |
| reducer 结构 | **CONFIRMED-CLOSED** |
| snapshot state canonical hash、状态键集/类型/域 | **CONFIRMED-CLOSED** |
| snapshot 三等式 | **CONFIRMED-CLOSED** |
| 区间、层内/跨层单调 | 核心比较 CLOSED；扫描可隐藏行，端到端 **STILL-OPEN** |
| 链终止、递减、防循环/深度 | **CONFIRMED-CLOSED** |
| genesis | 安全门 CLOSED；PyYAML 硬依赖未成文 |
| top-level 尾部覆盖 | 核心比较 CLOSED；扫描入口 **STILL-OPEN** |
| degraded 区间哨兵 | **CONFIRMED-CLOSED** |

## 3. 新的实现/规范偏差

### NEW-FINDING / HIGH — 部分损坏 manifest 仍失败开放

`_golden_manifest()` 只校验 version/hash，不校验 `scheduler_config` 是否存在、为对象及六键完整，[loader](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1111)；比较又仅在该字段为 dict 时执行，[identity 门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:836)。

复现：

```json
{
  "library_version": "6.3.1",
  "params_hash": "<64-hex>",
  "scheduler_config": {"desired_retention": 0.9}
}
```

proof 携相同单键配置，返回 `[]`；字段缺失/非 dict 时，proof 六键全 `0` 也可过。违反 schema 的“完整配置且与 manifest 同源”要求，[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:219)。

### NEW-FINDING / HIGH — `out_of_order:true` 可隐藏实际后继

完整合法两行：

- L1：`t1`，正常适用事件；
- L2：`t2 > t1`，但标 `out_of_order:true`；
- proof cursor=L1。

结果：

```text
validate_file == ([], [])
verify_degraded_proof == []
```

扫描器无条件排除严格 `true`，主体只验形态而不验 `review_time <= W` 语义，[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1246)。这与规范的乱序定义冲突，[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:191)。G3-3 写侧是上游防线，不能替代 proof 的 fail-closed 门。

### NEW-FINDING / HIGH — vault 身份仍可自报

严格集合只比较“实际出现的非空 vault 值”；缺失行不入集合。主体单独运行会拒绝缺 `vault_id` 的 review/1 行，但 proof 不调用主体，而声称的“账本先过主体校验”前置条件也未写进 schema/docstring。因此十六轮“全缺 vault_id”输入仍未闭合。

### NEW-FINDING / MEDIUM

- `proof.vault_id=[]` 且账本含 vault 时，在类型门前执行 `{claimed}`，抛 `TypeError: unhashable type: 'list'`，[先使用](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:668)、[后类型检查](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:793)。
- canonical 文本会拒 `maximum_interval=36500.0`、steps `[1.0,10.0]`。G3-4 的 hash 口径支持严格拒绝，但 §6.2 未冻结 scheduler 各键类型/序列化，因此当前属于规范 under-specified。
- 无 PyYAML 会拒绝连 `title: n` 这样的合法 new-card proof；这不冲突于“账本主体 stdlib-only”，但 proof 的新增硬依赖未写入依赖契约。

`out_of_order:false` 本身不是合法场景，计入适用集不会误拒合法 proof。`REVIEW_EVENT_TYPES={"answer_scored","answer_abandoned"}` 与 §6.1 挂载点一致；建议仅把 §6.2“复习事件”措辞进一步明确定义。

## 4. 五个 survivor 门

隔离 `/tmp` mutation、全 contract 基线 `143 passed, 1 skipped`：

| 破坏 | 结果 | 裁定 |
|---|---:|---|
| earliest 退回 `min(applicable)` | 仅新 earliest 测试红，`1F/142P/1S` | **CONFIRMED-CLOSED** |
| 两次 `.open("rb").read()` | single-read 与 recursion 两测试红，`2F/141P/1S` | **PARTIAL**，重叠而非隔离 |
| 递归丢弃 `scan/raw/ledger_vault_id` | 仍 `143P/1S` | **STILL-OPEN** |
| 删除 stability 上界 | 仅对应测试红，`1F/142P/1S` | **CONFIRMED-CLOSED** |
| 删除 params-hash 哨兵扫描 | 仅对应测试红，`1F/142P/1S` | **CONFIRMED-CLOSED** |

递归 survivor 有实际后果：ancestor prefix 改成 `"f"*64`，当前实现报实算不符；mutation 返回 `[]`。新增门只统计最外层读取次数，没有证明 ancestor 消费共享事实。[新增测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1827)

其他全绿 survivor：

- 保留一次 `Path.read_bytes()`，另加一次 `Path.open().read()`；
- `is True` 改成 `== True`，L2 `out_of_order=1` 可隐藏；
- `REVIEW_EVENT_TYPES` 分支漏掉历史 `answer_abandoned`；
- 删除 proof 的 `.canvas-config.yaml` 配置锚；
- 删除无 PyYAML 时正则命中诊断；
- 恢复 degraded 双字段重复行号。

因此新增测试整体只能判 **PARTIAL**。未发现纯恒真断言，但递归门、读取计数、non-review 只查某条错误不存在等断言均偏弱；PyYAML 测试的说明提到 escaped key，实际 fixture 只是默认 `title: n`。[相关测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1729)

## 5. 负验证脚本

未原地执行脚本；静态计数及进程内等价 mutation：

- A–L 十二个 Perl 模式当前均恰好命中 1 处。
- 实际红集：`A 1F/1P、B 1F/1P、C 2F、D 1F、E 1F/2P、F 1F/1P、G 1F/7P、H 1F、I 1F、J 1F、K 1F、L 2F`，当前无额外 FAILED。

但机械保证仍 **PARTIAL**：

- 命中计数失败得到 `?` 会被放行，实际 Perl mutation 返回码也未检查，[脚本](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:34)。
- “失败集合 ⊆ 预期集合”只要求至少一个预期项红；多测试/参数化场景不保证全部红，[判据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:63)。
- 预期测试体内 `1/0` 会被 pytest 记为 FAILED 而非 ERROR，脚本会误判为承重。
- 初始备份检查了返回码；中间恢复与 EXIT trap 的 `cp` 没检查。
- 最终 `cmp -s` 是有效逐字节校验，但只覆盖成功走到最终段且最后恢复成功的路径，[cmp](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:200)。

## 6. 范围声明与时态

**NEW-FINDING / MEDIUM：所谓六条并未落文。**

- schema 仍写“四件事”，[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)；
- 模块注释只有三条，[模块注释](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:330)；
- 函数 docstring 只有四条，[docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1040)；
- UAT 却声称“三条扩六条、全部已修”，[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:336)。

第⑤“主体校验前置”和第⑥“无身份证据时 vault 自报”都没有进入规范面。

现网 23 条中：`payload.vault_id=0`、`group_id=7`、`review/1=0`；同目录配置存在且当前可解析。因此第⑥只部分准确：一般形态下“两锚都缺则自报”属实，但当前现网并非配置缺失，也尚未实际进入 proof 路径。

**NEW-FINDING / LOW：** [CURRENT_TASK:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5) 和 [CURRENT_TASK:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:29) 仍写“第十八笔待提交/下一步提交”，但 HEAD 已是第十八笔。测试数字则已正确。

## 7. 回归与 G3-4

使用指定 venv、禁 bytecode/cache，实跑均 exit 0：

- contract：`143 passed, 1 skipped`
- golden：`19 passed`
- 既有账本：`6 passed`
- 三文件同进程：`168 passed, 1 skipped`
- `test_fsrs_manager.py`：`37 passed`
- UAT 所列 11 个 FSRS 文件：`191 passed`（816.83s）

`b6f11fb9..HEAD` 对 generator/manifest/vectors 的 diff 为空；内存 `generate()` 序列化与仓库两文件逐字节相同，20 vectors、3 retrievability points。

锁定对象：

- `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- generator/manifest/vectors blobs：`9d6ab4f6… / b59f331d… / 33c60199…`

主 checkout 现网账本 23 行，当前 CLI `RESULT: PASS`；前后 SHA-256 都是 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。

## 残留清单

- **BLOCKER：0**
- **HIGH：3**

  1. 部分损坏但可达的 manifest 仍可令任意/残缺 scheduler config 通过。
  2. 语义虚假的 `out_of_order:true` 可隐藏实际后继。
  3. 全缺/部分缺 vault 证据时 proof 身份仍是自报值。

- **MEDIUM：5**

  1. 非字符串 vault_id 可令 verifier 抛 TypeError。
  2. 递归共享、实际读取次数及若干关键分支测试仍不承重。
  3. 负验证脚本仍可能因子集、测试体异常及未知命中数误判。
  4. 六条范围、主体前置、PyYAML 依赖未进入规范锚点。
  5. scheduler_config 数值类型/canonical 口径未在 schema 冻结。

- **LOW：3**

  1. PyYAML exact-key 诊断和 degraded 去重没有回归门。
  2. CURRENT_TASK 提交时态及 G3-1 UAT 无基线 diff 表述过期。
  3. “现网带的是 group_id”措辞过宽，实际为 7/23。

最终裁定：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。** 本轮采用并行、生产入口、反例优先的历史审计规程，但所有事实均从当前 HEAD 重新复算。Graphiti MCP 本会话不可用；上述是本地 checkout/测试结论，不冒充远端 CI 状态。


