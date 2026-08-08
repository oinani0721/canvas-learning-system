# Canvas Learning System — Vault Index Orchestrator
# RAG-S1-2026-08-02 阶段 1: 索引正确性重写
#
# 统一索引原语层。此前写侧是两条互不相通的链: LanceDBIndexService (debounce
# 调度层, 只服务 Canvas 节点 + wikilink 图, 从不写 vault_notes) 与
# LanceDBClient.index_single_file/index_vault_notes (真写库原语, 只有手动
# HTTP 全量一条活路) — 增量索引从未真正存在, 索引自 2026-07-11 冻结 22 天。
#
# 本模块职责 (ChatGPT 第一轮 §三 P0-A, 用户 2026-08-02 批准):
#   - should_index / upsert / remove / reconcile / full_rebuild 五原语统一
#   - durable per-path pending: 同 path 覆盖、异 path 绝不互相取消、
#     索引中新事件标 dirty 完成后重放、入队即持久 (意图日志, 非失败日志)
#   - 双机制触发: watchfiles 文件事件加速 (best-effort) + 周期指纹
#     anti-entropy 扫描兜底 (正确性主力, SLO 由它确定性保证)
#   - freshness 遥测: last_index_at / pending_depth / lag_seconds / stale
#
# SLO: 保存后 60s 可检索 (事件路径 ~10s); 删除后 60s 不可检索;
#      lag > VAULT_INDEX_STALE_AFTER_S 即申报 stale。
#
# [Source: _bmad-output/研究/2026-08-02-RAG阶段1-索引重写实施计划.md]
# [Source: _bmad-output/审查/2026-08-02-ChatGPT-RAG三P0审查吸收与验证.md §三]

