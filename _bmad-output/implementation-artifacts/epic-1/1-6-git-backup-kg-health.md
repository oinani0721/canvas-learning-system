---
story_id: "1.6"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 4
depends_on: ["1.1"]
blocks: []
trace:
  - "FR-SYS-03"
  - "FR-SYS-05"
---

# Story 1.6: Git 备份文档 + KG 索引健康检查

Status: ready-for-dev

## Story

As a 学习者,
I want 可选的 Git 自动备份和知识图谱索引健康检查,
So that 我的学习数据有版本历史保护且图谱结构保持健康。

## Acceptance Criteria

1. **Given** 学习者安装并启用了 Obsidian Git 社区插件
   **When** 自动备份触发（定时/手动）
   **Then** 备份异步执行，不阻塞笔记编辑和 Skill 操作
   **And** .gitignore 正确排除 LanceDB 数据目录（`data/lancedb/`）和 Neo4j 数据目录
   **And** .gitignore 排除 `.obsidian/workspace.json`（频繁变更无价值文件）

2. **Given** 学习者未安装 Obsidian Git 插件
   **When** 正常使用系统
   **Then** 系统全部功能正常工作，无任何降级
   **And** 不显示任何 Git 相关错误或警告

3. **Given** 学习者触发知识图谱健康检查
   **When** 系统扫描 Graphify 索引
   **Then** 报告包含以下指标：
   - 孤立节点数量（有实体但无关系的节点）
   - 矛盾关系数量（同一对节点间存在语义矛盾的边）
   - 置信度分布（高/中/低各占比）
   - 总节点数和总关系数
   **And** 报告格式为结构化 JSON

4. **Given** Neo4j 不可用
   **When** 触发健康检查
   **Then** 返回错误信息 "Neo4j 未连接" + 修复建议
   **And** 不导致后端崩溃

5. **Given** 健康检查发现孤立节点
   **When** 报告生成
   **Then** 列出孤立节点的标题列表（最多 20 个）
   **And** 提示用户可以为这些节点添加 wikilink 关系

## Tasks / Subtasks

