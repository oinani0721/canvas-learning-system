# 独立复核请求 — CARD-DEBT-1（全量测试超时根因与 timeout 落地）· **补审 round-4（ZCode × GLM-5.3）**

> **通道与轮次**：round-1 / round-2 走 Codex `gpt-6-astra`（r1 绑 `f595562e` = B0/H1/M6；r2 绑 `bd99c495` = **B0/H0**/M8，均**未绑最终 HEAD**）；round-3 因账号配额**五次调用全 0 字节**未跑成；**本轮 = 补审**，按协议 §2.4.2 走 ZCode CLI + GLM-5.3（用户 2026-09-19 裁定 D-43 附款），轮次编号接 `-r4`。
>
> **审查绑定 = `9d270cdf`**（三份代码文件的最终态）。自证（车道预跑，非你执行）：
> `git --no-pager diff --stat --no-color 9d270cdf HEAD -- backend/pytest.ini backend/tests/conftest.py backend/tests/unit/test_debt1_default_gate.py` = **空**
> （其上两个后继 commit `0ac28596` / `96da70c6` 均为纯 `_bmad-output` 文档）。PREV（本卡开工锚）= `a7341ca4`。
>
> **你的读取面 = cwd（车道树工作树）**：三份文件与 `9d270cdf` 逐字节同（上条绑定 diff 空），行号以工作树为准。
> ⛔ **你的 Bash 被禁**（`--mode build` 天然只读）⇒ **全部 git 输出已内嵌在本 prompt 的 §① 末尾**；⛔ 不要试图运行 git、⛔ 不要修改任何文件。
> ⛔ 本分支上夹着**另一张卡**的 commit `d06f7127`（CARD-G4-13，改 `backend/scripts/**` 与 `backend/tests/regression/**`）——**不在本卡审查面**；按协议 §1「串行车道按本卡 diff 面判」，**只看本卡三份文件**。
>
> **前序独立审查（输入，非轮次）**：`_bmad-output/审查/CARD-DEBT-1-人审裁定-20260919.md`（4 路独立 Agent 对抗审查 + 主 session 逐条复算，绑最终 HEAD）。产出 **1 HIGH**（失败 item 的 teardown 无超时保护——A/B 实证：`--timeout=1` 下 call 先红 + 20s finalizer → 墙钟 **21s**、`Timeout` 字样 **0**；对照 B → 2s、`Failed: Timeout (>1.0s)`；机制：`pytest_exception_interact` → `cancel_timeout()` 拆闹钟且 `timeout_func_only=False` 的闹钟只上一次弦。**声明侧已整改**（ini 注释收窄 + 补「第四类例外」），**行为侧登记 DEBT-3 不修**）+ **7 MEDIUM**（登记不阻断）+ **8 条文档失实**（已改）。⛔ 它不构成任何轮次；**请对抗性地复核它的结论与处置是否可接受**。

## ① 背景与最小读取面（⛔ 只读这些，不要扩大到别的目录）

**这张卡做什么（三处实改 + 一份清单）**：

1. 共享 venv 装 `pytest-timeout==2.4.0`（批级通告 + 主 session 批准）；`backend/pytest.ini` 文件末新增 `timeout = 300` / `timeout_method = signal` 两键与一段注释（为什么加、N 怎么标定、默认门定义、未装插件只警告）；**`addopts`（`:19-21`）一个字没动**、`-m` 默认门**没有**进 addopts。
2. `backend/tests/conftest.py`（1104 行）：**文件末尾新增**一个 `pytest_collection_modifyitems`（`:1043` 起），按一级目录给 `tests/contract` / `tests/integration` / `tests/e2e` 自动补同名 marker；**既有行零删改**。
3. NEW `backend/tests/unit/test_debt1_default_gate.py`（481 行）：5 条子进程真跑的承重行为门。
4. `_bmad-output/审查/evidence-debt1/hang-census.md`：挂起清单（实测产出，DD-03 真跑、真存档、不推断）。

⛔ 本卡**不改** `backend/app/**`、不改任何测试断言、不删不 skip 任何用例、不改 CI、不改 `lefthook.yml` / `requirements.txt` / `pyproject.toml` / `setup.cfg` / `backend/tests/unit/conftest.py` / `backend/tests/support/live_port_guard.py`。

**请读的东西（最小面写死，全部在你 cwd 内）：**

- **内嵌 diff（本 §① 末）**：`git --no-pager diff --no-color a7341ca4 9d270cdf -- backend/pytest.ini backend/tests/conftest.py backend/tests/unit/test_debt1_default_gate.py`（**649 insertions / 0 deletions**，覆盖全部代码改动；请先读它）
- `backend/pytest.ini` 全文（139 行；本卡新增段在文件末）
- `backend/tests/conftest.py` 的 `:1-60`（门装载与 import 面）与 `:1043-1104`（新增 hook 全段）
- `backend/tests/support/live_port_guard.py` 的 `:150-215`（受拦端口与豁免常量）与 `:1564-1587`（`is_exempt` 的相对化口径）——**本卡零改动，仅作对照常量**
- `backend/tests/unit/test_debt1_default_gate.py` 全文（481 行，本卡新增的承重行为门）
- 挂起清单：`_bmad-output/审查/evidence-debt1/hang-census.md`
- 默认门实跑存档：`_bmad-output/审查/evidence-debt1/census-default-gate-20260918T212851.txt`（总结行在 `:3180`）；契约目录收集数：`_bmad-output/审查/evidence-debt1/contract-collect-20260918T202937.txt`（`:239`）
- 行为门终态：`_bmad-output/审查/evidence-debt1/gate-after-r5-20260919T040822.txt`（5 passed）· D-32 整改后复跑：`_bmad-output/审查/evidence-debt1/gate-after-d32-20260919T061825.txt`
- 负控终态存档：`_bmad-output/审查/evidence-debt1/negctl-1-20260919T041430.txt`（段①：删 hook）· `_bmad-output/审查/evidence-debt1/negctl-2-20260919T041529.txt`（段②：删 ini 的 `timeout = 300` 一行）
- durations 标定输入：`_bmad-output/审查/evidence-debt1/unit-open-20260918T192142.txt`（durations 段 `:1005` 起）
- 人审裁定书：`_bmad-output/审查/CARD-DEBT-1-人审裁定-20260919.md`
- 总账 v2：`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` 的 `:56`（DEBT-1 行）
- 协议：`.claude/rules/card-batch-protocol.md` 的 `§2.2`（其中 `tests/contract` 目录级挂起那一条，本卡对它提出措辞更正）

**内嵌 diff（原文，`a7341ca4 → 9d270cdf`，三文件）：**

