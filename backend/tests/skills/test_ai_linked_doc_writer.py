"""CARD-AILINKED-4TH-WRITER: ai-linked-doc 写点的四条写规门 (先红后绿)。

账本 `learning_events.jsonl` 的真实写者有**四方** (backend 的
`app.services.learning_event_log.append_event`、quiz-answer SKILL、
start-exam-board SKILL、ai-linked-doc SKILL)。前三方已按同一套写规硬化,
第四方 (ai-linked-doc) 长期是一行式 `python3 -c` 裸追加 —— 四缺陷:

  ① **子串查重** `json.dumps(evid) in line` —— 历史行里任意**非 event_id**
     字段的值恰好等于新 evid 时, 带引号的 JSON token 在该行里命中 ⇒ 新事件被
     误判 duplicate ⇒ **零次落账 (永久丢失一条真实事实)**;
  ② **无跨进程锁** —— 同 evid 并发时「查重 → 写」被撕开, 两个写者各写一条同 id
     的行; 而校验器对重复 id 判**整个账本**不合规 ⇒ 那个 vault 此后所有评分都
     进不来;
  ③ **无 LF 守卫** —— 尾行被截断 (无换行) 时新事件直接粘上去, 两个 JSON 粘成
     一行坏行, 连坐损坏前一条;
  ④ **无形态门** —— 不校 event_id 的码点/首尾空白/长度, 写得进但校验器读侧
     fail-closed ⇒ 「写得进、读不回」。

本文件的四个门逐条钉住这四条写规的**行为**。

⛔ 分工声明 (防被读成放水): 写点的**外形**(必须是 `python3 - <<'PYEOF'` 块)
由 `tests/regression/test_learning_events_schema_contract.py::
test_real_producer_ai_linked_doc_writer` 的提取锚 + `assert len(matches) == 1`
钉住, **不**由本文件钉。本文件的 `_extract_writer` **故意**兼容新旧两种外形 ——
否则「改 SKILL.md 之前先跑一遍看它红」这件事根本做不到: 那一刻写点还是单行
`python3 -c` 形态, 只认 PYEOF 的提取器会让四门红在**夹具**而不是写规, 先红
就成了走过场 (红点必须落在指定断言上, 这是本卡的硬判据)。

⛔ 本文件全程 `tmp_path` 派生, 不碰 live vault, 不连任何库。
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
SKILL_MD = WT / "canvas-vault" / ".claude" / "skills" / "ai-linked-doc" / "SKILL.md"

#: 写点模板自身声明的两处 `<>` 占位 —— 逐字替换, 其余字节原样执行。
PLACEHOLDER_VAULT = "<vault绝对路径>"
PLACEHOLDER_NODE = "<新节点名>"

#: 门② 外部持锁方的持锁时长。远小于写点侧的取锁超时 (30s, 与另三个写者同口径),
#: 所以本门**不触发**超时路径 —— 超时行为不在本卡承诺范围 (见验收单)。
HOLD_S = 4.0


#: 门② 的持锁驱动 —— 形态照抄 `tests/regression/test_g3_3_cas.py::_LEDGER_HOLD_DRIVER`:
#: 取账本的排他记录锁 → 打印 `held` (给测试侧一个确定的起跑信号) → 持锁 `hold` 秒 →
#: **释放前**把账本大小写进 out 文件 → close。
#: `out` 是**另一个文件**, 写它不会碰 `ev` 上的记录锁 (记录锁按「进程 × 文件」释放)。
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

#: 门② 的**起跑屏障** —— 把写点源码先读好、先 compile 好, 报 ready 后空转等 gate,
#: gate 一出现就 `exec`。写点源码**逐字不变** (从 SKILL.md 提取 + 只替两处 `<>` 占位),
#: 屏障只同步**执行时机**, 不碰它的任何一个字节。
#:
#: ⛔ 为什么非要屏障, 且必须是 **busy-spin** 屏障 (2026-09-16 本卡实测三档,
#: 卡文口径更正④ 的「两进程同屏障」一词就是这个意思):
#:   无屏障            → 改前 0/3 复现 (两个 `Popen` 的解释器启动差约 30ms,
#:                       第二个写者读到的已是第一个写完的账本, 子串写法照样命中);
#:   屏障 + sleep 轮询 → 改前 3/5 复现, 仍 flaky (macOS 上 `time.sleep(0.001)`
#:                       实测抖动 1~2ms, 与写点自身「读 → 写」的窗口同量级);
#:   屏障 + busy-spin  → 稳定复现 (`os.path.exists` 是 stat syscall, 约 2μs,
#:                       抖动比写点窗口低两个数量级)。
#: 写点的「读 → 写」之间天然有一段 `from datetime import ...` 的首次 import
#: (约 1ms) —— 屏障抖动只要远小于它, 两个写者的查重就必然都发生在任一写之前。
#: ⚠️ busy-spin 会吃满两个核几十毫秒, 这是刻意的代价; 带 60s 上限防夹具挂死。
_WRITER_BARRIER = """
import os, sys, time
gate, ready, path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as f:
    src = f.read()
