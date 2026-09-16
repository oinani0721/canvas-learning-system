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
  `python3 backend/scripts/g32cb_mutation_gates.py --list`   只列变异与锚点命中数 + 两维绑定自检（不改任何文件）
  `python3 backend/scripts/g32cb_mutation_gates.py --probe`  只**观察**每条实际红在哪条语句上（回填 `EXPECT_LOC` 用，
                                                            不做裁决、rc 恒 4；照样施加变异并无条件还原）
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import traceback
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutation_kill_identity import (  # noqa: E402  (必须在 sys.path 兜底之后)
    VERDICTS,
    RestoreGuard,
    check_expect_loc_unique,
    check_expect_msg_unique,
    failed_locations,
    failed_reasons,
    gate_hit,
    judge_env,
    judge_flags,
    kill_identity,
    loc_token_for,
    stmt_fingerprints,
    syntax_check,
)

WT = Path(__file__).resolve().parents[2]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
LEDGER_TEST = "tests/regression/test_g3_2_review_ledger.py"
#: 门文件绝对路径 —— round-19 的位置判据 (c)① 要拿它比对 pytest 报的失败位置。
GATE_FILE = WT / "backend" / LEDGER_TEST
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


#: 每条变异**声称**会打红的那一条断言的消息片段（首行字面，门文件里恰好 1 次）。
#:
#: ⛔ 为什么必须有（CARD-DEBT-mutation-kill-identity）：原判据
#: `rc == 1 and gate in out and "failed" in out` 只能回答「有没有红」，回答不了
#: 「红在**哪一条断言**上」。本仓已经因此吃过两次假杀（Z2 的 M1 与 M15）。
#: 判据面是 `-rf` 短摘要的 reason —— 它只取断言消息的**第一行**，所以片段必须
#: 落在第一行内（插值之后也算，只要没跨 `\n`）。
#:
#: ⚠️ 逐条的绑定依据（都是**先读门源码推出来**，再由跑批证实/证伪，不是抄跑批结果）：
#:   M1 拆严格 bool ⇒ 非布尔凭据不再被拒 ⇒ 落在 `r.returncode != 0` 那条；
#:   M2 去掉 foreign 凭据提升 ⇒ E1 重跑仍被拒 ⇒ 落在收敛判据那条；
#:   M3 去掉方向校验 ⇒ 方向不可证的锚被采信 ⇒ 落在 `r.returncode != 0` 那条；
#:   M4/M5 拆上限判据 ⇒ 超限输入不再在首写前被拒 ⇒ 各落在自己那条 rc 断言；
#:   M6 拆字符轴判据 ⇒ 写点侧(SKILL.md:2867 复用 `validate_record_full`)不再拒
#:      ⇒ 落在**写点侧**第一条 rc 断言（不是 ③ 的 validator 直调那条 —— 那条在它
#:      之后, 前面先红就跑不到）；
#:   M7 区间退化成枚举 ⇒ 出现漏网码点 ⇒ 落在「漏网 N 个码点」那条；
#:   M8 重建编码退化 ⇒ 门 docstring 自陈「编码退化的直接后果就是 B 写不进去」
#:      ⇒ 落在 `rB.returncode == 0` 那条；
#:   M9 拆 ASCII 转义回落 ⇒ 门 docstring 自陈落在 ① 的 `rc=0` 断言。
EXPECT_MSG: dict[str, str] = {
    "M1": "] 非布尔凭据不得被当成「已应用」",
    # ⛔ **本卡当场更正的一条**（CARD-DEBT-mutation-kill-identity 的第一个真发现）：
    # 作者先按脚本自陈的说法（「E1 重跑仍被拒 ⇒ 两阶段不收敛」）绑到 `:5316` 的
    # `⛔ 恢复后 E1 仍不可重跑`，实跑报 SURVIVED —— 该门**实际**红在**更早**的
    # `:5313 assert r2.returncode == 0, f"E2 应收敛: …"` 上：拆掉 foreign 提升后，
    # **E2 自己就写不进去了**（writer 撞上「receipt 记 true 却仍在待恢复队列」的自相矛盾，
    # fail-closed 拒写），链条在声称的那一步**之前**就断了。
    # ⇒ 防线确实承重（门红了），但**症状与卡文的叙述不是同一条**。旧判据
    # (`rc==1 and gate in out and "failed" in out`) 把这两者记成同一个 KILLED，
    # 于是「两阶段收敛那条断言被这条变异守着」这个说法从来没被验证过。
    # ⚠️ `:5316` 那条断言并没有失去承重方：`g32b` 的 `M161-foreign-no-credential-promotion`
    # （另一种拆法：`_ok_fg = True` 静默跳过提升并谎报成功）实测正落在它上面。
    # 两条变异拆同一道防线的不同侧面、症状不同 —— 这正是新判据能分辨出来的东西。
    "M2": "E2 应收敛: ",
    "M3": "⛔ 方向不可证的锚被直接采信",
    "M4": "⛔ 超限深度必须在首写前拒: rc=",
    "M5": "⛔ 超预算节点数必须在首写前拒: rc=",
    "M6": "/board] 非规范码点必须在首写前拒: rc=",
    "M7": " 个码点，前 8 个: ",
    "M8": "⛔ B 写不进去 ⇒ 重建把 A 的 receipt 弄坏了",
    "M9": "的 ASCII 转义回落没了",
}

