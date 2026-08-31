# Codex 单轮终裁存档 — CARD-DEBT-16（P1 七残项）

> **卡**: CARD-DEBT-16 · **批次**: BATCH-2026-08-31-第七批 · **车道**: V7
> **模型/参数**: `codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra"`
> **审查基线**: tracked HEAD `9cf0fb85ed839bb7035d023534fca222a24d6968`
> **输入审查包**: `_bmad-output/审查/2026-08-20-P1-05d-五轮审查包-给Codex.md`（2026-08-20 备好但从未送审）
> **轮次**: 单轮终裁（2026-08-24 用户裁定：重型多轮外审仪式 SUPERSEDED，实质义务不豁免，由本卡以单轮承接）
> **沙箱声明（Codex 原文）**: 仅使用合成临时 vault/LanceDB，未读取真实 vault、未连接或写入真实 Neo4j
> **提示词全文**: 见本文件 §附录
>
> ⛔ 本文件是**终裁原文逐字存档**，不做删改。我方复核意见与吸收结论在
> `2026-08-31-DEBT-16-P1残项CLOSED-STILL-OPEN台账.md`。

---

## 终裁原文

终裁结果：**1 项 CLOSED，6 项 STILL-OPEN**。审查基线为 tracked HEAD `9cf0fb85ed839bb7035d023534fca222a24d6968`；仅使用合成临时 vault/LanceDB，未读取真实 vault、未连接或写入真实 Neo4j。

### 1. 七项裁定表

