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
SRC = (
    WT
    / "canvas-vault"
    / ".claude"
    / "skills"
    / "board-recap"
    / "scripts"
    / "recap_exam_build.py"
)
TEST = WT / "backend" / "tests" / "skills" / "test_g5_9_recap_exam.py"
BACKUP = Path("/tmp") / "recap_exam_build.negverify.bak"
PY = WT / "backend" / ".venv" / "bin" / "python"

# 目录级 symlink 守卫在 _prepare 与 cmd_undo 各有一份（同文），变体 D 需要
# 用各自**独一无二的前置注释**锚定，否则 count(old) == 2 直接判变体失效。
_GUARD_BODY = (
    '    for sub in (BOARD_DIR, "节点", EXAM_DIR):\n'
    "        d = vault / sub\n"
    "        if not d.exists():\n"
    "            continue\n"
    "        try:\n"
    "            escaped = not d.resolve().is_relative_to(vault_resolved)\n"
    "        except (OSError, ValueError):\n"
    "            escaped = True\n"
    "        if escaped:\n"
)
_PREPARE_GUARD = (
    "    # 目录级 symlink 守卫 (与 recap_scan 同语义)\n    vault_resolved = vault.resolve()\n"
    + _GUARD_BODY
)
_PREPARE_GUARD_OFF = (
    "    # 目录级 symlink 守卫 (与 recap_scan 同语义)\n    vault_resolved = vault.resolve()\n"
    + _GUARD_BODY.replace("        if escaped:\n", "        if False:\n")
)


# dirfd 锚定是 HIGH-4 的**第三层**防御（前两层 = _prepare 目录守卫 + _symlink_probe）。
# 任何声称「回退 HIGH-4」的变体都必须把这一层一并关掉，否则拒绝来自它、
# 会得出「门非承重」的错误结论（变体 D/I 首跑各踩过一次）。
_DIRFD_OFF: list[tuple[str, str]] = [
    (
        "        dfd = os.open(exam, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)",
        "        dfd = os.open(exam, os.O_RDONLY | os.O_DIRECTORY)",
    ),
    (
        "    if (st_dfd.st_dev, st_dfd.st_ino) != (st_path.st_dev, st_path.st_ino):",
        "    if False:",
    ),
    (
        "    if st_dfd.st_dev != st_vault.st_dev:",
        "    if False:",
    ),
    # round-4 起 `_dirfd_still_in_vault` 的 S_ISLNK 检查成了第四层 —— 任何声称
    # 「回退 HIGH-4/父目录防护」的变体都必须连它一起禁, 否则拒绝来自它。
    (
        "    if stat.S_ISLNK(st_now.st_mode):",
        "    if False:",
    ),
    (
        "            if moved:",
        "            if False:",
    ),
]
_PATH_BASED_OPS: list[tuple[str, str]] = [
    (
        "        fd = os.open(tmp_name, flags, 0o644, dir_fd=dir_fd)",
        "        fd = os.open(tmp, flags, 0o644)",
    ),
    (
        "        os.link(\n"
        "            tmp_name, target_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd\n"
        "        )  # EEXIST 绝不覆盖",
        "        os.link(tmp, target)  # EEXIST 绝不覆盖",
    ),
    (
        "        vfd = os.open(target_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)",
        "        vfd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)",
    ),
]

