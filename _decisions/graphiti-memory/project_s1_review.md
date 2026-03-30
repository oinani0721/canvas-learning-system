---
name: S1 Review Session 三方独立审查结果
description: S1死代码清理方案经三个独立agent审查后的关键发现、缺陷和修订建议（2026-03-13）
type: project
---

## 审查结论：方案可靠性 HIGH，2 个 CRITICAL 缺陷必须修复

### CRITICAL 缺陷
1. **验证管道 Step 3 函数名错误** — `build_rag_graph` 不存在，实际是 `build_canvas_agentic_rag_graph`（state_graph.py:205）
2. **验证管道 Step 2 静默成功** — `__init__.py:75-109` 的 try/except 吞掉 ImportError，`from agentic_rag import *` 永远成功。需改为 `assert AGENTIC_RAG_AVAILABLE`

### HIGH 缺陷
3. **fusion/ 也应归档** — S3 需要参考融合算法，不只 reranking.py
4. **防回退换方案** — shell 脚本 → ruff banned-api 规则（零维护成本）
5. **"Beyond a Joke" 论文引用错误** — 实际讲编译器 DCE bug，不是 Python 动态分派

### MEDIUM 缺陷
6. 缺少 backend import 验证（rag_service.py:45）
7. review.py:66 悬空注释引用 env_config.py
8. conftest.py:176 mock 数据需同步更新 ghost table 修复
9. 归档目录需 mkdir -p

### 社区调研关键发现
- S1 全部验证是静态的，Meta SCARF 核心洞察是需要动态/运行时验证层
- vulture 应配置 --ignore-decorators 适配 FastAPI/LangGraph
- 社区推荐：deadcode（比 vulture 更多规则）、Skylos（处理框架魔法）、ruff F401

### 对抗性代码审查确认
- 9 个死模块全部独立验证确认死代码
- 2 个活跃模块确认活跃
- Ghost tables 4 个修复位置全部确认
- Fake verified 标记确认虚假（路径应为 src/api/routers/canvas.py 和 memory.py）

### 待用户确认
- 是否将修订合并回 S1 文档
