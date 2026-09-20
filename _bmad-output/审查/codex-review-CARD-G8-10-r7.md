> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-7
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r7.md)"`（rc=0；2026-09-20 11:22:12 → 11:32:21 -0700；stderr 295505 字节不入库）
> 审查绑定: `6816ff71`（= 收尾 commit ④ 首对象；此后只加 `_bmad-output` 面，绑定按 §1 `:(exclude)_bmad-output` 判据）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`
> ⛔ 判定: **BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 1 ⇒ 按卡文 §5「r7 若仍有 HIGH：停，不合并、不改底账、不自动 r8；交主 session 再裁」**

---

## 结论

**r7 不满足 `B/H = 0` 收口条件**：两个 r6-H1 显形输入本身已被 v4.5 拦下，但在已覆盖的 ```yaml fenced 面内仍存在一个新的未被拦下输入——PyYAML `safe_load()` 对同一 mapping 的重复 `outcome` 键执行 last-write-wins，早先的转义 `pass` 会被后来的 `not_yet` 覆盖，而保留的正则也识别不到该转义形式。

我只执行了只读检查；未修改文件，未连接数据库或网络服务。

---

# BLOCKER

无。

# HIGH

1. **`_bmad-output/审查/evidence-g810/check_g810_refs.py:393-399` — `safe_load()` 会静默折叠重复 YAML key，早先的 `outcome: pass` 记录可在已覆盖的 fenced YAML 面内消失。**  
   **未被拦下的输入**：在 §3 现有 canonical observability criteria 行之后、同一个 ```yaml fence 内追加：
   ```yaml
   - {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}
   ```
   然后按负控口径重锚 digest 并运行 v4.5。结果为：
   - PyYAML 6.0.3 实际解析该 mapping 为 `{'dim': 'observability-extra', 'outcome': 'not_yet', 'coverage': 'partial'}`；
   - `_iter_key_values()` 只看到最后的 `not_yet`，`pass_values=[]`；
   - v4.4/v4.5 保留的散文正则对 `outcome: "pa\u0073s"` 仍为 False；
   - 新行追加在 canonical observability 行之后，`yaml_line`/summary 对照仍取 canonical 行的 `outcome: not_yet`，不会触发 `yaml-mismatch`；
   - criteria 数量也没有独立下限/结构校验。
   
   因此在重锚 digest 后，该输入没有任何指定失败项。即使将重复 key 解释为非法 YAML，当前 `safe_load()` 也不抛 `yaml.YAMLError`，没有落入已声称的 `yaml-parse-error` fail-closed 分支；这与 UAT §九.23 “递归取全部 `outcome` 键” 的声称不符，也不属于 UAT §十.17/18 已声明的“非 fence / 非 outcome 键”边界。

# MEDIUM

无。r5 两条 MEDIUM、r6-M1、r6-L1 均仍在 UAT §十.9/14/15 与 §十一.10/16/17/21 登记为“只登记不修”，我没有把它们重新升级。

# LOW

1. **`_bmad-output/审查/evidence-g810/g810-green-r7-post4-20260920T112054.txt:1` / `:6` — 该证据自称“树净”，但机器输出同时记录 `dirty=1`，严格意义上不能证明全树净。**  
   **对照输入**：直接对照该文件第 1 行标题与第 6 行 `... dirty=1 ...`；若“树净”只想表示 tracked tree clean，则 checker 当前未区分 tracked/untracked，证据应改为“tracked 净”或提供可区分的状态证据。该问题只影响证据措辞，不影响 digest 复现。

---

## ① r6-H1 是否真的闭合？

**没有完全闭合。**

已核验两个指定显形输入确实先红后绿：

- `negctl-A-r7-pre-20260920T111438.txt:8-10`：v4.4 下 `failures=0`、`neg_rc=0`；
- `negctl-A-r7-post-20260920T111632.txt:8-10`：v4.5 下 `pass-unsupported`、`neg_rc=1`；
- `negctl-B-r7-pre-20260920T111438.txt:8-10`：v4.4 下穿透；
- `negctl-B-r7-post-20260920T111632.txt:8-10`：v4.5 下红。

但上述 HIGH 的重复 key 输入位于同一 claimed 覆盖面内，故 r6-H1 的“fenced YAML 有效/可接受标量不穿透”目标仍有残余缺口。

### (a) fence 之外的 YAML 面

**判定：可接受的已声明边界，不计 HIGH。**

理由：

- 底账 authoritative 机读索引实际是 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:181` 开始的 ```yaml block；
- v4.5 的脚本注释 `_bmad-output/审查/evidence-g810/check_g810_refs.py:131-135` 明确只认 ```yaml / ```yml；
- UAT §十.17 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:205` 已显式登记裸 ```、```json、缩进代码块与散文片段不解析，并给出 `` ```json `` 内转义 pass 的未拦下输入；
- 在“定位 = 底账一致性核对，而非任意 Markdown YAML 普查”的口径下，这属于声明边界。

### (b) “记录”语义

**判定：dict 键 `outcome` 的语义可接受，不计 HIGH。**

`pass` 出现在普通字符串值、枚举列表、非 `outcome` 字段中，不等价于 `criteria[*].outcome == "pass"` 的记录语义；UAT §十.18 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:206` 已登记该边界。HIGH 反例是 `outcome` 键本身，且在 ```yaml fence 内，因此不受该边界保护。

### (c) `strip()` 与 `yaml|yml` 收紧

**未发现新的恒红或既存底账假红。**

- canonical 底账在 v4.5 下历史证据 `g810-green-r7-post-20260920T111632.txt:6-8` 为 `failures=0`；
- 我又在当前 HEAD 独立复跑，`source_digest=80839c8cb75876c1be261411675540c7`、`failures=0`、`rc=0`；
- `strip()` 只会把解析后去包裹空白仍为 `pass` 的值判红，是 fail-closed；
- `yaml|yml` 与大小写不敏感只扩大识别面；
- YAML 门分支控制 `yamlgate-branches-r7-v45-20260920T111644.txt:4-25` 显示 5 条新增失败分支均红、对照绿。

---

## ② v4.5 是否仍有与声称不符的恒绿面？

**有：HIGH-1 的重复 key 折叠。**

除此之外：

- r5 两条 MEDIUM 仍在 UAT §十.9 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:193-194` 登记；
- r6-M1/L1 仍在 §十.14/15 `:199-200` 与 §十一.16/17 `:228-229` 登记；
- §十一.21 `:233` 也集中登记为下批承载项。

