# ADR-007: WebSocket for Batch Processing Real-time Updates

## Status

**Accepted** | 2026-01-20

Supersedes: ADR-006 for Epic 33 batch processing use case

## Context

Epic 33 (Agent Pool Batch Processing) requires real-time progress updates for long-running batch operations processing 100+ Canvas nodes. The existing Obsidian UI has already implemented WebSocket-based progress monitoring.

### Background

ADR-006 established SSE (Server-Sent Events) + HTTP as the standard real-time communication pattern for Canvas Learning System. However, Epic 33's batch processing UI was developed with WebSocket implementation before ADR-006 was created.

### The Conflict

| Aspect | ADR-006 (SSE + HTTP) | Epic 33 UI (WebSocket) |
|--------|----------------------|------------------------|
| Communication | Unidirectional (server → client) | Bidirectional |
| Implementation | Not yet built | 100% complete in Obsidian plugin |
| Cancel mechanism | HTTP POST `/tasks/{id}/cancel` | WebSocket message |
| Reconnection | Browser auto-reconnect | Manual implementation required |

### Why WebSocket for Epic 33

1. **UI Already Implemented**: Obsidian plugin's `ProgressMonitorModal` uses WebSocket at line 341
2. **Bidirectional Needs**: Batch processing benefits from client → server messages (cancel, pause, priority adjustment)
3. **Session Lifecycle**: WebSocket connection lifecycle maps naturally to batch session lifecycle
4. **Heartbeat Built-in**: WebSocket ping/pong provides connection health monitoring

## Decision

**Use WebSocket for Epic 33 batch processing real-time updates**, as an exception to ADR-006's SSE recommendation.

### Scope

This decision applies specifically to:
- `/ws/intelligent-parallel/{sessionId}` endpoint
- Epic 33 batch processing progress monitoring
- Stories 33.1-33.8

ADR-006 (SSE + HTTP) remains the default choice for other real-time features:
- Single-node analysis progress
- Performance monitoring dashboards
- Future real-time features (unless bidirectional communication is required)

## Technical Specification

### Endpoint

```
WebSocket: ws://localhost:8000/ws/intelligent-parallel/{sessionId}
```

### Connection Lifecycle

| Phase | Behavior |
|-------|----------|
| Connect | Validate sessionId exists, return 404 close code if not found |
| Active | Heartbeat ping every 30 seconds |
| Timeout | Auto-close after 10 minutes of inactivity |
| Complete | Auto-close when session completes |
| Client disconnect | Graceful cleanup |

### Event Types

| Event | Direction | Description |
|-------|-----------|-------------|
| `progress_update` | Server → Client | Progress percentage, completed/total nodes |
| `task_completed` | Server → Client | Individual node completion with file path |
| `task_failed` | Server → Client | Individual node failure with error message |
| `session_completed` | Server → Client | Final status, duration, success/failure counts |
| `error` | Server → Client | Connection or processing errors |

### Message Schema

```json
{
  "type": "progress_update" | "task_completed" | "task_failed" | "session_completed" | "error",
  "task_id": "string",
  "timestamp": "ISO8601",
  "data": {
    // type-specific payload
  }
}
```

### Fallback Mechanism

If WebSocket connection fails:
1. Client receives `error` event with `recoverable: true` and `retry_after` seconds
2. Client can poll `GET /api/v1/canvas/intelligent-parallel/{sessionId}` as fallback
3. UI already implements this fallback in `ProgressMonitorModal`

## Consequences

### Positive

1. **Zero UI Changes Required** - Obsidian plugin works immediately
2. **Natural Session Mapping** - Connection = session lifecycle
3. **Better Error Handling** - Immediate disconnect notification
4. **Future Extensibility** - Can add client → server messages (pause, priority)

### Negative

1. **Inconsistent Pattern** - Different from ADR-006's SSE recommendation
2. **Manual Reconnection** - Must implement reconnection logic (vs SSE auto-reconnect)
3. **Additional Complexity** - WebSocket state management in backend

### Mitigations

1. **Documentation** - Clearly document when to use WebSocket vs SSE
2. **Abstraction Layer** - `ConnectionManager` class handles WebSocket complexity
3. **Testing** - Comprehensive integration tests for reconnection scenarios

## Decision Criteria Summary

| Criterion | SSE (ADR-006) | WebSocket (This ADR) | Winner |
|-----------|---------------|----------------------|--------|
| UI Implementation Status | 0% | 100% | WebSocket |
| Bidirectional Communication | No | Yes | WebSocket |
| Browser Auto-reconnect | Yes | No | SSE |
| Session Lifecycle Mapping | Weak | Strong | WebSocket |
| Development Effort | High | Zero | WebSocket |

**Conclusion**: The practical benefit of zero UI changes and strong session mapping outweighs the theoretical advantages of SSE for this specific use case.

## Related Documents

- [ADR-006: SSE + HTTP Real-time Communication](ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md) - Superseded for Epic 33
- [ADR-0004: Async Execution Engine](0004-async-execution-engine.md) - Underlying execution pattern
- [Epic 33: Agent Pool Batch Processing](../../epics/EPIC-33-AGENT-POOL-BATCH-PROCESSING.md) - Parent epic
- [Story 33.2: WebSocket Real-time Updates](../../stories/33.2.story.md) - Implementation story
- [OpenAPI Spec: parallel-api.openapi.yml](../../../specs/api/parallel-api.openapi.yml) - API specification

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-01-20 | 1.0 | Initial creation from Story 33.2 validation conflict resolution | PO Agent (Sarah) |

---

*ADR created during Story 33.2 validation - Conflict Resolution #3*
*Approved by: User (2026-01-20)*
