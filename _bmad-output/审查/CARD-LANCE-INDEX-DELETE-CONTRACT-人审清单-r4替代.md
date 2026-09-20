# CARD-LANCE-INDEX-DELETE-CONTRACT — r4 人审替代清单

> 用途：Codex r4 因**配额用尽**无法完成（证据 `evidence-lance-index-delete/codex-r4-quota-blocked-*.txt`，
> 含最小探针复测自证）。按协议 §2.1「再 0 字节 → 主 session 人审替代，不等配额」，本文件是
> 人审的输入。⛔ 本卡**不自判通过**。
>
> 审查绑定：`1610f01b`（r3 审过的 SHA）→ `f6ea5006`（最终 HEAD）
> 读取面：`git --no-pager diff --no-color 1610f01b f6ea5006 -- . ':(exclude)_bmad-output'`
> 规模：**2 文件，116 插入 / 37 删除**。

---

## 一 r3 之后只改了一件**行为**，其余全是说明同步

| # | 面 | 性质 | 审什么 |
|---|---|---|---|
| **A** | `rebuild_index`：删旧指纹表后**立刻**补一张空的 + 整个重建包 `try/finally`，退出路径再补一次 | **行为改动** | 见 §二 |
| B | `DropVaultReport` docstring：「两个消费方零改动」→ 改正为「`index.py` 已改调 report，零改动的只有 canary」 | 说明（我写错的**事实陈述**） | 核事实 |
| C | 形态核 docstring：「缺列 ⇒ 排除」→「缺列**保留**；带 `vector` 才排除**并置降级**」 | 说明 | 与代码一致否 |
| D | 配置守卫 `logger` 文案：不再统一说「模糊表名闸」，改为按情形分述 | 说明 | 三种情形是否穷尽 |
| E | 来源③ docstring：区分「本卡补建之后」与「历史存量」 | 说明 | 边界是否如实 |
| F | M2 门 / 重试门 docstring：终态与代价描述同步 | 说明（测试侧） | 与断言一致否 |

**B–F 全部是 Codex r3 LOW-1 点名的「说明落后于行为」。** 若人审只想看风险，只需看 **A**。

---

## 二 唯一的行为改动：`rebuild_index` 的指纹表窗口

### r3 指出的问题

r2 的修法把补建放在**正常返回路径**上，覆盖不到：

1. `progress_callback` 抛异常 / 任务被取消 ⇒ 直接越过补建；
2. 即便最终会补，重建**期间**（`index_vault_notes` 要向量化，有 `await` 让出点）指纹表也是缺的
   —— 另一个客户端此时跑 drop 或启动自愈就能认领这个 vault 的内容表。

### 现在的实现

```
drop_table(fp_table)            # 旧指纹表
drop_table(table_name)          # 主内容表
_ensure_vault_fingerprint_table()   # ← ① 删完立刻补一张空的（窗口压到最小）
try:
    await index_vault_notes(..., force_rebuild=True, progress_callback=...)
finally:
    try:
        _ensure_vault_fingerprint_table()   # ← ② 退出路径兜底
    except Exception as e:
        logger.error(...)                   # 不让补建的失败掩盖正在传播的异常
```

### 人审请重点核的三点（这三点我**没有**证据，只有推理）

1. **① 真的把窗口收窄了吗**：`_ensure_vault_fingerprint_table` 自己要读 schema 再 `create_table`，
   那之间仍有失败面。
2. **`index_vault_notes` 的 `force_rebuild=True` 会不会把这张空表又删掉？** 若会，① 等于白做，
   `finally` 那次是唯一屏障，窗口没收窄。**我没有逐行追这条。**
3. **`finally` 用 `except Exception`**：`CancelledError` 在 3.8+ 继承 `BaseException`，不会被它捕获。
   这是有意的（不吞取消），但请确认这个选择对。

### 门与负控

- 门：`g29f1::test_rebuild_index_keeps_the_fingerprint_table_when_the_rebuild_itself_blows_up`
  （`progress_callback` 抛异常制造退出路径；承重断言是 `a_canvas_nodes` 经短 vault `a` 的
  drop 与 `_cache_tables()` 后**仍在、行数不变**）。
- 负控⑧：退回 r2 态 ⇒ 该门红成
  `重建中途抛异常后指纹表没了 …; 现存 = ['a_canvas_nodes']`；shasum 跑前跑后逐字同。

---

