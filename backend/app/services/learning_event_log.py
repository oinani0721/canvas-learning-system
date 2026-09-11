"""批次3' 2-4 — 统一学习事件日志 (MEM-FLYWHEEL-2026-07-22, 对账 schema 四要素)。

`<vault>/learning_events.jsonl` append-only: frontmatter 仍是真相源 (不改架构),
日志提供「过程可回放、图可重建」兜底 — 会话记忆层从「丢图即永失」变为可重放。

Schema 四要素 (ChatGPT 对账采纳):
  - event_id: 幂等键 (调用方构造稳定值, 重放/重试不双写)
  - event_version: schema 版本 (当前 1)
  - recorded_at / effective_at: 双时间戳 (记录时刻 vs 业务生效时刻,
    补录历史事件时两者分离)
  - event_type: 限 9 类核心动作 (EVENT_TYPES), 未知类型拒绝 — 防事件膨胀
    (callout_ingested 2026-07-23 对账评审入集后 "8 类" 注释曾未同步)

写点 (批次3' 接入 4 个, node_derived 留批次4' 拆分补强):
  backend: candidate_created (蒸馏) / candidate_accepted / candidate_disputed
           (= dispute 三件套第三件「可追溯」suppression log) / session_archived
  vault:   answer_scored / answer_abandoned (quiz-answer) / exam_created
           (start-exam-board) — SKILL 静态 python 直接 append 同一文件
"""

from __future__ import annotations

import errno
import fcntl
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

EVENT_VERSION = 1

#: 核心动作白名单 — 新增类型必须走对账评审, 不得随手扩
#: (callout_ingested 经 2026-07-23 燃料策略对账批次5' 方案评审加入)
EVENT_TYPES = frozenset(
    {
        "node_derived",
        "exam_created",
        "answer_scored",
        "answer_abandoned",
        "candidate_created",
        "candidate_accepted",
        "candidate_disputed",
        "session_archived",
        "callout_ingested",
    }
)

#: 进程内快路径 (CARD-G3-3 (b) 保留): 同进程多线程先在这里排队, 省掉一次系统调用。
#: ⛔ 它**不是**并发防线 —— threading.Lock 只在本进程内成立, 而账本的真实写者
#: 有**四方** (backend 进程、quiz-answer SKILL 的独立 python3、start-exam-board、
#: ai-linked-doc) —— 其中 ai-linked-doc 的一行式追加**未参与**本锁协议, 见验收单 §十.12,
#: 跨进程互斥只能靠下面的 fcntl 记录锁。
_write_lock = threading.Lock()

#: 账本追加锁的等待上限。追加本身是「读尾字节 + 写一行 + fsync」的毫秒级操作,
#: 30s 足够排掉任何正常争用; 超时说明有进程卡死, 此时**不写**比无锁硬写安全。
LEDGER_LOCK_TIMEOUT_S = 30.0
_LOCK_POLL_S = 0.02


