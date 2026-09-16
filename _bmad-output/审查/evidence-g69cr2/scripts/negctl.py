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
 # `\Z`（绝对串尾）退回 `$`（在末尾换行之前收尾）
 "ENDANCHOR": M(r'    r"(?:/(?P<etime>\d+(?::\d+(?::\d+)?)?))?)?\Z"',
                r'    r"(?:/(?P<etime>\d+(?::\d+(?::\d+)?)?))?)?$"  # NEGCTL'),
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
 # 裸名词法退回 [A-Za-z]{3,}（连带去掉「< 开头扫不到 > 就当裸名」那一支）
 "BARENAME": M(r'    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"',
               r'    r"^(?P<std><[^<>]+>|[A-Za-z]{3,})"  # NEGCTL'),
 # std 侧去掉「< 开头扫不到 > 就当裸名」那一支（只坏 `<AAA1` 一族，不动别的）
 "ANGLEFALLBACK": M(r'    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"',
                    r'    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+)"  # NEGCTL'),
 # 名字数字集从 ASCII 退回 \d（连带吃掉 Unicode 数字）
 "UNIDIGIT": M(r'    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"',
               r'    r"^(?P<std><[^>\x00]*>|(?!<)[^\d+,\-\x00]+|<[^>\d+,\-\x00]*)"  # NEGCTL'),
 # 引用名内容排除 `<`（r12 那条真误收的退化形态：`<AAA1<DEF>2` 会被当成裸名 `<AAA`+偏移 1）
 "QUOTEDINNER": M(r'    r"^(?P<std><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"',
                  r'    r"^(?P<std><[^<>\x00]*>|(?!<)[^0-9+,\-\x00]+|<[^>0-9+,\-\x00]*)"  # NEGCTL'),
 # 路径候选去掉「文件必须真实存在」这一关
 "PATHEXIST": M('        if base.is_file():', '        if True:  # NEGCTL 不验文件是否存在'),
 # 前导冒号不再禁用 POSIX 回退
 "COLONPOSIX": M('        if not env_tz.startswith(":"):',
                 '        if True:  # NEGCTL 冒号前缀也退 POSIX'),
 # _strip_name 退回只判 startswith
 "STRIPNAME": M('''    if len(name) >= 2 and name.startswith("<") and name.endswith(">"):
        return name[1:-1]
    return name''',
                '''    return name[1:-1] if name.startswith("<") else name  # NEGCTL'''),
 # fromutc 去掉 TypeError 分支
 "FROMUTCTYPE": M('''        if not isinstance(dt, datetime):''', '''        if False:  # NEGCTL'''),
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
 # NUL 防线现在在**正则**里（名字的三个字符类各自排除 `\x00`）, 不再有独立的检查行。
 # 变异 = 去掉 **dst 引用名**那一支的 NUL 排除, 与本段探针 `AAA0<B\x00BB>` 对齐
 # （⛔ 变异的位置必须与探针落在**同一支**上, 否则拆的不是探针经过的那条路）。
 "NUL": M(r'    r"(?:(?P<dst><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+)"',
          r'    r"(?:(?P<dst><[^>]*>|(?!<)[^0-9+,\-\x00]+)"  # NEGCTL'),
 # 「CAP」（1024 长度上限）那条变异已随该检查在 r12 被删除而移除 ——
 # 正则位宽放宽后指数回溯消失, 它从性能防线退化成纯误拒（Codex r11 M5）。
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

# ⛔ 接受域表的 nodeid 是 `accept-N` / `reject-N`, N = 它在表里的**下标**。
#    直接写死 N 极其脆弱: 往表中间插一条, 后面所有段的绑定**静默错位** ——
#    红仍是红, 但红的不是声称的那条（本卡 r12 往表里补对照组时就撞上了）。
#    改成按 **spec 文本**去表里现查下标: 表怎么改, 绑定跟着走; 查不到直接 abort。
def _acceptance_table():
    """从测试文件里把 `_ACCEPTANCE_DOMAIN_CASES` 原样执行出来（不 import 整个测试模块）。"""
    import ast
    src = (ROOT / "backend" / F).read_text(encoding="utf-8")
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "_ACCEPTANCE_DOMAIN_CASES" for t in n.targets))
    ns: dict = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<tbl>", "exec"), ns)
    return ns["_ACCEPTANCE_DOMAIN_CASES"]


