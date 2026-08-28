# CARD-G2-3 审查存档：Neo4j 概念/LEARNED 写身份加 group

> **批次**: BATCH-2026-08-28-第五批 · 车道 S2
> **被审对象**: `card/s2-neo4j` 分支相对 `37387a86` 的全量 diff
> **审查重点（卡片钦定）**: MERGE 键 null 防护 · 迁移器零写入
> **两路独立审查**: ① 内部多维对抗工作流（5 维 × 3 视角裁决，47 agent）② Codex CLI 静态审阅（read-only sandbox）

---

## 一、内部多维对抗审查（工作流 `wf_186e21c4-6b9`）

**方法**: 5 个独立维度并行找问题（null 防护 / 迁移零写入 / 调用方兼容 / 测试有效性 / 契约语义），
每条候选发现交 3 个对抗性裁决者（correctness / reproduce / blast-radius 三视角，默认判 refuted），
≥2 票认定为真才进确认清单。

**结果**: 14 条候选 → **10 条确认** / 4 条被反驳。全部 10 条已处置（见下表）。

| # | 严重级 | 发现 | 处置 |
|---|---|---|---|
| 1+2 | HIGH | **迁移器 `_APPLY_SPLIT` 无 LWW 保护**：`SET r2 += properties(r)` 在混合时代（代码先修、存量后迁）会用陈旧错挂边的 score/timestamp 覆盖 G2-3 后写入的**更新**边——MERGE 属性图是子集匹配，目标边可能是新边；且与 fallback replay 处处保留的 LWW 语义自相矛盾；post-apply census 复查看不出来（覆盖后组是一致的）→ 静默数据损坏 | ✅ 改为逐字段 LWW（`take_source` 时间戳比较），**永不**整体 `+= properties`（那会连 group_id 一起搬回旧值）；返回值新增 `applied_source`/`kept_target` 可审计。变异负控 M3 锁死 |
| 3 | MEDIUM | **`_APPLY_NULL_EDGE_BACKFILL` 造重复同身份边**：NULL 边回填时若 (u,c) 上已存在 `{group_id}` 兄弟边，裸 SET 产出两条同身份边，业务 MERGE 之后随机命中其一 → 分数漂移 | ✅ 加去重守卫：有兄弟边则 LWW 合并后删除 NULL 边，无兄弟边才 relabel；返回 `relabeled`/`merged_into_sibling` 分列。变异负控 M4 锁死 |
| 4 | MEDIUM | **fallback replay 组派生与主写路径不同构**：主路径 `memory_service._vault_scoped_group_id()` → `get_current_vault_id()`；replay 无 ContextVar 时落**字面量 `"default"`**。G2-3 前这会 clobber 主概念（已知破坏形态），G2-3 后变成"恢复的分数写进主 vault 读不到的平行组"= 恢复静默无效 | ✅ `_build_group_id_from_canvas` 改为镜像主路径（`get_current_vault_id()` + canvas 二级，D16 规约）。**残留移交 G2-2**：跨 vault 切换后重放旧 vault 条目仍归新 active vault——落盘条目本身不带 vault 维度，根治需 VaultScope + 条目补字段，已写入代码 docstring |
| 5 | HIGH | **解析链正向分支零测试覆盖**：门 4 全传显式 group_id（分支 1），fail-closed 门只覆盖解析失败；ContextVar（分支 2）与 canvas_path 推导（分支 3）无正向端到端覆盖——而生产主管道恰恰全靠这两支（memory_service 的 canvas 写入、canvas_service create/delete edge 只传 path） | ✅ 新增门 5 两条：`test_group_resolved_from_contextvar_branch`、`test_group_resolved_from_canvas_path_branch`。变异负控 M6/M7 锁死（打断任一分支即红） |
| 6 | MEDIUM | **fail-closed 门无鉴别力**：对凭空 ID 断言 False 无法区分"拒绝"与"降级执行了但没找到目标"；把 guard 换成静默 DEFAULT 降级（契约明令禁止、破坏面最大的回归）测试仍绿 | ✅ 三重加固：①目标改为真实存在的边/关联；②**同 ID 在 DEFAULT 组另布 canary**（降级会精确命中并删掉它）；③断言四次拒绝都留下 `fail-closed` 错误日志。变异负控 M2/M5 从假绿转为能红 |
| 7 | MEDIUM | **unit fail-closed 测试完全空转**：JSON fallback 对任何未知 ID 本就返 False，把三个 guard 整体删掉测试照样过 | ✅ 改为先建真实关联，再断言无 scope 调用后 store **逐字节不变** + ≥3 条 fail-closed 日志 |
| 8 | MEDIUM | **fallback replay 门写序盲区**：单键 clobber 只在"库里已有他组同名节点"时显形；只承担第一笔写入的函数退回单键也测不出 | ✅ 改为两个 replay 函数**各承担一次第二笔**（scoring A → learning B → scoring B → learning A），并断言组内 LWW 生效、组间零串写。变异负控 M8 锁死 |
| 9 | MEDIUM | **`_CLEANUP_QUERIES` 不覆盖回归态残留**：门 4 要抓的回归恰恰产出无 group_id、只有前缀 path/id 的 Canvas/Node/Episode——三条清理全不匹配，残留永久滞留共享 7692 容器，回归修好后重跑仍假红 | ✅ 补 4 条清理（Canvas by path / Node by id / Episode by SCORED 反查 / 无组孤儿 scoring Episode） |
| 10 | MEDIUM | **迁移器破坏性 prune 分支无测试**：seed 缺"NULL 组概念 + 带组边"这一唯一触发形，`_APPLY_PRUNE_ORPHAN`（DELETE）在真正对存量库 apply 时才首次运行 | ✅ seed 补形 ④，并断言 prune 真的触发（`prune_orphan` action 出现 + NULL 壳消失 + 边被新组节点接住） |

