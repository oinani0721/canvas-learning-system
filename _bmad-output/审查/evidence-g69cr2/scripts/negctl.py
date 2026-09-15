"""CARD-G6-9c-R2 负控 runner（r10 重建：按 parse_posix_tz 的 9 段校验层重新映射）。

判据口径:
  * 每段只跑它**声称守住**的那几个 nodeid, 并要求它们 FAILED —— 不是「某处有失败」。
  * 期望 RED 的段拿不到红 = 该段无人守（假绿）; 期望 GREEN 的两段是**如实登记**的
    性质证明（一条死分支、一条无 pytest 守卫的性能防线）, 它们变红反而说明我判错了。
  * 开跑前预检: 每个锚点必须在每个目标文件恰好命中 1 次, 否则整脚本 abort ——
    不允许「前几段印了 RED ✅、中途因锚点漂移而崩」。
  * 跑前/跑后对三个目标文件做 sha256 全文件比对。
"""
import atexit, hashlib, subprocess, sys
from pathlib import Path

ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review")
LOCAL = ROOT / "scripts/local_tz.py"
DISP = ROOT / "backend/app/core/display_tz.py"
RO = ROOT / "backend/app/api/v1/endpoints/review_overview.py"
TARGETS = [LOCAL, DISP, RO]
PYTEST = ROOT / "backend/.venv/bin/pytest"
F = "tests/regression/test_g6_9c_single_tz_source.py"
TZ = [LOCAL, DISP]

ORIGINAL = {t: t.read_bytes() for t in TARGETS}
SHA0 = {t: hashlib.sha256(b).hexdigest() for t, b in ORIGINAL.items()}

def restore():
    for t, b in ORIGINAL.items():
        if t.read_bytes() != b:
            t.write_bytes(b)
atexit.register(restore)

def M(old, new, files=None):
    return (old, new, files or TZ)

