# 05 — G1-8 备料（截图清单 + 审查任务书素材要点）

> ⛔ 本文件**只备料**：不写终审结论、不做脱敏包（ChatGPT 终审 / 脱敏包 / 四态复核唯一 owner = G1-8）。
> 用途：G1-8 开卡时直接引用本目录路径与截图清单。

## 1. 截图清单（授权走查后由用户/主 session 存入本目录；车道只 `shasum` 登记）

| 登记名（`screenshots/`） | 环节 | 拍摄对象 | 实见 |
|---|---|---|---|
| `user-01-annotate-context-144003.png` | ① | Obsidian + 节点 | 悬浮提示「berkeley-cs-support-resources 未创建」（批注/双链现场） |
| `user-01-callout-rendered-144005.png` | ① | Obsidian + 节点 | 渲染态 question callout（用户尝试拖选处） |
| `lane-01-annotate-issue-1413.png` | ① | Obsidian | 插件 Notice「请先选中文本再批注」 |
| `lane-01-selection-read-empty-crop-1442.png` | ① | 放大裁剪 | 渲染态 callout 细节（GLM §B.1 判定用图） |
| `lane-render-compare-crop-1444.png` | ①（观感） | 对照裁剪 | 14:10 vs 14:40 渲染对照 |
| `user-06-refresh-503-154428.png` / `user-06-refresh-503-154449.png` | ⑥ | Chrome | `/api/v1/review/overview/refresh` → 刷新失败·test-vault / HTTP 503 pick_failed |
| `lane-06-503-testvault-1613.png` | ⑥ | Chrome | 同失败页（车道 16:13 复现） |
| —（仍缺） | ② ③ ④ ⑤ ⑥成功页 | — | 无留影；②/④/⑤ 产物 sha 在案，③ 为 0 命中返回原文 |

> 约束：png 逐文件 `git add`，单文件 ≤ 2 MB（超出改 jpg 质量 80）；截图由用户/主 session 存入，车道只登记 sha（见卡文 (o)）。
> **已登记（2026-09-20 19:09）**：8 件（用户侧 4 / 车道侧 4），台账 `artifacts-sha-screenshots-20260920T190917.txt`；
> 用户侧原件来源 = 桌面 `截屏2026-09-20 下午2.40.03 / 2.40.05 / 3.44.28.png` 与**主干树 `feature-obsidian-hybrid-dev` worktree** 的 `_bmad-output/截屏2026-09-20 下午3.44.49.png`（batch15 主干收尾树）。
> 隐私口径：含用户 Obsidian/浏览器画面，原样收录未脱敏；G1-8 对外引用前须自行脱敏。

## 2. 审查任务书素材要点（供 G1-8 开卡时引用；不含结论）

1. **旅程定义**：两白板（原白板 `CS 61B` → 检验白板）一条链 —— 现 vault 新材料 → `/board-recap` → `search_notes` → `/start-exam-board` → `/quiz-answer`（本地 `mastery_*` + `fsrs_bridge`）→ 次日总览页（`/api/v1/review/overview/page`）。
2. **证据面**：本目录 `00-README.md`（六环节表）/ `01-skill-versions.md`（dev↔live DIFF=8）/ `02-live-snapshot-before.txt` + after（零静默改写门）/ `manifest.json` / `03-breakpoints.md` / 本文件；裁判存档 `unit-open|close-*.txt`、`silent-rewrite-gate-*.txt`、`negctl-*.txt`、`manifest-red|green-*.txt`。
3. **必须核的关键点**（照卡文 §四 prompt 三分节）：① 零静默改写门是否真能抓到集外变化（负控① 是否红在指定文件而非「diff 非空」）；② 白名单是否过宽（`节点/` 整目录放行会否掩盖 skill 误写别的节点）；③ `search_notes`「检回含新材料」判据可否被旧材料同名命中而假绿；④ 环节⑤「`mastery_*` 出现或变化」是否足以证明 FSRS 更新（`fsrs_bridge` 字段是否也该核）；⑤ 断点归属是否把「部署冻结造成的差异」误记为缺陷；⑥ 未授权路径下本卡产出是否仍有独立价值。
4. **边界**：只读、不连库（观察只经 `http://127.0.0.1:8011` GET）、不评 G1-8 终审、不评 G6-13 跨日、不评 8 处 skill 差异本身的对错。
5. **诚实声明（供 G1-8 参考，非结论）**：见 `manifest.json` 的 `known_limitations` 与 UAT 验收单「本卡未证明什么」段（各 ≥4）。
