> 批次: BATCH-2026-09-18-第十五批 · 车道 P10 · 卡 CARD-R-SLO round-4
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-SLO-r4.md)"`
> 审查绑定: `e4ef1ebf`（A4（终轮；绑定核见 commit B 后 diff））
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，行号括注；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: glm-5.3`（stderr :5） / `reasoning effort: max`（stderr :9）

---
## r4 复核结论

**最终分级：0 BLOCKER / 0 HIGH / 0 MEDIUM / 2 LOW**

审查对象按请求绑定 `a03f0ce3 → e4ef1ebf`；两项指定 diff 均已真跑。独立 `--numstat` 复核结果为：

- `docs/release-evidence/README.md`：12 insertions / 0 deletions
- `docs/release-evidence/slo-manifest.yaml`：269 insertions / 0 deletions

因此本卡在 `PREV..HEAD` 口径下仍是纯新增文档面改动；A4 对 README 的那处 `-/+` 是修订本卡自己在 A3 新增的 bullet，没有改坏卡前既有行。

---

## ② r3 三项整改核验

### H-R3-1 · 负控 3 输入侧证据 — **已解除**

单变量归因链现在完整到可复核：

- **A/B 输入落档与 sha256**：  
  `negctl-3-20260919T213522.txt:5-7` 登记两份输入及哈希。我在本轮只读重算：
  - A = `988301d1773173d3419cfb78d13b9655807a7c98f5984b5b7557ae2a0f12e11a`
  - B = `aab8d9c4d784300cc2390c9666fa63b27af7ba5b65ec36223d006f878cf53c5c`  
  两值逐字匹配存档。

- **A/B 除 5 处 `meets` 外逐字同构**：  
  存档内归一化 diff 为恰好 5 处：`negctl-3-20260919T213522.txt:8-14`，索引 `[2]/[5]/[6]/[7]/[8]`。  
  我另用 raw `diff -u` 独立复核，实际差异也只有这 5 个 `meets: false → true`，无其他 JSON 行差异。

- **`result=partial` 不变量有 pre-assert**：  
  生成器在写档前断言 `result == "partial"`：`negctl-3-20260919T213522.txt:67-70`。A 输入中顶层 `result` 位于 `negctl-3-inputs-A-20260919T213522.json:250`；raw diff 证明 B 同值。

- **唯一变量在生成器中可见**：  
  `negctl-3-20260919T213522.txt:61-64` 明确 `not_measured` 项的 `meets` 由 phase 决定，是唯一变量；其余导出逻辑相同。

- **两腿 validator 结果与计数匹配**：  
  A 腿 `[S9]×5`、`A_rc=1`、`A_S9_count=5`：`negctl-3-20260919T213522.txt:15-26`。  
  B 腿 PASS、0 failures、`B_rc=0`、`B_S9_count=0`：`negctl-3-20260919T213522.txt:27-33`。  
  这与源码路径一致：`backend/scripts/validate_release_manifest.py:457-458` 在 `meets=true` 时直接 `continue`，不会回查 `measured="not_measured"`。

- **生成器全文附录在场**：  
  `negctl-3-20260919T213522.txt:35-70`。

结论：A/B 输入、哈希、生成器、逐字段差异、validator 输出五者能互相扣上；本轮不再把“改 `meets`”与“改 `result`”混在一起。H-R3-1 到位。

---

### M-R3-1 · UAT 权威指针 — **已解除**

- UAT 已把首版负控 3 明确降级为历史对照、不作承重证据：`UAT-CARD-R-SLO-2026-09-19.md:147`。
- r3 整改记录明确 A4 输入落档组与 A/B 文件：`UAT-CARD-R-SLO-2026-09-19.md:210-216`。
- §5/§6/§7 不再以 A2 旧组为权威：`UAT-CARD-R-SLO-2026-09-19.md:106`、`:133`、`:147`、`:154`。
- A4 权威组文件本身存在且内容可读；当前 `slo-manifest.yaml` sha256 也与负控 1/2 的跑前/跑后值一致：  
  `ca5a2d5eb9dbe8306fa92f9a2b8c232ecb734d57f6a560fcec9519fc4cfe07a0`，见 `negctl-1-20260919T213522.txt:2-3,12-13`、`negctl-2-20260919T213522.txt:2-3,20-21`。

结论：旧 A2 承重指针问题已消除。仅剩一个 LOW 级“指针可读性”备注，见下方 L2。

---

### L-R3-1 · README 既有句不改，只新增澄清 — **已解除**

- 既有句仍在原处：`docs/release-evidence/README.md:151`，内容未被本卡删除或改写。
- 新增已知边界 bullet 的澄清尾段明确：既有句表达消费纪律，机器只查非空；歧义以新增 bullet 与 `consumption_note` 为准：`docs/release-evidence/README.md:271`。
- YAML `consumption_note` 同步说明“真实实测”是消费纪律、非机器门：`docs/release-evidence/slo-manifest.yaml:266`。
- UAT 已把该残留登记进“本卡未证明什么”与台账待登记项：`UAT-CARD-R-SLO-2026-09-19.md:232`、`:246`。
- 全卡 README diff 仍为 12 insertions / 0 deletions，满足“不改卡前既有行”的净效果约束。

结论：L-R3-1 到位，无回归。

---

## ③ r4 焦点逐项作答

### ⓪ 负控 3 v3 是否足以完成单变量归因 — **足够**

可承重理由：

1. A/B 文件实体入库，哈希可复算且复算一致。
2. raw diff 独立证明唯一语义差异就是 5 处 `meets false→true`。
3. `result=partial` 在生成器中 pre-assert，且 A/B 实体同值。
4. 生成器全文落档，逻辑可见。
5. A/B validator 输出差值恰好由 5 条 not_measured 项的 S9 未达标链消失构成。

不需要再补 HIGH 级证据。

---

### ① A4 增量是否引入新矛盾或新强主张 — **未发现**

A4 的非 `_bmad-output` 增量只有 README 已知边界 bullet 的澄清尾段：`docs/release-evidence/README.md:271`。该句做的是收窄解释：

- 明确“至少一条实测”不是机器检查真实实测；
- 明确机器只查 measurements 非空；
- 指向 `slo-manifest.yaml` 的 `consumption_note` 作为解释源。

这不是新增强主张，也没有与 S9 源码事实冲突。源码确实只要求非空并处理未达标项：`backend/scripts/validate_release_manifest.py:430-477`；schema 也只约束五键加可选 `unit/waiver`：`docs/release-evidence/manifest.schema.json:475-530`。

---

### ② 是否仍有未披露强主张或与前两轮收窄口径冲突 — **未发现 HIGH/MEDIUM 级问题**

关键口径已经保持一致：

- 现网“只读”已收窄为发起命令面 + outputs 锚点，不声明 service 层零副作用：`docs/release-evidence/README.md:198`、`UAT-CARD-R-SLO-2026-09-19.md:225-226`。
- `code_sha: null` 及 8011 代码树对应关系未证明：`docs/release-evidence/slo-manifest.yaml:33-35`。
- cold 不是真冷启动，且本次因一个超时整项 `not_measured`：`docs/release-evidence/slo-manifest.yaml:90-111`。
- 写侧四项未实测、只给 owner 与 method sketch：`docs/release-evidence/slo-manifest.yaml:160-255`。
- S9 不查 revision 存在、draft/locked、覆盖集、not_measured+meets=true：`docs/release-evidence/README.md:270-271`。
- 真实 J 卡消费链未端到端发生：`UAT-CARD-R-SLO-2026-09-19.md:229`。

仅有一个 LOW 级措辞风险，见 L1。

---

### ③ 若仍有 HIGH 的最小后续补证 — **无 HIGH，故无必补项**

本轮没有 HIGH。无需为通过本卡追加证据。LOW 项可留到后续文档/台账面处理，不影响本卡关闭。

---

## 分级发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

无。

### LOW

#### L1 · README 对写侧“可复跑命令”的概括略强于 YAML 的 `method sketch` 事实

- 证据：
  - README 概括写侧指标为“指定 owner 卡与可复跑命令”：`docs/release-evidence/README.md:198`。
  - 但四个写侧项在 YAML 中均自认 method sketch，实例、容器、请求体或环境需 owner 补全：
    - first index：`docs/release-evidence/slo-manifest.yaml:169`
    - Graphiti ACK：`docs/release-evidence/slo-manifest.yaml:193`
    - replay：`docs/release-evidence/slo-manifest.yaml:217`
    - recovery：`docs/release-evidence/slo-manifest.yaml:241`
  - UAT 也已披露这是 sketch 而非直接可复跑：`UAT-CARD-R-SLO-2026-09-19.md:199`。
- 影响：不构成事实冲突，因为 YAML 和 UAT 已收窄；但单独读 README §SLO manifest 的读者可能高估当前命令可执行性。
- 最小后续动作：后续文档/owner 卡清单中把这类命令称为“method sketch，owner 补实例与实参后复跑”，不要改本卡卡前既有行。

#### L2 · UAT 对 A4 重跑组的指针可再精确一点

- 证据：
  - UAT §6 只写“A4 轮重跑组（负控 3 含输入侧证据）”，未在同行列出 exact timestamps/files：`UAT-CARD-R-SLO-2026-09-19.md:147`。
  - exact A/B 文件名主要落在 §9d 的通配描述：`UAT-CARD-R-SLO-2026-09-19.md:214`。
  - §5/§7 对非负控门仍以 A3 组为权威、A4 为补充：`UAT-CARD-R-SLO-2026-09-19.md:106`、`:133`、`:154`。
- 影响：不会误指 A2 旧组，也没有把历史首版当权威；只是读者需要结合 §9d 或证据目录才能精确定位 A4 文件。
- 最小后续动作：后续若再有文档轮，新增一个小型 A4 evidence index，逐项列 `213522/213532/213533/213539/214207` 文件名；不需要本轮阻断。

---

## 回归检查

- 指定 diff 显示本卡非 `_bmad-output` 面只有 README 与 YAML，且均为纯新增。
- `landgate-20260919T213532.txt:2-5` 同步显示 2 files changed / 281 insertions；`:34-35` 显示本卡 `.py` 集合大小为 0。
- 全量 unit 收工仍为红：32 failed / 5771 passed / rc=1，见 `unit-close4-full-20260919T213539.txt:892-926`。
- 但修正版差分只有一条旧基线失败消失：`unit-close4-diff-20260919T214207.txt:2-4`；`named-close4-20260919T214207.txt:1-2` 显示相关 named 套件 208 passed / rc=0。
- 结合本卡零 `.py` 改动，未发现由本卡引入的测试回归。

---

## UNVERIFIED / 复核限制

- 我没有重跑 validator、pytest、现网请求、YAML 变异负控或测试命令；本轮只真跑了请求指定的两个 git diff，并做只读哈希/raw diff 复核。因此这些命令的“当前再执行结果”是 **UNVERIFIED**，但存档内部链路与源码静态语义一致。
- 机型/OS、live data SHA、8011 实测原始输出等事实未超出本轮最小读取面复算，未重新验证；相关不确定性已在 YAML/UAT 中披露。
