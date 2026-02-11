"""
Story 35.12 AC 35.12.3: Multimodal test fixtures.

Provides minimal test files (PNG, PDF) and factory functions for
real persistence integration tests.
"""

import struct
import zlib
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def make_minimal_png(width: int = 1, height: int = 1) -> bytes:
    """Create a minimal valid PNG image in memory.

    Returns a valid 1x1 red pixel PNG (< 100 bytes).
    No Pillow dependency required.
    """

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"

    # IHDR: width, height, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # IDAT: single row, filter byte 0, then RGB (255,0,0) per pixel
    raw_row = b"\x00" + b"\xff\x00\x00" * width
    raw = raw_row * height
    compressed = zlib.compress(raw)
    idat = _chunk(b"IDAT", compressed)

    # IEND
    iend = _chunk(b"IEND", b"")

    return sig + ihdr + idat + iend


def make_minimal_pdf() -> bytes:
    """Create a minimal valid 1-page PDF in memory.

    Returns a valid PDF (< 500 bytes) with a single blank page.
    No external dependency required.
    """
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n190\n%%EOF\n"
    )


def get_test_png_path() -> Path:
    """Get path to pre-generated test PNG, creating it if needed."""
    path = FIXTURES_DIR / "test_1x1.png"
    if not path.exists():
        path.write_bytes(make_minimal_png())
    return path


def get_test_pdf_path() -> Path:
    """Get path to pre-generated test PDF, creating it if needed."""
    path = FIXTURES_DIR / "test_1page.pdf"
    if not path.exists():
        path.write_bytes(make_minimal_pdf())
    return path
