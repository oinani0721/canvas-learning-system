"""CARD-G3-7-R2 (BATCH-2026-09-07-第十三批): mastery 侧 FSRS 投影化写边界门。

锁三件事:

  ① 锚点门 —— mastery_engine.py / mastery_store.py 源码里「非 FSRS 调度真相源」
     这句标注不得被后人顺手删掉。
  ② 写边界静态门 (AST 数写操作, 不是 grep 字面量) —— 这两个模块内不存在任何
     文件系统写操作 (直接调用 / 回调式引用 / 写模式 open 三种形态);
     另加 ②-b: `fsrs_card_states` 这个名字只能出现在说明文字里, 不得出现在
     可执行代码中 (**不是**计数门 —— 计数会被合法的文字改动推翻)。
  ③ 行为门 —— 真跑一次 `MasteryEngine._fsrs_update`, 断言 review 那份投影文件
     `review_service._CARD_STATES_FILE` **仍不存在**: mastery 的推进不落到
     review 的投影里。

⚠️ 本门**只禁写, 不禁读**。读 frontmatter 是 D0 修订 T1 要求的溯源方向
(所有视图最终溯源节点 .md 的 frontmatter); 把读也禁掉等于把缺陷钉成规格。
门 ② 为此带一条验伪锚: 禁用名单与读 API 名单若发生交集, 本门自己变红。

⚠️ 本门**不**证明 mastery 域的 FSRS 与 frontmatter 不漂移。它锁的是
「不落到 review 那份投影」这一条边界; 两份状态仍可任意分叉 —— 隔离不等于无害。
"""

import ast
import inspect
from pathlib import Path

import pytest

import app.services.mastery_engine as mastery_engine_module
import app.services.mastery_store as mastery_store_module
import app.services.review_service as rs_module
from app.models.mastery_state import ConceptState
from app.services.mastery_engine import MasteryEngine

# 本门覆盖的两个模块。用 inspect 取路径而不是手写相对路径 —— 硬编码路径会随
# 生产改名静默失效, 让「必须命中」的门变成假绿。
TARGET_MODULES = {
    "mastery_engine.py": Path(inspect.getfile(mastery_engine_module)),
    "mastery_store.py": Path(inspect.getfile(mastery_store_module)),
}

ANCHOR = "非 FSRS 调度真相源"

# ── 门 ② 的名单 ────────────────────────────────────────────────────────────
# 目标路径在静态上不可解析 —— 路径可以是运行期拼出来的, 所以「写到 .md 还是写到
# 别处」判不了。本门因此断言一个**更强**的不变量: 这两个模块根本不做文件写。
# 这对它们成立且有实义: engine 只算, store 只写 Neo4j, 两者都不该碰盘。
#
# ⚠️ 名字必须分两档 (Codex round-1 MEDIUM-2)。早前一档写法把 `replace` / `copy` /
# `remove` / `write` 直接拉黑, 于是 `"a".replace(...)`、`dict.copy()`、`list.remove()`
# 这些与文件系统毫无关系的调用都会被判成写 —— 一道**只该禁写**的门于是开始误拦
# 普通代码, 后人只能靠把名字从名单里删掉来过门, 那等于把门拆了。

# 第一档 —— 无歧义: 这些名字在标准库里只属于文件系统 API, 见到即算写。
UNAMBIGUOUS_FS_WRITES = frozenset(
    {
        "write_text",
        "write_bytes",
        "writelines",
        "mkdir",
        "makedirs",
        "touch",
        "unlink",
        "rmdir",
        "rmtree",
        "copyfile",
        "copy2",
        "copytree",
        "copyfileobj",
    }
)

# 第二档 —— 有歧义: str/list/dict 上也有同名方法, 只看名字必然误报。
# 只有当它挂在一个**看起来是文件系统**的接收者上时才算写 (见 _receiver_is_filesystem)。
AMBIGUOUS_FS_WRITES = frozenset(
    {
        "write",
        "dump",  # json.dump(obj, fp) 写文件; json.dumps 只产字符串
        "remove",
        "rename",
        "replace",
        "copy",
        "move",
    }
)

