# 代码审查请求 — CARD-维护B-R4「先渲染再核数」架构重切

你在审查一个**本地开发工具**的一次重构。被审物是一个 Markdown 报告自检脚本
（`recap_scan.py --verify`）：它读一份学习回顾报告和同目录的一份 JSON 数据快照，
核对报告里写的每个计数是否真的来自那份 JSON。它没有网络、没有权限边界、
不处理他人数据——纯粹是「作者自查自己写的数字有没有编造」。

## 一 请只读这些文件

    canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py
    canvas-vault/.claude/skills/board-recap/SKILL.md
    backend/tests/regression/test_recap_scan_signals.py

审查面 = 这一条 diff（其余提交与你无关）：

    git diff 7b94f318..HEAD -- \
      canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py \
      canvas-vault/.claude/skills/board-recap/SKILL.md \
      backend/tests/regression/test_recap_scan_signals.py

## 二 这次改了什么

前 31 轮审查反复得出同一个结论：**逐条正则枚举 Markdown 形态是开放集合**，
每补一个形态就冒出下一个。本次的答复是把「源码 → 可见文本 → 结构」收进
**单一入口** `render_visible(text) -> Doc`：

1. **渲染层** `Doc`（`Line` / `Section` 三级结构）——归一与结构只有一个定义点，
   各判据不再自己做归一，只在 `Doc` 上提问。旧的 `_visible_text` /
   `_visible_block` / `_strip_code_blocks` 成为它的薄封装。
2. **未知形态 fail-closed** ——渲染层剥除标记前先查白名单；白名单之外的构造
   报「未知形态」而不是静默剥掉。
3. **绑定层** ——台账每一行的数字都携带一个 JSON 字段路径
   （`ledger.seeds[i].tips_count` / `ledger.derived[i].tips_open`），
   种子与派生两个小节由**同一张表**驱动（消除口径分叉）。
4. **拒绝层** ——原先「JSON 里没有对应字段就跳过检查」的放行分支已按数据模式分流：
   该有字段而没有 = 判失败。

## 三 请重点回答（按重要度排序）

1. **能不能让编造的数字通过。** 这是本工具唯一的核心承诺。请找出：一份
   报告写了一个 JSON 里没有依据的计数，而 `--verify` 仍然返回 0 的具体写法。
   请给出可复现的报告片段。
2. **口径分叉。** 同一条规则是否在两处各写了一份，且两份不一致？
   （前 31 轮里这是最高频的缺陷类型：收集器认顶格标题、安全态判定认缩进标题，
   夹缝里的行两边都不管。）
3. **重构是否改变了既有行为。** `Doc` 的 `visible_block()` / `stripped_block()`
   是否与它们替换掉的旧函数逐字等价？不等价的地方是否只发生在新增的
   Obsidian 方言（`==高亮==` / `%%注释%%`）上？
4. **新的拒绝层是否误伤合法报告。** 特别是数据来自本地扫描（fallback）而非
   完整数据源（manifest）时，某些字段本就不产出——这种情况是否被正确地
   与「该有却缺失」区分开？
5. **诚实性。** 代码注释与 SKILL.md 里的声明，有没有比实际证明的更宽？
   （例：声称"已闭合"而实际只是"列举之外报错"。）

## 四 已裁决、不必再提

- **渲染层仍是有限列举，不是完整 CommonMark 实现。** 这是本卡明确接受的边界，
  已写进验收单。请不要把「不是完整 renderer」本身列为缺陷；
  但**列举内部的错误**（白名单漏了本域真实出现的构造、或收了不该收的）请务必指出。
- 不引入第三方 Markdown 库是本卡的既定约束（纯 stdlib）。
- 第六～第十形态的历史判据、`_join_free` 的过度拼接问题：前者已由渲染层统一，
  后者已在代码里如实登记为已知边界，均不必重复。

## 五 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级。每条给出：
文件:行号、问题、**可复现的最小报告片段**、建议方向。
没有 BLOCKER 时请明说「BLOCKER: 0」。
