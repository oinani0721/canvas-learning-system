// 批次4' 3-1/3-2 (MEM-FLYWHEEL): 派生时刻理解快照 + node_derived 事件锁定。
// UAT 实操抓到的断点: plugin 直连路径 (Cmd+Shift+D) 此前不写 derived_at/
// 快照字段、不落事件 — 只升级了 SKILL 路径。本套件锁 plugin 侧契约。
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  buildNodeDerivedEventLine,
  buildNodeFrontmatter,
  extractNearbyConfusion,
} from "../src/node-derivation";

test("buildNodeFrontmatter: relationships[0] 必含 derived_at", () => {
  const fm = buildNodeFrontmatter({
    sourceNoteStem: "lecture 2",
    activeBoard: "CS188 lecture 2",
    relationKey: "extends",
    description: "因为我不理解",
    createdAt: "2026-07-23T14:30:43.501Z",
  });
  assert.equal(fm.relationships[0].derived_at, "2026-07-23T14:30:43.501Z");
  assert.equal(fm.relationships[0].description, "因为我不理解");
});

test("buildNodeFrontmatter: 源节点有掌握度时写快照, 无则缺省", () => {
  const withMastery = buildNodeFrontmatter({
    sourceNoteStem: "s",
    activeBoard: "b",
    relationKey: "extends",
    description: "",
    createdAt: "2026-07-23T00:00:00Z",
    sourceMastery: 0.42,
  });
  assert.equal(withMastery.relationships[0].source_mastery_at_derivation, 0.42);
  const without = buildNodeFrontmatter({
    sourceNoteStem: "s",
    activeBoard: "b",
    relationKey: "extends",
    description: "",
    createdAt: "2026-07-23T00:00:00Z",
    sourceMastery: null,
  });
  assert.equal(
    without.relationships[0].source_mastery_at_derivation,
    undefined,
  );
});

test("buildNodeFrontmatter: confusion 截断 300 字并 trim", () => {
  const fm = buildNodeFrontmatter({
    sourceNoteStem: "s",
    activeBoard: "b",
    relationKey: "extends",
    description: "",
    createdAt: "2026-07-23T00:00:00Z",
    confusion: "  为什么反射代理不能规划  ",
  });
  assert.equal(fm.relationships[0].confusion, "为什么反射代理不能规划");
});

test("extractNearbyConfusion: 命中选区前后 10 行内最近的批注", () => {
  const content = [
    "# lecture 2",
    "> [!question]+ 反射代理为什么不够用？",
    "一些正文",
    "反射代理的局限性引出了规划代理的需求",
    "更多正文",
  ].join("\n");
  const out = extractNearbyConfusion(
    content,
    "反射代理的局限性引出了规划代理的需求",
  );
  assert.equal(out, "反射代理为什么不够用？");
});

test("extractNearbyConfusion: inline 空时取 callout 下一行正文", () => {
  const content = [
    "选中的目标行",
    "> [!error]+",
    "> 我把 minimax 和 expectimax 搞混了",
  ].join("\n");
  assert.equal(
    extractNearbyConfusion(content, "选中的目标行"),
    "我把 minimax 和 expectimax 搞混了",
  );
});

test("extractNearbyConfusion: 附近无批注 / 选区不在文中 → null", () => {
  assert.equal(extractNearbyConfusion("纯正文没有批注\n选中行", "选中行"), null);
  assert.equal(extractNearbyConfusion("完全无关内容", "找不到的选区"), null);
});

test("buildNodeDerivedEventLine: schema 与 backend 事件日志对齐", () => {
  const { eventId, line } = buildNodeDerivedEventLine(
    "规划代理",
    "2026-07-23T14:30:43.501Z",
  );
  assert.equal(eventId, "derive:规划代理");
  const rec = JSON.parse(line);
  assert.equal(rec.event_type, "node_derived");
  assert.equal(rec.event_version, 1);
  assert.equal(rec.node_id, "规划代理");
  assert.equal(rec.recorded_at, rec.effective_at);
  assert.ok(line.endsWith("\n"));
});
