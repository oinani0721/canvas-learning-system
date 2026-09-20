> 批次: BATCH-2026-09-18-第十五批 · 车道 P2 · 卡 CARD-STAGING-WRITERS-BOUNDED round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-STAGING-WRITERS-BOUNDED-r4.md)"`
> 审查绑定: `732d2a960f44d5f710a542e8ffdb6c30dc163f5b`（正文首句已自证 `ac0993b4 → 732d2a96`）
> 会话头自证（抄 .stderr 三行，括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---

绑定 `ac0993b4 → 732d2a96`：**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 1，不能判全部通过。**

代码与审 SHA 一致；验收单在审查期间出现未提交更新，下面区分提交内容与工作树内容。

[HIGH] `backend/app/core/failed_writes_constants.py:179` — 超时放行轮转仍会使健康慢回灌覆盖窗口内的新记录，属于本卡引入的退化。  
复现思路：**未被拦下的输入**：满额快照 `[A,B,C]` 重放期间超时，追加 `X` 触发轮转，新活动文件变成 `[X]`；若旧快照剩余失败项为 `C`，finalize 得到 `new_lines=[]`，写回 `[C]`，于是丢掉 `X`。

[HIGH] `backend/app/core/failed_writes_constants.py:185` — 超时轮转后，旧重放循环仍可重新保存旧代 checkpoint，重启后跳过新代记录。  
复现思路：**未被拦下的输入**：旧快照第 50 条重放期间轮转并写入 `X`，随后连续成功前缀达到 50、保存 checkpoint，再于 finalize 前退出；重启后单行 `[X]` 被 `i<50` 跳过。**对照输入**：新代有 51 条时仅跳过前 50 条，因此登记中的“整份全部跳过”必须注明新代行数不大于复活游标。

[MEDIUM] `backend/app/core/failed_writes_constants.py:332` — “探测失败＋实际半行＋追加成功”仍会粘连首条并清掉 pending，半行修复尚不完整。  
复现思路：**门未覆盖的路径**：把不可读探测门的完整尾行换成 `b'{"episo'`，继续拒绝读取、允许追加；纯内存执行实际函数得到 `{"episo{"episode_id": "A"}\n`，可解析记录为空，pending 也为空。**对照输入**：完整尾行仍成功。此问题 PREV 也存在，应称修复遗漏，不能称新增丢失回归。

[MEDIUM] `backend/tests/unit/test_staging_writers_bounded.py:337` — 时间戳门观察的是进入内部方法后的锁状态，仍未证明赋值发生在取锁之后。  
复现思路：**负控输入**：把时间戳赋值移到 `async with` 前，现门的 float、locked、时钟差、退出清空四项仍全部通过；**对照输入**：预先占锁再启动调用，正确实现等待期间不改时间戳，负控已经改写。当前生产顺序正确，缺陷在门的鉴别能力。

[MEDIUM] `_bmad-output/验收单/UAT-CARD-STAGING-WRITERS-BOUNDED-2026-09-18.md:469`（审 SHA）— 用户侧仍承诺“三样都拦住”“强退不会整批不见”，且提交内登记落后于代码。  
复现思路：**未被拦下的输入**：持续写盘失败、pending 留在内存后强退，即否定该承诺；已撤回的 outbox 也否定“不管哪条路都不会撑爆”。同句在工作树新版 `:497` 仍存在。

这里还存在明确的版本差异：

- finalize 风险：提交内 docstring、验收单均明确登记为 P2-C 前置。
- 游标复活：提交内 docstring 已登记，**提交内验收单未登记**；工作树新版才补入。
- 提交内验收单仍写 **19 门／八段负控／False 则拒写**；实际测试为 **23 门、952 行**，当前实现使用 `sep`。
- “下个 checkpoint 必然保存”还须满足连续成功前缀推进条件，不能无条件表述。

[LOW] `backend/app/core/failed_writes_constants.py:435` — 补换行失败后若成功轮转，遗留的 `sep` 会在新空文件多写一行，使首段达到 `max_lines+1`。  
复现思路：**未被拦下的输入**：上限 1、旧文件一条半行、首次补换行失败、随后轮转及追加成功；结果为 `\n{"episode_id":"A"}\n`，共两行。现门未触发这个组合；这是额外空行的边界回归，并非无界增长或直接丢记录。

其余逐项结论：

- **① 即时刷盘**：确实新增请求期同步 IO 和同步等锁，代码已如实登记。正常 `errors / failed / episode_ids` 计算不变，耗时指标包含刷盘时间。OSError 保留整批，部分完整行已写入后重试会重复；不可序列化／编码条目被丢弃。无 await 能避免单事件循环中的中途交错，不能证明无阻塞。
- **② 锁序**：限定读取面内未发现 `failed_writes_lock ↔ _dead_letter_io_lock` 反序。**当前 SHA 没有 `_outbox_io_lock`**，`event_bus.py` 相对 PREV 零改动，outbox 有界子项已撤回；作者“两条新链”的自述已过时。
- **③ exists 门**：Python 3.14.4 下纯内存注入确认，旧实现分别错误返回 `[] / -00 候选 / 0`，新实现分别上抛权限错误／改选 `-01`／上抛权限错误。**门未覆盖的路径**：100 个候选全部 stat 失败后，仍返回未经探测的随机兜底名；这是既有边界。
- **④ env**：本 SHA 唯一新增的是 `CLS_REPLAY_WINDOW_MAX_SECONDS`，经 `bound_from_env`；空串、非整数、零、负数均退回默认值。没有新增 `CLS_OUTBOX_*`。
- **⑤ ignore**：diff 新增 **0 条 `pyright:`、0 条 `type: ignore`**；没有证据表明靠新增 ignore 压平错误，但本轮未重跑 pyright。
- **r4 其余门**：真持锁下的 import 鉴别门有效；多行窗口分支也只消费一次 `sep`，纯内存组合验证通过。另外，换成 `time.time()` 会令 elapsed 成为巨大**负数、恒不超时**，测试注释写反了，时钟差断言本身有效。

本轮只做静态复核与纯内存执行，未修改文件、运行服务或连接数据库；未背书十段负控存档及 pytest 的 passed 数。指定裁定书当前只有 **111 行**，无法核对所指 `:158/:186`。


