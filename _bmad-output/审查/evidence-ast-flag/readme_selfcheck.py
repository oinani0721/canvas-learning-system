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

refs = sorted(set(re.findall(r"`([A-Za-z0-9_.\-]+\.(?:txt|py|nodeids|md))`", txt)))
missing = [r for r in refs if r not in have]
placeholders = re.findall(r"<[^>]{1,40}>", txt)
ellipses = re.findall(r"[^\s`]*" + chr(0x2026) + r"[^\s`]*", txt)

print(f"1. 引用 {len(refs)} 个具体文件名，缺失 = {missing or '（无）'}")
print(f"2. 尖括号占位 = {placeholders or '（无）'}")
print(f"3. 省略号引用 = {ellipses or '（无）'}")

print("\n验伪锚（三条判据各自必须能看见问题）：")
print("  1) 不存在的名字会被判 missing =", "no-such-file-20260917.txt" not in have)
_ph_probe = "见 " + chr(60) + "最终 ts" + chr(62) + ".txt"
print("  2) 占位正则对合成的占位样本有命中 =", bool(re.findall(r"<[^>]{1,40}>", _ph_probe)))
_el_probe = "见 a-" + chr(0x2026) + "-b.txt"
print("  3) 省略号正则对合成的省略号样本有命中 =", bool(re.findall(r"[^\s`]*" + chr(0x2026) + r"[^\s`]*", _el_probe)))

bad = bool(missing or placeholders or ellipses)
print("\nREADME-SELFCHECK:", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
