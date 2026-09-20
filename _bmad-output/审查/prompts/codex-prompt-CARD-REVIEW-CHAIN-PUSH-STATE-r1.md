# CARD-REVIEW-CHAIN-PUSH-STATE 独立审查请求（round-1）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`；本卡基线 `6d8ca202`（P5-A 末 commit）；**审查绑定 `626d5416`**。
批次 `[BATCH-2026-09-18-第十五批 / CARD-REVIEW-CHAIN-PUSH-STATE]`。

本卡代码面 = **两个 commit**：
- `9922d0bf`（主改动，9 文件 +266/−23）；
- `626d5416`（纯注释/docstring：三处自引行号更正 `:1176→:1181` ×2、`:60-66→:60-67`）。

这张卡修四件事：

1. **推送链「三态谎报」（本卡核心缺陷）**：Bark key 未配置时 `send` 返回 2 →
   `scripts/daily_review_run.py` 只写日志 `push:skip-nokey`、**state 一个字都不落账** ⇒
   昨天的 `last_result: "pushed"` 原样留存 ⇒ `/overview` 与交互页都显示「一切正常」，
   而用户手机上什么都没收到。修法（三处**同一 commit**）：
   · runner `:754/:755`：新增 `else` 支写 `generated_push_skipped_nokey` + `bark-nokey`（固定串）；
   · `review_overview._read_push_status`：新增**精确** `elif`（默认产品口径：未配 key =
   今天没推出去 = 降级 True）；
   · 登记门 `test_g6_9_boundary_matrix.py`：`RUNNER_ONLY_KEYS` +新键、`EXPECTED_HITS` 1→2 行。
2. **`last_error` 长度截断**：`_LAST_ERROR_MAX_LEN = 200`（:807），切点在
   `err.encode("utf-8")` 可编码门**之后**（与本文件兜底条目 :1181 的 `[:200]` 同口径）。
3. **G6-8 模板冻结绑最终模板（关闭 Codex r5 HIGH-1）**：`g68_five_view_contract.py` 原实现用
   `next()` 取顶层第一处常量赋值 ⇒ 模板后追加再绑定时门仍 PASS（r5 实测）。
   新增**判据① 单一绑定**（:488 起）+ **判据② 运行期锚**（:645 起，importlib 取运行期
   `_PAGE_TEMPLATE` 与 AST 常量逐字节比，fail-closed）；`_TEMPLATE_DUE_CALLSITES` 冻结集
   2 条**不变**。
4. **交互壳同款推送降级徽标（默认实施，可退）**：`review_app.py` import 共享文案
   `_PUSH_DEGRADED_LABEL`、模板占位符 `__PUSH_DEGRADED_LABEL_JSON__`、卡头第二枚徽标
   （严格 `entry.push_degraded === true`，title 与零 JS 页同文案）；`test_review_app.py`
   白名单 + `g68._APP_SHARED_IMPORTS` 两处同 commit 登记。

另：`inbox_preview.py:430` 的 +08:00 按默认**零改动**（用户当次裁 D-18 才改）；本卡只核
G6-8 契约里它的已声明文字与源码一致。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color 6d8ca202 626d5416 -- . ':(exclude)_bmad-output'   （本卡全部改动, 两 commit 净 diff）
scripts/daily_review_run.py:693-776                     （main() 推送段终态, 含新增 :754/:755）
backend/app/api/v1/endpoints/review_overview.py:2553-2628   （_read_push_status 终态全文）
backend/app/api/v1/endpoints/review_overview.py:1645-1670  （零 JS 页降级徽标, 对比用）
backend/app/api/v1/endpoints/review_overview.py:800-808    （_LAST_ERROR_MAX_LEN）
backend/app/api/v1/endpoints/review_app.py:60-67（import 块）, 190-195（注入常量）,
    538-552（卡头徽标 JS）, 1021-1045（handler + 替换链）
