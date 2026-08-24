---
type: dashboard
layout: active-learning-view
created_at: 2026-05-01
version: 1.0
story: "1.18"
---

# 📊 Canvas 学习仪表盘

> [!info]+ 这是什么？
> 一站式查看所有原白板状态 + 节点总数 + 平均掌握度 + 待复习节点。**Cmd+P 打开命令面板** → 搜索"启动考察"可以一键发起考察（复制 /start-exam-board 命令）。
>
> **数据源**：Plugin 实时从 `原白板/*.md` 和 `节点/*.md` 的 frontmatter 自动聚合。手动派生 / 追加 / 配置后**无需刷新**，DataviewJS 会自动重算。**例外**：FSRS 到期数消费 `outputs/今日复习.json` 投影（daily_review_pick 是到期口径唯一裁判，每日 9:05 生成），不做独立重算。

---

## 🎯 三大核心指标

```dataviewjs
const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");
const nodes = dv.pages('"节点"').where(p => p.type === "concept");

// 1. 平均掌握度（含颜色编码）
const masteryValues = nodes
  .map(p => typeof p.mastery_score === "number" ? p.mastery_score : 0.30)
  .array();
const avgMastery = masteryValues.length
  ? masteryValues.reduce((s, v) => s + v, 0) / masteryValues.length
  : 0;
const masteryColor = avgMastery > 0.7 ? "🟢" : avgMastery > 0.4 ? "🟡" : "🔴";
const masteryLabel = avgMastery > 0.7 ? "优秀" : avgMastery > 0.4 ? "进行中" : "起步";

// 2. 节点总数（按白板分组）
const nodesByBoard = {};
for (const node of nodes) {
  const sb = node.source_board;
  let boardName = "（无归属）";
  if (sb) {
    const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
    const m = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
    if (m) boardName = m[1].trim();
  }
  nodesByBoard[boardName] = (nodesByBoard[boardName] || 0) + 1;
}
const groupedStr = Object.entries(nodesByBoard)
  .sort((a, b) => b[1] - a[1])
  .map(([k, v]) => `${k}: ${v}`)
  .join(" / ");

// 3. FSRS 到期数（CARD-A2 2026-08-24: daily_review_pick 是到期口径唯一裁判,
//    这里只消费 outputs/今日复习.json 投影 (schema v3), 不再独立重算 —
//    修复 live 实测 13 vs 6 的口径分裂）
let fsrsLine = "⏳ 投影未生成 — `outputs/今日复习.json` 缺失（每日复习任务每天 9:05 自动生成，生成后此处自动出数）";
let backlogNames = [];
try {
  const raw = await dv.io.load("outputs/今日复习.json");
  if (raw) {
    const proj = JSON.parse(raw);
    // Codex-A2 H2: 结构校验 — 缺关键字段/版本异常时走明确降级,
    // 绝不把结构损坏的投影伪装成可信的"0 到期"
    const sv = proj?.schema_version;
    const hasDetail = Array.isArray(proj?.due_nodes);
    const statsDueOk = typeof proj?.stats?.due_nodes === "number";
    if (!proj || typeof proj !== "object" || typeof sv !== "number" || sv < 2 || !(hasDetail || statsDueOk)) {
      fsrsLine = "⚠️ 投影结构异常 — `outputs/今日复习.json` 缺关键字段或版本不受支持（不显示不可信数字），等下次生成自动覆盖修复";
    } else {
      const dueCnt = hasDetail ? proj.due_nodes.length : proj.stats.due_nodes;
      // due_reason 缺失时按 fsrs_due 空串退化推断 (v3 早期投影兼容)
      const reasonOf = d => d.due_reason ?? (d.fsrs_due ? "scheduled" : "new");
      const newCardCnt = hasDetail ? proj.due_nodes.filter(d => reasonOf(d) === "new").length : null;
      const malformedCnt = hasDetail ? proj.due_nodes.filter(d => reasonOf(d) === "malformed").length : 0;
      backlogNames = Array.isArray(proj.ineligible?.placeholder) ? proj.ineligible.placeholder : [];
      const backlogCnt = backlogNames.length || (proj.stats?.ineligible ?? 0);
      const parts = [];
      if (newCardCnt !== null) parts.push(`含 ${newCardCnt} 张新卡视同到期`);
      if (malformedCnt > 0) parts.push(`脏日期按到期处理 ${malformedCnt} 张`);
      parts.push(`待剖析积压 ${backlogCnt} 张另计`);
      const unassignedCnt = proj.stats?.unassigned ?? 0;
      if (unassignedCnt > 0) parts.push(`未归板 ${unassignedCnt} 张另计`);
      if (sv > 3) parts.push(`投影 v${sv}，按 v3 口径解读`);
      parts.push(`投影生成于 ${proj.generated_at ?? "?"}`);
      fsrsLine = `\`${dueCnt}\`（${parts.join(" · ")}）`;
    }
  }
} catch (e) {
  fsrsLine = "⚠️ 投影损坏 — `outputs/今日复习.json` 解析失败，等下次生成自动覆盖修复";
}

