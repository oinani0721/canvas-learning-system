> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-BOUND round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-BOUND-r5.md)"`
> 审查绑定: `26bf4a2e..f3336568`（= 最终 HEAD，终轮）（前一轮：r4 审 09d6da33）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `stderr:2 OpenAI Codex v0.153.3` / `stderr:5 model: gpt-6-astra` / `stderr:9 reasoning effort: ultra`

---

复核绑定 **`f3336568107467a464cd4d684321b63cd6722cb9`**。结论：**BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 2**。两条旧 HIGH 的具体实例已收口，但“隔离规则已固化为可靠常驻门”的声明不成立。

**MEDIUM**

1. **归档探测失败仍会报成正常零积压。**  
   [failure_counters.py:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failure_counters.py:110)：仅让父目录的 `os.stat()` 抛 EIO，保持活动文件可读，实际函数返回的 `overflow_files/overflow_bytes` 从 **`1/123` 变成 `0/0`**，却仍是 `partial=False、degraded=[]、incomplete=False`。原因是 `parent.exists()` 吞错后直接返回空列表。现有 [测试 :270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:270) 替换整个 `overflow_siblings` 抛错，避开了真实吞错点。

2. **目标名防撞仍可能选中已有归档。**  
   [failure_counters.py:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failure_counters.py:142)：固定微秒戳、预置 `-00` 目标，正常探测选择 `-01`；仅对已有目标的 `os.stat()` 注入 EIO，实际 helper 就改选 **已存在的 `-00`**，随后 POSIX `rename` 会覆盖它。已复现目标选择翻转，未执行磁盘覆盖；因为还需要撞名等前提，不列 HIGH，也不与已披露的跨进程竞态混算。

3. **AST 隔离门可以误认隔离，也会漏掉调用。**  
   [test_dead_letter_bounded_t6c.py:919](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:919)：执行实际扫描门，对未隔离调用只加一行 `# SYNC_CHECKPOINT_FILE not isolated`，结果便从 **拒绝变通过**；把同名属性补到错误的 `fwc` 模块也通过。模块级别名、fixture 内调用、`Test*` 类方法同样漏判。当前具体测试已隔离，此项是常驻保护失效，不能据此声称当前仍在写现网。

4. **隔离门的验伪锚检查了另一个对象。**  
   [test_dead_letter_bounded_t6c.py:945](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:945)：自验复制了一份局部 `scan()`，且只识别四个目标中的一个；在内存中将真正的常驻门替换成 `lambda: None`，现有验伪锚仍然通过。

**LOW**

1. **数行失败没有独立的降级门。**  
   [test_traces_backlog_t6c.py:724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:724)：新探针同时打坏数行与时间戳扫描；删掉生产代码中数行失败的 `_degrade()`，该探针仍可被时间戳分支托绿。对照输入应当只让第一次二进制打开失败、第二次成功；此时上述变异会错误返回 `backlog=None、partial=False`。当前实现正确，缺的是独立保护。

2. **更正后的说明仍有相反旧注释。**  
   [traces.py:231](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:231) 仍声称“内存上界就是 max_bytes”；[failed_writes_constants.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:80) 仍声称不可观测时“退回有界行为”。实际分别是 **整体 O(N)**，以及 import 持续失败时**停止轮转、持续越限**。

其余重点核对结果：

- **旧 HIGH-1 已收口**：实际 invalidator 的内存探针中，不存在→`True`；stat EIO、权限错误、锁进入时抛 `RuntimeError`→`False`，均没有继续读写或删除。
- **旧 HIGH-2 的具体用例已收口**：`:542` 已隔离真实 `fss.SYNC_CHECKPOINT_FILE`；当前相关测试未发现另一条实际漏隔离路径。
- **锁覆盖成立**：两个 memory 写点覆盖完整“计数→轮转→追加”；agent 写者持同锁。未发现同锁重入或锁顺序反转；跨进程非原子已有明确声明。
- **路径修复基本准确**：audit 与真实写侧锚一致；bug_log、dead_letter_episodes 的 cwd 限制已记录。未发现新增用户可控文件路径。
- **降级并非普遍假绿**：外层异常会明确标记 `partial/error/incomplete`；坏 JSON、空文件、非 JSONL 的处理符合说明。超大文件时间戳扫描受限，但数行仍读取全文件，没有耗时上限。
- **env 无已证实导入崩溃**：无效、负数、5000 位十进制输入均回默认；可解析的大整数没有上界，例如扫描预算设为 `9223372036854775807` 会在 `read(N+1)` 产生 `OverflowError`，由外层标记降级。env 行数下限为 1；helper 显式 `max_lines<=0` 才关闭上限，`max_rotations==0` 全删分支正确。
- **指定分支已有有效覆盖**：零保留、三条 early-return，以及 `_display_path` 的 fallback、根锚和深度闸均有对应输入。旁路可无限越限、overflow 无回灌方并最终删除，也已明确披露。
- **作者的 JSON 反驳成立**：本机 Python **3.14.4**、`recursionlimit=1000` 下，数组嵌套 **2000 / 100000 层均解析成功**。

本轮完成三路并行静态复核和纯内存对照探针；**39＋35＝74 是源码测试计数，不是本轮 pytest 通过数**。未修改文件、未连接数据库、未运行会写现网数据的命令；结束时 HEAD 与六个审查文件均未变化。


