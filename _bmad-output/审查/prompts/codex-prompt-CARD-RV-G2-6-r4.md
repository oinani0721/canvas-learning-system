# CARD-RV-G2-6 独立复核请求（round-4）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`977d1e6d`**，基线 `da690bf8`。
前三轮送审态：round-1 `523c10f0`（0B/2H/5M/5L）、round-2 `6bdb0fab`（0B/1H/4M/5L）、
round-3 `736eb490`（0B/3H/4M/4L）。

round-3 你指出的三条 HIGH 里，**有一条是 round-3 的修法自己引入的假绿**
（摘要编码用了不单射的 `backslashreplace`，两个不同的软链目标会判等），
另有两条新引入的 MEDIUM。五条我都在本机独立复现之后才动手。
**这一轮的重点仍然是：这些整改本身有没有引入新缺陷，以及同一缺陷类别还有没有没盖到的入口。**

**请只读以下五处，不要读别的文件、不要读任何 live vault 路径下的内容：**

1. round-3 之后的整改：`git diff 736eb490 977d1e6d -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff da690bf8 977d1e6d -- . ':(exclude)_bmad-output'`
3. 被复审的那段历史改动（零外审面）：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'`
4. 复审结论表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`
5. 被改文件全文：`scripts/verify_vault_install.py`

被测物是一个只读校验器：拿 `scripts/vault-install-manifest.json` 声明的部署边界，比对一个已存在的
Obsidian vault 目录，报告 match / missing / extra / content-drift / intentionally-excluded /
unreadable / hotkey-orphan / allowed-extra，并落一份文本报告。对被查目录只做 stat、列目录、读字节。

## 二 round-3 逐条处置（请核对处置是否到位、有无引入新问题）

| 你给的级别 | 问题 | 作者的处置 |
|---|---|---|
| HIGH【新引入】 | `backslashreplace` 不单射 ⇒ 摘要碰撞 = 假绿 | 三处摘要编码改 `surrogatepass`；补 AST 判据（摘要函数里的 `encode` 不得用 `backslashreplace`，带验伪锚断言至少见到 3 处 `encode`）+ 行为判据（两个不同软链目标必须给出不同摘要）。`_printable()` 那处是**报告输出渲染**，仍用 `backslashreplace`（要的是可读转义，不需要单射） |
| HIGH【遗漏】 | 还有四个「查不到即不存在／不扫描」的入口 | 四处全换 `_entry_state`：item 目标问不出来归 unreadable（原降级成 missing）；extra 覆盖面根问不出来登记（原静默跳过）；hotkeys 两处把「查不到」与「确实没有」分开 |
| HIGH【遗漏】 | `_leaf_digest` 落到 `"?:unknown"` 且 `bad=False`；`_kind_ok` 把查询失败当 `nondir` | `_leaf_digest` 先探 `_entry_state`；`_kind_ok` 问不出类型时对**所有** kind 返回 False |
| MEDIUM【新引入】 | `_entry_state` 把 `ENOTDIR` 错归 unreadable | `NotADirectoryError` 归 `absent` |
| MEDIUM【新引入】 | 提前 `continue` 遮掉同一项里的真实内容差异 | 调换顺序：先判漂移、再判读不动 |
| MEDIUM【遗留】 | stdout 编码失败 rc=1 / 断管 rc=120 脱离四档 | `__main__` 里先 `reconfigure(errors=...)`，再接住 `SystemExit` 与 `BrokenPipeError`；断管归 `EXIT_USAGE`。**没有为此放宽零写门**——`os.dup2(os.open(os.devnull,…))` 会让 AST 零写门变红，改用哑对象替换 `sys.stdout` |
| MEDIUM【遗留】 | hotkeys 假拦下不止 JS 转义 | **未改行为**，只扩大登记：拼接表达式同时造假拦下与假放行 |
| LOW ×4 | 入口门对照 / 去重门前提 / 编码门与展开门覆盖 / 表述三处 | 全部已改 |

## 三 请按重要性排序回答的问题

1. **`surrogatepass` 这个选择本身对不对？** 它在哪些输入上会抛、会不会引入新的碰撞面或新的异常出口？
   摘要路径上还有没有别的**有损**变换（不只是编码）会让不同输入判等？
2. **`_entry_state` 现在覆盖完整了吗？** 同一缺陷类别（把「问不出来」当成「不存在 / 空 / 不符合类型」）
   在这份代码里还有没有入口没换。请把仍在的位置列出来，并分「真漏 / 换了也没意义」两列。
3. **这一轮整改有没有引入新缺陷？** 特别看：`_kind_ok` 一律返回 False 会不会让某些条目
   从「故意不排除」变成「误报 extra」；先判漂移再判读不动的新顺序有没有别的副作用；
   `__main__` 里替换 `sys.stdout` 会不会影响正常路径。
4. 退出码契约现在是否完全自洽？还有没有出口会返回与四档语义冲突的值。
5. 新增与收紧后的测试门是否各自只拆一层？有没有哪条即使被测逻辑退化也仍会通过？
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
