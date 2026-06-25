"""P1 (A+-prime 2026-06-26): 节点当前态信号读取 — frontmatter 是真相源, 非 Graphiti。

A+-prime 分层契约 (ChatGPT 二审收敛):
- **当前态** (出题用"最新干净版"): 读 .md frontmatter tips[]/relationships[] —
  完全覆盖语义, 用户删改立即生效 (FrontmatterTipsSync 完全覆盖 + 原生删除)。
- **历史事件流** (时光机/演化): Graphiti :Entity-RELATES_TO 边 — append-only, 不直接
  喂 ACP 当前态。

为什么切: 此前 question_generator._get_tips 等直接读 Graphiti active 边
(invalid_at is None) 当当前态喂出题。但 Graphiti 无 tombstone, 用户删/改 callout
后旧边仍 active → 幽灵记忆污染针对性出题 (ChatGPT 二审 拷问4)。frontmatter 是
真相源且原生支持删除 → 当前态读它根治幽灵记忆。

[Source: _bmad-output/研究/2026-06-13-同步契约-务实方案-待ChatGPT审查.md A+-prime P1]
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import frontmatter

from app.config import settings

logger = logging.getLogger(__name__)

# 扁平节点池约定: node_id = 文件 basename, 落在 节点/ 或 原白板/ 下
_NODE_DIR_PREFIXES = ("节点", "原白板")


def _node_md_path(node_id: str) -> Path | None:
    """node_id → .md 路径 (节点/ 优先, 退 原白板/)。找不到返回 None。"""
    canvas_base = getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
    for prefix in _NODE_DIR_PREFIXES:
        p = Path(canvas_base) / prefix / f"{node_id}.md"
        if p.exists():
            return p
    return None


def read_node_frontmatter_signals(node_id: str) -> dict[str, Any]:
    """读节点 frontmatter → 当前态 {tips, errors, edge_reasons}。

    - tips:  frontmatter tips[] 中 tag != 'error' 的 text (List[str])
    - errors: tips[] 中 tag == 'error' 的项 (List[dict], 对齐旧 _get_error_history 形状)
    - edge_reasons: relationships[].description (List[str], 节点增殖原因)

    文件不存在 / 无 frontmatter → 全空 (= 当前态确实为空, 忠实反映用户删除,
    不再回退 Graphiti 以免重新引入幽灵记忆)。
    """
    result: dict[str, list[Any]] = {"tips": [], "errors": [], "edge_reasons": []}
    path = _node_md_path(node_id)
    if path is None:
        return result
    try:
        post = frontmatter.load(str(path))
    except (OSError, ValueError, UnicodeDecodeError) as e:
        logger.debug("[P1] frontmatter 读取失败 %s: %s", node_id, e)
        return result

    fm = post.metadata or {}
    for ft in fm.get("tips") or []:
        if not isinstance(ft, dict):
            continue
        text = str(ft.get("text") or "").strip()
        if not text:
            continue
        if ft.get("tag") == "error":
            result["errors"].append(
                {
                    "error_type": "user_marked",
                    "description": text,
                    "remedy": "",
                }
            )
        else:
            result["tips"].append(text)

    for rel in fm.get("relationships") or []:
        if not isinstance(rel, dict):
            continue
        desc = str(rel.get("description") or "").strip()
        if desc:
            result["edge_reasons"].append(desc)

    return result
