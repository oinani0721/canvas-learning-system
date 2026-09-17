# 独立复核请求 — CARD-G2-7a-TAIL（round-5，**D-15 上限轮 / 本卡最后一轮**）

## 〇 本轮是什么

前四轮 BLOCKER/HIGH 全为 0（r1 绑 `b3baf7d9` M1；r2 绑 `3735b565` M5 L1；
r3 绑 `25feb21d` M5 L2；r4 绑 `2358f9e0` M8 L3）。

你在 r4 指出：**8 条 MEDIUM 里 4 条、3 条 LOW 里 2 条是我 r3 修复新引入的**。
这个判断我接受，并且回看发现更根本的问题 —— 我在 r2 给自己定的门槛是
「只修**本卡新增**的缺陷，或**极小且纯增强**」，而 `io.open("log","w")`（你 r2 的 MEDIUM-2）
是**既有**缺口且**不小**，我 r2 就违反了自己的规则。代价是两轮往返、6 个新缺陷，
还让合法只读代码（`def label(io)`）在这道门上假红。

**所以本轮不是再修一轮，是做减法、撤回超范围的修复。**

| 动作 | 目的 |
|---|---|
| 整段删除 `_module_open_owners` / `_is_module_level_open` 与 owners 接线 | 撤回 r2+r3 对模块级 open 的处理 ⇒ 消掉 r4 M1/M2/M4 与 LOW-9 的三个假红 |
| 敏感名集 `{open,os,io,builtins}` 收回 `{open,os}` | 同上 |
| `AnnAssign` 只跳 **target 节点本身**、不跳整棵子树 | 消掉 r4 M3（对象表达式里的海象仍会执行） |
| FIFO 断言比对前**归一化空白** | 消掉 r4 LOW-10（改缩进 / 多个尾空格就红） |

**保留**（都是本卡新增、必须留）：`os.open` 旗标分支（r1，本卡唯一需要的豁免）、
参数展开拒绝（r2 修 r1 自己的回归）、`os`/`open` 的重绑定拒绝（r2 修 M1）、
FIFO 门的「提及恰好 1 条 + 那一行逐字相同」。

**我也接受你 r4 对我一个事实错误的纠正**：我写过「验伪锚 24 条」，实数是 22。
已实测更正；减法后为 16 条。

**明确登记移交、本卡不修**：模块级 `io.open`/`builtins.open` 误豁免、别名 `_open`、
`getattr(os,"open")`、`functools.partial(os.open,…)()`、`write_names` 名单遗漏
（`os.ftruncate`）、旗标属性被改值（`os.O_RDONLY = os.O_WRONLY|os.O_TRUNC`）——
同属一族、需**零写门的重新设计**；以及 main.js 侧的 M4/M5。

## 一 最小读取面

本轮审 SHA：`dcb8c0458032d5223236cc2e8ce46ba11aea278f`　r4 审 SHA：`2358f9e0b3597471380d2def00c270f854889cc5`
卡起点 PREV：`09567e35bf393c34d1ab185e89e6b9effede7141`

1. `git diff 2358f9e0b3597471380d2def00c270f854889cc5 dcb8c0458032d5223236cc2e8ce46ba11aea278f -- . ':(exclude)_bmad-output'` —— 本轮增量（全是删减）
2. `git diff 09567e35bf393c34d1ab185e89e6b9effede7141 dcb8c0458032d5223236cc2e8ce46ba11aea278f -- . ':(exclude)_bmad-output'` —— 整张卡的代码面
3. `backend/tests/unit/test_vault_install_manifest.py` 的零写门、`_is_readonly_open` 族、FIFO 回归门
4. `scripts/verify_vault_install.py` `:1272-1417`（`_check_hotkeys`；**自 r1 起一行未改**）

## 二 请按重要性排序回答

① **这次减法本身破坏了什么？** 删掉模块级 open 处理、收窄敏感名集、改 AnnAssign 跳法、
   归一化空白 —— 逐处给「新放行了什么 / 新误拒了什么」，并标 r4/r5 判值对照。
② **保留的四件是否仍然成立**：`os.open` 旗标分支、参数展开拒绝、`os`/`open` 重绑定拒绝、
   FIFO 门两条断言。特别是重绑定拒绝收窄到两个名字之后，r2 的 `os.open = partial(...)`
   那条**本卡新增**的缺口是否仍被拦住？
③ **归一化空白**是否把本该拦下的差异也一起抹掉了（例如 detail 内部的多空格有语义时）？
④ 16 条验伪锚里有没有因为删减而变成空判据的？
⑤ `scripts/verify_vault_install.py` 自 r1 起一行未改，请与 diff 对照确认；
   `_check_hotkeys` 的非阻塞打开 / 同 fd 形态判定 / 从同一 fd 读，三件事结论是否仍成立？

## 三 输出格式与边界

`BLOCKER`/`HIGH`/`MEDIUM`/`LOW` + 一句话结论 + `file:line` + 一句话说明「在什么输入下会看到」。
没有的级别写「无」。结尾给 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

边界：**只读**，不跑 hook、不暂存或提交、不连数据库或网络、不改工作树。
相关行为用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」描述。
不评 `_bmad-output/` 的文档写作质量，只在它与代码事实矛盾时指出。
