需整改——M2b 的 KILLED 裁定成立，138 条对账准确；需收窄三处“g32cb 已替代承重”的定性。

- **[MEDIUM] [codex-prompt-CARD-G3-2c-D.md:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/_bmad-output/审查/prompts/codex-prompt-CARD-G3-2c-D.md:56) — M1 没有覆盖 M143 的“缺失凭据拒绝”。**  
  实算 M143 旧锚命中 **0**；当前对应位置是 `SKILL.md:2067`，`:2085` 属于另一条状态矛盾检查。`g32cb_mutation_gates.py:150–151` 将严格 bool 判断退回“只拒 None”，**缺键仍被拒绝**；其测试 `test_g3_2_review_ledger.py:5211` 枚举字符串和整数，而缺键场景在 `:4734`。建议改为：“M1 证明非布尔值拒绝；M143 的缺失凭据变异本次未测。”

- **[MEDIUM] [codex-prompt-CARD-G3-2c-D.md:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/_bmad-output/审查/prompts/codex-prompt-CARD-G3-2c-D.md:57) — M2 打的是 foreign 恢复调用，不能替代 M145 的 dup 恢复调用。**  
  实算 M145 旧锚命中 **0**；当前 dup 提升仍在 `SKILL.md:2609`。g32cb M2 锚命中 **1**，定位到 `SKILL.md:2485–2486`，保留了 `:2609`。原门在测试 `:4753–4756` 重跑同一事件；M2 的门在 `:5309–5316` 由另一事件触发恢复。建议分开登记两个调用点，保留 M145 未测状态。

- **[MEDIUM] [codex-prompt-CARD-G3-2c-D.md:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/_bmad-output/审查/prompts/codex-prompt-CARD-G3-2c-D.md:58) — M3 打的是“缺方向证据时回落”，不是 M157 的“方向证据矛盾时拒绝”。**  
  实算 M157 **主锚 1、同层锚 0**；当前矛盾检查仍在 `SKILL.md:1857`、`:1881`。M3 锚命中 **1**，只修改 `:1893`，上述两处检查均保留。测试 `:5646–5649` 特意删除后继行的时刻和序数，场景也不同。建议写：“M3 已验证缺证据回落；M157 的矛盾方向检查本次未测。”

- **[LOW] [kill-table-138.md:99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/_bmad-output/审查/evidence-g32b/kill-table-138.md:99) — 主结果准确，但表内未呈现 M100/M151 的层声明失败及整体 FAIL。**  
  原始日志 `:174`、`:184` 明确记录变异体单独即可杀，`:191` 为整体 **FAIL**。因此“层声明过度”定性成立，这两项记录不能推出生产防线缺陷。建议在表首补充整体状态，并给表 `:99`、`:139` 加移交备注；**无需改动 134 的计数**。

- **[LOW] [codex-prompt-CARD-G3-2c-D.md:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/_bmad-output/审查/prompts/codex-prompt-CARD-G3-2c-D.md:20) — “status 只有证据目录”不符合当前工作树。**  
  开始观测为 **3 项未跟踪内容**，复核时为 **4 项**：证据目录、审查文档、提示文档，以及期间新增的本卡 UAT。暂存和未暂存 diff 均空。建议写“tracked 代码零改动，另有未跟踪证据及文档”。

**M2b 的独立复现结果：成立。** 我从 `MUTATIONS` 原条目提取替换文本，在隔离副本执行，未修改原仓库：

| 阶段 | pytest 退出码 | 实测 |
|---|---:|---|
| 基线 | 0 | 1 passed，3.28s |
| 变异，锚命中 1 | 1 | 1 failed，1.71s |
| 还原 | 0 | 1 passed，3.24s |

失败的是 [test_g3_2_review_ledger.py:1086](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:1086)：

```python
assert why in r.stderr, r.stderr
```

输入为 `2026-08-01T18:00:00+08:00`；预期拒因“非 UTC”，实际为“envelope 冲突”。前一条 `r.returncode != 0` **仍然通过**。这证明测试能够识别 UTC 检查被删除；此次击杀由**拒因身份变化**触发，不能扩大为“删除它后该样本成功写入”。

还原 SHA 为 `dd6d4e4b…fa73dbf`，与原始完整 SHA 相等；复制涉及的 **1253 个源文件内容未变**。隔离测试使用现有 venv，并设置本地配置 `DEBUG=true`、localhost CORS、`NEO4J_ENABLED=false`；此前配置加载的 `rc=4` 未计为击杀。[完整失败输出](/private/tmp/g32b-independent-m2b-m1z6qer_/mutant.txt:40)、[三态记录](/private/tmp/g32b-independent-m2b-m1z6qer_/result.json)、[可复现脚本](/private/tmp/g32b-independent-m2b-m1z6qer_/reproduce-m2b.py)。

**四条锚漂移成立，但只能静态确认防线仍在。** 除上述三条，M142 在 `g32b_mutation_gates.py:1563` 的旧 `bool(...)` 锚实算 **0**；当前 `SKILL.md:2098` 为 `(_rc_dup_applied is True)`，赋值逻辑仍在。M157 虽主锚命中，层锚失败发生在落盘前，整项跳过；不能算“主变异已经测过”。[独立计数记录](/private/tmp/g32b-independent-m2b-m1z6qer_/verify-anchors-history.py.txt:1)。

**138 条没有重算、漏算或把未测计为 KILLED。** 对脚本 AST、表格、原始日志分别解析，得到：

```text
MUTATIONS / 表格 / 原始主循环：138 / 138 / 138
KILLED / SURVIVED / ANCHOR-ERROR：134 / 0 / 4
重复 tag：0；顺序差异：0；绑定门差异：0；状态差异：0
134 条 KILLED 的对应原始行缺失：0
```

表格 `:9–146` 与日志 `:5–142` 一一对应；额外对照输出没有混入总数。表 `:5` 明示四条未测。问题在于后续的**替代覆盖解释过宽**，不在数值表。[完整对账观测](/private/tmp/g32b-independent-m2b-m1z6qer_/verify-evidence.py.txt:1)。

**旧 SURVIVED 原因仍未确定。** 我对比 `5a967446`、`2d03d767`、当前 HEAD：整个 SKILL 内容相同，M2b 测试及关键 fixture/helper 的 AST 相同。但 validator 确实改过，例如 `991ae914` 收窄字符校验字段；旧 UAT `:213` 的 schema SHA 也与本次不同。这证明历史代码并非全部冻结，**尚不能证明这些改动导致结果翻转**。

另一种可解释机制是人工还原或测试提前读入原代码：[测试文件:45–53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:45) 在导入时固定 `CODE`，之后磁盘文件变化不会更新它；旧 UAT `:201` 也记载过人工 checkout。旧记录没有实际加载字节、完整命令及进程时序，因此建议保留“当前 KILLED；旧 SURVIVED 未复现，原因未定”，不对并发解释作因果定案。

**四文件 SHA 足以证明列明文件最终内容恢复。** 我重算得到 **before＝after＝当前＝HEAD，4/4 一致**，两份清单自身也逐字节相同。它看不见执行期间发生后又被还原的污染、其他文件或外部状态，以及权限、inode 等元数据变化；因此不能单独证明全程独占或全系统零污染。

本轮 `git diff --exit-code HEAD -- backend/scripts/g32b_mutation_gates.py` 为 **rc=0、输出空**；harness SHA 为 `5d62bb23…0a0914e`。未修改仓库或审查 harness 本体。
