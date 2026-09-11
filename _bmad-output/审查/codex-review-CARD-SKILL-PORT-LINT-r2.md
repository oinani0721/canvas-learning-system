> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r2.md)"`
> 审查绑定: `9303201a..3b98081a`（**不绑合并态**：审查期间工作区已有未提交变更，Codex 明确声明以该提交内 886 行版本为准；本轮后又提交 `8bb94475` + `98ca073c`，round-3 另绑最终 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/worktrees/card-u4-hosts` / `model: gpt-6-astra` · `reasoning effort: ultra` · `sandbox: read-only`

---

复核绑定 **`3b98081a8fde6df14696d87ef441b11990e6a013`**。工作区测试文件在审查期间出现未提交变更；以下结论和行号均以该提交内的 **886 行版本**为准，并已从提交内容加载纯函数复验。

**BLOCKER：未发现。**

1. **HIGH — [test_skill_portability_lint.py:164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:164)：路径切分同时存在漏检和误报。**  
   将已有命名空间路径等计数替换为 `/tmp/cls-exam/a,b/../../x.json`，九项计数完全不变；正则只取得 `/tmp/cls-exam/a`，越界结果为 `[]`，但完整路径规范化为 **`/tmp/x.json`**。反向，合法文件名 `/tmp/cls-exam/..,x` 被截为 `/tmp/cls-exam/..`，误报越界。另有左边界缺失：`/var/cache/tmp/cls-exam/x.json` 也被当成命名空间内路径。这里的绕过是**替换已有命中**；直接追加仍会被四端计数拦住。

2. **MEDIUM — [test_skill_portability_lint.py:482](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:482)：删除越界基线条目会静默停止检查该 skill。**  
   删除 `ESCAPING_TMP_BASELINE["start-exam-board"]` 后，`:616` 的完整性断言仍通过；再将该 skill 的已有命名空间路径换成 `/tmp/cls-exam/../x`，四端计数不变，越界检查却不再遍历它。现有越界负控只变异 `exam-quick`，也发现不了这项删减。缺少 `set(ESCAPING_TMP_BASELINE) == EXPECTED_SKILLS`。

3. **MEDIUM（维护限制）— [test_skill_portability_lint.py:517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:517)：U6 合法登记没有锁住“零余量”。**  
   新增 `skills/clear-inbox/scripts/new_u6_tool.py`，含 `/tmp/cache`、`/Users/old-user/cache`，同时登记 `{tmp:1, users_path:1, tree_name:0}`，计数与两个交接测试均可通过。目录约束只保证登记位置，不能拒绝一起登记的新债；基线 diff 仍可供人工发现。另外，把已有 `recap_scan.py` 从主基线移入 U6 基线也会通过，目录规则没有保持原有维护归属。

4. **MEDIUM — [test_skill_portability_lint.py:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:183)：完整 token 规范化合规，仍不能证明实际路径合规。**  
   反例为 `REL=../x` 配合 `P="/tmp/cls-exam/${REL}"`：token 没有被截断，裸值为零，`normpath` 仍在命名空间内，但 shell 展开后指向 `/tmp/x`；等计数替换已有路径可绕过两条判据。分工表对此也通过，因为 `:599` 只检查原字符串前缀，不能独立证明实际范围。

5. **MEDIUM — [test_skill_portability_lint.py:783](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:783)：越界负控没有验证它声称的“计数门看不见”。**  
   三条用例都是追加，因此均使 `tmp_all`、`tmp_ns` 各增加一，现行层 2 实际也会红；裸值不变不足以证明计数门放行。它们确实直接验证了越界判据报红，**不是被其他层代为拒绝**，但没有验证两层的独立分工。应使用等计数替换，并实际断言 `check_body(...) == []`。

6. **MEDIUM — [test_skill_portability_lint.py:650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:650)：U6 正反用例没有调用正式交接判据。**  
   测试自行重写集合判断；即使正式 `:631` 退回 round-1 的 `== u6_seed`，当前两项常量仍通过，这条“新增登记必须放行”测试也继续通过，无法捕获它声称防守的回归。

7. **MEDIUM（既存覆盖限制）— [start-exam-board/SKILL.md:306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/canvas-vault/.claude/skills/start-exam-board/SKILL.md:306)：真实存在的 cwd 依赖逃出了四类判据。**  
   diff 中的 `cat .obsidian/cls-internal-key.txt` 依赖执行目录；从其他 cwd 执行会读取错误位置或读不到密钥。这段路径的九项正文指标全部为零，越界结果也为空，另外两层不会检查其路径语义。  
   `:505` 的 glob 还明确遗漏 templates、非 `.py` 文件、嵌套脚本和其他 `.claude` 目录；`~/`、`$HOME`、`/var/folders`、固定 `8080` 等也无对应指标。不过，**限定材料未提供这些位置现存债的可核实内容**，不能将构造反例冒充仓内实物。`127.0.0.1:8011` 则仍会被 `8011` 计数捕获。

8. **LOW — [test_skill_portability_lint.py:491](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:491)：多重集减少的诊断会漏报缺失项。**  
   当期望为 `[x,x]`、实际为 `[x]`，检查仍正确报红，但 `missing` 返回空列表，因为这里只判断成员是否存在，没有比较次数；因此消息会显示“缺失=[]”。

其余维度明确结论：

- **round-1 三个具体问题的直接整改成立**：普通 `../x` 三种形态能被越界判据识别；U6 新增零指标脚本不再被旧等号阻断；原来的 `all/ns` 同增、裸值不变案例会被四端计数捕获。
- **基线算术：未发现问题。** 收工证据的 **9×9 项**与常量完全一致。
- **BASELINE／QUIZ 覆盖完整性：未发现失效。** 当前九项指标均被消费；遗漏正文 skill 会被完整性断言发现。越界基线缺口见第 2 条。U5 若减少裸临时路径，实际需同步 `QUIZ_ANSWER_BASELINE`、越界清单及 `:562` 的硬编码裸值断言，并非只改交接常量。
- **sandbox 前提失效、严格恒真断言：未发现独立实例。** 现有负控目标都在复制的两个子树内；等值替换还有“替换确实发生”的前置断言。未改副本正控尚未纳入第四判据，但没有证据表明当前用例因此空跑。
- **symlink：未发现已证实的现存问题。** `normpath` 确实不能证明运行时落点；这限制了“实际指向哪里”的表述，但不足以把本静态门另判为运行时隔离缺陷。

本次未修改文件、未运行 pytest、未读取禁止正文，也未访问网络或数据库。

**本轮 BLOCKER 0 条，HIGH 1 条。**
