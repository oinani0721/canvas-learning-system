# RAG 三 P0 修复方案 — 对抗性审查请求（给 ChatGPT）

> 附件：`rag-p0_pack_2026-08-02.md`（60 文件完整源码，已脱敏，Repomix markdown 格式）
> 使用方法：本文件 + 附件一起上传/粘贴给 ChatGPT

<review_request>

<role>
你是「本地优先 RAG 系统 + LangGraph 管道 + 知识图谱记忆」领域的专家审查员。请深度检索中英文一手来源（官方文档/issue/成熟项目源码），结论必须带 URL 和证据分级（tier）。你的任务不是安抚，是对抗性审查——我们的修复方案哪里会再次失败，请直说。
</role>

<goal>
审查三个 P0 断裂的修复方案是否治本。**这些问题已经反复修了很多次都没修好**（详见 already_tried 节的复发史），所以这次要你回答的核心不是「怎么修」，而是「为什么我们修不好、这次的方案会不会又是一次表面修复、什么样的结构性改动才能让它不再复发」。
</goal>

<environment>
- 单用户本地系统：macOS (Apple Silicon)，Obsidian vault + Claude Code skills 驱动学习流
- 后端：FastAPI（docker，bind-mount 挂 worktree 代码）+ Neo4j 5.26（Graphiti 知识图谱）+ LanceDB（docker volume /lancedb）
- 检索栈：bge-m3 embedding（宿主 Ollama :11434）、bge-reranker-v2-m3（宿主 llama-server :18012，实测存活）、Qwen3.5 本地 LLM（:12341）
- Claude Code skills 是消费端：UserPromptSubmit hook 每轮自动注入检索片段；MCP search_notes 工具；skills 内 native Grep 优先路径
- 约束：单机单人、无云依赖偏好（Gemini API 仅 Graphiti 抽取在用）、笔记量当前 ~3.6k chunks、目标 5 万 chunks 量级
- 安全基线（2026-07-31 已收口）：端口全绑 127.0.0.1、MCP 只剩 5 只读工具
</environment>

<problem>
三个 P0 断裂（2026-08-02 由 7-agent 对抗性审查发现，41 条结论经怀疑者全量验证 0 推翻，完整报告在附件包内 `_bmad-output/审查/2026-08-02-RAG检索设计对抗性审查-三问三答.md`）：

**P0-A 向量索引冻结 22 天（增量链三处断裂叠加）**
- 铁证：LanceDB file_fingerprints 表 max(last_indexed)=2026-07-11T22:04:47，审查日为 08-02；用户 07-23 写入 节点/lecture 2.md 的批注原话在索引 content 中 0 命中
- 断裂 1：增量入口 POST /api/v1/index/refresh-changed 的唯一调用方是已淘汰的 Obsidian 旧插件，全仓 grep 无活调用方
- 断裂 2：即使被调用，`lancedb_index_service.py` 的 `_debounced_note_index` 只刷 wikilink 图，LanceDB re-index 是注释里的「(后续 Story)」从未实现
- 断裂 3：backend 启动 lifespan 不扫 vault（只恢复 canvas 失败队列）
- 放大器：skills 只在索引「空」(empty_index) 时才提示用户重建——stale 但非空时静默返回旧数据，用户无从察觉
- 次级问题：单文件端点 index_single_file 在容器内只走 CPU vectorizer（不像全量路径先试 Ollama），常 init 失败静默 return 0；且它只查目录黑名单不查文件名黑名单

**P0-B 6 源检索管道 0/5 通道存活（自 2026-05-11，近 3 个月）**
- 铁证：live 日志 2026-08-01 仍是 0/5 通道 + "coroutine 'node_search' was never awaited"；每次 search_notes 陪跑 ~31 秒后由裸 LanceDB 单源兜底；返回的 quality 恒 low 是「空管道结果无条件 low」的假信号，与检索质量无关
- 死因 1（4 个通道）：`agentic_rag/config.py` 读 env `LANCEDB_PATH`（未设置）→ fallback 相对路径 → 容器内空目录；docker-compose 设的是 `LANCEDB_DATA_PATH=/lancedb`——一个环境变量名不匹配杀死 4 通道，静默 3 个月
- 死因 2（Graphiti 通道）：nodes.py 写死 timeout_ms=200，Neo4j 实测单查询 1539ms → 必超时
- 死因 3（LLM 环节全挂）：L1 路由/multi-query/CRAG 评分挂在已退役 gemini-2.0-flash（live 404）和未安装的 ollama/qwen3:8b 上
- 死因 4：LangGraph rewrite 重试回环踩 async 条件边 bug（"wrote to unknown channel branch:to:<coroutine fan_out_retrieval>"），代码注释自标 P1 deferred
- 隐藏 bug：RAGService 把 config 直接传 ainvoke 而非包 configurable → runtime.context 恒 None，所有调参永远走默认值
- 连带：三套 reranker（管道内 CrossEncoder / supplementary_reranker / 18012 bge-reranker 适配器）一个都没接到实际生产主链（hook 注入链零 rerank）

