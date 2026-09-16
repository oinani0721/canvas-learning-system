#!/usr/bin/env python3
"""CARD-G6-8 — 五面复习视图一致性契约（可重跑）。

同一份 state 输入喂给复习视图的五个面, 逐字段比对它们对每块板给出的结论
（桶位 / 显示日 / 推迟 / 完成）, 任一字段跨面不等即 FAIL。

    五面（设计稿 §4 T3-B 逐字）
      ① review_overview   /overview 聚合 (_collect → _summarize → _gate_buckets)
      ② review_app        交互页 —— **纯消费方**, 不产出独立结论;
                          对它的契约是「不自造 due 算法」的静态断言
      ③ daily_review_pick Dashboard / outputs/今日复习.json 的生产器（**只读**）
      ④ 两个 skill 脚本    board-recap/recap_exam_build.py + clear-inbox/inbox_preview.py
      ⑤ 推送 payload      payload["notification"]（picker 产, daily_review_run 消费）

用法::

    cd backend && .venv/bin/python scripts/g68_five_view_contract.py \\
        --now 2026-09-12T03:00:00Z [--tz Asia/Shanghai] [--json 输出.json]

rc: 0 = verdict=PASS（零未登记分歧）; 1 = FAIL; 2 = 用法/环境错误。

⛔ 本脚本零 mock: 五面都跑**真实生产代码**, fixture 是 tmp 下的真 vault 目录与
真 JSON 文件。唯一被注入的是**时钟**（`--now`）与 `CANVAS_TZ`/`VAULTS_ROOT`/
`runner.BACKUPS` 三个作用域变量 —— 注入时钟是本契约成立的前提（不注入就没有
「同一 state 输入」可言）, 不是对被测行为打桩。

⛔ 不连 7691/7687, 不读写 live vault, 不写仓库树: 全部产物在 tempfile 目录内,
退出时删除（`--keep` 保留供排障）。
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: 本文件在 backend/scripts/ 下 ⇒ parents[2] = 车道树根。
WT = Path(__file__).resolve().parents[2]

#: 「该面不产出这个字段」的显式标记。⛔ 不是 None, 也不是空串 —— 缺席必须与
#: 「结论是空」可区分, 否则一个面悄悄不再产出某字段时矩阵仍然全等（假绿）。
NOT_PRODUCED = "<该面不产出此字段>"

#: 「这个面**声称**产出该字段, 但这块板上没有它的值」。⛔ 与 NOT_PRODUCED 严格
#: 区分: 前者是结构性缺席（review_app 是纯消费方, 本就不产出）, 后者是**丢了一块板**。
#: 把两者混成一个值, 「某面整块板消失」就会因为「产出该字段的面不足两个」而被
#: 比对循环跳过 —— 门看起来在比, 实际那条路径上无人看管。
MISSING = "<该面声称产出却缺了这块板>"

#: `display_day` = 该面**自己的**「今天」（各面按各自的时钟与时区算出来的）。
#: `projection_day` = 该面**从投影里读到并对外复述**的那个日期 —— 两者是两件事:
#: 前者测「各面的时钟口径是否同源」, 后者测「消费方复述生产者的值时有没有走样」。
#: ⛔ 分成两列是 Codex r1 HIGH-4 逼出来的: 原先 overview 的日期是**现算**的
#: （`_display_today(_display_now())`）, 于是把它响应里的投影日期改成 1970 年,
#: 整门照样绿 —— 那一列根本没有绑在被观察的响应上。
FIELDS = ("bucket", "display_day", "projection_day", "snoozed", "done")

#: 逐字段的**声明**产出方 —— 来自面普查（census）, 不是从数据里反推。
#: ⛔ 必须是声明: 从数据反推等于「谁没产出就当它不该产出」, 那正是 MISSING 要堵的洞。
#: ⛔ 每个字段**至少两个**产出方: 只剩一个产出方的列没有跨面契约可言, 它会变成
#: 一条恒真的判据（Codex r1 MEDIUM-5: 声明与实现同步缩减时对账仍通过）。
FIELD_PRODUCERS: dict[str, tuple[str, ...]] = {
    "bucket": ("review_overview", "picker"),
    "display_day": ("review_overview", "picker", "skill_inbox", "notification"),
    "projection_day": ("review_overview", "picker", "notification"),
    "snoozed": ("review_overview", "picker"),
    "done": ("review_overview", "picker"),
}

FACES = (
    "review_overview",
    "review_app",
    "picker",
    "skill_recap",
    "skill_inbox",
    "notification",
)


# ─────────────────────────── 已登记分歧（身份白名单）───────────────────────────
#: ⛔ 这张表按**身份**列举（面 / 字段 / 理由）, 不是「允许 N 条分歧」的计数式白
#: 名单 —— 计数式白名单挡不住等长替换（换一条分歧进来、数量不变就蒙混过关）。
#: 表里每一条都必须同时出现在验收单的「台账待登记条目」里。
#:
#: skill_inbox: `inbox_preview.py:430 _TZ_SHANGHAI = timezone(timedelta(hours=8))`
#: 是**刻意**的固定 +08:00（源码 :423 原话「人话时区：固定 +08:00，刻意不走
#: ZoneInfo("Asia/Shanghai")」）。它与 picker/overview 的 `local_tz.display_tz()`
#: 在非 +08:00 机器上给出不同的「今天」。是否应当统一是产品问题（收件箱清理与
#: 复习队列是否共用一个「今天」）, 本卡只把分叉**测出来并登记**, 不改它。
#: ⛔ **豁免必须是谓词, 不能是「面+字段」的空白支票**（Codex r1 HIGH-2）: 原先只按
#: (面, 字段) 匹配, 于是把 inbox 的日期改成 `2099-01-01`、甚至让它整块板缺席,
#: 都照样落进「已登记」而不判红 —— 白名单一旦不带谓词, 它豁免的就不是那条已知分歧,
#: 而是那一整格。谓词只认「恰好等于同一时刻在固定 +08:00 下的本地日」这一种取值。
def _inbox_fixed_offset_day(ctx: dict) -> str:
    """同一时刻在**固定 +08:00** 下的本地日 —— inbox 唯一被允许的取值。"""
    return ctx["now"].astimezone(timezone(timedelta(hours=8))).date().isoformat()


DECLARED_DIVERGENCES: tuple[dict, ...] = (
    {
        "face": "skill_inbox",
        "field": "display_day",
        # 谓词: 该面的值必须**恰好**是固定 +08:00 下的当地日。其它任何取值
        # （错日 / MISSING / NOT_PRODUCED）都不在豁免范围内, 一律按未登记分歧判红。
        "predicate": lambda value, ctx: value == _inbox_fixed_offset_day(ctx),
        "reason": "inbox_preview 的人话时区是刻意固定的 +08:00（:423/:430）, "
        "与 local_tz.display_tz() 在非 +08:00 机器上分叉; "
        "是否统一交产品（台账 ②, 本卡不改）",
    },
)


class ContractError(RuntimeError):
    """环境/用法错误 —— 与「契约判红」区分开（后者是 FAIL, 前者是 rc=2）。"""


# ─────────────────────────────── fixture ────────────────────────────────
#: A2 的 5 类口径分歧节点（复用 `backend/tests/regression/test_daily_review_pick.py::
#: test_projection_v3_due_nodes_and_ineligible_buckets` 的分类, 逐类一块板 ——
#: 一板一节点让「板级结论」无歧义, 另有一块板刻意放两个节点以覆盖「同板跨桶」）。
#:
#: ⛔ 期望值不从被测物取: 桶位由各面自己算, 本脚本只比它们**彼此**是否一致,
#: 不写死「应该是哪个桶」—— 那会让期望与被测量同源。


#: fixture **自己知道**它造了哪些板 —— 矩阵的行索引以此为准。
#:
#: ⛔ 行索引**不能从被测面反推**（Codex r2 HIGH-1 的更深一层）: 原先
#: `boards = set(picker) | set(overview)`, 于是一块板**从所有面同时消失**时它整行
#: 都不存在, 连个可比的格子都没有 —— 负控 `R2H1_BOTH_MISSING`（两面共用的提取层
#: 丢一块板）实测因此全绿。行索引必须来自**独立于被测面**的来源: 就是我们写进
#: fixture 的那份板清单。各面多报的板仍然并集进来（多报同样要判红）。
FIXTURE_BOARDS: frozenset[str] = frozenset({"板-到期", "板-新卡", "板-学习中", "板-脏日期", "板-今天晚些", "板-未来"})

#: 板级锚不够 —— 还要**节点级**（Codex r3 HIGH-2）: 只丢掉板内的**一个节点**时,
#: 板还在、`FIXTURE_BOARDS` 也完整, 两面又同时丢同一个节点 ⇒ 矩阵毫无反应。
#: 这里写死「应当出现在五桶里的 (板, 节点) 对」: fixture 里已归板且未被 ineligible
#: 拦下的那些（占位 / TestConcept 进 ineligible, 孤儿没有 source_board, 都不在内）。
FIXTURE_BUCKET_NODES: frozenset[tuple[str, str]] = frozenset(
    {
        ("板-到期", "规范到期"),
        ("板-到期", "同板未来"),
        ("板-新卡", "无type"),
        ("板-学习中", "学习中"),
        ("板-脏日期", "脏due"),
        ("板-今天晚些", "今天晚些"),
        ("板-未来", "远期"),
    }
)

#: fixture 刻意推迟的那块板 —— 它在**没有推迟**时会排在 `ranked` 首位。
#: ⛔ 选它不是随手（Codex r3 MEDIUM-5）: 原先推迟的板本来就在队尾, 于是把
#: `snoozed={}` 传进去矩阵照样全绿 —— 那条判据分不出「让位生效」与「压根没推迟」。
#: 推迟一块**本该排第一**的板, 才能用「它不在首位」这条独立期望把消费钉住。
FIXTURE_SNOOZED_BOARD = "板-到期"


def _node_md(board: str, extra: str = "") -> str:
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def _utc_z(dt: datetime) -> str:
    """A2 生产器 fsrs_due 形态: UTC 秒级 Z 后缀。"""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_nodes(now: datetime, display_tz) -> dict[str, str]:
    """A2 五类分歧节点 + 三个未到期节点, 覆盖全部五个桶。

    未到期两桶（due_today / future）必须按**显示时区的本地日**构造, 否则
    「今天晚些」这一桶在换时区跑时会静默塌进 future —— 契约就测不到它。
    """
    local = now.astimezone(display_tz)
    # 当地日内、now 之后的一个时刻（当地 23:30; 若 now 已过 23:30 则退到 now+1s
    # 所在当日的最后一秒 —— 仍是同一本地日, 仍晚于 now）。
    today_late = local.replace(hour=23, minute=30, second=0, microsecond=0)
    if today_late <= local:
        today_late = local.replace(hour=23, minute=59, second=59, microsecond=0)
        if today_late <= local:
            # now 就在当地 23:59:59 之后的那一秒 —— 当天已没有「晚些」可用,
            # 如实抛而不是悄悄换成明天（那会把 due_today 这一桶从矩阵里抹掉）。
            raise ContractError(
                f"--now 落在当地日最后一秒之后（{local.isoformat()}）, 无法构造 due_today 节点; 换一个 --now 再跑。"
            )
    return {
        # ① 规范到期 → due_now
        "规范到期": _node_md("板-到期", extra=f"fsrs_due: {_utc_z(now - timedelta(days=2))}\n"),
        # ② 无 type 字段 → picker 口径照收, 无 fsrs_due ⇒ new
        "无type": '---\nsource_board: "[[原白板/板-新卡]]"\n---\n真实内容。\n',
        # ③ 学习中（fsrs_state=1）且已到期 → learning_queue
        "学习中": _node_md(
            "板-学习中",
            extra=f"fsrs_due: {_utc_z(now - timedelta(hours=3))}\nfsrs_state: 1\n",
        ),
        # ④ 脏 fsrs_due（带时区偏移, 非生产器形态）→ fail-open 视同到期 ⇒ due_now
        "脏due": _node_md("板-脏日期", extra="fsrs_due: 2026-07-29T01:00:00+08:00\n"),
        # ⑤ 未到期 · 落在与 now 同一个显示时区本地日 → due_today
        "今天晚些": _node_md("板-今天晚些", extra=f"fsrs_due: {_utc_z(today_late)}\n"),
        # ⑥ 未到期 · 远期 → future
        "远期": _node_md("板-未来", extra=f"fsrs_due: {_utc_z(now + timedelta(days=9))}\n"),
        # ⑦ 同板跨桶: 板-到期 上再放一个未来节点 —— 板级结论不是单值,
        #    矩阵值必须是 ((节点, 桶), …) 的有序元组才比得动。
        "同板未来": _node_md("板-到期", extra=f"fsrs_due: {_utc_z(now + timedelta(days=30))}\n"),
        # ⑧ 占位符未剖析 → ineligible.placeholder（不进桶, 但必须不被静默吞掉）
        "占位": _node_md("板-到期").replace("真实内容。", "> 你的 1-2 句精准定义"),
        # ⑨ 测试文件名 → ineligible.test_excluded
        "TestConcept-伪节点": _node_md("板-到期"),
        # ⑩ 无 source_board → unassigned_nodes（不进桶）
        "孤儿": "---\ntype: concept\n---\n真实内容。\n",
    }


def build_vault(root: Path, name: str, nodes: dict[str, str]) -> Path:
    """tmp 下的真 vault 目录（与 test_daily_review_pick._build 同款形状）。"""
    vault = root / name
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    (vault / "outputs").mkdir()
    # ⛔ `.obsidian/` 是 `_list_vault_dirs` 的候选条件（与 GET /vault/list 同一条
    #    规则, review_overview :799-807）—— 缺它整个 vault 不会被 _collect() 列出来,
    #    review_overview 这一面会静默给不出任何结论。
    (vault / ".obsidian").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for node_name, content in nodes.items():
        (vault / "节点" / f"{node_name}.md").write_text(content, encoding="utf-8")
    return vault


# ─────────────────────────────── 面：picker ───────────────────────────────


def _board_bucket_rows(bucket_map: dict[str, list[dict]]) -> dict[str, tuple]:
    """{桶名: [行]} → {板: ((节点, 桶), …) 有序元组}。

    ⛔ 值是**节点级**的有序元组而不是板级聚合计数: 只比「每板几个」会让
    「身份被整体替换但每板数量不变」的投影蒙混过关（review_overview
    `_gate_buckets` docstring 里 Codex round-1 已实证过这条）。
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for bucket, rows in bucket_map.items():
        for row in rows:
            board = row.get("board")
            node = row.get("node")
            if not isinstance(board, str) or not isinstance(node, str):
                raise ContractError(f"桶 {bucket!r} 的行缺 board/node: {row!r}")
            out.setdefault(board, []).append((node, bucket))
    return {b: tuple(sorted(v)) for b, v in out.items()}


