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


---

## R2 轮（Codex 外审后整改）——**最终判据以这几份为准**

外审存档 `../codex-review-CARD-W4-5-ast-high6.md`（绑定 round-1 的 `6d6e3e09`）。
整改后代码已变，属**整改未复审**（见验收单 §八）。

| 裁判 | 文件 | 结论 |
|---|---|---|
| J1 | `J1-R2FINAL-20260906T150427.txt` | `PASS (48 绕过全抓 / 27 正例全净)` rc=0 |
| J2 | `J2-R2FINAL-20260906T150427.txt` | 以开工基线 `988fd655` 对照 **20 条「改前放行→改后抓」**；sha 逐字节相同 rc=0 |
| J3 | `J3-R2FINAL-20260906T150427.txt` | `36/36` rc=0 |
| J4 | `J4-R2FINAL-20260906T150412.txt` | `2019 passed`，红 **0**，新增红 **0**，`blocked=0` |
| J5 | `J5-R2FINAL-20260906T150412.txt` | `RUNTIME-FILES: unchanged` rc=0 |
| J6 | `J6-R2FINAL-20260906T150427.txt` | `0 violations in 385 files` rc=0 |
| J8 | `J8-R2FINAL-20260906T150427.txt` | **18/18 归因成立**（含 R2 整改 6 条）rc=0 |
| D-14 | `D14-pyright-R2FINAL-20260906T150514.txt` | 5 errors（基线 6）：新增 0、消除 1、行号交集空 |

### R2 轮的中间产物（如实保留）

- `J8-R2-FINAL-*.txt` — 归因变异第一次跑 R2 的 6 条变异，`R2-3` 报**归因不成立**。
  查因：它其实被「剔除失格 key」守住，不是被「按 key 聚合」。据此新造 `R2-3b`
  （两个定义都不失格、危险位被后定义覆盖成安全）才真正守住那条规则。
- `J8-R2-FINAL2-*.txt` — 加 `R2-3b` 后，`R2-3c`（不剔除失格 key）转为**归因不成立**。
  再查因：失格的成因必然让逐位表不一致，「按 key 聚合」已经把整 key 判 None ⇒
  这道过滤**没有独立可观测价值**，如实标注为冗余防线（代码注释同步写明）。
- `J2-R2-*.txt` — 基线是 `6d6e3e09`（round-1 commit），故只显示 5 条；
  `J2-R2-vs-开工基线-*.txt` 才是以 `988fd655` 为基线的全卡对照。
  J2 脚本已加 `W45_BASE` 环境变量支持显式指定基线。

### 两处「实测推翻外审推演」的证据

- d2/d3 方向：Codex 预测「d2 红、d3 绿」，实测**两条都红**（`_publish_return_elts`
  轮末发布让扫描期表恒空）。
- 「能区分每轮重建与 add-only 的输入」：Codex 给的 q/later/mix 构造，实测两种实现
  **结论相同**。两者都是对 round-1「扫描期直接写表」实现的推演，整改后不再适用。
