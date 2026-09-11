> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-6 round-6（U6-C 续修：端到端 snooze 门的时间炸弹）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-6-r6.md)"`
> 审查绑定: `8e517721da08622c8dad8e39db6da9eb0d5f9963..9fb119b97ebc4b3bd942f55ff7f5017962c13932`（送审时 `9fb119b9` 即 HEAD；本轮判出 1 LOW 并整改 ⇒ 已不再绑现 HEAD，收口轮见 r7）
> 会话头自证（抄 .stderr 会话头含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `provider: openai` / `sandbox: read-only` / `reasoning effort: ultra`

---

**修法方向正确，旧门没有放松。本轮结论：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1。**

审查绑定 `8e517721 → 9fb119b9`，确认只有测试文件 +105 / -1。全程只读、未连接数据库或网络；做了源码、Git、日志及纯内存函数核验，未重新运行 pytest。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW-1：新增注释错误地把“写入时已过期”宣称为生产不可达。**

位置：[test_review_overview.py:3970](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:3970)。

具体场景：端点在当地 `19:59:59.999` 读取时间，计算 `until=20:00:00`，通过 `until > now_local` 检查；随后经过目标校验、取锁或文件写入，到 `20:00:00.001` 才发布 state。写入前没有再次检查时间，生产器随后得到不活跃的 snooze，板不会让位。

实际链路是：

`review_overview_board_snooze:3168–3192 → _write_board_snooze:2706–2713 → refresh → daily_review_pick.main:1307 → active_snoozed:966`

从源码提取原函数的纯内存核验也得到：上述父时间通过检查，而上述子时间返回 `{}`。此外，snooze 与 refresh 本来就是两个独立请求，间隔没有“毫秒级”上界。`debounced` / `in_progress` 会直接返回，并不排队保证截止前重建；后续重试完全可能在截止后发生。`tomorrow` 在午夜前有同样场景。

这是本轮新增说明的事实错误。**到期后不活跃本身符合现有约定**，不能据此否定双侧钉钟修法，也不需要重审 U6-B 的锁实现。建议删去“生产不可达”“相差一次 spawn 的毫秒级”这两个保证。

其余问题核对如下：

1. **生产是否应接 `--now`：本轮无需接，但作者两条理由需要收窄。**

   `generated_at` 确实会换成父进程采样值；不过当前它也是子进程在扫描前采样的时间，并非生成完成时刻。

   runner 的理由更不完整：[daily_review_run.py:613](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:613) **直接调用** `picker.build_payload(..., now, ...)`，已经传递 runner 的参照时间，根本没有另起 picker 子进程。因此“不传 CLI 旗标”不能证明 runner 让生成器自行读钟。

   午夜分叉确实存在：父侧完成账日历键、子侧 `payload["date"]` 与完成分区可能采用不同日期。已检查 G6-6 引入前的版本，双读钟形态已经存在，归 G6-7/G6-7-R 面合理。[移交登记:505](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/验收单/UAT-CARD-G6-6-2026-09-09.md:505) 也存在，但位于当前未提交的 UAT 更新中。里面的“0.1–2s”“下一次 refresh 自愈”并非代码保证。

   仅在 `_run_pick` 新读一次父时间并传旗标，也不能统一之前的写账请求、之后的 GET 和 runner 的所有采样时刻。

2. **补丁作用域与匹配：当前调用窗口可靠，通用 fail-closed 保证不成立。**

   两个 helper 都修改进程级 `subprocess.run`。当前 fixture 已先加载 runner；两门随后只有两次串行 refresh 走 `_run_pick`，没有找到会同时被误追加参数的其他调用方。

   实际 stdlib 中，`check_output → run`，**会经过包装**；直接 `Popen`、`call/check_call`、`fork` 或提前绑定的 `run` 别名可以绕过。当前被测路径没有这些旁路。

   `endswith(basename)` 确实可能误匹配，例如其他命令参数为 `not_daily_review_pick.py`；`-m scripts.daily_review_pick` 或脚本别名则会漏匹配。但现行 `argv[1]` 是生产脚本完整路径，fixture 也清除了脚本环境覆盖，当前没有此问题。

   漏匹配后仍走 `run`，前提断言会红；全部改用 `Popen`，`seen` 为空也会红。**但如果未来只有第二次 refresh 绕过包装，`seen[-1]` 可能仍是第一次的合法记录，前提断言会绿。** 因而它证明的是“最后记录的调用已钉钟”，没有严格绑定第二次 refresh。属于当前保证的边界，不列为现有功能缺陷。

