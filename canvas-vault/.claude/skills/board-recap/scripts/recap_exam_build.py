#!/usr/bin/env python3
"""board-recap 第二刀 · 阶段回顾检验白板构建器 (CARD-G5-9, BATCH-2026-08-28-第五批).

职责边界 (与 SKILL.md 的分工):
  多板/阶段范围的检验白板生成 — preview (板名/成员链接/覆盖/未答数字 +
  拟写入全文) → 用户在 skill 层确认 → create 原子创建 检验白板/ 下 1 个
  md → undo 字节级回退。exam_service / verification_service 零接触 —
  格式契约直接复用 start-exam-board 的 检验白板/<stem>-<ts>.md 文件面。

硬约束:
  - **preview 零写侧**: preview 子命令只读 vault, 不写任何文件。未确认
    (= 不跑 create) 时全 vault 字节不变。
  - **create 恰 1 新文件**: 唯一写面 = ``检验白板/<anchor>-<ts>.md``;
    目标已存在 → 拒绝 (不覆盖); 同目录 tmp + os.replace 原子落盘;
    写前 lstat symlink 预检 (目录与目标被 symlink 布防 → 拒绝)。
  - **undo 字节级回退**: 校验路径 containment + generated_by 指纹 +
    sha256 全等 (用户改过的文件拒绝回退, 不静默丢改动); 回退 = move 到
    vault 外 --undo-dir 留痕, ⛔ 不物理删除 (对齐「默认不 delete」)。
  - **消费面兼容契约** (fixture 锁定):
    * frontmatter 无 ``questions`` 键、0 个 ``concept:`` 行 →
      board_manifest 的 exam_history 收录 question_count=0,
      past_question_digests 零新增;
    * ``type: exam_board`` + 路径在 检验白板/ 下 → start-exam-board
      Step 1 防嵌套拒绝以它为出题源;
    * ``status: done`` + 无答题区疑问批注 → quiz-answer Step 0 done
      分支「无新疑问」安全停, 零写侧;
    * frontmatter 为合法 YAML → board_manifest 扫描 0 parse_errors。
  - **不复制正文**: 产物内容 = 链接回原板/原节点 + 脚本数字 + 固定模板句,
    ⛔ 不含任何节点正文片段。诚实边界 (round-3 L2): 复用的
    ``_ledger_from_local`` 会**读取**节点全文以判 is_stub/统计正文 callout,
    所以正文确实进过内存 —— 保证的是"**不写进产物**", 不是"不读取"
    (哨兵串断言锁的正是前者)。
  - 纯 stdlib; 数据面复用同目录 recap_scan.py 的 fallback 只读扫描函数
    (importlib 加载, 确定性口径与 /board-recap 第一刀一致)。
  - 退出码: 0 = 正常 (拒绝也是 0, JSON 里给 refusal_reason — 拒绝是
    skill 的决策); 2 = 环境不可用 / 参数非法。

D5 前置登记 (诚实条款): 本卡开发时 D5 前置 1 (用户 UAT 反馈) 未发生 —
live 侧价值验证顺延 G5-11, 本脚本只交 worktree 面 + fixture 证据。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

EXAM_DIR = "检验白板"
BOARD_DIR = "原白板"
GENERATED_BY = "board-recap-exam v1 (CARD-G5-9)"
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}$")
# codex round-1 HIGH-1: argparse 的 required=True 只保证 flag **出现**, 不保证
# 值非空。原判定写作 `if args.expect_content_sha and args.expect_content_sha != sha`
# —— 空串 falsy 直接跳过比较, `--expect-content-sha ''` 即可创建用户从未确认过
# 的字节 (复核者隔离实测 created:true、写出 1092 bytes)。修法 = 形状白名单 +
# **无条件**比较: 值必须 64 位小写十六进制, 否则 exit 2 且零写侧。
# 同一形状约束施于 undo 的 --expect-sha (同型问题)。
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ── 复用第一刀的确定性扫描函数 (同目录 recap_scan.py) ──
# ⛔ round-4 新增 FAIL: importlib 加载会在 skill 目录写 __pycache__/*.pyc —
# 那是 vault 内的**写侧**, 直接违反 preview 零写侧承诺 (证据快照只覆盖四个
# 数据目录才没发现)。sys.dont_write_bytecode 必须在 exec_module **之前**置位,
# 并在之后恢复, 保证本脚本任何路径都不向 vault 落字节码。
_SCAN_PATH = Path(__file__).resolve().parent / "recap_scan.py"
_prev_dont_write = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    _spec = importlib.util.spec_from_file_location("recap_scan", _SCAN_PATH)
    _rs = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_rs)
finally:
    sys.dont_write_bytecode = _prev_dont_write


def _fail_env(msg: str) -> int:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    return 2


def _sanitize_ghost_id(raw: str) -> str:
    """幽灵 id 入产物前的结构净化 (round-4 H9)。

    幽灵 id 是白板 Concepts 小节里的**自由文本**（成员正则允许换行、反引号
    等）。原样放进 `` `…` `` 会被换行终止行、被反引号闭合代码跨度, 从而在
    产物里生成独立的 Markdown 行。这里折叠全部空白、剔除反引号与会起结构
    作用的字符, 并硬截断 —— 产物只把它当**标识串回显**, 不承载任何格式。
    """
    s = " ".join(str(raw or "").split())
    s = re.sub(r"[`\[\]|<>\\]", "", s)
    s = "".join(ch for ch in s if ch.isprintable())
    return s[:120] or "(空名)"


def _scan_board(vault: Path, stem: str) -> dict:
    """单板只读扫描 (fallback 口径, 与 recap_scan 第一刀一致)。"""
    board_path = _rs._contained_md(vault / BOARD_DIR, stem)
    if board_path is None:
        return {
            "board_stem": stem,
            "exists": False,
            "refusal_reason": "板名非法 (containment 拒绝)",
        }
    if not board_path.is_file():
        return {
            "board_stem": stem,
            "exists": False,
            "refusal_reason": "原白板文件不存在",
        }
    board_text = _rs._read(board_path)
    _, board_body = _rs._frontmatter_and_body(board_text)
    sec = _rs._CONCEPTS_SECTION_RE.search(board_body)
    sec_body = re.sub(r"<!--.*?-->", "", sec.group(1), flags=re.S) if sec else ""
    bullet_lines = "\n".join(
        ln for ln in sec_body.splitlines() if re.match(r"^\s*-\s", ln)
    )
    members = list(
        dict.fromkeys(m.strip() for m in _rs._CONCEPT_LINK_RE.findall(bullet_lines))
    )
    ledger = _rs._ledger_from_local(vault, members)
    tips_total = sum(r.get("tips_count", 0) for r in ledger)
    # 幽灵链接 (workflow round-2 confirmed): Concepts 里列了但节点文件不存在/
    # 名非法/不可读 → _ledger_from_local 给 role="unknown" + exists=False。
    # 原实现把它们计进 members 却不进 seeds/derived, 产出「成员 3(1 种子 +
    # 0 派生)」这种自相矛盾数字, 还把死 wikilink 原样写进产物且零标记。
    # 现在: 分开计数, member_ids 只留真实存在的, 幽灵单列并在产物显式成段。
    live_rows = [r for r in ledger if r.get("role") in ("seed", "derived")]
    # round-4 H9: ghost id 来自白板 Concepts 的自由文本 (成员正则允许换行与
    # 反引号) — 原样嵌进 `…` 会被换行/反引号突破隔离, 在产物里生成独立行。
    # 一律折叠空白 + 剔除反引号与 Markdown 结构字符后再入产物。
    ghosts = [
        {
            "node_id": _sanitize_ghost_id(r["node_id"]),
            "reason": r.get("role_source") or "unknown",
        }
        for r in ledger
        if r.get("role") not in ("seed", "derived")
    ]
    return {
        "board_stem": stem,
        "exists": True,
        "board_sha256": hashlib.sha256(board_text.encode("utf-8")).hexdigest(),
        # members 只数可解析成员, 与 seeds+derived 恒等 (X+Y==N 不再矛盾)
        "members": len(live_rows),
        "seeds": sum(1 for r in live_rows if r.get("role") == "seed"),
        "derived": sum(1 for r in live_rows if r.get("role") == "derived"),
        "listed_in_concepts": len(ledger),
        "ghost_links": ghosts,
        "ghost_count": len(ghosts),
        "tips_total": tips_total,
        # 学习 vault 无「已答」标记 → 未答 = 全部 tips 上界 (C5 同口径)
        "tips_unanswered_upper_bound": tips_total,
        "member_ids": [r["node_id"] for r in live_rows],
    }


def _render_content(boards: list[dict], anchor: str, ts: str, created_at: str) -> str:
    """产物全文 — 链接 + 脚本数字 + 固定模板句, 零正文复制。

    frontmatter 契约: 无 questions 键 / 0 个 concept: 行 / status: done /
    type: exam_board — 消费面兼容判据见模块 docstring。
    """
    n = len(boards)
    # ⛔ round-6 终裁复核: 节点/ 是**一 vault 一学科的扁平共享池**, 同一节点被
    # 两块板的 ## Concepts 同时列出是正常形态。原先各板 members/tips 直接相加
    # → 跨板成员在「阶段数字」里被重复计数, 且产物把同一节点重复列成员链接,
    # 全程零去重零声明。现在: 总计按 node_id 去重, 并如实声明去重量。
    all_member_ids: list[str] = []
    for b in boards:
        all_member_ids.extend(b["member_ids"])
    uniq_members = list(dict.fromkeys(all_member_ids))
    total_members = len(uniq_members)
    dup_members = len(all_member_ids) - total_members
    total_tips = sum(b["tips_total"] for b in boards)
    fm = [
        "---",
        "type: exam_board",
        "recap_kind: stage_recap",
        f'source_board: "[[原白板/{anchor}]]"',
        "recap_boards:",
        *[f'  - "[[原白板/{b["board_stem"]}]]"' for b in boards],
        f'created_at: "{created_at}"',
        "status: done",
        f"generated_by: {GENERATED_BY}",
        "---",
    ]
    lines = [
        *fm,
        "",
        f"# 阶段回顾 · {anchor} 等 {n} 板 · {ts[:10]}",
        "",
        "> [!info]+ 阶段回顾检验白板（链接回原板 · 不含正文 · 无题面）",
        "> 本板是阶段回顾产物：只列链接与脚本数字，不复制任何正文，也不含题目。",
        "> 要出题请对某块原白板运行 /start-exam-board（本板不可作为出题源）。",
        "",
        "## 覆盖范围",
        "",
    ]
    total_ghosts = sum(b["ghost_count"] for b in boards)
    for b in boards:
        ghost_note = (
            f" · ⚠ Concepts 另列 {b['ghost_count']} 条链接指向不存在/不可读的节点（见下）"
            if b["ghost_count"]
            else ""
        )
        lines.append(
            f"- [[原白板/{b['board_stem']}]] — 成员 {b['members']}"
            f"（{b['seeds']} 种子 + {b['derived']} 派生）/ 批注 {b['tips_total']} 条"
            f"（未答上界 {b['tips_unanswered_upper_bound']}，无已答标记）{ghost_note}"
        )
    lines += ["", "## 成员链接（回原节点）", ""]
    for b in boards:
        lines.append(f"### [[原白板/{b['board_stem']}]]")
        lines.append("")
        if b["member_ids"]:
            lines += [f"- [[节点/{m}]]" for m in b["member_ids"]]
        else:
            lines.append("- （本板 Concepts 小节无可解析成员）")
        lines.append("")
    if total_ghosts:
        # 幽灵链接单列成段并**不写成 wikilink**（写了就是死链），如实标原因
        lines += [
            "## 待修链接（Concepts 里列了但打不开）",
            "",
        ]
        for b in boards:
            for g in b["ghost_links"]:
                lines.append(
                    f"- `{b['board_stem']}` → `节点/{g['node_id']}.md`（{g['reason']}）"
                )
        lines.append("")
    lines += [
        "## 阶段数字（脚本产出 · 判读留人）",
        "",
        f"- 覆盖 {n} 板 / 总成员 {total_members}（按节点去重）/ 总批注 {total_tips} 条（未答上界 {total_tips}）"
        + (f" / 跨板重复成员 {dup_members} 个" if dup_members else "")
        + (f" / 待修链接 {total_ghosts} 条" if total_ghosts else ""),
        f"- 数据面：本地只读扫描（fallback 口径，与 /board-recap 第一刀一致）· 取数时刻 {created_at}",
        "",
    ]
    return "\n".join(lines)


def _symlink_probe(vault: Path, target: Path, tmp: Path) -> str | None:
    """写前 lstat 预检 — 目录 / 最终目标 / **落盘用的 tmp 路径** 三者。

    W4 (workflow round-1 复现, BLOCKER): 只查目录与 target 而漏 tmp,
    预置 ``<target>.g59-tmp`` symlink 会让 write_text 跟随链接写到 vault
    外 (覆盖任意外部文件), 随后 os.replace 把 target 本身变成指向 vault
    外的 symlink; 且 undo 的 resolve() 会逃出 exam_root 导致无法回退。
    本函数是第一道; 真正的防线是 _atomic_write 的 O_EXCL|O_NOFOLLOW。
    """
    for p in (vault / EXAM_DIR, target, tmp):
        if p.is_symlink():
            return f"写入目标被 symlink 布防: {p}"
    return None


def _created_at(ts: str) -> str:
    """--ts (YYYY-MM-DD-HHMM) → ISO Z 串。

    ⚠️ round-3 M7 + workflow round-2: 本函数只做格式转换 —— **调用方必须
    保证 ts 本身是 UTC 时刻**。默认 ts 现取 ``datetime.now(timezone.utc)``
    (原先取本地墙钟却硬贴 Z, 在 Asia/Shanghai 写出快 8 小时的假 UTC,
    与 start-exam-board 的 ``date -u`` 分属两个时钟, 导致
    board_manifest_service 的 exam_history 按 created_at 排序错位)。
    """
    return f"{ts[:10]}T{ts[11:13]}:{ts[13:15]}:00Z"


def _fsync_dir(d: Path) -> None:
    """目录项持久化 (round-3 M5): 只 fsync 文件不 fsync 父目录时,
    崩溃后可能文件内容在而目录项丢失。失败静默 (不是所有 FS 都支持)。"""
    try:
        fd = os.open(d, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _open_exam_dirfd(vault: Path) -> tuple[int | None, str | None]:
    """打开 检验白板/ 并返回一个**钉死该目录 inode** 的 dir_fd。

    主 session 并行复核 HIGH-4 的正解。三重校验:
    1. ``O_DIRECTORY|O_NOFOLLOW`` —— 目录本身若是 symlink 直接 ELOOP 失败;
    2. ``os.fstat(dfd)`` 与 ``os.stat(vault/EXAM_DIR)`` 的 (dev, ino) 必须相同
       —— 打开的确是我们校验过的那个目录, 不是打开后被换掉的另一个;
    3. dfd 与 vault 必须**同一文件系统** (st_dev 相同) —— 目录被换成指向外部
       挂载点的链接时, 即便前两条侥幸通过也会在这里被拦。
    → (dfd | None, 失败原因 | None)。调用方负责 os.close(dfd)。
    """
    exam = vault / EXAM_DIR
    try:
        dfd = os.open(exam, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as e:
        return (
            None,
            f"{EXAM_DIR}/ 打开失败 (被 symlink 布防或不是目录): {type(e).__name__}",
        )
    try:
        st_dfd = os.fstat(dfd)
        st_path = os.stat(exam)
        st_vault = os.stat(vault)
    except OSError as e:
        os.close(dfd)
        return None, f"{EXAM_DIR}/ 身份校验失败: {type(e).__name__}"
    if (st_dfd.st_dev, st_dfd.st_ino) != (st_path.st_dev, st_path.st_ino):
        os.close(dfd)
        return None, f"{EXAM_DIR}/ 在打开前后被替换 (inode 变化), 拒绝写入"
    if st_dfd.st_dev != st_vault.st_dev:
        os.close(dfd)
        return None, f"{EXAM_DIR}/ 与 vault 不在同一文件系统 (疑似越界挂载), 拒绝写入"
    return dfd, None


def _atomic_write(tmp: Path, target: Path, content: str, dir_fd: int) -> str | None:
    """O_EXCL|O_NOFOLLOW 写 tmp → fsync → **link 到 target (no-replace)** →
    unlink tmp → fsync 父目录。

    W4 纵深防御: O_NOFOLLOW 让 tmp 若是 symlink 直接 ELOOP 失败 (不跟随),
    O_CREAT|O_EXCL 让 tmp 已存在时直接失败 (不覆盖并发/残留文件) —
    lstat 预检与实际写之间的 TOCTOU 窗口由内核标志封死。
    round-3 H6: 落盘不再用 ``os.replace`` (它会**覆盖**预检之后才出现的
    target) —— 改用 ``os.link``: 目标已存在时内核直接 EEXIST, 原子且永不
    覆盖; 成功后 unlink tmp, 目标是同一 inode 的硬链接 (内容已 fsync)。
    round-3 M5: 补 fsync 父目录; tmp 清理失败如实回报而非静默吞掉。
    → (失败原因 | None, 告警 | None)。失败时目标未创建; 告警只表示 tmp
    未清理 (目标已正确落盘), 由调用方如实写进回执而非当作失败。

    ⛔ 主 session 并行复核 HIGH-4 (实测反例: probe 后把 检验白板/ 换成指向
    vault 外的目录 symlink, create 仍返回 created:true 且**文件落在 vault 外**):
    此前 `_prepare` 的目录守卫、`_symlink_probe` 与本函数的 open/link 全部**按路径**
    操作 —— 检查与使用之间隔着可被替换的路径解析, O_NOFOLLOW 只护住最后一段,
    中段/父目录被换掉时护不住。修法 = **dirfd 锚定**: 调用方用
    O_DIRECTORY|O_NOFOLLOW 打开 检验白板/ 拿到 dfd 并校验它确在 vault 内,
    此后所有操作只用 **basename + dir_fd=dfd**。dfd 钉死的是那一个目录 inode,
    路径事后怎么换都改变不了操作落点 —— 窗口从根本上消失, 而不是被压小。

    ⚠️ **作用域边界（独立复核明确要求不得外推）**: 本函数保证的是
    「**锚定成功之后**, `_atomic_write` 内部的落点不再依赖路径解析」。
    它**不**等于「整个程序从此完全不解析路径」——
      · `_prepare` 在锚定**之前**仍有 mkdir、`_symlink_probe` 与打开目录时的路径解析;
      · `cmd_undo` 是另一套**按路径**的流程, 不走本锚定。
    写文档/验收单时请照此口径, 不要写成「全程 dirfd 化」。
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    tmp_name, target_name = tmp.name, target.name
    try:
        fd = os.open(tmp_name, flags, 0o644, dir_fd=dir_fd)
    except OSError as e:
        return (
            f"临时文件创建失败 (symlink 布防或残留 {tmp.name}): {type(e).__name__}",
            None,
        )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", closefd=False) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        # round-4 H6: 发布的字节必须是**我们刚写的那个 inode** — 关闭 fd 后
        # 按路径 link, 期间 tmp 若被替换会发布他人内容。这里用写入时的 fd 记下
        # (dev,ino), link 之后立刻核对 target 是同一 inode, 不符则撤销发布。
        st_written = os.fstat(fd)
        os.close(fd)
        fd = -1
        os.link(
            tmp_name, target_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd
        )  # EEXIST 绝不覆盖
        # codex round-1 HIGH-2 (a): 只比 (dev,ino) 不足 —— 别的进程**原地改写
        # 同一个 tmp inode** 时两侧 inode 恒等, 核对照样通过, 发布出去的却是
        # 他人字节 (复核者隔离注入实测: 回执 SHA e51ca99e… 与目标实际 43cb09e0…
        # 分叉, 而 _atomic_write 返回 err=None)。修法 = 发布后**重读目标字节**
        # 并与我们要写的 content 做 sha 全等, inode 与字节两条都过才算发布成功。
        want_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        vfd = os.open(target_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        try:
            st_pub = os.fstat(vfd)
            got = b""
            while chunk := os.read(vfd, 1 << 20):
                got += chunk
        finally:
            os.close(vfd)
        same_inode = (st_pub.st_dev, st_pub.st_ino) == (
            st_written.st_dev,
            st_written.st_ino,
        )
        if not same_inode or hashlib.sha256(got).hexdigest() != want_sha:
            # codex round-1 HIGH-2 (b): 原实现在这里 target.unlink() —— 但走到
            # 本分支恰恰说明 target 已**不是我们的 inode**(被并发替换), 按路径
            # 删它等于删掉别人刚创建的文件, 且回执还报失败 → 文件静默丢失。
            # 修法: inode 不符时**绝不删**, 只如实回报; 仅当 inode 仍是我们的
            # (纯字节被原地改写) 才撤销自己的发布。
            if same_inode:
                try:
                    os.unlink(target_name, dir_fd=dir_fd)
                except OSError:
                    pass
                raise OSError("published bytes mismatch (in-place rewrite)")
            raise OSError(
                "published inode mismatch (concurrent replacement; 未删除该文件)"
            )
    except OSError as e:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_name, dir_fd=dir_fd)
        except OSError:
            pass
        kind = (
            "目标已存在 (并发创建), 拒绝覆盖"
            if isinstance(e, FileExistsError)
            else "原子写失败"
        )
        return f"{kind}: {type(e).__name__}", None
    warn = None
    try:
        os.unlink(tmp_name, dir_fd=dir_fd)
    except OSError as e:
        warn = f"临时文件未能清理 ({tmp.name}: {type(e).__name__})，下次 create 同 ts 会被拒绝，请手动删除"
    try:
        os.fsync(dir_fd)  # dirfd 已在手, 直接 fsync 它 (不再按路径重开)
    except OSError:
        pass
    return None, warn


