---
name: A3 四方向确认通过
description: 用户确认 A3 检索范围+Frontmatter+Wiki-links+Cross-Canvas 四方向全部通过，无阻断性问题（2026-03-13）
type: project
---

## [Decision] A3 四方向确认

**Why:** 经过社区/论文验证 + 代码对抗性审查，4个方向均无阻断性问题，用户确认通过。
**How to apply:** 实施时按 P0(Scope+Frontmatter) → P1(Wiki-links) → P2(Cross-Canvas) 优先级推进。

### 确认的方向
1. Scope 范围过滤 — P0
2. Frontmatter 解析集成 — P0
3. Wiki-links 集成（含1-hop邻居扩展） — P1
4. Cross-Canvas Bridge 跨课程桥接 — P2

### 待验证项（[Decision-Review] PENDING）
- 方向3的"三层渐进范围"机制无直接论文验证，需实测效果
- 方向4的RAG retriever需重写，实施后需验证跨课程检索质量

### 关键修复项（实施前提）
- _extract_heading_section heading level bug (方向3)
- WHERE子句SQL注入风险 (方向1)
- YAML frontmatter污染首chunk (方向1+2)
- API路由未注册 (方向4)
- find_related_canvases TODO空壳 (方向4)
