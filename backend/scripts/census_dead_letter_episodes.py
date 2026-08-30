#!/usr/bin/env python3
"""CARD-G4-9: dead-letter episodes 只读 census 分诊脚本。

BATCH-2026-08-28-第五批 / CARD-G4-9（G4-10 replay 的交接台账生成器）。

只读契约（grep 可自证 + 运行时守卫）:
  - 无 --apply / 无任何写回、重放、删除路径；
  - 不 import neo4j / graphiti / app.*（纯 stdlib），不建立任何网络连接；
    qa_metrics.db 的访问方式见 ``probe_qa_metrics`` docstring —— 源文件以
    ``O_RDONLY|O_NOFOLLOW`` 读取后灌入**内存库**，不经路径打开、不写源文件
    （**不使用** URI ``mode=ro``；该表述已于 round-9 废弃）；
  - 本进程**唯一有意的写动作**是产出 --out 台账 JSON（经 O_EXCL 临时文件 +
    原子替换发布；全文无任何截断调用）。⚠️ 这不等于"在任意环境下不可能有
    其它写入"——已知边界见下方"安全边界"段。写前双重碰撞守卫：resolve() 路径比较 +
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

安全边界（round-9/10 收敛，如实声明而非绝对化断言）:
  - **可确证**: 对本次运行列出的输入文件（--dlq / --compare / --qa-metrics-db），
    运行前后 shasum 逐字节不变（证据包留存本次一对 before/after）；
    ``test_census_dead_letter_readonly_contract.py`` 中**每条行为测试各自断言的
    那一个具体场景** fail-closed —— 这是逐例证据，**不构成**"所有误用路径均
    fail-closed"的整体证明。
  - **不声称**: 在共享可写目录、存在并发写者、SQLite DB 正被写入等敌意环境下
    的生产级安全。已知残余：lstat→replace 竞态、非一致性 DB 快照、tmp 名可
    预测、无单写者锁（分别移交 FU-A~FU-D，G4-10 复用前须补齐）。
  - **前提**: "DB 静止"由操作者保证 —— 0 行 / 固定 sha / 前后同 SHA 本身
    **不能证明**读取期间没有并发写者。

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
import hashlib
import json
import os
import re
import sqlite3
import stat
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


def _path_is_within(target: str, root: str) -> bool:
    """target 是否落在 root 目录内 —— 逐级向上比较 **inode 身份**。

    round-7 BLOCKER 整改: 不能用路径字符串前缀判断 —— 大小写不敏感卷上
    ``/Users/x`` 与 ``/users/x`` 的 realpath 字符串不同但 samefile=True，
    prefix guard 会漏。本实现从 target 逐级取父目录，只要任一级与 root 同
    (st_dev, st_ino) 即判定在其内；target 尚不存在时上溯到存在的祖先。
    """
    try:
        root_st = os.stat(root)
    except OSError:
        return False
    root_id = (root_st.st_dev, root_st.st_ino)
    cur = os.path.realpath(target)
    while True:
        try:
            st = os.stat(cur)
            if (st.st_dev, st.st_ino) == root_id:
                return True
        except OSError:
            pass  # 该级尚不存在（--out 待创建），继续上溯
        parent = os.path.dirname(cur)
        if parent == cur:
            return False
        cur = parent


def _same_file(a: str, b: str) -> bool:
    """按 inode 身份比较两个路径（不依赖字符串大小写/规范化）。"""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _split_jsonl_lines(raw: bytes) -> list[tuple[str, str | None]]:
    """按 JSONL 规范只以 LF 分帧，返回 [(line_text, decode_error_or_None)]。

    - 不用 splitlines(): U+2028/U+2029/裸 CR 会误分行（round-3）。
    - 逐行 **strict** decode（round-4 MEDIUM 整改）: errors="replace" 会把非法
      UTF-8 静默改写成合法对象，让坏字节冒充有效记录。解码失败的行带错误信息
      返回，由调用方归入 unparseable。
    """
    had_trailing_lf = raw.endswith(b"\n")
    if had_trailing_lf:
        raw = raw[:-1]
    if not raw:
        # round-5 LOW 整改: 单独 b"\n" 是一个空行，不是 0 行
        return [("", None)] if had_trailing_lf else []
    out: list[tuple[str, str | None]] = []
    for chunk in raw.split(b"\n"):
        try:
            out.append((chunk.decode("utf-8"), None))
        except UnicodeDecodeError as e:
            out.append(("", f"utf8_decode_error: {e}"))
    return out


def classify(rec: dict) -> str:
    et = rec.get("error_type", "")
    if not isinstance(et, str):
        return "unexpected"
    if et == "EntityTypeValidationError":
        return "schema_entity_type"
    if et == "GroupIdValidationError":
        return "group_id_format"
    if et == "BadRequestError" and _BUDGET_PAT.search(str(rec.get("error", ""))):
        return "budget_400"
    return "unexpected"


def inline_state(rec: dict) -> tuple[str, str]:
    """返回 (inline_state, sha_check)，fail-closed（见模块 docstring）。"""
    body = rec.get("episode_body", "")
    if not isinstance(body, str):  # round-4 LOW: episode_body 错型
        return "anomaly", "FAIL"
    declared_len = rec.get("episode_body_length")
    declared_sha = rec.get("episode_body_sha256", "")
    sha_wellformed = isinstance(declared_sha, str) and bool(_SHA256_HEX_PAT.match(declared_sha))
    # round-5 LOW 整改: errors="replace" 会把 JSON escaped lone surrogate
    # (\udXXX) 改写成 replacement char，可被构造出"对得上账"的假 full_verified。
    # 改 strict：无法编码即判 anomaly。
    try:
        body_bytes = body.encode("utf-8")
    except UnicodeEncodeError:
        return "anomaly", "FAIL"
    recomputed = hashlib.sha256(body_bytes).hexdigest()
    len_ok = isinstance(declared_len, int) and not isinstance(declared_len, bool)
    if sha_wellformed and recomputed == declared_sha and len_ok and len(body) == declared_len:
        return "full_verified", "pass"
    if sha_wellformed and len(body) == 200 and len_ok and declared_len > 200:
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
    # round-5 LOW 整改: bool 是 int 子类 —— episode_body_length=True 会通过长度门
    if not isinstance(declared_len, int) or isinstance(declared_len, bool) or len(full) != declared_len:
        return False
    try:
        full_bytes = full.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return hashlib.sha256(full_bytes).hexdigest() == declared_sha


def session_tokens(name: object) -> list[str]:
    """round-4 LOW 整改: name 非 str（None/数字/列表）不再抛异常。"""
    if not isinstance(name, str):
        return []
    tokens = []
    m = _SESSION_ARCHIVE_PAT.match(name)
    if m:
        tokens.append(m.group(1).lower())
    tokens.extend(t.lower() for t in _SESSION_INLINE_PAT.findall(name))
    return tokens


def resolve_group_attribution(tokens: list[str], transcripts_dir: Path) -> dict:
    """组级归因，fail-closed。

    round-5 BLOCKER① 整改: **先扫描后判定**。原实现在 token 冲突/无 token 时
    扫描前早退，导致这些候选从未进入 all_candidate_paths → 不进 --out 保护集
    → 可被无竞态截断。现无条件对每个 token 扫描收集候选（保护集所需），
    再做冲突/唯一性判定。
    """
    result = {
        "session_token": None,
        "transcript_paths": [],
        "transcript_exists": False,
        "transcript_match_count": 0,
        "attribution_conflict": False,
        # 保护集必须覆盖**所有见到的候选**（含不可读、含被冲突分支排除的）
        "all_candidate_paths": [],
    }
    uniq = sorted(set(tokens), key=len)

    root_str = str(transcripts_dir)
    walk_errors: list[str] = []

    def _on_walk_error(err: OSError) -> None:
        walk_errors.append(f"{getattr(err, 'filename', '?')}: {err}")

    # 单次遍历收集**每个 token** 的候选（无条件，供保护集与判定共用）
    per_token: dict[str, list[str]] = {t: [] for t in uniq}
    all_candidates: list[str] = []
    unreadable: list[str] = []
    stat_failures: list[str] = []
    # round-6 整改: **无论有无 token 都遍历** —— no_token 时原实现完全不扫描，
    # all_candidate_paths 为空，该组见不到的候选就进不了保护集。
    for dirpath, _dirnames, filenames in os.walk(transcripts_dir, onerror=_on_walk_error, followlinks=False):
        for fname in filenames:
            if fname.endswith(".jsonl"):
                matched = [t for t in uniq if fname.startswith(t)]
                candidate = os.path.join(dirpath, fname)
                # 候选一律入 all_candidate_paths（保护集口径），再谈可用性
                all_candidates.append(candidate)
                if not matched:
                    continue
                try:
                    if os.path.islink(candidate) or not os.path.isfile(candidate):
                        continue
                except OSError as e:
                    stat_failures.append(f"{candidate}: {e}")
                    continue
                if not os.access(candidate, os.R_OK):
                    unreadable.append(candidate)
                    continue
                if not _path_is_within(candidate, root_str):
                    continue  # 目录 symlink 逃逸（inode 身份判定）
                for t in matched:
                    per_token[t].append(candidate)
    result["all_candidate_paths"] = sorted(set(all_candidates))

    # round-8 HIGH 整改: 早退分支也必须携带扫描错误 —— 否则 no_token /
    # token_conflict 组的 walk 错误不会进入 scan_blocked 判定。
    if walk_errors:
        result["scan_errors"] = walk_errors[:5]
    if stat_failures:
        result["stat_failures"] = stat_failures[:5]

    if not uniq:
        # 无 token: 未做任何归因扫描 —— 不是"确认无源"（round-5 MEDIUM 整改）
        result["attribution_conflict"] = True
        result["no_token"] = True
        return result

    longest = uniq[-1]
    if any(not longest.startswith(t) for t in uniq[:-1]):
        result["attribution_conflict"] = True
        result["token_conflict"] = True
        return result
    result["session_token"] = longest

    if walk_errors:
        result["scan_errors"] = walk_errors[:5]
        result["attribution_conflict"] = True
        return result
    if stat_failures:
        result["stat_failures"] = stat_failures[:5]
        result["attribution_conflict"] = True
        return result
    if unreadable:
        result["unreadable_candidates"] = unreadable[:5]
        result["attribution_conflict"] = True
        return result

    matches = sorted(set(per_token[longest]))
    result["transcript_paths"] = matches
    result["transcript_match_count"] = len(matches)
    if len(matches) == 1:
        result["transcript_exists"] = True
    elif len(matches) > 1:
        result["attribution_conflict"] = True  # ambiguous 多命中，拒绝采信
    return result


def probe_qa_metrics(db_path: Path, error_types: list[str]) -> tuple[dict, tuple[int, int] | None]:
    """只读核销 qa_metrics.db。返回 (结果, 实际读取对象身份)。

    ⚠️ **只读语义的准确表述（round-9 必需项⑤，名实一致 DD-13）**：只读保证来自
    ①源文件以 ``O_RDONLY|O_NOFOLLOW`` 打开、全程不写该 fd；②读出的字节灌入
    **内存库**，与源文件完全解耦。内存连接本身在 SQLite 语义下可写（另设
    ``PRAGMA query_only=ON`` 作纵深防御），**不再声称 URI ``mode=ro``**。
    字段名为 ``source_fd_opened_readonly`` 而非 ``opened_readonly``。

    已知边界（round-9 必需项①，如实登记为 follow-up 而非声称已解决）：分块读
    raw bytes **不等于数据库一致性快照** —— 若源 DB 正被并发写入或存在 WAL /
    journal 旁文件，读到的字节可能是撕裂状态。本卡运行时假定 DB 静止，该假定
    **由操作者保证**（行数为 0、字节数固定、前后 SHA 相同都**不能证明**读取
    期间没有并发写者）。若 G4-10 复用本脚本于活跃 DB，须改用 SQLite backup
    API 或要求外部先冻结。

    round-8 BLOCKER①② 整改: 不再让 SQLite 按 **路径** 打开 —— 那既有 URI 转义
    问题（路径含 ``?``/``#`` 时 ``mode=ro`` 会落进被忽略的 fragment，SQLite 可能
    按默认读写模式打开），又有 A→B→A 的 ABA（验证 fd 是 A，connection 却可能读
    到 B）。改为从**已验证的 fd** 读全量字节 → ``sqlite3`` 内存库
    ``deserialize``：全程不经路径、不落任何文件，两个问题一并消失。
    """
    result: dict = {"db_path": str(db_path), "source_fd_opened_readonly": False}
    if not db_path.exists():
        result["verdict"] = "db_missing"
        return result, None
    try:
        fd = os.open(db_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as e:
        result["verdict"] = f"open_refused: {e}"
        return result, None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            result["verdict"] = "not_regular_file_refused"
            return result, None
        identity = (st.st_dev, st.st_ino)
        # round-10 整改: 字段语义即"源 fd 是否以只读方式成功打开"——
        # 此刻已成立，不得等到 deserialize 成功才置真（DB malformed 时
        # fd 确实已只读打开，返回 false 属名实不符）。
        result["source_fd_opened_readonly"] = True
        chunks = []
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            chunks.append(block)
        db_bytes = b"".join(chunks)
        result["bytes_read_from_verified_fd"] = len(db_bytes)
    finally:
        os.close(fd)

    conn = None
    try:
        conn = sqlite3.connect(":memory:")
        conn.deserialize(db_bytes)
    except Exception as e:  # noqa: BLE001 — 非法/加密 DB 如实记录，不中断 census
        result["verdict"] = f"deserialize_failed: {str(e)[:80]}"
        if conn is not None:
            conn.close()
        return result, identity

    try:
        result["file_identity_verified"] = True
        result["read_mode"] = "in_memory_deserialize_from_verified_fd"
        result["source_sha256"] = hashlib.sha256(db_bytes).hexdigest()
        # R9 建议项: 内存连接本身可写（deserialize 语义），显式设 query_only
        # 以匹配"只读核销"的语义 —— 但真正的只读保证来自**源 fd 只读 + 内存
        # 副本与源文件完全解耦**，query_only 只是纵深防御。
        conn.execute("PRAGMA query_only=ON")
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
    except sqlite3.Error as e:
        # round-10 整改（实测）: deserialize 是**延迟验证** —— malformed DB 的
        # DatabaseError 在首次 execute 时才抛出，原 try 只有 finally 没有
        # except，会炸掉整次 census。查询段一律 fail-closed 记录不中断。
        result["verdict"] = f"query_failed: {str(e)[:80]}"
    finally:
        conn.close()
    return result, identity


def snapshot_file(path: Path) -> tuple[bytes, dict, tuple[int, int]]:
    """一次性读全量 bytes；sha/行数/身份全部派生自**同一个 fd**。

    round-4 BLOCKER② 整改: 原实现按路径 stat 采集保护身份、稍后才按路径读取，
    两步之间对象可被换掉（源侧 TOCTOU）。现改为打开一次 fd → fstat 取身份 →
    从该 fd 读全量，返回的 (st_dev, st_ino) 即**实际被读取对象**的身份。
    """
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(f"不是常规文件（拒绝 FIFO/设备/目录）: {path}")
        identity = (st.st_dev, st.st_ino)
        chunks = []
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            chunks.append(block)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    info = {
        "path": str(path),
        "exists": True,
        # round-3 整改: JSONL 的行分隔符**只有** \n —— splitlines() 会把
        # U+2028/U+2029/裸 CR 也当分隔符，可能把一条 JSON 记录劈成两半。
        # 与 records 同口径按 \n 切分（末尾换行不算空行）。
        "line_count": len(_split_jsonl_lines(raw)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "mtime_note": "mtime 取自读取用 fd 的 fstat；绑定 exact bytes 的是 sha256",
    }
    return raw, info, identity


def describe_copy(path: Path) -> tuple[dict, tuple[int, int] | None]:
    """返回 (描述, 实际读取对象身份)；身份用于并入 --out 保护集。"""
    if not path.exists():
        return {"path": str(path), "exists": False}, None
    _, info, identity = snapshot_file(path)
    return info, identity


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

    protected_ids: set[tuple[int, int]] = set()
    # round-6 BLOCKER①② 架构整改: inode 保护集依赖**枚举完整性**（不可列举的
    # 子目录、ABA 换 inode 都能让某个真实源不进集合）。故增加**不依赖枚举**的
    # 路径层防御：--out 的 realpath 不得落在 transcripts 根内、不得等于任一
    # 输入路径。路径层 + inode 层双保险，任一命中即拒绝。
    if args.out:
        # round-7 BLOCKER 整改: 用 **inode 身份逐级比较**（_path_is_within），
        # 不用路径字符串前缀 —— normcase 在 POSIX 上是恒等函数，大小写不敏感
        # 卷上的别名根（/Users vs /users）realpath 字符串不同但 samefile=True。
        # round-8 BLOCKER③ 整改: rename/replace **不解析末级 symlink**（POSIX），
        # 故 --out 若是根内的 symlink（指向根外），realpath 会判"根外"而放行，
        # 但 replace 实际替换的是根内那个目录项。判定改用**父目录**语义 +
        # lstat 末级：父目录在根内 → 拒绝；末级本身是 symlink 也按其所在目录判。
        out_parent = os.path.dirname(os.path.abspath(args.out)) or "."
        if _path_is_within(out_parent, args.transcripts_dir) or _path_is_within(args.out, args.transcripts_dir):
            print(
                f"--out 落在 transcripts 根内（恢复源区域），无条件拒绝写出: {args.out}",
                file=sys.stderr,
            )
            return 2
        input_paths = [args.dlq, *args.compare] + ([args.qa_metrics_db] if args.qa_metrics_db else [])
        if any(_same_file(args.out, ip) for ip in input_paths):
            print(f"--out 与输入文件为同一对象（inode 比较），拒绝写出: {args.out}", file=sys.stderr)
            return 2

    # --out 碰撞守卫（写前）。round-2 BLOCKER-1 整改: 比较**文件身份**
    # (st_dev, st_ino) 而非 resolve() 字符串 —— 后者对 hardlink 与
    # 大小写不敏感文件系统上的 case-only 别名均失效（Codex 实测截断输入）。
    if args.out:
        out_path = Path(args.out)
        protected_paths = [dlq_path, *(Path(p) for p in args.compare)]
        if args.qa_metrics_db:
            protected_paths.append(Path(args.qa_metrics_db))
        for candidate in protected_paths:
            try:
                cst = candidate.stat()  # 跟随 symlink: 保护的是最终目标身份
                protected_ids.add((cst.st_dev, cst.st_ino))
            except OSError:
                # round-4 整改: stat 失败不再静默吞 —— 无法确认身份即 fail-closed
                print(f"输入文件无法 stat，拒绝继续（无法建立完整保护集）: {candidate}", file=sys.stderr)
                return 2
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
    try:
        raw_bytes, dlq_info, dlq_identity = snapshot_file(dlq_path)
    except OSError as e:
        print(f"DLQ 无法安全读取: {dlq_path} ({e})", file=sys.stderr)
        return 2
    protected_ids.add(dlq_identity)  # 保护的是**实际读取对象**，非路径快照
    raw_lines = _split_jsonl_lines(raw_bytes)

    records: list[tuple[int, dict]] = []
    unparseable: list[dict] = []
    for line_no, (line, decode_err) in enumerate(raw_lines, start=1):
        if decode_err is not None:
            unparseable.append({"line_no": line_no, "reason": decode_err})
            continue
        if not line.strip():
            unparseable.append({"line_no": line_no, "reason": "blank_line"})
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            unparseable.append({"line_no": line_no, "reason": f"json_error: {e}", "excerpt": line[:80]})
            continue
        # round-3 LOW 整改: 合法 JSON 但非对象（null / 数组 / 标量）此前解析成功
        # 却在 rec.get() 处抛 AttributeError 炸掉全量 —— 归入 unparseable。
        if not isinstance(rec, dict):
            unparseable.append(
                {"line_no": line_no, "reason": f"not_a_json_object: {type(rec).__name__}", "excerpt": line[:80]}
            )
            continue
        records.append((line_no, rec))

    # request_id 分组: (类型名, 值) 复合键；缺失/None → 按 line_no 单条成组
    groups: dict[tuple, list[tuple[int, dict]]] = defaultdict(list)
    for line_no, rec in records:
        rid = rec.get("request_id")
        # round-4 LOW 整改: 不可哈希的 request_id（list/dict）按 line_no 单条成组
        try:
            hash(rid)
            hashable = True
        except TypeError:
            hashable = False
        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
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
    unverifiable_keys = []
    attribution_conflicts = []
    for line_no, rec in records:
        cls = classify(rec)
        state, sha_check = inline_state(rec)
        rid = rec.get("request_id")
        try:
            hash(rid)
            hashable = True
        except TypeError:
            hashable = False
        key = ("__missing__", line_no) if (rid is None or not hashable) else (type(rid).__name__, rid)
        sess = group_attribution[key]
        if state == "full_verified":
            recover = "byte_exact"
            basis = "inline 正文全量：sha256 重算与声明一致且长度精确匹配"
        elif state != "anomaly" and full_body_verified(rec):
            recover = "byte_exact"
            basis = "episode_body_full 在盘且 sha256+长度双门对账通过（DEAD_LETTER_STORE_FULL_BODY 生产 opt-in 字段）"
        elif sess["attribution_conflict"]:
            # round-5 HIGH 整改: 可见性判定**优先于** anomaly —— 源看不见时
            # 无论 inline 是什么状态，都不能断言"不可恢复"。
            recover = "unverifiable"
            if sess.get("no_token"):
                why = "记录名未携带 session token，未做任何归因扫描"
            elif sess.get("token_conflict"):
                why = "同组多 token 前缀冲突"
            elif sess.get("scan_errors"):
                why = "扫描遍历受阻（不可读子树）"
            elif sess.get("stat_failures"):
                why = "候选 stat 失败"
            elif sess.get("unreadable_candidates"):
                why = "存在不可读候选"
            else:
                why = "transcript 多命中 ambiguous"
            extra = "；inline 亦对不上账（anomaly）" if state == "anomaly" else ""
            basis = f"源可见性不足，拒绝裁定：{why}{extra}。既不宣称可恢复，也不宣称不可恢复（fail-closed）"
        elif state == "anomaly":
            recover = "unrecoverable"
            basis = "inline 对不上账（anomaly：sha/长度与声明不符），且归因扫描完整可见但无可用源"
        elif sess["transcript_exists"]:
            recover = "approximate"
            basis = (
                f"inline 为 200 字符前缀（前缀性质依赖 to_dict()[:200] 生产不变量，sha 无法直接证明）；"
                f"经 request_id 组归因到唯一在盘 transcript {sess['session_token']}"
                f"（归因 ≠ 内容已验证——本工具未读 transcript 内容；G4-10 可重蒸馏/重格式化近似重建，非逐字节保证）"
            )
        else:
            recover = "unrecoverable"
            basis = "inline 截断；归因扫描完整可见（无遍历错误/无不可读候选）但未找到任何在盘上游源"
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
        elif recover == "unverifiable":
            unverifiable_keys.append(stable_key)
        if sess["attribution_conflict"]:
            attribution_conflicts.append(stable_key)
        ledger_records.append(
            {
                "stable_key": stable_key,
                "name": str(rec.get("name", ""))[:80],
                "group_id": rec.get("group_id"),
                "source_description": rec.get("source_description"),
                "error_type": rec.get("error_type"),
                "error_excerpt": str(rec.get("error", ""))[:120],
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
                # round-6 LOW 整改: ledger 自描述冲突原因，G4-10 可区分
                # 缺 token / token 冲突 / 扫描受阻 / 不可读 / 多命中
                "attribution_conflict_reason": (
                    "no_token"
                    if sess.get("no_token")
                    else "token_conflict"
                    if sess.get("token_conflict")
                    else "scan_errors"
                    if sess.get("scan_errors")
                    else "stat_failures"
                    if sess.get("stat_failures")
                    else "unreadable_candidates"
                    if sess.get("unreadable_candidates")
                    else "ambiguous_multi_match"
                    if sess["attribution_conflict"]
                    else None
                ),
                "recoverability": recover,
                "recoverability_basis": basis,
            }
        )

    # 语义重复簇（同 name + 全文 sha + group_id）——G4-10 重放去重策略依据
    cluster_map: dict[tuple, list[int]] = defaultdict(list)
    for line_no, rec in records:
        cluster_map[
            (str(rec.get("name", "")), str(rec.get("episode_body_sha256", "")), str(rec.get("group_id")))
        ].append(line_no)
    duplicate_clusters = [
        {"name": k[0][:80], "episode_body_sha256": k[1], "group_id": k[2], "line_nos": v, "occurrences": len(v)}
        for k, v in sorted(cluster_map.items(), key=lambda kv: -len(kv[1]))
        if len(v) > 1
    ]

    compare_infos = []
    for cp in args.compare:
        cinfo, cid = describe_copy(Path(cp))
        compare_infos.append(cinfo)
        if cid is not None:
            protected_ids.add(cid)

    if args.qa_metrics_db:
        qa_probe, qa_identity = probe_qa_metrics(
            Path(args.qa_metrics_db),
            [str(r.get("error_type", "")) for _, r in records],
        )
        if qa_identity is not None:
            protected_ids.add(qa_identity)  # 保护实际验证过的对象身份
    else:
        qa_probe = {"verdict": "skipped_no_db_arg"}

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
        "compare_copies": compare_infos,
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
            k: recover_dist.get(k, 0) for k in ["byte_exact", "approximate", "unverifiable", "unrecoverable"]
        },
        "inline_state_distribution": {
            k: inline_dist.get(k, 0) for k in ["full_verified", "truncated_prefix", "anomaly"]
        },
        "unrecoverable_list": unrecoverable_keys,
        "unverifiable_list": unverifiable_keys,
        "attribution_conflicts": attribution_conflicts,
        "duplicate_clusters": duplicate_clusters,
        "qa_metrics_probe": qa_probe,
        "records": ledger_records,
    }

    # round-3 BLOCKER-1 绕过① 整改: 归因到的 transcript 是恢复源，
    # --out 指向它同样会截断。写出前并入保护集（此时归因已完成）。
    # round-7 整改: 扫描受阻 ⇒ 保护集必然不完整（隐藏目录内的源看不见）。
    # 仅在台账标 unverifiable 不够 —— 直接拒绝写出，避免在保护集残缺时落盘。
    scan_blocked = [
        (k, v.get("scan_errors") or v.get("stat_failures"))
        for k, v in group_attribution.items()
        if v.get("scan_errors") or v.get("stat_failures")
    ]
    # round-8 HIGH 整改: 去掉 `and args.out` —— stdout 模式同样不得在保护集
    # 残缺时输出台账（否则 --out 省略即绕过该门）。
    if scan_blocked:
        print(
            f"transcripts 扫描受阻（{len(scan_blocked)} 组），保护集不完整，拒绝写出台账；首例: {scan_blocked[0][1]}",
            file=sys.stderr,
        )
        return 2

    for sess_info in group_attribution.values():
        for tpath in sess_info.get("all_candidate_paths", []):
            try:
                tst = os.stat(tpath)
                protected_ids.add((tst.st_dev, tst.st_ino))
            except OSError as e:
                # round-5 整改: 候选 stat 失败不再静默吞 —— 保护集不完整即拒绝写出
                print(f"候选源无法 stat，保护集不完整，拒绝写出: {tpath} ({e})", file=sys.stderr)
                return 2
    for rec_out in ledger_records:
        for tpath in rec_out.get("transcript_paths", []):
            try:
                tst = os.stat(tpath)
                protected_ids.add((tst.st_dev, tst.st_ino))
            except OSError:
                continue

    try:
        out_json = json.dumps(ledger, ensure_ascii=False, indent=1)
        out_json.encode("utf-8")  # round-7 LOW: 编码错误必须在写出前暴露
    except (UnicodeEncodeError, ValueError):
        # name/error/group_id 等字段若含 escaped lone surrogate，UTF-8 写出会抛错。
        # 回退 ensure_ascii=True（\uXXXX 转义，ASCII 安全）并在台账显式标注。
        ledger["json_encoding_note"] = "ensure_ascii=True fallback: 某字段含无法 UTF-8 编码的字符（lone surrogate）"
        out_json = json.dumps(ledger, ensure_ascii=True, indent=1)
    if args.out:
        # round-7 架构整改: 不再截断既有文件 —— 同目录 O_EXCL 新建临时文件 →
        # 写 → fsync → os.replace 原子替换。脚本从不 ftruncate 任何既有 inode，
        # 因此"截断某个既有对象"这条**具体路径**不再存在（已由回归测试就
        # hardlink / 根内 symlink / FIFO 三个场景各自取证）。⚠️ 这不等于
        # 声称"所有别名类绕过都已失效"—— lstat→replace 竞态等残余见模块
        # docstring 的安全边界段与 FU-B/FU-C。同时消除崩溃/ENOSPC 留部分台账。
        out_path = Path(args.out)
        # round-9 整改（由新增回归测试抓出的 round-7 架构回归）: 改用
        # replace 发布后不再打开 --out，S_ISREG 门随之丢失 —— os.replace 会
        # **静默替换任何类型的目标**（FIFO/设备/socket/symlink）。此处补回：
        # --out 若已存在且不是常规文件，或是 symlink（replace 替换链接本身
        # 而非其目标，与用户意图不符），一律拒绝。
        try:
            out_lst = os.lstat(out_path)
        except FileNotFoundError:
            out_lst = None
        except OSError as e:
            print(f"--out 无法 lstat，拒绝写出: {out_path} ({e})", file=sys.stderr)
            return 2
        if out_lst is not None:
            if stat.S_ISLNK(out_lst.st_mode):
                print(f"--out 是 symlink（replace 会替换链接本身），拒绝写出: {out_path}", file=sys.stderr)
                return 2
            if not stat.S_ISREG(out_lst.st_mode):
                print(f"--out 已存在且不是常规文件（FIFO/设备/目录/socket），拒绝写出: {out_path}", file=sys.stderr)
                return 2
        tmp_path = out_path.with_name(f".{out_path.name}.census-tmp-{os.getpid()}")
        try:
            tmp_fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except OSError as e:
            print(f"临时台账文件无法新建（O_EXCL）: {tmp_path} ({e})", file=sys.stderr)
            return 2
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8", closefd=False) as f:
                f.write(out_json + "\n")
                f.flush()
                os.fsync(tmp_fd)
        except Exception as e:
            os.close(tmp_fd)
            os.unlink(tmp_path)
            print(f"台账写入失败，已清理临时文件: {e}", file=sys.stderr)
            return 2
        os.close(tmp_fd)
        # 原子替换 + 父目录 fsync（round-8 MEDIUM 整改：replace 纳入 try，
        # EXDEV/EBUSY/EACCES/ENOSPC 等异常一律清理 tmp 不留残留）。
        try:
            os.replace(tmp_path, out_path)
            dir_fd = os.open(out_path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError as e:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            print(f"台账原子替换失败，已清理临时文件: {e}", file=sys.stderr)
            return 2
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
