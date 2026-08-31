#!/usr/bin/env python3
# CARD-OBS-nothrow-logging (BATCH-2026-09-01-第八批) — 负控（变异）门
"""证明 (c) 的回归锁**真的能红** —— 对着三个变异逐一注入, 指定的那道门必须
变红, 且失败原因必须是预期的那种红。

⚠️ 必须串行 (MEMORY `reference_mutation_script_serial_only`): 本脚本原地改
被测文件, 并发跑会让后一个变异的还原把前一个的 mutation 写回, 而测试照样全绿。

变异表 (卡文 (d) 指定 3 个):
- M1 rag-nothrow-removed : rag.py 的模块级包装拆回裸 getLogger
  → 指定门: /weak-concepts 入口日志注入 (预期 200 变 500)
  → 原因必须含 "500" 或 "await_count" (卡文: 只核 nodeid 不核原因 = G4-3
    round-5 MEDIUM-1 的教训 —— nodeid 红可能是 fixture 崩了, 不是门在工作)
- M2 memory-nothrow-removed: memory.py 同型
  → 指定门: memory episodes 端点注入 (预期结构化 detail 变裸 Internal Server Error)
- M3 nothrow-except-deleted: NoThrowLogger._guarded 的 try/except 整体删除
  (变成透明转发, 一二级降级全灭)
  → 指定门: rag 入口 + rag 503 + memory episodes 三道全红

形态照抄 g41b_mutation_negative_controls.py: 配料 count!=1 硬校验 (防配方
漂移静默零命中)、tempdir 备份 + finally 逐字节还原 (filecmp shallow=False,
shallow 会放过大小的同形损坏)、return 不进 finally (SyntaxWarning 教训)、
baseline 必须全绿才开跑、skip 不算红、pytest 带 -rf + -p no:cacheprovider。

本脚本相对 g41b 的两点不同 (如实声明):
- 原因匹配 = 失败输出全文必须含预期关键字 —— g41b 只核 nodeid; 本卡卡文点名
  要核原因。
- 还原保证的是"回到**开跑时**的字节", 不是"回到 HEAD"。若开跑时工作树已有
  未提交改动, 还原会原样保留它们 (脚本会先打印三文件的 porcelain 状态让运行
  者看见)。进程被 SIGKILL 强杀时 try/finally 不执行 —— 这是本方案与生俱来
  的边界, 验收单如实登记。
"""

import filecmp
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
PYTEST = BACKEND / ".venv" / "bin" / "python"

RAG_EP = BACKEND / "app" / "api" / "v1" / "endpoints" / "rag.py"
MEM_EP = BACKEND / "app" / "api" / "v1" / "endpoints" / "memory.py"
CORE = BACKEND / "app" / "core" / "nothrow_logging.py"
TARGETS = (RAG_EP, MEM_EP, CORE)

TEST_FILE = "tests/api/v1/endpoints/test_nothrow_logging_api.py"

GATE_ENTRY_200 = f"{TEST_FILE}::TestWeakConceptsEntryLog::test_entry_log_failure_keeps_200_and_service_still_awaited"
GATE_ENTRY_503 = f"{TEST_FILE}::TestWeakConceptsEntryLog::test_error_log_failure_keeps_structured_503"
GATE_MEM_DETAIL = (
    f"{TEST_FILE}::TestMemoryMainEndpointErrorLogs::test_error_log_failure_keeps_structured_detail[episodes]"
)

# 配料必须与落地后的源码逐字一致 (含注释与空白); count != 1 即拒跑。
_RAG_WRAPPED_LINE = "logger = nothrow(logging.getLogger(__name__))"
_RAG_UNWRAPPED_LINE = "logger = logging.getLogger(__name__)"

