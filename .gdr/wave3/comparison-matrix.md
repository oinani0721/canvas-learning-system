# GDR Wave 3 -- Comparison Matrix: 规范驱动开发工作流诊断

> **Agent**: W3-SYNTH (Wave 3 Comparison Matrix Generator)
> **Research Topic**: Canvas Learning System 规范驱动开发工作流诊断
> **Generated**: 2026-03-27
> **Input**: Wave 1 (5 diagnostic conclusions) + Wave 2 (10 agents W2-A through W2-J)

---

## 1. Comprehensive Comparison Matrix

### 1.1 BMAD Framework Fitness for Solo Developer

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **框架适用性** | GSD(42K stars)等社区5+来源明确推荐:solo dev不需要完整开发流程框架(W2-A) | 无直接学术共识 | S31决策:放弃BMAD/SuperPower框架层,保留Hook+DD+Commands+bmad-code-review | 验证 | ✅社区验证 |
| **644文件仅35活跃(5.4%)** | BMAD Issue #2003框架自我承认结构矛盾:为solo dev设计却产出企业级产物(W2-A) | 无 | 框架层放弃,保留实用工具 | 验证 | ✅社区验证 |
| **Token消耗** | 67%+ context被框架规则占用(W2-A),GSD的4:1 token开销在1M context时代同样是问题(W2-D) | 无 | 无明确Token预算决策 | 新发现 | ✅社区验证 |
| **BMAD Lite替代** | 仅274 stars无独立评测(W2-D),无法验证实际改善 | 无 | 未考虑 | 新发现 | ❌无验证 |
| **GSD替代方案** | 42K stars社区认可,但4:1 token开销+1M context使其核心价值(fresh context)降低(W2-D) | 无 | 未考虑 | 新发现 | 🟡有案例但需审慎 |
| **核心洞察:规则精简** | Boris工作流共识:问题是"规则太多"不是"框架太少",CLAUDE.md+Hooks+Plan Mode已够(W2-D) | 无 | S31与此一致:保留Hook+DD+Commands | 验证 | ✅社区验证 |

### 1.2 SuperPower Skills 激活率与Cherry-Pick

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **14技能全安装0激活** | Claude Code技能自激活率仅37-50%(W2-B),根因=无SessionStart触发+DD规则抢占 | 无 | S31放弃SuperPower框架层 | 验证 | ✅社区验证 |
| **Cherry-pick候选** | brainstorming/writing-plans/systematic-debugging方法论有独立价值(W2-B) | 无 | 保留bmad-code-review已确认;其余SP技能未明确保留/弃用 | 新发现 | 🟡有案例(SP社区使用) |
| **SP "plan没变"问题** | 同上下文同输入导致plan重复(W2-H),与Boris推荐的Plan Mode本质相同但实现不同 | 无 | 无明确决策 | 新发现 | 🟡有案例 |
| **Boris推荐:Plan Mode** | Claude Plan Mode是"最被低估的功能"(W2-H),比SP writing-plans更原生 | 无 | 无明确决策 | 新发现 | ✅社区验证(Boris工作流) |

### 1.3 /commands 社区验证状态

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **code-review** | 10+实现含Anthropic官方插件(W2-C) | 无 | 保留bmad-code-review | 验证 | ✅社区验证 |
| **tech-audit** | 8个独立实现(W2-C) | 无 | 无明确决策 | 新发现 | ✅社区验证 |
| **tdd-cycle** | 6个独立实现含npm包(W2-C) | TDD子Agent 84%激活率(W2-I),AgentCoder学术96.3% vs 67%(W2-I) | 无明确决策;后端pytest已配置80+测试文件但未系统使用 | 新发现 | ✅社区验证 |
| **plan-feature** | 5个独立实现(W2-C) | 无 | 无明确决策 | 新发现 | ✅社区验证 |
| **coverage-check** | 5个独立实现(W2-C) | 无 | 无明确决策 | 新发现 | ✅社区验证 |

