# CARD-G2-9-F2 移交裁定请求（交主 session 人审）

> 车道 `card-t1-lance` · 2026-09-14 · 代码冻结点 **`647ef77f`**（= Codex 末轮 r5 绑定 SHA）
> 依据 D-15：「轮次上限 5，第 5 轮仍有 HIGH → 停下交主 session 人审」+
> 「车道对 HIGH 的驳回要写理由但**不能自判通过**，裁定前该卡按未完成」。
> 本文件只提出裁定请求与证据，**不做任何自判**。验收单全文见
> `_bmad-output/验收单/UAT-CARD-G2-9-F2-2026-09-14.md`。

---

## 〇 一页速览

| 项 | 值 |
|---|---|
| 代码树 | `08100483` → **`647ef77f`**（2 文件，+1472/−102） |
| 文档 commit | `e0f0a9e1`、`30abf561`（纯 `_bmad-output`，代码树零差异 ⇒ **终审绑定成立**） |
| 门文件 | 16 → **32** nodeid，末态 **32 passed** |
| 邻近六套件 | 开工 118 passed / 收工 118 passed |
| `tests/unit` 目录级 | 红集 64 vs 基线 64，**diff 空** |
| 负控 | **17 段全红**，跑前跑后 shasum 逐字节相同 |
| Codex | r1→r5，末轮绑最终 HEAD：**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 1** |
| 是否 push | **否** |

---

## 一 裁定点 D-T1A-1：judge 1 未达成（`grep` 计数 0 → 实测 1）

### 事实

- 卡文核心裁判 1：`grep -cF 'startswith(f"{vid}_")'` 改前 3 → **改后 0**
- 实测末态：**1**，唯一命中在 `_has_vault_prefix`（`lancedb_client.py`）

### 为什么没做到 0

Codex r1-HIGH-4 实测出一条**生产活路径**：`index_vault_notes` 解析表名后把结果传给
`add_documents`，后者**再解析一次**。若按卡文把 `resolve_table_name` 的幂等守卫也换成归属
判定，则库里一旦存在 id 更长的 vault（`a` 与 `a_vault` 并存），`a_vault_notes` 第二次解析会
变成 `a_a_vault_notes` —— **删除走旧名、写入走新名**，而指纹照常更新，之后的增量索引会把该
文件判成「未变更」。这是比原缺陷更隐蔽的数据面问题。

因此守卫必须保持**纯命名判据**（`resolve(resolve(x)) == resolve(x)` 要无条件成立），
那处前缀判断只能留在 `_has_vault_prefix` 内。

### 车道做了什么 / 没做什么

- **没有**改写拼法去规避那条 grep（那等于把判据做成摆设）
- **另出 AST 替代判据**并落档 `evidence-g29f2/judge1-substitute-20260914T203954.txt`：
  ① `_owns_table` 末句经 `_table_owner` 得结论、体内不直接用 `_has_vault_prefix`；
  ② `_has_vault_prefix` 的调用方**恰为** `{_table_owner, resolve_table_name}`；
  ③ 自带验伪锚（人造「朴素前缀归属」函数被判不合规）⇒ 判据不是恒真摆设
- Codex r3 独立判断：「**命名幂等与完整归属判定的区分成立**……失去证明力的是该字面 grep 判据」

### 请裁

- **(甲)** 认可替代判据，judge 1 按「口径已被 HIGH-4 推翻」记录，不阻断；
- **(乙)** 要求恢复 judge 1 = 0（则必须接受 HIGH-4 那条回归，车道不建议）；
- **(丙)** 其他。

---

## 二 裁定点 D-T1A-2：与卡文 (c) 的两处口径差异