**被反驳的 4 条**（3 视角裁决判为不成立或不达严重级，如实记录）：
- 7691 硬拒是可绕过的子串启发式 —— 裁决判反驳；但**仍按防御深度加固**为端口解析（`targets_live_db()`，无端口/畸形 URI 一律按现网拒），并加 8 条参数化门（含 `:07691` 等价写法）。变异负控 M9 锁死
- `add_edge_relationship` 丢弃 `EdgeRelationship.group_id` —— 裁决判该字段在该链路非权威来源
- 删除时重新推导组会因上下文漂移孤立边 —— 裁决判相对 G2-3 前的**无 scope 全库删**不构成回归
- fallback replay 归属桶不同（与 #4 同源）—— 单独一票因会话额度中断，主发现 #4 已确认并修复

**变异负控（防假绿，可复跑 `backend/scripts/g23_mutation_negative_controls.py`）**：
9 类变异（写身份退回单键+SET / 删边降级 DEFAULT / 迁移器去 LWW / 迁移器去去重 / 关联降级 DEFAULT /
解析链两分支各打断 / fallback replay 退回单键 / 现网拒绝退回子串）**9/9 全被抓**，变异前后基线均绿。

---

## 二、Codex CLI 静态审阅（round-1）

**范围**: 卡片钦定两点（MERGE 键 null 防护 / 迁移器零写入与正确性）。
**结果**: 1 BLOCKER + 4 HIGH + 1 MEDIUM，总裁定「需整改」→ **全部处置完毕**。

