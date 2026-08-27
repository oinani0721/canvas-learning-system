#!/usr/bin/env python3
"""G5-1 (c)(d) — headless 回归机械裁判 v2 (BATCH-2026-08-27-第四批 / CARD-G5-1)。

v2 (Codex 一轮 BLOCKER-3 / HIGH-3 加固): 未执行、损坏、复用或半截日志一律判 FAIL。

逐条判定:
  J0 会话流完整性 (v2 新增):
     - 全部行必须是合法 JSON (坏行数 > 0 即 FAIL — 半截/损坏日志不许静默通过)
     - 恰 1 个 init 事件, 且 init.cwd == 本 worktree canvas-vault (跑错目录判废)
     - ≥1 个 result 落幕事件: subtype == success, 或 error_max_turns (有界截断——
       会话被 --max-turns 采样上限收束, transcript 完整落幕, 判定按截断前完整流并显式标注)
     - 全日志 session_id 唯一, 且**跨日志不得复用** (复制一份干净日志伪造全绿被此抓死)
  J1 skill 触发证据 (三个证据面全查, 任一命中即算触发):
     a. assistant tool_use name == "Skill" (显式调用形状)
     b. 任意行含 "Launching skill: <live-skill>" (Skill 工具 result 形状)
     c. 任意行含 command 展开痕迹: "<command-name>/<skill>" 或 '"commandName": "/<skill>"'
     负例: 三面必须全部零命中; 正例: 见下
  J2 outputs/ 清单前后一致 (负例) / 只许 outputs/ 新增 (正例, 逐行核 diff)
  J3 vault 内容面 manifest 前后逐字节一致 (负例) / 变更行必须全部是 outputs/ 加行 (正例)

正例触发判定 (两种实测形状, 2026-08-27 核实):
  形状一 (带参斜杠 → CLI slash command 展开注入, 无 Skill 工具调用):
     触发证据 = **Bash tool_use 引用 .claude/skills/<skill>/scripts/** (真的执行了 skill
     专属收集器, 普通 Read 不算) **且** 日志含 "VERIFY PASS" (skill 全链跑到机械自检过)
  形状二 (裸斜杠): 显式 Skill(skill) 调用
无参路径的选板询问: headless 工具面无 AskUserQuestion (init.tools 实测), 接受
AskUserQuestion tool_use, 或 (该工具不在 init.tools 且末轮文本枚举 ≥2 块板名并发问 =
环境强制文本降级, PASS 并显式标注)。AskUserQuestion UI 本体须交互环境实测。

退出码: 0 全部 PASS / 1 任一 FAIL / 2 缺产物
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
VAULT = REPO / "canvas-vault"
GREEN, RED, RESET = "\033[92m", "\033[91m", "\033[0m"

WRITE_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit", "Bash"}
#: live skill 全集 — 触发证据面 b/c 的匹配对象
LIVE_SKILLS = sorted(
    p.parent.name for p in (VAULT / ".claude" / "skills").glob("*/SKILL.md")
)


def parse_log(log: Path) -> dict:
    uses: list[dict] = []
    init_tools: list[str] = []
    init_count = 0
    init_cwd = ""
    result_success = 0
    result_total = 0
    bounded = False
    bad_lines = 0
    session_ids: set[str] = set()
    last_text = ""
    last_event_type = ""
    skill_evidence: list[str] = []
    raw_lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for raw in raw_lines:
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            bad_lines += 1
            continue
        sid = obj.get("session_id")
        if sid:
            session_ids.add(sid)
        t = obj.get("type")
        last_event_type = t or last_event_type
        if t == "system" and obj.get("subtype") == "init":
            init_count += 1
            init_tools = obj.get("tools", []) or []
            init_cwd = obj.get("cwd", "")
        elif t == "result":
            result_total += 1
            if obj.get("subtype") == "success":
                result_success += 1
            elif obj.get("subtype") == "error_max_turns":
                result_success += 1  # 有界截断: 会话被 --max-turns 采样上限收束,
                # transcript 完整落幕, 非伪造/损坏 — 判定按截断前的完整流进行
                bounded = True
        # 证据面 b/c: 在原始行上匹配 (含 user 侧 tool_result / 命令展开痕迹)
        for s in LIVE_SKILLS:
            for pat in (
                f"Launching skill: {s}",
                f"<command-name>/{s}",
                f'"commandName": "/{s}"',
                f'"commandName":"/{s}"',
            ):
                if pat in raw:
                    skill_evidence.append(f"{s} ({pat.split(':')[0].strip()})")
        if t == "assistant":
            for c in obj.get("message", {}).get("content", []):
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    uses.append({"name": c.get("name"), "input": c.get("input", {})})
                elif c.get("type") == "text" and (c.get("text") or "").strip():
                    last_text = c["text"]
    return {
        "uses": uses,
        "init_tools": init_tools,
        "init_count": init_count,
        "init_cwd": init_cwd,
        "result_success": result_success,
        "result_total": result_total,
        "bounded": bounded,
        "last_event_type": last_event_type,
        "bad_lines": bad_lines,
        "session_ids": session_ids,
        "last_text": last_text,
        "skill_evidence": sorted(set(skill_evidence)),
        "raw": "\n".join(raw_lines),
    }


def vault_board_stems() -> list[str]:
    boards = VAULT / "原白板"
    return sorted(p.stem for p in boards.glob("*.md")) if boards.is_dir() else []


def check_stream_integrity(log_id: str, p: dict) -> bool:
    ok = True
    if p["bad_lines"]:
        print(
            f"{RED}[{log_id}] J0 ✗ 日志含 {p['bad_lines']} 行坏 JSON (损坏/半截日志不算证据){RESET}"
        )
        ok = False
    if p["init_count"] != 1:
        print(f"{RED}[{log_id}] J0 ✗ init 事件 {p['init_count']} 个 (须恰 1){RESET}")
        ok = False
    elif Path(p["init_cwd"]).resolve() != VAULT.resolve():
        print(
            f"{RED}[{log_id}] J0 ✗ init.cwd={p['init_cwd']!r} 不是本 worktree vault{RESET}"
        )
        ok = False
    if p["result_success"] < 1:
        print(
            f"{RED}[{log_id}] J0 ✗ 无 result 落幕事件 (success/error_max_turns 之外的中断不算证据){RESET}"
        )
        ok = False
    elif p["result_total"] != 1 or p["last_event_type"] != "result":
        print(
            f"{RED}[{log_id}] J0 ✗ result 须恰 1 个且为末事件 "
            f"(实况 {p['result_total']} 个, 末事件={p['last_event_type']!r} — 拼接/续写日志判废){RESET}"
        )
        ok = False
    if len(p["session_ids"]) != 1:
        print(
            f"{RED}[{log_id}] J0 ✗ session_id 数 {len(p['session_ids'])} (须恰 1, 混流/拼接判废){RESET}"
        )
        ok = False
    if ok:
        note = (
            " · ⚠ error_max_turns 有界截断(采样上限收束, 判定按截断前完整流)"
            if p["bounded"]
            else ""
        )
        print(
            f"[{log_id}] J0 ✓ 会话流完整 (init·cwd 绑定 + result 落幕 + 零坏行 + 单一 session){note}"
        )
    return ok


def manifest_pair(log_id: str, suffix: str) -> tuple[Path, Path]:
    return (
        HERE / "manifests" / f"{log_id}{suffix}-before.txt",
        HERE / "manifests" / f"{log_id}{suffix}-after.txt",
    )


def check_positive_diff_outputs_only(log_id: str) -> bool:
    """正例: 内容面 diff 的每一行都必须是 outputs/ 下的新增。"""
    b, a = manifest_pair(log_id, "")
    if not (b.exists() and a.exists()):
        print(f"{RED}[{log_id}] J3 ✗ 缺 manifest{RESET}")
        return False
    before = set(b.read_text(encoding="utf-8").splitlines())
    after = set(a.read_text(encoding="utf-8").splitlines())
    removed = before - after
    added = after - before
    bad_removed = sorted(removed)
    bad_added = [ln for ln in added if not ln.split("  ", 1)[-1].startswith("outputs/")]
    if bad_removed or bad_added:
        print(
            f"{RED}[{log_id}] J3 ✗ 写侧越界: 消失/改动 {bad_removed[:3]} · outputs 外新增 {bad_added[:3]}{RESET}"
        )
        return False
    print(f"[{log_id}] J3 ✓ 变更恰为 outputs/ 新增 {len(added)} 行, 零删改零越界")
    return True


def check_sidecar(log_id: str, expect_utterance: str | None) -> bool:
    """v3: runner sidecar 绑定 — id 与话语必须与断言表抽取的 TSV 一致
    (交换两份干净日志冒名顶替被此挡住; 信任边界: sidecar 由 runner 生成,
    完整不可伪造性需签名转录, 超出本卡, 如实声明)。"""
    meta_p = HERE / "manifests" / f"{log_id}-meta.json"
    if not meta_p.exists():
        print(
            f"{RED}[{log_id}] J0 ✗ 缺 runner sidecar ({meta_p.name}) — 无法绑定话语{RESET}"
        )
        return False
    try:
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"{RED}[{log_id}] J0 ✗ sidecar 损坏{RESET}")
        return False
    if meta.get("id") != log_id:
        print(f"{RED}[{log_id}] J0 ✗ sidecar id={meta.get('id')!r} 不匹配{RESET}")
        return False
    if expect_utterance is not None and meta.get("utterance") != expect_utterance:
        print(f"{RED}[{log_id}] J0 ✗ sidecar 话语与断言表不一致 (冒名顶替?){RESET}")
        return False
    print(
        f"[{log_id}] J0 ✓ sidecar 绑定 (id+话语一致, exit_code={meta.get('exit_code')})"
    )
    return True


def judge_one(
    log_id: str,
    positive_skill: str | None,
    want_ask: bool,
    want_verify_pass: bool,
    expect_utterance: str | None = None,
) -> tuple[bool, set[str]]:
    log = HERE / "logs" / f"{log_id}.jsonl"
    if not log.exists():
        print(f"{RED}[{log_id}] 缺日志 {log}{RESET}")
        return False, set()
    p = parse_log(log)
    ok = check_stream_integrity(log_id, p)
    uses = p["uses"]
    skill_calls = [u for u in uses if u["name"] == "Skill"]
    names = sorted({u["name"] for u in uses})
    writes = [u["name"] for u in uses if u["name"] in WRITE_TOOLS]

    if positive_skill is None:
        ok &= check_sidecar(log_id, expect_utterance)
        misfires = [
            u["input"].get("skill") or u["input"].get("command") for u in skill_calls
        ]
        if misfires or p["skill_evidence"]:
            print(
                f"{RED}[{log_id}] J1 ✗ 触发证据命中: Skill调用={misfires} 展开痕迹={p['skill_evidence']}{RESET}"
            )
            ok = False
        else:
            print(
                f"[{log_id}] J1 ✓ 三面零命中 (tool_use 全名单: {names or '无'}; "
                f"Bash/写侧尝试 {len(writes)} 次—vault 外侧效应人工复核)"
            )
        for suffix, label in (("", "J3 vault 内容面"), ("-outputs", "J2 outputs/")):
            b, a = manifest_pair(log_id, suffix)
            if not (b.exists() and a.exists()):
                print(f"{RED}[{log_id}] {label} ✗ 缺 manifest{RESET}")
                ok = False
                continue
            if b.read_bytes() == a.read_bytes():
                print(f"[{log_id}] {label} ✓ 前后一致")
            else:
                print(f"{RED}[{log_id}] {label} ✗ 有变化{RESET}")
                ok = False
    else:
        hit = [
            u for u in skill_calls if (u["input"].get("skill") or "") == positive_skill
        ]
        # 形状一: Bash 真执行 skill 专属脚本 (Read 该目录不算) + VERIFY PASS 双条件
        bash_fp = [
            u
            for u in uses
            if u["name"] == "Bash"
            and f".claude/skills/{positive_skill}/scripts/"
            in json.dumps(u["input"], ensure_ascii=False)
        ]
        verify_pass = "VERIFY PASS" in p["raw"]
        if hit:
            print(
                f"[{log_id}] J1 ✓ Skill({positive_skill}) 显式调用触发 (共 {len(hit)} 次)"
            )
        elif bash_fp and (verify_pass or not want_verify_pass):
            note = " + VERIFY PASS" if verify_pass else ""
            print(
                f"[{log_id}] J1 ✓ 斜杠命令展开触发 (Bash 实跑 skill 脚本 ×{len(bash_fp)}{note})"
            )
        else:
            print(
                f"{RED}[{log_id}] J1 ✗ 未确证触发 {positive_skill} — Skill调用={bool(hit)} "
                f"Bash脚本指纹={len(bash_fp)} VERIFY_PASS={verify_pass}{RESET}"
            )
            ok = False
        if want_verify_pass and not verify_pass:
            print(
                f"{RED}[{log_id}] J1 ✗ 要求 VERIFY PASS 的正例未见 VERIFY PASS (不分触发形状){RESET}"
            )
            ok = False
        if want_ask:
            asks = [u for u in uses if u["name"] == "AskUserQuestion"]
            if asks:
                print(f"[{log_id}]    ✓ AskUserQuestion 出现 (无参选板路径确认)")
            elif "AskUserQuestion" not in p["init_tools"]:
                stems = vault_board_stems()
                listed = [s for s in stems if s in p["last_text"]]
                if len(listed) >= 2 and (
                    "？" in p["last_text"]
                    or "?" in p["last_text"]
                    or "哪" in p["last_text"]
                ):
                    print(
                        f"[{log_id}]    ✓ 无参选板询问出现 — ⚠ 文本降级 (headless 工具面无 AskUserQuestion, "
                        f"枚举 {len(listed)}/{len(stems)} 块板并发问; AskUserQuestion UI 须交互环境实测)"
                    )
                else:
                    print(
                        f"{RED}[{log_id}]    ✗ 无 AskUserQuestion 工具且末轮文本未构成选板询问{RESET}"
                    )
                    ok = False
            else:
                print(
                    f"{RED}[{log_id}]    ✗ AskUserQuestion 在工具面却未被使用 (skill 步骤漂移, 登记){RESET}"
                )
                ok = False
        ok &= check_positive_diff_outputs_only(log_id)
        b, a = manifest_pair(log_id, "-outputs")
        if b.exists() and a.exists():
            added = set(a.read_text(encoding="utf-8").splitlines()) - set(
                b.read_text(encoding="utf-8").splitlines()
            )
            print(f"[{log_id}] J2 outputs/ 新增清单: {sorted(added) or '无'}")
            if want_verify_pass and not added:
                print(
                    f"{RED}[{log_id}] J2 ✗ 全链正例必须产出 outputs/ 新增 (零新增 = 没跑完写侧){RESET}"
                )
                ok = False
    return ok, p["session_ids"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--positive", action="append", default=[], help="按正例判定的 ID (可多次)"
    )
    ap.add_argument("--positive-skill", default="board-recap")
    ap.add_argument(
        "--ask-ids", default="B2", help="额外要求选板询问的正例 ID (逗号分隔)"
    )
    ap.add_argument(
        "--verify-pass-ids", default="B1", help="要求 VERIFY PASS 的正例 ID (逗号分隔)"
    )
    args = ap.parse_args()

    tsv = HERE / "negatives.tsv"
    neg_rows = (
        [
            ln.split("\t", 1)
            for ln in tsv.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        if tsv.exists()
        else []
    )
    neg_ids = [r[0] for r in neg_rows]
    neg_utts = {r[0]: (r[1] if len(r) > 1 else None) for r in neg_rows}
    if not neg_ids and not args.positive:
        print("缺 negatives.tsv 且未指定 --positive")
        return 2

    ask_ids = {x.strip() for x in args.ask_ids.split(",")}
    vp_ids = {x.strip() for x in args.verify_pass_ids.split(",")}
    all_ok = True
    seen_sessions: dict[str, str] = {}
    for nid in neg_ids:
        ok, sids = judge_one(
            nid, None, False, False, expect_utterance=neg_utts.get(nid)
        )
        all_ok &= ok
        for s in sids:
            if s in seen_sessions:
                print(
                    f"{RED}[{nid}] J0 ✗ session_id 与 {seen_sessions[s]} 复用 (同一日志冒充多条!){RESET}"
                )
                all_ok = False
            seen_sessions[s] = nid
    for pid in args.positive:
        ok, sids = judge_one(pid, args.positive_skill, pid in ask_ids, pid in vp_ids)
        all_ok &= ok
        for s in sids:
            if s in seen_sessions:
                print(f"{RED}[{pid}] J0 ✗ session_id 与 {seen_sessions[s]} 复用{RESET}")
                all_ok = False
            seen_sessions[s] = pid

    n = len(neg_ids) + len(args.positive)
    if all_ok:
        print(
            f"{GREEN}PASS — {n} 条全部通过 (负例 {len(neg_ids)} / 正例 {len(args.positive)}; 会话跨日志零复用){RESET}"
        )
        return 0
    print(
        f"{RED}FAIL — 存在未通过条目 (误触发只登记不改 skill, 登记簿见矩阵文档 §五){RESET}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
