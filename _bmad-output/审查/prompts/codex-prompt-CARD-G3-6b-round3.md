# 一致性复核 round-3 (终轮, 同轮重试): CARD-G3-6b [BATCH-2026-09-01-第八批]

> 注: 本提示词是 round-3 的措辞中性化重试 —— 前一次运行因提示词用语被内容过滤器误拦,
> 审查任务本身 (只读复核本地测试与文档) 无任何变化。

你是独立对抗审查方, round-3 (按卡文预算是最后一轮)。round-2 报告
(_bmad-output/审查/codex-review-CARD-G3-6b-round2.md) 判 FAIL (1H/2M/2L)。
车道: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard
基线 9af18b27。卡文: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W6.md

## round-2 → round-3 整改清单 (逐条回应)

- [HIGH] 取值规则不在指纹内 (round(8)→round(7) 板序翻转 sha 不变; 绑定交换同理)
  → **双层修复**:
  a) 精度数据化: 新常量 `TIE_PICK_ROUND_DIGITS = 8`, tie_parts 的 priority_pick
     用它取整, `effective_rank_config` 登记 `tie_pick_round_digits` —— 改精度
     → 排序与 sha 同变 (门: `test_g36b_tie_precision_is_versioned` +
     `test_g36b_sha_changes_for_every_single_coefficient` 补精度/因子序变异)。
  b) 实现校验和兜底 (完备性收口): `effective_rank_config` 新增
     `implementation_sha256 = sha256(pick.py 自身字节)`。取值绑定这类无法全部
     数据化的字面代码, 任何改动 (精度/绑定/方向/新因子/注释) 都会反映到 sha。
     粒度从「系数」变「实现+系数」属预期内的保守取舍 (宁可指纹变多, 不可
     规则变更漏网)。门: `test_g36b_implementation_sha_is_registered_and_self_consistent`。
  你的「绑定交换」攻击在新机制下: 改 pick.py → implementation_sha256 变 →
  payload.rank_manifest.sha256 变。请实测复核。
- [MEDIUM] authoritative 父节缺失静默 → **已修**: 三层 (节/子节/叶键) 缺失、
  null、形状不符全部点名「缺失或形状不符(...) 用内置默认」;
  门 `test_g36b_parent_section_missing_warns_not_silent` 覆盖三种形状。
- [MEDIUM] pick 级金样不承重 → **已修**: 低 pick 移到字典序更晚的 B板,
  并断言删除首因子后按板名翻转 (test_g36b_tie_pick_level_decides 重写)。
- [LOW] 因子键唯一性 → 门 `test_g36b_tie_keys_unique_and_anchored`
  (无重复键 + board 恒末位)。
- [LOW] 验收单两处 121 → 已统一为 126。

## 本轮任务

1. 逐条验证上述整改真伪 (鼓励自行构造输入实测)。
2. 对实现校验和机制做完备性核查: 探查是否存在「排序规则变了 sha 不变」的残余遗漏面。
   已声明的设计边界 (请复核其成立性): (a) sha 摘 pick.py **运行时**源文件,
   若有人改了 pick.py 但部署链用了旧缓存/旧副本, 指纹摘的是实际运行的那份 —
   即指纹始终诚实于「真正执行的代码」; (b) decay_beta.py 的实现体不在指纹内
   (它有六常量快照+漂移告警, 本体归 CARD-G6-1b)。
3. 确认整改无回归 (当前 130 passed: pick 69 + overview 61)。
4. round-1/2 已 PASS 的项不重审, 除非整改波及。

## 输出格式

[BLOCKER|HIGH|MEDIUM|LOW] + 文件:行号 + 问题 + 建议修法; 末尾总裁决 PASS/FAIL。
没有发现也要明说查了什么。不要复述代码。
