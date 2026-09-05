"""CARD-G3-3 — per-node CAS 与乱序事件隔离 (复习写侧并发防护) 的行为门。

被测面 (全部**生产形态**, 不另写第二套实现):
  · `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的两个 PYEOF 静态块
    (写分主块 + A3 增量归纳块) —— 逐字提取后跑, 仅重定向 P 常量;
  · `canvas-vault/.claude/scripts/fsrs_bridge.py` 的 CAS 边界
    (`cas_token` / `cas_revision` / `cas_conflict`);
  · `backend/app/services/learning_event_log.py` 的跨进程账本锁与乱序补录标记。

⛔ 本文件**不改** `test_g3_2_review_ledger.py` / `validate_learning_events.py` /
   `g32*` (第十一批 Z6 车道的地盘), fixture 与常量在本文件内自包含。
⚠️ 并发门用**真子进程**, 不用线程: threading.Lock 在同进程里恒有效, 拿线程测
   跨进程锁等于测了个必然通过的东西 (假门)。
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from app.services import learning_event_log as ev

WT = Path(__file__).resolve().parents[3]
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VAULT_SCRIPTS = WT / "canvas-vault" / ".claude" / "scripts"

_SKILL_TEXT = SKILL.read_text(encoding="utf-8")
_BLOCKS = re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", _SKILL_TEXT, re.DOTALL)
_MAIN = [b for b in _BLOCKS if 'P = "/tmp/quiz-answer-payload.json"' in b]
_INCR = [b for b in _BLOCKS if 'P = "/tmp/quiz-answer-incr.json"' in b]
assert len(_MAIN) == 1, f"SKILL.md 应恰有 1 个主写点块, 实见 {len(_MAIN)}"
assert len(_INCR) == 1, f"SKILL.md 应恰有 1 个 A3 增量归纳块, 实见 {len(_INCR)}"
CODE = _MAIN[0]
INCR_CODE = _INCR[0]

SEB_SKILL = WT / "canvas-vault" / ".claude" / "skills" / "start-exam-board" / "SKILL.md"
_SEB_BLOCKS = [
    b
    for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", SEB_SKILL.read_text(encoding="utf-8"), re.DOTALL)
    if 'P = "/tmp/exam-created-event.json"' in b
]
assert len(_SEB_BLOCKS) == 1, f"start-exam-board 应恰有 1 个落账块, 实见 {len(_SEB_BLOCKS)}"
SEB_CODE = _SEB_BLOCKS[0]

NODE_REL = "节点/测试节点.md"
TS1 = "2026-08-01T10:00:00Z"
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)


# ────────────────────────────── fixture ──────────────────────────────


def _make_vault(tmp_path: Path) -> Path:
    """完整镜像布局: REPO=tmp_path, VAULT=tmp_path/canvas-vault。

    被测代码 symlink 引真文件 —— 主树漂移即被本文件测到 (与 G3-2 fixture 同形)。
    """
    repo = tmp_path
    v = repo / "canvas-vault"
    (v / "节点").mkdir(parents=True)
    (v / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (v / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (v / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    (v / ".canvas-config.yaml").write_text(
        '# 测试 config\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n', encoding="utf-8"
    )
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    return v


@pytest.fixture()
def vault(tmp_path):
    return _make_vault(tmp_path)


def _payload(event_id: str, **kw) -> dict:
    base = {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "ts": TS1,
        "review_time": TS1,
        "event_id": event_id,
        "exam_board": f"检验白板/{event_id}.md",
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }
    base.update(kw)
    return base


def _writer_code(vault: Path, payload: dict, tag: str) -> str:
    pfile = vault.parent / f"payload-{tag}.json"
    pfile.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pfile)))


def _spawn_writer(vault: Path, payload: dict, tag: str, env_extra: dict | None = None):
    """生产形态: 子进程 + cwd=vault (NODE 相对路径与生产一致)。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **(env_extra or {}))
    return subprocess.Popen(
        [sys.executable, "-c", _writer_code(vault, payload, tag)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(vault),
        env=env,
    )


def _run_writer(vault: Path, payload: dict, tag: str, env_extra: dict | None = None):
    proc = _spawn_writer(vault, payload, tag, env_extra)
    out, err = proc.communicate(timeout=180)
    return proc.returncode, out, err


def _exam_board_code(vault: Path, board: str) -> str:
    """逐字提取的建板落账块, 仅重定向 P 常量 (与主写点同范式)。"""
    pf = vault.parent / f"exam-created-{board}.json"
    pf.write_text(
        json.dumps(
            {"vault_root": str(vault), "exam_board": f"检验白板/{board}.md", "node": "测试节点", "ts": TS1},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return SEB_CODE.replace('"/tmp/exam-created-event.json"', json.dumps(str(pf)))


def _rows_of(ledger: Path) -> list[dict]:
    return [json.loads(x) for x in ledger.read_text(encoding="utf-8").split("\n") if x.strip()]


def _ledger_rows(vault: Path) -> list[dict]:
    p = vault / "learning_events.jsonl"
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _fm_value(vault: Path, key: str):
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', text, re.M)
    return m.group(1).strip() if m else None


def _validate(vault: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(vault / "learning_events.jsonl")],
        capture_output=True,
        text=True,
        timeout=120,
    )


# ─────────────── 门① 两进程同节点并发评分 → 无 lost update ───────────────
# ⚠️ 本门是本卡的承重门: 变异脚本 `backend/scripts/g33_mutation_gates.py`
#    拆掉 per-node 锁后, 它必须变红 (见该脚本的 KILLED 判据)。


@pytest.mark.parametrize("round_no", [1, 2])
def test_concurrent_same_node_no_lost_update(vault, round_no):
    """两个进程同时给同一节点评分: 两条都入账、frontmatter 反映最新、无覆盖。

    ⛔ 断言顺序**刻意**把「状态不变量」放在 rc 之前 (独立复核 M2 / 内部审查实测)。
    上一版先断言 `rc == 0`, 于是拆掉 per-node 锁后测试确实变红 —— 但红在 rc 上,
    是**仍在场的 CAS 层**贡献的, 卡文声称的 lost-update 断言 (attempt_count == 2)
    **从未真正被打红过**。那是「带层变异 + 假杀」: 变异报 KILLED, 击杀却由别的层给。
    现在先比状态: 账本记了几次评分, 笔记就必须算进几次 —— 无锁时两个进程各按旧
    基线算, 账本 2 行而 attempt_count 停在 1, 这条断言直接红, 与 rc 无关。
    """
    e1, e2 = f"板A-r{round_no}#q1", f"板B-r{round_no}#q1"
    p1 = _spawn_writer(vault, _payload(e1), f"c{round_no}a")
    p2 = _spawn_writer(vault, _payload(e2), f"c{round_no}b")
    r1 = p1.communicate(timeout=180)
    r2 = p2.communicate(timeout=180)
    ctx = f"P1 rc={p1.returncode}\nSTDOUT{r1[0]}\nSTDERR{r1[1]}\nP2 rc={p2.returncode}\nSTDOUT{r2[0]}\nSTDERR{r2[1]}"

    rows = _ledger_rows(vault)
    ids = [r["event_id"] for r in rows]
    node_text = (vault / NODE_REL).read_text(encoding="utf-8")
    att = _fm_value(vault, "attempt_count")

    # ⛔ 前提先立 (独立复核 R1-01 同型): 下面那条链式 `== 2` 在**全零**时同样失败, 抛出的
    # 还是那条 lost-update 消息 —— 两个写者都没跑成会伪装成「有一次被另一次盖掉了」。
    # (这里刻意**不复述**那条消息的原文: 负控脚本用它做 `expect_msg`, 而判据要求它在本文件里
    #  只出现一次 —— 连注释里的复述都会让那个唯一性自检变红。)
    assert len(rows) == 2, f"两个写者没有都落账, 本门的前提不成立 (这不是 lost update): ids={ids}\n{ctx}"

    # ── ① lost update 的判据: 账本里的评分次数 == 笔记算进的次数 ──
    #    (放在最前面, 不被任何 rc 断言遮住)
    applied = sum(1 for eid in (e1, e2) if f"quiz:{eid}" in node_text)
    assert int(att or 0) == len(rows) == applied == 2, (
        f"lost update: 账本 {len(rows)} 条评分, 笔记 attempt_count={att!r}, "
        f"校准记录里只有 {applied} 条 —— 有评分被另一次覆盖掉了。\n{ctx}"
    )
    assert sorted(ids) == sorted([f"quiz:{e1}", f"quiz:{e2}"]), f"账本应恰有两条事件, 实见 {ids}\n{ctx}"
    assert len(set(ids)) == len(ids), f"event_id 幂等键唯一性被并发破坏\n{ctx}"
    # 水位线必须是两条事件里更晚的那个采用时刻 (A3 会把同瞬间的第二条推到 W+1s)。
    latest = max(r["payload"]["review_time"] for r in rows)
    assert _fm_value(vault, "fsrs_last_review") == latest, f"frontmatter 未反映最新一条事件\n{ctx}"
    assert _validate(vault).returncode == 0, f"并发写出的账本未通过校验器\n{ctx}"

    # ── ② 次要断言: 两个进程都应正常收尾 (放在状态判据之后) ──
    assert p1.returncode == 0 and p2.returncode == 0, ctx


# ─────────────── 门② 账本并发追加: 幂等键唯一 + 无交错损坏 ───────────────

_APPEND_DRIVER = """
import os, pathlib, sys, time
sys.path.insert(0, sys.argv[1])
from app.services import learning_event_log as ev
ev._log_path = lambda: pathlib.Path(sys.argv[2])
# ⛔ 汇合点: 每个子进程要先 import 整个 app.services (秒级且抖动大)。不同步就
# 各自错开落地, 竞态窗口根本不重叠 —— 门看着绿, 其实什么都没测到 (实测: 去掉
# 锁的变异体照样让它全绿)。ready/go 把 import 时间从窗口里剔出去。
pathlib.Path(sys.argv[5]).write_text("1", encoding="utf-8")
while not os.path.exists(sys.argv[6]):
    time.sleep(0.005)
ok = ev.append_event("answer_scored", event_id=sys.argv[3], node_id=sys.argv[4])
sys.exit(0 if ok else 3)
"""


def _seed_ledger(ledger: Path, rows: int) -> None:
    """预置一个**有体量**的账本: 查重是全文件扫描, 行数决定临界区宽度。

    ⚠️ 空账本上的查重只要几十微秒, 六个进程同时进也可能不撞 —— 那样门测的是
    「今天恰好没撞」而不是「锁在起作用」。真实账本本来就会累积到这个量级。
    """
    import json as _json

    ledger.write_text(
        "".join(
            _json.dumps(
                {
                    "event_id": f"seed-{i}",
                    "event_version": 1,
                    "event_type": "candidate_created",
                    "node_id": "种子",
                    "recorded_at": TS1,
                    "effective_at": TS1,
                    "payload": {},
                },
                ensure_ascii=False,
            )
            + "\n"
            for i in range(rows)
        ),
        encoding="utf-8",
    )


def _run_barrier_appends(tmp_path: Path, ledger: Path, specs: list[tuple[str, str]]):
    """按汇合点同时释放 N 个追加进程, 返回各自 rc。"""
    backend = str(WT / "backend")
    go = tmp_path / "GO"
    procs = []
    for i, (eid, node) in enumerate(specs):
        ready = tmp_path / f"ready-{i}"
        procs.append(
            (
                ready,
                subprocess.Popen(
                    [sys.executable, "-c", _APPEND_DRIVER, backend, str(ledger), eid, node, str(ready), str(go)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                ),
            )
        )
    deadline = time.monotonic() + 180
    while not all(r.exists() for r, _ in procs):
        assert time.monotonic() < deadline, "子进程未在时限内就绪"
        time.sleep(0.05)
    go.write_text("1", encoding="utf-8")
    rcs = []
    for _, p in procs:
        p.communicate(timeout=180)
        rcs.append(p.returncode)
    return rcs


def test_concurrent_ledger_append_stays_wellformed(tmp_path):
    """8 个进程同时追加 → 8 行完整 JSONL, 无半行、无粘行、id 唯一。"""
    ledger = tmp_path / "learning_events.jsonl"
    _seed_ledger(ledger, 2000)
    rcs = _run_barrier_appends(tmp_path, ledger, [(f"e{i}", f"节点{i % 3}") for i in range(8)])
    assert rcs == [0] * 8, f"并发追加有进程失败: {rcs}"
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2008, f"并发追加丢/多行: {len(lines)}"
    ids = [json.loads(ln)["event_id"] for ln in lines[2000:]]  # 解析失败即交错损坏
    assert sorted(ids) == sorted(f"e{i}" for i in range(8))


def test_concurrent_ledger_append_same_id_writes_once(tmp_path):
    """同一个 event_id 被 6 个进程同时写 → 恰好 1 行 (查重与追加在同一把锁内)。"""
    ledger = tmp_path / "learning_events.jsonl"
    _seed_ledger(ledger, 2000)
    rcs = _run_barrier_appends(tmp_path, ledger, [("同一个", "节点X")] * 6)
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2001, f"幂等键唯一性被并发破坏: 多出 {len(lines) - 2000} 行"
    assert rcs.count(0) == 1, f"应恰有一个进程报写入成功, 实见 {rcs}"


def test_concurrent_cross_node_ledger_stays_wellformed(vault):
    """两个**不同节点**同时评分 → 账本两行都在且格式良好 (账本是跨节点共享写面)。

    ⚠️ per-node 锁挡不到这个形态 (两把不同的锁), 兜住它的是写点侧的账本追加锁。
    """
    node2 = vault / "节点" / "第二节点.md"
    node2.write_text(NODE_V0.replace("测试节点", "第二节点"), encoding="utf-8")
    p1 = _spawn_writer(vault, _payload("板A#q1"), "x1")
    p2 = _spawn_writer(vault, _payload("板B#q1", node="节点/第二节点.md"), "x2")
    r1, r2 = p1.communicate(timeout=180), p2.communicate(timeout=180)
    assert p1.returncode == 0, f"{r1[0]}\n{r1[1]}"
    assert p2.returncode == 0, f"{r2[0]}\n{r2[1]}"
    raw = (vault / "learning_events.jsonl").read_text(encoding="utf-8")
    assert "\n\n" not in raw, "账本出现空行 (两个写者各补了一次 LF)"
    rows = _ledger_rows(vault)
    assert sorted(r["node_id"] for r in rows) == ["测试节点", "第二节点"], rows
    assert _validate(vault).returncode == 0


_LEDGER_HOLD_DRIVER = """
import fcntl, os, sys, time
ev, out, hold = sys.argv[1], sys.argv[2], float(sys.argv[3])
fd = os.open(ev, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
fcntl.lockf(fd, fcntl.LOCK_EX)
print("held", flush=True)
time.sleep(hold)
with open(out, "w", encoding="utf-8") as f:
    f.write(str(os.path.getsize(ev)))   # 释放前的账本大小
os.close(fd)
"""

HOLD_S = 8.0


def test_writer_waits_for_held_ledger_lock(vault):
    """外部进程持有账本锁时, 写点必须**等**, 不得抢先追加。

    ⚠️ 判据有两条且互补:
      ① 持锁方释放前记下的账本大小仍是 0 —— 写点没在锁内追加;
      ② 写点的总耗时 >= 持锁时长的大部分 —— 它是**等**出来的, 不是「碰巧慢」。
    只有 ① 会被「写点本来就跑得比 8s 还慢」蒙混过去; 只有 ② 会被「写点在锁内
    写了但也确实等了别的东西」蒙混过去。两条一起才钉得住。
    """
    ev_path = vault / "learning_events.jsonl"
    size_file = vault.parent / "size-at-release.txt"
    holder = subprocess.Popen(
        [sys.executable, "-c", _LEDGER_HOLD_DRIVER, str(ev_path), str(size_file), str(HOLD_S)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        t0 = time.monotonic()
        rc, out, err = _run_writer(vault, _payload("板A#q1"), "hold1")
        elapsed = time.monotonic() - t0
    finally:
        holder.wait(timeout=60)
    assert rc == 0, f"rc={rc}\n{out}\n{err}"
    assert size_file.read_text(encoding="utf-8").strip() == "0", "持锁方释放前账本已经变大 —— 写点在别人持锁时抢写了"
    assert elapsed >= HOLD_S * 0.6, f"写点只用了 {elapsed:.1f}s, 没有真的等锁"
    assert len(_ledger_rows(vault)) == 1


def test_thread_critical_sections_do_not_overlap(monkeypatch, tmp_path):
    """H1: 两个线程的「取锁 → 收尾关闭 fd」区间必须**互不重叠**。

    ⛔ 为什么重叠就是缺陷: POSIX 记录锁是 per-process 的 —— 同进程第二个线程用
    另一个 fd 请求同一把锁会**立刻成功**(不阻塞)。所以只要 A 还没 close, B 就能
    「拿到」锁; 而 A 随后的 close 按「进程 × 文件」语义把**B 的**锁一并撤销。
    上一版把 `os.close(fd)` 放在 `with _write_lock` 之外, 正是这个重叠。
    ⛔ 判据是**记录下来的顺序**, 不是等待超时: 顺序里出现 A-acq → B-acq → A-close
    就判红, 与机器快慢无关。
    """
    import threading

    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text("", encoding="utf-8")
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)

    events, lock = [], threading.Lock()
    a_in_section = threading.Event()
    real_lock_exclusive, real_close = ev._lock_exclusive, os.close

    def traced_lock(fd, timeout):
        got = real_lock_exclusive(fd, timeout)
        name = threading.current_thread().name
        with lock:
            events.append((name, "acq"))
        if name == "A":
            a_in_section.set()
            # 给 B 一个**有界**的机会挤进来。修好之后 B 会被线程锁挡在门外,
            # 这 1.5s 就白等; 没修的话 B 会在这段时间里 acq, 顺序里就留下重叠。
            time.sleep(1.5)
        return got

    def traced_close(fd):
        with lock:
            events.append((threading.current_thread().name, "close"))
        return real_close(fd)

    monkeypatch.setattr(ev, "_lock_exclusive", traced_lock)
    monkeypatch.setattr(ev.os, "close", traced_close)

    tb_start = threading.Event()

    def run_a():
        ev.append_event("answer_scored", "A事件", node_id="N")

    def run_b():
        a_in_section.wait(timeout=30)  # 确保 B 是在 A 的临界区内才开始抢
        tb_start.set()
        ev.append_event("answer_scored", "B事件", node_id="N")

    ta, tb = threading.Thread(target=run_a, name="A"), threading.Thread(target=run_b, name="B")
    ta.start()
    tb.start()
    ta.join(timeout=120)
    tb.join(timeout=120)

    assert a_in_section.is_set() and tb_start.is_set(), "交接点没成立, 本门是空的"
    # 顺序必须是完整的两段: 每个线程的 acq 之后紧跟它自己的 close。
    assert len(events) == 4, f"事件数不对: {events}"
    seq = [f"{n}-{p}" for n, p in events]
    assert seq in (["A-acq", "A-close", "B-acq", "B-close"], ["B-acq", "B-close", "A-acq", "A-close"]), (
        f"两个线程的临界区重叠了 —— 先 acq 的那个还没 close, 另一个就拿到了同一把锁; "
        f"它的 close 会把对方的锁一并撤销。实测顺序: {seq}"
    )
    ids = [r["event_id"] for r in _rows_of(ledger)]
    assert sorted(ids) == ["A事件", "B事件"] and len(set(ids)) == 2, f"账本 IDs={ids}"


# ── 门⑥-ter 独立复核 (2026-09-05) 打回的四条回归的行为门 ──


def test_dedup_scan_splits_only_on_physical_lf(monkeypatch, tmp_path):
    """H2: 账本某行的字符串值含裸 U+2028/U+0085 时, 查重仍必须命中该 event_id。

    ⛔ `str.splitlines()` 会在这些字符上切行, 把一条合法记录切成两个碎片 ⇒ 都解析
    失败 ⇒ 查重漏命中 ⇒ 同一事件被写第二遍 ⇒ 幂等键唯一性破裂, 校验器判整份账本
    不合规。基线 `for line in f` 只切物理 LF。
    """
    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    for sep, name in (("\u2028", "U2028"), ("\u2029", "U2029"), ("\u0085", "NEL"), ("\x0b", "VT")):
        ledger.write_text("", encoding="utf-8")
        assert ev.append_event("answer_scored", f"quiz:{name}", node_id="N", payload={"note": f"前{sep}后"}), name
        assert ev.append_event("answer_scored", f"quiz:{name}", node_id="N", payload={"note": f"前{sep}后"}) is False, (
            f"{name}: 第二次写入没有被幂等挡住 —— 查重把含该字符的行切碎了"
        )
        lines = [x for x in ledger.read_text(encoding="utf-8").split("\n") if x.strip()]
        assert len(lines) == 1, f"{name}: 账本出现 {len(lines)} 行同 ID"
    probe = '{"a": "前\u2028后"}'
    assert len(probe.splitlines()) == 2 and len(probe.split("\n")) == 1, "本门前提不成立"


def test_short_write_is_not_reported_as_success(monkeypatch, tmp_path):
    """H4: os.write 短写必须返回 False, 不能报成功。"""
    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    real_write = os.write

    def short_write(fd, data):
        if b'"event_id"' in data:
            return real_write(fd, data[: len(data) // 2])
        return real_write(fd, data)

    monkeypatch.setattr(ev.os, "write", short_write)
    assert ev.append_event("answer_scored", "quiz:短写", node_id="N") is False, (
        "短写被报告成成功 —— 调用方会以为事件已入账"
    )


def test_out_of_order_is_caller_declared_not_auto_guessed(monkeypatch, tmp_path):
    """H3: 乱序标记只由调用方显式声明; 账本侧不得自动猜。"""
    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    ev.append_event(
        "answer_scored",
        "e1",
        node_id="N",
        payload=_review_payload(review_time="2026-08-01T10:00:00Z"),
        effective_at="2026-08-01T10:00:00Z",
    )
    ev.append_event(
        "answer_scored",
        "e0",
        node_id="N",
        payload=_review_payload(review_time="2026-08-01T09:00:00Z"),
        effective_at="2026-08-01T09:00:00Z",
    )
    rows = _rows_of(ledger)
    assert "out_of_order" not in rows[1]["payload"], (
        "账本侧自动猜了乱序 —— 它读不到已应用水位线, 猜错会让该节点永久写不进"
    )
    ev.append_event(
        "answer_scored",
        "e0b",
        node_id="N",
        payload=_review_payload(review_time="2026-08-01T09:30:00Z"),
        effective_at="2026-08-01T09:30:00Z",
        out_of_order=True,
    )
    assert _rows_of(ledger)[2]["payload"]["out_of_order"] is True
    ev.append_event("candidate_created", "c1", node_id="N", payload={"x": 1}, out_of_order=True)
    assert "out_of_order" not in _rows_of(ledger)[3]["payload"]


def test_illegal_out_of_order_form_does_not_hide_baseline(monkeypatch, tmp_path, caplog):
    """基准行的「未标」判定必须按 §6.2 冻结的布尔 true, 不能只看键存不存在。"""
    import logging

    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    pl = _review_payload(review_time="2026-08-01T10:00:00Z")
    pl["out_of_order"] = False
    ledger.write_text(
        json.dumps(
            {
                "event_id": "seed",
                "event_version": 1,
                "event_type": "answer_scored",
                "node_id": "N",
                "recorded_at": TS1,
                "effective_at": "2026-08-01T10:00:00Z",
                "payload": pl,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING, logger=ev.logger.name):
        ev.append_event(
            "answer_scored",
            "later",
            node_id="N",
            payload=_review_payload(review_time="2026-08-01T09:00:00Z"),
            effective_at="2026-08-01T09:00:00Z",
        )
    assert any("不晚于本节点账本里最新的" in r.getMessage() for r in caplog.records), (
        f"非法形态的 out_of_order 把基准行藏掉了 —— 迟到告警没触发: {[r.getMessage() for r in caplog.records]}"
    )


# ─────────────── 门③ CAS: 外部写者插队 → 零写 + 重跑收敛 ───────────────

RACE_MARK = "\n<!-- 外部写者在评分进行中插入的一段正文 -->\n"


def _race_env(vault: Path) -> dict[str, str]:
    """竞态注入用的 env —— 凭据路径与注入路径的**唯一**派生点。

    ⛔ 三处注入点 (`_install_racing_bridge` 与 M13 门自己那份内联注入) 都从这里取, 不各拼
    一次: 注入路径与 `_race_fired()` 查的凭据路径一旦分叉, 前提断言会恒红或恒真, 两个方向
    都会毁掉判据。
    """
    return {"G33_RACE_NODE": str((vault / NODE_REL).resolve())}


def _install_racing_bridge(vault: Path) -> tuple[str, dict[str, str]]:
    """把 fsrs_bridge 换成「真源码 + 在 main() 首行改一次节点」的版本。

    ⚠️ 这不是 mock: 除注入的那一行外逐字是生产源码, FSRS 真实参与。注入点选
    `main()` 是因为写点在**读节点之后、发布之前**才调 bridge —— 那正是 CAS
    要挡的时序 (Obsidian 里手改笔记恰好落在这个窗口)。
    """
    real = (VAULT_SCRIPTS / "fsrs_bridge.py").read_text(encoding="utf-8")
    anchor = "def main() -> int:\n"
    assert real.count(anchor) == 1, "fsrs_bridge.main 锚点漂移"
    inject = (
        anchor
        + "    import os as _os\n"
        + "    _rn = _os.environ.get('G33_RACE_NODE')\n"
        + "    if _rn:\n"
        + "        with open(_rn, 'a', encoding='utf-8') as _rf:\n"
        + f"            _rf.write({RACE_MARK!r})\n"
        # ⛔ 与节点正文**无关**的独立凭据: 证明这次注入真的执行过 (独立复核 R1-02)。
        # 少了它, 「注入根本没跑成」与「注入的正文被恢复发布覆盖掉」在最终正文上
        # 长得一模一样 —— 前者会伪装成后者。
        + "        with open(_rn + '.race-fired', 'a', encoding='utf-8') as _sf:\n"
        + "            _sf.write('1')\n"
    )
    p = vault / ".claude" / "scripts" / "fsrs_bridge.py"
    p.unlink()
    p.write_text(real.replace(anchor, inject, 1), encoding="utf-8")
    # ⛔ 连 env 一起返回: 凭据路径 (`_race_fired`) 与注入路径 (`G33_RACE_NODE`) 由**同一处**
    # 代码派生 (`_race_env`), 不靠调用方各自拼一次 —— 否则两者哪天不一致, 凭据会恒不存在
    # (前提断言恒红) 或恒存在 (前提断言恒真), 两个方向都会毁掉判据。
    return real, _race_env(vault)


def _race_fired(vault: Path) -> bool:
    """竞态注入的那段代码到底跑没跑过 —— **与节点正文无关**的独立凭据。

    ⛔ 为什么必须与节点正文无关: 「注入根本没跑成」与「注入的正文被发布整份覆盖掉」在
    最终正文上长得一模一样。凭据名是 `<节点>.race-fired`, 而发布走
    `os.replace(<节点>.quiz-tmp, <节点>)` —— 名字不同, 覆盖吃不掉它。
    """
    node = (vault / NODE_REL).resolve()
    return (node.parent / (node.name + ".race-fired")).exists()


def test_cas_conflict_refuses_and_rerun_converges(vault):
    real_src, race_env = _install_racing_bridge(vault)
    node = vault / NODE_REL

    rc, out, err = _run_writer(vault, _payload("板A#q1"), "cas1", race_env)
    # ⛔ 前提先立 (内部对抗审查): 这条门此前只靠断言顺序, 我判断过「rc 断言在前所以安全」——
    # **那个判断是错的**。它只挡住「运行期即死 ⇒ rc≠0」那一种失效, 挡不住**注入本身失效**:
    # 那时未变异与变异后都 rc=0, 红的是同一条断言、同一段文本, 而那段文本正是 M2 的
    # expect_msg ⇒ 假杀。harness 从不跑基线, expect_msg 是唯一区分手段。
    assert _race_fired(vault), f"竞态注入没有触发, 本门的前提不成立\nSTDOUT{out}\nSTDERR{err}"
    assert rc != 0, f"外部写者插队后仍照常发布 = CAS 门没起作用\nSTDOUT{out}"
    assert "CAS 冲突" in err, f"拒因不是 CAS 冲突: {err[-600:]}"
    text = node.read_text(encoding="utf-8")
    assert RACE_MARK.strip() in text, "外部写者的改动应当还在 (fixture 前提)"
    # ⛔ 判据是「外部写者那段正文还在 + 评分未落定」: 若写点照旧发布, 它会用
    # 内存里的旧 body 整份覆盖, 那段正文就消失了。
    assert "attempt_count:" not in text, "CAS 冲突后仍推进了 attempt (非零写)"
    assert "fsrs_last_review:" not in text, "CAS 冲突后仍推进了水位线"

    # 重跑 = 重新拿锁、重新读盘、重新计算 —— write-ahead + event_id 幂等保证收敛。
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").write_text(real_src, encoding="utf-8")
    rc2, out2, err2 = _run_writer(vault, _payload("板A#q1"), "cas2")
    assert rc2 == 0, f"重跑未收敛: rc={rc2}\nSTDOUT{out2}\nSTDERR{err2}"
    text2 = node.read_text(encoding="utf-8")
    assert RACE_MARK.strip() in text2, "重跑把外部写者的正文吃掉了"
    assert _fm_value(vault, "attempt_count") == "1"
    assert len(_ledger_rows(vault)) == 1, "重跑不得双写账本"
    assert _validate(vault).returncode == 0


def test_cas_token_and_conflict_semantics():
    """CAS 口径单测: revision 变、正文变、文件消失, 三种都必须判冲突。"""
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        sys.modules.pop("fsrs_bridge", None)
        import fsrs_bridge as fb  # pyright: ignore[reportMissingImports]
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
    tok = fb.cas_token(NODE_V0)
    assert tok["attempt_count"] is None and tok["fsrs_last_review"] is None
    rev = fb.cas_revision('attempt_count: "3"\nfsrs_last_review: 2026-08-01T10:00:00Z\n')
    assert rev == {"fsrs_last_review": "2026-08-01T10:00:00Z", "attempt_count": 3}, rev
    assert fb.cas_conflict("/nonexistent/节点.md", tok), "读不到文件必须算冲突"
    sys.modules.pop("fsrs_bridge", None)


def test_cas_body_only_change_is_a_conflict(tmp_path):
    """⛔ 只比 revision 两字段是不够的: 正文被改而 revision 不变时也必须判冲突。

    写点从读入那一刻起就把 body 留在内存里、发布时整份覆盖 —— 放行 = 静默吃掉
    用户刚补的正文。
    """
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        sys.modules.pop("fsrs_bridge", None)
        import fsrs_bridge as fb  # pyright: ignore[reportMissingImports]
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
    f = tmp_path / "n.md"
    f.write_text(NODE_V0, encoding="utf-8")
    tok = fb.cas_token(NODE_V0)
    assert fb.cas_conflict(str(f), tok) is None
    f.write_text(NODE_V0 + "用户后补的一段。\n", encoding="utf-8")
    why = fb.cas_conflict(str(f), tok)
    assert why and "正文" in why, f"正文改动未判冲突: {why!r}"
    assert fb.cas_revision(NODE_V0) == fb.cas_revision(NODE_V0 + "用户后补的一段。\n"), (
        "本门的前提: 这两份的 revision 面必须相同, 否则测的不是 body-only 场景"
    )
    sys.modules.pop("fsrs_bridge", None)


# ─────────────── 门④ 乱序补录: 加性标记 + frontmatter 不回退 ───────────────


def _review_payload(**over) -> dict:
    pl = {
        "schema_ext": "review/1",
        "vault_id": "canvas_vault_测试",
        "concept_id": "测试节点",
        "rating": 3,
        "grade_norm": 0.75,
        "review_time": TS1,
        "scored_at": TS1,
        "fsrs_library_version": "degraded:historic-run",
        "fsrs_params_hash": "degraded:historic-run",
        "exam_board": "检验白板/旧板.md",
        "attempt_count": 1,
    }
    pl.update(over)
    return pl


def test_out_of_order_marker_is_additive(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_log_path", lambda: tmp_path / "learning_events.jsonl")
    assert ev.append_event(
        "answer_scored",
        "e1",
        node_id="测试节点",
        payload=_review_payload(review_time="2026-08-01T10:00:00Z"),
        effective_at="2026-08-01T10:00:00Z",
    )
    caller_payload = _review_payload(review_time="2026-08-01T09:00:00Z")
    # ⛔ 加性比较的期望值必须有**独立来源**: 拿 caller_payload 本身当基准, 等于让
    # 被测函数自己提供期望值 —— 它若就地污染了这个 dict, 基准跟着一起变。这里留一份
    # 调用前的快照, 加性只对它比; 「有没有被就地污染」由下面那条断言单独负责。
    caller_snapshot = copy.deepcopy(caller_payload)
    # ⛔ 补录必须由**调用方显式声明** —— 账本侧读不到已应用水位线, 自动猜两个方向都会错
    # (误标会让写点对该节点永久 fail-closed; 漏标会把真实复习静默丢弃)。
    assert ev.append_event(
        "answer_scored",
        "e0",
        node_id="测试节点",
        payload=caller_payload,
        effective_at="2026-08-01T09:00:00Z",
        out_of_order=True,
    )
    rows = [json.loads(x) for x in (tmp_path / "learning_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert "out_of_order" not in rows[0]["payload"], "首个事件不该被标乱序"
    assert rows[1]["payload"]["out_of_order"] is True, "更早的补录事件必须标 out_of_order"
    # 加性: 除多这一个键外, payload 其余键逐字不变。
    assert {k: v for k, v in rows[1]["payload"].items() if k != "out_of_order"} == caller_snapshot, (
        "out_of_order 标记不是加性的: 除该键外, payload 其余键必须与调用方传进来的逐字相同"
    )
    # ⛔ 不得就地改调用方的 dict —— 同一个 payload 对象被复用时会把标记带到下一条。
    assert "out_of_order" not in caller_payload, "append_event 就地污染了调用方的 payload"
    # ⛔ 「没多这个键」不等于「一个字节没动」(独立复核 R1-04): 改用快照做加性比较后,
    # 「就地改调用方**已有**字段」这一形态就没人管了。整份比一次补回来。
    assert caller_payload == caller_snapshot, "append_event 改动了调用方 payload 的已有字段"


def test_later_and_foreign_events_are_not_marked(monkeypatch, tmp_path):
    """没有显式声明时, 任何事件都不该被打标 (账本侧不猜)。"""
    monkeypatch.setattr(ev, "_log_path", lambda: tmp_path / "learning_events.jsonl")
    ev.append_event("answer_scored", "a1", node_id="N1", payload=_review_payload(), effective_at="2026-08-01T10:00:00Z")
    # 更晚 → 不标
    ev.append_event("answer_scored", "a2", node_id="N1", payload=_review_payload(), effective_at="2026-08-01T11:00:00Z")
    # 更早但**别的节点** → 不标 (乱序是 per-node 语义)
    ev.append_event("answer_scored", "b1", node_id="N2", payload=_review_payload(), effective_at="2026-07-01T10:00:00Z")
    # 更早但**不是复习事件族** → 不标 (别的 event_type 没有水位线语义)
    ev.append_event(
        "candidate_created", "c1", node_id="N1", payload={"foo": "bar"}, effective_at="2026-07-01T10:00:00Z"
    )
    rows = [json.loads(x) for x in (tmp_path / "learning_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all("out_of_order" not in r["payload"] for r in rows), [
        r["event_id"] for r in rows if "out_of_order" in r["payload"]
    ]


def test_marked_event_does_not_regress_frontmatter(vault, monkeypatch):
    """乱序补录行注入后: 水位线不回退、attempt 不被它多加一次、后续评分照常。"""
    rc, out, err = _run_writer(vault, _payload("板A#q1"), "oo1")
    assert rc == 0, f"{out}\n{err}"
    w_after_first = _fm_value(vault, "fsrs_last_review")
    assert w_after_first == TS1

    monkeypatch.setattr(ev, "_log_path", lambda: vault / "learning_events.jsonl")
    assert ev.append_event(
        "answer_scored",
        "quiz:旧板#q9",
        node_id="测试节点",
        payload=_review_payload(review_time="2026-07-01T10:00:00Z", scored_at="2026-07-01T10:00:00Z"),
        effective_at="2026-07-01T10:00:00Z",
        out_of_order=True,  # 显式走 §6.2 补录通道
    )
    rows = _ledger_rows(vault)
    assert rows[-1]["payload"]["out_of_order"] is True

    rc2, out2, err2 = _run_writer(
        vault, _payload("板B#q1", ts="2026-08-01T10:10:00Z", review_time="2026-08-01T10:10:00Z"), "oo2"
    )
    assert rc2 == 0, f"补录行让后续评分卡死: {out2}\n{err2}"
    assert _fm_value(vault, "fsrs_last_review") == "2026-08-01T10:10:00Z", "水位线回退了"
    assert _fm_value(vault, "attempt_count") == "2", "补录行被误算进 attempt"
    assert _validate(vault).returncode == 0


# ─────────────── 门⑤ 幂等: 中断重跑不产生重复 event_id ───────────────


def test_rerun_is_idempotent(vault):
    rc, out, err = _run_writer(vault, _payload("板A#q1"), "id1")
    assert rc == 0, f"{out}\n{err}"
    node_sha = (vault / NODE_REL).read_bytes()
    rc2, out2, err2 = _run_writer(vault, _payload("板A#q1"), "id2")
    assert rc2 == 0, f"重跑 rc={rc2}: {out2}\n{err2}"
    assert "幂等跳过" in out2, out2
    assert (vault / NODE_REL).read_bytes() == node_sha, "幂等重跑改动了节点"
    ids = [r["event_id"] for r in _ledger_rows(vault)]
    assert ids == ["quiz:板A#q1"], ids
    assert _validate(vault).returncode == 0


# ─────────────── 门⑥ 锁本体: 超时不静默降级 + 跨进程真互斥 ───────────────

_HOLD_DRIVER = """
import fcntl, os, sys, time
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o644)
fcntl.lockf(fd, fcntl.LOCK_EX)
print("held", flush=True)
time.sleep(float(sys.argv[2]))
"""


def test_lock_exclusive_times_out_instead_of_writing(tmp_path):
    """⛔ 取不到锁时必须返回 False (调用方拒写), 不得静默降级为「没锁也写」。"""
    lk = tmp_path / "l.lock"
    holder = subprocess.Popen([sys.executable, "-c", _HOLD_DRIVER, str(lk), "5"], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        fd = os.open(str(lk), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            t0 = time.monotonic()
            got = ev._lock_exclusive(fd, 0.5)
            waited = time.monotonic() - t0
        finally:
            os.close(fd)
        assert got is False, "别的进程持锁时却报取到了锁"
        assert waited >= 0.5, f"没有真的等满超时 ({waited:.2f}s)"
    finally:
        holder.kill()
        holder.wait(timeout=10)


def test_append_event_refuses_when_ledger_locked(tmp_path, monkeypatch, caplog):
    ledger = tmp_path / "learning_events.jsonl"
    ledger.write_text("", encoding="utf-8")
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    monkeypatch.setattr(ev, "LEDGER_LOCK_TIMEOUT_S", 0.4)
    holder = subprocess.Popen([sys.executable, "-c", _HOLD_DRIVER, str(ledger), "6"], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        assert ev.append_event("answer_scored", "quiz:被锁住", node_id="N") is False, (
            "别人持着账本锁时 append_event 却报了写入成功"
        )
        assert ledger.read_text(encoding="utf-8") == "", "取不到锁却写了"
    finally:
        holder.kill()
        holder.wait(timeout=10)


# ── 门⑥-bis POSIX 记录锁的释放语义: 持锁期间不得再 open 同一个文件 ──
# ⚠️ 这一组是本卡**读代码时**发现的真缺陷的回归门 —— 三处账本锁原本都在持锁期间
#    做了一次「人畜无害」的 `with open(path) as f`, 收尾即丢锁, 后面的 write 是
#    裸奔的; 而既有的三道锁门测的都是「取锁那一刻」, 全部看不见它。

_POSIX_PROBE = """
import fcntl, os, sys
fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o644)
try:
    fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print("FREE")
except OSError:
    print("HELD")
"""


def _probe_lock(path) -> str:
    r = subprocess.run([sys.executable, "-c", _POSIX_PROBE, str(path)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


def test_posix_record_lock_is_released_by_any_unrelated_close(tmp_path):
    """把 OS 语义钉成门: 关掉**任意**一个指向该文件的 fd ⇒ 本进程的锁整体消失。

    这不是在测我们的代码, 是在测「为什么 `_read_all` 必须只用同一个 fd」——
    后人若把它改回 `open(path).read()`, 先看到这条注释再看到下一道行为门。
    """
    import fcntl

    f = tmp_path / "ledger.jsonl"
    f.write_bytes(b"x\n")
    fd = os.open(str(f), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        assert _probe_lock(f) == "HELD", "刚加的锁就没生效, 门的前提不成立"
        with open(f, encoding="utf-8") as g:  # 一次「无关的」读
            g.read()
        assert _probe_lock(f) == "FREE", "本机 POSIX 记录锁不按「进程 × 文件」释放 —— 那么 _read_all 的理由需要重估"
    finally:
        os.close(fd)


def test_read_all_does_not_drop_the_lock(tmp_path):
    """`_read_all` 读完之后锁必须还在（与上一条正好相反的行为）。"""
    import fcntl

    f = tmp_path / "ledger.jsonl"
    f.write_bytes(b'{"event_id":"a"}\n')
    fd = os.open(str(f), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        assert ev._read_all(fd) == b'{"event_id":"a"}\n'
        assert _probe_lock(f) == "HELD", "_read_all 之后锁丢了 —— 它一定是另开了 fd"
    finally:
        os.close(fd)


#: 子进程驱动: 在**生产 write 的那一刻**握手停住, 让父进程当场探锁。
#: ⛔ 用握手而不是时间阈值 (独立复核 M3 实测): 上一版判据是「抢到锁后子进程还剩
#: 多少活 > 60ms」, 定向调度下**双向都能翻**——只延迟 done 写入 150ms 就假红,
#: 真施加丢锁变异再让父探针暂停 1s 就假绿。握手把「此刻是否持锁」变成可直接观测。
_SCAN_CHILD = """
import os, pathlib, sys, time
sys.path.insert(0, sys.argv[1])
from app.services import learning_event_log as ev
ev._log_path = lambda: pathlib.Path(sys.argv[2])
ready, go, done, atwrite, resume = (pathlib.Path(sys.argv[i]) for i in (3, 4, 5, 6, 7))
_real_write = os.write

def hooked(fd, data):
    # 记录行(而不是 LF 守卫)即将落盘时停住: 此刻仍在临界区内, 锁必须还在手上。
    if b'"event_id"' in data and not atwrite.exists():
        atwrite.write_text("1", encoding="utf-8")
        while not resume.exists():
            time.sleep(0.002)
    return _real_write(fd, data)

os.write = hooked
ev.os.write = hooked
ready.write_text("1", encoding="utf-8")
while not go.exists():
    time.sleep(0.002)
ok = ev.append_event("answer_scored", "扫描期探针", node_id="N")
done.write_text("1" if ok else "0", encoding="utf-8")
"""


def test_append_event_still_holds_lock_at_the_moment_of_write(tmp_path):
    """`append_event` 在**真正落盘的那一刻**必须仍持有账本锁。

    ⛔ 判据是「此刻探锁拿不拿得到」, 不是任何时长阈值 —— 子进程在生产 os.write
    前停住并留下 atwrite 标记, 父进程这时去抢锁: 抢到 = 它中途把锁丢了。
    ⚠️ 前提自证: 必须真的观察到 atwrite 标记, 否则握手没成立、本门是空的。
    """
    ledger = tmp_path / "learning_events.jsonl"
    _seed_ledger(ledger, 200)  # 不再需要巨账本: 判据与耗时无关
    backend = str(WT / "backend")
    ready, go, done, atwrite, resume = (tmp_path / n for n in ("ready", "go", "done", "atwrite", "resume"))
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _SCAN_CHILD,
            backend,
            str(ledger),
            str(ready),
            str(go),
            str(done),
            str(atwrite),
            str(resume),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    stolen = None
    try:
        deadline = time.monotonic() + 180
        while not ready.exists():
            assert time.monotonic() < deadline, "子进程未就绪"
            time.sleep(0.02)
        go.write_text("1", encoding="utf-8")
        while not atwrite.exists():
            assert time.monotonic() < deadline, "没等到落盘前的握手点"
            assert child.poll() is None, f"子进程提前退出: {child.communicate()}"
            time.sleep(0.005)
        stolen = _probe_lock(ledger) == "FREE"  # 此刻探锁
        resume.write_text("1", encoding="utf-8")
        child.communicate(timeout=120)
    finally:
        if child.poll() is None:
            child.kill()
    assert atwrite.exists(), "握手点没成立, 本门是空的"
    assert stolen is False, "落盘那一刻账本锁已经不在手上 —— 临界区中途丢锁了"
    assert done.read_text(encoding="utf-8") == "1", "子进程没写成功"


def test_skill_ledger_section_opens_no_second_fd():
    """形态门: 写点侧账本临界区内不得再 open 账本。

    ⚠️ 如实说明这是**形态门不是行为门**: 写点侧那个窗口只有几十微秒
    (LF 守卫 close 之后紧接着就是 write), 行为门无法确定性复现。它与
    `test_append_event_holds_lock_across_the_whole_scan`(backend 侧, 真行为门)
    是同一个缺陷的两侧 —— 那一侧证明了这个缺陷是真的, 这一侧防它在写点侧复发。
    """
    body = CODE[CODE.index("_lock_exclusive(_fd, _LEDGER_LOCK_TIMEOUT_S") :]
    body = body[: body.index("_n = os.write(_fd, _line)")]
    # ⛔ 必须剥掉注释行再扫: 生产代码的注释里**引用了**旧写法 `with open(EV, "rb")`
    # 作为反面教材, 直接 grep 会命中那句解释 —— 判据被自己要防的字符串喂饱
    # (「判据不能自指」的又一形态; 首版就是这么假红的)。
    body = "\n".join(ln for ln in body.splitlines() if not ln.strip().startswith("#"))
    assert "open(EV" not in body, (
        "写点侧账本临界区内出现了 open(EV…) —— POSIX 记录锁按「进程 × 文件」释放, "
        f"这一句 close 时锁就整体没了。片段: {body[:400]!r}"
    )
    assert "os.lseek(_fd" in body and "os.read(_fd" in body, (
        "临界区里既没有 open(EV 也没有走 _fd 读 —— 判据可能因重构而落空(形态门失效)"
    )


# ─────────────── 门⑦ A3 增量归纳块: 同一把锁 + 不吃掉别人的写入 ───────────────


def _incr_code(vault: Path, callouts: list[str], tag: str) -> str:
    pfile = vault.parent / f"incr-{tag}.json"
    pfile.write_text(json.dumps({"node": NODE_REL, "callouts": callouts}, ensure_ascii=False), encoding="utf-8")
    return INCR_CODE.replace('"/tmp/quiz-answer-incr.json"', json.dumps(str(pfile)))


def _node_lock_path(vault: Path) -> Path:
    import hashlib

    node = vault / NODE_REL
    lk_dir = vault / ".locks"
    lk_dir.mkdir(exist_ok=True)
    return lk_dir / ("node-" + hashlib.sha1(str(node.resolve()).encode("utf-8")).hexdigest()[:16] + ".lock")


#: 持锁进程: 取锁 → 报 held → 等一会 → **整份重写**节点 → 放锁。
#: ⛔ 必须是「重写」不是「追加」(独立审查实测): 追加时两边的产物在文件里都留得住,
#: 于是把锁拆掉这道门照样全绿 —— 它是死门。重写才能让「谁基于旧内容算」显形。
_NODE_HOLDER_SRC = """
import fcntl, os, sys, time
lk, node, marker = sys.argv[1], sys.argv[2], sys.argv[3]
fd = os.open(lk, os.O_RDWR | os.O_CREAT, 0o644)
fcntl.lockf(fd, fcntl.LOCK_EX)
print("held", flush=True)
time.sleep(1.5)
s = open(node, encoding="utf-8").read()
open(node, "w", encoding="utf-8").write(s.rstrip() + "\\n" + marker + "\\n")
os.close(fd)
"""


def test_incremental_block_waits_for_node_lock(vault):
    """A3 增量块必须**等** per-node 锁, 并在持锁方写完的新内容上追加。

    ⛔ 判据是「两段内容都在」+「归纳的那段在持锁方那段**之后**」——
    只断言两段都在的话, 拆掉锁它照样绿 (append-only 的正文两边都留得住)。
    持锁方做的是整份重写, 所以无锁时增量块会拿旧内容覆盖掉它。
    """
    node = vault / NODE_REL
    marker = "持锁进程重写时加的一行。"
    holder = subprocess.Popen(
        [sys.executable, "-c", _NODE_HOLDER_SRC, str(_node_lock_path(vault)), str(node), marker],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        proc = subprocess.run(
            [sys.executable, "-c", _incr_code(vault, ["> [!question]+ 新疑问一条"], "w")],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(vault),
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        assert proc.returncode == 0, f"{proc.stdout}\n{proc.stderr}"
    finally:
        holder.wait(timeout=60)
    text = node.read_text(encoding="utf-8")
    assert marker in text, "增量块基于旧内容整份覆盖, 把持锁方的重写吃掉了 (lost update)"
    assert "新疑问一条" in text, "增量块没归纳成功"
    assert text.index(marker) < text.index("新疑问一条"), (
        "归纳出现在持锁方那段之前 —— 说明增量块读到的是**旧**内容, 没有真的等锁"
    )


def test_incremental_block_cas_preserves_racing_edit(vault):
    """A3 的 CAS: 读盘之后被外部改动 → 必须重读重算, 不能拿旧 body 覆盖。

    注入点用 fixture 里的 `fsrs_bridge.cas_token` 包装器 —— 它恰好在增量块
    「读完 → 还没写」之间被调用, 就是 CAS 要挡的时序。
    """
    real = (VAULT_SCRIPTS / "fsrs_bridge.py").read_text(encoding="utf-8")
    anchor = "def cas_token(node_text: str) -> dict:\n"
    assert real.count(anchor) == 1, "cas_token 锚点漂移"
    inject = (
        anchor
        + "    import os as _os\n"
        + "    _rn = _os.environ.get('G33_RACE_NODE')\n"
        + "    if _rn and not _os.environ.get('G33_RACE_DONE'):\n"
        + "        _os.environ['G33_RACE_DONE'] = '1'\n"
        + "        with open(_rn, 'a', encoding='utf-8') as _rf:\n"
        + "            _rf.write('外部写者在读后写前加的一行。\\n')\n"
        # ⛔ 与 `_install_racing_bridge` 同一套独立凭据 (内部对抗审查): 这条门此前只看
        # 最终正文里有没有那一行, 而「注入根本没跑成」与「注入被整份覆盖吃掉」在正文上
        # 无法区分 —— 同型假杀面。
        + "        with open(_rn + '.race-fired', 'a', encoding='utf-8') as _sf:\n"
        + "            _sf.write('1')\n"
    )
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").unlink()
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").write_text(real.replace(anchor, inject, 1), encoding="utf-8")

    node = vault / NODE_REL
    proc = subprocess.run(
        [sys.executable, "-c", _incr_code(vault, ["> [!question]+ 疑问A"], "cas")],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(vault),
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **_race_env(vault)),
    )
    assert proc.returncode == 0, f"{proc.stdout}\n{proc.stderr}"
    assert _race_fired(vault), f"竞态注入没有触发, 本门的前提不成立\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    text = node.read_text(encoding="utf-8")
    assert "外部写者在读后写前加的一行。" in text, "CAS 没挡住: 增量块拿读盘时的旧 body 覆盖了外部写者的改动"
    assert "疑问A" in text, "重读重算之后归纳丢了"
    assert "CAS 冲突" in proc.stdout, f"没有走到重读重算分支: {proc.stdout}"


def test_writer_refuses_when_other_writer_took_the_event_id(vault):
    """H5: 取得账本锁后发现同 event_id 已被别的写者写入 → fail-closed, 不追加。"""
    real = (VAULT_SCRIPTS / "fsrs_bridge.py").read_text(encoding="utf-8")
    anchor = "def main() -> int:\n"
    assert real.count(anchor) == 1
    # bridge 在「账本快照之后、追加之前」被调用 —— 正是别的写者插队的窗口。
    inject = (
        anchor
        + "    import os as _os, json as _json\n"
        + "    _ev = _os.environ.get('G33_RACE_LEDGER')\n"
        + "    if _ev and not _os.environ.get('G33_RACE_DONE'):\n"
        + "        _os.environ['G33_RACE_DONE'] = '1'\n"
        + "        _row = {'event_id': 'quiz:板A#q1', 'event_version': 1,\n"
        + "                'event_type': 'answer_scored', 'node_id': '测试节点',\n"
        + "                'recorded_at': '2026-08-01T10:00:00Z',\n"
        + "                'effective_at': '2026-08-01T10:00:00Z', 'payload': {}}\n"
        + "        with open(_ev, 'a', encoding='utf-8') as _lf:\n"
        + "            _lf.write(_json.dumps(_row, ensure_ascii=False) + '\\n')\n"
    )
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").unlink()
    (vault / ".claude" / "scripts" / "fsrs_bridge.py").write_text(real.replace(anchor, inject, 1), encoding="utf-8")

    rc, out, err = _run_writer(
        vault,
        _payload("板A#q1"),
        "steal",
        {"G33_RACE_LEDGER": str((vault / "learning_events.jsonl").resolve())},
    )
    rows = _ledger_rows(vault)
    ids = [r["event_id"] for r in rows]
    # ⛔ 前提与后果必须是**两条断言身份** (独立复核 R1-01)。`count(...) == 1` 在账本
    # **零行**时同样失败, 抛出的还是下面那条重复写入的消息 (只是 ids 为空列表) —— 于是
    # 「变异体在追加之前就死了(编译期或运行期)」会伪装成「重复写入被抓到」。先立前提:
    # 插队写者至少写下了那一行。
    # (同上: 注释里刻意不复述那条消息原文, 它是负控的 `expect_msg`, 须在本文件里唯一。)
    assert ids.count("quiz:板A#q1") >= 1, (
        f"账本里一行都没有 —— 写点在追加之前就死了, 本门的前提不成立 (这不是重复写入): {ids}\n{out}\n{err}"
    )
    assert ids.count("quiz:板A#q1") == 1, f"同 event_id 被写了两遍: {ids}"
    assert rc != 0, f"别的写者抢先写了同 ID, 本块却照常收尾\n{out}\n{err}"
    assert "取得账本锁后发现" in err, f"拒因不对: {err[-500:]}"


def test_exam_board_waits_for_held_ledger_lock(vault):
    """建板写点也必须等账本锁 (它是第三个共享写者)。"""
    ev_path = vault / "learning_events.jsonl"
    size_file = vault.parent / "seb-size.txt"
    holder = subprocess.Popen(
        [sys.executable, "-c", _LEDGER_HOLD_DRIVER, str(ev_path), str(size_file), str(HOLD_S)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        t0 = time.monotonic()
        proc = subprocess.run(
            [sys.executable, "-c", _exam_board_code(vault, "板X")],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(vault),
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        elapsed = time.monotonic() - t0
    finally:
        holder.wait(timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert size_file.read_text(encoding="utf-8").strip() == "0", "建板在别人持锁时抢写了账本"
    assert elapsed >= HOLD_S * 0.6, f"建板只用了 {elapsed:.1f}s, 没有真的等锁"
    assert len(_ledger_rows(vault)) == 1, "建板事件没落账"


def test_incremental_block_is_content_idempotent(vault):
    node = vault / NODE_REL
    for tag in ("i1", "i2"):
        proc = subprocess.run(
            [sys.executable, "-c", _incr_code(vault, ["> [!question]+ 同一条疑问"], tag)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(vault),
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        assert proc.returncode == 0, proc.stderr
    assert node.read_text(encoding="utf-8").count("同一条疑问") == 1, "增量块重跑双写"


# ───────── 门⑧ 两条**恢复路径**的发布点也必须过 CAS (CARD-G3-3-R1) ─────────
# ⛔ 为什么单列: `_cas_guard` 在写点里有三个调用点 —— 正常路径、A2 foreign 重放后
#    的恢复发布、dup 恢复路径发布。此前只有正常路径有门承重, 另外两个属于「已实现
#    但没有任何门测它」的形态: 把它们拆掉整份测试照样全绿。恢复动作与正常路径一样是
#    **整份覆盖** frontmatter+正文, 少一道 CAS 就是恢复动作自己把用户的并发编辑吃掉。


def _seed_review_row(vault: Path, event_id: str, exam_board: str) -> dict:
    """往 fresh vault 的账本里放**一条**待恢复的 review/1 行。

    形态逐字照抄生产写侧真实产出的行 (顶层 6 键 + payload 11 键, 实测于本 fixture),
    只改 event_id / exam_board —— 自造形态过不了写点侧的 `validate_record_full`,
    「fixture 形态 ≠ 生产形态」是本仓踩过的坑。
    ⛔ 只放**一条**: 若本次事件也在账本里, 会先撞 SKILL.md 的「本次事件与别人的事件
    同处待恢复队列」fail-closed, 那样测到的就不是 CAS 了。
    """
    row = {
        "event_id": event_id,
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": _review_payload(exam_board=exam_board),
    }
    (vault / "learning_events.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    return row


def test_a2_foreign_recovery_publish_respects_cas(tmp_path):
    """A2 foreign 重放后的恢复发布必须先过 CAS。

    ⚠️ 双段。**对照段不可省**: 只跑「注入竞态 → 失败」的话, 失败也可能是因为这个
    seed 根本没走到恢复发布 (被采用时刻门 / attempt 序数门先拦下), 那样门是空的。
    对照段先证明同一个 seed 真的走完了 foreign 重放并把恢复结果落了盘。
    ⚠️ **如实**: foreign 恢复路径按设计以非零码收尾 (`恢复已落定, 本次评分未写入 —
    请重跑`), 所以对照段的判据是「恢复结果落了盘 + 拒因是续跑要求」, 不是 rc==0。
    """
    # ── 对照: 不注入竞态 ──
    ctrl = _make_vault(tmp_path / "ctrl")
    _seed_review_row(ctrl, "quiz:板Z#q9", "检验白板/板Z#q9.md")
    rc0, out0, err0 = _run_writer(ctrl, _payload("板A#q1"), "fgn-ctrl")
    assert "A2 已恢复 1 个未完成事件" in out0, f"对照段没走到 foreign 恢复发布, 本门是空的\n{out0}\n{err0}"
    assert _fm_value(ctrl, "fsrs_last_review") == TS1, f"对照段的恢复结果没落盘\n{out0}\n{err0}"
    assert "quiz:板Z#q9" in (ctrl / NODE_REL).read_text(encoding="utf-8"), "对照段没写下被恢复事件的校准条目"
    # 该路径**按设计**非零收尾: 恢复先落定, 本次评分要求重跑续写。
    assert rc0 != 0 and "恢复已落定, 本次评分未写入" in err0, f"对照段的收尾语义变了: rc={rc0}\n{err0}"
    assert _validate(ctrl).returncode == 0, "对照段写出的账本未通过校验器"

    # ── 注入竞态: 外部写者在 bridge 调用时刻改节点 ──
    race = _make_vault(tmp_path / "race")
    _seed_review_row(race, "quiz:板Z#q9", "检验白板/板Z#q9.md")
    _, race_env = _install_racing_bridge(race)
    node = race / NODE_REL
    rc, out, err = _run_writer(race, _payload("板A#q1"), "fgn-race", race_env)
    text = node.read_text(encoding="utf-8")
    # ⛔ 先立前提, 再判后果 (独立复核 R1-02): 注入若根本没跑成, 最终正文里同样没有
    # RACE_MARK —— 「前提不成立」会伪装成「编辑被恢复发布覆盖」。凭据取一个与节点
    # 正文无关的独立信号。
    assert _race_fired(race), f"竞态注入没有触发, 本门的前提不成立\nSTDOUT{out}\nSTDERR{err}"
    # ⛔ 状态不变量排在 rc 之前: 本路径**拆掉 CAS 后 rc 仍是非零**(恢复照样以「请重跑」
    # 收尾), 拿 rc 当判据会被那个非零码喂饱 —— 与门① 同一个教训。
    assert RACE_MARK.strip() in text, "CAS 门没挡住 A2 foreign 恢复发布: 外部写者那段正文被整份覆盖吃掉了"
    assert "fsrs_last_review:" not in text, "CAS 冲突后仍把 foreign 恢复结果发布到了节点 (非零写)"
    assert rc != 0, f"CAS 冲突后仍以成功码收尾\nSTDOUT{out}\nSTDERR{err}"
    assert "冲突点: A2 foreign 重放后的恢复发布" in err, f"拒因不是这一个发布点的 CAS: {err[-600:]}"
    assert not list((race / "节点").glob("*.quiz-tmp")), "拒绝发布后留下了 .quiz-tmp 残留"


def test_dup_recovery_publish_respects_cas(tmp_path):
    """dup 恢复路径 (本次事件已入账、崩在发布前) 的发布也必须先过 CAS。

    与 foreign 段同形的双段结构; 这条路径**成功时 rc=0**, 所以 rc 在这里是有判别力
    的判据 —— 但状态不变量仍排在它前面 (先问「用户的正文还在吗」)。
    """
    # ── 对照: 不注入竞态 ──
    ctrl = _make_vault(tmp_path / "ctrl")
    _seed_review_row(ctrl, "quiz:板A#q1", "检验白板/板A#q1.md")
    rc0, out0, err0 = _run_writer(ctrl, _payload("板A#q1"), "dup-ctrl")
    assert rc0 == 0, f"对照段未收敛: rc={rc0}\nSTDOUT{out0}\nSTDERR{err0}"
    assert "A2 恢复(崩溃窗口①)" in out0, f"对照段没走到 dup 恢复路径, 本门是空的\n{out0}"
    assert _fm_value(ctrl, "fsrs_last_review") == TS1, f"对照段的恢复结果没落盘\n{out0}"
    assert len(_ledger_rows(ctrl)) == 1, "恢复路径不得再追加一行 (event_id 幂等)"
    assert _validate(ctrl).returncode == 0, "对照段写出的账本未通过校验器"

    # ── 注入竞态 ──
    race = _make_vault(tmp_path / "race")
    _seed_review_row(race, "quiz:板A#q1", "检验白板/板A#q1.md")
    _, race_env = _install_racing_bridge(race)
    node = race / NODE_REL
    rc, out, err = _run_writer(race, _payload("板A#q1"), "dup-race", race_env)
    text = node.read_text(encoding="utf-8")
    assert _race_fired(race), f"竞态注入没有触发, 本门的前提不成立\nSTDOUT{out}\nSTDERR{err}"
    assert RACE_MARK.strip() in text, "CAS 门没挡住 dup 恢复路径发布: 外部写者那段正文被整份覆盖吃掉了"
    assert "fsrs_last_review:" not in text, "CAS 冲突后仍把 dup 恢复结果发布到了节点 (非零写)"
    assert rc != 0, f"CAS 冲突后仍以成功码收尾\nSTDOUT{out}\nSTDERR{err}"
    assert "冲突点: dup 恢复路径发布" in err, f"拒因不是这一个发布点的 CAS: {err[-600:]}"
    assert not list((race / "节点").glob("*.quiz-tmp")), "拒绝发布后留下了 .quiz-tmp 残留"
