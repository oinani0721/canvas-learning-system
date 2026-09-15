# UAT · CARD-HARNESS-TREE-PARSE-REDO（`_harness_tree` 解析整体重做）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-HARNESS-TREE-PARSE-REDO]` · 车道 `card-t7-skills`（分支 `card/t7-skills`）
> 基线 `08100483` → 代码 commit **`f7f10be4`**（round-1 审过的中间态）→ **`4d21bc9b`**（按 round-1 结论整改）→ **`e844d6a1`**（按 round-2 结论 + 自查整改）→ **`34451227`**（按 round-3 结论整改）→ **`4eeaeaa6`**（按 round-4 结论整改）→ **`faaeb005`**（用户裁定「缺库即拒写」）→ **r7 待提交**（按 Codex r6 + 变异测试补门，最终 HEAD）· 未 push
> ⚠️ 卡文 (k) 写「单独 commit」；实际两个代码 commit —— Codex round-1 报 MEDIUM+LOW，按 D-15「审后再改代码必再送一轮」整改后必然产生第二个。两个 commit 都只落在同三文件。
> 证据目录 `_bmad-output/审查/evidence-harness-tree/`（全部 `.txt`，无 `*.stderr*` 入库）

---

## 一 本卡做了什么

`canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `_harness_tree`（`:370-460`）由**逐行正则**改为
**`yaml.safe_load` 优先 + `realpath` 取代 `normpath` + 缺 PyYAML 即拒写**，根治
`UAT-CARD-G3-3-R2-writer-boundary-2026-09-08.md` §七 round-5 登记的三条同族 MEDIUM：

| 代号 | 旧实现的实际行为（本卡先红实测） | 重做后 |
|---|---|---|
| M-a | `normpath` 按字符串消 `..`，symlink 在中间段时与 OS 逐段解析分叉 ⇒ 绑到 `mA/repo` 而不是 OS 会打开的 `mB/repo` | `os.path.realpath` 逐段解析，以 OS 会打开的那棵为准 |
| M-b | 引号正则不认 YAML 转义引号：`'…/repo'' #alt'` 被截成 `…/repo'`；`"…/repo\" #alt"` 被截成 `…/repo\`（字面反斜杠） | 交给 PyYAML，取 YAML 真值 |
| M-c | 只认列首逐字 `harness_tree:`；`harness_tree : /B` / `"harness_tree": /B` / `'harness_tree': /B` 三种合法 YAML 全部当成「没写这个键」⇒ 静默回退 vault 父目录 | `safe_load` 对四种写法给出同一个 dict |

降级分支（**仅** `except ImportError`）只接受 `harness_tree: <绝对路径>`（列首键、SP/TAB 分隔、裸值、不含 `#`），
其余一律 fail-closed；`safe_load` 抛解析错 ⇒ fail-closed 且点名 `harness_tree`，不吃成回退。
**三条分界逐字不变**：无键 / `null` / 空串 ⇒ 回退 `dirname(VAULT)`；有值但树不存在 ⇒ 拒写；config 断裂 ⇒ 拒写。

---

## 二 4-A　Claude 已代验（技术证据，逐条 tee 路径 + rc）

| # | 判据 | 结果 | 存档（`_bmad-output/审查/evidence-harness-tree/`） |
|---|---|---|---|
| 0 | 第 0 分钟：`pwd` / 分支 `card/t7-skills` / `HEAD=08100483` / `status` 空 / venv pytest+pyright / `.env` / `yaml 6.0.3` / `ruff 0.15.9` | 全通过 | 见 §三 |
| 1a | 开工基线① `-k harness_tree` | **16 passed** rc=0 | `g3_2-harness-open-20260914T195136.txt` |
| 1b | 开工基线② 整文件 | **165 passed** rc=0 | `g3_2-fullfile-open-20260914T195308.txt` |
| 1c | 开工基线③ `tests/skills` 目录级 | **546 passed** rc=0 | `skills-open-20260914T195609.txt` |
| 2 | **(b) 先红**（改 SKILL.md 前） | **6 failed, 16 passed** rc=1 —— 六条全红在各自判据断言 `assert r.returncode == 0`，前提断言全绿 | `g3_2-harness-red-20260914T200017.txt` |
| 3 | **(d)① 改后** `-k harness_tree` | **31 passed** rc=0（16 既有 + 15 新） | `g3_2-harness-close-20260914T200954.txt` |
| 4 | **(d)② 整文件收工** | **180 passed** rc=0（= 165 + 15 新 nodeid，零本卡新红） | `g3_2-fullfile-close-20260914T201024.txt` |
| 5 | **(e) SKILL-PORT-LINT** 指纹门先红 | `test_managed_files_match_digest_baseline` FAILED（基线 `c1588ec6…` vs 实测 `6f53bb50…`）；`test_layer2_body_counts_match_baseline` **passed**（计数未变） | `negctl-digest-20260914T200542.txt` |
| 6 | **(e) 收工** `tests/skills` 目录级 | **546 passed** rc=0（= 开工基线数） | `skills-close-20260914T200832.txt` |
| 7 | **(f)① 负控**：还原正则版 ⇒ 三组 M 门必红 | **6 failed** `neg1_pytest_rc=1`；跑前/还原态/还原后 sha256 三段齐（`6f53bb50…` → `c1588ec6…` → `6f53bb50…`，前后逐字同） | `negctl-both-20260914T201544.txt` |
| 8 | **(f)② 验伪锚**：SKILL.md 末尾加一行无害注释 ⇒ 指纹门必红 | FAILED `neg2_pytest_rc=1`（加注释后 sha `3165f557…`）；trap 还原回 `6f53bb50…` | 同上 |
| 9 | **(g) 降级分支** 9 个 nodeid | 全 passed（含"探针没生效就红"的自证断言与 6 组配对控制组） | 含于 #3 / #4 |
| 10 | **(h) 地盘门**（HEAD 口径） | `08100483..f7f10be4` 排除 `_bmad-output` 后**恰 3 文件**；`backend/app` 0 文件 | `ruff-territory-head-20260914T201828.txt` |
| 10b | (h) 验伪锚（**修正版**，见 §四.5） | 带 exclude 3 条 / 去掉 exclude 多出 **13** 条 `_bmad-output/`（总 16） | `territory-anchor-fixed-20260914T201838.txt` |
| 11 | **(k) ruff**（HEAD 口径，子 shell 包裹） | `files=2` / `check_rc=0` / 两文件 `head_fmt_rc=0`、`base_fmt_rc=0`；验伪锚 format rc=1、check rc=1 | `ruff-territory-head-20260914T201828.txt` |
| 12 | **(i) 硬边界自证** | 本卡新增 446 行中 `fsrs_bridge` / `decay_beta` / `7691` / `7687` / `lancedb.connect` / live vault 绝对路径 **各 0 命中**；三文件全文命中数 10/12/7 **与 `08100483` 基线逐文件相同**（既有引用，非本卡引入）；新增测试行 9 处落 `tmp_path` / `vault.parent` | `ruff-territory-20260914T201635.txt` |
| 13 | `*.stderr*` 入库 | 0 | `ruff-territory-head-…txt` 末段 |
| 14 | W4 哨兵 | 每次 `tests/regression` / `tests/skills` 跑均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | 各存档末尾 |

### 2.1 新增 15 个 nodeid

```
test_g33r2_harness_tree_symlink_resolved_by_os_not_string                (M-a, 1)
test_g33r2_harness_tree_yaml_escaped_quote_not_truncated[single|double]  (M-b, 2)
test_g33r2_harness_tree_noncanonical_key_form_is_honored[×3]             (M-c, 3)
test_g33r2_harness_tree_degraded_canonical_form_still_works              (降级, 1)
test_g33r2_harness_tree_degraded_absent_key_still_falls_back             (降级, 1)
test_g33r2_harness_tree_degraded_noncanonical_is_fail_closed[×6]         (降级, 6)
test_g33r2_harness_tree_degraded_unicode_space_is_fail_closed_too        (降级, 1)
```

### 2.2 (g) 降级探针机制（如实贴出）

本机 venv `yaml 6.0.3` ⇒ yaml-first 分支恒被走到，`except ImportError` 那段**零覆盖**。探针做法
（`_run_writer_no_yaml_at_harness_tree`，`test_g3_2_review_ledger.py:7289`）：对逐字提取出的写点代码做一次
锚定替换，把唯一的 `REPO = _harness_tree(VAULT)` 包成

```python
import sys as _t7a_sys
_t7a_sys.modules['yaml'] = None  # 探针: 只让 _harness_tree 这一次看不见 PyYAML
try:
    REPO = _harness_tree(VAULT)
finally:
    del _t7a_sys.modules['yaml']
```

锚点命中数必须恰为 1，否则门当场断言失败（防"探针没注入、门照样绿"）。每条降级门都另断言
stdout 里出现降级告警文本，作为"确实进了那条分支"的自证。

**为什么不整进程注入**（2026-09-14 实测，见 §四.6）：往 `PYTHONPATH` 放一个抛 `ImportError` 的
`yaml.py` 之后，写点会在更下游的 `_vault_id_of()`（写点 `SKILL.md:1422` 调用、`:1424` 抛；该函数由 `:469` 从校验器 `validate_learning_events` 导入，PyYAML 依赖在校验器一侧）
先 fail-closed，stderr `[quiz-answer] vault 归属无法绑定 (.canvas-config.yaml 缺失/损坏或 backend 不可达)`。
⇒ 在**真缺库**机器上"规范写法仍写得成"这半条根本不可达，整进程注入测不到本函数的降级分支。

