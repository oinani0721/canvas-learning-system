#!/usr/bin/env python3
"""CARD-G3-2c-B 变异负控：证明四道防线**承重**，而不只是"门是绿的"。

X7-A 只证明了 round-17 的门在这套代码上全绿；绿门 ≠ 有效门。本脚本对每道防线
做一次「拆掉它」的变异，看**指定的那道门**是否变红。

⛔ 本脚本的防呆设计，逐条都是踩过的坑（见 memory）：

1. **串行**：原地变异并发跑会互踩。全程单进程顺序执行，不并行。
2. **无条件还原**：`finally` 里不带任何「别覆盖第三方改动」的 exit 防护——
   exit 时不还原，变异体就留在生产文件里（`if False:  # MUTANT` 在 SKILL.md
   里活过整整一轮，两天后才被下一张卡的测试红抓出来）。
3. **信号也要还原**：`SIGTERM` 默认处置**不做栈展开**，`finally` 不会执行。
   装 handler 转成异常，让 `finally` 有机会跑。
4. **全文件 sha 基线，不靠 grep 标记**：变异体的替换文本**不一定含 "MUTANT"
   字样**（历史上就有一次不含），所以锚点是跑前对**每个会被变异的文件**记全
   文件 sha、跑完逐个复核，与变异体是否配合无关。
5. **KILLED 判据是 `rc == 1`，不是 `rc != 0`**：pytest 的 `4`=用法错、
   `5`=零收集、`2`=中断、`3`=内部错。门名一打错，`rc != 0` 会让整份报告全绿
   而毫无意义。
6. **判据比对失败身份，防假杀**：只看「有测试失败」会把「变异让别的门红了」
   当成击杀。必须是**指定的那条测试**失败才算 KILLED。

⚠️ **M9 = 退役变异 M154 的复活**（CARD-G3-2c-E）：X7-C 时 `M154-q-bare-ensure-ascii-false`
   被判假杀而退役，理由是「非规范码点在进入 `q_()` **之前**就被字符轴拒了 ⇒ 拆
   `q_()` 观察不到差异」，并留下自陈「`q_()` 的往返自证那一层若失效不会被任何门发现」。
   **当前**（CARD-CX-G3-2c-C-R1 把字符轴收窄到 5 个枚举字段之后）实测：
   `self_confidence_raw` 不在那 5 路径里，也不在落账 payload 的 11 键里 ⇒ 敌意值
   **能到达** `q_()`，载体可达。
   ⚠️ 措辞收窄（Codex round-1 #7）：「X7-C 当时不可达」是**那份验收单的记载**，
   「现在可达」是**本卡的实测**；两者合起来支持采用 M9，但不据此追认
   「恰恰是因为收窄才首次可达」这条因果——当前文件证不到历史。
   所以 M9 **不需要挂 depth 层**（卡文原本预判要挂）——不挂层就没有「击杀由层贡献」
   的假杀面，这比挂层严格更好。归因靠窄门
   `test_g32ce_q_ascii_escape_fallback_is_load_bearing`：拆**回落**（M9）落在它的
   `rc=0` 断言上；拆**往返自证**（`g32ccr1` 的 E4）落在它的「必须是转义形态」断言上，
   两种失效形态可分辨。

⚠️ **拆防线，不要改参数**（M4/M5 踩了两次才对）：
   门是**从实现读上限**再按它构造输入的（`_validator_limits()`）。于是
   ① 把上限改成 `10**9` ⇒ 门去构造十亿层嵌套，卡死（实测 300s 超时）；
   ② 把上限改成 4096 ⇒ 门读到 4096、构造 4097 层，**仍然超限仍然被拒**，
      变异对门完全不可见（实测 SURVIVED）。
   同源保证了门不会与实现漂移，代价就是**改参数等于同时改了门的期望**。
   正确的变异是拆掉**判据本身**（`if depth > MAX:` → `if False:`）：
   上限常量不动，门的构造不变，而检查不再执行。

⚠️ **锚点自检**（CARD-CX-G3-2c-C-R1）：M8 这类变异靠**硬编码源码字面量**匹配
   （连前导空格一起写死）。生产那行改个缩进、换个变量名，锚就静默失配。
   原先只在变异循环里逐条 `count(old) != 1` 判一次，要等 8 道门的绿态前提
   跑完（约 1 分钟）才报；现在提到**最前面**，锚一漂就非零退出、不跑任何变异。

用法：
  `python3 backend/scripts/g32cb_mutation_gates.py`          跑全部
  `python3 backend/scripts/g32cb_mutation_gates.py --list`   只列变异与锚点命中数（不改任何文件）
"""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
LEDGER_TEST = "tests/regression/test_g3_2_review_ledger.py"
#: `_pytest_bin()` 的一次性解析结果（身份自检要起子进程，不必每道门都跑一遍）
_PYTEST_CACHE: str | None = None


