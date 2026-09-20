"""CARD-HARNESS-TREE-PARSE-R2 — quiz-answer 主写点选树的三层收口。

本文件钉住 T7-A r10 H1 的收口与并入的两件同族缺口：

1. **忠实性**（`..._lying_parser_is_refused`）：`_harness_tree` 的 PyYAML 行为探针
   （`yaml.safe_load("a: 1")` 是否给出 `{"a": 1}`）只证明「它像个解析器」，**不证明
   它对真实 config 的解析忠于文件内容**。一个恒返 `{"a": 1}` 的假 `yaml` 模块能过
   探针，随后对写着 `harness_tree: <目标树>` 的 config 也返回 `{"a": 1}` ⇒ 生产按
   「没写这个键」**静默回退父树** ⇒ 学习事件绑到另一棵 harness 上。收口 = 文件明文
   有 `harness_tree:` 键时解析结果**不得沉默**（词法只做否决，绝不采用）。

2. **契约**（`..._harness_contract_refuses`）：写点从选中的树无条件导入 7 个名字，
   除「导得进」外零判据 ⇒ 任意旧版/异版 harness 分发被静默采用并按其语义写账本。
   收口 = `_harness_contract(REPO)` 的影子门 / 版本 / 形状 / 纯函数行为探针。

3. **半态**（`..._preflight_refuses_before_step3`）：缺 PyYAML 时 Step 3 已写分、
   Step 4 主写点才拒写 ⇒ 白板停在「已记分、节点未更新」。收口 = Step 2.9 预检块
   （先拒后写），既有半态**不回滚**（用户口径，分数保留并在拒因里点名）。

⛔ **零 mock（DD-03）**：假 `yaml` 模块、假 validator 树、`PYTHONPATH` 前置的
`yaml.py` 都是**负控输入**（坏环境本身的形态），不是对被测代码的 mock。被测实现
一律从 `SKILL.md` 逐字抽取（AST）或用 `subprocess` 真跑，本文件不另抄一份。

⛔ **全部路径 `tmp_path` 派生**：主干树的 `SKILL.md` / `validate_learning_events.py`
只作**读源**（`shutil.copy` / `symlink_to`），本文件不写 live vault、不连任何库。
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

#: 车道树根（本文件在 `backend/tests/skills/` ⇒ parents[3]），与 test_g3_2_review_ledger.py:43 同深度。
WT = Path(__file__).resolve().parents[3]
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
_SKILL_TEXT = SKILL.read_text(encoding="utf-8")

_BLOCK_RE = r"python3 - <<'PYEOF'\n(.*?)\nPYEOF"
_ALL_BLOCKS = re.findall(_BLOCK_RE, _SKILL_TEXT, re.DOTALL)

#: 主写点块（与 test_g3_2_review_ledger.py:49-56 同一条过滤器，逐字同）。
_MAIN_BLOCKS = [b for b in _ALL_BLOCKS if 'P = "/tmp/quiz-answer-payload.json"' in b]
assert len(_MAIN_BLOCKS) == 1, f"SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(_MAIN_BLOCKS)}"
CODE = _MAIN_BLOCKS[0]

#: 缺库拒因整句（与 test_g3_2_review_ledger.py:7350 逐字同 —— 两处锚同一句，漂了一起红）。
_NO_YAML_REFUSAL = "PyYAML 不可用 — harness_tree 指向哪棵树不可证"
#: 半态标记的稳定子串（Step 2.9 / 主块缺库拒因 / 契约拒因三处共用）。
_HALFSTATE_MARK = "分数保留"
#: 忠实性拒因的稳定子串。
_UNFAITHFUL_MARK = "解析结果与文件内容不符"


# ══════════════════════════════════════════════════════════════════════════
# 被测实现的逐字抽取（不另抄一份 —— 抄一份 = 两份手写清单，必然漂移）
# ══════════════════════════════════════════════════════════════════════════
def _extract(*names: str) -> tuple:
    """把主写点里指名的顶层函数**逐字**抽出来，在本进程里直接调用。

    ⛔ 与 `test_g3_2_review_ledger.py:7523 _extract_harness_tree()` 同法同口径：
    锚不到就当场断言失败（而不是悄悄测了个别的东西）。

    ⛔ 命名空间只镜像**被抽函数中最早那个定义之前**的顶层 import。这不是图省事 ——
    主写点顶层还有 `from decay_beta import …`（vault 脚本，需要 `sys.path` 先插
    `<vault>/.claude/scripts`），盲目 exec 全部顶层 import 会在这里 `ImportError`，
    把「夹具装不起来」伪装成「被测代码有毛病」。Step 2.9 预检块用的是同一条口径。
    """
    _mod = ast.parse(CODE)
    _fns = [n for n in _mod.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(_fns) == len(names), (
        f"⛔ 写点里 {names} 应各恰 1 处定义, 实见 {[n.name for n in _fns]} —— 锚不到就等于没测生产代码"
    )
    _cut = min(n.lineno for n in _fns)
    _ns: dict = {}
    for _st in _mod.body:
        if isinstance(_st, (ast.Import, ast.ImportFrom)) and _st.lineno < _cut:
            exec(compile(ast.Module(body=[_st], type_ignores=[]), "<skill-prelude>", "exec"), _ns)  # noqa: S102
    for _need in ("os", "re", "sys"):
        assert _need in _ns, f"⛔ 写点的顶层 import 里没有 {_need} —— 本 helper 的假设漂了, 先核写点"
    exec(compile(ast.Module(body=_fns, type_ignores=[]), "<skill-harness>", "exec"), _ns)  # noqa: S102
    return tuple(_ns[n] for n in names)


def _outcome(_fn, *args):
    """跑一次，把结局归一成 `("ok", <返回值>)` / `("exit", <拒因全文>)`。"""
    try:
        return ("ok", _fn(*args))
    except SystemExit as _e:
        return ("exit", str(_e))


def _usable_tree(root: Path) -> Path:
    """造一棵能通过 `isdir(<tree>/backend/scripts)` 的树（不含 validator）。"""
    (root / "backend" / "scripts").mkdir(parents=True, exist_ok=True)
    return root


def _real_harness(root: Path) -> Path:
    """造一棵**真能用**的 harness 树：validator 是 symlink → 主干那一份。

    ⛔ symlink 而不是 copy 是有意的：契约门的影子判据因此**只能**比未 realpath 的
    `__file__` 目录 —— 比 realpath 会把这棵合法的 alt 树判成影子（它的 validator
    物理上就在主干树里）。这一格同时是影子判据「没写成 realpath」的守卫。
    """
    (root / "backend" / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    return root


def _fake_validator_tree(root: Path, body: str) -> Path:
    """造一棵 validator 是**手写占位**的树（契约门的负控输入）。"""
    _s = root / "backend" / "scripts"
    _s.mkdir(parents=True, exist_ok=True)
    (_s / "validate_learning_events.py").write_text(body, encoding="utf-8")
    return root


#: 契约门占位 validator 的「全对」底本 —— 每格只在此基础上拆掉**一项**。
_VALIDATOR_STUB_OK = """\
import re

EVENT_VERSION = 1
_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")
_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")


def classify_card_state(fields):
    return ("new", "占位")


def _vault_id_of(p):
    return "占位"


def _looks_like_review_ext(rec):
    return False


def validate_record_full(record, manifest=None, vault_id=None):
    if not isinstance(record, dict):
        return (["顶层必须是 JSON object"], [])
    return ([], [])


def _golden_manifest(*a, **kw):
    return {}
