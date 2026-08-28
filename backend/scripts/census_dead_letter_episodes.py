#!/usr/bin/env python3
"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。

BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。

只读契约（grep 可自证 + 运行时守卫）:
  - 无 --apply / 无任何写回、重放、删除路径；
  - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何数据库/网络连接，
    唯一的 sqlite 访问经 URI ``mode=ro`` 只读打开 qa_metrics.db；
  - 唯一写出口是 --out 台账 JSON，写前双重碰撞守卫：resolve() 路径比较 +
    **文件身份 (st_dev, st_ino) 比较**，与 --dlq/--compare/--qa-metrics-db
    任一输入重合即 exit 2，防 "w" 截断输入（round-1 BLOCKER-1 + round-2
    hardlink / 大小写别名绕过整改）。

快照原子性（Codex round-1 BLOCKER-2 整改）:
  - DLQ 文件只读一次（bytes），头部 sha256/line_count 与逐条 records 全部
    派生自同一份内存字节 —— 台账头部声明的 sha 即 records 所来自的 exact bytes。

判定 fail-closed（Codex round-1 HIGH-1/2/3 整改）:
  - inline 三态: full_verified 要求 sha 对账通过 **且** len(body)==声明长度;
    truncated_prefix 要求声明 sha 为格式合法的 64-hex **且** len(body)==200
    且声明长度>200; 其余一律 anomaly。anomaly 不落 approximate —— 裁
    unrecoverable 并显式给 anomaly basis（不谎称"截断前缀"）。
    注: truncated_prefix 无法用 sha 证明 200 字符确为全文前缀 —— 该性质
    依赖 EpisodeTask.to_dict() 的 [:200] 生产不变量（episode_worker.py），
    台账 recoverability_basis 如实声明。
  - request_id 分组: 键为 (类型名, 值)，缺失/None 记录按 line_no 单条成组
    （不与字面 "None" 或跨类型值合组，杜绝跨 session 误归因传染）。
  - session 归因: 组内多 token 必须满足前缀一致（短 token 是最长 token 的
    前缀），否则记 attribution_conflict、拒绝采信任何 transcript；
    transcript glob 命中必须**恰好 1 个常规文件**才算归因成功，多命中记
    ambiguous 同样拒绝采信；transcripts 根**不存在或不可读/不可遍历**
    （chmod 000）时整体 exit 2（拒绝在源不可见时产出 unrecoverable 假象）；
    glob 结果拒绝 symlink 条目与逃逸到根外的目标（round-2 HIGH-3 整改）。
  - DLQ 坏 JSON 行不再炸掉全量: 逐行捕获，class=unparseable 保留 line_no
    进台账（分诊工具不能被单行毒药拒诊）。
  - episode_body_full 若在盘（DEAD_LETTER_STORE_FULL_BODY 开启时生产可写):
    重算 sha **且长度**双门对账通过才按 byte_exact 采信，且 anomaly 记录
    不得经此分支翻案（round-1 MEDIUM-1 + round-2 HIGH-1 整改）。

逐条产出（G4-10 消费契约）:
  - stable_key: {line_no, sha256_prefix(16 hex), request_id}。语义 =
    **冻结快照内的 occurrence key**（台账头部 dlq_file.sha256 即快照指纹；
    line_no 在该快照内已唯一，另两列为冗余对账/诊断维度）——不是跨文件
    重排或语义幂等键，G4-10 消费前先 diff 头部 sha。
  - reference_time 逐条透传 + duplicate_clusters 段（同 name+sha+group 的
    语义重复簇），G4-10 重放去重策略依据（Codex round-1 MEDIUM-2 整改）。
  - 隐私: transcript_paths 含本机用户名与 session UUID，台账为 private-only
    工件，禁止外发（Codex round-1 MEDIUM-3；仓库为私有仓，纪律=不 push 公网）。
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# 分类规则: error_type + error 文本特征 → class
_BUDGET_PAT = re.compile(r"exceed_context_size_error|exceeds the available context size")
# session token: request_id 组内从 name 提取。已知局限（如实声明）: 纯启发式，
# hex 样单词（added/deadbeef）可污染 inline 捕获 —— 下游有前缀一致门 + 恰 1 命中门兜底。
_SESSION_ARCHIVE_PAT = re.compile(r"^session-archive:([0-9a-fA-F-]+)")
_SESSION_INLINE_PAT = re.compile(r"(?<![0-9a-zA-Z_-])session:([0-9a-f-]{5,})")
_SHA256_HEX_PAT = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_CLASS_DIST = {"budget_400": 89, "schema_entity_type": 2, "group_id_format": 1}


