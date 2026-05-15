import {
  type App,
  type Editor,
  FuzzySuggestModal,
  Modal,
  Notice,
  Plugin,
  TFile,
} from "obsidian";
import {
  TAG_OPTIONS,
  type TagOption,
  UNDERSTANDING_OPTIONS,
  type UnderstandingOption,
  type UnderstandingValue,
  USER_INPUT_PROMPT,
  wrapSelection,
  type ParsedCallout,
} from "./callout";
import { CalloutSyncDebouncer } from "./callout-sync"; // DEPRECATED Plan B
import { FrontmatterTipsSync } from "./frontmatter-tips-sync";
import {
  extractBoardNameFromPath,
  extractSourceBoardFromFrontmatter,
  isFlatArchPath,
  isNodesPath,
  RELATION_TYPES,
  type RelationTypeOption,
} from "./ai-linked-doc";
import {
  buildBoardActivityLine,
  buildBoardConceptsLine,
  buildNodeBody,
  buildNodeFrontmatter,
  buildSourceReplacement,
  deriveConceptStub,
  resolveUniqueNodeName,
} from "./node-derivation";
import {
  type BacklinkSummary,
  buildSeedActivityLine,
  buildSeedConceptsLine,
  type ConfigureScenario,
  deduplicateExistingBoards,
  determineScenario,
  findBacklinkingNotes,
  parseVaultConfigYaml,
  recountBoardConcepts,
  renderWhiteboardTemplate,
  resolveUniqueSeedName,
  sanitizeBoardName,
  summarizeBacklinks,
  validateBoardName,
  type VaultConfig,
} from "./configure-whiteboard";
import {
  buildNodeChatPrompt,
  extractBodyWithoutFrontmatter,
  extractFrontmatterType,
  isNodePath,
  type NeighborSummary,
  type NodeChatContext,
} from "./node-chat-context";

const DEFAULT_BACKEND_URL = "http://localhost:8001";

interface CanvasPluginSettings {
  backendUrl: string;
}

