# 验收单 · CARD-G2-3 Neo4j 概念/LEARNED 写身份加 group

> **批次**: BATCH-2026-08-28-第五批 · 车道 S2
> **分支**: `card/s2-neo4j`（不 push，等你验收）
> **日期**: 2026-08-28
> **一句话**: 修掉了 G2-1 审计钉死的"搬家 bug"——以前你在两个不同 vault 里学同一个名字的概念
> （比如数学 vault 和 CS vault 都有"递归"），Neo4j 里只会存一个节点，后学的 vault 会把先学的
> vault 的归属和分数**整个抢走**。现在每个 vault 各有自己的节点和学习记录，互不覆盖、互不删除。

---

## 一、你得到了什么（用户视角）

1. **跨 vault 学习记录不再互相污染**：同名概念在不同 vault 是两个独立节点；A vault 的复习分数
   不会被 B vault 的一次答题覆盖；删 A vault 的白板连线不会顺手删掉 B vault 的同名连线。
2. **一台"存量体检机"**（`backend/scripts/migrate_write_identity_g23.py`）：对现网数据库做只读
   体检，报告有没有被旧 bug 污染的存量数据。**现网实测结果：污染存量 = 0**（你现网只有 1 个
   概念且归属正确），所以不需要任何数据搬迁——体检报告本身就是证明，存档在
   `_bmad-output/审查/evidence-g23/g23-live-7691-dryrun.json`。
3. **一道防呆闸**：万一系统内部拿不到"这是哪个 vault"的信息，写入会被**拒绝并记录错误日志**，
   而不是悄悄把数据塞进默认组（那正是以前跨 vault 污染的源头之一）。

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 10 站点逐条改造 | ✅ neo4j_client.py 8 方法（create_learning_relationship / create_canvas_node_relationship / create_edge_relationship / delete_edge_relationship / record_score_history / create_canvas_association / delete_canvas_association / update_canvas_association）+ fallback_sync_service.py 2 条 replay：group 全部进 MERGE/MATCH 锚定键，禁事后 SET 归属 |
| 组解析先行 + 恒物理化恒非 null | ✅ 新增 `_resolve_physical_group_id()`（显式 → ContextVar → canvas_path 推导 → to_physical_group_id），解析失败 fail-closed 拒写返 False + logger.error（首日观察，不静默降级 DEFAULT） |
| `_build_group_id_from_canvas` 返 None 分支 | ✅ 两条 replay fail-closed（条目计 failed 保持 pending 下轮重试）；canvas 事件 replay 下传 group 由 client 端兜底 |
| JSON 镜像层 `_handle_merge_learning` | ✅ 同型双键修复（{name, group_id} / {user, concept, group} 匹配，去除跨组 clobber 分支） |
| G2-1 两条 xfail 去标翻绿 | ✅ `test_concept_write_identity_dual_vault_current_state` + `test_learned_edge_write_identity_dual_vault_current_state` 现为正向行为门，7692 真库通过 |
| 每类违规新行为门 | ✅ 门 4 新增 6 条：Canvas/Node 双组独立（W1#5）、score history 双组独立（W1#9）、删 A 不影响 B（W2#7）、association update/delete A 不动 B（W1#10+W5#16+W2#15）、fallback replay 不合并（ContextVar 真实切组，不 mock）、group 缺失 fail-closed 防 500（拒写零写入） |
| 迁移器行为门 | ✅ `test_migrate_write_identity_g23.py` **26 passed**：dry-run 零写入 + apply 分裂/回填/去重/prune 正确 + **双闸拒绝现网**（端口 + 库身份）+ 空串/脏空白组留人 + 多源/多 NULL 边聚合 + **幂等** + **全属性保留** + **并列时间戳裁决自洽** + **逻辑重复概念跳过并登记** + **探针确实在测量（含文本伪装反例）** + **零写入失败改变退出码** + **不可达 live-uri 不算授权** |
| 裁判命令 | ✅ `pytest tests/integration/test_cypher_contract_gate.py tests/unit/test_neo4j_client.py -q` **64 passed**（+迁移门 26 = 90 passed） |
| 现网 7691 只读 dry-run | ✅ pending=0（"迁移=证明零动作"，与勘探预期一致）；**三重零写入证据全部实测**：运行时探针证明 READ 会话被服务端拒写 + 计数相等 + **全属性指纹相等**（逐 key 展开，不写死字段清单）；Concept=1 组一致；Canvas/Node/Episode 层无组存量全 0 |
| grep 清零门 | ✅ `SET c.group_id / SET r.group_id / r.group_id = CASE` 两文件 0 命中 |
| 存量回归零恶化 | ✅ 受影响面 19 个测试文件基线对照：修改前后失败清单**逐字节一致**（77 条全为既有债务，diff 为空；加固轮后复验仍一致） |
| 变异负控（防假绿） | ✅ **25/25 变异全被抓** —— 每处修复逐一改坏都必红（写身份退回单键+SET / 删边降级 DEFAULT / 迁移器去 LWW、去去重、去同身份收敛 / 关联降级 DEFAULT / 解析链两分支各打断 / fallback replay 退回单键 / 现网拒绝退回子串 / 去退化输入校验 / 去库身份闸 / 空串组当合法身份 / 去显式空白守卫 / 去段级校验 / 迁移只搬白名单字段 / 拒写探针改硬编码 / 逻辑重复不计 manual / 空串漏回推导链 / 探针任意异常当拒写 / 零写入失败不影响退出码 / 逻辑重复不跳过 apply / 去脏组跳过守卫），可复跑 `backend/scripts/g23_mutation_negative_controls.py` |
| 附带修复 | `health_check` 窄捕获（`ServiceUnavailable` 属 DriverError 非 Neo4jError，异常会逃逸）放宽为全捕获 fail-closed——该缺陷被本卡单测暴露 |

