# UAT — CARD-G3-3-R2-writer-boundary

> 批次: `[BATCH-2026-09-07-第十三批 / CARD-G3-3-R2-writer-boundary]` · 车道 `card-u5-lance`（分支 `card/u5-lance`）
> 前提 HEAD（U5-A 末 commit）: `8686d169` · 主干 CODE_BASE: `da690bf8`
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U5-B.md`（feature 主干树）
> 证据目录: `_bmad-output/审查/evidence-g33r2/`

---

## 一 做了什么（四件）

| # | 改动 | 落点 |
|---|---|---|
| 1 | `self_confidence_norm` **写点入口门**（fail-closed） | `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 主写点 PYEOF 块入口区，`evid` 拼好之后、**任何写入之前** |
| 2 | `event_id` **字符轴形态门** | `backend/app/services/learning_event_log.py::_event_id_shape_problems`，挂在 `append_event` 空判之后 |
| 3 | 校验器注释更新（**只改注释**） | `backend/scripts/validate_learning_events.py`（原 `:1639-1643`）—— `CHARSET_STRICT_FIELDS` 一字未动 |
| 4 | **E-2** `harness_tree` 解析 | `SKILL.md` 新增 `_harness_tree(vault_dir)`，`REPO = os.path.dirname(VAULT)` → `REPO = _harness_tree(VAULT)` |

外加：xfail(strict) 交接门**转正**（先证 XPASS 再去标）+ 58 个新增用例。

---

## 二 完成条件逐条对账

