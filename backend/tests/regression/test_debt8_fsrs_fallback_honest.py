# CARD-DEBT-8 回归锁定 (BATCH-2026-09-01-第八批)
# [Source: _bmad-output/implementation-artifacts/goal-cards/第八批-goals/W8-1.md]
"""FSRS 底层 fallback 激活时 algorithm 字段诚实性回归测试。

缺陷（双标志位分层失配）: review_service.FSRS_AVAILABLE (:80-97) 只判
`memory.temporal.fsrs_manager` 模块可导入; 底层 fsrs_manager.FSRS_AVAILABLE
(:21-26) 才判 py-fsrs 真库。py-fsrs 缺失时底层走 _fallback_review
(简单倍率调度, 非 FSRS-4.5 也非 Ebbinghaus 固定间隔), 而 review_service
:922/:1103 在 manager 存在时无条件写 "algorithm": "fsrs-4.5" ⇒ 谎报。

修复契约（默认裁决 ①-③）:
  ① fallback 激活 → algorithm="fsrs-fallback-scheduler"
    + degraded_reason 含 "fsrs_library_missing"（加性, 沿 CARD-D3 先例）;
  ② 不新增第三个模块级标志——底层可用性以 FSRSManager 实例属性
    library_available（取自模块级 FSRS_AVAILABLE）暴露;
  ③ 真实库在位零行为变化（对照探针锁定: 无新键、algorithm 不变）。

探针纪律: 主进程直调 ReviewService 会经 _save_card_states 写
backend/data/fsrs_card_states.json —— 所有探针必须子进程隔离
(sys.modules['fsrs']=None 屏蔽 import) 且 _CARD_STATES_FILE 指向 tmp。

本文件不比什么: 不证明 py-fsrs 在位时调度数值正确（tests/unit/
test_fsrs_manager.py 的职责）; 不证明 API 端点层转发该字段——已实证
GET /api/v1/review/fsrs-state 端点用显式字段白名单构造响应且 response
model 无 algorithm/degraded_reason 字段, 新键透不到 HTTP（移交项,
见验收单 UAT-CARD-DEBT-8 §移交项 1; test_fsrs_state_api.py 本身待
W4② 合入后由主 session 补跑）; manager 为 None 的 ebbinghaus-fallback
分支 (:944/:1145) 语义本卡零改动, 不在锁定面内。
"""

import subprocess
import sys
from pathlib import Path

_BACKEND = Path(__file__).parent.parent.parent
_LIB_PATH = str(_BACKEND / "lib")


def _run_probe(probe: str) -> subprocess.CompletedProcess:
    """隔离子进程探针 (同 test_fsrs_fallback_datetime_serialize 约定)。"""
    return subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_BACKEND),
    )


_PROBE_PRELUDE = r"""
import asyncio, json, pathlib, sys, tempfile
sys.path.insert(0, %r)
import app.services.review_service as rs
from memory.temporal import fsrs_manager as fm
# 前提自证: 上层标志为真（模块可导入）
assert rs.FSRS_AVAILABLE, "prerequisite: fsrs_manager module importable"
# 写盘隔离: 卡状态文件指向 tmp, 禁触 backend/data
rs._CARD_STATES_FILE = pathlib.Path(tempfile.mkdtemp()) / "fsrs_card_states.json"
svc = rs.ReviewService(canvas_service=None, task_manager=None)
assert svc._fsrs_manager is not None, "prerequisite: FSRSManager instantiated"
"""

_BLOCK_FSRS = "import sys\nsys.modules['fsrs'] = None  # 屏蔽 py-fsrs → 底层 fallback 激活\n"


def test_fallback_record_review_result_reports_honest_algorithm():
    """底层 fallback 激活时 record_review_result 不得谎报 fsrs-4.5,
    须报 fsrs-fallback-scheduler + degraded_reason 含 fsrs_library_missing。"""
    probe = (
        _BLOCK_FSRS
        + (_PROBE_PRELUDE % _LIB_PATH)
        + r"""
assert not fm.FSRS_AVAILABLE, "prerequisite: underlying py-fsrs blocked"
r = asyncio.run(
    svc.record_review_result(canvas_name="board", concept_id="c1", rating=3)
)
assert r["algorithm"] != "fsrs-4.5", f"lied fsrs-4.5: {r['algorithm']!r}"
assert r["algorithm"] == "fsrs-fallback-scheduler", f"got {r['algorithm']!r}"
reason = r.get("degraded_reason")
assert reason, f"degraded_reason empty: {reason!r}"
assert "fsrs_library_missing" in reason, f"got {reason!r}"
print("RECORD-HONEST-OK")
"""
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-1200:]
    assert "RECORD-HONEST-OK" in r.stdout


