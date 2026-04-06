"""
Mastery Store - Neo4j EntityNode Persistence Layer

Reads and writes ConceptState to/from Neo4j EntityNode properties.
Uses MERGE upsert pattern to create or update mastery data on existing nodes.

All mastery properties are stored as prefixed flat properties on EntityNode
to avoid schema changes to the existing graph model.

Story 5.5: CalibrationRecord persistence (mastery_calibration_records JSON property)
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import structlog
from typing import List, Optional

from app.config import DEFAULT_GROUP_ID
from app.models.mastery_models import CalibrationRecord
from app.models.mastery_state import ConceptState

logger = structlog.get_logger(__name__)


class MasteryStore:
    """Read/write ConceptState to/from Neo4j EntityNode properties."""

    def __init__(self, neo4j_client):
        """
        Args:
            neo4j_client: Neo4jClient instance from app.clients.neo4j_client
        """
        self._client = neo4j_client

    async def get_concept(
        self, concept_id: str, group_id: str = DEFAULT_GROUP_ID
    ) -> Optional[ConceptState]:
        """
        Load a single concept's mastery state from Neo4j.

        Looks for EntityNode with matching mastery_concept_id or name.
        """
        query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND (n.mastery_concept_id = $concept_id OR n.name = $concept_id)
          AND n.p_mastery IS NOT NULL
        RETURN properties(n) AS props
        LIMIT 1
        """
        try:
            records = await self._client.run_query(
                query,
                concept_id=concept_id,
                group_id=group_id,
            )
            if records and len(records) > 0:
                props = (
                    records[0]["props"]
                    if isinstance(records[0], dict)
                    else records[0].data()["props"]
                )
                return ConceptState.from_neo4j_props(props)
            return None
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to get concept {concept_id}: {e}")
            return None

    async def save_concept(
        self, concept: ConceptState, group_id: str = DEFAULT_GROUP_ID
    ) -> None:
        """
        Save (upsert) concept mastery state to Neo4j EntityNode.

        Uses MERGE on mastery_concept_id to create or update.
        """
        props = concept.to_neo4j_props()
        props["group_id"] = group_id
        props["updated_at"] = datetime.now(timezone.utc).isoformat()

        query = """
        MERGE (n:EntityNode {group_id: $group_id, mastery_concept_id: $concept_id})
        ON CREATE SET n += $props, n.created_at = datetime()
        ON MATCH SET n += $props
        """
        try:
            await self._client.run_query(
                query,
                group_id=group_id,
                concept_id=concept.concept_id,
                props=props,
            )
            logger.debug(f"Saved mastery state for {concept.concept_id}")
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to save concept {concept.concept_id}: {e}")

    async def get_all_concepts(
        self, group_id: str = DEFAULT_GROUP_ID
    ) -> list[ConceptState]:
        """
        Load all concepts with mastery data for a group.

        Returns concepts that have p_mastery property set.
        """
        query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND n.p_mastery IS NOT NULL
        RETURN properties(n) AS props
        ORDER BY n.mastery_topic, n.mastery_name
        """
        try:
            records = await self._client.run_query(query, group_id=group_id)
            results = []
            for record in records or []:
                props = (
                    record["props"]
                    if isinstance(record, dict)
                    else record.data()["props"]
                )
                results.append(ConceptState.from_neo4j_props(props))
            return results
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to get all concepts for {group_id}: {e}")
            return []

    async def get_or_create_concept(
        self,
        concept_id: str,
        topic: str = "",
        name: str = "",
        group_id: str = DEFAULT_GROUP_ID,
        bkt_difficulty: str = "medium",
    ) -> ConceptState:
        """
        Get existing concept or create a new one with defaults.

        Uses BKT P_L0 (prior probability) from DEFAULT_BKT_PARAMS to
        initialize p_mastery based on the concept's difficulty level.

        Used by API endpoints when a concept_id is referenced for the first time.
        """
        from app.models.mastery_state import DEFAULT_BKT_PARAMS

        existing = await self.get_concept(concept_id, group_id)
        if existing:
            return existing

        # Initialize p_mastery from BKT P_L0 for the given difficulty
        params = DEFAULT_BKT_PARAMS.get(bkt_difficulty, DEFAULT_BKT_PARAMS["medium"])
        initial_p_mastery = params["P_L0"]

        concept = ConceptState(
            concept_id=concept_id,
            topic=topic or "Unknown",
            name=name or concept_id,
            p_mastery=initial_p_mastery,
            bkt_difficulty=bkt_difficulty,
        )
        await self.save_concept(concept, group_id)
        return concept

    async def record_interaction_event(
        self,
        concept_id: str,
        grade: int,
        group_id: str = DEFAULT_GROUP_ID,
        source: str = "interaction",
    ) -> None:
        """
        Record an interaction event on the EntityNode.

        Phase 1: Simple property update. Phase 2: Separate EpisodicNode.
        """
        query = """
        MATCH (n:EntityNode {group_id: $group_id, mastery_concept_id: $concept_id})
        SET n.last_grade = $grade,
            n.last_grade_ts = datetime(),
            n.grade_source = $source
        """
        try:
            await self._client.run_query(
                query,
                group_id=group_id,
                concept_id=concept_id,
                grade=grade,
                source=source,
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to record interaction for {concept_id}: {e}")

    async def record_override_event(
        self,
        concept_id: str,
        level: str,
        reason: str = "",
        group_id: str = DEFAULT_GROUP_ID,
    ) -> None:
        """Record an override event on the EntityNode."""
        query = """
        MATCH (n:EntityNode {group_id: $group_id, mastery_concept_id: $concept_id})
        SET n.last_override_level = $level,
            n.last_override_reason = $reason,
            n.last_override_ts = datetime(),
            n.source_description = "mastery-override"
        """
        try:
            await self._client.run_query(
                query,
                group_id=group_id,
                concept_id=concept_id,
                level=level,
                reason=reason,
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to record override for {concept_id}: {e}")

    async def find_concept_by_name(
        self,
        name: str,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> Optional[ConceptState]:
        """
        Find a concept by fuzzy name match (case-insensitive CONTAINS).

        Used by Graphiti bridge when concept_id is unknown but concept name
        is available from a Misconception/ProblemTrap episode_body.
        """
        query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND n.p_mastery IS NOT NULL
          AND toLower(n.mastery_name) CONTAINS toLower($name)
        RETURN properties(n) AS props
        ORDER BY size(n.mastery_name) ASC
        LIMIT 1
        """
        try:
            records = await self._client.run_query(
                query,
                group_id=group_id,
                name=name,
            )
            if records and len(records) > 0:
                props = (
                    records[0]["props"]
                    if isinstance(records[0], dict)
                    else records[0].data()["props"]
                )
                return ConceptState.from_neo4j_props(props)
            return None
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to find concept by name '{name}': {e}")
            return None

    async def get_board_concepts(
        self,
        board_id: str,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> list[ConceptState]:
        """Load mastery data for all concept nodes belonging to a canvas board.

        Joins Canvas -> CONTAINS_NODE -> Node with EntityNode mastery data.
        The board_id is the canvas path (e.g. "学习笔记.canvas" or "学习笔记").
        Nodes are matched by Node.id == EntityNode.mastery_concept_id.

        Falls back to all concepts in the group if no Canvas-Node relationships
        exist yet (board data not synced).

        Returns:
            List of ConceptState objects for nodes on the specified board.
            Empty list on Neo4j errors (graceful degradation, consistent
            with get_all_concepts pattern).
        """
        # Try matching via Canvas -> CONTAINS_NODE -> Node -> EntityNode
        query = """
        MATCH (c:Canvas)-[:CONTAINS_NODE]->(n:Node)
        WHERE c.path = $board_id OR c.path = $board_id_with_ext
        WITH collect(n.id) AS node_ids
        MATCH (e:EntityNode)
        WHERE e.group_id = $group_id
          AND e.p_mastery IS NOT NULL
          AND e.mastery_concept_id IN node_ids
        RETURN properties(e) AS props
        ORDER BY e.mastery_topic, e.mastery_name
        """
        try:
            # Try with and without .canvas extension
            board_id_with_ext = (
                board_id if board_id.endswith(".canvas") else board_id + ".canvas"
            )
            board_id_without_ext = board_id.removesuffix(".canvas")

            records = await self._client.run_query(
                query,
                board_id=board_id_without_ext,
                board_id_with_ext=board_id_with_ext,
                group_id=group_id,
            )

            results: list[ConceptState] = []
            for record in records or []:
                props = (
                    record["props"]
                    if isinstance(record, dict)
                    else record.data()["props"]
                )
                results.append(ConceptState.from_neo4j_props(props))

            if results:
                return results

            # Fallback: if no Canvas-Node relationships exist yet,
            # return all concepts for the group (same as batch endpoint)
            logger.debug(
                f"No Canvas-Node relationships found for board '{board_id}', "
                f"falling back to all concepts in group '{group_id}'"
            )
            return await self.get_all_concepts(group_id)

        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to get board concepts for '{board_id}': {e}")
            # Graceful degradation: same pattern as get_all_concepts
            empty: list[ConceptState] = []
            return empty

    async def record_self_assess_event(
        self,
        concept_id: str,
        color: str,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> None:
        """Record a self-assessment event (Canvas color change)."""
        query = """
        MATCH (n:EntityNode {group_id: $group_id, mastery_concept_id: $concept_id})
        SET n.last_self_assess_color = $color,
            n.last_self_assess_ts = datetime(),
            n.source_description = "self-assessment"
        """
        try:
            await self._client.run_query(
                query,
                group_id=group_id,
                concept_id=concept_id,
                color=color,
            )
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.warning(f"Failed to record self-assess for {concept_id}: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Story 5.5: Calibration Record Persistence
    # ═══════════════════════════════════════════════════════════════════════════

    async def save_calibration_record(
        self,
        record: CalibrationRecord,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> None:
        """Append a CalibrationRecord to the node's calibration history.

        Storage: JSON-serialized list in mastery_calibration_records property.
        Uses read-modify-write with json.loads/json.dumps to avoid string
        concatenation errors on malformed JSON.
        """
        record_dict = record.model_dump(mode="json")

        # Step 1: Read existing records
        read_query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
        RETURN n.mastery_calibration_records AS records_json
        LIMIT 1
        """
        try:
            results = await self._client.run_query(
                read_query,
                group_id=group_id,
                node_id=record.node_id,
            )

            existing_records = []
            if results:
                raw = (
                    results[0]["records_json"]
                    if isinstance(results[0], dict)
                    else results[0].data()["records_json"]
                )
                if raw:
                    existing_records = json.loads(raw)

            # Step 2: Append new record and serialize with json.dumps
            existing_records.append(record_dict)
            updated_json = json.dumps(existing_records, ensure_ascii=False)

            # Step 3: Write back
            write_query = """
            MATCH (n:EntityNode)
            WHERE n.group_id = $group_id
              AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
            SET n.mastery_calibration_records = $records_json,
                n.mastery_calibration_count = coalesce(n.mastery_calibration_count, 0) + 1,
                n.mastery_calibration_last_quadrant = $quadrant,
                n.mastery_calibration_is_dangerous = $is_dangerous
            """
            await self._client.run_query(
                write_query,
                group_id=group_id,
                node_id=record.node_id,
                records_json=updated_json,
                quadrant=record.quadrant.value,
                is_dangerous=record.is_dangerous,
            )
            logger.debug(
                f"Saved calibration record for {record.node_id}: "
                f"quadrant={record.quadrant.value} is_dangerous={record.is_dangerous}"
            )
        except (
            RuntimeError,
            ConnectionError,
            asyncio.TimeoutError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as e:
            logger.error(f"Failed to save calibration record for {record.node_id}: {e}")

    async def get_calibration_records(
        self,
        node_id: str,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> List[CalibrationRecord]:
        """Load all CalibrationRecords for a given node.

        Deserializes from the mastery_calibration_records JSON property.

        Returns:
            List of CalibrationRecord objects. Empty list on Neo4j errors
            (graceful degradation consistent with get_all_concepts pattern).
        """
        query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND (n.mastery_concept_id = $node_id OR n.name = $node_id)
          AND n.mastery_calibration_records IS NOT NULL
        RETURN n.mastery_calibration_records AS records_json
        LIMIT 1
        """
        results = await self._client.run_query(
            query,
            group_id=group_id,
            node_id=node_id,
        )
        if not results:
            return []

        records_json = (
            results[0]["records_json"]
            if isinstance(results[0], dict)
            else results[0].data()["records_json"]
        )
        if not records_json:
            return []

        raw_list = json.loads(records_json)
        parsed: List[CalibrationRecord] = []
        for item in raw_list:
            if isinstance(item, str):
                parsed.append(CalibrationRecord.model_validate_json(item))
            else:
                parsed.append(CalibrationRecord.model_validate(item))
        return parsed

    async def get_dangerous_nodes(
        self,
        group_id: str = DEFAULT_GROUP_ID,
    ) -> List[str]:
        """Return node IDs that have MISCONCEPTION quadrant records.

        Used for prioritizing exam questions on dangerous blind spots.

        Returns:
            List of node_id strings. Empty list when no dangerous nodes exist
            (this is a valid state, not a fallback).
        """
        query = """
        MATCH (n:EntityNode)
        WHERE n.group_id = $group_id
          AND n.mastery_calibration_is_dangerous = true
        RETURN n.mastery_concept_id AS node_id,
               coalesce(n.mastery_calibration_count, 0) AS record_count
        ORDER BY record_count DESC
        """
        results = await self._client.run_query(query, group_id=group_id)
        if not results:
            return []
        node_ids: List[str] = []
        for r in results:
            nid = r["node_id"] if isinstance(r, dict) else r.data()["node_id"]
            if nid is not None:
                node_ids.append(nid)
        return node_ids


# ═══════════════════════════════════════════════════════════════════════════════
# Service-level singleton accessor
# ═══════════════════════════════════════════════════════════════════════════════

_store_instance: MasteryStore | None = None


def get_mastery_store() -> MasteryStore:
    """Get or create the singleton MasteryStore instance.

    Provides a service-layer accessor so that event handlers and other
    services don't need to import private helpers from API endpoint modules.
    """
    global _store_instance
    if _store_instance is None:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        _store_instance = MasteryStore(client)
    return _store_instance
