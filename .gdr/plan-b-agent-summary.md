# 4 Agent 并行对抗审查 — 调研汇总

## Agent A: Plan B 偏离 Story 2.4 spec

**6 核心发现**:
1. 真相源偏离: spec=frontmatter / Plan B=Neo4j EpisodicNode (CRITICAL)
2. 触发方向: spec=backend pull / Plan B=plugin push (HIGH)
3. AC#1/2/3: spec 要求 backend/app/services/callout_parser.py 新建; Plan B 把 parse 改到 plugin TS 端 (CRITICAL)
4. AC#4 注入: Plan B 写 Graphiti, 但 context_enrichment_service.py 零处 import memory_service/graphiti/neo4j_client → 死链 (BLOCKER)
5. AC#5 删除: spec frontmatter 数组移除; Plan B append-only 永远累积 (HIGH)
6. 离线弹性: spec 文件保留; Plan B plugin POST 失败 silent → 100% 数据丢失 (CRITICAL)

**Agent A Q1-Q5**:
Q1 (链路死链 BLOCKER): Plan B 写 Graphiti 但 context_enrichment_service.py line 276 只读 frontmatter "tips = fm.get('tips')", 零处调 memory_service 或 Neo4j. 日常 /chat-with-context 主链路不读 Graphiti tips. Plan B 数据怎么进 LLM 上下文? 是不是除了 quiz_from_callout 这条 P1 链路外, Plan B 全部写入都是 dead-end?
Q2 (删除不可逆): AC#5 要求"删除 callout → tip 从 tips[] 移除". Plan B 是 append-only, vault.on('modify') 只看修改后内容看不到"哪条被删了". Plan B 怎么实现 AC#5? 只能假装删除从未发生?
Q3 (离线丢失): plugin grep 0 处含 retry/queue/indexedDB. 离线编辑 POST 失败 → silent drop → 永久丢失. Plan B 离线场景损失率 100%?
Q4 (验收单作废): 用户加 50 条批注 frontmatter tips:[] 仍空. 用户没装 Neo4j Browser 怎么验证? spec UAT 步骤 4 在 Plan B 下变成"打开 Neo4j Browser 跑 Cypher"违反 DoD-3 D3-A. Plan B 让 Story 2.4 验收单变成无法验收?
Q5 (Story 3.6 + 1.16 数据混合): _get_tips 修复让 Story 3.6 侧栏 tip 和 Story 1.16 白板 callout 共用 source_description IN 查询. quiz 通道两种异质数据被 LIMIT 5 后随机筛选混入 ACP — prompt 污染?

## Agent B: content_hash 双层幂等 14 漏洞 (V1-V14)

**P0 BLOCKER**:
- V5: Neo4j 查询缺 node_id 过滤! 跨文件 hash prefix 碰撞 → file B 新 callout 被误判已存在跳过
- V8: AC#5 删除追踪 0 感知

**P1 HIGH**:
- V2: Lucene 默认 standard analyzer 分词 [hash:abc12345abcdef01] 为 token "hash" + hex 串 → 任何 query 含 "hash" 命中全部 callout → fulltext score 污染
- V3: Tier 2 fulltext 返回 raw content (含 hash marker) → 注入 LLM context → LLM 看到 [hash:xxx] 当内容
- V7: gunicorn 多 worker 部署 in-memory cache 失效
- V10: source_description canonical mismatch 风险
- V14: 跨 vault basename 撞名 (hash 输入未含 vault_id)

**关键事实证明**:
- Graphiti add_episode **不改写 content 字段** (store_raw_episode_content 默认 True) ✅ hash marker 设计安全
- 但 SET n = {...} 9 字段固定覆盖 → **永远不能依赖额外 metadata column 持久化** ❌ 长期演化必须绕过 Graphiti 直接写 Cypher

