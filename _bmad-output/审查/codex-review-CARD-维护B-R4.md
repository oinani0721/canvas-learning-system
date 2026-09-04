BLOCKER: 0

总体判定：FAIL。存在可复现的漏检和误拒，但没有导致数据破坏或脚本整体不可用的 BLOCKER。

等价性先给结论：`Doc.stripped_block()` 与旧 `_strip_code_blocks()` 逐字等价；`Doc.visible_block()` 不等价，代码级输出差异只来自新增的 `==高亮==` 归一。但这项差异进一步改变了标题结构识别。

## HIGH

1. [recap_scan.py:1734](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1734)、[recap_scan.py:1894](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1894)、[recap_scan.py:2647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2647) — `audit_span()` 比旧扫描更短。

   问题：新标题正则接受行尾分支 `$`，所以裸 `##` 会终止 H2/H3，裸 `###` 会终止 H3；旧 `^##[^\S\n]` / `^#{2,3}[^\S\n]` 必须在井号后实际存在非换行空白，不会终止。与此同时，安全态又手写了第二份要求空白的 H3 正则，因此裸 `###` 不会把后续行标成“不受认可小节覆盖”。

   最小反例：

   ```md
   ## 台账
   ### 种子
   - S — 批注 2 条
   ###
   - Ghost — 批注 2 条
   ## 末
   ```

   当 JSON 中已有值 `2` 时，`_verify_ledger_counts()` 与 D2 合计零诊断。裸 `##` 也能复现。新增测试 [test_recap_scan_signals.py:5987](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/backend/tests/regression/test_recap_scan_signals.py:5987) 只覆盖 H1、缩进 H2/H3、H4，遗漏了这个边界。

   此外，高亮先于标题识别执行：[recap_scan.py:1778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1778) 会把源码非标题 `==##== 末` 或 `##== 末==` 变成 `## 末`，同样提前结束审计范围。

   建议：标题结构应从高亮归一前的结构面判定；为审计边界保留“井号后是否实际消费了 `[^\S\n]`”属性。`bad_h3` 直接读 `Line.heading`/该属性，不再手写正则。补裸 H2、裸 H3及高亮伪标题回归。

2. [recap_scan.py:2701](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2701)、[recap_scan.py:2726](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2726)、[recap_scan.py:2830](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2830) — 共用身份解析存在静默跳过路径。

   问题：raw 行能匹配台账模板、raw 节点不在 ledger、visible 行却无法再解析时，`_resolve_ledger_node()` 直接返回 `None`，没有记录问题。例如 `<b>` 是白名单标签：

   ```md
   - <b></b> — 批注 2 条
   ```

   渲染后节点名消失；种子和派生绑定都被跳过。若 `2` 已在全局数值池，D2 也不补救。旧种子实现会继续使用 raw 身份并报“不在 ledger”。

   同一规则仍有调用方分叉：种子按 resolver 的 raw-exact 分支选择取数 match，而派生固定 `vis_ms or raw_ms`。含 `&mdash;` 的合法精确节点名可能在渲染后产生额外 ` — `，把节点名片段误当尾巴并误拒。

   建议：resolver 返回结构化结果，如 `(node_id, chosen_match/source)`；raw 未命中且 visible 不可解析时必须显式报“身份无法绑定”。

3. [SKILL.md:251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/SKILL.md:251)、[recap_scan.py:2534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2534)、[recap_scan.py:2833](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2833) — 两个台账小节尚未做到“每个统计数字逐字段绑定”。

   当前覆盖如下：

   | 报告数字 | JSON 路径 | 结果 |
   |---|---|---|
   | 种子批注数 | `ledger.seeds[].tips_count` | 已绑定 |
   | 种子理解度未闭环数 | `ledger.seeds[].tips_open` | 已绑定 |
   | 种子已派生点数 | `ledger.seeds[].derived_children_count` | 已绑定 |
   | 派生 tips 未闭环数 | `ledger.derived[].tips_open` | 已绑定 |
   | 派生批注数 | `ledger.derived[].tips_count` | 已绑定 |
   | 派生考过次数 | `ledger.derived[].attempt_count` | 已绑定，但有下一条类型误拒 |
   | `mastery <值>` | `ledger.*[].mastery_score` | 未绑定 |
   | `derived 计数 0` 占位说明 | `counts.derived` | 未绑定 |
   | 规模门尾部四项聚合 | `scale_gate.tail_counts.*` | 未绑定 |

   实测 `mastery_score=0.01`、报告写 `mastery 0.99`，ledger 与 prose 两门均无诊断。测试还明确说明真实报告存在 mastery 数字：[test_recap_scan_signals.py:1811](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/backend/tests/regression/test_recap_scan_signals.py:1811)。

   派生有一条数据时写 `- （无：derived 计数 0，本板尚无派生成员）` 也能通过。规模尾数由 [recap_scan.py:3622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:3622) 产出，但数值池在 [recap_scan.py:1553](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1553) 整块排除了 `scale_gate`，也没有直接绑定器。

   为什么：开放的 `rest=.*` 加三条字段正则不是“每个数字”绑定；D2 的全局数值碰撞池也不能证明数字属于当前节点/字段。

   建议：为 mastery、零派生说明和尾部聚合定义固定模板并直接比较对应路径；其余自由尾巴不得携带统计数字。

