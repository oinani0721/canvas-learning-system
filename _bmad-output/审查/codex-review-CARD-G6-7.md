> 批次: BATCH-2026-09-05-第十二批 · 车道 Y2 · 卡 CARD-G6-7 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-7.md)"`
> 审查绑定: `2c11d8e8..7ccdfd6c`（送审时 HEAD = 7ccdfd6c；**审后已整改，构成失绑，见验收单 §5**）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/.claude/worktrees/card-x2-g62b` / `model: gpt-6-astra`

---

审查绑定 `2c11d8e8..7ccdfd6c`，目标 HEAD 与被审文件均已复核；未修改仓库。确认 **1 HIGH、2 MEDIUM、2 LOW**。

**BLOCKER：未发现。**

**HIGH**

- [review_overview.py:2081](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:2081)、[daily_review_run.py:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/scripts/daily_review_run.py:113) · **复用的路径门未覆盖实际 state 写入位置，预置软链可导致节点全文丢失。**  
  触发：让 `backups/daily-review.<key>.state.tmp` 软链指向节点 Markdown。既有门只检查 vault 与 `outputs`；`tmp.write_text()` 随后跟随软链覆盖节点。隔离真实路由实测：节点变成 state JSON，接口仍返回 `200 / fsrs_touched=false`，表单返回 `303`。这是预置软链，无须竞态。建议在 runner 写入层保护实际 backups/state 路径，使用排他创建的唯一临时文件并拒绝软链，补入该对照输入。

**MEDIUM**

- [daily_review_run.py:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/scripts/daily_review_run.py:178)、[daily_review_pick.py:1225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/scripts/daily_review_pick.py:1225) · **完成账没有接通正常投影更新链，“今天让出榜首”可能全天不生效。**  
  触发：当天投影已缓存，随后标记榜首完成，节点没有变化，也没有跨越未来到期点。缓存不检查 `board_done`，直接返回旧投影；手动刷新调用的 picker CLI 也未传入 `board_done`。真实文件复现得到 `cached`，榜首和通知仍指向已完成板。建议将完成账变化纳入缓存失效，并让刷新/CLI 从同源 state 纯读传入完成账；测试须保留正常缓存字段。

- [review_app.py:651](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:651) · **此前刷新的异步结算会覆盖最新的完成失败提示。**  
  触发：刷新成功后的 GET 尚未返回，此时同库标完成得到 `503`；旧 GET 随后返回，`settlePendingSync()` 将共享的 `state.notes[vid]` 改成绿色“已重建…数字已更新”。真实模板的内存 JS 时序探针已复现。建议按动作及操作编号绑定反馈，旧刷新结算不得覆盖后来的完成操作。

**LOW**

- [test_review_overview.py:2725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_overview.py:2725) · **`_fsrs_fingerprint` 没有检查 frontmatter 边界，也不满足逐字节比较。**  
  触发：将结束 `---` 移到 `fsrs_due` 行之前，使该行成为正文；或仅将 CRLF 改成 LF。两种输入实测均保持指纹相等。建议检查真实 frontmatter 中的字段及完整值，并保留字节检查。当前主正例还有整树差集断言，能抓住上述文件变化，因此这不是整个测试假绿。

- [review_overview.py:1970](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_overview.py:1970) · **冷启动后的 GET 可能生成字节码缓存，严格的“读路径零写盘”不成立。**  
  触发：runner 尚未加载、缺有效缓存、未禁用字节码且缓存目录可写。真实 GET 隔离实测生成了 runner、send_bark 等 `.pyc`；没有创建或改写 state。建议在启动配置中明确禁用字节码，并覆盖冷加载测试；现有夹具提前加载 runner，覆盖不到这一点。未核验现网是否已启用 `-B`。

其余问题的核验结果：

- **两道门确实复用**：新 POST 直接调用 `_assert_same_origin`，经 `_refresh_target` 调用唯一的 `_assert_write_target_contained`。正常拒绝/异常分支不会变成成功 `303`；上述 HIGH 是越界写未被识别为错误。
- **state 派生及隔离同源**：读写均调用 runner 的 `state_path(vault_dir)`；写侧实调 `load_state/save_state`，损坏、错型走隔离重建；`_read_board_done` 本身不隔离、不保存。
- **自动触发链无 POST**：timer、`visibilitychange`、初始化均只进入 GET `poll()`；完成 POST 仅由点击路径触发。
- **FSRS 指定负对照有效**：污染开关开启后，POST 仍成功，测试首先失败于 `:2818 → :2738` 的指定断言，错误串为“FSRS 面被写动”。
- **原有落账未动**：基点 `171–183` 行与目标 `199–211` 行逐字节相同。`build_payload` 本体仅增加可选参数及稳定分区，原得分、排序律未改。
- **当天判定同源**：`_sh_today` 明确经 `_sh_day` 换算，没有另立时区入口。

验证：23 个 Python `g67` 用例通过；10 个 JS 用例通过；污染对照按预期失败。

**总体结论：建议暂缓通过，先修复实际 state 写入面的软链越界，再补齐推荐更新链和反馈归属。**


