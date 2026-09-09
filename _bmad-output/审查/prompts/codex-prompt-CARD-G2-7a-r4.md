# CARD-G2-7a 独立复核请求（round-4）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **__HEAD__**。

前三轮：r1 绑 `7aa89c5b`（0B/2H/4M/2L）、r2 绑 `3c1e3c00`（0B/1H/3M/3L）、
r3 绑 `725bbd19`（**0B/0H**/3M/5L）。**r3 已满足 D-15 的停止条件**，本轮是自愿加固：
r3 的 LOW-1/2/3 指出我三条门「给出虚假保证」（你自己跑的变异全部存活），这比没有门更糟。

**请只读以下五处（不要读别的、不要读 live vault、不要执行安装脚本）：**

1. r3 之后的整改：`git diff 725bbd19 __HEAD__ -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff 086771d3 __HEAD__ -- . ':(exclude)_bmad-output'`
3. 脚本与清单全文：`scripts/install-vault.sh`、`scripts/vault-install-manifest.json`
4. 校验器全文：`scripts/verify_vault_install.py`
5. 门文件：`backend/tests/unit/test_vault_install_manifest.py`

## 二 round-3 逐条处置

| 你给的级别 | 处置 |
|---|---|
| MEDIUM-1 摘要与 `-H` 不一致 ⇒ 正确复制报 drift | `_digest_pairs` 加 `follow_root`，copy 项**源侧**跟随**根**这一层软链；内部链两侧仍记 readlink 原文 |
| MEDIUM-2 generate 软链进 match | 探测改 `os.lstat` + `S_ISREG`（不跟随）+ 真开一次读 1 字节 |
| MEDIUM-3 `! cmp` 合并 rc 1 与 2；且我的门锁死了字面量 | 按返回码三分（1=不同 ✅ / 0=被复制 ❌ / 其余=读失败 ❌）；门解锁为「用 cmp 比较源与目标」，方向由三条行为门证明 |
| LOW-1 清理联动门并入了变量赋值 | 只认 `rm` 自己的操作数（含反斜杠续行）；验伪锚阈值从 `>=3` 降到 `>=1`（原值恰等于期望集大小，会抢在主断言前面） |
| LOW-2 结构门按整行子串 | 剥行内注释**与行尾续行反斜杠**后 `shlex` 分词，按 flag 字母集合判「有 R 就必须有 H」 |
| LOW-3 origin 门放过错数组/错区间；唯一锚被注释触发假红 | 新门按 path 反推**应属**哪个数组并比行号（30 条，带验伪锚），区间尾与真实结束行精确相等；`_sh_line` 改为优先取可执行行 |
| LOW-4 探测读整文件 | 只读 1 字节 |
| LOW-5 optional 文案过宽 | 收窄为「copy 比内容 / generate 不比」 |

我用**你给出的那几个变异体**回打新门：7/7 KILLED。首轮回打还暴露我自己两处
（`cp -PR` 因行尾反斜杠让 `shlex` 抛错被 `continue` 静默放行；软链变异体没拆到承重的
`lstat` 那句，补「链指向**可读**文件」的用例才分得开跟随与否），均已修并复验。
新的 origin 门首跑即抓到一个真错：生成段区间尾写的 `179` 落在 `echo` 行，真实 `fi` 在 `180`。

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
