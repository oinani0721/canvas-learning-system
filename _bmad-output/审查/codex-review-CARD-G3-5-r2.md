**结论：BLOCKER 0 / HIGH 5 / MEDIUM 3 / LOW 2。不能认定 round-1 已全部闭合。**

审查对象是 `card/u9-mastery`、基线 `155d3361` 上的**当前工作区修改**。最终重复采样内容一致。全程只读，未运行测试、变异 harness 或连接数据库；下列反例均为静态代码路径推导。

## HIGH

**H1．备份写入没有过闸，仍可覆写现网。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:377)，关联 `:380-381、:528、:542`。

`main()` 检查了 `--file` 和 `--out`，但两条派生备份路径直接交给 `shutil.copy2()`。

反例：输入是普通临时副本 `/tmp/snap.json`，而 `/tmp/snap.json.bak` 已是现网投影的符号链接或硬链接。输入通过检查后，第二次 `copy2()` 会覆写该链接指向的现网文件。

因此，**原 HIGH-2/4 的直接参数反例已修，但“迁移器不会写现网”仍不成立**。此外，`--out=/tmp/snap.json.bak` 也会在成功迁移后把简单备份覆盖成报告；时间戳备份仍在，但“双备份”承诺被破坏。

**H2．编码错误仍可在截断后绕过回滚，损坏文件却以 rc=1 退出。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:433](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:433)，关联 `:36、:437-438`。

写入只捕获 `OSError`。文件文本如 `{"\ud800":"{}"}` 含转义的孤立代理字符键，能被当前 `json.loads()` 接受，也能通过备份读回。

随后 `ensure_ascii=False` 保留该字符；`Path.write_text(..., encoding="utf-8")` 打开并截断目标后，编码抛出 `UnicodeEncodeError`。它不属于 `OSError`，不会进入 `_restore()`。CLI 因未捕获异常退出 1，目标却可能已经为空。

这直接反驳 `rc=1 ⇒ 未写入或已安全回滚` 的约定。**HIGH-3 仅部分修复。**

**H3．混合快照仍会用“推定归属”的旧值覆盖已有明确 vault 身份的记录。**

位置：[review_service.py:578](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:578)，关联 `:540、:580、:583`。

当前作用域为 `A`，输入：

```json
{"A":{"c":"A-new"},"c":"legacy-unknown"}
```

`bucket.update(legacy)` 得到：

```json
{"A":{"c":"legacy-unknown"}}
```

已有 `A.c` 被覆盖，下一次落盘将固化覆盖。代码虽会警告，但“过渡期不丢数据”“已迁桶原样载入”仍比行为宽。

逐条分类确实解决了“整个桶被降格成 concept”，**没有解决同桶同名冲突**。新增混合快照门选择不同 concept，并假定已迁桶不是当前桶，避开了这个显形点。

**H4．启动时拒载 legacy，后续正常保存会把它从磁盘永久删除。**

位置：[review_service.py:564](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:564)，关联 `:576、:517-519、:961-969`。

作用域解析失败时，加载器只返回已迁桶，legacy 没有保留在任何待处理结构中。之后一次具有合法作用域的成功写入，会用这些桶的全量快照替换原文件，删除此前“未加载”的 legacy。

触发链是：

> 启动推导失败 → legacy 未载入 → 后续请求显式注入合法 vault → 成功保存 → 原 legacy 消失。

因此，“本次不加载”并未形成贯穿后续保存的保护。现有 fail-closed 门只测空文件上的一次失败写入，未覆盖这条生命周期路径。

**H5．新增现网拒绝测试的失败路径会真的覆写现网。**

位置：[test_g3_5_vault_keyed_card_states.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:297)，关联 `:303-305`。

`test_out_pointing_at_live_file_is_refused` 直接把真实 `m.LIVE_CARD_STATES` 传给 `--out`，没有替换成临时保护文件。

一旦待测守卫回归为放行，流程会进入 `write_report()`，把真实现网投影覆盖成统计报告。**这个回归门在缺陷显形时，自身就违反禁写现网边界。**

同文件硬链接测试已使用临时保护文件，那里采用的隔离方式是合理的。

## MEDIUM

**M1．“中途写失败／退出码可分”测试没有测到这两件事。**

位置：[test_g3_5_vault_keyed_card_states.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:341)，关联 `:349-352`。

`_boom()` 在真正打开、截断或写入之前直接抛错，原文件从未损坏。因此，即使 `_restore()` 只返回 1、完全不复制备份，该门仍能通过。

它也没有制造回滚失败或断言 rc=3。该门证明的是“初始写入抛 `OSError` 后返回 1”，不能证明半写后的恢复与失败状态区分。

**M2．报告写失败仍会破坏整个 CLI 的退出码约定。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:461)，关联 `:260-263、:36`。

普通但不可写的报告文件，或不可写父目录中的报告路径，可以通过身份检查。迁移与重读校验成功后，`write_report()` 的异常未捕获，CLI 会退出 1。

此时输入已处于**迁移后状态**，不是文档约定的迁移前可信状态。新增 rc=1/3 区分只覆盖 `_restore()`，没有覆盖整个命令。

**M3．迁移器接受 service 无法读取的 vault 桶键，并报告成功。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:551](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:551)，关联 `:221、:534`；[review_service.py:413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:413)。

迁移器仅检查 `--vault-id` 非空并 `strip()`，随后直接用作桶键。例如 `--vault-id 'vault_a:subject'` 可以完成迁移并返回成功。

但 service 取的是 `group_id.split(":")[1]`，该结果不可能包含冒号。因此生成的这个桶无法被正常 `_bucket()` 选中。**内容重读一致，不等于迁移结果可被消费端读取。**

