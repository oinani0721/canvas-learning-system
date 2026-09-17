> 批次: BATCH-2026-09-11-第十四批 · 车道 T10 · 卡 CARD-RED-HYGIENE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-HYGIENE.md)"`
> 审查绑定: `2c7402168ed4f44cbad3c7d3413ba4ff2233dcff`（本轮绑最终 HEAD；Codex 在末尾自行实测 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` **输出为空**。⚠️ 本轮之后本卡又按其 MEDIUM-1/LOW-2 改了代码 ⇒ 本轮据 D-15 失绑，另送 r3。）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，逐行括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

本轮结论：**撤销 r1 HIGH-1 作为“本卡新增缺陷”的判断；guard 仍有 MEDIUM 漏检，不能整项宣告修复完成。** 未编辑项目文件。

**BLOCKER: 0**

**HIGH: 0**

目录级确实存在 `>`，我独立复跑结果如下。命令均在 `backend/` 执行：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit \
  --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
```

| 本次运行 | failed / passed | `<` | `>` | blocked |
|---|---:|---:|---:|---:|
| 默认 Node | 67 / 5133 | 30 | 33 | 0 |
| 仅前置已有 Node v24.16.0 | 35 / 5165 | 30 | 1 | 1 |

两跑均另有 `35 skipped / 19 xfailed`，**pytest 退出码均为 1**。第二跑唯一新增项就是 candidate422，正文为同一 `::1:7691 / MainThread` 指纹，`advisory=0 / unaccounted=0`，随后 JSON 降级。这里是被拦截的连接尝试。

对车道三条理由的最终意见：

1. **Node 环境故障：成立。** 默认入口仍缺 `libllhttp.9.3.dylib`，33 条额外失败全部来自 `test_review_app.py`。
2. **协议与哨兵身份：部分成立。** 引文确实存在于主工作树新版协议，本卡树没有该条；而且 `blocked` 从 0 到 1，不只是换了 nodeid，不能直接套用“次数恒定”的免责口径。
3. **PREV 红集对照：成立。** 独立提取、统一剥除 `FAILED/ERROR` 前缀后，两份旧存档的 34 条红与 `$PREV` 完全相同；最终跑只是额外增加 candidate422。

更关键的是，我直接执行：

```bash
git show f294878b:_bmad-output/审查/evidence-b13-integ/unit-integ5-20260911T010612.txt
```

该份**本卡之前已入库**的日志，在第 597–606 行已经出现相同 candidate422、相同连接指纹及 JSON 降级，第 1143 行同为 `blocked=1, advisory=0, unaccounted=0`。相关调用链相对 `$PREV` 也未修改。

因此，这就是 r1 看到的同类 W4 失败，但已有充分证据证明其早于本卡。**不应再用这一条阻断本卡；应另卡处理测试隔离、异步任务生命周期及协议计数。** 这一判断依据历史原始证据，不能仅靠“几个 SHA 都出现过”或“同 SHA 有时通过”。

**MEDIUM: 6（含两项历史 PARTIAL、一项外部协议问题）**

1. **guard 原复现已关闭，但同类直接写入仍漏检。**

   位置：[test_agents_health.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/api/v1/endpoints/test_agents_health.py:472)，`_assert_not_mutated_after_binding`、`_production_expected_templates`。

   按要求用 `PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python -c …`，AST 抽取真实 helper 和完整 guard，仅在内存替换 `inspect.getsource` 输入，实测：

   | 绑定后的操作 | 完整 guard | 运行时名单是否改变 |
   |---|---|---|
   | `expected_templates += ["new"]` | 红 | 是 |
   | `expected_templates[0] = "renamed"` | 红 | 是 |
   | `expected_templates[0] += "-renamed"` | **绿** | 是 |
   | `del expected_templates[0], other[0]` | **绿** | 是 |
   | `expected_templates[0] = other[0] = "renamed"` | **绿** | 是 |

   第一处遗漏因为 `AugAssign.target` 是 `Subscript`，最终检查只接受 `Name`；后两处因为后一个 target 覆盖了前一个 target。

   **处置：修。** 这些属于本实现明确声称覆盖的操作，不涉及一般别名分析。r1 MEDIUM-1 应标“原反例已修，仍有同类漏面”。“门通过时声明与运行时必然一致”仍不成立。

