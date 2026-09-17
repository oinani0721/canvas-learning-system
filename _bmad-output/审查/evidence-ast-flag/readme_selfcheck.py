"""README 索引自检 —— 三条，各带验伪锚。

Codex 连三轮抓到「索引引用对不上」，三次形态不同：错时间戳、尖括号占位、时间戳中段写成
省略号。前两版自检都只覆盖了当时那一种，所以下一种照样漏过去。这里把三条一次钉住。

本 docstring 与下面的输出**刻意不字面写出**被禁形态：写了就会被 README 自检（它扫的是
README，不是本文件）之外的同类判据误伤 —— 更重要的是提醒：判据的文档一旦落进判据自己的
命中面，正确修法是改文字，不是给判据开豁免。
"""
import pathlib, re, sys

EV = pathlib.Path(__file__).parent
txt = (EV / "README.md").read_text(encoding="utf-8")
have = {p.name for p in EV.iterdir()}

EXTS = ("txt", "py", "nodeids", "md")
# ⛔ Codex round-4 LOW：上一版的提取器有两个窄口 ——
#   (a) 扩展名只认小写，`NO-SUCH.TXT` 整条提不出来 ⇒ 连「判缺失」的机会都没有；
#   (b) 字符集不含 `/` 与空格，`missing/report.txt` / `no such.txt` 同样提不出来。
#   提不出来 = 静默放行，比判错更难发现。现在按 basename 校验，并把目录前缀、空格、
#   大小写全部纳入提取面。
REF_RE = re.compile(r"`\s*([^`\n]*?\.(?:" + "|".join(EXTS) + r"))\s*`", re.IGNORECASE)
# README 合法引用的、**不在本目录**的文件（逐个写死；新增要有理由）
EXTERNAL = {"lifespan_isolation_negative_control.py", "README.md"}


def extract(text):
    """从文本里提取「看起来是文件引用」的 token，返回 (原样, basename)。"""
    out = []
    for raw in REF_RE.findall(text):
        base = raw.strip().rsplit("/", 1)[-1]
        out.append((raw, base))
    return out


refs = sorted(set(extract(txt)))
missing = [raw for raw, base in refs if base not in have and base not in EXTERNAL]
placeholders = re.findall(r"<[^>]{1,40}>", txt)
ellipses = re.findall(r"[^\s`]*" + chr(0x2026) + r"[^\s`]*", txt)

print(f"1. 引用 {len(refs)} 个文件名（含目录前缀/空格/大小写变体），缺失 = {missing or '（无）'}")
print(f"2. 尖括号占位 = {placeholders or '（无）'}")
print(f"3. 省略号引用 = {ellipses or '（无）'}")

print("\n验伪锚（三条判据各自必须能看见问题）：")
# ⛔ 验伪锚必须**走同一条提取器**（Codex round-4 LOW：上一版直接查集合成员关系，
#    绕过了提取器，所以提取器的窄口它一个都发现不了）。
_probes = ["`no-such-file-20260917.txt`", "`missing/report.txt`", "`no such.txt`",
           "` no-such.txt `", "`NO-SUCH.TXT`"]
_caught = []
for _pr in _probes:
    _ex = extract(_pr)
    _ok = bool(_ex) and all(b not in have and b not in EXTERNAL for _, b in _ex)
    _caught.append((_pr, _ok))
print("  1) 五种「不存在的引用」形态是否都被同一条提取器判 missing：")
for _pr, _ok in _caught:
    print(f"       {'✓' if _ok else '✗ 漏过'} {_pr}")
assert all(_ok for _, _ok in _caught), "提取器仍有漏过的形态"
_ph_probe = "见 " + chr(60) + "最终 ts" + chr(62) + ".txt"
print("  2) 占位正则对合成的占位样本有命中 =", bool(re.findall(r"<[^>]{1,40}>", _ph_probe)))
_el_probe = "见 a-" + chr(0x2026) + "-b.txt"
print("  3) 省略号正则对合成的省略号样本有命中 =", bool(re.findall(r"[^\s`]*" + chr(0x2026) + r"[^\s`]*", _el_probe)))

bad = bool(missing or placeholders or ellipses)
print("\nREADME-SELFCHECK:", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