---

## 三 第 0 分钟与 §〇 锚点复核

```
pwd=…/worktrees/card-t7-skills   branch=card/t7-skills   HEAD=08100483   status_lines=0
backend/.venv/bin/pytest ✓   backend/.env ✓   backend/.venv/bin/pyright ✓
yaml=6.0.3   ruff 0.15.9
```

§〇 每条 file:line 逐条实测**全部对上**（改前）：`_harness_tree` `:370`、`REPO = _harness_tree(VAULT)` `:442`、
`:397/:425/:428/:431/:437/:438` 六行逐字同、SKILL.md sha256 `c1588ec6…`、F1 `:1165`/`:1184`、
既有 8 个门定义行 `:6864/:6887/:6922/:6938/:6975/:7022/:7063/:7086`、`-k harness_tree` = `16 passed, 149 deselected`。

改后行号（供后续卡引用，⚠️ 会漂，请用 `grep -nF` 重锚）：`_harness_tree` `:370`、调用点 `:460`、
F1 `:1183`/`:1202`；测试文件 7447 行。

---

## 四 卡文/手册事实更正（实测与卡文不符处，逐条如实）

1. **手册验伪锚命中 2 行、非"恰 1 行"**：`grep -nF '地盘扩充（裁定 R-B14-4' <手册>` 实测命中 `:69`（§一 真正的地盘扩充行，行内含 `test_g3_2_review_ledger.py`）与 `:476`（§三 T7-A 的 `/goal` 块副本，也含这句话）。自证仍**成立**（`:69` 那行满足全部条件），但卡文的"恰 1 行"口径需更正为"至少 1 行且 §一 那行含该文件名"。
2. **手册行号漂移**：`lint 基线指纹随卡更新并声明` 实测在 `:123`，卡文写 `:118`（卡文已自警"行号不可引"）。
3. **卡文只列了两道 lint 门，实际有三道**：除 `test_managed_files_match_digest_baseline`（文件 sha256）与 `test_layer2_body_counts_match_baseline`（body 计数）外，还有 **`test_tmp_block_fingerprints_match_baseline`**（含 `/tmp` 的 fence 块整块指纹，`TMP_BLOCK_BASELINE`）。主写点 PYEOF 块起始行仍是 `:229`，只有整块哈希变 `571eb660…` → `664dd4d8…`。本卡按手册 §一.3「lint 基线指纹随卡更新并声明」同一授权同步，并在代码里就地写明理由。
4. **卡文 (i) 的"三文件 `fsrs_bridge|decay_beta` 0 命中"不成立**：`08100483` 基线就有 10/12/7 共 29 处（vault fixture 合法 symlink 它们、SKILL.md 合法引用），本卡**现值与基线逐文件相同**。有判别力的口径是"本卡新增行 0 命中"，已按此实测并记入 #12。
5. **卡文 §二.7 的地盘验伪锚在本仓恒 0（假绿风险）**：`git diff --name-only | grep -c '^_bmad-output/'` 实测 **0** —— git 默认 `core.quotepath` 会把非 ASCII 路径整条加引号转义（`"_bmad-output/\345\256\241…"`），行首是 `"` 不是 `_`，`^` 锚点静默落空。修正写法 `git -c core.quotepath=false …` 后命中 13。两种写法的对照已同存档落盘。**建议回写协议/手册模板**。
6. **卡文 (g) 建议的整进程 `PYTHONPATH` 注入不可行**，理由见 §2.2（更下游 `_vault_id_of` 先 fail-closed）。已改用收窄到单次调用的探针，并把整进程实测结论如实登记。
7. **卡文 (b)/(g) 列的"Unicode 空白"在降级分支没有可判用例**：实测 PyYAML 对"冒号后直接跟 U+3000 / NBSP / TAB"直接抛 `ScannerError`（到不了取值那一步），而"值里含 U+3000 的合法路径"两条分支给出**同一个值**（本卡降级正则接受面窄于 PyYAML，但对它接受的输入与 PyYAML 逐字同值）。⇒ 造不出"平时成功、缺库才拒"的配对控制组。已改为单独一门 `..degraded_unicode_space_is_fail_closed_too`，钉**拒因来自哪一层**（路径判据 vs 写法判据）而非"谁拒谁不拒"。该用例的第一版曾被自己的配对控制组当场判否——控制组起了作用，如实记录。
8. **`QUIZ_ANSWER_BASELINE` 注释的行号早于本卡就已失实**：注释写 `:74/:2977/:2985/:3076`，`08100483` 实测为 `:74/:3086/:3094/:3185`（**已漂 109 行**），本卡 `_harness_tree` 重做再 `+18` ⇒ 现值 `:74/:3104/:3112/:3203`。已校正并在注释里补一条重测命令，说明"计数才是基线、行号只是线索"。
9. **负控自身的缺陷（已修，如实记）**：第一版负控脚本的 EXIT trap 用**相对路径**还原 SKILL.md，而脚本中途 `cd backend` ⇒ trap 触发时 cwd 已变，`cp` 落到不存在的 `backend/canvas-vault/…` 而失败，SKILL.md 被留在还原态。是"跑后 sha256 必须等于跑前"这条判据当场发现的。第二版改为**绝对路径 + 子 shell 包 `cd`**，并把 pytest 的 rc 在子 shell 内取（第一版 `${pipestatus[1]}` 取到的是 `tail` 的 rc，存档里留下了误导性的 `neg1_pytest_rc=0`，该存档 `negctl-regex-20260914T201513.txt` 保留但**以 `negctl-both-20260914T201544.txt` 为准**）。
10. **勘探口径更正②（卡文已预告，实测确认）**：既有 8 个 harness_tree 门（16 nodeid）本就**全绿、无任何 `xfail`**；全文件唯一 `xfail` 字样在 `:6307` 且是 docstring 文本、与 harness_tree 无关。故本卡不是"去标 xfail"，而是"新增 M 门先红后绿 + 既有保持绿"。

---

## 五 行为 / 措辞变化（(d)③ 逐条）

| 位置 | 变化 | 性质 |
|---|---|---|
| `test_g3_2_review_ledger.py:6967`（L-a） | TAB 参数行内注释「真 YAML plain scalar 禁 TAB ⇒ 链路层判损坏拒写」→「本机 PyYAML 的 scanner 直接拒这一行 ⇒ 本函数 fail-closed(实测, 不泛化成「YAML 规范禁 TAB」)」 | 措辞，round-5 LOW（L-a）收口；**断言未动** |
| `test_g3_2_review_ledger.py:6987-6998`（`:6975` docstring 的 `invalid` 段） | 旧文写「本函数的正则层按 s-white **剥掉**它、并不拒；拒写来自更下游的 config 读取层」—— redo 后**失实**。改为并列记两次实测：2026-09-08（正则实现，拒来自下游）/ 2026-09-14（PyYAML 之后，拒**上移到本函数**，报「.canvas-config.yaml 不是合法 YAML」） | 措辞；**断言未动**（仍只钉 rc≠0 且零写，不断言由哪一层拒） |
| `SKILL.md` fail-closed 拒因 | 新增 `[逐段解析 symlink 后: <realpath>]` 后缀，**仅当** `realpath ≠ 展开后的路径` 时附上；主位仍是"配置里写的那条路径" | 行为（消息文本）。**必要性已实测**：探针用未 realpath 化的 `/var/…` 临时目录时该后缀确实出现；若只报 realpath 结果，既有门 `:6975`/`:7025` 的"拒因必须含完整原路径"断言会在这类环境下假红 |
| `SKILL.md` docstring | 过时锚 `:1075` 改为符号化描述（真实位置是 F1 判定段，`:1075` 实为 `exam_board` 注释） | 措辞 |

**既有 16 个门的断言一行未改**，仅上述两处 docstring/注释措辞更正。

---

## 五-bis　round-2 整改（commit `4d21bc9b`，按 Codex round-1 结论 + 本卡自查）

> **起点是自查**：r1 还在跑的时候，我按自己在 docstring 里写下的不变量「装没装 PyYAML 不该改变身份绑定」对降级正则做了一次 27 条输入的对照，实测**4 条发散**（分隔符 TAB / 值含 `: ` / 值尾 `:` / 值尾 TAB —— 正则取到值而 PyYAML 对整份 config 抛 `ScannerError`）。r1 回来后报的 MEDIUM 与此**同源**，且多出 3 种我没想到的**结构**形态。两边合并成一次整改。

| # | 改动 | 来源 | 位置 |
|---|---|---|---|
| 1 | 降级正则收紧：分隔符只认 SP，值内禁 TAB 与冒号 | 本卡自查（4 条） | `SKILL.md` `_degraded_scan` 的 `_canon` |
| 2 | 含 `harness_tree` 的行若带 YAML 当换行的字符（U+0085 / U+2028 / U+2029 / VT / FF / FS / GS / RS）⇒ 拒 | Codex r1 MEDIUM | 同上 `_breaks` 判据 |
| 3 | 规范行后跟**续行** ⇒ 拒（PyYAML 会折叠成一个值，逐行扫描只看到前半） | Codex r1 MEDIUM | 同上 `_await_cont` |
| 4 | 任何含 `harness_tree` 而非那一种写法的行（含流式映射）⇒ 拒；判据从「像键的正则」改为「这一行提到了这个词」 | Codex r1 MEDIUM | 同上 |
| 5 | `os.path.realpath(..., strict=True)`，`OSError` 落到既有「树不存在」拒因 | Codex r1 LOW② | `SKILL.md` realpath 处 |
| 6 | docstring：三条分界**限 PyYAML 在的那条分支**；降级分支只有「无键 ⇒ 回退 / 其余 ⇒ fail-closed」两态 | Codex r1 Q2 | `_harness_tree` docstring ⚠️ **已被 §五-septies 取代**：降级分支整段删除，缺库只剩「拒写」一种结局 |
| 7 | 降级门控制组补「先弄坏缺省回退目标 + 断言账本恰 1 行」 | Codex r1 LOW① | `..degraded_noncanonical_is_fail_closed` |
| 8 | 降级 fail-closed 门 +3 结构参数（U+0085 / 续行 / 流式映射） | Codex r1 MEDIUM | 同上 |
| 9 | 探针 `finally` 改为哨兵记录原模块对象后按原样放回，不再只 `del` | Codex r1 Q5 | `_run_writer_no_yaml_at_harness_tree` |
| 10 | **新门** `..degraded_never_diverges_from_yaml`（40 参数） | 不变量本身 | 测试文件末 |

