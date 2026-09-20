> 批次: BATCH-2026-09-18-第十五批 · 车道 P10 · 卡 CARD-R-SLO round-3
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-SLO-r3.md)"`
> 审查绑定: `9b2089fb`（A3（三轮；审后被 A4 整改））
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，行号括注；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: glm-5.3`（stderr :5） / `reasoning effort: max`（stderr :9）

---
# r3 复核结论

**结论：0 BLOCKER / 1 HIGH / 1 MEDIUM / 1 LOW。**

当前 HEAD 确认为 `9b2089fb6a2ee790107b88586dd47a670f3d7e39`，父提交为 `d89aa5918b912dbe897b15a4799e62c2bb70492f`。本轮只读复核，未改任何文件。

- `a03f0ce3..9b2089fb`（exclude `_bmad-output`）仅新增：
  - `docs/release-evidence/README.md`：12 行
  - `docs/release-evidence/slo-manifest.yaml`：269 行
- `d89aa591..9b2089fb`（exclude `_bmad-output`）仅改 YAML 3 行；包含 `_bmad-output` 时另改 UAT。
- 未见本卡 `.py` / schema JSON / openapi 改动；与“零 `.py` 改动”一致。

---

## BLOCKER

无。

---

## HIGH

### H-R3-1 · 负控 3 的“单变量归因”仍只有输出证据，缺少输入构造证据；H-R2-1 只能算部分解除

**位置**

- `_bmad-output/审查/evidence-rslo/negctl-3-20260919T211541.txt:1-22`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:201-207`
- `backend/scripts/validate_release_manifest.py:457-458`

**已能复算的部分**

- A 腿 validator 输出正好 5 条 `[S9]`：`negctl-3-20260919T211541.txt:5-9`
- A 腿 `A_rc=1` / `A_S9_count=5`：`:13-14`
- B 腿 validator 输出 0 条 `[S9]`，`B_rc=0` / `B_S9_count=0`：`:16-21`
- 代码机制吻合：`meets=true` 时在 `validate_release_manifest.py:457-458` 直接 `continue`，不会回头检查 `measured="not_measured"`。

**未解除 / UNVERIFIED 的部分**

存档只有一行自述：

> `B 腿: 同上，唯一改动 = 5 个 not_measured 项 meets: false -> true；result 仍 partial`  
> 见 `negctl-3-20260919T211541.txt:15`

但存档没有保留：

1. B 腿运行前 `result==partial` 的断言输出；
2. A/B 两份具体输入 manifest；
3. 两份输入的 hash 或归一化 JSON；
4. 机器可复核的 A/B diff，证明除 5 个 `meets` 外其余字段逐字相同。

因此：

- **A/B 输出计数：已核实**
- **B 腿运行前不变量断言：UNVERIFIED**
- **“同文件、同 result、同其余字段”：UNVERIFIED**
- **H-R2-1 总体：部分解除**

这不是 validator 行为问题，而是证据链问题：r2 HIGH 的核心就是把 rc 差异归因到 `meets` 单变量，目前该归因仍依赖执行者自述。

**最小后续补证**

无需改 `.py`。在 commit B 前补充以下任一组证据即可：

- 归档 A/B 两份 manifest 的归一化 JSON + 逐字段 diff + B 腿 pre-assert 输出；或
- 归档生成负控的脚本/命令，并输出两腿输入 hash、断言结果、唯一 diff summary。

---

## MEDIUM

### M-R3-1 · UAT 仍指向 A2 旧证据组，未把 A3 最新重跑组钉成唯一权威版本

