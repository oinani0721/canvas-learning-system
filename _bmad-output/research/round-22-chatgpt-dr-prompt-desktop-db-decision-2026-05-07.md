---
report_id: "round-22-chatgpt-dr-prompt-desktop-db-decision"
report_type: "external-research-prompt"
date: "2026-05-07"
purpose: "ChatGPT Deep Research 提示词 — Epic-11 桌面化数据库选型决策"
target_consumer: "ChatGPT GPT-5 Pro / o4 / Deep Research mode (external)"
related_epics: ["epic-11"]
related_stories: ["11.1", "11.2", "11.3", "11.4"]
related_decisions: ["D17 (Round-22 fork)", "D18 (Desktop app)"]
related_specs:
  - "_bmad-output/implementation-artifacts/epic-11/_README.md"
  - "_bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md"
  - "_bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md"
status: "ready-to-send"
expected_dr_duration: "10-30 minutes"
expected_word_count: "1500-3000 words"
---

# ChatGPT Deep Research 提示词 — Epic-11 桌面化数据库选型决策

> **作者**：Claude Opus 4.7（Canvas + DeepTutor 集成 Round-22 Day 2）
>
> **触发原因**：BMAD R4 升级触发条件全部命中 — (a) 5 内部 Explore agent 已穷尽社区先例但仍无确定胜方；(b) 两个对立方案各有论据（Docker 简单但门槛 / Embedded 用户体验好但迁移成本未知）；(c) 决策影响 Epic-11 全部 4 Story + Epic-10 后续路径
>
> **决策性质**：Tech Architecture Decision，影响 ~80 person-hours

---

## 1. 文档用途

本文档是给 **ChatGPT Deep Research** 调研 Epic-11 数据库桌面化决策的完整提示词包。
DR 报告回流后保存到 `_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md`，整合进 Story 11.2 spec correct-course。

## 2. 使用流程（用户操作清单）

