# Codex 对抗性审查 — CARD-G6-2 交互复习壳 [BATCH-2026-09-01-第八批]

你是独立对抗性审查员。工作目录（cwd）已是本车道 worktree 根：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp

## 被审变更（只读这些文件，其余不碰）

1. backend/app/api/v1/endpoints/review_app.py （新增 — 交互复习壳单文件 HTML）
2. backend/app/api/v1/router.py （只加了 1 行 import + 1 行 include_router）
3. backend/tests/unit/test_review_app.py （新增测试 + node --test 渲染断言）
4. 对照物（未改动，用于验证共存/不双实现）：backend/app/api/v1/endpoints/review_overview.py

本卡完整需求（卡文）在：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W5.md
如需可读。默认裁决①-⑥ 与完成条件 (a)-(g) 以卡文为准。

## 审查重点（按卡文）

1. **零外部依赖与同源约束**：页面必须零 CDN/零外部 URL（只允许 obsidian:// 深链与本机相对路径）；JS 只 fetch 同源 GET /api/v1/review/overview 与 POST /api/v1/review/overview/refresh；两个路径必须来自 request.url_for 注入而非硬编码（注意：test_api_paths_follow_mount_prefix_not_hardcoded 用换前缀挂载的行为门锁这件事 —— 请验证该门真的能区分「注入」与「硬编码了恰好相同的值」）。
2. **轮询上下限与隐藏暂停**：周期 = clamp(最近未来 upcoming.next_due − now, 5s, 60s)；页面隐藏暂停、回前台立即拉；自动轮询绝不 POST refresh，只有手动按钮 POST。
3. **四态文案不伪装 ok**：ok/stale/no_projection/corrupt 徽标字面必须来自 review_overview._STATUS_META 的注入（不复制第二份）；unavailable 是前端第五态（fetch 失败/非 200/JSON 坏 → 横幅 + 保留旧数据，不白屏）；stale 且 due_count=0 不得显示休息日文案。
4. **JS 内不得重算任何 due 逻辑**：谁到期/计数/排序只能消费投影字段（due_count 权威口径、boards[].due、next_upcoming）；humanizeDue 只是显示层格式化。请特别找「看起来像格式化、实质是判定」的越界。
5. **与零 JS 页共存不双实现**：review_overview.py 必须零改动（git 可证）；共享 helper 只 import 不复制；本模块不得出现第二套投影读取/汇总管道。
6. **W6 三字段缺省渲染**：boards[].why_this_board / boards[].estimated_minutes / 顶层 rank_manifest —— 在场才渲染，缺省整块不出现；estimated_minutes 只认有限数。
7. **测试与门的真实性**：测试是否测的是「实际响应体」而非模板副本；有没有恒真门/死门；node --test 提取区段的标记是否可被注释欺骗；负验证脚本（../_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py，30 条机械变异串行 + 逐字节还原）的判据是否真的是「指定的那道门变红」。

## 已知边界（不算发现，已在验收单登记）

- 部署不在本卡；live 容器没有本卡路由，走查在本车道本地 server 上做。
- docker-compose.yml:202 DAILY_REVIEW_PICK 按 V3「甲」部署，用户是否本人作答待确认 —— 不在本卡范围。
- G6-1 的 D-3（板序）/D-6（配对原子性）按卡文不吸收，只登记移交。
- snooze / 完成反馈是 G6-6/G6-7 地盘，本卡不做。
- Host 白名单/同源门（_assert_same_origin）在 refresh 端点上，本卡 JS 发的是同源 fetch（同 host 同 port），预期通过；若你认为前端还有必须补的门，先对照 G6-1 已有裁决再提。

## 输出格式

按严重度分级：BLOCKER / HIGH / MEDIUM / LOW。每条给出：文件:行号、问题、为什么是问题（具体失败场景）、建议修复。没有问题的维度明确说「未发现」。最后给一行总结论：PASS 或 FAIL（存在未清零 BLOCKER/HIGH 即 FAIL）。
