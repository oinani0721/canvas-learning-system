# 复核任务（round-10，用户裁定后新增范围的第 5 轮 = 轮次上限）：CARD-HARNESS-TREE-PARSE-REDO

你是独立复核者，在做一次普通的代码评审。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..f7ffe2cb`（最终 HEAD = `f7ffe2cb`；r6~r9 审过的中间态依次为 `faaeb005` / `8d973a29` / `4c722826` / `9496f84d`）。
⛔ 本轮是**轮次上限（新增范围 5/5）**：作者已声明本轮之后不再改代码，剩余问题按合并门登记并交主 session 人审。

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
1. `git diff 9496f84d f7ffe2cb -- . ':(exclude)_bmad-output'`（本轮增量，最该细看）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`grep -n "def _harness_tree"` 定位，到 `REPO = _harness_tree` 那一行）
3. `backend/tests/regression/test_g3_2_review_ledger.py`：全部 harness_tree 门（`grep -n "def test_g33r2_harness_tree"`）与两个辅助 `_extract_harness_tree` / `_ht_outcome`
4. `_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`（三向对照复现脚本）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`

## 二 round-9 结论的整改自述（请独立核对，不要采信）

round-9 判：B 0 / **H 1** / M 2 / L 2。**五条全部接受并整改**：

1. **H1（解析期 OSError 被当成「config 不存在」⇒ 静默回退父树）** —— `open` 与 `parse` 拆成
   两个作用域：打不开 ⇒ 没有 config ⇒ 回退；**打开之后任何失败一律 fail-closed，不再豁免
   OSError**，拒因改为「.canvas-config.yaml 打开后读取/解析失败 (类型: 详情)」。
   作者注：这与 round-7 的 HIGH 属同一类问题、深了一层（一个 except 同时接住两种语义不同的失败）。
2. **M1（可调用不足以证明拿到了 PyYAML）** —— 改为**行为自证**：要求 `safe_load("a: 1")`
   给出 `{"a": 1}`，否则当作拿不到。作者明说这不是「证明它是 PyYAML」，而是「要求它在
   已知输入上表现得像个 YAML 解析器」。
3. **M2（第四探针没保护新判据）** —— 补第五、六种探针（`safe_load = 1` 不可调用 /
   `safe_load = list` 行为不对）⇒ **10 形状 × 6 探针 = 60 格**；另补一小片**有库侧**矩阵
   `..._pyyaml_available_failures_are_not_missing_config`（解析抛 OSError / 抛 ValueError /
   返回非 dict），因为那 60 格**每格都在制造「拿不到 PyYAML」**、走不到解析那一步。
4. **L1** —— 旧验证表里「INVALID = 缺陷类别被构造性消除」已就地撤销；`_ht_outcome` 的
   说明也已更正。
5. **L2** —— 计数更正为「矩阵内 11 KILLED / 2 INVALID / 1 SURVIVED，后者被有库侧格 KILLED
   ⇒ 合计 12 KILLED / 2 INVALID」。

152 / 301 / 546 全绿；ruff 两项 0；地盘仍恰三文件。

## 三 请按重要性回答的问题

0. **两条分界现在都站得住吗**：①「拿不到可用的 PyYAML ⇒ 绝不返回树」；②「打不开 config
   ⇒ 回退；打开了但读/解析失败 ⇒ 拒」。请找出**任何**一条仍能违反其一的路径。
   特别看：行为自证探针 `safe_load("a: 1")` 本身能不能被躲开（例如一个只对该输入正确、
   对文件对象乱来的假模块 —— 那正是本轮新门用来测试的形态，生产是否对它也安全）。
1. **⛔ 本轮最该查的：还缺哪个维度**（不是哪一格）。作者在本卡已**四次**栽在「缺口是一个
   维度」上：不变量门退化成恒真 / 14 格漏两条件组合 / 40 格漏「有库侧」/ 60 格漏「有库侧
   解析失败」。请检查现有全部门固定死了哪些前提，那些被固定的前提本身就是候选盲区。
2. **新加的有库侧三参数门是否恰当**：`parse_returns_junk` 判「回退」而另两条判「拒」——
   这个分界对吗？有没有第四种有库侧失败形态是它没覆盖而后果同样严重的？
3. **行为自证的代价**：每次解析前多跑一次 `safe_load("a: 1")`，有没有副作用或性能问题？
   在真实 PyYAML 下它会不会因某些配置（如自定义 Loader 注册）而失败？
4. **作者这一轮的两处自查纠错**（变异插错位置、判定逻辑写反）是否已在文档中如实记录、
   且没有留下与之矛盾的旧表述？
5. 有没有哪一道**既有**门因本轮改动而失效或变成恒真。
6. ⛔ **本轮是轮次上限**。若仍有 BLOCKER/HIGH，请明确指出它是否**必须**在合入前修复，
   以便主 session 人审时据以裁定。

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
