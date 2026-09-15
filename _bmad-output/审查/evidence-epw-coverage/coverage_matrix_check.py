"""CARD-EPW-COVERAGE 覆盖矩阵自校门。

判据（全部成立才 rc=0）：
  1. 主表恰 37 行（表头/分隔行不计）；
  2. 主表的 37 条 nodeid 与 red-align §三的 33 条 + 4 条「原本绿」**互为同一集合**
     （⛔ 按节名从 red-align 现场捞，不抄行号、不硬编码清单）；
  3. 四类承接计数 N1 + N2 + 15 + N3 == 37，且 `T10-C 已 un-skip 重写` 恰为 15；
  4. 统计段自述的 N1/N2/N3 与表内实数一致（防「表改了统计没改」）。

用法: python3 coverage_matrix_check.py <matrix.md> <red-align.md>
"""

import re
import sys

matrix_path, red_align_path = sys.argv[1], sys.argv[2]
matrix = open(matrix_path, encoding="utf-8").read()
red_align = open(red_align_path, encoding="utf-8").read()

# ── 1. red-align §三：33 条（代码块）+ 4 条原本绿（散文行）──────────────────
c1_block = re.search(
    r"### CARD-RED-C1 —— 33 条.*?```\n(.*?)```", red_align, re.S
)
if not c1_block:
    print("❌ red-align §三「CARD-RED-C1 —— 33 条」代码块未捞到（节名漂移？）")
    sys.exit(1)
c1 = [ln.strip() for ln in c1_block.group(1).splitlines() if ln.strip()]

green_sec = re.search(r"### 另：Y4-D 顺带关掉的 4 条「原本绿」\n(.*?)\n\n", red_align, re.S)
if not green_sec:
    print("❌ red-align §三「另：Y4-D 顺带关掉的 4 条」小节未捞到（节名漂移？）")
    sys.exit(1)
green_text = green_sec.group(1)
# 形态: `file::Class::{a, b, c}` + `file::Class::d`
green = []
for m in re.finditer(r"([\w./]+\.py)::(\w+)::\{([^}]*)\}", green_text):
    for name in m.group(3).split(","):
        green.append(f"tests/unit/{m.group(1)}::{m.group(2)}::{name.strip()}")
for m in re.finditer(r"([\w./]+\.py)::(\w+)::(test_\w+)(?!\s*[,}])", green_text):
    nodeid = f"tests/unit/{m.group(1)}::{m.group(2)}::{m.group(3)}"
    if nodeid not in green:
        green.append(nodeid)

expected = set(c1) | set(green)
print(f"red-align: C1={len(c1)} 原本绿={len(green)} 合计={len(expected)}")
if len(c1) != 33 or len(green) != 4 or len(expected) != 37:
    print("❌ red-align 侧条数不是 33 + 4 = 37")
    sys.exit(1)

# ── 2. 主表 37 行 ───────────────────────────────────────────────────────────
rows = []
for line in matrix.splitlines():
    # 列序: | # | `nodeid`(可带「（原本绿）」尾巴) | 语义 | 承接方 | 承接用例/依据 |
    m = re.match(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`[^|]*\|([^|]*)\|([^|]*)\|", line)
    if m:
        rows.append((int(m.group(1)), m.group(2).strip(), m.group(4).strip()))
print(f"matrix: rows={len(rows)}")
if len(rows) != 37:
    print(f"❌ 主表行数 {len(rows)} ≠ 37")
    sys.exit(1)
if [r[0] for r in rows] != list(range(1, 38)):
    print("❌ 主表序号不是 1..37 连续")
    sys.exit(1)

got = {f"tests/unit/{r[1]}" for r in rows}
missing = sorted(expected - got)
extra = sorted(got - expected)
for x in missing:
    print("❌ 矩阵缺 nodeid:", x)
for x in extra:
    print("❌ 矩阵多出 red-align 没有的 nodeid:", x)
if missing or extra:
    sys.exit(1)

# ── 3. 四类承接计数 ─────────────────────────────────────────────────────────
buckets = {"新文件": 0, "已有 retry 测试": 0, "T10-C 已 un-skip 重写": 0, "语义已删·无等价·登记退役": 0}
for _, nodeid, owner in rows:
    if owner not in buckets:
        print(f"❌ 承接方不在枚举内: {owner!r} ({nodeid})")
        sys.exit(1)
    buckets[owner] += 1
n1, n2, n3 = buckets["新文件"], buckets["已有 retry 测试"], buckets["语义已删·无等价·登记退役"]
t10c = buckets["T10-C 已 un-skip 重写"]
print(f"N1(新文件)={n1} N2(已有 retry 测试)={n2} T10-C={t10c} N3(退役)={n3}")
if t10c != 15:
    print(f"❌ T10-C 承接 {t10c} ≠ 15")
    sys.exit(1)
if n1 + n2 + 15 + n3 != 37:
    print(f"❌ N1+N2+15+N3 = {n1 + n2 + 15 + n3} ≠ 37")
    sys.exit(1)

# ── 4. 统计段自述值与表内实数一致 ───────────────────────────────────────────
declared = dict(
    N1=int(re.search(r"新文件承接 N1 = (\d+)", matrix).group(1)),
    N2=int(re.search(r"已有 retry 测试承接 N2 = (\d+)", matrix).group(1)),
    T10C=int(re.search(r"T10-C 已 un-skip 重写 = (\d+)", matrix).group(1)),
    N3=int(re.search(r"语义已删·无等价·登记退役 N3 = (\d+)", matrix).group(1)),
)
if (declared["N1"], declared["N2"], declared["T10C"], declared["N3"]) != (n1, n2, t10c, n3):
    print(f"❌ 统计段自述 {declared} 与表内实数 (N1={n1},N2={n2},T10C={t10c},N3={n3}) 不一致")
    sys.exit(1)

print("EPW-MATRIX-GATE: PASS")
