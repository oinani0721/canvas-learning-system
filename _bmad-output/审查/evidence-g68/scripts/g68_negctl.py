"""CARD-G6-8 负控 runner —— 「篡改任一面必红」的承重判据。

判据口径（与 CARD-G6-9c-R2 的 negctl 同一套纪律）:
  * 每段只跑它**声称守住**的那个 nodeid, 并要求**那一个** FAILED —— 不是
    「某处有失败」, 也不是「rc != 0」。
  * 除 FAILED 外还要求输出含该段**指定的文本锚**（哪一面、哪个字段红的）——
    否则「红了」可能红在别的原因上（import 崩、收集错误、另一条断言）。
  * 开跑前预检: 每个变异锚点在其目标文件里必须**恰好命中 1 次**, 否则整脚本
    abort —— 不允许「前几段印了 RED ✅、中途因锚点漂移而崩」。
  * `atexit` 无条件还原 + 五个目标文件跑前/跑后 `shasum -a 256` 逐字比对。

⛔ `scripts/daily_review_pick.py` 是 T4 地盘, 本卡只读: picker 这一面的负控只在
   **契约脚本的提取层**做（读成错值）, 一个字节都不碰 picker 源文件。
"""

import ast
import atexit
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review")
RO = ROOT / "backend/app/api/v1/endpoints/review_overview.py"
APP = ROOT / "backend/app/api/v1/endpoints/review_app.py"
INBOX = ROOT / "canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py"
RECAP = ROOT / "canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py"
SCRIPT = ROOT / "backend/scripts/g68_five_view_contract.py"
TARGETS = [RO, APP, INBOX, RECAP, SCRIPT]

PYTEST = ROOT / "backend/.venv/bin/pytest"
F = "tests/regression/test_g68_five_view_contract.py"

MAIN = f"{F}::test_five_view_matrix_is_field_wise_consistent"
APPGATE = f"{F}::test_review_app_has_no_independent_due_algorithm"
INBOXGATE = f"{F}::test_inbox_date_divergence_is_really_detected"

ORIGINAL = {t: t.read_bytes() for t in TARGETS}
SHA0 = {t: hashlib.sha256(b).hexdigest() for t, b in ORIGINAL.items()}


def restore():
    for t, b in ORIGINAL.items():
        if t.read_bytes() != b:
            t.write_bytes(b)


atexit.register(restore)


