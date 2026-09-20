> 批次: BATCH-2026-09-18-第十五批 · 车道 P2 · 卡 CARD-STAGING-WRITERS-BOUNDED round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-STAGING-WRITERS-BOUNDED-r3.md)"`
> 审查绑定: `5bb5262938bbfb15f4eff1fb566e9faad8d79179`（正文首句已自证 `ac0993b4 → 5bb52629`）
> 会话头自证（抄 .stderr 三行，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

审查绑定 `ac0993b4 → 5bb52629`，结束时 HEAD 未变。结论：**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 0；round-3 尚不能判通过。**

[HIGH] [memory_service.py:2922](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/services/memory_service.py:2922) — 半行修复忽略失败返回，仍可能“追加成功、记录不可解析、pending 已删除”。  
复现思路：**未被拦下的输入**：尾巴为 `{"episo`，探测或补换行发生一次 EIO，随后追加恢复且不轮转，最终得到粘连行并在 `:2943` 删除 pending；**对照输入**是补换行成功，现有半行门只覆盖后者。

两个未接边界修复的写者也不能仅凭“不重试”排除：本卡新增的请求期刷盘留下半行后，agent 写入全新记录 B，B 就会粘连；下一次原批重试看到末尾已有 LF，也救不回 B。**“半行失败 → 另一写者追加 → 原写者重试”是门未覆盖的路径**，且即时刷盘扩大了正常请求期间的暴露窗口。

[HIGH] [failed_writes_constants.py:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/core/failed_writes_constants.py:153) — 超时放行仍会破坏健康慢回灌的活动快照，这是本卡引入的安全退化。  
复现思路：**未被拦下的输入**：旧快照 `[A,B]` 尚在重放，超时后轮转并写入 C，新活动文件为 `[C]`，finalize `:391` 的 `1 > 2` 为假，C 随后被覆盖或错标 `.synced`；**对照输入**是未超时或直接持锁且时间戳为 `None`，两者仍禁止轮转。

docstring 和验收单确实登记了该退化及 REPLAY-REWRITE 移交。“不自判通过、交裁定”处置得当，但**登记不等于修复，也不能解除 HIGH**。本结论针对新增超时分支的因果链，没有另审回灌算法旧账。

[MEDIUM] [memory_service.py:2926](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/services/memory_service.py:2926) — 捕获范围收窄为 `OSError`，编码失败会逃出即时刷盘，改变批次方法的返回行为。  
复现思路：**未被拦下的输入**：失败原因含 `"\ud800"`，`json.dumps(ensure_ascii=False)` 成功，但 UTF-8 写入抛 `UnicodeEncodeError`——它属于 `ValueError`、不属于 `OSError`，于是请求无法返回 `errors / failed / episode_ids`；**对照输入**是普通中文原因，现有坏条目门只测 `object()` 导致的序列化错误，未覆盖编码失败。

[MEDIUM] [memory_service.py:1437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/backend/app/services/memory_service.py:1437) — 即时刷盘新增请求期同步 IO 和同步等锁，事件循环阻塞仍未修复。  
复现思路：**未被拦下的输入**：另一线程持有 `failed_writes_lock`，或文件扫描、轮转、追加缓慢时触发批次失败，整个事件循环等待；**门未覆盖的路径**是调度响应性，现有门只检查落盘结果。

这一限制已在代码和验收单如实登记；“append 与 clear 之间无 await”不能证明不会阻塞事件循环。

[MEDIUM] [UAT-CARD-STAGING-WRITERS-BOUNDED-2026-09-18.md:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox/_bmad-output/验收单/UAT-CARD-STAGING-WRITERS-BOUNDED-2026-09-18.md:397) — 验收单虽已提交，但内容没有完成所述 round-3 更新，仍有过强声明。  
复现思路：**未被拦下的输入**：直接读取 `git show 5bb52629:<验收单>`，仍能看到以下内容，工作树与提交版一致：

- `:395–397`：round-2 仍是“下一节由 r2 结果填写”。
- `:218–229`：只有四段负控，未登记所述⑤⑥。
- `:325`：仍称空 `git status` 是真正兜底；未见所述数据文件 SHA256 快照登记。
- `:301`：仍称“把无限期改成有上限”；`:406` 仍称所有路径不会撑爆、强退不会整批丢失。
- 未找到所述“超时后仍返回 True”的替代方案登记。

代码也有残留：`failed_writes_constants.py:69–71` 仍无条件声称窗口内不轮转、不会丢数据；`:132` 仍写“退回有界行为”。新增限定说明没有消除这些冲突。

其余问题核对如下：

- **正常刷盘与异常重试**：正常及已捕获的 OSError 路径没有修改 `errors / failed / episode_ids`；完整行部分成功后重试可能重复，已登记。逐条序列化保留好条目的修复成立。
- **补换行口径**：空文件、已有 LF、缺 LF 三种正常情况不会额外制造空行；生产计数原本就将未换行末尾计一行。但截断在 UTF-8 多字节内部的尾巴，补 LF 后仍不可整体解码，现有 ASCII 半行门没有覆盖。
- **锁顺序**：限定读取面内未发现新增反序。`DeadLetterStore.store → rotate_if_over_limit` 不传回调，原语不取锁，也没有反向获取 `failed_writes_lock`；不能据此宣称所有外部调用链均已证明安全。
- **outbox 自述不符**：本 SHA 的 `event_bus.py` 完全未改，`:359` 仍裸追加，没有 `_outbox_io_lock` 或两项 outbox 上限常量。验收单明确将 e3 退回第十六批，因此不另判漏实现，但“两条新有界链”不成立。
- **三条 exists 门有效**：Python 3.14.4 内存负控确认旧代码分别返回 `[] / -00候选 / 0`，新版分别上抛、跳到 `-01`、上抛。**门未覆盖的路径**包括缺失文件的对照，以及全部 100 个候选探测失败后返回未经确认的 UUID 名字；后者是既有兜底，不另计新增缺陷。
- **env 与 ignore**：实际新增的 replay 上限经过 `bound_from_env`，非法整数及低于下限会退回默认值。outbox 两常量不存在。本卡新增 `# pyright: ignore` 和 `# type: ignore` 均为 **0**。
- **AST 修复成立**：递归进入嵌套 `Test*` 类及相应负控已加入，内存执行扫描器通过；它仍只检查名字，不能证明路径真正隔离。

本轮只读，无文件修改、服务启动或连库；进行了静态核对和纯内存实验，未重跑落盘 pytest 或 `pyright app`。指定旧裁定书实际只有 **111 行**，无法核对其 `:158/:186`；也未越界读取其他证据日志来替验收单补证。


