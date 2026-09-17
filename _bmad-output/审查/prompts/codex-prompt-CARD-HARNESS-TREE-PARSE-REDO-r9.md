# 复核任务（round-9，用户裁定后新增范围的第 4 轮）：CARD-HARNESS-TREE-PARSE-REDO

你是独立复核者，在做一次普通的代码评审。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..9496f84d`（最终 HEAD = `9496f84d`；`faaeb005` / `8d973a29` / `4c722826` 是 r6 / r7 / r8 审过的中间态）。

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
1. `git diff 4c722826 9496f84d -- . ':(exclude)_bmad-output'`（本轮增量，最该细看）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`grep -n "def _harness_tree"` 定位，到 `REPO = _harness_tree` 那一行）
3. `backend/tests/regression/test_g3_2_review_ledger.py`：全部 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`）与两个辅助 `_extract_harness_tree` / `_ht_outcome`
4. `_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`（三向对照复现脚本）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`

## 二 round-8 结论的整改自述（请独立核对，不要采信）

round-8 判：B 0 / **H 0** / M 3 / L 2。**五条全部接受并整改，无一条登记不修**：

1. **M1（「import 成功」≠「拿到 PyYAML」：空的同名 yaml.py 照样导得进）** —— 导入后加判
   `callable(getattr(yaml, "safe_load", None))`，不成立即抛（走同一条缺库拒因）。
   并加**第四种探针** `imports_but_not_pyyaml`（`sys.modules["yaml"] = object()`）。
2. **M2（作者上一轮误判「P2 变异点被构造性消除」）** —— 作者承认判错：那只是旧文本锚失配。
   根因在矩阵的维度 —— 40 格**每格都在制造「拿不到 PyYAML」**，没有一格是「PyYAML 好好的、
   但 config 不存在」。已补 `..._pyyaml_available_no_config_falls_back_to_parent`，
   并实测 `M2-read-before-import` 变异体被它 KILLED。
3. **M3（「只在无 config 时才采用变量/缓存」从组合缝里穿过）** —— 已补两格组合形状
   `no_config_and_env_set` / `no_config_and_sidecar` ⇒ **10 形状 × 4 探针 = 40 格**。
4. **L1** —— 安装命令改用 `shlex.quote`（只加双引号挡不住 `$VAR` / `$(...)` / 反引号）。
5. **L2** —— 措辞残留四处全清。

作者自跑验证：**KILLED 11/14**（3 个 INVALID = 代码变了、旧文本锚失配，作者声明**不再据此
宣称缺陷类别消除**）；**阴性对照生产代码 40 格全绿**，且有库侧那一格正确回退父树。

129 / 278 / 546 全绿；ruff 两项 0；地盘仍恰三文件。

## 三 请按重要性回答的问题

0. **「拿不到 PyYAML 绝不返回树」现在是真的吗**：加了 `safe_load` 可调用性判断之后，
   还有没有**任何**一条路径能在「拿不到可用的 PyYAML」时返回一棵树？请特别看：
   `safe_load` 存在但**行为不对**（例如返回固定值、或本身抛异常）时会怎样；以及
   `getattr` 判据能不能被一个「有 safe_load 属性但不是函数」的对象躲过去。
1. **40 格 + 有库回退门里有没有恒真的**：逐格判断「什么样的错误实现能让它照样绿」。
   ⚠️ 作者在本卡已栽过**三次**（不变量门退化成恒真；14 格漏两条件组合；24 格漏「有库侧」
   整个维度）。请专门找**还缺哪个维度**，而不只是缺哪一格。
2. **组合覆盖是否补全**：现在有「无 config × {父树 / 变量 / 缓存}」三格，但
   「有 config × 变量」「有 config × 缓存」「父树 × 变量」等其它交叉呢？哪些是真需要的、
   哪些是冗余的？给出判断依据，不必穷举。
3. **第四探针是否名副其实**：`sys.modules["yaml"] = object()` 与真实「空的同名 yaml.py」
   的差别在哪？有没有它抓不到而真实场景会出事的形态？
4. **`shlex.quote` 是否真的够**：还有没有解释器路径形态会让那条命令不可照抄？
5. **作者对 INVALID 的新定性是否到位**：他声明「不再据此宣称缺陷类别消除」，那验收单与
   测试里还有没有残留的同类外推？
6. 有没有哪一道**既有**门因本轮改动而失效或变成恒真。

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
