# 独立复核请求 round-6（绑最终 HEAD）— CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`。**本卡最终 HEAD（请审这个）**：`475f2bee`。

## ⚠️ 关于轮次（请先独立核这一点，它决定这一轮该不该存在）

D-15：「有代码改动的卡 Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0，上限 5；
审后再改代码 ⇒ 必再送一轮（**只改 `_bmad-output` 不算**）；第 5 轮仍有 HIGH ⇒ 停下交主 session 人审。」

时间线：
- round-5 审 `bbdf19ea`：**BLOCKER 0 / HIGH 1 / MEDIUM 4，五条全部为文档口径、零代码问题**，全部成立整改。
- 整改得 `0491b12a`：**docs-only**（`git diff bbdf19ea 0491b12a -- backend` 为空）⇒ 按 §1 括注不触发再送轮。
- 随后本卡对最终状态跑了**7 视角对抗自审**（每条发现 3 角度反驳者验证），**确认一条代码层 HIGH**：
  目录符号链接让源码字面量门**静默放行**（`os.walk(followlinks=False)` 静默跳过目录链接，
  既不进 hits 也不进 unchecked —— 你五轮都没抓到它，我也不怪你，我自己也是自审才抓到的）。
  修复 = **审后再改代码** ⇒ 按协议明文「必再送一轮」。
- 故有本 round-6：它既是强制重审，也是**第一个绑最终 HEAD 的轮**。

**轮次计数的口径问题（交你与主 session 判，车道不自判）**：若 docs-only 整改计入 5 轮上限，
本轮超限、应停交人审；若按 §1 括注不计入，本轮合法。**请给出你的独立判断。**

本卡最终 HEAD 的 conftest sha256（供你核对）：`6f8f29f052921906a92beb691226e47e088771d24759c2eaf7c15e24b989fb76`

两轮之间的代码 diff：`git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a diff ce5bc6e9 475f2bee09e3772d627414a3bc76f70d02b5b93a -- backend/tests/unit/conftest.py`
（含 r5 整改期 docs-only 之后本轮唯一的代码改动：目录符号链接记账）

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

### round-5 五条（全部文档口径）—— 已全部整改（清单见上一版 prompt 的处置表，此处不重复）；
其中 HIGH（台账与 §三·八 自相矛盾的宽建议）已撤回并统一口径：**申请不等于获准，
r4 的 W4 哨兵偏离在主 session 裁定前仍阻断放行**。

### 自审发现并修复的代码层 HIGH（§三·九，Codex 五轮未抓到）

- **缺陷**：`os.walk(followlinks=False)` 对**目录**符号链接静默跳过 —— 目标里的 `.py`
  既不进 `hits` 也不进 `unchecked`，与 docstring「越界一律进 unchecked / 不静默跳过」正相反。
  round-1 MEDIUM 只让我修了**文件**链接那一半；「followlinks=False 挡住目录符号链接」
  这句话本身为真，但「挡住 ≠ 记账」—— 我把「不跟随」写成了「已设防」。
- **取证**（正控 + 被测）：同内容放普通目录 → 门**抓到**；放指向树外的目录符号链接后面 →
  **既不抓也不记账**。存档 `E/negctl-n4-dirlink-20260908T112304-VOID.txt`（修前）。
- **修复**：每层 walk 对 `dirnames` 逐个 `is_symlink()`；目标在扫描根内 ⇒ 跳过（walk 会独立
  走到真实目录）；根外或无法判定 ⇒ 进 `unchecked`。
- **承重验证**：`E/negctl-n4-dirlink-fixed-20260908T112758.txt`（脚本**先断言 sha 已变才写「修后」**）：
  正控仍抓到；被测改为记账；树内链接同样记账；零残留。
- ⚠️ **如实登记的第 14 处同型**：该修复的第一次补丁 `ANCHOR_FAIL` 未生效，我已在存档抬头写「修后」
  —— 由 sha 对比当场拦下，存档作废改名 `-VOID` 留档。验收单 §六⑫ 已把计数更新为
  「至少十五次」并逐条列 9~15（第 15 次正是补审抓的：写「已另行补跑」时补跑仍在进行）。
- ⚠️ **自审覆盖缺口（如实披露）**：7 视角中 5 个因 session limit 未跑成，实际先只覆盖 2/7；
  该 5 视角已补跑（claims-vs-evidence / claimed-vs-delivered / protocol-compliance /
  number-consistency / broken-judges），补审结果与处置见验收单 §三·九·补。
- ⚠️ **本轮未重跑 N2'**（唯一未重跑的承重裁判）：dirlink 记账改的是扫描遍历，
  N2' 验证的是 `/tmp` 差集的告警出口，路径不相交；理由与补救选项见 §三·九 末段。

### r6 全部裁判（绑本 HEAD）

四个门下目录级（`E/{unit,api,regression,skills}-after-r6-*.txt`）、P1 red/green、P2、7c①②、
N3b 同根对撞、N3c 端到端、N4 dirlink（正控+被测+树内对照）、静态门存档（ruff 双门、7a 双向验伪锚）。
具体数字以存档为准。

## 三、本轮请重点回答的问题（按重要性排序）

1. **轮次推理成立吗？** 这一轮该不该存在？若你认为超限，请直接说，我停交人审。
2. **dirlink 修复正确吗？** `git diff ce5bc6e9 HEAD -- backend/tests/unit/conftest.py` 里的
   目录符号链接记账逻辑有没有新引入的假绿 / 假红 / 死循环？记账条件（`is True` 才跳过、
   `None` 记账）与 `_hygiene_within_root` 三态的配合对不对？
3. **§三·九 的自证链有没有「声明比证据宽」？** 尤其「正控仍抓到 / 被测改为记账」这两句
   与存档实际输出是否相符？
4. **round-5 五条是否闭环？** 台账与 §三·八 还矛盾吗？有没有第三处残留？
5. **验收单（含 §六⑫ 的 15 次清单与 §三·九/§三·九·补）作为最终交付文档，还有没有事实层面站不住的地方？**
6. **作为绑最终 HEAD 的一轮：能不能合？** 能则明确 BLOCKER/HIGH = 0；不能则给**最小阻断项**
   并归类（阻断级 vs 登记不阻断）。已知待裁事项仅一件：r4 W4 哨兵偏离的限定例外
   （只能由主 session 裁，请只判它是否被**如实登记**）。

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