#: 显式豁免表 `{id: 具体理由}`。空 = 9 条全绑上了，没有欠账。
EXPECT_MSG_EXEMPT: dict[str, str] = {}


def _check_expect_msg() -> list[str]:
    """`EXPECT_MSG` 完整性 + 唯一性自检（共用实现，见 `mutation_kill_identity`）。"""
    gate_file = str(WT / "backend" / LEDGER_TEST)
    problems = check_expect_msg_unique(
        [(m[0], gate_file, EXPECT_MSG.get(m[0])) for m in MUTATIONS],
        exempt=EXPECT_MSG_EXEMPT,
        # ⛔ 片段还必须在**生产侧命中 0 次**：门里有些断言消息的**第一行**内嵌了
        # `{r.stderr}`，那条断言一旦红，被测子进程的输出就进了判据面。命中 0 次，
        # 生产输出就喂不饱它。⚠️ 只收被变异的那两个生产文件所在面，**不收**
        # `backend/scripts/` 整目录 —— 本文件自己就在那儿，表里逐字写着这些片段。
        prod_roots=(WT / "canvas-vault", WT / "backend" / "app", VALIDATOR),
    )
    stale = sorted((set(EXPECT_MSG) | set(EXPECT_MSG_EXEMPT)) - {m[0] for m in MUTATIONS})
    if stale:
        # ⛔ 反向也要看：表里留着已不存在的 id ⇒ 这张表与变异表脱节了，
        # 「每条都绑好了」这句话不再可信（与 g33 的 baseline_missing 同型）。
        problems.append(f"EXPECT_MSG/EXEMPT 里有已不存在的 id: {stale}")
    return problems


