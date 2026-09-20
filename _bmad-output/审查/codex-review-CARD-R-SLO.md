> 批次: BATCH-2026-09-18-第十五批 · 车道 P10 · 卡 CARD-R-SLO round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-R-SLO.md)"`
> 审查绑定: `8e36c412`（A（首轮；审后被 A2 整改））
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，行号括注；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: glm-5.3`（stderr :5） / `reasoning effort: max`（stderr :9）

---
## 结论

**0 BLOCKER / 4 HIGH / 1 MEDIUM / 1 LOW。**  
commit A 的地盘与四项已测数值本身核得住；draft/locked 边界、cold 的 1×000 保留、E2 `rc=0` 条件也都如实披露。主要问题集中在：cold 口径被 warm 预跑污染、导出契约有两条未被机器覆盖的失真路径、以及“现网零写”的说法强于证据能证明的范围。

---

## BLOCKER

无。

---

## HIGH

### H1. cold 不是声明的“20 条首见串”，且复跑命令缺少实际使用的 `-m 120`

**证据：**

- warm 命令明确取 seed 第 1 条并重复 20 次：  
  `docs/release-evidence/slo-manifest.yaml:76`，执行于 `:86`（17:11:44），存档 `measure-rag_warm-20260919T171144.txt:1-23`
- cold 命令随后读取同一 seed 文件全部 20 条：  
  `docs/release-evidence/slo-manifest.yaml:99`，执行于 `:109`（17:12:26），存档 `measure-rag_cold-20260919T171226.txt:1-6`
- 但 yaml 声称 cold 是“20 条首见串各一次”：  
  `docs/release-evidence/slo-manifest.yaml:36`、`:93`
- 实际第 1 条在 cold 前 42 秒已被 warm 查询 20 次；因此 cold 队列至多是 **19 条首见 + 1 条已暖查询**，不是 20 条首见。
- 另外，cold 实测原因明确说使用了 `curl -m 120`：  
  `docs/release-evidence/slo-manifest.yaml:110`；但 `method.command` 里没有 `-m 120`：  
  `docs/release-evidence/slo-manifest.yaml:99`。按 yaml 命令复跑时， timeout 行为不等于实测。

**影响：** cold 本来已因 1×000 判 `not_measured`，所以没有错误达标结论；但 manifest 作为 versioned SLO 的定义面，其 cold/cache 口径和复跑命令不实。该缺陷应在下一 revision 修正，不能把本轮 cold 描述成有效 first-seen 样本。

---

### H2. “现网零写 / live vault 只读”只能证明到“发出的 HTTP 命令面 + 一个输出文件未变”，不能证明服务层零写

**证据：**

- README 声称 8011/7691 不写：`docs/release-evidence/README.md:198`
- 脱敏门只证明：yaml 无绝对路径/敏感值、`measure-*.txt` 无写端点字样、live outputs 前后相同：  
  `desens-final-20260919T202600.txt:3-17`
- live outputs 只比对了一个文件：  
  `live-outputs-before.txt` / `live-outputs-after.txt`，均为 `outputs/今日复习.json`
- data SHA 是事后采集：`docs/release-evidence/slo-manifest.yaml:32`，没有同口径跑前 data SHA
- UAT 自己明确承认 `/rag/query` service 层写点未审，且可能有 42 次查询留痕：  
  `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:197`、`:210`

**影响：** 不能断言发生了写；但“零写”现在是 **UNVERIFIED / 门未覆盖的路径**。准确表述应收窄为“发起请求面无写端点、live outputs 锚点未变；service 层副作用未审”。若要证明 live vault 全量只读，需要跑前/跑后全量 data SHA 或等价审计。

---

### H3. `not_measured + meets:true` 是校验器未覆盖路径；E2/E3 存档只证明了作者导出器填 `false` 的路径

**证据：**

- yaml 导出规则说 `not_measured` 项 `meets` 只能 false：  
  `docs/release-evidence/slo-manifest.yaml:263`
- schema 只要求 `meets` 是 boolean：`manifest.schema.json:527-529`
- S9 只有在 threshold/measured 都能解析成同单位数字时才交叉核对：  
  `backend/scripts/validate_release_manifest.py:442-450`
- 若 `meets=true`，校验器直接 `continue`，不会检查 `measured=="not_measured"`：  
  `backend/scripts/validate_release_manifest.py:457-458`
- E2 存档显示的是本卡导出器实际填 false，并在 partial 下触发 `[S9]×5`：  
  `validate-export-e2-20260919T202340.txt:4-24`
- E3 清理版同样是 false 路径的 `[S9]×5`：  
  `validate-export-e3-20260919T202346.txt:13-24`
- 没有负控输入把 `not_measured` 项改成 `meets=true` 验证会红。

**附带缺口：** S9 对 E3+ 只要求 measurements 非空：`backend/scripts/validate_release_manifest.py:437-440`。如果消费卡只导出一条达标指标、省略 not_measured 指标，S9 不检查“9 项全导出”。这也是门未覆盖的路径；本卡 E2 导出了 9 项，但机器不强制未来消费卡同样做。

**影响：** yaml 的“只能 false”是填写纪律，不是机器保证。README 的泛化边界（`meets` 由填写者判定、无数值比较）在 `README.md:268` 有披露，但没有点名这两条具体绕过路径。消费门需要显式检查：`measured=not_measured ⇒ meets=false`，且导出集合覆盖约定指标。

---

### H4. null threshold 的实际导出行为 `(未定)` 未写进 `export_shape.mapping`

**证据：**

- 5 项 metric 的 candidate/locked 均为 null：cold `slo-manifest.yaml:94-97`、写侧四项 `:164-167`、`:188-191`、`:212-215`、`:236-239`
- mapping 只写了 locked 或 candidate 两条来源，没有写二者皆 null 时的 fallback：  
  `slo-manifest.yaml:260-261`
- schema 要求 `threshold` 是 minLength=1 的 string，不能导出 null：  
  `manifest.schema.json:510-517`
- 实际 E2 导出/校验输出显示 null threshold 被写成 `(未定)`：  
  `validate-export-e2-20260919T202340.txt:16-20`

**影响：** “mapping 文字与实际导出行为一致”这点不成立。按 yaml 文面执行会在 5/9 项上无从取值；按存档行为则需要补一条明确规则，例如 `locked/candidate 均为 null ⇒ "(未定)"`。

---

## MEDIUM

### M1. 写侧/未测项的 `method.command` 部分是方法草案，不是可直接复跑命令

**证据：**

- first index：`LANCEDB_DATA_PATH=<隔离目录>（独立进程/隔离实例）; ...` 不是可执行 shell 形态，也没有启动独立实例的命令：  
  `slo-manifest.yaml:169`
- Graphiti ACK 的请求体写成 `<episode 请求体见端点契约>`，未给可复跑 body：  
  `slo-manifest.yaml:193`
- recovery/replay 依赖 `<实例>` / `<cls 实例容器>` 等未绑定占位符：  
  `slo-manifest.yaml:217`、`:241`

**影响：** “每项都有 command 字段”成立，“每项都有可复跑采集命令”只部分成立。至少 first_index 与 graphiti_ack 需要未来 owner 卡补成可执行命令或明确标注为 method sketch，不应称为可直接复跑。

---

## LOW

### L1. 负控还原后的 `git status --porcelain -- docs/release-evidence` 未在存档中落证

**证据：**

- 负控 1 红在指定断言且前后 SHA 相同：  
  `negctl-1-20260919T204126.txt:2-15`
- 负控 2 红在 schema 拒收 `note` 且前后 SHA 相同：  
  `negctl-2-20260919T204126.txt:3-25`
- 但两件存档都没有还原后的 `git status --porcelain -- docs/release-evidence` 输出；UAT 只描述了还原方法：`UAT-CARD-R-SLO-2026-09-19.md:142-145`

**影响：** 文件内容还原有 SHA 证据；“status 为空”这一句是 **UNVERIFIED**。风险低，但下次负控应把 status 输出直接落档。

---

## ② 作者自述逐条核对

| # | 结论 | 核对结果 |
|---|---|---|
| 1 | **PARTIAL** | 字段齐：machine/OS/runtime/model/data scale/SHA/cache/concurrency/timezone/seed/repeats/statistic/adjudicator 都在 `slo-manifest.yaml:16-42`。machine/OS/model/data SHA/kg 等与 `env-probe-*`、`data-sha-*` 相符。seed hash/20条构成未在本次允许读取面内重算。更关键：`cache_state` 的“cold=20首见”不实，见 H1。 |
| 2 | **PARTIAL** | 每项都有 `method.command` 字段；yaml 无 `/Users/` 绝对路径，`desens-final-*:3-11` 支持无敏感值。但 cold 命令缺 `-m 120`，写侧部分命令不可直接复跑，见 H1/M1。 |
| 3 | **成立（cold 口径另见 H1）** | 四项 measured 数值与 `measure-stats-summary-*:5-19` 逐项一致；rebuild raw n=5 与存档 timing 相符。cold 的 `000 120.003677` 保留在原始存档 `:5`，并导致整项 `not_measured`；19 个成功样本的 p50/p95 仅作描述。写侧四项无估计值。 |
| 4 | **PARTIAL** | 五键与 schema `additionalProperties:false` 相容，`"not_measured"` 过 minLength；E2 B 在 `result=fail` 下 `rc=0`：`validate-export-e2-*:26-33`。但 null threshold fallback 未写明（H4），`not_measured+meets=true` 未被机器拒绝（H3）。candidate 追加 `(candidate)` 的实际导出文本未在存档中完整展开，精确字面为 UNVERIFIED。 |
| 5 | **PARTIAL** | revision 格式本身符合 `slo-manifest@<date>-rN`；`status: draft` + `locked_by:null` 自洽（`:6-15`）。“与校验器测试内既有形态相同”因测试文件不在本卡指定读取面，**UNVERIFIED**。 |
| 6 | **PARTIAL / 强 claim UNVERIFIED** | 发起命令面、live outputs 锚点、脱敏扫描支持“未主动打写端点”；但 service 层写点未审、无全量 live vault 前后 SHA，因此“现网零写/live vault 只读”未被证明，见 H2。 |
| 7 | **PARTIAL** | 两段负控都红在指定断言，且 yaml 前后 SHA 逐字同。还原后 git status 为空未落档，见 L1。 |
| 8 | **成立** | 我真跑了指定 diff；非 `_bmad-output` 面只有 README 与 yaml。`landgate-*:2-16` 亦证 README 11 行纯新增、yaml 268 行新增、README 删除行数 0。 |

---

## ③ 重点问题直接回答

- **⓪ yaml 是否自洽但不实：** threshold candidate 的数字来源可追溯到四项实测 p95；null threshold 明标无依据。但 cold/cache 的“20 首见”不实，且“进程未重启”虽写明，却不足以修正 warm 预跑污染。
- **① not_measured 误填 meets=true：** 会被 S9 放过；E2/E3 只证明 false 路径会触发 S9，不证明 true 被拒。
- **② README 锁版规则 vs 校验器：** README 与实际一致：S9 只查 E3+ revision 非 null 和 measurements 非空，不查 draft/locked/存在性；该无机器门已写进 `README.md:196` 与 `:270`。
- **③ 非200 与 p95：** cold 1×000 如实保留并导致 `not_measured`；p95 公式与 n=5 重建口径在 yaml 写明。注意 5.36s 是“其余 19 个 200 样本”的描述，不是包含 timeout 的 20 样本 p95。
- **④ 负控与 E2 rc=0：** 两段负控红因正确。E2 `rc=0` 的条件（改 `result=fail`）已在 UAT `:118-120`、`:180` 如实披露；E3 字面改造先红在 schema，清理版才是 `[S9]×5 + [S3]×1`，也已披露。
