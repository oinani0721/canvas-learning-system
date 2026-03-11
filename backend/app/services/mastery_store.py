"""
Mastery Store - Neo4j EntityNode Persistence Layer

Reads and writes ConceptState to/from Neo4j EntityNode properties.
Uses MERGE upsert pattern to create or update mastery data on existing nodes.

All mastery properties are stored as prefixed flat properties on EntityNode
to avoid schema changes to the existing graph model.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.mastery_state import ConceptState

logger = logging.getLogger(__name__)


class MasteryStore:
    """Read/write ConceptState to/from Neo4j EntityNode properties."""

    def __init__(self, neo4j_client):
        """
        Args:
            neo4j_client: Neo4jClient instance from app.clients.neo4j_client
        """
        self._client = neo4j_client

    async def get_concept(self, concept_id: str, group_id: str = "cs188") -> Optional[ConceptState]:
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
                query, concept_id=concept_id, group_id=group_id,
            )
            if records and len(records) > 0:
                props = records[0]["props"] if isinstance(records[0], dict) else records[0].data()["props"]
                return ConceptState.from_neo4j_props(props)
            return None
        except Exception as e:
            logger.warning(f"Failed to get concept {concept_id}: {e}")
            return None

    async def save_concept(self, concept: ConceptState, group_id: str = "cs188") -> None:
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
        except Exception as e:
            logger.error(f"Failed to save concept {concept.concept_id}: {e}")

    async def get_all_concepts(self, group_id: str = "cs188") -> list[ConceptState]:
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
                props = record["props"] if isinstance(record, dict) else record.data()["props"]
                results.append(ConceptState.from_neo4j_props(props))
            return results
        except Exception as e:
            logger.warning(f"Failed to get all concepts for {group_id}: {e}")
            return []

    async def get_or_create_concept(
        self,
        concept_id: str,
        topic: str = "",
        name: str = "",
        group_id: str = "cs188",
    ) -> ConceptState:
        """
        Get existing concept or create a new one with defaults.

        Used by API endpoints when a concept_id is referenced for the first time.
        """
        existing = await self.get_concept(concept_id, group_id)
        if existing:
            return existing

        concept = ConceptState(
            concept_id=concept_id,
            topic=topic or "Unknown",
            name=name or concept_id,
        )
        await self.save_concept(concept, group_id)
        return concept

    async def record_interaction_event(
        self,
        concept_id: str,
        grade: int,
        group_id: str = "cs188",
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
        except Exception as e:
            logger.warning(f"Failed to record interaction for {concept_id}: {e}")

    async def record_override_event(
        self,
        concept_id: str,
        level: str,
        reason: str = "",
        group_id: str = "cs188",
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
        except Exception as e:
            logger.warning(f"Failed to record override for {concept_id}: {e}")

    async def find_concept_by_name(
        self, name: str, group_id: str = "cs188",
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
                query, group_id=group_id, name=name,
            )
            if records and len(records) > 0:
                props = records[0]["props"] if isinstance(records[0], dict) else records[0].data()["props"]
                return ConceptState.from_neo4j_props(props)
            return None
        except Exception as e:
            logger.warning(f"Failed to find concept by name '{name}': {e}")
            return None

    async def record_self_assess_event(
        self,
        concept_id: str,
        color: str,
        group_id: str = "cs188",
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
        except Exception as e:
            logger.warning(f"Failed to record self-assess for {concept_id}: {e}")
