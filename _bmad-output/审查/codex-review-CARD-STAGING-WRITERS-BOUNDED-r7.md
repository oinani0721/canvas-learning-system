> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p2-outbox · 卡 CARD-STAGING-WRITERS-BOUNDED round-7（H1 整改复核）
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-STAGING-WRITERS-BOUNDED-r7.md)" > _bmad-output/审查/codex-review-CARD-STAGING-WRITERS-BOUNDED-r7.md 2> _bmad-output/审查/codex-review-CARD-STAGING-WRITERS-BOUNDED-r7.stderr </dev/null`
> 审查绑定: `4621946f`（= 最终代码 HEAD；`git --no-pager diff --stat --no-color 4621946f HEAD -- . ':(exclude)_bmad-output'` = 空）
> 会话头自证（抄 `.stderr`，行号括注；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: glm-5.3`（第 5 行） / `reasoning effort: max`（第 9 行）

---

## 裁决

**生产语义：PASS。** 未发现 BLOCKER / HIGH / MEDIUM 运行时缺陷；r6 HIGH 的两处死信裸追加问题已在进程内写者语义上修复。

**测试/门收口：PARTIAL。** 有 3 条 LOW，均为“分支或扫描器未被现有门覆盖”，不是当前运行时错误。

绑定核对：

- 当前 `HEAD = 4621946f99f11e2047cac6c0b29667360aaf6f8c`
- `4621946f` 的 parent 是 `49c545b6fbcf19c040c3b0fdc1ee7cdd90d63a90`
- `49c545b6..4621946f` 的代码改动确实只有 3 个文件：
  - `backend/app/core/failure_counters.py`
  - `backend/app/services/episode_worker.py`
  - `backend/tests/unit/test_staging_writers_bounded.py`
- `backend/app/core/failed_writes_constants.py` 在两 ref 的 blob 均为 `6ee6e34fac080ba15f1b3aed04dc2cbe4c0eda62`，确认一字未改。
- 本轮只读复核；未运行服务、未连库、未复跑 pytest/pyright。

---

## 发现清单

```text
[LOW] backend/tests/unit/test_staging_writers_bounded.py:839 — DeadLetterStore.store 的新负控只覆盖 ensure_line_boundary 返回 True 的“半行可补换行”路径，未覆盖 False => sep="\n" 调用方分支。
  复现思路：未被拦下的输入——把 episode_worker.py:288 的表达式改成恒 sep=""，在补换行可成功的 b'{"epi' 输入下本测试仍绿；现有 test_flush_does_not_glue_when_boundary_repair_fails 只能约束 failed_writes flush 链，不能约束这个新调用点。
```

```text
[LOW] backend/tests/unit/test_staging_writers_bounded.py:869 — write_dead_letter 的新负控同样未覆盖 ensure_line_boundary 返回 False 后由 failure_counters 调用方并入首行分隔符的分支。
  复现思路：未被拦下的输入——把 failure_counters.py:372 的 else 分支改成空分隔符，并让补换行那次 append 失败；本测试与既有 failed_writes 对照门都不会红。
```

```text
[LOW] backend/tests/unit/test_staging_writers_bounded.py:1030 — 文件本地 AST 隔离门的 _DEAD_LETTER_CHAIN 只识别 DeadLetterStore，不识别 fc.write_dead_letter。
  复现思路：门未覆盖的路径——新增一个不带 tmp_path/隔离 fixture 的 def test_x(): fc.write_dead_letter(<现网路径>, ...)，test_every_staging_test_isolates_live_files 仍会绿；本轮新测试自己显式使用 tmp_path，因此当前绿来自路径选择，不来自扫描器拦截。
