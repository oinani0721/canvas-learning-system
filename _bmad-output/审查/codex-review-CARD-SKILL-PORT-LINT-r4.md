> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r4.md)"`
> 审查绑定: `9303201a..83cd6104`（审时 HEAD = `83cd6104`，Codex 自证「结束时 HEAD 未变，两个受改文件与提交一致」sha256=e386e458…；本轮后已提交 `4446ac81` 整改，round-5 另绑该 HEAD）
> 会话头自证（抄 .stderr 会话块；stderr 头两行是 models-manager 刷新报错，非会话头，自证取 `:4/:6/:7/:10/:11`；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: …/worktrees/card-u4-hosts`(:6) / `model: gpt-6-astra`(:7) · `sandbox: read-only`(:10) · `reasoning effort: ultra`(:11)

---

复核绑定 **`83cd61042d6d99f38537a70d7013a2bc6edc44a2`**；结束时 HEAD 未变，两个受改文件与提交一致。仅使用指定材料和内存验证，未修改文件、运行 pytest、读取禁读正文或连接服务。

以下定位均属于 [backend/tests/skills/test_skill_portability_lint.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py)。

**BLOCKER：未发现。**

1. **HIGH — `test_skill_portability_lint.py:194、227`：白名单未识别引号上下文，仍允许内部路径冒充命名空间。**

   将已有赋值等计数替换为：

   ```python
   P = "/var/cache(/tmp/cls-exam/exam-candidates.json"
   ```

   实测九项计数完全相同，`escaping_tmp_paths=[]`、`suspicious_tmp_lines=[]`，实际路径却在 `/var/cache(` 下。`"/var/cache /tmp/cls-exam/…"` 同样通过：**引号内部的开括号、空白是路径字符，不能直接充当路径起点证据。**

   替换不增加物理行，后续可疑行号不变。原 `/`、`+`、非 ASCII 三个具体反例已修，但冒充类别尚未封住。

2. **HIGH — `test_skill_portability_lint.py:290、295、325`：逻辑行合并仍遗漏合法拼接，五条判据仍存在等计数缺口。**

   将 diff 可见的原赋值及下一条读取语句，等物理行数替换为：

   ```python
   P = ("/tmp/cls-exam/"
        '../exam-candidates.json'); p = json.load(open(P, encoding="utf-8"))
   ```

   Python 允许不同引号的相邻字面量拼接；当前实现却保留两个逻辑行。实测九项计数相同、越界结果和可疑行结果均为空，实际规范化为 **`/tmp/exam-candidates.json`**。两行换两行，`:577` 不会移位代抓。

   更小的同一行反例也已验证：

   ```python
   P = ("/tmp/cls-exam/" "." "./exam-candidates.json")
   ```

   原文没有连续 `..`，两个附加判据均放行，求值后仍穿越。以上是五条判据的缺口；本轮没有执行整套测试。

3. **MEDIUM — `test_skill_portability_lint.py:227、677`：已登记行仍只绑定行号，ASCII 逗号整改没有封住内容变质。**

   沿上一轮报告提供的内存第 98 行模型，将：

   ```text
   ... P="/tmp/quiz-answer-incr.json"
   ```

   替换为：

   ```text
   ... P="/tmp/quiz-answer-incr.json，sub/../../x"
   ```

   中文逗号仍截断 token；实测九项计数、越界多重集、可疑行号 `[98]` 全部不变，完整路径却规范化为 `/x`。引号内分号也能复现。**原 ASCII 反例已修，原 MEDIUM-4 的根因仍在。**这不代表禁读正文当前存在该输入。

4. **MEDIUM — `test_skill_portability_lint.py:1284、1295`：新增跨行负控被后续登记行移位代为打红。**

   该替换增加一行，使原登记行 `577→578`。内存复验：

   | 判据实现 | 可疑行号 |
   |---|---|
   | 当前合并逻辑 | `[198, 578]` |
   | 完全取消合并 | `[578]` |
   | 基线 | `[577]` |

   两种实现都满足当前“含 skill 名和 `[可疑行]`”的断言，因此**此负控自身不承重**。覆盖表中的独立拼接样本仍能发现完全取消合并，不能据此说整套回归保护失效。

5. **MEDIUM — `test_skill_portability_lint.py:745、763`：U6 seed 按新指示移入主基线，必被 seed 完整性断言阻断。**

   实测 `inbox_preview.py` 登记 `tmp=1`：留在 U6 表会报零余量错误；移入 `SCRIPTS_BASELINE` 又报“U6 交接项被删”。**零余量拦截已修好，但指定的人工审阅迁移路径不可完成。**

6. **MEDIUM — `test_skill_portability_lint.py:972、976`：动态扫描会读取未跟踪状态，并可通过文件符号链接读出扫描根。**

   若子树出现备份、日志、缓存或指向树外文本的文件符号链接，当前 `rglob → is_file → read_text` 都可能读取；没有 tracked/ignore、链接目标或大小限制。扫描还会收集完整路径列表、整文件解码。

   UTF-8 可解码的二进制也可能被计数；非法 UTF-8、不可读文件则被静默跳过。这里报告的是代码可确定的条件性副作用，**未实际扫描树，也未发现现存泄读或性能故障的证据**。

7. **LOW — `test_skill_portability_lint.py:194`：遗漏正常散文分隔符，会新增保守误报。**

   `路径：/tmp/cls-exam/x`、`路径，/tmp/cls-exam/x` 实测 `tmp_ns=0`，加空格后为 `1`。这也会触发与 shell 子串计数不一致；不能只修改基线消除。

8. **LOW — `test_skill_portability_lint.py:291、297`：无关前行的引号编辑也能改变可疑行号，不需要插入行。**

   对 `Normal prose.` 下一行的 `"/tmp/cls-exam/$REL"`，只在前行末尾增加 `"`，可疑行号便从 `[2]` 变为 `[1]`。合并没有区分散文与真实拼接上下文，基线因此脆弱。

9. **LOW — `test_skill_portability_lint.py:227`：ASCII 逗号会污染合理散文中的越界条目。**

   将 `Write /tmp/exam-created-event.json then…` 改成 `.json, then…`，实际路径未变，越界条目却变为 `/tmp/exam-created-event.json,`。当前列出的基线中**未发现已有这种垃圾条目**。

10. **LOW — `test_skill_portability_lint.py:929、1038`：两处整改缺少能捕获回退的负控。**

    覆盖表实际是 **12 行**，逐项纯函数调用均通过；最终 normpath 断言仅在前两条普通合规路径执行，退回旧 `startswith` 仍全部通过。另将 seed 豁免恢复为 r2 逻辑，现有六条交接用例也全部通过，因为非零负控只测试新脚本。

11. **LOW — `test_skill_portability_lint.py:623、708`：额外指标键没有断言消费。**

    例如增加 `SCRIPTS_BASELINE["scripts/decay_beta.py"]["p8011"] = 1`，检查仍只遍历三个 `SCRIPT_METRICS`，该新增登记不会受到检查。七张表本身均被消费；缺口是**指标键集合没有精确校验**。

其余负控维度：ASCII 逗号变质、双斜杠冒充均有替换成功前提及目标判据断言，**未发现空跑或其他判据代打红**。变量负控直接验证可疑行函数，拦截成立；但它采用追加，正文计数也会变化，因此没有证明整个门只能靠可疑行拦截。

round-3 七条处置逐项结论：

| 原意见 | 本轮结论 |
|---|---|
| HIGH-1 | 三个原始样本已修；上下文冒充仍在，见第 1 条 |
| HIGH-2 | 原同引号样本已拦；其他合法拼接仍漏，负控还有移位干扰 |
| MEDIUM-3 | `$1`、引号外 `$REL` 已拦，未发现这两个具体整改失效 |
| MEDIUM-4 | ASCII 原例已修；登记行变质类别仍在 |
| MEDIUM-5 | 可读、仍含 `8011` 的文件，删登记不再静默通过；新增扫描副作用见第 6 条 |
| MEDIUM-6 | seed 非零已拦；移表路径冲突、回归负控不足 |
| LOW-7 | 保留的误报已登记，未消除；无需重复算作新缺陷 |

基线维护矩阵如下：

| 维护方 | 七个常量中需要同步的位置 | 遗漏与额外约束 |
|---|---|---|
| U5-B | `QUIZ_ANSWER_BASELINE`；按结果变化更新 `ESCAPING_TMP_BASELINE["quiz-answer"]`、`SUSPICIOUS_TMP_LINES_BASELINE["quiz-answer"]` | 受测结果变化而漏改会红；裸值变化还需处理 `:813` 的硬编码 `==4`。同号内容变质可能静默通过 |
| U6 | 原 seed、新增零债脚本用 `U6_SCRIPTS_BASELINE`；原在主表的脚本用 `SCRIPTS_BASELINE` | 新脚本漏登记会红；seed 移表目前被阻断。若修改 SKILL.md，还可能牵涉 `BASELINE`、越界表和可疑行表 |
| U3-C | `OUT_OF_SCOPE_8011` | 次数或发现文件键变化会红；模板保留缺省 `8011` 且次数不变则不会红。迁移到 `.template` 仍会被扫描，应更新键，不能一律删条目 |

`_discover_out_of_scope_8011` 测量的是 **`8011` 字面量次数**，因此“模板化必红”和“红就说明仍写死端口”都不成立。除上述问题外，七表的既定指标消费、skill 覆盖完整性及主表／交接表重叠检查，**未发现新缺陷**。

**本轮 BLOCKER 0 条，HIGH 2 条。**