```diff
diff --git a/backend/pytest.ini b/backend/pytest.ini
index be02c977..98ee1c9a 100644
--- a/backend/pytest.ini
+++ b/backend/pytest.ini
@@ -39,3 +39,101 @@ markers =
     bdd: behavior-driven development tests (pytest-bdd)
     p2: marks P2 medium priority tests
     real_neo4j: marks tests that need the dedicated Neo4j test container (port 7692)
+
+# ============================================================================
+# 单用例超时 [BATCH-2026-09-18-第十五批 / CARD-DEBT-1]
+# ============================================================================
+# 为什么加：在这之前全量跑法会挂死，而「挂死」和「跑完了都过」在存档里长得
+# 一模一样 —— 没有哪一条判据能把它们分开，于是「跑过了」这三个字不可信。
+# timeout 把挂住的用例变成一条有名有姓的红，而不是一次没有结论的等待。
+#
+# N = 300 的标定（开工实测，证据
+# _bmad-output/审查/evidence-debt1/unit-open-20260918T192142.txt
+# 的 `slowest 25 durations` 段）：
+#   * 最慢的【通过】用例是 tests/unit/test_study_question_deep_mode.py::
+#     test_mode_answer_keeps_top_k_20_and_hard_cap_15 —— teardown 217.38s
+#     + call 5.02s，item 总墙钟约 222.4s。
+#   * timeout_func_only 保持默认 false，计时罩住 setup + call + teardown
+#     整个 item —— ⚠️ **仅对每一相都通过的 item 成立**（2026-09-19 人审替代
+#     A/B 实证更正，见下方「第四类例外」）。标定必须按 item 总墙钟算：只看
+#     durations 里的 call 行会取到 35.46s，N 就会被标成 120，当场把三条
+#     本来通过的用例判成超时。
+#   * 卡文的「最慢通过用例的 ≥3 倍」= 667s 超出卡文自己给的上限 300，
+#     按上限取 300。余量因此只有约 1.35 倍：那几条超长 teardown 本身是
+#     待查项（DEBT-3），它们再变慢会先撞上这个值 —— 那是预期内的信号。
+#
+# timeout_method = signal 是 POSIX 上的默认值，这里明写是为了钉住它：
+# thread 方法会 os._exit 掉整个会话，存档被截断在半路 —— 那恰好毁掉本卡
+# 想要的东西（一份读得出根因的挂起清单）。
+#
+# ⚠️ signal 保证的到底是什么（别把它读宽 —— Codex round-1 HIGH 整改）：
+# 插件的 handler 做的是在**主线程**里 pytest.fail()，它**不杀线程、不杀
+# executor、不杀进程**。所以它保证的是「到点把这条用例判红、让会话继续
+# 往下走」，**不是**「到点把挂着的东西终止掉」。以下三类输入不在保证范围内：
+#   ① 阻塞发生在非主线程（anyio portal / 事件循环的默认线程池 worker）——
+#      用例会红，但那个线程可能仍在跑，清理阶段还会等它；
+#   ② 主线程正卡在一段不检查 Python 信号的长 C 调用 —— handler 要等它返回；
+#   ③ 信号落在一段 except BaseException 里 —— 典型是 asyncio 的回调
+#      Handle._run（CPython asyncio/events.py 实测捕获的就是 BaseException）：
+#      pytest.fail() 抛的 Failed 的 mro 是 Failed → OutcomeException →
+#      BaseException（实测 issubclass(Failed, Exception) 为 False），
+#      **普通 except Exception 接不住它**，但 except BaseException 会，
+#      于是它可能被事件循环当成「回调里的异常」记账，用例照常通过。
+# 换 thread 方法能覆盖 ①②，代价是整个会话被 os._exit、存档截断 —— 本卡按
+# 「要一份读得出根因的清单」这个目的选了 signal，并把上面三类如实登记。
+#
+# ⚠️ **第四类例外（2026-09-19 人审替代实证补记，与上面三类不同轴）**：
+#   ④ **setup 或 call 一旦失败，本 item 的 teardown 就完全没有超时保护。**
+#      上面三类问的是「信号落到哪里」；这一类是「闹钟根本已经被拆了」。
+#      机制（两条源码路径实读）：任何一相真失败 → _pytest/runner.py 的
+#      check_interactive_exception 为真（无 pdb 闸门）→ 触发
+#      pytest_exception_interact → pytest_timeout 该 hook 调 cancel_timeout()
+#      → setitimer(ITIMER_REAL, 0) + SIGALRM 复位 SIG_DFL；而
+#      timeout_func_only=False 时闹钟只在 pytest_runtest_protocol 上一次弦，
+#      **从不重新上弦**。
+#      实证（scratchpad A/B，--timeout=1 + 20s finalizer）：
+#        A 先 assert False → 墙钟 21s、输出里 Timeout 字样 **0**、`1 failed in 20.13s`；
+#        B 同样 finalizer 但 assert True → 墙钟 2s、`Failed: Timeout (>1.0s)`。
+#      本仓当下即可达：unit 开工基线 32 条 FAILED，而标定 N 用的正是
+#      teardown 217s 那批用例 —— 它们一旦在 call 相红，teardown 就裸跑。
+#      ⇒ 「全量跑法不再挂死」这个目标，对**已失败**的 item 本配置给不出保证。
+#      第 5 条门测的探针只 time.sleep、挂之前从不失败，接不住这一类。
+#      登记不阻断（属 DEBT-3 面：超长 teardown 的根因治理）。
+#
+# ⚠️ 本卡实测到的只有一件事：**主线程里的同步 time.sleep 会按时被打断、判红、
+# 进程退出**（test_timeout_kills_hung_test）。上面三类都**没有实测**，
+# 它们是读 pytest-timeout 与 CPython 源码得到的边界声明，不是观测结论。
+#
+# 默认门（本卡定义，⛔ 故意不写进 addopts）：
+#   pytest tests --ignore=tests/integration --ignore=tests/e2e
+#          -m "not integration and not e2e and not contract"
+# 不进 addopts 的理由：addopts 会改掉所有车道每一次目录级跑法的选择集，
+# 连既有红基线的口径一起改掉。默认门是一条【跑法】，不是全局默认值。
+# 表达式里那三个 marker 由 tests/conftest.py 的 pytest_collection_modifyitems
+# 按目录自动补，不依赖各文件手写 pytestmark。
+#
+# 依赖 pytest-timeout==2.4.0，2026-09-18 装进共享 venv
+# （card-v5-lance/backend/.venv，11 条车道共用）。
+# 授权依据：第十五批开跑手册 §零.7「批中禁装工具…**唯一例外 P9-B DEBT-1 装
+# pytest-timeout**」——装包本身是本批点名的例外。
+# ⚠️ **更正（2026-09-19 人审替代）**：原文写「经协议 §2.3 批级通告 + 主 session
+# 批准后」。实测手册 §零 里**带时刻的通告行 0 命中**，且手册 mtime
+# 2026-09-18 00:52:49 早于装包 19:58:28 ⇒ 「批级通告」那半句在共享手册上
+# 得不到印证。手册是主干树资产、车道只读，补那一行是主 session 的活（已登台账）。
+#
+# ⚠️ **保护面只覆盖这个共享 venv**：backend/requirements.txt 里**没有**
+# pytest-timeout（:143-147 只有 pytest/asyncio/cov/xdist/mock）。所以
+# .github/workflows/test.yml 按 requirements 装出来的 CI 环境**没有任何
+# 超时保护**，只会对这两个键各打一条 PytestConfigWarning。新车道自建 venv 同理。
+# 补进 requirements.txt 不是本卡地盘（硬边界禁改），已登台账交 DEBT-4。
+#
+# 没装这个插件时这两个键会怎样：**在本卡实测过的那种调用方式下**只发
+# PytestConfigWarning: Unknown config option，照常跑完、红集不变、rc 不变
+# （实测存档 evidence-debt1/census-control-rootfiles-20260918T204620.txt:1801,1806，
+# 用 -p no:timeout 关掉插件复现）。
+# ⚠️ 这**不是**无条件的：加 `-o strict_config=true`，或把 PytestConfigWarning
+# 升成错误（`-W error::pytest.PytestConfigWarning`），未知 ini 键**可以**变成失败。
+# 另：`--strict-markers` 管的是**未注册 marker**，不管未知 ini 键 —— 拿它当依据
+# 是不充分的（Codex round-1/2 MEDIUM 更正）。
+timeout = 300
+timeout_method = signal
diff --git a/backend/tests/conftest.py b/backend/tests/conftest.py
index 3c87f591..5686be19 100644
--- a/backend/tests/conftest.py
+++ b/backend/tests/conftest.py
@@ -1032,3 +1032,73 @@ def mock_agent_service():
     mock._trigger_memory_write = AsyncMock()
     mock._call_gemini_api = AsyncMock(return_value="mock gemini response")
     return mock
+
+
+# ============================================================================
+# 按目录自动补 marker —— 「默认门」的地基
+# [BATCH-2026-09-18-第十五批 / CARD-DEBT-1]
+# ============================================================================
+
+
+def pytest_collection_modifyitems(config, items):
+    """按用例所在的一级目录补 ``contract`` / ``integration`` / ``e2e`` marker。
+
+    **默认门**（本卡定义，理由写在 ``backend/pytest.ini`` 的注释里，⛔ 不进
+    ``addopts``）::
+
+        pytest tests --ignore=tests/integration --ignore=tests/e2e
+               -m "not integration and not e2e and not contract"
+
+    在这之前这条表达式挡不住多少东西：``tests/integration`` 的 89 个文件里只有
+    27 个手写了 ``pytest.mark.integration``，``tests/e2e`` 的 13 个里只有 4 个写了
+    ``pytest.mark.e2e``，``tests/contract`` 的 6 个里只有 1 个写了
+    ``pytest.mark.contract``（``test_openapi_snapshot_drift.py:36``）。
+    谁新建一个文件忘了写 ``pytestmark``，它就会悄悄混进默认门。有了这个 hook，
+    「放在哪个目录」直接决定 marker。
+
+    ⚠️ **覆盖面如实说（2026-09-19 人审替代更正）**：原文写「忘写不再是一种可能」
+    与「``tests/contract`` 一个都没有」，两句都**过强/失实**：
+
+    - 本 hook 只管这三个目录。``backend/tests`` 下另外 11 个一级目录
+      （api / bdd / benchmark / core / load / performance / regression /
+      security / skills / smoke / unit）与约 25 个顶层 ``test_*.py``
+      一律不打标 —— 例如 ``tests/test_rollback_e2e.py``（顶层、无 pytestmark、
+      名字带 e2e）今天仍在默认门里。
+    - 不是安全洞：这些路径在 W4 里全是 fail-closed，真去连 7691 会被拦红。
+      但「忘写不再是一种可能」这句话**只在这三个目录内成立**。
+
+    **映射恰好三条**，不多不少::
+
+        {"contract": "contract", "integration": "integration", "e2e": "e2e"}
+
+    ⛔ **不打 ``real_neo4j``**，⛔ 不往这三条之外扩目录。理由在 W4：
+    ``tests/support/live_port_guard.py`` 的 ``EXEMPT_MARKERS``
+    = {integration, e2e, real_neo4j} 是「只记不拦」名单，``EXEMPT_PATH_PREFIXES``
+    = ("integration", "e2e") 是同一件事的路径侧。本 hook 打的 ``integration`` /
+    ``e2e`` 只落在**路径上早已豁免**的那两个目录里 ⇒ 对 W4 语义中性；打的
+    ``contract`` 不在 ``EXEMPT_MARKERS`` 里 ⇒ ``tests/contract`` 仍然 fail-closed。
+
+    要往映射里加第四条目录、或改其中任何一个 marker 名之前，**必须回去重核
+    ``EXEMPT_MARKERS``**：往这里写一个豁免 marker，等于悄悄把一批用例从 W4 的
+    拦截面挪进 advisory 面。``tests/unit/test_debt1_default_gate.py`` 的第三条用例
+    把这句话钉成了可执行判据 —— 那里的 marker 表达式由 ``EXEMPT_MARKERS`` 动态
+    拼出来，不是手抄的副本。
+
+    相对化口径与 ``live_port_guard.is_exempt`` 一致：取相对 ``backend/tests`` 的
+    首段目录；相对化失败（rootdir 之外的文件）一律不打 —— 和那边一样 fail-closed，
+    宁可漏打也不错打。
+    """
+    dir_to_marker = {"contract": "contract", "integration": "integration", "e2e": "e2e"}
+    tests_dir = Path(__file__).parent.resolve()
+    for item in items:
+        try:
+            rel = item.path.resolve().relative_to(tests_dir)
+        except Exception:  # noqa: BLE001 —— 相对化失败一律不打，与 is_exempt 同口径
+            continue
+        first = rel.parts[0] if rel.parts else ""
+        marker = dir_to_marker.get(first)
+        if marker is None:
+            continue
+        if item.get_closest_marker(marker) is not None:
+            continue
+        item.add_marker(marker)
diff --git a/backend/tests/unit/test_debt1_default_gate.py b/backend/tests/unit/test_debt1_default_gate.py
new file mode 100644
index 00000000..1c2682b3
--- /dev/null
+++ b/backend/tests/unit/test_debt1_default_gate.py
@@ -0,0 +1,481 @@
+"""CARD-DEBT-1 承重行为门：路径自动打 marker + ini timeout 真的生效。
+
+[BATCH-2026-09-18-第十五批 / CARD-DEBT-1]
+
+这个文件钉住三件**行为**（不是文本）：
+
+1. ``backend/tests/conftest.py`` 末尾的 ``pytest_collection_modifyitems`` 真的按
+   目录给 ``tests/contract`` / ``tests/integration`` / ``tests/e2e`` 打上同名
+   marker —— 于是「默认门」
+   ``-m "not integration and not e2e and not contract"`` 才真的选得干净。
+2. 自动打标**没有扩大 W4 的 advisory 面**。W4
+   （``tests/support/live_port_guard.py``）对
+   ``EXEMPT_MARKERS = {integration, e2e, real_neo4j}`` 只记不拦；本卡打的
+   ``contract`` 不在这个集合里，而 ``integration`` / ``e2e`` 只打到
+   ``EXEMPT_PATH_PREFIXES = ("integration", "e2e")`` 已经豁免的那两个目录上
+   ⇒ 对 W4 语义中性。**⚠️ 这句话只在路径保持稳定时成立**：hook 在收集期按
+   ``resolve()`` 的结果打 marker，W4 在运行期才判豁免；两个时刻之间若软链改指，
+   marker 会先于路径判定生效（Codex round-1/2 MEDIUM，登记不改，见验收单台账 ⑪）。
+   第 3 条用例把这句话变成可执行判据，**四层**，每层堵上一层接不住的那个变异
+   （分工表见该用例的 docstring）。
+3. ``backend/pytest.ini`` 的 ``timeout`` / ``timeout_method`` 真的被
+   ``pytest-timeout`` 读到（第 4 条）；一个**在主线程里同步阻塞**的用例到点会被
+   判红、会话继续往下走（第 5 条）。⚠️ 第 5 条**不**证明超时能终止任意挂起 ——
+   signal 方法只是在主线程 ``pytest.fail()``，不杀线程 / executor / 进程，
+   覆盖面与三类例外写在该用例的 docstring 与 ``backend/pytest.ini`` 的注释里。
+
+⛔ 实现约束（卡文 §一(g)）：每条用例都用 ``subprocess`` 起**真的 pytest 子进程**
+真收集 / 真超时——不用 ``pytester``（那需要在根 conftest 注册插件，越出本卡目的），
+不 mock ``subprocess``，不 monkeypatch pytest 内部。所有子进程都只做收集或跑一个
+本地 ``time.sleep``，不连任何数据库、不碰 live vault。
+"""
+
+from __future__ import annotations
+
+import ast
+import os
+import re
+import subprocess
+import sys
+import time
+from pathlib import Path
+
+import pytest
+
+from tests.support.live_port_guard import EXEMPT_MARKERS, EXEMPT_PATH_PREFIXES
+
+#: ``backend/`` 的绝对路径。本文件位于 ``backend/tests/unit/``，往上两级。
+BACKEND_ROOT = Path(__file__).resolve().parents[2]
+
+PYTEST_INI = BACKEND_ROOT / "pytest.ini"
+
+#: 样本文件。选取原则：**本卡的 hook 是它们身上唯一的 marker 来源**——
+#: 手写了 ``pytestmark`` 的文件当样本就没有「先红」（改 conftest 之前就已经绿），
+#: 门会绿在一个与本卡无关的原因上。
+#:
+#: * integration：``sorted(glob("tests/integration/test_*.py"))[0]``，实测
+#:   ``grep -c 'pytest.mark.integration'`` = 0、``grep -c 'from app.main import app'`` = 0。
+#: * e2e：``sorted(...)[0]`` 是 ``test_a11_kg_relevance_e2e.py``，它 :68-69 有手写
+#:   ``pytestmark = [pytest.mark.e2e, ...]`` ⇒ 不合用；取 sorted 序里第一个
+#:   ``pytest.mark.e2e`` = 0 **且** ``from app.main import app`` = 0 的文件
+#:   （不 import app.main 是为了让收集期零 lifespan 副作用）。
+#: * contract / unit：第 1、3 条用例的对照面，两者都没有任何 marker。
+INTEGRATION_SAMPLE = "tests/integration/test_2_5_x_e2e.py"
+E2E_SAMPLE = "tests/e2e/test_epic36_integration.py"
+CONTRACT_SAMPLE = "tests/contract/test_node_id_patterns.py"
+UNIT_SAMPLE = "tests/unit/test_vault_scope_409.py"
+
+#: 单个子进程的硬上限。到这个值还没回来 = ``subprocess.TimeoutExpired`` 把本用例判红，
+#: 而不是让它跟着挂住——本卡的主题就是「不许再挂死」。
+#:
+#: ⚠️ **这个数受 ini 的 ``timeout`` 约束，不能随便调大**：pytest-timeout 罩的是
+#: 整个 item（setup+call+teardown），而本文件里子进程调用最多的一条用例
+#: （:func:`test_integration_e2e_dir_autotagged`，2 个样本 × 2 次跑）会连起
+#: **4 个**子进程。最坏情况 4 × 本值必须 **< ini 的 timeout（300）**，
+#: 否则这道门会在负载下撞上自己装的那个超时 —— 判据反过来咬判据。
+#: 4 × 60 = 240 < 300 ✅。实测单次子进程约 24 秒（`gate-durations` 存档：
+#: 该条用例 4 次共 97.19s），60 秒留了约 2.5 倍余量。
+SUBPROCESS_TIMEOUT_S = 60
+
+#: 第 5 条用例里那个挂住的测试睡多久，以及给它的 CLI ``--timeout`` 值。
+#: 两者要拉开差距，才能区分「到点被打断判红」与「它自己睡完了」。
+HANG_SLEEP_S = 6
+HANG_CLI_TIMEOUT_S = 1
+
+#: 第 5 条的墙钟上限（卡文 §一(g)⑤）。``HANG_SLEEP_S`` 是 6，所以只要实测 < 5
+#: 就排除了「其实是睡满 6 秒自己结束的」这条解释。
+HANG_WALL_CLOCK_LIMIT_S = 5.0
+
+#: 根 conftest 里那张映射的**变量名**。:func:`_hook_dir_marker_map` 按它锚定，
+#: 而不是按「函数体内恰好一个 dict 字面量」—— 后者既挡不住「抽到的不是 hook 真用的
+#: 那张」，也会因为 hook 里多一个无关局部 dict 就红在一条与 W4 无关的断言上。
+MAP_VAR = "dir_to_marker"
+
+#: 卡文钉死的「映射恰三条」。这一条同时是第 2、3 层「期望空集」判据的**非空前提**：
+#: 映射若变成 ``{}``，那两层会全部空洞变绿。
+EXPECTED_DIRS = {"contract", "integration", "e2e"}
+
+
+def _run_pytest(*args: str, timeout: int = SUBPROCESS_TIMEOUT_S) -> subprocess.CompletedProcess:
+    """在 ``backend/`` 下起一个真的 pytest 子进程。
+
+    ``PYTEST_ADDOPTS`` 被清掉：它是进程外注入的参数，留着会让这道门的选择集
+    取决于调用者的 shell 环境（判据的环境是判据的一部分）。
+    ``PYTHONDONTWRITEBYTECODE`` 避免子进程往工作树写 ``__pycache__``。
+    """
+    env = dict(os.environ)
+    env.pop("PYTEST_ADDOPTS", None)
+    env["PYTHONDONTWRITEBYTECODE"] = "1"
+    return subprocess.run(
+        [sys.executable, "-m", "pytest", *args],
+        cwd=str(BACKEND_ROOT),
+        capture_output=True,
+        text=True,
+        timeout=timeout,
+        env=env,
+    )
+
+
+#: 收集用参数。``--override-ini=addopts=`` 不是可有可无的：
+#: ``backend/pytest.ini:19-21`` 的 ``addopts = -v --tb=short`` 会把 CLI 的 ``-q``
+#: 抵消成 verbosity=0，``--collect-only`` 于是打**树形**（``<Function ...>``）而不是
+#: nodeid 行 —— 那样 :func:`_nodeid_lines` 恒返回空列表，「0 条」的断言会
+#: **恒真**（空洞判据），「≥1 条」的断言会恒假。实测（本卡先红存档
+#: ``gate-before-20260918T194620.txt``）：不加 override 时 nodeid 行 = 0，
+#: 加了 = 50。清掉 addopts 只去掉两个显示项，不改选择集。
+#: 这也是仓内 ``.claude/hooks/post-tool-router.sh`` 用的同一招。
+COLLECT_ARGS = ("--collect-only", "-q", "-p", "no:cacheprovider", "--override-ini=addopts=")
+
+
+def _nodeid_lines(stdout: str) -> list[str]:
+    """``--collect-only -q`` 的输出里，哪几行是真的 nodeid。
+
+    只认「行首就是 ``tests/`` 且含 ``::``」——W4 的汇总行、warning 摘要、
+    统计行都不满足，不会被算成收集到的用例。
+    """
+    return [ln for ln in stdout.splitlines() if ln.startswith("tests/") and "::" in ln]
+
+
+def _fail_msg(label: str, proc: subprocess.CompletedProcess) -> str:
+    return f"{label}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
+
+
+def _assert_deselected_not_broken(proc: subprocess.CompletedProcess, what: str) -> None:
+    """断言「一条都没选中」是**因为被 deselect**，而不是因为收集塌了。
+
+    ⚠️ 为什么需要这一层：下面几处断言的形状是 ``_nodeid_lines(...) == []``。
+    一个**收集出错**的子进程同样一条 nodeid 都不打 —— 它会让这些断言绿在
+    「什么都没收集到」上，而不是绿在「marker 生效、被正确排除」上。
+    验伪锚（另起一个进程、不带 ``-m``）证明的是**那一次**能数出东西，
+    证明不了**这一次**没塌。所以每个「期望 0 条」的判据都必须在**同一次**输出里
+    拿到 deselect 的正面痕迹，并排除内部错误。
+    """
+    out = proc.stdout + proc.stderr
+    for bad in ("INTERNALERROR", "error during collection", "errors during collection"):
+        assert bad not in out, _fail_msg(f"{what}：子进程收集出错（命中 {bad!r}）", proc)
+    # ⛔ **正面白名单**，不是「排除 3 和 4」（Codex round-2 MEDIUM）：黑名单挡不住
+    # 中断（2）、也挡不住被信号杀死的负数 rc。一次 `--collect-only` 的正常结局只有两种：
+    # 0 = 收集到了东西，5 = 一条都没收集到。其余一律不是「正常的收集结果」。
+    assert proc.returncode in (0, 5), _fail_msg(
+        f"{what}：子进程 rc={proc.returncode}，不在 `--collect-only` 的正常结局 {{0, 5}} 内"
+        "（2=中断 / 3=内部错误 / 4=用法错误 / 负数=被信号杀死）。",
+        proc,
+    )
+    assert "deselected" in out, _fail_msg(
+        f"{what}：输出里没有 `deselected` —— 「0 条被选中」没有正面证据，不能排除它其实是收集塌了。",
+        proc,
+    )
+
+
+def _ini_timeout_value() -> float:
+    """从 ``backend/pytest.ini`` 文本里解析 ``timeout`` 的值。
+
+    故意读文本而不是读 ``config.getini``：这道门要验的就是「ini 里写的那个数
+    真的传到了插件」，两侧必须来自不同的读法，否则是同一个来源自证自己。
+    """
+    text = PYTEST_INI.read_text(encoding="utf-8")
+    m = re.search(r"^timeout\s*=\s*([0-9.]+)\s*$", text, re.MULTILINE)
+    assert m is not None, f"backend/pytest.ini 里没有顶层 `timeout = <N>` 行：\n{text}"
+    return float(m.group(1))
+
+
+def test_contract_dir_autotagged() -> None:
+    """``tests/contract`` 下的用例被自动打上 ``contract``。
+
+    没有 hook 时 ``-m "not contract"`` 一条也不排除 ⇒ 第一条断言（deselected）
+    就是本用例的红点。
+    """
+    excluded = _run_pytest(*COLLECT_ARGS, "-m", "not contract", CONTRACT_SAMPLE)
+    assert "deselected" in excluded.stdout, _fail_msg(
+        f"`-m 'not contract'` 对 {CONTRACT_SAMPLE} 没有 deselect 任何用例："
+        "根 conftest 的 pytest_collection_modifyitems 没有给 contract 目录打 marker。",
+        excluded,
+    )
+    assert _nodeid_lines(excluded.stdout) == [], _fail_msg(
+        f"`-m 'not contract'` 之后 {CONTRACT_SAMPLE} 仍有用例被选中。", excluded
+    )
+    _assert_deselected_not_broken(excluded, f"`-m 'not contract'` on {CONTRACT_SAMPLE}")
+
+    included = _run_pytest(*COLLECT_ARGS, "-m", "contract", CONTRACT_SAMPLE)
+    assert len(_nodeid_lines(included.stdout)) >= 1, _fail_msg(
+        f"`-m contract` 在 {CONTRACT_SAMPLE} 上零收集（rc=5 不是绿）。", included
+    )
+
+
+def test_integration_e2e_dir_autotagged() -> None:
+    """``tests/integration`` / ``tests/e2e`` 下的用例被自动打上同名 marker。
+
+    两个样本都实测没有手写 ``pytestmark``，所以这里绿只可能是 hook 打的。
+    只做 ``--collect-only``：这两个目录里有文件在 import 期 ``from app.main
+    import app``，执行它们会真起 lifespan（W4 对它们只记不拦）。
+
+    ⚠️ 不用 ``parametrize``：本文件的收集数是卡文的判据之一（应为 5），
+    参数化会把它变成 6。
+    """
+    for sample, marker in ((INTEGRATION_SAMPLE, "integration"), (E2E_SAMPLE, "e2e")):
+        included = _run_pytest(*COLLECT_ARGS, "-m", marker, sample)
+        assert len(_nodeid_lines(included.stdout)) >= 1, _fail_msg(
+            f"`-m {marker}` 在 {sample} 上零收集：目录自动打标没生效。", included
+        )
+
+        excluded = _run_pytest(*COLLECT_ARGS, "-m", f"not {marker}", sample)
+        # 先断言不变量、再上防空洞守卫（顺序理由见第 3 条用例第 4 层处的注释）
+        assert _nodeid_lines(excluded.stdout) == [], _fail_msg(
+            f"`-m 'not {marker}'` 之后 {sample} 仍有用例被选中。", excluded
+        )
+        _assert_deselected_not_broken(excluded, f"`-m 'not {marker}'` on {sample}")
+
+
+def _hook_dir_marker_map() -> dict:
+    """从根 conftest 的源码里把 hook 那张目录→marker 映射**读出来**。
+
+    用 AST 取函数体内的 dict 字面量，不 import conftest（import 它会拖起整条
+    ``app.main`` 链）。也不在这里手抄一份副本 —— 手抄的两份清单必然漂移。
+    """
+    src = (BACKEND_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
+    tree = ast.parse(src)
+    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "pytest_collection_modifyitems"]
+    assert len(fns) == 1, f"根 conftest 里 pytest_collection_modifyitems 应恰 1 个，实得 {len(fns)}"
+
+    # ⛔ **按名字锚定 `dir_to_marker` 的那次赋值**，不是「函数体内恰好一个 dict 字面量」。
+    # 后者有两个毛病：① hook 体内将来多一个无关的局部 dict（比如一个缓存）就会红在
+    # 一条与 W4 毫无关系的断言上；② 它也不保证抽到的那个 dict **就是 hook 真正用的
+    # 那张映射**。锚在赋值目标的名字上，两个毛病一起消失。
+    assigns = [
+        n
+        for n in ast.walk(fns[0])
+        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == MAP_VAR for t in n.targets)
+    ]
+    assert len(assigns) == 1, (
+        f"hook 体内应恰有 1 处 `{MAP_VAR} = ...` 赋值，实得 {len(assigns)}。\n"
+        "这道门按名字锚定那张映射。如果它被改名、搬到模块级、或被多次赋值，"
+        "请同步改这里 —— 而不是让门去猜哪个 dict 才是它。"
+    )
+    node = assigns[0].value
+    assert isinstance(node, ast.Dict), (
+        f"`{MAP_VAR}` 的右侧不是 dict 字面量，而是 {type(node).__name__}。\n"
+        "这道门只看得懂字面量（例如换成 dict(...) 调用或 {**BASE, ...} 之后就看不懂了）。"
+    )
+
+    # ⛔ 解析不了的条目必须**当场拒绝**，不能静默跳过（Codex round-2 MEDIUM）：
+    # 原来的写法是 `if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)`
+    # —— 一条 `"regression": "real_" + "neo4j"` 在运行时确实会打 `real_neo4j`，
+    # 但它的 value 是 ast.BinOp 不是 ast.Constant，于是被过滤掉、下面三层全部看不见它。
+    # 「我只检查我看得懂的那部分」就是一道抽出了安全子集的门。
+    #
+    # ⚠️ `ast.dump(None)` 会抛 `TypeError: expected AST, got 'NoneType'`（实测）——
+    # 而 `{**other}` 这种解包在 `d.keys` 里**就是 None**。所以这里不能直接 dump：
+    # 那会让「我这条断言声称自己管解包」变成「它先崩在 dump 上」。
+    def _show(n):
+        return "**解包（keys 里是 None）**" if n is None else ast.dump(n)
+
+    unresolved = [
+        (_show(k), _show(v))
+        for k, v in zip(node.keys, node.values)
+        if not (isinstance(k, ast.Constant) and isinstance(v, ast.Constant))
+    ]
+    assert unresolved == [], (
+        f"hook 的映射里有**静态解析不了**的条目：{unresolved}\n"
+        "这道门只能检查字面量键值对。出现拼接 / 变量 / 解包之后，下面几层不变量就看不见它了 —— "
+        "所以这里直接拒绝，而不是跳过。要么把它写成字面量，要么给这道门补一条能看懂它的判据。"
+    )
+
+    mapping = {k.value: v.value for k, v in zip(node.keys, node.values)}
+    # ⛔ 非空 + 恰好是卡文钉死的那三条。缺了这一条，下面「期望空集」的第 2、3 层
+    # 会在映射变成 `{}` 时**全部空洞变绿**（期望 0 的判据必须先证输入面非空）。
+    assert set(mapping) == EXPECTED_DIRS, (
+        f"hook 的映射目录集变了：实得 {sorted(mapping)}，期望 {sorted(EXPECTED_DIRS)}。\n"
+        "卡文钉死「映射恰三条」。要加第四条，必须先回去重核 EXEMPT_MARKERS "
+        "（理由见本文件第 3 条用例的 docstring），然后同步改这里。"
+    )
+    return mapping
+
+
+def test_autotag_does_not_widen_w4_exempt_markers() -> None:
+    """自动打标既没有扩大 W4 的豁免面，也没有把 marker 打到别的目录上。
+
+    这条用例有**四层**，每一层堵的是**上一层接不住的那个变异**。
+    第二层是 Codex round-1 的 MEDIUM 整改补的，第三、四层是送审前一轮内部对抗
+    复核抓出来的（那轮指出：前两层对 ``contract`` 这一个 marker 零覆盖）。
+
+    | 层 | 断言 | 它堵住的变异 | 前面几层为什么接不住 |
+    |---|---|---|---|
+    | 1 行为 | ``-m '<EXEMPT_MARKERS 拼出的表达式>'`` 在 unit / contract 两个样本上选中 0 条 | 把豁免 marker 打到这两个目录上 | —— |
+    | 2 结构 | 映射里凡 marker ∈ ``EXEMPT_MARKERS``，其目录必须已在 ``EXEMPT_PATH_PREFIXES`` | ⛔ **本层已不可达**，见下 | 第 1 层根本不收集 ``tests/regression`` |
+    | 3 结构 | 映射里每条都必须**目录名 == marker 名** | ``{"e2e": "contract"}``（键集不变）| ``contract`` **不在** ``EXEMPT_MARKERS`` 里，第 2 层的过滤直接跳过它 |
+    | 4 行为 | ``-m contract`` 在 unit 样本上选中 0 条 | ``dir_to_marker.get(first, "contract")`` | 第 3 层读的是 dict 字面量，而这个变异改的是 ``.get()`` 的默认值 |
+
+    第 3、4 层堵的那类变异后果最重：``contract`` 被打到 ``tests/unit`` 上之后，
+    默认门的 ``-m "... and not contract"`` 会把整个 ``tests/unit`` **静默**排除
+    —— **本文件自己也在 tests/unit 里，会跟着一起消失**，而成绩单只是少了几千条
+    passed，一条红都没有。
+
+    ⚠️ **第 2 层在当前顺序下不可达（2026-09-19 人审替代实证，如实降级）**：
+    :func:`_hook_dir_marker_map` 末尾的 ``set(mapping) == EXPECTED_DIRS`` 把键集
+    钉死成三条之后，能违反第 2 层的输入只剩 ``contract`` 映到某个豁免 marker
+    —— 而第 1 层跑的正是 ``EXEMPT_MARKERS`` 全集、样本里就有一个
+    ``tests/contract/`` 下的文件，必被它先抓走。枚举「键集恒等、值取自
+    {contract, integration, e2e, real_neo4j, other}」的全部 125 组合：
+    最先红在 L1 的 75 种 / L3 的 49 种 / 全绿 1 种 / **L2 = 0 种**。
+    实测三段（还原逐字节同）：加第 4 个键 → 红在 ``set(mapping)``；
+    ``contract → real_neo4j``（键集不变）→ 红在第 1 层；
+    ``e2e → contract``（键集不变）→ 红在第 3 层。
+    ⇒ 第 2 层现为**纵深防御**，不是被独立验证过的门；只有当 W4 的
+    ``EXEMPT_PATH_PREFIXES`` 缩小时它才重新可达。**不在本卡改**（改判据顺序
+    要动已绑定的代码），修法建议与登记见验收单 §五（台账 11b）。
+
+    ⚠️ **这条用例在两段负控下的表现，如实写明**：
+    - 段②（删 ini 的 ``timeout`` 行）下它仍绿 —— 是**控制组**。
+    - 段①（删掉整个 hook）下它**会红**，但红在 :func:`_hook_dir_marker_map` 的
+      「应恰 1 个」上 —— 那是**取证前提不成立**（映射根本不存在了），
+      不是「不变量被推翻」。它不是段① 的指定红点；段① 的指定红点是第 1、2 条用例。
+    """
+    # ── 第一层：行为 ────────────────────────────────────────────────────────
+    # 验伪锚：这条断言期望「0 条」，所以必须先证明「同一对样本、同一条提取
+    # 口径下，不加 -m 是能数出东西的」——否则输出格式一变（例如 addopts 改了
+    # verbosity）它就恒真，变成一道什么都不测的门。
+    anchor = _run_pytest(*COLLECT_ARGS, UNIT_SAMPLE, CONTRACT_SAMPLE)
+    assert len(_nodeid_lines(anchor.stdout)) >= 1, _fail_msg(
+        f"验伪锚失败：不加 -m 时 {UNIT_SAMPLE} / {CONTRACT_SAMPLE} 也数出 0 条 nodeid，"
+        "说明提取口径没对上输出格式，下面那条『0 条』的断言是空洞的。",
+        anchor,
+    )
+
+    expr = " or ".join(sorted(EXEMPT_MARKERS))
+    proc = _run_pytest(*COLLECT_ARGS, "-m", expr, UNIT_SAMPLE, CONTRACT_SAMPLE)
+    assert _nodeid_lines(proc.stdout) == [], _fail_msg(
+        f"`-m '{expr}'`（W4 豁免 marker 全集）在 {UNIT_SAMPLE} / {CONTRACT_SAMPLE} 上"
+        "选中了用例 = W4 的 advisory 面被自动打标扩大了。",
+        proc,
+    )
+    _assert_deselected_not_broken(proc, f"`-m '{expr}'` on {UNIT_SAMPLE} / {CONTRACT_SAMPLE}")
+
+    # ── 第二层：映射本身的结构不变量（与样本文件无关）────────────────────────
+    mapping = _hook_dir_marker_map()
+    widened = {
+        directory: marker
+        for directory, marker in mapping.items()
+        if marker in EXEMPT_MARKERS and directory not in EXEMPT_PATH_PREFIXES
+    }
+    assert widened == {}, (
+        f"映射把 W4 的豁免 marker 发给了路径上尚未豁免的目录：{widened}\n"
+        f"  hook 映射        = {mapping}\n"
+        f"  EXEMPT_MARKERS   = {sorted(EXEMPT_MARKERS)}\n"
+        f"  EXEMPT_PATH_PREFIXES = {sorted(EXEMPT_PATH_PREFIXES)}\n"
+        "这等于把一批用例从 W4 的拦截面悄悄挪进 advisory 面。"
+    )
+
+    # ── 第三层：每条映射必须「目录名 == marker 名」────────────────────────────
+    # 第二层只管 EXEMPT_MARKERS 里那三个 marker。``contract`` **不在**那个集合里，
+    # 所以 ``{"unit": "contract"}`` 这种「把 contract 打到别的目录上」第二层接不住 ——
+    # 而它的后果比扩大 advisory 面更糟：默认门的 `-m "... not contract"` 会把整个
+    # ``tests/unit`` 静默 deselect 掉（本文件自己也在 tests/unit 里，会一起消失），
+    # 成绩单只是少了几千条 passed，不红。
+    mismapped = {d: m for d, m in mapping.items() if d != m}
+    assert mismapped == {}, (
+        f"映射里有「目录名 != marker 名」的条目：{mismapped}\n"
+        f"  hook 映射 = {mapping}\n"
+        "本 hook 的契约是「按一级目录补**同名** marker」。把某个目录映到别的 marker 上，"
+        "会让默认门的 -m 表达式排除掉一整个本该跑的目录，而且不会红。"
+    )
+
+    # ── 第四层：行为侧兜住 ``.get()`` 的默认值 ────────────────────────────────
+    # 第三层读的是 dict 字面量。若有人把 ``dir_to_marker.get(first)`` 改成
+    # ``dir_to_marker.get(first, "contract")``，字面量没变、前三层全绿，
+    # 但**每个**目录都会拿到 contract。这里直接问一句：unit 样本有没有拿到 contract？
+    unit_as_contract = _run_pytest(*COLLECT_ARGS, "-m", "contract", UNIT_SAMPLE)
+    # ⚠️ 顺序要紧：**先断言不变量，再上防空洞守卫**。
+    # 守卫的职责是「当结果确实是 0 条时，区分『被正确排除』与『收集塌了』」。
+    # 把它放在前面会让「marker 被打多了」这个变异红在守卫上，而守卫的文案说的是
+    # 「不能排除收集塌了」—— 与事实（其实是全被选中）相反，归因会被带偏一整轮。
+    assert _nodeid_lines(unit_as_contract.stdout) == [], _fail_msg(
+        f"`-m contract` 在 {UNIT_SAMPLE} 上选中了用例 —— `contract` marker 被打到了 "
+        "tests/contract 之外。默认门会因此把这个目录整个排除掉，而且不会红。",
+        unit_as_contract,
+    )
+    _assert_deselected_not_broken(unit_as_contract, f"`-m contract` on {UNIT_SAMPLE}")
+
+
+def test_ini_timeout_header() -> None:
+    """``backend/pytest.ini`` 的 ``timeout`` / ``timeout_method`` 真的传到了插件。
+
+    判据取插件自己打印的 report header（``pytest_report_header``）——那是插件
+    **实际生效的设置**，不是我们再读一遍 ini。故意不带 ``-q``：``-q`` 会把
+    header 整段吞掉。
+    """
+    pytest.importorskip("pytest_timeout")
+    proc = _run_pytest(
+        "-c",
+        "pytest.ini",
+        "--rootdir",
+        ".",
+        "--collect-only",
+        "-p",
+        "no:cacheprovider",
+        CONTRACT_SAMPLE,
+    )
+    m = re.search(r"^timeout: ([0-9.]+)s", proc.stdout, re.MULTILINE)
+    assert m is not None, _fail_msg(
+        "pytest-timeout 没有打出 `timeout: <N>s` header：backend/pytest.ini 的 timeout 值没有被读到。",
+        proc,
+    )
+    assert float(m.group(1)) == _ini_timeout_value(), _fail_msg(
+        f"header 里的 timeout={m.group(1)}s 与 backend/pytest.ini 文本里的 timeout={_ini_timeout_value()} 不一致。",
+        proc,
+    )
+    assert re.search(r"^timeout method: signal", proc.stdout, re.MULTILINE) is not None, _fail_msg(
+        "header 里的 timeout method 不是 signal。", proc
+    )
+
+
+def test_timeout_kills_hung_test(tmp_path: Path) -> None:
+    """一个在**主线程里同步阻塞**的用例，到点会被判红、会话继续往下走。
+
+    被测文件写在 ``tmp_path``：pytest 从参数路径往上找不到任何 ini，rootdir 就
+    落在 tmp 里 ⇒ **根 conftest 不会被加载**，这个子进程零网络、零 fixture，
+    只剩「sleep 6 秒 vs --timeout=1」这一件事。
+
+    ⚠️ **这条证明什么、不证明什么**（Codex round-1 HIGH 整改，别把它读宽）：
+
+    - 证明：主线程的同步阻塞（这里是 ``time.sleep``）会被 ``SIGALRM`` 打断，
+      用例在 1 秒处判红、进程在 ``HANG_WALL_CLOCK_LIMIT_S`` 内退出。
+    - **不证明**：超时能**终止**任意挂起。``pytest-timeout`` 的 signal handler
+      做的是在主线程 ``pytest.fail()``，它**不杀线程、不杀 executor、不杀进程**。
+      于是至少三类输入不在本条覆盖面内：
+        ① 阻塞发生在非主线程（portal / executor worker）—— 用例会红，
+           但那个线程可能仍在跑，清理阶段还会等它；
+        ② 主线程正卡在一段不检查 Python 信号的长 C 调用 —— handler 要等它返回；
+        ③ 信号落在一段 ``except BaseException`` 里 —— 典型是 asyncio 的回调
+           ``Handle._run()``（CPython ``asyncio/events.py`` 实测捕获
+           ``BaseException``）。``pytest.fail()`` 抛的 ``Failed`` 的 mro 是
+           ``Failed → OutcomeException → BaseException``（实测
+           ``issubclass(Failed, Exception)`` 为 **False**），所以**普通
+           ``except Exception`` 接不住它**，但 ``except BaseException`` 会 ——
+           那时它会被事件循环当成「回调里的异常」记账，用例照常通过。
+      这三类**本卡都没有实测**，是读插件与 CPython 源码得到的边界声明；
+      登记见验收单「本卡未证明什么」。
+    """
+    pytest.importorskip("pytest_timeout")
+    hung = tmp_path / "test_debt1_hang_probe.py"
+    hung.write_text(
+        f"import time\n\n\ndef test_sleeps_longer_than_the_timeout():\n    time.sleep({HANG_SLEEP_S})\n",
+        encoding="utf-8",
+    )
+
+    started = time.monotonic()
+    proc = _run_pytest(
+        "-p",
+        "no:cacheprovider",
+        f"--timeout={HANG_CLI_TIMEOUT_S}",
+        "-q",
+        str(hung),
+        timeout=60,
+    )
+    elapsed = time.monotonic() - started
+
+    assert proc.returncode == 1, _fail_msg(f"挂住的用例没有被判红（rc={proc.returncode}）。", proc)
+    assert "Timeout" in proc.stdout + proc.stderr, _fail_msg("输出里没有 Timeout 字样：红的原因不是超时。", proc)
+    assert elapsed < HANG_WALL_CLOCK_LIMIT_S, _fail_msg(
+        f"墙钟 {elapsed:.2f}s ≥ {HANG_WALL_CLOCK_LIMIT_S}s：不能排除「它其实睡满了 {HANG_SLEEP_S}s 自己结束」。",
+        proc,
+    )
```

