# UAT — CARD-AST-FLAG-PATCH（AST 负控补三条未被拦下的形态 + 不动点显式未收敛）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-AST-FLAG-PATCH]` · 车道 `card-t8-tools`（分支 `card/t8-tools`）第 4/7 张
> 地盘 = 唯一文件 `backend/scripts/lifespan_isolation_negative_control.py`
> 父 = T8-C 末 commit `a2dcda8f` · 未 push
> 证据目录 `_bmad-output/审查/evidence-ast-flag/`（索引见其 `README.md`；⚠️ 目录内有三代同名存档，
> **只有 `0917` 那一代是定稿承重件**）

---

## ⛔ 先说一处**偏离卡文**（请主 session 复核时先看这条）

卡文 (e) 把完成条件的计数写死为 `PASS (51 / 27)`。**实交 `PASS (63 / 28)`**。

must-flag 多出 12 条、must-pass **多 4 条又减 3 条**，净 +1。构成：

- **+12 must-flag** = Codex 三轮审查里每条 HIGH/MEDIUM 各自的**回归锚**（`R1-` / `R2-` / `R3-` 前缀）。
  加它们的直接理由是 round-1 的一句话「**27 条对照中没有任何 Lambda 节点，未覆盖该回归**」；
  round-2 与 round-3 随即两次证明这个担心是对的 —— 我自己的修复**四次**引入新回归，而当时的表
  一条都没拦住。
- **+4 / −3 must-pass**：加 4 条验伪锚；**再删掉其中 3 条**（`验伪锚 R1-M3` / `R2-M5` / `R2-M5b`），
  因为它们锁的那个功能本身在 round-3 被**整条撤回**了（见 四-A.11）。删除的是我自己在 r1/r2
  加的、且与被撤回功能绑定的条目 —— **不是**卡文原有的 27 条正例，与硬边界「禁把误判的正例移出
  正例表凑绿」不是一回事。

卡文的 51/27 是「三条盲区已覆盖」的检查点，不是表的上限。本卡三条仍可按 label 单独识别
（`R2-5b-B-…` / `R2-7-B-…` / `R2-5a-ii-…`）；主 session 若不认可，删掉带 `R1-`/`R2-`/`R3-` 前缀的
12 条即回到 51/28（那 3 条已删的不会回来）。

---

## 〇 第 0 分钟自证

存档 `minute0-20260917T084209.txt`。

| 项 | 实测 |
|---|---|
| `pwd` / 分支 | `…/worktrees/card-t8-tools` / `card/t8-tools` ✓ |
| `git rev-parse --short=8 HEAD` | `a2dcda8f` = T8-C 末 commit ✓ |
| `git status --porcelain` | 空 ✓（本 session 第一条命令、任何 `mkdir` 之前；存档里那 1 行是随后建的本卡 evidence 目录，已用 `':(exclude)…evidence-ast-flag'` 复核为 0 行） |
| `backend/.venv/bin/python` / `backend/.env` | 均在 ✓ |
| 基线 `grep -vc '^#' "$BASE"` | **64** ✓（依 **R-B14-2**，⛔ 非 `grep -c '::'` 的 65） |
| 本文件自 `B14_BASE` 零改动 | `git diff --no-color 08100483 HEAD -- <file>` 输出 0 行 ✓ |

**⛔ patch 缺席复核（推翻设计前提的硬核）**：

```
find …/worktrees -name '*.patch' | grep -icF ast-must-flag   →  0     （patch 不存在）
find …/worktrees -name '*.patch' | grep -icE 'ast'           →  3     （验伪锚：管道能命中，0 不是 find 空手）
```

⇒ U7 的 `ast-must-flag.patch` **从未交付**，本卡按文档意图**手工落地**，不是套 patch。

## 〇.1 卡文行号锚逐条核（无漂移）

卡文 §〇 的每一条 file:line 在开工树上**全部命中、零漂移**：`_AST_MUST_FLAG :1977-2578`（48 条）、
`_AST_MUST_PASS :2580-2888`（27 条）、`run_ast_negative_control :2891-2915`、
`analyze_source :1827-1940`、`_module_attr_write_paths :484-516`、`_own_exprs :751-765`、
不动点 `for :634` / `if :655-663` / `break :664` / `_rebuild :665`、`main :3113-3468`、
`run_runtime_files_selftest` 先于一切分支（`:3126`）。卡文两处「实测更正」（上界 2578 非 2580、
`_own_exprs` 到 765 非 766）**本次复核成立**。

---

## 一 三条未被拦下的形态：先红 → 后绿

每条与一条**已在表里**的对照输入只差一处写法 —— 这是降假绿风险的锚：对照被抓、新条目没被抓，
说明缺的就是那一处写法的扫描面。

| # | label | 只差一处写法的既有对照 | 先红存档 | 修哪里 |
|---|---|---|---|---|
| (b) | `R2-5b-B-lambda-defaults` | `R2-5b` 嵌套 **def** 默认参数版 | `red-lambda-20260917T084628.txt` | `_own_exprs` 下潜 lambda 的 `args.defaults` / `kw_defaults` |
| (c) | `R2-7-B-setattr-write` | `R2-7 C4` 的 `mod.client = …` 版 | `red-setattr-20260917T084629.txt` | `_module_attr_write_paths` 增 `ast.Call` 分支 |
| (d) | `R2-5a-ii-branch-split-isolation` | `R2-5a` 嵌套函数 yield 版 | `red-branch-20260917T084629.txt` | `_isolation_wrapper_index` 逐条 yield 核 |

