# CARD-G6-9b 裁判存档索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-G6-9b]` · 车道 T3 (`card-t3-review`) · 2026-09-17
> 卡文 `第十四批-goals/T3-C.md`；协议 §2.1/§2.2/§2.3；裁定 R-B14-1/2/3/10/11b。

| 文件 | 对应判据 | 末行 rc |
|---|---|---|
| `minute0-*.txt` | (a) 第 0 分钟 + 基线 64 自证 + 开工 `grep -cF degraded`=0 | 0 |
| `unit-open-*.txt` | (a)(i) tests/unit 开工目录级 | 1（64 红 = 基线，非本卡） |
| `open.nodeids` / `base.nodeids` | (i) 开工 nodeid 集与 $BASE 集，diff 为空 | — |
| `g69b-red-*.txt` | 判据 2 改前：4 failed，门①②③ 红在 `KeyError: 'push_degraded'`，门④ 红在徽标缺失 | 1 |
| `g69b-green-*.txt` | 判据 2 改后：4 passed | 0 |
| `file-before-*.txt` | 判据 4 改前全文件：4 failed / 112 passed | 1 |
| `file-after-*.txt` | 判据 4 改后全文件：116 passed（= 112 + 4） | 0 |
| `negctl-1-degraded-const-false-*.txt` | (e)① degraded 恒 False → 门② FAILED；跑前/跑后 sha 同 | 0 |
| `negctl-2-badge-unconditional-*.txt` | (e)② 徽标条件恒真 → 门④ FAILED（红在验伪锚那一条） | 0 |
| `negctl-3-missing-as-false-*.txt` | (e)③ 缺失态改 `(False, "")` → 门③ FAILED | 0 |
| `pyright-close-*.txt` | (h) 收工 `pyright app` = 0 errors | 0 |
| `pyright-open-baseline-reconstructed-*.txt` | (h) 开工基线**重建**（见下方如实声明） | 0 |
| `pyright-warning-identity-*.txt` | (h) warning **身份**多重集对照：本卡新增 0 / 消失 0 | 0 |
| `ruff-worktree-*.txt` | 判据 5 ruff（zsh 数组，files=2 非空洞） | 0 |
| `ruff-falsification-anchor-*.txt` | 判据 5 ruff 验伪锚（F821 → rc=1；对照组 → rc=0） | 0 |
| `readonly-live-*.txt` | (j) 现网只读：backups/live vault 各 0 新文件；验伪锚 14 | 1（见文件内注记） |
| `unit-close-*.txt` / `close.nodeids` | (i) tests/unit 收工目录级 + 与 $BASE diff | 见文件末行 |

## `sentinel` 为什么是 0 字节且仍入库

`sentinel` 是 (j) 现网只读判据的**输入**（`find <现网目录> -type f -newer $EV/sentinel`），
不是任何一次裁判的**输出**。协议 §2.2「0 字节存档一律不入库」针对的是
「跑失败了、什么都没产出却当成证据」的那类文件；时间戳哨兵按设计就是空文件。
入库是为了让复核者能复算同一个时间锚。

- `sentinel` mtime = `2026-09-17T08:43:39+0800`（开工 `touch` 时刻）
- 该时刻早于本卡任何一次写操作；`readonly-live-*.txt` 里的验伪锚（$EV 下 14 个文件比它新）
  证明 `find -newer` 这条判据本身能命中，「现网 0」不是判据写坏了得出的空结论。

## 如实声明：pyright 开工基线是**重建**的

第 0 分钟漏跑 `pyright app`。补法 = 改完代码后把 `review_overview.py` 临时
`git show $PREV:` 还原、跑一次、再还原回本卡版并比 sha（存档内三行 sha 齐）。
**实测结论与卡文预期不符且已归因**：$PREV（T3-B 末 commit）状态下就是
`0 errors, 82 warnings`，不是批次基线 `08100483` 的 81 —— 那 +1 是
T3-A/T3-B 带进来的，不是本卡。本卡自身的 warning 身份多重集差集 = 新增 0 / 消失 0。

---

