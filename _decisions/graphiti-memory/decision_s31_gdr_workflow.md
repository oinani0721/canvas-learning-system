---
name: S31 GDR 工作流改进决策
description: S31 GDR 16-Agent调研确认：DD精简+DD-13升级+Graphiti修复+SP Cherry-pick+Boris工作流
type: project
---

S31 GDR 调研（16 Agent, 200+ 信源）确认以下改进方向：

1. **DD规则精简**: 13条→3硬规则(DD-03/DD-12/DD-13 exit 2)+2自动化(DD-10/DD-07)+其余降级
2. **DD-13升级**: PostToolUse警告→exit 2阻断（防止知识图谱投毒）
3. **Graphiti修复**: exclude_invalidated默认true + 解锁11工具 + search_mode多样化
4. **SP Cherry-pick**: brainstorming+systematic-debugging方法论→CLAUDE.md, writing-plans→Plan Mode
5. **最佳工作流**: CLAUDE.md + Hooks + Plan Mode（Boris工作流，A级证据）
6. **自定义/commands**: 5个全部有✅社区验证（code-review 10+实现, tech-audit 8实现, tdd-cycle 6实现）
7. **Graphiti+Agentic RAG**: 强可行（Zep官方示例+5社区实现+学术DMR 94.8%）

**Why:** 当前问题是"规则太多"不是"框架太少"。CLAUDE.md在agent场景执行率<30%，但exit 2 Hook可达95-98%。

**How to apply:** 实施改进方案后，开发工作流变为：Boris工作流(Plan Mode先行) + exit 2硬规则 + PostToolUse auto-test + Graphiti高级搜索