def check_ranked_yield_partition(
    ranked: list[dict], yielded: set[str], *, require_exact_boards: set[str] | None = None
) -> None:
    """picker 的 snooze/done 结论**被消费**的可观察后果: 让位分区。

    `build_payload` 对被推迟 / 今天已完成的板做**稳定分区**——它们整体让出榜首,
    排在其余板之后（picker `:1009-1028`）。所以「没有一块让位板排在非让位板之前」
    是这条消费的可观察不变量。

    ⛔ 为什么需要它（Codex r1 MEDIUM-6）: 契约原先只从**输入**重算 done/snoozed,
    `ranked` 被丢弃 —— 于是「让已完成板排回榜首」这种消费失效完全看不见。
    ⚠ 退化情形如实声明: 全部板都让位时分区退化为恒等（picker 注释明文), 此时本条
    恒真, 不构成判据。本卡 fixture 里非让位板非空, 不落在退化区。
    ⚠ 覆盖面如实声明: 本条只证「让位板整体靠后」, **不证**已完成与已推迟两者之间的
    先后（那是 U6-C 登记、D-37 按现状不改的那条顺序）。
    """
    boards = [r["board"] for r in ranked]
    # ⛔ 队列完整性先于分区（Codex r2 MEDIUM-5）: 早期版本只看顺序, 于是把
    #    `ranked` 整个清空照样过 —— 「没有队列」不该被读成「顺序没问题」。
    if not boards:
        raise ContractError("picker 的 ranked 为空 —— 没有队列就谈不上让位分区, 这一条不能当绿灯")
    # ⛔ 队列成员必须**恰好**是期望集合（Codex r2 MEDIUM-5 → r3 MEDIUM-4）:
    #    先前只要求「点名的那几块在场」, 于是把队列砍到只剩让位板仍然全过 ——
    #    分区条件在那种队列上退化成恒真。少一块 = 让位判定对它空转; 多一块 =
    #    队列里混进了不该在的板。两侧都要说话。
    # ⛔ 队列不许有重复项（Codex r4 LOW-8）: 集合相等对 `[A, A, B]` 无感,
    #    而「队列完整」这个说法里本来就含「每块板恰好一次」。
    if len(boards) != len(set(boards)):
        _dup = sorted({b for b in boards if boards.count(b) > 1})
        raise ContractError(f"picker 的 ranked 出现重复板: {_dup} —— 集合相等看不出重复, 但队列本该每板恰好一次")
    if require_exact_boards is not None and set(boards) != require_exact_boards:
        raise ContractError(
            f"picker 的 ranked 板集合与期望不符: 少了 {sorted(require_exact_boards - set(boards))}, "
            f"多了 {sorted(set(boards) - require_exact_boards)}"
        )
    if not yielded or all(b in yielded for b in boards):
        return  # 退化: 没有让位板, 或全部让位 —— 分区恒等, 本条不构成判据
    first_yield = next((i for i, b in enumerate(boards) if b in yielded), None)
    if first_yield is None:
        return
    late_unyielded = [b for b in boards[first_yield:] if b not in yielded]
    if late_unyielded:
        raise ContractError(
            "picker 的让位分区被破坏: 让位板（已推迟/今日已完成）之后仍出现未让位板 "
            f"{late_unyielded} —— snooze/done 的消费失效了; ranked 板序={boards}"
        )


