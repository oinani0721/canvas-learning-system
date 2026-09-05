# CARD-G3-3 / G3-3-R1 证据 — 负控变异 + 并发取证

> 工作树 `card-z2-cas`。
> **本文只作索引，不再逐字转录**（协议 §2.2：验收单与索引只引用路径与末行，不自述数字）。
> 上一轮（第十一批 CARD-G3-3）的 `.log` 文件被仓根 `.gitignore` 的 `*.log` 吞掉，
> 从 R1 起落盘一律用 `.txt` / `.json` 并带时间戳。

## 一 R1 收官证据（`[BATCH-2026-09-05-第十二批 / CARD-G3-3-R1]`）

| 内容 | 文件 | 末行 / 关键行 |
|---|---|---|
| **修前**实证「合入即红」（`--only M1`，按 id 前缀实际匹配 M1/M10-M15 七条） | `premerge-leftovers-20260905T164552.txt` | `MUTANT 新增残留 (基线之外): ['…/g32ccr1_negative_controls.py']` / `rc=1` |
| **负控之负控**：编译自检（旧 M15 串必判 `SYNTAX-INVALID` + 两个验伪锚 + 不落盘） | `syntax-selfcheck-20260905T165509.txt` | `未落盘 (跑前跑后 sha 逐字节相同): 是` / `rc=0` |
| 送审版全量变异（18 条，绑 `a795741f`） | `mutation-run-20260905T171138.txt` · `mutation-results-20260905T171138.json` | `杀灭: 18/18` / `SYNTAX-INVALID: 0` / `还原逐字节相同: 是` / `MUTANT 新增残留 (基线之外): 无` / `rc=0` |
| **对照输入：语法合法但运行期即死** | `runtime-death-falsifier-20260905T173550.txt` | 三条门在旧判据下 KILLED、新判据下 SURVIVED；`还原逐字节相同: 是` / `rc=0` |
| 整改中间轮（**留证，不是收官轮**） | `mutation-run-20260905T173726.txt` · `.json` | `杀灭: 18/18` 但 `rc=1`——新增的 `scan_ok`/`baseline_missing` 输出把探针留下的 `__pycache__/g33_mutation_gates.cpython-314.pyc` 报成残留（派生物，处置见验收单 §五.1） |
| 第一轮整改后全量变异（**中间态**，绑不住最终代码） | `mutation-run-20260905T174912.txt` · `.json` | `杀灭: 18/18` / `SYNTAX-INVALID: 0` / `还原逐字节相同: 是` / `MUTANT 扫描: 完成` / `新增残留: 无` / `基线缺失: 无` / `rc=0` |
| 并发取证 `--rounds 3` | `concurrency-run-20260905T171703.txt` · `.json` | `lost_update 轮数: 0/3` / `rc=0` |
| 送审版回归：`test_g3_3_cas.py` + `test_g3_2_review_ledger.py` | `regression-g33-g32-20260905T170619.txt` | `161 passed, 1 xfailed` / `rc=0` |
| 第一轮整改后回归（**中间态**） | `regression-g33-g32-20260906T014827.txt` | `161 passed, 1 xfailed` / `rc=0` |
| **对照输入（4 门版）** | `runtime-death-falsifier-20260906T020726.txt` | 4 条门旧判据 KILLED → 新判据 SURVIVED / `rc=0` |
| **绑定 sha + ruff + pyright** | `binding-20260906T021509.txt` · **`binding-20260906T022723.txt`（最终）** | `g33 = b209e5dc…` / `test_g3_3_cas = 3e44005c…`；ruff/pyright 全 rc=0 |
| ⭐ **收官全量变异（绑最终代码）** | `mutation-run-20260906T022737.txt` · `mutation-results-20260906T022737.json` | `杀灭: 18/18` / `SYNTAX-INVALID: 0` / `还原逐字节相同: 是` / `MUTANT 扫描: 完成` / `新增残留: 无` / `基线缺失: 无` / `rc=0` |
| ⭐ **收官回归（两文件）** | `regression-g33-g32-20260906T022107.txt` | `161 passed, 1 xfailed in 334.81s` / `rc=0` |
| ⭐ **收官 `tests/skills`** | `skills-final-20260906T023434.txt` | `369 passed`（与开工同数）/ `rc=0` |
| ⭐ **收官回归三文件** | `regression-three-20260906T023555.txt` | `210 passed, 1 skipped` / `rc=0` |
| **对照输入：只让 race 副本注入失效**（证 `_race_fired` 承重） | `race-fired-loadbearing-20260906T025034.txt` | M2 / M16 / M17 三条门全部红在 `_race_fired` 前提断言、`expect_msg` 不命中 → SURVIVED / `rc=0` |
| **对照输入：外审 round-2 的 R2-01 / R2-02 / R2-04** | `r2-falsifiers-20260906T025711.txt` | 三条旧行为全部 ⛔、新行为全部 ✅ / `rc=0` |
| **绑定 sha + ruff + pyright（round-2 整改后 = 最终）** | `binding-20260906T025102.txt` | `g33 = bed7e1e6…` / `test_g3_3_cas = 119d56f3…`；三项 rc=0 |
| ⭐⭐ **最终收官回归（两文件）** | `regression-g33-g32-20260906T025722.txt` | `161 passed, 1 xfailed in 375.40s` / `rc=0` |
| ⭐⭐ **最终收官全量变异（换判据后重验）** | `mutation-run-20260906T025116.txt` · `mutation-results-20260906T025116.json` | `杀灭: 18/18`（`expect_hit` 全 True）/ `SYNTAX-INVALID: 0` / `还原逐字节相同: 是` / `新增残留: 无` / `基线缺失: 无` / `rc=0` |
| 中间轮全量变异（自检抓到探针留下的 `.pyc`） | `mutation-run-20260906T021523.txt` · `.json` | `杀灭: 18/18` / `rc=0`（绑 `73dee2ff…`，非最终） |
| 回归：`test_fsrs_bridge.py` + `test_learning_event_log.py` + `test_learning_events_schema_contract.py` | `regression-three-20260905T171104.txt` | `210 passed, 1 skipped` / `rc=0` |
| `tests/skills` 目录级（开工） | `skills-baseline-20260905T170500.txt` | `369 passed` / `rc=0` |
| `tests/skills` 目录级（送审版收工，非最终） | `skills-final-20260905T171712.txt` | `369 passed` / `rc=0` |

