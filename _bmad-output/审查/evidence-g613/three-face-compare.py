#!/usr/bin/env python3
"""CARD-G6-13 三面对账 (d)② — picker JSON / API _collect / Markdown 副本。

用法: python3 three-face-compare.py <picker-*.json> <three-face-api.json> <md-*.md>
判据: (板,节点,桶) 集合三方相等; ranked 板序 picker==api[:n]==md[:n] 且 api==md 全长;
      集合为空 ⇒ 判据作废 (rc=2, 不算通过)。
输出含 `three_face_equal=` 与 (不等时) `ranked 板序不等`。
"""

import json
import re
import sys
from pathlib import Path

PICKER, API, MD = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

payload = json.loads(PICKER.read_text(encoding="utf-8"))
api = json.loads(API.read_text(encoding="utf-8"))
md = MD.read_text(encoding="utf-8")

print("进面对账前先证键集 (不猜键名):")
print("  picker top keys:", sorted(payload.keys()))
print("  api    top keys:", sorted(api.keys()))

vault = api["vaults"][0]
proj = vault["projection"]
print("  api projection keys:", sorted(proj.keys()))

picker_set = {(n["board"], n["node"], n["bucket"]) for n in payload["due_nodes"]}
api_set = {(b["board"], nd["node"], nd["bucket"]) for b in proj["boards"] for nd in b["nodes"]}

BUCKET_CN = {
    "新卡": "new",
    "学习中": "learning_queue",
    "到期待复习": "due_now",
    "今天晚些到期": "due_today",
    "未来排期": "future",
}
md_set = set()
cur = None
for line in md.splitlines():
    m = re.match(r"\*\*(新卡|学习中|到期待复习|今天晚些到期|未来排期)\*\*（\d+）", line)
    if m:
        cur = BUCKET_CN[m.group(1)]
        continue
    if line.startswith(">"):
        cur = None
        continue
    m2 = re.match(r"- (.+?) · (.+?) — ", line)
    if m2 and cur is not None:
        md_set.add((m2.group(2), m2.group(1), cur))

picker_ranked = [t["board"] for t in payload["top_boards"]]
api_ranked = [b["board"] for b in proj["boards"]]
md_ranked = []
for line in md.splitlines():
    m = re.match(r"\| (.+?) \| [-0-9.]+ \| \d+ \|", line)
    if m:
        md_ranked.append(m.group(1).strip())

set_ok = picker_set == api_set == md_set
ranked_ok = (
    api_ranked[: len(picker_ranked)] == picker_ranked
    and md_ranked[: len(picker_ranked)] == picker_ranked
    and api_ranked == md_ranked
)
nonempty = len(picker_set) > 0

print()
print("三面集合 picker:", len(picker_set), "api:", len(api_set), "md:", len(md_set))
print("集合相等(三方):", set_ok)
if not set_ok:
    print("  差集 picker-api:", sorted(picker_set - api_set))
    print("  差集 api-md:", sorted(api_set - md_set))
print("ranked 板序 picker:", picker_ranked)
print("ranked 板序 api   :", api_ranked)
print("ranked 板序 md    :", md_ranked)
print("ranked 板序 对比:", "OK" if ranked_ok else "ranked 板序不等")
# 作废条件 = **三面全空**（真无到期节点）；任何单面为空而他人非空 = 真实不一致, 落 rc=1 不等,
# 不许把「某面漏了」误报成「今天没东西可对」。
if len(picker_set) == 0 and len(api_set) == 0 and len(md_set) == 0:
    print("三面集合均为空 ⇒ 判据作废 (当日无到期节点)")
    raise SystemExit(2)

three_face_equal = set_ok and ranked_ok
print("three_face_equal=" + str(three_face_equal))
raise SystemExit(0 if three_face_equal else 1)
