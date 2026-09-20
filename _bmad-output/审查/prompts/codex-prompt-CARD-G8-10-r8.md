你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r8 = 用户 2026-09-20 裁定的「收敛轮」**（卡文 `收敛-CARD-G8-10-checker.md`：取代 r7 的「停」指令，连续 loop，直到绑最终 HEAD 的一轮 **B/H/M/L = 0/0/0/0** 才释放合并门；不逐轮交主 session；预授权最多 8 个 develop commit）。

- **本轮绑定**：`3457f70bc7b407a2c2e63a86c85c54cee89ac516`（r8 develop commit；父 = `dce85102` = r7 收尾 ④′）。r8 全部改动只在 `_bmad-output/**`：核对脚本 v4.5 → **v4.6**（sha256 `6e44e1437638fced14321dc239f4cc84cb0940f44fc7f0abd9fe2129a22590ae` → `3fd001741b7c80106684e36c8244ed2bbd9a8c7daf9802062c11419738793faf`）+ UAT r8 段 + evidence + 运行器；**product code diff = 0**（`git --no-pager diff --stat 4120e0b6 3457f70b -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。
- **r8 修法（7 项 open finding 全开修；口径见 UAT §九.30）**：
  ①（r7-H1）`StrictSafeLoader`（`construct_mapping` 按**显式 key** 检重，`<<` merge 键除外）⇒ 重复显式 key = `yaml-duplicate-key` 红；新增 `yaml.compose_all` **node 层扫描**（mapping 键 `outcome` 的值节点 strip == pass ⇒ `pass-unsupported`；覆盖 anchor 源 / 被 merge 消费的内层映射 / alias）——注意 **PyYAML 无 `AliasNode` 类**（composer 已把 alias 解析为同一节点对象）；v4.5 的 constructed 扫描保留。
  ②（r5-M1）`_resolve_under_root()`：file:line 引用与 **nodeid 同口径**归一化（绝对 / `..` / 越根 ⇒ 红）；nodeid 归一化后须在 `backend/tests/` 下。
  ③（r5-M2）`_check_provenance_tokens()`：`_bmad-output/` 根的无行号 evidence 路径必须存在 + 内容**逐文件进 digest**；平文 SHA 形态放宽为「4–40 位纯字母数字 token 且不在 `_ALNUM_NON_SHA_ALLOW`」⇒ 必须可解引用为 commit 且 **tree OID 进 digest**；白名单死项 ⇒ `token-allow-dead` 红。
  ④（r6-M1）`_owner_ids()`：owner ID 必须是**独立 token**（`path:line` 文件名内的 ID 子串不再满足）。
  ⑤（r7-L1）输出拆分 `dirty=… dirty_tracked=… dirty_untracked=…`；**r7 已入库证据文件未改**（其「树净」按本口径读作 tracked 净）。
  ⑥（r6-L1）**机器可读 sidecar manifest**（`g810-r8-sidecar.py` 生成；不改 `scripts/jev_review_triage.py`）。
  ⑦（幽灵引用）两副本核定：权威副本（feature 树，卡文指定为准）**含** §2.4/§2.4.1/§2.4.2/§2.4.3；车道本地副本停在 `8856390d`（第十四批）只有 §2.1–§2.3 ⇒ r7-era「协议无 §2.4/§2.4.1」只对本地陈旧副本成立；r8 起 §八 按 **§2.4.1** 引。

**最小读取面**（其余不必读）：

1. 脚本 diff：`git --no-pager diff --no-color dce85102 3457f70b -- _bmad-output/审查/evidence-g810/check_g810_refs.py`；并读 v4.6 全文（重点 `StrictSafeLoader` / `_collect_anchors` / `_scan_node_outcome_pass` / `_owner_ids` / `_check_provenance_tokens` / `_resolve_under_root` / main 内 YAML 段与 dirty 拆分）。
2. 负控（**先红后绿**，各两相位）：`negctl-r8-pre-20260920T131616.txt`（v4.5 九例全穿透 rc=0）→ `negctl-r8-post-20260920T131629.txt`（v4.6：A/B/C `pass-unsupported`〔node 层〕+ A 另含 `yaml-duplicate-key`、D `nodeid-missing 路径越界`、E1/E2 `ref-missing`、F1 `sha-missing`、F2 rc=0 但 digest 变 = 绑定、G `owner-missing`）；回归 = `regress-r8-{pre-20260920T131648,post-20260920T131656}.txt`（r6-A/r6-B/r7-A/r7-B 两相位红 + r7-H1 原形 pre rc=0 → post rc=1）；锚群 = `anchor-battery-r8-v46-20260920T131707.txt`（8/8 红 + 对照 rc=0）；YAML 门 = `yamlgate-branches-r8-v46-20260920T131716.txt`（5/5 红 + 对照 rc=0）；正常底账 = `g810-green-r8-20260920T131722.txt`（`v4.5@dce85102 = 767bc1af…` → `v4.6@dce85102 = a0269b1d…`，rc=0）与 **post-commit 复跑** `g810-green-r8-20260920T132049.txt`（`prev@dce85102 = 401019c2…` → `v4.6@3457f70b = e0e91238…`，rc=0，`dirty_tracked=1 dirty_untracked=0`）；开工自证 = `r8-startup-selfcheck-20260920T131816.txt`；幽灵引用核定 = `ghost-ref-check-r8-20260920T131742.txt`。
3. UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md`：§九.29–34（r8 开工自证/修法/幽灵引用/负控表/作废件/收尾结构）+ §十.25–31（r8 未证明什么）+ §十一.26–31（r8 待登记）；r8 判定字段 = 收尾回填（PENDING-R8，见 §九.34）。
4. 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md` §3 fenced YAML 块（**不要写死行号**）+ §2.13 六链表（r8 未改底账内容）。
5. JEV 分诊：`jev-triage-3457f70b.json` + 运行 stdout `jev-triage-3457f70b-run-20260920T132134.txt`（jev-1.13.0，`calls: 1`，唯一代码文件 = `check_g810_refs.py`（+262/−17），urgency **2.99** / P(review)=0.84 / risk=logic / VERDICT REVIEW）+ **机器可读 sidecar** `sidecar-g810-r8-3457f70b.json`（字段 calls/verdict/urgency/risk/review/test/code_files/sha/bound_head + 逐字段 provenance；另附 r7 retro `sidecar-g810-r7-retro-6816ff71.json`）。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **r7-H1 闭合**：复核者原形（`- {dim: observability-extra, outcome: "pa\u0073s", outcome: not_yet, coverage: partial}`）在 v4.5 下 rc=0（穿透，见 regress pre）、v4.6 下 rc=1（`pass-unsupported` node 层 + `yaml-duplicate-key`）；另两条同族（merge 源内 `!!str pass`、scalar alias 经 merge 源）v4.5 穿透 → v4.6 红。
2. **r5-M1 闭合**：`backend/tests/../app/models/service_status.py::ServiceStatus` v4.5 穿透 → v4.6 `nodeid-missing 路径越界（含 .. 段）`。
3. **r5-M2 闭合**：evidence 目录引用（不存在 / 物理移走）v4.5 穿透 → v4.6 `ref-missing`；平文 SHA 畸形值（`6337e32z8`）v4.5 穿透 → v4.6 `sha-missing`；**替换为另一有效 commit** ⇒ rc=0 但 digest 变（`a0269b1d… → 67e41faa4dff55e8dc912797c3e3b129`）= 绑定成立。
4. **r6-M1 闭合**：owner cell 只含「文件名带 G4-3 的 path:line」= v4.5 穿透 → v4.6 `owner-missing`。
5. **未放宽旧失败面**：r6-A/r6-B/r7-A/r7-B 两相位皆 rc=1；8 锚 8/8；YAML 门 5/5；正常底账 rc=0（两代 digest 链见上）。
6. **r7-L1 口径**：checker 输出 `dirty_tracked` / `dirty_untracked`；r7 已入库证据文件字节未改（未追改历史件）。
7. **r6-L1 口径**：sidecar 由 `g810-r8-sidecar.py` 生成（不改上游分诊脚本）；字段缺 ⇒ 生成器非 0 退出。
8. **幽灵引用**：两副本 grep 实证（见 §①.2 的 `ghost-ref-check-r8-*`）；卡文 §1 的「协议 §2.4」在权威副本下**不是**幽灵引用；UAT §八/§九.25 已加指向更正。
9. **未越界**：底账内容一字未动；只改 `_bmad-output/**`；product code diff = 0；未 amend 历史 commit（r8 = develop commit + 收尾 commit 两段，§九.34）。

# ③ 请按重要性回答（JEV urgency 降序：唯一代码文件 = checker，urgency 2.99 / risk=logic）

① **7 项 finding 是否真的闭合**？逐项给判（特别：r7-H1 的重复 key / merge 隐藏 / scalar alias 三形态是否都可被绕过——给**未被拦下的输入**或确认闭合；`StrictSafeLoader` 是否可能引入既存底账假红）。
② v4.6 是否仍有与**其声称**不符的恒绿面？（重点：`_check_provenance_tokens()` 的形态判定与白名单、node 层扫描的 alias/anchor/merge 覆盖、`_owner_ids()` 的 token 语义、`_resolve_under_root()` 的边界、dirty 拆分口径；UAT §十.25–31 的声明边界请判定「可接受」还是「仍需计」）
③ r8 证据链是否自洽：先红后绿、回归、锚群、YAML 门、digest 两代链、`sha_equal=yes`、绑定（`:(exclude)_bmad-output`）、UAT 的 PENDING-R8 口径（收尾回填）。
④ **本轮收口条件（B/H/M/L = 0/0/0/0）是否满足**；不满足请给最小反例输入（**M/L 也要给**——本 goal 的闸门含 M/L）。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**；若四级全无，写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`——该行会用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评核对脚本 v4.6 与 r8 证据面 + 上述 7 项闭合；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r8 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界（非 fence YAML 面 / 非 `outcome` 键 / 产品树散文路径）在**本轮**扩面——若你认为需扩面，记为 MEDIUM/LOW 并指出准确边界即可。