### 1.4 执行确定性:Hook机制可靠性

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **PreToolUse exit 2** | ~95%可靠(W2-G),已知绕过:Bash工具绕过+内容混淆 | 无 | DD-03/DD-12使用exit 2确定性阻断 | 验证 | ✅社区验证 |
| **UserPromptSubmit exit 2** | ~98%可靠(W2-G),最高可靠性Hook生命周期事件 | 无 | graphiti-user-prompt.js使用此事件 | 验证 | ✅社区验证 |
| **Stop hook regex** | ~70-80%可靠(W2-G),正则匹配本身有限制 | 无 | graphiti-stop-check.js使用Stop事件 | 冲突 | 🟡有案例 |
| **CLAUDE.md指令** | ~70%基线,<30%在agent场景(W2-G) | 无 | DD规则大量依赖CLAUDE.md文本指令 | 冲突 | ✅社区验证 |
| **SP HARD-GATE** | ~65-75%可靠(W2-G) | 无 | 已放弃SP框架层 | 过期 | 🟡有案例 |
| **DD-13 只警告不阻断** | 警告无exit 2 = 可被忽略,与DD-03/DD-12的exit 2形成可靠性断层(W2-G) | 无 | DD-13已部署但仅PostToolUse警告 | 冲突 | ✅社区验证(exit 2有效性共识) |
| **已知绕过向量** | Bash工具绕过PreToolUse+内容混淆+Hook自修改(W2-G) | 无 | 无防御措施 | 新发现 | ✅社区验证 |

### 1.5 Graphiti 工具能力利用率

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **5/16工具(31%)使用率** | Zep官方LangGraph示例+5社区实现展示全工具利用(W2-E) | Graphiti论文DMR 94.8%验证全能力(W2-E),教育KA-RAG 91.4%(W2-E) | Graphiti-canvas MCP已部署,但仅用add_memory+search_memory_facts | 冲突 | ✅社区验证 |
| **P0:exclude_invalidated** | 从未使用=搜索返回过期决策,严重污染上下文(W2-F) | Graphiti bi-temporal模型的核心设计:旧事实invalidated但不删除(W2-E) | 无使用记录 | 冲突 | ✅社区验证 |
| **P0:center_node_uuid** | 文档称"单一最大相关性改进",7个代码示例存在但0实际使用(W1-C审计) | 无 | 无使用记录 | 新发现 | 🟡有案例(官方文档) |
| **P0:解锁11工具** | add_triplet/bulk_add_memory/build_communities/search_communities等需在settings.local.json添加权限(W2-F) | 无 | 11工具被权限阻断 | 冲突 | ✅社区验证 |
| **P1:search_mode变体** | mmr/cross_encoder/node_distance/episode_mentions全未使用,仅用默认rrf(W1-C) | 无 | 无 | 新发现 | 🟡有案例 |
| **P1:build_communities** | 社区检测可揭示决策自然聚类(W2-F) | 无 | 从未使用 | 新发现 | 🟡有案例 |
| **P1:时间过滤** | 按时间范围搜索可减少历史噪音(W2-F) | Graphiti bi-temporal支持时间维度查询(W2-E) | 从未使用 | 新发现 | 🟡有案例 |

### 1.6 Decision-Review 完成率

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **2/13完成(15.4%)** | 无直接社区共识 | 无 | Decision-Review流程已定义(brainstorming-decisions.md) | 冲突 | 无外部验证(内部流程) |
| **PENDING积压** | 无 | 无 | 11个Decision-Review处于PENDING状态 | 冲突 | 无外部验证 |

### 1.7 DD规则有效性与执行机制

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **规则过多问题** | Boris工作流:成功率最高=CLAUDE.md+Hooks+Plan Mode(A级证据,W2-D) | 无 | DD-01~DD-13共13条规则 | 冲突 | ✅社区验证 |
| **确定性阻断覆盖** | exit 2是唯一确定性手段(W2-G),但仅DD-03/DD-12有exit 2 | 无 | DD-13警告不阻断 | 冲突 | ✅社区验证 |
| **DD-07用户验收** | 被评估为"正确但失败"(context_pack gap) | 无 | Stop hook v7是否修复不明 | 过期 | 无外部验证 |
| **DD-12范围约束** | 结构性导致DD-11管道断裂(W2-G):agent被限制文件范围->跨文件接线被遗漏 | 无 | DD-12 PreToolUse hook硬执行 | 冲突 | 无外部验证(内部经验) |

