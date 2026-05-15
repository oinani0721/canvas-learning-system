/**
 * MVP-α-5 (2026-05-14) — Plugin 反馈 toast + 状态栏.
 *
 * 用户初衷 (来自 _bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md §1):
 *   用户 10 分钟体验 MVP-α 时需要 5 个反馈瞬间, 让 "AI 看到我做的" 这件事可感.
 *   本模块负责其中的 2 个非 backend-dependent 瞬间:
 *     · 瞬间 #2 — Tips 数自增 (status bar 数字跃迁 + 短 Notice)
 *     · 瞬间 #3 — 导航路径 (status bar 显示 "递归 → factorial")
 *
 * 真相源 (复用 Story 2.4 Plan A):
 *   FrontmatterTipsSync 已经把 callout 同步到 frontmatter.tips[] 数组,
 *   本模块直接读 metadataCache.getFileCache(file).frontmatter.tips 长度,
 *   不再重新 parse callout — 单一数据流, 无重复.
 *
 * 设计原则 (复用 vault-indicator.ts 模式):
 *   - pure functions 不依赖 Obsidian runtime, node:test 可直接 import
 *   - StatusBarController 类持有 plugin + HTMLElement, 仅在 main.ts 实例化
 *   - Notice 触发用 callback 注入 (避免本模块顶部 import Notice 拖入 Obsidian
 *     runtime 到 test bundle, 跟 vault-indicator 一样保持纯净)
 */

import type { App, TFile } from "obsidian";

// ─────────────────────────────────────────────────────────────
// Pure functions (testable, no Obsidian runtime)
// ─────────────────────────────────────────────────────────────

/**
 * 从 frontmatter 提取 tips[] 数量.
 *
 * Story 2.4 FrontmatterTipsSync 写入约定:
 *   - 有 callout: fm.tips = FrontmatterTip[] (数组)
 *   - 无 callout: fm.tips 字段被 delete
 *
 * 防御性: 字段缺失 / 类型异常 (非数组) → 返回 0.
 */
export function countTipsFromFrontmatter(
  fm: Record<string, unknown> | null | undefined,
): number {
  if (!fm) return 0;
  const tips = fm.tips;
  if (!Array.isArray(tips)) return 0;
  return tips.length;
}

/**
 * 构造导航路径文字 "递归 → factorial".
 *
 * - prev 为空 (第一次打开) → 只返回 current
 * - prev === current (重复打开同一文件) → 只返回 current, 不冗余箭头
 * - 两端 trim, 防 frontmatter 误注空白
 * - current 为空 → 返回 "" (调用方决定如何兜底)
 */
export function buildNavPath(
  current: string,
  prev?: string | null,
): string {
  const cur = (current ?? "").trim();
  if (!cur) return "";
  const p = (prev ?? "").trim();
  if (!p || p === cur) return cur;
  return `${p} → ${cur}`;
}

/**
 * 构造 status bar 文本 (Tips 计数 + 导航路径).
 *
 * 格式:
 *   - 有 navPath: "📝 Tips: 2 · 📍 递归 → factorial"
 *   - 无 navPath: "📝 Tips: 0"
 *
 * 设计:
 *   - tips 段始终显示 (即使 N=0, 让用户看到从 0 → 1 的跃迁)
 *   - " · " 分隔, 风格与 vault-indicator.buildStatusBarLabel 一致
 *   - emoji 前缀让 status bar 即使被其他插件挤压也能瞥见
 */
export function buildStatusBarText(input: {
  tipsCount: number;
  navPath: string;
}): string {
  const tipsSeg = `📝 Tips: ${input.tipsCount}`;
  const pathSeg = input.navPath ? `📍 ${input.navPath}` : "";
  return pathSeg ? `${tipsSeg} · ${pathSeg}` : tipsSeg;
}

/**
 * 判断 tips 计数变化方向, 用于决定是否触发 Notice 反馈瞬间.
 *
 *   - "init":     prev === undefined (首次填充) → 不触发, 避免初始化噪音
 *   - "increase": new > prev → 用户新写了 callout → 触发 Notice "🎓 已记住 N 条"
 *   - "decrease": new < prev → 用户删了 callout → 不触发 (静默, 避免负面感觉)
 *   - "same":     不变 → 不触发
 */
export type TipsCountTransition = "init" | "increase" | "decrease" | "same";

export function classifyTipsTransition(
  prev: number | undefined,
  next: number,
): TipsCountTransition {
  if (prev === undefined) return "init";
  if (next > prev) return "increase";
  if (next < prev) return "decrease";
  return "same";
}

/**
 * 路径是否在 status bar 的 nav path 追踪范围 (节点/ 或 原白板/).
 *
 * 其他文件 (Dashboard.md / templates/ / 验收单/ / raw/) 不入 path —
 * 用户切到 Dashboard 后再切回学习节点, status bar 应继续显示学习路径,
 * 不要让 Dashboard 这种功能性文件污染 "递归 → factorial" 故事感.
 */
