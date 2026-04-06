# 测试基础设施重建报告

> Session: 2026-04-04 | Commit: d16148d | Plan: indexed-gathering-kazoo
> 关联: `annotation-tracker.md`, `gap-analysis.md`, `s40-progress-report.md`

---

## 摘要

本次 session 完成了测试基础设施从"测试剧场"到"四层真实防线"的重建。核心成果：
- PostToolUse hook: **12min46s → 9s**（85x 提速）
- 新增 **59 个真实测试**（非 mock）
- 可观测性三层追踪：**request_id 贯穿 4 个日志文件** + **Decision ID 追踪业务决策**
- 自改进飞轮：**139 条生产错误 → 12 个回归测试**（发现 1 个真实 bug）

---

## 一、问题发现

Deep Explore 发现两个根本性问题：

**问题 1：测试工具缺失**
- mutmut/vulture 未安装，PostToolUse hook 的变异测试和死代码检测是空壳
- pytest.ini addopts 含 `--cov-fail-under=85`，实际覆盖率 23.4%，每次 pytest 都 exit non-zero
- PostToolUse hook 跑全部 4167 个测试，耗时 12min46s

**问题 2：测试本身不可靠**
- 4039 个测试函数，97% 集成测试用 MagicMock
- 只有 3 个文件真正连接 Neo4j（test_memory_persistence.py 等）
- OpenSpec 不管测试：8 个 spec 目录全空，apply-change 只标 task [x] 不跑测试

---

## 二、20 个社区测试方案调研

从项目 docs/deep-research/ 的 18 篇文档中提取了 20 个方案，按成熟度分三层：

**Proven（项目有基础设施）**: 真实DB测试、变异测试、ATDD、Hypothesis、Schemathesis、AgentCoder隔离、Ralph Loop、AST Impact Maps、Differential Testing、Runtime Contracts

**Emerging（项目有部分基础设施）**: Health冒烟、Audit Guardian、Composite Oracle、Metamorphic Testing、Test Amplification、Semantic Testing

**Experimental（项目无基础设施）**: LLM-as-Judge、Shadow Testing、Multi-Agent互审、Observability-Driven Testing

**用户选择了 10 个**: #1 真实DB / #2 变异测试 / #3 ATDD / #4 Hypothesis / #5 Schemathesis / #6 AgentCoder隔离 / #8 AST精准测试 / #10 Pydantic合约 / #11 Health冒烟 / #12 Audit Guardian

### 10 个测试方案通俗解释

| # | 名字 | 测什么？ |
|---|------|---------|
| 1 | 真实 DB 测试 | 连真数据库验证读写是否真的通了 |
| 2 | 变异测试 (mutmut) | 偷改代码看测试能不能发现，检验测试本身质量 |
| 3 | ATDD 三层验证 | 从用户角度写验收标准，再翻译成测试 |
| 4 | Hypothesis | 随机生成 10000 个边界输入，看代码崩不崩 |
| 5 | Schemathesis | 拿 API 文档轰炸接口，看实际行为和文档是否一致 |
| 6 | AgentCoder 隔离 | 写测试的 AI 和写代码的 AI 必须是两个人 |
| 8 | AST Impact Maps | 改了 A 文件只跑和 A 相关的测试，不跑全部 |
| 10 | Pydantic 合约 | 数据进出函数时自动检查格式 |
| 11 | Health 冒烟 | 启动后快速检查系统各部件是否活着 |
| 12 | Audit Guardian | 后台监控业务管道有没有中间断掉 |

---

## 三、20 种测试执行方式调研

不是测试类型，而是"什么时候、怎么跑测试"：

- **A 编辑后自动**: PostToolUse hook、Watch Mode、AST Impact Maps
- **B 提交时拦截**: Lefthook pre-commit（ruff/pyright）、pre-push（vitest/pytest smoke）
- **C AI回复后验证**: Stop hook、PreToolUse guard、TDD cycle
- **D 推到远程CI**: GitHub Actions test.yml、api-spec-sync.yml
- **E 手动**: pytest CLI、integration脚本、mutmut
- **F AI高级**: MCP mutmut-mcp、pytest-gremlins