#: (目标文件, 原文, 变异文, 绑定 nodeid, 文本锚, 这一段声称守住什么)
SEGMENTS = [
    # ── ① review_overview ────────────────────────────────────────────
    (
        # ⚠ 锚点位置随 r1 HIGH-4 的修复而**迁移**: overview 的 display_day 现在绑
        #   响应顶层 `generated_at`, 不再走 `_display_today()`。而 `_display_today()`
        #   仍是「完成账的今天」(`_collect` → `_board_done_today`) 的唯一来源 ——
        #   所以改它显形在 **done** 列。红点换了地方不等于防线没了, 但锚必须跟着改,
        #   否则这一段量的就是另一回事了。
        "RO_DONE_DAY",
        RO,
        '    return d.isoformat() if d is not None else ""',
        '    return "1999-01-01" if d is not None else ""  # NEGCTL',
        MAIN,
        "G68DIFF|face=review_overview|field=done",
        "完成账的「今天」与 picker 的 payload['date'] 同一条换算",
    ),
    (
        # display_day 这一列的负控（RO_DONE_DAY 迁到 done 列之后, 这一列需要自己的段）:
        # 改响应顶层 generated_at —— 它是 overview「自己的今天」的唯一出门口。
        "RO_GENERATED_AT",
        RO,
        '        "generated_at": now.isoformat(timespec="seconds"),',
        '        "generated_at": "1999-01-01T00:00:00+08:00",  # NEGCTL',
        MAIN,
        "G68DIFF|face=review_overview|field=display_day",
        "总览页对外报的「此刻」与其余面的今天同一条换算",
    ),
    (
        "RO_BOARD_IDENTITY",
        RO,
        '        "bucket_rows": bucket_rows,',
        '        "bucket_rows": {k: [{**r, "board": r["board"] + "·NEGCTL"} for r in v]'
        " for k, v in bucket_rows.items()},  # NEGCTL",
        MAIN,
        "与 fixture 不符",
        "整块板从某一面消失时必须判红 —— r3 起先撞节点身份锚（红点迁移, 锚已跟改）",
    ),
    (
        # ⛔ 等长交换: `new` 与 `learning_queue` 在 fixture 里各 1 行, 交换后
        #    「逐桶行数 == 计数」那道漂移守卫照样过（它只发现长度变了）——
        #    本段证的正是矩阵比的是**身份**不是计数。
        "RO_BUCKET_SWAP",
        RO,
        '        "bucket_rows": bucket_rows,',
        '        "bucket_rows": {**bucket_rows, "new": bucket_rows["learning_queue"],'
        ' "learning_queue": bucket_rows["new"]},  # NEGCTL',
        MAIN,
        "G68DIFF|face=review_overview|field=bucket",
        "桶位身份（哪块板在哪个桶）跨面相等, 等长替换也必须判红",
    ),
    # ── ② review_app ─────────────────────────────────────────────────
    (
        "APP_DUE",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        "def _negctl_bare_due(node):  # NEGCTL\n"
        "    fsrs_due = node.get('fsrs_due')\n"
        "    return bool(fsrs_due)",
        APPGATE,
        "独立 due 算法",
        "review_app 不自造 due 算法",
    ),
    (
        "APP_SHARED_IMPORT",
        APP,
        "    _BUCKET_ORDER,\n",
        "",
        APPGATE,
        "共享桶序常量",
        "review_app 的桶序来自 import 而非本地复制",
    ),
    # ── ③ picker（只读 —— 只改契约脚本的提取层）───────────────────────
    (
        "PICKER_EXTRACT",
        SCRIPT,
        '    day = payload["date"]',
        '    day = "1999-01-01"  # NEGCTL',
        MAIN,
        "G68DIFF|face=picker|field=display_day",
        "picker 这一面真的进了矩阵（提取层读错值必被抓）",
    ),
    # ── ④ 两个 skill 脚本 ────────────────────────────────────────────
    (
        "INBOX_TZ",
        INBOX,
        "_TZ_SHANGHAI = timezone(timedelta(hours=8))",
        "_TZ_SHANGHAI = timezone(timedelta(hours=-7))  # NEGCTL",
        INBOXGATE,
        "竟然相同",
        "inbox 这一面真的进了矩阵（它的固定偏移被改成与显示时区同值即失去可区分性）",
    ),
    (
        "RECAP_MAIN",
        RECAP,
        "def main() -> int:",
        "def main_NEGCTL() -> int:",
        MAIN,
        "没有可调用的 main()",
        "recap 这一面「无可比结论」是关于它产出什么的结论, 不是「不看它」",
    ),
    # ── ⑤ 推送 payload（提取层）──────────────────────────────────────
    (
        "NOTI_EXTRACT",
        SCRIPT,
        "    day = noti_id[len(_NOTI_ID_PREFIX) :]",
        '    day = "1999-01-01"  # NEGCTL',
        MAIN,
        "G68DIFF|face=notification|field=display_day",
        "推送 payload 这一面真的进了矩阵",
    ),
    # ── Codex r1 的四组对照输入 —— 当轮全部**未被拦下**, 修复后必须各自判红 ──
    (
        # r1 HIGH-1: 通知缺席时该面原先返回 NOT_PRODUCED, 被比对循环整格过滤掉,
        #            于是「今天根本没发通知」表现为零分歧。
        "R1H1_NOTI_ABSENT",
        SCRIPT,
        '    noti = payload.get("notification")',
        "    noti = None  # NEGCTL",
        MAIN,
        "G68DIFF|face=notification",
        "声明产出方缺值必须判红, 不许用 NOT_PRODUCED 静默退出比较",
    ),
    (
        # r1 HIGH-2: 白名单原先只按 (面, 字段) 匹配 —— inbox 的日期改成 2099 年
        #            也照样落进「已登记」。修复后豁免带谓词, 只认固定 +08:00 的当日。
        "R1H2_INBOX_ABSURD_DAY",
        SCRIPT,
        '            return day if len(day) == 10 and day.count("-") == 2 else MISSING',
        '            return "2099-01-01"  # NEGCTL',
        MAIN,
        "G68DIFF|face=skill_inbox",
        "已登记分歧是「那一种已知取值」, 不是「那一格随便怎么错都行」",
    ),
    (
        # r1 HIGH-3: AST 门原先只认属性/裸名, 字段名写成**字符串常量**的两种写法
        #            （下标与 .get()）整条走过去。
        "R1H3_DICT_DUE_READ",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        "def _negctl_local_due(node, now):  # NEGCTL\n"
        '    return node["fsrs_due"] <= now and node.get("due_reason") == "scheduled"',
        APPGATE,
        "独立 due 算法",
        "字典下标与 .get() 形态的 due 字段读取同样算自造算法",
    ),
    (
        # r1 MEDIUM-5: 声明与实现同步缩减时对账仍通过。修复后每列至少两个产出方。
        "R1M5_SHRINK_DECLARATION",
        SCRIPT,
        '    "snoozed": ("review_overview", "picker"),',
        '    "snoozed": ("picker",),  # NEGCTL',
        MAIN,
        "跨面契约不成立",
        "把某列的声明产出方砍到只剩一个, 必须当场抛而不是静默退化成恒真判据",
    ),
    (
        # r1 HIGH-4: overview 的日期列原先是现算的, 把它响应里复述的投影日期改掉
        #            整门照样绿。修复后该列绑在响应上。
        "R1H4_RESPONSE_DATE",
        RO,
        '        "date": date_v,',
        '        "date": "1970-01-01",  # NEGCTL',
        MAIN,
        "G68DIFF|face=review_overview|field=projection_day",
        "消费方复述生产者的日期时走样必须判红（该列绑响应, 不是现算）",
    ),
    # ── Codex r2 的对照输入 —— 当轮全部**未被拦下**, 修复后必须各自判红 ──
    (
        # r2 HIGH-1: 两个产出方**同时**缺同一块板 ⇒ 取值集合只剩一个元素 ⇒ 零分歧。
        #            `_board_bucket_rows` 是两面共用的提取层, 从这里丢一块板即可复现。
        "R2H1_BOTH_MISSING",
        SCRIPT,
        "    return {b: tuple(sorted(v)) for b, v in out.items()}",
        '    return {b: tuple(sorted(v)) for b, v in out.items() if b != "\u677f-\u5230\u671f"}  # NEGCTL',
        MAIN,
        "与 fixture 不符",
        "两面同时缺一块板必须判红 —— r3 起先撞节点身份锚（红点迁移, 锚已跟改）",
    ),
    (
        # r2 HIGH-2: inbox 的日期原先是契约自己按 parse_now 算的, 不是它真实入口的产物。
        "R2H2_INBOX_ENTRY",
        INBOX,
        "def main() -> int:",
        "def main() -> int:\n    return 0  # NEGCTL 提前返回, 零产物",
        MAIN,
        "G68DIFF|face=skill_inbox",
        "inbox 这一列绑的是它真实入口的产物, 入口不产出即判红",
    ),
    (
        # r2 HIGH-3: 按语法形态枚举的 AST 门拦不住间接读法。
        "R2H3_INDIRECT_DUE_READ",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        'def _negctl_indirect_due(n, t, key="fsrs_due"):  # NEGCTL\n'
        "    return n.get(key) <= t",
        APPGATE,
        "独立 due 算法",
        "默认参数 / 模块常量等间接形态的 due 字段名同样算自造算法",
    ),
    (
        # r2 MEDIUM-5: 让位检查原先不验队列完整性, `ranked=[]` 照样过。
        "R2M5_RANKED_EMPTY",
        SCRIPT,
        "    check_ranked_yield_partition(ranked, yielded, require_exact_boards=due_boards)",
        "    check_ranked_yield_partition([], yielded, require_exact_boards=due_boards)  # NEGCTL",
        MAIN,
        "ranked 为空",
        "没有队列不该被读成「顺序没问题」",
    ),
    (
        # r2 MEDIUM-6: 推送点名原先只查「是不是认识的某块板」。
        "R2M6_NOTI_WRONG_BOARD",
        SCRIPT,
        "        recommended = ranked_boards[0] if ranked_boards else None",
        "        recommended = ranked_boards[-1] if ranked_boards else None  # NEGCTL",
        MAIN,
        "不等于生产器对当前推荐板",
        "推送标题必须等于生产器对 ranked[0] 应产出的那一串（r4 起判据改重建法, 锚已跟改）",
    ),
    # ── Codex r3 的对照输入 —— 当轮全部**未被拦下**, 修复后必须各自判红 ──
    (
        # r3 HIGH-1: AST 门按「整串相等」判字符串, 正则读法里字段名只是子串。
        "R3H1_REGEX_DUE_READ",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        "def _negctl_regex_due(text):  # NEGCTL\n"
        "    import re as _re\n"
        '    return _re.search(r"^fsrs_due: *(.*)$", text, _re.M)',
        APPGATE,
        "独立 due 算法",
        "字段名作为**子串**出现在正则里同样算自造算法（词边界匹配）",
    ),
    (
        # r3 HIGH-2: 板级锚挡不住「板内少一个节点」—— 两面同时丢同一个节点。
        "R3H2_NODE_DROPPED",
        SCRIPT,
        "            out.setdefault(board, []).append((node, bucket))",
        '            if node != "同板未来":  # NEGCTL\n'
        "                out.setdefault(board, []).append((node, bucket))",
        MAIN,
        "与 fixture 不符",
        "节点身份有自己的锚 —— 板还在、板级清单也完整时, 少一个节点必须判红",
    ),
    (
        # r3 MEDIUM-3: 清单对账原为 `<=`, 只抓多报不抓漏报。
        "R3M3_BOARDS_SHRINK",
        SCRIPT,
        'FIXTURE_BOARDS: frozenset[str] = frozenset({"板-到期", "板-新卡", "板-学习中", "板-脏日期", "板-今天晚些", "板-未来"})',
        'FIXTURE_BOARDS: frozenset[str] = frozenset({"板-到期", "板-新卡", "板-学习中", "板-脏日期", "板-今天晚些"})  # NEGCTL 清单漏报一块板',
        MAIN,
        "与 fixture 脱钩",
        "清单**漏报**也要抓到（对账是相等不是子集）",
    ),
    (
        # r3 MEDIUM-4: 队列只剩让位板时完整性检查退化。
        "R3M4_RANKED_TRIMMED",
        SCRIPT,
        "    check_ranked_yield_partition(ranked, yielded, require_exact_boards=due_boards)",
        "    check_ranked_yield_partition(\n"
        '        [r for r in ranked if r["board"] in yielded], yielded, require_exact_boards=due_boards\n'
        "    )  # NEGCTL",
        MAIN,
        "板集合与期望不符",
        "队列必须恰好覆盖有到期节点的板, 砍到只剩让位板时分区条件退化成恒真",
    ),
    (
        # r3 MEDIUM-5: fixture 原先推迟的是队尾板, `snoozed={}` 也全绿。
        "R3M5_SNOOZE_DROPPED",
        SCRIPT,
        "        payload, picker_conclusions, ranked_boards = face_picker(picker, vault, now, board_done, snoozed)",
        "        payload, picker_conclusions, ranked_boards = face_picker(picker, vault, now, board_done, {})  # NEGCTL",
        MAIN,
        "snoozed",
        "把推迟账整个丢掉必须判红（推迟的是一块本该排首位的板）",
    ),
    (
        # r3 MEDIUM-6: 任意短前缀被认作通知点名。
        "R3M6_SHORT_PREFIX",
        SCRIPT,
        "    return day, title if isinstance(title, str) else None",
        '    return day, "📚 今日复习 · 板" + "…" * 6  # NEGCTL 拼一个「看起来像截断」的短前缀标题',
        MAIN,
        "不等于生产器对当前推荐板",
        "标题按生产器 _title() 重建逐字相等 —— 重复省略号拼出的短前缀不算点名",
    ),
    (
        # MISSING 路径本身的负控: 节点身份锚上线后, 前两段的红点迁走了, 这条路径
        # 需要一个**仍然走得到它**的变异 —— 让一个声明产出方在某块板上没有值。
        "MISSING_PATH",
        SCRIPT,
        '            "skill_inbox": {b: {"display_day": inbox_day} for b in boards},',
        '            "skill_inbox": {b: {"display_day": inbox_day} for b in boards if b != "板-到期"},  # NEGCTL',
        MAIN,
        "该面声称产出却缺了这块板",
        "声明产出方在某块板上没有值 ⇒ MISSING ⇒ 判红",
    ),
    # ── Codex r4 的对照输入 —— 当轮全部**未被拦下**, 修复后必须各自判红 ──
    (
        # r4 HIGH-1: `r"\bfsrs_due\b"` 里字段名紧邻字母 b, 词边界规则失效。
        "R4H1_BOUNDARY_REGEX",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        "def _negctl_boundary_due(raw):  # NEGCTL\n"
        "    import re as _re\n"
        '    return _re.search(r"\\bfsrs_due\\b: *(.*)$", raw, _re.M)',
        APPGATE,
        "独立 due 算法",
        "正则源码里字段名紧邻字母时仍算读取（白名单式判据, 不靠边界规则）",
    ),
    (
        # r4 HIGH-2: 页面模板里加一处自判到期的 JS —— 身份豁免原先只看赋值名在不在。
        "R4H2_TEMPLATE_JS_DUE",
        APP,
        "const due = humanizeDue(n.fsrs_due, nowMs);",
        "const due = humanizeDue(n.fsrs_due, nowMs);\n"
        "const negctlDue = rows.filter(r => Date.parse(r.fsrs_due) <= nowMs);",
        APPGATE,
        "碰 due 字段的调用点变了",
        "模板里碰 due 的调用点按身份冻结 —— 多一处就要人判它还算不算纯消费",
    ),
    (
        # r4 MEDIUM-4: 形参名不进赋值检查, 函数体里读它又被模块级同名 import 豁免。
        "R4M4_PARAM_SHADOW",
        APP,
        "review_app_router = APIRouter()",
        "review_app_router = APIRouter()\n\n\n"
        'def _negctl_shadow(_BUCKET_ORDER=("future", "new")):  # NEGCTL\n'
        "    return list(_BUCKET_ORDER)",
        APPGATE,
        "独立 due 算法",
        "形参遮蔽同名 import 同样算自造（ast.arg 也在射程内）",
    ),
    (
        # r4 MEDIUM-5: 「它本该排首位」这个前提原先是假设的, 漂移了也没人知道。
        "R4M5_PREMISE_DRIFT",
        SCRIPT,
        'FIXTURE_SNOOZED_BOARD = "板-到期"',
        'FIXTURE_SNOOZED_BOARD = "板-新卡"  # NEGCTL 换一块本来就不在首位的板',
        MAIN,
        "fixture 前提已漂移",
        "「推迟让出首位」的参照必须实跑验证, 前提不成立要当场说",
    ),
    (
        # r4 MEDIUM-3: 节点锚与提取层同步缩减, 子集对账两边都过。
        "R4M3_NODE_ANCHOR_SHRINK",
        SCRIPT,
        '        ("板-到期", "规范到期"),',
        '        # ("板-到期", "规范到期"),  # NEGCTL 锚里漏报一个节点',
        MAIN,
        "与 fixture 脱钩",
        "节点锚**漏报**也要抓到（对账是相等不是子集）",
    ),
]


