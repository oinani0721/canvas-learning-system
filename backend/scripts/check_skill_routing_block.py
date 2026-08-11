#!/usr/bin/env python3
"""RAG-S2.6 T5 — 8 份 skill 的检索平面协议静态校验器。

skill 是 prompt 不是代码, 没法单测。本校验器守住**可静态断言**的那部分,
让「导航协议」不至于在后续编辑里悄悄腐烂:

  C1 ROUTING 块 8 份逐字节相等 (canonical = start-exam-board 那份)
  C2 ROUTING 块内容完整 (HARD-NAV-1..4 四条硬约束都在)
  C3 PLANE-BINDING 5 字段齐 + 取值合法 + 自洽
     (uses_structure: no ⇒ structure_tool/manifest_view 必须都是 none)
  C4 **工具面与绑定一致** — 声明用 STRUCTURE ⇔ frontmatter allowed-tools 含
     manifest 工具; 声明不用 ⇔ 一定不含 (这是真正的强制点: skill 调不了
     没被 allow 的工具)
  C5 uses_structure: yes ⇒ 至少 1 对 FALLBACK sentinel (降级路径必须写下来,
     否则后端一挂 skill 就地趴窝); FALLBACK sentinel 必须成对且不嵌套

用法:
    python3 backend/scripts/check_skill_routing_block.py            # 默认本仓 canvas-vault
    python3 backend/scripts/check_skill_routing_block.py --vault <path>
退出码: 0 全绿 / 1 有违规 / 2 环境不可用
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

MANIFEST_TOOL = "mcp__canvas-learning-mcp__get_board_manifest"
CANONICAL_SKILL = "start-exam-board"

#: 8 份 skill 全集 —— 少一份也算违规 (防「新加的 skill 忘了声明平面」)
EXPECTED_SKILLS = frozenset(
    {
        "ai-linked-doc",
        "chat-with-context",
        "configure-whiteboard",
        "exam-quick",
        "node-chat",
        "quiz-answer",
        "start-exam-board",
        "study-question",
    }
)

#: ⛔ 计划显式点名: exam-quick 必须**不含** manifest 工具 —— 它的存在前提是后端已挂,
#: 在故障链上叠 MCP 调用是倒退 (裁定见该 skill 的 §检索平面裁定)
MUST_NOT_HAVE_MANIFEST = frozenset({"exam-quick", "quiz-answer", "node-chat"})

BINDING_FIELDS = ("primary_plane", "uses_structure", "structure_tool", "manifest_view", "fallback_path")
VALID_PLANES = frozenset({"STRUCTURE", "SEMANTIC", "CONTENT", "EXAM"})
VALID_VIEWS = frozenset({"study", "exam", "none"})

_ROUTING_RE = re.compile(r"<!-- ROUTING:BEGIN v1 -->.*?<!-- ROUTING:END v1 -->", re.S)
_BINDING_RE = re.compile(r"<!-- PLANE-BINDING v1\n(.*?)\n-->", re.S)
_ALLOWED_TOOLS_RE = re.compile(r"^allowed-tools:\n((?:  - .*\n)+)", re.M)
_REQUIRED_HARD_NAV = ("HARD-NAV-1", "HARD-NAV-2", "HARD-NAV-3", "HARD-NAV-4")


class Checker:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def add(self, cid: str, ok: bool, detail: str = "") -> None:
        self.results.append((cid, ok, detail))
        mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"  {mark} {cid}" + (f" — {detail}" if detail and not ok else ""))

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [r for r in self.results if not r[1]]


def parse_binding(text: str) -> dict[str, str] | None:
    m = _BINDING_RE.search(text)
    if not m:
        return None
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def allowed_tools(text: str) -> list[str]:
    m = _ALLOWED_TOOLS_RE.search(text)
    return [ln.strip().removeprefix("- ").strip() for ln in m.group(1).splitlines()] if m else []


def fallback_pairs(text: str) -> tuple[int, str | None]:
    """→ (成对数, 错误说明)。BEGIN/END 必须严格交替且不嵌套。

    ⛔ 先剥掉 ROUTING / PLANE-BINDING 两块再数: ROUTING 的 HARD-NAV-3 正文里
    引用了 `<!-- FALLBACK:BEGIN/END -->` 字样, 那是**约定的说明**不是真 sentinel,
    不剥会让 8 份 skill 全部假阳性 (本校验器首跑实测踩到)。
    """
    body = _BINDING_RE.sub("", _ROUTING_RE.sub("", text))
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^\s*<!-- FALLBACK:(BEGIN|END)\b", body, re.M)]
    depth, pairs = 0, 0
    for _, kind in marks:
        if kind == "BEGIN":
            if depth:
                return pairs, "FALLBACK 块嵌套 (BEGIN 未闭合就又 BEGIN)"
            depth = 1
        else:
            if not depth:
                return pairs, "FALLBACK:END 没有对应的 BEGIN"
            depth, pairs = 0, pairs + 1
    if depth:
        return pairs, "FALLBACK:BEGIN 未闭合"
    return pairs, None


def main() -> int:
    ap = argparse.ArgumentParser(description="检索平面协议校验器 (RAG-S2.6)")
    ap.add_argument("--vault", help="vault 根目录 (缺省 = 本仓 canvas-vault)")
    args = ap.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).resolve().parents[2] / "canvas-vault"
    skills_dir = vault / ".claude" / "skills"
    if not skills_dir.is_dir():
        print(f"{RED}环境不可用: 找不到 {skills_dir}{RESET}")
        return 2

    found = {p.parent.name: p for p in sorted(skills_dir.glob("*/SKILL.md"))}
    print(f"检索平面协议校验 — {skills_dir}")
    print(f"发现 {len(found)} 份 skill\n")

    c = Checker()
    missing = EXPECTED_SKILLS - set(found)
    extra = set(found) - EXPECTED_SKILLS
    c.add(
        "C0[skill 全集]",
        not missing and not extra,
        f"缺={sorted(missing)} 多={sorted(extra)} (新 skill 必须同批声明平面并登记进本校验器)",
    )

    texts = {name: path.read_text(encoding="utf-8") for name, path in found.items()}

    # ── C1/C2 ROUTING 块 ──
    canonical = None
    if CANONICAL_SKILL in texts:
        m = _ROUTING_RE.search(texts[CANONICAL_SKILL])
        canonical = m.group(0) if m else None
    if canonical is None:
        c.add("C1[ROUTING canonical]", False, f"{CANONICAL_SKILL} 里取不到 ROUTING 块")
    else:
        c.add("C1[ROUTING canonical]", True)
        c.add(
            "C2[ROUTING 内容完整]",
            all(k in canonical for k in _REQUIRED_HARD_NAV),
            f"缺硬约束: {[k for k in _REQUIRED_HARD_NAV if k not in canonical]}",
        )
        for name in sorted(texts):
            m = _ROUTING_RE.search(texts[name])
            if m is None:
                c.add(f"C1[{name}]", False, "无 ROUTING 块")
            else:
                c.add(f"C1[{name}]", m.group(0) == canonical, "ROUTING 块与 canonical 不逐字节相等")

    # ── C3/C4/C5 逐 skill ──
    for name in sorted(texts):
        text = texts[name]
        binding = parse_binding(text)
        if binding is None:
            c.add(f"C3[{name}]", False, "无 PLANE-BINDING 块")
            continue

        problems = [f"缺字段 {f}" for f in BINDING_FIELDS if f not in binding]
        plane, uses = binding.get("primary_plane"), binding.get("uses_structure")
        tool, view = binding.get("structure_tool"), binding.get("manifest_view")
        if plane not in VALID_PLANES:
            problems.append(f"primary_plane={plane!r} 非法 (合法: {sorted(VALID_PLANES)})")
        if uses not in ("yes", "no"):
            problems.append(f"uses_structure={uses!r} 非法 (yes|no)")
        if view not in VALID_VIEWS:
            problems.append(f"manifest_view={view!r} 非法 (合法: {sorted(VALID_VIEWS)})")
        if uses == "no" and (tool != "none" or view != "none"):
            problems.append(f"uses_structure:no 但 structure_tool={tool!r} manifest_view={view!r} (必须都 none)")
        if uses == "yes" and tool != MANIFEST_TOOL:
            problems.append(f"uses_structure:yes 但 structure_tool={tool!r}")
        if not binding.get("fallback_path"):
            problems.append("fallback_path 为空")
        c.add(f"C3[{name}]", not problems, "; ".join(problems))

        # C4 工具面 ⇔ 绑定
        tools = allowed_tools(text)
        has_tool = MANIFEST_TOOL in tools
        want = uses == "yes"
        detail = f"allowed-tools {'含' if has_tool else '不含'} manifest 工具, 但 uses_structure={uses}"
        if name in MUST_NOT_HAVE_MANIFEST and has_tool:
            detail = f"⛔ {name} 被显式裁定禁用 STRUCTURE 平面, allowed-tools 不得含 manifest 工具"
        c.add(f"C4[{name}]", has_tool == want and not (name in MUST_NOT_HAVE_MANIFEST and has_tool), detail)

        # C5 FALLBACK sentinel
        pairs, err = fallback_pairs(text)
        if err:
            c.add(f"C5[{name}]", False, err)
        elif want and pairs < 1:
            c.add(f"C5[{name}]", False, "声明用 STRUCTURE 但没有任何 FALLBACK 降级块 (后端一挂即趴窝)")
        else:
            c.add(f"C5[{name}]", True, f"{pairs} 对")

    total, failed = len(c.results), len(c.failed)
    print(f"\n合计: {total - failed}/{total} 通过")
    if failed:
        print(f"{RED}FAIL — {failed} 项违规{RESET}")
        for cid, _, detail in c.failed:
            print(f"  {RED}{cid}{RESET}: {detail}")
        return 1
    print(f"{GREEN}PASS — 8 份 skill 的检索平面协议全绿{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
