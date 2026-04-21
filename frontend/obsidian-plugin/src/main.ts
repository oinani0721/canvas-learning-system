import {
  type App,
  type Editor,
  FuzzySuggestModal,
  Notice,
  Plugin,
} from "obsidian";
import {
  TAG_OPTIONS,
  type TagOption,
  UNDERSTANDING_OPTIONS,
  type UnderstandingOption,
  wrapSelection,
} from "./callout";
import {
  buildAIDocPrompt,
  extractBoardNameFromPath,
  isFlatArchPath,
} from "./ai-linked-doc";

const BACKEND_URL = "http://localhost:8001";

/**
 * Canvas Learning System — Obsidian Plugin
 *
 * Story 1.4: Registers 6 core commands in Obsidian Hotkeys panel.
 * Story 1.5: Detects hotkey conflicts on plugin load.
 * Story 1.16: Adds 7th command `canvas:annotate-callout` — select text, pick Tag + UnderstandingLevel,
 *             wrap as semantic callout with 3-state checkbox (Round 3 QA 2026-04-14 alignment).
 * Story 1.17: Adds 8th command `canvas:ai-linked-doc` — copy selection + prompt to clipboard,
 *             open Claudian sidebar to trigger `/ai-linked-doc` Skill (Mode D subscription usage).
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

    this.addCommand({
      id: "canvas:ai-linked-doc",
      name: "AI 创建双链文档",
      callback: () => this.handleAILinkedDoc(),
    });
  }

  /**
   * Story 1.17 v2.1: Copy selection + Skill-invoke prompt to clipboard, open Claudian sidebar.
   * Guidance Notice tells user to type /ai-linked-doc + paste. AI generation / file i/o /
   * wikilink replacement / index.md update is handled by the Claudian Skill
   * `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`, running in Claude Code CLI
   * with the user's subscription (Mode D, architecture.md:113).
   */
  private async handleAILinkedDoc() {
    console.log("[canvas:ai-linked-doc] triggered");
    const editor = this.app.workspace.activeEditor?.editor;
    if (!editor) {
      new Notice(
        "编辑器未激活：请在 Markdown 笔记正文内点一下让光标进入 Edit View，再按快捷键",
        5000,
      );
      return;
    }
    const selected = editor.getSelection();
    if (!selected) {
      new Notice("请先选中文本再创建双链", 3000);
      return;
    }

    const activeFile = this.app.workspace.getActiveFile();
    const sourcePath = activeFile?.path ?? "unknown";

    const activeBoard = extractBoardNameFromPath(sourcePath) ?? undefined;

    if (!isFlatArchPath(sourcePath) && sourcePath !== "unknown") {
      new Notice(
        `当前笔记 ${sourcePath} 不在 原白板/ 或 节点/ 路径下。Skill 会读 .canvas-config.yaml 或 AskUserQuestion 问你归属哪个原白板。`,
        7000,
      );
    }

    const prompt = buildAIDocPrompt(selected, sourcePath, activeBoard);

    try {
      await navigator.clipboard.writeText(prompt);
    } catch {
      new Notice("剪贴板写入失败，请检查 Obsidian 权限", 5000);
      return;
    }

    const claudianCmd = (this.app as any).commands.findCommand?.(
      "claudian:open-view",
    );
    if (!claudianCmd) {
      new Notice(
        "未检测到 Claudian 插件，请先安装并登录 Claude Code",
        5000,
      );
      return;
    }

    new Notice(
      "已复制到剪贴板。切到 Claudian 侧栏 → 输入框 Cmd+V 粘贴 → 回车。首行是 /ai-linked-doc 会触发 Skill。",
      8000,
    );
    (this.app as any).commands.executeCommandById("claudian:open-view");
  }

  /**
   * Story 1.16: Two-step modal — pick Tag (4 semantic) then UnderstandingLevel (3 states).
   * Wraps the selection as a callout with the chosen Tag and 3-state checkbox.
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
    new TagTypeModal(this.app, editor, selected).open();
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

class TagTypeModal extends FuzzySuggestModal<TagOption> {
  constructor(
    app: App,
    private editor: Editor,
    private selected: string,
  ) {
    super(app);
    this.setPlaceholder("第 1/2 步：选标签类型");
  }

  getItems(): TagOption[] {
    return [...TAG_OPTIONS];
  }

  getItemText(item: TagOption): string {
    return item.label;
  }

  onChooseItem(tag: TagOption) {
    setTimeout(() => {
      new UnderstandingModal(this.app, this.editor, this.selected, tag).open();
    }, 50);
  }
}

class UnderstandingModal extends FuzzySuggestModal<UnderstandingOption> {
  constructor(
    app: App,
    private editor: Editor,
    private selected: string,
    private tag: TagOption,
  ) {
    super(app);
    this.setPlaceholder(`第 2/2 步：选理解度（Tag: ${tag.label}）`);
  }

  getItems(): UnderstandingOption[] {
    return [...UNDERSTANDING_OPTIONS];
  }

  getItemText(item: UnderstandingOption): string {
    return item.label;
  }

  onChooseItem(und: UnderstandingOption) {
    this.editor.replaceSelection(
      wrapSelection(this.selected, this.tag, und.value),
    );
  }
}