def _pytest_bin() -> str:
    """pytest 可执行文件路径：环境变量 → 本车道 venv → **明确报错**。

    ⛔ 原为**硬编码另一个车道**的 venv 绝对路径：那个车道一旦被清理，本脚本立刻
    报废；在没有自己 venv 的新车道上也跑不起来，而且报出来的是一个
    `FileNotFoundError`，看的人得自己去猜原因。
    ⚠️ 这里**故意不写出**那条旧路径的字面 —— 裁判用 `grep -c '<旧车道名>'` 判 0，
    把它抄进注释等于让判据被自己的说明文字打红（判据不能自指）。
    形态与 `g32b_mutation_gates.py::_PYTEST_BIN()` 一致 —— 同型缺口在 g32b 那边
    早就修过（`G32B_PYTEST`），g32cb 一直没跟上（CARD-G3-2c-E）。
    """
    global _PYTEST_CACHE
    if _PYTEST_CACHE is not None:
        return _PYTEST_CACHE

    env = os.environ.get("G32CB_PYTEST")
    if env:
        cand = Path(env).expanduser()
        # ⛔ **必须 resolve 成绝对路径**（Codex round-1 LOW 实测）：`_run_gate()` 用
        # `cwd=WT/backend` 起子进程，于是从工作树根设 `G32CB_PYTEST=backend/.venv/bin/pytest`
        # 这种**相对路径**在这里 `exists()` 为真、到了子进程却 `FileNotFoundError(2)`。
        cand = cand if cand.is_absolute() else (Path.cwd() / cand).resolve()
        _reject_if_unusable(cand, f"环境变量 G32CB_PYTEST={env!r}（解析为 {cand}）")
        _PYTEST_CACHE = str(cand)
        return _PYTEST_CACHE

    local = (WT / "backend" / ".venv" / "bin" / "pytest").resolve()
    if local.exists():
        _reject_if_unusable(local, f"本车道 venv {local}")
        _PYTEST_CACHE = str(local)
        return _PYTEST_CACHE

    raise SystemExit(
        f"✗✗ 找不到 pytest：环境变量 G32CB_PYTEST 未设，且本车道无 {local} "
        f"—— 请设 G32CB_PYTEST 指向可用的 pytest 后重跑"
    )


def _reject_if_unusable(path: Path, who: str) -> None:
    """确认 `path` 真的是一个**能跑的 pytest**，否则**当场**报清楚。

    ⛔ 为什么不能只判 `exists()`（Codex round-1 LOW，逐条实测）：
      · 指向仓库里的某个普通脚本 ⇒ 接受，然后子进程抛 `PermissionError(13)`；
      · 指向 `/usr/bin/true` 或 `/bin/echo` ⇒ 每道门都「rc=0」，绿态前提**全绿**，
        变异阶段则全部 SURVIVED ⇒ 报出来是 **0/9 KILLED**。脚本 rc=1 不算假绿，
        但它把「你配错了 pytest」说成「9 道防线全都不承重」——**诊断指错方向**，
        而这正是本族反复栽的那类坑；
      · 指向 `/usr/bin/false` ⇒ 绿态前提第一道就 rc=1，脚本 rc=2 报「前提不成立」，
        同样指错方向。
    所以这里做三件事：是不是文件、有没有执行权限、`--version` 认不认自己是 pytest。
    """
    if not path.is_file():
        raise SystemExit(f"✗✗ {who} 不是一个文件 —— 请指向 pytest 可执行文件本身")
    if not os.access(path, os.X_OK):
        raise SystemExit(f"✗✗ {who} 没有执行权限")
    try:
        probe = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=60)
    except OSError as exc:
        raise SystemExit(f"✗✗ {who} 起不起来：{type(exc).__name__}: {exc}") from exc
    blob = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0 or "pytest" not in blob.lower():
        raise SystemExit(
            f"✗✗ {who} 不是 pytest：`--version` 退出码 {probe.returncode}、输出 {blob.strip()[:120]!r}。"
            f"⚠️ 不在这里拦住的话，后面会报成「0/9 KILLED」或「绿态前提不成立」，"
            f"把配置错误伪装成防线失效"
        )


