> 批次: BATCH-2026-09-07-第十三批 · 车道 U5(card-u5-lance) · 卡 CARD-HYGIENE-openapi round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-openapi-r3.md)"`
> 审查绑定: `a525d8ad` （收口轮：绑最终 HEAD；代码面自 `11dfe410` 起零变动）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `sandbox: read-only`

---

绑定 **`a525d8ad8c3235d07287cd58a56ed4b3d5431302`**。结论：**B0 / H0 / M5 / L2**。round-2 HIGH-1 对应的排除修复成立，但剩余 GET 写盘面和验收单的归因仍未收口。

BLOCKER：本节无。HIGH：本节无。

下文 `UAT` 指 [_bmad-output/验收单/UAT-CARD-HYGIENE-openapi-2026-09-09.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-HYGIENE-openapi-2026-09-09.md)。调用链路径均相对本仓。

**MEDIUM-1 — 把 mtime 观测升级为严格因果实测。**

位置：`UAT:269–276`；`find-newer-attribution-r2-20260910T025520.txt:26–34`。

一句话条件：**两轮复用已经创建的数据、且未证明请求和初始状态一致时，文件第二轮没有更新，不能证明唯一原因是排除了三条 GET。**

先回答几个具体问题：

| 情况 | 对 mtime 推断的影响 |
|---|---|
| 普通写入相同内容 | 实际执行非零长度写入，通常仍更新 mtime；“字节相同所以不更新”不是有效反例。应用比较内容后跳过写入则确实没有发生该次写。 |
| 写临时文件后原子替换 | 目标取得临时文件的 mtime，替换本身不保证产生新的内容修改时间。本仓 FSRS 路径先 `write_text` 再 `replace`，没有保留旧时间的逻辑。 |
| 别的进程持有文件 | 单纯持有不影响 mtime 更新；但若路径已被替换，进程继续写旧 inode，最终 `stat(path)` 看不到旧 inode 的写入。 |
| 写后删除、恢复旧文件或恢复时间戳 | 最终扫描可以漏掉中间写入。 |
| SQLite WAL、未刷出的用户态缓冲 | 主文件 mtime 不代表所有逻辑写入；写入可能在其他文件或尚未提交到文件系统。 |
| 时间精度、时钟调整、`find -newer` 严格大于 | 可以造成边界漏检；普通时间精度不足不能解释这里相差数小时的旧时间。 |

这些是推断成立所需的边界，**不表示本轮发生了这些反例**。

对具体 FSRS 实现，`review_service.py:604–605` 的正常成功写入会留下新 mtime，因此旧 mtime 是“终轮未发生该正常成功更新”的强佐证。但源码还显示：`:2468–2476` 先查已有卡，只有缺卡等条件满足才在 `:2507` 写盘。初始数据不同，本来就可能改变写行为。

所以应写：

> 终轮未观察到三个目标文件的 mtime 更新；FSRS 结果与排除修复一致。写链成立及其移出生成面已由源码和集合核对确认，历史唯一写者和严格因果关系未由此次对照独立证明。

这不推翻旧 HIGH-1；它纠正的是“**这不是推理**”这一证据等级。

**MEDIUM-2 — pending 文件的最终 mtime 无法证明只在关闭时写入。**

位置：`UAT:267`；`find-newer-attribution-r2-20260910T025520.txt:21–24、37–38`。

一句话条件：**后台曾经写入、最后 shutdown 又重写同一文件时，最终 mtime 只显示最后一次，运行中的写入全部被这个时间覆盖。**

关闭路径确实存在：

`backend/app/main.py:474`  
→ `services/vault_index_orchestrator.py:864`  
→ `:337 mkdir`、`:339 open("w")`、`:341 write`、`:342 os.replace`。

但同一持久化点还有：

| 写入来源 | 调用链，位于 `vault_index_orchestrator.py` |
|---|---|
| 文件监听 | `:774–776 enqueue` → `:298 / :316 _persist_sync` |
| 启动及周期扫描 | `:804 reconcile` → `:624–628 _persist_sync` |
| 后台批处理 | `:519 process_batch` → `:499 _persist_sync` |

