# 独立复核请求 round-4 — CARD-AST-FLAG-PATCH（第十四批 T8-D）

## ① 背景与最小读取面

round-3（绑 `a03af47c`）你给出 BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2。五条**全部经本车道
独立复现后接受，无一条驳回**。本轮请复核整改，绑定 **`a22254ab`**（代码树与 `e9b36cb3`
逐字同，其后只有一个纯 `_bmad-output` 提交）。

整改逐条：

- **HIGH-1 + HIGH-2 + MEDIUM-3 → 一并由「整条撤回」消掉。** `_module_binds_name` 已从文件里
  **删除**，`collect_setattr` 退回恒收。理由是你 HIGH-2 指出的那件事：一次绑定证明不了每个
  调用点都被遮蔽（`except E as setattr` 退出删名 / `if TYPE_CHECKING:` 不执行 / 遮蔽写在调用
  之后），而 `_module_attr_write_paths` 在 `_ModuleIndex` 建作用域表**之前**就被调用，拿不到
  调用点的作用域链、执行顺序与运行时可达性。
  代价是回到 round-1 那条 MEDIUM（本模块自定义一个不写属性的 `setattr` 时会被误判为违规），
  方向 **fail-closed**，已登记移交。补了 4 条 must-flag 锚（`:2962` 起）与 1 个「回装开关」
  变异；与该功能绑定的 3 条 must-pass 锚随之删除。
- **LOW-4** → 变异目标改 **ID 段精确相等**匹配，并在开跑前断言每个目标 ID 在两表里恰好 1 条。
- **LOW-5** → 索引自检收紧为三条（存在性 / 尖括号占位 / 省略号），各带验伪锚，脚本
  `readme_selfcheck.py`。顺带说明：该脚本与 README 的说明文字**刻意不字面写出**被禁形态 ——
  第一版写了，自检被自己的文档判红。
- 你要求收窄的那句「根位置与 `B14_BASE` 逐字同」已收窄，见验收单 §五.15。

**最小读取面**：

- `git diff a03af47c a22254ab -- backend/scripts/lifespan_isolation_negative_control.py`
- 同文件：`:455-485`（`_outer_evaluated_parts`）、`:488-538`（`_walk_same_scope`）、
  `:541-554`（`_lambda_outer_defaults`）、`:557-626`（`_module_attr_write_paths`）、
  `:893-952`（`_own_exprs`）、`:1614-1685`（`_isolation_wrapper_index`）、
  `:2049-2167`（`analyze_source`）、`:2962-3010`（四条新 must-flag）
- `_bmad-output/审查/evidence-ast-flag/` 的 `README.md`、`negctl.py`、`readme_selfcheck.py`、
  `negctl-anchors-20260917T094933.txt`、`verify-r3-findings-20260917T094933.txt`、
  `selfaudit-r3-recheck-20260917T095015.txt`、`territory-FINAL.txt`

## ② 作者自述，请独立核对

1. round-3 五条 finding **全部已处置**；四版对照见 `verify-r3-findings-20260917T094933.txt`。
2. `--ast-negative-control` → `PASS (63 / 28)`，`FALSE POSITIVE` 计数 0。
3. 真实消费面两文件与门的 401 文件完整扫描面，违规集**与本卡改动前逐字相同**（都为空）。
4. 定向负控 **9 个变异**全部杀掉指定的那一条；目标 ID 唯一性开跑前断言通过（9/9 各命中 1 条）；
   控制组红项为空。
5. 单测日志完整、与 64 条基线 nodeids diff 为空；地盘回执 `territory-FINAL.txt`；
   公共符号名仍全部保留；`backend/app` 零触及。

## ③ 按重要性排序的问题

0. **「整条撤回」是否留下了没收干净的尾巴**？文件里还有没有对已删函数的引用、或只在那个
   开关成立时才正确的注释 / 判据？`collect_setattr` 现在恒收 —— 除了我已登记的那条
   fail-closed 误判（本模块自定义不写属性的 `setattr`），还有别的形态会因此被误判吗？
1. **四条新 must-flag 锚是否名实相符**？它们声称「谁再加回模块级遮蔽开关就当场红」——
   `negctl.py` 里那个「回装开关」变异是否足以代表一类实现，还是只挡住了我写的那一种？
2. **前三轮修好的十一条是否仍然成立**？尤其 lambda 那几条（`in_lambda_body` 状态、
   `_lambda_outer_defaults` 递归、`push` 递归）与注解补收，有没有被本轮改动带偏？
3. **定向负控的 ID 唯一性断言是否真的解决了你 LOW-4 指出的问题**？断言只在**开跑前**对
   未变异的表做一次 —— 变异体里 ID 集合会变吗？若会，断言还成立吗？
4. **索引自检的三条是否覆盖完整**？除了错时间戳、尖括号占位、省略号，还有别的「引用看起来
   像真名但不是」的形态吗（例如大小写差异、目录前缀、反引号内带空格）？
5. 三条原始盲区（child lambda 默认参数 / `setattr` 写路径 / 逐条 yield 覆盖）是否仍成立？

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 与一句复现思路。
前三轮已处置的十六条若你认为仍未处置好，请明确说是哪一条、以及现在的失效路径。

## ⑤ 边界

只读。不跑任何变异 harness、不连 7691 / 7687、不写任何文件。不评「写侧用下标/别名/推导式
目标 + 读侧写成属性」那个组合形态（本卡明确不实现、已登记移交），不评「给 `Lambda` 建独立
作用域」该怎么做（已登记移交），也不评「`setattr` 遮蔽判定该怎么做对」（本卡已判定它需要
本函数拿不到的三样信息，整条撤回并登记移交下一批）。