const DEFAULT_SETTINGS: CanvasPluginSettings = {
  backendUrl: DEFAULT_BACKEND_URL,
};

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
  settings: CanvasPluginSettings = { ...DEFAULT_SETTINGS };
  /** v4.3 A 路线：mastery 聚合缓存。Story 1.18 路径 1 plugin API 暴露。 */
  private masteryCache = new Map<string, { value: number; ts: number }>();
  /** Story 2.4 Plan B Phase 1 (2026-05-14) DEPRECATED — 见 plan-b-postmortem.md */
  private calloutSync!: CalloutSyncDebouncer;
  /** Story 2.4 Plan A (2026-05-14): frontmatter tips[] 自动同步 */
  private frontmatterSync!: FrontmatterTipsSync;

  async onload() {
    await this.loadSettings();
    this.registerCanvasCommands();
    this.addSettingTab(new CanvasSettingTab(this.app, this));
    this.app.workspace.onLayoutReady(() => {
      this.checkHotkeyConflicts();
    });
    // Story 2.4 Plan A (2026-05-14): metadataCache.on('changed') → FrontmatterTipsSync
    // 用 Obsidian 内部 throttle 的 metadataCache 事件触发 frontmatter tips[] 自动维护
    // (vs Plan B 用 vault.on('modify') 容易跟自己写 frontmatter 形成循环)
    this.frontmatterSync = new FrontmatterTipsSync(this);
    this.registerEvent(
      this.app.metadataCache.on("changed", (file) => {
        if (file.path.startsWith("节点/") || file.path.startsWith("原白板/")) {
          this.masteryCache.clear();
          // Plan A core: 文件变化 → 重新解析 callout → 同步到 frontmatter tips[]
          void this.frontmatterSync.syncFile(file);
        }
      }),
    );

    // Story 2.4 Plan B Phase 1 (2026-05-14) — DEPRECATED 2026-05-14 路径 1 决策:
    // 4 方对抗审查 (Canvas / Claude / ChatGPT-1 / ChatGPT-2) 一致建议回退 Plan A。
    // 详见 _bmad-output/research/2026-05-14-plan-b-postmortem.md
    //
    // Plan B 入口已 disable — vault.on('modify') 监听不再触发 batch sync。
    // 代码保留作为 Plan C 未来重启时的参考（修复 ChatGPT 找的 7 盲点后才能复活）。
    //
    // this.calloutSync = new CalloutSyncDebouncer(this);
    // this.registerEvent(
    //   this.app.vault.on("modify", (file) => {
    //     if (file instanceof TFile) {
    //       this.calloutSync.scheduleSync(file);
    //     }
    //   }),
    // );
  }

  onunload() {
    // Plan B disabled — calloutSync 不再实例化
    this.calloutSync?.shutdown();
  }

  /**
   * Story 2.4 Plan B (2026-05-14): batch 同步文件内所有 callout 到 backend。
   *
   * 由 CalloutSyncDebouncer 在 vault.on('modify') + 500ms debounce 后调用。
   * Backend 用 content_hash 做幂等去重 — 同 hash 不创建 v2 episode，不同 hash
   * 触发 Graphiti add_episode 生成新版本（保留 v1 作为时序演化痕迹）。
   *
   * 静默失败：debounce 同步不应打扰用户（不像 P0-1 modal 同步有 Notice）。
   */
  async batchSyncCallouts(
    nodeId: string,
    callouts: ParsedCallout[],
  ): Promise<void> {
    if (callouts.length === 0) return;
    try {
      await this.callBackend(
        "/api/v1/tips/batch",
        "批注 debounce 同步",
        {
          node_id: nodeId,
          callouts: callouts.map((c) => ({
            tag: c.tag,
            tag_label: c.tagLabel,
            understanding: c.understanding,
            content: c.content,
            content_hash: c.contentHash,
          })),
          source_timestamp: new Date().toISOString(),
        },
        "POST",
      );
    } catch {
      // 静默：debounce sync 失败不应打扰用户体验
    }
  }

  async loadSettings() {
    const data = (await this.loadData()) as Partial<CanvasPluginSettings>;
    this.settings = { ...DEFAULT_SETTINGS, ...(data ?? {}) };
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  /**
   * Story 1.18 路径 1 · A 路线：plugin 公共 API（暴露到 app.plugins.plugins["canvas-learning-system"]）
   * 让 Dashboard.md 的 DataviewJS 块通过 app.plugins API 直接调用，无 React 依赖。
   */

  /** 返回某白板下所有节点的 mastery 聚合（avg + count + nodes 列表） */
  public getMasteryBatch(boardName: string): {
    count: number;
    avgMastery: number;
    nodes: Array<{ path: string; name: string; mastery: number }>;
  } {
    const cached = this.masteryCache.get(boardName);
    if (cached && Date.now() - cached.ts < 2000) {
      return cached.value as any;
    }
    const allFiles = this.app.vault.getMarkdownFiles().filter((f) =>
      f.path.startsWith("节点/"),
    );
    const matched: Array<{ path: string; name: string; mastery: number }> = [];
    for (const f of allFiles) {
      const fm = this.app.metadataCache.getFileCache(f)?.frontmatter as
        | Record<string, unknown>
        | undefined;
      if (!fm) continue;
      const sb = fm.source_board;
      if (!sb) continue;
      const sbStr =
        typeof sb === "string"
          ? sb
          : (sb as any).link || (sb as any).path || "";
      if (!sbStr.includes(`原白板/${boardName}`)) continue;
      const m = typeof fm.mastery_score === "number" ? fm.mastery_score : 0.30;
      matched.push({ path: f.path, name: f.basename, mastery: m });
    }
    const avg = matched.length
      ? matched.reduce((s, n) => s + n.mastery, 0) / matched.length
      : 0;
    const result = { count: matched.length, avgMastery: avg, nodes: matched };
    this.masteryCache.set(boardName, { value: result as any, ts: Date.now() });
    return result;
  }

  /** Dashboard.md 按钮调此方法触发对应命令（D4-3 confirm Modal 等） */
  public executeBoardCommand(boardName: string, action: string): void {
    if (action === "exam-start") {
      const boardFile = this.app.vault.getAbstractFileByPath(
        `原白板/${boardName}.md`,
      );
      if (boardFile && "extension" in (boardFile as any)) {
        this.app.workspace.getLeaf(false).openFile(boardFile as TFile);
        setTimeout(() => {
          (this.app as any).commands.executeCommandById(
            "canvas-learning-system:canvas:start-examination-confirm",
          );
        }, 200);
      } else {
        new Notice(`❌ 原白板/${boardName}.md 不存在`, 5000);
      }
    } else if (action === "open-board") {
      const boardFile = this.app.vault.getAbstractFileByPath(
        `原白板/${boardName}.md`,
      );
      if (boardFile && "extension" in (boardFile as any)) {
        this.app.workspace.getLeaf(false).openFile(boardFile as TFile);
      }
    }
  }

  /** Dashboard.md 强制刷新缓存（用户手动按"刷新"按钮） */
  public invalidateMasteryCache(boardName?: string): void {
    if (boardName) {
      this.masteryCache.delete(boardName);
    } else {
      this.masteryCache.clear();
    }
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
      name: "启动考察（直调，无 confirm）",
      callback: () => this.handleStartExaminationDirect(),
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
      callback: () => this.handleStartExaminationDirect(),
    });

    this.addCommand({
      id: "canvas:open-dashboard",
      name: "打开 Dashboard.md",
      callback: () => this.handleOpenDashboard(),
    });

    this.addCommand({
      id: "canvas:open-review-queue",
      name: "打开复习队列（GET /review/schedule）",
      callback: () =>
        this.callBackend(
          "/api/v1/review/schedule?days=7",
          "打开复习队列",
          undefined,
          "GET",
        ),
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

    this.addCommand({
      id: "canvas:configure-whiteboard",
      name: "建/配置原白板（v4 全 plugin 脚本）",
      callback: () => this.handleConfigureWhiteboard(),
    });

    this.addCommand({
      id: "canvas:append-note-to-board",
      name: "把当前笔记追加到已有原白板",
      callback: () => this.handleAppendNoteToBoard(),
    });

    this.addCommand({
      id: "canvas:start-examination-confirm",
      name: "启动考察（带 confirm 弹窗）",
      callback: () => this.handleStartExaminationConfirm(),
    });

    this.addCommand({
      id: "canvas:open-node-chat",
      name: "节点对话（注入上下文 + 切 Claudian）",
      callback: () => this.handleOpenNodeChat(),
    });
  }

  /**
   * Story 3.1 v1.0 — 节点 AI 对话入口（路线 A · 4 MVP 闭环达成后启动）
   *
   * 流程：
   *   1. 检 active file 在 节点/ 路径
   *   2. 收集 4 类上下文（frontmatter / body / selection / 1-hop 邻居）
   *   3. 组装 prompt（< 10KB，超长自动截断）
   *   4. 写剪贴板 + Notice + 切 Claudian sidebar
   *   5. 用户粘贴 → /node-chat Skill 接管对话（不写文件，纯对话）
   *
   * 复用 1.17 v3.0 已验证的 Hybrid 范式（plugin 仅做 deterministic 工作）。
   */
  private async handleOpenNodeChat() {
    console.log("[canvas:open-node-chat] triggered");
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }
    if (!isNodePath(activeFile.path)) {
      new Notice(
        `对话仅在 节点/ 下的概念页可用（当前 path: ${activeFile.path}）`,
        5000,
      );
      return;
    }

    const editor = this.app.workspace.activeEditor?.editor;
    const selection = editor?.getSelection();

    let content: string;
    try {
      content = await this.app.vault.read(activeFile);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 读节点正文失败: ${msg}`, 6000);
      return;
    }
    const body = extractBodyWithoutFrontmatter(content);
    const fmRaw =
      (this.app.metadataCache.getFileCache(activeFile)?.frontmatter as
        | Record<string, unknown>
        | undefined) ?? {};

    const neighbors = await this.collectNodeNeighbors(activeFile.path, 5);

    const context: NodeChatContext = {
      nodePath: activeFile.path,
      nodeBasename: activeFile.basename,
      frontmatter: fmRaw,
      body,
      selection: selection && selection.trim() ? selection : undefined,
      neighbors,
    };
    const result = buildNodeChatPrompt(context);

    try {
      await navigator.clipboard.writeText(result.prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.showRetryNotice(
        `❌ 剪贴板写入失败（${msg}），点重试再试一次`,
        () => void this.handleOpenNodeChat(),
      );
      return;
    }

    const sizeKb = (result.sizeBytes / 1024).toFixed(1);
    const truncatedHint = result.truncated
      ? `（已截断: ${result.truncationReason}）`
      : "";
    new Notice(
      `已复制节点 "${activeFile.basename}" 上下文（${sizeKb}KB / ${neighbors.length} 邻居）${truncatedHint}\n切到 Claudian 粘贴即可触发对话`,
      6000,
    );

    const claudianCmd = (this.app as any).commands?.findCommand?.(
      "claudian:open-view",
    );
    if (!claudianCmd) {
      new Notice(
        "未检测到 Claudian 插件，请先安装并登录 Claude Code",
        5000,
      );
      return;
    }
    (this.app as any).commands.executeCommandById("claudian:open-view");
  }

  /**
   * 从 metadataCache.resolvedLinks 取 1-hop 邻居（前 N 个）。
   * 每个邻居拉 frontmatter.type + 首 100 字摘要（用于 prompt 注入）。
   */
  private async collectNodeNeighbors(
    nodePath: string,
    max: number,
  ): Promise<NeighborSummary[]> {
    const resolved =
      ((this.app.metadataCache as any).resolvedLinks as
        | Record<string, Record<string, number>>
        | undefined) ?? {};
    const linkMap = resolved[nodePath] ?? {};
    const paths = Object.keys(linkMap).slice(0, max);

    const summaries: NeighborSummary[] = [];
    for (const p of paths) {
      const file = this.app.vault.getAbstractFileByPath(p);
      const fm =
        file && "extension" in (file as any)
          ? (this.app.metadataCache.getFileCache(file as TFile)
              ?.frontmatter as Record<string, unknown> | undefined)
          : undefined;
      const type = extractFrontmatterType(fm);

      let excerpt: string | undefined;
      if (file && "extension" in (file as any)) {
        try {
          const content = await this.app.vault.cachedRead(file as TFile);
          const body = extractBodyWithoutFrontmatter(content);
          excerpt = body.slice(0, 200);
        } catch {
          excerpt = undefined;
        }
      }

      summaries.push({
        path: p.replace(/\.md$/, ""),
        type,
        excerpt,
      });
    }
    return summaries;
  }

  /**
   * Story 1.18 v1.0 D4-3 — 启动考察前弹 confirm Modal。
   *
   * 用户决策：dashboard 上一键考察按钮**先弹 Modal 确认**，避免误触。
   * Modal 显示: "确认进入考察模式？将基于 mastery <0.5 的节点生成 5 题。"
   * 用户点"开始考察"→ 调 backend `/api/v1/exam/start`
   * 用户点"取消"或 Esc → Modal 关闭无副作用
   */
  private handleStartExaminationConfirm() {
    const activeFile = this.app.workspace.getActiveFile();
    const sourceContext = activeFile?.path.startsWith("原白板/")
      ? `原白板"${activeFile.basename}"`
      : "当前 vault";
    new ConfirmExamModal(this.app, sourceContext, () => {
      this.callBackend("/api/v1/exam/start", "启动考察");
    }).open();
  }

  /**
   * Story 1.19 v4.0 — 把"已有笔记追加到已存在白板"作为独立命令。
   *
   * 用户场景（v4 UAT 批注暴露的 gap）：
   *   用户已经在某个 md 上，想把它归类到某个**已经存在**的白板（不是建新白板）。
   *   v4 主命令 canvas:configure-whiteboard 只支持"建新白板"+ 反向引用检测追加；
   *   笔记没被反向引用时无明确"追加到已有白板"的 entry point。
   *
   * 流程：
   *   1. 检查 active file（必需）
   *   2. SelectExistingBoardModal（FuzzySuggestModal 列出 原白板/*.md）
   *   3. 校验该白板是否已含此笔记（避免重复 append）
   *   4. SeedModeModal（move / copy / skip）
   *   5. plugin 脚本完成（复用 appendSeedToExistingBoard 的核心逻辑）
   *   6. ✓ Notice
   */
  private handleAppendNoteToBoard() {
    console.log("[canvas:append-note-to-board] triggered");
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开你想归类的笔记（让它成为 active file）", 5000);
      return;
    }

    const boardFiles = this.app.vault
      .getMarkdownFiles()
      .filter((f) => f.path.startsWith("原白板/"));

    if (boardFiles.length === 0) {
      new Notice(
        "原白板/ 下还没有任何白板。请先用 canvas:configure-whiteboard 建一个。",
        6000,
      );
      return;
    }

    new SelectExistingBoardModal(this.app, boardFiles, (boardFile) => {
      void this.continueAppendNoteToBoard(activeFile, boardFile);
    }).open();
  }

  private async continueAppendNoteToBoard(
    sourceFile: TFile,
    boardFile: TFile,
  ) {
    if (sourceFile.path === boardFile.path) {
      new Notice("不能把白板自己追加到自己", 5000);
      return;
    }

    const seedStem = sourceFile.basename;
    const boardContent = await this.app.vault.read(boardFile);
    const expectedWikilink = `[[节点/${seedStem}]]`;
    if (boardContent.includes(expectedWikilink)) {
      new Notice(
        `⚠ 白板 ${boardFile.basename} 的 ## Concepts 已含 ${expectedWikilink}，跳过避免重复`,
        7000,
      );
      return;
    }

    new SeedModeModal(this.app, sourceFile.path, (mode) => {
      void this.executeAppendToBoard(sourceFile, boardFile, mode);
    }).open();
  }

  private async executeAppendToBoard(
    sourceFile: TFile,
    boardFile: TFile,
    mode: "move" | "copy" | "skip",
  ) {
    const t0 = Date.now();
    const boardName = boardFile.basename;
    const sourceInNodesPool = sourceFile.path.startsWith("节点/");

    if (mode === "skip" && !sourceInNodesPool) {
      new Notice(
        `✓ 已选白板 "${boardName}" 但跳过种子归类（你后续手动移动到 节点/）`,
        5000,
      );
      return;
    }

    const desiredStem = sourceFile.basename;
    let seedStem: string;
    try {
      seedStem = resolveUniqueSeedName(desiredStem, (path) => {
        if (path === sourceFile.path) return false;
        return this.app.vault.getAbstractFileByPath(path) !== null;
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 节点池重名解析失败：${msg}`, 7000);
      return;
    }
    const seedTargetPath = `节点/${seedStem}.md`;
    const inNodesPool = sourceFile.path === seedTargetPath;

    if (!inNodesPool && mode !== "skip") {
      try {
        if (mode === "move") {
          await this.app.fileManager.renameFile(sourceFile, seedTargetPath);
        } else {
          const content = await this.app.vault.read(sourceFile);
          await this.app.vault.create(seedTargetPath, content);
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        new Notice(`❌ 种子 ${mode} 到 ${seedTargetPath} 失败：${msg}`, 8000);
        return;
      }
    }

    const seedFile = this.app.vault.getAbstractFileByPath(seedTargetPath);
    if (seedFile && "extension" in (seedFile as any)) {
      try {
        await this.app.fileManager.processFrontMatter(
          seedFile as TFile,
          (fm) => {
            if (!fm.type) fm.type = "concept";
            if (typeof fm.subject === "string") delete fm.subject;
            fm.source_board = `[[原白板/${boardName}]]`;
            if (!fm.created_from) fm.created_from = "append_note_to_board";
          },
        );
      } catch {}
    }

    try {
      const cur = await this.app.vault.read(boardFile);
      const conceptsLine = buildSeedConceptsLine(seedStem);
      const activityLine = buildSeedActivityLine(
        `${seedStem}.md`,
        new Date().toISOString(),
      );
      const updated = appendBoardLines(cur, conceptsLine, activityLine);
      await this.app.vault.modify(boardFile, updated);
      await this.app.fileManager.processFrontMatter(boardFile, (fm) => {
        // v4.2 doc_count: 实时数 ## Concepts 行（不再累加，避免 cleanup 漂移）
        fm.doc_count = recountBoardConcepts(updated);
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(
        `⚠ 种子 ${mode} 已完成但白板 ${boardName} ## Concepts 更新失败：${msg}`,
        9000,
      );
      return;
    }

    const elapsed = Date.now() - t0;
    const action =
      mode === "move"
        ? "已移动"
        : mode === "copy"
          ? "已复制"
          : "已就地补 source_board";
    new Notice(
      `✓ 笔记 ${seedStem}.md ${action} → 追加到白板 "${boardName}"（${elapsed}ms）`,
      7000,
    );
  }

  /**
   * Story 1.19 v4.0 — configure-whiteboard 全 plugin 化（替代 v3.1 Skill）
   *
   * 流程：场景判定 → 读 vault config → 输入 board name → 检测冲突 + 反向引用
   *      → 建白板 md → (场景 B) 种子归类 → 回执 Notice
   *
   * 全部 deterministic，<300ms 完成（vs Skill v3.1 的 15-30s LLM 推理）。
   * Skill v3.1 保留作 fallback（用户输 /configure-whiteboard 仍能跑）。
   */
  private async handleConfigureWhiteboard() {
    console.log("[canvas:configure-whiteboard] triggered (v4 plugin)");
    const t0 = Date.now();

    const config = await this.readVaultConfig();
    if (!config) {
      new Notice(
        "❌ 未找到 .canvas-config.yaml 或解析失败。请先建 vault 级配置（参考 deploy-vault Skill）",
        8000,
      );
      return;
    }

    const activeFile = this.app.workspace.getActiveFile();
    const sourcePath = activeFile?.path ?? null;
    const scenario = determineScenario(sourcePath);

    new BoardNameInputModal(this.app, scenario, sourcePath, (boardName) => {
      void this.continueConfigureWhiteboard({
        boardName,
        scenario,
        sourcePath,
        activeFile,
        config,
        t0,
      });
    }).open();
  }

  private async readVaultConfig(): Promise<VaultConfig | null> {
    try {
      const text = await this.app.vault.adapter.read(".canvas-config.yaml");
      return parseVaultConfigYaml(text);
    } catch {
      return null;
    }
  }

  private async continueConfigureWhiteboard(args: {
    boardName: string;
    scenario: ConfigureScenario;
    sourcePath: string | null;
    activeFile: TFile | null;
    config: VaultConfig;
    t0: number;
  }) {
    const { boardName, scenario, sourcePath, activeFile, config, t0 } = args;
    const boardPath = `原白板/${boardName}.md`;

    const existing = this.app.vault.getAbstractFileByPath(boardPath);
    if (existing) {
      new Notice(
        `⚠ 原白板/${boardName}.md 已存在。请换名重试，或手动追加种子到该白板。`,
        8000,
      );
      return;
    }

    if (scenario === "scenario_b" && activeFile) {
      const resolvedLinks =
        (this.app.metadataCache as any).resolvedLinks ?? {};
      const hits = findBacklinkingNotes(resolvedLinks, activeFile.path);
      if (hits.length > 0) {
        const summaries = summarizeBacklinks(hits, (path) => {
          const f = this.app.vault.getAbstractFileByPath(path);
          if (!f || !("extension" in (f as any))) return undefined;
          return this.app.metadataCache.getFileCache(f as TFile)?.frontmatter as
            | Record<string, unknown>
            | undefined;
        });
        const existingBoards = deduplicateExistingBoards(summaries);

        if (existingBoards.length > 0) {
          new BacklinkWarningModal(
            this.app,
            activeFile.path,
            summaries,
            existingBoards,
            boardName,
            (choice) => {
              if (choice === "cancel") {
                new Notice(
                  `✗ 用户取消。请去 [[原白板/${existingBoards[0]}]] 查看后再决定`,
                  6000,
                );
                return;
              }
              if (choice === "append_to_existing") {
                void this.appendSeedToExistingBoard(
                  activeFile,
                  existingBoards[0],
                );
                return;
              }
              void this.actuallyCreateWhiteboard({
                boardName,
                boardPath,
                scenario,
                sourcePath,
                activeFile,
                config,
                t0,
                ignoredBacklinks: true,
              });
            },
          ).open();
          return;
        }
      }
    }

    void this.actuallyCreateWhiteboard({
      boardName,
      boardPath,
      scenario,
      sourcePath,
      activeFile,
      config,
      t0,
      ignoredBacklinks: false,
    });
  }

  private async actuallyCreateWhiteboard(args: {
    boardName: string;
    boardPath: string;
    scenario: ConfigureScenario;
    sourcePath: string | null;
    activeFile: TFile | null;
    config: VaultConfig;
    t0: number;
    ignoredBacklinks: boolean;
  }) {
    const { boardName, boardPath, scenario, activeFile, t0, ignoredBacklinks } =
      args;
    const createdAt = new Date().toISOString();

    let boardFile: TFile;
    try {
      const content = renderWhiteboardTemplate(boardName, createdAt);
      boardFile = await this.app.vault.create(boardPath, content);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 建白板失败：${msg}`, 8000);
      return;
    }

    if (scenario === "scenario_b" && activeFile) {
      new SeedModeModal(this.app, activeFile.path, (mode) => {
        void this.handleSeedRelocation({
          mode,
          activeFile,
          boardFile,
          boardName,
          createdAt,
          t0,
          ignoredBacklinks,
        });
      }).open();
      return;
    }

    const elapsed = Date.now() - t0;
    const note = ignoredBacklinks
      ? "（⚠ 用户选择忽略反向引用）"
      : "";
    new Notice(
      `✓ 原白板 "${boardName}" 已建立（${elapsed}ms）${note}\n位置: ${boardPath}\n种子: 0（空白板）`,
      8000,
    );
  }

  private async handleSeedRelocation(args: {
    mode: "move" | "copy" | "skip";
    activeFile: TFile;
    boardFile: TFile;
    boardName: string;
    createdAt: string;
    t0: number;
    ignoredBacklinks: boolean;
  }) {
    const { mode, activeFile, boardFile, boardName, createdAt, t0 } = args;

    if (mode === "skip") {
      const elapsed = Date.now() - t0;
      new Notice(
        `✓ 原白板 "${boardName}" 已建立（${elapsed}ms）。种子未归类（用户跳过）。`,
        7000,
      );
      return;
    }

    const seedStemDesired = activeFile.basename;
    let seedStem: string;
    try {
      seedStem = resolveUniqueSeedName(seedStemDesired, (path) => {
        return this.app.vault.getAbstractFileByPath(path) !== null;
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 种子重名解析失败：${msg}`, 8000);
      return;
    }
    const seedBasename = `${seedStem}.md`;
    const seedTarget = `节点/${seedBasename}`;

    try {
      if (mode === "move") {
        await this.app.fileManager.renameFile(activeFile, seedTarget);
      } else {
        const content = await this.app.vault.read(activeFile);
        await this.app.vault.create(seedTarget, content);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`⚠ 种子 ${mode} 失败：${msg}（白板已建好）`, 9000);
      return;
    }

    const seedFile = this.app.vault.getAbstractFileByPath(seedTarget);
    if (seedFile && "extension" in (seedFile as any)) {
      try {
        await this.app.fileManager.processFrontMatter(
          seedFile as TFile,
          (fm) => {
            if (!fm.type) fm.type = "concept";
            if (typeof fm.subject === "string") delete fm.subject;
            fm.source_board = `[[原白板/${boardName}]]`;
            if (!fm.created_from) fm.created_from = "configure_whiteboard_seed";
          },
        );
      } catch {}
    }

    try {
      const cur = await this.app.vault.read(boardFile);
      const conceptsLine = buildSeedConceptsLine(seedStem);
      const activityLine = buildSeedActivityLine(seedBasename, createdAt);
      const updated = appendBoardLines(cur, conceptsLine, activityLine);
      await this.app.vault.modify(boardFile, updated);
      await this.app.fileManager.processFrontMatter(boardFile, (fm) => {
        // v4.2 doc_count: 实时数 ## Concepts 行（不再累加，避免 cleanup 漂移）
        fm.doc_count = recountBoardConcepts(updated);
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`⚠ 白板 ${boardName} ## Concepts 更新失败：${msg}`, 9000);
      return;
    }

    const elapsed = Date.now() - t0;
    new Notice(
      `✓ 原白板 "${boardName}" 已建立 + 种子 ${seedBasename} 归入 节点/ + ## Concepts 已添加 [[节点/${seedStem}]]（共 ${elapsed}ms）`,
      8000,
    );
  }

  private async appendSeedToExistingBoard(
    seedFile: TFile,
    boardName: string,
  ) {
    const boardPath = `原白板/${boardName}.md`;
    const boardFile = this.app.vault.getAbstractFileByPath(boardPath);
    if (!boardFile || !("extension" in (boardFile as any))) {
      new Notice(`❌ 已有白板 ${boardPath} 找不到`, 6000);
      return;
    }

    const seedStem = seedFile.basename;
    const seedBasename = `${seedStem}.md`;
    const inNodesPool = seedFile.path.startsWith("节点/");

    if (!inNodesPool) {
      try {
        await this.app.fileManager.renameFile(
          seedFile,
          `节点/${seedBasename}`,
        );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        new Notice(`⚠ 种子移到 节点/ 失败：${msg}`, 8000);
        return;
      }
    }

    const finalSeedFile = this.app.vault.getAbstractFileByPath(
      `节点/${seedBasename}`,
    );
    if (finalSeedFile && "extension" in (finalSeedFile as any)) {
      try {
        await this.app.fileManager.processFrontMatter(
          finalSeedFile as TFile,
          (fm) => {
            if (!fm.type) fm.type = "concept";
            if (typeof fm.subject === "string") delete fm.subject;
            fm.source_board = `[[原白板/${boardName}]]`;
            if (!fm.created_from)
              fm.created_from = "configure_whiteboard_backlink_append";
          },
        );
      } catch {}
    }

    try {
      const cur = await this.app.vault.read(boardFile as TFile);
      const conceptsLine = buildSeedConceptsLine(seedStem);
      const activityLine = buildSeedActivityLine(
        seedBasename,
        new Date().toISOString(),
      );
      const updated = appendBoardLines(cur, conceptsLine, activityLine);
      await this.app.vault.modify(boardFile as TFile, updated);
      await this.app.fileManager.processFrontMatter(
        boardFile as TFile,
        (fm) => {
          // v4.2 doc_count: 实时数 ## Concepts 行（不再累加，避免 cleanup 漂移）
          fm.doc_count = recountBoardConcepts(updated);
        },
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`⚠ 白板 ${boardName} 更新失败：${msg}`, 9000);
      return;
    }

    new Notice(
      `✓ 种子 ${seedBasename} 已追加到已有白板 "${boardName}"（v4 反向引用检测建议）`,
      7000,
    );
  }

  /**
   * Story 1.17 v2.2 (D4-2): Show a sticky Notice with a retry button.
   * Used when clipboard write or Claudian invoke fails — preserves user's selection context
   * so retry can re-run handleAILinkedDoc without forcing user to re-select text.
   * Duration: 10s (long enough to read + click). User can also dismiss.
   */
  private showRetryNotice(message: string, retryFn: () => void) {
    const notice = new Notice("", 10000);
    notice.noticeEl.empty();
    notice.noticeEl.createSpan({ text: message });
    const btn = notice.noticeEl.createEl("button", {
      text: "重试",
      cls: "mod-cta",
    });
    btn.style.marginLeft = "8px";
    btn.onclick = () => {
      notice.hide();
      retryFn();
    };
  }

  /**
   * Story 1.17 v2.4: Copy selection + Skill-invoke prompt to clipboard, open Claudian sidebar.
   * AI generation / file i/o / wikilink replacement / 关系 callout 双写 is handled by
   * `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md`, running in Claude Code CLI
   * with the user's subscription (Mode D, architecture.md:113).
   *
   * D4-1 (toast 不打断 阅读): Plugin does NOT call workspace.openLinkText to auto-open the
   *   derived node — user stays on source md. Skill returns 3-line receipt with wikilink
   *   text the user can manually click to jump (not forced).
   * D4-2 (toast + 重试 按钮): Failures show a sticky Notice with a "重试" button that
   *   re-invokes handleAILinkedDoc, preserving user's selection context.
   * D1-2 (派生前立即弹关系类型 modal): Before clipboard write, open RelationTypeModal so the
   *   user picks one of 7 semantic types (prerequisite / depends_on / refines / extends /
   *   example_of / contradicts / related_to). Cancelling modal aborts derivation silently.
   */
  private handleAILinkedDoc() {
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

    let activeBoard = extractBoardNameFromPath(sourcePath) ?? undefined;

    if (!activeBoard && isNodesPath(sourcePath) && activeFile) {
      const cache = this.app.metadataCache.getFileCache(activeFile);
      const inherited = extractSourceBoardFromFrontmatter(
        cache?.frontmatter as Record<string, unknown> | undefined,
      );
      if (inherited) {
        activeBoard = inherited;
        new Notice(
          `继承源节点白板归属：${inherited}（v2.6 自动）`,
          3000,
        );
      }
    }

    if (!isFlatArchPath(sourcePath) && sourcePath !== "unknown") {
      new Notice(
        `当前笔记 ${sourcePath} 不在 原白板/ 或 节点/ 路径下。Skill 会读 .canvas-config.yaml 或 AskUserQuestion 问你归属哪个原白板。`,
        7000,
      );
    }

    if (!activeFile) {
      new Notice("无 active file，无法派生", 3000);
      return;
    }

    new RelationTypeModal(this.app, (relationKey) => {
      new DescriptionModal(this.app, relationKey, (description) => {
        void this.runHybridDerivation({
          selected,
          sourcePath,
          activeFile,
          editor,
          activeBoard,
          relationKey,
          description,
        });
      }).open();
    }).open();
  }

  /**
   * Story 1.17 v3.0 — Hybrid 阶段 1（plugin 脚本，<100ms）
   *
   * 把 v2.6 全 LLM Skill 流程的 7 个 deterministic 步骤迁回 plugin：
   *   1. 启发式提取概念名（无 LLM，零延迟）
   *   2. 节点池重名处理（_2 / _3 / ...）
   *   3. vault.create() 建节点 md（含 placeholder 正文 + AI_BODY_PLACEHOLDER 标记）
   *   4. processFrontMatter() 注入完整 frontmatter（含 relationships[] + status: ai_pending）
   *   5. editor.replaceSelection() 替换源笔记选中文为 wikilink + 关系 callout
   *   6. processFrontMatter + 字符串 append 更新白板 ## Concepts + ## Recent Activity
   *   7. 写剪贴板（v3 prompt = 极简，仅让 Skill 生成 3 段正文 + Edit 替换 placeholder）+ 切 Claudian
   *
   * 任一阶段 1 步骤失败 → 弹错 Notice，**不**回滚已 commit 的 artifact（partial commit 哲学）。
   * 阶段 2（Skill v5.0）成功 / 失败 / 用户取消 都不影响阶段 1 已建的骨架。
   */
  private async runHybridDerivation(args: {
    selected: string;
    sourcePath: string;
    activeFile: TFile;
    editor: Editor;
    activeBoard: string | undefined;
    relationKey: string;
    description: string;
  }) {
    const t0 = Date.now();
    const sourceNoteStem = args.activeFile.basename;

    let activeBoard = args.activeBoard;
    if (!activeBoard) {
      new Notice(
        `❌ 未确定活动白板：当前笔记 ${args.sourcePath} 不是白板路径也无 source_board frontmatter。请先在节点继承的笔记或原白板内派生。`,
        7000,
      );
      return;
    }

    const stub = deriveConceptStub(args.selected);
    let conceptName: string;
    try {
      conceptName = resolveUniqueNodeName(stub, (path) => {
        return this.app.vault.getAbstractFileByPath(path) !== null;
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 节点名解析失败：${msg}`, 8000);
      return;
    }

    const nodePath = `节点/${conceptName}.md`;
    const boardPath = `原白板/${activeBoard}.md`;

    const boardFile = this.app.vault.getAbstractFileByPath(boardPath);
    if (!boardFile) {
      new Notice(
        `❌ 原白板/${activeBoard}.md 不存在，请先 /configure-whiteboard 建白板`,
        8000,
      );
      return;
    }

    const createdAt = new Date().toISOString();
    let nodeFile: TFile;
    try {
      const nodeBody = buildNodeBody(
        conceptName,
        args.selected,
        sourceNoteStem,
      );
      nodeFile = await this.app.vault.create(nodePath, nodeBody);
      await this.app.fileManager.processFrontMatter(nodeFile, (fm) => {
        const data = buildNodeFrontmatter({
          sourceNoteStem,
          activeBoard: activeBoard!,
          relationKey: args.relationKey,
          description: args.description,
          createdAt,
        });
        Object.assign(fm, data);
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 建节点失败：${msg}`, 8000);
      return;
    }

    try {
      const replacement = buildSourceReplacement(
        conceptName,
        args.relationKey,
        args.description,
        args.selected,
      );
      args.editor.replaceSelection(replacement);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(
        `⚠ 节点已建但源笔记 wikilink 替换失败（${msg}）。请手动在源笔记加 [[节点/${conceptName}]]`,
        9000,
      );
    }

    try {
      if (boardFile instanceof Object && "extension" in (boardFile as any)) {
        const tFile = boardFile as TFile;
        const conceptsLine = buildBoardConceptsLine(
          conceptName,
          args.relationKey,
        );
        const activityLine = buildBoardActivityLine(
          conceptName,
          sourceNoteStem,
          args.relationKey,
          createdAt,
        );
        const cur = await this.app.vault.read(tFile);
        const updated = appendBoardLines(cur, conceptsLine, activityLine);
        await this.app.vault.modify(tFile, updated);
        await this.app.fileManager.processFrontMatter(tFile, (fm) => {
          // v4.2 doc_count: 实时数 ## Concepts 行（不再累加，避免 cleanup 漂移）
          fm.doc_count = recountBoardConcepts(updated);
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(
        `⚠ 节点 + 源笔记已 OK，但白板 ${activeBoard} 更新失败（${msg}）`,
        9000,
      );
    }

    const elapsedMs = Date.now() - t0;
    new Notice(
      `✓ 派生完成 [[节点/${conceptName}]]（${elapsedMs}ms）。新节点已开 — 在三段空白处写下你的理解，或打开 Claudian 围绕本节点对话。`,
      8000,
    );
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
    new TagTypeModal(this.app, editor, selected, this).open();
  }

  /**
   * P0-1 (2026-05-13): 批注同步到后端 — 修复 G1 (handleAnnotateCallout 0 fetch)
   *
   * 端到端闭环：用户 Cmd+Shift+A 批注 → wrapSelection 写本地 callout → 此方法
   * POST /api/v1/tips → memory_service.record_knowledge_entity (event_type=
   * callout_annotation) → memory_format.py 映射为 source_description=
   * 'callout-annotation-record' → question_generator._get_tips 可读出（P0-2b）。
   *
   * node_id 取 active file basename（扁平 vault 架构下 = 概念名 / 白板名）。
   * tags 数组编码 [tag:tips, understanding:fuzzy] 形式，供后续分析使用。
   */
  public async saveCalloutToBackend(
    selected: string,
    tag: TagOption,
    understanding: UnderstandingValue,
  ): Promise<void> {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      return;
    }
    const nodeId = activeFile.basename;
    const body = {
      content: selected,
      title: `${tag.label} · ${nodeId}`,
      tags: [`tag:${tag.value}`, `understanding:${understanding}`],
      node_id: nodeId,
      source_timestamp: new Date().toISOString(),
      event_type: "callout_annotation",
    };
    try {
      await this.callBackend("/api/v1/tips", "批注同步", body, "POST");
    } catch {
      // callBackend 内部已显示 Notice，此处吞掉异常防止 Modal 报错
    }
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
   * Story 1.4 AC #4 / Story 1.18 路径 B 修复 · v4.3：
   *   - 显式 method 参数（exam.start 是 POST 但 review.schedule 是 GET）
   *   - 解析返回体（JSON 或 text）让 Notice 显示有用信息
   *   - 用 settings.backendUrl（不再写死 localhost）
   */
  private async callBackend(
    endpoint: string,
    label: string,
    body?: any,
    method: "GET" | "POST" | "PUT" | "DELETE" = body ? "POST" : "GET",
  ): Promise<unknown | null> {
    const url = `${this.settings.backendUrl}${endpoint}`;
    try {
      const resp = await fetch(url, {
        method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      let parsed: unknown = null;
      try {
        parsed = await resp.json();
      } catch {
        parsed = null;
      }
      if (!resp.ok) {
        const detail =
          (parsed as any)?.detail ||
          (parsed as any)?.message ||
          `HTTP ${resp.status}`;
        new Notice(`${label} 失败: ${detail}`, 6000);
        return null;
      }
      const summary =
        (parsed as any)?.id ||
        (parsed as any)?.exam_id ||
        (parsed as any)?.total_count !== undefined
          ? `${label} 成功 · 共 ${(parsed as any).total_count} 项`
          : `${label} 成功`;
      new Notice(summary, 4000);
      return parsed;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(
        `${label} 失败: 后端未连接（${msg}）\n请先 docker compose up 启动 Canvas 后端`,
        6000,
      );
      return null;
    }
  }

  /**
   * Story 1.18 路径 B 修复 · 启动考察（直调 POST /api/v1/exam/start）
   * 修 v3 spec bug: 之前用 GET 触发 endpoint，但后端要求 POST + ExamSessionCreate body。
   * 推断 source_canvas_id：
   *   - active file 在 原白板/X.md → X 作为 board id（MVP 简化，正式应该用 vault_id + board UUID）
   *   - active file 不在 → 弹错让用户先打开白板
   */
  private async handleStartExaminationDirect() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile || !activeFile.path.startsWith("原白板/")) {
      new Notice(
        "请先打开一个原白板（原白板/<板名>.md）再启动考察",
        5000,
      );
      return;
    }
    const boardName = activeFile.basename;
    const result = await this.callBackend(
      "/api/v1/exam/start",
      `启动考察"${boardName}"`,
      {
        source_canvas_id: boardName,
        exam_mode: "mixed",
      },
      "POST",
    );
    if (result && (result as any).id) {
      new Notice(
        `✓ 考察会话已建：${(result as any).id}\n查询：GET /api/v1/exam/${(result as any).id}`,
        7000,
      );
    }
  }

  /**
   * Story 1.18 路径 B 修复 · 打开 Dashboard.md launcher（不再调 health endpoint）
   */
  private async handleOpenDashboard() {
    const dashFile = this.app.vault.getAbstractFileByPath("Dashboard.md");
    if (!dashFile || !("extension" in (dashFile as any))) {
      new Notice("Dashboard.md 不存在（应在 vault 根）", 5000);
      return;
    }
    await this.app.workspace.getLeaf(false).openFile(dashFile as TFile);
  }
}

/**
 * Story 1.18 路径 B · plugin Settings tab（暴露 backendUrl 配置）
 */
import { PluginSettingTab, Setting } from "obsidian";

class CanvasSettingTab extends PluginSettingTab {
  constructor(app: App, private plugin: CanvasLearningPlugin) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl("h2", { text: "Canvas Learning System · 设置" });

    new Setting(containerEl)
      .setName("Backend URL")
      .setDesc(
        "FastAPI 后端 URL（默认 http://localhost:8001）。修改后立即生效，无需重启。",
      )
      .addText((text) =>
        text
          .setPlaceholder(DEFAULT_BACKEND_URL)
          .setValue(this.plugin.settings.backendUrl)
          .onChange(async (value) => {
            this.plugin.settings.backendUrl = value || DEFAULT_BACKEND_URL;
            await this.plugin.saveSettings();
          }),
      );

    containerEl.createEl("p", {
      text: "注意：本地开发用 http://localhost:8001。如部署到远端（含 IP / 域名），用对应 URL。",
      cls: "setting-item-description",
    });
  }
}

/**
 * Story 1.19 v4.0 — 白板名输入 modal（无 LLM）。
 *
 * 默认值启发式：场景 A 留空让用户输；场景 B 用 active file basename 作 placeholder
 * （但不预填，避免误用同名 — 用户应主动思考白板名是否与种子笔记一致）。
 */
class BoardNameInputModal extends Modal {
  private inputEl?: HTMLInputElement;
  private hintEl?: HTMLDivElement;
  private submitted = false;

  constructor(
    app: App,
    private scenario: ConfigureScenario,
    private sourcePath: string | null,
    private onPicked: (boardName: string) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl, titleEl } = this;
    titleEl.setText(
      this.scenario === "scenario_a"
        ? "建白板（场景 A · 从零）"
        : `建白板（场景 B · 从 ${this.sourcePath} 派生）`,
    );

    contentEl.createEl("p", {
      text: "输入新白板的名字（中英文皆可，禁止 / \\ : * ? \" < > | # ^ [ ]）",
    });

    this.inputEl = contentEl.createEl("input", {
      type: "text",
      placeholder: "例如：线性代数 / CS 61B 数据结构 / Eigenvalues & Eigenvectors",
    });
    this.inputEl.style.width = "100%";
    this.inputEl.style.marginBottom = "8px";
    this.inputEl.style.fontSize = "var(--font-ui-medium)";
    this.inputEl.focus();

    this.hintEl = contentEl.createDiv();
    this.hintEl.style.fontSize = "var(--font-ui-small)";
    this.hintEl.style.color = "var(--text-muted)";
    this.hintEl.style.marginBottom = "12px";

    this.inputEl.addEventListener("input", () => this.updateHint());
    this.inputEl.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter") {
        evt.preventDefault();
        this.submit();
      }
    });

    const btnRow = contentEl.createDiv();
    btnRow.style.display = "flex";
    btnRow.style.gap = "8px";
    btnRow.style.justifyContent = "flex-end";

    const cancelBtn = btnRow.createEl("button", { text: "取消" });
    cancelBtn.onclick = () => this.close();

    const submitBtn = btnRow.createEl("button", {
      text: "下一步 (Enter)",
      cls: "mod-cta",
    });
    submitBtn.onclick = () => this.submit();

    this.updateHint();
  }

  private updateHint() {
    if (!this.inputEl || !this.hintEl) return;
    const raw = this.inputEl.value;
    const sanitized = sanitizeBoardName(raw);
    const validation = validateBoardName(sanitized);
    if (!sanitized) {
      this.hintEl.setText("请输入白板名");
      this.hintEl.style.color = "var(--text-muted)";
    } else if (!validation.valid) {
      this.hintEl.setText(`✗ ${validation.reason}`);
      this.hintEl.style.color = "var(--text-error)";
    } else {
      this.hintEl.setText(
        `✓ 将建到 原白板/${sanitized}.md（${sanitized.length} 字符）`,
      );
      this.hintEl.style.color = "var(--text-success)";
    }
  }

  private submit() {
    if (this.submitted) return;
    const raw = this.inputEl?.value ?? "";
    const sanitized = sanitizeBoardName(raw);
    const validation = validateBoardName(sanitized);
    if (!validation.valid) {
      new Notice(`✗ ${validation.reason}`, 4000);
      return;
    }
    this.submitted = true;
    this.close();
    this.onPicked(sanitized);
  }

  onClose() {
    this.contentEl.empty();
  }
}