"""


@pytest.fixture(autouse=True)
def _no_validator_leak():
    """每格前后都把 `validate_learning_events` 从 `sys.modules` / `sys.path` 摘干净。

    ⛔ 不摘的话，前一格 import 进来的那棵树会被后一格直接复用 —— 契约门看起来全绿，
    实际上第二格之后压根没去选中的树里找过。
    """
    _path0 = list(sys.path)
    sys.modules.pop("validate_learning_events", None)
    yield
    sys.modules.pop("validate_learning_events", None)
    sys.path[:] = _path0


# ══════════════════════════════════════════════════════════════════════════
# ① 忠实性：说谎的解析器不得被采用（r10 H1 收口）
# ══════════════════════════════════════════════════════════════════════════
#: 生产键级探针喂给解析器的那份文档 —— **从写点里逐字抽出来，不手抄**。
#: ⛔ round-3 把它从单行改成三行（丢文件尾巴的坏解析器对单行文档没有尾巴可丢，照样答对）。
#: 当时这里写的是手抄常量 + `assert _KEY_PROBE_DOC in CODE` 的防漂移 —— 那条 assert
#: **没红**，因为新文档恰好**包含**旧串（`in` 是子串判定）。两格门红才提醒了我。
#: ⇒ 改成正则抽取：写点改一个字，这里跟着改，零手抄面。
_KPROBE_M = re.search(r'_KPROBE_DOC = (".*?")\n', CODE)
assert _KPROBE_M, '⛔ 写点里找不到 `_KPROBE_DOC = "..."` —— 键级探针的文档定义漂了，先核写点'
_KEY_PROBE_DOC = ast.literal_eval(_KPROBE_M.group(1))
assert "harness_tree" in _KEY_PROBE_DOC, f"⛔ 抽出来的探针文档里没有 harness_tree: {_KEY_PROBE_DOC!r}"


def test_g33r2_key_probe_doc_must_be_multiline_with_the_key_last():
    """⛔ 键级探针的文档必须是**多行、且那个键在最后一行** —— 这是 round-3 HIGH 的结构守卫。

    单行探针没有尾巴可丢，于是一整类**丢文件尾巴**的坏解析器（缓冲截断 / 流被提前关闭 /
    只读前 N 行）照样答对、活过这一层；配上词法否决只认顶格裸键，两层一起落空。

    ⚠️ 本门是结构判据，不测行为——行为由 `..._truncating_parser_is_refused` 三格钉。
    它单独立在这里，是为了让「有人把探针改回单行」这件事红在一句看得懂的话上，
    而不是红成一堆行为门的连带失败。
    """
    _lines = _KEY_PROBE_DOC.splitlines()
    assert len(_lines) >= 3, (
        f"⛔ 探针文档只有 {len(_lines)} 行: {_KEY_PROBE_DOC!r}\n"
        f"   ⇒ 丢文件尾巴的坏解析器对它没有尾巴可丢，会照样答对（round-3 复核的 HIGH）。"
    )
    assert _lines[-1].startswith("harness_tree:"), (
        f"⛔ 探针文档的**最后一行**必须是那个键，否则丢尾巴也丢不到它: {_lines!r}"
    )
    #: ⛔ 这里**不能**写 `_KEY_PROBE_DOC in CODE`：`literal_eval` 解出的是**真换行**，
    #: 而 CODE 里是源码形式的 `\n`（反斜杠 + n 两个字符）—— 那条断言必假（实测栽过）。
    #: 抽取本身的正确性由模块级的 `_KPROBE_M` 断言保证。这里改为核**源码形式**确实在写点里。
    assert '_KPROBE_DOC = "' in CODE, "⛔ 写点里找不到探针文档的赋值 —— 抽取正则漂了"


def _fake_yaml(_file_answer, *, _honest_probes: bool):
    """造一个负控输入用的假 `yaml` 模块（= 坏环境本身的形态，不是对被测代码的 mock）。

    `_honest_probes=False` ⇒ **恒返** `_file_answer`（r10 H1 的原形态：它连探针带文件
    一视同仁，正因为答案恰好是第一道探针要的 `{"a": 1}` 才混过去）。这类模块死在
    **键级探针**那一层 —— 它对一份只写着 `harness_tree` 的最简文档也给不出那个键。

    `_honest_probes=True` ⇒ 对生产的**两个探针输入**（`"a: 1"` 与 `_KEY_PROBE_DOC`）
    用真 PyYAML 老实回答，只对别的输入（= 用户那份 config）返 `_file_answer`。
    ⛔ 这一档存在的理由：不老实答探针的模块活不到词法否决那一层，于是词法否决就成了
    **门未覆盖的路径**。要测第二层，负控输入就得能通过第一层。

    ⛔ 按**内容**分辨而不是按类型：生产把 config 改成「先读原文、再 `safe_load(str)`」
    之后，探针与 config 都是 `str`，`isinstance(_stream, str)` 会把 config 也一起放行。
    """
    import yaml as _real_yaml

    _m = types.ModuleType("yaml")

    def _safe_load(_stream, *_a, **_kw):
        if _honest_probes and _stream in ("a: 1", _KEY_PROBE_DOC):
            return _real_yaml.safe_load(_stream)
        return _file_answer

    _m.safe_load = _safe_load
    return _m


#: config 的三种**合法书写形式** —— 生产都支持（见既有门 `..._noncanonical_key_form_is_honored`
#: 与 `..._no_pyyaml_refuses_whole_flow_document`），而词法正则只认得第一种。
_CFG_FORMS = {
    "bare": 'vault_id: "v"\nharness_tree: {t}\n',
    "quoted": 'vault_id: "v"\n"harness_tree": {t}\n',
    "flow": "{{vault_id: v, harness_tree: {t}}}\n",
    #: ⛔ 键与冒号之间有空白 —— 真 PyYAML 认（ledger 侧另有一格 `[键与冒号之间有空格]`
    #: 专门钉「必须认」），而生产正则靠 `[ \t]*` 才命中它。
    #: 没有这一格，把 `^harness_tree[ \t]*:` 缩成 `^harness_tree:` 会让 r10 H1 原样复活，
    #: 而 42 格 + ledger 165 格一格不红（人审替代轮 v2 HIGH，两镜头各自实测复现）。
    "spaced_before_colon": 'vault_id: "v"\nharness_tree : {t}\n',
}

_LYING_CASES = {
    # ── 第一层：键级探针。恒返式假模块一律死在这里，**与用户怎么写这份 config 无关** ──
    #: r10 H1 的原形态。
    "constant_bare": dict(honest=False, file={"a": 1}, form="bare", want="读不出本写点唯一关心的那个键"),
    #: ⛔ 本卡 round-1 复核抓到的**未被拦下的输入**之一：键带引号 ⇒ 词法正则行首不命中。
    "constant_quoted_key": dict(honest=False, file={"a": 1}, form="quoted", want="读不出本写点唯一关心的那个键"),
    #: ⛔ 同上之二：整份 flow mapping ⇒ 行首是 `{`，词法正则同样不命中。
    "constant_flow_mapping": dict(honest=False, file={"a": 1}, form="flow", want="读不出本写点唯一关心的那个键"),
    # ── 第二层：词法否决。对两个探针都老实、只对这份 config 说谎 ⇒ 活得到这一层 ──
    "honest_probes_empty_mapping": dict(honest=True, file={}, form="bare", want=_UNFAITHFUL_MARK),
    "honest_probes_list": dict(honest=True, file=["not", "a", "dict"], form="bare", want=_UNFAITHFUL_MARK),
    #: ⛔ 钉住词法正则的 `[ \t]*` 那一向（人审替代轮 v2 HIGH）：同样是「探针诚实、只对
    #: 这份 config 谎报无键」，只是 config 用**冒号前带空格**的合法写法。
    #: 正则一旦缩成 `^harness_tree:`，这一格是唯一会红的地方。
    "honest_probes_spaced_key": dict(honest=True, file={}, form="spaced_before_colon", want=_UNFAITHFUL_MARK),
}


@pytest.mark.parametrize("_case", sorted(_LYING_CASES))
def test_g33r2_harness_tree_lying_parser_is_refused(tmp_path, monkeypatch, _case):
    """⛔ 解析器说不出 config 里那个键 ⇒ **拒写**，不得静默回退父树。

    这是 T7-A r10 H1 的收口，**两层**：

    1. **键级探针**（`constant_*` 三格）：问「给它一份只写着 `harness_tree` 的最简文档，
       它给不给得出这个键」。这一层**不看用户的文件**，所以与书写形式无关。
       ⛔ 三格用的是三种**不同的合法书写形式**（裸键 / 带引号的键 / 整份 flow mapping）：
       收口的第一版只有词法否决，而词法问的是「文件里有没有**顶格裸键**」—— 后两种写法
       行首都不是 `harness_tree`，正则一条都不命中，恒返 `{"a": 1}` 的模块在它们下面
       **照样静默回退父树**（本卡 round-1 复核实测复现）。缺的又是**一个维度**：
       判据挂在了「用户怎么写」上，而不是「解析器能不能读出这个键」上。
    2. **词法否决**（`honest_probes_*` 两格）：假模块对两个探针都老实作答、只对用户这份
       config 说谎 ⇒ 它活得过第一层，于是第二层才谈得上被测到。

    ⛔ 收口只做**否决**，绝不**采用**词法命中的那个值：采用 = 逐行降级解析回潮，
    那条路被四轮同族缺陷打回过（见 SKILL.md `_harness_tree` docstring）。
    """
    _c = _LYING_CASES[_case]
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
    _target = _usable_tree(tmp_path / "target-tree")
    _raw = _CFG_FORMS[_c["form"]].format(t=_target)
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    #: ── 前提自证：这份 config **本来就是对的**（这一种写法真 PyYAML 认） ──
    #: 少了这一步，「被拒」可能只是因为文件本身有毛病，本门什么也没证明。
    import yaml as _real_yaml

    _truth = _real_yaml.safe_load(_raw)
    assert isinstance(_truth, dict) and str(_truth.get("harness_tree")) == str(_target), (
        f"⛔ 前提没成立({_case}): 真 PyYAML 对这份 {_c['form']} 写法的 config 给出的是 {_truth!r}, 目标树应是 {_target}"
    )

    monkeypatch.setitem(sys.modules, "yaml", _fake_yaml(_c["file"], _honest_probes=_c["honest"]))
    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "exit", (
        f"⛔ 解析器说不出这份 config 里的 harness_tree, `_harness_tree` 却返回了一棵树\n"
        f"   形态: {_case}（书写形式 {_c['form']}，解析器对这份 config 给出 {_c['file']!r}，"
        f"对两个探针是否老实={_c['honest']}）\n"
        f"   文件明文: {_raw!r}\n"
        f"   返回值: {_got[1]!r}  (父树 = {str(tmp_path)!r})\n"
        f"   ⇒ config 指着 {_target}, 系统却把学习事件记到了另一棵树的账本上。"
    )
    assert _c["want"] in _got[1], (
        f"⛔ 拒因须落在该落的那一层({_case} 期望含 {_c['want']!r}): {_got[1]!r}\n"
        f"   ⇒ 拒因跑到另一层 = 这一格实际测的不是它声称的那道判据。"
    )
    assert _HALFSTATE_MARK in _got[1], f"⛔ 拒因须带半态标记(既有半态白板分数保留、不回滚)({_case}): {_got[1]!r}"


#: 三种「那串字落在**某个值内部**」的合法文档 —— 嵌套深度递增。
#: 「那串字落在某个值内部」的三种合法文档 —— 本层**已知且接受**的误拒面。
_VALUE_NEST_FORMS = {
    "toplevel_scalar": 'note: "open\nharness_tree: /a/b"\n',
    "inside_a_list": 'items:\n  - "open\nharness_tree: /a/b"\n',
    "inside_a_nested_dict": 'outer:\n  inner: "open\nharness_tree: /a/b"\n',
}


@pytest.mark.parametrize("_form", sorted(_VALUE_NEST_FORMS))
def test_g33r2_harness_tree_lexical_veto_false_refusal_cost_is_accepted(tmp_path, _form):
    """⚠️ 这三格钉的是本层**已知且接受的代价**，不是「正确行为」。

    形态（真 PyYAML 解析完全正确、顶层确实没有这个键）：

        note: "open
        harness_tree: /a/b"

    值是一个**跨行的流式标量**，续行**可以顶格**，于是词法正则在第 2 行命中 ⇒ **被拒**。
    这是一次**误拒**。本门断言它确实发生，并说明为什么接受它。

    ⛔ **为什么不用「豁免」去修**（三次尝试，全部实测，留档给后人）：
      v1 豁免只看顶层 `_doc.values()`      → 嵌套一层的值仍被误拒；
      v2 遍历整棵结构 + 环防护             → round-2 复核抓到：它是**整份文档一个布尔**，
         只要已解析结果里任意一个字符串含那串字，否决就对文件里**每一处**（含真正的
         顶层 `harness_tree` 键）一起失效；一个**截断式解析器**（非敌意）配一份普通的
         自文档 config 就能静默绑父树（由 `..._truncating_parser_cannot_disarm_the_veto` 钉住）；
      v3 改按「处数」比                    → **修不了**：PyYAML 把双引号跨行标量的换行
         **折叠成空格**，误拒形态（顶格 1 处 / 值内子串 1 次）与缺陷形态（同样 1 / 1）
         **完全同构**，计数区分不了。
    根本原因：豁免要拿**解析器的输出**去决定要不要相信解析器，而解析器正是这一层唯一
    不可信的那一方 —— 换 `yaml.compose()` 的位置跨度也一样（它可以谎报跨度覆盖全文）。

    ⇒ 取舍：**误拒**是可见的拒绝、拒因指明行号、用户改一下写法就好；**豁免**带来的是
    **静默绑错树**，用户无从察觉。方向不同，接受前者。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)
    _raw = _VALUE_NEST_FORMS[_form]
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    #: 前提自证：① 词法正则确实命中；② 真 PyYAML 解析**成功**且顶层没有这个键
    #: （⇒ 这确实是一份合法文档，被拒确实是误拒，而不是文档本身有毛病）。
    import yaml as _real_yaml

    assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is not None, (
        f"⛔ 前提没成立({_form}): 词法正则对这份文本不命中 —— 那它连误拒都产生不了"
    )
    _truth = _real_yaml.safe_load(_raw)
    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
        f"⛔ 前提没成立({_form}): 真 PyYAML 给出的是 {_truth!r} —— 这份文档并不合法/并非无键"
    )

    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "exit", (
        f"⛔ 本门钉的是**已知代价**({_form})：这份合法文档应当被拒（可见的拒绝）。\n"
        f"   实得 {_got!r}。若这里变绿，多半是有人又加回了「值内豁免」——\n"
        f"   先读本门 docstring 里那三次尝试，再读 SKILL.md `_harness_tree` 的同段记录。"
    )
    assert _UNFAITHFUL_MARK in _got[1], f"⛔ 该落在词法否决那一层({_form}): {_got[1]!r}"
    assert "行明文写着" in _got[1], f"⛔ 误拒的拒因必须**指明是第几行**，否则用户无从知道该改哪里({_form}): {_got[1]!r}"


