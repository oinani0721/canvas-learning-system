# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Canvas Service - Business logic for Canvas operations.

This service provides async methods for Canvas file operations,
wrapping the core canvas_utils.py functionality with async support.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
"""
import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List

from app.core.exceptions import (
    CanvasNotFoundException,
    NodeNotFoundException,
    ValidationError,
)

logger = logging.getLogger(__name__)


class CanvasService:
    """
    Canvas business logic service.

    Provides async methods for Canvas CRUD operations and node/edge management.
    Uses asyncio.to_thread for I/O operations to maintain async compatibility.

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """

    def __init__(self, canvas_base_path: str = None):
        """
        Initialize CanvasService.

        Args:
            canvas_base_path: Base path for Canvas files (positional or keyword)

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self.canvas_base_path = canvas_base_path or "./"
        self._initialized = True
        logger.debug(f"CanvasService initialized with base_path: {canvas_base_path}")

    def _validate_canvas_name(self, canvas_name: str) -> None:
        """
        Validate canvas name to prevent path traversal attacks.
        Allows subdirectory paths (/) but blocks dangerous patterns.

        Args:
            canvas_name: Canvas name to validate (can include subdirectories like "笔记库/子目录/test")

        Raises:
            ValidationError: If canvas name contains dangerous path traversal patterns
        """
        # Block absolute paths
        if canvas_name.startswith('/'):
            raise ValidationError(f"Absolute path not allowed: {canvas_name}")

        # Block dangerous patterns
        dangerous_patterns = ['..', '\\', '\0', '//', '/./']
        for pattern in dangerous_patterns:
            if pattern in canvas_name:
                raise ValidationError(f"Invalid canvas path: {canvas_name}")

    def _get_canvas_path(self, canvas_name: str) -> Path:
        """Get full path to canvas file.

        Normalizes canvas_name by removing common extensions (.canvas, .md)
        to prevent path construction errors like "file.md.canvas".

        [Source: Story 12.A.1 - AC 3: CanvasService 路径处理支持多种输入格式]
        """
        self._validate_canvas_name(canvas_name)
        # ✅ FIX Story 12.A.1: Normalize canvas_name by removing .canvas OR .md extension
        # This handles:
        #   - "Canvas/Math53/Lecture5" (standard format)
        #   - "Canvas/Math53/Lecture5.canvas" (with .canvas extension)
        #   - "KP13-线性逼近与微分.md" (incorrect .md extension from Obsidian)
        normalized_name = canvas_name.removesuffix('.canvas').removesuffix('.md')
        logger.debug(f"Canvas path normalized: '{canvas_name}' -> '{normalized_name}'")
        return Path(self.canvas_base_path) / f"{normalized_name}.canvas"

    async def read_canvas(self, canvas_name: str) -> Dict[str, Any]:
        """
        Read a Canvas file asynchronously.

        Args:
            canvas_name: Canvas file name (without .canvas extension)

        Returns:
            Canvas data dict

        Raises:
            CanvasNotFoundException: If canvas file doesn't exist
            ValidationError: If canvas name contains path traversal

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        canvas_path = self._get_canvas_path(canvas_name)
        logger.debug(f"Reading canvas: {canvas_path}")

        def _read_file() -> Dict[str, Any]:
            if not canvas_path.exists():
                raise CanvasNotFoundException(f"Canvas not found: {canvas_name}")
            with open(canvas_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        data = await asyncio.to_thread(_read_file)
        data['name'] = canvas_name
        return data

    async def write_canvas(self, canvas_name: str, canvas_data: Dict[str, Any]) -> bool:
        """
        Write canvas data to file.

        Args:
            canvas_name: Canvas file name (without .canvas extension)
            canvas_data: Canvas data to write

        Returns:
            True if successful

        Raises:
            ValidationError: If canvas name contains path traversal
        """
        canvas_path = self._get_canvas_path(canvas_name)
        logger.debug(f"Writing canvas: {canvas_path}")

        def _write_file() -> bool:
            canvas_path.parent.mkdir(parents=True, exist_ok=True)
            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, indent=2, ensure_ascii=False)
            return True

        return await asyncio.to_thread(_write_file)

    async def canvas_exists(self, canvas_name: str) -> bool:
        """
        Check if a canvas file exists.

        Args:
            canvas_name: Canvas file name

        Returns:
            True if canvas exists
        """
        try:
            canvas_path = self._get_canvas_path(canvas_name)
            return await asyncio.to_thread(canvas_path.exists)
        except ValidationError:
            return False

    async def list_canvases(self) -> List[str]:
        """
        List all available Canvas files.

        Returns:
            List of canvas names

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Listing canvases in: {self.canvas_base_path}")

        def _list_files() -> List[str]:
            base_path = Path(self.canvas_base_path)
            if not base_path.exists():
                return []
            return [f.stem for f in base_path.glob("*.canvas")]

        return await asyncio.to_thread(_list_files)

    async def add_node(
        self,
        canvas_name: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a node to a Canvas.

        Args:
            canvas_name: Target canvas name
            node_data: Node data to add

        Returns:
            Added node data with generated ID

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Adding node to {canvas_name}: {node_data}")

        canvas_data = await self.read_canvas(canvas_name)

        # Generate node ID if not provided
        node_id = node_data.get("id") or str(uuid.uuid4())[:8]
        new_node = {"id": node_id, **node_data}

        # Add default dimensions if not provided
        new_node.setdefault("width", 250)
        new_node.setdefault("height", 60)

        canvas_data["nodes"].append(new_node)
        await self.write_canvas(canvas_name, canvas_data)

        return new_node

    async def update_node(
        self,
        canvas_name: str,
        node_id: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a node in a Canvas.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to update
            node_data: New node data (partial update)

        Returns:
            Updated node data

        Raises:
            NodeNotFoundException: If node doesn't exist

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Updating node {node_id} in {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        # Find and update node
        for i, node in enumerate(canvas_data["nodes"]):
            if node.get("id") == node_id:
                # Merge updates, preserving existing data
                updated_node = {**node, **node_data, "id": node_id}
                canvas_data["nodes"][i] = updated_node
                await self.write_canvas(canvas_name, canvas_data)
                return updated_node

        raise NodeNotFoundException(f"Node not found: {node_id}")

    async def delete_node(self, canvas_name: str, node_id: str) -> bool:
        """
        Delete a node from a Canvas.

        Args:
            canvas_name: Target canvas name
            node_id: ID of node to delete

        Returns:
            True if deleted, False if not found

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Deleting node {node_id} from {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        # Find and remove node
        original_count = len(canvas_data["nodes"])
        canvas_data["nodes"] = [n for n in canvas_data["nodes"] if n.get("id") != node_id]

        if len(canvas_data["nodes"]) == original_count:
            return False

        # Also remove related edges
        canvas_data["edges"] = [
            e for e in canvas_data.get("edges", [])
            if e.get("fromNode") != node_id and e.get("toNode") != node_id
        ]

        await self.write_canvas(canvas_name, canvas_data)
        return True

    async def get_nodes_by_color(
        self,
        canvas_name: str,
        color: str
    ) -> List[Dict[str, Any]]:
        """
        Get all nodes with a specific color.

        Args:
            canvas_name: Target canvas name
            color: Color code to filter by (e.g., "1" for red, "3" for green)

        Returns:
            List of matching nodes
        """
        canvas_data = await self.read_canvas(canvas_name)
        return [
            node for node in canvas_data.get("nodes", [])
            if node.get("color") == color
        ]

    async def add_edge(
        self,
        canvas_name: str,
        edge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an edge between two nodes.

        Args:
            canvas_name: Target canvas name
            edge_data: Edge data with fromNode and toNode

        Returns:
            Added edge data with generated ID
        """
        logger.debug(f"Adding edge to {canvas_name}: {edge_data}")

        canvas_data = await self.read_canvas(canvas_name)

        # Generate edge ID if not provided
        edge_id = edge_data.get("id") or str(uuid.uuid4())[:8]
        new_edge = {"id": edge_id, **edge_data}

        if "edges" not in canvas_data:
            canvas_data["edges"] = []
        canvas_data["edges"].append(new_edge)

        await self.write_canvas(canvas_name, canvas_data)
        return new_edge

    async def delete_edge(self, canvas_name: str, edge_id: str) -> bool:
        """
        Delete an edge from a Canvas.

        Args:
            canvas_name: Target canvas name
            edge_id: ID of edge to delete

        Returns:
            True if deleted
        """
        logger.debug(f"Deleting edge {edge_id} from {canvas_name}")

        canvas_data = await self.read_canvas(canvas_name)

        original_count = len(canvas_data.get("edges", []))
        canvas_data["edges"] = [
            e for e in canvas_data.get("edges", [])
            if e.get("id") != edge_id
        ]

        if len(canvas_data.get("edges", [])) == original_count:
            return False

        await self.write_canvas(canvas_name, canvas_data)
        return True

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Called by dependency injection when using yield syntax.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        logger.debug("CanvasService cleanup completed")
