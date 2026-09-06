# 代码审查请求 · CARD-G6-7「完成本板反馈与当日进度」

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b`
审查绑定：`git diff 2c11d8e8e0c22b73c6d2081f5819fb8b7fa7a477..7ccdfd6c`（单 commit）

这是一个本机单用户的 Obsidian 学习系统。既有的「跨库复习总览」有两个页面：
零 JS 只读页 `/api/v1/review/overview/page` 与交互壳 `/api/v1/review/overview/app`，
都消费同一份由 `scripts/daily_review_pick.py` 生成的投影 JSON。本卡新增
**第一个写侧业务动作**：`POST /api/v1/review/overview/board-done`，把「这块白板
今天做完了」记进 runner 的 per-vault state 文件。

请只读以下位置（不必通读全仓）：

1. `backend/app/api/v1/endpoints/review_overview.py`
   - 模块 docstring 末尾的 CARD-G6-7 三条边界
   - `_sh_day` / `_sh_today`
   - `_vault_entry` / `_collect`（加性字段 board_done）
   - `_board_table_html` / `_board_done_form_html` / `_boards_split_html` / `_card_html`
   - `_assert_write_target_contained` / `_refresh_target` / `_assert_same_origin`（既有两道写侧门）
   - `_RUNNER_BASENAME` 起的整个 CARD-G6-7 段：`_runner_script` / `_load_runner` /
     `_runner_or_none` / `_require_runner` / `_read_board_done` / `_board_done_today` /
     `_write_board_done`
   - `review_overview_refresh`（既有唯一 POST，作对照）与文件末尾的 `review_overview_board_done`
2. `backend/app/api/v1/endpoints/review_app.py`
   - `doneKey` / `boardDoneBtnHtml` / `boardsSplitHtml` / `boardTableHtml` /
     `renderVaultCard` / `renderPage` / `renderBoardDoneResult` / `onBoardDoneClick`
     以及两条 `addEventListener("click", …)` 与 `async function poll()`
3. `scripts/daily_review_run.py`：`STATE_SCHEMA_VERSION` / `_vault_key` / `state_path` /
   `load_state` / `save_state`，以及 `ensure_payload` 里 `picker.build_payload(...)` 那一处调用
4. `scripts/daily_review_pick.py`：`build_payload` 的签名与其中标注 CARD-G6-7 的加性分区块
5. 测试：`backend/tests/unit/test_review_overview.py`（`g67` 前缀用例）、
   `backend/tests/unit/test_review_app.py`（`g67` 前缀用例 + `_BOOT_MJS` 的 addEventListener 存根）、
   `backend/tests/regression/test_daily_review_run.py` 与 `test_daily_review_pick.py`（`g67` 前缀用例）

## 二 作者自述（请独立核对，不要默认它成立）

- **零 FSRS 污染**：完成动作的写面恰是 `backups/daily-review.<vault_key>.state.json`
  一个文件；不写节点 md 的 `fsrs_*` frontmatter，不追加 `learning_events.jsonl`。
- **读松写紧**：写路径复用 `daily_review_run.load_state/save_state`（含损坏隔离与
  `os.replace` 原子写）；读路径另走 `_read_board_done` 纯读，因为 `load_state` 遇到
  损坏文件会改名隔离——那是一次写盘，放进 GET 会破坏本模块的只读契约。
- **两道写侧门复用不复制**：`_assert_same_origin` 由新端点直接调用；
  `_assert_write_target_contained` 经 `_refresh_target` 复用（直接调用点仍只有 1 处）。
- **state 加性扩展**：`schema_version` 1→2；旧文件缺 `board_done` 视同 `{}`，无迁移器；
  `board_done` 错型与 `board_last_recommended` 错型同等隔离重建。
- **生产器加性消费**：`build_payload` 新增可选 `board_done`；今天标完成的板做稳定分区
  让出榜首，不删行、不改分、不动排序律；全部完成时退化为恒等。
- **不撞既有轮询契约**：新 POST 只挂点击委托，不进 timer / `visibilitychange`。
- **已知残孔（作者已登记，不必再报为新发现）**：没有「取消完成」入口；runner 每小时
  档与 Web 点击之间是进程间 read-modify-write 窄竞态；Web 写入用 Asia/Shanghai 日、
  生产器比较用机器本地日（生产机上两者相同）。

## 三 请按重要性排序回答的问题

1. 新 POST 是否**真的**复用了那两道写侧门，而不是复制了一份等价逻辑？失败时是否
   一律回原样的 4xx/5xx（表单路径是否可能出现"与成功同形的 303"）？
2. state 路径派生是否与 `daily_review_run.state_path`（`:57` 起）同源？错型/损坏的
   state 在**写**路径上是否走既有隔离重建、在**读**路径上是否确实零写盘？
3. 新 POST 有没有任何路径能被自动轮询（timer）或 `visibilitychange` 间接触发？
4. 「FSRS 零触碰」那道门在对照输入下是否真会变红，且红在它声称的那条断言上？
   指纹函数 `_fsrs_fingerprint` 有没有覆盖不到的写面（例如某种改动它看不见）？
5. `scripts/daily_review_run.py` 的 credited_today 判定与落账（本卡基点的 171-183 行）
   是否逐字节未动？`build_payload` 的改动是否真的只是加性？
6. 「今天是否已完成」的判定是否复用了既有的 `_sh_day` 时区换算，还是另立了一套？
7. 其它你认为会导致数据错误、用户数据丢失或跨库串账的问题。

## 四 输出格式

按严重度分组（BLOCKER / HIGH / MEDIUM / LOW），每条给出：
`文件:行号` · 一句话问题 · 触发条件（什么输入或时序会让它发生）· 建议方向。
末尾给一句总体结论。若某条只是"看着可疑但没确认"，请标 `未确认` 并说明还缺什么证据。

## 五 边界（这些不在本卡范围，请不要按缺失报告）

- 不做 snooze / 不做任何压制 due 的逻辑（用户裁决 D-8，另卡）。
- 不做跨视图五面一致性比对（G6-8，另卡）。
- 不做「答题后触发重建」（用户裁决 D-11 丙）。
- 不写节点 frontmatter、不追加 `learning_events.jsonl`（这是本卡的硬边界，不是遗漏）。
- 不实现「取消完成」（已登记为残孔，交后续卡）。
- 用户已裁决：完成 = 移入「已完成」折叠区（不是隐藏）；允许一道题都没答就标完成，
  但页面必须明示「不影响 FSRS」。这三条是既定需求，请不要按设计缺陷报告。
- 端点鉴权范围（本后端此端点对能连到该端口的进程开放）是既有的全站现状，
  已在 `_assert_same_origin` 的 docstring 里如实登记并上过用户裁决点，不是本卡引入。