### 五-bis.1　新门为什么比「正则 vs PyYAML 对照表」强

收紧后的**正则本身仍然匹配** `harness_tree: /a/b<U+0085>`——真正拦住它的是扫描器里跑在
`_canon.match` **之前**的换行字符判据。只测正则会漏掉这一整族（本卡实测踩过这一脚）。
故新门用 `ast` 从写点里**逐字抽出** `_harness_tree` 本体，对同一份 config 分别以「yaml 可用」
与「`sys.modules['yaml'] = None`」各调一次，比较**结局**：

- 允许：两次结局完全相同（同一棵树 / 同一句拒因，拒因里带着各自解析出的路径）；
- 允许：降级侧是一个**点名 PyYAML 的拒绝**（认得窄 ⇒ 停下说话）；
- 禁止：两侧返回不同的树；禁止 PyYAML 拒了而降级侧放行。

### 五-bis.2　负控③（新门非 no-op）

把 SKILL.md 还原到 `f7f10be4`（收紧前）⇒ 新门 **红 11 条**，正是「自查 4 条 + 结构 7 条
（NEL×2 / LS / PS / 续行×2 / 流式映射）」。`neg3_pytest_rc=1`；trap 还原后 sha 与跑前逐字同
（`7ddba349…`）。存档 `evidence-harness-tree/negctl-invariant-20260914T203127.txt`。

### 五-bis.3　round-2 全量判据

| 判据 | 结果 | 存档 |
|---|---|---|
| `-k harness_tree` | **74 passed** rc=0（16 既有 + 6 M + 12 降级 + 40 不变量） | `g3_2-harness-close-r2-20260914T203447.txt` |
| 整文件 | **223 passed** rc=0（= 165 基线 + 58 新 nodeid，零本卡新红） | `g3_2-fullfile-close-r2-20260914T203447.txt` |
| `tests/skills` 目录级 | **546 passed** rc=0 | `skills-close-r2-20260914T203331.txt` |
| ruff（HEAD 口径） | `files=2` / `check_rc=0` / 两文件 `head_fmt_rc=0`、`base_fmt_rc=0` | `ruff-territory-r2-20260914T203833.txt` |
| 地盘核 | 仍恰三文件 | 同上 |
| 指纹再同步 | `MANAGED_FILE_DIGESTS` `6f53bb50…` → `7ddba349…`；`TMP_BLOCK_BASELINE` `B229` `664dd4d8…` → `094c1c37…`；`QUIZ_ANSWER_BASELINE` 计数仍 4/4 未动 | `skills-close-r2-…txt` |

---

## 五-ter　round-3 整改（commit `e844d6a1`，按 Codex round-2 结论 + 本卡按类别自查）

> **结论级变化**：round-2 的三条 MEDIUM 与我自查出的文档标记缺口指向同一件事 —— 逐行扫描
> 先天缺两样东西：**它不知道 YAML 在哪里换行**，也**不知道自己看的这一行处在什么语法上下文里**。
> round-1 补了一批正则、round-2 又找出一批，这正是本卡开头就写下的那个判断（「正则追不上 YAML
> 的合法形态」）在降级分支上重演。所以 round-3 不再补正则，**把降级分支从「尽量读懂」改成
> 「读不懂就停」**：整份文件里只要出现任何一种本函数推不动的 YAML 写法，当场 fail-closed。
> Codex round-2 的 Q3 给出的正是这个建议（「要么约束整份配置语法，要么缺库时明确拒绝解析」）。

| # | 改动 | 来源 |
|---|---|---|
| 1 | 换行类字符判据**前移**到「跳过空行 / 整行注释」之前 | Codex r2 MEDIUM-1 |
| 2 | 反斜杠 ⇒ 拒（双引号键里的转义能还原出同一个键，而原文不含那串字符） | Codex r2 MEDIUM-2 |
| 3 | 文档标记 `---` / `...`（非首个内容行）⇒ 拒 | **本卡自查** |
| 4 | 指令行 `%` / 锚点 `&` / 别名 `*` / 标签 `!` / 合并键 `<<:` / 流式括号 `{` `[` / 块标量 `\|` `>` / 一行内成奇数个的引号 ⇒ 全拒 | Codex r2 MEDIUM-2/3 |
| 5 | `_breaks` 改 `chr()` 拼装（见 §五-ter.2） | **本卡自查** |
| 6 | docstring：降级分支是**三态**不是两态；并写明「不做整份语法校验」这半条不保证 | Codex r2 LOW-1 |
| 7 | 不变量门 +9 参数 ⇒ **49 参数** | 上述各条 |

### 五-ter.1　自查怎么找到文档标记这条

按 Codex Q0 要我核对的六类来源，我自己先跑了一遍 12 类 YAML 特性的双分支对照
（`scratchpad/cov_audit.py` 形态，结果落在 §五-ter.3）。BOM / CRLF / 块标量 / 锚点 / 别名 /
前置 `---` / 重复键 / 嵌套键 / 标签 共 10 类是「相同」或「降级更窄（允许）」，**只有文档标记
两条违反不变量**：`safe_load` 只收单文档、见第二个就整份拒，而逐行扫描看不见文档边界，会把
**第二份文档里**的那行当成有效值（实测 PyYAML 抛 `ComposerError` 而降级取到了 `/c/d`）。

⛔ 修法不能以「有没有这个键」为条件：一份**根本没有** `harness_tree` 的多文档 config，
yaml 侧同样整份拒、降级侧回退到缺省树 —— 同样是被禁的那个方向。已按无条件拒实现，
并专门加了一条 `"other: 1\n---\nmore: 2"` 的参数钉住这一点。

### 五-ter.2　修复代码自己带上了要消灭的那类字符（自查抓到）

上一版把 `_breaks` 写成字面量 `"\v\f\x1c\x1d\x1e\x85  "`，写文件的中间工具层把
` ` / ` ` **展开成了真字符**，于是 SKILL.md 里嵌进两个**不可见的换行类字符** ——
正是本函数要消掉的那一类东西出现在了修复代码自己身上。实测确认后改成
`"".join(chr(_c) for _c in (0x0B, ..., 0x2029))`，并在注释里写明理由。复核：全文换行类真字符 = **0**，
`_breaks` 的实际字符集不变（8 个）。

### 五-ter.3　按来源分类的自查结果（12 类）

| 来源 | 结果 |
|---|---|
| BOM 开头 / CRLF / 重复键 / 前置 `---` | 两侧**相同** |
| 块标量 `\|` `>` / 锚点 `&` / 别名 `*` / 标签 `!!str` / 键缩进嵌套 | 降级**更窄**（允许） |
| **多文档 `---` / 文档结束 `...`** | ⛔ **违反不变量**（已修，见上） |

### 五-ter.4　负控④（新增 9 参数非 no-op）

还原到 `4d21bc9b`（round-2 版）⇒ 新参数中 **5 条变红**：3 条文档标记 + 转义键 + 多文档。
`neg4_pytest_rc=1`；trap 还原后 sha 与跑前逐字同（`9c4d7168…`）。
存档 `evidence-harness-tree/negctl-r3-20260914T205408.txt`。

### 五-ter.5　自查中修掉的两条**我自己写错的**测试参数

1. 转义键参数原写成 `"harness__tree"` —— 实测 PyYAML 给出的键是 **`harness__tree`（双
   下划线）**，不是目标键。转义应当**替换**那个下划线而不是再加一个；改成 `"harness_tree"`
   后 PyYAML 给出 `harness_tree` ⇒ 该参数这才真的测到东西（改前它在负控里不红，正是这个原因）。
2. `%YAML 1.1\n---\n…` 那条我原标注为「指令行」，实测 PyYAML 抛的是 `ComposerError`
   （「只收单文档」）而非指令语义 —— 标注已据实改写，不按「指令行」宣称。

### 五-ter.6　round-3 全量判据

| 判据 | 结果 | 存档 |
|---|---|---|
| `-k harness_tree` | **83 passed** rc=0（16 既有 + 6 M + 12 降级 + 49 不变量） | `g3_2-harness-close-r3-20260914T205708.txt` |
| 整文件 | **232 passed** rc=0（= 165 基线 + 67 新 nodeid） | `g3_2-fullfile-close-r3-20260914T205846.txt` |
| `tests/skills` | **546 passed** rc=0 | `skills-close-r3-20260914T205708.txt` |
| ruff（HEAD 口径） | `check_rc=0`、两文件 `head_fmt_rc=0` / `base_fmt_rc=0` | `ruff-territory-r3-20260914T205846.txt` |
| 地盘核 | 仍恰三文件 | 同上 |
| 指纹再同步 | SKILL.md `7ddba349…`→`9c4d7168…`；`B229` `094c1c37…`→`c8120a7b…` | `skills-close-r3-…txt` |

