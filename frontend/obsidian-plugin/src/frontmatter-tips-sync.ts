/**
 * FrontmatterTipsSync — Story 2.4 Plan A (2026-05-14)
 *
 * 监听 metadataCache 文件元数据变化，解析 callout → 写入 frontmatter tips[]
 * 数组。Obsidian 官方 app.fileManager.processFrontMatter API 原子写入。
 *
 * 核心设计（按 Story 2.4 spec + ChatGPT 5-14 对抗审查盲点修复）：
 *   1. metadataCache.on('changed') 而非 vault.on('modify') — Obsidian 内部
 *      已 throttle + 不会跟我们写 frontmatter 形成无限循环
 *   2. 完全覆盖 tips[] — 不 append, 不 dedupe — 自然支持删除（spec AC#5）
 *   3. 比对新旧内容相同则跳过 — 防止 frontmatter 写入触发新一轮 changed
 *   4. added_at 保留 — 匹配的旧 tip 沿用其 added_at, 新 tip 写当前时间
 *   5. parser 兼容 [!tip]+/- 单复数 — Story 2.4 spec AC#3 + #1 协议要求
 *
 * 与 Plan B（DEPRECATED）的区别：
 *   - 不调 backend POST — 完全本地
 *   - 不依赖 Graphiti / Gemini / Neo4j
 *   - 真相源 = file frontmatter（非 Graphiti EpisodicNode）
 *   - 离线 100% 安全（文件本身就是数据）
 *   - 删除天然支持
 *
 * 见 _bmad-output/research/2026-05-14-plan-b-postmortem.md
 */
import type { TFile } from "obsidian";
import { parseCalloutsFromContent, type ParsedCallout } from "./callout";
import type CanvasLearningPlugin from "./main";

const ALLOWED_PATH_PREFIXES = ["节点/", "原白板/"];

interface FrontmatterTip {
  text: string;
  tag: string;
  understanding: string;
  added_at: string;
  source: string;
}

export class FrontmatterTipsSync {
  constructor(private plugin: CanvasLearningPlugin) {}

  /** Called from metadataCache.on('changed') */
  async syncFile(file: TFile): Promise<void> {
    if (!this.shouldHandle(file)) return;

    try {
      const content = await this.plugin.app.vault.read(file);
      const callouts = await parseCalloutsFromContent(
        content,
        file.basename,
      );

      await this.plugin.app.fileManager.processFrontMatter(
        file,
        (fm: Record<string, unknown>) => {
          const oldTips = (fm.tips as FrontmatterTip[]) || [];
          const newTips = this.buildNewTips(callouts, oldTips);

          // 防无限循环 + 不必要写入：相同内容跳过
          if (this.tipsEqual(oldTips, newTips)) return;

          // spec AC#5: 完全覆盖 — 旧 tip 被删的 callout 自然消失
          if (newTips.length === 0) {
            // 用户删光了所有 callout — 移除 tips 字段
            delete fm.tips;
          } else {
            fm.tips = newTips;
          }
        },
      );
    } catch {
      // 静默 — frontmatter 写入失败不应打扰用户（文件本身仍有 callout）
    }
  }

  private shouldHandle(file: TFile): boolean {
    if (file.extension !== "md") return false;
    return ALLOWED_PATH_PREFIXES.some((p) => file.path.startsWith(p));
  }

  /**
   * 用新 callouts 构建 tips[], 保留旧 tip 的 added_at（基于 text+tag+understanding 匹配）。
   * 这样用户编辑 callout 内容不会破坏 added_at 时序记录。
   */
  private buildNewTips(
    callouts: ParsedCallout[],
    oldTips: FrontmatterTip[],
  ): FrontmatterTip[] {
    const now = new Date().toISOString();
    return callouts.map((c) => {
      const matched = oldTips.find(
        (t) =>
          t.text === c.content &&
          t.tag === c.tag &&
          t.understanding === c.understanding,
      );
      return {
        text: c.content,
        tag: c.tag,
        understanding: c.understanding,
        added_at: matched?.added_at || now,
        source: "callout_parse",
      };
    });
  }

  private tipsEqual(a: FrontmatterTip[], b: FrontmatterTip[]): boolean {
    if (a.length !== b.length) return false;
    return a.every(
      (t, i) =>
        t.text === b[i].text &&
        t.tag === b[i].tag &&
        t.understanding === b[i].understanding,
    );
  }
}
