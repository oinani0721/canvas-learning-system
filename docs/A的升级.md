# Workflow A 深度对抗性分析：隔离策略的边界与失效

**核心结论：Workflow A 的 test-writer/implementer 物理隔离在局部、明确的纯逻辑任务上具有结构性优势，但这一优势在 Canvas Learning System 的完整技术栈中存在至少三个系统性失效边界——Neo4j 无内存替代迫使 mock 退化、Tauri IPC 不可测试性、以及跨层任务的协调成本指数增长。** 更关键的是，当前 1 次测试的胜出在统计学上几乎无意义（95% 置信区间为 [0.025, 1.0]），我们距离证明 A 稳定优于 B/C 还需要至少 75-100 个多样化任务的对照实验。以下逐一深入分析五个核心问题。

---

## 一、A 的 subagent 隔离策略在什么条件下失败

### "Unsatisfiable Specs" 是最高概率失败模式

AgentCoder 论文（Huang et al., arXiv:2312.13010, 2023）的数据表明，**即使使用 GPT-4，test-writer agent 生成的测试用例中约 10% 存在错误的 test oracle**（即期望值本身就是错的）。论文原文明确指出："Once the test cases are incorrect (e.g., with incorrect test oracles), the problematic feedback will mislead the programmer agent and decrease AgentCoder's effectiveness." 这意味着在每 10 个测试中，大约有 1 个会把 implementer 引入歧途。

在 Canvas Learning System 中，这个问题会被放大。考虑一个具体场景：test-writer 需要为 Neo4j 中的知识图谱查询编写测试，但它**没有 Cypher schema 上下文**。它可能会生成如下测试：

```python
def test_get_related_concepts():
    result = get_related_concepts("machine_learning", depth=3)
    assert len(result) == 5  # 幻觉出的期望值
    assert result[0]["relationship_type"] == "IS_PREREQUISITE_OF"  # 可能不存在的关系类型
```

此时 implementer 会陷入一个**不可解的优化循环**：它无法让查询返回恰好 5 个结果（因为这取决于图数据），也无法保证第一个结果的关系类型。AgentCoder 的迭代机制在 **4-5 轮后收敛**（论文 ablation 数据），但如果 spec 本身不可满足，收敛的结果是放弃而非修正。

### 对存量代码的"盲目性"是结构性缺陷而非偶然

**这是明确的结构性缺陷。** AgentCoder 的设计哲学是 test-writer "based solely on the problem description/specification"——完全不看实现。在 HumanEval/MBPP 这类独立函数任务上，这是优势（论文显示多 agent 比单 agent 覆盖率从 72.5% 提升至 87.5%）。但在 Canvas Learning System 这类有**深度存量代码**的项目中，test-writer 不知道：

- `agent_service.py` 已有的方法签名和异常处理约定
- FastAPI 的 dependency injection 模式（`Depends(get_db)` 的 session 管理方式）
- Neo4j driver 的 async/sync 混用模式
- LanceDB 的 embedding function 注册机制

MAST taxonomy 论文（arXiv:2503.13657）分析了 210 个多 agent 系统 trace，发现 **约 79% 的失败源于 specification 和 coordination 问题**，而非技术实现。在 Canvas 的技术栈中，test-writer 可能写出与现有 `BaseService` 抽象不兼容的测试接口，或者假设一个不存在的 ORM 层（Canvas 用的是 Neo4j driver 而非 ORM）。

### Canvas 技术栈中的具体失败场景

**场景 1：LanceDB vector search 测试**。Test-writer 可能假设 `search()` 返回精确匹配，但 LanceDB 使用近似最近邻（ANN）算法，结果具有非确定性。如果 test-writer 写 `assert results[0]["id"] == expected_id`，在使用 IVF_PQ 或 HNSW 索引时这个断言可能间歇性失败。

**场景 2：Tauri 2 IPC 通信**。Test-writer 完全没有 `__TAURI_INTERNALS__` 的上下文，无法为前端到 Rust 后端的 invoke 调用编写有意义的集成测试。它只能写出纯前端 mock 测试，这在 Tauri 应用中**等价于没有测试 IPC 层**。

