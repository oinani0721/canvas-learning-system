# 验收单 · CARD-C5 board-recap 广度回顾 Skill（薄版）

> **批次**: BATCH-2026-08-25-跨vault与收束 · 车道 3 第二卡
> **分支**: `card/l3-recap-skill`（不 push，等你验收）
> **日期**: 2026-08-25
> **薄版硬边界**: 零写侧——绝不写你的白板/节点/检验白板；唯一写入 = `outputs/` 报告。设计稿 v2 的 research_questions 状态机与 Recent Activity 追加**明确裁掉**（拍板项 4，G5 红线）。

---

## 一、你怎么用（用户产品体验）

1. 在 Claudian 侧栏（或 vault 目录的 claude CLI）输入：`/board-recap CS188 lecture 2`
2. 等约 1-2 分钟，侧栏回执告诉你报告位置：`outputs/回顾-CS188 lecture 2-2026-08-25.md`
3. 在 Obsidian 打开这份报告，你会看到：
   - **规模自陈**（几成员/几批注/数据新鲜度，有降级会明说）
   - **你现在可以做的**（每条 = 现状 + 一个能直接照做的动作，零自填格子）
   - **台账**（种子/派生分列，每个节点的占位/考察/批注状态一行看完）
   - **AI 侧对账**（你没闭环的批注计数 + 最老 3 条原话）
   - **三维审查**（漏了什么 / 靠不靠谱 / 方向——方向段永远以材料为主语，不评判你）
4. 读完可随口说一句「记得 X 忘了 Y」——会被记进报告；不说也没关系。
5. **你的白板和节点一个字都不会被改**（见下方 shasum 证明）。

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 守门人 checker 全 PASS 且 9 skill（worktree vault） | **66/66 PASS · 9 份 skill 全绿** ✅ |
| 零静默修改：23 文件 shasum 前后一致 | **23/23 OK，0 mismatch**（覆盖五个波次共 21 次 agent 运行：19 次板级主/降级路径（含 4 次停后端 FALLBACK）+ 幂等二跑 + 假板拒绝）✅ |
| 3 板 blinded forward test（全新 agent 最小上下文）出报告且规定段落齐全 | **五个波次共 19 次板级 forward test**（Codex 实证审查驱动多轮加固重测）。终态 4 板报告全过内建确定性 verifier（`recap_scan.py --verify`）与外部 18 项机械裁判（规定段落 + HARD-R4 禁词 + ③段主语 + 占位符 + 甩锅句 + 64 位 SHA + 动作动词 + fallback 派生断言 + data_mode）；CS188/特征值=manifest 主路径，CS 61B=空 manifest 诚实降级且 manifest 专属数据全部写「无据（fallback）」✅ |
| 诚实降级：停 backend 走 FALLBACK 且报告头声明 | **线性代数板：MCP 缺失 → 静默降级本地扫描 → frontmatter `data_mode: fallback_local` + 正文头 ⚠ FALLBACK 声明，段落裁判 PASS** ✅ |
| 假板名显式拒绝 | **✗ 显式拒绝 + 列出 5 块可选板，零报告生成，不猜近似** ✅ |
| 幂等：同板同日二跑出现续读/覆盖询问 | **出现「续读上一份 / 覆盖重跑」二选一询问，未静默覆盖，并附上次「你现在可以做的」摘要** ✅ |

### 实现构成

- `canvas-vault/.claude/skills/board-recap/SKILL.md` — ROUTING 块逐字节抄 canonical（脚本注入非手打）+ PLANE-BINDING（STRUCTURE/study 视图）+ Step 2 FALLBACK 降级块
- `canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py` — 确定性收集器（纯 stdlib 只读）：manifest JSON 解析（兼容 MCP `{ok,error,manifest}` 包裹 + **fail-closed**：board_id 精确匹配/source_status 白名单/形状损坏降级）、**stdin 传参零临时文件**、**路径 containment（板名与成员名越界一律拒绝）**、种子/派生分流台账（含每种子派生子女数、每节点 tips/未闭环数）、tips 未答计数+最老 3 条（支持 `text: |-` block scalar，时间戳解析排序）、source revision（板 SHA-256 + 板文件 mtime + manifest freshness）、上次回顾「你现在可以做的」段+用户自评行抽取供闭环 diff、规模门（超线附详审名单+尾部聚合）、幂等检测（未来/非法日期不参选）
- SKILL.md 含 **Step 5.5 写后机械自检**：不再是 LLM 自查——强制跑 `recap_scan.py --verify <报告>`（确定性 verifier）：
  段落齐全 / 64 位完整 SHA / HARD-R4 禁词（偏离/你以为/其实你/你理解错/但资料说）/ ③方向段用户主语 / 占位符 / 甩锅句 /
  fallback 派生断言 / 动作项逐条白名单动词 + 无动作信号行拦截 / **数字终核**（绑定同目录 `.recap-scan-<板>.json`：
  frontmatter 三元组全等 + 规模自陈五元组 + AI 侧对账 tips 两数；快照缺失 fail-closed）——任一 ✗ 即 exit 1，不 PASS 不得发回执
