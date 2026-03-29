# Story 3.5: /命令技能集成 — SkillRegistry Service
# [Source: _bmad-output/implementation-artifacts/3-5-skill-command-integration.md]
"""
SkillRegistry — Service for scanning .claude/commands/ directory
and exposing skill metadata to the frontend via API.

Responsibilities:
  - Scan .claude/commands/ directory for all .md skill template files
  - Parse YAML frontmatter (name, description, icon) if present
  - Fallback: extract name from first # heading, description from first paragraph
  - Provide list_skills() API returning structured skill metadata
  - Provide get_skill_content() API returning full template content for execution
  - Support dynamic refresh (rescan on demand, no restart required)

Usage:
    registry = SkillRegistry.get_instance()
    skills = registry.list_skills()           # All skills with metadata
    content = registry.get_skill_content("basic-decompose")  # Full template
"""

import asyncio
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Default commands directory — project root / .claude / commands
_CONFIG_DIR = Path(__file__).parent.parent  # backend/app/
_BACKEND_DIR = _CONFIG_DIR.parent  # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent  # project root
_DEFAULT_COMMANDS_DIR = _PROJECT_ROOT / ".claude" / "commands"

# Regex for YAML frontmatter extraction
_FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n",
    re.DOTALL,
)

# Regex for extracting key-value pairs from YAML (simple flat YAML only)
_YAML_KV_PATTERN = re.compile(r"^(\w[\w-]*)\s*:\s*(.+)$", re.MULTILINE)

# Regex for first Markdown heading
_HEADING_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class SkillInfo:
    """Immutable representation of a skill command template."""

    skill_id: str  # File stem, e.g., "basic-decompose"
    name: str  # Display name, e.g., "基础拆解"
    description: str  # One-line description
    icon: str  # Icon identifier (e.g., "puzzle", "target")
    file_path: str  # Absolute path to the .md file


@dataclass
class SkillContent:
    """Skill metadata plus full template content."""

    skill_id: str
    name: str
    description: str
    icon: str
    content: str  # Full .md file content (including frontmatter)
    file_path: str


