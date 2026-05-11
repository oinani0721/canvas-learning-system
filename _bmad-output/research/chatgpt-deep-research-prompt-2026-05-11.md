# Tech Decision: Canvas Learning System v1.5 全链路对抗性审查 (2026-05-11)

> 复制下面 `~~~~~~` 整段给 ChatGPT Deep Research

~~~~~~
# Canvas Learning System Multi-Vault / RAG / Skill Architecture Adversarial Review

## Project Context

Repository: github.com/oinani0721/canvas-learning-system
Branch: `worktree-feature-obsidian-hybrid-dev`
Architecture: **Obsidian Hybrid** (Obsidian + Claudian sidebar + FastAPI backend + LanceDB + Neo4j + Graphiti + MCP)

**Round-22 fork DeepTutor decision was ABANDONED on 2026-05-08** in favor of continuing Obsidian Hybrid (based on Lost in Middle / Power of Noise / Context Rot academic evidence + Karpathy LLM Wiki framework). All deliverables described below assume Obsidian Hybrid as the permanent architecture.

## What I Need From You (5 Adversarial Tasks)

### Task 1: Validate v1.5 Skill Architecture Pattern

I designed **8 reusable HARD constraint patterns** in `study-question` skill v1.5 + ported 5 to `chat-with-context` v2.0:

1. **HARD-0 三态路径自检** (Path A naked / B plugin full / C hook light)
2. **HARD-11 ≥5 独立 file Read** (skip 同 file 不同 section 凑数)
3. **HARD-15 5 阶段进度透明化 + 开场首行强制**
4. **HARD-16 末尾必 dump supplementary + dedup + score<0.2 ⚠️ 低相关降权**
5. **HARD-17 跨 lecture Grep 平行结构搜索**
6. **HARD-18 路径 A/C MCP 自救** (search_notes 反向拉 backend)
7. **HARD-19 RAGAS-lite 量化自检** (Faithfulness/ContextPrecision/矛盾点 1 行)
8. **HARD-20 mastery 颜色阈值固定** (🟢≥0.7/🟡/🔴/⚪)

**Question**: 这 8 个模式是否真的"业界领先"还是过度工程?
- 对比 Perplexity Deep Research / NotebookLM / Mistral Le Chat / Khanmigo 的输出特征
- 哪些 HARD 是 educational vertical 真创新?
- 哪些是 reinventing wheel?
- 哪些跟 Anthropic Claude Code skill 设计哲学冲突?

特别注意:
- HARD-15 "首行强制 + 5 阶段全显" 是不是过度约束 LLM 自由?
- HARD-19 RAGAS-lite 在单次 query 内输出 Faithfulness 数字，业界是否有先例?
- HARD-16 dedup + 低相关降权 vs Perplexity "100-300 sources 全列" 哪个更对?

### Task 2: Validate Multi-Vault Phase B0/B1/B2 设计

当前多 vault 状态：
- **Phase A0.5** (commit ecf16f2): hook 鉴权 + Graphiti 规范 + taint scan — done
- **Phase B0** (今天 commit a4c1d95): 中文 sanitize + yaml v2 schema + plugin onboarding modal — done (35% → 95% ready)
- **Phase B1** (P1, 8-12h): per-vault config 配置加载 — pending
- **Phase B2** (P2, 6-10h): 请求级 vault 绑定 (LanceDBClient 显式 vault_id) — pending

并发隔离测试 (asyncio.gather 2 vault 跑 ContextVar) 已 8 测试覆盖 (commit 460377c)。

**Question**:
- Multi-vault 设计 vs Obsidian 官方 "Multi-vault" 范式 (1 instance = 1 vault) 对比
- vs Logseq workspace switching / Notion teamspaces 多租户隔离设计
- 请求级 vault 绑定走 ContextVar 是否真的足够? (vs full multi-tenant DB schema)
- `vault:<vault_id>:<subject>:<canvas>` group_id 命名规约的可扩展性 (用户加到 50 vault 时是否仍 work)

### Task 3: Validate Backend RAG 修复链路

**RAG-P0 修复** (commit c017269):
- A1 doc_type 字段写入 LanceDB schema (frontmatter.type 直读)
- A2 source-aware SQL where 过滤
- A3 默认排除 whiteboard (3 个入口: VaultNotesService + tool_executor + supplementary_search)
- A4 whiteboard 切片差异化 (`_strip_whiteboard_boilerplate` 剥离 86% boilerplate)
- A5 schema drift auto-detect (drop & recreate)

**v1.5 Schema Guard 修复** (commit cd9d0f7):
- `_search_internal` 加 schema guard: 列缺失时 drop where clause (不抛 LanceError)
- `note_search_tools.py` fallback raw LanceDB API (bypass LangGraph 5-channel routing bug)
- 用 env `LANCEDB_DATA_PATH` 非 config 相对路径
- 实测: search_notes 0 → 10 召回

**Known Issues** (deferred):
- LangGraph `fan_out_retrieval` conditional_edges 缺 path_map → 5 路并发实际未执行
- Ollama base_url `localhost:11434` (应为 `host.docker.internal:11434`) → query rewrite 失败 fallback
- HTTP `/index/vault?force_rebuild` endpoint singleton 持有旧 fingerprints (绕过办法: docker exec 直接调)

**Question**:
- 这 3 个 deferred bug 哪个最严重? 各自的真实影响?
- LangGraph 5 路融合管道 vs raw LanceDB API fallback — 前者修复 ROI 是否真值 8h?
- schema guard "missing column → drop clause" 设计是否过度宽容?
- 业界 RAG 框架 (LangChain / LlamaIndex / Haystack) 如何处理 schema mismatch?

