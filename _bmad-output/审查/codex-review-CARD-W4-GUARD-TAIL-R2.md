> 批次: BATCH-2026-09-18-第十五批 · 车道 P9（card-p9-testinfra） · 卡 CARD-W4-GUARD-TAIL-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-GUARD-TAIL-R2.md)"`
> 审查绑定: `ec245c8c`（= 送审时 HEAD；Codex 正文首句自报 `ec245c8ce105dc67103ce70b6fcff41b9e447801`，首尾未变）
> 会话头自证（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 4 行） / `model: gpt-6-astra`（第 7 行） / `reasoning effort: ultra`（第 11 行）

---

审查绑定 **`ec245c8ce105dc67103ce70b6fcff41b9e447801`**，首尾未变。全程只读、无网络连接；复现使用内存源码、子进程和管道，没有重跑会写盘的完整 pytest。

**BLOCKER / HIGH：未发现本卡新增项。MEDIUM：1 项；LOW：3 项。** A 格归因成立，但“全部收紧、没有红转绿”不成立。

1. **MEDIUM — 块外过滤会漏掉不同身份，实际出现 `rc=2 → rc=0`。**  
   位置：[w4_sentinel_identity.py:422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/support/w4_sentinel_identity.py:422)。

   **未被拦下的输入**：正常 C 块后追加抬头变成“本用例期间有大约”的块，其中记录截断为：
   ```text
   - ('127.0.0.1', 7691) on thread OtherThread (owner=
   ```
   与仅含正常块的**对照输入**使用相同四元组 `(2,2,0,0)`。通过管道调用真实 `main()`，基线返回 **2**，HEAD 返回 **0 / CONSISTENT**，另一身份被忽略。

   重复记录豁免也让旧 r4 原输入——正常块加同记录的漂移块——从 **2 变 0**。它不损失身份集合元素，却损失块来源与结构完整性检查；[test_w4_sentinel_rebind.py:520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_w4_sentinel_rebind.py:520) 换成不同记录，确实收窄了原门。另外，豁免前经过 ANSI 清理及 `strip()`，并非逐字节相同。

2. **LOW — 截断门把“未发生写盘”也归成权限不受强制。**  
   位置：[test_live_port_guard_contract.py:1852](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/backend/tests/unit/test_live_port_guard_contract.py:1852)。

   **复现思路**：让发布锁超时，使 `_publish_ledger` 返回 `False`；代码直接进入 `pytest.skip`，旧字节、发布序和陈旧发布断言全部未执行。root 在 `:1847` 也会固定 skip；限定证据中没有“必须至少一次非 skip”的 CI 验收约束，属于**门未覆盖的路径**。

3. **LOW — 三文件绿档缺最终退出码，目录档缺最终源码绑定。**  
   位置：[named-green-postfmt-20260918T172853.txt:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-w4-guard-tail-r2/named-green-postfmt-20260918T172853.txt:57)。

   末行只有 `243 passed`，没有进程 rc；api/regression/skills 的 open 档亦然。**复现思路**：以 pytest 总结之后才改变退出码的收尾行为作**对照输入**，这些档无法区分。目录执行档也没有命令与源码哈希，不能仅凭 open/close 文件名证明绑定最终 HEAD。

4. **LOW — AST 辅助脚本的退出码不能作为门。**  
   位置：[ast-gate.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra/_bmad-output/审查/evidence-w4-guard-tail-r2/ast-gate.py:59)。

   **负控输入**使用基线，输出 `head_has_typealias=False`，脚本仍在 `:63` 返回 0。两侧文本判词正确，但自动验收必须检查判词，不能只检查脚本 rc。

其余问题的核对结果：

