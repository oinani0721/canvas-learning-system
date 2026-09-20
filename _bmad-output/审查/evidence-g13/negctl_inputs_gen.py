#!/usr/bin/env python3
"""CARD-G1-3 —— 负控/对照输入的生成器。

**为什么有这个文件**：负控汇总只记录了每段的判定结果，没留下被判定的那份输入，
于是「段 4 是怎么构造的」「段 12 覆盖了一种还是两种路径」都无从复核
（Codex r6 LOW-4）。这里把每个输入的构造写成代码，任何人都能重新生成同一批副本再跑一遍。

跑法::

    python3 negctl_inputs_gen.py --ledger <台账路径> --out <输出目录>
    # 然后对每份副本跑：
    #   python3 ledger_lint.py --repo <树根> --ledger <副本> --trunk HEAD

⚠️ 副本一律写到 --out 指定的目录（用 scratch，不要写进仓）。本脚本**只读**台账原件。
"""

from __future__ import annotations

import argparse
import io
import os

ABS_MANIFEST = "docs/release-evidence/example-backfill-d5/journeys/J08/manifest.json"


def _load(path: str) -> list[str]:
    return io.open(path, encoding="utf-8").read().split("\n")


def _col(line: str, idx: int, val: str) -> str:
    c = line.split("|")
    c[idx] = val
    return "|".join(c)


