# Workflow A 升级路径与 2026 年最低返工率工作流深度研究

**核心结论：Workflow A 的物理隔离 + mutmut 门控模式方向正确，但需要三层关键升级才能稳定运行。** 第一，针对 Neo4j/LanceDB 集成层引入 testcontainers + 嵌入式模式的双轨 fixture 架构；第二，通过自动化 schema 摘要（stubgen + OpenAPI）实现 test-writer 的只读契约传递；第三，用 pytest-gremlins 的并行 AST 插桩模式替代 mutmut 放入 Stop hook，将变异测试从分钟级压缩到秒级。学术研究（TDAD, arXiv:2603.17973）的核心发现为"**上下文优于过程**"——泛泛的 TDD 流程指令反而使回归率从 6.08% 恶化到 9.94%，而精准传递受影响测试列表可降低 70% 回归。社区实证数据表明 2026 年返工率最低的组合是 **GSD 规划 + Workflow A 执行 + pytest-gremlins 审查**，辅以 TDAD 风格的依赖图分析。

---

## 一、Workflow A 升级方案：从单次成功到稳定低返工

### 1a. Neo4j/LanceDB 集成测试的双轨 fixture 架构

Workflow A 在纯函数层（如 scoring_utils.py）表现优异，但在数据库集成层的失效风险源于测试无法触及真实 I/O。解决方案是**为 Neo4j 使用 testcontainers，为 LanceDB 使用嵌入式模式**，形成双轨并行。

**testcontainers-python 当前状态**：v4.14.2（2026 年初），通过 `pip install testcontainers[neo4j]` 安装，`Neo4jContainer` 类直接支持 Neo4j 5.x 镜像。关键配置是 **session-scoped 容器 + function-scoped 清理**，避免每个测试重启容器（Neo4j 冷启动 **10-30 秒**，热缓存后约 10 秒）。

```python
# conftest.py —— 完整的双轨 fixture 配置
import pytest
import pytest_asyncio
from testcontainers.neo4j import Neo4jContainer
from neo4j import AsyncGraphDatabase
import lancedb
import uuid

# ===== Neo4j：session-scoped 容器，启动一次 =====
@pytest.fixture(scope="session")
def neo4j_container():
    with Neo4jContainer(
        image="neo4j:5.26-community",
        username="neo4j",
        password=str(uuid.uuid4())
    ).with_env("NEO4J_PLUGINS", '["apoc"]') as container:
        yield container

@pytest_asyncio.fixture(scope="session")
async def neo4j_driver(neo4j_container):
    bolt_url = neo4j_container.get_connection_url()
    driver = AsyncGraphDatabase.driver(
        bolt_url,
        auth=("neo4j", neo4j_container.NEO4J_ADMIN_PASSWORD)
    )
    yield driver
    await driver.close()

# function-scoped 清理：每个测试后清空数据，不重启容器
@pytest.fixture(autouse=True)
def clean_neo4j(neo4j_container):
    yield
    driver = neo4j_container.get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()

# ===== LanceDB：嵌入式模式，零启动成本 =====
@pytest.fixture
def lance_db(tmp_path):
    """function-scoped，每个测试独享新目录，无需容器。"""
    return lancedb.connect(str(tmp_path / "test_lance"))

@pytest.fixture
def lance_table(lance_db):
    data = [
        {"id": 1, "text": "概念A", "vector": [0.1, 0.2, 0.3]},
        {"id": 2, "text": "概念B", "vector": [0.4, 0.5, 0.6]},
    ]
    return lance_db.create_table("test_concepts", data)
```

**pyproject.toml 的 asyncio 配置**（解决 session-scoped async fixture 的事件循环问题）：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
# 关键：确保 session-scoped async fixture 与测试共享同一事件循环
```

**LanceDB 嵌入式模式的优势**：版本 0.30.1（2026 年 3 月），Alpha 状态但功能稳定。因为是进程内运行（基于 Lance 列式格式的本地文件系统存储），启动时间 **<100ms**，无需 Docker，`tmp_path` 自动清理。这意味着 LanceDB 测试天然隔离，无状态泄漏风险。（证据强度：**强**——来自 PyPI 官方文档和 LanceDB 架构设计）

**testcontainers vs Docker Compose 选择**：对于 Claude Code Agent 循环，testcontainers 是明确更优的选择。原因有三：（1）所有配置内聚在 `conftest.py` 中，agent 无需管理外部 YAML；（2）Ryuk 旁车容器在 agent 崩溃时自动清理；（3）随机端口分配避免并行测试冲突。Docker Compose 唯一优势是容器预热后零启动延迟，但这在 CI 循环中意义不大。（证据强度：**强**——testcontainers 官方文档明确推荐此模式）

### 1b. test-writer 的 "只读 schema 摘要" 自动化机制

核心问题是：如何让 test-writer Teammate 拥有足够上下文写出真实断言，同时不看到实现细节？推荐**三层契约文档自动生成**：

**第一层：Python `.pyi` 类型存根（stubgen）**

```bash
# 从现有代码自动生成（mypy 内置工具）
stubgen -p canvas_app.services -p canvas_app.models \
    --include-docstrings -o .claude/contracts/stubs/
