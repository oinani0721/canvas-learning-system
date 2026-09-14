# evidence-tail-cleanup — CARD-TAIL-CLEANUP-LOOP 存档索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-TAIL-CLEANUP-LOOP]` · 车道 `card-t5-bugs` · 基准 `B14_BASE` = `08100483`

## 为什么有两批存档（如实）

代码定稿过程中做了一次**只收行不改语义**的编辑：`ruff format --diff` 显示我新增的 4 处
`assert ..., ( "…" )` 想被收成一行，而那 4 处**落在本卡新增行内** —— 若不处理，「format 漂移
全是主干既有」这句话就不成立。收行后**行号整体下移**（承重断言 `:297 → :291`），因此所有
承重裁判**重跑一遍绑最终代码**，文件名带 `-final-`。

早期那批**不是失败运行**，结论与 `-final-` 一致，只是绑的是收行前的行号。
车道树 guard hook 禁 `rm`，故保留；**引用一律用 `-final-` 那份**。

## 权威 / 被取代对照

| 判据 | 权威存档（绑最终代码） | 被取代（收行前，结论同） |
|---|---|---|
| (a) 第 0 分钟自证 | `a-minute0-selfproof-20260914T194929.txt` | — |
| (b)① 根因门 先红 | `b1-rootcause-gate-RED-20260914T195006.txt` | — |
| (b)② TestCleanupScheduler 先红 | `b2-testcleanupscheduler-RED-20260914T195230.txt` | — |
| (d) 根因门 后绿 | `d1-rootcause-gate-GREEN-final-20260914T200600.txt` | `d1-rootcause-gate-GREEN-20260914T195454.txt` |
| (d) 测试 A/B 后绿 | `d2-testcleanupscheduler-GREEN-final-20260914T200600.txt` | `d2-testcleanupscheduler-GREEN-20260914T195454.txt` |
| (e) 负控 1+2 | `e-negctl-final-20260914T200649.txt` | `e1-negctl-config-field-renamed-20260914T195543.txt`（显示过滤把回溯定位行滤掉了）、`e1-negctl-config-field-renamed-locline-20260914T195634.txt`、`e2-negctl-backoff-await-removed-20260914T195705.txt` |
| (g) tests/unit 目录级 | `g-unit-close-final-20260914T200748.txt` + `base.nodeids` / `close.nodeids` | `g-unit-close-20260914T195745.txt` |
| (h) pyright app | `h-pyright-app-final-20260914T200600.txt` | `h-pyright-app-20260914T195518.txt` |
| (i) ruff check + 验伪锚 | `i-ruff-20260914T200503.txt` | — |
| (i) format 漂移归因 | `i2-ruffformat-drift-attribution-final-20260914T200740.txt` | `i2-ruffformat-drift-preexisting-20260914T200526.txt` |

## 两条容易误判的地方（给集成期复核）

1. **`a-minute0-selfproof-*.txt` 里含 `No such file`** —— 那是**故意的正向证据**：
   `ls backend/app/core/config.py` / `ls backend/app/core/background_task_manager.py` 都必须
   报「不存在」，才证明 §〇 的两条路径更正（设计稿写 `core/`，实测在 `services/` 与
   `app/config.py`）成立。**不是失败运行产物**，协议 §2.2「含 No such file 不入库」指的是
   裁判跑挂了的产物，不适用于本条。

2. **`b2-…-RED-*.txt` 头部第 2 行自身含 `AssertionError` / `AttributeError` 字样** ——
   首次内联自证因此把头部也 grep 进去，报出 `AttributeError 命中=1` 的假阳性。该文件
   末尾已附「判据自污染更正」段：按 `---` 之后的正文重判为 `AttributeError = 0`，并带
   同次验伪锚（正文 `Error` 总命中 = 2，证明 0 不是 grep 坏了）。