## r2 轮（按 Codex r1 MEDIUM-1 修三态映射后重跑）

| 文件 | 对应判据 | 结论 |
|---|---|---|
| `r2-g69b-green-20260917T091307.txt` | ⚠ **名不副实，如实说明**：这一跑名字叫 green 但里面是 `1 failed, 3 passed` | 它是**我自己新加的断言抓到修复不自洽**的那一跑（`push_degraded is None` 却带 `last_error == ""`）。保留作过程证据；不作「改后绿」引用。 |
| `r2-g69b-green-20260917T091343.txt` | (d) 修复自洽后的四门 | `collected 4 items` / 4 passed / rc=0 ← **这一份才是「改后绿」** |
| `r2-negctl-1-degraded-const-false-*.txt` | (e)① 重跑（锚点随代码改动重取） | 门② FAILED；sha 前后同 |
| `r2-negctl-2-badge-unconditional-*.txt` | (e)② 重跑 | 门④ FAILED，红在验伪锚；sha 前后同 |
| `r2-negctl-3-missing-as-false-*.txt` | (e)③ 重跑 | 门③ FAILED；sha 前后同 |
| `negctl-4-old-formula-20260917T091406.txt` | **新增负控④**：把三态映射还原成 r1 旧公式 | 门①③ 各红在本轮新加的那条断言上（`True is False` / `False is None`）——证明新断言不是空门；sha 前后同 |
| `r2-file-after-20260917T091523.txt` | (g) 全文件 | 116 passed / rc=0 |
| `r2-pyright-close-20260917T091539.txt` | (h) | `0 errors, 82 warnings` |
| `r2-ruff-20260917T091547.txt` | 判据 5 | `files=2` / All checks passed / rc=0 |
| `r2-unit-close-20260917T091556.txt` | (i) | 5081 passed；`close.nodeids` 与 `base` / `open` 两个 diff 均空 |
| `r2-readonly-live-attribution-*.txt` | (j) **归因版** | 见下 |

### (j) 判据口径更正：从「计数」改成「归因」

开工那次（08:53）现网 `find -newer sentinel` 计数为 **0**；r2 收工复核（09:21）变成
**backups 3 + canvas-vault 2**。逐文件归因后确认**与本卡无关**：作业时间窗跨过了现网
launchd 的两个档 —— 09:00 `memory-health.log`、09:05 每日复习链（`daily-review.log`
末行 `[2026-09-17 09:05:07] vault=canvas-vault generate:new push:accepted`，连带写
`daily-review.canvas-vault.state.json` 与 vault 的 `outputs/今日复习.{md,json}`）。

⚠ **这条判据本身的局限要写清楚**：`find -newer` 抓的是「sentinel 之后**任何人**写的」，
不是「本卡写的」。0 命中时它是充分的；非 0 时必须逐文件归因，否则无法区分
「本卡越界写了现网」与「现网自己的定时作业正常跑了」。归因证据见该存档四条：
runner 自有日志格式、live state 里本卡 11 个测试 vault 名各 0 命中（带验伪锚
`last_result` = 1 命中）、live state 的真实键集合、两个改动文件里零 live 绝对路径。

---

## r3 轮（按 Codex r2 MEDIUM-1 **撤回** `or bool(err)` 余量后重跑）

r2 的 MEDIUM 与 r1 的 MEDIUM 长在同一处：`or bool(err)` 这条「未知值但记了错误 ⇒ True」
的余量，是在 Codex r1 的建议（「由 last_result 的明确枚举决定三态」）**之外多加的**。
r2 进一步指出 `bool(err)` 跑在 `isinstance(err, str)` 门之前，连 `{"last_result": null,
"last_error": 123}` 这种类型都不对的垃圾值都能点亮徽标。
本轮**撤回**该余量（不是再加一层判断）：三态只认 `"pushed"` / `"generated_push_failed"`
两个枚举，其余一律 `(None, None)`；`last_error` 完全不参与判定，只做原因文本。
撤回后两条 MEDIUM 一起消失，且 `_read_push_status` 再无「没有门守着的分支」。