```

这会生成如下文件：
```python
# .claude/contracts/stubs/canvas_app/services/graph_service.pyi
from canvas_app.models import Concept, Relationship
from typing import Optional

async def create_concept(name: str, content: str, embedding: list[float]) -> Concept: ...
async def find_related(concept_id: str, max_depth: int = 2) -> list[Relationship]: ...
async def search_by_vector(query_vector: list[float], top_k: int = 5) -> list[Concept]: ...
```

**第二层：FastAPI OpenAPI schema（自动生成，零手动维护）**

```bash
python -c "
from canvas_app.main import app
import json
schema = app.openapi()
# 只保留 paths 和 components/schemas，去掉 info/servers
contract = {
    'paths': schema['paths'],
    'schemas': schema.get('components', {}).get('schemas', {})
}
with open('.claude/contracts/api_contract.json', 'w') as f:
    json.dump(contract, f, indent=2, ensure_ascii=False)
"
```

**第三层：CONTEXT.md 接口摘要（通过 inspect 自动提取）**

```python
#!/usr/bin/env python3
# scripts/generate_contract_context.py
import inspect, importlib, json

MODULES = [
    "canvas_app.services.graph_service",
    "canvas_app.services.vector_service",
    "canvas_app.services.scoring_utils",
]

def generate():
    lines = ["# Interface Contract（自动生成，勿手动编辑）\n"]
    for mod_name in MODULES:
        mod = importlib.import_module(mod_name)
        lines.append(f"## {mod_name}\n")
        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_"):
                continue
            sig = inspect.signature(obj)
            doc = (inspect.getdoc(obj) or "无文档").split("\n")[0]
            lines.append(f"- `{name}{sig}` — {doc}")
        lines.append("")
    with open(".claude/contracts/CONTEXT.md", "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    generate()
```

**SendMessage payload 设计**——test-writer 向 implementer 传递的内容应包含：

```json
{
  "task": "实现 graph_service.find_related",
  "spec_file": "tests/test_graph_service.py",
  "contract_ref": ".claude/contracts/CONTEXT.md#graph_service",
  "fixtures_available": ["neo4j_driver", "lance_db", "lance_table"],
  "acceptance_criteria": [
    "find_related(concept_id='c1', max_depth=2) 返回包含直接和间接关系",
    "不存在的 concept_id 返回空列表",
    "max_depth=0 只返回直接关系"
  ]
}
```

这个 payload 确保 implementer 不需要反复询问，因为它包含了**具体的测试文件路径、可用的 fixture 名、以及用自然语言表达的验收标准**。（证据强度：**中**——stubgen 和 OpenAPI 是成熟工具，但此组合模式尚无社区大规模验证）

### 1c. 变异测试从阻塞 CI 到 Stop hook 的性能跨越

**mutmut 3.5.0 的核心性能数据**：对 **~100 行纯函数**（如 scoring_utils.py），在 0.5 秒测试套件下，约生成 80-150 个变异体，总执行时间约 **15-60 秒**。这对 Stop hook 来说勉强可接受，但对交互式开发偏慢。

**pytest-gremlins：推荐的替代方案**。v1.5.1 稳定版，采用 AST 插桩模式（非 mutmut 的磁盘写入模式），一次插桩所有变异，通过环境变量切换激活变异——**无文件 I/O，无模块重载**。

| 模式 | 执行时间 | 相对 mutmut |
|------|----------|------------|
| 顺序模式 | 17.79s | 0.84x（略慢） |
| 并行模式 | 3.99s | **3.73x 快** |
| 并行 + 热缓存 | 1.08s | **13.82x 快** |

**关键注意**：以上基准由工具作者（Mike Lane）在合成项目上自测，GitHub 仅 **15 stars**，无独立验证。但工程架构合理——AST 插桩 + 覆盖率引导 + 并行子进程 + 内容哈希缓存，理论上确实比 mutmut 的序列化磁盘写入快得多。（证据强度：**弱**——自报数据，未经独立验证，但架构优势有理论支撑）

**推荐的 Stop hook 集成配置**：

```toml
# pyproject.toml
[tool.pytest-gremlins]
operators = ["comparison", "arithmetic", "boolean", "return"]
paths = ["src/canvas_app"]
exclude = ["**/migrations/*", "**/test_*"]
cache = true
max-pardons-pct = 5.0  # 超过 5% 存活变异则失败
```

```bash
#!/bin/bash
# .claude/hooks/mutation_gate.sh —— Stop hook 变异测试门
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | grep -v 'test_')
if [ -z "$CHANGED_FILES" ]; then exit 0; fi

echo '{"status": "running", "message": "🧬 变异测试中..."}' >&2
pytest --gremlins --gremlin-parallel --gremlin-workers=4 \
    --gremlin-paths="$CHANGED_FILES" 2>/dev/null

