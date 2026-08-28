# 验收单 · CARD-G5-4 偏航 lint 一梯队信号脚本化

> **批次**: BATCH-2026-08-28-第五批 · 车道 S6 第一卡
> **分支**: `card/s6-recap`（不 push，等你验收）
> **日期**: 2026-08-28
> **一句话**: 从今往后 `/board-recap` 的回顾报告里会多一小块「信号板」——四个**纯数字**信号
> （最老的未答问题挂了几天 / 多少成员有来源出处 / 几个拆出来的点说不清来源 / 批注里有没有重复堆积），
> 数字全部由脚本算、AI 只能照抄，**没有任何"你偏航了"的判定——判断留给你**。

---

## 一、你会看到什么（用户产品体验）

1. 以后在 Claudian 里跑 `/board-recap <板名>`，报告的「③ 方向」段开头会有一个信号小卡片，四行：
   - **未答问题年龄**：最老 78 天（参与统计 4 条，p25/p50/p75 = 77/77/77 天）【文件】
     ——这是你 CS188 板的真实数字：最老一条疑问已经挂了两个半月（天数随时间增长，取数时刻见证据包）
   - **来源覆盖率**：7/8 成员含来源锚点【文件】
   - **无来源结论**：0/7 派生角色成员缺来源锚点【推定】
   - **重复堆积**：0/4 条批注为重复条目【文件】
2. 每行末尾的【实测/文件/推定】告诉你这个数字有多可靠；算不出来的信号会诚实写「**无据**」，
   绝不用别的数字顶替
3. 报告**不会**说"你偏了"——只给数字和板内分位参考，偏没偏由你自己判断
4. 你的白板、节点、整个 live vault：**一个字节都没被改**（三块真实板实测取证，见下）

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 裁判测试 `backend/tests/regression/test_recap_scan_signals.py` | **105 条全绿**（`--collect-only` 实测数；24 首轮 + 四轮 Codex 与两轮 workflow 复核的逐条回归锁） |
| 既有 scan JSON 键回归 | v1 顶层键 + counts 键面逐一断言零破坏（加性铁律） |
| 0 阈值 | signals 块全层级无判定/合格线类键（键名扫描断言）；`policy: zero_threshold` |
| 零编造 | denominator==0 → value=null + availability=无据（空板/无 tips/无派生三形态各有用例） |
| 措辞两模式通杀 | fallback 与 manifest 两版全量报告（含信号行）过自家 verifier——派生词禁令与「偏离」禁词 0 命中（fixture 锁定） |
| --verify fail-closed | 篡改任一信号数字 exit 1（四信号 parametrize）；档位造假 exit 1；缺行 exit 1；无据错标双向 exit 1；**无据行夹带数字 exit 1**（含括号数字/全角斜线/中文数字四变体）；**未闭合 HTML 注释 exit 1**；**四信号合并成一行 exit 1**（防档位互相借用）；**信号行搬到 ③ 段之外 exit 1**；signals 子对象 schema 违约 exit 1（四变体）；fallback 写「无派生」exit 1 |
| 数据面口径一致 | role 判定认 `derived-from`/`derived_from`/`created_from=ai_linked_doc` 三形态（对齐后端 `_node_role`）；空 frontmatter 键不再从下一行捏造值；frontmatter 值里提到关键词不翻 role；`[[节点/null]]` 归一幂等 |
| 旧 JSON 兼容 | 无 signals 键的旧 scan JSON + 旧版报告 → verifier PASS（gate 绑定键存在） |
| 两模式一致性 | 用**真** `build_manifest` 交叉断言：同一 vault 的来源覆盖/无来源两信号 fallback 与 manifest 全等（F1 回归锁） |
| ledger 加性 `source_note` | manifest 透传 + fallback 抄录归一 stem，null 字面量不计锚 |
| ≥2 真实板 live 只读实测 | CS 61B / 特征值与特征向量 / CS188 lecture 2 三板，stdout 重定向 scratchpad，live vault **全 324 文件（含 .claude/）** shasum 前后**全等**（证据 `_bmad-output/审查/g5-4-evidence/`） |
| SKILL.md 同步 | 分工铁律 + Step 2 字段清单 + Step 4 维度③ + Step 5 模板（信号行格式与无据铁律）+ Step 5.5 规则 11；ROUTING 校验 66/66 |
| 关联回归 | `test_board_manifest_contracts.py` 64 绿 + `tests/skills/` 全量绿（合并 **234 passed**） |
| 与后端口径对拍 | 新增 `test_role_matches_backend_node_role_exactly`：直接 import `board_manifest_service._node_role`，对同一 frontmatter（null/空/引号空串/带注释的 created_from/manual 五形态）断言 fallback 与后端**结论相同** |

