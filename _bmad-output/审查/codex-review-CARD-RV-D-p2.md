> 批次: BATCH-2026-09-05-第十二批 · 车道 Y6 · 卡 CARD-RV-D round-1 prompt-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-D-p2.md)"`
> 审查绑定: `514cff3c..e22ad10a`（固定审面，与 HEAD 无关）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

结论：**P2 部分成立，交接锚还不能承担可靠的自动提醒职责。** 本审面确认 3 项 MEDIUM、2 项 LOW；未确认新增 BLOCKER/HIGH。

仅读取指定 diff 和两份补充上下文；行号均从 diff 新侧重建。执行了纯内存的判据验证，没有运行写点、pytest、变异 harness 或连接数据库。

1. **MEDIUM：条目边界切错，新增的“整条比较”仍会漏掉重复键。**

   依据：`e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6438` 遇到不以四个空格开头的行就停止；`:6440` 返回的切片不包含终止行。

   在 A 完整条目之后、B 之前加入一个空行，再加入同值重复键：

   ```yaml
       abandoned: false

       abandoned: false
     - event_id: B
   ```

   空行不会结束 YAML 中的 A 条目，却会让 helper 提前停止。从 diff 原样提取 helper 后，纯内存验证得到：

   | 检查 | 结果 |
   |---|---|
   | 载体行出现一次 | 满足 |
   | 提取后的 A 块等于原 A 块 | 满足 |
   | 原 A 块紧跟 `calibration_log:` | 满足 |
   | PyYAML 解析前后内容相等 | 满足 |

   因而 `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6515`、`:6525`、`:6528` 三道判据全部放行，但真实条目已经多出重复键。**完整生产门及 `_canon_tree` 未运行。**

   最小改动：切片应跨过并保留空白、注释行，到实际的下一条同级条目或顶层键才结束；补“空行＋同值重复键”负控。

2. **MEDIUM：整条测试的 xfail 会把修复后的其他失败继续记为预期失败。**

   依据：`e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6294` 的 marker 设置了 `strict=True`，但没有限定预期失败类型，覆盖了整个测试体。

   用户列出的三种推演正确；第四种也明确存在：

   | 未来行为 | 实际结果 |
   |---|---|
   | ① 拒绝，账本零行 | `:6324`–`:6326` 正常返回 → **XPASS(strict)，红** |
   | ② 首写成功、身份正确、重跑成功 | 全部断言通过 → **XPASS(strict)，红** |
   | ③ 先落账再拒绝 | `:6325` 断言失败 → **XFAIL，静默** |
   | ④ 身份已经修好，但原样重跑失败 | `:6332` 断言失败 → **XFAIL，静默** |

   YAML 解析异常、缺少条目或 `event_id` 等其他失败，也可能落入同一个预期失败豁免。

   最小改动：**保留 `strict=True`，收窄预期失败范围。** 建议拆出普通测试约束拒绝路径；交接测试仅把已知身份伪造转换为专用异常，并用 `raises=该异常` 限定 xfail。其他解析、零写、重跑断言应正常报红。仅拆成两个仍然整段 xfail 的测试不能解决问题；安全拒绝路径也不能简单 skip，否则失去转正提醒。

3. **MEDIUM：交接锚的“拒绝 ⇒ 零写”实际上只检查账本行数。**

   依据：`e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6325` 只有：

   ```python
   assert len(_ledger_lines(vault)) == 0
   ```

   因此③须进一步区分：**已经落账**会静默 XFAIL；如果只改坏节点文件、账本仍为零，则测试反而会 XPASS，触发一个不充分的“可转正”信号。

   同一 diff 的时间戳测试在 `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6206` 保存写面，并在 `:6219` 同时比较写面和账本，交接锚没有对应检查。

   最小改动：调用前保存节点及受保护写面的状态，拒绝后检查其不变，并让该检查处于预期失败豁免之外。既有 `_write_face` 是否覆盖完整写面，**未验证**，其定义不在审面。

4. **LOW：“逐字节、含结束边界”的表述超过实际检查能力。**

   依据：`e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6514` 使用默认换行处理的 `read_text()`；`:6431` 拆行，`:6440` 再用 `"\n"` 拼接，返回值不含末尾换行或终止行。

   块内行尾空格没有被删除，**其变化能被发现**；但 LF 改成 CRLF 会在读取时归一。纯内存模拟相同读取行为后，三个判据全部通过。

   最小改动：读取并比较保留原始换行的切片，或把承诺明确收窄为“换行归一后的文本不变”。

