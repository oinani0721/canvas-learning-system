# Story 38.6: Shared constants for failed writes fallback mechanism.
#
# Centralised here to avoid DRY violation (previously duplicated in
# agent_service.py and memory_service.py) and to provide a single lock
# that both the writer (_record_failed_write) and reader/recovery
# (recover_failed_writes, load_failed_scores) can share.
import threading
from pathlib import Path

# Fallback JSONL file for writes that failed after all retries.
FAILED_WRITES_FILE: Path = (
    Path(__file__).parent.parent.parent / "data" / "failed_writes.jsonl"
)

# Lock shared across writer (agent_service) and reader (memory_service)
# so that recovery/read never races with concurrent append writes.
failed_writes_lock = threading.Lock()