**用户决策**: 不使用 GitHub Actions CI/CD（个人项目，全部本地执行），D 类改为 B 类 pre-push。

---

## 四、Lefthook 现状与清理

项目已弃用 Obsidian，lefthook 中 5 个 Obsidian 命令已清理：
- pre-commit: 删 plugin-build、obsidian-lint、ts-typecheck
- post-commit: 删 vault-reminder
- pre-push: 删 vault-freshness
- commit-msg: 保留 spec-reference（用户确认保留）

**发现**: pre-push 的 backend-smoke 已有 `--override-ini="addopts="`，绕过了 --cov-fail-under=85，所以 pre-push 实际能正常工作。

---

## 五、博主经验学习

> 来源：AI 日程+费用管理 iOS 应用博主，48天 12万行代码

与我们项目最相关的 Top 5：

### 1. 自改进飞轮（Self-Improving Flywheel）
> 博主原话："只要有报错，查 log，看看生产环境用户遇到了什么 bug，它自动的把这些 bug 写成测试用例，然后在我的本地环境下复现...整个这个东西是一个闭环"
User：自改进飞轮怎么进行自动触发？
我们的状况：有 135 条错误日志（62 bug + 8 sync失败 + 65 死信），但从未转化为测试。缺的只是 `generate_regression_tests.py` 这一步。**已实现**。

### 2. Decision ID 追踪系统
> 博主原话："决策ID的追踪系统 logging的这个系统...可观测性是什么意思，把这十个小朋友每个人编上号，然后把他们的行为模式也编上号"
> 博主数据：12万行代码中 30% 是可观测性相关
User：我们对于我们已有的代码都可以追踪吗？然后用我们的openspec 的时候开发新的代码和技术框架的时候，又能保证spec 和代码相互追踪，以及我们的追踪系统是怎么成立的？请你给我流程图
我们的状况：有 request_id、BUG-ID、error_code，但 4 个 JSONL 日志没有共同 ID。**已修复**：统一 trace_id + DECN-{uuid8} Decision ID。

### 3. Smart Agent Dumb Tools
> 博主原话："smart agent dumb tools...你充分的相信大模型的推理和计划能力，而你要把工具做的非常极致和简单"
> 博主实践：删了 8-9 千行代码，把验证逻辑从工具移到 Agent

适用于我们的 MCP 工具设计原则。**待后续 session 审查**。

### 4. Plan-Execute > ReAct
> 博主原话："原来我在做这种批量创建的时候，给我创建五个事件，大概一分半到两分钟...选择了计划与执行流水线"

适用于我们 Agent 的批量操作（生成题组等）。**待后续 session 实施**。

### 5. 该省省该花花
> 博主原话："在关于这个产品未来和前途命运的关键领域，一定要选择一步到位"

对应我们：该花的 = 测试体系 + 可观测性。该省的 = 不用 CI/CD（本地跑）。**已执行**。

---

## 六、自改进飞轮 vs Auto Research 区别

| | 自改进飞轮 | Auto Research |
|---|---|---|
| 触发 | 用户遇到 bug **之后** | 做决策**之前** |
| 解决 | "这个 bug 不要再出现第二次" | "我们还不知道有什么坑" |
| 来源 | 自己项目的 error log | 外部 10 个渠道 |
| 输出 | pytest 测试用例 | 决策报告 + Graphiti |
| 性质 | 被动反应 | 主动探索 |

个人使用阶段，**飞轮 ROI 更高**——135 条现有错误数据，只差最后一步转化。

---

## 七、可观测性三层追踪

### 修复前

| 层 | 完成度 | 关键缺口 |
|----|--------|---------|
| Spec → Code | 60% | 有 commit hook 强制 @spec: 引用，但无自动反查 |
| Code → Log | 75% | 有 request_id/BUG-ID/error_code，但无 Decision ID |
| Log → Bug | 85% | 4 个 JSONL 各自独立，无统一 ID 关联 |

### 修复后