- 写侧防 symlink 双层防御：SKILL Step 2 任何 Write 前 Bash lstat 预检（四路径）+ scan JSON 的 `unsafe_write_targets` 复核，非空显式拒绝
- `backend/scripts/check_skill_routing_block.py` — EXPECTED_SKILLS 登记 board-recap（8→9）+ 硬编码 "8 份" 输出改动态
- 分工铁律：数字与清单全部出自脚本 JSON；LLM 只做三维审查叙述与白名单动作句

### 证据包

`_bmad-output/审查/c5-evidence-2026-08-25/`：shasum 基线 before.txt（23 文件）+ 终核 23/23 OK + 6 次 blinded forward test 完整日志（A/B/C 三板 + D 幂等 + E 假板 + F 停后端 FALLBACK）+ 段落裁判脚本。3 份回顾报告在 worktree `canvas-vault/outputs/`（测试产物，不入 commit）。

### Codex 对抗审查

- 存档：`_bmad-output/审查/codex-review-CARD-C5.md`（重点：薄版边界零写侧 + ROUTING 逐字节）
- 共九轮对抗循环（一轮 ultra + 八轮 high 聚焦复核），每轮 Codex 以实测反例驱动加固：
  - 一轮：FAIL — 2 BLOCKER + 4 HIGH + 3 MEDIUM + 1 LOW（固定 /tmp 串料面、路径逃逸越 vault 读、fallback 宽扫、block scalar 解析、分工契约缺数据、HARD-R4 报告级失守——全部实证级发现）
  - 二轮：抓 heredoc 时序 / 目录级 symlink / tips 吞字段 / nodes:[7] 假 manifest / 混合 pick_rank 崩溃等新反例 → 全部修复
  - 三轮：判 B1/H3/H4/H6/M8 RESOLVED；残 B2 写序 + H5 数字绑定 + M7/M9
  - 四轮：判 **B2（最后一个 BLOCKER）与 M9 RESOLVED**；残 H5（verifier 缺数字绑定，成员数改 999 仍 PASS）+ M7（非编号无动作行漏检）
  - 五轮修复：scan JSON 落盘 + verifier 数字绑定（缺快照 fail-closed）+ 无动作信号行拦截；五轮复核残 H5（tips 两行可整体消失）+ 三个同义/重复类 MEDIUM
  - 六轮修复：tips 两行改必需 + 动作段结构性只许编号项 + fallback 词表扩展；六轮复核抓「影子字段」类（注释藏真/键搬正文/段落重复）
  - 七轮修复：校验前剥 HTML 注释 + frontmatter 键锚定 --- 块 + 段落唯一性；七轮 a 被 OpenAI 过滤器中断（其反例已全数被拦），b 中性重发判 **M7 RESOLVED**、H5 残单点（栅栏正则不要求整行）
  - 八轮修复：闭合栅栏整行化；八轮复核抓最后一个旁路（先剥注释再认栅栏 → `---<!--x-->` 被洗合法）
  - 九轮修复：栅栏在原始文本判定 + frontmatter 块内禁注释标记；**九轮终判：H5 RESOLVED，「BLOCKER/HIGH 清零: 是」**（21/21 栅栏×注释扩展矩阵 + 7/7 历史反例被拒 + 4/4 正样本 PASS + checker 66/66）
- 处置全记录（含每轮反例复现命令）：存档附录一至九轮
- 已声明 backlog 边界（双方确认不影响裁决）：台账行级数字绑定、开放式自然语言同义改写

## 三、待确认节（live 部署，等你点头）

本卡全部开发/测试用 **worktree 副本 vault**（含从 live 只读复制的 CS188 lecture 2 板做测试）。live 生效需要：

1. **skill 目录 cp 到 live vault**：
   `cp -R <worktree>/canvas-vault/.claude/skills/board-recap "<live>/canvas-vault/.claude/skills/"`
2. **live 板 forward test 一次**（建议先拿 CS188 lecture 2，live 后端 8011 在线 → 走 manifest 主路径）
3. 可选：live vault 的 `CLAUDE.md` Skill 索引表加一行 `/board-recap`（本卡未动 live 任何文件）

## 四、已知边界（诚实声明）

- ROUTING 块正文写着「本块在 8 份 skill 里逐字节相同」——现在实际是 9 份。该数字在 canonical 块内，改一个字 = 9 份文件同步改（HARD-NAV-4），留给下一次 ROUTING 块统一升版时顺手修，本卡不动。
- tips `added_at` 是最后变更时间非首次批注（SKILL.md 已写死时序结论只可标【文件】档）。
- fallback 模式的 role/is_stub/mastery 是本地推定，报告会全部标【推定】。