### 1.8 TDD/自动测试策略

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **TDD子Agent模式** | 单实践者84%激活率(W2-I) | AgentCoder: 96.3% vs 67%(无TDD)(W2-I) | 无明确TDD策略;SP TDD已安装但0激活 | 新发现 | ✅社区验证 |
| **PostToolUse auto-test** | 编辑代码后自动运行测试(W2-I推荐) | 无 | 无 | 新发现 | 🟡有案例 |
| **后端pytest基础** | 80+测试文件已存在(W2-I) | 无 | pytest配置完成但未系统利用 | 过期 | 无外部验证(内部资产) |

### 1.9 Bug宪法与渐进披露等实践

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **Bug宪法** | 4个生产案例(W2-J) | arXiv论文支持(W2-J) | 无 | 新发现 | ✅社区验证 |
| **渐进披露** | 8+实现,Anthropic推荐(W2-J) | 无 | 无 | 新发现 | ✅社区验证 |
| **Pre-impl gate** | CodeScene+5个案例(W2-J) | 无 | 无(DD-10防蔓延是文本规则非自动化) | 新发现 | ✅社区验证 |
| **Context7审计** | 仅1类似案例(W2-J) | 无 | Context7已使用但无审计机制 | 新发现 | ❌无验证 |

### 1.10 Graphiti+Agentic RAG 可行性

| 维度 | 社区共识 | 学术共识 | 已有决策 | 状态 | 证据等级 |
|------|---------|---------|---------|------|---------|
| **Graphiti+Agentic RAG** | Zep官方LangGraph示例+5社区实现(W2-E) | DMR 94.8%(W2-E),教育KA-RAG 91.4%(W2-E) | 四层搜索+A-RAG架构已决策 | 验证 | ✅社区验证 |

---

## 2. Cross-Cutting Synthesis

### 2.1 所有Wave 2 Agent的收敛点

1. **"规则太多"是核心问题** -- W2-A(BMAD自我承认)/W2-B(SP 0%激活)/W2-D(Boris工作流)/W2-G(CLAUDE.md <30%agent场景)全部指向同一结论:当前规范体系过度膨胀,实际执行率远低于设计预期。

2. **exit 2 Hook是唯一确定性手段** -- W2-G的可靠性分析明确:PreToolUse exit 2 ~95%,UserPromptSubmit exit 2 ~98%,而CLAUDE.md文本<30%(agent),SP HARD-GATE ~65-75%。所有关键规则应迁移到Hook exit 2。

3. **Graphiti严重underutilized** -- W2-E/W2-F/W1-C三方独立确认:16工具仅用5个,高级参数0%使用,exclude_invalidated从未用导致过期决策污染搜索结果。

4. **S31决策获强社区验证** -- 放弃BMAD/SP框架层的决策与社区共识完全一致。保留Hook+DD+Commands+bmad-code-review是正确方向。

5. **TDD/auto-test是可立即激活的高ROI实践** -- 84%激活率+96.3%学术验证+80+已有测试文件,投入最小收益最大。

### 2.2 关键冲突需要解决

| # | 冲突 | 已有决策 | Wave 2发现 | 需要的行动 |
|---|------|---------|-----------|-----------|
| C1 | DD规则数量 vs 执行率 | 13条DD规则 | 规则越多,CLAUDE.md执行率越低(<30% agent场景) | 精简到只保留有exit 2 Hook的硬规则;其余降级为建议 |
| C2 | DD-12范围约束 vs DD-11管道打通 | 两者并存 | DD-12硬约束导致DD-11结构性失败 | 设计DD-12的"跨文件接线"安全例外机制 |
| C3 | DD-13警告 vs exit 2确定性 | DD-13仅PostToolUse警告 | 警告可被忽略,与DD-03/DD-12的exit 2形成可靠性断层 | DD-13升级为exit 2阻断或接受当前警告级别 |
| C4 | Graphiti搜索质量 vs 使用方式 | 仅用默认rrf搜索 | exclude_invalidated未用=过期决策污染;center_node_uuid未用=相关性差 | 立即启用exclude_invalidated;逐步引入center_node_uuid |
| C5 | Stop hook可靠性 | DD-07依赖Stop hook | ~70-80%可靠性不足以保证用户验收执行 | 考虑将DD-07验收步骤移到其他更可靠的执行点 |