```

---

## 逐项结论

### ① 锁语义：成立；docstring 举例滞后但无实际锁风险

两处都在 `_dead_letter_io_lock` 的同一临界区内完成「轮转 → 探边界/补边界 → 追加」：

- `episode_worker.py:270-290`
- `failure_counters.py:363-374`

`ensure_line_boundary` 本体不取锁，真实要求是：调用方已持有保护该目标文件 IO 序列的锁。对这两条死信链而言，`_dead_letter_io_lock` 正是那个锁；且本轮读取面内的两个死信写者用的是同一把锁，因此进程内不会出现“一个写者探测、另一个写者追加”的交错。

`failed_writes_constants.py:309-310` 仍举例说必须持 `failed_writes_lock`，这是文档措辞滞后；但它是例子与实际锁名不一致，不是互斥语义缺失。我不将它升为运行时缺陷。跨进程并发写同一文件仍不在 threading.Lock 覆盖面内，这是既有限制，非本修复引入或恶化。

### ② 惰性/局部 import：成立，无成环或半初始化问题

`failed_writes_constants.py:16` 顶层导入 `failure_counters`，所以 `failure_counters.py:370` 若改成顶层反向导入会成环；函数内惰性 import 是必要的。

可达性也成立：

- `write_dead_letter` 定义在 `failure_counters.py:306`，而 `failed_writes_constants` 顶层需要的 `bound_from_env` / `count_lines` / `rotate_if_over_limit` 都在更早位置已定义。
- 即使 `failure_counters` 先被单独完整导入，调用 `write_dead_letter` 时再导入 `failed_writes_constants`，其顶层反向 import 也能从已完整的 `failure_counters` 拿到名字。
- `episode_worker.py:286` 的局部 import 只在调用期执行，把改动面收在 `DeadLetterStore.store` 内；未发现 import lock 与 `_dead_letter_io_lock` 的反向嵌套路径。

### ③ False 路径的首行分隔符：实现正确；计数侧有一个保守性副作用

分两种情况：

1. **确认半行且补换行失败**：最终追加 `"\n" + record + "\n"`，字节形态是 `半行\n记录\n`。尾巴和记录不粘连，中间没有空行。
2. **探测本身失败但文件其实已在边界**：最终会额外写一个前导换行，可能形成空行。若探测失败持续存在，每次写都可能多一个空行。

读侧影响：按本测试与 JSONL 常规读法，空行会被跳过，不污染可解析记录。计数侧影响：`count_lines` 按 `b"\n"` 计数，因此额外空行会增加计数，可能让轮转提前发生。这是 `ensure_line_boundary` 既有的“宁可保守分隔/提前轮转，也不粘连或拒写”取舍；相比静默丢死信，方向正确。我没有找到本轮修复因此变得更糟的因果链。

### ④ 先轮转、后探边界：进程内无窗口

两处顺序都是：

1. `rotate_if_over_limit(...)`
2. `ensure_line_boundary(...)`
3. append record

整段都在 `_dead_letter_io_lock` 内。若真轮转发生，活动文件不存在或为空，`ensure_line_boundary` 自然返回 True，不需要显式清 `sep`。若轮转失败，探测仍作用于原活动文件，False fallback 仍防粘连。

因此进程内没有“轮转与探测之间”的可利用窗口。跨进程仍可能在 rename 与 append 间交错，这是原实现已明示的非原子限制；本修复没有扩大它。

### ⑤ pyright：未发现新增 ignore 掩盖

两 ref 的 diff 中没有任何新增 `pyright: ignore` 或 `type: ignore`。对四个读取面文件做静态 grep 也没有发现相关抑制。此处只独立核对了抑制项，未复跑 pyright。

### ⑥ 其它问题

没有发现新的运行时问题。作者自述的红演示与套件通过数字未在本轮复跑；静态复核显示：

- 还原两处旧裸写时，新增两条“可修复半行”负控确实会红；
- 但“探测/补换行失败”路径的死信调用方变异不会被现有门拦下，即上面前两条 LOW；
- AST 隔离门对 `fc.write_dead_letter` 有漏识别，即第三条 LOW。

**总体结论：H1 生产整改成立；可收口，建议把上述测试/AST 门缺口登记为后续小补丁。**