| # | 卡文写的 | 本卡做的 | 依据 |
|---|---|---|---|
| 1 | 规则含 `t == v` 一支 | **删掉该支** | 它既**扩大**认领面（`_owns_table("file_fingerprints","file_fingerprints")` 改前为假、加上变真 ⇒ `drop_vault_tables("file_fingerprints")` 会删掉 default 的变更检测基线，直接推翻「只减少认领」），又**判错主人**（表名恰等于某 vault id 只可能是别人拼出来的：`a_b` 是 vault `a` 的逻辑表 `b`）。Codex r4 复核：「删除 `name == vid` 不会使当前命名器生成的该 vault 真表无人认领」 |
| 2 | `resolve_table_name` 守卫改归属口径 | **改回纯命名判据** | 见 §一 |

两处均有门锁住（`test_owns_table_does_not_claim_name_equal_to_vault_id`、
`test_resolve_table_name_stays_idempotent_with_longer_vault`）与负控（NC4 / NC5，各红在指定断言）。

**请裁**：接受这两处偏差（车道倾向），或要求回到卡文字面口径。

---

## 三 裁定点 D-T1A-3（**最重要**）：末轮 2 条 HIGH 的处置

Codex r5 原文归类：
> **BLOCKER：该级别无。仍有两项 HIGH，均与 B14_BASE 同态，属于既有误删边界；未发现本卡新增 HIGH 回归。**

### 3.1 r5-HIGH-1 —— **车道实测：可闭合，且不破任何门**

**问题**：模糊表名拒绝闸（r4-H1 的整改）只加在 `drop_vault_tables`，**没加到启动自愈
`_cache_tables`**。于是「`a_b` 目录不可见 + 无指纹表 + `a_b_canvas_nodes` 有维度漂移」时，
`a` 的启动自愈仍会 drop 掉它。⇒ 这是**本卡修复自身的覆盖不对称**，不是定义域极限。

**提案补丁（8 行，未应用）** —— `_cache_tables` 选表时套用 drop 侧同一条规则：

```python
                logicals = set(self._canonical_logical_tables())
                prefix_len = len(f"{owner_vault}_")
                vector_tables = [
                    t
                    for t in self._tables_cache
                    if self._owns_table(t, owner_vault)
                    and not t.endswith(self.FINGERPRINT_TABLE)
                    and not ("_" in t[prefix_len:] and t[prefix_len:] not in logicals)
                ]
```

**探针实测（试打→跑→还原，代码树逐字节未变）**：

| 裁判 | 结果 | 存档 |
|---|---|---|
| 门文件 32 条 | **32 passed** | `evidence-g29f2/probe-r5high1-gatefile-*.txt` |
| 邻近六套件 | **118 passed** | `evidence-g29f2/probe-r5high1-neighbors-*.txt` |
| 代码树 sha | 前 `08f7e1ce…b6ce4` = 后 `08f7e1ce…b6ce4` ✓ | — |

> 为什么不破门③（`a_t01..a_t11` 必须被自愈）：那些表的余名是 `t01`…`t11`，**不含下划线**，
> 不触发模糊判定；门①/⑥ 的 `a_canvas_nodes` 余名是规范逻辑名，同样不触发。

**⛔ 车道没有应用它**：末轮 r5 已绑 `647ef77f`，此刻改代码 ⇒ 按 D-15「审后再改代码必再送
一轮」需要**第 6 轮**，而轮次上限是 5。改了会同时失去「有效绑定」与「轮次合规」。

**请裁三选一**：

- **(甲)** 授权**第 6 轮**（破例 +1），车道应用补丁 → 送 Codex r6 → 若 HIGH=0 即合并门通过；
- **(乙)** 补丁**移交第十五批**单独立卡，本卡按现状（HIGH 登记不阻断）合入；
- **(丙)** 主 session 在集成期自行应用该补丁并作**集成期修复独立 commit**（协议 §4.4）。

### 3.2 r5-HIGH-2 —— 车道判断为**真·定义域边界**（不建议在本卡闭合）

**问题**：配置 `LANCEDB_INDEX_TABLE_NAME=nodes` 时，vault `a_canvas` 会产生
`a_canvas_nodes`；该 vault 目录消失且无指纹表后，删 `a` 时余名 `canvas_nodes` 恰好命中规范
逻辑名，两道预检均放行。

