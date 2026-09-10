**结论：存在 4 项 HIGH，建议修正后再验收。** 审查对象是 `card/u9-mastery`、HEAD `155d3361` 上尚未提交的工作区改动。以下均为静态审查；未修改文件、运行测试或变异 harness、连接数据库。

**BLOCKER**

未发现需要单列为 BLOCKER 的已证实问题。

**HIGH**

1. **legacy 自动归桶没有可靠的历史归属依据，正常启动不会因缺请求上下文而拒载。**  
   [review_service.py:529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:529)、[review_service.py:548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:548)

   反例：旧进程服务 vault A，留下扁平快照；配置改成 B 后重启。`from_persisted()` 会把全部旧数据归入 B，下一次保存将该归属固化。两个时点都可以满足“一进程一 vault”，所以这个前提推不出“当前 vault 是唯一可证归属”。

   无 ContextVar 时，解析链仍会推导进程 active vault；只有推导失败或结果不可信才拒绝。因此，“没有请求上下文”本身不会保护启动加载。

   另有条件性解析问题：混合快照 `{"A":{"c":"旧卡"},"d":"另一张卡"}` 会被整体当作 legacy，包入当前桶，已有 A 桶也被降格成 concept。迁移器能正确区分这两种条目，加载器却不能。

   文件顶部 `:120` 和 `_load_card_states:828` 所写“legacy 不加载”，也与实际实现直接矛盾。

2. **`--dry-run` 可以覆写输入乃至现网文件；`--out` 绕过全部目标检查。**  
   [migrate_fsrs_card_states_vault_key_g35.py:174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:174)、[同文件:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:223)、[同文件:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:411)

   `run_dry_run()` 会调用 `write_report()`，后者创建目录并覆写 `--out`。静态反例：让 `--file` 和 `--out` 指向同一份临时快照，原数据就会被报告 JSON 覆盖，且没有备份。

   现网闸只检查 `--apply` 的 `--file`，不检查 `--out`。同样的问题也影响 apply：重读校验成功后，报告写入还能再次覆盖刚迁好的文件。因此不仅“零写入”不成立，“校验成功后留下的是迁移结果”也没有保证。

3. **写盘中途失败不进入回滚；恢复成功与恢复失败也没有明确结果区分。**  
   [migrate_fsrs_card_states_vault_key_g35.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:295)、[同文件:301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:301)、[同文件:314](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:314)

   `path.write_text()` 在 `try` 外。目标被截断后若磁盘满或写入发生 I/O 错误，异常直接退出，完全到不了后面的重读／还原分支。

   普通、互不别名的路径下，各阶段行为是：

   - 备份失败：源文件尚未改写，但可能留下不完整备份，不能保证“双备份有效”。
   - 写盘中途失败：可能留下空文件或部分 JSON，不自动还原。
   - 重读失败后恢复：`copy2()` 自身未捕获异常，也没有恢复后验证。恢复成功显式返回 1；恢复失败异常退出通常也是 1，**仅看退出码无法区分**，只能从 stderr 获得额外线索。

   `migrate_neo4j_data.py:185–201` 的参照先例并没有提供覆盖这些失败阶段的保证。

4. **`resolve()` 比较路径，不能证明目标不是现网文件的另一个名字。**  
   [migrate_fsrs_card_states_vault_key_g35.py:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:60)、[同文件:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:75)

   同一文件系统中，现网文件的硬链接可以有不同的 resolved 路径、相同 inode。该闸会放行，随后 `write_text()` 截断的是同一个文件。`:60` 所称绑定“真正指向哪个 inode”超出了实现。

   两条派生备份路径也未检查身份；预置备份符号链接可能让 `copy2()` 写向保护目标。这是静态可成立的绕过条件，并非声称现场已经存在这些别名。

**MEDIUM**

1. **主状态增加了 vault 维度，持久化失败标记仍以裸 concept 为身份。**  
   [review_service.py:804](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:804)、[review_service.py:927](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:927)、[review_service.py:2801](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2801)

   B 的 `c` 已持久化，随后 A 对同名 `c` 写盘失败，`_unpersisted_concepts.add(c)` 会让 B 的缓存查询也返回 `persisted=False`。这是键化后附属状态维度不一致造成的跨 vault 误报；不代表 B 的磁盘卡被覆盖。