# 有歧义的名字挂在这些模块上 = 文件写
FS_MODULE_NAMES = frozenset({"os", "shutil", "json", "pickle", "yaml", "shelve"})

# 接收者名字里出现这些片段 = 当作文件系统对象 (如 _CARD_STATES_FILE.write_text)
FS_RECEIVER_HINTS = ("path", "file", "dir", "fp", "fh")

# 读 API: 明确**允许**。本名单只用于门 ② 的验伪锚 —— 它与禁用名单必须无交集。
ALLOWED_READ_CALLS = frozenset(
    {
        "read_text",
        "read_bytes",
        "readlines",
        "read",
        "load",  # json.load
        "loads",
        "exists",
        "is_file",
        "is_dir",
        "glob",
        "rglob",
        "iterdir",
        "stat",
    }
)

_WRITE_MODE_CHARS = frozenset("wax+")


def _call_name(node: ast.Call) -> str | None:
    """取调用名: `a.b.c(...)` → 'c'; `f(...)` → 'f'; 其余 → None。"""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _open_is_write(node: ast.Call) -> bool:
    """`open(...)` 是否以写模式打开。

    ⚠️ mode 的位置取决于调用形态, 共**四种** (Codex r1 MEDIUM-2 + r2 MEDIUM-1
    + r3 MEDIUM-1 三轮补):
      · 内建 `open(path, mode)`            —— func 是 Name, mode = args[1];
      · 模块函数 `io.open(path, mode)`     —— func 是 Attribute 但接收者是
        **模块名** (io/builtins), mode 仍是 args[1];
      · 绑定方法 `Path(p).open(mode)`      —— func 是 Attribute 且接收者是
        表达式 (如 Call), mode = args[0];
      · 低层 `os.open(path, flags)`        —— 接收者是 os 模块但**语义不同**:
        第二参数是整数位掩码 flags (O_WRONLY/O_RDWR/O_APPEND/O_CREAT/O_TRUNC
        任一出现即写), 不是文本模式串。r3 版把 os.open 套了文本模式逻辑,
        `os.open(p, flags=os.O_WRONLY | os.O_CREAT)` 找不到字符串 mode 被
        当默认只读**放行** —— 新增漏报。
    r1 版一律取 args[1] ⇒ `Path(p).open("w")` 漏报; r2 版把所有 Attribute 当
    绑定方法 ⇒ 常量路径的 `io.open("notes.md", "w")` 漏报 (变量路径 p 非字符串
    常量会 fail-closed 报写, 所以 r2 的洞只在**字符串常量路径**上); r3 版修
    io.open 又漏了 os.open 的 flags 语义。本版四分。

    fail-closed: 文本形态下 mode 不是字面字符串时按**写**处理 —— 一个静态
    判不出模式的 open() 正是边界门最该拦下的形态。这条是**刻意的从严**, 代价
    是 `mode = "r"; open(p, mode)` 这种动态只读会被误拦; 真遇到时应当细化本
    函数, 而不是把 open 从名单里删掉。
    """
    func = node.func
    if isinstance(func, ast.Name):
        mode_index = 1  # 内建 open(path, mode)
    elif isinstance(func, ast.Attribute):
        recv = func.value
        recv_is_module = isinstance(recv, ast.Name) and recv.id in ("io", "builtins", "os")
        if recv_is_module and isinstance(func.ctx, ast.Load) and getattr(func, "attr", "") == "open":
            if isinstance(recv, ast.Name) and recv.id == "os":
                return _os_open_is_write(node)  # flags 语义, 单独判
            mode_index = 1  # io.open / builtins.open(path, mode)
        else:
            mode_index = 0  # 绑定方法 Path(p).open(mode)
    else:
        return True  # 罕见形态 (下标取函数等) —— 按写处理, fail-closed
    mode = node.args[mode_index] if len(node.args) > mode_index else None
    for kw in node.keywords:
        if kw.arg == "mode":
            mode = kw.value
    if mode is None:
        return False  # open(path) / Path(p).open() → 默认只读, 允许
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return bool(_WRITE_MODE_CHARS & set(mode.value))
    return True