| # | 级别 | Codex 发现 | 处置 |
|---|---|---|---|
| C1 | HIGH | **语义空组可绕过 fail-closed**：`group_id="   "` 被 canonical 归一为 `vault__default`（静默降级），`group_id="vault:"` 变成 truthy 的 `vault__`（空后缀垃圾组）；八方法随后照常 MERGE | ✅ **审查前已由边界实测独立发现并修复**：`_resolve_physical_group_id` 加输入 strip（空白→视为未提供）+ 输出形态校验（必须 `vault__` + 非空无空白后缀），不合格返 None 交调用方 fail-closed；6 条参数化退化输入门 + 变异控 M10 |
| C2 | MEDIUM | **`zero_writes` 不能证明零写入**：READ_ACCESS 是路由模式非访问控制；计数相等检测不到属性写与净零写 | ✅ 两条整改：①**实测澄清**——本部署（Neo4j 5.26 单实例）READ 模式会话内写查询被服务端拒绝（`Neo.ClientError.Statement.AccessMode`，实证已录）；②计数之外新增**属性敏感指纹**（Concept/LEARNED 全字段排序 sha256），`zero_writes` 现为「计数相等 AND 指纹相等」，证据 JSON 三字段并列 |
| C3 | HIGH | **`_APPLY_SPLIT` 不是按身份聚合的 LWW**：多条源边逐行 SET，结果依赖未保证的行序；重复目标边不删；`count(r2)` 只是展开行数 | ✅ 重写为**先聚合后写**：`collect` 源边 → `reduce` 选唯一 LWW 赢家 → 对唯一目标边写一次；返回 `identities/moved/applied_source/kept_target` 分列。新增多源 seed ⑧ 行为门 + 变异控 M3 |
| C4 | HIGH | **NULL-edge 去重守卫在多行下失效**：两条无兄弟 NULL 边会双双被改成同一 gid → 永久重复边，post-census 仍报零 pending | ✅ 统一形态重写：无论有无兄弟边，一律 `MERGE` 出唯一规范边 + LWW 并入 + 删除全部无组边（无兄弟时 MERGE 即等价 relabel 且天然不产重复）；另加**同身份重复边收敛 pass**（`_APPLY_DEDUPE_IDENTITY`）覆盖历史遗留重复。新增 seed ⑨（多 NULL 边）与 ⑩（预存重复边）+ 变异控 M4/M13 |
| C5 | HIGH | **空字符串 group 被当作可迁移身份**：`IS NOT NULL` 放行 `""`，空 gid 可进 MERGE 或被回填成空串，复查仍报成功 | ✅ 全部谓词改 `coalesce(trim(x.group_id),'') = ''` 口径（census/split/backfill/manual/dedupe/prune 六处）；apply 循环对空白 gid 显式 skip 并登记 action。新增 seed ⑦ 空串组门（断言空串数据原样留人裁定）+ 变异控 M12 |
| C6 | BLOCKER | **7691 防护只验证入口端口，可绕过**：`bolt://localhost:7692` 经端口转发到 7691，或路由种子转到生产 writer，均返回 False 后执行 `--apply`；端口不是数据库身份 | ✅ 加**第二道库身份闸**：`db.info()` 取 store identity（实测 Neo4j 5.26 返回 store 级 64 位指纹，与端口/主机无关）；目标身份 == 已知现网指纹（常量或 `NEO4J_LIVE_STORE_ID`）→ 拒绝；身份读不到 → fail-closed 拒绝（除非显式 `--allow-unverified-target`，须 [Decision]）；另做 best-effort 实时比对覆盖现网库重建。3 条身份闸行为门 + 变异控 M11 |

**round-1 后新增判据**：迁移器行为门 11 → 16 passed（含新增**幂等门**）；变异负控 9 → 13/13。

### Codex round-2 复核（判 6 项全 STILL-OPEN → 逐条再整改）

Codex 以冻结 patch 为准复核，判定六项均未真正闭合。逐条核对**全部属实**（部分是我在冻结点之后
才补的、部分是真缺陷），全部再整改：

