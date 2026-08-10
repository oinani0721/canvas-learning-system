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

掌握度/选点数学: 与 canvas-vault/.claude/scripts/decay_beta.py 单一真相源
数值等价 (契约测试 sys.path import 真相源做 1e-9 锁, 禁止漂移)。三态兼容
语义对齐 scripts/daily_review_pick.py (mastery_a/b → 仅旧分 → 无字段先验)。
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import frontmatter
import yaml

logger = logging.getLogger(__name__)

NODE_DIR = "节点"
BOARD_DIR = "原白板"
EXAM_DIR = "检验白板"

#: 顶层诚实信号常量 (计划 T2 契约字段)
ANNOTATION_TRUST = "untrusted_user_data"
ID_STABILITY = "basename_v1_will_upgrade_in_1_5"

#: 与 start-exam-board SKILL / daily_review_pick.py 同一条占位符规则
PLACEHOLDER = "你的 1-2 句精准定义"

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
    """'[[节点/x]]' / '[[y|别名]]' / 'x.md' → basename (canvas_projection_sync 同义)。"""
    text = str(raw or "")
    m = _WIKILINK_RE.search(text)
    inner = m.group(1) if m else text
    inner = inner.split("|", 1)[0]
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
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _parse_concepts_section(body: str) -> list[str]:
    """## Concepts 窄解析: 剥 HTML 注释后, 只认 `- [[...]]` 行, 返回归一 node_id。"""
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
            if line.startswith(">"):
                buf.append(line.lstrip(">").strip())
            else:
                _flush()
    _flush()
    return digests


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


# ── 主构建 ──


