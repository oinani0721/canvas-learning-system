#!/usr/bin/env python3
"""禁写面判据（CARD-G2-7b，Codex r2 BLOCKER-1~4 整改后的唯一实现）。

用法：
    cls_forbidden_paths.py <live_vault> [--strict] <label>:<path> ... [--outputs <label>:<path> ...]

两类对象、两套规则（缺 `--outputs` 时全部按 strict 判）：

  **strict**（三个路径参数 `--vault` / `--evidence-dir` / `--env-dir`）
      全部规则，含「自身是 `.env` / `*.env` / `.env.*`」——把它们指向一个 env 文件
      几乎肯定是笔误，且会导致写入对象与预期完全不同。

  **outputs**（脚本自己要产出的文件：`.env.<vault>` / key 文件 / 插件 `data.json` / …）
      跳过 env 文件名规则 —— `.env.<vault>` **本身就是** env 文件，用那条规则判它
      会让脚本永远拦下自己的正常产出（本卡实测：整改后所有正控 rc 71）。
      其余规则照旧：保护目录、`.git` 段、软链沿链。

每个待判对象一行输出 `HIT <label> <命中的那一条>` 或 `OK <label>`；
只要有一条 HIT，退出码 1；全部 OK 退出码 0；用法错 64。

═══ 为什么不用 bash 写 ═══

Codex r2 BLOCKER-1 指出（并用纯函数核验坐实）：bash 侧的三种解释——`cd -L` + `pwd -P`、
纯字符串折叠 `..`、大小写归一——**全部是词法/逻辑层面的**，没有一种能回答
「`mkdir -p` 最终写到哪个 inode」。一个反例就让三条同时错到同一个错答案：

    /safe/link/../probe        link → $HOME/.codex/sub
    物理落点 = $HOME/.codex/probe      （`..` 是 link **目标**的父目录）
    cd -L / 字符串折叠都得到 = /safe/probe   ⇒ 三条解释一致地漏拦

其余同类形态（Codex r2 逐条列出，本文件全部覆盖）：
  · `/safe/missing/../alias/probe`  折叠后不再解析 alias
  · `/safe/link<LF>/probe`          命令替换剥掉末尾换行 ⇒ 解析到别的目录
  · `"$HOME/*/../.codex/probe"`     bash `set -- $p` 会把 `*` 做**通配符展开**
  · 字面 `"~/probe"`                只有判据展开 `~`，实际写入用字面量

`os.path.realpath` 的语义正好是需要的那个：**先解软链再折叠 `..`**，顺序正确，
且对不存在的路径也能给出规范结果（Python 3.6+ 的 strict=False 行为）。
argv 保真（不剥末尾换行），也不做通配符展开。

═══ 判定规则 ═══

命中任一即拦（方向刻意选**多拦**——禁写面上误拦是麻烦，漏拦是事故）：

1. 路径中任何一段名为 `.git`（大小写归一后比）
2. 自身是 `.env` / `*.env` / `.env.*`（大小写归一后比）
3. 等于或位于下列任一目标之下（大小写归一后比）：
   live vault · `$HOME/Library` · `$HOME/.codex` · `.pi` · `.gemini` · `.deepcode`
   · `.dsh` · `$HOME/.config/opencode`
4. `$HOME/.claude*` **两条并存**（Codex r2 BLOCKER-3）：
   ① 已存在条目的**解析结果**（软链目标也算，如 `~/.claude → /external/claude`）
   ② `$HOME/.claude` 词法前缀（覆盖「现在不存在、正要去建」的）
   ——只留 ② 会丢掉软链目标；只留 ① 会丢掉尚不存在的。
5. 路径中任何一段是**软链**且解开后落在上述任一目标里（沿链写穿）
6. 字面以 `~` 开头（Codex r2 BLOCKER-1 第 5 条）：判据会展开它、shell 不会，
   两者落点必然分歧 ⇒ 直接拒，让调用方写绝对路径。

大小写归一的依据：macOS/APFS 缺省**大小写不敏感**，`.CODEX` 与 `.codex` 是同一目录。
在大小写敏感的文件系统上这会多拦（两个真不同的目录被当成一个），方向可接受。
⚠️ 如实声明：`str.lower()` 不等于 APFS 的 Unicode 等价折叠规则（Codex r2 已指出
`tr` 的 locale 依赖）；本实现用 Python 的 `str.lower()`，不依赖 locale，但仍不声称
与 APFS 的规范化完全一致。纯 ASCII 与常见中文路径不受影响。
"""

