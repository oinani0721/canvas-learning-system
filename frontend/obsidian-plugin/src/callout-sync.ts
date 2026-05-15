/**
 * CalloutSyncDebouncer — Story 2.4 Plan B Phase 1 (2026-05-14)
 *
 * 监听 vault.on('modify') 事件，对每个 .md 文件做 500ms debounce 后批量同步
 * callout 到 backend。
 *
 * 解决问题：用户在 callout 内继续输入"我的理解"后，原 P0-1 一次性 POST 不会
 * 感知。本类填补这个 gap — vault 任何 .md 修改 → 500ms 静默 → parse 文件
 * 内所有 callout → SHA256 dedup → batch POST 到 backend。
 *
 * 设计原则：
 *   - 静默失败：debounce sync 失败不打扰用户（不像 P0-1 modal 同步有 Notice）
 *   - 范围限定：只处理 节点/ 和 原白板/ 下的 .md（不扫 验收单/ raw/ outputs/）
 *   - 幂等：backend 用 content_hash 去重，重复 sync 同一 hash 不会创建 v2 episode
 */
import type { TFile } from "obsidian";
import { parseCalloutsFromContent, type ParsedCallout } from "./callout";
import type CanvasLearningPlugin from "./main";

const DEBOUNCE_MS = 500;
const ALLOWED_PATH_PREFIXES = ["节点/", "原白板/"];

export class CalloutSyncDebouncer {
  private timers = new Map<string, ReturnType<typeof setTimeout>>();

  constructor(private plugin: CanvasLearningPlugin) {}

  /**
   * 调度文件同步：清掉前一个 timer，开新 500ms timer。
   * 用户连续编辑 → 反复 reset → 静默 500ms 后才真正 sync。
   */
  scheduleSync(file: TFile): void {
    if (!this.shouldHandle(file)) return;

    const existing = this.timers.get(file.path);
    if (existing) clearTimeout(existing);

    const timer = setTimeout(() => {
      this.timers.delete(file.path);
      void this.syncFile(file);
    }, DEBOUNCE_MS);
    this.timers.set(file.path, timer);
  }

  private shouldHandle(file: TFile): boolean {
    if (file.extension !== "md") return false;
    return ALLOWED_PATH_PREFIXES.some((p) => file.path.startsWith(p));
  }

  private async syncFile(file: TFile): Promise<void> {
    try {
      const content = await this.plugin.app.vault.read(file);
      const callouts = await parseCalloutsFromContent(content, file.basename);
      if (callouts.length === 0) return;
      await this.plugin.batchSyncCallouts(file.basename, callouts);
    } catch {
      // 静默失败：debounce sync 不应打扰用户。
      // 后续 backend file watcher 会兜底（Plan C 升级路径）。
    }
  }

  /** Plugin onunload 时清理所有挂起 timer */
  shutdown(): void {
    for (const timer of this.timers.values()) clearTimeout(timer);
    this.timers.clear();
  }
}

export type { ParsedCallout };
