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
import unicodedata


def phys(p: str) -> str:
    """物理解析：展开 ~ → 绝对化 → **解软链后再折叠 `..`**。对不存在的路径也可用。"""
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(os.getcwd(), p)
    return os.path.realpath(p)


def k(p: str) -> str:
    """比较用的键：物理路径 + Unicode NFC 归一 + 大小写归一。

    Codex r3 HIGH-2：`realpath().lower()` 不统一 NFC/NFD —— APFS 把两种拼写视为同一对象，
    而 `课程-é`（NFC）与 `课程-e\u0301`（NFD）字符串不相等 ⇒ 保护根或其软链目标含可分解
    字符时会漏拦。先 NFC 再 lower。
    ⚠️ 如实声明：NFC + lower 仍不等于 APFS 的完整规范化规则，只是覆盖了最常见的一类。
    """
    return unicodedata.normalize("NFC", phys(p)).lower()


def build_targets(live: str) -> tuple[list[tuple[str, str]], list[str], bool]:
    home = os.path.expanduser("~")
    raw = [live, os.path.join(home, "Library")]
    for d in (".codex", ".pi", ".gemini", ".deepcode", ".dsh"):
        raw.append(os.path.join(home, d))
    raw.append(os.path.join(home, ".config", "opencode"))

    # 规则 4①：已存在的 .claude* 条目 —— 登记它们的**解析结果**（含软链目标）
    # Codex r3 HIGH-1 两处：
    #   ① `listdir` 失败原本静默 pass —— HOME 可执行但不可读时，已知子路径仍可访问，
    #      于是外部软链目标整批丢失、HOME 前缀补不上。改为**记录失败**，由调用方按
    #      fail-closed 处理（enumerate_failed）。
    #   ② `startswith(".claude")` 大小写敏感 —— `.CLAUDE-cache -> /external/cache` 漏登记。
    enumerate_failed = False
    # ⛔ `listdir` 成功 ≠ **解链**成功（Codex r5 BLOCKER-3）：HOME 有读权限（r）但无搜索权限
    #    （x）时，`listdir` 照常返回名字，而解析子项需要**搜索**权限 ——
    #    `realpath(strict=False)` 会把 EACCES 吞掉、返回未解析的路径串，于是外部保护目标
    #    （`.claude-cache -> /external/cache`）整批漏登记，而 `enumerate_failed` 仍是 False。
    #    这里两道一起上：先问权限位，再对每个软链条目**真的 readlink 一次**。
    #    只问权限位不够（`os.access` 用实际 uid，root 恒真——r4 LOW-1 同型）；
    #    只 readlink 也不够（还没走到条目就不可搜索时，islink 本身静默返回 False）。
    if not os.access(home, os.R_OK | os.X_OK):
        enumerate_failed = True
    try:
        for name in sorted(os.listdir(home)):
            if name.lower().startswith(".claude"):
                entry = os.path.join(home, name)
                raw.append(entry)
                try:
                    if os.path.islink(entry):
                        os.readlink(entry)
                except OSError:
                    enumerate_failed = True
    except OSError:
        enumerate_failed = True

    targets = []
    for r in raw:
        try:
            targets.append((k(r), r))
        except OSError:
            continue
    # 规则 4②：**词法**前缀（覆盖尚不存在的 .claude*）—— **两条轴并存**
    # ⛔ 绝不能对 `.claude` 那一段过 k()（Codex r4 BLOCKER-1，我 r3 统一 NFC 时引入的回归）：
    #    k() 内含 realpath。若 `$HOME/.claude -> /external/claude-base`, 前缀就变成
    #    `/external/claude-base` —— 于是 `$HOME/.claude-new/probe`（尚不存在, 枚举登记不到）
    #    **失去保护**, 而 `/external/claude-baseball/probe` 反被误拦。
    # ⛔ 但只留**词法** HOME 又丢掉物理轴（Codex r5 BLOCKER-1，r4 修上一条时引入的反向回归）：
    #    `HOME=/homealias -> /homephys` 时, 尚不存在的 `/homephys/.claude-new/probe`
    #    既不在枚举名单里、也不匹配 `/homealias/.claude` ⇒ 放行。
    #    ⇒ 这两条需求是**正交**的, 不是二选一：不 realpath `.claude` 这一段, 但要 realpath
    #      **HOME 那一段**。故前缀取两条：词法 HOME 与物理 HOME 各拼一次 `.claude`。
    #      两条都不含 realpath(`.claude`) ⇒ baseball 误拦与 `.claude-new` 失保护都不会回来。
    claude_prefixes: list[str] = []
    for base in (home, os.path.realpath(home)):
        pfx = unicodedata.normalize("NFC", os.path.join(base, ".claude")).lower()
        if pfx not in claude_prefixes:
            claude_prefixes.append(pfx)
    return targets, claude_prefixes, enumerate_failed


