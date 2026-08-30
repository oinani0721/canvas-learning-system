# g5-3-evidence — 分层稳定 ID 与 diff 契约取证

> **批次**: BATCH-2026-08-29-第六批 / CARD-G5-3 · 执行日 2026-08-30
> 被测物: `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` **v4.0**
> 契约正文: `docs/design/split-stable-id-contract.md`
> 裁判: `backend/tests/skills/test_split_stable_id.py`（**110 条**）+ 存量 `test_split_preview.py`（34 条）= **144 passed**
> 审查存档: `../codex-review-CARD-G5-3.md`（Codex 两轮 + 6 镜头 workflow 28 agent）
> 硬边界: live vault **全程只读**；产物写本 worktree 的 `canvas-vault/outputs/`；
> 变异演示只作用于 scratchpad 里的副本。

## 先红后绿履历

| 阶段 | 结果 | 存证 |
|---|---|---|
| 1. 只写裁判、未动引擎 | **19 failed / 2 passed** | `red-before-impl.txt` |
| 2. 引擎实现后首跑 | 5 failed —— 3 条是**裁判 fixture 自己写错**（漏了 `# 主板` 这级祖先）、1 条 out 目录撞名致「零产物」断言假绿、1 条 diff MD 缺「未执行」字样 | 见下方「裁判自身缺陷」 |
| 3. 修正后全量 | **64 passed**（30 新 + 34 存量） | — |
| 4. Codex 一轮 + 6 镜头 workflow（11 根因全处置 + 逐条补门） | 85 passed | — |
| 5. Codex 二轮复核（3 HIGH + 3 MEDIUM + 2 LOW 再处置 + 补门） | 100 passed | — |
| 6. Codex 三轮复核（3 PARTIAL + 13 类残余边界收口） | 123 passed | — |
| 7. Codex 四轮（语义层 1 HIGH + 产物清单 PARTIAL；把「整类收口」的过头说法改回诚实的信任边界） | 132 passed | — |
| 8. Codex 五轮（指正「只能绑层数」是推理错误 + 证伪 §4.1 #6 + 补齐 3 条无门的边界行） | 138 passed | — |
| 9. Codex 六轮（「自洽伪品」测试其实不自洽——第二次把可查的东西算进信任边界；补 5 道守卫 + 收紧 2 处措辞 + 补漏列的「换父」） | **144 passed**（110 新 + 34 存量） | `pytest-green.txt` |

那 2 条从一开始就绿的测试是**故意**的：`TestSchemaV2Additive`（v1 字段清单）与
`test_preview_mode_still_requires_vault_and_board` 断言的是「升级后不许破坏的既有行为」，
它们在实现前就该绿——绿是它们的正确状态。

### 阶段 2 暴露的裁判自身缺陷（记下来，因为它们本可以变成假绿）

1. **out 目录撞名**：`test_rejects_v1_schema_input` 里 diff 的 out-dir 用了 `out-7a`，
   而同测试前面 `preview(..., tag="7a")` 已经创建了 `out-7a`。
   「拒绝路径必须零产物」这条断言当时是靠**别人建的目录**才失败的——
   如果反过来（引擎真的漏写了守卫），它会因为目录本来就在而**假绿**。已改用独立的 `reject-7a`。
2. **fixture 预期漏祖先**：三条断言把 `heading_path_normalized` 写成 `["父章节","子小节"]`，
   实际板文件有 `# 主板` 这级 H1 祖先，正确值是 `["主板","父章节","子小节"]`。
   引擎是对的，裁判是错的——先红先照出来的正是这类问题。

## live 真实板取证（卡片 (d) 「≥2 块真实板两次运行 stable_id 完全一致」）

`run_live_evidence.sh`（set -x 全命令回放 + 逐步 rc + 引擎字节绑定）：

| 判据 | 结果 |
|---|---|
| live 基线 before/after 全字段 diff | **rc=0 零净差异**（`live-full-before.tsv` / `live-full-after.tsv`） |
| `CS188 lecture 2` 两跑 preview JSON | **逐字节相等**（27 候选，全部 stable_id 一致） |
| `特征值与特征向量` 两跑 preview JSON | **逐字节相等**（1 候选，整篇回退） |
| stable_id 明细清单（人可核对，不只靠 diff 沉默） | `live-stable-ids.txt` |
| run1 vs run2 的 diff | 两板均 `{added:0, changed:0, removed:0, moved:0, unchanged:27/1}` | 
| 引擎与全部产物 digest | `engine-and-products.sha256` |

