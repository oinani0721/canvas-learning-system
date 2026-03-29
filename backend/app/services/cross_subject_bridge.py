# Canvas Learning System - Cross-Subject Bridge Service
# Story 1.9: Tag Jaccard bridging for cross-subject retrieval (AC-5)
"""
Computes Tag Jaccard similarity between subjects to determine
which subjects should be included in cross-subject search.

Jaccard(A, B) = |A intersection B| / |A union B|
Tags source: node keywords, frontmatter tags.

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 7]
"""

import asyncio
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


def compute_tag_jaccard(tags_a: Set[str], tags_b: Set[str]) -> float:
    """
    Compute Jaccard similarity between two tag sets.

    Args:
        tags_a: Tag set for subject A.
        tags_b: Tag set for subject B.

    Returns:
        Jaccard coefficient (0.0 to 1.0).
    """
    if not tags_a and not tags_b:
        return 0.0
    intersection = tags_a & tags_b
    union = tags_a | tags_b
    if len(union) == 0:
        return 0.0
    return len(intersection) / len(union)


async def find_related_subjects(
    current_subject_id: str,
    all_subject_tags: Dict[str, Set[str]],
    threshold: float = 0.3,
) -> List[str]:
    """
    Find subjects related to the current one by Tag Jaccard similarity.

    Args:
        current_subject_id: The active subject.
        all_subject_tags: Mapping of subject_id -> set of tags.
        threshold: Minimum Jaccard coefficient to consider related (default 0.3).

    Returns:
        List of subject_ids that exceed the threshold.
    """
    current_tags = all_subject_tags.get(current_subject_id, set())
    if not current_tags:
        # No tags for current subject => no similarity can be computed
        empty: List[str] = []
        return empty

    related: List[str] = []  # ruff C408: use literal
    for subject_id, tags in all_subject_tags.items():
        if subject_id == current_subject_id:
            continue
        similarity = compute_tag_jaccard(current_tags, tags)
        if similarity >= threshold:
            related.append(subject_id)
            logger.debug(
                f"Cross-subject bridge: {current_subject_id} <-> {subject_id} "
                f"Jaccard={similarity:.3f} (threshold={threshold})"
            )

    return related


async def expand_search_subjects(
    current_subject_id: str,
    neo4j_driver: object,
    threshold: float = 0.3,
) -> List[str]:
    """
    Expand the search scope to include related subjects via Tag Jaccard.

    Called when ``cross_subject=True`` in a RAG query.  Fetches tags for
    all subjects from Neo4j, computes Jaccard similarity against the
    current subject, and returns a list that includes the current subject
    plus any related subjects exceeding the threshold.

    Args:
        current_subject_id: The subject the user is currently working in.
        neo4j_driver: Async Neo4j driver for tag extraction.
        threshold: Minimum Jaccard coefficient to include a subject.

    Returns:
        List of subject_ids to search (always includes *current_subject_id*).
    """
    # 1. Fetch all known subjects from Neo4j
    all_subject_ids: List[str] = []
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(
                "MATCH (s:Subject) RETURN s.id AS id"
            )
            records = await result.data()
            all_subject_ids = [r["id"] for r in records if r.get("id")]
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"expand_search_subjects: failed to list subjects: {e}")
        return [current_subject_id]

    if not all_subject_ids:
        return [current_subject_id]

    # 2. Fetch tags for each subject
    all_tags: Dict[str, Set[str]] = {}
    for sid in all_subject_ids:
        all_tags[sid] = await get_subject_tags_from_neo4j(neo4j_driver, sid)

    # 3. Find related subjects
    related = await find_related_subjects(
        current_subject_id, all_tags, threshold=threshold
    )

    # 4. Always include the current subject first
    result_subjects = [current_subject_id]
    for sid in related:
        if sid != current_subject_id:
            result_subjects.append(sid)

    logger.info(
        f"expand_search_subjects: {current_subject_id} -> {result_subjects} "
        f"(threshold={threshold})"
    )
    return result_subjects


async def get_subject_tags_from_neo4j(
    neo4j_driver: object,
    subject_id: str,
) -> Set[str]:
    """
    Extract tags for a subject from Neo4j node keywords and content.

    Args:
        neo4j_driver: Neo4j async driver.
        subject_id: Subject identifier.

    Returns:
        Set of tags extracted from nodes in this subject.
    """
    tags: Set[str] = set()
    query = """
    MATCH (n:CanvasNode {subjectId: $subject_id})
    WHERE n.title IS NOT NULL
    RETURN n.title AS title, n.ocrConcepts AS concepts
    """
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(query, subject_id=subject_id)
            records = await result.data()
            for rec in records:
                # Add title words as tags
                title = rec.get("title", "")
                if title:
                    for word in title.lower().split():
                        if len(word) > 1:
                            tags.add(word)
                # Add OCR concepts if present
                concepts = rec.get("concepts")
                if concepts and isinstance(concepts, list):
                    for concept in concepts:
                        tags.add(concept.lower().strip())
    except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
        logger.warning(f"Failed to get tags for subject {subject_id}: {e}")

    return tags