#: **断言源位置身份**（CARD-EXPECT-LOC-NARROW，用户裁定 D-28 的三套尾巴）。
#: 值形如 `stmt:<12 位十六进制>` = `sha256(所在作用域全名 + 语句的 AST 规范化 dump)[:12]`，
#: 由 `mutation_kill_identity.loc_token_for()` 折算（见该模块 `_fp` 的 docstring）。
#:
#: ⛔ **它挡的是哪一种假杀**（Y1-B HIGH-1，UAT-CARD-DEBT-mutkill-R2 §9 #4）：
#: `require_gate_file=True` 这道弱位置判据只问「有**某条**失败落在**门文件**里」。而门
#: 函数里往往既有**前提断言**（`assert _run_writer_settled(...).returncode == 0`，消息里
#: 内嵌被测子进程的输出）又有**目标断言**（这条变异本该打红的那一条）。子进程运行期拼出
#: 的文本里只要含目标断言的 `EXPECT_MSG` 片段，消息维与弱位置维**同时**被喂饱，而目标断言
#: 根本没执行 ⇒ 误判 KILLED。两条断言同在一个文件里，文件级位置分不开它们；绑到**语句**
#: 才分得开。本卡的对照输入存档：`_bmad-output/审查/evidence-expect-loc-narrow/negctl-*`。
#:
#: ⚠️ **这张表是怎么来的，如实说**：由 `--probe` 跑一遍变异、观察每条**实际**红在哪条语句
#: 上再回填 —— **判据与被测量同源**，所以它今天证不出「每条变异确实红在它声称的那条断言
#: 上」。价值在**从今往后**：门文件或生产代码一漂移、击杀落到别的语句上，就当场报
#: SURVIVED；语句本身被改写则报 HARNESS-ERROR（锚失效），而不是静默记 KILLED。
#: 这一条写进了验收单「本卡未证明什么」。
#:
#: ⚠️ 与 `EXPECT_MSG` 的关系是 **AND**：两张表都填的条目要**同时**满足。
#:
#: 回填证据：`_bmad-output/审查/evidence-expect-loc-narrow/probe-g32cb-*.txt`（9 条全部
#: 落在门文件里，无门外条目 ⇒ `EXPECT_LOC_EXEMPT` 为空）。行号注释是**回填当时**的观察值，
#: ⚠️ 指纹不随行号漂移（`_fp` 不含行号），门文件插注释/挪位置不会让它失配；**改断言文本或
#: 改测试函数名**才会 —— 那时报 HARNESS-ERROR「锚失效」，这是想要的方向。
EXPECT_LOC: dict[str, str] = {
    "M1": "stmt:03581c229ae0",  # 行 5221 · test_round17_fsrs_applied_must_be_strict_bool
    "M2": "stmt:41baf694c75b",  # 行 5313 · test_round17_foreign_degraded_recovery_converges
    "M3": "stmt:f944600be7cc",  # 行 5679 · test_g32cb_anchor_without_direction_evidence_falls_back
    "M4": "stmt:04b10d4bfe3b",  # 行 5419 · test_g32cb_depth_over_limit_rejected_before_first_append
    "M5": "stmt:0bf156d1a85b",  # 行 5458 · test_g32cb_node_budget_over_limit_rejected_before_first_append
    "M6": "stmt:c267f2ad5ddb",  # 行 5789 · test_g32cc_charaxis_nonconforming_codepoints_rejected
    "M7": "stmt:25baffef62be",  # 行 5858 · test_g32cc_forbidden_set_matches_expected_exactly
    "M8": "stmt:2a0babae6251",  # 行 6565 · test_g32cc_emitter_rebuild_never_mutates_existing_entries
    "M9": "stmt:10f3f6f4fd85",  # 行 6377 · test_g32ce_q_ascii_escape_fallback_is_load_bearing
}

#: 位置落在**共享 helper** 的断言上：指纹唯一、绑得上，但证不了红在**哪一道门**的调用
#: ⇒ 身份比「绑到本门函数里的那一条断言」弱一档。⛔ 与 `EXPECT_LOC_EXEMPT` 语义不同：
#: 这里是「绑上了但弱一档」，那里是「根本没绑」。不登记的话，新增一条时没人知道它落进了
#: helper（范式见 `g32b_mutation_gates.py::EXPECT_LOC_HELPER`）。
EXPECT_LOC_HELPER: dict[str, str] = {}

#: 位置绑不出来的条目 `{id: 具体理由}`。空 = 没有欠账。
#: ⛔ **这些条目落哪一档，如实说**：本套 `EXPECT_MSG` 覆盖率 100%、`EXPECT_MSG_EXEMPT`
#: 为空 ⇒ `kill_identity()` 只在 `expect_loc` 与 `expect_msg` **两维同时为空**时才给
#: `KILLED-UNBOUND`，本套取不到那一档。位置豁免条目的实际结果是 **`KILLED` + 「仅消息维」**
#: （`require_gate_file` 保持 `True`，弱位置判据仍在）。⛔ 不得照抄 g32b 的
#: `require_gate_file=tag not in EXPECT_LOC_EXEMPT`：那是为「两维皆空 ⇒ KILLED-UNBOUND」
#: 的条目写的，在本套会把「弱位置 AND 消息」整块降成「只消息」= 放宽判据。
EXPECT_LOC_EXEMPT: dict[str, str] = {}