def _truncating_yaml(_n_lines):
    """**非敌意**的坏解析器：只读前 `_n_lines` 行（缓冲截断 / 流被提前关闭那一类事故）。

    ⛔ 它是坏环境的形态，不是对被测代码的 mock。两道探针（`"a: 1"` 与 `_KEY_PROBE_DOC`）
    都是**单行**文档，所以它照样答对 —— 于是活得过键级探针那一层，正好用来测词法否决。
    """
    import yaml as _real_yaml

    _m = types.ModuleType("yaml")

    def _safe_load(_stream, *_a, **_kw):
        return _real_yaml.safe_load("\n".join(str(_stream).splitlines()[:_n_lines]))

    _m.safe_load = _safe_load
    return _m


#: round-3 复核 H1 的三种形态 —— 截断解析器 + 三种**不同书写形式**。
#: 前两种词法正则行首不命中（`"harness_tree"` 以引号开头、`{...}` 以花括号开头），
#: 所以它们**只能**靠键级探针拦；第三种裸键两层都拦得住，放在一起是为了对照。
#: 每格 = (config 文本, 截断到第几行)。⛔ **截断行数必须按这份文本定**：
#: `flow_mapping` 只有 2 行，截断到 2 行等于没截断 —— 那一格会红在「前提没成立」，
#: 而不是红在被测判据上（实测栽过一次）。前提断言把这件事挡在了判据之前。
_TRUNCATING_FORMS = {
    "bare_key": ("vault_id: v\nnote: docs\nharness_tree: {t}\n", 2),
    "quoted_key": ('vault_id: v\nnote: docs\n"harness_tree": {t}\n', 2),
    "flow_mapping": ("# config\n{{harness_tree: {t}}}\n", 1),
}


@pytest.mark.parametrize("_form", sorted(_TRUNCATING_FORMS))
def test_g33r2_harness_tree_truncating_parser_is_refused(tmp_path, monkeypatch, _form):
    """⛔ round-3 复核的 HIGH：**丢文件尾巴**的坏解析器必须在键级探针层就被拦下。

    当时键级探针喂的是**单行**文档 `harness_tree: <哨兵>` —— 一整类丢尾巴的坏解析器
    （缓冲截断 / 流被提前关闭 / 只读前 N 行）对单行文档**没有尾巴可丢**，照样答对。
    它们过了这一层；而词法否决只认**顶格裸键**，`"harness_tree": v` 与 `{harness_tree: v}`
    行首都不是它 ⇒ 两层一起落空 ⇒ **静默回退父树**。

    整改：探针文档改成**三行、那个键在最后一行**。本门的三格就是当时的三种形态。
    ⚠️ **如实**：这只是把阈值从「1 行」推到「探针行数」，不是关门 —— 一个只读前 5 行的
    解析器仍能答对这份 3 行探针。根本限制在于探针永远是**另一份**文件。
    """
    _tmpl, _cut = _TRUNCATING_FORMS[_form]
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
    _target = _usable_tree(tmp_path / "target-tree")
    _raw = _tmpl.format(t=_target)
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    #: 前提自证：① 真 PyYAML 对这份 config 给出**真键**（文件本身没写错）；
    #: ② 截断解析器确实把那个键丢了（它确实在谎报无键）。
    import yaml as _real_yaml

    _truth = _real_yaml.safe_load(_raw)
    assert str(_truth.get("harness_tree")) == str(_target), f"⛔ 前提没成立({_form}): 真 PyYAML 给出 {_truth!r}"
    _bad = _truncating_yaml(_cut)
    assert "harness_tree" not in (_bad.safe_load(_raw) or {}), (
        f"⛔ 前提没成立({_form}): 截断到 {_cut} 行没把真键丢掉, 那它就不是这一格要的负控输入"
    )
    #: 前提自证②：它仍答得对**两道探针**（否则它活不到词法层，这一格就成了别的门的重复）。
    assert _bad.safe_load("a: 1") == {"a": 1}, f"⛔ 前提没成立({_form}): 截断器答不对第一道探针"

    monkeypatch.setitem(sys.modules, "yaml", _bad)
    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "exit", (
        f"⛔ 丢尾巴的解析器没被拦住({_form})：返回 {_got[1]!r}\n"
        f"   （父树 = {str(tmp_path)!r}，config 指着 {_target}）\n"
        f"   ⇒ round-3 复核的 HIGH 回潮了。多半是键级探针的文档又变回单行了 ——\n"
        f"     单行文档没有尾巴可丢，丢尾巴的解析器对它照样答得对。"
    )
    assert "读丢了文档的尾巴" in _got[1] or "读不出本写点唯一关心的那个键" in _got[1], (
        f"⛔ 该落在**键级探针**那一层({_form}): {_got[1]!r}\n   ⇒ 拒因跑到别层 = 这一格实际测的不是它声称的那道判据。"
    )