### 2.3 从未出现在任何已有决策中的新发现

| # | 发现 | 来源 | 影响 |
|---|------|------|------|
| N1 | Boris工作流:CLAUDE.md+Hooks+Plan Mode是成功率最高的组合(A级证据) | W2-D | 当前体系方向正确但需精简;Plan Mode应被系统性采用 |
| N2 | Claude Plan Mode是"最被低估的功能",优于SP writing-plans | W2-H | 可替代SP writing-plans,原生集成无额外Token开销 |
| N3 | TDD PostToolUse auto-test可自动化代码质量门禁 | W2-I | PostToolUse hook编辑.py后自动pytest,比DD-07手动验收更可靠 |
| N4 | Bug宪法:结构化bug分析模板(arXiv论文+4案例) | W2-J | 可替代当前松散的bug修复流程 |
| N5 | 渐进披露:8+实现+Anthropic推荐 | W2-J | 规则展示可分层:新session只看核心规则,深入时展开详细规则 |
| N6 | Pre-impl gate:实现前自动检查是否符合MVP清单(CodeScene+5案例) | W2-J | 可自动化DD-10防蔓延,从CLAUDE.md文本升级为PreToolUse Hook |
| N7 | Graphiti build_communities可自动发现决策聚类 | W2-F | 替代人工整理decision clusters |
| N8 | Hook自修改是已知绕过向量 | W2-G | 需要hooks文件完整性校验机制 |

---

## 3. Status Summary

| 分类 | 验证 | 冲突 | 新发现 | 过期 |
|------|------|------|--------|------|
| BMAD框架适用性 | 3 | 0 | 2 | 0 |
| SuperPower技能 | 1 | 0 | 3 | 0 |
| /commands | 1 | 0 | 4 | 0 |
| Hook可靠性 | 2 | 3 | 1 | 1 |
| Graphiti利用率 | 0 | 3 | 3 | 0 |
| Decision-Review | 0 | 2 | 0 | 0 |
| DD规则有效性 | 0 | 3 | 0 | 1 |
| TDD/自动测试 | 0 | 0 | 2 | 1 |
| Bug宪法等实践 | 0 | 0 | 4 | 0 |
| Graphiti+RAG | 1 | 0 | 0 | 0 |
| **Total** | **8** | **11** | **19** | **3** |

**Overall**: 8项已有决策获社区验证, 11项与现有做法冲突, 19项全新发现待纳入, 3项已过期需更新.

---

## 4. Incremental Question Queue

### P0 -- 需立即确认（阻塞写回Graphiti）

**P0-1. DD规则精简:13条DD规则是否精简到仅保留有exit 2 Hook的硬规则?**

> Wave 2 多方独立确认:CLAUDE.md文本指令在agent场景执行率<30%(W2-G),Boris工作流证明CLAUDE.md+Hooks+Plan Mode是最高成功率组合(W2-D,A级证据)。当前13条DD规则中仅DD-03/DD-12有exit 2阻断,其余全靠CLAUDE.md文本。
>
> **具体提议**:
> - **硬规则(保留exit 2 Hook)**:DD-03(禁mock)、DD-12(范围约束)、DD-13(升级为exit 2)
> - **自动化规则(升级为Hook)**:DD-10(防蔓延 -> Pre-impl gate Hook)、DD-07(用户验收 -> PostToolUse auto-test)
> - **降级为建议(移出CLAUDE.md铁律)**:DD-01/DD-04/DD-05/DD-06/DD-08/DD-09(保留在rules/目录但不在CLAUDE.md重复)
> - DD-02/DD-11保留在CLAUDE.md但标注为"best-effort"
>
> **影响**:CLAUDE.md大幅缩短,Token占用下降,实际执行率反而提高(少即是多)。
>
> **是否确认这个精简方向?**