from __future__ import annotations

import os
import sys


def phys(p: str) -> str:
    """物理解析：展开 ~ → 绝对化 → **解软链后再折叠 `..`**。对不存在的路径也可用。"""
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(os.getcwd(), p)
    return os.path.realpath(p)


def k(p: str) -> str:
    """比较用的键：物理路径 + 大小写归一。"""
    return phys(p).lower()


def build_targets(live: str) -> tuple[list[tuple[str, str]], str]:
    home = os.path.expanduser("~")
    raw = [live, os.path.join(home, "Library")]
    for d in (".codex", ".pi", ".gemini", ".deepcode", ".dsh"):
        raw.append(os.path.join(home, d))
    raw.append(os.path.join(home, ".config", "opencode"))

    # 规则 4①：已存在的 .claude* 条目 —— 登记它们的**解析结果**（含软链目标）
    try:
        for name in sorted(os.listdir(home)):
            if name.startswith(".claude"):
                raw.append(os.path.join(home, name))
    except OSError:
        pass

    targets = []
    for r in raw:
        try:
            targets.append((k(r), r))
        except OSError:
            continue
    # 规则 4②：词法前缀（覆盖尚不存在的 .claude*）
    claude_prefix = os.path.join(phys(home), ".claude").lower()
    return targets, claude_prefix


def ancestor_symlink_hits(p: str, targets: list[tuple[str, str]], claude_prefix: str) -> str | None:
    """规则 5：路径中任何一段是软链且解开后落在保护目标里。

    `phys()` 已经解了链，所以这条主要覆盖「祖先段是软链、但它自己不在保护目标里，
    而它的**目标**在」的情形——`phys()` 会一并解掉，此处作为显式的第二道。
    """
    cur = os.path.expanduser(p)
    if not os.path.isabs(cur):
        cur = os.path.join(os.getcwd(), cur)
    seen = 0
    while cur and cur != os.sep and seen < 64:
        seen += 1
        if os.path.islink(cur):
            resolved = k(cur)
            for tk, orig in targets:
                if resolved == tk or resolved.startswith(tk + os.sep):
                    return f"{orig}（经软链 {cur}）"
            if resolved.startswith(claude_prefix):
                return f"{claude_prefix}*（经软链 {cur}）"
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def hits(
    raw_path: str,
    targets: list[tuple[str, str]],
    claude_prefix: str,
    *,
    skip_env_name: bool = False,
) -> str | None:
    # 规则 6：字面 ~ 开头 —— 判据展开、shell 不展开，落点必然分歧
    if raw_path.startswith("~"):
        return "字面 ~ 开头（判据会展开、shell 不会 ⇒ 落点分歧，请写绝对路径）"

    key = k(raw_path)
    parts = key.split(os.sep)

    # 规则 1：任何一段名为 .git（大小写归一后 —— Codex r2 BLOCKER-2：原实现比的是原串）
    if ".git" in parts:
        return ".git 目录内"

    # 规则 2：自身是 env 文件（同样大小写归一）。outputs 类跳过 —— 见文件头「两类对象」。
    if not skip_env_name:
        base = parts[-1] if parts else ""
        if base == ".env" or base.endswith(".env") or base.startswith(".env."):
            return "*.env 文件"

    # 规则 3 + 4：等于或位于保护目标之下
    for tk, orig in targets:
        if key == tk or key.startswith(tk + os.sep):
            return orig
    if key.startswith(claude_prefix):
        return f"{claude_prefix}*（前缀规则）"

    # 规则 5
    return ancestor_symlink_hits(raw_path, targets, claude_prefix)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("用法: cls_forbidden_paths.py <live_vault> <label>:<path> [...]", file=sys.stderr)
        return 64
    live = argv[1]
    targets, claude_prefix = build_targets(live)

    mode = "strict"
    items: list[tuple[str, str]] = []
    for a in argv[2:]:
        if a == "--strict":
            mode = "strict"
            continue
        if a == "--outputs":
            mode = "outputs"
            continue
        items.append((mode, a))

    bad = 0
    for mode_i, item in items:
        label, _, path = item.partition(":")
        if not path:
            print(f"用法错: 参数应为 <label>:<path>，收到 {item!r}", file=sys.stderr)
            return 64
        why = hits(path, targets, claude_prefix, skip_env_name=(mode_i == "outputs"))
        if why:
            print(f"HIT {label} {why}")
            bad += 1
        else:
            print(f"OK {label}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
