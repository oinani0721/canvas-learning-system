# 独立复核请求 — CARD-HYGIENE-conftest（BATCH-2026-09-07-第十三批 / 车道 card-u10-red-a）

请以只读方式独立复核下面这一张卡的改动。你的结论请按第四节格式输出。

---

## 一、背景与最小读取面（**只读这些，不要扩面**）

**树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
**基线 commit**：`da690bf8`（本卡从这里切）。本卡**只改一个文件**：`backend/tests/unit/conftest.py`。

**请只读以下内容**：

1. 本卡改动全文：
   `git -C <树根> diff da690bf8 HEAD -- backend/tests/unit/conftest.py`
2. 改动后的完整文件（读懂上下文用）：
   `<树根>/backend/tests/unit/conftest.py`
3. 全部裁判存档（负控 / 正控 / 目录级 / 双树并发）：
   `<树根>/_bmad-output/审查/evidence-hyg-conftest/` 目录下全部 `*.txt`
4. 本卡承接的上一轮外审意见（只读这两段）：
   `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/codex-review-CARD-TEST-hygiene-vaultinit.md` 的 `:14-20`（HIGH #1）与 `:48-54`（MEDIUM #5）
5. 验收单：`<树根>/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md`

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

## 二、作者自述（**请独立核对，不要采信**）

以下每一条都是作者的主张。请自己找证据判断真伪，不要因为它写在这里就当成前提。

1. **告警确实是 warning，不会被升级成错误**：`backend/pytest.ini` 无 `filterwarnings`、
   无 `-W error`、无 `--disable-warnings`，`addopts` 只有 `-v --tb=short`。
   ⇒ 告警进 warnings summary 与汇总行，`rc` 不受影响。
2. **源码字面量门排除了自身、且判据不自指**：门用 `Path(__file__).resolve()` 排除
   conftest 本体；conftest 里原先唯一那段整段字面量（改前 `:118` 的提示文案）已拆成
   `_TMP_LITERAL = "/tmp/" + "test-vault"` 的 `+` 号拼接（相邻字面量会被
   `ast.parse` 在词法期折叠回一个 `Constant`，等于没拆，所以必须用 `+`）。
   ⇒ 验伪锚 `grep -c '/tmp/test-vault' backend/tests/unit/conftest.py` 改前 = 1、
   改后 = 0，是一条**会翻转**的判据，不是恒 0 的死判据。
3. **降级面的负控修前红、修后不红，且告警看得见**：单文件形态 N1 / N1'
   （`negctl-n1-before-*.txt` / `negctl-n1-after-*.txt`）。
4. **源码门承重**：正控 P1（`negctl-p1-red-*.txt` / `negctl-p1-green-*.txt`）——
   在 `test_vault_init_service.py` 末尾临时加一行硬编码路径常量 → 门红且**指名到
   file:line** → 还原后 `git diff --quiet` rc=0、`shasum` 与改前一致 → 复跑转绿。
5. **既有硬 fail 面没有回退**：正控 P2（`negctl-p2-red-*.txt`）—— 临时让一个用例
   在 `backend/` 下建骨架目录 → 门仍硬红并指名 `backend/raw`。
6. **fixture 仍零副作用**：不创建 / 不删除 / 不写入任何文件、不 `os.chdir`、
   不 `import app.*`、不依赖 cwd（扫描根与 backend 根都走 `__file__`）。
7. **双树并发的时序面是真跑出来的，不是推演**：N2 / N2'
   （`unit-n2*.txt` / `treeB-*.txt` / `window-*.txt`）—— 真起了第二棵 worktree，
   在树 A 的 session 窗口内并发建目录，两侧存档各留 `date` 自证窗口交叠。
8. **零影响面是实跑的**：`tests/api` / `tests/regression` / `tests/skills` 三个目录级
   开工 / 收工各跑一次，nodeid 集逐个 diff 为空；`tests/unit` 与 202 条红基线
   diff 为空。

---

## 三、请重点回答的问题（按重要性排序）

1. **降级会不会让「本树自己写 `/tmp/test-vault…`」漏网？**
   源码字面量门只看 `ast.Constant` 字符串常量。作者已登记的盲区是「运行期拼接」
   （`"/tmp/" + name`、f-string 变量段、`os.path.join` 分段）。
   **这个盲区列全了吗？**还有哪些**未被拦下的输入形态**会走到 `/tmp` 根而这道门
   看不见？其中哪些是本仓 `tests/unit` 里真实存在或很可能出现的？
2. **AST 门对读不了 / 解析不了的文件的处置对不对？**
   作者声称走的是「记『无法检查』并进硬 fail 出口」，而不是静默当成通过。
   请核对代码是否真的如此，以及这个出口有没有可能被别的分支短路掉。
3. **负控的目录产生时机，真的落在树 A 的 session 窗口内吗？**
   作者给了三条前提断言（树 B 存档显示它真建出了目录 / 树 A 正文出现**同一个**
   目录名 / 两侧 `date` 显示窗口交叠）。请从存档本身核对这三条是否都成立 ——
   如果任何一条只能从「理论上应该会」推出来而存档里看不见，请直接指出。
4. **(n) 用「另一棵树的探针文件」代替「另一棵树的真实测试写者」，证明力够不够？**
   缺口是否已如实登记在验收单的「本卡未证明什么」里，还是被说成了已证明？
5. **fixture 是否仍然零副作用、不依赖 cwd？**
   特别是新增的 `rglob` 扫描：有没有可能因为符号链接、权限、或扫描根取错
   而扫到树外，或者静默吞掉本该报出来的错误？

---

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
