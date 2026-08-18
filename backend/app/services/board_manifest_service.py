"""RAG-S2.5 (2026-08-10): Board Manifest — 白板结构读模型 (structure read-model).

阶段 2.5 立足点: 一次调用完整回答「白板怎么拆的」(成员 + 派生原因 + 掌握度),
替代 Claude 侧几十次 Grep/Read 拼图。与阶段 2 语义检索的本质区别: 语义检索
允许近似, 结构检索是**完整性契约** (金集 P=R=1.00 硬门槛)。

架构约定 (计划 RAG-S2.5-2026-08-10, 用户 2026-08-10 裁定):
  - 数据源 = frontmatter 直读 (source_board 为真相源); Neo4j 投影修复记 backlog。
    数据源抽象成 Protocol, 未来切换不动读模型主体。
  - node_id/board_id = 文件 basename (1.5 稳定 ID 后升级, 见 id_stability 常量)。
  - 本模块返回**全量 superset dict** (含 study 级字段与 exam 禁项原料)。
    泄漏控制不在这里: serve 时统一过 app/models/board_manifest.py 的
    Pydantic 视图投影 (exam 禁项 = 模型结构性缺字段, 白名单唯一控制点)。
  - 正文只参与两个判定后即丢弃: _compute_is_stub (占位) 与 ## Concepts 窄解析
    (差集告警)。正文内容绝不进入返回值 (内容是 read_note 的职责)。
  - JSON 快照 = scan_vault 全量 state 原样序列化, 落 .claude/cache/ (RAG 黑名单
    双覆盖 + 非 .md 双保险)。live 失败 → 快照 (degraded) → 空壳 error 诚实三态。

掌握度/选点数学: 与 canvas-vault/.claude/scripts/decay_beta.py 单一真相源
数值等价 (契约测试 sys.path import 真相源做 1e-9 锁, 禁止漂移)。三态兼容
语义对齐 scripts/daily_review_pick.py (mastery_a/b → 仅旧分 → 无字段先验)。
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import frontmatter
import yaml

logger = logging.getLogger(__name__)

NODE_DIR = "节点"
BOARD_DIR = "原白板"
EXAM_DIR = "检验白板"

#: 快照相对路径 (计划 T2): .claude 在 VAULT_INDEX_SKIP_DIRS + config RAG 黑名单
#: 双覆盖, .json 非 .md 双保险 — 不新增 SKIP_DIRS 条目
SNAPSHOT_REL = Path(".claude") / "cache" / "board-manifest" / "manifest-v1.json"

#: 顶层诚实信号常量 (计划 T2 契约字段)
ANNOTATION_TRUST = "untrusted_user_data"
ID_STABILITY = "basename_v1_will_upgrade_in_1_5"

#: 与 start-exam-board SKILL / daily_review_pick.py 同一条占位符规则
PLACEHOLDER = "你的 1-2 句精准定义"

#: score 量纲申报 (RAG-S2.6, 2.5 收尾 backlog ①: 裸 score 被消费侧误读成满分制)。
#: 唯一写侧真相源 = 检验白板 frontmatter `questions[].score_dims.score_scale`
#: (vault 现址已有, 2.6 写侧一行不改)。缺字段时按现行评分口径推定并**显式**
#: 标 `[推定]` — DD-13 名实一致, 不把推断说成声明。
SCORE_SCALE_DEFAULT = "1-4 (1=最低) [推定]"
SCORE_SCALE_UNKNOWN = "未知量纲 [推定]"
SCORE_SCALE_MAX = 40

#: ⛔ 量纲必须**整串**长成「数字 区间符 数字 [(≤16 字说明)]」(如 `1-4 (1=最低)`)。
#: 2.5 独立审查的 3 个 HIGH 全部是自由文本回显通道 (orphans.reason /
#: parse_errors / source_board_raw), 新字段不得开第四条。
#:
#: ⛔⛔ 必须配 fullmatch 用, 且 ⛔ 禁止在两端留 `\s*`:
#: RAG-S2.6 独立审查 HIGH-1 实测 —— 首版写的是 `.match()` 且正则无尾锚,
#: 于是 `1-4 反例 diag(-1,-1) 行列式为正但非正定` 整串原样透出 (那正是
#: G6 金集的禁串之一, 被 errors/tips 通道挡住却从这里走了出去);
#: `\s` 还会吃掉 \r\n, 让 `1-4\r\n> [!note] 答案` 这类换行注入蒙混过关。
#: 内部间隔一律用 `[ ]` 不用 `\s`。
_SCORE_SCALE_SHAPE = re.compile(
    r"\d{1,3}(?:\.\d{1,3})?[ ]*[-–—~〜至到][ ]*\d{1,3}(?:\.\d{1,3})?"
    r"(?:[ ]*[(（][^()（）\n\r\t]{0,16}[)）])?"
)

# ── 衰减 Beta 常量与函数 (真相源: canvas-vault/.claude/scripts/decay_beta.py) ──
# ⛔ 禁止改动数值语义: tests/regression/test_board_manifest_contracts.py 以
# sys.path import 真相源逐点断言 1e-9 等价。backend 不直接 import vault 脚本
# (vault 在容器里是数据卷不是代码), 契约测试代替共享库钉死等价性。

PRIOR_A = 0.9
PRIOR_B = 2.1
GAMMA_DAILY = 0.99
BETA_EXPLORE = 1.0


def _beta_mu(a: float, b: float) -> float:
    return a / (a + b)


def _beta_sigma(a: float, b: float) -> float:
    n = a + b
    return math.sqrt(a * b / (n * n * (n + 1.0)))


def _beta_effective(a: float, b: float, days_idle: float) -> tuple[float, float]:
    a, b = float(a), float(b)
    if a <= 0.0 or b <= 0.0:
        raise ValueError(f"Beta 参数必须为正: a={a}, b={b}")
    f = GAMMA_DAILY ** max(0.0, float(days_idle))
    f = max(f, 1e-150)
    return a * f, b * f


def _beta_pick_score(a: float, b: float) -> float:
    return _beta_mu(a, b) - BETA_EXPLORE * _beta_sigma(a, b)


def _beta_from_legacy(mastery_score: float, pseudo_n: float = 3.0) -> tuple[float, float]:
    m = max(0.0, min(1.0, float(mastery_score)))
    return max(0.05, m * pseudo_n), max(0.05, (1.0 - m) * pseudo_n)


# ── 基础解析 helpers ──

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
#: ## Concepts 窄解析: 只认行首 `- [[...]]` (计划 T1: ≤30 行窄解析器)
_CONCEPT_LINE_RE = re.compile(r"^\s*-\s*\[\[([^\]]+)\]\]", re.M)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_EXAM_QUESTION_RE = re.compile(r"^>\s*\[!exam_question\][+-]?\s*(\S+)", re.M)


def resolve_node_id(raw: Any) -> str:
    """'[[节点/x]]' / '[[y|别名]]' / '[[x#小节]]' / 'x.md' → basename。

    对齐 canvas_projection_sync._resolve_node_id, 另剥 Obsidian #heading/#^block
    锚点 (Code-Review M6: 带锚点的 source_board 不得判成假孤儿)。
    """
    text = str(raw or "")
    m = _WIKILINK_RE.search(text)
    inner = m.group(1) if m else text
    inner = inner.split("|", 1)[0]
    inner = inner.split("#", 1)[0]
    return inner.split("/")[-1].strip().removesuffix(".md")


def validate_path_component(component: str) -> str:
    """board_id/node_id 输入护栏: 拒 /、\\、..、NUL (计划 T1 路径穿越校验)。"""
    if not component or "/" in component or "\\" in component or ".." in component or "\x00" in component:
        raise ValueError(f"非法路径成分: {component!r}")
    return component


def _aware_dt(value: Any) -> datetime | None:
    """str/datetime/date → tz-aware datetime; 解析失败返回 None (调用方上报)。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(value: Any) -> str | None:
    """frontmatter 里的日期字段序列化成 ISO 字符串 (原样保留字符串)。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(value)


def _num(value: Any) -> float | None:
    """untrusted 标量 → 有限浮点数, 否则 None。

    ⛔ inf/nan 必须挡在这里 (RAG-S2.6 审查 HIGH-2): YAML 的 `.inf` / `.nan` /
    `1e400` 会一路穿到 pick_score=nan, 而 nan 的比较恒 False 让 Timsort 保持
    输入序 —— 文件名排最前的节点静默吃掉 pick_rank=1, 且 json.dumps 吐出裸
    `NaN` (非法 JSON, 严格解析器直接崩)。
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return num if math.isfinite(num) else None


