# Canvas Learning System - Subject Resolver Service
# Story 38.1: Canvas Metadata Management System
"""
Subject Resolver Service.

Resolves subject, category, and group_id for Canvas files using
a multi-priority resolution strategy:

1. Manual override (API parameter)
2. Configuration file mapping (subject_mapping.yaml)
3. Path-based auto-inference
4. Default values

[Source: Design doc - Phase 2.2]
"""

import fnmatch
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from app.models.metadata_models import (
    MetadataSource,
    SubjectInfo,
    SubjectMappingConfig,
    SubjectMappingRule,
)

logger = logging.getLogger(__name__)


class SubjectResolver:
    """
    Subject resolver service.

    Provides unified subject/category/group_id resolution for Canvas files.

    Usage:
        >>> resolver = SubjectResolver(config_path="backend/config/subject_mapping.yaml")
        >>> info = resolver.resolve("Math 54/离散数学.canvas")
        >>> print(info.subject)  # "math54"
        >>> print(info.group_id)  # "math54:离散数学"

    [Source: Design doc - Phase 2.2 SubjectResolver Service]
    """

    # Default skip directories (merged with config)
    DEFAULT_SKIP_DIRS = {
        ".obsidian", ".git", "笔记库", "vault", "notes",
        "templates", "attachments", ".canvas-links"
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        auto_load: bool = True
    ):
        """
        Initialize SubjectResolver.

        Args:
            config_path: Path to subject_mapping.yaml (optional)
            auto_load: Whether to load config automatically
        """
        self.config_path = config_path or self._find_config_path()
        self.config: Optional[SubjectMappingConfig] = None
        self._skip_dirs = set(self.DEFAULT_SKIP_DIRS)

        if auto_load:
            self.load_config()

    def _find_config_path(self) -> str:
        """
        Find the default config file path.

        Searches in order:
        1. backend/config/subject_mapping.yaml
        2. config/subject_mapping.yaml
        3. ./subject_mapping.yaml
        """
        candidates = [
            Path(__file__).parent.parent.parent / "config" / "subject_mapping.yaml",
            Path("backend/config/subject_mapping.yaml"),
            Path("config/subject_mapping.yaml"),
            Path("subject_mapping.yaml"),
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        # Return default path even if doesn't exist
        return str(candidates[0])

    def load_config(self) -> bool:
        """
        Load configuration from YAML file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                self.config = SubjectMappingConfig()
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)

            if raw_config is None:
                raw_config = {}

            # Parse mappings
            mappings = []
            for m in raw_config.get("mappings", []):
                mappings.append(SubjectMappingRule(
                    pattern=m.get("pattern", ""),
                    subject=m.get("subject", ""),
                    category=m.get("category", "")
                ))

            # Parse config
            self.config = SubjectMappingConfig(
                mappings=mappings,
                category_rules=raw_config.get("category_rules", {}),
                defaults=raw_config.get("defaults", {
                    "subject": "general",
                    "category": "general"
                })
            )

            # Update skip directories
            skip_dirs = raw_config.get("skip_directories", [])
            self._skip_dirs.update(skip_dirs)

            logger.info(
                f"SubjectResolver config loaded: "
                f"{len(mappings)} mappings, "
                f"{len(self.config.category_rules)} category rules"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = SubjectMappingConfig()
            return False

    def resolve(
        self,
        canvas_path: str,
        manual_subject: Optional[str] = None,
        manual_category: Optional[str] = None
    ) -> SubjectInfo:
        """
        Resolve subject, category, and group_id for a Canvas file.

        Resolution priority:
        1. Manual override (if both subject and category provided)
        2. Configuration file mapping
        3. Path-based auto-inference
        4. Default values

        Args:
            canvas_path: Canvas file path (relative or absolute)
            manual_subject: Manual subject override (optional)
            manual_category: Manual category override (optional)

        Returns:
            SubjectInfo with subject, category, group_id, and source
        """
        # Normalize path
        normalized_path = self._normalize_path(canvas_path)
        canvas_name = self._extract_canvas_name(normalized_path)

        # 1. Manual override (highest priority)
        if manual_subject and manual_category:
            group_id = f"{manual_subject}:{canvas_name}"
            return SubjectInfo(
                subject=manual_subject,
                category=manual_category,
                group_id=group_id,
                source=MetadataSource.MANUAL
            )

        # Ensure config is loaded
        if self.config is None:
            self.load_config()

        # 2. Configuration file mapping
        config_result = self._resolve_from_config(normalized_path)
        if config_result:
            subject, category = config_result
            group_id = f"{subject}:{canvas_name}"
            return SubjectInfo(
                subject=subject,
                category=category,
                group_id=group_id,
                source=MetadataSource.CONFIG
            )

        # 3. Path-based auto-inference
        inferred_result = self._infer_from_path(normalized_path)
        if inferred_result:
            subject, category = inferred_result
            group_id = f"{subject}:{canvas_name}"
            return SubjectInfo(
                subject=subject,
                category=category,
                group_id=group_id,
                source=MetadataSource.INFERRED
            )

        # 4. Default values
        defaults = self.config.defaults if self.config else {
            "subject": "general",
            "category": "general"
        }
        subject = defaults.get("subject", "general")
        category = defaults.get("category", "general")
        group_id = f"{subject}:{canvas_name}"

        return SubjectInfo(
            subject=subject,
            category=category,
            group_id=group_id,
            source=MetadataSource.DEFAULT
        )

    def _normalize_path(self, canvas_path: str) -> str:
        """
        Normalize Canvas path for consistent matching.

        - Convert backslashes to forward slashes
        - Remove leading/trailing slashes
        - Remove .canvas extension for matching
        """
        # Convert to forward slashes
        normalized = canvas_path.replace("\\", "/")

        # Remove leading slashes
        normalized = normalized.lstrip("/")

        return normalized

    def _extract_canvas_name(self, canvas_path: str) -> str:
        """
        Extract Canvas name from path.

        "Math 54/离散数学.canvas" → "离散数学"
        "离散数学.canvas" → "离散数学"
        """
        # Get filename
        filename = os.path.basename(canvas_path)

        # Remove .canvas extension
        if filename.endswith(".canvas"):
            filename = filename[:-7]

        return filename

    def _resolve_from_config(
        self,
        normalized_path: str
    ) -> Optional[Tuple[str, str]]:
        """
        Resolve subject/category from configuration mappings.

        Args:
            normalized_path: Normalized Canvas path

        Returns:
            (subject, category) tuple if matched, None otherwise
        """
        if not self.config or not self.config.mappings:
            return None

        for rule in self.config.mappings:
            if self._match_pattern(normalized_path, rule.pattern):
                logger.debug(
                    f"Config match: {normalized_path} → "
                    f"{rule.pattern} → ({rule.subject}, {rule.category})"
                )
                return (rule.subject, rule.category)

        return None

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if path matches a glob pattern.

        Supports:
        - ** for recursive matching
        - * for single-level matching
        """
        # Normalize pattern
        pattern = pattern.replace("\\", "/").rstrip("/")

        # Handle ** pattern (recursive)
        if "**" in pattern:
            # Convert ** to regex
            regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
            regex_pattern = f"^{regex_pattern}"
            return bool(re.match(regex_pattern, path, re.IGNORECASE))

        # Handle * pattern (single level)
        if "*" in pattern:
            return fnmatch.fnmatch(path.lower(), pattern.lower())

        # Exact prefix match
        return path.lower().startswith(pattern.lower() + "/") or \
               path.lower() == pattern.lower()

    def _infer_from_path(
        self,
        normalized_path: str
    ) -> Optional[Tuple[str, str]]:
        """
        Infer subject/category from path using category rules.

        Uses the first significant directory component (skipping
        common non-subject directories) to infer the category.

        Args:
            normalized_path: Normalized Canvas path

        Returns:
            (subject, category) tuple if inferred, None otherwise
        """
        # Split path into components
        parts = normalized_path.split("/")

        # Find first significant directory
        first_dir = None
        for part in parts[:-1]:  # Exclude filename
            if part and part.lower() not in {d.lower() for d in self._skip_dirs}:
                first_dir = part
                break

        if not first_dir:
            # No directory, use filename as subject
            canvas_name = self._extract_canvas_name(normalized_path)
            # Try to match category rules against canvas name
            category = self._match_category_rules(canvas_name)
            if category:
                subject = self._normalize_subject_name(canvas_name)
                return (subject, category)
            return None

        # Try to match category rules
        category = self._match_category_rules(first_dir)
        if category:
            subject = self._normalize_subject_name(first_dir)
            return (subject, category)

        # No match, use first directory as both subject and category
        subject = self._normalize_subject_name(first_dir)
        return (subject, subject)

    def _match_category_rules(self, name: str) -> Optional[str]:
        """
        Match a name against category rules.

        Args:
            name: Directory or file name to match

        Returns:
            Category if matched, None otherwise
        """
        if not self.config or not self.config.category_rules:
            return None

        name_lower = name.lower()

        for category, patterns in self.config.category_rules.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower.endswith("*"):
                    # Prefix match
                    if name_lower.startswith(pattern_lower[:-1]):
                        return category
                elif name_lower == pattern_lower:
                    # Exact match
                    return category

        return None

    def _normalize_subject_name(self, name: str) -> str:
        """
        Normalize a name into a valid subject identifier.

        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove special characters
        """
        # Convert to lowercase
        subject = name.lower()

        # Replace spaces and underscores with hyphens
        subject = subject.replace(" ", "-").replace("_", "-")

        # Remove characters that aren't alphanumeric, hyphens, or Chinese
        subject = re.sub(r'[^\w\-\u4e00-\u9fff]', '', subject)

        # Remove consecutive hyphens
        subject = re.sub(r'-+', '-', subject)

        # Remove leading/trailing hyphens
        subject = subject.strip('-')

        return subject or "unknown"

    def get_config(self) -> SubjectMappingConfig:
        """
        Get current configuration.

        Returns:
            Current SubjectMappingConfig
        """
        if self.config is None:
            self.load_config()
        return self.config or SubjectMappingConfig()

    def update_config(self, new_config: SubjectMappingConfig) -> bool:
        """
        Update and save configuration.

        Args:
            new_config: New configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Build YAML structure
            yaml_data: Dict[str, Any] = {
                "mappings": [
                    {
                        "pattern": m.pattern,
                        "subject": m.subject,
                        "category": m.category
                    }
                    for m in new_config.mappings
                ],
                "category_rules": new_config.category_rules,
                "defaults": new_config.defaults,
                "skip_directories": list(self._skip_dirs)
            }

            # Write to file
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    yaml_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )

            # Update in-memory config
            self.config = new_config

            logger.info(f"SubjectResolver config saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def add_mapping(
        self,
        pattern: str,
        subject: str,
        category: str
    ) -> bool:
        """
        Add a new mapping rule.

        Args:
            pattern: Folder pattern
            subject: Subject identifier
            category: Category identifier

        Returns:
            True if added successfully
        """
        if self.config is None:
            self.load_config()

        if self.config is None:
            self.config = SubjectMappingConfig()

        # Check for duplicate pattern
        for existing in self.config.mappings:
            if existing.pattern.lower() == pattern.lower():
                # Update existing
                existing.subject = subject
                existing.category = category
                return self.update_config(self.config)

        # Add new mapping
        new_rule = SubjectMappingRule(
            pattern=pattern,
            subject=subject,
            category=category
        )
        self.config.mappings.append(new_rule)

        return self.update_config(self.config)

    def remove_mapping(self, pattern: str) -> bool:
        """
        Remove a mapping rule by pattern.

        Args:
            pattern: Pattern to remove

        Returns:
            True if removed successfully
        """
        if self.config is None:
            self.load_config()

        if self.config is None:
            return False

        original_count = len(self.config.mappings)
        self.config.mappings = [
            m for m in self.config.mappings
            if m.pattern.lower() != pattern.lower()
        ]

        if len(self.config.mappings) < original_count:
            return self.update_config(self.config)

        return False


# =============================================================================
# Singleton Instance
# =============================================================================

_resolver_instance: Optional[SubjectResolver] = None


def get_subject_resolver() -> SubjectResolver:
    """
    Get singleton SubjectResolver instance.

    Returns:
        SubjectResolver singleton
    """
    global _resolver_instance

    if _resolver_instance is None:
        _resolver_instance = SubjectResolver()

    return _resolver_instance


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SubjectResolver",
    "get_subject_resolver",
]
