# Technical Design: Score Feedback Pipeline (score_answer -> Graphiti -> Smarter Exams)

## 1. Problem Statement

The current `score_answer` pipeline has a **data dead-end**: scoring results update BKT/FSRS mastery state (via the `SCORE_SUBMITTED` event), but **no learning-quality data flows back to Graphiti**. Specifically:

1. **AutoSCORE dimension scores** (concept_accuracy, reasoning_quality, knowledge_coverage, knowledge_integration) are computed but discarded after the HTTP response.
2. **Misconceptions detected during examination** (low concept_accuracy, wrong reasoning) are not recorded as `Misconception` or `ProblemTrap` entities in Graphiti.
3. **Next exam session** cannot leverage prior scoring history from Graphiti to ask more targeted questions.
4. **GraphitiBridgeService** uses raw Cypher `MERGE` instead of the Graphiti `add_episode` API, bypassing Graphiti's built-in entity extraction, deduplication, and temporal tracking.

---

## 2. Data Flow: Current vs. Proposed

### 2.1 Current Flow (broken feedback loop)

```
score_answer()
  -> AutoSCORE evaluate()
  -> SCORE_SUBMITTED event
  -> handle_score_submitted()
       -> MasteryEngine.update_on_interaction() -> BKT/FSRS update
       -> MasteryStore.save_concept()
       -> BKT_UPDATED event -> handle_bkt_updated() -> MASTERY_CHANGED -> UI push
       -> FSRS_UPDATED event -> handle_fsrs_updated() -> record_knowledge_entity("fsrs_review")
  -> Return ScoreAnswerOutput to caller
  [END - no Graphiti writeback of scoring details or misconceptions]
```

### 2.2 Proposed Flow (closed feedback loop)

```
score_answer()
  -> AutoSCORE evaluate()
  -> SCORE_SUBMITTED event (existing, unchanged)
  -> [NEW] EXAM_SCORED event (Tier 2)
       -> handle_exam_scored()
            -> (a) Write MasteryUpdate episode to Graphiti (via MemoryService)
            -> (b) If low dimensions detected, write Misconception/ProblemTrap entities
            -> (c) Write ExamAttempt record for historical tracking
  -> Return ScoreAnswerOutput to caller (existing, unchanged)

generate_question() [next session]
  -> [NEW] Query Graphiti for prior ExamAttempt + Misconception records
  -> Feed into ACP assembly as "prior_weaknesses" context
  -> Generate question that targets unresolved misconceptions
```

---

## 3. New Event Type: EXAM_SCORED

### 3.1 Event Definition

Add to `LearningEventType` in `backend/app/models/canvas_events.py`:

```python
class LearningEventType(str, Enum):
    # ... existing types ...

    # Tier 2 (P1) IMPORTANT -- exam scoring feedback to Graphiti
    EXAM_SCORED = "exam_scored"
```

Add to `LEARNING_EVENT_TIER_MAP`:

```python
LearningEventType.EXAM_SCORED: EventTier.TIER_2_IMPORTANT,
```

### 3.2 Event Payload Schema

```python
{
    "node_id": str,                    # Canvas node examined
    "session_id": str,                 # Dialogue session
    "question_id": str,                # Question UUID
    "grade": int,                      # 1-4 FSRS grade
    "score": float,                    # 0.0-1.0 normalized
    "is_correct": bool,
    "feedback_summary": str,           # AutoSCORE feedback
    "dimension_scores": {              # Per-dimension 0-3 scores
        "concept_accuracy": int,
        "reasoning_quality": int,
        "knowledge_coverage": int,
        "knowledge_integration": int,
    },
    "low_confidence_dimensions": list, # Dimensions with low confidence
    "faithfulness_passed": bool,
    "source": "autoscore",
}
```

### 3.3 Emission Point

In `exam_tools.py score_answer()`, immediately after the existing `SCORE_SUBMITTED` emission (line ~447), add:

```python
# Emit EXAM_SCORED for Graphiti feedback loop
exam_scored_event = LearningEvent(
    event_type=LearningEventType.EXAM_SCORED,
    payload={
        "node_id": node_id,
        "session_id": session_id,
        "question_id": question_id,
        "grade": grade,
        "score": score,
        "is_correct": is_correct,
        "feedback_summary": feedback,
        "dimension_scores": {
            "concept_accuracy": autoscore_result.concept_accuracy.score,
            "reasoning_quality": autoscore_result.reasoning_quality.score,
            "knowledge_coverage": autoscore_result.knowledge_coverage.score,
            "knowledge_integration": autoscore_result.knowledge_integration.score,
        },
        "low_confidence_dimensions": autoscore_result.low_confidence_dimensions,
        "faithfulness_passed": faithfulness_passed,
        "source": "autoscore",
    },
    source="score_answer",
)
await event_bus.publish(exam_scored_event)
```

**Why a separate event instead of piggybacking on SCORE_SUBMITTED?**
- `SCORE_SUBMITTED` is Tier 1 CRITICAL and must remain fast (BKT/FSRS update only).
- Graphiti writes are I/O-heavy (Neo4j + potential LLM entity extraction).
- Separation allows EXAM_SCORED to fail independently without blocking mastery updates.

---

## 4. Event Handler: handle_exam_scored

New handler in `backend/app/services/event_handlers.py`:

```python
async def handle_exam_scored(event: LearningEvent) -> None:
    """Write exam scoring results to Graphiti memory system.

    Three write paths:
    (a) MasteryUpdate episode -- always written
    (b) Misconception/ProblemTrap entity -- conditional on low dimension scores
    (c) ExamAttempt record -- always written (historical tracking)

    Tier 2 (IMPORTANT): fire + retry + JSONL outbox on failure.
    """
    payload = event.payload
    node_id = payload.get("node_id")
    session_id = payload.get("session_id", "")
    grade = payload.get("grade", 0)
    score = payload.get("score", 0.0)
    is_correct = payload.get("is_correct", False)
    feedback = payload.get("feedback_summary", "")
    dims = payload.get("dimension_scores", {})
    faithfulness = payload.get("faithfulness_passed", True)

    if not node_id or not faithfulness:
        return

    from app.services.memory_service import get_memory_service
    from app.core.memory_format import build_episode_body

    memory_svc = await get_memory_service()

    # --- (a) MasteryUpdate episode ---
    mastery_body = build_episode_body(
        "MasteryUpdate",
        topic="exam",
        concept=node_id,
        grade=str(grade),
        p_mastery=f"{score:.3f}",
        effective="",  # Filled by downstream if needed
        level=_grade_to_level(grade),
    )
    await memory_svc.record_knowledge_entity(
        event_type="mastery_update",
        content=mastery_body,
        metadata={
            "node_id": node_id,
            "session_id": session_id,
            "grade": grade,
            "score": score,
            "dimension_scores": dims,
        },
    )

    # --- (b) Misconception/ProblemTrap detection ---
    concept_acc = dims.get("concept_accuracy", 3)
    reasoning = dims.get("reasoning_quality", 3)

    if concept_acc <= 1:
        # Low concept accuracy -> Misconception
        await memory_svc.record_knowledge_entity(
            event_type="misconception",
            content=build_episode_body(
                "Misconception",
                topic="exam",
                error=f"Node {node_id}: concept_accuracy={concept_acc}/3",
                correct=feedback,
                source=f"autoscore:session={session_id}",
            ),
            metadata={
                "node_id": node_id,
                "session_id": session_id,
                "trigger": "exam_low_concept_accuracy",
                "concept_accuracy": concept_acc,
                "grade": grade,
            },
        )

    if reasoning <= 1 and concept_acc > 1:
        # Low reasoning but OK concept -> ProblemTrap
        await memory_svc.record_knowledge_entity(
            event_type="problem_trap",
            content=build_episode_body(
                "ProblemTrap",
                topic="exam",
                problem=node_id,
                wrong=f"reasoning_quality={reasoning}/3",
                correct=feedback,
                insight="Student understands concept but applies it incorrectly",
                source=f"autoscore:session={session_id}",
            ),
            metadata={
                "node_id": node_id,
                "session_id": session_id,
                "trigger": "exam_low_reasoning",
                "reasoning_quality": reasoning,
                "grade": grade,
            },
        )

    # --- (c) ExamAttempt historical record ---
    await memory_svc.record_knowledge_entity(
        event_type="exam_attempt",
        content=(
            f"Exam attempt for node {node_id}: "
            f"grade={grade} score={score:.2f} correct={is_correct} | "
            f"accuracy={concept_acc} reasoning={reasoning} "
            f"coverage={dims.get('knowledge_coverage', 0)} "
            f"integration={dims.get('knowledge_integration', 0)} | "
            f"{feedback[:200]}"
        ),
        metadata={
            "node_id": node_id,
            "session_id": session_id,
            "question_id": payload.get("question_id", ""),
            "grade": grade,
            "score": score,
            "is_correct": is_correct,
            "dimension_scores": dims,
        },
    )


def _grade_to_level(grade: int) -> str:
    return {1: "Forgot", 2: "Struggled", 3: "Correct", 4: "Fluent"}.get(grade, "Unknown")
```