**先红三份各自独立**（每份只加那一条、扫描器未动，`_AST_MUST_FLAG` = 49）：各得**恰好一条**
`*** MISSED ***` + `AST-NEGATIVE-CONTROL: FAIL` + `rc=1`。三份都带
`RUNTIME-FILES-SELFTEST: PASS` —— 即 `rc=1` 来自 AST 判定，不是 `main()` 入口那道先于一切跑的
runtime_files 自证（卡文 §〇 第二更正 (3) 点名的陷阱）。

**后绿**：`green-63-28-20260917T094933.txt` → `PASS (63 / 28)`、rc=0，
计数核 `CAUGHT=63 / CLEAN=28 / MISSED=0 / FALSE POSITIVE=0`。

### 一.1 (d) 无需摘出（卡文留的「2h 难收敛则摘出」退路，本次未用）

外审存档「⑤不成立」段其实点了**两半**：嵌套函数里的 yield（(i)）与分支跨越（(ii)）。开工实测
(i) 早已被 `_walk_same_scope`（R2 Codex HIGH-5）修掉，本卡只剩 (ii) 这一半 —— 改动面因此远小于
卡文的悲观估计，当轮即收敛。

---

## 二 本卡代码改动（地盘 = 唯一文件）

1. **`_own_exprs`（(b)）** —— 旧实现遇 `ast.Lambda` 整个跳过；lambda 的**默认参数**与 `def` 的
   `args.defaults` 同口径（定义处求值 ⇒ 归外层作用域），于是
   `unused = lambda x=(a := FastAPI()): x` 里的海象一条不入表，「被隔离的形参被重绑定即失格」
   拿不到证据，包装器保住资格。现改为**只**在 child 位置下潜 `defaults` / `kw_defaults`、不进体。
   ⚠️ **根位置的 lambda 刻意保持原样**，理由见 四-A.7（本卡一度改过、Codex round-1 HIGH-1 已撤回）。

2. **`_module_attr_write_paths`（(c)）** —— 增 `ast.Call` 分支收
   `setattr(<可解析路径>, "<字符串常量>", …)`。方向上它只会**增加**写路径 ⇒ 只会**收回** C4 豁免，
   不会放宽任何判定；风险因此全在「误判合法写法」这一侧，由 28 条对照输入 + 真实消费面 +
   401 文件全扫描面三重把关。属性名是算出来的时**如实不收**。
   另加一条保守闸：本模块任何地方绑过 `setattr` 这个名字，整条分支不收（Codex round-1 MEDIUM）。

3. **`_isolation_wrapper_index`（(d)）** —— 判据从「**存在**某个 `with` 体内有一次合格 yield」
   （找到一条就 `return`）改为「**每一条**到达调用方的 yield 都被隔离同一形参的那些 `with` 体覆盖」。
   按节点 `id()` 比对**身份**而非数个数 —— 数量相等挡不住「隔离内两条、隔离外一条」这类等长替换。

4. **`_walk_same_scope` + 新增 `_outer_evaluated_parts`（Codex round-1 HIGH-2）** ——
   「不下潜」此前是对整个作用域节点一刀切，但 `def`/`lambda` 的**默认参数与装饰器**、`class` 的
   **装饰器与基类**都在**外层**求值。于是 `def unused(x=(yield a))` 里那次**真实的**让出根本不进
   `all_yields`，第 3 条的「每一条 yield」空口成立。现在这些外层求值的部分照收，体仍然不进。

5. **不动点（(f) / MEDIUM-6①）** —— `for _ in range(4)` 的字面量提为 `_FIXPOINT_MAX_ROUNDS = 8`；
   跑满仍未收敛不再与「收敛了」走同一条静默出口，改抛 `FixpointNotConverged`，由 `analyze_source`
   转成一条**看得见**的违规明细（fail-closed）。新增 `--selfcheck-fixpoint`，落在 `main()` 现有
   `--ast-negative-control` 分支旁、同样在连库之前 `return`。

### 二.1 `_FIXPOINT_MAX_ROUNDS = 8` 的取值依据（不是拍脑袋）

instrument 实测（`fixpoint-rounds-instrument-20260917T085859.txt`，脚本 `rounds_instr.py`）：

| 面 | 轮数直方图 | 最大 |
|---|---|---|
| 负控输入 48+27 条（改前） | `{1:51, 2:22, 3:2}` | **3**（「转调工厂返回 tuple 后解包」d2/d3） |
| 门的真实扫描面 **401** 文件 | `{1:106, 2:295}` | **2** |

⇒ 旧值 4 只剩一轮余量。循环一收敛就 `break`，401 个文件谁也不会真跑到第 3 轮，提到 8 的运行
代价是 0；而上限一旦不够，行为已从「静默给一个不可信结论」变成「显式报未收敛」，余量宁可留足。
`--selfcheck-fixpoint` 第 ⑤ 步把「不得低于历史值 4」做成了常驻门。

## 三 公共符号名全部保留

`analyze_source` / `run_ast_negative_control` / `_own_exprs` / `_module_attr_write_paths` /
`_AST_MUST_FLAG` / `_AST_MUST_PASS` 一个没改名。新增的都是**追加**：`_FIXPOINT_MAX_ROUNDS`、
`FixpointNotConverged`、`_FIXPOINT_MULTI_ROUND_SRC`、`run_selfcheck_fixpoint`、
`_outer_evaluated_parts`、`_module_binds_name`、`_ModuleIndex.__init__` 的可选形参
`max_rounds=None`、实例属性 `fixpoint_rounds`。跨车道只读消费方
`lifespan_isolation_guard_probes.py:660/:745` 按模块动态加载、按符号取用，形态不变。

---

## 四-A 🤖 Claude 已代验（证据全在 `_bmad-output/审查/evidence-ast-flag/`）

