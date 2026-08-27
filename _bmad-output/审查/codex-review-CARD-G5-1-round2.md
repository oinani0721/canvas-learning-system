整体裁决：**不通过**。

审查基线：`card/n5-split @ b47ebfba351f3eedb496a97961083c5e3b1d5df7`。本轮纯静态审阅，未运行攻击试验、checker 或 judge，未修改任何文件。

## 第一轮九项复核

| 项目 | 二轮裁决 | 结论 |
|---|---|---|
| B1 真实正例不足 | **STILL-OPEN** | A5、B4 均为真实用户逐字，新增有效。但卡片硬门仍是“四类各 ≥3 条真实正例” [goal-card:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/implementation-artifacts/goal-cards/2026-08-27-主goal全量分goal总账.md:409)，当前自陈为 A=3、B=2、C=2、D=0 [矩阵:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:58)，且明确承认 C/D 没有真实触发语 [矩阵:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:54)。诚实披露值得保留，但不能替代硬门。 |
| B2 标注不实 | **PARTIAL** | 指名的 N2→doc-demo、D3/N7→constructed 均已正确修正。原 23 条现为 **22 PASS / 1 PARTIAL（B3）**；新增 A5/B4 都 PASS。 |
| B3 裁判可伪造 | **STILL-OPEN** | 坏行、init/cwd、result、session 唯一性确实加固，但 judge 仍不绑定 utterance、`*-meta.json`、runner exit code或 manifest 采集批次；交换两份不同 session 的干净日志仍可通过。`result` 也只要求“至少一个”，不要求唯一且为最后事件 [judge:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:128)、[judge:312](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:312)。 |
| H1 T7 来源真实性 | **PARTIAL** | SHA、行号界、空白精确匹配均真实生效。但 `verbatim` 与 `doc-demo` 仍走同一逻辑，D1 改成 verbatim 仍可过；attribution 只要求窗口内出现。paraphrase 仅需任意四字重叠，不能证明语义或“已发生事件” [checker:342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:342)。 |
| H2 T8 文档同步 | **PARTIAL** | 已实现 ID 双向、话语同一行、触发列一致。但仍不比较 category、skill、status、source type/ref、理由、去向、headless、real_floor [checker:366](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:366)。来源类型或下限单边漂移仍可过。 |
| H3 正例指纹 | **PARTIAL** | B1 输入漂移已修，当前 YAML/runner 都是“特征值与特征向量”。但显式 `Skill(board-recap)` 分支直接 PASS，不要求 `VERIFY PASS`；outputs-only diff 也允许零新增 [judge:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:233)。所谓“双条件”只约束 Bash 分支。 |
| H4 T0–T2 硬化 | **PARTIAL** | polarity、布尔、状态枚举、非空、查重已补。但 `real_floor` 没有整数/非负/最低为 3 的 schema 门，只核键集合后直接 `int()`；把 floor 改成 0 或负数可放松门槛 [checker:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:165)、[checker:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:223)。 |
| M1 manifest 覆盖 | **PARTIAL** | 目录和 symlink 路径已计入；FIFO/socket 仍漏，symlink 只记录路径、不记录目标，原路径不变而 retarget 不可见 [negative runner:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/run_headless_negatives.sh:24)。 |
| M2 T3/T4 | **RESOLVED** | 旧问题已闭合：额外 direct live skill 会红，T4 只读首个 frontmatter 块 [checker:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:244)、[checker:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/backend/scripts/check_skill_trigger_matrix.py:106)。另有低风险余量：它没有真正解析 YAML，重复 `description` 键可能造成 checker 与实际加载器取值不同。 |

## 23 条来源标注

当前 YAML 已是 **25 条**，因此按“原 23 + 新增 2”复核：

- 原 23 PASS：A1、A2、A3、A4、B1、B2、C1、C2、C3、D1、D2、D3、N1–N10。
- 原 23 PARTIAL：**B3**。report:71–73 同时写着“思维导图已发生、`/board-recap` 规划”；四字重叠能证明锚点相关，但不足以把整句回顾请求证明为真实场景改写 [report:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-16-学生使用场景报告-深度学习与搜集调研的完整旅程.md:71)。
- 新增 A5：**PASS**，mian2:143 确有 `User：` 和完全相同原话，包括“把 相关”的原始空格 [mian2:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-15-面2-需求澄清结果-用户逐字定案.md:143)。
- 新增 B4：**PASS**，r1:13 是明确标注“逐字、未改动”的 User 引文 [r1:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/语料快照-G5-1/2026-08-15-批注回复-R1-新skill定位与数据基础核实.md:11)。

这里的 C1/C2 PASS 仅表示符合当前“已发生事件改写”的来源类型定义，不表示满足“真实触发语”硬门；施工文档自己也承认 C 类真实触发语不存在。

## 新发现

1. **HIGH — N2 登记严重不完整，测试污染 skill 施工面。**

   N2 不只写了两份 outputs。日志显示它用 `Write` 创建、再两次 `Edit` 修改：

   `canvas-vault/.claude/skills/board-split/scripts/export_mindmap.py`

   证据见 [N2.jsonl:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/N2.jsonl:28)、[N2.jsonl:33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/N2.jsonl:33)。该未跟踪脚本目前仍留在 vault，而 runner 整体排除了 `.claude/`，所以 manifest 没有报出。登记簿只写“经 Bash 写 outputs、产物已移出” [矩阵:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md:181)，不够诚实完整。

2. **HIGH — `real_floor` 是可自降级的声明，不是验收硬锚。**

   T1 对当前 `3/2/2/0` 确实执行，但 checker 不锁定目标值，也不要求每类 ≥3；T8 不同步文档中的 floor。16 类负控只测试“保持 floor 不变、把真实条目改 constructed”，没有测试把 floor 同步调低 [mutations:116](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/mutation_negative_controls.py:116)。

3. **MEDIUM — UAT 顶部仍有不实摘要。**

   验收单声称“这张卡不改任何 skill”“10 条负例零误触发、一个字节没变” [UAT:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/验收单/UAT-CARD-G5-1-触发矩阵与负例锁定-2026-08-27.md:6)、[UAT:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/验收单/UAT-CARD-G5-1-触发矩阵与负例锁定-2026-08-27.md:21)，与 N6、N2 以及上述脚本残留冲突；虽然后文技术表已部分纠正，用户首屏仍会被误导。

## 证据包与终判

- N6 `Skill(study-plan)`：**登记属实** [N6.jsonl:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/logs/N6.jsonl:8)。
- N2 outputs 红行：**属实但登记不完整**。
- B2 形式化漂移：**属实**，四份日志中两份无 Skill、两份显式 `Skill(board-recap)`。
- 16 类 mutation verdict：**对所列 16 个变异的代码与存档结果一致，但不能证明无其他绕过**。
- `final-verdict.txt`：确实保留 N2、N6 红行并以 FAIL 收尾 [final-verdict:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/final-verdict.txt:5)。按 judge 源码该状态返回 `1` [judge:349](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n5-split/_bmad-output/审查/g5-1-evidence/judge_headless_logs.py:349)；但证据包没有单独保存实际 shell exit code，因此“代码路径应为 1”已证，“当次进程退出码被独立记录”为 **UNVERIFIABLE**。

最终结论：**CARD-G5-1 不通过**。阻断依据是 B1 硬门未满足、B3 仍可伪造、N6 已发生真实误触发，以及 N2 存在未登记且未被 manifest 测量的 skill 代码写侧。


