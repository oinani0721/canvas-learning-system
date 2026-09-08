"""CARD-W4-4b 负控：把 Codex 点名的**宽松写法**临时写进生产代码，看旧门放不放行。

用法（由 m7-negctl.sh 调）::

    python negctl_patch.py apply <case>     # 打变异，成功即 exit 0
    python negctl_patch.py verify <case>    # 只检查语法与锚点，不改文件

设计要点（都是踩过的坑）：

* **锚点必须唯一**：每处替换断言 ``count == 1``。锚点漂移（0 命中）或撞车（>1）一律
  当场失败 —— 「变异没打进去」被读成「门没抓住」是假 SURVIVED 的头号来源。
* **变异后立刻 ``ast.parse``**：语法不合法的变异体会让门因「模块导不进来」而红，
  那是**假杀**（门因别的原因红，不是因为它声称的那条断言）。
* **不负责还原**：还原由调用方的 EXIT trap 从字节副本无条件做，并用 sha 复核。
  把还原写在这里 = 脚本被 SIGTERM 打断时变异体留在生产文件里。
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
GUARD = ROOT / "backend/tests/support/live_port_guard.py"

# ── 锚点（本卡实测，2026-09-08） ─────────────────────────────────────────────
FINALIZE_BODY = (
    "        with self._lock:\n"
    "            self.finalizing = True\n"
    "            return self._ledger_locked(stamp=True)"
)
LOCK_INIT = "        self._lock = threading.Lock()\n"
SELFTEST_IF = "            if _is_selftest_address(address):\n"
SEAM_TRY = (
    "            try:\n"
    "                _finalize_race_seam_hook()\n"
    "            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流\n"
    "                pass\n"
)
CONNECT_IF = '    if event == "socket.connect":\n'
INSTALL_TAIL = (
    "    _install_audit_hook()\n"
    "    register_final_accounting()\n"
    '    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":\n'
    "        assert_neo4j_target_blocked()\n"
)
FINAL_PUBLISH = (
    "            # 同一份快照，不再取第二次；经 _publish_ledger ⇒ 若迟到线程已经发布了\n"
    "            # 更新的一份，这里不回写（MEDIUM-4 的陈旧覆盖）。\n"
    "            _publish_ledger(path, ledger)\n"
)


def _edits(case: str) -> list[tuple[pathlib.Path, str, str]]:
    """返回 (文件, 旧串, 新串) 列表。每条都必须在文件里**恰好**出现一次。"""
    if case == "1":
        # M7① 旧门对 ast.dump 做子串匹配 ⇒ 换成另一把锁也照样绿。
        return [
            (GUARD, LOCK_INIT, LOCK_INIT + "        self._unrelated_lock = threading.Lock()\n"),
            (GUARD, FINALIZE_BODY, FINALIZE_BODY.replace("with self._lock:", "with self._unrelated_lock:")),
        ]
    if case == "2":
        # M7② 旧门是黑名单 ⇒ 名单外的新 self 调用一律漏网。
        helper = "    def _not_a_locked_helper(self) -> None:\n        return None\n\n"
        return [
            (
                GUARD,
                FINALIZE_BODY,
                "        with self._lock:\n"
                "            self.finalizing = True\n"
                "            self._not_a_locked_helper()\n"
                "            return self._ledger_locked(stamp=True)",
            ),
            (GUARD, "    def late_snapshot(self)", helper + "    def late_snapshot(self)"),
        ]
    if case == "3":
        # M7③ 旧门只查旧拼写 _FINALIZING ⇒ 新拼写的锁外读漏网。
        return [(GUARD, SELFTEST_IF, "            if STATE.finalizing:\n                pass\n" + SELFTEST_IF)]
    if case == "4":
        # M7④ 旧门按 ast.walk 数下标 ⇒ 恒假分支里的诱饵也算数。
        return [
            (
                GUARD,
                INSTALL_TAIL,
                "    if False:\n"
                "        _install_audit_hook()\n"
                "    register_final_accounting()\n"
                '    if os.environ.get(ENV_REQUIRE_BLOCKED_TARGET) == "1":\n'
                "        assert_neo4j_target_blocked()\n"
                "    _install_audit_hook()\n",
            )
        ]
    if case == "5a":
        # M7⑤ 旧门只要「存在一条含它的 Expr」⇒ if False: 里那条也算。
        return [
            (
                GUARD,
                SEAM_TRY,
                "            try:\n"
                "                if False:\n"
                "                    _finalize_race_seam_hook()\n"
                "            except BaseException:  # noqa: BLE001 —— 见上：注入点不得影响控制流\n"
                "                pass\n",
            )
        ]
    if case == "5b":
        # M7⑤ 旧门不管它落在哪个分支 ⇒ 提到受拦分支外面照样绿。
        return [
            (GUARD, SEAM_TRY, ""),
            (GUARD, CONNECT_IF, CONNECT_IF + "        _finalize_race_seam_hook()\n"),
        ]
    if case == "m4":
        # M4 修前对照：结算路径退回直接 write_ledger（没有发布顺序控制）。
        return [(GUARD, FINAL_PUBLISH, "            write_ledger(path, ledger)\n")]
    raise SystemExit(f"未知 case: {case}")


def main() -> int:
    action, case = sys.argv[1], sys.argv[2]
    edits = (_review_edits if case.startswith("r") else _edits)(case)
    touched: dict[pathlib.Path, str] = {}
    for path, old, new in edits:
        src = touched.get(path) or path.read_text(encoding="utf-8")
        hits = src.count(old)
        if hits != 1:
            print(f"ANCHOR-FAIL: {path.name} 里锚点出现 {hits} 次（期望 1）: {old[:60]!r}")
            return 2
        touched[path] = src.replace(old, new, 1)
    for path, src in touched.items():
        try:
            ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            print(f"MUTANT-SYNTAX-INVALID: {path.name}: {exc}")
            return 3
    if action == "verify":
        print(f"ANCHORS-OK: case={case} files={[p.name for p in touched]}")
        return 0
    for path, src in touched.items():
        path.write_text(src, encoding="utf-8")
    print(f"MUTANT-APPLIED: case={case} files={[p.name for p in touched]}")
    return 0


def _review_edits(case: str) -> list[tuple[pathlib.Path, str, str]]:
    """自查复核（2026-09-08 对抗性 review）发现的两个缺陷的**修前形态**。"""
    if case == "r1":
        # 复核 MEDIUM：_block_message 退回裸 {address!r}（恶意 __repr__ 劫持拒因绑定）
        return [
            (
                GUARD,
                'f"{BLOCK_REASON}: {_safe_repr(address)}. "',
                'f"{BLOCK_REASON}: {address!r}. "',
            )
        ]
    if case == "r2":
        # 复核 MEDIUM：_PUBLISHED_SEQ 退回「写盘成功之后才推进」（I/O 失败重开 M4 的门）
        return [
            (
                GUARD,
                "        _PUBLISHED_SEQ = seq  # 先行推进：写盘失败也不许更旧的再写（见上）\n"
                "        write_ledger(path, ledger)\n"
                "        return True",
                "        write_ledger(path, ledger)\n"
                "        _PUBLISHED_SEQ = seq\n"
                "        return True",
            )
        ]
    raise SystemExit(f"未知 review case: {case}")


if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
