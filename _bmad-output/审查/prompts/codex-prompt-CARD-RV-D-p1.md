# 独立复核：CARD-RV-D · P1（负控 harness + validator + schema doc）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene`

被审的是**一个已合并的整改 commit**：`514cff3c` → `e22ad10a`
（实测 `5 files changed, 856 insertions(+), 9 deletions(-)`）。
它上一次被审时，审的是「`514cff3c` + 工作区」这种**非 commit 状态**，
整改本身**零复审**就合并了。本卡补审。

**你的读取面就是这一份 diff 文件**（P1 部分，+348/−3）：

```
_bmad-output/审查/evidence-rv-d/rv-d-p1.diff
```

它包含三个文件的改动：

| 文件 | +/− | 性质 |
|---|---|---|
| `backend/scripts/g32ccr1_negative_controls.py` | 306 / 0 | **新增**：11 条负控输入的 harness |
| `backend/scripts/validate_learning_events.py` | 37 / 2 | 账本校验器 |
| `docs/learning-events-schema-v1.md` | 5 / 1 | schema 文档 |

⛔ **审面不是 HEAD。** `e22ad10a` 之后，后续两张卡又改了同族文件：
`git diff --stat e22ad10a HEAD -- <这 5 个文件>` = **2 files, +169/−11**。
读 HEAD 会把后两卡的改动算进本卡结论。若你为拿上下文打开了 HEAD 全文，
**结论只能引用 diff 内的行**，行号写成 `e22ad10a:<文件>:<行>`。

补充上下文（可读，非必须）：
`_bmad-output/审查/evidence-rv-d/审查上下文.md`、
`_bmad-output/审查/evidence-rv-d/e22ad10a-commit-message.txt`。

## 二 作者自述，请独立核对（不要默认成立）

摘自 `e22ad10a` 的 commit message，与 P1 相关的部分：

- **(a)** receipt 条目 14 键与严格字段表做差集 = `{question_id, self_confidence_raw}`，
  **裁定不扩表**。依据经上一轮打回后收窄为「当前落账写点不写、复放路径不读」
  —— 不是「结构上够不着」（`append_event()` 能写进账本）。
  「判据措辞同步落在代码注释 / docstring / schema §6.1；枚举表零改动。」
- **(c)** `value_charset_problems` 非 dict 分支不可达。AST 判据收紧三处：
  任何 Store 上下文的 `record`（原版漏海象）、守卫与调用同为顶层语句且守卫在前、
  守卫须比 dict 且立即 return。对应负控输入 E5 / E10。
- **(f)** 一致性门提取器从正则改 **AST** + 严格表逐项钉死（堵住空表空真），
  对应负控输入 E9；容器遍历补 tuple 样本（E11）。
- 自述的裁判数字：`g32ccr1 11/11 KILLED`。
  （本卡在主干现状上重跑，实测同为 11/11 KILLED、rc=0；
  但 `e22ad10a` 时刻的数字不可回溯复现，见边界。）

## 三 按重要性排序的问题

1. **这 11 条负控输入，是否各自只拆掉「被它测的那一道防线」？**
   若某一条同时拆掉了别的防线，那么它被判定为「已拦下」时，
   到底是哪一道门拦的就说不清了 —— 这会让整套 harness 的结论失去指向性。
   请逐条核（E1–E11 在 diff 里都有注释说明它拆的是什么）。

2. **判定条件本身的可靠性。** harness 判「已拦下」用的是这一行（主干 `:277`）：

   ```python
   killed = rc == 1 and gate in out and "failed" in out
   ```

   它**不解析失败集合、不绑定断言身份**。请判断：
   - 若负控输入生效了，但让门在**另一条**断言上变红，这个条件会不会仍然成立？
     （若会 ⇒ 「拦下」被归给了错误的原因）
   - 若负控输入让被测文件**语法错误 / 无法导入**，pytest 同样 rc≠0 且输出含
     `failed`/`error`，这个条件会不会仍然成立？
   - `gate in out` 这一项起了多少作用？它匹配的是门的**名字字符串**；
     若门名出现在 pytest 的收集行或摘要行里（而不是失败行里），这一项是否恒真？
   - 这 11 条里，有哪几条的「已拦下」**可能**是靠这个宽条件成立的
     （即：换成绑定断言身份的严格条件后，可能变成「未被拦下」）？
   - 要改成绑定失败身份，最小改动是什么？

3. **`validate_learning_events.py` 的 37 行新增是不是纯注释 / docstring？**
   另一轮勘探说「非注释新增只有 5 行且全在 docstring 里」——**请独立核**，
   逐行分类（注释 / docstring / 可执行语句），给出实数。
   若有可执行语句，它改变了什么行为？

4. **`docs/learning-events-schema-v1.md` 的 5 行新增与代码是否一致？**
   自述说「判据措辞同步落在 schema §6.1」。请核对文档里的措辞
   与 diff 里的代码实际做的事是否相符；若文档说得比代码宽（或反之），指出来。

5. **AST 判据的三处收紧（(c)）在 diff 里逐条对得上吗？**
   有没有哪一处是自述里有、代码里没有的？
   E5（在函数里重绑 `record`）与 E10（用海象重绑）是**两个独立的**对照输入，
   还是同一形态的两种写法？（若是后者，它们不构成独立覆盖。）

6. **严格表「逐项钉死」是写死字面量，还是从实现读取？**
   后者会让负控输入同时改掉门的期望值 —— 门就看不见变化了。
   这是已知的经典陷阱，请重点确认是哪一种。

## 四 输出格式

按严重度分级（BLOCKER / HIGH / MEDIUM / LOW），每条给出：
- 一句话结论
- `e22ad10a:<文件>:<行>` 形式的具体依据
- 建议的最小改动

**只读判定不了的，写「未验证」并说明缺什么** —— 不要猜。
最后给一段总评：作者自述的 (a) / (c) / (f) 三条，分别成立到什么程度。

## 五 边界

- 只读。不改任何文件，不连任何数据库端口。
- 那条「自评分数字段可改写记录身份」的隐患（属 P2 的 xfail 交接锚）
  **不在本卡修复范围** —— 它已被移交给写点边界卡，你不需要给修复方案。
- 不评价 `SKILL.md` 本身（本卡零代码改动，且它不在审面里）。
- 本卡只补审这一个 commit，不评价它之后 Z6-B/Z6-C 的改动。