| 文件 | 对应判据 | 结论 |
|---|---|---|
| `r3-g69b-green-*.txt` | (d) 四门 | `collected 4 items` / 4 passed / rc=0 |
| `r3-negctl-1-*.txt` | (e)① 失败枚举分支 degraded 恒 False | 门② FAILED；sha 前后同 |
| `r3-negctl-2-*.txt` | (e)② 徽标条件恒真 | 门④ FAILED，红在验伪锚；sha 前后同 |
| `r3-negctl-3-*.txt` | (e)③ 无 last_result 键分支改 `(False, "")` | 门③ FAILED；sha 前后同 |
| `r3-negctl-4-*.txt` | (e)④ 三态映射还原成 r1 旧公式 | 门① FAILED（`assert True is False`）；sha 前后同 |
| `r3-negctl-5-*.txt` | **新增 (e)⑤** | 见下 |
| `r3-file-after-*.txt` | (g) | 116 passed / rc=0 |
| `r3-pyright-close-*.txt` | (h) | `0 errors, 82 warnings`（三轮不变） |
| `r3-ruff-*.txt` | 判据 5 | `files=2` / All checks passed / rc=0 |
| `r3-unit-close-*.txt` | (i) | 5081 passed；close 与 base / open 两个 diff 均空 |

### 负控⑤ 为什么必须单独有一段

Codex r2 指出：负控④ 会让门③ **先**停在 null 那条断言上，同一次执行**到不了**后面
「未知值」那条断言 —— 所以负控④ 只证明了 null 那一格，没证明未知值那一格。
负控⑤ 专门隔离它：变异成「只保住 null 那一格正确、让未知值冒充成功」，
门③ 于是精确红在 `assert e4["push_degraded"] is None, "未知 last_result 值不是成功依据"`
（`assert False is None`）。这样门③ 的两条断言各自都有一段负控钉住。

### `_read_push_status` 八条分支的门覆盖（r3 收口后逐条对照）

| 分支 | 出口 | 守它的门 |
|---|---|---|
| 读文件 OSError（无文件） | `(None, None)` | 门③ 甲 |
| `json.loads` ValueError（坏 JSON） | `(None, None)` | 门③ 庚 |
| `st` 不是 dict | `(None, None)` | 门③ 己 |
| 无 `last_result` 键 | `(None, None)` | 门③ 乙 |
| `last_result == "pushed"` | `False` | 门① 甲（+ 乙：带陈旧 `last_error` 仍 False） |
| `last_result == "generated_push_failed"` | `True` | 门② 甲 |
| 其余值（含 null / 未知 / 带噪声 last_error） | `(None, None)` | 门③ 丙丁戊（戊含 `last_error` 为字符串与为 `123` 两例） |
| `last_error` 非 str / 编不出 UTF-8 | `(degraded, None)` | 门② 丙（`123`）/ 门② 乙（孤立 surrogate） |

---

## 收尾：Codex 三轮与 D-15

| 轮 | 绑定 SHA | B/H/M/L | 存档 |
|---|---|---|---|
| r1 | `4a972d3a` | 0/0/1/1 | `../codex-review-CARD-G6-9b-r1.md` |
| r2 | `7718ae60` | 0/0/1/0 | `../codex-review-CARD-G6-9b-r2.md` |
| r3 | `baf8a693`（最终 HEAD） | **0/0/0/2** | `../codex-review-CARD-G6-9b-r3.md` |

**D-15 达成**（r3 绑最终 HEAD 且 BLOCKER=0、HIGH=0；3 轮，上限 5）。r3 的两条 LOW
按协议 §1 **登记不修** —— 都是测试覆盖缺口，Codex 原文写明「当前生产实现没有对应错误」；
此时改代码 = 打破刚拿到的终审绑定。逐条移交见验收单 §Codex 轮次记录。

`negctl-mutation-sources-r3.txt` = 五段负控的变异源码（Codex r3 指出「变异源码不在读取面内
⇒ 结论只是条件性推导」，该意见成立，故一并落档供逐字复现）。
