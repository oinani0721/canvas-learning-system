# CARD-RV-G2-6 独立复核请求（round-2）

## 一 背景与最小读取面

仓库 worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`6bdb0fab`**，基线 `da690bf8`，round-1 送审态 `523c10f0`。

round-1 你给出 0 BLOCKER / 2 HIGH / 5 MEDIUM / 5 LOW。作者据此改了代码（见 §二），
**这一轮的重点是：那些整改本身有没有引入新缺陷。** 前三轮的经验是每一轮修复都会带进新东西。

**请只读以下五处，不要读别的文件、不要读任何 live vault 路径下的内容：**

1. round-1 之后的整改：`git diff 523c10f0 6bdb0fab -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff da690bf8 6bdb0fab -- . ':(exclude)_bmad-output'`
3. 被复审的那段历史改动（零外审面）：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'`
4. 复审结论表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`
5. 被改文件全文：`scripts/verify_vault_install.py`

被测物是一个只读校验器：拿 `scripts/vault-install-manifest.json` 声明的部署边界，比对一个已存在的
Obsidian vault 目录，报告 match / missing / extra / content-drift / intentionally-excluded /
unreadable / hotkey-orphan / allowed-extra，并落一份文本报告。对被查目录只做 stat、列目录、读字节。

## 二 round-1 逐条处置（请核对处置是否到位、有无引入新问题）

| 你给的级别 | 问题 | 作者的处置 |
|---|---|---|
| HIGH | 给了 `--source` 而源端缺该 copy 项时，未比较的目标仍记 match | 改记 `unreadable`，计入阻断 |
| HIGH | exclude 扫描失败仍可能静默返回 0 | `_iter_relative` 增 `unreadable` 出参，透传到 `hits_for` → `verify()` 登记，跨 exclude 项去重 |
| MEDIUM | `main.js` 未评估仍 rc=0 | **未改**，登记为已知盲区（这是卡文钉死的语义：不计退出码、但报告明写 not evaluated） |
| MEDIUM | 命令字面量法假放行/假拦下；`main.ts` 数量门不证明注册语义 | 正则改认三种引号（消除假拦下）；`main.ts` 门绑到 `addCommand({ id:` 注册点。假放行仍在，已登记 |
| MEDIUM | 新 hotkeys 输入重开了未捕获的编码异常 | 新增 `_printable()`，在 `render()` 的**输出边界**统一转义，一处覆盖全部来源 |
| MEDIUM | `argparse` 参数错误仍返回 2 | 自定义 `_Parser.error()` 抛 `SystemExit(EXIT_USAGE)` |
| MEDIUM | `:117` 把 `SKILL.md` 是目录的半成品计为完成 | 判据加 `-type f`；测试补行为断言与「SKILL.md 是目录」负控 |
| LOW ×3 | 重叠门未锁反向覆盖 / not evaluated 断言借用别段 / orphan 与非法 JSON 门未排除其他桶 | 均已收紧 |
| LOW | 方括号门对 GLOB_CHARS 不可区分 | 同意，维持登记 |
| LOW | 复审表 HEAD 绑定与 R3-2 证据表述过宽 | 已改：绑定限定到开工快照；R3-2 依据收窄为「只证明预置文件没被删，未证明发生过独占创建冲突」 |

两条口径限定也已采纳：不再声称「绝不读取树外」（改为「不写被审树」）；
「原先 1 不会变 0」限定为「白名单为空时成立」。

## 三 请按重要性排序回答的问题

1. **整改本身有没有引入新缺陷？** 特别看：`_iter_relative` 新出参的调用链是否有遗漏或重复登记；
   源端缺项改记 `unreadable` 之后，原先依赖 match 计数的地方是否被打破；
   `_printable()` 放在 `render()` 出口是否真的覆盖了全部输出路径。
2. 退出码契约现在是否自洽？还有没有别的出口会返回一个与四档语义冲突的值？
3. `_Parser.error()` 的改法有没有副作用（`--help`、子命令、未知参数、`SystemExit` 被上层吞掉等）？
4. hotkeys 那条链上还剩哪些假放行 / 假拦下？「产物里 0 个命令 id 就改报 unreadable」这个取舍
   有没有把一个本该报出来的真问题藏起来？
5. 新增与收紧后的测试门，是否**各自只拆一层**？有没有哪条即使被测逻辑退化也仍会通过？
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
