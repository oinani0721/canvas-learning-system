# CARD-G5-9 — 两份独立复核的合并处置表

> **处置卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③
> **停轮规则**: BLOCKER 或 HIGH > 0 → 再一轮；MEDIUM / LOW → 登记结案。
>
> 同一个 commit `4717a2cd` 被**两份独立复核**审过（起因见下方碰撞说明）：
>
> | 报告 | 出处 | 裁决 |
> |---|---|---|
> | `codex-review-CARD-G5-9.md` | 本卡（T2 车道）跑的 codex | 需再一轮 · BLOCKER 0 / HIGH 4 / MEDIUM 8 / LOW 2 |
> | `codex-review-CARD-G5-9-主session独立复核-2026-08-30.md` | 另一 session 并行跑的 codex | **FAIL** · **BLOCKER 2** / HIGH 4 / MEDIUM 5 / LOW 1 |
>
> 两份**不是重复劳动**：重叠 5 条，互补 8 条。对方抓到了本车道**漏判或定级偏轻**的 3 条实证缺陷。

---

## ⛔ 一、碰撞事故（必须先说，因为它影响 `9e24ef40` 的可信度）

**发生了什么**：本车道在 `card/s6-recap` 写 `codex-review-CARD-G5-9.md` 的同时，
另一 session 并行对同一 commit 做独立复核并**写入同一路径**。两个进程各持一个 fd
按各自 offset 落盘 ⇒ 产生拼接损坏文件（字节 `0..9890` 对方全文、`9890..16075` 本车道尾段、
拼接点 UTF-8 解码失败）。

**更糟的是**：该损坏文件被本车道的 `git add -A` 连同整改一起提交进 **`9e24ef40`**，
而那条提交信息却在描述本车道那份报告的内容 —— **提交信息与提交内容不符**。

**怎么发现的**：不是靠复核，是 round-2 的 Codex 在 transcript 里 `nl -ba` 打印了这个文件，
第 1 行是 `结论：**FAIL，不建议合并 4717a2cd。**` —— 与本车道报告的开头对不上。

**恢复**（两份都完整、无信息丢失）：
- 对方报告 = 损坏文件字节 `0..9890`（结尾语完整，未截断），逐字节切出；
- 本车道报告 = 由**已提交**的 transcript `g5-9-evidence/codex-round1-transcript.txt`
  第 4272–4449 行逐字重建。

**教训（已写进本卡验收单）**：
1. 多 session 并行时，**同一路径不是安全的产出位**——按车道加区分后缀，或写前 `test -e`。
2. **`git add -A` 会把并发 session 的中间态一并提交**。提交前应逐文件核对内容，
   而不是只看 `git status` 的文件名列表。

---

## 二、逐条合并对照（以「本车道整改后」为准）

| 对方编号 | 严重度（对方） | 本车道对应 | 状态 |
|---|---|---|---|
| B1 空 SHA 绕过确认门 | **BLOCKER** | HIGH-1 | ✅ **已修**（形状白名单 + 无条件比较），负验证变体 A/B |
| B2 DD-14 追踪链不合规 | **BLOCKER** | — | ⚠️ **部分处置 + 升级用户**，见 §三 |
| H3 回执 SHA 未绑定发布字节 | HIGH | HIGH-2(a) | ✅ **已修**（发布后回读比 sha），变体 E |
| H4 父目录 symlink check/use 窗口，**实测写出 vault 外** | HIGH | 本车道 MEDIUM-3（**定级偏轻，已认**） | ✅ **已修**（dirfd 锚定），变体 D/I |
| H5 undo 先 resolve 解掉 leaf symlink ⇒ 移走 referent 留死链 | HIGH | 本车道只提到 resolve 问题、未修 | ✅ **已修**（leaf symlink 直接拒绝），变体 J |
| H5 后半 close(fd) → 按路径 unlink 窗口 | HIGH | HIGH-3(1) | ✅ **已修**（unlink 前再核 identity），变体 H |
| H6 自造第二套 schema，非忠实复用 start-exam-board | HIGH | — | ⚠️ **升级用户裁决**，见 §三 |
| M7 Unicode 控制字符破坏消费兼容 | MEDIUM | — | 登记结案 → 移交，见 §四 |
| M8 `undo_hint` 不可直接执行 | MEDIUM | MEDIUM-7 | ✅ **已修** + 新增「把 hint 原样跑一遍」的门 |
| M9 多项安全测试假绿/只测前提 | MEDIUM | HIGH-4 | ✅ **已修**（33→55，假门补齐带合法 sha 的版本） |
| M10 undo 指纹不是结构化 provenance | MEDIUM | — | 登记结案 → 移交，见 §四 |
| M11 跨板共享节点**批注**被重复计数 | MEDIUM | 本车道 MEDIUM-4 只说链接未去重 | 登记结案 → 移交，见 §四（**数字错误，建议优先**） |
| L12 undo 不回目录拓扑基线 | LOW | — | 登记结案 → 移交 |

**本车道 8 MEDIUM / 2 LOW 的处置**：见 `codex-review-CARD-G5-9-round1-处置.md` §二、§三（不重复）。

---

