#!/usr/bin/env python3
"""每日复习推送编排 runner (DAILY-REVIEW-PUSH-2026-07-29, 终审 A4/A7 硬化版)。

顺序铁律: md/json 先落盘(保底) → 窗口内 Bark → 失败 osascript 兜底。
壳层 daily-review-push.sh 只负责 mkdir 锁 + 固定解释器; 业务全在此处
(可 --now 注入时间跑 12 场景验收矩阵)。

终审修正落点:
  A4: 时间门 9:05 ≤ 本地时间 < 21:00 (RunAtLoad 早触发只生成不推;
      唤醒补跑窗口内补推; 过窗只落盘) · state JSON 原子写 (os.replace)
      · last_push_accepted_date 命名 (HTTP 成功仅证明服务端接受)
  A7: payload 持久化 今日复习.json (生成成功推送失败 → 补跑只补推送)
      · osascript 走 argv (板名注入免疫) · 损坏 state 隔离重建不炸
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, time as dtime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import send_bark  # noqa: E402

REPO = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
# VAULT-SYNC (2026-08-02): 默认值仅作兜底 — 生产链由 wrapper 从 .env
# ACTIVE_VAULT 解析后经 --vault 传入, 与后端同源 (换 vault 只改 .env 一处)
VAULT = REPO / "canvas-vault"
STATE = REPO / "backups" / "daily-review.state.json"
LOG = REPO / "backups" / "daily-review.log"

PUSH_WINDOW = (dtime(9, 5), dtime(21, 0))

APPLESCRIPT = (
    "on run argv\n"
    "    display notification (item 2 of argv) with title (item 1 of argv)\n"
    "end run\n"
)


def _now(arg: str | None) -> datetime:
    if arg:
        dt = datetime.fromisoformat(arg.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.astimezone()
    return datetime.now(timezone.utc)


def load_state() -> dict:
    if not STATE.exists():
        return {"schema_version": 1, "board_last_recommended": {}}
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
        st.setdefault("board_last_recommended", {})
        return st
    except (json.JSONDecodeError, OSError):
        quarantine = STATE.with_name(
            STATE.name + ".corrupt-" + datetime.now().strftime("%Y%m%dT%H%M%S"))
        try:
            os.replace(STATE, quarantine)
        except OSError:
            pass
        print(f"[runner] state 损坏, 已隔离到 {quarantine.name}, 重建", file=sys.stderr)
        return {"schema_version": 1, "board_last_recommended": {}}


def save_state(st: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE)


def log_line(msg: str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%F %T")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {msg}\n")


def _nodes_max_mtime(vault: Path) -> float:
    """节点池最新改动时间 (CARD-A3 缓存失效判据)。

    文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓
    增删改名 (不留文件 mtime); 误报代价只是一次幂等重扫。保 mtime 的
    还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内。
    """
    pool = vault / "节点"
    latest = 0.0
    for p in pool.glob("*.md"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except OSError:
            continue  # 迭代间隙被删: 殿后的目录 stat 捕获该变动
    try:
        # 目录 stat 殿后取样 — 迭代期间发生的删除也已反映在目录 mtime 里
        latest = max(latest, pool.stat().st_mtime)
    except OSError:
        return 0.0  # 节点池不存在: 不因 mtime 失效, 保持旧缓存语义
    return latest


def ensure_payload(st: dict, now: datetime, today: str) -> tuple[dict | None, str]:
    """当日 payload: 没有才生成 (生成过则复用 — 补跑只补推送)。

    CARD-A3 (BATCH-2026-08-24-复习闭环): 复用多两道门 — ①节点池比 payload
    新 (quiz 写侧刚更新 fsrs_due / 新增重学卡) 则同日重扫; ②当前时间越过
    生成时记录的最早未来到期点 (next_due_utc) 也重扫 (Codex-A3 BLOCKER:
    09:59 落 fsrs_due=10:09 → 10:05 重扫时未到期 → 11:05 若只看 mtime 会
    整天 cached, 当天到期卡丢失 — 卡片 :89 警告的缺陷位移)。push 去重
    不在此处: last_push_accepted_date 天然保证同日只推一次。
    """
    payload_path = VAULT / "outputs" / "今日复习.json"
    first_gen_today = st.get("last_generate_date") != today
    if not first_gen_today and payload_path.exists():
        try:
            raw = payload_path.read_text(encoding="utf-8")
            # sha 校验 (Code-Review L3): 外部改动/半写的 payload 不复用, 重新生成
            if hashlib.sha256(raw.encode("utf-8")).hexdigest() == st.get("payload_sha256"):
                now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                due_crossed = bool(st.get("next_due_utc")) and st["next_due_utc"] <= now_z
                if not due_crossed and _nodes_max_mtime(VAULT) <= payload_path.stat().st_mtime:
                    return json.loads(raw), "cached"
        except (json.JSONDecodeError, OSError):
            pass  # 落盘 payload 损坏 → 重新生成

    import daily_review_pick as picker

    scan_started = time.time()
    payload, ranked = picker.build_payload(
        VAULT, now, st["board_last_recommended"], picker.load_decay(VAULT))
    out = VAULT / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    picker.atomic_write(out / "今日复习.md", picker.render_md(payload, ranked))
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    picker.atomic_write(payload_path, raw)
    # mtime 门基准回拨到扫描起点: 扫描-落盘窗口内落地的写侧更新, 其 mtime
    # 必然 > 基准, 下一轮触发重扫捞回 (否则该更新当天静默丢失, 无日志可查)
    os.utime(payload_path, (scan_started, scan_started))

    st["last_generate_date"] = today
    st["payload_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    # 最早未来到期点: ranked 是全量榜 (payload.top_boards 才截断), 每行
    # next_due 已是板内未来最小值; upcoming 按 next_due 升序, [0] 即全局
    # 最小, [:3] 截断不丢它。未归板节点不参与推荐, 其到期转场不改变输出。
    nexts = [r["next_due"] for r in ranked if r.get("next_due")]
    if payload.get("upcoming"):
        nexts.append(payload["upcoming"][0]["next_due"])
    st["next_due_utc"] = min(nexts, default="")
    if ranked and first_gen_today:
        # CARD-A3: 重扫路径不写 — tie-break 的「上次被推荐日期」是天级轮转
        # 语义, 重扫换榜也补写会把第二个板标成「今天推荐过」, 污染后续排序
        st["board_last_recommended"][ranked[0]["board"]] = today
    save_state(st)
    return payload, "new"


def osascript_fallback(noti: dict) -> bool:
    try:
        r = subprocess.run(
            ["/usr/bin/osascript", "-", noti["title"], noti["body"]],
            input=APPLESCRIPT, text=True, capture_output=True, timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main() -> int:
    global VAULT
    ap = argparse.ArgumentParser(description="每日复习推送编排")
    ap.add_argument("--now", help="ISO 时间覆盖 (12 场景验收矩阵用)")
    ap.add_argument("--vault", help="活 vault 路径 (wrapper 从 .env ACTIVE_VAULT 解析传入; 缺省回退 canvas-vault)")
    args = ap.parse_args()

    if args.vault:
        VAULT = Path(args.vault)

    now = _now(args.now)
    local = now.astimezone()
    today = local.date().isoformat()
    st = load_state()

    try:
        payload, gen = ensure_payload(st, now, today)
    except Exception as e:  # 生成失败 = 无保底, 唯一的非 0 退出
        log_line(f"generate:FAILED err={type(e).__name__}:{str(e)[:120]}")
        print(f"[runner] 生成失败: {e}", file=sys.stderr)
        return 1

    noti = (payload or {}).get("notification")
    push, fallback = "-", "-"
    if not noti:
        push = "skip-empty"  # 无板可推 (全占位/空 vault): md 已如实落盘
    elif st.get("last_push_accepted_date") == today:
        push = "skip-done"
    elif not (PUSH_WINDOW[0] <= local.time() < PUSH_WINDOW[1]):
        push = "skip-window"  # RunAtLoad 早触发 / 21:00 后唤醒: 只落盘
    else:
        rc = send_bark.send(noti)
        if rc == 0:
            st["last_push_accepted_date"] = today
            st["last_result"], st["last_error"] = "pushed", ""
            save_state(st)
            push = "accepted"
        else:
            push = "skip-nokey" if rc == 2 else "failed"
            if rc != 2:
                st["last_result"] = "generated_push_failed"
                st["last_error"] = "bark-send"
            # 本地兜底每日一次 (Code-Review L1 去重门); 无 key 也提醒一条
            # (Code-Review H1: key 配好前不能一切静默)
            if st.get("last_local_notify_date") != today:
                local_noti = noti if rc != 2 else {
                    "title": "📚 今日复习已生成",
                    "body": noti["body"] + "（Bark 未配置，仅本地提醒）",
                }
                fallback = "ok" if osascript_fallback(local_noti) else "fail"
                if fallback == "ok":
                    st["last_local_notify_date"] = today
            save_state(st)

    log_line(f"generate:{gen} push:{push} fallback:{fallback}")
    print(f"[runner] generate:{gen} push:{push} fallback:{fallback}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