| # | round-2 判定与依据 | 再整改 |
|---|---|---|
| C1 | STILL-OPEN：①显式空白仍会回退 ContextVar/canvas（落到**另一个 vault**）；②`vault::x → vault____x` 能通过输出校验 | ✅ ①显式传值但为空白 → 直接 fail-closed，绝不推导（空白是调用方 bug，不是"未提供"）；②校验改**段级**（按 `__` 切分，任一段为空即拒），`vault____x` 现被拒。门：`test_group_resolution_blank_explicit_does_not_fall_back` + 空段参数化门；变异控 M14/M15 |
| C2 | STILL-OPEN：`read_access_mode_enforced` 是硬编码；指纹漏 `next_review`/`agent_type` 等属性 | ✅ ①改**运行时探针**（READ 会话试写，拒→True；探针自清理），门测试要求它在 WRITE 会话返回 **False**——硬编码 `return True` 必红；②指纹改**全属性逐 key 展开**（`keys(n)`/`keys(r)`，Python 侧排序），不再写死字段清单。变异控 M17 |
| C3 | STILL-OPEN：并列/全 NULL 时间戳仍取无序 `collect()` 首项，赢家依赖行序 | ✅ `_LWW_PICK` 加 **elementId 字典序**兜底：时间戳并列或全 NULL 时按库内稳定唯一 id 定序，结果完全确定 |
| C4 | STILL-OPEN：无 `Concept(name,group_id)` 唯一约束时，重复**物理节点**各生成规范边，按物理节点分组的去重看不见逻辑重复 | ✅ 新增 `_DUPLICATE_CONCEPT_NODES` 检测同 (name, group) 多物理节点，**计入 manual pending**——工具在存在逻辑重复时不再报 OK。诚实边界：只检测不自动合并（合并节点要搬迁其全部关系，风险远超"身份键"范围），留人裁定。变异控 M18 |
| C5 | STILL-OPEN：census 三个计数器仍用 `IS NULL`；apply 只判 `gid.strip()` 却绑定原值 | ✅ 计数器全改 `coalesce(trim(...),'')` 口径（报表与 pending 口径一致）；apply 绑定 **stripped** gid |
| C6 | STILL-OPEN：指纹过期/env 覆盖 + 实时比对不可达时会放行；`--allow-unverified-target` 无真实 Decision 门 | ⚠️ **部分闭合 + 残余风险如实登记**：端口闸 + 身份闸双闸各覆盖对方盲区（端口闸挡不住转发、指纹闸挡不住库重建），身份读不到 fail-closed。残余：现网库重建导致常量指纹过期时，身份闸对新库失效——此时仍有端口闸。`--allow-unverified-target` 的 Decision 控制属流程约束，代码只能做到"默认拒绝 + 显式旗标 + 注明须 [Decision]" |
| 新增 Cypher | STILL-OPEN：split/backfill 只迁四个业务字段，**丢失其他 LEARNED 属性**；可能"幂等假绿" | ✅ 改为 `SET r2 += properties(best)` **全属性迁移**后立即 `r2.group_id = $gid` 钉回身份（SET 左到右生效）。新增属性保留门（`agent_type`/`source`/自定义字段全保留 + 身份键不被源边旧组覆盖）；幂等门已在 round-1 后加入。变异控 M16 |

**round-2 后判据**：裁判 60 → 64 passed；迁移器门 16 → 20 passed；变异负控 13 → 18/18。

### Codex round-3 复核（C3 CLOSED，5 项 STILL-OPEN → 再整改）

