> 批次: BATCH-2026-09-11-第十四批 · 车道 T10 · 卡 CARD-RED-HYGIENE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-HYGIENE.md)"`
> 审查绑定: `8bfcdfcea46c8e2c6408fa6ebd85851c7c9cce82`（⚠️ **不绑最终 HEAD**：审查期间本 session 按只读对抗自审的结论提交了 `b38e1d04`，Codex 在报告末尾已自行实测并如实声明「diff 非空：3 files changed, 27 insertions(+), 9 deletions(-)」。本轮据 D-15 不作终审，整改后另送 r2。）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，逐行括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

**本次不能判为通过：目录级重跑未复现 `>0`，且模板 guard 存在可复现漏检。** 配置退役、鉴权对照和六文件地盘检查成立。

以下问题及行号均绑定 **`8bfcdfce`**。审查期间其他进程修改并提交了文件，结束时 HEAD 已推进至 `b38e1d04`；本报告不构成对新提交的复核。我未修改项目文件。

**BLOCKER: 0**

**HIGH: 1**

1. **目录级“不增”与零连接尝试判据未通过；尚不能归因于本卡。**

   位置：`backend/tests/unit/test_review_app.py::_run_node/:917`、`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422/:168`。

   实际执行指定命令，基线非注释行及去重 nodeid 均为 **64**：

   ```bash
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit \
     --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
   ```

   | 运行条件 | 实际结果 | `<` | `>` | 端口哨兵 |
   |---|---|---:|---:|---|
   | 原环境 | 67 failed、5133 passed、35 skipped、19 xfailed | 30 | 33 | blocked=0 |
   | 仅将 PATH 前置已有 Node v24.16.0 | 35 failed、5165 passed、35 skipped、19 xfailed | 30 | 1 | blocked=1、advisory=0、unaccounted=0 |

   第一跑新增的 33 条全部是 Node 缺少 `libllhttp.9.3.dylib` 导致启动失败。第二跑唯一新增 nodeid 是上述已知 candidate flaky；随后单跑它为 **1 passed，blocked=0**。

   **失败场景：** 原环境无法启动 Node；换用可运行 Node 后，目录组合运行仍出现已知 flaky，并记录一次被阻断的连接尝试。连接未建立，单跑绿色也不能替代目录结果。

   **处置：登记移交环境故障及 flaky，保留本次失败记录。** 这是当前验收阻断，不是已经证明本卡引入生产回归；不能采用旧存档的 `>0 / blocked=0` 宣告本次通过。

**MEDIUM: 3**

1. **模板 guard 会漏掉初始化后的名单变化。**

   位置：[test_agents_health.py::_production_expected_templates](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/api/v1/endpoints/test_agents_health.py:473)，原提交 473–482、498–499。

   实跑 `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -B -c ...`，从 `git show 8bfcdfce:<文件>` 抽取真实 helper/guard，仅在内存替换 `inspect.getsource` 输入：

   ```text
   原名单：                         GUARD_PASS extracted=13 runtime=13 equal=True
   expected_templates += ["new"]：  GUARD_PASS extracted=13 runtime=14 equal=False
   expected_templates[0]="renamed"：GUARD_PASS extracted=13 runtime=13 equal=False
   ```

   `ast.walk` 还可能取到嵌套函数中的同名赋值，而遗漏外层带注解赋值。当前生产的简单字面量取值正确，但“增删改名换序任一发生都会红”不成立。

   **处置：修。** 限定实际作用域，对不支持的后续写入形态明确失败，并收窄覆盖声明。

2. **第零分钟“工作树干净”的证据不足。**

   位置：`minute0-20260916T021417.txt:10–11`。

   实读存档得到“须 0”，实际 **1**，没有 porcelain 原始路径。**空目录本身不会被 Git 计入脏项**；若重定向已创建正在写入的证据文件，则可以解释为 1，但现有存档无法证明这一点，也无法排除其他脏项。

   **处置：补当时原始路径证据，或明确记为未证实。** 不能判定确实掩盖了其他修改，也不能接受“仅 mkdir”作为充分解释。

3. **最终 commit 的 `python-typecheck` 实跑未被独立证明。**

   位置：`lefthook-exclude-justification-20260916T132600.txt:6–19`；`lefthook.yml::python-typecheck/:218–231`。

   实查：

   ```bash
   rg -n 'python-typecheck|Running pyright|Typecheck done|LEFTHOOK_EXCLUDE' \
     _bmad-output/审查/evidence-red-hygiene
   ```

   被审提交内只有**首次失败提交尝试**的 `✔️ python-typecheck (3.07 seconds)` 摘录，没有最终提交的完整执行输出。该 hook 在工具缺席时也会明确 SKIP 并返回 0，故勾号不足以证明实跑。

   当前指定 `$P app` 原环境因 Node 动态库缺失启动失败；仅前置已有 Node v24.16.0 后，实际得到：

   ```text
   0 errors, 81 warnings, 0 informations
   ```

   **处置：历史执行项标记 PARTIAL，补最终提交原始 hook 输出。** 当前检查通过不能追认历史执行；也没有证据断言它确实被跳过。

**LOW: 4**

1. **“零 await 等于 handler 正文未执行”措辞过宽。**

   位置：`test_system_endpoint_auth.py::_handler_was_not_reached/:177–189`。实读 `system.py::test_llm_connection/:893–901`，模型格式化等语句位于 LLM 调用之前。

   零 await 只能直接证明未走到 LLM await，不能单独证明前面语句未执行。当前路由依赖声明及对照共同支持鉴权前置，未发现现存鉴权漏洞。**建议修正文案。**