**Agent B Q1-Q5**:
Q1 (V5 跨文件碰撞): MATCH (e:Episodic) WHERE e.content CONTAINS $hash_marker 完全没 node_id 过滤. in-memory cache key=node_id|hash 能区分但 Neo4j 查询不区分. 64-bit prefix 跨文件场景碰撞概率? 为什么不在 Cypher 加 node_id?
Q2 (V2+V3 Lucene 污染): [hash:abc12345abcdef01] 被分词成 hash + hex 串 token 进 fulltext 索引. 用户 query 含"hash"将命中所有 callout. 怎么处理 fulltext score pollution? 切 keyword analyzer + 独立字段? 但 SET n = {...} 会抹掉额外字段.
Q3 (V8 删除追踪): vault.on('modify') + 整文件 batch 只识别"新增", 删除事件 0 感知. 倾向 (a) plugin local manifest 维护 hash set diff (b) valid_at 软删除 (c) 每次 batch 全删全插? 方案 a 跨设备同步怎么处理?
Q4 (V1 Graphiti 内部约束): get_episode_node_save_query 用 MERGE + SET n = {9 个固定字段}. 任何手工 patch 的额外字段在下次 add_episode 后被抹掉. 长期演化必须绕过 Graphiti 直写 Cypher. 是否承认内嵌 marker 是永久妥协? 是否应考虑 Plan C (脱离 Graphiti 的 callout 专用 collection)?
Q5 (64-bit 安全): SHA-256 前 16 hex (64-bit) 在密码学是 2^32 生日碰撞门槛. 是否应改用全 64 hex (256-bit)?

## Agent C: 长期数据库 + 检索成本

**1 年最坏情况预估**:
- EpisodicNode: 54,750 / EntityNode: ~164,000 / EntityEdge: ~109,500 / MENTIONS: ~273,750
- Neo4j DB size: 1.5-2 GB (HNSW 3x)
- Gemini API: ~219,000 次, ~$140-280/年 (2hr/天最坏)
- 单 episode 写入延迟: 14-20s

**核心反驳事实**:
- dedupe_nodes 源码 grep "temporal/time" — **0 命中**! 合并 LearningConcept "重新规划" T1 和 T2 → 同一 EntityNode → **演化痕迹擦除** (用户 G7 担忧成真)
- Graphiti issue #1083 (orphaned entities 未修)、#1300 (retention maintainer 零响应)、#1193 (cost concern)、#1204 (LaTeX JSON parse fail)

**对比 frontmatter spec**:
- 1 年增量: ~10 MB (Plan B 1.5-2 GB ~200x)
- LLM 成本: $0 (Plan B $140-280)
- 写入延迟: < 1ms (Plan B 14-20s)

**Agent C Q1-Q5**:
Q1 (dedupe temporal): dedupe_nodes.py 源码无 temporal 逻辑. LearningConcept "重新规划" T1/T2 被合并到同一节点. v1/v2/v3 episode 演化在 Entity 层不可用 — mastery 评分怎么知道 T1 60% / T2 85%?
Q2 (orphaned entity): Graphiti issue #1083 确认 remove_episode 留 orphaned entities, maintainer 半年没修. Canvas 后续怎么实现"撤销批注"? 只能 append 永远不能 delete? 1 年后 ~110K LearningConcept entity 多少是用户实际想保留的? 给出具体清理策略.
Q3 (dead-letter): 用户实测 1 句话 8 sync × 14-20s = 第 2-8 次同步时第 1 次还没落地. 第 3 次 Gemini 429 → episode dead-letter. Canvas dead letter 监控在哪? retry queue 在哪?
Q4 (IME 放大成本): 成本估算假设 1h 30 episode, 但 IME 触发频率高 3-5 倍. 2h/天 × 拼音放大 = ~$280/年 API. 这钱为什么不能换成 frontmatter revision_history[]? git diff 免费送演化追踪.
Q5 (DD-08 用户初衷): 用户从未表达过"需要 AI 自动从批注里抽取实体边". 用户说"批注落地 + wikilink 可追溯 + 跨白板可发现". 前 2 frontmatter 完美做, 第 3 个 Obsidian Graph View 原生. Plan B 解决的是 Graphiti 团队产品愿景而非 Canvas 用户学习愿景. 给出一个用户故事 — 一句用户的话 — 能且仅能用 Graphiti append-only 解决, frontmatter 无法解决. 给不出 Plan B 就是 over-engineering.

