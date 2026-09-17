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