**P0-C Graphiti 的 Claude session 写入腿停摆 ≥8 天且无人报警**
- 铁证：8765 端口无监听进程；known-gotchas G-MCP-001 宣称的 com.canvas.graphiti-mcp.plist 不在 ~/Library/LaunchAgents（launchctl list 无此任务）；Episodic 最新写入停在 2026-07-25，最近 7 天写入为零
- daemon 脚本本体还在（~/bin/graphiti-canvas-daemon.sh，包内 home-bin/ 下）——是 launchd 注册消失了，何时/为何消失无记录
- 监控盲区：memory-health.sh 五探针（Neo4j/后端/Qwen/Rerank/Embed）不监控 8765——停摆 8 天零报警
- backend 写入腿（tips callout-direct → episode_worker）实测存活，但覆盖面只有批注直连+SessionEnd 归档，session 内实时记忆（MCP search_memories 对应的写侧）断了
</problem>

<already_tried_and_concluded>
**这三类问题的复发史（为什么这次要对抗性审查而不是直接修）：**

1. **检索链已反复修过 ≥4 轮**：2026-05 Story 2.2+2.9 五连修（rerank/evidence/timeout/降级）→ 2026-05-11 fallback 注释已记录「0/5 通道」但只加了兜底没修根因 → 2026-07 MEM-FLYWHEEL「检索束改造」（recall +9pt，修的是 hook 链）→ 2026-07-20 轨道 B 修 MCP 422。**模式：每轮修的都是「让当前症状消失」（加 fallback/加兜底/换路径），死管道本体从未被修活，quality 假信号让每轮修复都「看起来好了」**
2. **索引链**：2026-07-10/11 全量重建跑通过（指纹表为证），增量链的「(后续 Story)」注释从 5 月挂到现在；旧插件淘汰时没人盘点它调用的端点清单（本次审查才发现 refresh-changed 成孤儿）
3. **graphiti-canvas MCP**：2026-04-06 G-MCP-001 修过一轮（stdio→HTTP daemon + launchd），当时验证通过；后来 plist 静默消失（疑似某次 launchd 清理或迁移遗漏），无监控所以无人知晓。**同类事故已发生 3 次**（memory-health 6 天停摆、备份 8 天断档、这次 MCP 8 天）——都是「launchd 任务静默死亡 + 无告警」
4. **已确认排除**：不是 LanceDB 数据损坏（裸 fallback 检索正常）；不是 Neo4j 挂了（health ok，backend 腿在写）；不是模型服务挂了（Ollama/18012/12341 实测全活）
5. **我方拟定的修复方案（待你审查）**：
   - P0-A：`_debounced_note_index` 补 index_single_file 接线 + lifespan 启动时跑一次指纹增量扫 + 给 SessionStart hook 或 launchd 加周期性增量触发
   - P0-B：env 名对齐（一行）+ Graphiti timeout 200ms→2.5s + 4 处模型 id 换现役 + LangGraph 条件边 path_map 修复 + RAGService config 包 configurable + hook 注入链接 18012 reranker
   - P0-C：二选一待裁决——(a) 重新 bootstrap launchd plist + memory-health 加 8765 探针；(b) 正式退役 session 写入腿，统一走 backend 腿（tips/archive），文档写明
</already_tried_and_concluded>

