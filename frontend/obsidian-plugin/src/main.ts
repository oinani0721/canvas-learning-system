import {
  type App,
  type Editor,
  FuzzySuggestModal,
  Modal,
  Notice,
  Plugin,
  requestUrl,
  TFile,
} from "obsidian";
import {
  TAG_OPTIONS,
  type TagOption,
  UNDERSTANDING_OPTIONS,
  type UnderstandingOption,
  type UnderstandingValue,
  USER_INPUT_PROMPT,
  NEW_QUESTION_PROMPT,
  padBlockInsert,
  wrapSelection,
  buildNewQuestionCallout,
  computeInsertionSpacing,
  generateAnnotationId,
  type ParsedCallout,
} from "./callout";
import { CalloutSyncDebouncer } from "./callout-sync"; // DEPRECATED Plan B
import { FrontmatterTipsSync } from "./frontmatter-tips-sync";
import {
  extractBoardNameFromPath,
  extractSourceBoardFromFrontmatter,
  isExamBoardPath,
  isFlatArchPath,
  isNodesPath,
  RELATION_TYPES,
  type RelationTypeOption,
} from "./ai-linked-doc";
import {
  buildBoardActivityLine,
  buildBoardConceptsLine,
  buildNodeBody,
  buildNodeDerivedEventLine,
  buildNodeFrontmatter,
  buildSourceReplacement,
  deriveConceptStub,
  extractNearbyConfusion,
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
import {
  buildTipsIncreaseNotice,
  StatusBarController,
} from "./status-bar";
import { QuickExamController } from "./exam-quick";
import {
  buildAcceptPayload,
  buildDisputePayload,
  type ErrorCandidate,
  filterPendingCandidates,
  formatCandidateLabel,
  inferVaultId,
  validateDisputeReason,
} from "./error-candidate-helpers";

const DEFAULT_BACKEND_URL = "http://localhost:8001";

const DEFAULT_NODE_PATH_PREFIXES = ["节点/"];

interface CanvasPluginSettings {
  backendUrl: string;
  /** Story 2.1 P1.6 — 节点池前缀（默认 ["节点/"]）。可在 data.json 配置多前缀。 */
  nodePathPrefixes: string[];
  /** DEAD (P0-3 2026-07-31): 唯一写方 vault selector dropdown 已随 runtime
   *  switch 退役下架, 现无任何读方。保留字段避免 data.json 反序列化 churn,
   *  随 Tier B 物理删除批次一并移除。 */
  activeVaultName: string;
  /** Wave-2 P0-1 (2026-05-12) — Internal API key for backend auth (X-CLS-Internal-Key)。
   *  空字符串 = dev mode (DEBUG=True 时 backend 跳过 auth middleware)。 */
  internalApiKey: string;
}

const DEFAULT_SETTINGS: CanvasPluginSettings = {
  backendUrl: DEFAULT_BACKEND_URL,
  nodePathPrefixes: [...DEFAULT_NODE_PATH_PREFIXES],
  activeVaultName: "",
  internalApiKey: "",
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
  /** MVP-α-5 (2026-05-14, 恢复自 f860f57): status bar 反馈瞬间 #2/#3 */
  private statusBar!: StatusBarController;
  /** MVP-α-3 (2026-05-14, 恢复自 f860f57): 单题考察 quick exam (反馈瞬间 #4/#5) */
  private quickExam!: QuickExamController;

  async onload() {
    await this.loadSettings();
    this.registerCanvasCommands();
    this.addSettingTab(new CanvasSettingTab(this.app, this));
    // Story 2.4 Plan A (2026-05-14): metadataCache.on('changed') → FrontmatterTipsSync
    // 用 Obsidian 内部 throttle 的 metadataCache 事件触发 frontmatter tips[] 自动维护
    // (vs Plan B 用 vault.on('modify') 容易跟自己写 frontmatter 形成循环)
    this.frontmatterSync = new FrontmatterTipsSync(this);

    // MVP-α-5 (2026-05-14, 恢复自 f860f57): status bar 反馈瞬间 #2/#3.
    // addStatusBarItem 在 plugin 实例上挂常驻 element, controller 持有它后只 setText.
    const statusBarEl = this.addStatusBarItem();
    this.statusBar = new StatusBarController(this, statusBarEl, {
      onTipsIncreased: (count) => {
        new Notice(buildTipsIncreaseNotice(count), 2500);
      },
    });

    // P10 修复 (2026-07-18): onLayoutReady 必须注册在 statusBar 初始化【之后】。
    // 布局已就绪时（运行中手动启用插件）Obsidian 会【同步立即】执行回调——
    // 旧版把本块放在 onload 开头, this.statusBar 尚未赋值 → TypeError →
    // 每次手动 enable 必崩（启动加载因回调延后执行而侥幸不崩, 潜伏两个月）。
    this.app.workspace.onLayoutReady(() => {
      this.checkHotkeyConflicts();
      // MVP-α-5 (恢复自 f860f57): 打开 Obsidian 时让 status bar 直接显示当前节点.
      const active = this.app.workspace.getActiveFile();
      if (active) this.statusBar.handleFileOpen(active);
    });

    this.registerEvent(
      this.app.metadataCache.on("changed", (file) => {
        if (file.path.startsWith("节点/") || file.path.startsWith("原白板/")) {
          this.masteryCache.clear();
          // Plan A core: 文件变化 → 重新解析 callout → 同步到 frontmatter tips[]
          void this.frontmatterSync.syncFile(file);
          // MVP-α-5: fan-out 到 statusBar 更新 Tips 计数
          this.statusBar.handleMetadataChanged(file);
        }
      }),
    );

    // MVP-α-5: workspace.on('file-open') → 更新 nav path "prev → current".
    this.registerEvent(
      this.app.workspace.on("file-open", (file) => {
        this.statusBar.handleFileOpen(file);
      }),
    );

    // MVP-α-3 (2026-05-14, 恢复自 f860f57): Quick Exam markdown UI (反馈瞬间 #4/#5).
    // controller 通过 closure 拿到 plugin 内的 callBackend + inferVaultId.
    // vault.on('modify') 在这里注册一个 fast-path 分发, controller 自己用 sessions
    // map 守门, 非考察文件 0 开销.
    this.quickExam = new QuickExamController({
      app: this.app,
      callBackendJson: (endpoint, label, body, method) =>
        this.callBackend(endpoint, label, body, method),
      inferCurrentVaultId: () =>
        inferVaultId(this.app.vault.getName(), undefined),
    });
    this.registerEvent(
      this.app.vault.on("modify", (file) => {
        if (file instanceof TFile) {
          void this.quickExam.onFileModified(file, Notice);
        }
      }),
    );

    // Story 2.4 Plan B Phase 1 (2026-05-14) — DEPRECATED 2026-05-14 路径 1 决策:
    // 4 方对抗审查 (Canvas / Claude / ChatGPT-1 / ChatGPT-2) 一致建议回退 Plan A。
    // 详见 _bmad-output/research/2026-05-14-plan-b-postmortem.md
    //
    // Plan C 复活 (2026-06-11, GRAPHITI-NATIVE-MEMORY 计划) — 7 盲点逐条对照:
    // #2 ghost field / #4 假 LRU / #7 顺序约束 → 已被 Graphiti-native 重构根治
    //   (统一 writer/reader 落 :Entity/RELATES_TO, 确定性边 uuid MERGE 幂等,
    //    直写 driver 不经 add_episode 队列); #1 协议 → F7 修列表嵌套解析;
    // #3 Notice 轰炸 → callBackend 新增 silent 参数, batch 全静默;
    // #5 cosmetic edit 版本噪声 → debounce 500→3000ms 缓解, 残留为已知项
    //   (编辑型批注的多版本本就是用户要的时序演化素材); #6 basename 身份 → 阶段取舍。
    // 作用: 用户在 callout 内续写"✍️ 我的理解"停笔 3s 后, 全文自动入个人记忆。
    this.calloutSync = new CalloutSyncDebouncer(this);
    this.registerEvent(
      this.app.vault.on("modify", (file) => {
        if (file instanceof TFile) {
          this.calloutSync.scheduleSync(file);
        }
      }),
    );
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
          // B2 (2026-07-12): tips 落当前 vault 桶, 不再进 vault:default
          vault_id: inferVaultId(this.app.vault.getName()),
          node_id: nodeId,
          callouts: callouts.map((c) => ({
            tag: c.tag,
            tag_label: c.tagLabel,
            understanding: c.understanding,
            content: c.content,
            content_hash: c.contentHash,
            annotation_id: c.annotationId, // P0: 批量通道也带稳定身份
          })),
          source_timestamp: new Date().toISOString(),
        },
        "POST",
        true, // 盲点#3: 后台同步全静默, 成功/失败都不弹 Notice
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
            "canvas-learning-system:canvas:start-examination",
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
    // 2026-07-10 S3 死命令清理(全景审计裁决):
    // - canvas:start-dialog 已删 —— 调用的 /api/v1/agents/dialog 后端不存在(必 404);
    //   节点对话走 canvas:open-node-chat,自由 RAG 对话在 Claudian 输 /chat-with-context。
    // - canvas:extract-concept 已删 —— 名实不符:选中文本被 /wikilink/build 静默丢弃,
    //   实际触发整库图重建;真正的概念提取 = canvas:ai-linked-doc(Cmd+Shift+D)。
    // - canvas:quiz-from-callout 已删 —— handleStartExaminationDirect 纯别名,零批注
    //   逻辑,且直调已被 B1-B4 裁决弃用的旧后端链;批注驱动考察 = /start-exam-board。
    this.addCommand({
      id: "canvas:start-examination",
      name: "启动考察（复制 /start-exam-board 命令）",
      callback: () => this.handleStartExaminationConfirm(),
    });

    this.addCommand({
      id: "canvas:open-dashboard",
      name: "打开 Dashboard.md",
      callback: () => this.handleOpenDashboard(),
    });

    // canvas:open-review-queue 已退役 (FSRS-V2-2026-07-30 Tier A): 其后端
    // /review/schedule 是永空幽灵端点。复习入口 = outputs/今日复习.md + 每日推送。

    this.addCommand({
      id: "canvas:annotate-callout",
      name: "批注为标注",
      callback: () => this.handleAnnotateCallout(),
    });

    // P7 (2026-07-16 UAT): "自发写新疑问"直插命令。annotate-callout 硬要求选中
    // 文本（选中式批注），检验白板答题中途冒出的新疑问只能纯手打 callout 格式 —
    // 格式门槛导致纯文本疑问被 /quiz-answer 归纳链静默丢弃。本命令在光标处直插
    // 空白 question callout。默认不绑键（用户在 设置→快捷键 搜"插入新疑问"自绑）。
    this.addCommand({
      id: "canvas:insert-question-callout",
      name: "插入新疑问（空白 question callout）",
      callback: () => this.handleInsertQuestionCallout(),
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

    // 轨道 B (2026-07-20) 过时文案清理: 原 canvas:start-examination-confirm
    // 已删 — "带 confirm 弹窗"名实不符 (M4 后不弹窗、直接复制命令) 且与
    // canvas:start-examination 完全同 handler。Dashboard 按钮已改指后者。
    this.addCommand({
      id: "canvas:open-node-chat",
      name: "节点对话（注入上下文 · 复制到 Claude Code）",
      callback: () => this.handleOpenNodeChat(),
    });

    // M4 吸收 (2026-07-13, 路线图 v2): Quick Exam 后端 Gemini 管道退役, 单节点
    // 定向考察并入检验白板全链 (/start-exam-board node 参数: 订阅出题+静默评分
    // +掌握度演化全复用, 且获得信息隔离保护)。本命令改引导范式 (与"启动考察"
    // 同款)。旧 quickExam 后端链代码保留作 UAT 回退保险, UAT 通过后一并摘除。
    this.addCommand({
      id: "canvas:start-quick-exam",
      name: "Quick Exam（单节点定向考察 · 复制 /start-exam-board node 命令）",
      callback: () => this.handleQuickExamAbsorbed(),
    });

    // 方案 A (轨道 B 2026-07-20, 用户拍板决策点 3) — P13 修复: 原「接受」
    // 「异议」两条命令合并为一条「复盘错误候选」。active file 无候选时
    // 自动全库扫 节点/ (Dashboard 上触发不再报"没有待处理")。流程:
    // 选候选 → 选处理方式 (✅ 接受 / ⚠️ 异议) → 后端双写 frontmatter +
    // 正文三态卡片原地变态。
    this.addCommand({
      id: "canvas:review-error-candidate",
      name: "复盘错误候选（接受 / 异议）",
      callback: () => this.handleReviewErrorCandidate(),
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
      `已复制节点 "${activeFile.basename}" 上下文（${sizeKb}KB / ${neighbors.length} 邻居）${truncatedHint}\n切到 Claude Code 窗口粘贴即可触发对话`,
      6000,
    );

    // 轨道 B (2026-07-20) D-1 文案收敛: 主路径 = Claude Code 原生窗口粘贴,
    // Claudian 侧栏仅在已安装时顺手打开 (缺席不再报错阻断)。
    const claudianCmd = (this.app as any).commands?.findCommand?.(
      "claudian:open-view",
    );
    if (claudianCmd) {
      (this.app as any).commands.executeCommandById("claudian:open-view");
    }
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
    // 检验白板 v1（诚实版）：不再调旧后端 /api/v1/exam/start（熟练度管道 B1-B4 断裂，
    // 调必失败）。改为复制 /start-exam-board 命令，引导用户走 Claude Code Skill 路径。
    const activeFile = this.app.workspace.getActiveFile();
    const cmd = activeFile?.path.startsWith("原白板/")
      ? `/start-exam-board from ${activeFile.basename}`
      : "/start-exam-board";
    void navigator.clipboard.writeText(cmd);
    new Notice(
      `已复制：${cmd}\n切到 Claude Code 窗口粘贴执行。`,
      8000,
    );
  }

  /**
   * M4 吸收 (2026-07-13 路线图 v2)：Quick Exam → 检验白板单节点定向考察。
   *
   * 引导范式：active file 须在 节点/ 下 → 读 frontmatter source_board 定
   * 所属原白板 → 复制 `/start-exam-board from <板> node <节点>` + 提示去
   * Claude Code 粘贴。出题/评分全走订阅（Skill 链），不再调后端 Gemini。
   */
  private handleQuickExamAbsorbed() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile || !activeFile.path.startsWith("节点/")) {
      new Notice("请先打开 节点/ 下的概念节点文件，再触发单节点定向考察");
      return;
    }
    const concept = activeFile.basename;
    const fm = this.app.metadataCache.getFileCache(activeFile)?.frontmatter;
    // source_board 形如 "[[原白板/特征值与特征向量]]" — 抽 stem
    const rawBoard: string = fm?.source_board ?? "";
    const boardMatch = /\[\[(?:原白板\/)?([^\]|]+?)\]\]/.exec(rawBoard);
    const boardStem = boardMatch?.[1]?.trim();
    const cmd = boardStem
      ? `/start-exam-board from ${boardStem} node ${concept}`
      : `/start-exam-board node ${concept}`;
    void navigator.clipboard.writeText(cmd);
    new Notice(
      `已复制：${cmd}\n切到 Claude Code 窗口粘贴执行——出题引用你的批注、答完 /quiz-answer 静默评分并演化掌握度。`,
      8000,
    );
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

    if (
      !activeBoard &&
      (isNodesPath(sourcePath) || isExamBoardPath(sourcePath)) &&
      activeFile
    ) {
      const cache = this.app.metadataCache.getFileCache(activeFile);
      const inherited = extractSourceBoardFromFrontmatter(
        cache?.frontmatter as Record<string, unknown> | undefined,
      );
      if (inherited) {
        activeBoard = inherited;
        const originLabel = isExamBoardPath(sourcePath)
          ? "检验白板疑问派生"
          : "源节点";
        new Notice(
          `继承${originLabel}白板归属：${inherited}（自动）`,
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
    let sourceNoteStem = args.activeFile.basename;

    let activeBoard = args.activeBoard;
    if (!activeBoard) {
      const examHint = isExamBoardPath(args.sourcePath)
        ? "若在检验白板内派生，请确认其 frontmatter 含 source_board: \"[[原白板/<名>]]\"（由 /start-exam-board 自动写入）。"
        : "请先在节点继承的笔记或原白板内派生。";
      new Notice(
        `❌ 未确定活动白板：当前笔记 ${args.sourcePath} 不是白板路径也无 source_board frontmatter。${examHint}`,
        7000,
      );
      return;
    }

    // 检验白板派生（交付3 · 设计 §三轮①）：疑问节点应挂到"被考的原节点"，而非瞬态
    // 检验白板会话文件。从检验白板 frontmatter 的 selected_node 读被考节点，令其成为疑问
    // 节点的 source_note / up / derived-from / relationships.target 及入图 target。
    // description 仍来自用户 modal（书签意图）；AI 判断的因果原因由 /quiz-answer 路径②回填。
    // selected_node 缺失/被考节点不存在 → 硬失败（静默回退到检验白板文件名会造成错链：
    // 疑问节点挂到瞬态考试文件，知识图谱与 Dataview 全被污染）。
    if (isExamBoardPath(args.sourcePath)) {
      const cache = this.app.metadataCache.getFileCache(args.activeFile);
      const examined = cache?.frontmatter?.selected_node;
      if (typeof examined !== "string" || !examined.trim()) {
        new Notice(
          "❌ 检验白板缺 selected_node，无法判断疑问源自哪个被考原节点。请用 /start-exam-board 重新生成检验白板。",
          8000,
        );
        return;
      }
      const examinedStem = examined.trim();
      if (!this.app.vault.getAbstractFileByPath(`节点/${examinedStem}.md`)) {
        new Notice(`❌ 被考原节点不存在：节点/${examinedStem}.md`, 8000);
        return;
      }
      sourceNoteStem = examinedStem;
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

    // 批次4' 3-1 (MEM-FLYWHEEL): 派生时刻理解快照 — 源节点当时的掌握档 +
    // 选区附近最近一条疑问/错误批注 (「当时为什么困惑」永久留档)。
    // 快照取材失败不阻断派生 (留空即可, 投影 sync 对缺省字段做 coalesce)。
    let sourceMastery: number | null = null;
    let confusion: string | null = null;
    try {
      const snapshotFile =
        sourceNoteStem === args.activeFile.basename
          ? args.activeFile
          : (this.app.vault.getAbstractFileByPath(
              `节点/${sourceNoteStem}.md`,
            ) as TFile | null);
      if (snapshotFile) {
        const fmCache =
          this.app.metadataCache.getFileCache(snapshotFile)?.frontmatter;
        const rawMastery =
          fmCache?.mastery_score ?? fmCache?.mastery ?? fmCache?.mastery_level;
        if (rawMastery !== undefined && rawMastery !== null) {
          const parsed = Number(rawMastery);
          if (Number.isFinite(parsed)) sourceMastery = parsed;
        }
      }
      const sourceContent = await this.app.vault.read(args.activeFile);
      confusion = extractNearbyConfusion(sourceContent, args.selected);
    } catch {
      // 快照是增强信息, 静默降级
    }

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
          sourceMastery,
          confusion,
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

    // P4 (X1): 实时上报派生关系原因 → Graphiti (Graphiti-native, 不必等启动回填)。
    // 派生节点(conceptName)持有 frontmatter relationship 指向源节点(sourceNoteStem),
    // 故出边源=conceptName, target=sourceNoteStem。失败非致命(回填兜底)。
    void this.saveRelationToBackend(
      conceptName,
      sourceNoteStem,
      args.relationKey,
      args.description,
    );

    // 批次3'/4' (MEM-FLYWHEEL): node_derived 学习事件 → vault 根
    // learning_events.jsonl (append-only + event_id 幂等)。失败不阻断派生。
    try {
      const { eventId, line } = buildNodeDerivedEventLine(
        conceptName,
        createdAt,
      );
      const evPath = "learning_events.jsonl";
      const adapter = this.app.vault.adapter;
      let seen = false;
      if (await adapter.exists(evPath)) {
        const existing = await adapter.read(evPath);
        seen = existing.includes(JSON.stringify(eventId));
      }
      if (!seen) {
        await adapter.append(evPath, line);
      }
    } catch {
      // 事件日志是兜底记录, 静默降级
    }

    const elapsedMs = Date.now() - t0;
    new Notice(
      `✓ 派生完成 [[节点/${conceptName}]]（${elapsedMs}ms）。新节点已开 — 在三段空白处写下你的理解，或在 Claude Code 里围绕本节点对话。`,
      8000,
    );
  }

  /**
   * P4 (A+-prime): 派生关系原因实时上报 → POST /api/v1/tips/relation →
   * record_knowledge_entity(node_derived) → write_relation_reason (Graphiti-native)。
   * 修 X1: 用户写下"为什么拉出"后不必重启后端即可被针对性考察读回。
   */
  public async saveRelationToBackend(
    sourceNodeId: string,
    targetNodeId: string,
    relationType: string,
    reason: string,
  ): Promise<void> {
    try {
      await this.callBackend(
        "/api/v1/tips/relation",
        "派生关系同步",
        {
          // B2 (2026-07-12): tips 落当前 vault 桶
          vault_id: inferVaultId(this.app.vault.getName()),
          source_node_id: sourceNodeId,
          target_node_id: targetNodeId,
          relation_type: relationType,
          reason,
          source_timestamp: new Date().toISOString(),
        },
        "POST",
        true, // 静默: 失败有回填兜底, 不打扰派生流程
      );
    } catch {
      // 静默 — 实时上报失败由启动回填兜底
    }
  }

  /**
   * P7 (2026-07-16 UAT): 自发新疑问直插 — 与选中式批注（handleAnnotateCallout）
   * 互补，无需选中文本。在光标处插入空白 question callout，光标自动停在
   * "> ✍️ 我的疑问：" 之后直接打字（P0-6 同款体验）。
   *
   * 产出格式兼容：/quiz-answer 归纳 Grep + /start-exam-board 安全抽取器 +
   * parseCalloutsFromContent（含 %%cb-xxx%% 稳定身份）。捕获路径按落点分工：
   * 节点/、原白板/ 走 callout-sync 停笔回填；检验白板/ 不在 sync 前缀白名单内，
   * 由 /quiz-answer 离线归纳兜底（本 handler 自身不做任何后端上报）。
   */
  private handleInsertQuestionCallout() {
    const editor = this.app.workspace.activeEditor?.editor;
    if (!editor) {
      new Notice("编辑器未激活");
      return;
    }
    const cursor = editor.getCursor();

    // MEDIUM-1 (Code-Review 2026-07-16): 劈块防护 — 光标在 callout/引用块内部时
    // 直插会把原批注拦腰劈开（尾行沦为无头 blockquote，且截断触发 sync 虚假 v2）。
    // 锚点下移到引用块最后一行，在块外插入。
    let anchor = cursor.line;
    if (editor.getLine(anchor).trimStart().startsWith(">")) {
      while (
        anchor + 1 < editor.lineCount() &&
        editor.getLine(anchor + 1).trimStart().startsWith(">")
      ) {
        anchor++;
      }
    }

    const currentLine = editor.getLine(anchor);
    const prevLine = anchor > 0 ? editor.getLine(anchor - 1) : "";
    const nextLine =
      anchor + 1 < editor.lineCount() ? editor.getLine(anchor + 1) : "";
    const { lead, tail } = computeInsertionSpacing(
      currentLine,
      prevLine,
      nextLine,
    );

    const block = buildNewQuestionCallout(generateAnnotationId());
    // 空白行（含纯空格/Tab 行）整行替换，防止残留缩进把 ">" 变成 code block；
    // 非空行从行尾追加。
    const isBlankLine = currentLine.trim() === "";
    editor.replaceRange(
      `${lead}${block}${tail}`,
      { line: anchor, ch: isBlankLine ? 0 : currentLine.length },
      isBlankLine ? { line: anchor, ch: currentLine.length } : undefined,
    );

    // lead 只含 "\n"（条数 = anchor 行之后的新增行数）→ prompt 行 = anchor + lead 数 + 1
    editor.setCursor({
      line: anchor + lead.length + 1,
      ch: NEW_QUESTION_PROMPT.length,
    });
    editor.focus();
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
    annotationId?: string,
  ): Promise<void> {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      return;
    }
    const nodeId = activeFile.basename;
    const body = {
      // B2 (2026-07-12): tips 落当前 vault 桶
      vault_id: inferVaultId(this.app.vault.getName()),
      content: selected,
      title: `${tag.label} · ${nodeId}`,
      tags: [`tag:${tag.value}`, `understanding:${understanding}`],
      node_id: nodeId,
      // P0 (A+-prime): 稳定逻辑身份, 后端 write_callout 用它而非首行做 identity
      annotation_id: annotationId ?? "",
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
   * T5 (2026-07-10) — Story 2.5.X AC #5/#7: 错误候选 accept/dispute。
   *
   * 流程: 活动文件 frontmatter error_candidates[] → filterPending →
   * FuzzySuggestModal 选一条 → (dispute 再收理由) → POST 带 key →
   * 后端直接改 md frontmatter (accept 移入 errors[] + Graphiti;
   * dispute 标 disputed), plugin 不重复写文件。
   */
  private async handleReviewErrorCandidate(): Promise<void> {
    // 方案 A + P13 (轨道 B 2026-07-20): active file 优先, 无候选自动
    // 全库扫 节点/ (metadataCache 范式照抄 getMasteryBatch) — 在
    // Dashboard 页面上触发也能列出全部待复盘候选, 消除循环跳转。
    const collect = (file: TFile): ReviewCandidateItem[] => {
      const fm = this.app.metadataCache.getFileCache(file)?.frontmatter;
      return filterPendingCandidates(fm?.error_candidates).map(
        (candidate) => ({ candidate, file }),
      );
    };
    const active = this.app.workspace.getActiveFile();
    let items: ReviewCandidateItem[] = active ? collect(active) : [];
    if (items.length === 0) {
      items = this.app.vault
        .getMarkdownFiles()
        .filter((f) => f.path.startsWith("节点/"))
        .flatMap(collect);
    }
    if (items.length === 0) {
      new Notice("全库没有待处理的错误候选 ✅");
      return;
    }

    const chosen = await new Promise<ReviewCandidateItem | null>((resolve) => {
      new ErrorCandidateSuggestModal(this.app, items, resolve).open();
    });
    if (!chosen) return;

    const action = await new Promise<"accept" | "dispute" | null>((resolve) => {
      new ReviewActionModal(this.app, chosen, resolve).open();
    });
    if (!action) return;

    const vaultId = inferVaultId(this.app.vault.getName());
    const nodeId = chosen.file.path; // 端点契约: vault-relative path

    if (action === "accept") {
      const result = await this.callBackend(
        "/api/v1/errors/accept-candidate",
        "复盘错误候选",
        buildAcceptPayload(chosen.candidate.id, nodeId, { vaultId }),
      );
      if (result) {
        new Notice(
          `✅ 候选已接受并移入 errors[]，节点里的卡片已变为「已确认」（Graphiti 后台同步中）`,
          5000,
        );
      }
      return;
    }

    const reason = await new Promise<string | null>((resolve) => {
      new DisputeReasonModal(this.app, resolve).open();
    });
    if (reason === null) return;
    const check = validateDisputeReason(reason);
    if (!check.valid) {
      new Notice(`异议理由无效: ${check.error}`);
      return;
    }
    const result = await this.callBackend(
      "/api/v1/errors/dispute-candidate",
      "复盘错误候选",
      buildDisputePayload(chosen.candidate.id, nodeId, reason.trim(), {
        vaultId,
      }),
    );
    if (result) {
      new Notice(
        "✅ 已标记 disputed，节点里的卡片已变为「已异议」（不入 errors[]，理由已记录）",
        5000,
      );
    }
  }

  /**
   * Story 1.4 AC #4 / Story 1.18 路径 B 修复 · v4.3：
   *   - 显式 method 参数（exam.start 是 POST 但 review.schedule 是 GET）
   *   - 解析返回体（JSON 或 text）让 Notice 显示有用信息
   *   - 用 settings.backendUrl（不再写死 localhost）
   */
  // 批次5' (MEM-FLYWHEEL): FrontmatterTipsSync 的批注直连需要复用统一请求
  // helper (key/silent/错误处理) — private → public
  public async callBackend(
    endpoint: string,
    label: string,
    body?: any,
    method: "GET" | "POST" | "PUT" | "DELETE" = body ? "POST" : "GET",
    silent = false, // 盲点#3: 后台 debounce 同步用静默传输, 不弹 Notice 轰炸
  ): Promise<unknown | null> {
    const url = `${this.settings.backendUrl}${endpoint}`;
    try {
      const resp = await fetch(url, {
        method,
        headers: {
          ...(body ? { "Content-Type": "application/json" } : {}),
          ...(this.settings.internalApiKey
            ? { "X-CLS-Internal-Key": this.settings.internalApiKey }
            : {}),
        },
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
        if (silent) {
          console.warn(`[canvas] ${label} 失败: ${detail}`);
        } else {
          new Notice(`${label} 失败: ${detail}`, 6000);
        }
        return null;
      }
      if (!silent) {
        const summary =
          (parsed as any)?.id ||
          (parsed as any)?.exam_id ||
          (parsed as any)?.total_count !== undefined
            ? `${label} 成功 · 共 ${(parsed as any).total_count} 项`
            : `${label} 成功`;
        new Notice(summary, 4000);
      }
      return parsed;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (silent) {
        console.warn(`[canvas] ${label} 失败: 后端未连接（${msg}）`);
      } else {
        new Notice(
          `${label} 失败: 后端未连接（${msg}）\n请先 docker compose up 启动 Canvas 后端`,
          6000,
        );
      }
      return null;
    }
  }

  // 2026-07-10 S3: handleStartExaminationDirect 已删 —— 直调 /api/v1/exam/start 属
  // B1-B4 裁决弃用的旧后端考察链;canvas:start-examination 现与 confirm 版同走
  // handleStartExaminationConfirm(复制 /start-exam-board 命令,v1 检验白板路径)。

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

    // ─── 状态卡：当前 vault 是否被 backend 认识 ─────────────────
    // 用户视角第一眼看到「✓ 已挂载 / ⚠️ 不匹配 / ❌ 后端未启动」+ 一键修复
    this.renderVaultStatus(containerEl);

    // ─── 快捷键状态 + 导航（Story 2.1 Phase 1 P1.6 — UX 改进） ──────
    this.renderHotkeyStatus(containerEl);

    // ─── 高级配置（折叠，默认收起；非技术用户无需展开） ────────────
    this.renderAdvancedSection(containerEl);
  }

  /**
   * Story 2.2 follow-up · vault status detector（用户视角主入口）
   *
   * 用户原话："我只是要确认当前的 Canvas Learning System 是否挂载在当前 vault"
   * 设计：状态卡先行 — 进 Settings 第一眼看到「✓ 已挂载 / ⚠️ 不匹配 / ❌ 后端未启动」
   * 三态都给恰好一个 CTA（重连 / 一键切换 / 重试），零端口暴露。
   * 路径不可对比（host vs container 不同 namespace），改用 vault_name 作 stable key。
   */
  private renderVaultStatus(container: HTMLElement): void {
    const card = container.createDiv({ cls: "canvas-vault-status-card" });
    card.style.cssText = "padding: 16px; margin: 12px 0; border-radius: 8px; "
      + "background: var(--background-secondary); border: 1px solid var(--background-modifier-border);";
    card.createEl("h3", { text: "Canvas 后端状态", attr: { style: "margin: 0 0 8px 0;" } });
    const bodyEl = card.createDiv();
    bodyEl.setText("正在检查后端连通性...");
    const ctaEl = card.createDiv({ attr: { style: "margin-top: 12px;" } });

    void this.detectAndRender(bodyEl, ctaEl);
  }

  /**
   * 异步检测 Obsidian 当前 vault ↔ backend active vault 是否同源，并渲染状态。
   * 直接调用 backend /api/v1/vault/current 拿 source-of-truth，按 vault_name 比对。
   */
  private async detectAndRender(bodyEl: HTMLElement, ctaEl: HTMLElement): Promise<void> {
    const localName = this.app.vault.getName();
    const backendUrl = this.plugin.settings.backendUrl.replace(/\/$/, "");

    let resp;
    try {
      resp = await requestUrl({
        url: `${backendUrl}/api/v1/vault/current`,
        method: "GET",
        throw: false,
      });
    } catch (e) {
      this.renderBackendDownState(bodyEl, ctaEl, localName, backendUrl, (e as Error).message);
      return;
    }

    if (resp.status !== 200) {
      this.renderBackendDownState(bodyEl, ctaEl, localName, backendUrl, `HTTP ${resp.status}`);
      return;
    }

    const remote = resp.json as { vault_name: string; vault_path: string; vault_id: string };
    if (remote.vault_name === localName) {
      this.renderSyncedState(bodyEl, ctaEl, localName, remote.vault_id);
    } else {
      this.renderMismatchState(bodyEl, ctaEl, localName, remote);
    }
  }

  private renderSyncedState(
    bodyEl: HTMLElement,
    ctaEl: HTMLElement,
    localName: string,
    vaultId: string,
  ): void {
    bodyEl.empty();
    bodyEl.createSpan({
      text: "✓ Canvas 已挂载当前 vault",
      attr: { style: "color: var(--text-success); font-weight: 600;" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: `当前 vault：「${localName}」  ·  vault_id: ${vaultId}`,
      attr: { style: "color: var(--text-muted); font-size: 0.9em;" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: "你可以放心使用所有 Canvas 功能（AI 对话 / 双链派生 / 检验白板等）。",
      attr: { style: "color: var(--text-muted); font-size: 0.9em;" },
    });
    ctaEl.empty();
  }

  private renderMismatchState(
    bodyEl: HTMLElement,
    ctaEl: HTMLElement,
    localName: string,
    remote: { vault_name: string; vault_path: string; vault_id: string },
  ): void {
    bodyEl.empty();
    bodyEl.createSpan({
      text: "⚠️ Vault 不匹配 — Canvas 当前不在这个 vault",
      attr: { style: "color: var(--text-warning); font-weight: 600;" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: `Obsidian 当前打开：「${localName}」`,
      attr: { style: "font-size: 0.9em;" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: `Canvas 后端挂载在：「${remote.vault_name}」（${remote.vault_path}）`,
      attr: { style: "font-size: 0.9em; color: var(--text-muted);" },
    });

    // P0-3 (2026-07-31): 一键切换 CTA 下架 — /api/v1/vault/switch 改可变全局
    // Settings, 并发请求会 mid-flight 串 vault (端点已隔离返回 410)。
    // vault 改为部署期固定, 切换走 .env + docker compose。
    ctaEl.empty();
    const hint = ctaEl.createDiv();
    hint.style.cssText = "font-size: 0.9em; color: var(--text-muted); max-width: 480px;";
    hint.setText(
      "运行时切换已退役（防并发串库）。如需让 Canvas 挂载本 vault：编辑项目 .env 的 "
      + "ACTIVE_VAULT=<本 vault 目录名>（须在 VAULTS_ROOT 下），"
      + "然后在终端运行 docker compose up -d backend。",
    );
    const retryBtn = ctaEl.createEl("button", { text: "重新检查" });
    retryBtn.style.cssText = "margin-top: 6px; padding: 6px 14px; cursor: pointer;";
    retryBtn.onclick = () => {
      bodyEl.setText("正在重新检查...");
      ctaEl.empty();
      void this.detectAndRender(bodyEl, ctaEl);
    };
  }

  private renderBackendDownState(
    bodyEl: HTMLElement,
    ctaEl: HTMLElement,
    localName: string,
    backendUrl: string,
    reason: string,
  ): void {
    bodyEl.empty();
    bodyEl.createSpan({
      text: "❌ Canvas 后端未启动",
      attr: { style: "color: var(--text-error); font-weight: 600;" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: `无法连接 ${backendUrl}（${reason}）。Obsidian 当前 vault：「${localName}」`,
      attr: { style: "font-size: 0.9em; color: var(--text-muted);" },
    });
    bodyEl.createEl("br");
    bodyEl.createSpan({
      text: "请检查 Docker 是否运行（终端：docker ps），或在「高级」段修改 Backend URL。",
      attr: { style: "font-size: 0.9em; color: var(--text-muted);" },
    });

    ctaEl.empty();
    const retryBtn = ctaEl.createEl("button", { text: "重新检查" });
    retryBtn.style.cssText = "padding: 6px 14px; cursor: pointer;";
    retryBtn.onclick = () => {
      bodyEl.setText("正在重新检查...");
      ctaEl.empty();
      void this.detectAndRender(bodyEl, ctaEl);
    };
  }

  /**
   * 高级配置折叠段（默认收起）— 含 BackendURL / 节点前缀 / vault 只读状态
   * 非技术用户无需展开；进阶用户可手动调整 BackendURL、改节点池前缀
   */
  private renderAdvancedSection(container: HTMLElement): void {
    const details = container.createEl("details");
    details.createEl("summary", { text: "▸ 高级配置（端口 / 节点前缀 / 显式 vault 切换）" });
    const inner = details.createDiv({ attr: { style: "padding: 8px 0 0 16px;" } });

    new Setting(inner)
      .setName("Backend URL")
      .setDesc("FastAPI 后端 URL（默认 http://localhost:8011 — docker host 映射端口）")
      .addText((text) =>
        text
          .setPlaceholder(DEFAULT_BACKEND_URL)
          .setValue(this.plugin.settings.backendUrl)
          .onChange(async (value) => {
            this.plugin.settings.backendUrl = value || DEFAULT_BACKEND_URL;
            await this.plugin.saveSettings();
          }),
      );

    // Wave-2 P0-1 (2026-05-12) — Internal API Key 配置
    // 生产 env (DEBUG=False + backend INTERNAL_API_KEY 配置) 必须填，否则 4 命令全部 403。
    // dev env (DEBUG=True) 留空即可，backend 跳过 auth middleware。
    new Setting(inner)
      .setName("Internal API Key (X-CLS-Internal-Key)")
      .setDesc(
        "生产环境 (DEBUG=False) 必填 — 与 backend 的 INTERNAL_API_KEY env 保持一致。"
        + "留空 = dev mode (DEBUG=True, backend 跳过 auth)。"
        + "Wave-2 P0-1 修复: 之前 3 命令 (chat / study / node-chat) 全部漏带此 header → 生产 403。",
      )
      .addText((text) =>
        text
          .setPlaceholder("(留空 = dev mode)")
          .setValue(this.plugin.settings.internalApiKey)
          .onChange(async (value) => {
            this.plugin.settings.internalApiKey = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(inner)
      .setName("节点路径前缀")
      .setDesc('识别「节点池」的目录前缀（JSON 数组）。默认 ["节点/"]。英文 vault 可改 ["Nodes/"]')
      .addText((text) =>
        text
          .setPlaceholder('["节点/"]')
          .setValue(JSON.stringify(this.plugin.settings.nodePathPrefixes))
          .onChange(async (value) => {
            try {
              const parsed = JSON.parse(value);
              if (
                Array.isArray(parsed)
                && parsed.every((p) => typeof p === "string" && p.length > 0)
              ) {
                this.plugin.settings.nodePathPrefixes = parsed;
                await this.plugin.saveSettings();
              } else {
                new Notice("❌ 需要非空字符串数组（如 [\"节点/\"]）", 4000);
              }
            } catch {
              new Notice("❌ JSON 格式错误", 4000);
            }
          }),
      );

    // P0-3: 老 vault switch dropdown 下架 (后端 /vault/switch 已隔离 410),
    // 折叠段保留只读的 vault 挂载状态展示
    this.renderVaultMountStatus(inner);
  }

  /**
   * P0-3 (2026-07-31) · vault 挂载只读状态（原 vault selector dropdown 下架）
   *
   * 异步从 backend /api/v1/vault/list 拿候选列表（VAULTS_ROOT 下含 .obsidian/ 的目录），
   * 只读展示当前挂载 vault 与候选清单。运行时切换已退役（防并发串库），
   * 切换 = 编辑 .env CANVAS_BASE_PATH + docker compose up -d backend。
   */
  private renderVaultMountStatus(container: HTMLElement): void {
    new Setting(container)
      .setName("当前挂载 Vault（只读）")
      .setDesc(
        "backend 当前挂载的 vault 由部署期 .env 的 ACTIVE_VAULT 固定。"
        + "如需切换：改 .env 的 ACTIVE_VAULT=<vault 目录名> 后运行 docker compose up -d backend。",
      );
    const statusEl = container.createEl("p", {
      text: "正在加载 vault 状态...",
      cls: "setting-item-description",
    });
    statusEl.style.whiteSpace = "pre-line";

    void (async () => {
      try {
        const url = `${this.plugin.settings.backendUrl.replace(/\/$/, "")}/api/v1/vault/list`;
        const resp = await requestUrl({
          url,
          method: "GET",
          throw: false,
        });
        if (resp.status !== 200) {
          statusEl.setText(
            `❌ 无法加载 vault 状态 (HTTP ${resp.status}). 请确认 backend 正在运行 + Backend URL 正确。`,
          );
          return;
        }
        const data = resp.json as {
          vaults_root: string;
          active_vault: string;
          vaults: { name: string; path: string; vault_id: string; is_active: boolean }[];
        };
        if (!Array.isArray(data.vaults) || data.vaults.length === 0) {
          statusEl.setText(
            `⚠️ VAULTS_ROOT (${data.vaults_root}) 下未发现含 .obsidian/ 的目录。`,
          );
          return;
        }
        const lines = data.vaults.map(
          (v) => `${v.is_active ? "● " : "○ "}${v.name} (${v.vault_id})`,
        );
        statusEl.setText(
          `当前挂载: ${data.active_vault} · VAULTS_ROOT: ${data.vaults_root}\n${lines.join("\n")}`,
        );
      } catch (e) {
        statusEl.setText(`❌ 加载 vault 状态异常：${(e as Error).message}`);
      }
    })();
  }

  /**
   * Story 2.1 Phase 1 P1.6 — 快捷键状态导航段
   *
   * 不在 plugin SettingTab 内造 hotkey UI（违 Obsidian 社区惯例）。
   * 仅显示当前绑定状态 + 一键跳转到全局 Hotkeys 设置页。
   */
  private renderHotkeyStatus(container: HTMLElement): void {
    const section = container.createDiv({ cls: "canvas-hotkey-status" });
    section.createEl("h3", { text: "⌨️ 快捷键绑定" });
    section.createEl("p", {
      text: "Obsidian 设计：所有命令的快捷键统一在「Settings → 快捷键」全局管理。本插件命令默认未绑定，请按需自定义。",
      cls: "setting-item-description",
    });

    // 收集本插件命令 + 当前绑定状态
    const PLUGIN_PREFIX = "canvas-learning-system:";
    const allCommands = (this.app as any).commands?.commands ?? {};
    const hotkeyMgr = (this.app as any).hotkeyManager;
    const customKeys = hotkeyMgr?.customKeys ?? {};
    const defaultKeys = hotkeyMgr?.defaultKeys ?? {};

    const pluginCmds = Object.keys(allCommands)
      .filter((id) => id.startsWith(PLUGIN_PREFIX))
      .sort();

    let boundCount = 0;
    const formatHotkey = (h: any): string => {
      if (!h) return "";
      const mods = (h.modifiers ?? []).join("+");
      return mods ? `${mods}+${h.key}` : h.key;
    };

    const list = section.createEl("ul", { cls: "canvas-hotkey-list" });
    for (const cmdId of pluginCmds) {
      const name = allCommands[cmdId]?.name ?? cmdId;
      const keys = customKeys[cmdId] ?? defaultKeys[cmdId] ?? [];
      const bound = Array.isArray(keys) && keys.length > 0;
      if (bound) boundCount++;
      const li = list.createEl("li");
      li.createEl("span", {
        text: bound ? "✅ " : "⚠️ ",
      });
      li.createEl("strong", { text: name });
      li.createEl("span", {
        text: bound
          ? `  [${keys.map(formatHotkey).join(", ")}]`
          : "  （未绑定）",
        cls: bound ? "" : "mod-warning",
      });
    }

    const summary = section.createEl("p", {
      cls: "setting-item-description",
    });
    summary.createEl("strong", {
      text: boundCount === pluginCmds.length
        ? `✅ 已绑定 ${boundCount}/${pluginCmds.length} 个命令`
        : `⚠️ ${pluginCmds.length - boundCount} 个命令未绑定快捷键`,
    });

    new Setting(section)
      .setName("配置快捷键")
      .setDesc("跳转到 Obsidian「Settings → 快捷键」并自动搜索 canvas-learning-system 命令。")
      .addButton((btn) =>
        btn
          .setButtonText("打开快捷键设置")
          .setCta()
          .onClick(() => {
            const setting = (this.app as any).setting;
            if (!setting) {
              new Notice("无法打开设置页", 3000);
              return;
            }
            setting.open();
            setting.openTabById("hotkeys");
            // 多候选 selector + 重试，应对不同 Obsidian 版本的 DOM 结构
            const trySetSearch = (attempts = 0): void => {
              const candidates = [
                ".hotkey-list-search-container input",
                "input.hotkey-list-search-input",
                ".search-input-container input[type=\"search\"]",
                ".vertical-tab-content-container input[type=\"text\"]",
                ".vertical-tab-content-container input[type=\"search\"]",
              ];
              for (const sel of candidates) {
                const el = document.querySelector(sel) as HTMLInputElement | null;
                if (el && el.offsetParent !== null) {
                  el.focus();
                  el.value = "canvas-learning-system";
                  el.dispatchEvent(new Event("input", { bubbles: true }));
                  return;
                }
              }
              if (attempts < 10) {
                setTimeout(() => trySetSearch(attempts + 1), 100);
              }
            };
            trySetSearch();
          }),
      );
  }
}

/**
 * Story 1.19 v4.0 — 白板名输入 modal（无 LLM）。
 *
 * 默认值启发式：场景 A 留空让用户输；场景 B 用 active file basename 作 placeholder
 * （但不预填，避免误用同名 — 用户应主动思考白板名是否与种子笔记一致）。
 */


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
    // P0 (A+-prime): 生成稳定批注 id，同时嵌入 callout 标题 + 随实时上报发送，
    // 保证即时上报与停笔回填两条通道指向同一逻辑身份。
    const annotationId = generateAnnotationId();
    // 1) 本地写入 callout
    const from = this.editor.getCursor("from");
    const to = this.editor.getCursor("to");
    const wrapped = wrapSelection(this.selected, this.tag, und.value, annotationId);
    // 2026-07-25 (UAT ⑧): 行内选区时补换行包裹 — callout 是块级语法, 粘进
    // 句子中间会渲染碎裂且同步器解析不到 (详见 callout.ts padBlockInsert)
    const padded = padBlockInsert(
      wrapped,
      from.ch,
      this.editor.getLine(to.line).slice(to.ch),
    );
    this.editor.replaceSelection(padded.text);

    // 2) P0-6 (2026-05-14): 光标自动定位到 callout 末尾用户输入区
    // wrapped 最后一行是 "> "（USER_INPUT_PROMPT），光标停在 ch=2 让用户直接输入。
    // 这样用户做完 tag + understanding 选择后，自然继续打字写下自己的理解 / 疑问 /
    // 批注，无需额外 modal，符合 Obsidian native UX。
    const wrappedLines = wrapped.split("\n");
    const targetLine =
      from.line + padded.leadingNewlines + wrappedLines.length - 1;
    const targetCh = USER_INPUT_PROMPT.length; // "> " 后面
    this.editor.setCursor({ line: targetLine, ch: targetCh });
    this.editor.focus();

    // 3) 实时同步到个人记忆 (RE-ENABLED 2026-06-11, GRAPHITI-NATIVE-MEMORY 计划):
    // P0-1 曾于 2026-05-14 废弃 (plan-b postmortem) — 但该决策前提是"后端管道
    // G-FAKE 断裂, POST 了也进不了记忆"。2026-06-10 后端已重构为 Graphiti-native
    // (memory_service 结构化路由 → :Entity/RELATES_TO, e2e 10/10 验证), 前提失效。
    // 恢复实时 POST = 用户批注即刻进时序记忆 (用户核心诉求: 打批注→读回原话)。
    // 失败非致命 (callBackend 内部 Notice), vault 回填脚本兜底离线场景。
    void this.plugin.saveCalloutToBackend(
      this.selected,
      this.tag,
      und.value as UnderstandingValue,
      annotationId,
    );
  }
}

/**
 * T5 (2026-07-10) — Story 2.5.X: 错误候选选择 Modal。
 *
 * resolve(null) 覆盖用户 Esc 关闭 (onClose 时未选择则视为取消)。
 */
/** 方案 A (轨道 B 2026-07-20): 全库化后候选须携带来源节点。 */
interface ReviewCandidateItem {
  candidate: ErrorCandidate;
  file: TFile;
}

class ErrorCandidateSuggestModal extends FuzzySuggestModal<ReviewCandidateItem> {
  private chosen = false;

  constructor(
    app: App,
    private items: ReviewCandidateItem[],
    private onResolve: (c: ReviewCandidateItem | null) => void,
  ) {
    super(app);
    this.setPlaceholder("选择要复盘的错误候选（pending · 前缀为所在节点）");
  }

  getItems() {
    return this.items;
  }

  getItemText(item: ReviewCandidateItem) {
    return `${item.file.basename} · ${formatCandidateLabel(item.candidate)}`;
  }

  onChooseItem(item: ReviewCandidateItem) {
    this.chosen = true;
    this.onResolve(item);
  }

  onClose() {
    super.onClose();
    if (!this.chosen) {
      // 延迟一拍: onChooseItem 在 onClose 之后触发时避免误报取消
      window.setTimeout(() => {
        if (!this.chosen) this.onResolve(null);
      }, 0);
    }
  }
}

/**
 * 方案 A (轨道 B 2026-07-20) — 命令合并后的处理方式二选一。
 * 样稿流程: 选候选 → 选处理方式 (✅ 接受 / ⚠️ 异议)。
 */
class ReviewActionModal extends Modal {
  private resolved = false;

  constructor(
    app: App,
    private item: ReviewCandidateItem,
    private onResolve: (action: "accept" | "dispute" | null) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h3", { text: "这条候选怎么处理？" });
    contentEl.createEl("p", {
      text: `${this.item.file.basename} · ${formatCandidateLabel(this.item.candidate)}`,
    });
    const btnRow = contentEl.createDiv({
      attr: { style: "margin-top: 12px; display: flex; gap: 8px;" },
    });
    const acceptBtn = btnRow.createEl("button", {
      text: "✅ 接受（确认是我的误区，移入错题）",
    });
    acceptBtn.addEventListener("click", () => {
      this.resolved = true;
      this.close();
      this.onResolve("accept");
    });
    const disputeBtn = btnRow.createEl("button", {
      text: "⚠️ 异议（AI 判断错了，写理由）",
    });
    disputeBtn.addEventListener("click", () => {
      this.resolved = true;
      this.close();
      this.onResolve("dispute");
    });
  }

  onClose() {
    this.contentEl.empty();
    if (!this.resolved) {
      this.onResolve(null);
    }
  }
}

/**
 * T5 (2026-07-10) — Story 2.5.X AC #7: 异议理由输入 Modal (必填非空)。
 */
class DisputeReasonModal extends Modal {
  private submitted = false;

  constructor(
    app: App,
    private onResolve: (reason: string | null) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h3", { text: "异议理由（必填）" });
    contentEl.createEl("p", {
      text: "写一句真实理由（如「我没这么说过，是 AI 过度推断」）。候选将标为 disputed，不进入正式错题。占位字符（如 111）会被拒绝。",
    });
    const input = contentEl.createEl("textarea", {
      attr: {
        rows: "3",
        style: "width: 100%;",
        placeholder: "例：我没这么说过，是 AI 过度推断",
      },
    });
    input.focus();
    const btnRow = contentEl.createDiv({
      attr: { style: "margin-top: 12px; text-align: right;" },
    });
    const submit = btnRow.createEl("button", { text: "提交异议" });
    submit.addEventListener("click", () => {
      this.submitted = true;
      this.close();
      this.onResolve(input.value);
    });
  }

  onClose() {
    this.contentEl.empty();
    if (!this.submitted) {
      this.onResolve(null);
    }
  }
}
