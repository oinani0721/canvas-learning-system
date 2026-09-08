# CARD-RV-G2-6 独立复核请求（round-3）

## 一 背景与最小读取面

仓库 worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`__HEAD3__`**，基线 `da690bf8`。
前两轮送审态：round-1 `523c10f0`（0B/2H/5M/5L）、round-2 `6bdb0fab`（0B/1H/4M/5L）。

round-2 你给的那条 HIGH 是「整改遗漏」：round-2 的修法只覆盖了**已经进入遍历**的失败，
没覆盖**连遍历都没开始**的失败（`Path.exists()` 把「不存在」和「问不出来」返回成同一个值）。
作者据此又改了一轮（见 §二）。**这一轮的重点仍是：这些整改本身有没有引入新缺陷，
以及同一缺陷类别还有没有没盖到的入口。**

**请只读以下五处，不要读别的文件、不要读任何 live vault 路径下的内容：**

1. round-2 之后的整改：`git diff 6bdb0fab __HEAD3__ -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff da690bf8 __HEAD3__ -- . ':(exclude)_bmad-output'`
3. 被复审的那段历史改动（零外审面）：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'`
4. 复审结论表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`
5. 被改文件全文：`scripts/verify_vault_install.py`

被测物是一个只读校验器：拿 `scripts/vault-install-manifest.json` 声明的部署边界，比对一个已存在的
Obsidian vault 目录，报告 match / missing / extra / content-drift / intentionally-excluded /
unreadable / hotkey-orphan / allowed-extra，并落一份文本报告。对被查目录只做 stat、列目录、读字节。

## 二 round-2 逐条处置（请核对处置是否到位、有无引入新问题）

| 你给的级别 | 问题 | 作者的处置 |
|---|---|---|
| HIGH | exclude 的存在性谓词吞 `OSError`，在进入 round-2 建的 unreadable 透传链之前就提前返回 | 新增三态谓词 `_entry_state()`（`present`/`absent`/`unreadable`，用 `os.lstat`），`_iter_relative` 入口与 `hits_for` 精确分支两处都换掉 |
| MEDIUM | 两侧都读不动、摘要相等时同一 copy 项仍计入 match | `unreadable_here` 非空即不记 match |
| MEDIUM | `_printable()` 挡不住 render **之前**的摘要编码异常 | 三处摘要编码改 `errors="backslashreplace"` |
| MEDIUM | `expanduser()` 对 `~未知用户名` 抛 `RuntimeError` ⇒ CLI 以 1 结束 | 抽 `_expanduser()`，`--vault`/`--source`/`--report`/`--manifest` 四处共用，归用法错档 |
| MEDIUM | 三种引号没消除「部分命令解析失败」的假拦下；表述过宽 | **未改行为**，只改表述并登记：JS 转义形态仍提取不到，真修需要 JS 语法分析 |
| LOW ×5 | `SKILL.md` 目录负控不承重 / 单一真相源门是自证 / unreadable 门没锁去重 / 文档旧口径 / `grep` 零命中当自证 | 全部已改（负控改成「7 合格文件 + 1 目录入口」并加前提断言；单一真相源改成行为门；去重改数次数；代码里「退出码 2」全部改成用法错档；`grep` 那条降级为辅助检查） |

## 三 请按重要性排序回答的问题

1. **`_entry_state()` 的引入是否完整？** 同一缺陷类别（把「问不出来」当成「不存在 / 空」）
   在这份代码里还有没有别的入口没换掉？请把你认为仍在的那些位置列出来，
   并说明它们是「真漏」还是「换了也没意义」。
2. **这一轮整改有没有引入新缺陷？** 特别看：`unreadable_here` 非空即 `continue` 之后，
   原先落在 match 的项现在去了哪里、有没有哪条既有语义被打破；
   `backslashreplace` 会不会让两个本该不同的摘要变得相同；
   `_expanduser()` 的四个调用点是否都在正确的位置返回用法错档。
3. 退出码契约现在是否**完全**自洽？还有没有出口会返回与四档语义冲突的值，
   或者以未捕获异常的形式脱离契约？
4. hotkeys 那条链上还剩哪些假放行 / 假拦下？作者登记的「JS 转义形态」是否穷尽了这一类？
5. 新增与收紧后的测试门是否**各自只拆一层**？有没有哪条即使被测逻辑退化也仍会通过？
   特别是新增的 `_entry_state` 相关门与去重门。
6. 复审结论表（材料 4）现在还有没有说得比证据宽的地方？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给：一句问题陈述 + `file:line` + 一句复现思路。
若某项核对下来没有问题，也请明说「核对结果：无问题」，并说明你核对到什么程度。

## 五 边界

- 只读审查：请不要修改工作树、不要运行安装脚本、不要连任何数据库。
- 不评价 live vault 上那 5 个多出来的条目应否放进白名单（另一张卡 U3-B 的裁定）。
- 不评价部署脚本 `deploy-vault.sh`（另一张卡 U3-C）。
- 不需要提供攻击性内容；本卡关心的是**误伤与漏报**：审计工具会不会改到被审对象，
  或者把「没查」说成「查过没问题」。
