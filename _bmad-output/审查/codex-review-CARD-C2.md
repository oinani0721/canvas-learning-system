结论：**BLOCK，不可合入**。当前有 3 组硬约束 BLOCKER；目标测试虽为 `5 passed`，但没有覆盖这些反例。

审查快照：`card/l1-crossvault@ec2b545470b3e89cbde4e706bd1e41b3d1b5ac0f`。`router.py` 的 tracked diff 确实只有 import/include 两行。

## BLOCKER

1. **畸形 `generated_at` 可让全局 500。**  
   [review_overview.py:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:106)

   `datetime.fromisoformat()` 接受 `9999-12-31T23:59:59-23:59`，随后 `astimezone()` 抛 `OverflowError`；代码只捕获 `ValueError`。异常逃出 `_vault_entry`，再从 line 142 的列表推导逃出 `_collect`。真实生产入口探针：

   - `GET /api/v1/review/overview` → **500**
   - 同一路径的 page 端点也调用 `_collect()`，因此会遭遇相同异常。

   违反“generated_at 畸形按 stale”及“单库坏账全局绝不 500”。

2. **畸形类型/格式可冒充今日新鲜投影。**  
   [review_overview.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:68)

   任意值先经 `str()`，随后使用宽松 ISO 解析。实测以下同日值均返回 `status=ok`：

   - JSON 数字 `20260825` → `"20260825"`，Python 3.14 将其解析为当天日期；
   - `"2026-08-25"` 纯日期；
   - `"2026-08-25T10:00:00"` 无时区时间。

   A2 生产器固定输出带时区的秒级时间戳，见 [daily_review_pick.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_pick.py:273)。上述输入应判 stale，而不是 ok。

3. **没有 schema v3/嵌套形状门禁，形状垃圾大量被标为 ok。**  
   [review_overview.py:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:52)

   代码只验证根节点是 dict，不验证 `schema_version == 3` 或冻结字段类型。真实文件探针结果：

   - `schema_version: 2` → `ok`
   - 仅含 `generated_at` → `ok`
   - `stats: []` → 被 `or {}` 吞掉，`ok`
   - `due_nodes: "garbage"` 且 stats 缗失 → `due_count=0, ok`
   - `stats.due_nodes: "99"` → 静默改用明细长度，`ok`
   - `stats.due_nodes: true` → 因 `bool` 属于 `int`，保留为 `true`；page 的 `int(True)` 显示 `1`
   - `ineligible.placeholder: "abc"` → 当作长度 3，`ok`
   - 非标准 JSON `NaN` 可被 `json.loads` 接受；生产入口返回 200 并归一化成 `null`，仍未标 corrupt

   这同时违反“只消费冻结 schema v3”和“形状垃圾必须单库 corrupt”。

## HIGH

- **settings fixture 未可靠恢复全局状态。**  
  [test_review_overview.py:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:62)、[config.py:1056](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/config.py:1056)

  `reload_settings()` 会永久写 `os.environ`，fixture 只保存有效配置值，不保存键原先是否存在。子进程探针在两键原先不存在时复现：teardown 后 `VAULTS_ROOT`、`ACTIVE_VAULT` 均从“不存在”变成“存在”。

  此外，[conftest.py:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/conftest.py:23) 已提前导入 `app.main`；reload 后 `app.main.settings` 与 `app.config.settings/get_settings()` 指向不同对象。若 line 71 reload 后、fixture 成功 yield 前 `TestClient` 构造失败，line 75 也不会执行。测试体断言失败后的常规 teardown 会运行，但以上三种污染风险仍存在。

## MEDIUM

- **测试没有真正锁住关键约束。**  
  [test_review_overview.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:78)

  - 聚合用例中 stats 数字恰好等于 `due_nodes` 长度；忽略 stats、重数明细的错误实现也会通过。
  - corrupt 用例仅覆盖坏 JSON 和根 list，没有覆盖嵌套容器、非法 due_count、权限拒绝、目录型投影或时间溢出。
  - stale 用例没有把“今日 generated_at”文件的 mtime 回拨；实现若同时额外参考旧 mtime，测试仍会通过。
  - 没有在请求前后锁定投影 exact bytes/mtime，未用测试证明只读。

## 异常路径核对

| 输入 | 当前结果 |
|---|---|
| truthy 非 dict `stats` | `.get` 异常，被捕获为 corrupt：PASS |
| falsy 非 dict `stats=[]` | 被洗成 `{}`，随后 ok：FAIL |
| 非 list `due_nodes` | 可被忽略或回退为 0，随后 ok：FAIL |
| string/bool `due_count` | 回退明细长度或 bool 被接受；不会在 page 的 `int()` 崩溃，但语义不诚实：FAIL |
| 普通不可解析 `generated_at` | stale：PASS |
| 数字/纯日期/无时区 `generated_at` | 可被标 ok：FAIL |
| 极端带时区 `generated_at` | `OverflowError`，真实端点 500：FAIL |
| 投影文件权限拒绝 | `corrupt / PermissionError`：PASS |
| 目录名冒充投影文件 | `corrupt / IsADirectoryError`：PASS |
| 缺文件/缺 outputs | 显式 `no_projection`：PASS |

## HTML 静态转义覆盖