### 4.1 Handler Registration

In `register_all_handlers()`:

```python
event_bus.subscribe(
    LearningEventType.EXAM_SCORED,
    handle_exam_scored,
    subsystem="memory",
)
```

---

## 5. New Entity Types in memory_format.py

Add `ExamAttempt` to the `ENTITY_TYPES` registry in `backend/app/core/memory_format.py`:

```python
"ExamAttempt": {
    "name_prefix": "ExamAttempt",
    "source_description": "exam-attempt-record",
    "keywords": set(),  # Only written programmatically, not by keyword classification
    "body_template": (
        "[Exam] Node: {node_id} | Grade: {grade} | Score: {score} | "
        "Accuracy: {accuracy} | Reasoning: {reasoning} | "
        "Coverage: {coverage} | Integration: {integration} | "
        "Feedback: {feedback}"
    ),
},
```

---

## 6. Recursive Feedback: Prior Weaknesses in Question Generation

### 6.1 Query Prior Exam History

When `generate_question()` is called (either legacy or Story 6.3 path), query Graphiti for prior exam attempts and misconceptions for the target node.

New utility function in `backend/app/services/exam_history_service.py`:

```python
async def get_prior_weaknesses(node_id: str, limit: int = 5) -> dict:
    """Query Graphiti for prior misconceptions and low-scoring dimensions.

    Returns:
        {
            "misconceptions": ["concept_accuracy=1: ...", ...],
            "problem_traps": ["reasoning_quality=1: ...", ...],
            "recent_attempts": [
                {"grade": 2, "weak_dims": ["concept_accuracy"], "feedback": "..."},
            ],
            "recurrent_weaknesses": ["concept_accuracy"],  # Dims that failed 2+ times
        }
    """
    from app.services.memory_service import get_memory_service

    memory_svc = await get_memory_service()

    # Search for misconceptions related to this node
    misconceptions = await memory_svc.search_memories(
        query=f"misconception {node_id}",
        max_results=limit,
    )

    # Search for problem traps
    traps = await memory_svc.search_memories(
        query=f"problem_trap {node_id}",
        max_results=limit,
    )

    # Search for exam attempts
    attempts = await memory_svc.search_memories(
        query=f"exam_attempt {node_id}",
        max_results=limit,
    )

    # Compute recurrent weaknesses: dimensions that scored <= 1 in 2+ attempts
    dim_fail_counts = {"concept_accuracy": 0, "reasoning_quality": 0,
                       "knowledge_coverage": 0, "knowledge_integration": 0}
    recent = []
    for attempt in attempts:
        meta = attempt.get("metadata", {})
        dims = meta.get("dimension_scores", {})
        weak = []
        for dim, val in dims.items():
            if isinstance(val, (int, float)) and val <= 1:
                dim_fail_counts[dim] = dim_fail_counts.get(dim, 0) + 1
                weak.append(dim)
        recent.append({
            "grade": meta.get("grade"),
            "weak_dims": weak,
            "feedback": attempt.get("content", "")[:200],
        })

    recurrent = [dim for dim, count in dim_fail_counts.items() if count >= 2]

    return {
        "misconceptions": [m.get("content", "") for m in misconceptions],
        "problem_traps": [t.get("content", "") for t in traps],
        "recent_attempts": recent,
        "recurrent_weaknesses": recurrent,
    }
```