def walk_visited(p: str, limit: int = 256) -> tuple[list[str], bool]:
    """模拟内核 `namei`：**逐段**解析, 返回途中经过的每一个路径对象。

    ⛔ Codex r5 BLOCKER-2 —— 旧的 `resolve_chain` 把「路径」当成一个**原子对象**来解，
    而内核是**逐段**解的。两个拓扑因此漏掉：

      (a) `alias -> hop/sub`, `hop -> repo/.git`, `.git -> external/meta`
          旧实现只在**整条路径**上判 `islink`：`islink("/x/hop/sub")` 会先解掉 `hop`
          落到 `external/meta/sub`, `sub` 自身不是链 ⇒ False ⇒ 链停在第一跳。
          中间那个 `.git` **原始串里没有、realpath 结果里也没有**, 两边都看不见。
      (b) `alias -> /repo/.git/../sub`, `.git -> /external/meta/sub`
          旧实现 `os.path.normpath(nxt)` 把 `.git/..` **词法折叠**成 `/repo/sub` ——
          而内核是**解完 `.git` 才处理 `..`**, 真实落点是 `/external/meta/sub`。

    这与 r3 BLOCKER-1（`mkdir -p` 的写入面不是一个 inode 而是一串）是**同一个认知错误
    的第二次出现**：上次是「创建面是一串」, 这次是「遍历面是一串」。

    做法：从根开始逐段拼, 每拼一段就记录该段的完整路径；遇软链读出目标并把目标的**段**
    压回待处理队列（**不 normpath**, 让 `..` 在解链之后才被处理）；遇 `..` 先记录当前
    位置再上移（`..` 之前的那一级是真的被遍历过的）。

    ⚠️ 与 `phys()` / `k()` 是**两个不同命题**, 不可互相替代也不可合并：
       前者答「途中经过哪些对象」, 后者答「最终落点是哪个」。合并 = 又一次「统一 helper
       会删掉一条规则」。
    返回 (visited, truncated)；`truncated` 为真时调用方必须 fail-closed。
    """
    path = os.path.expanduser(p)
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    pending = path.split(os.sep)
    cur = os.sep
    visited: list[str] = []
    steps = 0
    while pending:
        steps += 1
        if steps > limit:
            # ⛔ 超限**不再静默 break**（原第 21 条「未证明 64 跳够用」的正面回应）：
            #    静默停下等于对剩余部分宣称「安全」, 而我们并不知道。
            return visited, True
        seg = pending.pop(0)
        if seg in ("", "."):
            continue
        if seg == "..":
            visited.append(cur)
            parent = os.path.dirname(cur.rstrip(os.sep)) if cur != os.sep else os.sep
            cur = parent or os.sep
            continue
        nxt = os.sep + seg if cur == os.sep else cur.rstrip(os.sep) + os.sep + seg
        visited.append(nxt)
        try:
            is_link = os.path.islink(nxt)
        except OSError:
            is_link = False
        if not is_link:
            cur = nxt
            continue
        try:
            tgt = os.readlink(nxt)
        except OSError:
            cur = nxt
            continue
        if not os.path.isabs(tgt):
            # 相对目标以**链所在目录**为基准, 即 cur（不是 nxt）。
            tgt = os.sep + tgt if cur == os.sep else cur.rstrip(os.sep) + os.sep + tgt
        visited.append(tgt)
        pending = tgt.split(os.sep) + pending
        cur = os.sep
    visited.append(cur)
    return visited, False


