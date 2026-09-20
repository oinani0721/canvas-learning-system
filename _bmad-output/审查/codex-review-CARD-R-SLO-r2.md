> 批次: BATCH-2026-09-18-第十五批 · 车道 P10 · 卡 CARD-R-SLO round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-SLO-r2.md)"`
> 审查绑定: `d89aa591`（A2（次轮；审后被 A3 整改））
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，行号括注；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: glm-5.3`（stderr :5） / `reasoning effort: max`（stderr :9）

---
## r2 结论

**绑定核**：当前 `HEAD = d89aa5918b912dbe897b15a4799e62c2bb70492f`；`a03f0ce3 → d89aa591` 且排除 `_bmad-output` 后仅改：

- `docs/release-evidence/slo-manifest.yaml`
- `docs/release-evidence/README.md`

`docs/release-evidence` 当前 `git status --porcelain` 为 0 行。`8e36c412 → d89aa591` 整改增量也仅落在上述两文件。

**总体**：`0 BLOCKER / 1 HIGH / 1 MEDIUM / 1 LOW`。代码面零改动；单测目录级 close2 为 32 failed / 5771 passed，相对基线 33 failed 仅少 1 条既有失败，`unit-close2-diff-20260919T210328.txt` 未显示新增回归；承重命名套件 `named-close2-20260919T210328.txt` 为 208 passed。

---

## BLOCKER

无。

---

## HIGH

### H-R2-1 · 负控 3 不具区分度，不能证明 “`not_measured + meets=true` 被 S9 放行” 是由 `meets=true` 造成

- 证据：`negctl-3-20260919T205702.txt:2-8` 的输入同时写了 **`5 not_measured items with meets=TRUE; result=fail`**，随后 validator PASS。
- 但 `validate-export-e2-20260919T205634.txt:80-86` 已证明：**`meets=false` 且 `result=fail` 同样 PASS**。因此该负控同时改变了 `meets` 与 `result`，rc=0 不能归因于 `meets=true` 分支。
- 源码本身确实存在该缺口：`backend/scripts/validate_release_manifest.py:457-458` 在 `meets=true` 时直接 `continue`；` :459-467` 只在 `result != "fail"` 时要求 waiver。也就是说，README 对缺口的描述是真的，但负控 3 不是有效隔离变量的承重证据。
- 最小复跑口径：保持 `result=partial`（或 `pass`），同一导出只 A/B `meets=false/true`；预期 false 出 `[S9]×5`、true 出 0 条 `[S9]`，才能证明该路径。

**影响**：H3 的文档披露与源码事实成立，但“新增负控段 3”这一整改证据不达标。

---

## MEDIUM

### M-R2-1 · cold 口径仍把其余 19 条说成“首见”，未证明进程历史中没有命中过这些查询

- `docs/release-evidence/slo-manifest.yaml:36`：cold 改述为“20 条互异串各一次，其中第 1 条已暖 ⇒ 实为 19 条首见+1 条已暖”。
- `docs/release-evidence/slo-manifest.yaml:93` 与 `:110` 同样使用“19 条首见 / 其余 19/20”的表述。
- r1 指出的第 1 条 warm 污染已修正；但本卡未重启进程，也未提供跑前 query/cache 历史快照，因此无法证明其余 19 条在现网进程历史中从未被请求过。
- 更准确的表述应为：“19 条未由本卡 warm 环节预跑；是否存在历史命中未证”。这不改变 cold 整项 `not_measured` 的结论，但避免把“本卡序列中的首见”说成进程缓存意义上的首见。

---

## LOW

### L-R2-1 · YAML 中 “E3+ 至少一条实测” 与机器行为存在措辞差

- `docs/release-evidence/slo-manifest.yaml:266` 写 “E3+ 另需 revision 非 null 且至少一条实测”。
- 机器实际只检查：`manifest_revision` 非 null 且 `measurements` 数组非空（`backend/scripts/validate_release_manifest.py:430-441`），不检查其中是否有一条 `measured != "not_measured"`。
- README `:271` 已更准确地说 S9 “只要求 `measurements` ≥1 条、不检查覆盖集”。建议 YAML 同步改成 “measurements 非空”，或明确“至少一条真实实测是消费纪律，不是机器门”。

---

## r1 整改逐条核验

| r1 项 | 结论 | 证据 |
|---|---|---|
| H1 cold 口径 / `-m` | **部分解除** | 第 1 条 warm 污染与 timeout 命令已修正：`slo-manifest.yaml:36,53,76,93,99,110,123`；raw cold 第 4 条确为 `000 120.003677`。但见 M-R2-1：其余“19 条首见”仍缺历史查询证据。 |
| H2 只读口径收窄 | **已解除** | `README.md:198` 明确“发起命令面 + 已核对锚点”，且声明不证明 service 层零副作用；UAT `:209` 同步。`live-outputs-before/after` 逐字相同，均为 `105f563c…`。 |
| H3 导出纪律缺口披露 + 负控 3 | **部分解除** | `slo-manifest.yaml:263-266`、`README.md:271` 与 validator 源码一致，未把纪律说成机器门；但负控 3 本身不具区分度，见 H-R2-1。 |
| H4 threshold 三态 `(未定)` | **已解除** | `slo-manifest.yaml:260`、`README.md:199`；`validate-export-e2-…:20-24,41-66` 显示 cold + 写侧四项均导出 `(未定)`。 |
| M1 写侧 method sketch 注记 | **已解除** | 四项分别在 `slo-manifest.yaml:169,193,217,241`，均注明实例/实参由 owner 卡补全。 |
| L1 负控还原状态落档 | **已解除** | `negctl-1-…:3,13-14` 与 `negctl-2-…:3,21-23` 均有前后同 SHA 与还原后 0 行 status。 |

---

## r2 焦点逐项

### ⓪ 整改是否引入新失实

- `(未定)` 三态、`method sketch` 注记与导出存档一致，未发现新失实。
- cold 的 “19 条首见” 仍过度确定，见 M-R2-1。
- “E3+ 至少一条实测” 的机器语义不精确，见 L-R2-1。

### ① seed / data_sha / statistics

- **seed**：当前 `rag-queries.txt` SHA256 复算为 `4dd05b33342dfdcad3ddaa4de89834592fa45631b451b404b2f26676c91e2afa`，20 行、20 个互异值，与 `slo-manifest.yaml:39` 及 seed 存档一致。warm raw 中 `qsha=4e4c15e3…` 等于第 1 行去换行后的 SHA256，cold #4 `def863…` 也匹配。
- **seed 构成**：“live 节点×14 + 原白板×6” 在当前最小读取面内没有独立 live-side 来源清单可复核；**UNVERIFIED**。
- **data_sha**：YAML `df036977…` 与 `data-sha-20260919T171754.txt:2-4` 的值、`md_count=214` 一致。因存档命令使用 `<live>` 且本轮未触碰 live 数据，未独立重算全量 SHA；**live 值 UNVERIFIED，档内一致性 PASS**。
- **statistics**：独立按 raw 样本重算：
  - first paint：p50 9.9ms / p95 39.1ms / n=20 / 20×200
  - warm：p50 1668.7ms / p95 1866.5ms / n=20 / 20×200
  - kg：p50 3.6ms / p95 27.1ms / n=20 / 20×200
  - rebuild：p50/p95 0.05s / n=5
  - cold 成功子集 19 条：p50 3.286965s / p95 5.362801s；YAML 明写“其余 19/20”，故与 raw 超时样本并列时不存在口径偷换。

### ② 导出纪律与负控 3 表达

- YAML `slo-manifest.yaml:263-266` 与 README `:271` 同口径：`not_measured ⇒ meets=false` 与 9 项覆盖是消费纪律，不是机器门。
- validator 证实：
  - `meets=true` 直接跳过后续未达标链：`:457-458`
  - 未达标链只由 `meets=false` 且 `result != fail` 触发：`:459-467`
  - 覆盖集只查非空，不查 9 项全量：`:437-441`
- 文档没有把该缺口说成机器门；但负控 3 的实验设计不具区分度，见 H-R2-1。

### ③ revision 形态 vs 既有测试

- 当前 YAML revision `slo-manifest@2026-09-19-r1` 符合 README/YAML 声明的 `slo-manifest@<YYYY-MM-DD>-r<N>` 形态。
- schema 只要求 string + minLength：`manifest.schema.json:484-490`；validator 只查非 null，不查 pattern：`validate_release_manifest.py:430-436`。
- 测试既有用例同时存在合规形态 `slo-manifest@2026-08-28-r1`（`test_validate_release_manifest.py:119-120,667-669`）与宽松字符串 `slo-v1`（`:654-659,684-688`），说明测试没有锁定 revision 格式。
- 结论：r1 ②#5 可关闭——不是实现矛盾，而是“文档规定形态、机器不 enforcement”；该边界已由 README 锁版无机器门条目覆盖。

---

## 绑定限制

最新一组 r2 裁判存档（如 `negctl-*-20260919T205702`、`validate-export-*-20260919T205634`、`unit-close2-*`）当前仍是待随 commit B 入库的工作区证据；本轮审定的代码/文档对象绑 `d89aa591`。收工 B 必须逐字提交这些存档，且不得再改 `docs/release-evidence` 两文件，否则本结论不自动延伸到最终 HEAD。
