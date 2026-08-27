# 验收单 · CARD-G5-2 拆分建议 preview 引擎（只读）

> **批次**: BATCH-2026-08-27-第四批 · 车道 5 第二卡
> **分支**: `card/n5-split`（不 push，等你验收）
> **日期**: 2026-08-27
> **一句话**: 这是「信息收集第二刀」的读侧——它读你的白板和种子笔记，产出一份
> 「建议拆成这些节点」的预览清单（带来源行号、重名检查、已派生检查），**只出建议绝不动笔**。
> 真正创建节点要等 G5-10，且逐条经你确认。

---

## 一、你怎么看这份建议（用户产品体验）

1. 在 Obsidian 打开本 worktree 的 `canvas-vault/outputs/split-preview-CS188 lecture 2.md`
2. 你会看到：
   - **候选单元清单**：27 个建议节点（比如「反射代理-(Reflex-Agents)」），每个都标了
     它来自 `节点/lecture 2.md` 的第几行到第几行、在讲义的哪个章节路径下
   - **已派生重叠**：你以前用 Cmd+Shift+D 拆过的地方（比如 2.3 规划代理那节你拆过 3 个节点）
     被明确标出来——不会建议你重复拆
   - **重名检查**：建议名如果撞了你现有的节点，会给出 `_2` 后缀备选
   - **「确认后将发生的 wikilink 插入」**：每条候选下面有一段 diff 预览，显式写着
     **⛔ 未执行**——那只是展示「如果你确认，源文件会多出哪两行」，本轮一个字都没写
3. 再打开 `split-preview-特征值与特征向量.md`：Fundamentals 笔记没有小节结构，引擎诚实回退
   「整篇 = 1 个候选」，并且把你现网已经拆过的 `Eigenvalues-are-special-vectors-that-sat` 标为已派生重叠
4. **你的两块真实白板、所有节点、整个 live vault：一个字节都没被改**（证据见下）

## 二、技术判据（Claude 已代跑 · v2 = Codex 二轮审查后加固重做）

| 裁判 | 结果 |
|---|---|
| 裁判测试 `backend/tests/skills/test_split_preview.py` | **34 条全绿**（四轮先红后绿：首轮 14 全红 → 真实板 2 缺陷先红 → Codex 二轮 15 条对抗测试 → Codex 三轮 3 条（祖先 symlink 零写/目录级 symlink/反事实常驻+JS 空白负例）） |
| slug 金样本双向断言 | 40 字符硬砍中间值 == 现网名 `Eigenvalues-are-special-vectors-that-sat` ✅ + 现行词边界规则终值 == `Eigenvalues-are-special-vectors-that` ✅（真相源 node-derivation.ts:32 双向钉死） |
| slug 等价性 v2 | 空白集改 **ECMAScript 口径**（U+FEFF 等）+ 词边界阈值按 **UTF-16 code unit**（Codex 反例 😀+18a+-+25b 入测试）+ 连字符非空白防回归锚；四条显式偏差完整声明（时间戳 fallback→锚点哈希 / NFC 归一 / claimed 互撞 / 9+ 标注不 throw） |
| 重名 / 9+ 重名 | `_2` 后缀同规 + 9+ 标 `conflict_unresolvable` 且**停用该条展示性 diff**（不渲染可执行外观的 wikilink 行） ✅ |
| 派生重叠 | callout 命中 + 未覆盖小节不连坐 + **fence/注释里的 callout 不算证据** ✅ |
| 中文 NFC/NFD | NFD 池文件名 vs NFC 候选名仍判重名；`conflict_with` 报池内实际字节名 ✅ |
| 生成段剥离 | 仅按三类确定性标记；对抗 fixture 钉死（AUTO 对/fence/Recent Activity 内的富假小节全不成候选）；注释内标题不切分不截断；纯脚手架板 **0 单元 + 诚实自陈** ✅ |
| 同输入二跑 | JSON 与 MD **逐字节相等**（零时间戳零随机） ✅ |
| 规模门 | 超限截断且**恰为文档序最前 N 个**（名单级钉死） ✅ |
| 零写侧（物理 fail-closed） | vault 全树（文件 bytes+mtime+mode+目录集合）前后一致；板名/成员名双 containment（拒绝钉具体诊断+零产物）；**祖先 symlink out-dir 拒绝 / 硬链接目标拒绝 / symlink 目标 O_NOFOLLOW 原子拒绝 / 越界与 symlink 种子跳过留痕** 全部有测试 ✅ |
| ≥2 真实板取证 | CS188 lecture 2（27 单元）+ 特征值与特征向量（1 单元）——live vault **全部 324 文件** sha256+size+mtime_ns+ctime_ns+mode+nlink+目录+symlink 目标，v3 引擎两板运行前后 **diff 为空**（set -x 命令回放 + 引擎字节绑定 digest 全入证据包；判定边界如实声明） |
| 越界禁令 | 无 SKILL.md（`check_skill_routing_block.py` 66/66 不受影响）、无 LLM 层、不做确认/创建、不冻结稳定 ID |

