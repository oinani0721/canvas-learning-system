# 复核任务 — CARD-EPW-COVERAGE（第十四批 / 车道 card-t10-red）

## 一 任务

审一张**只写测试**的卡：为 `GraphitiEpisodeWorker` 新增一份等价覆盖文件、翻转去标三条
指向本卡的 `xfail(strict=True)`、并把 CARD-RED-C1 登记的 33+4 条覆盖缺口落成一张 37 行
覆盖矩阵。卡的硬边界是「⛔ 不改 `backend/app`」——被覆盖的生产代码全程只读。

请判断：新用例是否**真的**钉住了它们声称的语义、矩阵的逐条承接是否与来源清单对齐、
去标是否只发生在测试侧、是否有越地盘或误碰生产代码。

## 二 最小读取面（只读这些，路径写死）

工作目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`

1. `backend/app/services/episode_worker.py` —— 被覆盖对象（⛔ 只读，本卡未改，勿评其设计）
2. `backend/tests/unit/test_episode_worker_coverage_epw.py` —— 本卡新增的等价覆盖文件
3. `backend/tests/unit/test_story_38_6_scoring_reliability.py` —— 本卡去标处（只改了
   `TestAC1TimeoutRetryAlignment` 这个类，以及 `from app.services.episode_worker import …`
   那一行的导入清单；**其余类不是本卡改的**——`TestAC3StartupRecovery` 是上一张卡 T10-C 的面）
4. `backend/tests/unit/test_episode_worker_retry.py` —— 参照文件（本卡不改，用于判断新文件是否重复造轮子）
5. `_bmad-output/审查/evidence-epw-coverage/coverage-matrix-*.md` —— 覆盖矩阵（37 行 + 两个附录）
6. `_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py` 与
   `_bmad-output/审查/evidence-epw-coverage/coverage_matrix_check.py` —— 本卡自带的两道静态门
7. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md`
   的 §三「CARD-RED-C1 —— 33 条」代码块与「另：Y4-D 顺带关掉的 4 条『原本绿』」小节
   —— 37 条缺口的唯一来源（按节名捞，不看行号）
8. `_bmad-output/审查/evidence-epw-coverage/` 下的裁判存档 `*.txt`（可选，用于核对自述数字）

## 三 重点查什么

1. **新用例是否空洞**：每条断言是否会因被测语义改变而失败？是否存在「只要代码不抛异常就绿」
   的摆设断言？负控存档（`epw-negctl-*.txt` 红 / `epw-negctl-restored-*.txt` 绿）证明的是不是
   它声称的那条断言。特别看：退避用例把 `random.uniform` 换成「返回上界」的桩之后，
   断言的是不是真实公式 `min(2**retry_count, 60)`。
2. **覆盖矩阵是否对齐**：37 行的 nodeid 是否与 red-align §三逐条同集合；`N1+N2+15+N3=37`
   是否成立；标成「T10-C 已 un-skip 重写」的 15 条是否确实由前一卡承接（本卡第 0 分钟实测
   两处 skip 已删）；标成「语义已删·无等价·登记退役」的那 1 条理由是否站得住。
3. **承接强度是否被夸大**：等价是语义层映射，不是断言逐字复刻。文件头声明了 5 处语义
   收窄/反转（退避定值→上界、无 per-attempt 超时、错误类型区分位置、重试身份反转、
   计数器归属）。请核对这些声明**是否与代码事实一致**，以及矩阵/用例 docstring 里有没有
   **没被声明**的其它收窄。
4. **去标是否合法**：三条 xfail 的去标有没有依赖对 `backend/app` 的任何修改（应当没有）；
   改写后的两条是否名实一致；删掉的那一条是否确实无等价可写。
5. **隔离是否成立**：新文件与 38_6 里每一处 `GraphitiEpisodeWorker(` / `DeadLetterStore(`
   是否都显式传了 tmp_path 派生的死信路径（默认值是相对路径 `data/dead_letter_episodes.jsonl`，
   而裁判都在 `cd backend` 后跑）；有没有对单例工厂 `get_episode_worker()` 的直调；
   `epw_path_gate.py` 这道门自身有没有**门未覆盖的路径**（例如经 `memory_service` 的间接入口，
   它只做「import 了就必须出现 patch 目标串」的启发式）。