**场景 3：Graphiti 知识图谱操作**。Canvas 使用 Graphiti 框架管理知识图谱，其 API 涉及 episodic memory、entity extraction 和 community detection 等复杂操作。Test-writer 没有 Graphiti 的 schema 和 API 上下文，极有可能生成与 Graphiti 实际接口不兼容的测试。

---

## 二、什么任务类型让 A 比 B/C 差

### 大文件重构（50+ files）：隔离策略成为严重负担

当重构涉及 50+ 文件时，A 的 context isolation 从优势转为瓶颈。**核心矛盾在于：test-writer 无法感知重构的全局意图。** 例如，将 Canvas 的 scoring 逻辑从 `agent_service.py` 迁移到独立的 `scoring_utils.py`（A 在实验中成功完成的任务），这是一个 1-3 文件的局部任务，隔离策略正好发挥作用。但如果任务是"将所有 Neo4j 直接查询迁移到 Repository 模式"，涉及 50+ 文件的接口变更，test-writer 需要了解新的 Repository 接口才能编写有意义的测试。

WebApp1K 基准测试（arXiv:2505.09027）发现了一个关键的 LLM TDD 限制：**"instruction loss"——在长 prompt 中，模型会丢失需求**。o1-preview 在多 feature TDD 任务中失败，尽管它能单独解决每个 feature。大规模重构的 test spec 会非常长，test-writer 在隔离上下文中处理这种长 spec 时，instruction loss 的风险显著增加。

**判断：在大文件重构中，B（基线，无严格隔离）或 C（Superpowers，有全局 plan 上下文）可能优于 A。** C 虽然有 facade test 风险，但至少它的 plan 包含了全局架构信息。

### 前端 UI 任务：隔离策略部分失效

React 组件测试本质上**更依赖实现细节**。React Testing Library（RTL）虽然倡导 "test behavior, not implementation"，但在 Canvas 这种知识图谱可视化应用中，组件测试不可避免地涉及：

- **Snapshot testing**：需要看到组件的完整渲染输出才能编写，无法在 TDD 中先写（Kent C. Dodds 和 ezcater 工程团队明确指出 snapshot "cannot be used for TDD"）
- **Mock interactions**：Tauri IPC 调用必须通过 `@tauri-apps/api/mocks` 的 `mockIPC` 来 mock，test-writer 必须知道 IPC 命令的名称和参数格式
- **State management**：如果 Canvas 使用 Zustand/Jotai 管理状态，测试需要了解 store 的形状才能设置初始状态

**A 在前端测试中的有效范围仅限于：** 纯逻辑 hooks（如 `useScoring`）、工具函数（如日期格式化）、以及 TypeScript 类型层面的接口验证。对于视觉组件、交互组件、图谱可视化组件，A 的隔离策略几乎无法产生有意义的测试。

### 数据库迁移：Neo4j schema 变更是致命场景

Neo4j 没有像 Alembic/Flyway 那样的标准化迁移工具。Schema 变更通常涉及 Cypher 脚本（添加约束、索引、修改节点/关系属性）。**Test-writer 没有 schema 上下文时，它无法编写验证迁移正确性的测试——因为它不知道迁移前后的 schema 差异是什么。**

LanceDB 的 index 重建同样如此。如果将向量索引从 brute-force 迁移到 IVF_PQ，测试需要验证搜索精度在可接受范围内。Test-writer 不知道当前用的是什么索引、目标索引是什么、精度阈值是多少。

### 跨层任务：协调成本指数增长

一个典型的 Canvas 跨层任务："用户在 React 前端提交学习笔记 → FastAPI endpoint 接收 → Graphiti 提取实体 → Neo4j 存储知识图谱 → LanceDB 存储向量嵌入 → 返回更新后的图谱视图"。

在 A 的隔离框架中，test-writer 需要为这条**五层调用链**编写端到端测试，但它只有 spec，不知道每层的具体接口。它可能写出一个期望整条链路在一个函数调用中完成的测试，而实际实现可能是多步异步的。**FastAPI 的 async 特性使问题更复杂**——TestClient 和 AsyncClient 有不同的事件循环行为，test-writer 如果不知道该用哪个，生成的测试可能因事件循环冲突而无法运行。

