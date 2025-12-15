# Canvas Learning System - Claude Code Instructions

## Epic 实现状态 (UltraThink 深度验证 2025-12-15)

| Epic | 名称 | 实现率 | 关键代码位置 |
|------|------|--------|-------------|
| 1-5 | 原始Canvas系统 | 100% | `backend/app/services/` |
| 10 | Canvas集成 | 100% | `canvas_service.py` |
| 11/15 | FastAPI后端 | 100% | `backend/app/main.py` (11端点) |
| **12** | **LangGraph多Agent** | **88%** | `src/agentic_rag/` |
| **13** | **Obsidian插件** | **90%** | `canvas-progress-tracker/` (22服务) |
| **14** | **复习系统** | **95%** | `review_service.py` (1,247行) |
| 16 | 跨Canvas | 100% | Git tag确认 |
| 18 | 回滚系统 | 100% | `src/rollback/` |

### Epic 12 LangGraph 实际代码位置

```
src/agentic_rag/                      # LangGraph实现 (非backend/)
├── state_graph.py          (12KB)    # StateGraph编排
├── state.py                (5KB)     # State schema
├── nodes.py                (27KB)    # 7个核心节点
├── clients/
│   ├── graphiti_client.py            # Graphiti集成
│   ├── lancedb_client.py             # LanceDB集成
│   └── temporal_client.py            # Temporal Memory
├── fusion/
│   ├── rrf_fusion.py                 # RRF融合
│   ├── weighted_fusion.py            # 加权融合
│   └── cascade_retrieval.py          # Cascade融合
└── reranking.py                      # Reranking策略
```

---

## 部署关键路径 (必读)

### Obsidian 插件部署

**构建输出**: `canvas-progress-tracker/obsidian-plugin/main.js`

| 位置 | 路径 | 状态 |
|------|------|------|
| **正确目标** | `C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\` | 使用此路径 |
| ~~错误位置~~ | ~~`C:\Users\ROG\托福\笔记库\.obsidian\plugins\canvas-review-system\`~~ | 已删除 (2025-12-15) |

### 部署检查清单

```powershell
# 1. 构建插件
cd canvas-progress-tracker/obsidian-plugin && npm run build

# 2. 复制到正确位置 (注意路径!)
Copy-Item main.js "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force
Copy-Item manifest.json "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force

# 3. 验证部署 (main.js 应 >= 520KB)
Get-Item "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\main.js"

# 4. 重启 Obsidian 加载新插件
```

### 后端服务

- **位置**: `backend/app/services/`
- **启动**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **端口**: **8000** (统一配置，前后端一致)

---

## 项目结构

```
C:\Users\ROG\托福\
└── Canvas/                              # 主项目 Git仓库
    ├── backend/                         # FastAPI后端
    │   └── app/services/                # 21个服务文件 (10,708行)
    ├── src/agentic_rag/                 # LangGraph RAG系统 (Epic 12)
    ├── canvas-progress-tracker/         # Obsidian插件源码
    │   └── obsidian-plugin/
    │       └── main.js                  # 构建输出 (部署源)
    ├── scripts/legacy/                  # 迁移的旧脚本 (302个)
    ├── 笔记库/                          # Obsidian Vault
    │   └── .obsidian/plugins/
    │       └── canvas-review-system/    # 插件部署目标
    └── CLAUDE.md                        # 本文件
```

---

## Context Snapshot System

当会话压缩时，PreCompact hook 会自动在此文件中插入快照标记。
SessionStart hook 会在新会话开始时自动清理过期标记。
