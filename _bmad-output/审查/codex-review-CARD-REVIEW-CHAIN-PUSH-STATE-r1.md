> 批次: BATCH-2026-09-18-第十五批 · 车道 P5 · 卡 CARD-REVIEW-CHAIN-PUSH-STATE round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-REVIEW-CHAIN-PUSH-STATE-r1.md)"`
> 审查绑定: `626d5416`（送审时 HEAD=`626d5416`；代码面自 626d5416 后零改动，判据见 evidence-review-chain-push-state/ 绑定存档）
> 会话头自证（抄 .stderr 含 codex 版本行 + `model:` 行 + `reasoning effort` 行三行，括注行号；stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

**裁决：代码终态 `626d5416` 的四项主修在产品实现面成立；未发现 BLOCKER/HIGH。** 但测试闭合面有两个 MEDIUM 缺口：G6-8 新增的“运行期锚”没有自己的先红负控，交互壳降级徽标也没有执行真实 `renderVaultCard` 行为门。另有若干 LOW 级注释/登记边界问题。

## 绑定与只读证据

- HEAD 实测为 `626d5416822e939be75dd4dc9a0367c11dc79366`，等于送审绑定。
- `9922d0bf` 实测 9 文件 `+266/−23`；`626d5416` 实测 3 文件 `+3/−3`，净 diff 因此为 `+267/−24`，与两 commit 组合一致。
- `626d5416` 仅改三处自引行号，未见代码行为变化。
- `git diff --check 6d8ca202..626d5416` 无输出。
- 只读 AST 实测：`review_app._PAGE_TEMPLATE` Store 仅 1 处、顶层字符串常量赋值 1 处；模板长度 47142；due 冻结集仍恰 2 行；`__PUSH_DEGRADED_LABEL_JSON__` 与 `push_degraded === true` 在模板中各恰 1 处。
- 未运行 pytest/pyright/ruff，因为本轮边界要求只读且 pytest 会写 cache/tmp；以下测试先红结论来自 diff + 控制流独立核对。pyright/ruff 的“0 errors/clean”是作者自述，本轮只核实了新增 ignore 为 0。

## 发现清单

- **[MEDIUM] backend/tests/regression/test_g68_five_view_contract.py:420 — G6-8 判据②“运行期锚”缺少自己的失败面负控，两个现有负控都在判据①提前红，删除生产端 `g68_five_view_contract.py:655-656` 的逐字节比较后该测试仍可绿；负控输入：保持 AST 单一绑定，把已导入的运行期 `app.api.v1.endpoints.review_app._PAGE_TEMPLATE` 改成 `template + " "` 后再调用，应断言抛出“运行期 `_PAGE_TEMPLATE` 与 AST 常量不逐字节相同”。**
- **[MEDIUM] backend/tests/unit/test_review_app.py:280 — 交互壳徽标门只证明占位符注入与源码里恰有一处严格条件，未证明真实渲染输出；未被拦下的输入：保留 `push_degraded === true` 字面但从 `return` 拼接中删掉 `pushBadge`，现有测试仍绿；对照输入应复用本文件既有 node harness 直接调 `renderVaultCard`，分别喂 `true` / `false` / `None`。**
- **[LOW] backend/tests/unit/test_review_app.py:329 — 新共享单例 `_PUSH_DEGRADED_LABEL` 未加入 `_BANNED_REBINDS`，与 `_DONE_NOTE` / `_SNOOZE_NOTE` 的防重绑定纪律不同步；门未覆盖的路径：import 后再写 `_PUSH_DEGRADED_LABEL = ...` 时 AST 结构门不红。**
- **[LOW] backend/app/api/v1/endpoints/review_overview.py:2586 — 注释仍称“两个明确枚举”，终态实际是 `pushed` / `generated_push_failed` / `generated_push_skipped_nokey` 三个明确取值；对照输入：读 :2601-2616 的三个精确分支，行为正确但注释漂移。**
- **[LOW] backend/tests/regression/test_g6_9_boundary_matrix.py:618 — docstring 仍说扫描确认“没有任何 Python 文件提到那四个键”，当前键集为五个且 `EXPECTED_HITS` 为两行；对照输入：读 :634-658，注释与登记门终态相反。**
- **[LOW] scripts/daily_review_run.py:722 — `skip-empty` / `skip-window` 早退不更新 `last_result`，昨日 `"pushed"` 会留存；`skip-done` 则表示今日已 accepted，不应按失败现形；对照输入：昨日 `pushed`，今日 notification 为空或在推送窗口外，state 的 `last_result` / `last_error` 不动。应登记为“最近一次结果无观察时间戳”的口径边界，而不是默认把未到窗口判降级。**

## A-H 逐项结论

### A. G6-8 运行期锚是否破坏 `--now` 独立运行 — PASS，形态上不新增依赖面

`run()` 在调用静态断言前已经：

1. `:1087-1088` 把 `WT/backend` 插入 `sys.path`；
2. `:1089` 导入 `app.config.reload_settings`；
3. `:1092` 导入 `app.api.v1.endpoints.review_overview`。

而 `review_app` 自己的导入面只是 FastAPI 与 `review_overview` 共享名，`importlib.import_module("app.api.v1.endpoints.review_app")` 不再引入新的 app 依赖层。