# (变体名, 说明, [(old, new), ...], 期望变红的 -k 选择式)
# 一个变体可含**多处**替换 —— 纵深防御的性质必须同时禁掉所有层，否则只禁一层
# 测试仍绿，会得出「门非承重」的错误结论（变体 D 首跑实测踩过这一点）。
VARIANTS: list[tuple[str, str, list[tuple[str, str]], str]] = [
    (
        "A",
        "HIGH-1 回退: --expect-content-sha 恢复 falsy 短路（空串绕过用户确认）",
        [
            (
                '    if not _SHA256_RE.match(args.expect_content_sha or ""):\n'
                "        return _fail_env(\n"
                '            "--expect-content-sha 必须是 preview 回执里的 64 位小写十六进制 "\n'
                '            "content_sha256（空串或非法形状一律拒绝，防绕过用户确认）"\n'
                "        )\n"
                "    if args.expect_content_sha != sha:",
                "    if args.expect_content_sha and args.expect_content_sha != sha:",
            )
        ],
        "test_create_rejects_malformed_expect_content_sha",
    ),
    (
        "B",
        "HIGH-1 同型回退: undo 的 --expect-sha 去掉形状白名单",
        [
            (
                '    if not _SHA256_RE.match(args.expect_sha or ""):\n'
                "        return _fail_env(\n"
                '            "--expect-sha 必须是 create 回执里的 64 位小写十六进制 content_sha256"\n'
                "        )\n",
                "",
            )
        ],
        "test_undo_rejects_malformed_expect_sha",
    ),
    (
        "C",
        "HIGH-4 survivor 复现: 从 wikilink 禁止集里只移除 `|`",
        [
            (
                'bad = [s for s in stems if any(c in s for c in "#|^][")]',
                'bad = [s for s in stems if any(c in s for c in "#^][")]',
            )
        ],
        "test_board_name_rejects_each_wikilink_char",
    ),
    (
        "D",
        "HIGH-4 survivor 复现: 同时禁用目录守卫 + _symlink_probe + dirfd 锚定（纵深三层）",
        [
            (_PREPARE_GUARD, _PREPARE_GUARD_OFF),
            (
                "    for p in (vault / EXAM_DIR, target, tmp):\n        if p.is_symlink():",
                "    for p in (vault / EXAM_DIR, target, tmp):\n        if False:",
            ),
            *_DIRFD_OFF,
        ],
        "test_create_refuses_symlinked_exam_dir_with_valid_sha or test_create_refuses_tmp_symlink_with_valid_sha",
    ),
    (
        "E",
        "HIGH-2(a) 回退: 发布后只比 (dev,ino)，不回读字节",
        [
            (
                "        if not same_inode or hashlib.sha256(got).hexdigest() != want_sha:",
                "        if not same_inode:",
            )
        ],
        "test_atomic_write_rejects_inplace_rewritten_publish",
    ),
    (
        "F",
        "HIGH-2(b) 回退: inode 不符时按路径 unlink（会删掉并发者的文件）",
        [
            (
                "            raise OSError(\n"
                '                "published inode mismatch (concurrent replacement; 未删除该文件)"\n'
                "            )",
                "            try:\n"
                "                target.unlink()\n"
                "            except OSError:\n"
                "                pass\n"
                '            raise OSError("published inode mismatch")',
            )
        ],
        "test_atomic_write_does_not_delete_concurrent_replacement",
    ),
    (
        "G",
        "HIGH-3(2) 回退: 删源前不回读校验留痕字节",
        [
            (
                "    if st_dest.st_size != len(raw) or hashlib.sha256(back).hexdigest() != sha:",
                "    if False:",
            )
        ],
        "test_undo_refuses_when_retention_bytes_corrupted",
    ),
    (
        "I",
        "主session HIGH-4 回退: 写侧从 dirfd 锚定退回按路径 open/link",
        [*_DIRFD_OFF, *_PATH_BASED_OPS],
        "test_create_refuses_when_exam_dir_swapped_after_probe",
    ),
    (
        "J",
        "主session HIGH-5 回退: undo 恢复对 leaf symlink 的 resolve (移走 referent)",
        [
            (
                "    raw_target = vault / args.path\n"
                "    if raw_target.is_symlink():\n"
                "        return _fail_env(\n"
                '            f"undo 目标是 symlink, 拒绝 (回退语义对别名无定义, 避免移走 referent "\n'
                '            f"并留下死链): {args.path}"\n'
                "        )\n"
                "    target = raw_target.resolve()",
                "    target = (vault / args.path).resolve()",
            )
        ],
        "test_undo_refuses_symlink_alias_instead_of_moving_referent",
    ),
    (
        "K",
        "round-3 HIGH-1 回退: 去掉写入后「dfd 是否仍是 vault 内那个目录」的复核",
        [
            (
                "        if not write_err:\n"
                "            moved = _dirfd_still_in_vault(dfd, vault)\n"
                "            if moved:",
                "        if False:\n"
                "            moved = _dirfd_still_in_vault(dfd, vault)\n"
                "            if moved:",
            )
        ],
        "test_create_detects_exam_dir_moved_out_of_vault_after_anchor or "
        "test_create_detects_exam_dir_swapped_to_another_dir_after_anchor",
    ),
    (
        "L",
        "round-3 HIGH-2 回退: 失败路径不再撤销已发布的 target",
        [
            (
                "        if published:\n"
                "            rb_state, rb_err2 = _rollback_published(",
                "        if False:\n"
                "            rb_state, rb_err2 = _rollback_published(",
            )
        ],
        "test_atomic_write_rolls_back_when_readback_raises",
    ),
    (
        "M",
        "round-3 HIGH-3 回退: 撤销前不再复核 identity、且吞掉 unlink 失败",
        [
            (
                "    if identity is not None and (st_now.st_dev, st_now.st_ino) != identity:\n"
                '        return "kept", None  # 已不是我们的 inode ⇒ 是别人的文件, 绝不删',
                '    if False:\n        return "kept", None',
            ),
            (
                '        return "kept", f"撤销结果未确认 (unlink 失败 {type(e).__name__}), 目标可能仍在"',
                "        pass",
            ),
        ],
        "test_rollback_published_refuses_to_delete_someone_elses_file or "
        "test_rollback_published_reports_unlink_failure_instead_of_swallowing",
    ),
    (
        "N",
        "round-3 HIGH-4 回退: _fsync_dir 恢复 fail-open + undo 不再据此拒绝",
        [
            (
                '                return "failed", f"目录 fsync 失败 {type(e).__name__}"',
                '                return "ok", None',
            ),
            (
                '    dsync_err = dsync_msg if dsync_state in ("failed", "unsupported") else None\n'
                "    if dsync_err:",
                '    dsync_err = dsync_msg if dsync_state in ("failed", "unsupported") else None\n'
                "    if False:",
            ),
        ],
        "test_undo_refuses_when_retention_dir_fsync_fails or "
        "test_fsync_dir_reports_failure_instead_of_silently_succeeding",
    ),
    (
        "O",
        "round-4 HIGH-1 回退: 写入后复核改回 os.stat (跟随 symlink) 且不拒 symlink",
        [
            (
                "        st_now = os.lstat(vault / EXAM_DIR)",
                "        st_now = os.stat(vault / EXAM_DIR)",
            ),
            ("    if stat.S_ISLNK(st_now.st_mode):", "    if False:"),
        ],
        "test_create_detects_exam_dir_replaced_by_symlink_alias",
    ),
    (
        "P",
        "round-4 HIGH-2/3 回退: 撤销未完成时不再写进回执",
        [("        if rollback_note:", "        if False:")],
        "test_atomic_write_reports_target_left_behind_when_rollback_refuses",
    ),
    (
        "Q",
        "round-4 HIGH-4 回退: EPERM 重新并入 fsync 豁免集",
        [
            (
                "            if errno_ in (errno.EINVAL, errno.ENOTSUP):",
                "            if errno_ in (errno.EINVAL, errno.ENOTSUP, errno.EPERM):",
            )
        ],
        "test_fsync_dir_does_not_treat_eperm_as_unsupported",
    ),
    (
        "R",
        "round-4 HIGH-5 回退: 删源后的目录 fsync 结果重新被忽略",
        [
            (
                '                    if src_state == "ok"',
                "                    if True",
            )
        ],
        "test_undo_warns_when_source_dir_fsync_unconfirmed",
    ),
    (
        "S",
        "round-4 LOW-1 回退: 双空判据恢复无条件删除",
        [
            (
                "    if identity is None and expect_sha is None:",
                "    if False:",
            )
        ],
        "test_rollback_published_refuses_without_any_criterion",
    ),
    (
        "T",
        'round-5 HIGH-1 回退: undo 只挡 "failed", "unsupported" 照样删源',
        [
            (
                '    dsync_err = dsync_msg if dsync_state in ("failed", "unsupported") else None',
                '    dsync_err = dsync_msg if dsync_state == "failed" else None',
            )
        ],
        "test_undo_refuses_when_retention_dir_fsync_unsupported",
    ),
    (
        "U",
        "round-5 HIGH-2a 回退: 第二次撤销成功时不清旧 rollback_note",
        [
            (
                '            if rb_state in ("deleted", "absent"):\n'
                "                rollback_note, rollback_deleted = None, False\n"
                '            elif rb_state == "deleted_unsynced":\n'
                "                rollback_note, rollback_deleted = rb_err2, True",
                "            if False:\n"
                "                rollback_note, rollback_deleted = None, False\n"
                '            elif rb_state == "deleted_unsynced":\n'
                "                rollback_note, rollback_deleted = rb_err2, True",
            )
        ],
        "test_atomic_write_clears_stale_rollback_note_on_second_success",
    ),
    (
        "V",
        'round-5 HIGH-2b 回退: unlink 后不 fsync 目录, 直接报 "deleted"',
        [
            (
                "    try:\n        os.fsync(dir_fd)\n    except OSError as e:",
                "    try:\n        pass\n    except OSError as e:",
            )
        ],
        "test_rollback_reports_unsynced_when_dir_fsync_fails",
    ),
    (
        "W",
        "round-5 LOW-1 回退: 成功路径不再单列 tmp 的 FileNotFoundError",
        [
            (
                "    except FileNotFoundError:\n"
                "        # round-5 LOW-1: tmp 已被并发清掉是**正常**结果, 不是「未能清理」。\n"
                "        # 失败路径早已单列了它, 成功路径漏了 ⇒ 会发出误导性的「请手动删除」。\n"
                "        pass\n"
                "    except OSError as e:",
                "    except OSError as e:",
            )
        ],
        "test_atomic_write_no_false_warning_when_tmp_already_gone",
    ),
    (
        "X",
        "round-5 MEDIUM-2 回退: _fsync_dir 去掉 O_DIRECTORY|O_NOFOLLOW",
        [
            (
                "        fd = os.open(d, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)",
                "        fd = os.open(d, os.O_RDONLY)",
            )
        ],
        "test_fsync_dir_refuses_symlink_path",
    ),
    (
        "H",
        "HIGH-3(1) 回退: 去掉紧贴 unlink 前的 identity 复核",
        [
            (
                "    if (st_pre_unlink.st_dev, st_pre_unlink.st_ino) != identity:",
                "    if False:",
            )
        ],
        "test_undo_refuses_when_target_swapped_before_unlink",
    ),
    (
        "Y",
        'round-6 反例1 回退: EINVAL/ENOTSUP 落回 "deleted"',
        [
            (
                '        if getattr(e, "errno", None) in (errno.EINVAL, errno.ENOTSUP):',
                "        if False:",
            )
        ],
        "test_rollback_always_reports_unsynced_when_fsync_unconfirmed",
    ),
    (
        "Z",
        "round-6 反例1b 回退: 不再封闭非 OSError(删后异常外逸=无回执)",
        [
            (
                "    except Exception as e:  # noqa: BLE001",
                "    except ValueError as e:  # 故意收窄",
            )
        ],
        "test_rollback_does_not_leak_non_oserror_after_unlink",
    ),
    (
        "AA",
        "round-6 反例2 回退: 首次撤销分支重新读错变量名(UnboundLocalError)",
        [
            (
                '                    rollback_note = rb_err if rb_state == "deleted_unsynced" else None',
                '                    rollback_note = rb_err2 if rb_state == "deleted_unsynced" else None',
            )
        ],
        "test_atomic_write_first_rollback_unsynced_yields_structured_receipt",
    ),
    (
        "AB",
        "round-6 反例3 回退: 回执文案不再区分「已删未确认」与「仍在」",
        [("            if rollback_deleted:", "            if False:")],
        "test_atomic_write_first_rollback_unsynced_yields_structured_receipt",
    ),
    (
        "AC",
        "round-7 阻断3B 回退: unlink 的 FileNotFoundError 重新泛化为 kept",
        [
            (
                "    except FileNotFoundError:\n"
                '        # ⛔ round-7 阻断 3B: 原实现把它泛化成 "kept" ⇒ 调用方声称「目标仍在\n'
                "        # vault 里」，而路径**实际已经不存在**（lstat 看见之后被并发者删掉）。\n"
                "        # 这是确定性的「回执与实际副作用相反」。归 absent 才是事实。\n"
                '        return "absent", None\n'
                "    except OSError as e:",
                "    except OSError as e:",
            )
        ],
        "test_rollback_reports_absent_when_target_vanished_before_unlink",
    ),
    (
        "AD",
        "round-7 阻断3B 回退: unlink 其他错误恢复断言式措辞",
        [
            (
                '        return "kept", f"撤销结果未确认 (unlink 失败 {type(e).__name__}), 目标可能仍在"',
                '        return "kept", f"unlink 失败 {type(e).__name__}"',
            )
        ],
        "test_rollback_unconfirmed_wording_is_conservative",
    ),
    (
        "AE",
        "round-7 阻断3A 回退: 第三调用点去掉崩溃重现警示",
        [
            (
                '                        "崩溃后目标可能重现, 请复查该路径)"',
                '                        ")"',
            )
        ],
        "test_create_third_callsite_unsynced_has_crash_warning",
    ),
    (
        "AF",
        "round-8 HIGH-1 回退: 回读块的 FileNotFoundError 重新被宽泛 OSError 兜住",
        [
            (
                "        except FileNotFoundError:\n"
                "            # ⛔ round-8 HIGH-1: 3B 只修了 unlink 那一半, **回读块仍被宽泛的\n"
                "            # except OSError 兜住**。可达路径: lstat 成功 → 并发者删文件 →\n"
                "            # os.open 抛 FileNotFoundError → 被归 kept ⇒ 回执说「目标可能仍在」，\n"
                "            # 而它**已经不存在**。与 unlink 侧同理, 必须归 absent。\n"
                '            return "absent", None\n'
                "        except OSError as e:",
                "        except OSError as e:",
            )
        ],
        "test_rollback_reports_absent_when_target_vanished_before_readback",
    ),
    (
        "AG",
        "round-8 HIGH-2 矩阵门①②: 首次撤销把 deleted_unsynced 误当无需说明",
        [
            (
                '                    rollback_note = rb_err if rb_state == "deleted_unsynced" else None',
                "                    rollback_note = None",
            )
        ],
        "test_matrix_callsite1_2_consumes_each_state",
    ),
    (
        "AH",
        "round-8 HIGH-2 矩阵门③: 目录移出分支的 absent 文案错用 deleted 文案",
        [
            (
                '                    "absent": " (该文件已不存在)",',
                '                    "absent": " (已撤销该文件)",',
            )
        ],
        "test_matrix_callsite3_consumes_each_state",
    ),
]


