# 2. 使用LangGraph实现多Agent协作系统

Date: 2025-10-18

## Status

Accepted

Enables: [ADR-0004: 异步并行执行引擎](#0004-async-execution-engine.md)

## Context

Canvas Learning System需要实现14个专项Agents（12个学习型 + 2个系统级）的协作系统，支持费曼学习法的完整闭环：

1. **多Agent协作需求**:
   - 12个学习型Agents: 拆解、解释、评分、检验等专项功能
   - 2个系统级Agents: 智能调度、记忆管理等基础设施
   - 需要主控Agent（canvas-orchestrator）统一调度
   - 支持自然语言调用协议（非函数式调用）

2. **状态管理需求**:
   - 跨Agent共享Canvas数据（节点、边、颜色）
   - 维护学习会话状态（当前节点、评分历史）
   - 支持状态持久化和恢复

3. **工作流需求**:
   - 支持条件分支（if评分<60 → basic-decomposition; else → deep-decomposition）
   - 支持循环迭代（填写理解 → 评分 → 拆解 → 重复）
   - 支持人机交互（用户填写 → Agent评分 → 用户优化 → Agent再评分）

4. **可扩展性需求**:
   - 易于添加新的Agent
   - 支持Agent动态组合和并行执行（Epic 10）
   - 支持Agent版本管理和A/B测试

### 候选方案对比

| 方案 | 优点 | 缺点 | 评分 |
|------|------|------|------|
| **LangGraph** | • 官方LangChain生态<br>• StateGraph状态管理<br>• 支持循环和条件分支<br>• 活跃社区和文档<br>• 支持流式输出 | • Python only<br>• 学习曲线中等 | ⭐⭐⭐⭐⭐ |
| AutoGen (Microsoft) | • 多Agent对话<br>• 支持人机交互<br>• 微软支持 | • 主要面向对话场景<br>• 状态管理不如LangGraph<br>• 文档相对较少 | ⭐⭐⭐⭐ |
| CrewAI | • 角色扮演Agent<br>• 任务分配简单 | • 适合简单任务分工<br>• 不支持复杂状态管理<br>• 社区较小 | ⭐⭐⭐ |
| 自定义Agent框架 | • 完全控制<br>• 无依赖 | • 开发周期长<br>• 需要自己实现状态管理<br>• 维护成本高 | ⭐⭐ |
| LangChain原生 | • 简单直接<br>• 官方支持 | • 缺少图结构<br>• 不支持复杂工作流<br>• 状态管理有限 | ⭐⭐⭐ |

## Decision

我们决定使用**LangGraph**作为Canvas Learning System的多Agent协作框架。

**选择理由**:

1. **StateGraph完美匹配需求** 🎯:
   - 使用`StateGraph`定义Agent工作流
   - 每个Agent是一个node，可以定义条件边
   - 状态在Agents之间自动传递和更新
   - 支持循环节点（用户填写 → 评分 → 拆解 → 重复）

2. **官方LangChain生态支持** 🏛️:
   - LangGraph是LangChain官方推荐的图执行框架
   - 与LangChain的`ChatPromptTemplate`, `RunnableSequence`无缝集成
   - 活跃的社区和完善的文档（952页官方文档）
   - 长期维护保障

3. **自然语言调用协议支持** 💬:
   - Agent可以通过prompt engineering实现自然语言调用
   - 不依赖函数签名，灵活性高
   - 支持返回JSON格式结果（我们的需求）

4. **流式输出和可观测性** 👁️:
   - 支持流式输出中间结果
   - 可以监控Agent执行状态
   - 便于调试和优化

5. **未来扩展性** 🚀:
   - Epic 10: 异步并行执行引擎可以基于LangGraph实现
   - Epic 12: Graphiti记忆管理可以作为LangGraph的State层
   - 支持Agent版本管理（不同model参数）

**技术实现**:

我们将创建`.claude/agents/`目录存储14个Agent定义（Markdown格式），通过Claude Code的Task tool调用：

```python
# Agent调用协议（自然语言调用）
call_statement = f"""
Use the {agent_name} subagent to {task_description}

Input: {json.dumps(input_data, ensure_ascii=False, indent=2)}

Expected output: {output_format_description}

⚠️ IMPORTANT: Return ONLY the raw JSON. Do NOT wrap it in markdown code blocks.
"""
```

**Agent分类**:

- **学习型Agents (12个)**: 直接支持用户学习活动
  1. canvas-orchestrator (主控)
  2. basic-decomposition, deep-decomposition, question-decomposition (拆解系列)
  3. oral-explanation, clarification-path, comparison-table, memory-anchor, four-level-explanation, example-teaching (解释系列)
  4. scoring-agent, verification-question-agent (评分检验系列)

- **系统级Agents (2个)**: 支撑系统基础设施
  1. review-board-agent-selector (智能调度, Epic 10)
  2. graphiti-memory-agent (记忆管理, Epic 12/14)

## Consequences

### 正面影响

1. **开发效率大幅提升** ⚡:
   - 不需要从零实现Agent协作框架
   - StateGraph简化了状态管理逻辑
   - 丰富的示例代码和模板

2. **代码可维护性高** 🔧:
   - Agent定义清晰（Markdown格式）
   - 调用协议统一（自然语言调用）
   - 状态流转逻辑集中管理

3. **测试和调试友好** 🧪:
   - 可以单独测试每个Agent
   - 流式输出便于观察中间状态
   - 可以replay执行历史

4. **社区资源丰富** 📚:
   - 952页官方LangGraph文档
   - 大量开源项目和示例
   - 活跃的Discord社区

### 负面影响

1. **学习曲线** ⚠️:
   - 团队需要学习LangGraph的核心概念（StateGraph, Node, Edge）
   - 需要理解LangChain的LCEL语法
   - **缓解措施**: 创建`langgraph` Skill (952页离线文档)，提供快速参考

2. **Python依赖** ⚠️:
   - LangGraph仅支持Python（无JavaScript/TypeScript版本）
   - 如果未来需要Web界面，需要通过API调用
   - **缓解措施**: 当前项目是Python-based，暂无问题；未来可以通过FastAPI暴露API

3. **版本依赖风险** ⚠️:
   - LangGraph在快速迭代，API可能变化
   - 需要锁定版本（requirements.txt: `langgraph==0.2.48`）
   - **缓解措施**: 定期review更新日志，渐进式升级

4. **调试复杂度** ⚠️:
   - 多Agent协作的调试比单Agent复杂
   - 状态流转可能不够透明
   - **缓解措施**: 使用LangSmith追踪执行过程，添加详细日志

### 技术债务

- **TODO**: 创建LangGraph最佳实践文档
- **TODO**: 开发Agent测试框架（单元测试 + 集成测试）
- **TODO**: 监控LangGraph版本更新，评估升级影响

### 度量指标

- **Agent调用成功率**: 目标>99%
- **单Agent平均执行时间**: <6秒
- **StateGraph状态传递正确率**: 目标100%
- **Code覆盖率**: 目标>95% (Agent调用逻辑)

## References

- LangGraph官方文档: https://langchain-ai.github.io/langgraph/
- LangGraph GitHub: https://github.com/langchain-ai/langgraph
- LangChain官网: https://python.langchain.com/
- Canvas Learning System Skill: `.claude/skills/langgraph/` (952页离线文档)
- Canvas Learning System PRD: `docs/prd/FULL-PRD-REFERENCE.md` (Epic 2-3: Agent系统)

## Notes

此决策是Canvas Learning System **Agent架构的基石**。LangGraph的StateGraph机制使得14个Agents可以高效协作，状态管理清晰，扩展性强。

**历史背景**: 在项目启动阶段（2025-10-18），我们评估了5种Agent框架，LangGraph以其官方生态支持、StateGraph状态管理和活跃社区脱颖而出。

**实施状态**:
- ✅ Epic 2 (问题拆解系统) - 实现了basic-decomposition, deep-decomposition
- ✅ Epic 3 (补充解释系统) - 实现了6个解释Agent
- ✅ Epic 5 (智能化增强) - 实现了scoring-agent
- ⏳ Epic 10 (异步并行执行) - 基于LangGraph实现并行Agent调用

**重要约束**: 所有Agent调用必须通过**自然语言调用协议**（非函数式调用），返回纯JSON（不使用markdown code fence），以保证Claude Code的Task tool正确解析结果。

## Related ADRs

- [ADR-0004: 异步并行执行引擎](#0004-async-execution-engine.md) - 基于LangGraph实现并行Agent调度
- [ADR-0003: Graphiti记忆管理](#0003-graphiti-memory.md) - Graphiti与LangGraph的State层集成
