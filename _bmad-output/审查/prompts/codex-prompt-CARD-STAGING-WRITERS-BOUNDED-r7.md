# 对抗性代码复核 — CARD-STAGING-WRITERS-BOUNDED H1 整改（BATCH-2026-09-18-第十五批 · round-7）

## ① 背景与最小读取面（只读这些，不要全仓扫）

本仓是 Tauri + React + FastAPI 的桌面学习系统。本卡（CARD-STAGING-WRITERS-BOUNDED）此前已收口；
**本轮 = zcode 补审 r6 发现的唯一 HIGH 的整改复核**：`DeadLetterStore.store`（episode_worker.py）与
同型残留 `write_dead_letter`（failure_counters.py）在各自 IO 锁下裸追加、无行边界防护 ——
上次写半行（ENOSPC/EIO）后下一条死信粘尾成不可解析行，且死信**无重试缓冲** ⇒ 静默丢失。
整改：两处均复用 `ensure_line_boundary`（补得上就补换行；探测失败就把分隔符并进本条第一行 ——
任何情况下都不粘连、不拒写）。

审查绑定：`PREV = 49c545b6`，`审SHA = 4621946f`（= 当前 HEAD）。
r6 评审全文（只读参照）：`_bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md` 的 HIGH 段。

最小读取面（逐条，不要超出）：

1. `git --no-pager diff --no-color 49c545b6 4621946f -- . ':(exclude)_bmad-output'` —— 本轮整改全部改动（3 文件）
2. `backend/app/services/episode_worker.py`：`DeadLetterStore.store` 全段（含 `_dead_letter_io_lock` 与局部 import）
3. `backend/app/core/failure_counters.py`：`write_dead_letter` 全段（含惰性 import）
4. `backend/app/core/failed_writes_constants.py`：`ensure_line_boundary`（只读引用；本修复**一字未改**，
   其 docstring 的锁举例为 `failed_writes_lock`）
5. 新测试 3 条：`backend/tests/unit/test_staging_writers_bounded.py` 的
   `test_dead_letter_store_does_not_concatenate_onto_dangling_tail` /
   `test_write_dead_letter_does_not_concatenate_onto_dangling_tail` /
   `test_failed_writes_chain_repairs_dangling_tail_control`（+ 文件本地隔离扫描器）
6. 既有对照范式：同文件 `test_third_writer_does_not_concatenate_onto_dangling_tail` /
   `test_flush_does_not_glue_when_boundary_repair_fails`

## ② 作者自述 —— 请独立核对，不要采信

1. 两处写者都在**各自 IO 锁**下复用 `ensure_line_boundary`：`store` 持 `_dead_letter_io_lock`；
   `write_dead_letter` 亦在同锁区内。语义与 failed_writes 链一致：True=已知在边界（补过/无需补）；
   False=不能确定 ⇒ `sep="\n"` 并进本条第一行（**不拒写** —— 两处写者都没有重试缓冲）。
2. 顺序 = **先轮转、后探边界**（与 `append_failed_writes_bounded` 一致）：轮转后文件为空 ⇒ 探测自然 True，
   不需要「真轮转后清 sep」的舞步。
3. `failure_counters` 侧用**惰性 import**（`from app.core.failed_writes_constants import ensure_line_boundary`
   在函数内）—— 该模块被 failed_writes_constants 顶层导入，顶层反向 import 会成环；调用期两侧必已加载完整。
   `episode_worker` 侧同样用局部 import（把 diff 收在 DeadLetterStore 段内 = 本修复硬边界）。
4. 新测试 3 条：两负控（预置 `b'{"epi'` 半行尾巴后 store / write_dead_letter 各一条 ⇒ 断言尾巴行原样保留、
   新记录自成可解析行、无粘连）+ 一对照（同输入走 failed_writes 链先补换行）；隔离扫描器（文件本地 AST 门）过。
5. **红演示**（先红后绿）：临时还原两处旧裸写 ⇒ 两负控 FAILED、对照仍 PASSED；还原修复后 staging 29 passed。
6. 承重裁判：点名套件 189 passed / unit 目录级 32F·5778P 对基线 diff 只 `<` / pyright 成对 0 errors
   （82 warnings 不变，零新增 ignore）。
7. `ensure_line_boundary` 本体未动（不在本修复硬边界内）：其 docstring 的锁举例为 `failed_writes_lock`，
   本复用持 `_dead_letter_io_lock` —— 语义等价（护同一文件的 IO 临界区），措辞未同步，如实登记。

## ③ 按重要性排序的问题（逐项给结论）

- **①** 锁语义：两处复用都在各自文件的 IO 锁内吗？`ensure_line_boundary` docstring 的举例差异是否有实际风险？
- **②** 惰性/局部 import：有无成环或半初始化风险？调用期可达性？
- **③** 探测失败路径（`sep="\n"` 并入首行）：在死信链是否会产生多余空行污染（读侧 / 计数侧口径）？
- **④** 「先轮转、后探边界」次序：是否存在窗口（如轮转与探测之间）？
- **⑤** pyright 0 是否靠 ignore 掩盖？（本修复零新增 ignore）
- **⑥** 若发现其它真问题，照报。
- **Jev 分诊（urgency 降序，§2.4.3；落 `evidence-staging-writers-bounded/jev-triage-4621946f.json`）**：

  | 文件 | urgency | risk |
  |---|---|---|
  | `episode_worker.py` | 2.81 | logic |
  | `failure_counters.py` | 2.33 | logic |
  | `test_staging_writers_bounded.py` | 1.75 | test_or_docs |

## ④ 输出格式

逐条给：

```
[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话结论>
  复现思路：<一句，用下列措辞>
```

措辞请用：**负控输入**（把某处改回旧写法后哪条门会红）、**对照输入**（同族里必须仍绿的那条）、
**未被拦下的输入**（某个取值/顺序/时序没有被现有判据挡住）、**门未覆盖的路径**（代码里没有任何门经过的分支）。

## ⑤ 边界

- **只读**。不要修改任何文件，不要提出需要运行服务或连接数据库的验证步骤。
- **只审本轮整改面**（上述 5 条读取面）：卡已收口，r6 的其余 LOW 与整卡重审不在本轮范围；
  P2-C（回灌重写）面不在本轮范围。
- 不连库；本修复零连库。
- 若你认为本修复**让既有行为变得更糟**，那属于本轮范围，请明确说出因果链。