obj = compile(src, "<ai-linked-doc-writer>", "exec")   # 预编译: gate 之后只剩执行
open(ready, "w").close()
_t0 = time.time()
while not os.path.exists(gate):
    if time.time() - _t0 > 60:
        raise SystemExit("barrier timeout")
exec(obj, {"__name__": "__main__"})
"""


def _spawn_barriered_writers(tmp_path: Path, code: str, n: int = 2) -> list[subprocess.Popen]:
    """起 n 个**同屏障**的写点进程, 全部就绪后同时放行。"""
    src = tmp_path / "writer-src.py"
    src.write_text(code, encoding="utf-8")
    gate = tmp_path / "gate"
    readies = [tmp_path / f"ready-{i}" for i in range(n)]
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", _WRITER_BARRIER, str(gate), str(readies[i]), str(src)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(n)
    ]
    deadline = time.monotonic() + 30.0
    while not all(r.exists() for r in readies):
        assert time.monotonic() < deadline, "写者未在 30s 内全部就绪 —— 夹具问题, 不是写规问题"
        time.sleep(0.005)
    gate.write_text("go", encoding="utf-8")
    return procs


def _extract_writer() -> str:
    """从 SKILL.md **逐字提取**第四写者的代码模板 (不重写、不改写)。

    两种外形都认 (理由见模块 docstring 的「分工声明」):
      新 (本卡落地): ```bash 块里的 `python3 - <<'PYEOF' … PYEOF`, 用
                    `'node_derived'` 标记过滤 (与 producer 门同款过滤法);
      旧 (本卡改前): markdown 行内代码跨度 `` `python3 -c "<code>"` ``。
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    blocks = re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", text, re.DOTALL)
    matches = [b for b in blocks if "'node_derived'" in b]
    if matches:
        assert len(matches) == 1, f"ai-linked-doc SKILL.md 应恰有 1 个 node_derived 写点 PYEOF 块, 实见 {len(matches)}"
        return matches[0]
    m = re.search(r'python3 -c "(.+?)"`', text, re.DOTALL)
    assert m, "ai-linked-doc SKILL.md 找不到第四写者写点模板 (PYEOF 块与 python3 -c 单行都没匹配到)"
    return m.group(1)


def _render(vault: Path, node_name: str) -> str:
    """把逐字提取的模板里两处 `<>` 占位替换成本次运行的实参。"""
    return _extract_writer().replace(PLACEHOLDER_VAULT, str(vault)).replace(PLACEHOLDER_NODE, node_name)


