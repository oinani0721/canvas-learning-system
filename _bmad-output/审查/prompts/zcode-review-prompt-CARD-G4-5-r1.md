# ZCode 补审 prompt — CARD-G4-5（r1 · GLM-5.3 · 协议 §2.4.2）

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage` · 卡 `CARD-G4-5`（semantic episode 写读组对称：组族收敛到单一 builder）
> 补审通道（协议 §2.4.2）：GLM-5.3 × ZCode CLI · `--mode build`（只读：Bash/Write 被禁，Read 可用）
> 审查绑定：`bbd2a9fb`（代码终态；HEAD `c33240fa` 与其差异仅在 `_bmad-output/` 文档面；四个卡文件自 `bbd2a9fb` 后零改动）
> 送审时间：2026-09-19 · 生成：车道 card-p1-storage（自动生成，供只读评审）

（本文件为自包含送审包：五节指令 + 末尾内嵌完整变更集。你的运行环境不能运行 git——一切 git 输出以附录为准。）

---

## ① 背景 + 最小读取面（写死）

**卡要解决的问题**：写侧（`episode_worker.py` 的 add_episode 通道）与读侧（`memory_service.py` 的 Tier 1 与 legacy 两条 Graphiti 检索路径）此前**各自手拼**同一条组规则 `[本组, 影子组]`（影子组 = `semantic_group_id(...)` 语义影子图）。三处手拼没有任何机制保证一起修改——哪天有人动了后缀或规范化顺序而只改一处，读侧组集合就不再包含写侧实际写入的组，表现为**检索静默少召回**（无崩溃点）。

**终态改动（= 本 prompt 附录的变更集）**：

1. `group_id_compat.py` 新增两个纯函数：写侧唯一入口 `semantic_write_group`（:145）与读侧静态半边唯一入口 `static_group_family`（:166）；
2. `memory_service.py` 新增 `_read_group_family`（:2022；静态半边 + 动态半边 `_expand_vault_subgroups` 枚举 `本组__*` 子组，去重保序），Tier 1 与 legacy 两处改为调用它；
3. `episode_worker.py` 写侧改为经 `semantic_write_group`（:602）；
4. 新增门 `tests/unit/test_group_family_builder.py`（571 行）：写==读 property（hypothesis）、两路径同构、`_expand_vault_subgroups` 六条行为、AST 常驻门（禁第二处手拼组族）。

卡片此前经内部对抗审查两轮，两条 HIGH（legacy sink 四态、AST 门加宽）均已修复（提交 `622a3626` / `bbd2a9fb`）——你的任务是对修复后的**终态**做一轮独立复核：按 §③ 逐项核实、按 §④ 输出发现清单。

**最小读取面（写死；只读，不修改）**：

- （A）**内嵌变更集**：本文件附录 = `git --no-pager diff --no-color d4c19c06 bbd2a9fb -- backend/app/graphiti/group_id_compat.py backend/app/services/episode_worker.py backend/app/services/memory_service.py backend/tests/unit/test_group_family_builder.py` 全文（+670/−17）。
- （B）树内文件（用 Read；路径相对 cwd）：
  1. `backend/app/graphiti/group_id_compat.py` — 全文件（234 行；重点 `sanitize_group_id_for_graphiti` :69、`semantic_group_id` :121、两个新 builder :145 / :166）
  2. `backend/app/core/vault_scope.py:576-681` — `read_scope_params` :596 / `read_group_filter` :623 / `group_in_read_scope` :650（R4 前缀语义）
  3. `backend/app/services/memory_service.py` — `_search_graphiti` :1788-1937、`_search_graphiti_legacy` :1939-2020、`_read_group_family` :2022-2045、`_expand_vault_subgroups` :2047-2117、四态折算面 :2372-2390 与 :2465-2490
  4. `backend/app/services/episode_worker.py:585-610`（写侧单点）
  5. `backend/tests/unit/test_group_family_builder.py`（571 行，全文件）
  6. `backend/tests/unit/test_group_id_compat.py`（既有契约断言）
  7. `.claude/rules/cypher-read-contract.md:74-76`（R4「⚠️ 前缀语义」段与「已封堵站点（G4-1a）」段）

- 行号为送审时实测；若你读到的行号有漂移，以**符号名**为准。
- 不要求读任何 `_bmad-output/` 文档或其他路径。

## ② 作者自述（请独立核对，勿直接采信）

1. 写侧行为逐字节等价：`semantic_write_group(g)` 就是原链 `semantic_group_id(sanitize_group_id_for_graphiti(g))` 本身；三处既有字面量断言（`canvas-test__semantic` / `vault__cs_61b__semantic` / `math-group__semantic`，见 `test_episode_worker_retry.py` / `test_episode_worker_coverage_epw.py` / `test_s02_entity_types.py`）原样绿。
2. 读侧两路径同构：`_search_graphiti` 与 `_search_graphiti_legacy` 传给 Graphiti 的 `group_ids` **集合相等**，且都等于 `await _read_group_family(gid_phys)`。
3. ⚠️ 终态要点（必须核实）：**legacy 调用刻意不传 `fail_sink`**——与改前逐条同语义；本卡初版曾传 `fail_sink=fail_sink`（该形参绑定硬失败通道 `tier_failures`），经内部对抗审查判为 HIGH-1（实测 `EMPTY → UNAVAILABLE` 四态漂移）后已于 `622a3626` 回退，终态注释在变更集内。请核实：① 回退属实（终态 legacy 的 sink 语义与改前逐条相同）；②「子组枚举失败在 legacy 不可观测」这一既有不同构**仍存在且被如实登记**（其正确修复需动 `CARD-G4-2` 的 sink 管道，属本卡范围外，已移交）。此项为**已知状态**，不要作为新发现重复上报，除非你认为回退本身不正确。
4. `_expand_vault_subgroups` 行为零改动（分页 / 硬上限 / 缓存 / 异常语义），本卡只补测试。
5. R4 前缀语义零改动：`read_group_filter` / `group_in_read_scope` / `_PHYSICAL_SEPARATOR` 一字未动。
6. AST 常驻门当前形态：`semantic_group_id` 在 `group_id_compat.py` 之外的 Call = 0；List/Tuple 字面量含其 Call = 0；f-string / `+` 拼接 / `as` 别名三种形态计入计数；含控制组与 `builder_defs` 非空验伪锚。
7. pyright `app` = 0 errors；本卡零新增 ignore。

## ③ 按重要性排序的问题（逐项给结论）

- ⓪ property 的策略是否真覆盖中文 punycode 段、已物理化形态、已带 `:semantic` 后缀的输入（还是退化成 ASCII 单段族恒等式）？
- ① `static_group_family` 对「输入已是影子组」的去重（只返单元素），是否会让某条读路径少查主组（召回收窄）？
- ② legacy 终态（不传 fail_sink）：回退后与改前逐条同语义是否属实？「枚举失败在 legacy 不可观测」是否被如实登记为未修？
- ③ AST 门加宽后，还有哪类**未被拦下的输入**（如 `getattr` / 间接调用 / 动态 import）？属「门未覆盖的路径」——如实登记即可，不阻断。另核：加宽是否对**对照输入**误红（如 docstring 提及后缀被计数）？
- ④ `_read_group_family` 去重保序是否改变 Graphiti `group_ids` 的顺序语义（RRF 是否依赖顺序）？
- ⑤ pyright 0 是否靠 ignore 掩盖？
- ⑥ 若你发现其它真问题，按 §④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写；无发现时写全 0）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--mode build` 已禁 Bash/Write；如遇权限阻断属预期，不是缺陷）；
- **不连库**：不连 7691 / 7687 / 7692；
- **不评**（本卡范围外）：`episode_worker.py` :585-610 之外；`memory_service.py` 的 P2 区间（:273-530 / :636 / :1423-1686 / :2672-2900）；fulltext 路径改法（:2221 起）；C2-13 T-new-7 是否接通；
- **不评已登记移交项本身**（§②.3、③.③ 所列），除非你发现**终态与之不符**；
- 本轮只审 `bbd2a9fb` 所钉代码终态；不审 `_bmad-output/` 文档面。

