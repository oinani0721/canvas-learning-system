# Codex 对抗性审查 — CARD-G6-2 交互复习壳 [BATCH-2026-09-01-第八批] · round-3（重试）

你是独立对抗性审查员。工作目录（cwd）已是本车道 worktree 根：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp

这是第 3 轮的**重试**：上一轮执行被内容安全分类器误拦（见 codex-review-CARD-G6-2-round3.stderr
末尾的 cyber flag），未产出裁决。为避免再次误拦，本轮**读面收窄**（见下），
不影响你对抗性怀疑的权利——你依然可以否证任何一条整改声明。

## ⚠️ 本轮读面限制（防误拦，必须遵守）

- **不要整读** `_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py`
  与 `backend/tests/unit/test_review_app.py` 中的**攻击样本正文**（XSS payload、
  变异注入串等对抗性载荷内容会被分类器拦截）。
- 变异负验证的证据以存档日志为准：`_bmad-output/审查/evidence-g62/mutation-run-final.log`
  末行 `负验证 PASS: 42/42 条变异均被指定的那道门抓住; 还原后基线仍全绿`（判据 =
  pytest returncode==1 + "1 failed" + `-rf` summary 里 FAILED 正是指定节点）。
  你可以抽查该 log 的行与列，不需要打开变异脚本本体。
- 允许读：review_app.py、router.py、test_review_app.py 的**结构与门名**（grep 函数名/
  docstring/断言主句即可，跳过以 `//` 或 `'` 开头内嵌的 payload 字面量段落）、
  review_overview.py（对照物）、mutation-run-final.log、两轮历史审查存档、UAT 验收单。

## 被审变更

1. backend/app/api/v1/endpoints/review_app.py （交互复习壳单文件 HTML）
2. backend/app/api/v1/router.py （1 行 import + 1 行 include）
3. backend/tests/unit/test_review_app.py （56 基线外 31 条新增门）
4. 对照物（未改动）：backend/app/api/v1/endpoints/review_overview.py

卡文：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W5.md

## round-2 各条的整改声明（请逐条证伪；读面按上面的限制）

- **HIGH-1 因果一致性**：POST rebuilt 不再声称「数字已更新」，改「正在同步最新数字…」
  并登记 state.pendingSync；poll() 以 `++state.pollGen` 代际号守卫——响应先过形状校验
  （Array.isArray(data.vaults)）再验 gen，乱序旧响应（成功或失败）整包丢弃不碰状态；
  最新 GET 成功 → 「数字已更新」，失败 → 「同步失败」。门：乱序逆序 resolve 测试 +
  同步结算三场景测试；变异 M39/M40/M41 对准（42/42 全红日志为证）。
- **HIGH-3 提取同源**：_extract_script 大小写不敏感地数 `</script\s*>` 总数（恰 1），
  正文 `<!--`/`-->` 拒绝；指定门 test_real_page_extracted_script_is_well_formed
  （真实响应被毒化即红）；变异 M38 对准。
- **HIGH-4a 变异判据**：变红 = returncode==1（pytest 测试失败专属码；collection error=2/
  用法错=4 等不再冒充）+ "1 failed" + FAILED 指定节点。
- **HIGH-4b AST 门**：调用侧正向合约——Name 白名单 {APIRouter, list, _js_json,
  HTMLResponse}，Attribute 白名单 {get, replace, url_for, dumps, items}，其余形态
  （Subscript 下标取内建 / lambda / getattr）一律红；import 白名单维持。变异
  M35/M36/M37 三形态对准。
- **MEDIUM**：M1 null-prototype 容器（__proto__ 库目点击流专项断言）；M2 200 坏形状
  在提交状态前拒绝（坏响应不清旧数据、徽标翻红）；M3 inflight→disabled 渲染断言；
  M4 休息日最近到期转上海本地日（09-02T16:30Z→显示 09-03）；M5 外链门补
  data:/javascript:/blob:/file:、协议相对 a href、CSS url()。
- **LOW**：LOW-1 已修（`if not _NODE`）；LOW-2（TTL 渲染时惰性过滤）与 LOW-3（隐藏态
  首轮 GET 照发）**有意保留**，验收单已声明，不算缺陷。

## 审查重点

1. 零外部依赖与同源约束；2. 轮询 clamp 与隐藏暂停、自动轮询绝不 POST；3. 四态不伪装
ok；4. JS 不重算 due；5. 与零 JS 页共存；6. W6 三字段缺省渲染；7. 门与测试的真实性
（按门名/断言主句抽查即可）；8. 上述整改是否真实、代际守卫与 schedule 交互、
settlePendingSync 时序、提取门转义变体等有没有新绕过面。

## 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 文件:行号、问题、具体失败场景、建议修复。
对 round-2 的 4 HIGH + 5 MEDIUM 逐条 VERIFIED / NOT VERIFIED + 理由。没问题的维度明说
「未发现」。最后一行总结论：PASS 或 FAIL（有未清零 BLOCKER/HIGH 即 FAIL）。