#: (id, 说明, 目标文件, 原文本, 变异文本, 必须变红的测试)
#: ⚠️ 「必须变红的测试」是**身份判据**：变异后必须是这一条失败，别的门红不算数。
MUTATIONS = [
    (
        "M1",
        "truthiness 回退：严格 bool 判定退回「只拒 None」(round-17 B① 的原形态)",
        SKILL,
        "    if _rc_dup is not None and type(_rc_dup_applied) is not bool:",
        "    if _rc_dup is not None and _rc_dup_applied is None:  # MUTANT M1",
        "test_round17_fsrs_applied_must_be_strict_bool",
    ),
    (
        "M2",
        "去掉 foreign 凭据提升：`fsrs_applied: false` 补了调度却不升 true",
        SKILL,
        "        if _fa_fg is False:\n            fm, _ok_fg = _promote_applied(fm, _rid_)",
        "        if False:  # MUTANT M2 去掉 foreign 提升\n            fm, _ok_fg = _promote_applied(fm, _rid_)",
        "test_round17_foreign_degraded_recovery_converges",
    ),
    (
        "M3",
        "去掉写序锚方向校验：没有时刻/序数证据也认这个锚",
        SKILL,
        "                            if _ib_a is None and not _ord_ok:\n                                pass                      # 无证据 ⇒ 锚不可用, 走回落\n                            else:",
        "                            if False:  # MUTANT M3 去掉方向校验\n                                pass\n                            else:",
        # ⛔ 目标门换过一次，原因记在这里：原先绑
        # `test_round17_anchor_direction_is_verified`，实测 M3 `SURVIVED(rc=0)`。
        # 那道门的场景里后继 B 是**正常行**（review_time 与 attempt_count 都在），
        # `_ib_a` 不为 None ⇒ 原代码本来就走 else 分支，本变异拆掉的分支在该场景
        # **根本不执行**；它的拒绝来自另一处的「自相矛盾」检查。
        # 变异与门不匹配 ⇒ SURVIVED 不是「防线没用」，是「没有门守着这条防线」。
        # 补了 `test_g32cb_anchor_without_direction_evidence_falls_back`
        # （B 退化成无 review_time / 无 attempt_count 的 §6.3 行）才走得到该分支。
        "test_g32cb_anchor_without_direction_evidence_falls_back",
    ),
    (
        "M4",
        "去掉深度上限：§6.1 输入硬上限的深度维度失效（节点预算仍在）",
        VALIDATOR,
        "        if depth + 1 > MAX_VALUE_DEPTH:",
        "        if False:  # MUTANT M4 拆掉深度判据",
        "test_g32cb_depth_over_limit_rejected_before_first_append",
    ),
    (
        "M5",
        "去掉节点预算：只剩深度维度（证明两个维度各自承重，不是一个兜住另一个）",
        VALIDATOR,
        "        if seen > MAX_VALUE_NODES:",
        "        if False:  # MUTANT M5 拆掉节点判据",
        "test_g32cb_node_budget_over_limit_rejected_before_first_append",
    ),
    (
        "M6",
        "拆掉字符轴判据：非规范码点（NEL/LS/PS/C1/DEL/孤立代理）不再被拒（CARD-G3-2c-C）",
        VALIDATOR,
        "            if lo <= cp <= hi:",
        "            if False:  # MUTANT M6 拆掉字符轴判据",
        "test_g32cc_charaxis_nonconforming_codepoints_rejected",
    ),
    (
        "M7",
        "把禁止集从**区间**退化成**枚举**（只留 round 里点过名的 5 个码点）—— 这正是前 17 轮「修一个再生一个」的形态",
        VALIDATOR,
        # 锚只取区间元组的**头部**（noncharacters 段随后追加），避免每次扩集都要改锚
        "FORBIDDEN_CODEPOINT_RANGES = (\n"
        "    (0x0000, 0x001F),\n"
        "    (0x007F, 0x007F),\n"
        "    (0x0080, 0x009F),\n"
        "    (0x2028, 0x2029),\n"
        "    (0xD800, 0xDFFF),",
        "FORBIDDEN_CODEPOINT_RANGES = (  # MUTANT M7 区间退化成枚举\n"
        "    (0x0085, 0x0085),\n"
        "    (0x2028, 0x2029),\n"
        "    (0x0090, 0x0090),\n"
        "    (0x007F, 0x007F),",
        "test_g32cc_forbidden_set_matches_expected_exactly",
    ),
    (
        "M8",
        "重建已有 receipt 的编码退回裸 json.dumps（round-17 B② 的原缺陷形态）—— "
        "载体必须是 receipt 里、又不受字段级字符轴约束的字段，否则观察不到差异",
        SKILL,
        '                    _rebuilt.append(f"{_pfx}{_kq(_k)}: {q_(_e[_k])}")',
        '                    _rebuilt.append(f"{_pfx}{_k}: {json.dumps(_e[_k], ensure_ascii=False, default=str)}")  # MUTANT M8',
        "test_g32cc_emitter_rebuild_never_mutates_existing_entries",
    ),
    (
        "M9",
        "拆掉 `q_()` 的 **ASCII 转义回落**（`ensure_ascii=True` → `False`）—— "
        "裸形证不成往返、又没有第二条路 ⇒ fail-closed 拒写，敌意载体从「能写、读得回」"
        "退化成「写不进去」",
        SKILL,
        "        _asc = json.dumps(v, ensure_ascii=True)",
        "        _asc = json.dumps(v, ensure_ascii=False)  # MUTANT M9 拆掉 ASCII 转义回落",
        "test_g32ce_q_ascii_escape_fallback_is_load_bearing",
    ),
]


