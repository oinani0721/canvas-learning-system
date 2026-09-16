> 批次: BATCH-2026-09-11-第十四批 · 车道 T4 · 卡 CARD-U9C-EVAL round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)"`
> 审查绑定: `27e40fac14a448d876689c7b95715383e7ff8c3e`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr，括注各自行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

复核绑定 `27e40fac14a448d876689c7b95715383e7ff8c3e`。本轮未重跑 pytest；完成源码、Git、存档交叉核对，并用无写入的内存实验验证了 FSRS 反例。

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 1**  
**LOW: 5**

**M1 — 五项依赖的身份判断基本正确，但后面的开销结论仍有事实错误。**

依据：[评估文档:442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:442) 写“三个 singleton 查表命中”，并称“py-fsrs 缺失时工厂返 `None`，新建对象数降为 1”。

具体反例：

- `USE_FSRS=True`、底层 `fsrs` 无法导入，但仓内包装模块可导入时，[fsrs_manager.py:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/lib/memory/temporal/fsrs_manager.py:25) 捕获 `ImportError` 并降级；`ReviewService` 侧仍认为包装模块可用。内存实测：工厂返回非 `None`、`library_available=False`，两次返回不同对象。**仍然新建 FSRSManager**。
- Graphiti 首次初始化失败时，`dependencies.py:798–815` 返回 `None`，未缓存成功实例；下一次仍尝试初始化，不能概括为“查表命中”。

均属于本卡依赖生命周期评估范围。`BackgroundTaskManager` 本轮修正本身正确；应区分“包装对象存在”“底层库可用”以及“依赖已成功缓存”。

**L1 — “每次重走实例化链并再次抛出”仍少一个限定。**

依据：[评估文档:368](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:368)，同样措辞残留于 `:452–455`。

反例就是文档自己的输入：`{"a":{"x":"old"},"x":"legacy"}`。A 请求冲突失败后，首次 B 请求满足“singleton 仍为空、实际调用工厂”两个限定，却成功构造。应补上：**本次数据与作用域仍满足拒绝条件时才再次抛出**。属于本卡覆盖范围。

**L2 — 对中间件捕获范围的收窄仍漏掉内层异常处理器。**

依据：[评估文档:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:483) 称“凡是从路由或更内层逸出、未被端点自己接住的异常都走这条路”。

反例：`review.py:1315` 抛出的 `HTTPException(400)` 未被端点捕获，却由内层 `ExceptionMiddleware` 的默认处理器处理，不进入 CORS 中间件的 `except`。这是文档对其他异常的扩展结论有误，**不推翻目标 `VaultScopeUnresolved` 的结论**。

**L3 — 新等式证明了本输入未脱敏，没有证明 500 字符截断上限。**

依据：[新测试:424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:424) 称等式“同时锁住了 `[:500]` 截断口径”，但当前异常只有 311 字符。

具体变异：把生产 `safe_message[:500]` 改成 `safe_message` 或 `safe_message[:1000]`，当前五条用例仍能通过。等式本身正确；应收窄覆盖说明，或使用超过 500 字符的输入验证上限。

**L4 — 测试说明仍有两处旧措辞未同步。**

依据：[新测试:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:392) 仍将“加专用处理器并真正注册”指认为当前议题 α；评估文档已将讨论改为中间件脱敏等处置面。`:206` 的整节标题也仍单向写“原文被屏蔽”，实际该节测试两个相反结果。

这是说明同步遗漏，不影响执行结果；也不意味着新增专用处理器在技术上必然无效。

**L5 — 运行证据的说明尚未与最终整改完全对应。**

依据：[评估文档:448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:448) 称“上表由读码得出，未在运行时观测过”，与 `:429–436` 三项运行时身份自证冲突。应区分“单独依赖探针已执行”和“完整工厂未执行”。

此外，[索引:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:818) 标为“当前”的日志来自 19:07，早于最终提交新增的完整消息等式。最终 commit 自报 `5 passed`，所以不能断言没跑过；但现有存档无法独立证明新增断言已通过。

其余重点核验结果：

- **A、B、D 的核心结论成立；C 的“两层执行、工厂中段只读”边界与实现一致。**
- 两个 fail-fast 输入和消息断言对应正确；HTTP 两例能区分当前两种处理实现，响应差异由中间件是否挂载决定。
- 负控不能单独检出 legacy 分支内部恒真，文档已诚实声明；指定的两个补充用例确能接住相应变异。
- `:589` 作为冲突集合计算行的引用正确，不采纳该行号意见成立。
- 四个 commit 的改动均在申报范围，`backend/app/**` 无改动。
- 未发现新增测试调用真实工厂或 LanceDB 的路径；Neo4j 守卫和两份日志重定向均在位。
- 零写存档支持**该次 pytest 对指定 bug_log 文件未造成变化**，不证明全树零写；文档已声明此边界。保留污染、交主 session 处理，以及保留错误 `rc=0` 原件并另行更正，处置适当。

总体判断：**核心交付物如实，主要覆盖边界诚实，但依赖事实、残留概括与最终证据对应关系尚未完全整改闭合。**


