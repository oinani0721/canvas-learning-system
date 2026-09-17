> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-8 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-8-r4.md)"`
> 审查绑定: `dfc1c7e565f28274465a31aac89f0bef1e67b43b`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: gpt-6-astra`（stderr :5） / `reasoning effort: ultra`（stderr :9）

---

**round-4：FAIL。BLOCKER=0，HIGH=2，尚不满足 D-15 收口条件。**

绑定 HEAD：`dfc1c7e565f28274465a31aac89f0bef1e67b43b`。审查前后 HEAD 一致，四个地盘文件与该提交一致。

1. **HIGH — 普通常见的正则读取仍未被拦下。**  
   [g68_five_view_contract.py:523](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:523)  
   对照输入：`re.search(r"\bfsrs_due\b: *(.*)$", raw, re.M).group(1)`。实测能读取日期，AST 门却返回 `offenders=[]`：正则源码里的 `\b` 以字母 `b` 紧邻字段名，外层词边界匹配因此失败。`r"\Afsrs_due: …"` 同样未被拦下；bytes 字面量读取也未纳入检查。

2. **HIGH — 模板身份豁免允许页面自行判 due。**  
   [g68_five_view_contract.py:484](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:484)  
   对照输入：在 `_PAGE_TEMPLATE` 的真实 `queueLayersHtml` 中，将 `rows[b]` 换成：
   ```javascript
   rows[b].filter(r => Date.parse(r.fsrs_due) <= nowMs)
   ```
   实测 AST 门通过；运行模板原函数时，“同板未来”从页面消失。**赋值名仍在场，只证明名字没有变化，不能证明其中 JS 仍是纯消费方。**

3. **MEDIUM — 节点锚与提取结果同步缩减仍可通过。**  
   [g68_five_view_contract.py:909](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:909)  
   对照输入：从 `FIXTURE_BUCKET_NODES` 删除 `("板-到期","规范到期")`，同时让共用提取层过滤该节点；板内仍有“同板未来”，子集对账和节点身份检查均通过，现有针对“同板未来”的负控也仍成立。  
   **应做完整对账，但不能直接换成 `==`**：当前 `_declared_pairs` 还包含占位、测试节点，需要先独立明确排除集合，再核对完整分区。

4. **MEDIUM — 导入豁免跨越作用域，参数遮蔽未被拦下。**  
   [g68_five_view_contract.py:511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:511)  
   对照输入：`def local_order(_BUCKET_ORDER=("future", "new")): return list(_BUCKET_ORDER)`。实测门通过。参数属于 `ast.arg`，未进入赋值检查；局部读取又被模块的同名 import 豁免。

5. **MEDIUM — snooze 的“原本排首位”前提没有被验证。**  
   [g68_five_view_contract.py:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:336)  
   排序漂移后的对照输入：未消费 snooze 的队列已是 `[板-新卡, 板-脏日期, 板-学习中, 板-到期]`。集合完整，两道检查均通过。新增首位条件在当前非让位板非空的条件下，已被前面的分区检查蕴含。  
   应验证无推迟对照确实会改变排序；这里是**未约束的退化前提**，不是声称当前 fixture 已退化。

6. **MEDIUM — 重复省略号仍能把任意短前缀认作点名。**  
   [g68_five_view_contract.py:997](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:997)  
   对照输入：
   ```python
   prefix = "📚 今日复习 · 板"
   title = prefix + "…" * (TITLE_LIMIT - len(prefix))
   ```
   `rstrip("…")` 得到“板”，总长度又恰好满足上限，仍被接受。长度相等不足以证明真实截断。

7. **MEDIUM — 排障日志回流为 `E ` 行，负控失败归因仍会误判。**  
   [g68_negctl.py:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:466)  
   对照输入：合法 Python 负控打印 `snoozed`，随后抛无关异常。日志通过 `_run` 的断言消息成为 `E snoozed`，不属于 `Captured` 段。真实 pytest 输出实测得到 `failed=True、anchor_hit=True、runner_ok=True`。  
   正常 FAIL 仅含其他字段分歧、stderr 含 `snoozed`，也得到同样结果。归因需要绑定结构化字段或稳定错误码，诊断文本应继续展示但不参与匹配。

8. **LOW — 集合相等不检查队列重复项。**  
   [g68_five_view_contract.py:284](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:284)  
   对照输入：`ranked=[A,A,B]`、`yielded={B}`、期望集合 `{A,B}`，实测通过。若要声称队列完整，还需要唯一性检查。

9. **LOW — 普通函数说明文本会误红。**  
   [g68_five_view_contract.py:514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:514)  
   对照输入：给普通函数增加 docstring“显示投影里的 fsrs_due 字段，不计算到期”。实测抛出“独立 due 算法”。当前只豁免模块 docstring，因此不能将判据描述为只检查可执行读取。

另外两项定向结论：

- `due_nodes` 与 `ranked` **不是恒真比较**：允许读取的实现中，两者分别构造，只截短 `ranked` 会被拦下；重复项则见第 8 条。
- 在限定读取面内，**没有发现新增 `projection_day` 必须补登记的已知分歧**；这不代表已覆盖陈旧投影等其他时态。

本轮只读完成：直接执行的原有纯函数检查 **10/10 通过**，另做上述内存对照。确认 runner 定义了 27 段，但未运行会改写文件的原 runner，未独立复证“27 段全部通过”；未连库、未跑完整复习链。