def _check_expect_loc() -> list[str]:
    """`EXPECT_LOC` 完整性 + 唯一性自检（共用实现，见 `mutation_kill_identity`）。"""
    gate_file = str(GATE_FILE)
    problems = check_expect_loc_unique(
        [(m[0], gate_file, EXPECT_LOC.get(m[0])) for m in MUTATIONS],
        exempt=EXPECT_LOC_EXEMPT,
    )
    stale = sorted((set(EXPECT_LOC) | set(EXPECT_LOC_EXEMPT)) - {m[0] for m in MUTATIONS})
    if stale:
        # ⛔ 反向也要看：表里留着已不存在的 id ⇒ 这张表与变异表脱节了（同 `_check_expect_msg`）。
        problems.append(f"EXPECT_LOC/EXEMPT 里有已不存在的 id: {stale}")
    stale_h = sorted(set(EXPECT_LOC_HELPER) - {m[0] for m in MUTATIONS})
    if stale_h:
        problems.append(f"EXPECT_LOC_HELPER 里有已不存在的 id: {stale_h}")
    # ⛔ 指纹所在作用域必须就是该条变异点名的那道门；落在共享 helper 里的必须显式登记
    # `EXPECT_LOC_HELPER`（身份弱一档）。不核这一条的话，「绑到了具体断言」这句话会把
    # 「绑到了某个被多道门共用的 helper 断言」也算进去 —— 比证据宽。
    from mutation_kill_identity import _fp, _stmts_with_scope  # 局部导入：不在顶部再挂一层

    scopes: dict[str, str] = {}
    for node, sc in _stmts_with_scope(GATE_FILE):
        scopes.setdefault(_fp(node, sc), sc)
    for m in MUTATIONS:
        loc = EXPECT_LOC.get(m[0])
        if not loc or not loc.startswith("stmt:"):
            continue
        sc = scopes.get(loc[5:])
        if sc is None:
            continue  # 「指纹已找不到」由共用自检报，这里不重复
        if sc != m[5] and m[0] not in EXPECT_LOC_HELPER:
            problems.append(
                f"{m[0]}: expect_loc 的指纹落在作用域 `{sc}`（≠ 门 {m[5]}）—— 共享 helper "
                f"身份弱一档，须登记 EXPECT_LOC_HELPER 并写理由"
            )
    return problems


def _loc_coverage_line() -> str:
    """只读入口打印的绑定覆盖行。⛔ 文案与表一一对应，不自述「全部绑到具体断言」。"""
    return (
        f"  绑定覆盖：EXPECT_MSG {len(EXPECT_MSG)} 条 / EXPECT_LOC {len(EXPECT_LOC)} 条 "
        f"/ 消息豁免 {len(EXPECT_MSG_EXEMPT)} / 位置豁免 {len(EXPECT_LOC_EXEMPT)} "
        f"/ 位置弱一档(共享 helper) {len(EXPECT_LOC_HELPER)} （共 {len(MUTATIONS)} 条变异）"
    )


#: 当前**已落盘**的变异 `{路径: 原始文本}` —— 信号到达时按它无条件还原。
_ACTIVE_SNAPSHOT: dict[Path, str] = {}


def _restore_active() -> None:
    """把 `_ACTIVE_SNAPSHOT` 里记着的文件写回。幂等。"""
    for _p, _t in list(_ACTIVE_SNAPSHOT.items()):
        _p.write_text(_t, encoding="utf-8")
    _ACTIVE_SNAPSHOT.clear()


def _restore_active_or_keep_exit_code() -> None:
    """还原；若已在退出展开中，二次还原的异常**吞掉**以保住约定退出码。

    ⛔ round-3 MEDIUM：`RestoreGuard._finish` 抛 `SystemExit(131)` 后，调用方栈展开
    仍会进入 `finally` 再还原一次。若还原持续遇到同一个 I/O 错误（例如存证写入失败），
    第二次异常会**替换掉** `SystemExit(131)`，进程按未捕获异常退出 —— 约定的
    「还原失败=131」这个信号就丢了。还原尝试与诊断都保留，只是不让它改写退出码。
    """
    # ⛔ round-4 HIGH：判据必须绑**进入包装时**的状态。`exiting()` 在 `_finish` 抛出
    # **之前**就已置位，所以「捕获到异常时 exiting() 为 True」既可能是二次异常，也可能
    # 是**本次还原自己触发的首次 SystemExit(130)** —— 后者被吞掉就等于信号退出失效，
    # 进程继续跑下一条变异。只抑制「进来前就已在退出展开」的那种。
    _was_exiting = _GUARD.exiting()
    try:
        _restore_active()
    except BaseException:
        if not _was_exiting:
            raise
        try:
            traceback.print_exc()
        except BaseException:  # noqa: BLE001
            pass


