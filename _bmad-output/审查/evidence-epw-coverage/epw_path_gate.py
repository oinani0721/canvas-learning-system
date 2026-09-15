"""CARD-EPW-COVERAGE 死信路径三入口 AST 门（逐 Call 断言，不用 grep -c 比大小）。

入口：
  - ``GraphitiEpisodeWorker(`` 直调        → 必须带 kwarg ``dead_letter_path=``
  - ``DeadLetterStore(`` 直调              → 必须带 kwarg ``file_path=``
  - ``get_episode_worker(`` /
    ``cleanup_episode_worker(`` 直调        → 一律 FAIL（单例工厂 episode_worker.py
    ``get_episode_worker`` 内无参实例化，恒用默认相对路径 ``data/dead_letter_episodes.jsonl``，
    且模块级 ``_worker_instance`` 跨用例残留）
  - 间接入口：``memory_service`` 内 ``_enqueue_episode`` / ``record_knowledge_entity`` /
    ``_search_graphiti`` / ``_search_graphiti_legacy`` 都调 ``get_episode_worker()``
    ⇒ 源码 import 了 memory_service 就必须出现 patch 目标串 ``get_episode_worker``
    （启发式，不追调用链；``--strict-ms`` 时阻断，否则只 ⚠️ ADVISORY 登记）

用法：
    python3 epw_path_gate.py [--strict-ms] <file.py>
rc=0 且打印 ``EPW-PATH-GATE: PASS`` 为通过。

⚠️ **本门已知的未覆盖路径（Codex r1 MEDIUM-4，如实声明，不主张它能独立承担隔离验收）**：
  - r1 提的两条已封：**写死的路径字面量**（带着 kwarg 却指向真坟场）与 **import 别名**
    （`import get_episode_worker as get_w` 后调 `get_w()`）；
  - **仍未封**：① 值是变量/参数时只看形态不看取值（`p = "data/dead_letter_episodes.jsonl";
    GraphitiEpisodeWorker(dead_letter_path=p)` 仍 PASS——需要数据流分析）；② `memory_service`
    启发式只查源码里**是否出现** ``get_episode_worker`` 这个串，删掉某个用例的 ``ready_worker``
    fixture 形参、只留 fixture 定义里的那个串，门照样 PASS（注释里的同名串也算数）；
    ③ 经 ``memory_service`` 的**间接**入口不追调用链。
  运行期的后置防线是 (i) 的 sentinel，而 sentinel 又抓不到「建了默认路径 worker 但这次没落死信」。
  两层各有盲区 —— 本门是**必要条件**，不是充分条件。
"""

import ast
import sys

strict_ms = "--strict-ms" in sys.argv
p = [a for a in sys.argv[1:] if a != "--strict-ms"][0]
src = open(p, encoding="utf-8").read()
t = ast.parse(src)


def nm(c):
    f = c.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")


scope = {}  # lineno -> 最内层 class/def 名（归因用：落在 TestAC3StartupRecovery 区 = T10-C 重写区）
for n in ast.walk(t):
    if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        for line in range(n.lineno, (n.end_lineno or n.lineno) + 1):
            scope[line] = n.name

# Codex r1 MEDIUM-4 加固 ①：解析 import 别名。
# `from app.services.episode_worker import get_episode_worker as get_w` 之后调 `get_w()`
# 与直调同效，原门只按被调名字匹配、看不见别名。
SINGLETON_NAMES = {"get_episode_worker", "cleanup_episode_worker"}
singleton_aliases = set(SINGLETON_NAMES)
worker_aliases = {"GraphitiEpisodeWorker"}
store_aliases = {"DeadLetterStore"}
for n in ast.walk(t):
    if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("app.services.episode_worker"):
        for a in n.names:
            if a.asname:
                if a.name in SINGLETON_NAMES:
                    singleton_aliases.add(a.asname)
                elif a.name == "GraphitiEpisodeWorker":
                    worker_aliases.add(a.asname)
                elif a.name == "DeadLetterStore":
                    store_aliases.add(a.asname)


def _path_value_is_safe(node):
    """Codex r1 MEDIUM-4 加固 ②：kwarg 在场还不够，值不能是写死的路径字面量。

    `GraphitiEpisodeWorker(dead_letter_path="data/dead_letter_episodes.jsonl")` 带着 kwarg
    却指向真死信坟场，原门照样 PASS。要求：值必须是**表达式**（`str(tmp_path / …)` 一类），
    不得是 `ast.Constant` 字面量，也不得是纯字面量拼接的 JoinedStr。
    """
    if isinstance(node, ast.Constant):
        return False
    if isinstance(node, ast.JoinedStr) and all(isinstance(v, ast.Constant) for v in node.values):
        return False
    return True


bad = []
warn = []
counts = {"worker": 0, "deadletter": 0, "singleton": 0}
for c in (x for x in ast.walk(t) if isinstance(x, ast.Call)):
    k = nm(c)
    kws = {kw.arg: kw.value for kw in c.keywords}
    where = f"{p}:{c.lineno} [{scope.get(c.lineno, '<module>')}]"
    if k in worker_aliases:
        counts["worker"] += 1
        if "dead_letter_path" not in kws:
            bad.append(
                f"{where} GraphitiEpisodeWorker( 缺 kwarg dead_letter_path=（位置参数形态也判 FAIL，改写成 kwarg）"
            )
        elif not _path_value_is_safe(kws["dead_letter_path"]):
            bad.append(
                f"{where} GraphitiEpisodeWorker(dead_letter_path=…) 的值是写死的路径字面量"
                f"（{ast.unparse(kws['dead_letter_path'])}）——必须是 tmp_path 派生的表达式"
            )
    elif k in store_aliases:
        counts["deadletter"] += 1
        if "file_path" not in kws:
            bad.append(f"{where} DeadLetterStore( 缺 kwarg file_path=（位置参数形态也判 FAIL，改写成 kwarg）")
        elif not _path_value_is_safe(kws["file_path"]):
            bad.append(
                f"{where} DeadLetterStore(file_path=…) 的值是写死的路径字面量"
                f"（{ast.unparse(kws['file_path'])}）——必须是 tmp_path 派生的表达式"
            )
    elif k in singleton_aliases:
        counts["singleton"] += 1
        alias_note = "" if k in SINGLETON_NAMES else f"（import 别名，实为 {'/'.join(sorted(SINGLETON_NAMES))} 之一）"
        bad.append(f"{where} {k}( 单例工厂恒用默认死信路径，禁直调{alias_note}")


def _ms(x):
    if isinstance(x, ast.ImportFrom):
        m = x.module or ""
        return m.startswith("app.services.memory_service") or (
            m == "app.services" and any(a.name == "memory_service" for a in x.names)
        )
    return isinstance(x, ast.Import) and any(a.name.startswith("app.services.memory_service") for a in x.names)


ms = any(_ms(x) for x in ast.walk(t))
if ms and "get_episode_worker" not in src:
    msg = f"{p}: import 了 memory_service 却没 patch get_episode_worker（间接入口：memory_service 的 4 处 get_episode_worker() 调用）"
    (bad if strict_ms else warn).append(msg)

print(
    f"worker={counts['worker']} deadletter={counts['deadletter']} "
    f"singleton={counts['singleton']} imports_memory_service={ms} strict_ms={strict_ms}"
)
for w in warn:
    print("⚠️ ADVISORY(登记不阻断，归因见 scope)", w)
for b in bad:
    print("❌", b)
print("EPW-PATH-GATE:", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
