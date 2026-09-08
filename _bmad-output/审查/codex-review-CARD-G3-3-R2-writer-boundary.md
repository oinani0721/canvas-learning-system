> 批次: BATCH-2026-09-07-第十三批 · 车道 U5 · 卡 CARD-G3-3-R2-writer-boundary round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-3-R2-writer-boundary.md)"`
> 审查绑定: `609ce455`（= 承重裁判全部通过的独立 commit；HEAD 若不同须如实写）
> 会话头自证（抄 .stderr 前三行 + model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `--------`（续 `workdir: …card-u5-lance` / `model: gpt-6-astra` / `sandbox: read-only`）
---
本次仅做静态复核，未运行测试、写操作或连接网络、数据库。diff 确为 **5 文件，+536/-18**。以下“无”仅适用于许可读取面，不代表全路径已获证明。

**BLOCKER：无。HIGH：无。**

**MEDIUM**

1. **[SKILL.md:384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/canvas-vault/.claude/skills/quiz-answer/SKILL.md:384)**：`harness_tree` 的贪婪引号正则会吞入尾注释，空值后的注释也会被误当路径。  
   **观察**：`harness_tree: "/valid/repo" # use "main"` 被解析成 `/valid/repo" # use "main`；`harness_tree: # reset` 被解析为相对路径 `# reset`，均会错误拒绝。

2. **[test_g3_2_review_ledger.py:6775](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:6775)**：“任何写入之前”测试实际只检查部分残留新增路径，不能证明从未发生写入。  
   **观察**：改写已有节点、删除已有文件、创建后删除临时文件均可逃过该路径差集；`:6778` 还豁免了所有路径名包含 `.lock` 或 `quiz-answer` 的新增文件。

3. **[test_g3_2_review_ledger.py:6814](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:6814)**：显式配置正例使用 `vault.parent`，与默认回退路径相同，不能证明配置树被采用。  
   **观察**：若实现改成“检查配置目录存在，但最终始终返回 vault 父目录”，当前这些 harness 用例仍可通过。

4. **[test_learning_event_log.py:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_learning_event_log.py:149)**：拒因断言检查的是另一次直接调用 helper 的结果，没有绑定 `append_event` 实际经过的拒绝分支。  
   **观察**：输入 `None` 时，helper 报“必须是字符串”，但 `append_event` 在既有空判 `learning_event_log.py:254` 已返回；该测试仍通过。

5. **[test_learning_event_log.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_learning_event_log.py:245)**：两项一致性测试有承重，但不能锁住完整遍历行为或禁止集本身。  
   **观察**：仅把写门改成扫描 `event_id[:7]`，现有样本仍通过，却会漏掉 `quiz:xxx\u2028y`；另外，两侧同时删除 `(0xFDD0, 0xFDEF)`，范围相等、数量及现有锚点断言仍通过。这里仅指这两项测试，未推断整个测试集结果。

**LOW**

6. **[SKILL.md:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/canvas-vault/.claude/skills/quiz-answer/SKILL.md:337)**：`math.isfinite()` 先于范围检查，超大 JSON 整数会触发 `OverflowError`，绕过预定的清晰拒因。  
   **观察**：传入数值形式的 `10^400`；仍会失败退出，但不会得到“须为 null 或 0..1 的数”的受控错误。

7. **[test_g3_2_review_ledger.py:6757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:6757)**：合法值测试遗漏了科学计数法的 YAML 类型往返问题，这是原拼接方式的残留。  
   **观察**：`self_confidence_norm=1e-6` 通过新门，`:1587` 裸写为 `1e-06`，按同段已说明的 PyYAML/YAML 1.1 解析规则会读回字符串；这不属于本次新增的注入漏洞，也未证明会导致节点无法评分。

8. **[test_g3_2_review_ledger.py:6309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/regression/test_g3_2_review_ledger.py:6309)**：“方向判据”可以保留，但不能算当前执行到的身份保持证据。  
   **观察**：固定注入字符串在新门必被拒绝，`:6329` 起成功分支当前不可达；而新增 `:6693/:6711` 已要求同一输入必须失败，因此“删掉此分支就允许未来伪造”的解释过强。

对六个问题的补充判定：

- **入口到读取的数据流**：可见入口把合法数值写回为 `float`；`:1499` 正常分支读取 `p`，`:1513` 复放分支直接赋 `scn_=None`，没有从历史 payload 恢复该字段。不过，**`:421–1479` 的中间控制流、增量归纳块不在许可读取面内**，不能据此证明不存在重新赋值、重绑 `p` 或另一入口。

- **数字串与 `strip()`**：拒绝数字串本身是合理的类型契约，但普查明确承认历史 receipt 无法区分输入原先是字符串还是数字，因此不能证明所有历史调用都兼容。注释中“接受字符串就必须先 `strip()`，所以重开注入面”的因果不成立：若最后转换成有限、范围内的 `float` 并只使用该数值，被剥掉的字符不会重新进入 YAML。默认 `str.strip()` 会剥两端的 `U+0009–000D、001C–001F、0020、0085、00A0、1680、2000–200A、2028–2029、202F、205F、3000`，不会清除内部换行，也不剥 `U+200B/FEFF`；**只 strip 后继续裸插值字符串**才仍有问题。

- **字符口径**：两侧范围元组及可见逐字符 helper 的闭区间判定一致。完整形态门额外拒绝非字符串、空串、首尾空白和超过 512 字符，所以接受域更窄；例如 `" x"`、`"x\u00A0"`、513 个 `a` 不违反字符禁止集，但被形态门拒绝。未来若写门的禁止集更小，会出现“写入成功、读侧拒收”；若更大，则会提前拒绝读侧原本接受的值。许可范围在 `value_charset_problems` 的 docstring 内截止，未独立核验其完整字段分发体。

- **其他 harness 输入**：裸空值、`""`、`''` 回退父目录；指向文件则拒绝；相对路径相对 **VAULT** 解析。`backend/scripts` 是指向目录的符号链接时会放行，断链或指向文件时拒绝，这没有证明物理目录必须被限制在配置树内。简单引号内的 `#`、裸路径中不带前置空白的 `#` 会保留，普通裸值尾部 ` # 注释` 会剥除；异常情况见 MEDIUM 1。

- **拒绝测试的区分能力**：新增分数用例 `:6713` 确实检查实际 stderr 中的新门特征串；原转正测试仅检查账本零行，不能独立绑定拒绝层。harness 用例只检查 `"harness_tree"`，也不能精确区分预期拒绝与解析函数内部其他异常。

作者六条声明的核对结果：

| 声明 | 判定 |
|---|---|
| 1. 门在任何写入之前 | **部分确认**：位于 `evid` 之后；绝对零写未获证明，测试还明确豁免其声称门前创建的锁文件。 |
| 2. 读取、拼接未改，且唯一上游 | **未改成立；唯一上游未核实**，受中间代码读取边界限制。 |
| 3. 所有既有调用方均放行 | **仅枚举样本成立**；不能推广到所有输入，普查本身记载外部 ID 可控且新门属于收紧。 |
| 4. `CHARSET_STRICT_FIELDS` 未扩 | **成立**，diff 仅修改其上方注释。 |
| 5. 配置坏树不回退 | **对正确解析出的非空坏路径成立**；空值明确回退，注释解析存在上述缺陷。 |
| 6. 三个 harness 的 `--list` 完全相同 | **未核实**：许可材料没有对应输出，且本次禁止运行。 |