def face_picker(picker, vault: Path, now: datetime, board_done: dict, snoozed: dict) -> tuple[dict, dict, list[str]]:
    """③ picker（**只读**）—— 返回 (payload, 板级结论)。

    picker 的 snooze/done 结论不落 payload（「完成状态不进 projection」是 A2 的
    明文纪律）, 它表达在 `ranked` 的**让位分区**上。所以这里取它**实际用来判定
    的那两个函数/键**: `active_snoozed()`（与页面侧 `_snoozed_active` 是同一个
    函数）与 `board_done.get(board) == payload["date"]`（与 picker :1011 的
    `_today_key` 逐字同源）—— 不另写一套判定; 并用 `check_ranked_yield_partition`
    观察这两个结论**被消费**后的可见后果。
    """
    payload, ranked = picker.build_payload(
        vault,
        now,
        {},
        picker.load_decay(vault),
        board_done=board_done,
        snoozed=snoozed,
    )
    buckets = _board_bucket_rows(payload["buckets"])
    day = payload["date"]
    awake = picker.active_snoozed(snoozed, now)
    yielded = set(awake) | {b for b, d in board_done.items() if d == day}
    # ⛔ 队列必须**恰好**是「有到期节点的板」那一集合（Codex r3 MEDIUM-4）:
    #    只要求「点名的那几块在场」时, 把队列砍到只剩让位板仍然全过 —— 分区条件
    #    在那种队列上退化成恒真。期望集合从 picker **自己的**三个到期桶导出,
    #    与队列同源但不同路（一个是 buckets, 一个是 ranked）。
    #    （期望集合取 payload 自己的 `due_nodes` 明细 —— 那是 A2 冻结的到期口径
    #     权威清单, 与 `ranked` 同源但不同路。）
    due_boards = {row["board"] for row in payload["due_nodes"] if row.get("board")}
    check_ranked_yield_partition(ranked, yielded, require_exact_boards=due_boards)
    # ⛔ snooze 真的被消费了吗（Codex r3 MEDIUM-5）: 前面那些判定全部从**同一份输入**
    #    重算, 于是「把 snoozed 清空」与「让位生效」在矩阵里无法区分。这里用一条
    #    **独立期望**钉死: fixture 推迟的是一块本该排首位的板, 那它就不该在首位。
    ranked_boards_now = [r["board"] for r in ranked]
    if FIXTURE_SNOOZED_BOARD in snoozed and len(set(ranked_boards_now)) > 1:
        # ⛔ 「它本该排首位」这个前提必须**实跑验证**, 不能假设（Codex r4 MEDIUM-5）:
        #    fixture 的排序会随别的改动漂移, 前提一旦不成立, 下面那条判据就退化成恒真
        #    而没人知道。跑一次**无推迟**的对照, 拿它的首位来当参照。
        _ctrl_payload, _ctrl_ranked = picker.build_payload(
            vault, now, {}, picker.load_decay(vault), board_done=board_done, snoozed={}
        )
        _ctrl_first = _ctrl_ranked[0]["board"] if _ctrl_ranked else None
        if _ctrl_first != FIXTURE_SNOOZED_BOARD:
            raise ContractError(
                f"fixture 前提已漂移: 无推迟时 ranked 首位是 {_ctrl_first!r}, 不是被推迟的 "
                f"{FIXTURE_SNOOZED_BOARD!r} —— 「推迟让出首位」这条判据失去参照, 换一块板再推迟"
            )
        if ranked_boards_now[0] == FIXTURE_SNOOZED_BOARD:
            raise ContractError(
                f"被推迟的板 {FIXTURE_SNOOZED_BOARD!r} 仍排在 ranked 首位 —— snooze 没有被消费; "
                f"ranked 板序={ranked_boards_now}（无推迟对照的首位也是它, 说明推迟完全没生效）"
            )
    conclusions = {
        board: {
            "bucket": rows,
            "display_day": day,
            # picker 既是生产者又是「复述者」: 它落盘的 `date` 就是投影日期本身。
            "projection_day": day,
            "snoozed": board in awake,
            "done": board_done.get(board) == day,
        }
        for board, rows in buckets.items()
    }
    return payload, conclusions, [r["board"] for r in ranked]


# ────────────────────────── 面：review_overview ───────────────────────────


def face_review_overview(ro, vaults_root: Path, vault_id: str) -> tuple[dict, bool]:
    """① /overview 聚合面 —— 走 `_collect()` 真实读路径。"""
    collected = ro._collect()
    entries = [v for v in collected["vaults"] if v["vault_id"] == vault_id]
    if len(entries) != 1:
        raise ContractError(f"_collect() 未给出 vault {vault_id!r} 的唯一条目（实得 {len(entries)} 条）")
    entry = entries[0]
    if entry["status"] not in ("ok", "stale"):
        raise ContractError(f"_collect() 把 fixture 投影判成 {entry['status']}: {entry.get('error')!r}")
    proj = entry["projection"]
    rows = proj.get("bucket_rows")
    if not isinstance(rows, dict):
        raise ContractError(
            "投影摘要缺 bucket_rows —— review_overview 这一面没有可比结论, "
            "契约无从成立（检查 _gate_buckets 是否仍出门节点行）"
        )
    buckets = _board_bucket_rows(rows)
    # ⛔ 两个日期都必须从**响应里读**, 不许现算（Codex r1 HIGH-4）:
    #    · display_day  = 响应顶层 `generated_at` 的日期部分 —— 这是本面按自己的
    #      时钟与时区给出的「今天」（`_collect()` 里 `now = _display_now()`）;
    #    · projection_day = 响应中它**复述**的投影日期 `projection["date"]`。
    #    原先写的是 `_display_today(_display_now())` —— 那是把被测量重新算一遍,
    #    于是把响应里的投影日期改成 1970 年, 整门照样绿。
    generated_at = collected.get("generated_at")
    if not isinstance(generated_at, str) or len(generated_at) < 10:
        raise ContractError(f"_collect() 的 generated_at 不是可取日期的字符串: {generated_at!r}")
    day = generated_at[:10]
    projection_day = proj.get("date")
    snoozed_boards = set(entry["snoozed"])
    done_boards = set(entry["board_done"])
    return {
        board: {
            "bucket": bucket_rows,
            "display_day": day,
            "projection_day": projection_day if projection_day is not None else MISSING,
            "snoozed": board in snoozed_boards,
            "done": board in done_boards,
        }
        for board, bucket_rows in buckets.items()
    }, collected["tonight_available"]


# ─────────────────────────── 面：review_app（静态）───────────────────────────

#: review_app 允许从 review_overview 引进来的共享名（:60-66 的 import 清单）。
_APP_SHARED_IMPORTS = ("_BUCKET_CN", "_BUCKET_ORDER", "_DONE_NOTE", "_SNOOZE_NOTE", "_STATUS_META")

#: AST 门里**按身份**豁免的字符串常量（模块级赋值名）。⛔ 不是按长度豁免:
#: 长度不是语义边界（Codex r3）。`_PAGE_TEMPLATE` 是 review_app 的页面模板
#: （HTML + 那段纯消费 /overview JSON 的 JS）, 它不在「Python 侧是否自造 due 算法」
#: 的射程内。名单里的名字若不在了, 门会当场抛 —— 豁免边界变了必须有人重判。
_EXEMPT_STRING_NAMES = ("_PAGE_TEMPLATE",)

