# ChatGPT 最终审查 prompt — Story 2.1 Phase 1.7+ (commit 11e6e26)

> **目的**：确认 ChatGPT 对 cefabb2 提的 5 个 P0 已经全部修复 + 没有新引入 regression。如果 PASS，转入非技术用户 UAT。

---

## 审查指引（system prompt）

你是有 15 年生产 Python 后端经验的 staff engineer，做**对抗性 code review**。这是同一个项目的第二轮审查 — 上次基于 `cefabb2` 你给了 5 P0 + 多个 HIGH，评分 4/10。我已经按你的反馈修了，现在请基于 `11e6e26` 重新评估。

任务：
1. **验证 P0 修复**：你之前指出的 5 P0 是否真的修了，是否引入新 regression
2. **找新问题**：修复代码本身可能有 bug（line scanner 边界 / escape 函数边界）
3. **决定 ship 资格**：如果≤2 个新 P0 + ≤5 个新 HIGH 且核心场景验收通过 → recommend ship 给非技术用户做 UAT。否则继续阻断。

输出 format：
```
## P0 修复验证
- P0#1 (trace 传递): ✅/❌ + 证据
- P0#2 (build_timestamp): ✅/❌ + 证据
- P0#5 (callout 吞并): ✅/❌ + 证据
- P0-A (path traversal): ✅/❌ + 证据
- P0-B (prompt injection): ✅/❌ + 证据

## 新发现
- [新 P0 数量] / [新 HIGH 数量]
- 详情列表（File:Line + Attack + Fix）

## Ship Recommendation
- [评分 X/10]
- ✅ Ship to UAT / ⚠️ Fix N items first / ❌ 仍有 ship blocker
```

---

## 项目坐标

```
仓库: oinani0721/canvas-learning-system
分支: worktree-feature-obsidian-hybrid-dev   ← 关键：不是 main
HEAD: 11e6e26                                 ← 最新审查目标
上次审查 HEAD: cefabb2                         ← 你给 5 P0 那次
```

GitHub fetch URL（需要 fetch 单文件可用 raw）:
```
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-obsidian-hybrid-dev/backend/app/api/v1/endpoints/chat.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-obsidian-hybrid-dev/backend/app/services/wikilink_graph_service.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-obsidian-hybrid-dev/backend/app/services/wikilink_context_service.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-obsidian-hybrid-dev/backend/app/services/chat_context_assembler.py
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/worktree-feature-obsidian-hybrid-dev/backend/app/main.py
```

测试文件:
```
backend/tests/unit/test_wikilink_context_service.py        (5 P0#5 + 4 P0-A regression)
backend/tests/unit/test_chat_context_assembler.py          (3 P0-B injection regression)
backend/tests/unit/test_chat_endpoint.py                   (P1.1 retrieval_trace test)
backend/tests/unit/test_wikilink_graph_service.py          (build_timestamp tests)
backend/tests/unit/test_security_p0_vulnerabilities.py     (专门 security file)
```

---

## 修复清单（详细对照）

### P0#1 — chat.py 没传 trace=enrichment.trace

**修复位置**：`backend/app/api/v1/endpoints/chat.py:156`

```python
assembled = assembler.assemble_context(
    current_note=current_note,
    neighbors=enrichment.neighbors,
    token_budget=req.token_budget,
    trace=enrichment.trace,  # ← 这一行是 P0#1 的修复
)
```

**说明**：这个修复早就在我本地 unstaged 改动里，但漏 commit 进了 `cefabb2`。所以你在 `cefabb2` 看到没传是真实状态，但我本地 backend 已经有这个 fix（这就是为什么用户实测 manifest 有真实 timestamp）。现在 11e6e26 已经把这个 unstaged 的 fix 一起 commit 进去了。

**Test**：`tests/unit/test_chat_endpoint.py::test_enrich_context_returns_retrieval_trace` 验证 manifest 含 graph_version + included items。

---

### P0#2 — WikilinkGraphService 缺 build_timestamp 字段

**修复位置**：`backend/app/services/wikilink_graph_service.py`

```python
class WikilinkGraphService:
    def __init__(self) -> None:
        # ...
        self._build_timestamp: Optional[str] = None  # ← 新增

    @property
    def build_timestamp(self) -> Optional[str]:  # ← 新增 property
        return self._build_timestamp

    async def build(self, vault_path: str) -> dict[str, Any]:
        # ... build logic ...
        async with self._lock:
            # ... existing assignments ...
            self._build_timestamp = datetime.now(timezone.utc).isoformat(  # ← 新增
                timespec="seconds"
            )

    def get_stats(self) -> dict[str, Any]:
        return {
            "vault_path": self._vault_path,
            "is_built": self.is_built,
            "total_nodes": self._node_count,
            "total_edges": self._edge_count,
            "build_timestamp": self._build_timestamp,  # ← 新增
        }
```