@pytest.mark.parametrize("_form", sorted(_TRUNCATING_FORMS))
def test_g33r2_harness_tree_truncating_forms_control_group(tmp_path, _form):
    """控制组：同样三种书写形式 + **真 PyYAML** ⇒ 照常采用 config 指的那棵树。

    ⛔ 少了这一格，上一门的「被拒」可能只是因为这三种写法本身生产就不支持 —— 那就
    证不到「差别在于解析器丢没丢尾巴」。两门唯一的变量就是解析器。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)
    _target = _usable_tree(tmp_path / "target-tree")
    _raw = _TRUNCATING_FORMS[_form][0].format(t=_target)
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))
    assert _got == ("ok", os.path.realpath(str(_target))), (
        f"⛔ 控制组不成立({_form}): 真 PyYAML 下这种合法写法也没被采用 ⇒ 上一门证不到因果: {_got!r}"
    )


def _tail_only_yaml(_n_lines):
    """**非敌意**的坏解析器：只解析**最后** `_n_lines` 行（丢头，不是丢尾）。

    ⛔ 它是 round-4 复核 L1 给的负控输入：对三行探针它只读到 `harness_tree: <哨兵>`，
    于是**那个键的校验照样通过** —— 唯一拦得住它的是探针对 `a` / `b` 两项的校验。
    """
    import yaml as _real_yaml

    _m = types.ModuleType("yaml")

    def _safe_load(_stream, *_a, **_kw):
        return _real_yaml.safe_load("\n".join(str(_stream).splitlines()[-_n_lines:]))

    _m.safe_load = _safe_load
    return _m


def test_g33r2_harness_tree_tail_only_parser_is_refused(tmp_path, monkeypatch):
    """⛔ 丢**头**的解析器也必须被拦 —— 拦它的是探针对前两行 `a` / `b` 的校验。

    round-4 复核 L1：删掉生产那两项校验后，当时的 15 格（含新增七格）**仍全部通过** ——
    因为所有既有负控都是「丢尾巴」形态，对它们来说末行的 `harness_tree` 才是关键，
    前两行是不是对的无所谓。⇒ `a` / `b` 那两项校验当时是**门未覆盖的路径**。

    本门补上它：一个只解析**最后一行**的解析器，对探针读到的正是
    `harness_tree: <哨兵>`（那个键的校验会过），只有 `a` / `b` 拦得住它。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
    _target = _usable_tree(tmp_path / "target-tree")
    _raw = f'"harness_tree": {_target}\nnote: docs\n'
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    import yaml as _real_yaml

    #: 前提自证（四条，缺一这一格就测不到它声称的判据）：
    _truth = _real_yaml.safe_load(_raw)
    assert str(_truth.get("harness_tree")) == str(_target), f"⛔ 前提没成立: 真 PyYAML 给出 {_truth!r}"
    _bad = _tail_only_yaml(1)
    assert "harness_tree" not in (_bad.safe_load(_raw) or {}), "⛔ 前提没成立: 丢头解析器没把真键丢掉"
    _probe_answer = _bad.safe_load(_KEY_PROBE_DOC)
    assert _probe_answer.get("harness_tree") == "__quiz_answer_key_probe__", (
        f"⛔ 前提没成立: 它对探针的**那个键**答错了 ⇒ 本格测的就不是 a/b 校验了: {_probe_answer!r}"
    )
    assert "a" not in _probe_answer and "b" not in _probe_answer, (
        f"⛔ 前提没成立: 它没丢掉探针的前两行 ⇒ a/b 校验拦不到它: {_probe_answer!r}"
    )

    monkeypatch.setitem(sys.modules, "yaml", _bad)
    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "exit", (
        f"⛔ 丢**头**的解析器没被拦住：返回 {_got[1]!r}（父树 = {str(tmp_path)!r}）\n"
        f"   ⇒ 多半是探针里对 `a` / `b` 的两项校验被删了 —— 那两项不是装饰，\n"
        f"     它们是唯一拦得住「丢头」这一类的判据。"
    )
    assert "读不出本写点唯一关心的那个键" in _got[1] or "读丢了文档的尾巴" in _got[1], (
        f"⛔ 该落在**键级探针**那一层: {_got[1]!r}"
    )


#: round-4 复核 L2 的负控输入：不是 `re.Pattern`，但把 `fullmatch` 委托给真正则 ——
#: 四条行为探针全过，只有形状层的 `isinstance(..., re.Pattern)` 拦得住它。
_VALIDATOR_STUB_WRAPPED_RE = (
    _VALIDATOR_STUB_OK.replace(
        "import re\n",
        "import re\n\n\nclass _W:\n"
        "    def __init__(self, r):\n        self._r = r\n"
        "    def fullmatch(self, s):\n        return self._r.fullmatch(s)\n",
        1,
    )
    .replace(
        "_TS_RE = re.compile(",
        "_TS_RE = _W(re.compile(",
        1,
    )
    .replace(
        '(?:\\.\\d+)?Z$")',
        '(?:\\.\\d+)?Z$"))',
        1,
    )
)


def test_g33r2_harness_contract_refuses_a_non_pattern_wrapper(tmp_path):
    """⛔ 名字在、行为对、但**不是编译正则** ⇒ 仍须拒（形状层）。

    round-4 复核 L2：删掉生产那两行 `isinstance(..., re.Pattern)` 检查后，当时的六格契约
    负控**仍全部通过** —— 因为它们拆的都是「行为」或「缺名字」，没有一格拆「类型对不对」。
    ⇒ 形状层的这一半是**门未覆盖的路径**。

    本门补上：一个把 `fullmatch` 委托给真正则的包装对象 —— 四条行为探针它全答得对，
    只有 `isinstance` 拦得住它。
    """
    assert _VALIDATOR_STUB_WRAPPED_RE != _VALIDATOR_STUB_OK, "⛔ 前提没成立: 变体与底本逐字相同"
    assert "_TS_RE = _W(re.compile(" in _VALIDATOR_STUB_WRAPPED_RE, "⛔ 前提没成立: 包装没生效"
    _repo = _fake_validator_tree(tmp_path / "wrapped-re-tree", _VALIDATOR_STUB_WRAPPED_RE)

    (_harness_contract,) = _extract("_harness_contract")
    _got = _outcome(_harness_contract, str(_repo))

    assert _got[0] == "exit", (
        f"⛔ 一个不是 `re.Pattern`、但 `fullmatch` 委托给真正则的对象通过了契约门: {_got[1]!r}\n"
        f"   ⇒ 多半是形状层的 `isinstance(..., re.Pattern)` 两行被删了。"
    )
    assert "不是编译正则" in _got[1], f"⛔ 该落在**形状层**: {_got[1]!r}"