基线采集器复用 G5-2 的 `../g5-2-evidence/collect_live_baseline.py`（同一把尺，
判定边界与它一致：atime 不采、before/after 快照不排除「先改后恢复」、xattr/ACL 未采）。

## 四态实景演示（真实内容，非合成 fixture）

`run_four_state_demo.sh` + `mutate_board.py`：把 live 的 `CS188 lecture 2` 及节点池
**只读复制**到 scratchpad，在副本上施加四种互不重叠的改动，跑 diff。

变异目标由 `mutate_board.py` 按候选分布自动选——该板的 27 个候选**全部来自种子笔记
`节点/lecture 2.md`**（板体本身是脚手架），写死板文件会打空，这一点被首跑当场照出来了。

实测结果（`four-state-demo-summary.txt`）：

```
summary={"added": 2, "changed": 1, "removed": 1, "moved": 1, "unchanged": 24}
  changed  bsa1-c367a1abd4899411  reasons=['content']   课程概述与理性代理
  added    bsa1-b3311ff77462b4ad                        理性代理-(Rational-Agents)
  moved    bsa1-e77719c20b7c29d9                        反射代理-(Reflex-Agents)
  added    bsa1-5774ca7ab109fb84                        规划代理-(Planning-Agents)-1459()（修订版）
  removed  bsa1-f5dcfd4b5a403353                        规划代理-(Planning-Agents)
```

三处值得解释清楚（否则会被误读成缺陷）：

1. **为什么 added 是 2 而不是 1**：一条是改标题带来的新 ID（`规划代理…（修订版）`），
   另一条 `理性代理-(Rational-Agents)` 是**内容门效应**——补的那句正文落进了这个
   子小节的直属正文，把它从「不足 2 行 / 60 字」推过了门槛，于是它**新成为候选**。
   这不是 ID 不稳定，是候选集合本身变了（契约 §4.3）。
2. **为什么改标题后节点名里多了 `1459()`**：`clean_heading` 的时间戳剥离锚定**行尾**。
   原标题 `2.3 规划代理 (Planning Agents) [14:59]()` 里时间戳在行尾会被吸收；
   追加 `（修订版）` 后它不在行尾了 → 不被剥离 → 进了名字也进了身份键。
   这条锚定边界写在契约 §2.2，此处是它的实拍。
3. **moved 只有 1 条**：`moved` = LCS 补集（最小移动集），交换两块只标其中一块。
   契约 §8.4 已声明这是定义使然而非漏判；完整位移图景看 entry 的 `old.rank`/`new.rank`。

live 基线在演示前后同样对账 rc=0（脚本末尾），证明「复制出去改副本」没有回写 live。

## 目录内容

| 文件 | 说明 |
|---|---|
| `red-before-impl.txt` | 阶段 1 先红存证（19 failed / 2 passed） |
| `pytest-green.txt` | 全绿存证（144 passed） |
| `run_live_evidence.sh` | live 取证脚本（自记录） |
| `live-run-log.txt` | 上者的 set -x 完整转录 |
| `live-full-before.tsv` / `live-full-after.tsv` | live vault 全字段基线（diff 为空） |
| `live-stable-ids.txt` | 两块真实板的 stable_id / 指纹 / occurrence 明细 |
| `live-diff-summary.txt` | run1 vs run2 的四态汇总 |
| `engine-and-products.sha256` | 引擎与全部产物的字节绑定 |
| `run_four_state_demo.sh` / `mutate_board.py` | 四态实景演示（scratchpad 副本，live 只读） |
| `four-state-demo-log.txt` / `four-state-demo-summary.txt` | 演示转录与汇总 |
| `dump_ids.py` | 取证辅助：把 preview/diff 打成人可核对的清单 |
| `judge-and-contract.sha256` | 裁判与契约文档的字节绑定（两份 manifest 均 `shasum -c` 通过） |
| `raw-reviews/` | 原始审查转录：Codex 全文 + 6 镜头 workflow 全量 JSON |
| `run_mutation_check.sh` / `mutate_engine.py` / `mutation-check.txt` | 回归门变异反证（33 个变异体逐个撤销修复，断言对应的门变红） |
| `verify_manifests.sh` | 证据自洽校验：两份 manifest `shasum -c` + 绿证条数与实跑一致（一条命令随时复跑） |
| `.gitignore`（`run1/`） | `run1/` 是两跑比对的中间物（live preview 全量副本），与 outputs/ 内容重复且含用户讲义标题，**不入库**；「两跑一致」由 `live-run-log.txt` 的 `b*-two-run-diff rc=0` + 字节 manifest 证明，复跑脚本即可重建 |

