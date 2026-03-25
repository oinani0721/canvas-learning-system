# 源码树分析

> 生成时间: 2026-03-24 | 扫描模式: exhaustive

## 项目根目录

```
canvas-learning-system/
├── frontend/              # Tauri+React 桌面应用
│   ├── src/               # React 源码 (54 文件, 14,852 行)
│   │   ├── components/    # 30 UI 组件 (6 子目录)
│   │   ├── stores/        # 4 Zustand stores
│   │   ├── services/      # 12 services (含 Agent SDK engine)
│   │   ├── hooks/         # 3 React hooks
│   │   ├── App.tsx        # 应用入口 (ReactFlow 画布 + 面板布局)
│   │   └── types.ts       # 共享类型定义
│   ├── sidecar/           # Node.js Agent SDK sidecar (468 行)
│   │   └── sidecar.js     # Claude Agent SDK JSON-RPC bridge
│   └── src-tauri/         # Rust Tauri 后端
│       ├── src/main.rs    # Tauri 应用入口
│       └── Cargo.toml     # Rust 依赖
│
├── backend/               # FastAPI Python 后端
│   ├── app/               # 核心应用 (179 文件, 83,846 行)
│   │   ├── api/v1/        # API 路由层
│   │   │   ├── router.py  # 路由聚合器 (31 个 sub-router)
│   │   │   ├── system.py  # 系统健康端点
│   │   │   └── endpoints/ # ~155 REST 端点 (35 文件)
│   │   ├── services/      # 38 service 类 (业务逻辑层)
│   │   ├── models/        # 24 Pydantic 数据模型文件
│   │   ├── mcp/           # MCP 服务器 + 15 工具
│   │   │   ├── server.py  # FastAPI-MCP ASGI 集成
│   │   │   ├── pipeline_token.py  # 工具链 token 验证
│   │   │   └── tools/     # 6 个工具模块文件
│   │   ├── clients/       # 数据库/AI 客户端 (14 文件)
│   │   ├── graphiti/      # Graphiti 实体类型定义
│   │   ├── core/          # 核心基础设施 (异常、日志、配置)
│   │   ├── middleware/     # 中间件 (CORS, 指标, 成本追踪)
│   │   └── dependencies.py # FastAPI 依赖注入
│   ├── Dockerfile         # 后端容器镜像
│   ├── requirements.txt   # Python 依赖
│   └── .env.example       # 环境变量模板
│
├── src/                   # Legacy Python (311 文件)
│   ├── agentic_rag/       # 活跃：Agentic RAG 管道 (19,220 行)
│   │   ├── pipeline/      # 6 路并行检索 + fusion + rerank
│   │   ├── models/        # 数据模型
│   │   ├── retrievers/    # 检索器实现
│   │   └── quality/       # 质量检查 + faithfulness
│   ├── memory/temporal/   # 活跃：FSRS 间隔重复 (1,335 行)
│   ├── rollback/          # 活跃：回滚引擎 (2,613 行)
│   ├── api/               # 非活跃：旧 API 接口
│   ├── command_handlers/  # 非活跃：Obsidian CLI 命令
│   ├── canvas_utils.py    # 非活跃：34,641 行 monolith
│   ├── verification_graph/# 非活跃：未接线的验证图
│   └── tests/             # 测试文件
│
├── docker-compose.yml     # 服务编排 (Neo4j + Ollama + Backend)
├── _decisions/            # 架构决策文档 (ADR)
├── _archive/              # 归档的 legacy 代码 (旧 Obsidian 插件)
├── docs/                  # 项目文档
│   ├── architecture/      # 架构设计文档
│   ├── prd/               # 产品需求文档
│   ├── epics/             # Epic 定义
│   ├── stories/           # Story 定义
│   └── design/            # UI 设计文件
├── config/                # 配置文件 (alerts.yaml 等)
├── data/                  # 数据目录 (LanceDB, 备份等)
└── CLAUDE.md              # AI 助手项目说明
```

## 代码量统计

