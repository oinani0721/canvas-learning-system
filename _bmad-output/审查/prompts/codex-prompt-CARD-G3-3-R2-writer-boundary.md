# 独立代码复核请求 — CARD-G3-3-R2-writer-boundary

## 一 背景与最小读取面

仓库根（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

这是一个本地学习系统。`quiz-answer` 是一个「给自己的测验打分」的写点：它读一份 JSON payload，
更新知识节点 markdown 的 frontmatter（写一条 receipt），并往 append-only 的
`learning_events.jsonl` 账本追加一行。本次改动修的是一个**已被复现的输入校验缺失**：
payload 里的 `self_confidence_norm`（自评分数）此前没有任何类型/取值检查，
就被裸插值进 receipt 的 YAML 条目里，而它与该条目的 `event_id`（幂等键）同处一段，
于是一个带换行的值可以让该条目多出一行、改掉这条 receipt 的身份标识。
观察到的后果：首次写入返回 0，此后每一次对该节点的评分都返回 1（该节点无法再评分）。

**请只读以下范围**（不需要读别的文件；不要运行任何写操作）：

1. `git diff 8686d169 609ce455 -- . ':(exclude)_bmad-output'` —— 本次全部代码改动（5 文件，+536/-18）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:290-420`
   （写点入口区：新增的 `self_confidence_norm` 门在 `:333-341`，`_harness_tree` 在 `:356-394`，
   `REPO = _harness_tree(VAULT)` 在 `:396`）
3. 同文件 `:1480-1600`（改后实测范围：`:1499` 读该字段、`:1513` 复放路径、`:1587` 拼进 YAML —— 这三行本次**未改**）
4. `backend/app/services/learning_event_log.py` 的 `:150-280`
   （新增 `_EVENT_ID_FORBIDDEN_RANGES` / `_EVENT_ID_MAX_LEN` / `_event_id_shape_problems`，
   以及它在 `append_event` 里的挂载点）
5. `backend/scripts/validate_learning_events.py` 的 `:1600-1700`
   （本次只改了注释；`CHARSET_STRICT_FIELDS` 与 `FORBIDDEN_CODEPOINT_RANGES` 未改，
   后者的定义在 `:426-450`，需要时可一并读）
6. `backend/tests/regression/test_g3_2_review_ledger.py` 的 `:6294-6330`（转正的那个测试）与 `:6680-` 起的新增段
7. `backend/tests/regression/test_learning_event_log.py` 的 `:77-` 起的新增段
8. `_bmad-output/审查/evidence-g33r2/event-id-shapes-20260908T092658.txt`（写门之前做的只读样本普查）

## 二 作者自述——请独立核对，不要采信

以下每一条都是我的声明，请自行到代码里验证，并明确指出哪些不成立：

1. **门在任何写入之前**：`self_confidence_norm` 的检查位于写点入口区，在 `evid` 拼好之后、
   在任何文件写入（账本追加、frontmatter 原子写、临时文件）之前。
2. **`:1587` 那行拼接未改**：该字段的读取点与拼接点一字未动，新门是它们唯一的上游；
   因此下游只可能拿到 `None` 或 `float`。
3. **形态门不误拒既有调用方**：`append_event` 的 5 个生产调用点（`memory.py` / `tips.py` /
   `errors.py` ×2 / `conversation_distiller.py`）与既有回归样本（含 `x-1`、`wrong` 这种
   无前缀 id）以及真实账本里的 id（含内部空格、中文、括号、`&`，有的没有 `#` 段）
   全部被放行。
4. **`CHARSET_STRICT_FIELDS` 未扩**：该表逐字未动（我用两份不依赖行号的快照做了前后对照）。
5. **`harness_tree` 解析不回退**：配置里写了该键但指向的目录不存在时，写点拒绝并报错，
   而不是悄悄退回「vault 的父目录」。
6. **三个变异 harness 的锚点命中数不变**：`g32b` / `g32cb` / `g32ccr1` 的 `--list`
   输出在改动前后逐字相同，异常锚点数为 0。

## 三 请按重要性排序回答的问题

1. 入口门与 `:1499` 那次读取之间，有没有**别的路径**会重新写回 `p["self_confidence_norm"]`
   或让这道门不生效？特别看复放分支（`:1513` 附近）与增量归纳块。
2. 「不接受数字串」这个裁定是否引入了新的问题？反过来看：如果将来有人改成接受字符串并加
   `strip()`，`strip()` 会吃掉哪些字符、这是否会让被吃掉的部分重新变得可控？
3. 形态门对 C0/C1/代理区/noncharacters 的判据，与校验器 `value_charset_problems` 是否
   **真的同口径**？哪一侧更宽？如果两边不一致，方向上是「误拒」还是「漏网」，各自后果是什么？
   （我用一个测试断言两侧的范围元组相等，另一个测试比对同一批输入的结论；请判断这两个断言
   是否真的承重——换句话说，有没有哪种改动会让它们在本该报错时仍然通过。）
4. `_harness_tree` 在这些输入下的行为是否合理：值为空字符串、带引号的空串、指向一个**文件**
   而不是目录、`backend/scripts` 是一个符号链接、值里含 `#`、相对路径。
5. 去掉 `xfail` 之后，`:6323-6330` 的「写入分支」（`returncode == 0` 之后那几行）是否已经
   **不可达**？如果恒不可达，把它留着算不算一条死判据？我在 docstring 里主张它是「方向判据」，
   请评估这个主张。
6. 新增的测试用例里，有没有**判据比它声称的宽或窄**的？特别是那些断言「拒绝」的用例——
   它们能否区分「被本次新增的门拒绝」与「被上游某道既有门拒绝」？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何观察到它（走哪条路径、什么输入下会显现）

没有问题的级别请明确写「无」。

## 五 边界

- 只读复核，不要修改任何文件，不要运行测试或任何写操作。
- 不要连接任何数据库或网络服务。
- 不评审 `start-exam-board` 与 `ai-linked-doc` 这两个写点（它们的问题本次只做登记，不在范围内）。
- 不评审变异 harness 的全量覆盖率（那属于另一张卡）。
- `_bmad-output/` 下除第 8 项那份普查存档外，不必阅读。
