# 独立复核请求 round-5（末轮）— CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`。**本卡最终 HEAD（请审这个）**：`bbdf19ea`。
**这是第 5 轮，也是 D-15 规定的最后一轮。** round-4 绑 `ce5bc6e9`，你给了
BLOCKER 0 / HIGH 2 / MEDIUM 4 / LOW 1，**七条我全部判成立并整改，无驳回项**，整改 commit = `bbdf19ea`。

两轮之间的代码 diff：`git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff ce5bc6e9 bbdf19ea -- backend/tests/unit/conftest.py`

⚠️ 请特别核 round-4 HIGH #2 那条 —— 你点名它是「第 9 处：把未交付的证据登记成已交付」。
我这轮**真跑并交付**了 `E/negctl-p1-green-r5-20260908T091401.txt`。请确认它确实存在、
确实是 P1-green（不是自指探针的绿跑冒充）、且绑定的 sha 与 `bbdf19ea` 一致。

**请只读以下内容**：

1. 本卡改动全文：
   `git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff da690bf8 HEAD -- backend/tests/unit/conftest.py`
2. 改动后的完整文件（读懂上下文用）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py`
3. 全部裁判存档（负控 / 正控 / 目录级 / 双树并发）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest/` 目录下全部 `*.txt`
4. 本卡承接的上一轮外审意见（只读这两段）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/codex-review-CARD-TEST-hygiene-vaultinit.md` 的 `:14-20`（HIGH #1）与 `:48-54`（MEDIUM #5）
5. 验收单：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md`
   （**§三·五 是本轮重点**：round-1 三条发现的逐条整改与承重验证）
6. **round-1 你自己的意见全文**（用于核对我是否真的改到位、有没有曲解）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/codex-review-CARD-HYGIENE-conftest.md`
7. **`backend/pytest.ini`**（round-1 你判我自述 #1「普遍保证不成立」的直接原因是它不在
   允许读取面内 —— 本轮把它加进来，请直接核验）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/pytest.ini`
8. 两轮之间的代码 diff（只有这一个文件）：
   `git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff 13a138c9 2c799422 -- backend/tests/unit/conftest.py`

**背景一句话**：`backend/tests/unit/conftest.py` 有一道 session 级卫生门，检查跑完
`tests/unit` 后有没有往工作树里撒 vault 骨架。它的三类信号里，`/tmp/test-vault*`
目录差集这一类读的是 `Path("/tmp").glob(...)` 的**全机**结果 —— `/tmp` 是全机共享的，
本仓有 60+ 个 worktree 并行跑测试，**别的树**在本 session 首尾两次快照之间建出匹配目录，
就会让**本车道**的 teardown 报错、`rc=1`，并在 nodeid 口径的红基线 diff 里多出一条
`ERROR` 行 —— 也就是把别人的环境噪音判成了本车道的回归。上一轮外审（读取面第 4 项
HIGH #1）给了三条出路，本卡取第三条：**把它定义为「环境受干扰、需要重跑」**。

**本卡的机制**（按信号能不能归属到本 worktree 分流）：

- **可归属 → 硬 fail 不变**：树内 vault 骨架路径、树内 tracked 文件 sha，
  外加**本卡新增**的树内源码字面量门（AST 扫 `tests/unit/**/*.py` 的
  `ast.Constant` 字符串，命中硬编码的 `/tmp/` + `test-vault` 路径即红）。
- **不可归属 → 降为告警**：`/tmp` 目录差集改走
  `warnings.warn(pytest.PytestWarning(...))`，文案含固定串「环境受干扰」。

这条降级是本卡**唯一的放宽面**；补偿是新增的源码字面量硬门，且骨架 / tracked sha
两个既有硬 fail 面一字未动。

---

## 二、本轮整改自述（**请独立核对，不要采信**）

