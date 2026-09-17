# 独立复核请求 — CARD-AST-FLAG-PATCH（第十四批 T8-D）

## ① 背景与最小读取面

`backend/scripts/lifespan_isolation_negative_control.py` 是一道 AST 静态门加它自己的
负控自检：门判「测试代码里会不会在没有隔离的情况下启动真实应用的 lifespan」，自检用
两张表互相验伪 —— `_AST_MUST_FLAG`（必须被判违规的负控输入）与 `_AST_MUST_PASS`
（必须判合规的对照输入，防「恒判违规」的假门）。

上一张卡（CARD-W4-5）记载了三条门**未被拦下**的输入形态，并说交接一份
`ast-must-flag.patch`。本卡第 0 分钟实测：该 patch 在两处记载路径与全部 worktree 下
都不存在（`find … -name '*.patch' | grep -icF ast-must-flag` = 0，同一管道
`grep -icE 'ast'` = 3 作验伪锚）。故本卡不是套 patch，是按文档记载手工补三条
`_AST_MUST_FLAG` 条目（48 → 51）并修对应的扫描盲区，外加给知识迭代的轮数上限
补一条显式「未收敛」处置。

**最小读取面（只读这些，不必读全文 3700 行）**：

- `git diff 20abe003^ 20abe003 -- backend/scripts/lifespan_isolation_negative_control.py`
- 同文件：`:455-481`（`_walk_same_scope`）、`:484-541`（`_module_attr_write_paths`）、
  `:601-607`（`_FIXPOINT_MAX_ROUNDS` 与 `FixpointNotConverged`）、`:681-723`（不动点循环）、
  `:808-847`（`_own_exprs`）、`:1438-1507`（`_mark_isolation_wrappers` docstring）、
  `:1509-1580`（`_isolation_wrapper_index`）、`:1944-2062`（`analyze_source`）、
  `:2099-2120` 与 `:2690-2742`（`_AST_MUST_FLAG` 首尾，本卡三条在尾部）、
  `:2744-2760`（`_AST_MUST_PASS` 首段）、`:3055-3079`（`run_ast_negative_control`）、
  `:3082-3168`（`_FIXPOINT_MULTI_ROUND_SRC` 与 `run_selfcheck_fixpoint`）、
  `:3366-3390`（`main` 入口与两个提前 return 的分支）
- 外审存档 `_bmad-output/审查/codex-review-CARD-W4-5-ast-high6.md` 的
  「⑤不成立：它没有检查包装器每一条 yield」一段
- 证据索引 `_bmad-output/审查/evidence-ast-flag/README.md`

## ② 作者自述，请独立核对

1. 三条新 `_AST_MUST_FLAG` 条目在改扫描器**之前**确为门未拦下的输入，改之后被判违规。
   证据：`red-lambda-*.txt` / `red-setattr-*.txt` / `red-branch-*.txt` 三份先红（每份只加
   一条条目、扫描器未动），`green-51-27-20260917T090018.txt` 后绿。
2. 后绿是 `AST-NEGATIVE-CONTROL: PASS (51 / 27)`，`_AST_MUST_PASS` 27 条**全部**仍判合规
   （存档里 `CLEAN` 计数 27、`FALSE POSITIVE` 计数 0）。
3. 真实消费面（`backend/tests/support/live_port_guard.py`、
   `backend/tests/support/guard_plugin.py`）的 `analyze_source` 结果、以及门的 401 文件
   完整扫描面的违规集，**改前改后逐字相同**（都为空）。
4. 「未收敛」处置不是静默的：跑满上限抛 `FixpointNotConverged`，`analyze_source` 把它转成
   一条违规明细返回。`--selfcheck-fixpoint` 先红（副本仅剔掉那一处 hunk、保留子命令本身）
   后绿，红正文含两条 `MISSED: 未收敛未被报出`。
5. 公共符号名全部保留：`analyze_source` / `run_ast_negative_control` / `_own_exprs` /
   `_module_attr_write_paths` / `_AST_MUST_FLAG` / `_AST_MUST_PASS` 一个没改名
   （跨车道消费方 `lifespan_isolation_guard_probes.py:660/:745` 按模块动态加载、按符号取用）。

## ③ 按重要性排序的问题

0. `_own_exprs` 对 `ast.Lambda` 改成「只产出 `args.defaults` / `args.kw_defaults`、不进体」，
   与 `def` 的 `args.defaults` 是否真的同口径？会不会把 lambda **体内**的表达式也带出来、
   从而给合法写法造成新的误判？另外本卡把「根节点自己就是 lambda」这一支也一并纳入同一规则
   （旧实现在该位置会走遍 lambda 体）—— 这个顺带的行为变更是否有未被 27 条对照输入覆盖的风险面？
1. `_module_attr_write_paths` 新增的 `setattr` 分支：对**非常量属性名**、对别名对象、对
   `setattr` 这个名字本身被局部重新绑定的情形，处置是否与注释里写的一致？有没有把合法写法
   错误地收进写路径集（那会收回本该成立的 C4 豁免）？`delattr` / `object.__setattr__` /
   `vars(mod)[...] = ...` 同族形态本卡未覆盖并已登记移交，这个范围划法是否合理？
2. `_isolation_wrapper_index` 从「存在某个 `with` 体内有一次合格 yield」改为「每一条到达
   调用方的 yield 都被隔离同一形参的那些 `with` 体覆盖」：是否误伤既有 27 条对照输入里的
   合法让出？「多条分支各自隔离」的写法在新判据下仍合格这一点是否成立（作者的 docstring
   这样写，并在 `probe-isolation-boundaries-*.txt` 里实测过六条边界）？按节点 `id()` 比对
   身份而不是数个数，这个选择有没有别的失效面？
3. `_FIXPOINT_MAX_ROUNDS = 8` 的取值：是否 ≥ 真实源的收敛轮数？会不会对正常运行误报未收敛？
   作者的依据是 instrument 实测（负控输入最多 3 轮、401 文件扫描面最多 2 轮，见
   `fixpoint-rounds-instrument-*.txt`）。这个依据本身可靠吗？
4. `--selfcheck-fixpoint` 用的承重输入是否**真的**需要 ≥2 轮？该自检的五步里，有没有哪一步
   在「把修复移除」之后仍然会通过（即门未覆盖的路径）？先红那份是靠 `sed` 从定稿副本里剔掉
   一处 hunk 造出来的，这个红是否确实来自「缺未收敛处置」而不是别的原因？
5. 公共符号名是否全部保留、消费方是否不被打断？

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` 与一句复现思路。

## ⑤ 边界

只读。不跑任何变异 harness、不连 7691 / 7687、不写任何文件。不评「写侧用下标/别名/推导式
目标 + 读侧写成属性」那个组合形态（本卡明确不实现、已登记移交），也不评既有隔离判定设计
在本卡改动面之外的其余部分。
