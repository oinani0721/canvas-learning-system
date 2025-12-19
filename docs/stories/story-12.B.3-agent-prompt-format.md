# Story 12.B.3: Agent Prompt格式统一

**Epic**: 12.B - Agent-RAG Integration Enhancement
**Status**: Done
**Priority**: P1

## Story

作为Canvas学习系统开发者，我需要统一所有Agent调用的prompt格式为JSON，以便：
1. Agent模板能够正确解析输入参数
2. 保证前后端传递的内容格式一致
3. 支持日志记录和调试

## Acceptance Criteria

- [x] AC1: `call_decomposition()` 构建JSON格式的prompt，包含 `material_content`, `topic`, `user_understanding`
- [x] AC2: `call_scoring()` 构建JSON格式的prompt，包含 `question_text`, `user_understanding`, `reference_material`
- [x] AC3: `call_explanation()` 构建JSON格式的prompt，包含 `material_content`, `topic`, `concept`, `user_understanding`
- [x] AC4: 添加 `_extract_topic_from_content()` 辅助方法从内容中提取主题
- [ ] AC5: 为 `_extract_topic_from_content()` 添加专门的单元测试（推荐但未完成）

## Technical Implementation

### Backend Changes

**File**: `backend/app/services/agent_service.py`

1. **`_extract_topic_from_content()` method** (lines 1059-1097):
   - 从内容第一行提取主题
   - 清理markdown标记（#, **, *, _）
   - 最大长度截断（默认50字符）
   - 空内容返回 "Unknown"

2. **`call_decomposition()` JSON prompt** (lines 1298-1307):
```python
json_prompt = json.dumps({
    "material_content": content,
    "topic": self._extract_topic_from_content(content),
    "user_understanding": user_understanding
}, ensure_ascii=False, indent=2)
```

3. **`call_scoring()` JSON prompt** (lines 1330-1338):
```python
json_prompt = json.dumps({
    "question_text": question_text or self._extract_topic_from_content(node_content),
    "user_understanding": user_understanding,
    "reference_material": node_content
}, ensure_ascii=False, indent=2)
```

4. **`call_explanation()` JSON prompt** (lines 1376-1386):
```python
json_prompt = json.dumps({
    "material_content": content,
    "topic": topic,
    "concept": topic,  # Some agents use 'concept' instead of 'topic'
    "user_understanding": user_understanding
}, ensure_ascii=False, indent=2)
```

### Frontend Changes

**File**: `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`
- `nodeContent` extraction from Canvas node data (lines 871-887)

**File**: `canvas-progress-tracker/obsidian-plugin/src/api/types.ts`
- `ExplainRequest.node_content?: string` field added (line 322)

**File**: `canvas-progress-tracker/obsidian-plugin/main.ts`
- `node_content: context.nodeContent` passed to all explanation API calls

## File List

| File | Lines Changed | Description |
|------|---------------|-------------|
| `backend/app/services/agent_service.py` | ~100 | JSON prompt construction, topic extraction |
| `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts` | ~20 | nodeContent extraction |
| `canvas-progress-tracker/obsidian-plugin/src/api/types.ts` | ~5 | ExplainRequest.node_content |
| `canvas-progress-tracker/obsidian-plugin/main.ts` | ~10 | node_content passing |

## Testing

### Related Tests (Passing)
- `backend/tests/unit/test_agent_memory_injection.py`: 11 tests
- `backend/tests/api/v1/endpoints/test_agents_learning_event.py`: 19 tests

### Missing Tests (Recommended)
- Unit tests for `_extract_topic_from_content()` edge cases:
  - Empty content → "Unknown"
  - Markdown heading → cleaned topic
  - Long content → truncated to 50 chars
  - Multiple lines → first line only

## Dependencies

- Story 12.B.2: Node内容传递 (provides `node_content` from frontend)
- Agent templates in `.claude/agents/*.md` (define expected JSON input format)

## Dev Notes

- JSON prompts use `ensure_ascii=False` to preserve Chinese characters
- `indent=2` for readable logs
- Topic extraction uses first line strategy (most Canvas nodes have concept name as first line)

---

## QA Results

### Review Date: 2025-12-15

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

Implementation is correct and matches the expected input formats defined in agent templates (`.claude/agents/*.md`). The JSON prompt construction follows a consistent pattern across all agent call methods. The `_extract_topic_from_content()` helper method is well-implemented with appropriate fallback handling.

### Refactoring Performed

None - code quality is acceptable.

### Compliance Check

- Coding Standards: [✓] Code follows project patterns
- Project Structure: [✓] Changes in appropriate locations
- Testing Strategy: [~] Related tests pass (30/30), but missing dedicated unit tests for topic extraction
- All ACs Met: [~] 4/5 ACs implemented, AC5 (unit tests) recommended but not mandatory

### Improvements Checklist

- [x] JSON prompt format matches agent templates
- [x] Frontend passes node_content correctly
- [x] Topic extraction handles edge cases (empty, markdown)
- [ ] Add unit tests for `_extract_topic_from_content()` edge cases
- [ ] Consider adding input validation for JSON prompt fields

### Security Review

No security concerns. JSON prompt construction does not expose sensitive data or allow injection.

### Performance Considerations

No performance concerns. JSON serialization is lightweight and the `_extract_topic_from_content()` method is O(n) for first line extraction.

### Files Modified During Review

None.

### Gate Status

Gate: **CONCERNS** → docs/qa/gates/12.B.3-agent-prompt-format.yml

**Concerns:**
1. Missing dedicated unit tests for `_extract_topic_from_content()`
2. No formal story file existed (now created)

### Recommended Status

[~] Ready for Done with minor concerns - Implementation is complete and functional. Recommend adding unit tests in a follow-up story.

(Story owner decides final status)
