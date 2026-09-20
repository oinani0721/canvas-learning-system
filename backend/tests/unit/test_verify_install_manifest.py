# CARD-DEBT-10 (BATCH-2026-09-18-第十五批) — 机器级安装副本 manifest 化的裁判
#
# 被测物: scripts/verify_install_manifest.py + scripts/vault-install-manifest.json
#         的顶层 `machine_items`（6 件: 5 个 launchd plist + 1 个 wrapper 安装副本）。
# 真相源: 真实 manifest 本体（本文件不另造一份 machine_items —— 造一份就会漂）。
#
# fixture 口径（DD-03 禁 mock）: 真文件、真 plistlib、真 sha256、真子进程跑 CLI。
#   不 patch 文件系统、不 mock 哈希。整套 fixture 是 **hermetic** 的: tmp home +
#   tmp harness, 连 `com.canvas.daily-review.plist` 里那条指向真机 wrapper 的绝对
#   路径也被改写进 tmp home —— 否则测试的真值会跟着这台机器的实际状态翻转
#   （真机 wrapper 一漂, 本文件就集体变红, 那是把环境当断言）。
#
# 钉死点:
#   1. **零写（两把锁）**: ① AST 门 —— 全文件的写调用（含 os.open/os.write/chmod/
#      makedirs/replace/unlink/shutil.copy*/Path.write_*）必须全部落在
#      {_apply_reinstall, _write_report} 两个函数体内, 数的是 ast.Call 节点不是文本;
#      ② 行为门 —— `--reinstall --dry-run` 前后对 `--home` 整棵树做
#      「相对路径 + sha256 + mode + 软链目标」全量快照, 逐项相同。
#      单靠任何一把都能被绕过: AST 门看不见「调了别人写」, 快照门看不见「写在树外」。
#   2. **六类状态各自独立承重, 一次只打一类**: MATCH / DRIFT / MISSING / UNREADABLE /
#      EXTERNAL-PRESENT / EXTERNAL-MISSING, 断言「恰该 label 是该状态」而不是只断 rc
#      —— 只断 rc 的判据会被任意一类差异喂饱。
#   3. **退出码分档**: 0 全对 / 1 只缺 / 2 漂·读不动·解析不动·程序体不对（与缺并存也取 2）
#      / 3 用法错。`test_missing_alone_is_exit_1` 是「缺失语义没被 mismatch 吞掉」的
#      唯一守门人; 禁止把任何一条 rc 断言弱化成 `!= 0`。
#   4. **EXTERNAL-* 不计退出码但必须可见**: 4 件全丢仍 rc 0 —— 这是 managed:external
#      的定义（仓库不保管它的内容）, 不是漏报; 所以另钉「报告正文出现 EXTERNAL-MISSING
#      且摘要有计数与警示行」, 让它不能静默。
#   5. **program_source 按内容比不按路径比**: 已装 plist 指主干树而校验器可能跑在
#      另一棵 worktree —— 按路径比 = 恒 DRIFT 假红。同内容不同目录 ⇒ PROGRAM-MATCH;
#      指向不存在 ⇒ PROGRAM-DANGLING（计阻断）; 报告必须打出它实际指向哪棵树。
#   6. **「读不到」计阻断**: chmod 000 的安装副本 ⇒ UNREADABLE + rc 2, 不得压成
#      「没有这条数据」再当 MATCH。
#   7. **落点门**: 报告不许落进受管面（manifest 推出来的 `<home>/Library` 与
#      `<harness>/scripts`）, 违反 ⇒ rc 3 且落点不存在。判定走 resolve() 物理解析。
#   8. **幂等**: apply 之后漂移件变 MATCH、external 件 sha 一位不动、第二次计划为空。
#      真实 HOME 的 --apply 缺 --i-confirm-home-write ⇒ rc 3, 且真机 6 件 sha 不变。
#   9. **软链安装副本**: 归 UNREADABLE（读它拿到的是别处的内容）, 且永不进重装计划
#      —— apply 不会沿链写穿到别处。
#  10. **blob 等价**: 纯 Python 算的 source_blob 与真 `git hash-object` 逐字同。
#
# 本门不证明什么: 不证明真实 ~/Library 的 --apply 在真机正确（只在 tmp HOME 验;
#   真机 apply 需用户当次授权, 未授权即 SKIP）; 不证明 4 个 external plist 的语义
#   （KeepAlive / 时刻 / PATH）合理（只登记在位 + sha, 不评语义）; 不证明 launchctl
#   加载状态与清单一致（本脚本不调 launchctl）; 不证明跨机器 / 跨用户 HOME 的可移植性。
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
VERIFIER = SCRIPTS_DIR / "verify_install_manifest.py"
MANIFEST = SCRIPTS_DIR / "vault-install-manifest.json"

# 写调用口径 —— 本清单是 AST 门的全部输入面。宽于卡文 (f)④ 的最小集: 低层写原语
# （os.open / os.write / os.pwrite / os.writev / os.ftruncate / chmod 族）、shutil 的
# 全部复制与归档入口、tempfile 的四个落盘入口都在内。
# ⚠️ 名单是手写的, 天然不完备 —— 所以下面同时钉三件事, 而不是只钉名单:
#   ① 绑定形态 `p.open("w")` 的 mode 在 args[0] 而不是 args[1]（内部对抗复核实测:
#      按 args[1] 取会让 Path.open 写法整族漏报, 而这个文件到处是 Path 对象）;
#   ② `*args` / `**kwargs` 让 mode 判不出来时**保守判为写**;
#   ③ `from os import replace` / `import os as o` 这类改名一并归一化后再查名单。
WRITE_DOTTED = frozenset(
    {
        "os.open",
        "os.write",
        "os.pwrite",
        "os.writev",
        "os.fdopen",
        "os.replace",
        "os.rename",
        "os.renames",
        "os.unlink",
        "os.remove",
        "os.removedirs",
        "os.makedirs",
        "os.mkdir",
        "os.rmdir",
        "os.chmod",
        "os.fchmod",
        "os.lchmod",
        "os.chown",
        "os.fchown",
        "os.chflags",
        "os.symlink",
        "os.link",
        "os.truncate",
        "os.ftruncate",
        "os.utime",
        "os.mkfifo",
        "os.mknod",
        "os.dup2",
        "io.open",
        "io.FileIO",
        "io.BufferedWriter",
        "shutil.copy",
        "shutil.copy2",
        "shutil.copyfile",
        "shutil.copyfileobj",
        "shutil.copytree",
        "shutil.copymode",
        "shutil.copystat",
        "shutil.move",
        "shutil.rmtree",
        "shutil.make_archive",
        "shutil.unpack_archive",
        "tempfile.mkstemp",
        "tempfile.mkdtemp",
        "tempfile.TemporaryFile",
        "tempfile.NamedTemporaryFile",
        "tempfile.SpooledTemporaryFile",
        "tempfile.TemporaryDirectory",
    }
)
WRITE_METHODS = frozenset(
    {
        "write",
        "write_text",
        "write_bytes",
        "writelines",
        "mkdir",
        "rmdir",
        "unlink",
        "touch",
        "rename",
        "replace",
        "symlink_to",
        "hardlink_to",
        "chmod",
        "lchmod",
        "truncate",
    }
)
WRITE_MODE_CHARS = frozenset("wax+")
# `os.open` 是读写共用的一个入口: `O_RDONLY | O_DIRECTORY` 是读目录, 与写无关。
# 一律算写会产生假阳性（门开始报一个只读函数）, 而假阳性会逼人去放宽白名单 ——
# 那才是真正危险的后果。所以按 flags 判, 判不出来时保守算写。
OPEN_WRITE_FLAGS = frozenset({"O_CREAT", "O_WRONLY", "O_RDWR", "O_TRUNC", "O_APPEND", "O_EXCL"})
OPEN_READ_FLAGS = frozenset({"O_RDONLY", "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK", "O_NOCTTY"})
MODULES_WITH_WRITERS = frozenset({"os", "io", "shutil", "tempfile", "builtins", "pathlib"})
# 写调用只许待在这两个函数体内, 且比对的是**限定名**（`verify._write_report` 这种
# 嵌套定义不算数）—— 裸名白名单只要求「最近一层 def 恰好叫这个名字」, 在函数里再
# 定义一个同名内层函数就能骗过它。
# owner 用 `def:` / `class:` 前缀限定。裸名白名单有两个洞: ① 在 verify() 里再定义一个
# 叫 _write_report 的内层函数; ② 在模块级定义一个**类**叫 _write_report, 它体内的写
# 调用同样会被记成 owner="_write_report"（Codex r1 HIGH-1 实测）。带 kind 前缀 + 限定
# 路径之后, 只有模块级的那两个 def 才对得上。
ALLOWED_WRITE_OWNERS = frozenset({"def:_apply_reinstall", "def:_write_report"})
# verify() 的调用链里不许出现这两个写者 —— 门只查「写调用在谁体内」是**调用点**判据,
# 查不到「verify() 调了一个会写的函数」。这条是它的补集。
ZERO_WRITE_ENTRYPOINTS = ("verify", "_verify_one", "_verify_program", "plan_reinstall")