def classify(rec: dict) -> str:
    et = rec.get("error_type", "")
    if et == "EntityTypeValidationError":
        return "schema_entity_type"
    if et == "GroupIdValidationError":
        return "group_id_format"
    if et == "BadRequestError" and _BUDGET_PAT.search(rec.get("error", "")):
        return "budget_400"
    return "unexpected"


def inline_state(rec: dict) -> tuple[str, str]:
    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
    body = rec.get("episode_body", "")
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
    recomputed = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    if sha_wellformed and recomputed == declared_sha and len(body) == declared_len:
        return "full_verified", "pass"
    if sha_wellformed and len(body) == 200 and isinstance(declared_len, int) and declared_len > 200:
        return "truncated_prefix", "prefix_only"
    return "anomaly", "FAIL"


def full_body_verified(rec: dict) -> bool:
    """episode_body_full 在盘且 sha **与长度**双门对账通过（生产 opt-in 字段，当前 live 0 条）。

    round-2 HIGH-1 整改: 原实现只核 sha，声明长度矛盾的记录（如 body="abc"
    但 episode_body_length=999）仍被判 byte_exact —— 与 inline 侧同门收紧。
    """
    full = rec.get("episode_body_full")
    declared_sha = rec.get("episode_body_sha256", "")
    declared_len = rec.get("episode_body_length")
    if not isinstance(full, str) or not _SHA256_HEX_PAT.match(str(declared_sha)):
        return False
    if not isinstance(declared_len, int) or len(full) != declared_len:
        return False
    return hashlib.sha256(full.encode("utf-8", errors="replace")).hexdigest() == declared_sha


def session_tokens(name: str) -> list[str]:
    tokens = []
    m = _SESSION_ARCHIVE_PAT.match(name)
    if m:
        tokens.append(m.group(1).lower())
    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
    return tokens


def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
    """组级归因，fail-closed: 前缀一致门 + 恰 1 个常规文件命中门。"""
    result = {
        "session_token": None,
        "transcript_paths": [],
        "transcript_exists": False,
        "transcript_match_count": 0,
        "attribution_conflict": False,
    }
    uniq = sorted(set(tokens), key=len)
    if not uniq:
        return result
    longest = uniq[-1]
    if any(not longest.startswith(t) for t in uniq[:-1]):
        result["attribution_conflict"] = True
        return result
    result["session_token"] = longest
    pattern = str(transcripts_dir / "**" / f"{longest}*.jsonl")
    # round-2 HIGH-3 整改: 拒绝 symlink 条目与逃逸到根外的目标 —— 原实现
    # 经 glob+isfile 跟随 symlink，根内 .jsonl→根外 .txt 会被当唯一来源采信。
    root_real = os.path.realpath(transcripts_dir)
    matches = []
    for candidate in glob.glob(pattern, recursive=True):
        if os.path.islink(candidate) or not os.path.isfile(candidate):
            continue
        real = os.path.realpath(candidate)
        if not real.startswith(root_real + os.sep):
            continue  # 目录 symlink 逃逸
        matches.append(candidate)
    matches = sorted(matches)
    result["transcript_paths"] = matches
    result["transcript_match_count"] = len(matches)
    if len(matches) == 1:
        result["transcript_exists"] = True
    elif len(matches) > 1:
        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
    return result


def probe_qa_metrics(db_path: Path, error_types: list[str]) -> dict:
    """只读核销 qa_metrics.db 能否作为源指针（URI mode=ro，无写路径）。"""
    result: dict = {"db_path": str(db_path), "opened_readonly": False}
    if not db_path.exists():
        result["verdict"] = "db_missing"
        return result
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        result["opened_readonly"] = True
        tables = [
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        ]
        result["tables"] = tables
        if "qa_error_logs" in tables:
            total = conn.execute("SELECT COUNT(*) FROM qa_error_logs").fetchone()[0]
            result["qa_error_logs_rows"] = total
            hits = {}
            for et in sorted(set(error_types)):
                hits[et] = conn.execute("SELECT COUNT(*) FROM qa_error_logs WHERE error_type = ?", (et,)).fetchone()[0]
            result["error_type_hits"] = hits
            result["verdict"] = "no_source_rows" if total == 0 else "rows_present_see_hits"
        else:
            result["verdict"] = "qa_error_logs_table_missing"
    finally:
        conn.close()
    return result