## ② 作者自述 —— 以下每一条请独立核对，不要采信

1. **自动打标恰三条，且对 W4 语义中性**：映射 `{"contract": "contract", "integration": "integration", "e2e": "e2e"}`，不含 `real_neo4j`；`live_port_guard.EXEMPT_MARKERS` = {integration, e2e, real_neo4j}（只记不拦名单），`EXEMPT_PATH_PREFIXES` = ("integration", "e2e")；本卡打的 integration/e2e 只落在路径早已豁免的那两个目录，contract 不在豁免名单 ⇒ 我声称 advisory 面没有变宽。
2. **`addopts` 未动**：`backend/pytest.ini:19-21` 与 `a7341ca4` 逐字同；`-m` 默认门没有写进 addopts。
3. **timeout 值有 durations 存档支撑**：N=300 取自开工 `tests/unit --durations=25`（`unit-open-20260918T192142.txt`）；最慢**通过**项 teardown 217.38s + call 5.02s ⇒ item 总墙钟 ≈ 222.4s。⚠️ **已收窄**：`timeout_func_only=False` 计时罩整个 item **只对「每一相都通过」的 item 成立**（第四类例外，见 ⓪ 的 HIGH；ini 注释已收窄）。标定按 item 总墙钟、余量仅约 1.35×（已写进未证明清单）。
4. **census 每条结论来自存档**，尤其「contract 目录级挂起**不是** pact provider 等真服务」：`test_pact_provider.py:35-40` 的 `PACT_DIR` 指向不存在的目录、`:43` `PACT_BROKER_URL` 默认空、`:298` skipif 把整个验证类跳过；另有两个探针存档（pact 面 25 passed / 0.55s / rc=0；schemathesis 面 20 分钟被外层砍、rc=124、ini `timeout` 触发过 1 次）。
5. **根 conftest 零删改既有行**：只在文件末追加；`grep -c '^-[^-]'`（conftest 相对 `a7341ca4` 的 diff）= 0。
6. **两段负控各红在指定断言**：段① → **3 failed / 2 passed**（红在 `deselected` 断言）；段② → **1 failed / 4 passed**（红在 header 正则断言）。被我标成**控制组**的（段① 下第 ③ 条、段② 下第 ⑤ 条）如实标注。还原用 `git show HEAD:<path> > <path>`，跑后 sha256 与 HEAD 逐字节相同。
7. **默认门实跑**：有总结行（`147 failed, 9041 passed, 51 skipped, 196 deselected, 18 xfailed in 2831.38s`）；未被外层墙钟砍；`deselected = 196` 与 `tests/contract` 收集数 196 相等。⚠️ 墙钟 **47 分 33 秒，未达 ≤20 分钟目标**（如实登记，卡在 unit ≈17 分 + regression ≈15-19 分）。
8. **D-32 纯注释整改（`9d270cdf`）**：`pytest.ini` 非注释行 diff 为空、`configparser` 解出的有效配置 9 键全同（`timeout=300` / `timeout_method=signal` / `addopts` 原值）；两份 `.py` 去 docstring 后 `ast.dump` 与 `47c94bab` 相同（验伪锚 `x=1` vs `x=2` → False）；整改后复跑门 5 passed。
9. **人审裁定的处置**：1 HIGH「只改声明不改行为」（声明侧注释收窄 + 行为侧登记 DEBT-3）；7 MEDIUM 全部登记不阻断（含 AST 三层只看字面量可被 `.update()` 绕 · `_run_pytest` 未清 `PYTEST_TIMEOUT`（env 优先于 ini）· 第①层缺「表达式有选中能力」正控 · `pytest-timeout` **不在** `backend/requirements.txt` ⇒ CI 零超时保护 · `stop-test-runner.js` 的 `-m "not integration"` 选择集被本卡静默改小 · §2.3 通告行没落到共享手册 · 承重存档未落 shasum）。

