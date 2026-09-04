# 代码审查 — 一次重构的等价性与覆盖面复核

请审查一个**本地开发辅助脚本**的重构。它是作者写给自己用的文档自检工具：
读一份 Markdown 学习笔记和同目录的一份 JSON 数据快照，检查笔记里写的统计数字
是否与 JSON 中的字段一致。没有网络、没有权限模型、不处理他人数据。
这次重构把散落的文本处理逻辑合并成了一个统一入口。

## 一 只读这三个文件

    canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py
    canvas-vault/.claude/skills/board-recap/SKILL.md
    backend/tests/regression/test_recap_scan_signals.py

审查范围 = 这一条 diff：

    git diff 7b94f318..HEAD -- \
      canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py \
      canvas-vault/.claude/skills/board-recap/SKILL.md \
      backend/tests/regression/test_recap_scan_signals.py

## 二 重构内容

1. **统一入口** `render_visible(text) -> Doc`：把「源码文本 → 显示文本 → 章节结构」
   收进一处。`Doc` 提供 `Line`（逐行的 raw / visible / 是否在代码块内 / 标题层级）
   与 `Section`（章节范围）。旧的三个函数成为它的薄封装。
2. **两种段落语义并存**：`Section.hi` 是文档树语义（同级或更高级标题终止）；
   `Doc.audit_span()` 是检查覆盖语义（只有顶格且层级在 `[2, 本级]` 的标题终止）。
   后者用于复现重构前的检查范围。
3. **表驱动的字段绑定**：`_LEDGER_ROLE_SECTIONS` 把两个小节映射到 JSON 的两个
   数组，收集与状态判定共用这张表。
4. **共用的身份解析** `_resolve_ledger_node()`：两段式（先按原文精确匹配，
   再按归一后的名字找唯一候选，多个候选则拒绝）。

## 三 请回答（按重要度）

1. **等价性**：`Doc.visible_block()` / `Doc.stripped_block()` 与它们替换掉的旧函数
   是否逐字等价？不等价之处是否只发生在新建模的 `==高亮==` 上？
2. **覆盖面**：`audit_span()` 的段落范围与重构前的两处扫描
   （`^##[^\S\n]` 与 `^#{2,3}[^\S\n]`）是否**同样宽**？有没有哪种标题写法
   会让新实现的范围更短？（范围变短意味着某些行不再被检查。）
3. **同一规则的多份实现**：文件里有没有哪条规则被写了两遍且两遍不一致？
   前几轮的经验是这类问题最容易长期潜伏。请特别看：
   身份解析、章节终点、代码块判定、标题识别这四处。
4. **绑定完整性**：`### 种子` 与 `### 派生` 两个小节里，报告可以写出的每一个
   数字，是否都有对应的 JSON 字段路径与之比对？哪些数字目前没有被比对？
5. **误拒**：新增的检查里，有没有哪一条会拒绝掉**合法**的输入？
   特别是 JSON 为历史形态（扁平数组、缺字段）时。
6. **声明与证据**：代码注释和 SKILL.md 里的说法，有没有比实际做到的更宽？

## 四 已知边界，不必重复指出

- 文本处理层是**有限列举**，不是完整 CommonMark 实现。这是本次明确接受的边界，
  已写进验收单。请不要把「不是完整实现」本身当作缺陷；但**列举内部的错误**
  （表里漏了本域真实出现的写法、或收了不该收的）请务必指出。
- 不引入第三方 Markdown 库是既定约束。
- 有 5 处逐行文本处理尚未改走统一入口（`_verify_prose_counts` 一处、
  `_verify_fallback_derive_numbers` 三处、`_verify_report` 一处），已如实登记。

## 五 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：文件:行号、问题、
为什么它是问题、建议方向。没有 BLOCKER 时请明说「BLOCKER: 0」。
