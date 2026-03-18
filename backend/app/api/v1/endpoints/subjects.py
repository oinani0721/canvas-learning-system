# Canvas Learning System - Subjects API
# Story 1.9: Multi-Subject Knowledge Graph Isolation (Task 8)
"""
CRUD endpoints for user-managed subjects.

Each subject is persisted as a ``:Subject`` node in Neo4j with properties:
    id (str), name (str), color (str|null), createdAt (str).

Deleting a subject only removes the ``:Subject`` node; all associated
``CanvasNode`` / ``CanvasBoard`` data is preserved (soft-delete).

[Source: _bmad-output/implementation-artifacts/1-9-multi-subject-kg-isolation.md#Task 8]
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.clients.neo4j_client import get_neo4j_client
from app.models.subject_models import (
    SubjectCreate,
    SubjectListResponse,
    SubjectResponse,
    SubjectUpdate,
)

logger = logging.getLogger(__name__)

subjects_router = APIRouter()


def _generate_subject_id() -> str:
    """Generate a short unique identifier for a subject."""
    return f"subj_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# GET /subjects/ -- list all subjects
# ---------------------------------------------------------------------------


@subjects_router.get(
    "/",
    response_model=SubjectListResponse,
    summary="List all subjects",
    description="Returns every user-created subject with a node count.",
    tags=["Subjects"],
)
async def list_subjects() -> SubjectListResponse:
    """
    Fetch every ``:Subject`` node from Neo4j together with the number
    of ``CanvasNode`` entries that reference each subject.

    HIGH-1 fix: Uses shared Neo4jClient singleton instead of per-request driver.

    [Source: Story 1.9 Task 8 — GET /api/v1/subjects/]
    """
    neo4j_client = get_neo4j_client()
    records = await neo4j_client.run_query(
        """
        MATCH (s:Subject)
        OPTIONAL MATCH (n:CanvasNode {subjectId: s.id})
        RETURN s.id        AS id,
               s.name      AS name,
               s.color     AS color,
               s.createdAt AS createdAt,
               count(n)    AS nodeCount
        ORDER BY s.createdAt ASC
        """
    )

    subjects = [
        SubjectResponse(
            id=rec["id"],
            name=rec["name"],
            color=rec.get("color"),
            created_at=rec.get("createdAt", ""),
            node_count=rec.get("nodeCount", 0),
        )
        for rec in records
    ]
    return SubjectListResponse(subjects=subjects, total=len(subjects))


# ---------------------------------------------------------------------------
# POST /subjects/ -- create a new subject
# ---------------------------------------------------------------------------


@subjects_router.post(
    "/",
    response_model=SubjectResponse,
    status_code=201,
    summary="Create a subject",
    description="Persist a new :Subject node in Neo4j.",
    tags=["Subjects"],
)
async def create_subject(body: SubjectCreate) -> SubjectResponse:
    """
    Create a new subject.

    Generates a unique ``id`` and stores a ``:Subject`` node in Neo4j.

    [Source: Story 1.9 Task 8 — POST /api/v1/subjects/]
    """
    subject_id = _generate_subject_id()
    now_iso = datetime.now(timezone.utc).isoformat()

    neo4j_client = get_neo4j_client()

    # Check duplicate name
    dup_records = await neo4j_client.run_query(
        "MATCH (s:Subject {name: $name}) RETURN s.id AS id LIMIT 1",
        name=body.name,
    )
    if dup_records:
        raise HTTPException(
            status_code=409,
            detail=f"Subject with name '{body.name}' already exists (id={dup_records[0]['id']})",
        )

    await neo4j_client.run_query(
        """
        CREATE (s:Subject {
            id: $id,
            name: $name,
            color: $color,
            createdAt: $created_at
        })
        """,
        id=subject_id,
        name=body.name,
        color=body.color,
        created_at=now_iso,
    )

    logger.info(
        "[Story 1.9] Subject created: id=%s name=%s",
        subject_id,
        body.name,
    )
    return SubjectResponse(
        id=subject_id,
        name=body.name,
        color=body.color,
        created_at=now_iso,
        node_count=0,
    )


# ---------------------------------------------------------------------------
# PUT /subjects/{subject_id} -- update subject name / color
# ---------------------------------------------------------------------------


@subjects_router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update a subject",
    description="Update the name and/or color of an existing subject.",
    tags=["Subjects"],
)
async def update_subject(subject_id: str, body: SubjectUpdate) -> SubjectResponse:
    """
    Update subject properties.

    Only ``name`` and ``color`` can be changed.  If neither field is
    provided the endpoint returns 400.

    HIGH-2 fix: Added duplicate name check (same logic as create_subject).

    [Source: Story 1.9 Task 8 — PUT /api/v1/subjects/{id}]
    """
    if body.name is None and body.color is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'name' or 'color' must be provided",
        )

    neo4j_client = get_neo4j_client()

    # HIGH-2 fix: Check for duplicate name (exclude current subject from check)
    if body.name is not None:
        dup_records = await neo4j_client.run_query(
            "MATCH (s:Subject {name: $name}) WHERE s.id <> $subject_id RETURN s.id AS id LIMIT 1",
            name=body.name,
            subject_id=subject_id,
        )
        if dup_records:
            raise HTTPException(
                status_code=409,
                detail=f"Subject with name '{body.name}' already exists (id={dup_records[0]['id']})",
            )

    # HIGH-3 safety note: The SET clause is built from hardcoded property
    # names only ("s.name = $name", "s.color = $color"). All actual values
    # are passed as Cypher parameters ($name, $color), so there is no
    # injection risk. The f-string only interpolates the fixed set_parts.
    set_parts: list[str] = []
    params: dict = {"subject_id": subject_id}

    if body.name is not None:
        set_parts.append("s.name = $name")
        params["name"] = body.name
    if body.color is not None:
        set_parts.append("s.color = $color")
        params["color"] = body.color

    set_clause = ", ".join(set_parts)
    update_records = await neo4j_client.run_query(
        f"""
        MATCH (s:Subject {{id: $subject_id}})
        SET {set_clause}
        RETURN s.id        AS id,
               s.name      AS name,
               s.color     AS color,
               s.createdAt AS createdAt
        """,
        **params,
    )

    if not update_records:
        raise HTTPException(
            status_code=404,
            detail=f"Subject {subject_id} not found",
        )

    record = update_records[0]

    # Fetch node count separately to keep the update query simple
    cnt_records = await neo4j_client.run_query(
        "MATCH (n:CanvasNode {subjectId: $sid}) RETURN count(n) AS c",
        sid=subject_id,
    )
    node_count = cnt_records[0]["c"] if cnt_records else 0

    logger.info("[Story 1.9] Subject updated: id=%s", subject_id)
    return SubjectResponse(
        id=record["id"],
        name=record["name"],
        color=record.get("color"),
        created_at=record.get("createdAt", ""),
        node_count=node_count,
    )


# ---------------------------------------------------------------------------
# DELETE /subjects/{subject_id} -- soft-delete (remove :Subject node only)
# ---------------------------------------------------------------------------


@subjects_router.delete(
    "/{subject_id}",
    summary="Delete a subject",
    description=("Remove the :Subject node. Associated CanvasNode and CanvasBoard data is NOT deleted (soft-delete)."),
    tags=["Subjects"],
)
async def delete_subject(subject_id: str) -> dict:
    """
    Soft-delete a subject.

    Only the ``:Subject`` metadata node is removed.  All ``CanvasNode``
    entries that reference this ``subjectId`` are left intact so that
    data is never lost.

    [Source: Story 1.9 Task 8 — DELETE /api/v1/subjects/{id}]
    """
    neo4j_client = get_neo4j_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    records = await neo4j_client.run_query(
        """
        MATCH (s:Subject {id: $subject_id})
        WITH s, s.name AS name
        DELETE s
        RETURN name
        """,
        subject_id=subject_id,
    )

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"Subject {subject_id} not found",
        )

    logger.info(
        "[Story 1.9] Subject deleted: id=%s name=%s",
        subject_id,
        records[0]["name"],
    )
    return {
        "data": {
            "status": "ok",
            "subject_id": subject_id,
            "message": f"Subject '{records[0]['name']}' deleted (data preserved)",
        },
        "meta": {"timestamp": now_iso},
    }
