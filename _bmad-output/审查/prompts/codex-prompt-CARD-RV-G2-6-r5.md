# CARD-RV-G2-6 独立复核请求（round-5 — 卡族轮次上限）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`ee18eb44`**，基线 `da690bf8`。
前四轮送审态：`523c10f0`（0B/2H/5M/5L）、`6bdb0fab`（0B/1H/4M/5L）、
`736eb490`（0B/3H/4M/4L）、`977d1e6d`（0B/4H/3M/2L）。

**本卡的协议轮次上限是 5，这是最后一轮。** 若这一轮仍有 BLOCKER 或 HIGH，
车道不自判通过，交主 session 人审——所以请把「还剩什么」说清楚，比给出结论更重要。

round-4 的四条 HIGH 里，有一条是 round-4 的修法自己引入的（`_kind_ok` 一律返回 False），
两条是「摘要在编码之前就丢了信息」（`Path` 规范化、特殊文件类型合并）。
七条我都本机独立复现之后才动手。

**请只读以下五处，不要读别的文件、不要读任何 live vault 路径下的内容：**

1. round-4 之后的整改：`git diff 977d1e6d ee18eb44 -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff da690bf8 ee18eb44 -- . ':(exclude)_bmad-output'`
3. 被复审的那段历史改动（零外审面）：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'`
4. 复审结论表：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md`
5. 被改文件全文：`scripts/verify_vault_install.py`

被测物是一个只读校验器：拿 `scripts/vault-install-manifest.json` 声明的部署边界，比对一个已存在的
Obsidian vault 目录，报告 match / missing / extra / content-drift / intentionally-excluded /
unreadable / hotkey-orphan / allowed-extra，并落一份文本报告。对被查目录只做 stat、列目录、读字节。

## 二 round-4 逐条处置

| 你给的级别 | 问题 | 作者的处置 |
|---|---|---|
| HIGH | 软链目标经 `str(Path.readlink())` 规范化后判等 | 改 `os.readlink()` 取原文 |
| HIGH | FIFO / socket / 设备节点一律 `"?:unknown"` | 记 `stat.S_IFMT` 类型位；`_leaf_digest` 改为单次 `lstat` 决定分支，不再用会吞 OSError 的 `is_*()` |
| HIGH【round-4 新引入】 | `_kind_ok` 一律 False，丢失败原因 + 误报 extra | 改**三态** `bool \| None`；`matches_exact` / `is_under_exclusion` / `hits_for` 全部接三态并透传失败位置 |
| HIGH | `lstat` 成功 ≠ 跟随软链后查得到 | 新增 `_resolved_kind()`（dir/file/other/unreadable），extra 覆盖面根与 `main.js` 两处都用它 |
| MEDIUM【round-4 新引入】 | 「两侧内容相同、只一侧不可读」被报成 drift | `_digest` 拆成 `_digest_pairs()` + `_fold(pairs, skip)`；`verify()` 取两侧 unreadable **并集**做 skip |
| MEDIUM | 目标 missing 时源端查询失败只进 detail | 同时登记 unreadable |
| MEDIUM | 断管保护只覆盖最后的 stdout flush | `main()` 外层加 `except BrokenPipeError`；收尾**两个流**都 flush 并各自换哑对象 |
| LOW | 摘要门按名字判 | 改**性质门**：10 个两两不同的叶子喂进真实摘要，断言两两不同 |
| LOW | 去重门只证有两条配置 | 改逐条单独跑 `hits_for`，每条都必须到达该位置 |

**明确没改、已登记的三处**（请判断这个取舍是否可接受）：
`_forbidden_roots` 与报告落点的身份/类型查询（那条链已经 fail-closed，查询失败最坏是多拒一次）；
skeleton 的 `is_dir()`；hotkeys 的假放行/假拦下（需要 JS 语法分析）。

## 三 请按重要性排序回答的问题

1. **这一轮整改有没有引入新缺陷？** 特别看：`_digest_pairs` 的 key 由「相对被测目录」改成
   「相对 base」之后，exclude 过滤与 skip 匹配是否仍然对齐；三态 `_kind_ok` 的三个调用点
   是否都真的接住了 None；`_fold` 的 skip 是否可能把**真差异**也剔掉。
2. **摘要现在是否单射？** 还有没有别的**有损变换**（不只是编码）让不同输入判等。
3. `_entry_state` / `_resolved_kind` 两个三态谓词是否覆盖完整；仍在用会吞 OSError 的谓词
   做「有/无」「是/不是」判断的位置还有哪些，请分「真漏 / 换了也没意义」两列。
4. 退出码契约现在是否完全自洽。
5. 新增与收紧后的测试门是否各自只拆一层。
6. 复审结论表（材料 4）还有没有说得比证据宽的地方。
7. **如果这一轮仍有 HIGH，请说明它属于「本卡范围内该修」还是「应转下一张卡」**，
   以便主 session 裁定。

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给：一句问题陈述 + `file:line` + 一句复现思路。
若某项核对下来没有问题，也请明说「核对结果：无问题」，并说明你核对到什么程度。

## 五 边界

- 只读审查：请不要修改工作树、不要运行安装脚本、不要连任何数据库。
- 不评价 live vault 上那 5 个多出来的条目应否放进白名单（另一张卡 U3-B 的裁定）。
- 不评价部署脚本 `deploy-vault.sh`（另一张卡 U3-C）。
- 不需要提供攻击性内容；本卡关心的是**误伤与漏报**：审计工具会不会改到被审对象，
  或者把「没查」说成「查过没问题」。