def _prepare(args) -> tuple[list[dict], str, Path] | int:
    """preview/create 共用的数据面: 扫描各板 + 定目标路径。"""
    vault = Path(args.vault)
    if not (vault / BOARD_DIR).is_dir():
        return _fail_env(f"vault 不可用: {vault / BOARD_DIR} 不存在")
    # 目录级 symlink 守卫 (与 recap_scan 同语义)
    vault_resolved = vault.resolve()
    for sub in (BOARD_DIR, "节点", EXAM_DIR):
        d = vault / sub
        if not d.exists():
            continue
        try:
            escaped = not d.resolve().is_relative_to(vault_resolved)
        except (OSError, ValueError):
            escaped = True
        if escaped:
            return _fail_env(
                f"vault 不可用: {sub}/ 目录 resolve 到 vault 之外 (symlink 越界)"
            )
    stems = list(dict.fromkeys(args.boards))
    if not stems:
        return _fail_env("--boards 至少给 1 块板")
    anchor = args.anchor or stems[0]
    if anchor not in stems:
        return _fail_env(f"--anchor {anchor!r} 不在 --boards 里")
    # round-3 M6: wikilink 语义字符 — `#` 是 heading 锚点、`|` 是别名分隔,
    # 板名含它们时产物写出的 [[原白板/A#B]] 会被消费方 (resolve_node_id)
    # 截断成另一个板名 → scan_vault 归属错乱且不报 parse error。文件系统
    # 允许这两个字符, 所以必须在本层显式拒绝而不是指望 containment。
    # round-6 终裁复核: `]` 同样是 wikilink 终止符 (板名含 `]]` 时
    # resolve_node_id 在首个 `]]` 处截断 → 归属错乱), `[` 同理
    bad = [s for s in stems if any(c in s for c in "#|^][")]
    if bad:
        return _fail_env(f"板名含 wikilink 语义字符 (#/|/^/[/]), 拒绝: {bad}")
    # round-3 M7: --ts 不只验形状 — 必须是真实存在的日历时刻
    # (2026-99-99-9999 曾通过, 会写出非法 created_at 并阻断 SnapshotV3 刷新)
    if not _TS_RE.match(args.ts):
        return _fail_env(f"--ts 非法: {args.ts!r} (须为 YYYY-MM-DD-HHMM)")
    try:
        datetime.strptime(args.ts, "%Y-%m-%d-%H%M")
    except ValueError as e:
        return _fail_env(f"--ts 不是真实时刻: {args.ts!r} ({e})")
    boards = [_scan_board(vault, s) for s in stems]
    target = vault / EXAM_DIR / f"{anchor}-{args.ts}.md"
    return boards, anchor, target


