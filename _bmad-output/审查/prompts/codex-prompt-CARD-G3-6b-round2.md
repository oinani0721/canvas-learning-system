# 对抗性审查 round-2: CARD-G3-6b [BATCH-2026-09-01-第八批]

你是独立对抗审查方, 这是 round-2。round-1 报告 (_bmad-output/审查/codex-review-CARD-G3-6b.md)
判 FAIL (1H/4M), 本轮复核整改。车道 (git worktree, 分支 card/w6-whyboard):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
下称 LANE。基线 commit = 9af18b27。卡文:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W6.md

## round-1 → round-2 整改清单 (逐条回应)

- [HIGH] 因子序双真相源 → **已修 (构造性)**: 新常量 `TIE_FACTOR_KEYS`;
  `_tie` 排序键改为 `tuple(tie_parts[k] for k in TIE_FACTOR_KEYS)` 逐键派生
  (daily_review_pick.py rank_boards), `effective_rank_config` 摘同一常量。
  交换常量位置 → 排序与指纹同变。新门 `test_g36b_tie_keys_are_single_source`
  (交换 1↔3 位: 板序翻转 + sha 同变, 双断言)。
  你的攻击场景 (内存交换 blr/min_last) 现在必然同时改排序与 sha。
- [MEDIUM] 金样覆盖不足 → **已修**: `test_g36b_tie_pick_level_decides`
  (pick 级)、`test_g36b_tie_removing_min_last_level_flips_order` (删除第三因子
  序翻转, fixture 浮点配平: 两板 top 同参同 idle 保 pick 平, Z 板第二节点
  pick≈0.224>0.1536 不夺 top 只拉 min_last)、单源门的 blr×board 优劣相反构造。
  注意一个数学事实 (已在测试 docstring 声明): min_last 更老 ⟺ 板内存在更老
  节点 ⟺ 该节点 σ 更大 pick 更低, 故 min_last 级只在 pick 严格平局时可达,
  平局构造要求 top 同参同 idle —— 每级独立 fixture 是可达的最全覆盖。
- [MEDIUM] 未来 blr 日期 clamp 成 0 → **已修**: `_board_factors` 不再夹负;
  模板新分支「上次推荐日期晚于今天」(S4 docstring 同步);
  `test_g36b_future_recommend_date_is_not_disguised_as_today` (gap=-2 原样上抛)。
- [MEDIUM] 消费端单边缺省仍渲染 → **已修**: 渲染改原子对
  (`if why and mins is not None`, review_overview.py _board_table_html);
  新门 `test_g36b_one_sided_explain_fields_render_nothing` (两个单边方向)。
- [MEDIUM] authoritative 缺键静默 → **已修**: 缺键与非法统一点名
  「缺失或非法(...)」; `test_g36b_missing_or_corrupt_manifest_degrades_honestly`
  补半份配置断言 (只给 per_due_node → per_new_node 点名回落)。
- 你 round-1 的范围备注 (untracked 的 prompt/report/stderr/UAT): 这些是卡文
  「收尾」节明令生成的产物, 属预期; live 14 节点单值取值分布已由开工时
  grep 实测 (sort|uniq -c 输出在验收单), 你可用同法独立复核。

## 本轮任务

1. 逐条验证上述整改真伪 (可自行构造输入实测, 不要只读代码相信注释)。
2. 对新引入的 `TIE_FACTOR_KEYS` 单源机制做对抗: 找「排序变了 sha 不变」或
   「sha 变了排序不变」的新攻击面 (注意: 排序键值本身 pick/blr 字符串变化
   引起的正常序变不需要 sha 变 —— sha 摘的是**因子配置**不是数据)。
3. 检查整改是否引入回归 (126 passed 基线: pick 65 + overview 61)。
4. round-1 已判 PASS 的项 (D 全项 / A 大部) 不需重审, 除非整改波及。

## 输出格式

对每条发现: [BLOCKER|HIGH|MEDIUM|LOW] + 文件:行号 + 问题 + 建议修法。
末尾总裁决: PASS / FAIL。没有发现也要明说哪几项查了什么。不要复述代码。
