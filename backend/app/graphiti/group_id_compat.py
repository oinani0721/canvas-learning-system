"""
Graphiti group_id compatibility shim.

Background:
    Canvas D16 group_id 规约 (Story 2.5.Y AC #2, locked 2026-05-05) uses
    colon-separated format: `vault:<vault_id>` / `vault:<vault_id>:<subject>`.

    Graphiti's upstream validation rejects any group_id containing characters
    outside `[A-Za-z0-9_-]`, which means **all Canvas group_ids fail Graphiti
    add_episode / search calls** with `GroupIdValidationError`.

    This compatibility shim sanitizes Canvas group_ids at the Graphiti API
    boundary (and only at the boundary). All Canvas business logic (Cypher
    queries, subject_config, memory_service writers/readers) continues to use
    the Canvas D16 format internally.

    Boundary locations (must call sanitize before passing to graphiti_core):
    - `episode_worker._process_task` → graphiti.add_episode(group_id=...)
    - `memory_service._search_graphiti` → graphiti.search_(group_ids=[...])
    - `memory_service._search_graphiti_legacy` → graphiti.search(group_ids=[...])

    Reverse direction: not currently needed — Canvas readers query
    Neo4j's EpisodicNode.source_description / node_id, not its group_id
    field (which is owned by Graphiti and stored in sanitized form).

Source:
    P0-5 (2026-05-14) — discovered after P0 三件套 + P0-4 schema fixes
    finally let GraphitiEpisodeWorker run to add_episode and hit the
    upstream group_id validator.
"""

_GRAPHITI_SEPARATOR = "__"


def sanitize_group_id_for_graphiti(canvas_group_id: str) -> str:
    """Convert Canvas D16 group_id to Graphiti-safe form.

    Examples:
        vault:cs_61b              → vault__cs_61b
        vault:cs_61b:algorithms   → vault__cs_61b__algorithms
        vault:default             → vault__default
        cs188 (legacy, no colon)  → cs188 (unchanged)

    Args:
        canvas_group_id: Canvas-side group_id in D16 format.

    Returns:
        Graphiti-safe equivalent (only [A-Za-z0-9_-] characters).
    """
    if not canvas_group_id:
        return canvas_group_id
    return canvas_group_id.replace(":", _GRAPHITI_SEPARATOR)


def desanitize_group_id_from_graphiti(graphiti_group_id: str) -> str:
    """Convert Graphiti-stored group_id back to Canvas D16 format.

    Inverse of `sanitize_group_id_for_graphiti`. Useful when surfacing
    Graphiti's group_id back to Canvas-side code that expects D16 colons.

    Caveat: this uses a simple "__" → ":" replace, which is unambiguous
    only if no Canvas group_id segment legitimately contains "__".
    D16 segments are vault_id / subject_id which use single underscores
    (cs_61b, not cs__61b), so this is safe under the current spec.
    """
    if not graphiti_group_id:
        return graphiti_group_id
    return graphiti_group_id.replace(_GRAPHITI_SEPARATOR, ":")
