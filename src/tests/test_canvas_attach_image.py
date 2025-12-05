"""
Tests for CanvasJSONOperator attach_image and detach_image methods.

Verified from Story 6.1:
- AC 6.1.1: Canvas节点可附加PNG/JPG/GIF/SVG图片
- AC 6.1.2: 图片显示为缩略图
- AC 6.1.3: 图片元数据存储
"""

import pytest
from copy import deepcopy

# Import the module under test
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from canvas_utils import CanvasJSONOperator


class TestAttachImage:
    """Tests for CanvasJSONOperator.attach_image method."""

    @pytest.fixture
    def sample_canvas_data(self):
        """Create sample canvas data for testing."""
        return {
            "nodes": [
                {
                    "id": "text-abc123",
                    "type": "text",
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "height": 100,
                    "text": "示例节点"
                },
                {
                    "id": "text-def456",
                    "type": "text",
                    "x": 300,
                    "y": 0,
                    "width": 200,
                    "height": 100,
                    "text": "第二个节点"
                }
            ],
            "edges": []
        }

    def test_attach_png_image(self, sample_canvas_data):
        """Test attaching PNG image to node (AC 6.1.1)."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "images/diagram.png"
        )

        assert attachment is not None
        assert attachment["type"] == "image"
        assert attachment["path"] == "images/diagram.png"
        assert attachment["format"] == "png"
        assert "id" in attachment
        assert attachment["id"].startswith("img-")

        # Verify node has attachments
        node = sample_canvas_data["nodes"][0]
        assert "attachments" in node
        assert len(node["attachments"]) == 1
        assert node["attachments"][0]["path"] == "images/diagram.png"

    def test_attach_jpg_image(self, sample_canvas_data):
        """Test attaching JPG image (AC 6.1.1)."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "photo.jpg"
        )

        assert attachment["format"] == "jpg"
        assert attachment["path"] == "photo.jpg"

    def test_attach_jpeg_image(self, sample_canvas_data):
        """Test attaching JPEG image (AC 6.1.1)."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "photo.jpeg"
        )

        assert attachment["format"] == "jpeg"

    def test_attach_gif_image(self, sample_canvas_data):
        """Test attaching GIF image (AC 6.1.1)."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "animation.gif"
        )

        assert attachment["format"] == "gif"

    def test_attach_svg_image(self, sample_canvas_data):
        """Test attaching SVG image (AC 6.1.1)."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "icon.svg"
        )

        assert attachment["format"] == "svg"

    def test_attach_image_with_thumbnail(self, sample_canvas_data):
        """Test attaching image with thumbnail (AC 6.1.2)."""
        thumbnail_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "diagram.png",
            thumbnail_base64=thumbnail_b64
        )

        assert "thumbnail" in attachment
        assert attachment["thumbnail"] == thumbnail_b64

    def test_attach_image_with_metadata(self, sample_canvas_data):
        """Test attaching image with metadata (AC 6.1.3)."""
        metadata = {
            "width": 200,
            "height": 150,
            "format": "png",
            "file_size": 1024,
            "mime_type": "image/png"
        }

        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "diagram.png",
            metadata=metadata
        )

        assert "metadata" in attachment
        assert attachment["metadata"]["width"] == 200
        assert attachment["metadata"]["height"] == 150
        assert attachment["metadata"]["file_size"] == 1024

    def test_attach_multiple_images(self, sample_canvas_data):
        """Test attaching multiple images to same node."""
        CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image1.png"
        )
        CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image2.jpg"
        )
        CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image3.gif"
        )

        node = sample_canvas_data["nodes"][0]
        assert len(node["attachments"]) == 3

    def test_attach_image_to_different_nodes(self, sample_canvas_data):
        """Test attaching images to different nodes."""
        CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image1.png"
        )
        CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-def456",
            "image2.png"
        )

        assert len(sample_canvas_data["nodes"][0]["attachments"]) == 1
        assert len(sample_canvas_data["nodes"][1]["attachments"]) == 1

    def test_attach_image_nonexistent_node(self, sample_canvas_data):
        """Test attaching image to non-existent node raises KeyError."""
        with pytest.raises(KeyError, match="节点不存在"):
            CanvasJSONOperator.attach_image(
                sample_canvas_data,
                "nonexistent-node",
                "image.png"
            )

    def test_attach_unsupported_format(self, sample_canvas_data):
        """Test attaching unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="不支持的图片格式"):
            CanvasJSONOperator.attach_image(
                sample_canvas_data,
                "text-abc123",
                "document.pdf"
            )

    def test_attach_unsupported_bmp(self, sample_canvas_data):
        """Test BMP format is not supported."""
        with pytest.raises(ValueError, match="不支持的图片格式"):
            CanvasJSONOperator.attach_image(
                sample_canvas_data,
                "text-abc123",
                "image.bmp"
            )

    def test_attach_unsupported_webp(self, sample_canvas_data):
        """Test WebP format is not supported."""
        with pytest.raises(ValueError, match="不支持的图片格式"):
            CanvasJSONOperator.attach_image(
                sample_canvas_data,
                "text-abc123",
                "image.webp"
            )

    def test_attach_image_case_insensitive_extension(self, sample_canvas_data):
        """Test extension matching is case insensitive."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "IMAGE.PNG"
        )

        assert attachment["format"] == "png"

    def test_attach_image_has_created_at(self, sample_canvas_data):
        """Test attachment has created_at timestamp."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image.png"
        )

        assert "created_at" in attachment
        # Verify it's a valid ISO format timestamp
        from datetime import datetime
        datetime.fromisoformat(attachment["created_at"])

    def test_attach_image_unique_ids(self, sample_canvas_data):
        """Test each attachment gets unique ID."""
        att1 = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image1.png"
        )
        att2 = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "image2.png"
        )

        assert att1["id"] != att2["id"]

    def test_attach_image_with_path_containing_spaces(self, sample_canvas_data):
        """Test attaching image with spaces in path."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "my images/test file.png"
        )

        assert attachment["path"] == "my images/test file.png"

    def test_attach_image_with_absolute_path(self, sample_canvas_data):
        """Test attaching image with absolute path."""
        attachment = CanvasJSONOperator.attach_image(
            sample_canvas_data,
            "text-abc123",
            "/home/user/images/photo.jpg"
        )

        assert attachment["path"] == "/home/user/images/photo.jpg"


class TestDetachImage:
    """Tests for CanvasJSONOperator.detach_image method."""

    @pytest.fixture
    def canvas_with_attachments(self):
        """Create canvas data with attachments."""
        return {
            "nodes": [
                {
                    "id": "text-abc123",
                    "type": "text",
                    "x": 0,
                    "y": 0,
                    "text": "节点1",
                    "attachments": [
                        {"id": "img-11111111", "path": "image1.png", "type": "image"},
                        {"id": "img-22222222", "path": "image2.jpg", "type": "image"},
                        {"id": "img-33333333", "path": "image3.gif", "type": "image"}
                    ]
                },
                {
                    "id": "text-def456",
                    "type": "text",
                    "x": 300,
                    "y": 0,
                    "text": "节点2"
                }
            ],
            "edges": []
        }

    def test_detach_by_attachment_id(self, canvas_with_attachments):
        """Test removing attachment by ID."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            attachment_id="img-22222222"
        )

        assert removed == 1
        node = canvas_with_attachments["nodes"][0]
        assert len(node["attachments"]) == 2
        # Verify img-22222222 was removed
        ids = [att["id"] for att in node["attachments"]]
        assert "img-22222222" not in ids
        assert "img-11111111" in ids
        assert "img-33333333" in ids

    def test_detach_by_image_path(self, canvas_with_attachments):
        """Test removing attachment by path."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            image_path="image1.png"
        )

        assert removed == 1
        node = canvas_with_attachments["nodes"][0]
        assert len(node["attachments"]) == 2
        paths = [att["path"] for att in node["attachments"]]
        assert "image1.png" not in paths

    def test_detach_all_attachments(self, canvas_with_attachments):
        """Test removing all attachments when no ID/path specified."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123"
        )

        assert removed == 3
        node = canvas_with_attachments["nodes"][0]
        assert "attachments" not in node

    def test_detach_removes_empty_attachments_array(self, canvas_with_attachments):
        """Test that empty attachments array is removed from node."""
        # Remove all attachments one by one
        CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            attachment_id="img-11111111"
        )
        CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            attachment_id="img-22222222"
        )
        CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            attachment_id="img-33333333"
        )

        node = canvas_with_attachments["nodes"][0]
        assert "attachments" not in node

    def test_detach_from_nonexistent_node(self, canvas_with_attachments):
        """Test detaching from non-existent node raises KeyError."""
        with pytest.raises(KeyError, match="节点不存在"):
            CanvasJSONOperator.detach_image(
                canvas_with_attachments,
                "nonexistent-node"
            )

    def test_detach_from_node_without_attachments(self, canvas_with_attachments):
        """Test detaching from node without attachments returns 0."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-def456"  # This node has no attachments
        )

        assert removed == 0

    def test_detach_nonexistent_attachment_id(self, canvas_with_attachments):
        """Test detaching non-existent attachment ID."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            attachment_id="img-nonexistent"
        )

        assert removed == 0
        node = canvas_with_attachments["nodes"][0]
        assert len(node["attachments"]) == 3  # Unchanged

    def test_detach_nonexistent_image_path(self, canvas_with_attachments):
        """Test detaching non-existent image path."""
        removed = CanvasJSONOperator.detach_image(
            canvas_with_attachments,
            "text-abc123",
            image_path="nonexistent.png"
        )

        assert removed == 0
        node = canvas_with_attachments["nodes"][0]
        assert len(node["attachments"]) == 3  # Unchanged