if [ $? -ne 0 ]; then
    echo '{"status": "failed", "message": "❌ 变异体存活过多，需加强测试"}' >&2
    exit 2  # exit 2 阻止 Claude 停止，强制其修复
fi
exit 0
```

**mutmut 的增量优化配置**（如果选择保留 mutmut）：

```toml
[tool.mutmut]
paths_to_mutate = ["src/canvas_app/"]
mutate_only_covered_lines = true  # 只变异有测试覆盖的行
type_check_command = ['mypy', '--output-format=json']  # 过滤类型无效变异
max_stack_depth = 3  # 限制测试相关性深度
```

```bash
# 增量运行：只对 git diff 变更文件做变异
mutmut run --paths-to-mutate $(git diff --name-only HEAD~1 | grep '\.py$' | tr '\n' ' ') --CI
```

### 1d. Agent Teams tmux 模式完整配置

**`.claude/settings.json`**——项目级配置：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/mutation_gate.sh"
      }]
    }],
    "TaskCompleted": [{
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/verify_no_facade.sh"
      }]
    }],
    "SubagentStop": [{
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/check_test_quality.sh"
      }]
    }]
  }
}
```

**`~/.tmux.conf`**——必须配置：

```bash
set -g base-index 1             # 窗口从 1 开始
setw -g pane-base-index 1       # 面板从 1 开始（关键！Claude Code Agent Teams 依赖此设置）
set -g remain-on-exit off       # agent 退出时自动关闭面板
set -g mouse on                 # 鼠标点击/拖拽面板
set -g focus-events on          # 传递焦点事件给程序
set -sg escape-time 0           # 无 Escape 延迟
set -g history-limit 50000      # 滚动缓冲区
```

**test-writer Teammate 的 CLAUDE.md**：

```markdown
# Test Writer 角色定义

你是一个测试编写专家。你的唯一职责是编写高质量的测试文件。

## 严格禁止
- ❌ 绝对不要读取 `src/` 目录下的 .py 实现文件
- ❌ 绝对不要在测试文件内定义 @staticmethod 或 helper 函数来复制生产逻辑
- ❌ 绝对不要使用 unittest.mock.patch 来替代真实模块导入

## 必须遵守
- ✅ 只参考 `.claude/contracts/` 下的接口契约文档（CONTEXT.md、.pyi 存根、api_contract.json）
- ✅ 所有被测函数必须通过 `from canvas_app.xxx import yyy` 真实导入
- ✅ 使用 conftest.py 中已定义的 fixture（neo4j_driver, lance_db, lance_table）
- ✅ 每个测试必须有明确的 assert 语句，断言具体返回值或副作用

## 可用上下文
- `.claude/contracts/CONTEXT.md` —— 函数签名和文档摘要
- `.claude/contracts/stubs/` —— .pyi 类型存根
- `.claude/contracts/api_contract.json` —— FastAPI OpenAPI schema
- `conftest.py` —— 可用的 pytest fixture 列表

## 通信协议
完成测试后，使用 SendMessage 将以下内容发送给 implementer：
1. 测试文件路径
2. 测试覆盖的函数签名列表
3. 每个测试的预期行为描述
```

**implementer Teammate 的 CLAUDE.md**：

```markdown
# Implementer 角色定义

你是一个实现专家。你的职责是让 test-writer 编写的测试全部通过。

## 严格禁止
- ❌ 不修改任何 test_*.py 文件
- ❌ 不在测试文件中添加任何代码
- ❌ 不使用内联修复（inline fix），必须提取为独立模块/函数

## 必须遵守
- ✅ 只修改 `src/` 目录下的实现文件
- ✅ 新功能必须提取为独立模块，不内联到现有大函数中
- ✅ 所有公共函数必须有类型注解
- ✅ 实现完成后运行 `pytest tests/ -x` 确认全部通过

## 代码质量要求
- 每个函数不超过 20 行（radon 复杂度 ≤ B 级）
- 新增逻辑必须为独立可测试单元
- 使用 `from canvas_app.xxx import yyy` 的方式确保可被测试导入
```

### 1e. Tauri IPC 层：mockIPC 兼容隔离策略，但需类型契约桥梁

**`@tauri-apps/api/mocks` 在 Tauri 2 中完全可用**且与 Workflow A 的"真实导入"原则兼容。关键原因：mockIPC 在 `window.__TAURI_INTERNALS__` 层全局拦截 invoke 调用，被测代码仍然使用 `import { invoke } from '@tauri-apps/api/core'` 的真实导入路径，不需要任何 facade 或 wrapper。

**推荐的分层测试策略**：

| 层级 | 工具 | Workflow A 适用性 |
|------|------|-------------------|
| React 纯 UI 逻辑 | Vitest + React Testing Library | ✅ 完全适用 |
| IPC 调用契约 | Vitest + mockIPC | ✅ 适用，需共享类型契约 |
| Rust 命令实现 | cargo test + MockRuntime | ⚠️ 独立流程，不在 A 的隔离范围内 |
| 全链路 E2E | WebDriver + tauri-driver | ❌ 不适用 A 的隔离策略，需独立 E2E |