## 三 ⚠️ 人审最该权衡的那件事（不在本次 diff 里，但是本卡的产品面取舍）

r2 HIGH-B 的修法是 **fail-closed**：指纹表名被一张带 `vector` 的表占住时，
`_looks_like_fingerprint_table` 排除它的**同时置 `_vault_registry_degraded`**。

**代价**（已写进代码注释与验收单 §四 ⑯）：

- 任何带 `vector` 且名字以 `_file_fingerprints` 结尾的表，会让**所有 scoped vault** 的
  删索引与维度自愈都停（default／空口径不受影响 —— 它们本来就跳过降级闸）；
- **只改回配置不会移除已有的占名表**，降级会**持续**，运维必须改表名或删表；
- 本卡**没有提供退出降级的工具**。

我的判断是「可见地停」优于「静默删掉别人的表」，但这是产品面的取舍，**请主 session 裁**。

---

## 四 为什么「r3 已修完」推不出「r4 会是 0 HIGH」

| 轮 | B/H/M/L | 抓到的是 |
|---|---|---|
| r1 | 0/**2**/4/3 | 实现缺陷 + 三条**过强主张** |
| r2 | 0/**2**/0/2 | **r1 修复引入的新耦合**（形态核 × 存在性早退互相抵消） |
| r3 | 0/**1**/0/3 | **r2 修复只覆盖了正常路径**（异常/取消 + 重建期间窗口） |

三轮都不是重提，**每一轮都在前一轮修复所开出的新面上**。根因是：卡文把
「建表即建指纹表」写成了一个钩子，而它实际是一个**不变量**（scoped vault 只要有内容表，
就必须有指纹表），不变量要求堵住**所有**会破坏它的路径。

⇒ 人审时建议直接问：**「这道保护现在还有哪条路径上不生效？」** 已知仍不生效的两条
（都已登记、本卡未改）：

1. `partial` 终态：指纹表删成功、内容表删失败 ⇒ 又变成「有内容、无指纹」（**基线既有**）；
2. `initialize()` 先跑 `_cache_tables()`，早于任何写入钩子 ⇒ 不能声称
   「任何破坏性路径之前指纹表必已建成」。

---

## ⚠️ 本清单的审查面已变更（2026-09-19 更新）

原清单绑定 `f6ea5006`（r3 之后）。本轮内部对抗审查后 P1-B 代码**又改了一次**，
按 D-15「审后改代码必再送一轮且当前 HEAD 重跑全套裁判」，人审替代也须绑新面。

### 新增需审的 diff

```
git --no-pager diff --no-color f6ea5006 HEAD -- \
  backend/lib/agentic_rag/clients/lancedb_client.py \
  backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py
```

= `dcc9589e` 一个 commit，2 文件 +66 行，内容是**指纹表归属闸**：
`_ensure_vault_fingerprint_table` 新增 `_table_owner(fp_table, vid) != vid ⇒ 不建也不认领`。

### 审这段时请重点核

1. 归属闸放在 `_fingerprint_table_exists()` 判断**之前**是否正确 —— 已存在且形态合格时
   直接 return 与「归属不是自己就 return」两条早退的先后顺序，有没有输入使结论不同。
2. 该闸让「建表即建指纹表」这条不变量在**命名空间碰撞的 vault 上不成立**（有意为之，
   因为强行成立会毁对方数据）。这个例外是否在 docstring / 验收单里说清楚了。
3. 新门 `test_ensure_fingerprint_refuses_a_name_owned_by_another_vault` 的**控制组**
   （`a_file_file_fingerprints` 必须建得出来）是否真的能在钩子整体失效时变红。
4. 是否有别的调用点依赖「`_ensure` 一定会建出表」这个前提。

### 当前终审绑定实测（本 session）

- P1-B 本卡 diff 面 vs HEAD：**空**（仍绑定，判据见 `evidence-lance-index-delete/serial-lane-binding-*.txt`）
- 三门文件 **95 passed**；`pyright app` **0 errors**；`tests/unit` 32 red vs 基线 33（零引入）；
  `tests/regression` **1913 passed rc=0**
- openapi.json `5e0f87b7..HEAD` 差异 **0 行**

### ⛔ 效力声明

本清单是 **Codex r4 的人审替代**，需主 session/用户认可才算数。
内部 Agent 对抗审查（`internal-adversarial-review-P1-2026-09-19.md`）**不充当** Codex 轮次。
