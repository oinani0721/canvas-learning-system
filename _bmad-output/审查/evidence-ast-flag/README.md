# evidence-ast-flag — CARD-AST-FLAG-PATCH 证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-AST-FLAG-PATCH]`。
> ⚠️ 本目录有**四代**存档（初版 `0842–0850` / format 后 `0900` / Codex r1 整改后 `0917` /
> **Codex r2 整改后 `0930–0933`**）。**只有 `0930–0933` 那一代是定稿的承重件**；
> 前三代保留作过程记录，**不得引为定稿依据**。

## 承重（定稿一代，按裁判编号）

| 裁判 | 文件 | 结论 |
|---|---|---|
| 1 第 0 分钟 | `minute0-20260917T084209.txt` | 分支/HEAD/status 空/基线 64/patch 缺席 0（验伪锚 3） |
| — 改前基线 | `baseline-48-27-20260917T084255.txt` | `PASS (48 / 27)` |
| 2 三盲区先红（各一份） | `red-lambda-20260917T084628.txt` / `red-setattr-20260917T084629.txt` / `red-branch-20260917T084629.txt` | 各只加一条条目 ⇒ 各**恰好一条** `*** MISSED ***` + `FAIL` + rc=1 |
| 3 后绿 | **`green-59-31-20260917T093255.txt`** | `PASS (59 / 31)`，CAUGHT=59 CLEAN=31 MISSED=0 FALSE-POSITIVE=0 |
| 3+ 定向负控（本卡自加，承重） | **`negctl-anchors-20260917T093255.txt`** + `negctl.py` | **11 处**修复逐个撤掉，**指定的那一条**各自变红；控制组红项为空 |
| 4 消费面 / 全扫描面 | `consumers-before-20260917T084638.txt` + `fullscan-before-20260917T084647.txt` vs **`consumers-after-20260917T093307.txt`** | 两文件违规集与 401 文件全扫描面违规集**改前改后逐字相同**（都为空） |
| 5 fixpoint 红 / 绿 | **`fixpoint-red-20260917T093255.txt`** / **`fixpoint-green-20260917T093255.txt`** | 红正文含 `MISSED: 未收敛未被报出` ×2 且 `RUNTIME-FILES-SELFTEST: PASS`；绿 `FIXPOINT-SELFCHECK: PASS` |
| 6 地盘 | `territory-20260917T092132.txt` | 只 `backend/scripts/lifespan_isolation_negative_control.py`（验伪锚：去掉 exclude 多出 55 条 `_bmad-output/` 路径）。⚠️ 该件绑 `6564fc09`；定稿 SHA 的地盘回执见 `territory-FINAL.txt` |
| 7 ruff | **`ruff-r2fix-20260917T093307.txt`** | `check` / `format --check` 均 rc=0；F821 验伪锚 rc=1 |
| 8 tests/unit | **`unit-close-20260917T093245.txt`** + `base.nodeids` / `close.nodeids` | 与 64 基线 diff 空 |
| — pyright | `close-pyright-20260917T085652.txt` | `0 errors, 81 warnings`（本卡零触及 `backend/app`） |
| — Codex r1 复现 | `verify-r1-findings-20260917T091714.txt` + `verify_r1.py` | 四条 finding 整改前后的旧/新对照 |
| — Codex r2 复现 | **`verify-r2-findings-20260917T093255.txt`** + `verify_r2.py` | 七条 finding 的 `B14_BASE` / r1 定稿 / 现版**三版**对照 |

## 纵深（非卡文要求，本卡自加）

