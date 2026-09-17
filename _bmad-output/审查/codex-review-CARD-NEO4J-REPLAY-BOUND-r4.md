> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-BOUND round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-BOUND-r4.md)"`
> 审查绑定: `26bf4a2e..09d6da33`（前一轮：r3 审 11caca05）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `stderr:2 OpenAI Codex v0.153.3` / `stderr:5 model: gpt-6-astra` / `stderr:9 reasoning effort: ultra`

---

**结论：BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 7。当前不能认定 round-3 的问题全部收口。**

审查绑定 `09d6da33bb738d6b4a512520c403b3299e9d0574`。三个并行审查方向已交叉核对；反例仅在内存中执行提取的真实函数。未修改文件、未连接数据库、未读取现网数据，也未运行存在写入风险的 pytest。

**HIGH 2**

1. **checkpoint 探测失败会被当成“游标已作废”，允许错误换代。**  
   [failed_writes_constants.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:134) 使用 `Path.exists()`；当前 Python **3.14.4** 会将 checkpoint 的瞬时 `EIO` 吞成 `False`，随后函数返回 `True`。  
   内存对照已复现：正常探测→删除旧游标、允许轮转；仅让 checkpoint 的 `os.stat` 抛 `EIO`→**没有执行任何读取或删除，仍允许轮转，旧游标保留**。故障恢复后，旧代游标会关联新代文件。这不属于已披露的 overflow retention 丢弃。

2. **HIGH-2 的现网隔离修复仍漏了一个测试。**  
   [test_dead_letter_bounded_t6c.py:531](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:531) 未申请 `bounded_failed_writes`，也未重定向 `fss.SYNC_CHECKPOINT_FILE`；两级 conftest 没有额外隔离。  
   对照：现网 checkpoint 不存在时无动作；若存在 `{"failed_writes":{"index":9}}`，该测试设置上限 1 后的**第二次追加就会删除它**，测试仍可通过。`:849` 的指针门仅验证 fixture，覆盖不到这个未使用 fixture 的用例。

**MEDIUM 1**

1. **不丢批的容量说明漏掉了活动文件的初始占用。**  
   [failed_writes_constants.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:211) 给出的 `max_lines × (max_rotations + 1)` 不足以作为保住本批的判据。  
   真实分块与 retention 算法的内存对照：`L=5、K=1`，空文件追加 7 条→全部保留；**原有 4 条再追加同样 7 条→本批 `new0` 被删除**。第一份 overflow 包含旧 4 条及 `new0`，第二次轮转会删除它。这里要求纠正限制说明和验收判据，不是在否定已授权的 retention 取舍。

**LOW 7**

| 位置 | 问题及可区分的反例 |
|---|---|
| [test_dead_letter_bounded_t6c.py:814](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:814) | **“never raises” 没测到扩大后的外层捕获。** 把外层改回 `except OSError`，现有五种输入仍全部通过；加入嵌套 2000 层 JSON，当前返回 `False`，变异版本抛 `RecursionError`。 |
| [test_dead_letter_bounded_t6c.py:803](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:803) | **H1b 只核其他游标的键，没有核值。** 将 ASCII 退路改成保存 `{k: None for k in data}`，现有存在性断言仍通过，但其他游标内容已经丢失。 |
| [test_traces_backlog_t6c.py:625](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:625) | **读取预算门检查单次最大值，未检查累计量。** 将读取变成循环小块读取并拼接，原测试仍 PASS：当前读取 **101 B**，变异版本累计读取 **200038 B**。 |
| [test_traces_backlog_t6c.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:291) | **扫描失败门替换了产生错误标签的整层。** 它直接返回 `read:OSError`；把真实 scanner 的读取异常分支改成返回 `reason=None`，该门仍绿。应让实际 `open/read` 抛错后检验降级标签。 |
| [traces.py:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:242) | **新增换行口径缺少回归输入。** 两个测试文件没有 U+2028/U+2029 对照；改回 `splitlines()`，现有输入无法发现。`{"timestamp":"a\u2028b"}` 可使结果从原字符串翻为 `None`。 |
| [traces.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:151) | **深度 fallback 未覆盖。** 根锚门会提前返回，正常路径门只有两段。用锚 `/a`、路径 `/a/b/c/d/file.jsonl`，删除深度闸后会从文件名退化为暴露完整相对层级。 |
| [traces.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:203) | **“内存上界就是 max_bytes”仍不准确。** 1 MiB 换行输入、同值预算，真实函数内存实验峰值约 **9.07 MiB**；`decode`、切片和 `split` 都产生额外对象。当前保证是读取返回量 ≤ N+1、整体内存 O(N)。 |

其余重点核对结果：

- **锁与原子性：**现有进程内写者共享锁，覆盖核行数、轮转、追加全段；未发现重复取锁或 checkpoint 反序嵌套。跨进程仍可能竞态，作者已有明确披露。
- **路径：**`audit` 与真实写侧锚一致；`bug_log` 依赖 `cwd=backend` 的限制已注明。未发现由 `request_id` 控制读取路径的新增入口。
- **backlog：**非 JSONL 保持三个字段为 `null`；异常降级带 `partial/degraded/error`，顶层带 `incomplete`，不能仅凭 HTTP 200 判绿。完整首行、尾部半行、多字节截断和换行边界的内存对照符合预期。
- **编码与 env：**ASCII 重试能保留其他游标原值；重试及删除同时失败会返回 `False`。坏值、负数和超长数字未发现导入期异常逃逸；可解析的巨整数没有上界限制。env 的行数 `0` 回默认，直接调用 helper 的 `max_lines<=0` 才表示关闭；保留数 `0` 表示全删。
- **已披露限制：**源码已准确写出 agent 旁路越限可无限持续，以及 overflow 无回灌方；请求中的“暂时越限”仍过强。`max_rotations=0`、轮转三条 early-return、路径异常 fallback 和根锚浅路径已有有效门。

当前源码实际为 **36＋31＝67 个测试定义**，不是自述的 66；这不是本轮 pytest 通过数量。


