# 01 — skill 版本表（dev 树 ↔ live 副本 逐文件 sha256）

> CARD-G8-7（两白板全旅程走查证据包）· [BATCH-2026-09-18-第十五批]
> 数据源：`skill-versions-*.txt`（本目录，同次落档，末行 rc=0）
> dev 树 = 车道树 `card-p3-deploy` 的 `canvas-vault/.claude/skills/`；live 副本 = `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/`
> **车道 HEAD**：`9d4f7bf0bfa245cd9a36d60177ed8ff528a255cb`（= P3-B CARD-DEBT-10 末 commit）
> 生成时刻：2026-09-19T17:0x-07:00 · dev skills 文件总数（`find … -name '*.md' -o -name '*.py' -o -name '*.sh' -not -path '*pycache*'`）= **13**

## 主表 — 13 个 dev skill 文件逐文件对照（DIFF 预期 = 8）

| # | 文件 | dev 树 sha256 | live 副本 sha256 | 同/异 |
|---|---|---|---|---|
| 1 | `ai-linked-doc/SKILL.md` | `f3673ca9529eaeff1358b50e11b4a9455a12f137cd676a4d1568f5f29b2ae176` | `77807e2a8e3b6d3f291724e0f6b53c706a6cc4b6c841d13a1e63cdb30dda7767` | **DIFF** |
| 2 | `board-recap/SKILL.md` | `86ff0b3fa0179604816e9251ae35bcf0df6151f7cdc62a4ef88dd46bed4c3aa4` | `aa6eede2371a130915b7c9a55b6afc69c35894dbec8457a746b6b0dcab9c92c4` | **DIFF** |
| 3 | `board-recap/scripts/recap_scan.py` | `7ec79cba1e6b47f8463c138d2b26b7484d47c26f57928cc77c26387daf117e0e` | `210ca7fd89dee38f2371a9b276bd385ae24d464a637f4f912b8ba00ef30e3908` | **DIFF** |
| 4 | `board-recap/scripts/recap_exam_build.py` | `cf6a60b5159e2627acea6814fed0c546a1e8f684c0ab38c1a63407f5b553e771` | `MISSING` | **DIFF**（live 缺） |
| 5 | `board-split/scripts/split_preview.py` | `d088c5e38f0c6eb0f9ca98a547bb4a06a9e45eed722dbdd604a7b578602ab7ad` | `MISSING` | **DIFF**（live 缺） |
| 6 | `clear-inbox/scripts/inbox_preview.py` | `a2b97f068445d9b441262c4eb02f72071b06483e4f91d884e274b71eb631e565` | `MISSING` | **DIFF**（live 缺） |
| 7 | `quiz-answer/SKILL.md` | `6ae2558f1def3e94588bf0a043bb2d9e4b5904a618de5ec4b5260f5c206601b0` | `9652e1e1c1d2ef2aee71cf0996abaadab30a7e1e5cccc302e00df06379431006` | **DIFF** |
| 8 | `start-exam-board/SKILL.md` | `0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce` | `c605c3821f966761c2597a8a1c99df85eb0bbd5f32e46f106817272bcd7c3318` | **DIFF** |
| 9 | `chat-with-context/SKILL.md` | `cdd0472591e75860e947aa726dcbd46aa150e3eaa1ceef50be6dee332af2738c` | `cdd0472591e75860e947aa726dcbd46aa150e3eaa1ceef50be6dee332af2738c` | SAME |
| 10 | `configure-whiteboard/SKILL.md` | `9eb21ecc6ac044a914ce11009025f8a84e51c5135221ec3b50f8c021ccfa2177` | `9eb21ecc6ac044a914ce11009025f8a84e51c5135221ec3b50f8c021ccfa2177` | SAME |
| 11 | `exam-quick/SKILL.md` | `eb30e407a14145477710cbf439e7e85705afeb157c98c5993ee0b3616c324853` | `eb30e407a14145477710cbf439e7e85705afeb157c98c5993ee0b3616c324853` | SAME |
| 12 | `node-chat/SKILL.md` | `3b15bc91dabea7e7b3876b75c2c0973e7a9284d48081e5d1b864623258b40fb7` | `3b15bc91dabea7e7b3876b75c2c0973e7a9284d48081e5d1b864623258b40fb7` | SAME |
| 13 | `study-question/SKILL.md` | `0142b7833ff3ab54c9307227d59ebaa7d5ff3f9c18a76b07344d0ab295fa22e4` | `0142b7833ff3ab54c9307227d59ebaa7d5ff3f9c18a76b07344d0ab295fa22e4` | SAME |

**DIFF 计数 = 8**（dev↔live 双列，与卡文 §〇 第 2 行实测逐条一致；dev 目录 13 文件中有 8 处不同或缺失）。
live 侧 `canvas-vault/.claude/skills/` 共 **9 目录**，比 dev 少 `board-split` 与 `clear-inbox`（后两者只有 `scripts/`）。

## 附 — 脚本面两行（卡文 (c)② 要求必含；非 skill 目录，另列以保持主表行数 = dev skills 文件数 13）

| 文件 | dev 树 sha256 | live 副本 sha256 | 同/异 |
|---|---|---|---|
| `canvas-vault/.claude/scripts/fsrs_bridge.py` | `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0` | `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0` | SAME |
| `canvas-vault/.claude/scripts/decay_beta.py` | `3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90` | `3bf4ed9402a4c8edfde16630a79094a5d4518fd181fa60810319fe46d37abb90` | SAME |

⇒ 与卡文 §〇 第 3 行实测一致（`fsrs_bridge.py` / `decay_beta.py` 两侧逐字节同），`daily-review-wrapper.sh` 的 `cmp -s` 门不会因本卡状态翻红；本卡对两文件零写者。

## 结论

**旅程跑的是 live 列，HEAD 列仅供对照；本卡零部署。** 8 处 dev↔live 差异在走查窗口内冻结登记（不「顺手同步」），逐条归属见 `03-breakpoints.md`。