| # | round-3 判定与依据 | 再整改 |
|---|---|---|
| C1 | STILL-OPEN：`group_id=""` 因是假值绕过空白闸，仍进推导链——只封住了非空的空白串，**两种"空"行为分裂** | ✅ 守卫改为 `isinstance(group_id, str) and not group_id.strip()`：`""` 与 `"   "` 口径统一，都 fail-closed。想走推导链必须显式传 `None`。变异控 M19 |
| C2 | STILL-OPEN：①探针把**任意异常**都判作拒写（一次连接抖动就能伪造"零写入有保障"）；②`zero_writes=False` 不影响 exit 0（自证失败还报成功）。指纹整改本身已到位 | ✅ ①探针按错误码区分：只有 `AccessMode` 拒绝才返 True，其他异常返 **None（未知）**，`zero_writes` 要求 `read_enforced is True`；②dry-run 零写入结论为假 → 打印 `INTEGRITY FAILURE` 且**非零退出**。变异控 M20/M21 |
| C3 | **CLOSED** — `_LWW_PICK` 已对非空/并列/全 NULL 时间戳建立确定性全序，赢家属性整体迁移 | — |
| C4 | STILL-OPEN：`manual_total>0` 不阻止其他自动 apply，且 `MERGE (c2 {name,gid})` 面对重复节点会**多匹配扇出写入** | ✅ 对"同 (name,gid) 多物理节点"的身份**显式跳过 + 登记 action**（`*_skipped_duplicate_concept_nodes`），留人先合并节点；跳过项绝不静默略过。变异控 M22 |
| C5 | STILL-OPEN：三个循环只用 `.strip()` 判空，**绑定的仍是原始 gid** | ✅ 全部绑定 stripped 值；更进一步：`group_id` 含首尾空白本身是脏数据（绑 stripped 匹配不上库内原值＝静默空转，绑原值＝空白进身份键，**两种绑定都错**）→ 改为**跳过 + 登记**（`*_skipped_untrimmed_gid`）交人工清洗。变异控 M23 |
| C6 | STILL-OPEN：实时比对失败时依赖可能过期的常量放行；`--allow-unverified-target` 无 Decision 门 | ✅ 实时比对不可达且操作者**无显式表态**（`--live-uri` 非默认 / `NEO4J_LIVE_STORE_ID` / `--allow-unverified-target`）→ **拒绝**，不再"默认参数 + 连不上"就悄悄放行。残余（现网库重建致常量过期时端口闸仍在）如实登记 |
| 新增 Cypher | STILL-OPEN：多目标 `r2` 时 MERGE 多行展开；**去重 pass 排在 split/backfill 之后**，可能重复处理同一源集合 | ✅ 去重 pass 调整为**先行**（①去重 → ②分裂 → ③回填），配合 C4 的重复身份跳过，MERGE 面对的目标已唯一 |

**round-3 后判据**：裁判 64 passed；迁移器门 20 → 25 passed；变异负控 18 → 23/23。

### Codex round-4 复核（C1/C2b/C3/C4+Cypher/C5 全部 CLOSED，余 2 项）

| # | round-4 判定 | 再整改 |
|---|---|---|
| C1 | **CLOSED** — 空串与纯空白串均在推导前返回 None | — |
| C2b | **CLOSED** — `zero_writes=False` 令 `success=False`，退出码 2 | — |
| C4+Cypher | **CLOSED** — 去重先行，三个写分支均在 MERGE 前跳过并登记重复物理节点身份 | — |
| C5 | **CLOSED** — 三循环均用 stripped gid；非空 untrimmed gid 跳过并登记 | — |
| C2a | STILL-OPEN：除错误码外仍以**异常文本**含 `read access mode` 判 True，普通异常可伪装拒写 | ✅ 删除文本兜底，**只认错误码** `Neo.ClientError.Statement.AccessMode`（已实测 `neo4j.exceptions.ClientError.code`）。门测试加"消息含该短语但无错误码"的伪装用例（须判 None）+ "带正确码"的真拒绝用例（须判 True，防收紧过头误杀）。变异控 M24 |
| C6 | STILL-OPEN：**任意非默认但不可达的 `--live-uri` 都被当作授权表态**并放行 = 等于没有门 | ✅ 取消该口子。实时比对不可达时只认两类真实依据：① `NEO4J_LIVE_STORE_ID`（提供当前现网指纹）② `--allow-unverified-target`（[Decision] 约束）。门测试锁死"不可达 live-uri 无旗标 → 拒绝"；本卡的门测试相应改为**显式声明未验证**（诚实：它们确实不接触现网）。变异控 M25 |