def snapshot_file(path: Path) -> tuple[bytes, dict]:
    """一次性读全量 bytes；描述信息（sha/行数/mtime）全部派生自这份 exact bytes。"""
    raw = path.read_bytes()
    info = {
        "path": str(path),
        "exists": True,
        # round-2 LOW 整改: 与 records 的 splitlines() 同口径（bare CR / U+2028
        # 等行分隔符下 count("\n") 会与 records 数不一致）。
        "line_count": len(raw.decode("utf-8", errors="replace").splitlines()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        "mtime_note": "mtime 为 stat 快照，仅供参考；绑定 exact bytes 的是 sha256",
    }
    return raw, info


def describe_copy(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}
    _, info = snapshot_file(path)
    return info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--dlq",
        default="data/dead_letter_episodes.jsonl",
        help="DLQ JSONL 路径（census 对 live 挂载运行时传绝对路径）",
    )
    ap.add_argument(
        "--qa-metrics-db",
        default=None,
        help="qa_metrics.db 路径（省略则跳过源指针核销并如实标注 skipped）",
    )
    ap.add_argument(
        "--transcripts-dir",
        default=os.path.expanduser("~/.claude/projects"),
        help="session transcript 根目录（近似恢复源指针核销；不存在则 exit 2 拒诊）",
    )
    ap.add_argument(
        "--compare",
        action="append",
        default=[],
        help="其它 DLQ 副本路径（可重复，产出 sha 对照表）",
    )
    ap.add_argument("--out", default=None, help="台账 JSON 输出路径（省略则打 stdout）")
    args = ap.parse_args(argv)

    dlq_path = Path(args.dlq)
    if not dlq_path.exists():
        print(f"DLQ 文件不存在: {dlq_path}", file=sys.stderr)
        return 2

    transcripts_dir = Path(args.transcripts_dir)
    if not transcripts_dir.is_dir():
        print(
            f"transcripts 根目录不存在/不可见: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
            file=sys.stderr,
        )
        return 2
    # round-2 HIGH-3 整改: 存在但不可读/不可遍历的根（chmod 000）此前 exit 0
    # 并把全部记录假判 unrecoverable —— 同样 fail-closed 拒诊。
    if not os.access(transcripts_dir, os.R_OK | os.X_OK):
        print(
            f"transcripts 根目录不可读/不可遍历: {transcripts_dir} —— 拒绝在源不可见时裁定可恢复性（fail-closed）",
            file=sys.stderr,
        )
        return 2

    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
    if args.out:
        out_path = Path(args.out)
        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
        if args.qa_metrics_db:
            protected_paths.append(Path(args.qa_metrics_db))
        protected_ids = set()
        for candidate in protected_paths:
            try:
                st = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
                protected_ids.add((st.st_dev, st.st_ino))
            except OSError:
                continue
        # 路径字符串比较作为第二道（输出文件尚不存在时 stat 无身份可比）
        out_resolved = out_path.resolve()
        if out_resolved in {p.resolve() for p in protected_paths}:
            print(f"--out 与输入文件路径重合，拒绝写出（防截断）: {out_resolved}", file=sys.stderr)
            return 2
        if out_path.exists():
            try:
                out_st = out_path.stat()
            except OSError as e:
                print(f"--out 无法 stat，拒绝写出: {out_path} ({e})", file=sys.stderr)
                return 2
            if (out_st.st_dev, out_st.st_ino) in protected_ids:
                print(
                    f"--out 与输入文件为同一 inode（hardlink/大小写别名），拒绝写出（防截断）: {out_path}",
                    file=sys.stderr,
                )
                return 2

    # BLOCKER-2 整改: 单次读取，records 与头部描述共享同一份 exact bytes
    raw_bytes, dlq_info = snapshot_file(dlq_path)
    raw_lines = raw_bytes.decode("utf-8", errors="replace").splitlines()

    records: list[tuple[int, dict]] = []
    unparseable: list[dict] = []
    for line_no, line in enumerate(raw_lines, start=1):
        if not line.strip():
            unparseable.append({"line_no": line_no, "reason": "blank_line"})
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
            continue
        records.append((line_no, rec))

    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
    for line_no, rec in records:
        rid = rec.get("request_id")
        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
        groups[key].append((line_no, rec))
    group_attribution: dict[tuple, dict] = {}
    for key, members in groups.items():
        tokens: list[str] = []
        for _, rec in members:
            tokens.extend(session_tokens(rec.get("name", "")))
        group_attribution[key] = resolve_group_attribution(tokens, transcripts_dir)

    ledger_records = []
    class_dist: Counter = Counter()
    recover_dist: Counter = Counter()
    inline_dist: Counter = Counter()
    unrecoverable_keys = []
    attribution_conflicts = []
    for line_no, rec in records:
        cls = classify(rec)
        state, sha_check = inline_state(rec)
        rid = rec.get("request_id")
        key = ("__missing__", line_no) if rid is None else (type(rid).__name__, rid)
        sess = group_attribution[key]
        if state == "full_verified":
            recover = "byte_exact"
            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
        elif state != "anomaly" and full_body_verified(rec):
            # round-2 HIGH-1 整改: anomaly 记录不得经 full_body 分支翻案
            recover = "byte_exact"
            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
        elif state == "anomaly":
            recover = "unrecoverable"
            basis = "inline 对不上账（anomaly：sha/长度与声明不符），fail-closed 不采信截断前缀假设，也不采信 transcript 归因"
        elif sess["attribution_conflict"]:
            recover = "unrecoverable"
            basis = "session 归因冲突/多命中（fail-closed 拒绝采信任何 transcript），且 inline 仅截断前缀"
        elif sess["transcript_exists"]:
            recover = "approximate"
            basis = (
                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
            )
        else:
            recover = "unrecoverable"
            basis = "inline 截断且无在盘上游源"
        class_dist[cls] += 1
        recover_dist[recover] += 1
        inline_dist[state] += 1
        stable_key = {
            "line_no": line_no,
            "sha256_prefix": str(rec.get("episode_body_sha256", ""))[:16],
            "request_id": rid,
        }
        if recover == "unrecoverable":
            unrecoverable_keys.append(stable_key)
        if sess["attribution_conflict"]:
            attribution_conflicts.append(stable_key)
        ledger_records.append(
            {
                "stable_key": stable_key,
                "name": rec.get("name", "")[:80],
                "group_id": rec.get("group_id"),
                "source_description": rec.get("source_description"),
                "error_type": rec.get("error_type"),
                "error_excerpt": rec.get("error", "")[:120],
                "failed_at": rec.get("failed_at"),
                "reference_time": rec.get("reference_time"),
                "class": cls,
                "episode_body_length": rec.get("episode_body_length"),
                "episode_body_sha256": rec.get("episode_body_sha256"),
                "inline_state": state,
                "sha_check": sha_check,
                "session_token": sess["session_token"],
                "transcript_paths": sess["transcript_paths"],
                "transcript_match_count": sess["transcript_match_count"],
                "attribution_conflict": sess["attribution_conflict"],
                "recoverability": recover,
                "recoverability_basis": basis,
            }
        )

    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
    cluster_map: dict[tuple, list[int]] = defaultdict(list)
    for line_no, rec in records:
        cluster_map[(rec.get("name", ""), rec.get("episode_body_sha256", ""), rec.get("group_id"))].append(line_no)
    duplicate_clusters = [
        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
        if len(v) > 1
    ]

    qa_probe = (
        probe_qa_metrics(
            Path(args.qa_metrics_db),
            [r.get("error_type", "") for _, r in records],
        )
        if args.qa_metrics_db
        else {"verdict": "skipped_no_db_arg"}
    )

    deviation = {
        k: {"expected": EXPECTED_CLASS_DIST.get(k, 0), "actual": class_dist.get(k, 0)}
        for k in sorted(set(class_dist) | set(EXPECTED_CLASS_DIST))
        if EXPECTED_CLASS_DIST.get(k, 0) != class_dist.get(k, 0)
    }

    ledger = {
        "card": "CARD-G4-9",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "privacy": "private-only: transcript_paths 含本机用户名与 session UUID，禁止外发/公网发布",
        "stable_key_semantics": (
            "冻结快照（dlq_file.sha256）内的 occurrence key；line_no 在快照内唯一，"
            "sha256_prefix/request_id 为冗余对账维度——非跨文件重排或语义幂等键"
        ),
        "dlq_file": dlq_info,
        "compare_copies": [describe_copy(Path(p)) for p in args.compare],
        "total_lines": len(raw_lines),
        "total_records": len(records),
        "unparseable_lines": unparseable,
        # round-2 LOW 整改: 固定 schema 补零，消费者无需自行补齐缺席键
        "class_distribution": {
            k: class_dist.get(k, 0) for k in ["budget_400", "schema_entity_type", "group_id_format", "unexpected"]
        },
        "expected_class_distribution": EXPECTED_CLASS_DIST,
        "class_deviation": deviation,
        "recoverability_distribution": {
            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unrecoverable"]
        },
        "inline_state_distribution": {
            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
        },
        "unrecoverable_list": unrecoverable_keys,
        "attribution_conflicts": attribution_conflicts,
        "duplicate_clusters": duplicate_clusters,
        "qa_metrics_probe": qa_probe,
        "records": ledger_records,
    }

    out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")
        print(f"台账已写入: {args.out}")
    else:
        print(out_json)

    print(
        f"census: {len(records)} 条 (+{len(unparseable)} unparseable) | class={dict(class_dist)} | "
        f"recoverability={dict(recover_dist)} | 归因冲突={len(attribution_conflicts)} | "
        f"重复簇={len(duplicate_clusters)} | 偏差={deviation or '无'} | "
        f"qa_metrics 核销={qa_probe.get('verdict')}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