def test_g33r2_harness_tree_truthful_parser_still_binds_alt_tree():
    """控制组：真 PyYAML + config 指向 alt 树 ⇒ 照常采用（词法否决没误伤正路）。"""
    import tempfile

    with tempfile.TemporaryDirectory() as _td:
        _root = Path(_td)
        _vd = _root / "canvas-vault"
        _vd.mkdir()
        _usable_tree(_root)
        _alt = _usable_tree(_root / "alt-harness")
        _raw = f'vault_id: "v"\nharness_tree: {_alt}\n'
        (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

        (_harness_tree,) = _extract("_harness_tree")
        _got = _outcome(_harness_tree, str(_vd))
        assert _got == ("ok", os.path.realpath(str(_alt))), (
            f"⛔ 真解析器给出了键, 就该采用那棵树({_alt}), 实得 {_got!r} —— 词法否决误伤了正路"
        )


def test_g33r2_harness_tree_real_list_document_falls_back():
    """控制组：config 文件**本来就是个列表**（真 PyYAML）⇒ 按「没写这个键」回退父树。

    ⛔ 这一格是 `parse_returns_junk` 的**正确场景**。原门用一个说谎的假模块制造
    「非 dict」，再断言「回退父树是对的」—— 那把错误结果固化成了期望：文件里明明
    写着目标树。「YAML 本身是列表 ⇒ 回退」这条语义要成立，文件就得真的是列表。
    """
    import tempfile

    with tempfile.TemporaryDirectory() as _td:
        _root = Path(_td)
        _vd = _root / "canvas-vault"
        _vd.mkdir()
        _usable_tree(_root)
        _raw = "- a\n- b\n"
        (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

        #: 前提自证：真 PyYAML 对这份文件确实给出一个 list，且文件里**没有** harness_tree 字面键。
        import yaml as _real_yaml

        assert isinstance(_real_yaml.safe_load(_raw), list), "⛔ 前提没成立: 这份 config 不是列表"
        assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is None, "⛔ 前提没成立: 文件里有 harness_tree 字面键"

        (_harness_tree,) = _extract("_harness_tree")
        _got = _outcome(_harness_tree, str(_vd))
        assert _got == ("ok", str(_root)), (
            f"⛔ 文件真的是列表(没有这个键)⇒ 应按「没写」回退父树 {str(_root)!r}, 实得 {_got!r}"
        )


# ══════════════════════════════════════════════════════════════════════════
# ② 契约：选中的树必须是本写点认识的那套 validate_learning_events
# ══════════════════════════════════════════════════════════════════════════
_CONTRACT_CASES = {
    "event_version_2": _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = 2"),
    "version_bool": _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = True"),
    "missing_name": _VALIDATOR_STUB_OK.replace("def _golden_manifest(*a, **kw):\n    return {}\n", ""),
    "ts_re_rejects_z": _VALIDATOR_STUB_OK.replace(
        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")',
        '_TS_RE = re.compile(r"^\\d{4}$")',
    ),
    #: round-3 复核 LOW-1：原表没有守住**形状层**（callable / 编译正则）的删除 ——
    #: 内存删掉生产那两段后五格负控结局全不变。这一格补上：名字在、但不是函数。
    "vault_id_of_not_callable": _VALIDATOR_STUB_OK.replace(
        'def _vault_id_of(p):\n    return "占位"\n',
        "_vault_id_of = None\n",
    ),
    "validate_accepts_scalar": _VALIDATOR_STUB_OK.replace(
        '    if not isinstance(record, dict):\n        return (["顶层必须是 JSON object"], [])\n',
        "",
    ),
    #: ⛔ 下面 5 格补的是**实测出来的门未覆盖的路径**（2026-09-19 变异探针，存档
    #: `evidence-harness-tree-r2/probe-uncovered-judges-20260919T043826.txt`）：
    #: 把生产里这 5 条判据逐条换成 `if False:`，349 格**一格不红** —— 它们当时完全没有
    #: 门看着。round-4 复核指过这个方向（「表里缺专属负控」）并补了 2 格，但**没人去数
    #: 还剩几条**，于是剩下这 5 条一直裸奔。⇒ 审查意见指出方向 ≠ 方向上的缺口都补完了。
    #:
    #: ⚠️ 注意 `ts_re_rejects_z`(旧) 与 `ts_re_accepts_bare_date`(新) 是同一个正则的
    #: **两向**判据：旧表只锁了「该认的认」，「该拒的拒」删掉没人知道。
    #: 契约是个**合取**（认该认的 ∧ 拒该拒的），门只测一半 ⇒ 一个恒返回 match 的假正则
    #: 能过掉所有旧格。`_WHOLE_SECOND_RE` 当时**两向都没门**，下面两格各补一向。
    "ts_re_accepts_bare_date": _VALIDATOR_STUB_OK.replace(
        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")',
        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}(?:T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z)?$")',
    ),
    "whole_second_re_rejects_whole_second": _VALIDATOR_STUB_OK.replace(
        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")',
        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d+Z$")',
    ),
    "whole_second_re_accepts_missing_seconds": _VALIDATOR_STUB_OK.replace(
        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")',
        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}(?::\\d{2})?Z$")',
    ),
    "classify_says_review_for_empty_frontmatter": _VALIDATOR_STUB_OK.replace(
        'def classify_card_state(fields):\n    return ("new", "占位")\n',
        'def classify_card_state(fields):\n    return ("review", "占位")\n',
    ),
    #: ⛔ 这一格刻意返回 `0` 而不是 `True`：生产判的是 `is not False`，
    #: 写成 `if _vle._looks_like_review_ext({}):` 的话 `0` 会被放行。
    #: 返回 `True` 两种写法都红 ⇒ 区分不出来；返回 `0` 才钉得住「用的是 `is not False`」。
    "looks_like_returns_zero_not_false": _VALIDATOR_STUB_OK.replace(
        "def _looks_like_review_ext(rec):\n    return False\n",
        "def _looks_like_review_ext(rec):\n    return 0\n",
    ),
}


@pytest.mark.parametrize("_case", sorted(_CONTRACT_CASES))
def test_g33r2_harness_contract_refuses(tmp_path, _case):
    """⛔ 选中的树不是本写点认识的那套 validator ⇒ **拒写**，不得静默按它的语义写账本。

    收口前：写点从 `REPO` 无条件 `from validate_learning_events import <7 个名字>`，
    除「导得进」外零判据。于是任意旧版/异版 harness 分发都会被采用 —— T7-A 已实测
    的反例就是本仓 `b85a168a` 那棵旧树（`_vault_id_of` 是另一套实现，账本照写）。

    每格只拆**一项**（版本 / 名字 / 正则语义 / 纯函数行为），其余全对 ⇒ 红了就一定
    是那一项被抓住的，不是「随便哪里坏了都会红」。
    """
    _body = _CONTRACT_CASES[_case]
    assert _body != _VALIDATOR_STUB_OK, f"⛔ 前提没成立: {_case} 的占位 validator 与全对底本逐字相同 = 没拆到东西"
    _repo = _fake_validator_tree(tmp_path / f"tree-{_case}", _body)

    (_harness_contract,) = _extract("_harness_contract")
    _got = _outcome(_harness_contract, str(_repo))

    assert _got[0] == "exit", f"⛔ 契约被拆了一项({_case}) 却照常放行 —— 写点会按这棵树的语义写账本: {_got[1]!r}"
    assert ("契约不符" in _got[1]) or ("不是选中的树" in _got[1]), f"⛔ 拒因须点名契约({_case}): {_got[1]!r}"
    assert _HALFSTATE_MARK in _got[1], f"⛔ 契约拒因须带半态标记({_case}): {_got[1]!r}"


def test_g33r2_harness_contract_refuses_shadowed_module(tmp_path, monkeypatch):
    """⛔ `sys.modules` 里先坐着一个同名模块 ⇒ 拒（影子门）。

    树选对了不等于**导进来的就是那棵树的**：`sys.modules` 先到先得，一个早于本写点
    被 import 的同名模块会让 `sys.path.insert` 完全失效，而 7 个名字照样导得到。
    """
    _repo = _real_harness(tmp_path / "real-tree")
    _elsewhere = _fake_validator_tree(tmp_path / "elsewhere", _VALIDATOR_STUB_OK)
    _shadow = types.ModuleType("validate_learning_events")
    _shadow.__file__ = str(_elsewhere / "backend" / "scripts" / "validate_learning_events.py")
    _shadow.EVENT_VERSION = 1
    monkeypatch.setitem(sys.modules, "validate_learning_events", _shadow)

    (_harness_contract,) = _extract("_harness_contract")
    _got = _outcome(_harness_contract, str(_repo))

    assert _got[0] == "exit", f"⛔ 导进来的是别处那一份, 却照常放行: {_got[1]!r}"
    assert "不是选中的树" in _got[1], f"⛔ 影子拒因须说清来源不对: {_got[1]!r}"
    assert str(_elsewhere) in _got[1], f"⛔ 影子拒因须报出**实际**来源路径, 否则用户无从查: {_got[1]!r}"


def test_g33r2_harness_contract_accepts_real_tree(tmp_path):
    """控制组：validator 是 symlink → 主干那一份的真树 ⇒ 返回 7 元组。

    ⛔ 本格同时守着「影子判据比 `abspath` 不比 `realpath`」：这棵树合法，但它的
    validator 物理上就在主干树里 —— 比 realpath 会把它判成影子，控制组当场红。
    """
    _repo = _real_harness(tmp_path / "real-tree")

    (_harness_contract,) = _extract("_harness_contract")
    _got = _outcome(_harness_contract, str(_repo))

    assert _got[0] == "ok", f"⛔ 控制组不成立: 真树被契约门拒了 ⇒ 上面那些拒绝证不到是契约抓的: {_got[1]!r}"
    _names = _got[1]
    assert isinstance(_names, tuple) and len(_names) == 7, f"⛔ 应返回 7 个名字, 实得 {_names!r}"

    import validate_learning_events as _vle

    assert _names[6] is _vle._TS_RE, "⛔ 返回的 `_TS_RE` 不是选中那棵树里的那一个"
    assert os.path.dirname(os.path.abspath(_vle.__file__)) == os.path.join(str(_repo), "backend", "scripts"), (
        f"⛔ 前提没成立: 导进来的 validator 不在选中的树里 ({_vle.__file__})"
    )


# ══════════════════════════════════════════════════════════════════════════
# ③ 半态：Step 2.9 预检先拒后写（subprocess 真跑，零 mock）
# ══════════════════════════════════════════════════════════════════════════
def _preflight_block() -> str:
    """把 Step 2.9 预检块从 SKILL.md **逐字**抽出来（第 2 个 PYEOF 块）。"""
    _pf = [b for b in _ALL_BLOCKS if "quiz-answer/preflight" in b]
    assert len(_pf) == 1, (
        f"⛔ SKILL.md 里应恰有 1 个 Step 2.9 预检块(含 `quiz-answer/preflight` 标记), 实见 {len(_pf)}"
        " —— 改前红在这里属预期(还没加 Step 2.9)"
    )
    return _pf[0]


def _preflight_vault(root: Path) -> Path:
    """在 `tmp_path` 下搭一个标准布局 vault，把主干 SKILL.md 复制进去。"""
    _vd = root / "canvas-vault"
    _sk = _vd / ".claude" / "skills" / "quiz-answer"
    _sk.mkdir(parents=True)
    shutil.copy(SKILL, _sk / "SKILL.md")
    (_vd / "节点").mkdir()
    (_vd / "节点" / "概念.md").write_text("# 概念\n", encoding="utf-8")
    return _vd