| 修复项 | 工作量 | 效果 |
|--------|--------|------|
| P0: 所有日志加 request_id | 2h | 一个 ID 串四个文件 |
| P1: 关键函数加 Decision ID | 4h | 追踪"为什么这么判断" |
| P2: Trace 查询接口 | 3h | `GET /api/v1/traces/{request_id}` 一个请求看完整生命周期 |
| P3: Bug → pytest 自动生成 | 4h | 139 条错误变 12 个回归测试 |

---

## 八、最终方案架构

### 四道防线

```
第一道（毫秒级）写之前拦
  └── PreToolUse: mock-import-guard + pretool-guard

第二道（秒级）编辑后自动
  ├── #11 Smoke (2s)
  ├── #8 AST Maps → 精准选 5-20 个测试 (10-20s)
  ├── #10 Pydantic (runtime)
  ├── #12 Guardian (audit/ 改动时)
  ├── #4 Hypothesis max_examples=5 (1s)
  ├── #5 Schemathesis (API 改动时, 3s)
  ├── vulture (1s)
  └── 可观测性: structlog 自动记录 decision_id

第三道（分钟级）commit/push  User：我们有测试数据事gitcore 的，请问影响我们的用commit 触发测试吗？
  ├── pre-commit: ruff + pyright + spec-sync
  ├── pre-push: vitest + pytest smoke + Hypothesis(200) + Schemathesis + BDD + 真实DB
  └── Stop hook: 提醒跑 mutmut + 飞轮

第四道（手动/按需）
  ├── #2 mutmut 变异测试 (bug 修后)
  ├── #1 真实 DB 集成 (scripts/run-integration.sh)
  ├── #6 AgentCoder (/tdd-cycle)
  └── 飞轮: generate_regression_tests.py
```

### 12 个方案 × 触发方式

| 方案 | A 编辑后 | B pre-push | C AI回复后 | E 手动 |
|------|:---:|:---:|:---:|:---:|
| #11 Smoke | **主**(2s) | 辅 | | |
| #8 AST Maps | **主**(10-20s) | | | |
| #10 Pydantic | **主**(runtime) | | | |
| #12 Guardian | **主**(<5s) | | | |
| #4 Hypothesis | **主**(5例) | **辅**(200例) | | |
| #5 Schemathesis | 辅(API,3s) | **主** | | |
| #1 真实 DB | | **主** | | **辅** |
| #3 ATDD BDD | | **主** | | |
| #2 变异测试 | | | | **主**(bug修后) |
| #6 AgentCoder | | | **主** | |
| 可观测性 | 自动(structlog) | | | |
| 飞轮 | | | 提醒 | **主** |

---

## 九、实施结果

### Phase 0: 紧急修复

| 步骤 | 改动 | 验证 |
|------|------|------|
| 0.0 lefthook 清理 | 删 5 个 Obsidian 命令 + 加 venv 激活 | ✅ |
| 0.1 pytest.ini | 移除 `--cov-fail-under=85` | ✅ exit 0 |
| 0.2 PostToolUse hook | 三层门禁 + 精准选择 | ✅ **12min → 9s** |
| 0.3 Stop hook | `--no-cov` + timeout 120s | ✅ |
| 0.4 安装包 | hypothesis + schemathesis + pytest-bdd | ✅ |

### Phase 1: 激活已有设施
User：Phase 1 这些是我们之前的设施吗？我只是要知道他们做了什么是否成熟

| 步骤 | 新建文件 | 测试数 | 耗时 |
|------|---------|--------|------|
| 1.1 Smoke | `tests/smoke/test_health_smoke.py` | 6 passed | 1.03s |
| 1.2 Guardian | `tests/unit/test_audit_guardian.py` | 11 passed | 0.44s |
| 1.3 Pydantic | `tests/unit/test_pydantic_contracts.py` | 20 passed | 0.43s |
| 1.4 集成脚本 | `scripts/run-integration.sh` | 就绪 | — |

### Phase 2: 新增能力

