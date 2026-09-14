> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-CENSUS round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-CENSUS.md)"`
> 审查绑定: `081004834e37b1b0253cf81dc7b44e784646c934`（= HEAD，本卡零代码；census 文档 mtime 19:57:49 早于 codex 启动 19:58:03，审查期间审查对象逐字未变）
> 会话头自证（抄 .stderr，括注各行在 .stderr 的行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:4） / `model: gpt-6-astra`（.stderr:7） / `reasoning effort: ultra`（.stderr:11）
> 另: `sandbox: read-only`（.stderr:10） · `session id: 01a09fc8-0f89-79a2-9979-6e5a64394cc8`（.stderr:13）
> 裁定: BLOCKER 0 / HIGH 6 / MEDIUM 4 / LOW 2 —— **12 条经本卡逐条独立实测全部成立，零误报**；
> 均为 census 文档事实错误（本卡零代码 ⇒ 无代码整改），已在 census v2 §九 来源 A 逐条落地。
> 复核结论存档: `evidence-neo4j-replay-census/judge27-28-*.txt` / `judge29-30-*.txt` / `judge31-*.txt` / `judge32-*.txt`

---

**复核不通过：BLOCKER 0 / HIGH 6 / MEDIUM 4 / LOW 2。** 两个指定重放器的孤儿结论成立，但七链表的写侧、读侧、有界性及处置前提存在实质遗漏。

HEAD 核对为 `081004834e37b1b0253cf81dc7b44e784646c934`，代码无差异。本次未修改文件、未连库、未启动 lifespan、未运行测试。以下仅指出文档事实问题；“census”指[本卡文档](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/_bmad-output/审查/2026-09-14-NEO4J-REPLAY-CENSUS.md)。

1. **HIGH — 链 5 已有写侧 10,000 条上限，“有界机制全部在孤儿体内”错误。**

   `canvas_service.py:97` 设置上限；`:165-166` 每次追加后保留最后 10,000 条，`:171` 覆写，完全不依赖回灌。census `:45、:78-81、:188、:209` 与此冲突。判据 16 标作“全文”的证据恰好截在 `events.append(event)`，漏掉紧接着的截留代码。条数有界不代表字节数也有界。

   复现：`nl -ba backend/app/services/canvas_service.py | sed -n '95,99p;152,172p'`。

2. **HIGH — 链 3 漏登记两种写入格式，“回灌器写好，只差入口”不成立。**

   除评分记录，还存在 `memory_service.py:1665-1673` 的结构化 outbox，以及 `:1422-1427` 暂存、`:2872-2874` 关闭时落盘的批量失败记录。`FallbackSyncService` 在 `:146` 将所有记录交给评分 helper，`:314-321` 对缺少 `concept/concept_id` 的这两类记录返回 False；旧重放器才在 `memory_service.py:2735` 区分 `knowledge_entity`。

   census `:43、:208` 的“UI 可见”也过强：评分写侧 `agent_service.py:117-127` 不存 `user_id`，而 `memory_service.py:805-806` 会在查询携带非空用户 ID 时过滤掉它。

   复现：`nl -ba backend/app/services/memory_service.py | sed -n '802,806p;1422,1427p;1665,1673p;2870,2875p'`，对照 `fallback_sync_service.py:138-150、314-321`。

3. **HIGH — 链 3／5／7 的历史 vault 归属风险未登记到处置前提。**

   `fallback_sync_service.py:324、:392、:441` 根据 Canvas 名重新构造 group；`:638-644` 使用当前上下文或 active vault，而非原记录的 vault。`:623-625` 已明确记载：切换 vault 后，旧待恢复记录可能归入新 active vault。census `:208-210` 未登记这一前置风险。

   复现：`nl -ba backend/app/services/fallback_sync_service.py | sed -n '314,324p;385,392p;433,441p;608,646p'`。

