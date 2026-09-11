**结论：缩小后的“不丢”声明仍不成立。** 键化核心未发现可证的串桶缺陷，但冲突 legacy 会被下一次正常保存永久删除。

本轮：**BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 1**。其中一项 MEDIUM 是文件系统条件反例。审查包含当前未提交回退；以下均为静态核验，未运行测试、变异 harness、迁移器或数据库操作，未修改文件。

**HIGH-1：冲突 legacy 的“未载入”，最终仍会变成永久删除。**

位置：[review_service.py:581](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:581)、[review_service.py:957](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:957)。

当前作用域为 `vault_a`，输入：

```json
{"vault_a":{"c":"A-new"},"c":"legacy-unknown"}
```

构造过程保留 `A-new`，跳过 `legacy-unknown`；`to_nested()` 只输出桶。之后任意成功保存都会用该全量快照替换原文件，冲突 legacy 没有备份或其他保留位置。

因此，fail-fast 只闭合了“作用域解析失败”的删除链，**没有闭合“作用域成功但发生冲突”的同一条删除链**。“同名冲突保留明确身份”成立，“本卡只保证不丢”不成立。

对应[测试:230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:230)仍称“不覆盖也不丢”，实际断言只证明桶内值保留，没有检查后续保存。

**MEDIUM-1：dry-run 与 apply 对 vault 参数的处理不同，预览会漏报覆盖。**

位置：[迁移器:620](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:620)。

输入为 `{"va":{"c":"explicit"},"c":"legacy"}`，两种模式均传 `--vault-id ' va '`：

- dry-run 原样使用 `' va '`，预览新桶，得到 `clobbered=[]`。
- apply 使用 `.strip()` 后的 `'va'`，实际覆盖已有 `va.c`。

只切换模式就改变目标身份及冲突结果。apply 自身仍会打印覆盖警告，但 **dry-run 没有预告实际执行会发生的覆盖**。

**MEDIUM-2：两条备份可以互相别名，“双备份”实际只剩一份。**

位置：[迁移器:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:409)。

预置 `snap.json.bak.<本次时间戳>` 为指向 `snap.json.bak` 的符号链接，不传 `--out`。现有检查只比较各备份与现网、各备份与报告，没有比较两份备份自身。

两次 `copy2` 会写同一文件；符号链接不会增加目标的 `st_nlink`，因此多硬链接闸也不拒绝。最终可以 rc=0 并报告两份备份，但后来覆盖简单备份时，“时间戳备份”也随之改变。

这不代表当次回滚必然失败，但双份备份及历史版本保留的保证不成立。

**MEDIUM-3：现网目录保护仍有大小写别名缺口，取决于文件系统。**

位置：[迁移器:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:94)、[迁移器:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:130)。

在大小写不敏感卷上，`canvas-vault/x.json` 与 `Canvas-Vault/x.json` 可以指向同一文件；`resolve()` 不负责统一实际路径大小写，而这里使用区分大小写的路径包含比较。

已保护 inode 集只包含现网 FSRS 单文件；普通 vault 文件若 `st_nlink == 1`，另外两道判据也不会挡住。新建报告文件还没有 inode，同样依赖这道路径判断。

**本轮未检查本机卷属性，未现场复现；这是条件性反例，不能表述成已确认现网可绕过。**

**LOW-1：回退的执行逻辑基本干净，但说明没有同步完成。**

[review_service.py:122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:122)及[review_service.py:873](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:873)仍描述解析失败时“该部分不载入”，实际会拒绝整个容器构造。

[测试:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:299)还保留“模块级 dataclass 自省”的说明，迁移器已经没有 dataclass。未发现已删除隔离区、保留键、认领或预检功能的悬空可执行引用。

**已核实成立的部分**

1. **fail-fast 在当前 loader 内确实有效。**  
   [构造异常:573](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:573)不会被[loader:888](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:888)捕获，会使 `ReviewService.__init__` 失败。这个路径没有用空容器继续覆盖原文件，比“忽略 legacy 后继续保存”安全。

   缺少请求 ContextVar 本身不会必然触发拒绝，解析链允许推导合法 active vault。**现网 220 B 文件及实际配置不在读取面内，本轮不能确认其启动结果。** 也只能确认 service 构造失败，不能将其扩大为整个后端进程及其他写者都已停止。

2. **Mapping 与 dirty 的当前调用面匹配。**  
   已检查到的 `get`、索引、包含判断、`bool/items`、`dict(states)`、回滚 `pop/setitem` 均有实现；`__eq__` 与普通 dict 比较当前桶。  
   [get_history:1905](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:1905)遍历当前桶；[get_cached_card_states:2639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2639)明确收窄了 “all”。dirty 使用 `(vault, concept)`，全桶快照成功后清空全部 dirty 自洽。允许读取面内未发现因此破坏调用方的证据，但不能证明所有外部调用方都接受该语义。

3. **该 HTTP 端点无需新增 vault 参数。**  
   [review.py:1395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/api/v1/endpoints/review.py:1395)已有 Query；`:1424` 在取得 service、执行 `:1430` 前注入 ContextVar。内部键化无需改变这条端点签名。此证据不覆盖后台、CLI、scheduler 等入口。

4. **题述中的两条弱测试已被进一步修正。**  
   [unit:785](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:785)及[regression:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_7_truth_source.py:273)现在检查当前 vault 的确切 dict 桶，分别保留完整状态值、写盘正控及 persisted/dirty 判据。原测试目的未被削弱。它们使用同一 resolver 推导预期桶，单凭这两条仍不能独立证明 vault 解析正确。

5. **分支裁定当前口径自洽，旧的意图越界已撤回。**  
   census 明确包含经公开 API 间接消费，因此端点计入 N 合理。“乙支可达”已在[分支裁定:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:80)限定为定义上的可能；[`:111`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:111)明确不再宣布 `/goal` 括注是失效预测。  
   本轮确认的是这些文档与可见调用链的一致性，没有重新全仓证明 N 总数，也没有认证读取面外的手册原文。

6. **迁移器的常规失败处理和数量分支成立。**  
   模式互斥；不传 `--out` 的 dry-run 无文件写入，传入则会写报告。`n_old == 0` 不产生备份，并明确报告 `nothing-to-migrate`；全部发生冲突时净增可以为零，仍与无需迁移区分。  
   写盘中途的 `OSError`、编码异常会进入回滚；备份失败发生于源文件写入之前。回滚写入或读回失败返回 3，正常恢复返回 1。**持续磁盘满或权限故障不保证能恢复，代码已区分退出码。** 回滚后的检查仅验证 JSON 可解析，没有验证与原始快照逐字相等。

7. **真相源和 TOCTOU 的限制登记符合实现。**  
   [frontmatter_signals.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/frontmatter_signals.py:35)确实使用进程级路径；键化未修改该 reader，也未增加锁内重读。[TOCTOU 注释:2697](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2697)承认窗口仍在是准确的。没有证据支持一进程多 vault 的完整隔离。

最后，**N2 不能承担生产可达性的全部证明**。[测试:177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:177)人为打断解析链，覆盖受控故障下的守卫；它没有直接断言内存未推进。历史“变异后红在点名断言”的输出本轮未读取，不能独立背书。`current_vault_id()` 也并非严格“恒不抛”：它不主动拒绝无上下文，但依赖调用异常可以传播；当前类说明已经修正了这一点。


