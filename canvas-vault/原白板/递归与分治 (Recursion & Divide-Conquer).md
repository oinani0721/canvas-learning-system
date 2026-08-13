---
type: whiteboard
board_name: "递归与分治 (Recursion & Divide-Conquer)"
created_at: "2026-04-30T09:10:17Z"
doc_count: 0
doc_mastery_avg: 0.00
---

# 递归与分治 (Recursion & Divide-Conquer)

> [!info]+ 原白板说明（扁平架构 · round-11）
> 这是学习主题"**递归与分治 (Recursion & Divide-Conquer)**"的原白板。本文档即白板本身（不是白板目录的索引）。
>
> - **节点 md** 都在 vault 根的 `节点/` 文件夹（扁平池，一 vault 一学科零重名）
> - **subject** 字段读 vault 级 `.canvas-config.yaml`（不在每个 md frontmatter 重复）
> - 左栏文件树默认**折叠节点文件夹**，你主要从这份白板 md 入口管理
> - Cmd+Click `[[wikilink]]` 仍可跳转到节点 md（节点级 AI 对话继续工作）
>
> ## 你在这白板里能做什么
> - 选中任意文本 → `Cmd+Shift+D` 让 AI 派生新节点（Story 1.17），**自动建双向 wikilink**
> - 选中文本 → `Cmd+Shift+A` 加 Tips/错误/提问/关键点 callout + 3 态理解度 checkbox
> - 按 `Cmd+G` 打开 Graph View 看本白板所有 wikilink 拓扑
> - 按 `Cmd+E` 切 Reading View 看渲染后 callout

## Concepts

- [[节点/my-recursion-notes]] — seed note (mastery: 0.30)

<!--
本 section 由三处维护：
  1. /configure-whiteboard Skill（Story 1.19）— 种子笔记 append 时写 "seed note (mastery: 0.30)"
  2. /ai-linked-doc Skill（Story 1.17）— AI 派生新节点时 append "extracted, weak (0.30)"
  3. 你手动 — 直接写 `- [[xxx]]` 都会被 Graph View 识别
wikilink 目标都指向 vault 根的 节点/ 文件夹下 md。
-->

## 🔗 节点关系图（v2.8 · 白板核心 · 自动从真实双链生成）

```dataviewjs
const here = dv.current().file.link;
const strip = (s) => s ? s.replace(/\.md$/, "") : s;
const nodes = dv.pages('"节点"')
  .where(p => strip(p.source_board?.path) === strip(here.path));

// ⛔ v2.8 掌握度四态回退 — 权威口径 = .claude/scripts/sync_board_concepts.py 与
//    backend _normalize_mastery（beta 状态量 → 显式分 → 旧版字段 → 缺失）。
//    禁改回单字段 mastery_score：v2.7 的老毛病 —— legacy 节点显「—」、
//    占位节点照标 0.3，与上方 Concepts 目录同屏打架。
const num = (x) => { const v = Number(x); return Number.isFinite(v) ? v : null; };
const masteryOf = (p) => {
  const a = num(p.mastery_a), b = num(p.mastery_b), s = num(p.mastery_score);
  if (a !== null && b !== null) return (a > 0 && b > 0) ? (s !== null ? s : a / (a + b)) : null;
  if (s !== null) return s;
  const legacy = num(p.mastery);
  return legacy !== null ? legacy : num(p.mastery_level);
};
const STUB = "你的 1-2 句精准定义";
const bodies = {};
for (const p of nodes.array()) bodies[p.file.path] = await dv.io.load(p.file.path);
const statusOf = (p) => {
  if ((bodies[p.file.path] || "").includes(STUB)) return "待剖析占位";
  const m = masteryOf(p);
  const g = m === null ? "掌握度 —" : "掌握度 " + m.toFixed(2);
  const n = num(p.attempt_count);
  return g + " · " + (n !== null && n > 0 ? "已考 " + n + " 次" : "未考");
};
const srcNameOf = (l) => l.fileName ? l.fileName() : String(l.path || l).split('/').pop().replace('.md','');

if (nodes.length === 0) {
  dv.paragraph("> 🌱 当前白板暂无派生节点，用 Cmd+Shift+D 派生第一个");
} else {
  // ⛔ v2.8 稳定序号 id — v2.7 的 replace(/[^a-zA-Z0-9_]/g,"_") 把中文名打成
  //    下划线串，同形中文名会 id 碰撞、两个节点被画成一个。
  const ids = new Map();
  const idOf = (name) => { if (!ids.has(name)) ids.set(name, "n" + ids.size); return ids.get(name); };
  let chart = "graph TD\n";
  const declared = new Set();
  nodes.forEach(n => {
    const id = idOf(n.file.name);
    if (!declared.has(id)) {
      chart += `  ${id}["${n.file.name}<br/>${statusOf(n)}"]\n`;
      chart += `  style ${id} fill:#fff3e0,stroke:#f57c00\n`;
      declared.add(id);
    }
    if (n["derived-from"]) {
      const srcName = srcNameOf(n["derived-from"]);
      const srcId = idOf(srcName);
      if (!declared.has(srcId)) {
        chart += `  ${srcId}["${srcName}<br/>(源笔记)"]\n`;
        chart += `  style ${srcId} fill:#e1f5ff,stroke:#0288d1\n`;
        declared.add(srcId);
      }
    }
  });
  nodes.forEach(n => {
    if (n["derived-from"]) {
      chart += `  ${idOf(srcNameOf(n["derived-from"]))} -->|派生| ${idOf(n.file.name)}\n`;
    }
  });
  nodes.forEach(n => {
    (n.file.outlinks || []).forEach(link => {
      const target = nodes.find(p => p.file.path === link.path);
      if (target && target.file.name !== n.file.name) {
        chart += `  ${idOf(n.file.name)} -.->|wikilink| ${idOf(target.file.name)}\n`;
      }
    });
  });
  dv.paragraph("```mermaid\n" + chart + "```");
}
```

> **白板 = 节点关系**（社区共识：5 大思想领袖 + 5 真实成熟项目均零分类容器段）。Cmd+G 看 Graph View 全 vault 拓扑。

## Recent Activity

- 2026-04-30T09:10:17Z: Whiteboard created
- 2026-04-30T09:10:17Z: Seed note my-recursion-notes imported
