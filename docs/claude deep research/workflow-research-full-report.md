# AI 编码工作流返工率研究综合报告
> Canvas Learning System（Tauri 2 + React + TypeScript + FastAPI + Neo4j + LanceDB）
> 研究时间：2026 年 4 月 | 状态：基于实测 + 文献 + 社区调研

---

## 目录

1. [核心结论：一句话版本](#一、核心结论一句话版本)
2. [问题的本质：为什么返工率降不下来](#二、问题的本质为什么返工率降不下来)
3. [Workflow A 的定义与实测成绩](#三、workflow-a-的定义与实测成绩)
4. [Workflow A 的失效边界](#四、workflow-a-的失效边界)
5. [Workflow A 升级方案](#五、workflow-a-升级方案)
6. [2026 年社区返工率最低工作流实证](#六、2026-年社区返工率最低工作流实证)
7. [混合方案：BMAD 规划 + X 执行](#七、混合方案bmad-规划--x-执行)
8. [Ralph Loop 的真实定位](#八、ralph-loop-的真实定位)
9. [对比实验设计：10-20 任务大基数测试](#九、对比实验设计10-20-任务大基数测试)
10. [工具速查：pytest-gremlins 是什么](#十、工具速查pytest-gremlins-是什么)
11. [实施路线图](#十一、实施路线图)

---

## 一、核心结论：一句话版本

> **只要测试和实现在同一个 context 里生成，LLM 就有能力、也有倾向写出镜像测试。这是返工率高的根本原因，与 prompt 质量无关。**

- BMAD 没解决这个问题——它是规划工具，没有执行层隔离
- Superpowers 试图用 prompt 压制但结构上失败了
- Workflow A 是目前唯一在架构层面切断这个路径的方案

---

## 二、问题的本质：为什么返工率降不下来

### 2.1 BMAD 的问题出在执行层

BMAD 是优秀的规划工具，PRD 质量高、粒度清晰。但它没有执行引擎——它假设 LLM 会老实按 story 实现，实际上 LLM 拿到 story 之后仍然在单一 context 里同时写实现和测试，facade 问题完全没有被解决。规划再好，执行层没有物理隔离，返工率就降不下来。

### 2.2 Superpowers 的问题出在结构性缺陷

实测结果（Workflow C 写出 `@staticmethod _compute_color` 这种 facade）已经证明了这一点。

Superpowers 的 Iron Law 是 prompt 约束，不是机械防护。Superpowers 的 plan 格式要求包含完整实现代码，subagent 在写测试时已经在 prompt 中看到了实现代码。LLM 在同一个 context 里同时看到实现意图和测试任务，它会"合理化"出一条阻力最小的路径——在测试文件里复制生产逻辑，绕过真实 import。

这不是用得不对，是架构上就防不住。Konstantinou et al. 的研究发现：**LLM 在看到实现代码时，超过 99% 的生成测试基于"实际行为"而非"期望行为"**。

### 2.3 Facade Test 的典型形态

```python
# Workflow C（Superpowers）的典型 facade 测试
class TestColorMappingOn012Scale:
    @staticmethod
    def _compute_color(total_score: float) -> str:
        """Replicate the color mapping logic from agent_service.py."""
        if total_score >= 10:
            return "2"  # green
        elif total_score >= 7:
            return "3"  # purple
        else:
            return "4"  # red

    def test_perfect_score_12_is_green(self):
        assert self._compute_color(12.0) == "2"  # 断言自己写的函数，不是生产代码
```

这个测试永远通过，但如果生产代码里重新引入 bug，它完全检测不到。**Mutation kill rate = 0%**。

---

## 三、Workflow A 的定义与实测成绩

### 3.1 架构定义

```
BMAD/GSD 规划
      ↓
test-writer Teammate（独立 tmux pane，独立 context）
      ↓ SendMessage（传递测试文件路径 + 验收标准）
implementer Teammate（独立 tmux pane，独立 context）
      ↓
mutmut / pytest-gremlins 变异测试 Stop hook
```

**核心原则**：test-writer 根本看不到实现代码，被迫写黑盒测试。

### 3.2 实测成绩（1 次对比实验）

| 指标 | Workflow A | Workflow B（基线） | Workflow C（Superpowers） |
|------|-----------|------------------|--------------------------|
| Facade 数量 | **0** | 未深入分析 | 全测试文件均为 facade |
| 真实断言数 | **84** | 未统计 | 0（全部断言自身逻辑） |
| Mutation kill rate | **通过** | 未测试 | **0%**（理论值） |
| 代码架构 | 提取独立模块 | 未分析 | 内联修改 |
| 并发测试 | 有（10并发写入） | 无 | 无 |

### 3.3 重要限制

- **样本量 N=1**，95% 置信区间为 [0.025, 1.000]，统计上几乎无意义
- 任务类型单一：局部数学 bug 修复 + 文件 IO，是 Workflow A 最擅长的场景
- 无社区大规模验证

---

## 四、Workflow A 的失效边界

### 4.1 失效场景矩阵

| 任务类型 | 失效风险 | 原因 |
|---------|---------|------|
| 纯函数 / utility 模块 | 低（优势场景） | 无依赖，真实 import 完全有效 |
| 文件 IO / 并发 | 低 | tmp_path 隔离足够 |
| LanceDB 操作 | 低 | 嵌入式模式，无需 Docker |
| FastAPI 同步端点 | 中 | TestClient 可用但有限 |
| Neo4j 操作 | **高** | 无内存替代，约 85% 概率退化为 mock |
| 大文件重构（50+文件） | **高** | test-writer 盲目性，无全局视图 |
| 前端 React + Tauri IPC | **高** | Tauri runtime 不可在 vitest 中真实启动 |
| 跨层集成任务 | **高** | 协调成本指数增长 |
| 探索性/R&D 任务 | **高** | 需求不明确时 test-first 限制创造性 |

### 4.2 "Unsatisfiable Specs" 是最高概率失败模式

AgentCoder 论文数据：**约 10% 的 test-writer 生成的测试存在错误的 test oracle**（期望值本身就是错的）。一旦 test-writer 幻觉出一个不可能实现的 API，implementer 会陷入无法收敛的死循环。

### 4.3 Neo4j 是最大退化点

Neo4j 没有内存模式，没有像 SQLite 对 PostgreSQL 那样的轻量替代品。测试 Cypher 查询的唯一替代是 mock `neo4j.Session.run()`——但这完全无法验证 Cypher 语法或语义的正确性，重新引入 facade 风险。

---

## 五、Workflow A 升级方案

### 5.1 Neo4j + LanceDB 双轨 Fixture（最优先）

```python
# conftest.py
import pytest, pytest_asyncio
from testcontainers.neo4j import Neo4jContainer
from neo4j import AsyncGraphDatabase
import lancedb, uuid

# Neo4j：session-scoped 容器，启动一次（冷启动 10-30 秒）
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
    driver = AsyncGraphDatabase.driver(
        neo4j_container.get_connection_url(),
        auth=("neo4j", neo4j_container.NEO4J_ADMIN_PASSWORD)
    )
    yield driver
    await driver.close()

# 每个测试后清空数据，不重启容器
@pytest.fixture(autouse=True)
def clean_neo4j(neo4j_container):
    yield
    with neo4j_container.get_driver().session() as s:
        s.run("MATCH (n) DETACH DELETE n")

# LanceDB：嵌入式模式，零启动成本，无需 Docker
@pytest.fixture
def lance_db(tmp_path):
    return lancedb.connect(str(tmp_path / "test_lance"))
```

### 5.2 test-writer 的 Schema 摘要自动生成

不给 test-writer 看实现代码，但给它看接口契约：

```bash
# 自动生成 Python 类型存根
stubgen -p canvas_app.services -p canvas_app.models \
    --include-docstrings -o .claude/contracts/stubs/

# 自动生成 FastAPI OpenAPI 契约
python -c "
from canvas_app.main import app
import json
contract = {'paths': app.openapi()['paths'],
            'schemas': app.openapi().get('components',{}).get('schemas',{})}
open('.claude/contracts/api_contract.json','w').write(json.dumps(contract,indent=2))
"
```

### 5.3 Facade 自动检测器

```python
#!/usr/bin/env python3
# scripts/detect_facade.py
import ast, os, sys

class FacadeDetector(ast.NodeVisitor):
    def __init__(self):
        self.warnings = []

    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            self.generic_visit(node)
            return
        # 非测试函数出现在测试文件里 = 疑似 facade
        body = [n for n in node.body
                if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        if len(body) > 2:
            self.warnings.append(
                f"⚠️ FACADE: 测试文件中定义了非测试函数 '{node.name}' "
                f"(第 {node.lineno} 行, {len(body)} 条语句)"
            )
        self.generic_visit(node)

if __name__ == "__main__":
    all_warnings = []
    for root, _, files in os.walk("tests"):
        for f in files:
            if f.startswith('test_') and f.endswith('.py'):
                path = os.path.join(root, f)
                detector = FacadeDetector()
                detector.visit(ast.parse(open(path).read()))
                for w in detector.warnings:
                    all_warnings.append(f"{path}: {w}")
    for w in all_warnings:
        print(w)
    sys.exit(2 if all_warnings else 0)
```

### 5.4 变异测试 Stop Hook

```bash
#!/bin/bash
# .claude/hooks/mutation_gate.sh
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | grep -v 'test_')
if [ -z "$CHANGED_FILES" ]; then exit 0; fi

echo "🧬 运行变异测试..." >&2

# 优先用 pytest-gremlins（快 3-13x）
if python -m pytest --gremlins --gremlin-parallel --gremlin-workers=4 \
    --gremlin-paths="$CHANGED_FILES" 2>/dev/null; then
    exit 0
fi

# 降级到 mutmut（更成熟稳定）
mutmut run --paths-to-mutate "$CHANGED_FILES" --CI
if [ $? -ne 0 ]; then
    echo "❌ 变异体存活过多，需加强测试" >&2
    exit 2  # exit 2 阻止 Claude 停止
fi
```

### 5.5 Agent Teams 完整配置

**.claude/settings.json**：
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "Stop": [{
      "hooks": [{"type": "command", "command": "bash .claude/hooks/mutation_gate.sh"}]
    }],
    "TaskCompleted": [{
      "hooks": [{"type": "command", "command": "python scripts/detect_facade.py"}]
    }]
  }
}
```

**~/.tmux.conf**（必须配置）：
```bash
set -g base-index 1
setw -g pane-base-index 1     # Claude Code Agent Teams 依赖此设置
set -g mouse on
set -sg escape-time 0
```

**test-writer 的 CLAUDE.md**：
```markdown
# Test Writer 角色

## 严格禁止
- ❌ 不读取 src/ 下的实现文件
- ❌ 不在测试文件内定义 @staticmethod 复制生产逻辑
- ❌ 不使用 unittest.mock.patch 替代真实 import

## 必须遵守
- ✅ 只参考 .claude/contracts/ 下的接口契约
- ✅ 所有被测函数必须 from canvas_app.xxx import yyy 真实导入
- ✅ 使用 conftest.py 中的 fixture（neo4j_driver, lance_db）
```

### 5.6 Tauri 前端测试边界

| 层级 | 工具 | Workflow A 适用性 |
|------|------|-----------------|
| React 纯逻辑 hooks | Vitest + RTL | ✅ 完全适用 |
| IPC 调用契约 | Vitest + mockIPC | ✅ 适用，需共享类型契约 |
| Rust 命令实现 | cargo test | ⚠️ 独立流程 |
| 全链路 E2E | tauri-driver | ❌ 绕过 A 的隔离，用独立 E2E |

---

## 六、2026 年社区返工率最低工作流实证

### 6.1 学术数据（带条件限制）

| 工作流 | 数据 | 真实条件 | 证据强度 |
|--------|------|---------|---------|
| TDFlow (CMU, arXiv:2510.23761) | SWE-bench Verified 94.3% | **前提：人工写好测试**；自主模式仅 68% | 中 |
| AgentCoder (arXiv:2312.13010) | HumanEval 96.3% pass@1 | **仅适用单函数任务**，不是仓库级 | 强（基准局限） |
| TDAD (arXiv:2603.17973) | 回归率降低 70% | SWE-bench 100实例；泛泛TDD指令反而恶化至9.94% | 中（待复现） |

**TDAD 的关键洞察**：给 test-writer 传递受影响的测试列表（AST 依赖图），比给它"请写好测试"的指令有效得多。这是投入产出比最高的单一改进。

### 6.2 社区验证工作流现状

| 工具 | Stars | 实际效果 | 可信度 |
|------|-------|---------|-------|
| GSD（get-shit-done） | 39,800 | ≤3任务/计划，上下文工程，社区普遍正面 | 中（无量化） |
| disler/claude-code-hooks-mastery | ~2,200 | Builder/Validator hooks 模式，可复用脚本 | 中 |
| swingerman/atdd | 小众 | 双流测试（验收+单元），Uncle Bob 背书 | 弱（社区小） |
| snarktank/ralph | ~13,900 | 机械性任务有效，复杂任务无效 | 中（轶事为主） |

### 6.3 有社区验证、有证据的最低返工率组合（仅 3 个）

**① Ralph Loop + testcontainers 集成测试门**
机械性任务的社区实战验证，最简单可落地。

**② TDAD 依赖图注入 + 任意执行引擎**
学术实证 70% 回归降幅，代码开源可用（`pip install tdad`）。

**③ BMAD V6 规划 + Ralph Loop 执行**
bmalph 桥接工具存在，两者均有大量用户。

> ⚠️ 其余组合均为基于工程逻辑的设计推断，无社区大规模验证。

---

## 七、混合方案：BMAD 规划 + X 执行

### 7.1 BMAD → Ralph 的转换

`bmalph`（github.com/LarsCowe/bmalph）是已存在的 CLI 桥接工具：

```bash
bmalph init --name canvas-learning-system
# 使用 BMAD agent 完成规划
bmalph implement    # 自动将 BMAD artifacts → Ralph prd.json
bmalph run          # 启动 Ralph 循环
```

**核心问题**：BMAD stories 是特性级作用域，Ralph 要求每个 story 在一个上下文窗口内完成。bmalph 通过 Scrum Master agent 执行"epic 分片"解决此问题，但质量参差不齐。

### 7.2 推荐的最终混合方案

```
GSD discuss/plan → PLAN.md（每计划 ≤ 3 任务）
       ↓
为每个任务自动生成 Interface Contract
（stubgen + OpenAPI + CONTEXT.md）
       ↓
Workflow A 执行（test-writer → implementer 物理隔离）
       ↓
pytest-gremlins 变异测试 Stop hook
       ↓
TDAD 风格依赖图注入（精准定位受影响测试）
       ↓
Facade 静态检测（AST 比对）
```

**为什么 GSD 优于 BMAD 作为规划层**：
- GSD 的 PLAN.md 天然限制每计划 ≤ 3 个任务，与 Workflow A 的 1-3 文件限制契合
- GSD 的"目标反向验证"（什么必须为 TRUE）直接映射为测试断言
- 不需要 bmalph 这类额外转换工具

### 7.3 理论推断的返工率排序

| 排名 | 组合 | 核心防护层 |
|------|------|-----------|
| 1 | GSD → TDAD注入 → Workflow A → pytest-gremlins + disler hooks | 四层防护 |
| 2 | GSD → Workflow A → pytest-gremlins + disler hooks | 三层防护 |
| 3 | GSD → TDAD注入 → Workflow A → ATDD双流 → mutmut | 最严格，配置成本最高 |
| 4 | Ralph Loop外层 → TDAD注入 → Workflow A内层 → pytest-gremlins | 互补嵌套 |
| 5 | GSD → Workflow A → mutmut（最小可行版本） | 今天可落地 |

> 以上均为理论推断，未经大规模社区验证。

---

## 八、Ralph Loop 的真实定位

### 8.1 你对 Ralph Loop 的理解需要纠正

**错误理解**：同一个 plan 重复跑，产出更好的代码。

**正确理解**：plan 是状态机，不是重复执行的模板。每次循环推进状态机往前走**一步**，完成一个 story，标记为完成，然后退出。下一次循环找下一个未完成的 story。

提高的不是代码质量，而是**上下文新鲜度**——每次循环从零开始读规格说明，不被之前的失败尝试污染。

### 8.2 Ralph Loop 运行逻辑示例（Jest→Vitest 迁移）

```
第1次循环
  ├─ 清空上下文（不记得之前做过什么）
  ├─ 读 prd.json → 找到 US-001（安装 Vitest，删除 Jest 依赖）
  ├─ 执行任务
  ├─ 跑测试：通过 ✅
  ├─ US-001.passes = true
  └─ 退出

第2次循环
  ├─ 清空上下文（不记得第1次）
  ├─ 读 prd.json → US-001已完成，找到 US-002（迁移 tests/scoring/）
  ├─ 执行任务
  ├─ 跑测试：失败 ❌（漏了一个 jest.mock）
  ├─ 修复，再跑测试：通过 ✅
  ├─ US-002.passes = true
  └─ 退出
```

### 8.3 Ralph Loop 适用 vs 不适用

| 场景 | Ralph Loop 效果 | 原因 |
|------|----------------|------|
| 机械性迁移（Jest→Vitest、linting） | ✅ 好 | 满足三个条件 |
| 测试覆盖率提升 | ✅ 好 | 有机器可验证的完成标准 |
| **修 Bug** | ❌ 差 | 推理链断裂，每次循环盲目探索 |
| **自主 TDD（自己写测试再实现）** | ❌ 差 | context 未隔离，facade 风险极高 |
| 人工写好测试后让 Ralph 实现 | ✅ 好 | 等价于 TDFlow 的人工测试条件 |
| 复杂架构设计 | ❌ 差 | 跨循环架构意图无法保持 |

### 8.4 Ralph Loop 修 Bug 为什么不行

```
第1次循环：猜一个修法，测试通过（但测试可能本来就没覆盖这个边界）→ 标记完成

或者：

第1次循环：改了 A，测试失败
第2次循环：不记得第1次改了什么，又改了 B，还是失败
第3次循环：不记得前两次，改了 C……
```

根本矛盾：**bug 修复需要跨步骤的诊断推理，Ralph 每次清空上下文，推理链无法延续。**

### 8.5 Ralph Loop 配合 TDD

| 情况 | 效果 | 原因 |
|------|------|------|
| 人工先写好失败测试，Ralph 负责让测试通过 | ✅ 好 | 测试本身就是精确 spec + 机器可验证 |
| Ralph 自己写测试再写实现（纯自主 TDD） | ❌ 差 | 测试和实现在同一 context，facade 必然出现 |

**结论：在 TDD 场景里，Workflow A 严格优于 Ralph。** Ralph 解决的是上下文腐烂问题，而 Workflow A 的每个 Teammate 本来就有独立的新鲜上下文，Ralph 没有额外价值。

### 8.6 2026 年 Ralph Loop 的命运：被平台吸收

Claude Code 2.0 已引入 `/loop` 命令、Auto Mode、`/schedule` 云端定时任务。Cursor 推出 Background Agents（最多 8 个并行）。**Ralph Loop 的核心模式正在从社区 hack 变为平台级功能**，外部脚本的必要性在降低。

---

## 九、对比实验设计：10-20 任务大基数测试

### 9.1 任务分层矩阵（共 18-21 个任务）

| 层级 | 复杂度 | 示例任务 | 数量 | 目标失效模式 |
|------|--------|---------|------|-------------|
| L1 纯函数 | 简单 | scoring_utils 新增规则 | 3 | 基线 |
| L2 单层 IO | 简单 | 文件写入工具函数 | 3 | Facade 诱导 |
| L3 单数据库 | 中等 | Neo4j CRUD + Cypher 优化 | 3 | Unsatisfiable spec |
| L4 跨层 | 中等 | FastAPI + Neo4j + 向量搜索 | 4 | Context contamination |
| L5 前端 | 中等 | React + Tauri IPC 组件 | 3 | IPC mock 质量 |
| L6 全栈 | 困难 | 端到端知识图谱创建 | 3 | 综合失效 |

### 9.2 三类陷阱任务（必须包含）

- **Facade 诱导**：要求修复 scoring bug，但 spec 故意只描述输入输出、不指明具体函数
- **Unsatisfiable spec**：要求函数"同时返回按相关度和按时间排序的结果"（自相矛盾）
- **Context contamination**：仓库中放置使用旧 API 约定的模块，测试 workflow 是否被污染

### 9.3 评估指标

| 指标 | 类型 | 工具 | 权重 |
|------|------|------|------|
| Mutation kill rate | 连续 (0-100%) | pytest-gremlins | **主指标** |
| 功能正确性 | 二值 | pytest | 基本门槛 |
| Facade 检测 | 二值 | AST 静态分析 | 关键 |
| 是否提取独立模块 | 二值 | 人工审查 | 代码质量 |
| Token 消耗 | 连续 | API 日志 | 效率 |
| Implementer 重试次数 | 计数 | 日志 | 返工率 |

### 9.4 统计方法

- 二值结果（pass/fail、有无 facade）：**Cochran's Q 检验**
- 连续结果（mutation kill rate）：**Friedman 检验**
- 事后检验：McNemar 配对检验 + Bonferroni 校正（α/3 = 0.0167）

**功效分析**：
- 15 个任务 × 3 次重复 = 45 对配对，大效应量（20% 差异）约 80% 功效
- **推荐 20 个任务 × 3 次重复 = 60 对**，大效应量 >95% 功效

### 9.5 实验控制

```bash
# 每个任务从相同 git 状态开始
BASE_SHA=$(git rev-parse HEAD)

for task in "${TASKS[@]}"; do
  for wf in A B C; do
    for rep in 1 2 3; do
      git worktree add "/tmp/exp/${task}_${wf}_${rep}" "$BASE_SHA"
      # 运行对应 workflow
      # 收集指标
      git worktree remove "/tmp/exp/${task}_${wf}_${rep}" --force
    done
  done
done
```

- temperature=0（不保证确定性，但减少随机性）
- Latin square 随机化 A/B/C 执行顺序
- task_id 作为混合效应模型的随机效应

---

## 十、工具速查：pytest-gremlins 是什么

pytest-gremlins 是一个 pytest 插件，和 mutmut 做同样的事——故意修改生产代码，检测测试能否发现。

**比 mutmut 快的原因**：mutmut 每次修改都写磁盘再重新加载模块。pytest-gremlins 用 AST 插桩——一次性嵌入所有变异，通过环境变量切换，无磁盘 I/O，支持并行。

**性能对比**（作者自测数据，未独立验证）：

| 模式 | 时间 | vs mutmut |
|------|------|-----------|
| 顺序模式 | 17.79s | 0.84x（略慢） |
| 并行模式 | 3.99s | **3.73x 快** |
| 并行 + 热缓存 | 1.08s | **13.82x 快** |

**注意**：GitHub 约 15 stars，成熟度不高。如果遇到问题，mutmut 是更稳妥的备选。

**"Stop hook 门"的含义**：配置为 Claude Code 的 Stop 事件钩子。存活变异体超过阈值（5%），脚本返回 exit code 2，Claude Code 不允许停止，强制 agent 继续修改测试直到通过。

---

## 十一、实施路线图

### 第一阶段（1-2 天，立即可做）

1. 部署 `~/.tmux.conf` 的 pane-base-index 配置
2. 部署 `.claude/settings.json` 的 Agent Teams 配置
3. 写好 test-writer 和 implementer 的 CLAUDE.md 角色定义
4. 运行 `stubgen` 生成初始 interface contract

**目标**：把现有 Workflow A 从"单次成功"升级为"有契约保障的可重复流程"

### 第二阶段（3-5 天）

1. 部署 testcontainers + LanceDB 双轨 fixture 到 conftest.py
2. 安装 pytest-gremlins，配置 Stop hook
3. 部署 facade 静态检测器到 TaskCompleted hook

**目标**：覆盖数据库集成层，mutation testing 自动化

### 第三阶段（1-2 周）

运行 20 × 3 × 3 对比实验（Workflow A vs GSD+A 混合 vs Ralph 基线），用 Cochran's Q + Friedman 双检验分析。

**目标**：获得统计显著的实验结论，决定是否值得继续投入 Workflow A

---

## 结语

继续优化 BMAD story 粒度或 Superpowers 的 Iron Law 强度，是在错误的层面解决问题。

**返工率的根因在 context 隔离，不在 prompt 质量。**

最关键的单一改进：把 TDAD 的依赖图分析集成到 test-writer 的初始 context——不是"请写好测试"，而是"这个修改影响了 test_graph_service.py 的 test_find_related 和 test_vector_search.py 的 test_search_by_embedding"。这个看似简单的变化，在学术实证中产生了 70% 的回归降幅。

---

*报告版本：v1.0 | 2026-04-02 | 基于实测对比 + arXiv 文献 + 社区调研综合*