| 部分 | 文件数 | 代码行数 | 状态 |
|------|--------|----------|------|
| Frontend (React+TS) | 54 | 14,852 | 活跃 |
| Backend (FastAPI Python) | 179 | 83,846 | 活跃 |
| Sidecar (Node.js) | 1 | 468 | 活跃 |
| Src-Legacy (Python, 活跃部分) | ~30 | 23,168 | 部分活跃 |
| Src-Legacy (Python, 非活跃) | ~280 | ~49,000 | 非活跃 |
| **合计** | **546+** | **~145,000+** | - |

## 关键目录详解

### frontend/src/components/ (30 个组件)

```
components/
├── ChatPanel.tsx          # 主聊天面板 (含消息列表+输入栏)
├── NodeContextMenu.tsx    # 节点右键菜单 (颜色/考试/档案)
├── Settings.tsx           # 全局设置面板
├── StatusBar.tsx          # 底部状态栏
├── SyncIndicator.tsx      # 同步状态指示器
├── chat/                  # 聊天子组件 (13 个)
│   ├── InputBar.tsx       # 消息输入栏
│   ├── MessageBubble.tsx  # 消息气泡
│   ├── ToolCallCard.tsx   # 工具调用展示卡片
│   ├── ObserverBadge.tsx  # Observer 学习行为标记
│   ├── SkillSelector.tsx  # /命令 技能选择器
│   └── ...
├── dashboard/             # 仪表板 (2 个)
│   ├── ExamCard.tsx       # 考试卡片
│   └── ReviewItem.tsx     # 复习项
├── exam/                  # 考试子组件 (6 个)
│   ├── ExamCanvas.tsx     # 考试画布
│   ├── ExamModeSelector.tsx # 考试模式选择器
│   └── ...
├── markdown/              # Markdown 渲染 (1 个)
├── nodes/                 # 节点类型 (3 个)
│   ├── KnowledgeNode.tsx  # 知识节点
│   ├── ImageNode.tsx      # 图片节点
│   └── nodeTypes.ts       # 节点类型注册
└── profile/               # 学习档案 (1 个)
    └── LearningProfile.tsx
```

### backend/app/services/ (38 个 service)

按功能分组：

| 分组 | 主要 Service | 说明 |
|------|-------------|------|
| Agent | agent_service, agent_routing_engine, agent_selector, react_agent | AI Agent 调度与执行 |
| Canvas | canvas_service, cross_canvas_service | Canvas CRUD + 跨画布关联 |
| Mastery | mastery_engine, mastery_store, mastery_fusion, calibration_tracker | 掌握度引擎 (BKT+FSRS 融合) |
| Memory | memory_service, learning_context_service | 学习记忆 + 上下文组装 |
| Exam | exam_service, exam_service_ext, question_generator, autoscore | 考试生成 + 自动评分 |
| RAG | rag_service, context_enrichment_service, scoring_faithfulness | RAG 检索 + 忠实度评分 |
| Review | review_service | 复习调度 (FSRS 驱动) |
| System | health_monitor, resource_monitor, error_aggregator, error_classifier | 健康监控 + 错误分类 |
| Infra | event_bus, websocket_manager, session_manager, sync_service | 事件总线 + 会话管理 |
| Index | lancedb_index_service, markdown_image_extractor | 向量索引 + 图片提取 |
| Archive | conversation_archive, conversation_distiller, archive_scheduler | 对话归档 (Hot-Warm-Cold) |
| Other | skill_registry, prompt_registry, recommendation_service | 技能注册 + Prompt 管理 |

### src/ Legacy 活跃代码

| 模块 | 行数 | 说明 | 被 backend/ 调用 |
|------|------|------|-----------------|
| agentic_rag/ | 19,220 | 6 路并行检索管道: LanceDB semantic + Neo4j graph + Graphiti temporal + multimodal + textbook + cross-canvas | 是 (via PYTHONPATH) |
| memory/temporal/ | 1,335 | FSRS 间隔重复算法实现 | 是 |
| rollback/ | 2,613 | Canvas 回滚引擎: snapshot + diff + restore | 是 |
