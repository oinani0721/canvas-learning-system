终裁：**需再一轮**。分级为 **BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 2**。

冻结、当前生产实现、硬边界和裁判命令本身没有 BLOCKER；但观测旁路移交、变异门完整性和最终文证冻结仍不足以验收。

## HIGH

1. **仍有第 12 处观测旁路，且 §十重新出现失实全称**

[`rag.py:419`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:419) 的 `/weak-concepts` 入口 `logger.info` 仍在业务 `try` 外：

- 基线：HTTP 200，service `await_count=1`
- patch `logger.info` 抛错：HTTP 500，`await_count=0`

同端点 [`rag.py:441`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:441) 还有第二处：

- service 抛 `RAGUnavailableError` 时基线为结构化 503
- patch `logger.error` 抛错后变为裸 500

两处都是 HEAD 存量债，不是本卡新引入，也不属于本卡四个主端点；可以移交，不强求本卡修。但 [`验收单:964`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:964) 又写成“**全部**绕过点”“**全在**硬边界外”，直接违背前文“不宣称列全”，且 `rag.py` 本身就是本卡修改文件。

建议：删除全称，将 `rag.py:419/441` 显式并入 `CARD-OBS-nothrow-logging`；若本卡顺手闭合，则用统一 no-throw adapter 并补真实路由门。

## MEDIUM

1. **`judge_kill` 第三版仍可假杀**

[`mutation_gate_check_g43.py:385`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:385) 使用子串匹配。合成结果可复现：

```text
M10 预期 healthy_states...，实际只有错误参数 [ok] 失败
judge_kill(...) -> True
```

同样，`test_items_payload_shape_unchanged_but_unrelated` 也能匹配预期短串；同一 nodeid 因 fixture 崩溃而红，也会被当成正确原因。参数 ID 变化本身不易漏判，但恰恰因此丢失了 `[empty]` 实例绑定。

建议：

- 登记完整 nodeid，M10 精确到两个 `[empty]`
- 用集合精确匹配，不用 `e in a`
- 同一 pytest 进程记录 collected、call phase、FAILED/ERROR 和断言指纹
- 任意 ERROR 均拒绝判杀

`rc==1` 本身确认无问题：对本卡普通断言型变异，1 才是 `TESTS_FAILED`；2–5 分别是中断、内部错误、用法错误、无测试，拒绝它们是合理的 fail-closed。

2. **登记的 M12 真杀，但两个同型 M12 真存活**

三个 memory 模型字段在 [`memory_schemas.py:160`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/models/memory_schemas.py:160)、`:247`、`:580`。现 M12 只改第一处；值域门也只检查 `LearningHistoryResponse`，见 [`test_memory_four_state_api.py:636`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:636)。

隔离副本分别把以下字段改回 `Optional[str]`：

- `ConceptHistoryResponse.retrieval_status`
- `ReviewSuggestionsResponse.retrieval_status`

两次均为：

```text
79 passed, 148 deselected
collected=79
FAILED=[]
```

建议参数化检查三个模型的字段引用和值域，并新增独立 M12a/M12b 变异。

3. **HIGH-2 行为已闭合，但 §七之二仍是旧快照**

当前原样裁判实跑：

```text
79 passed, 148 deselected
PORT7691_SOCKET_CALLS=0
```

两个运行时文件前后集合、mtime、size、SHA 均未变化：

- `bug_log.jsonl`: `9fc67ea4f666ad6233e7b48492c19968a5987b41690a4fe23885243bc6d9b1aa`
- `vault_index_pending.jsonl`: `44623702d447997aa1b1b8f68c14fd2ece71a369d125b3adda546ec0fcac48ae`

但 [`验收单:867`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:867) 仍写 75 passed，`:873` 写新增 73，`:885` 写 pending 为 14,449 B；当前分别应为 79、77、14,020 B。

“跑了 4 次”没有淡化问题：文档明确承认越界、DDL、文件写入和未清理。但 exact 4 只有作者自述，现有证据不能独立证明，宜写“作者登记至少 4 次”或补逐次记录。

4. **验收单排除冻结不适合作为最终冻结**

19 个已登记文件确实全部匹配；但 [`验收单:610`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:610) 排除的正是主要声明载体。其当前 SHA 为：

```text
24551898a9344e8b1436b3d43adb9e2c2dc5fd9d923efe649a1b0eaa612fa95b
```

修改验收单不会触发 19 项冻结失败，因此不能证明“证据—声明同一快照”。

这个例外作为施工中草稿可以理解，作为终验冻结不合理。建议把整改流水拆为独立 append-only 日志；验收单最终定稿后，由版本化 manifest 将其纳入，并以 commit、签名摘要或外部复核报告锚定 manifest。

## LOW

- [`memory.py:268`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/memory.py:268)、`:323`、`:436` 的异常处理日志失败不会把成功变 500，但会把结构化 500 detail 遮成裸 `Internal Server Error`。应并入观测治理卡。
- “19 文件”正确，但“5 组”错误：冻结文件实际有生产、新测试、断言适配、登记文档、审查存档、证据共 **6 个** artifact 分组。

## 确认无问题

- 冻结：最终重跑 `count=19, mismatch=0`，HEAD 精确为 `9cf0fb85ed839bb7035d023534fca222a24d6968`。
- M10：仅两个 `[empty]` 门失败，均为 `spy.call_count 1 != 0`，真杀。
- M11：7 failed，预期门因缺少 `items` 报 `KeyError`，真杀。
- 当前 M12：2 failed，预期值域门因缺少 `ServiceStatus` 定义报错，真杀。
- 12 个变异共 18 个 patch 锚点，全部恰好命中一次。
- `rag.py:278-283` 的新 try/except 只包入口日志；subject ContextVar、service 调用和响应构造均在外面。新增门实跑 200 且 `query.await_count==1`，不会吞业务错误。
- 消费方证据：C 组确为 1 条非消费方命中；E 组确为 10 条，合计自检正确。
- 数字复算：

| 宣称 | 结果 |
|---|---|
| 77 = 47 + 30 | 动态 collect-only 确认 |
| 裁判 79 passed | 原样实跑确认 |
| 12 变异、各 collected 79 | 确认 |
| 302 → 379 | HEAD 隔离归档与当前树分别 collect-only 确认 |
| 243 → 320 | 两份 59-nodeid 失败集逐字相同，机械复算确认；未重跑会触发 live lifespan 的全量命令 |
| 46 failed / 33 passed | 隔离 HEAD 回放确认 |
| 15 项 | 11:45 快照成立；当前 raw status 为 16，新增项是 11:46 生成的零字节 round4 审查占位 |
| 冻结 19 文件 | 确认 |

- 硬边界：6 个生产/快照文件和 5 个既有测试共 11 个文件，`git rev-parse HEAD:<path>` 与 `git hash-object <path>` 全部相同。
- 共享工作树未被隔离变异污染；终局再次复核 19 项冻结仍全部匹配。

**明确终裁：需再一轮。** 最小闭合条件是：补 M12 两个存活变体、修 `judge_kill` 精确因果绑定、修正 §七之二与 §十、将最终验收单及最终 79 条副作用证据纳入新冻结。弱概念端点的存量 HIGH 可以明确移交，不必强塞进本卡实施范围。