/**
 * Story 1.19 v4.0 — 反向引用检测命中后的 3 选项 modal（替代 Skill 的 AskUserQuestion）。
 */
type BacklinkChoice = "append_to_existing" | "create_new_anyway" | "cancel";

class BacklinkWarningModal extends Modal {
  constructor(
    app: App,
    private sourcePath: string,
    private summaries: BacklinkSummary[],
    private existingBoards: string[],
    private newBoardName: string,
    private onChoose: (choice: BacklinkChoice) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl, titleEl } = this;
    titleEl.setText("⚠️ 检测到反向引用");

    contentEl.createEl("p", {
      text: `${this.sourcePath} 已被 ${this.summaries.length} 个节点反向引用，可能已属于已有白板。`,
    });

    const list = contentEl.createEl("ul");
    for (const s of this.summaries.slice(0, 5)) {
      const li = list.createEl("li");
      li.setText(
        `${s.sourceMdPath}${
          s.sourceBoardName ? ` （白板: ${s.sourceBoardName}）` : ""
        }`,
      );
    }
    if (this.summaries.length > 5) {
      contentEl.createEl("p", {
        text: `…还有 ${this.summaries.length - 5} 个未列出`,
      });
    }

    const btnRow = contentEl.createDiv();
    btnRow.style.display = "flex";
    btnRow.style.flexDirection = "column";
    btnRow.style.gap = "8px";
    btnRow.style.marginTop = "12px";

