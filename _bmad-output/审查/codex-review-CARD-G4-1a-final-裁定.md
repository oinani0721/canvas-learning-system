# Codex 收敛确认 · CARD-G4-1a（final round）

> 模型: gpt-5.6-sol · effort=high · sandbox=read-only · **单线程**（提示词显式禁派生子 agent）
> 日期: 2026-08-30 · 被审 HEAD: 18a5bbc8ad02b2bfb41448d4f0e81be99354f452

## 为什么这轮改成单线程窄范围

round-2 / round-3 用 ultra + 并行子 agent，**两次都在子 agent 汇总阶段被外部内容
过滤中断**（第二次已按经验改过措辞仍触发 ⇒ 触发点在汇总而非提示词）。本轮显式
禁止派生子 agent、收窄到 5 个可判定问题、要求短输出，顺利跑完并给出裁定。

## 问的 5 件事

1. inheritance 邻居查询三 alias（n / neighbor / r）是否都**严格**过滤（不容忍 NULL）
2. client 的 `get_review_suggestions` / `get_learning_history` 是否已无「不传作用域就不过滤」分支
3. `require_read_group`：(a) ContextVar 有值按「显式」处置（不误伤 deprecated 兼容层）
   (b) 只有推导落 default 桶才 fail-closed
4. 强化后的门是否在**一次读的同一结果集**上同时锁住「本 vault 四类子组全在」与「他 vault 一条不在」
5. 真库门实跑是否 49 passed

## 裁定（Codex 原文）

```
1. PASS — n、neighbor、r 均调用默认 `allow_null=False` 的严格 `read_group_filter`。
2. PASS — 两方法均无条件调用 `read_scope_params`，JSON fallback 也强制 `require_read_group`。
3. PASS — ContextVar 非默认值按 `explicit=True` 校验；仅 active-vault 推导分支对未配置的 default 桶 fail-closed。
4. PASS — 单次读取后断言 `got == _A_SCOPE_EXPECTED`，同时锁定四类本 vault 数据完整且他 vault 数据不存在。
5. PASS — 指定命令实跑结果为 `49 passed, 10 warnings in 2.60s`。
裁定: 可合并
```

## 与前三轮的关系

| 轮次 | 模式 | 状态 | 产出 |
|---|---|---|---|
| round-1 | ultra + 并行 | 完整 | 13 条（3 BLOCKER + 4 HIGH + 4 MEDIUM + 2 LOW）→ 全闭合 |
| round-2 | ultra + 并行 | **中断** | 2 条反证 → 全闭合 |
| round-3 | ultra + 并行 | **中断** | 3 条反证 → 2 修 + 1 登记为已知边界 |
| **final** | **high + 单线程** | **完整** | **5/5 PASS，裁定「可合并」** |

本轮只确认**收敛状态**，不重复前三轮的全面扫描——前三轮的深度发现与逐条处置
记录在 `codex-review-CARD-G4-1a.md` 与 `codex-review-CARD-G4-1a-round1-整改记录.md`。

⚠️ 如实声明：本轮的覆盖面窄于 round-1（5 个定点问题 vs 全面扫描）。它闭合的是
「前三轮所有发现是否真的修好了」这个问题，**不等价于**一次全新的全面审查。