## 三、升级用户裁决的两项（本卡不擅自决定）

### B2 — DD-14 追踪链：这是一处**规则与批次实践的冲突**，不是单纯违规

对方的依据是 `CLAUDE.md:8` 的 DD-14「commit 含 PLAN-NNN」。核查后如实陈述：

- 被审的 `4717a2cd` 是**第五批**的提交，标题用 `[BATCH-2026-08-28-第五批 / CARD-G5-9]`，无 `PLAN-NNN`；
- 但**本批与前几批的全部提交都是这个形态**（`BATCH-…/CARD-…`），不是这一条的孤例；
- 即：要么 DD-14 的 `PLAN-NNN` 口径已被 `BATCH/CARD` 实际取代而文档未更新，
  要么全批次提交都不合规。**这不是 T2 车道能单方面裁定的**，也不该由一张收口卡去改根 CLAUDE.md。

⇒ **升级用户/主 session 裁决**：确认 `BATCH-…/CARD-…` 是否为 DD-14 的合规形态并更新 CLAUDE.md，
或明确要求后续提交补 `PLAN-NNN`。

**本卡已做的部分**：对方同时点出 `CURRENT_TASK.md:5` 仍声明分支 `card/n5-split`（陈旧恢复锚点）
—— 这条属实且可立即修，已随本次整改更新为 `card/s6-recap` 的真实状态。

### H6 — frontmatter schema：**总账明文写了「需用户拍板」**

对方指出生成器用 `status: done` + `recap_kind` + `recap_boards` 并省略
`selected_node`/`questions`，与 `start-exam-board/SKILL.md:383` 的原模板不同，
且迫使 `quiz-answer/SKILL.md` 与 `Dashboard.md` 增加特判；总账 `:471` 明确记载
**该 frontmatter 形状需用户拍板**。

本卡判断：这条**不该由收口卡单方面改**——它牵动三个消费方的契约，
且已有明文的「待用户拍板」登记。⇒ **升级用户裁决**，选项大致是：
(a) 维持现状（阶段回顾板是独立 subtype，消费方特判是设计的一部分）；
(b) 改为忠实复用 start-exam-board 的 schema（则要重做 quiz-answer/Dashboard 的排除逻辑）。

⚠️ 与此相关的 MEDIUM-5（本车道）也指向同一处：`board_manifest_service` 完全不读 `recap_kind`，
把阶段回顾板计入 `exam_board_count`（实测 `exam_history 1→2`）。两条应**合并成一张卡**一起裁。

---

## 四、登记结案 → 移交（按停轮规则不再开轮）

| 条目 | 移交理由 |
|---|---|
| M7 Unicode 控制字符（U+007F 致 `file_parse_failed`；U+0085 致 `exam_history.board_id=null`） | 板名字符白名单是**跨 skill 的共同问题**（recap_scan / split_preview / start-exam-board 都受影响），不应只在本脚本单点收；建议与 G5-3 的稳定 ID 归一化（NFC/NFD）合并成一张「板名字符契约」卡 |
| M10 undo 指纹只做子串包含，手工文件正文含该串即被接纳 | 要做成结构化 provenance 需改产物 frontmatter 形状 ⇒ 与 §三 H6 的 schema 裁决同域，等裁决后一并做 |
| M11 跨板共享节点**批注重复计数**（两板共享含 1 条批注的节点 ⇒ 输出「总成员 1 / 总批注 2」） | ⚠️ 这是**数字错误**（成员已去重、批注没有），建议移交时列为优先项。本卡未修的原因：改它会改动产物里的用户可见数字，属行为变更，应与 §三 的 schema 裁决一起走，避免同一处反复改 |
| L12 缺失 `检验白板/` 时 undo 留下空目录 | 纯拓扑残留，无数据风险；fixture 总预建目录所以测不到 |

---

## 五、本次（二段）整改的判据

| 项 | 结果 |
|---|---:|
| `test_g5_9_recap_exam.py` | 33 → **55 passed**（首段 +20、二段 +2） |
| S6 完整裁判（`test_recap_scan_signals.py` + `test_g5_9_recap_exam.py`） | **160 passed**（裁定书基线 138） |
| 负验证 `round1-high-negverify.py`（⛔ 串行） | **10 变体 10/10 如期变红**；还原后字节与备份逐字相同 |
| `ruff check` / `ruff format` | All checks passed |

### 二段负验证又抓到两个「变体失效」（与首段同型，如实记录）

- **变体 D** 首跑仍绿：因为新加的 dirfd 锚定成了 symlink 防御的**第三层**，只禁前两层拦不住。
  ⇒ 变体补齐第三层后如期变红。
- **变体 I** 首跑仍绿：我只回退了 `_atomic_write` 内部的操作，但 `_open_exam_dirfd`
  的 `O_NOFOLLOW` 仍在，拒绝来自它。⇒ 变体改为**连 `_open_exam_dirfd` 一起回退**后如期变红。

> 同一个教训第三次出现：**纵深防御下，"只禁一层"的变体会给出「门非承重」的假结论。**
> 变体必须覆盖该性质的**所有**防线，否则负验证本身就是假绿。