这些任务由 `main.py:434` → `orchestrator.py:841–844` 启动，可在运行期间和结束附近写入。

而且：

`21:46:42 + 5:06:32 = 02:53:14`，**并非 `02:53:30`**，相差 16 秒。

合理结论是“mtime 接近结束，与 shutdown 写路径相容”。本轮没有闭合出保留 GET 直接调用该持久化点的链，但也不能凭这个时间确认历史唯一写者。`UAT:448–450` 自己仍写“未闭合到本次全跑的具体写者”，与 `:267` 的确定归因冲突。

**MEDIUM-3 — 剩余统计 GET 仍有请求期 SQLite 初始化写。**

位置：[backend/tests/contract/test_openapi_contract.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/contract/test_openapi_contract.py:80)；`backend/app/api/v1/system.py:969` 等。

一句话条件：**单例未初始化、数据库或表缺失，或者迁移尚未执行时，这些保留 GET 会创建目录、数据库、表或索引。**

以下路径均在 `backend/app/`：

| 保留 GET | 到写盘点的调用链 |
|---|---|
| `/system/qa-metrics` | `api/v1/system.py:969–970` → `services/difficulty_matcher.py:439 mkdir`、`:393 _ensure_init` → `:139–142 SQLite connect / CREATE / commit`；另 `system.py:978–979` → `extraction_validator.py:480` → `:170–180 CREATE / ALTER / commit` |
| `/system/extraction-records` | `system.py:1062–1063` → `extraction_validator.py:417` → `:170–180` |
| `/system/error-aggregation` | `system.py:1246–1247` → `error_aggregator.py:247` → `:188–191 CREATE / commit` |
| `/system/pipeline-health` | `system.py:1017–1018` → `health_monitor.py:81、127、476–477` → 上述 error aggregator 初始化 |
| `/system/llm-stats` | `system.py:712` → `middleware/cost_tracker.py:545–547` → `:218 makedirs`、`:220–226 CREATE / commit` |

前四条涉及 `backend/data/qa_metrics.db`。最后一条涉及 `llm_call_logs.db`，**另需 cost tracker 未经 lifespan 预热**；正常 lifespan 在 `main.py:151` 已先初始化，不能据此断言终轮由该 GET 写入。

这也提供了具体混杂因素：首轮建好 schema，终轮仍保留这些 GET，却可以不再更新数据库文件。它们的 mtime 消失不能归功于那三条排除。

**MEDIUM-4 — 排除 multimodal health 后，其余四个 GET 仍会建目录。**

位置：[backend/app/dependencies.py:897](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/dependencies.py:897)。

一句话条件：**MultimodalService 尚未构造且媒体目录缺失时，任一剩余 multimodal GET 的依赖解析都会创建目录。**

涉及：

`/api/v1/multimodal`、`/multimodal/list`、`/multimodal/by-concept/{concept_id}`、`/multimodal/{content_id}`。

调用链：

`endpoints/multimodal.py:214 / :261 / :360 / :411`  
→ `dependencies.py:906、830、897`  
→ `services/multimodal_service.py:1599–1603` 构造单例  
→ `:205 _ensure_storage_dirs`  
→ **`:214、216 mkdir(parents=True, exist_ok=True)`**。

存储根由 `dependencies.py:849–850` 计算为配置的 canvas 根下 `multimodal/`。这是请求期惰性初始化；目录已存在时没有新增变化，不能用终轮扫描否定该路径。

**MEDIUM-5 — 剩余 review／RAG GET 可首次写出学习记忆 JSON。**

位置：[backend/app/clients/neo4j_edge_client.py:792](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/clients/neo4j_edge_client.py:792)。

一句话条件：**LearningMemoryClient 尚未初始化、`learning_memories.json` 不存在且相应查询分支可达时，读取 GET 会创建初始 JSON 文件。**

入口链：