# ── 变异表（old 必须是文件中恰好出现一次的**整行**或整块）───────────────────
MUTS = {
 "CAND":    M('        for year in (y - 2, y - 1, y, y + 1):',
              '        for year in (y - 1, y, y + 1):  # NEGCTL'),
 "YGUARD":  M('            if not 1 <= year <= 9999:',
              '            if False:  # NEGCTL'),
 "S9999":   M('                if year >= 9999:',
              '                if False:  # NEGCTL'),
 "ENDRULE": M('        end = ("M", 11, 1, 0, 3600 + dst_off - std_off)',
              '        end = _parse_rule("M11.1.0", None)  # NEGCTL'),
 "STARTR":  M('        start = _parse_rule("M3.2.0", None)',
              '        start = None  # NEGCTL'),
 "CTRL":    M('    if spec != spec.rstrip("\\n\\r"):', '    if False:  # NEGCTL'),
 "ENC":     M('        spec.encode("utf-8")',
              '        _ = spec.encode("utf-8", "surrogateescape")  # NEGCTL'),
 "ASCII":   M('        if not all(x.isascii() and x.isdigit() for x in _f):',
              '        if False:  # NEGCTL'),
 "HMAX":    M('        if _hmax is not None and int(_f[0]) > _hmax:',
              '        if False:  # NEGCTL'),
 "MIN60":   M('        if len(_f) > 1 and int(_f[1]) > 59:', '        if False:  # NEGCTL'),
 "SEC60":   M('        if len(_f) > 2 and int(_f[2]) > 60:', '        if False:  # NEGCTL'),
 "RULEA":   M('        if _txt is not None and not _txt.lstrip("JM").replace(".", "").isascii():',
              '        if False:  # NEGCTL'),
 "STDREQ":  M('    if not g["std_off"]:', '    if False:  # NEGCTL'),
 # 和式口径退回 r10 的「每名 <=507」单名上限
 "NAMESUM": M('''    _name_bytes = sum(
        len(_strip_name(_nm).encode("utf-8")) + 1
        for _nm in (g["std"], g["dst"])
        if _nm is not None and _strip_name(_nm)
    )
    if _name_bytes > 512:
        return None
''',
 '''    if g["dst"] is not None:  # NEGCTL 退回单名 <=507 口径
        for _nm in (g["std"], g["dst"]):
            if len(_strip_name(_nm).encode("utf-8")) > 507:
                return None
'''),
 # 量纲: 字节 -> 字符（和式表达式里只有一处 encode，改它即可覆盖 std/dst 两侧）
 "NAMECHAR": M('        len(_strip_name(_nm).encode("utf-8")) + 1',
               '        len(_strip_name(_nm)) + 1  # NEGCTL 字节->字符'),
 # 空名也加一个 NUL（Codex r10 指出的空 dst 名侧）
 "EMPTYNAME": M('        if _nm is not None and _strip_name(_nm)',
                '        if _nm is not None  # NEGCTL 空名也算一个 NUL'),
 # H1: 只判 dst 名缺席就早退 —— 漏掉「无 dst 名但带合法规则」那一支
 "H1EARLY": M('    if g["dst"] is None and g["start"] is None:',
              '    if g["dst"] is None:  # NEGCTL'),
 # 正则数字位宽退回 {1,3}/{1,2}
 "REWIDTH": M('    r"(?P<std_off>[+-]?\\d+(?::\\d+(?::\\d+)?)?)?"',
              '    r"(?P<std_off>[+-]?\\d{1,3}(?::\\d{1,2}(?::\\d{1,2})?)?)?"  # NEGCTL'),
 # 裸名词法退回 [A-Za-z]{3,}
 "BARENAME": M('    r"^(?P<std><[^<>]*>|[^\\x00-\\x1f\\d+,\\-]+)"',
               '    r"^(?P<std><[^<>]+>|[A-Za-z]{3,})"  # NEGCTL'),
 # M4: 冒号从「只剥一个」退回 lstrip（剥全部）
 "COLON": M('    raw = env_tz[1:] if env_tz.startswith(":") else env_tz  # C 库只剥一个冒号',
            '    raw = env_tz.lstrip(":")  # NEGCTL 剥全部冒号'),
 # M5: 去掉 zoneinfo 路径候选
 "ZIPATH": M('            cands.append("/".join(parts[parts.index("zoneinfo") + 1 :]))',
             '            pass  # NEGCTL 不再从绝对路径提取 IANA 名'),
 # L7: 去掉 fromutc 的 tzinfo 身份校验
 "FROMUTC": M('''        if dt.tzinfo is not self:
            raise ValueError("fromutc: dt.tzinfo is not self")
''', ''),
 "STDMAG":  M('    if abs(std_off) >= 86400:', '    if False:  # NEGCTL'),
 "RULEOK":  M('    if (g["start"] is not None and _start_rule is None) or (g["end"] is not None and _end_rule is None):',
              '    if False:  # NEGCTL'),
 "DSTMAG":  M('    if abs(dst_off) >= 86400 or abs(dst_off - std_off) >= 86400:',
              '    if False:  # NEGCTL'),
 "TZNAME":  M('        return self._dst_name if self._in_dst(wall - off) else self._std_name',
              '        return self._dst_name if off == self._dst_off else self._std_name  # NEGCTL'),
 # J60/J365 是**区分性**变异对: 前者只坏 J60(杀 02-29 那格), 后者只坏 J365(杀 12-31 那格)。
 # 两段都要在, 否则会误以为两个闰年探针互为冗余、留一个就够。
 "J60":     M('    yday = a + (1 if (kind == "J" and calendar.isleap(year) and a >= 60) else 0) - (1 if kind == "J" else 0)',
              '    yday = a + (1 if (kind == "J" and calendar.isleap(year) and a >= 300) else 0) - (1 if kind == "J" else 0)  # NEGCTL'),
 "J365":    M('    yday = a + (1 if (kind == "J" and calendar.isleap(year) and a >= 60) else 0) - (1 if kind == "J" else 0)',
              '    yday = a + (1 if (kind == "J" and calendar.isleap(year) and 60 <= a < 300) else 0) - (1 if kind == "J" else 0)  # NEGCTL'),
 "NUL":     M('    if "\\x00" in spec:', '    if False:  # NEGCTL'),
 "CAP":     M('    if len(spec) > 1024:', '    if False:  # NEGCTL'),
 "REWIDTH_ONE": M('    r"(?P<std_off>[+-]?\\d+(?::\\d+(?::\\d+)?)?)?"',
                  '    r"(?P<std_off>[+-]?\\d{1,3}(?::\\d{1,2}(?::\\d{1,2})?)?)?"  # NEGCTL',
                  [LOCAL]),
 "HIGH2":   M('''        raise ValueError(
            f"display_tz 缺席或为 null — 无可信参照时区规则, 旧投影的归桶无法重算 "
            f"(generated_at={generated_at} 自带的固定偏移只在那一刻等于生产者的真实偏移)"
        )
''', '        ref_tz = ref.tzinfo  # NEGCTL 退回静默用固定偏移\n', [RO]),
}