3. **三个参数有承重价值，但不是三个不同生产分支。**

   三者都走 `until > now`，且相差恰好十小时。这是检验时间平移后性质不变，重复同一分支是合理设计。

   `now.year == 2026` 变异的结果确为 `False / True / False`；加上原来的 2026 门，正好是 **2 failed / 2 passed**。

   输入差异不止年份：完整 `until`、投影日期、逾期天数也不同，后者分别为 **366 / 2808 / 29583 天**。不过三组节点始终到期，夹具没有 `last_examined`，没有引入八十年的衰减分支。2099 的时区转换正常，不接近年份 1/9999 的溢出边界。

4. **前提断言没有弄松旧门。**

   独立比较 AST，原门 **12 条 assert 全部逐项相同**，包括 stats、boards、buckets、GET status、`due_count == 3` 和 snoozed 集合。

   漏钉时确实到不了让位断言，但先报告测试前提失败是准确诊断，测试仍然失败。钉钟正确而 `active_snoozed` 回归时，仍会红在让位断言。两个问题同时发生时，首个失败不能证明不存在第二个问题。

5. **扫描结果成立，覆盖范围有限；找到三个既有盲区。**

   独立重算得到指定模式违规 **0 条**、松掉第三项后命中 **2 条**。但它漏掉：

   | 既有用例位置 | 具体失败场景 |
   |---|---|
   | `test_review_overview.py:1365`，`test_refresh_rebuilds_projection_and_response_matches_disk` | 真实时间到达 `2099-01-01T00:00Z` 后，两条“未来”节点到期，`:1374` 预期 `due_nodes == 0`，实际为 2。 |
   | `test_review_overview.py:3533`，`test_g67r_refresh_passes_state_and_done_board_yields_top` | 父侧写完成日期后跨上海午夜，子进程按次日匹配，`:3542` 的让位断言失败。 |
   | `test_review_overview.py:1093`，`test_buckets_gate_accepts_real_producer_payload` | 夹具取日后、GET 前跨午夜，投影成为 `stale`，`:1128` 仍期待 `ok`。 |

   这些不是本轮新增缺陷。G6-6 的其他 picker、runner 用例显式传递参照时间，未找到另一颗本轮引入的同类炸弹。

6. **第三读钟对当前目标断言无害。**

   `_read_entry:2001` 仍读真实时间，会让 refresh 回执的 `entry.status` 随日期成为 `stale/ok`；但 `_rebuild_projection:2151` 只拒绝 `corrupt`，两门只要求 refresh HTTP 200。

   原门最后 GET 经 `_collect` 使用已钉的 `_display_now()`，再把同一读数传入 `_display_today(now)`。两门 TTL 都设为零，`monotonic()` 剩余影响是耗时和记录，不左右让位。因此成立的是**当前判定独立于真实日期**，不是整个响应逐字段都不受时间影响。

7. **数字与证据：部分确认，部分只能保留为未独立证实。**

   - **365 = 362 + 3：确认。** 旧、新日志对应 362、365，代码只新增一个三参数测试。
   - **脚本名取生产常量：确认。** `:3983` 使用 `mod._PICK_REL[-1]`。
   - **变异结果和最终还原：日志与当前文件 SHA 一致。** 但日志未保存完整 harness、逐例 traceback 或每轮还原 hash；“目标断言出现 True”只直接证明至少出现一次，不能独立证明全部操作历史。
   - **ruff rc=0：有修正后日志。**
   - **pyright 最终多重集 8=8：缺最终原始输出。** [现存日志:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g66/lint-typecheck-u6c-20260911T083601.txt:17) 仍是整改前的 9 条未用变量和 1 条类型错误。当前 `_runner` 修正已在代码里，AST 对比也支持原有八个未读变量站点不变；这支持零新增判断，但不等于复证了最终 pyright 多重集。
   - **mtime 日期：确认主仓库两个文件分别为 9 月 10 日 10:05:07、09:13:00（+08:00）。** 此 worktree 的对应相对路径不存在。mtime 支持当前最后修改时间早于所述作业开始，不能独立证明整个作业历史“零触碰”。


