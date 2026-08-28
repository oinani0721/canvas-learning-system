---
type: uat
title: "UAT · CARD-G4-16 doc_type 族接线普查与裁定（2026-08-28）"
date: 2026-08-28
status: awaiting_user
scope: "BATCH-2026-08-28-第五批 / CARD-G4-16 — doc_type 18 文件 146 行普查、6 取值接线/死值裁定、两处名实不符注释修正"
worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
---

# UAT · CARD-G4-16 doc_type 族接线普查与裁定

> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
> 你的笔记进搜索库时会被贴一个"文档角色"标签（doc_type：普通笔记/视频转录/白板/检验白板/概念节点）。
> 这张卡把这个标签在代码里的**每一次出现（146 处）查了个遍**，逐个回答"这标签真的有人在用吗，还是挂空挡"，
> 并修正了两条撒谎的注释。**没有改任何行为**——检验白板不进搜索结果的隔离防线一个字节没动。

## 📌 你需要过目的三个结论

1. **标签体系基本是真的**：note / video_transcript / whiteboard / exam_board 四个值全部"接线"——尤其 whiteboard/exam_board 是"检验白板不让搜索抄答案"隔离防线的第二层（7+1 处消费点实测在位），live 库 2203 条里的 16 条白板内容在默认配置下确实被排除在检索外（有一个默认关闭的旧回退开关会绕过这层，已登记 follow-up，这张卡按铁律不碰隔离面）。
2. **抓到一个"假消费者"**：代码注释声称"概念笔记（concept）按类型加权、权重最高"——实测这条加权的直接查表**从来没生效过**（查表用的是另一个字段，那个字段永远不会等于 concept；你的 117 条概念笔记实际按"所在路径"拿权重：普通路径按手写笔记最高档 1.0，放在视频目录下的按转录 0.75）。对你现在的检索结果**没有实际影响**（Codex 复核补充：该键还参与一个阈值的整体计算，但当前不是决定值）。已改正注释，删除死键列为 follow-up。
3. **值域没有关门**：frontmatter 里 `type:` 写什么就入库什么（无白名单校验）——目前 live 库 0 条野值，但这扇门要等 G8-1 台账定了角色口径后再关（已登记 follow-up，本卡不越权代定）。

## ✅ 技术验证（Claude 已代跑）

| 项 | 结果 | 证据 |
|---|---|---|
| 枚举锚定（判据 a） | `git grep -n doc_type 37387a86 -- "backend/*.py"` = **18 文件 146 行**（pinned；裸 grep 会扫 .venv 得 30/198——复核须用 pinned 命令），与勘探预告一致；逐行清单入证据包 | `G4-16-evidence/doc_type-146-occurrences@37387a86.txt` |
| 基线先行存档（判据 b） | 动手前存档两个落点测试文件基线：**9 failed / 102 passed**（全部 9 条为既有失败，勘探预告约 10、实测 9 按实测为准） | `G4-16-evidence/baseline-before-edits.txt` |
| 6 取值逐个裁定（判据 a） | note/video_transcript/whiteboard/exam_board=**接线**（exam_board live=0 两因已实测坐实）；concept=**值接线；权重键直接 lookup 不可达、聚合可达非决定项**；空串/自由值=**值域未闭合**（登记 FU-3/FU-4） | 报告 §4 + live 分布实测（video_transcript 2001/concept 117/note 69/whiteboard 16/exam_board 0） |
| ≤1h 轻量处置（判据 c） | `supplementary_reranker.py` concept 键注释 + `supplementary_search_service.py` :1044 区注释——两处均**注释-only**（ruff 全过；git diff 无任何代码 token 变化） | git diff 本卡 commit |
| 零新增失败（判据 e） | 处置后重跑：**9 failed / 102 passed**，FAILED 清单逐条 diff 为空 → PASS | `G4-16-evidence/after-edits.txt` |
| grep 复核 0 未裁定残留（判据 e） | 生产面 doc_type 取值字面量全集 = {note, video_transcript, whiteboard, exam_board}（写侧/排除集）+ concept/空串（§4 已裁）——无表外残留 | `G4-16-evidence/live-distribution-and-value-grep.txt` |
| 隔离面零改动（硬边界） | exclude_doc_types 7 处消费点、目录黑名单、config.py 防御注释：0 触碰（git diff 自证） | git diff 本卡 commit |
| Codex 独立审查 round-1 | **FAIL**（0 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW）。同时确认三项硬判据 PASS：两文件与 HEAD **无属性 AST 完全相等**（注释-only 铁律成立）、隔离面零改动、9 条既有失败根因归因正确（独立溯源翻转 commit `fcd34953`）；pinned git grep 18/146 独立复算一致 | `_bmad-output/审查/codex-review-CARD-G4-16.md` |
| Codex findings 逐条整改 | **10/10 完成**（见下）；整改含 1 项本轮补做的实测（exam_board live=0 两因坐实）；整改后复跑落点测试失败节点与基线逐条相同 | 报告 §9 + 证据包 |
| Codex 复审 round-2 | **仍阻断**（7/10 CLOSED；HIGH-3/MEDIUM-3/MEDIUM-5 未闭合 + 3 新 MEDIUM + 1 新 LOW）。同时独立复跑坐实三条铁律：AST 全等注释-only、隔离面零改动、9 failed/102 passed 与基线同集合同顺序；HIGH-2 的 live vault 两因经其独立 find 复测确认 | `_bmad-output/审查/codex-review-CARD-G4-16-round2.md` |
| round-2 findings 逐条整改 | **7/7 完成**：自由值权重加路径条件 / §8 摘要与 §1 口径统一 / 测试 provenance 补强+诚实边界 / source_type 赋值链表述修正 / reranker 陈旧算例注记 / 字面量 grep 降级为辅助视图 / 根脚本行号按 pinned SHA 修正。整改后 AST 仍全等、9 failed/102 passed 不变 | 报告 §10 + 证据包 |
| 独立 Workflow 4-agent 复核 | 枚举 agent：18/146、写入方双路径、exclude 7+1 处、TYPE_WEIGHTS 死键论证全 CONFIRMED（0 blocker）；注释-only agent：tokenize 剥离注释后 **代码 token 逐一相同**（707/3940 个），运行期 TYPE_WEIGHTS/阈值三值断言全过 | Workflow wf_737b1a95-20b journal |