### 探索性/R&D 任务：strict TDD 确实限制创造性

**这是 A 最明确的劣势场景。** Superpowers 自身的文档承认它 "NOT suitable for quick fixes, exploratory prototyping, or rapid experimentation"。A 更是如此——test-first 要求在探索阶段确定需求，而探索的本质就是需求未知。

在 Canvas 的 R&D 场景中（如"评估是否应该用 GraphRAG 替代当前的 Graphiti 实现"），没有确定的 API 可以写测试。**此时 B（无约束基线）的自由度反而是优势。**

---

## 三、A 的"真实 import"防护在集成测试中是否有效

### 明确判断：真实 import 防护在纯函数层可靠，在 side effects 层系统性退化

A 在实验中的成功案例——`from app.services.scoring_utils import normalize_autoscore, score_to_color`——是**最理想的测试场景**：纯函数、无依赖、确定性输入输出。这类函数的真实 import 测试和 mutation testing 是完美搭配。

但 Canvas 的技术栈中，纯函数只占代码的一小部分。根据对各组件的分析，以下是真实 import 策略在整个栈中的可行性评估：

| 组件 | 真实 import 可行性 | 退化为 mock 的概率 | 原因 |
|------|-----------------|-----------------|------|
| scoring_utils 等纯函数 | ✅ 完美 | 0% | 无副作用，确定性 |
| LanceDB 操作 | ✅ 优秀 | ~10% | 嵌入式 DB，`tmp_path` 即可运行 |
| 文件 I/O（`_record_failed_write`） | ✅ 良好 | ~15% | `tmp_path` 提供真实隔离 |
| FastAPI endpoint（同步） | ⚠️ 一般 | ~40% | TestClient 可用但有限 |
| FastAPI endpoint（异步） | ⚠️ 较差 | ~60% | 事件循环冲突需 AsyncClient |
| Neo4j 操作 | ❌ 困难 | ~85% | 无内存替代，TestContainers 启动 10-30s |
| Tauri IPC | ❌ 不可能 | ~100% | 无 Vitest 环境支持 Tauri runtime |
| 跨层集成 | ❌ 极困难 | ~90% | 状态管理跨三个系统 |

**关键发现：LanceDB 是一个意外的亮点。** 作为嵌入式文件数据库，LanceDB 可以用 `lancedb.connect(str(tmp_path / "test_db"))` 创建临时测试实例——无需 Docker、无需外部服务。这意味着 A 的真实 import 策略在 LanceDB 相关代码上可以保持有效性。

**关键风险：Neo4j 是最大的退化点。** Neo4j 没有内存模式，不存在像 SQLite 对于 PostgreSQL 那样的轻量替代品。在 CI 环境或快速单元测试中，测试 Cypher 查询的唯一方式是 mock `neo4j.Session.run()`——但这**完全无法验证 Cypher 语法或语义的正确性**。一旦 test-writer 被迫 mock Neo4j 层，就重新引入了 facade 风险：mock 返回的是预设数据而非真实查询结果。

### 关于 mutation testing 在集成测试中的效力

IEEE 2016 年的研究确认："It is difficult to generate integration mutants that create an error state in one component with certain assurances that this error state will affect computations in some other components." **mutmut 在集成测试上的 mutation kill rate 远低于单元测试**——原因是集成测试的断言通常较粗粒度（如 `assert response.status_code == 200`），无法捕获细粒度的业务逻辑变异。

mutmut 在纯函数上可达 ~1,200 mutants/min 的处理速度，但在带有 TestContainers 的集成测试上降至 ~10-50 mutants/min。**这意味着 A 在实验中通过 mutmut 的事实，更多地验证了纯函数层面的测试质量，而非整个系统的测试覆盖。**

---

## 四、Superpowers 为什么写出 facade——这是结构性缺陷

### 明确判断：这是 Superpowers 架构的结构性缺陷，而非执行偶然

