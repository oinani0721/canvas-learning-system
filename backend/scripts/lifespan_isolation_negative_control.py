#!/usr/bin/env python
"""负门 —— 证明「lifespan 隔离 + socket 门 + 结账哨兵」这套防线真的在承重。

[BATCH-2026-09-01-第九批 / CARD-TEST-isolate-lifespan-R1]

方法：在 tmp 里建一份**只含 git tracked 文件**的 backend 副本，在**副本**的
``tests/api/v1/endpoints/test_metadata_subject_mapping.py`` 里把 ``no_lifespan``
摘掉，跑其中三条钉死的 nodeid。此时 client fixture 会重新触发 ``app.main`` 的
真实 lifespan，向 ``NEO4J_URI`` 指向的库发起连接。防线的行为应当是：

1. socket 门（audit hook 承重）在 connect 前拦下 —— 进程**永不真连**；
2. 连接处抛出的异常会被 ``app/main.py`` 的 try/except 吞掉 —— 所以根 conftest 的
   结账哨兵把每次被吞掉的拦截转成该用例 ``FAILED``；
3. 正证据闭环：子进程的门账必须 ``total == blocked > 0`` 且
   ``advisory == unaccounted == 0``。

## 运行时文件的判据方向（第九批更正）

第八批把「三个运行时文件前后 sha 不变」当成**变异运行**的 PASS 判据。方向反了：
socket 门只管连接，**挡不住文件写**；挡住文件写的是 ``no_lifespan``。所以摘掉隔离
之后运行时文件被写，恰恰是「隔离在承重」的正证据。本版改成：

* **硬判据**：*正控*（隔离态）运行时文件必须 unchanged —— 这才是本卡要证的那句话；
* **硬判据**：*变异态*必须**确实写了**至少一个运行时文件 —— 否则说明 lifespan 在
  到达写路径之前就 abort 了，这条负门此刻在测别的东西（2026-09-03 实测过一次：
  LanceDB canonical/legacy 环境变量冲突让 lifespan 在 Neo4j 之前就退出，
  ``blocked=0`` 看起来却像「哨兵没接住」）；
* **现场复原**：变异态新造出来的运行时文件（跑前 absent）由脚本删除。跑前就存在
  且内容变了的**不覆盖**（可能混有并发写入），直接判失败交人工。
  orchestrator 的 durable journal 落在 ``app/data/`` 下（``state_dir`` 不给就取
  模块相对路径），重定向不了；文件名自 CARD-G2-5 起是 vault 命名空间下的
  ``vault_index_pending__<vault_key>.jsonl``，见 ``RUNTIME_FILE_GLOBS``。

## 第八批 BLOCKER 的收口：子进程环境必须钉死，而不是继承

第八批本脚本把调用者环境整份继承给子进程。门**只按端口判定**（7691/7687），
所以只要 ``NEO4J_URI`` 指向别的库，「摘掉隔离」就会**真的连上去**——脚本只会
事后因 ``blocked=0`` 报失败，而实害已经发生，runtime SHA 也看不到数据库侧改动。

本版的收口是三重的，且每一重都在**任何测试跑起来之前**生效：

* :func:`_child_env` 清掉全部 ``NEO4J*`` 变量，重新钉死
  ``NEO4J_URI=bolt://127.0.0.1:7691``（受拦端口）+ 假凭据 + 测试容器 7692；
* ``W4_GUARD_REQUIRE_BLOCKED_TARGET=1`` 让 ``live_port_guard.install()`` 在装门时
  就核对目标端口在射程内，不在就**拒绝装门**（子进程直接起不来）；
* step 0c 用同一份环境起一个只读子进程，实际构造 ``Settings`` 并打印
  ``NEO4J_URI``——证明应用侧解析出来的也是那个受拦地址，而不只是环境变量好看。

同时 ``W4_GUARD_NO_EXEMPT=1`` 彻底关掉豁免：负控运行里不允许出现 advisory。

## 这道负门不比什么

* 只对**一个**代表文件做变异（在副本上），且只跑其中 **3 条钉死的 nodeid**（覆盖
  GET 成功 / POST 写 / 404 三种请求形态）——变异态每用例要完整跑一遍真实
  lifespan（被拦的连接各自带驱动级重试/超时），全 19 条 ≈ 35 分钟。它证明的是
  「防线 + lifespan 摘除」的组合在该形态上红得符合预期；不证明其余用例与其它
  12 个改造文件的个体变异也会红（fixture 形态相同，未逐一变异）。
* 只跑 pytest 主进程。防线不拦子进程（见 live_port_guard 模块 docstring），
  本脚本也不构造子进程连接场景。
* AST 门是**静态**分析：它证明的是「源码里没有裸 TestClient(app.main 的 app)」，
  不证明「运行时真的没连」。运行时证明由变异运行承担。
* AST 门**追不动容器取值与跨函数/跨模块的实例传递**（2026-09-03 自查实测的已知
  盲区）。⚠️ CARD-W4-5（2026-09-06）改变了「追不动」的**后果**，但没有改变「追不动」
  本身，两者必须分开说：

  - **仍然追不动**（能力没变）：``clients = [TestClient(app)]`` 之后
    ``with clients[0]:`` —— 门不知道 ``clients[0]`` 是什么，那要元素级别名分析；
    ``import othermod as m`` 之后 ``with m.client:`` 同理（跨模块）。
  - **但不再放行**（后果变了）：(c) 的三分把「追不到来源」从静默放行改成
    **fail-closed 判违规**。所以上面第一例在**有 TestClient 可达性的模块里**
    今天会被判违规（实测），理由写的是「来源静态不可证」而不是「它是 TestClient」——
    门并没有看穿容器，只是不再假定它无害。第二例则由 :func:`_unprovable_context_exempt`
    的 C4 显式放行（跨模块盲区，如实声明）。

  能**追到来源**的六条是：绑到局部名字（``client = TestClient(app)`` →
  ``with client:``）、存到 ``self.<attr>``、**每条 return 都是 main 实例**的本模块
  工厂（``with make():``）、海象绑定（``enter_context(c := TestClient(app))``）、
  **字面 tuple 与本模块工厂 tuple 返回值的按位解包**（``_, c = make()``，此前是
  自认漏检的「阻断项 D」）、以及**部分 return 是 main 实例**的本模块工厂
  （``with make(flag):``，`main_client_funcs` 的 all 口径漏掉的那一半）。
* 底层 socket / atexit / shell 注入等旁路由
  ``backend/scripts/lifespan_isolation_guard_probes.py`` 单独证明，不在本脚本内。

## 为什么不再原地变异（R1 Codex HIGH-6/HIGH-7 的结构性收口）

第八批到第九批 round-1 都是**原地**改真实文件再还原，于是要靠「写盘前置标志 +
finally 写回 + atexit/信号兜底 + 还原前 CAS」一整套纪律去追一个本来就不该发生的写。
Codex 指出两个洞：并发编辑会在 collect/正控期间落到目标文件上而 CAS 看不出来；
变异运行造出的运行时文件用「跑前 absent、跑后存在」判归属并 ``unlink``，可能删掉
别的进程刚写的真实数据。

现在改成在 tmp 副本上变异 —— **真实工作树的 tracked 文件与运行时文件全程一个字节
都不写**，上面那两条链条从源头消失，也就不需要 CAS 与还原纪律了。脚本仍会断言
「真实树 untouched」，把这句话变成每次运行都要过的门，而不是一句声明。
残余：副本是**复制那一刻**的快照，复制期间的并发编辑不在射程（脚本会比对副本与
工作树里目标文件的 sha，不一致即停）。
"""

from __future__ import annotations

import ast
import atexit
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
TARGET_REL = "tests/api/v1/endpoints/test_metadata_subject_mapping.py"
TARGET = BACKEND_DIR / TARGET_REL

#: 原文件里的隔离形态（必须恰好出现一次，否则说明文件已被动过，先停下来）。
ANCHOR = "with no_lifespan(app), TestClient(app) as c:"
MUTATED = "with TestClient(app) as c:"

#: 与 tests/support/live_port_guard.py 的 BLOCK_REASON 保持一致。
EXPECTED_REASON = "live Neo4j port connect attempted"

#: 与 backend/scripts/lifespan_isolation_runtime_sha.sh 的监视清单保持一致。
#:
#: 第三项是 orchestrator journal 的**旧固定名**（``legacy_state_path``，G2-5 之前的
#: 形态）。它以前靠 ``vault_index_pending*.jsonl`` 这条过宽 glob 顺带收进来；
#: M14 收窄之后 glob 只认命名空间形态，旧名必须显式列成固定项，否则监视面变窄。
RUNTIME_FILE_RELPATHS = [
    "data/bug_log.jsonl",
    "data/outbox/events.jsonl",
    "app/data/vault_index_pending.jsonl",
]

#: ⛔ 不能写成固定文件名（2026-09-04 主干合并后当场抓到的假门）：CARD-G2-5
#: （第七批）把 orchestrator 的 durable journal 从 ``app/data/vault_index_pending.jsonl``
#: 改成了 vault 命名空间下的 ``vault_index_pending__<vault_key>.jsonl``
#: （``app/core/vault_state_paths.py::namespaced_state_path``），而且 vault_key 还会
#: 因 ``NAME_MAX`` 的**字节**预算被 hash 截断 —— 文件名根本不可预先硬编码。
#: 后果分两个方向，都很难看：
#:   * 本脚本这一侧：「变异态必须写至少一个运行时文件」的正证据锚点落空 → 负控
#:     报 FAIL（fail-closed，还算诚实）；
#:   * ``runtime_sha.sh`` 那一侧：断言的是 ``unchanged``，锚点落空直接变**假绿**。
#: 所以按 stem 前缀 glob，新旧两种文件名一并收（旧的固定名也匹配）。
#:
#: 覆盖面刻意与合并前**等价**：只跟随这一个 journal 的改名，不新增监视项。
#: 同族的 ``lancedb_pending_index__<key>.jsonl``（``lancedb_index_service.py:76``）
#: 合并前就不在清单里，本卡只登记移交，不在此扩面（扩面会让 runtime_sha 变严，
#: 属于另一张卡的范围决策）。
#:
#: ⛔ M14 收窄（CARD-W4-3b，2026-09-05）：上一版写成 ``vault_index_pending*.jsonl``，
#: 比生产写侧**实际能产出的形态更宽** —— ``vault_index_pending_backup.jsonl``、
#: ``vault_index_pending.jsonl.old.jsonl`` 这类**人手放的旁文件**也会被收进监视面，
#: 于是「谁在 backend/app/data 里放了个同前缀备份」会让本门判 CHANGED（假红），
#: 而门一旦以「会误报」出名，下一个人就会去放宽它。收窄成两条**可由写侧证明**的形态：
#:   * ``legacy_state_path()`` 的旧固定名 —— 进 :data:`RUNTIME_FILE_RELPATHS` 精确项；
#:   * ``namespaced_state_path()`` 的 ``<stem>__<safe_key>.jsonl`` —— 本 glob，
#:     ``NAMESPACE_SEP`` 是双下划线（``vault_state_paths.py:36``），而
#:     ``sanitize_vault_id`` 保证 key 只含 ``\\w``、压缩形态是 ``<前缀>-<sha12>``，
#:     两者都不含 ``/``，所以 ``__*`` 恰好覆盖全部可能的 key。
#: ⚠️ 收窄是**放松**方向，证据在验收单 §M14：全仓 20 个同前缀文件逐个列出，
#: 收窄前后被收的集合**完全相同**（旧 glob 多收的那一类在真实树上一个都没有）。
RUNTIME_FILE_GLOBS = [
    "app/data/vault_index_pending__*.jsonl",
]


def runtime_files(backend_dir: Path) -> list[Path]:
    """固定项 + glob 项。

    ⚠️ glob **每次调用都重新展开** —— before 快照时文件还不存在、after 才被写出来
    正是本门要抓的情形；把展开结果缓存下来就等于抓不到新建文件。
    展开结果排序，避免文件系统顺序波动造成假 delta。
    """
    fixed = [backend_dir / rel for rel in RUNTIME_FILE_RELPATHS]
    globbed: list[Path] = []
    for pattern in RUNTIME_FILE_GLOBS:
        globbed.extend(backend_dir.glob(pattern))
    return fixed + sorted(globbed)


