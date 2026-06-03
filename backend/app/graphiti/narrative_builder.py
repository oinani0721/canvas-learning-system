# Canvas Learning System - Narrative Builder (5-ge-1 AC#6)
#
# 把 CanvasGraphEpisodeV1 结构化事件渲染成自然语言叙述句, 含 [[wikilink]] 关系 +
# 探索路径。narrative 是 Graphiti search_facts 语义命中的关键载体 (AC#6)。
#
# 纯函数, 无副作用, 不触网。
#
# [Source: _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md AC#6]

from __future__ import annotations

from app.graphiti.canvas_episode import CanvasGraphEpisodeV1, ContextPayload, EventType


def _wiki(node: str) -> str:
    """渲染为 Obsidian 双链 [[node]]。"""
    return f"[[{node}]]"


def _path_trace(ctx: ContextPayload) -> str:
    """探索路径渲染: ['概览','递归定义','base case'] → '[概览]→[递归定义]→[base case]'。"""
    if not ctx.path_trace:
        return ""
    return "→".join(f"[{p}]" for p in ctx.path_trace)


def _bracket_list(items: list[str]) -> str:
    """['回溯','树递归'] → '[回溯][树递归]'。"""
    return "".join(f"[{x}]" for x in items)


def _links_clause(ctx: ContextPayload) -> str:
    """出链 / 反向引用从句 (两端可空)。"""
    parts: list[str] = []
    if ctx.out_links:
        parts.append(f"该节点出链到 {_bracket_list(ctx.out_links)}")
    if ctx.in_links:
        parts.append(f"被 {_bracket_list(ctx.in_links)} 反向引用")
    return ", ".join(parts)


def _location_clause(payload: CanvasGraphEpisodeV1) -> str:
    """白板 + 探索路径定位从句, 如 '在 [递归白板] 中沿 [概览]→[base case] 路径'。"""
    ctx = payload.context
    board = ctx.source_board or payload.canvas_path
    trace = _path_trace(ctx)
    loc = f"在 [{board}] 中" if board else ""
    if trace:
        loc += f"沿 {trace} 路径"
    return loc


def build_narrative(payload: CanvasGraphEpisodeV1) -> str:
    """把 CanvasGraphEpisodeV1 渲染成自然语言叙述 (含 [[wikilink]] + 探索路径)。

    示例 (callout_added):
        用户在 [递归白板] 中沿 [概览]→[递归定义]→[base case] 路径, 对节点
        [[recursion-base-case]] 写下 tip: "递归一定要先想 base case"。
        该节点出链到 [回溯][树递归], 被 [递归总览][DFS] 反向引用。
    """
    et = payload.event_type
    loc = _location_clause(payload)
    links = _links_clause(payload.context)
    node = _wiki(payload.node_id)

    # ── callout 类 ───────────────────────────────────────────────────────
    if et in (
        EventType.CALLOUT_ADDED,
        EventType.CALLOUT_UPDATED,
        EventType.CALLOUT_REMOVED,
    ):
        verb = {
            EventType.CALLOUT_ADDED: "写下",
            EventType.CALLOUT_UPDATED: "修改",
            EventType.CALLOUT_REMOVED: "删除",
        }[et]
        ctype = payload.callout.callout_type if payload.callout else "note"
        text = payload.callout.text if payload.callout else ""
        loc_sep = ", " if loc else ""  # NIT1: loc 为空时不留悬挂逗号
        sentence = f'用户{loc}{loc_sep}对节点 {node} {verb} {ctype}: "{text}"。'

    # ── wikilink 类 ──────────────────────────────────────────────────────
    elif et in (EventType.WIKILINK_ADDED, EventType.WIKILINK_REMOVED):
        verb = "新增" if et == EventType.WIKILINK_ADDED else "删除"
        rel = payload.relation_type or "related_to"
        src = _wiki(payload.source_node_id or payload.node_id)
        tgt = _wiki(payload.target_node_id or payload.node_id)
        sentence = f"用户{loc}{verb}了从 {src} 到 {tgt} 的「{rel}」关系。"

    # ── calibration 类 ───────────────────────────────────────────────────
    elif et == EventType.CALIBRATION_VOTE:
        vote = payload.callout.text if payload.callout else ""
        suffix = f': "{vote}"' if vote else ""
        sentence = f"用户{loc}对节点 {node} 做了校准投票{suffix}。"

    # ── error 类 ─────────────────────────────────────────────────────────
    elif et == EventType.ERROR_MARKED:
        detail = payload.callout.text if payload.callout else ""
        suffix = f', 记录: "{detail}"' if detail else ""
        sentence = f"用户{loc}在节点 {node} 上标记了错误{suffix}。"

    else:  # 兜底 (理论不可达, EventType 已穷举)
        sentence = f"用户{loc}对节点 {node} 触发了事件 {et.value}。"

    if links:
        sentence += f" {links}。"
    return sentence