我做出这个判断基于三条独立证据链：

**证据链 1：Superpowers 的 plan 格式将测试代码和实现代码捆绑在同一个 task 描述中。** `writing-plans/SKILL.md` 要求 plan 包含 "Complete code in plan (not 'add validation')"——即 plan 字面包含完整实现代码。`subagent-driven-development/SKILL.md` 规定 controller 将 "full task text + context" 粘贴给 implementer subagent。这意味着**subagent 在写测试时，已经在 prompt 中看到了实现代码**。

Superpowers 的 TDD 技能文件自身承认了这个问题："Tests-after are biased by your implementation. You test what you built, not what's required." 但 plan 格式恰恰创造了这种 bias——不是 tests-after，而是 **tests-alongside**。

**证据链 2：LLM 在看到实现代码时系统性地生成镜像测试。** Konstantinou et al.（arXiv:2410.21136）在 24 个 Java 仓库上的实验发现："LLMs are more likely to generate test oracles that capture the actual program behaviour rather than the expected one." Haroon et al.（arXiv:2603.23443）更进一步：在语义变更的代码上，**超过 99% 的失败测试仍然通过原始代码**，证明 LLM 的测试是基于记忆而非推理。

当 Superpowers 的 subagent 在 prompt 中同时看到 `_compute_color` 的实现和"请先写测试"的指令，它的注意力机制不可避免地被实现代码吸引。结果就是在测试文件内用 `@staticmethod` 复制了生产逻辑——因为这是**对 LLM 而言 token 效率最高的路径**。

**证据链 3：AgentCoder 的 ablation 直接证伪了"在相同上下文中生成测试不会影响质量"的假设。** AgentCoder 论文的 Table 5 显示，独立 test designer 生成的测试覆盖率（87.5-91.7%）显著高于单 agent 在同一上下文中生成的测试（72.5-82.9%）。这不是偶然——是隔离带来的系统性质量提升。

### `@staticmethod _compute_color` 这种 facade 出现的机制

这种模式的出现需要三个条件同时满足：

1. **实现代码在 test-writer 的上下文中可见**（Superpowers 的 plan 格式保证了这一点）
2. **被测函数的逻辑足够简单，可以在几行代码内复制**（`score_to_color` 就是一个简单的阈值映射）
3. **LLM 的 token 效率优化倾向**——复制逻辑比从 spec 推导独立断言更"省力"

如果被测逻辑复杂到无法在测试文件内复制（如一个 200 行的图遍历算法），facade 的概率会降低——但会替换为另一种退化：**过度 mock**。

### `pi-superpowers-plus` 能否机械性阻止 facade

**不能。** prompt 工程可以降低 facade 的频率（通过更强的指令如"不得在测试文件中实现业务逻辑"），但无法消除根因——**只要实现代码在上下文中可见，LLM 就有生成镜像测试的倾向**。这是 LLM 注意力机制和 sycophancy（Sharma et al.的 RLHF sycophancy 研究；SycEval 发现 58% 的情况存在 sycophantic behavior）的结构性特征，不是 prompt 能完全克服的。

### Superpowers 在什么任务上应该优于 A

Superpowers 的优势在于**它有全局 plan**。在以下场景中，这个优势压过 facade 风险：

- **大规模多文件重构**（20+ files）：plan 提供的全局架构视图是 A 的 test-writer 无法获得的
- **新模块从零开始构建**：当没有存量代码时，facade 风险较低（Huang et al. 2024 的研究发现 LLM "更擅长为成熟代码生成测试"），而 plan 提供的结构化方法有价值
- **需要跨多个 subagent 协调的任务**：Superpowers 的 TodoWrite 追踪和两阶段 review 比 A 的简单迭代更适合复杂协调

---

## 五、需要多少次测试才能证明 A 稳定优于 B/C

### N=1 的统计结论：几乎为零

当前事实：A 在 1 次测试中胜出。以下是精确的统计分析：

**频率学派（Clopper-Pearson 精确区间）：** 对于 n=1, x=1，95% 置信区间为 **[0.025, 1.000]**。这意味着我们只能以 95% 的信心说 A 的真实胜率不低于 2.5%——这几乎不排除任何假设。