4. **HIGH — `/traces` 与死信写侧路径不同，“request_id 落盘 ⇒ 可查”不成立。**

   `failure_counters.py:25` 写的是 **`backend/data/failed_edge_syncs.jsonl`**；`traces.py:17、:22` 读的是 **`backend/app/data/failed_edge_syncs.jsonl`**。因此 census `:44` 漏了确定的路径错位。

   链 2 同样需要登记路径条件：`episode_worker.py:306` 是相对 CWD 的 `data/...`，而 traces 固定读 `backend/app/data/...`；从 `backend/` 启动时两者也不一致，不能只检查 `request_id`。

   复现：`nl -ba backend/app/core/failure_counters.py | sed -n '23,29p'`，对照 `traces.py:17-24` 和 `episode_worker.py:303-311`，逐级展开 `.parent`。

5. **HIGH — 链 2 的死信来源不限于 Markdown，不能统一断言字段足以回源重生成。**

   census `:211` 的充分性判断被会话归档通道反驳：`memory_service.py:495-499` 投递会话正文，来源是 `endpoints/memory.py:864-875` 的请求消息；死信 `episode_worker.py:107` 仅保留前 200 字。`vault_backfill.py:195、:210-212` 只扫描现存 Markdown 的 callouts／relationships，不恢复任意会话全文或全部学习事件。

   复现：`nl -ba backend/app/services/memory_service.py | sed -n '481,500p'`，对照 `backend/app/services/vault_backfill.py:195-216`。

6. **HIGH — 链 4 的死信本身不足以重放，缺少回源及源仍然有效的前提。**

   census `:212` 列出的 `edge_id/canvas_name/retry_count/request_id` 不含原操作所需的 `from_node_id/to_node_id/edge_label`。实际调用在 `canvas_service.py:481-487`，落盘参数在 `:508-515`。源 Canvas 已修改或删除时，不能据此恢复原失败操作。

   复现：`nl -ba backend/app/services/canvas_service.py | sed -n '480,487p;506,516p'`。

7. **MEDIUM — 判据 19 漏了一个已有启动恢复入口的 outbox 候选，不能据此确认七条全集。**

   `event_bus.py:48-49` 通过 `OUTBOX_DIR / "events.jsonl"` 定义 **`backend/data/outbox/events.jsonl`**，属于三种扫描形态之外的变量拼接。`:263、:303` 是失败入箱路径，`:383、:401` 读取并重发，`main.py:212-216` 已接生产启动恢复；没有磁盘容量或年龄上限。

   **限定：已证明生产注册和恢复入口存在，未证明单纯 Neo4j 断连一定沿活跃 handler 写入该箱**——部分下层会降级到其他链。因此应登记候选及纳入／排除依据，不能直接宣称“已证第八条离线写活链”。

   复现：`rg -n 'OUTBOX_DIR|OUTBOX_FILE|_write_outbox|recover_outbox' backend/app/services/event_bus.py backend/app/main.py`。

8. **MEDIUM — 文件中的两个配置场景成立，但“本机实际关／example 部署实际开”没有被实测证明。**

   census `:181、:187-188` 将“.env 行被注释”直接推成“进程变量未设”。`config.py:943` 使用相对 CWD 的 `.env`；`:1066-1072` 允许 overrides 写入进程环境。本地 `pydantic_settings/main.py:266` 的来源顺序也明确是构造参数、进程环境、dotenv。结论必须附“实际装载该文件且无更高优先级覆盖”的条件。

   复现：`nl -ba backend/app/config.py | sed -n '940,966p;1056,1075p'`。

9. **MEDIUM — 门位于 `:387` 核对通过，但不能据此把修改地盘从 `:386-404` 自动缩成 `:387-404`。**

   `main.py:386` 是后续 `:394-395` 使用的客户端取值；`:405-406` 是整个回填块的异常处理。census `:172、:282` 混淆了“条件语句定位更正”与“允许修改的语义范围”。目前证据不能断言这些外围行必须修改，也不能证明可以排除它们。

   复现：`nl -ba backend/app/main.py | sed -n '380,406p'`。

