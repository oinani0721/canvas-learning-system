# CARD-G4-16 — doc_type 族接线普查与裁定报告

> **批次**: BATCH-2026-08-28-第五批 / CARD-G4-16（2h · wave 1 · 防暗坑）
> **锚点**: 计划书 L69（§2.3 STILL-OPEN 前半「doc_type 整族未接线」）——G4-12 已收该行后半"指标名实不符"，本卡收 doc_type 消费链本体
> **代码基线**: worktree `card/s5-census` @ **`37387a86`**（全部 file:line 以此 SHA 为准；config.py 同时在他卡编辑面上，行号会漂移——复核请先 checkout 此 SHA）
> **证据包**: `_bmad-output/审查/G4-16-evidence/`（146 行 grep 清单、落点测试 before/after、live 分布实测）
> **执行日期**: 2026-08-28

---

## §1 枚举口径与总量

`git grep -n "doc_type" 37387a86 -- "backend/*.py"` → **18 文件 146 行**（逐行清单：证据包 `doc_type-146-occurrences@37387a86.txt`；**必须用 pinned git grep 复核**——工作树裸 `grep -rn backend` 会扫入 `backend/.venv` 得 30 文件 198 行，Codex round-1 MEDIUM-5）。与勘探预告完全一致。

**范围声明（Codex round-1 HIGH-4）**：本 census 的对象是 **backend/*.py 中 LanceDB `vault_notes` 行级 `doc_type` 字段**。仓库根 `scripts/migrate_story_frontmatter.py:60` 写 `doc_type: story`、`scripts/sync_links.py:58` 消费 story/epic——那是 **BMAD 文档 frontmatter 的同名异物命名空间**，不入 LanceDB、不与本字段互通，不在本卡值域表内（如实登记防混淆）。

**18 文件角色分布**（行数 = doc_type 出现行数）：

| 角色 | 文件 | 行数 |
|---|---|---|
| **写侧（唯一写入方）** | `lib/agentic_rag/clients/lancedb_client.py` | 69 |
| 生产消费·检索服务 | `app/services/supplementary_search_service.py` | 5 |
| 生产消费·检索器 | `lib/agentic_rag/retrievers/vault_notes_retriever.py` | 13 |
| 生产消费·隔离面 | `app/services/tool_executor.py` / `app/services/react_agent.py` / `lib/agentic_rag/agent_graph.py` | 3 / 2 / 1 |
| 生产消费·MCP | `app/mcp/tools/note_search_tools.py` | 2 |
| 注释引用（本卡修正对象） | `app/services/supplementary_reranker.py` | 1 |
| 配置/文档注释 | `app/config.py`（:48-50 双层防御注释）/ `app/api/v1/endpoints/metadata.py`（:569 docstring） | 2 / 1 |
| 回归裁判脚本 | `scripts/run_vault_retrieval_regression.py`（:134/:143 污染硬禁类型判定） | 3 |
| 测试契约（7 文件） | `test_rag_p0_doc_type_filter`(20) / `test_rag_stage2_chain_unify_contracts`(9) / `test_rag_stage2_chunk_contracts`(7) / `test_rag_stage2_t6_verification_contracts`(4) / `test_immutable_skip_dirs_contract`(2) / `test_rag_stage2_rerank_contracts`(1) / `test_rag_stage0_contracts`(1) | 44 |

**写入方论证（Codex round-1 MEDIUM-3/LOW-1 修订）**：`vault_notes` 表的**显式值生产者恰两处**，均在 `lancedb_client.py`——批量索引路径（:1773-1777 推导 → :1795 metadata + :1818 SQL 列）与单文件更新路径（:2058-2062 推导 → :2078 + :2101），两路共用同一推导规则：`frontmatter.type` **直通**（:2740 lower/strip，无白名单——`whiteboard` 即由此直通入库，:2767 只是消费该值做样板剥离，不是推断点）→ 检验白板推断 `exam_board`（:2756）→ 路径启发 `video_transcript`（`_is_video_transcript`）→ 默认 `"note"`。此外存在**通用 sink**：公共 `add_documents()`（:3615）可无校验透传调用方传入的任意 `doc_type`（含 Chroma 迁移脚本内嵌 metadata_json 路径）——静态未发现当前有第三方经此向 `vault_notes` 写第三种值，但"唯一"须限定为"两显式生产者 + 通用 sink 无校验"。多模态 image_ocr 写路径（:1279-1293）**不含 doc_type 字段**——读侧空串回退的真实来源之一。

## §2 live 分布实测（容器内只读）

`docker exec` 容器内 lancedb 只读扫描 `canvas_vault_vault_notes`（2203 行，2026-08-28）：

```
video_transcript 2001 (90.8%) | concept 117 | note 69 | whiteboard 16 | exam_board 0 | 空/自由值 0
```

## §3 消费链实测

- **排除过滤（真实消费主链）**：`exclude_doc_types=["whiteboard","exam_board"]` 于 react_agent:115/:124、tool_executor:112/:122、agent_graph:208、supplementary_search_service:834/:849 显式传入，vault_notes_retriever:82 为默认值——共 7 处显式 + 1 处默认，SQL `NOT IN` 落到 lancedb doc_type 列。**边界（Codex round-1 MEDIUM-4）**：该隔离只覆盖默认 Tier-1 路径——`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关闭）开启后 legacy tier-2 直查裸 `vault_notes` 无 doc_type WHERE（supplementary_search_service.py:863），"在库但检索不可见"仅在默认配置下成立（登记 FU-5）。这是检验白板信息隔离（Karpicke 主动回忆）的**读侧第二层防御**（第一层 = config.py 目录黑名单，:48-50 注释如实记录"验收单/_待处理 无 doc_type，单层防御"）。
- **正向过滤（休眠 API）**：`vault_notes_retriever` 的 `doc_type: List[str]` 参数（:100/:143/:191）生产调用 **0 处**（仅 test_rag_p0_doc_type_filter 锁 `_build_where_filters` 契约）——注释自述"未来出题链定向取材 opt-in"，属预留接口非死代码（测试在位防漂移）。
- **material dict 透传（Codex round-1 HIGH-1 修订）**：supplementary_search_service:975 读 `metadata.doc_type`（"" 回退）→ :1047 进 material dict。**生产消费方存在**：MCP `note_search_tools._material_to_item` 的 clean 分支把 `doc_type` 列入 signal_keys 透传进 `NoteResultItem.metadata` 对外输出（note_search_tools.py:289/:385；tainted 分支按契约剔除，test_rag_stage2_chain_unify_contracts:265 锁定）——是**纯透传**（无分支/加权逻辑），此前报告与注释称"0 生产读取方"过强，已修正。原 :1044-1045 注释声称"doc_type=按类型加权与断言用"仍为**名实不符**：加权实际按材料 `source_type` 在 `rerank()` 内 `weights.get` 完成（`get_type_weight` 仅测试调用，Codex round-1 MEDIUM-2 修订），与 doc_type 无关。
- **裁判消费**：run_vault_retrieval_regression:134/:143 以 doc_type ∈ 硬禁集（whiteboard/exam_board 类）判定检索污染——回归门真实消费方。

## §4 六取值逐个裁定（接线 / 死值）

| # | 取值 | 写侧 | live 行数 | 读侧消费 | **裁定** |
|---|---|---|---|---|---|
| 1 | `note` | 默认值 + frontmatter（:1773/:2058） | 69 | 不在排除集 → 可检索；测试契约锁定 | **接线** |
| 2 | `video_transcript` | 路径启发（:1774/:2059） | 2001 | 同上；且与并行 source_type=video_transcript 一起驱动 rerank 权重 | **接线** |
| 3 | `whiteboard` | frontmatter `type: whiteboard` 直通（:2740；:2767 仅消费做样板剥离，LOW-1 修订） | 16 | exclude 集 7+1 处消费（隔离第二层）；默认 Tier-1 下在库但检索不可见 = 设计行为（Tier-2 flag 例外见 §3/FU-5） | **接线** |
| 4 | `exam_board` | 检验白板推断（:2756） | 0 | exclude 集同上。live 0 行原因（Codex round-1 HIGH-2 指出原归因不完整，本轮实测坐实）：exam-quick 考察文件写向**可索引**的 `节点/考察-*.md`（exam-quick.ts:39/:75，目录黑名单不拦）——live vault 实测该形态文件 **0 个**；`检验白板/` 目录唯一 1 个 md 则被目录黑名单拦截。0 行 = "无考察文件存在 + 黑名单拦检验白板目录"两因叠加，非纯黑名单 | **接线**（0 行原因已实测坐实，非死值） |
| 5 | `concept` | frontmatter `type: concept` 直通 | 117 | 入库真实 + MCP metadata 透传在位；但**无按 "concept" 特化分支的读侧**——自称消费方 `TYPE_WEIGHTS["concept"]` 实为 **source_type 键**，indexer 永不写 source_type="concept" → **直接 lookup 不可达**；concept 材料命中的权重键由**路径启发的 source_type 独立决定**（普通路径→note 1.0，/videos/ 下→video_transcript 0.75），与 doc_type 无关；聚合面 `get_filter_threshold()` 消费全表 values()（chat.py:428 生产调用），concept=1.0 非最小值、当前不影响阈值（Codex round-1 HIGH-3/MEDIUM-1 修订） | **值接线；权重键=直接 lookup 不可达、聚合可达但非决定项**（注释已修正保键；删键列 FU-1） |
| 6 | 空串/自由值 | image_ocr 路径缺字段 + frontmatter 任意小写串直通（:2740 无白名单；note_search_tools:276 注释自认无枚举校验） | 0 | 读侧 "" 回退（:975）后仅影响透传与 doc_type 过滤；**权重不受影响**——source_type 恒独立有值（自由值笔记 source_type=note→1.0；image_ocr 行 source_type=image_ocr→0.6，非 DEFAULT 0.5；Codex round-1 HIGH-3 修订） | **值域未闭合**（live 暂 0 行；白名单校验列 FU-3，口径依 G8-1） |

**grep 复核 0 未裁定残留**：146 行中除上表六值与字段名本身的出现外，无其他 doc_type 取值字面量（TYPE_WEIGHTS 的 lecture_notes/discussion 等 6 个 PRD 档位是 **source_type** 前向兼容键、注释已自述 forward-compat，不属 doc_type 值域；test fixture 的 "lecture"/"discussion" 仅锁 `_build_where_filters` SQL 拼接契约）。

## §5 ≤1h 轻量处置（本卡完成，注释-only，零行为改动）

1. `supplementary_reranker.py` `TYPE_WEIGHTS["concept"]`：原注释"派生概念节点 (doc_type=concept) → 用户手写, 最高"名实不符（该键按 source_type 匹配、直接 lookup 永不命中）。**保守方案：改注释保键**——终版注释（经 Codex round-1 修订）如实声明：直接 lookup 不可达（生产加权 = rerank() 内 weights.get，get_type_weight 仅测试调用）、doc_type=concept 笔记的 source_type 由路径启发独立决定（note 或 video_transcript）、聚合面 get_filter_threshold() 可达但 concept=1.0 当前非决定值；删键裁定列 FU-1。
2. `supplementary_search_service.py` :1044 区注释：删去"doc_type=按类型加权与断言用"的错误声明，终版（经 Codex round-1 修订）改为："doc_type 不参与加权（加权按 source_type 走权重表）；生产消费 = MCP note_search_tools 将 clean 材料 doc_type 透传进输出 metadata（纯透传无分支）；另有测试契约锁定 + 定向取材预留"。

## §6 落点测试 before/after（裁判判据）

两个落点测试文件 = `tests/unit/test_supplementary_reranker.py` + `tests/unit/test_supplementary_search_service.py`。

- **基线（动手前存档）**：**9 failed / 102 passed**（`G4-16-evidence/baseline-before-edits.txt`）——全部 9 条在 reranker 文件：TypeWeightsIndexerTransition×2 + TestFilterFloor×4 + TestFilterFloorTaintExclusion×3；search_service 文件 0 失败。勘探预告"约 10 个既有失败"，实测 9，偏差 1 条按实测为准。
- **处置后**：**9 failed / 102 passed**，FAILED 清单逐条 diff 为空 → **零新增失败 PASS**（`after-edits.txt`）。
- ruff check + format 两文件全过。
- **证据绑定补强（Codex round-1 MEDIUM-5）**：证据包新增 `test-run-metadata.txt`（精确 pytest 命令 / venv Python 版本 / HEAD sha / 失败节点集合 diff 说明——before/after 失败节点逐条相同，仅耗时行不同）。

**9 条既有失败根因方向**（登记入 FU-2，本卡不修）：测试仍按 2026-05-12 设计断言 `note→0.7 中档`（test :579 docstring 自述），而 RAG-S2 T2（2026-08-09）已把 note/concept 翻转为 1.0（权重方向"手写最高"）且 rerank_score 计算随之变化 → FilterFloor 族的 0.42 过滤阈值场景不再触发。属"生产权重翻转未同步测试"的陈债（Codex 独立溯源到翻转 commit `fcd34953`，并确认 floor 用例修法应调输入使 floor 继续触发、不应放宽预期），与本卡注释修正无关（before/after 失败节点全等自证）。

## §7 follow-up 登记（超出本卡预算项，显式移交）

| # | 事项 | 建议归属 |
|---|---|---|
| FU-1 | `TYPE_WEIGHTS["concept"]` 删键：**非绝对死键**（get_filter_threshold 聚合消费全表 values()，chat.py:428）——删键前须断言阈值不漂移 + 补"concept 材料按 source_type 命中权重"回归断言 | 检索质量后续卡（与 FU-2 同修最经济） |
| FU-2 | 落点测试 9 条既有失败：按 RAG-S2 T2 翻转后的权重表重写断言（或裁定翻转错误回滚——需检索质量数据裁决，本卡无权代裁） | 检索质量后续卡 |
| FU-3 | doc_type 枚举白名单校验（写侧 :2740 frontmatter 直通 + note_search_tools 无枚举）：**枚举口径依 G8-1 raw/wiki/schema 角色台账定版后落地**，本卡不代 G8-1 冻结值域 | G8-1 及其后续 |
| FU-4 | image_ocr 写路径补 doc_type 字段（当前缺字段 → 读侧空串回退），随 FU-3 白名单一并定值 | 同 FU-3 |
| FU-5 | `ENABLE_LANCEDB_TIER2_FALLBACK`（默认关）开启后 tier-2 直查绕过 doc_type 排除（supplementary_search_service.py:863）——检验白板隔离在该配置下失效，需补 tier-2 侧 WHERE 或在 flag 文档标注隔离代价 | 隔离面后续卡（本卡铁律禁改隔离面，仅登记） |

## §8 G8-1 台账对齐条目（软依赖注记）

供 G8-1 收录：`doc_type` = LanceDB 行级**文档角色** schema 字段；权威值域现状 = {note, video_transcript, whiteboard, exam_board, concept} + 未闭合 frontmatter 直通面；写入方唯一（lancedb_client 双路径）；消费主链 = 检验白板隔离排除集 + 回归污染裁判；与 source_type（内容来源形态：note/video_transcript/image_ocr/neighbor_expansion）**字段职责与赋值链分离**（doc_type 主要来自 frontmatter 直通+推断、source_type 纯路径启发；二者共享 `_is_video_transcript` 路径启发但互不复制取值），G4-16 前的注释曾将二者混同（已修正）。命名与取值最终口径以 G8-1 台账为准。

## §9 Codex round-1 整改记录（FAIL → 全项整改）

Codex round-1 终裁 FAIL（0 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW），同时确认：两文件与 HEAD 的无属性 AST 完全相等（注释-only 铁律 PASS）、隔离面零改动 PASS、9 条既有失败根因归因 PASS（溯源 `fcd34953`）、pinned git grep 18/146 复算 PASS。逐条整改：

- **HIGH-1（遗漏 MCP 生产消费方）**：§3 与 supplementary_search_service 注释改为如实声明 note_search_tools:289/:385 透传消费；"0 生产读取方"表述撤回。
- **HIGH-2（exam_board live=0 归因）**：本轮补实测——live vault `节点/考察-*.md` 实存 0 个 + `检验白板/` 唯一 1 md 被黑名单拦截，两因叠加坐实（§4 行 4 重写，UNVERIFIED 消除）。
- **HIGH-3（六值表混同 doc_type/source_type）**：concept/空串/image_ocr 三处行为结论按 source_type 独立决定改写（§4 行 5/6 + reranker 注释重写）。
- **HIGH-4（根 scripts/ 命名空间）**：§1 增范围声明，BMAD frontmatter `doc_type: story` 同名异物如实登记。
- **MEDIUM-1（非绝对死键）**：get_filter_threshold 聚合可达入注释与 FU-1；裁定改"直接 lookup 不可达、聚合可达非决定项"。
- **MEDIUM-2（get_type_weight 调用链）**：注释与报告改为 rerank() 内 weights.get 为生产路径。
- **MEDIUM-3（通用 sink）**：§1 写入方论证改"两显式生产者 + add_documents 无校验 sink"。
- **MEDIUM-4（Tier-2 旁路）**：§3 边界声明 + FU-5 登记（本卡铁律禁改隔离面）。
- **MEDIUM-5（可复验性）**：枚举命令改 pinned git grep（工作树裸 grep 会扫 .venv 得 30/198 的陷阱已写明）；证据包补 test-run-metadata.txt。
- **LOW-1（whiteboard 来源行号）**：:2740 直通为写侧来源，:2767 为消费点（§1/§4 修正）。

整改后复跑落点测试：9 failed / 102 passed，失败节点与基线逐条相同——注释修订不改任何行为。
