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

## 🔗 节点关系图（v2.7 · 白板核心 · 自动从真实双链生成）

```dataviewjs
const here = dv.current().file.link;
const nodes = dv.pages('"节点"')
  .where(p => p.source_board?.path === here.path);

if (nodes.length === 0) {
  dv.paragraph("> 🌱 当前白板暂无派生节点，用 Cmd+Shift+D 派生第一个");
} else {
  let chart = "graph TD\n";
  const declared = new Set();
  nodes.forEach(n => {
    const id = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
    if (!declared.has(id)) {
      const mastery = n.mastery_score ?? '—';
      chart += `  ${id}["${n.file.name}<br/>精通度 ${mastery}"]\n`;
      chart += `  style ${id} fill:#fff3e0,stroke:#f57c00\n`;
      declared.add(id);
    }
    if (n["derived-from"]) {
      const srcName = n["derived-from"].fileName ? n["derived-from"].fileName() : n["derived-from"].path.split('/').pop().replace('.md','');
      const srcId = srcName.replace(/[^a-zA-Z0-9_]/g, "_");
      if (!declared.has(srcId)) {
        chart += `  ${srcId}["${srcName}<br/>(源笔记)"]\n`;
        chart += `  style ${srcId} fill:#e1f5ff,stroke:#0288d1\n`;
        declared.add(srcId);
      }
    }
  });
  nodes.forEach(n => {
    if (n["derived-from"]) {
      const srcName = n["derived-from"].fileName ? n["derived-from"].fileName() : n["derived-from"].path.split('/').pop().replace('.md','');
      const src = srcName.replace(/[^a-zA-Z0-9_]/g, "_");
      const dst = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
      chart += `  ${src} -->|派生| ${dst}\n`;
    }
    (n.file.outlinks || []).forEach(link => {
      const target = nodes.find(p => p.file.path === link.path);
      if (target && target.file.name !== n.file.name) {
        const src = n.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
        const dst = target.file.name.replace(/[^a-zA-Z0-9_]/g, "_");
        chart += `  ${src} -.->|wikilink| ${dst}\n`;
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