### (a) 第 0 分钟 + 四件开工基线 ✅

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-u5-lance` ✓ |
| 分支 / HEAD | `card/u5-lance` / `8686d169`（= U5-A 末 commit）✓ |
| `git status --porcelain` | 空 ✓ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在 ✓ |
| `$BASE` 自证 | `test -f` 通过；`grep -vc '^#' $BASE` = **202** ✓（路径为 feature 主干树绝对路径） |
| ① `tests/skills` 开工 | **369 passed** — `skills-open-20260908T092131.txt` |
| ② 五回归开工 | **371 passed, 1 skipped, 1 xfailed** — `five-regression-open-20260908T092233.txt`（恰 1 xfailed ✓） |
| ③ 三 harness `--list` | ANCHOR-ERROR **=0** ×3 — `anchor-*-open-20260908T092644.txt` |
| ④ `tests/unit` 开工 diff | **空**（202 逐条相同）— `unit-open-20260908T092641.txt` |

> ⚠️ 判据口径事故（如实记）：首次抽取 nodeid 时用 `sed` 剥掉了 `FAILED `/`ERROR ` 前缀，而基线**保留**前缀 ⇒ 两边都是 202 条却 diff 全不等（406 行）。**数量相同 + 全不等**是判据口径分叉的指纹，不是「本卡引入 202 条红」。修正抽取式后 diff 归零。

### (b) 样本普查先于写门 ✅

存档：`event-id-shapes-20260908T092658.txt`（tests 样本 + 5 个 backend 调用方源码行 + live 账本只读 + live 节点 receipt 值）。

**关键实测结论（三条，都推翻了规划稿）**：

1. **设计稿正则 `^[a-z]+:[^#]+#[A-Za-z0-9_-]+$` 作废**——live 账本 22 行里 **12 条会被它拒掉**：
   - `exam:CS 61B-2026-08-11-1349`（**含内部空格**、无 `#` 段）
   - `exam:递归与分治 (Recursion & Divide-Conquer)-2026-07-24-0714`（中文 + 括号 + `&` + 空格）
   - `derive:规划代理的特点`（纯中文、无 `#` 段）、`archive:<uuid4>`、`callout:cb-…`
   - 既有 regression 样本里还有 **`x-1` / `wrong` 这类无 `type:` 前缀**的合法输入。
2. **落点更正被实证**：live 账本 22 行 payload **零**含 `self_confidence_norm` ⇒ 它确是 **receipt-only**，`append_event` 侧碰不到它。所以本卡是**两条互不相干的门**，不是一条。
3. **数字串裁定 = 不接受**（卡文 (c) 缺省）。依据链：
   - live receipt 只有 `0`×4 / `0.4`×1，而 receipt 对 `str`/`int`/`float` **不可分辨**（`scn_` 不过 `q_()`，裸插值下 `"0.4"` 与 `0.4` 写出完全相同的字面）——**看 receipt 永远证不出上游类型**；
   - 断案的是**换算链**：live 节点 `self_confidence_raw: "2"` → `norm: 0.4`，正是规范 `:175`「数字 0-5 → 除以 5」的除法产物（float）；`raw: 不懂` ×4 → `norm: 0`；
   - `SKILL.md:218` 示例 payload 写作**裸数字** `0.5`；
   - 接受字符串必须先 `strip()`，那等于在身份键旁边重开一个「吃掉哪些字符」的口子。

**所有真实样本必被新门放行** ✓ —— 15 条放行用例逐条取自普查（含 live 真实值 4 条、5 个调用点拼法 5 条、无前缀 id 2 条）。

### (c) 写点入口门 ✅

```python
_scn = p.get("self_confidence_norm")
if _scn is None:            pass                      # 放行
elif isinstance(_scn, bool) or not isinstance(_scn, (int, float)) \
     or not math.isfinite(_scn) or not (0.0 <= _scn <= 1.0):
    raise SystemExit(...)                             # fail-closed
else: p["self_confidence_norm"] = float(_scn)         # 转 float
```

- `bool` **先判**（它是 `int` 子类，不先拦就被 `float(True)` 静默写成 `1.0` = 把「没填」伪装成「完全懂」）；
- `:1436` 与 `:1524` **一字未改**（判据 ③ 文本口径 3 行各命中 1 次）；
- `import math` 用**插入**而非改既有 import 行，保住判据 ④「只删 1 行」。

### (d) `append_event` 字符轴形态门 ✅

`_event_id_shape_problems(event_id) -> list[str]`：非 `str` / 空 / `!= strip()` / 禁止码点 / `> 512` → 各报一条（码点报 `U+%04X`）；命中 → `logger.warning` + `return False`（**不抛**，与 `:181-183` 同形，也与本函数「永不抛异常」的契约一致）。

- 放行 **15 例** / 拒绝 **14 例**（均 ≥4）；
- **不要求 `type:` 前缀**（(b) 实证）；
- **与校验器同口径**：`_EVENT_ID_FORBIDDEN_RANGES` 与 `FORBIDDEN_CODEPOINT_RANGES` 逐范围相等，由 `test_g33r2_shape_gate_charset_matches_validator` 承重；另有 `test_g33r2_shape_gate_agrees_with_validator_on_event_id` 比**行为**（集合相等而遍历写错时，前者照样绿）。
- **`CHARSET_STRICT_FIELDS` 未扩**——两份不依行号快照开工/收工 diff **均空**（见 §三 判据 5）。

> ⚠️ **方向如实声明**：新门**不能比校验器窄**。窄了就留下「写得进、读不回」——一条含 U+2028 的 `event_id` 能被 `append_event` 写进账本，而校验器读侧对该码点 fail-closed 判的是**整个账本**不合规 ⇒ 那个 vault 从此所有评分都进不来（= `value_charset_problems` docstring 记录的 round-1 BLOCKER 数据丢失路径）。故禁止集取**校验器全集**（含 U+2028/2029 与 noncharacters），比卡文 (d) 列举的六条更宽。

> ⚠️ **设计取舍如实声明**：用「独立定义 + 一致性门」而非 `import` 本体——`backend/app/**` 至今**零**依赖 `backend/scripts/**`，加 sys.path hack 会同时弄脏 pyright 面与打包面。代价是必然会漂移，所以一致性门是这个设计的**全部承重处**（它自带非空验伪锚，防「两侧一起被清空」被读成「一致」）。

### (e) 校验器只改注释 ✅

- `CHARSET_STRICT_FIELDS` 整块（声明行 + 5 键 + 收尾 `)`）**逐字未动**；
- `:1644-1647` 那四行（`#: 行为证据见…` / `#:` / 两行 producer 说明）**未被吃掉**（grep 自证仍在）；
- 改后 `g32ccr1 --list` ANCHOR-ERROR **=0**。

### (f) xfail 翻转 ✅

| 步 | 实测 |
|---|---|
| 去标**前** | `FAILED … ` 且正文含 **`[XPASS(strict)]`** — `xpass-strict-20260908T103407.txt`（末行 `rc=1`） |
| **分支绑定** | `branch-binding-20260908T103453.txt`：`returncode=1` ⇒ 走**拒写**分支；账本 **0 行**；拒因含「须为 null 或 0..1 的数」⇒ **确由本卡新门拒**；节点字节不变 |
| 去标**后** | `1 passed`（并入五回归 final 429 passed） |
| docstring | 已更正 `:1320/:1408` → **`:1436` 读 / `:1524` 拼**，并写明「写入分支现走不到，保留它是**方向判据**」 |
| `:6323-6330` 二选一 | **原样保留**（逐字自证） |
| 新增对称用例 | `bool True/False` / `1.5` / `-0.1` / `"0.5"` / `"nan"` / 两种换行注入 / `list` / `dict` = **10 拒**；`0.5 / None / 0 / 1 / 0.4 / 1.0 / 0.0` = **7 放行** |

> ⚠️ **捕获面事故（如实记）**：首次取 XPASS 存档用了 `tail -20`，把 FAILURES 正文段里的 `[XPASS(strict)]` 截掉了，导致 `grep -c` = 0，一度读成「真失败」。**判据没错，是捕获面太窄**。截断存档已移出证据目录（`scratchpad/xpass-truncated-discarded.txt`），重取全量后 XPASS 命中 1。

### (g) E-2 `harness_tree` ✅

`_harness_tree(vault_dir)`：读 `VAULT/.canvas-config.yaml` → **逐行正则** `^harness_tree:\s*(.*?)\s*$`（**不依赖 PyYAML**，与 `:1075`「PyYAML 不可用 → 退回正则扫描」同口径）→ 剥引号/尾注释 → `expanduser` → 相对路径相对 VAULT → `normpath` → `isdir(tree/backend/scripts)` 否则 **SystemExit 不回退**。

| 用例 | 实测 |
|---|---|
| ① 无键 | 回退 `dirname(VAULT)`，rc=0 且照常写入 ✓ |
| ② 坏路径（4 变体：绝对/`~`/带引号/相对） | rc≠0、stderr 含 `harness_tree`、账本 0 行、写入面字节不变 ✓ |
| ③ 显式真 REPO（带引号） | rc=0，与①同结果 ✓（**这条是「解析真被用上」的验伪锚**——没有它，「解析根本没跑」也能让①②④全绿） |
| ④ `~/definitely-missing-…` | rc≠0，且拒因里**不含未展开的 `~`** ⇒ 证 `expanduser` 走到了 ✓ |
| 空值 / 空引号串 | **回退**（不是 fail-closed）——「值被清掉」≠「值写错了」，混成一条会让「清空该键」变砖化操作 ✓ |

Codex 问题④ 预判的边界也已实测：`harness_tree: ""` / 裸空值 / 指向**文件**而非目录 / 带引号+尾注释 / 裸值+尾注释 —— 全部符合预期。

**`canvas-vault/.canvas-config.yaml` 未动**（`git status --porcelain --` 恒空，U3 地盘）；`:341` 未改。

### (h) harness 锚点不破 ✅

三 harness `--list` 收工 ANCHOR-ERROR **=0**，与开工输出 `diff` **行数 0**（三份全空）。格式化后又复核一次（`anchor-*-final-*.txt`），仍全 0。
**未跑全量变异**（U8-B 面）——三 harness 全量 KILLED 数在本卡后**未复测**，归 U8-B 集成树复跑。

### (i) 目录级与回归 ✅

| 裁判 | 开工 | 收工 |
|---|---|---|
| `tests/skills` | 369 passed | **369 passed, 0 failed** |
| 五回归五文件 | 371 passed, 1 skipped, **1 xfailed** | **429 passed, 1 skipped, 0 failed, 0 xfailed** |
| `tests/unit` nodeid diff | 空 | **空**（`>` 行 **0**，`<` 行 0）|
| `tests/unit` SKIPPED | 48 | **48** |

新增用例 **58** = 57 个 `g33r2` 前缀 + 1 个转正（429 − 371 = 58，精确吻合）。
承重那跑用**固定路径** `unit-close-20260908T105222.txt`（禁 glob）。

> ⚠️ 补了红基线 diff 的已知盲区：nodeid diff 对**类/模块级 skip 关掉的原本绿测试**失明，故另收 SKIPPED 计数对照（48 = 48）。

### (j) 禁顺手修存量 ✅

- `pyright app/services/learning_event_log.py` → **0 errors, 0 warnings**（主干本为 0 错 ⇒ 未引入）；
- `ruff check` 四文件 → **All checks passed**；
- `ruff format` **归因用内容口径**（不用行号交集——改契约会让新错误落在没动过的行上）：三文件「基线 format --diff 改动行数」vs「当前」的**增量**，格式化后全为 **0**；
- `test_learning_event_log.py:72-76` 的**存量 4 行漂移原样保留**（用 `ruff format --range 78-` 只格式化本卡新增段，自证 hunk 仍在）；
- 未碰任何其它 `backend/app` 文件。

### (k) 只登记不做 ✅

存档 `registered-not-fixed-20260908T105302.txt`，四组：ai-linked-doc 第四写者（子串查重 / 无锁 / 无 LF 守卫 / **绕开本卡形态门**）、start-exam-board 第三写者、5 个 backend 调用点形态表（**均未检查 `append_event` 返回值** —— 登记，改它属各端点地盘）、复放路径对称形态。

### (m) 地盘门 ✅

`git diff --name-only da690bf8 HEAD -- . ':(exclude)_bmad-output'`（工作树）恰为允许集 5 文件，无越界：

```
backend/app/services/learning_event_log.py
backend/scripts/validate_learning_events.py
backend/tests/regression/test_g3_2_review_ledger.py
backend/tests/regression/test_learning_event_log.py
canvas-vault/.claude/skills/quiz-answer/SKILL.md
```

---

## 三 核心裁判逐条

| # | 裁判 | 结果 |
|---|---|---|
| 1 | 单跑 g32ccr1 门 | 去标前 `FAILED` 含 `XPASS(strict)` ✓ / 去标后 `1 passed` ✓ |
| 2 | 五回归五文件 | 开工 1 xfailed → 收工 **0 failed 0 xfailed** ✓ |
| 3 | `tests/skills` 目录级 | **0 failed**（369=369）✓ |
| 4 | 三 harness `--list` | ANCHOR-ERROR=0 ×3，开工/收工 diff **空** ✓ |
| 5 | 严格表两份**不依行号**快照 | ① 运行期真值 diff 空 ② 整块文本 diff 空（开工自证 **7 行 / 6 个含 `(` / 尾行 `)`** 三数全中）✓ |
| 6 | `tests/unit` nodeid diff | **空**（0 个 `>`）✓ |
| 7 | `git diff --stat da690bf8 HEAD -- canvas-vault/.claude/scripts/` | **空** ✓；`fsrs_bridge.py` sha 开工=收工 `a766fbcc…` ✓ |
| 8 | E-2 四用例 | ②④ rc≠0 含 `harness_tree` / ①③ rc=0 ✓ |
| 11 | live 只读 | 账本 sha 开工=收工 `2a18023e…` ✓；`节点/ -newer sentinel` = **0** ✓ |

**判据 ④**（只插不删）：`git diff --no-color da690bf8 -- SKILL.md \| grep -c '^-[^-]'` = **1**，唯一删除行是 `-REPO = os.path.dirname(VAULT)` ⇒ `q_()` 本体与 `:1505-1529` 拼接链**零改动**。
**禁改锚行**文本复核：`node_id` 门行 / `_e_id, _e_pl = evid, p` / `_e_id = str(ev.get(...))` / `sys.path.insert(…REPO…)` 各命中 1 次 ✓。

---

## 四 DoD-3

### 4-A 技术证据

见 §二 / §三 全表；证据目录 `_bmad-output/审查/evidence-g33r2/`（33 份 `.txt`，承重裁判末行带 `rc=`，`*.stderr*` **零入库**）。

### 4-B 用户视角（零技术词）

给一道题打分时，自评那一格只能填 0 到 1 之间的数，填了别的东西会被当场拦下并告诉我原因，不会悄悄把这条记录的身份改掉；课程库如果指错了后端目录，也会明说而不是继续写——我感觉评分记录更可信了。

**felt-sense**：以前那个毛病最阴的地方不是「记错一次」，而是**第一次还好好的，从第二次开始这个知识点就再也评不了分了**——你根本不知道是哪一步坏的。现在它在动笔之前就停住，把哪个值不对、为什么不能要，一次说清楚。心里那种「不知道什么时候会突然坏掉」的悬着感没了。

---

## 五 本卡未证明什么

1. **未证明** start-exam-board / ai-linked-doc 两个写点的 `event_id` 形态与查重行为——第三/第四写者只登记（它们都**绕开** `append_event`，本卡形态门管不到）。
2. **未复跑**三 harness 全量变异，只核锚点命中数；三 harness 全量 KILLED 数在本卡后**未复测**，归 U8-B 集成树复跑。
3. **未证明**复放路径在 `ev.payload` 含非法 `self_confidence_norm` 时的对称行为——该路径把 `scn_` 恒置 `None`，观察不到。
4. **未证明** vault 不是 repo 直接子目录**且**无 `harness_tree` 时的行为（回退 `dirname(VAULT)`，与主干同，不修）。
5. **未证明**新形态门与 `value_charset_problems` 在**全部** Unicode 码点上一致——只按 (b) 样本 + 11 个对撞样本 + 集合逐范围相等来证；两者共用同一个禁止集定义，但遍历实现是两份代码。
6. **未证明** `harness_tree` 在 `backend/scripts` 是 symlink、或指向另一棵**真实可用**代码树时的端到端行为（用例只造了目录结构，未跑跨树 import）。
7. **未证明** 5 个 backend 调用点在形态门拒绝后的**下游行为**——它们均不检查 `append_event` 返回值，本卡未改。
8. **未部署 live**（本批无部署卡）；`.canvas-config.yaml` 树内仍无 `harness_tree` 键，E-2 消费端已就位但**生产上尚无人写该键**。

---

## 六 台账待登记条目

1. **Z6-A/RV-D Codex HIGH「`self_confidence_norm` 可改写 receipt 身份」→ 本卡修复**：写点门落 `SKILL.md` 入口区；XPASS 存档 `evidence-g33r2/xpass-strict-20260908T103407.txt`；分支绑定 `branch-binding-20260908T103453.txt`；去标 nodeid `test_g3_2_review_ledger.py::test_g32ccr1_self_confidence_norm_must_not_forge_receipt_identity`。
2. **设计稿 event_id 正则作废**（`^[a-z]+:[^#]+#[A-Za-z0-9_-]+$`）：live 账本 22 行中 12 条会被拒（含内部空格 / 中文 / 括号 / `&` / 无 `#` 段），既有 regression 还有 `x-1`/`wrong` 无前缀样本。实际门 = **字符轴 + 首尾空白 + 长度**，不管命名法。普查存档 `event-id-shapes-20260908T092658.txt`。
3. **E-2 `harness_tree` 消费端落地**：键名与 U3-B **逐字同**；树内 `.canvas-config.yaml` **仍无该键**（本卡不改，U3 地盘）⇒ U3-B 写入后需在集成树复跑 (g)①③。
4. **ai-linked-doc 第四写者缺陷登记** → 第十四批候选卡：子串查重（`derive:A` 被 `derive:AB` 匹配 ⇒ 事件永久丢失）/ 无锁 / 无 LF 守卫 / 无形态门。
5. **三 harness 锚点命中数开工=收工**：`anchor-*-{open,close,final}-*.txt` 共 9 份，diff 全空。
6. **Codex 各轮存档路径、绑定 SHA、B/H/M/L**（见 §七，本节随轮次补）。
7. **`tests/unit` 目录级 diff = 空**（202=202，0 个 `>`）；SKIPPED 48=48（补红基线 diff 盲区）。承重跑 `unit-close-20260908T105222.txt`。
8. **基线文件在 feature 主干树且 untracked** ⇒ 本批所有 NEW @ `da690bf8` 的车道引用 `evidence-b13/**` 必须用主干树**绝对路径** + 开工 `test -f` / `grep -vc '^#'` = 202 自证。**建议主 session 收进手册 §零。**
9. **卡文行号勘误**：`_writer_code` 前稿 `:217-220` → 实测 `:216-219`（起点漏 `def` 行）——卡文 §〇 已自行更正，此处备案。
10. **行为变化登记（需知会消费侧）**：live 现存 receipt 写作 `self_confidence_norm: 0`（int 裸插值）；本卡把 int 转 float ⇒ 今后写 `0.0`。YAML 语义等价（`safe_load` 均为数字 0），但**字面变化**。
11. **判据口径事故两则**（方法论，建议入 gotcha）：
    - **nodeid 前缀口径分叉**：基线保留 `FAILED `/`ERROR ` 前缀，抽取时 `sed` 掉 ⇒ 两边都是 202 条却全不等。「**数量相同 + 全不等**」是口径分叉的指纹，先怀疑判据再怀疑被测物。
    - **捕获面截断**：`tail -20` 把 pytest FAILURES 正文里的 `[XPASS(strict)]` 截掉 ⇒ `grep -c` = 0，一度把「门转正」读成「真失败」。判据没错，是**捕获面**太窄；承重存档必须收全量。
12. **格式漂移归因口径**：用 `ruff format --diff` 在**基线版 vs 当前版**各跑一次比**增量**（内容口径），不用行号交集（改契约会让新错误落在没动过的行上）；基线侧必须带 `--stdin-filename`，漏了会假判定。修只用 `--range`，**禁**顺手 format 整文件（`test_learning_event_log.py` 有 4 行存量漂移，已保留）。

---

## 七 Codex 轮次

### round-1（绑定 `609ce455`）

- 存档：`_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary.md`（首部六行 blockquote 按协议 §2.1）
- prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-G3-3-R2-writer-boundary.md`（五分节；禁用措辞扫描 0 命中）
- 模型 `gpt-6-astra` · `ultra` · `codex-cli 0.153.3` · read-only
- **BLOCKER 0 / HIGH 0 / MEDIUM 5 / LOW 3**（tokens 61,129）

**逐条独立验证与处置**（每条先复现再改，未复现的不改）：

| # | 级别 | 内容 | 独立验证 | 处置 |
|---|---|---|---|---|
| M1 | MEDIUM | `_harness_tree` 引号正则贪婪，`"/x" # use "main"` 解析成 `/x" # use "main`；`harness_tree: # reset` 的 `#` 被当路径 | **复现确认**（两种形态实测都错） | ✅ 修：引号内容改非贪婪 `(.*?)`；裸值 `#` **一律**视为注释起点（路径含 `#` 须加引号，与 YAML 本身规则一致）+ 2 个回归用例 |
| M2 | MEDIUM | 零写测试只看新增路径差集，对「改写已有/删除/建后删」三盲；`.lock`/`quiz-answer` 豁免按**名字子串**过宽 | **确认**（判据面确实窄于声明） | ✅ 修：全树 `(path → size, sha256)` 内容指纹逐条比对 + 精确路径豁免（锁名 = `sha1(realpath(NODE))[:16]` 可推算）+ 锁文件必须 0 字节 + 判据自证探针 |
| M3 | MEDIUM | 显式真 REPO 用例写 `vault.parent` = 回退值本身，「解析被采用」证不出来 | **确认**（我在 docstring 里称它是验伪锚，当时不成立） | ✅ 修：两端点对照——A 端先把缺省目标 `backend/` 改名并**断言前提成立**（缺省必须失败），B 端只加一行配置必须成功 |
| M4 | MEDIUM | 拒因断言查的是另一次直接调 helper 的结果，与 `append_event` 实际分支无绑定（`None` 时空判先拒、门没跑也绿） | **确认** | ✅ 修：改查 `caplog` 里 `append_event` 自己打出的形态门 warning（该句只在形态门分支产生）+ 新增假值分层用例（断言空判拒、形态门**不**拒，门序对调会红） |
| M5 | MEDIUM | 一致性门锁不住「截断遍历」（`event_id[:7]`）与「两侧同时删同段」 | **确认** | ✅ 修：深位孪生体（坏码点在 45+ 字符处）+ 合法深位对照 + 关键码点表逐段覆盖（补 `0xFDD0/FDEF`、每平面末两码点抽三个平面）+ 误拒方向验伪锚（ASCII/中文/emoji/扩展 B 不得入集） |
| L6 | LOW | `math.isfinite(10**400)` 抛 `OverflowError` 绕过受控拒因 | **复现确认** | ✅ 修：`float()` 前置 + `except (OverflowError, ValueError)` 走同一句拒因 |
| L7 | LOW | `1e-6` 经裸插值写 `1e-06`，PyYAML 读回**字符串**（类型保真，原拼接方式残留） | **实测不砖化**（重跑 rc=0 / 后续评分 rc=0 / validator rc=0，`evidence-g33r2/low7-scientific-notation-probe-*.txt`） | 📋 登记不改（Codex 自评也不属本卡范围；它是 `:1524` 裸插值的既有形态，该行本卡禁改） |
| L8 | LOW | 「写入分支是方向判据，删掉它等于允许伪造」的解释过强——非法载荷的拒绝面已由 `illegal_is_fail_closed` 组锁住 | **确认**（逻辑成立） | ✅ 修：docstring 措辞按实测更正——保留分支的真实价值是**语义演化**场景（门合法化时唯一还锁身份保持的锚），当前不可达性由拒绝面组间接保证 |
| 补充 | — | 「接受字符串须 strip() ⇒ 重开吃字符口子」的因果不成立（若只使用转出的 float，被剥字符不进 YAML） | **确认** | ✅ 修：SKILL.md 注释理由换成真实依据（**类型契约**：上游给字符串=归一化没做完，报给它；并如实记下原因果为何不成立） |

**R1 整改后裁判全部重跑**：五回归 **436 passed, 1 skipped, 0 failed, 0 xfailed**；`test_learning_event_log.py` 43 passed；`g33r2/g32ccr1` 选集 28 passed；tests/skills **369 passed**；三 harness ANCHOR-ERROR=0 且与开工逐字同（双侧滤 `rc=` 后 diff=0——单侧漏滤会假报 2 行，判据口径又踩一次）；判据③④/验伪锚①②/禁改锚行/fsrs 零写全部复核通过；ruff check 过、pyright 0 错、format 增量三文件 0（存量 4 行原样保留）。

### round-2（绑定 `<R1 整改 commit>`）

（随轮次补）
