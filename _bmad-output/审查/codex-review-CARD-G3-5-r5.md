**结论：本轮仍不能判定闭合。发现 1 条 HIGH、6 条 MEDIUM、1 条 LOW；未发现 BLOCKER。** r4 的部分修复成立，但保留键冲突仍可静默丢值，隔离区认领也存在计数与报告错误。

审查对象为 `card/u9-mastery`，HEAD `3bc0ed9a` 加当前工作区相对 `155d3361` 的改动。以下反例均为**源码推导，未执行测试、迁移器或变异 harness**；未修改文件、未连接数据库。下文 `R` 表示实际保留键 `__g35_orphan_legacy__`。

## HIGH

**H1 — 保留键作为 legacy concept 且目标桶已有同名记录时，迁移成功却丢掉 legacy 值。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:290)，数量门在同文件 `:451-452`。

输入：

```json
{
  "A": {"__g35_orphan_legacy__": "bucket"},
  "__g35_orphan_legacy__": "legacy"
}
```

指定 `--apply --vault-id A`：

- 该分支只把 concept 加入 `clobbered`，**既未覆盖，也未放回隔离区**。
- `n_old=1`、`gained=0`、`expected=1-1=0`，数量门放行。
- 在正常 I/O 下最终返回 `0`，文件只留下 `"bucket"`，`"legacy"` 消失；`:443` 却报告“用裸键那份覆盖”。

双备份提供恢复机会，但不改变成功产物丢值的事实。**r4 H1 的“非 dict 一律按普通 legacy 处置”只在加载器侧成立，迁移器尚未闭合。**

## MEDIUM

**M1 — 列表化无法区分旧的“单条值本身是列表”与新的“候选列表”。**

位置：[review_service.py:634](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:634)、同文件 `:675`；迁移器 `:280-289`。

旧隔离快照 `{R: {"c": []}}` 会被加载器解释成零份候选，随后删除；下一次成功保存便丢掉原条目，且没有告警。旧单条值 `["x","y"]` 则变成两份候选，迁移后为 `A.c="x"`、隔离区剩 `"y"`，原记录的类型和边界被改变。

**当前新生成的列表值没有这个问题**：`:687` 使用 `append(v)`，会把原列表包成 `[[]]` 或 `[["x","y"]]`，能够稳定重载。问题在于没有版本标记来兼容旧隔离格式。

这是历史任意值保全承诺的缺口，不代表正常 FSRS 字符串卡必然受损。对于真正的新格式空候选列表，丢弃空槽本身没有卡数据损失。

**M2 — 毒条目预检仍漏掉 vault 顶层键，可持续阻断所有合法保存。**

位置：[review_service.py:668](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:668)，保存失败路径 `:1085-1107`。

预检只验证桶内 concept 键和值，没有验证外层 `vid`。例如：

```json
{"\ud800": {"c": "ok"}}
```

该文本能被 `json.loads` 读取，毒 vault 键随后原样进入快照。每次全量 UTF-8 写入都会失败，而异常处理只回滚本次合法 pending，毒桶一直留下。甚至 `{"\ud800":{}}` 也成立。

触发面是外来或历史快照，并非标准 vault 命名管线。**r4 M1 仍属部分修复。**

**M3 — 隔离冲突被重复扣数，导致本可认领的其他条目也全部被拒。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:283)，同文件 `:448-459`。

输入简写：

```text
{"A":{"c":"existing"}, R:{"c":["iso"],"d":["free"]}}
```

目标为 A。构造结果正确地保留隔离区 `c`、认领 `d`，但未认领的 `c` 也被加入 `clobbered`：

```text
gained = 1
claimed_from_isolation = 1
expected = 0 + 1 - 1 = 0
```

因此整次迁移返回 `1`，`d` 也无法迁入。隔离余量已经排除了未认领项，再减 `clobbered` 属于重复扣减。**“冲突留下，其他条目照常认领”尚未贯通主流程。**

**M4 — 保留键值为 `null` 时，被迁移器误当成键不存在。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:275)、同文件 `:290`。

`{R:null}` 在 `classify()` 中算一条 legacy，但 `raw.get()` 配合 `is not None` 使构造阶段完全忽略它。最终 `gained=0`、`expected=1`，返回 `1`；混入其他可迁条目也会整体失败。

加载器会保留这个非 dict 值，两端口径不一致。此反例**不会写盘丢值**，但否定“所有非 dict 值均按普通 legacy 处理”。

**M5 — 纯隔离输入的 dry-run 仍错误预告 apply 不写入、不备份。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:367)，对照 `:416`。

输入 `{R:{"c":["iso"]}}` 时，dry-run 因 `n_old==0` 输出“无可迁移条目……apply 将直接退出且不产生备份”。实际 apply 同时检查 `n_isolated`，会认领、备份并改写文件。

**r4 H3 的“误报无须迁移”在预演计划面仍然存在。**

**M6 — 多份候选由脚本自动选第一份，剩余项却未按承诺报告。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:273)、同文件 `:287-289`、`:575-592`；加载器承诺在 `review_service.py:683`。

