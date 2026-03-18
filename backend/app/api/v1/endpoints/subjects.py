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
from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.models.subject_models import (
    SubjectCreate,
    SubjectListResponse,
    SubjectResponse,
    SubjectUpdate,
)

logger = logging.getLogger(__name__)

subjects_router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_neo4j_driver():
    """
    Create an async Neo4j driver from application settings.

    Uses the same configuration as the rest of the backend
    (NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD).
    """
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )
    return driver


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

    [Source: Story 1.9 Task 8 — GET /api/v1/subjects/]
    """
    driver = await _get_neo4j_driver()
    try:
        settings = get_settings()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run(
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
            records = await result.data()

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
    finally:
        await driver.close()


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

    driver = await _get_neo4j_driver()
    try:
        settings = get_settings()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Check duplicate name
            dup_result = await session.run(
                "MATCH (s:Subject {name: $name}) RETURN s.id AS id LIMIT 1",
                name=body.name,
            )
            dup_record = await dup_result.single()
            if dup_record:
                raise HTTPException(
                    status_code=409,
                    detail=f"Subject with name '{body.name}' already exists "
                    f"(id={dup_record['id']})",
                )

            await session.run(
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
            subject_id, body.name,
        )
        return SubjectResponse(
            id=subject_id,
            name=body.name,
            color=body.color,
            created_at=now_iso,
            node_count=0,
        )
    finally:
        await driver.close()


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

    [Source: Story 1.9 Task 8 — PUT /api/v1/subjects/{id}]
    """
    if body.name is None and body.color is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'name' or 'color' must be provided",
        )

    driver = await _get_neo4j_driver()
    try:
        settings = get_settings()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Build dynamic SET clause
            set_parts: list[str] = []
            params: dict = {"subject_id": subject_id}

            if body.name is not None:
                set_parts.append("s.name = $name")
                params["name"] = body.name
            if body.color is not None:
                set_parts.append("s.color = $color")
                params["color"] = body.color

            set_clause = ", ".join(set_parts)
            result = await session.run(
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
            record = await result.single()

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Subject {subject_id} not found",
            )

        # Fetch node count separately to keep the update query simple
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            cnt_result = await session.run(
                "MATCH (n:CanvasNode {subjectId: $sid}) RETURN count(n) AS c",
                sid=subject_id,
            )
            cnt_record = await cnt_result.single()
            node_count = cnt_record["c"] if cnt_record else 0

        logger.info("[Story 1.9] Subject updated: id=%s", subject_id)
        return SubjectResponse(
            id=record["id"],
            name=record["name"],
            color=record.get("color"),
            created_at=record.get("createdAt", ""),
            node_count=node_count,
        )
    finally:
        await driver.close()


# ---------------------------------------------------------------------------
# DELETE /subjects/{subject_id} -- soft-delete (remove :Subject node only)
# ---------------------------------------------------------------------------

@subjects_router.delete(
    "/{subject_id}",
    summary="Delete a subject",
    description=(
        "Remove the :Subject node. Associated CanvasNode and CanvasBoard "
        "data is NOT deleted (soft-delete)."
    ),
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
    driver = await _get_neo4j_driver()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        settings = get_settings()
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run(
                """
                MATCH (s:Subject {id: $subject_id})
                WITH s, s.name AS name
                DELETE s
                RETURN name
                """,
                subject_id=subject_id,
            )
            record = await result.single()

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Subject {subject_id} not found",
            )

        logger.info(
            "[Story 1.9] Subject deleted: id=%s name=%s",
            subject_id, record["name"],
        )
        return {
            "data": {
                "status": "ok",
                "subject_id": subject_id,
                "message": f"Subject '{record['name']}' deleted (data preserved)",
            },
            "meta": {"timestamp": now_iso},
        }
    finally:
        await driver.close()
