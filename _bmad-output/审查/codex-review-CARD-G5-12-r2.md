> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-12 round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-12-r2.md)" > _bmad-output/审查/codex-review-CARD-G5-12-r2.md 2> _bmad-output/审查/codex-review-CARD-G5-12-r2.stderr </dev/null`
> 审查绑定: `5e608026`（不绑最终 HEAD——其后代码已按本轮意见整改（r2-HIGH-1/M1/LOW-1），移交 round-3）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

## 复核结论：PARTIAL——不建议本轮收口

我按只读边界复核，未运行 pytest、未连数据库/网络、未执行任何写盘命令。

### 绑定与整改面核验

- 当前 HEAD 确为 `5e6080267b8af81bafbb381116f8c3db60b7565e`。
- 排除 `_bmad-output/` 后，工作树与 HEAD 无差异；`1191dc1f..5e608026` 确认仅 `backend/tests/regression/test_sync_board_concepts.py`，`+163/-0`。
- 脚本 sha256 实测仍为 `282b7a968033f622cba03fae57e4330424c2465ad08d73f5abdc8f3162f6d123`。
- 旧 25 个测试函数名保留，当前为 26 个，新增仅为 `test_g512_user_region_hash_is_sensitive`。
- 但全仓 tracked 工作树并不干净：`_bmad-output/审查/evidence-g512/writers-census.md` 当前是 modified，详见 HIGH-1。

### r1 三条整改命题核对

1. **r1-M1：PARTIAL，不算真正整改完成。**  
   段边界/围栏方向确实收窄了，但段内 `_CONCEPT_LINE` 仍被无条件排除，没有实现脚本稳态下的“成员 + `_SCRIPT_LINE`/`_PLUGIN_LINE` 白名单”口径；非成员行和带自定义批注的成员行仍是脚本保留、helper 丢弃。
2. **r1-L1：PASS。**  
   h1b 第二遍现在先把可重建成员行换成 plugin 旧形态，再执行写模式同步；`stale not in final` 足以证明这次确实落盘。成员行在 helper 排除面内、stamp 在 sentinel 机器头内，用户尾巴仍由保护/回插路径保留，第三串 hash 的归因没有被二次写盘污染。
3. **r1-L3：PASS。**  
   `(e1)` 能钉住“ `_EMPTY_HINT` 排除不能空转”：若删除该分支，`with_hint` 会多出占位行而红；`(e2)` 能钉住“不能改成前缀匹配”：`_EMPTY_HINT + "x"` 若也被排除，不等式会红。
4. **r1-L2：登记不改可接受。**  
   脚本与 helper 都对 sentinel 尾巴做 `lstrip()`，因此承诺确实应表述为“非空文字逐字节”，而不是含前导空白的全字节不变；该限制已在清单/UAT 登记。

---

## BLOCKER

无。

## HIGH

### HIGH-1：送审证据未绑定到 `5e608026`，且“tracked 工作树干净”不成立

- `file:line`：`_bmad-output/审查/evidence-g512/writers-census.md:70`
- 缺陷：当前 tracked 文件有未提交修改；`5e608026` 里的同一行仍保留 r1 已指出的“TS 源码逐字同”不准确表述，本轮读取到的“已修正”证据并不是该 HEAD 的内容。
- 复现思路：门未覆盖的路径是 evidence-SHA 绑定；对照 `git status --porcelain=v1` 中的 `M _bmad-output/审查/evidence-g512/writers-census.md` 与 `git diff -- <path>`，可见 line 70 的修正只存在于工作树，`git show 5e608026:<path>` 仍是旧文案。

## MEDIUM

### MEDIUM-1：r1-M1 的核心残差仍在——helper 排除面仍宽于脚本真实收编白名单

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:86-88`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:434-445`
- 缺陷：helper 对 `## Concepts` 段内所有 `_CONCEPT_LINE` 形状行都排除，但脚本稳态下只收编“本板成员且匹配 `_SCRIPT_LINE` 或 `_PLUGIN_LINE`”的行，非成员行和带自定义文字的成员行会保留；`_EMPTY_HINT` 也被全文精确排除，而脚本只在空块 render 中产生它。
- 复现思路：未被拦下的输入是 `test_a2...` 中的 `- [[节点/成员甲]] 我卡在第 3 步` 或非成员 `- [[教材第三章]] 这本书第三章要重看`——脚本按 `:438-442` 保留，helper 按 `:86` 丢弃；若未来回归删掉这类行，新增 sha256 门不变。既有 a1/a2 子串断言能覆盖固定夹具，但不能支撑“用户文字区逐字节”的完整承诺。

## LOW

### LOW-1：helper 的段/围栏状态机与脚本定位算法仍有边界分歧

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:76-85`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:256-262`、`:282-304`
- 缺陷：helper 用 stripped 行识别标题并把 `---` 当段结束，而 `locate_section` 只认原始行 `## Concepts` / `##[^#]` 且不把 `---` 当结束；helper 对 ``` / ~~~ 不区分闭合字符并跨全文维持状态，而 `code_spans` 只在段内运行且要求同字符闭合。
- 复现思路：对照输入是带前导空白的伪 ` ## Concepts` 后接清单形用户文字，或段内 ``` 开栏后用 ~~~ 假闭合——helper 可把脚本不管理的清单行排除；`---` 后的成员机器行则是反向分歧，helper 会保留而脚本仍按 Concepts 段处理，可能造成未来假红。

---

计数：`BLOCKER 0 / HIGH 1 / MEDIUM 1 / LOW 1`