def _load_module():
    """按路径加载被测脚本。**先注册 sys.modules 再 exec** —— 协议 §3:

    Python 3.14 的 @dataclass 自省要取 sys.modules[cls.__module__].__dict__,
    不先注册则 exec_module 期 KeyError。本脚本有 @dataclass, 踩得到。
    """
    name = "_debt10_verify_install_manifest"
    spec = importlib.util.spec_from_file_location(name, VERIFIER)
    if spec is None or spec.loader is None:  # pragma: no cover — 路径错时立即失败
        raise RuntimeError(f"无法加载 {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 不往仓根 scripts/ 落 __pycache__
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:  # pragma: no cover — 加载失败不留半成品模块
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


vi = _load_module()


# ── AST 零写门（也被 §二.4 的独立判据直接 import, 一份口径两个调用方）────


def _dotted(node: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _import_aliases(tree: ast.AST) -> tuple[dict[str, str], dict[str, str]]:
    """收集改名, 让名单查询在改名之后仍然成立。

    返回 (模块别名 -> 真模块名, 裸名 -> 它代表的 dotted 名)。
    `import os as o` 后的 `o.replace(...)`、`from os import replace` 后的
    `replace(...)`，在没有这一步时都查不到名单里去。
    """
    modules: dict[str, str] = {}
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in MODULES_WITH_WRITERS:
                    modules[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                dotted = f"{node.module}.{alias.name}"
                if dotted in WRITE_DOTTED or dotted == "builtins.open":
                    names[alias.asname or alias.name] = dotted
    return modules, names


def _normalize_dotted(dotted: str, modules: dict[str, str]) -> str:
    head, _, tail = dotted.partition(".")
    return f"{modules.get(head, head)}.{tail}" if tail else dotted


def _mode_is_write(call: ast.Call, *, bound: bool) -> bool:
    """`open(...)` 的 mode 含 w/a/x/+ ⇒ 写；判不出来一律**保守判为写**。

    `bound=True` 是 `p.open(mode)` 这种绑定形态 —— 它的 mode 在 `args[0]`,
    不是内建 `open(file, mode)` 的 `args[1]`。按 args[1] 取会让
    `Path.open("w")` 整族静默漏报, 而这个被测文件从头到尾都在操作 Path 对象。
    """
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return True  # open(*args): mode 判不出来
    if any(keyword.arg is None for keyword in call.keywords):
        return True  # open(p, **opts): mode 判不出来
    index = 0 if bound else 1
    mode_node: ast.AST | None = call.args[index] if len(call.args) > index else None
    for keyword in call.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if mode_node is None:
        return False  # 没给 mode ⇒ 默认 'r'
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return bool(set(mode_node.value) & WRITE_MODE_CHARS)
    return True  # mode 不是字面量 ⇒ 保守判为写


def _os_open_is_write(call: ast.Call) -> bool:
    """`os.open(path, flags)` 只有带写位才算写。判不出来 ⇒ 保守算写。"""
    flag_node = call.args[1] if len(call.args) >= 2 else None
    for keyword in call.keywords:
        if keyword.arg == "flags":
            flag_node = keyword.value
    if flag_node is None:
        return True
    seen: set[str] = set()
    for sub in ast.walk(flag_node):
        # 只收 `O_` 开头的名字: `os.O_RDONLY` 里那个 `os` 是模块名不是 flag,
        # 把它一起收进来会让「是不是只读集合的子集」恒为 False = 恒判写。
        if isinstance(sub, ast.Attribute) and sub.attr.startswith("O_"):
            seen.add(sub.attr)
        elif isinstance(sub, ast.Name) and sub.id.startswith("O_"):
            seen.add(sub.id)
    if seen & OPEN_WRITE_FLAGS:
        return True
    return not (seen and seen <= OPEN_READ_FLAGS)


def _is_write_call(call: ast.Call, modules: dict[str, str], names: dict[str, str]) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute):
        dotted = _dotted(func)
        normalized = _normalize_dotted(dotted, modules) if dotted else None
        if normalized == "os.open":
            return _os_open_is_write(call)
        if normalized is not None and normalized in WRITE_DOTTED:
            return True
        if func.attr == "open":
            return _mode_is_write(call, bound=True)
        return func.attr in WRITE_METHODS
    if isinstance(func, ast.Name):
        # `open` 与它的别名（`from builtins import open as fopen`、`w = open`）
        # 一样要按 mode 判 —— 直接判 True 会把每一次读都报成写。
        if func.id == "open" or names.get(func.id) == "builtins.open":
            return _mode_is_write(call, bound=False)
        return func.id in names
    return False


def _call_label(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        return _dotted(func) or f"<expr>.{func.attr}"
    if isinstance(func, ast.Name):
        return func.id
    return "<expr>"  # pragma: no cover


def _walk_owned(tree: ast.AST):
    """产出 (限定 owner, 任意 ast 节点)。owner 形如 `def:f` / `class:C.def:m` / `<module>`。

    两条归属纪律:
      - owner 是**限定名且带 kind 前缀**, 所以「verify 里的内层 _write_report」与
        「模块级的类 _write_report」都对不上裸名白名单;
      - 一个 def 上除 body 以外的一切（装饰器、默认值、**kw_defaults**、注解、
        returns、type_params）都在**外层**作用域求值, 必须按外层 owner 记账 ——
        手写枚举三个子树再 `continue` 会让 kw_defaults 里的写调用整个看不见。
    """
    out: list[tuple[str, ast.AST]] = []

    def qualify(owner: str, kind: str, name: str) -> str:
        leaf = f"{kind}:{name}"
        return leaf if owner == "<module>" else f"{owner}.{leaf}"

    def walk(node: ast.AST, owner: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            for child in ast.iter_child_nodes(node):
                if child not in node.body:
                    walk(child, owner)  # 非 body 的一切在外层作用域求值
            inner = qualify(owner, kind, node.name)
            for statement in node.body:
                walk(statement, inner)
            return
        if isinstance(node, ast.Lambda):
            walk(node.args, owner)
            walk(node.body, qualify(owner, "def", "<lambda>"))
            return
        out.append((owner, node))
        for child in ast.iter_child_nodes(node):
            walk(child, owner)

    walk(tree, "<module>")
    return out


def _walk_calls(tree: ast.AST):
    """产出 (限定 owner, ast.Call)。"""
    return [(owner, node) for owner, node in _walk_owned(tree) if isinstance(node, ast.Call)]


def _variable_aliases(tree: ast.AST, modules: dict[str, str]) -> dict[str, str]:
    """`w = os.replace` 这种变量别名。只认最简单的一层, 但这一层挡住的是最现实的写法。"""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not isinstance(target, ast.Name):
            continue
        dotted = _dotted(value) if isinstance(value, ast.Attribute) else None
        if dotted and _normalize_dotted(dotted, modules) in WRITE_DOTTED:
            out[target.id] = dotted
        elif isinstance(value, ast.Name) and value.id == "open":
            out[target.id] = "builtins.open"
    return out


def collect_write_call_owners(path: Path) -> list[tuple[str, str, int]]:
    """返回 [(限定 owner, 调用名, 行号)] —— 数的是 ast.Call 节点。

    注释里写 `os.replace(...)`、字符串字面量里写 `"write_text"`、`if False:` 下的
    死分支, 都骗不过它（文本门连破三轮的教训）。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules, names = _import_aliases(tree)
    names = {**names, **_variable_aliases(tree, modules)}
    found: list[tuple[str, str, int]] = []
    for owner, call in _walk_calls(tree):
        if _is_write_call(call, modules, names):
            found.append((owner, _call_label(call), call.lineno))
    return found


def collect_call_edges(path: Path) -> dict[str, set[str]]:
    """限定 owner → 它体内**提到**的本文件顶层函数名集合。

    两处刻意过近似（宁可多连一条边, 也不漏）:
      - 只看「调用位上的裸名」会漏掉把写者**当参数传出去**和**从容器里取出来调**
        两种形态, 所以改成数任何一次 Name 引用;
      - owner 是限定名, 嵌套 def / lambda / 方法体里的引用会落在 `def:f.def:g` 这种
        更深的键上, 上游必须把它们一并算进 `f` 的出边, 否则「把写者调用藏进一个内层
        函数」就断开了整条链。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top_level = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    edges: dict[str, set[str]] = {}
    for owner, node in _walk_owned(tree):
        # 数的是**引用**不是「调用位上的裸名」: `table = {"w": _write_report}` 是一条
        # 赋值而不是调用, 只在 Call 节点里找名字就会漏掉整条路线。
        if isinstance(node, ast.Name) and node.id in top_level:
            edges.setdefault(owner, set()).add(node.id)
    return edges


def _edges_for(edges: dict[str, set[str]], name: str) -> set[str]:
    """`def:name` 自身 + 一切嵌套在它里面的 owner 的出边并集。"""
    prefix = f"def:{name}."
    out: set[str] = set(edges.get(f"def:{name}", set()))
    for key, value in edges.items():
        if key.startswith(prefix):
            out |= value
    return out


def writers_reachable_from(path: Path, entrypoint: str) -> set[str]:
    """从 `entrypoint` 出发, 沿调用图能走到的**写者**函数集合。

    ⛔ 这条是 AST 零写门的补集。那一条是**调用点**判据 —— 它查「写调用长在谁体内」,
    因此对「`verify()` 里加一行 `_write_report(...)`」完全无感: 写调用还在
    `_write_report` 体内, owner 集合一字不变, 门照绿（Codex r1 HIGH-1 实测）。
    """
    edges = collect_call_edges(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defined = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert entrypoint in defined, f"入口 {entrypoint!r} 在被测文件里不存在 —— 门会空转"
    writer_names = {owner.split(":")[-1] for owner in ALLOWED_WRITE_OWNERS}
    seen: set[str] = set()
    found: set[str] = set()
    stack = [entrypoint]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in writer_names and current != entrypoint:
            found.add(current)
        stack.extend(_edges_for(edges, current))
    return found


# ── fixture ────────────────────────────────────────────────────

LAUNCH_AGENTS = "Library/LaunchAgents"
WRAPPER_BIN = "Library/Application Support/CanvasReview/bin"


def _machine_items() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["machine_items"]


def _write(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)


def _synth_plist(label: str, program: Path) -> bytes:
    return plistlib.dumps(
        {
            "Label": label,
            "ProgramArguments": ["/bin/bash", str(program)],
            "RunAtLoad": True,
        }
    )


@pytest.fixture
def machine_env(tmp_path: Path):
    """搭一套 hermetic 的「干净机器」: tmp harness（仓内源）+ tmp home（安装副本）。

    `com.canvas.daily-review.plist` 的 ProgramArguments[1] 在 harness 侧就被改写成
    tmp home 的 wrapper 安装路径 —— 源与安装副本仍逐字节相同（MATCH）, 而程序体
    校验完全落在 tmp 树内, 不读这台机器的任何东西。
    """
    home = tmp_path / "home"
    harness = tmp_path / "harness"
    items = _machine_items()
    wrapper_install = home / WRAPPER_BIN / "daily-review-wrapper.sh"

    for item in items:
        # harness 侧: 仓内源 + 程序体
        if item["source"] is not None:
            payload = (REPO_ROOT / item["source"]).read_bytes()
            if item["source"].endswith("com.canvas.daily-review.plist"):
                parsed = plistlib.loads(payload)
                parsed["ProgramArguments"][1] = str(wrapper_install)
                payload = plistlib.dumps(parsed)
            _write(harness / item["source"], payload)
        if item.get("program_source"):
            _write(
                harness / item["program_source"],
                (REPO_ROOT / item["program_source"]).read_bytes(),
                0o755,
            )

    for item in items:
        install = home / item["install"][2:]
        if item["source"] is not None:
            source_bytes = (harness / item["source"]).read_bytes()
            _write(install, source_bytes, 0o755 if item["role"] == "launchd-wrapper" else 0o644)
        else:
            _write(install, _synth_plist(item["label"], harness / item["program_source"]))

    return {"home": home, "harness": harness, "items": items}


def _run(
    env: dict,
    *args: str,
    report: Path | None = None,
    home_arg: str | None = None,
    child_home: Path | None = None,
) -> subprocess.CompletedProcess:
    """跑一次 CLI。

    `home_arg` 覆盖传给 `--home` 的**拼法**（用来喂别名拼法, 内容仍是同一个目录）;
    `child_home` 设子进程的 `HOME` 环境变量 —— `Path.home()` 读的就是它, 所以这是
    在**完全 hermetic 的 tmp 树里**让「--home 就是真实 HOME」这个分支真正生效的办法,
    不必拿真机的 ~/Library 当靶子。
    """
    argv = [
        sys.executable,
        str(VERIFIER),
        "--home",
        home_arg if home_arg is not None else str(env["home"]),
        "--harness",
        str(env["harness"]),
        *args,
    ]
    if report is not None:
        argv += ["--report", str(report)]
    child_env = dict(os.environ)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if child_home is not None:
        child_env["HOME"] = str(child_home)
    return subprocess.run(argv, capture_output=True, text=True, env=child_env)


def _statuses(stdout: str) -> dict[str, str]:
    """报告正文 → {label: status}。

    ⛔ 解析不到任何一条就当场炸, 不返回空字典 —— 否则「报告格式变了/进程根本没跑起来」
    会让 `_statuses(a) == _statuses(b)` 这类断言退化成 `{} == {}` 恒真。
    """
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        if line.startswith("- label="):
            fields = dict(part.split("=", 1) for part in line[2:].split(" ") if "=" in part)
            out[fields["label"]] = fields["status"]
    assert out, f"报告里一条 label 都没解析到 —— 判据输入面为空, 作废。stdout={stdout[:400]!r}"
    return out


def _lines(stdout: str) -> list[str]:
    """按**整行**取, 给需要精确匹配的断言用。

    子串断言挡不住包含关系: `"PLAN 空"` 同时被 `"PLAN 空（…）"` 与
    `"POST-PLAN 空（…）"` 满足, `"EXTERNAL-MISSING=4"` 是 `"⚠️ EXTERNAL-MISSING=4"`
    的子串 —— 两条断言看着独立, 其实是同一条。
    """
    return [line.rstrip() for line in stdout.splitlines()]


def _program_rules(stdout: str) -> dict[str, str]:
    """label → program_rule。按**整个词**取。

    `program_rule=Program` 是 `program_rule=ProgramArguments[0]` 的前缀, 子串断言
    会被后者满足 —— 「Program 键被忽略」这条回归因此照样绿。
    """
    out: dict[str, str] = {}
    label = None
    for line in stdout.splitlines():
        if line.startswith("- label="):
            label = line[len("- label=") :].split(" ", 1)[0]
        elif label and "program_rule=" in line:
            out[label] = line.split("program_rule=", 1)[1].split(" ", 1)[0]
    assert out, f"一条 program_rule 都没解析到 —— 判据输入面为空。stdout={stdout[:300]!r}"
    return out


def _program_statuses(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    label = None
    for line in stdout.splitlines():
        if line.startswith("- label="):
            label = line[len("- label=") :].split(" ", 1)[0]
        elif label and line.strip().startswith("program_status="):
            out[label] = line.strip().split("=", 1)[1].split(" ", 1)[0]
    return out


def _tree_snapshot(root: Path) -> dict[str, str]:
    """相对路径 → sha256 + 权限位（软链记链目标）。目录也进快照, 所以「多出一个

    空目录」「少了一个文件」这类改动同样会被 dict 相等判出来。
    """
    snapshot: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        for name in dirnames:
            path = base / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                # os.walk 把目录软链列进 dirnames; 只记 mode 的话「换个指向、权限位
                # 不变」在快照里看不出来（Codex r1 MEDIUM-10）。目标必须进快照。
                snapshot[f"{path.relative_to(root)}/"] = f"dirlink -> {os.readlink(path)}"
            else:
                snapshot[f"{path.relative_to(root)}/"] = f"dir mode={oct(info.st_mode & 0o777)}"
        for name in filenames:
            path = base / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                snapshot[str(path.relative_to(root))] = f"link -> {os.readlink(path)}"
            else:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                snapshot[str(path.relative_to(root))] = f"{digest} mode={oct(info.st_mode & 0o777)}"
    return snapshot


# ── ① 干净 fixture 全 MATCH ─────────────────────────────────────


def test_clean_fixture_is_all_match_exit_0(machine_env):
    done = _run(machine_env)
    assert done.returncode == 0, done.stdout + done.stderr
    statuses = _statuses(done.stdout)
    assert statuses == {
        "com.canvas.daily-review": "MATCH",
        "daily-review-wrapper.sh": "MATCH",
        "com.canvas.memory-health": "EXTERNAL-PRESENT",
        "com.canvas.neo4j-backup": "EXTERNAL-PRESENT",
        "com.canvas.qwen-graphiti": "EXTERNAL-PRESENT",
        "com.canvas.reranker-graphiti": "EXTERNAL-PRESENT",
    }
    # ⛔ 比**整个字典**不比值集合: 集合相等挡不住「少了三条 label」（把生产代码限制成
    # 只检查其中两件, 值集合仍是 {"PROGRAM-MATCH"}, 门照绿 —— Codex r1 MEDIUM-9）。
    assert _program_statuses(done.stdout) == {
        "com.canvas.daily-review": "PROGRAM-MATCH",
        "com.canvas.memory-health": "PROGRAM-MATCH",
        "com.canvas.neo4j-backup": "PROGRAM-MATCH",
        "com.canvas.qwen-graphiti": "PROGRAM-MATCH",
        "com.canvas.reranker-graphiti": "PROGRAM-MATCH",
    }
    assert any(line.startswith("PLAN 空") for line in _lines(done.stdout))


def test_report_prints_both_sha_and_source_blob(machine_env):
    """断的是**值**不是标签: `source_blob=` 这个前缀被 `source_blob=-` 一样满足,

    只钉标签的断言在「blob 恒为 None」这种回归下照样绿。
    """
    done = _run(machine_env)
    source = machine_env["harness"] / "scripts/launchd/daily-review-wrapper.sh"
    expected_blob = vi._git_blob_sha1(source.read_bytes())
    expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert len(expected_blob) == 40 and len(expected_sha) == 64
    assert f"source_blob={expected_blob}" in done.stdout
    assert f"source_sha256={expected_sha}" in done.stdout
    assert f"installed_sha256={expected_sha}" in done.stdout
    # 报告必须打出程序体**实际指向哪棵树**与**用了哪条取值规则**,
    # 否则「按内容比」会掩盖「指错了树」
    assert f"program_path={machine_env['home']}" in done.stdout
    assert "program_rule=interpreter+ProgramArguments[1]" in done.stdout


# ── ② 改一字节 → 恰该 label DRIFT ───────────────────────────────


def test_single_byte_flip_is_drift_on_exactly_that_label(machine_env):
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    data = bytearray(install.read_bytes())
    data[-1] = data[-1] ^ 0x01
    install.write_bytes(bytes(data))

    done = _run(machine_env)
    statuses = _statuses(done.stdout)
    assert statuses["daily-review-wrapper.sh"] == "DRIFT"
    assert statuses["com.canvas.daily-review"] == "MATCH"
    assert [label for label, value in statuses.items() if value == "DRIFT"] == ["daily-review-wrapper.sh"]
    assert sorted(value for value in statuses.values() if value.startswith("EXTERNAL")) == ["EXTERNAL-PRESENT"] * 4
    assert done.returncode == 2, done.stdout
    # 附带且必然的耦合: daily-review 的 plist 正指着这份被改的 wrapper,
    # 所以程序体侧同时报 PROGRAM-DRIFT —— 这是 program_source 校验在工作的证据,
    # 不是串台。安装侧状态仍然「恰一件 DRIFT」。
    assert _program_statuses(done.stdout)["com.canvas.daily-review"] == "PROGRAM-DRIFT"


# ── ③ 删一件 → 恰它 MISSING, rc 1 ───────────────────────────────


def test_missing_alone_is_exit_1(machine_env):
    """缺失语义没被 mismatch 吞掉 —— 本卡唯一的 rc==1 守门人, 禁止弱化成 != 0。"""
    (machine_env["home"] / LAUNCH_AGENTS / "com.canvas.daily-review.plist").unlink()
    done = _run(machine_env)
    statuses = _statuses(done.stdout)
    assert statuses["com.canvas.daily-review"] == "MISSING"
    assert statuses["daily-review-wrapper.sh"] == "MATCH"
    assert done.returncode == 1, done.stdout
    # plist 不在位 ⇒ 无从解析它的 ProgramArguments, 该轴记 SKIPPED 且不抬退出码
    assert _program_statuses(done.stdout)["com.canvas.daily-review"] == "SKIPPED"


def test_missing_wrapper_also_dangles_the_plist_and_escalates_to_2(machine_env):
    """缺失 + 程序体悬空并存时取 2 —— 两轴独立, 高档吃低档。"""
    (machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh").unlink()
    done = _run(machine_env)
    assert _statuses(done.stdout)["daily-review-wrapper.sh"] == "MISSING"
    assert _program_statuses(done.stdout)["com.canvas.daily-review"] == "PROGRAM-DANGLING"
    assert done.returncode == 2, done.stdout


# ── ④ 读不动 → UNREADABLE, 计阻断 ───────────────────────────────


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视权限位")
def test_unreadable_install_is_blocking(machine_env):
    install = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.daily-review.plist"
    install.chmod(0o000)
    try:
        done = _run(machine_env)
    finally:
        install.chmod(0o644)
    statuses = _statuses(done.stdout)
    assert statuses["com.canvas.daily-review"] == "UNREADABLE"
    assert "MATCH" not in statuses["com.canvas.daily-review"]
    assert _program_statuses(done.stdout)["com.canvas.daily-review"] == "UNPARSEABLE"
    assert done.returncode == 2, done.stdout


# ── ⑤ external 缺失: 可见, 但不计退出码 ──────────────────────────


def test_external_missing_is_visible_but_not_blocking(machine_env):
    for label in ("memory-health", "neo4j-backup", "qwen-graphiti", "reranker-graphiti"):
        (machine_env["home"] / LAUNCH_AGENTS / f"com.canvas.{label}.plist").unlink()
    done = _run(machine_env)
    statuses = _statuses(done.stdout)
    assert sorted(value for value in statuses.values() if value.startswith("EXTERNAL")) == ["EXTERNAL-MISSING"] * 4
    assert done.returncode == 0, done.stdout
    # 4 件全丢也 rc 0 是 managed:external 的定义, 所以它必须在正文与摘要里喊出来。
    # ⚠️ 两条断言各钉一处、按**整行**比: 写成子串会让 "EXTERNAL-MISSING=4" 被
    # "⚠️ EXTERNAL-MISSING=4" 满足, 看着是两条独立断言, 其实塌成同一条。
    lines = _lines(done.stdout)
    assert "EXTERNAL-MISSING=4" in lines, lines
    assert any(line.startswith("⚠️ EXTERNAL-MISSING=4") for line in lines), lines
    assert sum(1 for line in lines if line.startswith("- label=")) == 6


# ── ⑥ program_source: 按内容比, 不按路径比 ──────────────────────


def test_program_match_is_content_not_path(machine_env, tmp_path):
    elsewhere = tmp_path / "another-tree" / "scripts" / "memory-health.sh"
    _write(elsewhere, (machine_env["harness"] / "scripts/memory-health.sh").read_bytes(), 0o755)
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(_synth_plist("com.canvas.memory-health", elsewhere))

    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-MATCH"
    assert str(elsewhere) in done.stdout  # 报告要打出它实际指向哪棵树
    assert done.returncode == 0, done.stdout


def test_program_dangling_when_target_absent(machine_env, tmp_path):
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(_synth_plist("com.canvas.memory-health", tmp_path / "nope" / "gone.sh"))
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"
    assert done.returncode == 2, done.stdout


def test_program_drift_when_content_differs(machine_env, tmp_path):
    elsewhere = tmp_path / "stale" / "memory-health.sh"
    _write(elsewhere, b"#!/usr/bin/env bash\necho stale\n", 0o755)
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(_synth_plist("com.canvas.memory-health", elsewhere))
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DRIFT"
    assert done.returncode == 2, done.stdout


def test_unparseable_plist_is_blocking(machine_env):
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(b"this is not a plist at all")
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "UNPARSEABLE"
    assert done.returncode == 2, done.stdout


# ── ⑦ dry-run 零写 ─────────────────────────────────────────────


def test_dry_run_writes_nothing_and_prints_the_plan(machine_env):
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")

    before = _tree_snapshot(machine_env["home"])
    done = _run(machine_env, "--reinstall", "--dry-run")
    after = _tree_snapshot(machine_env["home"])

    assert after == before, "dry-run 动了 --home 树"
    assert "PLAN cp " in done.stdout
    assert "DRY-RUN 未写入任何字节" in done.stdout
    assert done.returncode == 2, done.stdout


def test_dry_run_plan_lists_only_repo_managed_items(machine_env):
    (machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist").unlink()
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    done = _run(machine_env, "--reinstall", "--dry-run")
    plan_lines = [line for line in done.stdout.splitlines() if line.startswith("PLAN cp ")]
    assert len(plan_lines) == 1
    assert plan_lines[0].endswith("# daily-review-wrapper.sh")


# ── ⑧ apply 幂等 + 真实 HOME 的确认门 ───────────────────────────


def test_apply_fixes_drift_and_is_idempotent(machine_env):
    """修复方向必须钉死: 仓内源 → 安装副本, 不是反过来。

    ⚠️ MATCH 是**对称**相等（installed_sha == source_sha）, 所以「把安装副本盖回仓内源」
    与「把仓内源装到安装位置」在状态字符串上长得一模一样; AST 门只看谁在写、快照门只看
    `--home`, 两把锁都锚在同一侧。实测把 source/dest 交换后整个文件 39 passed 照旧。
    所以这里断两件 MATCH 断不出来的事:
      ① harness 整棵树跑前跑后逐项相同 —— 仓内源一个字节都不许被写;
      ② 安装副本的内容等于**事先取下来的**仓内源字节, 而不只是「两边相等」。
    """
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    source = machine_env["harness"] / "scripts/launchd/daily-review-wrapper.sh"
    source_bytes = source.read_bytes()
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    external = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    external_sha = hashlib.sha256(external.read_bytes()).hexdigest()
    harness_before = _tree_snapshot(machine_env["harness"])

    first = _run(machine_env, "--reinstall", "--apply")
    assert first.returncode == 0, first.stdout + first.stderr
    assert "APPLIED daily-review-wrapper.sh" in _lines(first.stdout)
    assert any(line.startswith("POST-PLAN 空") for line in _lines(first.stdout))
    assert _statuses(first.stdout)["daily-review-wrapper.sh"] == "MATCH"
    assert hashlib.sha256(external.read_bytes()).hexdigest() == external_sha
    # ① 方向: 仓内源一个字节都没被写
    assert _tree_snapshot(machine_env["harness"]) == harness_before, "apply 写到了 harness 树"
    # ② 方向: 安装副本现在等于**原来的**仓内源字节（不是「两边互等」）
    assert install.read_bytes() == source_bytes
    assert source.read_bytes() == source_bytes

    after_first = _tree_snapshot(machine_env["home"])
    second = _run(machine_env, "--reinstall", "--apply")
    assert second.returncode == 0, second.stdout + second.stderr
    assert any(line.startswith("PLAN 空") for line in _lines(second.stdout))
    assert "APPLIED 空" in _lines(second.stdout)
    assert _tree_snapshot(machine_env["home"]) == after_first
    assert _tree_snapshot(machine_env["harness"]) == harness_before


def test_apply_preserves_existing_install_mode(machine_env):
    """重装的权限位口径与手工 cp 一致: 目标已在则保留它原有的权限位。

    仓内源是 0644 而已装 wrapper 是 0755 —— 若照搬源的权限位, 一次重装就会
    把可执行位悄悄降掉。
    """
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.chmod(0o755)
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    assert (machine_env["harness"] / "scripts/launchd/daily-review-wrapper.sh").stat().st_mode & 0o777 == 0o644

    done = _run(machine_env, "--reinstall", "--apply")
    assert done.returncode == 0, done.stdout + done.stderr
    assert install.stat().st_mode & 0o777 == 0o755


def test_apply_against_real_home_requires_explicit_confirmation():
    """真实 HOME 的 --apply 缺确认标志 ⇒ rc 3, 且真机 6 件一位不动。

    这条是唯一一处让测试触到真实 ~/Library 的地方, 且只 stat + 读 sha。
    """
    items = _machine_items()
    real_home = Path.home()
    targets = [real_home / item["install"][2:] for item in items]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in targets if path.is_file()}
    assert before, "真机 6 件一件都读不到 —— 判据的输入面为空, 作废"

    child_env = dict(os.environ)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(
        [sys.executable, str(VERIFIER), "--home", str(real_home), "--reinstall", "--apply"],
        capture_output=True,
        text=True,
        env=child_env,
    )
    assert done.returncode == 3, done.stdout + done.stderr
    assert "--i-confirm-home-write" in done.stderr
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in targets if path.is_file()}
    assert after == before


# ── ⑨ 报告落点门 ───────────────────────────────────────────────


def test_report_inside_managed_home_root_is_rejected(machine_env):
    target = machine_env["home"] / "Library" / "debt10-report.txt"
    done = _run(machine_env, report=target)
    assert done.returncode == 3, done.stdout + done.stderr
    assert not target.exists()


def test_report_inside_harness_scripts_is_rejected(machine_env):
    target = machine_env["harness"] / "scripts" / "debt10-report.txt"
    done = _run(machine_env, report=target)
    assert done.returncode == 3, done.stdout + done.stderr
    assert not target.exists()


def test_report_outside_managed_surface_is_written(machine_env, tmp_path):
    target = tmp_path / "evidence" / "debt10-report.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    done = _run(machine_env, report=target)
    assert done.returncode == 0, done.stdout + done.stderr
    assert target.is_file()
    assert "## 逐件状态" in target.read_text(encoding="utf-8")


def test_report_location_guard_resolves_symlinks(machine_env, tmp_path):
    """落点判定走物理解析: 一条指向受管面的软链不能绕过它。"""
    link = tmp_path / "sneaky"
    link.symlink_to(machine_env["home"] / "Library")
    done = _run(machine_env, report=link / "debt10-report.txt")
    assert done.returncode == 3, done.stdout + done.stderr
    assert not (machine_env["home"] / "Library" / "debt10-report.txt").exists()


# ── 软链安装副本 ───────────────────────────────────────────────


def test_symlinked_install_is_unreadable_and_never_written(machine_env, tmp_path):
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    decoy = tmp_path / "decoy.sh"
    decoy.write_bytes(b"#!/usr/bin/env bash\necho decoy\n")
    decoy_sha = hashlib.sha256(decoy.read_bytes()).hexdigest()
    install.unlink()
    install.symlink_to(decoy)

    done = _run(machine_env, "--reinstall", "--apply")
    assert _statuses(done.stdout)["daily-review-wrapper.sh"] == "UNREADABLE"
    assert "软链" in done.stdout
    assert done.returncode == 2, done.stdout
    assert "PLAN 空" in done.stdout  # 读不动的件不进计划: 不拿猜测覆盖未知状态
    assert hashlib.sha256(decoy.read_bytes()).hexdigest() == decoy_sha
    assert install.is_symlink()


# ── 参数组合 ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "args",
    [
        ("--reinstall",),
        ("--dry-run",),
        ("--apply",),
        ("--reinstall", "--dry-run", "--apply"),
    ],
)
def test_bad_flag_combinations_are_usage_errors(machine_env, args):
    done = _run(machine_env, *args)
    assert done.returncode == 3, f"{args} → {done.returncode}: {done.stdout}{done.stderr}"


def test_unknown_flag_is_usage_error_not_argparse_2(machine_env):
    """argparse 默认对未知参数 SystemExit(2) —— 会与「内容漂」档串味, 必须归 3。"""
    done = _run(machine_env, "--no-such-flag")
    assert done.returncode == 3, done.stdout + done.stderr


# ── manifest schema ────────────────────────────────────────────


def test_manifest_machine_items_schema_holds():
    items = vi.load_machine_items(MANIFEST)
    assert len(items) == 6
    assert sum(1 for item in items if item.managed == "repo") == 2
    assert sum(1 for item in items if item.managed == "external") == 4
    for item in items:
        assert item.install.startswith("~/")
        assert "/Users/" not in item.install
        assert item.role in vi.VALID_ROLES
        if item.managed == "repo":
            assert (REPO_ROOT / item.source).is_file()
        else:
            assert item.source is None
        if item.program_source is not None:
            assert (REPO_ROOT / item.program_source).is_file()


@pytest.mark.parametrize(
    "mutation,fragment",
    [
        ({"install": "/Users/someone/Library/x.plist"}, "'~/' 开头"),
        ({"install": "~/Library/../../etc/passwd"}, ".."),
        ({"managed": "somehow"}, "managed"),
        ({"role": "cron"}, "role"),
        ({"source": "/abs/path"}, "相对路径"),
    ],
)
def test_manifest_schema_rejects_bad_entries(tmp_path, mutation, fragment):
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][0])
    entry.update(mutation)
    raw["machine_items"] = [entry]
    bad = tmp_path / "bad-manifest.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError) as caught:
        vi.load_machine_items(bad)
    assert fragment in str(caught.value)


def test_manifest_schema_rejects_inline_content_baseline(tmp_path):
    """sha 在校验时算, 不进 manifest（与 :261 的 template-free 门同口径）。"""
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][0])
    entry["sha256"] = "deadbeef"
    raw["machine_items"] = [entry]
    bad = tmp_path / "bad-manifest.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError) as caught:
        vi.load_machine_items(bad)
    assert "内容基线字段" in str(caught.value)


def test_missing_machine_items_key_is_manifest_error(tmp_path):
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw.pop("machine_items")
    bad = tmp_path / "no-machine-items.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError):
        vi.load_machine_items(bad)


# ── AST 零写门 ─────────────────────────────────────────────────


def test_no_write_calls_outside_the_two_writers():
    found = collect_write_call_owners(VERIFIER)
    assert found, "AST 门一个写调用都没数到 —— 输入面为空, 判据作废"
    owners = {owner for owner, _, _ in found}
    assert owners - ALLOWED_WRITE_OWNERS == set(), (
        f"写调用逃出允许名单: {sorted((o, c, n) for o, c, n in found if o not in ALLOWED_WRITE_OWNERS)}"
    )
    assert "def:verify" not in owners
    assert "<module>" not in owners


@pytest.mark.parametrize("entrypoint", ZERO_WRITE_ENTRYPOINTS)
def test_no_writer_is_reachable_from_the_read_only_entrypoints(entrypoint):
    """零写承诺的**另一半**: 只读入口的调用链里不许走到两个写者。

    上面那条是调用点判据 —— 它查「写调用长在谁体内」, 所以在 `verify()` 里加一行
    `_write_report(...)` 它完全看不见: 写调用仍在 `_write_report` 体内, owner 集合
    一字不变。两条合起来才是「verify 及其调用链零写」。
    """
    reachable = writers_reachable_from(VERIFIER, entrypoint)
    assert reachable == set(), f"{entrypoint} 的调用链能走到写者: {sorted(reachable)}"


def test_call_graph_gate_flags_a_planted_writer_call(tmp_path):
    """对照输入: 在 verify() 里加一行对写者的调用, 调用图门必须报出来。"""
    mutated = tmp_path / "mutated.py"
    source = VERIFIER.read_text(encoding="utf-8")
    needle = '    """全量只读校验。'
    assert needle in source
    mutated.write_text(
        source.replace(needle, '    _write_report(Path("x"), "ran")\n' + needle, 1),
        encoding="utf-8",
    )
    assert writers_reachable_from(mutated, "verify") == {"_write_report"}
    # 而**调用点**门对这个变异完全无感 —— 这正是为什么需要两条
    owners = {owner for owner, _, _ in collect_write_call_owners(mutated)}
    assert owners - ALLOWED_WRITE_OWNERS == set()


def test_ast_gate_sees_through_comments_and_dead_branches(tmp_path):
    """验伪锚: 门数的是 ast.Call 节点。

    注释与字符串字面量里的写调用**不该**被数到（文本门会误判）; `if False:` 下的
    真调用**必须**被数到（它是可执行代码, 只是这次没走到）。
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import os\n"
        "def innocent():\n"
        "    # os.replace('a', 'b')\n"
        '    marker = "write_text"\n'
        "    return marker\n"
        "def guilty():\n"
        "    if False:\n"
        "        os.replace('a', 'b')\n",
        encoding="utf-8",
    )
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert owners == {"def:guilty"}


def test_ast_gate_flags_a_planted_write_in_verify(tmp_path):
    """对照输入: 把一行写调用移植进 verify(), 门必须把 verify 报出来。"""
    mutated = tmp_path / "mutated.py"
    source = VERIFIER.read_text(encoding="utf-8")
    needle = '    """全量只读校验。'
    assert needle in source
    mutated.write_text(source.replace(needle, '    open("planted", "w")\n' + needle, 1), encoding="utf-8")
    owners = {owner for owner, _, _ in collect_write_call_owners(mutated)}
    assert "def:verify" in owners
    assert owners - ALLOWED_WRITE_OWNERS == {"def:verify"}


# ── blob 等价 ──────────────────────────────────────────────────


def test_git_blob_sha1_matches_real_git():
    """纯 Python 算的 source_blob 必须与真 `git hash-object` 逐字同。

    不 shell out 是刻意的（只读校验器不该 fork 一个能写仓库的二进制）, 代价是
    等价性必须自己钉住, 否则报告里那个 40 位数字没人核过。
    """
    target = SCRIPTS_DIR / "launchd" / "daily-review-wrapper.sh"
    done = subprocess.run(["git", "hash-object", str(target)], capture_output=True, text=True, cwd=REPO_ROOT)
    assert done.returncode == 0, done.stderr
    assert vi._git_blob_sha1(target.read_bytes()) == done.stdout.strip()


def test_script_cannot_launch_any_external_program():
    """⛔ 重装之后的重载是人的动作 —— 脚本里不得有任何启动外部程序的能力。

    钉「不能跑任何外部程序」而不是钉「没有 launchctl 这个词」: 后者是名字判据,
    换成 `"launch" + "ctl"` 或走一个变量就绕过了; 前者是能力判据, 它同时覆盖
    launchctl、git、cp 和任何将来想加进来的子进程。
    """
    source = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported = {
        alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert "subprocess" not in imported
    assert "pty" not in imported

    spawners = {"system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp", "startfile"}
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and (
            func.attr in spawners or func.attr.startswith("exec") or func.attr.startswith("spawn")
        ):
            offenders.append((func.attr, node.lineno))
        if isinstance(func, ast.Name) and func.id in {"eval", "exec", "compile", "__import__"}:
            offenders.append((func.id, node.lineno))
    assert offenders == [], f"脚本里有启动外部程序 / 动态执行的调用: {offenders}"

    # ⚠️ 刻意**不**再加一条「源码里不许出现 launchctl 这个词」: 那是名字判据,
    # 既弱（`"launch" + "ctl"` 就绕过）又会反过来逼着报告删掉「本校验器不调用
    # launchctl」这句诚实的边界声明。上面三条是能力判据 —— 没有 subprocess、
    # 没有 exec/spawn/system、没有动态执行, 这个进程压根起不了任何外部程序,
    # 名字怎么拼都没用。


# ── 内部对抗复核 2026-09-19 的整改门（3 HIGH + MEDIUM 各配一条对照输入）──────
#
# 下面每一条都对应一个「改之前会绿、改之后才红」的具体输入。原先这些路径**一条
# 对照输入都没有** —— 门看着覆盖了, 其实从没被走到过。


def _case_variant(path: Path) -> str | None:
    """返回同一个目录的大小写变体拼法; 文件系统区分大小写时返回 None。"""
    variant = path.parent / path.name.upper()
    if variant == path:
        variant = path.parent / path.name.lower()
    if variant == path:
        return None
    try:
        return str(variant) if os.path.samefile(str(variant), str(path)) else None
    except OSError:
        return None


def test_confirmation_guard_is_not_vacuous(machine_env):
    """确认门必须在**计划非空**时被验到。

    原先那条真机测试在这台机器上恒为空计划（两件 repo 管理的都是 MATCH）, 于是
    「前后 sha 不变」不论守卫在不在都成立 —— 断言是空洞的。这里把子进程的 HOME
    指到 tmp 树, 让「--home 就是真实 HOME」这个分支在完全 hermetic 的环境里生效,
    同时先造出真实漂移, 计划非空。
    """
    home = machine_env["home"]
    install = home / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    drifted = install.read_bytes()

    dry = _run(machine_env, "--reinstall", "--dry-run", child_home=home)
    plan_lines = [line for line in _lines(dry.stdout) if line.startswith("PLAN cp ")]
    assert len(plan_lines) == 1, "计划为空 ⇒ 下面那条断言会退化成恒真"

    blocked = _run(machine_env, "--reinstall", "--apply", child_home=home)
    assert blocked.returncode == 3, blocked.stdout + blocked.stderr
    assert "--i-confirm-home-write" in blocked.stderr
    assert install.read_bytes() == drifted, "守卫没拦住, 文件被改了"

    allowed = _run(machine_env, "--reinstall", "--apply", "--i-confirm-home-write", child_home=home)
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert install.read_bytes() != drifted


def test_case_variant_home_still_requires_confirmation(machine_env):
    """别名拼法也算真实 HOME —— 身份按 inode 判, 不按路径字符串判。

    macOS 启动卷大小写不敏感, `/users/x` 与 `/Users/x` 是同一个目录却是两个字符串;
    `/System/Volumes/Data/...` 那层 firmlink 同理, 而那正是 `df` 打印的拼法。
    """
    home = machine_env["home"]
    variant = _case_variant(home)
    if variant is None:
        pytest.skip("此文件系统区分大小写, 造不出同一目录的别名拼法")
    install = home / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    drifted = install.read_bytes()

    done = _run(machine_env, "--reinstall", "--apply", home_arg=variant, child_home=home)
    assert done.returncode == 3, done.stdout + done.stderr
    assert install.read_bytes() == drifted
    # ⚠️ 断的是**第一道门自己的那句话**。只断 rc 3 / 只断 "--i-confirm-home-write" 的话,
    # 第二道门（写目标落在真实 HOME 内）会替它挡住同一个输入 —— 于是把第一道门的
    # inode 判定换回字符串比较, 整个文件照样全绿（实测: 负控⑥ 103 passed 存活）。
    # 更强的门吃掉弱门的测试面, 这是给第一道门留的独立杀伤点。
    assert "--apply 指向真实 HOME" in done.stderr, done.stderr
    assert "写目标落在真实 HOME" not in done.stderr, done.stderr


def test_apply_creates_a_missing_install_copy(machine_env):
    """MISSING 件的 apply 路径此前一条对照输入都没有 —— 四条 apply 测试全是 DRIFT。"""
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    source_bytes = (machine_env["harness"] / "scripts/launchd/daily-review-wrapper.sh").read_bytes()
    install.unlink()
    assert not install.exists()

    done = _run(machine_env, "--reinstall", "--apply")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "APPLIED daily-review-wrapper.sh" in _lines(done.stdout)
    assert install.read_bytes() == source_bytes
    assert _statuses(done.stdout)["daily-review-wrapper.sh"] == "MATCH"


def test_apply_on_missing_parent_directory_creates_it(machine_env):
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    source_bytes = (machine_env["harness"] / "scripts/launchd/daily-review-wrapper.sh").read_bytes()
    install.unlink()
    install.parent.rmdir()
    done = _run(machine_env, "--reinstall", "--apply")
    assert done.returncode == 0, done.stdout + done.stderr
    assert install.read_bytes() == source_bytes


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视权限位")
def test_apply_failure_inside_the_writer_is_exit_2_not_a_raw_traceback(machine_env):
    """写路径上的 OSError 必须落到承诺的档位, 不能裸抛让解释器退 1。

    场景要求**真的走进** `_apply_reinstall`: 件必须先进计划（DRIFT）, 然后写才失败。
    把父目录改成不可写即可 —— 读得到（所以状态是 DRIFT 不是 UNREADABLE）、写不进去。
    """
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    drifted = install.read_bytes()
    install.parent.chmod(0o500)
    try:
        done = _run(machine_env, "--reinstall", "--apply")
    finally:
        install.parent.chmod(0o755)
    assert done.returncode == 2, done.stdout + done.stderr
    assert "Traceback" not in done.stderr
    assert "安装失败" in done.stderr
    assert install.read_bytes() == drifted


def test_untraversable_install_dir_is_unreadable_not_missing(machine_env):
    """「问不出来」不许被压成「不存在」。

    `os.path.lexists()` 把 ENOTDIR / EACCES 一并吞成 False, 于是退出码从承诺的
    「读不动 = 2」降成「只是缺东西 = 1」—— 一个环境故障被伪装成一条缺失记录。
    """
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.unlink()
    install.parent.rmdir()
    install.parent.write_bytes(b"not a directory")  # 父目录位置上放一个普通文件

    done = _run(machine_env)
    statuses = _statuses(done.stdout)
    assert statuses["daily-review-wrapper.sh"] == "UNREADABLE"
    assert statuses["daily-review-wrapper.sh"] != "MISSING"
    assert "问不出来" in done.stdout
    assert done.returncode == 2, done.stdout
    # 计划里不许出现它: 读不动的件不拿猜测覆盖未知状态
    assert any(line.startswith("PLAN 空") for line in _lines(done.stdout))


def test_install_remainder_must_be_relative(tmp_path, machine_env):
    """`~//Library/x` 的余段是绝对路径, `home / "/Library/x"` 会丢掉 home。"""
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][1])
    escape = tmp_path / "ESCAPED"
    entry["install"] = f"~/{escape}/x.sh"  # 注意: escape 是绝对路径, 拼出来就是 `~//...`
    raw["machine_items"] = [entry]
    bad = tmp_path / "escape-manifest.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(vi.ManifestError) as caught:
        vi.load_machine_items(bad)
    assert "相对路径" in str(caught.value)

    done = _run(machine_env, "--reinstall", "--apply", "--manifest", str(bad))
    assert done.returncode == 3, done.stdout + done.stderr
    assert not escape.exists(), "安装路径逃出了 --home"