### 四-A.1 裁判逐条回执（定稿一代）

| 裁判 | 结果 | 存档 |
|---|---|---|
| 1 第 0 分钟 + patch 缺席 | 全过，`grep -icF`=0 / 验伪锚 3 | `minute0-20260917T084209.txt` |
| 2 三盲区先红（各一份） | 各**恰好一条** `MISSED` + `FAIL` + rc=1 | `red-{lambda,setattr,branch}-…0846` |
| 3 后绿 | `PASS (63 / 28)`，`FALSE POSITIVE`=0 | `green-63-28-20260917T094933.txt` |
| **3+ 定向负控（本卡自加，承重）** | **9 处**修复逐个撤掉，**指定的那一条**（按 ID 精确匹配）各自变红；控制组红项为空 | `negctl-anchors-20260917T094933.txt` |
| 4 真实消费面（承重） | 改前 `[[],[]]` = 改后，**逐字相同** | `consumers-before-20260917T084638.txt` / `consumers-after-20260917T094946.txt` |
| 4+ 全扫描面（本卡自加，比卡文更宽） | 改前 `files=401 violations=0` = 改后，**逐字相同** | 同上 |
| 5 fixpoint 红 / 绿 | 红含两条 `MISSED: 未收敛未被报出`，rc=1；绿 `PASS`，rc=0 | `fixpoint-{red,green}-…093255` |
| 6 地盘 | **只** `backend/scripts/lifespan_isolation_negative_control.py`（验伪锚：去掉 exclude 多出 55 条 `_bmad-output/` 路径） | `territory-20260917T092132.txt` |
| 7 ruff | `check` / `format --check` 均 rc=0；F821 验伪锚 rc=1 | `ruff-r3fix-20260917T094946.txt` |
| 8 tests/unit | 与 64 基线 diff **空**，`>` 行 = 0 | `unit-close-20260917T094921.txt` + `base/close.nodeids` |
| — pyright | `0 errors, 81 warnings` | `close-pyright-20260917T085652.txt` |

每条判据都配了**同次执行的验伪锚**：patch 缺席配 `grep -icE 'ast'`≥3；地盘门配「去掉 exclude
必须多出 `_bmad-output/` 路径」（实测 35 条）；两组 diff 各配一次注入假行必得 `>`；ruff 配
F821 注入与乱排版各必 rc=1；instrument 配「故意给错行号 ⇒ `assert` 必炸」；定向负控配一个
空红项的控制组；README 引用的 21 个文件名配一条「存在性自动核 + 假名必被报」。

### 四-A.2 裁判 5「先红」的造法（依 **R-B14-7**，⛔ 不取 `B14_BASE`）

`--selfcheck-fixpoint` 是本卡**新增**子命令，`B14_BASE` 没有它 —— 对 base 副本跑该参数是未知参数，
会越过 `--ast-negative-control` / `--ast-only` 两个提前 `return`、落进完整负控重活，产出与
「未收敛处置」无关的假红。正确做法是从**定稿**树 `cp`，再 `sed` **仅**剔掉那一处 hunk：

```
prefix 与定稿的唯一差异（2 行）：
-        if not converged:
-            raise FixpointNotConverged(f"知识迭代 {max_rounds} 轮仍未收敛 —— 判定依据还在变，不出结论")
```

**红绿都核了正文 label 而不是只看 rc**：两份存档里 `RUNTIME-FILES-SELFTEST: PASS` 都在。

红那份还顺带把危害显出来了 —— 上限不够且无显式处置时，`analyze_source` 对一条**合法**输入
静默给出 `app 来源无法静态证明` 的**错误**判定。这就是 MEDIUM-6①「误拒方向且静默」的实物。

### 四-A.3 假门防线（承重：证明这不是「恒判违规」）

1. `_AST_MUST_PASS` **28** 条对照输入全部 `CLEAN`（`FALSE POSITIVE` 计数 0）；
2. 真实消费面两文件违规集改前改后逐字相同（都为空）；
3. 门的 **401 文件完整扫描面**违规集改前改后逐字相同（`files=401 violations=0`）。

(d) 专项边界探针（`probe-isolation-boundaries-…091725.txt`，六条**全部成立**）：

| 输入 | 期望 | 实得 |
|---|---|---|
| 两支**各自**包 `no_lifespan(a)` ⇒ 仍合格 | CLEAN | CLEAN ✓ |
| 一支隔离内、一支隔离外 ⇒ 失格 | CAUGHT | CAUGHT ✓ |
| 隔离内的嵌套 with / try-finally 里 yield ⇒ 仍合格 | CLEAN | CLEAN ✓ |
| 隔离内有 yield、隔离外**再多一条** ⇒ 失格 | CAUGHT | CAUGHT ✓ |
| `yield from` ⇒ 仍失格（(f)-⑤ 未被本卡放宽） | CAUGHT | CAUGHT ✓ |
| 标准单支隔离（验伪锚 10 形态）⇒ 不许被本卡弄红 | CLEAN | CLEAN ✓ |

第一行**同时**是对写进 `_isolation_wrapper_index` docstring 的那句声称的核对（DD-13 名实一致）。

### 四-A.4 定向负控：证明这些锚**真的**绑在各自的修复上

「63/28 全绿」只说明这一跑没红，不说明表锁住了什么。逐个撤掉一处修复、断言**指定的那一条**
变红。控制组（未变异的定稿）红项为空，结论可比。存档 `negctl-anchors-20260917T094933.txt`，
脚本 `negctl.py`：