这些仍是“已登记、按裁定不修”，不是本轮新 HIGH。

---

## ③ r7 证据链是否自洽？

**主体自洽；仅有 LOW-1 的“树净/ dirty=1”文书口径不一致。**

独立核对结果：

- 绑定正确：`6816ff711bda23f3e71314f83f440bd7852b15ca` 的父对象确为 `9457ba436f2fde41e607d75b3f4afb0b37b07235`；
- v4.4@parent sha256 实测 `69d9e281d7f24ec4917cefd7aeba6e3a82df4b2ea229865e007dcdaf0027ff2f`；
- v4.5@④ sha256 实测 `6e44e1437638fced14321dc239f4cc84cb0940f44fc7f0abd9fe2129a22590ae`；
- 底账 sha256 实测仍为 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`；
- `git diff --stat 9457ba43 6816ff71 -- . ':(exclude)_bmad-output'` 为空，product code diff = 0；
- r6 两负控回归：
  - `negctl-r6A-regress-v45-...txt:8-10`：两重 `pass-unsupported`，`failures=2`，rc=1；
  - `negctl-r6B-regress-v45-...txt:8-9`：`owner-invalid ... '张三'`，rc=1；
- 锚群：`anchor-battery-r7-v45-...txt:4-44` 为 8/8 rc=1，对照 rc=0；
- YAML 门：`yamlgate-branches-r7-v45-...txt:4-25` 为 0 块 / parse error / import missing / block scalar / `!!str` 五分支全红，对照绿；
- digest 三值链与证据一致：
  - v4.4@`9457ba43` = `b667ea26ef309bc99a67617967f133bd`；
  - v4.5@`9457ba43` = `54e576a8bc9094ea1e031d38acd58d4a`；
  - v4.5@④ = `80839c8cb75876c1be261411675540c7`，我在当前 HEAD 复跑得到同值且 rc=0；
- r7 负控各文件均有 `sha_equal=yes`；
- JEV stdout `jev-triage-6816ff71-run-...txt:5-12` 确认唯一代码文件、urgency 2.90、risk logic、REVIEW；JSON 本体无 `calls`/`verdict` 顶层字段，确属已登记的 r6-L1 延续；
- r6-M2 复核闭合：10:31:39 post2 三段、JEV、r6 prompt、r6 审查存档均 tracked，`post3` 0 命中；`§2.4.1` 残留已按 UAT §九.25 改为 §2.1 并登记卡文幽灵引用；
- UAT §九.26/27 `:181-182` 明确 r7 判定、post4、JEV 文件名等 PENDING 字段由收尾 amend 回填；当前首对象里这些文件未入库不构成自相矛盾。

---

## ④ r7 收口条件是否满足？

**不满足。** `B=0` 但 `H=1`。

最小反例即 HIGH-1：

```yaml
- {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}
```

该行放入现有 §3 ```yaml fence 的 criteria 数组，并重锚 digest；v4.5 的 YAML 面只看到 `not_yet`，legacy 正则也看不到 `pass`。

---

## ⑤ 其它判断

- 未发现越界：r7 first object 只改 `_bmad-output/**`，底账与 product code 均未动。
- 当前 worktree 的 r7 prompt/JEV/审查/post4 等未 tracked 文件符合 UAT §九.26 的“收尾 amend 回填”结构，不按越界处理。
- `post4` 的 `dirty=1` 如上所述只能证明 digest 复现，不能严格证明“全树净”。
- HIGH-1 的最小后续修法方向应是 strict YAML loading / duplicate-key rejection，或在进入 `_iter_key_values()` 前按事件或自定义 SafeLoader 拒绝重复 mapping key；若 PyYAML 接受重复 key，则至少应显式 `yaml-duplicate-key` 红，而不能让它 last-write-wins。
