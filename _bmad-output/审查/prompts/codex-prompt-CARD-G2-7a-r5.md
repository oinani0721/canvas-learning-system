# CARD-G2-7a 独立复核请求（round-5）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **7cb2d93e**。

前三轮：r1 绑 `7aa89c5b`（0B/2H/4M/2L）、r2 绑 `3c1e3c00`（0B/1H/3M/3L）、
r3 绑 `725bbd19`（**0B/0H**/3M/5L）。**r3 已满足 D-15 的停止条件**，本轮是自愿加固：
r3 的 LOW-1/2/3 指出我三条门「给出虚假保证」（你自己跑的变异全部存活），这比没有门更糟。

**请只读以下五处（不要读别的、不要读 live vault、不要执行安装脚本）：**

1. r4 之后的整改：`git diff 5a0257fc 7cb2d93e -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff 086771d3 7cb2d93e -- . ':(exclude)_bmad-output'`
3. 脚本与清单全文：`scripts/install-vault.sh`、`scripts/vault-install-manifest.json`
4. 校验器全文：`scripts/verify_vault_install.py`
5. 门文件：`backend/tests/unit/test_vault_install_manifest.py`

## 二 round-4 逐条处置

| 你给的级别 | 处置 |
|---|---|
| MEDIUM-1 hotkeys 两层同时放行 | hotkeys 的读/JSON/顶层类型自校验**提到 main.js 分支之前**；补门（main.js 缺席时顶层非对象仍须 rc=2） |
| LOW-1 `path.open("wb+")` 未被零写门拦下 | 我 round-3 引入的回归。按调用形态取模式位置：绑定方法 `args[0]`、内置 `args[1]` |
| LOW-2 `/bin/cp -R` 未被结构门拦下；`.claude` 复制点无行为门 | 按 **basename** 认命令；补 `.claude` 复制点的写穿行为门 |
| LOW-3 rm 行内注释里的路径被当操作数 | 先剥行内注释再取操作数（续行判断也用剥后文本） |
| LOW-4 数组重复定义被 dict 吞掉；数组 origin 写成区间也通过 | 逐个断言唯一定义；数组声明的 origin 不得是区间 |
| LOW-5 `_sh_line` 优先/回退两头都错 | 锚**分型**：`kind="code"` 只在剥注释后的代码里找，`kind="comment"` 只在注释行里找，取消回退 |
| LOW-6 探测说明比证据宽 | 写明：不证明整件可读、不排除祖先目录软链、空文件属合法形态 |

我用**你给出的 6 个变异体**回打新门：**6/6 KILLED**，各绑自己声称的断言。
顺带修一个夹具形态问题：`_build_vault` 把 hotkeys.json 写成 `content of …`（非法 JSON），
它一直没被发现正是因为 MEDIUM-1 那个提前 return，生产修好后夹具立刻暴露。

另：收工红基线出现「新引入 1 + 修复 1」，逐步定责后确认是 **W4 哨兵归属漂移**
（MemoryService 惰性初始化只连一次 7691，记在当时在跑的用例名下；本卡新增 32 条门改变时序）。
哨兵事件总数 12==12、总红 173==173，两条差异都是哨兵归属条目。

## 三 请按重要性排序回答的问题

1. **`follow_root` 会不会造成新的假绿**：源侧根链被解引用后，「源是链、目标是实体」这个
   事实就不出现在任何报告里了。这与 `-H` 的语义一致，但**校验器的主张**是否因此变宽？
   若源链指向 vault 之外、或指向另一个 vault 的目录，现在会发生什么？
2. **`_probe_regular_readable` 只读 1 字节**：对「前 1 字节可读、后续读失败」的文件（截断的
   网络文件系统、坏块）它会放行。这个收窄是否可接受，还是应当声明得更窄？
3. **origin 归属门的 `owner()` 分类**：`.claude/<两段以上>`、`.obsidian/plugins/<两段以上>`
   这些我返回 `None`（不由数组声明）。分类有没有漏掉真实存在的类别，从而让某些 item
   完全不受该门约束？验伪锚 `checked == 30` 够不够？
4. **还有哪些门在给虚假保证**：请像 r3 那样直接给变异体。我特别怀疑树自洽门
   （只断言 rc 与 optional-missing 集合）与 hotkeys 那两层。
5. `_sh_line` 的「优先可执行行、否则回退全部命中」是否引入了新的歧义面？
6. 现在还有哪些声明比证据宽？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：一句问题 + `file:line` + 一句复现思路。
无问题的项明说「核对结果：无问题」并说明核对程度。

## 五 边界

只读审查；不执行安装脚本；不连数据库；不评 U3-C/U5-B 的消费方。
不需要攻击性内容；关心**误伤与漏报**。
