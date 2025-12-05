"""
Multimodal content processors.

This module provides processors for handling different types of media content:
- ImageProcessor: PNG, JPG, GIF, SVG processing with thumbnails

Verified from Story 6.1 (AC 6.1.1): Canvas节点可附加PNG/JPG/GIF/SVG图片
"""

from .image_processor import ImageProcessor, ImageMetadata

__all__ = ["ImageProcessor", "ImageMetadata"]