#: ⛔ round-19 统一（CARD-DEBT-mutkill-R2 (h)）：四个信号（**补齐 SIGQUIT** ——
#: 收口前这里只挂 SIGTERM/SIGINT/SIGHUP，而 SIGQUIT 的默认处置同样不做栈展开）
#: + 先还原再退出 + **还原期不可打断**（旧写法把信号转异常让 finally 跑，信号若
#: 落在还原循环内部，异常从 finally 里逃出去 ⇒ 部分还原）。
_GUARD = RestoreGuard(_restore_active)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _nodeid(test_name: str) -> str:
    """门函数名 → pytest nodeid。判据比的是 nodeid，不是「门名字样在输出里」。"""
    return f"{LEDGER_TEST}::{test_name}"


def _observed_loc(out: str) -> tuple[str | None, str | None]:
    """本次失败的**位置** token（`--probe` 回填 `EXPECT_LOC` 用）；没有则 `(None, None)`。

    ⛔ 回填这件事如实说：它是「跑一次看它红在哪」再写回表里，**判据与被测量同源** ——
    今天证不出「这条变异确实打红了它声称的那条断言」。价值在**从今往后**（见
    `EXPECT_LOC` 的表头注释）。
    ⚠️ 原始 `<路径>:<行号>` 也一并返回：`expect_loc` 的取值方式将来若再变，有了原始
    位置就能**离线重算**，不必再跑一趟 probe（范式：g32b `observed_loc`）。
    """
    locs = failed_locations(out)
    if not locs:
        return None, None
    path, lineno, _ = locs[0]
    return loc_token_for(GATE_FILE, path, lineno), f"{path}:{lineno}"