---

## 五-quater　round-4 整改（commit `34451227`，按 Codex round-3 结论 + 本卡自查）

Codex round-3：BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1。**三条整改、一条登记不修、LOW 登记**。

| # | round-3 结论 | 处置 |
|---|---|---|
| MEDIUM-1 | Unicode 空白从续行检查旁边溜过去（**与本卡自查同一条**） | ✅ 修 |
| MEDIUM-2 | 首个文档标记整行早退会吞掉同行配置；连续起始标记 / 开头结束标记未更新文档状态 | ✅ 修 |
| MEDIUM-3 | 整行引号计数证不出引号是否闭合 | ⚠️ **登记不修**（见下） |
| MEDIUM-4 | 非换行类 YAML 非法字符未被拒，且不只导致「无键回退」 | ✅ 修 |
| LOW-1 | 57 参数门对新增三组判据失效不敏感 | ⚠️ **登记**（见下） |

### 五-quater.1　MEDIUM-1：同一个函数里「什么算空白」两处口径不一致

`_cl.strip()` 按 **Unicode** 空白判空行，续行判据 `_cl[:1] in (" ", "\t")` 只认 **ASCII** ⇒
全角空格 / NBSP 起首的行**既不算空行也不算续行**，被整个跳过，降级照样采用前一行的值，
而 PyYAML 对整份报解析错。修法：空行判定收窄到 `strip(" \t")`（YAML 的 s-white 口径），
续行判定放宽到 `_cl[:1].isspace()`。

⚠️ **这与 SKILL.md 里 round-3 记下的老教训是同一条**：「同一个函数里几处判据必须同口径，
否则『哪些字符算空白』会随代码路径而变」。当年在正则实现上踩过，这次在降级扫描里又踩了
一次 —— 值得作为一条独立的工程教训登记。

### 五-quater.2　MEDIUM-4：非换行类非法字符

别的字段里放一个 U+0001，PyYAML 整份 `ReaderError`，而逐行扫描照样返回那棵树。修法：
新增 `_nonprint` 判据，**逐字抄 PyYAML 自己 `reader.py` 的 NON_PRINTABLE 字符集**，与
`_breaks` 互补 —— 那八个是「合法但会断行」的，这个是「压根不合法」的。

### 五-quater.3　MEDIUM-3：登记不修的理由（这是一个产品取舍，不是技术难点）

用「一行里引号成不成对」当跨行引号标量的判据，**证不出引号闭没闭合** —— 普通值里的字面
引号与跨行标量的定界引号恰好凑成偶数时就会放行。堵死只有两条路：

1. 在降级分支里塞进一个**真正的词法分析器** —— 那就是把 PyYAML 重写一遍，与本卡的结论
   （「正则追不上 YAML」）自相矛盾；
2. 缺库时**对含任何引号的 config 一律拒** —— 现网 `.canvas-config.yaml` 里就有引号
   （`vault_id: "canvas_vault"` 等），这等于「缺库机器上 quiz-answer 一律拒写」。

第 2 条其实与实测事实一致（缺库机器上更下游的 `_vault_id_of` 本来也会 fail-closed），但它是
一个**用户可见的行为决定**，超出本卡「重做解析」的范围。⛔ 因此 docstring 已就地写明：
「绝不采用一棵 PyYAML 不会给出的树」这句话**在这一个盲区上尚未被证明**，不得当成已证结论
引用。**移交主 session 裁：走第 2 条（缺库即拒写）还是维持现状（登记盲区）。**

### 五-quater.4　LOW-1：不变量门结构上测不到「过度拒绝」

门的允许条件是「两侧结局相同 **或** 降级侧是点名 PyYAML 的拒绝」。于是**任何**多余的拒绝
判据都落在「允许」里 —— 删掉指令行 / 八符号 / 奇数引号三组判据，57 条参数仍全绿（Codex
内存实测）。这是门的**结构性**局限，不是参数选得不好：要钉住「这条判据还活着」，需要的是
变异测试（逐条删判据看哪条门变红），不是再加参数。登记，建议另立卡。

### 五-quater.5　Codex round-3 对我 prompt 的两处更正（已采纳）

1. 我在 Q1 里举例说「注释里有单个引号会被拒」—— **错**：整行注释在奇偶计数之前就被跳过，
   只有**内容行的尾注释**才参与计数。
2. Q3：`_breaks` 八个字符里 VT/FF/FS/GS/RS 在 PyYAML 里是**非法字符而不是换行**；集合对
   「换行」这一类无遗漏，但对「非法字符」这一类不完整 —— 这正是 MEDIUM-4 的由来，已由
   `_nonprint` 补齐。

### 五-quater.6　round-4 全量判据

| 判据 | 结果 |
|---|---|
| `-k harness_tree` | **91 passed**（16 既有 + 6 M + 12 降级 + 57 不变量） |
| 整文件 | **240 passed**（= 165 基线 + 75 新 nodeid） |
| `tests/skills` | **546 passed** |
| ruff | `check_rc=0`、两文件 `head_fmt_rc=0` / `base_fmt_rc=0` |
| 地盘核 | 仍恰三文件 |
| 负控⑤ | 还原到 `e844d6a1` ⇒ 新增 8 参数中 **5 条变红**（4×M-1 + 1×M-4）；3 条文档标记参数两版都通过（已被既有 `_seen_content` 判据覆盖）——**如实记录，不宣称 8 条全都有区分力** |
| 不可见字符 | 本卡引入 **0**；文件里仅剩两个 U+FEFF 是 `08100483` 既有、在 `^﻿?---` 正则里有意为之 |
| 指纹再同步 | SKILL.md `9c4d7168…`→`035b22bb…`；`B229` `c8120a7b…`→`8b8ce50d…` |

> ⚠️ 存档 `negctl-r4-*.txt` 的标题行因复用上一轮脚本、`sed` 只替换了编号，正文仍写「round-3
> 新增的 9 条参数」—— 实际测的是 round-4 新增的 8 条。如实登记，不重跑。

---

## 五-quinquies　round-5 整改（commit `4eeaeaa6`，按 Codex round-4 结论）

Codex round-4：B 0 / H 0 / M 2 / L 2。**它对本卡三条登记的反驳全部成立，逐条接受。**

### 五-quinquies.1　LOW-1：我的登记理由是错的

我写「门的允许条件把『降级更窄』一律放行 ⇒ 结构上测不到判据失效 ⇒ 必须另立变异测试卡」。
**漏掉了一点**：判据一删，降级就比 PyYAML **更宽**，于是落进「违反」而不是「更窄」。
按复核方给的配方逐变体实测（`scratchpad/low1_verify.py` 形态：完整实现 vs 删掉某一组判据），
三条孤立输入构成一条**对角线** —— 每条只让**一组**判据的删除变红：

| 输入（接在 fixture header 之后） | PyYAML 侧 | 只让哪一组判据的删除变红 |
|---|---|---|
| `%FOO bar` + 规范行 | `ParserError` | 删-指令行 |
| `note: *undefined` + 规范行 | `ComposerError` | 删-八符号 |
| `note: "unclosed` + 规范行 | `ScannerError` | 删-奇数引号 |

三条已入门 ⇒ **57 → 60 参数**。原「另立变异卡」的台账条目**作废**。

### 五-quinquies.2　MEDIUM-1/2：盲区表述从「尚未证明」改为「已有反例」

复核方内存跑真函数确认：存在一份 config，PyYAML 走回退而本函数**采用了另一棵存在的树**。
所以正确表述是「已有反例」，不是我原来写的「尚未被证明」。**这个区别很重要** —— 前者是
「已知会错，只是决定先不修」，后者听起来像「大概没事」。docstring 已就地改正。

同时补上原先漏掉的一半（round-4 MEDIUM-2）：盲区**不只导致「判成无键而回退」**。别的字段里
有生成不出来的隐式类型、不可哈希的复杂键、块结构错误时，PyYAML 整份拒（ValueError /
ConstructorError / ParserError / ScannerError），而本函数跳过非目标行、**照样采用**目标行那棵树。

### 五-quinquies.3　LOW-2：`_breaks` 的说明错了

八个字符里只有 U+0085 / U+2028 / U+2029 是 PyYAML 的**换行**；VT / FF / FS / GS / RS 是它的
**非法字符**（报 ReaderError），与 `_nonprint` 重叠。拦截行为本身正确，但不能笼统说成
「合法但会断行」。已据实更正。

### 五-quinquies.4　仍然登记不修的两条（移交主 session 裁）

两处盲区的堵法只有两条，都超出本卡范围：
1. 在降级分支里塞进一个真正的 YAML 词法/对象生成分析器 = 把 PyYAML 重写一遍，与本卡结论自相矛盾；
2. 缺库时**对含任何引号或任何非平凡结构的 config 一律拒** —— 与实测一致（缺库时更下游的
   vault 归属绑定本来也会 fail-closed，**保守拒不会损失任何一次原本能完成的写入**，这一点
   复核方明确认可），但它是**用户可见的行为决定**。

⛔ **建议主 session 直接裁第 2 条**：复核方已指出「按此前提，提前保守拒绝不会损失一次原本
能完成的写入」，代价只是缺库机器上的错误信息从「vault 归属无法绑定」变成「请装 PyYAML」。