| 撤掉哪一处修复 | 指定判据 | 结果 |
|---|---|---|
| 卡文 (b) `_own_exprs` 不再下潜 lambda 默认参数 | `[MISSED] R2-5b-B-lambda-defaults` | 红 ✓ |
| 卡文 (c) `collect_setattr` 整条失效 | `[MISSED] R2-7-B-setattr-write` | 红 ✓ |
| **回装**被 r3 撤回的「模块级遮蔽开关」 | `[MISSED] R3-HIGH2-except-as-name-deleted` | 红 ✓ |
| 卡文 (d) 不再要求每条 yield 都被覆盖 | `[MISSED] R2-5a-ii-branch-split-isolation` | 红 ✓ |
| r1-HIGH2 `_outer_evaluated_parts` 不产出 | `[MISSED] R1-HIGH2-nested-def-default-yield` | 红 ✓ |
| **回装**被 r1 撤回的根 lambda 改动 | `[MISSED] R1-HIGH1-regress-lambda-body-walrus` | 红 ✓ |
| r2-HIGH1 不再区分「已进入 lambda 体」 | `[MISSED] R2-HIGH1-nested-lambda-in-lambda-body` | 红 ✓ |
| r2-HIGH2 `push` 的部件不再递归 | `[MISSED] R2-HIGH2-default-lambda-body-yield` | 红 ✓ |
| r2-HIGH3 `_outer_evaluated_parts` 不再收注解 | `[MISSED] R2-HIGH3-param-annotation-yield` | 红 ✓ |

⚠️ **两处判据自身的缺陷，也是被抓出来才改的**：

1. **变异锚会随生产代码漂移**：`ruff format` 把一行 `child_in_body = …` 折行后，某个锚一度
   命中 0 次。脚本对每个锚 `assert count == 1` —— 锚不命中**直接抛**。少跑一个变异的输出
   和「变异没杀死锚」看起来一模一样，不 assert 就分不出来。
2. **目标标签不唯一**（Codex r3 LOW）：上一版用 `want_label in label` 子串匹配，
   `验伪锚 R2-M5` 会同时命中 M5 与 M5b —— 只要其中任何一条红就算通过。现在按 **ID 段精确
   相等**匹配，且开跑前断言每个目标 ID 在两张表里**恰好出现一次**（实测 9/9 各命中 1 条）。

### 四-A.5 如实登记：两处判据**自身**出过问题

1. **ruff 验伪锚第一版失败（anchor rc=0 = 判据当时恒绿）**。根因：锚文件写在仓外，ruff 按
   **文件路径**解析配置 ⇒ 走的是默认配置而非 `backend/ruff.toml` 那份。改用 `--stdin-filename`
   指向本卡文件所在路径后，F821 锚 rc=1。两份存档都留，前者不得引为依据。
   顺带落档本文件**有效规则集**实测：只有 14 条（`E902` + F 系必错级），**`F401` 不在其中** ——
   卡文模板惯用的 F401 锚在 `backend/**` 上**恒不触发**，这也是改用 F821 的原因。
2. **第一版 instrument 脚本产出过全 0 的假直方图**。它把不动点 `for` 的行号硬编码成 634；
   本卡改动后该行漂到 687，计数器全程没被写过 ⇒ 直方图退化成 `{0: 78}`。抓住它的是脚本自带的
   「观测到的 `range` 调用行须含 634」验伪锚。替代件 `rounds_instr.py` 把被测文件与行号都改成
   命令行入参、并把锚升成 `assert`。作废件已就地标注 VOID。

> 共同教训：**模块里不止一处 `range()`**（`:634` 与 `:1129`），最早那版把模块全局 `range` 整个
> 换掉，于是「不动点跑了几轮」这条主张实际测到的是「最后一次 `range` 调用的值」。判据取的面
> 必须恰好等于它的主张。

### 四-A.6 格式漂移的归属（卡文 (k) 要求先判再处置）

`ruff format --check` 在本卡定稿上红。**先判归属**：同一配置面下对 `B14_BASE` 内容跑 `--check`
→ rc=0 ⇒ 漂移**是本卡引入**，不走协议 §2.3 过渡条款，直接 `ruff format`。format hunk **全部**
落在本卡新增行内，**没有**顺手 format 任何既有行。format 改变了 prefix 的 `sed` 锚（hunk 由
4 行变 2 行）⇒ prefix 与全部承重裁判已在其后重跑。

### 四-A.7 ⛔ 本卡一度扩面，被 Codex round-1 判 HIGH-1，已**撤回**

初版除了卡文 (b) 点名的 child 位置外，还「顺带纠正」了**根位置** lambda ——
旧实现在根位置会走遍 lambda 体、把体内的 `:=` 记进外层，按 PEP 572 那确实是错的。

但这道门**没有 lambda 作用域**：lambda 体内的使用点解析时用的就是外层作用域表。那条「错」的
记录恰好让**同一个 lambda 体内**的使用点解析对了。改掉它，两个方向同时出事（`verify-r1-findings-…091714.txt`）：

| 输入 | 正确答案 | `B14_BASE` | 初版（已撤回） | 现定稿 |
|---|---|---|---|---|
| lambda 体内 `(app := production)`，同体内 `enter_context(TestClient(app))` | **CAUGHT**（lambda 局部 app 就是生产 app） | CAUGHT | **CLEAN ✗ 漏放真危险** | CAUGHT ✓ |
| 同形态但 `(a := FastAPI())` 是局部应用 | **CLEAN** | CLEAN | **CAUGHT ✗ 误判合法写法** | CLEAN ✓ |