2. **两处旧测试保留了粗粒度正控，但断言弱于新身份所需的绑定。**  
   [test_review_service_fsrs.py:778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:778)、[test_g3_7_truth_source.py:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_7_truth_source.py:265)

   两条仍分别检查“某处落盘出现精确状态”和“某处落盘出现 cid”，没有被完全掏空。但现在正确身份是 `(vault, concept)`：当前桶内存正确、落盘却放进错误 vault，两个 `any(...)` 都可能通过。

   G3-7 的 `cid in bucket` 还没有检查 bucket 是字典，字符串包含该 cid 子串也可能满足断言。可以显式注入测试 vault 后检查对应桶，无须绑定用户配置。因此“一字不减”只能限定为“仍能检查发生过某种落盘”。

**LOW**

1. **分支选择总体自洽，但两段论证超出了证据。**  
   [branch-decision:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:66)、[同文件:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:70)、[同文件:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:91)

   “把三串检索搬到 `backend/app` 也仍然零命中”直接错误：`review.py:1383` 就含 `fsrs-state`，service 更大量包含另外两串。单个调用表达式不含检索串，不等于整个文件不含。

   乙支在抽象定义下可以达到 N=0，但需要所有非所有权消费者消失；没有客户端流量不能让现存端点消费者归零。

   把 `/goal` 括注判为“排批时对 N=0 的预期”，涉及形成时间与作者意图。限定读取面没有原始形成记录，不能独立确证。按文中引用的条件式选择甲可以自洽，并不等于已经证明括注只是失效预测。

2. **`current_vault_id()`“恒不抛”不是代码能保证的绝对性质。**  
   [review_service.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:370)、[vault_scope.py:304](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/core/vault_scope.py:304)

   函数没有主动拒绝无 ContextVar 的情况，但也没有捕获其依赖调用的异常。能确认的是“正常情况下回落 active vault，不能用缺 ContextVar 作为失败判据”，而非任何执行都不会抛异常。

**已核实成立的部分**

- **该 GET 端点不需要为此次键化新增 HTTP 字段。** [review.py:1395](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/api/v1/endpoints/review.py:1395) 已声明 `vault_id`，`:1424` 在 service 调用前注入作用域，`:1430` 仍传裸 concept。这支持“不必改变 OpenAPI 结构”；不证明所有入口都经过这一条注入链。census 还列出了 history、record 两个入口，其注入链不能由该 GET 片段代证。

- **Mapping 接口能承接所见既有调用形状。** [review_service.py:1893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:1893) 的真假判断和 `items()` 都作用于当前桶，迭代所得仍为 concept→card，没有把 vault 桶误当卡数据。`get_cached_card_states:2688` 也能通过 Mapping 接口构造字典。两者范围确实收窄；允许读取面没有证实依赖跨桶“all”的生产调用方。

- **N≥1 足以支持甲支，端点计入符合 census 自己的定义。** [census:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:20) 明确包含经公开 API 间接消费。一个文件三个调用点仍计一个消费者。这里证明的是静态消费关系；没有证明实际请求流量，也没有证明仓外消费者为零。

- **fail-closed 守卫有实质行为，但 N2 证据必须限定。** [review_service.py:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:430) 在解析返回 `None` 时确实拒写。[测试:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_5_vault_keyed_card_states.py:188) 人工打断解析依赖；若负控确在点名断言变红，可证明该故障注入条件下守卫受测试约束。不能据此推出普通启动／CLI／后台缺上下文就会拒写。本读取面没有负控执行产物，实际红点未独立核实；测试也没有直接检查全部内存桶前后不变。

- **迁移数量公式符合其覆盖策略。** [迁移器:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:251)、`:281–282` 能通过日志／报告区分“没有待迁项”和执行迁移；单看 exit 0 不行。全部旧键均覆盖已有键时，净增可以为零仍成功，所以 `migrated` 实际表示净增量。该判据不证明归属正确或没有覆盖损失。不给 `--out` 的 dry-run 确实没有写入路径；`n_old==0` 确实不创建备份。

- **进程级真相源和 TOCTOU 的未闭合声明准确。** [frontmatter_signals.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/frontmatter_signals.py:35) 没有按请求 vault 选目录；[review_service.py:2739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:2739) 也正确承认键化没有关闭读取真相源后等待的窗口。不能据此验收端到端多 vault 隔离。本卡明确新增的归属风险是上述 legacy 自动归桶；四个新回归用例另外也未覆盖重启加载、HTTP、迁移失败、并发或真实多 vault frontmatter。


