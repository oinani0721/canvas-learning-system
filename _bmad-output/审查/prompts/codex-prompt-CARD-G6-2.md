# Codex 对抗性审查 — CARD-G6-2 交互复习壳 [BATCH-2026-09-01-第八批] · round-2

你是独立对抗性审查员。工作目录（cwd）已是本车道 worktree 根：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp

这是**第 2 轮**。round-1（../codex-review-CARD-G6-2.md）判 FAIL，提出 4 个 HIGH，
本轮除常规复审外，必须逐条验证这 4 条的整改是否真实、有无引入新问题。

## 被审变更（只读这些文件，其余不碰）

1. backend/app/api/v1/endpoints/review_app.py （新增 — 交互复习壳单文件 HTML）
2. backend/app/api/v1/router.py （只加了 1 行 import + 1 行 include_router）
3. backend/tests/unit/test_review_app.py （新增测试 + node --test 渲染断言）
4. ../_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py （负验证脚本）
5. 对照物（未改动，用于验证共存/不双实现）：backend/app/api/v1/endpoints/review_overview.py

本卡完整需求（卡文）在：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W5.md
如需可读。默认裁决①-⑥ 与完成条件 (a)-(g) 以卡文为准。

## round-1 四个 HIGH 的整改声明（请逐条证伪）

- **HIGH-1 刷新反馈被重绘抹掉 / detached DOM / 缺 rebuild_count**：
  整改为「持久状态 + 重绘恢复」——POST 结局写进 state.notes（vault_id → {html, atMs}，
  15s TTL，常量 NOTE_TTL_MS）；renderVaultCard/renderPage 增加 notes/inflight 入参，
  每次渲染都从状态恢复反馈；POST 完成先就地补（applyNote），就地补不到且有数据时
  renderCards 重绘恢复；rebuilt 后 poll() 重拉也不会丢反馈；同库在飞时按钮禁用是
  渲染态的一部分（重绘不会意外解锁）；debounced/in_progress/rebuilt 三个 JSON 分支
  都显示 rebuild_count（「本进程累计 N 次」）。接线行为由
  test_js_refresh_wiring_note_survives_rerender_and_inflight_guard 在沙箱里以假事件
  驱动断言（6 个子场景）。
- **HIGH-2 node 缺失时 10 门假绿 skip**：整改为 fail-closed——删除了全部
  skipif/skip 机制；node_harness fixture 在 node 不可用时直接 pytest.fail；文件结构上
  不存在任何 skip 路径；_assert_node_green 另有 skipped 非零即红的正则门。
- **HIGH-3 marker 注释欺骗**：整改为「不割取」——不再有任何按注释标记提取代码的
  通道；测试把响应里的**整个 <script> 原文**放进受控沙箱（stub document/fetch/
  setTimeout/clearTimeout）用 new Function **直接执行**，纯函数从执行后的沙箱作用域
  return 导出。注释里藏一份好代码骗提取器、浏览器执行另一份的攻击面不成立
  （执行的就是浏览器执行的同一段字节）。
- **HIGH-4 变异判据 returncode≠0 误认证 + M30 空转**：双重整改——
  (a) 变红判据改为三重匹配：pytest 退出非零 **且** stdout 含 "1 failed" **且**
  -rf short summary 里 FAILED 的是**指定的那个测试节点**（exit 4 / collected 0 /
  collection error 不再能冒充变红）；35 条变异全部重跑。
  (b) 旧 M30（`if False` 不读盘、只靠注释里的 "subprocess" 字样触发字符串黑名单）
  删除，换成两条真变异：端点里 `import pathlib`（import 白名单）与
  `open("今日复习.json").read()`（内建调用门）——由新增的
  test_review_app_module_imports_are_closed（**AST 结构门**：import 白名单 + 禁
  open/exec/eval/__import__/read_text 调用）承接，不再有「换拼法绕过字符串黑名单」的问题。

## 审查重点（按卡文，round-1 七项继续有效）

1. 零外部依赖与同源约束（url_for 注入 — test_api_paths_follow_mount_prefix_not_hardcoded
   用换前缀挂载的行为门锁「注入 vs 硬编码了恰好相同的值」）。
2. 轮询上下限与隐藏暂停；自动轮询绝不 POST refresh。
3. 四态文案不伪装 ok（_STATUS_META import 注入不复制）；stale 且 due_count=0 不许说休息日。
4. JS 内不得重算任何 due 逻辑（行为门：due_count 与明细刻意不一致的 fixture）。
5. 与零 JS 页共存不双实现（review_overview.py 零改动 git 可证）。
6. W6 三字段缺省渲染。
7. 测试与门的真实性（沙箱执行是否真的无割取通道；负验证判据是否还有误认证空间；
   NOTE_TTL/在飞防抖的接线门是否真能抓住 HIGH-1 类回归）。
8. **本轮新增**：上述四条整改有没有「修了个寂寞」「引入新缺陷」「把 round-1 的问题
   换个形态保留下来」。

## 已知边界（不算发现，已在验收单登记）

- 部署不在本卡；live 容器没有本卡路由，走查在本车道本地 server 上做。
- docker-compose.yml:202 DAILY_REVIEW_PICK 按 V3「甲」部署，用户是否本人作答待确认。
- G6-1 的 D-3（板序）/D-6（配对原子性）按卡文不吸收，只登记移交。
- snooze / 完成反馈是 G6-6/G6-7 地盘，本卡不做。
- Host 白名单/同源门（_assert_same_origin）在 refresh 端点上（G6-1 已有），本卡 JS
  发的是同源 fetch，预期通过。
- 本页无鉴权依赖 refresh 端点的既有同源门；GET 侧只读，无新暴露面。

## 输出格式

按严重度分级：BLOCKER / HIGH / MEDIUM / LOW。每条给出：文件:行号、问题、为什么是
问题（具体失败场景）、建议修复。对四条整改逐条给出 VERIFIED / NOT VERIFIED + 理由。
没有问题的维度明确说「未发现」。最后给一行总结论：PASS 或 FAIL（存在未清零
BLOCKER/HIGH 即 FAIL）。
