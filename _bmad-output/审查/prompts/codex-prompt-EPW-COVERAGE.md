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

## 六 本轮变更（r2 → r3，仅本轮存在此节）

r1 = B0/H1/M4/L2，r2 = **B0/H0**/M1/L4。r2 已达 D-15 通过线，但其 MEDIUM 1 + LOW 4 都是真缺口且
可在测试侧关闭，故继续整改并再送一轮（`backend/app` 仍零改动）：

- **r2 MEDIUM-1**（上界桩分辨不出 `uniform(0, cap)` 与 `uniform(cap/2, cap)`）
  → `test_retry_actually_sleeps_backoff_seconds_series_2_4_8` 的桩改成返回**区间 1/4 点**
  （`low + (high-low)*0.25`），并新增对 `random.uniform` **实参**的等值断言
  `uniform_calls == [(0,2),(0,4),(0,8)]`（下界必须是 0），实际 sleep 值断言相应变成 `[0.5,1.0,2.0]`。
- **r2 LOW-1**（`to_dict()` 把 `queue_depth`/耗时写死成 0 也能通过）
  → 新增 `test_worker_metrics_to_dict_serializes_nonzero_depth_and_times`（喂已知样本求值：
  `queue_depth=7` / `avg=1000.0` / `max=1500.0`，并钉 100 条滑窗），
  `test_queue_full_drops_and_counts` 补 `to_dict()["queue_depth"] == 1` 的序列化观察点。
- **r2 LOW-2**（门放行 `str("危险字面量")` 与跨模块 `import … as` 别名）
  → 危险字面量改成**递归扫表达式子树**里的每个字符串常量（`str(...)` 包一层、f-string 都命中）；
  别名收集**不限来源模块**。docstring 的「已封 / 仍未封」两段按实际能力重写。
- **r2 LOW-3**（重叠表低估参照文件）→ 逐行重数：同题 8 / 部分同题 6 / 未触及 7（8+6+7=21），
  #1 移入「同题」（参照文件有 `episodes_failed == 4` 的等式）、#20 移入「同题」
  （参照文件的失败形态就是 `RuntimeError`）。
- **r2 LOW-4**（warning 只验首尾两条）→ 改为逐条核 `attempt 1/3`、`2/3`、`3/3`。

**本轮请重点判**：① 上述整改是否真的关闭了对应问题；② 新写法本身有没有新的门未覆盖的路径
（特别是 1/4 点桩与 `uniform_calls` 断言的组合，是否还留有「实际重试不走 `backoff_seconds`」的对照输入）；
③ 重叠表这次的分类是否与参照文件的实际断言逐条对得上。其余口径同上文 §一～§五。