A = "test_accepted_domain_matches_libc"
def acc(*idx):
    return [f"{F}::{A}[{'accept' if s.startswith('a') else 'reject'}-{n}-{c}]"
            for s, n in idx for c in ("backend", "scripts")]

# ── 段表: (段名, [变异键], [必须变红的 nodeid], 该段守什么) ─────────────────
SEGMENTS = [
 ("候选年下界", ["CAND"], [f"{F}::test_dst_window_candidates_cover_rules_that_roll_into_the_following_year"],
  "HIGH-1: 季度起始年最早到 y-2, 写成 y-1 会漏掉跨年窗口"),
 ("候选年守卫", ["YGUARD"], [f"{F}::test_candidate_year_guard_keeps_extreme_epochs_from_raising"],
  "极端纪元下 _dst_window(0)/(10000) 会抛"),
 ("9999南半球", ["S9999"], [f"{F}::test_southern_season_in_year_9999_is_not_dropped"],
  "r9 L1: 南支上界写成 elif year < 9999 会整段丢掉 9999 年季度"),
 ("省略规则-结束时刻", ["ENDRULE"],
  [f"{F}::test_omitted_rule_transition_points_track_the_standard_side_offset",
   f"{F}::test_default_transition_time_matches_libc_minute_by_minute"],
  "HIGH-new: end 必须按 3600+dst_off-std_off 现算, 写死 02:00 只在 Δ=+1h 那族对"),
 ("省略规则-起始规则", ["STARTR"],
  [f"{F}::test_omitted_transition_rules_use_the_libc_default_instead_of_falling_back_to_utc"],
  "HIGH-2: dst 有名而规则省略时必须补 posixrules, 不能静默退 UTC"),
 ("尾部换行", ["CTRL"], acc(("r", 9)), "正则 $ 放过尾部换行, 需显式拒"),
 ("严格UTF-8", ["ENC"],
  [f"{F}::test_display_tz_survives_non_utf8_tz_bytes",
   f"{F}::test_non_utf8_key_never_reaches_response_on_any_branch"],
  "r5→r6: surrogateescape 只把失败从启动挪到响应出口"),
 ("ASCII数字", ["ASCII"], acc(("r", 17)), "Python \\d 连全角一起匹配, C 库拒"),
 ("切换时刻小时", ["HMAX"], acc(("r", 15)), "167 接受 / 168 拒"),
 ("切换时刻分钟", ["MIN60"], acc(("r", 13)), "分钟 >59 拒"),
 ("切换时刻秒", ["SEC60"], acc(("r", 14)), "秒 60 接受 / 61 拒"),
 ("规则ASCII", ["RULEA"], acc(("r", 16)), "规则文本里的全角数字"),
 ("std偏移必填", ["STDREQ"], acc(("r", 10), ("r", 11)), "r9 M3: 所有形态都必填"),
 ("名字和式512", ["NAMESUM"], acc(("r", 20), ("r", 21)),
  "退回单名 ≤507 口径 ⇒ 无 dst 形态不查(误收) + 两名各 507 和 1016(误收)"),
 ("名字量纲字节", ["NAMECHAR"], acc(("r", 18)), "中×170 = 510 字节 / 170 字符, 按字符算会误收"),
 # ── 以下 8 段为 r11 新增（Codex r10 的 H1 / M1 / M2 / M4 / M5 / M9 / L7）──
 ("空名占NUL", ["EMPTYNAME"], acc(("a", 31)),
  "空 dst 名不占缓冲区: `<A×511>-1<>,…` 和 = 512 收; 给空名也加 NUL 会误拒"),
 # ⛔ 这段曾绑接受域表的 accept-22/23 而**假绿**: 变异后那两个串**仍被接受**,
 #    只是算错一小时 —— 接受域门只判收/拒, 对「收了但算错」全盲。改绑组合门的
 #    **第二阶段**（换算对拍）, 并用文本锚钉住它红在换算而不是接受域。
 ("H1无dst名带规则", ["H1EARLY"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r10 H1: 无 dst 名但带合法规则时 C 库照常实行 DST, 早退会误算一小时", "换算对拍失败"),
 ("正则数字位宽", ["REWIDTH"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r10 M2: C 库数字字段无位数上限, `{1,3}` 会把前导零串整片误拒", "误拒·未声明"),
 ("裸名词法", ["BARENAME"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r10 M1: 裸名吃到数字为止, `[A-Za-z]{3,}` 会把 `A1` / `ABC<DEF>2` 误拒", "误拒·未声明"),
 ("TZ多重冒号", ["COLON"],
  [f"{F}::test_tz_path_forms_match_libc"],
  "r10 M4: C 库只剥一个冒号, lstrip 会把 `::Asia/Shanghai` 误认成上海(差 8 小时)"),
 ("TZ绝对路径", ["ZIPATH"],
  [f"{F}::test_tz_path_forms_match_libc"],
  "r10 M5: `/usr/share/zoneinfo/...` C 库能解析, 去掉候选会退 UTC"),
 ("fromutc身份校验", ["FROMUTC"],
  [f"{F}::test_fromutc_rejects_foreign_tzinfo"],
  "r10 L7: 缺校验会把 naive / 异 tzinfo 静默当成本时区的 UTC 读数换算"),
 ("模块级常量同源", ["REWIDTH_ONE"],
  [f"{F}::test_two_copies_share_identical_module_level_constants"],
  "r10 M9: 只改一份副本的正则, 除这道门外**全套都绿**（Codex 实测 199 个参数格全过）"),
 ("std偏移量级", ["STDMAG"],
  [f"{F}::test_offset_domain_is_checked_on_every_branch_not_only_omitted_rules"],
  "|std_off| < 24h 的 Python 可表示性收紧"),
 ("规则可解析", ["RULEOK"], acc(("r", 12)), "r9 M4: 无 dst 形态也要验规则"),
 ("dst偏移量级", ["DSTMAG"],
  [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
  "省略规则分支不得放宽偏移域"),
 ("tzname口径", ["TZNAME"], [f"{F}::test_tzname_uses_dst_membership_not_offset_equality"],
  "r9 L2: 偏移相等不等于处在 DST 里"),
 # ⛔ 这两段曾绑错门: 绑到「范围」那个测试(它根本不测闰日)于是假绿。真正守它们的是
 #    gate ⑦ 的组合扫描, 且**只有 2024 那两个闰年探针**能显形 —— 2026 年两个 J 值都不翻。
 ("J规则闰日-J60", ["J60"], [f"{F}::test_posix_tz_string_resolves_to_process_local_not_etc_localtime"],
  "J60 在闰年从 3/1 提前到 2/29: 只杀 2024-02-29 那格", "AAA5BBB,J60/2,J300/2"),
 ("J规则闰日-J365", ["J365"], [f"{F}::test_posix_tz_string_resolves_to_process_local_not_etc_localtime"],
  "J365 在闰年终点提前一天: 只杀 2024-12-31 那格", "WART4WARST,J1/0,J365/25"),
 # ⛔ 这段原先被我放进「期望 GREEN」并声称 NUL 检查是死分支 —— 错的。样本只取了
 #    「NUL 在引用名外」那一个值; 引用名**内部**的 NUL 由正则的 [^<>] 放行, 只有这条能拒。
 ("NUL引用名内", ["NUL"],
  [f"{F}::test_omitted_rule_branch_does_not_widen_the_accepted_offset_domain"],
  "NUL 在引用名内部是这条检查的唯一显形位置(正则的 [^<>] 放行 NUL)",
  "parse_posix_tz('AAA0<B" + chr(92) + "x00BB>')"),
 ("HIGH-3归桶", ["HIGH2"],
  [f"{F}::test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent"],
  "display_tz 缺席时不得静默用 generated_at 的固定偏移重算归桶"),
]
# 如实登记: 这两条**预期不变红**, 段本身就是它们性质的证明。
EXPECT_GREEN = [
 ("ReDoS上限", ["CAP"], [f"{F}::{A}"],
  "1024 是**性能**防线不是正确性防线: 去掉它接受域一字不变, 只是 4000 字符的坏串"
  "从 0.000s 退回 0.475s。它由计时判据守, 不由 pytest 守 —— 如实登记而非假装有守卫。"),
]

def apply_mut(keys):
    for k in keys:
        old, new, files = MUTS[k]
        for f in files:
            t = f.read_text(encoding="utf-8")
            assert t.count(old) == 1, f"{k} 锚点在 {f.name} 命中 {t.count(old)} 次"
            f.write_text(t.replace(old, new), encoding="utf-8")

def preflight():
    bad = []
    for k, (old, _new, files) in MUTS.items():
        for f in files:
            n = f.read_text(encoding="utf-8").count(old)
            if n != 1:
                bad.append(f"{k} @ {f.name}: 命中 {n} 次（应 1）")
    if bad:
        print("⛔ 预检失败, 拒绝开跑（锚点已随代码漂移）:")
        for b in bad: print("   " + b)
        sys.exit(2)
    print(f"✅ 预检通过: {len(MUTS)} 个锚点在各自目标文件均恰好命中 1 次\n")
    # 绑定自证：完整 HEAD + 被变异的三个生产文件 + **测试文件**的全量 sha256
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    print(f"HEAD = {head}")
    for t in TARGETS + [ROOT / "backend" / F]:
        print(f"  sha256 {hashlib.sha256(t.read_bytes()).hexdigest()}  {t.relative_to(ROOT)}")
    print()

def run(nodeids):
    r = subprocess.run([str(PYTEST), *nodeids, "-q", "--tb=long", "-p", "no:cacheprovider"],
                       cwd=ROOT / "backend", capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

def main():
    preflight()
    rows, fails = [], 0
    for want_red, table in ((True, SEGMENTS), (False, EXPECT_GREEN)):
        for row in table:
            name, keys, nodeids, why = row[:4]
            must = row[4] if len(row) > 4 else None
            apply_mut(keys)
            rc, out = run(nodeids)
            restore()
            if "ERROR" in out and "error" in out.lower().split("\n")[-2:][0]:
                pass
            not_found = "::" in out and "not found" in out
            got_red = rc != 0 and not not_found
            # 文本锚: 红必须红在**声称的那个串**上, 不接受「某处有失败」
            anchored = (must is None) or (must in out)
            ok = (got_red == want_red) and not not_found and (not want_red or anchored)
            fails += 0 if ok else 1
            tail = [l for l in out.splitlines() if l.strip().startswith(("E  ", "assert", "FAILED"))][:1]
            rows.append((name, "RED" if got_red else "GREEN", "期望RED" if want_red else "期望GREEN",
                         "✅" if ok else ("⛔ nodeid 不存在" if not_found else
                                         ("⛔ 红了但不在声称的串上" if got_red and not anchored else "⛔ 假绿")),
                         why, tail[0][:90] if tail else ""))
            print(f"[{'✅' if ok else '⛔'}] {name:16s} {'RED' if got_red else 'GREEN':6s} "
                  f"({'期望RED' if want_red else '期望GREEN'})  {why[:58]}")
            # 逐段留证：跑了哪些 nodeid、rc 多少、红在哪条断言、文本锚是否命中
            print(f"      变异={keys}  rc={rc}")
            for _nid in nodeids:
                print(f"      nodeid: {_nid}")
            if must is not None:
                print(f"      文本锚 {must!r}: {'命中' if anchored else '**未命中**'}")
            _sum = [l for l in out.splitlines() if l.startswith("FAILED ") or l.startswith("E   ")]
            for l in _sum[:3]:
                print(f"      | {l[:150]}")
            if not _sum and want_red:
                print("      | (无 FAILED/E 行 —— 该段没有可辨认的失败正文)")
            if not ok:
                print("      ---- 该段输出尾部 ----")
                print("\n".join("      " + l for l in out.splitlines()[-12:]))
    print()
    sha1 = {t: hashlib.sha256(t.read_bytes()).hexdigest() for t in TARGETS}
    for t in TARGETS:
        same = SHA0[t] == sha1[t]
        print(f"{'✅' if same else '⛔'} {t.name:22s}\n     跑前 {SHA0[t]}\n     跑后 {sha1[t]}")
        fails += 0 if same else 1
    print(f"\n段数 {len(SEGMENTS)} 期望RED + {len(EXPECT_GREEN)} 期望GREEN, 不合判据 {fails}")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