def _pycache_dirs(root: Path) -> list:
    """`root` 下所有 `__pycache__` 目录 —— 「纯读零写」里最容易漏掉的那一种写。"""
    return sorted(str(_p.relative_to(root)) for _p in root.rglob("__pycache__"))


def _run_preflight(_vd: Path, _env_extra: dict) -> subprocess.CompletedProcess:
    """按**真实用户环境**跑预检。

    ⛔ 这里**显式删掉** `PYTHONDONTWRITEBYTECODE`（round-2 复核 MEDIUM）：本函数原先把它
    设成 `"1"`，理由写的是「否则 import validator 会在 fixture 树里落 `__pycache__`，零写
    断言当场自毁」—— 那句话把因果说反了。真实用户跑 `/quiz-answer` 时环境里**没有**这个
    变量，所以那条落盘路径是真实存在的，而这道门恰好把它关掉了 ⇒ **门未覆盖的路径**。
    现在改成：门按真实环境跑，由**预检块自己** `sys.dont_write_bytecode = True` 去保证
    零写 —— 声称是它作出的，保证也该由它给。
    """
    _env = dict(os.environ)
    _env.pop("PYTHONDONTWRITEBYTECODE", None)
    _env["QUIZ_ANSWER_NODE"] = str(_vd / "节点" / "概念.md")
    _env.update(_env_extra)
    return subprocess.run(
        [sys.executable, "-"],
        input=_preflight_block(),
        env=_env,
        capture_output=True,
        text=True,
        cwd=str(_vd),
        timeout=120,
    )


def _write_face(root: Path) -> set:
    """vault 下每个文件的 (相对路径, 大小, mtime_ns) —— 零写断言的比较面。"""
    _face = set()
    for _p in sorted(root.rglob("*")):
        if _p.is_file():
            _st = _p.stat()
            _face.add((str(_p.relative_to(root)), _st.st_size, _st.st_mtime_ns))
    return _face


_PREFLIGHT_REFUSALS = ("no_pyyaml", "bad_tree", "contract_broken")