| 步骤 | 操作 | 预期 |
|---|---|---|
| 1 | 确认 `oinani0721/canvas-learning-system` 仓库 visibility（[GitHub Settings](https://github.com/oinani0721/canvas-learning-system/settings)）| Public / Private 两条不同路径 |
| 2 | 如 Private：临时改 Public OR 用备选方案（§5）| 让 DR 能读关键文件 |
| 3 | 在 ChatGPT 选 GPT-5 Pro / o4 + Deep Research 模式 | 启动深度调研能力 |
| 4 | 复制 §3 Pre-flight 1 prompt 给 ChatGPT 跑（30 秒） | 确认仓库 fetch 通 |
| 5 | 复制 §4 主 Prompt 给 ChatGPT 跑（10-30 分钟） | DR 报告产出 |
| 6 | 把 DR 报告 paste 给 Claude（或保存到指定路径）| Claude 整合到 Story 11.2 spec correct-course |

## 3. Pre-flight 1: 确认仓库可访问

**复制以下整段给 ChatGPT，确认 fetch 工具可用**：

```
Before deep research, please confirm you can access these GitHub raw URLs:
1. https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-deeptutor-canvas-mvp/_bmad-output/implementation-artifacts/epic-11/_README.md
2. https://raw.githubusercontent.com/oinani0721/DeepTutor/mvp-canvas-integration/docker-compose.canvas.yml
3. https://raw.githubusercontent.com/HKUDS/DeepTutor/main/README.md

If any returns 404 or auth error, tell me which one — I may need to make the repo public or provide an alternative.
```

**预期回应**：
- 全部 200 OK → 跳到 §4 主 Prompt
- canvas-learning-system 401 → 用 §5 Private fallback
- DeepTutor / HKUDS 失败 → 检查我提供的 URL 是否正确

---

## 4. 主 Prompt（Pre-flight 通过后跑）

**复制以下整段（含三个反引号包裹的 markdown 块）给 ChatGPT**：

````markdown
# Deep Research: Desktop Database Architecture for Electron-bundled AI Learning App

## GitHub Repository Access (PUBLIC repos, fetch directly)

| Repo | URL | Branch | Role |
|---|---|---|---|
| **canvas-learning-system** | https://github.com/oinani0721/canvas-learning-system | `worktree-feature-deeptutor-canvas-mvp` | Domain backend (FastAPI + Neo4j + LanceDB + Graphiti). All 5 core features implemented here. |
| **DeepTutor fork** | https://github.com/oinani0721/DeepTutor | `mvp-canvas-integration` | UI shell (Next.js + FastAPI proxy). Forked from upstream. |
| **DeepTutor upstream** | https://github.com/HKUDS/DeepTutor | `main` | Reference for upstream architecture (do not edit). |
| **Graphiti library** | https://github.com/getzep/graphiti | `main` | Third-party temporal KG library, Neo4j-coupled. |

**Raw fetch URL pattern**: `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file_path>`

## Files to READ FIRST (priority evidence — read these before searching elsewhere)

### Tier 1: Cypher coupling proof (this is the core "Neo4j lock-in" question)

```
canvas-learning-system / worktree-feature-deeptutor-canvas-mvp /
├── backend/app/utils/cypher_helpers.py                ← Strict group_id WHERE injection
├── backend/app/core/subject_config.py                  ← build_vault_group_id(), Graphiti namespacing
├── backend/app/services/vault_switch_coordinator.py    ← Story 1.8 hot-swap state machine
├── backend/app/api/v1/endpoints/vault.py               ← POST /vault/switch endpoint
├── backend/app/services/wikilink_graph_service.py      ← obsidiantools NetworkX → Neo4j
├── backend/app/services/episode_worker.py              ← Graphiti episode enqueue (group_id mandatory)
├── backend/app/services/memory_service.py              ← record_learning_event() Graphiti binding
├── backend/app/services/mastery_engine.py              ← BKT + FSRS, state in Neo4j
├── backend/app/services/autoscore.py                   ← AutoSCORE 4-dim grading
└── backend/app/services/exam_service.py                ← ACP 5-layer prompt assembly
```

For each file: identify Cypher patterns used (especially APOC procedures, MATCH-WITH chains, Graphiti API calls). Estimate migration difficulty per file.

### Tier 2: LanceDB + multi-vault isolation (already-built foundation, do NOT re-design)

```
canvas-learning-system /
├── backend/lib/agentic_rag/clients/lancedb_client.py   ← resolve_table_name(vault_id_) prefix
├── backend/tests/unit/test_lancedb_vault_isolation.py  ← Story 1.9 test coverage
├── backend/tests/unit/test_cypher_helpers.py           ← Story 2.5.Y D16 hardening tests
└── backend/tests/unit/test_subject_config_vault.py     ← vault_id naming rules
```

### Tier 3: Decision context (Round-22 research that locked current architecture)

```
canvas-learning-system /
├── _bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md
├── _bmad-output/research/round-22-deeptutor-deep-explore-2026-05-06.md
├── _bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md
└── _bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md
```

### Tier 4: Current Epic specs (this is what your recommendation will reshape)

```
canvas-learning-system /
├── _bmad-output/implementation-artifacts/epic-10/_README.md         ← 10-day MVP, Day 2 done
├── _bmad-output/implementation-artifacts/epic-11/_README.md         ← Desktop app, target after Day 10
├── _bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md  ← Docker supervisor C+ design
├── _bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md ← macOS Sandbox + electron-builder
└── _bmad-output/验收单/Story-10.3-day2-cleanup-vault-mount.md       ← Day 2 already shipped (vault mount working)
```

### Tier 5: Docker compose orchestration (current Web mode reference)

```
canvas-learning-system / docker-compose.yml          ← Canvas backend + Neo4j + LanceDB
DeepTutor fork / docker-compose.canvas.yml           ← Multi-service compose (DeepTutor + Canvas)
DeepTutor fork / docker-compose.yml                  ← DeepTutor base
DeepTutor fork / Dockerfile                          ← Production target (Next.js standalone)
```

## Files to NOT bother reading (waste of quota)

- `canvas-learning-system / _bmad-archive/**` — Archived obsolete specs (Tauri v0 era, ZOMBIE scripts)
- `canvas-learning-system / .claude/worktrees/feature-obsidian-hybrid-dev/**` — Old worktree, superseded by feature-deeptutor-canvas-mvp
- `canvas-learning-system / docs/known-gotchas.md` — Web-mode bug history, not relevant to desktop decision
- `canvas-learning-system / frontend/obsidian-plugin/**` — Obsidian plugin path was abandoned in Round-22 (D17 fork decision)
- `canvas-learning-system / canvas-vault/**` — User's actual notes content, not source code
- `DeepTutor / docs/**` — Marketing docs, not architecture
- Any `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, `build/`

## Project Context

### Mission
Canvas Learning System integrates with DeepTutor (forked from HKUDS/DeepTutor v1.3.7). Currently Day 2 of 10-day MVP sprint. Post-MVP plans: package as Electron desktop app (Epic-11, ~80h, Day 11-22).

### 5 Core Features (locked, all currently depend on Neo4j)
1. **OriginWhiteboard + wikilinks** — NetworkX from obsidiantools, persisted to Neo4j
2. **ExamWhiteboard + AutoSCORE** — 4-dim grading, mastery in Neo4j
3. **MasteryDashboard (BKT + FSRS)** — Bayesian Knowledge Tracing + spaced repetition, state in Neo4j
4. **ErrorCandidate (4 error types)** — Stored as Graphiti episodes (Neo4j-backed via getzep/graphiti)
5. **Graphiti episodic memory** — Zep AI's library, requires Neo4j Bolt protocol

### NEG-2 User Sovereignty (hard constraint)
- ❌ Reject "upload to internal storage" pattern (like AnythingLLM upload-and-embed)
- ✅ Must: user picks local folder → app reads directly → no copy/sync
- ✅ Multi-vault: hot-swap between subject vaults (CS61B / Linear Algebra / Math)

## The Decision

Choose database stack for **Electron desktop app (Epic-11)**:
- Preserves Canvas backend's Cypher queries (count them yourself by reading Tier 1 files)
- Preserves Graphiti library compatibility (Neo4j Bolt protocol)
- Minimizes user install friction (target: NO Docker Desktop dependency)
- Total .app size budget: <500 MB
- First-launch cold start: <10s
- Works fully offline (NEG-2)

### Options to evaluate

**A: Docker Compose Supervisor (current Story 11.2 spec)** — User installs Docker Desktop (~600 MB), Electron supervises `docker compose up -d`. See `epic-11/11-2-ipc-bridge-fastapi-subprocess.md` for full design.

**B: Embedded Database Replacement** — Replace Neo4j with embedded graph DB, bundle FastAPI via PyInstaller (~80-150 MB) inside Electron.
- B1 Kuzu (kuzudb/kuzu)
- B2 Memgraph (subprocess, ~50 MB)
- B3 SQLite + recursive CTEs
- B4 Neo4j Embedded JVM (200+ MB JRE)
- B5 DuckDB / ChromaDB (no graph traversal)

**C: Neo4j Aura cloud** — Free tier 200k nodes. Violates NEG-2 (offline req).

**D: Hybrid (Docker if available, embedded fallback)** — 2 code paths, 2x QA.

## What we already know (from internal research, do not redo)

1. ✅ Canvas backend has mature multi-vault isolation: `build_vault_group_id()` + `cypher_with_group_filter()` + `LanceDBClient.resolve_table_name()` + `VaultSwitchCoordinator` + Story 2.5.Y D16 hardening
2. ✅ macOS Docker Desktop has bind mount inode-stale issue (moby#6011) — required container restart in Story 10.3
3. ✅ AnythingLLM Desktop is upload-and-embed (verified via Mintplex-Labs/anything-llm `server/models/documents.js` + Issues #2235/#3285) — NOT a folder-direct-read pattern. So D18 "AnythingLLM mode" only means Electron + electron-builder + autoupdate engineering practice, NOT vault data flow
4. ✅ Electron + PyInstaller bundling: ~80-150 MB for FastAPI + deps, ~3s first-start
5. ⚠️ Kuzu Cypher reportedly ~95% compatible with Neo4j — need YOUR verification reading our actual Cypher patterns

## Desired Output

### 1. Recommendation with reasoning (800-1500 words)
- Which option (A / B1-B5 / D) — must be one of these, no new options unless you justify
- Quantitative comparison: install size MB, cold start ms, migration person-hours, risk score
- Counter-arguments to your recommendation
- Confidence level (high / medium / low)

### 2. Implementation sketch (500 words)
- Migration roadmap with concrete steps + person-hour estimates
- Specific code/config sketches (Kuzu schema, entitlements.plist, dockerfile, etc.)
- Test strategy verifying 5 core features still work post-migration

### 3. Risk + Fallback (300 words)
- Top 3 risks + mitigations
- Fallback plan if recommendation fails
- Decision review trigger conditions

### 4. Industry precedent (3-5 examples, recent 2024-2025)
Look at: **Reor**, **Khoj**, **Recall**, **Cherry Studio**, **Smart Connections**, **Continue.dev Desktop**, **LM Studio**, **Open WebUI desktop wrapper**, **Logseq**, **Obsidian + AI plugins**, plus any others you find. For each: what DB stack, what trade-off, what they sacrificed.

### 5. CRITICAL question — direct yes/no answer required

**"After reading the Tier 1 files in `canvas-learning-system` (cypher_helpers.py, vault_switch_coordinator.py, episode_worker.py, memory_service.py, mastery_engine.py, exam_service.py, autoscore.py, wikilink_graph_service.py), is there a way to ship Canvas Learning System as a desktop app WITHOUT requiring users to install Docker Desktop, while preserving all 5 core features without rewriting the Cypher queries that depend on Neo4j-specific features (APOC, complex MATCH-WITH chains, Graphiti library's Neo4j-Bolt coupling)?"**

- If yes — outline the path with effort estimate (counting actual queries you found)
- If no — quantify: how much rewrite is realistic in 5-10 person-days? Which queries are showstoppers?

### 6. Specific data to extract from our codebase
After reading the files, please report:
- Exact count of Cypher queries in `cypher_helpers.py` and dependent services
- List of APOC procedures used (if any)
- Graphiti library API calls (count + which methods)
- Bolt-specific behaviors that would not survive a Bolt-emulating embedded DB (e.g., Memgraph)

## Constraints
- 10-day MVP currently Day 2 done (Story 10.3 shipped). Epic-11 starts Day 11+. ~9 days to finalize architecture.
- Solo developer + Claude Code assistance, no team
- Target user: non-technical learners (high school / undergrad). Cannot expect "Docker container" understanding
- Platforms: Mac priority, Windows secondary, Linux nice-to-have
- Cannot rewrite Graphiti library (third-party dep, deep Neo4j coupling)
- Cannot break Web mode (Web users continue with Docker Compose)

## Output format
- Use markdown headings for each numbered section
- Cite file paths with line ranges when discussing code: e.g., `cypher_helpers.py:20-96`
- Cite external sources with full URLs
- Give numbers wherever possible (don't say "fast", say "<3s cold start" or "300 ops/sec")
- This decision affects 4 user stories (Epic-11.1 to 11.4) and ~80 person-hours of work — be thorough.
````

---

## 5. 备选方案：仓库 Private 时的处理

如果 `oinani0721/canvas-learning-system` 仓库无法 Public，三个备选路径：

### 5.1 选项 X：用 backup 仓库（如其 Public）

把 §4 主 Prompt 中所有 `canvas-learning-system` 的 GitHub URL 替换为 `canvas-learning-system-backup`：

```diff
- https://github.com/oinani0721/canvas-learning-system
+ https://github.com/oinani0721/canvas-learning-system-backup
```

### 5.2 选项 Y：手动上传 Tier 1 + Tier 4 文件

使用 ChatGPT 的 "Attach files" 功能，上传以下 14 个文件：

**Tier 1（10 个 Cypher 耦合证据文件）**：
1. `backend/app/utils/cypher_helpers.py`
2. `backend/app/core/subject_config.py`
3. `backend/app/services/vault_switch_coordinator.py`
4. `backend/app/api/v1/endpoints/vault.py`
5. `backend/app/services/wikilink_graph_service.py`
6. `backend/app/services/episode_worker.py`
7. `backend/app/services/memory_service.py`
8. `backend/app/services/mastery_engine.py`
9. `backend/app/services/autoscore.py`
10. `backend/app/services/exam_service.py`

**Tier 4（4 个 spec 文件）**：
11. `_bmad-output/implementation-artifacts/epic-10/_README.md`
12. `_bmad-output/implementation-artifacts/epic-11/_README.md`
13. `_bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md`
14. `_bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md`

在主 Prompt 顶部加入：

```
Files to read are attached (uploaded). Skip the "Files to READ FIRST"
GitHub fetch step — use the attached files instead.
DeepTutor fork (oinani0721/DeepTutor) and HKUDS/DeepTutor are public,
fetch via GitHub raw URLs for those.
Tier 2/3/5 files: skip (focus on attached Tier 1 + 4).
```

### 5.3 选项 Z：手动 paste 全文（不推荐）

如果文件太大无法上传，用 Claude 帮你提取每个文件关键段落（Cypher 调用 / Graphiti API 调用），paste 进 ChatGPT 对话开头作为 evidence dump。

---

## 6. DR 报告回流路径

收到 ChatGPT 的 Deep Research 报告后：

1. **保存原文**：另存到 `_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md`（使用 round-22 系列命名）
2. **提取关键决策**：Claude 整合到 `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md` 或新建 `D19-desktop-db-stack-2026-05-07.md`
3. **修订 Story 11.2 spec**：根据 DR 推荐结论 correct-course
   - 若选 A (Docker)：保持当前 spec
   - 若选 B (Embedded)：重写 Story 11.2 + 新建 Story 11.2.5 (Cypher migration)
   - 若选 D (Hybrid)：拆 Story 11.2 + 11.2.5 双路径
4. **更新 sprint-status.yaml**：epic-11 status 决策日期 + DR ref

---

## 7. 这次调研的 BMAD 升级触发条件确认

按 BMAD scoped CLAUDE.md "ChatGPT Deep Research 升级触发条件"：

- ✅ **触发条件 1：Explore agent 找不到社区先例** — 5 内部 agent 调研后仍未确定胜方（Kuzu Cypher 兼容度、Memgraph 嵌入、Graphiti 替代库均无明确结论）
- ✅ **触发条件 2：两个对立技术方案各有论据，无明显胜方** — Docker (低迁移成本但用户门槛) vs Embedded (用户体验好但 ~50 Cypher 迁移未量化)
- ✅ **触发条件 3：决策影响后续 5+ Story** — Epic-11.1/11.2/11.3/11.4 + Epic-10 后续 vault 多 vault Stage 1-3 衔接

三条全命中 → 升级合规。

---

## 8. 元信息

- **作者**：Claude Opus 4.7（1M context）
- **生成时间**：2026-05-07
- **生成上下文**：Round-22 Day 2 收官 + Epic-11 spec 修订 commit `db3040b` 后
- **下游消费者**：ChatGPT GPT-5 Pro / o4 + Deep Research mode（external）
- **预期 DR 时长**：10-30 分钟（取决于 fetch + 调研深度）
- **预期产出**：1500-3000 字调研报告 + 行业先例引用 + 量化迁移成本估算

---

*本文档是 ChatGPT Deep Research 升级流程产物。所有 DR 调研结论必须在 Round-22 后续报告中可追溯到本提示词。*