## 🔧 Codex round-1 整改记录（10/10 关闭，FAIL → 整改完毕）

- **HIGH-1 遗漏 MCP 生产消费方**：note_search_tools:289/:385 把 clean 材料 doc_type 透传进 MCP 输出 metadata——"0 生产读取方"表述撤回，报告 §3 与注释改为如实声明透传消费。
- **HIGH-2 exam_board live=0 归因错误**：原"目录黑名单先行拦截"不完整。本轮补实测：live vault `节点/考察-*.md` 实存 **0 个**（exam-quick 写入的目录可索引、黑名单不拦）+ `检验白板/` 唯一 1 md 被黑名单拦——两因叠加坐实，UNVERIFIED 消除。
- **HIGH-3 六值表混同 doc_type/source_type**：concept 命中的权重键由路径启发的 source_type 独立决定（/videos/ 下→0.75 非 note 1.0）；自由值笔记权重仍 note 1.0（非 DEFAULT）；image_ocr→0.6（非 0.5）。§4 行 5/6 与两处注释全部重写。
- **HIGH-4 根 scripts/ 命名空间遗漏**：`migrate_story_frontmatter.py:60` 的 `doc_type: story` 是 BMAD frontmatter 同名异物——报告 §1 增范围声明如实登记。
- **MEDIUM-1 非绝对死键**：get_filter_threshold() 聚合消费全表（chat.py:428 生产调用）——裁定改"直接 lookup 不可达、聚合可达非决定项"，FU-1 补删键前置断言。
- **MEDIUM-2 调用链写错**：生产加权 = rerank() 内 weights.get，get_type_weight 仅测试调用——注释与报告修正。
- **MEDIUM-3 通用 sink**："写入方唯一"限定为"两显式生产者 + add_documents 无校验 sink"。
- **MEDIUM-4 Tier-2 旁路**：`ENABLE_LANCEDB_TIER2_FALLBACK`（默认关）开启后绕过 doc_type 排除——隔离结论限定 Tier-1 + 新增 FU-5（本卡铁律禁改隔离面，仅登记）。
- **MEDIUM-5 可复验性**：枚举命令改 pinned `git grep`（裸 grep 扫 .venv 得 30/198 陷阱写明）；证据包补 `test-run-metadata.txt`（命令/Python 版本/HEAD/对照口径）。
- **LOW-1 whiteboard 来源行号**：:2740 frontmatter 直通为写侧来源、:2767 仅消费——§1/§4 修正。

## 🔧 Codex round-2 复审整改记录（7/10 CLOSED → 剩 3 项 + 4 新发现全关闭）

- **HIGH-3 未闭合**：§4 仍无条件写"自由值→note 1.0"，但放在 `/videos/` 下会变 0.75。→ 加路径条件二分表述。
- **MEDIUM-3 未闭合**：§8 移交摘要退回"写入方唯一"，与 §1 的"两生产者 + 通用 sink"自相矛盾。→ 口径统一。
- **MEDIUM-5 未闭合**：测试证据缺过滤管道说明与 blob 摘要，10 行摘要不是所列命令的直接产物。→ metadata 补齐命令管道/pytest.ini 影响/blob 摘要/exit code，并**如实声明历史 stdout 无法事后补造**（可复验的是当前 HEAD 复跑同结果，Codex 已独立复跑确认）。
- **新 MEDIUM ×3**：source_type 非"纯路径启发"（image_ocr 显式、neighbor_expansion 运行期）→ §8 修正；reranker floor 注释仍写翻转前算例 → 加注历史情形与 FU-2 归属（仍注释-only）；字面量 grep 含假阳性 → 降级为启发式辅助视图并补生成命令。
- **新 LOW**：根脚本行号按 pinned SHA 修正为 migrate:62 / sync:63、:85。

## 📄 交付物清单

- `_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md` — census 报告（18 文件角色表 / 6 取值裁定 / follow-up 登记 / G8-1 对齐条目）
- `_bmad-output/审查/G4-16-evidence/` — 146 行清单、before/after 测试对照、live 分布实测
- `backend/app/services/supplementary_reranker.py` / `supplementary_search_service.py` — 两处注释修正（注释-only）
- `_bmad-output/审查/codex-review-CARD-G4-16.md` — Codex 独立审查存档

## ⏭️ follow-up（显式登记，本卡不代裁）

- **FU-1** TYPE_WEIGHTS["concept"] 删键（非绝对死键：阈值聚合可达——删键前须断言阈值不漂移 + 补回归断言）
- **FU-2** 落点测试 9 条既有失败（根因：`fcd34953` 权重翻转未同步测试断言；floor 用例应调输入使 floor 继续触发而非放宽预期——Codex 口径）
- **FU-3/FU-4** doc_type 白名单校验 + image_ocr 写路径补字段——枚举口径**依 G8-1 台账定版**，本卡不代冻结值域
- **FU-5** Tier-2 fallback flag（默认关）开启后绕过 doc_type 排除——隔离面收口归后续卡（本卡铁律禁改）