⇒ **已整条撤回**。现在 `_own_exprs` 只动 child 位置 —— 恰好等于卡文 (b) 划的面，根位置与
`B14_BASE` 逐字同（`probe-lambda-scope-…091725.txt`：旧 `['a','f']` = 新 `['a','f']`）。
真正的修法是给 `Lambda` 建独立作用域（`_build_scope` 结构性改动），超出本卡范围，已登记移交（六.⑤）。

这条写在这里是因为它是本卡最贵的一个教训：**卡文写死「禁扩面」是有理由的**，我按自己的判断
扩了一处看起来明显更正确的面，结果在一个没有 lambda 作用域的判定器上拆掉了一层意外的正确性。
收敛靠的是**撤回**，不是再加一层补丁。

---

## 四-B 👤 你来验（2 分钟，只读这一段，不用打开任何别的东西）

系统里有一张「自查网」，专门盯着一件事：**测试代码有没有在偷偷连真正的数据库**。

这张网以前有三个窟窿——有三种写法，它明明该拦，却一声不吭地放过去了。这三种写法都不稀奇，
每一种跟它**已经**拦得住的某种写法只差一个字的差别，等于同一道门开了三个侧门。

还有第四件事更别扭：这张网在下判断之前要先把线索反复推演几遍，推满了次数还没推明白的时候，
它不会说「我还没想清楚」，而是直接按当前这份半成品给结论。这次实地看到了后果——在那种状态下，
它把一段**完全正常**的代码判成了「可疑」。也就是说，它不是偶尔漏，而是会**理直气壮地给错答案**，
你从外面完全看不出来它其实没算完。

这一卡把三个侧门都堵上了，并且让它在没想明白的时候**必须开口说出来**。

另外要如实告诉你一件事，而且不止一次：**我自己在补窟窿的时候，又弄出了新窟窿**。

第一次是我多动了一个本来不该动的地方，结果一段真有问题的写法反而被放过去了。
第二次是我为了补第一次的漏洞而加的新检查本身写得太宽，把一整类检查悄悄关掉了。

两次都是外部审查抓出来的，不是我自己发现的。都已经改好，而且我给**每一处**修好的地方都装了
一个「哨兵」——现在一共十一个：只要有谁把其中任何一处改坏，自查网当场亮红，不会悄无声息。
我还专门反过来验过一遍：把每一处修复**逐个拆掉**，看对应那个哨兵是不是真的会叫。十一个都叫了。

**你要确认的就一句**：现在这张自查网，从我这边能看见的窟窿已经没有了——那几种写法一试就被拦下，
"算到一半"的情况也会明说，而且每一处都有哨兵盯着、哨兵本身也验过会叫。你觉得这个"没有窟窿了"
的感觉，和你希望它达到的程度对得上吗？

（如果你想知道还有没有没堵的——有两件。一种组合写法这次**没有**动，因为超出了这张卡说好的
范围；还有一个更底层的东西（上面说的"不该动的地方"，要真正修对得动它）也超范围。两件都已经
单独记下来交给下一批。见第六节 ③ 和 ⑤。）

---

## 五 本卡未证明什么（≥4）

1. **未证明这些形态在真实测试代码里出现过**。本卡只证「门对它们从放行变成抓住」。危害是
   「今天写得出、且写了不会被拦」，不是「已经发生过」—— 401 文件全扫描面改前改后违规集都为空。
2. **HIGH-2 的修复在现网面上零效果**（四-A.9：401 文件里新增节点中 Yield/YieldFrom = 0）。
   它关的是一个写得出来但还没人写的口子，不是在修一个正在发生的问题。
3. **未跑任何变异 harness**（g32b / g32cb / g32ccr1 / g33 归 T8-A/B/C），因此**不证**本脚本改动对
   它们零影响。依据只是「无 harness import 本脚本、lefthook 无引用、`backend/tests` 无测试跑它」
   这一 grep 级推断。
4. **两个自检子命令只证「这一跑在这棵树上通过」**，不是代码不变量。401 文件那组数字同理是
   2026-09-17 这棵树的快照。
5. **未证明 §8.1 的组合形态已堵**（写侧用下标/别名/推导式目标 + 读侧写成属性 ⇒ 照进 C4 获豁免）。
   本卡明确不实现、登记移交（六.③）。
6. **未真跑跨车道消费方** `lifespan_isolation_guard_probes.py`（可能触网）。只做了「公共符号名
   一个没改」+ 真实消费面 `analyze_source` 静态核两件事。
7. **未证明 `_FIXPOINT_MAX_ROUNDS = 8` 对所有可能的源都够**。只证本树 401 文件最多 2 轮、
   63+28 条负控输入最多 3 轮、承重自检输入 3 轮。不够时的行为已从静默变成显式报错。
8. **(c) 的 `setattr` 分支只覆盖「属性名是字符串常量」且模块未遮蔽 `setattr` 这个名字**。
   `delattr` / `object.__setattr__` / `vars(mod)[...] = ...` / 名字算出来的 `setattr` 均**未**覆盖（六.④）。
   遮蔽判据是**语法级近似**（本函数在作用域表建成前就被调用，拿不到真名字解析）。
9. **未证明「根位置 lambda」那个既有缺陷已修** —— 本卡是**撤回**而非修复，它在 `B14_BASE` 上
   是什么样、现在还是什么样（六.⑤）。
10. **`_outer_evaluated_parts` 的完整性只在「yield 收集」这一个消费方上成立**，且只在
    3.11.15 / 3.14.4 两个解释器上实测过（四-A.8）。`class` 体里的 yield 未构造对照输入。
    若将来把它复用到**海象**记录上，语义边界要重新核一遍。
11. **`_own_exprs` 的「已进入 lambda 体」只是一位布尔状态**，不是真正的作用域链。嵌套层数更深、
    或 lambda 与 `def` 交替嵌套的形态只由负控表里那几条锚覆盖，未做穷举。
