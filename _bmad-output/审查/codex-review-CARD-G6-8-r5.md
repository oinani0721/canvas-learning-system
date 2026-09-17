> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-8 round-5（上限轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-8-r5.md)"`
> 审查绑定: `33ede99d49f46663e6105ad6186d775917ff3e38`（本轮送审时的 HEAD，也是最终代码树）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: gpt-6-astra`（stderr :5） / `reasoning effort: ultra`（stderr :9）

---

**本轮不通过：BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1。**  
绑定最终 HEAD：`33ede99d49f46663e6105ad6186d775917ff3e38`。按 D-15，第 5 轮仍有 HIGH，车道应停下交主 session 人审。

1. **HIGH — 模板冻结没有绑定最终模板。**  
   [g68_five_view_contract.py:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:591) 只读取第一次字符串常量赋值，后续模板加工未覆盖。负控输入：在模板后追加：
   ```python
   _PAGE_TEMPLATE = _PAGE_TEMPLATE.replace(
       "const due = humanizeDue(", "const due = Number("
   )
   ```
   **实测门仍 PASS、报告旧两行，但实际模板两处均变成 `Number(...fsrs_due, nowMs)`。** 这直接违反本轮收窄后的“调用点没变过”，无需评判 JS 语义。

2. **MEDIUM — 非字符串绑定仍可遮蔽共享名。**  
   [g68_five_view_contract.py:480](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:480) 未检查 `ast.MatchAs`、`ast.alias`，随后裸名读取又因同名 import 获豁免。负控输入：
   ```python
   def _d(value):
       match value:
           case _BUCKET_ORDER:
               return list(_BUCKET_ORDER)
   ```
   实测 PASS；`from collections import deque as _BUCKET_ORDER` 后再调用该名也 PASS。两者都是静态可见的普通绑定语法。

3. **MEDIUM — 节点锚与排除集仍能同步缩减。**  
   [g68_five_view_contract.py:1004](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:1004)。对照输入：从 `FIXTURE_BUCKET_NODES` 删除 `("板-到期","规范到期")`，将其加入 `_EXCLUDED`，并在共享提取层过滤该节点。实测实际对账语句、节点身份检查及所得矩阵均通过。**这是三处同步变化的路径**；排除集没有独立核验节点确实属于 ineligible。

4. **MEDIUM — 标题重建与生产输出共用同一个判定来源。**  
   [g68_five_view_contract.py:1097](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:1097)。对照输入：在内存中的 `_title` 函数固定使用 `board="板-未来"`；推荐板为“板-新卡”时，生产标题与重建期望都变成“📚 今日复习 · 板-未来”，相等检查仍通过。因此它能检查与生产器格式一致，却不能独立证明点名身份正确。私有函数改名或不兼容改签名则会抛错判红，不会静默失效。

5. **MEDIUM — `snoozed` 人话锚仍接受错误失败原因。**  
   [g68_negctl.py:329](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:329)、[test_g68_five_view_contract.py:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g68_five_view_contract.py:52)。负控输入：把调用末参写成 `snoozed_typo`。锚点唯一、语法合法，但执行先产生 `NameError`；其 traceback 经“没有产出报告”断言进入 `E ` 行，runner 仍得到 `FAILED=True、hit=True、ok=True`。**这是解析器层实证**；语法检查、捕获段截断和 SHA 还原检查均不能证明失败归因正确。

6. **LOW — 文本集合没有冻结调用点数量。**  
   [g68_five_view_contract.py:602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:602)。负控输入：在原调用后增加独立块 `{ const due = humanizeDue(n.fsrs_due, nowMs); }`，将调用行单独换行。实测调用由两处增至三处，去重后的集合仍相同，门 PASS。

其余问题的结论：

- **字符串误红边界仍在**：普通返回文案 `"不计算 fsrs_due，只显示投影"` 会判红；这是保守文本规则，不能解释为识别出了计算行为。
- **空白粒度**：行首尾空白变化通过；行内空白变化、拆成两行均判红。整行文本冻结对格式调整敏感，也不能替代调用位置与数量身份。
- **M5 未发现新增非确定性**：第二次调用保留固定 `now`，只清空 `snoozed`，不覆盖第一次的结果；两次独立子进程 stdout 相等检查仍有意义。
- **结构化码改善了归因，但未全部迁移**：本轮确证的是上述 `snoozed` 锚，不能据此认定所有 AST 人话锚都有同样问题。

验证采用限定源码、并行独立审查及内存对照；矩阵的 13 个声明产出方单字段改值均被拦下。未修改文件、连库或运行完整复习链，也未重跑会改写文件的 32 段 runner，因此不独立确认“32/32”。结束时 HEAD 与四个地盘文件保持不变。