2. **W4 协议把汇总行数误作拦截次数。**

   位置：主工作树 `feature-obsidian-hybrid-dev@8856390d` 的 `.claude/rules/card-batch-protocol.md:79`；本卡 `live_port_guard.py::_GuardState` 汇总实现。

   对 `blocked=0 / 1 / 9` 三个标准单行汇总分别运行 `grep -c 'blocked='`，结果全部为 **1**。该命令无法证明次数恒定。另外，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 是实现中的输出前缀，并非其读取的环境开关。

   失败场景：拦截次数实际增加，协议命令仍显示“恒定”；相同端口指纹也不能区分不同来源的新偷连。

   **处置：登记移交协议卡。** 解析最终汇总的数值，保留失败原因、总红数及历史归属证据，不能只凭 nodeid 或一个字符串豁免新增失败。

3. **自审汇总与逐条表格不一致，流程原因缺原始证据。**

   位置：[SELF-REVIEW-adversarial-20260916.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-red-hygiene/SELF-REVIEW-adversarial-20260916.md:25)，§一、§二。

   用 Python 逐行解析，得到：

   | 项目 | 汇总声称 | 表格实数 |
   |---|---:|---:|
   | 主 session 判成立 | 17 | **18** |
   | 工作流判成立 | 3 | **2** |
   | 不成立翻为成立 | 14 | **15** |
   | 已修 | 11 | **15** |
   | 登记移交 | 6 | **3** |

   RH-1 的自核还以“运行时解析源码”为由否认就地改表漏检，已被真实反例证伪。因此，**流程及主 session 自核确实漏检**；但“验证者因为严重度低而判不成立”的具体原因，只有摘要，没有原始 verifier 正文，不能独立确认。

   **处置：修证据。** 保留历史裁定，追加更正；补完整 finding、`refuted`、理由，重新计算汇总。成立性和严重度应分别记录。

4. **最终 R2 证据尚未入库。**

   位置：`evidence-red-hygiene/FINAL-R2-*`、`FINAL-sentinel-5runs-*`。

   执行 `git status --porcelain=v1`、`git cat-file -e 2c740216:<路径>`：`FINAL-R2-unit-close`、`comm`、`run4` 不在指定 SHA 中；结束核验时 `run5`、五跑汇总也为未跟踪文件，RESPONSE 为工作区修改。

   失败场景：只检出指定提交的复核者拿不到这些最终运行证据。“全部存档已入库”不成立。

   **处置：补纯证据提交。** 可以采用当前工作区观测，但须如实标明来源；不影响本轮代码绑定。

5. **第 0 分钟干净状态仍为历史 PARTIAL。**

   位置：`minute0-20260916T021417.txt:10–11`。

   `nl -ba` 确认仅保留计数 **1**，没有 porcelain 原始路径。RESPONSE/UAT 接受 PARTIAL 的处置正确，不能追认为通过。

   **处置：保留未证实。** 同期完整终端记录、审计记录或快照可能补证；Git 提交历史、现在的状态、重新运行都不能恢复当时未提交路径。

6. **成功 commit 的 typecheck 执行历史仍无法证明。**

   位置：`FINAL-precommit-hooks-20260916T192534.txt`、`lefthook.yml::python-typecheck:205`。

   实读原始输出为：

   ```text
   python-typecheck (skip) no files for inspection
   ```

   它是 commit 前单跑 hook 的记录；实际成功提交输出未捕获。只有 commit1 修改了 `backend/app`；commit2/3 对应 glob skip。没有放进 `LEFTHOOK_EXCLUDE`，不等于实际执行。

   **处置：保留历史 PARTIAL，不追认。** 当前类型状态已独立验证：默认入口因 Node 缺库失败；仅前置已有 Node v24.16.0 后，指定绝对路径的 `pyright app` 为 **rc=0，0 errors, 81 warnings, 0 informations**。

**LOW: 3**

1. **FINAL3 的预期句与紧邻输出矛盾。**

   `FINAL3-guard-shapes-20260916T192147.txt:30–43`：07 明确通过，末尾却写“01/02 通过，03–11 全红”，随后 `probe_rc=0 / rc=0`。独立探针确认 07 应通过。

   **处置：修存档说明。** 形态探针应自动核对预期，不能让退出码 0 掩盖预期文本错误。

