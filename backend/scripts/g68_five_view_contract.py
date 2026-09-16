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

FIELDS = ("bucket", "display_day", "snoozed", "done")

#: 逐字段的**声明**产出方 —— 来自面普查（census）, 不是从数据里反推。
#: ⛔ 必须是声明: 从数据反推等于「谁没产出就当它不该产出」, 那正是上面 MISSING
#: 要堵的洞。`run()` 会把声明与实测对照, 两边不符即 ContractError。
FIELD_PRODUCERS: dict[str, tuple[str, ...]] = {
    "bucket": ("review_overview", "picker"),
    "display_day": ("review_overview", "picker", "skill_inbox", "notification"),
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
DECLARED_DIVERGENCES: frozenset[tuple[str, str, str]] = frozenset(
    {
        (
            "skill_inbox",
            "display_day",
            "inbox_preview 的人话时区是刻意固定的 +08:00（:423/:430）, "
            "与 local_tz.display_tz() 在非 +08:00 机器上分叉; "
            "是否统一交产品（台账 ③, 本卡不改）",
        ),
    }
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


def face_picker(picker, vault: Path, now: datetime, board_done: dict, snoozed: dict) -> tuple[dict, dict]:
    """③ picker（**只读**）—— 返回 (payload, 板级结论)。

    picker 的 snooze/done 结论不落 payload（「完成状态不进 projection」是 A2 的
    明文纪律）, 它表达在 `ranked` 的**让位分区**上。所以这里取它**实际用来判定
    的那两个函数/键**: `active_snoozed()`（与页面侧 `_snoozed_active` 是同一个
    函数）与 `board_done.get(board) == payload["date"]`（与 picker :1011 的
    `_today_key` 逐字同源）—— 不另写一套判定。
    """
    payload, _ranked = picker.build_payload(
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
    conclusions = {
        board: {
            "bucket": rows,
            "display_day": day,
            "snoozed": board in awake,
            "done": board_done.get(board) == day,
        }
        for board, rows in buckets.items()
    }
    return payload, conclusions


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
    day = ro._display_today(ro._display_now())
    snoozed_boards = set(entry["snoozed"])
    done_boards = set(entry["board_done"])
    return {
        board: {
            "bucket": bucket_rows,
            "display_day": day,
            "snoozed": board in snoozed_boards,
            "done": board in done_boards,
        }
        for board, bucket_rows in buckets.items()
    }, collected["tonight_available"]


# ─────────────────────────── 面：review_app（静态）───────────────────────────

#: review_app 允许从 review_overview 引进来的共享名（:60-66 的 import 清单）。
_APP_SHARED_IMPORTS = ("_BUCKET_CN", "_BUCKET_ORDER", "_DONE_NOTE", "_SNOOZE_NOTE", "_STATUS_META")

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

    # 可执行代码里对 due 字段的**属性/下标读取**（字符串常量除外 —— 页面 JS 是
    # 一个大字符串, 它是 /overview JSON 的纯消费方, 不在本断言的射程内）。
    reads: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _DUE_ALGO_MARKERS:
            reads.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in _DUE_ALGO_MARKERS and isinstance(node.ctx, ast.Load):
            if node.id not in imported:
                reads.add(node.id)
    offenders += sorted(reads - set(offenders))
    if offenders:
        raise ContractError(
            f"review_app 出现独立 due 算法的迹象（在可执行代码里定义/读取 {offenders}）—— "
            "它必须是 /overview 投影的纯消费方"
        )
    return {"imported_shared": sorted(imported & set(_APP_SHARED_IMPORTS)), "offenders": []}


# ───────────────────────────── 面：两个 skill 脚本 ─────────────────────────────


def face_skill_inbox(now_raw: str) -> str:
    """④b clear-inbox/inbox_preview.py —— 它的「今天」。

    `parse_now()` 把裸时刻按**固定 +08:00** 解释（:430 `_TZ_SHANGHAI`）, 带偏移的
    时刻则原样收下; 页面人话再按同一个 +08:00 格式化（:606）。所以它的日期结论 =
    `parse_now(--now).astimezone(+08:00).date()`。
    """
    sys.path.insert(0, str(WT / "canvas-vault" / ".claude" / "skills" / "clear-inbox" / "scripts"))
    import inbox_preview  # noqa: PLC0415  — 路径在运行期才确定

    dt = inbox_preview.parse_now(now_raw)
    return dt.astimezone(inbox_preview._TZ_SHANGHAI).date().isoformat()


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
    """
    noti = payload.get("notification")
    if noti is None:
        return NOT_PRODUCED, None
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


def check_producers_declaration(per_face: dict[str, dict], boards: list[str]) -> None:
    """声明 vs 实测对账 —— 防「声明表与代码各说各话」。

    ⛔ 两个方向都查: 声明产出却一块板都没给出值 = 该面其实没进矩阵（白名单在给
    一件不存在的事发豁免）; 未声明却产出了值 = 声明表漏了一个面, 它的分歧永远
    不会被比到。
    """
    for field, producers in FIELD_PRODUCERS.items():
        for face in FACES:
            produced = any(field in per_face.get(face, {}).get(b, {}) for b in boards)
            if face in producers and not produced:
                raise ContractError(
                    f"面 {face} 被声明产出字段 {field}, 实测一块板都没给出值 —— 它没有真正进矩阵, 对它的比对是空转"
                )
            if face not in producers and produced:
                raise ContractError(
                    f"面 {face} 产出了字段 {field} 却不在 FIELD_PRODUCERS 声明里 —— "
                    "它的分歧不会被比到, 补声明或说明为何不纳入"
                )


def diff_matrix(matrix: dict) -> tuple[list[dict], list[dict]]:
    """逐板逐字段比对 → (未登记分歧, 已登记分歧)。

    ⛔ 逐板逐字段全量比对, 不做「差异数 ≤ N」之类的计数式判据。
    """
    undeclared: list[dict] = []
    declared: list[dict] = []
    declared_keys = {(face, field) for face, field, _ in DECLARED_DIVERGENCES}
    for board in sorted(matrix):
        for field in FIELDS:
            cells = matrix[board][field]
            producing = {f: v for f, v in cells.items() if v != NOT_PRODUCED}
            if len(producing) < 2:
                continue  # 少于两面产出该字段 ⇒ 无从比对（census 里已如实标注）
            values = {json.dumps(v, ensure_ascii=False, sort_keys=True, default=str) for v in producing.values()}
            if len(values) == 1:
                continue
            # 按取值分组。
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
                    (declared if (face, field) in declared_keys else undeclared).append(row)
    return undeclared, declared


# ─────────────────────────────────── 主流程 ───────────────────────────────────


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
        vault = build_vault(vaults_root, vault_id, nodes)

        # ── state: 一块板推迟到明天, 一块板今天标完成 ────────────────────
        today_key = now.astimezone(display_tz).date().isoformat()
        snoozed = {"板-未来": (now + timedelta(days=1)).isoformat()}
        board_done = {"板-学习中": today_key}
        state_file = runner.state_path(vault)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            json.dumps({"board_done": board_done, "snoozed": snoozed}, ensure_ascii=False),
            encoding="utf-8",
        )

        # ── ③ picker（只读）+ ⑤ 推送 payload ─────────────────────────────
        payload, picker_conclusions = face_picker(picker, vault, now, board_done, snoozed)
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
        inbox_day = face_skill_inbox(now_raw)
        recap_note = face_skill_recap()

        # ── 组装矩阵 ────────────────────────────────────────────────────
        boards = sorted(set(picker_conclusions) | set(overview_conclusions))
        per_face: dict[str, dict] = {
            "picker": picker_conclusions,
            "review_overview": overview_conclusions,
            # 纯消费方: 四个字段一律不产出（它的契约是上面的静态断言）
            "review_app": {},
            # 无可比结论（理由见 face_skill_recap）
            "skill_recap": {},
            # 只产出日期结论, 且基准是刻意固定的 +08:00
            "skill_inbox": {b: {"display_day": inbox_day} for b in boards},
            # 推送只说「今天做哪块」: 日期结论对全部板成立
            "notification": {b: {"display_day": noti_day} for b in boards},
        }
        check_producers_declaration(per_face, boards)
        matrix = build_matrix(per_face, boards)
        undeclared, declared = diff_matrix(matrix)

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
                "review_overview": "产出 bucket/display_day/snoozed/done 四字段（_collect → _summarize → _gate_buckets）",
                "review_app": f"纯消费方, 四字段均不产出; 静态断言通过（共享 import: {app_static['imported_shared']}）",
                "picker": "产出四字段（buckets/date + active_snoozed/board_done 同源判定）; 本卡只读",
                "skill_recap": recap_note,
                "skill_inbox": f"只产出 display_day={inbox_day}（基准固定 +08:00, 已登记分歧）",
                "notification": f"只产出 display_day={noti_day}; 点名板={noti_title!r}",
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
        print(f"  DECLARED 板={row['board']} 字段={row['field']} 面={row['face']} 值={row['value']}")
    print("\n【未登记分歧】")
    if not report["undeclared_divergences"]:
        print("  （无）")
    for row in report["undeclared_divergences"]:
        tail = (
            f"≠ 多数派{row['majority_faces']}={row['majority_value']}"
            if row["majority_faces"]
            else "（无严格多数派：产出方各执一词，每一方都如实列出）"
        )
        print(f"  DIFF 板={row['board']} 字段={row['field']} 面={row['face']} 值={row['value']} {tail}")
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