- `probe-isolation-boundaries-20260917T093307.txt` —— (d) 的六条边界性质。
- `probe-lambda-scope-20260917T093307.txt` —— `_own_exprs` 旧/新绑定对照：**只有 child 位置的默认参数**变了（`['g']`→`['c','g']`），根位置与 `B14_BASE` 逐字同（`['a','f']`）。
- `probe-annotation-yield-by-version-20260917T093019.txt` —— ⛔ **逐版本**实测注解里的 `yield`：3.11.15 **合法**且外层真多一条 `YIELD_VALUE`；3.14.4 `SyntaxError`。CI matrix 是 `['3.11','3.12']`。
- `probe-walk-same-scope-delta-20260917T092246.txt` + `probe_walk_delta.py` —— 新旧 `_walk_same_scope` 在 401 文件上的差分（旧有而新没有 = 0）。
- `probe-setattr-shadow-rate-20260917T092145.txt` —— `_module_binds_name` 在真实面上的触发率（0/401，交集 0）。
- `fixpoint-rounds-instrument-20260917T085859.txt` + `rounds_instr.py` —— `_FIXPOINT_MAX_ROUNDS=8` 的取值依据。
- `probe_direction.py` / `probe-lambda-direction-20260917T091725.txt` —— 根位置 lambda 的方向核（本卡一度改过、经 r1 HIGH-1 已撤回）。

## 如实登记：四处判据 / 改动**自身**出过问题（保留记录）

1. **`ruff-20260917T085053.txt` 的验伪锚失败**（anchor rc=0 = 判据当时恒绿）。根因：锚文件放在仓外，ruff 按**文件路径**解析配置。已改 `--stdin-filename` 重做。**该件不得引为依据。**
   顺带实测：`backend/**` 只启用 14 条必错级规则（`E902` + F 系），**`F401` 不在其中**。
2. **`rounds2.py` / `rounds_real.py` / `fixpoint-rounds-instrument-…085801.txt` 作废（VOID）**，文件内已就地写明。根因：硬编码行号 634 在改动后漂到 687，直方图退化成 `{0: N}` 的假数据。替代件 `rounds_instr.py` 把锚升成 `assert`。
3. **`probe-outer-evaluated-completeness-20260917T092116.txt` 的结论是错的**（⛔ **不得引用**）。它断言「注解里不能写 `yield`，故不是缺口」—— 那是**只在本机 3.14 上**测的，而 CI 跑 3.11/3.12。Codex r2 HIGH-3 指出后逐版本复测（见上方 `probe-annotation-yield-by-version-*`）：3.11 上完全合法。代码已按 3.11 口径补收注解。
4. **本卡 r1 的两处修复各自引入了新回归**，均由 Codex r2 抓出并已修：根 lambda 的递归下潜（HIGH-1）、`_walk_same_scope` 的 `stack.extend` 未再过 `push`（HIGH-2）。两者都已加回归锚（`R2-HIGH1-*` / `R2-HIGH2-*`）。
5. **定向负控的变异锚会随生产代码漂移**：`ruff format` 把一行 `child_in_body = ...` 折行后，r2 那个锚一度命中 0 次。脚本对每个锚 `assert count == 1`，锚不命中直接抛 —— 不会静默少跑一个变异。

## 索引自检

本文件引用的每个具体文件名都必须真实存在，且**不得含 `<…>` 占位**（Codex r1 LOW / r2 LOW 连栽两次）。
自检口径：把 README 里所有反引号包裹的 `*.txt` / `*.py` / `*.nodeids` 名字取出，逐个 `test -e`；
同时 `grep -c '<[^>]*ts[^>]*>'` 必须为 0。

## 格式漂移的归属（卡文 (k) 要求先判再处置）

`ruff format --check` 在本卡定稿上红，**是本卡引入**（同一配置面下对 `B14_BASE` 内容跑 `--check` rc=0，见 `ruff-format-20260917T090107.txt`），故**不**走协议 §2.3 过渡条款，直接 `ruff format`。format hunk 全部落在本卡新增行内。

## prefix.py

裁判 5 的「先红」副本 = `cp` **定稿**文件后 `sed` **仅**剔除「未收敛处置」那一处 2 行 hunk（保留 `--selfcheck-fixpoint` 子命令）。依 **R-B14-7** 不从 `B14_BASE` 取。实测确认它不在门的扫描面内（401 不变）。
