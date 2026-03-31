# Story 7.3: Prompt 版本管理与回归测试 — PromptRegistry
# [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md]
"""
PromptRegistry — Singleton service for loading, caching, and managing
versioned LLM prompt templates from the backend/app/prompts/ directory.

Responsibilities:
  - Scan prompts/ directory and load all {name}_v{N}.md files
  - Parse file-header metadata (引用方, 版本, 创建日期)
  - Provide get(name, version) API — default returns latest version
  - Compute SHA-256 content hashes for change detection
  - Support version listing and rollback via version parameter

Usage:
    registry = PromptRegistry.get_instance()
    registry.load_all()
    content = registry.get("autoscore")            # latest
    content = registry.get("autoscore", version=1)  # specific version
"""

import hashlib
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from app.core.exceptions import PromptLoadError

logger = logging.getLogger(__name__)

# Default prompts directory — relative to this file's location
_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Regex for file naming convention: {name}_v{version}.md
_FILENAME_PATTERN = re.compile(r"^(.+)_v(\d+)\.md$")

# Regex patterns for metadata header lines (HTML comments)
_META_SERVICE_REF = re.compile(r"<!--\s*引用方:\s*(.+?)\s*-->")
_META_VERSION_DATE = re.compile(
    r"<!--\s*版本:\s*v(\d+)\s*\|\s*创建:\s*(\d{4}-\d{2}-\d{2})\s*-->"
)


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable representation of a loaded prompt template."""

    name: str  # e.g., "autoscore"
    version: int  # e.g., 1
    content: str  # Full template content (including header)
    content_hash: str  # SHA-256 hex digest
    service_ref: str  # 引用方 service path
    created_at: str  # Creation date string (YYYY-MM-DD)
    file_path: Path  # Absolute path to the .md file


class PromptRegistry:
    """
    Singleton registry that loads and manages versioned prompt templates.

    Thread-safe. Call load_all() once during application startup,
    then use get() / list_versions() throughout the application lifetime.
    """

    _instance: Optional["PromptRegistry"] = None
    _lock = threading.Lock()

    def __init__(self, prompts_dir: Optional[Path] = None):
        self._prompts_dir = prompts_dir or _DEFAULT_PROMPTS_DIR
        # _registry[name][version] = PromptTemplate
        self._registry: Dict[str, Dict[int, PromptTemplate]] = {}
        self._loaded = False
        # Optional per-name active version overrides (for rollback)
        self._active_versions: Dict[str, int] = {}

    # ─── Singleton ────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls, prompts_dir: Optional[Path] = None) -> "PromptRegistry":
        """Return the singleton PromptRegistry, creating it if needed."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(prompts_dir=prompts_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing only)."""
        with cls._lock:
            cls._instance = None

    # ─── Loading ──────────────────────────────────────────────────────────

    def load_all(self) -> int:
        """
        Scan the prompts directory and load all versioned .md templates.

        Returns:
            Number of templates successfully loaded.

        Raises:
            PromptLoadError: If prompts directory does not exist.
        """
        if not self._prompts_dir.exists():
            raise PromptLoadError(
                message=f"Prompts directory does not exist: {self._prompts_dir}",
                file_path=str(self._prompts_dir),
            )

        self._registry.clear()
        loaded_count = 0

        for md_file in sorted(self._prompts_dir.glob("*_v*.md")):
            match = _FILENAME_PATTERN.match(md_file.name)
            if not match:
                logger.warning(
                    "[PromptRegistry] Skipping file with unexpected name: %s",
                    md_file.name,
                )
                continue

            name = match.group(1)
            version = int(match.group(2))

            try:
                template = self._load_single(md_file, name, version)
                self._registry.setdefault(name, {})[version] = template
                loaded_count += 1
                logger.info(
                    "[PromptRegistry] Loaded %s v%d (hash=%s)",
                    name,
                    version,
                    template.content_hash[:12],
                )
            except PromptLoadError:
                raise
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                raise PromptLoadError(
                    message=f"Failed to load template: {exc}",
                    prompt_name=name,
                    file_path=str(md_file),
                ) from exc

        self._loaded = True
        logger.info(
            "[PromptRegistry] Loaded %d templates across %d prompt names",
            loaded_count,
            len(self._registry),
        )
        return loaded_count

    def _load_single(self, file_path: Path, name: str, version: int) -> PromptTemplate:
        """Load and parse a single prompt template file."""
        raw = file_path.read_text(encoding="utf-8")
        if not raw.strip():
            raise PromptLoadError(
                message="File is empty",
                prompt_name=name,
                file_path=str(file_path),
            )

        service_ref, created_at = self._parse_metadata(raw, name, file_path)
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return PromptTemplate(
            name=name,
            version=version,
            content=raw,
            content_hash=content_hash,
            service_ref=service_ref,
            created_at=created_at,
            file_path=file_path.resolve(),
        )

    @staticmethod
    def _parse_metadata(content: str, name: str, file_path: Path) -> tuple:
        """
        Extract metadata from the HTML-comment header.

        Returns:
            (service_ref, created_at) tuple.

        Raises:
            PromptLoadError: If required metadata fields are missing.
        """
        service_match = _META_SERVICE_REF.search(content)
        version_date_match = _META_VERSION_DATE.search(content)

        if not service_match:
            raise PromptLoadError(
                message="Missing metadata: '引用方' comment not found",
                prompt_name=name,
                file_path=str(file_path),
            )
        if not version_date_match:
            raise PromptLoadError(
                message="Missing metadata: '版本/创建' comment not found",
                prompt_name=name,
                file_path=str(file_path),
            )

        service_ref = service_match.group(1).strip()
        created_at = version_date_match.group(2).strip()
        return service_ref, created_at

    # ─── Query API ────────────────────────────────────────────────────────

    def get(self, name: str, version: Optional[int] = None) -> str:
        """
        Return the prompt template content for the given name and version.

        Args:
            name: Template name (e.g., "autoscore").
            version: Specific version number. If None, returns the
                     active version (set via set_active_version) or
                     the latest available version.

        Returns:
            The full template content string.

        Raises:
            PromptLoadError: If name or version not found.
        """
        versions = self._registry.get(name)
        if not versions:
            raise PromptLoadError(
                message=f"No template found with name '{name}'",
                prompt_name=name,
            )

        if version is None:
            # Use active version override if set, otherwise latest
            version = self._active_versions.get(name, max(versions.keys()))

        template = versions.get(version)
        if template is None:
            available = sorted(versions.keys())
            raise PromptLoadError(
                message=(
                    f"Version v{version} not found. Available versions: {available}"
                ),
                prompt_name=name,
            )

        return template.content

    def get_template(self, name: str, version: Optional[int] = None) -> PromptTemplate:
        """
        Return the full PromptTemplate dataclass for the given name/version.

        Same resolution logic as get(), but returns the PromptTemplate
        instead of just the content string.
        """
        versions = self._registry.get(name)
        if not versions:
            raise PromptLoadError(
                message=f"No template found with name '{name}'",
                prompt_name=name,
            )

        if version is None:
            version = self._active_versions.get(name, max(versions.keys()))

        template = versions.get(version)
        if template is None:
            available = sorted(versions.keys())
            raise PromptLoadError(
                message=(
                    f"Version v{version} not found. Available versions: {available}"
                ),
                prompt_name=name,
            )
        return template

    def get_metadata(self, name: str, version: Optional[int] = None) -> Dict:
        """Return metadata dict for a prompt template."""
        tpl = self.get_template(name, version)
        return {
            "name": tpl.name,
            "version": tpl.version,
            "service_ref": tpl.service_ref,
            "created_at": tpl.created_at,
            "content_hash": tpl.content_hash,
            "file_path": str(tpl.file_path),
        }

    def get_hash(self, name: str, version: Optional[int] = None) -> str:
        """Return the SHA-256 content hash for a prompt template."""
        return self.get_template(name, version).content_hash

    def list_versions(self, name: str) -> List[int]:
        """
        Return sorted list of available version numbers for a template name.

        Raises:
            PromptLoadError: If name not found.
        """
        versions = self._registry.get(name)
        if not versions:
            raise PromptLoadError(
                message=f"No template found with name '{name}'",
                prompt_name=name,
            )
        return sorted(versions.keys())

    def list_names(self) -> List[str]:
        """Return sorted list of all registered prompt template names."""
        return sorted(self._registry.keys())

    @property
    def is_loaded(self) -> bool:
        """Whether load_all() has been called successfully."""
        return self._loaded

    # ─── Version Rollback ─────────────────────────────────────────────────

    def set_active_version(self, name: str, version: int) -> None:
        """
        Pin a specific version as the active version for a template name.

        This enables rollback: if v2 causes quality regression, pin v1.
        Call with version=None to revert to "latest" behavior.

        Raises:
            PromptLoadError: If name or version not found.
        """
        versions = self._registry.get(name)
        if not versions:
            raise PromptLoadError(
                message=f"No template found with name '{name}'",
                prompt_name=name,
            )
        if version not in versions:
            available = sorted(versions.keys())
            raise PromptLoadError(
                message=(
                    f"Cannot set active version to v{version}. Available: {available}"
                ),
                prompt_name=name,
            )
        self._active_versions[name] = version
        logger.info(
            "[PromptRegistry] Active version for '%s' set to v%d",
            name,
            version,
        )

    def clear_active_version(self, name: str) -> None:
        """Remove the active version pin, reverting to 'latest' behavior."""
        self._active_versions.pop(name, None)
        logger.info(
            "[PromptRegistry] Active version pin cleared for '%s' (using latest)",
            name,
        )

    def get_active_version(self, name: str) -> Optional[int]:
        """Return the pinned active version, or None if using latest."""
        return self._active_versions.get(name)


# ─── Module-level convenience ─────────────────────────────────────────────


def get_prompt_registry(prompts_dir: Optional[Path] = None) -> PromptRegistry:
    """Get the singleton PromptRegistry instance."""
    return PromptRegistry.get_instance(prompts_dir=prompts_dir)
