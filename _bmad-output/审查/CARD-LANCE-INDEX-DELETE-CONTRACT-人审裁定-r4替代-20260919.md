# P1-B r4 人审替代 — 裁定书

> 批次 BATCH-2026-09-18-第十五批 · 卡 CARD-LANCE-INDEX-DELETE-CONTRACT
> **用户授权**：2026-09-19 明确裁定「认人审替代，本批收口」（AskUserQuestion 应答）
> 依据：卡批次协议 §1「主 session 人审替代，不等配额」先例
> 审查绑定：`e3602e85`（含本轮 `dcc9589e` 归属闸）
> 阻塞实证：`evidence-lance-index-delete/codex-model-unavailable-20260919.md`

## 〇 本裁定替代的是什么

替代 **Codex r4**（绑最终 HEAD 的那一轮）。P1-B 的 Codex 实况保留如实：
**r1/r2/r3 已真跑并逐轮整改**（存档在库，首部按协议 §2.1），r4 因 `gpt-6-astra`
在当前 ChatGPT 账号返回 400 未能执行。本裁定**不追认** r1-r3 之外的任何轮次。

## 一 逐条核查（清单 §「审这段时请重点核」4 项）

### 核查项 1 —— 归属闸与存在性核的先后序 ✅ 通过

实测控制流（`_ensure_vault_fingerprint_table` 函数内相对偏移）：

```
行+37 if self._db is None: return
行+39 if not self._scope_depends_on_registry(...): return
行+41 fp_table = self._fingerprint_table_name
行+54 if self._table_owner(fp_table, _vid) != _vid: return   ← 归属闸
行+62 if self._fingerprint_table_exists():                    ← 存在性核
行+84 create_table(...)
```

穷举调换后的两类输入：

| 输入 | 现序 | 调换后 |
|---|---|---|
| 归属非己 ∧ 表已存在且形态合格 | return | return（结论同） |
| **归属非己 ∧ 表不存在** | return（安全） | `_fingerprint_table_exists()` 为 False ⇒ **穿透到 create = 缺陷复活** |

⇒ 当前顺序是**唯一安全序**，第二行正是本次要堵的路径。

### 核查项 2 —— 不变量的例外是否说清楚 ✅ 通过（本次补厚）

「建表即建指纹表」这条不变量在**命名空间碰撞的 vault 上有意不成立**。
代码侧归属闸注释块明写理由与后果；本裁定同时在验收单补一段显式声明（见 §三）。

### 核查项 3 —— 控制组能否在钩子整体失效时变红 ✅ 通过（注入实证）

负控 `negctl-3`：让 `_ensure_vault_fingerprint_table` **整体 no-op**（不是只拆归属闸）。
结果 —— 先红的是**控制组**断言，正文：

```
AssertionError: 控制组的指纹表没建出来 ⇒ 建表钩子本身坏了, 本门对归属闸无辨别力。
现存 = ['a_canvas_nodes', 'a_file_canvas_nodes']
```

即该门在「钩子整体坏掉」时**不会假绿、也不会错怪归属闸**，而是报出自己无辨别力。
还原后 shasum 逐字节同、`negctl-3` 零残留。

### 核查项 4 —— 有无调用方依赖「表一定建得出来」 ✅ 通过

全仓调用点 3 处（`lancedb_client.py` :2230 / :2250 / :4809），逐条核：
函数签名 `-> None`，**无一读返回值**；三处后续行均为日志，**无一假设表已存在**。
⇒ 归属闸的「不建」不会打破任何调用方的前提。

## 二 裁定

- **阻断级 = 0**（协议 §1 口径：无数据丢失 / 无 live vault 或 7691 写入 / 无安全面 /
  无指定裁判红 / 无负控自身谎报 PASS）。
- 本轮 `dcc9589e` 的 4 项重点核查**全部通过**，其中 2 项由注入/实测支撑，非仅读码。
- 条件 **(n) 以人审替代达成**（用户 2026-09-19 授权）。⚠️ 台账与验收单必须写明
  「以人审替代达成，非 Codex r4」，不得简写成「Codex 通过」。

## 三 随裁定必须同步的声明（已写入验收单）

> **不变量的已知例外**：「scoped vault 写过内容表就必有指纹表」在
> **命名空间碰撞的 vault**（如 `a` 与 `a_file` 并存）上**有意不成立**。
> 强行成立会让 `a` 建出归属 `a_file` 的表，造成 ① `DELETE /index/a` 永久 409
> collision、② `DELETE /index/a_file` 销毁 `a` 的指纹基线。
> 此类 vault 退回改前口径（目录不可发现时归属保护失效），**修法是改 vault id**，
> 不在本卡范围 ⇒ 台账移交。

## 四 本裁定未证明什么

1. 未证明人审替代的覆盖面与 Codex r4 等价 —— 4 项核查是主 session 自己列的清单。
2. 未证明 r1/r2/r3 之外没有新的审查面（Codex 每轮都在前一轮修复打开的面上找到新问题，
   r4 本可能延续该模式）。
3. 未在真 LanceDB 失败下复现任何发现（`drop_table` / `list_tables` 真实失败未构造）。
4. 未证明 §三 的例外在现网存在实际碰撞 vault（现网只读，未对账）。