`wikilink_context_service.py` 的 `getattr(service, "build_timestamp", None) or "unbuilt"` 现在能拿到真实 ISO timestamp。

---

### P0#5 — _CALLOUT_PATTERN 贪婪 regex 吞并相邻 callout

**修复位置**：`backend/app/services/wikilink_context_service.py:_extract_user_callouts`

完全替换 regex 为 line scanner（O(n) 无 backtracking）：

```python
_CALLOUT_HEADER_PATTERN = re.compile(
    r"^[ ]{0,3}>[ ]?\[!(?P<kind>[\w/-]+)\][+-]?[ \t]*(?P<title>.*)$"
)
_QUOTE_PREFIX_PATTERN = re.compile(r"^[ ]{0,3}>")

def _extract_user_callouts(text: str) -> list[dict[str, str]]:
    if not text:
        return []
    callouts: list[dict] = []
    current: dict | None = None
    in_code_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        # Code fence toggle (``` 或 ~~~)
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            if current is not None:
                callouts.append(current)
                current = None
            continue
        if in_code_fence:
            continue
        # Callout header
        m = _CALLOUT_HEADER_PATTERN.match(line)
        if m:
            if current is not None:
                callouts.append(current)
                current = None
            kind_raw = (m.group("kind") or "").lower().strip()
            if not kind_raw:
                continue
            if any(kind_raw.startswith(p) for p in _NOISE_CALLOUT_KIND_PREFIXES):
                continue
            if kind_raw not in _USER_ANNOTATION_KINDS:
                continue
            title = (m.group("title") or "").strip()[:_CALLOUT_TITLE_MAX]
            current = {"kind": kind_raw, "title": title, "_lines": []}
            continue
        # Quote line
        if _QUOTE_PREFIX_PATTERN.match(line):
            if current is not None:
                stripped_q = _strip_quote_prefix(line)
                if stripped_q or current["_lines"]:
                    current["_lines"].append(stripped_q)
            continue
        # 非 quote 行 break 当前 callout
        if current is not None:
            callouts.append(current)
            current = None
    if current is not None:
        callouts.append(current)
    out: list[dict[str, str]] = []
    for c in callouts:
        content = "\n".join(c["_lines"]).strip()[:_CALLOUT_CONTENT_MAX]
        if c["title"] or content:
            out.append({"kind": c["kind"], "title": c["title"], "content": content})
        if len(out) >= _MAX_CALLOUTS_PER_NEIGHBOR:
            break
    return out
```

`_extract_body_excerpt` 也改成 line scanner（同样原理：跳过已识别的 callout block，保留普通 blockquote）。

**Test**：5 个 regression cases (相邻 / blank quote / 3 连续 / code fence / relation 噪音过滤)。

---

### P0-A — _read_neighbor_md path traversal

**修复位置**：`backend/app/services/wikilink_context_service.py:_resolve_vault_md_path`

```python
_MAX_NEIGHBOR_MD_BYTES = 1_000_000  # 1MB DoS cap

def _resolve_vault_md_path(neighbor_path: str, vault_path: str | None) -> Path | None:
    if not neighbor_path or not vault_path:
        return None
    try:
        root = Path(vault_path).resolve(strict=True)
        raw = Path(neighbor_path)
        candidate = (raw if raw.is_absolute() else root / raw).resolve(strict=True)
        # 边界检查: 必须在 vault root 下 (含 symlink resolve)
        candidate.relative_to(root)
        if candidate.suffix.lower() != ".md":
            return None
        if candidate.stat().st_size > _MAX_NEIGHBOR_MD_BYTES:
            logger.debug("wikilink_context.neighbor_too_large", ...)
            return None
        return candidate
    except (OSError, ValueError) as e:
        logger.debug("wikilink_context.neighbor_resolve_failed", ...)
        return None


def _read_neighbor_md(neighbor_path: str, vault_path: str | None) -> str | None:
    candidate = _resolve_vault_md_path(neighbor_path, vault_path)
    if candidate is None:
        return None
    try:
        return candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        logger.debug("wikilink_context.neighbor_read_failed", ...)
        return None
