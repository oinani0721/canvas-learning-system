# ✅ Verified from Story 12.3 AC 3.4 - Dual Write Adapter
# ✅ Verified from Architecture doc - VectorDatabaseAdapter pattern
"""
Dual Write Adapter Module

Implements dual-write pattern for gradual migration from ChromaDB to LanceDB.
All writes go to both databases simultaneously during migration period.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WriteResult:
    """Result of a write operation."""

    success: bool
    primary_success: bool
    secondary_success: bool
    latency_ms: float
    errors: List[str] = field(default_factory=list)


@dataclass
class DualWriteStats:
    """Statistics for dual write operations."""

    total_writes: int = 0
    successful_writes: int = 0
    failed_writes: int = 0
    primary_failures: int = 0
    secondary_failures: int = 0
    avg_latency_ms: float = 0.0
    last_write_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_writes": self.total_writes,
            "successful_writes": self.successful_writes,
            "failed_writes": self.failed_writes,
            "primary_failures": self.primary_failures,
            "secondary_failures": self.secondary_failures,
            "avg_latency_ms": self.avg_latency_ms,
            "last_write_time": self.last_write_time.isoformat() if self.last_write_time else None,
        }


class VectorDatabaseAdapter(ABC):
    """
    Abstract base class for vector database adapters.

    Defines the interface for storing and searching vector memories.
    """

    @abstractmethod
    def store_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory with its embedding.

        Args:
            memory_id: Unique identifier for the memory
            content: Text content of the memory
            embedding: Vector embedding of the content
            metadata: Optional metadata dictionary

        Returns:
            The memory ID that was stored
        """
        pass

    @abstractmethod
    def search_memory(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            filter_dict: Optional metadata filters

        Returns:
            List of matching memories with scores
        """
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory by ID.

        Args:
            memory_id: ID of memory to retrieve

        Returns:
            Memory dict or None if not found
        """
        pass


class ChromaDBAdapter(VectorDatabaseAdapter):
    """ChromaDB implementation of VectorDatabaseAdapter."""

    def __init__(self, client: Any, collection_name: str):
        """
        Initialize ChromaDB adapter.

        Args:
            client: ChromaDB client instance
            collection_name: Name of collection to use
        """
        self.client = client
        self.collection_name = collection_name
        self._collection = None

    @property
    def collection(self):
        """Lazy load collection."""
        if self._collection is None and self.client:
            self._collection = self.client.get_or_create_collection(self.collection_name)
        return self._collection

    def store_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in ChromaDB."""
        if self.collection is None:
            raise ValueError("ChromaDB collection not available")

        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}]
        )
        return memory_id

    def search_memory(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search memories in ChromaDB."""
        if self.collection is None:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter_dict
        )

        memories = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            memories.append({
                "id": doc_id,
                "content": documents[i] if documents else None,
                "metadata": metadatas[i] if metadatas else {},
                "score": 1 - distances[i] if distances else 0,  # Convert distance to similarity
            })

        return memories

    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from ChromaDB."""
        if self.collection is None:
            return False

        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from ChromaDB."""
        if self.collection is None:
            return None

        try:
            results = self.collection.get(
                ids=[memory_id],
                include=["documents", "metadatas", "embeddings"]
            )
            if results["ids"]:
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0] if results["documents"] else None,
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                    "embedding": results["embeddings"][0] if results["embeddings"] else None,
                }
        except Exception:
            pass
        return None


class LanceDBAdapter(VectorDatabaseAdapter):
    """LanceDB implementation of VectorDatabaseAdapter."""

    def __init__(self, connection: Any, table_name: str):
        """
        Initialize LanceDB adapter.

        Args:
            connection: LanceDB connection instance
            table_name: Name of table to use
        """
        self.connection = connection
        self.table_name = table_name
        self._table = None

    @property
    def table(self):
        """Lazy load table."""
        if self._table is None and self.connection:
            try:
                self._table = self.connection.open_table(self.table_name)
            except Exception:
                # Table doesn't exist yet
                pass
        return self._table

    def _ensure_table(self, record: Dict[str, Any]) -> None:
        """Create table if it doesn't exist."""
        if self._table is None and self.connection:
            self._table = self.connection.create_table(
                self.table_name,
                data=[record]
            )

    def store_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in LanceDB."""
        record = {
            "id": memory_id,
            "text": content,
            "vector": embedding,
            **(metadata or {})
        }

        if self.table is None:
            self._ensure_table(record)
        else:
            # Add to existing table
            self.table.add([record])

        return memory_id

    def search_memory(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search memories in LanceDB."""
        if self.table is None:
            return []

        try:
            # ✅ Verified from Context7 - LanceDB search
            query = self.table.search(query_embedding).limit(limit)

            if filter_dict:
                # Build filter string
                filter_parts = []
                for key, value in filter_dict.items():
                    if isinstance(value, str):
                        filter_parts.append(f'{key} = "{value}"')
                    else:
                        filter_parts.append(f"{key} = {value}")
                if filter_parts:
                    query = query.where(" AND ".join(filter_parts))

            results = query.to_pandas()

            memories = []
            for _, row in results.iterrows():
                memories.append({
                    "id": row.get("id"),
                    "content": row.get("text"),
                    "metadata": {k: v for k, v in row.items() if k not in ("id", "text", "vector", "_distance")},
                    "score": 1 - row.get("_distance", 0),
                })

            return memories

        except Exception as e:
            logger.error(f"LanceDB search failed: {e}")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from LanceDB."""
        if self.table is None:
            return False

        try:
            self.table.delete(f'id = "{memory_id}"')
            return True
        except Exception:
            return False

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from LanceDB."""
        if self.table is None:
            return None

        try:
            df = self.table.to_pandas()
            row = df[df["id"] == memory_id]
            if not row.empty:
                row = row.iloc[0]
                return {
                    "id": row.get("id"),
                    "content": row.get("text"),
                    "metadata": {k: v for k, v in row.items() if k not in ("id", "text", "vector")},
                    "embedding": row.get("vector"),
                }
        except Exception:
            pass
        return None