    const appendBtn = btnRow.createEl("button", {
      text: `A. 追加到已有白板 "${this.existingBoards[0]}"（推荐）`,
      cls: "mod-cta",
    });
    appendBtn.onclick = () => {
      this.close();
      this.onChoose("append_to_existing");
    };

    const newBtn = btnRow.createEl("button", {
      text: `B. 仍建新白板 "${this.newBoardName}"（碎片化风险）`,
    });
    newBtn.onclick = () => {
      this.close();
      this.onChoose("create_new_anyway");
    };

    const cancelBtn = btnRow.createEl("button", {
      text: "C. 取消（先去看一下已有白板再决定）",
    });
    cancelBtn.onclick = () => {
      this.close();
      this.onChoose("cancel");
    };
  }

  onClose() {
    this.contentEl.empty();
  }
}

/**
 * Story 1.18 v1.0 D4-3 — 启动考察 confirm Modal。
 *
 * 用户决策（2026-04-30）：dashboard 上一键考察按钮**先弹 confirm Modal 防误触**。
 * 显示"确认进入考察模式？将基于 mastery <0.5 的节点生成 5 题"+ 2 按钮（开始/取消）。
 */
class ConfirmExamModal extends Modal {
  constructor(
    app: App,
    private sourceContext: string,
    private onConfirm: () => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl, titleEl } = this;
    titleEl.setText("启动考察 · 确认");

