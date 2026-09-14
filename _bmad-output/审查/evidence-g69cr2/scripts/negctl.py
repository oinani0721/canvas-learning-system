# CARD-G6-9c-R2 负控 runner：每段只拆一层防线，EXIT trap 无条件还原，
# 全文件 shasum -a 256 跑前/跑后逐字相同。禁 git stash / git checkout。
import atexit, hashlib, subprocess, sys
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review")
LOCAL = ROOT / "scripts/local_tz.py"
DISP = ROOT / "backend/app/core/display_tz.py"
RO = ROOT / "backend/app/api/v1/endpoints/review_overview.py"
TARGETS = [LOCAL, DISP, RO]
PYTEST = ROOT / "backend/.venv/bin/pytest"
F = "tests/regression/test_g6_9c_single_tz_source.py"

ORIGINAL = {t: t.read_bytes() for t in TARGETS}

def sha(t): return hashlib.sha256(t.read_bytes()).hexdigest()
SHA_BEFORE = {t: sha(t) for t in TARGETS}

def restore():
    for t, b in ORIGINAL.items():
        if t.read_bytes() != b:
            t.write_bytes(b)
atexit.register(restore)

# ---- 变异定义：(旧文本, 新文本, 作用文件列表) ----
MUT_HIGH1 = ("for year in (y - 2, y - 1, y, y + 1):  # 规则可滚出名义年, 季度起始年最早到 y-2",
             "for year in (y - 1, y, y + 1):  # NEGCTL-MUTATED",
             [LOCAL, DISP])
MUT_HIGHNEW_BLOCK_OLD = '''        start = _parse_rule("M3.2.0", None)'''
MUT_HIGHNEW = (MUT_HIGHNEW_BLOCK_OLD,
               '''        return None  # NEGCTL-MUTATED\n        start = _parse_rule("M3.2.0", None)''',
               [LOCAL, DISP])
MUT_ENDRULE = ('end = ("M", 11, 1, 0, 3600 + dst_off - std_off)',
               'end = _parse_rule("M11.1.0", None)  # NEGCTL-MUTATED',
               [LOCAL, DISP])
YDAY_OLD = 'yday = a + (1 if (kind == "J" and calendar.isleap(year) and a >= 60) else 0) - (1 if kind == "J" else 0)'
MUT_LEAP_J60_ONLY = (YDAY_OLD,
                     YDAY_OLD.replace("a >= 60", "a >= 300") + "  # NEGCTL-MUTATED",
                     [LOCAL, DISP])
MUT_LEAP_J365_ONLY = (YDAY_OLD,
                      YDAY_OLD.replace("a >= 60", "60 <= a < 300") + "  # NEGCTL-MUTATED",
                      [LOCAL, DISP])
MUT_HIGH2 = ('        raise ValueError(\n            f"display_tz 缺席或为 null — 无可信参照时区规则, 旧投影的归桶无法重算 "\n            f"(generated_at={generated_at} 自带的固定偏移只在那一刻等于生产者的真实偏移)"\n        )\n',
             '        ref_tz = ref.tzinfo  # NEGCTL-MUTATED: 还原成固定偏移回退\n',
             [RO])
# ⑧ 还原省略规则分支的偏移收紧
MUT_OFFGUARD = ("        if abs(std_off) >= 86400 or abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:\n            return None",
                "        if False:  # NEGCTL-MUTATED\n            return None",
                [LOCAL, DISP])
# ⑨ 只还原 dst 侧的越界检查（Codex r2 MEDIUM-2 点名的单侧退化面）
MUT_OFFGUARD_DST_ONLY = ("        if abs(std_off) >= 86400 or abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:",
                         "        if abs(std_off) >= 86400 or abs(dst_off - std_off) >= 86400:  # NEGCTL-MUTATED",
                         [LOCAL, DISP])
MUT_OFFGUARD_STD_ONLY = ("        if abs(std_off) >= 86400 or abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:",
                         "        if abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:  # NEGCTL-MUTATED",
                         [LOCAL, DISP])
# ⑩ 只还原「标准偏移必填」
MUT_STDOFF_REQUIRED = ('        if not g["std_off"]:\n            return None',
                       '        if False:  # NEGCTL-MUTATED\n            return None',
                       [LOCAL, DISP])

def apply(muts):
    for old, new, files in muts:
        for f in files:
            s = f.read_text(encoding="utf-8")
            n = s.count(old)
            assert n == 1, f"变异锚点在 {f.name} 命中 {n} 次（应为 1）: {old[:50]!r}"
            f.write_text(s.replace(old, new, 1), encoding="utf-8")

def run(nodeids):
    r = subprocess.run([str(PYTEST), "-q", "-p", "no:cacheprovider", "--no-header", "--tb=long", *nodeids],
                       cwd=ROOT / "backend", capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(Path.home())})
    return r.returncode, r.stdout + r.stderr