import asyncio
import fnmatch
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Add backend/lib to sys.path for agentic_rag imports (same idiom as
# rag_service.py / note_search_tools.py).
_backend_root = Path(__file__).parent.parent.parent  # app/services/ -> backend/
_lib_path = str(_backend_root / "lib")
if _lib_path not in sys.path:
    sys.path.insert(0, _lib_path)

_MAX_ATTEMPTS = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PendingEntry:
    """One durable per-path index intent."""

    rel_path: str
    op: str  # "upsert" | "delete"
    state: str = "pending"  # "pending" | "in_flight" | "failed"
    attempts: int = 0
    enqueued_at: str = ""
    force: bool = False  # bypass fingerprint skip (full_rebuild)
    dirty: bool = False  # new event arrived while in_flight -> replay
    # Code-Review M1: exponential backoff gate. "failed" is NOT a terminal
    # state — it means "attempts exhausted, retrying on a long backoff"
    # (poison files self-heal instead of retrying 3x every scan forever).
    next_retry_at: str = ""

    def retry_due(self, now_iso: str) -> bool:
        return not self.next_retry_at or self.next_retry_at <= now_iso

    def to_json(self) -> Dict[str, Any]:
        return {
            "rel_path": self.rel_path,
            "op": self.op,
            "state": self.state,
            "attempts": self.attempts,
            "enqueued_at": self.enqueued_at,
            "force": self.force,
            "dirty": self.dirty,
            "next_retry_at": self.next_retry_at,
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "PendingEntry":
        return cls(
            rel_path=str(data.get("rel_path", "")),
            op=str(data.get("op", "upsert")),
            state=str(data.get("state", "pending")),
            attempts=int(data.get("attempts", 0)),
            enqueued_at=str(data.get("enqueued_at", "")),
            force=bool(data.get("force", False)),
            dirty=bool(data.get("dirty", False)),
            next_retry_at=str(data.get("next_retry_at", "")),
        )


class VaultIndexOrchestrator:
    """Single write-side entry point for the vault_notes LanceDB index."""

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self._pending: Dict[str, PendingEntry] = {}
        self._pending_file = Path(__file__).parent.parent / "data" / "vault_index_pending.jsonl"
        self._client: Optional[Any] = None
        self._client_lock = asyncio.Lock()
        self._wake = asyncio.Event()
        self._stopping = False
        self._tasks: List[asyncio.Task] = []
        self._last_index_at: Optional[datetime] = None
        self._last_reconcile_at: Optional[datetime] = None
        self._force_fts_once = False  # M5: set by recover(), cleared on rebuild
        self._excluded_count = 0  # OBS-4: blacklist exclusions since start
        self._excluded_logged: set = set()  # rate-limit: one log per path

        from app.config import settings

        self._chunk_size = getattr(settings, "VAULT_INDEX_CHUNK_SIZE", 500)
        self._chunk_overlap = getattr(settings, "VAULT_INDEX_OVERLAP", 50)
        self._scan_interval = getattr(settings, "VAULT_INDEX_SCAN_INTERVAL_S", 60)
        self._stale_after = getattr(settings, "VAULT_INDEX_STALE_AFTER_S", 300)
        self._skip_dirs = [d.strip() for d in settings.VAULT_INDEX_SKIP_DIRS.split(",") if d.strip()]

    # ------------------------------------------------------------------
    # client / subject helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> Any:
        """Write-side LanceDBClient, lazily connected WITHOUT the CPU
        vectorizer preload (Ollama batch is the primary embed path) and
        WITHOUT startup dimension checks (read-path drop side effect)."""
        if self._client is not None:
            return self._client
        async with self._client_lock:
            if self._client is None:
                from agentic_rag.clients import LanceDBClient
                from agentic_rag.config import LANCEDB_CONFIG

                client = LanceDBClient(db_path=LANCEDB_CONFIG["db_path"])
                if not client.connect_lightweight() or client._db is None:
                    raise RuntimeError(f"orchestrator: LanceDB connect failed (db_path={LANCEDB_CONFIG['db_path']})")
                self._client = client
        return self._client

    def _subject(self) -> str:
        """Row-level subject tag — same derivation as the full-scan endpoint
        (G-DEFAULT fix): vault:<vault_id> group, never DEFAULT_GROUP_ID."""
        from app.config import get_current_vault_id, sanitize_vault_id
        from app.core.subject_config import build_vault_group_id

        return build_vault_group_id(sanitize_vault_id(get_current_vault_id()))

    # ------------------------------------------------------------------
    # should_index — blacklist single source
    # ------------------------------------------------------------------

    def should_index(self, rel_path: str) -> Tuple[bool, str]:
        """Decide whether a vault-relative path belongs in the notes index.

        Returns (ok, reason). reason is a machine-readable slug used by the
        structured API status (accepted/excluded/...).
        """
        rel_path = rel_path.replace("\\", "/").lstrip("/")
        if not rel_path.endswith(".md"):
            return False, "not_markdown"

        from agentic_rag.clients.lancedb_client import DEFAULT_VAULT_SKIP_FILES

        for part in rel_path.split("/")[:-1]:
            if any(fnmatch.fnmatch(part, pat) for pat in self._skip_dirs):
                return False, "blacklisted_dir"
        base_name = os.path.basename(rel_path)
        if any(fnmatch.fnmatch(base_name, pat) for pat in DEFAULT_VAULT_SKIP_FILES):
            return False, "blacklisted_file"
        return True, "ok"

    # ------------------------------------------------------------------
    # durable pending
    # ------------------------------------------------------------------

    def enqueue(
        self,
        op: str,
        rel_path: str,
        force: bool = False,
        reset_backoff: bool = False,
        persist: bool = True,
    ) -> str:
        """Add an index intent. Returns structured status:
        accepted | coalesced | excluded.

        Deletes are NEVER excluded by the blacklist — rows for a path may
        exist in the table from before that path was blacklisted, and
        removing them must always be possible.

        reset_backoff: True for REAL user events (watcher/API save) — clears
        the M1 failure backoff so an edited file retries immediately. The
        periodic reconcile pass keeps it False, otherwise it would defeat
        the backoff every scan (poison-file retry storm).
        persist: batch callers (reconcile) pass False and persist once at
        the end — per-call full-file rewrite is O(N²) during bursts (H4).
        """
        # Code-Review M3: path traversal guard — the old chain was inert so
        # "../../x.md" was harmless; this chain really writes the index.
        # Absolute paths are rejected BEFORE any normalization strips the
        # leading slash (order matters: lstrip-then-isabs never fires).
        raw = rel_path.replace("\\", "/")
        if os.path.isabs(raw):
            return "excluded"
        rel_path = os.path.normpath(raw).replace("\\", "/")
        if not rel_path or rel_path == "." or rel_path.startswith(".."):
            return "excluded"

        if op == "upsert":
            ok, _reason = self.should_index(rel_path)
            if not ok:
                return "excluded"

        existing = self._pending.get(rel_path)
        if existing is not None:
            # Same path: overwrite intent, keep earliest enqueued_at (lag
            # must measure from the OLDEST unserved intent).
            existing.op = op
            existing.force = existing.force or force
            if reset_backoff:
                existing.attempts = 0
                existing.next_retry_at = ""
                if existing.state == "failed":
                    existing.state = "pending"
            if existing.state == "in_flight":
                existing.dirty = True
            if persist:
                self._persist_sync()
            self._wake.set()
            return "coalesced"

        self._pending[rel_path] = PendingEntry(
            rel_path=rel_path,
            op=op,
            enqueued_at=_utcnow().isoformat(),
            force=force,
        )
        if persist:
            self._persist_sync()
        self._wake.set()
        return "accepted"

    def _persist_sync(self) -> None:
        """Atomically rewrite the pending JSONL (tmp + os.replace).

        The pending set is small (bounded by files changed between worker
        passes), so full rewrite is simpler and safer than append-compact.
        """
        try:
            self._pending_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._pending_file.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                for entry in self._pending.values():
                    fh.write(json.dumps(entry.to_json(), ensure_ascii=False) + "\n")
            os.replace(tmp, self._pending_file)
        except Exception as e:
            logger.error(f"[RAG-S1] pending persist failed: {e}")

    def recover(self) -> int:
        """Load durable pending on startup. in_flight -> pending (the crash
        interrupted them mid-index; delete-before-insert makes replay safe)."""
        if not self._pending_file.exists():
            return 0
        recovered = 0
        try:
            with open(self._pending_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = PendingEntry.from_json(json.loads(line))
                    except Exception:
                        continue
                    if not entry.rel_path:
                        continue
                    if entry.state == "in_flight":
                        entry.state = "pending"
                    entry.dirty = False
                    self._pending[entry.rel_path] = entry
                    recovered += 1
        except Exception as e:
            logger.error(f"[RAG-S1] pending recovery failed: {e}")
        if recovered:
            # M5: the pre-crash batch may have committed rows + fingerprints
            # without its final FTS rebuild — force one on the next batch.
            self._force_fts_once = True
            self._wake.set()
        return recovered

    # ------------------------------------------------------------------
    # worker
    # ------------------------------------------------------------------

    async def process_batch(self) -> Dict[str, int]:
        """Drain current pending entries once. Batch semantics:
        - fingerprints prefetched once (F4)
        - FTS rebuilt once per batch, only if rows changed
        - dirty entries are re-queued, not lost
        """
        now_iso = _utcnow().isoformat()
        batch = [e for e in list(self._pending.values()) if e.state in ("pending", "failed") and e.retry_due(now_iso)]
        if not batch:
            return {"processed": 0, "chunks": 0, "failed": 0}

        client = await self._get_client()
        table = client.resolve_table_name("vault_notes")
        fps = client._get_all_fingerprints()
        subject = self._subject()

        processed = 0
        failed = 0
        chunks = 0
        # Code-Review M5: after crash recovery, replayed entries may hit the
        # "fingerprint unchanged" skip while the pre-crash batch never got its
        # FTS rebuild — force one rebuild for the first post-recovery batch.
        rows_changed = self._force_fts_once

        for entry in batch:
            if self._stopping:
                break
            # in_flight is a memory-only state (H4): persisting it bought
            # nothing — recovery already replays interrupted entries, and
            # delete-before-insert makes the replay idempotent.
            entry.state = "in_flight"
            try:
                if entry.op == "delete":
                    client._delete_file_chunks(table, entry.rel_path)
                    client._remove_fingerprint(entry.rel_path)
                    rows_changed = True
                else:
                    abs_path = os.path.join(self.vault_path, entry.rel_path)
                    if not os.path.isfile(abs_path):
                        # File vanished between enqueue and processing —
                        # honest semantics: treat as delete, never silent skip.
                        client._delete_file_chunks(table, entry.rel_path)
                        client._remove_fingerprint(entry.rel_path)
                        rows_changed = True
                    else:
                        n = await client.index_single_file(
                            file_path=abs_path,
                            table_name="vault_notes",
                            subject=subject,
                            vault_path=self.vault_path,
                            max_tokens=self._chunk_size,
                            overlap_tokens=self._chunk_overlap,
                            rebuild_fts=False,
                            known_fingerprints={} if entry.force else fps,
                            skip_dirs=self._skip_dirs,
                        )
                        chunks += n
                        if n > 0:
                            rows_changed = True

                processed += 1
                self._last_index_at = _utcnow()
                if entry.dirty:
                    # New event arrived mid-index — replay from scratch.
                    # force is deliberately KEPT (L2): a full_rebuild intent
                    # must survive the replay or the file escapes re-embedding.
                    entry.dirty = False
                    entry.state = "pending"
                    entry.attempts = 0
                    entry.next_retry_at = ""
                else:
                    self._pending.pop(entry.rel_path, None)
            except Exception as e:
                failed += 1
                entry.attempts += 1
                entry.state = "pending" if entry.attempts < _MAX_ATTEMPTS else "failed"
                # M1: exponential backoff, capped at 1h — poison files retry
                # hourly (self-healing) instead of 3x per scan forever.
                backoff_s = min(3600, 60 * (2**entry.attempts))
                entry.next_retry_at = (_utcnow() + timedelta(seconds=backoff_s)).isoformat()
                logger.error(
                    f"[RAG-S1] index {entry.op} failed for {entry.rel_path} "
                    f"(attempt {entry.attempts}, next retry in {backoff_s}s): {e}"
                )

        # H4: one persist per batch. Crash between entries only loses
        # "completed" markers — replaying completed entries is idempotent
        # (fingerprint hit = skip), so durability is preserved at O(N) cost.
        self._persist_sync()

        if rows_changed:
            client._rebuild_fts_index(table)
            self._force_fts_once = False

        if processed or failed:
            logger.info(
                f"[RAG-S1] batch done: processed={processed} chunks={chunks} "
                f"failed={failed} pending_left={len(self._pending)}"
            )
        return {"processed": processed, "chunks": chunks, "failed": failed}

    async def _worker_loop(self) -> None:
        while not self._stopping:
            try:
                await self._wake.wait()
                self._wake.clear()
                await self.process_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[RAG-S1] worker loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

    # ------------------------------------------------------------------
    # reconcile / full rebuild
    # ------------------------------------------------------------------

    def _scan_vault_md_files(self) -> List[str]:
        """Walk the vault applying the SAME blacklist as should_index."""
        from agentic_rag.clients.lancedb_client import DEFAULT_VAULT_SKIP_FILES

        md_files: List[str] = []

        def _skipped_dir(name: str) -> bool:
            return any(fnmatch.fnmatch(name, pat) for pat in self._skip_dirs)

        def _skipped_file(name: str) -> bool:
            return any(fnmatch.fnmatch(name, pat) for pat in DEFAULT_VAULT_SKIP_FILES)

        for root, dirs, files in os.walk(self.vault_path):
            dirs[:] = [d for d in dirs if not _skipped_dir(d)]
            for f in files:
                if f.endswith(".md") and not _skipped_file(f):
                    md_files.append(os.path.join(root, f))
        return md_files

    async def reconcile(self, force: bool = False) -> Dict[str, int]:
        """Anti-entropy pass: fingerprint diff -> enqueue. This is the SLO
        backstop — even with every file event lost, one pass brings the
        index back in sync within the scan interval."""
        client = await self._get_client()
        # H4: the scan (os.walk + full-vault SHA256) and orphan sweep (full
        # table read) are synchronous/blocking — run them off the event loop
        # so HTTP reads never stall behind a reconcile pass.
        md_files = await asyncio.to_thread(self._scan_vault_md_files)
        new_rel, changed_rel, deleted_rel = await asyncio.to_thread(
            client._get_changed_files, self.vault_path, md_files
        )

        # H4: burst enqueue with persist=False — one durable write at the end
        # instead of O(N) full-file rewrites (O(N²) bytes) per pass.
        enqueued = 0
        if force:
            for fp in md_files:
                rel = os.path.relpath(fp, self.vault_path).replace("\\", "/")
                if self.enqueue("upsert", rel, force=True, persist=False) in (
                    "accepted",
                    "coalesced",
                ):
                    enqueued += 1
        else:
            for rel in list(new_rel) + list(changed_rel):
                if self.enqueue("upsert", rel, persist=False) in (
                    "accepted",
                    "coalesced",
                ):
                    enqueued += 1
        for rel in deleted_rel:
            if self.enqueue("delete", rel, persist=False) in (
                "accepted",
                "coalesced",
            ):
                enqueued += 1

        # Orphan sweep: rows whose path is now blacklisted or gone from disk
        # but NOT tracked by the (fresh, vault-scoped) fingerprint table — the
        # fingerprint diff can only see paths it has fingerprints for. Without
        # this, rows indexed before a blacklist change (e.g. the 2026-07-11
        # chunks/merged.md era) linger forever. Guarantees convergence:
        # table contents ⊆ currently-indexable set.
        orphans = 0
        try:
            # _find_orphan_rows is PURE (no enqueue/no Event) so it is safe
            # in a worker thread; enqueue happens back on the event loop.
            orphan_paths = await asyncio.to_thread(self._find_orphan_rows, client)
            for rel in orphan_paths:
                if self.enqueue("delete", rel, persist=False) in (
                    "accepted",
                    "coalesced",
                ):
                    orphans += 1
            enqueued += orphans
        except Exception as e:
            logger.warning(f"[RAG-S1] orphan sweep failed (non-fatal): {e}")

        if enqueued:
            self._persist_sync()

        self._last_reconcile_at = _utcnow()
        result = {
            "scanned": len(md_files),
            "new": len(new_rel),
            "changed": len(changed_rel),
            "deleted": len(deleted_rel),
            "orphans": orphans,
            "enqueued": enqueued,
        }
        if enqueued:
            logger.info(f"[RAG-S1] reconcile: {result}")
        return result

    def _find_orphan_rows(self, client: Any) -> List[str]:
        """PURE scan (thread-safe, no enqueue): table rows whose path should
        no longer be indexed — blacklisted since indexing, or gone from disk
        without a fingerprint record. Caller enqueues deletes on the loop."""
        table = client.resolve_table_name("vault_notes")
        if client._db is None or table not in client._db.table_names():
            return []
        try:
            table_paths = set(client._db.open_table(table).to_pandas()["canvas_file"].dropna().unique())
        except Exception:
            return []

        orphans: List[str] = []
        for rel in table_paths:
            if not rel:
                continue
            ok, _reason = self.should_index(rel)
            on_disk = os.path.isfile(os.path.join(self.vault_path, rel))
            if not ok or not on_disk:
                orphans.append(rel)
        return orphans

    async def full_rebuild(self) -> Dict[str, int]:
        """Re-embed every file WITHOUT dropping the table (阶段 1 偏离 1:
        全量 = 增量的极限情形 — delete-before-insert per file keeps the
        table serving reads throughout; orphan rows are cleaned by the
        deleted-files branch of the same pass)."""
        return await self.reconcile(force=True)

    # ------------------------------------------------------------------
    # freshness telemetry
    # ------------------------------------------------------------------

    def _task_states(self) -> Dict[str, str]:
        """OBS-1 (2026-08-09): per-task liveness — `any(not done)` could not
        tell WHICH loop died (two dead tasks still reported running=True)."""
        states: Dict[str, str] = {}
        for t in self._tasks:
            name = t.get_name()
            if not t.done():
                states[name] = "alive"
                continue
            try:
                exc = t.exception()
            except asyncio.CancelledError:
                states[name] = "cancelled"
                continue
            states[name] = f"error:{type(exc).__name__}" if exc else "done"
        return states

    def freshness(self) -> Dict[str, Any]:
        now = _utcnow()
        oldest: Optional[datetime] = None
        for entry in self._pending.values():
            if entry.state == "failed":
                continue
            try:
                ts = datetime.fromisoformat(entry.enqueued_at)
            except Exception:
                continue
            if oldest is None or ts < oldest:
                oldest = ts
        lag_seconds = (now - oldest).total_seconds() if oldest else 0.0
        failed = sum(1 for e in self._pending.values() if e.state == "failed")

        # OBS-2 (2026-08-09): RELATIVE ages alongside absolute timestamps.
        # Absolute UTC timestamps caused a real misdiagnosis: an operator
        # (me) read them as local time and "computed" a 7-hour stall that
        # never happened. Relative seconds are timezone-proof.
        since_reconcile = (now - self._last_reconcile_at).total_seconds() if self._last_reconcile_at else None
        since_index = (now - self._last_index_at).total_seconds() if self._last_index_at else None
        # OBS-3: a dead scan loop keeps pending empty forever (nobody
        # enqueues) so pending-lag alone can NEVER flag it — "loop death"
        # needs its own staleness dimension.
        scan_overdue = since_reconcile is not None and since_reconcile > 3 * self._scan_interval
        task_states = self._task_states()
        return {
            # Code-Review M2: "enabled" (config flag) is not "running" —
            # a startup failure must not present green freshness telemetry.
            "worker_running": bool(self._tasks) and any(not t.done() for t in self._tasks),
            "tasks": task_states,
            "last_index_at": (self._last_index_at.isoformat() if self._last_index_at else None),
            "last_reconcile_at": (self._last_reconcile_at.isoformat() if self._last_reconcile_at else None),
            "seconds_since_last_reconcile": (round(since_reconcile, 1) if since_reconcile is not None else None),
            "seconds_since_last_index": (round(since_index, 1) if since_index is not None else None),
            "scan_overdue": scan_overdue,
            "pending_depth": len(self._pending),
            "failed_entries": failed,
            # OBS-4: blacklist exclusions were absolutely silent — a user's
            # most natural test (new note with Obsidian's default "未命名"
            # name) vanished without a trace.
            "excluded_count": self._excluded_count,
            "lag_seconds": round(lag_seconds, 1),
            "stale": lag_seconds > self._stale_after or scan_overdue,
        }

    # ------------------------------------------------------------------
    # triggers: watcher (accelerator) + periodic scan (correctness backstop)
    # ------------------------------------------------------------------

    async def _watch_loop(self) -> None:
        """watchfiles accelerator. Best-effort: on Docker bind mounts the
        event stream may be incomplete — the periodic reconcile pass is the
        correctness guarantee, this only shortens save->searchable latency."""
        try:
            from watchfiles import Change, awatch
        except ImportError:
            logger.warning(
                "[RAG-S1] watchfiles unavailable — running on periodic "
                "reconcile only (SLO still holds via scan interval)"
            )
            return
        try:
            async for changes in awatch(self.vault_path, stop_event=None, recursive=True):
                if self._stopping:
                    break
                for change, abs_path in changes:
                    if not abs_path.endswith(".md"):
                        continue
                    rel = os.path.relpath(abs_path, self.vault_path).replace("\\", "/")
                    # reset_backoff: a real user save must retry a previously
                    # failed file immediately (M1) — only reconcile keeps the
                    # backoff untouched.
                    if change == Change.deleted:
                        self.enqueue("delete", rel, reset_backoff=True)
                    else:  # added | modified
                        status = self.enqueue("upsert", rel, reset_backoff=True)
                        # OBS-4 (2026-08-09): blacklist exclusion must leave a
                        # trace — a brand-new note named 未命名.md/Untitled.md
                        # hits DEFAULT_VAULT_SKIP_FILES and used to vanish in
                        # absolute silence (live-confirmed user confusion).
                        # Rate-limited: one log per path per process.
                        if status == "excluded":
                            self._excluded_count += 1
                            if rel not in self._excluded_logged:
                                self._excluded_logged.add(rel)
                                logger.warning(f"[RAG-S1] file save EXCLUDED from index (blacklist): {rel}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[RAG-S1] watcher stopped ({e}) — periodic reconcile continues to guarantee the SLO")

    async def _scan_loop(self) -> None:
        """Periodic anti-entropy pass. Runs one pass IMMEDIATELY on startup
        (startup reconciliation: catches everything changed while down)."""
        while not self._stopping:
            try:
                await self.reconcile()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[RAG-S1] reconcile pass failed: {e}", exc_info=True)
            try:
                await asyncio.sleep(self._scan_interval)
            except asyncio.CancelledError:
                break

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def _on_task_done(self, task: "asyncio.Task") -> None:
        """OBS-5 (2026-08-09): loud death. Because self._tasks holds strong
        refs, Python's "Task exception was never retrieved" would only fire
        at GC — i.e. NEVER while the process lives. Without this callback a
        loop can die in absolute silence."""
        if self._stopping:
            return
        try:
            exc: Any = task.exception()
        except asyncio.CancelledError:
            exc = "cancelled"
        logger.critical(
            f"[RAG-S1] task {task.get_name()} exited unexpectedly "
            f"(exception={exc!r}) — index freshness degraded; check "
            "freshness.tasks via the vault index status endpoint"
        )

    def start(self) -> None:
        """Spawn worker + watcher + scan loop. Caller (lifespan) must keep a
        strong reference to this orchestrator (tasks are referenced here)."""
        recovered = self.recover()
        if recovered:
            logger.info(f"[RAG-S1] recovered {recovered} pending index intents")
        self._tasks = [
            asyncio.create_task(self._worker_loop(), name="rag-s1-worker"),
            asyncio.create_task(self._watch_loop(), name="rag-s1-watcher"),
            asyncio.create_task(self._scan_loop(), name="rag-s1-scan"),
        ]
        for task in self._tasks:
            task.add_done_callback(self._on_task_done)
        logger.info(
            f"[RAG-S1] orchestrator started: vault={self.vault_path} "
            f"scan_interval={self._scan_interval}s stale_after={self._stale_after}s"
        )

    async def shutdown(self) -> None:
        self._stopping = True
        self._wake.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._persist_sync()
        logger.info("[RAG-S1] orchestrator shut down (pending flushed)")


# ------------------------------------------------------------------
# module singleton
# ------------------------------------------------------------------

_orchestrator: Optional[VaultIndexOrchestrator] = None


def get_vault_index_orchestrator() -> Optional[VaultIndexOrchestrator]:
    """Singleton accessor. Returns None when disabled via
    ENABLE_VAULT_INDEX_ORCHESTRATOR=false (rollback switch: off = stage-0
    behavior, manual full-scan endpoint only)."""
    global _orchestrator
    from app.config import settings

    if not getattr(settings, "ENABLE_VAULT_INDEX_ORCHESTRATOR", True):
        return None
    if _orchestrator is None:
        _orchestrator = VaultIndexOrchestrator(vault_path=settings.canvas_base_path)
    return _orchestrator