| ID | 裁定 | 证据（文件:行号 / commit） | 若 STILL-OPEN：可复现失败场景 |
|---|---|---|---|
| **P1-05** | **STILL-OPEN（部分闭合）** | C1 `c154a7f283875bf3542461a782f73b869a474592` 已将 containment 门接入 full/single 入口：[lancedb_client.py:507,1657,1974](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:507)。但 full scan 在准入后集合为空时于 [lancedb_client.py:1663-1666](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1663) 提前返回，早于 fingerprint diff 和旧行删除 [lancedb_client.py:1678-1702](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1678)；该 direct 入口仍由 [metadata.py:580-600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/metadata.py:580) 使用。 | 临时库先索引合法 `节点/only.md`，再把它替换为指向 vault 外 `outside.md` 的 symlink；调用 `index_vault_notes(vault_path=..., force_rebuild=False)`。观测：返回 `0`，但 row 与 fingerprint 各仍为 `1`、路径均为 `节点/only.md`。同状态经 orchestrator [reconcile/delete/orphan:483-530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/vault_index_orchestrator.py:483) 后二者才归零。 |
| **P1-01** | **CLOSED** | 当前跳写条件已经与 generation 解耦：必须同 generation、版本严格等于 3、且整包通过 SnapshotV3；否则强制重写：[board_manifest_service.py:958-985](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/board_manifest_service.py:958)、严格加载 [board_manifest_service.py:1020-1072](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/board_manifest_service.py:1020)。同代 v1、future version、根/嵌套错型及带垃圾键 v3 的回归锁位于 [test_snapshot_schema_migration_contract.py:126-180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/tests/regression/test_snapshot_schema_migration_contract.py:126)、[test_snapshot_v3_contract.py:262-340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/tests/regression/test_snapshot_v3_contract.py:262)。修复提交 `1683328c2e51bd53e965817c3a556f1026414da9` 在当前祖先链。 | — |
| **P1-08** | **STILL-OPEN** | C4 `1b7485b98812dbfea380f70f05ae3253dd79e68d` 立下的纪律仍写在 [CURRENT_TASK.md:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/CURRENT_TASK.md:16)，但后续提交 `270c171664…` 又在 [CURRENT_TASK.md:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/CURRENT_TASK.md:7) 写入 `517 passed`，并在 [CURRENT_TASK.md:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/CURRENT_TASK.md:11) 把当前 HEAD 已完成的 s6/t2 合并仍写成未来动作。`_bmad-output` 的当前 goal 总账仍使用定性 CI 状态 [总账:1085](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:1085)；历史审查报告内的测试计数属于冻结证据，不视为状态锚点。 | 新上下文只读恢复锚点前 15 行：观测到禁止落盘的通过数，并被告知执行已在 HEAD 完成的“下一步”。因此同一文件内纪律与实际锚点矛盾。 |
| **B4** | **STILL-OPEN** | `CanvasGraphEpisodeV1` 的 vault/group/canvas/node IDs 仍是裸 `str`，且无 provenance：[canvas_episode.py:208-247](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/graphiti/canvas_episode.py:208)。生产 API、MemoryService 与 writer 未形成统一强制门：[memory.py:547-576](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/memory.py:547)、[memory_service.py:1402-1453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/memory_service.py:1402)、[graphiti_structured_writer.py:106-142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/graphiti_structured_writer.py:106)。完整会话原文 sibling 隔离已做，但摘要/tips/Q&A 仍走普通 group：[memory.py:749-761](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/memory.py:749)、[conversation_distiller.py:359-407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/conversation_distiller.py:359)。SnapshotV3 无来源 digest [snapshot_v3.py:243-251](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/models/snapshot_v3.py:243)，generation 仅绑定路径/mtime/size [board_manifest_service.py:501-519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/board_manifest_service.py:501)。 | ① `node_id="../../forged"` 及不匹配的 vault/group/canvas 可被请求模型和 episode 模型接受。② 传入 `provenance={...}` 后 `model_dump()` 静默丢字段。③ 正常 session 的全文进 sibling，但结构化摘要仍进入普通 group。④ 生成 score=`0.4` 的快照后，仅把落盘 score 改成 `0.99` 且保留 generation；下一次 live 不重写磁盘，删除节点源触发降级后返回伪改的 `0.99`。 |
| **TOCTOU** | **STILL-OPEN** | single 入口先 containment check、后按路径重新 open：[lancedb_client.py:1973-1981](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1973)。full 入口也是先检查，再分别 hash/read：[lancedb_client.py:1655-1660,1681,1718-1728](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1655)。同型窗口还存在于 backfill、relationship、projection、error rebuild，例如 [vault_backfill.py:195-201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/vault_backfill.py:195)。 | 在检查返回后、正文读取前确定性替换路径对象。single/full 两真实 Lance 入口均观测：`returned=1`、替换后 marker 出现在索引 row、`row_count=1`；说明检查、hash、正文未绑定同一文件句柄/同一组 bytes。图写入后的真实 Neo4j 影响为 `UNVERIFIABLE`，但 Lance 持久化反例已经足够判开。 |
| **P1-03** | **STILL-OPEN（部分闭合）** | 已闭合：统一四态 [service_status.py:39-139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/models/service_status.py:39)、三条 statused 入口、CanvasRAGState [state.py:183-202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/state.py:183)、RAG fallback，提交 `9960b14640272f5d57ac2ebf008c70499fb4c3a8` 经 `d3dcb16cd0262f93da7b08e5e7d560abd1faded7` 合入。仍缺：Graphiti/Lance 客户端内部异常直接降 `[]` [graphiti_client.py:312-379](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/graphiti_client.py:312)、[lancedb_client.py:3061-3077](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:3061)；search/suggestions 生产兼容入口主动剥状态 [memory_service.py:1091-1106,2384-2409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/memory_service.py:1091)；history 无健康兜底时仍固定判 degraded [memory_service.py:795-805](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/memory_service.py:795)。 | ① 真实 Graphiti client 内部查询抛 `ConnectionError`：观测 `client_search=[]`、`channel_errors={}`、融合结果 `status="empty"`、reason=`null`。② statused search/suggestions 返回 `unavailable("backend down")`，经旧生产入口后均只剩 `[]`。③ 冷启动、无内存 episode、Neo4j 主/恢复查询均失败：观测 `items=[]、status="degraded"`，而统一折算规则 [service_status.py:172-192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/models/service_status.py:172) 要求 `unavailable`。 |
| **P1-04** | **STILL-OPEN** | API schema 无 `status/degraded_reason`：[memory_schemas.py:130-149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/models/memory_schemas.py:130)、[rag.py:122-142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/rag.py:122)；endpoint 重建响应时丢状态 [memory.py:201-237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/memory.py:201)、[rag.py:264-326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/api/v1/endpoints/rag.py:264)。`frontend/` 对 `retrieval_status|retrievalStatus` 零命中；LearningProfile 将子数据失败折成 `?? []`：[LearningProfile.tsx:36-96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/frontend/src/components/profile/LearningProfile.tsx:36)。git 全历史未找到 CARD-G4-3 提交。 | MemoryService 返回 `items=[]、status=unavailable、reason="neo4j down"`，调用真实 endpoint 后响应只有 items/分页字段；RAG 返回 unavailable 后仍是 200 空结果且无状态。消费者看到的 bytes 与健康真空相同。 |