def _run_writer(vault: Path, node_name: str, timeout: float = 30.0) -> subprocess.CompletedProcess:
    """跑一次第四写者 (独立进程, 与真实 Skill 的 `Bash` 调用同款)。"""
    return subprocess.run(
        [sys.executable, "-c", _render(vault, node_name)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _ledger_lines(path: Path) -> list[str]:
    """账本的**非空物理行** —— 按物理 LF 切, 不解析。

    ⛔ 不用 `str.splitlines()` (与 services `_iter_lines` / start-exam-board 写点
    同口径): splitlines 额外在 `\\v \\f \\x1c \\x1d \\x1e \\x85 \\u2028 \\u2029`
    上切行, 而这些字符**可以合法出现**在账本某行的字符串值里。
    ⚠️ 这不是洁癖, 是本文件自身的**假绿防线**: 门④(ii) 恰好喂一个 U+2028 ——
    改前无形态门, 那条 event_id 含裸 U+2028 的记录**会落账**且是一条完整合法的
    JSON 行; 若这里按 splitlines 切, 它会被切成两个碎片、两半都解析失败 ⇒
    「账本不含该 evid」这条断言**反而通过** ⇒ 门④(ii) 在改前变成绿的, 先红作废。
    """
    if not path.exists():
        return []
    raw = path.read_bytes()
    parts = raw.split(b"\n")
    if raw.endswith(b"\n"):
        parts = parts[:-1]  # 末尾 LF 之后的空串不是一行
    out = []
    for b in parts:
        if not b.strip():
            continue
        try:
            out.append(b.decode("utf-8"))
        except UnicodeDecodeError:
            continue  # 无法解码的坏行 —— 与写点同口径地跳过, 不算 duplicate 证据
    return out


def _ledger_records(path: Path) -> list[dict]:
    """账本里能解析成 dict 的记录 (坏行跳过 —— 坏行的存在由门③ 单独判)。"""
    out = []
    for line in _ledger_lines(path):
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _count_event_id(path: Path, evid: str) -> int:
    """账本里 `event_id` 字段**逐条 parsed 相等**于 evid 的条数。

    ⛔ 判据只能是 parsed-field 相等: 行数会被「一行里粘了两条」蒙混, 子串计数会被
    「别的字段恰好含这个值」蒙混 —— 而这两件事正是本卡要修的缺陷本身。
    """
    return sum(1 for r in _ledger_records(path) if r.get("event_id") == evid)


def _write_line(path: Path, obj: dict, *, trailing_lf: bool = True) -> None:
    """预置一条历史事件 (可选不带尾随 LF —— 模拟被截断的尾行)。"""
    path.write_text(json.dumps(obj, ensure_ascii=False) + ("\n" if trailing_lf else ""), encoding="utf-8")


def _event(event_id: str, node_id: str) -> dict:
    return {
        "event_id": event_id,
        "event_version": 1,
        "event_type": "node_derived",
        "node_id": node_id,
        "recorded_at": "2026-08-01T10:00:00+00:00",
        "effective_at": "2026-08-01T10:00:00+00:00",
        "payload": {},
    }


# ── 门① 子串查重误判 ⇒ 事件永久丢失 ────────────────────────────────


def test_substring_dedup_false_positive_loses_event(tmp_path):
    """历史行里**非 event_id** 字段的值恰等于新 evid 时, 新事件必须照常落账。

    这是子串查重的真实触发方向 (不是 finding 字面写的「derive:A ⊂ derive:AB」——
    `json.dumps` 两端带引号, 那条按字面不复现)。这里预置的历史行 event_id 是
    `exam:X`, 但它的 `node_id` 值恰好是 `derive:测试节点`; 子串写法把带引号的
    `"derive:测试节点"` 在该行里一命中就判 duplicate ⇒ 新事件**零次落账**。
    """
    ledger = tmp_path / "learning_events.jsonl"
    evid = "derive:测试节点"
    _write_line(ledger, _event("exam:X", evid))  # node_id 值 == 目标 evid

    proc = _run_writer(tmp_path, "测试节点")
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    assert _count_event_id(ledger, evid) == 1, (
        f"子串误判 duplicate 永久丢失: 历史行的 node_id 值恰等于 {evid!r}, "
        f"新事件被当成重复而零次落账 (实见 {_count_event_id(ledger, evid)} 条 event_id=={evid!r})"
    )


def test_undecodable_line_is_not_dedup_evidence(tmp_path):
    """历史行**无法按 UTF-8 解码**时, 它不构成 duplicate 证据 —— 新事件照常落账。

    ⛔ 这是「坏行吃掉真实事件」的第二条路径 (独立复核 round-2 实测指出):
    若查重前对整本做 `decode('utf-8', 'replace')`, 非法字节会被换成 U+FFFD,
    于是一条**本来无法解码**的历史行摇身变成「有效 JSON」; 它的 event_id 若恰好
    等于本次 evid, 新事件就被判 duplicate 而**零次落账** —— 与子串查重同一个后果。
    ⛔ 反方向也不能走: 整本严格解码会让一条坏行**中止整次追加**, 那更坏。
    正解是按物理 LF 切 bytes、逐行严格解码, 解不开的那一行跳过。
    """
    ledger = tmp_path / "learning_events.jsonl"
    evid = "derive:测试节点"
    # 这条历史行的 event_id 恰是目标 evid, 但 payload 里塞了一个非法 UTF-8 字节
    bad = json.dumps(_event(evid, "别的节点"), ensure_ascii=False).encode("utf-8")
    assert bad.count(b'"payload": {}') == 1
    bad = bad.replace(b'"payload": {}', b'"payload": {"note": "\xff"}')
    ledger.write_bytes(bad + b"\n")

    proc = _run_writer(tmp_path, "测试节点")
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    assert _count_event_id(ledger, evid) == 1, (
        f"无法解码的坏行被当成了 duplicate 证据: 历史行解不开 UTF-8, 不该证明 {evid!r} 已存在, "
        f"新事件却零次落账 (实见 {_count_event_id(ledger, evid)} 条)"
    )


# ── 门② 同 evid 并发 (外部持锁方在场) ⇒ 只能落一条 ─────────────────


def _run_concurrent_same_evid(tmp_path, backlog, use_holder, truncated_tail=False):
    """跑一趟「两个同 evid 写者同屏障并发」。返回 (n, size_at_release, elapsed, raw)。

    backlog         账本预置多少条**不含目标 evid** 的历史行 (0 = 空账本);
    use_holder      是否先起一个外部进程把账本锁攥住 HOLD_S 秒;
    truncated_tail  预置内容的最后一条**不带尾随 LF** (模拟截断的尾行) —— 让本趟
                    同时覆盖「两个写者各补一次 LF ⇒ 账本多出空行」那条并发面
                    (独立复核 LOW-1: 门③ 只有单写者, 那条 `"\n\n"` 判据此前
                    没有任何并发场景喂给它)。
    """
    vault = tmp_path / f"vault-{backlog}-{int(use_holder)}"
    vault.mkdir()
    ledger = vault / "learning_events.jsonl"
    if backlog:
        body = "".join(
            json.dumps(_event(f"exam:背景{i}", f"背景节点{i}"), ensure_ascii=False) + "\n" for i in range(backlog)
        )
        if truncated_tail:
            body = body[:-1]  # 砍掉最后一个 LF
        ledger.write_text(body, encoding="utf-8")
    else:
        ledger.write_text("", encoding="utf-8")

    size_file = vault / "size-at-release.txt"
    holder = None
    if use_holder:
        holder = subprocess.Popen(
            [sys.executable, "-c", _LEDGER_HOLD_DRIVER, str(ledger), str(size_file), str(HOLD_S)],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held", "持锁驱动没报 held —— 夹具问题, 不是写规问题"
        t_held = time.monotonic()  # 持锁方**开始持锁**的时刻
    try:
        writers = _spawn_barriered_writers(vault, _render(vault, "测试节点"), n=2)
        t0 = time.monotonic()
        # ⛔ 夹具健康断言 (独立复核 MEDIUM-2): HOLD_S 从 t_held 就开始走, 而 elapsed
        # 从 t0 起算 —— 两者之间的「起写者 + 等就绪」若耗掉太多, 持锁期的剩余时间会
        # 不足 HOLD_S*0.6, 于是**正确实现**也会被 ③ 判红 (假红)。这里把准备耗时钉在
        # HOLD_S 的 1/4 以内 (剩余 >= 0.75*HOLD_S > 0.6*HOLD_S), 并在超出时明确报
        # 「夹具问题」而不是混进写规判据里。实测准备耗时约 0.03s, 余量约 30 倍。
        if use_holder:
            prep = t0 - t_held
            assert prep < HOLD_S * 0.25, (
                f"写者准备耗时 {prep:.2f}s 过长 (上限 {HOLD_S * 0.25:.2f}s) —— 夹具问题, 判据不可比"
            )
        # timeout 远大于 HOLD_S: 改后两个写者都要等满持锁期, 不能被误判成超时。
        outs = [w.communicate(timeout=120) for w in writers]
        elapsed = time.monotonic() - t0
    finally:
        if holder is not None:
            holder.wait(timeout=60)

    for i, w in enumerate(writers):
        assert w.returncode == 0, f"写者{i} rc={w.returncode}\n{outs[i][0]}\n{outs[i][1]}"

    n = _count_event_id(ledger, "derive:测试节点")
    size = size_file.read_text(encoding="utf-8").strip() if use_holder else None
    return n, size, elapsed, ledger.read_text(encoding="utf-8")


#: 门② 档 B 预置的历史行数 —— 见门② docstring 的「为什么要两档」。
#: 实测: 20000 行 ≈ 3.9MB, 写点侧「读 + 逐行 json.loads」约 36ms, 而写点取锁的
#: 轮询间隔是 20ms —— 解析耗时必须**大于**轮询间隔, 富余才够钉住 fd 生命周期。
_BACKLOG_B = 20000


def test_concurrent_same_evid_under_held_lock_writes_once(tmp_path):
    """两个**同 evid** 的写者并发时, 账本最终只能有一条; 有人持锁时必须等。

    ⛔ 为什么是「同 evid 双写」而不是「不同 evid 双写」: 写点用 `O_APPEND`, 内核对
    **不同内容**的并发追加本就保证两条都落盘、不需要任何锁 —— 「断言两行都在」那种
    形态在改前**恒绿**, 是假门。锁的真实作用是让「查重 → 写」不被撕开。

    ⛔ 四条断言缺一不可:
      ① 恰 1 条 —— 证「查重 → 写」真的没被撕开;
      ② 持锁方释放前账本大小仍是 0 —— 证没在别人持锁时抢写;
      ③ 总耗时 >= 持锁时长的大部分 —— 证它是**等**出来的, 不是碰巧慢;
      ④ 账本无空行 —— 证两个写者没有对同一条无 LF 尾行**各补一次** LF
        (这条面此前没有任何并发场景喂给它, 独立复核 LOW-1 指出后由档 B 覆盖)。
    ②③ 只看得见「取锁那一刻」, 看不见 **fd 生命周期**: 锁内若用第二个 `open(ev)`
    读, POSIX 记录锁按「进程 × 文件」被隐式释放, 此时 ②③ 仍**全绿**而 ① 红。
    反过来只有 ① 会被「写点本来就慢 / 根本没跑」蒙混。

    ⛔ 为什么要**两档账本** (2026-09-16 本卡负控实测倒逼, 这是本门最容易被做假的地方):
      档 A 空账本 + 外部 holder —— 服务 ②③ 两条, 并在**改前**(写点还是 `python3 -c`
        单行) 让 ① 也红: 改前的「读 → 写」之间隔着一段 `from datetime import ...`
        的首次 import (约 1ms), 屏障抖动远小于它, 两个写者的查重必然都发生在任一写之前。
      档 B 大账本 + 不用 holder —— 专钉 **fd 生命周期**。改后的写点把 import 全提到
        了开头, 「读 → 写」窗口缩到几十微秒; 拿空账本跑, 就算把锁整个去掉、或者锁内
        二次 open 把锁悄悄丢掉, 两个写者也**撞不上**, ① 照样绿 —— 负控实测: 去掉
        `fcntl.lockf` 只红 2/3, 锁内换二次 open **全绿**(本该红 ① 的那一段什么都没证到)。
        档 B 把账本撑到解析耗时 (约 36ms) **大于**写点取锁的轮询间隔 (20ms): 一旦锁
        失效, 后到的写者会在前者写盘之前拿到锁并 `os.read` 出**旧快照**, ① 必红。
      ⇒ ① 取两档的较劣者。少了档 B, 这条断言对「锁失效」根本不敏感 = 假门。

    ⛔ 四条**全部求值**后才一次性 fail, 不用短路 assert: 短路会让「各条红不红」
    这件事无法从一次运行里读出来 —— 而本门的价值恰恰在于**哪几条红**
    (只红 ① = 锁内二次 open 丢了锁; ①②③ 全红 = 根本没锁)。
    """
    n_a, size_at_release, elapsed, _ = _run_concurrent_same_evid(tmp_path, backlog=0, use_holder=True)
    # 档 B 的预置尾行**无 LF** —— 顺带把「两个写者各补一次 LF」那条并发面喂给 ④。
    n_b, _, _, raw_b = _run_concurrent_same_evid(tmp_path, backlog=_BACKLOG_B, use_holder=False, truncated_tail=True)

    problems = []
    if n_a != 1 or n_b != 1:
        bad = "档 A(空账本+持锁方)" if n_a != 1 else "档 B(大账本)"
        problems.append(
            f"① 同 evid 并发重复落账: {bad} 里两个写者各写了一条 event_id=='derive:测试节点' "
            f"(档 A {n_a} 条 / 档 B {n_b} 条) —— 「查重 → 写」被撕开, 校验器对重复 id 判整个账本不合规"
        )
    if size_at_release != "0":
        problems.append(f"② 写点在别人持锁时抢写了账本 —— 持锁方释放前账本已经变大 (size-at-release={size_at_release})")
    if elapsed < HOLD_S * 0.6:
        problems.append(f"③ 写点没有真的等锁: 两个写者总共只用了 {elapsed:.2f}s (持锁 {HOLD_S}s)")
    if "\n\n" in raw_b:
        problems.append("④ 账本出现空行 (两个写者对同一条无 LF 尾行各补了一次 LF) —— 空行在校验器侧判整本不合规")
    if problems:
        pytest.fail(
            f"门② 四条互补判据 —— 本次红 {len(problems)}/4 "
            f"(档A n={n_a}, 档B n={n_b}, size-at-release={size_at_release}, elapsed={elapsed:.2f}s):\n"
            + "\n".join(problems)
        )


def test_serial_same_evid_stays_idempotent(tmp_path):
    """伴随回归 (**非承重**, 改前也绿): 同 evid 串行连跑两次仍恰 1 条。

    happy-path 幂等在改前就成立 (子串写法碰巧也能命中自己写的那条), 所以它
    **不能**充当先红依据; 留着只防改后回归。
    """
    ledger = tmp_path / "learning_events.jsonl"
    evid = "derive:测试节点"
    for _ in range(2):
        proc = _run_writer(tmp_path, "测试节点")
        assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert _count_event_id(ledger, evid) == 1, f"串行二跑应幂等, 实见 {_count_event_id(ledger, evid)} 条"


# ── 门③ 尾行被截断 (无 LF) ⇒ 必须先补 LF 再追加 ────────────────────


def test_lf_guard_isolates_truncated_tail(tmp_path):
    """账本尾行无换行 (截断) 时, 新事件不得粘上去 —— 先补 LF 隔离。

    承重判据 = **恰 2 条非空行, 且每条都能 `json.loads`**。改前两条子断言同时红:
    `{...}{...}` 粘成一行 ⇒ 只有 1 条非空行, 且那条解析失败 (连坐损坏前一条)。
    """
    ledger = tmp_path / "learning_events.jsonl"
    _write_line(ledger, _event("exam:Y", "别的节点"), trailing_lf=False)  # 截断的尾行

    proc = _run_writer(tmp_path, "测试节点")
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    lines = _ledger_lines(ledger)
    assert len(lines) == 2, (
        f"尾行无 LF 时新事件粘连成坏行: 账本应有 2 条非空行, 实见 {len(lines)} 条 (首条前 80 字符: {lines[0][:80]!r})"
    )
    for i, line in enumerate(lines):
        try:
            json.loads(line)
        except ValueError as e:
            pytest.fail(
                f"尾行无 LF 时新事件粘连成坏行: 第 {i + 1} 行无法 json.loads ({e}); 行首 80 字符: {line[:80]!r}"
            )

    # 非承重伴随判据 (改前也绿, 不作先红依据)。⚠️ 本门只有**一个**写者, 所以这条
    # 在这里测不到「两个写者各补一次 LF」那条并发面 (独立复核 LOW-1 指出) ——
    # 那条面由门② 的档 B 覆盖 (预置尾行无 LF + 两个写者同屏障并发)。留在这里只
    # 作单写者形态的廉价回归。
    assert "\n\n" not in ledger.read_text(encoding="utf-8"), "账本出现空行 (单写者补了多于一次 LF)"


# ── 门④ event_id 形态门 ⇒ 非法形态拒写 (且不阻断派生) ──────────────

#: ⛔ 反例集只列**可达**的三类。evid 恒由模板拼 `derive:<新节点名>`, 前缀非空且
#: 非空白 ⇒ 「空 evid」(`derive:`) 与「前导空格」(`derive: 名字`) 对
#: `_event_id_shape_problems` 实测**均返回合规、不拒写**, 写进门里就是恒不红的
#: 假子用例。若将来写点改成拿裸节点名当 evid, 这两类会重新可达 (已登记)。
_MALFORMED = [
    # (子用例 id, 节点名, 形态类别)
    ("trailing_space", "测试节点 ", "尾随空白"),
    # ⛔ 源码里用 \u2028 转义写, 不敲裸码点。U+2028 属 services
    # `_EVENT_ID_FORBIDDEN_RANGES` 与校验器 `FORBIDDEN_CODEPOINT_RANGES` 的**共有**集。
    ("u2028", "测试\u2028节点", "U+2028"),
    ("too_long", "长" * 600, "超长"),
]


@pytest.mark.parametrize("case_id,node_name,shape", _MALFORMED, ids=[c[0] for c in _MALFORMED])
def test_shape_gate_rejects_malformed_event_id(tmp_path, case_id, node_name, shape):
    """非法形态的 event_id 必须**拒写**, 且拒写不阻断派生 (rc 仍 0)。

    形态门的码点集不得比校验器窄 —— 窄了就留下「写得进、读不回」: 一条含
    U+2028 的 event_id 能被写进账本, 而校验器读侧对该码点 fail-closed, 判的是
    **整个账本**不合规 ⇒ 那个 vault 从此所有评分都进不来。

    同门内另有一条合法 evid 的验伪锚 (`test_shape_gate_allows_legal_event_id`) ——
    防「把所有写都拒了」也算绿。
    """
    ledger = tmp_path / "learning_events.jsonl"
    evid = "derive:" + node_name

    proc = _run_writer(tmp_path, node_name)
    assert proc.returncode == 0, f"形态门拒写不得阻断派生: rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    n = _count_event_id(ledger, evid)
    assert n == 0, (
        f"非法 evid 落账（{shape}）: event_id={evid[:60]!r}… (长度 {len(evid)}) 被写进账本 {n} 条 —— "
        "校验器读侧对该形态 fail-closed, 判整个账本不合规"
    )


def test_shape_gate_allows_legal_event_id(tmp_path):
    """验伪锚: 形态合规的 evid 必须照常落账 (证明门④ 不是「把所有写都拒了」)。"""
    ledger = tmp_path / "learning_events.jsonl"
    evid = "derive:测试节点"
    proc = _run_writer(tmp_path, "测试节点")
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert _count_event_id(ledger, evid) == 1, "合法 evid 未落账 —— 形态门把正常写也拒了"
