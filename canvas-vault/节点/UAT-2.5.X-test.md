---
type: concept
board_name: UAT-2.5.X
mastery_score: 0.30
errors: []
error_candidates:
  - id: "uat-cand-001"
    status: pending
    source: ai_suggested
    node_id: "节点/UAT-2.5.X-test.md"
    session_id: "s-uat-2026-05-05-001"
    group_id: "cs_61b:main"
    candidate_dedupe_hash: "uat001hash000abc"
    pedagogy_type: conceptual_confusion
    legacy_type: knowledge_gap
    legacy_remedy: backtrack_definition
    description: "学生混淆了 admissibility 和 consistency, 认为它们等价"
    context: "对话第 3 轮"
    ai_reason: null
    evidence_turns: []
    raw_dialog_excerpt: null
    confidence: 0.85
    confidence_source: llm
    sub_tags: [synonym_confusion]
    suggested_remedy_strategies: [discrimination_comparison]
    created_at: "2026-05-05T08:00:00+00:00"
    last_seen_at: "2026-05-05T08:00:00+00:00"
    seen_count: 1
    seen_sessions: [s-uat-2026-05-05-001]
    status_changed_at: null
    status_changed_by: null
  - id: "uat-cand-002"
    status: pending
    source: ai_suggested
    node_id: "节点/UAT-2.5.X-test.md"
    session_id: "s-uat-2026-05-05-001"
    group_id: "cs_61b:main"
    candidate_dedupe_hash: "uat002hash000def"
    pedagogy_type: procedural_error
    legacy_type: reasoning_fallacy
    legacy_remedy: counterexample_construction
    description: "因果倒置: 把 'h ≤ optimal cost' 推成 admissibility 的因"
    context: "对话第 5 轮"
    confidence: 0.55
    confidence_source: llm
    sub_tags: []
    suggested_remedy_strategies: [error_finding]
    created_at: "2026-05-05T08:01:00+00:00"
    last_seen_at: "2026-05-05T08:01:00+00:00"
    seen_count: 1
    seen_sessions: [s-uat-2026-05-05-001]
    status_changed_at: null
    status_changed_by: null
---

# UAT-2.5.X-test

这是 Story 2.5.X 用户主权 C+ 测试节点。frontmatter 已手动准备 2 条 pending candidates，供 UAT V1-V4 主流程使用：

- **uat-cand-001** (🟢 confidence 0.85): 学生混淆 admissibility 和 consistency
- **uat-cand-002** (🔴 confidence 0.55): 因果倒置（admissibility ≠ h ≤ optimal cost）

## 跑 UAT 路径

### V1 — 验证 Dashboard 渲染
1. 打开 vault 根 `Dashboard.md`
2. 滚到 `📋 待复盘错误候选` section
3. 应看到：
   - **总览**：⏳ pending = 2
   - **详细列表**：本节点 (UAT-2.5.X-test) 2 条候选
   - 颜色：🟢 cand-001 / 🔴 cand-002

### V2 — 接受错误候选 (Cmd+P)
1. 切回当前节点（让它成为 active file）
2. **Cmd+P** → 输入 "接受错误候选" → Enter
3. 弹 SuggestModal，应见 2 条候选
4. 选 cand-001 → Enter
5. 期望 Notice：`✓ 已接受 → errors[] (Graphiti: queued)`
6. **回 Obsidian 重新打开本文件** 看 frontmatter：
   - `errors[]` 多 1 条（含 `source: user_confirmed_ai` / `from_candidate_id: uat-cand-001`）
   - `error_candidates[0].status` 改为 `accepted`

### V3 — 异议候选
1. **Cmd+P** → "异议错误候选"
2. 选 cand-002（仅剩它 pending）
3. 弹 DisputeReasonModal，输入理由："我不是因果倒置, 只是问 admissibility 与 optimal cost 的关系"
4. 点 **✅ 提交异议**
5. 期望 Notice：`⚠ 已标记 disputed + 写入理由`
6. 重打开看 frontmatter：cand-002 `status: disputed` + `dispute_reason: "..."`

### V4 — 标记 AI 误判
1. 在文件 frontmatter 手动加第 3 条候选 cand-003（spec UAT V4 提供完整 yaml 段）
2. **Cmd+P** → "标记错误候选为 AI 误判（dismiss）"
3. 选 cand-003
4. 期望 Notice：`✗ 已标记为 AI 误判 (dismissed)`

---

> 跑完后告诉 Claude **"V1/V2/V3/V4 通过"**, 或选中失败行 `Cmd+Shift+A` 批 ❌ 错误。