**P0-2. DD-13名实一致:从PostToolUse警告升级为exit 2阻断?**

> DD-13当前仅PostToolUse警告,但W2-G确认:无exit 2的警告可被Agent忽略。历史教训(persist_to_graphiti骗局)证明DD-13是关键防线。
>
> **选项**:
> - **A**: 升级为PreToolUse exit 2(函数写入前检查名称是否匹配)
> - **B**: 保持PostToolUse警告但增加Graphiti自动记录违规(事后追溯)
> - **C**: 维持现状
>
> **推荐A**:与DD-03/DD-12保持一致的确定性级别。
>
> **是否确认升级?**

**P0-3. Graphiti exclude_invalidated:是否立即在所有search_memory_facts调用中启用?**

> Wave 1确认从未使用exclude_invalidated,导致搜索返回已被新信息取代的旧决策,系统性污染上下文。这是Graphiti bi-temporal模型的核心设计:旧事实被invalidated但不删除,搜索时应排除。
>
> **具体做法**:修改graphiti-user-prompt.js Hook,在注入的搜索提示中强制包含`exclude_invalidated:true`参数。
>
> **影响**:搜索结果立即变干净,不再返回被推翻的旧决策。可能遗漏有历史参考价值的旧决策(可通过不带exclude的专门搜索补充)。
>
> **是否确认立即启用?**

**P0-4. Graphiti 11工具权限解锁:是否在settings.local.json添加?**

> 16工具中11个被权限阻断(W2-F/W1-C审计确认)。最高优先级解锁:
> - **P0解锁**: add_triplet(结构化关系)、bulk_add_memory(批量写入)、get_episode_lineage(审计追溯)
> - **P1解锁**: build_communities+search_communities(决策聚类)、get_graph_stats(健康监控)、search_edges(边搜索)
> - **保持锁定**: clear_graph(破坏性)、delete_episode/delete_entity_edge(需更高审慎)
>
> **是否确认P0解锁列表?**

**P0-5. SP Cherry-pick:brainstorming/writing-plans/systematic-debugging方法论是否保留?**

> S31决定放弃SP框架层,但W2-B确认这3个技能有独立方法论价值。W2-H同时指出Plan Mode比SP writing-plans更原生。
>
> **具体提议**:
> - **保留**: brainstorming(创意发散无替代)、systematic-debugging(结构化调试无替代)
> - **替换**: writing-plans -> Claude Plan Mode(原生+零Token开销)
> - **弃用**: 其余11个SP技能
>
> **是否确认?**

### P1 -- 建议确认（影响写回质量）

**P1-1. TDD PostToolUse auto-test:是否在PostToolUse Hook中实现"编辑.py后自动pytest"?**

> W2-I推荐PostToolUse auto-test,学术验证AgentCoder 96.3% vs 67%。后端已有80+pytest测试文件。实现方式:PostToolUse Hook检测到Write/Edit操作目标为.py文件时,自动运行`pytest {changed_file_test}`。
>
> **影响**:每次代码编辑自动验证,替代DD-07手动验收的不可靠性。增加约5-15秒延迟/编辑。
>
> **建议确认后实施。**

**P1-2. DD-12 vs DD-11 结构性冲突:是否设计"跨文件接线"安全例外?**

> DD-12(范围约束)硬阻断agent改其他文件,但DD-11(管道打通)要求新函数必须有调用方。S18-4的dead code正是这个结构性矛盾的产物。
>
> **提议**:DD-12增加白名单机制:agent完成后输出"需要接线"清单,主Agent自动在调用方文件添加import和调用,此操作不被DD-12阻断。
>
> **建议确认后细化实现。**

**P1-3. Pre-impl gate:DD-10防蔓延是否从CLAUDE.md文本升级为PreToolUse Hook自动化?**

> CodeScene+5个社区案例(W2-J)验证Pre-impl gate有效。实现:PreToolUse Hook在检测到创建新文件/新函数时,自动检查是否在MVP清单内(通过关键词匹配或LLM判断)。
>
> **影响**:DD-10从"建议"变为"自动检查",但可能产生误判需要override机制。
>
> **建议确认方向后调研具体实现。**