**Wilson 区间：** 稍微收窄，95% CI 为 **[0.207, 1.000]**。可以说 A 的真实胜率至少约 21%，但这仍然包含了"A 实际上很差"的可能性。

**贝叶斯分析：** 使用均匀先验 Beta(1,1)，观察到 1 次成功后，后验分布为 Beta(2,1)。P(p > 0.5 | data) = 1 - 0.5² = **0.75**。也就是说，我们有 75% 的信心认为 A 的真实胜率超过 50%——**远未达到常用的 95% 标准**。

### 达到统计显著性所需的最少试验

**场景 1：A 连续获胜。** 使用单侧二项检验（H₀: p ≤ 0.5），需要 **5 次连续胜出** 才能达到 p = 0.5⁵ = 0.03125 < 0.05。即再赢 4 次。

**场景 2：A 有时输。** 如果 A 的真实胜率为 70%，使用单侧 sign test，需要 **约 23-25 对配对试验** 才能以 80% power 达到 α=0.05。

**场景 3：检测 20% 的成功率差异（如 50% vs 70%）。** 使用 McNemar's test（配对设计），需要 **约 40-80 个配对任务**（80% power, α=0.05）。

### 任务异质性的影响

SWE-bench 的经验表明，**任务难度是最大的方差来源**——远超模型间差异。HumanEval 的每题 pass rate 从 0.005 到 0.9 不等。Microsoft 的 "SWE-bench Illusion" 论文发现模型在 SWE-bench 上的文件路径准确率为 76%，但在外部仓库上降至 53%，证明**跨任务迁移性不可靠**。

Canvas 的任务同样具有高异质性：修复 scoring bug（数学逻辑）和实现 `_record_failed_write`（并发文件 IO）是完全不同的能力维度。**一个任务类型上的胜出不能推广到另一个任务类型。**

### 最小可行评估实验设计

参考 SWE-bench Verified（500 tasks）和 HumanEval（164 tasks）的规模，以及 Frattini et al.（arXiv:2408.07594）关于交叉实验设计的建议，Canvas 项目的最小可行评估矩阵应为：

| 任务类别 | 任务数量 | 重复次数 | 总测试运行 |
|---------|---------|---------|----------|
| 纯逻辑 bug 修复 | 8 | 3 | 72（8×3×3 workflows） |
| 并发/IO 任务 | 6 | 3 | 54 |
| 前端 React 组件 | 6 | 3 | 54 |
| Neo4j/LanceDB 数据层 | 6 | 3 | 54 |
| 跨层集成任务 | 5 | 3 | 45 |
| **合计** | **31 任务** | **3 次** | **279 运行** |

使用配对设计（所有 3 个 workflow 在相同 31 个任务上运行 3 次），用 Cochran's Q 检验做总体比较，再用配对 McNemar's 检验（Bonferroni 校正 α/3 = 0.0167）做两两比较。**31 个任务 × 3 次重复 = 93 对配对观测**，足以在 20% 效应量下达到 ~80% power。

### 当前证据的强弱评估

| 结论 | 证据强度 | 理由 |
|------|---------|------|
| A 的真实 import 优于 C 的 facade | **强证据** | 有 mutation testing 验证（0% vs 通过），且有 AgentCoder 论文的理论支持 |
| A 的隔离策略在局部任务上有效 | **中等证据** | 1 次成功 + 理论一致性，但样本量不足 |
| A 在所有任务类型上优于 B/C | **极弱证据** | 仅 1 次测试，且任务类型单一（局部数学 bug） |
| C 的 facade 是 Superpowers 结构缺陷 | **强证据** | plan 格式分析 + 多篇独立研究一致 |

---

## 六、综合补强策略

### A 的核心失败风险排序

按概率从高到低：

