# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-12-02

### Epic 16: 跨Canvas关联学习系统

这个版本引入了跨Canvas关联学习功能，支持不同Canvas之间的概念关联和教材引用。

#### Added

**关联管理UI (Stories 16.1, 16.4)**
- Canvas关联管理Modal界面
- 支持创建、编辑、删除关联
- Toolbar按钮快速访问
- 关联模式Toggle控制 (Ctrl+Shift+L)
- 模式状态持久化存储

**配置管理 (Story 16.2)**
- `.canvas-links.json`配置文件自动生成
- 支持手动和自动关联
- 配置文件热加载和验证

**Graphiti知识图谱集成 (Story 16.3)**
- 跨Canvas关系存储到Neo4j
- 2秒超时优雅降级
- 30秒缓存机制
- 双写模式（本地 + Graphiti）

**教材引用系统 (Stories 16.5, 16.6)**
- Agent自动引用关联教材上下文
- 节点教材引用指示器
- 悬浮提示显示引用详情
- 前置知识自动检测

**关联状态指示器 (Story 16.7)**
- 状态栏显示关联数量
- 同步状态实时更新
- 右键菜单支持刷新/清理
- 脉冲动画提示变化

#### Technical Details

**新增文件** (11个TypeScript文件):
- `AssociationModal.ts` - 关联管理对话框
- `AssociationConfigService.ts` - 配置管理服务
- `GraphitiAssociationService.ts` - Graphiti集成
- `AssociationModeManager.ts` - 模式管理
- `TextbookContextService.ts` - 教材上下文
- `PrerequisiteDetector.ts` - 前置知识检测
- `TextbookReferenceView.ts` - 引用显示组件
- `StatusBarIndicator.ts` - 状态栏指示器
- `AssociationTypes.ts` - 类型定义

**API验证**:
- 所有Obsidian API调用均有@obsidian-canvas Skill验证标注
- 所有Graphiti调用均有@graphiti Skill验证标注

---

## [2.0.0] - 2025-11-29

### Epic 12: 三层记忆系统 + Agentic RAG

这是一个重大版本更新，引入了全新的三层记忆架构和智能检索增强系统。

#### Added

**三层记忆系统**
- **Layer 1: Graphiti时序知识图谱**
  - 时间感知的知识图谱存储
  - 自动追踪学习历程和概念关系
  - 支持复杂的知识结构查询
- **Layer 2: LanceDB向量数据库**
  - 从ChromaDB迁移到LanceDB
  - 高性能语义检索 (P95 < 50ms)
  - 支持多模态嵌入
- **Layer 3: Temporal Memory (FSRS)**
  - 基于FSRS算法的艾宾浩斯复习调度
  - 个性化复习间隔计算
  - 四个复习触发点 (24h, 7d, 30d, 动态)

**Agentic RAG检索增强**
- **LangGraph StateGraph编排**
  - 完整的检索工作流编排
  - 支持并行和顺序节点
  - 自适应路由决策
- **并行检索 (Graphiti + LanceDB)**
  - 双源并行检索
  - 自动故障降级
  - 可配置超时和重试
- **3种融合算法**
  - RRF (Reciprocal Rank Fusion): 通用场景
  - Weighted: 检验白板生成 (薄弱点权重70%)
  - Cascade: 高精度需求分层过滤
- **混合Reranking**
  - Cohere API: 高质量场景
  - Local (cross-encoder): 日常检索 (零成本)
  - 自动降级机制
- **质量控制循环**
  - 质量评分阈值检查
  - 自动Query重写 (最多2次)
  - 成本感知策略选择

**LangSmith可观测性**
- 100%请求追踪
- 延迟和成本监控
- 性能仪表盘
- 项目级别追踪分离

**完整测试套件**
- 回归测试 (360+ 测试用例)
- 性能基准测试 (MRR/Recall/F1)
- E2E集成测试 (2个完整场景)
- 契约测试 (API兼容性验证)

**文档和部署**
- 用户指南 (`docs/user_guide_epic12.md`)
- 运维手册 (`docs/operations/epic12_operations.md`)
- API文档 (`docs/api/agentic_rag_api.md`)
- 部署脚本 (`scripts/deploy_epic12.py`)
- 健康检查 (`scripts/health_check_epic12.py`)

#### Changed

- **检验白板生成**: 使用Agentic RAG替代原有检索
  - 准确率从70%提升到85%+
  - 支持薄弱点优先策略
- **检索延迟优化**: P95 < 400ms (含Reranking)
- **向量数据库**: 从ChromaDB迁移到LanceDB

#### Performance

| 指标 | Epic 11 | Epic 12 | 提升 |
|------|---------|---------|------|
| MRR@10 | 0.25 | 0.38+ | +52% |
| Recall@10 | 0.50 | 0.68+ | +36% |
| F1@10 | 0.60 | 0.77+ | +28% |
| P95延迟 | 200ms | 400ms | (含Reranking) |

#### Dependencies

新增依赖:
- `langgraph >= 0.2.55` - LangGraph工作流编排
- `lancedb >= 0.6.0` - 向量数据库
- `neo4j >= 5.15` - 图数据库驱动
- `cohere >= 5.0.0` - Reranking API (可选)
- `fsrs >= 1.0.0` - FSRS复习算法

#### Migration

从v1.x升级:

1. **安装新依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **启动Neo4j** (如使用Docker):
   ```bash
   docker run -d --name neo4j-canvas \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password123 \
     neo4j:5.15
   ```

3. **配置环境变量**:
   ```bash
   cp .env.example .env
   # 编辑.env设置NEO4J_URI等
   ```

4. **运行部署脚本**:
   ```bash
   python scripts/deploy_epic12.py
   ```

5. **验证部署**:
   ```bash
   python scripts/health_check_epic12.py
   ```

---

## [1.5.0] - 2025-11-15

### Epic 10-11: 并行执行引擎 + FastAPI后端

#### Added
- 异步并行执行引擎
- 智能Agent调度器
- FastAPI REST API后端
- 资源感知负载均衡

---

## [1.0.0] - 2025-10-01

### Epic 1-6: 核心学习系统

#### Added
- 14个专业化Agent
- Canvas颜色系统 (红→紫→绿)
- 4维评分系统
- 检验白板生成
- 基础复习提醒

---

## Links

- [用户指南](docs/user_guide_epic12.md)
- [运维手册](docs/operations/epic12_operations.md)
- [API文档](docs/api/agentic_rag_api.md)
- [项目README](README.md)
