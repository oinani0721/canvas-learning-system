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
| **收官全量变异**（18 条） | `mutation-run-20260905T171138.txt` · `mutation-results-20260905T171138.json` | `杀灭: 18/18` / `SYNTAX-INVALID: 0` / `还原逐字节相同: 是` / `MUTANT 新增残留 (基线之外): 无` / `rc=0` |
| 并发取证 `--rounds 3` | `concurrency-run-20260905T171703.txt` · `.json` | `lost_update 轮数: 0/3` / `rc=0` |
| 回归：`test_g3_3_cas.py` + `test_g3_2_review_ledger.py` | `regression-g33-g32-20260905T170619.txt` | `161 passed, 1 xfailed` / `rc=0` |
| 回归：`test_fsrs_bridge.py` + `test_learning_event_log.py` + `test_learning_events_schema_contract.py` | `regression-three-20260905T171104.txt` | `210 passed, 1 skipped` / `rc=0` |
| `tests/skills` 目录级（开工） | `skills-baseline-20260905T170500.txt` | `369 passed` / `rc=0` |
| `tests/skills` 目录级（收工） | `skills-final-20260905T171712.txt` | `369 passed` / `rc=0` |

`mutation-results-*.json` 每条含 `expect_msg` / `expect_hit` / `error_lines`——
`error_lines` 是 pytest 回溯里真正抛出来的异常文本，用来核对**红在哪一条断言上**
（上一轮 M15 假杀就是死在这一格没人看）。

pyright（本卡改动的两个文件）：`0 errors, 0 warnings, 0 informations`。

## 二 上一轮（第十一批 CARD-G3-3）留存

`mutation-results.json` / `concurrency-run.json` 为上一轮结果，保留作对照。
⚠️ 其中 `M15-post-lock-redup` 记为 `KILLED`——**那是假杀**，根因与修法见
`_bmad-output/验收单/UAT-CARD-G3-3-R1-2026-09-05.md` §一。
`mutation-run.log` / `concurrency-run.log` 未入库（被 `*.log` 忽略）。