# os.open 的写 flags 位 (O_RDONLY=0 只读; 其余打开/创建形态都算写)
_OS_OPEN_WRITE_FLAGS = frozenset({"O_WRONLY", "O_RDWR", "O_APPEND", "O_CREAT", "O_TRUNC", "O_TEMPORARY"})
# os.open 全部已知 flags 名 (含只读/附加位)。名单外的名字 = 未知来源 ⇒
# fail-closed 按写 (r4 MEDIUM-1)。平台相关位尽量列全; 真遇到落单的平台
# flag 被误报时, 把它加进名单即可 —— 方向是「宁可误报写」, 不放行未知。
_OS_OPEN_KNOWN_FLAGS = _OS_OPEN_WRITE_FLAGS | frozenset(
    {
        "O_RDONLY",
        "O_EXCL",
        "O_NONBLOCK",
        "O_NDELAY",
        "O_SYNC",
        "O_DSYNC",
        "O_RSYNC",
        "O_NOFOLLOW",
        "O_CLOEXEC",
        "O_BINARY",
        "O_TEXT",
        "O_INHERIT",
        "O_NOINHERIT",
        "O_SHORT_LIVED",
        "O_RANDOM",
        "O_SEQUENTIAL",
        "O_LARGEFILE",
        "O_ASYNC",
    }
)


def _os_open_is_write(node: ast.Call) -> bool:
    """`os.open(path, flags)` 按整数位掩码 flags 判写 (Codex r3 MEDIUM-1,
    r4 MEDIUM-1 修正 fail-closed 方向)。

    flags 出现在第二位置参数或 `flags=` 关键字。位或表达式 `os.O_WRONLY |
    os.O_CREAT` 逐段抽名字检查。判定:
      · 命中任一**写** flag → 写;
      · 每个片段都是已知 flag 名且无写位 (纯 O_RDONLY 族) → 只读放行;
      · 出现名单外的名字 (变量等) 或解析不出名字 (调用/常量等非名字形态)
        → **写** (fail-closed)。r4 版用 `not names` 兜底, 于是 `flags =
        os.O_WRONLY; os.open(p, flags)` 的 names={"flags"} 非空却全未知,
        被误放行 —— 与本函数声明的 fail-closed 相反; 本版只有「全部已知
        且无写位」才放行。
    flags 是 os.open 的**必填**参数 (Codex r4 LOW-3: 缺省是 TypeError,
    不存在「缺省=只读」语义); 缺 flags 时本函数返回 False 仅表示「静态上
    不报写」, 该调用本身无效, 矩阵注释已注明。
    """
    flags = node.args[1] if len(node.args) > 1 else None
    for kw in node.keywords:
        if kw.arg == "flags":
            flags = kw.value
    if flags is None:
        return False  # 无效调用 (flags 必填) —— 不报写, 见 docstring
    names: set[str] = set()
    unparsed = False

    def _collect(n: ast.expr) -> None:
        # r4 MEDIUM-1 第二反例: 必须保留「子表达式无法解析」的状态 ——
        # `os.O_RDONLY | get_flags()` 若只把 O_RDONLY 收进 names 而丢弃
        # 调用片段, 就会在「全部已知」的假象下放行。
        nonlocal unparsed
        if isinstance(n, ast.Attribute):
            names.add(n.attr)
        elif isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, ast.BinOp):
            _collect(n.left)
            _collect(n.right)
        else:
            unparsed = True  # 调用/常量/下标等 —— 解析不完整

    _collect(flags)
    if names & _OS_OPEN_WRITE_FLAGS:
        return True
    # 放行仅当: 无未解析片段 且 收到的名字全部已知 且 无写位。任一不满足 ⇒ 写
    return not (not unparsed and names and names <= _OS_OPEN_KNOWN_FLAGS)


