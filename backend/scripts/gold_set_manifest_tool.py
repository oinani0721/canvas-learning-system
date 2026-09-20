#!/usr/bin/env python3
"""CARD-G4-13 金集 manifest 工具 —— 采集 / 标注清单 / 回写 / 冻结 / 校验。

[BATCH-2026-09-18-第十五批 / CARD-G4-13]

这个工具解决一件事：金集是检索质量门禁的**真值**，而真值一旦能被悄悄改掉，
门禁就只是在给自己打分。所以：

* ``build``   —— 实算四份金集的 sha256 / 条数 / 分类分布，写进 ``gold_set_manifest.yaml``；
* ``verify``  —— 重算并比对。**两个 runner 在跑之前都会调它**，不符就拒跑（rc=2）；
* ``census``  —— 打印分类映射与 ``user_verdict`` 计数，给验收单用；
* ``checklist`` —— 出一份**零技术词**的勾选清单，给用户在 Obsidian 里逐条裁定；
* ``apply-verdicts`` —— 把勾选结果按隐藏锚回写进 yaml；
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
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

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
    """实算并写 manifest。已冻结时必须 ``--bump-revision --reason``。"""
    revision = 1
    history = []
    if manifest_path.exists():
        old = load_yaml(manifest_path)
        if old.get("frozen") and not bump:
            print(
                f"⛔ {manifest_path.name} 已冻结（frozen: true, revision: {old.get('revision')}）。"
                "要改它请显式带 --bump-revision --reason '<为什么>' —— "
                "冻结不是不能改，是改了要留下说得出理由的痕迹。",
                file=sys.stderr,
            )
            return 1
        if bump:
            if not reason:
                print("⛔ --bump-revision 必须同时给 --reason", file=sys.stderr)
                return 1
            revision = int(old.get("revision") or 0) + 1
            history = list(old.get("revision_history") or [])
            history.append({"revision": revision, "at": _now_iso(), "reason": reason})

    files = [describe_file(p, key) for p, key in GOLD_SETS]
    main_total = sum(f["query_count"] for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS])
    attack_total = sum(
        f["by_class"].get(ATTACK_CLASS, 0) for f in files if (REPO_ROOT / f["path"]) in [p.resolve() for p in MAIN_SETS]
    )

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
        "# gold_set_manifest.yaml — CARD-G4-13 金集冻结清单（由 backend/scripts/gold_set_manifest_tool.py 生成）\n"
        "#\n"
        "# ⛔ 不要手改这个文件：sha256 / 计数都是实算的，手改只会让 verify 红。\n"
        "#    要改金集 → 改 yaml → `python scripts/gold_set_manifest_tool.py build --bump-revision --reason '...'`。\n"
        "#\n"
        "# 两个 retrieval runner 在跑之前都会调 verify_gold_set_file()；不符就拒跑（rc=2）。\n\n"
        + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"OK build revision={revision} main={main_total} attack={attack_total} -> {manifest_path.name}")
    return 0


def verify_all(manifest_path: Path | None = None) -> tuple[int, list]:
    """重算并比对。返回 ``(rc, 行列表)``。

    rc 语义与两个 runner 的既有约定一致：
    ``0`` 全符 / ``1`` 内容不符 / ``2`` 文件缺失或 yaml 解析错（= 环境/输入错）。
    """
    manifest_path = manifest_path or MANIFEST_PATH
    lines: list = []
    if not manifest_path.exists():
        return 2, [f"MISSING {manifest_path} manifest 不存在"]
    try:
        m = load_yaml(manifest_path)
    except yaml.YAMLError as exc:
        return 2, [f"UNPARSEABLE {manifest_path} {exc}"]

    rc = 0
    for entry in m.get("files") or []:
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            lines.append(f"MISSING {entry['path']} 期望存在 实测不存在")
            rc = max(rc, 2)
            continue
        try:
            doc = load_yaml(path)
        except yaml.YAMLError as exc:
            lines.append(f"UNPARSEABLE {entry['path']} {exc}")
            rc = max(rc, 2)
            continue

        actual_sha = sha256_of(path)
        if actual_sha != entry["sha256"]:
            lines.append(f"MISMATCH {entry['path']} sha256={entry['sha256']} actual={actual_sha}")
            rc = max(rc, 1)
            continue

        qs = doc.get("queries") or []
        if len(qs) != entry["query_count"]:
            lines.append(f"MISMATCH {entry['path']} query_count={entry['query_count']} actual={len(qs)}")
            rc = max(rc, 1)
            continue
        cv = (doc.get("config") or {}).get("version")
        if cv != entry.get("config_version"):
            lines.append(f"MISMATCH {entry['path']} config_version={entry.get('config_version')} actual={cv}")
            rc = max(rc, 1)
            continue

        bad = _field_problems(qs)
        if bad:
            lines.append(f"MISMATCH {entry['path']} fields_ok=True actual={bad[0]}（共 {len(bad)} 条）")
            rc = max(rc, 1)
            continue

        lines.append(f"OK {entry['path']} sha256={actual_sha[:12]}… queries={len(qs)}")
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


def verify_gold_set_file(path: Path, manifest_path: Path | None = None) -> tuple[bool, str]:
    """**两个 runner 调的就是这个**：单份金集是否与 manifest 相符。

    返回 ``(是否相符, 一行说明)``。runner 拿到 ``False`` 就打印说明并 ``return 2``。
    ⛔ 环境/输入错（manifest 解析失败 / 顶层非映射 / 已登记文件缺失 / 条目 sha 非法）
    也走 ``(False, 文案)``、**不以异常逃逸**：它是两个 runner 的 fail-closed 边界，
    崩溃会让 runner 以未捕获异常收场（exit 1 =「指标回退」档），把 rc=2
    「环境/输入错」的语义污染掉（r1 H-1；口径对齐 ``verify_all``，2026-09-19 r2 整改）。
    """
    manifest_path = manifest_path or MANIFEST_PATH
    if not manifest_path.exists():
        return False, f"manifest 不存在: {manifest_path}"
    try:
        m = load_yaml(manifest_path)
    except yaml.YAMLError as exc:
        return False, f"manifest 解析失败（环境/输入错）: {manifest_path} —— {exc}"
    if not isinstance(m, dict):
        return False, f"manifest 顶层不是映射（环境/输入错）: {manifest_path}（实测 {type(m).__name__}）"
    want = rel_to_repo(Path(path))
    if want is None:
        return False, f"{path} 在仓外 —— manifest 只登记仓内路径，无法校验"
    for entry in m.get("files") or []:
        if not isinstance(entry, dict) or entry.get("path") != want:
            continue
        if not Path(path).exists():
            return False, f"{want} 已登记但文件缺失（环境/输入错）: {path}"
        want_sha = entry.get("sha256")
        if not isinstance(want_sha, str):
            return False, f"{want} manifest 条目的 sha256 缺失或非法（环境/输入错）: {want_sha!r}"
        actual = sha256_of(Path(path))
        if actual != want_sha:
            return False, f"{want} sha256 期望 {want_sha[:12]}… 实测 {actual[:12]}…"
        return True, f"OK {want} sha256={actual[:12]}… queries={entry.get('query_count')}"
    return False, f"{want} 未登记在 manifest 里"


# ═══════════════════════════════════════════════════════════════════════════
# census
# ═══════════════════════════════════════════════════════════════════════════


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


def apply_verdicts(paths: list, md: Path, verdict_by: str, verdict_at: str | None = None) -> tuple[list, list]:
    """把勾选结果回写进 yaml。返回 ``(改动的 id 列表, 问题列表)``。

    没勾的、勾了多个的、锚找不到的 —— **一律不动那一条**并列进问题列表。
    默默猜一个值比不动更糟。
    """
    verdict_at = verdict_at or _now_iso()
    text = md.read_text(encoding="utf-8")
    picks: dict = {}
    problems: list = []

    current = None
    for line in text.splitlines():
        m = GSID_RE.search(line)
        if m:
            current = m.group(1)
            continue
        if current and line.lstrip().startswith("- [x]"):
            vm = re.search(r"<!--\s*verdict:([a-z_]+)\s*-->", line)
            if not vm:
                continue
            if current in picks:
                problems.append(f"{current}: 勾了不止一个（{picks[current]} 与 {vm.group(1)}）—— 该条不动")
                picks[current] = None
            elif picks.get(current, "") is None:
                continue
            else:
                picks[current] = vm.group(1)

    picks = {k: v for k, v in picks.items() if v}
    changed: list = []
    for path in paths:
        doc = load_yaml(path)
        qs = doc.get("queries") or []
        touched = False
        for q in qs:
            v = picks.get(q.get("id"))
            if not v:
                continue
            if v not in VERDICT_ENUM:
                problems.append(f"{q.get('id')}: 勾到一个不认识的值 {v!r} —— 该条不动")
                continue
            q["user_verdict"] = v
            q["verdict_by"] = verdict_by
            q["verdict_at"] = verdict_at
            changed.append(q.get("id"))
            touched = True
        if touched:
            _rewrite_queries_in_place(path, qs)
    unknown = sorted(set(picks) - set(changed))
    problems.extend(f"{u}: 清单里勾了，但四份金集里找不到这个 id" for u in unknown)
    return changed, problems


def _rewrite_queries_in_place(path: Path, queries: list) -> None:
    """只重写 ``queries:`` 段，**保留文件头部的注释块**（版本纪律写在那里）。"""
    text = path.read_text(encoding="utf-8")
    idx = text.index("\nqueries:")
    head = text[: idx + 1]
    body = yaml.safe_dump({"queries": queries}, allow_unicode=True, sort_keys=False, width=100)
    path.write_text(head + body, encoding="utf-8")


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
    """
    vault = Path(vault)
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
    if ns.cmd == "collect":
        collect_candidates(Path(ns.vault), Path(ns.out))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