    contentEl.createEl("p", {
      text: `确认从 ${this.sourceContext} 进入考察模式？`,
    });
    contentEl.createEl("p", {
      text: "Plugin 将调用后端 /api/v1/exam/start 基于 mastery < 0.5 的节点生成 5 题。",
    });
    contentEl.createEl("p", {
      text: "⏰ 考察过程预计 5-15 分钟。",
    });

    const btnRow = contentEl.createDiv();
    btnRow.style.display = "flex";
    btnRow.style.gap = "8px";
    btnRow.style.justifyContent = "flex-end";
    btnRow.style.marginTop = "16px";

    const cancelBtn = btnRow.createEl("button", { text: "❌ 取消 (Esc)" });
    cancelBtn.onclick = () => this.close();

    const confirmBtn = btnRow.createEl("button", {
      text: "✅ 开始考察",
      cls: "mod-cta",
    });
    confirmBtn.onclick = () => {
      this.close();
      this.onConfirm();
    };
  }

  onClose() {
    this.contentEl.empty();
  }
}

/**
 * Story 1.19 v4.0 — 选已有原白板（FuzzySuggestModal 列出 原白板/*.md）。
 *
 * 用于"追加笔记到已有白板"独立命令（canvas:append-note-to-board）。
 */
class SelectExistingBoardModal extends FuzzySuggestModal<TFile> {
  constructor(
    app: App,
    private boardFiles: TFile[],
    private onChoose: (boardFile: TFile) => void,
  ) {
    super(app);
    this.setPlaceholder(
      `选要追加到的原白板（共 ${boardFiles.length} 个，输入过滤）`,
    );
  }