def test_ancestor_symlink_install_dir_is_refused(machine_env, tmp_path):
    """只查叶子是不是软链挡不住「受管根本身是软链」—— 写会落到链目标里。"""
    home = machine_env["home"]
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "Application Support" / "CanvasReview" / "bin").mkdir(parents=True)
    real_library = home / "Library"
    install = home / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.write_bytes(install.read_bytes() + b"\n# drifted\n")
    # 把 <home>/Library 整个换成一条指向树外的软链
    shutil.move(str(real_library), str(tmp_path / "library_real"))
    real_library.symlink_to(elsewhere)

    done = _run(machine_env, "--reinstall", "--apply")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "--home 之外" in done.stderr
    assert not list((elsewhere / "Application Support" / "CanvasReview" / "bin").iterdir())


def test_fifo_install_does_not_hang(machine_env):
    """没有写端的 FIFO 会让 read_bytes() 在内核里永久阻塞, except OSError 等不到。

    一个挂住的校验器比一个报错的校验器更糟 —— 定时任务会一直卡在那里。
    """
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.unlink()
    os.mkfifo(str(plist))
    child_env = dict(os.environ)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--home",
            str(machine_env["home"]),
            "--harness",
            str(machine_env["harness"]),
        ],
        capture_output=True,
        text=True,
        env=child_env,
        timeout=60,
    )
    assert "不是普通文件" in done.stdout
    assert done.returncode in (0, 2), done.stdout


