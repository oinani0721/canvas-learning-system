#!/usr/bin/env python3
"""CARD-G8-10 r8 —— JEV 分诊的**机器可读 sidecar manifest** 生成器（r6-L1 闭合）。

背景：`scripts/jev_review_triage.py`（jev-1.13.0）输出的 JSON 只有 code_files / files[…risk, urgency,
review, test…]，**没有** 字段级 `calls` / `verdict`（r6-L1 / r7 同型登记）。本 goal 的硬边界是
「不改 scripts/jev_review_triage.py」，故由本脚本把 ① 上游 JSON 与 ② 运行 stdout 的机器可读事实
解析并落成 sidecar：`sidecar-g810-r8-<short>.json`（字段：calls / verdict / urgency / risk / review /
test / code_files / sha / bound HEAD + 逐字段 provenance）。缺字段 ⇒ 非 0 退出（L 保持 open）。

v4.7（r9，修 r8-L2）：`code_files` 现**就地解码 git quoted/octal 形式**（`"\345\256\241"` → 真实
UTF-8 路径），并把原样保留在 `code_files_raw`。

v4.9-r20.1（r20 实测补正）：VERDICT 列大小写不敏感白名单比对（JEV 会出小写 `pass`），转录仍原样。
v4.9-r20（r19-M1 补强）：`row-file` 要求**真后缀**（`pos+len(basename) == len(首列)` 且其前为 `/` 或行首），
  `<basename>-junk` 尾串变体亦红。
v4.9-r19（r18-M1 补强）：`row-file` 由子串包含改为**路径边界后缀**（前缀须为 `/` 或行首），
  `evil-<basename>` 之类不再通过。
v4.9-r18（r17-M1 补强）：数据行首列须含 JSON `files[0]` 的文件 basename（防克隆数值 + 改名）；
  verdict 词本身只能转录 stdout（无独立来源）——该边界见 UAT §十.65。
v4.9-r17（r16-L2/M2 整改）：行筛/解析用 `str.lstrip()`（Unicode 空白）；verdict 数据行必须与 JSON `files` 互核（行数 == len(files)，首行 churn/urgency/review/test/risk 相等），不一致 ⇒ `row-*` 红。
v4.9-r16（r15-M2/M3 整改）：`Model:` / `标记人工审查:` 行计数**允许行首空白**（缩进坏行同样计数）；
  verdict 只认**数据行**（churn+三数值+风险词+判定词），表头/散文不计；非 PARTIAL 缺数据行 ⇒ `verdict-missing` 红。
v4.8（r10，修 r9-M4）：解码**带结构校验** —— 非空 / 非绝对路径 / 不含 `..` 段 / 不含 UTF-8 替换字符
（U+FFFD，= 解码失败的信号）/ 不含 NUL；任一不满足 ⇒ `path_decoded=false` + `path_validation_failures`
记录 + **非 0 退出**。另有信息字段 `path_exists_in_worktree`（相对生成时工作目录；不进退出码）。

用法: python3 g810-r8-sidecar.py --json <jev-triage-*.json> --stdout <run-*.txt> --out <sidecar.json>
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def _decode_git_path(raw: str) -> str:
    r"""git quoted/octal 路径 → 真实路径（r8-L2）。

    形如 `"a/\345\256\241.py"`：去掉包裹引号后把 `\ooo` 八进制转义变字节、其余 C 转义（\\ \" \n \t）
    还原，最后按 UTF-8 解码。非引号包裹的输入原样返回。
    """
    s = raw.strip()
    if not (s.startswith('"') and s.endswith('"') and len(s) >= 2):
        return s
    s = s[1:-1]
    out = bytearray()
    i = 0
    simple = {"n": 10, "t": 9, "r": 13, '"': 34, "\\": 92, "/": 47, "a": 7, "b": 8, "f": 12, "v": 11}
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in "01234567":
                j = i + 1
                digits = ""
                while j < len(s) and len(digits) < 3 and s[j] in "01234567":
                    digits += s[j]
                    j += 1
                out.append(int(digits, 8) & 0xFF)
                i = j
                continue
            if nxt in simple:
                out.append(simple[nxt])
                i += 2
                continue
        out.extend(c.encode("utf-8"))
        i += 1
    return out.decode("utf-8", errors="replace")


def _validate_relative_path(p: str) -> str | None:
    """解码后的路径结构校验（v4.8 / r9-M4）→ 通过返回 None，否则返回失败原因。"""
    if not p or not p.strip():
        return "空路径"
    if p.startswith("/"):
        return "绝对路径"
    if len(p) >= 2 and p[1] == ":":  # Windows 盘符
        return "绝对路径（盘符）"
    if ".." in p.split("/"):
        return "含 .. 段"
    if "\ufffd" in p:
        return "含 U+FFFD（UTF-8 解码失败残留）"
    if "\\" in p:
        return "含反斜杠（未解码的转义序列 / 非预期路径字符）"
    if "\x00" in p:
        return "含 NUL"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--stdout", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--round", default="r8")
    ap.add_argument("--allow-empty", action="store_true",
                    help="上游分诊 0 code files（例如只改 .zsh/text）⇒ 记 partial=true 的 PARTIAL 记录并以 0 退出")
    ap.add_argument("--card", default="CARD-G8-10")
    args = ap.parse_args()

    jp = Path(args.json)
    sp = Path(args.stdout)
    payload = json.loads(jp.read_text(encoding="utf-8"))
    stdout = sp.read_text(encoding="utf-8", errors="replace")

    # v4.9-r14 / r13-M4：calls 只认 `Model: … | calls: N` 机器行（防较早散文行伪装）
    # v4.9-r15 / r14-M3：`Model:` 与 `标记人工审查:` 行都必须唯一（多行 ⇒ 红，防首行 stale 掩盖）
    # v4.9-r17 / r16-L2：用 str.lstrip() 语义（Unicode 空白，含 NBSP / form-feed）筛行；解析取自同一行
    _model_lines = [l for l in stdout.splitlines() if l.lstrip().startswith("Model:")]
    _mark_lines = [l for l in stdout.splitlines() if l.lstrip().startswith("标记人工审查:")]
    _line_count_problems = []
    if len(_model_lines) != 1:
        _line_count_problems.append(f"model-line-count: Model 行 {len(_model_lines)} 条（要求洽 1）")
    if len(_mark_lines) > 1:
        _line_count_problems.append(f"marker-line-count: 标记人工审查 行 {len(_mark_lines)} 条（要求 ≤1）")
    calls_m = re.search(r"Model:\s*\S+\s*\|\s*calls:\s*(\d+)", _model_lines[0]) if len(_model_lines) == 1 else None
    model_m = re.search(r"Model:\s*([0-9A-Za-z._\-]+)", _model_lines[0]) if len(_model_lines) == 1 else None
    # v4.9-r16 / r15-M3：verdict 只认**数据行**（churn + 三个数值 + 风险词 + 判定词）；
    #   表头（FILE … RISK VERDICT）与散文不构成 verdict；非 PARTIAL 场景缺数据行 ⇒ verdict-missing 红。
    # v4.9-r17 / r16-M2：数据行除列形/白名单外，还必须与 JSON `files` **互核**
    #   （行数 == len(files)；首行的 churn/urgency/review/test/risk 与 files[0] 相等）
    _VERDICT_WORDS = ("REVIEW", "TEST", "SKIP", "PASS", "FAIL", "BLOCK", "OK")
    # v4.9-r20.1（r20 实测发现）：JEV 的 VERDICT 列会输出小写 `pass` ⇒ 白名单比对**大小写不敏感**，
    #   行末列允许混合大小写；sidecar 仍**原样转录**（不归一化）。
    _ROW_RE = re.compile(
        r"^\s*(\S.*?)\s+([+±\-]?\d+/\-?\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\w+)\s+([A-Za-z]+)\s*$",
        re.M)
    _rows = [m for m in _ROW_RE.finditer(stdout) if m.group(7).upper() in _VERDICT_WORDS]
    verdict_m = _rows[0] if _rows else None
    _row_problems: list[str] = []
    _files0 = payload.get("files") or []
    if _files0:
        if len(_rows) != len(_files0):
            _row_problems.append(f"row-count: 数据行 {len(_rows)} ≠ files {len(_files0)}")
        elif _rows:
            _m0, _f0 = _rows[0], _files0[0]
            _exp_churn = f"+{_f0.get('added')}/-{_f0.get('removed')}"
            if _m0.group(2) != _exp_churn:
                _row_problems.append(f"row-churn: {_m0.group(2)} ≠ {_exp_churn}")
            for _gi, _key in ((3, "urgency"), (4, "review"), (5, "test")):
                try:
                    if abs(float(_m0.group(_gi)) - float(_f0.get(_key))) > 5e-4:
                        _row_problems.append(f"row-{_key}: {_m0.group(_gi)} ≠ {_f0.get(_key)}")
                except (TypeError, ValueError):
                    _row_problems.append(f"row-{_key}: 无法比对（行 {_m0.group(_gi)} / JSON {_f0.get(_key)}）")
            if str(_m0.group(6)) != str(_f0.get("risk")):
                _row_problems.append(f"row-risk: {_m0.group(6)} ≠ {_f0.get('risk')}")
            # v4.9-r18 / r17-M1：行首列须含 files[0] 的文件 basename（防「克隆数值 + 改名」）
            _fn0 = ""
            _rawf0 = str(_f0.get("file") or "")
            _parts0 = [p for p in re.findall(r'"([^"]+)"', _rawf0) if p]
            if _parts0:
                _fn0 = os.path.basename(_parts0[0])
            else:
                _fn0 = os.path.basename(_rawf0.strip().split(" ")[0]) if _rawf0.strip() else ""
            # v4.9-r20 / r19-M1：首列须**真正以 basename 结尾**且其前为 `/` 或行首
            #   （`<basename>-junk` 之类尾串变体不再逃逸）
            _head0 = _m0.group(1).strip().rstrip('"')
            if _fn0:
                _pos0 = _head0.rfind(_fn0)
                _is_suffix0 = (_pos0 != -1) and (_pos0 + len(_fn0) == len(_head0))
                _boundary0 = (_pos0 == 0) or (_pos0 > 0 and _head0[_pos0 - 1] == "/")
                if not (_is_suffix0 and _boundary0):
                    _row_problems.append(
                        f"row-file: 行首列 {_head0[-60:]!r} 不以路径边界**结尾**于 files[0] basename {_fn0!r}")
    else:
        if _rows:
            _row_problems.append(f"row-extra: files=[] 但存在 {len(_rows)} 条数据行")
    _verdict_rows = len(_rows)
    marked_m = re.search(r"标记人工审查:\s*(\d+)/(\d+)", _mark_lines[0]) if len(_mark_lines) == 1 else None
    files = payload.get("files") or []
    first = files[0] if files else {}
    verdict = None
    if verdict_m is not None:
        verdict = verdict_m.group(7)      # v4.9-r20.2：VERDICT = 行末列（原样转录；不再按大小写回退取列）
    code_files_raw = [c.strip() for c in (payload.get("code_files") or [])]
    code_files = [_decode_git_path(c) for c in code_files_raw]
    path_failures = {c: r for c in code_files if (r := _validate_relative_path(c))}
    # v4.9-r13 / r12-M3：PARTIAL 必须三方一致（files=[] ∧ calls=0 ∧ code_files=[]），否则红
    _calls_now = int(calls_m.group(1)) if calls_m else None
    _marked = marked_m.group(1) + "/" + marked_m.group(2) if marked_m else None
    _marked_ok = (_marked is None) or (_marked == "0/0")     # v4.9-r14 / r13-L4
    _files_present_empty = ("files" in payload) and (payload["files"] == [])
    _cf_present_empty = ("code_files" in payload) and (payload["code_files"] == [])
    partial_ok = (not files) and _files_present_empty and (_calls_now == 0) and _cf_present_empty and _marked_ok
    partial = bool(args.allow_empty and partial_ok)
    partial_inconsistent = bool(args.allow_empty and not partial_ok)
    missing = [k for k, v in {"calls": calls_m, "verdict": verdict, "urgency": first.get("urgency"),
                              "risk": first.get("risk"), "review": first.get("review"),
                              "test": first.get("test"), "code_files": code_files or None,
                              "sha": payload.get("sha"), "bound_head": payload.get("sha")}.items()
             if v is None and not (partial and k in ("verdict", "urgency", "risk", "review", "test", "code_files"))]
    if partial:
        verdict = None          # 0 个 triaged 文件：表头 VERDICT 不算判定（PARTIAL，不得写「已审」）
    if _line_count_problems:
        missing = list(missing) + _line_count_problems
    if _row_problems:
        missing = list(missing) + _row_problems
    if verdict_m is None and not partial:
        missing = list(missing) + [f"verdict-missing: 未找到数据行（数据行数={_verdict_rows}；表头/散文不计 verdict）"]
    if partial_inconsistent:
        missing = list(missing) + [
            "<partial-inconsistent: --allow-empty 要求 fields 存在且 files=[] ∧ calls(Model 行)=0 ∧ code_files=[] ∧ 标记人工审查 0/0；"
            f"实见 files={len(files)} calls={_calls_now} code_files={len(payload.get('code_files') or [])}>"
        ]
    sidecar = {
        "card": args.card,
        "round": args.round,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "generator": "g810-r8-sidecar.py（解析上游 JSON + 运行 stdout；不改 scripts/jev_review_triage.py）",
        "tool": payload.get("model"),
        "tool_stdout_model": model_m.group(1) if model_m else None,
        "source_json": jp.name,
        "source_stdout": sp.name,
        "commit_subject": payload.get("commit"),
        "sha": payload.get("sha"),
        "bound_head": payload.get("sha"),
        "ref": payload.get("ref"),
        "calls": int(calls_m.group(1)) if calls_m else None,
        "verdict": verdict,
        "urgency": first.get("urgency"),
        "urgency_conf": first.get("urgency_conf"),
        "risk": first.get("risk"),
        "risk_conf": first.get("risk_conf"),
        "review": first.get("review"),
        "test": first.get("test"),
        "flagged": marked_m.group(1) + "/" + marked_m.group(2) if marked_m else None,
        "code_files": code_files,
        "code_files_raw": code_files_raw,
        "path_decoded": not path_failures,
        "path_validation_failures": path_failures,
        "path_exists_in_worktree": {c: Path(c).exists() for c in code_files},
        "files": files,
        "usage": payload.get("usage"),
        "latency_ms": payload.get("latency_ms"),
        "field_provenance": {
            "calls": f"stdout 机器可读行 'Model: … | calls: N'（{sp.name}）",
            "verdict": f"stdout 分诊表 VERDICT 列（{sp.name}）",
            "urgency/risk/review/test": f"上游 JSON files[0]（{jp.name}）",
            "sha/bound_head": f"上游 JSON .sha（{jp.name}）",
            "code_files": f"上游 JSON .code_files（{jp.name}）→ git quoted/octal 就地解码为真实 UTF-8 路径（raw 存 code_files_raw；结构校验见 path_validation_failures）",
        },
        "field_missing": missing,
        "partial": partial,
        "partial_inconsistent": partial_inconsistent,
        "partial_reason": ("JEV 分诊 0 code files（本 commit 只改 .zsh/UAT 等非 triaged 文件）⇒ 按卡文口径记 PARTIAL，不得写「已审」"
                           if partial else None),
        "note": "r6-L1 闭合证据：本 sidecar 是**字段级机器可读**的（calls / verdict / urgency / risk / review / test / code_files / sha / bound HEAD）；上游 JSON 缺 calls/verdict，故由 stdout 解析补足并在 field_provenance 注明来源；r8-L2/r9-M4 后 code_files 为解码 + 结构校验过的相对路径（校验失败 ⇒ path_decoded=false 且非 0 退出）。",
    }
    Path(args.out).write_text(json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        f"sidecar={args.out} calls={sidecar['calls']} verdict={sidecar['verdict']} urgency={sidecar['urgency']} "
        f"risk={sidecar['risk']} sha={sidecar['sha']} field_missing={missing} path_decoded={sidecar['path_decoded']} "
        f"path_validation_failures={path_failures}"
    )
    return 1 if (missing or path_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
