# 候选年上界充分性验证：对同一批 spec，比较 (y-1..y+1) / (y-2..y+1) / (y-3..y+2) 三种候选窗
# 与 libc 的分歧数。只在隔离目录跑（scratchpad 根有 select.py 会遮蔽 stdlib）。
import importlib.util, itertools, os, sys, time
from datetime import datetime, timedelta, timezone

ROOT = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review"
spec = importlib.util.spec_from_file_location("_cw_local_tz", ROOT + "/scripts/local_tz.py")
mod = importlib.util.module_from_spec(spec); sys.modules["_cw_local_tz"] = mod; spec.loader.exec_module(mod)
PosixTZ = mod._PosixTZ

def make_in_dst(lo, hi):
    def _in_dst(self, ts):
        y = time.gmtime(ts).tm_year
        for year in range(y + lo, y + hi + 1):
            s, e = self._dst_window(year)
            if s <= e:
                if s <= ts < e:
                    return True
            else:
                if s <= ts < self._dst_window(year + 1)[1]:
                    return True
        return False
    return _in_dst

STRATEGIES = {"y-1..y+1": (-1, 1), "y-2..y+1": (-2, 1), "y-3..y+2": (-3, 2)}

# spec 空间：极端偏移 × 三类规则 × 极端切换时刻
OFFS = ["-14", "-12", "-9:30", "-1", "0", "1", "5", "11", "14", "23"]
RULES = ["M1.1.0", "M2.5.0", "M3.2.0", "M6.1.0", "M10.1.0", "M12.5.0",
         "J1", "J59", "J60", "J364", "J365", "0", "1", "59", "60", "364", "365"]
TIMES = [None, "0", "2", "24", "25", "167", "167:59:59"]

def probe_points(years):
    out = []
    for y in years:
        for m, d in ((1, 1), (1, 2), (2, 28), (3, 1), (6, 15), (12, 30), (12, 31)):
            try: base = datetime(y, m, d, tzinfo=timezone.utc)
            except ValueError: continue
            for h in (0, 1, 2, 3, 4, 6, 12, 18, 23):
                out.append(base + timedelta(hours=h))
        t = datetime(y, 1, 1, 9, tzinfo=timezone.utc)
        while t.year == y:
            out.append(t); t += timedelta(days=11)
    return out

YEARS = [2008, 2015, 2020, 2023, 2024, 2027, 2028, 2031, 2036]
PTS = probe_points(YEARS)
print(f"probe points per spec = {len(PTS)}")

import random
random.seed(20260914)
specs = set()
for off in OFFS:
    for sr, er in itertools.product(RULES, RULES):
        specs.add(f"AAA{off}BBB,{sr},{er}")
for _ in range(1200):
    off = random.choice(OFFS); doff = random.choice(OFFS)
    sr, er = random.choice(RULES), random.choice(RULES)
    st, et = random.choice(TIMES), random.choice(TIMES)
    s = f"AAA{off}BBB{doff},{sr}" + (f"/{st}" if st else "") + f",{er}" + (f"/{et}" if et else "")
    specs.add(s)
specs = sorted(specs)
print(f"spec count = {len(specs)}")

results = {k: {"mismatch_specs": set(), "mismatch_points": 0} for k in STRATEGIES}
skipped = 0
for sp in specs:
    tz = mod.parse_posix_tz(sp)
    if tz is None:
        skipped += 1; continue
    os.environ["TZ"] = sp; time.tzset()
    libc_vals = []
    ok = True
    for t in PTS:
        try: libc_vals.append(t.astimezone().replace(tzinfo=None))
        except Exception: ok = False; break
    if not ok: skipped += 1; continue
    for name, (lo, hi) in STRATEGIES.items():
        PosixTZ._in_dst = make_in_dst(lo, hi)
        for t, lv in zip(PTS, libc_vals):
            try: got = t.astimezone(tz).replace(tzinfo=None)
            except Exception: got = None
            if got != lv:
                results[name]["mismatch_specs"].add(sp)
                results[name]["mismatch_points"] += 1
print(f"skipped (unparsable/overflow) = {skipped}")
print()
for name in STRATEGIES:
    r = results[name]
    print(f"{name:>10}: 分歧 spec 数 = {len(r['mismatch_specs']):4d}   分歧点数 = {r['mismatch_points']}")
    for s in sorted(r["mismatch_specs"])[:6]:
        print(f"              例: {s}")
