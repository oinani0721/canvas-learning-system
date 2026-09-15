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

bad = []
warn = []
counts = {"worker": 0, "deadletter": 0, "singleton": 0}
for c in (x for x in ast.walk(t) if isinstance(x, ast.Call)):
    k = nm(c)
    kws = {kw.arg for kw in c.keywords}
    where = f"{p}:{c.lineno} [{scope.get(c.lineno, '<module>')}]"
    if k == "GraphitiEpisodeWorker":
        counts["worker"] += 1
        if "dead_letter_path" not in kws:
            bad.append(
                f"{where} GraphitiEpisodeWorker( 缺 kwarg dead_letter_path=（位置参数形态也判 FAIL，改写成 kwarg）"
            )
    elif k == "DeadLetterStore":
        counts["deadletter"] += 1
        if "file_path" not in kws:
            bad.append(f"{where} DeadLetterStore( 缺 kwarg file_path=（位置参数形态也判 FAIL，改写成 kwarg）")
    elif k in ("get_episode_worker", "cleanup_episode_worker"):
        counts["singleton"] += 1
        bad.append(f"{where} {k}( 单例工厂恒用默认死信路径，禁直调")


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