**IPC 类型契约文件**（test-writer 和 implementer 共享）：

```typescript
// src/types/commands.ts —— 共享的 IPC 契约
export interface TauriCommands {
  'create_concept': {
    args: { name: string; content: string; };
    returns: { id: string; name: string; created_at: string; };
  };
  'search_concepts': {
    args: { query: string; top_k?: number; };
    returns: Array<{ id: string; name: string; score: number; }>;
  };
  'get_graph_neighbors': {
    args: { concept_id: string; max_depth?: number; };
    returns: Array<{ id: string; relationship: string; depth: number; }>;
  };
}
```

**Vitest 配置 + mockIPC 测试示例**：

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});

// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll } from 'vitest';
import { randomFillSync } from 'crypto';
import { clearMocks } from '@tauri-apps/api/mocks';

afterEach(() => { cleanup(); clearMocks(); });
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: { getRandomValues: (buf: any) => randomFillSync(buf) },
  });
});
```

**核心限制**：mockIPC 无法验证 Rust 端真实行为、IPC 权限模型（Tauri 2 的 capabilities）、以及真实序列化/反序列化。对于这些场景，**应绕过 Workflow A 的隔离策略，采用独立的 E2E 测试**（WebDriver + tauri-driver，但注意 **macOS 不原生支持 tauri-driver**，需社区 tauri-plugin-webdriver）。（证据强度：**强**——官方文档明确支持 mockIPC 在 vitest 中使用）

---

## 二、2026 年社区返工率最低工作流的实证分析

### 2a. 学术工作流的真实成绩与条件限制

**TDFlow（arXiv:2510.23761，CMU）**：声称 **94.3% SWE-bench Verified**，但这是在**提供人工编写的真实测试**的条件下达成的测试解决率，不是自主问题解决率。**自主模式仅 68.0%**。使用了 GPT-5 + Claude 4 Sonnet 组合（前沿模型，成本极高）。论文的核心洞察实际上支持 Workflow A 的方向：**瓶颈在测试生成而非测试解决**——当人类写出好测试时，LLM 解决率接近 94%。800 次运行中仅 7 次发现"测试作弊"。（证据强度：**中**——论文发表但无独立复现）

**AgentCoder（arXiv:2312.13010）**：**96.3% pass@1 在 HumanEval 上**。这是**函数级代码生成基准**（164 个 Python 编程题），不是仓库级软件工程。其三 agent 架构（Programmer + Test Designer + Test Executor）的"独立测试生成"原则与 Workflow A 一致，但**适用范围严格限制在单函数隔离任务**，不可推广到全栈项目。HumanEval 已是近饱和基准（前沿模型均 >90%），参考价值有限。（证据强度：**强**——论文经过验证，但基准局限性明确）

**TDAD（arXiv:2603.17973）**：这是**最具实操价值的论文**。在 100 个 SWE-bench Verified 实例上，测试级回归率从 **6.08% 降至 1.82%（70% 降幅）**。关键发现极其重要：**添加泛泛的 TDD 流程指令（不提供针对性测试上下文）反而将回归率恶化到 9.94%**——比什么都不做还差。机制是构建 AST 依赖图（代码↔测试），在提交补丁前查询静态 test_map.txt 识别受影响测试。使用开源模型 Qwen3-Coder 30B，消费级硬件可运行，`pip install tdad` 即可使用。（证据强度：**中**——已提交 ACM AIWare 2026 但尚未同行评审，代码/数据已开源）

### 2b. 社区验证工作流的真实状态

**GSD（Get Shit Done，39,800 ⭐）**是当前社区采用率最高的执行框架。其核心创新是 PLAN.md 作为"可执行指令"——每个计划最多 3 个任务，每个子 agent 获得完整 200K 上下文窗口，编排器保持 ~15% 上下文使用率。波并行（wave parallelism）+ 原子提交（每个任务一个 git commit）+ 目标反向验证（"什么必须为 TRUE"而非"做了什么任务"）。多位社区用户反馈："在 SpecKit、OpenSpec 和 TaskMaster 中产出最佳结果。"

**disler/claude-code-hooks-mastery（2,200-3,000 ⭐）** 的 Builder/Validator 模式是当前最成熟的 hook 质量门控实现。通过 Stop hook 附加验证器（`validate_new_file.py`、`validate_file_contains.py`），如果输出不满足结构要求（缺少必要章节、文件未创建等），exit code 2 阻止 agent 停止，强制修复。**10 commits 总量说明这是一个参考实现而非大型框架。**

**swingerman/atdd** 实现了 Robert C. Martin 的 ATDD 双流测试方法论。核心机制是**验收测试 + 单元测试双流约束**——AI 不能仅写通过单元测试的代码，还必须满足业务验收测试。spec-guardian agent 检测"实现泄漏"（spec 中不应出现类名、API 端点等实现细节）。Uncle Bob 的评价："两条不同的测试流迫使 Claude 更深入地思考代码结构。"

**"wreckit 14-gate verification pipeline" 经调查不存在**。mikehostetler/wreckit（26 ⭐）是一个实现 Ralph Loop 的 CLI 工具，其流程为 `ideas → research → plan → implement → PR → done`，没有"14-gate"概念。"14"这个数字可能源于 Claude Code hooks 系统支持的 **14+ 钩子事件类型**或 aaddrick/claude-pipeline 的 14 个 JSON schema，但这些是不同的概念。（证据强度：**强**——直接查证 GitHub 仓库确认不存在）

**Ralph Loop + Agent Teams 的实际使用**：Meag Tessmann（Medium, 2026 年 2 月）描述了一个混合模式——Agent Teams 处理创造性/判断性决策（"什么"和"为什么"），Ralph Loop 处理机械性工作（"做到它通过"）。分界线是"**输出是否可机器验证？如果是，循环；如果否，找人**"。Geoffrey Huntley 用 Ralph Loop 3 个月构建了一个完整编程语言；YC hackathon 团队用 \$297 API 成本一夜交付了 6+ 仓库。

### 2c. Neo4j + LanceDB 双数据库栈的特殊挑战

经过广泛搜索，**没有发现社区专门讨论 graph DB + vector DB 组合的 AI TDD 方案**。这是一个未被覆盖的空白领域。最接近的是 TDAD 的 AST 依赖图分析（用图结构分析代码依赖），但它是代码分析工具，不是数据库测试方案。

**testcontainers-python 对 Neo4j 5.x 的支持状态**：已验证可用，`Neo4jContainer("neo4j:5.26")` 正常工作。Neo4j 5.26 是 2026 年初的最新稳定版，`with_env("NEO4J_PLUGINS", '["apoc"]')` 可加载 APOC 插件。已知问题包括文档稀疏（远不如 Java 的 Testcontainers Neo4j 模块详细）和 Docker Hub 拉取速率限制（免费账户每 6 小时 100 次拉取）。

**对于 CI 循环的推荐**：testcontainers 优于 Docker Compose。原因已在 1a 中详述。额外补充：在 GitHub Actions `ubuntu-latest` runner 上 Docker 默认可用，无需额外配置。但需注意 Ryuk 旁车容器需要 Docker socket 访问权限。

---

## 三、已验证的混合方案分析

### 3a. BMAD V6 → Ralph 的转换：bmalph 桥接工具已存在

**关键发现：`bmalph`（github.com/LarsCowe/bmalph）是一个已存在的 CLI 工具，专门桥接 BMAD 和 Ralph。** 它的工作方式是：Phase 1-3 使用 BMAD agent 交互式规划，然后 `bmalph implement` 命令自动将 BMAD 产物转换为 Ralph 的 prd.json 格式，`bmalph run` 启动自主 Ralph 循环。

```bash
bmalph init --name canvas-learning-system
# Phase 1-3: 使用 BMAD agent（Analyst → PM → Architect → Scrum Master）
bmalph implement    # 自动 BMAD artifacts → Ralph prd.json
bmalph run          # 启动 Ralph 循环
```

**粒度鸿沟是核心兼容性挑战**。BMAD stories 是特性级作用域（一个 story 可能涉及多个文件和整个功能），而 Ralph 要求每个 story 必须**在一个上下文窗口（~200K tokens）内完成**。bmalph 通过让 Scrum Master agent 执行"epic 分片"解决此问题——将综合 PRD 拆解为聚焦的、自包含的开发单元。

**BMAD V6 当前状态**（19,100+ ⭐）：V6 处于 Alpha 阶段（接近 Beta 质量）。关键新特性包括 BMad-CORE 模块化基础、规模自适应智能（Quick Flow / BMad Method / Enterprise Method 三轨）、文档分片（大 PRD 拆为高上下文片段）、50+ 工作流和 19-21 个专业 agent。已知执行阶段问题：经社区测试，标准 Web 应用需要 **5.5-8 小时**的规划+执行时间，被批评为"过度工程化"。（证据强度：**中**——社区多方报告一致，但具体时间数据方法论不明）

### 3b. BMAD 规划 + Workflow A 执行 + mutmut 审查的完整流程

**这个组合尚无社区验证先例**，但从工程分析角度可行性较高。关键集成点：

**BMAD story 粒度与 Workflow A 的 1-3 文件限制兼容性**：BMAD stories 默认是特性级的，**不兼容**。解决方案是定制 Scrum Master agent 的规则，在 `bmad/_cfg/agents/` 中添加约束：

```markdown
<!-- bmad/_cfg/agents/scrum_master_override.md -->
## Story 粒度约束（适配 Workflow A）
- 每个 story 最多影响 3 个文件
- 每个 story 必须包含 "Interface Contract" 字段
- 如果一个特性需要修改超过 3 个文件，必须拆分为多个 story
- 每个 story 的实现应可在 200K token 上下文窗口内完成
```

**在 BMAD story 中嵌入 interface contract**：BMAD 的 Enterprise 轨道已包含集成契约（integration contracts）。可以在 story 模板中强制添加：

```markdown
## Story: 实现概念向量搜索 (S-003)