---

## 附录：变更集全文（git diff d4c19c06 → bbd2a9fb，4 文件）

```diff
diff --git a/backend/app/graphiti/group_id_compat.py b/backend/app/graphiti/group_id_compat.py
index 13e17352..32b00d2d 100644
--- a/backend/app/graphiti/group_id_compat.py
+++ b/backend/app/graphiti/group_id_compat.py
@@ -16,8 +16,13 @@ Background:
 
     Boundary locations (must call sanitize before passing to graphiti_core):
     - `episode_worker._process_task` → graphiti.add_episode(group_id=...)
+      —— CARD-G4-5 起经 `semantic_write_group()` 单一入口, 不再手拼。
     - `memory_service._search_graphiti` → graphiti.search_(group_ids=[...])
     - `memory_service._search_graphiti_legacy` → graphiti.search(group_ids=[...])
+      —— 这两处 CARD-G4-5 起都经 `memory_service._read_group_family()`, 它
+      = `static_group_family()` (静态半边, 本模块) + `_expand_vault_subgroups()`
+      (动态半边, 连 Neo4j 故留在 memory_service)。手拼 `[gid, semantic_group_id(gid)]`
+      的形态由 `tests/unit/test_group_family_builder.py` 的 AST 门禁掉。
 
     Reverse direction: not currently needed — Canvas readers query
     Neo4j's EpisodicNode.source_description / node_id, not its group_id
@@ -137,6 +142,50 @@ def semantic_group_id(group_id: str) -> str:
     return f"{group_id}{sep}{_SEMANTIC_SUFFIX}"
 
 
+def semantic_write_group(group_id: str) -> str:
+    """**写侧唯一入口**: 任意来源 group_id → 语义影子图的物理组 (CARD-G4-5)。
+
+    := ``semantic_group_id(sanitize_group_id_for_graphiti(group_id))``
+
+    为什么要有这个函数: 写侧 (``episode_worker``) 与读侧 (``memory_service`` 两处)
+    此前各自手拼这条链。手拼的问题不是"写错了", 而是**改一处不会带另一处** ——
+    写侧哪天改了后缀或规范化顺序, 读侧的组集合就不再包含它, 表现为检索静默少召回。
+
+    与读侧的关系 (本函数的**契约**, 由 ``test_group_family_builder.py`` 的 property 锁住):
+
+    - ``semantic_write_group(g) in static_group_family(sanitize_group_id_for_graphiti(g))``
+      —— 写进去的组一定在读取家族里;
+    - ``vault_scope.group_in_read_scope(semantic_write_group(g), g) is True``
+      —— 且落在 R4 前缀可见面内 (``scope`` 或 ``scope + "__"`` 前缀)。
+
+    幂等: 物理形态 / 逻辑形态 / 已带后缀的输入都收敛到同一个 ``…__semantic``。
+    """
+    return semantic_group_id(sanitize_group_id_for_graphiti(group_id))
+
+
+def static_group_family(group_id_phys: str) -> list:
+    """**读侧静态半边唯一入口**: 物理组 → ``[本组, 影子组]`` (CARD-G4-5)。
+
+    ⚠️ 只是**静态**半边。读侧完整的组族 = 本函数 + **动态**半边 (``本组__*`` 子组枚举),
+    后者由 ``memory_service._expand_vault_subgroups`` 提供 —— 它要连 Neo4j, 而本模块
+    必须保持**纯函数**(无 I/O、无 ContextVar), 所以不搬进来。两者的拼接点是
+    ``memory_service._read_group_family``。
+
+    去重保序: 输入若**本身就是影子组**, 返回 ``[gid]`` 单元素 (``semantic_group_id``
+    对已带后缀的输入幂等返回自身, 拼出来会重复)。空串返回 ``[]``。
+
+    ⛔ 不在这里做 ``sanitize``: 调用方给的已经是物理组 (读侧在 ``require_read_group``
+    之后就已物理化)。在这里再 sanitize 一次会把参数语义从"物理组"悄悄放宽成"任意组",
+    而两者在出错时的表现不同 —— 物理组进来才是可断言的前提。
+    """
+    if not group_id_phys:
+        return []
+    shadow = semantic_group_id(group_id_phys)
+    if shadow == group_id_phys:
+        return [group_id_phys]
+    return [group_id_phys, shadow]
+
+
 def to_physical_group_id(group_id: str) -> str:
     """任意来源 group_id → Neo4j 物理存储格式 (T1 统一, 2026-07-10 交接任务书).
 
diff --git a/backend/app/services/episode_worker.py b/backend/app/services/episode_worker.py
index 6b7e31d5..1f768f43 100644
--- a/backend/app/services/episode_worker.py
+++ b/backend/app/services/episode_worker.py
@@ -589,15 +589,17 @@ class GraphitiEpisodeWorker:
         # 也不会 invalidate 主图边。分组在此单点固定, 不暴露给任何 enqueue
         # 调用方; 主图只由 graphiti_structured_writer 直写。读侧已同构:
         # search_memories 主图+影子图同查。
-        from app.graphiti.group_id_compat import (
-            sanitize_group_id_for_graphiti,
-            semantic_group_id,
-        )
+        # CARD-G4-5: 写侧收敛到单一入口 semantic_write_group ——
+        # 它就是 semantic_group_id(sanitize_group_id_for_graphiti(x)) 这条链本身,
+        # 行为逐字节等价(既有三处字面量断言原样绿)。收敛的意义是: 读侧
+        # memory_service._read_group_family 引用的是**同一个模块的同一套规则**,
+        # 改一处两边一起改, 不会出现"写进去的组不在读取家族里"。
+        from app.graphiti.group_id_compat import semantic_write_group
 
         kwargs: dict[str, Any] = {
             "name": task.name,
             "episode_body": task.episode_body,
-            "group_id": semantic_group_id(sanitize_group_id_for_graphiti(task.group_id)),
+            "group_id": semantic_write_group(task.group_id),
             "source_description": task.source_description,
             "reference_time": task.reference_time,
         }
diff --git a/backend/app/services/memory_service.py b/backend/app/services/memory_service.py
index f865d1e9..e4ebc702 100644
--- a/backend/app/services/memory_service.py
+++ b/backend/app/services/memory_service.py
@@ -1846,10 +1846,7 @@ class MemoryService:
             # M2 双图检索 (2026-07-13, 路线图 v2): 主图 + 语义影子图同查 —
             # 影子图只由 LLM 抽取通道写入 (semantic_group_id 服务端固定),
             # 读侧扩展让对话上下文能召回蒸馏产物的隐式关系 fact。
-            from app.graphiti.group_id_compat import (
-                sanitize_group_id_for_graphiti,
-                semantic_group_id,
-            )
+            from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
 
             # CARD-G4-1a (2026-08-30): 此前 group_id 为空 → _search_groups=None
             # → graphiti search_ 不带 group_ids = **搜全部 vault**。改 fail-closed
@@ -1864,8 +1861,9 @@ class MemoryService:
             # (审查实锤: q1 完美中文答案搁浅在 punycode 组)
             # —— 这正是 Tier 1 侧的"前缀语义"实现: 组集合 = 本组 + 影子组 +
             # 全部 `本组__*` 子组, 与 read_group_filter 的可见面等价。
-            _search_groups = [_gid_phys, semantic_group_id(_gid_phys)]
-            _search_groups += await self._expand_vault_subgroups(
+            # CARD-G4-5: 组族收敛到单一 builder —— 手拼 [本组, 影子组] 的形态已由
+            # tests/unit/test_group_family_builder.py 的 AST 门禁掉。
+            _search_groups = await self._read_group_family(
                 _gid_phys, fail_sink=coverage_sink
             )
             search_kwargs: Dict[str, Any] = {
@@ -1961,10 +1959,7 @@ class MemoryService:
         try:
             # P0-5 (2026-05-14): sanitize group_id at Graphiti boundary
             # M2 双图检索 (2026-07-13): legacy 路径与 Tier1 保持同构 — 主图+影子图
-            from app.graphiti.group_id_compat import (
-                sanitize_group_id_for_graphiti,
-                semantic_group_id,
-            )
+            from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
 
             # CARD-G4-1a: legacy 路径与 Tier 1 同修 —— 空 group 时 group_ids=None
             # 同样是全 vault 搜索面 (它是 recipe 不可用时的实际生产路径)。
@@ -1975,8 +1970,19 @@ class MemoryService:
                     group_id, context="memory_service._search_graphiti_legacy"
                 )
             )
-            _legacy_groups = [_gid_phys, semantic_group_id(_gid_phys)]
-            _legacy_groups += await self._expand_vault_subgroups(_gid_phys)
+            # CARD-G4-5: 与 Tier 1 走**同一个** builder（本卡范围仅此一项）。
+            # ⛔ 这里**刻意不传 fail_sink**。本卡初版曾传 `fail_sink=fail_sink`, 自称
+            # "修掉一处不同构", 实为制造新的不同构 —— 本函数的 `fail_sink` 形参由
+            # `_search_graphiti` (:1835) 绑定为 `tier_failures`(**硬失败**通道), 而
+            # Tier 1 侧把同一种失败喂给 `coverage_sink`(:1866)。四态折算 (:2473-2481)
+            # 下 `tier_failures` 非空 + 零候选 ⇒ **unavailable**, `coverage_failures`
+            # 只到 degraded。CARD-G4-2 HIGH-5 的注释 (:2376-2381) 明文要求"子组枚举
+            # 失败只影响检索广度, 不该报成 unavailable" —— 传进去正好违反它。
+            # 实测 A/B: 传 ⇒ EMPTY 变 UNAVAILABLE(独立审查 2026-09-19 同进程复现)。
+            # 正确修法是给本函数加 `coverage_sink` 形参并由 :1835 一并下传, 那要动
+            # CARD-G4-2 的 sink 管道, **不在本卡范围** ⇒ 登记移交, 此处保持改前语义
+            # (legacy 的子组枚举失败仍不可见, 与 PREV 逐条相同)。
+            _legacy_groups = await self._read_group_family(_gid_phys)
             results = await asyncio.wait_for(
                 worker._graphiti.search(
                     query=query,
@@ -2013,6 +2019,31 @@ class MemoryService:
     #: 批次1'④: 白板级子组枚举缓存 {前缀: (过期时间戳, 组列表)}
     _subgroup_cache: Dict[str, Any] = {}
 
+    async def _read_group_family(
+        self, gid_phys: str, *, fail_sink: Optional[List[str]] = None
+    ) -> List[str]:
+        """读侧**完整**组族 = 静态半边 + 动态半边 (CARD-G4-5)。
+
+        - 静态半边 `static_group_family(gid_phys)` = `[本组, 影子组]` —— 纯函数,
+          与写侧 `semantic_write_group` 同一个模块、同一套规则。这正是本卡要的
+          "写读组对称": 写进哪个组, 读时一定查得到, 因为两边引用的是同一份代码。
+        - 动态半边 `_expand_vault_subgroups(gid_phys)` = 全部 `本组__*` 子组
+          (中文白板名的 punycode 组就落在这里) —— 要连 Neo4j, 所以留在本类。
+
+        去重**保序**: 静态半边在前, 动态半边追加; 重复的丢掉后面那个。
+        ⚠️ 顺序是否对 Graphiti 的 RRF 有语义影响, 本卡**未证明** (见验收单"未证明"),
+        这里只保证与改前逐元素同序 —— 改前也是 `[本组, 影子组] + 子组`。
+        """
+        from app.graphiti.group_id_compat import static_group_family
+
+        family = list(static_group_family(gid_phys))
+        seen = set(family)
+        for gid in await self._expand_vault_subgroups(gid_phys, fail_sink=fail_sink):
+            if gid not in seen:
+                seen.add(gid)
+                family.append(gid)
+        return family
+
     async def _expand_vault_subgroups(
         self, gid_phys: str, fail_sink: Optional[List[str]] = None
     ) -> List[str]:
diff --git a/backend/tests/unit/test_group_family_builder.py b/backend/tests/unit/test_group_family_builder.py
new file mode 100644
index 00000000..76aa60f6
--- /dev/null
+++ b/backend/tests/unit/test_group_family_builder.py
@@ -0,0 +1,571 @@
+"""CARD-G4-5 写读组对称契约门（BATCH-2026-09-18-第十五批）。
+
+锁的缺陷形态：**写侧和读侧各自手拼同一条规则**。
+
+改前：
+
+- 写侧 `episode_worker.py:600` 手拼 `semantic_group_id(sanitize_group_id_for_graphiti(g))`；
+- 读侧 `memory_service.py:1867` / `:1978` 各手拼一次 `[本组, semantic_group_id(本组)]`。
+
+三处拼的是同一条规则，但**没有任何东西保证它们一起改**。哪天有人动了后缀、动了
+规范化顺序、或只改了写侧，读侧的组集合就不再包含写进去的那个组 —— 表现不是报错，
+而是**检索静默少召回一半**（语义影子图里的东西再也搜不到）。这种缺陷没有崩溃点，
+只能靠「写进去的组 ∈ 读取组族」这条 property 把它钉住。
+
+本文件四组门：
+
+1. **写==读 property**（hypothesis）：对任意 D16 逻辑组 `g`，
+   `semantic_write_group(g) ∈ static_group_family(sanitize(g))`，
+   且它落在 `vault_scope.group_in_read_scope` 的可见面内；**双向** —— 同时断言
+   对**别的 vault** 不可见（保召回与保隔离是同一条 property 的两侧）。
+2. **两路径同构**：`_search_graphiti` 与 `_search_graphiti_legacy` 传给 Graphiti 的
+   `group_ids` **集合相等**，且都等于 `_read_group_family` 的输出。
+3. **`_expand_vault_subgroups` 行为**（本卡零改动，只补测试）：分页拼接 / 硬上限截断 /
+   后端降级 / 中途异常 / 缓存命中；并断言它产出的每个 gid 也落在可见面内
+   （对称性覆盖到**动态**半边）。
+4. **禁第二处组拼接的 AST 门**（常驻）：`backend/app/**` 里
+   「List/Tuple 字面量元素含 `semantic_group_id(` Call」= 0，
+   且 `semantic_group_id` 的 Call 不出现在 `group_id_compat.py` 之外。
+
+⚠️ **关于 mock**（与 `test_mastery_injection_memory_contract.py` 同口径）：门 2 的
+`AsyncMock` 不是"让功能假装可用"，它是**检测能力的来源** —— 我们要看的正是
+"传给 Graphiti 的实参组集合"，真 Graphiti 反而看不到这个。门 1/3/4 全是纯函数、
+内存谓词与静态分析，零 mock。
+
+⚠️ 本文件零 Neo4j、零网络：`_expand_vault_subgroups` 的**真 Cypher 面**不在此证明
+（见验收单「本卡未证明什么」①）。
+"""
+
+from __future__ import annotations
+
+import ast
+import pathlib
+from unittest.mock import AsyncMock, MagicMock
+
+import pytest
+from hypothesis import given, settings
+from hypothesis import strategies as st
+
+# ⛔ 模块顶层**不 import 任何本卡新符号**（`semantic_write_group` /
+#    `static_group_family` / `_read_group_family`）—— 否则这个文件在改代码前
+#    根本收集不了，(b) 的「先红」就只能红在 collection error 上，证明不了任何事。
+#    新符号一律在用例体内 import。
+
+_APP_ROOT = pathlib.Path(__file__).resolve().parents[2] / "app"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 门① 写 == 读 property
+# ═══════════════════════════════════════════════════════════════════════════
+
+#: D16 逻辑组的段：ASCII 词字符 ∪ 中文（走 punycode 分支）∪ 已物理化 ∪ 已带后缀。
+#: ⛔ 策略必须真的覆盖中文段 —— 只喂 ASCII 的话 `sanitize` 的 punycode 分支
+#: 一次都走不到，property 会退化成"单段 ASCII 族恒等式"。
+_ASCII_SEG = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=12)
+_CJK_SEG = st.text(alphabet="特征值向量线性代数导数积分", min_size=2, max_size=6)
+_SEG = st.one_of(_ASCII_SEG, _CJK_SEG)
+
+
+@st.composite
+def _logical_group(draw):
+    """`vault:<seg>(:<seg>){0,2}`，另含已物理化 / 已带 semantic 后缀两种形态。"""
+    segs = draw(st.lists(_SEG, min_size=1, max_size=3))
+    shape = draw(st.sampled_from(["logical", "physical", "already_semantic"]))
+    if shape == "logical":
+        return "vault:" + ":".join(segs)
+    if shape == "physical":
+        # 已物理化形态：调用方可能直接把 vault__x 传进来
+        from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
+
+        return sanitize_group_id_for_graphiti("vault:" + ":".join(segs))
+    return "vault:" + ":".join(segs) + ":semantic"
+
+
+@settings(max_examples=200, deadline=None)
+@given(g=_logical_group())
+def test_write_group_is_always_inside_the_read_family(g):
+    """写进去的组**一定**在读取家族里，且落在 R4 前缀可见面内。
+
+    这是本卡的核心 property。它锁的不是某一行代码，而是「写侧和读侧引用同一套规则」
+    这件事本身 —— 任何一侧被改坏，这条断言立刻红。
+    """
+    from app.core.vault_scope import group_in_read_scope
+    from app.graphiti.group_id_compat import (
+        sanitize_group_id_for_graphiti,
+        semantic_write_group,
+        static_group_family,
+    )
+
+    written = semantic_write_group(g)
+    family = static_group_family(sanitize_group_id_for_graphiti(g))
+
+    assert written in family, (
+        f"写进去的组不在读取家族里 ⇒ 语义影子图的内容搜不到。\n  g={g!r}\n  written={written!r}\n  family={family!r}"
+    )
+    assert group_in_read_scope(written, g) is True, (
+        f"写进去的组落在 R4 前缀可见面之外 ⇒ Cypher / 内存兜底两侧都查不到它。\n  g={g!r}  written={written!r}"
+    )
+    assert all(group_in_read_scope(x, g) for x in family), (
+        f"读取家族里有成员落在可见面之外: {[x for x in family if not group_in_read_scope(x, g)]!r}（g={g!r}）"
+    )
+
+
+@settings(max_examples=200, deadline=None)
+@given(g=_logical_group())
+def test_write_group_is_invisible_to_a_different_vault(g):
+    """**零泄漏半边**：写进 vault A 的组，对 vault B **不可见**。
+
+    ⛔ 这条和上一条必须成对。只测"读得到"会让一个"恒返回 True"的
+    `group_in_read_scope` 照样绿 —— 那等于把跨 vault 隔离整个拆掉。
+    """
+    from app.core.vault_scope import group_in_read_scope
+    from app.graphiti.group_id_compat import semantic_write_group
+
+    written = semantic_write_group(g)
+    other = "vault:zz_other_vault_g45"
+    assert group_in_read_scope(written, other) is False, (
+        f"vault A 写进去的组对 vault B 可见 ⇒ 跨 vault 泄漏。\n  g={g!r}  written={written!r}  other={other!r}"
+    )
+
+
+@settings(max_examples=100, deadline=None)
+@given(g=_logical_group())
+def test_static_group_family_is_idempotent_on_the_shadow_group(g):
+    """对影子组再取一次家族 = 它自己（不再套一层后缀，也不会凭空多出主组）。"""
+    from app.graphiti.group_id_compat import (
+        sanitize_group_id_for_graphiti,
+        static_group_family,
+    )
+
+    family = static_group_family(sanitize_group_id_for_graphiti(g))
+    shadow = family[-1]
+    assert static_group_family(shadow) == [shadow], (
+        f"对影子组取家族没有幂等: static_group_family({shadow!r}) = {static_group_family(shadow)!r}"
+    )
+
+
+def test_static_group_family_edge_cases():
+    """空串 / 已是影子组 两个边界 —— property 的策略不会生成空串，单独钉。"""
+    from app.graphiti.group_id_compat import static_group_family
+
+    assert static_group_family("") == []
+    assert static_group_family("vault__a__semantic") == ["vault__a__semantic"], "输入本身就是影子组时不得重复拼出两份"
+    assert static_group_family("vault__a") == ["vault__a", "vault__a__semantic"]
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 门② 两路径同构
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _svc_with_subgroups(subgroups):
+    """造一个 MemoryService，其 `_expand_vault_subgroups` 返回给定子组。"""
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    svc = _make_service(_make_neo4j_mock())
+    svc._expand_vault_subgroups = AsyncMock(return_value=list(subgroups))
+    return svc
+
+
+def _worker_with_graphiti():
+    """打桩 episode worker：只为捕获传给 Graphiti 的实参。"""
+    graphiti = MagicMock()
+    graphiti.search_ = AsyncMock(return_value=MagicMock(edges=[], nodes=[]))
+    graphiti.search = AsyncMock(return_value=[])
+    worker = MagicMock()
+    worker.is_ready = True
+    worker._graphiti = graphiti
+    return worker, graphiti
+
+
+@pytest.mark.asyncio
+async def test_both_search_paths_pass_the_same_group_family(monkeypatch):
+    """Tier 1 与 legacy 传给 Graphiti 的 `group_ids` **集合相等**，且都 == `_read_group_family`。
+
+    ⛔ 判据是**集合相等**并且两侧都等于 builder 的输出 —— 不是"非空"、也不是
+    "两边一样就行"（两边一样地错也叫一样）。
+    """
+    from app.core.subject_config import _current_subject_id
+
+    vault = "vault:g45_iso"
+    subgroups = ["vault__g45_iso__board_a", "vault__g45_iso__board_a__semantic"]
+
+    token = _current_subject_id.set(vault)
+    try:
+        worker, graphiti = _worker_with_graphiti()
+        monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: worker)
+
+        svc = _svc_with_subgroups(subgroups)
+        expected = await svc._read_group_family("vault__g45_iso")
+
+        await svc._search_graphiti("q", group_id=vault, limit=5)
+        tier1_groups = graphiti.search_.call_args.kwargs["group_ids"]
+
+        svc2 = _svc_with_subgroups(subgroups)
+        await svc2._search_graphiti_legacy("q", group_id=vault, limit=5)
+        legacy_groups = graphiti.search.call_args.kwargs["group_ids"]
+    finally:
+        _current_subject_id.reset(token)
+
+    assert set(tier1_groups) == set(legacy_groups), (
+        f"两条读路径的组集合不同构 ⇒ 同一次查询走哪条路径决定了能搜到什么。\n"
+        f"  tier1={sorted(tier1_groups)!r}\n  legacy={sorted(legacy_groups)!r}"
+    )
+    assert set(tier1_groups) == set(expected), (
+        f"Tier 1 的组集合不等于 _read_group_family 的输出 ⇒ 它没走 builder。\n"
+        f"  actual={sorted(tier1_groups)!r}\n  expected={sorted(expected)!r}"
+    )
+    assert set(legacy_groups) == set(expected), (
+        f"legacy 的组集合不等于 _read_group_family 的输出 ⇒ 它没走 builder。\n"
+        f"  actual={sorted(legacy_groups)!r}\n  expected={sorted(expected)!r}"
+    )
+    # 承重: 家族里确实含影子组（否则上面三条在"两边都没有影子组"时也全绿）
+    assert "vault__g45_iso__semantic" in set(tier1_groups), (
+        f"组集合里没有影子组 ⇒ 语义图内容搜不到: {sorted(tier1_groups)!r}"
+    )
+
+
+@pytest.mark.asyncio
+async def test_legacy_path_keeps_enumeration_failure_out_of_the_hard_failure_sink(
+    monkeypatch,
+):
+    """legacy 的子组枚举失败**不得**进它的 `fail_sink`（那是硬失败通道）。
+
+    本卡初版曾在 `:1977` 传 `fail_sink=fail_sink`，自称"修掉不同构"，实为回归：
+    该形参由 `_search_graphiti` (:1835) 绑定为 `tier_failures`，而 Tier 1 侧把
+    **同一种**失败喂给 `coverage_sink`。四态折算 (:2473-2481) 下 `tier_failures`
+    非空 + 零候选 ⇒ `unavailable`；`coverage_failures` 只到 `degraded`。
+    CARD-G4-2 HIGH-5 的注释 (:2376-2381) 明文要求"子组枚举失败只影响检索广度,
+    不该报成 unavailable"。独立审查 2026-09-19 同进程 A/B 实测 EMPTY→UNAVAILABLE。
+
+    ⚠️ 本门期望"sink 为空"。空值判据必须先证**输入面非空**，否则枚举压根没失败
+    时它恒绿（见下方 `probe` 验伪锚）。
+    """
+    from app.core.subject_config import _current_subject_id
+    from app.graphiti.group_id_compat import sanitize_group_id_for_graphiti
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    vault = "vault:g45_sink"
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=RuntimeError("injected enumeration failure"))
+    svc = _make_service(neo4j)
+
+    worker, _ = _worker_with_graphiti()
+    monkeypatch.setattr("app.services.memory_service.get_episode_worker", lambda: worker)
+
+    sink: list = []
+    probe: list = []
+    token = _current_subject_id.set(vault)
+    try:
+        # 验伪锚：同一注入下，枚举**确实**失败并且**确实**会往它拿到的 sink 里写。
+        # 若这里为空 ⇒ 故障没注进去，下面的"sink 为空"就是空洞的绿。
+        await svc._expand_vault_subgroups(sanitize_group_id_for_graphiti(vault), fail_sink=probe)
+        await svc._search_graphiti_legacy("q", group_id=vault, limit=5, fail_sink=sink)
+    finally:
+        _current_subject_id.reset(token)
+
+    assert any("subgroup enumeration" in m for m in probe), (
+        f"验伪锚失效：故障未注入或 _expand_vault_subgroups 不再写 sink ⇒ 本门无辨别力。\n  probe={probe!r}"
+    )
+    assert sink == [], (
+        "legacy 把子组枚举失败写进了**硬失败**通道 (tier_failures) ⇒ 零候选时四态"
+        f"从 empty 变 unavailable，违反 CARD-G4-2 HIGH-5。\n  sink={sink!r}"
+    )
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 门③ _expand_vault_subgroups 行为（本卡零改动，只补测试）
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+def _paged_run_query(total: int):
+    """按 offset/limit 返回预置页的 run_query 替身。"""
+
+    async def _run(cypher, **params):
+        offset = params["offset"]
+        limit = params["limit"]
+        prefix = params["prefix"]
+        return [{"gid": f"{prefix}g{i:05d}"} for i in range(offset, min(offset + limit, total))]
+
+    return _run
+
+
+@pytest.mark.asyncio
+async def test_expand_subgroups_pages_until_short_page():
+    """501 条 ⇒ 两次调用、offset 递增 500、结果拼接完整。"""
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=_paged_run_query(501))
+    svc = _make_service(neo4j)
+
+    out = await svc._expand_vault_subgroups("vault__g45_page")
+
+    assert len(out) == 501, f"分页拼接不完整: {len(out)}"
+    assert neo4j.run_query.await_count == 2, f"应恰好两次分页调用: {neo4j.run_query.await_count}"
+    assert [c.kwargs["offset"] for c in neo4j.run_query.await_args_list] == [0, 500]
+
+
+@pytest.mark.asyncio
+async def test_expand_subgroups_truncates_at_hard_cap_and_says_so():
+    """撞到硬上限 ⇒ 截断 + `fail_sink` 含 truncated（覆盖面收窄不假装完整）。"""
+    from app.services.memory_service import _SUBGROUP_HARD_CAP
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=_paged_run_query(_SUBGROUP_HARD_CAP + 1000))
+    svc = _make_service(neo4j)
+
+    sink: list = []
+    out = await svc._expand_vault_subgroups("vault__g45_cap", fail_sink=sink)
+
+    assert len(out) >= _SUBGROUP_HARD_CAP
+    assert any("truncated" in m for m in sink), f"截断没有记进 fail_sink: {sink!r}"
+
+
+@pytest.mark.asyncio
+async def test_expand_subgroups_backend_down_returns_empty_and_does_not_cache():
+    """后端降级 ⇒ `[]` + fail_sink + **不写缓存**（否则 5 分钟内按收窄面检索）。"""
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    # ⚠️ 降级信号不是 `_initialized`：`_neo4j_backend_failure` 的判据是
+    #    `is_fallback_mode is True` 或 `stats["initialized"] is False`（它刻意要求
+    #    真实 bool，因为 MagicMock 的属性恒 truthy，用 truthy 判断会把每个 mock
+    #    都判成降级）。写错这个常量，本门就会在"探针压根没触发"的情况下假绿。
+    neo4j = _make_neo4j_mock()
+    neo4j.is_fallback_mode = True
+    neo4j.run_query = AsyncMock(side_effect=AssertionError("降级时不该查库"))
+    svc = _make_service(neo4j)
+
+    from app.services.memory_service import _neo4j_backend_failure
+
+    assert _neo4j_backend_failure(neo4j), "前提失效: 降级探针没报警，本门什么都没测"
+
+    sink: list = []
+    out = await svc._expand_vault_subgroups("vault__g45_down", fail_sink=sink)
+
+    assert out == []
+    assert any("unusable" in m for m in sink), f"降级没有记进 fail_sink: {sink!r}"
+    assert "vault__g45_down__" not in svc._subgroup_cache, "降级结果被写进了缓存"
+
+
+@pytest.mark.asyncio
+async def test_expand_subgroups_midway_exception_keeps_partial_and_does_not_cache():
+    """中途异常 ⇒ 返已收集部分 + fail_sink 含异常类名 + **不写缓存**。"""
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    calls = {"n": 0}
+
+    async def _run(cypher, **params):
+        calls["n"] += 1
+        if calls["n"] == 1:
+            return [{"gid": f"{params['prefix']}g{i:05d}"} for i in range(params["limit"])]
+        raise RuntimeError("injected midway failure")
+
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=_run)
+    svc = _make_service(neo4j)
+
+    sink: list = []
+    out = await svc._expand_vault_subgroups("vault__g45_mid", fail_sink=sink)
+
+    assert len(out) == 500, f"没有返回已收集的部分: {len(out)}"
+    assert any("RuntimeError" in m for m in sink), f"异常类名没进 fail_sink: {sink!r}"
+    assert "vault__g45_mid__" not in svc._subgroup_cache, "失败结果被写进了缓存"
+
+
+@pytest.mark.asyncio
+async def test_expand_subgroups_uses_cache_on_second_call():
+    """成功一次后命中缓存，不再查库。"""
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=_paged_run_query(3))
+    svc = _make_service(neo4j)
+
+    first = await svc._expand_vault_subgroups("vault__g45_cache")
+    n_after_first = neo4j.run_query.await_count
+    second = await svc._expand_vault_subgroups("vault__g45_cache")
+
+    assert first == second
+    assert neo4j.run_query.await_count == n_after_first, "第二次仍然查库了（缓存没命中）"
+
+
+@pytest.mark.asyncio
+async def test_expanded_subgroups_are_all_inside_the_read_scope():
+    """**动态**半边也必须落在 R4 可见面内 —— 对称性不能只覆盖静态半边。"""
+    from app.core.vault_scope import group_in_read_scope
+    from tests.unit.test_story_31a2_helpers import _make_neo4j_mock, _make_service
+
+    neo4j = _make_neo4j_mock()
+    neo4j.run_query = AsyncMock(side_effect=_paged_run_query(5))
+    svc = _make_service(neo4j)
+
+    gid_phys = "vault__g45_scope"
+    out = await svc._expand_vault_subgroups(gid_phys)
+
+    assert out, "前提失效: 枚举返回空，本门什么都没测"
+    bad = [g for g in out if not group_in_read_scope(g, gid_phys)]
+    assert not bad, f"动态半边产出的组落在可见面之外: {bad!r}"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 门④ 禁第二处组拼接（AST，常驻）
+# ═══════════════════════════════════════════════════════════════════════════
+
+
+#: 语义影子组的后缀标记。⛔ 只在**构造式**里认它（f-string 片段 / `+` 拼接操作数），
+#: 不认裸 `ast.Constant` —— 否则 docstring 里提到 "__semantic" 就会把门打成假红
+#: （实测 app/ 下有 3 处这样的 docstring：group_id_compat.py ×2、memory_service.py ×1）。
+_SUFFIX_MARKS = ("__semantic", ":semantic")
+
+
+def _is_suffix_const(node) -> bool:
+    return (
+        isinstance(node, ast.Constant) and isinstance(node.value, str) and any(m in node.value for m in _SUFFIX_MARKS)
+    )
+
+
+def _builds_shadow_suffix(node) -> bool:
+    """该节点是否**拼出**一个带语义后缀的串（f-string 或 `+` 拼接）。"""
+    if isinstance(node, ast.JoinedStr):
+        return any(_is_suffix_const(v) for v in node.values)
+    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
+        return any(_is_suffix_const(o) or _builds_shadow_suffix(o) for o in (node.left, node.right))
+    return False
+
+
+def _shadow_names(tree) -> set:
+    """本文件里指向 `semantic_group_id` 的**全部**名字（含 `as` 别名）。
+
+    ⛔ 按名字比对的 AST 与 grep 在「有人用别名调用」这点上本来是等价的 ——
+    这里解析 ImportFrom 的 asname 才真正拉开差距。
+    """
+    names = {"semantic_group_id"}
+    for n in ast.walk(tree):
+        if isinstance(n, ast.ImportFrom):
+            for a in n.names:
+                if a.name == "semantic_group_id" and a.asname:
+                    names.add(a.asname)
+    return names
+
+
+def _scan_app():
+    """扫 `backend/app/**`，按 **AST 节点**计数（不是文本）。"""
+
+    def nm(f):
+        return f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
+
+    calls, literals, builder_calls, builder_defs = [], [], [], []
+    for p in sorted(_APP_ROOT.rglob("*.py")):
+        tree = ast.parse(p.read_text(encoding="utf-8"))
+        shadow = _shadow_names(tree)
+        for n in ast.walk(tree):
+            if isinstance(n, ast.Call):
+                k = nm(n.func)
+                if k in shadow and p.name != "group_id_compat.py":
+                    calls.append(f"{p.name}:{n.lineno}")
+                if k in ("static_group_family", "semantic_write_group", "_read_group_family"):
+                    builder_calls.append(f"{p.name}:{n.lineno}")
+            if isinstance(n, (ast.List, ast.Tuple)) and any(
+                (isinstance(e, ast.Call) and nm(e.func) in shadow) or _builds_shadow_suffix(e) for e in n.elts
+            ):
+                literals.append(f"{p.name}:{n.lineno}")
+            if isinstance(n, ast.FunctionDef) and n.name in (
+                "static_group_family",
+                "semantic_write_group",
+            ):
+                builder_defs.append(f"{p.name}:{n.lineno}")
+    return calls, literals, builder_calls, builder_defs
+
+
+def test_no_second_place_assembles_the_group_family():
+    """⛔ 组族只准在一个地方拼。
+
+    改前 `memory_service.py` 两处各有一个 `[本组, semantic_group_id(本组)]` 字面量；
+    它们和写侧是"同一条规则的三份手抄"，改一份不会带另外两份。本门把这种形态禁掉。
+
+    ⚠️ **验伪锚**：门必须同时断言它扫到了 builder 的 `def` —— 否则一次空扫描
+    （路径写错、rglob 匹配不到）会让上面两条"= 0"的断言无条件通过。
+    """
+    calls, literals, builder_calls, builder_defs = _scan_app()
+
+    assert builder_defs, (
+        "验伪锚失败: 扫描没找到 static_group_family / semantic_write_group 的 def —— "
+        f"本次扫描很可能是空的，下面的『= 0』证明不了任何事。ROOT={_APP_ROOT}"
+    )
+    assert literals == [], (
+        f"又有地方手拼组族字面量 [本组, semantic_group_id(本组)]: {literals}\n"
+        "请改调 group_id_compat.static_group_family / memory_service._read_group_family。"
+    )
+    assert calls == [], (
+        f"semantic_group_id 被 group_id_compat.py 之外的代码直接调用: {calls}\n"
+        "写侧请用 semantic_write_group，读侧请用 static_group_family。"
+    )
+    # 承重: builder 确实被那两个消费方调着（否则"没人手拼"可能只是"没人用"）
+    consumers = {c.split(":")[0] for c in builder_calls}
+    assert {"memory_service.py", "episode_worker.py"} <= consumers, (
+        f"builder 的消费方不全: {sorted(consumers)}（期望含 memory_service.py 与 episode_worker.py）"
+    )
+
+
+def test_ast_gate_counts_nodes_not_text():
+    """本门自己的**验伪锚**：注释里写同样的字样不得被计数。
+
+    没有这一条，`_scan_app` 哪天被改成 `grep` 也照样绿，而 grep 会把注释、docstring、
+    字符串字面量全算进去 —— 那种门在"有人把手拼挪进注释"时会假红，在"有人用别名调用"
+    时会假绿。
+    """
+    src_with_comment = "# _probe = [_x, semantic_group_id(_x)]\n"
+    src_with_code = "_probe = [_x, semantic_group_id(_x)]\n"
+
+    def count(src):
+        def nm(f):
+            return f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
+
+        tree = ast.parse(src)
+        return sum(
+            1
+            for n in ast.walk(tree)
+            if isinstance(n, (ast.List, ast.Tuple))
+            and any(isinstance(e, ast.Call) and nm(e.func) == "semantic_group_id" for e in n.elts)
+        )
+
+    assert count(src_with_comment) == 0, "注释被当成代码计数了"
+    assert count(src_with_code) == 1, "真代码没被计数 —— 判据本身失效"
+
+
+def test_ast_gate_catches_the_three_escape_forms():
+    """加宽后的门必须抓到 f-string / `+` 拼接 / `as` 别名三种逃逸（独立对抗审查 2026-09-19 HIGH）。
+
+    改前的门只认 `ast.Call` 且名为 `semantic_group_id`，于是这三种写法整建制绕过：
+    把 `_search_graphiti` 的组族改回 `[g, f"{g}__semantic"] + subs` 时门**全绿**。
+    ⛔ 本门直接喂 `_builds_shadow_suffix` / `_shadow_names` 这两个**真函数**，
+    不是内联副本 —— 副本测试证明不了 `_scan_app` 用的是哪套逻辑。
+    """
+
+    def elt(src):
+        """取 `[...]` 字面量的第二个元素节点。"""
+        return ast.parse(src, mode="eval").body.elts[1]
+
+    # ── 三种逃逸形态：加宽后必须全部被认出 ──
+    assert _builds_shadow_suffix(elt('[g, f"{g}__semantic"]')) is True, "f-string 形态逃逸"
+    assert _builds_shadow_suffix(elt('[g, g + "__semantic"]')) is True, "+ 拼接形态逃逸"
+    assert _builds_shadow_suffix(elt('[g, g + ":semantic"]')) is True, "冒号后缀形态逃逸"
+
+    # ── 别名形态：靠 _shadow_names 解析 asname ──
+    tree = ast.parse("from app.graphiti.group_id_compat import semantic_group_id as sg\nx = [g, sg(g)]\n")
+    names = _shadow_names(tree)
+    assert "sg" in names, f"别名未被解析出来 ⇒ 别名调用仍可绕过。names={names!r}"
+
+    # ── 控制组（防过度加宽）：这些**不该**被认成拼影子组 ──
+    assert _builds_shadow_suffix(elt("[g, other(g)]")) is False, "普通调用被误判"
+    assert _builds_shadow_suffix(elt('[g, g + "__board_a"]')) is False, "无关后缀被误判"
+    assert _builds_shadow_suffix(ast.parse('"docstring 提到 __semantic"', mode="eval").body) is False, (
+        "裸字符串常量被误判 ⇒ docstring 会把门打成假红"
+    )
+
+    # ── 真实面：app/ 下仍应为 0（加宽不得引入假红）──
+    _, literals, _, builder_defs = _scan_app()
+    assert builder_defs, "验伪锚：builder 的 def 没找到 ⇒ 扫描面坏了，下面的 0 是空洞的"
+    assert literals == [], f"app/ 出现手拼组族字面量: {literals!r}"
```