**位置**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:146`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:153`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:116-130`
- 最新证据：
  - `negctl-3-20260919T211541.txt:1` 自称绑定 `9b2089fb`
  - `landgate-20260919T211549.txt:1` 自称 `HEAD=9b2089fb`
  - `desens-final-20260919T211549.txt:1`

**问题**

UAT §6 仍写：

> “存档：`negctl-1-*.txt` / `negctl-2-*.txt` / `negctl-3-*.txt`（**绑定 A2 的那组为准**…）”

见 `UAT:146`。

但这与实际权威证据相反：

- A2 组的 `negctl-3-20260919T205702.txt` 是首版非配对设计，且自称绑定 `d89aa591`；
- A3 组的 `negctl-3-20260919T211541.txt` 才是配对版，并自称绑定 `9b2089fb`。

这会误导后续审计者选择已被 r2 否定的旧档。另有同类旧指针：

- UAT §7 仍指向 `desens-final-20260919T202600.txt`，而非 A3 重跑 `desens-final-20260919T211549.txt`；
- UAT §5 仍指向早期 `validate-export-*` / `unit-close-*` / `named-close-*`，而非本轮 `211540` / `211555` / `212159` 组；
- UAT 头部说 r3 见 §6，但 §6 未列出本轮 r3 具体存档清单。

当前最新 A3 重跑文件仍是 untracked，等待 commit B 入库；这本身符合 A3→B 的流程，但 UAT 不能在 B 中继续把 A2 组写成“为准”。

**处置**

commit B 前把 UAT 的权威存档指针统一改为 `20260919T211540/211541/211549/211555/212159` 这组，并明确首版 `205702` 仅作历史对照，不作承重证据。

---

## LOW

### L-R3-1 · README 旧填写提醒仍写“至少一条实测”，与“机器只查 measurements 非空”存在残余歧义

**位置**

- `docs/release-evidence/README.md:151`
- `docs/release-evidence/README.md:214`
- `docs/release-evidence/README.md:270-271`
- `docs/release-evidence/slo-manifest.yaml:266`
- `backend/scripts/validate_release_manifest.py:431-441`

README `:151` 写：

> “E3 及以上必须有 revision 且至少一条实测”

这句位于“填写硬性提醒”上下文中，可以被解释为消费纪律；但单看容易误认为机器会检查 `measured != "not_measured"`。

实际机器行为是：

- E3+ 只检查 `manifest_revision` 非 null；
- `measurements` 非空；
- 不检查至少一条真实实测。

见 `validate_release_manifest.py:431-441`。YAML `:266` 和 README `:270-271` 已正确区分“measurements 非空”与“至少一条真实实测是消费纪律”，因此这只是残余文档歧义，不是行为错误。

---

# ② r2 三项整改核验

## H-R2-1 · 负控 3 配对演示

**结论：部分解除。**

- 输出层面成立：
  - A：`[S9]×5` / rc=1
  - B：0 条 `[S9]` / rc=0
- 归因层面未完全闭环：
  - B 腿 pre-assert 未落档；
  - A/B 输入等同性与“唯一变量”未留机器可复核证据。

详见 H-R3-1。

## M-R2-1 · cold cache 口径收窄

**结论：已解除。**

当前 wording 为：

- `docs/release-evidence/slo-manifest.yaml:36`
  - 明确 “19 条未由本卡 warm 环节预跑 + 1 条已暖”
  - 明确 “其余 19 条在进程历史中是否曾被命中未证”
  - 明确 “只读约束下拿不到查询历史”
- `docs/release-evidence/slo-manifest.yaml:93`
  - cold description 同步写 “其余 19 条的历史命中未证”

与实测证据一致：

- seed 文件 20 行且 20 行互异；
- 第 1 条 hash 与 warm 查询相同；
- warm 为同串 20 次；
- cold 为 20 条各一次，其中第 4 条 `000 / 120.003677`，其余 19 条 200。
  - 见 `measure-rag_warm-20260919T171144.txt:1-22`
  - 见 `measure-rag_cold-20260919T171226.txt:1-22`

未发现继续声称 “19 条首见” 的强主张。

## L-R2-1 · `consumption_note` 机器语义改述

**结论：已解除，余一个 README 旧句式歧义。**

`docs/release-evidence/slo-manifest.yaml:266` 现在写：

- E3+ 机器要求 = revision 非 null + measurements 非空；
- “至少一条真实实测（measured≠not_measured）” 是消费纪律，不是机器门；
- `not_measured + meets=true` 不被 S9 拦，已有配对实证指向。

这与 validator 实际行为一致：

- `validate_release_manifest.py:431-441` 只做非 null / 非空检查；
- `:457-458` 在 `meets=true` 时直接放行；
- `manifest.schema.json:492-529` 只要求每条 measurement 具备五键，`measured` 是普通非空字符串，不限制不能写 `not_measured`。

README `:270-271` 也如实登记该边界。残余旧句式见 L-R3-1。

---

# ③ r3 焦点逐项回答

## ⓪ 三项整改是否引入新的不一致

**数值与实测：未发现回归。**

独立重算结果与 YAML 一致：

- 首屏：p50 ≈ 9.911ms，p95 ≈ 39.092ms
- RAG warm：p50 ≈ 1668.68ms，p95 ≈ 1866.504ms
- KG read：p50 ≈ 3.622ms，p95 ≈ 27.113ms
- review rebuild：p50 = 0.05s，p95 = 0.05s
- cold 仅描述成功的 19 条：p50 ≈ 3.286965s，p95 ≈ 5.362801s；第 4 条 120s 超时导致整项 `not_measured`

**validator / schema / README / YAML：主要语义一致。**

不一致点：

- UAT A2/A3 权威证据组指针错误，见 M-R3-1；
- README `:151` 旧句式有机器门/消费纪律歧义，见 L-R3-1。

**代码面：无回归。**

A3 未改 validator、schema 或任何 `.py`。

## ① 配对版负控 3 的 A/B 同构性

**输出结果可复算：是。**

- A validator `[S9]` 行数 = 5
- B validator `[S9]` 行数 = 0
- A rc = 1
- B rc = 0

**输入同构性：UNVERIFIED。**

存档没有 A/B 输入 manifest、hash、归一化 diff 或 pre-assert 输出；只有 `negctl-3-20260919T211541.txt:15` 的自述。

**B 腿运行前 `result==partial` 断言：UNVERIFIED。**

存档只显示 B 输出中 result 为 partial，未显示运行前断言。

## ② 全套承重裁判重跑结果

**结论：存档层面成立；因本 r3 明确只读，我没有重新执行 pytest 或 validator。**

### unit-close3

- `unit-close3-full-20260919T211555.txt:925-926`
  - `32 failed, 5771 passed, 44 skipped, 13 xfailed`
  - rc=1
- `unit-close3-diff-20260919T212159.txt:2-5`
  - base=33，close3=32
  - diff 只有 `<` 一条：
    - `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`
- 该 missing node 在 `base.nodeids:3`，不在 close3；
- close3 node IDs 与 full 输出中的 32 条 failed summary 集合完全一致；
- close2 与 close3 node IDs 完全一致，支持“既有 flaky 消失，无新增失败”。

**判定：成立。**

### named-close3

- `named-close3-20260919T212159.txt:1-3`
  - `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`
  - `208 passed, 10 warnings`
  - rc=0

**判定：存档层面成立。**

### yaml / revision

- `yaml-check-20260919T211540.txt:2-3`
  - metrics=9
  - measured=4
  - not_measured=5
  - status=draft
- `rev-check-post-20260919T211540.txt:2-3`
  - revision 对照 OK
  - 9 个 metric

**判定：成立。**

### validate export

- E2 A：partial + 5 个 `meets=false` ⇒ `[S9]×5` / rc=1  
  `validate-export-e2-20260919T211540.txt:69-79`
- E2 B：result=fail 的合法出口 ⇒ rc=0  
  `validate-export-e2-20260919T211540.txt:80-86`
- E3 literal：schema 拒绝 live + reconstructed 残留  
  `validate-export-e3-20260919T211540.txt:2-9`
- E3 clean：既有 `[S3]` + `[S9]×5`  
  `validate-export-e3-20260919T211540.txt:10-22`

**判定：与 validator 行为一致。**

### 负控 1 / 2 还原

- 负控 1：
  - 跑前后 YAML SHA 均为 `ca5a2d5e…`
  - `mid_rc=1`
  - 还原后 status 标题为空输出
  - 见 `negctl-1-20260919T211541.txt:3,11,13-14`
- 负控 2：
  - 同 SHA 前后一致
  - schema 拒 `note`
  - `mid_rc=1`
  - 见 `negctl-2-20260919T211541.txt:3,7-19,21-22`
- 当前 HEAD blob 与磁盘 YAML SHA 也同为 `ca5a2d5e…`

**判定：成立。**

### landgate / desens

- `landgate-20260919T211549.txt:1-5`
  - `PREV=a03f0ce3 HEAD=9b2089fb`
  - exclude `_bmad-output` 后仅 README + YAML
- `landgate:34-35`
  - 本卡 PREV..HEAD `.py` 集合大小 0
- `desens-final-20260919T211549.txt:2-7`
  - 各敏感项 0
  - live outputs anchor identical

**判定：存档层面成立。**

## ③ 是否仍有未披露强主张

**未发现新的“零写 / 零副作用 / 真冷启 / 19 条首见 / 机器保证真实实测”类强主张。**

当前关键措辞已经收窄：

- 只读定义限定为“发起命令面 + outputs 锚点”，并明确不证明 service 层零副作用：
  - `docs/release-evidence/README.md:198`
  - `UAT:217`
- cold 明确进程历史命中未证：
  - `slo-manifest.yaml:36`
  - `slo-manifest.yaml:93`
- 真实实测要求明确为消费纪律、非机器门：
  - `slo-manifest.yaml:266`
  - `README:270-271`
- code SHA 未证明、draft 未锁版、service 层写点未审等仍保留在 UAT 未证明清单：
  - `UAT:213-222`

残余只有 L-R3-1 的 README 句式歧义；不构成新的实质性 overclaim。

---

## 关卡建议

**现在状态**

- 三项 r2 wording 中，M/L 已解除；
- H 的输出结果已复算，但输入构造与 pre-assert 未落档；
- 全套重跑存档与 HEAD 自称绑定一致，但最新组仍待 commit B 入库。

**不建议现在把 H-R2-1 记为完全解除。**

**解锁条件**

1. 补负控 3 的 A/B 输入构造证据与 B 腿 pre-assert 输出；
2. 修正 UAT 权威证据组指针，统一指向 A3 最新重跑组；
3. commit B 入库这些证据后，再做最终 SHA 绑定核。
