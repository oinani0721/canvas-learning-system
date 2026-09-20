"""CARD-SEB-WRITER-SUBSTRING-TMP: start-exam-board Step 6.5 落账块的写规门 (先红后绿)。

账本 `learning_events.jsonl` 的真实写者有**四方** (backend 的
`app.services.learning_event_log.append_event`、quiz-answer SKILL、
ai-linked-doc SKILL、start-exam-board SKILL)。前三方的查重都已是
**parsed-field 等值** (`json.loads` 之后比 `event_id`), 只剩本块仍是子串 ——
两条缺陷, 两条都通向同一个后果「零次落账, 一条真实的考察事实永久丢失」:

  ① **子串查重** `json.dumps(evid, ensure_ascii=False) in ln` (改前 `:477`) ——
     历史行里任意**非 event_id** 字段的值 (`node_id` / `payload.exam_board` …)
     恰好等于新 evid 时, 带引号的 JSON token 在该行里命中 ⇒ 新事件被误判
     duplicate ⇒ **一次都没写**;
  ② **有损解码** `b"".join(_chunks).decode("utf-8", "replace")` (改前 `:473`) ——
     非法字节被换成 U+FFFD 之后, 一条**本来无法解码**的历史行摇身变成「有效
     JSON」; 它的 event_id 若恰等于本次 evid, 新事件同样零次落账。
     ⛔ 反方向也不能走: 整本严格解码会让一条坏行**中止整次追加**, 方向更坏。
     正解 = 切 **bytes**、逐行**严格**解码、解不开的那一行跳过。

门①② 钉这两条缺陷 (改前必红); 门③④⑤ 是**对照门** (改前改后都绿) ——
它们在场是为了证明修复没有把「真重复仍然只写一遍」「二跑幂等」「坏行不逸出为
整次失败」这三件本来成立的事一起改坏。

⛔ 分工声明 (防被读成放水): 写点的**外形** (必须是 `python3 - <<'PYEOF'` 块、
且恰有 1 个) 由 `tests/regression/test_learning_events_schema_contract.py::
test_real_producer_start_exam_board_writer` 与 `tests/regression/test_g3_3_cas.py`
的模块级提取锚钉住, **不**由本文件钉。本文件的 `_P_LITERAL_RE` **故意**同时认
新旧两种路径字面量 —— 否则「改 SKILL.md 之前先跑一遍看它红」这件事根本做不到:
那一刻 `P` 还是裸 `/tmp/exam-created-event.json`, 只认新字面量的夹具会让门①②
红在**夹具**而不是写规, 先红就成了走过场 (红点必须落在指定断言上)。

⛔ DD-03 禁 mock: 写点是从 SKILL.md **逐字提取**的真代码, 用 `subprocess` 真跑
(与真实 Skill 的 `Bash` 调用同款)。全程 `tmp_path` 派生, 不碰 live vault,
不连 7691/7687/7692 任何库。
"""

import json
import re
import subprocess
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
SKILL_MD = WT / "canvas-vault" / ".claude" / "skills" / "start-exam-board" / "SKILL.md"