class SkillRegistry:
    """
    Registry that scans .claude/commands/ and provides skill metadata.

    Thread-safe. Call load() once during startup or on-demand via refresh().
    """

    _instance: Optional["SkillRegistry"] = None
    # Use threading.Lock for the synchronous singleton pattern (called from
    # both sync and async code paths). The lock is only held for object
    # construction (microseconds), so it does not block the event loop.
    _lock = threading.Lock()

    def __init__(self, commands_dir: Optional[Path] = None):
        self._commands_dir = commands_dir or _DEFAULT_COMMANDS_DIR
        self._skills: Dict[str, SkillInfo] = {}
        self._loaded = False
        # asyncio.Lock for protecting concurrent async operations (e.g. refresh)
        self._async_lock = asyncio.Lock()

    # ─── Singleton ────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls, commands_dir: Optional[Path] = None) -> "SkillRegistry":
        """Return the singleton SkillRegistry, creating it if needed.

        Uses threading.Lock (not asyncio.Lock) because this is a synchronous
        class method that must work from both sync and async contexts.
        The lock is held only for object construction (microseconds).
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(commands_dir=commands_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing only)."""
        with cls._lock:
            cls._instance = None

    # ─── Loading ──────────────────────────────────────────────────────────

    def load(self) -> int:
        """
        Scan .claude/commands/ and load all .md skill templates.

        Returns:
            Number of skills successfully loaded.
        """
        if not self._commands_dir.exists():
            logger.warning(
                "[SkillRegistry] Commands directory does not exist: %s",
                self._commands_dir,
            )
            self._skills.clear()
            self._loaded = True
            return 0

        self._skills.clear()
        loaded_count = 0

        for md_file in sorted(self._commands_dir.glob("*.md")):
            try:
                skill = self._parse_skill(md_file)
                self._skills[skill.skill_id] = skill
                loaded_count += 1
                logger.debug(
                    "[SkillRegistry] Loaded skill: %s (%s)",
                    skill.skill_id,
                    skill.name,
                )
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                logger.warning(
                    "[SkillRegistry] Failed to parse skill file %s: %s",
                    md_file.name,
                    exc,
                )

        self._loaded = True
        logger.info(
            "[SkillRegistry] Loaded %d skills from %s",
            loaded_count,
            self._commands_dir,
        )
        return loaded_count

    def refresh(self) -> int:
        """
        Rescan the commands directory. Supports AC-4 (user custom skills).

        Returns:
            Number of skills after refresh.
        """
        return self.load()

    def _parse_skill(self, file_path: Path) -> SkillInfo:
        """Parse a single .md file into SkillInfo."""
        raw = file_path.read_text(encoding="utf-8")
        skill_id = file_path.stem  # e.g., "basic-decompose"

        name = ""
        description = ""
        icon = "file-text"  # default icon

        # Try extracting from YAML frontmatter.
        # Use yaml.safe_load for robust parsing of multi-line values, quoted
        # strings, and other YAML features that the simple regex misses.
        fm_match = _FRONTMATTER_PATTERN.match(raw)
        if fm_match:
            fm_block = fm_match.group(1)
            try:
                import yaml

                fm_data = yaml.safe_load(fm_block) or {}
                if isinstance(fm_data, dict):
                    name = str(fm_data.get("name", "")).strip()
                    description = str(fm_data.get("description", "")).strip()
                    icon = str(fm_data.get("icon", icon)).strip()
                else:
                    # YAML parsed but not a dict — fall through to heading
                    fm_data = {}
            except Exception:
                # yaml.safe_load failed — fallback to regex key-value extraction
                fm_kvs = dict(_YAML_KV_PATTERN.findall(fm_block))
                name = fm_kvs.get("name", "").strip().strip('"').strip("'")
                description = fm_kvs.get("description", "").strip().strip('"').strip("'")
                icon = fm_kvs.get("icon", icon).strip().strip('"').strip("'")

        # Fallback: extract name from first # heading
        if not name:
            heading_match = _HEADING_PATTERN.search(raw)
            if heading_match:
                name = heading_match.group(1).strip()

        # Fallback: use skill_id as name
        if not name:
            name = skill_id

        # Fallback: extract description from first non-heading paragraph
        if not description:
            description = self._extract_first_paragraph(raw)

        return SkillInfo(
            skill_id=skill_id,
            name=name,
            description=description,
            icon=icon,
            file_path=str(file_path.resolve()),
        )

    @staticmethod
    def _extract_first_paragraph(content: str) -> str:
        """
        Extract the first non-empty paragraph after frontmatter and heading.

        Used as fallback description when frontmatter lacks 'description'.
        """
        # Remove frontmatter
        fm_match = _FRONTMATTER_PATTERN.match(content)
        if fm_match:
            content = content[fm_match.end() :]

        lines = content.split("\n")
        paragraph_lines: list[str] = []
        found_heading = False

        for line in lines:
            stripped = line.strip()
            # Skip empty lines before content
            if not stripped:
                if paragraph_lines:
                    break  # End of first paragraph
                continue
            # Skip headings
            if stripped.startswith("#"):
                found_heading = True
                continue
            # Skip usage lines and code blocks
            if stripped.startswith("**用法**") or stripped.startswith("```"):
                if paragraph_lines:
                    break
                continue
            # Collect paragraph text
            if found_heading or not stripped.startswith("#"):
                paragraph_lines.append(stripped)

        result = " ".join(paragraph_lines)
        # Truncate to reasonable description length
        if len(result) > 120:
            result = result[:117] + "..."
        return result

    # ─── Query API ────────────────────────────────────────────────────────

    def list_skills(self) -> List[SkillInfo]:
        """
        Return all loaded skills as a sorted list.

        Auto-loads if not yet loaded.
        """
        if not self._loaded:
            self.load()
        return sorted(self._skills.values(), key=lambda s: s.skill_id)

    def get_skill(self, skill_id: str) -> Optional[SkillInfo]:
        """Return skill metadata by ID, or None if not found."""
        if not self._loaded:
            self.load()
        return self._skills.get(skill_id)

    def get_skill_content(self, skill_id: str) -> Optional[SkillContent]:
        """
        Return full skill metadata + template content.

        Reads the file content fresh each time to support live editing.
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            return None

        file_path = Path(skill.file_path)
        if not file_path.exists():
            logger.warning(
                "[SkillRegistry] Skill file no longer exists: %s",
                skill.file_path,
            )
            return None

        content = file_path.read_text(encoding="utf-8")
        return SkillContent(
            skill_id=skill.skill_id,
            name=skill.name,
            description=skill.description,
            icon=skill.icon,
            content=content,
            file_path=skill.file_path,
        )

    @property
    def is_loaded(self) -> bool:
        """Whether load() has been called."""
        return self._loaded

    @property
    def commands_dir(self) -> Path:
        """Return the configured commands directory path."""
        return self._commands_dir


# ─── Module-level convenience ─────────────────────────────────────────────


def get_skill_registry(
    commands_dir: Optional[Path] = None,
) -> SkillRegistry:
    """Get the singleton SkillRegistry instance."""
    return SkillRegistry.get_instance(commands_dir=commands_dir)
