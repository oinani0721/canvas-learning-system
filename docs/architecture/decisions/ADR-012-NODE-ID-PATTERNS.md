# ADR-012: Node ID Pattern Standardization

**Date**: 2025-12-17
**Status**: Accepted
**Deciders**: Canvas Learning System Team
**Epic**: 12.K (Story 12.K.4)

---

## Context

Canvas Learning System generates node IDs in two scenarios:

1. **Obsidian Native Nodes**: Created by Obsidian Canvas, using pure hexadecimal IDs (e.g., `b33c50660173e5d3`)
2. **Agent-Generated Nodes**: Created by our 12 learning agents, using semantic prefix IDs (e.g., `vq-b33c5066-0-ee742d`)

The original `NodeRead` schema pattern `^[a-f0-9]+$` only accepted Obsidian native IDs, causing Pydantic validation failures for agent-generated nodes. This resulted in HTTP 500 errors when using basic decomposition, deep decomposition, and other agent features.

---

## Decision

We standardize node ID patterns with the following rules:

### 1. Relaxed Pattern

```python
# New Pattern (Epic 12.K.1)
pattern = r"^[a-zA-Z0-9][-a-zA-Z0-9]*$"
```

This pattern:
- Starts with alphanumeric character (letter or digit)
- Allows hyphens as separators
- Does NOT allow spaces, special characters, or leading hyphens
- Is a **superset** of the original pattern (backward compatible)

### 2. ID Format Standards

| Generator | Format | Example | Location |
|-----------|--------|---------|----------|
| Obsidian | `{16-char-hex}` | `b33c50660173e5d3` | N/A (native) |
| Verification Question | `vq-{nodeId[:8]}-{idx}-{uuid6}` | `vq-b33c5066-0-ee742d` | agent_service.py:2898 |
| Question Decomposition | `qd-{nodeId[:8]}-{idx}-{uuid6}` | `qd-b33c5066-1-ab12cd` | agent_service.py:3050 |
| Explanation | `explain-{type}-{nodeId[:8]}-{uuid4}` | `explain-oral-b33c50-a1b2` | agent_service.py:2390 |
| Four-Level | `explain-four-level-{nodeId[:8]}-{uuid4}` | `explain-four-level-b33c-a1b2` | agent_service.py:2435 |
| Understanding | `understand-{nodeId[:8]}-{uuid4}` | `understand-b33c5066-a1b2` | agent_service.py:2473 |
| Error Node | `error-{agentType}-{uuid8}` | `error-oral-12345678` | agent_service.py:430 |
| Edge | `edge-{fromId[:8]}-{toId[:8]}` | `edge-vq-abc12-qd-def34` | agent_service.py |

### 3. Semantic Prefix Convention

| Prefix | Meaning | Usage |
|--------|---------|-------|
| `vq-` | Verification Question | Questions testing concept understanding |
| `qd-` | Question Decomposition | Sub-questions from verification questions |
| `explain-` | Explanation | Generated explanation content |
| `understand-` | Understanding | Understanding check nodes |
| `error-` | Error | Error placeholder nodes |
| `edge-` | Edge | Generated edges between nodes |

---

## Consequences

### Positive

1. **Backward Compatible**: New pattern accepts all existing Obsidian native IDs
2. **Semantic Clarity**: ID prefixes clearly indicate node origin and type
3. **Debugging Aid**: Prefixes help identify which agent generated a node
4. **No Data Migration**: Existing canvas files work without modification

### Negative

1. **Longer IDs**: Agent-generated IDs are longer than Obsidian native IDs
2. **Pattern Complexity**: Slightly more complex validation regex

### Neutral

1. **Consistent Encoding**: All IDs use ASCII characters only (no Unicode issues)
2. **Unique Guarantees**: UUID suffixes ensure uniqueness within agent operations

---

## Compliance

### Files Updated

| File | Change | Line |
|------|--------|------|
| `backend/app/models/schemas.py` | Pattern relaxed | 221-223 |
| `specs/data/canvas-node.schema.json` | Pattern relaxed | 20 |

### Contract Tests

See `backend/tests/contract/test_node_id_patterns.py` (Story 12.K.5)

---

## References

- [Epic 12.K: NodeRead Schema Fix](../../prd/epics/EPIC-12K-NODEREAD-SCHEMA-FIX.md)
- [JSON Canvas Spec 1.0](https://jsoncanvas.org/spec/1.0/)
- [Obsidian Canvas Node Format](https://github.com/obsidianmd/obsidian-api)
