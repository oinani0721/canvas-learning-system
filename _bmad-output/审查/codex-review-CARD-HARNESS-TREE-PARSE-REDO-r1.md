> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-HARNESS-TREE-PARSE-REDO round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO.md)"`
> 审查绑定: `08100483..f7f10be4`（该轮的 HEAD = `f7f10be4`；本轮之后按其 MEDIUM/LOW 改代码 ⇒ HEAD 已前进到 `4d21bc9b`，故本轮**不绑最终 HEAD**，见 r2）
> 会话头自证（抄 .stderr 前 12 行中的三条，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

复核绑定确认：HEAD 为 `f7f10be4`，父提交为 `08100483`，三个代码文件与提交一致。**降级分支的收口不成立。**

**BLOCKER：无。**

**HIGH：无。** 当前证据证明到解析与选树层，未证明真实缺库环境最终完成错误写入。

**MEDIUM：**

- **降级扫描仍会接受与 PyYAML 不同的值，或漏掉合法键后静默回退。** 位置：[SKILL.md:410](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:410)，涉及 `:411–424`、`:445–453`。

  单行配置的 Python repr 为 **`'harness_tree: /repo\x85\n'`**：`\x85` 表示文件中的实际 **U+0085** 字符。

  | 解析分支 | 得到的值 |
  |---|---|
  | PyYAML 6.0.3 | `'/repo'` |
  | 降级正则 | `'/repo\x85'` |

  PyYAML 将 U+0085 视为换行；正则的 `[^#]*?` 将它吃进路径，且已经命中 `_canon`，不会进入 `_loose` 拒绝分支；若带该字符的目录具有 `backend/scripts`，错误树照样放行。

  同一缺口还有两种直接反例：`harness_tree: /repo\n  more\n` 分别得到 `'/repo more'`、`'/repo'`；合法单行 `{harness_tree: /B}` 则被两个正则同时漏掉，降级静默回退父目录。普通续行形态已用现有仓库路径只读实证：提取出的函数确实接受了截短后的树。

**LOW：**

- **新增六参数降级门的正常控制组对绑定树失明。** 位置：[test_g3_2_review_ledger.py:7384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7384)，断言在 `:7391`。例如配置为 `harness_tree: ../alt-harness-degraded-rel` 时，alt 和缺省树都可用，控制组只检查退出码；错误回退仍能通过，也没有检查实际写入。**整条门并非只看退出码**，其降级拒绝半段有告警、拒因和零写断言。

- **“以 OS 会打开的路径为准”仍有非严格解析边界，属于旧版已有问题。** 位置：[SKILL.md:452](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:452)。令 `ROOT` 为本仓库根，输入 `ROOT/canvas-vault/.claude/skills/quiz-answer/SKILL.md/../../../../..`：原路径因中间段是文件而不可遍历，但默认 `strict=False` 的 `realpath` 得到 `ROOT`，随后目录检查通过；已只读实证函数返回 `ROOT`。原 `normpath` 也有此行为，不能算本卡新增回归。

其余问题的核对结果：

- **Q1：** 对有效、可遍历的 symlink，相对目标、多重链和 `.`／`..` 混排由 `realpath` 逐段处理；没有残留的先行 `normpath`。新增 M-a 门只覆盖其中一种布局，不能证明全部边界。
- **Q2：** [SKILL.md:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:434) 的 **yaml-first 四态均回退**：非 dict、缺键、`None`、空串，已用提取出的函数验证。但缺库分支会拒绝 `harness_tree:`、`harness_tree: null`、`harness_tree: ""`；“分界不变”不能跨分支宣称。
- **Q3：** [SKILL.md:442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:442) 对整份 YAML 解析错误抛 `SystemExit`，不回退。即使 TAB 错在其他键，也会拒绝。措辞明确说“config 不是合法 YAML”，随后说明 harness 绑定不可证，并保留解析器位置，**没有把错误直接归咎于 harness_tree 键**。异常处理骨架与 F1 相同，另有文件读取的 `OSError` 回退。
- **Q4：** 既有 16 个 nodeid 的断言未变，解析结果与期望一致：五参数依次为保留 `#alt`、剥除注释、`ScannerError`、保留 U+3000 与 `#alt`、保留 NBSP 与 `#alt`；值首 U+3000/NBSP 也原样保留。TAB 门原本只要求非零码与零写，更新说明而保留断言恰当。
- **Q5：** [测试探针:7314](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7314) 确会使 `import yaml` 抛出 `ModuleNotFoundError`，属于 `ImportError`；每条门还检查该分支专属告警，未发现当前代码不进入分支却通过的路径。`finally` 删除占位后恢复后续可导入性，但没有恢复可能预先存在的模块对象，因此不是严格的原状态恢复。
- **Q6：** M-a/M-b/M-c 六个主门及降级 canonical 门都有破坏错误树／缺省树和账本断言；失明范围限于上述 LOW 所指控制组。

未运行会写盘的 pytest、未联网或连接数据库。三处 lint 基线更新可由 diff 确认，当前 SKILL 摘要与新基线一致；历史“全部通过、先红后绿、负控后逐字恢复”仅有验收单自述，本次未读取范围外日志，不能独立认证。