def _receiver_is_filesystem(func: ast.Attribute) -> bool:
    """有歧义的名字, 其接收者是否看起来是文件系统对象/模块。"""
    recv = func.value
    if isinstance(recv, ast.Name):
        if recv.id in FS_MODULE_NAMES:
            return True
        low = recv.id.lower()
        return any(h in low for h in FS_RECEIVER_HINTS)
    if isinstance(recv, ast.Attribute):
        low = recv.attr.lower()
        if recv.attr in FS_MODULE_NAMES or any(h in low for h in FS_RECEIVER_HINTS):
            return True
        # os.path.<x> 这类两级模块引用
        return isinstance(recv.value, ast.Name) and recv.value.id in FS_MODULE_NAMES
    if isinstance(recv, ast.Call):
        # Path(p).replace(q) —— 构造出来的路径对象
        inner = recv.func
        name = inner.attr if isinstance(inner, ast.Attribute) else getattr(inner, "id", "")
        return name in ("Path", "PurePath", "PosixPath", "WindowsPath")
    return False


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """收集全部 docstring 常量节点的 id —— 它们是说明文字, 不是引用。"""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            ids.add(id(first.value))
    return ids


def _needle_in_executable_code(source: str, needle: str) -> list[str]:
    """`needle` 在**可执行代码**里的出现处 (docstring 与注释不算)。

    注释根本不进 AST, 所以天然被排除; docstring 是 AST 里的常量, 逐个认出来剔掉。
    剩下命中的只可能是: 真的字符串引用、标识符、属性名。
    """
    tree = ast.parse(source)
    docstrings = _docstring_node_ids(tree)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstrings:
                continue
            if needle in node.value:
                hits.append(f"str-literal@L{node.lineno}")
        elif isinstance(node, ast.Name) and needle in node.id:
            hits.append(f"name:{node.id}@L{node.lineno}")
        elif isinstance(node, ast.Attribute) and needle in node.attr:
            hits.append(f"attr:{node.attr}@L{node.lineno}")
    return hits