_M3_OLD = """        try:
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + _STACKLEVEL_OFFSET
            getattr(self.inner, method)(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — 观测面刻意兜底, 见模块 docstring
            try:
                _FALLBACK_LOGGER.warning(
                    "nothrow: logger %r method %r raised during logging: %r",
                    getattr(self.inner, "name", "<unknown>"),
                    method,
                    exc,
                )
            except Exception:  # noqa: BLE001 — 兜底的兜底: 日志后端整体坏死
                pass
"""
_M3_NEW = """        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + _STACKLEVEL_OFFSET
        getattr(self.inner, method)(*args, **kwargs)
"""


@dataclass
class Mutation:
    name: str
    target: Path
    edits: list  # [(old, new), ...]
    expect_red_tests: list  # nodeid 整段匹配 (parametrize 尾巴也必须逐字一致)
    reason_keywords: list = field(default_factory=list)
    # 按门覆盖原因关键字 (Codex round-2 LOW-7): 共用关键字的门会被"状态码恰
    # 好相同"的无关失败背书 —— memory 门本来就期望 500, 必须用 content-type
    # 鉴别。缺省回落 reason_keywords。
    reason_by_gate: dict = field(default_factory=dict)
    desc: str = ""


MUTATIONS = [
    Mutation(
        name="M1-rag-nothrow-removed",
        target=RAG_EP,
        edits=[(_RAG_WRAPPED_LINE, _RAG_UNWRAPPED_LINE)],
        expect_red_tests=[GATE_ENTRY_200],
        reason_keywords=["500", "await_count"],
        desc="/weak-concepts 入口日志注入在包装拆掉后必须红 (200→500)",
    ),
    Mutation(
        name="M2-memory-nothrow-removed",
        target=MEM_EP,
        edits=[(_RAG_WRAPPED_LINE, _RAG_UNWRAPPED_LINE)],
        expect_red_tests=[GATE_MEM_DETAIL],
        reason_keywords=["500", "Internal Server Error"],
        desc="memory episodes 注入在包装拆掉后必须红 (结构化 detail→裸 500)",
    ),
    Mutation(
        name="M3-nothrow-except-deleted",
        target=CORE,
        edits=[(_M3_OLD, _M3_NEW)],
        expect_red_tests=[GATE_ENTRY_200, GATE_ENTRY_503, GATE_MEM_DETAIL],
        reason_keywords=["500"],
        reason_by_gate={GATE_MEM_DETAIL: ["Internal Server Error", "text/plain"]},
        desc="except 删除 (透明转发) 后三道门全红",
    ),
]


def _apply(text: str, edits) -> str:
    for old, new in edits:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"变异原料失配: 期望恰 1 处命中, 实得 {count}\n---\n{old[:240]}\n---\n"
                "(被测源码改过 ⇒ 请同步更新本脚本的变异原料, 否则负控是假的)"
            )
        text = text.replace(old, new)
    return text


