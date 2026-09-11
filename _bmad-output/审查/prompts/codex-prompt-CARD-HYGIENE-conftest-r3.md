# 独立复核请求 round-3 — CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`。**本卡最终 HEAD（请审这个）**：`459190f0`。
**这是第 3 轮。** round-2 绑 `2c799422`，你给了 BLOCKER 0 / HIGH 3 / MEDIUM 2。
**五条我全部判为成立并整改，无驳回项**，整改 commit = `459190f0`。
整改后**全部裁判再次重跑**（这次包含 api / regression / skills 三个目录级 ——
那正是 round-2 HIGH #2 指出我上一轮没跑的）。

两轮之间的代码 diff：
`git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff 2c799422 459190f0 -- backend/tests/unit/conftest.py`

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

### 对 round-2 五条发现的处置（全部判成立，无驳回）

1. **HIGH #1 诊断结论越界** —— 三类信号原先共用一句「运行污染了工作树」+ 同一份写者推定。
   已改成三分段各自报，标题换成「tests/unit **卫生门未通过**」：
   - 【工作树被写坏】首尾快照真的变了 ⇒ 本次运行确实写了东西。**写者推定只留这一段**。
   - 【源码规则命中】明写「**不表示本次运行写了任何东西**」。
   - 【检查无法完成】明写「这**不是**已经发生写入的证据，只是这道门这次没能看全」。
   r3 实测三类各归各位：P1（从不执行的常量）→【源码规则命中】，
   「运行污染了工作树」0 次、「最可能的写者」0 次；
   P2（真建骨架目录）→【工作树被写坏】，写者推定 1 次；
   N3c（枚举被拒）→【检查无法完成】，污染断言 0 次。
   验收单 4-B 段的「这是别人弄的」也已改掉。

2. **HIGH #2「全部裁判重跑」缺三目录本轮存档** —— **补跑**，不是改措辞。
   `{api,regression,skills}-after-r3-20260908T081114.txt`：268 passed / 1464 passed+6skip+10xfail /
   369 passed，rc 全 0，与开工**红** nodeid 集 diff 全空，三轮 `环境受干扰` 计数均 0。

3. **HIGH #3 抄错时刻** —— `06:56:28` 被我抄成 `07:56:28`。已更正；结论仍成立
   （06:56:28 < 06:59:14）但依据换成正确数字。并补上你指出的口径区分：
   我比的是**进程运行窗口**，门比的是 **fixture 两次快照的窗口**，后者内含于前者
   ⇒ 前者无交集是后者无交集的**充分条件**，两者不可互换着写。

4. **MEDIUM 大小写别名假红** —— 新增 `_hygiene_within_root()` 三态判定：先试字面
   `is_relative_to`，不成立再逐级向上用 `samefile` 做**文件系统身份**比对；
   比对本身失败返回 `None` ⇒ 进「检查无法完成」。
   验证带**反向验伪锚**（`probe-case-alias-20260908T081030.txt`）：
   别名 → True；`/etc/hosts`、`backend/tests/api`、`backend/app` → 仍 False；
   树内正常文件 → True；树外不存在路径 → None（不崩、不判 True）。
   同时按你的提醒明确：扫描根是 `tests/unit`，链到**同一 worktree 的其他目录**也会被拒。

5. **MEDIUM N3c 前提 rc 采集错** —— `ls … | head -1` 后取 `$?` 拿的是 `head` 的 rc。
   已改先存变量再取 rc，另加**不经 shell 管道**的 Python 侧独立第二源。
   r3 实测 `ls_rc=1` + `py_scandir=PermissionError`。

### 自述核对的两处处置

- **#11「红 nodeid 集」措辞未完全落实** —— 成立，5 处旧措辞已全改，并在「未证明什么」补上
  「存档只有文件级进度点，不能证明全部通过用例的 nodeid 集也相同」。
- **#14「三次之外没有更多同型错误」不成立** —— 成立。计数已从三次改为**六次**并逐条列出，
  且明写「六」是**已被发现的**次数、不是全部。另新增一条**真实事故**登记：
  窗口三我把通告发送面从 10 条车道缩到 5 条，漏发的 U6 车道恰好在该时段跑目录级被打红，
  且我给出的清单是阶段性快照却没标注截止时刻 —— 同一型第 7 次，这次代价落在别人身上。

### r3 全部裁判存档

N1'（`E/negctl-n1-after-20260908T081952.txt`）、P1 red/green、P2、7c①②、
N3b 同根对撞（`E/negctl-n3b-enum-denied-samefixture-20260908T081124.txt`）、
N3c 端到端（`E/negctl-n3c-enum-e2e-20260908T081124.txt`）、
N2' 双树并发（`E/unit-n2p-20260908T082024.txt` + `treeB-probe-n2p-*` + `window-n2p-*`，
树 B 目录 `/tmp/test-vault-treeB-57658`，对 202 基线 diff **为空**）、
四个门下目录级。三端点对照（r3）：开工基线 0/29/0/rc=1 · N2 修前 1/30/0/rc=1 ·
N2' 修后 0/29/1/rc=1（列：门 fail / ERROR tests/ / 环境受干扰 / rc）。

## 三、本轮请重点回答的问题（按重要性排序）

1. **HIGH #1 的三分段真的把语义分干净了吗？**
   有没有哪条输入会落进**错误的**分段？例如：既有快照变化又有源码命中时，
   写者推定会不会又跨到不该跟的那一段后面？三段标题本身有没有仍然越界的措辞？
2. **`_hygiene_within_root()` 的三态判定有没有引入新的假绿？**
   特别是：`samefile` 逐级向上的循环会不会在某些布局下**误判为 True**（把树外说成树内）？
   返回 `None` 的分支会不会被后续逻辑当成「通过」？循环有没有不终止的可能？
3. **`2c799422 → 459190f0` 之间有没有引入新的回归？**
   fixture 是否仍零副作用、不依赖 cwd、不新增 `app.*` 导入？
   三类列表的收集与出口有没有哪条路径漏掉（收集了但不进 `sections`）？
4. **round-2 三条 HIGH 各自的整改是否**真的**闭环，还是只改了你点名的那一处？**
   尤其 HIGH #2：我补跑了三个目录，但「全部裁判重跑」这句话现在**准确**了吗？
5. **验收单里我自认的六次 + 一次事故（共七次）同型错误之外，还有第八处吗？**
   round-2 你在这个问题上判我「不成立」并找出三处，请再查一次。
6. **有没有哪一条我判「成立并整改」其实是误解了你的意思、改错了方向？**

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