class _Terminated(Exception):
    """把 SIGTERM/SIGINT 转成异常，好让 finally 里的还原跑得到。"""


def _install_signal_handlers() -> None:
    def _handler(signum, _frame):
        raise _Terminated(f"收到信号 {signum}")

    for _sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(_sig, _handler)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_gate(test_name: str) -> tuple[int, str]:
    # ⚠️ 必须继承 os.environ 再覆盖：只给 PATH/HOME 的窄 env 会让写点子进程
    # 拿不到解释器环境而挂住（实测一次 10 分钟外部超时就是这么来的）。
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        r = subprocess.run(
            [_pytest_bin(), "-q", "-p", "no:cacheprovider", f"{LEDGER_TEST}::{test_name}"],
            cwd=WT / "backend",
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
    except OSError as exc:
        # ⛔ 不要让启动失败混进「门红了」里（Codex round-1 LOW）：那会把
        # 「pytest 起不来」读成「防线失效」。
        raise SystemExit(f"✗✗ 起不动 pytest（{_pytest_bin()}）：{type(exc).__name__}: {exc}") from exc
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _self_heal() -> list[str]:
    """启动即自愈：还原**上一次跑残留的**变异体。

    ⛔ 这一层不是冗余。实测教训：装了 SIGTERM handler 也**不够** —— 外部超时
    杀的是整个进程组，handler 还没来得及等 `subprocess.run` 返回就被终止，
    `finally` 的还原没跑完，`MAX_VALUE_DEPTH = 10**9` 就留在了生产文件里。
    无论 finally 和信号处理写得多小心，外部 kill 总可能发生；唯一可靠的兜底
    是**下一次启动时先检查并还原**。
    """
    healed = []
    for mid, _desc, target, old, new, _gate in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if new in src:
            target.write_text(src.replace(new, old, 1), encoding="utf-8")
            healed.append(f"{mid} @ {target.name}")
    return healed


def _anchor_audit() -> tuple[bool, list[tuple[str, int, str, str, str]]]:
    """锚点自检：每条变异的原文本必须在目标文件里**恰好命中 1 次**。

    命中 0 次 = 锚漂了（生产那行改了缩进/改了名），变异写不进去、门照常绿。

    ⚠️ **如实说明这道自检加了什么**（CARD-CX-G3-2c-C-R1）：变异循环里**本来就有**
    `src.count(old) != 1 → ANCHOR-ERROR + continue`，且末尾按
    `n_killed == len(MUTATIONS)` 判定 ⇒ 锚漂时脚本会 `return 1`，**不会**
    报成「8/8 KILLED」的假绿。本函数加的不是那个防线，而是两件事：
      ① 把判断提到所有慢步骤**之前**（原先要等 8 道门的绿态前提跑完才逐条发现）；
      ② 给 `--list` 一个不改任何文件的只读入口。
    别把它写成「防假绿」——那是说得比做得宽。

    ⚠️ **已知盲区，本卡未修**（Codex round-1 LOW，副本实测）：判据是「原文本
    在**整个文件**里出现 1 次」，而不是「命中了那条**执行语句**」。于是
      · 生产那行的前导空格由 20 变 21 —— 锚仍是子串，count 仍为 1；
      · 把活行改成等价写法、只在**注释**里留下旧锚 —— 同样 count 为 1，
        变异落在注释上，变异前后执行块的 AST 完全相同。
    这两种情况下变异是**无效**的，但完整 runner 会把它报成 SURVIVED（非零退出），
    不会伪装成 KILLED。要真正堵上得绑定执行块内的语句身份（AST），属另立卡。
    """
    rows, ok = [], True
    for mid, desc, target, old, _new, gate in MUTATIONS:
        n = target.read_text(encoding="utf-8").count(old)
        rows.append((mid, n, str(target.relative_to(WT)), gate, desc))
        if n != 1:
            ok = False
    return ok, rows


def _print_anchor_rows(rows, *, with_desc: bool) -> None:
    for mid, n, rel, gate, desc in rows:
        print(f"  [{mid}] 锚命中 {n} 次 @ {rel} → {gate}", flush=True)
        if n != 1:
            print("       ⛔ 须恰好 1 次 —— 锚文本漂了，变异会静默失配", flush=True)
        if with_desc:
            print(f"       {desc}", flush=True)


def main() -> int:
    if "--list" in sys.argv[1:]:
        ok, rows = _anchor_audit()
        print("═══ 变异清单与锚点自检 ═══")
        _print_anchor_rows(rows, with_desc=True)
        return 0 if ok else 4

    _install_signal_handlers()
    healed = _self_heal()
    if healed:
        print(f"⚠️ 自愈：还原了上一次残留的变异体 {healed}", flush=True)

    # ── 锚点自检**先于**一切慢步骤：锚漂了就别跑，免得报出「8/8 KILLED」式假绿 ──
    _ok, _rows = _anchor_audit()
    print("═══ 锚点自检 ═══", flush=True)
    _print_anchor_rows(_rows, with_desc=False)
    if not _ok:
        print("⛔ 锚点自检不通过 —— 中止（不跑变异）", flush=True)
        return 4

    # ── 跑前：全文件 sha 基线（对**每个**会被变异的文件，不只是其中一个）──
    touched = sorted({m[2] for m in MUTATIONS}, key=str)
    baseline = {p: _sha(p) for p in touched}
    print("═══ 变异前 sha 基线 ═══", flush=True)
    for p, h in baseline.items():
        print(f"  {h}  {p.relative_to(WT)}", flush=True)

    # ── 绿态前提：变异前每道门必须是绿的，否则「变红」没有意义 ──
    print("\n═══ 绿态前提（变异前每道门必须绿）═══", flush=True)
    for mid, _desc, _f, _old, _new, gate in MUTATIONS:
        rc, _out = _run_gate(gate)
        print(f"  [{mid}] {gate} → rc={rc} {'✅' if rc == 0 else '❌ 前提不成立'}", flush=True)
        if rc != 0:
            print(f"⛔ {mid} 的门在变异前就不是绿的，变异结果无意义。中止。", flush=True)
            return 2

    results = []
    print("\n═══ 变异（串行）═══", flush=True)
    for mid, desc, target, old, new, gate in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if src.count(old) != 1:
            print(f"  [{mid}] ⛔ 锚文本在 {target.name} 中出现 {src.count(old)} 次（须恰好 1 次）— 跳过", flush=True)
            results.append((mid, gate, "ANCHOR-ERROR", desc))
            continue
        try:
            target.write_text(src.replace(old, new, 1), encoding="utf-8")
            rc, out = _run_gate(gate)
            # KILLED 判据：rc 恰为 1（测试失败），且失败的是**指定的那一条**
            killed = rc == 1 and (f"{gate}" in out) and ("1 failed" in out or "failed" in out)
            verdict = "KILLED" if killed else f"SURVIVED(rc={rc})"
            print(f"  [{mid}] {desc}\n        {gate} → rc={rc} ⇒ {verdict}", flush=True)
            if not killed:
                print(
                    f"        ⚠️ 输出尾部: {out.strip().splitlines()[-1][:160] if out.strip() else '(空)'}", flush=True
                )
            results.append((mid, gate, verdict, desc))
        finally:
            # ⛔ 无条件还原。不加任何「文件被第三方改过就别覆盖」的防护——
            # 那种防护会在 exit 时把变异体留在生产文件里。
            target.write_text(src, encoding="utf-8")

    # ── 跑后：逐个复核 sha（外部的、全量的判据，不依赖变异体配合）──
    print("\n═══ 变异后 sha 复核 ═══", flush=True)
    dirty = []
    for p, h0 in baseline.items():
        h1 = _sha(p)
        ok = h0 == h1
        print(f"  {'✅' if ok else '⛔'} {p.relative_to(WT)}  {h1}", flush=True)
        if not ok:
            dirty.append(p)

    print("\n═══ 汇总 ═══", flush=True)
    for mid, gate, verdict, desc in results:
        print(f"  {mid:4} {verdict:16} {gate}", flush=True)
    n_killed = sum(1 for _, _, v, _ in results if v == "KILLED")
    print(f"\n  {n_killed}/{len(MUTATIONS)} KILLED", flush=True)
    if dirty:
        print(f"⛔ 有文件未还原：{[str(p) for p in dirty]}", flush=True)
        return 3
    return 0 if n_killed == len(MUTATIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
