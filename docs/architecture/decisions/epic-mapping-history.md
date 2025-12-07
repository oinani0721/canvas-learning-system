# Epic编号映射历史 (Architecture Decision Record)

**创建日期**: 2025-12-04
**状态**: Active
**决策者**: Canvas Learning System Team

---

## 背景

Canvas Learning System在迭代过程中经历了多次Epic编号调整。
本文档记录Epic编号的演变历史，确保团队对Epic归属有统一理解。

---

## Epic映射表

### 已完成Epic (YAML确认) - 共15个

| Epic编号 | 当前名称 | 原始名称/来源 | 完成日期 | Stories |
|---------|----------|--------------|----------|---------|
| 1 | 基础学习系统 | FULL-PRD-REFERENCE | 2025-10-15 | 3 |
| 2 | 评分系统 | FULL-PRD-REFERENCE | 2025-10-20 | 3 |
| 3 | 颜色流转系统 | FULL-PRD-REFERENCE | 2025-10-22 | 2 |
| 4 | 检验白板系统 | FULL-PRD-REFERENCE | 2025-10-25 | 3 |
| 5 | 多Agent编排系统 | FULL-PRD-REFERENCE | 2025-10-28 | 2 |
| 6 | 记忆系统集成 | V2规划 Epic 6 | 2025-10-30 | 2 |
| 10 | 异步并行执行引擎 | V2规划 Epic 10 | 2025-11-10 | 2 |
| 11 | Canvas监控/进度追踪系统 | 原Epic 9延续 | 2025-11-20 | 9 |
| 12 | 3层记忆系统+Agentic RAG | Migration PRD | 2025-11-29 | 16 |
| 13 | Obsidian Plugin核心功能 | Migration PRD | 2025-12-02 | 8 |
| 14 | 艾宾浩斯复习系统迁移 | Migration PRD | 2025-12-02 | 7 |
| 15 | FastAPI后端基础架构 | 原Epic 11重分配 | 2025-11-27 | 6 |
| 16 | 跨Canvas关联学习系统 | Migration PRD | 2025-12-02 | 7 |
| 17 | 性能优化和监控 | Migration PRD | 2025-12-04 | 6 |
| 18 | 数据迁移和回滚 | Migration PRD | 2025-12-04 | 5 |
| 19 | 检验白板进度追踪 | 原Epic 15移入 | 2025-12-04 | 5 |

---

## V2规划Epic归属说明

V2升级PRD (`CANVAS-LEARNING-SYSTEM-V2-EPIC-PLANNING.md`) 中定义了Epic 6-10。
由于后续迭代调整，部分Epic已合并到其他Epic中。

| V2 Epic | 原名称 | 归属决策 | 说明 |
|---------|--------|----------|------|
| Epic 6 | 知识图谱驱动系统 | **保留** → YAML Epic-6 | Memory System Integration |
| **Epic 7** | 多Agent并发处理系统 | **已合并** → Epic 10 + Epic 12 | 并发功能分布在异步引擎和LangGraph编排 |
| **Epic 8** | 智能可视化和布局系统 | **已合并** → Epic 19 | 可视化功能移入进度追踪系统 |
| **Epic 9** | 企业级错误监控系统 | **已合并** → Epic 11 + Epic 17 | 监控功能分布在监控系统和性能优化 |
| Epic 10 | 用户体验提升 | **保留** → YAML Epic-10 | Async Parallel Execution |

---

## Epic 0 状态确认

| 项目 | 状态 |
|------|------|
| PRD标注 | Done (Section 4, line 5625) |
| YAML记录 | 无 |
| Git提交 | 无明确提交 |
| 决策 | Epic 0为文档化工作（技术文档验证基础设施），不需YAML跟踪 |
| 交付物 | Context7/Skills验证报告、示例Story模板 |

**结论**: Epic 0 的工作已融入日常开发流程，无需单独追踪。

---

## 决策记录

| 日期 | 决策 | 影响 |
|------|------|------|
| 2025-11-20 | Epic 11从FastAPI重分配为学习记忆监控系统 | YAML中Epic 11为监控系统 |
| 2025-11-27 | FastAPI后端重分配为Epic 15 | 避免编号冲突 |
| 2025-12-04 | 检验白板进度追踪从Epic 15移入Epic 19 | 完成进度追踪功能 |
| 2025-12-04 | 确认V2 Epic 7/8/9已合并到其他Epic | 整理编号映射 |

---

## 相关文档

- PRD主文档: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
- V2规划: `docs/prd/CANVAS-LEARNING-SYSTEM-V2-EPIC-PLANNING.md`
- YAML状态: `.bmad-core/data/canvas-project-status.yaml`
- 基础PRD: `docs/prd/FULL-PRD-REFERENCE.md`

---

## 质量指标汇总

| 指标 | 值 |
|------|-----|
| 已完成Epic总数 | 15 |
| 总Story数 | 70+ |
| 测试通过率 | 99.2% |
| Agent完成数 | 14/14 (100%) |
| 最新提交 | 0e97e359 (Epic 19) |

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | 2025-12-04 | 初始创建，记录Epic 1-19映射和V2归属 |
