# 独立复核请求 — CARD-AILINKED-4TH-WRITER（ai-linked-doc 第四写者对齐账本写规）

## 一 背景与最小读取面（只读这些，不必扫全仓）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
分支 `card/t7-skills`，本卡审查绑定 `HEAD = 41629ec3`，前一卡 tip `PREQ = d5ad6fca`。

本卡要修的缺陷：学习事件账本 `learning_events.jsonl` 有**四个**真实写者（backend 的
`append_event`、quiz-answer SKILL、start-exam-board SKILL、ai-linked-doc SKILL）。前三方已按同一套
写规硬化，第四方 ai-linked-doc 长期是一行式 `python3 -c` 裸追加，四缺陷：① 子串查重
② 无跨进程锁 ③ 无 LF 守卫 ④ 无 event_id 形态门。

请读：

1. `git diff d5ad6fca 41629ec3 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，5 文件）
2. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 的 **Step 5.5** 小节（改后的写点 PYEOF 块，约 :214-345）
3. `backend/app/services/learning_event_log.py` 的 `:14` / `:57` 附近（本卡只改这两处注释）
   与 `:188-343`（backend 侧四写规的参照实现，**只读不改**）
4. `backend/tests/skills/test_ai_linked_doc_writer.py` 全文（本卡新增的四门）
5. `backend/tests/regression/test_learning_events_schema_contract.py` 的
   `test_real_producer_ai_linked_doc_writer`（producer 门，本卡改了它的提取段）
6. 同口径对照：`canvas-vault/.claude/skills/quiz-answer/SKILL.md:260-320` 与 `:650-710`、
   `canvas-vault/.claude/skills/start-exam-board/SKILL.md:437-490`

## 二 作者自述（请独立核对，不要采信）

1. **parsed-field 相等查重**与 backend `:320`（`record.get("event_id") == event_id`）/ quiz-answer
   `:660` 注释口径逐字同语义；无法解析的行不算命中（坏行不构成 duplicate 证据，跳过）。
2. **`fcntl.lockf` 罩住「查重 → LF 守卫 → 写 → close」整段**，且锁内**只用同一个 fd** 读
   （`os.lseek` + `os.read` 循环），没有第二个 `open`/`read_text`/`read_bytes`。
3. **LF 守卫在锁内**（两个写者各补一次 LF 会造空行，空行在校验器侧判整本不合规）。
4. **形态门的禁止码点集**与校验器 `backend/scripts/validate_learning_events.py:426`
   `FORBIDDEN_CODEPOINT_RANGES` **同集**（C0 / DEL / C1 / LS-PS / 代理区 / noncharacters /
   17 个平面的 xFFFE-xFFFF），长度上限 512，首尾空白**拒写不 strip**。
5. **五段负控各红在指定断言**，第 ⑤ 段（锁内同 fd 读换成二次 `open`）只红「恰 1 行」那条，
   而「size-at-release==0」「elapsed>=HOLD_S*0.6」两条仍绿。
6. **门⑪ 普查集合仍是 4 份**（`grep -rn learning_events.jsonl backend/app canvas-vault/.claude`）。
7. **producer 门提取段已改 PYEOF 形态**，仍逐字提取、恰取 1 块，且该函数体之外一行未动
   （`:1007` 起的 start-exam-board / quiz-answer 两个 producer 门未被触碰）。
8. `backend/app/services/learning_event_log.py` **仅改 docstring/注释**：去 docstring 后
   `ast.dump` 与 `PREQ` 版相同；`pyright app`（cwd=`backend/`）= `0 errors, 81 warnings`。

### 两处与卡文原口径不同，请重点判断是否站得住

- **(A) 写点位置**：卡文说「改 `SKILL.md:189` 的写点」。实测 `:189` 位于 `:128-191` 这个
  **无语言标注的 fenced 块内部**，而该块是 Step 3 给 LLM 生成器的 System Prompt 模板。
  markdown 的 ``` fence 不能嵌 ``` fence，原位改成 ```bash 块会让第一个 ``` 被当成外层块的
  闭合。故把写点**移出**该模板块，落为 **Step 5.5** 独立 ```bash 块（Step 5 正是「写新节点
  文件」，原 bullet 自己写的就是「新节点写入成功后」）。请判断：这个移动是否改变了 Skill 的
  执行语义？有没有更小的改法？留在 prompt 模板里的其余 bullet 是否因此缺了什么？