> ⚠️ **本段的建议理由随后被实测证伪、但结论被用户采纳** —— 见 §五-septies。那句「不会损失
> 任何一次原本能完成的写入」是**假的**（三向对照有反例）。用户是在知道真实代价之后仍裁定
> 走拒写的，理由换成了「可见的拒绝好过静默地绑错一棵树」。**引用本段时必须连这条更正一起引。**

### 五-quinquies.5　round-5 全量判据

| 判据 | 结果 |
|---|---|
| `-k harness_tree` | **94 passed**（16 既有 + 6 M + 12 降级 + 60 不变量） |
| 整文件 | **243 passed**（= 165 基线 + 78 新 nodeid） |
| `tests/skills` | **546 passed** |
| ruff | 先 `head_fmt_rc=1`/`base_fmt_rc=0`（本卡引入）⇒ `ruff format` 后两项均 0；format 的 5 处 hunk 全在本卡改动区 |
| 地盘核 | 仍恰三文件 |
| 指纹再同步 | SKILL.md `035b22bb…`→`784a1cfc…`；`B229` `8b8ce50d…`→`7fae3bc3…` |

---

## 五-sexies　round-5 结论与收口（轮次上限 5/5）

Codex round-5（绑最终 HEAD `4eeaeaa6`）：**BLOCKER 0 / HIGH 0**，MEDIUM 2 / LOW 3。
⇒ **D-15 通过条件满足**（绑最终 HEAD 的一轮 B=0、H=0），轮次用满 5/5。

它确认：**「两处盲区按『已有反例、登记未修』移交准确」**，并对 MEDIUM-1/2 各自独立内存复现。

### 五-sexies.1　按 D-32 做的纯措辞尾巴（commit 见 §九；逻辑零变化，可逐行等价核）

| # | round-5 结论 | 改了什么 |
|---|---|---|
| LOW-1 | `_breaks` 的说明**没全部改正**（常量处注释 + 错误消息仍统称「换行字符」） | 注释写清「只有 U+0085/U+2028/U+2029 是 PyYAML 的换行，VT/FF/FS/GS/RS 是它的非法字符、与 `_nonprint` 重叠」；错误消息改为「YAML 当作换行、或直接判为非法的字符」 |
| LOW-3 | 「堵死只有两条路、否则等于重写 PyYAML」**不是准确的技术穷举** | ⚠️ **我把它写成了假二分**。据实补上至少还有两条：③ 缺库时**直接明确退出**，压根不进解析 —— 就不必判引号也不必判「非平凡结构」；④ 只认一个**明确限定的极小文档子集**并把那个子集完整验证到底 —— 那不等于重写整个 PyYAML。「把选项说窄了会让后面的人以为没得选」 |

⛔ 这两处都是 SKILL.md 的**注释 / docstring / 错误消息文本**，控制流零变化，走 D-32（不占轮次、不重置）。
连带只有两处机械后果：`MANAGED_FILE_DIGESTS` `784a1cfc…`→`5c7df579…`、`B229` `7fae3bc3…`→`f7536167…`。

### 五-sexies.2　LOW-2：登记不修（已到轮次上限，改测试需第 6 轮）

三条文档标记参数**测不到「文件首标记」那一半**：门的固定配置头在标记之前就把 `_seen_content`
置真，于是删掉「标记同行内容」检查或 `_doc_started = True` 后，60 条参数仍全绿（复核方实测）。
它们仍能测「内容之后的文档标记」，但证不到本卡 round-4 对**首标记状态**的那部分修复。

**修法（留给下一张卡）**：给不变量门加一个「整份文档」模式的参数入口（另一道门
`..degraded_noncanonical_is_fail_closed` 已有 `_mode="whole"` 的先例），用不带配置头的整份文本
作参数。**本卡不做** —— 轮次已到 5/5，改测试代码需再送一轮，按合并门 §1 登记不阻断。

### 五-sexies.3　最终判据（工作树态，HEAD = `4eeaeaa6` + D-32 尾巴）

| 判据 | 结果 |
|---|---|
| `-k harness_tree` | **94 passed**（16 既有 + 6 M + 12 降级 + 60 不变量） |
| 整文件 | **243 passed**（= 165 开工基线 + 78 新 nodeid，零本卡新红） |
| `tests/skills` | **546 passed**（= 开工基线数） |
| ruff | `check_rc=0`；两文件 `head_fmt_rc=0` / `base_fmt_rc=0`；验伪锚 format rc=1、check rc=1 |
| 地盘门 | 恰 **3 文件**；验伪锚去掉 exclude 多出 **35** 条 `_bmad-output/`；`backend/app` **0** |
| 硬边界 | 本卡新增 **783** 行中 `fsrs_bridge` / `decay_beta` / `7691` / `7687` / `lancedb.connect` / live vault 绝对路径 **各 0** |
| W4 哨兵 | 每次目录级跑均 `blocked=0, advisory=0, unaccounted=0` |

---

## 五-septies　用户裁定后的新增范围：缺 PyYAML 即拒写（commit `faaeb005`）

> ⛔ 本节记的不只是「做了什么」，还有**一条我给用户的论据被实测证伪**。两者在文档里分量不同：
> 「未证明」读起来像「大概没事」，「已证伪」是「已知会这样」。这一条属后者。

### 五-septies.1　裁定与它的前提

我在 round-5 收尾时向用户建议「缺 PyYAML 时干脆拒写」，论据是复核方认可的一句话：
**「保守拒不会损失任何一次原本能完成的写入」**（因为缺库时更下游的 vault 归属绑定本来也会
fail-closed）。用户据此裁定「是」。

**在据此删代码之前，我用一个 9 agent 的工作流独立验证了这个前提 —— 它被推翻了。**

四路独立判定（静态 / 真跑 / 调用图 / 专门反驳），2/4 支持、2 条反例。裁定意见：
**全称形式为假，条件形式为真**。

### 五-septies.2　三向对照实测（我本人复现，非转述）

复现脚本已入库：`_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py`。
解释器 = `/opt/homebrew/bin/python3 -S`（py3.14，`find_spec("yaml") is None`，零足迹，
**不是** PYTHONPATH 注入 —— 复核方指出注入法在某些树布局下可被 `sys.path.insert` 遮蔽）。

| | 解释器 | `harness_tree` | rc | 账本 | mastery |
|---|---|---|---|---|---|
| **A** | 真缺 PyYAML | → 本仓 `b85a168a` 旧树 | **0** | **1 行** | 0.5 → **0.57** |
| **B** | 真缺 PyYAML | 无（回退到当前树） | 1 | 0 | 不变 |
| **C** | 有 PyYAML | 无（回退到当前树） | 0 | 1 行 | 0.5 → 0.57 |

A vs B 把因果钉在 **harness_tree** 上；B vs C 把因果钉在 **PyYAML** 上；C 证明夹具本身有效
（B 的失败不是夹具坏了）。旧树 `b85a168a` 的 `validate_learning_events.py` 实测 `import yaml`
计数 = **0**，其 `_vault_id_of` 是正则白名单解析。

⇒ **「缺库时下游本来也会拒」不是写点的性质，而是 `harness_tree` 选中那棵树的性质。**
而 `harness_tree` 是部署侧可写的运行期自由变量，本函数在拒绝的那一刻，结构上无从知道
自己是不是丢掉了一次本来能完成的写入。

### 五-septies.3　用户在知道代价后的重新裁定

我带着这个更正回去问，用户重新裁定：**仍走拒写**。理由（我在选项里写明、用户选定）：
本函数一以贯之的取向是「**可见的拒绝**好过**静默地绑错一棵树**」，且前者可恢复（装上
PyYAML 就好）、后者用户无从察觉。

⛔ **此后任何地方都不得再引用「保守拒无代价」。** 正确表述：「代价 = A 那一类场景，
已实测、可复现（脚本已入库）、可恢复。」

### 五-septies.4　代码改动

`_degraded_scan` **整段删除**，`except ImportError` 直接 `raise SystemExit` 点名 PyYAML。
净减 **134 行**（`_harness_tree` 从 224 行降到 90 行）。PyYAML 可用时的行为**零变化**。
代价与三向实测已逐字写进该函数 docstring —— 谁想把降级加回来，得先读那一段。

### 五-septies.5　⚠️ 顺带抓到一个假门（这是本节第二件要紧事）

删掉降级解析后，原来那道 60 参数的核心不变量门（「缺库分支要么与 PyYAML 同值、要么更窄」）
**一条参数不改就全绿** —— 因为降级恒拒 ⇒ 每条都落进「更窄」那一档 ⇒ **无论实现对错都绿**。

这正是我在 round-5 §五-sexies 里担心过、并专门让复核方查的那件事，这次真的发生了。
**一个曾经能抓东西的门，会因为被守护对象的形态改变而悄悄退化成恒真** —— 而它表面上还是绿的。

换成更强也更简单的断言：**缺库时对任何 config 都不返回任何树，一律抛且点名 PyYAML**。
负控⑥（还原到 `4eeaeaa6`，含降级解析）⇒ **12 条变红**，证明新门非 no-op。
存档 `evidence-harness-tree/negctl-r6-failclosed-*.txt`。

### 五-septies.6　门重构（4 → 2 + 1 重写）