- `/review/history`：`endpoints/review.py:681` → `review_service.py:1509、1513–1514`；要求 `graphiti_client` 非空。
- `/review/progress/multi/{original_canvas_path}`：`review.py:1198` → `review_service.py:2036、2079、2092–2093`；同样要求该 client 非空。
- `/rag/weak-concepts/{canvas_file}`：`endpoints/rag.py:480` → `rag_service.py:435、358、370–374`；要求 LangGraph 可用。

共同写点：

`clients/graphiti_client.py:4` 重导出  
→ `neo4j_edge_client.py:792 mkdir`、`:800–808` 缺文件初始化  
→ `:822 atomic_write_json_async`  
→ `utils/atomic_io.py:140、118、71、79、85`，创建临时文件、写入并替换目标。

默认目标由 `neo4j_edge_client.py:43–45` 定义为 **`backend/data/learning_memories.json`**。这是源码确认的条件性写入，不是本轮历史写入证明。

**LOW-1 — 日志归因机制基本成立，但“必须排除整个 health 面”的理由不成立。**

位置：`UAT:266`；终轮归因文件 `:15–19`。

一句话条件：**若用“排除整个 health 面”的损失来决定日志豁免，所依据的覆盖代价被夸大了。**

授权源码中闭合的直接写者是 **`GET /api/v1/health/neo4j`**：

`endpoints/health.py:837` enabled 分支  
→ `:849` 导入 logger  
→ `:853、865、883、909` 记录请求开始和结果  
→ `core/memory_system_logger.py:68、35、41`，建目录并使用文件 handler。

因此“请求期健康检查日志”这个分类准确；本次 `22:06:45` 的具体写者仍只是与该机制一致，mtime 本身不能识别请求或进程。可以继续登记日志豁免，但无需把代价描述成整个 health GET 面。

另外，日志可能性不限于该文件：未处理异常还可经 `main.py:721` → `core/bug_tracker.py:155–156` 追加 `bug_log.jsonl`；本轮是否触发未证明。

**LOW-2 — UAT 最终汇总仍有旧数字和超出检测范围的保证。**

位置：`UAT:465、478–484、510`。

一句话条件：**读者只看完成表和用户段时，会得到过时的排除数量，以及 fixture 能覆盖所有课程目录污染的错误印象。**

具体段落：

- `:465` 仍写“追加 **1** 条”“**114** 行”；最终应为 **4／117**。
- `:484` 仍写“114 项”。
- `:478–483` 的“不会再……多出”“真冒出来……会……告诉我”，以及 `:510` 的“一旦写进来 fixture 会报警”，缺少“**模块检查时仍存在于 backend 顶层五项**”的限定。

这里需要修正文案；不要求扩大已登记的 `_SKELETON` 授权范围。

其余核对结果：

- **问题 4：本节无发现。** 实际安装的 schemathesis **4.14.3** 中，`schemas.py:218` 克隆已有集合，`:224` 追加排除；`filters.py:151–152` 复制旧集合，`:289` 执行 `_excludes.add()`，`:166–168` 任一排除命中即拒绝。四次 `.exclude()` 累积生效，与采集结果一致。
- **集合正控全部成立。** 独立重算为 `206 → 89`、排除 `117`；差集完全一致，GET `/` 保留；相对 `dddfc598` 的采集清单，新增 0，恰移除指定三条。
- **没有把 3-c 写成通过。** `UAT:247、255` 明确记载两轮未通过。问题主要是上述确定归因和宽泛保证。
- **(g) 只能确认合计口径。** `89+3=92` 的算术成立；块 B 原始基线文件不在本轮指定读取面，未独立认证“三条失败原因相同”，分跑结果也不是单进程目录全跑的实测。
- 本轮未为全部 89 条签零写证明：部分 rollback、索引调用进入授权范围外的 `src/` 或第三方实现，已停在边界。

**不需要再跑五小时。** 先修正归因与汇总文字；对新增写链若需动态验收，可在隔离临时目录仅验证相关本地初始化函数并记录实际文件操作。重复使用已初始化数据的全量测试，不能解决这里的冷初始化盲点。

本轮未修改文件，未读取 `.env`，未连接数据库、外部服务或发起 HTTP 请求。