输入 `{R:{"c":["one","two"]}}`，目标 A：

- 自动把 `"one"` 放进 A，`"two"` 留在隔离区；
- CLI 没有选择候选的参数；
- 输出“迁移完成”、报告 `result="ok"`，却没有剩余隔离数量或候选明细；
- `n_isolated_after` 已在 `:439` 算出，随后未用于报告。

这符合作者披露的“取第一份”算法，但**不完全符合“由人在迁移时选”“脚本不替人选”“把其余逐条报出来”这些源码承诺**。`--vault-id A` 只表达目标桶；不足以证明第一份就是人裁定属于 A 的记录。返回 `0` 至多证明本次部分认领成功，不能证明迁完。

## LOW

**L1 — 保留名守卫旁的生产注释仍与本轮处置说明、新测试矛盾。**

位置：[review_service.py:454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:454)。

这里仍写 `sanitize_vault_id`“理论上能产出这个串”；新测试 `test_g3_5_vault_keyed_card_states.py:425-427` 则写前导下划线会被剥掉、标准管线产不出。

因此“已把该事实写进注释”只在测试注释成立，生产解释没有同步。守卫本身确实存在；本轮未扩读 sanitizer 实现，不能把测试注释当成独立实测。

## 已核实成立的部分

- **r4 H2 的新格式同名保全成立。** `review_service.py:678-688` 用逐个 `append` 合并；已有字符串候选与新冲突记录都能留下，重载不会自动认领。历史列表兼容问题见 M1。
- **r4 H1 的两道保留名守卫成立。** service `:453-462` 返回 `None`；迁移器 `:664-671` 拒绝该 `--vault-id`、返回 `2`。加载器 `:637-638` 也不再跳过保留键下的非 dict 值。
- **r4 H3 的单份、无冲突认领成立。** 隔离区独立计数，不计入 `n_new` 或跨 vault 冲突；作者给出的单卡示例可沿源码推出成功。不能推广到上述冲突和多份场景。
- **r4 M2 的固定反向符号链接检查成立。** 迁移器 `:469-492` 在两次 `copy2` 前检查实际生成的备份路径与 `--out` 的 resolved 路径及 inode。已登记的路径替换窗口仍未闭合。
- **备份与回滚已具备明确失败分流。** `:493-512` 备份失败时不开始改输入；`:553-557` 捕获写盘中途异常并还原；`:524-540` 将还原失败或还原后不可解析区分为 `rc=3`，正常还原为 `rc=1`。它不能保证磁盘满、权限变化时必然恢复，但调用者能区分两种结果。
- **dry-run 的准确承诺是“不改输入、不产生备份”。** 不给 `--out` 才是零文件写入；给了会创建目录并写报告，源码已有此限定。
- **该 HTTP 入口足以支持 service 读取 ContextVar。** [review.py:1395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/api/v1/endpoints/review.py:1395) 已有 Query，`:1424` 注入，`:1430` 调用 service。本次键化无需新增 HTTP 参数；不等于证明所有后台或其他入口经过该注入链。
- **Mapping 覆盖了该文件现有调用形式。** `get`、索引、成员检查、`bool/items` 和 `dict(states)` 均有对应实现。`get_history:2033-2034` 的真假判断与遍历一致地作用于当前桶；`get_cached_card_states:2767-2774` 也明确收窄为当前 vault。未发现方法缺失导致的形状回归，但不能据此证明所有仓外调用者都接受语义收窄。
- **无 ContextVar 不等于解析失败。** `vault_scope.py:269-318` 明确回落 active vault；正常启动、CLI、scheduler 因此可能归桶。`current_vault_id()` 没捕获依赖异常，字面“恒不抛”不成立；当前 service 注释已准确收窄。N2 的源码证明其针对“推导故障”设门，**本轮不能确认变异运行确实红在指定断言，也不能据此证明生产触发频率**。
- **N 的定义与甲支推导自洽，r4 L1 正文已修。** census 明确包含经公开 API 的间接消费，故端点可以计入；当前入口足证 `N≥1`。乙支仅在所有外部消费关系消失时于定义上可达。分支裁定 `:102-117` 已不再宣告 `/goal` 括注失效。本轮没有独立复算全仓“恰为 1”。
- **两条既有落盘断言已不是“任意桶含 cid”。** unit `:785-793` 保留具体桶内精确值相等，regression `:272-276` 检查具体 dict 桶中的 cid，原测试意图保留。它们从 service 派生期望 vault，因此不能单独证明请求身份解析正确。
- **真相源与 TOCTOU 的登记基本准确。** `frontmatter_signals.py:35-37` 仍按进程级路径读取；`review_service.py:2825-2829` 明确键化未闭合时间窗口。本卡不能被解读为完整的一进程多 vault 隔离。未发现足以另立新项的加重证据；继承的跨进程快照覆盖与已登记 H4 不重复计为新问题。

验收单不在本轮指定读取面内，**“这些限定已同步写入验收单”未独立核验**。轮次上限不改变上述未闭合项的状态。