dv.paragraph(
  `📊 **平均精通度**: \`${avgMastery.toFixed(2)}\` ${masteryColor} ${masteryLabel}\n\n` +
  `📚 **节点总数**: \`${nodes.length}\`（${groupedStr || "暂无"}）\n\n` +
  `⏰ **FSRS 到期**: ${fsrsLine}\n\n` +
  `🗂️ **原白板总数**: \`${boards.length}\``
);

if (backlogNames.length > 0) {
  // 文件名含 wikilink 保留字符 (|[]#^) 时退化为纯文本, 防死链
  dv.paragraph(
    `> 🗂️ **待剖析积压**（${backlogNames.length} 张占位节点，定义未写完不参与复习，不计入到期数）: ` +
    backlogNames.map(n => /[|\[\]#^]/.test(n) ? n : `[[节点/${n}|${n}]]`).join("、")
  );
}
```

---

## 🗺️ 活跃原白板（按节点数排序，含交互按钮）

> [!success]+ v4.3 路径 1 升级 — 交互式按钮已就绪
> 每个白板行右侧多 2 个按钮：📂 打开白板 / 🚀 启动考察。点击直接调 plugin API（无需 Cmd+P）。

```dataviewjs
const plugin = app.plugins.plugins["canvas-learning-system"];
if (!plugin) {
  dv.paragraph("> ❌ Canvas plugin 未加载，请先在 Settings → Community plugins 启用。");
} else {
  const boards = dv.pages('"原白板"').where(p => p.type === "whiteboard");
  if (boards.length === 0) {
    dv.paragraph("> 🌱 暂无原白板。Cmd+P → 搜「建/配置原白板」从零建第一个。");
  } else {
    // v4.3 用 plugin API 聚合（带缓存，<10ms）
    const boardStats = boards.array().map(board => {
      const stats = plugin.getMasteryBatch(board.file.name);
      const color = stats.avgMastery > 0.7 ? "🟢" : stats.avgMastery > 0.4 ? "🟡" : "🔴";
      return { board, ...stats, color };
    });

    boardStats.sort((a, b) => b.count - a.count);

    const container = dv.el("div", "");
    const table = container.createEl("table");
    const thead = table.createEl("thead");
    const headerRow = thead.createEl("tr");
    ["白板", "节点数", "平均掌握度", "状态", "操作"].forEach(h => {
      headerRow.createEl("th", { text: h });
    });
    const tbody = table.createEl("tbody");

    boardStats.forEach(s => {
      const row = tbody.createEl("tr");
      const nameCell = row.createEl("td");
      const link = nameCell.createEl("a", {
        text: s.board.file.name,
        cls: "internal-link",
      });
      link.onclick = (e) => {
        e.preventDefault();
        plugin.executeBoardCommand(s.board.file.name, "open-board");
      };

      row.createEl("td", { text: String(s.count) });
      row.createEl("td", { text: `${s.color} ${s.avgMastery.toFixed(2)}` });

      const statusText = s.count === 0
        ? "空白板（用 Cmd+Shift+D 派生节点）"
        : s.avgMastery > 0.7
          ? "✅ 掌握良好"
          : s.avgMastery > 0.4
            ? "📖 进行中"
            : "🚀 起步阶段";
      row.createEl("td", { text: statusText });

      const actionsCell = row.createEl("td");
      actionsCell.style.whiteSpace = "nowrap";

      const openBtn = actionsCell.createEl("button", { text: "📂" });
      openBtn.title = `打开 原白板/${s.board.file.name}.md`;
      openBtn.style.marginRight = "4px";
      openBtn.onclick = () => {
        plugin.executeBoardCommand(s.board.file.name, "open-board");
      };

      const examBtn = actionsCell.createEl("button", { text: "🚀 考察" });
      examBtn.title = "复制 /start-exam-board 命令 → 粘贴到 Claudian / Claude Code 执行（v1 检验白板，不走旧后端）";
      examBtn.style.marginRight = "4px";
      examBtn.disabled = s.count === 0;
      if (s.count === 0) {
        examBtn.style.opacity = "0.4";
        examBtn.style.cursor = "not-allowed";
      } else {
        examBtn.onclick = () => {
          plugin.executeBoardCommand(s.board.file.name, "exam-start");
        };
      }
    });

    // 全局刷新按钮
    const refreshDiv = container.createEl("div");
    refreshDiv.style.marginTop = "8px";
    const refreshBtn = refreshDiv.createEl("button", {
      text: "🔄 强制刷新缓存",
    });
    refreshBtn.title = "清空 plugin mastery 缓存，下次表格渲染重新聚合";
    refreshBtn.onclick = () => {
      plugin.invalidateMasteryCache();
      // 触发当前 dataview 块重新计算（用 dv.app.workspace.activeLeaf 重新刷新当前文件）
      const file = app.workspace.getActiveFile();
      if (file) {
        app.workspace.getActiveViewOfType(require("obsidian").MarkdownView)?.previewMode?.rerender(true);
      }
    };
  }
}
```

---

## 📚 节点池（按白板归属分组）

```dataviewjs
const nodes = dv.pages('"节点"').where(p => p.type === "concept");

if (nodes.length === 0) {
  dv.paragraph("> 🌱 节点池空。在某白板内 Cmd+Shift+D 派生第一个概念节点。");
} else {
  // 按 source_board 分组
  const groups = {};
  for (const n of nodes) {
    const sb = n.source_board;
    let boardName = "（无归属，需修复）";
    if (sb) {
      const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
      const m = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
      if (m) boardName = m[1].trim();
    }
    if (!groups[boardName]) groups[boardName] = [];
    groups[boardName].push(n);
  }

  for (const [boardName, ns] of Object.entries(groups)) {
    dv.header(4, `🗂️ ${boardName}（${ns.length} 节点）`);
    ns.sort((a, b) =>
      (a.mastery_score || 0.30) - (b.mastery_score || 0.30)
    );
    dv.list(ns.map(n => {
      const m = typeof n.mastery_score === "number" ? n.mastery_score : 0.30;
      const color = m > 0.7 ? "🟢" : m > 0.4 ? "🟡" : "🔴";
      return `${color} ${n.file.link} \`${m.toFixed(2)}\``;
    }));
  }
}
```

---

## 📋 待复盘错误候选（Story 2.5.X · D15 用户主权 C+）

> [!info]+ 这是什么？
> 你和 AI 对话时, 系统会**自动识别可能的误解**, 写入节点的 `error_candidates[]` 草稿区（**不直接进 errors[]**）。
> 你需要**主动确认**这些候选才会成为正式错题（方案 A · 2026-07-20 起单命令）：
> - **Cmd+P → "复盘错误候选"** → 选候选 → 选 ✅ 接受（移入 `errors[]` + 同步 Graphiti）或 ⚠️ 异议（写理由，不进 errors[]）
> - 在 Dashboard 页面直接跑也可以——没打开节点时命令会自动扫全库列出所有待复盘候选
> - 处理后节点正文里的候选卡片会自动变态（🔴 待复盘 → ✅ 已确认 / ⚠️ 已异议）
> - **30 天未处理** → 自动 expired 归档

```dataviewjs
// Story 2.5.X Task 6 — error_candidates[] 保活视图
const allNodes = dv.pages('"节点"')
  .where(p => Array.isArray(p.error_candidates) && p.error_candidates.length > 0);

let totalPending = 0;
let totalExpired = 0;
let totalAccepted = 0;
let totalDismissed = 0;
let totalDisputed = 0;
const pendingByNode = new Map();

for (const note of allNodes) {
  const cands = note.error_candidates || [];
  const pendingHere = [];
  for (const c of cands) {
    if (!c || typeof c !== "object") continue;
    const status = c.status || "pending";
    if (status === "pending") {
      totalPending++;
      pendingHere.push(c);
    } else if (status === "expired") totalExpired++;
    else if (status === "accepted") totalAccepted++;
    else if (status === "dismissed") totalDismissed++;
    else if (status === "disputed") totalDisputed++;
  }
  if (pendingHere.length > 0) {
    // 方案 A: 按钮需要真实路径打开节点, link 仅供显示
    pendingByNode.set(note.file.link, { cands: pendingHere, path: note.file.path });
  }
}

// 总览
dv.header(4, `📊 候选状态总览`);
dv.table(
  ["状态", "数量"],
  [
    ["⏳ pending（待复盘）", totalPending],
    ["✅ accepted", totalAccepted],
    ["✏️ edited", "—"],
    ["✗ dismissed (AI 误判)", totalDismissed],
    ["⚠️ disputed (有异议)", totalDisputed],
    ["🗄️ expired (30 天归档)", totalExpired],
  ]
);

if (totalExpired > 0) {
  dv.paragraph(`> [!warning]+ 已自动归档 ${totalExpired} 条 (>30 天未处理)`);
}

// pending 详细列表
if (totalPending === 0) {
  dv.paragraph("> ✅ 暂无待复盘的错误候选");
} else {
  dv.header(4, `⏳ 待复盘 ${totalPending} 条 (按节点分组)`);
  for (const [nodeLink, entry] of pendingByNode) {
    const cands = entry.cands;
    dv.header(5, `${nodeLink} (${cands.length} 条)`);
    // 方案 A (轨道 B 2026-07-20, 决策点 4): 每节点一颗处理按钮 —
    // 打开该节点 + 触发合并后的「复盘错误候选」命令
    const btn = dv.el("button", "🔍 复盘此节点候选");
    btn.onclick = async () => {
      await app.workspace.openLinkText(entry.path, "", false);
      setTimeout(() => {
        app.commands.executeCommandById(
          "canvas-learning-system:canvas:review-error-candidate"
        );
      }, 200);
    };
    const rows = cands.map(c => {
      const conf = typeof c.confidence === "number" ? c.confidence : 0.5;
      let icon = "🔴";  // <0.6 低置信
      if (conf >= 0.8) icon = "🟢";
      else if (conf >= 0.6) icon = "🟡";
      const desc = c.misconception || c.description || "(无描述)";
      const ptype = c.pedagogy_type || "—";
      const seen = c.seen_count || 1;
      const lastSeen = c.last_seen_at ? String(c.last_seen_at).slice(0, 10) : "—";
      return [icon, desc.slice(0, 80), ptype, conf.toFixed(2), seen, lastSeen];
    });
    dv.table(
      ["", "描述", "类型", "置信", "见过", "最后"],
      rows
    );
  }
  dv.paragraph(
    "💡 **如何处理**: 点上方「🔍 复盘此节点候选」按钮，或任意位置 `Cmd+P` 搜 \"复盘错误候选\"（自动全库扫描）"
  );
}

// 方案 A (轨道 B 2026-07-20, C2 观察 c): 已处理候选人类可读清单 —
// 处理后不再"只有 Notice 没有去向", 折叠列表随时可回看
const handled = [];
for (const page of allNodes) {
  for (const c of page.error_candidates) {
    if (["accepted", "edited", "disputed", "dismissed"].includes(c.status)) {
      handled.push({ node: page.file.link, c });
    }
  }
}
if (handled.length > 0) {
  dv.header(4, `✅ 已处理 ${handled.length} 条（点开回看）`);
  const stateIcon = { accepted: "✅ 已确认", edited: "✅ 已确认(改)", disputed: "⚠️ 已异议", dismissed: "🚫 已忽略" };
  dv.table(
    ["节点", "处理", "误解", "理由/时间"],
    handled.map(({ node, c }) => [
      node,
      stateIcon[c.status] || c.status,
      String(c.misconception || c.description || "").slice(0, 60),
      c.dispute_reason
        ? String(c.dispute_reason).slice(0, 30)
        : String(c.status_changed_at || "").slice(0, 10),
    ])
  );
}
```

---

## ⏰ 待复习（FSRS 到期）

> [!info]+ FSRS 调度已上线（FSRS-V2 2026-07-30）
> 每次 `/quiz-answer` 评分即一次 FSRS 复习，到期日写入节点 `fsrs_due`。
> 每日到期清单与一键开考命令见 **`outputs/今日复习.md`**（早 9:05 自动生成+推送）。
>
> **弱点视图**：列出所有 `mastery_score < 0.5` 的节点（掌握度维度，与到期互补）：

```dataviewjs
const weakNodes = dv.pages('"节点"')
  .where(p => p.type === "concept")
  .where(p => (typeof p.mastery_score === "number" ? p.mastery_score : 0.30) < 0.5);

if (weakNodes.length === 0) {
  dv.paragraph("> ✅ 所有节点 mastery ≥ 0.5，暂无弱项。");
} else {
  dv.header(4, `🚨 需要复习的弱项节点 (${weakNodes.length})`);
  const sorted = weakNodes.array().sort((a, b) =>
    (a.mastery_score || 0.30) - (b.mastery_score || 0.30)
  );
  dv.list(sorted.map(n => {
    const m = typeof n.mastery_score === "number" ? n.mastery_score : 0.30;
    const sb = n.source_board;
    let boardName = "（无归属）";
    if (sb) {
      const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
      const mt = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
      if (mt) boardName = mt[1].trim();
    }
    return `🔴 ${n.file.link} (${boardName}) \`mastery: ${m.toFixed(2)}\``;
  }));
}
```

---

## 🚀 一键考察

> [!tip]+ v1 检验白板范式（2026-07-13 更新，旧后端管道已退役）
> 「启动考察」不再调后端 `/api/v1/exam/start`——它把 `/start-exam-board` 命令**复制到剪贴板**，你切到 Claude Code 窗口粘贴执行（Claudian 侧栏亦可）。出题引用你的批注原话，答完 `/quiz-answer` 静默评分并演化掌握度。
>
> ## 触发方式（任选其一）
>
> 1. **上方表格 🚀 按钮** ⭐ 推荐：活跃原白板表格每行的「🚀 考察」→ 自动打开白板并复制 `/start-exam-board from <板名>`
> 2. **命令面板**：`Cmd+P` → 搜"启动考察" → Enter（在 `原白板/<板名>.md` 内触发会自动带 `from <板名>`）
> 3. **单节点定向**：打开 `节点/<概念>.md` → `Cmd+P` → 搜"Quick Exam" → 复制 `/start-exam-board from <板> node <节点>`（跳过薄弱选择，直考此节点）
>
> ## 行为
>
> - 触发后 Notice 显示已复制的完整命令 → 切 Claude Code 粘贴执行
> - 新检验白板生成在 `检验白板/<板名>-<时间戳>.md`（不是 outputs/）
> - 答题手写在 `<!-- answer:start/end -->` 区，填「理解自评」，然后 `/quiz-answer`

---

## 🗂️ 考察历史（读 检验白板/ frontmatter 汇总）

```dataviewjs
// T6 (2026-07-10) — 考察历史聚合: 扫 检验白板/ type=exam_board 的 frontmatter。
// HARD-SILENT 不破: 进行中场次只显示状态不显示分数; 完成场次才显示均分。
const boards = dv.pages('"检验白板"')
  .where(p => p.type === "exam_board")
  .sort(p => p.created_at, "desc");

if (boards.length === 0) {
  dv.paragraph("_还没有考察记录。用 `/start-exam-board` 开第一场。_");
} else {
  let done = 0, inProgress = 0;
  const rows = [];
  for (const b of boards) {
    const qs = Array.isArray(b.questions) ? b.questions : [];
    const scored = qs.filter(q => q && typeof q.score === "number");
    // P8 修复 (轨道 B 2026-07-20): /quiz-answer 实际写 status: done, 旧字面量
    // "completed" 永不命中 (靠全题已评兜底侥幸正确); scored_pending_node_update
    // 半态明确排除, 防评分中途被提前当完成显示均分 (HARD-SILENT)。
    const isDone = ["completed", "done"].includes(b.status)
      || (b.status !== "scored_pending_node_update" && qs.length > 0 && scored.length === qs.length);
    if (isDone) done++; else inProgress++;
    const scoreCell = isDone && scored.length > 0
      ? (scored.reduce((s, q) => s + q.score, 0) / scored.length).toFixed(1)
      : "—";
    rows.push([
      b.file.link,
      b.source_board ?? "—",
      b.status ?? "?",
      `${scored.length}/${qs.length}`,
      scoreCell,
      String(b.created_at ?? "").slice(0, 10),
    ]);
  }
  dv.paragraph(`**${boards.length}** 场考察 · ✅ 完成 ${done} · ⏳ 进行中 ${inProgress}`);
  dv.table(["检验白板", "来源白板", "状态", "已评/总题", "均分", "日期"], rows);
}
```

---

## 🛠️ Canvas 4 命令速查

| 场景 | 命令 | 触发 |
|---|---|---|
| 建新白板（无种子） | `canvas:configure-whiteboard` | Cmd+P 搜"建/配置原白板" |
| 建新白板 + 种子 | `canvas:configure-whiteboard` | 打开种子 md → 上面命令 |
| 笔记追加到已有白板 | `canvas:append-note-to-board` | 打开 md → Cmd+P 搜"把当前笔记追加" |
| 节点内派生子节点 | `canvas:ai-linked-doc` | 选中文字 → **Cmd+Shift+D** |
| 文字加 callout 批注 | `canvas:annotate-callout` | 选中文字 → **Cmd+Shift+A** |
| 启动考察 | `canvas:start-examination` | Cmd+P 搜"启动考察" |

---

## 📈 最近学习活动（按节点最后修改时间倒序，前 10 条）

> [!info]+ v1.2 修复 + 重设计
> v1.0 / v1.1 这里叫"学习历史"，列的是**白板创建时间**，价值低且 `localeCompare` 用在 DateTime 对象上 → TypeError。
> 现改为"**最近学习活动**"：列最近**改过 frontmatter / 加 callout / 派生节点**的节点（按 `file.mtime` 倒序），真实反映学习轨迹。

```dataviewjs
const plugin = app.plugins.plugins["canvas-learning-system"];
const nodes = dv.pages('"节点"').where(p => p.type === "concept");

if (nodes.length === 0) {
  dv.paragraph("> 🌱 节点池为空。Cmd+Shift+D 在白板内派生第一个节点。");
} else {
  // file.mtime 是 dataview 自动提供的 DateTime 对象，用 - 数值比较（不是 localeCompare）
  const sorted = nodes.array().sort((a, b) => {
    const ta = a.file.mtime?.ts ?? 0;
    const tb = b.file.mtime?.ts ?? 0;
    return tb - ta;
  });

  const top10 = sorted.slice(0, 10);

  dv.table(
    ["节点", "所属白板", "上次修改", "Mastery"],
    top10.map(n => {
      // 提取所属白板
      let boardName = "（无归属）";
      const sb = n.source_board;
      if (sb) {
        const path = typeof sb === "string" ? sb : (sb.path || sb.link || "");
        const m = path.match(/原白板\/([^\]|]+?)(?:\.md)?(?:\|[^\]]*)?(?:\]\])?$/);
        if (m) boardName = m[1].trim();
      }

      // 相对时间（"3 分钟前" / "2 小时前" / "昨天"）
      const now = Date.now();
      const ts = n.file.mtime?.ts ?? now;
      const diffMin = Math.round((now - ts) / 60000);
      let relTime;
      if (diffMin < 1) relTime = "刚刚";
      else if (diffMin < 60) relTime = `${diffMin} 分钟前`;
      else if (diffMin < 1440) relTime = `${Math.round(diffMin / 60)} 小时前`;
      else relTime = `${Math.round(diffMin / 1440)} 天前`;

      // mastery 颜色
      const m = typeof n.mastery_score === "number" ? n.mastery_score : 0.30;
      const color = m > 0.7 ? "🟢" : m > 0.4 ? "🟡" : "🔴";

      return [
        n.file.link,
        boardName,
        relTime,
        `${color} ${m.toFixed(2)}`,
      ];
    })
  );

  // 顶部统计
  const past24h = sorted.filter(n => {
    const ts = n.file.mtime?.ts ?? 0;
    return Date.now() - ts < 24 * 60 * 60 * 1000;
  }).length;
  dv.paragraph(`📊 过去 24 小时活跃节点: **${past24h}** / 总节点 ${nodes.length}`);
}
```

---

## 🔗 关键链接

- **本 Dashboard 源码**：`canvas-vault/Dashboard.md`
- **Story 1.18 spec**：`_bmad-output/implementation-artifacts/epic-1/1-18-dashboard-md-mvp.md`
- **Story 1.18 验收单**：`_bmad-output/验收单/Story-1.18-dashboard-mvp.md`
- **CLAUDE.md 速查**：`_bmad-output/.claude/CLAUDE.md`

---

> [!success]+ Dashboard v1.0 已 ship（2026-05-01）
> 4 MVP 闭环最后一环。所有数据自 vault frontmatter 实时聚合，零 LLM 调用，零外部依赖（无需 Buttons plugin）。FSRS 到期统计已于 2026-07-30 接活（FSRS-V2）。