#: review_app 里**允许**含 due 标识符的字符串常量, 按身份逐条列出。
#: ⛔ 不用「词边界」之类的启发式（Codex r4 HIGH-1）: `r"\bfsrs_due\b: …"` 这种正则源码
#: 里字段名紧邻字母 `b`, 任何边界规则都失效。改成**白名单**: 只有这几个确切的串
#: 允许含标识符, 其余含 due 标识符的字符串一律违约。新增一个就得在这里写一行 ——
#: 那是一个看得见的动作。
_ALLOWED_MARKER_STRINGS = ("__BUCKET_ORDER_JSON__",)

#: 页面模板里**碰 due 字段的那几行**, 按身份冻结。
#:
#: ⛔ 这道门**不声称**「模板里的 JS 是纯消费方」（Codex r4 HIGH-2）: 同一个标识符
#: 既出现在合法消费（把到期时刻渲染成人话）也能出现在自造到期判定里, 区分它们靠的是
#: **语义**, 而 JS 的语义在 Python AST 门的射程之外。四轮下来每补一个语法特例就来一种
#: 新写法 —— 那是「开放式判据」, 不会收敛。
#:
#: 门改为声称一件**可判定**的事: 模板里碰 due 字段的调用点集合**没有变过**。
#: 变了就红, 由人判新的那一处还算不算纯消费。覆盖面上限如实写在验收单。
_TEMPLATE_DUE_CALLSITES = frozenset(
    {
        "const due = humanizeDue(n.fsrs_due, nowMs);",
        "const due = humanizeDue(r.fsrs_due, nowMs);",
    }
)

#: 「自造 due 算法」的词法特征 —— 出现在 review_app 自己定义的函数体里即违约。
_DUE_ALGO_MARKERS = (
    "_BUCKET_ORDER",  # 只许 import, 不许在本文件里重新赋值
    "fsrs_due",
    "due_reason",
    "fsrs_state",
)