### 对抗审查（两条独立审查线）

**Codex ultra**
- round-1：`codex-review-CARD-G5-4.md`——6 项实质发现全部处置
  （F1 两模式信号分叉 HIGH / F2 未闭合注释渲染隐藏 BLOCKER 候选 / F3 无据行夹带数字 /
  F4 null 字面量计锚 / F5a verifier fail-open / F5b+F6 截断口径与 fixture 失真）。
  终稿遭 Codex 平台过滤器误拦（已知坑），发现清单从完整 transcript（193k tokens）提取存档
- round-2：`codex-review-CARD-G5-4-round2.md`——**BLOCKER 0 / HIGH 4 / MEDIUM 3 / LOW 2**，九项全部处置
  （H1 role 拼写分叉 / H2 无据行数字四变体绕过 / H3 同行档位借用 / H4「无派生」同义句 /
  M1 归一幂等 / M2 子对象 schema fail-open / M3 ③段范围 / L1 fixture 忠实度 / L2 文案）
- round-3：`codex-review-CARD-G5-4-round3.md`——**HIGH 8 / MEDIUM 7 / LOW 4**（裁决 FAIL），
  逐条处置见 `codex-review-CARD-G5-4-round3-处置.md`：verifier 从"词表匹配"升级为
  **整行严格模板 fullmatch** + 结构级段落禁令；role 判定改为与后端 `_node_role` 同构的 truthiness 三支
- round-4：`codex-review-CARD-G5-4-round4.md`——终裁轮（中断前口头提出的 4 点已一并修复并加锁）

**多视角 workflow（并行独立复核）**：两轮 fan-out（5 视角 + 4 视角，共 22 agent），抓出 7 条实质发现，全部亲手复现确认并处置——
其中 **W2**（空 frontmatter 键从下一行捏造值，既有 v1 缺陷被新信号放大）、
**W4**（G5-9 tmp symlink 写穿 vault 外，BLOCKER）、
**幽灵链接自相矛盾数字**与 **created_at 假 UTC 致 exam_history 排序错位**是 Codex 各轮均未覆盖的面。

### 实现构成

- `canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py` — signals 构建器 + verifier 信号绑定扩展（加性）
- `canvas-vault/.claude/skills/board-recap/SKILL.md` — 六处同步
- `backend/tests/regression/test_recap_scan_signals.py` — 105 条裁判
- `_bmad-output/审查/g5-4-evidence/` — live 三板取证（全部处置后最终重取版）

## 三、验收步骤（1 分钟）

1. 打开 `_bmad-output/审查/g5-4-evidence/README.md`，看三块真实板的信号表——
   「CS188 最老未答问题 78 天」「CS 61B 来源覆盖 0/2」这些数字符不符合你的直觉
2. 你的白板确认没被动过（shasum 前后全等已代验，也可随便开一块板看看）
3. 想真跑一次：等这批合并部署后 `/board-recap CS188 lecture 2`，看 ③ 段的信号卡片

## 四、诚实边界（不掩饰）

- 未答问题年龄基于 tips 的 `added_at` = **最后变更时间**而非首次批注时间（C5 已知边界），所以该信号永远只标【文件】档
- 学习 vault 没有「已答」标记，「未答」是**上界**（报告里也这么写）
- fallback 模式的「派生角色」是本地推定（推定档如实标注）；重复判定是文本归一后全等（200 字截断口径已声明），不做语义相似
- live 后端未起时三板走的都是 fallback——manifest 模式的【实测】档由 fixture + 真 build_manifest 交叉测试覆盖
