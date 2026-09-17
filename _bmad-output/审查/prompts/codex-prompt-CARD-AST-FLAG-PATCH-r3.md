# 独立复核请求 round-3 — CARD-AST-FLAG-PATCH（第十四批 T8-D）

## ① 背景与最小读取面

round-2（绑 `6564fc09`）你给出 BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 1。七条**全部经本车道
独立复现后接受，无一条驳回**。本轮请复核整改本身，绑定 **`a03af47c`**（代码树与 `5f9fd306`
逐字同，其后只有一个纯 `_bmad-output` 提交）。

整改逐条：

- **HIGH-1（我 r1 自造的回归）** → `_own_exprs` 的栈现在带一位 `in_lambda_body`：进了某个
  lambda **体**就是调用时求值，「默认参数归外层」在那里不成立。lambda 展开抽成
  `_lambda_outer_defaults`（递归，产出里不含 lambda）。根位置行为与 `B14_BASE` 逐字同。
- **HIGH-2（我 r1 自造的回归）** → `_walk_same_scope` 的 `push` 改成**递归**：部件再过一次
  `push`，默认值自身是 lambda 时不再被当普通节点走遍。
- **HIGH-3（既有缺口 + 我一条错结论）** → `_outer_evaluated_parts` 补收 `arg.annotation` 与
  `node.returns`。我上一轮断言「注解里不能写 `yield`」是**只在本机 3.14 上**测的；逐版本
  复测确认 3.11.15 上两种写法都合法且外层真多一条 `YIELD_VALUE`，CI matrix 是 3.11/3.12。
- **HIGH-4 + MEDIUM-5（我 r1 自造的 fail-open + 漏判）** → `_module_binds_name` 改为**只看
  顶层绑定**，并补 `MatchAs` / `MatchStar` / `MatchMapping.rest` / `ExceptHandler.name` 四种
  不含 `Name` 节点的真绑定。
- **MEDIUM-6** → 本轮提交收录**完整**单测日志（1185 行，含汇总行与 `rc=`）并重生成两份
  `nodeids`；**LOW-7** → 索引重写，占位引用清零，自检口径加「占位计数须为 0」。
- **另加 8 条负控表条目**锁住上述修复（`_AST_MUST_FLAG` 53→59、`_AST_MUST_PASS` 29→31）。
  连同 r1 的 4 条，本卡共偏离卡文写死的 51/27 十二条，已在验收单与提交里显式标出交主 session。

**最小读取面**：

- `git diff 6564fc09 a03af47c -- backend/scripts/lifespan_isolation_negative_control.py`
- 同文件：`:455-485`（`_outer_evaluated_parts`）、`:488-538`（`_walk_same_scope`）、
  `:541-586`（`_module_binds_name`）、`:589-602`（`_lambda_outer_defaults`）、
  `:605-669`（`_module_attr_write_paths`）、`:936-995`（`_own_exprs`）、
  `:1657-1728`（`_isolation_wrapper_index`）、`:2092-2210`（`analyze_source`）、
  `:2920-3004`（六条新 must-flag）、`:3335-3355`（两条新 must-pass）
- `_bmad-output/审查/evidence-ast-flag/` 的 `README.md`、`negctl.py`、
  `negctl-anchors-20260917T093255.txt`、`verify-r2-findings-20260917T093255.txt`、
  `probe-annotation-yield-by-version-20260917T093019.txt`、`territory-FINAL.txt`

## ② 作者自述，请独立核对

1. round-2 七条 finding **全部已修**：你给的每个输入在本轮定稿上的判定见
   `verify-r2-findings-20260917T093255.txt`（`B14_BASE` / r1 定稿 / 现版三版对照，11 个输入）。
2. `_own_exprs` 的**根位置**行为与 `B14_BASE` 逐字同；只有 child 位置的默认参数下潜是新的
   （`probe-lambda-scope-20260917T093307.txt`）。
3. `--ast-negative-control` → `PASS (59 / 31)`，`FALSE POSITIVE` 计数 0。
4. 真实消费面两文件与门的 401 文件完整扫描面，违规集**与本卡改动前逐字相同**（都为空）。
5. 定向负控扩到 **11 个变异**：逐个撤掉一处修复、断言**指定的那一条**变红，控制组红项为空。
   每个变异锚 `assert count == 1`，锚漂移直接抛（本轮实测抓到过一次：`ruff format` 折行后
   某个锚命中 0 次）。
6. 单测日志完整（含汇总行与 `rc=`），与 64 条基线 nodeids diff 为空；地盘回执见
   `territory-FINAL.txt`；公共符号名仍全部保留。

## ③ 按重要性排序的问题

0. **HIGH-1 / HIGH-2 的修法是否彻底**？`in_lambda_body` 只是一位布尔状态，不是真正的作用域链 ——
   更深的嵌套、lambda 与 `def` 交替嵌套、`async` 形态里，有没有它判错的路径？
   `_lambda_outer_defaults` 的递归终止与产出集合是否真的「不含 lambda」？
   递归 `push` 会不会在某些形态下无限递归或漏掉部件？
1. **HIGH-3 的补收是否过界或仍不足**？`arg.annotation` 覆盖了 posonly / args / kwonly /
   vararg / kwarg 五类 —— 有没有漏的？把注解纳入「外层求值」在 3.14（PEP 649 注解作用域）
   下会不会造成**新的误判**（我的判断是不会，因为那边 `yield` 根本进不来，但请独立核）？
   `class` 的 `keywords` / `bases` 是否也该按同样口径处理，我列了但没准备对照输入。
2. **HIGH-4 + MEDIUM-5 的收窄是否留下新的 fail-open**？「只看顶层绑定」对
   `if TYPE_CHECKING:` 之类**顶层条件块内**的绑定、对 `try/except` 顶层块内的绑定，
   行为是否符合预期？四种 pattern/except 绑定形态是否覆盖完整（还有别的无 `Name` 节点的
   绑定形态吗）？我如实登记的那条残留（调用写在有局部同名绑定的函数体里 ⇒ 过收 ⇒ fail-closed
   误判）方向判断是否正确？
3. **新增的 8 条负控表条目是否名实相符**？两条注解锚在本机 3.14 上 `compile` 不过、但
   `ast.parse` 过 —— 我实测它们是因「TestClient 未被隔离」而红、不是因 `SyntaxError` 而红，
   请独立确认这不是空门。两条 must-pass（`match case setattr` / `except as setattr`）判 CLEAN
   是否真的正确？
4. **定向负控的 11 个变异是否各自成立**？有没有哪个变异其实是靠别的机制让指定锚变红的？
   控制组为空这一条的证明力边界（你 round-2 已指出，我已写进验收单）是否还有别的说法？
5. 三条原始盲区（child lambda 默认参数 / `setattr` 写路径 / 逐条 yield 覆盖）在两轮整改后
   是否仍然成立、没有被回退？公共符号名是否仍全部保留？

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 与一句复现思路。
前两轮已修的十一条若你认为仍未修好，请明确说是哪一条、以及现在的失效路径。

## ⑤ 边界

只读。不跑任何变异 harness、不连 7691 / 7687、不写任何文件。不评「写侧用下标/别名/推导式
目标 + 读侧写成属性」那个组合形态（本卡明确不实现、已登记移交），也不评「给 `Lambda` 建
独立作用域」这件事本身该怎么做（已登记移交下一批）。
