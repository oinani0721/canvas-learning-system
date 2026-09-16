# 独立复核请求 — CARD-G2-7a-TAIL（round-4，**最后一轮整改**）

## 〇 判定口径与本轮重点

D-15：绑最终 HEAD 的一轮 BLOCKER/HIGH = 0。前三轮都已达到：
- r1 绑 `b3baf7d9`：`B0 H0 M1 L0`
- r2 绑 `3735b565`：`B0 H0 M5 L1`
- r3 绑 `25feb21d`：`B0 H0 M5 L2`

**本轮最需要你看的是一个模式**：我前两轮的修复**各自引入了新缺陷**，而且都是你抓出来的 ——

| 我的修复 | 它引入的新缺陷 | 你给的判值对照 |
|---|---|---|
| r1 修 MEDIUM（`os.open` 分支） | r2 MEDIUM-1（展开形态被误放行） | PREV/r1 = False/True |
| r2 修 MEDIUM-2（名字白名单 `io`/`builtins`） | r3 MEDIUM-2（`io = Path(...)` 的变量被当模块 ⇒ 写模式放行） | r2/r3 = 拒绝/通过 |
| r2 新增重绑定拒绝 | r3 LOW-2（无值类型注解被误判 ⇒ 假红） | r2/r3 = 通过/拒绝 |

所以**第一优先级不是找老毛病，而是：这一轮（r3→r4）的修复本身又带进了什么？**
请对本轮每一处改动都问一遍「它新放行了什么 / 新误拒了什么」，并给出与前一轮的判值对照。

**不要用「既有 / 上一轮已过 / 已登记」豁免任何问题**。地盘文件：

```
scripts/verify_vault_install.py
backend/tests/unit/test_vault_install_manifest.py
```

## 一 最小读取面

本轮审 SHA：`2358f9e0b3597471380d2def00c270f854889cc5`
r3 审 SHA：`25feb21d699ea8dae1e30975f74534d1ec69fa55`
卡起点 PREV：`09567e35bf393c34d1ab185e89e6b9effede7141`

1. `git diff 25feb21d699ea8dae1e30975f74534d1ec69fa55 2358f9e0b3597471380d2def00c270f854889cc5 -- . ':(exclude)_bmad-output'`
   —— **本轮增量**（只有 `test_vault_install_manifest.py`，+107 / −38）。
2. `git diff 09567e35bf393c34d1ab185e89e6b9effede7141 2358f9e0b3597471380d2def00c270f854889cc5 -- . ':(exclude)_bmad-output'`
   —— 整张卡的代码面（两个文件）。
3. `backend/tests/unit/test_vault_install_manifest.py`
   - `:643-825` — 零写门（含重绑定拒绝段 + 24 条验伪锚）
   - `:836-861` — `_module_open_owners()`（**本轮新增**）
   - `:864-879` — `_is_module_level_open()`（**本轮改签名**）
   - `:882-911` — `_is_os_open()` / `_os_open_flag_names()`
   - `:914-967` — `_is_readonly_open()`（**本轮改签名**）
   - `:3313-3419` — `_report_section()` 与 FIFO 回归门（**本轮改了断言方式**）
4. `scripts/verify_vault_install.py` `:1272-1417`（`_check_hotkeys`；**自 r1 起一行未改**）

## 二 本轮四处修法（请逐处找它新引入了什么）

1. **M2 双向**：`_is_module_level_open` 的 owner 集不再是字面白名单，改由
   `_module_open_owners(tree)` 从**被分析源码自己的 `import`** 推出；该名字若在本文件里被
   Store 过就从集合剔除。缺省参数是**空集**（= 谁都不算模块调用）。
   生产脚本实测 `owners = 空集`（它没有 import io/builtins）。
2. **M1**：重绑定判据从「Assign 的 `targets`」改成按 **`ast.Store` 上下文**遍历，
   另补函数形参与 `import` 别名两类绑定面。敏感名集 = `{open, os, io, builtins}`；
   Attribute 侧仍按 `attr in write_names`。
3. **LOW-2**：排除 `AnnAssign` 且 `value is None`（实现方式：先收集这些 `target` 子树的
   `id()`，遍历时跳过）。
4. **LOW-1**：放弃从渲染文本切回结构化身份。改成
   ①「`## unreadable` 段里**提到** `HOTKEYS_REL` 的行必须**恰好 1 条**」
   ②「那一行必须与生产渲染**逐字相同**」。

**我接受并已登记为移交、本轮不修的**：M3（别名 / `getattr` / `partial` / `write_names`
名单遗漏）、M4（非普通 `main.js` 只记 note 不计退出码）、M5（`main.js` 形态检查与读取之间
的并发替换窗口）。这三条都是三版皆有的既有面，且 M3 属零写门的重新设计。

## 三 请按重要性排序回答的问题

① **本轮新引入了什么？** 逐处给「未被拦下的输入」或「被误拒的合法输入」，并标出
   r3/r4 的判值对照。特别看：
   - `_module_open_owners` 的「被 Store 过就剔除」——会不会把**合法的** `import io` 误剔除
     （例如 `for io in ...` 这种同名遮蔽，或函数内部的同名局部）？剔除之后 `io.open("log","w")`
     会走哪条分支、判成什么？
   - `id()` 去重收集 `AnnAssign` 子树 —— 有没有**对象生命周期 / id 复用**导致误跳过的可能？
     有没有哪种无值注解的 `target` 形态（`Subscript`、`Tuple`）会漏掉或多跳？
   - 敏感名集只有四个名字 —— `Path`、`pathlib`、`functools` 被重绑定会不会同样改变判定前提？
② **LOW-1 的「整行逐字相同」是否引入了新的脆弱面**？除了 detail 文案与 `role="-"` 这两处
   我已声明的耦合之外，还有什么会让它在**生产行为正确**时变红（假红）？
③ **24 条验伪锚**里有没有新出现的空判据？本轮新加的五条（真模块 io 写/只读、`_io` 别名写、
   变量 io 的写/只读）分别能抓住哪一种错误实现？
④ 零写门整体：加了重绑定拒绝与 owner 集之后，`offenders == []` 与 `rebinds == []` 两条结论
   各自证明什么、不证明什么？有没有出现「两条互相假设对方成立」的循环？
⑤ `scripts/verify_vault_install.py` 自 r1 起一行未改，请与 diff 对照确认；
   `_check_hotkeys` 的非阻塞打开 / 同 fd 形态判定 / 从同一 fd 读，三件事的结论是否仍成立？

## 四 输出格式

`BLOCKER` / `HIGH` / `MEDIUM` / `LOW` + 一句话结论 + `file:line` +
一句话说明「在什么输入下会看到这个问题」。没有的级别写「无」。
结尾给一行 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**：不要运行 hook、不要暂存或提交文件、不要连数据库或网络、不要改动工作树。
- 相关行为请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法描述。
- 不需要评审 `_bmad-output/` 下的文档写作质量，只在它与代码事实矛盾时指出。