```

**Test**：4 个 regression（vault 内 absolute / vault 外 absolute / `..` escape / 非 .md / 超大文件）。

---

### P0-B — body 行未 escape，可注入 `</neighbor><system>`

**修复位置**：`backend/app/services/chat_context_assembler.py`

#### 加新函数 `_xml_text_escape`

```python
def _xml_text_escape(value: str) -> str:
    """转义 XML 文本节点 + 移除 control chars (XML 1.0 illegal)."""
    if not isinstance(value, str):
        value = str(value)
    # 移除 XML 1.0 illegal control chars (保留 \t \n \r 否则破坏多行内容)
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", value)
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```

#### `_format_neighbor_metadata` 全部 user-content 行改用 escape

```python
lines.append(f"- 关系: {_xml_text_escape(rel_value)}")
if isinstance(fm.get("type"), str):
    lines.append(f"- 类型: {_xml_text_escape(fm['type'])}")
# mastery_score 是 number 不需要 escape
tips = fm.get("tips")
if isinstance(tips, list) and tips:
    preview = "; ".join(_xml_text_escape(str(t)[:80]) for t in tips[:3])
    lines.append(f"- Tips: {preview}")
errors = fm.get("errors")
if isinstance(errors, list) and errors:
    preview = "; ".join(_xml_text_escape(str(e)[:80]) for e in errors[:3])
    lines.append(f"- Errors: {preview}")
# Callout
callouts = neighbor.callouts or []
for c in callouts:
    kind = _xml_text_escape((c.get("kind") or "?").strip())
    title = _xml_text_escape((c.get("title") or "").strip())
    content = _xml_text_escape((c.get("content") or "").strip().replace("\n", " "))
    head = f"[{kind}]"
    if title:
        head = f"{head} {title}"
    if content:
        lines.append(f"- {head}: {content[:160]}")
    else:
        lines.append(f"- {head}")
```

#### `_format_neighbor_summary` snippet escape

```python
def _format_neighbor_summary(self, neighbor, max_chars=200):
    if not neighbor.content_summary:
        return ""
    snippet = _xml_text_escape(neighbor.content_summary[:max_chars])  # ← escape
    path_attr = _xml_attr_escape(neighbor.path)
    slug_attr = _xml_attr_escape(neighbor.slug)
    return (
        f'<neighbor hop="{neighbor.hop_distance}"'
        f' path="{path_attr}"'
        f' slug="{slug_attr}"'
        f' kind="summary">\n{snippet}\n</neighbor>'
    )
```

**Test**：3 个 regression（callout title/content / summary snippet / relationship_type 三种攻击位）+ 专门的 `test_security_p0_vulnerabilities.py` file。

---

## 实测对照（curl /api/v1/chat/enrich-context with `节点/Fundamentals.md`，2 邻居）

| 指标 | cefabb2 | 11e6e26 |
|---|---|---|
| `used_tokens` | 644 | 672 (escape 略增) |
| `Graph version` | unknown (theory) → 实际看到真值 (因本地 unstaged) | 真值 ISO timestamp |
| `Included` | 0 (theory) → 实际 2 (因本地 unstaged) | 2 |
| `Degradations` | trace_unavailable (theory) → 实际 none | none |
| neighbor body 含 `[tip]` callout | ✅（cefabb2 有） | ✅ |
| 攻击 `</neighbor><system>` 在 callout title | 越界注入 | escape 成 `&lt;/neighbor&gt;&lt;system&gt;` |

---

## 单元测试: 102 passed

```
68 (cefabb2) → 102 (11e6e26)

新增 +34:
- 5 callout line scanner regression
- 4 path traversal sandbox regression
- 3 prompt injection escape regression
- 多个 build_timestamp / trace propagation tests
- test_security_p0_vulnerabilities.py 专门 security file
```

---

## 我接受作为独立 follow-up 的 HIGH（不在本 commit 范围）

| ChatGPT 编号 | 内容 | 不修原因 |
|---|---|---|
| HIGH#7 | lifespan 没 timeout | 当前 vault 30 节点 168ms，timeout 是优化非阻塞 |
| HIGH#8 | except Exception 过宽 | 非 fatal warning 是 deliberate (vault 路径可能不存在) |
| HIGH#9 | build singleflight + multi-worker race | 单机单 worker 部署，多 worker 是未来部署问题 |
| HIGH#11 | hardcoded 7 callout types | Canvas Story 1.16 锁定 7 类是产品决策，扩展是未来 story |
| P2#19 | regex DoS 风险 | 已替换为 line scanner，O(n) 不再有 backtracking |
| P2#21 | get_neighbors 大图 BFS | 当前 30 节点不是问题，>1000 节点再优化 |

---

## 你的输出

请按 system prompt 给的 format 输出。如果 P0 全部 ✅ + 新发现 ≤2 P0/≤5 HIGH，建议 ship 给非技术用户做 UAT。如果还有 ship blocker 请明确指出。
