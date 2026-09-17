> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-BOUND round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测；stderr:2 亦作 `OpenAI Codex v0.153.3`）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-BOUND.md)"`
> 审查绑定: `26bf4a2e..47075cbe`（47075cbe = 当时 HEAD 的代码 commit，绑最终 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `stderr:2 OpenAI Codex v0.153.3` / `stderr:5 model: gpt-6-astra` / `stderr:9 reasoning effort: ultra`
> （三字段均由 stderr 会话头自证，行号如上；`workdir` 在 `stderr:4` = `…/card-t6-neo4j`。）

---

审查绑定：`26bf4a2e → 47075cbef21e5423a7a1a219b662799075351292`，分支 `card/t6-neo4j`。

**结论：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 3。** 进程内锁覆盖成立；主要问题在异常时阻断追加，以及积压观测误报。

## BLOCKER：0

## HIGH：0

## MEDIUM：3

### M1．有界检查和清理失败，会阻断原本能够成功的追加

- [failed_writes_constants.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:77)：活动文件**可写但不可读**时，`rotate_if_over_limit` 已吞下第一次读失败，这里再次 `count_lines()` 却直接抛出；对照旧版裸追加可以成功，新版不写入，批量路径还会在 `memory_service.py:2886` 清空 pending。
- [failure_counters.py:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failure_counters.py:139)：父目录允许写入、遍历，但不允许列目录时，数行和 rename 可以成功，随后 `overflow_siblings→iterdir` 抛错，导致后续追加不执行；这里只保护了 `unlink`，没有保护枚举步骤。

这违背了“清理失败不应阻断新死信落盘”的声明。上述权限对照来自控制流分析，未创建文件或执行 chmod。

### M2．部分读取失败被包装成正常的零值，缺少错误标记

[traces.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:172)、`:141`、`:253`：

- 归档目录枚举抛 `PermissionError`，活动文件仍可读：响应为 `overflow_files=0 / overflow_bytes=0`，**没有 `error`**。
- 数行成功、第二次打开文件扫描时间戳失败：`oldest/newest=null`，同样没有 `error`。
- 唯一 JSONL 链读取失败：该链正确返回 `error` 和 `backlog=null`，但顶层仍返回 `total_backlog=0`，没有“不完整”标记。

这些结果已通过抽取原函数的内存异常探针观察到。**检查 HTTP 200，甚至检查部分顺利路径没有 `error`，都不足以证明观测完整。**

### M3．超大 JSONL 会在异步路由中同步扫描，阻塞其他请求

[traces.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:245)，相关执行点 `:124–130、193–194`：

对照输入为历史超大活动文件，或一条极长、没有换行的记录：路由同步完成数行和时间戳解析两遍扫描，中间没有让出事件循环；长行还会被整体读入并解析，内存随最大单行长度增长。

因此不能保证超大输入仍及时返回 200，`:116` 的“O(1) 内存”也缺少单行长度限制这一前提。当前测试没有覆盖此路径。

## LOW：3

### L1．旁路虽已披露，但“暂时越限”和磁盘上限说明仍过强

[failed_writes_constants.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failed_writes_constants.py:54)、`:73`；作者 [UAT:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/_bmad-output/验收单/UAT-CARD-NEO4J-REPLAY-BOUND-2026-09-15.md:182)。

具体反例：

- 持续只有 `agent_service` 写入、始终没有后续 helper 调用，越限可以无限持续。
- helper 随后把整份超大活动文件轮转，因此“每个 overflow 都 ≤ limit”不成立。
- 单批超过总保留容量时，retention 会删除该批较早条目，“且一条不丢”不能无条件成立。

作者已明确记录旁路及 overflow 最终删除；问题是部分结论超出了这些限定。**这项不要求修改其他地盘。**

### L2．路径降级分支可能再次抛错，导致整路由 500

[traces.py:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/api/v1/endpoints/traces.py:110)、`:212`。

项目声明支持 Python ≥3.9；在旧版本中，符号链接循环可使 `Path.resolve()` 抛 `RuntimeError`。它不被 `_display_path` 捕获，而 `_safe_backlog_entry` 的异常分支再次调用同一函数，异常便逃出整条路由。

已核对本机 Python 3.9.6 标准库源码，并以内存异常探针验证捕获路径；当前项目虚拟环境为 3.14，未在真实文件上制造链接循环。

### L3．测试门能证明基本行为，尚不能证明所宣称的全部边界和条目身份

| 锚点 | 能逃过现有测试的对照或变异 |
|---|---|
| [failure_counters.py:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/core/failure_counters.py:140) | 去掉零保留特判，统一使用 `siblings[:-max_rotations]`：零保留变成不删除，现有测试保留数均为正，拦不住。**当前实现本身正确。** |
| 同文件 `:172–186` | `max_lines<=0`、数行失败、rename 失败均没有对应输入；**低于阈值返回已被测试覆盖，不能说全部 early-return 都漏测。** |
| [test_dead_letter_bounded_t6c.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_dead_letter_bounded_t6c.py:151)、`:262` | 丢一个 ID、重复另一个 ID，行数仍守恒；尚未证明条目身份守恒。 |
| 同测试 `:170–174` | 错误保留 `err1、err2`，删除更新的 `err3、err4`，仍满足“两份且没有 err0”。 |
| [test_traces_backlog_t6c.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/unit/test_traces_backlog_t6c.py:245) | `_display_path` 恒返回空字符串仍通过；仓外 `tmp_path` **已覆盖 ValueError fallback**，缺的是准确文件名、仓内相对路径及异常分支断言。 |

未发现无条件恒真的断言；发现的是**判据偏弱、输入覆盖不足**。并发和同微秒碰撞也没有确定性测试门。

## 其余问题的核对结论

- **原子性／死锁：**两个 memory 写入点和 agent 旁路共用 `failed_writes_lock`；helper 不自取锁。dead-letter 的锁覆盖完整数行、轮转、追加，未发现与 `_counter_lock` 嵌套或二次获取路径。
- **跨进程：**仍可能重复轮转或覆盖归档。`exists→rename` 不是跨进程唯一性保证；作者在 `failure_counters.py:253` 和 UAT 中已明确声明非原子，没有隐瞒。
- **目录改动：**audit 新路径与 `guardian.py:28–29` 写侧一致；bug_log 写侧是相对 cwd 的 `data/bug_log.jsonl`，仅在 **cwd=backend** 时匹配。未发现新增任意文件路径读取；修正目录会使既有未鉴权 trace 路由实际读到日志，不代表内容已经脱敏。
- **坏输入：**普通坏 JSON、空行、非 dict 会跳过；空文件正常；非 JSONL 的三个积压／时间字段为 null。权限和超大输入的例外见上。
- **env：**缺失、空白、无效整数、负数及行数零回默认；保留数零有效。100 位正整数正常接受，5000 位转换错误被捕获，未发现所问导入期崩溃。合法超大值没有上限钳制。helper 的 `max_lines<=0` 禁用语义与 env 的 `minimum=1` 属于不同入口。
- **后缀与披露：**`.overflow.` 清理范围与 `.synced.` 隔离成立；overflow 无回灌且超保留删除，作者记录明确充分。静态 backlog 路由顺序也正确。

**验证边界：**全程只读，未连接数据库、未修改文件，未运行 pytest 或真实权限／并发实验；使用静态调用链核对及内存函数探针。UAT 是未跟踪的作者说明，仅用于核对披露，代码结论绑定上述 SHA。