#: 落账块的提取锚 —— 与两个 regression 门同款正则; 用 `"exam_created"` 过滤
#: 而**不是** `P` 字面量: 后者会随本卡的命名空间迁移而变, 拿它当锚 = 先红落在夹具。
_BLOCK_RE = re.compile(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", re.DOTALL)
_EXTRACT_MARK = '"exam_created"'

#: 输入文件路径的重定向锚 —— **新旧两种字面量都认** (见模块 docstring 分工声明)。
_P_LITERAL_RE = re.compile(r'P = "/tmp/(?:cls-exam/)?exam-created-event\.json"')

#: 本文件全程用同一组实参。`evid` 由写点自己从 `exam_board` 派生:
#: `"exam:" + splitext(basename("检验白板/测试节点-检验.md"))[0]` == `"exam:测试节点-检验"`。
#: ⛔ 不在这里手写 evid 的构造逻辑 —— 那等于把被测代码抄一遍; 五条门都只用这个常量,
#: 它与写点自己派生出来的值是否一致, 由门④ (空账本真跑后账本里恰有 1 条 `EVID`) 反证。
BOARD = "检验白板/测试节点-检验.md"
NODE = "测试节点"
EVID = "exam:测试节点-检验"
TS = "2026-09-18T10:00:00+00:00"


def _extract_writer() -> str:
    """从 SKILL.md **逐字提取**落账块 (不重写、不改写)。"""
    text = SKILL_MD.read_text(encoding="utf-8")
    blocks = _BLOCK_RE.findall(text)
    matches = [b for b in blocks if _EXTRACT_MARK in b]
    assert len(matches) == 1, (
        f"start-exam-board SKILL.md 应恰有 1 个落账块 ({_EXTRACT_MARK} 标记), 实见 {len(matches)} "
        f"—— 这是**夹具**问题, 不是写规问题"
    )
    return matches[0]


def _render(p_path: Path) -> str:
    """把逐字提取的写点里的输入文件路径重定向到 `tmp_path` 派生的那份。"""
    code, n = _P_LITERAL_RE.subn(f"P = {json.dumps(str(p_path))}", _extract_writer())
    assert n == 1, f"输入文件字面量应恰替换 1 处, 实见 {n} —— **夹具**问题, 不是写规问题"
    return code


def _write_input(p_path: Path, vault: Path) -> None:
    """预置 Step 6.5 的输入 JSON (真实链路里由宿主的 `Write` 工具落盘)。"""
    p_path.write_text(
        json.dumps(
            {"vault_root": str(vault), "exam_board": BOARD, "node": NODE, "ts": TS},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _run_writer(vault: Path, p_path: Path, timeout: float = 60.0) -> subprocess.CompletedProcess:
    """跑一次落账块 (独立进程, 与真实 Skill 的 `Bash` 调用同款)。"""
    return subprocess.run(
        [sys.executable, "-c", _render(p_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _ledger_records(path: Path) -> list[dict]:
    """账本里能解析成 dict 的记录。

    ⛔ 按**物理 LF** 切 bytes、逐行**严格**解码 —— 与写点改后同口径:
    用 `str.splitlines()` 会额外在 `\\v \\f \\x1c \\x1d \\x1e \\x85 \\u2028 \\u2029`
    上切, 那些字符可以合法出现在账本某行的字符串值里; 用 `decode(..., "replace")`
    会把坏行洗成「有效 JSON」—— 那正是门② 要抓的缺陷, 判据自己犯同一条就成了假绿。
    """
    if not path.exists():
        return []
    raw = path.read_bytes()
    parts = raw.split(b"\n")
    if raw.endswith(b"\n"):
        parts = parts[:-1]
    out: list[dict] = []
    for chunk in parts:
        if not chunk.strip():
            continue
        try:
            rec = json.loads(chunk.decode("utf-8"))
        except (ValueError, RecursionError):
            continue  # 坏行 —— 与写点同口径地跳过
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _count_event_id(path: Path, evid: str) -> int:
    """账本里 `event_id` 字段**逐条 parsed 相等**于 evid 的条数。

    ⛔ 判据只能是 parsed-field 相等: 行数会被「一行里粘了两条」蒙混, 子串计数会被
    「别的字段恰好含这个值」蒙混 —— 而这两件事正是本卡要修的缺陷本身。
    """
    return sum(1 for r in _ledger_records(path) if r.get("event_id") == evid)


def _history(event_id: str, node_id: str, **extra_payload) -> dict:
    """按写点自己写出的记录形态预置一条历史行。"""
    payload = {"exam_board": BOARD}
    payload.update(extra_payload)
    return {
        "event_id": event_id,
        "event_version": 1,
        "event_type": "exam_created",
        "node_id": node_id,
        "recorded_at": "2026-08-01T10:00:00+00:00",
        "effective_at": "2026-08-01T10:00:00+00:00",
        "payload": payload,
    }


def _setup(tmp_path: Path, name: str) -> tuple[Path, Path, Path]:
    """返回 `(vault, ledger, p_path)`, 三者全部 `tmp_path` 派生。"""
    vault = tmp_path / name
    vault.mkdir()
    return vault, vault / "learning_events.jsonl", tmp_path / f"{name}-input.json"


# ── 门① 子串查重误判 ⇒ 事件永久丢失 ────────────────────────────────


def test_substring_dedup_false_positive_loses_event(tmp_path):
    """历史行里**非 event_id** 字段的值恰等于新 evid 时, 新事件必须照常落账。

    这是子串查重的真实触发方向: `json.dumps` 两端带引号, 所以「evid 是某个更长
    字符串的前缀」按字面**不**复现; 真正复现的是「历史行的某个**别的**字段值
    **恰好整个等于** evid」—— 这里预置的历史行 event_id 是 `derive:别的`, 而它的
    `node_id` 值恰好是 `exam:测试节点-检验`, 于是带引号的 JSON token 在该行里命中,
    子串写法判 duplicate ⇒ 新事件**零次落账**。
    """
    vault, ledger, p_path = _setup(tmp_path, "vault-substring")
    ledger.write_text(
        json.dumps(_history("derive:别的", EVID), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _write_input(p_path, vault)

    proc = _run_writer(vault, p_path)
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    got = _count_event_id(ledger, EVID)
    assert got == 1, (
        f"子串查重把事件吃掉了: 历史行的 node_id 值恰等于 {EVID!r} (它的 event_id 是 "
        f"'derive:别的', 并不是重复), 新事件却被判 duplicate 而零次落账 —— "
        f"账本里 event_id=={EVID!r} 的记录实见 {got} 条, 期望 1 条"
    )


# ── 门② 无法解码的历史行不构成 duplicate 证据 ──────────────────────


def test_undecodable_line_is_not_dedup_evidence(tmp_path):
    """历史行**无法按 UTF-8 解码**时, 它不构成 duplicate 证据 —— 新事件照常落账。

    这是「坏行吃掉真实事件」的第二条路径, 与门① 的子串面**互相独立**:
    查重前对整本做 `decode("utf-8", "replace")` 会把非法字节换成 U+FFFD, 于是一条
    本来无法解码的历史行变成「有效 JSON」; 它的 event_id 恰等于本次 evid 时,
    新事件就被判 duplicate 而零次落账。负控段② 只把逐行严格解码改回 `"replace"`
    (不碰查重方式), 届时本门必红而门① 仍绿 —— 那证明两门测的是两条路径。
    """
    vault, ledger, p_path = _setup(tmp_path, "vault-undecodable")
    bad = json.dumps(_history(EVID, "别的节点", note="BADBYTE"), ensure_ascii=False).encode("utf-8")
    assert bad.count(b'"note": "BADBYTE"') == 1, "预置失败: 坏字节注入锚不唯一 —— 夹具问题"
    bad = bad.replace(b'"note": "BADBYTE"', b'"note": "\xff"')
    ledger.write_bytes(bad + b"\n")
    _write_input(p_path, vault)

    proc = _run_writer(vault, p_path)
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    got = _count_event_id(ledger, EVID)
    assert got == 1, (
        f"无法解码的坏行被当成了 duplicate 证据: 那条历史行解不开 UTF-8, 不该证明 "
        f"{EVID!r} 已经存在, 新事件却零次落账 —— 账本里可解码且 event_id=={EVID!r} 的"
        f"记录实见 {got} 条, 期望 1 条"
    )


# ── 门③ 对照: 真重复仍然只写一遍 ──────────────────────────────────


def test_true_duplicate_is_still_skipped(tmp_path):
    """历史行的 event_id **就是**本次 evid 且可解码时, 不得写第二遍。

    ⛔ 对照门: 它在改前改后都绿。缺了它, 「把查重整段删掉」这种改法也能让门①②
    变绿 —— 那不是修复, 是把查重拆了。校验器对重复 id 判**整个账本**不合规,
    真写两遍的代价是那个 vault 此后所有评分都进不来。
    """
    vault, ledger, p_path = _setup(tmp_path, "vault-duplicate")
    ledger.write_text(
        json.dumps(_history(EVID, NODE), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _write_input(p_path, vault)

    proc = _run_writer(vault, p_path)
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"

    got = _count_event_id(ledger, EVID)
    assert got == 1, (
        f"真重复被写了第二遍 (查重失效): 账本里 event_id=={EVID!r} 实见 {got} 条, 期望恰 1 条 "
        f"—— 重复 id 会让校验器判整个账本不合规"
    )


# ── 门④ 对照: 空账本二跑幂等 + 输入文件被清理 ──────────────────────


def test_empty_ledger_twice_writes_once_and_removes_input(tmp_path):
    """空账本上连跑两次: 账本恰 1 条, 且每次跑完输入文件都被 `os.remove`。

    ⛔ 对照门: 改前改后都绿。第二次必须**重新落一次输入文件** —— 写点结尾的
    `os.remove(P)` 是真实链路的一部分 (宿主每次建板都新写一份), 这里如实复现。
    它同时反证了 `EVID` 常量与写点自己从 `exam_board` 派生出来的值一致:
    第一跑之后账本里那条记录的 event_id 若不等于 `EVID`, 本断言就红。
    """
    vault, ledger, p_path = _setup(tmp_path, "vault-idempotent")

    for attempt in (1, 2):
        _write_input(p_path, vault)
        proc = _run_writer(vault, p_path)
        assert proc.returncode == 0, f"第{attempt}跑 rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
        assert not p_path.exists(), f"第{attempt}跑结束后输入文件未被 os.remove: {p_path}"

    got = _count_event_id(ledger, EVID)
    assert got == 1, f"二跑不幂等: 账本里 event_id=={EVID!r} 实见 {got} 条, 期望恰 1 条"


# ── 门⑤ 对照(纵深): 深嵌套坏行不逸出为整次失败 ────────────────────


def test_deeply_nested_bad_line_does_not_abort_append(tmp_path):
    """一条深层嵌套的坏行只能吃掉它自己那一行, 不能吃掉一次真实派生。

    ⛔ 对照门 (纵深): 改前改后都绿, 它钉的是 `except` 子句的**覆盖面**而不是
    先红面。改后的逐行解析里 `json.loads` 对上万层 `[` 在部分 Python 版本上抛的是
    `RecursionError` 而不是 `ValueError` (T7-B 独立复核实测 3.9.6 复现 / 3.14.4 不复现,
    本机 3.14.4 实测抛 `JSONDecodeError`) —— 它一旦逸出到外层 `except Exception`,
    整次事件就**不落账**了。所以两个异常都必须在逐行那层接住。
    ⚠️ 如实声明: 本机版本上本门走的是 `ValueError` 分支, `RecursionError` 分支
    未在本卡实跑覆盖 (验收单「本卡未证明什么」已登记)。
    """
    vault, ledger, p_path = _setup(tmp_path, "vault-deepnest")
    ledger.write_bytes(b"[" * 100000 + b"\n")
    _write_input(p_path, vault)

    proc = _run_writer(vault, p_path)
    assert proc.returncode == 0, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert "事件已落日志" in proc.stdout, (
        f"深嵌套坏行让整次追加失败了 (坏行的代价必须只限于它自己那一行): stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )

    got = _count_event_id(ledger, EVID)
    assert got == 1, f"深嵌套坏行在场时新事件没落账: event_id=={EVID!r} 实见 {got} 条, 期望 1 条"
