> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-BOUND round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-BOUND-r2.md)"`
> 审查绑定: `26bf4a2e..b8cd3a82`（前一轮：r1 审 47075cbe）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `stderr:2 OpenAI Codex v0.153.3` / `stderr:5 model: gpt-6-astra` / `stderr:9 reasoning effort: ultra`

---

## 结论

**暂不建议放行 `b8cd3a82`：BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 3。**

已确认完整 HEAD 为 `b8cd3a82fe6ee036eff8e26f5d2b0cc676e9fca7`。全程只读；验证采用源码检查、原函数 AST 提取后的纯内存复现及隔离路由调用，**未运行 pytest、未连接数据库、未写现网数据**。

## BLOCKER：0

## HIGH：1

### H1．回灌守卫遗漏遗留 checkpoint，新追加记录会被跳过并误标为已回灌

**位置：** [failed_writes_constants.py:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:128)，轮转调用在同文件 `:147`。

`_sync_all_lock` 已释放，不代表旧文件对应的持久化游标已经清除。新写侧只检查锁，允许文件换代，却保留旧游标。

**已复现，无需进程崩溃：**

1. 原文件 51 条；回灌保存 `index=50`。
2. finalize 重读发生一次 `PermissionError`，保留文件和 checkpoint，随后释放回灌锁。
3. 写侧追加新条目 `z`：

| 对照条件 | 下一轮实际重放 | 结果 |
|---|---|---|
| `max_lines=100`，不轮转 | 第 51 条、`z` | `z` 得到重放 |
| `max_lines=50`，发生轮转 | 空列表 | 新文件中的 `z` 被旧游标跳过，返回 `pending=0`，文件改名为 `.synced.*` |

这是本卡新增轮转引入的文件代际失配；`z` 从未进入 overflow，也没有经过 retention 删除，**不属于已披露的取舍**。

现有测试 `test_dead_letter_bounded_t6c.py:454、475` 只测持锁/未持锁时是否轮转，没有覆盖遗留 checkpoint 后再次回灌。

## MEDIUM：3

### M1．权限不足仍可能被报成“完整、零积压”

**位置：** [traces.py:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:250)，关联 `failure_counters.py:104`。

当前 venv 为 **Python 3.14.4**，原生 `Path.exists()` 会吞掉权限异常。父目录及活动文件的存在性检查失败时，分别返回空兄弟列表和“不存在”，绕过新增的异常标记。

**已复现：** 底层检查实际抛出 `PermissionError`，结果仍为：

```text
exists=False, backlog=0, partial=False, degraded=[]
total_backlog=0, incomplete=False
```

测试 `test_traces_backlog_t6c.py:270` 直接替换整个 `overflow_siblings` 使其抛错，覆盖不到内部 `exists()` 吞错的路径。

### M2．异常 Unicode 时间戳会使整个端点返回 500

**位置：** [traces.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:192)。

对照输入：

- `{"timestamp":"2026-09-01T00:00:00Z"}` → **200**
- ASCII JSONL 文本 `{"timestamp":"\ud800"}` → **500**

`json.loads` 接受该转义并产生孤立代理字符；`str(ts)` 原样返回，随后响应的 UTF-8 序列化抛出 `UnicodeEncodeError`。异常发生在 `_safe_backlog_entry` 之外，因此一条坏记录会使整条路由失败。已用真实 FastAPI/Starlette 响应路径确认。

### M3．尺寸闸未限制检查之后的实际读取量

**位置：** [traces.py:170](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:170)，读取在 `:177–178`。

交错为：`stat` 时未超限 → 写者追加超长行 → 扫描器开始读取。后续 `for line` 没有字节预算，仍可把整条超长记录读入内存。

**纯内存复现：** `max_bytes=1`、检查时大小为 1、读取时已有 10053 字节，扫描仍完成且 `reason=None`。现有超限测试只覆盖扫描前已经超限的文件。

## LOW：3

### L1．第 101 个同时间戳名称仍会破坏“删最老”

**位置：** [failure_counters.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failure_counters.py:139)。

冻结时间并预占 `-00.jsonl` 至 `-99.jsonl` 后，兜底名称 `-99-<uuid>.jsonl` 排在旧 `-99.jsonl` **之前**；保留一份时会删掉最新归档。触发条件极端，但“族内仍排最后”的注释不成立。现有碰撞测试只测到 `-02`。

### L2．轮转及扫描的异常保护仍缺少实际故障输入

**位置：** [test_dead_letter_bounded_t6c.py:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:358)。

这里只替换 `fwc.count_lines`；轮转函数使用的是 `fc.count_lines`，因此没有触达 `failure_counters.py:196–198` 的数行失败分支，`:203–205` 的 rename 失败分支也缺少输入。

同样，`test_traces_backlog_t6c.py:291` 替换整个时间戳扫描器，只验证标签传播，没有验证真实扫描器的 stat/read 异常处理。

### L3．存在恒真断言及测试名称与输入不符

**位置：** [test_dead_letter_bounded_t6c.py:545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:545)、[test_traces_backlog_t6c.py:412](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:412)。

- `assert ".overflow." in n` 恒真：`n` 已由同文件 `:42` 按此条件筛选；旁边的 `.jsonl` 断言有效。
- 名为 `anchor_is_root` 的测试实际传入 `/nonexistent-anchor-t6c`，只测试锚外 fallback，没有测试 `/`。
- `test_traces_backlog_t6c.py:448` 的总数断言无法区分“忽略 None”和“把 None 当 0 求和”，两者结果都为 2。

## 其余重点核对结果

- **进程内锁覆盖成立，未发现二次获取路径。** 两处 memory 写者和 agent 旁路共享文件锁；两个 helper 不自取锁；dead-letter 写锁与计数锁没有嵌套。跨进程非原子已有披露，但存在性检查不能保证跨进程不覆盖。
- **活跃回灌窗口内的守卫有效；挂住时没有时限保证。** `_sync_all_lock` 覆盖健康检查及其他回灌链，任一阶段持续占锁，failed_writes 就持续裸追加。“暂时越限”不能解释为有界等待。
- **路径修正符合写侧。** audit 锚点正确；bug_log、episode 的 cwd 限制已明确记录。未发现本次改动新增任意文件读取入口。
- **后缀隔离成立。** 新 `.overflow.*.jsonl` 可被兄弟发现逻辑识别，不会被既有 `.synced.` 清理处理。
- **env 未发现导入崩溃。** 无效值、负数及超过整数转换位数限制的值回默认；巨大合法正整数会放宽上限。环境变量 `MAX_LINES=0` 回默认，直接调用 helper 的 `max_lines<=0` 才关闭轮转；`max_rotations=0` 确实立即清空归档。
- **48 条测试确为 24＋24。** 零保留分支、未达阈值、关闭轮转，以及 `_display_path` 成功/异常 fallback 均有有效断言。
- **已知限制的代码披露已收紧。** overflow 无回灌、保留超限删除、纯 agent 写入可无限增长都写明了；请求背景中的“暂时越限”仍比当前代码文档更强。H1 则使守卫注释中的“不丢数据”仍然不成立。


