# 独立复核请求 — CARD-W4-SENTINEL-REBIND **round-4**（HIGH-1 判据结构性重写后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`，分支 `card/t9-w4`。
r1 审 `86535afb`，r2 审 `5c696c92`，r3 审 `9a280b16`，**本轮审查 SHA `6adea906`（= 当前 HEAD）**。
本卡起点 `a4dbd156`。

**请只读这几处**：

1. `git --no-pager diff --no-color 9a280b16 6adea906 -- . ':(exclude)_bmad-output'`（本轮全部代码改动）
2. 需要整体时：`git --no-pager diff --no-color a4dbd156 6adea906 -- . ':(exclude)_bmad-output'`
3. `backend/tests/support/w4_sentinel_identity.py` **全文**（本轮唯一改逻辑的文件）
4. `backend/tests/unit/test_w4_sentinel_rebind.py` **全文**（38 → 61 例）
5. `backend/tests/support/hygiene_snapshot_tristate.py` 全文（r1 之后未改）
6. `backend/tests/unit/conftest.py` 的 `:78-106` 与 `:315-340`（r1 之后未改）
7. **只读锚（本轮判据的依据，请重点核这三处）**：三个正文产出点及其**自报条数**的抬头 ——
   `live_port_guard.py:1545-1551`（抬头写 `unaccounted=M`，随后遍历 `ledger["unaccounted_records"]`）、
   `live_port_guard.py:1588-1596`（`format_sentinel`，抬头写「本用例期间有 N 次…」+ 两行说明，随后遍历 records）、
   `backend/tests/conftest.py:176-185`（抬头写「N 次拦截无人结账」，随后遍历 `STATE.unaccounted_blocked()`）
8. 本轮判据存档（`_bmad-output/审查/evidence-w4-sentinel-rebind/`）：
   `w4sr-negctl-r4-*.txt`（先绿 61 → 退化回 r3 版真红 16 → 还原 61，parser sha 逐字同）、
   `unit-close-r4-*.txt`、`unit-close-diff-r4-*.txt`
9. **真实存档端到端**：`real-archive-e2e-20260915T001036.txt` —— 本轮期间目录级跑**真的**触发了一次
   现网 7691 偷连（`unit-close-r4c`，`blocked=1`，C 型块），与同代码同环境的 `unit-close-r4d`
   （`blocked=0`）构成一对**真实**存档；判据在其上正确判 DIFFER。此前只在构造样本上验过。
   归因见 `unit-close-diff-r4-20260915T001049.txt`。
10. **三份作废存档**（均由文件自身指认，未静默删除）：`voided-run-*`、`unit-close-r4-20260914T234911`
   （绑改前 parser sha，我主动 kill）、`unit-close-r4b-20260914T235339`（runner 丢了
   `PYTHONDONTWRITEBYTECODE=1` ⇒ 与基线不可比）。
11. 前三轮存档（对照）：`codex-review-CARD-W4-SENTINEL-REBIND{,-r2,-r3}.md`

## 二 本轮整改自述（请独立核对，不要采信）

**HIGH-1 我没有再打第四个补丁，而是把判据换成了闭合结构。** 你的四类输入我全部复现属实
（`worker\n- continued` / 空线程名 / `ADDR-A\n- tail` / owner 前截断，`\r` 同理），
并且你指出的「r2 把覆盖 ④ 的测试换成了恰好止于 `on thread` 的输入」也属实。

三轮的共同根因我认下：**开放式地判断「这行坏没坏」永远补不完**
（r1 `\S+` → r2「像不像记录」→ r3「截断+孤儿痕迹」，每次都是换个输入又活过来）。

新判据的依据是**守卫本体的结构**（上面读取面 7）：三个产出点都在遍历记录之前**自报本块条数**。于是：

- **只读被抬头自报过条数的块**；块内从第一条 `- ` 行起**连取 N 行**，这 N 行必须**逐行**匹配 `_BODY_RE`；
- 少一行（存档截断）、多一行（自报与实际不符）、任一行解析不出 —— 一律 `W4LedgerConflict` / CLI rc=2；
- **块外的行根本不看** ⇒ 你 MEDIUM-2 的三条假红（`cache refreshed (owner=worker)`、源码回显、
  `- waiting on thread`）一并消失；
- 兜底：`blocked > 0 却一个自报条数的块都没有` ⇒ 拒判（身份集为空不代表没有记录）。