| 门 | 处置 |
|---|---|
| `..._degraded_canonical_form_still_works` | 删，语义反转 ⇒ 新 `..._no_pyyaml_refuses_canonical_form_accepted_cost`：连最规范写法也拒；**配对控制组**（有 PyYAML ⇒ rc=0 + 账本 1 行）证明这份 config 本来写得成 ⇒ **把我们明知接受的代价钉在测试里** |
| `..._degraded_absent_key_still_falls_back` | 删，语义反转 ⇒ 新 `..._no_pyyaml_refuses_even_without_the_key`：老布局 vault 在缺库机器上也拒。理由：「有没有这个键」本身就得解析 YAML 才判得出，缺库时不可证 |
| `..._degraded_noncanonical_is_fail_closed`（9 参数） | 折叠 —— 其形态已全部在 60 参数 unit 层覆盖（此声称已列进 r6 prompt 请复核方独立核对） |
| `..._degraded_unicode_space_is_fail_closed_too` | 同上折叠 |
| `..._degraded_never_diverges_from_yaml`（60 参数） | 重写为 `..._no_pyyaml_never_returns_a_tree`，断言换强；参数表逐条保留（它们仍是「曾经真的让两条分支分叉过的形态」的回归表） |

### 五-septies.7　行为变化（用户可见）

**老布局 vault（没写 `harness_tree` 键）在缺 PyYAML 的机器上，从「照常写入」变成「拒写并
要求装 PyYAML」。** 这是本次裁定里对用户最可见的一半，已由
`..._no_pyyaml_refuses_even_without_the_key` 钉住。

⚠️ 另有一条**不属本卡、但用户会看到**的事实（callgraph 路发现，静态）：缺库时净效果**不是
「什么都没写」** —— Step 3 早已由 Claude 用 Edit 把分数写进检验白板（`status:
scored_pending_node_update`），主写点块之前还会建 `.locks` 锁文件。所以缺库用户看到的是
**一张记了分但节点没更新的半态白板**。登记，另立卡评估。

### 五-septies.8　判据

| 判据 | 结果 |
|---|---|
| `-k harness_tree` | **84 passed**（16 既有 + 6 M + 2 新端到端 + 60 不变量） |
| 整文件 | **233 passed** |
| `tests/skills` | **546 passed** |
| ruff | `check_rc=0`；format 先红（本卡引入）⇒ `ruff format` 后两项均 0 |
| 地盘核 | 仍恰三文件；`backend/app` 0 |
| 负控⑥ | 还原到 `4eeaeaa6` ⇒ 新不变量门 **12 条红** |
| 不可见字符 | 本卡引入 0 |
| 指纹 | SKILL.md `5c7df579…`→`f52a5946…`；`B229` `f7536167…`→`8d5ce8d4…` |

---

## 五-octies　变异测试：13/25 存活，门被逼着补了一轮（2026-09-15）

> r5 的 LOW-1 说「要钉住判据还活着，需要的是变异测试」；我当时判「另立卡」，Codex r4 说
> 「补参数就行」。**实测下来两边各对一半**：3 条哨兵参数确实杀掉了 3 组判据的删除（r5 做了），
> 但**光靠加参数猜不出夹具形状的缺口** —— 那要系统性变异才看得见。这次补上了。

### 五-octies.1　怎么跑的

12 个 agent、25 个「似是而非的错误实现」，五个角度各提一批（偷偷把降级加回来 / 静默回退 /
消息不对 / 部分拒绝 / 改有库那一侧），逐个在**内存里**打到 `_harness_tree` 上再跑门。
⛔ 全程不碰仓库文件（当时 Codex r6 正在只读审这棵树）。

**结果：25 个变异体，13 个存活，0 个无效。** 每个存活者都附了**阳性对照**（证明该分支不是
死代码，喂对输入它真的会开口）与**反向证伪**（例如把环境变量指向真树后复跑，60 条参数
**全部**返回那棵树）。

⚠️ 如实记：`parallel[5]` 那一组 agent 卡死（6 次尝试无进展），**还有一批变异体没评上**；
综合那一步也因登录刷新失败没跑成，裁定由我本人补做。所以「25 个」不是穷举。

### 五-octies.2　存活的根因：不是参数不够，是**夹具形状太窄**

那 60 条 config 彼此太像，于是整类错误实现从门下面走过去：

| 根因 | 哪一类实现能躲过 |
|---|---|
| 每条都带同一个引号注释头 | 「只解析简单 config」的降级 |
| 目标路径**没有一条真实存在** | 「先试着解析、树真存在就用」——`realpath(strict=True)` 恒 OSError，这条判据在门内**结构上跑不到** |
| 每条都**有** config 文件 | 「文件不存在就静默回退」 |
| 父目录从来不是一棵树 | 「父目录是树就用它」——而那正是 docstring 明说的**老布局常态** |
| 门从不设环境变量 | 一条 `*_HARNESS_TREE` 后门，**完全绕过 config** |
| 每条都用全新 tmp | 「把上次解析结果缓存进 sidecar」——用户改了 config 而系统装作没看见 |
| 探针只造一种缺库 | `sys.modules["yaml"]=None` 抛的是 `ModuleNotFoundError`，于是把 `except ImportError` **收窄**成它照样全绿 |
| 消息判据只查 `"PyYAML" in msg` | 把两条拒因合成一个模板、把缺库说成 config 有毛病 |

最危险的一个是 `R3-try-then-refuse`：它的阳性对照**复现了 docstring 自己那条反例** ——
多文档 config 下 PyYAML 整份 `ComposerError` 拒，而变异体返回了树 A。

### 五-octies.3　据此补的门

| 新门 | 维度 | 杀哪一类 |
|---|---|---|
| `..._no_pyyaml_refuses_across_fixture_shapes` | **7 形状 × 2 缺库方式 = 14 格** | 上表前 7 行 |
| 同上的 `plain_import_error` 维（monkeypatch `builtins.__import__` 抛**普通 ImportError**） | — | `except` 子句收窄（真实场景：PyYAML 装着但 C 扩展 `_yaml` 版本错配） |
| 60 参数门的消息判据 | 只查子串 → **锚整句**（与两道端到端门共用同一常量） | 消息模板合并 |

⛔ 每一种形状都**特意把诱惑摆好**：目标树是真的、父目录是真的、环境变量指着真树、sidecar
里写着真树 —— 任何肯读它们的实现都会立刻返回一棵树而不是拒。这才叫有区分力。

### 五-octies.4　验证新门真能杀（不验就只是信仰）

脚本入库：`_bmad-output/审查/evidence-harness-tree/verify-new-gates-kill-mutants-20260915.py`
（自证：任一格不符即非零退出）。

**KILLED 9/9**，且每个变异体被**为它设计的那一格**抓住（一条干净的对角线）：

```
R3-try-then-refuse     → target_tree_really_exists
R6-env-override        → env_override_set
M1-parent-is-a-tree    → parent_is_a_usable_tree
R4-sidecar-cache       → sidecar_present
R5-json-superset       → pure_json_config
R1-simple-config-only  → minimal_unquoted_config
P2-open-before-import  → no_config_file
WM-narrow-except       → plain_import_error   ← 只有第二探针那一维抓得住
WM-merge-message       → 整句锚（14 格全抓）
```

**阴性对照**：生产代码本身 14 格全绿 ⇒ 新门无误伤。

### 五-octies.5　顺带被新门抓到的一个自引缺陷

给拒因加上 `sys.executable` 之后，**14 条新门齐刷刷 `NameError: name 'sys' is not defined`**。
生产没问题（写点顶部 import 了 `sys`），错的是 `_extract_harness_tree()` 的命名空间只放了
`{os, re}` —— **测试夹具与被测代码的 import 面漂了**。
已改成**逐字取写点在 `def _harness_tree` 之前的顶层 import** 来构造命名空间，并加断言
「缺 os/re/sys 任一即当场停」。这样生产以后再多 import 什么，夹具自动跟上，不用人去追。

### 五-octies.6　判据

| 判据 | 结果 |
|---|---|
| `-k harness_tree` | **102 passed**（16 既有 + 6 M + 2 缺库端到端 + 1 flow 文档 + 3 采用门 + 14 形状门 + 60 不变量） |
| 整文件 | **251 passed** |
| `tests/skills` | **546 passed** |
| 变异验证 | KILLED 9/9，阴性对照 14 格全绿 |
| ruff | check + format 均 0 |
| 地盘核 | 仍恰三文件 |
| 指纹 | SKILL.md `f52a5946…`→`f708913c…`；`B229` `8d5ce8d4…`→`543e37de…` |

---

## 六 4-B　用户侧（零技术词）

配置里指到学习引擎的那行，就算写法略有出入或路径拐了个弯，系统要么照正确的那棵读、要么直接说
「这儿写错了」，再也不会悄悄读错地方——我感觉终于放心了。

还有一种情况它现在也会当面说出来：如果这台机器少装了一个它读配置要用的东西，它不再"尽力猜着读"，
而是停下来告诉我缺什么、怎么补。我一开始觉得这样是不是太较真了，但想明白了——猜错的那次我根本
不会知道，而它停下来我一眼就看见、照着装上就好。

**felt-sense**：以前那种"它好像跑成功了，可我不确定它到底记到哪儿去了"的悬着的感觉没有了。现在只有两种
结局：正确地写进去，或者当着我的面停下来告诉我哪一行写错了、写的是什么、它实际找到的是哪里。中间那片
"看起来正常、其实记错了地方"的灰色地带被拿掉了。多出来的那点"它有时会拦住我"，换来的是我不用再
疑心它背着我记到了别处——这笔我换得很值。

---

## 七 本卡未证明什么（≥4）