def cmd_preview(args) -> int:
    prep = _prepare(args)
    if isinstance(prep, int):
        return prep
    boards, anchor, target = prep
    vault = Path(args.vault)
    missing = [b["board_stem"] for b in boards if not b["exists"]]
    out: dict = {
        "mode": "preview",
        "write_side": "none",
        "anchor": anchor,
        "ts": args.ts,
        "boards": boards,
        "target_path": str(target.relative_to(vault)),
        "target_exists": target.exists(),
    }
    if missing:
        out["refusal_reason"] = f"以下板不存在或板名非法: {missing} (create 将拒绝)"
    elif target.exists() or target.is_symlink():
        # round-3 L1: 既有目标此前只给 target_exists=true 而无 refusal_reason,
        # 与 SKILL.md「refusal_reason 非空 → 如实转告并停」的契约不符
        out["refusal_reason"] = (
            f"目标已存在: {target.name} (create 将拒绝覆盖; 换 --ts 或先 undo)"
        )
    else:
        content = _render_content(boards, anchor, args.ts, _created_at(args.ts))
        # round-6: 与产物同口径 —— 成员按 node_id 去重 (扁平共享池跨板重复)
        all_ids: list[str] = []
        for b in boards:
            all_ids.extend(b["member_ids"])
        uniq = list(dict.fromkeys(all_ids))
        out["totals"] = {
            "boards": len(boards),
            "members": len(uniq),
            "members_listed": len(all_ids),
            "duplicate_members": len(all_ids) - len(uniq),
            "tips_total": sum(b["tips_total"] for b in boards),
            "ghosts": sum(b["ghost_count"] for b in boards),
        }
        out["content"] = content
        out["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        out["next_step"] = (
            "用户确认后跑 create，并把本 content_sha256 传给 --expect-content-sha"
            "（绑定所见即所写）"
        )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_create(args) -> int:
    prep = _prepare(args)
    if isinstance(prep, int):
        return prep
    boards, anchor, target = prep
    vault = Path(args.vault)
    missing = [b["board_stem"] for b in boards if not b["exists"]]
    if missing:
        print(
            json.dumps(
                {
                    "mode": "create",
                    "created": False,
                    "refusal_reason": f"板不存在/非法: {missing}",
                },
                ensure_ascii=False,
            )
        )
        return 0
    if target.exists() or target.is_symlink():
        print(
            json.dumps(
                {
                    "mode": "create",
                    "created": False,
                    "refusal_reason": f"目标已存在, 拒绝覆盖: {target.name}",
                },
                ensure_ascii=False,
            )
        )
        return 0
    content = _render_content(boards, anchor, args.ts, _created_at(args.ts))
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    # round-3 H5: preview→create 之间 vault 可能变化 (新增成员/改批注),
    # 相同 --ts 并不保证所见即所写。--expect-content-sha 把用户**确认过的
    # 那份字节**绑进来: 不符即拒, 零写侧, 让 skill 重跑 preview 再确认。
    # codex round-1 HIGH-1: 形状先于比较 —— 空串/非 64 位 hex 一律 exit 2,
    # 不再走 falsy 短路; 比较本身改为**无条件**。
    if not _SHA256_RE.match(args.expect_content_sha or ""):
        return _fail_env(
            "--expect-content-sha 必须是 preview 回执里的 64 位小写十六进制 "
            "content_sha256（空串或非法形状一律拒绝，防绕过用户确认）"
        )
    if args.expect_content_sha != sha:
        print(
            json.dumps(
                {
                    "mode": "create",
                    "created": False,
                    "refusal_reason": (
                        "内容与用户确认的 preview 不一致 (期间 vault 有变化) — "
                        "已零写侧退出, 请重跑 preview 让用户确认新内容"
                    ),
                    "expected_sha256": args.expect_content_sha,
                    "actual_sha256": sha,
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        return 0
    try:
        (vault / EXAM_DIR).mkdir(exist_ok=True)
    except OSError as e:  # round-3 L3: I/O 异常归一到 JSON+exit 2 契约
        return _fail_env(f"{EXAM_DIR}/ 目录不可用: {type(e).__name__}")
    tmp = target.with_name(target.name + ".g59-tmp")
    probe = _symlink_probe(vault, target, tmp)
    if probe:
        return _fail_env(probe)
    # 主 session 并行复核 HIGH-4: 上面的 probe 仍是「按路径检查」，与实际写入之间
    # 隔着可被替换的路径解析（实测：probe 后把 检验白板/ 换成指向 vault 外的目录
    # symlink，create 仍 created:true 且文件落在 vault 外）。这里改为**先取 dirfd
    # 锚定目录 inode**，之后所有写侧操作只用 basename + dir_fd —— 路径事后怎么换
    # 都改变不了操作落点。probe 保留为第一道快速拒绝（诊断信息更友好）。
    dfd, dfd_err = _open_exam_dirfd(vault)
    if dfd_err:
        return _fail_env(dfd_err)
    try:
        write_err, warn = _atomic_write(tmp, target, content, dfd)
    finally:
        os.close(dfd)
    if write_err:
        return _fail_env(write_err)
    rel = str(target.relative_to(vault))
    receipt = {
        "mode": "create",
        "created": True,
        "created_path": rel,
        "content_sha256": sha,
        "bytes": len(content.encode("utf-8")),
        # round-3 H8: 路径含空格/括号/& 时未加引号的 hint 是**语法错误的**
        # shell 命令 (zsh -n 实测 parse error) — 逐参数 shlex.quote
        # round-3 H8 + round-4: 路径含空格/括号/& 时未加引号的 hint 是**语法
        # 错误的** shell 命令 (zsh -n 实测 parse error) — 逐参数 shlex.quote;
        # 且 undo-dir 占位符不能写成 `<...>` (shell 重定向语法, 整条仍解析失败),
        # 改成可直接替换的引号串。
        # codex round-1 MEDIUM-7: SKILL.md 称 undo_hint「可直接复制执行」, 但串以
        # `undo …` 开头 —— 缺 `python3 <本脚本>` 前缀, 在普通 shell 里 `undo` 不是
        # 命令 (zsh: command not found)。补上解释器与脚本绝对路径, 让文档的承诺成立。
        "undo_hint": (
            f"{shlex.quote(sys.executable)} {shlex.quote(str(Path(__file__).resolve()))} "
            f"undo --vault {shlex.quote(str(vault))} --path {shlex.quote(rel)} "
            f"--expect-sha {sha} --undo-dir 'PUT_A_DIR_OUTSIDE_THE_VAULT_HERE'"
        ),
    }
    if warn:
        receipt["warning"] = warn
    print(json.dumps(receipt, ensure_ascii=False, indent=1))
    return 0


def cmd_undo(args) -> int:
    vault = Path(args.vault)
    # codex round-1 HIGH-1 同型: --expect-sha 也必须先过形状白名单, 否则空串
    # 会让下游的 sha 全等比较失去意义 (undo 的判定虽然是无条件比较, 但空串
    # 期望值配上"不符即拒"会退化成**恒拒**, 掩盖真实的绑定失效)。
    if not _SHA256_RE.match(args.expect_sha or ""):
        return _fail_env(
            "--expect-sha 必须是 create 回执里的 64 位小写十六进制 content_sha256"
        )
    # ⛔ round-6 终裁复核: cmd_undo 此前完全没有 create 侧的「目录 symlink 越界」
    # 守卫 —— containment 只比 target.resolve() 与 exam_root.resolve(), 两者
    # 一起被 symlink 带出 vault 后仍判 contained=True, undo 就会去动 vault 外
    # 的文件。这里补上与 _prepare 同款的目录级守卫。
    vault_resolved = vault.resolve()
    for sub in (BOARD_DIR, "节点", EXAM_DIR):
        d = vault / sub
        if not d.exists():
            continue
        try:
            escaped = not d.resolve().is_relative_to(vault_resolved)
        except (OSError, ValueError):
            escaped = True
        if escaped:
            return _fail_env(
                f"vault 不可用: {sub}/ 目录 resolve 到 vault 之外 (symlink 越界)"
            )
    # 主 session 并行复核 HIGH-5 前半: 原实现直接 `.resolve()`, 会**解掉最后一段
    # 的 symlink** —— 传入同目录 alias(`alias.md -> real.md`) 时, 回执声称移除的是
    # alias, 实际移走的却是 referent, 并在 vault 里留下一条死链。后面的 O_NOFOLLOW
    # 完全看不到这一点, 因为它拿到的已经是 resolve 之后的真实路径。
    # 修法: 先按**未解析路径**判 leaf 是不是 symlink, 是就直接拒绝 —— undo 的语义
    # 是「把我创建的那个文件移走」, 对 alias 无定义, 不猜。
    raw_target = vault / args.path
    if raw_target.is_symlink():
        return _fail_env(
            f"undo 目标是 symlink, 拒绝 (回退语义对别名无定义, 避免移走 referent "
            f"并留下死链): {args.path}"
        )
    target = raw_target.resolve()
    exam_root = (vault / EXAM_DIR).resolve()
    try:
        contained = target.is_relative_to(exam_root)
    except ValueError:
        contained = False
    if not contained:
        return _fail_env(f"undo 目标必须在 {EXAM_DIR}/ 内: {args.path}")
    if not target.is_file():
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": "目标不存在 (无可回退)",
                },
                ensure_ascii=False,
            )
        )
        return 0
    # round-3 H7: 校验的字节与最终移走的字节必须**是同一个 inode** —
    # 原实现 read_bytes 校验后按路径 shutil.move, 期间编辑器/同步程序若替换
    # 文件, 移走的是未经校验的新版本 (用户改动被静默丢进留痕目录)。
    # 现在: O_NOFOLLOW 打开拿 fd → 从 fd 读校验 → 记 (dev, ino) →
    # 移动前后各 lstat 一次比对同一 inode, 不符即拒。
    try:
        tfd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        return _fail_env(f"undo 目标打开失败 (symlink 或权限): {type(e).__name__}")
    try:
        st_open = os.fstat(tfd)
        raw = b""
        while chunk := os.read(tfd, 1 << 20):
            raw += chunk
    finally:
        os.close(tfd)
    identity = (st_open.st_dev, st_open.st_ino)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != args.expect_sha:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": "内容 sha256 与创建回执不符 (文件已被改动, 拒绝静默丢弃改动)",
                    "actual_sha256": sha,
                },
                ensure_ascii=False,
            )
        )
        return 0
    if GENERATED_BY.encode("utf-8") not in raw:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": "缺本脚本 generated_by 指纹, 拒绝回退非本脚本产物",
                },
                ensure_ascii=False,
            )
        )
        return 0
    undo_dir = Path(args.undo_dir).resolve()
    try:
        inside_vault = undo_dir.is_relative_to(vault.resolve())
    except ValueError:
        inside_vault = False
    if inside_vault:
        return _fail_env("--undo-dir 必须在 vault 之外 (vault 内不留新文件)")
    try:
        undo_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:  # round-3 L3
        return _fail_env(f"--undo-dir 不可用: {type(e).__name__}")
    # W5 (workflow round-1): 留痕名只含秒级时间戳 + 固定 target.name, 同秒
    # 二次 undo 同一 (anchor,ts) 会被 shutil.move 覆盖 → 先前留痕字节丢失,
    # 违反「不物理删除」。碰撞时顺延 -2/-3…, 绝不覆盖既有留痕。
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # round-3 H7 二段: 移动前复核 inode 未被替换 (校验窗口结束)
    try:
        st_now = os.lstat(target)
    except OSError as e:
        return _fail_env(f"undo 目标已消失: {type(e).__name__}")
    if (st_now.st_dev, st_now.st_ino) != identity:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": (
                        "校验后文件被替换 (inode 变化) — 拒绝移走未经校验的版本"
                    ),
                },
                ensure_ascii=False,
            )
        )
        return 0
    # W5 + round-3 M4: 留痕目的端**独占创建** (O_EXCL) 而不是 exists() 后
    # shutil.move —— 后者在目的端有竞态, 且跨文件系统会退化成 copy+unlink。
    # 这里: 先在目的端 O_EXCL 写出校验过的字节 + fsync, 确认落盘后才 unlink
    # 源 (耐久回退: 任何时刻崩溃都不会两头皆空)。
    dest = undo_dir / f"undone-{stamp}-{target.name}"
    seq, dfd = 1, None
    while dfd is None:
        try:
            dfd = os.open(
                dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644
            )
        except FileExistsError:
            seq += 1
            if seq > 999:
                return _fail_env("留痕文件名碰撞超过 999 次, 拒绝回退 (换 --undo-dir)")
            dest = undo_dir / f"undone-{stamp}-{seq}-{target.name}"
        except OSError as e:
            return _fail_env(f"留痕文件创建失败: {type(e).__name__}")
    try:
        with os.fdopen(dfd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        try:
            dest.unlink()
        except OSError:
            pass
        return _fail_env(f"留痕写入失败, 已放弃回退 (原文件未动): {type(e).__name__}")
    _fsync_dir(undo_dir)
    # codex round-1 HIGH-3 (2): 留痕写完 + fsync 之后**从未回读校验** —— 复核者
    # 隔离注入原地改写留痕 inode 后, 源文件照删、回执 retained SHA 报 765bf07e…
    # 而留痕实际是 3710644e…: 「写留痕后才删源」的耐久承诺被架空 (留下的是坏
    # 备份, 而源已不可回). 修法 = 删源之前把留痕**重新打开读回**, inode 与
    # sha 两条都全等才继续; 任一不符 → 绝不删源 (vault 内原件仍在, 不丢字节)。
    try:
        rfd = os.open(dest, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            st_dest = os.fstat(rfd)
            back = b""
            while chunk := os.read(rfd, 1 << 20):
                back += chunk
        finally:
            os.close(rfd)
    except OSError as e:
        return _fail_env(
            f"留痕写出后不可回读, 已放弃回退 (原文件未动): {type(e).__name__}"
        )
    if st_dest.st_size != len(raw) or hashlib.sha256(back).hexdigest() != sha:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": (
                        "留痕落盘后回读校验不符 (备份被替换或原地改写) — "
                        "未删除 vault 内文件; 该留痕不可信, 请换 --undo-dir 重试"
                    ),
                    "retained_at": str(dest),
                    "retained_sha256_actual": hashlib.sha256(back).hexdigest(),
                    "expected_sha256": sha,
                },
                ensure_ascii=False,
            )
        )
        return 0
    # round-4: inode 复核与 unlink 之间仍有窗口 — 留痕写入耗时里文件可能被
    # 替换。紧贴 unlink 前**再复核一次**, 把窗口压到系统调用级; 不符则保留
    # 原文件 (留痕已在 vault 外, 不丢字节) 并如实告知。
    # round-4 H7: 只比 (dev,ino) 不够 —— 编辑器**原地改写**同一 inode 时
    # 两次 lstat 都不变, undo 会删掉用户刚写的内容。改为**重读内容比对 sha**
    # (inode 一并核, 覆盖替换与原地改写两种形态)。
    try:
        cfd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        return _fail_env(
            f"undo 目标在留痕后不可读 (留痕已存 {dest}): {type(e).__name__}"
        )
    try:
        st_final = os.fstat(cfd)
        cur = b""
        while chunk := os.read(cfd, 1 << 20):
            cur += chunk
    finally:
        os.close(cfd)
    if (st_final.st_dev, st_final.st_ino) != identity or hashlib.sha256(
        cur
    ).hexdigest() != sha:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": (
                        "留痕写出期间原文件内容发生变化 (替换或原地改写) — "
                        f"未删除 vault 内文件; 校验过的旧版本已备份在 {dest}"
                    ),
                    "retained_at": str(dest),
                },
                ensure_ascii=False,
            )
        )
        return 0
    # codex round-1 HIGH-3 (1): 上面的重读校验在 os.close(cfd) 后才 unlink,
    # 中间仍有窗口 —— 复核者在该窗口换入 USER-NEW-BYTES, 结果新 inode 被删、
    # 留痕里只有旧版本, 而回执报 undone:true。POSIX 没有「按 inode 删除」的
    # 原语, 能做到的最紧形态是**紧贴 unlink 前再 lstat 一次**核 identity,
    # 把窗口压到相邻两个系统调用之间。残留窗口如实声明在 SKILL.md。
    try:
        st_pre_unlink = os.lstat(target)
    except OSError as e:
        return _fail_env(
            f"删除前复核失败, 未删除 (留痕已存 {dest}): {type(e).__name__}"
        )
    if (st_pre_unlink.st_dev, st_pre_unlink.st_ino) != identity:
        print(
            json.dumps(
                {
                    "mode": "undo",
                    "undone": False,
                    "refusal_reason": (
                        "删除前一刻文件被替换 (inode 变化) — 未删除, "
                        f"避免误删他人写入; 校验过的旧版本已备份在 {dest}"
                    ),
                    "retained_at": str(dest),
                },
                ensure_ascii=False,
            )
        )
        return 0
    try:
        os.unlink(target)
    except OSError as e:
        return _fail_env(
            f"留痕已保存 {dest} 但原文件删除失败 (vault 内仍在): {type(e).__name__}"
        )
    _fsync_dir(target.parent)
    print(
        json.dumps(
            {
                "mode": "undo",
                "undone": True,
                "removed_path": args.path,
                "retained_at": str(dest),
                "retained_sha256": sha,
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="阶段回顾检验白板构建器 (preview 只读 / create 恰 1 新文件 / undo 字节回退)"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    # round-3 M7: 默认戳取 **UTC** — 原先用本地墙钟却给 created_at 贴 Z,
    # 与 start-exam-board 的 `date -u` 分属两个时钟 (Asia/Shanghai 快 8h),
    # 导致 exam_history 按 created_at 排序错位。
    default_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    for name in ("preview", "create"):
        p = sub.add_parser(name)
        p.add_argument("--vault", required=True)
        p.add_argument(
            "--boards", nargs="+", required=True, help="原白板 stem 列表 (≥1)"
        )
        p.add_argument(
            "--anchor", default=None, help="锚板 (文件名主干; 缺省=第一块板)"
        )
        p.add_argument(
            "--ts",
            default=default_ts,
            help="时间戳 YYYY-MM-DD-HHMM (**UTC**; preview→create 传同值)",
        )
        if name == "create":
            # round-4 H5: 原为可选 → 省略即退回"同 ts 靠巧合"的不安全语义,
            # 且测试 helper 自己也在省略。改为 **required**: 没有用户确认过的
            # 字节指纹就没有 create。
            p.add_argument(
                "--expect-content-sha",
                required=True,
                help="preview 回执的 content_sha256（必传）— 不符即拒，绑定用户确认过的字节",
            )
    u = sub.add_parser("undo")
    u.add_argument("--vault", required=True)
    u.add_argument(
        "--path", required=True, help="create 回执里的 created_path (vault 相对路径)"
    )
    u.add_argument("--expect-sha", required=True, help="create 回执里的 content_sha256")
    u.add_argument("--undo-dir", required=True, help="vault 外留痕目录")
    args = ap.parse_args()
    return {"preview": cmd_preview, "create": cmd_create, "undo": cmd_undo}[args.cmd](
        args
    )


if __name__ == "__main__":
    sys.exit(main())
