#!/usr/bin/env python3
"""CARD-C5 裁判: 回顾报告规定段落检查。usage: check_report_sections.py <report.md> [--expect-fallback]"""
import re
import sys

REQUIRED = [
    ("frontmatter type: recap", re.compile(r"^type:\s*recap\s*$", re.M)),
    ("规模自陈 callout", re.compile(r"\[!info\]\+\s*规模自陈")),
    ("## 数据来源与新鲜度", re.compile(r"^## 数据来源与新鲜度", re.M)),
    ("## 本段新增", re.compile(r"^## 本段新增", re.M)),
    ("## 你现在可以做的", re.compile(r"^## 你现在可以做的", re.M)),
    ("## 台账", re.compile(r"^## 台账", re.M)),
    ("## AI 侧对账", re.compile(r"^## AI 侧对账", re.M)),
    ("## 三维审查", re.compile(r"^## 三维审查", re.M)),
    ("board_sha256 in frontmatter", re.compile(r"^board_sha256:", re.M)),
]

FORBIDDEN = [
    ("HARD-R4 禁词(偏离/你以为/其实你/你理解错/但资料说)", re.compile(r"偏离|你以为|其实你|你理解错|但资料说")),
    ("占位符残留(<X>/<板名>/<节点名>/PENDING)", re.compile(r"<X>|<板名>|<节点名>|<node|PENDING")),
    ("白名单外动作/甩锅句(docker/启动服务/请先启动/终端/命令行)", re.compile(r"docker|启动服务|请先启动|终端|命令行")),
]

SECTION3_FORBIDDEN = re.compile(r"你当时|你当初|你选择|你决定")

path = sys.argv[1]
expect_fallback = "--expect-fallback" in sys.argv
text = open(path, encoding="utf-8").read()
ok = True
for name, rx in REQUIRED:
    hit = bool(rx.search(text))
    print(("  ✓ " if hit else "  ✗ ") + name)
    ok &= hit
for name, rx in FORBIDDEN:
    m = rx.search(text)
    clean = m is None
    print(("  ✓ 0命中 " if clean else f"  ✗ 命中[{m.group(0)}] ") + name)
    ok &= clean
sec3 = re.search(r"^### ③.*?(?=^### |\Z)", text, re.M | re.S)
if sec3:
    m3 = SECTION3_FORBIDDEN.search(sec3.group(0))
    clean3 = m3 is None
    print(("  ✓ 0命中 " if clean3 else f"  ✗ 命中[{m3.group(0)}] ") + "③方向段用户主语(你当时/你当初/你选择/你决定)")
    ok &= clean3
else:
    print("  ✗ 缺 ### ③ 方向段")
    ok = False

# 规则5: 完整 64 位 SHA
msha = re.search(r'^board_sha256:\s*"?([0-9a-f]+)"?', text, re.M)
sha_ok = bool(msha) and len(msha.group(1)) == 64
print(("  ✓ " if sha_ok else "  ✗ ") + f"board_sha256 完整 64 hex (got {len(msha.group(1)) if msha else 0})")
ok &= sha_ok

# 规则7: fallback 派生断言禁词
if expect_fallback:
    mfd = re.search(r"已派生|未派生|从未派生", text)
    fd_ok = mfd is None
    print(("  ✓ 0命中 " if fd_ok else f"  ✗ 命中[{mfd.group(0)}] ") + "fallback 派生断言(已派生/未派生/从未派生)")
    ok &= fd_ok

# 规则8: 动作句白名单动词逐条命中
VERB = re.compile(r"/node-chat|/start-exam-board|/board-recap|Cmd\+Shift\+D|Cmd\+Shift\+A|Dashboard")
macts = re.search(r"^## 你现在可以做的\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
if macts:
    items = re.findall(r"^\d+\.\s.*(?:\n(?!\d+\.\s|##).*)*", macts.group(1), re.M)
    bad = [it[:40] for it in items if not VERB.search(it)]
    act_ok = not bad and bool(items)
    print(("  ✓ " if act_ok else "  ✗ ") + f"动作句白名单动词逐条命中 ({len(items)} 条{'; 违规: ' + str(bad) if bad else ''})")
    ok &= act_ok
if expect_fallback:
    hit = bool(re.search(r"data_mode:\s*fallback_local", text)) and ("FALLBACK" in text)
    print(("  ✓ " if hit else "  ✗ ") + "FALLBACK 声明（frontmatter + 正文）")
    ok &= hit
else:
    hit = bool(re.search(r"data_mode:\s*manifest", text))
    print(("  ✓ " if hit else "  ✗ ") + "data_mode: manifest")
    ok &= hit
print(("PASS " if ok else "FAIL ") + path)
sys.exit(0 if ok else 1)