def build(ledger: str, out: str, repo: str) -> dict[str, str]:
    lines = _load(ledger)
    rows = [i for i, l in enumerate(lines) if l.startswith("| CAP-")]
    hdr = next(i for i, l in enumerate(lines) if l.startswith("| id |"))
    made: dict[str, str] = {}

    def w(name: str, ls: list[str], note: str) -> None:
        os.makedirs(out, exist_ok=True)
        io.open(os.path.join(out, name), "w", encoding="utf-8").write("\n".join(ls))
        made[name] = note

    def E5(x: str) -> str:
        return _col(x, 5, " E5 ")

    # ── 核心段：每段只拆一层 ────────────────────────────────────────────
    m = list(lines)
    m[rows[0]] = m[rows[0]].replace("backend/tests/unit/test_deploy_vault_sh.py",
                                    "backend/tests/unit/test_deploy_vault_sh_NONEXISTENT.py", 1)
    w("mut1.md", m, "段1 L4：证据里一条真实路径改成不存在的文件名")

    m = list(lines); m[rows[1]] = _col(m[rows[1]], 5, " E3 ")
    w("mut2.md", m, "段2 L3：E1→E3，证据列不动（无 manifest）")

    m = list(lines); m[rows[2]] = _col(m[rows[2]], 5, " E3 ")
    c = m[rows[2]].split("|")
    c[8] = c[8].rstrip() + f" · `{ABS_MANIFEST}` "
    m[rows[2]] = "|".join(c)
    w("mut3.md", m, "段3 L3：证据指向真实存在但 mode=reconstructed 的 manifest")

    # ⚠️ 段 4 必须同时改自述：只截行不改自述会同时红 L15，就不是只拆一层了。
    m4 = lines[:rows[14]] + lines[rows[-1] + 1:]
    m4 = [l.replace("**本版条目数**: 21", "**本版条目数**: 14") if "本版条目数" in l else l
          for l in m4]
    w("mut4.md", m4, "段4 L1：截到 14 行**且自述同步改为 14**（不同步会连带红 L15）")

    m = list(lines); m[rows[3]] = m[rows[3]].replace("`b4705dde`", "`41cc849c`", 1)
    w("mut5.md", m, "段5 L11：证据 SHA 改过本行入口但未合入主干（L4/L12 应仍绿）")

    m = list(lines); m[rows[0]] = m[rows[0]].replace("`8eeaa899`", "`9c4e7e82`", 1)
    w("mut6.md", m, "段6 L12：证据 SHA 是主干祖先但没改过本行入口（L4/L11 应仍绿）")

    m = list(lines); c = m[rows[0]].split("|")
    c[11] = " 7e1d6b53 "
    c[8] = c[8].replace("`8eeaa899`", "`79134975`")
    m[rows[0]] = "|".join(c)
    w("mut8.md", m, "段8 L9：核验 SHA 换成未合入的车道 tip，证据 SHA 换成它的祖先（L11/L12 会被这条自洽链骗过）")

    m = list(lines); m[rows[2]] = _col(m[rows[2]], 5, " E3 ")
    c = m[rows[2]].split("|")
    c[8] = c[8].rstrip() + " · `docs/release-evidence/example-backfill-d5/Journeys/J08/manifest.json` "
    m[rows[2]] = "|".join(c)
    w("mut9.md", m, "段9 L3：大小写变体路径（旧整串正则对它命中 0 次）")

    m = list(lines); m[rows[0]] = _col(m[rows[0]], 8, " 主干 `8eeaa899` ")
    w("mut10.md", m, "段10 L4：删光某行证据的文件路径与 tag，只留 SHA")

    # 段 12 是两份输入，不是一份 —— r6 LOW-4 指出汇总把它们合成了一条
    for name, ref, note in (
        ("mut12a.md", os.path.join(repo, ABS_MANIFEST), "段12a L3：绝对路径写法"),
        ("mut12b.md", "../card-p10-docs/" + ABS_MANIFEST, "段12b L3：`../<树名>/` 上跳写法"),
    ):
        m = list(lines); m[rows[2]] = _col(m[rows[2]], 5, " E3 ")
        c = m[rows[2]].split("|")
        c[8] = c[8].rstrip() + f" · `{ref}` "
        m[rows[2]] = "|".join(c)
        w(name, m, note)

    # ── 藏行六形态（r4 HIGH）────────────────────────────────────────────
    tail = rows[15:]
    base = [l for i, l in enumerate(lines) if i not in set(tail)]
    k2 = next(i for i, l in enumerate(base) if l.strip().startswith("| **E5**"))

    m = list(lines)
    for i in tail:
        m[i] = E5(m[i])[1:]          # 只删掉行首那一个竖线
    w("f1.md", m, "f1：后六行改 E5 + 只删行首竖线（渲染完全不变）")

    w("f2.md", base + ["", "> " + lines[hdr].strip(), "> " + lines[hdr + 1].strip()]
      + ["> " + E5(lines[i]).strip() for i in tail], "f2：引用块表格")
    w("f3.md", base + [""] + [f"- {lines[i].split('|')[1].strip()} — E5" for i in tail],
      "f3：普通列表")
    w("f4.md", base[:k2 + 1] + [f"| {lines[i].split('|')[1].strip()} | E5 |" for i in tail]
      + base[k2 + 1:], "f4：塞进两列规则表")
    w("f5.md", base + ["", "``` ```", "", lines[hdr], lines[hdr + 1]]
      + [E5(lines[i]) for i in tail], "f5：行内三反引号扰乱围栏")
    w("f6.md", base[:k2 + 1]
      + [f"| <table><tr><td>{lines[i].split('|')[1].strip()}</td></tr></table> | x |" for i in tail]
      + base[k2 + 1:], "f6：单元格内 HTML 表")

    # ── 自述定位三形态（r5 M-1）─────────────────────────────────────────
    w("h1-fakedecl.md",
      ["```text", "> **本版条目数**: 15", "```", ""] + base + [""]
      + [f"- {lines[i].split('|')[1].strip()} — E5" for i in tail],
      "h1：代码块里的假声明抢占真声明 + 行挪成列表")
    w("h2-dupdecl.md", lines + ["", "> **本版条目数**: 15", ""], "h2：代码块外两处自述")
    w("h3-decimal.md",
      [l.replace("**本版条目数**: 21", "**本版条目数**: 21.5") if "本版条目数" in l else l
       for l in lines], "h3：自述写 21.5（旧实现读成 21）")

    # ── 对照输入：合法写法不得假红 ──────────────────────────────────────
    w("g1.md", lines + ["", "说明 A | 说明 B", "-------------", ""], "g1：Setext 标题")
    w("g2.md", lines + ["", "````", "```", lines[hdr], lines[hdr + 1], lines[rows[0]], "```", "````", ""],
      "g2：四反引号包三反引号")
    m = list(lines)
    kk = next(i for i, l in enumerate(m) if l.startswith("| E 级 |"))
    m[kk] = m[kk].replace("本仓判定条件", "本仓判定条件（含 a \\| b）")
    w("g3.md", m, "g3：表头里合法的转义竖线")
    w("g4.md", lines + ["", "请勿使用行内代码 `<table>` 标签。", ""], "g4：行内代码讲 <table>")
    m = list(lines)
    c = m[rows[14]].split("|")
    c[2] = " Canvas 边理由 \\| 向量化写入 "
    m[rows[14]] = "|".join(c)
    w("h4-escpipe.md", m, "h4：能力名里写合法的转义竖线（旧实现七条判据假红）")
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 CARD-G1-3 的全部负控/对照输入")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--out", required=True, help="输出目录（用 scratch，别写进仓）")
    ap.add_argument("--repo", default=os.getcwd(), help="树根，供绝对路径输入使用")
    args = ap.parse_args()
    made = build(args.ledger, args.out, os.path.abspath(args.repo))
    print(f"# 生成 {len(made)} 份输入 → {args.out}")
    for name, note in made.items():
        print(f"  {name:<18} {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
