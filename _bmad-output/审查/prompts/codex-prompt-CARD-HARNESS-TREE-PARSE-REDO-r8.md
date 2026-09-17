# 复核任务（round-8，用户裁定后新增范围的第 3 轮）：CARD-HARNESS-TREE-PARSE-REDO

你是独立复核者，在做一次普通的代码评审。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..4c722826`（最终 HEAD = `4c722826`；`faaeb005` / `8d973a29` 是 r6 / r7 审过的中间态）。

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
1. `git diff 8d973a29 4c722826 -- . ':(exclude)_bmad-output'`（本轮增量，最该细看）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`grep -n "def _harness_tree"` 定位，到 `REPO = _harness_tree` 那一行）
3. `backend/tests/regression/test_g3_2_review_ledger.py`：全部 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`）与两个辅助 `_extract_harness_tree` / `_ht_outcome`
4. `_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`（三向对照复现脚本）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`

## 二 round-7 结论的整改自述（请独立核对，不要采信）

round-7 判：B 0 / **H 1** / M 1 / L 2。**四条全部接受并整改，无一条登记不修**：

1. **H1（import 与读 config 共用一个 try ⇒ 导入抛 OSError 被当成「没有 config」⇒ 静默回退
   父目录）** —— 已拆成**两个 try**。拿 PyYAML 那一层用 `except Exception`（裁定是「拿不到
   就拒写」，拿不到的原因有多少种不重要），并把 `type(_ie).__name__: _ie` 写进拒因。
   作者实测：导入抛 `PermissionError` ⇒ 拒写，不再回退。
2. **M1（14 格漏掉「无 config **且** 父目录是可用树」的组合）** —— 已补第八种形状
   `no_config_and_parent_is_tree`，并加第三种探针 `import_raises_oserror`
   ⇒ **8 形状 × 3 探针 = 24 格**。
3. **L1** —— 安装命令里的解释器路径加引号并转义内部引号。
4. **L2** —— 措辞残留六处全清（验收单四处 + 测试两处），含一处与紧随其后的更正自相矛盾、
   一处把调用顺序说反。

作者自跑的变异验证：**KILLED 10/11**，阴性对照生产代码 **24 格全绿**；唯一非 KILLED 的
`P2-open-before-import` 为 **INVALID（锚点命中 0 次）**，作者称「H1 的修法从结构上消掉了
那个变异点」。验证脚本已入库：
`_bmad-output/审查/evidence-harness-tree/verify-new-gates-kill-mutants-20260915.py`。

112 / 261 / 546 全绿；ruff 两项 0；地盘仍恰三文件。

## 三 请按重要性回答的问题

0. **H1 真的修干净了吗**：拆成两个 try 之后，还有没有**任何**一条路径能在「拿不到 PyYAML」
   时返回一棵树（而不是拒）？请特别看：拿 PyYAML 那一层的 `except Exception` 会不会吞掉
   本不该吞的东西（例如 `KeyboardInterrupt` / `SystemExit` 是否受影响）；以及 `_exe_q`
   的引号处理在哪些路径形态下仍会出错。
1. **24 格里有没有恒真的格**：逐格判断「什么样的错误实现能让这一格照样绿」。
   ⚠️ 作者在本卡已栽过两次（旧不变量门退化成恒真；14 格漏掉两条件同时成立的组合），
   这是本轮最该查的。请特别找**还需要几个条件同时成立**才测得到的组合。
2. **作者称 `P2-open-before-import` 变 INVALID 是「变异点被构造性消除」** —— 属实吗？
   还是只是换个写法就能再做出同类变异（例如把 open 移进拿 PyYAML 那个 try）？
3. **第三探针 `import_raises_oserror` 是否名副其实**：monkeypatch `__import__` 抛
   `PermissionError` 与真实「yaml 包源码不可读」的差别在哪？
4. **「拿不到 PyYAML 的原因」被写进拒因**，会不会泄漏不该出现在用户可见文本里的东西
   （路径、环境细节）？
5. **措辞更正是否到位**：r7 点的六处残留改后还有没有；有没有新引入的自相矛盾。
6. 有没有哪一道**既有**门因为本轮改动而失效或变成恒真（尤其 16 个既有门 + 6 个 M 门 +
   上一轮新加的 flow 文档门 / 采用门）。

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
