"""CARD-G3-7-R2 (BATCH-2026-09-07-第十三批): mastery 侧 FSRS 投影化写边界门。

锁三件事:

  ① 锚点门 —— mastery_engine.py / mastery_store.py 源码里「非 FSRS 调度真相源」
     这句标注不得被后人顺手删掉。
  ② 写边界静态门 (AST 数写调用, 不是 grep 字面量) —— 这两个模块内不存在任何
     文件系统写调用; 外加 `fsrs_card_states` 字面量计数 (engine 恰好 1 条注释锚,
     store 0)。
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
# 写调用: 任何会修改文件系统的调用。判据按**调用名**取 (Name.id 或 Attribute.attr),
# 因为目标路径在静态上不可解析 —— 路径可以是运行期拼出来的, 所以「写到 .md 还是
# 写到别处」静态判不了。本门因此断言一个**更强**的不变量: 这两个模块根本不做
# 文件写。这对它们成立且有实义: engine 只算, store 只写 Neo4j, 两者都不该碰盘。
BANNED_WRITE_CALLS = frozenset(
    {
        "write_text",
        "write_bytes",
        "writelines",
        "write",
        "dump",  # json.dump(obj, fp) 写文件; json.dumps 只产字符串, 不在名单
        "mkdir",
        "makedirs",
        "touch",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "rename",
        "replace",
        "copy",
        "copyfile",
        "copy2",
        "move",
    }
)

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

    fail-closed: mode 不是字面字符串时按**写**处理。一个静态判不出模式的
    open() 正是这道边界门最该拦下的形态, 放行它等于给绕过留门。
    """
    mode = None
    if len(node.args) >= 2:
        mode = node.args[1]
    for kw in node.keywords:
        if kw.arg == "mode":
            mode = kw.value
    if mode is None:
        return False  # open(path) → 只读, 允许
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return bool(_WRITE_MODE_CHARS & set(mode.value))
    return True


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


def _find_write_calls(source: str) -> list[str]:
    """返回源码里全部文件写调用, 形如 ['write_text@L120', 'open(w)@L88']。"""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name is None:
            continue
        if name == "open":
            if _open_is_write(node):
                found.append(f"open(write-mode)@L{node.lineno}")
            continue
        if name in BANNED_WRITE_CALLS:
            found.append(f"{name}@L{node.lineno}")
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
    overlap = BANNED_WRITE_CALLS & ALLOWED_READ_CALLS
    assert not overlap, (
        f"禁用名单侵入了读 API: {sorted(overlap)}。本门只禁写不禁读；"
        " 禁读会把「backend 不许溯源 frontmatter」这个缺陷写成规格。"
    )

    writing_source = (
        "from pathlib import Path\n"
        "import json\n"
        "def f(p):\n"
        "    Path(p).write_text('x')\n"
        "    with open(p, 'w') as fh:\n"
        "        json.dump({}, fh)\n"
    )
    hits = _find_write_calls(writing_source)
    assert len(hits) == 3, f"正控失败: 检查器应报出 3 处写调用, 实得 {hits}"

    reading_source = (
        "from pathlib import Path\n"
        "import json\n"
        "def g(p):\n"
        "    raw = Path(p).read_text('utf-8')\n"
        "    with open(p) as fh:\n"
        "        return json.load(fh), raw\n"
    )
    assert _find_write_calls(reading_source) == [], (
        "负控失败: 检查器把纯读源码报成了写 —— 这会误拦合法的 frontmatter 读。"
    )


def test_mastery_modules_contain_no_filesystem_writes():
    """门 ②: 两个 mastery 模块内不存在任何文件系统写调用。

    比卡文要求的「不写 .md / 不写 fsrs_card_states.json」更强, 理由写在模块
    常量 BANNED_WRITE_CALLS 上方: 写目标的路径可以是运行期拼出来的, 静态判不了
    「写到哪」, 所以判「有没有写」。这两个模块本来就不该碰盘, 该不变量成立。
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
