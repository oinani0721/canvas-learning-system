**本轮确认：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 1。** 上轮 HIGH-1 的特定删除链已闭合；M-1、M-2 的生产修复成立，但测试覆盖和历史备份保证仍有缺口。

审查对象是 `card/u9-mastery` 当前工作区相对 `155d3361` 的改动，当前 HEAD 为 `fad58bfa`。全程只读，未运行测试、变异 harness 或连接数据库。已登记的大小写不敏感卷问题仍属条件性未闭合面，本轮不冒充已确认漏洞。

**MEDIUM-1：新增 M-1 测试没有覆盖原缺陷。**

位置：[test_g3_5_vault_keyed_card_states.py:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:496)，具体调用在 `:506`。

`test_dry_run_and_apply_use_the_same_vault_id` 实际只执行 `--apply`，随后检查桶键；没有执行 dry-run，也没有检查预览是否报告覆盖。

原缺陷恰好是“**apply 已经 strip，只有 dry-run 没 strip**”。因此，恢复原来的错误 dry-run 行为，这条测试仍可通过。生产修复正确，但“新增门锁住两种模式一致”的自述不成立。有效门应从同一初始快照检查 dry-run 的目标桶、覆盖警告，再核对 apply 结果。

**MEDIUM-2：两份本次备份互不别名，仍不能保证保留历史版本。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:402)，互比在 `:412–425`，实际覆盖写入在 `:452`。

可静态推出的反例：

```text
snap.json.bak.<本次时间戳> → snap.json.bak.<旧时间戳>
snap.json.bak             是另一份独立文件
```

旧时间戳目标是普通文件、`st_nlink == 1`，且不在受保护路径内时：

- 本次两条备份的 resolved 路径、inode 不同，互比通过。
- 现网闸通过。
- 第一次 `copy2` 跟随符号链接，覆盖旧历史备份。

已有同秒时间戳文件也会被直接覆盖，因为没有独占创建或已存在拒绝。

这**没有推翻本次双备份独立性**，但推翻了 `:408–411` 延伸出来的“保留历史版本”保证。时间戳备份需要拒绝已有目标及符号链接，才能支持更强承诺。

**LOW-1：新增作用域失败仍被上层日志归因为文件写入失败。**

位置：[review_service.py:2756](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2756)。

新增守卫在作用域不可解析时，尚未写入容器、尚未尝试写盘就返回 `False`；这里却统一打印：

```text
file write failed — card exists in memory only
```

“文件写入失败”的归因不实，也不能据此认为卡已保留在 `_card_states` 缓存中。底层另有作用域错误日志，因此属于诊断误导，未发现它绕过 fail-closed。

**已核实成立的部分**

1. **HIGH-1 的删除链确实闭合。**  
   [review_service.py:592](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:592) 检出同名后抛 `VaultScopeUnresolved`；loader 的 `:902` 只捕获文件读取、JSON 和编码异常，不会吞掉该异常。因此 `__init__:853` 无法完成，不会得到“跳过 legacy 后仍可保存”的服务对象。非冲突 legacy 会进入桶，落盘快照保留全部已接纳桶。

   **成立的保证是“不会因这两种 legacy 拒绝原因而继续保存、静默删掉它们”。无条件的“本卡保证不丢”仍过宽。** 归属仍是推定；既有读盘失败后返回空容器的路径、外部写者及所有存储故障，也没有因此获得不丢保证。这些不作为本轮新增缺陷重报。

2. **可用性代价明确，但未发现纯正常形态被新增冲突门误拒。**  
   任意一条与当前推定桶同名的 legacy 都会阻断整个 `ReviewService` 构造，**两份值完全相同也一样**，因为只比较 concept 名。纯扁平且作用域可解析、纯嵌套、不冲突混合快照均不会触发新增冲突门。

   这是用户已接受的统一拒绝策略。它证明“服务对象构造失败”，不能单凭这些切片进一步断言“整个 FastAPI 进程必然无法启动”。

3. **M-1、M-2 的指定生产修复成立。**  
   [迁移器:641](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:641) 将同一个 strip 后变量传给两种模式，原空白参数造成的隐藏覆盖路径已消失。`:412–425` 在任一次复制前比较双备份路径及 inode，覆盖静态正反向、链式符号链接和硬链接别名。上面的 MEDIUM-2 是历史文件覆盖问题。

4. **迁移器已有合理的失败分类，不能再按旧自述批评“还原失败也返回 1”。**  
   [迁移器:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:474) 已区分还原完成 `rc=1`、还原失败或还原后不可读 `rc=3`；写盘中途的 `OSError` 和编码异常也会进入恢复路径。备份失败则提前退出，不继续迁移源文件。

   持续磁盘满、持续权限拒绝仍可能导致恢复失败；恢复后这里只验证 JSON 可读，不能扩大成任意故障下的精确原文恢复证明。

5. **dry-run 和数量判据的准确边界成立。**  
   无 `--out` 的 dry-run 不写文件；有 `--out` 会创建目录并写报告，代码已说明。`n_old == 0` 提前退出且不产生备份，报告为 `nothing-to-migrate`；迁移完成为 `ok`，并核对完整落盘对象。两者都返回 `0`，所以**不能只看退出码区分**。

6. **端点注入链和分支论证的有界结论成立。**  
   [review.py:1424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/api/v1/endpoints/review.py:1424) 在调用 service 前注入作用域，已有 Query 字段足以支持本端点内部换键，无需因本次改动增加 HTTP 字段。它不证明所有后台或直接 service 入口都有请求注入。

   按 census 明确包含间接 API 消费的定义，端点计入合理，当前调用足以支持 **N≥1**；精确 N=1 仍受历史扫描范围限制。乙支是“所有非所有权消费方消失时”定义上可达。当前[分支文档:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:109) 已撤回“`/goal` 括注是失效预期”，本轮不应重复报这个旧问题。

7. **Mapping 语义一致，但没有证明全部调用方兼容。**  
   `bool/items/keys/get/__getitem__` 都选当前桶，`dict(states)` 所需协议存在；落盘另走全桶快照。[get_history:1919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:1919) 因此只回退到当前桶，其他桶非空不会使当前桶判真；`get_cached_card_states` 的 “all” 也确实收窄到当前 vault。未发现所读调用形式存在协议缺口，但限定读取面不足以证明所有历史调用方都接受这一收窄。

8. **两条旧测试的原有落盘断言没有被削弱。**  
   当前版本已不是“某个桶里有 cid”：分别在 [unit 测试:785](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:785) 和 [G3-7 测试:272](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_7_truth_source.py:272) 定点检查当前 vault、要求桶为 dict，并保留原来的精确值或存在性断言。它们仍不独立证明作用域解析正确，因为预期 vault 来自被测实现自身。

最后两项证据边界需要保留：`current_vault_id()` 只是**不会因缺少 ContextVar 主动拒绝**，并非任何执行下恒不抛；正常无请求上下文仍可回落进程 active vault。N2 源码展示的是故障注入场景，不能凭源码确认“变异实测红在指定断言”；所述 220 B 副本加载成功也不在本轮独立验证结果内。

进程级 `CANVAS_BASE_PATH` 和尚存的 await 窗口与登记一致：**投影键化没有闭合真相源多 vault 隔离，也没有闭合 TOCTOU。** 本轮未找到独立于这些既有边界的新增串库根因。


