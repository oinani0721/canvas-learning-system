> 批次: BATCH-2026-09-05-第十二批 · 车道 Y5 · 卡 CARD-TOOL-dredd-prereq round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOL-dredd-prereq.md)"`
> 审查绑定: `67ee147c`（本卡零代码改动，代码树与该 SHA 一致；被审对象是 `_bmad-output/` 下的判据页与测量存档）
> 会话头自证（抄 .stderr，stderr 本身不入库；第 1 行是 stdin 提示、第 3 行是分隔线，故取承载字段的 2/4/5/8 行）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review` / `model: gpt-6-astra` / `sandbox: read-only`

---

已核对指定行号，**未发现纯行号错位**；问题主要是措辞超出对应代码或测量的支持范围。两次 `rc=1` 的记录与收口机制相符，对照组的 `blocked` 增量为 0、用例 `PASSED` 也有记录支持。

下文简称：[判据页](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/_bmad-output/审查/2026-09-06-Dredd-schemathesis-接CI可行性判据与成本.md)、[探针](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/_bmad-output/审查/evidence-dredd-prereq/profile_harness.py)、[run-1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/_bmad-output/审查/evidence-dredd-prereq/profile-20260906T103504.txt)、[run-2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/_bmad-output/审查/evidence-dredd-prereq/profile-both-20260906T104054.txt)。

## BLOCKER

无。

## HIGH

[HIGH-1] 已定位的是 TestClient 进入／退出区间，不能直接等同于纯 app startup／shutdown 耗时。  
位置: 判据页:13-14、30、79-80；探针:179-193、330  
依据: 正文写“**全部**落在 app lifespan 的 **startup……与 shutdown……**两段”；实际探针调用是 `client.__enter__()` 和 `self._client.__exit__(*exc)`，探针自身另写“`TestClient.__enter__` 照常建 portal”。  
为什么这是问题: 这些计时边界会包含客户端、portal 和线程收尾工作，而 request 区间也包含应用处理，因此对账没有完成“app 与 schemathesis 自身”的组件耗时分离。  
建议: 改成“主要墙钟落在 TestClient.__enter__／__exit__ 包装区间，app lifespan 与 portal／线程清理尚未分别计时”；对照组的 startup 约 1ms 应解释为客户端进入及 no-op lifespan 往返，不能称为业务 startup 耗时。

[HIGH-2] 对照组只跳过了后续 lifespan，未证明被测 app 是“从未启动”的状态。  
位置: 判据页:60-61、188、192、264；探针:41、343、359；`backend/tests/support/lifespan.py:67-83`  
依据: 正文写“唯一变量”“被测对象从「启动过的 app」变成「没启动的 app」”“启动期才装配的对象不存在”；辅助器却明确写“`app.main.app` 是**进程级单例**”，实现只设置 `router.lifespan_context = _noop_lifespan` 并恢复。  
为什么这是问题: run-2 对照紧接五次完整 lifespan，复用同一个 app，探针没有重建 app 或清理其 state、单例和缓存，所以“启动对象不存在”及唯一变量声明均证据不足。  
建议: 改成“同进程主用例之后，复用既有 app 并跳过后续 lifespan，观测到中位 8ms、blocked 增量 0”；§六补充“未证明等同于全新未启动态”，若保留原结论，缺独立初始状态及关键对象状态证据。

## MEDIUM

[MEDIUM-1] 小残差不能独立证明同时不存在漏计和重复计。  
位置: 判据页:35；探针:144-156、255-262  
依据: “所以「四段之和 ≈ 整次墙钟」既排除漏计也排除重复计”；计时实现为 `time.perf_counter() - self._t0`。  
为什么这是问题: `_Timed` 不扣除嵌套计时，残差实际为“漏计量－重复计量”，例如漏计 10ms 与重复计 10ms 可以相互抵消。  
建议: 改成“当前固定成功路径的源码顺序及每段 n=5 支持串行计时，残差用于补充对账”；本次调用链未发现实际重叠，但不能把这一判断仅归功于加总吻合，也不能推广到 hook 重入或并发调用。

[MEDIUM-2] 采样标签可能错桶，且 app 帧占比不能直接升级为墙钟占比。  
位置: 判据页:93-98、186、261；探针:78-92、147-156  
依据: `seg = _CURRENT_SEGMENT` 先执行，随后才执行 `sys._current_frames()`；正文写“447”／“453”个 app 帧，并在 §四称“本卡实测 startup 的墙钟主项是……`_build_sync`”。  
为什么这是问题: 标签读取与取帧之间可能跨段，标签切换与计时起止也不同步，而所有线程共用一个标签、分母又仅包含有 app 帧的线程样本，因此不能据此量化关键路径的墙钟份额。  
建议: 保留“采得的 startup 桶 app 帧主要落在 `_build_sync`”，删除确定的墙钟份额暗示；§六补充标签竞争、线程混合及条件分母限制，误差秒数应写“证据不足”，因为 0.2s 是采样休眠间隔，并非错桶误差上限。

[MEDIUM-3] shutdown 的具体任务归属和模型装载次数没有被日志、采样闭合。  
位置: 判据页:103-111、262；探针:78-90  
依据: “⇒ 每轮 lifespan 至少装载 2 次模型”“指向……`asyncio.create_task(_eager_init_lancedb_singleton())`”“而该后台任务正在装 BGE-M3”；采样只累计 `(seg, _fmt_frame(f))`。  
为什么这是问题: 每轮两条装载日志与 TLS／transformers 帧是观测，但输出丢失线程身份和等待关系，不能证明装载完成次数、具体 task 身份或该任务阻塞退出。  
建议: 改成“每轮观察到两条模型装载日志，退出区间采到 TLS 和模型相关帧；具体任务关联及等待关系尚未确认”；“线索，不是结论”应覆盖整条任务归因，§六不能只保留“TLS 对端未知”。

[MEDIUM-4] 存档脚本不能原样生成 run-1 的报告格式，逐字节同源声明需要收窄。  
位置: 判据页:22；探针:261-262；run-1:532-536  
依据: “与跑出下表的工作树文件逐字节相同”；脚本使用 `未归类={total - s:10.6f}s`、`after_call hooks={after:.6f}s`，run-1 却显示 `未归类=  0.000s (其中 after_call hooks=0.000s, 余 0.000s)`。  
为什么这是问题: 六位小数的格式字符串不能原样输出这组只有三位小数的字段，因此当前存档不足以绑定两轮均使用同一字节版本。  
建议: 分别说明两轮实际脚本版本及差异，或将同源声明明确限定到 run-2；这项差异本身不证明核心计时逻辑改过。

[MEDIUM-5] 本轮测量不能反推旧 7.1s 的主要组成，也不能证明旧测量排除了 shutdown。  
位置: 判据页:82-89；探针:41、292-300  
依据: “⇒ 那个 7.1s 的主项是 **`import app.main` 的模块导入**”“shutdown 段从来没被量过”“只覆盖了 startup”；本探针在计时之前执行 `from app.main import app`。  
为什么这是问题: 本卡没有测 import，也没有提供旧计时起止边界，而且所谓 `from_asgi` 时间还包含随后的 `operation = schema[TARGET_PATH][TARGET_METHOD]`，不能跨轮反推历史组成。  
建议: 改成“本轮进入区间中位为 19.082／23.016s；旧 7.1s 的组成及是否包含退出，证据不足”；缺旧探针的准确边界和可比较的环境证据。

[MEDIUM-6] 门立即抛异常不能排除调用方重试，也不能证明屏蔽连接“几乎无收益”。  
位置: 判据页:149-150、186；`backend/tests/support/live_port_guard.py:513`  
依据: `raise RuntimeError(_block_message(address))`；正文据此写“30s 的墙钟不是「连库重试等出来的」”，并写“几乎无收益”“而且解决不了耗时”。  
为什么这是问题: 该行只证明门自身没有等待，未排除上层捕获异常后的重试、退避或回退成本，也没有测量替代方案的干预效果。  
建议: 改成“门本身立即抛出；调用方后续等待及单独屏蔽连接后的耗时变化未测”，§六补充该因果边界。

[MEDIUM-7] 全文仍存在跨 operation 和未实施方案的文字外推。  
位置: 判据页:187、237、254-255；`backend/tests/contract/test_openapi_contract.py:37-41、83`  
依据: “边际成本从 ~31.6s 降到……~9ms”“11 → 2~3”“每 operation ~9ms + 一次性 schema 收集”；生产用例则有 `max_examples=10`、`phases=[Phase.explicit, Phase.generate]` 和 `case.call_and_validate(...)`。  
为什么这是问题: 单个固定 health Case 的分段耗时不能确定其他 operation 或复用客户端后的成本，且单次 call 计时已排除 schema 构造，所以“乘以 operation 数会重复计算一次性成本”的解释也不成立。  
建议: 删除“每 operation ~9ms”，将复用后的耗时和连接数标为未测假设；保留不估总时间的结论，但说明缺 operation 差异、example 次数、校验及运行状态数据——未发现对 208.70s 的显式倍数计算，仍不能据此宣称全文没有外推。

[MEDIUM-8] 豁免代码只证明放行，不能证明连接建立、写入成功或整个用例所有线程均被豁免。  
位置: 判据页:177-180、205-208；`live_port_guard.py:253-256、513`；`conftest.py:124-125`；`main.py:172-173、386-397`  
依据: “**连接真的建立**”“豁免等于让合约测试对用户现网库做 DDL 与写入”“豁免一次关掉的是……三层”；源码还写“裸线程默认 `<unknown>` 且永不豁免”，相关调用存在 `if memory_svc is not None:` 和 `if _worker_graphiti is not None:` 条件。  
为什么这是问题: 不抛拦截异常只允许连接继续尝试，不能保证连接或条件写路径成功，而局部豁免机制也不能扩大为整个用例的所有连接均绕过。  
建议: 改成“对命中豁免的连接只记 advisory、不阻止尝试；连接及初始化条件满足时可进入 DDL／写调用”，并注明本卡未实测豁免后的成功连接或写入。

## LOW

[LOW-1] “30–37s”遗漏了 run-1 的最短样本。  
位置: 判据页:13、254、271；run-1:532、537  
依据: 正文写“30–37s”“30.1–37.0s”，原始输出为 `min=  23.117s max=  37.045s`。  
为什么这是问题: 正文覆盖两轮十个样本时，没有如实包含其中的 23.117s。  
建议: 全体范围改为 **23.117–37.045s**，或明确限定某一轮，并将“全部”“没有任何一部分”改为“绝大部分”，保留已测非零请求耗时。

[LOW-2] “合计中位 9ms”不能由各段单独中位数直接核实。  
位置: 判据页:14；run-2:525-527  
依据: 三段分别报告 `median=0.000s`、`median=0.000s`、`median=0.009s`，其中序列化 `max=0.011s`。  
为什么这是问题: 中位数一般不能相加，现有输出没有逐轮三段和的中位数，而且 `0.000s` 只是显示精度下的舍入值。  
建议: 改成“request 段中位 9ms；hooks 和序列化各自中位见表”，或提供逐轮配对求和后的统计。

[LOW-3] 对未归类残差及 after_call 的说明遗漏了未包装的执行路径。  
位置: 判据页:54-56；探针:208-217；`schemathesis/generation/case.py:413-414`  
依据: 正文写“`after_call` hooks 各 ≤ 0.000009s，余下……是……那几行”；源码在 `dispatch("after_call", ...)` 后还有 `self.operation.schema.hooks.dispatch("after_call", hook_context, self, response)`。  
为什么这是问题: 探针只包装前一个 dispatch，schema 侧 dispatch 以及其他包装器、参数处理等工作仍在残差里，不能将剩余耗时确定归到所列几行。  
建议: 将 ≤9µs 限定为被包装的 global dispatch，并写“其余探针外工作合计形成残差，未逐项计时”；这不影响秒级与毫秒级的量级判断。

BLOCKER/HIGH 清零：否
