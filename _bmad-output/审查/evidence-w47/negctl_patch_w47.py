"""CARD-W4-7 负控：把「被否掉的设计」临时写进生产代码，看旧门放不放行。

用法（由 h2-negctl.sh / m1-negctl.sh 调）::

    python negctl_patch_w47.py apply <case>     # 打变异，成功即 exit 0
    python negctl_patch_w47.py verify <case>    # 只检查语法与锚点，不改文件

设计要点（沿用 W4-4b 那套，都是踩过的坑）：

* **锚点必须唯一**：每处替换断言 ``count == 1``。锚点漂移（0 命中）或撞车（>1）
  一律当场失败 —— 「变异没打进去」被读成「门没抓住」是假 SURVIVED 的头号来源。
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

# ── 锚点（本卡实测，2026-09-08，U7-B 位移后）─────────────────────────────────
SENTINEL_ASSIGN = '_SELFTEST_HOST = "\\x00w4-live-port-guard-selftest"\n'
CLASSIFIER_TAIL = "    return type(host) is str and host == _SELFTEST_HOST  # noqa: E721 —— str 子类不算\n"


def _edits(case: str) -> list[tuple[pathlib.Path, str, str]]:
    """返回 (文件, 旧串, 新串) 列表。每条都必须在文件里**恰好**出现一次。"""
    if case == "h2":
        # RV-C H-2：哨兵常量换成普通主机名。原 6 条用例全都拦不住这一手 ——
        # 4 条以该常量为输入/期望值（跟着一起变），2 条本就不看它。
        return [(GUARD, SENTINEL_ASSIGN, '_SELFTEST_HOST = "localhost"\n')]
    if case == "m1":
        # RV-C M-1：分类器只判「host 是精确 str」，不再比对哨兵值 ——
        # Codex 原话：该类六个测试仍能满足。后果是每条到 7691 的真实连接
        # 都被判成自证 ⇒ 不记账 ⇒ 结账无从据此拒绝 rc=0。
        return [(GUARD, CLASSIFIER_TAIL, "    return type(host) is str  # noqa: E721 —— 负控变异体\n")]
    if case == "r1-high1":
        # Codex round-1 HIGH-1 修前形态：extract_port 只捕 Exception（漏 BaseException）
        return [(GUARD, "    except BaseException:  # noqa: BLE001 —— 见下：这里只能 fail-closed，不能让异常逸出\n",
                 "    except Exception:  # noqa: BLE001 —— 负控：退回只捕 Exception\n")]
    if case == "r1-high2":
        # Codex round-1 HIGH-2 修前形态：str 子类一律放行（比旧实现更宽的判定回退）
        return [(
            GUARD,
            "    if not isinstance(name, str):\n        return False\n"
            "    # 未绑定调用 ⇒ 走 str 自己的实现，子类重载骗不过（同 tuple.__len__/__getitem__ 的用法）\n"
            "    return str.__eq__(name, \"uvloop\") is True or str.startswith(name, \"uvloop.\")\n",
            "    if type(name) is not str:  # noqa: E721 —— 负控：退回一律放行 str 子类\n"
            "        return False\n"
            "    return name == \"uvloop\" or name.startswith(\"uvloop.\")\n",
        )]
    if case == "r2-med1":
        # round-2 Codex MEDIUM-1 给的静态反例：它能满足上一版的说谎子类用例
        # （取反型 "uvloop" / "json"），却放行 uvloop.loop。
        return [(
            GUARD,
            '    return str.__eq__(name, "uvloop") is True or str.startswith(name, "uvloop.")\n',
            '    return str.__eq__(name, "uvloop") is True or (\n'
            '        str.startswith(name, "uvloop.") and name.startswith("uvloop.")\n'
            '    )\n',
        )]
    if case == "r3-med1":
        # round-3 Codex MEDIUM-1 给的静态反例：对子模块分支冗余地排除根名。
        # 实测它放行 uvloop.loop-affirmer（重载相等恒真 ⇒ not(name=="uvloop") 为假）。
        return [(
            GUARD,
            '    return str.__eq__(name, "uvloop") is True or str.startswith(name, "uvloop.")\n',
            '    return str.__eq__(name, "uvloop") is True or (\n'
            '        str.startswith(name, "uvloop.") and not (name == "uvloop")\n'
            '    )\n',
        )]
    raise SystemExit(f"未知 case: {case}")


def main() -> int:
    action, case = sys.argv[1], sys.argv[2]
    edits = _edits(case)
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


if __name__ == "__main__":
    sys.exit(main())
