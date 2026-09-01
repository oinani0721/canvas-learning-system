"""
LanceDB Auto-Index Service — Story 38.1

Automatically triggers LanceDB index updates after Canvas CRUD operations.
Uses per-canvas debouncing to coalesce rapid updates and tenacity retry
for resilience. Failed index operations are persisted to JSONL for
startup recovery.

AC-1: Auto-trigger after add_node/update_node, async non-blocking, <5s
AC-2: Failure does not block CRUD; 3 retries with exponential backoff
AC-3: Pending operations recovered on startup from JSONL file
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import os
import threading

import structlog
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = structlog.get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# LanceDB Index Service
# ═══════════════════════════════════════════════════════════════════════════════


class LanceDBIndexService:
    """
    Manages automatic LanceDB indexing for Canvas nodes.

    Features:
    - Per-canvas debounce (default 500ms) to coalesce rapid updates
    - 3x retry with exponential backoff on failure
    - JSONL persistence for failed operations (startup recovery)
    - Lazy LanceDB client initialization
    """

    def __init__(self, state_dir: Optional[str] = None) -> None:
        """``state_dir``: journal 落盘目录 (默认 ``backend/app/data``)。

        ⛔ Codex round-1 HIGH-2: legacy 路径改由 ``_pending_file.parent`` 派生,
        免得"测试只搬 _pending_file"时隔离动作打到真实 data 目录。
        """
        self._lancedb_client = None
        self._client_unavailable = False  # [Review H1/M2] skip retries when module missing
        self._pending_tasks: Dict[str, asyncio.Task] = {}
        self._indexing_canvases: set[str] = set()  # [Review M1] track active indexing
        self._file_lock = threading.Lock()  # [Review H2] protect JSONL concurrent writes
        # CARD-G2-5: pending journal 按 vault 命名空间 (旧的无维度路径只在
        # recover_pending() 里被隔离, 不加载)。key 取部署期 settings.vault_id,
        # 不读 per-request ContextVar —— 见 app/core/vault_state_paths.py。
        from app.core.vault_state_paths import (
            deployment_vault_key,
            namespaced_state_path,
        )

        _data_dir = Path(state_dir) if state_dir else Path(__file__).parent.parent / "data"
        self._state_dir: Path = _data_dir
        self._journal_stem: str = "lancedb_pending_index"
        self._vault_key: str = deployment_vault_key()
        self._pending_file: Path = namespaced_state_path(_data_dir, self._journal_stem, vault_key=self._vault_key)
        self._debounce_seconds: float = settings.LANCEDB_INDEX_DEBOUNCE_MS / 1000.0
        self._index_timeout: float = settings.LANCEDB_INDEX_TIMEOUT
        # CARD-G2-5 round-2 HIGH-3: durable 写失败的对外可见计数。
        self._durable_write_failures: int = 0
        self._last_durable_error: Optional[str] = None

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def schedule_index(
        self,
        canvas_name: str,
        canvas_base_path: str,
        trigger_node_id: Optional[str] = None,
    ) -> None:
        """
        Schedule a debounced LanceDB index update for a canvas.

        If a previous debounce task exists for the same canvas, it is cancelled
        and replaced. This ensures only the latest update triggers indexing.

        Args:
            canvas_name: Canvas name (without .canvas extension)
            canvas_base_path: Base directory for canvas files
            trigger_node_id: Node ID that triggered this index (for logging, AC-2)
        """
        if not settings.ENABLE_LANCEDB_AUTO_INDEX:
            return

        # Cancel existing debounce task for this canvas
        existing = self._pending_tasks.get(canvas_name)
        if existing and not existing.done():
            existing.cancel()
            logger.debug(f"[Story 38.1] Cancelled previous debounce for {canvas_name}")

        # Create new debounced task
        # wave-5 Stage B P0 (2026-05-11): snapshot ContextVar (vault) so the
        # debounced LanceDB index task runs under the originating request's
        # vault — prevents cross-vault leak. [ChatGPT v4 Agent C P0 fix]
        ctx = contextvars.copy_context()
        task = asyncio.create_task(
            self._debounced_index(canvas_name, canvas_base_path, trigger_node_id),
            context=ctx,
        )
        self._pending_tasks[canvas_name] = task

        # [Review M2] Auto-clean completed tasks to prevent memory leak
        # Only remove if the dict still holds THIS task (not a newer replacement)
        task.add_done_callback(
            lambda _t, cn=canvas_name: self._pending_tasks.pop(cn, None) if self._pending_tasks.get(cn) is _t else None
        )

    def schedule_note_index(
        self,
        note_path: str,
        vault_root: str,
        coalesce_key: Optional[str] = None,
    ) -> None:
        """⛔ DEPRECATED (RAG-S1 2026-08-03, quarantine-first — 勿新增调用方).

        由 VaultIndexOrchestrator 替代: 本方法的下游 _debounced_note_index 只刷
        wikilink 图、零 LanceDB 写入 (「后续 Story」从未实现), 且整 vault 单
        coalesce key 让异 path 互相 cancel (ChatGPT 反证 #1)。唯一调用方
        POST /index/refresh-changed 已改走 orchestrator。Canvas 侧的
        schedule_index() 不受影响。观察期后随 Tier B 物理删除。

        Round-23 Story 8.1 原设计 — Schedule debounced .md note re-index.

        Args:
            note_path: vault 相对路径 (如 '节点/admissibility.md').
            vault_root: vault 绝对路径.
            coalesce_key: 可选合并 key (默认 vault_root, 同 vault 多文件合并到 1 次).
        """
        if not settings.ENABLE_LANCEDB_AUTO_INDEX:
            return

        key = coalesce_key or f"vault:{vault_root}"

        existing = self._pending_tasks.get(key)
        if existing and not existing.done():
            existing.cancel()
            logger.debug(f"[Story 8.1] Cancelled previous note index debounce for {key}")

        # wave-5 Stage B P0 (2026-05-11): snapshot ContextVar so debounced
        # note re-index inherits vault context — prevents cross-vault leak.
        ctx = contextvars.copy_context()
        task = asyncio.create_task(self._debounced_note_index(key, note_path, vault_root), context=ctx)
        self._pending_tasks[key] = task

        task.add_done_callback(
            lambda _t, k=key: self._pending_tasks.pop(k, None) if self._pending_tasks.get(k) is _t else None
        )

    async def _debounced_note_index(self, key: str, note_path: str, vault_root: str) -> None:
        """Round-23 Story 8.1 — Wait debounce, then refresh wikilink graph + LanceDB note index."""
        try:
            await asyncio.sleep(self._debounce_seconds)
        except asyncio.CancelledError:
            return

        if key in self._indexing_canvases:
            logger.debug(f"[Story 8.1] Skipping duplicate note index for {key}")
            self._pending_tasks.pop(key, None)
            return

        self._pending_tasks.pop(key, None)
        self._indexing_canvases.add(key)
        try:
            from app.services.wikilink_graph_service import (
                get_wikilink_graph_service,
            )

            wgs = get_wikilink_graph_service()
            await wgs.refresh(changed_files=[note_path])
            logger.info(
                f"[Story 8.1] Wikilink graph refreshed for note {note_path} "
                f"(vault={vault_root}, build_ts={wgs.build_timestamp})"
            )
        except Exception as e:
            logger.warning(f"[Story 8.1] Note index refresh failed for {note_path}: {e}")
        finally:
            self._indexing_canvases.discard(key)

    @property
    def _legacy_pending_file(self) -> Path:
        """G2-5 之前的无维度 journal —— 由当前 journal 的目录派生 (见 __init__)。"""
        from app.core.vault_state_paths import legacy_state_path

        return legacy_state_path(self._pending_file.parent, self._journal_stem)

    async def recover_pending(self, canvas_base_path: str) -> Dict[str, int]:
        """
        Recover and retry pending index operations from JSONL file.

        Called during application startup (AC-3).

        Args:
            canvas_base_path: Base directory for canvas files

        Returns:
            Dict with 'recovered' and 'pending' counts

        CARD-G2-5: 只加载**本 vault** 的 journal; G2-5 之前的无维度旧文件在这里
        被改名隔离并跳过 (条目无从判断 vault 归属, 按当前 vault 重放 = 串台)。
        """
        from app.core.vault_state_paths import quarantine_legacy_state_file

        quarantine_legacy_state_file(
            self._legacy_pending_file, context="lancedb_index_service", active_path=self._pending_file
        )

        if not self._pending_file.exists():
            return {"recovered": 0, "pending": 0, "persist_failed": 0}

        try:
            lines = self._pending_file.read_text(encoding="utf-8").strip().splitlines()
        except (OSError, FileNotFoundError) as e:
            logger.warning(f"[Story 38.1] Failed to read pending file: {e}")
            return {"recovered": 0, "pending": 0, "persist_failed": 0}

        if not lines:
            return {"recovered": 0, "pending": 0, "persist_failed": 0}

        # Deduplicate: keep latest entry per canvas_name
        unique: Dict[str, Dict[str, Any]] = {}
        orig_lines = set(lines)  # round-3 竞态修复: 锁内重读时区分「旧残影」与「并发新 append」
        for line in lines:
            try:
                entry = json.loads(line)
                unique[entry["canvas_name"]] = entry
            except (json.JSONDecodeError, KeyError):
                continue

        logger.info(f"[Story 38.1] LanceDB: {len(unique)} pending index updates recovered")

        recovered = 0
        still_pending: list[Dict[str, Any]] = []

        for canvas_name, entry in unique.items():
            try:
                # [Review M1] Use retry version for consistency (3 attempts)
                await self._do_index_with_retry(canvas_name, canvas_base_path)
                recovered += 1
                logger.info(f"[Story 38.1] Recovered index for {canvas_name}")
            except Exception as e:
                logger.warning(f"[Story 38.1] Recovery failed for {canvas_name}: {e}")
                still_pending.append(entry)

        # [Review H2] Lock protects against concurrent _persist_pending() appends
        rewrite_ok = True
        with self._file_lock:
            # ⛔ CARD-G2-5 round-3 Codex HIGH（recover 竞态）: 重放发生在锁外,
            # 期间 `_persist_pending()` 可以成功 append 新意图 —— 若用旧快照
            # rewrite/unlink, 成功落盘的新意图会被静默删除且对外报成功。
            # 修复: 锁内重读当前 journal, 只取**不在旧快照行集合里**的行
            # (= 重放窗口内新 append 的条目; 旧快照行无论已消费与否都是残影,
            # 由 still_pending/unlink 语义接管), 与 still_pending 合并。
            # append 与 rewrite 同锁互斥, 「重读→replace」之间是连续同步代码,
            # 竞态窗口消除。
            fresh = []
            try:
                cur_lines = self._pending_file.read_text(encoding="utf-8").strip().splitlines()
            except (OSError, FileNotFoundError) as e:
                # ⛔ round-4b Codex MEDIUM: 重读失败不得当作「空文件」继续
                # rewrite/unlink —— 那会用旧快照覆盖未知内容。fail-closed:
                # 不写不删, 计数 + persist_failed=1。
                self._durable_write_failures += 1
                self._last_durable_error = f"{type(e).__name__}: {e}"
                logger.error(
                    f"[Story 38.1] journal re-read FAILED ({e}) — keeping file as-is, {len(still_pending)} intent(s) preserved"
                )
                return {
                    "recovered": recovered,
                    "pending": len(still_pending),
                    "persist_failed": 1,
                }
            for ln in cur_lines:
                if not ln.strip() or ln in orig_lines:
                    continue  # 旧快照残影 (含已消费/仍 pending 的行), 不参与合并
                try:
                    fresh.append(json.loads(ln))
                except json.JSONDecodeError:
                    continue
            merged = self._merge_journal_entries(fresh, still_pending)
            if merged:
                rewrite_ok = self._rewrite_journal(merged)
            else:
                # All recovered — remove file（空删语义留在这里: helper 只管写）
                try:
                    self._pending_file.unlink()
                except OSError:
                    pass

        return {
            "recovered": recovered,
            # ⛔ round-4b Codex MEDIUM: 重放窗口内新 append 的条目 (fresh) 同样
            # 仍待处理, 必须计入 pending (旧版只数 still_pending 会少报)。
            "pending": len(still_pending) + len(fresh),
            # ⛔ CARD-G2-5 HIGH-3: 重写失败 = 崩溃后无法恢复这批意图, 必须可见。
            "persist_failed": 0 if rewrite_ok else 1,
        }

    @staticmethod
    def _merge_journal_entries(
        fresh: list[Dict[str, Any]], still_pending: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """按 canvas_name 去重合并, timestamp 最新者胜（平局取 still_pending——刚失败的那次更可信）。"""
        by_canvas: Dict[str, Dict[str, Any]] = {}
        for e in sorted(
            list(fresh) + list(still_pending),
            key=lambda x: (str(x.get("timestamp", "")), x in still_pending),
        ):
            name = e.get("canvas_name")
            if name:
                by_canvas[str(name)] = e
        return list(by_canvas.values())

    def _rewrite_journal(self, entries: list[Dict[str, Any]]) -> bool:
        """原子重写 journal（tmp + os.replace），只含 still-pending 条目。

        ⛔ 调用方必须已持有 ``self._file_lock``（threading.Lock 非可重入, 本方法
        内不再 acquire —— 自己再 acquire 会同线程自死锁, 表现为事件循环挂死）。
        返回 False 时**不动原 journal**（意图不丢）并清理 tmp 残片。

        tmp 名 = ``<journal>.tmp``（即 ``<stem>__<key>.jsonl.tmp``）: 与
        vault_index_orchestrator 的 tmp 形态一致, 字节预算正是按这个后缀预留的
        （``vault_state_paths.namespaced_state_path``）; 与隔离件命名空间
        ``<stem>.jsonl.pre-g25.bak[.N]`` 逐字不同（隔离器只对精确路径做
        ``exists()``, 无任何 glob —— 不会误吞 tmp）。
        """
        tmp = self._pending_file.with_name(self._pending_file.name + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                for e in entries:
                    fh.write(json.dumps(e, ensure_ascii=False) + "\n")
            os.replace(tmp, self._pending_file)
            return True
        except (OSError, TypeError, ValueError) as e:
            self._durable_write_failures += 1
            self._last_durable_error = f"{type(e).__name__}: {e}"
            logger.error(
                f"[Story 38.1] journal rewrite FAILED ({e}) — original journal kept, {len(entries)} intent(s) preserved"
            )
            try:
                tmp.unlink()  # 清残片, 不留垃圾
            except OSError:
                pass
            return False

    async def cleanup(self) -> None:
        """Cancel all pending debounce tasks. Called during shutdown."""
        for canvas_name, task in self._pending_tasks.items():
            if not task.done():
                task.cancel()
        self._pending_tasks.clear()

    # ─────────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────────

    async def _debounced_index(
        self,
        canvas_name: str,
        canvas_base_path: str,
        trigger_node_id: Optional[str] = None,
    ) -> None:
        """Wait for debounce window, then index with retry."""
        try:
            await asyncio.sleep(self._debounce_seconds)
        except asyncio.CancelledError:
            # A newer update superseded this one — expected behavior
            return

        # [Review M1] Skip if this canvas is already being indexed
        if canvas_name in self._indexing_canvases:
            logger.debug(f"[Story 38.1] Skipping duplicate index for {canvas_name}")
            self._pending_tasks.pop(canvas_name, None)
            return

        # Remove from pending tasks map
        self._pending_tasks.pop(canvas_name, None)

        # [Review H3] Build node context string for AC-2 compliant logging
        node_ctx = f" (triggered by node {trigger_node_id})" if trigger_node_id else ""

        self._indexing_canvases.add(canvas_name)
        try:
            await self._do_index_with_retry(canvas_name, canvas_base_path)
            logger.info(f"[Story 38.1] LanceDB auto-index completed for {canvas_name}{node_ctx}")
        except Exception as e:
            # [Review H3] AC-2: include trigger node ID in warning
            logger.warning(
                f"[Story 38.1] LanceDB index update failed for canvas {canvas_name}{node_ctx}, queued for retry: {e}"
            )
            if not self._persist_pending(canvas_name, str(e), trigger_node_id):
                # ⛔ CARD-G2-5 HIGH-3: durable journal 也写失败了 —— 这条重试
                # 意图真的丢了（崩溃后无法恢复），与上面的 WARNING（还有
                # journal 兜底）语义不同，必须用 ERROR 区分。
                logger.error(
                    f"[Story 38.1] intent lost: durable journal write FAILED for canvas {canvas_name} "
                    f"(state_dir={self._state_dir}) — this retry intent will NOT survive a crash"
                )
        finally:
            self._indexing_canvases.discard(canvas_name)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _do_index_with_retry(self, canvas_name: str, canvas_base_path: str) -> int:
        """Index a canvas with retry. Decorated by tenacity."""
        return await self._do_index(canvas_name, canvas_base_path)

    async def _do_index(self, canvas_name: str, canvas_base_path: str) -> int:
        """
        Perform actual LanceDB indexing for a canvas.

        Returns:
            Number of nodes indexed
        """
        # [Review M2] Fast-fail when agentic_rag module is unavailable
        if self._client_unavailable:
            raise RuntimeError("LanceDB client permanently unavailable (module not installed)")

        client = self._get_or_init_client()
        if client is None:
            raise RuntimeError("LanceDB client not available")

        # [Review H1] Use try/except instead of accessing private _initialized
        try:
            if hasattr(client, "initialize"):
                await client.initialize()
        except (RuntimeError, OSError, ConnectionError) as e:
            # [Review M3] initialize() is idempotent; log but don't block indexing
            logger.debug(f"[Story 38.1] LanceDB client.initialize() skipped: {e}")

        # Resolve subject metadata
        from app.services.subject_resolver import get_subject_resolver

        resolver = get_subject_resolver()
        canvas_path = f"{canvas_name}.canvas"
        info = resolver.resolve(canvas_path)

        # Read canvas file from disk
        full_path = Path(canvas_base_path) / canvas_path
        if not full_path.exists():
            raise FileNotFoundError(f"Canvas file not found: {full_path}")

        canvas_data = json.loads(full_path.read_text(encoding="utf-8"))
        nodes = canvas_data.get("nodes", [])

        # Index with timeout (AC-1: within 5 seconds)
        node_count: int = await asyncio.wait_for(
            client.index_canvas(
                canvas_path=canvas_path,
                nodes=nodes,
                table_name=settings.LANCEDB_INDEX_TABLE_NAME,
                subject=info.subject,
            ),
            timeout=self._index_timeout,
        )

        return node_count

    def _get_or_init_client(self):
        """Lazy-load LanceDB client (same pattern as metadata.py:get_lancedb_client)."""
        if self._lancedb_client is not None:
            return self._lancedb_client

        try:
            from agentic_rag.clients.lancedb_client import LanceDBClient

            self._lancedb_client = LanceDBClient()
            logger.debug("[Story 38.1] LanceDB client created for auto-index")
            return self._lancedb_client
        except ImportError as e:
            # [Review M2] Mark permanently unavailable to avoid 3x retry waste
            self._client_unavailable = True
            logger.warning(f"[Story 38.1] LanceDB client not available: {e}")
            return None
        except (RuntimeError, OSError, ConnectionError) as e:
            logger.warning(f"[Story 38.1] LanceDB client init failed: {e}")
            return None

    def _persist_pending(
        self,
        canvas_name: str,
        error: str,
        trigger_node_id: Optional[str] = None,
    ) -> bool:
        """Persist a failed index operation to JSONL for startup recovery (AC-3).

        ⛔ CARD-G2-5 HIGH-3: 返回 False = durable 写失败（调用方必须让失败可见,
        不得假报成功）。捕获面维持 (OSError, TypeError, ValueError) —— 其它异常
        会向上逃逸到 _debounced_index 的 fire-and-forget 任务边界（如实登记,
        不静默加宽捕获面）。
        """
        try:
            entry = {
                "canvas_name": canvas_name,
                "timestamp": datetime.now().isoformat(),
                "error": error,
            }
            if trigger_node_id:
                entry["trigger_node_id"] = trigger_node_id
            self._pending_file.parent.mkdir(parents=True, exist_ok=True)
            # [Review H2] Lock protects concurrent JSONL appends on Windows
            with self._file_lock:
                with open(self._pending_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except (OSError, TypeError, ValueError) as e:
            self._durable_write_failures += 1
            self._last_durable_error = f"{type(e).__name__}: {e}"
            logger.error(f"[Story 38.1] Failed to persist pending index: {e}")
            return False

    def durable_status(self) -> Dict[str, Any]:
        """只读: durable 写失败计数与最近错误。

        CARD-G2-5 HIGH-3 供后续状态面消费（本卡不接端点, 登记移交）。
        """
        return {
            "failures": self._durable_write_failures,
            "last_error": self._last_durable_error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_lancedb_index_service_instance: Optional[LanceDBIndexService] = None


def get_lancedb_index_service() -> Optional[LanceDBIndexService]:
    """Get or create the singleton LanceDBIndexService."""
    global _lancedb_index_service_instance
    if not settings.ENABLE_LANCEDB_AUTO_INDEX:
        return None
    if _lancedb_index_service_instance is None:
        _lancedb_index_service_instance = LanceDBIndexService()
    return _lancedb_index_service_instance