**为什么不可解**：此时 `a_canvas_nodes` 在**两种合法解释**下都成立 —— vault `a` 的
`canvas_nodes`，或 vault `a_canvas` 的 `nodes`。表名本身信息量不足，任何表名启发式都给不出
正确答案；要闭合需要**表级归属元数据**（写表时落 `owner_vault`），属设计级改动、超本卡范围。

Codex 自己的归类：「**基线既有边界。** `08100483` 的朴素 `a_` 前缀同样会删除此表」。

**请裁**：按「登记不阻断 + 移交（表级归属元数据）」处置（车道倾向），或另有指示。

---

## 四 其余登记项（不需裁定，只需登记）

| # | 条目 | 来源 |
|---|---|---|
| 1 | `DELETE /index/{vault_id}` 把「拒绝 / 全部删除失败 / 本来没有表」混成同一个 404，部分失败仍回 200 | Codex r2/r3/r4/r5 一致判为**消费端移交**（本卡禁改 `backend/app`） |
| 2 | r5-M1 历史逻辑名（`a_custom_nodes`）导致误拒或残留 | 超轮次上限未修 |
| 3 | r5-M2 `LANCEDB_INDEX_TABLE_NAME` 以 `_file_fingerprints` 结尾会造出伪 vault 并阻止合法删除 | 超轮次上限未修 |
| 4 | r5-LOW 钉住上下文不支持嵌套（内层退出会提前解除外层） | 当前两条破坏性路径互不嵌套，是**未验证前提** |
| 5 | `:3825` 残余默认分页站点，末态实测 `:1152 / :1382 / :4127 / :4136 / :4240`；其中 `_fingerprint_table_exists` 本卡已收口，**其余四处登记不阻断** | 卡文 (h) |
| 6 | `drop_vault_tables` 契约变化：返回值「尝试数 → 实删数」+ 四道整次拒绝闸 + 两个诊断字段（**目前无生产消费方**） | 本卡 |
| 7 | 收工工作树剩 4 个未跟踪临时标记（`sentinel` 0 字节 + 3 个点文件），`rm` 被 guard hook 拦下，未绕过 | 与手册 §四.5 的 U6 先例同型 |
| 8 | 本卡 **5 个代码 commit**（卡文写「单独一笔」）：r1~r4 每轮整改必须落在 Codex 绑定 SHA 之后另起 commit，否则末轮绑定不成立 | 主 session squash 时按卡合并 |
| 9 | **两次空门**（`…listing_fails` / `…pinned_vault_ids…`）由负控抓到并修复 —— 建议写进协议 §2.2「判据必须自证会红」 | 本卡 |
| 10 | r2 **存档**含 1 处协议 §2 禁用措辞 —— 系 Codex 自己在结论正文所写，非 prompt；存档保持逐字原样。五份 **prompt** 四词计数全 0（带验伪锚） | 本卡 |

---

## 五 合并门自评（对照手册「阻断级 = 0 即可合」）

| 阻断级项 | 本卡状态 |
|---|---|
| 数据丢失 | 本卡**关闭**互前缀跨 vault 删表面；r5 两条 HIGH 经 Codex 归类为「与 B14_BASE 同态，非本卡新增回归」 |
| live vault / 7691 / 7687 写入 | 零（现网四个 LanceDB 目录 `-newer sentinel` 全 0，带验伪锚；`fsrs_bridge`/`decay_beta` 零命中） |
| 安全 | 无涉及 |
| 指定裁判红 | 门文件 32 passed、邻近 118 passed、`tests/unit` diff 空 |
| 负控假绿 | 17 段全红；**两次自查出的空门已修复并复跑转红**（窄口径「负控本身谎报 PASS」= 无） |

⚠️ 以上是**对照表**，不是自判结论。D-15 明确「裁定前该卡按未完成」。