- **(B) 门② 两档账本**：卡文规定门② 的账本「预置为空文件」。第一轮负控实测**推翻**了只用
  空账本的形态——改后的写点把 import 全提到开头、并用 `os.read` 一次性读，「读 → 写」窗口从
  改前的约 1ms（首次 `from datetime import`）缩到几十微秒，于是：去掉 `fcntl.lockf` 只红 2/3
  （`n=1`），锁内换成二次 `open` **全绿**（本该红「恰 1 行」的那一段什么都没证到）。
  故门② 改为两档：档 A 空账本 + 外部 holder（服务先红的三条），档 B 20000 行账本 + 无 holder
  （解析约 36ms > 写点取锁轮询间隔 20ms，锁一失效后到的写者必然读到旧快照）。① 取两档较劣者。
  请判断：档 B 的时序论证是否成立？20000 行 / 36ms 对 20ms 的富余是否够？有没有更可靠、
  不依赖时间常数的形态？

## 三 请按重要性排序回答的问题

⓪ **parsed-field 相等**是否真的覆盖了「历史行中**非 event_id** 字段的值恰好等于新 evid」
   这条**此前未被拦下的输入**（原子串写法在这条输入上把新事件误判 duplicate、零次落账）？
   写点里有没有哪条路径会让 `json.loads` 的异常逸出、导致整个写点提前退出？

① **fd 生命周期**：锁内是否全程同一个 fd？`os.close(fd)` 是否在锁内（`finally`）？
   有没有任何一处隐式打开该文件的操作（含异常分支、日志、`print`）会让 POSIX 记录锁
   按「进程 × 文件」被整体释放？（backend `:276-281` 踩过这个坑；本卡门② 的「恰 1 行」
   断言就是冲这条来的——而「等到锁 / 没抢写」两条判据看不见这次隐式释放。）

② **LF 守卫**：两个写者各补一次 LF 是否会造空行（对照 `test_g3_3_cas.py:338` 的
   `"\n\n" not in raw`）？守卫放在锁内是否足够？`raw` 为空（首次写）时不补 LF 是否正确？
   门② 用「holder 持锁期同 evid 双写」而非「不同 evid 双写」是否站得住（`O_APPEND` 对
   不同内容的并发追加本就两条都落盘，后者在改前恒绿）？

③ **形态门**：首尾空白是否**拒写**而不是 strip？码点集是否比校验器 `:426` 窄
   （窄了就留下「写得进、读不回」的路径）？门④ 的三类反例（尾随空白 / U+2028 / 超长）
   在 `derive:` 前缀下是否**都真的可达**？（「空 evid」「前导空格」已实测不可达、已从门里去掉。）
   形态门放在取锁**之前**是否有问题？

④ **外形与提取**：写点改为 PYEOF 块后 `learning_events.jsonl` 字面量是否仍在（门⑪ 集合不漂）？
   块正文是否无行首 `PYEOF`？两处 `<>` 占位是否逐字保留？producer 门是否只动了 ai-linked-doc
   那一个函数？新测试的 `_extract_writer` 兼容新旧两种外形——这是为了让「改 SKILL.md 之前
   先跑一遍看它红」可行（那一刻写点还是单行形态）。这个兼容是否削弱了任何主张？
   （作者的说法是：钉外形是 producer 门 `assert len(matches) == 1` 的职责，四门钉的是写规行为。）

⑤ **backend docstring 改动**是否误触逻辑？pyright 是否仍 0？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句定位思路。
没有问题的分级请明确写「无」。

## 五 边界

- **只读**，不要修改任何文件；不连任何数据库（7691 / 7687 一律不碰）。
- 不评 `canvas-vault/.claude/skills/start-exam-board/SKILL.md:477` 那条同类子串残留的处置
  （已登记移交，非本卡面）。
- 不评「完整 vault 里真实跑一次 ai-linked-doc skill」——本卡只逐字提取写点模板用 subprocess 跑。
