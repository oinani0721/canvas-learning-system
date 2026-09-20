你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景

CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r21 = 用户 2026-09-20「追加修复，直到审核说没有问题而通过」授权的第 6 个预算外轮**。闸门：**绑最终 HEAD 的一轮 B/H/M/L = 0/0/0/0** 才说「复核第十五批 P6」并释放合并门。

上一轮 **r20（含 r20 补）= B0/H0/M0/L1**（存档 `codex-review-CARD-G8-10-r20.md`，绑 `fd2046f7`）：唯一 LOW = UAT §十 出现**两个编号 70**（r20 新增五条复用 70，且 §十.72 的内部引用在双 70 下无法唯一解引用）；复核给出的最小修复 = 新增五条重排为 71–75 并修正内部引用。

- **本轮绑定**：`67db0c6198a6f0b91c116da5136a65cf857b7f0e`（r21 commit；父 = `fd2046f7`）。**本轮只改 UAT**（§十 重排 + 内部引用），其余文件与 r20 补一致。
  - **已入库（该 SHA 树内；逐条 `git cat-file -e 67db0c61:<path>` 校核过：**15/15 通过**）**：`g810-r12-artifact-audit.zsh`（v2.6.3）、`g810-r8-sidecar.py`（v4.9-r20.2）、`g810-r15-audit-ctl.zsh`（C1–C9）、`g810-r15-sidecar-negctl.zsh`（N1–N14+P3+T+P1）、`g810-r20-sidecar-rerun.zsh`；`audit-ctl-r15-20260920T162933-10633.txt`、`sidecar-negctl-r15-20260920T163053-12113.txt`；`sidecar-g810-r20-74746264.json`；两代复跑件（`…-v4920`×2、`…-v49202`×2）与两个合并件；UAT。
  - **未入库（收尾阶段新增；本 prompt 不据其数字作论断）**：`g810-green-r11-20260920T163755.txt`、`artifact-audit-r12-20260920T163755-16865.txt`、`jev-triage-67db0c61.json`、`jev-triage-67db0c61-run-20260920T163807.txt`、`sidecar-g810-r21-67db0c61.json`、`sidecar-g810-r20b-fd2046f7.json`、`jev-triage-fd2046f7.json`、`jev-triage-fd2046f7-run-20260920T163128.txt`、`codex-review-CARD-G8-10-r20.md`、`prompts/codex-prompt-CARD-G8-10-r20.md`、本 prompt、本审查存档（r20 轮与 r21 轮的收尾件均随 r21 收尾 commit 入库）。
- **r21 修法**：§十 重排（原双 70 之后四条顺移；现为 70..75 连续无重复），并把「r20 补未证明面」的内部引用由 §十.72 改为 §十.73（其指向的「r20 未证明面（复述）」现编号 73）。
- **本轮 JEV 说明（如实）**：r21 只改 UAT ⇒ JEV 分诊 **0 triaged 文件（`calls: 0`）** ⇒ 按卡文口径记 **PARTIAL**（sidecar `partial: true` + `partial_reason`，`verdict/urgency/risk/review/test = null`；**不得写「已审」**）。请判定该 PARTIAL 记录是否满足本轮 sidecar 要求。
- **product code diff = 0**；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。

# ② 请独立核对

1. UAT §十 是否再无重复编号、且内部引用（§十.73/75 的「同 §十.…」）指向正确条目（可 `grep -nE '^[0-9]+\.' ` 对 §十/§十一/§九 三节各扫一遍复算）。
2. r20 的 M 级问题（若你重新评估）是否仍为 0：`row-file` 真后缀 + 复跑绑定两处的既有结论是否仍成立（树内证据未变）。
3. 已入库 20/20 与未入库 7 件是否与 `67db0c61` 树一致（可 `git cat-file -e` 复算）。
4. 声明边界（§十.36–75）是否仍属「可接受」；若需计 M/L，给最小反例。

# ③ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」）。某级无条目写「无」。

**若四级全无，请在开头写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`**（该行是本 goal 释放合并门的依据）；否则给分级与最小反例。

# ④ 边界

只读；不连任何库；只评 r21 的 UAT 变更 + 既有工具/证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且本轮未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面。
