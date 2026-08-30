#!/usr/bin/env python3
"""CARD-收口A ③ — G5-9 codex round-1 四条 HIGH 整改的负验证。

判据：把实现里每一条新判定**改回整改前的形态**，对应的新门必须变红；
      全部变体跑完后，被测文件字节须与备份**逐字相同**，且完整套件全绿。

⛔ 必须串行运行（脚本原地改被测文件；并发会让 B 的还原把 A 的 mutation 写回，
   而测试照样全绿 —— 本项目踩过的坑，见 MEMORY reference_mutation_script_serial_only）。

用法: cd backend && .venv/bin/python ../_bmad-output/审查/g5-9-evidence/round1-high-negverify.py
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
SRC = WT / "canvas-vault" / ".claude" / "skills" / "board-recap" / "scripts" / "recap_exam_build.py"
TEST = WT / "backend" / "tests" / "skills" / "test_g5_9_recap_exam.py"
BACKUP = Path("/tmp") / "recap_exam_build.negverify.bak"
PY = WT / "backend" / ".venv" / "bin" / "python"

# 目录级 symlink 守卫在 _prepare 与 cmd_undo 各有一份（同文），变体 D 需要
# 用各自**独一无二的前置注释**锚定，否则 count(old) == 2 直接判变体失效。
_GUARD_BODY = (
    "    for sub in (BOARD_DIR, \"节点\", EXAM_DIR):\n"
    "        d = vault / sub\n"
    "        if not d.exists():\n"
    "            continue\n"
    "        try:\n"
    "            escaped = not d.resolve().is_relative_to(vault_resolved)\n"
    "        except (OSError, ValueError):\n"
    "            escaped = True\n"
    "        if escaped:\n"
)
_PREPARE_GUARD = "    # 目录级 symlink 守卫 (与 recap_scan 同语义)\n    vault_resolved = vault.resolve()\n" + _GUARD_BODY
_PREPARE_GUARD_OFF = "    # 目录级 symlink 守卫 (与 recap_scan 同语义)\n    vault_resolved = vault.resolve()\n" + _GUARD_BODY.replace(
    "        if escaped:\n", "        if False:\n"
)

# (变体名, 说明, [(old, new), ...], 期望变红的 -k 选择式)
# 一个变体可含**多处**替换 —— 纵深防御的性质必须同时禁掉所有层，否则只禁一层
# 测试仍绿，会得出「门非承重」的错误结论（变体 D 首跑实测踩过这一点）。
VARIANTS: list[tuple[str, str, list[tuple[str, str]], str]] = [
    (
        "A",
        "HIGH-1 回退: --expect-content-sha 恢复 falsy 短路（空串绕过用户确认）",
        [(
            '    if not _SHA256_RE.match(args.expect_content_sha or ""):\n'
            "        return _fail_env(\n"
            '            "--expect-content-sha 必须是 preview 回执里的 64 位小写十六进制 "\n'
            '            "content_sha256（空串或非法形状一律拒绝，防绕过用户确认）"\n'
            "        )\n"
            "    if args.expect_content_sha != sha:",
            "    if args.expect_content_sha and args.expect_content_sha != sha:",
        )],
        "test_create_rejects_malformed_expect_content_sha",
    ),
    (
        "B",
        "HIGH-1 同型回退: undo 的 --expect-sha 去掉形状白名单",
        [(
            '    if not _SHA256_RE.match(args.expect_sha or ""):\n'
            "        return _fail_env(\n"
            '            "--expect-sha 必须是 create 回执里的 64 位小写十六进制 content_sha256"\n'
            "        )\n",
            "",
        )],
        "test_undo_rejects_malformed_expect_sha",
    ),
    (
        "C",
        "HIGH-4 survivor 复现: 从 wikilink 禁止集里只移除 `|`",
        [(
            'bad = [s for s in stems if any(c in s for c in "#|^][")]',
            'bad = [s for s in stems if any(c in s for c in "#^][")]',
        )],
        "test_board_name_rejects_each_wikilink_char",
    ),
    (
        "D",
        "HIGH-4 survivor 复现: 同时禁用目录 symlink 守卫与 _symlink_probe（纵深两层）",
        [
            (_PREPARE_GUARD, _PREPARE_GUARD_OFF),
            (
                "    for p in (vault / EXAM_DIR, target, tmp):\n        if p.is_symlink():",
                "    for p in (vault / EXAM_DIR, target, tmp):\n        if False:",
            ),
        ],
        "test_create_refuses_symlinked_exam_dir_with_valid_sha or test_create_refuses_tmp_symlink_with_valid_sha",
    ),
    (
        "E",
        "HIGH-2(a) 回退: 发布后只比 (dev,ino)，不回读字节",
        [(
            "        if not same_inode or hashlib.sha256(got).hexdigest() != want_sha:",
            "        if not same_inode:",
        )],
        "test_atomic_write_rejects_inplace_rewritten_publish",
    ),
    (
        "F",
        "HIGH-2(b) 回退: inode 不符时按路径 unlink（会删掉并发者的文件）",
        [(
            "            raise OSError(\n"
            '                "published inode mismatch (concurrent replacement; 未删除该文件)"\n'
            "            )",
            "            try:\n"
            "                target.unlink()\n"
            "            except OSError:\n"
            "                pass\n"
            '            raise OSError("published inode mismatch")',
        )],
        "test_atomic_write_does_not_delete_concurrent_replacement",
    ),
    (
        "G",
        "HIGH-3(2) 回退: 删源前不回读校验留痕字节",
        [(
            "    if st_dest.st_size != len(raw) or hashlib.sha256(back).hexdigest() != sha:",
            "    if False:",
        )],
        "test_undo_refuses_when_retention_bytes_corrupted",
    ),
    (
        "H",
        "HIGH-3(1) 回退: 去掉紧贴 unlink 前的 identity 复核",
        [(
            "    if (st_pre_unlink.st_dev, st_pre_unlink.st_ino) != identity:",
            "    if False:",
        )],
        "test_undo_refuses_when_target_swapped_before_unlink",
    ),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_pytest(selector: str | None) -> tuple[int, str]:
    cmd = [str(PY), "-m", "pytest", str(TEST), "-q", "-p", "no:cacheprovider",
           "-p", "no:warnings", "--override-ini=addopts="]
    if selector:
        cmd += ["-k", selector]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=WT / "backend", timeout=900)
    tail = [ln for ln in r.stdout.splitlines() if ln.strip()][-1:]
    return r.returncode, (tail[0] if tail else "<no output>")


def main() -> int:
    if not SRC.exists():
        print(f"FAIL 被测脚本不存在: {SRC}")
        return 1
    shutil.copy2(SRC, BACKUP)
    base_sha = sha(BACKUP)
    print(f"备份: {BACKUP} (sha {base_sha[:16]}…)\n")

    ok = True
    print("=== 基线: 完整套件应全绿 ===")
    rc, line = run_pytest(None)
    print(f"  {'✅' if rc == 0 else '❌'} 基线 exit={rc} | {line}")
    ok &= rc == 0

    for name, desc, pairs, selector in VARIANTS:
        print(f"\n=== 变体 {name}: {desc} ===")
        text = SRC.read_text(encoding="utf-8")
        bad = False
        for i, (old, new) in enumerate(pairs, 1):
            hits = text.count(old)
            if hits != 1:
                print(f"  ❌ 第 {i} 处 mutation 命中 {hits} 处（须恰好 1）——变体失效，不能据此宣称承重")
                bad = True
                break
            text = text.replace(old, new, 1)
        if bad:
            ok = False
            continue
        SRC.write_text(text, encoding="utf-8")
        try:
            rc, line = run_pytest(selector)
            if rc != 0:
                print(f"  ✅ 如期变红 | {line}")
            else:
                print(f"  ❌ 弱化实现后仍全绿 = 该门非承重 | {line}")
                ok = False
        finally:
            shutil.copy2(BACKUP, SRC)
            if sha(SRC) != base_sha:
                print("  ❌ 还原失败：字节与备份不一致")
                ok = False

    print("\n=== 还原后复核 ===")
    same = sha(SRC) == base_sha
    print(f"  {'✅' if same else '❌'} 字节与备份逐字相同 (sha {sha(SRC)[:16]}…)")
    ok &= same
    rc, line = run_pytest(None)
    print(f"  {'✅' if rc == 0 else '❌'} 还原后完整套件 exit={rc} | {line}")
    ok &= rc == 0

    print(f"\nRESULT: {'PASS — 全部新门均为承重门' if ok else 'FAIL — 见上方 ❌'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
