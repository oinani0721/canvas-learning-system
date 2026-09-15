绑定最终 HEAD **`9496f84d`**。结论：**BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 2**。

## BLOCKER

无。

## HIGH

**H1：解析期间的 `OSError` 仍会被误当成“config 不存在”，静默返回父树。**

- 位置：[SKILL.md:458](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:458)。
- 触发：config 明确指向 B，但 `safe_load` 抛 `OSError`，或真实 PyYAML 读取配置流时发生 EIO，函数便返回父树 A。
- 已用真实 PyYAML 加内存读取故障复现。这不是 r9 新引入的问题，但最终 HEAD 仍存在；不能把所有 `OSError` 都解释为文件缺失。

## MEDIUM

**M1：入口可调用仍不足以证明“拿到了可用的 PyYAML”，绝对不返回树的保证仍不成立。**

- 位置：[SKILL.md:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:435)。
- 触发：同名 `yaml.py` 提供 `safe_load = list`，或提供恒返回 `None` 的函数，即使 config 指向另一树，仍会返回父树；恒返回字典也能指定另一棵存在的树。
- 无 config 时甚至不会调用这个入口，因此“调用必抛异常”的损坏入口也能通过检查后返回父树。普通 `RuntimeError` 在 **config 存在**时会拒绝，但误报为 YAML 非法。

**M2：第四探针没有保护新增的“必须可调用”判据。**

- 位置：[test_g3_2_review_ledger.py:7726](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7726)。
- 触发：把生产判断错误地弱化为 `hasattr(yaml, "safe_load")`，**40 格及有库回退门仍全部通过**；但真实同名模块设置 `safe_load = 1`、config 不存在时，该变体会返回父树。
- `object()` 只覆盖属性缺失。缺的是“属性存在但不可调用”和“可调用但行为损坏”这两个维度。

## LOW

**L1：旧结论没有全部就地撤销，“措辞残留全清”不成立。**

- 位置：[验收单:673](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:673)、[测试辅助:7552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7552)。
- 触发：单独阅读旧验证表，仍会看到“INVALID＝缺陷类别被构造性消除”；读取 `_ht_outcome` 说明，仍会看到“比较两次 exit 等于比较解析树”，但当前缺库拒因没有解析树。
- 验收单后文和新增测试确已正确撤回 INVALID 外推；问题是旧表及旧注释仍保留相反表述。

**L2：本轮统计把一个 SURVIVED 错计为第三个 INVALID。**

- 位置：[验收单:762](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:762)。
- 触发：核对[原始日志:9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/审查/evidence-harness-tree/verify-kills-r9-20260916T002455.txt:9)，实际矩阵结果是 **11 KILLED / 2 INVALID / 1 SURVIVED**；有库门再杀死 M2 后，合计应为 **12 KILLED / 2 INVALID**。

## 其余问题的核对结果

- **40 格不是恒真。** 内存执行实际测试逻辑所得：

  | 实现 | 40 格通过数 | 有库回退门 |
  |---|---:|---|
  | 当前生产代码 | 40 | 通过 |
  | 错改为 `hasattr` | 40 | 通过 |
  | 恒返回父树 | 0 | 通过 |
  | 恒缺库拒绝 | 40 | 失败 |

- **组合覆盖：**“有 config × 变量/缓存”已有对应格，只是 config 无 `harness_tree` 键。当前生产不读取这些变量或缓存，不能仅凭缺少“父树 × 变量”就判缺陷；若引入候选来源之间的优先级，才需要测试显式键冲突、多个候选同时可用等组合。
- **第四探针：**对当前检查，`object()` 与真实空模块都因没有入口而被拒；真实模块另有模块身份和来源属性。普通不可调用属性目前确实被挡，带 `__call__` 的对象可以通过，是否正确取决于实际行为。
- **`shlex.quote`：**本技能使用 POSIX shell，未发现新的路径引用问题；空格、单双引号、变量符号、命令替换符号和换行的参数往返验证通过。
- **既有门：**未发现本轮使既有实际断言或指纹门退化为恒真。三向脚本已固定旧写点版本，并包含三组结果断言。

验证限于源码读取、摘要核对和内存执行；未运行 pytest 或写盘复现脚本，未修改文件，未连接网络或数据库。