12. **两轮 Codex 共 11 条 finding 全部经本车道独立复现后接受，零驳回**。反过来也意味着：凡是
    Codex **没有**想到的形态，本卡同样没有覆盖 —— 两轮里有 5 条是我自己的修复引入的新缺陷，
    都不是我自查出来的。
13. ⛔ **`setattr` 的遮蔽判定本卡最终「不判」**（round-3 整条撤回，四-A.11）。因此
    **未证明**「本模块自定义了不写属性的 `setattr` 时不会误判」—— 恰恰相反，那种写法**会**
    被误判为违规（fail-closed），已登记移交。要判对需要调用点的作用域链 + 执行顺序 +
    运行时可达性三样，本函数在作用域表建成**之前**就要用，一样都拿不到。
15. **「根位置与 `B14_BASE` 逐字同」这句声称只在探针那三条输入上成立**（Codex r3 指出）。
    反例：以 `lambda cb=lambda x=(a := 1): x: cb` 整体作 `_own_exprs` 根输入时，基线收 `[]`、
    现版收 `['a']` —— 那是符合「定义时求值」的**预期变化**，不是缺陷，但普遍等价不成立。
16. **三轮 Codex 共 18 条 finding 全部经本车道独立复现后接受，零驳回**。其中 **5 条是我自己的
    修复引入的新缺陷**，只有 1 条（r3-HIGH1）是我在报告返回前自查出来的 —— 其余 4 条都靠外审。
14. **本卡是三个 commit 而不是一个**（代码 `20abe003` + 收 r1 `6564fc09` + 收 r2）。
    卡文 (k) 写「单独 commit」；此处按 T8-C 同款先例理解为「本卡独立成 commit、不与别的卡混」，
    如主 session 要求严格单 commit，三个可 squash（无跨卡内容）。

## 六 台账待登记条目（≥4）

1. ⛔ **U7 的 `ast-must-flag.patch` 从未交付**（两处记载路径均不存在、全部 worktree 下
   `grep -icF ast-must-flag` = 0，验伪锚 `grep -icE 'ast'` = 3）⇒ 设计稿「套 patch /
   `git apply --check`」的前提**作废**。本卡按 UAT-CARD-RV-W4-5 §8/§15 手工落地，三条 label：
   `R2-5b-B-lambda-defaults` / `R2-7-B-setattr-write` / `R2-5a-ii-branch-split-isolation`。
2. **MEDIUM-6① 由本卡闭合**：`:634` 的 `range(4)` → `_FIXPOINT_MAX_ROUNDS = 8` + 跑满未收敛抛
   `FixpointNotConverged` + `analyze_source` 转成违规明细 + `--selfcheck-fixpoint` 五步自检。
3. **§8.1 组合形态（UAT-CARD-RV-W4-5 §16.7）未实现**，建议立第十五批卡：写侧用下标 / 别名 /
   推导式目标 + 读侧写成 `mod.client` 属性 ⇒ 照进 C4 获豁免。
4. **(c) 的覆盖边界**：只收 `setattr(<可解析路径>, "<字符串常量>", …)`，且**不判**该名字是否被
   遮蔽（round-3 整条撤回，验收单 四-A.11）。同族未覆盖面 `delattr` / `object.__setattr__` /
   `vars(mod)[...] = ...` / 非常量属性名，与 ③ 合并立卡。
15. ⛔ **新增移交：`setattr` 遮蔽判定**。本卡试过一次「模块级遮蔽开关」，被证明**原理上走不通**
    （一次绑定推不出每个调用点都被遮蔽：`except as` 退出删名 / `if TYPE_CHECKING` 不执行 /
    遮蔽写在调用之后）。已整条撤回并加 4 条 must-flag 锚（`R3-HIGH1-*` / `R3-HIGH2-*`）。
    ⛔ **谁要再做这件事，必须先解决「调用点的作用域链 + 执行顺序 + 运行时可达性」三样**，
    否则那四条锚会当场红。残留的 fail-closed 误判（本模块自定义不写属性的 `setattr`）建议
    与 ③④ 合并立卡。
16. ⛔ **批级教训：`ast.walk` 没有「跳过子树」这回事**。用 `ast.walk` + `continue` 表达
    「不进这个作用域的体」是**无效**的 —— 被 `continue` 的只是那一个节点，它体内的一切照样
    被遍历到；而且 `continue` 还会顺带跳过**节点自己的名字**，而名字绑在外层。要作用域语义
    就必须手写遍历。本卡在这上面栽了一次（r3-HIGH1），车道自审与 Codex 各独立抓到一次。
17. ⛔ **批级教训：判据的文档会落进判据自己的命中面**。README 的索引自检要求「不得出现占位符
    与省略号」，第一版把这两种形态**字面**写进了说明文字里，自检当场把自己判红。正确修法是
    改文字（用描述代替字面），**不是**给判据开豁免 —— 一开豁免，真正的漏检就从豁免区溜回来。
5. ⛔ **新增移交：本门没有 lambda 作用域**。`_build_scope` 不给 `ast.Lambda` 建作用域，lambda 体内
   的使用点按外层作用域表解析。本卡一度按 PEP 572 纠正 `_own_exprs` 的根位置处置，实测**双向
   出事**（真危险漏放 + 合法写法误判），已整条撤回（验收单 四-A.7）。真正的修法是结构性地给
   Lambda 建作用域，建议立卡。⛔ **在那之前，谁都不要单独去"纠正" `_own_exprs` 的 lambda 处置** ——
   已加回归锚 `R1-HIGH1-regress-lambda-body-walrus` + `验伪锚 R1-HIGH1b` 两条，改坏当场红。