### Interface Contract
```python
# 输入
async def search_concepts(query: str, top_k: int = 5) -> list[ConceptResult]

# 依赖
from canvas_app.services.vector_service import embed_text
from canvas_app.services.graph_service import get_concept_by_id

# fixture 可用
neo4j_driver (session-scoped), lance_db (function-scoped)
```

### Acceptance Criteria
- 搜索 "机器学习" 返回相关度排序的概念列表
- top_k=0 返回空列表
- 不存在匹配时返回空列表
```

### 3c. 替代混合方案对比

**GSD + Workflow A 是比 BMAD + Workflow A 更优的组合**，原因有三：

第一，GSD 的 PLAN.md 天然限制每计划最多 3 个任务，与 Workflow A 的 1-3 文件限制高度契合。第二，GSD 的"目标反向验证"（"什么必须为 TRUE"）直接映射为测试断言，与 test-first 范式同构。第三，GSD 的编排器保持 ~15% 上下文使用率，为 test-writer 和 implementer 各保留完整上下文窗口。

**OpenSpec 的 Propose → Apply → Archive 状态机**适合作为**增量演进**（brownfield）场景的规划层替代 BMAD，但不适合 Canvas Learning System 的当前阶段（仍在构建核心功能，更接近 greenfield）。OpenSpec 的优势是 delta-based specs——仅加载变更规格，token 效率极高。

**TaskMaster AI（25,700 ⭐）** 是分解层工具，不是执行编排器。它的核心能力是 PRD → 结构化任务图，带依赖管理和复杂度分析。可以与 Workflow A 配合（TaskMaster 分解 → Workflow A 执行），但**缺少 GSD 的波并行和上下文隔离**能力。

### 推荐的最终混合方案

```
GSD discuss/plan → PLAN.md（每计划 ≤ 3 任务）
       ↓