def test_relative_program_path_is_dangling_not_cwd_resolved(machine_env):
    """相对的程序路径不拿进程 cwd 去补全 —— 那会让同样的磁盘内容换个目录就翻档。"""
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "ProgramArguments": ["/bin/bash", "scripts/memory-health.sh"],
                "RunAtLoad": True,
            }
        )
    )
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"
    assert "不是绝对路径" in done.stdout
    assert done.returncode == 2, done.stdout


def test_program_key_takes_precedence_over_program_arguments(machine_env, tmp_path):
    """launchd: `Program` 在时它才是可执行体, 只读 ProgramArguments[1] 会盯错文件。"""
    real = tmp_path / "real-program.sh"
    real.write_bytes((machine_env["harness"] / "scripts/memory-health.sh").read_bytes())
    decoy = tmp_path / "decoy.sh"
    decoy.write_bytes(b"#!/usr/bin/env bash\necho decoy\n")
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "Program": str(real),
                "ProgramArguments": [str(real), str(decoy)],
            }
        )
    )
    done = _run(machine_env)
    programs = _program_statuses(done.stdout)
    assert programs["com.canvas.memory-health"] == "PROGRAM-MATCH"
    # ⚠️ `program_rule=Program` 是 `program_rule=ProgramArguments[0]` 的**前缀** ——
    # 子串断言会被后者满足, 于是「Program 键被忽略」的回归照样绿。按整个词比。
    rules = _program_rules(done.stdout)
    assert rules["com.canvas.memory-health"] == "Program", rules
    assert set(rules) == set(_program_statuses(done.stdout))
    assert str(decoy) not in done.stdout