P1-01 的边界需特别说明：`mastery_a=mastery_b=1e308` 可使派生 `sigma/pick_score=NaN`，这个反例真实存在；但重写同一个当前 v3 并不能修复它，而且五轮包已把“同 generation、schema 合法但内容真实性/数值语义不足”明确归入 B4 [五轮包:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/_bmad-output/审查/2026-08-20-P1-05d-五轮审查包-给Codex.md:39)。因此它使 **B4** 保持开放，不重新打开已完成的 **P1-01 generation/schema 迁移义务**。

绿灯与裁定不冲突：

- P1-05 的 40 个唯一相关回归只证明“拒绝文件不新增”及 orchestrator 能清旧行；direct 测试从空库开始 [test_real_entrypoint_admission.py:72-85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/tests/regression/test_real_entrypoint_admission.py:72)，未覆盖历史 row。
- P1-03 的 81 个定向测试让 getter 在客户端外层抛异常，或手工注入 `channel_errors`；没有经过客户端内部 `enable_fallback=True → []`，并且测试还锁定旧 list wrapper。
- B4 邻接 48 测试只验证基础模型/路由/writer 原样传递，没有让 episode schema 成为 endpoint→queue→writer 的强制门。
- TOCTOU 的现有用例只测试稳定路径状态，没有“检查后、读取前”交错。
- P1-04 当前没有 G4-3 契约、trace 或 UI 验收绿灯。

### 2. owner 映射表

| STILL-OPEN 项 | owner 卡 | what / 完成判据方向 / 估时 / wave |
|---|---|---|
| P1-05 | **需补卡 DEBT-17：direct full-scan 准入收敛** | 移除空准入集的 pre-diff return，并清理 fingerprint deletion 与无 fingerprint orphan。真 LanceDB 覆盖“合法入库→目录黑名单/文件黑名单/外部 symlink/物理删除”，一次默认 full scan 后 rows+fingerprints 均为 0；覆盖 metadata endpoint。**3h，Wave 1，无依赖。** |
| P1-08 | **需补卡 DEBT-18：可执行锚点纪律** | 重建 CURRENT_TASK 前 15 行，删除 CI 通过数和已经完成的未来动作；建立只检查“可变状态文档”的 lint，冻结审查证据显式 allowlist。fixture 写入 run 号或 `517 passed` 必须使 lint 变红。**2h，Wave 1。** |
| B4 | **CARD-G4-8，归属恰当但必须拆分** | **G4-8A** payload admission/provenance/session namespace：真实 endpoint→queue→writer 拒绝伪造 ID、持久化 required provenance、所有 session 结构化产物隔离；**5–7h，Wave 3，deps G4-5 + DEBT-11**。**G4-8B** Snapshot 数值闭包与来源完整性：覆盖 `1e308` HTTP JSON、canonical-source digest/等价证明、同代 `0.4→0.99` 改写必须重建或拒绝；**6–8h，Wave 2，不应被 G4-5/DEBT-11 阻塞**。 |
| TOCTOU | **需补卡 INFRA-DEBT-01：已验证文件对象贯穿** | 不归 G4-8；它跨 Lance、backfill、relationship、projection、error rebuild。统一 `open_admitted_markdown` 或等价抽象，使 containment、regular-file、identity、hash、正文基于同一 fd/handle/bytes。所有生产 reader 的确定性交错必须显式拒绝/一致重试，并产生零 hash/index/dry-run/graph-write；macOS/Linux 契约一致。**10h；Wave 1 启动。建议拆 01A Lance/orchestrator 5h、01B 其余 reader 5h（Wave 2，依赖 01A）。** |
| P1-03 | **CARD-G4-2 重开；流程不允许重开则建 G4-2R，owner 链仍属 G4-2** | 修复真实客户端吞异常、五路 RAG 状态覆盖、history unavailable 折算，并迁移全部生产调用方离开剥状态 wrapper。**余量约 4–6h，Wave 1。** |
| P1-04 | **CARD-G4-3** | 原卡范围准确，无需拆：API 加性字段、trace、Claudian/总览消费；真实不可达后端下 UI 必须显示 degraded/unavailable，健康空结果显示 empty。**总账估时 6h，Wave 2，依赖 G4-2R。** |