@pytest.mark.parametrize("_case", _PREFLIGHT_REFUSALS)
def test_g33r2_preflight_refuses_before_step3(tmp_path, _case):
    """⛔ Step 2.9 预检在 **Step 3 写分之前** 就拒，且**一个字节都不写**。

    收口前的顺序是：Step 3 用 `Edit` 写分 + 置 `scored_pending_node_update` →
    Step 4 主写点建锁 → 才发现拿不到 PyYAML ⇒ 拒。白板就停在「已记分、节点未更新」
    这个半态上（UAT #23）。用户看到的是一个记了分却没更新的检验白板，而真正的原因
    （装错了解释器）只出现在一段早已滚过去的 stderr 里。

    ⛔ 「不写」是本门的承重断言，不是「rc≠0 就算」：预检若顺手建了锁 / 落了
    `__pycache__` / 起了 payload 暂存，它就不再是**纯读**的前置检查，放在 Step 3
    之前反而多了一处可失败的写。
    """
    _vd = _preflight_vault(tmp_path)
    _env_extra: dict = {}

    if _case == "no_pyyaml":
        #: 负控输入 = 坏环境的形态：`PYTHONPATH` 前置一个导入即抛的同名 `yaml.py`。
        _stub = tmp_path / "no-yaml"
        _stub.mkdir()
        (_stub / "yaml.py").write_text('raise ImportError("本机没有装 PyYAML")\n', encoding="utf-8")
        _env_extra["PYTHONPATH"] = str(_stub)
        _repo = _real_harness(tmp_path / "harness")
        (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")
        _want = _NO_YAML_REFUSAL
    elif _case == "bad_tree":
        (_vd / ".canvas-config.yaml").write_text(
            f"harness_tree: {tmp_path / 'this-tree-does-not-exist'}\n", encoding="utf-8"
        )
        _want = "指向不存在的树"
    else:  # contract_broken
        _repo = _fake_validator_tree(
            tmp_path / "broken-harness",
            _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = 2"),
        )
        (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")
        _want = "契约不符"

    _face0 = _write_face(_vd)
    _r = _run_preflight(_vd, _env_extra)

    assert _r.returncode != 0, (
        f"⛔ 预检放行了({_case}) ⇒ 流程会往 Step 3 写分, 半态白板照旧: stdout={_r.stdout[-400:]!r}"
    )
    assert _want in _r.stderr, f"⛔ 拒因须点名「{_want}」({_case}): {_r.stderr[-600:]!r}"
    assert _HALFSTATE_MARK in _r.stderr, (
        f"⛔ 拒因须带半态标记(既有半态白板分数保留、不回滚)({_case}): {_r.stderr[-600:]!r}"
    )
    assert _write_face(_vd) == _face0, f"⛔ 预检是纯读的前置检查, 拒绝时写入面必须逐字节不变({_case})"
    assert not (_vd / ".locks").exists(), f"⛔ 预检不得建锁({_case}) —— 锁是主写点 Step 4 的事"
    assert _pycache_dirs(tmp_path) == [], (
        f"⛔ 预检落了字节码({_case}): {_pycache_dirs(tmp_path)}\n"
        f"   ⇒ 「纯读零写」的声称不成立。本门按**真实用户环境**跑（不设 PYTHONDONTWRITEBYTECODE），"
        f"该由预检块自己 `sys.dont_write_bytecode = True` 保证。"
    )


def test_g33r2_preflight_refuses_without_node_env(tmp_path):
    """⛔ 环境变量没传进来 ⇒ 给一句话拒因，不是一段 traceback。

    预检整个的价值就在于「把拒绝说清楚」——用户看到 `KeyError: 'QUIZ_ANSWER_NODE'`
    是学不到任何东西的，而这恰恰是最容易发生的一种失败（prose 里那行 `QUIZ_ANSWER_NODE=…`
    被漏抄了）。
    """
    _vd = _preflight_vault(tmp_path)
    _env = dict(os.environ)
    _env.pop("PYTHONDONTWRITEBYTECODE", None)  # 真实用户环境，见 `_run_preflight` 的 docstring
    _env.pop("QUIZ_ANSWER_NODE", None)
    _face0 = _write_face(_vd)
    _r = subprocess.run(
        [sys.executable, "-"],
        input=_preflight_block(),
        env=_env,
        capture_output=True,
        text=True,
        cwd=str(_vd),
        timeout=120,
    )

    assert _r.returncode != 0, f"⛔ 环境变量没传却放行了: {_r.stdout[-300:]!r}"
    assert "QUIZ_ANSWER_NODE" in _r.stderr, f"⛔ 拒因须点名是哪个环境变量没传: {_r.stderr[-400:]!r}"
    assert "Traceback" not in _r.stderr, (
        f"⛔ 这条路径吐了 traceback 而不是一句话拒因 —— 多半是 `os.environ[…]` 下标写法: {_r.stderr[-400:]!r}"
    )
    assert _write_face(_vd) == _face0, "⛔ 拒绝时写入面必须逐字节不变"


def test_g33r2_preflight_passes_on_a_good_vault(tmp_path):
    """控制组：库在、树在、契约对 ⇒ 预检 rc=0 并报出选中的树。

    少了这一半，上面那三格「被拒」可能只是因为预检块本身压根跑不起来。
    """
    _vd = _preflight_vault(tmp_path)
    _repo = _real_harness(tmp_path / "harness")
    (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")

    _r = _run_preflight(_vd, {})

    assert _r.returncode == 0, f"⛔ 控制组不成立: 好 vault 也被预检拒了: {_r.stderr[-600:]!r}"
    assert "契约 ok" in _r.stdout, f"⛔ 预检通过时应报出结论: {_r.stdout!r}"
    assert os.path.realpath(str(_repo)) in _r.stdout, (
        f"⛔ 预检应报出**选中的那棵树**, 否则用户无从确认它找对了本子: {_r.stdout!r}"
    )
    #: ⛔ 控制组这一格才是最会落盘的：它一路走到 `import validate_learning_events`。
    #: 按真实用户环境跑（`_run_preflight` 已删掉 PYTHONDONTWRITEBYTECODE）⇒ 若预检块
    #: 自己没把字节码关掉，这里会在 harness 树里看到 `__pycache__`。
    assert _pycache_dirs(tmp_path) == [], (
        f"⛔ 预检**通过**这条路上落了字节码: {_pycache_dirs(tmp_path)}\n"
        f"   ⇒ 「纯读零写」的声称不成立（这一格一路走到 import validator，最容易暴露）。"
    )


# ══════════════════════════════════════════════════════════════════════════
# ④ 结构门：Step 2.9 的位置与块序（(e)⑤）
# ══════════════════════════════════════════════════════════════════════════
def test_g33r2_step29_precedes_step3():
    """⛔ `## Step 2.9` 必须排在 `## Step 3` **之前** —— 否则「先拒后写」就是空话。

    本门钉的是**顺序**这个性质本身：预检块写得再对，排在写分之后也救不了半态白板。
    """
    _lines = _SKILL_TEXT.splitlines()
    _s29 = [i for i, ln in enumerate(_lines, 1) if ln.startswith("## Step 2.9")]
    _s3 = [i for i, ln in enumerate(_lines, 1) if ln.startswith("## Step 3 ·")]
    assert len(_s29) == 1, f"⛔ SKILL.md 应恰有 1 个 `## Step 2.9` 标题, 实见 {len(_s29)} —— 改前红在这里属预期"
    assert len(_s3) == 1, f"⛔ SKILL.md 应恰有 1 个 `## Step 3 ·` 标题, 实见 {len(_s3)}"
    assert _s29[0] < _s3[0], f"⛔ Step 2.9 在 :{_s29[0]}、Step 3 在 :{_s3[0]} —— 预检排在写分之后 = 半态照旧"


def test_g33r2_preflight_block_precedes_step3():
    """⛔ **可执行的那个块本身**必须排在 Step 3 的写分指令之前 —— 不是只有标题。

    round-5 复核在这里抓到一个**门未覆盖的路径**：把预检的 fenced block 单独挪到 Step 3
    指令之后（`## Step 2.9` 标题留在原地），当时的两道结构门**都 PASS** ——
      · `..._step29_precedes_step3` 测的是「`## Step 2.9` **标题**的行号」；
      · `..._preflight_is_the_second_pyeof_block_…` 测的是「在 PYEOF 序列里的**序号**」。
    标题在前、块在后，「先拒后写」当场失效，而两道门都看不见。⇒ 缺的是**块自己的位置**。

    本门把三样东西钉在一条线上：`## Step 2.9` 标题 < 预检 fence < `## Step 3 ·` 标题。
    中间那一条是新的；两头那两条顺带保证标题没有脱离它描述的块。
    """
    _text = _SKILL_TEXT
    _i_title = _text.index("## Step 2.9")
    _i_step3 = _text.index("## Step 3 · ")
    _fence = "```bash\nQUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF'\n"
    assert _text.count(_fence) == 1, f"⛔ 预检 fence 应恰 1 处, 实见 {_text.count(_fence)}"
    _i_block = _text.index(_fence)

    def _line(_o):
        return _text[:_o].count("\n") + 1

    assert _i_title < _i_block, (
        f"⛔ `## Step 2.9` 标题（行 {_line(_i_title)}）排在预检块（行 {_line(_i_block)}）之后 —— 标题脱离了它描述的块。"
    )
    assert _i_block < _i_step3, (
        f"⛔ **预检块本身**在行 {_line(_i_block)}，而 `## Step 3 ·` 在行 {_line(_i_step3)} ——"
        f" 块排在写分指令之后，「先拒后写」失效。\n"
        f"   ⚠️ 只看标题位置的门看不见这个：标题可以留在原地而块被挪走"
        f"（round-5 复核实测两道旧门在这种形态下都 PASS）。"
    )
    #: 顺带钉住块**确实是预检块**——否则上面三条比的可能是另一个 fence。
    assert "quiz-answer/preflight" in _text[_i_block : _i_block + 4000], (
        "⛔ 那个 fence 之后的内容里没有 `quiz-answer/preflight` 标记 —— 比错块了"
    )


def test_g33r2_preflight_is_the_second_pyeof_block_and_main_stays_single():
    """⛔ 预检块是文件第 2 个 PYEOF 块，且主写点块仍**恰 1** 个。

    `_MAIN_BLOCKS` 的过滤器（`P = "/tmp/quiz-answer-payload.json"`）是 test_g3_2 的
    夹具基石：预检块若含那个字面量，那边 collect 当场 ERROR。本门在这一侧钉住它。

    ⛔ 同理，预检块不得含 `def _harness_tree(` 字面量 —— 它自己要按这个串去定位
    主块，写成字面量的话「含该锚的块恰 1」当场自指失效（块序判据变成恒真）。
    """
    assert len(_MAIN_BLOCKS) == 1, f"⛔ 主写点块应恰 1, 实见 {len(_MAIN_BLOCKS)}"
    assert len(_ALL_BLOCKS) == 3, (
        f"⛔ SKILL.md 应有 3 个 PYEOF 块(A3 增量 / Step 2.9 预检 / 主写点), 实见 {len(_ALL_BLOCKS)}"
    )

    _pf = _preflight_block()
    assert _ALL_BLOCKS[1] is _pf, "⛔ 预检块应是文件第 2 个 PYEOF 块(A3 增量第 1、主写点第 3)"
    assert 'P = "/tmp/quiz-answer-payload.json"' not in _pf, (
        "⛔ 预检块含主块过滤字面量 ⇒ test_g3_2 夹具 collect 会 ERROR"
    )
    assert "/tmp" not in _pf, "⛔ 预检块不得出现 `/tmp` —— 会动 lint 的 `tmp_all` 基线与块指纹集合"
    assert "def _harness_tree(" not in _pf, "⛔ 预检块含定位锚字面量 ⇒ 它自己也会命中, 自指失效"
    assert "fsrs_bridge" not in _pf, "⛔ 预检块不得 import `fsrs_bridge`(零写者 vault 脚本, 与选树无关)"

    _anchored = [b for b in _ALL_BLOCKS if "def _harness_tree(" in b]
    assert len(_anchored) == 1, f"⛔ 含 `def _harness_tree(` 的块应恰 1(预检块靠它定位), 实见 {len(_anchored)}"


# ══════════════════════════════════════════════════════════════════════════
# ⑤ 门未覆盖的路径（2026-09-19 变异探针实测补齐）
# ══════════════════════════════════════════════════════════════════════════
#: 手法：把生产里每一条判据的条件逐个换成 `if False:`（= 让它永不拒绝，语法与函数体
#: 一字不动），看 349 格里有没有任何一格会红。红 ⇒ 有门看着；全绿 ⇒ 这条判据现在
#: 删掉也没人知道。存档 `evidence-harness-tree-r2/probe-uncovered-judges-20260919T043826.txt`
#: （同目录 …T043255.txt 是**作废**的第一版，头部写了它为什么假绿）。
#:
#: ⚠️ 该手法对**控制流型**判据（决定要不要执行某段）不适用：换成 `False` 会抽掉后续
#: 代码的前提，红成一片（`tree-cf-is-none` 35 格、`tree-not-tree` 121 格），
#: 那种红不构成「有门看着这条判据」，只证明代码崩了。下面两格补的是**校验/补全型**
#: 的两条真缺口。


def _needs_trailing_newline_yaml():
    """要求文档以换行结尾的坏解析器 —— 没有结尾换行就给 `None`。

    ⛔ 它是**坏环境本身的形态**，不是对被测代码的 mock：流式读取器把最后一行没有换行的
    内容当作不完整记录丢掉，是真实存在的事故形态。

    关键在于它**只**在第一道探针上出错：
      · 第一道探针的输入是 `"a: 1"` —— **没有**结尾换行 ⇒ 它给 `None`；
      · 键级探针的输入 `_KPROBE_DOC` 以换行结尾 ⇒ 它老实回答。
    """
    import yaml as _real_yaml

    _m = types.ModuleType("yaml")

    def _safe_load(_stream, *_a, **_kw):
        _s = str(_stream)
        if not _s.endswith("\n"):
            return None
        return _real_yaml.safe_load(_s)

    _m.safe_load = _safe_load
    return _m


def test_g33r2_first_probe_catches_what_the_key_probe_cannot(tmp_path, monkeypatch):
    """⛔ 第一道通用探针有一个**未被键级探针接替**的观测点，本格是它唯一的门。

    实测（2026-09-19）：把第一道探针的 `_probe.get("a") == 1` 判据换成 `if False:`，
    349 格**一格不红**。当时第一反应是「它冗余了 —— 键级探针的文档含 `a: 1` 且校验
    `a == 1`，把它的活全接了」。**那只对了一半**：键级探针的文档是三行、**以换行结尾**的，
    它验不到「解析器对一份**没有结尾换行的单行文档**怎么处理」。

    ⇒ 覆盖归属必须逐条列**未被接替的观测点**，不能只说「归到哪」——
      「A 的职责被 B 接了」这句话，要能撑住得先证明 A 的每个观测点 B 都看得到。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
    _target = _usable_tree(tmp_path / "target-tree")
    (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_target}\n", encoding="utf-8")

    _bad = _needs_trailing_newline_yaml()

    #: 前提自证（三条，缺一这格就不是在测它声称的东西）
    assert _bad.safe_load("a: 1") is None, "⛔ 前提没成立: 它对第一道探针的输入并没有出错"
    assert _bad.safe_load(_KEY_PROBE_DOC) == {
        "a": 1,
        "b": 2,
        "harness_tree": "__quiz_answer_key_probe__",
    }, "⛔ 前提没成立: 它对键级探针答错了 ⇒ 这格测的就不是「第一道探针独有」那个观测点了"
    assert _KEY_PROBE_DOC.endswith("\n"), "⛔ 前提没成立: 键级探针文档不以换行结尾 ⇒ 两道探针在这一点上没差别, 本格空转"

    monkeypatch.setitem(sys.modules, "yaml", _bad)
    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "exit", (
        f"⛔ 第一道探针没拦住它 —— 而键级探针也拦不住(前提已证它答得对) ⇒ 会径直走到读 config。\n"
        f"   实得 {_got!r}(父树 = {tmp_path}, config 指着 {_target})"
    )
    assert "PyYAML 不可用" in _got[1], f"⛔ 该落在「拿不到 PyYAML」那一层: {_got[1]!r}"
    assert "对 'a: 1' 给出的是" in _got[1], f"⛔ 拒因必须点名**第一道探针**, 否则别的层红了这格也算过: {_got[1]!r}"


def test_g33r2_relative_harness_tree_is_resolved_against_the_vault(tmp_path):
    """⛔ config 写**相对路径**时必须相对 vault 目录补全，本格是这条判据唯一的门。

    实测（2026-09-19）：把 `if not os.path.isabs(_given):` 换成 `if False:` 后
    349 格一格不红 —— 补全这一步当时完全没有门看着。

    ⚠️ 删掉它的后果**不是报错**，是解析基准悄悄从 vault 目录换成**进程 CWD**：
    同一份 config 在不同工作目录下指向不同的树。而 `quiz-answer` 是被别处调起来的，
    CWD 不由用户控制 —— 这正是本卡反复在防的那类「静默绑错树」。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _usable_tree(tmp_path)  # 父树可用 ⇒ 回退也会「成功」
    _alt = _usable_tree(_vd / "alt-tree")  # 相对 vault 的目标树
    (_vd / ".canvas-config.yaml").write_text("harness_tree: alt-tree\n", encoding="utf-8")

    #: 前提自证：这个相对路径**不能**恰好在 CWD 下也解析得通，否则两种基准给同一答案
    assert not os.path.isdir(os.path.join(os.getcwd(), "alt-tree", "backend", "scripts")), (
        f"⛔ 前提没成立: CWD({os.getcwd()}) 下也有一棵 alt-tree ⇒ 两种基准同答案, 本格证不到东西"
    )

    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "ok", f"⛔ 相对路径应被补全后接受, 实得: {_got!r}"
    assert _got[1] == os.path.realpath(_alt), (
        f"⛔ 补全基准错了 —— 期望相对 vault 目录({_vd})解析到 {os.path.realpath(_alt)}, 实得 {_got[1]!r}"
    )


def test_g33r2_lexical_veto_does_not_over_match_a_similar_key(tmp_path):
    """⛔ 词法否决**不得过宽**：`harness_tree_backup:` 不是 `harness_tree:`。

    这一格钉的是生产正则**末尾那个冒号**。把 `^harness_tree[ \t]*:` 写成 `^harness_tree`
    （少一个字符，而且是「简化正则」这类清理里最常见的一种）之后：
    一份完全合法、真 PyYAML 解析正确、顶层**只有** `harness_tree_backup` 的 config
    会命中词法正则 ⇒ 而解析结果里确实没有 `harness_tree` 键 ⇒ **误拒**。

    ⚠️ 本格与 `..._lexical_veto_false_refusal_cost_is_accepted` 三格的区别：
    那三格钉的是**已接受的**误拒（那串字确实以顶格形式出现在文件里）；
    这一格钉的是**不该有的**误拒（文件里根本没有那个键，只有一个名字以它开头的**别的键**）。
    两者都期望某个结局，但含义相反 —— 所以不能合并。

    ⚠️ 为什么 2026-09-19 的覆盖实测没抓到这一向：那次把 15 条 `if` 判据换 `if False:`，
    而 `_lex = re.search(...)` 是**赋值语句**，判据内容在赋值右侧，那套枚举够不着。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _parent = _usable_tree(tmp_path)  # 没有 harness_tree 键 ⇒ 正确行为是回退到它
    _raw = 'vault_id: "v"\nharness_tree_backup: /nowhere/at/all\n'
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    #: 前提自证（两条）：① 真 PyYAML 解析成功且顶层**没有** harness_tree；
    #: ② 但它确实有一个**名字以它开头**的别的键 —— 否则这一格测不到「过宽」。
    import yaml as _real_yaml

    _truth = _real_yaml.safe_load(_raw)
    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
        f"⛔ 前提没成立: 真 PyYAML 给出 {_truth!r} —— 这份 config 顶层不该有 harness_tree"
    )
    assert any(k.startswith("harness_tree") for k in _truth), (
        f"⛔ 前提没成立: 没有以 harness_tree 开头的别的键 ⇒ 本格测不到「否决过宽」: {_truth!r}"
    )

    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "ok", (
        "⛔ 词法否决**过宽**了：文件里根本没有 harness_tree 键，只有一个名字以它开头的\n"
        f"   别的键（harness_tree_backup），却被当成「解析结果与文件内容不符」拒掉。\n"
        f"   实得 {_got!r}\n"
        "   ⇒ 多半是生产正则末尾的 `:` 被去掉了（`^harness_tree[ \\t]*:` → `^harness_tree`）。"
    )
    assert _got[1] == os.path.realpath(_parent), (
        f"⛔ 没有 harness_tree 键时应回退父目录 {os.path.realpath(_parent)}, 实得 {_got[1]!r}"
    )


#: 词法正则 `^harness_tree[ \t]*:` 的**第三个**承重 token：行首锚 `^`。
#: 这三份 config 都含 `harness_tree:` 字样，但**都不在行首**，真 PyYAML 顶层也都没有该键
#: ⇒ 正确行为是**回退父树**（`ok`），不是拒。
#: ⛔ 第一种正是本写点 docstring **明文承诺**的那一句：「注释掉的 `# harness_tree:` 不顶格
#: ⇒ 正则不命中, 也照旧回退」—— 在本格之前，那是一条**零门的行为契约**。
_NON_ANCHORED_FORMS = {
    "commented_out": '# harness_tree: /old/tree\nvault_id: "v"\n',
    "inline_comment": 'vault_id: "v"   # 想换树就改 harness_tree: 这一项\n',
    "indented_nested": 'nested:\n  harness_tree: /a/b\nvault_id: "v"\n',
}


@pytest.mark.parametrize("_form", sorted(_NON_ANCHORED_FORMS))
def test_g33r2_lexical_veto_requires_the_line_start_anchor(tmp_path, _form):
    """⛔ 词法否决只认**顶格**：那串字出现在注释里/缩进里，不构成「文件明文写着这个键」。

    人审替代轮 v3 的发现：生产正则三个承重 token（`^` / `[ \t]*` / 末尾 `:`）里，
    前一轮给后两个各补了一格，**`^` 一个门都没有** —— 删掉它 358 个 nodeid 一格不红。

    ⚠️ 与 `..._lexical_veto_false_refusal_cost_is_accepted` 三格的区别（不能合并）：
    那三格里那串字**确实以顶格形式**出现在文件中，被拒是**已接受的代价**；
    这三格里它**不在行首**，被拒就是**不该有的**误拒。两边都断言某个结局，含义相反。

    ⚠️ 与 `..._does_not_over_match_a_similar_key` 的区别：那格钉**末尾冒号**
    （`harness_tree_backup:` 不是 `harness_tree:`），这格钉**行首锚**。

    ⛔ 定级如实：删掉 `^` 的后果是否决**多发**（可见的误拒），不是**漏发**（静默绑错树）——
    `re.search` 去掉 `^` 是匹配集的严格超集，而 `_lex` 只进
    `if _lex and (key not in _doc): raise`，所以 r10 H1 的复活路径结构上到不了这里。
    这与 `[ \t]*` 那一向**不对称**：那个删掉是收窄 ⇒ 漏发 ⇒ 静默绑错树。
    ⇒ 「这条判据没有门」不足以定级，要问**它坏掉时系统往哪个方向坏**。
    """
    _vd = tmp_path / "canvas-vault"
    _vd.mkdir()
    _parent = _usable_tree(tmp_path)  # 没有顶层 harness_tree 键 ⇒ 正确行为是回退到它
    _raw = _NON_ANCHORED_FORMS[_form]
    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")

    #: 前提自证（三条）：① 真 PyYAML 解析成功且顶层**没有** harness_tree；
    #: ② 文本里**确实含**那串字（否则本格与 `^` 无关，测的是别的东西）；
    #: ③ 但它**不在任何一行的行首**（否则它属于「已接受的误拒面」，期望应当相反）。
    import yaml as _real_yaml

    _truth = _real_yaml.safe_load(_raw)
    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
        f"⛔ 前提没成立({_form}): 真 PyYAML 给出 {_truth!r} —— 顶层不该有 harness_tree"
    )
    assert "harness_tree:" in _raw, f"⛔ 前提没成立({_form}): 文本里没有那串字 ⇒ 本格与行首锚无关"
    assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is None, (
        f"⛔ 前提没成立({_form}): 它顶格命中了 ⇒ 属「已接受的误拒面」, 本格的期望应当相反"
    )

    (_harness_tree,) = _extract("_harness_tree")
    _got = _outcome(_harness_tree, str(_vd))

    assert _got[0] == "ok", (
        f"⛔ 词法否决把**非顶格**出现的那串字当成了「文件明文写着这个键」({_form})。\n"
        f"   文件: {_raw!r}\n   实得 {_got!r}\n"
        "   ⇒ 多半是生产正则的行首锚 `^` 被删了（`^harness_tree[ \\t]*:` → `harness_tree[ \\t]*:`）。"
    )
    assert _got[1] == os.path.realpath(_parent), (
        f"⛔ 顶层没有该键时应回退父目录 {os.path.realpath(_parent)}, 实得 {_got[1]!r}({_form})"
    )