2. **部分更正未同步到它声称更正的原件。**

   `nl -ba` 与增量 diff 确认：

   - RESPONSE 声称已删除的“增/删/改名/换序任一发生都会红”，仍在 `test_mock_expected_templates_match_production_truth_source:585–586`。
   - `attribution-*.txt:7–8、31–32` 仍保留“不在基线的测试文件 ⇒ 本卡对消失红项贡献为零”的不足推理，实际只补了四文件/六文件说明。
   - `minute0-*.txt:31–36` 仍宣告干净成立，未指向后来的 PARTIAL。
   - 新五跑汇总把同 SHA 非确定性直接推成“与本卡改动无关”，推论过强；这些样本也只展示了哨兵出现/消失，没有展示两个 nodeid 之间翻转。

   **处置：追加明确撤回及替代证据链接。** 避免单读原件得出已经撤销的结论。

3. **FINAL-territory 仍是旧 SHA，状态判据与输出不符。**

   `FINAL-territory-20260916T191958.txt:1–3` 明绑 `b38e1d04`；第 40 行要求状态项数 `≤1`，实际第 45 行为 **4**，随后 `rc=0`。

   我重算最终 SHA：代码面 **6 文件**，OpenAPI 与 `$PREV` 及工作区逐字节相同；exclude 锚为 **43 / 0**，本卡变更文件名含 stderr 为 **0**。所以是存档问题，没有发现地盘越界。

   **处置：补最终版本，撤销不适用的状态条件。** 旧版的 `36 / 0` 不应冒充最终三提交计数。

六个反面问题的逐条回答：

1. **退役是否漏消费方？** 未发现。除全仓及排除面的引用核查，还检查了生产非字面量 `getattr` 和配置转储路径。真实 Settings 的 kwargs、环境变量、dotenv source 三种内存输入均验证：`extra="ignore"`，旧键不成为属性、不进入 `model_dump()`。部署 `.env` 残留旧键会被忽略；仓外消费者不在已证明范围内。

2. **拒绝时零调用是否恒真？** 单独使用可能假绿；当前对照有效。两例使用同一配置、payload、路径和替身，仅改变鉴权 override；对照还要求 200 和非零 await，能够排除共享路径上的错误 patch、端点和 body 校验阻断。fixture 最终 `clear()`，不会因对照只 `pop` 鉴权而遗留 `get_settings`。三段负控失败身份及首尾哈希对账成立。

3. **guard 是否仍漏？** 是，见 MEDIUM-1。长度断言和逐元素比较都非恒真；改空表时完整 guard 会红。改从常量或文件读取会明确 `AssertionError`，不是静默空表。嵌套独立同名变量与带注解绑定的修复有效。

4. **目录级是否没有 `>`？** 否。本次可用 Node 独立跑仍为 **`<30 / >1 / blocked=1`**；该项已有本卡之前的同形原始证据，不判本卡新增 HIGH。

5. **pyright 是否被跳过？** 最后两次提交面不触发 glob；commit1 成功提交的实际执行历史无法补证。当前 `pyright app` 已实跑通过，不能据此倒推历史 hook 执行。

6. **(e)(g) 是否该在本卡修？** 登记移交正确。flaky 测试及隔离链、contract 测试/schema 都在明确禁改面。contract 当前失败是读取已删除 schema 时的 `FileNotFoundError`，尚未运行到 pattern 比较；不能写成已证明 pattern 不一致。

其他验收核对：四个目标文件当前合跑为 **41 passed / 4 xfailed，端口账本全零**。健康测试 RED/GREEN/改名负控的身份、数量、恢复哈希一致；改名负控证明同长度改名可被逐元素比较捕获。退役算术严格为 `3F/7P/5X → 0F/9P/4X`：删除一个失败测试和一个 xfailed，另外两个失败转绿，没有把删除算成转绿。

格式豁免成立：stdin 格式化逐版计算实际改行，确为 `$PREV` **284–286**、首提交 **247–249**、最终 **250–252**，三版原文相同，与本卡实际新增行交集为空。当前五个 Python 文件 `ruff check` 全通过，format 仅剩该处旧漂移；spec-sync 豁免由生产消费分析和完整 OpenAPI 对照支持。两份 SUPERSEDED 的主要作废理由诚实，替代证据修复了原来的矛盾及无效锚；其余残留问题已列于上文。

绑定声明：本次审查 SHA 为 **`2c7402168ed4f44cbad3c7d3413ba4ff2233dcff`**；`git --no-pager diff --stat --no-color 2c7402168ed4f44cbad3c7d3413ba4ff2233dcff HEAD -- . ':(exclude)_bmad-output'` **执行成功且输出为空**，工作区代码面对该 SHA 的 diff 也为空。


