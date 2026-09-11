# 独立复核请求 round-4 — CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`。**本卡最终 HEAD（请审这个）**：`ce5bc6e9`。
**这是第 4 轮**（D-15 上限 5）。round-3 绑 `459190f0`，你给了 BLOCKER 0 / HIGH 2 / MEDIUM 1，
**三条我全部判成立并整改，无驳回项**，整改 commit = `ce5bc6e9`。

两轮之间的代码 diff（只有这一个文件）：
`git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff 459190f0 ce5bc6e9 -- backend/tests/unit/conftest.py`

⚠️ **本轮有一件我主动提请你审的事**（不是你上轮提的）：r4 收工 `tests/unit` 目录级出现了
**一个 `>` 行**（`test_accept_candidate_already_accepted_returns_422` 增、
`test_mock_degradation_transparency…test_mock_mode_logs_warning` 减，总数仍 202）。
我把取证与**未能排除的部分**全写在验收单 **§三·八**，请重点核这一节的结论有没有再次超出证据。

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

### 对 round-3 三条的处置（全部成立，无驳回）

1. **HIGH #1 分段内部仍推断确定写入** —— 这是 round-2 HIGH #1 的未闭合部分：
   我把三类信号拆开了，却在**每一段新写的话里**各埋一个越界断言。逐条改：

   | 位置 | 改前 | 改后 |
   |---|---|---|
   | 快照段标题 | 「…即本次运行确实写了东西」 | 「【**快照差异**】…发生了变化；差异本身**不指认写者**，也不单独证明写入内容（sha 侧读取失败记 `None`，`None ↔ hash` 未必是内容改变）」 |
   | 快照段提示 | 「**最可能的写者**: …」 | 「**最常见**的成因（**是排查起点，不是结论**）: …」 |
   | 源码段 | 「它拦的是『**将来会**往全机共享 /tmp 写』」 | 「只说明源码里出现了被禁止的硬编码常量，**既不表示本次运行写了什么，也不预言将来一定会写**（常量可能从不执行——P1 用的就是这种）」 |
   | 无法检查段 | 「**既没通过也没违规**」 | 「**是否违规尚不能判定**」，并补「**也不表示这些目标没有问题**」 |

   同一句话还写在**收集处的注释**里，是本卡 patch 脚本的**越界措辞黑名单自校验**抓到的。
   静态存档 `E/static-gates-r4-20260908T084107.txt`：四条越界串全部归零，
   两条新串（`尚不能判定` / `不指认写者`）各出现 2 次。

2. **HIGH #2 验收单仍把「未发现写者」写成已排除本树回归** —— 三处收窄：
   `U:42` → 「**在这两条搜索的命中里未发现写者**」并写明文本搜索与 AST 门**共享同一组盲区**；
   历史说明补上漏掉的 **(d)**，(d) 节旧文案标 ~~删除线~~ +「已撤回，勿引用」；
   方案依据重写为**三条不依赖「本树没有写者」**的理由（其中「门读的是全机 glob 结果」
   这一条与本树有无写者**无关**，单独就足以推翻原方案）。
   复查：「本树已无 `/tmp` 根写者」全单只剩 3 处**否定式**出现。

3. **MEDIUM 清理对账判据第三次复发** —— 根因是前两次**只在存档追加更正、没修脚本本体**。
   本次从根上改 `cleanup.sh`（`grep -oE '/tmp/test-vault[^ ]*'` → `awk '/^d/ {print $NF}'`），
   按你的建议**保留原始失败记录**并在同一存档追加 §6b：更正判据（12 = 12、rc=0）
   + **验伪锚**（塞一个假条目 → rc=1）+ worktree 残留 0。

### 你在自述核对里指出的缺档，已补

- **#3** 7a/7d/ruff 缺 r3 独立存档 → `E/static-gates-r4-20260908T084107.txt`
  （7a 带**双向**验伪锚：当前版 = 0、`da690bf8` 版 = 1）。
- **#4** 缺独立命名的 P1-green → r4 已补独立存档。
- **#7** `_hygiene_within_root` docstring 边界 → 已写明「**目标文件本身消失不一定返回 `None`**，
  只要父目录仍在且字面包含成立就返回 `True`，由后续 `read_bytes()` 的 `OSError` 收进 `unchecked`」。
- **#13** `U:569` → 已改「**红** nodeid 口径」。
- **#14** 「加 pytest.ini 后告警不会升级」仍只能条件成立 → 接受，并承认我 round-2 把你的原意
  窄化理解成「只是没读 ini」是**对前意见原因的收窄**。
- **#15** 「七次之外没有更多」不成立 → 接受，计数改为 **8** 并写明**无法穷尽**，
  且加了一句「『我已经找完了』这句话本身就是同一型错误的一个实例」。

### ⚠️ 我主动提请复核的一件事（验收单 §三·八）

r4 收工出现 1 个 `>` 行。我的取证与定性：
- **已证明**：失败正文是 W4 哨兵（越界连接现网 Neo4j 7691）；
  `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=12, advisory=0, unaccounted=0)` 与开工基线逐字相同；
  红总数恒 202；**同一份代码连跑两次归属即翻转**（r4b diff 为空，conftest sha 与 r4 相同）；
  换回 `da690bf8` 原版 conftest 在本树跑也是另一侧（备份 + `trap` 还原，前后 sha 一致）。
- **未证明**：本卡在 session setup 段新增的 `os.walk` + AST 扫描（252 文件 ~0.5s）
  **是否改变漂移概率**。基线对照只跑 1 次且未触发 —— 「没触发」不等于「不会触发」。
  要排除需 n≥10 的无负载交错采样（约 80 分钟），本卡未做，成本理由已写明。
- **处置**：交付轮取 r4b，但 r4 原样留档；判据改绑「连接次数 + 失败正文」；
  登记为未证明项并移交主 session 裁定。**没有写成「与本卡无关」。**

## 三、本轮请重点回答的问题（按重要性排序）

1. **验收单 §三·八 的结论有没有再次超出证据？**
   我声称「已证明 / 未证明」的划分对不对？有没有哪一条我说「已证明」其实证据不够，
   或者说「未证明」其实已经有足够证据？处置（取 r4b 交付 + 留档 r4 + 改绑判据 + 移交）是否恰当？
2. **三段措辞现在还有越界吗？**
   逐句核 C 的三个 `sections.append`，以及收集处注释。有没有仍在断言证据支持不到的东西？
   新写的「不指认写者」「尚不能判定」「是排查起点，不是结论」本身有没有反过来说得太弱、
   以至于读者会忽略真正的硬失败？
3. **`459190f0 → ce5bc6e9` 有没有引入新的回归或新的假绿？**
   fixture 是否仍零副作用、不依赖 cwd、不新增 `app.*` 导入？三类收集与出口有无遗漏路径？
4. **round-3 三条整改是否真的闭环**，还是只改了你点名的那一处？
   尤其 MEDIUM：我说「从根上修了脚本」，但那个脚本不在你的读取面内 —— 存档里的证据够不够支撑这句话？
5. **第 9 处同型错误在哪里？**
   前三轮你分别在我声称「没有更多」之后找出 +3 和 +1。我这轮把计数写成 8 并声明「无法穷尽」。
   请再找一次。
6. **有没有哪一条我判「成立并整改」其实误解了你的意思、改错了方向？**

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
