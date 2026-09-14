# 独立复核请求 — CARD-W4-SENTINEL-REBIND **round-5**（HIGH-1 判据结构性重写后复审）

## 一 背景与最小读取面（只读；请严格限定在下列面内，不要扩读全仓）

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`，分支 `card/t9-w4`。
r1 `86535afb` · r2 `5c696c92` · r3 `9a280b16` · r4 `6adea906`，**本轮审查 SHA `3e10f587`（= 当前 HEAD）**。
本卡起点 `a4dbd156`。

**请只读这几处**：

1. `git --no-pager diff --no-color 9a280b16 3e10f587 -- . ':(exclude)_bmad-output'`（本轮全部代码改动）
2. 需要整体时：`git --no-pager diff --no-color a4dbd156 3e10f587 -- . ':(exclude)_bmad-output'`
3. `backend/tests/support/w4_sentinel_identity.py` **全文**（本轮唯一改逻辑的文件）
4. `backend/tests/unit/test_w4_sentinel_rebind.py` **全文**（38 → 67 例）
5. `backend/tests/support/hygiene_snapshot_tristate.py` 全文（r1 之后未改）
6. `backend/tests/unit/conftest.py` 的 `:78-106` 与 `:315-340`（r1 之后未改）
7. **只读锚（本轮判据的依据，请重点核这三处）**：三个正文产出点及其**自报条数**的抬头 ——
   `live_port_guard.py:1545-1551`（抬头写 `unaccounted=M`，随后遍历 `ledger["unaccounted_records"]`）、
   `live_port_guard.py:1588-1596`（`format_sentinel`，抬头写「本用例期间有 N 次…」+ 两行说明，随后遍历 records）、
   `backend/tests/conftest.py:176-185`（抬头写「N 次拦截无人结账」，随后遍历 `STATE.unaccounted_blocked()`）
8. 本轮判据存档（`_bmad-output/审查/evidence-w4-sentinel-rebind/`）：
   `w4sr-negctl-r5-20260915T002406.txt`（先绿 67 → 退化回 r4 版真红 4（各对应 r4 的一条发现）→ 还原 67，parser sha 逐字同）、
   `unit-close-r5-20260915T002449.txt`、`unit-close-diff-r5-20260915T003033.txt`（含验伪锚）、
   **`codex-r1to4-regression-20260915T002400.txt`（你 r1–r4 全部 19 条对抗输入 + 2 份真实存档一次性重打）**
9. **真实存档端到端**：`real-archive-e2e-20260915T001036.txt` —— 本轮期间目录级跑**真的**触发了一次
   现网 7691 偷连（`unit-close-r4c`，`blocked=1`，C 型块），与同代码同环境的 `unit-close-r4d`
   （`blocked=0`）构成一对**真实**存档；判据在其上正确判 DIFFER。此前只在构造样本上验过。
   归因见 `unit-close-diff-r4-20260915T001049.txt`。
10. **三份作废存档**（均由文件自身指认，未静默删除）：`voided-run-*`、`unit-close-r4-20260914T234911`
   （绑改前 parser sha，我主动 kill）、`unit-close-r4b-20260914T235339`（runner 丢了
   `PYTHONDONTWRITEBYTECODE=1` ⇒ 与基线不可比）。
11. 前三轮存档（对照）：`codex-review-CARD-W4-SENTINEL-REBIND{,-r2,-r3}.md`

## 二 本轮整改自述（请独立核对，不要采信）

**HIGH-1 你说中了要害：我 r3 说的「闭合」只闭合了一半。**
块内确实闭合（恰好 N 行、行行可解析），但**进入块的那一步**我写的是「向前扫到第一条 `- ` 行」——
那仍然是「找找看」。`address="\n- tail"` 让首条记录退化成只剩 `  - `（strip 后是 `-`、
不满足 `startswith("- ")`）被当说明行**跳过**，扫描继续前进落到后半段上并解析成功。
⛔ 我记下的规律：**判据闭不闭合看最弱的那一环，不是最强的那一环。**
**改法**：记录起点是**已知常量**——A/B 型在抬头下一行；C 型在抬头后固定两行说明
（`_FORMAT_SENTINEL_PROSE_LINES = 2`，直接对应 `format_sentinel` 的源码结构）。**不再扫**。

**MEDIUM-2 已改**：你说得对，旧兜底只管「一个块都没有」，于是「一个块正常、另一个块抬头漂了」
时漂掉那块的记录静默消失。新增闭合兜底：**每一行完整匹配 `_BODY_RE` 的记录行都必须被某个块认领**，
否则拒判。因为只认**完整**记录行（须同时有 `- ` 前缀、` on thread `、` (owner=`），
你 r3 MEDIUM-2 的三条假红不会回来（已加四条 parametrize 反向锚）。

**MEDIUM-4 已改**：B 型抬头锚死 `BLOCK_REASON`，且**只依赖到「N 次拦截」为止** ——
判据依赖的文案越短，产出方在其后改字越不会误伤它。

**MEDIUM-3 已改**：A/B 源码锚改为**锚住判据实际依赖的那一段，不多不少**
（A 覆盖到 `unaccounted={unaccounted} reported_status={status}；`；B 覆盖到 `—— {len(unaccounted)} 次拦截`）。

**MEDIUM-5 已改**：那条测试的两档现在都带正常 C 块、只有 A 缺汇总行，才真正打在缺四元组门上。

**LOW-6 已改**（措辞清零）。**LOW-7 已改**：我把旧判据的**误报不同**写成了「会漏」，存档已追加更正。
⚠️ 这是我在本卡第二次「在说明文字里写了个不准的断言」（第一次是 pipestatus 归因）。

**⚠️ 两处我自己的失误也如实说**：`ruff format` 折行让我的替换锚失配；修复脚本把 `\*` 写成 `\\*`，
使 B 型正则去匹配反斜杠 —— **后者是被那条运行期往返锚抓出来的**。没有它，B 型块会静默失明。

**回归**：`codex-r1to4-regression-*.txt` 把你 r1–r4 的**全部 19 条对抗输入 + 2 份真实存档**
一次性重打，全部符合预期。测试 61 → 67。

## 三 请回答的问题（按重要性排序）

① **「记录起点是常量」这个新前提站得住吗？** 请攻它：
   (a) C 型说明行**恒为 2 行**吗？有没有分支让 `format_sentinel` 少打/多打一行？
   (b) A/B 型的记录**真的紧跟抬头下一行**吗？中间有没有可能插进别的输出（两处都是裸 `print`）？
   (c) 抬头行本身若被换行切开（抬头里含用户可控内容吗？），偏移会指到哪里？

② **孤儿兜底有没有造出新的假红？** 它对**任何**完整匹配 `_BODY_RE` 却不在块内的行都拒判。
   真实存档里有没有合法出现这种行的场合（例如文档引用、日志回显整条记录、
   同一条记录被 pytest 在别处再打印一次）？

③ **本轮是否有回归**：请特别核 r1–r4 那 19 条输入我是否真的都还红/绿在该红/该绿的位置，
   以及 `blocked_count` / `summary_quad` / 解码拒判 / 三态与 conftest 路由。

④ **这是本卡的第 5 轮，也是轮次上限。** 若仍有 HIGH，我按 D-15 停车交主 session 人审。
   所以请明确区分：哪些是**必须本卡收掉**的，哪些你认为**登记移交即可**。

⑤ 还有没有新的门未覆盖的路径？不要求穷尽。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` + 一句话复现思路，
用**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**表述。
请在开头**明确给出本轮的 BLOCKER 数与 HIGH 数**。经核对成立的项请明说「核对通过」并给出位置。

## 五 边界

- **只读**：不要修改仓库里的任何文件，不要跑 hook，不要暂存文件。
- **不连库**：不要尝试连接 7691 / 7687 / 7692。
- **不评 `live_port_guard.py` 守卫本体的设计**（但**可以且应该**核对我对它结构的引用是否属实）。
- **不做全称封闭证明**。