def _run_gate(test_name: str) -> tuple[int, str]:
    # ⚠️ 必须继承 os.environ 再覆盖：只给 PATH/HOME 的窄 env 会让写点子进程
    # 拿不到解释器环境而挂住（实测一次 10 分钟外部超时就是这么来的）。
    env = dict(os.environ)
    # ⛔ judge_env() 放在**后面**覆盖 os.environ：外层导出的 COLUMNS=80 会把
    # `-rf` 短摘要的 reason 截成空串 ⇒ expect_msg 恒不命中 ⇒ 全报 SURVIVED。
    env.update(judge_env())
    try:
        r = subprocess.run(
            # ⛔ 命令行开关统一从 `judge_flags()` 取（round-19，四套一份）：`-rf` 给
            # 短摘要、`--tb=line` 给失败位置行、`--show-capture=no` 让被测进程的
            # captured 输出根本不进判据面。少哪一条会怎么坏见该函数 docstring。
            [_pytest_bin(), *judge_flags(), _nodeid(test_name)],
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
        for p in _check_expect_msg():
            print(f"  ⛔ EXPECT_MSG 自检: {p}")
            ok = False
        # ⛔ 位置判据同样要进只读入口的退出码 —— 否则「`--list` 通过」只覆盖了两维里的
        # 一维，说得比证据宽（范式：g32b `--list` 块）。
        for p in _check_expect_loc():
            print(f"  ⛔ EXPECT_LOC 自检: {p}")
            ok = False
        print(_loc_coverage_line())
        return 0 if ok else 4

    # `--probe` = **观察**入口（首次回填 `EXPECT_LOC` 用）：跑变异、但**不做裁决**，
    # 每条一律记 OBSERVED、rc 恒 4 —— 它的输出不可能被误读成「通过」。
    # ⚠️ 它照样会写盘（施加变异后无条件还原），不是「只读」；「只读」的是**结论**。
    _probe = "--probe" in sys.argv[1:]

    # ⛔ EXPECT_MSG 自检**先于**一切慢步骤：绑不唯一 ⇒ 「红在哪一条断言上」
    # 不再可证，跑完再报等于白跑 20 分钟。
    if bad := _check_expect_msg():
        for p in bad:
            print(f"⛔ EXPECT_MSG 自检失败 — {p}", flush=True)
        return 4
    # ⛔ `--probe` 跳过位置自检：它就是**为了**把 `EXPECT_LOC` 填出来才跑的，表还空着。
    # 作为交换，probe 一律不判定、rc 恒 4（与 g32b 同口径）。
    if not _probe:
        if bad := _check_expect_loc():
            for p in bad:
                print(f"⛔ EXPECT_LOC 自检失败 — {p}", flush=True)
            return 4

    _GUARD.install()
    # ⛔ 自愈也在写盘且发生在 install() 之后 —— 与 g32b 同款窗口(已落盘但快照未登记),
    # 放进 critical(): 这段期间收到的信号只记待办、不打断(独立复核 2026-09-08)。
    with _GUARD.critical():
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
    #: `--probe` 的观察表 `{id: (stmt token, 原始 <路径>:<行号>, rc)}`。
    _observed: dict[str, tuple[str | None, str | None, int]] = {}
    print("\n═══ 变异（串行）═══", flush=True)
    for mid, desc, target, old, new, gate in MUTATIONS:
        src = target.read_text(encoding="utf-8")
        if src.count(old) != 1:
            print(f"  [{mid}] ⛔ 锚文本在 {target.name} 中出现 {src.count(old)} 次（须恰好 1 次）— 跳过", flush=True)
            results.append((mid, gate, "ANCHOR-ERROR", desc))
            continue
        mutated_text = src.replace(old, new, 1)
        # ⛔ 先编译自检，再跑门：语法不合法的变异体让被测进程在**编译期**就死，
        # 于是「防线被拆掉之后本该发生的坏事」根本没机会发生，而门却因为**别的
        # 断言**红了被记成 KILLED（Z2 的 M15 就是这个形态）。它照出的是负控自己
        # 坏了 —— 单列第三种裁决，不并进 KILLED / SURVIVED 任何一边。
        if syn := syntax_check(target, mutated_text):
            print(f"  [{mid}] ⛔ SYNTAX-INVALID 变异体编译不过 — {syn}", flush=True)
            results.append((mid, gate, "SYNTAX-INVALID", desc))
            continue
        try:
            # ⛔ 先登记快照再落盘：信号可能落在 write 与 finally 之间。
            _ACTIVE_SNAPSHOT[target] = src
            target.write_text(mutated_text, encoding="utf-8")
            rc, out = _run_gate(gate)
            nodeid = _nodeid(gate)
            expect = EXPECT_MSG.get(mid)
            if _probe:
                # ⛔ probe 只**观察**，从不判定：裁决一律 OBSERVED、rc 恒 4。
                _tok, _raw = _observed_loc(out)
                _observed[mid] = (_tok, _raw, rc)
                print(f"  [{mid}] {gate} → OBSERVED rc={rc} loc={_tok!r} at={_raw!r}", flush=True)
                results.append((mid, gate, "OBSERVED", desc))
                continue
            # ⛔ round-19：裁决统一走共用模块的 `kill_identity()`，六档口径与另三套
            # 逐字一致。它内部依次判：判据面在不在 → rc 是不是 1 → 摘要区里失败的
            # 是不是指定的那道门 → 失败**位置**在不在门文件里（(c)① 弱位置判据）→
            # 失败位置是不是 `EXPECT_LOC` 指名的那条语句 → 摘要区 reason 含不含 `EXPECT_MSG`。
            # ⛔ CARD-EXPECT-LOC-NARROW（D-28 的三套尾巴）：`expect_loc` 补齐之后，
            # Y1-B HIGH-1 那种「前提断言把子进程输出插进消息首行」的形态被挡住 ——
            # 前提断言与目标断言同在门文件里，弱位置判据分不开，语句级指纹分得开。
            # ⚠️ `require_gate_file` **恒 `True`**，位置豁免条目也不例外：
            # `kill_identity()` 里 `if require_gate_file or expect_loc is not None:` 是
            # **整块**弱位置判据，对「有 expect_msg、无 expect_loc」的条目置 False 等于
            # 把它从「弱位置 AND 消息」降成「只消息」= 放宽判据（口径见 EXPECT_LOC_EXEMPT）。
            verdict, why = kill_identity(
                rc,
                out,
                nodeid,
                expect,
                gate_file=GATE_FILE,
                expect_loc=EXPECT_LOC.get(mid),
                require_gate_file=True,
            )
            killed = verdict.startswith("KILLED")
            print(f"  [{mid}] {desc}\n        {gate} → rc={rc} ⇒ {verdict} ({why})", flush=True)
            if not killed:
                obs = [r for nid, r in failed_reasons(out) if gate_hit(nodeid, {nid})]
                locs = [(Path(_p).name, _ln) for _p, _ln, _ in failed_locations(out)]
                print(f"        ⚠️ expect={expect!r}", flush=True)
                print(f"        ⚠️ 该门实际拒因: {obs or '(该门没红)'}", flush=True)
                print(f"        ⚠️ 实际失败位置: {locs or '(无位置行)'}", flush=True)
                print(
                    f"        ⚠️ 输出尾部: {out.strip().splitlines()[-1][:160] if out.strip() else '(空)'}", flush=True
                )
            results.append((mid, gate, verdict, desc))
        finally:
            # ⛔ 无条件还原。不加任何「文件被第三方改过就别覆盖」的防护——
            # 那种防护会在 exit 时把变异体留在生产文件里。
            # ⛔ round-19：放进 `critical()`，还原期收到的信号只记待办、不打断。
            with _GUARD.critical():
                # round-4 MEDIUM: 接入已定义的保号函数（此前只定义未调用）。
                _restore_active_or_keep_exit_code()

    # ── 跑后：逐个复核 sha（外部的、全量的判据，不依赖变异体配合）──
    print("\n═══ 变异后 sha 复核 ═══", flush=True)
    dirty = []
    for p, h0 in baseline.items():
        h1 = _sha(p)
        ok = h0 == h1
        print(f"  {'✅' if ok else '⛔'} {p.relative_to(WT)}  {h1}", flush=True)
        if not ok:
            dirty.append(p)

    if _probe:
        # ⛔ probe 的输出不进裁决口径：单独一张观察表 + rc 恒 4。⚠️ 还原自检（上面那段
        # sha 复核）**照跑** —— 观察模式一样会写盘，还原没干净必须当场报出来。
        print("\n── PROBE 观察表（不是裁决）──", flush=True)
        for _t, (_tok, _raw, _rc) in _observed.items():
            print(f"  {_t}\trc={_rc}\tloc={_tok!r}\tat={_raw!r}", flush=True)
        print("\n── 可回填的 EXPECT_LOC（观察值, 不是已验证的期望值）──", flush=True)
        _fps = stmt_fingerprints(GATE_FILE)
        for _t, (_tok, _raw, _rc) in _observed.items():
            _lines = _fps.get(_tok[5:], []) if _tok and _tok.startswith("stmt:") else []
            print(f'    "{_t}": "{_tok}",   # 门文件行 {_lines or "(不在门文件里)"} ← {_raw}', flush=True)
        if dirty:
            print(f"⛔ 有文件未还原：{[str(p) for p in dirty]}", flush=True)
            return 3
        print("\n⚠️ --probe 只观察不判定，rc 恒为 4。", flush=True)
        return 4

    print("\n═══ 汇总 ═══", flush=True)
    for mid, gate, verdict, desc in results:
        print(f"  {mid:4} {verdict:22} {gate}", flush=True)
    # ⛔ round-19：六档口径与另三套逐字一致（`mutation_kill_identity.VERDICTS`），
    # 且「六档之和 = len(MUTATIONS)」是可核的不变量 —— 原先有个 `JUDGE-SURFACE-MISSING`
    # 第七档不在任何计数里，一条落进去就无声消失。
    n = {v: sum(1 for _, _, x, _ in results if x == v) for v in VERDICTS}
    # ⛔ 文案不得比证据宽（同型教训 2026-09-08 已在 g32b 犯过一次）：位置豁免条目**没有**
    # 绑到具体断言，它们仍只是「弱位置 + 消息」；所以这里逐项报数，不写「全部绑到具体断言」。
    # ⛔ 也不得写「⇒ KILLED-UNBOUND」：本套 `EXPECT_MSG` 覆盖率 100%，那一档取不到
    # （`kill_identity()` 只在两维同时为空时才给），位置豁免条目实际落「仅消息维 KILLED」。
    print(
        f"\n  {n['KILLED']}/{len(MUTATIONS)} KILLED "
        f"(绑定: 消息 + 断言源位置(`stmt:` 指纹) {len(EXPECT_LOC)} 条; "
        f"位置豁免 {len(EXPECT_LOC_EXEMPT)} 条 = **仅消息维**, 位置仍只绑到门文件一级; "
        f"位置弱一档(共享 helper) {len(EXPECT_LOC_HELPER)} 条)",
        flush=True,
    )
    print(f"  KILLED-UNBOUND: {n['KILLED-UNBOUND']} (仅证明指定门红了)", flush=True)
    print(f"  SURVIVED: {n['SURVIVED']}", flush=True)
    print(f"  HARNESS-ERROR: {n['HARNESS-ERROR']} (负控自己坏了, 不是关于被测物的结论)", flush=True)
    # ⛔ 两者都**不是**关于被测物的结论：ANCHOR-ERROR 是变异没打进去，
    # SYNTAX-INVALID 是负控自己坏了。单列，不许并进 KILLED / SURVIVED 任何一边。
    print(f"  ANCHOR-ERROR: {n['ANCHOR-ERROR']} (变异未施加)", flush=True)
    print(f"  SYNTAX-INVALID: {n['SYNTAX-INVALID']} (>0 说明负控自己坏了)", flush=True)
    # ⛔ 分母必须是「本次**应该**处理多少条变异」，不是 `len(results)` —— 后者恒等于
    # 六档之和（每个写进 `results` 的裁决值都字面来自 `VERDICTS`），那是个**恒真判据**。
    # 用变异条数当分母才能抓住「某条变异跑完没落进任何一档」（独立复核 2026-09-08）。
    _total = sum(n.values())
    _sum_ok = _total == len(MUTATIONS)
    print(
        f"  六档之和: {_total} (应 = 变异条数 {len(MUTATIONS)}) "
        f"{'✓' if _sum_ok else '⛔ 对不上, 有条目没落进任何一档'}",
        flush=True,
    )
    n_killed = n["KILLED"]
    if dirty:
        print(f"⛔ 有文件未还原：{[str(p) for p in dirty]}", flush=True)
        return 3
    # ⛔ 退出码语义四套统一（独立复核 2026-09-08：原先 HARNESS-ERROR 与 SURVIVED 压成
    # 同一个 rc=1 —— 「pytest 没跑成」与「门不承重」两个方向完全相反的结论共用一个码）：
    #   rc=2  有 HARNESS-ERROR（负控自己坏了，先去修 harness，别去改门）
    #   rc=1  有 SURVIVED 或别的 failures（关于被测物的结论）
    #   rc=4  部分跑（--only / --probe / --list 自检不过）—— 不构成全量结论
    #   rc=0  全部 KILLED；⚠️ **已登记**的 KILLED-UNBOUND 残留只报不判失败 ——
    #         未登记的那种在跑之前就被 `_check_expect_loc()` / `_check_expect_msg()`
    #         挡在 rc=2 上了，走不到这里。
    if not _sum_ok:
        print("⛔ 六档计数对不上 —— 有条目没落进任何一档，计数口径坏了(负控自己坏, rc=2)", flush=True)
        return 2
    if n["HARNESS-ERROR"]:
        print(f"⛔ HARNESS-ERROR {n['HARNESS-ERROR']} 条 —— 负控自己坏了 (rc=2)", flush=True)
        return 2
    return 0 if (n_killed + n["KILLED-UNBOUND"]) == len(MUTATIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