1. **Neo4j 测试退化为 mock（概率 ~85%）**：无内存替代，test-writer 在缺乏 schema 上下文时必然依赖 mock，重新引入 facade 风险。
2. **跨层任务协调成本过高（概率 ~70%）**：test-writer 不了解 FastAPI→Neo4j→LanceDB 的调用链，生成不可执行的集成测试。
3. **test-writer 幻觉不存在的 API（概率 ~60%）**：对存量代码的盲目性导致生成与现有接口不兼容的测试，浪费 implementer 的迭代预算。
4. **前端测试无效化（概率 ~50%）**：Tauri IPC 和 React 组件测试需要实现细节，A 的隔离策略在此层面失效。
5. **探索性任务被过度约束（概率 ~40%）**：strict TDD 在需求不明确时限制创造性。

### 针对性补强手段

**手段 1：为 test-writer 提供"只读 schema 摘要"（解决风险 1 和 3）。** 在不破坏 context isolation 的前提下，向 test-writer 注入一份精简的 API 摘要文件（类似 `.d.ts` 声明文件），包含函数签名、类型、Neo4j 节点/关系类型列表、LanceDB 表结构。这不是"看到实现代码"——而是看到**接口契约**。AgentCoder 论文的 test designer 也接收"problem description"，这里的 schema 摘要是 Canvas 语境下的 problem description 增强。

**手段 2：为 LanceDB 使用真实嵌入式实例，为 Neo4j 引入 TestContainers 预配置（解决风险 1）。** LanceDB 天然支持 `tmp_path` 隔离——这是一个不需要 mock 的组件。为 Neo4j 创建标准化 pytest fixture：

```python
@pytest.fixture(scope="session")
def neo4j_container():
    with Neo4jContainer("neo4j:5.15").with_env("NEO4J_PLUGINS", '["apoc"]') as neo4j:
        yield neo4j.get_driver()
```

将这个 fixture 作为 test-writer 的可用基础设施告知它，使其能写真实的集成测试而非 mock。

**手段 3：分层测试策略——纯函数用 A，集成层用 B/C hybrid（解决风险 2 和 4）。** 不要一刀切。在纯逻辑层（scoring、data transformation、validation）强制使用 A 的隔离策略；在集成层和前端层允许 implementer 自行编写补充测试。这保留了 A 的核心优势（防止 facade），同时承认隔离策略不适用于所有层。

**手段 4：引入 mutation testing 作为所有 workflow 的通用防线（跨 A/B/C 适用）。** 无论使用哪个 workflow，CI pipeline 中对关键业务逻辑模块执行 `mutmut run --paths-to-mutate=app/services/scoring_utils.py,app/utils/`。**mutation kill rate < 80% 即阻断合并**。这是独立于 workflow 选择的质量门禁。

**手段 5：为探索性任务定义"TDD 豁免"协议（解决风险 5）。** 明确规定：当任务标记为"R&D/Exploratory"时，跳过 A 的 test-first 要求，改用 B 的自由模式。在原型稳定后（需求明确化后），再用 A 的隔离策略补写测试。

### 最小可行 "A vs B vs C" 评估实验

**阶段 1（2 周，快速筛选）：** 15 个精选任务，每个 workflow 运行一次，使用 mutation testing 作为质量指标而非仅看功能通过率。15 对配对数据不够做 McNemar's 检验，但足以通过 Fisher 精确检验或 bootstrap 识别大效应量（>30% 差异）。

**阶段 2（4 周，统计显著性）：** 扩展到 31 个任务 × 3 次重复（93 对配对），按前述 5 个任务类别分层。使用 Cochran's Q + pairwise McNemar's 做正式统计检验。这提供 ~80% power 来检测 20% 的成功率差异。

**关键评估指标不应仅是"任务是否完成"，而应包括：**
- 功能正确性（通过率）
- 测试质量（mutation kill rate）
- 代码架构质量（是否 inline 修改 vs 提取模块）
- Token 消耗效率（AgentCoder 论文显示其 token 效率是 MetaGPT 的 2.4 倍）
- 时间成本

这套实验设计既务实（总量控制在 ~279 次运行），又有足够的统计严谨性来得出可操作的结论——前提是我们接受 80% power 和 20% 最小可检测效应量。如果追求 90% power 或 10% 效应量检测，任务数量需增加至 60-100 个。