def test_report_guard_holds_when_managed_root_is_a_symlink(machine_env, tmp_path):
    """受管根自己是软链时, 只 resolve 一侧会让包含判定两边对不上。"""
    home = machine_env["home"]
    elsewhere = tmp_path / "library_elsewhere"
    shutil.move(str(home / "Library"), str(elsewhere))
    (home / "Library").symlink_to(elsewhere)
    target = home / "Library" / "sneaky-report.txt"

    done = _run(machine_env, report=target)
    assert done.returncode == 3, done.stdout + done.stderr
    assert not target.exists()
    assert not (elsewhere / "sneaky-report.txt").exists()


def test_duplicate_install_after_normalization_is_rejected(tmp_path):
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    first = dict(raw["machine_items"][1])
    second = dict(first)
    second["label"] = "duplicate-by-dot-segment"
    second["install"] = first["install"].replace("/bin/", "/./bin/")
    raw["machine_items"] = [first, second]
    bad = tmp_path / "dup-manifest.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError) as caught:
        vi.load_machine_items(bad)
    assert "." in str(caught.value)


@pytest.mark.parametrize("field", ["install", "source", "program_source"])
def test_nul_and_unencodable_values_are_manifest_errors(tmp_path, field):
    """裸 ValueError 会穿过 main 的两个 except 让解释器退 1, 而契约承诺的是 3。"""
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][0])
    if field not in entry or entry[field] is None:
        pytest.skip(f"第一条没有 {field}")
    entry[field] = entry[field] + "\x00evil"
    raw["machine_items"] = [entry]
    bad = tmp_path / f"nul-{field}.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError):
        vi.load_machine_items(bad)