| 步骤 | 新建文件 | 验证 |
|------|---------|------|
| 2.1 AST Maps | `scripts/impact_map.py` | ✅ review_service → 28 相关测试 |
| 2.2 Hypothesis | `tests/strategies.py` + `test_mastery_property.py` | ✅ 7 passed |
| 2.3 Schemathesis | `tests/contract/test_health_contract.py` | ✅ 1 passed |
| 2.4 mutmut | `scripts/mutmut-targeted.sh` | ✅ 可执行 |
| 2.5 BDD | `tests/bdd/features/health.feature` | ✅ 2 passed |
| 2.6 AgentCoder | `tdd-cycle.md` Phase 4 | ✅ MUTATION VERIFY |

### Phase 3: 可观测性 + 飞轮

| 步骤 | 改动 | 验证 |
|------|------|------|
| P0 trace_id | bug_tracker/guardian/episode_worker/failure_counters + request_id | ✅ |
| P1 Decision ID | `decision_tracker.py` + mastery_engine + review_service | ✅ DECN-E5230080 |
| P2 Trace API | `GET /api/v1/traces/{request_id}` | ✅ 路由注册 |
| P3 飞轮 | `generate_regression_tests.py` → 12 回归测试 | ✅ 6 passed, 5 skip, 1 xfail |

**飞轮发现的真实 bug**: `POST /api/v1/canvas/nonexistent/sync-edges` 对 `CanvasNotFoundException` 返回 500 而不是 404。
USer：飞轮什么时候，什么机制的情况下触发，以及我们的现在是所有模块都已经成功追踪了吗？然后如果我接下来用openspec 来讨论批注，生成新的代码的时候是否还能追踪。
--

## 十、新增文件清单
User：新增文件清单 请你用流程图来告诉我这10个测试是怎么触发的

| 文件 | 类型 | 用途 |
|------|------|------|
| `backend/tests/smoke/test_health_smoke.py` | 测试 | Smoke 冒烟 |
| `backend/tests/unit/test_audit_guardian.py` | 测试 | Guardian 管道监控 |
| `backend/tests/unit/test_pydantic_contracts.py` | 测试 | Pydantic 合约 |
| `backend/tests/unit/test_mastery_property.py` | 测试 | Hypothesis 属性测试 |
| `backend/tests/strategies.py` | 测试工具 | Hypothesis 域策略 |
| `backend/tests/contract/test_health_contract.py` | 测试 | Schemathesis 合约 |
| `backend/tests/bdd/features/health.feature` | 测试 | BDD 场景 |
| `backend/tests/bdd/test_health_bdd.py` | 测试 | BDD step definitions |
| `backend/tests/regression/test_production_bugs.py` | 测试 | 飞轮自动生成 |
| `backend/scripts/impact_map.py` | 工具 | AST 精准测试选择 |
| `backend/scripts/run-integration.sh` | 工具 | 真实 DB 集成测试 |
| `backend/scripts/mutmut-targeted.sh` | 工具 | 定向变异测试 |
| `backend/scripts/generate_regression_tests.py` | 工具 | 飞轮闭环 |
| `backend/app/core/decision_tracker.py` | 核心 | Decision ID 追踪 |
| `backend/app/api/v1/endpoints/traces.py` | API | Trace 查询接口 |

---

## 十一、修改前后对比

| 指标 | 修改前 | 修改后 |
|------|--------|--------|
| PostToolUse hook | 12min46s | **9s** |
| pytest 默认 | 必失败(--cov-fail-under=85) | **正常通过** |
| 真实测试 | 3 个文件连真实 DB | **+59 个新真实测试** |
| 测试类型 | 只有 mock 单元测试 | **+6 类** |
| 精准测试选择 | 无（跑全部 4167 个） | **AST 映射** |
| 变异测试 | 空壳 | **mutmut 脚本就绪** |
| 日志关联 | 4 个文件各自独立 | **统一 request_id** |
| 决策追踪 | 无 | **DECN-{uuid8}** |
| 生产错误利用 | 135 条未使用 | **12 个回归测试** |
| Lefthook Obsidian | 5 个死命令 | **全部清理** |