def _json_safe(value: Any) -> Any:
    """透传字段深度清洗: YAML 解析出的 datetime/date 等对象 → JSON 原生类型。

    tips/errors/error_candidates 是任意深度用户数据 (live 实测 added_at/
    created_at 是 datetime 对象), 不清洗则快照 json.dumps 直接 TypeError。
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _safe_err(e: Exception) -> str:
    """解析异常 → 去内容化错误串 (Code-Review H2/M5)。

    ⛔ 禁用 str(e): 纯 Python yaml loader 的 MarkedYAMLError 会引用出错行
    **原文** (含 correction 等禁项文本), parse_errors 在 exam 视图必带 —
    只存异常类型名 + 行列号, 内容一律不回显。
    """
    mark = getattr(e, "problem_mark", None)
    loc = f" @ line {mark.line + 1}" if mark is not None else ""
    return f"{type(e).__name__}{loc}"


def _bounded_str(value: Any, limit: int) -> str | None:
    """untrusted frontmatter 标量 → 截断字符串 (Code-Review H3/L9: 类型归一
    防单字段 ValidationError 炸整个端点 + 信封字段统一硬截断)。"""
    if value is None:
        return None
    return str(value)[:limit]


# ── 数据源抽象 (计划: manifest 内部抽象数据源接口, 便于未来切 Neo4j 投影) ──


class ManifestDataSource(Protocol):
    def list_boards(self) -> list[Path]: ...

    def list_node_files(self) -> list[Path]: ...

    def list_exam_boards(self) -> list[Path]: ...

    def load_frontmatter(self, path: Path) -> tuple[dict[str, Any], str]: ...


class FrontmatterDataSource:
    """唯一实现: vault 目录直读 (节点/ 原白板/ 检验白板/ 非递归 *.md)。"""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)

    def _glob(self, subdir: str) -> list[Path]:
        d = self.base_path / subdir
        if not d.is_dir():
            return []
        return sorted(p for p in d.glob("*.md") if p.is_file())

    def list_boards(self) -> list[Path]:
        return self._glob(BOARD_DIR)

    def list_node_files(self) -> list[Path]:
        return self._glob(NODE_DIR)

    def list_exam_boards(self) -> list[Path]:
        return self._glob(EXAM_DIR)

    def load_frontmatter(self, path: Path) -> tuple[dict[str, Any], str]:
        post = frontmatter.load(str(path))
        return dict(post.metadata or {}), post.content or ""


# ── 判定与抽取 ──


def _compute_is_stub(body: str) -> bool:
    """占位模板判定。正文只在本函数边界内使用 (HARD-ISO 实现级隔离点)。"""
    return PLACEHOLDER in body


#: 同步脚本写的托管块边界 (canvas-vault/.claude/scripts/sync_board_concepts.py)
_AUTOGEN_BEGIN_RE = re.compile(r"^\s*<!--\s*AUTO-GENERATED by \.claude/scripts/sync_board_concepts\.py")
_AUTOGEN_END_RE = re.compile(r"^\s*<!--\s*/AUTO-GENERATED")


def _autogen_span(body: str) -> tuple[int, int] | None:
    """`## Concepts` 段内托管块的行区间 (BEGIN, END)，无则 None。"""
    lines = body.splitlines()
    begin = next((i for i, ln in enumerate(lines) if _AUTOGEN_BEGIN_RE.match(ln)), None)
    if begin is None:
        return None
    end = next((i for i in range(begin + 1, len(lines)) if _AUTOGEN_END_RE.match(lines[i])), None)
    return (begin, end) if end is not None else None


def _parse_concepts_section(body: str) -> list[str]:
    """## Concepts 窄解析: 剥 HTML 注释后, 只认 `- [[...]]` 行, 返回归一 node_id。

    ⛔ RAG-S2.6 第 3 轮审查 FIX-8「三把锁口径统一」: 同一批行有三个写者 ——
    同步脚本(删/留)、plugin recountBoardConcepts(数进 doc_count)、本函数(做差集)。
    脚本改成白名单收编后会**保留**段内的非成员游离行(如 `- [[教材第三章]]`),
    若本函数仍全段扫描, 那些行会被误报成 `concepts_only` 幽灵链接。
    ⇒ 有托管块时**只认块内**; 无块(迁移前/手工板)才回落全段扫描。
    """
    span = _autogen_span(body)
    if span is not None:
        begin, end = span
        inner = "\n".join(body.splitlines()[begin + 1 : end])
        return [resolve_node_id(f"[[{m.group(1)}]]") for m in _CONCEPT_LINE_RE.finditer(inner)]

    text = _HTML_COMMENT_RE.sub("", body)
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        if re.match(r"^##\s+Concepts\s*$", line):
            in_section = True
            continue
        if in_section and re.match(r"^##[^#]", line):
            break
        if in_section:
            m = _CONCEPT_LINE_RE.match(line)
            if m:
                collected.append(resolve_node_id(f"[[{m.group(1)}]]"))
    return collected


def _extract_question_digests(body: str, limit: int = 160) -> dict[str, str]:
    """检验白板正文 [!exam_question] callout → {qid: 题面摘句 ≤limit 字}。

    题面不在 frontmatter questions[] 里 (那里只有评分元数据), 只能从正文
    callout 提取。摘句是 exam 视图白名单槽位, 硬截断由这里保证。
    """
    digests: dict[str, str] = {}
    lines = body.splitlines()
    current_qid: str | None = None
    buf: list[str] = []

    def _flush() -> None:
        nonlocal current_qid, buf
        if current_qid is not None:
            text = " ".join(s for s in buf if s)
            text = re.sub(r"[*_`$]+", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            digests[current_qid] = text[:limit]
        current_qid, buf = None, []

    for line in lines:
        m = _EXAM_QUESTION_RE.match(line)
        if m:
            _flush()
            current_qid = m.group(1).lower()
            continue
        if current_qid is not None:
            if re.match(r"^>\s*\[!", line):
                # Code-Review M4: 相邻/嵌套 callout ([!feedback] 评分反馈可含
                # 正确答案, [!hint]- 未必已曝光) 是摘句边界 — 立即终止收集,
                # 绝不吸入题面之外的 callout 内容
                _flush()
            elif line.startswith(">"):
                buf.append(line.lstrip(">").strip())
            else:
                _flush()
    _flush()
    return digests


def _score_scale(question: dict[str, Any]) -> str:
    """questions[].score_dims.score_scale → 量纲申报串 (形状白名单 + 40 字硬截断)。

    三态 (全部定长, 无自由文本通道):
      写侧有且**整串**形状合法 → 原样 (≤40)
      写侧无                   → SCORE_SCALE_DEFAULT (带 `[推定]` 后缀)
      写侧有但形状不合法        → SCORE_SCALE_UNKNOWN (可见地降级, 不静默透传)

    ⛔ 先验形状**再**截断 (不是先截后验): 先截 40 会把超长投毒串削成
    「看起来合法」的半个 token 放行 (RAG-S2.6 审查 HIGH-1 同批修)。
    合法量纲本就远短于 40, 超长即判非法。
    """
    dims = question.get("score_dims")
    if not isinstance(dims, dict):
        return SCORE_SCALE_DEFAULT
    raw = dims.get("score_scale")
    if raw is None:
        return SCORE_SCALE_DEFAULT
    text = str(raw).strip()
    if not text:
        return SCORE_SCALE_DEFAULT
    if len(text) > SCORE_SCALE_MAX or not _SCORE_SCALE_SHAPE.fullmatch(text):
        return SCORE_SCALE_UNKNOWN
    return text


def _normalize_mastery(fm: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """mastery 四态归一化 → ({score,a,b,source}, error)。

    四态 (计划 T1, 语义对齐 daily_review_pick.scan_nodes 三态兼容):
      beta      — mastery_a + mastery_b 齐 (富节点)
      score_only — 仅 mastery_score (标准 ai_linked_doc)
      legacy_v2 — `mastery:` / `mastery_level:` (v2 遗留)
      absent    — 全无 (种子未考, score=null)
    """
    a = _num(fm.get("mastery_a"))
    b = _num(fm.get("mastery_b"))
    score = _num(fm.get("mastery_score"))
    legacy = next(
        (v for k in ("mastery", "mastery_level") if (v := _num(fm.get(k))) is not None),
        None,
    )
    # ⛔ 字段在但不可用 (非数字 / inf / nan / 1e400) 必须显式上报, 不静默降档:
    # 静默降档会让投毒节点悄悄换一条计分路径, 而 parse_errors 空空如也
    # (RAG-S2.6 审查 HIGH-2)。⛔ 错误文案不回显原值 — 那是 2.5 H2 的通道。
    if (fm.get("mastery_a") is not None and a is None) or (fm.get("mastery_b") is not None and b is None):
        return {"score": None, "a": None, "b": None, "source": "absent"}, (
            "mastery_a/b 存在但非有限数值 (非数字 / inf / nan), 按未评估处理"
        )
    if a is not None and b is not None:
        err = None
        if a <= 0.0 or b <= 0.0:
            err = f"mastery_a/b 非正 (a={a}, b={b}), 数据损坏"
        mu = _beta_mu(a, b) if err is None else None
        return {"score": score if score is not None else mu, "a": a, "b": b, "source": "beta"}, err
    if score is not None:
        return {"score": score, "a": None, "b": None, "source": "score_only"}, None
    if legacy is not None:
        return {"score": legacy, "a": None, "b": None, "source": "legacy_v2"}, None
    return {"score": None, "a": None, "b": None, "source": "absent"}, None


def _pick_hint(
    mastery: dict[str, Any], last_examined_dt: datetime | None, now: datetime
) -> tuple[dict[str, Any] | None, str | None]:
    """选点提示 = μ−σ 含闲置回升 (读时时效, 不写回)。

    (a,b) 解析与 daily_review_pick 同规则: beta 直取 / 旧分 from_legacy 低置信
    继承 / absent 用先验 (从未考 σ 大自动优先)。
    """
    source = mastery["source"]
    if source == "beta":
        a, b = mastery["a"], mastery["b"]
    elif source in ("score_only", "legacy_v2"):
        a, b = _beta_from_legacy(mastery["score"])
    else:
        a, b = PRIOR_A, PRIOR_B

    days_idle: float | None = None
    if last_examined_dt is not None:
        days_idle = max(0.0, (now - last_examined_dt).total_seconds() / 86400.0)
    try:
        a_eff, b_eff = _beta_effective(a, b, days_idle or 0.0)
        return {
            "mu": _beta_mu(a_eff, b_eff),
            "sigma": _beta_sigma(a_eff, b_eff),
            "pick_score": _beta_pick_score(a_eff, b_eff),
            "days_idle": days_idle,
        }, None
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        return None, f"pick_hint 计算失败: {e}"


def _node_relation(fm: dict[str, Any]) -> dict[str, Any] | None:
    """派生关系: relationships[0] 优先, 退 derived-from 单链。

    ⚠️ 字段同名陷阱 (计划已验证事实 #5): relationships[].description 是
    派生原因 (exam 可暴露白名单槽位, 500 字硬截断);
    error_candidates[].misconception/correction 是禁项, 不经过本函数。
    """
    rels = fm.get("relationships")
    if isinstance(rels, list):
        for rel in rels:
            if not isinstance(rel, dict):
                continue
            reason = str(rel.get("description") or "").strip() or None
            return {
                "type": str(rel.get("type") or "unknown"),
                "target_node_id": resolve_node_id(rel.get("target")),
                "derived_reason": reason[:500] if reason else None,
                "derived_at": _iso(rel.get("derived_at")),
            }
    derived_from = fm.get("derived-from") or fm.get("derived_from")
    if derived_from:
        return {
            "type": "derived_from",
            "target_node_id": resolve_node_id(derived_from),
            "derived_reason": None,
            "derived_at": None,
        }
    return None


def _node_role(fm: dict[str, Any]) -> str:
    """seed/derived/unknown: 有派生痕迹 = derived; 有归属无派生痕迹 = seed。"""
    if (
        fm.get("relationships")
        or fm.get("derived-from")
        or fm.get("derived_from")
        or fm.get("created_from") == "ai_linked_doc"
    ):
        return "derived"
    if fm.get("source_board"):
        return "seed"
    return "unknown"


def compute_generation(base_path: Path) -> str:
    """freshness generation = sha256[:12](sorted relpath|mtime_ns|size, 三目录)。

    任何成员文件的增删改 (含 mtime touch) 都变更 generation → 快照重写判据。
    """
    base = Path(base_path)
    entries: list[str] = []
    for subdir in (NODE_DIR, BOARD_DIR, EXAM_DIR):
        d = base / subdir
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            try:
                st = p.stat()
            except OSError:
                continue
            entries.append(f"{subdir}/{p.name}|{st.st_mtime_ns}|{st.st_size}")
    payload = "\n".join(sorted(entries)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


# ── 全量扫描 (快照序列化单位) ──


def scan_vault(
    base_path: Path | str,
    now: datetime | None = None,
    include_exam_history: bool = True,
    data_source: ManifestDataSource | None = None,
) -> dict[str, Any]:
    """全量扫描 → full state: 板/成员/孤儿/检验历史/解析错误/freshness。

    - vault 结构缺失 (节点/ 或 原白板/ 目录不在) → FileNotFoundError,
      由 serve_manifest 触发快照兜底。
    - 单文件解析失败只进 parse_errors, 不熄火不兜底 (OBS-4 不静默)。
    - 返回值 JSON-safe (日期已 _iso 字符串化), 可原样序列化为快照。
    """
    base = Path(base_path)
    now = now or datetime.now(timezone.utc)
    if not (base / NODE_DIR).is_dir() or not (base / BOARD_DIR).is_dir():
        raise FileNotFoundError(f"vault 结构缺失 (需 {NODE_DIR}/ 与 {BOARD_DIR}/): {base}")
    ds = data_source or FrontmatterDataSource(base)
    parse_errors: list[dict[str, str]] = []

    # 1. 板枚举 (原白板/*.md)
    boards: dict[str, dict[str, Any]] = {}
    for path in ds.list_boards():
        stem = path.stem
        try:
            fm, body = ds.load_frontmatter(path)
        except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as e:
            parse_errors.append({"path": f"{BOARD_DIR}/{path.name}", "error": _safe_err(e)})
            continue
        # Code-Review H3: untrusted 标量必须类型归一 — `doc_count: 大约五个`
        # 不得让投影 ValidationError 500 整个端点 (含列板模式)
        board_name = _bounded_str(fm.get("board_name"), 120) or stem
        doc_count = _num(fm.get("doc_count"))
        boards[stem] = {
            "board_id": stem,
            "board_name": board_name,
            "board_name_mismatch": board_name != stem,
            "doc_count_declared": int(doc_count) if doc_count is not None else None,
            "concepts_listed": _parse_concepts_section(body),
            "members": [],
        }
    # Code-Review M6: wikilink 归属匹配大小写不敏感 (macOS 文件系统同语义)
    boards_ci = {k.casefold(): k for k in boards}

    # 2. 节点池扫描 (节点/*.md) → 按 source_board 分组; 无归属/未知板 → orphans
    orphans: list[dict[str, Any]] = []
    node_stems: list[str] = []
    for path in ds.list_node_files():
        stem = path.stem
        node_stems.append(stem)
        try:
            fm, body = ds.load_frontmatter(path)
        except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as e:
            parse_errors.append({"path": f"{NODE_DIR}/{path.name}", "error": _safe_err(e)})
            continue

        mastery, mastery_err = _normalize_mastery(fm)
        if mastery_err:
            parse_errors.append({"path": f"{NODE_DIR}/{path.name}", "error": mastery_err})

        last_exam_raw = fm.get("last_examined")
        last_exam_dt = _aware_dt(last_exam_raw)
        if last_exam_raw is not None and last_exam_dt is None:
            # Code-Review H2: 原值只回显 repr 前 80 字 — parse_errors 在 exam
            # 视图必带, 无界回显 = 第三条自由文本泄漏通道
            parse_errors.append(
                {
                    "path": f"{NODE_DIR}/{path.name}",
                    "error": f"last_examined 无法解析, 按从未考: {repr(last_exam_raw)[:80]}",
                }
            )

        hint, hint_err = (None, None)
        if mastery_err is None:
            hint, hint_err = _pick_hint(mastery, last_exam_dt, now)
        if hint_err:
            parse_errors.append({"path": f"{NODE_DIR}/{path.name}", "error": hint_err})

        calibration_log = fm.get("calibration_log")
        entry: dict[str, Any] = {
            "node_id": stem,
            "exists": True,
            "role": _node_role(fm),
            "is_stub": _compute_is_stub(body),
            "relation": _node_relation(fm),
            "mastery": mastery,
            "attempt_count": (int(v) if (v := _num(fm.get("attempt_count"))) is not None else None),
            "last_examined": _iso(last_exam_raw),
            "pick_hint": hint,
            "past_question_digests": [],
            # study-only 字段 (exam 视图投影时结构性丢弃); 标量全部 _bounded_str
            # 类型归一 (Code-Review H3: `title: 2026` 不得炸投影)
            "title": _bounded_str(fm.get("title"), 200),
            "aliases": [str(x)[:120] for x in fm.get("aliases") or [] if x is not None],
            "created_at": _iso(fm.get("created_at")),
            "created_from": _bounded_str(fm.get("created_from"), 80),
            "source_note": (resolve_node_id(fm.get("source_note")) if fm.get("source_note") else None),
            "tips": [_json_safe(t) for t in fm.get("tips") or [] if isinstance(t, dict)],
            "errors": [_json_safe(e) for e in fm.get("errors") or [] if isinstance(e, dict)],
            "error_candidates": [_json_safe(c) for c in fm.get("error_candidates") or [] if isinstance(c, dict)],
            "next_review": _iso(fm.get("next_review")),
            "calibration_count": (len(calibration_log) if isinstance(calibration_log, list) else 0),
        }

        raw_board = fm.get("source_board")
        if not raw_board:
            orphans.append({"node_id": stem, "reason": "无 source_board", "source_board_raw": None})
            continue
        target_board = boards_ci.get(resolve_node_id(raw_board).casefold())
        if target_board is None:
            # Code-Review H1: reason 只用定长枚举文案, 不插值 untrusted 值;
            # source_board_raw 硬截断 120 — orphans 在 exam 视图必带,
            # 不得成为第三条自由文本泄漏通道
            orphans.append(
                {
                    "node_id": stem,
                    "reason": "source_board 指向不存在的白板",
                    "source_board_raw": _bounded_str(raw_board, 120),
                }
            )
            continue
        boards[target_board]["members"].append(entry)

    # 3. 检验白板扫描 → 板级历史 + 节点级题目摘句
    exam_history: list[dict[str, Any]] = []
    if include_exam_history:
        for path in ds.list_exam_boards():
            try:
                fm, body = ds.load_frontmatter(path)
            except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as e:
                parse_errors.append({"path": f"{EXAM_DIR}/{path.name}", "error": _safe_err(e)})
                continue
            linked_board = boards_ci.get(resolve_node_id(fm.get("source_board")).casefold())
            questions = [q for q in fm.get("questions") or [] if isinstance(q, dict)]
            digests = _extract_question_digests(body)
            exam_history.append(
                {
                    "exam_board_id": path.stem,
                    "board_id": linked_board,
                    "created_at": _iso(fm.get("created_at")),
                    "status": _bounded_str(fm.get("status"), 40),
                    "selected_node": _bounded_str(fm.get("selected_node"), 200),
                    "question_count": len(questions),
                }
            )
            for q in questions:
                concept = resolve_node_id(q.get("concept") or q.get("concept_path"))
                qid = str(q.get("id") or "").lower()[:40]
                digest_entry = {
                    "exam_board_id": path.stem,
                    "qid": qid or None,
                    "asked_at": _iso(fm.get("created_at")),
                    "score": _num(q.get("score")),
                    "score_scale": _score_scale(q),
                    "self_confidence": _bounded_str(q.get("self_confidence"), 40),
                    "digest": digests.get(qid) or None,
                }
                if linked_board in boards:
                    for member in boards[linked_board]["members"]:
                        if member["node_id"] == concept:
                            member["past_question_digests"].append(digest_entry)
        for b in boards.values():
            for member in b["members"]:
                member["past_question_digests"].sort(key=lambda d: d["asked_at"] or "")
        exam_history.sort(key=lambda e: e["created_at"] or "")

    return {
        "freshness": {
            "generated_at": now.isoformat(),
            "generation": compute_generation(base),
            "lag_seconds": 0.0,
            "stale": False,
        },
        "boards": boards,
        "node_stems": node_stems,
        "orphans": orphans,
        "exam_history": exam_history,
        "parse_errors": parse_errors,
    }


# ── 请求裁切 (live 与快照共用同一条路径 → 泄漏控制点唯一) ──


def _assign_pick_ranks(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """板内**可考察候选**秩 → 写进 pick_hint.pick_rank (RAG-S2.6)。

    排序键 (pick_score, node_id): pick_score 是 μ−σ 含闲置折旧的选点分, 越低
    越该考; node_id 是并列时的确定性 tie-break — 2.5 前 skill 靠「## Concepts
    段靠前」破并列, manifest 是文件名序, 必须显式给规则。

    ⛔ 只给 **is_stub=false 且 pick_hint 可算** 的成员赋秩。占位节点本就不可考
    (start-exam-board 历来跳过), 若让它占掉 rank=1, 消费侧「过滤占位后取
    rank==1」就会扑空。恒等式: 过滤 is_stub 后 rank==1 必然存在或全板皆占位。

    ⛔ 不改列表顺序 (nodes[] 契约恒为文件名序), 也不改写入参 dict —
    live 与快照两条路径都过这里, 就地改会污染 full/snapshot state。

    在 _carve 而非 scan 阶段赋秩: 2.6 之前写下的历史快照没有本字段, 放在
    serve 侧计算才能让降级态也拿到秩 (否则 degraded 时 rank 全 null)。
    """

    def _rankable(m: dict[str, Any]) -> bool:
        """⛔ 排序键必须是**有限数值**才准入 (RAG-S2.6 审查 HIGH-2 + LOW-1)。

        两条独立理由:
          ① nan 的比较恒 False → Timsort 保持输入序 → 投毒节点静默拿走 rank=1
          ② 历史/损坏快照里 pick_hint 可能缺 pick_score 或是字符串, 裸取会
             KeyError (被 API 层误映射成 404「白板不存在」) 或 TypeError (裸 500)
        """
        if m.get("is_stub"):
            return False
        hint = m.get("pick_hint")
        if not isinstance(hint, dict):
            return False
        score = hint.get("pick_score")
        return isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score)

    ranked = sorted(
        (m for m in members if _rankable(m)),
        key=lambda m: (m["pick_hint"]["pick_score"], m["node_id"]),
    )
    rank_by_id = {m["node_id"]: i for i, m in enumerate(ranked, start=1)}
    out: list[dict[str, Any]] = []
    for m in members:
        hint = m.get("pick_hint")
        if not isinstance(hint, dict):
            out.append(m)
            continue
        out.append({**m, "pick_hint": {**hint, "pick_rank": rank_by_id.get(m["node_id"])}})
    return out


def _carve(full: dict[str, Any], board_id: str | None, include_exam_history: bool) -> dict[str, Any]:
    """full state → 请求形状 dict。board_id 不存在抛 KeyError (API 层转 404)。"""
    boards: dict[str, dict[str, Any]] = full["boards"]
    exam_history = full["exam_history"] if include_exam_history else []
    result: dict[str, Any] = {
        "source": "live",
        "source_status": "ok",
        "freshness": dict(full["freshness"]),
        "degraded": False,
        "degraded_reason": None,
        "annotation_trust": ANNOTATION_TRUST,
        "id_stability": ID_STABILITY,
        "board": None,
        "boards": None,
        "nodes": [],
        "orphans": full["orphans"],
        "dual_source_gap": None,
        "exam_history": [],
        "parse_errors": full["parse_errors"],
    }

    if board_id is None:
        result["boards"] = [
            {
                "board_id": b["board_id"],
                "board_name": b["board_name"],
                "board_name_mismatch": b["board_name_mismatch"],
                "doc_count_declared": b["doc_count_declared"],
                "member_count_actual": len(b["members"]),
                # Code-Review L12: 计数恒用 full 历史 — include_exam_history=False
                # 裁掉的是列表, 不得把板的检验白板计数静默归零
                "exam_board_count": sum(1 for e in full["exam_history"] if e["board_id"] == b["board_id"]),
            }
            for b in boards.values()
        ]
        result["exam_history"] = exam_history
        return result

    if board_id not in boards:
        raise KeyError(f"白板不存在: {board_id}")

    b = boards[board_id]
    members = b["members"]
    if not include_exam_history:
        # 快照 full 恒含历史; 请求关掉时在裁切层剥离 (浅拷贝防止污染 full)
        members = [{**m, "past_question_digests": []} for m in members]
    members = _assign_pick_ranks(members)
    member_ids = {m["node_id"] for m in members}
    concepts = b["concepts_listed"]
    node_stems = set(full["node_stems"])
    result["board"] = {
        "board_id": b["board_id"],
        "board_name": b["board_name"],
        "board_name_mismatch": b["board_name_mismatch"],
        "doc_count_declared": b["doc_count_declared"],
        "member_count_actual": len(members),
    }
    result["nodes"] = members
    # 差集告警 (读侧只告警不改写; 写侧视图化留 2.6):
    #   concepts_only — 目录挂着但 frontmatter 没认领 (exists=false 即幽灵链接)
    #   frontmatter_only — frontmatter 认领但目录漏记
    result["dual_source_gap"] = {
        "concepts_only": [{"node_id": c, "exists": c in node_stems} for c in concepts if c not in member_ids],
        "frontmatter_only": sorted(member_ids - set(concepts)),
    }
    result["exam_history"] = [e for e in exam_history if e["board_id"] == board_id]
    return result


def build_manifest(
    base_path: Path | str,
    board_id: str | None = None,
    include_exam_history: bool = True,
    now: datetime | None = None,
    data_source: ManifestDataSource | None = None,
) -> dict[str, Any]:
    """live 单发构建 (无快照参与): scan + carve。

    board_id=None → 列板模式 (boards[] 摘要); 指定 board_id → 单板成员全量。
    非法 board_id 抛 ValueError (API 层转 422); 不存在抛 KeyError (转 404)。
    """
    if board_id is not None:
        board_id = validate_path_component(board_id)
    full = scan_vault(base_path, now=now, include_exam_history=include_exam_history, data_source=data_source)
    return _carve(full, board_id, include_exam_history)


# ── JSON 快照 (last known good, 不做 TTL 删除) ──


def snapshot_file(base_path: Path | str) -> Path:
    return Path(base_path) / SNAPSHOT_REL


#: E-2 (R11-BATCH2-2026-08-17): 快照禁写字段 — study 面自由文本原文。
#:
#: 为何只列三项就够: 金集 forbidden_keys 里的 misconception / correction /
#: raw_dialog_excerpt / evidence_turns / ai_reason 全部**嵌在**这三个容器内部
#: (见 :457 注释), 剔顶层即连根拔除。
#:
#: 为何不剔 title / aliases / source_note / calibration_count: 它们同在
#: forbidden_keys 但性质不同 —— 是「exam 视图不需要」而非「泄题」, exam 侧靠
#: models/board_manifest.py 的结构性缺字段隔离已足够。留在快照里, 降级态的
#: study 视图才不至于连标题都没有。
SNAPSHOT_STRIPPED_MEMBER_KEYS = ("tips", "errors", "error_candidates")


def _project_for_snapshot(full: dict[str, Any]) -> dict[str, Any]:
    """快照投影 (E-2 方案 A): 剔除 members 的泄题原文, 其余原样序列化。

    堵的洞: scan_vault 返回的是全量 superset (文件头 :11-13), 泄漏控制原本
    只在 serve 时的 Pydantic 视图投影上。快照落盘的是**投影前**的 state ——
    谁直接读 .claude/cache/board-manifest/manifest-v1.json 就绕过了整个控制点。

    ⛔ 必须深拷贝: :716 契约明示 live 与快照共用同一份 full state, 就地 pop
    会让同一次请求的 live 响应也跟着丢字段。

    降级态代价 (方案 A, 用户 2026-08-17 裁定时已知情): study 视图从快照恢复时
    这三项为空列表 —— models/board_manifest.py:122-124 三字段均
    default_factory=list, 缺字段不触发 ValidationError。exam 视图零影响。

    pick_rank 无需特意保留: :716-719 明示秩在 _carve (serve 侧) 计算, 快照本就
    不含该字段; 只要 pick_hint.pick_score 与 is_stub 还在, 降级态自会重算。
    """
    projected = copy.deepcopy(full)
    for board in (projected.get("boards") or {}).values():
        if not isinstance(board, dict):
            continue
        for member in board.get("members") or []:
            if isinstance(member, dict):
                for key in SNAPSHOT_STRIPPED_MEMBER_KEYS:
                    member.pop(key, None)
    return projected


def write_snapshot_if_changed(base_path: Path | str, full: dict[str, Any]) -> bool:
    """generation 变更才重写; tmp + os.replace 原子; 失败仅 warning 不影响 live。

    E-2: 落盘前过 _project_for_snapshot —— 投影放在本函数内部而非调用侧, 让
    「快照永不含泄题原文」成为函数级不变量, 未来新增调用方无需重复记得。
    """
    path = snapshot_file(base_path)
    try:
        if path.exists():
            try:
                prev = json.loads(path.read_text(encoding="utf-8"))
                if prev.get("freshness", {}).get("generation") == full["freshness"]["generation"]:
                    return False
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                pass  # 损坏快照 → 直接重写覆盖
        path.parent.mkdir(parents=True, exist_ok=True)
        # Code-Review L10: 唯一名 tmp 防跨进程写竞态 (宿主脚本与容器并跑时
        # 固定名 tmp 可把半成品发布为正式快照)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                # E-2: 投影放在 generation 比对之后 — 只有真要落盘时才付
                # deepcopy 成本, 未变更的常态路径已在上方 return False
                f.write(json.dumps(_project_for_snapshot(full), ensure_ascii=False))
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
        return True
    except (OSError, TypeError, ValueError) as e:
        # TypeError/ValueError: 序列化炸 (理应被 _json_safe 挡住, 双保险) —
        # 快照失败绝不拖垮 live 服务
        logger.warning("[manifest] 快照写入失败 (不影响 live 服务): %s", e)
        return False


#: 快照 schema 必备键 (Code-Review L11: 缺键快照会让 _carve KeyError 被误映射
#: 成 404「白板不存在」— 结构不全一律按快照不可用处理)
_SNAPSHOT_REQUIRED_KEYS = frozenset({"freshness", "boards", "node_stems", "orphans", "exam_history", "parse_errors"})


def load_snapshot(base_path: Path | str) -> dict[str, Any] | None:
    path = snapshot_file(base_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("[manifest] 快照不可用: %s", e)
        return None
    if not isinstance(data, dict) or not _SNAPSHOT_REQUIRED_KEYS <= set(data):
        logger.warning("[manifest] 快照 schema 不全, 按不可用处理: %s", path)
        return None
    return data


def serve_manifest(
    base_path: Path | str,
    board_id: str | None = None,
    include_exam_history: bool = True,
    stale_after_s: int = 86400,
    now: datetime | None = None,
) -> dict[str, Any]:
    """降级三态 (计划 T2, 诚实不假空成功):

      live ok       → source=live / source_status=ok (顺手 generation 变更才重写快照)
      live 失败+快照 → source=local_json / snapshot / degraded=true / lag+stale 标注
      快照也无      → source=local_json / error / nodes=[] (200 空壳, 显式报因)

    单节点解析失败**不**触发兜底 (进 parse_errors); 只有 vault 结构级不可达才降级。
    板不存在在 live 与快照两态同语义抛 KeyError (API 层转 404)。
    """
    if board_id is not None:
        board_id = validate_path_component(board_id)
    now = now or datetime.now(timezone.utc)

    try:
        # 快照必须全量 (含检验历史), include_exam_history 只影响本次裁切
        full = scan_vault(base_path, now=now, include_exam_history=True)
    except OSError as e:
        live_error = str(e)
    else:
        write_snapshot_if_changed(base_path, full)
        return _carve(full, board_id, include_exam_history)

    snap = load_snapshot(base_path)
    if snap is not None:
        result = _carve(snap, board_id, include_exam_history)
        gen_at = _aware_dt(snap.get("freshness", {}).get("generated_at"))
        lag = max(0.0, (now - gen_at).total_seconds()) if gen_at else None
        result["source"] = "local_json"
        result["source_status"] = "snapshot"
        result["degraded"] = True
        result["degraded_reason"] = f"live 扫描失败, 退快照: {live_error}"
        result["freshness"]["lag_seconds"] = round(lag, 1) if lag is not None else None
        result["freshness"]["stale"] = lag is None or lag > stale_after_s
        return result

    return {
        "source": "local_json",
        "source_status": "error",
        "freshness": None,
        "degraded": True,
        "degraded_reason": f"live 扫描失败且无可用快照: {live_error}",
        "annotation_trust": ANNOTATION_TRUST,
        "id_stability": ID_STABILITY,
        "board": None,
        "boards": None,
        "nodes": [],
        "orphans": [],
        "dual_source_gap": None,
        "exam_history": [],
        "parse_errors": [],
    }