- [ ] Task 1: .gitignore 配置文档与验证 (AC: #1, #2)
  - [ ] 1.1: 在 vault 初始化（Story 1.1 VaultInitService）中生成 `.gitignore` 文件，包含：`data/lancedb/` · `data/neo4j/` · `.obsidian/workspace.json` · `.obsidian/workspace-mobile.json` · `*.sqlite` · `*.sqlite-wal`
  - [ ] 1.2: 如果 `.gitignore` 已存在，追加缺失规则（不覆盖用户自定义规则）
  - [ ] 1.3: 在 Story 1.1 的安装引导报告中增加 Git 备份状态字段：`git_plugin_installed: bool`（检测 `.obsidian/plugins/obsidian-git/` 是否存在）

- [ ] Task 2: Obsidian Git 配置文档 (AC: #1, #2)
  - [ ] 2.1: 在 vault 的 CLAUDE.md 中添加 Git 备份说明段落：推荐配置（auto-commit 间隔 10 分钟、auto-push 关闭）、.gitignore 已自动配置
  - [ ] 2.2: 说明 Git 插件为可选组件，不影响任何核心功能

- [ ] Task 3: KG 健康检查 service (AC: #3, #4, #5)
  - [ ] 3.1: 创建 `backend/app/services/kg_health_service.py`
  - [ ] 3.2: 实现 `KGHealthService.__init__(neo4j_client)` 依赖注入 Neo4j 客户端
  - [ ] 3.3: 实现 `run_health_check() -> KGHealthReport` 执行以下 Cypher 查询：
    - 孤立节点：`MATCH (n) WHERE NOT (n)--() RETURN n.title LIMIT 20`
    - 矛盾关系：`MATCH (a)-[r1]->(b), (a)-[r2]->(b) WHERE type(r1) <> type(r2) RETURN count(*)`
    - 置信度分布：`MATCH (n) RETURN CASE WHEN n.confidence >= 0.7 THEN 'high' WHEN n.confidence >= 0.4 THEN 'medium' ELSE 'low' END AS level, count(*) AS cnt`
    - 总体统计：`MATCH (n) RETURN count(n)` + `MATCH ()-[r]->() RETURN count(r)`
  - [ ] 3.4: `KGHealthReport` dataclass：`orphan_count: int` · `orphan_titles: List[str]` · `contradiction_count: int` · `confidence_distribution: Dict[str, int]` · `total_nodes: int` · `total_relationships: int` · `checked_at: datetime`

- [ ] Task 4: KG 健康检查 endpoint (AC: #3, #4)
  - [ ] 4.1: 在 `backend/app/api/v1/endpoints/health.py` 中新增 `GET /api/v1/health/kg`
  - [ ] 4.2: 调用 `KGHealthService.run_health_check()` 返回 JSON 报告
  - [ ] 4.3: Neo4j 连接异常返回 `503 Service Unavailable` + `{"error": "Neo4j 未连接", "suggestion": "请检查 Docker 容器是否运行: docker ps | grep neo4j"}`

- [ ] Task 5: 测试 (AC: #1, #3, #4, #5)
  - [ ] 5.1: `backend/tests/unit/test_kg_health_service.py` — 各 Cypher 查询返回正确结构、Neo4j 不可用时的错误处理
  - [ ] 5.2: `backend/tests/unit/test_gitignore_generation.py` — .gitignore 生成正确、追加模式不覆盖已有规则
  - [ ] 5.3: `backend/tests/integration/test_kg_health_integration.py` — 真实 Neo4j 连接下的端到端健康检查（需 Neo4j 可用）

## Dev Notes

- **Obsidian Git 是社区插件**: 本 story 不编写 Git 功能代码，只做配置文档和验证。Obsidian Git 插件本身已是成熟方案（20K+ 安装量），异步非阻塞是其内置行为
- **Service 风格**: 参考 `backend/app/services/rag_service.py` — structlog、类型标注
- **Neo4j 客户端**: `backend/app/clients/neo4j_client.py`（AsyncGraphDatabase），端口 `bolt://localhost:7691`
- **Cypher 查询**: 孤立节点查询需注意 Graphify 创建的节点可能使用特定 label，需确认实际 label
- **置信度字段**: Graphify 节点的置信度字段名需从实际数据确认（可能是 `confidence` 或 `weight`）
- **structlog**: `structlog.get_logger(__name__)` 统一
- **.gitignore 幂等**: 追加规则前先检查是否已存在，避免重复行

### Project Structure Notes

- 新建文件：`backend/app/services/kg_health_service.py`
- 修改文件：`backend/app/services/vault_init_service.py`（Story 1.1 产出，追加 .gitignore 生成逻辑）
- 修改文件：`backend/app/api/v1/endpoints/health.py`（新增 /health/kg endpoint）
- 测试文件：`backend/tests/unit/test_kg_health_service.py`
- 测试文件：`backend/tests/unit/test_gitignore_generation.py`
- 测试文件：`backend/tests/integration/test_kg_health_integration.py`

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-03] — 可选 Git 备份
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SYS-05] — KG 索引健康检查
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.6] — AC 原文
- [Source: backend/app/clients/neo4j_client.py] — Neo4j 异步客户端
- [Source: backend/app/api/v1/endpoints/health.py] — 现有健康检查 endpoint
- [Source: docs/architecture.md#Neo4j] — Neo4j 连接配置（bolt://localhost:7691）

## UAT Script

> 非技术用户验收脚本

1. **验证 .gitignore 配置** (AC: #1)
   - 运行安装引导后，打开 vault 根目录下的 `.gitignore` 文件
   - 应该看到已排除的路径：`data/lancedb/` 等
   - 如果你之前已有 .gitignore，检查是否保留了你的自定义规则

2. **验证无 Git 不影响使用** (AC: #2)
   - 如果你没有安装 Obsidian Git 插件，所有学习功能应该正常使用
   - 安装引导报告中 Git 状态显示为 "未安装（可选）"

3. **验证知识图谱健康检查** (AC: #3, #5)
   - 在浏览器访问 `http://localhost:8001/api/v1/health/kg`
   - 应该看到 JSON 报告，包含：
     - 孤立节点数量和名称列表
     - 矛盾关系数量
     - 置信度分布（高/中/低百分比）
     - 节点和关系总数

4. **验证 Neo4j 不可用处理** (AC: #4)
   - 关闭 Neo4j Docker 容器
   - 访问 `http://localhost:8001/api/v1/health/kg`
   - 应该看到错误信息 "Neo4j 未连接" 和修复建议，而不是服务器崩溃

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.6.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_kg_health_service.py -x -q` | 0 failed |
| CP-1.6.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_gitignore_generation.py -x -q` | 0 failed |
| CP-1.6.3 | ruff | `ruff check backend/app/services/kg_health_service.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes
<!-- Auto-filled -->

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