backend/scripts/g68_five_view_contract.py:421-429（_APP_SHARED_IMPORTS）, 469-669（断言全函数, 含判据①②）
backend/scripts/g68_five_view_contract.py:991-1115      （run() 的调用前提: sys.path 插入时序）
backend/tests/regression/test_g6_9_boundary_matrix.py:605-672  （登记门终态）
```

行号为送审时实测；漂移以**符号名**为准。

**本卡新增/修改的测试（请核其"先红后绿"面与断言绑定）：**
- `test_daily_review_run.py::test_skip_nokey_overwrites_stale_pushed_state`（新；先红 = `last_result` 断言实得 `"pushed"`）
- `test_review_overview.py::test_overview_push_degraded_true_when_skipped_nokey`（新；先红 = `push_degraded` 实得 None）
- `test_review_overview.py::test_overview_last_error_truncated_to_200`（新；先红 = 1000 ≠ 200）
- `test_g68_five_view_contract.py::test_template_freeze_binds_final_template`（新；双负控在用例内）
- `test_review_app.py::test_push_degraded_badge_injected_and_placeholder_replaced`（新）
- `test_g6_9_boundary_matrix.py::test_push_failure_visibility_in_backend_app_is_exactly_review_overview`（改：登记面 1→2）

**背景材料（只读；本卡由来与关闭目标）：**
- `_bmad-output/审查/codex-review-CARD-G6-8-r5.md`（:13 起 HIGH：「模板冻结没有绑定最终模板」+ 其负控形态）
- `_bmad-output/验收单/UAT-CARD-G6-9b-2026-09-17.md`：:243「未证明 #10 skip-nokey 不会现形」、
  :292 待办「#9 last_error 未截断」、:314「未证明 #17 `_read_push_status` 对 skip-nokey 无能为力」
  —— 本卡正面修的就是这三条。
- `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` **§二 T3-B 行**：
  ⚠️ 本树同名文件只有 111 行（缺第十四批全批复核），须读 feature 主干树那份（T3-B 行在 :144）：
  `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md`
- jev 分诊（jev-1.13.0，绑 `9922d0bf`，`evidence-review-chain-push-state/jev-triage-9922d0bf.json`）：
  | 文件 | urgency | P(review) | risk |
  |---|---|---|---|
  | g68_five_view_contract.py | 3.09 | 0.85 | error_handling |
  | review_overview.py | 2.38 | 0.66 | logic |
  | test_g68_five_view_contract.py | 2.18 | 0.61 | test_or_docs |
  （其余 3 文件 pass；③ 的问题顺序按 urgency 降序。）

## ② 作者自述（请独立核对，勿直接采信）

1. 三处（runner / 读侧 / 登记门）在**同一 commit** `9922d0bf`；枚举字面三处逐字同
   （`generated_push_skipped_nokey` / `bark-nokey`）。
2. `push` 日志字面仍是 `skip-nokey`（未改）；失败分支 `generated_push_failed`/`bark-send`
   未动；`last_push_kind` / 反转门 / 本地兜底语义未动（新增支只写 `last_result` + `last_error`）。
3. 截断在 `err.encode("utf-8")` 门**之后**；坏串路径（孤立 surrogate）仍 → None，
   不在坏串上切片。
4. g68 冻结集 `_TEMPLATE_DUE_CALLSITES` 仍 2 条（AST 实测 `sites==frozen: True`）；
   新判据 fail-closed（import 失败或不等 ⇒ `ContractError`，不 skip）；负控覆盖
   r5 再绑定形态与 `"".join([...])` 非常量形态（后者的红点在「不再是模块级字符串常量赋值」）。
5. review_app 新增行不含 `fsrs_due`/`due_reason`/`fsrs_state`；`_PAGE_TEMPLATE` 仍单一绑定
   （AST：Store=1）；徽标条件是严格 `=== true`。
6. `inbox_preview.py` 本卡零 diff（`git diff 6d8ca202 626d5416 -- canvas-vault/` 为空）。
7. pyright `app` = `0 errors`（改前/改后各一次）；ruff check/format 本卡 9 文件 clean。

## ③ 按重要性排序的问题（逐项给结论；顺序 = jev 分诊 urgency 降序）

- **A（g68，urgency 3.09）** 判据② 的运行期锚 `importlib.import_module("app.api.v1.endpoints.review_app")`
  在 `--now` 独立运行模式（`cd backend && python scripts/g68_five_view_contract.py ...`）下会不会
  把 app 依赖带进契约脚本而让 live 跑法失败？现状：调用点在 `run()` :1107，其前 :1091-1094 已
  插入 `sys.path` 并 import 过 review_overview —— 该前提是否足够？请给形态级结论与最值得补的
  对照输入（例如 `python scripts/...` 之外的第二条启动路径）。
- **B（review_overview，urgency 2.38）** 新 `elif` 是否又打开「未知值 → True」的门？应仅精确匹配
  新枚举。请核：`last_result: null`、未知串、`generated_push_failed` 带垃圾 `last_error`、
  新枚举带坏 `last_error`（surrogate）四种输入是否与改前语义一致。
- **C** 新枚举落地后，**还有哪条路径会让旧 `"pushed"` 继续存活**？（例：`skip-empty` /
  `skip-done` / `skip-window` 三个早退分支不落账 —— 如实评估它们是否也该现形；本卡只修 rc==2，
  其余登记。注意 `skip-done` 语义 = 「今天已经推过」，与 rc==2 不同。）
- **D** 截断 `err[:200]` 是否会切断多码元字符造成**二次编码问题**？（str 切片安全性；
  与 encode 门的次序）另：200 是否可能把某个序列切在半途？请给最坏输入形态。
- **E** review_app 徽标 `title` 的 `esc(...)` 是否覆盖 `last_error` 全部输入面（属性上下文；
  `"`、`&`、`<` 的转义）？与零 JS 页 `html.escape(quote=True)` 的覆盖差在哪？
- **F** 登记门 `EXPECTED_HITS` 扩为 2 行后，验伪锚（扫 runner 源码有无该键）是否仍能区分
  「扫错地方」与「真的没有」？新增键注释里写的 runner 行号（:755）与终态是否一致？
- **G** pyright 0 是否靠 ignore 掩盖？（本卡新增 ignore 应为 0。）
- **H** 其它真问题按 ④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--sandbox read-only`）；不连库（7691/7687/7692）；不 push。
- **不评**（范围外）：P5-A 的时区解析器面（CARD-G6-9c-R3 已独立收口）；G6-13 跨日旅程；
  `inbox_preview.py:430` 的 +08:00 产品口径本身（按默认不改，是用户裁量项）；
  G6-9b / r12 等已登记且本卡未动的 MEDIUM/LOW。
- 本轮只审 `626d5416` 所钉代码终态；`_bmad-output/` 文档面不在审查面。
