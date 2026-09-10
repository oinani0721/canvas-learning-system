> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r3.md)"`
> 审查绑定: `9303201a..98ca073c`（审时 HEAD = `98ca073c`，Codex 自证「结束时 HEAD 未变」；本轮后已提交 `83cd6104` 整改，round-4 另绑该 HEAD）
> 会话头自证（抄 .stderr 会话块；stderr 头三行是 models-manager 刷新报错，非会话头，自证取 `:4/:6/:7/:10/:11`；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: …/worktrees/card-u4-hosts`(:6) / `model: gpt-6-astra`(:7) · `sandbox: read-only`(:10) · `reasoning effort: ultra`(:11)

---

复核绑定 **`98ca073cde2282528300a214487b878ec4a2ac19`**；结束时 HEAD 未变，测试文件与该提交一致。仅使用指定材料和内存中的纯函数验证，未修改文件、运行 pytest、读取禁止正文或连接网络服务。

下述行号均属于 [backend/tests/skills/test_skill_portability_lint.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py)。

**BLOCKER：未发现。**

1. **HIGH — `test_skill_portability_lint.py:172、205`：左边界漏排 `/`、`+` 和非 ASCII 路径字符，嵌套路径仍能冒充命名空间。**

   将 diff 中 `start-exam-board/SKILL.md:198` 的原路径等计数替换为：

   ```python
   P = "/var/cache//tmp/cls-exam/exam-candidates.json"
   ```

   实测九项计数完全相同，`escaping_tmp_paths=[]`、`suspicious_tmp_lines=[]`，严格计数与 shell 子串计数也相同；但完整路径规范化后位于 **`/var/cache/tmp/…`**。`/var/cache+/tmp/…`、`/var/缓存/tmp/…` 同样绕过。两个正则共同把内部 `/tmp` 当作起点，行级判据没有命中条件。

2. **HIGH — `test_skill_portability_lint.py:205、255`：物理行切分漏掉确定的跨行路径穿越。**

   同一原赋值可替换为合法 Python：

   ```python
   P = ("/tmp/cls-exam/"
        "../exam-candidates.json")
   ```

   或使用反斜杠续行。实测九项计数不变、两个附加判据均为 `[]`；`ast.literal_eval` 得到 `/tmp/cls-exam/../exam-candidates.json`，规范化结果为 **`/tmp/exam-candidates.json`**。这不依赖未知变量，也不依赖 Markdown 渲染解释。

   **`:842–843` 的最终断言也不能兜底。** 将包含真实换行的路径 `"/tmp/cls-exam/a\nb/../../exam-candidates.json"` 直接喂给 `test_three_judges_cover_each_other_without_gap(..., 0, False, False, ...)`，整个用例实测通过，尽管完整路径规范化后越界；`startswith` 没有证明实际归属。此项并入同一 HIGH，不重复计数。

   上述两类替换的局部九项向量均保持：

   ```text
   (0, 0, 0, 1, 1, 0, 0, 0, 0)
   ```

   替换位置有引号边界，因此不会改变其余正文命中，整份文件九项计数也保持不变。

3. **MEDIUM — `test_skill_portability_lint.py:220`：“变量展开必须登记”仍漏掉位置参数和引号拼接。**

   `P="/tmp/cls-exam/$1"` 在参数为 `../x` 时越界，但三判据全放行；正则只接受展开中的 `[A-Za-z_]`，遗漏 `$1`、`${1}` 等。另一个实测漏检形态是：

   ```sh
   REL=../x
   P="/tmp/cls-exam/"$REL
   ```

   这里报告的是**没有要求登记**，不是要求静态门求解所有运行期变量。

4. **MEDIUM — `test_skill_portability_lint.py:607`：可疑行基线只绑定行号，已登记行的内容可以静默变质。**

   内存构造第 98 行，将：

   ```text
   ... P="/tmp/quiz-answer-incr.json"
   ```

   替换为：

   ```text
   ... P="/tmp/quiz-answer-incr.json,sub/../../x"
   ```

   九项计数相同，越界提取结果仍为 `/tmp/quiz-answer-incr.json`，可疑行号仍为 `[98]`；完整路径却规范化为 `/x`。登记没有绑定被审阅的内容。

   `[98]` **不会整体豁免 quiz-answer**：新增一个能被检测到的第 99 行会红；但第 98 行内部变化可以被掩盖。遵守读取边界，本轮**没有证据断言该文件当前存在其他真实问题**。

5. **MEDIUM — `test_skill_portability_lint.py:875`：删除 `OUT_OF_SCOPE_8011` 条目会静默停止监测，没有覆盖集合约束。**

   删除 `"mcp.json"` 后，该文件不再被遍历；设为 `{}` 时，计数比较成为 `{ } == { }`，`:890–891` 的交集断言也通过。验伪锚只证明登记项不在原覆盖面，不能证明登记项没有被删。这是 round-2 MEDIUM-2 同类问题在新常量中的再现。

6. **MEDIUM（保留的维护限制）— `test_skill_portability_lint.py:692`：零余量约束跳过原有两份 U6 脚本。**

   将 `inbox_preview.py` 的登记值改为 `tmp=1`，`check_handoff_constants(...)` 实测仍返回 `[]`；若脚本同步增加一次 `/tmp`，层 3 的精确计数也允许通过。**新增登记项必须为零的整改成立，原两份零余量没有被同样锁住**，仍依赖人工审阅基线变化。

7. **LOW — `test_skill_portability_lint.py:172、792`：合法短选项连写会误报。**

   `curl -o/tmp/cls-exam/exam-candidates.json` 的输出路径仍在命名空间内，但前置 `o` 使 `tmp_ns=0`；分开的 `-o /tmp/…` 为 `1`。前者还会触发严格计数与 shell 计数不一致，单改计数基线无法消除；需要改写命令形式。

六个交接用例**各自承重，未发现恒真或其他错误消息代为打红的缺陷**。独立删除对应判据后的结果是：

| 判据变异 | 失败用例 |
|---|---|
| 恢复 U6 精确集合限制 | 1：新增合规项必须放行 |
| 删除 seed 完整性检查 | 2：交接项缺失 |
| 删除地盘检查 | 3：非 U6 地盘 |
| 删除新增项零余量检查 | 4：新增项带债 |
| 删除 quiz 单列检查 | 5：quiz 并回主基线 |
| 删除重叠检查 | 6：重复登记 |

第 3 个输入同时触发重叠、地盘、非零三条错误，**并非只触发自己那条**；但 `:964` 指定要求地盘错误消息，删除该分支后测试仍失败，因此没有归因失效。

round-2 处置逐项结论：HIGH(a)、(c) 的原始具体漏检已拦住，推广后的缺口见上文；HIGH(b) 的误报仍存在，属于作者选择保守登记，并未消除。MEDIUM-2、MEDIUM-5、MEDIUM-6、LOW-8 的直接整改成立；MEDIUM-3、MEDIUM-4 的剩余边界分别见第 6、3 条。已声明的 MEDIUM-7 覆盖限制未发现新的仓内实物证据。新增替换负控有“替换确实发生”和目标判据断言，**未发现前提失败后静默空跑**。

基线维护路径如下：

| 维护方 | 需要同步的位置 | 遗漏结果 |
|---|---|---|
| U5-B | 指标变化时改 `QUIZ_ANSWER_BASELINE`；越界路径变化时改 `ESCAPING_TMP_BASELINE["quiz-answer"]`；可疑内容或行号变化时改 `SUSPICIOUS_TMP_LINES_BASELINE["quiz-answer"]`；裸值变化还需处理 `:742` 的硬编码 `==4` | 对应受测结果变化而漏改会红；已登记行同号变质可能静默通过 |
| U6 | 新增合规脚本登记到 `U6_SCRIPTS_BASELINE`；主基线脚本仍改 `SCRIPTS_BASELINE`；新带债脚本按当前规则走主基线审阅 | 新脚本未登记会红；原 seed 同步加债和更新计数存在第 6 条限制 |
| U3-C | 处理 `OUT_OF_SCOPE_8011` | 值不匹配会红；提前删项可能静默失明 |

除上述问题外，三套 per-skill 覆盖完整性、主／交接基线重叠检查及多重集次数诊断，**未发现新缺陷**。

**本轮 BLOCKER 0 条，HIGH 2 条。**