export function shouldTrackInNavPath(path: string): boolean {
  return path.startsWith("节点/") || path.startsWith("原白板/");
}

/**
 * 构造 Tips 自增 Notice 文案.
 *
 * pure function 单独 export 让 main.ts wiring 和测试用同一份文案,
 * 避免 hard-coded 字符串在两处分叉.
 */
export function buildTipsIncreaseNotice(count: number): string {
  return `🎓 已记住 ${count} 条 Tips`;
}

// ─────────────────────────────────────────────────────────────
// StatusBarController (thin wiring, depends on Obsidian runtime)
// ─────────────────────────────────────────────────────────────

/**
 * 主 plugin 暴露给 StatusBarController 用的最小接口.
 *
 * 用 structural interface 而非 import CanvasLearningPlugin 避免 cycle:
 *   main.ts → status-bar.ts → main.ts 会让 esbuild 抱怨。
 */
export interface StatusBarPluginAPI {
  app: App;
}

/**
 * StatusBarController — 持有 HTMLElement, 维护 tips 计数 + 导航路径状态.
 *
 * 由 main.ts onload 实例化:
 *
 *   const el = this.addStatusBarItem();
 *   this.statusBar = new StatusBarController(this, el, {
 *     onTipsIncreased: (count) => new Notice(buildTipsIncreaseNotice(count), 2500),
 *   });
 *   this.registerEvent(
 *     this.app.metadataCache.on('changed', (f) => this.statusBar.handleMetadataChanged(f as TFile))
 *   );
 *   this.registerEvent(
 *     this.app.workspace.on('file-open', (f) => this.statusBar.handleFileOpen(f))
 *   );
 *
 * 设计:
 *   - 不直接 registerEvent (DI 让 main.ts 注册) — 关注点分离 + 单测容易 mock
 *   - 持有 currentFile + prevFile + lastTipsCount 三态
 *   - render() 仅 element.setText, 不重建 DOM
 *   - Notice 触发用 onTipsIncreased 回调注入 (不在本模块顶部 import Notice)
 */
export class StatusBarController {
  private currentFile: TFile | null = null;
  private prevFile: TFile | null = null;
  private lastTipsCount: number | undefined = undefined;

  constructor(
    private plugin: StatusBarPluginAPI,
    private element: HTMLElement,
    private opts: {
      onTipsIncreased?: (count: number) => void;
    } = {},
  ) {
    this.render();
  }

  /**
   * metadataCache.on('changed') 触发: file frontmatter 已重新解析.
   *
   * 仅当此 file 是当前 active file 时更新 (避免后台 sync 噪音).
   * 计数 increase 时触发 onTipsIncreased 回调 (Notice 反馈瞬间 #2).
   */
  handleMetadataChanged(file: TFile): void {
    if (!this.currentFile || file.path !== this.currentFile.path) return;
    const count = this.readTipsCount(file);
    const transition = classifyTipsTransition(this.lastTipsCount, count);
    this.lastTipsCount = count;
    this.render();
    if (transition === "increase" && this.opts.onTipsIncreased) {
      this.opts.onTipsIncreased(count);
    }
  }

  /**
   * workspace.on('file-open') 触发: 更新 prev → current.
   *
   * - file 为 null (用户关闭所有文件) → 清空 currentFile, 保留 prev (历史路径)
   * - 不在 shouldTrackInNavPath 范围 → 不更新 (Dashboard 等不污染 path)
   * - 重复打开同一文件 → 不更新 prev (避免 "factorial → factorial")
   */
  handleFileOpen(file: TFile | null): void {
    if (!file) {
      this.currentFile = null;
      this.lastTipsCount = undefined;
      this.render();
      return;
    }
    if (!shouldTrackInNavPath(file.path)) {
      return;
    }
    if (this.currentFile && this.currentFile.path !== file.path) {
      this.prevFile = this.currentFile;
    }
    this.currentFile = file;
    this.lastTipsCount = this.readTipsCount(file);
    this.render();
  }

  /**
   * 暴露给 main.ts 在 backend 阶段切换时手动追加 status bar 提示 (α-3 用).
   *
   * 比如 "正在生成题目..." / "评分完成" 阶段, main.ts 可调
   * statusBar.setTransientHint("⏳ 出题中") 让用户瞥见阶段, render() 再把它清掉.
   *
   * 当前留 stub, α-3 落地时再补 lifecycle (timer / explicit clear).
   */
  setTransientHint(_hint: string | null): void {
    // α-3 落地时 wire up
  }

  // ─── private ───

  private readTipsCount(file: TFile): number {
    const fm = this.plugin.app.metadataCache.getFileCache(file)?.frontmatter;
    return countTipsFromFrontmatter(fm);
  }

  private render(): void {
    const navPath = this.currentFile
      ? buildNavPath(this.currentFile.basename, this.prevFile?.basename)
      : "";
    const text = buildStatusBarText({
      tipsCount: this.lastTipsCount ?? 0,
      navPath,
    });
    this.element.setText(text);
  }
}