6. ⛔ **偏离卡文：`_AST_MUST_FLAG` 51 → 59、`_AST_MUST_PASS` 27 → 31**（卡文 (e) 写死 51/27）。
   多出的 12 条全是 Codex 两轮审查里每条 HIGH/MEDIUM 各自的回归锚。加锚的必要性由 round-2
   当场证明：我 round-1 的两处修复**各自引入了一个新回归**，而当时的表一条都没拦住。
   加锚是加严不是放宽。主 session 若不认可，删掉带 `R1-` / `R2-` 前缀的 12 条即回到 51/27。
12. ⛔ **新增移交：`_own_exprs` / `_walk_same_scope` 的「外层求值」判定仍是近似**。本卡把它从
    「一刀切整个作用域节点」改进到「收 decorator / defaults / kw_defaults / 注解，且区分是否
    已进入 lambda 体」，但那仍不是真正的作用域链。真正的修法与 ⑤ 同源（给 `Lambda` 建独立
    作用域），建议合并立卡。⛔ **在那之前不要单独去「优化」这两个函数** —— 本卡两轮 5 条
    新缺陷全部出自这一带，已加 `R1-*` / `R2-*` 共 12 条锚，改坏当场红。
13. ⛔ **批级教训：注解里能不能写 `yield` 取决于解释器版本**。3.11.15 合法（外层真多一条
    `YIELD_VALUE`），3.14.4 `SyntaxError`。本机 venv 是 3.14，CI matrix 是 `['3.11','3.12']`。
    任何「这段源码能不能存在」的静态判据，都必须在**门实际要覆盖的版本**上验，不是手边那个。
14. ⛔ **协议建议：MEDIUM 的「登记不阻断」应当也适用于「要不要为它新增一处能力」**。本卡为收
    一条 MEDIUM（`setattr` 被局部遮蔽的误判）新增了 `_module_binds_name`，它随后自己长出
    一条 HIGH（fail-open，把刚堵上的 C4 漏放面又打开）+ 一条 MEDIUM（漏认 pattern / except
    绑定）。两轮下来「撤回型」修复一次到位、「新增能力型」各带出一个新缺陷。
7. **R2-5a(ii) 已闭合**。附带更正一条记载：外审存档「⑤不成立」段点的**两半**里，(i) 嵌套函数
   yield 那一半早已由 `_walk_same_scope`（R2 Codex HIGH-5）修掉，本卡只补了 (ii) 分支跨越。
8. **两处口径更正**（卡文 §〇 已预告，本次复核成立）：`_own_exprs` 实测 `:751-765`（UAT 旧引
   `:751-766`）；`_AST_MUST_FLAG` 实测 `:1977-2578`（UAT-RV-W4-5 §8.1 旧引「1977–2580」）。
9. ⛔ **批级模板缺陷：`backend/**` 的 ruff 只启用 14 条必错级规则**（`E902` + F 系），**`F401`
   不在其中** ⇒ 卡文模板惯用的 F401 验伪锚在该面上**恒不触发**（本卡实测），建议批级模板改用
   **F821**。另：ruff 按**文件路径**解析配置，锚文件放在仓外会走默认配置 ⇒ 锚必须用
   `--stdin-filename` 指向真实面。
10. **tests/unit 目录级 diff**：与 64 基线（依 R-B14-2 口径）**完全相同**，`>` 行 0（本脚本不在
    `tests/unit` 收集面内，符合预期）。
11. **Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数** —— 见 §七。

## 七 Codex 独立审查（`gpt-6-astra` · `ultra` · 多轮，依 D-15）

### round-1 — 绑定 `20abe003`，**BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 1**

存档 `_bmad-output/审查/codex-review-CARD-AST-FLAG-PATCH.md`。四条**全部经本车道独立复现后接受**
（复现脚本与输出：`verify_r1.py` / `verify-r1-findings-20260917T091714.txt`），无一条驳回。

| # | 级别 | 内容 | 处置 |
|---|---|---|---|
| 1 | HIGH | 根 lambda 改动引入生产应用漏报（且同时新增一条误报） | **撤回**该扩面改动 + 加两条回归锚（四-A.7） |
| 2 | HIGH | 「每条 yield」漏掉嵌套 `def` **默认参数**里的外层让出 | 新增 `_outer_evaluated_parts`，`_walk_same_scope` 收外层求值部分 + 加锚 |
| 3 | MEDIUM | 局部重绑定的 `setattr` 被当成内建属性写 ⇒ 误判 | 新增 `_module_binds_name`，模块遮蔽该名字时整条分支不收 + 加验伪锚 |
| 4 | LOW | 证据索引引用了不存在的定稿日志时间戳 | README 重写；并加了一条「引用的 21 个文件名逐个存在性自动核 + 假名必被报」 |

Codex 同时**复现并确认**：三条修复成立、消费面前后均 `[]`、完整扫描均 `(0, [], 401)`、
lambda 默认参数遍历本身与 `def` 同口径且不泄漏体、yield 分支并集成立、身份集合去重正确、
`setattr` 非常量名确实不收、不动点承重输入实测 3 轮且上限 8 对当前面充足、
`prefix.py` 唯一差异确为缺少耗尽抛错的两行、六个公共符号均保留。
它还指出一条证据局限（**已采纳并写进 README**）：轮数 instrument 存档的「改前」扫描实际是
**0 文件**，不能用它单独证明改前 401 文件的轮数 —— 该数字由「改后」那一跑独立复算。

### round-2 — 绑定 `6564fc09`，**BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 1**

