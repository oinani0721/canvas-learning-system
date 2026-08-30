# CARD-D4 回归锁定 (BATCH-2026-08-27-Anki化与诚实收尾)
# [Source: _bmad-output/implementation-artifacts/goal-cards/2026-08-27-第三批小goal卡-Anki化与诚实收尾.md#CARD-D4]
"""FSRS_AVAILABLE=False fallback 写侧 datetime 序列化回归测试。

缺陷（写读不对称）: fallback create_card (:146-156) 与 _fallback_review
直出 raw datetime 的 due 字段, 但 serialize_card 的 else 分支原来直接
json.dumps —— datetime 不可 JSON 序列化, 三连崩 TypeError; 而 deserialize
的 fallback 分支一直有 fromisoformat (:381), 铁证写侧欠一个 isoformat。

近死码诚实评级 P3: 现网 fsrs 6.3.1 在位, 仅环境损坏/未来 7.x 升级才会
激活 fallback。本文件用屏蔽 fsrs import 的隔离子进程实测 fallback 分支
(同 test_fsrs_legacy_state_zero.py 的探针模式), 锁定:
  - create → serialize → deserialize roundtrip 无 TypeError 且 due 等值还原;
  - review_card 后的卡与 card_to_state(card).card_data 同样可序列化。

范围纪律: 本卡只修 serialize else 分支 (~4 行), 真实 fsrs 分支零改动。
"FSRS_AVAILABLE 判不到底层 fsrs 缺失" 问题超范围 (后续候选 DEBT-8), 禁混。
"""

import subprocess
import sys
from pathlib import Path

_LIB_PATH = str(Path(__file__).parent.parent.parent / "lib")


def _run_probe(probe: str) -> subprocess.CompletedProcess:
    """屏蔽 fsrs import 的隔离子进程探针 (同 legacy_state_zero 约定)。"""
    return subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=60)


def test_fallback_create_serialize_deserialize_roundtrip_in_isolated_process():
    """create_card 直出 raw datetime due → serialize 不得 TypeError,
    deserialize 后 due 必须等值还原 (isoformat/fromisoformat 对称)。"""
    probe = (
        r"""
import json, sys
from datetime import datetime
sys.modules["fsrs"] = None  # 强制 ImportError → FSRS_AVAILABLE=False
sys.path.insert(0, %r)
from memory.temporal.fsrs_manager import FSRS_AVAILABLE, FSRSManager
assert not FSRS_AVAILABLE
m = FSRSManager()
created = m.create_card()
assert isinstance(created["due"], datetime), "前提: fallback create_card 直出 datetime"
serialized = m.serialize_card(created)  # 修复前此行 TypeError 三连崩
payload = json.loads(serialized)
assert isinstance(payload["due"], str), f"due 应序列化为 isoformat 字符串: {payload['due']!r}"
restored = m.deserialize_card(serialized)
assert restored["due"] == created["due"], (
    f"due 未等值还原: {restored['due']!r} != {created['due']!r}"
)
assert restored["state"] == created["state"]
print("ROUNDTRIP-OK")
"""
        % _LIB_PATH
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-800:]
    assert "ROUNDTRIP-OK" in r.stdout


def test_fallback_reviewed_card_and_card_to_state_serializable_in_isolated_process():
    """review_card 后的卡 (due=now+interval 的 datetime) 与
    card_to_state(...).card_data 同样必须可序列化。"""
    probe = (
        r"""
import json, sys
from datetime import datetime
sys.modules["fsrs"] = None
sys.path.insert(0, %r)
from memory.temporal.fsrs_manager import FSRS_AVAILABLE, FSRSManager
assert not FSRS_AVAILABLE
m = FSRSManager()
card = m.create_card()
updated, log = m.review_card(card, 3)
assert isinstance(updated["due"], datetime), "前提: _fallback_review 直出 datetime"
serialized = m.serialize_card(updated)  # 修复前 TypeError
restored = m.deserialize_card(serialized)
assert restored["due"] == updated["due"], "review 后 due 未等值还原"
cs = m.card_to_state(updated, "concept", "board.canvas")  # 内部再 serialize 一次
payload = json.loads(cs.card_data)
assert isinstance(payload["due"], str)
assert cs.state != 0
print("REVIEWED-OK")
"""
        % _LIB_PATH
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-800:]
    assert "REVIEWED-OK" in r.stdout