**round-4 后判据**：裁判 64 passed；迁移器门 25 → 26 passed；变异负控 23 → 25/25。

### Codex round-5 终裁：**可合并** ✅

| # | round-5 判定 |
|---|---|
| C2a | **CLOSED** — 仅按错误码判定；伪装文本与真错误码两个门测试均覆盖 |
| C6 | **CLOSED** — 实时不可达时只认环境指纹或显式旗标；非默认 URI 无旗标会拒绝 |
| 新引入问题 | 仅一条**测试注释陈旧**（仍把 `--live-uri` 列为授权表态），非功能性阻断 → 已修正注释 |

**总裁定：可合并**（五轮 Codex 对抗 + 一轮内部 5 维工作流，BLOCKER/HIGH 全部清零）。

---

## 四、五轮收敛轨迹（诚实记录）

| 轮次 | 发现 | 处置 |
|---|---|---|
| 内部对抗工作流（5 维 × 3 视角，47 agent） | 14 候选 → **10 确认** | 全修（迁移器无 LWW / replay 组派生错位 / 解析链正向零覆盖 / fail-closed 断言无鉴别力 / 清理不全 / prune 分支无测试 等） |
| Codex round-1 | 1 BLOCKER + 4 HIGH + 1 MEDIUM | 全修（端口≠数据库身份 → store identity 闸；多行聚合 LWW；空串组；零写入证据强化） |
| Codex round-2 | 6 项 STILL-OPEN | 全修（显式空白不回退 / 段级校验 / 运行时探针 / 全属性指纹 / elementId 定序 / 逻辑重复入 manual / 全属性迁移） |
| Codex round-3 | C3 CLOSED，5 项 STILL-OPEN | 全修（空串口径统一 / 探针按码区分 / 零写入失败改退出码 / 重复身份跳过 / 去重先行 / 脏空白留人 / 实时不可达需依据） |
| Codex round-4 | 5 项 CLOSED，2 项 STILL-OPEN | 全修（探针删文本兜底 / 取消"任意 live-uri 即授权"口子） |
| **Codex round-5** | **全部 CLOSED** | 注释修正后 **可合并** |

判据随轮次增长：裁判 49 → **64 passed**；迁移器门 3 → **26 passed**；变异负控 9 → **25/25 全抓**。

> 诚实记录：Codex 首轮进程挂起近 3 小时零输出（已知 codex exec 挂起坑），停止后以更窄范围重跑才产出上表。本卡的另一路内部对抗审查（§一）独立于此完成。

---

## 五、裁判命令与证据

```bash
# 卡片裁判命令 — 64 passed
cd backend && .venv/bin/pytest tests/integration/test_cypher_contract_gate.py tests/unit/test_neo4j_client.py -q
# 迁移器行为门 — 26 passed
.venv/bin/pytest tests/integration/test_migrate_write_identity_g23.py -q
# 变异负控 — 25/25 能红（防假绿的可复跑证据）
.venv/bin/python scripts/g23_mutation_negative_controls.py
# 现网只读 dry-run（pending=0 + 三重零写入证据）
.venv/bin/python scripts/migrate_write_identity_g23.py --uri bolt://localhost:7691 --out <evidence>.json
# grep 清零门（后置 SET group_id 归属写法）
grep -n "SET c.group_id\|SET r.group_id\|r.group_id = CASE" \
  app/clients/neo4j_client.py app/services/fallback_sync_service.py   # 期望 0 命中
```

**证据包**：`_bmad-output/审查/evidence-g23/g23-live-7691-dryrun.json`
（现网实测 `pending=0` / `read_access_mode_enforced=true`（运行时探针）/ `counts_equal=true` /
`fingerprint_equal=true`（全属性指纹）/ `zero_writes=true`）

**零回归**：受影响面 19 个测试文件与基线 `37387a86` 逐字节对照，失败清单三轮复验全等
（77 条全为既有债务，本卡零新增失败）。