### 3. C 批修复引入的新缺陷清单

**没有证据证明 C1/C2/C4 本身引入了新的生产缺陷**；但发现一处 C1 未闭合旧洞和一处 C4 后续回归：

- C1：direct full-scan 的空集提前返回由更早提交 `0c4fe286d…` 引入，早于 `c154a7f2`。C1 关闭了固定态越界读取，但没有覆盖历史行收敛，因此是“不完整修复”，不是 C1 新造缺陷。
- C2：`1e308 → NaN` 的 finite-only validator 与 beta 运算均早于 `1683328c`；属于 G4-8B 的数值/来源完整性缺口，不是 C2 migration 回归。
- C4：`270c171664…` 在 C4 之后重新写入 `517 passed`；这是缺少自动纪律门导致的后续回归，不是 `1b7485b9` 当次改动直接引入。

三个 strict 边角的构造结果：

- 不存在的 vault 内文件：`should_index()` 返回 `ok` 是事件排队语义；worker 处理时仍不存在会转 delete [orchestrator.py:360-366](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/app/services/vault_index_orchestrator.py:360)。
- candidate 等于 vault 根：containment helper 判“未越界”正确；single 入口随后以非文件拒绝 [lancedb_client.py:1924-1927](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1924)。
- 同 CWD 的相对 vault/file 判在内；只传相对 file 配绝对 vault 会保守拒绝，而生产契约要求 absolute file [lancedb_client.py:1907-1912](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt/backend/lib/agentic_rag/clients/lancedb_client.py:1907)。
- 扫描后 reconcile 的拒绝旧行可清；失败只发生在仍受支持的 direct full-scan 路径。

另有低严重度旁观项：reconcile 对同一路径同时计 deleted/orphan 时报告 `enqueued=2`，实际 pending 唯一键只有 1；可并入 DEBT-17 修正遥测计数。

### 4. 收官判词

- **P1-05：STILL-OPEN**——固定态 vault 准入反例已关，但 direct full-scan 对历史拒绝行不收敛，不能结案。
- **P1-01：CLOSED**——旧版、future、缺版及 schema 非法快照已经能在 generation 不变时强制迁移；来源真实性另属 B4。
- **P1-08：STILL-OPEN**——C4 的纪律没有变成可执行门，后续锚点已重新落盘通过数并陈述过期动作。

就这三项而言，最小收官清单是封闭的两张卡：

1. **DEBT-17**：上述四类“先合法入库、后被拒/删除”fixture 经 direct endpoint 一次调用后 rows/fingerprints 全清。
2. **DEBT-18**：CURRENT_TASK 前 15 行修正；可变状态文档 lint 对 run 号、通过数、已完成未来动作全部先红后绿。

