> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-6 round-2 prompt-2（重发）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-6-r2.md)"`
> 审查绑定: `39d6c93c7ef67aa4aeea4c6bf11ed45a6d7be2f1` + **当时未提交的工作区改动**（本轮之后又有 round-2 整改，故本轮不绑最终 HEAD；末轮见 round-3 存档）
> 会话头自证（抄 .stderr 会话头含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `sandbox: read-only`
>
> 首发（`codex-review-CARD-G6-6-r2.md`）因配额耗尽 0 字节中断；本份是协议 §2.2 要求的那次重发，配额已恢复。

---

审查基于 `72ab01ed → 39d6c93c`，以下行号以 HEAD 为准；未提交变更另行注明。全程只读，未连接数据库或网络服务。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW：4 条，其中第 4 条已由未提交变更修正。**

1. **推迟键会与另一库的完成键碰撞。**  
   [review_app.py:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:214)

   具体场景：两个库分别叫 `math`、`snooze:math`，均有板 `A`。此时：
   ```js
   snoozeKey("math", "A") === doneKey("snooze:math", "A")
   ```
   `math/A` 推迟请求在飞时，另一库的完成按钮被错误禁用；完成 handler 也会静默返回。执行 HEAD 的实际 JS 已复现禁用及 `POST=0`。后端允许这些目录名。

2. **DST 门不能抓住“沿用今天固定偏移”的回归。**  
   [test_review_overview.py:3995](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:3995)

   现有纽约两组输入均在切换完成后的上午，今天与次日零点的偏移相同。把实现变成 `timezone(now_local.utcoffset())`，这两组结果仍逐字相同。

   具体漏检场景：`America/Nuuk`，`2026-03-28T10:00-02:00` → 正确结果为 `2026-03-29T00:00-01:00`；错误实现会晚一小时唤醒。秋季对应场景会早一小时。

   **生产实现当前正确，问题在测试覆盖。** 未提交注释所称“没有这种现行 IANA 时区”不成立，尚未闭合此缺口。

3. **busy 新门没有覆盖完整的 handler→重绘链及取回分支。**  
   [test_review_app.py:3141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_app.py:3141)

   测试直接构造 `busy[snoozeKey(...)]`，没有让 handler 建立该状态。独立内存变异发现：

   - 只把取回渲染侧改回 `unsnoozeBusy[doneKey(...)]`；
   - 或只把推迟 handler 改回 `doneKey(...)`；

   四个 G66 JS 门、14 个子测试仍全部通过。前者会让取回请求在飞期间重绘出的按钮提前恢复可点；后者重现写键与读键不一致。现有变异证据同时改两处渲染分支，不能证明两处分别受到保护。

4. **损坏条目日志错误标识所属库。**  
   [review_overview.py:2499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2499)

   两个不同库分别存在孤立 surrogate 板名时，日志均记录 `vault=backups`，无法定位所属账本。这里的 `parent.name` 正常情况下是 ASCII `backups`，因此问题是诊断标识错误，并非再次编码失败。**工作区改为记录 state 文件名，已修正此项。**

其余问题的核对结果：

| 问题 | 结论 |
|---|---|
| 1：时钟与 DST | 两档换算使用 `_display_now()` 所取时区，未发现第三套时钟或 `_DISPLAY_TZ*` 常量；Nuuk 双向探针确认目标日期偏移正确。午夜跳时导致 `00:00` 本身不存在的情况，仍属于未规定的边界语义。 |
| 2：非法值与金样 | 指定非法输入均退化为空活跃集；两条金样门未改，精确 payload 比较能抓新增顶层键。 |
| 3：缓存 | v2 缺签名且空账不会因此白重扫；正常唤醒点越界即可独立触发重扫。两项先分别求值，最终短路不会吞掉唤醒。 |
| 4：只读与坏值 | 读侧不调用 state 隔离／修复写路径；中文、emoji、重音字符保留，surrogate 丢弃，极值时间标签有降级保护。 |
| 5：FSRS | 既有三项写面允许集未放宽；新增负控明确要求失败消息包含 `_FSRS_GATE_MSG`，并先确认请求及落账成功。 |
| 6：POST 与 20:00 | 新 POST 仅由点击触发。JS 不比较小时数。GET 内布尔与活跃过滤共用一次读数；POST 内换算与 422 共用另一次读数。**GET、POST 跨请求并非同一次读数**，跨 20:00 的竞态由 422 处理。 |
| 7、8：入口与分区 | 无节点级或自定义时长入口，无静默夹档；空活跃集不增加折叠区，完成且推迟的板只渲染一次。两条既有 details 计数断言未改。 |
| 9：合约门 | AST 两表各只加 `_SNOOZE_NOTE`；检查器与探针矩阵未改。四条枚举门仍为精确登记。 |
| 10：升版断言 | 实际是 **4 个既有测试中的 6 条断言**，均检查升版结果，跟随常量正当；输入版本字面量及高版本不降级门保留，另有实值 `== 3` 门。 |

round-2 的 M-1～M-4 原失败路径已闭合。M-3 极值仍保持活跃，只跳过无法表达的 UTC 唤醒点；其他原因重扫也不会使其自动过期。LOW-1 的 `finally` 覆盖 import 异常，替换后的门确实观察 import 时的标志；没有把仅人工双线程可复现、尚无生产交叠路径的现象列为缺陷。

验证包括源码／差异核对、Python 内存探针，以及实际 JS 的 14 个子测试和独立变异；未运行需要写入临时文件或 state 的 pytest。