  getItems(): TFile[] {
    return [...this.boardFiles];
  }

  getItemText(file: TFile): string {
    return file.basename;
  }

  onChooseItem(file: TFile) {
    this.onChoose(file);
  }
}

/**
 * Story 1.19 v4.0 — 种子 move/copy/skip 选择 modal。
 */
type SeedMode = "move" | "copy" | "skip";

class SeedModeModal extends FuzzySuggestModal<{ key: SeedMode; label: string }>
{
  constructor(
    app: App,
    private sourcePath: string,
    private onChoose: (mode: SeedMode) => void,
  ) {
    super(app);
    this.setPlaceholder(
      `种子笔记 ${sourcePath} 怎么处理？(move 推荐，copy 保留原位，skip 不归类)`,
    );
  }

  getItems() {
    return [
      {
        key: "move" as SeedMode,
        label: "Move（推荐）— 把种子搬到 节点/，原位置删除",
      },
      {
        key: "copy" as SeedMode,
        label: "Copy — 复制到 节点/，原位置保留副本",
      },
      {
        key: "skip" as SeedMode,
        label: "Skip — 不归类种子（白板将是空的）",
      },
    ];
  }

  getItemText(item: { label: string }) {
    return item.label;
  }

  onChooseItem(item: { key: SeedMode }) {
    this.onChoose(item.key);
  }
}

