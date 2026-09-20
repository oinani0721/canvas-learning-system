#!/usr/bin/env python3
"""CARD-SEB-WRITER-SUBSTRING-TMP (e) 普查: 9 份 SKILL.md 的 fence 分桶 + 执行动作命中。

来源: T7-B 验收单 §七「建议普查其余 Skill 执行动作混进 prompt 模板」。
T7-B 形态 = **写点嵌在给生成器看的 System Prompt 模板 fence 内** —— 那种块会被
模型当成要生成的文本而不是要执行的动作, 于是「写点」根本不跑。

判法: 按 fence 语言标签分桶; 标签 ∉ {bash, python, sh, shell} 的 fence 里若出现
执行动作关键词, 记为候选 (start, end, tag, 命中词), 再由人逐条判「T7-B 形态 /
执行者指令 fence(非缺陷) / 已修」。

⛔ 已知假阴面 (验收单如实登记): 关键词集合只有下面 7 个, 此外的执行动作形态
本脚本看不见。

验伪锚: 同一个 fence 配对逻辑对 ```bash fence 数一次 PYEOF, 必须给出
ai-linked-doc 2 / start-exam-board 6 / quiz-answer 4 —— 证明脚本真读到了 fence 内容。

用法: python3 skill-fence-census.py <worktree-root>
"""
import glob
import os
import re
import sys

KW = re.compile(r"python3 |PYEOF|`Bash`|Bash:|mkdir -p|os\.write|`Write`")
FENCE_RE = re.compile(r"^(`{3,4})(\S*)\s*$")
EXEC_TAGS = {"bash", "python", "sh", "shell"}
SAME_FAMILY = re.compile(r'in ln for ln|decode\("utf-8", "replace"\)')


def fences(lines):
    """产出 (start_lineno, end_lineno, tag, body) —— 开/关按同长度反引号配对。"""
    out = []
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        ticks, tag = m.group(1), m.group(2)
        j = i + 1
        while j < len(lines):
            m2 = FENCE_RE.match(lines[j])
            if m2 and m2.group(1) == ticks and m2.group(2) == "":
                break
            j += 1
        out.append((i + 1, min(j, len(lines) - 1) + 1, tag, lines[i + 1 : j]))
        i = j + 1
    return out


def main() -> int:
    root = sys.argv[1]
    files = sorted(glob.glob(os.path.join(root, "canvas-vault/.claude/skills/*/SKILL.md")))
    n_flag = 0
    print("=== (e) 普查: prompt 模板 fence 内的执行动作 (T7-B 形态) ===")
    print(f"关键词集合 = {KW.pattern}")
    for path in files:
        rel = os.path.relpath(path, root)
        text = open(path, encoding="utf-8").read()
        lines = text.split("\n")
        blocks = fences(lines)
        buckets: dict[str, int] = {}
        for _s, _e, tag, _b in blocks:
            buckets[tag or "(no-tag)"] = buckets.get(tag or "(no-tag)", 0) + 1
        print(f"\n--- {rel}  fences={len(blocks)} 分桶={dict(sorted(buckets.items()))}")
        for start, end, tag, body in blocks:
            if tag in EXEC_TAGS:
                continue
            joined = "\n".join(body)
            hits = sorted(set(KW.findall(joined)))
            if hits:
                n_flag += 1
                print(f"    FLAG {rel}:{start}-{end} tag={tag!r} 命中={hits}")
        for idx, line in enumerate(lines, 1):
            if SAME_FAMILY.search(line):
                print(f"    SAME-FAMILY {rel}:{idx}: {line.strip()[:110]}")
    print(f"\nfiles= {len(files)}  flagged_fences= {n_flag}")

    print("\n=== 验伪锚: ```bash fence 内的 PYEOF 计数 (证明真读到了 fence 内容) ===")
    for path in files:
        rel = os.path.relpath(path, root)
        lines = open(path, encoding="utf-8").read().split("\n")
        n = sum(
            "\n".join(b).count("PYEOF") for _s, _e, tag, b in fences(lines) if tag == "bash"
        )
        if n:
            print(f"    {rel}: bash-fence 内 PYEOF 出现 {n} 次")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