1. **未证明真缺 PyYAML 机器上的端到端行为**。本机 venv 有 `yaml 6.0.3`，降级分支靠把缺库收窄到 `_harness_tree` 那一次调用来覆盖，是**分支级**覆盖。整进程实测另有结论（更下游 `_vault_id_of` 先 fail-closed，见 §2.2），两者各测一件事，都不等于"在一台真没装 PyYAML 的机器上跑过"。
2. **未证明 `harness_tree` 键在生产上已有写入方**。U3-B 写入端落地情况未验，当前真实触达面可能仍为 0 —— 也就是说本卡修好的这条路，目前可能还没有用户真的走过。
3. **未证明 `expanduser` 的展开契约**（无 `HOME` / 未知 `~user` / 空 `HOME`）。沿用 Python 默认，round-5 的 L 登记项仍未闭合。
4. **未证明 realpath 在极端边界上的行为**：循环 symlink、权限拒绝、跨文件系统、链指向相对目标、多重链嵌套。新门只覆盖"链在中间段 + 单层 `..`"这一种最长前缀式错指。
5. **未重新认证 `_run_writer_settled` 提取链与 G3-2 其余 150 个测试的设计**（Codex 每轮只限指定差分；整文件 180 passed 只说明没被本卡弄红）。
6. **未证明降级正则的接受面与 PyYAML 在所有输入上逐字同值**。只对本卡门覆盖的那些形态做了对照；"接受面窄于 PyYAML、但接受的都同值"是设计意图与抽样实测，不是穷举证明。这正是 Codex 问题 ⓪ 要问的。
7. **未证明 `tests/unit` 面不受影响** —— 本卡改动面不碰 unit，故按卡文未跑 `tests/unit` 目录级，也未引用 `unit-red-baseline-08100483.txt`。**本卡无 `tests/unit` 面**。
8. **未证明 lefthook 钩子实际跑过**：commit 时 lefthook 打印了 `core.hooksPath` 冲突提示（hooks 未安装到本仓 `.git/hooks`）。本卡改的两个 `.py` 的 `ruff check` / `ruff format --check` 由我**手工**按卡文 §二.8 逐文件对照基线跑过（`check_rc=0`、两文件 `head_fmt_rc=0`/`base_fmt_rc=0`），但这不等于 `python-lint` 钩子本身跑过。

9. **未穷举证明降级扫描的接受面 ⊆ PyYAML**。新门用的是一张 40 条的输入表（本卡自查 4 类 + Codex round-1 指出的结构 7 类 + 规范/边界若干），不是穷举。YAML 的合法形态空间远大于此；「收紧后再没有发散」只在这张表上成立。
10. **未证明 `strict=True` 对所有既有部署形态无回归**。只证了本文件 74 个 harness_tree nodeid + 整文件 223 全绿；真实部署里 `harness_tree` 触达面当前可能为 0（见第 2 条），没有线上样本可验。
11. **未证明降级分支新增的宽判据（`"harness_tree" in 行`）不会误伤真实 config**。它会把「某个无关键的值里恰好含这个词」的配置也拒掉。方向是 fail-closed（安全），但本卡没有真实 config 样本可测。
12. **未证明 lefthook 两次提交跑的是同一套钩子**：`f7f10be4` 那次打印了 `core.hooksPath` 冲突提示、看不到钩子输出；`4d21bc9b` 那次实际跑了（Ghost Files / Mutant-Scan / Python ruff lint 都有输出）。两次之间我没有改过 git 配置，差异原因未查。两次的 ruff 判据都由我手工按 §二.8 逐文件对照基线跑过。

13. **⛔ 已有反例, 不是「尚未证明」**：降级分支「绝不采用一棵 PyYAML 不会给出的树」这句话，在**两处盲区上已被复核方内存跑真函数复现出反例**（① 整行引号奇偶证不出闭合；② 别的字段里有生成不出来的隐式类型 / 不可哈希复杂键 / 块结构错误时，PyYAML 整份拒而本函数照样采用目标行那棵树）。登记不修，移交主 session。
14. **未证明「读不懂就停」判据集在类别层面完备**。round-5 的 Q0 仍列出两类未覆盖（块集合与普通标量结构、隐式类型解析与对象生成）。本卡的证据是 60 条输入表 + 按来源分类的人工核对，不是穷举也不是形式证明。
15. **未证明这些判据在真实 config 上的误伤率**。只核过现网 config「文档标记 = 0」，没跑过全量真实配置样本。
16. **门测不到「文件首文档标记」那一半**（round-5 LOW-2）：固定配置头让 `_seen_content` 先置真，删掉「标记同行内容」检查或 `_doc_started=True` 后 60 条参数仍全绿。修法已写在 §五-sexies.2，本卡到轮次上限未做。
17. **五份 Codex 存档均未独立复跑作者的 pytest 结果**（各轮结尾都写明）。94 / 243 / 546 只有作者自跑的存档为证。
18. **未证明 lefthook 两次提交跑的是同一套钩子**：`f7f10be4` 那次打印了 `core.hooksPath` 冲突提示、看不到钩子输出；`4d21bc9b` 起几次实际跑了。两次之间未改 git 配置，差异原因未查。各轮 ruff 判据均由我手工按 §二.8 逐文件对照基线跑过。

---

## 八 台账待登记条目（≥4）

1. **`_harness_tree` 四轮同族「静默换树」缺陷（M-a/M-b/M-c）已由本卡整体重做修复**：commit `f7f10be4`；新增 15 nodeid（清单见 §2.1）；既有 16 门保持绿；整文件 165 → 180 passed。
2. **地盘扩充已裁（R-B14-4）**：`backend/tests/regression/test_g3_2_review_ledger.py` 写它**已授权、非越界**。本卡是该文件本批**唯一写者**（T7-B 只验门不改、T7-C/T7-D 不碰、T8 短 goal 将其列为禁改门文件），集成冲突风险 0。出处 R-B14-4 + 手册 §一 `:69`。
3. **设计稿 §3/§4 本体尚未回写 R-B14-4**（`grep -c 'test_g3_2_review_ledger' <设计稿>` 至今 0），且 §4 T7-A「判据」只写 `tests/skills` + SKILL-PORT-LINT、漏了行为门所在面（`tests/regression`）。建议归档时回写或注明「以 R-B14-4 为准」。
4. **「既有 xfail → 去标」口径不成立**（16 门本就全绿无 xfail），本卡改为「新增 M 门先红后绿 + 既有保持绿」。见 §四.10。
5. **SKILL-PORT-LINT 三处基线随卡更新**：① `MANAGED_FILE_DIGESTS["skills/quiz-answer/SKILL.md"]` `c1588ec6…` → `6f53bb50…`；② `TMP_BLOCK_BASELINE["quiz-answer"]` 的 `B229:571eb660…` → `B229:664dd4d8…`（**卡文未列的第三道门**，见 §四.3）；③ `QUIZ_ANSWER_BASELINE` 计数**不变**（`tmp_all`/`claude_dir_ref` 仍 4/4），仅校正注释里的行号标注（见 §四.8）。
6. **docstring 内 `:1075` 过时锚已改符号化**（真实位置是 F1 判定段，现 `:1183`/`:1202`）。
7. **⚠️ 批级模板缺陷（建议回写协议 §2.2 / 手册）**：地盘验伪锚 `git diff --name-only … | grep -c '^_bmad-output/'` 在含中文路径的本仓**恒 0 = 假绿**，必须写 `git -c core.quotepath=false`。本卡已落两种写法的对照存档。见 §四.5。
8. **⚠️ 负控模板缺陷（建议回写协议 §2.2）**：EXIT trap 里用相对路径还原 + 脚本中途 `cd` = 还原静默失败；且 `( cmd | tail )` 外层取 `pipestatus` 会取到 `tail` 的 rc。两条都在本卡实际发生并被"跑后 sha 必须等于跑前"抓到。见 §四.9。
9. **降级分支在真缺库机器上不可达为成功路径**（更下游 `_vault_id_of` 同样要 PyYAML）。这条决定了"降级要不要宽容"的取舍——宽容换不来一次成功写入，只会换来猜错树。建议作为 G3-2 的一条结构性事实登记；是否让 `_vault_id_of` 也有降级路径，另立卡评估。
10. **既有 SyntaxWarning 未修（非本卡引入）**：`test_g3_2_review_ledger.py:6981` 的 docstring 含裸 `\s`，Python 3.14 每跑必告警、3.17 将成错误。位于本卡编辑的同一个 docstring 的相邻段，但不属"regex 专属措辞更新"范围，**本卡不顺手改**，登记供后续卡处置。
11. **Codex 各轮**：存档路径、绑定 SHA、B/H/M/L 计数 —— 见 §九。

12. **Codex round-1 的 MEDIUM 已整改、不是登记项**：按 §1 合并门 MEDIUM 本可登记不阻断，但它否定的是本卡的核心不变量（降级分支会绑到另一棵树），登记 = 让本卡的中心主张不成立。故整改并追加 round-2。**结论**：本卡 Codex 结论里**没有**「登记不修」的 MEDIUM/LOW。
13. **复核结论须逐字复测的又一实例**：Codex 的 U+0085 反例我第一次测成 `ScannerError`（因为我在 NEL 后面多加了一个字），差点判它报错；按它给的**逐字 repr** 重测才确认成立。流式映射那条则相反 —— 它的表述未限定「必须是整份文档」，实测接在本仓 header 之后是 `ScannerError`，范围比它说的窄。两条都记进 §九。
14. **本卡产出一条可复用的门形态**：「同一份输入、两条实现分支、结局只允许相同或其中一侧明确弃权」。它比「对照两个正则的捕获值」强一个量级 —— 后者会漏掉「拦截发生在正则之外」的整族。建议作为负控模板登记。