| round-4 发现 | 处置 |
|---|---|
| **HIGH #1** 「计数＋失败正文」不能当替代合并判据 | **撤回**「判据改绑」写法（它扩大了原验收门的接受范围）。改为**向主 session 申请一次限定例外**，仅针对这一条 W4 哨兵类失败，其余红项逐条对账要求**不放宽**；**r4 与 r4b 共同送审**，明写「r4b 的空 diff 不消除 r4 的偏离」；并**撤回**「补 n≥10 就能真正排除」——无预定义效应阈值时有限次数不能排除任意概率变化 |
| **HIGH #2** 「r4 已补 P1-green」与交付不符（第 9 处） | **round-5 真跑并交付** `E/negctl-p1-green-r5-20260908T091401.txt`：抬头绑 HEAD 与 conftest / target 两个 sha256，结果 `8 passed` / `ERROR tests/` = 0 / `rc=0`。验收单已把这条从「已补齐」改成「**上一轮声称已补、实际未交付**」并标为第 9 处 |
| **MEDIUM** 清理脚本修复无法核验 | 把脚本片段 + **新旧写法在同一份开工存档上的实测条数（13 vs 12）** + 多出来那条的实际内容落进 `E/cleanup-script-fix-20260908T091401.txt`。⚠️ 期间发现我那条自检判据**本身也太宽**（grep 整个脚本含注释 ⇒ 恒命中 1），已更正为只看**可执行行**并补验伪锚 |
| **MEDIUM** 文本搜索与 AST 并不共享同一组盲区 | **技术性更正**：`b"/tmp/test-vault-x"` 不命中 AST 门却**会**命中完整路径 grep；`Path("/tmp") / "test-vault-x"` 不命中 AST 门却**会**命中 `grep 'test-vault'`。改成「两种搜索都不足以穷尽写者，但**覆盖范围不同**」，并写明「我在收窄一个越界结论时，顺手编了一个新的错误理由去支撑它」 |
| **MEDIUM** warning 旧保证未同步撤回 | 源码注释（C）与验收单**同步**收窄为「本仓 ini **本身**未配置这些策略、各轮存档中告警可见且未升级」，不再声称普遍保证；并更正我 round-2 把前意见原因窄化成「只是没读 ini」 |
| **MEDIUM** 历史空 diff 引用指向已被复用的文件 | 改为**每轮独立文件名** `red-diff-{r1open,n2,n2p-r3,r4,r4b,r5}.txt`，历史引用同步修正 |
| **LOW** 「最常见」缺频率依据 | 改为「**可先排查的情形**（是排查起点，不是结论，**也不主张它最高发**）」 |

### r5 全部裁判（绑 `bbdf19ea`）

P1 red（`E/negctl-p1-red-20260908T091401.txt`）+ **P1 green（`E/negctl-p1-green-r5-20260908T091401.txt`）**、
P2、7c①②、N3b 同根对撞、N3c 端到端、`tests/unit` 目录级
（`E/unit-after-r5-20260908T091741.txt`：**diff 0 行 / 202 条 / `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12` /
门 fail 0 / 环境受干扰 0**）。ruff check / format --check 均 rc=0。

## 三、本轮请重点回答的问题（按重要性排序）

1. **round-4 七条是否真的闭环**，尤其 HIGH #2 那份 P1-green 存档：它存在吗？是真的 P1-green 吗？
   绑定的 sha 与 `bbdf19ea` 一致吗？有没有又出现「声称交付但实际没有」的第二例？
2. **§三·八 关于那个 `>` 行的定性，现在还有越界吗？**
   「申请限定例外、待主 session 裁定」这个姿态是否恰当？还是说这条本身就该判为阻断？
3. **`ce5bc6e9 → bbdf19ea` 有没有引入新的回归 / 假绿？**
   fixture 是否仍零副作用、不依赖 cwd、不新增 `app.*` 导入？
4. **第 10 处同型错误在哪里？** 你已连续四轮在我声称「没有更多」之后找出新的
   （+3 / +1 / +1 = 第 9 处）。我这轮又自己发现一处（自检判据 grep 含注释恒命中，已登记为第 10 处）。
   请再找一次，并直说计数这件事本身是否还有意义。
5. **作为末轮**：以你的判断，这份改动**能不能合**？如果不能，**最小的阻断项**是什么？
   如果剩余问题都属于「登记不阻断」，请明确说，好让主 session 据此裁定。

## 四、输出格式

请按下面的结构输出，**每条结论都要给出你据以判断的文件与行号**：

```
## 结论
<一段话：这次改动能不能合，主要风险是什么>

## 发现
### [BLOCKER|HIGH|MEDIUM|LOW] <标题>
- **位置**: <file:line>
- **问题**: <是什么>
- **依据**: <你看到的证据，引原文或行号>
- **影响**: <会导致什么>
- **建议**: <怎么改>

## 作者自述逐条核对
| # | 主张 | 成立? | 依据 |
|---|---|---|---|

## 我没有检查的面
<如实列出>
```

严重度口径：**BLOCKER** = 数据丢失 / 写 live vault / 安全；**HIGH** = 门失效、
判据不成立、结论与证据不符；**MEDIUM/LOW** = 可读性、健壮性、登记类。

---

## 五、边界（**请不要评这些**）

- 不评 `backend/tests/contract/**` 的属性输入链（那是另一张卡 U5-D 的地盘）。
- 不评 `backend/tests/conftest.py` / `backend/tests/support/**` 的 W4 端口门
  （另一条车道 U7 的地盘，本卡禁改）。
- 不评 `tests/unit` 那 202 条既有红本身（那是第十三批多张 RED 卡分别在修的存量，
  本卡只要求 diff 为空，不要求变绿）。
- 不评上一轮外审的 MEDIUM #5（`None ↔ hash` 未区分「内容改变」与「检查无法完成」）
  的**修法** —— 本卡明确不扩面，只登记移交；但如果你认为「不修」这个决定本身
  在本卡语境下会造成新的假红或假绿，请说。
- 本卡零生产代码改动（`backend/app/**` 一行未动），不必评生产逻辑。