/**
 * Story 1.17 v3.0 — append 白板的 ## Concepts + ## Recent Activity 行（保 section 顺序）。
 *
 * 白板 md 标准结构：frontmatter + ## Concepts + ## 🔗 节点关系图 + ## Recent Activity。
 * Concepts 段在 dataviewjs 块前；Activity 段在文件末尾。
 */
function appendBoardLines(
  current: string,
  conceptsLine: string,
  activityLine: string,
): string {
  let out = current;
  const conceptsHeader = "## Concepts";
  const conceptsIdx = out.indexOf(conceptsHeader);
  if (conceptsIdx >= 0) {
    const afterHeader = conceptsIdx + conceptsHeader.length;
    const nextSectionIdx = out.indexOf("\n## ", afterHeader);
    const nextHrIdx = out.indexOf("\n---", afterHeader);
    const nextDataviewIdx = out.indexOf("\n```dataviewjs", afterHeader);
    const candidates = [nextSectionIdx, nextHrIdx, nextDataviewIdx].filter(
      (i) => i > 0,
    );
    const insertAt = candidates.length > 0 ? Math.min(...candidates) : -1;
    if (insertAt > 0) {
      const before = out.slice(0, insertAt);
      const after = out.slice(insertAt);
      const trimmedBefore = before.replace(/\n+$/, "\n");
      out = `${trimmedBefore}${conceptsLine}\n${after}`;
    } else {
      out = `${out}\n${conceptsLine}\n`;
    }
  } else {
    out = `${out}\n## Concepts\n\n${conceptsLine}\n`;
  }

  const activityHeader = "## Recent Activity";
  const activityIdx = out.indexOf(activityHeader);
  if (activityIdx >= 0) {
    out = out.replace(/\n*$/, "");
    out = `${out}\n${activityLine}\n`;
  } else {
    out = `${out}\n\n## Recent Activity\n\n${activityLine}\n`;
  }
  return out;
}

