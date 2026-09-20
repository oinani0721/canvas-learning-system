# 第十五批 P1 内部对抗审查（⛔ 非 Codex 轮次，不满足 D-15）

> 批次: BATCH-2026-09-18-第十五批 · 车道 P1 · 卡 P1-B `CARD-LANCE-INDEX-DELETE-CONTRACT` + P1-C `CARD-G4-5`
> 日期: 2026-09-19 · 依据: 根 CLAUDE.md 铁律 3「代码审查必须独立 Agent」
> 审查绑定: P1-B 代码面 `5e0f87b7..f6ea5006`；P1-C 代码面 `f6ea5006..b41f49c3`（两卡均已实测仍绑 HEAD，判据 + 验伪锚见 `evidence-lance-index-delete/serial-lane-binding-*.txt`）

## ⛔ 效力声明（引用前必读）

- 本文件 **不得**充当 D-15 的 Codex 轮次。P1-B 的 Codex 实况 = r1/r2/r3 已跑并整改，**差绑最终 HEAD 的 r4**；P1-C = **0 轮**。
- 阻塞原因见 `evidence-lance-index-delete/codex-model-unavailable-20260919.md`：`gpt-6-astra` 在当前 ChatGPT 账号返回 400 `not supported`（**非配额**，已复测）。
- 台账/验收单引用本文件时必须标注「内部 Agent 审查，非 Codex」。

## 一、审查配置

5 个独立视角，只读，各自绑定上述 SHA：

| # | 视角 | 判定 |
|---|---|---|
| 1 | P1-B 契约回归（int 契约 / `_last_drop_*` 语义 / 四道闸 / outcome 序 / 旧调用方） | B=1* H=2 M=3 L=3 |
| 2 | P1-B fail-closed 完整性与信息外泄 | B=1* H=5 M=4 L=2 |
| 3 | P1-B 测试面猎杀假绿（25 条逐条 revert-sensitivity） | B=0 H=1 M=2 L=6 |
| 4 | P1-C 组族语义与 R4 前缀 | B=0 H=1 M=3 L=5 |
| 5 | P1-C 门与 AST 门有效性 | B=0 H=2 M=4 L=8 |

\* 两条 B 均经主 session 复核**降级**，理由见 §三。

## 二、已修（本轮新增 2 个 commit，均带负控闭环）

### 1. `622a3626` P1-C：legacy 子组枚举失败不进硬失败通道

审查者 4 与 5 **各自独立**报出，其一做同进程 A/B 实测 `EMPTY → UNAVAILABLE`。主 session 复核结构事实无误。

- 缺陷是**本卡初版自己引入**的：`_search_graphiti_legacy` 传 `fail_sink=fail_sink`，而该形参由 `_search_graphiti`(:1835) 绑定为 `tier_failures`（硬失败通道），Tier 1 侧同一种失败走 `coverage_sink`(:1866)。四态折算(:2473-2481)下前者零候选 ⇒ `unavailable`，后者只到 `degraded`。CARD-G4-2 HIGH-5 注释(:2376-2381)明文禁止这个方向。
- 代码注释当时写的是「顺带修掉一处不同构」——**实为制造新的不同构**。
- 处置：改回不传，与 PREV 逐条同语义。正确修法（给 legacy 加 `coverage_sink` 形参 + :1835 下传）要动 CARD-G4-2 的 sink 管道，**不在本卡范围** ⇒ 移交。
- 门 `test_legacy_path_reports_..._into_its_fail_sink` **把缺陷锁成了契约**（正确修法会让它红），已换成 `test_legacy_path_keeps_enumeration_failure_out_of_the_hard_failure_sink`，并配输入面非空验伪锚。
- 负控：注入 `negctl-1` 自证 → 门红 → `git show HEAD:` 还原 shasum 逐字节同 → 零残留。

### 2. `dcc9589e` P1-B：指纹表归属闸

审查者 2 报出，主 session 实测确认归属规则（`a_file_fingerprints` 归 `a_file`）。

- 同样是**本卡引入**：`_ensure_vault_fingerprint_table` 的 docstring 写「名字被占时不能建」，实现只核 schema 形态、**不核归属**。vault `a` 与 `a_file` 并存时会建出归属 `a_file` 的表，新造两条改前不存在的破坏：① `DELETE /index/a` 永久 409 collision；② `DELETE /index/a_file` 销毁 `a` 的指纹基线。
- 处置：归属不是自己的就不建也不认领。命名空间碰撞本身不是本卡能修的（改名才是）⇒ 移交。
- 门 `test_ensure_fingerprint_refuses_a_name_owned_by_another_vault`，**带控制组**（不撞名的 vault 指纹表必须建得出来）。初版写成同步调用协程 `add_documents` 未 await，正是控制组当场抓到的。
- 负控：`negctl-2` 拆闸 → 红 → 还原逐字节同 → 重新绿。

## 三、两条 BLOCKER 的降级裁定（主 session 复核）

### B-1「openapi.json 未再生 ⇒ 漂移门红」→ **降级为「卡文明令的预期状态」**