def chain_hits(p: str, targets: list[tuple[str, str]], claude_prefixes: list[str]) -> str | None:
    """对 p 的整条遍历途径逐跳查 `.git` 段、保护目标与 `.claude*` 前缀。"""
    visited, truncated = walk_visited(p)
    for hop in visited:
        hop_key = unicodedata.normalize("NFC", hop).lower()
        if ".git" in hop_key.split(os.sep):
            return f".git 目录内（遍历途中经过 {hop}）"
        for tk, orig in targets:
            if hop_key == tk or hop_key.startswith(tk + os.sep):
                return f"{orig}（遍历途中经过 {hop}）"
        for pfx in claude_prefixes:
            if hop_key.startswith(pfx):
                return f"{pfx}*（遍历途中经过 {hop}）"
    if truncated:
        return "遍历跳数超过上限（疑似环或深链）, 无从断言安全 ⇒ fail-closed"
    return None


def ancestor_symlink_hits(p: str, targets: list[tuple[str, str]], claude_prefixes: list[str]) -> str | None:
    """规则 5：路径中任何一段是软链且解开后落在保护目标里。

    ⛔ **职责与 `chain_hits` 严格不重叠**（r5 整改时由变异测试逼出来的）：
    第一版我让本函数**也**调 `chain_hits`, 结果变异测试显示「删掉 `hits()` 里的逐段判据」
    那条门**仍绿** —— 因为本函数把它兜住了。两层互相兜底 = 谁都测不出承重，
    正是 r4 批过的「留着让人以为有两道防线」。
    ⇒ 现在分工是：
       · `chain_hits`（在 `hits()` 里直接调）—— **逐段遍历**轴：途中经过的每个对象
       · 本函数 —— **整体 realpath**轴：`k(cur)` 把祖先软链一次解到底后比保护目标
      两者是不同的计算，各自有变异门证明承重；本函数**不再**转调 `chain_hits`。
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
            for pfx in claude_prefixes:
                if resolved.startswith(pfx):
                    return f"{pfx}*（经软链 {cur}）"
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def mkdir_p_segments(raw_path: str) -> list[str]:
    """`mkdir -p <p>` 会实际创建的每一个中间目录（按创建顺序）。

    ⛔ Codex r3 BLOCKER-1：写入面不是**一个** inode 而是**一串**。
        mkdir -p "$HOME/.codex/new/../../deploy_env"
    最终落点是合法的 `$HOME/deploy_env`，但 mkdir 会**先创建 `$HOME/.codex/new`**——
    只判最终 realpath 完全看不到这一步。`..` 之前的每一段都是真会落地的目录。

    做法：按 `/` 逐段累积；遇到 `..` 时**不折叠**（因为前面的段已经被建出来了），
    而是把它当成一个新的前缀继续（后续段由 realpath 负责算物理落点）。
    返回的每个前缀都要单独过一遍判据。
    """
    p = os.path.expanduser(raw_path)
    if not os.path.isabs(p):
        p = os.path.join(os.getcwd(), p)
    out: list[str] = []
    cur = ""
    for seg in p.split(os.sep):
        if seg == "":
            continue
        cur = cur + os.sep + seg
        if seg == ".":
            continue
        out.append(cur)
    return out


def hits(
    raw_path: str,
    targets: list[tuple[str, str]],
    claude_prefixes: list[str],
    *,
    skip_env_name: bool = False,
) -> str | None:
    # 规则 6：字面 ~ 开头 —— 判据展开、shell 不展开，落点必然分歧
    if raw_path.startswith("~"):
        return "字面 ~ 开头（判据会展开、shell 不会 ⇒ 落点分歧，请写绝对路径）"

    key = k(raw_path)
    parts = key.split(os.sep)

    # 规则 1：任何一段名为 .git（大小写归一后 —— Codex r2 BLOCKER-2：原实现比的是原串）
    # ⚠️ 必须**同时**在原始路径上查（Codex r3 BLOCKER-1 第二半）：若 `.git -> /external/meta`,
    #    realpath 之后 `.git` 这个段就消失了, 只看 key 会放行 `<repo>/.git/x`。
    raw_expanded = os.path.expanduser(raw_path)
    raw_parts = [unicodedata.normalize("NFC", s).lower() for s in raw_expanded.split(os.sep)]
    if ".git" in parts or ".git" in raw_parts:
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
    # 词法前缀要拿**词法 key** 比（同口径, 不解链）；物理 key 也比一次, 两轴都不漏。
    # 前缀现为**两条**（词法 HOME / 物理 HOME, 见 build_targets 的 r5 BLOCKER-1 注释）。
    lex_key = unicodedata.normalize("NFC", os.path.abspath(os.path.expanduser(raw_path))).lower()
    for pfx in claude_prefixes:
        if key.startswith(pfx) or lex_key.startswith(pfx):
            return f"{pfx}*（词法前缀规则）"

    # ⛔ 逐段遍历判据（Codex r5 BLOCKER-2）：这一层是**唯一**的逐段轴。
    #    r4 的注释说这一层是死代码——那结论对**当时**的 `resolve_chain` 成立
    #    （它只解整条路径的末段, 能命中的 `ancestor_symlink_hits` 都能命中）。
    #    换成逐段 walker 之后关系反转：walker 能看见「祖先软链的目标里再有软链」
    #    这类中间跳, 而 `ancestor_symlink_hits` 的 `k(cur)` 一次解到底, 看不见途中。
    #    ⚠️ 承重性是**变异测试逼出来的**：第一版 `ancestor_symlink_hits` 也转调 chain_hits,
    #    于是删掉这一行门仍绿（两层互相兜底 ⇒ 谁都证不出承重）。现已拆开职责。
    ch = chain_hits(raw_path, targets, claude_prefixes)
    if ch is not None:
        return ch

    # 规则 5（保留；与 walker 的关系见 ancestor_symlink_hits 的 docstring，不宣称两道防线）。
    return ancestor_symlink_hits(raw_path, targets, claude_prefixes)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("用法: cls_forbidden_paths.py <live_vault> <label>:<path> [...]", file=sys.stderr)
        return 64
    live = argv[1]
    targets, claude_prefixes, enumerate_failed = build_targets(live)

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
        # ⚠️ 规则 6（字面 ~）必须在**逐段之前**查原始串：`mkdir_p_segments` 会先
        #    `expanduser`, 之后没有任何一段还以 `~` 开头 ⇒ 逐段判会让这条规则失效。
        #    （新加一层让原有一条失效, 与 r2 BLOCKER-3「收紧丢掉一轴」同型, 故显式前置。）
        why = None
        if path.startswith("~"):
            why = "字面 ~ 开头（判据会展开、shell 不会 ⇒ 落点分歧，请写绝对路径）"
        # ⛔ 逐段判（Codex r3 BLOCKER-1）：`mkdir -p` 会创建的每个中间目录都要过判据,
        #    只判最终落点会漏掉 `$HOME/.codex/new/../../deploy_env` 这类形态。
        segs = mkdir_p_segments(path) if why is None else []
        for seg_path in segs:
            # 中间段按 outputs 口径判（它们是目录, 不该被 env 文件名规则拦）;
            # 最终那一段仍按调用方给的口径判。
            is_last = seg_path == segs[-1]
            why = hits(
                seg_path,
                targets,
                claude_prefixes,
                skip_env_name=(True if not is_last else (mode_i == "outputs")),
            )
            if why:
                if not is_last:
                    why = f"{why}（mkdir -p 会创建的中间段 {seg_path}）"
                break
        if why:
            print(f"HIT {label} {why}")
            bad += 1
        else:
            print(f"OK {label}")

    # ⛔ fail-closed（Codex r3 HIGH-1）：HOME 枚举失败时 .claude* 的外部软链目标整批
    #    登记不上, 而 HOME 词法前缀补不了那一类。此时不敢声称「全部 OK」。
    if enumerate_failed and bad == 0:
        print("HIT _enumerate 无法枚举 HOME（.claude* 的外部目标可能未登记）, fail-closed")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
