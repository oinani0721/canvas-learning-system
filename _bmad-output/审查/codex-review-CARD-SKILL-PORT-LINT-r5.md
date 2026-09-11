> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-5（D-15 上限最终轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-r5.md)"`
> 审查绑定: `9303201a..4446ac81`（审时 HEAD = `4446ac81`，Codex 自证「结束时 HEAD 未变，两个受改文件与提交一致」；本轮为第 5 轮上限，仍有 HIGH ⇒ 按 D-15 停下交主 session 人审，车道不再改代码）
> 会话头自证（抄 .stderr 会话块；stderr 头三行是 models-manager 刷新报错，非会话头，自证取 `:4/:6/:7/:10/:11`；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(:4) / `workdir: …/worktrees/card-u4-hosts`(:6) / `model: gpt-6-astra`(:7) · `sandbox: read-only`(:10) · `reasoning effort: ultra`(:11)

---

复核绑定 **`4446ac816d9934c3bf393867db5d461870f1488e`**；结束时 HEAD 未变，两个受改文件与提交一致。仅使用限定材料和内存纯函数验证，未修改文件、运行 pytest、读取禁读正文或连接服务。

**BLOCKER：未发现。**

**HIGH：发现 4 类缺陷。**

1. **HIGH — [test_skill_portability_lint.py:306](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:306)、`:345`：误拼独立参数会掩盖真实越界，方向并非只有误报。**

   在普通 fence 内，将：

   ```sh
   cp "/tmp/cls-exam/a" "/tmp/cls-exam/x"
   ```

   替换为：

   ```sh
   cp "/tmp/cls-exam/a" "/var/cache(/tmp/cls-exam/x"
   ```

   `shlex.split()` 确认目的路径是独立的越界参数；拼组函数却得到：

   ```text
   /tmp/cls-exam/a/var/cache(/tmp/cls-exam/x
   ```

   该组仍位于命名空间前缀下，而实现只检查组、不独立检查各字面量。实测九项计数完全相同，`tmp_all=tmp_ns=2`，越界与可疑行均为 `[]`。

2. **HIGH — [test_skill_portability_lint.py:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:278)、`:281–288、338`：扫描结果不正确对应语言字面量，存在错误闭合、吞尾和转义漏检。**

   两个可直接替换原 `P` 赋值的合法 Python 常量：

   ```python
   P = """/var/cache"/tmp/cls-exam/exam-candidates.json"""
   ```

   ```python
   P = "/tmp/cls-exam/\x2e\x2e/exam-candidates.json"
   ```

   第一例被扫描成空串、`/var/cache`、空串，路径尾部消失；第二例保留源码转义，没有识别出确定的 `..`。`ast.literal_eval()` 证明实际路径分别位于 `/var/cache"` 下、规范化为 `/tmp/exam-candidates.json`。

   两例与原赋值九项计数完全相同，越界与可疑行均为 `[]`，且不增加物理行。

   shell 单引号也存在同类吞尾：`cp '/tmp/cls-exam/\' "/var/cache(/tmp/cls-exam/x"` 中，反斜杠并不转义单引号，扫描器却吞到行尾。因此“未闭合取行尾，多抓不少放”的保证不成立。

3. **HIGH — [test_skill_portability_lint.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:255)、`:306、379`：合法 Python 拼接仍会漏拼。**

   最小单行反例：

   ```python
   P = ("/tmp/cls-exam/" r"." "./exam-candidates.json")
   ```

   `r` 前缀阻断间隙匹配，组结果为：

   ```text
   ['/tmp/cls-exam/', '../exam-candidates.json']
   ```

   Python 常量实际规范化为 `/tmp/exam-candidates.json`；九项计数不变，两个附加判据均为空。`u` 前缀同病。

   跨行行尾注释、行尾 `+` 也会阻断合并。例如以下两行可替换原赋值及读取两行，避免后续行号移位：

   ```python
   P = ("/tmp/cls-exam/" +
        "." "./exam-candidates.json"); p = json.load(open(P, encoding="utf-8"))
   ```

   实测同样等计数、越界为空、可疑行为空。

4. **HIGH — [test_skill_portability_lint.py:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:262)、`:343–349`：fence 识别遗漏会关闭字面量和拼组保护。**

   将代码块使用合法的 `~~~python` 标记，`P = "/var/cache(/tmp/cls-exam/x"` 就被当作散文处理；与安全赋值等计数，越界、可疑行均为空。

   四反引号外层代码块中的三反引号内容行也会错误切换状态；已用包含该内容的合法 Python 三引号字符串复现。另因标记行被删除，相邻独立代码块还可能跨块合并，形成第 1 条的遮蔽。

   **普通未闭合三反引号 fence：未发现漏检**，它会持续保持代码上下文。