def acc(*specs):
    """按 spec 文本定位表里的下标, 生成两份副本的 nodeid。"""
    table = _acceptance_table()
    out = []
    for spec in specs:
        hits = [i for i, row in enumerate(table) if row[0] == spec]
        assert len(hits) == 1, f"接受域表里 {spec[:40]!r} 命中 {len(hits)} 次（应恰好 1）"
        i = hits[0]
        kind = "accept" if table[i][2] else "reject"   # 第 3 列 = 本实现收不收
        out += [f"{F}::{A}[{kind}-{i}-{c}]" for c in ("backend", "scripts")]
    return out

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
 # ⛔ 原「尾部换行」段已删: 它变异的那条检查（②）在 r12 被删除 —— 理由被 L4 推翻。
 #    同一条防线现在由正则的 `\Z` 结尾锚守, 故改成变异 `\Z` → `$`。
 ("正则结尾锚", ["ENDANCHOR"], acc("AAA-1BBB,M3.2.0,M11.1.0\n"),
  "Python 的 `$` 在末尾换行**之前**收尾 ⇒ 写 `$` 会把带规则的尾部换行串误收"),
 ("严格UTF-8", ["ENC"],
  [f"{F}::test_display_tz_survives_non_utf8_tz_bytes",
   f"{F}::test_non_utf8_key_never_reaches_response_on_any_branch"],
  "r5→r6: surrogateescape 只把失败从启动挪到响应出口"),
 # ⛔ 探针必须选在**只有这一条检查能拦**的串上: `M３.2.0` 被「数字字段 ASCII」与
 #    「规则文本 ASCII」两条同时拦着, 拆掉任一条它都不会红（r12 实测假绿）。
 #    全角落在**切换时刻的分钟**上, 只有数字字段那条管得着。
 ("ASCII数字", ["ASCII"], acc("AAA0BBB,M3.2.0/2:３0,M11.1.0"),
  "Python \\d 连全角一起匹配, C 库拒（探针: 全角在切换时刻分钟字段）"),
 ("切换时刻小时", ["HMAX"], acc("AAA0BBB,M3.2.0/168,M11.1.0"), "167 接受 / 168 拒"),
 ("切换时刻分钟", ["MIN60"], acc("AAA0BBB,M3.2.0/2:60,M11.1.0"), "分钟 >59 拒"),
 ("切换时刻秒", ["SEC60"], acc("AAA0BBB,M3.2.0/2:00:61,M11.1.0"), "秒 60 接受 / 61 拒"),
 # 同上: 全角落在**规则文本**（`start`/`end`）里, 只有规则文本那条管得着。
 ("规则ASCII", ["RULEA"], acc("AAA0BBB,J３60,M11.1.0"),
  "规则文本里的全角数字（探针: 全角在 start 字段, 数字字段检查看不到它）"),
 ("std偏移必填", ["STDREQ"], acc("<AAA><BBB>,M3.2.0,M11.1.0", "<AAA>"), "r9 M3: 所有形态都必填"),
 ("名字和式512", ["NAMESUM"], acc("<" + "A" * 512 + ">-1", "<" + "A" * 507 + ">-1<" + "B" * 507 + ">,M3.2.0,M11.1.0"),
  "退回单名 ≤507 口径 ⇒ 无 dst 形态不查(误收) + 两名各 507 和 1016(误收)"),
 ("名字量纲字节", ["NAMECHAR"], acc("AAA0<" + "中" * 170 + ">"), "中×170 = 510 字节 / 170 字符, 按字符算会误收"),
 # ── 以下 8 段为 r11 新增（Codex r10 的 H1 / M1 / M2 / M4 / M5 / M9 / L7）──
 ("空名占NUL", ["EMPTYNAME"], acc("<" + "A" * 511 + ">-1<>,M3.2.0,M11.1.0"),
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
 # ── 以下 6 段为 r12 新增（Codex r11 的 H1 / H2 / M1 / M2 / L5）──
 # ⛔ 这段守的是 r12 组合门扩到 98532 组合后才暴露的**真误收**（1666 条）:
 #    引用名内容含 `<` 时（`<AAA1<DEF>2`）, 若把内容字符集写成 `[^<>]*`, 该串会掉到
 #    裸名分支被当成 `<AAA` + 偏移 `1` 收下, 而 C 库的引用名是「`<` 到**第一个** `>`」,
 #    名字应是 `AAA1<DEF`。这是「判据看不见的地方, 错和对一样」的实例。
 ("引用名内容含尖括号", ["QUOTEDINNER"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r12: 引用名是 `<` 到第一个 `>`, 内容允许 `<`; 写 `[^<>]*` 会误收 1666 条",
  "误收"),
 ("尖括号裸名回退", ["ANGLEFALLBACK"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r11 M1: std 侧 `<` 开头扫不到 `>` 时 C 库当裸名收（`<AAA1`）, 去掉这一支会误拒",
  "误拒·未声明"),
 ("名字数字集ASCII", ["UNIDIGIT"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r11 M2: `\\d` 连非 ASCII 数字一起吃 ⇒ `ABC١1` / `ABC１1` 被误拒",
  "误拒·未声明"),
 ("路径必须存在", ["PATHEXIST"],
  [f"{F}::test_tz_path_forms_match_libc"],
  "r11 H1: 不验文件存在 ⇒ `/does-not-exist/zoneinfo/Asia/Shanghai` 被认成上海(差 8 小时)"),
 ("冒号禁POSIX回退", ["COLONPOSIX"],
  [f"{F}::test_tz_path_forms_match_libc"],
  "r11 H2: `:AAA-1` C 库给 UTC, 退 POSIX 会把它当合法规格串收下"),
 ("strip_name闭合判定", ["STRIPNAME"],
  [f"{F}::test_accepted_domain_grid_matches_libc"],
  "r11 M1: 只判 startswith 会把 `<AAA1` 剥成 `AA` ⇒ 名字长度少算两字节",
  "误收"),
 ("fromutc类型校验", ["FROMUTCTYPE"],
  [f"{F}::test_fromutc_rejects_foreign_tzinfo"],
  "r11 L5: 非 datetime 参数应抛 TypeError（stdlib 口径）, 缺了会撞成 AttributeError"),
 ("std偏移量级", ["STDMAG"],
  [f"{F}::test_offset_domain_is_checked_on_every_branch_not_only_omitted_rules"],
  "|std_off| < 24h 的 Python 可表示性收紧"),
 ("规则可解析", ["RULEOK"], acc("AAA-1,J0,J0"), "r9 M4: 无 dst 形态也要验规则"),
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
  "NUL 排除现在在**正则的名字字符类**里（r12 起, 独立的 ③ 检查已删——七种位置全由正则拒）",
  "parse_posix_tz('AAA0<B" + chr(92) + "x00BB>')"),
 ("HIGH-3归桶", ["HIGH2"],
  [f"{F}::test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent"],
  "display_tz 缺席时不得静默用 generated_at 的固定偏移重算归桶"),
]
# 如实登记: 这两条**预期不变红**, 段本身就是它们性质的证明。
# ⛔ EXPECT_GREEN 现在是**空的**, 这是一条真实的进展而不是省略:
#    上一轮唯一一段期望 GREEN 是「1024 长度上限」—— 当时如实登记它「只由计时判据守、
#    不由 pytest 守」。r12 查明那条上限在正则位宽放宽之后**零收益**（灾难性回溯来自
#    有界量词嵌套, 不是串长; 同一条 4000 字符坏串 0.475s → 0.012ms）, 于是整条删除。
#    检查没了, 为它开的「如实登记」段自然一并消失 —— 现在每一段都必须真的变红。
EXPECT_GREEN: list = []

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
