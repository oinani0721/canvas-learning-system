# evidence-ast-flag — CARD-AST-FLAG-PATCH 证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-AST-FLAG-PATCH]`。承重存档以下表为准。

## 承重（按裁判编号）

| 裁判 | 文件 | 结论 |
|---|---|---|
| 1 第 0 分钟 | `minute0-20260917T084209.txt` | 分支/HEAD/status 空/基线 64/patch 缺席 0（验伪锚 3） |
| — 基线 | `baseline-48-27-20260917T084255.txt` | 改前 `PASS (48 / 27)` |
| 2 三盲区先红 | `red-lambda-*.txt` / `red-setattr-*.txt` / `red-branch-*.txt` | 各只加一条 ⇒ 各一条 `*** MISSED ***` + `FAIL` + rc=1 |
| 3 后绿 | **`green-51-27-20260917T090106.txt`** | `PASS (51 / 27)`，CAUGHT=51 CLEAN=27 MISSED=0 FALSE-POSITIVE=0 |
| 4 消费面/全扫描面 | `consumers-before-20260917T084638.txt` + `fullscan-before-20260917T084647.txt` vs **`consumers-after-20260917T090121.txt`** | 两文件违规集与 401 文件全扫描面违规集**改前改后逐字相同**（都为空） |
| 5 fixpoint 红/绿 | **`fixpoint-red-20260917T090106.txt`** / **`fixpoint-green-20260917T090106.txt`** | 红正文含 `MISSED: 未收敛未被报出` ×2 且 `RUNTIME-FILES-SELFTEST: PASS`（证明红不来自 runtime 自证）；绿 `FIXPOINT-SELFCHECK: PASS` |
| 6 地盘 | `territory-<ts>.txt` | commit 后跑，只本文件 |
| 7 ruff | `ruff-20260917T085113.txt` + `ruff-format-<ts>.txt` | `check` 0；`format --check` 见下「格式漂移」 |
| 8 tests/unit | `unit-close-<ts>.txt` + `base.nodeids`/`close.nodeids` | 与 64 基线 diff 空 |

## 纵深（非卡文要求，本卡自加）

- `probe-isolation-boundaries-20260917T090121.txt` —— (d) 改动的六条边界性质（含 docstring 声称的「两支各自隔离仍合格」、`yield from` 仍失格、验伪锚 10 形态不被弄红）。
- `probe-lambda-scope-20260917T090121.txt` —— `_own_exprs` docstring 三条声称的旧/新对照实测。
- `fixpoint-rounds-instrument-20260917T085859.txt` + `rounds_instr.py` —— `_FIXPOINT_MAX_ROUNDS=8` 的取值依据（负控最多 3 轮 / 401 文件最多 2 轮），末段含「故意给错行号 ⇒ assert 炸」的锚自验。
- `close-pyright-20260917T085652.txt` —— `0 errors, 81 warnings`（本卡零触及 `backend/app`）。

## 如实登记：两处判据自身出过问题（保留记录）

1. **`ruff-20260917T085053.txt` 的验伪锚失败**（anchor rc=0 = 判据当时恒绿，不可用）。根因：锚文件放在仓外，走的是默认 ruff 配置而非本文件那份。已用 `--stdin-filename` 重做为 `ruff-20260917T085113.txt`，F821 锚 rc=1。**两份都留**，前者不得引为依据。
2. **`rounds2.py` / `rounds_real.py` / 第一份 instrument txt 全部作废（VOID）**，文件内已就地写明。根因：硬编码行号 634 在本卡改动后漂到 687，计数器全程没被写过，直方图退化成 `{0: N}` 的假数据；抓住它的是脚本自带的「须含 634」验伪锚。替代件 `rounds_instr.py` 把锚升成 `assert`。

## 格式漂移的归属（卡文 (k) 要求先判再处置）

`ruff format --check` 在本卡定稿上红，**是本卡引入**（同一配置面下对 B14_BASE 内容跑 `--check` rc=0，见 `ruff-format-<ts>.txt`），故**不**走协议 §2.3 过渡条款，直接 `ruff format` 修正。4 个 format hunk 全部落在本卡新增行内（`raise` 单行化、两处推导式/`all()` 单行化、一处 `failures.append` 单行化）。format 后全部承重裁判已重跑，即上表加粗的那几份。

## prefix.py

裁判 5 的「先红」副本 = `cp` 定稿文件后 `sed` **仅**剔除「未收敛处置」那一处 2 行 hunk（保留 `--selfcheck-fixpoint` 子命令，实测 3 处命中）。依 **R-B14-7** 不从 `B14_BASE` 取（base 无此子命令）。实测确认它不在门的扫描面内（401 不变，无 prefix 条目）。