上述第 2、3 条的单路径反例，局部九项向量均保持：

```text
(0, 0, 0, 1, 1, 0, 0, 0, 0)
```

它们可就地替换 diff 中的原赋值，frontmatter、scripts 和后续可疑行号不变，因而构成五条判据合起来的等值缺口。这里证明的是判据贡献等值，未声称运行过整套测试。

**MEDIUM：发现 1 条未声明的静态盲区。**

5. **MEDIUM — [test_skill_portability_lint.py:339](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:339)、`:534、632`：去重加上正文不计裸 `/tmp`，让新登记项成为可重复使用的盲区。**

   在已有“禁写 `/tmp`”声明的文本中，新增：

   ```python
   P = "/tmp"
   ```

   实测九项计数仍全零，越界集合仍只有 `('/tmp', '/tmp')`，可疑行仍为空；新增的命名空间外字面量不会要求登记。

   去重也无法察觉已有越界路径之间的次数重新分配：`A,A,B → A,B,B` 的总计数和越界集合均不变。集合语义已声明，但这些漏检后果没有如实界定。

**LOW：断言与维护边界。**

6. **LOW — [test_skill_portability_lint.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1025)、`:1056`：分号变质覆盖行不承重。**

   该行只要求越界结果非空；即使重新在分号处截断，原 `/tmp/quiz-answer-incr.json` 自己已经越界。内存变异让扫描结果在分号／中文逗号处截断后，**全部 16 行覆盖表仍通过**，但目标 `/x` 已消失。

7. **LOW — [test_skill_portability_lint.py:348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:348)、`:528–530、746–748`：三条新基线会产生容易误解的红，但其中保守性已有登记。**

   仅调整 `mkdir` 命令的 backtick 包围范围，计数及命令含义不变，越界集合就会增加或缺失 `Bash: mkdir -p /tmp/cls-exam`；仅去掉“禁写 `/tmp`”中的 backtick 也会使登记项缺失。因此红表示**文本基线漂移**，不能直接解释成新增真实越界或完成整改。

   U6 若修改相关 SKILL 文本可能遇到；仅修改 scripts 不会触发这些条目。它们也不会直接影响 U5-B 的 quiz-answer 条目。限定读取下，**未独立重算三条登记在原正文中的出现位置**。

8. **LOW — [test_skill_portability_lint.py:1104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1104)：跳过目录内容并未消除递归枚举成本。**

   `.git`／`__pycache__` 判断发生在 `sorted(root.rglob("*"))` 之后；存在巨大目录树时仍会遍历并收集全部路径。文件链接内容及超大文件整读的整改成立，**未发现现存性能故障证据**。

r4 十一条处置逐项结论：

| 原意见 | 本轮独立结果 |
|---|---|
| HIGH-1 | 原空格／括号冒充样本已拦；新的遮蔽与字面量语义缺口见第 1、2 条。 |
| HIGH-2 | 原混合引号和单行点号样本已拦；合法拼接遗漏见第 3 条。 |
| MEDIUM-3 | 原分号／中文逗号完整字面量已能识别；新增回归断言不足见第 6 条。 |
| MEDIUM-4 | 原行号移位代红问题已解决；当前直接断言未发现该归因失效。 |
| MEDIUM-5 | 已修：seed 带债迁入主表放行，留驻 U6 拦截。 |
| MEDIUM-6 | 指定内容读取限制成立；未跟踪文本继续读取是明确选择；枚举成本仍在。 |
| LOW-7 | 保守误报已登记，未消除。 |
| LOW-8 | 已限制为 fence 内合并，原散文引号搬动行号问题已修。 |
| LOW-9 | fence 裸 token 尾逗号误报已登记，未消除。 |
| LOW-10 | normpath 末尾断言的限制已声明；seed 留驻回退保护已补齐。 |
| LOW-11 | 已修：额外指标键会被精确键集断言拒绝。 |

覆盖表实际 **16 行，非 17 行**；交接表 **8 行**，直接调用均通过。取消逻辑行合并或拼组后，对应覆盖行确实失败；对照组也已补齐五条判据。除第 6 条外，**未发现新的前提空跑或其他判据代打红实例**。

收尾判断：**不能认定残余风险只剩已登记误报和运行期不确定性**；以上仍包含可静态确定、未经声明的漏检。

**本轮 BLOCKER 0 条，HIGH 4 条。**