def _imported_fs_writers(tree: ast.AST) -> set[str]:
    """`from os import replace` / `from shutil import copyfileobj` 一类导入的名字。

    r2 整改版把 `from os import replace; replace(a, b)` 归入「import 别名盲区」——
    归类错了: 这不是别名 (别名是 `as r`), 是**直接导入**, AST 完全可见
    (Codex r2 MEDIUM-2)。本函数把 FS 模块里属于两档名单的名字记下来,
    之后按 Name 调用即命中。
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None:
            continue
        # "os.path" → 取顶层 "os" 判模块归属
        top = node.module.split(".")[0]
        if top not in FS_MODULE_NAMES:
            continue
        for alias in node.names:
            if alias.name in UNAMBIGUOUS_FS_WRITES or alias.name in AMBIGUOUS_FS_WRITES:
                names.add(alias.asname or alias.name)
    return names


def _find_write_calls(source: str) -> list[str]:
    """返回源码里全部文件写操作, 形如 ['write_text@L120', 'open(write-mode)@L88']。

    覆盖的形态 (Codex r1 MEDIUM-2 + r2 MEDIUM-1/2 两轮补全):
      1. 直接调用 `p.write_text(x)` / `os.replace(a, b)` / `open(p, "w")`;
      2. **回调式**引用 `asyncio.to_thread(p.write_text, data)` —— 名字被当值
         传走, 语法上不是 Call。生产的真实持久化通道 `_save_card_states` 用的
         正是这个形态, 只查 Call 会整条漏掉。r2 整改版只扫第一档的名字,
         `to_thread(os.replace, a, b)` 仍漏 —— 本版两档都扫 (第二档需接收者
         判 filesystem);
      3. 有歧义的名字只在接收者像文件系统时才算 (AMBIGUOUS_FS_WRITES);
      4. `from os import replace` 后的裸 Name 调用 (r2 MEDIUM-2)。

    已知从严面 (fail-closed 方向, 登记不修):
      · 变量名含 file/path/dir 等片段的**非文件对象**调用 `.replace()/.copy()`
        会误拦 (如 `file_text = p.read_text(); file_text.replace(a, b)`) ——
        赋值追踪超出本门复杂度预算, 宁可误拦逼人看一眼;
      · `shutil.copyfileobj(buf1, buf2)` 操作两个 BytesIO 是内存复制, 静态
        判不了参数类型, 会被报为写 —— copyfileobj 确实也能写真文件。
    """
    tree = ast.parse(source)
    found: list[str] = []
    called_attr_nodes: set[int] = set()
    called_name_nodes: set[int] = set()
    imported_writers = _imported_fs_writers(tree)
    write_names = UNAMBIGUOUS_FS_WRITES | AMBIGUOUS_FS_WRITES

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            called_attr_nodes.add(id(node.func))
        elif isinstance(node.func, ast.Name):
            called_name_nodes.add(id(node.func))
        name = _call_name(node)
        if name is None:
            continue
        if isinstance(node.func, ast.Name) and name in imported_writers:
            # 导入表必须**最先**查 (r4 MEDIUM-2: r3 版把它放在 open 特判
            # 之后, `from shutil import copyfile as open` 的 open('a','b')
            # 被文本 open 逻辑抢先把第二路径当 mode 放行, 导入表记录了却
            # 轮不到查询)。r3 MEDIUM-2 的别名 r/cp 漏报也在此修——调用名是
            # **别名或原名**, 必须先查导入表再查原名单。
            found.append(f"{name}(imported)@L{node.lineno}")
            continue
        if name == "open":
            if _open_is_write(node):
                found.append(f"open(write-mode)@L{node.lineno}")
            continue
        if name in UNAMBIGUOUS_FS_WRITES:
            found.append(f"{name}@L{node.lineno}")
            continue
        if name in AMBIGUOUS_FS_WRITES:
            if isinstance(node.func, ast.Attribute) and _receiver_is_filesystem(node.func):
                found.append(f"{name}@L{node.lineno}")

    # 形态 2: 没有被调用、只是被当值传走的写方法引用 (两档都扫)。
    # r3 MEDIUM-2: 裸名 (`from os import replace; asyncio.to_thread(replace, a,
    # b)`) 也是回调形态 —— 只查 Attribute 会漏, Name 且在导入表里同样算。
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in write_names:
            if id(node) in called_attr_nodes:
                continue
            if node.attr in UNAMBIGUOUS_FS_WRITES or _receiver_is_filesystem(node):
                found.append(f"{node.attr}(callback-ref)@L{node.lineno}")
        elif isinstance(node, ast.Name) and node.id in imported_writers:
            if id(node) not in called_name_nodes:
                found.append(f"{node.id}(callback-ref)@L{node.lineno}")
    return found


# ── 门 ① 锚点 ──────────────────────────────────────────────────────────────


def test_projection_anchor_present_in_both_modules():
    """门 ①: 两个模块的源码各含「非 FSRS 调度真相源」标注 ≥1 次。

    这条注释是后人读到 `concept.fsrs_*` 时唯一的现场提示——它说明这些字段是
    投影不是调度真相源。顺手删掉它不会打红任何功能测试, 所以要有一道门盯着。
    """
    missing = []
    for label, path in TARGET_MODULES.items():
        text = path.read_text("utf-8")
        count = text.count(ANCHOR)
        if count < 1:
            missing.append(f"{label} (path={path}, count={count})")
    assert not missing, (
        f"门 ①: 以下模块缺少投影化标注锚点「{ANCHOR}」: {missing}。"
        " CARD-G3-7-R2 加的这条注释不得被删——它是现场唯一说明"
        " concept.fsrs_* 不是调度真相源的地方。"
    )


# ── 门 ② 写边界 (AST) ──────────────────────────────────────────────────────


def test_write_call_checker_is_not_vacuous():
    """门 ② 的验伪锚 + 正控, 三条缺一不可。

    1. 禁用名单与读 API 名单**无交集** —— 本门只禁写不禁读; 若有人把 read_text
       之类塞进禁用名单, 这条立刻变红 (D0 修订 T1: 禁读 = 把缺陷钉成规格)。
    2. 检查器对**确实在写**的源码必须报出来 (正控) —— 否则门 ② 的「零命中」
       只是检查器坏掉。
    3. 检查器对**只读**的源码必须不报 (负控) —— 否则它宽到无意义。
    """
    overlap = (UNAMBIGUOUS_FS_WRITES | AMBIGUOUS_FS_WRITES) & ALLOWED_READ_CALLS
    assert not overlap, (
        f"禁用名单侵入了读 API: {sorted(overlap)}。本门只禁写不禁读；"
        " 禁读会把「backend 不许溯源 frontmatter」这个缺陷写成规格。"
    )

    # 判据矩阵。含四轮反例, 各轮错向如实记 (r3 LOW-5 更正: r2 的 io.open 洞
    # 只在**字符串常量路径**上——变量路径 p 非字符串常量会 fail-closed 报写,
    # 所以矩阵必须用常量路径才能锁住那个回退):
    #   r1 版错: 绑定 open 写(漏)/读带 buffering(误)/字符串 replace(误)/回调式写(漏);
    #   r2 版错: io.open("notes.md","w")(漏, 常量路径)/io.open("card.md","r")(误);
    #   r3 版错: os.open flags(漏)/导入别名(漏)/裸名回调(漏);
    #   内建 open 两行各版都对, 留作回归保护。
    cases: list[tuple[str, str, bool]] = [
        # (标签, 源码片段, 期望是否命中)
        ("内建 open 写", "open(p, 'w')", True),
        ("内建 open 读", "open(p)", False),
        ("绑定 open 写", "Path(p).open('w')", True),  # ← r1 版漏报
        ("绑定 open 读带 buffering", "Path(p).open('r', -1)", False),  # ← r1 版误报
        ("io.open 常量路径写", "io.open('notes.md', 'w')", True),  # ← r2 版漏报(常量路径才是真反例)
        ("io.open 常量路径读", "io.open('card.md', 'r')", False),  # ← r2 版误报(文件名含 a)
        ("io.open 变量路径写", "io.open(p, 'w')", True),
        ("builtins.open 常量路径写", "builtins.open('notes.md', 'w')", True),
        ("os.open flags 位掩码写", "os.open(p, flags=os.O_WRONLY | os.O_CREAT)", True),  # ← r3 版漏报
        (
            "os.open 缺 flags 无效调用",
            "os.open(p)",
            False,
        ),  # flags 必填, 缺省 TypeError (r4 LOW-3); 本项仅证检查器不报写
        ("os.open O_RDONLY 只读", "os.open(p, os.O_RDONLY)", False),
        ("os.open 未知变量 flags", "flags = os.O_WRONLY\n    os.open(p, flags)", True),  # ← r4 版 fail-closed 反向放行
        ("os.open 混合未知调用", "os.open(p, os.O_RDONLY | get_flags())", True),  # ← r4 版丢弃未知调用后放行
        (
            "as open 导入劫持写",
            "from shutil import copyfile as open\n    open('a.md', 'b.md')",
            True,
        ),  # ← r4 版 open 特判先于导入表
        ("字符串 replace", "s.replace('a', 'b')", False),  # ← r1 版误报
        ("字典 copy", "d.copy()", False),  # ← r1 版误报
        ("列表 remove", "items.remove(x)", False),  # ← r1 版误报
        ("os.replace 真改名", "os.replace(a, b)", True),
        ("shutil.move 真移动", "shutil.move(a, b)", True),
        ("json.dump 写文件", "json.dump(obj, fh)", True),
        ("json.dumps 只产字符串", "json.dumps(obj)", False),
        ("Path 对象 write_text", "Path(p).write_text('x')", True),
        ("回调式写", "asyncio.to_thread(Path(p).write_text, data)", True),  # ← r1 版漏报
        ("回调式二档写", "asyncio.to_thread(os.replace, a, b)", True),  # ← r2 版漏报
        ("from-import 裸名写", "from os import replace\n    replace(a, b)", True),  # ← r2 版漏报
        ("from-import 别名写", "from os import replace as r\n    r(a, b)", True),  # ← r3 版漏报(记录了没查询)
        ("第一档导入别名写", "from shutil import copyfile as cp\n    cp(a, b)", True),  # ← r3 版漏报
        ("裸名回调写", "from os import replace\n    asyncio.to_thread(replace, a, b)", True),  # ← r3 版漏报
        ("Path 读", "Path(p).read_text('utf-8')", False),
        ("json.load 读", "json.load(fh)", False),
        ("常量名文件对象写", "_CARD_STATES_FILE.write_text('x')", True),
    ]
    wrong = []
    for label, snippet, expect_hit in cases:
        src = f"def _z(p, s, d, items, x, a, b, obj, fh, data, os, shutil, json, Path, asyncio):\n    {snippet}\n"
        hits = _find_write_calls(src)
        if bool(hits) != expect_hit:
            wrong.append(f"{label}: {snippet!r} 期望{'命中' if expect_hit else '放行'}, 实得 {hits}")
    assert not wrong, "写检查器判据矩阵不符:\n  " + "\n  ".join(wrong)


def test_mastery_modules_contain_no_filesystem_writes():
    """门 ②: 两个 mastery 模块内不存在任何文件系统写操作。

    比卡文要求的「不写 .md / 不写 fsrs_card_states.json」更强, 理由写在模块
    常量 UNAMBIGUOUS_FS_WRITES / AMBIGUOUS_FS_WRITES 上方: 写目标的路径可以
    是运行期拼出来的, 静态判不了「写到哪」, 所以判「有没有写」。这两个模块
    本来就不该碰盘, 该不变量成立。
    """
    offenders = {}
    for label, path in TARGET_MODULES.items():
        hits = _find_write_calls(path.read_text("utf-8"))
        if hits:
            offenders[label] = hits
    assert not offenders, (
        f"门 ②: mastery 模块出现文件写调用 {offenders}。"
        " mastery 域的 concept.fsrs_* 是投影, 只应经 MasteryStore 落 Neo4j;"
        " 写盘意味着它开始自己造第二份真相源。"
    )


def test_fsrs_card_states_appears_only_as_prose_anchor():
    """门 ②-b: `fsrs_card_states` 在两个 mastery 模块里只能是**说明文字**。

    判据不是「出现几次」。计数会被合法的文字改动推翻 —— 本卡自己就撞上过:
    (g) 要求在 `_fsrs_update` 里补一句「本模块**不写** fsrs_card_states.json」,
    这句话让原本写死的 `== 1` 立刻变成 2。跟着把常数改大只是让门随注释漂移,
    门就不再承重了。

    真正要锁的不变量是: 这个名字**不得出现在可执行代码里**——不做字符串引用,
    不做标识符/属性名。也就是说 mastery 侧永远不去碰 review 那份投影文件。
    注释与 docstring 里爱写多少写多少, 那是给人看的锚点, 不是引用。
    """
    offenders = {}
    for label, path in TARGET_MODULES.items():
        hits = _needle_in_executable_code(path.read_text("utf-8"), "fsrs_card_states")
        if hits:
            offenders[label] = hits
    assert not offenders, (
        f"门 ②-b: mastery 模块在**可执行代码**里引用了 fsrs_card_states"
        f" {offenders}。mastery 域不得触碰 review_service 的那份投影;"
        f" 说明文字可以提它, 代码不行。"
    )

    # 锚点仍须在 (与门 ① 同理: 说明被整段删掉时要有人报警)。
    # ⚠️ 两个模块**同一口径**: 只查代码引用, 不查提及次数。早前这里对 store 留过
    # 一条「原文不得出现」的断言, 与上面「文字里提不算引用」直接打架 —— CARD-G3-7-R2
    # 给 store 补的投影化说明本身就要提到这个文件名, 那条断言会逼人把说明删掉。
    # 一道门内两套口径, 先红的那一个会诱导人去改判据而不是改代码。
    for label in ("mastery_engine.py", "mastery_store.py"):
        text = TARGET_MODULES[label].read_text("utf-8")
        assert "fsrs_card_states" in text, (
            f"{label} 里关于「本模块不写 fsrs_card_states.json」的说明被删光了。"
            " 这句话是现场唯一说明 mastery 侧与 review 那份投影没有关系的地方。"
        )


def test_executable_code_checker_is_not_vacuous():
    """门 ②-b 的验伪锚: 检查器必须能分开「代码里用了」和「文字里提了」。

    没有这条, `_needle_in_executable_code` 恒返回空列表也能让上面那道门全绿。
    """
    needle = "fsrs_card_states"

    prose_only = (
        '"""模块说明: 本模块不写 fsrs_card_states.json。"""\n'
        "def f():\n"
        '    """也不经 fsrs_card_states 那套。"""\n'
        "    # 注释里提 fsrs_card_states 同样不算引用\n"
        "    return 1\n"
    )
    assert _needle_in_executable_code(prose_only, needle) == [], (
        "负控失败: 检查器把 docstring/注释里的提及当成了代码引用 —— 那会逼后人删掉说明文字才能过门。"
    )

    real_uses = (
        "from pathlib import Path\n"
        "def g(cfg):\n"
        "    p = Path('data') / 'fsrs_card_states.json'\n"
        "    return cfg.fsrs_card_states, p\n"
    )
    hits = _needle_in_executable_code(real_uses, needle)
    assert len(hits) == 2, f"正控失败: 检查器应报出 2 处真实引用 (字符串常量 + 属性名), 实得 {hits}"


# ── 门 ③ 行为 ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fsrs_update_does_not_write_review_projection(tmp_path, monkeypatch, review_service_factory):
    """门 ③: `_fsrs_update` 跑完后, review 的投影文件仍不存在。

    这道门有两个前提, 都必须**在门内断言**, 否则「文件不存在」可以由完全
    无关的原因造成 (patch 没生效 / 被测方法压根没执行), 门就成了恒真的摆设:

      前提 A (正控): 被 patch 的 `_CARD_STATES_FILE` **确实**是生产写通道的
        落点 —— 先经真实通道 `_save_card_states` 写一次, 断言文件出现。
      前提 B: `_fsrs_update` **确实跑到底了** —— 断言它写出了 fsrs_card_data。
        少了这条, `fsrs_manager` 为 None 时的早退也会让门"通过"。
    """
    engine = MasteryEngine()
    if engine.fsrs_manager is None:
        pytest.skip(
            "FSRS 引擎不可用 (mastery_engine.FSRS_ENGINE_AVAILABLE=False)。"
            " 本门锁的是真实 FSRS 路径的写边界; 换成 MagicMock 替身会让"
            " 「没写文件」变成替身的属性而不是被测代码的属性, 那是假绿, 故跳过。"
        )

    # ── 前提 A: 正控 —— 证明 patch 点就是生产写通道的落点
    probe = tmp_path / "positive-control-card-states.json"
    monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", probe)
    svc = review_service_factory()
    assert await svc._save_card_states(pending=("g37r2-probe", '{"state": 1}')) is True
    assert probe.exists(), (
        "正控失败: 经真实通道 _save_card_states 写入后, 被 patch 的路径上没有"
        " 出现文件 —— 说明这个 patch 点不是生产写通道的落点, 本门后面的"
        " 「文件不存在」将毫无信息量。"
    )

    # ── 被测: 换一个全新的、此刻确实不存在的目标
    target = tmp_path / "mastery-must-not-write-here.json"
    monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", target)
    assert not target.exists(), "前置条件: 被测目标在跑之前必须不存在"

    concept = ConceptState(
        concept_id="g37r2-boundary",
        topic="fsrs-truth-source",
        name="projection boundary",
    )
    engine._fsrs_update(concept, grade=3)

    # ── 前提 B: 被测方法确实跑到底了 (不是早退)
    assert concept.fsrs_card_data is not None, (
        "_fsrs_update 没有写出 fsrs_card_data —— 它多半在 `if not"
        " self.fsrs_manager: return` 处早退了。此时「目标文件不存在」是因为"
        " 被测代码没执行, 不是因为它守住了边界。"
    )

    # ── 真正的判据
    assert not target.exists(), (
        f"门 ③: `_fsrs_update` 在 review 的投影路径上写出了文件 {target}。"
        " mastery 域的 FSRS 推进必须留在 MasteryStore (Neo4j) 侧,"
        " 不得落进 review_service 的 fsrs_card_states.json 投影。"
    )