### 6.2 Integration Point in generate_question

In the Story 6.3 `QuestionGenerator.generate_exam_question()` path, inject prior weaknesses into the ACP before prompt construction:

```python
# In generate_exam_question, after ACP assembly:
from app.services.exam_history_service import get_prior_weaknesses

prior = await get_prior_weaknesses(target_node_id)
if prior["recurrent_weaknesses"] or prior["misconceptions"]:
    acp["prior_weaknesses"] = prior
    # This tells the 5-layer prompt to specifically probe these areas
```

The 5-layer prompt template receives `prior_weaknesses` and adjusts question focus:
- If `recurrent_weaknesses` includes `concept_accuracy`: ask definition/explanation questions
- If `recurrent_weaknesses` includes `reasoning_quality`: ask application/analysis questions
- If recent `misconceptions` exist: directly test the misconception content

---

## 7. GraphitiBridgeService: Migration from Raw Cypher to add_episode

### 7.1 Current Problem

`GraphitiBridgeService.bridge_to_claude_format()` (line 145-184) uses raw Cypher MERGE:

```python
cypher = """
MERGE (n:EntityNode {node_id: $nodeId, group_id: $groupId})
ON CREATE SET ...
ON MATCH SET ...
"""
```

This bypasses Graphiti's entity extraction, temporal tracking, and relationship inference.

### 7.2 Migration Strategy

**Phase 1 (this design):** Keep raw Cypher for `bridge_to_claude_format` (existing write path from color changes), but all **new** writes from `handle_exam_scored` go through `MemoryService.record_knowledge_entity()` which already uses Neo4j's `record_episode` method.

**Phase 2 (future):** When the Graphiti MCP `add_memory` API is available server-side (not just via Claude Code MCP), migrate `bridge_to_claude_format` to use it. This requires:
- A server-side Graphiti Python SDK client (currently only MCP client exists)
- Or an HTTP wrapper around the MCP `add_memory` tool

For Phase 1, the `record_knowledge_entity` path is the correct choice because:
- It writes to both in-memory cache and Neo4j
- It supports the dual-write to Graphiti JSON (Story 36.9)
- It uses deterministic IDs for idempotency
- It integrates with the existing bridge via `_bridge_to_claude_graphiti()`

---

## 8. Anti-Bloat Strategy: Deduplication, Expiry, and Aggregation

### 8.1 Problem: Exam Data Accumulation

Each exam attempt writes 1-3 records to Graphiti (MasteryUpdate + optional Misconception/ProblemTrap + ExamAttempt). Over hundreds of exam sessions, this could bloat the graph.

### 8.2 Mitigation Strategies

#### (a) Deterministic Episode IDs (already in place)

`_generate_deterministic_episode_id()` prevents duplicate writes for the same (user, canvas, node, concept) tuple. Extend this to exam attempts:

```python
def _generate_exam_episode_id(node_id: str, session_id: str, question_id: str) -> str:
    content = f"exam:{node_id}:{session_id}:{question_id}"
    return f"exam-{hashlib.sha256(content.encode()).hexdigest()[:16]}"
```

#### (b) Misconception Deduplication by Content Hash

Before writing a new Misconception, check if the same misconception already exists for this node:

```python
existing = await memory_svc.search_memories(
    query=f"misconception {node_id} concept_accuracy",
    max_results=3,
)
# Skip if substantially similar misconception already recorded within last 7 days
```

#### (c) ExamAttempt Sliding Window

Only keep the last N exam attempts per node (default N=10). When writing a new attempt, check count:

```python
EXAM_ATTEMPTS_PER_NODE_LIMIT = 10
```

