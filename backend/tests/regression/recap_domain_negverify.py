#!/usr/bin/env python3
"""维护卡 B · 负验证（变异）脚本 —— 证明双向门是**承重**的，不是摆设。

⛔ 三条铁律，全部来自踩过的坑：
  1. **必须串行**（MEMORY `reference_mutation_script_serial_only`）：本脚本原地改
     被测文件再还原，并发跑会让 B 的还原把 A 的 mutation 写回，而测试照样全绿。
     脚本自带互斥锁，重入直接拒绝。
  2. **变体必须禁掉该性质的全部防线**（MEMORY `reference_mutation_must_disable_all_layers`）：
     只退化一层时纵深防御会让测试仍绿，从而误判「门非承重」去改本来正确的测试。
  3. **还原后必须与备份逐字节相同**——这道自检本身抓出过"还原不干净"。

用法: python recap_domain_negverify.py   （无参数；退出码 0 = 全部如期变红）
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
PYTEST = ROOT / "backend/.venv/bin/pytest"
SUITE = "tests/regression/test_recap_scan_signals.py"
LOCK = Path(tempfile.gettempdir()) / "recap-domain-negverify.lock.d"

# 每条变体 = (名称, [(原文, 替换), ...], 期望至少变红的用例关键字)
# ⛔ 列表里给出的是**该性质的全部防线**，一次全禁——只禁一层会得到假绿。
MUTANTS: list[tuple[str, list[tuple[str, str]], str]] = [
    (
        "survivor-1 围栏闭合退回宽松判定（E1 全线：长度 + 尾随空白 两条一起禁）",
        [
            (
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[^\\S\\n]*$")',
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")',
            ),
            (
                'if (\n                mc\n                and mc.group("fence")[0] == fence[0]\n'
                '                and len(mc.group("fence")) >= len(fence)\n            ):',
                "if mc:",
            ),
        ],
        "four_fence_short_close or fence_close_needs_trailing_blank_only",
    ),
    (
        "survivor-2 规模行允许式去掉行尾锚（H-2 前半全线）",
        [
            (
                # ⛔ CARD-维护B-R2 (d): 允许式表已从 _verify_report 局部提为模块级
                # _FALLBACK_DERIVE_ALLOW，缩进 16→12 空格——锚点随之更新（变异性质不变）。
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"\n            r"\\s*/\\s*\\d+\\s*批注\\s*/?\\s*$"',
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"',
            )
        ],
        "scale_line_tail_append",
    ),
    (
        "survivor-3 种子行只查形状不绑值（H-2 后半全线）",
        [("    _verify_seed_ledger_counts(text, scan, problems)\n", "")],
        "seed_ledger_fake_count",
    ),
    (
        "survivor-4 信号行尾部退回开放式 + 恢复字符黑名单（H-3 全线）",
        [
            (
                "rf\"{sig['denominator']}\\s*{re.escape(tail)}\"",
                "rf\"{sig['denominator']}\\s*(?P<tail>[^【】]*)\"",
            )
        ],
        "signal_tail_append",
    ),
    (
        "survivor-5 D2 叙述域计数绑定整体关闭（本卡原始命题）",
        [("    _verify_prose_counts(text, scan, problems)\n", "")],
        "bare_count_in_prose",
    ),
    # ── CARD-维护B-R2 (g): 第七批复核 F-4 的三个 survivor + 本卡两处新面的承重变体。
    # 每条的 keyword 都指向 (b)-(e) 配的新承重门；隔离拷贝重放证据见验收单 4-A。
    (
        "survivor-6 S1 `_NODATA_REASONS` 增「任意原因」（F-4: 既有门只喂固定 bogus）",
        [('    "数据源不可用",\n)', '    "数据源不可用",\n    "任意原因",\n)')],
        "skill_sync_nodata_reasons_table or nodata_reason_outside_table",
    ),
    (
        "survivor-7 S3 围栏剥离退回单层（F-4: `> > ```` 逃逸 + Obsidian 渲染引用内代码块）",
        [
            (
                # ⛔ CARD-维护B-R2 round-3 锚点更新: bare 现为「引用+无序/有序/多层
                # 列表 marker」交替剥法 + 列表容器边界跟踪。变异性质不变——退回
                # "只剥一层引用"形态时, c1/c2/列表项围栏/r3 门都应变红。
                'bare = re.sub(r"^(?:[>\\s]|(?:[-*+]|\\d{1,9}[.)])[^\\S\\n]+)*", "", ln)',
                'bare = re.sub(r"^>?[^\\S\\n]*", "", ln)',
            )
        ],
        "multilevel_blockquote_fence or strip_code_blocks_unit_contract or list_item_fence",
    ),
    (
        "survivor-8 S4 允许式表增「备注：…派生」自由式（F-4: 无依据可写的模式混入）",
        [
            (
                '        "skill:③段固定句式",\n    ),\n)',
                '        "skill:③段固定句式",\n    ),\n'
                '    (re.compile(r"^\\s*备注[：:].*派生.*$"), "skill:③段固定句式"),\n)',
            )
        ],
        "freeform_derivation_note or derive_allow_entries_are_grounded",
    ),
    (
        "survivor-9 (e) 注记槽退化为自由文本（H-3「先开放再排除」黑名单老路复活）",
        [
            (
                "            note_slot = (\n"
                '                rf"(?:\\s*[·，,、]?\\s*"\n'
                "                rf\"(?:{'|'.join(re.escape(x) for x in _SIGNAL_TAIL_NOTES)}))?\"\n"
                "            )",
                '            note_slot = r"(?:[^【】]*)"',
            )
        ],
        "signal_tail_note_outside_table",
    ),
    (
        "survivor-10 (e) `_SIGNAL_TAIL_NOTES` 增「另有仨条」（封闭表被单侧扩表）",
        [
            (
                '_SIGNAL_TAIL_NOTES = ("口径一致",)',
                '_SIGNAL_TAIL_NOTES = ("口径一致", "另有仨条")',
            )
        ],
        "skill_sync_signal_tail_notes_table",
    ),
    # ── CARD-维护B-R3 (e): C「中文数词终态」的两条承重变体 ──
    # round-5 HIGH 的两个可失效面各配一条: ①判据本身退回多位文法解析器;
    # ②提取面收窄导致多字串根本不进检查面 (漏拦冒充 fail-closed)。
    # D2 叙述段与 fallback 允许式**共用同一判据/同一提取常量**, 故每条变体
    # 改一处即禁掉该性质的**全部**防线 (脚本铁律 2)。
    (
        "survivor-11 (C) 判据退回多位解析器（round-5 HIGH 全线：两侧共用判据，一处即全禁）",
        [
            (
                "    return _CJK_NUM.get(s) if len(s) == 1 else None",
                "    total, section, digit, seen = 0, 0, None, False\n"
                "    for ch in s:\n"
                "        if ch in _CJK_NUM:\n"
                "            digit = _CJK_NUM[ch]\n"
                "            seen = True\n"
                "        elif ch in _CJK_UNIT:\n"
                "            unit = _CJK_UNIT[ch]\n"
                "            if unit >= 10000:\n"
                "                section = (section + (digit or 0)) if (section or digit) else 1\n"
                "                total += section * unit\n"
                "                section, digit = 0, None\n"
                "            else:\n"
                "                section += (digit if digit is not None else 1) * unit\n"
                "                digit = None\n"
                "            seen = True\n"
                "        else:\n"
                "            return None\n"
                "    if not seen:\n"
                "        return None\n"
                "    return total + section + (digit or 0)",
            )
        ],
        "r5_cjk or r5_derive or r5_prose or r4_derive_allow_cjk",
    ),
    (
        "survivor-12 (C) 提取面收窄成单字（「抓得到才拒得掉」全线：唯一提取模式被禁）",
        [
            (
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}](?:{_D2_JOIN_ONE}*+[{_NUMERAL_LIKE_CHARS}])*"',
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}]"',
            )
        ],
        "r5_cjk or r5_derive or r5_prose or r5_noise or r4_derive_allow_cjk",
    ),
    # ── R3 round-2 (车道对抗审查 1B+4H): 连接语义的承重变体 ──
    (
        "survivor-13 (C-2) 数串不再跨连接字符（CJK 与 ASCII 两侧提取面一起禁）",
        [
            (
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}](?:{_D2_JOIN_ONE}*+[{_NUMERAL_LIKE_CHARS}])*"',
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}]+"',
            ),
        ],
        "r5_noise_split",
    ),
    (
        "survivor-14 (C-2) 剥噪声还原被禁（_join_free 变恒等：token 带着噪声去判/查池）",
        [('    return _D2_JOIN_RE.sub("", s)', "    return s")],
        "r5_noise_split or r5_prose_single_char or r5_cjk",
    ),
    # ── R3 round-3 (Codex round-2 四条 HIGH): 统一取数规则的三条承重变体 ──
    (
        "survivor-15 (C-3) 判值放宽为「取末位字」（表内单字判据被禁：廿五/一零 被赋值）",
        [
            (
                "    return _cjk_single_to_int(token)",
                "    return _CJK_NUM.get(token[-1])",
            )
        ],
        "r6_cross_class or r5_prose or r5_derive",
    ),
    (
        "survivor-16 (C-3) 定界集退回窄集合（表外数词字不进提取面 ⇒ 从尾片重锚）",
        [
            (
                'sorted(set(_CJK_NUM_CHARS) | set(_CJK_NUM_EXTRA) | set("0123456789"))',
                'sorted(set(_CJK_NUM_CHARS) | set("0123456789"))',
            )
        ],
        "r6_cross_class",
    ),
    (
        "survivor-17 (C-3) CJK 小数形态检查被摘除（五点五个 / 5点5个 拆成两个 5 碰池）",
        [
            (
                "            for m_dec in _CJK_DECIMAL_RE.finditer(line):",
                "            for m_dec in ():",
            )
        ],
        "r6_cross_class",
    ),
    # ── R3 round-4 (Codex round-3 三条 HIGH): 区间端点与 fallback 前处理 ──
    (
        "survivor-18 (C-4) 区间某端无出处时退回「保留原串交给后面逐个判」"
        "（而后面的循环只取紧邻量词的一端 ⇒ 另一端免检）",
        [
            (
                "                bad_ends.extend(e for e in ends if e not in pool)\n"
                '                return " " * len(mm.group(0))',
                "                return (\n"
                '                    " " * len(mm.group(0))\n'
                "                    if all(e in pool for e in ends)\n"
                "                    else mm.group(0)\n"
                "                )",
            )
        ],
        "r7_range",
    ),
    (
        "survivor-19 (C-4) fallback 的千分位归一与小数防线被摘除（退回对原行直接 findall 逐片入池）",
        [
            (
                "            norm = _normalize_number_seps(ln.translate(_FULLWIDTH_DIGITS))\n"
                "            for m_dec in _DECIMAL_ANY_RE.finditer(norm):",
                "            norm = ln.translate(_FULLWIDTH_DIGITS)\n            for m_dec in ():",
            )
        ],
        "r7_range",
    ),
    (
        "survivor-20 (C-4) 小数分隔符两侧不再容连接字符 + 只认半角逗号（标签包住小数点 / 全角逗号千分位重新免检）",
        [
            (
                '_DECIMAL_SEP = rf"{_D2_JOIN_ONE}*[.．点]{_D2_JOIN_ONE}*"',
                '_DECIMAL_SEP = r"[.点]"',
            ),
            (
                'return re.sub(r"(?<=[0-9])[,，](?=[0-9]{3}(?![0-9]))", "", line)',
                'return re.sub(r"(?<=[0-9]),(?=[0-9]{3}(?![0-9]))", "", line)',
            ),
        ],
        "r7_range",
    ),
]


def run_suite(keyword: str) -> tuple[int, str, int, int]:
    """跑目标用例，返回 (rc, 输出尾部, 收集到的用例数, 失败数)。

    ⛔ Codex round-1 HIGH: 原实现只看 `rc != 0` 就判「如期变红」——
    pytest 的 rc=5 是**一个用例都没匹配到**（`-k` 写错就会这样），
    rc=2/3/4 是用法错误/内部错误。把它们当成"门变红了"正是
    MEMORY `reference_gate_design_pitfalls` 的头号形态：
    **把「没有发生」当成「验证通过」**。现在解析出真实的 passed/failed 计数，
    要求"确实收集到用例"且"确实有失败"才算变红。
    """
    r = subprocess.run(
        [str(PYTEST), SUITE, "-q", "-p", "no:cacheprovider", "-k", keyword],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=600,
    )
    out = r.stdout
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    return r.returncode, out[-400:], passed + failed, failed


def main() -> int:
    try:
        LOCK.mkdir()  # 原子互斥: 已存在即抛
    except FileExistsError:
        print(f"⛔ 另一个负验证进程正在跑（锁: {LOCK}）。变异脚本必须串行——见脚本 docstring。")
        return 2
    try:
        original = TARGET.read_bytes()
        backup_sha = hashlib.sha256(original).hexdigest()

        rc0, out0, n0, f0 = run_suite("domain_")
        if rc0 != 0 or f0 or n0 == 0:
            print(f"⛔ 基线不可信（rc={rc0} 收集={n0} 失败={f0}）:\n{out0}")
            return 2
        print(f"基线: 双向门全绿 · 被测文件 sha256={backup_sha[:12]}…\n")

        failures = 0
        for name, subs, keyword in MUTANTS:
            text = original.decode("utf-8")
            for old, new in subs:
                if old not in text:
                    print(f"❌ {name}: 变异点未命中（实现已变？）——按失败计")
                    failures += 1
                    text = None
                    break
                text = text.replace(old, new, 1)
            if text is None:
                continue
            TARGET.write_text(text, encoding="utf-8")
            try:
                rc, out, n, f = run_suite(keyword)
            finally:
                TARGET.write_bytes(original)  # 立刻还原，异常也还原
            got = hashlib.sha256(TARGET.read_bytes()).hexdigest()
            assert got == backup_sha, f"还原后字节与备份不同！{got[:12]} != {backup_sha[:12]}"
            # ⛔ 必须是"收集到用例 且 确实有失败"，不能只看 rc != 0
            if n == 0:
                print(f"❌ {name}: `-k {keyword}` 一个用例都没匹配到（rc={rc}）——这不是变红")
                failures += 1
            elif f == 0:
                print(f"❌ {name}: 变异后 {n} 个用例仍全绿 = 该门不承重\n{out}")
                failures += 1
            else:
                print(f"✅ {name}: 如期变红（{f}/{n} 失败）")

        print(f"\n{'全部承重' if not failures else f'{failures} 条未承重'}（共 {len(MUTANTS)} 条变体）")
        return 1 if failures else 0
    finally:
        LOCK.rmdir()


if __name__ == "__main__":
    sys.exit(main())