## 二·五、对抗审查抓到并已修的真实缺陷（本卡最有价值的部分）

内部 5 维 × 3 视角对抗工作流（47 agent）产出 14 条候选、**确认 10 条全部修复**，其中三条是真问题：

1. **迁移器会用旧数据覆盖新数据**（HIGH）：`SET r2 += properties(r)` 在"代码先修、存量后迁"的混合
   时代会把陈旧错挂边的分数/时间戳盖到 G2-3 后写入的新边上——而且盖完之后归属是一致的，
   工具自己的复查还报"迁移成功"。已改为逐字段 last-write-wins 比较，且永不整体覆盖属性。
2. **恢复的分数会写进你读不到的平行组**（MEDIUM）：失败重放的组派生用字面量 `"default"`，
   与主写路径的 `get_current_vault_id()` 不同构。修复前（G2-3 之前）这会污染主概念，
   本卡复合键后变成"恢复静默无效"。已改为镜像主路径。
3. **多条测试是假绿**（HIGH+MEDIUM×4）：解析链的两个正向分支（生产主管道恰恰全靠它们）零覆盖；
   fail-closed 断言无法区分"拒绝"与"降级后没找到目标"——把 guard 换成静默降级仍全绿。
   已用"真实目标 + DEFAULT 组 canary + 错误日志断言"三重加固，并以 9 类变异负控证明每道门能红。

4 条候选被三视角裁决反驳（如实记录在审查存档），其中"现网拒绝可被 `:07691` 绕过"虽被反驳，
仍按防御深度改成了真实端口解析。

**Codex 外部审查 round-1 又抓到 1 BLOCKER + 4 HIGH + 1 MEDIUM，同样全部处置**（详见审查存档 §二）：

- **BLOCKER**：现网防护只看端口——但**端口不是数据库身份**，端口转发能让"安全端口"落到现网库。
  已加第二道**库身份闸**（比对 `db.info()` 的 store 指纹），身份读不到就 fail-closed 拒绝。
- **HIGH ×2**：迁移器的 LWW 与去重守卫在**多行**场景下失效（多条源边逐行写、结果依赖数据库不保证的
  行序；两条无组边会双双改成同一身份 → 永久重复边）。已重写为"先聚合选唯一赢家、再写唯一目标边"，
  并新增同身份重复边收敛。
- **HIGH ×2**：空字符串组被当成合法身份（会把空 gid 写进身份键）；语义空组（空白串）绕过 fail-closed
  被静默降级成默认组——后者在 Codex 报告前已由我方边界实测独立发现并修复。
- **MEDIUM**：`zero_writes` 结论过强。已改为三重证据（服务端拒写实测 + 计数相等 + 属性指纹相等）。

## 三、边界与如实声明

1. **本卡只修写侧**。Canvas/Node/Episode 层的读侧无 group 查询（审计 §5 #8/#11-14/#17/#18）
   仍属读侧收敛卡；写侧复合键化后理论上新旧节点可短暂并存——现网实测无此存量
   （legacy_informational 全 0），跨层收敛由 G2-9 隔离 canary 收口。
2. **memory_service.py 零改动**（S1 地盘）：其调用 `create_learning_relationship(group_id=...)`
   签名不变；`record_temporal_event` 的 canvas 节点/边写入不传 group 时由 client 端
   ContextVar/canvas_path 推导链兜底，语义与其上方 `record_episode` 一致（该兜底路径现有
   门 5 两条正向行为门覆盖）。
2b. **⛔ 移交 G2-2（VaultScope 统一）**：失败重放条目本身不带 vault 维度（`agent_service`
   落盘的 failed_writes 无 group_id 字段），本卡把派生对齐到进程 active vault 后，
   跨 vault 切换期间重放旧 vault 的待恢复条目仍会归到新 active vault。根治需 VaultScope +
   落盘条目补 vault 字段——已写进 `_build_group_id_from_canvas` docstring。
3. **迁移器 --apply 从未对现网执行**（硬拒 + 本次无需执行）；apply 引擎的正确性在 7692
   用手工 seed 的三类 legacy 形数据实测（分裂/回填/manual 保留）。
4. canvas_association 三方法**零生产调用方**（G2-1 勘探坐实），新增 group 参数无兼容面。
5. **diff 含格式漂移，如实登记**：`canvas_service.py`（真实改动仅 3 处 / 18 行）、`neo4j_client.py`、
   `fallback_sync_service.py` 的 diff 行数被 `ruff format` 全文件重排放大——这些文件在基线上就有
   存量格式漂移，而仓库的 pre-commit 格式门要求 ruff 格式化，二者不可兼得（实测：把 canvas_service
   还原成"基线 + 3 处精修"的 18 行最小 diff 后，格式门直接拒绝提交）。审阅时可用
   `git diff 37387a86 -- <file> | grep -E "group|G2-3"` 快速定位语义行。

## 四、Codex 审查处置（存档 `_bmad-output/审查/codex-review-CARD-G2-3.md`）

<!-- CODEX-SECTION -->

## 五、验收方法（你只需 5 分钟）

1. 打开 `_bmad-output/审查/evidence-g23/g23-live-7691-dryrun.json`——看 `pending.total: 0`
   和 `reconciliation.zero_writes: true` 两行，这就是"现网无污染、体检零写入"的证明。
2. 你日常使用无任何操作变化；如果你有两个 vault 且学过同名概念，之后各自的复习分数
   会各归各位（这正是修复的核心）。
3. 满意 → 回复"G2-3 通过"；有疑问 → 在本单批注。
