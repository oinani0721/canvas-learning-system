# evidence-ast-flag — CARD-AST-FLAG-PATCH 证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-AST-FLAG-PATCH]`。承重存档以下表为准。
> ⚠️ 本目录有**三代**同名存档（初版 `0842–0850` / format 后 `0900` / Codex round-1 整改后 `0917`）。
> **只有 `0917` 那一代是定稿的承重件**；前两代保留作过程记录，不得引为定稿依据。

## 承重（定稿一代，按裁判编号）

| 裁判 | 文件 | 结论 |
|---|---|---|
| 1 第 0 分钟 | `minute0-20260917T084209.txt` | 分支/HEAD/status 空/基线 64/patch 缺席 0（验伪锚 3） |
| — 改前基线 | `baseline-48-27-20260917T084255.txt` | `PASS (48 / 27)` |
| 2 三盲区先红（各一份） | `red-lambda-…084628` / `red-setattr-…084629` / `red-branch-…084629` | 各只加一条条目 ⇒ 各**恰好一条** `*** MISSED ***` + `FAIL` + rc=1 |
| 3 后绿 | **`green-53-29-20260917T091714.txt`** | `PASS (53 / 29)`，CAUGHT=53 CLEAN=29 MISSED=0 FALSE-POSITIVE=0 |
| 3+ 定向负控（本卡自加，承重） | **`negctl-anchors-20260917T091714.txt`** | 六处修复**逐个**撤掉，**指定的那一条**负控输入各自变红；控制组红项为空 |
| 4 消费面 / 全扫描面 | `consumers-before-…084638` + `fullscan-before-…084647` vs **`consumers-after-20260917T091725.txt`** | 两文件违规集与 401 文件全扫描面违规集**改前改后逐字相同**（都为空） |
| 5 fixpoint 红 / 绿 | **`fixpoint-red-20260917T091714.txt`** / **`fixpoint-green-20260917T091714.txt`** | 红正文含 `MISSED: 未收敛未被报出` ×2 且 `RUNTIME-FILES-SELFTEST: PASS`（证明红不来自 runtime 自证）；绿 `FIXPOINT-SELFCHECK: PASS` |
| 6 地盘 | `territory-<最终 ts>.txt` | 只 `backend/scripts/lifespan_isolation_negative_control.py` |
| 7 ruff | **`ruff-r1fix-20260917T091743.txt`** | `check` / `format --check` 均 rc=0；F821 与乱排版两个验伪锚均 rc=1 |
| 8 tests/unit | **`unit-close-20260917T091749.txt`** + `base.nodeids` / `close.nodeids` | 与 64 基线 diff 空 |
| — pyright | `close-pyright-20260917T085652.txt` | `0 errors, 81 warnings`（本卡零触及 `backend/app`） |
| — Codex round-1 复现 | **`verify-r1-findings-20260917T091714.txt`** | 四条 finding 整改前后的旧/新对照 |

## 纵深（非卡文要求，本卡自加）

- `probe-isolation-boundaries-…091725.txt` —— (d) 的六条边界性质（含写进 docstring 的「两支各自隔离仍合格」、`yield from` 仍失格、验伪锚 10 形态不被弄红）。
- `probe-lambda-scope-…091725.txt` —— `_own_exprs` 的旧/新绑定对照：**只有 child 位置的默认参数**变了（`['g']` → `['c','g']`），根位置与 `B14_BASE` 逐字同（`['a','f']`）。
- `probe-lambda-direction-…091725.txt` —— 根位置 lambda 的方向核（本卡一度改过、经 Codex round-1 HIGH-1 已撤回）。
- `fixpoint-rounds-instrument-…085859.txt` + `rounds_instr.py` —— `_FIXPOINT_MAX_ROUNDS=8` 的取值依据，末段含「故意给错行号 ⇒ `assert` 必炸」的锚自验。
- `negctl.py` / `verify_r1.py` / `probe_direction.py` —— 上述判据的可重跑脚本。

## 如实登记：三处判据 / 改动**自身**出过问题（保留记录）

1. **`ruff-20260917T085053.txt` 的验伪锚失败**（anchor rc=0 = 判据当时恒绿）。根因：锚文件放在仓外，ruff 按**文件路径**解析配置 ⇒ 走的是默认配置而非 `backend/ruff.toml`。已用 `--stdin-filename` 重做。**该件不得引为依据。**
   顺带实测：`backend/**` 只启用 14 条必错级规则（`E902` + F 系），**`F401` 不在其中** ⇒ 卡文模板惯用的 F401 锚在该面上恒不触发。
2. **`rounds2.py` / `rounds_real.py` / `fixpoint-rounds-instrument-…085801.txt` 全部作废（VOID）**，文件内已就地写明。根因：硬编码行号 634 在本卡改动后漂到 687，计数器全程没被写过 ⇒ 直方图退化成 `{0: N}` 的假数据。抓住它的是脚本自带的「须含 634」验伪锚。替代件 `rounds_instr.py` 把锚升成 `assert`。
3. **本卡一度扩面改了「根位置 lambda」，被 Codex round-1 判 HIGH 并已撤回**（详见验收单 §四-A.7）。`green-51-27-*` 与 `0850`/`0900` 两代 `consumers/probe` 存档都是**撤回前**的状态。

## 格式漂移的归属（卡文 (k) 要求先判再处置）

`ruff format --check` 在本卡定稿上红，**是本卡引入**（同一配置面下对 `B14_BASE` 内容跑 `--check` rc=0，见 `ruff-format-20260917T090107.txt`），故**不**走协议 §2.3 过渡条款，直接 `ruff format`。format hunk 全部落在本卡新增行内，**没有**顺手 format 任何既有行。

## prefix.py

裁判 5 的「先红」副本 = `cp` **定稿**文件后 `sed` **仅**剔除「未收敛处置」那一处 2 行 hunk（保留 `--selfcheck-fixpoint` 子命令，实测 3 处命中）。依 **R-B14-7** 不从 `B14_BASE` 取（base 无此子命令）。实测确认它不在门的扫描面内（401 不变，无 prefix 条目）。
