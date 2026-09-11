**结论：r3 的修复部分成立，但尚不能认定全部闭合。** 本轮发现 **3 项 HIGH、1 项条件性 HIGH、2 项 MEDIUM、1 项 LOW**；未发现 BLOCKER。

审查对象为 `card/u9-mastery`，HEAD `3bc0ed9a` 加当前未提交改动，相对基线 `155d3361`。全程只读，未运行测试、迁移器或变异 harness，未连接数据库。以下反例均为静态控制流推演。验收单正文及 N2 执行日志不在指定读取面内，因此不能独立确认“登记完整”或“负控实跑结果”。

**HIGH**

**H1 — 保留键会吞掉合法 legacy concept，也允许迁移出不可消费的桶。**

位置：[review_service.py:611](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:611)，以及同文件 `:562–564`；迁移器 `:572–593`。

旧快照完全可能包含：

```json
{"__g35_orphan_legacy__": "{\"state\": 1}"}
```

加载器命中保留键，但值不是 dict，于 `:617` 直接跳过；既没有保留，也没有错误日志。下一次成功保存会永久删除它。**此反例不依赖这个名字是否是合法 vault ID。**

此外，迁移器允许 `--vault-id __g35_orphan_legacy__`，可以迁移成功并返回 0，但加载器随后把整个桶解释为隔离区。若内存确实存在同名 vault 桶且同时有 orphan，`:564` 还会直接覆盖该桶。

所以保留键目前只是约定名称，没有真正建立与业务键互不冲突的命名空间。

**H2 — 隔离区内部仍会静默覆盖同名条目。**

位置：[review_service.py:662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:662)、`:687`。

在 `va` 作用域加载：

```json
{
  "__g35_orphan_legacy__": {"c": "old-isolated"},
  "va": {"c": "bucket-card"},
  "c": "new-legacy"
}
```

新 legacy 与 `va.c` 冲突后进入 `orphan`，随后：

```python
{**already_isolated, **orphan}
```

把 `old-isolated` 覆盖为 `new-legacy`。解析失败时，`:662` 的合并也有同样问题。

因此“已隔离条目随每次保存原样保留”仍不成立：解决了隔离区与普通 vault 桶的位置冲突，却没有保住两份同名、尚未裁定归属的记录。

**H3 — 作者指定的迁移器无法裁定隔离条目的归属，却会报告无须迁移。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:221)，以及 `:238–248`、`:362–381`；对应 service 承诺在 `:601`、`:655–657`。

输入仅含：

```json
{"__g35_orphan_legacy__": {"c": "card"}}
```

实际流程是：

- `classify()` 把保留键当 vault 桶，得到 `n_old=0、n_new=1`。
- `--apply --vault-id A` 返回 `nothing-to-migrate`、退出码 0。
- 条目继续留在隔离区，完全没有归入 A。

混合输入也只迁移裸键，隔离区原样留下。加载器“与 classify 同口径”和“等待迁移器显式裁定归属”两项声明均被当前代码直接否定。类似地，legacy 被推定归错且已落盘后，指定另一个 `--vault-id` 也不会重新归属已有桶。

**H4〔条件性〕— 现网检查没有绑定随后实际写入的文件对象。**

位置：[迁移器:594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:594)，以及 `:599`、`:409–416`、`:476`、`:483`。

成立条件：另一个进程能够在检查后替换输入路径。

具体顺序：

1. 现网闸检查独占的临时副本，通过；随后读入该副本。
2. 另一个进程将该路径替换为指向 `LIVE_CARD_STATES` 的符号链接。
3. 后续只检查备份目的地；`copy2()` 和 `write_text()` 都重新打开输入路径。
4. 迁移结果写进现网，重读校验仍可成功，最终返回 0。

`st_nlink > 1` 修复了**检查时已存在的硬链接**，没有消除检查与实际打开之间的身份变化。这不是独占临时副本正常运行必现的问题，也未在本轮实测。

另外，大小写不敏感卷上的目录大小写别名仍是未闭合面：live vault 的检查使用路径父链比较，普通节点又不在受保护 inode 集内。本轮未核实卷属性，不能把这一条件风险写成本机已复现。

**MEDIUM**

**M1 — 毒条目预检遗漏已分桶数据，仍可阻断所有后续保存。**

位置：[review_service.py:618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:618)、`:643–644`、`:1048`、`:1054–1063`。

嵌套桶直接复制进 `_buckets`，只有 legacy 和隔离区经过预检。例如磁盘中使用转义写法的合法 JSON：

```json
{"va": {"c": "\ud800"}}
```

可以加载，却会让任意 vault 的下一次正常保存发生 UTF-8 编码失败。异常处理只回滚本次 pending，毒存量继续保留，后续保存继续失败。

因此，“加载时对每个条目预检”以及 `:1056` 的“存量条目必然干净”均过宽。r3 M1 的**毒 legacy**反例已处理，不能推广为整个快照都已处理。

