# 独立代码复核请求（round-4）— CARD-G3-3-R2-writer-boundary

## 一 背景与最小读取面

仓库根（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

round-3（存档 `_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary-r3.md`，绑定 `23b26e6e`）
给出 BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 0，指出 Python `\s` 超出 YAML s-white。
作者独立复现后整改。本轮复核整改后的最终态；这是本卡第四轮。

**请只读以下范围**（不要运行任何写操作）：

1. `git diff 23b26e6e aa4a89fc -- . ':(exclude)_bmad-output'` —— round-3 整改的全部代码改动（2 文件）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:390-440`
   （`_harness_tree` 的注释分隔判据收窄到 `[ \t]+#`，注释记录三轮演化）
3. `backend/tests/regression/test_g3_2_review_ledger.py` 的
   `:6959-7010` 附近（分隔符参数化用例改三态期望）

## 二 作者自述（round-3 整改声明）——请独立核对，不要采信

1. 裸值注释判据现为：`#` 是值首字符 ⇒ 空值回退；否则 `re.sub(r'[ \t]+#.*$', '', _raw).strip()`。
   即只有 SP/TAB 分隔的 `#` 才是注释，全角空格 U+3000 / NBSP U+00A0 分隔的 `#` 保留为路径内容。
2. 三轮演化都写进了注释（`\s+#` 会把「注释掉键」变砖化 → 一律截会静默换树 → `\s` 含
   全角空格/NBSP 仍会静默换树），意图是让后来者不要再改回去。
3. 分隔符参数化用例改为三态期望：
   - `path`（无分隔 / U+3000 / NBSP）：值含 `#alt` ⇒ 路径不存在 ⇒ 拒，且拒因含**完整原路径**；
   - `comment`（SP）：注释剥掉 ⇒ 值 = alt 树 ⇒ 正常写入；
   - `invalid`（TAB）：实测发现真 YAML 的 plain scalar 禁 TAB，校验器读 config 那层
     直接判损坏拒写（rc≠0「vault 归属无法绑定 … config 损坏」）。该态只断言
     **不静默**（rc≠0 且零写），不断言由哪一层拒——因为两层各自 fail-closed，
     绑死某一层会让判据比它能证明的更窄。
4. 参数化里的不可见字符一律写成 `\uXXXX` 转义而非字面字符。

## 三 请按重要性排序回答的问题

1. `[ \t]+#` 这个收窄有没有引入**第四种**错误形态？特别看：
   - 值以 SP/TAB 结尾但无 `#`（`harness_tree: /repo   `）——`.strip()` 的行为；
   - `#` 前混合 SP 与 U+3000（`/repo <U+3000>#alt`、`/repo<U+3000> #alt`）两种顺序；
   - 多个 `#`（`/repo #a #b`）。
2. TAB 那一态：`invalid` 的断言只钉「rc≠0 且零写」。若将来 config 读取层改成
   容忍 TAB，这条用例会怎样？它会变成假绿吗，还是会因为另一半（正则层剥 TAB
   ⇒ 值 = alt ⇒ 应写入）而报红？请判断这个三态设计在语义演化下是否稳健。
3. 三轮注释累积在 `_harness_tree` 里已相当长。从**可维护性**角度看，这些注释
   有没有哪一条实际上已经**被后一轮推翻**却仍留在文件里（会误导后来者）？
4. 四轮累计之后，对这张卡整体（`self_confidence_norm` 写点门 + `event_id` 形态门
   + `harness_tree` 解析 + 相关测试判据）还有没有**新**的 BLOCKER/HIGH。
   MEDIUM/LOW 若属可登记项，请标注「登记即可」。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何观察到它

没有问题的级别请明确写「无」。

## 五 边界

- 只读复核，不要修改任何文件，不要运行测试或任何写操作。
- 不要连接任何数据库或网络服务。
- 不评审 `start-exam-board` 与 `ai-linked-doc` 写点（登记项）。
- 不评审变异 harness 全量覆盖率（U8-B 的面）。
- `_bmad-output/` 下除前三轮存档外不必阅读。