<key_files>
附件 `rag-p0_pack_2026-08-02.md`：60 个文件完整源码（Repomix markdown，已脱敏，[REDACTED:*] 为脱敏占位，其中 coalesce_key 等少量变量名属误伤可忽略）。结构：
- `backend/lib/agentic_rag/` 全库（6 源管道：nodes/state_graph/config/retrievers/clients/reranking/llm_router 等）
- `backend/app/`：索引链（metadata/index/lancedb_index_service/config/main）+ 检索消费链（rag_service/note_search_tools/supplementary_search_service/supplementary_reranker/rerank_service/chat 的 enrich-hook）+ Graphiti 链（episode_worker/memory_service/llm_factory/tips/rerank_client）
- `canvas-vault/.claude/`：现行 skills 实态（study-question/chat-with-context 的 native Grep 优先 + MCP fallback）、hooks settings.json、mcp.json
- `home-bin/graphiti-canvas-daemon.sh`、`scripts/memory-health.sh`、`docker-compose.yml`、`docs/known-gotchas.md`
- `_bmad-output/审查/2026-08-02-RAG检索设计对抗性审查-三问三答.md`（7-agent 审查完整结论）
另：graphiti-canvas MCP 在 ~/.claude.json 的定义仅 3 行：`"graphiti-canvas": { "type": "http", "url": "http://127.0.0.1:8765/mcp/" }`
</key_files>

<research_questions>
1. **复发根因**：对照复发史，我们的组织性/架构性问题是什么？（假信号掩盖真故障、fallback 文化、无契约测试锁接线、launchd 无监控…）请给出结构性诊断，而不只是逐条修 bug
2. **P0-A 方案审查**：拟定的三处接线（debounce 补调用/lifespan 增量扫/周期触发器）会不会引入新问题（启动变慢、容器内 CPU vectorizer 失败路径、并发索引冲突）？成熟的本地笔记 RAG（Obsidian Smart Connections/Copilot、Khoj、Reor 等）的索引新鲜度机制是怎么做的——文件监听 vs 保存钩子 vs 周期扫，单机场景哪种最稳？
3. **P0-B 方案审查**：逐项检查我们的 6 处修复是否完备；更根本地——**这个 6 源 LangGraph 管道值不值得修活**？证据：真正干活的 hook 链（hybrid+RRF）设计已 adequate，管道死了 3 个月用户主观体验没有塌方。请给出「修活管道」vs「正式退役管道、把资源投给 hook 链+rerank+metadata」的对抗性论证，各自的量化收益预期
4. **quality 假信号**：如何设计一个诚实的检索质量遥测（对 fallback 结果也评分、区分「管道死」与「检索差」）？有没有轻量的本地 RAG 评测实践（如定期跑固定 query 集的 recall 探针）适合单人系统？
5. **P0-C 裁决**：session 写入腿（MCP 8765）重建 vs 退役——考虑：它停摆 8 天用户无感知；backend 腿覆盖批注+归档；重建后要加监控+鉴权（MCP delete 工具无鉴权）。给出明确建议和理由
6. **launchd 静默死亡模式**：同类事故 3 次（memory-health/备份/MCP）。单机 macOS 上让后台任务「死了会喊疼」的成熟做法是什么（SMAppService/健康心跳文件/互相探活/推送告警）？给出适合本系统的最小方案
7. **防再犯契约**：哪些接线应该用测试锁死（env 名与 compose 一致性、调用方存在性、模型 id 现役性、索引新鲜度上限）？给出具体的契约测试清单
</research_questions>

<case_requirements>
找 10+ 成熟案例/一手来源，每个 7 字段：url_primary / url_wayback / accessed_date(+HTTP状态) / info_type(fact|opinion|benchmark) / sample_size / tier(T1官方|T2权威|T3社区|T4传闻) / fit_score(1-5，对照「单人本地 Obsidian+Claude 学习系统」画像)。重点领域：本地笔记 RAG 索引新鲜度机制、LangGraph 生产管道的存活监控、单机后台任务告警、RAG 质量遥测。
</case_requirements>

<deliverable>
1. 复发根因的结构性诊断（回答 Q1）
2. 三个 P0 的修复方案裁决表：我方方案逐项 keep/修改/否决 + 理由 + 你的替代方案
3. 「6 源管道修活 vs 退役」的明确推荐（带量化论证）
4. 防再犯契约测试清单（可直接转化为 pytest 的具体断言描述）
5. 案例表（≥10 条 7 字段）
6. 诚实标注你无法从附件确认、需要我们实机验证的点
</deliverable>

</review_request>