def _run_pytest(selectors) -> tuple:
    cmd = [
        str(PYTEST),
        "-m",
        "pytest",
        *selectors,
        "-q",
        "--no-header",
        "-rf",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:randomly",
    ]
    proc = subprocess.run(cmd, cwd=str(BACKEND), capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _failed_tests(out: str) -> list:
    """从 -rf 短摘要取失败的 nodeid (只认 'FAILED ' 行)。

    ⚠️ 本仓 pytest 9.0.2 的摘要行是 `FAILED <nodeid>` (实测 2026-09-01, 无
    " - 原因" 段); 旧 pytest 是 `FAILED <nodeid> - <原因>`。两种格式都兼容:
    有 " - " 取前面, 没有取整行。g41b 原版要求 " - " 必在, 在 pytest 9 上
    会把每道门误判成"未红" (死门) —— 预验证 M2 抓出后修正。
    """
    failed = []
    for line in out.splitlines():
        if line.startswith("FAILED "):
            failed.append(line[len("FAILED ") :].split(" - ", 1)[0].strip())
    return failed


def _test_matches(spec: str, nodeid: str) -> bool:
    """整段匹配, 不用子串 —— 'test_foo' 不能被 'test_foo_bar' 满足 (g41b round-2)。"""
    tail = nodeid.rsplit("::", 1)[-1]
    spec_tail = spec.rsplit("::", 1)[-1]
    if "[" in spec_tail:
        return tail == spec_tail
    return tail.split("[", 1)[0] == spec_tail


def _summary(out: str) -> str:
    for line in out.splitlines():
        if line.startswith("=") and ("passed" in line or "failed" in line or "error" in line):
            return line.strip()
    return "(无摘要行)"


def main() -> int:
    if not PYTEST.exists():
        print(f"⛔ 找不到 pytest: {PYTEST}", file=sys.stderr)
        return 2

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *(str(t.relative_to(BACKEND.parent)) for t in TARGETS)],
        cwd=str(BACKEND.parent),
        capture_output=True,
        text=True,
    ).stdout
    if status.strip():
        print("⚠️ 开跑时目标文件已有未提交改动 (还原将保留这些改动, 不回 HEAD):")
        print(status)

    originals = {t: t.read_text() for t in TARGETS}

    with tempfile.TemporaryDirectory() as tmp:
        backups = {}
        for t in TARGETS:
            b = Path(tmp) / (t.name + ".orig")
            b.write_text(originals[t])
            backups[t] = b

        # ── baseline: 指定门在未变异时必须全绿 ────────────────────────────
        all_gates = sorted({nid for m in MUTATIONS for nid in m.expect_red_tests})
        code, out = _run_pytest(all_gates)
        print(f"[baseline] {_summary(out)}")
        if code != 0:
            print("⛔ 基线就不是全绿 — 先修好再跑负控", file=sys.stderr)
            return 2
        if " skipped" in out or "skipped," in out:
            print("⚠️ 有 skip — skip 不构成『能红』证据", file=sys.stderr)

        dead_gates = 0
        for m in MUTATIONS:
            print(f"\n=== {m.name}: {m.desc} ===")
            m.target.write_text(_apply(originals[m.target], m.edits))
            # 逐门单跑 + 逐门原因匹配 (Codex round-1 LOW-7): 多门合跑时对整份
            # 输出做一次 any(keyword) 的话, 第一门的关键字能替其余门的"别的
            # 原因失败"背书 —— 原因必须按门绑定。
            per_gate = []
            try:
                for nid in m.expect_red_tests:
                    code, out = _run_pytest([nid])
                    failed = _failed_tests(out)
                    red = code != 0 and " failed" in out and any(_test_matches(nid, x) for x in failed)
                    summary = _summary(out)
                    # 卡文口径: 失败原因含 "500" / "await_count" —— **任一**命中
                    # (M1 下 await_count 断言排在状态码断言之后, 前者红了后者
                    # 不会渲染; all 语义会把 M1 误判死门 —— 首跑实测)。
                    kws = m.reason_by_gate.get(nid, m.reason_keywords)
                    reasons_ok = any(kw in out for kw in kws)
                    per_gate.append((nid, red, reasons_ok, summary))
            finally:
                shutil.copyfile(backups[m.target], m.target)
                restored_ok = filecmp.cmp(backups[m.target], m.target, shallow=False)
            if not restored_ok:
                print("⛔ 还原后字节不一致 — 立即人工检查!", file=sys.stderr)
                return 3
            # return 不放进 finally (g41a 教训: 会吞掉正在传播的异常)

            bad = [nid for nid, red, rok, _s in per_gate if not (red and rok)]
            if bad:
                dead_gates += 1
                for nid, red, rok, summary in per_gate:
                    if not (red and rok):
                        why = "没有以『测试失败』的方式变红" if not red else "失败原因不是预期的"
                        print(f"⛔ 死门: {m.name} → {nid.rsplit('::', 1)[-1]} — {why}")
                        print(f"   实得: {summary}")
                continue
            print(f"✓ {m.name}: 指定门全红且原因逐门匹配 | {per_gate[0][3]}")

        print()
        if dead_gates:
            print(f"NEGATIVE-CONTROL: FAIL ({dead_gates} dead gates)", file=sys.stderr)
            return 1
        print(
            "NEGATIVE-CONTROL: PASS (3 mutants each killed by named gates "
            "with expected reason; restored byte-identical)"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