| 动态值 | 输出处理 | 结论 |
|---|---|---|
| vault 名文本 | `html.escape` | PASS |
| vault 名 `obsidian://` href | `quote(..., safe="")` 后 `html.escape` | PASS |
| `due_count` | `int()` 数字规范化 | PASS；未调用 escape，但不能输出 HTML 元字符 |
| `placeholder_backlog` | `int()` 数字规范化 | PASS；同上 |
| `recommended_board` | `str` 后 `html.escape` | PASS |
| 投影 `generated_at` | `str` 后 `html.escape` | PASS |
| `error` | `str` 后 `html.escape` | PASS |
| status `label` | 封闭 `_STATUS_META` 常量 | PASS |
| status `color` | 封闭十六进制颜色常量 | PASS |
| `body` | 仅组合上述已处理值 | PASS |
| `cards` | 仅组合 `_card_html()` 返回片段 | PASS |
| 页面生成时间 | `html.escape` | PASS |

`status` 本身不直接输出；JSON 中的 path、active_vault、投影 vault_id/date/top_node/pending/next_upcoming 也不进入 HTML。没有未处理的文件侧字符串。页面只有内联 HTML/style；无 CDN、外链 script/style、`src`、CSS `url()` 或 `@import`。

## 其他通过项

- 只读实现：仅 `read_text`，未写文件，也未调用调度/到期计算入口；当前代码完全不读取 mtime。
- vault 候选规则与 [vault.py:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/vault.py:145) 一致：根目录直接子项、非隐藏目录、`.obsidian` 必须为目录；因此 `_bmad-output` 会被纳入。
- 路由注册无互相遮蔽。既有 GET 都有固定首段 `/history`、`/progress/...`、`/verification/...`、`/fsrs-state/...`、`/session/...`，没有根级 catch-all；实际应用路由表中 `/overview` 与 `/overview/page` 均唯一。
- 测试确实使用 `tmp_path` 真目录/真文件、真实 `reload_settings`，无 mock 文件系统。
- 实跑：`5 passed, 10 warnings in 0.62s`。这是目标文件结果，不代表完整 backend suite/CI。
- 全程未修改文件，也未读取 live vault 投影内容。`git status` 另有 out-of-scope 的 backups、验收文档和 live outputs；合入时需精确暂存，不能直接 `git add .`。

最终结论：**CARD-C2 拒绝合入**。至少需修复严格 v3/形状门禁、generated_at 的严格格式与全异常降级，以及 settings fixture 的可逆恢复，并补齐上述 hostile 回归后再审。



---

# 附录 A — 第一轮处置记录（Claude, 2026-08-25）

## BLOCKER 处置

1. **B1 OverflowError 500 → 已修（双防线）**。①stale 判定 except 扩为 Exception（fromisoformat 通过但 astimezone 溢出的 OverflowError 按 stale 降级）；②_collect 列表推导改逐库 try——单库任何未预期异常以 corrupt 条目呈现，全局绝不 500。测试 lax-overflow 用例锁定 "9999-12-31T23:59:59-23:59" 全局仍 200。
2. **B2 宽松时间冒充新鲜 → 已修**。generated_at 先过严格正则（A2 生产器确切形态：带时区秒级 `YYYY-MM-DDTHH:MM:SS±HH:MM|Z`）才解析；数字串/纯日期/无时区一律 stale。且 _summarize 拒非 str generated_at（JSON 数字 20260825 → corrupt）。测试 lax-* 四形态锁定。
3. **B3 无形状门禁 → 已修**。严格 v3 门禁：schema_version 必须 int 3（bool 拒）；stats 必须 dict 且 stats.due_nodes 必须非负非 bool int（_strict_int，type is int）；top_boards/upcoming/due_nodes 必须 list、ineligible 必须 dict、placeholder 必须 list；json.loads 加 parse_constant 拒 NaN/Infinity；违反任一 → corrupt。删除明细重数 fallback（v3 stats 是权威计数）。敌对形状 10 连测锁定（bad-version/bad-stats-list/bad-due-nodes/bad-count-bool/bad-count-str/bad-placeholder/bad-nan/bad-genat-num…）。

## HIGH 处置

- **settings fixture → 已修**。保存两键的「存在性+值」，try/finally 保证 TestClient 构造失败同样恢复；原不存在的键 pop 掉后 reload_settings()（无 overrides，只按恢复后 env 重建缓存与模块全局）。与 test_vault_switch.py 同跑验证无新增交叉污染。

## MEDIUM 处置

- 聚合用例 stats_due=7 与明细 len=1 刻意解耦（重数明细的实现必红）。
- corrupt 用例扩至 10 种敌对形状（含嵌套容器/bool/str 计数/NaN/数字 generated_at）。
- stale 用例把今日投影 mtime 回拨一周（偷看 mtime 的实现必红——runner 本就刻意回拨 mtime）。
- 新增 test_readonly_contract_files_untouched：请求前后投影 bytes+mtime 逐一断言不变。

## 复验与说明

- 裁判 6 passed；ruff 全绿；真实环境 e2e 复跑：canvas-vault ok due=6、test-vault ok due=2、_bmad-output no_projection，全局 200。
- 与 test_vault_switch.py 同跑出现的 1 failed（test_vault_id_changes_after_reload）为存量环境失败：canvas-vault/.canvas-config.yaml 存在时 settings.vault_id 优先读 yaml，reload ACTIVE_VAULT 不改其值——单独跑该文件同样失败，最后触碰是 7 月 P0-3 commit，与本卡零关系（backend/tests/unit 存量债已有记录）。
- git add 将精确按文件暂存，不 git add . （backups/ 与 live outputs 不入库）。
