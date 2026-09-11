#!/usr/bin/env python3
"""路径安全**判据与原语**（CARD-G2-7b）。

两块内容，合在一处是为了单一来源：
  · **判据**（禁写面）—— `hits()` / `chain_hits()` / `walk_visited()` / `under()` / …
  · **原语**（安全写入）—— `open_pinned()` / `chmod_pinned()`（Codex r7 HIGH-1）
模块名沿用 `cls_forbidden_paths`（4 个调用点已引用）；DD-13 名实一致按本段口径理解：
它管的是「路径安全」这一件事的判与做，不只是「判」。

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

import errno
import os
import stat
import sys
import unicodedata


class ForbiddenPath(PermissionError):
    """判据自己的拒绝 —— 与**内核**的 EACCES 区分开（Codex r9 MEDIUM-1）。

    `PermissionError` 本身就是 `OSError(EACCES/EPERM)` 的子类，所以
    `except PermissionError: raise` 会把内核对 0200 文件的 EACCES 一并吞掉，
    让下面的 `O_WRONLY` 回退**永远不可达** —— 我 r8 写的那个回退就是这么废掉的。
    给判据的拒绝一个专属类型，两者才分得开。
    """


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


def open_pinned(path: str, flags: int, mode: int = 0o600, live_vault: str = "") -> int:
    """沿**物理**父路径逐级 `O_DIRECTORY|O_NOFOLLOW` 打开, 再 `openat` 叶子。

    ⛔ Codex r7 HIGH-1：`O_NOFOLLOW` **只挡末段**, 祖先目录照样被跟随。
    `.env.<vault>` 的父目录在 preflight 之后被换成指向保护区的软链时,
    `os.open(完整路径)` 会打开保护区里的同名文件, 随后 `fchmod`/`ftruncate`/写
    **全部落在保护对象上** —— 权限越界被 r6 的 `fchmod(fd)` 修掉了, 内容越界还在。

    ⛔⛔ **第一版被我自己的冒烟测试当场证伪，痕迹保留**：
    初版只做「`realpath(父目录)` 后逐级 `O_NOFOLLOW`」，理由是「合法软链已被解析掉所以
    不会误拒」。误拒确实没了，**但拦截也没了** —— 在**写入时刻**调 `realpath` 等于
    **跟着攻击者当下的那条链走**：它把要检测的那个被换掉的软链解成了目标真路径，
    于是逐级遍历一路畅通。冒烟用例 ③（`safe/sub -> prot/sub`）直接打出 "没拒"。
    教训与本卡 r5 的 `chmod` 同型：**解析/检查必须发生在「可信时刻」，不能在作用时刻现算。**

    现在的形态是两步，缺一不可：
      ① `realpath` 父目录后, **立刻用本模块的判据重新校验解析结果**（`hits()`）——
         父目录此刻若指进任何保护目标, 直接拒。这一步管「链被换到哪」。
      ② 再沿**那个已校验的物理串**逐级 `O_DIRECTORY|O_NOFOLLOW` 打开、`openat` 叶子 ——
         这一步管「校验之后到打开之间又被换」, 由内核原子拒绝。
    合法的祖先软链（macOS `/tmp -> /private/tmp`）在 ① 解析掉且不命中保护目标, 故不误拒。

    ⚠️ 如实声明：本函数关的是「祖先被换成指向**保护目标**的软链」。
    换成指向另一个**非保护**目录、或把祖先**改名/替换成真目录**仍可绕过
    （需要目录 fd 的稳定性前提或权限隔离），已登记为未闭合。

    放在本模块是为了**单一来源**：4 个调用点各抄一份遍历 = 必然漂移
    （本卡已因「两份手抄清单」栽过一次），且 ① 要用的判据就在本模块里。
    """
    leaf = os.path.basename(path)
    if not leaf:
        raise ValueError(f"open_pinned 需要一个叶子名, 收到: {path!r}")
    parent = os.path.realpath(os.path.dirname(path) or os.sep)
    # ① **原路径**与**解析后的父目录**都要过判据 —— 缺一不可：
    #    · 只判 parent（我 r7 的做法）会**丢掉 walker 的沿链保护**（Codex r8 HIGH-1）：
    #      `safe/sub -> repo/.git -> external/meta` 解析后 parent 只剩 `external/meta`,
    #      既不在固定目标里、也不再含 `.git` ⇒ 放行, 而原来的 `hits(原路径)` 会拒。
    #      这是本卡第 6 次「改判据形状 = 删掉一条已有规则」, 故这里**只加不换**。
    #    · 只判原路径则漏掉「解析后落进保护目标」那一轴（r7 HIGH-1 本身）。
    targets, claude_prefixes, enumerate_failed = build_targets(live_vault or _default_live())
    why = hits(path, targets, claude_prefixes, skip_env_name=True) or hits(
        parent, targets, claude_prefixes, skip_env_name=True
    )
    if why is None and enumerate_failed:
        why = "无法枚举 HOME, fail-closed"
    if why is not None:
        raise ForbiddenPath(f"父目录解析后落在禁写面({why}): {path} -> {parent}")
    # ② 沿已校验的物理串逐级 O_NOFOLLOW —— 校验之后再被换掉的那一级由内核拒。
    dirfd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for seg in parent.split(os.sep):
            if not seg:
                continue
            nxt = os.open(seg, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nxt
        return os.open(leaf, flags | os.O_NOFOLLOW, mode, dir_fd=dirfd)
    finally:
        os.close(dirfd)


def _default_live() -> str:
    """`live_vault` 缺省来源：与 deploy-vault.sh 的 `CLS_LIVE_VAULT` 同一口径。

    缺省值刻意取**主仓 canvas-vault**（与脚本头注一致）。取不到就给一个不存在的路径,
    让 `chain_resolvable` 走 FileNotFoundError 放行分支 —— 不因为环境变量缺失而恒拒。
    """
    return os.environ.get("CLS_LIVE_VAULT", "") or os.path.join(
        os.path.expanduser("~"), "Desktop/canvas/canvas-learning-system/canvas-vault"
    )


def chmod_pinned(path: str, mode: int = 0o600, live_vault: str = "") -> None:
    """在同一个 pinned fd 上改权限 —— 替代路径式 `chmod`（Codex r7 HIGH-1 同族）。

    路径式 `chmod` 每次都重新解析路径, 末段被换成软链时会改到**软链目标**的权限。
    这里先按 `open_pinned` 拿到已确认的 fd, 再 `fchmod` —— 检查与作用落在同一句柄。
    """
    # ⛔ 必须与 B4 写入同律地挡硬链接（Codex r8 HIGH-3，旧裸 chmod 也有此洞）：
    #    叶子被换成保护文件的**硬链接**时 `O_NOFOLLOW` 照常打开, 直接 fchmod 就改了共享 inode。
    # ⛔ 且必须限定**普通文件**（r8 MEDIUM-2）：FIFO 会让 open 阻塞（故加 O_NONBLOCK）,
    #    目录被 chmod 成 0600 会丢搜索权限。
    # ⚠️ 0200（只写不可读）的既存文件用 O_RDONLY 打不开（r8 MEDIUM-1）⇒ EACCES 时退到 O_WRONLY。
    try:
        fd = open_pinned(path, os.O_RDONLY | os.O_NONBLOCK, live_vault=live_vault)
    except ForbiddenPath:
        raise  # 判据自己的拒绝：永不回退
    except OSError as e:
        # 只有**内核**的 EACCES 才回退（0200 只写文件）。ForbiddenPath 已在上面拦掉,
        # 所以这里不会把判据的拒绝误当成权限问题（r9 MEDIUM-1 修正）。
        if e.errno != errno.EACCES:
            raise
        fd = open_pinned(path, os.O_WRONLY | os.O_NONBLOCK, live_vault=live_vault)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(f"chmod_pinned 只对普通文件生效, 实际类型 {stat.S_IFMT(st.st_mode):#o}: {path}")
        if st.st_nlink > 1:
            raise OSError(f"{path} 有 {st.st_nlink} 个硬链接, 改权限会改共享 inode")
        os.fchmod(fd, mode)
    finally:
        os.close(fd)


def write_all(fd: int, data: bytes) -> None:
    """循环写直到全部落盘 —— `os.write` 可能**短写**（Codex r8 HIGH-4）。

    空间不足 / 文件大小限制时 `os.write` 返回值小于请求长度，而文件**已被截断**；
    忽略返回值等于把「只写了一半」当成功，后面的 `fsync` 也证明不了完整。
    旧的缓冲文本写入本来自带这个保障，换成裸 `os.write` 时被丢掉了 ——
    「换成更底层的实现」总会丢掉高层替你做的事。

    放在本模块与 `open_pinned` 同理：两个 heredoc 各抄一份 = 必然漂移（本卡栽过）。
    """
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        if n <= 0:
            raise OSError(f"短写: 还剩 {len(view)} 字节未写入")
        view = view[n:]


def under(key: str, tk: str) -> bool:
    """`key` 是否等于 `tk` 或位于其下 —— **三处比较的单一来源**。

    ⛔ Codex r6 BLOCKER-2：原来三处各手写 `key == tk or key.startswith(tk + os.sep)`。
    当保护目标解析结果是**根**（`.claude-cache -> /` 这类退化配置）时，
    `tk + os.sep` 变成 `"//"`，于是 `/safe/out` 既不等于 `/` 也不以 `//` 开头 ⇒ **全部漏拦**。
    三份手抄的比较必然一起错（本卡已登记过「两份手抄清单必然漂移」同型）。
    """
    if tk == os.sep:
        return True  # 根之下 = 全部
    return key == tk or key.startswith(tk + os.sep)


def chain_resolvable(entry: str) -> bool:
    """`entry` 的整条解析链是否**真的走得通**（Codex r6 BLOCKER-1）。

    r5 我只对第一跳做了 `readlink`。但 `.claude-cache -> /opaque/hop -> /external/protected`
    且 `/opaque` 不可搜索时：第一跳 `readlink` 成功，`realpath(strict=False)` 却把 EACCES
    吞掉、只登记到 `/opaque/hop`，`enumerate_failed` 仍是 False ⇒ 直接写
    `/external/protected/x` 被放行。**「第一跳可读」不等于「整条链可解析」。**

    `os.stat` 会走完整条链，任何一段不可搜索都抛 EACCES。
    ENOENT（悬空链 / 目标暂不存在）**不算失败** —— 那是合法状态，且此时也没有
    可被写穿的真实对象；其余 OSError 一律按「问不出来」处理。
    """
    try:
        os.stat(entry)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


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
    #    ⚠️ **实测更正**（r6 变异：单独去掉本行，对应的门仍绿 ⇒ 它当前零承重）：
    #    r5 我写的「两道都要」在加入 `chain_resolvable` 之后已不成立 —— 整链检查
    #    覆盖了本行能覆盖的全部已测情形。保留它只作**早失败**的纵深（比逐条 stat 便宜），
    #    **不宣称**它是第二道防线。承重的是下面对每个目标的 `chain_resolvable`。
    #    （`os.access` 用实际 uid，root 下恒真 —— r4 LOW-1 同型，这也是它不能单独承重的原因。）
    if not os.access(home, os.R_OK | os.X_OK):
        enumerate_failed = True
    try:
        for name in sorted(os.listdir(home)):
            if name.lower().startswith(".claude"):
                entry = os.path.join(home, name)
                raw.append(entry)
                # ⛔ 不能只验第一跳（Codex r6 BLOCKER-1）：整条链都要走得通。
                if not chain_resolvable(entry):
                    enumerate_failed = True
    except OSError:
        enumerate_failed = True

    targets = []
    for r in raw:
        # ⛔ 整链可解析性要对**每一个**保护目标都验, 不只是 `.claude*`（r6 变异测量的结论）：
        #    `k()` 内的 `realpath(strict=False)` 对所有目标都会吞掉 EACCES。若 `~/.codex`
        #    本身是指向外部的软链而 HOME 不可搜索, 它就只会以**词法**路径入表 ——
        #    指向那个外部真实目标的写入随即漏拦。原来只对 `.claude*` 验, 其余目标同病未治。
        if not chain_resolvable(r):
            enumerate_failed = True
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


def walk_visited(p: str, limit: int = 64) -> tuple[list[str], bool]:
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
    # 根本身也要登记（Codex r6 BLOCKER-2 的第二半：目标解析成 `/` 时 walker 从不记录根）。
    visited: list[str] = [os.sep]
    hops = 0
    while pending:
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
        # ⛔ 上限计的是**软链跳数**, 不是处理过的段数（Codex r6 MEDIUM-1）：
        #    r5 我把 `steps += 1` 放在循环顶端, 于是 `"/" + "./"*256 + "safe/out"`
        #    这种**没有任何软链的合法浅路径**也会撞上限 ⇒ 误拦。
        #    只有解链才可能不收敛（环），普通段只会让 pending 变短、必然终止,
        #    所以把预算花在跳数上既够用又不误伤。上限对齐 POSIX SYMLOOP_MAX 量级。
        hops += 1
        if hops > limit:
            # 超限**不静默 break**：静默停下等于对剩余部分宣称「安全」, 而我们并不知道。
            return visited, True
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
            if under(hop_key, tk):
                return f"{orig}（遍历途中经过 {hop}）"
        for pfx in claude_prefixes:
            if hop_key.startswith(pfx):
                return f"{pfx}*（遍历途中经过 {hop}）"
    if truncated:
        return "遍历跳数超过上限（疑似环或深链）, 无从断言安全 ⇒ fail-closed"
    return None


def ancestor_symlink_hits(p: str, targets: list[tuple[str, str]], claude_prefixes: list[str]) -> str | None:
    """规则 5：路径中任何一段是软链且解开后落在保护目标里。

    ⛔ **如实声明：本函数在现有用例下零承重**（r6 探针实测 —— 停用它整份测试全绿）。

    经过：r5 我让本函数也转调 `chain_hits`, 变异显示「删掉 `hits()` 的逐段判据」门仍绿；
    我据此拆开职责（本函数只留 `k(cur)` 的整体 realpath 轴）并**宣称两轴各自承重**。
    Codex r6 MEDIUM-5 指出那七条变异里没有一条失效过本函数, 该宣称无据。
    r6 探针照做, 结论是**全绿** ⇒ 逐段 walker 已覆盖它能覆盖的全部已测情形。

    保留它是纵深（`k(cur)` 一次解到底与逐段解析是两种计算, 遇 walker 跳数超限或
    `readlink` 退化时理论上还能补一手），但**不得再宣称是第二道防线** ——
    r4 已因「留着让人以为有两道防线」批过一次，这次用测量说话而不是用注释说话。
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
                if under(resolved, tk):
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
        if under(key, tk):
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
        # ⛔ 根路径入口漏检（Codex r7 MEDIUM-2）：`/`、`////`、`/./` 的逐段列表是**空的**,
        #    于是下面的循环一次都不跑、直接落到 `OK` —— 即便保护目标已解析成根。
        #    空列表不代表「没有写入面」, 而代表「写入面就是根本身」。
        if why is None and not segs:
            segs = [os.sep]
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