⭐⭐ = 绑定**最终代码**（`binding-20260906T025102.txt`：`bed7e1e6…` / `119d56f3…`）的收官跑。
⭐ = 绑定上一轮定稿（`binding-20260906T022723.txt`）的收官跑——外审 round-2 之后代码又改过，
所以它们**绑不住最终代码**，保留为过程留证。代码一共定稿三次，对应三轮审查依次落地。

`mutation-results-*.json` 每条含 `expect_msg` / `expect_hit` / `error_lines`——
`error_lines` 是 pytest 回溯里真正抛出来的异常文本，用来核对**红在哪一条断言上**
（上一轮 M15 假杀就是死在这一格没人看）。

pyright / ruff（本卡改动的两个文件，绑最终 sha）：见 `binding-20260906T022723.txt`，三项 rc=0。

## 二 上一轮（第十一批 CARD-G3-3）留存

`mutation-results.json` / `concurrency-run.json` 为上一轮结果，保留作对照。
⚠️ 其中 `M15-post-lock-redup` 记为 `KILLED`——**那是假杀**，根因与修法见
`_bmad-output/验收单/UAT-CARD-G3-3-R1-2026-09-05.md` §一。
`mutation-run.log` / `concurrency-run.log` 未入库（被 `*.log` 忽略）。
