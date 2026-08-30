#!/usr/bin/env python3
"""每日复习选板 (DAILY-REVIEW-PUSH-2026-07-29, ChatGPT 终审 A3 修正版)。

扫 vault 节点/*.md frontmatter → 衰减 Beta 读时时效 pick → 板级 min 聚合
→ outputs/今日复习.md (人读) + outputs/今日复习.json (推送 payload, 终审 A7:
stdout 是瞬时数据, 推送失败补跑必须有持久化 payload)。

schema v3 (CARD-A2, BATCH-2026-08-24-复习闭环): 本 JSON 是全系统到期口径
唯一裁判 — Dashboard.md 直接 dv.io.load 消费 due_nodes 明细 + ineligible
分桶 (占位符待剖析积压单独成桶), 不再独立重算。v2→v3 纯加性, 推送链
(daily_review_run/send_bark 只读 notification) 被动兼容。

三态兼容 (live 实测 18 节点: 新字段 1 / 仅旧 10 / 无字段 7):
  mastery_a/b (+last_examined) → effective() 闲置折扣后 pick
  仅 mastery_score             → from_legacy() 均值继承低置信
  无字段                       → 先验 Beta(0.9,2.1), 从未考 σ 大自动优先

终审 A3 三修正:
  1. eligibility 与 start-exam-board 同规则 — 含「你的 1-2 句精准定义」
     占位符的未剖析节点跳过 (否则推荐无法出题的节点到手机)
  2. 输出命令绑定 node <top_node> — start-exam-board 自己重选点时不含
     闲置折扣, 不绑定会出现「通知说考 A 实际考 B」
  3. min() 并列 tie-break: 板上次被推荐日期(久者先) → 最老 last_examined
     → 板名 (防启动期先验板按扫描顺序永久霸榜)

依赖: 仅 stdlib + vault 内 decay_beta.py (launchd 环境无 pip 包可假设)。

═══════════════════════════════════════════════════════════════════════
CARD-G3-6a 桶位与 why_due (BATCH-2026-08-29-第六批) — 加性扩展语义裁定
═══════════════════════════════════════════════════════════════════════
schema_version 仍为 3。落地前先书面裁定, 审查按本节判 (S1/S2/S3)。

S1 桶位划分律与优先级 (无重叠 · 无遗漏)
  划分域 = 已归板 (source_board 可解析) 且未被 ineligible 拦下的节点 —
  与 stats.due_nodes + stats.future_nodes 的口径域完全同一。未归板节点
  不进桶 (已由 unassigned_nodes 点名); 占位符 / 测试文件名 / 损坏节点不
  进桶 (已由 ineligible 三桶点名) — 不重复点名, 也不静默吞。
  级联优先级 (自上而下先匹配先归, 每个域内节点恰好落一桶):
    1 new            due_reason=="new" — 无 fsrs_due 且非 fail-open 的真新卡
    2 learning_queue 已到期 且 fsrs_state ∈ {0, 1, 3}
    3 due_now        其余已到期 (含 fsrs_state==2 Review 与 malformed fail-open)
    4 due_today      未到期 且 fsrs_due 落在与 now 同一个 Asia/Shanghai 日
    5 future         其余未到期
  完备性: 域内每节点的 due_now 布尔恒二分 — True 侧被 1/2/3 穷尽 (3 = 1
  的否定 ∧ 2 的否定), False 侧被 4/5 穷尽 (同上海日与否)。互斥由级联保证。
  合计恒等 (构造保证 + 契约测试):
    |new| + |learning_queue| + |due_now| == stats.due_nodes
    |due_today| + |future|              == stats.future_nodes
  fsrs_state 取值裁定 (勘探实测: live 14 节点仅 1 个带该字段, 值为 1):
  py-fsrs v6 State 枚举无 New — Learning=1 / Review=2 / Relearning=3;
  历史哨兵 0 已由 fsrs_bridge.py:106-117 在读侧归一为 Learning (CARD-C3
  裁定), 本文件同口径把 0 并入 learning_queue, 与评分侧「刚开始学」语义
  一致 (卡面建议为 {1,3}; 本裁定是其超集, 只影响存量 0 值节点, live 实
  测为 0 个)。非整数 / 无法解析的 fsrs_state 按「无状态」落 due_now —
  未知值不吞节点, 只是不享受分层优待。

S2 加标签不搬移 (R2 高风险面 — 本卡明令禁止搬移)
  新桶只以字段 / 标签表达: due_nodes 行尾加性追加 bucket + why_due, 顶层
  加性追加 buckets 分组。节点仍全部留在 due_nodes 内, stats.due_nodes 口
  径分毫不动。理由: review_overview.py 把 stats.due_nodes 当权威计数并用
  due_nodes group-by 派生板级到期数, Dashboard.md:57-72 直接 dv.io.load
  消费 due_nodes 明细 — 任何「把 learning/new 搬出 due_nodes」的做法都会
  同时改动这两个消费方的数字, 属破坏性变更而非加性扩展。
  加性上界同样是契约: 顶层只加 buckets 一个键; boards rollup 行 / ineligible
  / notification / top_boards / upcoming / stats 一个字段不加不改。

S3 why_due 取值枚举与生成规则
  why_due 是恒非空人话串 (桶位是机器枚举, why_due 是给人看的那一句), 由
  下列 6 个确定性模板生成, 槽位只填投影内已有的真实数据 — fsrs_due /
  fsrs_state / last_examined 派生的闲置天数 / Asia/Shanghai 本地时刻,
  一律不虚构、不估算:
    new            "新卡未排期，视同即刻到期 · <闲置片段>"
    learning_queue "<学习中|重学中> · <到期片段> · <闲置片段>"
    due_now 排期    "到期待复习 · <到期片段> · <闲置片段>"
    due_now 脏日期  "到期待复习 · 到期时间无法解析(<原值安全化摘录>)，保守视同到期 · <闲置片段>"
    due_today      "今天 HH:MM 到期（尚未到点）"
    future         "<明天|N 天后> M月D日 HH:MM 到期"
  片段规则: 闲置片段 = "从未考察" | "已闲置 N 天" (N 取整, 源自
  last_examined); 到期片段 = "已逾期 N 天（M月D日到期）" | "今天 HH:MM
  到期" | 脏日期说明。
  原值安全化摘录 (Codex round-1 MEDIUM): 脏 fsrs_due 原值先按 ISO-8601
  合法字符白名单过滤 (非白名单字符逐个替换为 "?") 再截 40 字 —— why_due
  会被拼进 outputs/今日复习.md 并可能被下游 HTML 渲染, 原样透传等于把
  frontmatter 里的任意串接进渲染面。摘录保留足以认出原值的形状, 但不再是
  逐字原值, 本行即其书面定义。
  极值兜底 (2 条, Codex round-1 MEDIUM 显式纳入规格): 当 fsrs_due 或 now
  的时刻在时区换算中不可表示 (年份极值 astimezone 溢出) 时, 六模板的时间
  槽位无从生成, 改用
    到期片段兜底  "到期时刻超出可显示范围"
    future 兜底   "到期时刻超出可显示范围，按未来排期处理"
  —— 如实说"算不出", 不猜、不静默丢节点。同一情形下判桶的"今天"基准退化
  为 UTC 日 (见 _today_sh)。
  非到期两桶 (due_today/future) 的 why_due 读作「何时到期」— 同一字段名
  承载「为什么今天不用做」的诚实说明, 绝不给未到期节点编造到期理由。
  时区: 人话一律 Asia/Shanghai (与 CARD-D1 总览页同一口径); 落盘的
  fsrs_due / next_due 仍是 UTC-Z 原样, 不动。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: 与 start-exam-board SKILL Step 3 完全同一条占位符规则 (终审 A3)
PLACEHOLDER = "你的 1-2 句精准定义"

#: 生产数据污染标记 (对齐 memory-health.sh 批次1'⑥ 审计清单) — 不推测试节点。
#: ⚠ 只匹配文件名: 真实节点 frontmatter 可能引用测试会话 id (live 实测
#: Fundamentals 的 error_candidates 含 m3-e2e-sessionend-test, 按全文匹配会误杀)
TEST_MARKERS = ("TestConcept", "UAT-2.5", "m3-e2e")

#: [Decision-FSRS-2] WHEN/WHAT 分工 (FSRS-V2-2026-07-30):
#: FSRS 管 WHEN — fsrs_due 决定今天谁到期, 无字段 = New 卡即刻到期;
#: 衰减 Beta 管 WHAT — 到期集合内按 pick=μ−σ 排序。
#: 本文件保持纯 stdlib: 只做 UTC 定长字符串日期比较, 不 import fsrs。

#: Bark 通知标题上限 (方案规范: ≤20 全角字符)
TITLE_LIMIT = 20

#: CARD-G3-6a 人话时区: 统一 Asia/Shanghai (与 CARD-D1 总览页同一口径 —
#: launchd/容器跑 UTC 时 astimezone() 的"本地日"会跨午夜误判)。缺 tzdata
#: 时退化为固定 +8 (Asia/Shanghai 自 1991 年起无夏令时, 语义等价)。
try:
    from zoneinfo import ZoneInfo

    _TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
except Exception:  # noqa: BLE001 — ZoneInfoNotFoundError / ImportError 同一退化
    _TZ_SHANGHAI = timezone(timedelta(hours=8))

#: CARD-G3-6a S1 五桶 — 级联优先级顺序即本元组顺序 (落盘 buckets 键序亦同)
BUCKET_NEW = "new"
BUCKET_LEARNING = "learning_queue"
BUCKET_DUE_NOW = "due_now"
BUCKET_DUE_TODAY = "due_today"
BUCKET_FUTURE = "future"
BUCKET_ORDER = (BUCKET_NEW, BUCKET_LEARNING, BUCKET_DUE_NOW, BUCKET_DUE_TODAY, BUCKET_FUTURE)

#: 人读标签 (仅 render_md 用; JSON 落盘恒用英文键)
BUCKET_CN = {
    BUCKET_NEW: "新卡",
    BUCKET_LEARNING: "学习中",
    BUCKET_DUE_NOW: "到期待复习",
    BUCKET_DUE_TODAY: "今天晚些到期",
    BUCKET_FUTURE: "未来排期",
}

#: S1 fsrs_state 裁定: py-fsrs v6 Learning=1 / Relearning=3; 历史哨兵 0 由
#: fsrs_bridge.py 读侧归一为 Learning (CARD-C3), 本文件同口径并入。
LEARNING_STATES = (0, 1, 3)

#: S3 原值安全化白名单 (Codex round-1 MEDIUM): ISO-8601 时间戳的合法字符集。
#: 脏 fsrs_due 原值进 why_due 前逐字符过滤 —— why_due 会拼进人读 md 并可能
#: 被下游 HTML 渲染, 原样透传等于把 frontmatter 任意串接进渲染面。
_DUE_RAW_UNSAFE = re.compile(r"[^0-9A-Za-z:+. -]")


def _aware(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _fm_num(fm: str, key: str):
    # 容负号 (Code-Review L5): mastery_a: -3 应进 corrupt 分支而非静默当无字段
    m = re.search(rf'^{key}:\s*"?(-?[0-9]*\.?[0-9]+)"?\s*$', fm, re.M)
    return float(m.group(1)) if m else None


def _fm_str(fm: str, key: str):
    m = re.search(rf'^{key}:\s*"?([^"\n]+?)"?\s*$', fm, re.M)
    return m.group(1).strip() if m else None


def _board_name(raw: str | None):
    """source_board 归一化 → 板名 (live 数据实为 wikilink '[[原白板/X]]')。"""
    if not raw:
        return None
    name = raw.strip()
    if name.startswith("[[") and name.endswith("]]"):
        name = name[2:-2]
    name = name.split("|")[0]                 # [[path|alias]] 取 path
    name = name.rsplit("/", 1)[-1].strip()    # 原白板/X → X
    return name or None


def _fm_int(fm: str, key: str):
    """整数型 frontmatter (fsrs_state)。非整数 / 溢出 / 缺失一律 None = 无状态。

    S1: 未知状态不吞节点 — 只是不享受 learning_queue 分层优待, 仍按到期落
    due_now。inf.is_integer() 为 False, 巨值串因此也走 None 分支。
    """
    v = _fm_num(fm, key)
    if v is None or not float(v).is_integer():
        return None
    return int(v)


def _sh_local(ts: str):
    """UTC-Z 定长时间串 → Asia/Shanghai aware datetime; 不可表示时 None。

    ts 已由 scan_nodes 的 fsrs_due 门禁保证形态 (非规范值早被 fail-open
    清空)。年份极值 (9999-12-31T23:59:59Z + 8h) astimezone 会 OverflowError
    — 人话层绝不崩全轮, 交由调用方走兜底文案 / 归 future。
    """
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).astimezone(_TZ_SHANGHAI)
    except (ValueError, OverflowError, OSError):
        return None


def _today_sh(now: datetime):
    """判桶的「今天」基准 (Asia/Shanghai 日)。

    极值 now (年份边界) 换算会 OverflowError —— 此处退化为 UTC 日而非崩掉
    整轮 (S3 极值兜底同款诚实降级)。注意: HEAD 起 build_payload 的
    payload["date"] 对同类极值本就会抛 OverflowError, main() 已在入口显式
    拒绝这类 --now; 本兜底是给直接调用 build_payload 的路径留的防线。

    Codex round-2 MEDIUM: UTC 回退本身也可能溢出 (如 year=1 且 offset=+14,
    换算要减 14 小时 → 年份下溢), 故最后再退一档到 now 自身表示的日期 ——
    该值恒可得, 三档保证本函数永不抛。
    """
    for tz in (_TZ_SHANGHAI, timezone.utc):
        try:
            return now.astimezone(tz).date()
        except (OverflowError, OSError):
            continue
    return now.date()


def _safe_raw(raw: str) -> str:
    """S3 原值安全化摘录: 非白名单字符 → "?", 再截 40 字。"""
    return _DUE_RAW_UNSAFE.sub("?", raw)[:40]


def _idle_cn(idle_days) -> str:
    """S3 闲置片段: 源自 last_examined, 无则如实说从未考察。"""
    return "从未考察" if idle_days is None else f"已闲置 {int(idle_days)} 天"


def _overdue_cn(n: dict, today_sh) -> str:
    """S3 到期片段 (仅已到期节点)。脏日期如实点名原值摘录, 不装能解析。"""
    if n["due_fail_open"]:
        return f"到期时间无法解析({_safe_raw(n['fsrs_due_raw'])})，保守视同到期"
    due_sh = _sh_local(n["fsrs_due"])
    if due_sh is None:
        return "到期时刻超出可显示范围"
    delta = (due_sh.date() - today_sh).days
    if delta < 0:
        return f"已逾期 {-delta} 天（{due_sh.month}月{due_sh.day}日到期）"
    return f"今天 {due_sh:%H:%M} 到期"


def assign_bucket(n: dict, now: datetime) -> tuple[str, str]:
    """S1 级联判桶 + S3 模板生成 → (bucket, why_due)。

    调用前提: n 已归板 (划分域)。级联顺序即 BUCKET_ORDER — 先匹配先归,
    因此每个域内节点恰好落一桶 (互斥), 且 due_now 布尔二分被五桶穷尽
    (完备)。why_due 恒非空。
    """
    today_sh = _today_sh(now)
    idle = _idle_cn(n["idle_days"])
    if n["due_now"]:
        if not n["fsrs_due"] and not n["due_fail_open"]:
            return BUCKET_NEW, f"新卡未排期，视同即刻到期 · {idle}"
        if n["fsrs_state"] in LEARNING_STATES:
            phase = "重学中" if n["fsrs_state"] == 3 else "学习中"
            return BUCKET_LEARNING, f"{phase} · {_overdue_cn(n, today_sh)} · {idle}"
        return BUCKET_DUE_NOW, f"到期待复习 · {_overdue_cn(n, today_sh)} · {idle}"
    # 未到期两桶: fsrs_due 恒为规范非空串 (空串必定 due_now)
    due_sh = _sh_local(n["fsrs_due"])
    if due_sh is None:
        # 不可表示 = 年份极值远期, 定义上不可能是"今天" → future 兜底
        return BUCKET_FUTURE, "到期时刻超出可显示范围，按未来排期处理"
    delta = (due_sh.date() - today_sh).days
    if delta == 0:
        return BUCKET_DUE_TODAY, f"今天 {due_sh:%H:%M} 到期（尚未到点）"
    when = "明天" if delta == 1 else f"{delta} 天后"
    return BUCKET_FUTURE, f"{when} {due_sh.month}月{due_sh.day}日 {due_sh:%H:%M} 到期"


def scan_nodes(vault: Path, now: datetime, decay):
    """扫描 节点/ 池 → (nodes, stats, ineligible, placeholder_boards)。
    逐节点容错: 单个脏节点不崩全轮。

    ineligible 分桶 (schema v3, CARD-A2): 被跳过的节点按原因点名, 不再只有
    计数 — Dashboard 消费 placeholder 桶显示"待剖析积压"。
    placeholder_boards (CARD-D1 P1): {板名: 占位符数} 板级归属, 供 boards
    rollup; 无 source_board 的占位符不入 (只在扁平列表)。
    """
    stats = {"new": 0, "legacy": 0, "none": 0, "ineligible": 0, "test_excluded": 0, "corrupt": 0}
    ineligible = {"placeholder": [], "test_excluded": [], "corrupt": []}
    placeholder_boards: dict[str, int] = {}  # CARD-D1 P1: 占位符板级归属
    now_z = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    nodes = []
    for path in sorted((vault / "节点").glob("*.md")):
        stem = path.stem
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] 读取失败跳过 {stem}: {e}", file=sys.stderr)
            continue
        if any(mk in stem for mk in TEST_MARKERS):
            stats["test_excluded"] += 1
            ineligible["test_excluded"].append(stem)
            continue
        m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
        fm, body = (m.group(1), m.group(2)) if m else ("", text)
        if PLACEHOLDER in body:
            stats["ineligible"] += 1
            ineligible["placeholder"].append(stem)
            # CARD-D1 P1: 占位符按 source_board 归板 (fm 已解析零额外 IO);
            # 无 source_board 的占位符只留扁平列表, 不虚构归属
            ph_board = _board_name(_fm_str(fm, "source_board"))
            if ph_board:
                placeholder_boards[ph_board] = placeholder_boards.get(ph_board, 0) + 1
            continue

        a_raw, b_raw = _fm_num(fm, "mastery_a"), _fm_num(fm, "mastery_b")
        legacy = next(
            (v for k in ("mastery_score", "mastery", "mastery_level")
             if (v := _fm_num(fm, k)) is not None),
            None,
        )
        if a_raw is not None and b_raw is not None:
            a, b, state = a_raw, b_raw, "new"
        elif legacy is not None:
            a, b = decay.from_legacy(legacy)
            state = "legacy"
        else:
            a, b, state = decay.PRIOR_A, decay.PRIOR_B, "none"
        stats[state] += 1

        last_exam = _fm_str(fm, "last_examined")
        idle_days = None
        if last_exam:
            try:
                idle_days = max(0.0, (now - _aware(last_exam)).total_seconds() / 86400.0)
            except ValueError:
                print(f"[pick] last_examined 无法解析, 按从未考: {stem}", file=sys.stderr)
                last_exam = None
        try:
            # pick_score 也在 try 内 (Code-Review M2): 除零/溢出同属脏数据
            a_eff, b_eff = decay.effective(a, b, idle_days or 0.0)
            pick = decay.pick_score(a_eff, b_eff)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] Beta 参数损坏跳过 {stem}: {e}", file=sys.stderr)
            continue
        if not math.isfinite(pick):
            # Codex-A2 H1: 巨值 mastery 让 pick 静默算成 NaN/inf 不抛异常 —
            # v3 起每个到期节点的 pick 都进 JSON, 单个 NaN = 全文件非法。
            # 与其余脏数据同语义: 进 corrupt 桶, 不崩全轮。
            stats["corrupt"] += 1
            ineligible["corrupt"].append(stem)
            print(f"[pick] Beta 参数溢出跳过 {stem}: pick={pick}", file=sys.stderr)
            continue

        fsrs_due = _fm_str(fm, "fsrs_due") or ""
        fsrs_due_raw = fsrs_due   # CARD-G3-6a: fail-open 清空前留底, 供 why_due 点名
        due_fail_open = False
        # Code-Review M2: Obsidian Properties 面板可能把 datetime 重新序列化成
        # 带偏移格式, 词法比较会反向误判「永不到期」。非规范格式 fail-open
        # 视同到期 (与 New 语义一致), 不静默消失。
        # Codex-A2 M2: 形状正确但日历非法 (如月份 13) 词法比较会误判成未来,
        # 同样 fail-open — 脏值策略统一为一条。
        if fsrs_due:
            due_ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fsrs_due))
            if due_ok:
                try:
                    datetime.strptime(fsrs_due, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    due_ok = False
            if not due_ok:
                print(f"[pick] fsrs_due 非规范格式, 视同到期: {stem} ({fsrs_due})", file=sys.stderr)
                fsrs_due = ""
                due_fail_open = True
        nodes.append({
            "node": stem,
            "board": _board_name(_fm_str(fm, "source_board")),
            "state": state,
            "pick": pick,
            "idle_days": idle_days,          # None = 从未考
            "last_examined": last_exam or "",
            "fsrs_due": fsrs_due,
            "due_now": (not fsrs_due) or fsrs_due <= now_z,  # 无字段 = New 即刻到期
            "due_fail_open": due_fail_open,
            "difficulty": _fm_str(fm, "fsrs_difficulty") or "",
            # CARD-G3-6a 内部字段 (不落盘): S1 判桶 / S3 人话的输入
            "fsrs_due_raw": fsrs_due_raw,
            "fsrs_state": _fm_int(fm, "fsrs_state"),
        })
    return nodes, stats, ineligible, placeholder_boards


def rank_boards(nodes, board_last_recommended: dict):
    """板级聚合: priority = min(pick), 终审 A3 tie-break。"""
    boards: dict[str, list] = {}
    unassigned = []
    for n in nodes:
        if not n["board"]:
            unassigned.append(n["node"])
            continue
        boards.setdefault(n["board"], []).append(n)

    ranked, upcoming = [], []
    for board, members in boards.items():
        due = [n for n in members if n["due_now"]]
        if not due:
            # WHEN: 全员未到期 → 不进推荐榜, 记最近的未来到期 (F1 放假语义)
            nxt = min(members, key=lambda n: n["fsrs_due"])
            upcoming.append({"board": board, "next_due": nxt["fsrs_due"], "node": nxt["node"]})
            continue
        top = min(due, key=lambda n: n["pick"])   # WHAT: 到期集合内衰减 Beta 排序
        ranked.append({
            "board": board,
            "top_node": top["node"],
            "priority": round(top["pick"], 4),
            "pending": len(due),                   # 到期即待复习 (Decision-FSRS-2)
            "idle_days": (None if top["idle_days"] is None else int(top["idle_days"])),
            "difficulty": top["difficulty"],
            "next_due": min((n["fsrs_due"] for n in members if not n["due_now"]), default=""),
            "_tie": (
                round(top["pick"], 8),
                board_last_recommended.get(board, ""),   # 空串 = 从未被推荐, 排最前
                min(n["last_examined"] for n in due),    # 空串 = 有从未考节点, 排最前
                board,
            ),
        })
    ranked.sort(key=lambda r: r["_tie"])
    for r in ranked:
        del r["_tie"]
    upcoming.sort(key=lambda u: u["next_due"])
    return ranked, upcoming, unassigned


def _title(board: str) -> str:
    prefix = "📚 今日复习 · "
    room = TITLE_LIMIT - len(prefix)
    return prefix + (board if len(board) <= room else board[: room - 1] + "…")


def _body(top: dict) -> str:
    idle = "从未考察" if top["idle_days"] is None else f"已闲置 {top['idle_days']} 天"
    if top["pending"] >= 2:
        return f"{top['top_node']} 等 {top['pending']} 节点待巩固 · {idle}"
    return f"{top['top_node']} 待巩固 · {idle}"


def build_payload(vault: Path, now: datetime, board_last_recommended: dict, decay):
    nodes, stats, ineligible, placeholder_boards = scan_nodes(vault, now, decay)
    ranked, upcoming, unassigned = rank_boards(nodes, board_last_recommended)
    stats["unassigned"] = len(unassigned)
    # CARD-G3-6a S1: 级联判桶 + why_due 一次算好, due_nodes 行与 buckets 分组
    # 同源引用同一对值 (禁两处各算一遍 → 禁口径分裂)。划分域 = 已归板。
    for n in nodes:
        if n["board"]:
            n["bucket"], n["why_due"] = assign_bucket(n, now)
    # v3 (CARD-A2): due_nodes 明细与 stats 数字同源派生 — 自洽靠构造保证,
    # 本投影是全系统到期口径唯一裁判 (Dashboard 只消费不重算)
    due_rows = [
        {
            "node": n["node"],
            "board": n["board"],
            "state": n["state"],
            "pick": round(n["pick"], 4),
            "fsrs_due": n["fsrs_due"],           # 空串 = 新卡即刻到期
            # Codex-A2 M1: 消费方须能区分真新卡与 fail-open 的脏日期卡
            "due_reason": ("malformed" if n["due_fail_open"]
                           else ("scheduled" if n["fsrs_due"] else "new")),
            "last_examined": n["last_examined"],
            "difficulty": n["difficulty"],
            # CARD-G3-6a 加性 (S2 加标签不搬移): 行仍在 due_nodes 内, 只多两
            # 个字段 — 到期三桶之一 + 人话理由。旧字段一个不改。
            "bucket": n["bucket"],
            "why_due": n["why_due"],
        }
        for n in nodes if n["board"] and n["due_now"]
    ]
    stats["due_nodes"] = len(due_rows)
    stats["future_nodes"] = sum(1 for n in nodes if n["board"] and not n["due_now"])
    # CARD-D1 P1 (BATCH-2026-08-27): 顶层加性 boards 全量 rollup — 补
    # top_boards/upcoming 各截 [:3] 与 placeholder 板级无归属的结构性缺口。
    # schema_version 保持 3; ineligible.placeholder 扁平列表 / notification /
    # top_boards / upcoming 零改动 (A2 冻结)。due 计数与 due_rows 同源分组,
    # 合计恒等 stats.due_nodes。
    members_by_board: dict[str, list] = {}
    for n in nodes:
        if n["board"]:
            members_by_board.setdefault(n["board"], []).append(n)
    boards_rollup = []
    for board in sorted(set(members_by_board) | set(placeholder_boards)):
        members = members_by_board.get(board, [])
        due = [n for n in members if n["due_now"]]
        future = [n for n in members if not n["due_now"]]
        boards_rollup.append({
            "board": board,
            "due": len(due),
            # 三分语义与 due_rows.due_reason 同一判据: new=真新卡 /
            # scheduled=已排期 / malformed=due-new-scheduled 隐含
            "due_new": sum(1 for n in due if not n["fsrs_due"] and not n["due_fail_open"]),
            "due_scheduled": sum(1 for n in due if n["fsrs_due"]),
            "future": len(future),
            "next_due": min((n["fsrs_due"] for n in future), default=""),
            "placeholder": placeholder_boards.get(board, 0),
            "earliest_overdue": min((n["fsrs_due"] for n in due if n["fsrs_due"]), default=""),
        })
    # CARD-G3-6a 加性: 顶层 buckets 五桶节点级分组 — 划分的权威表达。
    # 五键恒在 (空 vault 亦为五个空数组, 与 ineligible 同风格, 消费方不做
    # 存在性分支); 桶内按扫描序 (= due_nodes 行序) 稳定。行只带消费方渲染
    # 队列必需的四字段: 到期三桶与 due_nodes 同源, due_today/future 是
    # due_nodes 结构上装不下的那两桶 (它们不到期, 搬进去就违反 S2)。
    buckets: dict[str, list] = {b: [] for b in BUCKET_ORDER}
    for n in nodes:
        if not n["board"]:
            continue
        buckets[n["bucket"]].append({
            "node": n["node"],
            "board": n["board"],
            "why_due": n["why_due"],
            "fsrs_due": n["fsrs_due"],
        })
    payload = {
        "unassigned_nodes": unassigned,  # Code-Review M3: 点名而非只给数字
        "schema_version": 3,             # v3: +due_nodes 明细 +ineligible 分桶
        #                                  (纯加性; v2: FSRS WHEN 化 upcoming/due 语义)
        # CARD-C1a: 顶层加性新增 — send 侧据此组合 per-vault 有效通知 id,
        # C2 总览页据此标卡片; notification.id 值与其余字段零改动 (A2 冻结)
        "vault_id": Path(vault).resolve().name,
        "date": now.astimezone().date().isoformat(),
        "generated_at": now.astimezone().isoformat(timespec="seconds"),
        "top_boards": ranked[:3],
        "upcoming": upcoming[:3],
        "due_nodes": due_rows,
        "boards": boards_rollup,  # CARD-D1 P1 加性: 板级全量 rollup
        "buckets": buckets,       # CARD-G3-6a 加性: 五桶节点级分组 (S1 划分)
        "ineligible": ineligible,
        "stats": stats,
        "notification": None,
    }
    day_id = f"canvas-review-{payload['date']}"
    if ranked:
        payload["notification"] = {
            "title": _title(ranked[0]["board"]),
            "body": _body(ranked[0]),
            "group": "canvas复习",
            "id": day_id,
        }
    elif upcoming:
        # F1 放假语义: 有调度中的板但今天零到期 → 诚实说不用复习
        nxt = upcoming[0]
        payload["notification"] = {
            "title": "📚 今日无到期节点",
            "body": f"按计划推进，休息一天 · 最近到期 {nxt['board']} · {nxt['next_due'][:10]}",
            "group": "canvas复习",
            "id": day_id,
        }
    return payload, ranked


def render_md(payload, ranked) -> str:
    s = payload["stats"]
    lines = [
        f"# 今日复习 · {payload['date']}",
        "",
        f"> 生成 {payload['generated_at']} · 到期={s['due_nodes']} / 未到期={s['future_nodes']}（不含未归板）"
        f" · 节点状态: new={s['new']} / legacy={s['legacy']}"
        f" / 无字段={s['none']} / 未剖析跳过={s['ineligible']} / 测试排除={s['test_excluded']}"
        f" / 未归板={s['unassigned']} / 损坏={s['corrupt']}",
        "",
        "| 板 | 优先分 | 到期待复习 | 最该考 | 难度 | 闲置 | 板内下次到期 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ranked:
        idle = "从未考" if r["idle_days"] is None else f"{r['idle_days']} 天"
        nxt = r["next_due"][:10] if r["next_due"] else "-"
        diff = r["difficulty"] or "-"
        lines.append(
            f"| {r['board']} | {r['priority']} | {r['pending']} | {r['top_node']} | {diff} | {idle} | {nxt} |"
        )
    if payload.get("upcoming"):
        for u in payload["upcoming"]:
            lines.append(f"| {u['board']} | - | 0（未到期） | - | - | - | {u['next_due'][:10]} |")
    if ranked:
        lines += ["", "## 一键开考（整行复制到 Claudian）", ""]
        for r in ranked:
            lines.append(f"- `/start-exam-board from {r['board']} node {r['top_node']}`")
    else:
        lines += ["", "> ✅ 今日无到期节点，休息一天。"]
    # CARD-G3-6a: 人读清单加性分层段 — 这是「桶位/why_due」唯一的用户直接
    # 可感面 (JSON 侧给消费方, 这里给人)。表格零改动, 只在末尾追加一段。
    bucketed = payload.get("buckets") or {}
    if any(bucketed.get(b) for b in BUCKET_ORDER):
        lines += [
            "",
            "## 分层队列",
            "",
            " · ".join(f"{BUCKET_CN[b]} {len(bucketed.get(b, []))}" for b in BUCKET_ORDER),
        ]
        for b in BUCKET_ORDER:
            rows = bucketed.get(b, [])
            if not rows:
                continue
            lines += ["", f"**{BUCKET_CN[b]}**（{len(rows)}）"]
            for r in rows:
                lines.append(f"- {r['node']} · {r['board']} — {r['why_due']}")
    if payload.get("unassigned_nodes"):
        lines += ["", "> ⚠ 未归板节点（无 source_board，不参与推荐）: "
                  + "、".join(payload["unassigned_nodes"])]
    lines += [
        "",
        "> WHEN=FSRS 到期（无 fsrs_due 字段 = 新卡即刻到期）；WHAT=到期集合内按 μ−σ 排序",
        "> （含闲置回升，证据质量半衰期 69 天）。未剖析占位节点已跳过；命令已绑定最该考节点。",
    ]
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def load_decay(vault: Path):
    sys.path.insert(0, str(vault / ".claude" / "scripts"))
    import decay_beta
    return decay_beta


def main():
    # allow_abbrev=False 与 runner/push.sh 同源 (Codex-C1a F1)
    ap = argparse.ArgumentParser(description="每日复习选板", allow_abbrev=False)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--state", help="daily-review.state.json (只读, 取 board_last_recommended)")
    ap.add_argument("--now", help="ISO 时间覆盖 (测试用)")
    ap.add_argument("--write", action="store_true", help="写 outputs/今日复习.md+json")
    args = ap.parse_args()

    vault = Path(args.vault)
    # 裸时间当本地时区, 与 daily_review_run.py 语义统一 (Code-Review L6)
    if args.now:
        dt = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        now = dt if dt.tzinfo else dt.astimezone()
        # Codex-G3-6a round-1 HIGH: 日历极值时刻 (如 9999-12-31T23:59:59Z)
        # 在本地/上海时区换算时 OverflowError —— HEAD 起就会在
        # payload["date"] 处抛 traceback 中断整轮, 本卡把桶位判定挪到更前
        # 只是让崩点提前。与其抛 traceback, 在入口一次性拒绝并说清原因
        # (不改任何冻结字段的计算)。
        try:
            now.astimezone()
            now.astimezone(_TZ_SHANGHAI)
        except (OverflowError, OSError):
            ap.error(f"--now 超出可换算范围 (本地/上海时区换算溢出): {args.now}")
    else:
        now = datetime.now(timezone.utc)
    blr = {}
    if args.state and Path(args.state).exists():
        try:
            blr = json.loads(Path(args.state).read_text(encoding="utf-8")).get(
                "board_last_recommended", {})
        except (json.JSONDecodeError, OSError):
            pass  # state 损坏由 runner 处置, 选点侧降级为无记录

    payload, ranked = build_payload(vault, now, blr, load_decay(vault))
    if args.write:
        out = vault / "outputs"
        out.mkdir(parents=True, exist_ok=True)
        atomic_write(out / "今日复习.md", render_md(payload, ranked))
        atomic_write(out / "今日复习.json",
                     json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