⚠ `canvas-vault/outputs/` 下的 preview / diff 产物**不入 git**（沿用 G5-2 惯例：
那是 live vault 内容的投影，属用户数据）。它们留在工作区供你在 Obsidian 打开查看。

## 对抗审查后的加固（详见 `../codex-review-CARD-G5-3.md`）

Codex 判「不通过」（2 BLOCKER / 3 HIGH / 2 MEDIUM / 2 LOW），6 镜头 workflow 存活 24 条。
去重后 **11 个真实根因**，全部处置并逐条补了回归门。其中三处是两路**独立**命中、
交叉印证的：

1. **规模门跨线报假 removed**（5 个镜头 + Codex 同时命中）——两侧阈值**相同**时，
   板体跨过阈值就会把尾部一字未动的小节挤出窗口报成 removed。现网 `CS188 lecture 2`
   已 27/30。→ 告警条件放宽到 `over_threshold` + 条目打 `⚠截断嫌疑`。
2. **`## Concepts` 重复列种子 → 整板 exit 1**（相对 G5-2 的可用性倒退）→ 源头 NFC 去重。
3. **fallback 命名含行号 → 纯行漂移报 changed(name)**（与契约 §4.2 直接冲突）→ 锚点去行号。

Codex 独有的两条 BLOCKER 处置口径也记在案：
- **重复标题的身份歧义**不改语义、改**权威范围**（`identity_ambiguous` 红旗 + §7.6 禁止
  G5-10 持久化）——因为单跑 preview 只有位置与内容两种区分信息，二者必居其一；
- **G5-10 指纹时序矛盾**改存两个指纹（确认时刻 / re-baseline 后）。

### live 判据不再能被静默跳过

Codex 一轮 HIGH-3 实证：把 `LIVE_VAULT` 指到不存在路径后整套仍 exit 0（`2 skipped`），
卡片 (d) 的「≥2 块真实板」硬门形同虚设。现在缺 live 一律 `pytest.fail`；
只有显式 `G53_ALLOW_NO_LIVE=1` 才降级 skip 且理由里写明 UNVERIFIED。
反证：指向 `/private/tmp/definitely-not-a-vault-g53` → `rc=1, 2 failed`。

## 回归门变异反证（补「先红」的缺口）

对抗审查抓到的 11 个根因是**先修后补门**，所以那批回归门的「先红」没有天然存证。
`run_mutation_check.sh` 补上这一环：把每条修复**逐个撤销**（在 /private/tmp 的引擎副本上，
不动仓库任何文件），让对应的门跑在被污染的引擎上，断言它**变红**。

结果：**33 个变异体全部让对应的门变红 —— 无空转门**（`mutation-check.txt`，日志内 engine/judge 哈希与当前文件逐字相符）。

⚠ **一条如实声明的缺口**：还有一条修复没有行为门 ——「身份自检从规模门截断之后移到之前」。
它唯一已知的可达触发路径是「同一来源文件被扫两次」，而那条路径已在**源头**
（Concepts 种子 NFC 去重）消除；去重之后同一份 preview 内的四元组按构造互异，
除非发生 64-bit 哈希真碰撞否则自检根本触发不了，也就无法用黑盒测试证明「它跑在截断之前」。
该修复保留为纵深防御，覆盖状态是「无测试」，不假装有。