def build_manifest(
    base_path: Path | str,
    board_id: str | None = None,
    include_exam_history: bool = True,
    now: datetime | None = None,
    data_source: ManifestDataSource | None = None,
) -> dict[str, Any]:
    """构建全量 manifest superset dict (study 级, 未过视图投影)。

    board_id=None → 列板模式 (boards[] 摘要); 指定 board_id → 单板成员全量。
    单节点解析失败进 parse_errors 不熄火 (OBS-4 不静默); board_id 不存在抛
    KeyError (API 层转 404); 非法 board_id 抛 ValueError (API 层转 422)。
    """
    base = Path(base_path)
    now = now or datetime.now(timezone.utc)
    if board_id is not None:
        board_id = validate_path_component(board_id)
    ds = data_source or FrontmatterDataSource(base)
    parse_errors: list[dict[str, str]] = []

    # 1. 板枚举 (原白板/*.md)
    boards: dict[str, dict[str, Any]] = {}
    for path in ds.list_boards():
        stem = path.stem
        try:
            fm, body = ds.load_frontmatter(path)
        except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as e:
            parse_errors.append({"path": f"{BOARD_DIR}/{path.name}", "error": str(e)})
            continue
        board_name = str(fm.get("board_name") or stem)
        boards[stem] = {
            "board_id": stem,
            "board_name": board_name,
            "board_name_mismatch": board_name != stem,
            "doc_count_declared": fm.get("doc_count"),
            "concepts_listed": _parse_concepts_section(body),
            "members": [],
        }

    # 2. 节点池扫描 (节点/*.md) → 按 source_board 分组; 无归属/未知板 → orphans
    orphans: list[dict[str, Any]] = []
    node_stems: set[str] = set()
    for path in ds.list_node_files():
        stem = path.stem
        node_stems.add(stem)
        try:
            fm, body = ds.load_frontmatter(path)
        except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as e:
            parse_errors.append({"path": f"{NODE_DIR}/{path.name}", "error": str(e)})
            continue

        mastery, mastery_err = _normalize_mastery(fm)
        if mastery_err:
            parse_errors.append({"path": f"{NODE_DIR}/{path.name}", "error": mastery_err})

        last_exam_raw = fm.get("last_examined")
        last_exam_dt = _aware_dt(last_exam_raw)
        if last_exam_raw is not None and last_exam_dt is None:
            parse_errors.append(
                {
                    "path": f"{NODE_DIR}/{path.name}",
                    "error": f"last_examined 无法解析, 按从未考: {last_exam_raw!r}",
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
            # study-only 字段 (exam 视图投影时结构性丢弃)
            "title": fm.get("title"),
            "aliases": [str(x) for x in fm.get("aliases") or [] if x is not None],
            "created_at": _iso(fm.get("created_at")),
            "created_from": fm.get("created_from"),
            "source_note": (resolve_node_id(fm.get("source_note")) if fm.get("source_note") else None),
            "tips": [t for t in fm.get("tips") or [] if isinstance(t, dict)],
            "errors": [e for e in fm.get("errors") or [] if isinstance(e, dict)],
            "error_candidates": [c for c in fm.get("error_candidates") or [] if isinstance(c, dict)],
            "next_review": _iso(fm.get("next_review")),
            "calibration_count": (len(calibration_log) if isinstance(calibration_log, list) else 0),
        }

        raw_board = fm.get("source_board")
        if not raw_board:
            orphans.append({"node_id": stem, "reason": "无 source_board", "source_board_raw": None})
            continue
        target_board = resolve_node_id(raw_board)
        if target_board not in boards:
            orphans.append(
                {
                    "node_id": stem,
                    "reason": f"source_board 指向不存在的白板: {target_board}",
                    "source_board_raw": str(raw_board),
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
                parse_errors.append({"path": f"{EXAM_DIR}/{path.name}", "error": str(e)})
                continue
            linked_board = resolve_node_id(fm.get("source_board")) or None
            questions = [q for q in fm.get("questions") or [] if isinstance(q, dict)]
            digests = _extract_question_digests(body)
            exam_history.append(
                {
                    "exam_board_id": path.stem,
                    "board_id": linked_board,
                    "created_at": _iso(fm.get("created_at")),
                    "status": fm.get("status"),
                    "selected_node": fm.get("selected_node"),
                    "question_count": len(questions),
                }
            )
            for q in questions:
                concept = resolve_node_id(q.get("concept") or q.get("concept_path"))
                qid = str(q.get("id") or "").lower()
                digest_entry = {
                    "exam_board_id": path.stem,
                    "qid": qid or None,
                    "asked_at": _iso(fm.get("created_at")),
                    "score": _num(q.get("score")),
                    "self_confidence": (
                        str(q.get("self_confidence")) if q.get("self_confidence") is not None else None
                    ),
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

    # 4. 组装顶层 (freshness lag=0: live 现算现返回)
    result: dict[str, Any] = {
        "source": "live",
        "source_status": "ok",
        "freshness": {
            "generated_at": now.isoformat(),
            "generation": compute_generation(base),
            "lag_seconds": 0.0,
            "stale": False,
        },
        "degraded": False,
        "degraded_reason": None,
        "annotation_trust": ANNOTATION_TRUST,
        "id_stability": ID_STABILITY,
        "board": None,
        "boards": None,
        "nodes": [],
        "orphans": orphans,
        "dual_source_gap": None,
        "exam_history": [],
        "parse_errors": parse_errors,
    }

    if board_id is None:
        result["boards"] = [
            {
                "board_id": b["board_id"],
                "board_name": b["board_name"],
                "board_name_mismatch": b["board_name_mismatch"],
                "doc_count_declared": b["doc_count_declared"],
                "member_count_actual": len(b["members"]),
                "exam_board_count": sum(1 for e in exam_history if e["board_id"] == b["board_id"]),
            }
            for b in boards.values()
        ]
        result["exam_history"] = exam_history
        return result

    if board_id not in boards:
        raise KeyError(f"白板不存在: {board_id}")

    b = boards[board_id]
    members = b["members"]
    member_ids = {m["node_id"] for m in members}
    concepts = b["concepts_listed"]
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