| 问题 | 结论 |
|---|---|
| **0：A 格归因** | **PASS。** 当前 HEAD 内存负控仅撤掉目标嵌套保护：A **3→0**，B **3→3**。出口追踪只到 `_final_accounting:1556`，未到迟到出口 `:823`。唯一事件发生在结算前；若提前退出，就无法满足 CHILD-JSON 前提。C 因需要成功写盘，本轮未重跑；存档为绿，静态上不经过该错误报告分支。 |
| **1：权限与断言顺序** | 正常文件权限约束下，文件自身 `0400` 会在截断前拒绝写打开；现有 Darwin、UID 501 存档明确是 **PASS，非 skip**。这不能外推到所有 ACL/文件系统状态。负控 `negctl-3` 中，新门停在 `:1861`，确实没有执行后面的陈旧发布断言；既有失败写盘测试另行在 `:1811` 报红，因此两侧有组合证据，不能说新门独自证明两侧。 |
| **2：TypeAlias** | **3.14.4 实测 PASS。** 普通、泛型、`*Ts`、`**P`、默认类型参数及中文名称均得到 `ast.Name`；属性、下标目标不是合法源码。真实 `install()` 通过。另须区分：helper 的空元组退化兼容旧解释器，但新增测试 `:1921` 无条件解析新语法，在 3.11 会 `SyntaxError`。 |
| **3：正文与假红范围** | 常规产出记录、普通括号 nodeid、带空格线程名均兼容。拒判范围比“确有第二种切法”更宽：地址 `(' (owner=x', 7691)` 的额外分隔符位于线程分隔符之前，仍因全行计数被拒。仅 owner 内含 ` on thread ` 不触发该拒判。没有发生率证据，不能量化为“极小”。 |
| **4：重复豁免** | 集合元素不变的论证成立；由此推导“没有任何信息损失、旧门未削弱”不成立，见 MEDIUM。 |
| **5：最终抬头** | 当前生产表达式与完整尾巴匹配，正常存档未见误拒。**门未覆盖的路径**：`:628-632` 的源码锚仍只查旧前缀，`:670-674` 手抄尾巴；内存负控修改真实尾巴后，旧锚仍真而正则已不匹配。正则也接受退出码 `0/4`，不是对 `FINAL_EXIT_CODE` 值域的严格校验。 |
| **6：BaseException** | **PASS。** 唯一生产调用点 `:813/:821` 原本就吞掉 `SystemExit/KeyboardInterrupt` 并退出 3；新处理器让后续报告与 flush 获得执行机会，退出语义不变。不能外推到 `_final_accounting:1529`：那里仍只捕获 `Exception`，属于既有**门未覆盖的路径**。 |

**7：完成性与红集**

| 存档 | collected | 收工结果 | 最终 rc |
|---|---:|---|---:|
| unit-close | 5844 | 32 failed、5755 passed、44 skipped、13 xfailed | 1 |
| api-close | 269 | 269 passed | 0 |
| regression-close | 1920 | 1913 passed、6 skipped、1 xfailed | 0 |
| skills-close | 555 | 555 passed | 0 |
| contract-close（目录） | 77 | 2 failed、75 passed | 1 |
| 本卡三文件 postfmt | 243 | 243 passed | **未记录** |

直接从原始 `FAILED/ERROR` 行重算：四目录及 contract 的 open→close 红集均相同，**无新增，也未减少**；相对 `base.nodeids`，unit 少一条。三文件增加 24 项，与 unit 收集数增加 24 项吻合。

五组真实 open/close 存档用当前判据重新比较，均返回 0。负控 4 单撤 `fullmatch` 仍绿有如实保留；4c 同撤右锚与 `fullmatch` 才命中目标门。`negctl-2` 的历史源码哈希属于基线，本轮已补做当前 HEAD 的 A/B 归因验证。

最后两处口径更正均成立：第二个 ` on thread ` 应检查 owner 分隔符之前；`W4LedgerConflict(` 实数为 **11→15**。指定生产者、conftest、guard_plugin、hygiene 文件均零 diff。不过指定台账 `:105` 当前是 **Y4-A RV-E**，不是本卡来源行。
