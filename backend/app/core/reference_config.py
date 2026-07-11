"""
Reference source priority configuration.

Loads priority rules from data/reference_priority.json.
Rules define which vault sources are boosted/penalized in search results.
"""

import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "data" / "reference_priority.json"

# Cached config
_config: Dict[str, Any] | None = None


def _load_config() -> Dict[str, Any]:
    global _config
    if _config is not None:
        return _config

    default = {
        "source_priorities": [
            {"pattern": "videos/lectures/**", "weight": 1.5, "label": "讲义"},
            {"pattern": "videos/discussions/**", "weight": 1.4, "label": "讨论"},
            {"pattern": "*-explanations/**", "weight": 0.5, "label": "AI解释"},
        ],
        "max_references": 5,
    }

    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                _config = json.load(f)
                logger.info(
                    f"Loaded reference priority config: {len(_config.get('source_priorities', []))} rules"
                )
                return _config
    except (json.JSONDecodeError, ValueError, KeyError, OSError) as e:
        logger.warning(f"Failed to load reference_priority.json: {e}, using defaults")

    _config = default
    return _config


def reload_config() -> None:
    """Force reload config from disk (for hot-reload or API update)."""
    global _config
    _config = None
    _load_config()


def get_source_priorities() -> List[Dict[str, Any]]:
    return _load_config().get("source_priorities", [])


def get_max_references() -> int:
    return _load_config().get("max_references", 5)


def apply_source_priority(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply source priority weights to search results and re-sort."""
    priorities = get_source_priorities()
    if not priorities:
        return results

    for r in results:
        metadata = r.get("metadata", {})
        path = metadata.get("canvas_file", "")

        # Try metadata_json for file_path if canvas_file empty
        if not path:
            meta_json = metadata.get("metadata_json", "")
            if meta_json and isinstance(meta_json, str):
                try:
                    path = json.loads(meta_json).get("file_path", "")
                except json.JSONDecodeError:
                    pass

        if not path:
            continue

        for p in priorities:
            if fnmatch(path, p["pattern"]):
                original_score = r.get("score", 0.0)
                # R1 根因二 (2026-07-12): 保留原始语义分 — 乘性权重曾在
                # min_relevance 过滤前执行, 把"语义相关性"和"来源优先级"两个
                # 正交维度乘在一起: 无关材料 ×1.5 击穿门槛 (烤面包查询 10 条
                # 全过), 正确命中 ×0.3/×0.9 被误杀。此后契约: 过滤用
                # _raw_score (语义), 排序/展示用 score (加权) — 各司其职。
                r["_raw_score"] = original_score
                r["score"] = original_score * p["weight"]
                break

    return sorted(results, key=lambda x: x.get("score", 0.0), reverse=True)