我在受限网络下做了只读 import 探针：导入成功，解析到的是本 worktree 的 `review_app.py`，运行期 `_PAGE_TEMPLATE` 为 47142 字符 str。导入过程中 LiteLLM 有远程 cost map 拉取失败警告并回退，但不是失败；且这不是新锚独有的依赖，因为 `run()` 已经先导入 `review_overview` / app 包。

最值得补的第二条启动对照是：从 repo root 执行 `python backend/scripts/g68_five_view_contract.py ...`，对照文档里的 `cd backend && python scripts/...`。脚本按 `__file__` 推导 `WT/backend`，理论上两条路径等价；完整执行会写 tempfile，本轮按只读边界未跑。

### B. `_read_push_status` 是否重新打开“未知值 → True” — PASS

终态是三个精确 equality 分支：`pushed` → False，两个已知失败枚举 → True，其余一律 `(None, None)`。`last_error` 不参与三态判定。

内存 mock `Path.read_text` 实测：

- `last_result=None` + 噪声 error → `(None, None)`
- 未知字符串 + 噪声 error → `(None, None)`
- `generated_push_failed` + 非字符串 error → `(True, None)`
- `generated_push_failed` + 孤立 surrogate → `(True, None)`
- `generated_push_skipped_nokey` + 孤立 surrogate → `(True, None)`

没有未知值滑进 True 的路径。

### C. 旧 `"pushed"` 继续存活的路径 — PARTIAL / 登记边界

- `skip-empty`：无 notification，不进 send 分支，不更新推送结果。
- `skip-window`：尚未到推送窗口，不进 send 分支，不更新推送结果。
- `skip-done`：`last_push_accepted_date == today`，今日确实已 accepted；留存 `"pushed"` 是真话，不应降级。

因此本卡修住的核心是“到窗口、有内容、尝试发送但 rc==2”这一档。剩余问题是 state 没有记录 `last_result` 的观察时间，读侧只能语义化为“最近一次结果”，不能区分“昨天成功”与“今天尚未到尝试点”。这应登记，不建议在本卡默认改成降级。

### D. `err[:200]` 截断安全性 — PASS

截断发生在 `err.encode("utf-8")` 成功之后。Python `str` 按 Unicode code point 切片，不会把有效 astral character 切成半个 code unit；孤立 surrogate 在 encode 门整体丢弃，不会先切片。

最坏输入形态是复杂 grapheme cluster：例如重复的 `👨‍👩‍👧‍👦` ZWJ 序列。第 200 个 code point 可能落在序列中间，输出仍是合法 UTF-8，不会二次编码失败，但展示上可能变成不完整/碎片化语义。另注意 200 是 code point 数，不是字节数。

### E. `review_app` title 转义覆盖 — PASS

JS `esc()` 覆盖 `& < > " '` 五个危险字符；Python `html.escape(..., quote=True)` 也是同一覆盖面，单引号实体写法不同但语义等价。`pushWhy`、固定前缀和 `PUSH_DEGRADED_LABEL` 均经过 `esc` 后进入属性，未看到与零 JS 页的转义覆盖差。

### F. 登记门验伪锚 — PASS，但注释漂移

`RUNNER_ONLY_KEYS` 已加入 `generated_push_skipped_nokey`，`EXPECTED_HITS` 恰两行；runner 源码验伪锚仍要求所有键在 runner 中存在，能区分“消费面变了”和“扫描关键词过期”。新注释里的 runner `:755` 与终态一致。LOW 项是 docstring 仍写“四个键 / 零命中”。

### G. pyright 是否靠 ignore 掩盖 — PASS / 自述未复跑

本卡新增 ignore/pyright suppress 为 0；新增的只有 `except Exception` 上的 `# noqa: BLE001`，并且该异常会转换成 `ContractError`，是 fail-closed 而非吞错。pyright 与 ruff 的 0-error/clean 结论本轮没有独立执行。

### H. 新测试先红后绿绑定 — 主链成立，两个 MEDIUM 缺口已在清单中

- runner nokey 用例：旧代码 rc==2 不写 state，`last_result` 保持 `"pushed"`，先红点确在 :1040。
- overview nokey 用例：旧读侧把新枚举归未知 → None，先红点确在 :4953。
- truncation 用例：旧读侧返回整串，1000 ≠ 200，先红点确在 :4979。
- G6-8 模板用例：旧 `next()` 提取第一处常量，r5 再绑定负控会 PASS，先红点确在 :427；join 形态也会因旧提取缺失而红。但判据②自身没有负控。
- review_app 注入门：旧模板无新占位符，先红点确在 :289；但没有真实渲染 true/false/None 的行为门。
- boundary 登记门：若只套用新测试到旧代码，runner 验伪锚会先因新键缺失而红；登记面变更被绑定。

**`inbox_preview.py:430` 实测仍为 `_TZ_SHANGHAI = timezone(timedelta(hours=8))`，且 `6d8ca202..626d5416 -- canvas-vault/` 为空；G6-8 注释中的 :430 声明与源码一致。**

BLOCKER=0 HIGH=0 MEDIUM=2 LOW=4
