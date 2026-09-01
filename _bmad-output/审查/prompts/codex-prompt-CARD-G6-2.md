# Codex 对抗性审查 — CARD-G6-2 交互复习壳 [BATCH-2026-09-01-第八批] · round-3

你是独立对抗性审查员。工作目录（cwd）已是本车道 worktree 根：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp

这是**第 3 轮**。round-1 判 FAIL（4 HIGH，已整改）；round-2 判 FAIL（HIGH-1/HIGH-3/HIGH-4
NOT VERIFIED + 1 个新 HIGH + 5 MEDIUM + 3 LOW）。本轮除常规复审外，必须逐条验证
round-2 各条（含 MEDIUM/LOW 的处置声明）。

## 被审变更（只读这些文件，其余不碰）

1. backend/app/api/v1/endpoints/review_app.py
2. backend/app/api/v1/router.py （1 行 import + 1 行 include）
3. backend/tests/unit/test_review_app.py
4. ../_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py
5. 对照物（未改动）：backend/app/api/v1/endpoints/review_overview.py

卡文：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W5.md

## round-2 各条的整改声明（请逐条证伪）

**HIGH-1（刷新因果一致性）** → 整改为「pendingSync 两段式 + GET 代际守卫」：
- POST rebuilt 不再声称「数字已更新」，只显示「正在同步最新数字…」，同时登记
  state.pendingSync[vid]（null-prototype 容器）。
- poll() 每次 `++state.pollGen` 取代际号；响应回来先过形状校验
  （`Array.isArray(data.vaults)`），再验 `gen === state.pollGen` —— 乱序旧响应
  （成功或失败）**整包丢弃**，不碰状态不排程；最新 GET 成功 → settlePendingSync(true)
  → 「✅ 已重建（累计 N 次）· 数字已更新」；失败 → settlePendingSync(false) →
  「⚠ 已重建（累计 N 次）· 数字同步失败，后端恢复后自动重试」。
- 新门：test_js_poll_out_of_order_discards_stale_response（两条 GET 挂起、逆序 resolve、
  断言旧响应不覆盖）+ test_js_rebuilt_sync_flow_never_claims_prematurely ①②②b
  （正在同步/成功结算/失败结算+恢复后数据照常更新且失败反馈不被洗成成功）。
  变异 M39/M40/M41 全部对准这些门。

**HIGH-3（大小写 </SCRIPT> 分叉）** → 整改为「结束符计数 + 注释开合拒绝」：
- _extract_script 用大小写不敏感的正则数 `</script\s*>` 的**总出现次数**（恰为 1）；
  正文任何位置多出结束符 → 红。不再用 maxsplit 截断（round-3 自查：截断式提取会把
  注入的结束符当切割点吞掉，canary 恒不触发 = 死门）。
- 正文出现 `<!--` / `-->` → 红（tokenizer script-data-escaped 状态分叉面）。
- 开标签大小写不敏感地只允许一个且恰为字面 `<script>`。
- 新门 test_script_extraction_rejects_case_insensitive_terminator 对三种毒化样本
  （`// </SCRIPT>`、`</script >`、`/* <!-- */`）断言必抛。变异 M38 对准它。

**HIGH-4a（变异判据）** → 「变红」收紧为 `returncode == 1`（pytest 测试失败专属码）
+ `1 failed` + `-rf` summary 里 FAILED 的正是指定节点。collection error(2)/内部错(3)/
用法错(4)/未收集(5) 一律不算变红。

**HIGH-4b（AST 门可换形绕过）** → 调用侧改成**正向合约**：枚举全部允许的调用形态
（Name ∈ {APIRouter, list, _js_json, HTMLResponse}；Attribute ∈ {get, replace,
url_for, dumps, items}），func 为任何其它形态（含 Subscript 下标取内建、lambda 包裹、
getattr）一律红。import 侧维持白名单。变异 M35/M36/M37 三种形态（直呼 open /
`__builtins__["open"]` / lambda 包 open）全部对准它。

**MEDIUM**：M1 notes/inflight/pendingSync 改 Object.create(null)（"__proto__" 库目
点击流有专项断言）；M2 poll 的 200 坏形状在提交状态前拒绝（旧数据不清、徽标翻红、
横幅说话——test_js_malformed_200_keeps_last_data）；M3 renderPage 的 inflight→disabled
渲染断言 + 在飞防抖对 __proto__ 生效断言；M4 restDayHtml 最近到期日期转上海本地日
（2026-09-02T16:30:00Z → 显示 2026-09-03，专项断言）；M5 外链门补 data:/javascript:/
blob:/file:、协议相对 a href、CSS url()。
**LOW**：LOW-1 已修（`if not _NODE`）；LOW-2（TTL 是渲染时惰性过滤，DOM 提示可留到
下一次重绘）与 LOW-3（隐藏态首轮 GET 照发）**有意保留**，已在验收单「本卡未证明什么 /
语义声明」登记，不属缺陷。

## 审查重点（前两轮七项继续有效 + 本轮第 8 项）

1. 零外部依赖与同源约束；2. 轮询 clamp 与隐藏暂停、自动轮询绝不 POST；3. 四态不伪装
ok；4. JS 不重算 due；5. 与零 JS 页共存；6. W6 三字段缺省渲染；7. 测试与门的真实性
（沙箱执行无割取、负验证判据、接线门是否承重）；8. round-2 各条整改是否真实、
「正在看管的东西」有没有新的绕过面（例如代际守卫与 schedule 的交互、settlePendingSync
的时序、提取门的转义变体）。

## 已知边界（不算发现）

- 部署不在本卡；走查在本车道本地 server。V3 四答待用户确认。D-3/D-6 不吸收只登记。
- snooze/完成反馈是 G6-6/G6-7 地盘。GET 侧无新暴露面；refresh 同源门为 G6-1 既有。
- 刷新反馈 15s TTL 是渲染时惰性过滤（LOW-2 声明）；隐藏态首轮 GET 照发（LOW-3 声明）。

## 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 文件:行号、问题、具体失败场景、建议修复。
对 round-2 的 4 HIGH + 5 MEDIUM 逐条给 VERIFIED / NOT VERIFIED + 理由。没问题的维度
明说「未发现」。最后一行总结论：PASS 或 FAIL（有未清零 BLOCKER/HIGH 即 FAIL）。