# ⛔ 独立冻结的变体名集合(round-8 HIGH-3) —— **不得由 VARIANTS 推导**,
# 否则误删变体时两边一起变、自检恒真。改动变体清单时必须手工同步这里。
EXPECTED_NAMES: frozenset[str] = frozenset(
    "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z AA AB AC AD AE AF AG AH".split()
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_pytest(selector: str | None) -> tuple[int, str]:
    cmd = [
        str(PY),
        "-m",
        "pytest",
        str(TEST),
        "-q",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:warnings",
        "--override-ini=addopts=",
    ]
    if selector:
        cmd += ["-k", selector]
    r = subprocess.run(
        cmd, capture_output=True, text=True, cwd=WT / "backend", timeout=900
    )
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
    executed_names: list[str] = []
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
                print(
                    f"  ❌ 第 {i} 处 mutation 命中 {hits} 处（须恰好 1）——变体失效，不能据此宣称承重"
                )
                bad = True
                break
            text = text.replace(old, new, 1)
        if bad:
            ok = False
            continue
        SRC.write_text(text, encoding="utf-8")
        try:
            rc, line = run_pytest(selector)
            executed_names.append(name)  # ⚠️ 只有 pytest **真的跑过**才记名
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

    # ⛔ round-8 HIGH-3: round-7 那版自检门是**循环论证** —— `ran` 在 mutation 校验和
    # pytest 执行**之前**就自增, 而「声明数」又取同一个 VARIANTS 的长度。
    # 于是再误删 W/X 时两个数会**一起减少, 仍显示一致**; mutation 未命中、pytest
    # 根本没跑, 也照样计入「实跑」。它抓不到它本该抓的那个失败。
    # ⇒ 改为三条独立判据:
    #   ① EXPECTED_NAMES 是**独立冻结**的常量(不由 VARIANTS 推导);
    #   ② executed_names 只在 pytest **真的返回**之后才追加;
    #   ③ 定义集合 / 唯一性 / 执行集合三者必须完全一致。
    print("\n=== 变体清单自检(独立冻结集合) ===")
    defined = [v[0] for v in VARIANTS]
    print(
        f"  冻结期望 {len(EXPECTED_NAMES)} 个 / 定义 {len(defined)} 个 / 实跑 {len(executed_names)} 个"
    )
    if len(defined) != len(set(defined)):
        dup = sorted({n for n in defined if defined.count(n) > 1})
        print(f"  ❌ 变体名重复: {dup}")
        ok = False
    if set(defined) != EXPECTED_NAMES:
        print(
            f"  ❌ 定义集合 != 冻结期望; 缺失={sorted(EXPECTED_NAMES - set(defined))} 多余={sorted(set(defined) - EXPECTED_NAMES)}"
        )
        print(
            "     (若确实新增/删除了变体, 请**同步更新 EXPECTED_NAMES 常量**并在处置表说明)"
        )
        ok = False
    if set(executed_names) != EXPECTED_NAMES:
        print(
            f"  ❌ 实跑集合 != 冻结期望; 未执行={sorted(EXPECTED_NAMES - set(executed_names))}"
        )
        ok = False
    if ok:
        print("  ✅ 冻结期望 / 定义 / 实跑 三者完全一致")

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
