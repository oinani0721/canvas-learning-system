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


#: P1-05 (Codex 对抗审查 2026-08-19 · R11-BATCH2 返工): 中性降级的 max_references。
#: 与正式 JSON 保持一致, 避免降级态顺带改变返回条数。
_NEUTRAL_MAX_REFERENCES = 10


def _load_config() -> Dict[str, Any]:
    """加载引用优先级配置; 失败时**中性降级**而非退回旧权重。

    ⛔ P1-05 修复 (Codex 审查 2026-08-19): 此处原本硬编码一份 fallback ——
    videos/lectures 1.5 · videos/discussions 1.4 · max_references 5 —— 那是
    RAG-S2 T2 (2026-08-09) 权重翻转**之前**的旧值, 方向与正式配置**相反**:
    它把视频转录系统性加权到用户手写笔记之上, 正是那次翻转要纠正的问题。
    于是配置文件一旦缺失或损坏, 系统会静默回到用户初衷的反面。
    更隐蔽的是 `_CONFIG_PATH.exists()` 为 False 时根本不进 except 分支,
    连一条 warning 都没有 —— 纯静默。

    改为中性降级: 空规则列表 = 不做任何 boost/demote
    (apply_source_priority 的 `if not priorities: return results` 已支持该路径),
    引用排序退化为纯语义分序。

    为何不 fail-closed 抛错: 本模块只影响引用**排序**, 让整条检索链挂掉的代价
    高于不加权。为何不复制一份新权重: 那会造出第三份真相源, 下次调权重又要
    同步两处 —— 正是本次要消除的问题。
    """
    global _config
    if _config is not None:
        return _config

    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                _config = json.load(f)
                logger.info(f"Loaded reference priority config: {len(_config.get('source_priorities', []))} rules")
                return _config
        logger.error(
            "reference_priority.json 不存在 (%s) — 中性降级: 引用排序退化为纯语义分序, "
            "用户手写笔记不再获得提权。请检查部署是否漏挂 data 目录。",
            _CONFIG_PATH,
        )
    except (json.JSONDecodeError, ValueError, KeyError, OSError) as e:
        logger.error(
            "reference_priority.json 加载失败 (%s) — 中性降级: 引用排序退化为纯语义分序: %s",
            _CONFIG_PATH,
            e,
        )

    # 每次新建 dict/list, 不共享可变对象 (调用方若就地改动不会污染后续调用)
    _config = {"source_priorities": [], "max_references": _NEUTRAL_MAX_REFERENCES}
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
