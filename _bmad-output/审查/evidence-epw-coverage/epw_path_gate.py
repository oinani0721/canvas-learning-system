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

⚠️ **本门已知的未覆盖路径（如实声明，不主张它能独立承担隔离验收）**

已封（各配验伪锚，见 `epw-path-gate-probes-*.txt` / `-v3-*` / `-v5-*`；反向锚证不误杀）：
  - 漏传 kwarg / 位置参数形态；
  - 直调 ``get_episode_worker`` / ``cleanup_episode_worker``（含 ``import … as`` 别名，
    **不限来源模块**——从 ``app.services.memory_service`` 转出的同名符号也算，Codex r2 LOW-2）；
  - 单个字符串常量里出现完整危险片段（裸字面量、``str("…")`` 包一层、f-string 内嵌整段）；
  - **纯字面量表达式**（不依赖任何变量），无论常量怎么切分拼接 —— 由「值必须依赖变量」
    这条正向规则统一覆盖（Codex r3 LOW-2 → r4 LOW-2 重写）。

**仍未封**（本门是必要条件，不是充分条件）：
  ① 值经**变量中转**且那个变量本身就是危险路径：``p = "data/dead_letter_episodes.jsonl"``
     然后 ``GraphitiEpisodeWorker(dead_letter_path=p)`` 仍 PASS —— 正向规则只看「是否依赖变量」，
     不看变量的取值，要判得准需要数据流分析。**这是本门当前最大的洞**；
  ② ``memory_service`` 启发式只查源码里**是否出现** ``get_episode_worker`` 这个串：
     删掉某个用例的 ``ready_worker`` fixture 形参、只留 fixture 定义里的那个串，门照样 PASS
     （注释里的同名串也算数）；
  ③ 经 ``memory_service`` 的**间接**入口不追调用链。

运行期的后置防线是 (i) 的 sentinel，而 sentinel 又抓不到「建了默认路径 worker 但这次没落死信」。
两层各有盲区。
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
# Codex r2 LOW-2 加固：别名收集**不限来源模块**。`from app.services.memory_service import
# get_episode_worker as get_w` 与从 episode_worker 导入等效（memory_service 转出同一个符号），
# 原先只认 `app.services.episode_worker` 开头的模块，跨模块别名整条漏掉。
for n in ast.walk(t):
    if isinstance(n, ast.ImportFrom):
        for a in n.names:
            target = a.asname or a.name
            if a.name in SINGLETON_NAMES:
                singleton_aliases.add(target)
            elif a.name == "GraphitiEpisodeWorker":
                worker_aliases.add(target)
            elif a.name == "DeadLetterStore":
                store_aliases.add(target)

#: 出现在死信路径表达式**任何位置**的这些字面量片段都判危险（含 `str("…")` 包一层、f-string 等）。
DANGEROUS_PATH_FRAGMENTS = ("dead_letter_episodes.jsonl", "data/dead_letter")

#: 判「值是否依赖变量」时要忽略的名字——它们是包装/转换，不携带路径来源。
_PATH_WRAPPER_NAMES = {"str", "os", "Path", "pathlib", "PurePath", "fspath"}


def _path_value_is_safe(node):
    """kwarg 在场还不够，值不能指向真死信坟场。

    - Codex r1 MEDIUM-4：`GraphitiEpisodeWorker(dead_letter_path="data/dead_letter_episodes.jsonl")`
      带着 kwarg 却指向真坟场，原门照样 PASS ⇒ 裸字面量一律 FAIL。
    - Codex r2 LOW-2：`str("data/dead_letter_episodes.jsonl")` 是 `ast.Call`、不是 `Constant`，
      于是又被放行 ⇒ **递归**扫整个表达式子树里的每一个字符串常量。
    - Codex r3 LOW-2：`str("data/" + "dead_letter_" + "episodes.jsonl")` 的三个常量**各自**都不含
      完整危险片段，逐个查又漏了 ⇒ 当时加了「常量按 `ast.walk` 顺序拼起来再查一次」。
    - **Codex r4 LOW-2（本版重写）**：上一版那个拼接检查两头不讨好——
      ① `ast.walk` 是**广度**遍历、不是求值顺序：`"data/" + "dead_" + "letter_" + "episodes.jsonl"`
         会拼成 `episodes.jsonlletter_data/dead_`，**仍然漏检**；
      ② 反过来又**误杀**了 `str(tmp_path / ("data/" + "dead_letter.jsonl"))` —— 它其实落在 tmp_path 内。
      根因：「按字面量猜路径」本来就判不了归属。改成一条**正向**规则——

        值表达式必须至少含一个**非包装名**（`str`/`Path`/`os` 之外的 `Name`），
        也就是这个路径得**依赖某个变量**（测试里就是 `tmp_path` / `dead_letter_path` 一类 fixture）。

      纯字面量拼出来的表达式不含自由变量 ⇒ 一律 FAIL（无论常量怎么切、`ast.walk` 什么顺序）；
      经 `tmp_path` 派生的写法都带着那个变量 ⇒ 不会被误杀。
      **逐个常量**的危险片段检查保留（挡「把整段危险路径写进一个常量」的 f-string 形态）。
    """
    literals = [
        sub.value for sub in ast.walk(node) if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
    ]
    # ① 单个常量里出现完整危险片段
    if any(frag in lit for lit in literals for frag in DANGEROUS_PATH_FRAGMENTS):
        return False
    # ② 正向规则：路径必须依赖变量；纯字面量表达式（含任意切分拼接）一律 FAIL
    free_names = {
        sub.id for sub in ast.walk(node) if isinstance(sub, ast.Name) and sub.id not in _PATH_WRAPPER_NAMES
    }
    if not free_names:
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