为每个任务自动生成 Interface Contract
（stubgen + OpenAPI + CONTEXT.md）
       ↓
Workflow A 执行（test-writer → implementer 隔离）
       ↓
pytest-gremlins 变异测试 Stop hook
       ↓
TDAD 风格依赖图分析（识别受影响测试）
       ↓
facade 静态检测（AST 比对）
```

（证据强度：**弱**——此组合为推断性设计，各组件已验证但整体组合无社区先例）

---

## 四、10-20 任务大基数对比测试的实验设计

### 4a. 任务选择：六层矩阵 + 三类陷阱

**任务分层矩阵**——每层 3-4 个任务，共 18-21 个：

| 层级 | 复杂度 | 示例任务 | 建议数量 | 目标失效模式 |
|------|--------|---------|---------|-------------|
| L1 纯函数 | 简单 | scoring_utils.py 新增评分规则 | 3 | 基线（预期全部通过） |
| L2 单层 IO | 简单 | 文件写入工具函数 | 3 | facade 诱导 |
| L3 单数据库 | 中等 | Neo4j CRUD + Cypher 查询优化 | 3 | unsatisfiable spec |
| L4 跨层 | 中等 | FastAPI 端点 + Neo4j + 向量搜索 | 4 | context contamination |
| L5 前端 | 中等 | React + Tauri IPC 组件 | 3 | IPC mock 质量 |
| L6 全栈 | 困难 | 端到端知识图谱创建流程 | 3 | 综合失效 |

**三类"陷阱任务"设计**：

（1）**Facade 诱导任务**：要求修复 `scoring_utils.py` 中一个边界条件 bug，但 spec 中故意只描述输入输出行为、不指明具体函数。naive 的 test-writer 倾向于在测试中重新实现评分逻辑来验证结果。检测指标：测试文件内是否有非 `test_` 前缀的函数定义且 AST 大小 > 200。

（2）**Unsatisfiable spec 任务**：要求"函数应同时返回按相关度排序和按时间排序的结果"——这是矛盾的，除非返回两个列表。测试 workflow 是否能发现矛盾、主动澄清、还是盲目实现一个不一致的版本。

（3）**Context contamination 任务**：在仓库中放置一个使用旧 API 约定的模块（如直接操作 Neo4j driver），但目标模块应通过 service 层抽象访问。测试 workflow 是否被仓库中的旧模式"污染"。

### 4b. 评估指标体系

**主指标：mutation kill rate**（变异杀死率）。使用 pytest-gremlins 或 mutmut 对每个任务的输出代码运行变异测试，计算被杀死的变异体百分比。这是测试质量的最可靠衡量——kill rate 高意味着测试真正验证了行为，而非 facade。

**辅助指标矩阵**：

| 指标 | 类型 | 工具 | 权重 |
|------|------|------|------|
| Mutation kill rate | 连续 (0-100%) | pytest-gremlins | 主指标 |
| 功能正确性 | 二值 (pass/fail) | pytest | 基本门槛 |
| Facade 检测 | 二值 (有/无) | AST 静态分析 | 关键 |
| 行覆盖率 | 连续 (%) | coverage.py | 参考 |
| 圈复杂度变化 | 连续 | radon cc | 代码质量 |
| 是否提取独立模块 | 二值 | 人工审查 | 代码质量 |
| Token 消耗 | 连续 | API 日志 | 效率 |
| Wall-clock 时间 | 连续 (秒) | 计时 | 效率 |
| Implementer 重试次数 | 计数 | 日志 | 返工率 |

**Facade 自动检测器**——完整 Python 实现：

```python
#!/usr/bin/env python3
# scripts/detect_facade.py
import ast, os, sys