def _lock_exclusive(fd: int, timeout: float) -> bool:
    """跨进程排他锁 (POSIX 记录锁)。取到返回 True, 超时返回 False。

    ⚠️ 选型理由已按独立复核更正 (2026-09-05): 原注释写「flock 同进程两个 fd 会
    自锁死」—— 复核实测**证伪**: 旧 fd 仍开着时第二个 fd 确实被阻塞, 但关掉旧 fd
    后即可取得, 「重复调用本身不会自锁」。所以那不是选 lockf 的理由。
    真正的理由只有一条: 本模块把「查重 → LF 守卫 → 写」全放在**同一个 fd** 上做,
    需要的只是一把可用的跨进程排他锁; `lockf` 与 `flock` 都能满足, 选 lockf 是
    因为它与写点侧 (per-node 锁文件) 用的是同一套语义, 便于统一推理。
    ⛔ 但 lockf 的 per-process 语义**不能**被用来掩盖 fd 生命周期问题 ——
    「本进程关掉指向该文件的任意一个 fd ⇒ 该文件上全部记录锁整体释放」这条性质
    要求 open/lock/scan/write/close 必须在**同一段互斥区**内完成, 见 append_event。
    ⛔ 超时不静默降级为「没锁也写」: 那正是丢事件的路径。
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError as e:
            # ⛔ 只有「被别人占着」才该继续等 (EACCES/EAGAIN)。别的 errno
            # (ENOLCK / EBADF / EINVAL / 文件系统不支持记录锁) 是**真错误**,
            # 空等满超时只会把真因藏起来, 让调用方以为是争用。
            if e.errno not in (errno.EACCES, errno.EAGAIN):
                logger.error("[learning-events] 取账本锁失败 (errno=%s, 非争用): %s", e.errno, e)
                return False
            if time.monotonic() >= deadline:
                return False
            time.sleep(_LOCK_POLL_S)


def _iter_lines(raw: bytes):
    """按**物理 LF** 切行 —— 与 `for line in open(path)` 逐字同语义。

    ⛔ 不能用 `str.splitlines()` (2026-09-05 独立复核 + 本地实测): 它额外在
    `\v \f \x1c \x1d \x1e \x85(NEL) \u2028 \u2029` 上切行, 而这些字符**可以
    合法出现**在账本某行的字符串值里 (§6.1 的字符轴只强制 5 个身份字段)。
    后果实测: 一条含裸 U+2028 的合法记录被切成两个碎片 → 都 JSON 解析失败 →
    **查重漏掉那个 event_id** → 同一事件被写第二遍 → 幂等键唯一性破裂 →
    校验器判整个账本不合规 → 此后所有评分都进不来。
    (基线 `[True, False]` → 引入 splitlines 后 `[True, True]`, 账本 1 行变 2 行。)
    """
    text = raw.decode("utf-8")
    parts = text.split("\n")
    if text.endswith("\n"):
        parts = parts[:-1]  # 末尾 LF 之后的空串不是一行 (与文件迭代同款)
    return parts


def _read_all(fd: int) -> bytes:
    """把整个文件读出来 —— **只用这一个 fd**。

    ⛔ 为什么不是 `path.read_bytes()` / `open(path)`: POSIX 记录锁的释放语义是
    「本进程关掉指向该文件的**任意**一个 fd ⇒ 该文件上的全部记录锁整体释放」。
    于是一句人畜无害的 `with open(path) as f: ...` 在收尾时就把锁悄悄丢了,
    之后的 write 是**裸奔**的 —— 而「取到锁没有」这类门只看取锁那一刻, 看不见它。
    (2026-09-05 于 macOS 实测复现: 持锁后做一次无关的 open+close, 另一个进程
     立刻就能拿到同一把锁。)
    """
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(fd, 1 << 20)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


#: 复习事件族的 schema 扩展 marker (docs/learning-events-schema-v1.md §6.1 冻结)。
#: 乱序判据只对这一族成立 —— 别的事件类型没有「水位线」概念。
_REVIEW_EXT_MARKER = "review/1"


def _instant(value):
    """ISO 时刻 → aware datetime; 不可解析/无时区返回 None (不做裁决, 只排序)。"""
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def _log_path() -> Path:
    from app.config import settings

    canvas_base = getattr(settings, "CANVAS_BASE_PATH", None) or "/vaults/canvas-vault"
    return Path(canvas_base) / "learning_events.jsonl"


#: `event_id` 的**字符轴**禁止集 — 与校验器 `validate_learning_events.py::
#: FORBIDDEN_CODEPOINT_RANGES` 是同一个闭合集 (C0 / DEL / C1 / LS-PS / 代理区 /
#: Unicode noncharacters)。
#: ⛔ 这里重列一份而不是 import 本体: `backend/app/**` 至今不依赖 `backend/scripts/**`
#: (全仓零先例), 加 sys.path hack 会同时弄脏 pyright 面与打包面。防漂移不靠自觉 —
#: `tests/regression/test_learning_event_log.py::test_g33r2_shape_gate_charset_matches_validator`
#: 逐范围断言两侧**相等**, 校验器扩集而这里没跟上 = 当场报红。
#: ⛔ 为什么必须同口径、不能更窄: 窄了就留下「写得进、读不回」——
#: 一条含 U+2028 的 event_id 能被本函数写进账本, 而校验器读侧对该码点 fail-closed,
#: 判的是**整个账本**不合规 ⇒ 那个 vault 从此所有评分都进不来。这正是
#: `value_charset_problems` docstring 记录的 round-1 BLOCKER 那条数据丢失路径。
_EVENT_ID_FORBIDDEN_RANGES: tuple[tuple[int, int], ...] = (
    (0x0000, 0x001F),  # C0 控制符 (含 \n \r \t)
    (0x007F, 0x007F),  # DEL
    (0x0080, 0x009F),  # C1 控制符 (含 U+0085 NEL — 在终端里看起来就是个空格)
    (0x2028, 0x2029),  # LINE / PARAGRAPH SEPARATOR
    (0xD800, 0xDFFF),  # 代理区 — 孤立代理会让 utf-8 编码直接失败
    (0xFDD0, 0xFDEF),  # Unicode noncharacters
) + tuple(
    # 每个平面末尾的 U+xFFFE / U+xFFFF (17 个平面共 34 个码点)
    (0x10000 * _plane + 0xFFFE, 0x10000 * _plane + 0xFFFF)
    for _plane in range(17)
)

#: `event_id` 长度上限 — 幂等键要参与**每一行**的全文件扫描比较, 并原样进 receipt YAML。
#: 2026-09-08 只读普查: live 账本现存最长 62 字符, 512 留了两个数量级余量。
#: 它挡的是「把一整篇批注塞进 id」这类形态, 不是任何正常业务 id。
_EVENT_ID_MAX_LEN = 512


def _event_id_shape_problems(event_id: object) -> list[str]:
    """`event_id` 的形态问题清单 (空清单 = 形态合规)。

    ⛔ 只管**形态**, 不管命名法。既有合法输入里有 `x-1` / `wrong` 这种**无
    `type:` 前缀**的 id (regression 样本), 5 个 backend 调用点各带自己的前缀
    (`archive:` / `callout:` / `accept:` / `dispute:` / `cand:`), live 账本里
    还有含**空格**与中文的 `exam:CS 61B-2026-08-11-1349`、无 `#` 段的
    `derive:规划代理的特点`。任何「必须匹配 `<type>:<x>#<y>`」的正则都会当场拒掉
    生产数据 — 2026-09-08 只读普查实证, 设计稿的那条正则据此作废
    (存档 `_bmad-output/审查/evidence-g33r2/event-id-shapes-*.txt`)。

    ⛔ 首尾空白**拒绝**而不是 strip: 与 quiz-answer 写点入口同款理由 —— strip 会把
    上游两个本来不同的 id 撞成一个, 那是替上游做主。带空白 = 上游 bug, 报给它。

    ⛔ 报出**码点**是硬要求: C1 与 LS/PS 在终端和编辑器里大多不可见,
    只说「含非法字符」等于让上游去猜 (与校验器 `_codepoint_problem` 同款立场)。
    """
    if not isinstance(event_id, str):
        return [f"event_id 必须是字符串, 实见 {type(event_id).__name__}"]
    if not event_id:
        return ["event_id 为空 (幂等键必填)"]
    problems: list[str] = []
    if event_id != event_id.strip():
        problems.append(
            f"event_id 首尾含空白 ({event_id!r}) — 幂等键的字面即身份, "
            "带空白的写法会与不带的各算一条 (双写账本 + 双吃 mastery)"
        )
    for ch in event_id:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in _EVENT_ID_FORBIDDEN_RANGES):
            problems.append(
                f"event_id 含非规范码点 U+{cp:04X} — 该码点在 JSONL 行 / receipt YAML "
                f"的某一层有特殊语义或不可编码, 写进去就读不回原值; "
                f"值片段: {event_id[:40]!r}"
            )
            break
    if len(event_id) > _EVENT_ID_MAX_LEN:
        problems.append(
            f"event_id 过长 ({len(event_id)} 字符 > {_EVENT_ID_MAX_LEN}) — 幂等键要参与每行比较并原样进 receipt YAML"
        )
    return problems


def append_event(
    event_type: str,
    event_id: str,
    node_id: str = "",
    payload: Optional[dict[str, Any]] = None,
    effective_at: Optional[str] = None,
    out_of_order: bool = False,
) -> bool:
    """append-only 落一条学习事件; event_id 已存在 → 幂等跳过。

    永不抛异常 (记录失败不得影响主链) — 返回 False 表示未写入
    (幂等跳过 / 取锁超时 / 短写 / IO 失败, 区别见日志)。

    `out_of_order=True` = **调用方显式声明**这是一条补录/重放事件
    (schema v1 §6.2 :270 的补录通道)。写入时给 `payload.out_of_order` 补上冻结的
    布尔 `true`; 该行按 §6.2 不进 pending 集合, 消费侧不会拿它推进 frontmatter。
    仅对复习事件族 (`payload.schema_ext == "review/1"`) 生效 —— 别的 event_type
    没有水位线语义。
    """
    try:
        if event_type not in EVENT_TYPES:
            logger.warning("[learning-events] 拒绝未知 event_type=%r (9 类白名单)", event_type)
            return False
        if not event_id:
            logger.warning("[learning-events] 拒绝空 event_id (幂等键必填)")
            return False
        # ⛔ CARD-G3-3-R2 形态门: 空判之后、**任何写入之前**。
        # 与上一条同形 fail-closed —— `return False` 而不是抛, 因为本函数的契约
        # 就是「永不抛异常 (记录失败不得影响主链)」, 抛出去会把一个日志问题
        # 升级成主链故障。拒因进 warning 且带码点, 上游才修得动。
        shape_problems = _event_id_shape_problems(event_id)
        if shape_problems:
            logger.warning("[learning-events] 拒绝形态非法的 event_id: %s", shape_problems)
            return False

        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        # ⛔ CARD-G3-3 (b): 跨进程锁必须罩住「查重 → LF 守卫 → 写」**整段**,
        # 而不只是那一次 write。幂等判据是「文件里有没有这个 event_id」——
        # 两个进程各自扫完都没看到, 就各写一条同 id 的行, event_id 全文件唯一
        # 被破坏; 而校验器对重复 id 判**整个账本**不合规, 从此所有评分都进不来。
        # 锁挂在账本 fd 上 (无需额外锁文件); 进程崩溃时内核自动释放。
        # ⛔ O_RDWR 而不是 O_WRONLY: 持锁期间的查重与 LF 守卫都必须走**这同一个
        # fd**(见 `_read_all` 的释放语义说明), 所以它得可读。
        # ⛔ 线程锁必须罩住 **open → lock → scan → write → close** 的完整生命周期
        # (独立复核 H1 实测): 上一版把 `os.close(fd)` 放在 `with _write_lock` **之外**,
        # 于是线程 A 退出线程锁后、还没 close 时, 线程 B 进来取到了记录锁; A 随后的
        # close 把**B 正在持有的**锁一并撤销 (POSIX 记录锁按「进程 × 文件」释放)。
        # 实测: 外部抢锁在 A close 前 BLOCKED、close 后 ACQUIRED, 两个调用都返回 True,
        # 账本出现同 ID 两行。所以「同一调用内用同一个 fd」是必要条件而非充分条件。
        with _write_lock:
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                if not _lock_exclusive(fd, LEDGER_LOCK_TIMEOUT_S):
                    # ⛔ 不降级为「没锁也写」: 无锁硬写正是丢事件/破坏幂等键的路径。
                    logger.error(
                        "[learning-events] 等账本锁超时 (%.0fs, %s), 本次事件未写入 — 有进程长时间持锁未退出",
                        LEDGER_LOCK_TIMEOUT_S,
                        path,
                    )
                    return False
                # 幂等: 文件内已有该 event_id → 跳过 (日志量级小, 全文扫描可接受;
                # 大文件时可换尾部 N 行 + 索引)。
                # G3-2 (CARD-G3-2, schema §二/§6.2 A4.5): 查重改为 parsed-field
                # equality — 原子串匹配 (`json.dumps(event_id) in line`) 在任意
                # 历史行 payload 文本恰好含该 JSON 串形时会把新事件误判 duplicate
                # 而**零次落账** (丢一次真实事实)。幂等语义不变 (event_id 唯一),
                # 只修正查重实现的正确性; 无法解析的行不算命中 (留痕后跳过)。
                #: CARD-G3-3 (d): 同一趟扫描里顺带取本节点**适用**复习事件的最晚
                #: 生效时刻 —— 乱序判据的比较基准。适用面 = 同 node_id /
                #: schema_ext=review/1 / 未标 out_of_order (与 schema §6.2 pending
                #: 集合定义逐字同款; 已标乱序的行本就不参与推进, 拿它当基准会让
                #: 一串补录事件互相抬高门槛)。
                latest_review = None
                raw = _read_all(fd)
                # (round-2 HIGH: 空文件不能去读尾字节 — 否则首事件永远写不进去)
                if raw:
                    for line in _iter_lines(raw):
                        try:
                            record = json.loads(line)
                        except ValueError:
                            # 坏行 (截断/损坏) 不构成 duplicate 证据, 但要留痕
                            logger.warning(
                                "[learning-events] 账本存在无法解析的行 (截断/损坏), 查重跳过该行: %r", line[:80]
                            )
                            continue
                        if not isinstance(record, dict):
                            continue
                        if record.get("event_id") == event_id:
                            return False
                        if not node_id or record.get("node_id") != node_id:
                            continue
                        prior_payload = record.get("payload")
                        if (
                            isinstance(prior_payload, dict)
                            and prior_payload.get("schema_ext") == _REVIEW_EXT_MARKER
                            # §6.2 冻结: 唯一合法值是布尔 true。只按「键在不在」判,
                            # 会让一条非法的 `out_of_order: false` 把基准行藏掉。
                            and prior_payload.get("out_of_order") is not True
                        ):
                            inst = _instant(record.get("effective_at"))
                            if inst is not None and (latest_review is None or inst > latest_review):
                                latest_review = inst
                    # G3-2 LF 守卫 (schema §二 截断自愈): 尾行无换行时先补 LF 再
                    # 追加 — 否则新事件粘进坏行连坐损坏 (Codex round-1 HIGH:
                    # 预置 partial JSON 后 append 会把两个 JSON 粘成一行坏行)。
                    # ⛔ 必须在锁内: 两个进程各自读到「尾行无 LF」会**各补一个**,
                    # 于是账本多出一个空行 —— 空行在校验器与 quiz-answer 写点两侧
                    # 都判整个账本不合规。
                    if not raw.endswith(b"\n"):
                        os.write(fd, b"\n")
                        logger.warning("[learning-events] 检测到无换行结尾的尾行 (疑似截断), 已补 LF 隔离后再追加")
                now = datetime.now(timezone.utc).isoformat()
                effective = effective_at or now
                # ⛔ 复制一份: 调用方的 dict 不属于本函数, 就地加键会让同一个
                # payload 对象被复用时把标记带到下一条事件上。
                payload_out = dict(payload or {})
                # ── CARD-G3-3 (d) 乱序补录通道 (schema v1 §6.2 :266/:270 冻结)。
                # 判据 = 「effective_at 不晚于本节点已记录的最新适用复习事件」,
                # 即规格的 `review_time <= W`(含同一瞬间 —— 在线写侧由 A3 推进到
                # W+1s 保证严格大于, 所以走到「等于」的只会是补录/重放)。
                # 标记是**加性**的: 只多一个 payload 键, 旧读方按 §6.1 忽略未知键;
                # 而按 §6.2 pending 定义, 标了它的行不进适用集 ⇒ 消费侧 (quiz-answer
                # 的 A2 重放) 不会拿它推进 frontmatter, 水位线**不回退**。
                # ⚠️ 只对复习事件族成立: 别的 event_type 没有水位线语义, 给它们
                # 打这个标记等于凭空发明一个契约里没有的判据。
                is_review = payload_out.get("schema_ext") == _REVIEW_EXT_MARKER
                if out_of_order and is_review:
                    # §6.2 冻结: 唯一合法值是布尔 true, 未标则不写该键。
                    payload_out["out_of_order"] = True
                elif out_of_order:
                    logger.warning(
                        "[learning-events] 事件 %s 声明了 out_of_order 但不是 review/1 事件 — "
                        "该键只对复习事件族有语义, 已忽略",
                        event_id,
                    )
                # ── ⛔ 这里**不做自动补标** (独立复核 H3 + 内部审查, 2026-09-05)。
                # 上一版按「effective_at 不晚于账本里本节点最新适用复习事件」自动打标,
                # 两个方向都会错, 而且错法都很贵:
                #   ① 账本最新时刻 L **不等于**已应用水位线 W —— append_event 在账本侧,
                #      读不到节点 frontmatter。实测链: E1@10:00 已应用(W=10:00) →
                #      E2@10:01 因 CAS 冲突入账但未应用(W 仍 10:00) → 补录 E3@10:00:30
                #      被自动标 out_of_order(因为 ≤ L=10:01), 而写点侧的语义门要求
                #      标记行 review_time ≤ W=10:00 ⇒ 报「被伪装成乱序的真实后继」
                #      **永久 fail-closed**, 该节点从此写不进任何评分;
                #   ② L < W 时 (节点状态导入 / 账本缺行), `L<事件≤W` 会**漏标**。
                # 更要命的是语义方向: schema §6.2 :271 把「未标 out_of_order 的迟到行」
                # 明确留给**人工裁定**(读方分不清「已应用」和「被漏掉的真实复习」,
                # 两者对用户意义相反)。自动补标等于替用户默认裁定成「丢弃」——
                # 同一秒的真实复习会从 `rc=1 fail-closed` 退化成 `rc=0 静默永久丢失`。
                # 账本侧**没有**可证的 W, 所以这里只告警、把裁定权还给调用方。
                if is_review and not out_of_order:
                    # 比较面用 §6.2 的判据字段 payload.review_time (缺失才回落顶层
                    # effective_at) —— 上一版直接读顶层 effective_at, 而它在调用方
                    # 省略时默认为 now, 于是补录调用既不会被察觉、又会写出一条
                    # effective_at 与 payload.review_time 不同瞬间的行 (validator 判 FAIL)。
                    cmp_inst = _instant(payload_out.get("review_time")) or _instant(effective)
                    if cmp_inst is not None and latest_review is not None and cmp_inst <= latest_review:
                        logger.warning(
                            "[learning-events] 事件 %s 的 review_time=%s 不晚于本节点账本里最新的"
                            "适用复习事件 (%s) —— 若这是补录/重放, 请显式传 out_of_order=True 走 §6.2 "
                            "补录通道; 若这是真实后继, 请人工核对节点水位线。本次**按原样写入, 未加标记**。",
                            event_id,
                            payload_out.get("review_time") or effective,
                            latest_review.isoformat(),
                        )
                record = {
                    "event_id": event_id,
                    "event_version": EVENT_VERSION,
                    "event_type": event_type,
                    "node_id": node_id,
                    "recorded_at": now,
                    "effective_at": effective,
                    "payload": payload_out,
                }
                line_bytes = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
                written = os.write(fd, line_bytes)
                # ⛔ 必须校验写了几个字节 (独立复核 H4 实测): 改成单次 os.write 之后
                # 短写会**静默成功** —— 基线用 `open(path,"a").write()` 时短写会抛
                # OSError 从而返回 False, 现在 os.write 只是返回一个较小的数。
                # 实测 (内核文件大小限额): 5000 字符 payload 只落盘 1000 字节且无 LF,
                # 基线返回 False + 记录错误, 而上一版**返回 True 且无任何错误**。
                # 残行本身由下一次追加的 LF 守卫自愈; 但「把残行报成成功」是回退。
                if written != len(line_bytes):
                    logger.error(
                        "[learning-events] 账本短写 (%d/%d 字节, %s) — 本次事件未完整写入; "
                        "残行将由下一次追加的 LF 守卫隔离",
                        written,
                        len(line_bytes),
                        path,
                    )
                    return False
            finally:
                os.close(fd)  # close 即释放本进程对该文件的记录锁
        return True
    except Exception as e:  # noqa: BLE001 — 日志兜底, 不炸主链
        logger.warning("[learning-events] append 失败 (主链不受影响): %s", e)
        return False
