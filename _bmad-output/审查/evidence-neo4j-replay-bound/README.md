# evidence-neo4j-replay-bound — CARD-NEO4J-REPLAY-BOUND（T6-C）证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-NEO4J-REPLAY-BOUND]` · `T6B_TIP = 26bf4a2e` · 代码 commit `47075cbe`。
> 逐份标注「权威 / 被取代」——车道树 guard hook 拦 `rm`，被取代的存档只能保留不能删。

| 文件 | 权威? | 是什么 |
|---|---|---|
| `unit-open-20260915T115331.txt` | **权威** | 开工 `tests/unit` 目录级（425.88s）。33 failed / 5079 passed / 29 errors，rc=1 |
| `open.nodeids` | **权威** | 上一条的 nodeid 口径（62 行）。⚠️ 该跑 collection 早于本卡新测试文件创建，`grep -c t6c` = 0 |
| `base.nodeids` | **权威** | `$BASE`（feature 主干树 `unit-red-baseline-08100483.txt`）去注释排序后的 64 行 |
| `red-t6c-20260915T115509.txt` | **被取代** | 先红第一版：16 failed / 7 passed。被 `red-t6c-strengthened-*` 取代的原因见下 |
| `red-t6c-strengthened-*.txt` | **权威** | 加固后的先红（仅 dead-letter 文件）：7 failed / 3 passed。初版有 3 条门在改前是**平凡绿**（零轮转时结论自动成立），补前置断言后才真正承重 |
| `green-t6c-*.txt` | **被取代** | 中途的后绿跑（当时 5 failed，正在修「单批超限」与 `NameError: _count_lines`） |
| `green-t6c-final-*.txt` | **权威** | 后绿：23 passed，rc=0 |
| `green-plus-neighbors-*.txt` | **权威** | 后绿 + 邻近三套件合跑：61 passed / 3 skipped，rc=0 |
| `neighbors-close-*.txt` | **权威** | 邻近三套件收工单跑：38 passed / 3 skipped，rc=0 |
| `neighbors-open-*.txt` | **权威** | **对照输入**：4 个生产文件用 `git show $T6B_TIP:` 写回后的邻近三套件 = 开工基线。38 passed / 3 skipped。同跑内打印 `DATA_DIR = …parent.parent.parent.parent / "data"` 自证确在改前态 |
| `negctl-1-*.txt` | **权威** | 负控①：删掉两处 `rotate_if_over_limit(...)` 调用。7 failed，红在「活动文件超行数: 8 > 上限 5」。shasum 前后逐行同 |
| `negctl-2-*.txt` | **权威** | 负控②：`OVERFLOW_SUFFIX` `.overflow.` → `.synced.`。承重断言红在「`.synced.` 兄弟被本卡 retention 误删」，日志逐字佐证清理了 `failed_edge_syncs.synced.2020-01-01-000000` |
| `pyright-*.txt` | **被取代** | format 调整前的 pyright（0 errors / 81 warnings） |
| `pyright-final-*.txt` | **权威** | 最终 pyright：`0 errors, 81 warnings, 0 informations`，与 `08100483` 基线持平 |
| `ruff-*.txt` | **权威** | 6 文件 `ruff check` rc=0 + 验伪锚（F821 探针 rc=1 有效 / F401 探针 rc=0 = 该锚在 backend 恒不触发） |
| `openapi-drift-*.txt` | **权威** | `check-openapi-drift.py --write` 取证：paths 199（快照 197），numstat 66+/1-，内容 = 本卡新路由 + `x-generated-at`。取证后已写回 HEAD 态，本卡不 commit 该文件 |
| `commit-20260915T*.txt` | **权威** | **裸跑被 `python-lint` 拦下**的原始输出（协议 §2.3 要求）：`3 files would be reformatted, 3 files already formatted` |
| `commit-ok-*.txt` | **权威** | 带 `LEFTHOOK_EXCLUDE=python-lint,spec-sync-flat,spec-sync-root` 的成功 commit。`python-typecheck` **未**排除且跑绿 |
| `unit-close-20260915T121549.txt` / `close.nodeids` | **被取代** | round-1 的收工目录级跑（5102 passed）。r2 改了代码后由下面那份取代 |
| `unit-close-r2-*.txt` / `close-r2.nodeids` / `close-r2.diff` | **权威** | 最终收工目录级跑：`33 failed, 5127 passed, 29 errors`，62 nodeids，相对开工**新增 `>` = 0** |

## round-2（收口 Codex r1 + 内部对抗复核）新增

| 文件 | 权威? | 是什么 |
|---|---|---|
| `selfreview-workflow-20260915.md` | **权威** | **入库的内部对抗性复核**（协议 §五.5）。5 维度找 → 每条 3 镜头独立证伪。38 条发现 → 存活 20（BLOCKER 1 / HIGH 5 / MEDIUM 10 / LOW 4）、证伪 18，含逐条原文。⚠️ 绑 `47075cbe` 且**审查期间对象未冻结**；⚠️ 26 个 verify agent 因 API 错误未跑成 ⇒ 覆盖不完整，票数已逐条标注 |
| `negctl-3-r1fixes-*.txt` | **权威** | 负控③：逐条还原 Codex r1 的修复。**六段**（M1a/M1b/L3a/L3b/M2/L2）全部 `rc=1` 红在指定门，还原 shasum 逐字节同 |
| `negctl-4-replay-window-*.txt` | **权威** | 负控④：回灌窗口守卫。A 摘掉守卫 ⇒ 窗口门红；B 守卫恒真 ⇒ 控制组红（防「永不轮转」蒙混）。还原 shasum 同 |
| `green-r2-*.txt` | **被取代** | r2 中途的门跑 |
| `green-r2-final-*.txt` | **权威** | 最终门 + 全部触碰 `FAILED_WRITES_FILE` 的 9 个套件：`168 passed / 2 failed`。两条红**均在开工基线 `open.nodeids` 里**（既有红，已逐条核） |
| `pyright-r2-final-*.txt` | **权威** | 最终 pyright：`0 errors, 81 warnings` |
| `commit-r2-*.txt` | **权威** | r2 commit（`b8cd3a82`）。`python-typecheck` 未排除且 `exit: 0` |
| `codex-review-*` | — | 见 `_bmad-output/审查/`（不在本目录）。r1 存档已按协议 §2.1 补六行首部，三字段均由 stderr 自证（`:2` / `:5` / `:9`） |

## 口径备注

- 数行一律 `b"\n"` 计数（生产 `count_lines` 与测试 `_nlines` 同口径）；**不用** `splitlines()`——它在 U+2028/U+2029 处额外切行。
- git 输出一律 `git --no-pager … --no-color`。
- `*.stderr*` 不入库（`.gitignore` 覆盖）。