P1-01 无追加动作。其余四项的全部后续义务已封闭映射到 G4-2R、G4-3、G4-8A/B、INFRA-DEBT-01，不存在未指派残项。真实存量 Neo4j episode/快照的不合规数量为 **UNVERIFIABLE**；需要获准的只读生产 census 才能统计，但不影响本轮代码路径裁定。



---

## 附录：送审提示词全文

```markdown
你是本仓自有代码的**技术债收口裁判**。这是我方自己维护的开源学习工具仓库（Canvas Learning System，Tauri+React+FastAPI+Neo4j+LanceDB），任务是**工程质量债务的结案裁定**，不是安全攻防演练：我要你判断七条历史遗留的工程整改项现在是"已闭合(CLOSED)"还是"仍未闭合(STILL-OPEN)"，并给每条未闭合项指派后续负责的工作卡。

## 背景（为什么只有一轮）

2026-08-20 我方备好了第五轮审查包 `_bmad-output/审查/2026-08-20-P1-05d-五轮审查包-给Codex.md`，但从未送审。2026-08-24 用户裁定放弃重型多轮外审仪式，改走"小卡流水线 + 每卡单轮独立审查"。仪式形态被豁免，但**实质义务不豁免**——七条残项的 CLOSED/STILL-OPEN 台账与 owner 链必须补齐。本次即为那一轮终裁，之后不再有第二轮。

## 你要裁定的七条残项

| ID | 是什么 | 当时状态 |
|----|--------|----------|
| **P1-05** | vault 文件准入边界：索引器应只收 vault 内的 .md，实现上曾把解析到 vault 外的路径也读进来 | 四轮判 STILL-OPEN，C1 批 `c154a7f2` 已修，未复核 |
| **P1-01** | 快照 generation 不迁移：内容未变的旧快照永不重写，导致旧 schema/旧内容长期滞留 | 四轮判 STILL-OPEN，C2 批 `1683328c` 已修，未复核 |
| **P1-08** | 锚点文档（CURRENT_TASK 等）陈述失实：写死 CI run 号/通过数等会过期的值 | 四轮判 STILL-OPEN，C4 批 `1b7485b9` 已修，未复核 |
| **B4** | episode payload 的 node_id 准入、provenance 字段、`session:` 命名空间隔离、快照完整性来源证明 | 用户裁定当时不修，独立成轮 |
| **TOCTOU** | `realpath` 判定与随后的 `open` 非原子，判定与打开之间存在窗口 | 我方在五轮包中"诚实登记为债务"，未修 |
| **P1-03** | 服务层四态贯穿：`ok/empty/degraded/unavailable` 要贯穿 MemoryService / CanvasRAGState / rag_service，故障不得静默降为空列表 | 当时未做 |
| **P1-04** | API/trace/UI 面四态：响应 schema 携带 status+degraded_reason，前端能区分"没有记忆"和"系统坏了" | 当时未做 |

## 送审后发生的事（你必须实查确认，不要采信我的转述）

1. **P1-03 可能已被 CARD-G4-2 覆盖**：commit `9960b146` "feat: 四态贯穿服务层 Memory/RAG"，已由 `d3dcb16c` 合并进主线。请实查 `backend/app/services/rag_service.py`、`backend/app/services/memory_service.py`、`backend/lib/agentic_rag/state.py`，判断 P1-03 的义务（三条读路径 search/history/suggestions + CanvasRAGState + 故障不降空列表）是**全部**闭合、**部分**闭合还是未闭合。部分闭合一律记 STILL-OPEN 并写清缺口。
2. **P1-04 的 owner 卡是 CARD-G4-3**，git log 中我未找到其提交。请实查 API schema（`backend/app/api/v1/endpoints/`、`backend/app/models/`）与前端消费面，确认是否仍 STILL-OPEN。
3. **P1-05 的修复代码现在在**：`backend/lib/agentic_rag/clients/lancedb_client.py:507`（`_resolves_outside_vault` 定义）、`:1657`、`:1974`（两处调用），`backend/app/services/vault_index_orchestrator.py:157`（`should_index`）、`:194-196`。请核对四轮反例是否真的关闭，以及 C 批修复本身有无引入新缺陷（五轮包 Q2 列的三个 strict 场景仍然有效：`should_index` 对不存在文件的 realpath 行为、`_resolves_outside_vault` 对 vault 根自身与相对路径的边角、扫描期就过 `should_index` 之后 reconcile 的删除检测是否受影响——曾入库的被拒文件旧行会不会永不清理）。
4. **P1-01 的修复代码现在在**：`backend/app/models/snapshot_v3.py`、`backend/app/services/board_manifest_service.py`，回归锁在 `backend/tests/regression/test_snapshot_v3_contract.py`、`backend/tests/regression/test_board_manifest_contracts.py`。
5. **B4 的 owner 卡已明确是 CARD-G4-8**（"B4 payload 准入与快照完整性"，wave 3，deps: G4-5 + DEBT-11，尚未开工）。请裁定这个归属是否恰当、是否需要拆分。
6. **TOCTOU 的归属未定**——这是本轮必须给出的裁定之一：它应归到某张 G4 卡（若归，指名哪张、为什么），还是应独立登记为一张新的 infra-debt 补卡（若是，给出卡的 what / 完成判据方向 / 预估工时 / wave）。请先实查该窗口在当前代码里是否仍然存在、实际影响面多大，再定归属。
7. **P1-08 的锚点文档**：`CURRENT_TASK.md`（若存在）与 `_bmad-output/` 下的状态文档。C4 立的纪律是"不落盘 CI run 号与通过数，改记定性事实 + 实查命令"。请抽查该纪律现在是否仍被遵守（后续批次有没有把过期数值又写回去）。

## 允许你读的范围（read-only sandbox）

工作目录 `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt`。重点读：上面点名的源码与测试文件、`_bmad-output/审查/2026-08-20-P1-05d-五轮审查包-给Codex.md`（原始送审包，含四轮反例与我方回执）、`_bmad-output/审查/2026-08-20-Codex复核P1-05b-九路独立验证与处置方案.md`、`_bmad-output/审查/2026-08-20-Codex四轮终裁-九路验证与C批次方案.md`、`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（卡片档案，用于 owner 映射）。可自由 `git log` / `git show` 查证 commit。

