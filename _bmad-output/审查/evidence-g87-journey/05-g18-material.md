# 05 — G1-8 备料（截图清单 + 审查任务书素材要点）

> ⛔ 本文件**只备料**：不写终审结论、不做脱敏包（ChatGPT 终审 / 脱敏包 / 四态复核唯一 owner = G1-8）。
> 用途：G1-8 开卡时直接引用本目录路径与截图清单。

## 1. 截图清单（授权走查后由用户/主 session 存入本目录；车道只 `shasum` 登记）

| 文件名 | 环节 | 拍摄对象 | 应显示 |
|---|---|---|---|
| `shot-1-<ts>.png` | ① vault 准备 | Obsidian 主窗口 | 选定板（默认 CS 61B）新增节点/批注 |
| `shot-2-<ts>.png` | ② board-recap | Claudian 侧栏 + Obsidian | `/board-recap` 执行与 `outputs/回顾-*.md` 落地 |
| `shot-3-<ts>.png` | ③ search_notes | Claudian 输出 | 检索返回含环节①新材料 |
| `shot-4-<ts>.png` | ④ start-exam-board | Obsidian | 新检验白板 `type: exam_board` |
| `shot-5-<ts>.png` | ⑤ quiz-answer | Obsidian 节点 | 节点顶部 `mastery_score` 变化 |
| `shot-6-<ts>.png` | ⑥ 次日总览页 | 浏览器 | `http://127.0.0.1:8011/api/v1/review/overview/page` 渲染 |

> 约束：png 逐文件 `git add`，单文件 ≤ 2 MB（超出改 jpg 质量 80）；截图由用户/主 session 存入，车道只登记 sha（见卡文 (o)）。

## 2. 审查任务书素材要点（供 G1-8 开卡时引用；不含结论）

1. **旅程定义**：两白板（原白板 `CS 61B` → 检验白板）一条链 —— 现 vault 新材料 → `/board-recap` → `search_notes` → `/start-exam-board` → `/quiz-answer`（本地 `mastery_*` + `fsrs_bridge`）→ 次日总览页（`/api/v1/review/overview/page`）。
2. **证据面**：本目录 `00-README.md`（六环节表）/ `01-skill-versions.md`（dev↔live DIFF=8）/ `02-live-snapshot-before.txt` + after（零静默改写门）/ `manifest.json` / `03-breakpoints.md` / 本文件；裁判存档 `unit-open|close-*.txt`、`silent-rewrite-gate-*.txt`、`negctl-*.txt`、`manifest-red|green-*.txt`。
3. **必须核的关键点**（照卡文 §四 prompt 三分节）：① 零静默改写门是否真能抓到集外变化（负控① 是否红在指定文件而非「diff 非空」）；② 白名单是否过宽（`节点/` 整目录放行会否掩盖 skill 误写别的节点）；③ `search_notes`「检回含新材料」判据可否被旧材料同名命中而假绿；④ 环节⑤「`mastery_*` 出现或变化」是否足以证明 FSRS 更新（`fsrs_bridge` 字段是否也该核）；⑤ 断点归属是否把「部署冻结造成的差异」误记为缺陷；⑥ 未授权路径下本卡产出是否仍有独立价值。
4. **边界**：只读、不连库（观察只经 `http://127.0.0.1:8011` GET）、不评 G1-8 终审、不评 G6-13 跨日、不评 8 处 skill 差异本身的对错。
5. **诚实声明（供 G1-8 参考，非结论）**：见 `manifest.json` 的 `known_limitations` 与 UAT 验收单「本卡未证明什么」段（各 ≥4）。
