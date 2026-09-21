#!/usr/bin/env python3
"""CARD-G4-13 金集 manifest 工具 —— 采集 / 标注清单 / 回写 / 冻结 / 校验。

[BATCH-2026-09-18-第十五批 / CARD-G4-13]

这个工具解决一件事：金集是检索质量门禁的**真值**，而真值一旦能被悄悄改掉，
门禁就只是在给自己打分。所以：

* ``build``   —— 实算四份金集的 sha256 / 条数 / 分类分布，写进 ``gold_set_manifest.yaml``；
* ``verify``  —— 重算并比对。**两个 runner 在跑之前都会调它**，不符就拒跑（rc=2）；
* ``census``  —— 打印分类映射与 ``user_verdict`` 计数，给验收单用；
* ``checklist`` —— 出一份**零技术词**的勾选清单，给用户在 Obsidian 里逐条裁定；
* ``apply-verdicts`` —— 把勾选结果按隐藏锚**逐行**回写进 yaml（fail-closed：锚丢失 /
  读不懂的勾选一律不写，只动三个标注字段行）；
* ``collect`` —— **只读**扫一个 vault，把真实用户提问捞成候选（不入集、不写 vault）。

⛔ 设计约束（卡文 §一(e)）：只用 stdlib + ``yaml``。
**不 import app / lance / httpx，不连任何端口** —— 它要能在离线机器上、在
``pytest`` 进程里、在两个 runner 的最前面被调用。

⚠️ 关于「冻结」：``build`` 在 manifest 已存在且 ``frozen: true`` 时**拒绝覆盖**，
必须显式 ``--bump-revision --reason "<为什么>"``。冻结不是把文件设成只读，
而是「改它要留下一条说得出理由的痕迹」。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

#: manifest 文件头（build 与 approve 共用 —— 两处写字必须逐字一致）。
MANIFEST_HEADER = (
    "# gold_set_manifest.yaml — CARD-G4-13 金集冻结清单（由 backend/scripts/gold_set_manifest_tool.py 生成）\n"
    "#\n"
    "# ⛔ 不要手改这个文件：sha256 / 计数都是实算的，手改只会让 verify 红。\n"
    "#    要改金集 → 改 yaml → `python scripts/gold_set_manifest_tool.py build --bump-revision --reason '...'`。\n"
    "#\n"
    "# 两个 retrieval runner 在跑之前都会调 verify_gold_set_file()；不符就拒跑（rc=2）。\n\n"
)

#: ``backend/`` 的绝对路径。本文件位于 ``backend/scripts/``。
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

REGRESSION_DIR = BACKEND_DIR / "tests" / "regression"
MANIFEST_PATH = REGRESSION_DIR / "gold_set_manifest.yaml"

#: manifest 登记的四份金集，以及每份按哪个键分类。
#: 顺序就是 manifest ``files[]`` 的顺序 —— 两个主集在前，便于 ``census`` 读。
GOLD_SETS = (
    (REGRESSION_DIR / "vault_gold_set.yaml", "query_type"),
    (REGRESSION_DIR / "memory_gold_set.yaml", "category"),
    (REGRESSION_DIR / "vault_gold_set_shadow.yaml", "query_type"),
    (REGRESSION_DIR / "memory_gold_set_shadow.yaml", "category"),
)

#: 主集（``totals.main_set_queries`` 只数这两份；shadow 是探索区不计入门禁基数）。
MAIN_SETS = (GOLD_SETS[0][0], GOLD_SETS[1][0])

#: 跨 vault 攻击类的类名。vault 走 ``query_type``、memory 走 ``category``，名字相同。
ATTACK_CLASS = "cross_vault_attack"

VERDICT_ENUM = ("pending", "relevant", "irrelevant", "ambiguous", "needs_split")
SOURCE_KIND_ENUM = ("node", "whiteboard", "exam_board", "review_doc", "fixture", "synthetic")

#: 勾选清单里三个选项对应的 verdict 值。文案是给**非技术用户**看的，
#: 所以清单里出现的是中文短句，隐藏锚里才是枚举值。
CHECKLIST_CHOICES = (
    ("relevant", "相关 —— 这条提问，它给出的笔记确实能回答"),
    ("irrelevant", "不相关 —— 给出的笔记答非所问"),
    ("ambiguous", "说不清 —— 我也拿不准，或者这条提问本身有歧义"),
)

#: ``checklist`` 里每条的隐藏锚。``apply-verdicts`` 按它定位，不靠行号、不靠标题文字。
GSID_RE = re.compile(r"<!--\s*gsid:([^\s>]+)\s*-->")

#: 清单条目的**可见标题行**（``**vq-d01** — 「…」``）。与隐藏锚交叉核对 ——
#: 锚被误删时，勾选绝不能落到上一条头上（M-1，2026-09-20 r3）。
ITEM_TITLE_RE = re.compile(r"^\*\*(?P<id>[A-Za-z0-9._-]+)\*\*\s*[—–-]")  # id 必须是"一个词"
#: —— 清单尾「补审」段的粗体说明行（含空格/中文）不得被误认成条目标题。
#: 勾选行（容忍大写 ``X`` —— L-1）与行里的 verdict 隐藏锚。
CHECKED_LINE_RE = re.compile(r"^\s*-\s*\[[xX]\]")
CHECK_VERDICT_RE = re.compile(r"<!--\s*verdict:\s*([a-z_]+)\s*-->")
#: yaml 里三个标注字段的**规范形态**行（r6 起只用于校验键行是否规范，不用于定位；
#: 定位一律走 PyYAML 节点树的行号 —— 见 ``_apply_verdict_edits``）。
VERDICT_LINE_RE = re.compile(r"^(?P<pad>\s+)(?P<key>user_verdict|verdict_by|verdict_at):")


# ═══════════════════════════════════════════════════════════════════════════
# 基础读写
# ═══════════════════════════════════════════════════════════════════════════


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def queries_of(path: Path) -> list:
    return load_yaml(path).get("queries") or []


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_to_repo(path: Path) -> str | None:
    """manifest 里一律写**仓相对路径** —— 绝对路径换台机器就对不上。

    ⚠️ 仓外路径返回 ``None``，**不抛异常**：``verify_gold_set_file`` 是两个 runner
    的 fail-closed 边界，它自己必须不崩。崩溃（未捕获 ValueError）与「不符」
    （有文案的 rc=2）在 runner 里是两种完全不同的结局 —— 前者会把「金集被指到
    仓外了」显示成一个看不懂的堆栈。本卡的行为门就抓到过这一点。
    """
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ═══════════════════════════════════════════════════════════════════════════
# build / verify
# ═══════════════════════════════════════════════════════════════════════════


def describe_file(path: Path, class_key: str) -> dict:
    """一份金集在 manifest 里的那条记录。"""
    rel = rel_to_repo(path)
    if rel is None:
        raise ValueError(f"{path} 在仓外 —— manifest 只登记仓内路径（写进去换台机器就对不上）")
    doc = load_yaml(path)
    qs = doc.get("queries") or []
    by_class: dict = {}
    verdicts: dict = {v: 0 for v in VERDICT_ENUM}
    for q in qs:
        by_class[q.get(class_key) or "<unclassified>"] = by_class.get(q.get(class_key) or "<unclassified>", 0) + 1
        v = q.get("user_verdict")
        if v in verdicts:
            verdicts[v] += 1
        else:
            verdicts.setdefault("<invalid>", 0)
            verdicts["<invalid>"] += 1
    return {
        "path": rel,
        "config_version": (doc.get("config") or {}).get("version"),
        "sha256": sha256_of(path),
        "query_count": len(qs),
        "class_key": class_key,
        "by_class": dict(sorted(by_class.items())),
        "verdict_counts": verdicts,
    }


def build_manifest(manifest_path: Path, base_commit: str, bump: bool, reason: str | None) -> int:
    """实算并写 manifest。已存在时必须 ``--bump-revision --reason``（revision 单调）。

    r3（L-6）：旧实现只在 ``frozen: true`` 时拦 —— 手改 ``frozen: false`` 再 build 会把
    revision 重置回 1 并丢掉 ``revision_history``。现在任何**已存在的 manifest** 都
    拒绝无痕覆盖：要改只能显式升版 + 写理由。
    r4：旧 manifest 读不动 / 顶层非映射 / ``revision`` 非正整数 / ``revision_history``
    非 list —— 全部拒绝重写（r3 版会把 ``revision: null`` 当 0 重置成 1、把 dict
    history 用 ``list(...)`` 吞成 dict 键列表）。
    """
    revision = 1
    history: list = []
    bump_resets_adjudication = False
    if manifest_path.exists():
        try:
            old = load_yaml(manifest_path)
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
            print(f"⛔ 旧 manifest 读不动/解析不了（环境/输入错）—— 先人工确认再 build: {exc}", file=sys.stderr)
            return 1
        if not isinstance(old, dict):
            print(f"⛔ 旧 manifest 顶层不是映射（实测 {type(old).__name__}）—— 拒绝重写", file=sys.stderr)
            return 1
        if not bump:
            print(
                f"⛔ {manifest_path.name} 已存在（revision: {old.get('revision')}）—— "
                "revision 单调，任何重写都要显式带 --bump-revision --reason '<为什么>'。"
                "改它要留下说得出理由的痕迹。",
                file=sys.stderr,
            )
            return 1
        if not reason:
            print("⛔ --bump-revision 必须同时给 --reason", file=sys.stderr)
            return 1
        prev = old.get("revision")
        if not isinstance(prev, int) or isinstance(prev, bool) or prev < 1:
            print(f"⛔ 旧 manifest revision 非法（{prev!r}）—— 拒绝重置/截断，先人工确认", file=sys.stderr)
            return 1
        hist = old.get("revision_history")
        if hist is None:
            hist = []
        if not isinstance(hist, list):
            print(f"⛔ 旧 manifest revision_history 不是列表（{type(hist).__name__}）—— 拒绝覆盖", file=sys.stderr)
            return 1
        revision = prev + 1
        history = list(hist)
        entry: dict = {"revision": revision, "at": _now_iso(), "reason": reason}
        old_adj = old.get("adjudication")
        if isinstance(old_adj, dict) and old_adj.get("status") == "approved":
            entry["prev_adjudication"] = dict(old_adj)  # 旧签字留痕（新 revision 必须重签）
        history.append(entry)
        bump_resets_adjudication = True

    files = [describe_file(p, key) for p, key in GOLD_SETS]
    main_total = sum(f["query_count"] for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS])
    attack_total = sum(
        f["by_class"].get(ATTACK_CLASS, 0) for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS]
    )

    if bump_resets_adjudication:
        # 新 revision 的内容必须重新签字：把 adjudication 重置回 pending
        # （旧签名已在上面的 revision_history 里留痕；否则 approve 会以「已 approved」拒签，
        #  而内容已经变了 —— r18 复核 M-4）。
        _old = load_yaml(manifest_path).get("adjudication")
        prev_adj = {
            "status": "pending",
            "signed_by": None,
            "signed_at": None,
            "checklist_path": (_old or {}).get("checklist_path") if isinstance(_old, dict) else None,
        }
    else:
        prev_adj = (load_yaml(manifest_path).get("adjudication") if manifest_path.exists() else None) or {
            "status": "pending",
            "signed_by": None,
            "signed_at": None,
            "checklist_path": None,
        }

    doc = {
        "revision": revision,
        "frozen_at": _now_iso(),
        "base_commit": base_commit,
        "frozen": True,
        "files": files,
        "totals": {
            "main_set_queries": main_total,
            "cross_vault_attack": attack_total,
            "all_registered_queries": sum(f["query_count"] for f in files),
        },
        "adjudication": prev_adj,
    }
    if history:
        doc["revision_history"] = history

    manifest_path.write_text(
        MANIFEST_HEADER + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"OK build revision={revision} main={main_total} attack={attack_total} -> {manifest_path.name}")
    return 0


def verify_all(manifest_path: Path | None = None) -> tuple[int, list]:
    """重算并比对。返回 ``(rc, 行列表)``。

    rc 语义与两个 runner 的既有约定一致：
    ``0`` 全符 / ``1`` 内容不符 / ``2`` 文件缺失或 yaml 解析错（= 环境/输入错）。

    r3（L-6）：逐文件对账之外，还复核 ``totals`` 与文件重算一致、``adjudication``
    合法（``approved`` ⇒ 必须有 ``signed_by`` / ``signed_at``），并把
    OSError·UnicodeDecodeError 族与坏条目一并归 rc=2（不再以异常逃逸）。
    r4：登记文档**形状**也守卫 —— 顶层非映射 / ``queries`` 非列表 / ``config`` 非映射
    归 rc=2（r3 版会在 ``doc.get`` / ``len(qs)`` / ``cfg.get`` 上崩）。
    """
    try:
        manifest_path = Path(manifest_path or MANIFEST_PATH)
    except TypeError as exc:
        return 2, [f"UNPARSEABLE manifest_path 不是路径（环境/输入错）: {manifest_path!r} —— {exc}"]
    lines: list = []
    if not manifest_path.exists():
        return 2, [f"MISSING {manifest_path} manifest 不存在"]
    try:
        m = load_yaml(manifest_path)
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        return 2, [f"UNPARSEABLE {manifest_path} {exc}"]
    if not isinstance(m, dict):
        return 2, [f"UNPARSEABLE {manifest_path} 顶层不是映射（环境/输入错）"]
    entries = m.get("files")
    if not isinstance(entries, list):
        return 2, [f"UNPARSEABLE {manifest_path} files 字段非法（环境/输入错）"]
    if not entries:
        return 2, [f"MISSING {manifest_path} files 为空 —— 未登记任何文件（环境/输入错）"]

    rc = 0
    counted: dict = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            lines.append(f"UNPARSEABLE {manifest_path} files 条目非法（环境/输入错）: {entry!r}")
            rc = max(rc, 2)
            continue
        rel = entry["path"]
        path = REPO_ROOT / rel
        if not path.exists():
            lines.append(f"MISSING {rel} 期望存在 实测不存在")
            rc = max(rc, 2)
            continue
        try:
            doc = load_yaml(path)
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
            lines.append(f"UNPARSEABLE {rel} {exc}")
            rc = max(rc, 2)
            continue
        if not isinstance(doc, dict):
            lines.append(f"UNPARSEABLE {rel} 顶层不是映射（环境/输入错，实测 {type(doc).__name__}）")
            rc = max(rc, 2)
            continue
        try:
            actual_sha = sha256_of(path)
        except (OSError, UnicodeDecodeError) as exc:
            lines.append(f"UNREADABLE {rel} {exc}")
            rc = max(rc, 2)
            continue

        want_sha = entry.get("sha256")
        if not isinstance(want_sha, str):
            lines.append(f"UNPARSEABLE {rel} manifest 条目 sha256 非法（环境/输入错）")
            rc = max(rc, 2)
            continue
        if actual_sha != want_sha:
            lines.append(f"MISMATCH {rel} sha256={want_sha} actual={actual_sha}")
            rc = max(rc, 1)
            continue

        qs = doc.get("queries")
        if not isinstance(qs, list):
            lines.append(f"UNPARSEABLE {rel} queries 不是列表（环境/输入错，实测 {type(qs).__name__}）")
            rc = max(rc, 2)
            continue
        if any(not isinstance(q, dict) for q in qs):
            lines.append(f"UNPARSEABLE {rel} queries 含非映射条目（环境/输入错）")
            rc = max(rc, 2)
            continue
        if len(qs) != entry.get("query_count"):
            lines.append(f"MISMATCH {rel} query_count={entry.get('query_count')} actual={len(qs)}")
            rc = max(rc, 1)
            continue
        cfg = doc.get("config") or {}
        if not isinstance(cfg, dict):
            lines.append(f"UNPARSEABLE {rel} config 不是映射（环境/输入错，实测 {type(cfg).__name__}）")
            rc = max(rc, 2)
            continue
        if cfg.get("version") != entry.get("config_version"):
            lines.append(f"MISMATCH {rel} config_version={entry.get('config_version')} actual={cfg.get('version')}")
            rc = max(rc, 1)
            continue

        bad = _field_problems(qs)
        if bad:
            lines.append(f"MISMATCH {rel} fields_ok=True actual={bad[0]}（共 {len(bad)} 条）")
            rc = max(rc, 1)
            continue

        class_key = entry.get("class_key")
        counted[rel] = {
            "query_count": len(qs),
            "attack": sum(1 for q in qs if class_key and q.get(class_key) == ATTACK_CLASS),
        }
        lines.append(f"OK {rel} sha256={actual_sha[:12]}… queries={len(qs)}")

    if rc == 0:  # r3：totals / adjudication 与重算一致（L-6）
        main_resolved = [p.resolve() for p in MAIN_SETS]
        main_total = sum(v["query_count"] for rel, v in counted.items() if (REPO_ROOT / rel).resolve() in main_resolved)
        attack_total = sum(v["attack"] for rel, v in counted.items() if (REPO_ROOT / rel).resolve() in main_resolved)
        all_total = sum(v["query_count"] for v in counted.values())
        totals = m.get("totals")
        if not isinstance(totals, dict):
            lines.append("MISMATCH totals 缺失或非映射（与文件重算不一致）")
            rc = max(rc, 1)
        else:
            for key, want in (
                ("main_set_queries", main_total),
                ("cross_vault_attack", attack_total),
                ("all_registered_queries", all_total),
            ):
                if totals.get(key) != want:
                    lines.append(f"MISMATCH totals.{key}={totals.get(key)} 重算={want}")
                    rc = max(rc, 1)
        adj = m.get("adjudication")
        if not isinstance(adj, dict) or adj.get("status") not in ("pending", "approved"):
            got = adj.get("status") if isinstance(adj, dict) else adj
            lines.append(f"MISMATCH adjudication.status={got!r}（应为 pending | approved）")
            rc = max(rc, 1)
        elif adj.get("status") == "approved":
            sb, sa = adj.get("signed_by"), adj.get("signed_at")
            if not (isinstance(sb, str) and sb.strip() and isinstance(sa, str) and sa.strip()):
                lines.append(f"MISMATCH adjudication.status=approved 但签名缺失 signed_by={sb!r} signed_at={sa!r}")
                rc = max(rc, 1)
    return rc, lines


def _field_problems(queries: list) -> list:
    """每条 query 的标注字段是否齐全合法。"""
    bad = []
    for q in queries:
        qid = q.get("id", "<no-id>")
        if q.get("user_verdict") not in VERDICT_ENUM:
            bad.append(f"{qid}.user_verdict={q.get('user_verdict')!r}")
        src = q.get("source")
        if not isinstance(src, dict) or src.get("kind") not in SOURCE_KIND_ENUM:
            bad.append(f"{qid}.source={src!r}")
        elif src.get("ref") is not None and not isinstance(src.get("ref"), str):
            bad.append(f"{qid}.source.ref={src.get('ref')!r}")
    return bad


def _nonempty_str(v) -> bool:
    """真·非空字符串：**两头的空白也要剔掉**（`" "` 会让匹配恒真 / 硬禁恒命中 —— r12 复核 M1）。"""
    return isinstance(v, str) and bool(v.strip())


def _contains_ok(v) -> bool:
    """``expect_hit[i].contains`` 的可接受形态：**真值**标量、``str()`` 后非空白、**非 nan/inf**。

    ⚠️ runner 是 ``if e.get("contains")`` 先判真值再 ``str()`` —— ``0``/``0.0``（falsy）
    会被静默跳过内容检查（fail-open）；``nan``/``inf`` 虽真值，但会被按字面 ``"nan"``/``"inf"``
    匹配（意图几乎必然落空）。两类都拒（r14 复核 LOW-1 / r15 复核 LOW-2）。
    ``bool`` 也拒 —— 它是 int 子类，放进来会得到 ``"True"`` 这种反直觉匹配面。
    """
    if isinstance(v, bool) or v is None or isinstance(v, (list, dict)):
        return False
    if isinstance(v, float) and not math.isfinite(v):
        return False  # nan/inf 会被 runner 按字面 "nan"/"inf" 匹配 —— 意图几乎必然落空，直接拒（r15 复核 LOW-2）
    if not v:
        return False
    return bool(str(v).strip())


def _grade_ok(v) -> bool:
    """``expect_hit[i].grade`` 的可接受形态（runner 走 ``int(...)``）：0..10 的 int / 整值 float /
    ``int()`` 可解析的数字串（含全角、正号、两侧空白 —— 与 runner 的真实接受面一致）。"""
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return 0 <= v <= 10
    if isinstance(v, float):
        return v.is_integer() and 0 <= v <= 10
    if isinstance(v, str):
        try:
            n = int(v.strip())
        except ValueError:
            return False
        return 0 <= n <= 10
    return False


def _is_finite_number(v) -> bool:
    """bool 不算数值；float 要 isfinite；**int 一律视为有限**（不调 isfinite —— 超大 int 会 OverflowError）。"""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v) if isinstance(v, float) else True


def verify_gold_set_file(path: Path, manifest_path: Path | None = None) -> tuple[bool, str]:
    """**两个 runner 调的就是这个**：单份金集是否与 manifest 相符。

    返回 ``(是否相符, 一行说明)``。runner 拿到 ``False`` 就打印说明并 ``return 2``。
    ⛔ 环境/输入错一律走 ``(False, 文案)``、**不以异常逃逸**：它是两个 runner 的
    fail-closed 边界，崩溃会让 runner 以未捕获异常收场（exit 1 =「指标回退」档），
    把 rc=2「环境/输入错」的语义污染掉。覆盖面：manifest 解析失败 / 顶层非映射 /
    **不可读（OSError·UnicodeDecodeError）族** / **``files`` 非列表或含非映射条目** /
    已登记文件缺失或不可读 / 条目 sha 或 query_count 非法 —— 全部不崩
    （r1 H-1；r2 整改；r3 补 M-R2a/M-R2b；r4 补非目标坏条目 / query_count）。

    ⚠️ 本函数只回答「相符/不符」（bool 压缩），**不承诺**与 CLI ``verify_all`` 的
    rc 一一对应：sha 不符在 ``verify_all`` 是 rc=1、经本函数 + runner 统一按 rc=2
    呈现，两者靠**文案**区分（L-R2a：旧 docstring「口径对齐」是 overclaim）。
    """
    try:
        manifest_path = Path(manifest_path or MANIFEST_PATH)
        target_path = Path(path)
    except TypeError as exc:
        return False, f"入参不是路径（环境/输入错）: path={path!r} manifest={manifest_path!r} —— {exc}"
    if not manifest_path.exists():
        return False, f"manifest 不存在: {manifest_path}"
    try:
        m = load_yaml(manifest_path)
    except yaml.YAMLError as exc:
        return False, f"manifest 解析失败（环境/输入错）: {manifest_path} —— {exc}"
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"manifest 不可读（环境/输入错）: {manifest_path} —— {exc}"
    if not isinstance(m, dict):
        return False, f"manifest 顶层不是映射（环境/输入错）: {manifest_path}（实测 {type(m).__name__}）"
    entries = m.get("files")
    if not isinstance(entries, list):
        return False, f"manifest files 字段非法（环境/输入错）: {manifest_path}（实测 {type(entries).__name__}）"
    if not entries:
        return False, f"manifest 未登记任何文件（环境/输入错）: {manifest_path}"
    for entry in entries:
        if not isinstance(entry, dict):
            return False, f"manifest files 条目非法（环境/输入错）: {entry!r}"
    want = rel_to_repo(target_path)
    if want is None:
        return False, f"{path} 在仓外 —— manifest 只登记仓内路径，无法校验"
    for entry in entries:
        if entry.get("path") != want:
            continue
        if not target_path.exists():
            return False, f"{want} 已登记但文件缺失（环境/输入错）: {path}"
        want_sha = entry.get("sha256")
        if not isinstance(want_sha, str):
            return False, f"{want} manifest 条目的 sha256 缺失或非法（环境/输入错）: {want_sha!r}"
        want_count = entry.get("query_count")
        if not isinstance(want_count, int) or isinstance(want_count, bool) or want_count < 0:
            return False, f"{want} manifest 条目的 query_count 缺失或非法（环境/输入错）: {want_count!r}"
        try:
            actual = sha256_of(target_path)
        except (OSError, UnicodeDecodeError) as exc:
            return False, f"{want} 不可读（环境/输入错）: {path} —— {exc}"
        if actual != want_sha:
            return False, f"{want} sha256 期望 {want_sha[:12]}… 实测 {actual[:12]}…"
        # 内容形状守卫（r5）：sha 相符 ≠ 内容可跑 —— queries 含非映射条目会让两个
        # runner 在取 q["query"] 时 TypeError → exit 1（污染「指标回退」档）。
        try:
            doc = load_yaml(target_path)
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
            return False, f"{want} 解析失败（环境/输入错）: {target_path} —— {exc}"
        if not isinstance(doc, dict):
            return False, f"{want} 顶层不是映射（环境/输入错）"
        qs = doc.get("queries")
        if not isinstance(qs, list) or any(not isinstance(q, dict) for q in qs):
            return False, f"{want} queries 不是映射列表（环境/输入错）"
        if len(qs) != want_count:
            return False, f"{want} queries 数量 {len(qs)} ≠ manifest {want_count}"
        if not isinstance(doc.get("config"), dict):
            return False, f"{want} config 不是映射（环境/输入错）—— runner 会 KeyError/AttributeError"
        # r10：非 JSON 标量（YAML 日期 / !!binary / 集合等）会让 httpx/JSON 落盘 TypeError ⇒
        # 一次全文档 JSON 化检查把它整类关掉，不用逐键枚举。
        try:
            json.dumps(doc, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            return False, f"{want} 含不可 JSON 序列化的标量（环境/输入错）: {exc}"
        bad_q = [q.get("id") for q in qs if "id" not in q or not isinstance(q.get("query"), str)]
        if bad_q:
            return False, f"{want} 有条目缺 id 或 query 非字符串（环境/输入错）: {bad_q[:3]}"
        for q in qs:
            qid = q.get("id")
            if not _nonempty_str(qid):
                return False, f"{want} 有条目 id 不是非空字符串（环境/输入错）: {qid!r}"
            if not _nonempty_str(q.get("query")):
                return False, f"{want} 条目 {qid!r} 的 query 是空白串（环境/输入错）"
            for sk in ("language", "query_type", "category"):
                if sk in q and not _nonempty_str(q[sk]):
                    return False, f"{want} 条目 {qid!r} 的 {sk} 不是非空字符串（环境/输入错）: {q[sk]!r}"
        # r7：把「映射但不可跑」的两类残余也拦在 runner 之前 ——
        # ① 一个期望键都没有的条目（memory runner 会 q["expect_any"] KeyError）；
        # ② config 里 runner 会 int()/float()/`.get` 的键类型不对（ValueError/AttributeError）。
        # 按 manifest 声明的类目键区分文件「种类」：vault 用 query_type、memory 用 category。
        # 两个 runner 的取值面不同（memory 在非 expect_empty 分支直接 q["expect_any"]），
        # 所以守卫必须按种类要求**各自**能跑的期望键（r8）。
        kind = entry.get("class_key")
        if kind == "query_type":
            for q in qs:
                qid = q.get("id")
                hits, nots, empty = q.get("expect_hit"), q.get("expect_not_hit"), q.get("expect_empty")
                if not (hits or nots or empty):
                    return False, f"{want} vault 条目 {qid!r} 缺期望键（环境/输入错）"
                if empty and hits:
                    return False, f"{want} vault 条目 {qid!r} expect_empty 与 expect_hit 并存（自相矛盾）"
                if "expect_hit" in q and (
                    not isinstance(hits, list)
                    or any(
                        not isinstance(h, dict)
                        or not _nonempty_str(h.get("file"))
                        or ("contains" in h and not _contains_ok(h["contains"]))
                        or ("grade" in h and not _grade_ok(h["grade"]))
                        for h in hits
                    )
                ):
                    return (
                        False,
                        f"{want} vault 条目 {qid!r} 的 expect_hit 形态不对"
                        "（file 须非空 str；contains 须真值标量且 str() 后非空白、非 nan/inf"
                        "（数字请加引号）；grade 须 0..10）",
                    )
                if "expect_not_hit" in q and (
                    not isinstance(nots, list)
                    or any(
                        not isinstance(n_, dict)
                        or not _nonempty_str(n_.get("path_glob"))
                        or isinstance(n_.get("max_in_top_k"), bool)
                        or (
                            "max_in_top_k" in n_
                            and (
                                isinstance(n_["max_in_top_k"], bool)
                                or not isinstance(n_["max_in_top_k"], int)
                                or not (0 <= n_["max_in_top_k"] <= 10**6)
                            )
                        )
                        for n_ in nots
                    )
                ):
                    return False, f"{want} vault 条目 {qid!r} 的 expect_not_hit 形态不对（环境/输入错）"
                if "expect_empty" in q and not isinstance(empty, bool):
                    return False, f"{want} vault 条目 {qid!r} 的 expect_empty 不是 bool（环境/输入错）"
        elif kind == "category":
            for q in qs:
                qid = q.get("id")
                if q.get("expect_empty"):
                    if q.get("expect_any"):
                        return False, f"{want} memory 条目 {qid!r} expect_empty 与 expect_any 并存（自相矛盾）"
                    continue
                anys = q.get("expect_any")
                if not isinstance(anys, list) or not anys or any(not _nonempty_str(a) for a in anys):
                    return False, f"{want} memory 条目 {qid!r} 的 expect_any 缺失/不是非空字符串列表（环境/输入错）"
                if "expect_empty" in q and not isinstance(q["expect_empty"], bool):
                    return False, f"{want} memory 条目 {qid!r} 的 expect_empty 不是 bool（环境/输入错）"
        else:
            return False, f"{want} manifest 条目的 class_key 非法（环境/输入错）: {kind!r}"
        cfg = doc["config"]
        for num_key in ("tolerance", "duplicate_ratio", "max_results", "top_k"):
            if num_key not in cfg:
                continue
            v = cfg[num_key]
            if not _is_finite_number(v):
                return False, f"{want} config.{num_key} 不是有限数值（环境/输入错）: {v!r}"
        for rng_key in ("tolerance", "duplicate_ratio"):
            if rng_key in cfg and not (0.0 <= cfg[rng_key] <= 1.0):
                return False, f"{want} config.{rng_key} 超出 [0,1]（环境/输入错）: {cfg[rng_key]!r}"
        for int_key in ("max_results", "top_k"):
            if int_key in cfg and (
                isinstance(cfg[int_key], bool) or not isinstance(cfg[int_key], int) or not (1 <= cfg[int_key] <= 10**6)
            ):
                return False, f"{want} config.{int_key} 不在 [1, 10^6]（环境/输入错）: {cfg[int_key]!r}"
        for id_key in ("group_id", "vault_id"):
            if id_key in cfg and cfg[id_key] is not None and not _nonempty_str(cfg[id_key]):
                return False, f"{want} config.{id_key} 不是非空字符串或 null（环境/输入错）: {cfg[id_key]!r}"
        ver = cfg.get("version")
        if ver is None or not _is_finite_number(ver) or not (0 <= ver <= 10**6):
            return False, f"{want} config.version 不在 [0, 10^6]（环境/输入错）: {ver!r}"
        for map_key in ("contamination", "forbidden", "delivery"):
            if map_key in cfg and not isinstance(cfg[map_key], dict):
                return False, f"{want} config.{map_key} 不是映射（环境/输入错）: {type(cfg[map_key]).__name__}"
        # r12（r11 复核 M1）：内部键必须是**非空 str 列表** —— 字符串会被逐字符迭代
        # （含 "*" ⇒ 假硬禁 rc=1；不含 ⇒ 硬禁门恒空 fail-open）。
        for map_key, list_keys in (
            ("contamination", ("path_globs", "doc_types")),
            ("forbidden", ("path_globs", "doc_types", "markers")),
        ):
            if map_key not in cfg:
                continue
            m_sub = cfg[map_key]
            for lk in list_keys:
                if lk in m_sub and (
                    not isinstance(m_sub[lk], list) or not m_sub[lk] or any(not _nonempty_str(x) for x in m_sub[lk])
                ):
                    return False, (
                        f"{want} config.{map_key}.{lk} 不是非空字符串列表"
                        f"（空表会让该门恒空；str 会被逐字符迭代）: {m_sub[lk]!r}"
                    )
        if "delivery" in cfg:
            dv = cfg["delivery"]
            if "hard_cap" in dv:
                hc = dv["hard_cap"]
                if isinstance(hc, bool) or not isinstance(hc, int) or not (0 <= hc <= 10**6):
                    return False, f"{want} config.delivery.hard_cap 不在 [0, 10^6]（环境/输入错）: {hc!r}"
            for fk in ("min_relevance", "elbow_drop_threshold"):
                if fk in dv:
                    fv = dv[fk]
                    if not _is_finite_number(fv) or not (0.0 <= fv <= 1.0):
                        return False, f"{want} config.delivery.{fk} 不是 [0,1] 有限数值（环境/输入错）: {fv!r}"
        if "leak_markers" in cfg:
            lm = cfg["leak_markers"]
            if not isinstance(lm, list) or not lm or any(not _nonempty_str(x) for x in lm):
                return False, f"{want} config.leak_markers 不是非空字符串列表（空表会让泄漏指标恒 0）: {lm!r}"
        return True, f"OK {want} sha256={actual[:12]}… queries={want_count}"
    return False, f"{want} 未登记在 manifest 里"


def census(manifest_path: Path | None = None) -> int:
    manifest_path = manifest_path or MANIFEST_PATH
    total = 0
    for path, key in GOLD_SETS:
        qs = queries_of(path)
        total += len(qs)
        by = {}
        verd = {}
        for q in qs:
            by[q.get(key) or "<unclassified>"] = by.get(q.get(key) or "<unclassified>", 0) + 1
            verd[q.get("user_verdict")] = verd.get(q.get("user_verdict"), 0) + 1
        print(f"{path.name}  ({key})  n={len(qs)}")
        for k, v in sorted(by.items()):
            print(f"    {k:<28} {v}")
        print(f"    verdicts: {dict(sorted(verd.items(), key=lambda kv: str(kv[0])))}")
    main = sum(len(queries_of(p)) for p in MAIN_SETS)
    attack = sum(len([q for q in queries_of(p) if (q.get(k) == ATTACK_CLASS)]) for p, k in GOLD_SETS if p in MAIN_SETS)
    print(f"\nmain_set_queries={main}  cross_vault_attack={attack}  all_registered={total}")
    if manifest_path.exists():
        adj = load_yaml(manifest_path).get("adjudication") or {}
        print(f"adjudication.status={adj.get('status')}  signed_by={adj.get('signed_by')}")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# approve（用户裁定收尾：置 approved + 签字）
# ═══════════════════════════════════════════════════════════════════════════


def _parse_iso_utc(ts: str) -> str | None:
    """把 ISO8601（允许尾 ``Z``）规范成 UTC ``…Z``；不可解析返回 ``None``。"""
    try:
        dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def approve_manifest(
    manifest_path: Path, signed_by: str, signed_at: str | None = None, checklist: str | None = None
) -> int:
    """把 manifest 的 ``adjudication`` 置为 **approved + 用户签字**（fail-closed）。

    ⛔ 前置（全过才写）：

    * ``--signed-by`` 非空（空签名等于没签）；
    * ``--at`` 若给必须是 ISO8601；``--checklist`` 若给必须实际存在；
    * manifest 当前 ``verify_all`` rc=0（冻结面自洽）；
    * manifest 登记路径必须**恰等于四份金集**（registry 不许悄悄缩水 —— r17 复核 M-1）；
    * 当前非 ``approved``（拒绝静默覆写既有签名/回溯时间 —— r17 复核 M-3）；
    * **两个主集**（MAIN_SETS = 103 条，goal 口径）里没有任何 ``user_verdict: pending``
      —— AI 不得代填；shadow 集的 pending 不在用户 session 面内（r17 复核 H-2），不拦签字。

    写入用「临时文件 + ``os.replace``」原子替换，替换前对**新内容**重跑 ``verify_all``；
    任何一步不过 ⇒ 不改动原文件；临时文件异常一律走文案 + rc=1（不冒泡 traceback）。
    """
    if not isinstance(signed_by, str) or not signed_by.strip():
        print("⛔ --signed-by 不能为空 —— 空签名等于没签", file=sys.stderr)
        return 1
    if signed_at is not None:
        normalized = _parse_iso_utc(signed_at)
        if normalized is None:
            print(f"⛔ --at 不是 ISO8601 时间: {signed_at!r}", file=sys.stderr)
            return 1
        signed_at = normalized
    if checklist is not None:
        cp = Path(checklist)
        if not cp.exists() or not cp.is_file():
            print(f"⛔ --checklist 不存在或不是文件: {checklist}", file=sys.stderr)
            return 1
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        print(f"⛔ manifest 不存在: {manifest_path}", file=sys.stderr)
        return 1

    rc, lines = verify_all(manifest_path)
    if rc != 0:
        print("⛔ 先让 `verify` 全绿再签字：", file=sys.stderr)
        for ln in lines:
            print(f"  {ln}", file=sys.stderr)
        return 1

    m = load_yaml(manifest_path)
    if not isinstance(m, dict):
        print("⛔ manifest 顶层不是映射 —— 拒绝签字", file=sys.stderr)
        return 1
    want_paths = sorted(x for x in (rel_to_repo(path) for path, _key in GOLD_SETS) if x)
    got_paths = sorted(e.get("path") for e in (m.get("files") or []) if isinstance(e, dict) and e.get("path"))
    if got_paths != want_paths:
        print(
            f"⛔ manifest 登记路径与四份金集不符（registry 完整性）—— 拒绝签字:\n"
            f"   want={want_paths}\n   got ={got_paths}",
            file=sys.stderr,
        )
        return 1

    adj0 = m.get("adjudication") if isinstance(m.get("adjudication"), dict) else {}
    if adj0.get("status") == "approved":
        print(
            f"⛔ 已 approved（signed_by={adj0.get('signed_by')!r}, signed_at={adj0.get('signed_at')!r}）"
            "—— 拒绝静默覆写签名；要改需先走 build --bump-revision 并人工确认",
            file=sys.stderr,
        )
        return 1

    pending: list = []
    for path in MAIN_SETS:
        rel = rel_to_repo(path) or str(path)
        try:
            qs = queries_of(path)
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
            print(f"⛔ 读不动 {rel}（环境/输入错）: {exc}", file=sys.stderr)
            return 1
        n = sum(1 for q in qs if (q.get("user_verdict") or "pending") == "pending")
        if n:
            pending.append(f"{rel}: {n}")
    if pending:
        print("⛔ 主集还有 pending 的 user_verdict —— AI 不得代填，用户没标完不许签字：", file=sys.stderr)
        for it in pending:
            print(f"  {it}", file=sys.stderr)
        return 1

    adj = dict(adj0)
    adj["status"] = "approved"
    adj["signed_by"] = signed_by.strip()
    adj["signed_at"] = signed_at or _now_iso()
    if checklist is not None:
        adj["checklist_path"] = checklist
    adj.setdefault("checklist_path", None)
    m["adjudication"] = adj

    tmp = manifest_path.with_name(manifest_path.name + ".approve.tmp")
    try:
        try:
            tmp.write_text(
                MANIFEST_HEADER + yaml.safe_dump(m, allow_unicode=True, sort_keys=False, width=100),
                encoding="utf-8",
            )
        except (OSError, UnicodeDecodeError) as exc:
            print(f"⛔ 临时文件写不动（环境/输入错）—— 原文件不动: {exc}", file=sys.stderr)
            return 1
        rc2, lines2 = verify_all(tmp)
        if rc2 != 0:
            print("⛔ 新内容 verify 不为 0 —— 保持原文件不动：", file=sys.stderr)
            for ln in lines2:
                print(f"  {ln}", file=sys.stderr)
            return 1
        try:
            tmp.replace(manifest_path)
        except OSError as exc:
            print(f"⛔ 替换 manifest 失败（环境/输入错）—— 原文件不动: {exc}", file=sys.stderr)
            return 1
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
    print(f"OK approve signed_by={adj['signed_by']} signed_at={adj['signed_at']} -> {manifest_path.name}")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# checklist / apply-verdicts
# ═══════════════════════════════════════════════════════════════════════════


def _expect_hint(q: dict) -> str:
    """把「它期望命中什么」翻译成一句**非技术**的话。"""
    if q.get("expect_empty"):
        return "（期望：库里**没有**这个主题，应当什么都不返回）"
    hits = q.get("expect_hit") or []
    if hits:
        names = "、".join(str(h.get("file")) for h in hits if isinstance(h, dict) and h.get("file"))
        if names:
            return f"（期望命中的笔记：{names}）"
    anys = q.get("expect_any") or []
    if anys:
        return f"（期望结果里出现这些词之一：{'、'.join(str(a) for a in anys)}）"
    nots = q.get("expect_not_hit") or []
    if nots:
        return "（期望：**不该**出现另一个 vault 的同名资产）"
    return "（期望：见金集原文）"


def write_checklist(paths: list, out_md: Path) -> int:
    """出一份给用户逐条勾的清单。⛔ 段落里零技术词。"""
    lines = [
        "# 金集裁定清单 — CARD-G4-13",
        "",
        "下面每一条是**一次提问**，以及系统认为「应该给你看到什么」。",
        "你只需要读一句提问、看一眼它期望的笔记名，然后勾一个格子：",
        "**相关 / 不相关 / 说不清**。三选一，勾错了改回来就行。",
        "",
        "> 不用管技术细节，也不用打开任何终端。勾完保存，告诉我一声即可。",
        "",
    ]
    n = 0
    for path in paths:
        lines.append(f"## {path.name}")
        lines.append("")
        for q in queries_of(path):
            qid = q.get("id")
            lines.append(f"<!-- gsid:{qid} -->")
            lines.append(f"**{qid}** — 「{q.get('query')}」")
            lines.append(f"  {_expect_hint(q)}")
            for value, label in CHECKLIST_CHOICES:
                lines.append(f"- [ ] {label}  <!-- verdict:{value} -->")
            lines.append("")
            n += 1
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return n


def _yaml_scalar(value) -> str:
    """把值渲成一个**行内** yaml 标量（时间戳这类会被自动加引号，读回仍是 str）。

    ⚠️ 不要直接 ``safe_dump(value)`` 再 strip：顶层标量的 dump 会带文档结束标记
    ``...``（实测踩过 —— 渲染出的行会把后续字段挤出文档，预检当场解析失败）。
    ⚠️ 值里含**真实**换行/回车 ⇒ 拒绝 —— r3 守卫误写成查字面反斜杠-n 两字符，
    漏掉真换行（r4 修正）。
    """
    dumped = yaml.safe_dump({"v": value}, allow_unicode=True, default_flow_style=False)
    scalar = dumped.split(":", 1)[1].strip()
    if "\n" in scalar or "\r" in scalar:
        raise ValueError(f"值渲染成多行了（本函数只支持行内标量）: {value!r}")
    return scalar


def _parse_checklist_picks(text: str) -> tuple[dict, list]:
    """解析勾选清单 → ``(picks, problems)``。

    fail-closed（r3；r4 收紧边界）：

    * 隐藏锚必须**独占一行**才算锚；内嵌在标题/正文里的 ``<!-- gsid:… -->`` **不夺权**
      （r3 复核 ①：旧版谁先出现谁赢，标题里内嵌的锚能把勾选骗到另一条头上）。
    * 勾选只归属「已见到匹配的条目标题」的当前条目（勾选在标题之前 ⇒ 不归属）；
    * markdown 标题（``#``…）与分隔线 ``---`` 结束当前条目 —— 清单尾「补审」段的
      勾选不得记到最后一条头上。

    锚被误删时勾选绝不记到上一条（M-1：旧实现取「最近一个锚」）；读不懂的勾选不再
    静默跳过（L-1：旧实现 ``continue`` 无 problem）。
    """
    picks: dict = {}
    problems: list = []
    current: str | None = None
    titled = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^#{1,6}\s", stripped) or stripped == "---":
            current, titled = None, False
            continue
        m = GSID_RE.fullmatch(stripped)
        if m:
            current, titled = m.group(1), False
            continue
        h = ITEM_TITLE_RE.match(stripped)
        if h:
            titled_id = h.group("id").strip()
            if current is None or titled_id != current:
                problems.append(f"标题 {titled_id} 与隐藏锚 {current!r} 对不上（锚被删/被改？）—— 本条勾选忽略")
                current, titled = None, False
            else:
                titled = True
            continue
        if CHECKED_LINE_RE.match(line):
            if current is None or not titled:
                problems.append(f"勾选行不在任何条目标题之下（锚/标题缺失或已越界）—— 忽略：{stripped[:60]!r}")
                continue
            vm = CHECK_VERDICT_RE.search(line)
            if not vm:
                problems.append(f"{current}: 勾选行里没有 verdict 锚（被改坏/删掉了？）—— 本条不动")
                continue
            v = vm.group(1)
            if current in picks:
                problems.append(f"{current}: 勾了不止一个（{picks[current]} 与 {v}）—— 该条不动")
                picks[current] = None
            elif picks.get(current, "") is None:
                continue
            else:
                picks[current] = v
    return {k: v for k, v in picks.items() if v}, problems


def _node_key_lines(node, key: str) -> list:
    """mapping 节点里名为 ``key`` 的键**所在行号**列表（重复键返回多个）。"""
    out: list = []
    if isinstance(node, yaml.MappingNode):
        for k_node, _v_node in node.value:
            if isinstance(k_node, yaml.ScalarNode) and k_node.value == key:
                out.append(k_node.start_mark.line)
    return out


def _apply_verdict_edits(path: Path, updates: dict, queries_in_yaml: list) -> tuple[list, list]:
    """把 ``{id: {字段: 新值}}`` **逐行**写回 yaml，返回 ``(已写 id, problems)``。

    r6：条目与标注字段的位置**全部来自 PyYAML 节点树的行号**（``yaml.compose``），
    不再用任何文本层启发式 —— 字符串值 / block scalar / 被覆盖的同级键里长得像
    ``- id:`` 的行永远不会被当条目（r3~r5 三轮复核反复挖出的同一类）；同一 id /
    同一标注键出现多次 ⇒ 拒绝；标注键行必须是**规范形态**（``key: value`` 单行），
    否则该条不动（fail-closed，绝不猜）。只改三行，其余字节原样（字节级读写）。

    落盘前仍做两道总闸：全文档预检不变量（除被点条目三字段外逐键一致）+ 读回校验。
    """
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{path.name}: 读不动/不是 UTF-8（环境/输入错）—— 不回写: {exc}"]
    try:
        root = yaml.compose(text)
    except yaml.YAMLError as exc:
        return [], [f"{path.name}: YAML 节点树解析失败（环境/输入错）—— 不回写: {exc}"]
    if not isinstance(root, yaml.MappingNode):
        return [], [f"{path.name}: 顶层不是映射节点 —— 不回写"]

    seq_nodes = [v for k, v in root.value if isinstance(k, yaml.ScalarNode) and k.value == "queries"]
    if len(seq_nodes) != 1 or not isinstance(seq_nodes[0], yaml.SequenceNode):
        return [], [f"{path.name}: 顶层 `queries` 不是唯一的序列节点 —— 不回写"]

    items: list = []
    for item in seq_nodes[0].value:
        if not isinstance(item, yaml.MappingNode):
            return [], [f"{path.name}: queries 里有非映射条目 —— 不回写"]
        if len(_node_key_lines(item, "id")) != 1:
            return [], [f"{path.name}: 有条目 id 键缺失或重复 —— 不回写"]
        id_val = None
        for k_node, v_node in item.value:
            if isinstance(k_node, yaml.ScalarNode) and k_node.value == "id" and isinstance(v_node, yaml.ScalarNode):
                id_val = v_node.value
        items.append({"id": str(id_val), "node": item, "start": item.start_mark.line})
    if [it["id"] for it in items] != [str(q.get("id")) for q in queries_in_yaml]:
        return [], [f"{path.name}: 节点树 id 序与解析结果不符 —— 不回写"]

    lines = text.splitlines(keepends=True)
    spans: dict = {}
    for k, it in enumerate(items):
        end = items[k + 1]["start"] if k + 1 < len(items) else len(lines)
        spans.setdefault(it["id"], []).append((it["start"], end, it["node"]))

    plans: dict = {}  # qid -> {行号: 新行}
    applied: list = []
    problems: list = []
    for qid, fields in updates.items():
        where = spans.get(qid) or []
        if len(where) != 1:
            problems.append(f"{qid}: 节点树里出现 {len(where)} 次（应恰 1 次）—— 不回写")
            continue
        start, end, node = where[0]
        found: dict = {}
        multi_line_value = False
        for key in ("user_verdict", "verdict_by", "verdict_at"):
            hits = []
            for k_node, v_node in node.value:
                if isinstance(k_node, yaml.ScalarNode) and k_node.value == key:
                    if not isinstance(v_node, yaml.ScalarNode) or v_node.end_mark.line != v_node.start_mark.line:
                        multi_line_value = True
                    hits.append(k_node.start_mark.line)
            found[key] = hits
        missing = [k for k in found if len(found[k]) != 1]
        if missing or multi_line_value:
            problems.append(f"{qid}: 标注键缺失/重复/值跨行（{missing}, multi_line={multi_line_value}）—— 该条不动")
            continue
        plan: dict = {}
        skip: str | None = None
        for key, value in fields.items():
            line_i = found[key][0]
            if not (start <= line_i < end):
                skip = f"{qid}: {key} 的键行不在条目行区间内 —— 该条不动"
                break
            m = VERDICT_LINE_RE.match(lines[line_i])
            if not m or m.group("key") != key:
                skip = f"{qid}: {key} 行不是规范形态（{lines[line_i].strip()[:40]!r}）—— 该条不动"
                break
            try:
                scalar = _yaml_scalar(value)
            except ValueError as exc:
                skip = f"{qid}: {exc} —— 该条不动"
                break
            eol = "\r\n" if lines[line_i].endswith("\r\n") else ("\n" if lines[line_i].endswith("\n") else "")
            plan[line_i] = f"{m.group('pad')}{key}: {scalar}{eol}"
        if skip is not None:
            problems.append(skip)
            continue
        plans[qid] = plan
        applied.append(qid)

    edits: dict = {}
    for plan in plans.values():
        edits.update(plan)
    if not edits:
        return [], problems

    def _render(edit_map: dict) -> str:
        return "".join(edit_map.get(i, ln) for i, ln in enumerate(lines))

    # 预检：先在内存里读回，确认三个字段解析出的值与目标一致，再落盘。
    # 预处理/渲染若把文档弄坏，整批放弃（fail-closed，不落盘半个文件）。
    new_text = _render(edits)
    try:
        doc = yaml.safe_load(new_text) or {}
    except yaml.YAMLError as exc:
        return [], [*problems, f"预检解析失败 —— 放弃全部 {len(applied)} 条回写: {exc}"]
    if not isinstance(doc, dict):
        return [], [*problems, "预检：回写后顶层不是映射 —— 放弃全部回写"]
    qs = doc.get("queries")
    if not isinstance(qs, list):
        return [], [*problems, "预检：回写后 queries 不是列表 —— 放弃全部回写"]
    got = {q.get("id"): q for q in qs if isinstance(q, dict)}
    for qid in list(applied):
        q = got.get(qid) or {}
        bad = [k for k, v in updates[qid].items() if q.get(k) != v]
        if bad:
            problems.append(f"{qid}: 预检读回不一致 {bad} —— 该条放弃（不写）")
            for i in plans[qid]:
                edits.pop(i, None)
            applied.remove(qid)
    if applied:
        # 全文档不变量（r4）：除被点条目的三个字段外，解析结果必须与原文逐键一致 ——
        # 否则说明回写动到了别的东西，整批放弃。
        try:
            orig_doc = yaml.safe_load(text) or {}
        except yaml.YAMLError:  # 原文解析不了 ⇒ 无法建立不变量，整批放弃
            return [], [*problems, "预检：原文解析不了，无法建立全文档不变量 —— 放弃全部回写"]
        expected = copy.deepcopy(orig_doc)
        for q in expected.get("queries") or []:
            if isinstance(q, dict) and q.get("id") in updates:
                q.update(updates[q["id"]])
        if expected != doc:
            return [], [*problems, "预检：回写后除标注字段外还有其他解析差异 —— 放弃全部回写"]
    if edits:
        path.write_bytes(_render(edits).encode("utf-8"))
    return applied, problems


def _load_queries_strict(path: Path) -> tuple[list | None, str | None]:
    """解析金集并校验形状；坏形状返回 ``(None, 文案)``（fail-closed，不抛）。"""
    try:
        doc = load_yaml(path)
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        return None, f"读不动/解析不了（环境/输入错）: {exc}"
    if not isinstance(doc, dict):
        return None, f"顶层不是映射（环境/输入错，实测 {type(doc).__name__}）"
    qs = doc.get("queries")
    if not isinstance(qs, list) or any(not isinstance(q, dict) for q in qs):
        return None, "queries 不是映射列表（环境/输入错）"
    return qs, None


def apply_verdicts(paths: list, md: Path, verdict_by: str, verdict_at: str | None = None) -> tuple[list, list]:
    """把勾选结果**逐行**回写进 yaml。返回 ``(改动的 id 列表, 问题列表)``。

    没勾的、勾了多个的、锚找不到/对不上的、字段行缺失的 —— **一律不动那一条**
    并列进问题列表；只改三个标注字段行，其余字节原样（M-1/M-2/L-1，r3/r4）。
    默默猜一个值比不动更糟。
    """
    verdict_at = verdict_at or _now_iso()
    picks, problems = _parse_checklist_picks(md.read_text(encoding="utf-8"))
    known: set = set()
    changed: list = []
    for path in paths:
        qs_in_yaml, why = _load_queries_strict(path)
        if qs_in_yaml is None:
            problems.append(f"{path.name}: {why} —— 本文件不回写")
            continue
        ids_here = {q.get("id") for q in qs_in_yaml}
        known |= ids_here
        updates: dict = {}
        for qid, v in picks.items():
            if qid not in ids_here:
                continue
            if v not in VERDICT_ENUM:
                problems.append(f"{qid}: 勾到一个不认识的值 {v!r} —— 该条不动")
                continue
            updates[qid] = {"user_verdict": v, "verdict_by": verdict_by, "verdict_at": verdict_at}
        if updates:
            written, probs = _apply_verdict_edits(path, updates, qs_in_yaml)
            changed.extend(written)
            problems.extend(probs)
    problems.extend(f"{u}: 清单里勾了，但四份金集里找不到这个 id" for u in sorted(set(picks) - known))
    return changed, problems


# ═══════════════════════════════════════════════════════════════════════════
# collect（只读）
# ═══════════════════════════════════════════════════════════════════════════

_QUESTION_CALLOUT = re.compile(r">\s*\[!question\]\+?\s*(.*)")

#: callout **标题行**里的模板占位：Obsidian 插件写进去的锚（``%%cb-xxxx%%``）、
#: 「❓ 提问」这类固定抬头、以及「待剖析 · 源自 [[...]]」的出处行。
#: ⚠️ 本卡实测踩过：只读标题行的话，10 条候选里捞到的**全是这些模板**，
#: 一条真实提问都没有 —— 用户写的内容在 callout 的**续行**（`> ` 开头）里。
#: ⚠️ 用 ``search`` 语义而不是整行相等：实测这些抬头**带后缀**
#: （`待剖析 · 源自 [[检验白板/…]]（2026-08-11）`），整行锚定的正则一条都匹配不上。
_TEMPLATE_TITLE = re.compile(r"(❓\s*提问|待剖析|%%cb-[^%]*%%)")

#: 续行里要跳过的：勾选项（`- [ ] ✅ 已懂`）、空续行、AI 生成的出处/原因说明。
_SKIP_BODY = re.compile(r"^(-\s*\[[ x]\]|AI 判断来源|原因[:：])|^$")


def collect_candidates(vault: Path, out_json: Path) -> int:
    """**只读**扫一个 vault，把真实用户提问捞成候选。

    ⛔ 只 read_text，绝不写 ``vault`` 下的任何东西。产物只写到 ``out_json``。
    ⛔ ``--out`` 落在 ``--vault`` 内**直接拒绝**（L-3，r3）：「只读」不能只靠
    调用方自觉不把产物写进被扫的树。
    """
    vault = Path(vault).resolve()
    out_res = Path(out_json).resolve()
    try:
        out_res.relative_to(vault)
    except ValueError:
        pass
    else:
        raise ValueError(f"--out 不得落在 --vault 内（collect 只读 vault）: {out_json}")
    out_json = out_res
    cands: list = []
    for md in sorted((vault / "节点").glob("*.md")) if (vault / "节点").is_dir() else []:
        lines = md.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            m = _QUESTION_CALLOUT.match(line.strip())
            if not m:
                continue
            title = m.group(1).strip()
            # 标题行如果是模板占位（`❓ 提问 %%cb-xxxx%%` / `待剖析 · 源自 [[…]]`），
            # 真内容在续行里 —— 往下读 `> ` 续行，取第一句像提问的。
            picked, picked_line = (title, i) if title and not _TEMPLATE_TITLE.search(title) else (None, i)
            if picked is None:
                for k in range(i, min(i + 12, len(lines))):
                    body = lines[k].lstrip()
                    if not body.startswith(">"):
                        break
                    body = body[1:].strip()
                    if body and not _SKIP_BODY.search(body) and not _TEMPLATE_TITLE.search(body):
                        picked, picked_line = body, k + 1
                        break
            if picked:
                cands.append(
                    {
                        "query": picked,
                        "source": {"kind": "node", "ref": f"{md.relative_to(vault)}:{picked_line}"},
                        "why": "用户手写 [!question] callout",
                    }
                )
    for md in sorted((vault / "原白板").glob("*.md")) if (vault / "原白板").is_dir() else []:
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("# ") and line[2:].strip():
                cands.append(
                    {
                        "query": line[2:].strip(),
                        "source": {"kind": "whiteboard", "ref": f"{md.relative_to(vault)}:{i}"},
                        "why": "原白板一级标题",
                    }
                )
                break
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(cands, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK collect n={len(cands)} -> {out_json}（⛔ 候选而已，没有入集）")
    return len(cands)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="实算 sha/计数，写 manifest")
    b.add_argument("--base-commit", default="9c4e7e82")
    b.add_argument("--bump-revision", action="store_true")
    b.add_argument("--reason", default=None)

    sub.add_parser("verify", help="重算并比对；0 全符 / 1 不符 / 2 缺文件或解析错")
    sub.add_parser("census", help="打印分类映射与 verdict 计数")

    c = sub.add_parser("checklist", help="出用户裁定勾选清单")
    c.add_argument("--out", required=True)

    a = sub.add_parser("apply-verdicts", help="按隐藏锚回写勾选结果")
    a.add_argument("--from", dest="src", required=True)
    a.add_argument("--by", default="user")

    ap_approve = sub.add_parser("approve", help="用户标完后置 approved + 签字（pending 未清/签名空/verify 红 一律拒）")
    ap_approve.add_argument("--signed-by", required=True)
    ap_approve.add_argument("--at", default=None, help="签字时间（默认 now UTC）")
    ap_approve.add_argument("--checklist", default=None, help="勾选清单路径（记进 adjudication.checklist_path）")

    co = sub.add_parser("collect", help="只读扫 vault 出候选 query")
    co.add_argument("--vault", required=True, help="⛔ 必须显式给，没有默认值")
    co.add_argument("--out", required=True)

    ns = ap.parse_args(argv)

    if ns.cmd == "build":
        return build_manifest(MANIFEST_PATH, ns.base_commit, ns.bump_revision, ns.reason)
    if ns.cmd == "verify":
        rc, lines = verify_all()
        for ln in lines:
            print(ln)
        return rc
    if ns.cmd == "census":
        return census()
    if ns.cmd == "checklist":
        n = write_checklist(list(MAIN_SETS), Path(ns.out))
        print(f"OK checklist n={n} -> {ns.out}")
        return 0
    if ns.cmd == "apply-verdicts":
        changed, problems = apply_verdicts(list(MAIN_SETS), Path(ns.src), ns.by)
        for p in problems:
            print(f"SKIP {p}")
        print(f"OK apply-verdicts changed={len(changed)}")
        return 1 if problems else 0
    if ns.cmd == "approve":
        return approve_manifest(MANIFEST_PATH, ns.signed_by, ns.at, ns.checklist)
    if ns.cmd == "collect":
        try:
            collect_candidates(Path(ns.vault), Path(ns.out))
        except ValueError as exc:
            print(f"⛔ {exc}", file=sys.stderr)
            return 2
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
