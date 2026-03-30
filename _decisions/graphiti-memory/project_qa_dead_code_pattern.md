---
name: QA代码普遍为死代码——激活而非重写
description: 8个QA Story并行分析发现：旧E7的QA代码大量已实现但未接入管道，实施核心是激活+接入而非重写。
type: project
---

# QA 代码"死代码"模式（2026-03-17 并行 Story 创建发现）

8 个分散到各 Epic 的 QA Story 并行分析后发现一致模式：

| Story | 代码文件 | 实现度 | 核心问题 |
|-------|---------|--------|---------|
| 1-10 LLM日志 | llm_call_logger.py + cost_tracker.py | ~90% | LiteLLM 回调未注册 |
| 1-11 忠实度基础 | faithfulness_check.py (586行) | ~95% | 已接入 LangGraph，需补边界测试 |
| 2-13 Prompt版本 | prompt_registry.py | ~80% | 4个检索管道内联prompt未外部化 |
| 3-12 Token追踪 | cost_tracker.py + system.py API | 100%(后端） | 纯前端工作 |
| 3-13 注入防护 | prompt_injection_guard.py (282行) | ~90% | 死代码，0个文件import它 |
| 5-8 人工抽验 | extraction_validator.py | ~70% | 未接入归档管道 |
| 6-9 评分忠实度 | 需新建 | 0% | 需区分RAG忠实度vs评分忠实度 |
| 6-10 难度匹配 | difficulty_matcher.py | ~85% | 未接入考察管道 |

**Why:** 旧 Epic 7 集中实现了 QA 基础设施，但从未被其他 Epic 调用。E7 分散后，这些代码需要"激活"——接入实际管道。

**How to apply:** 实施这些 Story 时，先审查已有代码，重点工作是接入管道和补充测试，而非从零开发。避免重新发明轮子。
