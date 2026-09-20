> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-12 round-3
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-12-r3.md)" > _bmad-output/审查/codex-review-CARD-G5-12-r3.md 2> _bmad-output/审查/codex-review-CARD-G5-12-r3.stderr </dev/null`
> 审查绑定: `87ba9d66`（不绑最终 HEAD——其后代码已按本轮意见整改（r3-HIGH-1/M1/LOW-1），移交 round-4）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

## 复核结论：PARTIAL——代码行为面未发现 BLOCKER，但 r2-M1 未完全闭环，且负控证据的 final-SHA 绑定声明不成立

本轮只读复核：未运行 pytest、未连接数据库/网络、未写盘。当前 HEAD 实测为 `87ba9d6609e2c963ba219dfcf35796e71fd36a0a`；`git status --porcelain=v1 --untracked-files=no` 为空，tracked 工作树干净。脚本在 `1191dc1f / 371c21ae / 5e608026 / 87ba9d66` 中 blob 均为 `8fe83195678c77bdcd4b86455438427c7ed84268`，当前 sha256 为 `282b7a968033f622cba03fae57e4330424c2465ad08d73f5abdc8f3162f6d123`。

### 关键命题核对

- **r2-HIGH-1：PASS。**  
  `writers-census.md:69` 的修正文案已进入 `87ba9d66` 的 tracked blob；`5e608026..87ba9d66` 中该文件只有这一处表述修正。当前 tracked diff 为空。
- **r2-M1：PARTIAL。**  
  `_SCRIPT_LINE` / `_PLUGIN_LINE` 确实直接引用模块常量，没有手抄；自定义成员行也已留在区域内。但脚本真实删除条件还要求 `node_id in member_ids`，helper 目前只按“机器形状”排除，机器形状的非成员行仍会被误排除，见 MEDIUM-1。
- **r2-LOW-1：PASS，限本卡断言链。**  
  标题判定已改为原始行 `_CONCEPTS_HEADING`；段界已改为原始行 `_NEXT_HEADING`，不再把 `---` 当段界；围栏只在 Concepts 段内跟踪，并用 `_FENCE_RE` 同字符闭合。`code_spans` 的 4空格/tab缩进代码块仍未显式建模，但 `_SCRIPT_LINE` / `_PLUGIN_LINE` 都锚定行首 `-`，缩进机器行不会进入 helper 排除面；未发现对本卡 h1/h1b/self-test 的误红或漏红。
- **`(f)` 臂：PASS。**  
  `custom_a` / `custom_b` 若被 broad `_CONCEPT_LINE` 排除，两串会相等并红；当前不等式能钉住“带自定义文字的成员行必须在区域内”。
- **`(c)` 臂仍承重。**  
  `(e1)` 先证明脚本形态 `_SCRIPT_LINE` 的排除非空转，`(c)` 再证明 plugin 形态 `_PLUGIN_LINE` 与脚本形态映射相同；两者合起来覆盖两类机器形态。
- **测试保留：PASS。**  
  父提交到 `87ba9d66` 的测试 diff 为 `+176/-0`；测试函数从 25 个增至 26 个，新增仅 `test_g512_user_region_hash_is_sensitive`，既有断言未被删除。
- **负控结果：数值一致，但绑定见 HIGH-1。**  
  最新三段仍分别是：1a 两绿、1b `[begin_note_line]` 红、2 两参数均红；脚本还原 sha 均为 `282b7a96…`。`regression-dir-close2` 在 `87ba9d66` commit 时间之后运行，`1914 passed / 6 skipped / 1 xfailed`。

---

## BLOCKER

无。

## HIGH

### HIGH-1：最新负控存档没有绑定到 `87ba9d66`，“均在 87ba9d66 上重跑”的声明不成立

- `file:line`：`_bmad-output/审查/evidence-g512/negctl1a-spec-456-20260919T230329.txt:1`；同类还有 `negctl1b-protect-layer-20260919T230329.txt:1`、`negctl2-split-342-20260919T230329.txt:1`
- 缺陷：三份最新负控存档均自标 `HEAD=5e608026`，文件名/生成时间为 `23:03:29`，早于 `87ba9d66` 的 committer time `2026-09-19T23:04:22-07:00`，因此不能证明三段负控是在最终 SHA 的干净检出上运行。
- 复现思路：门未覆盖的路径是负控 provenance；对照存档第 1 行的 `HEAD=5e608026` 与 `git show -s --format=%cI 87ba9d66` 的 `23:04:22-07:00`，再把三个 `230329` 文件名/修改时间与 commit 时间对齐即可看出绑定缺口。

## MEDIUM

### MEDIUM-1：r2-M1 仍有残差——helper 白名单缺少“本板成员”条件，机器形状的非成员行会假绿

- `file:line`：`backend/tests/regression/test_sync_board_concepts.py:94-96`；对照 `canvas-vault/.claude/scripts/sync_board_concepts.py:434-443`
- 缺陷：helper 对所有匹配 `_SCRIPT_LINE` / `_PLUGIN_LINE` 的行都排除，但脚本先检查 `node_id in member_ids`，非成员行即使完全同形也会保留并告警，因此该行不属于脚本真实收编集合。
- 复现思路：未被拦下的输入是 Concepts 段内、围栏外的 `- [[节点/不是成员]] — 种子 · 待剖析占位`；对照输入是把 `不是成员` 换成本板在册成员——helper 两者都排除，而脚本只删除后者，前者按 `:438-440` 保留，未来误删该非成员行时 sha256 门不变。

## LOW

### LOW-1：writers-census §5 仍保留 r2 之前的旧排除面描述

- `file:line`：`_bmad-output/审查/evidence-g512/writers-census.md:102`
- 缺陷：census 仍写成排除所有 `_CONCEPT_LINE` 行和未限定块的 `_EMPTY_HINT` 行，而最终 helper 已改为“ Concepts 段内、围栏外、`_SCRIPT_LINE`/`_PLUGIN_LINE` 白名单”且 `_EMPTY_HINT` 仅限 BEGIN..END 块内。
- 复现思路：门未覆盖的路径是 evidence 文档一致性；对照 `backend/tests/regression/test_sync_board_concepts.py:53-58` 与 `:94-98` 的最终实现，可见 census §5 的判据描述没有随 r2-M1 整改同步更新。

---

计数：`BLOCKER 0 / HIGH 1 / MEDIUM 1 / LOW 1`