def run_runtime_files_selftest() -> int:
    """:func:`runtime_files` 的行为自证 —— **无条件**先于一切跑（M15 的 Python 侧）。

    X4 验收单 §7.9a #15 的缺口是「glob 修复没有任何门保护」：``runtime_sha.sh`` 那侧
    由 ``lifespan_isolation_guard_probes.py`` 的 ``runtime-glob-*`` 族补上；本函数补
    Python 这一侧。四条判据，每条都对应一种**具体的坏法**：

    1. **每次调用重新展开** —— 第一次调用时 journal 还不存在，新建之后第二次调用
       必须看得见。把展开结果缓存下来（``@lru_cache`` / 模块级列表）就抓不到
       「跑完才出现的 journal」，而那正是本门要抓的那一类。
    2. **旧固定名仍在监视面** —— M14 收窄之后它由 :data:`RUNTIME_FILE_RELPATHS`
       的精确项承接；接不住就是监视面偷偷变窄。
    3. **单下划线旁文件不在监视面** —— 收窄的正证据（写侧产不出这个形态）。
    4. **glob 项按字节序排列** —— 与**独立构造**的期望清单比对（不是拿两次调用互比：
       那只测「枚举可重复」，去掉 ``sorted()`` 照样通过，round-1 Codex MEDIUM-2），
       并**验证乱序前提**：原始枚举本次若恰好已有序，本条判据在此环境下无鉴别力，
       那就报失败说清楚，不绿着糊过去。顺序不稳会让快照因**排列不同**而字符串不等 ⇒ 假红。

    ⛔ 只在 tmp 假 backend 里造文件：真实 ``backend/app/data`` 是生产运行时数据。
    """
    print("=== RUNTIME-FILES SELFTEST ===")
    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="w4-runtime-files-selftest-"))
    try:
        fake = tmp / "backend"
        (fake / "app" / "data").mkdir(parents=True)
        (fake / "data" / "outbox").mkdir(parents=True)

        before = runtime_files(fake)
        journal = fake / "app" / "data" / "vault_index_pending__selftest.jsonl"
        if journal in before:
            problems.append("前提被破坏：journal 在创建之前就出现在监视清单里")
        journal.write_text("{}\n", encoding="utf-8")
        after = runtime_files(fake)
        if journal not in after:
            problems.append(
                "glob 没有每次重新展开：新建的 "
                f"{journal.name} 不在第二次调用的结果里（缓存展开 ⇒ 抓不到 after 才出现的 journal）"
            )

        legacy = fake / "app" / "data" / "vault_index_pending.jsonl"
        if legacy not in runtime_files(fake):
            problems.append(
                f"旧固定名 {legacy.name} 不在监视清单里 —— M14 收窄让监视面变窄了"
                "（它应由 RUNTIME_FILE_RELPATHS 的精确项承接，与文件是否存在无关）"
            )

        sidecar = fake / "app" / "data" / "vault_index_pending_backup.jsonl"
        sidecar.write_text("{}\n", encoding="utf-8")
        if sidecar in runtime_files(fake):
            problems.append(f"单下划线旁文件 {sidecar.name} 进了监视面 —— glob 比写侧能产出的形态宽（M14）")

        # ⛔ 顺序判据必须与**独立构造**的期望清单比，不能拿两次调用互比
        #    （round-1 Codex MEDIUM-2）：`runtime_files(fake) != runtime_files(fake)`
        #    两次调用之间目录没变、枚举顺序也没变，于是把 `sorted(globbed)` 改成
        #    `globbed` 照样通过 —— 它测的是「枚举可重复」，不是「排序做了」。
        data_dir = fake / "app" / "data"
        order_names = [f"vault_index_pending__{k}.jsonl" for k in ("zeta", "alpha", "Mid", "beta", "10", "2")]
        for name in order_names:
            (data_dir / name).write_text("{}\n", encoding="utf-8")
        raw = list(data_dir.glob("vault_index_pending__*.jsonl"))
        # 期望清单**逐个列举**（含判据 1 那步建的 journal），不拿 glob 结果当期望 ——
        # 用被测的东西算期望就成了自证。
        expected = sorted(data_dir / n for n in [*order_names, journal.name])
        got = [p for p in runtime_files(fake) if p.name.startswith("vault_index_pending__")]
        if got != expected:
            problems.append(f"glob 项没有按字节序排列：实得 {[p.name for p in got]}，期望 {[p.name for p in expected]}")
        # 前提验证：这一批名字在**本次运行的这个文件系统上**确实枚举乱序。
        # 前提不成立 ⇒ 上面那条判据在此环境下无鉴别力（去掉 sorted 也会通过），
        # 那就不能声称「排序承重已验证」—— fail-closed 说出来，而不是绿着糊过去。
        if raw == sorted(raw):
            problems.append(
                "顺序判据无鉴别力：原始 glob 枚举本次恰好已是字节序 "
                f"（{[p.name for p in raw]}），去掉 sorted() 也会通过 —— 排序承重未验证"
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if problems:
        print("RUNTIME-FILES-SELFTEST: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(
        "RUNTIME-FILES-SELFTEST: PASS "
        f"({len(RUNTIME_FILE_RELPATHS)} 固定项 + {len(RUNTIME_FILE_GLOBS)} glob；"
        "重新展开 / 旧名在册 / 旁文件排除 / 按字节序排列（乱序前提已验证）四条全过)"
    )
    return 0


#: 钉死的**完整 nodeid**（第八批 Codex MEDIUM：此前用 ``-k`` 子串过滤 + 名字
#: substring 判定，三个名字加任意后缀仍能满足「身份钉死」）。这里直接把完整
#: nodeid 当 pytest 参数传，并对预采集集做**集合全等**比对。
FIXED_TARGET_NODEIDS = (
    f"{TARGET_REL}::TestGetSubjectMapping::test_get_returns_200",
    f"{TARGET_REL}::TestAddSubjectMapping::test_add_returns_200",
    f"{TARGET_REL}::TestRemoveSubjectMapping::test_remove_nonexistent_returns_404",
)

PYTEST_TIMEOUT_S = 1500

#: 门的汇总行必须**整行唯一**匹配，且 total==blocked>0、advisory==unaccounted==0
#: （第八批 Codex HIGH：旧版只取 total/blocked 且只要求 blocked>=1，
#: ``attempts=7 (blocked=3, advisory=4, unaccounted=0)`` 会通过——而 advisory
#: 那 4 次已经调用了原始 connect，也就是真连过）。
SUMMARY_RE = re.compile(
    r"^NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=(\d+) "
    r"\(blocked=(\d+), advisory=(\d+), unaccounted=(\d+)\)$"
)

# ═══════════════════════════════════════════════════════════════════════════
# AST 门 —— 静态扫描「裸 with TestClient(app.main 的 app)」
# ═══════════════════════════════════════════════════════════════════════════

#: 扫描范围：``backend/tests/`` 下**除 integration / e2e 之外的全部 .py**。
#:
#: 第八批只扫 ``tests/api`` + ``tests/unit`` + 三个具名根文件（259 个），
#: ``tests/regression``、``tests/contract``、``tests/bdd``、``tests/smoke`` 以及其余
#: 根级 ``tests/*.py`` 都在盲区里 —— 那些文件里今天没有 ``with TestClient(app.main
#: 的 app)``（它们用的是**不带 with** 的 ``TestClient(app)``，Starlette 只在
#: ``__enter__`` 里跑 lifespan，所以不触发启动副作用），但没有任何东西拦着谁明天
#: 加一个。2026-09-03 实测扩到全量后为 371 个文件、**0 违规**，扩射程是纯增益。
#:
#: ``tests/integration`` 与 ``tests/e2e`` 仍在射程外：它们按路径豁免（只记录不拦截），
#: 本来就允许跑真实 lifespan —— 这是卡文裁决的既定设计，不是遗漏。
AST_EXCLUDED_TOP_DIRS = ("integration", "e2e")
AST_ROOT = "tests"

#: 同一 with 语句里允许充当隔离基元的名字（必须真的 import 自 tests.support.lifespan）。
ISOLATION_HELPER_NAMES = {"no_lifespan", "lifespan_lite"}

#: 会触发 ``__enter__`` 的方法名（``ExitStack`` / ``AsyncExitStack``）。
#: 走这条路进入的 TestClient 同样会跑真实 lifespan（R1 Codex HIGH-8）。
_ENTER_CONTEXT_ATTRS = {"enter_context", "enter_async_context"}
#: ``ExitStack.enter_context(self, cm)`` / ``AsyncExitStack.enter_async_context(self, cm)``
#: 的那个形参名 —— 关键字调用走它（CARD-W4-5 (a)）。
_ENTER_CONTEXT_CM_PARAM = "cm"
#: ``with (a if c else b):`` 的展开深度上限。超过就 fail-closed 记违规，不静默放行。
_IFEXP_MAX_DEPTH = 8

#: TestClient 的合法来源模块。
TESTCLIENT_MODULES = {"fastapi.testclient", "starlette.testclient"}
#: FastAPI 类的合法来源模块。
FASTAPI_MODULES = {"fastapi", "fastapi.applications"}

# 来源标签
O_MAIN_APP = "app.main:app"  # app.main 的进程级单例 app
O_MAIN_MODULE = "app.main:module"  # app.main 模块对象（供 m.app）
O_FASTAPI_CLASS = "fastapi:FastAPI"  # 真正 import 来的 FastAPI 类
O_FASTAPI_MODULE = "fastapi:module"  # fastapi 模块对象（供 fastapi.FastAPI()）
O_LOCAL_APP = "local:FastAPI()"  # 由**可证的** FastAPI 类构造出来的局部 app
O_TESTCLIENT_CLASS = "testclient:TestClient"
O_TESTCLIENT_MODULE = "testclient:module"


class _InstanceMain(NamedTuple):
    """由 app.main 的 app 构造出来的 TestClient **实例**（还没进 with，所以还没跑
    lifespan；一旦进了 with / enter_context 就会跑）。R1 Codex HIGH-8。

    ``app_ref`` 是**它包的那个 app 的引用路径**（``app`` / ``m.app``）——检查
    「外层 ``with no_lifespan(X)``」时要比对的是 X 而不是客户端变量名；静态取不到
    时为 ``None``（fail-closed，:meth:`_flag_instance_context` 里直接判违规）。

    ⛔ 这里是**结构化载体**，不是旧的 ``"testclient:instance(app.main):<name>"``
    字符串编码（CARD-W4-5 (e)，X4 HIGH）。字符串版有两个各自独立的不可证面：

    1. **取值靠切片**：``origin[len(前缀)+1:]`` 假定 app 名里不含分隔符。本卡把
       ``app_ref`` 从「名字」扩到「属性链路径」（``m.app``）之后这个假定就更脆——
       任何一次分隔符选择失误都会静默取回半截名字，而半截名字照样能与某个
       ``no_lifespan(X)`` 比对**成功**，于是漏放。
    2. **判型靠 startswith**：将来任何一个恰好以该前缀开头的新来源标签都会被
       ``_is_instance_main`` 认成 main 实例。前缀是全局字符串空间里的约定，不是
       类型；约定不会在加新标签时提醒你。

    换成 NamedTuple 后，「是不是 main 实例」= :func:`isinstance`、「它包的是谁」=
    字段读取，两者都不再依赖字符串形状。NamedTuple 而不是 dataclass 是因为 origin
    要进 ``set``（:meth:`resolve_name` 的「全部绑定必须同源」判据）——它天然可哈希。
    """

    app_ref: str | None

    def __str__(self) -> str:  # 违规文案里 `解析结果={origin}` 要人能读
        return f"testclient:instance(app.main):{self.app_ref or '?'}"


def _instance_main(app_ref: str | None) -> _InstanceMain:
    return _InstanceMain(app_ref)


def _instance_app_name(origin: object) -> str | None:
    """从实例来源里取回它包的 app 引用路径；不是 main 实例则 None。"""
    return origin.app_ref if isinstance(origin, _InstanceMain) else None


def _is_instance_main(origin: object) -> bool:
    return isinstance(origin, _InstanceMain)


def _ref_path(expr: ast.expr | None) -> str | None:
    """表达式的**可写出来的引用路径**：``x`` → ``"x"``；``m.app`` → ``"m.app"``。

    只认「最终 base 是 :class:`ast.Name` 的属性链」——``f().app`` / ``d["k"].app``
    这类每次求值都可能是不同对象的形态一律 ``None``（取不到路径 ⇒ 上游 fail-closed）。

    它是 (e) 的另一半：有了路径，``TestClient(m.app)`` 才能与 ``no_lifespan(m.app)``
    比对上（旧实现只认 :class:`ast.Name`，于是那个合法写法被判违规）。
    """
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        base = _ref_path(expr.value)
        return None if base is None else f"{base}.{expr.attr}"
    return None


#: 一个名字/表达式的**来源标签**：本模块那些 ``O_*`` 字符串常量之一，或结构化的
#: :class:`_InstanceMain`（CARD-W4-5 (e) 把 main 实例从字符串编码换成了载体）。
#: 两者都可哈希 —— :meth:`_ModuleIndex.resolve_name` 的「全部绑定必须同源」判据
#: 要把它们放进 ``set``。
Origin = str | _InstanceMain


#: 由局部 FastAPI() 构造出来的 TestClient 实例 —— 进 with 也无害。
O_TESTCLIENT_INSTANCE_LOCAL = "testclient:instance(local)"
O_HELPER = "tests.support.lifespan:helper"
#: ``import somelib as m`` 里那个 **module 对象**（不在已知模块表里的那些）。
#: 与 unknown 分开是 (c)-C4 的判据基础：模块对象的属性不由本模块构造，
#: 属跨模块盲区；unknown 则可能就是本模块自己造的 TestClient 实例。
O_IMPORTED_MODULE = "module:imported"
#: 本模块 ``def`` 出来的函数名（``localfunc:<name>``）。有了它，「这个名字此刻
#: 还是不是本模块那个 def」可证 —— 被赋值重绑定后解析结果就变了。
O_LOCAL_FUNC_PREFIX = "localfunc:"
O_UNKNOWN = "unknown"

#: 「这个名字绑着一个 **module 对象**」的全部来源标签（(c)-C4）。
_MODULE_OBJECT_ORIGINS = {O_IMPORTED_MODULE, O_MAIN_MODULE, O_FASTAPI_MODULE, O_TESTCLIENT_MODULE}


def _module_has_testclient(tree: ast.Module) -> bool:
    """本模块 AST 里有没有 TestClient 的可达性（(c)-C3 的判据）。

    四条命中面，取并集（宽，因为它是**放行**条件——放行条件宽了就是漏，所以要尽量
    命中）：词法上出现 ``TestClient`` 名字或属性、``from fastapi/starlette.testclient
    import ...``（覆盖 ``as TC`` 别名）、``import fastapi.testclient``。
    """
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id == "TestClient":
            return True
        if isinstance(n, ast.Attribute) and n.attr == "TestClient":
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "") in TESTCLIENT_MODULES:
            return True
        if isinstance(n, ast.Import) and any(a.name in TESTCLIENT_MODULES for a in n.names):
            return True
        if isinstance(n, ast.alias) and (n.asname or n.name).split(".")[-1] == "TestClient":
            return True
    return False


_POS_MAX = (10**9, 0)