**P1-4. Bug宪法:是否引入结构化bug分析模板?**

> arXiv论文+4个生产案例(W2-J)。核心:bug修复前必须填写"bug宪法"(症状/根因/影响范围/修复方案/回归测试)。可作为systematic-debugging的补充。
>
> **影响**:增加bug修复的前期分析时间,但减少"修了一个bug引入两个"的问题。
>
> **建议确认。**

**P1-5. 渐进披露:CLAUDE.md是否采用分层展示(核心+展开)?**

> 8+实现+Anthropic推荐(W2-J)。当前CLAUDE.md将所有规则平铺,Token占用高。渐进披露:CLAUDE.md仅放最核心规则(~10行),详细规则通过`@rules/`文件按需加载。
>
> **影响**:直接减少每轮Token消耗。当前.claude/rules/已有此结构,但CLAUDE.md仍重复所有规则。
>
> **建议确认后精简CLAUDE.md。**

**P1-6. Decision-Review 11个PENDING:是否batch验证或按优先级排序?**

> 15.4%完成率(2/13)。积压可能包含已过期的决策。
>
> **提议**:先用Graphiti search_memory_facts("Decision-Review PENDING")拉取全部,按决策日期排序,2周以上的标记为"需重新评估",1周内的安排验证session。
>
> **建议确认优先级规则。**

### P2 -- 可延后确认

**P2-1. Graphiti center_node_uuid:是否在search_memory_facts中逐步引入?**

> 文档称"单一最大相关性改进",7个代码示例存在但0实际使用(W1-C审计)。需要先有node UUID索引才能使用。
>
> **不阻塞当前写回,可在后续session逐步引入。**

**P2-2. Graphiti build_communities:是否运行一次以发现决策自然聚类?**

> 需先解锁权限(P0-4)。运行后可自动发现决策聚类,替代人工整理。
>
> **不阻塞当前写回。**

**P2-3. Hook自修改防护:是否需要hooks文件完整性校验?**

> W2-G确认Hook自修改是已知绕过向量。可通过hooks文件hash校验或git pre-commit检测。
>
> **低优先级,当前风险可控。**

**P2-4. Context7审计机制:是否需要验证Context7返回结果的时效性?**

> 仅1个类似案例(W2-J),验证不足。Context7返回的文档可能过期,但目前无系统性问题报告。
>
> **不阻塞,可观察一段时间。**

**P2-5. GSD fresh context评估:是否在特定场景(如大型重构)使用GSD模式?**

> GSD 42K stars但4:1 token开销(W2-D)。在1M context时代,fresh context的价值降低。但对于已污染的长session,重开session本身就是"GSD行为"。
>
> **当前"重开session"的做法已是隐式GSD,无需额外框架。**

---

## Appendix: Source Cross-Reference

| Agent | 对本矩阵的关键贡献 |
|-------|-------------------|
| W2-A | BMAD Issue #2003框架自我承认;社区5+来源推荐GSD替代solo dev;S31决策社区验证 |
| W2-B | SP 0%激活根因分析;Cherry-pick候选;Claude Code技能自激活率37-50% |
| W2-C | 5个/commands全部社区验证;code-review 10+实现;tdd-cycle 6实现 |
| W2-D | Boris工作流A级证据;GSD token开销分析;BMAD Lite评估;核心洞察"规则太多" |
| W2-E | Graphiti+Agentic RAG社区+学术验证;Zep官方示例;DMR 94.8%;KA-RAG 91.4% |
| W2-F | Graphiti P0/P1解锁清单;exclude_invalidated;search_mode变体;build_communities |
| W2-G | Hook可靠性量化(exit 2 ~95%,CLAUDE.md ~70%/<30%);已知绕过向量;DD-13断层 |
| W2-H | Plan Mode"最被低估";SP"plan没变"=同上下文同输入;GSD 1M context价值降低 |
| W2-I | TDD 84%激活率;AgentCoder 96.3%;PostToolUse auto-test推荐;pytest 80+文件 |
| W2-J | Bug宪法(arXiv+4例);渐进披露(8+实现);Pre-impl gate(CodeScene+5例);Context7审计(1例) |