5. **LOW：harness 的自我更正已进入代码，但调用处仍保留相反注释。**

   `e22ad10a:backend/scripts/g32cb_mutation_gates.py:204`–`:210` 明确登记原来已有 ANCHOR-ERROR 分支，不会因为锚漂就报告 8/8 KILLED；因此更正**并非只在 commit message**。

   但 `e22ad10a:backend/scripts/g32cb_mutation_gates.py:250` 仍写着：

   > 免得报出「8/8 KILLED」式假绿

   最小改动：改成“提前发现锚点失配，避免执行后续基线检查和测试”，消除同文件中的矛盾。

关于最重要的 E1/E2，其余判据核对如下：

- **E1 能识别。** `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6515` 在整个 `nd_after` 中计数，覆盖节点文件的 frontmatter 和正文。原行保留、别处再复制一份，会得到 2。它使用的是子串计数，并非独立行计数。
- **A 内部的 E2 键序重排能识别。** `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6525` 的整块比较已经承担这一职责；“紧跟 header”不是唯一判据。交换 A 内两条不同字段行，整块比较会失败。
- **仍有位移能同时满足全部三个条件：** 把 `calibration_log:` 连同整个 A/B 段一起移过另一个顶层键，例如 `attempt_count:`。计数、块内容、header 邻接均不变。这确实改变文件中既有行的相对顺序，但没有改变 A 内部顺序及其首条身份。`:6528` 没有固定整个段相对其他顶层键的位置。因此不能把该门描述为防止所有行序变化；若要求保护这种顺序，应补顶层键相对顺序检查。
- **第三阶段的 `rc==0` 补在正确位置。** `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6544` 原样重跑 A，`:6548` 立即检查返回值，随后才读取并比较 attempt。非零拒绝即使没有增加 attempt，也会失败；`:6560` 还检查 receipt 总数仍为 2。这个具体漏洞已在判据层堵住。

g32cb 的执行顺序也能从 diff 确认：

- 普通运行先安装信号处理、执行 `_self_heal()`，然后才自检；自检位于 SHA 基线之前。依据：`e22ad10a:backend/scripts/g32cb_mutation_gates.py:245`、`:251`、`:258`。因此“提前”不是早于自愈；锚命中数不为 1 时，在这里返回 4。
- **`--list` 同时校验锚点。** `e22ad10a:backend/scripts/g32cb_mutation_gates.py:239`–`:243` 调用 `_anchor_audit()`，通过返回 0，否则返回 4，并非只打印名称。
- 注释诱饵及仍保留原子串的缩进漂移，**新自检挡不住**：`:222` 仍只做整个目标文件的 `.count(old)`。盲区已在 `:212`–`:218` 登记。完整 runner 在这些情况下实际报什么，本审面没有运行验证。

新增测试的副作用与数量：

- **未发现新增生产模块补丁、模块常量赋值或生产源码写回。** 显式写删使用传入的 `vault` 路径，见 `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6136`、`:6204`、`:6314`。但真实路径隔离**未验证**：缺少 `vault` fixture、`NODE_REL` 和 `_run_writer_settled` 的定义，不能只凭参数名证明它们必然使用临时目录。
- 静态新增 **5 个测试函数**，分别位于 `e22ad10a:backend/tests/regression/test_g3_2_review_ledger.py:6045`、`:6125`、`:6184`、`:6222`、`:6305`；仅最后一个新增 xfail。补入既有测试的 tuple 样本及函数内部循环，不另外增加收集用例数。
- 因而新增量是 **4 个普通测试＋1 个 xfail 测试**，与 `339 passed / 1 skipped / 1 xfailed` **数量相容，但不能证明该历史汇总**。若其他结果不变，对应此前应是 `335 passed / 1 skipped`。
- 实际唯一 XFAIL 是否恰好来自这个 nodeid、是否失败在身份断言，均**未验证**；需要绑定 `e22ad10a` 的逐项测试报告和失败原因。历史 8/8 KILLED 同样未验证。

总评：**(b) 部分成立**——新增门明确检查两个 receipt-only 字段的 U+0085 往返及重跑，并分别检查本次 `ts`、`review_time` 输入；不足以从只读 diff 确认普遍“不可达”。**(d) 部分成立**——E1、A 内键序重排、非零拒绝伪装幂等的判据有效，但条目边界仍能漏过真实重复键，字节和位移承诺也需要收窄。**(e) 基本成立**——提前校验、带校验的 `--list` 和盲区登记均已落地，尚有一处矛盾注释。交接锚会在两种完整修法满足全部断言时自动提醒；**当前整体 xfail 也会掩盖部分修复后的其他失败，因此还不能作为可靠的交接闭环。**