def _pos(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


class _Scope:
    """一个 Python 作用域的**有序**绑定表。

    绑定按 ``(lineno, col_offset)`` 排序保存，因此可以做「该使用点之前最后一次
    绑定是什么」的 reaching-definition 判断（第八批 Codex HIGH：旧版是扁平集合，
    ``with TestClient(app)`` 之后再写 ``app = FastAPI()`` 也会被当成局部应用）。
    """

    __slots__ = ("node", "parent", "kind", "bindings")

    def __init__(self, node, parent, kind: str) -> None:
        self.node = node
        self.parent = parent
        self.kind = kind  # module | function | class
        self.bindings: dict[str, list[tuple[tuple[int, int], Origin]]] = {}

    def bind(self, name: str, pos: tuple[int, int], origin: Origin) -> None:
        self.bindings.setdefault(name, []).append((pos, origin))

    def sorted_bindings(self, name: str) -> list[tuple[tuple[int, int], Origin]]:
        return sorted(self.bindings.get(name, ()), key=lambda b: b[0])


class _ModuleIndex:
    """一次 ``ast.parse`` 的作用域索引 —— 追踪真实 import、语句顺序与重绑定。

    与第八批版本的三处结构性差别（均为 Codex HIGH 的直接整改）：

    1. **来源要可证**：``FastAPI()`` 只有在被调用的那个名字**解析得到真正从
       ``fastapi`` import 来的类**时才算局部应用；本地 ``def FastAPI(): ...``
       之类一律 unknown（= 违规）。
    2. **顺序要对**：同作用域内按位置取「使用点之前的最后一次绑定」；只在使用点
       之后才绑定的名字 = unknown。
    3. **重绑定要失效**：``no_lifespan`` 被本地 def / 赋值重新绑定后，该使用点
       解析到的就不再是 ``O_HELPER``，隔离资格随之失效。

    另外类体是**独立作用域**（Python 语义如此），不再把 ``class C: app = FastAPI()``
    的绑定漏进模块/函数作用域。
    """

    def __init__(self, tree: ast.Module) -> None:
        #: 「返回局部 FastAPI() 的函数」名集（名字级过程间近似）：正例文件
        #: （test_rag_four_state_api 等）的模式是 helper 内 ``app = FastAPI()``
        #: 然后 return，测试里元组解包后传入 TestClient —— 不识别会把正例
        #: 误判成 unknown 违规。近似是**单向放宽**且要求「函数体内确有由可证
        #: FastAPI 类构造的赋值 + return 同一个名字」，冒用面极窄。
        self.fastapi_returning_funcs: set[str] = set()
        #: 失格的工厂 key —— 同名多定义时「任一定义不合格 ⇒ 整个 key 不合格」。
        #: 见 :meth:`_mark_fastapi_returning` 里的说明（阻断项 E）。
        #: ⛔ 与 :attr:`fastapi_returning_funcs` **每轮一起重建**，两者都不累积
        #: （M16 + round-1 Codex HIGH-1：只重建其中一个会造成暂态资格传播）。详见
        #: :meth:`_mark_all_fastapi_returning` 的 docstring。
        self.disqualified_factory_keys: set[str] = set()
        #: 本轮扫描的逐 key 裁定（``key -> 全部定义都合格``），轮末发布成上面两个集合。
        #: 扫描期间**不**被 :meth:`_is_local_app_factory_call` 读到 —— 那正是要点。
        self._factory_verdicts: dict[str, bool] = {}
        #: 「每一条 return 都返回 app.main 的 TestClient 实例」的函数（`类名.方法名`
        #: 或 `<module>.函数名`）—— `with make():` 会跑真实 lifespan（L2-d）。
        self.main_client_funcs: set[str] = set()
        #: `self.<attr> = TestClient(app.main 的 app)` —— 记 `类名.attr`，
        #: 让 `with self.<attr>:` 也能被抓（L2-b）。
        self.main_client_attrs: set[str] = set()
        #: 本模块里**自建的隔离包装器**：`<owner>.<name>` → 被隔离的那个形参下标。
        #: 形态必须窄到可证（见 :meth:`_mark_isolation_wrappers`）。
        self.isolation_wrappers: dict[str, int] = {}
        #: 返回 tuple 的本模块工厂：`key` → **每个位置**各自的来源。供调用方解包时
        #: 按位配对（CARD-W4-5 (d)），取代「整体来源原样传给每个元素」的旧扩散。
        #: 与上面几个集合同为迭代状态 ⇒ 一并进 M16 不动点判据。
        self.factory_return_elts: dict[str, tuple] = {}
        #: **存在**一条 return 是 main 实例、但不是条条都是的函数 —— :attr:`main_client_funcs`
        #: 的 all 口径漏掉的那一半。(c)-C2 用它把「调用面」里本模块可证的可疑部分
        #: 收回来 fail-closed，而不是整个调用面放行。同为迭代状态 ⇒ 进 M16。
        self.partial_main_client_funcs: set[str] = set()
        #: 本模块 AST 里有没有 TestClient 的可达性（(c)-C3 的判据）。
        #: ⛔ 必须是 **AST 级**而不是文本 grep：`tests/support/live_port_guard.py`
        #: 的 "TestClient" 只出现在 docstring 里（:34/:54），文本判据会把一个零
        #: TestClient 的文件当成有可达性，于是它那 7 处 `with self._lock:` 全被
        #: fail-closed 判违规 —— 而该文件是别的卡的地盘，改不动，门就永远红。
        self.module_has_testclient = _module_has_testclient(tree)
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of: dict[int, _Scope] = {}
        # 建表与「哪些函数返回局部 app」互为输入 —— 迭代到不动点，最后再建一次表，
        # 保证对外暴露的 scopes 反映的是**最终**知识（否则验伪锚 4 那种
        # `app, n = make()` 会被建表期的空知识判成 unknown）。
        for _ in range(4):
            self._rebuild(tree)
            before = (
                set(self.fastapi_returning_funcs),
                set(self.main_client_funcs),
                set(self.main_client_attrs),
                dict(self.isolation_wrappers),
                # M16 之后失格名单每轮重算 ⇒ 它也是迭代状态的一部分，必须进
                # 不动点判据；漏掉它，「失格集还在变」的那一轮会被当成已收敛。
                set(self.disqualified_factory_keys),
                # CARD-W4-5 (d)：逐位来源表跨轮变化（工厂 return 里的元素来源要等
                # `fastapi_returning_funcs` 收敛后才算得准），同样必须进判据。
                dict(self.factory_return_elts),
                # CARD-W4-5 (c)：部分-main 工厂集同理，跟着 main 实例解析一起变。
                set(self.partial_main_client_funcs),
            )
            # 可信集与失格集在 `_mark_all_fastapi_returning` 内部**一起**发布
            # （冻结知识 + 按 key 聚合 + 整组通过才发布，见该方法 docstring）。
            self._mark_all_fastapi_returning(tree)
            self._mark_main_client_sources(tree)
            self._mark_isolation_wrappers(tree)
            if (
                self.fastapi_returning_funcs,
                self.main_client_funcs,
                self.main_client_attrs,
                self.isolation_wrappers,
                self.disqualified_factory_keys,
                self.factory_return_elts,
                self.partial_main_client_funcs,
            ) == before:
                break
        self._rebuild(tree)

    def _rebuild(self, tree: ast.Module) -> None:
        self.module_scope = _Scope(tree, None, "module")
        self.scope_of = {}
        # 父链：用来找「支配本 with 的外层 with」（R1 Codex MEDIUM-13）
        self.parents: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parents[id(child)] = node
        self._build_scope(tree.body, self.module_scope)

    # ── 作用域构建 ──────────────────────────────────────────────────────
    def _build_scope(self, body, scope: _Scope) -> None:
        for stmt in body:
            self._walk_stmt(stmt, scope)

    def _walk_stmt(self, stmt: ast.stmt, scope: _Scope) -> None:
        """把 stmt 记进 scope；遇到新作用域则建子作用域，不把绑定漏给父层。"""
        self.scope_of[id(stmt)] = scope

        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 专门的来源标签：这样「这个名字此刻确实还是本模块那个 def」可以被
            # 证明；被后续赋值重绑定后解析结果就不再是它，工厂近似随之失效。
            scope.bind(stmt.name, _pos(stmt), f"{O_LOCAL_FUNC_PREFIX}{stmt.name}")
            child = _Scope(stmt, scope, "function")
            for arg in self._all_args(stmt.args):
                child.bind(arg.arg, (0, 0), O_UNKNOWN)  # 形参：来源不可证
            self._build_scope(stmt.body, child)
            return
        if isinstance(stmt, ast.ClassDef):
            scope.bind(stmt.name, _pos(stmt), O_UNKNOWN)
            child = _Scope(stmt, scope, "class")
            self._build_scope(stmt.body, child)
            return

        self._record_bindings(stmt, scope)
        self._record_walrus(stmt, scope)

        # 非作用域语句：递归其子块，绑定仍归当前 scope
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            block = getattr(stmt, field, None)
            if not block:
                continue
            for sub in block:
                if isinstance(sub, ast.stmt):
                    self._walk_stmt(sub, scope)
                else:  # ExceptHandler / match_case 容器
                    self.scope_of[id(sub)] = scope
                    # ``except E as name`` —— ExceptHandler 有 .name，这条早就在
                    name = getattr(sub, "name", None)
                    if isinstance(name, str):
                        scope.bind(name, _pos(sub), O_UNKNOWN)
                    # ``match … case X() as c`` —— match_case **没有** .name 属性，
                    # 上面那行对它恒取不到，于是整族 capture 名此前从不入表
                    # （CARD-W4-5 (d)）。捕获名进表后它才会遮蔽同名的外层绑定，
                    # 否则 `case _ as app:` 之后的 `TestClient(app)` 仍按外层那个
                    # 可证 app 解析 —— 静默放行。
                    self._record_match_captures(getattr(sub, "pattern", None), scope)
                    for inner in getattr(sub, "body", []) or []:
                        self._walk_stmt(inner, scope)

    def _record_match_captures(self, pattern, scope: _Scope) -> None:
        """把 match 模式里的捕获名绑成 :data:`O_UNKNOWN`（来源不可证）。

        三类捕获：``MatchAs.name``（``case x:`` / ``case P() as x:``）、
        ``MatchStar.name``（``case [*rest]:``）、``MatchMapping.rest``
        （``case {**rest}:``）。守卫表达式里的海象另由 :meth:`_record_walrus` 覆盖。
        """
        if pattern is None:
            return
        for pat in ast.walk(pattern):
            cap = None
            if isinstance(pat, (ast.MatchAs, ast.MatchStar)):
                cap = pat.name
            elif isinstance(pat, ast.MatchMapping):
                cap = pat.rest
            if isinstance(cap, str):
                scope.bind(cap, _pos(pat), O_UNKNOWN)

    def _own_exprs(self, node: ast.AST):
        """``node`` 自己那一层的表达式子树 —— 不进入语句，也不进入 lambda。

        进入子语句会让同一个海象被父语句与子语句各绑一次（无害但冗余）；进入
        lambda 则是**错的**：lambda 体里的 ``:=`` 绑定的是 lambda 自己的作用域。
        推导式**不**排除——PEP 572 明确规定推导式里的海象绑定到外层作用域。
        """
        stack: list[ast.AST] = [node]
        while stack:
            cur = stack.pop()
            for child in ast.iter_child_nodes(cur):
                if isinstance(child, (ast.stmt, ast.Lambda)):
                    continue
                yield child
                stack.append(child)

    def _record_walrus(self, stmt: ast.stmt, scope: _Scope) -> None:
        """海象 ``(x := v)``：在**当前**作用域绑定（CARD-W4-5 (d)）。

        它此前整族不入表，于是 ``stack.enter_context(client := TestClient(app))``
        里的 ``client`` 解析不到任何绑定 ⇒ ``O_UNKNOWN`` ⇒ 旧的 unknown 放行分支
        直接过。绑定位置取海象自己的 ``(lineno, col_offset)``，因为它在**表达式求值
        那一刻**才生效——写在使用点之后的海象不该影响使用点（reaching-definition
        口径与 :meth:`resolve_name` 一致）。
        """
        for sub in self._own_exprs(stmt):
            if isinstance(sub, ast.NamedExpr):
                # NamedExpr.target 的类型就是 Name（语法上不可能是别的）
                scope.bind(sub.target.id, _pos(sub), self._value_origin(sub.value, stmt, scope))

    @staticmethod
    def _all_args(a: ast.arguments):
        return [
            *a.posonlyargs,
            *a.args,
            *a.kwonlyargs,
            *([a.vararg] if a.vararg else []),
            *([a.kwarg] if a.kwarg else []),
        ]

    def _record_bindings(self, stmt: ast.stmt, scope: _Scope) -> None:
        pos = _pos(stmt)
        if isinstance(stmt, ast.ImportFrom):
            mod = stmt.module or ""
            for alias in stmt.names:
                bound = alias.asname or alias.name
                origin = O_UNKNOWN
                if mod == "app.main" and alias.name == "app":
                    origin = O_MAIN_APP
                elif mod in TESTCLIENT_MODULES and alias.name == "TestClient":
                    origin = O_TESTCLIENT_CLASS
                elif mod in FASTAPI_MODULES and alias.name == "FastAPI":
                    origin = O_FASTAPI_CLASS
                elif mod == "fastapi" and alias.name == "testclient":
                    origin = O_TESTCLIENT_MODULE
                elif mod == "tests.support.lifespan" and alias.name in ISOLATION_HELPER_NAMES:
                    origin = O_HELPER
                elif mod == "app" and alias.name == "main":
                    origin = O_MAIN_MODULE
                scope.bind(bound, pos, origin)
            return
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                # `import a.b` 绑定的是**顶层包** `a`；`import a.b as x` 绑定 `x` = a.b
                bound = alias.asname or alias.name.split(".")[0]
                # import 出来的东西**一定是模块对象**——这件事本身可证，与「是不是
                # 我们认识的那个模块」无关。分开记，(c)-C4 才能凭它放行
                # `mod._refresh_guard` 这类跨模块属性而不必放行全部 unknown。
                origin = O_IMPORTED_MODULE
                if alias.asname:
                    if alias.name == "app.main":
                        origin = O_MAIN_MODULE
                    elif alias.name in TESTCLIENT_MODULES:
                        origin = O_TESTCLIENT_MODULE
                    elif alias.name == "fastapi":
                        origin = O_FASTAPI_MODULE
                elif bound == "fastapi":
                    # `import fastapi` 与 `import fastapi.testclient` 绑定的都是
                    # **顶层 fastapi 模块**这同一个对象，来源相同。若这里只认前者，
                    # 两条 import 并存时「全部绑定必须一致」会把 fastapi 判成 unknown，
                    # 于是 `fastapi.testclient.TestClient(...)` 整条链解析失败（误报）。
                    origin = O_FASTAPI_MODULE
                # `import app.main`（无 asname）绑定的是包 `app` —— 保持 unknown；
                # `app.main.app` 这种链式属性由 _attribute_origin 的专门分支解析。
                scope.bind(bound, pos, origin)
            return
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = getattr(stmt, "value", None)
            if isinstance(stmt, ast.Assign):
                targets = stmt.targets
            elif isinstance(stmt, ast.AnnAssign):
                targets = [stmt.target]
            else:
                targets = [stmt.target]
            if value is None:
                for t in targets:
                    self._bind_target(t, pos, O_UNKNOWN, scope)
                return
            origin = self._value_origin(value, stmt, scope)
            for t in targets:
                self._bind_target(t, pos, origin, scope, value=value, stmt=stmt)
            return
        if isinstance(stmt, ast.Delete):
            # ``del app`` —— 名字此后不再绑着原来那个对象（CARD-W4-5 (d)）。
            # 不绑的话 `del` 之后重新赋值成生产 app 时，「全部先前绑定必须同源」
            # 会把已经作废的那条局部 app 绑定也算进去 ⇒ 两条不同源 ⇒ 恰好 unknown；
            # 但只 del 不重绑的写法则会让作废的绑定**单独**成为唯一来源 ⇒ 误放行。
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    scope.bind(t.id, pos, O_UNKNOWN)
            return
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                var = item.optional_vars
                if var is not None:
                    self._bind_target(var, pos, O_UNKNOWN, scope)
            return
        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            self._bind_target(stmt.target, pos, O_UNKNOWN, scope)
            return
        if isinstance(stmt, (ast.Global, ast.Nonlocal)):
            for name in stmt.names:
                scope.bind(name, pos, O_UNKNOWN)
            return

    def _bind_target(self, target: ast.expr, pos, origin, scope: _Scope, value=None, stmt=None) -> None:
        if isinstance(target, ast.Name):
            scope.bind(target.id, pos, origin)
            return
        if isinstance(target, ast.Starred):
            # ``a, *rest = …`` —— rest 绑的是一个**列表**，不是原来那个元素。
            self._bind_target(target.value, pos, O_UNKNOWN, scope)
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            # 解包：**逐元素**配对，配不上就每个元素一律 unknown（CARD-W4-5 (d)）。
            # 旧实现把整体来源原样传给每个元素，两个方向同时错：
            #   * 放宽 —— `def make(): return FastAPI(), TestClient(app.main.app)`
            #     整体判成 O_LOCAL_APP，于是 `_, c = make()` 里的 c 也成了「局部
            #     app」，`with c:` 静默放行（模块 docstring 自认的阻断项 D）；
            #   * 收紧 —— `n` 这种明明是常量的位置也被当成 app 来源。
            elts = self._unpack_element_origins(target, value, stmt, scope)
            for i, elt in enumerate(target.elts):
                # 嵌套解包 `(a, b), c = …` 不再往下传 value：配对只做一层，
                # 更深的层次拿不出可证的位置对应关系。
                self._bind_target(elt, pos, elts[i] if elts is not None else O_UNKNOWN, scope)

    def _unpack_element_origins(self, target, value, stmt, scope: _Scope):
        """解包时每个位置**各自**的来源；对不上返回 ``None``（调用方全判 unknown）。

        两种可证的配对，且只有两种：

        * 右侧是**字面** tuple/list 且长度相同 —— 逐元素各求各的来源；
        * 右侧是本模块工厂调用且 :attr:`factory_return_elts` 里有它的逐位表 ——
          按位置取（表本身要求该工厂的**每一条** return 都是同宽 tuple 且同位同源，
          见 :meth:`_mark_main_client_sources`）。

        带 ``*`` 的目标一律放弃：星号吸收的元素个数静态不定，位置对不上。
        """
        if value is None or stmt is None:
            return None
        if any(isinstance(e, ast.Starred) for e in target.elts):
            return None
        if isinstance(value, (ast.Tuple, ast.List)):
            if len(value.elts) != len(target.elts) or any(isinstance(e, ast.Starred) for e in value.elts):
                return None
            return [self._value_origin(e, stmt, scope) for e in value.elts]
        if isinstance(value, ast.Call):
            cols = self._factory_return_elts_for(value, stmt, scope)
            if cols is not None and len(cols) == len(target.elts):
                return list(cols)
        return None

    def _callee_factory_key(self, func: ast.expr, node: ast.AST, scope: _Scope) -> str | None:
        """这次调用指向哪个本模块工厂 key；形态与 :meth:`_is_local_app_factory_call`
        同口径（裸名字必须仍绑着本模块那个 def，或 ``self.``/``cls.`` 的同类方法），
        够不上就 ``None`` —— 刻意不接受 ``other.make()``（谁都能有个同名方法）。"""
        if isinstance(func, ast.Name):
            if self.resolve_name(func.id, _pos(node), scope) != f"{O_LOCAL_FUNC_PREFIX}{func.id}":
                return None
            return f"<module>.{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in ("self", "cls"):
            return f"{self._enclosing_class_name(node)}.{func.attr}"
        return None

    def _factory_return_elts_for(self, call: ast.Call, node: ast.AST, scope: _Scope):
        """这次调用命中哪个本模块工厂的逐位来源表；够不上就 ``None``。"""
        key = self._callee_factory_key(call.func, node, scope)
        return None if key is None else self.factory_return_elts.get(key)

    def factory_returns_any_main(self, func: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """这次调用的目标工厂里**存在**一条返回 main 实例的 return（CARD-W4-5 (c)）。

        :attr:`main_client_funcs` 要求条条都是，于是::

            def make(flag):
                if flag:
                    return TestClient(app)     # app.main 的 app
                return other
            with make(True): ...               # 跑真实 lifespan

        整个从判定里漏掉。这条让 (c)-C2 的「调用面归属跨函数盲区」不是无条件放行：
        本模块内可证的可疑调用照样 fail-closed。
        """
        key = self._callee_factory_key(func, node, scope)
        return key is not None and key in self.partial_main_client_funcs

    def attribute_base_is_module(self, expr: ast.Attribute, node: ast.AST, scope: _Scope) -> bool:
        """``<import 来的模块>.<attr>``（CARD-W4-5 (c)-C4 的判据）。

        模块对象的属性不由本模块构造 —— 它要真是个 TestClient 实例，那也是**别的
        模块**造的，属跨模块盲区（与 C2 同族，模块 docstring 已声明）。与「放行全部
        unknown」的区别在于：这里「它是个模块」这件事本身可证（import 语句语义）。
        """
        base = expr.value
        if not isinstance(base, ast.Name):
            return False
        return self.resolve_name(base.id, _pos(node), scope) in _MODULE_OBJECT_ORIGINS

    def _value_origin(self, value: ast.expr, stmt: ast.stmt, scope: _Scope) -> Origin:
        """赋值右侧的来源。只有**可证**的形态才给非 unknown。"""
        if isinstance(value, ast.Call):
            callee = self._callable_origin(value.func, stmt, scope)
            if callee == O_FASTAPI_CLASS:
                return O_LOCAL_APP
            if self._is_local_app_factory_call(value.func, stmt, scope):
                return O_LOCAL_APP
            # TestClient(...) 的**实例**：记下它包的是哪种 app，供
            # `with client:` / `enter_context(client)` 追踪（R1 Codex HIGH-8）
            if self.is_testclient_call(value, stmt, scope):
                app_arg = self.testclient_app_arg(value)
                if app_arg is None:
                    return _instance_main(None)  # 无参/取不到 ⇒ fail-closed
                origin = self.resolve_arg(app_arg, stmt, scope)
                if origin == O_LOCAL_APP:
                    return O_TESTCLIENT_INSTANCE_LOCAL
                # 引用路径扩到**来源可证的属性链**（``m.app``，CARD-W4-5 (e)）：
                # 旧实现只认 ast.Name，于是 `with no_lifespan(m.app), TestClient(m.app)`
                # 里的 app_ref 恒为 None，隔离比对根本不发生 ⇒ 合法写法被判违规。
                # 属性链只有在**自身解析得出非 unknown 来源**时才给路径 —— 否则
                # `whatever.app` 这种谁都能冒充的写法会拿到一个可比对的名字。
                if isinstance(app_arg, ast.Attribute) and origin != O_UNKNOWN:
                    return _instance_main(_ref_path(app_arg))
                return _instance_main(app_arg.id if isinstance(app_arg, ast.Name) else None)
            # 本模块里「每一条 return 都返回 app.main 实例」的工厂：`with make():`
            # 同样会跑 lifespan（L2-d）。
            if self._is_main_client_factory_call(value.func, stmt, scope):
                return _instance_main(None)
            return O_UNKNOWN
        if isinstance(value, ast.Name):
            return self.resolve_name(value.id, _pos(stmt), scope)
        if isinstance(value, ast.Attribute):
            return self._attribute_origin(value, stmt, scope)
        return O_UNKNOWN

    def _is_local_app_factory_call(self, func: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """本模块内「返回局部 FastAPI() 的工厂」调用形态。

        两种、且只有两种：
          * ``make()`` —— 裸名字，必须是本模块 def 出来的那个名字；
          * ``self.make()`` / ``cls.make()`` —— 同类方法（``test_rag_four_state_api``
            的 ``self._real_service_client()`` 就是这一形态）。

        **刻意不接受** ``other.make()``：``other`` 的类型无法静态证明，任何对象
        只要有个同名方法就能冒充局部工厂 —— 那是把 fail-closed 拆掉。
        """
        if isinstance(func, ast.Name):
            if f"<module>.{func.id}" not in self.fastapi_returning_funcs:
                return False
            # 名字此刻必须仍绑定到本模块那个 def（重绑定后不再算数）
            return self.resolve_name(func.id, _pos(node), scope) == f"{O_LOCAL_FUNC_PREFIX}{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id not in ("self", "cls"):
                return False
            # 按**调用点所在的那个类**限定（R1 Codex HIGH-11：同名方法跨类污染）
            owner = self._enclosing_class_name(node)
            return f"{owner}.{func.attr}" in self.fastapi_returning_funcs
        return False

    def _callable_origin(self, func: ast.expr, node: ast.AST, scope: _Scope) -> Origin:
        if isinstance(func, ast.Name):
            return self.resolve_name(func.id, _pos(node), scope)
        if isinstance(func, ast.Attribute):
            return self._attribute_origin(func, node, scope)
        return O_UNKNOWN

    def _attribute_origin(self, attr: ast.Attribute, node: ast.AST, scope: _Scope) -> Origin:
        """属性访问的来源。**递归**解析 base，从而支持完整属性链。

        R1 Codex MEDIUM-13：``fastapi.testclient.TestClient(...)`` 是
        ``Attribute(Attribute(Name('fastapi'), 'testclient'), 'TestClient')``，
        旧实现只认 base 是 ``Name`` 的一层，整条链解析不出来 → 误判。
        """
        base = attr.value
        # app.main.app（`import app.main` 之后绑定的是顶层包 `app`）
        if (
            isinstance(base, ast.Attribute)
            and isinstance(base.value, ast.Name)
            and base.value.id == "app"
            and base.attr == "main"
            and attr.attr == "app"
        ):
            return O_MAIN_APP
        if isinstance(base, ast.Name):
            base_origin = self.resolve_name(base.id, _pos(node), scope)
        elif isinstance(base, ast.Attribute):
            base_origin = self._attribute_origin(base, node, scope)
        else:
            return O_UNKNOWN
        if base_origin == O_MAIN_MODULE and attr.attr == "app":
            return O_MAIN_APP
        if base_origin == O_TESTCLIENT_MODULE and attr.attr == "TestClient":
            return O_TESTCLIENT_CLASS
        if base_origin == O_FASTAPI_MODULE and attr.attr == "FastAPI":
            return O_FASTAPI_CLASS
        if base_origin == O_FASTAPI_MODULE and attr.attr == "testclient":
            return O_TESTCLIENT_MODULE
        return O_UNKNOWN

    # ── FastAPI-returning helper 识别 ───────────────────────────────────
    def _mark_all_fastapi_returning(self, tree: ast.Module) -> None:
        """两轮：先按「可证 FastAPI 类」标一轮，再让 helper 调 helper 收敛一次。

        ⛔ **冻结知识 + 按 key 聚合 + 整组通过才发布**（M16 修复，CARD-W4-3b
        2026-09-05；round-1 Codex HIGH-1 的整改）。

        **原缺陷（M16）**：:attr:`disqualified_factory_keys` 跨迭代累积、一旦失格
        不再翻身。E（同名工厂重定义）要的是「同一个 key 的**每个定义**都合格才算
        工厂」，但累积实现顺带把**中间状态**也钉死了 —— ``ast.walk`` 按定义顺序走，
        于是 ``def outer(): return inner()`` 写在 ``inner`` **之前**时，第一轮 outer
        会因「``inner`` 此刻还不在已知工厂集」被判不合格并**永久**失格。实测：
        outer 在前 ⇒ 1 violation（误拒），inner 在前 ⇒ 0。同一段代码换个顺序两种结论。

        ⛔ **第一版修法（只把失格集每轮清空）是错的，且比不修更糟** —— round-1
        Codex HIGH-1 用纯 AST 在内存里交叉复现，父版 1 violation → 那一版 **0**：

            def outer():        # ①
                return make()
            def make():         # ② 安全版
                a = FastAPI()
                return a
            def make():         # ③ 不安全版 —— Python 运行时用的是这个
                return real_app

        因为 :attr:`fastapi_returning_funcs` 当时仍是 **add-only 累积**，两个集合的
        生命周期不一致，于是出现**暂态资格传播**：第二遍 walk 里 ① 读到了第一遍刚
        加进去、**本轮差集还没执行**的 ``make`` 资格，抢先拿到安全身份；随后差集只
        剔掉 ``make``，``outer`` 幸存 —— 而它调用的 ``make()`` 返回的是生产 app。
        把内外循环上限加到 20/40 仍然漏检：这不是迭代次数不够，是**发布时机**错了。

        **现在的口径**（三条一起才成立，少一条就退回上面某个缺陷）：

        1. **冻结知识**：本轮所有判定只读 ``frozen`` —— 上一轮**结束时**的可信集。
           扫描过程中产生的新资格一律不参与本轮求值，暂态传播无从发生。
        2. **按 key 聚合**：同名多定义的裁定用 ``and`` 合并（``verdicts[key]``），
           「存在一条安全的不算数，必须条条都是」这句哲学直接落在数据结构上。
        3. **整组通过才发布**：两个集合在轮末**一起**重建 —— 可信集不再是 add-only，
           失格集也不再累积，它们是同一次裁定的两半。

        这样：E（②③ 同名）在任何知识水平下整组都不合格，永不进集；前向引用
        （outer→inner，无重定义）在知识补齐后的下一轮自然通过；HIGH-1 那个组合
        （①+②③）里 ``outer`` 每一轮读到的 ``frozen`` 都不含 ``make``，因此也永不进集。
        三条反例/正例都在 ``_AST_MUST_FLAG`` / ``_AST_MUST_PASS`` 里常设钉住。
        """
        for _ in range(2):
            # (1) 冻结：本轮求值只看上一轮结束时的知识。`_is_local_app_factory_call`
            #     读的是 self.fastapi_returning_funcs，所以直接把它按住不动，
            #     裁定写进独立的 verdicts，轮末才发布。
            frozen = set(self.fastapi_returning_funcs)
            self.fastapi_returning_funcs = frozen
            self._factory_verdicts = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._mark_fastapi_returning(node)
            # (3) 发布：两个集合一起重建。先全放进可信集，再减掉失格的那些 ——
            #     ⛔ 下面这个差集**承重**：注释掉它，E 的两条反例当场 MISSED
            #     ⇒ AST-NEGATIVE-CONTROL: FAIL（LOW#18 的常设门）。
            verdicts = self._factory_verdicts
            self.fastapi_returning_funcs = set(verdicts)
            self.disqualified_factory_keys = {k for k, ok in verdicts.items() if not ok}
            self.fastapi_returning_funcs -= self.disqualified_factory_keys

    def _mark_fastapi_returning(self, fd) -> None:
        """判定「本函数的**每一条**可达 return 都返回可证的局部 app」。

        R1 Codex HIGH-10 打回的旧判据是「**存在**一条 return 返回局部 app」，于是

            a = FastAPI()
            a = production_app
            return a

        被标成安全，调用方裸启生产 lifespan。现在改成：

        * 每一条 return 都在**它自己的位置**上按 :meth:`resolve_name` 解析
          （「全部先前绑定必须一致」的口径，见该方法），必须解析为 ``O_LOCAL_APP``；
        * 函数里**必须至少有一条** return（没有 return 的函数不算工厂）；
        * 任何一条不合格 ⇒ 整个函数不算工厂。
        """
        own = self.scope_of.get(id(fd.body[0])) if fd.body else None
        if own is None:
            return
        # 只看**本函数自己作用域**里的语句：嵌套函数的 return 归它自己，
        # 不能算到外层函数头上（否则 `def outer(): def inner(): return FastAPI()`
        # 会把 outer 误标成返回局部 app）。
        own_stmts = [s for s in ast.walk(fd) if self.scope_of.get(id(s)) is own]
        returns = [s for s in own_stmts if isinstance(s, ast.Return) and s.value is not None]
        if not returns:
            return
        key = self._factory_key(fd)
        ok = True
        for stmt in returns:
            candidates = stmt.value.elts if isinstance(stmt.value, ast.Tuple) else [stmt.value]
            if not any(self._value_origin(c, stmt, own) == O_LOCAL_APP for c in candidates):
                # 这条 return 拿不出可证的局部 app ⇒ 这个**定义**不算工厂。
                ok = False
                break
        # ⛔ 裁定写进 verdicts、**按 key 用 and 聚合**，不直接改两个对外集合：
        #    同一个 key 可能有多个定义（`def make()` 写两遍），而 Python 运行时用的是
        #    **后**定义的那个。「存在一条安全的不算数，必须条条都是」这句哲学就落在
        #    这个 `and` 上（阻断项 E，2026-09-04 round-2 抢救出，复现见 X4 验收单 §7.6f）。
        #    发布时机与冻结知识见 :meth:`_mark_all_fastapi_returning` 的 docstring ——
        #    直接 add/discard 会让本轮新资格被同轮的别的定义读到（round-1 Codex HIGH-1）。
        self._factory_verdicts[key] = self._factory_verdicts.get(key, True) and ok

    def _mark_main_client_sources(self, tree: ast.Module) -> None:
        """收敛两类「会把 app.main 的 TestClient 实例递出来」的源。

        * ``main_client_funcs``：函数的**每一条** return 都解析为 main 实例
          （与 FastAPI 工厂同口径：存在一条安全的不算数，必须条条都是）；
        * ``main_client_attrs``：``self.<attr> = TestClient(<app.main 的 app>)``。

        ⚠️ **不覆盖容器，也不覆盖解包**（2026-09-04 补准确）：

        * ``clients = [TestClient(app)]`` 之后 ``with clients[0]:`` —— 索引访问；
        * ``def make(): return FastAPI(), TestClient(app.main.app)`` 之后
          ``_, c = make(); with c:`` —— **tuple 解包**。这一条是 round-2 抢救出的
          阻断项 D，本 session 实测确认漏检（0 违规）。它与索引访问同族：都要做
          **容器/序列元素级别的别名分析**才追得动，不是判据写松了。
          注意工厂登记那一步对 tuple 用的是 ``any(... == O_LOCAL_APP ...)``，
          即「tuple 里**存在**一个可证局部 app 就登记」—— 那是为了识别
          ``app, n = make()` 这类正例（见本类 ``fastapi_returning_funcs`` 的注释），
          单独把它改成 ``all`` 会误伤正例，而**并不能**堵住 D：D 的漏检发生在
          调用方解包那一步，不在登记这一步。

        ⚠️ 上面第二条（tuple 解包漏检，阻断项 D）自 CARD-W4-5 (d) 起**不再是盲区**：
        :attr:`factory_return_elts` 把返回 tuple 的工厂逐位登记，调用方解包时按位配对，
        ``_, c = make()`` 里的 ``c`` 于是拿得到 :class:`_InstanceMain`。索引访问
        （``clients[0]``）仍是盲区——那要的是容器元素级别名分析，本卡不做。

        两者都如实登记为已知盲区，见模块 docstring「这道负门不比什么」。
        """
        # ⛔ 逐位表**每轮重建 + 冻结上一轮知识**（M16 的完整教训，见
        #    :meth:`_mark_all_fastapi_returning`）。两条的证据强度**不一样**，
        #    如实分开写：
        #
        #    * **冻结求值 —— 承重，有门。** 转调工厂（`def outer(): return inner()`）
        #      要读被调者的表，而 `ast.walk` 按**定义顺序**走。只清空不冻结的话，
        #      `outer` 写在 `inner` 前面时每一轮都读到刚被清空的表 ⇒ 永远补不齐 ⇒
        #      「同一段代码换个定义顺序两种结论」（M16 原始缺陷的形态）。
        #      变异实测：把 `frozen_return_elts` 改成恒空，验伪锚 d2/d3 当场翻红。
        #    * **每轮重建 —— 防御性纪律，本卡没造出能看见它的输入。** 2026-09-06
        #      变异实测：删掉下面那行清空（退回 add-only 累积），40 条反例与 23 条
        #      正例**全部不变**。查因是 dict 赋值本身就覆盖，而「某 key 在轮 N 登记、
        #      轮 N+1 不登记」需要 `frozen` 里的条目消失，add-only 下它不会消失。
        #      保留这行是因为 M16 的教训值 —— 但**不要**把它写成「已被门守住」。
        frozen_return_elts = dict(self.factory_return_elts)
        self.factory_return_elts = {}
        self.partial_main_client_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                own = self.scope_of.get(id(node.body[0])) if node.body else None
                if own is None:
                    continue
                own_stmts = [s for s in ast.walk(node) if self.scope_of.get(id(s)) is own]
                returns = [s for s in own_stmts if isinstance(s, ast.Return) and s.value is not None]
                # `r.value is not None` 由上一行的 returns 构造保证，这里重述一遍是给
                # 类型检查器看的（narrowing）——本卡改动行不许留新的 pyright 报错。
                main_rets = [
                    r for r in returns if r.value is not None and _is_instance_main(self._value_origin(r.value, r, own))
                ]
                if returns and len(main_rets) == len(returns):
                    self.main_client_funcs.add(self._factory_key(node))
                elif main_rets:
                    # 「**有些** return 是 main 实例」——all 口径判不出来，但
                    # `with make(flag):` 只要走到那一支就跑真实 lifespan。
                    # (c)-C2 据此把这类调用从「调用面盲区」里拉回来 fail-closed。
                    self.partial_main_client_funcs.add(self._factory_key(node))
                self._mark_factory_return_elts(node, returns, own, frozen_return_elts)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and getattr(node, "value", None) is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                attrs = [
                    tgt
                    for tgt in targets
                    if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self"
                ]
                if not attrs:
                    continue
                scope = self.scope_for(node)
                if _is_instance_main(self._value_origin(node.value, node, scope)):
                    owner = self._enclosing_class_name(node)
                    for tgt in attrs:
                        self.main_client_attrs.add(f"{owner}.{tgt.attr}")

    def _mark_factory_return_elts(self, fd, returns, own: _Scope, frozen: dict) -> None:
        """登记「返回 tuple 的工厂」的**逐位来源**，供调用方解包时按位配对。

        登记条件（全部满足才登记，任何一条不满足就不给这个 key 建表 ⇒ 调用方按
        unknown 处理，fail-closed）：

        * 至少一条 return，且**每一条** return 要么是字面 tuple、要么是一次能在
          ``frozen`` 里查到逐位表的**本模块工厂调用**（转调，见下）；
        * 所有 return 的宽度相同，且字面 tuple 里都不带 ``*``（星号宽度静态不定）；
        * 同一位置在所有 return 上**同源**，否则该位置单独记 unknown。

        与 :attr:`main_client_funcs` 的 all 口径同族：「存在一条是这样的」不算数。

        **转调这一支是回归修复**（本卡自查发现）：``def outer(): return inner()``
        而 ``inner`` 返回 tuple 时，只认字面 tuple 会让 ``app, n = outer()`` 拿不到
        逐位表 ⇒ 每元素 unknown ⇒ ``TestClient(app)`` 被误判违规。改前那份代码因为
        「整体来源原样传给每个元素」反而放行，所以这是 (d) 引入的**新误报**，
        `_AST_MUST_PASS` 原有的转调正例（验伪锚 12/13）用的是单值 return、不解包，
        看不见它。现补两条正例（验伪锚 d2/d3）把两个定义顺序都钉住。

        ``frozen`` 是**上一轮结束时**的表，不是本轮正在填的那张 —— 理由见
        :meth:`_mark_main_client_sources` 开头的注释（同轮顺序依赖 = M16 原始缺陷）。
        """
        key = self._factory_key(fd)
        if not returns:
            return
        rows: list[tuple] = []
        for r in returns:
            if isinstance(r.value, ast.Tuple):
                if any(isinstance(e, ast.Starred) for e in r.value.elts):
                    return
                rows.append(tuple(self._value_origin(e, r, own) for e in r.value.elts))
            elif isinstance(r.value, ast.Call):
                callee = self._callee_factory_key(r.value.func, r, own)
                cols = frozen.get(callee) if callee is not None else None
                if cols is None:
                    return
                rows.append(tuple(cols))
            else:
                return
        if len({len(row) for row in rows}) != 1:
            return
        self.factory_return_elts[key] = tuple(col[0] if len(set(col)) == 1 else O_UNKNOWN for col in zip(*rows))

    def _mark_isolation_wrappers(self, tree: ast.Module) -> None:
        """识别**自建的隔离包装器**，避免把合法写法误判成违规。

        ``@contextlib.contextmanager`` 包一层 ``no_lifespan`` 是很自然的写法::

            @contextlib.contextmanager
            def isolated(a):
                with no_lifespan(a):
                    yield a

            with isolated(app), TestClient(app) as c: ...

        这段是**安全**的，但按「helper 必须直接 import 自 tests.support.lifespan」
        的口径会被判违规（实测确认，属 R1 Codex 归类的「误判为违规 = MEDIUM」）。

        识别条件收得很窄，三条**全部**满足才算：

        1. 函数体里有一个 ``with``，其某个 item 解析为 :data:`O_HELPER`
           （真的是 import 来的 ``no_lifespan``/``lifespan_lite``）；
        2. 该 helper 调用的实参是本函数**自己的某个位置形参**；
        3. 那个 ``with`` 的**体内**有 ``yield`` —— 即隔离确实覆盖了让出控制权的
           那一刻。只在 with 外面 yield 的包装器不算数（隔离没盖住调用方的代码）。

        CARD-W4-5 (f) 再加两条（X4 HIGH，仍是「全部满足才算」）：

        4. **被隔离的形参在体内没有被重绑定**。有重绑定就失格：``no_lifespan(a)``
           盖住的是**执行到那一行时** ``a`` 指着的那个对象，之后 ``a = production_app``
           不会让隔离跟过去；而调用点比对的是**形参下标**，它对重绑定一无所知，
           于是 ``with wrapper(app), TestClient(app)`` 被判安全，实际裸启生产 app。
        5. **yield 出去的就是被隔离的那个对象**。旧判据只问「with 体内有没有
           yield」，于是::

               with no_lifespan(a):
                   yield other_app        # 隔离盖的是 a，递出去的是别人

           照样拿到资格 —— 调用方以为 wrapper(app) 隔离了 app，其实拿到的是另一个。

        记下被隔离的**形参下标**，调用点按同一下标的实参名比对；换个参数传就不算。

        ⛔ **每轮重建 + 按 key 聚合**（CARD-W4-5 (f)-⑥，本卡实测发现）：卡文说本条
        「在『同名多定义任一不合格 ⇒ 整 key 失格』之外补两条」，暗示包装器侧已有那个
        口径 —— **实测它此前不存在**。旧实现直接 ``self.isolation_wrappers[key] = idx``，
        是 add-only 覆盖，于是::

            @contextlib.contextmanager
            def isolated(a):
                with no_lifespan(a):
                    yield a          # 合格 → 写进表
            @contextlib.contextmanager
            def isolated(a):
                yield a              # 不合格 → 只是「不写」，删不掉上面那条
            with isolated(app), TestClient(app): ...   # 判安全，而运行时用的是第二个

        与 :meth:`_mark_all_fastapi_returning` 的阻断项 E 完全同形（那边有
        ``_factory_verdicts`` 聚合，这边没有）。现在：本轮所有定义先各自裁定，
        同一 key 上**任一定义不合格、或两个定义的下标不一致 ⇒ 整 key 失格**，
        轮末整体发布；集合每轮重建，不再累积（M16 同款纪律）。
        """
        verdicts: dict[str, int | None] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            key = self._factory_key(node)
            idx = self._isolation_wrapper_index(node)
            if key in verdicts and verdicts[key] != idx:
                verdicts[key] = None  # 同名多定义裁定不一致 ⇒ 整 key 失格
            else:
                verdicts[key] = idx
        self.isolation_wrappers = {k: v for k, v in verdicts.items() if v is not None}

    def _isolation_wrapper_index(self, node) -> int | None:
        """单个 ``def`` 的隔离包装器资格：合格则返回被隔离的形参下标，否则 ``None``。

        五条**全部**满足才合格，见 :meth:`_mark_isolation_wrappers` 的 docstring。
        """
        own = self.scope_of.get(id(node.body[0])) if node.body else None
        if own is None:
            return None
        params = [a.arg for a in (node.args.posonlyargs + node.args.args)]
        if not params:
            return None
        for stmt in ast.walk(node):
            if not isinstance(stmt, (ast.With, ast.AsyncWith)):
                continue
            if self.scope_of.get(id(stmt)) is not own:
                continue
            yields = [y for b in stmt.body for y in ast.walk(b) if isinstance(y, (ast.Yield, ast.YieldFrom))]
            if not yields:
                continue
            for item in stmt.items:
                ctx = item.context_expr
                if not isinstance(ctx, ast.Call):
                    continue
                if self._callable_origin(ctx.func, stmt, own) != O_HELPER:
                    continue
                if not (ctx.args and isinstance(ctx.args[0], ast.Name) and ctx.args[0].id in params):
                    continue
                isolated_param = ctx.args[0].id
                # (f)-④ 形参被重绑定 ⇒ 失格。形参自己那条绑定的位置是 (0, 0)
                # （见 `_walk_stmt` 建函数作用域那一段），别的位置就是重绑定。
                if any(pos != (0, 0) for pos, _ in own.sorted_bindings(isolated_param)):
                    continue
                # (f)-⑤ 每一条 yield 递出去的都必须**就是**被隔离的那个名字。
                # `yield from` 递的是一个可迭代对象、不是被隔离的那一个，一律失格。
                if not all(isinstance(y, ast.Yield) and _ref_path(y.value) == isolated_param for y in yields):
                    continue
                return params.index(isolated_param)
        return None

    def isolation_wrapper_param(self, func: ast.expr, node: ast.AST, scope: _Scope) -> int | None:
        """这次调用是不是自建隔离包装器；是则返回被隔离的形参下标。"""
        if isinstance(func, ast.Name):
            key = f"<module>.{func.id}"
            if key not in self.isolation_wrappers:
                return None
            if self.resolve_name(func.id, _pos(node), scope) != f"{O_LOCAL_FUNC_PREFIX}{func.id}":
                return None
            return self.isolation_wrappers[key]
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in ("self", "cls"):
            return self.isolation_wrappers.get(f"{self._enclosing_class_name(node)}.{func.attr}")
        return None

    def _is_main_client_factory_call(self, func: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """调用形态与 :meth:`_is_local_app_factory_call` 同口径，只是查另一张表。"""
        if isinstance(func, ast.Name):
            if f"<module>.{func.id}" not in self.main_client_funcs:
                return False
            return self.resolve_name(func.id, _pos(node), scope) == f"{O_LOCAL_FUNC_PREFIX}{func.id}"
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id not in ("self", "cls"):
                return False
            return f"{self._enclosing_class_name(node)}.{func.attr}" in self.main_client_funcs
        return False

    def is_main_client_attr(self, expr: ast.expr, node: ast.AST) -> bool:
        """``self.<attr>`` 是否是本类里存下来的 app.main TestClient 实例。"""
        if not (isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name)):
            return False
        if expr.value.id not in ("self", "cls"):
            return False
        return f"{self._enclosing_class_name(node)}.{expr.attr}" in self.main_client_attrs

    def _factory_key(self, fd) -> str:
        """工厂身份 = 「(类名或 <module>) . 方法名」。

        R1 Codex HIGH-11：旧实现只按**方法名**记，于是 A 类的 ``make`` 返回局部 app
        会让 B 类同名、返回生产 app 的 ``make`` 也被判安全。按类限定之后，
        ``self.make()`` 只能命中**它自己那个类**里的定义。
        """
        enclosing = self.scope_of.get(id(fd))
        while enclosing is not None and enclosing.kind != "class":
            enclosing = enclosing.parent
        owner = getattr(enclosing.node, "name", "<anon>") if enclosing is not None else "<module>"
        return f"{owner}.{fd.name}"

    def _enclosing_class_name(self, node: ast.AST) -> str:
        scope = self.scope_of.get(id(node))
        while scope is not None and scope.kind != "class":
            scope = scope.parent
        return getattr(scope.node, "name", "<anon>") if scope is not None else "<module>"

    # ── TestClient 识别 ─────────────────────────────────────────────────
    def is_testclient_call(self, call: ast.expr, node: ast.AST, scope: _Scope) -> bool:
        """这次调用是不是在构造 TestClient。

        两条路，取并集（检测面要宽，判定面才敢严）：
          * **词法**叫 ``TestClient``（哪怕被本地遮蔽——那种情况另有一条违规）；
          * **解析**到真正 import 自 fastapi/starlette 的 TestClient 类
            （覆盖 ``as TC`` 别名与 ``fastapi.testclient.TestClient`` 全链）。
        """
        if not isinstance(call, ast.Call):
            return False
        return _syntactic_call_name(call) == "TestClient" or self._callable_origin(call.func, node, scope) == (
            O_TESTCLIENT_CLASS
        )

    @staticmethod
    def testclient_app_arg(call: ast.Call) -> ast.expr | None:
        """取 TestClient(...) 的 app 实参：第一个位置参数，或 ``app=`` 关键字。

        R1 Codex MEDIUM-13：只看位置参数会漏掉 ``TestClient(app=app)``。
        """
        if call.args:
            return call.args[0]
        for kw in call.keywords:
            if kw.arg == "app":
                return kw.value
        return None

    # ── 解析 ────────────────────────────────────────────────────────────
    def scope_for(self, node: ast.AST) -> _Scope:
        """节点所属作用域。

        ``scope_of`` 只对**语句**建了索引，所以表达式节点（比如
        ``stack.enter_context(client)`` 这个 Call）要沿父链往上找到它所在的语句。
        直接 fallback 到 module_scope 会让函数内的局部名字整片解析不出来。
        """
        cur: ast.AST | None = node
        while cur is not None:
            scope = self.scope_of.get(id(cur))
            if scope is not None:
                return scope
            cur = self.parents.get(id(cur))
        return self.module_scope

    def parent_of(self, node: ast.AST) -> ast.AST | None:
        return self.parents.get(id(node))

    def resolve_name(self, name: str, pos: tuple[int, int], scope: _Scope) -> Origin:
        """在 ``scope`` 处、位置 ``pos`` 上，名字 ``name`` 的来源。

        判据（R1 Codex HIGH-9 整改后）：**所有**位于 ``pos`` 之前的绑定必须来源
        一致，才给出那个来源；有任何分歧一律 unknown（= 违规，fail-closed）。

        为什么不能只取「最后一次绑定」：那是**词法**上的最后一次，不是**控制流**
        上的。Codex 的反例——

            app = production_app
            if use_local:
                app = FastAPI()
            with TestClient(app): ...

        ——「最后一次绑定」是 ``FastAPI()``，于是判安全；而 ``use_local`` 为假时
        跑的是生产 app 的真实 lifespan。做完整的 reaching-definition 需要 CFG；
        这里用「全部先前绑定必须一致」这个**更保守**的近似：它对上面这种分支写法
        必然判 unknown，代价是「先赋 A 后无条件覆盖成 B」的写法也会被判 unknown
        （本仓库 371 个文件实测 0 例，见 AST 门输出）。

        * **本作用域**：只看 ``pos`` 之前的绑定；一个都没有 ⇒ unknown。
        * **外层作用域**：函数调用时刻不确定，要求该名字在外层的**全部**绑定一致。
        * 类作用域对内层函数不可见（Python 语义），查找链跳过它。
        """
        cur: _Scope | None = scope
        first = True
        while cur is not None:
            skip = (not first) and cur.kind == "class"
            if not skip and name in cur.bindings:
                bindings = cur.sorted_bindings(name)
                if first:
                    origins = {o for p, o in bindings if p < pos}
                    if not origins:
                        return O_UNKNOWN
                else:
                    origins = {o for _, o in bindings}
                return origins.pop() if len(origins) == 1 else O_UNKNOWN
            cur = cur.parent
            first = False
        return O_UNKNOWN

    def resolve_arg(self, arg: ast.expr, node: ast.AST, scope: _Scope) -> Origin:
        if isinstance(arg, ast.Name):
            return self.resolve_name(arg.id, _pos(node), scope)
        if isinstance(arg, ast.Attribute):
            return self._attribute_origin(arg, node, scope)
        if isinstance(arg, ast.Call):
            return self._value_origin(arg, node if isinstance(node, ast.stmt) else arg, scope)
        return O_UNKNOWN


def _enter_context_arg(call: ast.Call) -> ast.expr | None:
    """取 ``enter_context(...)`` 的上下文管理器实参（CARD-W4-5 (a)，X4 HIGH）。

    位置参优先 → ``cm=`` → 第一个具名关键字。旧实现只看 ``call.args``，于是
    ``stack.enter_context(cm=TestClient(app))`` —— 一个 CPython 签名原样接受、
    会跑真实 lifespan 的写法 —— 在 ``if not node.args: continue`` 那行直接畅通。

    「第一个具名关键字」这条兜底不是猜：``ExitStack.enter_context(self, cm)`` 与
    ``AsyncExitStack.enter_async_context(self, cm)`` 各自只有一个非 self 形参，
    任何具名关键字要么就是它，要么这次调用本来就 TypeError。
    ``**kwargs`` 展开（``kw.arg is None``）取不到名字 ⇒ ``None`` ⇒ 调用方判违规。
    """
    if call.args:
        return call.args[0]
    for kw in call.keywords:
        if kw.arg == _ENTER_CONTEXT_CM_PARAM:
            return kw.value
    for kw in call.keywords:
        if kw.arg is not None:
            return kw.value
    return None


def _syntactic_call_name(node: ast.expr) -> str | None:
    """Call(...) 的**词法**函数名：``f()`` → f；``m.f()`` → f。"""
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _item_isolates(index: "_ModuleIndex", ctx, host_node, scope, app_ref: str) -> bool:
    """一个 ``with`` item 是否对引用路径为 ``app_ref`` 的 app 施加了隔离。

    两条路：直接调 import 来的 ``no_lifespan``/``lifespan_lite``；
    或调本模块**自建的隔离包装器**（窄定义见 `_mark_isolation_wrappers`），
    此时比对的是**被隔离的那个形参下标**上的实参。

    比对用 :func:`_ref_path`（CARD-W4-5 (e)）：``m.app`` 这类属性链在两侧写法相同
    时才算同一个 app；取不到路径（``f().app``）一律不算覆盖。
    """
    if not isinstance(ctx, ast.Call):
        return False
    if index._callable_origin(ctx.func, host_node, scope) == O_HELPER:
        return bool(ctx.args) and _ref_path(ctx.args[0]) == app_ref
    idx = index.isolation_wrapper_param(ctx.func, host_node, scope)
    if idx is None or idx >= len(ctx.args):
        return False
    return _ref_path(ctx.args[idx]) == app_ref


def _isolation_sibling_covers(index: "_ModuleIndex", with_node, upto_pos: int, app_arg, scope) -> bool:
    """同一个 ``with`` 语句里，位置**在前**的兄弟项是否对同一个 app 做了隔离。"""
    app_ref = _ref_path(app_arg)
    if app_ref is None:
        return False
    for hpos, hitem in enumerate(with_node.items):
        if hpos >= upto_pos:
            break
        if _item_isolates(index, hitem.context_expr, with_node, scope, app_ref):
            return True
    return False


def _isolation_enclosing_covers_name(index: "_ModuleIndex", node, app_ref: str) -> bool:
    """按**引用路径**找支配本节点的外层 ``with no_lifespan(<app_ref>):``。"""
    cur = index.parent_of(node)
    while cur is not None:
        if isinstance(cur, (ast.With, ast.AsyncWith)):
            scope = index.scope_for(cur)
            for hitem in cur.items:
                if _item_isolates(index, hitem.context_expr, cur, scope, app_ref):
                    return True
        cur = index.parent_of(cur)
    return False


def _isolation_enclosing_covers(index: "_ModuleIndex", node, app_arg) -> bool:
    """**外层**的 ``with no_lifespan(app):`` 是否支配本节点（R1 Codex MEDIUM-13）。

    外层隔离块内的一切都在 no-op lifespan 生效期间执行，真实 startup 不会跑，
    所以那是安全写法，旧实现却报违规。这里沿父链往上找 With，逐个看它是不是对
    **同一个名字**做了隔离。
    """
    app_ref = _ref_path(app_arg)
    if app_ref is None:
        return False
    return _isolation_enclosing_covers_name(index, node, app_ref)


def _describe(expr) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        # 整条链写得出来就写整条（`m.app`），写不出来才退回旧的省略形态
        return _ref_path(expr) or f"<...>.{expr.attr}"
    if isinstance(expr, ast.Call):
        syn = _syntactic_call_name(expr)
        return f"{syn}(...)" if syn else "<expr>(...)"
    if isinstance(expr, ast.NamedExpr):
        return f"({expr.target.id} := ...)"
    return "<expr>"


def _unprovable_context_exempt(index, node, scope, expr, how: str) -> str | None:
    """不可证的 ``__enter__`` 目标里，哪些**可证**不必 fail-closed（CARD-W4-5 (c)）。

    这不是「其余情况放行」的另一种写法 —— 四条各自都是可证命题，各自都配了
    ``_AST_MUST_PASS`` 正例与 ``_AST_MUST_FLAG`` 反例；命中任何一条要说得出理由。
    一刀切 fail-closed 的实测代价见每条注释里的数字（2026-09-06 于 385 个文件）。
    """
    # ── C1 异步上下文协议 ──────────────────────────────────────────────
    # Starlette 的 TestClient 继承 httpx.Client，只实现 __enter__/__exit__，
    # **没有** __aenter__。送进 `async with` / `enter_async_context` 的对象因此
    # 可证不是 TestClient —— 真送了会 AttributeError，根本跑不到 lifespan。
    if how == "enter_async_context" or isinstance(node, ast.AsyncWith):
        return "C1:async-context-protocol"
    # ── C2 调用面归属 ────────────────────────────────────────────────
    # `with f():` 的返回值是不是 TestClient，属**跨函数传递**——模块 docstring
    # 已把它声明为已知盲区。把这个面一并 fail-closed 实测会让 385 个文件里的
    # 194 个变红（1431 条），全部是 pytest.raises / open / patch 这类，与本门
    # 要防的东西无关；那是把「TestClient lifespan 门」改成「全部 with 可证性门」，
    # 不是本卡范围。⛔ 但盲区不等于放行：调用的若是本模块工厂、且它**存在**一条
    # 返回 main 实例的 return（只是没满足 main_client_funcs 的 all 口径），
    # 仍然 fail-closed —— 本模块内可证的部分一条都不放。
    if isinstance(expr, ast.Call):
        if index.factory_returns_any_main(expr.func, node, scope):
            return None
        return "C2:call-surface-cross-function"
    # ── C3 模块内无 TestClient 可达性 ─────────────────────────────────
    # 本模块 AST 里连 TestClient 这个名字都没有 ⇒ 它构造不出 TestClient 实例。
    # 判据必须是 AST 级：`tests/support/live_port_guard.py` 的 "TestClient" 只在
    # docstring 里（:34/:54），文本 grep 会把这个零 TestClient 的文件判成有可达性。
    if not index.module_has_testclient:
        return "C3:no-testclient-in-module"
    # ── C4 import 来的模块的属性 ─────────────────────────────────────
    # `mod._refresh_guard` 这类对象不由本模块构造（同 C2 的跨模块盲区），
    # 区别是「它是个模块」这件事由 import 语句语义直接可证。
    if isinstance(expr, ast.Attribute) and index.attribute_base_is_module(expr, node, scope):
        return "C4:imported-module-attribute"
    return None


def _flag_instance_context(violations, index, rel, node, scope, expr, how: str) -> None:
    """判定「把一个对象送进 ``__enter__``」是否合规 —— 三分（CARD-W4-5 (c)）。

    覆盖 ``with client:``、``with self.client:``、``enter_context(client)``、
    以及 (b) 展开出来的 IfExp 分支。三分是：

    * **可证是 app.main 的 TestClient 实例** ⇒ 违规（除非有支配的隔离块）；
    * **可证不是** ⇒ 放行（局部实例 / FastAPI 类 / 模块对象 / helper …）；
    * **不可证** ⇒ 违规并标注 fail-closed 理由，除非命中
      :func:`_unprovable_context_exempt` 里逐条列举的可证窄化。

    ⛔ 第三分是本卡新增的。旧实现是 ``if origin is None or not _is_instance_main:
    return`` —— 一个静默放行分支，于是 ``with (client if c else client):``
    （IfExp 解析不出 origin）、``enter_context(client := TestClient(app))``
    （海象不入绑定表）这类**今天就能写出来、会跑真实 lifespan** 的源码全部畅通。

    关键修正（round-2 自查）：外层隔离要比对的是**这个实例包着的那个 app 的引用
    路径**，不是客户端变量名 —— 之前拿 ``client`` 去找 ``no_lifespan(client)``，
    于是合法的 `with no_lifespan(app): with client:` 被误报。
    """
    if isinstance(expr, ast.NamedExpr):
        # `enter_context(client := TestClient(app))` —— 送进 __enter__ 的是海象的
        # **值**；名字绑定另由 `_ModuleIndex._record_walrus` 记表。旧实现两边都没有：
        # NamedExpr 既不是 Call 也不是 Name ⇒ origin 恒 None ⇒ 静默放行。
        _flag_instance_context(violations, index, rel, node, scope, expr.value, how)
        return
    origin = None
    desc = _describe(expr)
    if isinstance(expr, ast.Name):
        origin = index.resolve_name(expr.id, _pos(node), scope)
    elif isinstance(expr, ast.Attribute):
        origin = (
            _instance_main(None)
            if index.is_main_client_attr(expr, node)
            else index._attribute_origin(expr, node, scope)
        )
    elif isinstance(expr, ast.Call):
        if index._is_main_client_factory_call(expr.func, node, scope):
            # `with make():` —— 工厂的每一条 return 都是 app.main 实例（L2-d）
            origin = _instance_main(None)
            desc = f"{_describe(expr.func)}()"
        else:
            origin = index._value_origin(expr, node if isinstance(node, ast.stmt) else expr, scope)
    if _is_instance_main(origin):
        app_ref = _instance_app_name(origin)
        if app_ref is not None and _isolation_enclosing_covers_name(index, node, app_ref):
            return
        hint = f"（它包的是 {app_ref}）" if app_ref else "（包的 app 名静态不可知，fail-closed）"
        violations.append(
            f"{rel}:{node.lineno}: {how} {desc} —— 它是用 app.main 的 app 构造的 TestClient 实例，"
            f"进入上下文会跑真实 lifespan{hint}；构造点没有隔离，本处也没有支配的外层隔离块"
        )
        return
    if origin is not None and origin != O_UNKNOWN:
        return  # 可证不是 main 实例
    exempt = _unprovable_context_exempt(index, node, scope, expr, how)
    if exempt is not None:
        return
    violations.append(
        f"{rel}:{node.lineno}: {how} {desc} —— 送进上下文的对象来源静态不可证"
        f"（解析结果={origin}），无法证明它不是用 app.main 的 app 构造的 TestClient 实例；"
        "按违规处理（fail-closed）。合法写法：把它换成能追溯来源的局部名字，"
        "或用 no_lifespan/lifespan_lite 包住构造点"
    )


def analyze_source(source: str, rel: str) -> list[str]:
    """对一份源码跑 AST 门，返回违规明细（空 = 合规）。

    三类被检面（R1 Codex HIGH-8 之后）：

    1. ``with TestClient(<app>) ...`` —— 直接进 with 的构造；
    2. ``client = TestClient(<app>)`` 之后 ``with client:`` —— 实例被追踪进 with；
    3. ``stack.enter_context(TestClient(<app>))`` / ``enter_context(client)``
       —— ExitStack 同样会触发 ``__enter__``。

    ⚠️ **不带 with 的裸 ``TestClient(app)`` 不算违规**：Starlette 只在
    ``__enter__`` 里跑 lifespan，构造本身没有启动副作用（本仓库 7 个文件用这种
    写法，全部无害）。
    """
    violations: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}: SyntaxError {e}"]
    index = _ModuleIndex(tree)

    def flag_client_construction(call, node, scope, pos_in_with=None, with_node=None, how=""):
        """判定一次「会触发 lifespan 的 TestClient 构造」是否合规。"""
        app_arg = index.testclient_app_arg(call)
        if app_arg is None:
            violations.append(f"{rel}:{node.lineno}: TestClient() 取不到 app 实参 —— 人工复核{how}")
            return
        origin = index.resolve_arg(app_arg, node, scope)
        if origin == O_LOCAL_APP:
            return
        desc = _describe(app_arg)
        if origin != O_MAIN_APP:
            violations.append(
                f"{rel}:{node.lineno}: TestClient({desc}) —— app 来源无法静态证明"
                f"（解析结果={origin}，按违规处理，人工复核）{how}"
            )
            return
        covered = with_node is not None and _isolation_sibling_covers(index, with_node, pos_in_with, app_arg, scope)
        if not covered:
            covered = _isolation_enclosing_covers(index, node, app_arg)
        if not covered:
            violations.append(
                f"{rel}:{node.lineno}: TestClient({desc}) —— app 来自 app.main 且没有"
                "生效中的 no_lifespan/lifespan_lite（同 with 语句里排在前面的兄弟项，"
                f"或支配本处的外层 with 块）{how}"
            )

    def check_with_ctx(ctx, node, scope, pos_i, depth=0):
        """判定一个 ``with`` item 的 ``context_expr``。

        条件表达式两支**各判一次**（CARD-W4-5 (b)）：``with (a if c else b):`` 里
        运行时走哪一支静态不可知，任一支违规就是违规。旧实现只分「是不是 Call」，
        IfExp 落进 else 支后在 `_flag_instance_context` 里解析不出 origin ⇒ 静默
        放行，于是 ``with (client if c else client):`` 这种直白写法都抓不到。
        """
        if isinstance(ctx, ast.IfExp):
            if depth >= _IFEXP_MAX_DEPTH:
                violations.append(
                    f"{rel}:{node.lineno}: with 的条件表达式嵌套超过 {_IFEXP_MAX_DEPTH} 层，"
                    "本门不再展开 —— 无法证明每一支都不会跑真实 lifespan，按违规处理（fail-closed）"
                )
                return
            check_with_ctx(ctx.body, node, scope, pos_i, depth + 1)
            check_with_ctx(ctx.orelse, node, scope, pos_i, depth + 1)
            return
        if isinstance(ctx, ast.Call):
            syn = _syntactic_call_name(ctx)
            callee_origin = index._callable_origin(ctx.func, node, scope)
            if syn == "TestClient" and callee_origin != O_TESTCLIENT_CLASS:
                violations.append(
                    f"{rel}:{node.lineno}: with TestClient(...) —— TestClient 这个名字"
                    f"解析不到 {sorted(TESTCLIENT_MODULES)} 的真实 import"
                    f"（当前来源={callee_origin}），无法证明它是被隔离约束覆盖的那个 TestClient"
                )
                return
            if index.is_testclient_call(ctx, node, scope):
                flag_client_construction(ctx, node, scope, pos_in_with=pos_i, with_node=node)
            else:
                # `with make():` —— 返回 app.main 实例的工厂调用（L2-d）
                _flag_instance_context(violations, index, rel, node, scope, ctx, "with")
            return
        # with client: / with self.client: / with (x := ...) —— 送一个已存在的对象
        _flag_instance_context(violations, index, rel, node, scope, ctx, "with")

    for node in ast.walk(tree):
        scope = index.scope_for(node)

        # ── 面 1/2：with 语句 ────────────────────────────────────────────
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for pos_i, item in enumerate(node.items):
                check_with_ctx(item.context_expr, node, scope, pos_i)
            continue

        # ── 面 3：ExitStack.enter_context(...) ──────────────────────────
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _ENTER_CONTEXT_ATTRS
        ):
            target = _enter_context_arg(node)
            if target is None:
                # 旧实现在这里 `continue` —— 于是 `stack.enter_context(cm=TestClient(app))`
                # 直接畅通（CARD-W4-5 (a)，X4 HIGH）。取不到 = 不可证，判违规。
                violations.append(
                    f"{rel}:{node.lineno}: {node.func.attr}(...) 取不到上下文管理器实参 ——"
                    "既没有位置参，也没有 cm= 或任何具名关键字（例如只有 **kwargs 展开），"
                    "无法证明送进去的不是 TestClient，按违规处理（fail-closed，人工复核）"
                )
                continue
            if isinstance(target, ast.Call) and index.is_testclient_call(target, node, scope):
                flag_client_construction(target, node, scope, how="（经 enter_context）")
            else:
                _flag_instance_context(violations, index, rel, node, scope, target, node.func.attr)
    return violations


def ast_scope_files() -> list[Path]:
    """射程内文件：``backend/tests`` 下除 integration / e2e 顶层目录外的全部 .py。"""
    root = BACKEND_DIR / AST_ROOT
    files: list[Path] = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in AST_EXCLUDED_TOP_DIRS:
            continue
        files.append(p)
    return files


def run_ast_gate() -> tuple[int, list[str], int]:
    """返回 (违规数, 违规明细, 扫描的文件数)。"""
    files = ast_scope_files()
    # 射程不能悄悄缩水成空集/极小集 —— 空集扫描必然 0 违规，是最典型的假绿。
    if len(files) < 200:
        return (
            1,
            [f"AST 射程只剩 {len(files)} 个文件（期望 ≥200）—— 射程缩水会让本门恒绿，判门损坏"],
            len(files),
        )

    violations: list[str] = []
    for path in files:
        rel = str(path.relative_to(BACKEND_DIR))
        violations.extend(analyze_source(path.read_text(encoding="utf-8"), rel))
    return len(violations), violations, len(files)


# ═══════════════════════════════════════════════════════════════════════════
# AST 门的负控（四类绕过必须被抓 + 验伪锚：正例必须不被抓）
# ═══════════════════════════════════════════════════════════════════════════

_AST_MUST_FLAG: list[tuple[str, str]] = [
    (
        "属性式 TestClient（import fastapi.testclient as tc）",
        "import fastapi.testclient as tc\n"
        "from app.main import app\n"
        "def t():\n"
        "    with tc.TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "局部重定义同名 no_lifespan（import provenance 必须失效）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "import contextlib\n"
        "@contextlib.contextmanager\n"
        "def no_lifespan(a):\n"
        "    yield a\n"
        "def t():\n"
        "    with no_lifespan(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "with 之后才 app = FastAPI()（语句顺序）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n"
        "    app = FastAPI()\n",
    ),
    (
        "class body 污染冒充局部 app",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class C:\n"
        "    app = FastAPI()\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "伪造本地 FastAPI() 工厂",
        "from fastapi.testclient import TestClient\n"
        "def FastAPI():\n"
        "    return object()\n"
        "app = FastAPI()\n"
        "def t():\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "helper 顺序在 TestClient 之后",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with TestClient(app), no_lifespan(app) as c:\n"
        "        pass\n",
    ),
    (
        "TestClient 名字被本地遮蔽（无法证明是真 TestClient）",
        "from fastapi import FastAPI\n"
        "def TestClient(a):\n"
        "    return a\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "import app.main as m; m.app 裸用",
        "import app.main as m\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(m.app) as c:\n"
        "        pass\n",
    ),
    (
        "外部对象冒充局部 app 工厂（other.make() 不是 self.make()）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t(other):\n"
        "    app = other.make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "R1-8a：client = TestClient(app) 之后 with client:",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    with client:\n"
        "        pass\n",
    ),
    (
        "R1-8b：ExitStack.enter_context(TestClient(app))",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with contextlib.ExitStack() as stack:\n"
        "        c = stack.enter_context(TestClient(app))\n",
    ),
    (
        "R1-8c：enter_context(先前构造的实例)",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    stack = contextlib.ExitStack()\n"
        "    stack.enter_context(client)\n",
    ),
    (
        "R1-9：分支里才赋局部 app（控制流不是词法顺序）",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t(use_local):\n"
        "    app = production_app\n"
        "    if use_local:\n"
        "        app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "R1-10：工厂里 a=FastAPI() 之后被覆盖成生产 app",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    a = production_app\n"
        "    return a\n"
        "def t():\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "R1-11：同名方法跨类污染（A.make 安全不代表 B.make 安全）",
        "from app.main import app as production_app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class A:\n"
        "    def make(self):\n"
        "        a = FastAPI()\n"
        "        return a\n"
        "class B:\n"
        "    def make(self):\n"
        "        return production_app\n"
        "    def test_x(self):\n"
        "        app = self.make()\n"
        "        with TestClient(app) as c:\n"
        "            pass\n",
    ),
    (
        "R1-13c：TestClient(app=...) 关键字形态",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with TestClient(app=app) as c:\n"
        "        pass\n",
    ),
    (
        "L2-b：TestClient 实例存进 self 再在别处 with",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "class T:\n"
        "    def setup(self):\n"
        "        self.c = TestClient(app)\n"
        "    def test_x(self):\n"
        "        with self.c:\n"
        "            pass\n",
    ),
    (
        "L2-d：工厂函数返回 TestClient(app) 后直接 with make()",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    return TestClient(app)\n"
        "def t():\n"
        "    with make():\n"
        "        pass\n",
    ),
    (
        "L1-c：包装器没有真的调 no_lifespan",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "L1-d：包装器在 with 之外 yield（隔离没盖住让出控制权那一刻）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        pass\n"
        "    yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "L1-e：包装器隔离的是**另一个**形参",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(other, a):\n"
        "    with no_lifespan(other):\n"
        "        yield a\n"
        "def t():\n"
        "    spare = FastAPI()\n"
        "    with isolated(spare, app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "工厂名被重绑定后仍冒充局部 app 工厂",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app as real_app\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t():\n"
        "    make = lambda: real_app\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    # ── LOW#18（X4 验收单 §7.7a 其四）：阻断项 E 的原始反例 ────────────────
    # E 修好了却没进常设反例清单，等于「加门 ≠ 加强度」——下一个人把
    # `fastapi_returning_funcs -= disqualified_factory_keys` 那行删掉，22/11 照样
    # 全绿。这两条把 E 的两个方向都钉住：
    #   * 安全版**先**定义（安全版先进集合，key 相同 ⇒ 调用点按安全算）；
    #   * 安全版**后**定义（Python 运行时真正用的就是它，但门不该因此放行 ——
    #     判据是「每个定义都合格」，不是「最后一个定义合格」）。
    # 运行时用的是**后**定义的那个，所以第一条才是真实害；第二条防的是有人
    # 把差集改成「只看最后一个定义」这种看似更精确、实则又漏一半的收窄。
    (
        "同名工厂重定义：安全版在前，不安全版在后（阻断项 E 的原始形态）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app as real_app\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def make():\n"
        "    return real_app\n"
        "def t():\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "同名工厂重定义：不安全版在前，安全版在后（顺序反过来同样不算数）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app as real_app\n"
        "def make():\n"
        "    return real_app\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t():\n"
        "    app = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    # ── round-1 Codex HIGH-1：转调 + 同名重定义的**组合** ───────────────────
    # 这一条是本卡自己的 M16 初版修复引入的漏检（父版报 1，初版报 0），由独立复核
    # 用纯 AST 交叉复现抓到。机制是**暂态资格传播**：只把失格集每轮重算、而可信集
    # 仍 add-only 时，`outer` 会读到同一轮里刚被安全版 `make` 加进去、但本轮差集
    # 还没执行的资格，抢先拿到安全身份；随后差集只剔掉 `make`，`outer` 幸存 ——
    # 而它调用的 `make()` 在运行时返回的是生产 app。
    # 加大迭代次数**不能**修（内外 20/40 仍漏），修法是「冻结知识 + 按 key 聚合 +
    # 整组通过才发布」，见 `_mark_all_fastapi_returning`。
    (
        "转调一个同名重定义过的工厂（round-1 Codex HIGH-1 的组合形态）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app as real_app\n"
        "def outer():\n"
        "    return make()\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def make():\n"
        "    return real_app\n"
        "def t():\n"
        "    app = outer()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    # ══════════════════════════════════════════════════════════════════
    # CARD-W4-5（第十二批）：X4 两轮终审列为未整改的 5 HIGH + 1 unknown 放行。
    # 下面 13 条里有 12 条在改动前**实测 0 违规**（六组 before/after 见验收单），
    # 也就是「今天就能写出来、会跑真实 lifespan、而门判它合规」的源码。
    # 唯一的例外是最后一条 (e)-2，它改动前后都被抓（原因不同），留在这里是
    # 作为 `验伪锚 e` 的配对反例——锁住 (e) 的放宽不许过头。
    # ══════════════════════════════════════════════════════════════════
    (
        "(a)-1 enter_context(cm=TestClient(app))：关键字传参绕过位置参扫描",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with contextlib.ExitStack() as stack:\n"
        "        c = stack.enter_context(cm=TestClient(app))\n",
    ),
    (
        "(a)-2 enter_context(**kw)：实参静态不可知必须 fail-closed，不是 continue",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t(kw):\n"
        "    with contextlib.ExitStack() as stack:\n"
        "        c = stack.enter_context(**kw)\n",
    ),
    (
        "(b)-1 with (client if flag else client)：IfExp 不是 Call，旧实现整支放行",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t(flag):\n"
        "    client = TestClient(app)\n"
        "    with (client if flag else client):\n"
        "        pass\n",
    ),
    (
        "(b)-2 with (nullcontext() if flag else TestClient(app))：危险的是 orelse 支",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t(flag):\n"
        "    with (contextlib.nullcontext() if flag else TestClient(app)):\n"
        "        pass\n",
    ),
    (
        "(c)-1 enter_context(client := TestClient(app))：海象既不入绑定表也不是 Call",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with contextlib.ExitStack() as s:\n"
        "        s.enter_context(client := TestClient(app))\n",
    ),
    (
        "(c)-2 with <不可证的形参>：模块内有 TestClient 可达性 ⇒ 不许静默放行",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t(client):\n"
        "    with client:\n"
        "        pass\n",
    ),
    (
        "(c)-3 with make(flag)：**有些** return 是 main 实例（all 口径漏掉的那一半）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def make(flag, other):\n"
        "    if flag:\n"
        "        return TestClient(app)\n"
        "    return other\n"
        "def t(o):\n"
        "    with make(True, o):\n"
        "        pass\n",
    ),
    (
        "(d)-1 tuple 解包出 TestClient 实例（模块 docstring 自认的阻断项 D）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "import app.main\n"
        "def make():\n"
        "    return FastAPI(), TestClient(app.main.app)\n"
        "def t():\n"
        "    _, c = make()\n"
        "    with c:\n"
        "        pass\n",
    ),
    (
        "(d)-2 del 之后名字不再绑着那个局部 app",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    del app\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "(d)-3 match-case 的 capture 名遮蔽了外面那个可证的局部 app",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t(x):\n"
        "    app = FastAPI()\n"
        "    match x:\n"
        "        case [app]:\n"
        "            with TestClient(app) as c:\n"
        "                pass\n",
    ),
    (
        "(f)-1 包装器体内重绑定了被隔离的形参（隔离盖的是重绑定之前那个对象）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        a = app\n"
        "        yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "(f)-2 包装器 yield 出去的不是被隔离的那个对象",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a, other):\n"
        "    with no_lifespan(a):\n"
        "        yield other\n"
        "def t(o):\n"
        "    with isolated(app, o), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "(f)-3 包装器同名重定义：合格版在前、不合格版在后（Python 用后者）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        yield a\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "(c)-4 容器取值 with clients[0]：追不动 ⇒ fail-closed，不再静默放行",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    clients = [TestClient(app)]\n"
        "    with clients[0]:\n"
        "        pass\n",
    ),
    (
        "(e)-2 no_lifespan(m.other) 不覆盖 TestClient(m.app)（配对反例：放宽不许过头）",
        "import app.main as m\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(m.other), TestClient(m.app) as c:\n"
        "        pass\n",
    ),
]

_AST_MUST_PASS: list[tuple[str, str]] = [
    (
        "验伪锚 1：标准隔离形态",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 2：函数级 import + 别名 TestClient",
        "def t():\n"
        "    from app.main import app\n"
        "    from fastapi.testclient import TestClient as TC\n"
        "    from tests.support.lifespan import lifespan_lite\n"
        "    with lifespan_lite(app), TC(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 3：局部 FastAPI()（来源可证）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 4：helper 返回局部 FastAPI() 后解包",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def make():\n"
        "    a = FastAPI()\n"
        "    return a, 1\n"
        "def t():\n"
        "    app, n = make()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 6：外层 with no_lifespan(app) 支配内层 with TestClient(app)",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(app):\n"
        "        with TestClient(app) as c:\n"
        "            pass\n",
    ),
    (
        "验伪锚 7：完整属性链 fastapi.testclient.TestClient + 局部 app",
        "import fastapi\n"
        "import fastapi.testclient\n"
        "from fastapi import FastAPI\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    with fastapi.testclient.TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 8：裸 TestClient(app) 不进 with —— 不跑 lifespan，不算违规",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    return client.get('/x')\n",
    ),
    (
        "验伪锚 9：局部 app 构造的实例进 with —— 无害",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app = FastAPI()\n"
        "    client = TestClient(app)\n"
        "    with client:\n"
        "        pass\n",
    ),
    (
        "验伪锚 10：自建 contextmanager 包 no_lifespan（合法，不该报）",
        "import contextlib\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "@contextlib.contextmanager\n"
        "def isolated(a):\n"
        "    with no_lifespan(a):\n"
        "        yield a\n"
        "def t():\n"
        "    with isolated(app), TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 11：外层 no_lifespan(app) 支配 with client:（合法，不该报）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    client = TestClient(app)\n"
        "    with no_lifespan(app):\n"
        "        with client:\n"
        "            pass\n",
    ),
    # ── M16（X4 验收单 §7.10 D 类）：失格名单不得误拒**前向引用**的安全工厂 ──
    # `outer()` 转调 `inner()`、而 `inner` 定义在**后面** —— 纯 Python 里完全合法
    # （调用发生在 import 之后，两个名字都已绑定）。失格名单跨迭代累积的那一版会
    # 在第一轮把 outer 钉死，之后学会 inner 也翻不了身。两条正例把顺序两个方向
    # 都锁住：只有 A 是回归锚（B 在修复前就已经是绿的），留 B 是为了让「顺序不
    # 影响结论」这句话本身有门。
    (
        "验伪锚 12：转调工厂，被调者定义在**后**（前向引用，合法）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def outer():\n"
        "    return inner()\n"
        "def inner():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def t():\n"
        "    app = outer()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 13：转调工厂，被调者定义在**前**（同一段代码换个顺序，结论必须相同）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def inner():\n"
        "    a = FastAPI()\n"
        "    return a\n"
        "def outer():\n"
        "    return inner()\n"
        "def t():\n"
        "    app = outer()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 5：同类方法工厂 self._make()（test_rag_four_state_api 的真实形态）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "class T:\n"
        "    def _make(self):\n"
        "        app = FastAPI()\n"
        "        return app, 1\n"
        "    def test_x(self):\n"
        "        app, _ = self._make()\n"
        "        with TestClient(app, raise_server_exceptions=False) as c:\n"
        "            pass\n",
    ),
    # ══════════════════════════════════════════════════════════════════
    # CARD-W4-5：(c) 的三分把「不可证」从静默放行改成 fail-closed 之后，四条
    # **可证**的窄化各配一条正例。它们是这道门不至于变成噪声机器的全部依据 ——
    # 一刀切 fail-closed 实测会让 385 个文件里的 196 个变红（1453 条），其中 194
    # 个只是 `with pytest.raises(...)` / `with open(...)` 这类（2026-09-06 实测）。
    # 删掉任何一条窄化，对应的这条正例立刻翻红。
    # ══════════════════════════════════════════════════════════════════
    (
        "验伪锚 C1：async with lock（TestClient 没有 __aenter__，可证不是它）",
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "async def t(lock):\n"
        "    async with lock:\n"
        "        pass\n",
    ),
    (
        "验伪锚 C2：with pytest.raises(...)（调用面 = 已声明的跨函数盲区）",
        "import pytest\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with pytest.raises(ValueError):\n"
        "        pass\n",
    ),
    (
        "验伪锚 C3：模块内零 TestClient 可达性时的 with self._lock",
        "class C:\n    def m(self):\n        with self._lock:\n            pass\n",
    ),
    (
        "验伪锚 C4：import 来的模块的属性（对象不由本模块构造）",
        "import somemod as mod\n"
        "from app.main import app\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    with mod._refresh_guard:\n"
        "        pass\n",
    ),
    (
        "验伪锚 e：no_lifespan(m.app) 覆盖 TestClient(m.app)（属性链两侧同路径）",
        "import app.main as m\n"
        "from fastapi.testclient import TestClient\n"
        "from tests.support.lifespan import no_lifespan\n"
        "def t():\n"
        "    with no_lifespan(m.app), TestClient(m.app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 a：enter_context(cm=<局部 app 的 TestClient>)（关键字面不许一律判违规）",
        "import contextlib\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    a = FastAPI()\n"
        "    with contextlib.ExitStack() as s:\n"
        "        s.enter_context(cm=TestClient(a))\n",
    ),
    # ── NamedExpr 递归的承重锚（本卡归因变异实测补上）：反例 (c)-1 在没有这条
    #    递归时**照样被抓**——被 (c) 三分的 fail-closed 兜住，只是理由从「它是
    #    app.main 的 client」退化成「来源不可证」。也就是说那条反例证明不了这条
    #    递归。真正只有这条递归能做到的是**不误报**：海象包着局部 app 时必须放行。
    (
        "验伪锚 c1：enter_context(c := TestClient(局部 app))（海象递归不许把合法写法判红）",
        "import contextlib\n"
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    a = FastAPI()\n"
        "    with contextlib.ExitStack() as s:\n"
        "        s.enter_context(c := TestClient(a))\n",
    ),
    (
        "验伪锚 b：IfExp 两支都是局部 app 的 client（展开不许把合法写法判红）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t(flag):\n"
        "    a = FastAPI()\n"
        "    c1 = TestClient(a)\n"
        "    c2 = TestClient(a)\n"
        "    with (c1 if flag else c2):\n"
        "        pass\n",
    ),
    (
        "验伪锚 d：字面 tuple 解包逐位配对（n 是常量，不该被当成 app 来源）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def t():\n"
        "    app, n = FastAPI(), 1\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    # ── (d) 的回归锚：转调工厂 + tuple + 解包。逐位表若只认「字面 tuple」，
    #    `outer` 拿不到表 ⇒ 每元素 unknown ⇒ 这两条当场翻红。两个定义顺序都留，
    #    因为「被调者在前」那条还额外锁住冻结知识（只清空不冻结时它会红）。
    (
        "验伪锚 d2：转调工厂返回 tuple 后解包，被调者定义在**后**",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def outer():\n"
        "    return inner()\n"
        "def inner():\n"
        "    a = FastAPI()\n"
        "    return a, 1\n"
        "def t():\n"
        "    app, n = outer()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
    (
        "验伪锚 d3：转调工厂返回 tuple 后解包，被调者定义在**前**（换顺序结论须相同）",
        "from fastapi import FastAPI\n"
        "from fastapi.testclient import TestClient\n"
        "def inner():\n"
        "    a = FastAPI()\n"
        "    return a, 1\n"
        "def outer():\n"
        "    return inner()\n"
        "def t():\n"
        "    app, n = outer()\n"
        "    with TestClient(app) as c:\n"
        "        pass\n",
    ),
]


def run_ast_negative_control() -> int:
    """四类绕过必须被抓；四条正例必须不被抓（验伪锚，防「恒判违规」的假门）。"""
    print("=== AST GATE NEGATIVE CONTROL ===")
    failures: list[str] = []
    for label, src in _AST_MUST_FLAG:
        vs = analyze_source(src, f"<negctl:{label}>")
        status = "CAUGHT" if vs else "*** MISSED ***"
        print(f"  [must-flag] {status}: {label}")
        if not vs:
            failures.append(f"绕过未被抓: {label}")
        else:
            print(f"              → {vs[0]}")
    for label, src in _AST_MUST_PASS:
        vs = analyze_source(src, f"<negctl:{label}>")
        status = "CLEAN" if not vs else "*** FALSE POSITIVE ***"
        print(f"  [must-pass] {status}: {label}")
        if vs:
            failures.append(f"正例误判: {label} → {vs}")
    if failures:
        print("AST-NEGATIVE-CONTROL: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"AST-NEGATIVE-CONTROL: PASS ({len(_AST_MUST_FLAG)} 绕过全抓 / {len(_AST_MUST_PASS)} 正例全净)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 子进程环境（第八批 BLOCKER 的收口）
# ═══════════════════════════════════════════════════════════════════════════

#: 负控钉死的连接目标：受拦端口 + loopback。门必然拦得住它。
PINNED_NEO4J_URI = "bolt://127.0.0.1:7691"
PINNED_TEST_URI = "bolt://127.0.0.1:7692"
#: 假凭据 —— 即使某条路径绕过了门，也拿不到任何真实库的会话。
PINNED_NEO4J_USER = "w4-negctl-invalid-user"
PINNED_NEO4J_PASSWORD = "w4-negctl-invalid-password"


def _child_env(vault_tmp: Path, lance_tmp: Path, ledger: Path | None, backend_dir: Path) -> dict[str, str]:
    """构造子进程环境：清 Neo4j 面 → 钉死受拦目标 → 关豁免 → 隔离写路径。

    ``backend_dir`` 是子进程的 backend 根（负控里恒为**隔离副本**），
    ``PYTHONPATH`` 必须指向它，否则 ``-p tests.support.guard_plugin`` 会加载到
    真实树里的那一份，验的就不是副本的代码了。
    """
    env = os.environ.copy()
    # 1) 清掉调用者带进来的**全部** Neo4j 相关变量（含 NEO4J_URI/USER/PASSWORD/
    #    TEST_URI/AUTH/DATABASE… 无论叫什么，只要以 NEO4J 开头）。
    for key in [k for k in env if k.upper().startswith("NEO4J")]:
        env.pop(key, None)
    # 2) 钉死：目标端口必在门的射程内；凭据是假的。
    env["NEO4J_URI"] = PINNED_NEO4J_URI
    env["NEO4J_TEST_URI"] = PINNED_TEST_URI
    env["NEO4J_USER"] = PINNED_NEO4J_USER
    env["NEO4J_PASSWORD"] = PINNED_NEO4J_PASSWORD
    # 3) 门自身的 fail-closed 开关：目标不在射程内就拒绝装门（子进程起不来）。
    env["W4_GUARD_REQUIRE_BLOCKED_TARGET"] = "1"
    # 4) 负控运行里不允许出现 advisory —— 豁免彻底关掉。
    env["W4_GUARD_NO_EXEMPT"] = "1"
    # 5) 写路径隔离到 tmp（live vault / 现网 LanceDB 只读）。
    #    ⚠️ canonical 与 legacy 两个 LanceDB 变量必须**同值**：
    #    `lib/agentic_rag/config.py::_resolve_lancedb_db_path` 在两者不同时抛
    #    RuntimeError，而 `app/main.py:103` 是**无守护直调**——于是 lifespan 会在
    #    LanceDB 这一步就 abort，**根本走不到 Neo4j 预热**，负门拿到 blocked=0
    #    却以为是「哨兵没接住」。只 pin canonical 而让 legacy 从 .env（本车道
    #    .env:94 就有 LANCEDB_PATH）漏进来，负门就变成了在测另一件事。
    #    2026-09-03 于本车道实测：只 pin canonical ⇒ 3 条全部 setup ERROR
    #    "Conflicting LanceDB paths"、attempts=0；两者同值 ⇒ 连接尝试正常发生。
    env["CANVAS_BASE_PATH"] = str(vault_tmp)
    env["LANCEDB_DATA_PATH"] = str(lance_tmp)
    env["LANCEDB_PATH"] = str(lance_tmp)
    # 6) 防注入：addopts 能塞 --rootdir/--confcutdir 绕开根 conftest；
    #    PYTEST_PLUGINS 能在门装上之前 import 任意插件。
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    # ⚠️ 不设 PYTEST_DISABLE_PLUGIN_AUTOLOAD：根 conftest 与目标文件依赖
    #    hypothesis / pytest-asyncio / pytest-bdd 的注册，关掉 autoload 会让
    #    collection 直接坏掉——那是「门没被验证」而不是「门更严」。门前窗口改由
    #    guard_plugin 的 **import 期装门** 收敛（见该模块 docstring）。
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # -p 插件加载早于 pytest 把 rootdir 塞进 sys.path —— 必须显式给 PYTHONPATH。
    # ⚠️ 只放隔离副本，**不**追加调用者原有的 PYTHONPATH：否则真实树可能排在前面，
    # 子进程会去 import 真实树的 tests.support.*，验的就不是副本了。
    env["PYTHONPATH"] = str(backend_dir)
    if ledger is not None:
        env["W4_GUARD_LEDGER"] = str(ledger)
    else:
        env.pop("W4_GUARD_LEDGER", None)
    return env


def _base_cmd() -> list[str]:
    """pytest 子进程命令前缀。

    用 ``sys.executable -m pytest`` 而不是 ``BACKEND_DIR/.venv/bin/pytest``
    （第八批 Codex MEDIUM/卡文裁判 2）：负控必须跑在**调用者指定的那个解释器**上，
    否则「我用 A 解释器验证的门」和「你用 B 解释器跑的测试」不是同一件事。
    """
    return [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "tests.support.guard_plugin",  # 显式点名装门（不受 rootdir/confcutdir 影响）
        "-p",
        "no:cacheprovider",
        "--override-ini=addopts=",
    ]


def _parse_summary(stdout: str) -> tuple[int, int, int, int] | str:
    """整行唯一解析门的汇总行。返回 (total, blocked, advisory, unaccounted) 或错误串。"""
    hits = [m for line in stdout.splitlines() if (m := SUMMARY_RE.match(line.strip()))]
    if len(hits) != 1:
        return f"门汇总行匹配 {len(hits)} 次（期望恰好 1 次）"
    return tuple(int(g) for g in hits[0].groups())  # type: ignore[return-value]


# ═══════════════════════════════════════════════════════════════════════════
# 变异 + 子进程 + 还原
# ═══════════════════════════════════════════════════════════════════════════


def make_isolated_backend(tmp_root: Path) -> Path:
    """把当前工作树的 ``backend/`` 复制一份到 tmp，变异只在副本上做。

    R1 Codex HIGH-6/HIGH-7 的结构性收口：

    * **HIGH-7（变异前无 CAS）**：真实的 tracked 测试文件从头到尾**一个字节都不
      被写**，所以「读原文 → 期间别人编辑 → 用旧变异体覆盖」这条链根本不存在，
      不需要靠 CAS 去追一个本来就不该发生的写。
    * **HIGH-6（`absent → exists` 就 unlink 可能删掉别人的数据）**：变异运行产生的
      运行时文件（orchestrator 的 journal 只落在 ``app/data/`` 下，重定向不了）
      落在**副本**里，随 tmp 目录一起消失；真实树下的同名文件本脚本**永远不删**。

    **只复制 git tracked 的文件**（内容取自工作树，所以未提交的改动照样进副本 ——
    负控要验的就是此刻这份代码）。这一条不是为了省空间，是为了不把数据带出去：
    ``backend/data/`` 下有 ``llm_call_logs.db`` / ``neo4j_memory.json`` /
    ``learning_memories.json`` 这类**运行时数据**，它们全是 git-ignored 的，
    整目录 ``copytree`` 会把它们原样搬进 ``/tmp``（2026-09-03 实测搬了 12 个文件，
    含一个 36KB 的 sqlite）。tracked-only 的复制把这一面直接消掉。

    ``.env`` 是 git-ignored 但副本必须能读到它（``Settings`` 依赖），所以用**软链**
    而不是拷贝 —— 凭据一个字节都不落到 tmp。
    """
    iso = tmp_root / "iso-backend"
    iso.mkdir(parents=True)
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", "."],
        cwd=BACKEND_DIR,
        capture_output=True,
        check=True,
        timeout=120,
    )
    names = [n for n in listing.stdout.decode("utf-8").split("\0") if n]
    if len(names) < 500:
        raise RuntimeError(f"git ls-files 只列出 {len(names)} 个文件，副本会不完整，拒绝继续")
    for name in names:
        src = BACKEND_DIR / name
        if not src.exists():  # 已删除但还在 index 里
            continue
        dst = iso / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst, follow_symlinks=False)
    real_env = BACKEND_DIR / ".env"
    if real_env.exists():
        (iso / ".env").symlink_to(real_env)
    # 副本里不应有任何运行时残留（tracked-only 复制本来就不会带，这里做个断言式清理）
    for p in runtime_files(iso):
        if p.exists():
            p.unlink()
    return iso


def sha_of(path: Path) -> str:
    if not path.exists():
        return "absent"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_snapshot(root: Path) -> str:
    """``root`` 下受监视运行时文件的 "<sha|absent>  <path>" 快照。

    ⛔ 必须传 root 并**在每次快照时重新展开 glob**：模块级缓存一份 Path 列表会让
    「跑完之后新出现的 journal」永远进不了 after 快照 —— 那正是本门要抓的东西。
    """
    return "\n".join(f"{sha_of(p)}  {p}" for p in runtime_files(root))


def _parse_junit(path: Path, target_rel: str) -> list[tuple[str, dict]]:
    """junitxml → ``[(nodeid, {"outcome": ..., "text": ...}), ...]``，**保留重复项**。

    刻意返回列表而不是 dict：同一个 nodeid 可能出现多次（参数化、重复传参、
    插件重跑），dict 会把它们悄悄合并成一条，于是「三条各跑一次」这句判据就变成了
    「三个不同的名字出现过」——数量对不上也看不出来。
    """
    module_dotted = target_rel[:-3].replace("/", ".")
    out: list[tuple[str, dict]] = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        if classname.startswith(module_dotted):
            chain = classname[len(module_dotted) :].lstrip(".")
            nid = f"{target_rel}::" + (f"{chain.replace('.', '::')}::{name}" if chain else name)
        else:
            nid = f"{classname.replace('.', '/')}::{name}"
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        node = failure if failure is not None else (error if error is not None else None)
        if node is not None:
            outcome = "failed" if failure is not None else "error"
            text = " ".join(filter(None, [(node.get("message") or ""), (node.text or "")]))
        elif skipped is not None:
            outcome, text = "skipped", (skipped.get("message") or "")
        else:
            outcome, text = "passed", ""
        out.append((nid, {"outcome": outcome, "text": text}))
    return out


def main() -> int:
    print("=== lifespan isolation NEGATIVE CONTROL ===")
    print(f"    interpreter: {sys.executable}")

    # -- 00. runtime_files 自证 —— **先于一切**，且不受任何 --xxx 短路影响 ------
    #    它证明的是「本脚本自己用来判定运行时文件有没有被写的那个函数」行为正确。
    #
    #    放在 `--ast-*` 分支之前是**刻意的选择**，理由如实写清（round-1 Codex LOW-3
    #    更正了上一版的说法）：两条 AST 捷径本身**并不**调用 runtime_snapshot ——
    #    `--ast-negative-control` 和 `--ast-only` 都在运行时快照之前就 return 了。
    #    这里要的是「本脚本的**每一个**入口都跑一遍综合自检」，不给「换个参数跑就
    #    不会红」的选择权。代价如实登记：纯静态检查因此也需要一个可写的临时目录
    #    （mkdtemp/mkdir/write_text），在只读文件系统上会失败。
    if run_runtime_files_selftest() != 0:
        print("NEGATIVE-CONTROL: FAIL — runtime_files 自证未通过，后续判定不可信")
        return 1

    if "--ast-negative-control" in sys.argv:
        return run_ast_negative_control()

    # -- 0a. 门必须被根 conftest 接线（否则哨兵缺席，负门失去被测对象）--------
    conftest_text = (BACKEND_DIR / "tests/conftest.py").read_text(encoding="utf-8")
    if "live_port_guard" not in conftest_text:
        print(
            "NEGATIVE-CONTROL: FAIL — 根 tests/conftest.py 未引用 live_port_guard："
            "结账哨兵不会在子进程里工作，负门失去被测对象。"
        )
        return 1

    # -- 0b. AST 门（裁判 6）------------------------------------------------
    n_violations, violation_lines, n_files = run_ast_gate()
    print(f"[0] AST gate: {n_violations} violations across {n_files} files")
    for v in violation_lines:
        print(f"    VIOLATION: {v}")
    if "--ast-only" in sys.argv:
        if n_violations:
            print("AST-GATE: FAIL")
            return 1
        print(f"AST-GATE: PASS (0 violations in {n_files} files)")
        return 0

    tmp_root = Path(tempfile.mkdtemp(prefix="lifespan-negctl-"))
    cleaned = False

    def _cleanup(*_a) -> None:
        nonlocal cleaned
        if cleaned:
            return
        cleaned = True
        shutil.rmtree(tmp_root, ignore_errors=True)

    atexit.register(_cleanup)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, lambda *_: (_cleanup(), sys.exit(130)))

    vault_tmp = tmp_root / "vault"
    lance_tmp = tmp_root / "lancedb"
    vault_tmp.mkdir()
    lance_tmp.mkdir()
    pos_junit = tmp_root / "positive-junit.xml"
    neg_junit = tmp_root / "negctl-junit.xml"
    pos_ledger = tmp_root / "ledger-positive.json"
    neg_ledger = tmp_root / "ledger-negative.json"

    # -- 0c. 隔离副本：变异只在这里做，真实 tracked 文件一个字节都不写 --------
    iso = make_isolated_backend(tmp_root)
    iso_target = iso / TARGET_REL
    print(f"[0b] 隔离副本: {iso}")

    # 真实树的运行时文件在整个脚本期间必须纹丝不动（本脚本从不写、也从不删它们）
    real_before = runtime_snapshot(BACKEND_DIR)

    # -- 0d. 前置：逐项精确核对**应用侧解析出来的**隔离环境 -------------------
    preflight_env = _child_env(vault_tmp, lance_tmp, None, iso)
    preflight = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, os, sys;"
            "sys.path.insert(0, 'lib');"
            "from app.config import get_settings;"
            "from agentic_rag.config import _resolve_lancedb_db_path;"
            "s = get_settings();"
            "print('W4_PREFLIGHT=' + json.dumps({"
            "'neo4j_uri': s.NEO4J_URI,"
            "'neo4j_user': getattr(s, 'NEO4J_USER', None),"
            "'neo4j_password': getattr(s, 'NEO4J_PASSWORD', None),"
            "'canvas_base_path': str(s.canvas_base_path),"
            "'lancedb_resolved': _resolve_lancedb_db_path(),"
            "'lancedb_data_path_env': os.environ.get('LANCEDB_DATA_PATH'),"
            "'lancedb_path_env': os.environ.get('LANCEDB_PATH'),"
            "}))",
        ],
        cwd=iso,
        env=preflight_env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    resolved: dict = {}
    for line in preflight.stdout.splitlines():
        if line.startswith("W4_PREFLIGHT="):
            resolved = json.loads(line.split("=", 1)[1])
    print(f"[0c] Settings 解析（rc={preflight.returncode}）: {json.dumps(resolved, ensure_ascii=False)}")
    # R1 Codex MEDIUM-15：旧版只精确核对 NEO4J_URI，LanceDB 只要求非空、
    # canvas 路径完全不查 —— 解析漂移到现网 LanceDB 或真实 vault 时前置检查照样通过。
    expected_preflight = {
        "neo4j_uri": PINNED_NEO4J_URI,
        "neo4j_user": PINNED_NEO4J_USER,
        "neo4j_password": PINNED_NEO4J_PASSWORD,
        "canvas_base_path": str(vault_tmp),
        "lancedb_resolved": str(lance_tmp),
        "lancedb_data_path_env": str(lance_tmp),
        "lancedb_path_env": str(lance_tmp),
    }
    mismatch = {k: (v, resolved.get(k)) for k, v in expected_preflight.items() if resolved.get(k) != v}
    if preflight.returncode != 0 or mismatch:
        print("NEGATIVE-CONTROL: FAIL — 应用侧解析出的隔离环境与钉死值不符（期望, 实得）:")
        for k, (want, got) in mismatch.items():
            print(f"    {k}: {want!r} != {got!r}")
        print("--- preflight stdout tail ---")
        print(preflight.stdout[-1200:])
        print("--- preflight stderr tail ---")
        print(preflight.stderr[-1200:])
        return 1

    original = iso_target.read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    mutated_bytes = original.decode("utf-8").replace(ANCHOR, MUTATED).encode("utf-8")

    # 副本内容必须与真实工作树逐字节一致，否则本门验的不是这份代码
    if hashlib.sha256(TARGET.read_bytes()).hexdigest() != original_sha:
        print("NEGATIVE-CONTROL: FAIL — 隔离副本里的目标文件与工作树不一致（复制期间被改？）")
        return 1

    pytest_rc: int | None = None
    total = 0
    green: list[str] = []
    red_nodeids: set[str] = set()
    red_for_wrong_reason: list[str] = []
    reason_verified: set[str] = set()
    expected_nodeids: set[str] = set()
    summary: tuple[int, int, int, int] | str = "未运行"
    ledger_problem: str | None = None
    child_stdout = ""
    child_stderr = ""
    iso_runtime_before = runtime_snapshot(iso)
    positive_runtime_ok = False
    mutated_runtime_delta = ""

    # -- 1. 预采集 nodeid（变异前）：必须与钉死的完整 nodeid 集全等 -------
    collect = subprocess.run(
        _base_cmd() + [*FIXED_TARGET_NODEIDS, "--collect-only", "-q"],
        cwd=iso,
        env=_child_env(vault_tmp, lance_tmp, None, iso),
        capture_output=True,
        text=True,
        timeout=PYTEST_TIMEOUT_S,
    )
    expected_nodeids = {ln.strip() for ln in collect.stdout.splitlines() if "::" in ln}
    if collect.returncode != 0 or expected_nodeids != set(FIXED_TARGET_NODEIDS):
        print(
            f"NEGATIVE-CONTROL: FAIL — 预采集失败或与钉死 nodeid 不全等（collect rc={collect.returncode}）："
            f"缺 {sorted(set(FIXED_TARGET_NODEIDS) - expected_nodeids)}，"
            f"多 {sorted(expected_nodeids - set(FIXED_TARGET_NODEIDS))}"
        )
        print(collect.stdout[-1500:])
        return 1
    print(f"[1] 预采集 nodeid: {len(expected_nodeids)} 条（与钉死完整 nodeid 全等，collect rc=0）")

    # -- 1b. 正控：三条必须**各跑一次且全 passed**，门账全零，运行时零写 -----
    #     R1 Codex HIGH-12：只查 rc=0 证明不了「三条全绿」—— 在 client fixture
    #     yield 之后 `pytest.skip()` 同样是 rc=0/零门账，而变异态照旧按预期红，
    #     于是整条负门变成假 PASS。所以正控也出 junit，逐条核对 outcome。
    pos = subprocess.run(
        _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=short", "-rA", f"--junitxml={pos_junit}"],
        cwd=iso,
        env=_child_env(vault_tmp, lance_tmp, pos_ledger, iso),
        capture_output=True,
        text=True,
        timeout=PYTEST_TIMEOUT_S,
    )
    pos_summary = _parse_summary(pos.stdout)
    pos_cases = _parse_junit(pos_junit, TARGET_REL) if pos_junit.exists() else []
    pos_outcomes = [(nid, c["outcome"]) for nid, c in pos_cases]
    positive_runtime_ok = runtime_snapshot(iso) == iso_runtime_before
    print(f"[1b] 正控 rc={pos.returncode} 门汇总={pos_summary} outcomes={pos_outcomes}")
    pos_problem = None
    if pos.returncode != 0:
        pos_problem = f"正控 rc={pos.returncode} ≠ 0"
    elif sorted(nid for nid, _ in pos_outcomes) != sorted(FIXED_TARGET_NODEIDS):
        # **多重集**比较：三条各恰好一次。用集合比会把重复项吞掉。
        pos_problem = f"正控 junit 的 nodeid 多重集与钉死集不等（要求各恰好一次）：{pos_outcomes}"
    elif any(outcome != "passed" for _, outcome in pos_outcomes):
        pos_problem = f"正控三条不是全 passed：{pos_outcomes}（skip/error 也不算绿）"
    elif not isinstance(pos_summary, tuple):
        pos_problem = f"正控门汇总行解析失败：{pos_summary}"
    elif pos_summary != (0, 0, 0, 0):
        pos_problem = f"正控门账非零：{pos_summary}（隔离态不应有任何连接尝试）"
    elif not positive_runtime_ok:
        pos_problem = "正控（隔离态）动了运行时文件 —— no_lifespan 没挡住启动副作用"
    if pos_problem:
        print(f"NEGATIVE-CONTROL: FAIL — {pos_problem}")
        print("--- 正控 stdout tail ---")
        print(pos.stdout[-2000:])
        return 1
    print("[1c] 正控：三条全 passed、门账全零、运行时文件 unchanged")

    # -- 2. 在**副本**里摘掉 no_lifespan（真实文件不动）--------------------
    count = original.decode("utf-8").count(ANCHOR)
    if count != 1:
        print(
            f"NEGATIVE-CONTROL: FAIL — 隔离锚点出现 {count} 次（期望恰好 1 次），"
            f"文件形态与本脚本假设不符，拒绝盲改: {TARGET_REL}"
        )
        return 1
    iso_target.write_bytes(mutated_bytes)
    print(f"[2] 已在副本里摘掉 no_lifespan: {iso_target}")

    # -- 3. 变异运行 ----------------------------------------------------
    cmd = _base_cmd() + [*FIXED_TARGET_NODEIDS, "-q", "--tb=no", "-rA", f"--junitxml={neg_junit}"]
    print("[3] pytest 子进程（串行，cwd=隔离副本）:", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            cwd=iso,
            env=_child_env(vault_tmp, lance_tmp, neg_ledger, iso),
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as e:
        print("NEGATIVE-CONTROL: FAIL — 变异运行超时；faulthandler dump（stderr）如下")
        print((e.stderr or "")[-5000:])
        print("--- stdout tail ---")
        print((e.stdout or "")[-1000:])
        return 1
    pytest_rc = proc.returncode
    child_stdout = proc.stdout
    child_stderr = proc.stderr
    print(f"    pytest exit={pytest_rc}")

    # -- 3b. 正证据：total == blocked > 0 且 advisory == unaccounted == 0 --
    summary = _parse_summary(proc.stdout)
    if not isinstance(summary, tuple):
        print(f"NEGATIVE-CONTROL: FAIL — {summary}（guard_plugin 未加载？）")
        print(proc.stdout[-1500:])
        return 1
    s_total, s_blocked, s_advisory, s_unacct = summary
    print(f"[3b] 子进程门汇总: total={s_total} blocked={s_blocked} advisory={s_advisory} unaccounted={s_unacct}")

    # -- 3c. 父进程独立复核账本 -----------------------------------------
    if not neg_ledger.exists():
        ledger_problem = "子进程未落账本（最终结算 atexit 未跑？）"
    else:
        led = json.loads(neg_ledger.read_text(encoding="utf-8"))
        print(
            f"[3c] 账本: {json.dumps({k: v for k, v in led.items() if k != 'unaccounted_records'}, ensure_ascii=False)}"
        )
        if (led["total"], led["blocked"], led["advisory"], led["unaccounted"]) != summary:
            ledger_problem = f"账本 {led} 与 stdout 汇总 {summary} 不一致"
        elif not led.get("exempt_disabled"):
            ledger_problem = "账本显示豁免未被禁用（W4_GUARD_NO_EXEMPT 未生效）"

    # -- 4. 解析 junitxml：红因判定必须吃完整 failure/error 正文 ---------
    if not neg_junit.exists():
        print("NEGATIVE-CONTROL: FAIL — junitxml 未生成")
        return 1
    red_list: list[str] = []
    for nid, case in _parse_junit(neg_junit, TARGET_REL):
        total += 1
        if case["outcome"] in ("passed", "skipped"):
            green.append(nid)  # skip 不是红
            continue
        red_list.append(nid)
        red_nodeids.add(nid)
        if EXPECTED_REASON in case["text"]:
            reason_verified.add(nid)
        else:
            red_for_wrong_reason.append(f"{nid} :: {case['text'][:160] or '<无正文 — 红因不明>'}")

    print(
        f"[4] junitxml: total={total} red={len(red_nodeids)} "
        f"green={len(green)} red-wrong-reason={len(red_for_wrong_reason)}"
    )
    for g in green:
        print(f"    GREEN (不应绿): {g}")
    for w in red_for_wrong_reason:
        print(f"    RED-WRONG-REASON: {w}")

    # -- 5. 运行时文件：副本必须被写（隔离承重的正证据）；真实树必须纹丝不动 --
    iso_runtime_after = runtime_snapshot(iso)
    mutated_runtime_delta = "" if iso_runtime_after == iso_runtime_before else iso_runtime_after
    real_after = runtime_snapshot(BACKEND_DIR)
    real_untouched = real_after == real_before
    target_untouched = hashlib.sha256(TARGET.read_bytes()).hexdigest() == original_sha
    print(f"[5] 真实树运行时文件 untouched={real_untouched}; 真实目标文件 untouched={target_untouched}")
    if mutated_runtime_delta:
        print("[5b] 副本里变异态确实写了运行时文件（= 隔离在承重的正证据）:")
        for line in mutated_runtime_delta.splitlines():
            print(f"      {line}")

    # -- 6. 裁定 --------------------------------------------------------------
    problems: list[str] = []
    if pytest_rc != 1:
        problems.append(f"pytest 退出码 {pytest_rc} ≠ 1（期望恰为 tests-failed）")
    if not (s_total == s_blocked > 0):
        problems.append(f"门账 total({s_total}) == blocked({s_blocked}) > 0 不成立")
    if s_advisory != 0:
        problems.append(f"advisory={s_advisory} ≠ 0（有连接以豁免名义真的发出去了）")
    if s_unacct != 0:
        problems.append(f"unaccounted={s_unacct} ≠ 0（有拦截无人结账）")
    if ledger_problem:
        problems.append(ledger_problem)
    if total != len(expected_nodeids):
        problems.append(f"用例总数 {total} ≠ 预采集 {len(expected_nodeids)} — 解析或收集缩水")
    if green:
        problems.append(f"{len(green)} 个用例在 no_lifespan 摘除后没红（哨兵没接住）")
    if sorted(red_list) != sorted(FIXED_TARGET_NODEIDS):
        # 多重集比较：三条各恰好红一次（集合比会把重复项吞掉）
        problems.append(f"红集多重集与钉死 nodeid 不等（要求各恰好一次）：{sorted(red_list)}")
    if red_for_wrong_reason:
        problems.append(f"{len(red_for_wrong_reason)} 个用例红了但原因不对（不是 live port connect）")
    if reason_verified != red_nodeids:
        problems.append(f"红因可验证集 {len(reason_verified)} ≠ 红集 {len(red_nodeids)} —— 红因不明，fail-closed")
    if not mutated_runtime_delta:
        problems.append(
            "变异态**没有**写任何运行时文件 —— 说明 lifespan 没跑到写路径就 abort 了，"
            "这条负门此刻在测别的东西（历史教训：LanceDB canonical/legacy 冲突会让它"
            "在到达 Neo4j 之前就退出）"
        )
    if not real_untouched:
        problems.append(f"真实树的运行时文件被动过（本脚本从不写它们）：\n{real_before}\n---\n{real_after}")
    if not target_untouched:
        problems.append("真实树的目标测试文件被动过（本脚本只改副本）")
    if n_violations:
        problems.append(f"AST 门 {n_violations} 处违规（见上方 VIOLATION 清单）")

    if problems:
        print("NEGATIVE-CONTROL: FAIL")
        for p in problems:
            print(f"  - {p}")
        print("--- 变异运行 child stdout tail ---")
        print(child_stdout[-4000:])
        if child_stderr.strip():
            print("--- 变异运行 child stderr tail ---")
            print(child_stderr[-2000:])
        return 1

    print(
        f"NEGATIVE-CONTROL: PASS ({len(reason_verified)} nodeids red for expected reason; "
        f"summary={summary}; positive control: 3/3 passed, zero attempts, zero runtime writes; "
        f"mutated run in an isolated copy did touch runtime files (isolation is load-bearing); "
        f"real tree untouched; AST-GATE: PASS 0/{n_files} files)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
