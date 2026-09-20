"""CARD-DEBT-1 承重行为门：路径自动打 marker + ini timeout 真的生效。

[BATCH-2026-09-18-第十五批 / CARD-DEBT-1]

这个文件钉住三件**行为**（不是文本）：

1. ``backend/tests/conftest.py`` 末尾的 ``pytest_collection_modifyitems`` 真的按
   目录给 ``tests/contract`` / ``tests/integration`` / ``tests/e2e`` 打上同名
   marker —— 于是「默认门」
   ``-m "not integration and not e2e and not contract"`` 才真的选得干净。
2. 自动打标**没有扩大 W4 的 advisory 面**。W4
   （``tests/support/live_port_guard.py``）对
   ``EXEMPT_MARKERS = {integration, e2e, real_neo4j}`` 只记不拦；本卡打的
   ``contract`` 不在这个集合里，而 ``integration`` / ``e2e`` 只打到
   ``EXEMPT_PATH_PREFIXES = ("integration", "e2e")`` 已经豁免的那两个目录上
   ⇒ 对 W4 语义中性。**⚠️ 这句话只在路径保持稳定时成立**：hook 在收集期按
   ``resolve()`` 的结果打 marker，W4 在运行期才判豁免；两个时刻之间若软链改指，
   marker 会先于路径判定生效（Codex round-1/2 MEDIUM，登记不改，见验收单台账 ⑪）。
   第 3 条用例把这句话变成可执行判据，**四层**，每层堵上一层接不住的那个变异
   （分工表见该用例的 docstring）。
3. ``backend/pytest.ini`` 的 ``timeout`` / ``timeout_method`` 真的被
   ``pytest-timeout`` 读到（第 4 条）；一个**在主线程里同步阻塞**的用例到点会被
   判红、会话继续往下走（第 5 条）。⚠️ 第 5 条**不**证明超时能终止任意挂起 ——
   signal 方法只是在主线程 ``pytest.fail()``，不杀线程 / executor / 进程，
   覆盖面与三类例外写在该用例的 docstring 与 ``backend/pytest.ini`` 的注释里。

⛔ 实现约束（卡文 §一(g)）：每条用例都用 ``subprocess`` 起**真的 pytest 子进程**
真收集 / 真超时——不用 ``pytester``（那需要在根 conftest 注册插件，越出本卡目的），
不 mock ``subprocess``，不 monkeypatch pytest 内部。所有子进程都只做收集或跑一个
本地 ``time.sleep``，不连任何数据库、不碰 live vault。
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.support.live_port_guard import EXEMPT_MARKERS, EXEMPT_PATH_PREFIXES

#: ``backend/`` 的绝对路径。本文件位于 ``backend/tests/unit/``，往上两级。
BACKEND_ROOT = Path(__file__).resolve().parents[2]

PYTEST_INI = BACKEND_ROOT / "pytest.ini"

#: 样本文件。选取原则：**本卡的 hook 是它们身上唯一的 marker 来源**——
#: 手写了 ``pytestmark`` 的文件当样本就没有「先红」（改 conftest 之前就已经绿），
#: 门会绿在一个与本卡无关的原因上。
#:
#: * integration：``sorted(glob("tests/integration/test_*.py"))[0]``，实测
#:   ``grep -c 'pytest.mark.integration'`` = 0、``grep -c 'from app.main import app'`` = 0。
#: * e2e：``sorted(...)[0]`` 是 ``test_a11_kg_relevance_e2e.py``，它 :68-69 有手写
#:   ``pytestmark = [pytest.mark.e2e, ...]`` ⇒ 不合用；取 sorted 序里第一个
#:   ``pytest.mark.e2e`` = 0 **且** ``from app.main import app`` = 0 的文件
#:   （不 import app.main 是为了让收集期零 lifespan 副作用）。
#: * contract / unit：第 1、3 条用例的对照面，两者都没有任何 marker。
INTEGRATION_SAMPLE = "tests/integration/test_2_5_x_e2e.py"
E2E_SAMPLE = "tests/e2e/test_epic36_integration.py"
CONTRACT_SAMPLE = "tests/contract/test_node_id_patterns.py"
UNIT_SAMPLE = "tests/unit/test_vault_scope_409.py"

#: 单个子进程的硬上限。到这个值还没回来 = ``subprocess.TimeoutExpired`` 把本用例判红，
#: 而不是让它跟着挂住——本卡的主题就是「不许再挂死」。
#:
#: ⚠️ **这个数受 ini 的 ``timeout`` 约束，不能随便调大**：pytest-timeout 罩的是
#: 整个 item（setup+call+teardown），而本文件里子进程调用最多的一条用例
#: （:func:`test_integration_e2e_dir_autotagged`，2 个样本 × 2 次跑）会连起
#: **4 个**子进程。最坏情况 4 × 本值必须 **< ini 的 timeout（300）**，
#: 否则这道门会在负载下撞上自己装的那个超时 —— 判据反过来咬判据。
#: 4 × 60 = 240 < 300 ✅。实测单次子进程约 24 秒（`gate-durations` 存档：
#: 该条用例 4 次共 97.19s），60 秒留了约 2.5 倍余量。
SUBPROCESS_TIMEOUT_S = 60

#: 第 5 条用例里那个挂住的测试睡多久，以及给它的 CLI ``--timeout`` 值。
#: 两者要拉开差距，才能区分「到点被打断判红」与「它自己睡完了」。
HANG_SLEEP_S = 6
HANG_CLI_TIMEOUT_S = 1

#: 第 5 条的墙钟上限（卡文 §一(g)⑤）。``HANG_SLEEP_S`` 是 6，所以只要实测 < 5
#: 就排除了「其实是睡满 6 秒自己结束的」这条解释。
HANG_WALL_CLOCK_LIMIT_S = 5.0

#: 根 conftest 里那张映射的**变量名**。:func:`_hook_dir_marker_map` 按它锚定，
#: 而不是按「函数体内恰好一个 dict 字面量」—— 后者既挡不住「抽到的不是 hook 真用的
#: 那张」，也会因为 hook 里多一个无关局部 dict 就红在一条与 W4 无关的断言上。
MAP_VAR = "dir_to_marker"

#: 卡文钉死的「映射恰三条」。这一条同时是第 2、3 层「期望空集」判据的**非空前提**：
#: 映射若变成 ``{}``，那两层会全部空洞变绿。
EXPECTED_DIRS = {"contract", "integration", "e2e"}


def _run_pytest(*args: str, timeout: int = SUBPROCESS_TIMEOUT_S) -> subprocess.CompletedProcess:
    """在 ``backend/`` 下起一个真的 pytest 子进程。

    ``PYTEST_ADDOPTS`` 被清掉：它是进程外注入的参数，留着会让这道门的选择集
    取决于调用者的 shell 环境（判据的环境是判据的一部分）。
    ``PYTHONDONTWRITEBYTECODE`` 避免子进程往工作树写 ``__pycache__``。
    """
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


#: 收集用参数。``--override-ini=addopts=`` 不是可有可无的：
#: ``backend/pytest.ini:19-21`` 的 ``addopts = -v --tb=short`` 会把 CLI 的 ``-q``
#: 抵消成 verbosity=0，``--collect-only`` 于是打**树形**（``<Function ...>``）而不是
#: nodeid 行 —— 那样 :func:`_nodeid_lines` 恒返回空列表，「0 条」的断言会
#: **恒真**（空洞判据），「≥1 条」的断言会恒假。实测（本卡先红存档
#: ``gate-before-20260918T194620.txt``）：不加 override 时 nodeid 行 = 0，
#: 加了 = 50。清掉 addopts 只去掉两个显示项，不改选择集。
#: 这也是仓内 ``.claude/hooks/post-tool-router.sh`` 用的同一招。
COLLECT_ARGS = ("--collect-only", "-q", "-p", "no:cacheprovider", "--override-ini=addopts=")


def _nodeid_lines(stdout: str) -> list[str]:
    """``--collect-only -q`` 的输出里，哪几行是真的 nodeid。

    只认「行首就是 ``tests/`` 且含 ``::``」——W4 的汇总行、warning 摘要、
    统计行都不满足，不会被算成收集到的用例。
    """
    return [ln for ln in stdout.splitlines() if ln.startswith("tests/") and "::" in ln]


def _fail_msg(label: str, proc: subprocess.CompletedProcess) -> str:
    return f"{label}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"


def _assert_deselected_not_broken(proc: subprocess.CompletedProcess, what: str) -> None:
    """断言「一条都没选中」是**因为被 deselect**，而不是因为收集塌了。

    ⚠️ 为什么需要这一层：下面几处断言的形状是 ``_nodeid_lines(...) == []``。
    一个**收集出错**的子进程同样一条 nodeid 都不打 —— 它会让这些断言绿在
    「什么都没收集到」上，而不是绿在「marker 生效、被正确排除」上。
    验伪锚（另起一个进程、不带 ``-m``）证明的是**那一次**能数出东西，
    证明不了**这一次**没塌。所以每个「期望 0 条」的判据都必须在**同一次**输出里
    拿到 deselect 的正面痕迹，并排除内部错误。
    """
    out = proc.stdout + proc.stderr
    for bad in ("INTERNALERROR", "error during collection", "errors during collection"):
        assert bad not in out, _fail_msg(f"{what}：子进程收集出错（命中 {bad!r}）", proc)
    # ⛔ **正面白名单**，不是「排除 3 和 4」（Codex round-2 MEDIUM）：黑名单挡不住
    # 中断（2）、也挡不住被信号杀死的负数 rc。一次 `--collect-only` 的正常结局只有两种：
    # 0 = 收集到了东西，5 = 一条都没收集到。其余一律不是「正常的收集结果」。
    assert proc.returncode in (0, 5), _fail_msg(
        f"{what}：子进程 rc={proc.returncode}，不在 `--collect-only` 的正常结局 {{0, 5}} 内"
        "（2=中断 / 3=内部错误 / 4=用法错误 / 负数=被信号杀死）。",
        proc,
    )
    assert "deselected" in out, _fail_msg(
        f"{what}：输出里没有 `deselected` —— 「0 条被选中」没有正面证据，不能排除它其实是收集塌了。",
        proc,
    )


def _ini_timeout_value() -> float:
    """从 ``backend/pytest.ini`` 文本里解析 ``timeout`` 的值。

    故意读文本而不是读 ``config.getini``：这道门要验的就是「ini 里写的那个数
    真的传到了插件」，两侧必须来自不同的读法，否则是同一个来源自证自己。
    """
    text = PYTEST_INI.read_text(encoding="utf-8")
    m = re.search(r"^timeout\s*=\s*([0-9.]+)\s*$", text, re.MULTILINE)
    assert m is not None, f"backend/pytest.ini 里没有顶层 `timeout = <N>` 行：\n{text}"
    return float(m.group(1))


def test_contract_dir_autotagged() -> None:
    """``tests/contract`` 下的用例被自动打上 ``contract``。

    没有 hook 时 ``-m "not contract"`` 一条也不排除 ⇒ 第一条断言（deselected）
    就是本用例的红点。
    """
    excluded = _run_pytest(*COLLECT_ARGS, "-m", "not contract", CONTRACT_SAMPLE)
    assert "deselected" in excluded.stdout, _fail_msg(
        f"`-m 'not contract'` 对 {CONTRACT_SAMPLE} 没有 deselect 任何用例："
        "根 conftest 的 pytest_collection_modifyitems 没有给 contract 目录打 marker。",
        excluded,
    )
    assert _nodeid_lines(excluded.stdout) == [], _fail_msg(
        f"`-m 'not contract'` 之后 {CONTRACT_SAMPLE} 仍有用例被选中。", excluded
    )
    _assert_deselected_not_broken(excluded, f"`-m 'not contract'` on {CONTRACT_SAMPLE}")

    included = _run_pytest(*COLLECT_ARGS, "-m", "contract", CONTRACT_SAMPLE)
    assert len(_nodeid_lines(included.stdout)) >= 1, _fail_msg(
        f"`-m contract` 在 {CONTRACT_SAMPLE} 上零收集（rc=5 不是绿）。", included
    )


def test_integration_e2e_dir_autotagged() -> None:
    """``tests/integration`` / ``tests/e2e`` 下的用例被自动打上同名 marker。

    两个样本都实测没有手写 ``pytestmark``，所以这里绿只可能是 hook 打的。
    只做 ``--collect-only``：这两个目录里有文件在 import 期 ``from app.main
    import app``，执行它们会真起 lifespan（W4 对它们只记不拦）。

    ⚠️ 不用 ``parametrize``：本文件的收集数是卡文的判据之一（应为 5），
    参数化会把它变成 6。
    """
    for sample, marker in ((INTEGRATION_SAMPLE, "integration"), (E2E_SAMPLE, "e2e")):
        included = _run_pytest(*COLLECT_ARGS, "-m", marker, sample)
        assert len(_nodeid_lines(included.stdout)) >= 1, _fail_msg(
            f"`-m {marker}` 在 {sample} 上零收集：目录自动打标没生效。", included
        )

        excluded = _run_pytest(*COLLECT_ARGS, "-m", f"not {marker}", sample)
        # 先断言不变量、再上防空洞守卫（顺序理由见第 3 条用例第 4 层处的注释）
        assert _nodeid_lines(excluded.stdout) == [], _fail_msg(
            f"`-m 'not {marker}'` 之后 {sample} 仍有用例被选中。", excluded
        )
        _assert_deselected_not_broken(excluded, f"`-m 'not {marker}'` on {sample}")


def _hook_dir_marker_map() -> dict:
    """从根 conftest 的源码里把 hook 那张目录→marker 映射**读出来**。

    用 AST 取函数体内的 dict 字面量，不 import conftest（import 它会拖起整条
    ``app.main`` 链）。也不在这里手抄一份副本 —— 手抄的两份清单必然漂移。
    """
    src = (BACKEND_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "pytest_collection_modifyitems"]
    assert len(fns) == 1, f"根 conftest 里 pytest_collection_modifyitems 应恰 1 个，实得 {len(fns)}"

    # ⛔ **按名字锚定 `dir_to_marker` 的那次赋值**，不是「函数体内恰好一个 dict 字面量」。
    # 后者有两个毛病：① hook 体内将来多一个无关的局部 dict（比如一个缓存）就会红在
    # 一条与 W4 毫无关系的断言上；② 它也不保证抽到的那个 dict **就是 hook 真正用的
    # 那张映射**。锚在赋值目标的名字上，两个毛病一起消失。
    assigns = [
        n
        for n in ast.walk(fns[0])
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == MAP_VAR for t in n.targets)
    ]
    assert len(assigns) == 1, (
        f"hook 体内应恰有 1 处 `{MAP_VAR} = ...` 赋值，实得 {len(assigns)}。\n"
        "这道门按名字锚定那张映射。如果它被改名、搬到模块级、或被多次赋值，"
        "请同步改这里 —— 而不是让门去猜哪个 dict 才是它。"
    )
    node = assigns[0].value
    assert isinstance(node, ast.Dict), (
        f"`{MAP_VAR}` 的右侧不是 dict 字面量，而是 {type(node).__name__}。\n"
        "这道门只看得懂字面量（例如换成 dict(...) 调用或 {**BASE, ...} 之后就看不懂了）。"
    )

    # ⛔ 解析不了的条目必须**当场拒绝**，不能静默跳过（Codex round-2 MEDIUM）：
    # 原来的写法是 `if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)`
    # —— 一条 `"regression": "real_" + "neo4j"` 在运行时确实会打 `real_neo4j`，
    # 但它的 value 是 ast.BinOp 不是 ast.Constant，于是被过滤掉、下面三层全部看不见它。
    # 「我只检查我看得懂的那部分」就是一道抽出了安全子集的门。
    #
    # ⚠️ `ast.dump(None)` 会抛 `TypeError: expected AST, got 'NoneType'`（实测）——
    # 而 `{**other}` 这种解包在 `d.keys` 里**就是 None**。所以这里不能直接 dump：
    # 那会让「我这条断言声称自己管解包」变成「它先崩在 dump 上」。
    def _show(n):
        return "**解包（keys 里是 None）**" if n is None else ast.dump(n)

    unresolved = [
        (_show(k), _show(v))
        for k, v in zip(node.keys, node.values)
        if not (isinstance(k, ast.Constant) and isinstance(v, ast.Constant))
    ]
    assert unresolved == [], (
        f"hook 的映射里有**静态解析不了**的条目：{unresolved}\n"
        "这道门只能检查字面量键值对。出现拼接 / 变量 / 解包之后，下面几层不变量就看不见它了 —— "
        "所以这里直接拒绝，而不是跳过。要么把它写成字面量，要么给这道门补一条能看懂它的判据。"
    )

    mapping = {k.value: v.value for k, v in zip(node.keys, node.values)}
    # ⛔ 非空 + 恰好是卡文钉死的那三条。缺了这一条，下面「期望空集」的第 2、3 层
    # 会在映射变成 `{}` 时**全部空洞变绿**（期望 0 的判据必须先证输入面非空）。
    assert set(mapping) == EXPECTED_DIRS, (
        f"hook 的映射目录集变了：实得 {sorted(mapping)}，期望 {sorted(EXPECTED_DIRS)}。\n"
        "卡文钉死「映射恰三条」。要加第四条，必须先回去重核 EXEMPT_MARKERS "
        "（理由见本文件第 3 条用例的 docstring），然后同步改这里。"
    )
    return mapping


def test_autotag_does_not_widen_w4_exempt_markers() -> None:
    """自动打标既没有扩大 W4 的豁免面，也没有把 marker 打到别的目录上。

    这条用例有**四层**，每一层堵的是**上一层接不住的那个变异**。
    第二层是 Codex round-1 的 MEDIUM 整改补的，第三、四层是送审前一轮内部对抗
    复核抓出来的（那轮指出：前两层对 ``contract`` 这一个 marker 零覆盖）。

    | 层 | 断言 | 它堵住的变异 | 前面几层为什么接不住 |
    |---|---|---|---|
    | 1 行为 | ``-m '<EXEMPT_MARKERS 拼出的表达式>'`` 在 unit / contract 两个样本上选中 0 条 | 把豁免 marker 打到这两个目录上 | —— |
    | 2 结构 | 映射里凡 marker ∈ ``EXEMPT_MARKERS``，其目录必须已在 ``EXEMPT_PATH_PREFIXES`` | ⛔ **本层已不可达**，见下 | 第 1 层根本不收集 ``tests/regression`` |
    | 3 结构 | 映射里每条都必须**目录名 == marker 名** | ``{"e2e": "contract"}``（键集不变）| ``contract`` **不在** ``EXEMPT_MARKERS`` 里，第 2 层的过滤直接跳过它 |
    | 4 行为 | ``-m contract`` 在 unit 样本上选中 0 条 | ``dir_to_marker.get(first, "contract")`` | 第 3 层读的是 dict 字面量，而这个变异改的是 ``.get()`` 的默认值 |

    第 3、4 层堵的那类变异后果最重：``contract`` 被打到 ``tests/unit`` 上之后，
    默认门的 ``-m "... and not contract"`` 会把整个 ``tests/unit`` **静默**排除
    —— **本文件自己也在 tests/unit 里，会跟着一起消失**，而成绩单只是少了几千条
    passed，一条红都没有。

    ⚠️ **第 2 层在当前顺序下不可达（2026-09-19 人审替代实证，如实降级）**：
    :func:`_hook_dir_marker_map` 末尾的 ``set(mapping) == EXPECTED_DIRS`` 把键集
    钉死成三条之后，能违反第 2 层的输入只剩 ``contract`` 映到某个豁免 marker
    —— 而第 1 层跑的正是 ``EXEMPT_MARKERS`` 全集、样本里就有一个
    ``tests/contract/`` 下的文件，必被它先抓走。枚举「键集恒等、值取自
    {contract, integration, e2e, real_neo4j, other}」的全部 125 组合：
    最先红在 L1 的 75 种 / L3 的 49 种 / 全绿 1 种 / **L2 = 0 种**。
    实测三段（还原逐字节同）：加第 4 个键 → 红在 ``set(mapping)``；
    ``contract → real_neo4j``（键集不变）→ 红在第 1 层；
    ``e2e → contract``（键集不变）→ 红在第 3 层。
    ⇒ 第 2 层现为**纵深防御**，不是被独立验证过的门；只有当 W4 的
    ``EXEMPT_PATH_PREFIXES`` 缩小时它才重新可达。**不在本卡改**（改判据顺序
    要动已绑定的代码），修法建议与登记见验收单 §五（台账 11b）。

    ⚠️ **这条用例在两段负控下的表现，如实写明**：
    - 段②（删 ini 的 ``timeout`` 行）下它仍绿 —— 是**控制组**。
    - 段①（删掉整个 hook）下它**会红**，但红在 :func:`_hook_dir_marker_map` 的
      「应恰 1 个」上 —— 那是**取证前提不成立**（映射根本不存在了），
      不是「不变量被推翻」。它不是段① 的指定红点；段① 的指定红点是第 1、2 条用例。
    """
    # ── 第一层：行为 ────────────────────────────────────────────────────────
    # 验伪锚：这条断言期望「0 条」，所以必须先证明「同一对样本、同一条提取
    # 口径下，不加 -m 是能数出东西的」——否则输出格式一变（例如 addopts 改了
    # verbosity）它就恒真，变成一道什么都不测的门。
    anchor = _run_pytest(*COLLECT_ARGS, UNIT_SAMPLE, CONTRACT_SAMPLE)
    assert len(_nodeid_lines(anchor.stdout)) >= 1, _fail_msg(
        f"验伪锚失败：不加 -m 时 {UNIT_SAMPLE} / {CONTRACT_SAMPLE} 也数出 0 条 nodeid，"
        "说明提取口径没对上输出格式，下面那条『0 条』的断言是空洞的。",
        anchor,
    )

    expr = " or ".join(sorted(EXEMPT_MARKERS))
    proc = _run_pytest(*COLLECT_ARGS, "-m", expr, UNIT_SAMPLE, CONTRACT_SAMPLE)
    assert _nodeid_lines(proc.stdout) == [], _fail_msg(
        f"`-m '{expr}'`（W4 豁免 marker 全集）在 {UNIT_SAMPLE} / {CONTRACT_SAMPLE} 上"
        "选中了用例 = W4 的 advisory 面被自动打标扩大了。",
        proc,
    )
    _assert_deselected_not_broken(proc, f"`-m '{expr}'` on {UNIT_SAMPLE} / {CONTRACT_SAMPLE}")

    # ── 第二层：映射本身的结构不变量（与样本文件无关）────────────────────────
    mapping = _hook_dir_marker_map()
    widened = {
        directory: marker
        for directory, marker in mapping.items()
        if marker in EXEMPT_MARKERS and directory not in EXEMPT_PATH_PREFIXES
    }
    assert widened == {}, (
        f"映射把 W4 的豁免 marker 发给了路径上尚未豁免的目录：{widened}\n"
        f"  hook 映射        = {mapping}\n"
        f"  EXEMPT_MARKERS   = {sorted(EXEMPT_MARKERS)}\n"
        f"  EXEMPT_PATH_PREFIXES = {sorted(EXEMPT_PATH_PREFIXES)}\n"
        "这等于把一批用例从 W4 的拦截面悄悄挪进 advisory 面。"
    )

    # ── 第三层：每条映射必须「目录名 == marker 名」────────────────────────────
    # 第二层只管 EXEMPT_MARKERS 里那三个 marker。``contract`` **不在**那个集合里，
    # 所以 ``{"unit": "contract"}`` 这种「把 contract 打到别的目录上」第二层接不住 ——
    # 而它的后果比扩大 advisory 面更糟：默认门的 `-m "... not contract"` 会把整个
    # ``tests/unit`` 静默 deselect 掉（本文件自己也在 tests/unit 里，会一起消失），
    # 成绩单只是少了几千条 passed，不红。
    mismapped = {d: m for d, m in mapping.items() if d != m}
    assert mismapped == {}, (
        f"映射里有「目录名 != marker 名」的条目：{mismapped}\n"
        f"  hook 映射 = {mapping}\n"
        "本 hook 的契约是「按一级目录补**同名** marker」。把某个目录映到别的 marker 上，"
        "会让默认门的 -m 表达式排除掉一整个本该跑的目录，而且不会红。"
    )

    # ── 第四层：行为侧兜住 ``.get()`` 的默认值 ────────────────────────────────
    # 第三层读的是 dict 字面量。若有人把 ``dir_to_marker.get(first)`` 改成
    # ``dir_to_marker.get(first, "contract")``，字面量没变、前三层全绿，
    # 但**每个**目录都会拿到 contract。这里直接问一句：unit 样本有没有拿到 contract？
    unit_as_contract = _run_pytest(*COLLECT_ARGS, "-m", "contract", UNIT_SAMPLE)
    # ⚠️ 顺序要紧：**先断言不变量，再上防空洞守卫**。
    # 守卫的职责是「当结果确实是 0 条时，区分『被正确排除』与『收集塌了』」。
    # 把它放在前面会让「marker 被打多了」这个变异红在守卫上，而守卫的文案说的是
    # 「不能排除收集塌了」—— 与事实（其实是全被选中）相反，归因会被带偏一整轮。
    assert _nodeid_lines(unit_as_contract.stdout) == [], _fail_msg(
        f"`-m contract` 在 {UNIT_SAMPLE} 上选中了用例 —— `contract` marker 被打到了 "
        "tests/contract 之外。默认门会因此把这个目录整个排除掉，而且不会红。",
        unit_as_contract,
    )
    _assert_deselected_not_broken(unit_as_contract, f"`-m contract` on {UNIT_SAMPLE}")


def test_ini_timeout_header() -> None:
    """``backend/pytest.ini`` 的 ``timeout`` / ``timeout_method`` 真的传到了插件。

    判据取插件自己打印的 report header（``pytest_report_header``）——那是插件
    **实际生效的设置**，不是我们再读一遍 ini。故意不带 ``-q``：``-q`` 会把
    header 整段吞掉。
    """
    pytest.importorskip("pytest_timeout")
    proc = _run_pytest(
        "-c",
        "pytest.ini",
        "--rootdir",
        ".",
        "--collect-only",
        "-p",
        "no:cacheprovider",
        CONTRACT_SAMPLE,
    )
    m = re.search(r"^timeout: ([0-9.]+)s", proc.stdout, re.MULTILINE)
    assert m is not None, _fail_msg(
        "pytest-timeout 没有打出 `timeout: <N>s` header：backend/pytest.ini 的 timeout 值没有被读到。",
        proc,
    )
    assert float(m.group(1)) == _ini_timeout_value(), _fail_msg(
        f"header 里的 timeout={m.group(1)}s 与 backend/pytest.ini 文本里的 timeout={_ini_timeout_value()} 不一致。",
        proc,
    )
    assert re.search(r"^timeout method: signal", proc.stdout, re.MULTILINE) is not None, _fail_msg(
        "header 里的 timeout method 不是 signal。", proc
    )


def test_timeout_kills_hung_test(tmp_path: Path) -> None:
    """一个在**主线程里同步阻塞**的用例，到点会被判红、会话继续往下走。

    被测文件写在 ``tmp_path``：pytest 从参数路径往上找不到任何 ini，rootdir 就
    落在 tmp 里 ⇒ **根 conftest 不会被加载**，这个子进程零网络、零 fixture，
    只剩「sleep 6 秒 vs --timeout=1」这一件事。

    ⚠️ **这条证明什么、不证明什么**（Codex round-1 HIGH 整改，别把它读宽）：

    - 证明：主线程的同步阻塞（这里是 ``time.sleep``）会被 ``SIGALRM`` 打断，
      用例在 1 秒处判红、进程在 ``HANG_WALL_CLOCK_LIMIT_S`` 内退出。
    - **不证明**：超时能**终止**任意挂起。``pytest-timeout`` 的 signal handler
      做的是在主线程 ``pytest.fail()``，它**不杀线程、不杀 executor、不杀进程**。
      于是至少三类输入不在本条覆盖面内：
        ① 阻塞发生在非主线程（portal / executor worker）—— 用例会红，
           但那个线程可能仍在跑，清理阶段还会等它；
        ② 主线程正卡在一段不检查 Python 信号的长 C 调用 —— handler 要等它返回；
        ③ 信号落在一段 ``except BaseException`` 里 —— 典型是 asyncio 的回调
           ``Handle._run()``（CPython ``asyncio/events.py`` 实测捕获
           ``BaseException``）。``pytest.fail()`` 抛的 ``Failed`` 的 mro 是
           ``Failed → OutcomeException → BaseException``（实测
           ``issubclass(Failed, Exception)`` 为 **False**），所以**普通
           ``except Exception`` 接不住它**，但 ``except BaseException`` 会 ——
           那时它会被事件循环当成「回调里的异常」记账，用例照常通过。
      这三类**本卡都没有实测**，是读插件与 CPython 源码得到的边界声明；
      登记见验收单「本卡未证明什么」。
    """
    pytest.importorskip("pytest_timeout")
    hung = tmp_path / "test_debt1_hang_probe.py"
    hung.write_text(
        f"import time\n\n\ndef test_sleeps_longer_than_the_timeout():\n    time.sleep({HANG_SLEEP_S})\n",
        encoding="utf-8",
    )

    started = time.monotonic()
    proc = _run_pytest(
        "-p",
        "no:cacheprovider",
        f"--timeout={HANG_CLI_TIMEOUT_S}",
        "-q",
        str(hung),
        timeout=60,
    )
    elapsed = time.monotonic() - started

    assert proc.returncode == 1, _fail_msg(f"挂住的用例没有被判红（rc={proc.returncode}）。", proc)
    assert "Timeout" in proc.stdout + proc.stderr, _fail_msg("输出里没有 Timeout 字样：红的原因不是超时。", proc)
    assert elapsed < HANG_WALL_CLOCK_LIMIT_S, _fail_msg(
        f"墙钟 {elapsed:.2f}s ≥ {HANG_WALL_CLOCK_LIMIT_S}s：不能排除「它其实睡满了 {HANG_SLEEP_S}s 自己结束」。",
        proc,
    )
