> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-EXPECT-LOC-NARROW round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXPECT-LOC-NARROW.md)"`
> 审查绑定: `796f6490ba951a1826e2c28e97037ab47d71f4b8..0e6d82c00fad046a434461fa1a102617bd2d03c7`（= 最终 HEAD；`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 实测为空）
> 会话头自证（抄 `.stderr`，括注其实际行号；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`(:2) / `model: gpt-6-astra`(:5) / `reasoning effort: ultra`(:9)

---

审查绑定 `796f6490… → 0e6d82c0…`。**BLOCKER / HIGH / MEDIUM：未发现已证实的问题。LOW：2 项。** 三套接线和 37 条指纹核对通过，但“Y1-B HIGH-1 全面闭合”的表述需要收窄。

全程只读；未运行门、pytest 或数据库，仅做源码、存档、AST 核对及内存裁判重放。

1. **LOW — “闭合”文案比对照证据宽（Q0、Q4）。**  
   定位：[验收单:254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-EXPECT-LOC-NARROW-2026-09-17.md:254)、[裁判:901](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:901)。

   三对原始输入确实满足要求：位置落在前提断言，reason 含目标消息；before/after 的 `out` 逐字相同，重放均为 **KILLED → SURVIVED**：

   | 套 | 前提行 → 目标行 |
   |---|---|
   | g32cb | `test_g3_2_review_ledger.py:5214 → 5221` |
   | g32ccr1 | 同文件 `6540 → 6581` |
   | g33 | `test_g3_3_cas.py:640 → 641` |

   **对照思路：**保持原来的前提失败、单条摘要和 `rc=1`，只在 FAILURES 区额外加入 `<门文件>:<目标行>: AssertionError: <expect_msg>`，三套均重新判为 **KILLED**。位置核采用“任一 token 命中”，该输入未被原对照覆盖。

   这是已复现的**裁判输入边界**，但本次未证明真实 pytest 路径能产生它，故不升级为 HIGH，也不归因于本卡修改了共用裁判。建议将“闭合”改为“本卡三份对照输入已被拦下”。

   此外，[驱动:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-expect-loc-narrow/negctl_expect_loc_driver.py:132)统一构造了 stderr 内嵌原因；实际 g32cb 前提无显式消息、g32ccr1 为 `"A 首写"`，g33 的 `{out}{err}` 位于换行之后。因此这些存档证明裁判翻转，不能当作三套真实输出路径的完整复现。

2. **LOW — g33 固定门文件前提值得显式检查（Q10）。**  
   定位：[g33:465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:465)、[g33:481](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/g33_mutation_gates.py:481)。

   唯一性核逐条解析 nodeid 文件，作用域核却固定读取 `TESTS`，查不到指纹便跳过。  
   **对照思路：**未来加入另一门文件中的唯一指纹，共用唯一性核可以通过，作用域核也可能直接跳过，使 `--selfcheck-loc` 错报通过；正式裁决随后通常才报锚失效。当前 **18/18 nodeid 均属于 TESTS**，所以属于后续加固，不阻断本卡。

其余维度：

| 问题 | 核对结果 |
|---|---|
| **Q1 指纹唯一性** | **未发现。**37 个绑定在各自门文件均恰好命中一条。同作用域复制同形语句会使命中数变为 2，[自检:1518](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/mutation_kill_identity.py:1518)会报错，运行期也重核。E2/E6 等三对是多条变异绑定同一语句，不是身份歧义。 |
| **Q2 弱位置判据** | **未发现。**实际调用在 g32cb:697、g32ccr1:592、g33:973，全部字面量 `True`；没有照抄豁免表达式。 |
| **Q3、Q7 豁免及取值来源** | **未发现。**仅 M5 豁免，理由明确是本批禁跑、落点未观测，没有宣称技术上不可绑定。其余 9/11/17 条均与 probe 存档逐项一致。 |
| **Q5 g33 键对齐** | **未发现。**18 个唯一 mid、18 条内联消息；17 个位置绑定与 1 个豁免不交叉，并集恰等于变异键集合。 |
| **Q6 残留措辞** | **未发现错误的肯定表述。**字面命中仍存在于“不得写”、历史解释及“已作废”语境；没有把本三套的位置豁免宣称为 `KILLED-UNBOUND`。 |
| **Q8 `--skip`** | **未发现。**循环过滤、`_selected`、JSON `partial`、部分跑返回均同步；使用集合精确匹配。短值 `M1`、未知值均在写入前拒跑。 |
| **Q9 probe 跳自检** | **未发现错误裁决，但确有诊断边界。**旧位置锚漂移可不告警地经过 probe；它只输出 `OBSERVED`，不会产生 `KILLED`，也不自动回填旧表。必须以独立自检或正式裁决确认锚有效。 |

证据方面，已核最终 AST 比对算法及三套 `True` 记录；首次 docstring 比对失败随后已修正，不能据存档时间较早判失效。限定读取面没有原始编辑前快照，未独立重算那两侧内容。存档裁决覆盖确为 **9 条／1 条／17 条**；目录级记录是失败集合与基线相同，**不是全绿**。