def precheck() -> None:
    bad = []
    for key, target, old, _new, _nid, _anchor, _claim in SEGMENTS:
        hits = target.read_text(encoding="utf-8").count(old)
        if hits != 1:
            bad.append(f"   {key} @ {target.name}: 命中 {hits} 次（应 1）")
    if bad:
        print("⛔ 预检失败, 拒绝开跑（锚点已随代码漂移）:")
        print("\n".join(bad))
        raise SystemExit(2)


def failure_block(out: str, short: str) -> str:
    """只取**这个 nodeid 自己的失败块**。

    ⛔ Codex r1 MEDIUM-7 实证: 直接在整份 pytest 输出里找文本锚会误判 —— traceback
    会把失败点**之前**那些**已经通过**的断言的源码一并显示出来, 于是「锚命中」可能
    命中的是一条通过了的断言的字面量。判据必须缩到失败块内。

    pytest 的失败块形如:
        ______________________ test_xxx _______________________
        <traceback 与断言输出>
    到下一个 `____ test_yyy ____` 或 `=== short test summary info ===` 为止。

    ⛔ 边界必须认「**连续**下划线」的测试分隔线（Codex r2 MEDIUM-8）: pytest 在
    **同一个测试内部**用 `_ _ _ _ _`（下划线之间有空格）分隔 traceback 的各帧。
    原来的判据只看「以 _ 开头、以 _ 结尾、_ 够多」, 于是把帧分隔线当成了下一个测试
    的边界, 把真正的异常输出截掉。
    """
    # `______ test_xxx ______`: 两端各有一段**连续**下划线（≥3）, 中间是名字。
    boundary = re.compile(r"^_{3,}\s.*\s_{3,}$")
    lines = out.splitlines()
    start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if boundary.match(s) and short in s:
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("=") and "short test summary" in s:
            end = j
            break
        if boundary.match(s) and short not in s:
            end = j
            break
    return "\n".join(lines[start:end])


