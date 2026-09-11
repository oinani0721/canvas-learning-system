**结论：BLOCKER 0 / HIGH 3 / MEDIUM 3 / LOW 2。r2 不能判为全部关闭。**

审查期间 HEAD 从 `155d3361` 更新为 `3bc0ed9a`；五个代码文件的首尾 SHA-256 一致，以下结论适用于这份内容。全程只读，未运行测试、迁移器、变异 harness，也未连接数据库。下面的反例均为静态推演。

## BLOCKER

无。

## HIGH

**H1 — legacy concept 与 vault 同名时，隔离区仍会在成功保存中永久丢数据。**

位置：[review_service.py:540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:540)，关联 `:1003-1018`。

触发链：

1. 启动解析失败，输入 `{"vault_a":"legacy-card"}` 进入 `_orphan_legacy`。
2. 后续在合法 `vault_a` 下保存 `new-c`。
3. `to_nested()` 先生成 `{"vault_a":{"new-c":"new-card"}}`，随后 `setdefault("vault_a", "legacy-card")` 跳过旧值。
4. 保存返回 `True`，旧 legacy 已从磁盘消失。

因此“每次原样写回、不会丢”的承诺不成立。新增 H4 门使用 `orphan-c` 与 `vault_a`，没有覆盖同名显形点；r2 H4 只解决了不重名的情形。

**H2 — 隔离状态没有持久化，重启即可绕过“等待人工裁定”。**

位置：[review_service.py:582](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:582)，实际处理在 `:590-621`。

当前 A 加载：

```json
{"A":{"c":"A-new"},"c":"legacy-unknown"}
```

本次确实保留 `A.c`，并隔离顶层 `c`。但保存没有记录“此条已经被隔离”及原因；下次在 B 作用域加载，B 没有 `c`，加载器便自动把它归入 `B.c`，随后保存固化。

这与“直到有人用迁移器显式裁定归属”直接冲突。即使不换 vault，因启动故障被隔离的数据，也会在故障恢复后的重启中自动收养。新增 H3/H4 门都未覆盖保存后重新加载。

**H3 — live vault 内其他文件的硬链接仍能绕过现网闸。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:93)，关联 `:129-131`、`:253`。

受保护 inode 集合只包含 `LIVE_CARD_STATES`；live vault 的保护仅检查路径包含关系。

若 `/tmp/report.json` 是 live vault 内某个节点文件的硬链接，普通临时快照配合 `--dry-run --out /tmp/report.json`：

- resolved 路径仍在 `/tmp`；
- inode 不属于唯一收录的投影 JSON；
- 报告写入会直接截断 live vault 内的同一文件。

无需并发换链即可成立。r2 H1 对**投影 JSON** 的备份别名修复有效，但不能推出“整个 live vault 的等价写入均被拒绝”。

## MEDIUM

**M1 — 毒 legacy 留在隔离区后，会持续阻断所有合法保存。**

位置：[review_service.py:612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:612)，关联 `:1003-1028`。

输入为包含转义孤立代理字符键的合法 JSON：`{"\ud800":"legacy"}`。启动解析失败后，它进入隔离区。

之后任何正常 pending 都必须与该 orphan 一起进行 `ensure_ascii=False` 序列化和 UTF-8 写入，因此发生 `UnicodeEncodeError`。异常处理只撤回本次正常 pending，毒 orphan 留存，下一次保存继续失败。

旧加载器接受毒 legacy 的问题已有；**拒载后仍由隔离区把故障传播到后续全部合法保存**，是此次保留方案新增的失败路径。迁移器的编码测试没有覆盖 service 这条链。

**M2 — `--out` 可以覆盖刚生成的备份。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:139)，关联 `:367-379`、`:462`。

普通参数即可触发：

```text
--apply --file /tmp/snap.json --vault-id vx --out /tmp/snap.json.bak
```

报告只与源文件比较身份，没有与备份比较。迁移成功并验证后，报告覆写简单备份，仍返回 0。

通常时间戳备份尚在；若两条备份路径原先互为链接，则两份备份可同时被报告破坏。因此“双备份”和报告作为独立附属产物的保证不完整。

**M3 — 分桶没有解决跨实例、跨进程的整份快照覆盖。**

位置：[review_service.py:920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:920)，关联 `:984-1011`。

两个 service 实例先读取同一旧快照；实例一保存 A 桶，实例二随后依据自己的旧内存保存 B 桶，整份替换文件，A 的新增桶及隔离条目就会消失。**顺序写入也能触发**，无需同时写。

这是继承的持久化机制缺口，不应算成此次新造的竞态；但本卡保证必须限定为“共享同一容器实例”。“一进程一 vault”也不足以排除两个进程共用这份文件。新双 vault 门只使用一个 `svc`。

## LOW