### Codex 二轮审查处置（0 BLOCKER + 6 HIGH → 全部处置，逐条见证据包 README v2 对照表）

写侧物理 fail-closed（H1）/ seed 名越界读 containment（H2）/ slug JS 空白集与 UTF-16 边界（H3）/
live 宣称降为可辩护口径 + 全字段采集器（H4）/ 拒绝测试钉诊断（H5）/ 剥离对抗 fixture + 反事实（H6）；
一轮实弹 symlink 探测被引擎当场拒绝（零写入）的留痕也在包内。

### 实现构成

- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` **v3** — 确定性只读引擎（物理写侧 fail-closed 次序修正+单 FD 写 / 目录级 symlink containment / slug 精修+偏差5声明）
- `backend/tests/skills/test_split_preview.py` — 34 条裁判用例，fixtures 全部 tmp_path 程序化构造
- `_bmad-output/审查/g5-2-evidence/` v3 — 全字段 live 基线 + set -x 命令回放 + 引擎字节绑定 digest + 二/三轮处置对照表

## 三、验收步骤（2 分钟）

1. Obsidian 打开 `canvas-vault/outputs/split-preview-CS188 lecture 2.md`，扫一眼候选清单——
   建议名合不合理、行号点过去对不对、已拆过的地方是不是都被标了
2. 打开 `split-preview-特征值与特征向量.md`，确认「整篇回退 + 已派生重叠」符合你的直觉
3. 你的白板确认没被动过（也可以随便打开哪块板看一眼）
4. 不满意直接批注；「建议名不好听」这类命名打磨属 G5-3/G5-10 的确认阶段

## 四、Codex 对抗审查

- 一轮：实弹 symlink 探测被引擎拒绝后遭 OpenAI cyber 过滤器误拦中断（留痕在证据包 README）
- 二轮存档：`_bmad-output/审查/codex-review-CARD-G5-2.md`（裁决不通过：0 BLOCKER + 6 HIGH，处置见 §二）
- 三轮存档：`_bmad-output/审查/codex-review-CARD-G5-2-round3.md`（判 H5+5 项 MEDIUM RESOLVED；新抓 4 面 → v3 加固）
- 四轮存档：`_bmad-output/审查/codex-review-CARD-G5-2-round4.md`——**终裁：可验收（带声明边界）**，
  0 新 BLOCKER/HIGH；三轮全部 HIGH 判 RESOLVED；Codex 撤回其三轮对 H6 反事实测试的静态误判
  （「三轮静态推断错误，现予撤回」）。声明边界（不掩饰）：祖先替换 TOCTOU / bind-overlay mount /
  标记吞 EOF 设计立场 / TS oracle 未实跑；两项声明性 MEDIUM（零写单测未锁 xattr 等深层元数据、
  标记弱配对）保持声明状态。