# ── AST 门自身的对照输入（每条都是「改之前漏报」的真实写法）──────────────


@pytest.mark.parametrize(
    "snippet,expected_owner",
    [
        ('def f(p):\n    return p.open("w")\n', "f"),
        ('def f(dest):\n    return dest.open("wb")\n', "f"),
        ("def f(args):\n    return open(*args)\n", "f"),
        ("def f(p, opts):\n    return open(p, **opts)\n", "f"),
        ("import os as o\ndef f(a, b):\n    return o.replace(a, b)\n", "f"),
        ("from os import replace as rp\ndef f(a, b):\n    return rp(a, b)\n", "f"),
        ("import shutil\ndef f(a, b):\n    return shutil.copyfileobj(a, b)\n", "f"),
        ("import os\ndef f(fd, d):\n    return os.pwrite(fd, d, 0)\n", "f"),
        ("def f(handle, d):\n    return handle.write(d)\n", "f"),
        ("import tempfile\ndef f(d):\n    return tempfile.mkstemp(dir=d)\n", "f"),
    ],
)
def test_ast_gate_catches_every_previously_missed_write_form(tmp_path, snippet, expected_owner):
    probe = tmp_path / "probe.py"
    probe.write_text(snippet, encoding="utf-8")
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert f"def:{expected_owner}" in owners, snippet


