#!/usr/bin/env python3
"""CARD-SEB-WRITER-SUBSTRING-TMP AST 门（(b)② / (f)⑥）。

⛔ 数的是 **AST 节点**不是文本：修复后的注释里**故意保留**「禁用
`json.dumps(evid) in line`」字样，文本 grep 会在那里假红，AST 不受影响
（工程坑：结构门必须数 AST Call 节点，不是文本）。

验伪锚 = 同一个 count() 喂 `git show 9c4e7e82:<SKILL.md>` 的旧文本，
必须恒回 (1, 0, …)；它证明脚本真在数节点、且改后的 (0, 1, …) 不是脚本瞎了。

用法: python3 ast-gate.py <worktree-root>
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

SEB_REL = "canvas-vault/.claude/skills/start-exam-board/SKILL.md"
BASE_SHA = "9c4e7e82"
BLOCK_RE = re.compile(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", re.DOTALL)


def count(text: str) -> tuple[int, int, list[str]]:
    blocks = [b for b in BLOCK_RE.findall(text) if '"exam_created"' in b]
    assert len(blocks) == 1, f"落账块应恰 1 个, 实见 {len(blocks)}"
    tree = ast.parse(blocks[0])

    n_in = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Compare)
        and any(isinstance(o, ast.In) for o in n.ops)
        and isinstance(n.left, ast.Call)
        and ast.unparse(n.left.func) == "json.dumps"
    )
    n_eq = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Compare)
        and any(isinstance(o, ast.Eq) for o in n.ops)
        and any(
            '.get("event_id")' in ast.unparse(x) or ".get('event_id')" in ast.unparse(x)
            for x in [n.left, *n.comparators]
        )
    )
    handlers = sorted(
        {ast.unparse(h.type) for h in ast.walk(tree) if isinstance(h, ast.ExceptHandler) and h.type}
    )
    return n_in, n_eq, handlers


def main() -> int:
    root = Path(sys.argv[1])
    head_text = (root / SEB_REL).read_text(encoding="utf-8")
    base_text = subprocess.run(
        ["git", "-C", str(root), "show", f"{BASE_SHA}:{SEB_REL}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    print("HEAD", count(head_text))
    print("BASE", count(base_text), "  <- 验伪锚: 恒 (1, 0, ...)")
    print("同文本?", head_text == base_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