审查者缺卡文上下文（主 session prompt 未给，责任在主 session）。卡文 (j) 与判据 5 明写：
- 「本卡 commit **不含** openapi.json」「收工 `git diff $PREV HEAD -- backend/openapi.json | wc -l` → **0**」
- 「`test_openapi_snapshot_drift.py` 收工**预期红**，输出贴验收单并登记『待主 session 再生』」

实测：openapi.json 净零 ✅、漂移门红 ✅ = **正是卡文要求的终态**。不阻断。

### B-2「`partial` 留下『有内容表、没指纹表』」→ **降级为 HIGH，登记不阻断**

事实成立（删除循环退出后无补建，与 `rebuild_index` 口径不一致）。但：
- 触发前提是 `drop_table` 真实失败，审查者自陈「未构造出一次真实失败」；
- 修它要在删除路径上加建表动作，语义上与「用户正在删这个 vault 的索引」相悖，属**产品口径决策**，非车道可自裁；
- 按协议 §1 阻断级定义（数据丢失/live vault 或 7691 写入/安全/指定裁判红/负控假绿）不命中。

⇒ 登记移交，写入台账与验收单「未证明」。

## 四、登记不阻断（移交，按来源归类）

**本卡引入、已如实记录**
1. 闸① `registry_degraded` 新增置位点 ⇒ 爆炸半径 = 该客户端实例上**所有 scoped vault**，且**无产品内解除途径**（已在上一轮报给用户，待裁）。
2. 同一端点两个 409 语义不同、体形不同（resolver 的 `detail` 是 str，refusal 的是 dict）⇒ `resp.json()["detail"]["refusal_kind"]` 在前者抛 TypeError。
3. 端点对 `drop_vault_tables_report` 无异常边界，逃逸异常由 `CORSExceptionMiddleware` 把 `str(e)[:500]` 回进 body ⇒ 脱敏不变量**没有执行面**。
4. `partial` 的指纹表缺口（见 §三 B-2）。
5. `drop_vault_tables` 的 int **值**在同一串用户操作下变大（每次写入补建指纹表）；`GET /index/stats` 每 scoped vault `tables` 计数 +1。
6. `rebuild_index` 的 `try/finally` 兜底补建**零门覆盖**（单拆它指定门仍全绿）；且该门的前提锚 `or isinstance(exc.value, RuntimeError)` 右支恒真。
7. AST 门可被 f-string / 字符串拼接 / 别名调用整建制绕过；其「验伪锚」测的是函数内联副本而非 `_scan_app` 本身；`consumers` 锚被 `_read_group_family` 自己的函数体满足。

**既有缺陷、本卡把它提升成契约面**
8. `edge_rationales` 不在 `_BUILTIN_LOGICAL_TABLES` ⇒ 任何写过 edge rationale 的 vault 删索引**永久 409 ambiguous**，且 409 文案给的修复指示是错的。
9. 别名 vault_id（`CS_61B` / `CS 61B`）通过 resolver 但**未归一化**就拼表名 ⇒ 索引完好却回 404，破坏「404 只意味着名下没有表」这条主张。
10. r5-M2 的**实害未闭合**：撞名配置下 vault `a` 改前改后都删不掉自己的索引（`collision` → `registry_degraded`，只换了 kind）。门名 `does_not_forge_vault` 易被读成「已修」。
11. `_pinned_vault_ids` 在降级态把 V 钉成空集（读 cache 而非返回值）—— 当前被两个消费方的降级早退挡住，是上了膛的枪。

**P1-C 侧**
12. 写侧无 `canonical_group_id` 层、读侧有 ⇒ 非规范输入（`cs188` / `cs_61b:main` / `CS 61B`）下「写组 ∈ 读组族」为假；`semantic_write_group` docstring 自称「任意来源」过宽。
13. canvas 级写组不在 static 半边，对称性靠实时 Neo4j 枚举兜着；`_read_group_family` docstring 把结论写成了无条件的。
14. `backend/scripts/quarantine_graphiti_pollution.py:185` 是同一条规则的**第四份**手抄，在 AST 门扫描面之外（`backend/scripts/` 不在 `_APP_ROOT`）。
15. 去重使传给 Graphiti 的 `group_ids` 元素**个数**变少（集合相等、可见面不变），而 `fulltext_query` 有 `len(group_ids) >= 128` 的静默返空阈值 ⇒「本卡零行为变化」的说法不精确。
16. `_subgroup_cache` 是**类属性**（进程级共享），本卡门文件向它写入约 5000 条且无清理 fixture。

## 五、本轮未证明

1. 未证明任何 P1-B 发现在**真 LanceDB 失败**下可复现（审查者均未构造出真实 `drop_table` / `list_tables` 失败）。
2. 未证明 §四 #8/#9 在现网配置下的实际触发率（只做了静态推演 + 机械验算）。
3. 未跑 `tests/unit` 目录级与 `tests/regression`，未对红基线做 diff —— 本轮只跑了点名文件。
4. 未证明本轮两个修复不影响 P1-A 面（`edges.py` / `neo4j_client.py` 零改动，但未重跑其门）。
5. 未证明内部 Agent 审查的覆盖面与 Codex 等价 —— 5 个视角是主 session 选的，不是协议规定的审查面。