6. **越界**：`git diff` 面是否只有 `backend/tests/unit/test_episode_worker_coverage_epw.py`
   与 `backend/tests/unit/test_story_38_6_scoring_reliability.py` 两份代码文件（`_bmad-output` 除外）。

## 四 口径

- **只读**。不要修改任何文件，不要跑 `pytest`，不要连数据库（Neo4j 7691/7687）或任何网络服务。
- 不评 T10-C（CARD-Y4-D-TAIL）对 `TestAC3StartupRecovery` 与 `test_graphiti_json_dual_write.py`
  的 un-skip 重写质量——那是上一张卡的面，本卡只核「skip 已删」这个事实。
- 不评 `backend/app/services/episode_worker.py` 的生产设计（本卡禁改生产）。若发现生产侧隐患，
  按 MEDIUM/LOW 记为移交项即可。
- 不评 `test_qa_38_4_dual_write_extra.py` 里那条同名 reason 的 xfail——它不在本卡地盘，已登记移交。
- 判「门未覆盖的路径」时请给出**具体的对照输入**（什么样的写法会让门放行而缺陷仍在），
  不要只说「可能不够严」。

## 五 输出

按 **BLOCKER / HIGH / MEDIUM / LOW** 四级分组输出，每条给 `file:line` + 一句话事实 + 为什么它
是这一级。没有就写「该级 0 条」。最后给一段总评：这份等价覆盖能不能替代被 skip 的那 22 条
（21 条声称承接 + 1 条退役），以及哪些结论是本卡证据支撑不了的。

---

## 六 本轮变更（r4 → r5，末轮；仅本轮存在此节）

轮次：r1 = B0/H1/M4/L2 → r2 = B0/H0/M1/L4 → r3 = B0/H0/M1/L3 → r4 = **B0/H0/M0/L4**。
r2 起就在通过线内，但每轮的 M/L 都是可在测试侧关闭的真缺口，故一路整改到本轮
（`backend/app` 始终零改动）。**本轮是末轮**（协议上限 5）。按 r4 的 4 条 LOW：

- **r4 LOW-1**（上界桩最小为 1、哨兵最小 0.37 ⇒ `max(random.uniform(0, cap), 0.1)` 这种
  **下限抬升**看不出来）→ 封顶用例再跑一遍，桩返回 `0.001` 这个远低于任何合理下限的样本，
  断言属性原样交出 `[0.001, 0.001, 0.001]`。
- **r4 LOW-2**（门的常量拼接检查既漏检四段拼接、又**误杀** `str(tmp_path / ("data/" + "dead_letter.jsonl"))`）
  → 删掉按 `ast.walk` 顺序拼接那条（`walk` 是广度遍历、根本不是求值顺序），改成一条**正向**规则：
  值表达式必须至少含一个**非包装名**的 `Name`（即路径要依赖变量）。纯字面量表达式无论怎么切分
  都 FAIL；tmp_path 派生的写法都带着那个变量、不会被误杀。逐个常量的危险片段检查保留。
- **r4 LOW-3**（矩阵 #2 声称 `episodes_dead_lettered == 1`，承接用例其实只等 `>= 1`）
  → 在该用例里补上精确计数断言，让说明与实测一致。
- **r4 LOW-4**（`test_enqueue_after_stop_returns_false` 无条件要求 `stop()` 后返回 False，
  但 `QueueShutDown` 分支只在 Python 3.13+ 存在；生产容器是 python:3.11-slim）
  → 加 `skipif(not hasattr(asyncio.Queue, "shutdown"))` + docstring 写明版本边界；
  生产兼容分支本身**不改**（不在本卡地盘），登记为移交项。

负控随之扩到 **18 条**（条数由 `MUTATIONS` 的 AST 实测与驱动输出的 `── 负控` 块数双向核对）。

**本轮请重点判**：① 这 4 条是否真的关闭；② 门的新正向规则有没有引入新的**误杀**
（真实三份文件必须仍 PASS，`str(tmp_path / (…))` 形态必须 PASS）；
③ 正向规则留下的主要洞（值经变量中转、变量本身就是危险路径）是否已在 docstring 如实声明；
④ 还有没有**新**的、我这轮引入的过强声明。其余口径同上文 §一～§五。