class DualWriteAdapter(VectorDatabaseAdapter):
    """
    Dual-write adapter for gradual migration.

    Writes to both ChromaDB (primary) and LanceDB (secondary) simultaneously.
    Reads from primary by default but can be configured to read from secondary.

    Example usage:
        chromadb_adapter = ChromaDBAdapter(client, "canvas_memories")
        lancedb_adapter = LanceDBAdapter(connection, "canvas_memories")
        dual_adapter = DualWriteAdapter(chromadb_adapter, lancedb_adapter)

        # All writes go to both databases
        dual_adapter.store_memory("id1", "content", embedding, metadata)
    """

    def __init__(
        self,
        primary: VectorDatabaseAdapter,
        secondary: VectorDatabaseAdapter,
        read_from_secondary: bool = False,
        retry_count: int = 3,
        retry_delay_ms: int = 100
    ):
        """
        Initialize dual-write adapter.

        Args:
            primary: Primary database adapter (ChromaDB)
            secondary: Secondary database adapter (LanceDB)
            read_from_secondary: If True, reads from secondary instead of primary
            retry_count: Number of retry attempts on failure
            retry_delay_ms: Delay between retries in milliseconds
        """
        self.primary = primary
        self.secondary = secondary
        self.read_from_secondary = read_from_secondary
        self.retry_count = retry_count
        self.retry_delay_ms = retry_delay_ms
        self.stats = DualWriteStats()
        self._latencies: List[float] = []

    def store_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in both databases."""
        start_time = time.time()
        errors: List[str] = []

        primary_success = False
        secondary_success = False

        # Write to primary with retry
        for attempt in range(self.retry_count):
            try:
                self.primary.store_memory(memory_id, content, embedding, metadata)
                primary_success = True
                break
            except Exception as e:
                errors.append(f"Primary write attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay_ms / 1000)

        # Write to secondary with retry
        for attempt in range(self.retry_count):
            try:
                self.secondary.store_memory(memory_id, content, embedding, metadata)
                secondary_success = True
                break
            except Exception as e:
                errors.append(f"Secondary write attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay_ms / 1000)

        # Update statistics
        latency_ms = (time.time() - start_time) * 1000
        self._update_stats(primary_success, secondary_success, latency_ms)

        if errors:
            logger.warning(f"Dual write errors for {memory_id}: {errors}")

        if not primary_success:
            raise Exception(f"Primary write failed for {memory_id}")

        return memory_id

    def search_memory(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search from configured read source."""
        source = self.secondary if self.read_from_secondary else self.primary
        return source.search_memory(query_embedding, limit, filter_dict)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete from both databases."""
        primary_success = self.primary.delete_memory(memory_id)
        secondary_success = self.secondary.delete_memory(memory_id)
        return primary_success and secondary_success

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get from configured read source."""
        source = self.secondary if self.read_from_secondary else self.primary
        return source.get_memory(memory_id)

    def _update_stats(
        self,
        primary_success: bool,
        secondary_success: bool,
        latency_ms: float
    ) -> None:
        """Update write statistics."""
        self.stats.total_writes += 1
        self._latencies.append(latency_ms)

        if primary_success and secondary_success:
            self.stats.successful_writes += 1
        else:
            self.stats.failed_writes += 1

        if not primary_success:
            self.stats.primary_failures += 1
        if not secondary_success:
            self.stats.secondary_failures += 1

        self.stats.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        self.stats.last_write_time = datetime.now()

    def get_stats(self) -> DualWriteStats:
        """Get current dual write statistics."""
        return self.stats

    def switch_to_secondary(self) -> None:
        """Switch reads to secondary database."""
        self.read_from_secondary = True
        logger.info("Switched reads to secondary (LanceDB)")

    def switch_to_primary(self) -> None:
        """Switch reads back to primary database."""
        self.read_from_secondary = False
        logger.info("Switched reads to primary (ChromaDB)")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of dual write system."""
        stats = self.stats
        return {
            "healthy": stats.failed_writes == 0 or (stats.failed_writes / max(stats.total_writes, 1)) < 0.01,
            "total_writes": stats.total_writes,
            "failure_rate": stats.failed_writes / max(stats.total_writes, 1),
            "avg_latency_ms": stats.avg_latency_ms,
            "read_source": "secondary" if self.read_from_secondary else "primary",
        }