def test_ast_gate_owner_is_qualified_so_a_nested_shadow_cannot_pass(tmp_path):
    """裸名白名单只要求「最近一层 def 恰好叫这个名字」—— 在 verify() 里再定义一个

    叫 `_write_report` 的内层函数就能骗过它。owner 用限定名就骗不过。
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        'def verify():\n    def _write_report():\n        return open("shadow", "w")\n    return _write_report\n',
        encoding="utf-8",
    )
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert owners == {"def:verify.def:_write_report"}
    assert owners - ALLOWED_WRITE_OWNERS == {"def:verify.def:_write_report"}


def test_ast_gate_sees_keyword_only_defaults(tmp_path):
    """`def f(*, y=os.makedirs(...))` 的默认值在 def 时于**外层**作用域求值 ——

    手写枚举 decorator_list/args.defaults/body 三个子树会让它整个看不见。
    """
    probe = tmp_path / "probe.py"
    probe.write_text('import os\ndef f(x, *, y=os.makedirs("/tmp/x")):\n    return x\n', encoding="utf-8")
    found = collect_write_call_owners(probe)
    assert found, "kw_defaults 里的写调用没被看见"
    assert {owner for owner, _, _ in found} == {"<module>"}


# ── Codex r1 整改门（4 HIGH + 6 MEDIUM，每条一个对照输入）──────────────────


def test_report_guard_is_not_fooled_by_a_case_alias(machine_env):
    """大小写别名也算受管面 —— `resolve()` 不折叠大小写。

    `<harness>/SCRIPTS/launchd/...` 与 `<harness>/scripts/launchd/...` 在
    macOS 启动卷上是同一个目录, 只看路径字符串的落点门会放行, 随后报告会**覆盖仓内
    的 plist 源文件**（Codex r1 HIGH-2）。
    """
    scripts = machine_env["harness"] / "scripts"
    variant = _case_variant(scripts)
    if variant is None:
        pytest.skip("此文件系统区分大小写, 造不出同一目录的别名拼法")
    victim = machine_env["harness"] / "scripts/launchd/com.canvas.daily-review.plist"
    before = victim.read_bytes()

    done = _run(machine_env, report=Path(variant) / "launchd" / "com.canvas.daily-review.plist")
    assert done.returncode == 3, done.stdout + done.stderr
    assert "受管面" in done.stderr
    assert victim.read_bytes() == before, "报告覆盖了仓内的 plist 源"


def test_confirmation_is_keyed_on_the_write_target_not_on_home_spelling(machine_env, tmp_path):
    """确认门要问的是「**这次要写的地方**在不在真实 HOME 里」。

    只问「`--home` 是不是家目录」时, `--home /` 配一条 `~/Users/<user>/…` 的安装路径
    就能让 home ≠ 真实 HOME 而写目标恰恰是真实的安装副本（Codex r1 HIGH-3）。
    本用例不真写任何东西: 它断言在写之前就被拦下, 且真机文件一位未动。
    """
    real_home = Path.home()
    real_install = real_home / WRAPPER_BIN / "daily-review-wrapper.sh"
    if not real_install.is_file():
        pytest.skip("真机上没有这份安装副本, 造不出这个场景")
    before = hashlib.sha256(real_install.read_bytes()).hexdigest()

    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][1])
    assert entry["managed"] == "repo"
    entry["install"] = f"~/{real_install.relative_to('/')}"  # `--home /` 下展开成真实路径
    raw["machine_items"] = [entry]
    crafted = tmp_path / "root-home-manifest.json"
    crafted.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    done = _run(
        machine_env,
        "--reinstall",
        "--apply",
        "--manifest",
        str(crafted),
        home_arg="/",
    )
    assert done.returncode == 3, done.stdout + done.stderr
    assert "--i-confirm-home-write" in done.stderr
    assert hashlib.sha256(real_install.read_bytes()).hexdigest() == before


def test_report_never_echoes_credentials_from_a_plist(machine_env):
    """报告要落盘、要贴进验收单 —— plist 里的 `NAME=VALUE` 一律不许原样出现。

    两条路径都堵: ① `env` 形态里那串环境赋值不再被当成程序路径;
    ② 出错时只描述 ProgramArguments 的**形状**, 不回显它的内容（Codex r1 HIGH-4）。
    """
    secret = "SYNTHETIC_DEBT10_SECRET_VALUE"
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    program = machine_env["harness"] / "scripts/memory-health.sh"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "ProgramArguments": ["/usr/bin/env", f"API_KEY={secret}", str(program)],
            }
        )
    )
    done = _run(machine_env)
    assert secret not in done.stdout, "凭据进了报告正文"
    assert secret not in done.stderr
    # env 形态下要跳过赋值找到真正的程序, 而不是把 `API_KEY=...` 当成程序路径
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-MATCH"

    # 非法元素的出错分支同样不许回显内容
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "ProgramArguments": ["/bin/bash", f"--api-key={secret}", 7],
            }
        )
    )
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "UNPARSEABLE"
    assert secret not in done.stdout, "出错原因回显了整组参数"
    assert "个元素" in done.stdout  # 只描述形状


def test_missing_interpreter_is_dangling_not_match(machine_env, tmp_path):
    """解释器本身不存在时这个任务根本跑不起来 —— 不能因为第二个参数内容对得上就判 MATCH。"""
    program = machine_env["harness"] / "scripts/memory-health.sh"
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "Program": str(tmp_path / "does-not-exist" / "bash"),
                "ProgramArguments": [str(tmp_path / "does-not-exist" / "bash"), str(program)],
            }
        )
    )
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"
    assert "解释器本身读不了" in done.stdout
    assert done.returncode == 2, done.stdout


def test_nul_in_a_plist_program_path_stays_inside_the_four_exit_codes(machine_env):
    """binary plist 里带 NUL 的程序路径会让 `os.stat()` 抛 `ValueError` ——

    只捕 `OSError` 的代码会让它裸抛、解释器退 1, 而契约承诺的是四档之一。
    """
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {"Label": "com.canvas.memory-health", "ProgramArguments": ["/bin/bash", "/tmp/a\x00b"]},
            fmt=plistlib.FMT_BINARY,
        )
    )
    done = _run(machine_env)
    assert done.returncode in (0, 1, 2, 3), done.stdout + done.stderr
    assert done.returncode == 2, done.stdout + done.stderr
    assert "Traceback" not in done.stderr
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"


def test_ast_gate_does_not_treat_a_class_named_like_a_writer_as_allowed(tmp_path):
    """模块级 `class _write_report:` 体内的写调用, 裸名白名单会把它当成允许 owner。"""
    probe = tmp_path / "probe.py"
    probe.write_text('class _write_report:\n    f = open("x", "w")\n', encoding="utf-8")
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert owners == {"class:_write_report"}
    assert owners - ALLOWED_WRITE_OWNERS == {"class:_write_report"}


@pytest.mark.parametrize(
    "snippet",
    [
        'from builtins import open as fopen\ndef f(p):\n    return fopen(p, "w")\n',
        "import os\ndef f(a, b):\n    w = os.replace\n    return w(a, b)\n",
        'import io\ndef f(p):\n    return io.FileIO(p, "w")\n',
    ],
)
def test_ast_gate_catches_aliased_writers(tmp_path, snippet):
    probe = tmp_path / "probe.py"
    probe.write_text(snippet, encoding="utf-8")
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert "def:f" in owners, snippet


def test_tree_snapshot_notices_a_retargeted_directory_symlink(tmp_path):
    """目录软链换个指向、权限位不变 —— 只记 mode 的快照看不出来。"""
    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir()
    link = root / "link"
    link.symlink_to(root / "a")
    before = _tree_snapshot(root)
    link.unlink()
    link.symlink_to(root / "b")
    assert _tree_snapshot(root) != before


# ── 第二轮对抗复核整改门（2 HIGH + 11 MEDIUM + 8 LOW，每条一个对照输入）────────


def test_ancestor_home_with_alias_spelling_still_requires_confirmation(tmp_path):
    """两道确认门合起来才盖得住「祖先 --home + 别名拼法」。

    门① 按 inode 判 `--home` 本身；门② 判**写目标**是否落在真实 HOME 内。
    门② 原先用的是**允许性**谓词（只比 resolve 后的路径字符串），于是
    `--home <家目录的祖先>` + 一条大小写变体的安装路径两道门都过 —— 真机被写。
    本用例全程在 tmp 树里，把子进程的 HOME 指过去，绝不碰真实 `~/Library`。
    """
    fake_home = tmp_path / "fakehome"
    harness = tmp_path / "harness"
    install_dir = fake_home / "Library" / "bin"
    install_dir.mkdir(parents=True)
    source = harness / "scripts" / "launchd" / "wrapper.sh"
    _write(source, b"#!/usr/bin/env bash\necho source\n", 0o644)
    victim = install_dir / "wrapper.sh"
    _write(victim, b"#!/usr/bin/env bash\necho drifted\n", 0o755)
    before = victim.read_bytes()

    alias = _case_variant(fake_home)
    if alias is None:
        pytest.skip("此文件系统区分大小写, 造不出同一目录的别名拼法")
    alias_name = Path(alias).name

    manifest = tmp_path / "alias-manifest.json"
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["machine_items"] = [
        {
            "label": "alias.wrapper",
            "role": "launchd-wrapper",
            "managed": "repo",
            "source": "scripts/launchd/wrapper.sh",
            "install": f"~/{alias_name}/Library/bin/wrapper.sh",
            "origin": "test-only",
            "note": "test-only",
        }
    ]
    manifest.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    child_env = dict(os.environ)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    child_env["HOME"] = str(fake_home)
    done = subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--manifest",
            str(manifest),
            "--home",
            str(tmp_path),  # 家目录的**祖先**
            "--harness",
            str(harness),
            "--reinstall",
            "--apply",  # 故意不带 --i-confirm-home-write
        ],
        capture_output=True,
        text=True,
        env=child_env,
    )
    assert done.returncode == 3, done.stdout + done.stderr
    assert "--i-confirm-home-write" in done.stderr
    assert victim.read_bytes() == before, "别名拼法让写目标穿过了确认门"


def test_report_cannot_land_in_the_real_home_managed_root(machine_env, tmp_path):
    """`--home` 指到别处时, 真实 HOME 的同名受管根同样不许当落点。"""
    target = Path.home() / "Library" / "debt10-should-not-exist.txt"
    done = _run(machine_env, report=target)
    assert done.returncode == 3, done.stdout + done.stderr
    assert not target.exists()


def test_relative_interpreter_is_dangling_not_cwd_resolved(machine_env):
    """解释器路径也不拿进程 cwd 补全 —— 与程序路径同口径。"""
    program = machine_env["harness"] / "scripts/memory-health.sh"
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(plistlib.dumps({"Label": "com.canvas.memory-health", "ProgramArguments": ["bash", str(program)]}))
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"
    assert "解释器路径不是绝对路径" in done.stdout
    assert done.returncode == 2, done.stdout


def test_interpreter_options_are_not_taken_as_the_program(machine_env):
    """`-c` 这类解释器选项不是程序路径。"""
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "ProgramArguments": ["/bin/bash", "-c", "echo hi"],
            }
        )
    )
    done = _run(machine_env)
    assert _program_statuses(done.stdout)["com.canvas.memory-health"] == "PROGRAM-DANGLING"
    assert "-c" not in _program_rules(done.stdout)["com.canvas.memory-health"]
    assert done.returncode == 2, done.stdout


def test_assignment_with_a_slash_in_the_name_does_not_leak(machine_env):
    """`a/b=<凭据>` 的「= 之前那段」含 `/`, 不是环境赋值 —— 但它照样不许原样进报告。"""
    secret = "SYNTHETIC_DEBT10_SLASHY_SECRET"
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.memory-health.plist"
    plist.write_bytes(
        plistlib.dumps(
            {
                "Label": "com.canvas.memory-health",
                "ProgramArguments": ["/usr/bin/env", f"a/b={secret}", "/bin/true"],
            }
        )
    )
    done = _run(machine_env)
    assert secret not in done.stdout
    assert secret not in done.stderr


def test_oversized_install_copy_is_reported_not_slurped(machine_env):
    """门拿着 st_size 却不看 = 白 stat 一次。超上限要有档位, 不是把进程挂在上面。"""
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    with install.open("wb") as handle:
        handle.truncate(vi.MAX_READ_BYTES + 1)
    done = _run(machine_env)
    assert _statuses(done.stdout)["daily-review-wrapper.sh"] == "UNREADABLE"
    assert "太大" in done.stdout
    assert done.returncode == 2, done.stdout


def test_unencodable_symlink_target_does_not_break_the_report(machine_env, tmp_path):
    """macOS 允许软链目标不是合法 UTF-8；原样拼进报告会让落盘时抛 UnicodeEncodeError。"""
    install = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    install.unlink()
    os.symlink(os.fsdecode(b"/tmp/\xff\xfe-gone"), install)
    report = tmp_path / "evidence" / "r.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    done = _run(machine_env, report=report)
    assert done.returncode == 2, done.stdout + done.stderr
    assert report.is_file(), "报告因为一个损坏的软链写不出来了"
    assert "软链" in report.read_text(encoding="utf-8")


def test_partial_apply_still_writes_a_report(machine_env, tmp_path):
    """多件计划中途失败 = 半更新的树；只丢一行 stderr 的话事后翻不出装进去了哪几件。"""
    wrapper = machine_env["home"] / WRAPPER_BIN / "daily-review-wrapper.sh"
    plist = machine_env["home"] / LAUNCH_AGENTS / "com.canvas.daily-review.plist"
    wrapper.write_bytes(wrapper.read_bytes() + b"\n# drifted\n")
    plist.write_bytes(plist.read_bytes() + b"\n")
    # 计划顺序跟 manifest 顺序: plist 在前、wrapper 在后。让**后一件**写不进去,
    # 才真的走出「前面装好了、后面炸了」这个半更新状态。
    wrapper.parent.chmod(0o500)
    report = tmp_path / "evidence" / "r.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    try:
        done = _run(machine_env, "--reinstall", "--apply", report=report)
    finally:
        wrapper.parent.chmod(0o755)
    assert done.returncode == 2, done.stdout + done.stderr
    body = report.read_text(encoding="utf-8")
    assert "APPLY-ERROR" in body
    assert "APPLIED com.canvas.daily-review" in body, body
    assert "APPLIED daily-review-wrapper.sh" not in body


@pytest.mark.parametrize("field", ["label", "origin", "note"])
def test_nul_in_rendered_string_fields_is_a_manifest_error(tmp_path, field):
    """label / origin / note 都会被原样渲染进报告 —— 只查「非空字符串」不够。"""
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = dict(raw["machine_items"][0])
    entry[field] = entry[field] + "\x00evil"
    raw["machine_items"] = [entry]
    bad = tmp_path / f"nul-{field}.json"
    bad.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(vi.ManifestError):
        vi.load_machine_items(bad)


# ── 两条门自身的对照输入 ──────────────────────────────────────


@pytest.mark.parametrize(
    "snippet,expect_flagged",
    [
        ("import os\ndef f(p):\n    return os.open(p, os.O_RDONLY | os.O_DIRECTORY)\n", False),
        ("import os\ndef f(p):\n    return os.open(p, os.O_WRONLY | os.O_CREAT)\n", True),
        ("import os\ndef f(p, fl):\n    return os.open(p, fl)\n", True),
        ("import os\ndef f(p):\n    return os.open(p)\n", True),
    ],
)
def test_os_open_is_judged_by_its_flags(tmp_path, snippet, expect_flagged):
    """只读地打开一个目录不是写。假阳性会逼人去放宽白名单, 那比漏报更危险。"""
    probe = tmp_path / "probe.py"
    probe.write_text(snippet, encoding="utf-8")
    owners = {owner for owner, _, _ in collect_write_call_owners(probe)}
    assert ("def:f" in owners) is expect_flagged, snippet


@pytest.mark.parametrize(
    "snippet",
    [
        # 写者当参数传出去
        "def _write_report(p, t):\n    pass\ndef helper(fn):\n    pass\ndef verify():\n    return helper(_write_report)\n",
        # 写者藏进一个内层函数
        'def _write_report(p, t):\n    pass\ndef verify():\n    def _flush():\n        return _write_report("x", "y")\n    return _flush\n',
        # 写者从容器里取出来调
        'def _write_report(p, t):\n    pass\ndef verify():\n    table = {"w": _write_report}\n    return table["w"]("x", "y")\n',
        # 多跳
        'def _write_report(p, t):\n    pass\ndef middle():\n    return _write_report("x", "y")\ndef verify():\n    return middle()\n',
    ],
)
def test_call_graph_gate_follows_indirect_routes_to_a_writer(tmp_path, snippet):
    probe = tmp_path / "probe.py"
    probe.write_text(snippet, encoding="utf-8")
    assert writers_reachable_from(probe, "verify") == {"_write_report"}, snippet


def test_call_graph_gate_refuses_a_nonexistent_entrypoint(tmp_path):
    """入口名打错时门会静静地空转 —— 那是最糟的一种绿。"""
    probe = tmp_path / "probe.py"
    probe.write_text("def verify():\n    return 1\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="门会空转"):
        writers_reachable_from(probe, "no_such_entrypoint")


def test_helper_predicates_are_used_in_the_right_direction():
    """禁止性判定必须用并集谓词, 允许性判定必须用物理谓词 —— 两者不可互换。

    我在 docstring 里写了这条规则, 然后在第三个调用点用错了一个（复核实测可写穿）。
    写下规则不等于遵守规则, 所以这里让一条门去查每个调用点。
    """
    source = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    prohibitive_users: set[str] = set()
    permissive_users: set[str] = set()
    for owner, call in _walk_calls(tree):
        func = call.func
        if not isinstance(func, ast.Name):
            continue
        if func.id == "_within_any_form":
            prohibitive_users.add(owner)
        elif func.id == "_physically_within":
            permissive_users.add(owner)
    # 禁止性位置: 报告落点门 + 真实 HOME 写目标确认
    assert "def:report_location_problem" in prohibitive_users
    assert "def:main" in prohibitive_users
    # 允许性位置: 写入包含判定
    assert "def:_apply_reinstall" in permissive_users
    # main 里不许再出现允许性谓词（那正是用反的那一处）
    assert "def:main" not in permissive_users