**L1 — r2 L2 所称“正文已改”与当前分支裁定不符。**

位置：[branch-decision-20260909T113301.md:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md:66)，关联 `:97-101`。

- `:66` 仍从单个调用表达式不含检索串，推出字符串方法“在 review.py 上判不出”；但 `review.py:1383` 就含 `fsrs-state`。`:68` 的限定没有删除前文错误结论。
- `:97-99` 仍断言括注的形成时间、作者预期及“预期被推翻”，`:101` 又承认无法确证。

结尾交主 session 复核已落实，正文中的过强断言仍在。该问题不推翻按 `N≥1` 选甲。

**L2 — 报告尚未写入，输出已经宣称写成。**

位置：[migrate_fsrs_card_states_vault_key_g35.py:298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/scripts/migrate_fsrs_card_states_vault_key_g35.py:298)，关联 `:300`、`:329-343`。

dry-run 先打印“本次写了一份报告”，再调用可能失败的 `write_report()`；其返回值未消费。`n_old==0` 路径也宣称“未做任何写入”，之后仍可能写报告。r2 L1 的文档措辞改善了，运行输出仍未完全一致。

## 已核实成立的部分

以下是当前代码和测试结构的静态确认，不代表本轮执行通过。

- **端点已有所需 HTTP 参数。** `review.py:1395-1401` 已有 vault/subject/group Query，`:1424` 注入后在同一异步调用链进入 service。这个入口的键化不要求新增参数或修改 OpenAPI 契约；不能据此推广为所有入口都经过注入。

- **端点计入消费方合理，选甲有足够依据。** 按 census 的静态消费文件定义，端点经 service API 间接消费也计数。现存调用足以支持 `N≥1`；乙在所有非所有权消费关系消失时定义上可达，当前无流量不会令 N 归零。本轮没有重新扫描全仓证明“恰好只有一个”。

- **Mapping 没有把 vault 桶误交给既有卡处理循环。** `get_history` 的 `__bool__` 与 `items()` 都指向当前桶，循环仍拿到裸 concept 与 card；`dict(self._card_states)` 也取得当前桶。`get_cached_card_states` 的范围确实收窄，不能再作为跨 vault 汇总接口。限定读取面内未发现缺失 Mapping 方法导致的直接调用错误。

- **无 ContextVar 不等于解析失败。** `current_vault_id():311-318` 正常回落到进程 active vault，但未捕获依赖异常，因此“恒不抛”并不严格成立；当前新增注释已修正这一绝对表述。正常启动自动推定 legacy 归属及配置漂移风险，也已明确登记。

- **r2 H1/H2/H5、M1 的直接修复成立。** 两条备份路径都在任何 `copy2` 前过闸；写盘捕获 `ValueError`，覆盖 `UnicodeEncodeError`；现网拒写测试使用 tmp 替身；中途失败门确实先截断再抛；还原失败门允许两次备份成功，再拒绝还原并要求 rc=3。备份失败在源写入前退出，写入失败进入还原，恢复失败或恢复后读不出则返回 3。

- **这些门仍有明确覆盖上限。** 编码门只要求 `rc∈{1,3}`、非空且可解析，没有要求精确恢复原内容及正常恢复时严格 rc=1；备份保护门只构造了简单备份路径。N2 只断言返回值、磁盘和日志，未直接检查全部内存桶；“变异后红在点名断言”的运行证据本轮未认证，也不能由它推出正常缺上下文就会拒写。限定的 `vault_scope.py` 读取范围还截在解析函数中途，未覆盖故障转换尾部。

- **r2 M2/M3 的直接改动成立。** 常见报告写入异常不再改变主流程退出码；apply 确实拒绝 `:`、`/`、`\`。这分别受报告与备份别名问题、尚未证明完整 vault 规范化一致性的限制。不给 `--out` 的 dry-run 没有文件写入代码。

- **两处旧落盘断言没有按提示所述被削弱为“任意桶包含”。** 当前 unit 用例定位桶、检查 dict 并比较精确卡值；regression 定位桶并检查 cid。原来的落盘目的保留。不过期望 vault 来自 service 自己的 `_dirty_key()`，它们不能独立证明 vault 解析正确。

- **未发现第二处同类 patch 撤销事故。** H4 现在只恢复两个作用域符号，保留 `_CARD_STATES_FILE` 的 fixture patch。新测试全文没有可执行的 `monkeypatch.undo()`；其余宽 patch 的恢复边界也未发现同类问题。这不等于独立认证事故清理和零写复跑结果。

- **真相源及 TOCTOU 的核心登记属实。** reader 仍使用进程级 `CANVAS_BASE_PATH`；真相源读取后仍有 await 和锁等待，键化没有关闭窗口。代码没有证明请求 vault 与真相源目录相匹配，因此“下一次 GET 必然纠正”也必须保留此前提。


