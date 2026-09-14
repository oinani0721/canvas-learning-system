> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-A · 卡 CARD-G3-9 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-9-r4.md)"`
> 审查绑定: `72b1cabd`（该轮送审时的 HEAD；**本轮 BLOCKER=0 / HIGH=0 且绑当时最终 HEAD ⇒ D-15 收口条件已达成**。
> 其后仍采纳 8 条 MEDIUM（含 2 条本卡自己引入的回归）并再送 round-5，属自愿加严，非门要求。）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

绑定 `72b1cabd5ac65d493292663f80a3b6c3271be52e`。**发现 8 项 MEDIUM；BLOCKER / HIGH 未发现。r3 修复尚未完全闭合。**

1. **MEDIUM — [g39_three_view_reconcile.py:486](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:486)**：`Request()` 仍在 `try` 外，实际向 CLI 传入 `--overview-url 'http://[::1'` 或 `127.0.0.1`，可观察到 `ValueError` 逃逸，未生成差异报告；现有测试只向 `open()` 注入异常，漏掉构造阶段。

2. **MEDIUM（新回归）— [g39_three_view_reconcile.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:139)**：将 `generated_at` 设为叶值 `1`、嵌套 500 层的数组，标准 JSON 解析成功、Node 插值正常得到 `"1"`，但脚本递归触发未捕获的 `RecursionError`，整次报告中断。

3. **MEDIUM — [g39_three_view_reconcile.py:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:373)**：新增零到期板、令其 `next_due={"x":1}`，并在 overview 补齐对应合法零板后，三面与 N5 两面均得到空差异，证明归一后的损坏没有另行报出；[回归测试:1030](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_g39_three_view_reconcile.py:1030) 使用缺少这些板的 overview，其宽泛断言可被“缺板”差异满足。

4. **MEDIUM — [g39_three_view_reconcile.py:607](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:607)**：宽松计数比较仍在 `607 / 787 / 877`，零卡投影设 `stats.due_nodes=false`，或只把 overview 零板的 `due` 改成 `false`，均能观察到空差异，布尔值漏洞尚未补全。

5. **MEDIUM — [g39_three_view_reconcile.py:313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:313)**：`upcoming` 为 `null`、对象、字符串或数字时被静默当作空数组，三面及 N5 均全绿；删除 `boards` 后提供对象形状的 `upcoming`，还会只留下 N4、N5 注释。

6. **MEDIUM — [g39_three_view_reconcile.py:405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:405)**：仅将基础夹具新卡 `n2` 的 `fsrs_due` 从 `""` 改成 `{}`，三面及 overview 缺席时均为空差异，非法排序原料被归一为空串却没有自检报错。

7. **MEDIUM — [g39_three_view_reconcile.py:666](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:666)**：node 自检只验字符串类型，将 `node` 改成空串或同板已有节点名，在 N5 下均观察到 `rc=0`，非空与唯一性仍依赖其他比较间接发现。

8. **MEDIUM（新回归）— [g39_three_view_reconcile.py:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g39_three_view_reconcile.py:149)**：设 `placeholder=[]`、板级 placeholder 全零、`stats.ineligible=0.0`，overview backlog 为 `0`，脚本唯一差异却是 `0.0 ↔ 0`；JS 两者都显示 `0`，且参照端点接受该输入，因此这是按 Python 类型严格比较造成的假红。

其余维度明确结论：

- **重定向：未发现。** 301/302/303/307/308 均未跟随；`Refresh` 不触发第二次请求。
- **连接失败被扩大捕获误判：未发现。** 当前平台六种 errno、DNS 失败及连接拒绝，直接异常和 `URLError` 包装均保留 N3。
- **浅层 JSON 插值判定：未发现。** 110 种形状与 Node 对照无分歧；问题在上述递归深度。
- **`not-comparable` 与数字比较：未发现。** 标记不会与数字相等，结构降级也会独立报差异。
- **自检上移：已成立。** 原有检查确实不依赖 overview；剩余问题是检查内容不足。
- **N1–N5：白名单分支未发现新增豁免路径，但输入尚未闭合。** 第 5 项仍可携带 N4、N5 全绿。

以上经指定源码、内存探针及省略 `--out` 的 CLI 交叉验证；未写盘、未连接数据库或启动后端，未复跑含写盘夹具的测试套件。


