# 复核 verify 的问题1：省略规则时 end 的切换时刻该不该随 dst-std 偏移差走。
import importlib.util, os, sys, time
from datetime import datetime, timedelta, timezone
ROOT = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review"
spec = importlib.util.spec_from_file_location("_er", ROOT + "/scripts/local_tz.py")
mod = importlib.util.module_from_spec(spec); sys.modules["_er"] = mod; spec.loader.exec_module(mod)

# 当前树上的实现（已含我落的 M3.2.0/M11.1.0 字面量）
def parse_cur(s): return mod.parse_posix_tz(s)

# 候选修正：end 的 secs = 3600 + dst_off - std_off
_orig = mod.parse_posix_tz
def parse_fix(s):
    m = mod._POSIX_TZ_RE.match(s)
    if not m: return None
    g = m.groupdict()
    std_off = mod._posix_offset_seconds(g["std_off"]) if g["std_off"] else 0
    if g["dst"] is None:
        return mod._PosixTZ(s, mod._strip_name(g["std"]), std_off, None, None, None, None)
    dst_off = mod._posix_offset_seconds(g["dst_off"]) if g["dst_off"] else std_off + 3600
    if g["start"] is None or g["end"] is None:
        start = ("M", 3, 2, 0, 2 * 3600)
        end = ("M", 11, 1, 0, 3600 + dst_off - std_off)
    else:
        start = mod._parse_rule(g["start"], g["stime"]); end = mod._parse_rule(g["end"], g["etime"])
    if start is None or end is None: return None
    return mod._PosixTZ(s, mod._strip_name(g["std"]), std_off, mod._strip_name(g["dst"]), dst_off, start, end)

SPECS = ["CET-1CEST",            # Δ=+1h  (常规)
         "XYZ5XYD",              # Δ=+1h
         "IST-1GMT0",            # Δ=-1h  (负偏移差, 本仓 _DEFAULT_TRANSITION_SCANS 里的真实形态)
         "<+10:30>-10:30<+11>",  # Δ=+30min
         "ABC-1DEF-5",           # Δ=+4h
         "NZST-12NZDT-13:30",    # Δ=+1.5h
         "AAA5BBB7"]             # Δ=-2h
def scan(fn, sp, y0, y1, step_min):
    os.environ["TZ"] = sp; time.tzset()
    tz = fn(sp)
    if tz is None: return None, "parse->None"
    bad = 0; first = None; tot = 0
    t = datetime(y0, 1, 1, tzinfo=timezone.utc); end = datetime(y1, 1, 1, tzinfo=timezone.utc)
    while t < end:
        tot += 1
        try:
            got = t.astimezone(tz).replace(tzinfo=None); lib = t.astimezone().replace(tzinfo=None)
        except Exception: t += timedelta(minutes=step_min); continue
        if got != lib:
            bad += 1
            if first is None: first = (t.isoformat(), str(got), str(lib))
        t += timedelta(minutes=step_min)
    return (bad, tot, first), None

print("=== 2007..2037 切换窗逐分钟（10/25-11/08 与 03/01-03/20）===")
for sp in SPECS:
    for label, fn in (("当前树", parse_cur), ("候选修正", parse_fix)):
        os.environ["TZ"] = sp; time.tzset()
        tz = fn(sp)
        if tz is None: print(f"  {sp:24s} {label}: parse->None"); continue
        bad = 0; tot = 0; first = None
        for y in range(2007, 2038):
            for (m0, d0, days) in ((10, 25, 15), (3, 1, 20)):
                t = datetime(y, m0, d0, tzinfo=timezone.utc)
                stop = t + timedelta(days=days)
                while t < stop:
                    tot += 1
                    try:
                        got = t.astimezone(tz).replace(tzinfo=None); lib = t.astimezone().replace(tzinfo=None)
                    except Exception: t += timedelta(minutes=1); continue
                    if got != lib:
                        bad += 1
                        if first is None: first = (t.isoformat(), str(got), str(lib))
                    t += timedelta(minutes=1)
        flag = "OK" if bad == 0 else "MISMATCH"
        print(f"  {sp:24s} {label:6s}: {flag} bad={bad}/{tot}" + (f"  first={first}" if first else ""))