15. **⚠️ 工程教训（建议进工程坑索引）：同一个函数里「什么算空白」的口径必须一处定义**。SKILL.md 的正则实现在 round-3 就吃过一次（`\s` 连全角空格一起吃掉），本卡的降级扫描**又吃了一次**（裸 `.strip()` 按 Unicode 判空行 vs 续行判据只认 ASCII）。两次表现相同：某一类行「两头不沾」被整个跳过。
16. **⚠️ 批级模板缺陷（建议回写协议）：凡在文本里写 `\uXXXX` 转义，落盘后必须逐字复核**。本卡一天内被同一隐患咬**三次**、且三次是不同的工具层：① SKILL.md 的 `\u2028`/`\u2029` 被展开成**真的不可见换行字符**落进生产文件；② 测试参数 `\u005f` 少算一个下划线，使那条参数在负控里不红（测了个寂寞）；③ r3 prompt 的 `\u005f` 被展开，使其中一问变成自相矛盾的表述、该问那一轮没测到东西。**修法**：不可见字符一律 `chr(0xXXXX)` 拼装（本卡代码与新增门参数已全改），落盘后跑一次「不可见字符 = 0」复核。
17. **⚠️ 产品取舍移交主 session**：缺 PyYAML 时是否**直接明确退出 / 或对含引号与非平凡结构的 config 一律拒**。⛔ 复核方明确认可「按『下游同样需要 PyYAML』这个前提，提前保守拒绝**不会损失一次原本能完成的写入**」⇒ 实际代价只是错误信息从「vault 归属无法绑定」变成「请装 PyYAML」。**建议直接裁走这条。**
18. **⚠️ 另立卡**：不变量门加「整份文档」模式参数入口，补上「文件首文档标记」那一半覆盖（§五-sexies.2）。
19. **⚠️ 论证纪律教训**：本卡两次把「还有别的选项」说成了二分 —— ① LOW-1 我断言「门结构上测不到判据失效」，漏掉「判据一删降级反而更宽」；② LOW-3 我断言「堵死只有两条路」，漏掉「缺库直接退出」与「只认极小子集并完整验证」。两次都是**把自己想到的两条当成了全集**。
20. **Codex 轮次与存档**：r1 `f7f10be4` (0/0/1/2) → r2-p1 **0 字节被 cyber 拦**（prompt 问法落在任务边界上，按协议改写后重发）→ r2-p2 `4d21bc9b` (0/0/3/1) → r3 `e844d6a1` (0/0/4/1) → r4 `34451227` (0/0/2/2) → **r5 `4eeaeaa6` (0/0/2/3)，绑最终 HEAD、B=H=0、轮次 5/5 用满**。
21. **合并门口径下的本卡状态**：阻断级 = **0**（无数据丢失 / 无 live vault 或 7691 写入 / 无安全问题 / 无指定裁判红 / 无负控假绿）⇒ **可合**。

22. **⛔ 已立卡（用户 2026-09-14 裁定「另立必排卡」）：harness 树零契约校验**。写点从
    `harness_tree` 选中的那棵树**无条件导入 7 个名字**（`classify_card_state` / `_vault_id_of` /
    `_WHOLE_SECOND_RE` / `_looks_like_review_ext` / `validate_record_full` / `_golden_manifest` /
    `_TS_RE`），**零版本/契约校验**（实测在 `_harness_tree` 体内 grep `version|契约|compat|sha|cmp`
    = 0 命中），只有兜底 `except Exception → SystemExit`。⇒ 任意旧版/异版 harness 分发都会被
    **静默采用并按其语义写账本**。这是 §五-septies.2 那条反例得以成立的**结构根因**，面比降级
    解析的盲区大得多。⛔ 建议主 session 排进下一批。
23. **⚠️ 另立卡：缺库时的半态白板**。缺 PyYAML 时净效果不是「什么都没写」—— Step 3
    （`SKILL.md` 的 `grep -n "scored_pending_node_update"` 段）早已由 Claude 用 Edit 把分数写进
    检验白板，主写点块之前还会建 `.locks` 锁文件。用户看到的是**一张记了分但节点没更新的
    半态白板**。本卡的拒写让这个半态更常见，值得单独评估（是否该把 Step 3 也挪到 vault 绑定之后）。
24. **⚠️ 工程教训（建议进工程坑索引）：门会因为被守护对象变形而悄悄退化成恒真**。本卡实测：
    删掉降级解析后，那道 60 参数的核心不变量门**一条不改就全绿** —— 它的允许条件（「降级更窄
    即放行」）在「降级恒拒」之后把所有输入都吸进了允许档。**它表面上仍是绿的。** 改动会不会
    让某道门变成恒真，应当与「会不会让它变红」一起检查；判法是**把实现改错，看它红不红**。
25. **⚠️ 论证纪律（第三次）：我又一次把「我想到的」当成了全集**。§五-sexies 已记两次，这是
    第三次 —— 「缺库时下游本来也会拒」我只验了 harness_tree 缺省那一个取值，就把结论写成了
    对**所有** harness_tree 取值成立的全称句。**全称句只能被反例杀死，不能被一个正例证实。**
    写「必然 / 无论怎样 / 不会损失任何」之前，先找出句子里的自由变量，再问自己验了它几个取值。

---

## 九 Codex 复核

| 轮次 | 绑定 | 存档 | B / H / M / L | 处置 |
|---|---|---|---|---|
| r1 | `08100483..f7f10be4`（**非**最终 HEAD） | `codex-review-CARD-HARNESS-TREE-PARSE-REDO-r1.md` | **0 / 0** / 1 / 2 | MEDIUM 与两条 LOW **全部整改**（见 §五-bis），未留登记不修项 |
| r2（p1） | — | `codex-review-…-r2.md` **0 字节** | — | ⛔ 被 cyber 过滤器拦（跑了 57,682 tokens，最后一步输出被拦）。根因：问题 ⓪ 写成「找出一行能被接受而 PyYAML 会拒的配置并给出 repr」，落在协议 §2 的任务边界上。按协议「0 字节重发一次」 |
| r2（p2） | `08100483..4d21bc9b` | `codex-review-…-r2-p2.md` | **0 / 0** / 3 / 1 | 问法改为「按来源分类核对覆盖面、不索取具体输入」后通过。三条 MEDIUM + 一条 LOW **全部整改**（见 §五-ter） |
| r3 | `08100483..e844d6a1` | `codex-review-…-r3.md` | **0 / 0** / 4 / 1 | MEDIUM 3 条整改、MEDIUM-3 与 LOW-1 **登记不修**（§五-quater.3/.4） |
| r4 | `08100483..34451227` | `codex-review-…-r4.md` | **0 / 0** / 2 / 2 | 三条反驳**全部接受**：LOW-1 原登记理由错、已补 3 条哨兵参数；MEDIUM-1/2 与 LOW-2 按 D-32 纯 docstring 更正（§五-quinquies） |
| r5 | `08100483..4eeaeaa6`（最终 HEAD） | `codex-review-…-r5.md` | **0 / 0** / 2 / 3 | **轮次上限 5/5**。确认两处盲区移交定性准确；LOW-1/LOW-3 按 D-32 纯措辞更正，LOW-2 登记不修（§五-sexies） |

> ⛔ **D-15 结论（分两段账，别混）**：
> · **原范围**（卡文定义的「重做解析」）：轮次 **5/5 用满**，末轮 r5 绑当时最终 HEAD `4eeaeaa6`，
>   **BLOCKER = 0、HIGH = 0**。r5 之后在原范围内只做了 D-32 的纯注释/消息尾巴。
> · **用户裁定后的新增范围**（缺库即拒写）：这是**逻辑改动**，不是 D-32 尾巴。已另起轮次
>   r6（绑 `faaeb005`，B=0/H=0）、r7（绑最终 HEAD）。⚠️ 原先写的「r5 之后未再改逻辑」在
>   `faaeb005` 落地后**已不成立**，此处据实改写。

**r1 结论原文要点**：BLOCKER 无；HIGH 无；MEDIUM = 「降级扫描仍会接受与 PyYAML 不同的值，或漏掉合法键后静默回退」（U+0085 / 续行折叠 / 流式映射三种反例）；LOW① = 降级门控制组对绑定树失明；LOW② = 非严格 `realpath` 对「中间段是文件」的路径仍会给出祖先目录（旧版已有，非本卡新增）。

**逐条复测更正（不直接采信复核结论，全部按其逐字形态重跑）**：
- U+0085：Codex 给的形态 `'harness_tree: /repo\x85\n'` 实测 PyYAML 给 `'/repo'`、旧正则给 `'/repo\x85'` ⇒ **发散成立**。（我最初测的是尾部再跟一个字的变体，那种 PyYAML 会整份 `ScannerError`，据此差点误判 Codex 报错 —— 记此一笔。）
- 续行：`harness_tree: /repo` + 缩进 `more` ⇒ PyYAML `'/repo more'`、旧正则 `'/repo'` ⇒ **发散成立**。
- 流式映射：`{harness_tree: /B}` **只有当它是整份文档时**才被 PyYAML 接受；接在本仓 fixture 的三行 header 之后实测 `ScannerError`。Codex 表述未限定这一点，**范围比它说的窄**，但仍是真缺口（整份 flow mapping 是合法 config），已按「全键写进同一个 flow mapping」的形态入门。

命令与模型固定见协议 §2；prompt `_bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO.md`（五分节、最小读取面写死、四禁用措辞各 0 命中，已实测）。
