> 批次: BATCH-2026-09-11-第十四批 · 车道 T4 · 卡 CARD-U9C-EVAL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)"`
> 审查绑定: `463fe762593db1f3d7f27aa76a2df0ad4b8b3379`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr，括注各自行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

已核实分支、HEAD 和单提交范围。**核心声明 B 不成立，当前交付物需要更正。** 本次未运行 pytest、生产工厂或数据库；运行了不写文件的 AST 变异检查。

**BLOCKER: 0**

**HIGH: 1**

**H1 — 最小测试 app 的屏蔽结果不代表生产 HTTP；生产路径会返回 CARD-G3-5 消息。**

依据：[新测试:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:209) 新建 app 并主动注册处理器，但本树生产代码没有调用 `register_exception_handlers`。生产 [main.py:694](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/main.py:694) 的 `CORSExceptionMiddleware` 捕获所有 `Exception`，在 `:735–741` 返回：

```python
{"code": 500, "message": safe_message[:500],
 "error_type": type(e).__name__, "bug_id": bug_id}
```

其中 `safe_message` 来自 `str(e)`，中间件在 `:757` 注册。

具体反例：singleton 为 `None`，持久化输入为 `{"vault_a":{"c":"A-new"},"c":"legacy-unknown"}`，前置依赖正常完成；请求 `GET /api/v1/review/history?vault_id=vault_a`。工厂调用位于 [review.py:693](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/api/v1/endpoints/review.py:693)，在端点 `try` 之外；构造触发 `review_service.py:593` 后，中间件返回含 CARD-G3-5 的 500。

这属于本卡声称的真实 HTTP 面，直接推翻[评估文档:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:169)及 `:239–245` 的结论。它也证明 **`code==500` 加 `bug_id` 并非排他性指纹**。完整测试另断言了固定 `message`，但测试 app 缺少生产中间件，因此仍可通过。

**MEDIUM: 3**

**M1 — “review 面每个请求持续 500，直到迁移”不成立。**

[评估文档:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:278) 推断 singleton 恒为 `None`、请求持续失败。现有代码有两个反例：

- 使用 H1 的冲突输入，请求 `/api/v1/review/fsrs-state/c?vault_id=vault_a`。[review.py:1459](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/api/v1/endpoints/review.py:1459) 在 `try` 内调用工厂，`:1507–1515` 捕获异常，返回默认 **HTTP 200**，包含 `found=False` 和带原文的 `reason`。
- 第一次用 `vault_a` 构造失败后，第二次改用 `vault_b`。[review_service.py:589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:589) 检查的是当前桶；B 桶没有冲突，`:602` 可以归入 legacy，随后构造成功。无需先运行迁移器。

两者都在本卡讨论的请求范围内。持续失败必须限定为“后续仍满足相同拒绝条件”，响应状态还取决于端点如何处理异常。

**M2 — 负控能检出函数入口无条件抛出，但不能保证检出 fail-fast 判定变成无条件。**

[新测试:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:165) 写“fail-fast 改成无条件抛，本条必红”；然而纯 nested 输入在 [review_service.py:561](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:561) 已返回，不会到达作用域解析及 `:565` 判定。

具体变异：把 `:565` 的 `if vault_id is None:` 改成 `if True:`。本次内存 AST 检查结果：

```text
baseline negative_control_pass= True
line565_if_true negative_control_pass= True
```

因此该负控的保证过强。**不能据此说四条测试全部仍绿**：同名分支的消息断言会检出这个变异。既有同族测试 `:245–252` 的“有效作用域＋不冲突 legacy”正控也能直接检出。

**M3 — 每次失败都重新建立 memory、graphiti 依赖的开销结论不成立。**

[评估文档:286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:286) 把重新调用依赖工厂等同于重新建立依赖。但 [memory_service.py:2908](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/memory_service.py:2908) 和 [dependencies.py:779](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/dependencies.py:779) 都会返回已有 singleton。

具体状态：依赖首次初始化成功，之后 `ReviewService` 构造失败。下一请求可以复用这些依赖；`ReviewService` 赋值失败不会清除它们。该反例就在文档声明的工厂控制流推演范围内。

**LOW: 2**

**L1 — 地盘核证据没有进入指定提交。**

[评估文档:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:441) 引用 `evidence-u9c-eval/territory-*.txt`，但 HEAD 不包含匹配文件；当前 `territory-20260916T145925.txt` 为未跟踪文件。干净检出该提交时，这条存档索引无法兑现。

**L2 — unit 存档的退出码与失败摘要冲突，不能作为 pytest 成功证据。**

[unit 存档:1180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/evidence-u9c-eval/unit-20260916T144844.txt:1180) 是 `35 failed … 29 errors`，下一行却为 `rc=0`，没有保存命令解释该退出码来自哪一层。这不证明失败由本卡引入，但不能把此 `rc=0` 解释为 pytest 成功。

其余复核结果：

| 项目 | 判断 |
|---|---|
| A | 唯一生产实例化点、脚本零命中、lifespan 不预构造均成立；不能由此推出所有相关请求均返回 500。 |
| B | **不成立**，见 H1。 |
| C | 被测 `from_persisted`、handler 和 `BugTracker` 行为确实是真实现；但“唯一替换路径”字面不准确，测试 `:70–75` 也替换了两个作用域解析函数。工厂未执行如实，生产 HTTP 链遗漏未充分声明。 |
| D | **成立**。摘要无条件含 `blocked=`；绿色存档 `:51–53` 确为零计数、4 passed、rc=0。 |

两个正例当前确实分别命中 `:570`、`:593`，消息断言都与对应分支吻合。HTTP 测试也确实同时断言了异常含消息、响应不含消息，排除了“根本没产生目标异常”的简单假绿；缺陷是生产路径代表性。同族覆盖有重叠，但新增消息断言没有口径冲突。

提交仅新增所述测试、评估文档及证据文件，`backend/app/**` 差异为空。未发现新增四例可达真实 Neo4j/LanceDB 的调用路径，bug log 请求期写入已重定向到临时目录；不过 Neo4j 摘要不证明 LanceDB 隔离，单个默认日志文件不存在也不足以证明“整个树零写入”。

**总体判断：零生产改动及未执行工厂的声明如实，但核心 HTTP 表征错误，覆盖边界声明不完整，当前不能按“事实口径已钉准”验收。**


