import {
  type App,
  type Editor,
  FuzzySuggestModal,
  Notice,
  Plugin,
} from "obsidian";
import { CALLOUT_TYPES, type CalloutType, wrapSelection } from "./callout";

const BACKEND_URL = "http://localhost:8001";

/**
 * Canvas Learning System — Obsidian Plugin
 *
 * Story 1.4: Registers 6 core commands in Obsidian Hotkeys panel.
 * Story 1.5: Detects hotkey conflicts on plugin load.
 * Story 1.16: Adds 7th command `canvas:annotate-callout` — wrap selection as Obsidian callout.
 */
export default class CanvasLearningPlugin extends Plugin {
  async onload() {
    this.registerCanvasCommands();
    this.app.workspace.onLayoutReady(() => {
      this.checkHotkeyConflicts();
    });
  }

  /**
   * Story 1.4 AC #1: Register 6 commands in Obsidian's command palette.
   * All commands default to unbound — user binds in Settings > Hotkeys.
   */
  private registerCanvasCommands() {
    this.addCommand({
      id: "canvas:start-dialog",
      name: "启动学习对话",
      callback: () => this.callBackend("/api/v1/agents/dialog", "启动学习对话"),
    });

    this.addCommand({
      id: "canvas:start-examination",
      name: "启动考察",
      callback: () => this.callBackend("/api/v1/exam/start", "启动考察"),
    });

    this.addCommand({
      id: "canvas:extract-concept",
      name: "提取概念",
      callback: () => {
        const editor = this.app.workspace.activeEditor?.editor;
        const selected = editor?.getSelection();
        if (!selected) {
          new Notice("请先选中文本再提取概念");
          return;
        }
        this.callBackend("/api/v1/wikilink/build", "提取概念", { text: selected });
      },
    });

    this.addCommand({
      id: "canvas:quiz-from-callout",
      name: "批注考察",
      callback: () => this.callBackend("/api/v1/exam/start", "批注考察"),
    });

    this.addCommand({
      id: "canvas:open-dashboard",
      name: "打开仪表盘",
      callback: () => this.callBackend("/api/v1/system/health", "打开仪表盘"),
    });

    this.addCommand({
      id: "canvas:open-review-queue",
      name: "打开复习队列",
      callback: () => this.callBackend("/api/v1/review/queue", "打开复习队列"),
    });

    this.addCommand({
      id: "canvas:annotate-callout",
      name: "批注为标注",
      callback: () => this.handleAnnotateCallout(),
    });
  }

  /**
   * Story 1.16: Prompt for callout type and wrap the current selection.
   */
  private handleAnnotateCallout() {
    const editor = this.app.workspace.activeEditor?.editor;
    if (!editor) {
      new Notice("编辑器未激活");
      return;
    }
    const selected = editor.getSelection();
    if (!selected) {
      new Notice("请先选中文本再批注", 3000);
      return;
    }
    new CalloutTypeModal(this.app, editor, selected).open();
  }

  /**
   * Story 1.5 AC #1-5: Detect hotkey conflicts among Canvas commands.
   */
  private checkHotkeyConflicts() {
    const hotkeyManager = (this.app as any).hotkeyManager;
    if (!hotkeyManager?.customKeys) return;

    const canvasBindings = new Map<string, string[]>();

    for (const [commandId, hotkeys] of Object.entries(hotkeyManager.customKeys)) {
      if (!commandId.startsWith("canvas-learning-system:canvas:")) continue;
      if (!Array.isArray(hotkeys)) continue;

      for (const hk of hotkeys as any[]) {
        if (!hk.modifiers || !hk.key) continue;
        // AC #4: Normalize modifier order for consistent comparison
        const canonical = [...hk.modifiers].sort().join("+") + "+" + hk.key;
        const existing = canvasBindings.get(canonical) || [];
        existing.push(commandId.replace("canvas-learning-system:", ""));
        canvasBindings.set(canonical, existing);
      }
    }

    const conflicts: string[] = [];
    for (const [key, commands] of canvasBindings) {
      if (commands.length > 1) {
        const names = commands
          .map((c) => this.app.commands.findCommand(c)?.name || c)
          .join("' 和 '");
        conflicts.push(`${key} 同时绑定了 '${names}'`);
      }
    }

    if (conflicts.length > 0) {
      new Notice(`Canvas 快捷键冲突:\n${conflicts.join("\n")}`, 8000);
    }
  }

  /**
   * Story 1.4 AC #4: Backend unavailable → friendly error.
   */
  private async callBackend(endpoint: string, label: string, body?: any) {
    try {
      const resp = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: body ? "POST" : "GET",
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!resp.ok) {
        new Notice(`${label} 失败: HTTP ${resp.status}`, 5000);
      }
    } catch {
      new Notice("后端未连接，请先启动 Canvas 后端", 5000);
    }
  }
}

class CalloutTypeModal extends FuzzySuggestModal<CalloutType> {
  constructor(
    app: App,
    private editor: Editor,
    private selected: string,
  ) {
    super(app);
    this.setPlaceholder("选择标注类型");
  }

  getItems(): CalloutType[] {
    return [...CALLOUT_TYPES];
  }

  getItemText(item: CalloutType): string {
    return item;
  }

  onChooseItem(item: CalloutType) {
    this.editor.replaceSelection(wrapSelection(this.selected, item));
  }
}
