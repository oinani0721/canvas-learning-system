# 复核任务（round-7，用户裁定后新增范围的第 2 轮）：CARD-HARNESS-TREE-PARSE-REDO

你是独立复核者，在做一次普通的代码评审。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..8d973a29`（最终 HEAD = `8d973a29`；`faaeb005` 是 round-6 审过的中间态）。

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
1. `git diff faaeb005 8d973a29 -- . ':(exclude)_bmad-output'`（本轮增量，最该细看）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`grep -n "def _harness_tree"` 定位，到 `REPO = _harness_tree` 那一行）
3. `backend/tests/regression/test_g3_2_review_ledger.py`：全部 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`）与两个辅助 `_extract_harness_tree` / `_ht_outcome`
4. `_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`（三向对照复现脚本）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`

## 二 round-6 结论的整改自述（请独立核对，不要采信）

round-6 判：B 0 / H 0 / M 2 / L 4。**六条全部接受并整改，无一条登记不修**：
1. **M1（折叠有覆盖损失）** —— 作者原先声称「原 9 参数形态已全在 60 参数覆盖」**是错的**。
   已补 `..._no_pyyaml_refuses_whole_flow_document`（整份 flow 文档，含有库控制组）与
   `..._pyyaml_adopts_these_forms`（相对路径 / 值尾 U+0085 / 续行折叠 3 参数，弄坏缺省端后
   断言**真的绑到目标树**，补回被删掉的有库侧采用控制）。
2. **M2（复现脚本在最终 HEAD 跑不出反例）** —— 已钉死 `PIN_REV = "4eeaeaa6"` 并加三条期望
   自证（任一不符即非零退出）。
3. **L3** —— 拒因补上 `sys.executable` 与绑定它的安装命令。
4. **L1 / L2 / L4** —— 三处措辞据实更正（「缺库时成功写入不可达」改条件句；「老布局从照常
   写入变拒写」**代价写大了**，已按 B 格收窄；负控计数改为「62 项中 10 unit + 2 端到端」）。

另：作者自跑了一轮**变异测试**（25 个错误实现，13 个存活），据其结果补了
`..._no_pyyaml_refuses_across_fixture_shapes`（**7 夹具形状 × 2 缺库方式 = 14 格**）与第二探针
（monkeypatch `__import__` 抛**普通 ImportError**，因为 `sys.modules=None` 抛的是
`ModuleNotFoundError`，单探针看不见 `except` 子句收窄），并把 60 参数门的消息判据由子串
改为**锚整句**。声称「新门 KILLED 9/9、阴性对照生产代码 14 格全绿」，验证脚本已入库：
`_bmad-output/审查/evidence-harness-tree/verify-new-gates-kill-mutants-20260915.py`。

102 / 251 / 546 全绿；ruff 两项 0；地盘仍恰三文件。

## 三 请按重要性回答的问题

0. **「KILLED 9/9 + 阴性对照全绿」是否属实**：请自己跑一遍那个验证脚本的逻辑（或独立重做），
   核对每个变异体确实被它声称的那一格抓住，且生产代码在 14 格里确实无一误伤。
1. **14 格形状门里有没有恒真的格**：逐格判断「什么样的错误实现能让这一格照样绿」。
   ⚠️ 作者在本卡已栽过一次（旧不变量门在降级删除后退化成恒真），这是本轮最该查的。
2. **M1 的补覆盖是否真的补回来了**：`..._pyyaml_adopts_these_forms` 的三个形态，是否确实
   恢复了「有库侧真的采用目标树」这半边控制？它的 `_disable_tree` 前提是否成立？
3. **第二探针是否名副其实**：monkeypatch `builtins.__import__` 与真实「PyYAML 装着但导入链炸」
   的差别在哪？有没有它抓不到而真实场景会出事的形态？
4. **复现脚本钉死版本后是否真能自证**：三条期望的判法有没有漏洞（例如某一条恒真）？
5. **措辞更正是否到位**：L1/L2/L4 三处改后还有没有残留；`_extract_harness_tree()` 改成
   逐字取写点 import 面之后，有没有引入新的脆弱点（例如写点改用条件导入时会怎样）。
6. 有没有哪一道**既有**门因为本轮改动而失效或变成恒真（尤其 16 个既有门 + 6 个 M 门）。

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
