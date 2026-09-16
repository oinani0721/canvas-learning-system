> 批次: BATCH-2026-09-11-第十四批 · 车道 T4 · 卡 CARD-U9C-EVAL round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)"`
> 审查绑定: `b0abea797aa1edce1c1250949a751151428ff428`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr，括注各自行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

已核实 `card/t4-g3@b0abea797aa1edce1c1250949a751151428ff428`。**H1 核心整改成立，测试判别力已改善；但评估文档仍有事实概括错误。**

本轮全程只读，未重跑 pytest、未执行生产工厂；核对了存档，并进行了纯内存 AST 变异检查、消息截断计算及 zsh 退出码复验。

**BLOCKER: 0**

**HIGH: 0**

**MEDIUM: 3**

**M1 — “工厂调用包进 try，就返回 HTTP 200”仍不成立。**

- 依据：[评估文档:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:373) 写“包了就是 200 + reason”。但 [review.py:1225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/api/v1/endpoints/review.py:1225) 的 `/review/progress/multi/{path}` 在 `try` 内调用工厂，却只捕获 `CanvasNotFoundException`。
- 具体反例：依赖已初始化、ReviewService singleton 为 `None`、持久化数据含无法归属的 legacy；首先请求该端点，`VaultScopeUnresolved` 穿过 `try`，仍返回 **500**。属于本卡讨论的生产请求面。
- 应判断的是“是否捕获**这个异常，以及捕获后返回什么**”。`/review/fsrs-state/{concept_id}` 返回 **200＋原文 reason** 的具体结论正确。

**M2 — “依赖都是 singleton，重入不重建”整改过头。**

- 依据：[评估文档:362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:362) 将 memory／canvas／graphiti 一并概括为复用；但 [review_service.py:2976](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:2976) 每次直接构造 `CanvasService`，`:2982` 调用的工厂在启用且可用时也会新建 `FSRSManager`（`:756`）。
- 具体反例：memory、graphiti 已初始化，但连续两次因同一 legacy 冲突构造失败。第二次会复用这两个服务，同时**重新构造 CanvasService 和启用的 FSRSManager**。
- 这是本卡明确声明以只读证据覆盖的工厂中段。应逐项说明复用，不能概括为全部重建或全部不重建。

**M3 — 议题 α 仍把“注册 generic handler”列为脱敏办法，但本卡自己的新测试已经证明它单独无效。**

- 依据：[评估文档:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:399) 将“让生产真的注册它”与“给中间件加脱敏”并列；`:426–428` 又保留“加一个 handler”的移交建议。
- 具体反例就是[新测试:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:243)的现有配置：先注册全部 handler，再挂真中间件，结果仍返回原文。
- 因而**仅接上现有 generic handler 不会改变该路由异常的响应**，也不会处理 fsrs-state 已吞掉异常后的 200 响应。属于本卡交付的设计移交范围。

**LOW: 4**

**L1 — 中间件“生产最外层、捕获所有异常”的拓扑描述错误。**

- [评估文档:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:225)及新测试 `:246–248、:283` 沿用了错误注释。
- [main.py:757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/main.py:757) 后面继续添加 Encoding、CORS、Metrics；实际从外到内是 `Metrics → CORS → Encoding → CORSException`。
- 反例：外侧 Metrics 自身抛异常，内侧 CORSException 接不到。因此文档 `:394–395` 的“所有未处理异常”过强。**这不推翻本卡内部路由异常被它接住的结论。**

**L2 — 旧结论仍留在权威摘要和测试说明中，整改尚未保持全文一致。**

- [评估文档:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:100)、`:421` 仍写“持续／整片 500”；`:427` 仍以“运维看不到指引”为建议前提。
- [新测试:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:125)仍宣称“无条件抛出，负控必红”，与下面已经正确修订的 docstring 冲突。
- 具体反例：将生产 `:565` 改为 `if True:`，负控仍通过。其接住者确实是同名测试，而非负控。另一个小行号偏差：冲突条件实际在 `:590`，不是说明中的 `:589`。

**L3 — 实际提交范围比①申报的集合多两个审查文件。**

- base..HEAD 另外新增了 [round-1 审查文件:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/codex-review-CARD-U9C-EVAL-r1.md:1)和[审查 prompt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md:1)，均不在①列出的测试、评估文档、证据目录内。
- 两者都是审查辅助材料，**没有生产影响**；应更正范围申报。当前未提交的 prompt 修改及 r2 审查文件另行区分，不计入指定 HEAD。

**L4 — “HTTP 能直接看到完整迁移脚本名和 --vault-id 用法”不覆盖同名冲突分支。**

- 依据：[评估文档:286](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:286)作此保证；实际响应在 [main.py:739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/main.py:739)截取前 500 字符。
- 具体输入：`vault_a` 桶与 legacy 中有 **5 个相同的 36 字符 UUID 键**。纯 AST 求值得到消息长 **538** 字符，脚本名位于零基区间 `[491,532)`，响应只留下 `migrate_f`。此外，`:593` 分支完整原文本来就没有 `--vault-id`。
- 属于本卡明确覆盖的同名冲突分支。异常信息泄露结论仍成立，完整操作指引保证不成立。

其余重点复核结果：

| 项目 | 判断 |
|---|---|
| A | 核心成立：唯一生产构造点、脚本零构造、lifespan 不预构造均有当前源码支持。 |
| B／H1 整改 | 当前树没有生产注册调用；目标路由异常会由真中间件返回原文前 500 字符。反向更正正确。 |
| C／HTTP 判别力 | 被测函数、handler、中间件均是真实现。异常侧与响应侧断言有效；`error_type` 足以区分这两个确定候选层，`code＋bug_id` 单独不够。 |
| 两分支／负控 | 两分支消息断言吻合；AST 变异确认两条“接住者”正确。同族覆盖有重叠，无契约冲突。 |
| D | 更正成立；r2 存档确为三项零计数、**5 passed、rc=0**。 |
| 生产文件 | `backend/app/**` 两提交差异为空。 |

**零写证明与历史证据处置：**[零写存档:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/evidence-u9c-eval/zero-write-proof-20260916T190821.txt:4)充分支持“那次 pytest 前后，指定 bug log 的内容和 mtime 未变”，不能证明所有历史运行、全树或每一次写操作均为零。当前文件确为一条探针记录，hash 与存档一致；验伪追加及恢复后，当前 mtime 已是 **19:08:40**。污染自报、保留现场并交主 session 处置合理。

unit 原件保留并在 §6.5 更正也合理；我复验了 `$pipestatus` 被上一条 `echo` 更新的现象。该 `rc=0` 不能作为 unit 成功证据。新增测试未发现可达真实 Neo4j／LanceDB 的调用路径；Neo4j 有守卫存档，LanceDB 只有静态路径核查，文档已声明这一限制。

**总体判断：核心 HTTP 整改、零生产改动和主要覆盖边界披露如实，但文档仍有上述错误与残留矛盾，尚不能认定“事实口径已全部钉准”。**


