# 独立复核请求 — CARD-W4-SENTINEL-REBIND（W4 哨兵判据改绑 + conftest sha 三态）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`
分支 `card/t9-w4`，前提 commit `PREREQ = a4dbd156`（前一卡 CARD-W4-4b7-TAIL 末 commit），
**审查 SHA `86535afb`**。

**请只读这几处**：

1. `git --no-pager diff --no-color a4dbd156 86535afb -- . ':(exclude)_bmad-output'`（代码面全部改动，恰 4 文件）
2. `backend/tests/support/w4_sentinel_identity.py` **全文**（283 行，新增）
3. `backend/tests/support/hygiene_snapshot_tristate.py` **全文**（55 行，新增）
4. `backend/tests/unit/test_w4_sentinel_rebind.py` **全文**（300 行，新增）
5. `backend/tests/unit/conftest.py` 的 `:76-98`（`_hygiene_snapshot`）与 `:288-395`
   （卫生断言主体，本卡只改其中 `:311-330` 的 sha 路由）
6. 只读锚（**不评其设计**，只作解析对象的事实依据）：
   `backend/tests/support/live_port_guard.py` 的 `:205`/`:207`/`:225`/`:230`/`:282`/`:351-363`/
   `:440-461`/`:520-528`/`:1540-1556`/`:1588-1596`；`backend/tests/conftest.py` 的 `:179-190`/`:216-230`
7. 本卡口径更正的依据：`_bmad-output/审查/evidence-w4-sentinel-rebind/coverage-corrections-20260914T224142.txt`
8. 判据存档（同目录）：`minute-zero-20260914T222720.txt`、`anchor-drift-20260914T222824.txt`、
   `w4sr-red-20260914T224221.txt`、`w4sr-green-20260914T224407.txt`、
   `w4sr-negctl-tristate-20260914T224442.txt`、`w4sr-negctl-identity-20260914T224508.txt`、
   `unit-close-clean-20260914T225233.txt`、`unit-close-diff-20260914T225819.txt`、
   `territory-and-readonly-20260914T225322.txt`、`voided-run-20260914T225245.txt`

**背景**：`live_port_guard.py` 是 pytest 进程内的一道「看门」——用 CPython `sys.addaudithook`
拦下任何到现网 Neo4j 端口（7691/7687）的 `socket.connect`，进程退出时结账。它的「哨兵红」
此前用 pytest 的 `FAILED` nodeid 集合当身份，但同一份代码**原样重跑两次**，红会挂到**不同的
nodeid** 上（U10-A 实测 `candidate422` ↔ `mock_warning`）——归属取决于哪个用例恰好触发了那次
lifespan 健康检查，与代码无关。本卡把判据改绑到两个跨跑恒定的量，并顺带收口 conftest 卫生
快照里「两次都没读到 ⇒ 静默当未变化」那个假阴。

## 二 作者自述（请独立核对，不要采信）

**A. 三条与卡文字面冲突的口径更正**（这是本卡最需要独立复核的部分）：

1. **更正③ 失败正文产出点是 3 处不是 2 处**。卡文 §〇 与我自己的首版锚点表都写「两处」
   （`live_port_guard.py:1551` / `:1595`），实测还有 `backend/tests/conftest.py:184`。
   后果：同一条未结账记录可被印两次 ⇒ 正文行条数 ≠ `blocked` ⇒ 本卡**只判集合、不判条数**。
2. **更正④ 线程名含每跑不同的对象地址**。`asyncio-portal-<hex>` 的 hex 是对象地址；
   全仓 evidence 实测几十种不同的 hex。⇒ 照卡文 (d)② 字面把整串
   `<addr> on thread <thread>` 当身份，新判据会**原样继承它要替换掉的那个 flaky**。
   本卡实现 `normalise_thread()`：`asyncio-portal-<hex>` → `asyncio-portal-<id>`，
   只抹地址、保留线程类别（`MainThread` 与 portal 线程仍须可区分）。
3. **更正⑤ 卡文 (d)① 的「多处 `blocked=` 取值必须一致，不一致返回哨兵/抛」不成立**。
   `blocked` 是**单调**计数器（`:282` 归零、`:355`/`:361` 只 `+= 1`，全文件无减法），
   两个产出点是同一计数器的**两个时刻**（`summary_line` 由 `tests/conftest.py:227` 在
   `pytest_terminal_summary` 取；`_final_accounting` 由 atexit 在更晚取）。
   ⇒ 要求相等会在门**正常工作**的那天把它判成工具错误。本卡的不变量是 `final >= summary`，
   只有 `final < summary`（计数器倒退）才抛。

   另两条较轻的：**更正⑥** `advisory` 是「只记不拦」= 放行（`:230` 逐字），只判 `blocked`
   会把真连现网当没事 ⇒ CLI 比对整条四元组并带 `total == blocked + advisory` 自洽门；
   **更正⑦** 退出码不占用 `3`（= `FINAL_EXIT_CODE`，逐字印在被读的存档正文里），本工具用 0/1/2。