def test_fallback_record_review_result_keeps_persistence_signal():
    """CARD-D3 持久化信号不得被本卡冲掉: fallback 激活且写失败时,
    degraded_reason 须同时携带 fsrs_library_missing 与 card_state_write_failed。"""
    probe = (
        _BLOCK_FSRS
        + (_PROBE_PRELUDE % _LIB_PATH)
        + r"""
assert not fm.FSRS_AVAILABLE

async def _fail_save(pending=None):
    return False

svc._save_card_states = _fail_save
r = asyncio.run(
    svc.record_review_result(canvas_name="board", concept_id="c1", rating=3)
)
reason = r.get("degraded_reason") or ""
assert "fsrs_library_missing" in reason, f"got {reason!r}"
assert "card_state_write_failed" in reason, f"D3 signal lost: {reason!r}"
print("D3-SIGNAL-OK")
"""
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-1200:]
    assert "D3-SIGNAL-OK" in r.stdout


def test_fallback_schedule_review_reports_honest_algorithm():
    """底层 fallback 激活时 schedule_review (:922) 同样不得谎报 fsrs-4.5,
    且 log_decision 决策日志的 reason 也不得宣称 FSRS-4.5。"""
    probe = (
        _BLOCK_FSRS
        + (_PROBE_PRELUDE % _LIB_PATH)
        + r"""
assert not fm.FSRS_AVAILABLE
captured = []
rs.log_decision = lambda **kw: captured.append(kw)  # 捕获决策日志
r = asyncio.run(svc.schedule_review(canvas_name="board", concept_id="c2"))
assert r["algorithm"] != "fsrs-4.5", f"lied fsrs-4.5: {r['algorithm']!r}"
assert r["algorithm"] == "fsrs-fallback-scheduler", f"got {r['algorithm']!r}"
reason = r.get("degraded_reason")
assert reason and "fsrs_library_missing" in reason, f"got {reason!r}"
assert captured, "log_decision not called"
log_reason = captured[-1].get("reason", "")
assert "FSRS-4.5" not in log_reason, f"decision log still lies: {log_reason!r}"
assert "fallback" in log_reason, f"got {log_reason!r}"
print("SCHEDULE-HONEST-OK")
"""
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-1200:]
    assert "SCHEDULE-HONEST-OK" in r.stdout


def test_fallback_get_fsrs_state_reports_honest_algorithm():
    """底层 fallback 激活时 get_fsrs_state 响应须加性携带
    algorithm=fsrs-fallback-scheduler + degraded_reason。"""
    probe = (
        _BLOCK_FSRS
        + (_PROBE_PRELUDE % _LIB_PATH)
        + r"""
assert not fm.FSRS_AVAILABLE
r = asyncio.run(svc.get_fsrs_state("c3"))
assert r["found"] is True
assert r.get("algorithm") == "fsrs-fallback-scheduler", f"got {r.get('algorithm')!r}"
reason = r.get("degraded_reason")
assert reason and "fsrs_library_missing" in reason, f"got {reason!r}"
print("STATE-HONEST-OK")
"""
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-1200:]
    assert "STATE-HONEST-OK" in r.stdout


def test_real_library_responses_unchanged():
    """裁决③对照: 真实库在位时 algorithm 仍为 fsrs-4.5, 且三个响应
    均不新增 fallback 专属键（degraded_reason 语义与 HEAD 逐键一致:
    record_review_result 持久化成功时为 None; schedule_review /
    get_fsrs_state 响应根本没有该键, 也没有 algorithm 新键）。"""
    probe = (
        (_PROBE_PRELUDE % _LIB_PATH)
        + r"""
assert fm.FSRS_AVAILABLE, "prerequisite: real py-fsrs present"
rec = asyncio.run(
    svc.record_review_result(canvas_name="board", concept_id="c1", rating=3)
)
assert rec["algorithm"] == "fsrs-4.5", f"got {rec['algorithm']!r}"
assert rec["degraded_reason"] is None, f"got {rec['degraded_reason']!r}"
sch = asyncio.run(svc.schedule_review(canvas_name="board", concept_id="c2"))
assert sch["algorithm"] == "fsrs-4.5", f"got {sch['algorithm']!r}"
assert "degraded_reason" not in sch, "new key leaked into real-library path"
st = asyncio.run(svc.get_fsrs_state("c3"))
assert st["found"] is True
assert "algorithm" not in st, "new key leaked into real-library path"
assert "degraded_reason" not in st, "new key leaked into real-library path"
print("REAL-UNCHANGED-OK")
"""
    )
    r = _run_probe(probe)
    assert r.returncode == 0, r.stderr[-1200:]
    assert "REAL-UNCHANGED-OK" in r.stdout