This is enforced at query time (LIMIT in search) rather than deletion, so no data is lost from Neo4j -- only the most recent N are returned to the question generator.

#### (d) Misconception Resolution

When a student scores `concept_accuracy >= 2` on a node that has prior Misconceptions, mark the misconception as `resolved`:

```python
if concept_acc >= 2:
    # Check for existing unresolved misconceptions
    priors = await memory_svc.search_memories(
        query=f"misconception {node_id}",
        max_results=5,
    )
    for prior in priors:
        meta = prior.get("metadata", {})
        if not meta.get("resolved"):
            # Write a resolution record
            await memory_svc.record_knowledge_entity(
                event_type="misconception_resolved",
                content=f"Misconception resolved for node {node_id}: "
                        f"concept_accuracy improved to {concept_acc}/3",
                metadata={
                    "node_id": node_id,
                    "resolved_misconception_id": prior.get("episode_id"),
                    "new_concept_accuracy": concept_acc,
                },
            )
```

---

## 9. Files to Modify

| File | Change | Scope |
|------|--------|-------|
| `backend/app/models/canvas_events.py` | Add `EXAM_SCORED` to `LearningEventType` + tier map | 3 lines |
| `backend/app/core/memory_format.py` | Add `ExamAttempt` entity type | 8 lines |
| `backend/app/mcp/tools/exam_tools.py` | Emit `EXAM_SCORED` event after scoring | ~20 lines |
| `backend/app/services/event_handlers.py` | Add `handle_exam_scored()` + register | ~80 lines |
| `backend/app/services/exam_history_service.py` | **New file**: `get_prior_weaknesses()` | ~60 lines |
| `backend/app/services/question_generator.py` | Inject `prior_weaknesses` into ACP | ~10 lines |

**Total estimated change:** ~180 lines across 6 files (1 new).

---

## 10. Sequence Diagram

```
Student answers question
         |
    score_answer()
         |
    AutoSCORE evaluate()
         |
    +----+----+
    |         |
 [existing]  [NEW]
    |         |
SCORE_SUBMITTED    EXAM_SCORED
    |              |
handle_score_      handle_exam_scored()
submitted()        |
    |         +----+----+----+
    |         |         |    |
MasteryEngine  (a)      (b)   (c)
BKT+FSRS    MasteryUpdate  Misconception  ExamAttempt
update       episode     (conditional)    record
    |         |         |    |
    v         +----+----+----+
Mastery            |
Store         Graphiti/Neo4j
persist       (via MemoryService)
                   |
                   v
           [NEXT EXAM SESSION]
                   |
           generate_question()
                   |
           get_prior_weaknesses()
                   |
           Query Graphiti for:
           - Prior ExamAttempts
           - Unresolved Misconceptions
           - Recurrent weak dimensions
                   |
           Inject into ACP as
           prior_weaknesses context
                   |
           Generate targeted question
           that probes known gaps
```

---

## 11. Triggering Strategy

**When:** Every `score_answer` call where `faithfulness_passed=True`.

**Why immediate (not batched):**
- Exam sessions are low-frequency (a few questions per session, not hundreds per second).
- The student needs accurate feedback on the **next** question in the same session.
- Batching would introduce stale data during the active exam session.
- `record_knowledge_entity` already uses fire-and-forget for the dual-write path, so it does not block the score response.

**Faithfulness gate:** If `faithfulness_passed=False`, the scoring is unreliable and should not pollute Graphiti with potentially incorrect misconception records. The EXAM_SCORED event is simply not emitted.

---

## 12. Testing Strategy

1. **Unit test:** `handle_exam_scored` with mock MemoryService -- verify 3 write paths trigger correctly based on dimension scores.
2. **Integration test:** Full pipeline `generate_question -> score_answer -> verify Graphiti records exist -> generate_question again -> verify prior_weaknesses injected`.
3. **Anti-bloat test:** Run 20 exam attempts on the same node, verify only the last 10 are returned by `get_prior_weaknesses`, and duplicate misconceptions are not created.
4. **Misconception resolution test:** Record a misconception, then score well on the same node, verify resolution record is created.
