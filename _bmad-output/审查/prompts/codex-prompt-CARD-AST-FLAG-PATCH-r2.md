# 独立复核请求 round-2 — CARD-AST-FLAG-PATCH（第十四批 T8-D）

## ① 背景与最小读取面

round-1（绑 `20abe003`）你给出 BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 1。四条**全部经本车道
独立复现后接受，无一条驳回**。本轮请复核整改本身，绑定 **`6564fc09`**。

整改摘要：

- **HIGH-1 → 整条撤回**。初版除卡文点名的 child 位置外，还"顺带纠正"了根位置 lambda。
  你的两个输入实测都成立（真危险被放行 + 合法写法被判违规）。根因是本门**没有 lambda
  作用域** —— 体内使用点解析时用的就是外层作用域表，旧那条按 PEP 572 算错的记录恰好让
  同一体内的使用点解析对了。现在 `_own_exprs` 只动 child 位置 = 恰好等于卡文划的面，
  根位置与 `B14_BASE` 逐字同。真修法（给 `Lambda` 建独立作用域）超出本卡范围，已登记移交。
- **HIGH-2 → 新增 `_outer_evaluated_parts`**，`_walk_same_scope` 现在收「在外层求值」的那些
  部分（`def`/`lambda` 的默认参数与装饰器、`class` 的装饰器与基类），体仍不进。
- **MEDIUM → 新增 `_module_binds_name`**，本模块任何位置绑过 `setattr` 这个名字，
  `collect_setattr` 整条分支不收。
- **LOW → 证据索引重写**，并加了一条「引用的文件名逐个存在性自动核」。
- **另加 4 条负控表条目锁住上述修复**（`_AST_MUST_FLAG` 51→53、`_AST_MUST_PASS` 27→29），
  因为你指出「27 条对照中没有任何 Lambda 节点，未覆盖该回归」。这**偏离卡文写死的 51/27**，
  已在验收单与 commit 里显式标出交主 session 裁定。

**最小读取面**：

- `git diff 20abe003 6564fc09 -- backend/scripts/lifespan_isolation_negative_control.py`
- 同文件：`:455-472`（`_outer_evaluated_parts`）、`:475-519`（`_walk_same_scope`）、
  `:522-543`（`_module_binds_name`）、`:546-610`（`_module_attr_write_paths`）、
  `:877-930`（`_own_exprs`）、`:1592-1663`（`_isolation_wrapper_index`）、
  `:2826-2853`（两条新 must-flag）、`:3165-3184`（两条新 must-pass）、
  `:2027-2145`（`analyze_source`）、`:3235-3300`（`run_selfcheck_fixpoint`）
- `_bmad-output/审查/evidence-ast-flag/negctl.py` 与 `negctl-anchors-20260917T091714.txt`
- `_bmad-output/审查/evidence-ast-flag/README.md`

## ② 作者自述，请独立核对

1. round-1 四条 finding **全部已修**：你给的四个输入在本轮定稿上的判定分别是
   CAUGHT / CLEAN / CAUGHT / CLEAN（`verify-r1-findings-20260917T091714.txt`）。
2. `_own_exprs` 的根位置处置与 `B14_BASE` **逐字同**，只有 child 位置的默认参数下潜是新的。
3. `--ast-negative-control` → `PASS (53 / 29)`，`FALSE POSITIVE` 计数 0。
4. 真实消费面两文件与门的 401 文件完整扫描面，违规集**与本卡改动前逐字相同**（都为空）。
5. 定向负控：六处修复**逐个**撤掉，**指定的那一条**负控输入各自变红；控制组（未变异定稿）
   红项为空。见 `negctl.py` 与其存档。
6. 公共符号名仍全部保留；新增的都是追加。

## ③ 按重要性排序的问题

0. **HIGH-1 的撤回是否彻底**？`_own_exprs` 现在的根位置行为与 `B14_BASE` 是否真的等价
   （不只是我给的三条探针输入等价）？child 位置新增的默认参数下潜，有没有别的路径能
   借它产生 round-1 那类来源解析偏差？
1. **HIGH-2 的 `_outer_evaluated_parts` 是否完整**？`def`/`lambda`/`class` 三类里，还有哪些
   子表达式实际上在外层求值而我漏列了？反过来，我列进去的有没有其实在内层求值的（那会
   造成新的误判）？`_walk_same_scope` 现在对根节点与 child 走同一条 `push` 规则，这个
   统一是否引入了别的行为变化？
2. **MEDIUM 的 `_module_binds_name` 是语法级近似**（它在作用域表建成之前就要用）。
   它收得很宽（任何位置任何绑定形态都算）是刻意的保守选择 —— 这个方向对不对？有没有
   它**漏判**遮蔽的形态（那会留下 round-1 那条误判），或者**过度**触发导致本该收的
   `setattr` 写路径被整个丢掉（那会重新打开 C4 的漏放面）？
3. **新增的 4 条负控表条目是否名实相符**？两条 must-flag 描述的危害是否真实存在，
   两条 must-pass 判 CLEAN 是否真的正确（尤其 `验伪锚 R1-M3` —— 它判 CLEAN 依赖既有的
   C4 设计，请确认这不是把一个本该被抓的形态写进了正例表）。
4. **定向负控的判据本身是否成立**？它断言的是「**指定的那一条**变红」而不是「某处失败」。
   控制组红项为空这一条是否足以支撑「结论可比」？有没有哪个变异其实是靠别的机制变红的？
5. 三条盲区修复（child lambda 默认参数 / `setattr` 写路径 / 逐条 yield 覆盖）在本轮整改后
   是否仍然成立、没有被回退？

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 与一句复现思路。
round-1 里已修的四条若你认为仍未修好，请明确说是哪一条、以及现在的失效路径。

## ⑤ 边界

只读。不跑任何变异 harness、不连 7691 / 7687、不写任何文件。不评「写侧用下标/别名/推导式
目标 + 读侧写成属性」那个组合形态（本卡明确不实现、已登记移交），也不评「给 `Lambda` 建
独立作用域」这件事本身该怎么做（已登记移交下一批）。