**代价我写在函数 docstring 里**：抬头文案若被改动，本函数会**看不见**那个块 ——
方向是「记录消失」而非「记录错认」，由上面那条兜底接住；**但 `blocked = 0` 时没有任何东西接住**。

**⛔ 改完之后我逐条攻了自己刚立的这三个前提，又抓出两处（我找的，不是你指出的）：**

- **`declared == 0` 的块会假红**。抬头 A 的触发条件是 `unaccounted > 0 **or** (blocked > 0 and status == 0)`，
  第二个分支会打出 `unaccounted=0` 的抬头、后面零条记录。我的解析器当时对 `declared == 0` 仍会
  「向前扫到第一条 `- ` 行」，会扫到**别处**的记录行然后判「自报条数与实际不符」。已短路。
- **C 型抬头一宽一严**。我原写成 `^.*? —— 本用例期间有…`（容忍任意前缀），记录行却要求 `^- `。
  已收紧为与 `_FINAL_RE` 同口径、锚死 `BLOCK_REASON` 字面量。

**并补上了那个代价的唯一防线**：新增 `TestJudgeIsBoundToTheRealProducers`（6 例）——
直接调 `live_port_guard.format_sentinel` 造**真输出**再让判据解析、按产出方写法复原 A/B 型抬头的
运行期整行、`declared=0` 不假红、以及 `BLOCK_REASON` 与两处抬头文案的源码锚。
（写这条锚时发现抬头 B 在源码里是**跨两个相邻字面量**拼的，源码里没有连续的那句话，
故源码锚只能分段核、另建运行期往返锚。）

**MEDIUM-3 已改**：`errors="replace"` → `errors="strict"`，解码失败即拒判。你那两份
`work\x80er` / `work\x81er` 现在 rc=2。

**LOW-6 已改**：`test:171`、`:193`、parser `:265` 三处 advisory 措辞全清。

**⛔ LOW-7 你是对的，我已本机复验**：`zsh -f -c 'false | true | true; print -r -- $pipestatus[1]'` ⇒ `1`，
下标 1 就是第一段。我那条更正块把原因写错了，真实原因**未知**。存档已追加第二条更正，
我的持久工程坑笔记也同步改了。**更正块不是免检区**这条教训我记下了。

**⛔ 你指出我在审查期间改了你在读的目录（86 → 108 行），属实**。那是追加更正、未改结论，
但仍违反「审查对象在审查期间冻结」。本轮所有中间产物都先落 scratchpad，审完才进 evidence。

**未改（维持登记移交）**：r2 MEDIUM-5（裸 repr、`worker (owner=A)` 切错边界）、
r2 MEDIUM-6 + 你 r3 新发现的同族一条（缺右括号的汇总行被 `if m` 滤掉）、
你 r3 另列的两条门未覆盖路径（全文去 ANSI 抹掉字段自身的 ANSI；`(owner=` 前缀即接受身份）。

## 三 请回答的问题（按重要性排序）

① **闭合判据本身是否成立？** 请攻击它的三个前提：
   (a)「三个产出点都自报条数」—— 有没有第四个产出点，或某个产出点在某条路径上**不打抬头**？
   (b)「块内 N 行连续」—— 有什么真实输出会插进记录之间（xdist 前缀、日志交错、pytest 换页）？
   (c)「抬头 A 的条数 = `unaccounted`」—— 我是读 `:1545-1551` 推断的，**没在真实存档上见过 A 型块**。

② **新判据有没有造出新的假绿**？特别是：抬头文案漂移且 `blocked = 0` 时无人接住；
   多个块相邻时的边界；`declared = 0` 的块；同一条记录被两个产出点各印一次时的集合去重。

③ **有没有造出新的假红**？我最担心的是 (b)：真实长跑里若有东西插进记录之间，
   本判据会判「自报条数与实际不符」而拒判 —— 这会让本卡自己的目录级判据在某天突然变红。

④ **本轮是否有回归**：`blocked_count` 的 `final >= summary`、`summary_quad` 算术自洽门、
   重复汇总/总账抛冲突、缺四元组拒判、`normalise_thread` 的 portal 归一、三态函数与 conftest 路由。

⑤ 还有没有**新的**门未覆盖的路径？不要求本卡穷尽。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路，
用**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**表述。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件，不要跑 hook，不要暂存文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评 `live_port_guard.py` 守卫本体的设计**（但**可以且应该**核对我对它结构的引用是否属实）。
- **不做全称封闭证明**。