class FacadeDetector(ast.NodeVisitor):
    def __init__(self, prod_functions: dict):
        self.prod_functions = prod_functions
        self.warnings = []

    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            self.generic_visit(node)
            return
        # 检查：非测试函数包含实质逻辑
        body = [n for n in node.body
                if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) > 2:  # 超过 2 条语句 = 实质逻辑
            self.warnings.append(
                f"⚠️ FACADE: 测试文件中定义了非测试函数 '{node.name}' "
                f"(第 {node.lineno} 行, {len(body)} 条语句)"
            )
        # 检查是否与生产代码结构重复
        normalized = ast.dump(ast.Module(body=body, type_ignores=[]))
        for prod_name, prod_ast in self.prod_functions.items():
            if normalized == prod_ast:
                self.warnings.append(
                    f"🚨 FACADE_DUPLICATE: '{node.name}' 与生产函数 "
                    f"'{prod_name}' 结构完全一致！"
                )
        self.generic_visit(node)

def extract_prod_functions(prod_dir):
    funcs = {}
    for root, _, files in os.walk(prod_dir):
        for f in files:
            if f.endswith('.py') and not f.startswith('test_'):
                tree = ast.parse(open(os.path.join(root, f)).read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        body = [n for n in node.body
                                if not (isinstance(n, ast.Expr)
                                        and isinstance(n.value, ast.Constant))]
                        funcs[node.name] = ast.dump(
                            ast.Module(body=body, type_ignores=[]))
    return funcs

if __name__ == "__main__":
    prod_funcs = extract_prod_functions("src/canvas_app")
    all_warnings = []
    for root, _, files in os.walk("tests"):
        for f in files:
            if f.startswith('test_') and f.endswith('.py'):
                tree = ast.parse(open(os.path.join(root, f)).read())
                detector = FacadeDetector(prod_funcs)
                detector.visit(tree)
                for w in detector.warnings:
                    all_warnings.append(f"{os.path.join(root, f)}: {w}")
    for w in all_warnings:
        print(w)
    sys.exit(2 if all_warnings else 0)  # exit 2 可用于 hook 阻止
```

### 4c. 统计方法：双检验策略 + Monte Carlo 功效分析

**二值结果（pass/fail、有无 facade）使用 Cochran's Q 检验**；**连续结果（mutation kill rate、复杂度、token 数）使用 Friedman 检验**。两者都是配对多处理的非参数检验，假设相同任务在 A/B/C 三个 workflow 下分别运行。

**事后检验**：Cochran's Q 显著后用 **McNemar 配对检验 + Bonferroni 校正**（α/3 = 0.0167）；Friedman 显著后用 **Nemenyi 检验**（控制族错误率）或 **Conover 检验**（更有检验力但更宽松）。Python 实现使用 `scikit-posthocs` 包。

**关键功效分析结论**：

对于 15 个任务、3 个 workflow 的设计：
- **大效应量**（如 60% vs 80% 通过率，绝对差 20%）：Friedman 检验约 **80% 功效**，基本够用
- **中效应量**（如 70% vs 80%，绝对差 10%）：仅约 **50-60% 功效**，不够
- **15 个任务 × 3 次重复 = 45 个观测**：功效提升到 **85-95%** 用于大效应

**Monte Carlo 功效模拟代码**（建议在正式实验前运行）：

```python
import numpy as np
from scipy.stats import friedmanchisquare
from statsmodels.stats.contingency_tables import cochrans_q

def power_friedman(n_tasks, effect_means, n_sims=10000, alpha=0.05):
    """模拟 Friedman 检验的功效。effect_means: 各 workflow 的平均得分。"""
    sig = 0
    for _ in range(n_sims):
        data = np.random.normal(loc=effect_means, scale=1.0, size=(n_tasks, 3))
        _, p = friedmanchisquare(data[:, 0], data[:, 1], data[:, 2])
        if p < alpha:
            sig += 1
    return sig / n_sims

def power_cochran_q(n_tasks, proportions, n_sims=10000, alpha=0.05):
    """模拟 Cochran's Q 检验的功效。proportions: 各 workflow 的通过率。"""
    sig = 0
    for _ in range(n_sims):
        data = np.column_stack([
            np.random.binomial(1, p, size=n_tasks) for p in proportions
        ])
        result = cochrans_q(data)
        if result.pvalue < alpha:
            sig += 1
    return sig / n_sims

# 场景 1：15 个任务，workflow A=80%, B=60%, C=70%
print(f"Cochran Q 功效 (n=15): {power_cochran_q(15, [0.8, 0.6, 0.7]):.3f}")
# 场景 2：45 个观测（15 任务 × 3 重复）
print(f"Cochran Q 功效 (n=45): {power_cochran_q(45, [0.8, 0.6, 0.7]):.3f}")
# 场景 3：Friedman，mutation kill rate 差异 [0.85, 0.65, 0.75]
print(f"Friedman 功效 (n=15): {power_friedman(15, [0.85, 0.65, 0.75]):.3f}")
```

**最终推荐**：**20 个任务 × 3 次重复 = 60 个观测**。这在大效应量下提供 >95% 功效，在中效应量下提供 ~80% 功效。如果资源有限，15 个任务 × 3 次重复 = 45 个观测是可接受的最低配置。

### 4d. 实验控制：四重隔离机制

**（1）输入一致性**：所有 workflow 使用同一份 BMAD/GSD story 作为输入。story 质量由独立评审者在实验前盲审评分（1-5 分），评分作为混合效应模型的协变量。

**（2）LLM 随机性控制**：设置 temperature=0，但注意**这不保证确定性输出**（GPU 浮点运算的原子操作和 MoE 路由引入随机性）。学术研究显示即使贪婪解码，同一提示的 10 次运行中最大-最小准确率差异可达 **15%**。因此**3 次重复是必须的**，报告均值 + 方差。

**（3）环境隔离**：每个任务-workflow 组合从相同 git commit 开始，使用 Docker 容器或 `git worktree` 隔离。实验前记录并验证 git SHA：

```bash
#!/bin/bash
# scripts/run_experiment.sh
BASE_SHA=$(git rev-parse HEAD)
TASKS=("task_01" "task_02" ... "task_20")
WORKFLOWS=("A" "B" "C")
REPS=(1 2 3)

for task in "${TASKS[@]}"; do
  for wf in "${WORKFLOWS[@]}"; do
    for rep in "${REPS[@]}"; do
      # 创建隔离的 worktree
      git worktree add "/tmp/exp/${task}_${wf}_${rep}" "$BASE_SHA"
      cd "/tmp/exp/${task}_${wf}_${rep}"

      # 验证起始状态
      CURRENT_SHA=$(git rev-parse HEAD)
      [ "$CURRENT_SHA" != "$BASE_SHA" ] && echo "ERROR: SHA mismatch!" && exit 1

      # 运行 workflow（具体命令根据 A/B/C 不同）
      run_workflow "$wf" "$task" 2>&1 | tee "results/${task}_${wf}_${rep}.log"

      # 收集指标
      collect_metrics "$task" "$wf" "$rep"

      # 清理
      cd -
      git worktree remove "/tmp/exp/${task}_${wf}_${rep}" --force
    done
  done
done
```

**（4）顺序随机化**：使用 **Latin square 设计**——每个任务内 A/B/C 的执行顺序随机化。对于 AI workflow，虽然无"学习效应"，但上下文残留（如 Docker 缓存、模型 API 缓存）可能引入偏差。Latin square 确保每种顺序均衡分布。

```python
import random
tasks = list(range(1, 21))
workflows = ['A', 'B', 'C']
# 对每个任务随机排列 workflow 顺序
schedule = {t: random.sample(workflows, len(workflows)) for t in tasks}
```

**混合效应模型推荐结构**：

```python
# Python (pymer4) 或 R (lme4)
# 连续结果（mutation kill rate）：
# kill_rate ~ workflow + difficulty + (1 | task_id) + (1 | rep_id)
# 二值结果（pass/fail）：
# pass ~ workflow + difficulty + (1 | task_id), family=binomial
```

task_id 作为随机效应（因为这 20 个任务是从更大可能任务集合中抽样的），difficulty 作为固定效应（因为只有 3 个水平），workflow 作为固定效应（核心关注变量）。

---

## 结论：实施优先级路线图

**第一阶段（1-2 天，立即可做）**：部署 1d 的 tmux 配置和 CLAUDE.md 角色定义，加入 1b 的自动化 schema 摘要生成脚本，将现有 Workflow A 从"单次成功"升级为"有契约保障的可重复流程"。

**第二阶段（3-5 天）**：部署 1a 的 testcontainers + LanceDB 双轨 fixture 到 conftest.py，让 Workflow A 覆盖数据库集成层。同时安装 pytest-gremlins 并配置为 Stop hook（1c），替代 mutmut 作为变异测试门控。

**第三阶段（1-2 周）**：运行 4a-4d 的 20 × 3 × 3 对比实验，比较升级后的 Workflow A、GSD + Workflow A 混合方案、以及 Ralph Loop 基线。使用 Cochran's Q + Friedman 双检验分析结果。

最关键的单一改进是**将 TDAD 的依赖图分析集成到 test-writer 的上下文中**——给 test-writer 传递的不是泛泛的"请写好测试"，而是"这个修改影响了 test_graph_service.py 的 test_find_related 和 test_vector_search.py 的 test_search_by_embedding"。这个看似简单的变化在学术实证中产生了 **70% 的回归降幅**，是所有升级中投入产出比最高的一项。