## LOW

**L1．“dry-run 不写任何文件”仍是错误声明。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:272)，关联 `:21-23、:304-317、:336-350`。

带 `--out` 的 dry-run 会创建目录、写报告；空迁移分支也可能写报告。成立的表述是“不修改输入快照、不产生迁移备份”。只有不带 `--out` 的 dry-run 才是零文件写入。

**L2．branch-decision 增加了限定，但没有清除与限定相反的断言。**

位置：[branch-decision-20260909T113301.md:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:66)，关联 `:68、:97-101`。

- `:66` 仍从“单个调用表达式不含检索串”推出“字符串方法在 review.py 上判不出消费方”；`:68` 又承认路由字面量命中 `fsrs-state`。
- `:97-99` 仍把括注的形成时间、作者预期及“预期被推翻”写成事实；`:101` 才承认无法确证。

按引用的条件式选甲可以自洽，但不能证明括注只是失效预测。**LOW-1 处置仍属部分完成。**

## 六条新增门的实际证明范围

以下是静态判断，不代表本轮执行通过。行号均属于 [test_g3_5_vault_keyed_card_states.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py)。

| 新门 | 判断 |
|---|---|
| 混合快照，`:228` | 能锁住“整体分类导致桶降格”；不能锁同桶冲突、归属正确或拒载后的数据保留。 |
| 纯嵌套快照，`:253` | 有效正控；旧 `all(dict)` 实现也能通过，不能单独证明 HIGH-1 修复。 |
| dry-run 输入／输出同路径，`:285` | 经 `main()` 且检查字节不变，能锁该直接反例；未覆盖 apply、链接别名。 |
| 报告指向现网，`:297` | 命中实际入口，但存在 H5 的测试安全缺陷。 |
| 现网硬链接，`:308` | 真实构造同 inode 不同路径，能验证 helper 的身份判断；不锁入口是否调用 helper，也不覆盖备份写点。 |
| 写失败回滚，`:332` | 未制造损坏、未测 rc=3，对所宣称的核心恢复能力证据不足，见 M1。 |

## 已核实成立的部分

- **两个 round-1 MEDIUM 已修复。** dirty 集的添加与查询已统一使用 `(vault_id, concept_id)`；稳定请求作用域下，A 的失败不再直接污染 B 的同名 concept。两处旧测试也恢复了明确桶、明确形状及原来的值／落盘断言，原持久化意图没有被削弱。它们仍不独立证明 resolver 选对了请求身份。见 [review_service.py:892](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:892)、[test_review_service_fsrs.py:785](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:785)、[test_g3_7_truth_source.py:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_7_truth_source.py:272)。

- **HIGH-2/4 原来的直接参数反例已堵住。** `--out` 在两种模式分派之前检查；输入／输出同路径、同 inode，以及直接传入的现网投影硬链接都有实际判断。**HIGH-3 的普通 `OSError` 路径也确实改进了**：写失败进入恢复，恢复复制或读回失败返回 3。备份与恢复的读回目前只验证 JSON 可解析，没有比较迁移前内容。见 [迁移器:528](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:528)、[迁移器:402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:402)。

- **数量与空操作分流成立，但不能只看退出码。** `n_old=0` 会提前返回，不进入备份阶段，报告为 `nothing-to-migrate`；非空路径存在净增判据、整体内容相等检查及重读计数检查。两种成功均返回 0；全为覆盖时净增也可以为 0。见 [迁移器:334](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:334)。

- **指定 GET 入口不需要新增 HTTP 参数。** `vault_id` 已声明，resolver 在调用 service 前注入 ContextVar，因此这次内部键化不要求改变该端点的 OpenAPI 形状。这个证据不能推广成“所有入口都经过同一注入链”。见 [review.py:1395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/api/v1/endpoints/review.py:1395)、`:1424、:1430`。

- **所列既有调用点没有发现 Mapping 方法缺失。** `get_history` 的 `bool/items()` 和 `get_cached_card_states` 的 `dict()` 都读取当前桶，持久化则导出全部桶。这与分桶目标一致；跨 vault “all” 是否仍有外部需求，限定读取面不能证明。见 [review_service.py:1959](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:1959)、`:2743-2754`。

- **LOW-2 的最新措辞成立。** `current_vault_id()` 没有兜住依赖异常，不能说“恒不抛”；正常缺 ContextVar 会回落 active vault。N2 的依赖故障注入能检验守卫敏感性，但“负控红了”不足以独立证明生产可达性，更不能证明正常启动会拒载。本轮没有核验负控运行产物；指定的 `require_read_group` 读取段也止于函数中途。见 [vault_scope.py:311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/core/vault_scope.py:311)。

- **按 census 定义计入端点层合理，选甲的条件论证成立。** 定义包含经公开 API 间接消费，因此 `review.py` 可以计入；N 是文件数，不是请求流量。全部非所有权消费方消失时，定义上可取 0，当前没有流量不会使 N 变成 0。本轮确认了定义与引用一致，没有扩大读取去重新穷尽整个仓库。见 [census:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:15)、`:248-255`。

- **真相源与 TOCTOU 的登记方向准确。** `CANVAS_BASE_PATH` 仍是进程级配置，投影分桶不能证明一进程多 vault 的真相源隔离；键化也没有关闭真相源读取后的等待窗口。本轮发现的 legacy 覆盖／删除是本卡另外带来的风险，不能由“真相源缺口另卡处理”涵盖。见 [frontmatter_signals.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/frontmatter_signals.py:35)、[review_service.py:2805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2805)。


