# evidence-exc-handler-wire — 存档索引与作废声明

> `[BATCH-2026-09-18-第十五批 / CARD-EXC-HANDLER-WIRE-REDACT]` · 车道 P8（`card-p8-backend`）
> 承重存档一律 `.txt`（仓根 `.gitignore` 有全局 `*.log`）；末行 `rc=$pipestatus[1]`。
> 验收单按**全文件名**引用，不用 glob。

## ⛔ 作废存档（**不得作为判据引用**）

| 文件 | 作废原因 |
|---|---|
| `pin-before-20260918T170517.txt` | 管道写成了 `… \| tail -12 \| tee`，只截到末 12 行，且 `tail` 吃掉了被测命令的 rc。同一判据的有效存档是 `pin-before-full-20260918T170658.txt`（全量 tee，`rc=` 取自 `$pipestatus[1]`）。 |
| `unit-close-20260918T173546.txt` | 该次 `tests/unit` 目录级跑被 `TaskStop` **主动中止**（当时已决定采纳 Codex r1 的门加强，这次跑会被整改作废）。**中途被掐掉的跑不产出任何阴性结论**，本文件只作过程记录。有效的 unit 目录级存档见下表。 |

## 有效的目录级存档（三次 unit，如实全列）

| 存档 | 绑定 | 结果 | 说明 |
|---|---|---|---|
| `unit-open-20260918T165112.txt` | `9c4e7e82`（开工） | 32 failed，哨兵 `blocked=0` | 与 B15_BASE 的 33 条 diff 只有 `<`（1 条已知 flaky） |
| `unit-close-r1fix-20260918T174011.txt` | `7d3bdc2b` | 33 failed，哨兵 **`blocked=1`** | ⚠️ 本卡引入的 `>`：`test_production_app_maps_core_canvas_not_found_to_404` 红在 W4 哨兵 |
| `unit-close-w4fix-20260918T180027.txt` | `8c4a66a8` | 33 failed，哨兵 **`blocked=1`** | ⚠️ 第一次修法**无效**（根因判错，详见验收单 §二 4-A） |
| `unit-close-final-*.txt` | **`6d8e4ee0`（终）** | 32 failed / 5739 passed，哨兵 **`blocked=0`** | diff 对基线只有 `<`，零新增红 |

## 负控六段

`negctl-{1,2,3}-full-*.txt` = 卡文 (k) 指定三段（体脱敏 / 接线 / fsrs reason）；
`negctl-{4,5}-full-*.txt` = core 族六档门（删 `NodeNotFoundException→404` 映射 / core 500 体改回 `str(exc)`）；
`negctl-6-full-*.txt` 与 `negctl-6b-full-*.txt` = 覆盖键失配（后者在加了 DI 替身命中断言之后重跑，红点前移到命中断言）。
每段含跑前/跑后 `shasum -a 256` 两行与还原后 `git status` 为空。