对删除取舍还应明确：service 加载及保存流程没有先建立备份，日志也没有保存被删值。**若没有既存备份，下一次成功保存可能删除唯一副本；‘从备份恢复’不是代码提供的保证。** 验收单是否写明这一后果，本轮无法核验。

**M2 — `--out` 仍可通过时间戳备份的符号链接覆盖备份。**

位置：[迁移器:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:188)、`:198`、`:403–415`、`:499`。

静态反例：预置本次时间戳路径：

```text
snap.json.bak.<本次时间戳> -> /tmp/report
```

再指定 `--out /tmp/report`。

输出路径既不同于简单备份，文件名也不以 `snap.json.bak.` 开头，因此通过初检。时间戳备份经符号链接写入 `/tmp/report`；迁移成功后，报告又覆盖该文件。最终退出码为 0，但时间戳备份实际变成报告。

简单备份仍在，所以定为 MEDIUM。r3 M2 修复了直接命名路径，没有覆盖这个反向符号链接别名。

**LOW**

**L1 — `/goal` 括注意图仍被正文断言为事实，与限定块相互矛盾。**

位置：[branch-decision-20260909T113301.md:103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:103)，以及 `:104`、`:107`。

正文仍断言括注形成于排批时点，是对 `census=0` 的预期，而且已被实测推翻；限定块又承认没有形成记录，无法确证作者意图。

按条件式选择甲可以自洽，**不能由此证明括注只是失效预测**。r3 L1 指定的字符串搜索主句已改好，但同一文档另一处仍保留了它自己在 `:74` 批评的“主句过强、旁边追加限定”问题。

**已核实成立的部分**

- **r3 H1/H2 的普通场景已修复。** 非保留名的 legacy 与 vault 同名时，可以分别保存；保留键下的条目重载后不会自动收养。对应 service `:562–565、611–617`，新增测试 `:291–338`。这不覆盖 H1、H2 的新反例。

- **Mapping 覆盖了本文件现有调用方式。** `get_history` 的 `bool/items` 都取当前桶，不会把 vault ID 当 concept 遍历；`get_cached_card_states` 确实返回当前桶。见 [review_service.py:1989](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:1989)、`:2719–2730`。允许读取面内未发现具体调用方因此失效，但不能证明所有后台或仓外调用方都兼容此语义收窄。

- **已有 HTTP 字段与注入链支持本次不新增契约字段。** `review.py:1395–1399` 已有 Query；`:1424` 经 helper `:60` 注入 ContextVar；`:1430` 调用 service。该链支持 service 内部键化，不证明其他入口都经过它。

- **把端点计为消费方符合 census 定义。** census `:15–22、32` 明确包含经公开 API 间接消费；端点真实调用足以证明 `N≥1`，支持条件式选甲。乙在定义上仍可达，条件是所有非所有权消费关系消失；没有请求流量不等于 `N=0`。本轮没有重扫全仓来独立证明总数恰好为 1。

- **无 ContextVar 不等于解析失败。** 正常后台、CLI、启动路径会回落 active vault。`current_vault_id()` 也不是绝对“恒不抛”，其依赖异常没有捕获；当前新增注释已收窄为“不主动拒绝缺上下文”。legacy 随配置 A→B 重启而误归属、随后固化的后果，service `:582–593` 已明确登记。N2 源码确实注入推导故障并检查 False、未落盘和错误日志；即使负控实跑变红，也只证明该注入条件下的路径与测试敏感度，不证明正常启动会进入失败分支。

- **两处既有测试当前已不是弱 `any(...)` 断言。** unit `:785–791` 定点检查桶并精确比较卡值；regression `:273–276` 定点检查桶形状及 cid。原来的落盘目的保留了。不过预期 vault 来自同一个 `svc._dirty_key()`，不能独立证明作用域解析正确。

- **r3 H3 的硬链接拒绝成立，但有明确代价。** `st_nlink > 1` 也会拒绝完全位于私人临时目录的合法硬链接快照；这是保守策略的误拒范围。独立普通复制文件不受影响，不能泛称所有正常快照方式都不受影响。

- **迁移及报告控制流已有实质改进。** 不带 `--out` 的 dry-run 没有写入；带它会创建目录并写报告。空迁移在备份前退出，报告可与实际迁移区分，但两者退出码均为 0。备份失败时尚未改输入；写盘中途的 OSError、编码异常会尝试还原；还原或还原后重读失败返回 3，成功还原返回 1。持续磁盘满或权限变化仍可能导致还原失败，代码没有承诺必然恢复。r3 L2 两处提前宣称报告成功也已修正。

- **真相源与持久化限制仍然存在。** `frontmatter_signals.py:35–37` 仍使用进程级目录；本卡没有改掉这条路径，也未发现新增代码改变它。service `:2781–2785` 关于“键化没有闭合 TOCTOU”的补充准确。跨实例整份快照覆盖仍是继承问题；“共享同一容器实例内”这一收窄必要，不能推广为一进程一 vault 即可安全共用文件。