### Task 4: Validate ChatGPT 对照 Round-22 决策

2026-05-08 用户基于 4 学术证据弃用 fork DeepTutor:
- Liu 2023 (Lost in Middle)
- Cuconasu SIGIR 2024 (Power of Noise)
- Chroma 2025 (Context Rot)
- Karpathy LLM Wiki framework

回归 Obsidian Hybrid，理由："wiki 范式只承载 final state，缺 4 维度 (when/where/why/how-sure)"。

**Question**:
- 这 4 学术证据是否真支持"内容越多幻觉越严重"结论? 还是被过度引用?
- Karpathy LLM Wiki 在 60KB vault scale 是否真比 RAG 强? 有 quantitative benchmark 吗?
- "wiki 范式缺 4 维度" 这个 framework 来源是哪几个学术工作? (Concept Map / Spatial Hypertext / TextNet / Tree-of-Thoughts?)
- 是否存在 case where fork DeepTutor 反而更优 (例如 vault 增长到 1MB+ token 时)?

### Task 5: Story 2.9 Phase 2 实施方案审查

**当前未实施** (deferred to next session):

Story 2.9 6 个 AC:
- AC #1: Query-Aware Rerank (~2h)
- AC #2: Hub Penalty + Degree Scoring (~2h)
- AC #3: Path Trace (~1h)
- AC #4: Backlink + Heading + Alias 扩展 (~3h)
- AC #5: Relationship Evidence (~1.5h)
- AC #6: Plugin Timeout 降级 (~0.5h)

总工时 10h，用户已确认下一轮实施。

**Question**:
- 6 个 AC 实施顺序应该是什么? 哪 2 个最高 ROI?
- AC #2 hub penalty 公式 `log(degree / median_degree + 1)` 是否真合理? 业界有 PageRank-aware rerank 先例吗?
- AC #4 Backlink 扩展 vs Obsidian metadataCache.resolvedLinks 已有数据，是否重复造轮子?
- AC #6 plugin timeout 降级到 node-chat 路径，是否反而让用户混淆 (两个 skill 输出差异)?

## Constraints

- macOS M-series 本地 + 5s hook 预算 (chat-with-context) / 30-45s 显式深度 (study-question)
- bge-m3 embedding 锁定 (1024d)
- Apache-2.0 / MIT 兼容
- 不 fork Claudian (已尝试 fork DeepTutor 失败)
- 5 个 skill 共存: chat-with-context / node-chat / ai-linked-doc / configure-whiteboard / study-question

## Files Reference

读以下文件原文 (Tier 0):

- `_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md` (645 行)
- `_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md` (1067 行)
- `_bmad-output/research/round-22-pivot-to-obsidian-hybrid-2026-05-08.md` (弃用决策)
- `canvas-vault/.claude/skills/study-question/SKILL.md` v1.5 (439 行)
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md` v2.0 (228 行)
- `canvas-vault/.claude/mcp.json` (_claudian.servers 双命名空间)
- `_bmad-output/implementation-artifacts/epic-2/2-9-rag-rerank-and-evidence.md` (Story 2.9 6 AC 完整 spec)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (项目级 Story 状态)

## Recent Commits (chronological)

```
a4c1d95 feat(round-23): b0.3 plugin onboarding modal + chat-with-context v2.0
cd9d0f7 feat(study-question): v1.5 + backend schema guard + raw lancedb fallback + 3 uat
460377c fix(multi-vault-p0-1): mv1 vault_id 必填 + contextvar + mv2 plugin payload + mv3 8 tests
f3c002a feat(study-question-p0): sq1 skill.md + sq2 cmd+shift+q + sq3 mode=deep + sq4 8 tests
c017269 chore(auto-sync): 6 files, metadata.py (RAG-P0 A1-A5)
```

## Output Format

请按以下 5 节回答，每节 200-400 词:

1. **Task 1 verdict**: Skill 8 HARD 模式是否业界领先? 哪些过度工程?
2. **Task 2 verdict**: Multi-vault 设计是否可扩展到 50+ vault? Concurrency 隔离是否够?
3. **Task 3 verdict**: 3 个 deferred bug 的严重度排序 + LangGraph 修复 ROI 评估
4. **Task 4 verdict**: Round-22 弃用决策的学术证据是否被过度引用? 反例 case?
5. **Task 5 verdict**: Story 2.9 Phase 2 6 AC 实施顺序 + 最高 ROI 2 个 AC

每节末尾给 **最盲点** (一段 100 词，你认为我可能没看到的最大风险或机会)。
~~~~~~

---

## 使用方法

1. 复制上面 `~~~~~~` 之间的整段 (含 ~~~~~~ 自身)
2. 打开 ChatGPT (推荐 GPT-4 / GPT-4o + Deep Research 模式)
3. 粘贴对话框运行
4. 把 ChatGPT 5 节 verdict 复制回 Canvas (新建 `_bmad-output/research/chatgpt-review-response-2026-05-11.md`)
5. Claude 读取 ChatGPT 反馈做 correct-course

## 预期 ChatGPT 反馈类型

ChatGPT Deep Research 应该会:
- 引用 5-10 篇相关论文 (RAG / Skill design / multi-tenant DB)
- 跟 Perplexity / NotebookLM / Mistral 做产品对比
- 找出 2-3 个我们没考虑的 edge case
- 评估每个 Task 的"最大盲点"

---

**Generated**: 2026-05-11
**Trace**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Session 战果**: 5 commits (c017269 / f3c002a / 460377c / cd9d0f7 / a4c1d95) + 3 UAT 验收单 + 6 SKILL.md 版本迭代
