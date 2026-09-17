> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t1-lance · 卡 CARD-G2-9-F1-canary round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `OpenAI Codex v0.153.3`（`codex --version` 实测 `codex-cli 0.153.3`）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F1-canary.md)"`
> 审查绑定: `49db0305`（送审时 HEAD；零代码卡，本卡全部改动在 `_bmad-output/` 下）
> 会话头自证（按实际行号抄 `.stderr` 中含 codex 版本 / model / reasoning effort 的三行——0.153.x 把 `model:` 排在会话头靠后，字面抄前三行会漏字段；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

## 结论：PARTIAL，不能据此认定移交项全部闭环

两态报告、验伪报告来源、前后 SHA 和提交地盘核均成立。**关键遗漏仍是：没有本次运行证据证明 probe 判 FAIL 时，进程返回 `EXIT_ISOLATION_FAILED`。** 两处更正方向正确，但仍残留“零 socket”“零网络”等证据外推。

全程只读，未复跑 canary、测试或执行数据库连接命令。

下文简称：

- **UAT**：[本卡验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-20260915.md)
- **EV/**：[本卡 evidence 目录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/_bmad-output/审查/evidence-g29f1-canary)
- **脚本**：[g29_dual_vault_canary.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/scripts/g29_dual_vault_canary.py)

## 一、问题，按重要性排序

### HIGH — probe FAIL → 失败退出码仍未实跑验证

当前 rc 守卫实际位于 `_run_canary_cli`：**脚本 1451–1457 行**。代码结构支持“probe 非 PASS 时返回 `EXIT_ISOLATION_FAILED`”，但本卡：

- ON 只有 PASS；
- OFF 跳过 probe；
- `--verify-judges` 在 **1389–1419 行提前返回**，不经过 probe 写入和该 rc 守卫。

因此，**OFF 缺键不崩溃已经实证；FAIL → 退出码仍只有静态依据。**

UAT **438 行**承认未证明 probe 判据可翻红，却在 **451 行**写“U5-A 移交项落地”，收尾措辞过强。历史红也补不了这个缺口：`EV/red-ref-keys-20260915T121014.txt:2–3` 明确说明旧报告没有 `verdict` 键。

**应明确保留的未完成项：本次没有执行验证 `side_effect_probe.verdict == "FAIL"` 时的进程退出码。**

### MEDIUM — 更正后的“负控零 socket”仍证据不足

两条负控确实发生在 `_run_canary_cli` 调用前，见**脚本 1369–1377 行**。但这只能证明**未进入 canary runtime 主流程**。

UAT **196、440、460 行**及 `EV/attempts-semantics-correction-20260915T184001.txt:20–23`，仍把这一点扩大成整个进程“零 socket”。

`preflight` 是程序的阶段标签，不是网络活动记录。尤其负控②此前执行了**脚本 353 行**的外部 guard 调用；允许读取面没有完整覆盖启动、依赖及拒绝处理的全部行为。因此：

> 可确认按预期层在 runtime 入口前被拒；“没有打开任何 socket、没有连接任何库”在本读取面下证据不足。

这不意味着已经发现连接发生。

另外，UAT **445 行**仍将 `ATTEMPTS=0` 用作共享 **7692** 无并发干扰的间接支持。账本监控的是 **7687/7691**，对该主张没有证明力，应删除这项依据。

### MEDIUM — “加载很快 ⇒ 零网络”是尚未更正的第三处外推

UAT **349、456 行**仍把约 `5×10⁴ it/s` 写成“未走网络／零网络”。同样的论证出现在：

`EV/embed-dep-correction-20260915T183156.txt:32–36`

权重加载速度不能排除加载前后的元数据请求、缓存检查等网络访问。证据支持“四次权重加载完成”，**不支持零网络**。

关于“不设嵌入端前置门”：

- **作为本次成功环境下的执行选择，可以保留。**
- 不能推出嵌入不可达时仍能完成。
- 更严格地说，允许面内的 evidence 只展示了预热调用和构造片段，**没有展示完整 `except` 实现**；“吞掉异常”的具体代码，本轮也无法独立完整认证。

ADDENDUM 撤回“本次证明 fallback 生效”的方向正确；UAT **74、354 行**的无条件“结论仍正确”，应统一收窄为本次环境结论。

### MEDIUM — `purge_left_nothing` 被扩大成跑后无残留

UAT **114、117 行**把该字段解释为“跑完清理干净”“没有在共享 7692 留下脏数据”。

但 `EV/canary-verify-judges-20260915T102632Z.json:139–145` 将对应变异明确描述为**起点前提**。两态报告展示了特定对象、特定阶段的计数，没有提供最终共享容器对账。

**不能据此断言实际留下了脏数据；同样不能据此证明跑后没有残留。** 此项应加入“本卡未证明什么”。

### LOW — 所称同次 `test -e` 实测没有落在证据中

UAT **199 行**称被拒路径经 `test -e` 确认不存在；`EV/negctl-summary-20260915T182726.txt:22–23` 指称对应 tee 有该输出。

实际 `EV/negctl-forbidden-path-20260915T182702.txt` **全文仅 9 行，末行为 `rc=2`，没有该检查输出**；目录内也未找到对应实测。

脚本 **392–398、407 行**支持“本函数在 mkdir 前拒绝”，但不能冒充已经保存的路径存在性检查。

### LOW — 验收完成状态与当前文件状态不一致

UAT **431 行**把“Codex＋验收单＋commit”标为完成，引用的两个章节实际不存在；**464 行**仍保留复核存档、最终 SHA 和计数的 `PENDING`。

此外，当前 UAT 相对 HEAD 存在 **35 行新增、3 行删除**，所以 **249 行**的“工作树相对 HEAD 全树 diff 空”已不是当前事实。它不影响 `_bmad-output` 外提交差异为空，但应标清历史快照与当前状态。

## 二、五条作者主张逐项判定

| 主张 | 独立核对结果 |
|---|---|
| **ON/OFF rc、字段和配对** | **PASS。** ON tee **93、96 行**指向 `…101823Z.json`、`rc=0`；JSON **214–225 行**三项 probe 条件全部满足。OFF tee **82、85 行**指向 `…102343Z.json`、`rc=0`；对应 JSON 全文无 probe 键，tee 无 KeyError/Traceback。两份 tmp 路径也分别吻合，配对不依赖文件排序。 |
| **两条负控** | **阶段、拒绝层、rc 均 PASS；零连接主张证据不足。** 缺 URI tee **3–8 行**：`preflight`、`_preflight_neo4j_uri`、rc=2；禁后缀 tee **4–9 行**：`preflight`、`_preflight_lancedb_path`、rc=2。汇总 **3、6–8、12–14 行**确实记录三重绑定。 |
| **verify 本卡新跑来源** | **PASS。** tee **226 行**指向本卡目录，**228 行**为 rc=0；报告 **158 行**时间戳为 `20260915T102632Z`。独立重算：12 个变异均 `applied=true`、`KILLED`，目标判据覆盖基线 14 项，与 `all_killed`、coverage 一致。 |
| **SHA 前后相同** | **PASS。** `canary-sha-start.txt:1` 与 `canary-sha-end.txt:1` 各 107 bytes，文件字节完全相同；SHA 为 `5411cf14da00cabfec8e1f8ddd1f56c8ffeeda745b1eb147536d4927e200ee7a`。这是前后快照一致的证明。 |
| **地盘 diff 和非空验伪锚** | **PASS。** 当前 HEAD 为 `49db0305c02d372f3afa1f56788988acdd9f0cd6`。独立执行指定排除命令：rc=0、无 diff 行；同区间不排除：`54 files changed, 5108 insertions(+)`。与 `EV/turf-outside-bmad-20260915T193339.txt:2–12` 一致，排除了命令失败造成的假空。 |

补充：两份原始 unit 快照均为 **35 FAILED＋29 ERROR**，64 个 nodeid 集合完全相同，测试自身均 **rc=1**。这是“没有新增红项”，不是整套测试通过。

## 三、更正残留及范围问题

- **旧错误确实还在原文件中：**
  - `EV/negctl-summary-20260915T182726.txt:9、15` 仍写“0＝零 socket”。
  - `EV/embed-dep-correction-20260915T183156.txt:42–43` 仍写“不可达不会失败”“本次证明 fallback 生效”。
  
  后续追加件有明确撤回指向，所以属于**可辨认的历史错误记录**；不能说已经全目录清除。当前摘要中仍有效的过强结论，是上文指出的零 socket、零网络及错误的计数器用途。

- **F2 最长前缀覆盖：未发现冒领。** UAT **144、437 行**及 `EV/t1a-change-surface-20260915T184238.txt:19` 明确排除该面。本卡只能提供非前缀重叠输入的回归证据。

- **OFF 无键：没有被当成 probe PASS。** UAT **130 行**和 `EV/two-state-assert-20260915T182549.txt:10` 均明确写“探针没跑”。

- **历史红：没有冒充本卡重建。** `EV/red-ref-20260915T120948.txt:1–5` 明示旧日期、旧目录和历史属性。但它不能证明当前 verdict／退出码链可翻红。

- **`blocked=0`：主要隔离结论已正确排除它。** UAT **150 行**明确说明不是 vault 隔离证据；**445 行**的并发论证仍需清理。

- **verify 不覆盖 probe：声明成立。** early return 的代码结构支持这一限定；但不能因此把未覆盖的退出码验证视为已经收尾。

**“本卡未证明什么”至少应补明：probe FAIL 的实际退出码、完整进程零 socket、嵌入加载零网络，以及运行结束后的残留对账。** 现有成功证据可以保留，整卡“移交项已全部落地”的结论应暂时收窄。
