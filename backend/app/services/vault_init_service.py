"""Vault initialization and plugin detection service.

Creates the standard Canvas Learning System vault directory structure,
generates Templater-compatible template files, and detects required
Obsidian plugins.

[Source: Story 1.1 — FR-SYS-01, FR-SYS-06]
"""

import json
from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

VAULT_DIRECTORIES = [
    "raw",
    "wiki/concepts",
    "wiki/canvases",
    "outputs/exam_boards",
]

REQUIRED_COMMUNITY_PLUGINS = [
    ("dataview", "Dataview"),
    ("templater-obsidian", "Templater"),
    ("quickadd", "QuickAdd"),
    ("obsidian-meta-bind-plugin", "Meta Bind"),
]

REQUIRED_CORE_PLUGINS = [
    ("bases", "Bases"),
]

CLAUDE_MD_SKELETON = """\
# Canvas Learning System — Vault

## 目录结构

| 目录 | 用途 |
|------|------|
| `raw/` | 原始导入笔记（未处理） |
| `wiki/concepts/` | 概念笔记（Templater 模板生成） |
| `wiki/canvases/` | Obsidian Canvas 画布文件 |
| `outputs/exam_boards/` | 考察板（exam-board 模板生成） |

## Templater 模板

- `concept.md` — 新建概念笔记时自动填充 frontmatter（掌握度、复习时间、关系等）
- `exam-board.md` — 新建考察板时自动填充题目和评分结构

## Claudian 使用指南

通过 Claudian（Claude MCP sidecar）与后端交互：
- "帮我检查系统状态" — 运行启动验证（Neo4j/Ollama/FastAPI/MCP）
- "帮我复习" — 查看待复习概念（基于 FSRS 算法）
- "拆解这个概念" — 将复杂概念分解为子问题
"""


@dataclass
class PluginStatus:
    plugin_id: str
    display_name: str
    plugin_type: str
    installed: bool


class VaultInitService:
    def initialize_vault(self, vault_path: str) -> dict:
        root = Path(vault_path)
        root.mkdir(parents=True, exist_ok=True)
        created = []
        skipped = []

        for dir_rel in VAULT_DIRECTORIES:
            dir_path = root / dir_rel
            if dir_path.exists():
                skipped.append(dir_rel)
                logger.info("vault_dir_exists", path=dir_rel)
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(dir_rel)
                logger.info("vault_dir_created", path=dir_rel)

            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

        claude_md = root / "CLAUDE.md"
        if not claude_md.exists():
            claude_md.write_text(CLAUDE_MD_SKELETON)
            logger.info("claude_md_created", path=str(claude_md))
        else:
            logger.info("claude_md_exists", path=str(claude_md))

        return {"created": created, "skipped": skipped}

    def check_required_plugins(self, vault_path: str) -> list[PluginStatus]:
        root = Path(vault_path)
        obsidian_dir = root / ".obsidian"
        results: list[PluginStatus] = []

        community_installed: list[str] = []
        community_plugins_file = obsidian_dir / "community-plugins.json"
        if community_plugins_file.exists():
            try:
                community_installed = json.loads(community_plugins_file.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning(
                    "community_plugins_parse_error", path=str(community_plugins_file)
                )

        for plugin_id, display_name in REQUIRED_COMMUNITY_PLUGINS:
            results.append(
                PluginStatus(
                    plugin_id=plugin_id,
                    display_name=display_name,
                    plugin_type="community",
                    installed=plugin_id in community_installed,
                )
            )

        core_installed: list[str] = []
        core_plugins_file = obsidian_dir / "core-plugins.json"
        if core_plugins_file.exists():
            try:
                core_installed = json.loads(core_plugins_file.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("core_plugins_parse_error", path=str(core_plugins_file))

        for plugin_id, display_name in REQUIRED_CORE_PLUGINS:
            results.append(
                PluginStatus(
                    plugin_id=plugin_id,
                    display_name=display_name,
                    plugin_type="core",
                    installed=plugin_id in core_installed,
                )
            )

        return results