# ⑫⑬⑭⑮ Codex r3 整改面的负控
MUT_NEWLINE = ('        if "\\n" in spec or "\\r" in spec or "\\x00" in spec:', '        if "\\x00" in spec:  # NEGCTL-MUTATED', [LOCAL, DISP])
MUT_LENGTH = ('        if len(spec.encode("utf-8", "surrogateescape")) > 255:', '        if False:  # NEGCTL-MUTATED', [LOCAL, DISP])
MUT_YEARGUARD = ("            if not 1 <= year <= 9999:", "            if False:  # NEGCTL-MUTATED", [LOCAL, DISP])
MUT_ABS_DIFF = ("or abs(dst_off - std_off) >= 86400:", "or (dst_off - std_off) >= 86400:  # NEGCTL-MUTATED", [LOCAL, DISP])
# ⑯⑰ Codex r4 整改面的负控
MUT_BYTELEN = ('        if len(spec.encode("utf-8", "surrogateescape")) > 255:', '        if len(spec) > 255:  # NEGCTL-MUTATED', [LOCAL, DISP])
MUT_YEAR_UPPER = ("            if not 1 <= year <= 9999:", "            if not 1 <= year <= 9998:  # NEGCTL-MUTATED", [LOCAL, DISP])
# ⑱⑲⑳ Codex r5 整改面的负控
MUT_SURROGATE = ('        if len(spec.encode("utf-8", "surrogateescape")) > 255:', '        if len(spec.encode("utf-8")) > 255:  # NEGCTL-MUTATED', [LOCAL, DISP])
MUT_NUL = ('        if "\\n" in spec or "\\r" in spec or "\\x00" in spec:', '        if "\\n" in spec or "\\r" in spec:  # NEGCTL-MUTATED', [LOCAL, DISP])
MUT_SOUTH_UPPER = ("            elif year < 9999:", "            else:  # NEGCTL-MUTATED", [LOCAL, DISP])
SEGMENTS = [
    ("① 还原 HIGH-1 候选窗(y-2 → y-1)", [MUT_HIGH1],
     [f"{F}::test_dst_window_candidates_cover_rules_that_roll_into_the_following_year"],
     "候选窗漏格"),
    ("② 还原 HIGH-new(补默认规则 → return None)", [MUT_HIGHNEW],
     [f"{F}::test_omitted_transition_rules_use_the_libc_default_instead_of_falling_back_to_utc"],
     "dst 有名省略规则被退 UTC"),
    ("③ 还原 HIGH-2 双向堵(敏感性复算短路)", [MUT_HIGH2],
     [f"{F}::test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent"],
     "display_tz 缺席或为 null"),
    ("④ 还原 (c)+(d) 后跑门⑦(新增非 2026 样本须至少一条红)", [MUT_HIGH1, MUT_HIGHNEW],
     [f"{F}::test_posix_tz_string_resolves_to_process_local_not_etc_localtime"],
     "墙钟与 C 库不一致"),
    ("⑤ 还原 end 切换时刻(现算 → 写死当地 02:00)", [MUT_ENDRULE],
     [f"{F}::test_omitted_rule_transition_points_track_the_standard_side_offset"],
     "省略规则的切换点与 C 库不符"),
    ("⑥ 闰日条件 a>=60 → a>=300(只坏 J60): 门⑦ 的 2024-02-29 格必红、2024-12-31 格必绿",
     [MUT_LEAP_J60_ONLY],
     [f"{F}::test_posix_tz_string_resolves_to_process_local_not_etc_localtime"],
     "2024-02-29"),
    ("⑦ 闰日条件 a>=60 → 60<=a<300(只坏 J365): 门⑦ 的 2024-12-31 格必红、2024-02-29 格必绿",
     [MUT_LEAP_J365_ONLY],
     [f"{F}::test_posix_tz_string_resolves_to_process_local_not_etc_localtime"],
     "2024-12-31"),
    ("⑧ 还原省略规则分支的偏移收紧(|偏移| ≥24h 放行): 非法偏移串被错误接受",
     [MUT_OFFGUARD],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
     "省略规则分支扩大了错误接受面"),
    ("⑨ 只还原 dst 侧越界检查(单侧退化): AAA23BBB24 被错误接受",
     [MUT_OFFGUARD_DST_ONLY],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
     "AAA23BBB24"),
    ("⑪ 只还原 std 侧越界检查(对称的单侧退化): AAA24BBB23 被错误接受",
     [MUT_OFFGUARD_STD_ONLY],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
     "AAA24BBB23"),
    ("⑩ 只还原「标准偏移必填」: <AAA><BBB> 被错误接受",
     [MUT_STDOFF_REQUIRED],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
     "<AAA><BBB>"),
    ("⑫ 还原末尾换行检查: AAA0<BBB>\\n 被错误接受", [MUT_NEWLINE],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"], "AAA0<BBB>"),
    ("⑬ 还原整串长度检查: 508 字符串被错误接受", [MUT_LENGTH],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"], "AAAAAAAAAAAAAAAAAAAA"),
    ("⑭ 还原候选年越界跳过: 公元 2 年换算抛 ValueError", [MUT_YEARGUARD],
     [f"{F}::test_candidate_year_guard_keeps_extreme_epochs_from_raising"], "候选年守卫失效"),
    ("⑮ abs(差值) → 裸差值(负向退化): AAA-12BBB12 被错误接受", [MUT_ABS_DIFF],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"], "AAA-12BBB12"),
    ("⑯ 长度按字符而非 UTF-8 字节: 176 字符/516 字节的引用名被错误接受", [MUT_BYTELEN],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"], "516 字节"),
    ("⑰ 候选年上界收到 9998: 9999 年的北半球季度被整个跳过", [MUT_YEAR_UPPER],
     [f"{F}::test_candidate_year_guard_keeps_extreme_epochs_from_raising"], "候选年上界收得过紧"),
    ("⑱ surrogateescape → 严格 encode: 非法字节 TZ 让 display_tz() 抛(启动失败面)", [MUT_SURROGATE],
     [f"{F}::test_display_tz_survives_non_utf8_tz_bytes"], "display_tz() 在 TZ="),
    ("⑲ 去掉 NUL 检查: 引用名内含 NUL 的自报值被错误接受", [MUT_NUL],
     [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"], "含 NUL"),
    ("⑳ 南半球上界 elif year<9999 → else: 9999 年南支算到 10000 抛", [MUT_SOUTH_UPPER],
     [f"{F}::test_candidate_year_guard_keeps_extreme_epochs_from_raising"], "南半球分支的候选年上界失效"),
]

# ⛔ 预检：每个段用到的变异锚点必须在**开跑前**就全部命中。
#    本卡踩过两次「锚点随生产代码演进失效」—— 脚本跑到第 13/14 段才 AssertionError 中止，
#    前面的段看着全绿，末尾的「全部 N 段 RED」根本没打印出来。
_seen = set()
for _label, _muts, _ids, _msg in SEGMENTS:
    for _old, _new, _files in _muts:
        for _f in _files:
            _n = _f.read_text(encoding="utf-8").count(_old)
            assert _n == 1, f"⛔ 预检失败: 段「{_label}」的锚点在 {_f.name} 命中 {_n} 次（应为 1）: {_old[:60]!r}"
            _seen.add((_f.name, _old))
print(f"预检通过: {len(SEGMENTS)} 段 / {len(_seen)} 个(文件, 锚点)对全部唯一命中")
print()

print("=== shasum -a 256 跑前 ===")
for t in TARGETS: print(f"  {SHA_BEFORE[t]}  {t.relative_to(ROOT)}")
print()

all_ok = True
for label, muts, nodeids, must_contain in SEGMENTS:
    apply(muts)
    rc, out = run(nodeids)
    restore()
    tail = [ln for ln in out.splitlines() if "passed" in ln or "failed" in ln or "error" in ln.lower()]
    hit = must_contain in out
    ok = rc != 0 and hit
    all_ok &= ok
    print(f"{label}")
    print(f"   rc={rc}  汇总: {tail[-1] if tail else '(无)'}")
    print(f"   失败正文含 {must_contain!r}: {hit}")
    print(f"   判定: {'RED ✅（负控成立）' if ok else 'NOT-RED ❌（负控失败）'}")
    if "门⑦" in label:
        import re as _re
        y2024 = [ln for ln in out.splitlines() if ln.startswith("FAILED") and "2024-01-01" in ln or ("2024" in ln and "instant" in ln)]
        red_ids = [ln for ln in out.splitlines() if ln.startswith("FAILED")]
        print("   门⑦ 红格 nodeid:")
        for ln in red_ids: print("      " + ln[:150])
        print(f"   红在新增非 2026 样本上的断言正文出现 2024: {chr(39)}2024{chr(39) } in out = " + str("2024" in out))
    if label.startswith("⑥") or label.startswith("⑦"):
        other = "2024-12-31" if must_contain == "2024-02-29" else "2024-02-29"
        has_this, has_other = must_contain in out, other in out
        print(f"   互斥判定: 正文含 {must_contain}={has_this}（须 True）, 含 {other}={has_other}（须 False）")
        seg_ok = has_this and not has_other
        all_ok &= seg_ok
        print(f"   区分性: {'成立 ✅' if seg_ok else '不成立 ❌'}")
        for ln in out.splitlines():
            if ln.startswith("FAILED"): print("      " + ln[:140])
    # 还原后立刻确认字节一致
    bad = [t.name for t in TARGETS if sha(t) != SHA_BEFORE[t]]
    print(f"   还原后 sha 与跑前一致: {not bad}" + (f"  不一致: {bad}" if bad else ""))
    print()

print("=== shasum -a 256 跑后 ===")
for t in TARGETS: print(f"  {sha(t)}  {t.relative_to(ROOT)}")
print()
print("逐字相同:", all(sha(t) == SHA_BEFORE[t] for t in TARGETS))
print(f"全部 {len(SEGMENTS)} 段 RED:", all_ok)
sys.exit(0 if all_ok and all(sha(t) == SHA_BEFORE[t] for t in TARGETS) else 1)