## Agent D: 真实用户失败场景 F1-F15

**CRITICAL**:
- F1: Cmd+Q 退出 debounce 未 fire (plugin 0 处 onunload 钩子) → 100% 数据丢失 (必然不是概率)
- F10: 删除整个 callout → KG 留 ghost episode → 隐私 + 学习错乱

**HIGH**:
- F2/F3: 离线无 retry queue → silent drop
- F5: Find & Replace 50 callout → Gemini 队列堵塞 12.5 分钟
- F6: backend 重启 + Graphiti 异步队列 → in-memory cache 空 + Neo4j lag → 重复 v2
- F7: Templater/Linter 副作用 modify → parser 损坏 markdown silent throw → silent fail
- F9: git checkout 旧版本 → plugin 重 parse 旧 callout 算旧 hash → backend skipped → Neo4j v4 不回滚
- F11: 中文/LaTeX/emoji callout → Gemini 解析失败 (issue #1204)
- F13: crypto.subtle 异常 → unhandled rejection → silent fail
- F15: refresh-changed vs tips/batch 双路径并行 (当前代码现状)

**重要基线偏移**:
真实代码现状: plugin 是 1500ms debounce → POST /api/v1/index/refresh-changed (paths-only), **没有客户端 callout 解析、没有 SHA256、没有 /tips/batch 调用方**. 后端 /tips/batch 端点就绪但 plugin 未真正接入 — Plan B 是"半成品"状态.

**Agent D Q1-Q5**:
Q1 (F1 onunload): Obsidian plugin onunload() 是同步的. 即使 onunload 调 requestUrl POST, Obsidian 是否在请求完成前 kill 进程? 正确持久化方案: 写本地 file (.canvas-pending-queue.json) 还是 IndexedDB? 哪个保证 next plugin load 100% replay 成功? Obsidian 1.5+ 官方 API?
Q2 (F6 重启竞态): in-memory cache 进程重启清空. Graphiti add_episode 异步, 重启时 Gemini queue 还有未完成 episode. 第一次 batch POST 来 Neo4j 查询返回 false → 重复创建. 修复 (a) 启动 warmup cache 从 Neo4j 加载最近 1000 hash (b) 每个 add_episode 写 pending_hash lock 节点? 哪个更稳? 社区先例?
Q3 (F10 tombstone 范式): append-only 删除 (a) soft delete (deleted_at + 查询过滤) (b) tombstone event. Graphiti EpisodicNode 时序图哪种更符合? 选 tombstone, 删除后重写完全相同内容 → content_hash 相同 → resurrect 旧 v1 还是创建 v2? Bluesky/Mastodon 怎么处理?
Q4 (F5 分层 sync): Graphiti P95 ~15s. Find & Replace 50 callout = 12.5 分钟队列. 用户期望"改完立刻看到效果". 分层 (a) ≤3 fast path (b) 4-20 异步 progress URL (c) >20 拒绝 or 降级到只 hash 不 LLM? 后者意味 callout 进 KG 但不参与语义检索, 可接受?
Q5 (F11 LaTeX 失败感知): issue #1204 (LaTeX \frac JSON parse fail). batch fail tolerance 单条不阻塞, 用户看到聚合"5 成功 1 失败" 不知哪条. 修复 (a) 失败 callout 回传 plugin 高亮 (但 Obsidian 没"高亮某行"官方 API) (b) 写 .canvas-sync-errors.md 让用户自看? 60 岁用户哪种?

## 整合 — 4 BLOCKER
- B1 数据链路死链 — Agent A Q1 — context_enrichment_service 不读 Graphiti
- B2 删除追踪 0 感知 — Agent A Q2 + B Q3 + D Q3 — append-only 与 AC#5 根本矛盾
- B3 Cmd+Q 100% 数据丢失 — Agent D Q1 — plugin 无 onunload flush
- B4 跨文件 hash prefix 碰撞 — Agent B Q1 — Neo4j 查询缺 node_id 过滤
