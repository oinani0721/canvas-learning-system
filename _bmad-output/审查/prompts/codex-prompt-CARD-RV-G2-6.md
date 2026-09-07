# CARD-RV-G2-6 独立复核请求（round-1）

## 一 背景与最小读取面

仓库 worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡 HEAD `523c10f0`，基线 `da690bf8`。

这张卡做两件事：(A) 复审一段**没有经过外部审查**的历史整改；(B) 在其上加四项新能力。

(A) 的来历：卡 CARD-G2-6 的 Codex round-3 审的是 `ff105706`，之后作者又改了代码到
`c4e6b165`（`2 files +453/−50`）就直接合并了，那段改动**从未被第三方看过**。
本卡先把它逐条复审（结论表见下），再做 (B)。

**请只读以下四处，不要读别的文件、不要读任何 live vault 路径下的内容：**

1. 零外审面（被复审的那段历史改动）：
   `git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'`
2. 本卡改动：
   `git diff da690bf8 523c10f0 -- . ':(exclude)_bmad-output'`
3. 本卡的复审结论表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`
4. 被改文件全文：`scripts/verify_vault_install.py`

被测物是一个**只读校验器**：拿 `scripts/vault-install-manifest.json` 声明的部署边界，
去比对一个已存在的 Obsidian vault 目录，报告 match / missing / extra / content-drift /
intentionally-excluded / unreadable，并落一份文本报告。它对被查目录只做 stat、列目录、
读字节，唯一的写是 `--report` 指定的报告文件。

## 二 作者自述（请独立核对，不要采信）

1. **复审结论**：r3 的 8 条代码缺陷整改在 HEAD 上**全部成立**（P1=0）；2 条「门缺口」
   补门中 1 条经机械变异证明承重，另 1 条（方括号端到端门）对 `GLOB_CHARS` 变异
   **不可区分**，已如实登记为 P2 且选择不修。
2. **rc 分级无降级路径**：退出码由两档改四档（0 ok / 1 只有 missing / 2 mismatch /
   3 用法错）。作者声称**任何原先返回 1 的阻断场景都不会变成 0**。
3. **`extra_allow` 重叠拒绝**：新增的 manifest 顶层白名单，与已声明项或 exclude 模式
   重叠时拒绝加载。作者承认这是**字面层面**的重叠判定，不做两个通配模式之间的语言包含判定。
4. **hotkeys 两层**：校验器层比对同一 vault 内 `hotkeys.json` 的键与 `main.js` 里的
   命令 id 字面量；测试层单独钉住源码 `main.ts` 恰 10 个命令 id。
5. **`install-vault.sh:117` 单行改动**：skills 自检由「数目录条目」改为「数含 SKILL.md 的目录」。

## 三 请按重要性排序回答的问题

1. `c4e6b165` 那 8 条整改（报告落盘改为临时文件 + `os.replace`、禁写根的两层软链递归展开、
   落点按 `(st_dev, st_ino)` 身份比较、叶子摘要传播读取失败状态等）在 HEAD 上是否**真的成立**？
   有没有引入新的缺陷？作者的复审结论表里有没有说得比证据宽的地方？
2. rc 分级有没有把原本阻断的路径变成 0？特别看：多个桶同时非空时的取值、
   `unreadable` 的归档、`allowed_extra` 与 `intentionally_excluded` 不计退出码是否会掩盖真问题。
3. `extra_allow` 的通配模式能否放行一条本该被 declared 或 exclude 管住的路径？
   能否让校验器看到 vault 之外的东西？重叠判定的近似性有没有实际危害？
4. hotkeys 的字面量取值法有哪些假放行 / 假拦下的面？`main.js` 缺失时报
   `not evaluated` 而不计退出码，这个取舍在部署场景下是否留下盲区？
5. 新增的翻转用例是否**各自只拆一层**？有没有哪条测试即使被测逻辑退化也仍然会通过？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给：一句问题陈述 + `file:line` + 一句复现思路。
若某项核对下来没有问题，也请明说「核对结果：无问题」，并说明你核对到什么程度。

## 五 边界

- 只读审查：请不要修改工作树、不要运行安装脚本、不要连任何数据库。
- 不评价 live vault 上那 5 个多出来的条目应否放进白名单（那是另一张卡 U3-B 的裁定）。
- 不评价部署脚本 `deploy-vault.sh`（那是另一张卡 U3-C）。
- 不需要提供攻击性内容；本卡关心的是**误伤与漏报**，即审计工具会不会改到被审对象、
  或者把「没查」说成「查过没问题」。