## 裁定纪律

- 每条结论必须落到 `文件:行号` 或 `commit SHA`。**判 CLOSED 必须给出你实查到的闭合证据**，不接受"我方声称已修"作为证据。
- 判 STILL-OPEN 必须给可复现的失败场景（输入 → 观测值），不要只写"看起来不完整"。
- 若某条的验收绿灯（测试通过）与你的判断冲突，解释那个绿灯为什么是假的（例如测试没调真实入口、fixture 让断言恒真）。
- **部分闭合一律记 STILL-OPEN**，并在证据栏写明"已闭合的半边"与"仍缺的半边"。
- 若你无法在 read-only 下证实某条，明确写 `UNVERIFIABLE` + 需要什么才能证实，**不要猜**。

## 交付物（严格按此结构）

### 1. 七项裁定表
| ID | 裁定 | 证据（文件:行号 / commit） | 若 STILL-OPEN：可复现失败场景 |

### 2. owner 映射表
每条 STILL-OPEN 项 → owner 卡 ID。已知候选：B4→G4-8、P1-03→G4-2、P1-04→G4-3。若某条无现成卡可归，明确写"需补卡"并给出卡的 what / 完成判据方向 / 预估工时 / wave 建议。TOCTOU 的归属裁定必须在此给出。

### 3. C 批修复引入的新缺陷清单
若无，写明你尝试构造反例的路径与为什么构造失败。

### 4. 收官判词
P1-05 / P1-01 / P1-08 三项各给一句终裁。若你认为仍不能收官，给出**封闭可枚举**的最小收官清单（我们只剩这一轮，清单必须有限且每条可验收）。
```
