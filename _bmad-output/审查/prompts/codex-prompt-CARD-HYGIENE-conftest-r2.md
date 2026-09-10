# 独立复核请求 round-2 — CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`（本卡从这里切）。**本卡最终 HEAD（请审这个）**：`2c799422`。
**这是第 2 轮。** round-1 绑 `13a138c9`，你给了 BLOCKER 0 / HIGH 2 / MEDIUM 1，判「不建议原样合并」。
两条 HIGH 与那条 MEDIUM 我**全部判为成立并整改**（无驳回项），整改 commit = `2c799422`。
整改后**全部裁判已重跑**，没有复用 round-1 的任何存档。
本卡**只改一个文件**：`backend/tests/unit/conftest.py`（地盘门实测：
`git diff --name-only --no-color da690bf8 HEAD -- . ':(exclude)_bmad-output'` 恰为该一项）。

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

### 对 round-1 三条发现的处置

1. **HIGH #1（目录枚举失败静默通过）—— 判成立，已改**。
   `Path.rglob` 在遍历期抑制 `PermissionError`，原来的 `try/except OSError` 只包住 `resolve()`
   与 `read_bytes()`，够不着枚举这一层。改用 `os.walk(scan_root, onerror=_on_walk_error)`，
   回调把失败目录记进 `unchecked`；`followlinks=False`（默认）同时挡住目录符号链接。
   **承重验证做了两层**：
   - **N3b 同根对撞**（`E/negctl-n3b-enum-denied-samefixture-*.txt`）：把 round-1 的旧实现当
     对照体，两版放进内容逐字节相同的两个扫描根（各含 1 个顶层 + 1 个子目录命中样本），
     同一审计钩子条件下跑。旧版 denied → `([], [])`；新版 denied → `([], [1])`；
     **baseline 两边都是 2**（先断言抽取非空，否则「都没命中」无法与「都没扫到」区分）。
   - **N3c 端到端**（`E/negctl-n3c-enum-e2e-*.txt`）：真实 `chmod 000` 子目录 → 门硬红，
     `ERROR tests/`=1、rc=1、「无法检查」与「目录枚举失败」各 2 次。
     做这一层是因为 N3b 只证明函数返回值，不证明门会因此变红。
   - ⚠️ 第一版 N3b（`E/negctl-n3b-enum-denied-20260908T073843.txt`）是**坏的对照**（两版扫描根
     不同，baseline 11 vs 0），我把它留档而不是删掉。

2. **HIGH #2（漏检超出登记 + 措辞越界）—— 判成立，已改**。
   告警文案改为「归属未知：可能来自本 session，也可能来自任何别的进程 ⇒ 不判红，
   但请核查或重跑，不要直接当成『别人弄的』」，并明说源码门只看字符串常量、
   **不能**证明本树没有写者。docstring 盲区补齐你列的七类。
   另**更正我 round-1 的一处技术不准确**：我原写「f-string 变量段漏网」，
   按你的精度补充，前缀完整的 f-string **会**命中，只有前缀被拆开的才漏。

3. **MEDIUM（符号链接越界读取）—— 判成立，已改**。
   加 `resolved.is_relative_to(scan_root)`，越界进 `unchecked` 报边界不符。
   未普查树内是否实际存在此类链接（已登记为未证明项）。

### 我接受的三处收窄（round-1 你在「作者自述逐条核对」里提的）

- 自述 #1「告警不会升级」：你判「本次存档成立、普遍保证不成立」。已把 `pytest.ini` 加进读取面。
- 自述 #8「nodeid diff 为空」：你判只成立于**红** nodeid 口径。验收单已一律改写「红 nodeid 集」。
- P1 证明力：你指出它是未执行写入的常量 ⇒ 证明的是**源码规则承重**，不是写入归属。已按此措辞。

### 整改后重跑的裁判（全部，未复用 round-1 存档）

N1'（`E/negctl-n1-after-20260908T074442.txt`）、P1 red/green（`E/negctl-p1-*-2026090807412*.txt`
与 `...074420.txt`）、P2（`E/negctl-p2-red-20260908T074140.txt`）、7c①②
（`E/selfprobe-*-2026090807423*.txt` / `...074245.txt`）、N2' 双树并发
（`E/unit-n2p-20260908T074540.txt` + `treeB-probe-n2p-*` + `window-n2p-*`）。

**三端点对照**（我用它替代卡文原写的「N2' rc=0」——目录级带 202 条既有红，rc 恒为 1，
那个期望值不可达；如果你认为这个替代不成立，请直接说）：

| 轮次 | 门 pytest.fail | ERROR tests/ | 环境受干扰 | rc | vs 202 基线 diff |
|---|---|---|---|---|---|
| 开工基线（无干扰） | 0 | 29 | 0 | 1 | 空 |
| N2 修前（+树B） | 1 | 30 | 0 | 1 | 多一条 `>` |
| N2' 修后 r2（+树B） | 0 | 29 | 1 | 1 | 空 |

## 三、本轮请重点回答的问题（按重要性排序）

1. **HIGH #1 真的修干净了吗？**
   `os.walk(onerror=...)` 之外，还有没有别的路径能让「没检查」被返回成「无违规」？
   例如：`onerror` 回调本身抛异常、`dirnames` 被就地修改、`os.walk` 对某类 I/O 错误
   根本不调用 `onerror`、或者 `unchecked` 在某个分支上被短路掉。
2. **N3b/N3c 这两层验证够不够，有没有假杀 / 假绿？**
   特别是：N3b 用审计钩子拒绝**所有** `os.scandir`，这会不会让「新版记了 unchecked」
   变成一个平凡结论（比如它其实是别的原因红的）？N3c 的 `chmod 000` 在这台机器上
   是否真的构成「枚举被拒」而不是别的失败？
3. **HIGH #2 的措辞收窄到位了吗？**
   现在的告警文案有没有仍然超出证据的地方？盲区清单还缺哪些形态？
4. **MEDIUM 的越界拦截会不会误伤？**
   `is_relative_to` 用的是 `resolve()` 后的路径与 `resolve()` 后的扫描根比较。
   在符号链接、大小写不敏感文件系统、或 `/private/tmp` 这类 macOS 前缀改写下，
   有没有把**合法的树内文件**判成越界（假红）的情形？
5. **两轮之间有没有引入新的回归？**
   `git diff 13a138c9 2c799422 -- backend/tests/unit/conftest.py` 是本轮全部代码改动。
   fixture 是否仍然零副作用、不依赖 cwd、不 import `app.*`？
6. **验收单里我自认的「判据比证据宽」三次同型错误**（§六 第 12 条），
   有没有第四处我还没发现的？

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
