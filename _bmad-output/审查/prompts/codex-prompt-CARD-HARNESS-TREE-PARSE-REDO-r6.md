# 复核任务（round-6，用户裁定后的新增范围）：CARD-HARNESS-TREE-PARSE-REDO

你是独立复核者，在做一次普通的代码评审。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..faaeb005`（最终 HEAD = `faaeb005`）。

## 一 背景

`_harness_tree` 解析 vault 的 `.canvas-config.yaml` 中的 `harness_tree` 键，决定 `REPO` ——
那棵装着 `backend/scripts/validate_learning_events.py` 的代码树。选错树 = 事件被写去绑定到
另一棵 harness，用户看不见。

round-1~5 已收敛（每轮绑当时最终 HEAD 的 BLOCKER/HIGH 都是 0，轮次 5/5 用满）。本轮是
**用户裁定后的新增范围**：用户 2026-09-14 裁定「缺 PyYAML 时直接拒写，不做任何降级解析」，
于是 `_degraded_scan` 整段删除（净减 134 行），门相应重构。

⚠️ 这条裁定是在**知道代价**之后做的。作者先前给出的「保守拒不损失一次原本能完成的写入」
已被实测证伪：在一台真正 `find_spec("yaml") is None` 的 py3.14 上三向对照 —— harness_tree
指向本仓 `b85a168a` 旧树（其 `_vault_id_of` 零 yaml）⇒ rc=0、账本 1 行、mastery 0.5→0.57；
换成当前树 ⇒ 拒写零字节；换回有 PyYAML 的解释器 ⇒ rc=0。复现脚本已入库：
`_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`。

请读：
1. `git diff 4eeaeaa6 faaeb005 -- . ':(exclude)_bmad-output'`（本轮增量，最该细看）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`grep -n "def _harness_tree"` 定位，到 `REPO = _harness_tree` 那一行）
3. `backend/tests/regression/test_g3_2_review_ledger.py`：全部 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`）与两个辅助 `_extract_harness_tree` / `_ht_outcome`
4. `_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`（三向对照复现脚本）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`

## 二 作者自述（请独立核对，不要采信）

1. PyYAML 可用时的行为**零变化**（三条分界、realpath、报错文本都没动）。
2. 缺 PyYAML 时 `_harness_tree` 对**任何** config 都抛 `SystemExit` 且点名 PyYAML，绝不返回。
3. 原 60 参数的不变量门在删除降级解析后**退化成恒真**（作者实测：一条不改全绿），已换成
   「缺库时绝不返回任何树」的强断言；负控（还原到 `4eeaeaa6`）⇒ 12 条变红。
4. 4 个降级门重构成 2 个更锐的端到端门，其中一个专门把「我们明知接受的代价」钉住。
5. 原 9 参数 noncanonical 门的形态**已全部在 60 参数 unit 层覆盖**，折叠不是覆盖损失。
6. 84 / 233 / 546 全绿；ruff 两项 0；地盘仍恰三文件。

## 三 请按重要性回答的问题

0. **PyYAML 可用时真的零行为变化吗**：逐条核 16 个既有门 + 6 个 M 门的期望，以及
   `_harness_tree` 在 yaml 分支上的每一条出口（回退 / 采用 / 三种拒）是否与 `4eeaeaa6` 逐字同义。
1. **新门里有没有恒真的**：`..._no_pyyaml_never_returns_a_tree`（60 参数）、
   `..._no_pyyaml_refuses_canonical_form_accepted_cost`、`..._no_pyyaml_refuses_even_without_the_key`
   —— 逐个判断「什么样的错误实现能让它照样绿」。作者上一版正是在这里栽过（旧不变量门退化成恒真）。
2. **作者自述 5 是否属实**：原 9 参数 noncanonical 门覆盖的形态，是否真的每一条都在 60 参数
   表里有对应项？如果有遗漏，指出是哪一条形态、现在还测不测得到。
3. **缺库拒写的用户可修复性**：那句错误消息是否足以让一个非技术用户自己修好？它会不会与
   更下游的「vault 归属无法绑定」混淆？
4. **docstring 对代价的记述是否准确**：对照复现脚本与实测数字，有没有夸大或缩小。
5. **有没有残留的降级假设**：代码注释、其他门的 docstring、验收单里，还有没有地方仍按
   「缺库会退回正则扫描」在描述行为？
6. 删除 `_degraded_scan` 有没有连带删掉任何**别处仍在依赖**的东西（辅助函数、常量、门）。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：一句话结论、`file:line`、
一句话说明在什么输入下会出现该结果。没有问题的分级请显式写「无」。

## 五 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 任何数据库。
- 不评 `backend/app/services/learning_event_log.py`（属另一张卡的面）。
- 不评 `test_g3_2_review_ledger.py` 里 harness_tree 区以外那 150 个测试的设计。
- 不评 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py`（本卡零改动）。
- 「harness 树零契约校验」已由用户裁定另立卡，本轮**不必**再论证它该不该修，只需在它影响
  本轮结论时点出。