## ③ 请优先回答的问题（按重要性排序）

⓪ **自动打标有没有让 `tests/integration` / `tests/e2e` 之外的任何用例拿到 `integration` / `e2e` / `real_neo4j` 中的任何一个 marker？**（= W4 的 advisory 面有没有被这次改动扩大）如果有**门未覆盖的路径**能做到（软链、`rootdir` 之外的用例、conftest 加载顺序导致 hook 不执行、别处还有一个 `pytest_collection_modifyitems` 与它叠加），请指出那条路径。

① `timeout_method = signal` 在 `asyncio_mode = auto` + anyio portal 线程的组合下，会不会把「超时」显示成**别的失败**（= 假归因），或者对 C 级阻塞根本杀不掉（= 门绿了但东西还挂着）？请说明在什么**对照输入**下这两种情况会发生。

② `hang-census.md` 里每一条的根因，是从存档读出来的还是推断出来的？特别是「不是 pact」这一条，以及 contract 目录的慢（人审已改为 schemathesis 探针证据 + `blocked=19` 归 `test_health_contract`）——如果证据只支持更弱的说法，请指出该弱到什么程度。

③ 默认门的 `-m "not integration and not e2e and not contract"` 有没有让**本来在跑的用例静默消失**？`deselected` 数与 `tests/contract` 的收集数是否对得上？如果有用例既不在 contract 目录、又被这条表达式排除掉了，请指出是哪一条以及为什么。