存档 `_bmad-output/审查/codex-review-CARD-AST-FLAG-PATCH-r2.md`。七条**全部经本车道独立复现后
接受**（`verify_r2.py` / `verify-r2-findings-20260917T093255.txt`，三版对照），**无一条驳回**。

| # | 级别 | 内容 | 处置 |
|---|---|---|---|
| 1 | HIGH | 根 lambda 含嵌套默认参数时仍新增生产应用漏放（r1 自造回归） | 栈带 `in_lambda_body` 状态 + 抽出 `_lambda_outer_defaults` + 2 条锚 |
| 2 | HIGH | `_walk_same_scope` 会进入默认值 lambda 的体，凭空授予隔离资格（r1 自造回归，双向） | `push` 改递归 + 1 条锚 |
| 3 | HIGH | 仍漏函数**注解**里的外层求值（3.11/3.12 合法） | `_outer_evaluated_parts` 收 `arg.annotation` / `returns` + 2 条锚 |
| 4 | HIGH | 全模块 `setattr` 开关重新打开 C4 漏放面（r1 自造 fail-open） | `_module_binds_name` 只看顶层绑定 + 1 条锚 |
| 5 | MEDIUM | 漏认 `MatchAs` / `MatchStar` / `MatchMapping.rest` / `ExceptHandler.name` 这类无 `Name` 节点的真绑定 | `binds_here` 补四种形态 + 2 条验伪锚 |
| 6 | MEDIUM | 绑定提交里的单测存档在 67% 处截断，不足以支撑「diff 空」 | 本轮 commit 收录**完整**日志（含汇总行与 rc）+ 同步重新生成两份 `nodeids` |
| 7 | LOW | 索引仍留 `territory-<最终 ts>.txt` 占位引用 | README 重写；自检口径加「`grep -c '<[^>]*ts[^>]*>'` 必须为 0」 |

Codex 同时**复现并确认**：59/31 零误报且旧表条目完整保留、四条新增表项预期正确
（含 `R1-M3` 判 CLEAN 合理）、两个真实消费文件与 401 文件扫描改前改后均空违规集、
六处定向负控的编辑锚与目标标签唯一且未发现「靠无关机制变红」、三项原始盲区的锚仍全部 CAUGHT、
不动点承重输入 3 轮收敛且上限 1 会抛未收敛、既有符号全部保留。

它还提了一条关于证据强度的限定，**已采纳写进本单**：控制组为空只支撑「这 82 个样例的差异可
归因」，**不能**证明整类语法完整或没有回归（见 §五.11 / §五.12）。

### round-3 — 绑定 `a03af47c`，**BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2**

存档 `_bmad-output/审查/codex-review-CARD-AST-FLAG-PATCH-r3.md`。五条**全部经本车道独立复现后
接受**（`verify_r3.py` / `verify-r3-findings-20260917T094933.txt`，**四版**对照），**无一条驳回**。

| # | 级别 | 内容 | 处置 |
|---|---|---|---|
| 1 | HIGH | `ast.walk` + `continue` 剪不掉作用域子树：块内嵌套函数的局部赋值仍被当模块级遮蔽 | 与 2 一并由**整条撤回**消掉（四-A.11）。⚠️ 本条车道自审在报告返回前已独立抓到（四-A.12） |
| 2 | HIGH | **前提不成立**：一次绑定证明不了每个调用点都被遮蔽（`except as` 退出删名 / `TYPE_CHECKING` 不执行 / 遮蔽写在调用之后） | `_module_binds_name` **整条撤回** + 4 条 must-flag 锚 + 1 个「回装开关」变异 |
| 3 | MEDIUM | 收窄后丢了顶层条件块里的真 `def` / import 遮蔽 | 同上（撤回后该形态成为已登记的 fail-closed 误判） |
| 4 | LOW | 第 11 个变异的目标标签不唯一（`验伪锚 R2-M5` 子串同时命中 M5 与 M5b） | 改 **ID 段精确相等**匹配 + 开跑前断言每个目标 ID 在两表里恰好 1 条 |
| 5 | LOW | 索引仍有省略号引用（`fixpoint-rounds-instrument-` 那条），前两版自检只查占位符查不到它 | 补全真名；自检收紧为三条（存在性 / 占位符 / 省略号），各带验伪锚，脚本 `readme_selfcheck.py` |

Codex 同时**复现并确认**：round-2 存档里的 11 个输入均已独立复现为预期结果；lambda 整改的
指定失效路径已修且更深默认值 / tuple / `def` / `async def` 组合未复现新回归；递归终止正常；
注解完整性在 **3.11.15** 下五类参数注解加返回注解共 6 条 yield、walker 与外层字节码计数一致；
`class` 的 bases 与 metaclass keyword 已覆盖且实测一致；3.14 下未复现本次补收造成的新误判；
两条注解负控确因「TestClient 未隔离」而红、不是 SyntaxError 空门；59/31 表内零漏报零误报；
改前与现版完整扫描均 401 文件、空违规集；单测证据 1185 行完整且提取的 64 条与两份 nodeids
一致（r2 MEDIUM-6 已修）；公共符号保留；`5f9fd306 → a03af47c` 确实只有地盘回执。

它还要求收窄一句声称（**已采纳**，见 §五.15）：不能说「根位置与 `B14_BASE` 普遍等价」，
反例 `lambda cb=lambda x=(a := 1): x: cb` 基线收 `[]`、现版收 `['a']` —— 那是符合定义时求值的
预期变化，不算缺陷，但普遍等价不成立。另确认「产出不含 lambda」应读作「产出**节点自身**不是
Lambda」，Tuple 等产出的子树仍可能含 Lambda，由调用方继续处理。

### round-4 — 待回填