class TestAttachDetachIntegration:
    """Integration tests for attach and detach workflow."""

    @pytest.fixture
    def empty_canvas(self):
        """Create empty canvas data."""
        return {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "x": 0,
                    "y": 0,
                    "text": "Test"
                }
            ],
            "edges": []
        }

    def test_attach_then_detach_by_id(self, empty_canvas):
        """Test complete attach-detach workflow by ID."""
        # Attach
        attachment = CanvasJSONOperator.attach_image(
            empty_canvas,
            "node-1",
            "test.png",
            thumbnail_base64="base64data",
            metadata={"width": 100, "height": 100}
        )

        # Verify attached
        node = empty_canvas["nodes"][0]
        assert len(node["attachments"]) == 1

        # Detach by ID
        removed = CanvasJSONOperator.detach_image(
            empty_canvas,
            "node-1",
            attachment_id=attachment["id"]
        )

        # Verify detached
        assert removed == 1
        assert "attachments" not in node

    def test_attach_then_detach_by_path(self, empty_canvas):
        """Test complete attach-detach workflow by path."""
        # Attach
        CanvasJSONOperator.attach_image(
            empty_canvas,
            "node-1",
            "my_image.png"
        )

        # Detach by path
        removed = CanvasJSONOperator.detach_image(
            empty_canvas,
            "node-1",
            image_path="my_image.png"
        )

        assert removed == 1
        assert "attachments" not in empty_canvas["nodes"][0]

    def test_multiple_attach_partial_detach(self, empty_canvas):
        """Test attaching multiple then detaching some."""
        # Attach 3 images
        CanvasJSONOperator.attach_image(empty_canvas, "node-1", "a.png")
        att2 = CanvasJSONOperator.attach_image(empty_canvas, "node-1", "b.jpg")
        CanvasJSONOperator.attach_image(empty_canvas, "node-1", "c.gif")

        assert len(empty_canvas["nodes"][0]["attachments"]) == 3

        # Detach one
        CanvasJSONOperator.detach_image(
            empty_canvas,
            "node-1",
            attachment_id=att2["id"]
        )

        assert len(empty_canvas["nodes"][0]["attachments"]) == 2

    def test_data_integrity_after_operations(self, empty_canvas):
        """Test canvas data integrity after multiple operations."""
        original_node_count = len(empty_canvas["nodes"])
        original_edge_count = len(empty_canvas["edges"])

        # Perform various attach/detach operations
        CanvasJSONOperator.attach_image(empty_canvas, "node-1", "img1.png")
        CanvasJSONOperator.attach_image(empty_canvas, "node-1", "img2.png")
        CanvasJSONOperator.detach_image(empty_canvas, "node-1", image_path="img1.png")
        CanvasJSONOperator.attach_image(empty_canvas, "node-1", "img3.png")
        CanvasJSONOperator.detach_image(empty_canvas, "node-1")  # Remove all

        # Verify data integrity
        assert len(empty_canvas["nodes"]) == original_node_count
        assert len(empty_canvas["edges"]) == original_edge_count
        assert empty_canvas["nodes"][0]["id"] == "node-1"
        assert empty_canvas["nodes"][0]["text"] == "Test"