**B. 三态**：`classify_sha_change(before, after)` —— 两侧均为 hash 且相等 ⇒ `unchanged`；
均为 hash 且不等 ⇒ `changed`；**任一侧为 None（含 None↔None）⇒ `unchecked`**。
`conftest.py` 只改路由：`changed` 进 `pollution`、`unchecked` 进 `cannot_check`、
`unchanged` 不记；`exists` 侧、三段信号、告警固定串「环境受干扰」文案锚点一律未动。

**C. 我如实声明的一个漏判**（写在 `hygiene_snapshot_tristate.py` docstring 里）：
被跟踪文件若**真的被删**，两次都读不到 ⇒ `None↔None` ⇒ `unchecked`，调用方只知「没查成」、
不知「因为它没了」。卡文 §五③ 写「归 `exists` 侧覆盖」——**实测不成立**：
`_HYGIENE_SKELETON_PATHS = ("raw","wiki","outputs","CLAUDE.md")` 与
`_HYGIENE_TRACKED_FILES = (".gitignore","config/subject_mapping.yaml")` 是**两批不相交的路径**。
相对旧实现仍是严格改善（旧实现对同一情形是**静默放过**）。

**D. 判据**：先红（收集期 ImportError）→ 后绿 28/28；负控两段各红在指定断言、sha 跑前跑后
逐字同、且双向验证（退化 rc=1 / 还原 rc=0）；`tests/unit` 目录级 diff 对 64 基线**完全相同**
（`>` 0 条、`<` 0 条）；地盘恰 4 文件；`live_port_guard.py` / `guard_plugin.py` / 根 `conftest.py`
三份 sha 与 HEAD 逐字同；调用形态门 12 个 token 对工具文件全 0，且同一批 token 对
`live_port_guard.py` 有命中（1/27/4/2）作验伪锚。

**E. 我犯过一个过程错误并已登记**：首次目录级跑与负控①**时间窗重叠**，那一跑读到了变异态，
我自己 3 条测试假红。已作废该跑、重跑并落 `voided-run-*.txt` 记根因
（EXIT trap + sha 前后同只证明「还原正确」，**不证明**「期间没有别的进程读到变异态」）。

## 三 请回答的问题（按重要性排序）

① **三条口径更正是否成立？** 请独立复核依据，尤其更正⑤：`blocked` 真的单调吗？两个产出点
真的是两个时刻吗？如果我错了、卡文对，那本工具会在「两值合法不等」时**放过**本该报的冲突——
请指出该情形下的具体后果。反之若我对，请确认 `final >= summary` 这条不变量本身有没有漏面
（例如 `summary_line` 在一次跑里被打印多次、或 `_final_accounting` 的 `blocked` 来自
`finalize_and_snapshot()` 的快照而非实时字段）。

② **`failure_body_identities` 的身份定义是否还有「每跑不同的量」没被剔除？**
逐字段问：`address`（`_safe_repr` 的裸 repr）、`thread`（已归一 portal hex）——
还有别的线程名形态带地址/序号吗？`address` 里会不会出现每跑不同的内容？
正则 `^- (?P<addr>.+?) on thread (?P<thread>\S+) \(owner=` 的非贪婪 + 从左锚，
在 owner 含 ` on thread ` / ` (owner=` 时是否真的不把 owner 切进身份？

③ **`blocked_count` 返回 `None` 与返回 `0` 的区分是否在所有路径上都守住了？**
CLI 把 `None` 判成 rc=2（说不清），把 `0` 当有效观测。存档里有没有一种形态会让
「门根本没装/没记账」被读成 `blocked=0`（= 查了，是零）？（提示：`summary_line` 不含
`installed` 字段；pytest-xdist 每个 worker 有独立 STATE。）

④ **三态路由改动对 `tests/unit` 全 session 的影响面**：`cannot_check` 非空会让整个卫生门
`pytest.fail`。本树两个被跟踪文件可读 ⇒ 改动是 no-op（目录级 diff 完全相同可证）。
但在**别的环境**（权限受限 / 符号链接 / 文件真被删）下，这个改动会把原先静默通过的 session
变成整体失败——这个方向是否可接受？有没有更好的处置？

⑤ **`_SUMMARY_RE` / `_FINAL_RE` 的整行锚是否会漏收真实存档**？本仓存档常把上一轮判据输出
抄进证据文件、也常有 `sed -n` 回显。整行锚是为了拒回显，但会不会把**真产出行**也拒掉
（例如带 `stderr_tail = ` 前缀、或被 `cut` 截断的那类）？方向是假红还是假绿？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路，
用**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**表述。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件，不要跑 hook，不要暂存文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评 `live_port_guard.py` 守卫本体的设计**：它是前两卡的面，本卡只读解析它的输出。
- **不做全称封闭证明**：请把剩余漏面**列举**出来而不是要求本卡穷尽。