/**
 * Story 1.17 v2.5 D1-4 + D1-5: Free-text Modal that lets user describe
 * "为什么要把这个节点拉出来 (派生意图)" after picking the relation type.
 * D1-4 决策 B 可选: 留空也能提交（textarea 不强制非空）+ Esc 等同于留空提交
 * D1-5 决策 C 三处都写: description 通过 buildAIDocPrompt 第 5 参数下游 Skill 落到
 *   (1) 源笔记 callout body, (2) 新节点 frontmatter relationships[].description,
 *   (3) AI prompt 让 Skill 据此指导节点正文生成
 */
class DescriptionModal extends Modal {
  private textareaEl?: HTMLTextAreaElement;
  private submitted = false;

  constructor(
    app: App,
    private relationKey: string,
    private onPicked: (description: string) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl, titleEl } = this;
    titleEl.setText(`派生描述（关系: ${this.relationKey}）`);

    contentEl.createEl("p", {
      text: "可选：用一句话描述「为什么把这个节点拉出来」。留空 / 按 Esc 跳过。",
    });

    this.textareaEl = contentEl.createEl("textarea");
    this.textareaEl.rows = 4;
    this.textareaEl.placeholder = "例如：为了单独梳理特征方程的求解步骤，避免 Fundamentals 笔记过长。";
    this.textareaEl.style.width = "100%";
    this.textareaEl.style.marginBottom = "12px";
    this.textareaEl.style.fontSize = "var(--font-ui-medium)";
    this.textareaEl.focus();

    this.textareaEl.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter" && (evt.metaKey || evt.ctrlKey)) {
        evt.preventDefault();
        this.submit();
      }
    });

    const btnRow = contentEl.createDiv({ cls: "modal-button-container" });
    btnRow.style.display = "flex";
    btnRow.style.gap = "8px";
    btnRow.style.justifyContent = "flex-end";

    const skipBtn = btnRow.createEl("button", { text: "跳过 (Esc)" });
    skipBtn.onclick = () => {
      this.textareaEl!.value = "";
      this.submit();
    };

    const submitBtn = btnRow.createEl("button", {
      text: "提交 (Cmd/Ctrl+Enter)",
      cls: "mod-cta",
    });
    submitBtn.onclick = () => this.submit();
  }

  private submit() {
    if (this.submitted) return;
    this.submitted = true;
    const value = this.textareaEl?.value ?? "";
    this.close();
    this.onPicked(value);
  }

  onClose() {
    if (!this.submitted) {
      this.submitted = true;
      this.onPicked("");
    }
    this.contentEl.empty();
  }
}

/**
 * Story 1.17 v2.4 D1-2: Modal that lets user pick one of 7 relation types
 * BEFORE clipboard write + Claudian invocation. Empty selection or Esc dismisses
 * the derivation (no clipboard mutation, no Skill trigger).
 */
class RelationTypeModal extends FuzzySuggestModal<RelationTypeOption> {
  constructor(
    app: App,
    private onPicked: (relationKey: string) => void,
  ) {
    super(app);
    this.setPlaceholder(
      "派生关系：新节点和当前源笔记是什么关系？(7 类，输入过滤)",
    );
  }

  getItems(): RelationTypeOption[] {
    return [...RELATION_TYPES];
  }

  getItemText(item: RelationTypeOption): string {
    return `${item.label} — ${item.description}`;
  }

  onChooseItem(rel: RelationTypeOption) {
    this.onPicked(rel.key);
  }
}

class TagTypeModal extends FuzzySuggestModal<TagOption> {
  constructor(
    app: App,
    private editor: Editor,
    private selected: string,
    private plugin: CanvasLearningPlugin,
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
      new UnderstandingModal(
        this.app,
        this.editor,
        this.selected,
        tag,
        this.plugin,
      ).open();
    }, 50);
  }
}

class UnderstandingModal extends FuzzySuggestModal<UnderstandingOption> {
  constructor(
    app: App,
    private editor: Editor,
    private selected: string,
    private tag: TagOption,
    private plugin: CanvasLearningPlugin,
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
    // 1) 本地写入 callout
    const from = this.editor.getCursor("from");
    const wrapped = wrapSelection(this.selected, this.tag, und.value);
    this.editor.replaceSelection(wrapped);

    // 2) P0-6 (2026-05-14): 光标自动定位到 callout 末尾用户输入区
    // wrapped 最后一行是 "> "（USER_INPUT_PROMPT），光标停在 ch=2 让用户直接输入。
    // 这样用户做完 tag + understanding 选择后，自然继续打字写下自己的理解 / 疑问 /
    // 批注，无需额外 modal，符合 Obsidian native UX。
    const wrappedLines = wrapped.split("\n");
    const targetLine = from.line + wrappedLines.length - 1;
    const targetCh = USER_INPUT_PROMPT.length; // "> " 后面
    this.editor.setCursor({ line: targetLine, ch: targetCh });
    this.editor.focus();

    // 3) P0-1 (2026-05-13) DEPRECATED 2026-05-14 路径 1 决策:
    // Plan B 数据入口已禁用 — 不再 POST /api/v1/tips。
    // Plan A 改由 FrontmatterTipsSync 监听 vault.on('modify') 写 frontmatter
    // tips[] 直接到本地 .md, 无 backend call. 见 plan-b-postmortem.md
    //
    // void this.plugin.saveCalloutToBackend(
    //   this.selected, this.tag, und.value as UnderstandingValue,
    // );
  }
}
