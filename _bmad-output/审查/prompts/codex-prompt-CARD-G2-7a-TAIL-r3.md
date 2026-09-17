# 独立复核请求 — CARD-G2-7a-TAIL（round-3）

## 〇 判定口径

用户裁定 D-15：有代码改动的卡多轮审查，直到**绑最终 HEAD 的一轮** BLOCKER/HIGH = 0。
- round-1（绑 `b3baf7d9`）：`B=0 H=0 M=1 L=0` —— 那条 MEDIUM 已修。
- round-2（绑 `3735b565`）：`B=0 H=0 M=5 L=1` —— 其中 3 条已修、3 条登记移交（逐条见 §二）。
- 因为 round-2 之后又改了代码，按 D-15 必须重送本轮重绑。

**不要用「既有 / 上一轮已过 / 已登记」豁免任何问题** —— 落在下面两个地盘文件内就照报：

```
scripts/verify_vault_install.py
backend/tests/unit/test_vault_install_manifest.py
```

## 一 背景 + 最小读取面（请只读下面这些）

本轮审 SHA：`25feb21d699ea8dae1e30975f74534d1ec69fa55`
round-2 审 SHA：`3735b565b2ada7606aa1294c2d82e0520d7b3a64`
前一卡末 commit（PREV，卡起点）：`09567e35bf393c34d1ab185e89e6b9effede7141`

1. `git diff 3735b565b2ada7606aa1294c2d82e0520d7b3a64 25feb21d699ea8dae1e30975f74534d1ec69fa55 -- . ':(exclude)_bmad-output'`
   —— **本轮增量**（只有 `test_vault_install_manifest.py`，+70 / −7）。
2. `git diff 09567e35bf393c34d1ab185e89e6b9effede7141 25feb21d699ea8dae1e30975f74534d1ec69fa55 -- . ':(exclude)_bmad-output'`
   —— 整张卡的代码改动面（两个文件）。
3. `backend/tests/unit/test_vault_install_manifest.py`
   - `:643-791` — 零写门 `test_verifier_write_calls_are_confined_to_write_report`
     （含重绑定拒绝段 + 19 条验伪锚）
   - `:799-905` — `_OS_OPEN_READONLY_FLAGS` / `_is_module_level_open()` / `_is_os_open()` /
     `_os_open_flag_names()` / `_is_readonly_open()`
   - `:3251-3350` — `_report_section()` 与 FIFO 回归门（本轮改了断言绑定方式）
4. `scripts/verify_vault_install.py` `:1272-1417`（`_check_hotkeys`；**自 round-1 起一行未改**，供对照）

## 二 对 round-2 六条的逐条处置

| 条目 | 定性（我的判断） | 处置 |
|---|---|---|
| **M1** `os.open` 被重绑定后仍按位置判 | **本卡新增**（你给的 PREV/r1/r2 = False/True/True，我实跑复现） | **修** |
| **M2** 所有 Attribute 调用当绑定方法 ⇒ `io.open("log","w")` 判只读 | 三版均存在（既有） | **修**（4 行、纯增强） |
| **M3** 名字筛选漏别名 / `getattr` / `partial` / 名单遗漏 | 三版均存在（既有，属该门的重新设计） | **登记移交 + 改 docstring 过强措辞** |
| **M4** 非普通 `main.js` 只记 note 不计退出码 | 既有 UAT-G2-7a MEDIUM-3；卡文明令本卡不扩面 | **登记移交** |
| **M5** `main.js` 形态检查与读取之间的并发替换窗口 | 既有（你自己也写了「不是本卡新引入」） | **登记移交** |
| **LOW-1** FIFO 门路径断言与理由断言可由两条不同的行分别满足 | **本卡新增**（我自己写的门） | **修** |

**修法**：

1. **LOW-1**：改为先按**路径相等**（不是 `startswith`）从 `## unreadable` 段筛出 hotkeys 那一行、
   断言**恰好一条**，再要求**那一条**含形态理由。你给的对照报告实测已判红。
2. **M1**：新增「写 API 重绑定即拒」——`<owner>.<写名> = ...` 或遮蔽内置 `open` 时，
   按位置判 mode/flags 的前提失效，本门直接报违规而不是继续按一个不成立的前提去判。
   ⚠️ 只拦这两类、不一刀切：一刀切会误伤同名局部变量（生产脚本 `:899` 的 `link = cur / rel`）。
3. **M2**：新增 `_is_module_level_open()`，`io.open` / `builtins.open` 不再当绑定方法，模式按 `args[1]` 取。
4. **M3**：docstring 里「`os.*` 全族」这句**过强措辞**已改成如实表述，并逐条列出四类未覆盖输入
   （别名 / `getattr` / `partial` / 名单遗漏）。门本身的覆盖面**没有**扩大。

**我接受你 round-2 §② 的更正并已照录**：真实 `os.open` 里 `**kw` 不能覆盖已绑定的 `flags`
（重复传参会 `TypeError`），所以 `os.open(p, os.O_RDONLY, **kw)` 这条锚应理解为**保守拒绝**，
不能解释成「成功覆盖写旗标的实例」。

**验伪锚 16 → 19 条**；另落一份 20 例判定矩阵（正例 5 / 反例 15，0 例不符）。

## 三 请按重要性排序回答的问题

① **LOW-1 的修法是否真的把两条断言绑到了同一条 finding**？路径相等匹配用的是
   `row.strip().split("  —", 1)[0].strip() == vv.HOTKEYS_REL` —— 这个切法在
   detail 为空、detail 自身含 `"  —"`、或 role 字段非 `-`（渲染成 `path [role]  — detail`）
   时是否会切错？请给未被拦下的输入。

② **重绑定拒绝是否有假红 / 假绿**？假红：生产脚本里哪些合法写法会被它误判（我实测当前 0 命中，
   但 `for` 目标、`with ... as`、解包赋值、`global` 声明这些形态我没纳入判据）。
   假绿：除了 `<owner>.<写名> = ...` 与遮蔽 `open` 之外，还有哪些赋值形态能改变调用解析？

③ **`_is_module_level_open` 的白名单（`io` / `builtins`）是否够**？
   `from io import open` 之后的裸 `open(...)`、`import io as _io` 之后的 `_io.open(...)`
   分别会走哪条分支、判成什么？

④ 19 条验伪锚里有没有**新出现的空判据**（在任何实现下都通过）？特别是本轮新加的三条
   （`io.open` 写 / `builtins.open` 写 / `io.open` 只读）。

⑤ 本轮增量有没有影响 `_check_hotkeys` 与 FIFO 回归门的既有结论？
   `verify_vault_install.py` 自 round-1 起一行未改，请与 diff 对照确认。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：一句话结论 + `file:line` +
一句话说明「在什么输入下会看到这个问题」。没有问题的级别请明确写「无」。
结尾给一行 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**：不要运行 hook、不要暂存或提交文件、不要连任何数据库或网络服务、不要改动工作树。
- 相关行为请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法来描述。
- 不需要评审 `_bmad-output/` 下的文档写作质量，只在它与代码事实矛盾时指出。