10. **MEDIUM — 链 1 漏登记运行时读取，“self._data 单调增长”也不准确。**

    `neo4j_client.py:447-449` 初始化加载 JSON，`:915` 的降级查询读取 `_data`；`:2197-2202` 还会删除 association 并覆写文件。census `:41` 把运行时读侧与自动回灌混为一列。无自动容量淘汰仍可成立，严格单调增长不成立。

    复现：`nl -ba backend/app/clients/neo4j_client.py | sed -n '444,449p;911,920p;2194,2204p'`。

11. **LOW — `_sync_failed_writes` 的定义行号仍有一处错误。**

    census `:43` 写 `:129`，实际定义在 `fallback_sync_service.py:113`；`:129` 是加载 checkpoint。

    复现：`rg -n 'async def _sync_failed_writes' backend/app/services/fallback_sync_service.py`。

12. **LOW — 链 7 不宜直接轮转的判断核对通过，但读取方式和丢失时机表述不准确。**

    `neo4j_edge_client.py:794-796` 初始化读固定文件，`:892、:955` 查询内存。轮转不会立即清空已初始化实例；重新初始化时文件缺席，`:800-808` 才创建空存储，旧记录退出运行时查询。另 `:966` 的 `format_for_context` 只格式化传入列表，并不读文件，census `:99-100` 应作此区分。

    复现：`nl -ba backend/app/clients/neo4j_edge_client.py | sed -n '788,808p;885,893p;951,955p;966,985p'`。

其余作者自述的明确核对结果：

- **核对通过：两个指定重放器及工厂在当前生产源码没有调用或方法引用。** 全标识符归类及只解析、不导入应用的 AST 检查，均支持 `memory_service.py:2687`、`fallback_sync_service.py:53、:656` 为孤儿；唯一构造 `:661` 位于未被调用的工厂内部。`gateway.py:19、:27` 是 re-export，未发现其可达调用路径。复现可用 `rg -n 'recover_failed_writes|sync_all_fallbacks|get_fallback_sync_service|FallbackSyncService' backend/app` 逐命中归类。

- **核对通过，但正则不具通用完备性。** `(await |\.)<name>\(` 会漏裸调用、保存方法后经别名调用、括号包装及部分动态拼接；四种补充枚举也不是完整 Python 调用分析。当前没有找到这些目标函数的漏网调用。census 自己的 `memory_service.py:802` 回调用法就是“名字后不带左括号”的有效对照。

- **核对通过：正常 Settings 构造不存在所担心的缺字段第三态。** `config.py:477-479` 定义默认 False，`:961` 始终构造 `Settings()`；`reload_settings` 仍走该路径，`extra="ignore"` 不删除已声明字段。小写属性 `:928-930` 同值；未找到当前测试注入造成缺字段回落的实际反例。热重载另有引用限制：`canvas_service.py:37` 持有旧实例，重绑 `config.settings` 不自动更新它。

- **核对通过：启动三个定位点为 `main.py:387、:392、:404`。**

- **核对通过：链 7 确实具有生产运行时存储职责。** `dependencies.py:222、:231` 注入客户端，`agent_service.py:4998` 写入、`:2087` 查询；不轮转的依据得到实际调用链支持。

- **核对通过：离线早退会跳过该回灌器的全部清理。** `fallback_sync_service.py:64-74` 在三个 `_sync_*` 调用之前返回；它证明不能依赖成功回灌保证长期离线期间的清理，但不证明所有写侧均无界，链 5 已是反例。

- **核对通过：链 6 当前无生产写入接线。** `DUAL_WRITE_DEAD_LETTER_PATH`／`failed_dual_writes` 在生产源码仅命中 `failure_counters.py:27-29` 的定义。该结论限于当前源码，不能据此证明历史上从未产生过文件。