2. **少量计数、索引说明不准确。**

   - `auth_client_with_llm_spy/:162` 写“既有 12 条”；实跑 `git show f294878b:<文件> | rg -c '^    def test_'` 为 **10**，新增后才是 12。
   - `test_cache_configuration.py:6` 仍列出已删除的 retry Settings 测试。
   - 格式豁免存档 `:69` 的 PREV 行号不准确：独立 stdin 格式化、`difflib` 重算，实际修改行是 **PREV 284–286 → 被审 SHA 247–249**。

   **建议修说明。** 不影响实际测试计数或格式豁免结论；前两项后来出现的外部修改不计入本 SHA。

3. **定性结论超出了采样证据。**

   位置：commit message 的 flaky 定性；`contract-nodeid-CORRECTED-20260916T130606.txt:6–7、29、44`。

   实读各五次单跑及整文件绿色记录，只能证明这些运行未复现，不能推出“排除同文件互扰、源于跨文件”。删除前 schema 与当前模型相同，也不能证明历史“从不存在 pattern 分歧”。

   **建议修为有限结论，根因继续登记移交。** 当前契约失败身份确为文件缺失，不受这些措辞问题影响。

4. **最终地盘证据未进入被审提交。**

   `git ls-tree -r --name-only 8bfcdfce -- <证据目录>` 得到 **22 份**存档；`territory-headcommit-20260916T144321.txt` 不在其中，而 `territory-worktree:38–39` 指向它作为替代证据。

   **建议补齐归档链。** 我独立检查确认代码面确为六文件，OpenAPI 与父提交相同，所以这是归档缺口，不是地盘越界。

六个反面问题的直接回答：

1. **退役是否漏消费方：未发现。**  
   `git grep` 在 PREV 的 `backend/app` 仅命中两字段定义，删除后零命中；取消四目录排除也未发现真实消费者。另检查动态 `getattr`、Settings 字典导出及环境覆盖路径，没有读这两键的生产路径。`Settings.model_config/:927` 为 `extra="ignore"`；以内存旧 `.env` 内容和非法旧环境值构造真实 Settings 均成功，两键不再作为属性或 `model_dump()` 字段出现。旧部署残留键被忽略。

2. **鉴权断言是否恒真、是否污染：不成立。**  
   对照保持同 fixture、配置、payload、端点，仅覆盖鉴权依赖，要求 `200` 且实际 await 大于零；错 patch、错端点、同 payload 被 422 阻断都会使对照失败。fixture 在原提交 `:174` 最终 `clear()`，测试内只 `pop` 不会留下 `get_settings` 覆盖。M1/M2 对照红、M3 承重红，存档身份及前后哈希一致。其证明范围限制见 LOW-1。

3. **AST guard 是否漏路径：有，见 MEDIUM-1。**  
   两条断言均非恒真。常量/文件读取会触发非列表断言；单独改为注解赋值会因找不到赋值而红；非字面量元素会异常失败，不会被吞成绿。空列表也不能通过最终比较。改名负控准确证明了**当前字面量形态下，等长改名被 equality 捕获**，没有证明所有后续生产形态。

4. **目录级是否真的没有 `>`：本次不是，见 HIGH-1。**  
   旧存档的 `<30 / >0` 自身对账成立。我进一步比较 PREV 已入库的 `epw-unit-close7.nodeids` 与本卡存档，双方同为完全相同的 **34 条红**，因此“本卡贡献 0”有支持；原先仅凭本卡测试文件不在 BASE 的推理不充分。

5. **pyright 是否跳过：历史最终提交未证实；当前源码可通过。**  
   已实际运行指定绝对路径，未用 `tail -1`。默认 Node 损坏；仅调整本次进程 PATH 后为 **0 errors**。两者不能混写成“原命令直接通过”。

6. **(e)(g) 只定性不改是否合理：合理。**  
   它们在明确禁改范围，应该移交。契约文件独立重跑为 **1 failed、49 passed**，失败在 `:157 open()` 的 `FileNotFoundError`。本次还重新观察到了 candidate 的目录红、单跑绿；移交合理，但不能据此豁免目录验收失败。

其余判据实核结果：

- **目标测试：** 四个文件合跑 **41 passed、4 xfailed**，其中 health 13、auth 两文件 19、cache 9 passed/4 xfailed。health 的 RED 两个断言身份、12→13 passed，以及改名负控 `1 failed/12 passed` 均与存档一致。
- **退役算术：** `3F+7P+5X`，删除 **1F、1X**，修复其余 **2F**，严格得到 `9P+4X`；删除的严格 xfail 没有被算成转绿。
- **格式豁免：** 五个 Python 文件 lint 全通过；仅 cache 文件有既有格式漂移。实际漂移行与本卡改动不相交，豁免依据成立。
- **OpenAPI、地盘：** 只读 `check-openapi-drift.py --snapshot backend/openapi.json` 返回 `DRIFT: none (paths=197 schemas=357)`；六文件边界成立。T5 在旧行 725 附近新增字段，本卡删除旧行 640–655，hunk 不重叠。
- **作废证据：** 两份 `SUPERSEDED` 均诚实保留并指出原错误；替代记录修复了无效 lint 锚及“历史输出非空却写为空”的问题。`territory-worktree` 的第三个错误锚也已明确作废。仍存在的过度推断见 LOW-3。

**绑定声明：本次审查 SHA 为 `8bfcdfcea46c8e2c6408fa6ebd85851c7c9cce82`；结束时 HEAD 为 `b38e1d04c074214570916d11f434933a47edaf36`，执行 `git --no-pager diff --stat --no-color 8bfcdfcea46c8e2c6408fa6ebd85851c7c9cce82 HEAD -- . ':(exclude)_bmad-output'` 非空：3 files changed，27 insertions(+)，9 deletions(-)。**


