# evidence-w4-5 —— CARD-W4-5-ast-high6 裁判证据索引

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-W4-5-ast-high6]`，开工 SHA `988fd655`。
> 中间轮次**全部保留**（代码在实施过程中定稿了四次，每次都重跑了裁判）。
> 下表标 **FINAL** 的那几份跑在**最终定稿代码**上，其余是迭代过程的如实记录。

## 最终跑（判据以这几份为准）

| 裁判 | 文件 | 结论 |
|---|---|---|
| J1 负控 + AST 负控 | `J1-FINAL2-20260906T141525.txt` | `AST-NEGATIVE-CONTROL: PASS (40 绕过全抓 / 24 正例全净)` rc=0 |
| J2 before/after | `J2-FINAL2-20260906T141525.txt` | 14 条「改前放行→改后抓」；`SHA0 == SHA1` 逐字节相同 rc=0 |
| J3 探针 | `J3-FINAL2-20260906T141525.txt` | `GUARD-PROBES: PASS — 36/36`（该文件本卡零改动）rc=0 |
| J4 门下目录级 | `J4-FINAL2-20260906T141511.txt` | 见文件尾（对照基线 `J4-before-20260906T132332.txt`）|
| J5 运行时文件门 | `J5-FINAL-20260906T141511.txt` | `RUNTIME-FILES: unchanged` rc=0 |
| J6 全仓重扫 | `J6-FINAL2-20260906T141525.txt` | `AST-GATE: PASS (0 violations in 385 files)` rc=0 |
| J8 归因变异（自加） | `J8-attribution-FINAL-20260906T141351.txt` | 12/12 归因成立；生产文件跑前跑后 sha 逐字节相同 rc=0 |

## 基线（开工，SHA `988fd655` 的代码）

- `J1-before-*.txt` — `PASS (25 / 13)`
- `J3-before-*.txt` — `36/36`
- `J6-astonly-before-*.txt` — `0 violations in 385 files`
- `J4-before-20260906T132332.txt` — `2019 passed, 6 skipped, 2 xfailed`，红 nodeid **0**，`blocked=0`

## 迭代中间轮（如实保留，不是最终判据）

`J1-final*` / `J2-before-after` / `J2-final*` / `J2-DEF` / `J3-final*` / `J3-DEF` /
`J4-after` / `J4-FINAL` / `J4-DEF` / `J5-final` / `J5-DEF` / `J6-final*` /
`J8-attribution-mutants-*` —— 对应代码定稿前的四个版本。其中：

- `J8-attribution-mutants-20260906T141135.txt` 是**归因变异第一轮**，12 条里 5 条报「归因不成立」。
  查因后 3 条是**变异本身写坏了**（改了文案/参数而不是拆防线），2 条是真实发现
  （(b) 的 IfExp 展开与 NamedExpr 递归被 (c) 三分兜住）。这一份保留，因为它是
  「变异要拆防线不是改参数」这条教训的实证。
- `J8-attribution-mutants-20260906T141320.txt` 是第二轮（变异修正后，11/12）；剩下 1 条是
  我的**期望列表写错**（把 (b)-1/(b)-2/(c)-1 写进了「三分应该守住」），第三轮更正为 12/12。

## cases/

20 份最小可复现源码（`case-*.py` 反例 / `pass-*.py` 正例），是实施期间用来定位判定路径的
探针输入。**权威副本在 `_AST_MUST_FLAG` / `_AST_MUST_PASS` 两张表里**——J2 的 before/after
是直接从那两张表用 AST 提取源码后喂给两个版本的，不读这个目录，两侧同源。