④ 新加的两个 ini 键，在**没装这个插件**的 venv（主仓 venv、CI）里是警告还是失败？验收单里那句「只警告不致错」有没有如实写、依据够不够（我给的是全仓没有 `--strict-config` / `--strict-markers`）？

⑤ 两段**负控输入**（段① 删掉 hook、段② 删掉 ini 的 `timeout` 行）是不是各自红在了我指定的那条断言上？被我标成**控制组**（删了也不该红）的那两条，标注是否属实？有没有哪一条断言其实在**未被拦下的输入**上也会绿？

⑥（补审追加）**对 `9d270cdf` 的 D-32「纯注释等价」证明**是否严密（有没有行为性改动藏进「注释」）？**人审裁定的 1 HIGH / 7 MEDIUM 的处置**（尤其「只改声明不改行为」）是否可接受、7 条 MEDIUM 里有没有实际是 HIGH 的？以及以上全部内容里**上述审查都没覆盖到的面**。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 一句话结论
- `file:line`（精确到行）
- 一句复现思路，措辞请用「**负控输入** / **对照输入** / **未被拦下的输入** / **门未覆盖的路径**」

如果某条只是风格或偏好，请标 LOW 并说明它不影响正确性。

## ⑤ 边界

- **只读**，不要修改任何文件；不要试图运行命令（你的工具面里 Bash 不可用）。
- 不要连接任何数据库、不要起容器、不要跑需要网络的东西。
- 不要评审 DEBT-2（xdist 收集不确定性）、DEBT-3（挂起用例本身怎么修）、DEBT-4（CI 与依赖声明）的面——本卡对它们只登记不改。
- 不要评审 `backend/tests/support/live_port_guard.py` 的**改动**：那是上一张卡 P9-A 的面，本卡对它零改动，只把它当对照常量读。
- 不要评审 `backend/app/**`：本卡不触它。
