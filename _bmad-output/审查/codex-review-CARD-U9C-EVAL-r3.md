> 批次: BATCH-2026-09-11-第十四批 · 车道 T4 · 卡 CARD-U9C-EVAL round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md)"`
> 审查绑定: `400a285924bb71e49cb8f9f257dfc3fdac36d607`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr，括注各自行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

已核对 `card/t4-g3@400a285924bb71e49cb8f9f257dfc3fdac36d607`。**核心 HTTP 整改成立，但仍有 2 项 MEDIUM、3 项 LOW。**

本轮只读，未重跑 pytest、未执行生产工厂；核查了源码、提交及存档，并进行了不导入生产模块的纯内存验证。

**BLOCKER: 0**

**HIGH: 0**

**MEDIUM: 2**

**M1 — round-3 将 `BackgroundTaskManager` 判为“每次新建”，引入了新事实错误。**

- 依据：[评估文档:416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:416) 写“每次新建”，`:419` 据此总结“三个对象真新建”。实际上，[background_task_manager.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/background_task_manager.py:91) 的 `__new__` 返回缓存的 `_instance`，`:99–101` 又防止重复初始化。
- 具体情形：同一进程连续两次因 legacy 冲突构造失败，第二次 `BackgroundTaskManager()` 返回原对象。我抽取原构造方法在内存中验证，结果为 `first is second == True`，既有任务状态保留。
- **属于本卡工厂重入评估范围。** 应改为复用该单例；FSRS 还须保留“启用且可用”的条件，不能无条件总结新建数量。

**M2 — 议题 α 仍保留“只注册 generic handler 即可落实屏蔽”的错误选项。**

- 依据：[评估文档:462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:462) 仍将“让生产真的注册它”与“给中间件加脱敏”并列；但同文 `:491–495` 已正确说明前者单独无效。
- 具体反例就是[新测试:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:244)：先注册 handlers，再挂真实中间件，响应仍包含原文。
- **属于本卡设计移交范围。** 后面增加正确解释，并没有消除前面仍然有效呈现的错误建议。

**LOW: 3**

**L1 — “singleton 恒 None／每个 review 请求都会重入”仍缺少必要限定。**

- 依据：[评估文档:427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:427) 作此概括；但 [review.py:1320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/api/v1/endpoints/review.py:1320) 的 verification-history 端点直接使用 graphiti，并不调用 ReviewService 工厂。
- 另一个具体序列：数据为 `{"a":{"x":"old"},"x":"legacy"}`，依赖正常；A 请求因冲突失败，B 请求成功初始化全局 singleton，随后 A 请求会在 [review_service.py:2953](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:2953) 快速返回，不再触发该冲突检查。
- **属于已讨论的工厂生命周期范围**，不依赖未探的 frontmatter 串库。宜限定为“singleton 尚未成功初始化、且实际调用工厂的请求”；持续失败还要求相关状态保持不变。

**L2 — 部分已更正结论仍未同步到全文及送审声明。**

- [评估文档:456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/2026-09-16-U9C-VaultScopeUnresolved-拒启-评估.md:456) 仍称“所有未处理异常都走这条路”。具体反例是外层 Metrics 自身抛错，内层 CORSException 接不到；这不推翻目标路由异常的结论。
- 同文 `:464–465` 仍以“工厂调用包进 try”概括 200 面。具体反例为 [review.py:1225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/api/v1/endpoints/review.py:1225)：在 try 内调用，但只捕获 `CanvasNotFoundException`，目标异常仍逸出。
- [送审 prompt:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/_bmad-output/审查/prompts/codex-prompt-CARD-U9C-EVAL.md:56) 的声明 C 仍写“唯一被替换的是 bug_tracker 落盘路径”，实际[测试:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:80)还替换了两个作用域解析函数。评估文档 §7.2 已如实列明，因此这是声明同步遗漏，并非被测层遭替换的新发现。
- 测试 `:44、:206` 也仍保留 HTTP 层单向“屏蔽”的旧概括。以上均属于本轮要求检查的残留口径。

**L3 — HTTP 测试钉住了消息子串，尚未完整钉住其宣称的“未脱敏原文”。**

- 依据：[测试:376](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_u9c_startup_rejection_eval.py:376) 声称同时钉住 `safe_message` 未脱敏；实际 `:417–418` 只检查 `CARD-G3-5` 和迁移脚本名。
- 具体反例：将响应消息中的绝对路径脱敏，但保留这两个子串，全部现有断言仍能通过。
- **属于本卡声称的回归覆盖范围。** 当前源码未脱敏的结论正确；若要锁住原文，可增加 `body["message"] == str(raised[0])[:500]`。

其余重点复核结果：

| 项目 | 判断 |
|---|---|
| 声明 A | 核心成立：唯一生产构造点、脚本无构造方、lifespan 不预构造均有源码支持。 |
| 声明 B | 成立：当前树未发现生产注册调用；目标异常逸出端点后由中间件返回原文前 500 字符。 |
| 声明 C | 被测函数、handler、中间件均为真实实现；“唯一替换”字面声明不成立，见 L2。工厂未执行的边界已披露。 |
| 声明 D | 成立：摘要无条件输出；整改后的零计数判据正确。 |
| 两个 fail-fast 分支 | 输入及消息断言分别对应 `:570`、`:593`，与同族测试无契约冲突。 |
| HTTP 分层 | 当前两个确定候选层可由 `error_type` 在／不在区分；共用 app 构造中，决定响应方向的变量确为是否挂中间件。 |
| 负控 | 无 legacy 输入提前返回，不能发现 `:565 → if True`；该变异由同名测试接住，冲突条件恒真由同族正常归桶测试接住。 |
| 截断整改 | 复算吻合：311／538 字符、`migrate_f` 截断、同名分支不含 `--vault-id`。 |

**关于 `:589` 的不采纳：可以成立。** [源码:589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:589) 确为冲突集合计算，且内部包含 `if cid in bucket` 判定；`:590` 才是外层 `if clobbered:`。不能把计算行引用一律认定为行号错误。若描述的是外层条件变异，则应明确写 `:590`。

**证据及范围处置：**

- 三个提交均未修改 `backend/app/**`，全部提交文件位于补充申报后的范围内。当前额外存在 prompt 修改及未跟踪 r3 审查稿，已与指定 HEAD 区分。
- 零写存档充分支持“**那次 pytest 前后，指定 bug log 的内容与记录的 mtime 未变**”，不能扩大为全树或所有历史运行零写。文档已声明该边界；污染自报、保留现场并移交清理合理。
- 未发现这五条测试可达真实 Neo4j／LanceDB 调用路径；两个已知日志写入别名均被重定向。Neo4j 有守卫存档，LanceDB 仍只是静态路径核查。
- unit 原件保留错误 `rc=0`、另行解释更正的处置恰当；不能将该行当作 unit 全绿证据。证据索引文件齐全，两个 scratchpad 脚本未随树交付，相关结果只能结合正文摘录和源码复核。

**总体判断：核心交付及主要覆盖边界披露如实，零生产改动成立；但 round-3 新增了单例判断错误，并残留上述矛盾，尚不能认定“事实口径已全部钉准”。**