4. [recap_scan.py:613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:613)、[recap_scan.py:2863](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2863) — 新派生绑定误拒当前合法 fallback 数据。

   问题：fallback 收集器通过 `_fm_scalar()` 把 `attempt_count` 输出为字符串；绑定器却比较 `int(报告值) != JSON字符串`。因此 JSON `"5"` 与报告“考过 5 次”仍被报不一致。

   建议：收集时使用 `_int_or_none()`；验证侧同时兼容历史纯数字字符串，非法、布尔或非整数值继续 fail-closed。

## MEDIUM

1. [recap_scan.py:1027](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1027)、[recap_scan.py:1085](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1085)、[recap_scan.py:1147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1147)、[SKILL.md:292](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/SKILL.md:292) — 四空格代码块规则仍有两份不一致实现。

   有数信号用 `(?! {4}|\t)` 拒绝缩进代码行；无据信号的 `[>\s\-*·]*` 却接受任意缩进。四条无据信号全部缩进四格时，`_verify_signal_lines()` 零诊断，与“藏进四空格代码块等同缺行”的声明相反。

   建议：两类信号共用同一行首策略；至少给无据模板增加相同的缩进拒绝。围栏状态机本身只有一份，这个问题出在“缩进代码”仍由消费方各自判断。

2. [recap_scan.py:1758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1758)、[recap_scan.py:2019](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2019)、[SKILL.md:304](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/SKILL.md:304) — 新未知形态门误拒明确允许的 inline code。

   问题：未知形态直接扫描 raw 行，没有先屏蔽代码跨度。``原话：`vector<T>`。`` 被报未知标签；``本轮 2 条原话：`$x$`。`` 被报数学公式。高亮替换也会把代码字面量 `` `==raw==` `` 改成 `` `raw` ``。

   为什么：SKILL 明允 tips 原话放在行内代码里；CS 学习笔记中的泛型和公式字面量是正常输入。

   建议：HTML、高亮和未知形态检测前保护 inline-code spans，处理完成后原样恢复。

3. [recap_scan.py:2549](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2549)、[recap_scan.py:2565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2565)、[test_recap_scan_signals.py:6038](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/backend/tests/regression/test_recap_scan_signals.py:6038) — 历史 JSON 的兼容策略不对称。

   扁平 `ledger: [...]` 不会误拒，但派生身份和所有派生数字会完全跳过绑定；这不是“验证通过”。反向地，分组历史形态若缺 `derived` 键，即使派生小节只有无数字占位说明，也会立即被拒。

   建议：增加 scan schema/version。扁平形态应明确标为“派生未核验”；若要兼容缺角色数组，只在相应小节实际写出台账身份/统计数字时拒绝，或者要求先重新采集快照。

## LOW

1. [recap_scan.py:1886](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1886)、[test_recap_scan_signals.py:5854](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/backend/tests/regression/test_recap_scan_signals.py:5854) — `Doc.visible_block()` 注释声称与重切前“逐字等价”，实际新增了高亮替换。当前测试只比较 Doc 与当前薄封装，是同源自洽，不能证明相对 `7b94f318` 的等价性。

   建议：改为“除新增 `==…==` 归一外等价”，并用冻结的 legacy oracle/样例做差分门。

2. [recap_scan.py:2461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2461)、[test_recap_scan_signals.py:5563](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/backend/tests/regression/test_recap_scan_signals.py:5563) — 缺字段契约的说明已过期。两处仍称旧 scan 缺字段时“不报/不误报”，实现及同一测试后半实际要求“报告写了数而字段无值即拒绝”。

   建议：统一为当前规则：“报告未写该数则不检查；写了但 JSON 无值则 fail-closed。”

3. [SKILL.md:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/SKILL.md:295)、[recap_scan.py:2036](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x6-recap-r4/canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:2036) — SKILL 声称正文中的公式、脚注、图片一律拒绝；实现仅在该行含数词样字符时检查这三类。未知 HTML 标签才是全文检查。

   建议：把声明收窄为“含数字的行不得使用这些构造”，或真正实施全文禁止。

两个确认项：

- `Section.hi` 与 `audit_span()` 保留两种语义本身合理；缺陷是 `audit_span()` 的实际终止集合不等于 legacy 集合。
- “报告写了数字、对应旧 JSON 字段缺失”按新增 SKILL 的 fail-closed 契约应当拒绝，不属于误拒；真正的误拒是当前 fallback 自产的字符串 `attempt_count`，以及无数字内容却因缺角色数组被拒。

仓库内仅读取了指定三文件与限定 diff；高严重度项用 `python3 -B` 导入脚本做了无写入函数级复现。未运行 pytest/完整 CLI，因为它们会读取 fixtures 并写临时目录，超出本次“只读三文件”的边界。


