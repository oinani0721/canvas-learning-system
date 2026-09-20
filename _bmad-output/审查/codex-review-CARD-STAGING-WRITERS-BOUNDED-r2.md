> 批次: BATCH-2026-09-18-第十五批 · 车道 P2 · 卡 CARD-STAGING-WRITERS-BOUNDED round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-STAGING-WRITERS-BOUNDED-r2.md)"`
> 审查绑定: `3fb1557e10ffe310dfefa07219eb976dd0dc8961`（正文首句已自证同 SHA）
> 会话头自证（抄 .stderr 三行，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

绑定 **`3fb1557e10ffe310dfefa07219eb976dd0dc8961`**。结论：**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 0**，r1 尚未全部关闭。

代码及新测试与该 SHA 一致；**本卡验收单存在未提交改稿**，下文区分工作区登记与提交内证据。验证采用静态核对和内存执行，未改文件、启动服务或连接数据库。

[HIGH] [failed_writes_constants.py:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/core/failed_writes_constants.py:145) — 超时放行仍会破坏正在进行的回灌；已经承认是本卡引入，但登记不等于修复。
  复现思路：**未被拦下的输入**：回灌快照为 `[A,B]`，超时后轮转并写入 C，活动文件变成 `[C]`；抽取当前 finalize 内存执行，B 待重试时结果变成 `[B]`，全部成功时 C 被标为 `.synced`；**对照输入**是不轮转的 `[A,B,C]`，结果正确保留 `[B,C]`。

`:110–121` 的风险登记准确，checkpoint 失效确实挡不住本次 finalize。不过“只能动禁改面才能处理”过强：可以仅在本卡守卫中**超时告警后仍返回 True**，把放行轮转延期至 REPLAY-REWRITE。代价是继续接受越限；调高阈值只推迟风险，不能保证安全。

[HIGH] [memory_service.py:2927](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/services/memory_service.py:2927) — OSError 重试不只有重复风险：残缺尾行可能吞掉重试记录，随后成功路径仍删除 pending。
  复现思路：**未被拦下的输入**：pending 只有 A，首次写出 `{"episo` 后抛 OSError；未达轮转阈值时重试完整 A，实际追加 helper 会形成 `{"episo{"episode_id":"A"}\n`，成功后 pending 为空，却没有合法 A；**门未覆盖的路径**是半行写入失败，现有门只让 `mkdir` 在写入前失败。

这是当前刷盘函数与追加 helper 的内存执行结果，IO 故障在边界注入。即时刷盘把这种故障提前到请求期；即使故障在 cleanup 前消失，后续成功重试也不保证恢复。`:2874–2878` 只登记重复，遗漏了这一结果。

[MEDIUM] [failed_writes_constants.py:290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/core/failed_writes_constants.py:290) — “至多失效 N 秒”的整改没有清干净，且验收单修订未绑定审 SHA。
  复现思路：**未被拦下的输入**：直接持锁且时间戳为 `None`，或轮转持续失败，越限可无限持续，直接反驳这里的“只是不再无限期”“窗口至多持续到上限”。

同一文件 `:77–79` 仍说返回 False 意味回灌窗口尚未打开或已经关闭，也不适用于超时分支。验收单 **`@3fb1557e:308`** 仍写“至多失效”，工作区改稿 `:301` 仍写“只把无限期改成有上限”。工作区已登记“本卡引入的安全退化”，但不能据此认定提交内登记已同步完成。

[MEDIUM] [memory_service.py:1437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/services/memory_service.py:1437) — 请求期同步 IO、同步等锁仍会阻塞事件循环；该风险已如实登记，尚未解决。
  复现思路：**未被拦下的输入**：另一线程长时间持有 `failed_writes_lock`，或计数、轮转、追加很慢；**门未覆盖的路径**是其他协程的调度延迟，当前刷盘门没有验证它。

[MEDIUM] [test_staging_writers_bounded.py:566](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/tests/unit/test_staging_writers_bounded.py:566) — AST 门仍漏扫描路径，而空 `git status` 不能补足隔离证明。
  复现思路：**门未覆盖的路径**：把违规方法放进 `TestOuter.TestInner`，或经 fixture/helper 间接写入，扫描器返回 `[]`；**对照输入**是直接 `TestOuter.test_*` 方法，能够报缺隔离。

此外，`:583–585` 已承认“声明 tmp_path、却调用默认 `DeadLetterStore()`”会放行，却把空 status 称为真正兜底。实际 `git check-ignore` 确认相关 JSONL 和 overflow 文件受 `*.jsonl` 忽略；普通 status 看不到这些未跟踪文件的写入。这证明验收手段不足，**不代表已发现当前测试污染数据**。

其余逐项核对：

- **outbox 撤回成立。** PREV、审 SHA、工作文件的 `event_bus.py` blob 相同；指定锁、上限常量和轮转 helper 均零命中。新测试没有 outbox 行为门或 fixture；仍留有 `:393` 的过时标题、`:543/:608/:637/:645` 的静态 AST 规则与字符串验伪锚，它们不调用 EventBus。
- **原无条件 clear 问题已修。** **负控输入**把 OSError 分支改回清空，保留 pending 门会红；序列化失败门与成功即时落盘门是仍应绿的**对照输入**。完整记录写入后失败再重试确会重复，已登记；只有新条目追加时，`del[:len(batch)]` 正确保留新增尾部。`cleanup()` 只调用一次，没有无限重试循环。
- **返回语义未改。** 正常及已捕获异常路径不改 `errors / failed / episode_ids`；返回前延迟增加，耗时指标包含刷盘。不可序列化批次仍整批丢弃，混合好坏条目也会一起删除，单条序列化门没有覆盖混合批次。
- **限定调用链未见新增反序锁。** 死信链持 `_dead_letter_io_lock` 后不反向取 `failed_writes_lock`；轮转原语自身不取这两把锁。outbox 新锁已撤销。
- **三条 exists 负控有效。** Python 3.14.4 内存核验结果为：旧 siblings 返回 `[]`、新实现抛 `PermissionError`；旧 count 返回 `0`、新实现抛异常；旧目标选择交出 `-00`、新实现交出 `-01`。精确后缀修复成立。**门未覆盖的路径**包括全部 100 次 stat 均失败后返回未经探测的 UUID 候选；该 fallback 原已存在，不列本卡新增缺陷。
- **env 与 ignore 核对通过。** 本轮实际只新增 replay 上限，走 `bound_from_env`；outbox 两个常量已撤销。坏文本、空值、零、负数、小数及超长整数均验证回退默认值。本卡新增 `# pyright: ignore` 和 `# type: ignore` 都是 **0 条**；本轮未重跑 `pyright app`，因此不独立背书“0 errors”。


