# Codex 定向第四轮复审 — CARD-G6-2 交互复习壳 [BATCH-2026-09-01-第八批]

你是独立对抗性审查员。工作目录（cwd）已是本车道 worktree 根：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp

## 本轮性质与范围（定向，窄）

用户对 round-3 终裁（FAIL：1 BLOCKER + 3 HIGH）的裁决是「定向第四轮」。round-3 的
三条 HIGH 已在 commit `7ca194ac` 整改；**本轮只审这个整改提交**，不重开已 VERIFIED
的旧账（round-2 已 VERIFIED 的 HIGH-2/HIGH-4a/M3/M4 不需要再证）。

审三个文件：
1. `git show 7ca194ac` 的 diff（整改本体）
2. `backend/app/api/v1/endpoints/review_app.py`（终版全文）
3. `backend/tests/unit/test_review_app.py` 的**结构与门名**（见读面限制）

对照物（未改动）：`backend/app/api/v1/endpoints/review_overview.py`。
卡文（如需）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W5.md`

## ⚠️ 读面限制（防内容安全误拦，必须遵守）

- **不要整读** `_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py` 与
  `backend/tests/unit/test_review_app.py` 里的**攻击样本字面量**（XSS payload、
  变异注入串）。用 grep 拿门名/断言主句即可。
- 变异负验证证据以存档日志为准：`_bmad-output/审查/evidence-g62/mutation-run-final.log`
  末行 `负验证 PASS: 46/46 ...`（判据 = returncode==1 + "1 failed" + FAILED 指定节点）。
- 其它证据：`evidence-g62/裁判命令输出-r4.txt`（89 passed / external [] / 基线=1 /
  pyright 0 错）。

## 逐项验证清单（round-3 三 HIGH 的整改声明，请证伪）

### HIGH-1 结算绑定证据 + 渲染探针先行
声明：POST rebuilt 只显示「正在同步最新数字…」并登记 `state.pendingSync`；最新 GET
（`pollGen` 代际守卫 + 形状校验前置）先做**渲染探针**（renderPage 抛错则整体走 catch，
lastData/结算/横幅全不提交），然后按 `renderedVids`（渲染成功且 `projection` 可用的库）
结算 pendingSync——目标库不在 renderedVids（corrupt/缺投影/从聚合消失）→ 结算为
「同步失败」；在 → 「数字已更新」。最终帧在结算后另行渲染（含结算后的反馈）。
门：test_js_settle_binds_to_rendered_vault_evidence（①corrupt ②目标库消失 ③有证据
三场景）+ 乱序测试 + 同步结算三场景；变异 M46 对准。

### HIGH-3 结束符语言
声明：_extract_script 大小写不敏感地数 `</script` **前缀**总出现次数（恰 1）——覆盖
`</script/`、`</script x=y>`、`</SCRIPT>`、`</script >` 全部浏览器合法形态；正文
`<!--`/`-->` 拒绝；开标签只允许一个字面 `<script>`。门：
test_script_extraction_rejects_case_insensitive_terminator（5 毒样本）+
test_real_page_extracted_script_is_well_formed（真实响应；M38/M43 指定门）。

### HIGH-4b AST 门收口
声明：调用侧正向合约之外，新增**重绑定/参数遮蔽禁令**（Assign/AugAssign/AnnAssign
目标与函数参数命中白名单名 → 红，封 `list = open; list(...)` 拼写合法绕过）与
**接收者白名单**（Attribute 调用接收者 unparse 基名 ∈ {json, request,
review_app_router, _STATUS_META, _PAGE_TEMPLATE} 或接收者本身是白名单 Call → 否则红，
封任意对象挂同名方法）。import 白名单维持。变异 M44（`list = open`）/M45（`[1].items()`）
对准。

### 随行补口（低权重，一并看）
M1 freshNotes 返回 Object.create(null)；LOW-2 隐藏时 rebuilt 不触发 GET（pending 留给
回前台 visibilitychange 的 poll 结算）；LOW-3 STATUS_META own-key 访问（`constructor`
不命中继承属性）。

### BLOCKER（DD-14 无 PLAN-NNN）——**不在本轮代码审查范围**
用户已知悉，裁决权在用户/主 session（goal-card `@spec:` 引用等价性）。你不需要审它，
也不要因它改总结论的措辞口径——总结论只针对上述三个 HIGH 的整改与随行补口。

## 输出格式

- 三个 HIGH 各给 VERIFIED / NOT VERIFIED + 理由（发现新问题则给 文件:行号 + 具体失败
  场景 + 严重度 BLOCKER/HIGH/MEDIUM/LOW）。
- 随行补口若有问题一并列。
- 最后一行：`总结论：PASS`（三条 HIGH 全 VERIFIED 且无新 BLOCKER/HIGH）或
  `总结论：FAIL（...）`。