_CAPTURED = re.compile(r"^-+\s*Captured .*-+$")


def error_lines(block: str) -> str:
    """失败块里 pytest 真正的**错误输出**行（前缀 `E `）。

    ⛔ 先切掉 `----- Captured stdout call -----` 之后的部分（Codex r3 MEDIUM-7）:
    被测试 `print()` 出来的内容原样显示, 一行 `print("E 独立 due 算法")` 就能让锚
    命中 —— 而它根本不是失败原因。捕获段里的东西一律不作失败归因。

    ⛔ 只在这些行里找文本锚（Codex r2 MEDIUM-7）: 失败块里同时包含被回显的**源码**,
    于是一条 `assert True, "……锚……"` 的源码字面量也能让锚命中 —— 红是红了, 但红的
    原因不是那条声称的断言。`E ` 前缀的行才是实际抛出来的那条。
    """
    lines = block.splitlines()
    for i, ln in enumerate(lines):
        if _CAPTURED.match(ln.strip()):
            lines = lines[:i]
            break
    return "\n".join(ln for ln in lines if ln.strip().startswith("E "))


def run_nodeid(nodeid: str) -> tuple[int, str]:
    proc = subprocess.run(
        [str(PYTEST), "-q", "-p", "no:cacheprovider", nodeid],
        cwd=str(ROOT / "backend"),
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(Path.home())},
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    precheck()
    print(f"CARD-G6-8 负控 · {len(SEGMENTS)} 段 · 每段要求「指定 nodeid FAILED 且输出含指定文本锚」\n")
    bad = 0
    for key, target, old, new, nodeid, anchor, claim in SEGMENTS:
        src = target.read_text(encoding="utf-8")
        assert src.count(old) == 1
        mutated = src.replace(old, new, 1)
        target.write_text(mutated, encoding="utf-8")
        try:
            # ⛔ 变异后必须仍是**合法 Python**: 一个写坏的变异串（例如把行尾逗号
            #    注释掉）会让 pytest 以 rc=4 收集失败收场 —— 那不是「门抓到了」,
            #    是这一段负控本身坏了。不当场说破就会被当成红。
            try:
                ast.parse(mutated)
            except SyntaxError as e:
                print(f"[⛔] {key:<20} 变异后语法不成立: {e} —— 这一段负控写坏了, 不是门的结论")
                bad += 1
                continue
            rc, out = run_nodeid(nodeid)
        finally:
            target.write_text(src, encoding="utf-8")
        short = nodeid.split("::")[-1]
        failed = f"FAILED {nodeid}" in out or f"FAILED {F}::{short}" in out
        # ⛔ 锚只在**该 nodeid 自己的失败块**里找（见 failure_block 的说明）。
        hit = anchor in error_lines(failure_block(out, short))
        ok = rc != 0 and failed and hit
        flag = "[✅]" if ok else "[⛔]"
        if not ok:
            bad += 1
        print(f"{flag} {key:<20} rc={rc} FAILED={failed} 文本锚={'命中' if hit else '未命中'}")
        print(f"     守: {claim}")
        print(f"     绑: {short}")
        print(f"     锚: {anchor!r}")
        if not ok:
            print("     ── 实得输出尾部 ──")
            for line in out.strip().splitlines()[-12:]:
                print(f"     | {line}")
        print()

    print("\n跑前/跑后 sha256 逐字比对:")
    for t in TARGETS:
        now = hashlib.sha256(t.read_bytes()).hexdigest()
        ok_sha = now == SHA0[t]
        # ⛔ 还原失败必须进 bad 并影响退出码（Codex r2 MEDIUM-9）: 原先只打一个 ⛔
        #    就算了, rc 照样 0 —— 「变异残留在树上」这件事会被读成通过。
        if not ok_sha:
            bad += 1
        mark = "✅" if ok_sha else "⛔"
        print(f"{mark} {t.name}")
        print(f"     跑前 {SHA0[t]}")
        print(f"     跑后 {now}")

    print(f"\n段数 {len(SEGMENTS)} 期望RED, 不合判据 {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