def assert_review_app_has_no_due_algorithm(app_path: Path) -> dict:
    """② review_app 的契约: **不自造 due 算法**, 桶位/归日只从 import 来。

    用 AST 而不是 grep: 注释与字符串里出现 `fsrs_due` 不算违约（本文件的职责
    注释就提到它）, 只有**可执行代码**里出现才算。
    """
    tree = ast.parse(app_path.read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "app.api.v1.endpoints.review_overview":
            imported |= {a.name for a in node.names}
    missing = [n for n in _APP_SHARED_IMPORTS if n not in imported]
    if missing:
        raise ContractError(
            f"review_app 不再从 review_overview 引入共享桶序常量（缺 {missing}）—— "
            "「共享不复制」这条纪律已破, 静态断言的前提不成立"
        )

    # 本文件自己**赋值**出来的名字（模块级常量 / 函数内变量 / 函数与类定义）。
    assigned: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assigned.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assigned.add(node.id)
    offenders = sorted(m for m in _DUE_ALGO_MARKERS if m in assigned)

    # 可执行代码里对 due 字段的读取。
    #
    # ⛔ **不再按语法形态逐个枚举**（Codex r1 HIGH-3 → r2 HIGH-3 的教训）: 前两轮
    #    先补了「属性 / 裸名」, 再补了「下标 / `.get()` 首参」, 对方立刻拿
    #    `def f(n, key="fsrs_due"): return n.get(key)` / `getattr(n, "fsrs_due")` /
    #    模块常量键 / `match` 解构走过去。**只要判据还在枚举写法, 它就永远收敛不了**
    #    —— 这是「开放式判据」的典型形状。
    #
    #    改判据的**形状**: 在 review_app 的 Python 代码里, due 字段名**作为字符串
    #    常量出现在任何位置**即违约（默认参数、模块常量、`getattr` 实参、`match`
    #    模式……一网打尽）, 外加属性/裸名两种非字符串形态。
    #
    # ⚠ 页面模板是一个巨大的字符串常量, review_app 是 /overview JSON 的纯消费方,
    #   那段 HTML/JS 不在本断言射程内。⛔ 豁免**按身份**, 不按长度（Codex r3 指出
    #   「长度不是有效语义边界」）: 只放过**模块 docstring** 与赋给
    #   `_EXEMPT_STRING_NAMES` 里那些名字的字符串常量, 其余一律在射程内。
    #
    # ⛔ 字符串判据是**包含**不是相等（Codex r3 HIGH-1）: `re.search(r"^fsrs_due: …")`
    #   这种读法里字段名只是子串, 相等判据整条走过去。
    #
    # ⛔ 还要认两处**不是 ast.Constant** 的字段名（同上）:
    #     · `match n: case SimpleNamespace(fsrs_due=v)` —— 名字在 `MatchClass.kwd_attrs`,
    #       那是一串**裸 str**, `ast.walk` 走不到;
    #     · `f(fsrs_due=…)` —— 名字在 `ast.keyword.arg`, 同样是裸 str。
    #
    # ⚠ **原理上限, 如实声明**: 运行期拼出来的字段名（`"fsrs_" + "due"`）任何静态
    #   判据都拦不住。本门拦的是「照常写出来」的读法, 不是刻意的混淆。
    exempt_nodes: set[int] = set()
    docstring = ast.get_docstring(tree, clean=False)
    # ⛔ **所有** docstring 都豁免, 不只是模块级（Codex r4 LOW-9）: 一个普通函数的
    #    说明文字里写「显示投影里的 fsrs_due 字段, 不计算到期」会被误红 ——
    #    那是在描述它**不做**什么, 不是在做。
    for holder in ast.walk(tree):
        if isinstance(holder, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(holder, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    exempt_nodes.add(id(body[0].value))
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if any(isinstance(t, ast.Name) and t.id in _EXEMPT_STRING_NAMES for t in node.targets):
                exempt_nodes.add(id(node.value))
    missing_exempt = [
        n
        for n in _EXEMPT_STRING_NAMES
        if not any(
            isinstance(b, ast.Assign) and any(isinstance(t, ast.Name) and t.id == n for t in b.targets)
            for b in tree.body
        )
    ]
    if missing_exempt:
        # 豁免名单里的名字不在了 ⇒ 要么页面模板改名了, 要么它被拆散了。
        # 任一情况下这条豁免的边界都变了, 必须有人重新判, 不能默默放宽。
        raise ContractError(f"页面模板常量 {missing_exempt} 不在 review_app 里了 —— AST 门的豁免边界变了, 需重判")

    reads: set[str] = set()
    exempted: list[tuple[str, int]] = [
        (n, len(node.value.value))
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for t in node.targets
        if isinstance(t, ast.Name) and (n := t.id) in _EXEMPT_STRING_NAMES
    ]
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _DUE_ALGO_MARKERS:
            reads.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in _DUE_ALGO_MARKERS and isinstance(node.ctx, ast.Load):
            if node.id not in imported:
                reads.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
            if id(node) in exempt_nodes:
                continue
            text = node.value.decode("utf-8", "replace") if isinstance(node.value, bytes) else node.value
            # ⛔ **裸包含 + 身份白名单**, 不用词边界（Codex r4 HIGH-1）: `r"\bfsrs_due\b"`
            #    这种正则源码里字段名紧邻字母 `b`, 任何边界规则都失效。白名单只放过
            #    确切的几个串（见 `_ALLOWED_MARKER_STRINGS`）, 其余含标识符的一律违约。
            if text in _ALLOWED_MARKER_STRINGS:
                continue
            for marker in _DUE_ALGO_MARKERS:
                if marker in text:
                    reads.add(marker)
        elif isinstance(node, ast.MatchClass):
            reads |= {a for a in (node.kwd_attrs or []) if a in _DUE_ALGO_MARKERS}
        elif isinstance(node, ast.keyword) and node.arg in _DUE_ALGO_MARKERS:
            reads.add(node.arg)
        # ⛔ 形参名也算（Codex r4 MEDIUM-4）: `def f(_BUCKET_ORDER=("future","new"))`
        #    ——形参在 `ast.arg`, 不进赋值检查; 函数体里读它又被模块级同名 import 豁免。
        elif isinstance(node, ast.arg) and node.arg in _DUE_ALGO_MARKERS:
            reads.add(node.arg)
    offenders += sorted(reads - set(offenders))
    if offenders:
        raise ContractError(
            f"review_app 出现独立 due 算法的迹象（在可执行代码里定义/读取 {offenders}）—— "
            "它必须是 /overview 投影的纯消费方"
        )

    # ── 页面模板里碰 due 字段的调用点: **按身份冻结**（Codex r4 HIGH-2）──────
    # ⛔ 这道检查**不声称**模板里的 JS 是纯消费方 —— 同一个标识符既能用于把到期时刻
    #    渲染成人话（现状: `humanizeDue(n.fsrs_due, nowMs)`）, 也能用于自造到期判定
    #    （`rows[b].filter(r => Date.parse(r.fsrs_due) <= nowMs)`）, 区分靠语义, 而
    #    JS 的语义在 Python AST 门的射程之外。它声称的是一件**可判定**的事:
    #    这些调用点**没有变过**。变了就红, 由人判新的那一处还算不算纯消费。
    template = next(
        (
            n.value.value
            for n in tree.body
            if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)
            and any(isinstance(t, ast.Name) and t.id == "_PAGE_TEMPLATE" for t in n.targets)
        ),
        "",
    )
    template_sites = {
        ln.strip() for ln in template.splitlines() if any(m in ln for m in ("fsrs_due", "due_reason", "fsrs_state"))
    }
    if template_sites != _TEMPLATE_DUE_CALLSITES:
        raise ContractError(
            "页面模板里碰 due 字段的调用点变了（该集合按身份冻结, 不是「JS 是纯消费方」的证明）: "
            f"新增 {sorted(template_sites - _TEMPLATE_DUE_CALLSITES)}; "
            f"消失 {sorted(_TEMPLATE_DUE_CALLSITES - template_sites)} —— 需人判新的那一处是否仍是纯消费"
        )

    return {
        "imported_shared": sorted(imported & set(_APP_SHARED_IMPORTS)),
        "offenders": [],
        # 模板里被冻结的 due 调用点 —— 摊开可见, 免得这条豁免变成暗门。
        "template_due_callsites": sorted(template_sites),
        # 被豁免的那几个字符串常量（名字 + 长度）—— 摊开写出来, 免得豁免变成暗门。
        "exempted_strings": sorted(exempted),
        "docstring_len": len(docstring or ""),
    }


# ───────────────────────────── 面：两个 skill 脚本 ─────────────────────────────


#: inbox_preview 渲染里那行「基准时刻 `--now`：<本地时刻>（Asia/Shanghai）」的锚。
_INBOX_NOW_LINE = "基准时刻 `--now`："


def face_skill_inbox(now_raw: str, tmp_root: Path) -> str:
    """④b clear-inbox/inbox_preview.py —— 它的「今天」, **取自它真正的产物**。

    ⛔ 不许在契约里自己按 `parse_now()` 再算一遍（Codex r2 HIGH-2）: 那样量的是
    「契约照着它的规则算出来的日期」, 不是「它实际交出来的日期」—— 把它的 `main()`
    改成用 2099 年、或者干脆提前 `return 0` 不产出任何东西, 契约都毫无反应。
    这里跑**真实入口** `main()`（`--vault` / `--now` 指向 tmp 空仓）, 再从它落盘的
    preview 里把那行「基准时刻」抠出来。产物缺席 / 抠不到 ⇒ 返回 `MISSING`, 由矩阵判红。

    ⚠ 空收件箱是它的合法形态（`--inbox-dir` 缺省路径不存在 = 空仓回执）—— 本契约
    只要它的**日期结论**, 不需要真有待处理文件。
    """
    scripts_dir = WT / "canvas-vault" / ".claude" / "skills" / "clear-inbox" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import inbox_preview  # noqa: PLC0415  — 路径在运行期才确定

    vault = tmp_root / "inbox-vault"
    (vault / "outputs").mkdir(parents=True, exist_ok=True)
    argv = sys.argv
    sys.argv = ["inbox_preview.py", "--vault", str(vault), "--now", now_raw]
    try:
        rc = inbox_preview.main()
    except SystemExit as e:  # argparse / 守卫的正常退出路径
        rc = e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = argv
    if rc != 0:
        return MISSING
    outs = sorted((vault / "outputs").glob("inbox-preview-*.md"))
    if not outs:
        return MISSING
    for line in outs[-1].read_text(encoding="utf-8").splitlines():
        if _INBOX_NOW_LINE in line:
            tail = line.split(_INBOX_NOW_LINE, 1)[1]
            # 形如 `2026-09-12 11:00（Asia/Shanghai）· schema v…`
            stamp = tail.strip().split("（", 1)[0].strip()
            day = stamp.split(" ", 1)[0]
            return day if len(day) == 10 and day.count("-") == 2 else MISSING
    return MISSING


def face_skill_recap() -> str:
    """④a board-recap/recap_exam_build.py —— **无可比结论**, 如实登记。

    该脚本的域是「阶段回顾检验白板的构建」: 它不读 fsrs_due、不判到期、不分桶,
    唯一的时间量是 `--ts` 文件戳, 且刻意取 **UTC**（:1397-1399 原注: 与
    start-exam-board 的 `date -u` 同一个时钟, 避免 created_at 排序错位）。
    把一个 UTC 文件戳与复习队列的「显示时区本地日」摆进同一列比较, 比的是
    两个不同的东西 —— 那是**凑出来的**对比, 不是契约。故本面四个字段一律
    NOT_PRODUCED, 理由落在 census 里。

    ⛔ 仍然**加载它一次**并断言入口在场: 「无可比结论」是关于它产出什么的结论,
    不是「不看它」的借口 —— 脚本若被删/入口改名, 本面必须说话。
    """
    import importlib.util

    path = WT / "canvas-vault" / ".claude" / "skills" / "board-recap" / "scripts" / "recap_exam_build.py"
    spec = importlib.util.spec_from_file_location("recap_exam_build_g68", path)
    if spec is None or spec.loader is None:
        raise ContractError(f"无法为 {path} 建立 import spec")
    mod = importlib.util.module_from_spec(spec)
    # ⛔ 必须先注册再 exec_module: 该模块 importlib 复用同目录 recap_scan.py,
    #    而 recap_scan 里有模块级 @dataclass —— Python 3.14 的 dataclass 自省要
    #    去 sys.modules[cls.__module__].__dict__ 取名字, 未注册就崩
    #    （协议 §3 同款; 第十批 X6 为此让 tests/skills 红了 117 条）。
    sys.modules["recap_exam_build_g68"] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop("recap_exam_build_g68", None)
        raise
    if not callable(getattr(mod, "main", None)):
        raise ContractError("recap_exam_build.py 没有可调用的 main() —— 入口已变, 本面的登记理由需重判")
    return "无可比结论：域是检验白板构建（--ts 是 UTC 文件戳）, 不产出复习队列的桶位/本地日结论"


# ───────────────────────────── 面：推送 payload ─────────────────────────────

_NOTI_ID_PREFIX = "canvas-review-"


def face_notification(payload: dict) -> tuple[str, str | None]:
    """⑤ payload["notification"] —— 推送这一面的日期结论与它点名的板。

    `id` 是 `canvas-review-<date>`（picker `day_id`）, `title` 里是 ranked[0] 的板名。
    桶位/推迟/完成这三个字段推送面不产出（它只说「今天做哪块」）。

    ⛔ 通知缺席时返回 **MISSING 而不是 NOT_PRODUCED**（Codex r1 HIGH-1）: 后者会让
    这一面整格退出比较, 于是「今天根本没发通知」这件事在矩阵里表现为零分歧。
    「缺席」是一个要判红的结论, 不是「我不产出这个字段」。
    ⚠ 生产器在 `ranked` 与 `upcoming` 都空时**本就**不产通知（那是合法的空库形态）。
    本卡 fixture 恒有到期板 ⇒ 恒有通知; 真出现空库要跑这条契约时, 应当先把
    「空库该不该有通知」裁定清楚再决定这一格的期望, 不能靠哨兵把它绕过去。
    """
    noti = payload.get("notification")
    if noti is None:
        return MISSING, None
    noti_id = noti.get("id")
    if not isinstance(noti_id, str) or not noti_id.startswith(_NOTI_ID_PREFIX):
        raise ContractError(f"notification.id 非生产器形态: {noti_id!r}")
    day = noti_id[len(_NOTI_ID_PREFIX) :]
    title = noti.get("title")
    return day, title if isinstance(title, str) else None


# ─────────────────────────────── 矩阵与比对 ───────────────────────────────


def build_matrix(per_face: dict[str, dict], boards: list[str]) -> dict:
    """{面: {板: {字段: 值}}} → {板: {字段: {面: 值}}}。

    声明产出该字段的面（`FIELD_PRODUCERS`）若在某块板上没有值 → 记 `MISSING`,
    它参与比对并会判红; 未声明产出的面记 `NOT_PRODUCED`, 不参与比对。
    """
    matrix: dict[str, dict[str, dict[str, object]]] = {}
    for board in boards:
        matrix[board] = {}
        for field in FIELDS:
            producers = FIELD_PRODUCERS[field]
            cells: dict[str, object] = {}
            for face in FACES:
                if face not in producers:
                    cells[face] = NOT_PRODUCED
                    continue
                row = per_face.get(face, {}).get(board)
                cells[face] = MISSING if (row is None or field not in row) else row[field]
            matrix[board][field] = cells
    return matrix


def check_bucket_node_identity(per_face: dict[str, dict]) -> None:
    """每个产出 `bucket` 的面, 它报出来的 (板, 节点) 集合必须**恰好**是 fixture 那一份。

    ⛔ 板级锚挡不住「板内少一个节点」（Codex r3 HIGH-2）: 两面同时丢掉同一个节点时,
    板还在、板级清单也完整, 矩阵里那一格的两个值仍然相等 —— 零分歧。
    节点身份必须有自己的锚, 而且这个锚来自 fixture, 不是从面反推的。
    """
    for face in FIELD_PRODUCERS["bucket"]:
        got = {
            (board, node)
            for board, row in per_face.get(face, {}).items()
            for node, _bucket in (row.get("bucket") or ())
        }
        if got != FIXTURE_BUCKET_NODES:
            raise ContractError(
                f"面 {face} 报出的 (板, 节点) 集合与 fixture 不符 —— "
                f"少了 {sorted(FIXTURE_BUCKET_NODES - got)}; 多了 {sorted(got - FIXTURE_BUCKET_NODES)}"
            )


def check_producers_declaration(per_face: dict[str, dict], boards: list[str]) -> None:
    """声明 vs 实测对账 —— 防「声明表与代码各说各话」。

    ⛔ 两个方向都查: 声明产出却一块板都没给出值 = 该面其实没进矩阵（白名单在给
    一件不存在的事发豁免）; 未声明却产出了值 = 声明表漏了一个面, 它的分歧永远
    不会被比到。
    """
    if set(FIELD_PRODUCERS) != set(FIELDS):
        raise ContractError(f"FIELD_PRODUCERS 的键与 FIELDS 不一致: {sorted(FIELD_PRODUCERS)} vs {sorted(FIELDS)}")
    for field, producers in FIELD_PRODUCERS.items():
        # ⛔ 每列至少两个产出方（Codex r1 MEDIUM-5）: 只剩一个产出方的列没有跨面
        #    契约可言 —— 「把声明砍到只剩一个面, 同时让另一个面别再产出」会让这一列
        #    静默退化成恒真判据, 而两侧同步缩减时旧版对账查不出来。
        if len(producers) < 2:
            raise ContractError(f"字段 {field} 只剩 {len(producers)} 个声明产出方 —— 跨面契约不成立")
        for face in FACES:
            # ⛔ 只看该面**真的交出来的**那些值。早期版本把「这块板该面没有」也按
            #    NOT_PRODUCED 计入, 于是「某面整块板消失」被误报成「它交出了
            #    NOT_PRODUCED」而当场抛 —— 真正的 MISSING 信号反而被这条误报盖住
            #    （负控 RO_BOARD_IDENTITY 实测 rc=2 抓到）。板缺席走 MISSING 那条路,
            #    由 build_matrix / diff_matrix 判红, 不在这里抛。
            rows = per_face.get(face, {})
            emitted = [rows[b][field] for b in boards if b in rows and field in rows[b]]
            produced = [v for v in emitted if v != NOT_PRODUCED]
            # ⛔ 声明产出方不许交出 NOT_PRODUCED（Codex r1 HIGH-1）: 那个哨兵会被
            #    比对循环整格过滤掉, 于是「通知缺席 ⇒ 该面悄悄退出比较 ⇒ 零分歧」。
            #    没有值就该是 MISSING（参与比对并判红）, 不是「我不产出这个字段」。
            # ⛔ 这一条排在「一块板都没给出值」**之前**: 一个面若每块板都交出哨兵,
            #    两条都成立, 而先报的那条决定了排障时看到的根因 —— 「交出了哨兵」
            #    比「没有值」更准确, 也更接近要改的地方。
            if face in producers and any(v == NOT_PRODUCED for v in emitted):
                raise ContractError(
                    f"面 {face} 在字段 {field} 上交出了 NOT_PRODUCED —— 声明产出方缺值必须用 MISSING, "
                    "NOT_PRODUCED 会让它整格退出比较"
                )
            if face in producers and not produced:
                raise ContractError(
                    f"面 {face} 被声明产出字段 {field}, 实测一块板都没给出值 —— 它没有真正进矩阵, 对它的比对是空转"
                )
            if face not in producers and produced:
                raise ContractError(
                    f"面 {face} 产出了字段 {field} 却不在 FIELD_PRODUCERS 声明里 —— "
                    "它的分歧不会被比到, 补声明或说明为何不纳入"
                )


def _is_declared(face: str, field: str, value, ctx: dict) -> bool:
    """这条分歧是否落在**已登记**的范围内。

    ⛔ 不是按 (面, 字段) 发空白支票, 而是逐条跑谓词: 已登记的是「那一种已知取值」,
    不是「那一格随便怎么错都行」（Codex r1 HIGH-2）。谓词抛异常 ⇒ 按未登记处理,
    宁可多判红也不吞。
    """
    for rule in DECLARED_DIVERGENCES:
        if rule["face"] != face or rule["field"] != field:
            continue
        try:
            if rule["predicate"](value, ctx):
                return True
        except Exception:  # noqa: BLE001 — 谓词自身出错不得变成豁免
            return False
    return False


def diff_matrix(matrix: dict, ctx: dict | None = None) -> tuple[list[dict], list[dict]]:
    """逐板逐字段比对 → (未登记分歧, 已登记分歧)。

    ⛔ 逐板逐字段全量比对, 不做「差异数 ≤ N」之类的计数式判据。
    `ctx` 供已登记分歧的谓词取上下文（如基准时刻）; 缺省 = 无上下文, 谓词取不到
    它要的键就会抛, 按未登记处理。
    """
    undeclared: list[dict] = []
    declared: list[dict] = []
    ctx = ctx or {}
    for board in sorted(matrix):
        for field in FIELDS:
            cells = matrix[board][field]
            producing = {f: v for f, v in cells.items() if v != NOT_PRODUCED}
            # ⛔ `MISSING` **永不算一致, 也永不进多数派**（Codex r2 HIGH-1）: 它是
            #    「声明产出却缺了这块板」这条结论本身。早期版本把它当成一个普通取值,
            #    于是两个产出方**同时**缺同一块板 ⇒ 取值集合只有一个元素 ⇒ 零分歧;
            #    缺值多数派还能把唯一真实分歧挤成少数派。每一个缺值都单独判红。
            for face, value in producing.items():
                if value != MISSING:
                    continue
                row = {
                    "board": board,
                    "field": field,
                    "face": face,
                    "value": json.dumps(MISSING, ensure_ascii=False),
                    "majority_value": None,
                    "majority_faces": [],
                }
                (declared if _is_declared(face, field, value, ctx) else undeclared).append(row)
            present = {f: v for f, v in producing.items() if v != MISSING}
            if len(present) < 2:
                # 剩下不足两个**有值**的面 ⇒ 无从比对; 缺值本身已在上面逐条判红。
                continue
            values = {json.dumps(v, ensure_ascii=False, sort_keys=True, default=str) for v in present.values()}
            if len(values) == 1:
                continue
            # 按取值分组（只对**有值**的面）。
            producing = present
            tally: dict[str, list[str]] = {}
            for face, value in producing.items():
                tally.setdefault(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str), []).append(face)
            sizes = sorted((len(v) for v in tally.values()), reverse=True)
            # ⛔ 只有**严格**多数派（最大组 > 次大组）才配当参照。平局时没有多数派:
            #    `bucket` 这一列只有两个面产出, 两值不等就是 1:1 —— 早期版本用
            #    `max(..., key=len)` 取「第一个最大组」, 于是归属完全由 FACES 的
            #    书写顺序决定, 把另一面单方面标成分歧方。负控 RO_BUCKET_SWAP 实测
            #    抓到过这一点: 改的是 review_overview, 报出来的却是 picker ——
            #    红是红了, 但红的归属是错的, 只看「红没红」的判据会放过它。
            #    平局时把**每一个**产出方都报成分歧方, 谁对谁错交人判。
            has_majority = len(tally) > 1 and sizes[0] > sizes[1]
            majority_faces = max(tally.values(), key=len) if has_majority else None
            for key, faces in tally.items():
                if majority_faces is not None and faces is majority_faces:
                    continue
                for face in faces:
                    row = {
                        "board": board,
                        "field": field,
                        "face": face,
                        "value": key,
                        "majority_value": (
                            [k for k, v in tally.items() if v is majority_faces][0]
                            if majority_faces is not None
                            else None
                        ),
                        "majority_faces": sorted(majority_faces) if majority_faces is not None else [],
                    }
                    bucket = declared if _is_declared(face, field, producing[face], ctx) else undeclared
                    bucket.append(row)
    return undeclared, declared


# ─────────────────────────────────── 主流程 ───────────────────────────────────


#: 判据码前缀 —— 只有本契约的分歧行会产出这串。
#: ⛔ 负控的文本锚必须绑在**这个码**上而不是人话字段名（Codex r4 MEDIUM-7）:
#: 被测模块的诊断输出经 stderr / 断言消息回流后也会带上 `E ` 前缀与 `snoozed`
#: 这类字样, 拿人话当锚就分不清「门抓到了」和「日志里恰好有这个词」。
DIFF_CODE_PREFIX = "G68DIFF"


def diff_code(row: dict) -> str:
    """一条分歧的机器可读身份: `G68DIFF|face=…|field=…`。"""
    return f"{DIFF_CODE_PREFIX}|face={row['face']}|field={row['field']}"


def _parse_now(raw: str) -> datetime:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as e:
        raise ContractError(f"--now 不是合法 ISO-8601 时刻: {raw!r}") from e
    if dt.tzinfo is None:
        raise ContractError(f"--now 必须带时区偏移（裸时刻在跨时区读写下指的是不同的绝对时间）: {raw!r}")
    return dt


def run(now_raw: str, tz_name: str, out_json: Path | None, keep: bool) -> int:
    now = _parse_now(now_raw)

    # ⛔ 三个作用域变量必须在 import 被测模块**之前**就位:
    #    · CANVAS_TZ —— picker 的 `_DISPLAY_TZ` 是**模块级常量**, import 那一刻固化;
    #    · VAULTS_ROOT —— review_overview 的 `_collect()` 从 settings 取;
    #    · runner.BACKUPS —— state 文件默认落在**仓库树的 backups/**, 必须改道 tmp。
    os.environ["CANVAS_TZ"] = tz_name

    tmp_root = Path(tempfile.mkdtemp(prefix="g68-five-view-"))

    # ⛔ 被测模块在 import / 运行期往 **stdout** 打带时刻的日志（`RAGService: …` 带
    #    秒级时间戳、picker 的 `[pick] fsrs_due 非规范格式…`）。它们混进报告会让
    #    「同输入二跑逐字节相等」永远不成立 —— 那条确定性判据是本脚本能当回归门的
    #    前提。所以计算期把 stdout 换成缓冲区, 只有报告本身写回真 stdout;
    #    出异常时把缓冲内容倒到 stderr, 不吞排障信息。
    _real_stdout = sys.stdout
    noise = io.StringIO()
    sys.stdout = noise
    try:
        vaults_root = tmp_root / "vaults"
        vaults_root.mkdir()
        backups = tmp_root / "backups"
        backups.mkdir()

        sys.path.insert(0, str(WT / "scripts"))
        import local_tz  # noqa: PLC0415
        import daily_review_pick as picker  # noqa: PLC0415
        import daily_review_run as runner  # noqa: PLC0415

        display_tz = local_tz.display_tz()
        runner.BACKUPS = backups  # 与 tests 同款隔离点（runner 注释 :42-44 点名）

        vault_id = "vault-g68"
        nodes = build_nodes(now, display_tz)
        # ⛔ 常量与 fixture 不许漂移: `FIXTURE_BOARDS` 是矩阵行索引的独立锚, 它若
        #    与实际造出来的节点脱钩, 那个锚就锚在空处了。从节点正文里把板名解出来对账。
        _declared_boards = {
            line.split("原白板/", 1)[1].split("]]", 1)[0]
            for md in nodes.values()
            for line in md.splitlines()
            if "原白板/" in line
        }
        # ⛔ 对账必须是**相等**不是子集（Codex r3 MEDIUM-3）: `<=` 只抓得到「清单多报」,
        #    抓不到「清单漏报」—— 从清单里删掉一块板、同时让提取层也不返回它, 两边都过。
        if FIXTURE_BOARDS != _declared_boards:
            raise ContractError(
                f"FIXTURE_BOARDS 与 fixture 脱钩: 清单多了 {sorted(FIXTURE_BOARDS - _declared_boards)}, "
                f"少了 {sorted(_declared_boards - FIXTURE_BOARDS)} —— 矩阵的行索引锚不可信"
            )
        # 节点级锚同样对账（同一条理由, 见 FIXTURE_BUCKET_NODES）。
        _declared_pairs = {
            (line.split("原白板/", 1)[1].split("]]", 1)[0], name)
            for name, md in nodes.items()
            for line in md.splitlines()
            if "原白板/" in line
        }
        # ⛔ 节点锚也要**相等**对账（Codex r3 MEDIUM-3 → r4 MEDIUM-3）: `<=` 只抓多报,
        #    「从锚里删一个节点、同时让提取层也不返回它」两边都过。相等对账要先把
        #    「已归板但**不该进桶**」的那几个显式排除掉 —— 它们由 ineligible 拦下,
        #    排除集合写死在这里, 改动同样是一个看得见的动作。
        _EXCLUDED = {("板-到期", "占位"), ("板-到期", "TestConcept-伪节点")}
        _expected_pairs = _declared_pairs - _EXCLUDED
        if FIXTURE_BUCKET_NODES != _expected_pairs:
            raise ContractError(
                f"FIXTURE_BUCKET_NODES 与 fixture 脱钩: 锚里多了 "
                f"{sorted(FIXTURE_BUCKET_NODES - _expected_pairs)}, 少了 "
                f"{sorted(_expected_pairs - FIXTURE_BUCKET_NODES)}（已排除 ineligible: {sorted(_EXCLUDED)}）"
            )
        vault = build_vault(vaults_root, vault_id, nodes)

        # ── state: 一块板推迟到明天, 一块板今天标完成 ────────────────────
        today_key = now.astimezone(display_tz).date().isoformat()
        # ⛔ 被推迟 / 已完成的板必须是**有到期节点**的板（Codex r2 MEDIUM-5）:
        #    picker 的 `ranked` 只收有到期节点的板, 原先推迟的「板-未来」根本不进
        #    队列 —— 让位判定对它完全空转, 却看起来像通过了。
        snoozed = {FIXTURE_SNOOZED_BOARD: (now + timedelta(days=1)).isoformat()}
        board_done = {"板-学习中": today_key}
        state_file = runner.state_path(vault)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            json.dumps({"board_done": board_done, "snoozed": snoozed}, ensure_ascii=False),
            encoding="utf-8",
        )

        # ── ③ picker（只读）+ ⑤ 推送 payload ─────────────────────────────
        payload, picker_conclusions, ranked_boards = face_picker(picker, vault, now, board_done, snoozed)
        (vault / "outputs" / "今日复习.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        noti_day, noti_title = face_notification(payload)

        # ── ① review_overview ───────────────────────────────────────────
        os.environ["VAULTS_ROOT"] = str(vaults_root)
        os.environ["ACTIVE_VAULT"] = vault_id
        # ⛔ 以 `python scripts/g68_...py` 启动时 sys.path[0] 是 `backend/scripts`,
        #    `app` 包不在其上 —— 显式把 `backend/` 加进来（与 pytest 的 rootdir
        #    行为对齐, 让脚本跑法与门跑法看到同一个 `app`）。
        if str(WT / "backend") not in sys.path:
            sys.path.insert(0, str(WT / "backend"))
        from app.config import reload_settings  # noqa: PLC0415

        reload_settings(overrides={"VAULTS_ROOT": str(vaults_root), "ACTIVE_VAULT": vault_id})
        from app.api.v1.endpoints import review_overview as ro  # noqa: PLC0415

        # 时钟注入: `_collect()` 内部读 `_display_now()`。⛔ 这是**注入时钟**,
        # 不是给被测行为打桩 —— 没有它就没有「同一 state 输入」这回事。
        # ⛔ 无条件还原: 本函数可能被同一进程里的测试直接调用, 留着补丁会让
        #    后续用例拿到一个钉死的时钟（而它们自己并不知道）。
        pinned_local = now.astimezone(display_tz)
        _orig_display_now = ro._display_now
        ro._display_now = lambda: pinned_local
        try:
            overview_conclusions, tonight_available = face_review_overview(ro, vaults_root, vault_id)
        finally:
            ro._display_now = _orig_display_now

        # ── ② review_app（静态断言）─────────────────────────────────────
        app_static = assert_review_app_has_no_due_algorithm(
            WT / "backend" / "app" / "api" / "v1" / "endpoints" / "review_app.py"
        )

        # ── ④ 两个 skill 脚本 ───────────────────────────────────────────
        inbox_day = face_skill_inbox(now_raw, tmp_root)
        recap_note = face_skill_recap()

        # ── 组装矩阵 ────────────────────────────────────────────────────
        # ⛔ 行索引 = fixture 自报的板清单 ∪ 各面实际报出来的板。前半让「所有面同时
        #    丢掉一块板」判红, 后半让「某面多报一块不存在的板」判红。
        boards = sorted(FIXTURE_BOARDS | set(picker_conclusions) | set(overview_conclusions))
        per_face: dict[str, dict] = {
            "picker": picker_conclusions,
            "review_overview": overview_conclusions,
            # 纯消费方: 四个字段一律不产出（它的契约是上面的静态断言）
            "review_app": {},
            # 无可比结论（理由见 face_skill_recap）
            "skill_recap": {},
            # 只产出日期结论, 且基准是刻意固定的 +08:00
            "skill_inbox": {b: {"display_day": inbox_day} for b in boards},
            # 推送只说「今天做哪块」: 它的 id 里那个日期既是它自己的「今天」,
            # 也是它复述的投影日 —— 两列同值, 都要参与比对。
            "notification": {b: {"display_day": noti_day, "projection_day": noti_day} for b in boards},
        }
        # ⛔ 推送点名的板必须**正是当前推荐板**（Codex r2 MEDIUM-6）: 早期版本只查
        #    「它是不是矩阵认识的某块板」—— 于是把标题换成另一块（甚至正处于推迟态的）
        #    板、或者干脆换成 None, 判据都毫无反应。推荐板 = picker 自己的 `ranked[0]`。
        #    ⚠ 长板名会被 `_title()` 截断加省略号, 故按**前缀**比而不是相等; 截断点
        #    由 picker 的 TITLE_LIMIT 决定, 不在本卡地盘内。
        recommended = ranked_boards[0] if ranked_boards else None
        if noti_day != MISSING:
            if noti_title is None:
                raise ContractError("推送在场却没有标题 —— 它点名了哪块板无从判定")
            # ⛔ 用生产器**自己的** `_title()` 重建期望标题, 逐字相等（Codex r4 MEDIUM-6）:
            #    先前按「以 `…` 收尾 + 长度顶到 TITLE_LIMIT」判截断, 于是
            #    `"📚 今日复习 · 板" + "…"*n` 这种重复省略号照样过。重建法把整类
            #    「拼一个看起来像截断的标题」一次性关掉 —— 截断规则归生产器, 不在本卡复述。
            expected_title = picker._title(recommended) if recommended is not None else None
            if noti_title != expected_title:
                raise ContractError(
                    f"推送标题 {noti_title!r} 不等于生产器对当前推荐板 {recommended!r} 应产出的 "
                    f"{expected_title!r}（按 picker._title() 重建）"
                )
        check_bucket_node_identity(per_face)
        check_producers_declaration(per_face, boards)
        matrix = build_matrix(per_face, boards)
        undeclared, declared = diff_matrix(matrix, ctx={"now": now, "display_tz": display_tz})

        # ── snooze / done / tonight_available 一致性（(f)）──────────────
        expected_tonight = pinned_local.hour < ro._SNOOZE_TONIGHT_HOUR
        tonight_ok = tonight_available == expected_tonight

        report = {
            "now": now_raw,
            "tz": tz_name,
            "display_tz": getattr(display_tz, "key", None),
            "boards": boards,
            "matrix": matrix,
            "census": {
                "review_overview": "产出全部五字段; display_day 取响应顶层 generated_at 的日期部分, "
                "projection_day 取响应中复述的 projection.date（两者都从响应读, 不现算）",
                "review_app": f"纯消费方, 五字段均不产出; 静态断言通过（共享 import: {app_static['imported_shared']}）",
                "picker": "产出全部五字段（buckets/date + active_snoozed/board_done 同源判定 + "
                "ranked 让位分区被观察）; 本卡只读",
                "skill_recap": recap_note,
                "skill_inbox": f"只产出 display_day={inbox_day}（基准固定 +08:00, 已登记分歧且带谓词）",
                "notification": f"产出 display_day/projection_day={noti_day}; 点名板={noti_title!r}",
            },
            "tonight_available": {
                "from_overview": tonight_available,
                "expected_now_hour_lt_20": expected_tonight,
                "now_local_hour": pinned_local.hour,
                "ok": tonight_ok,
            },
            "declared_divergences": declared,
            "undeclared_divergences": undeclared,
        }
        verdict = "PASS" if (not undeclared and tonight_ok) else "FAIL"
        report["verdict"] = verdict

        sys.stdout = _real_stdout
        _print_report(report)
        if out_json is not None:
            out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        if verdict != "PASS":
            # ⛔ FAIL 也要回放计算期缓冲（Codex r2 LOW-10）: 原先只在**异常**路径回放,
            #    于是正常判红时那些诊断打印全被吞掉 —— 排障的人拿不到被测模块当时说了
            #    什么。走 stderr, 不进 stdout, 「二跑逐字节相等」那条判据不受影响。
            captured = noise.getvalue()
            if captured:
                print("── 计算期被测模块的 stdout（排障用）──", file=sys.stderr)
                print(captured, file=sys.stderr)
        return 0 if verdict == "PASS" else 1
    except BaseException:
        sys.stdout = _real_stdout
        captured = noise.getvalue()
        if captured:
            print("── 计算期被测模块的 stdout（排障用）──", file=sys.stderr)
            print(captured, file=sys.stderr)
        raise
    finally:
        sys.stdout = _real_stdout
        if keep:
            print(f"[--keep] fixture 保留在 {tmp_root}")
        else:
            shutil.rmtree(tmp_root, ignore_errors=True)


def _print_report(report: dict) -> None:
    """确定性输出: 同一输入二跑必须逐字节相等（禁打印时刻/临时路径/内存地址）。"""
    print("═" * 78)
    print(f"CARD-G6-8 五面复习视图一致性契约 · now={report['now']} · tz={report['tz']}")
    print(f"显示时区解析结果: {report['display_tz']}")
    print("═" * 78)
    print("\n【面普查 census】")
    for face in FACES:
        print(f"  {face:<18} {report['census'][face]}")
    print("\n【五面矩阵】行=板, 列=面, 值逐字段")
    for board in report["boards"]:
        print(f"\n  ▸ {board}")
        for field in FIELDS:
            cells = report["matrix"][board][field]
            print(f"      {field:<12}")
            for face in FACES:
                value = cells[face]
                shown = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
                print(f"        {face:<18} {shown}")
    t = report["tonight_available"]
    print(
        f"\n【tonight_available】overview={t['from_overview']} "
        f"expected(now.hour={t['now_local_hour']} < 20)={t['expected_now_hour_lt_20']} "
        f"→ {'一致' if t['ok'] else '不一致'}"
    )
    print("\n【已登记分歧（不判红, 见 DECLARED_DIVERGENCES 与验收单台账）】")
    if not report["declared_divergences"]:
        print("  （无）")
    for row in report["declared_divergences"]:
        print(f"  DECLARED {diff_code(row)} 板={row['board']} 字段={row['field']} 面={row['face']} 值={row['value']}")
    print("\n【未登记分歧】")
    if not report["undeclared_divergences"]:
        print("  （无）")
    for row in report["undeclared_divergences"]:
        tail = (
            f"≠ 多数派{row['majority_faces']}={row['majority_value']}"
            if row["majority_faces"]
            else "（无严格多数派：产出方各执一词，每一方都如实列出）"
        )
        print(
            f"  DIFF {diff_code(row)} 板={row['board']} 字段={row['field']} 面={row['face']} 值={row['value']} {tail}"
        )
    print(f"\nverdict={report['verdict']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CARD-G6-8 五面复习视图一致性契约")
    ap.add_argument("--now", required=True, help="基准时刻 ISO-8601, 必须带时区偏移")
    ap.add_argument("--tz", default="Asia/Shanghai", help="CANVAS_TZ（显示/归日时区 IANA 名）")
    ap.add_argument("--json", dest="out_json", default=None, help="把完整报告写成 JSON")
    ap.add_argument("--keep", action="store_true", help="保留 tmp fixture 供排障")
    args = ap.parse_args(argv)
    try:
        return run(args.now, args.tz, Path(args.out_json) if args.out_json else None, args.keep)
    except ContractError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
