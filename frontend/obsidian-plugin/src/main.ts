import {
  type App,
  type Editor,
  FuzzySuggestModal,
  Modal,
  Notice,
  Plugin,
  requestUrl,
  type TFile,
} from "obsidian";
import {
  TAG_OPTIONS,
  type TagOption,
  UNDERSTANDING_OPTIONS,
  type UnderstandingOption,
  wrapSelection,
} from "./callout";
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
  buildAcceptPayload,
  buildDismissPayload,
  buildDisputePayload,
  type ErrorCandidate,
  filterPendingCandidates,
  formatCandidateLabel,
  inferVaultId,
  validateDisputeReason,
} from "./error-candidate-helpers";
import {
  buildOnboardingYaml,
  shouldTriggerOnboarding,
  validateOnboardingInput,
} from "./onboarding-helpers";
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
  buildChatWithContextFallbackPrompt,
  buildNodeChatPrompt,
  type ChatFallbackReason,
  extractBodyWithoutFrontmatter,
  extractFrontmatterType,
  isNodePath,
  type NeighborSummary,
  type NodeChatContext,
} from "./node-chat-context";
import {
  buildFailureNoticeMessage,
  buildGlobalSearchPayload,
  buildSuccessNoticeMessage,
  classifyFetchFailure,
  GLOBAL_SEARCH_TIMEOUT_MS,
  type GlobalSearchResponse,
} from "./global-search";

const DEFAULT_BACKEND_URL = "http://localhost:8011";  // docker host 映射端口（container 内 8001 → host 8011，由 .env API_PORT 决定）
const DEFAULT_NODE_PATH_PREFIXES = ["节点/"];
// Story 2.2+2.9 T1 (2026-05-11) — chat-with-context backend 超时阈值
// 3000ms = chat-with-context 设计预算（study-question deep mode 30-45s 走独立路径）
// 超时触发 plugin 端 1-hop local fallback（collectNodeNeighbors + buildNodeChatPrompt）
const CHAT_ENRICH_TIMEOUT_MS = 3000;

/**
 * Story 2.1 Phase 1 P1.6 — 默认快捷键表（路径 D：成熟方案）。
 *
 * 设计原则（3 agent deep explore 后定）：
 * - 用 Mod+Shift+<字母> 体系（Obsidian + Excalidraw + QuickAdd 等惯例）
 * - 避开 Obsidian 内置（Mod+S/P/O/F/N 等）+ 常用第三方插件占用
 * - 用户自定义优先：Obsidian 内核保证 hotkeys.json 的 customKeys 覆盖默认值
 * - migration 安全：用户已绑过的命令重 install plugin 不会被覆盖
 *
 * Story 决策来源：
 * - Mod+Shift+A → annotate-callout（Story 1.16 决定）
 * - Mod+Shift+D → ai-linked-doc（Story 1.17 决定）
 * - Mod+Shift+E → chat-with-context（Story 2.1 用户决定）
 * - Mod+Shift+C → open-node-chat（Story 3.1 spec 提及）
 * - 其他按命令首字母联想分配
 */
type HotkeyDef = { modifiers: ("Mod" | "Shift" | "Alt" | "Ctrl")[]; key: string };
const DEFAULT_HOTKEYS: Record<string, HotkeyDef[]> = {
  "canvas:chat-with-context": [{ modifiers: ["Mod", "Shift"], key: "E" }],
  "canvas:open-node-chat": [{ modifiers: ["Mod", "Shift"], key: "C" }],
  "canvas:ai-linked-doc": [{ modifiers: ["Mod", "Shift"], key: "D" }],
  "canvas:annotate-callout": [{ modifiers: ["Mod", "Shift"], key: "A" }],
  "canvas:configure-whiteboard": [{ modifiers: ["Mod", "Shift"], key: "W" }],
  "canvas:append-note-to-board": [{ modifiers: ["Mod", "Shift"], key: "B" }],
  "canvas:open-dashboard": [{ modifiers: ["Mod", "Shift"], key: "H" }],
  "canvas:open-review-queue": [{ modifiers: ["Mod", "Shift"], key: "R" }],
  "canvas:start-dialog": [{ modifiers: ["Mod", "Shift"], key: "L" }],
  "canvas:start-examination-confirm": [{ modifiers: ["Mod", "Shift"], key: "X" }],
  "canvas:extract-concept": [{ modifiers: ["Mod", "Alt"], key: "C" }],
  "canvas:quiz-from-callout": [{ modifiers: ["Mod", "Alt"], key: "Q" }],
  // Story 2.3 v1.2 — study-question 不绑 hotkey（用户批注 2026-05-10）
  // 理由：search-info 类 skill 不依赖编辑器 selection / 不改文件，hotkey 占心智但无价值。
  // 触发路径双轨：
  //   1. Claudian 输入框直接打 `/study-question 问题`（SDK 一等公民，但失 backend full RAG）
  //   2. Cmd+P 命令面板搜 "解题深度模式"（保留 plugin full RAG 注入路径）
  // hotkey 仅留给"必须依赖 selection 才能工作"的 ai-linked-doc / annotate-callout / configure-whiteboard。
  // 旧绑定 Cmd+Shift+Q 是 macOS 系统级注销 hotkey（永远绑不上）；
  // v1.1 改 Cmd+Shift+S 解决了冲突但仍无价值，v1.2 直接移除。
  // start-examination（直调无 confirm）刻意不绑：与 -confirm 重复触发风险，由用户主动选 confirm 版
};

interface CanvasPluginSettings {
  backendUrl: string;
  /** Story 2.1 P1.6 — 节点池前缀（默认 ["节点/"]）。可在 data.json 配置多前缀（如英文 vault 用 ["Nodes/"]）。 */
  nodePathPrefixes: string[];
  /** 用户视角的 active vault 名（vault selector 选中态镜像）。Backend 是 source of truth，本地仅记录最近选择 */
  activeVaultName: string;
  /**
   * Wave-2 P0-1 (2026-05-12) — Internal API key for backend auth header X-CLS-Internal-Key.
   * 空字符串 = dev mode (DEBUG=True, backend 跳过 auth middleware)。
   * 非空 = prod mode (DEBUG=False + INTERNAL_API_KEY 配置, 4 handler 必须带此 header 否则 403)。
   * ChatGPT v2 对抗审查发现 plugin 4 handler 全部漏带 → P0 阻断生产部署。
   */
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

  async onload() {
    await this.loadSettings();
    this.registerCanvasCommands();
    this.addSettingTab(new CanvasSettingTab(this.app, this));
    this.app.workspace.onLayoutReady(() => {
      this.checkHotkeyConflicts();
      // Round-23 Phase B0.3 (2026-05-11): 多 vault onboarding modal
      // 检测 .canvas-config.yaml 不存在时弹出 modal，自动生成 vault_id 写入 yaml
      // 已存在 config → 跳过（主仓 canvas-vault 已 ship，此 modal 仅对新 vault 触发）
      void this.checkVaultOnboarding();
    });
    this.registerEvent(
      this.app.metadataCache.on("changed", (file) => {
        if (file.path.startsWith("节点/") || file.path.startsWith("原白板/")) {
          this.masteryCache.clear();
        }
      }),
    );

    // Story 2.2 follow-up — 增量索引 hook：vault 文件 modify/create/delete/rename
    // 批量 debounce 1500ms 后 POST /api/v1/index/refresh-changed 让 backend SHA-256
    // fingerprint 比对 + 单文件 < 500ms 增量 reindex。无白名单（.obsidian/.git/.trash
    // 已在 backend skip_dirs 默认过滤），仅过滤非 .md 文件。
    this.registerIncrementalIndexHook();
  }

  /**
   * Round-23 Phase B0.3 (2026-05-11) — 多 vault onboarding modal 检测
   *
   * 触发条件：.canvas-config.yaml 不存在（新 vault 首次打开）
   * 已存在 config → 跳过（已 onboarded vault 不重弹）
   *
   * 设计理念：让用户加新 vault（如另一门课）时一键生成 vault_id + subject，
   * 避免手动编辑 yaml 容易出错。Round-23 plan §3.1.3 落地。
   */
  private async checkVaultOnboarding(): Promise<void> {
    const configPath = ".canvas-config.yaml";
    try {
      const exists = await this.app.vault.adapter.exists(configPath);
      // P1 fix (ChatGPT 2026-05-11): 决策抽到纯函数 shouldTriggerOnboarding,
      // 让测试可独立验证决策逻辑(IO 还在,但决策可测)
      if (!shouldTriggerOnboarding(exists)) {
        return;
      }
      console.log(
        "[canvas-onboarding] .canvas-config.yaml not found, opening onboarding modal",
      );
      new VaultOnboardingModal(this.app, async (input) => {
        // P1 fix: 用纯函数 validate + buildOnboardingYaml(从 onboarding-helpers 导入,可测)
        const validation = validateOnboardingInput(input.displayName, input.subject);
        if (!validation.valid) {
          new Notice(`❌ ${validation.error}`, 4000);
          return;
        }
        const vaultId = inferVaultId(input.displayName);
        const yamlContent = buildOnboardingYaml(
          vaultId,
          input.displayName,
          input.subject,
        );
        try {
          await this.app.vault.adapter.write(configPath, yamlContent);
          new Notice(
            `✅ Canvas Vault 初始化完成\n` +
              `vault_id: ${vaultId}\n` +
              `subject: ${input.subject || "general"}\n` +
              `配置已写入 .canvas-config.yaml`,
            8000,
          );
          // 通知 backend 新 vault 创建（best-effort，失败不阻塞）
          void this.notifyBackendVaultCreated(vaultId, input.displayName);
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : String(err);
          new Notice(`❌ 写入 .canvas-config.yaml 失败: ${msg}`, 8000);
        }
      }).open();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`[canvas-onboarding] check failed: ${msg}`);
    }
  }

  /**
   * Best-effort 通知 backend 新 vault 创建（让 backend 预热 LanceDB 表前缀等）
   */
  private async notifyBackendVaultCreated(
    vaultId: string,
    displayName: string,
  ): Promise<void> {
    const backendUrl = this.settings.backendUrl.replace(/\/$/, "");
    try {
      const resp = await requestUrl({
        url: `${backendUrl}/api/v1/vault/created`,
        method: "POST",
        contentType: "application/json",
        body: JSON.stringify({ vault_id: vaultId, display_name: displayName }),
        throw: false,
      });
      if (resp.status === 200) {
        console.log(`[canvas-onboarding] backend notified: ${vaultId}`);
      } else if (resp.status !== 404) {
        // 404 = endpoint 还未实现，是预期行为；其他状态码记录
        console.warn(
          `[canvas-onboarding] backend notify returned ${resp.status}`,
        );
      }
    } catch (err: unknown) {
      // backend 未启动 / 网络问题 — onboarding 仍成功，只是 backend 预热失败
      console.warn(`[canvas-onboarding] backend notify failed: ${err}`);
    }
  }

  /** Story 2.2 follow-up — 增量索引：plugin 监听文件事件 + 批量推送 backend */
  private pendingRefreshPaths = new Set<string>();
  private refreshDebounceTimer: number | null = null;
  private readonly REFRESH_DEBOUNCE_MS = 1500;

  private registerIncrementalIndexHook(): void {
    const onFile = (file: TFile | { path: string }) => {
      if (!file.path.toLowerCase().endsWith(".md")) return;
      this.pendingRefreshPaths.add(file.path);
      this.scheduleRefreshFlush();
    };

    this.registerEvent(this.app.vault.on("modify", onFile));
    this.registerEvent(this.app.vault.on("create", onFile));
    this.registerEvent(this.app.vault.on("delete", onFile));
    this.registerEvent(
      this.app.vault.on("rename", (file, oldPath) => {
        // rename 既要 cleanup 老路径也要 reindex 新路径
        if (oldPath.toLowerCase().endsWith(".md")) {
          this.pendingRefreshPaths.add(oldPath);
        }
        if (file.path.toLowerCase().endsWith(".md")) {
          this.pendingRefreshPaths.add(file.path);
        }
        this.scheduleRefreshFlush();
      }),
    );
  }

  private scheduleRefreshFlush(): void {
    if (this.refreshDebounceTimer !== null) {
      window.clearTimeout(this.refreshDebounceTimer);
    }
    this.refreshDebounceTimer = window.setTimeout(() => {
      void this.flushPendingRefresh();
    }, this.REFRESH_DEBOUNCE_MS);
  }

  private async flushPendingRefresh(): Promise<void> {
    if (this.pendingRefreshPaths.size === 0) return;
    const paths = Array.from(this.pendingRefreshPaths);
    this.pendingRefreshPaths.clear();
    this.refreshDebounceTimer = null;

    const backendUrl = this.settings.backendUrl.replace(/\/$/, "");
    try {
      const resp = await requestUrl({
        url: `${backendUrl}/api/v1/index/refresh-changed`,
        method: "POST",
        contentType: "application/json",
        body: JSON.stringify({ paths }),
        throw: false,
      });
      if (resp.status !== 200) {
        // backend 不可达不打扰用户（降级日志即可），下次保存再试
        console.warn(
          `[Canvas] incremental index refresh failed: HTTP ${resp.status}`,
          paths,
        );
      }
    } catch (e) {
      console.warn(`[Canvas] incremental index refresh exception:`, (e as Error).message);
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
   * Wave-2 P0-1 (2026-05-12) — 构造 backend fetch headers。
   *
   * ChatGPT v2 对抗审查 P0 发现：原 4 handler (handleChatWithContext / handleStudyQuestion /
   * handleOpenNodeChat / handleGlobalSearch) 全部用裸 `{ "Content-Type": "application/json" }`,
   * 在 DEBUG=False + INTERNAL_API_KEY 配置的生产 env 下全部 403 (backend 的 internal-key
   * middleware 拒收)。
   *
   * 设计:
   * - 始终含 `Content-Type: application/json`（4 handler 都 POST JSON）
   * - 若 `settings.internalApiKey` 非空 → 加 `X-CLS-Internal-Key: <key>` (prod auth)
   * - 若为空 → 不加（dev mode 兼容，DEBUG=True 时 backend 跳过 auth）
   *
   * 这是 pure function — 不读 fetch 调用方 body，只读 settings。helper 暴露为 public
   * 以便单元测试可调（tests/auth-headers.test.ts）。
   */
  public buildBackendHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    // Wave-3 W3-4a (2026-05-12, Claude self-audit F1): use trim() so whitespace-only
    // keys (e.g. user accidentally types "  ") don't reach backend as "valid" header
    // and trigger 403. Also send trimmed value so trailing/leading spaces don't fail
    // backend constant-time compare.
    const key = (this.settings.internalApiKey ?? "").trim();
    if (key.length > 0) {
      headers["X-CLS-Internal-Key"] = key;
    }
    return headers;
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
      isNodePath(f.path, this.settings.nodePathPrefixes),
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
   * Story 1.4 + Story 2.1 Phase 1 P1.6（路径 D 成熟方案）：
   * 注册 13 个命令，每个命令注入 DEFAULT_HOTKEYS 默认快捷键。
   *
   * Obsidian 内核行为：
   * - hotkeys.json 的 customKeys 覆盖 default（用户自绑优先）
   * - default 对没绑过的命令开箱即用
   * - migration 安全（用户已绑过的不会被覆盖）
   */
  private registerCanvasCommands() {
    const cmds: Array<{
      id: string;
      name: string;
      callback: () => unknown | Promise<unknown>;
    }> = [
      {
        id: "canvas:start-dialog",
        name: "启动学习对话",
        callback: () => this.callBackend("/api/v1/agents/dialog", "启动学习对话"),
      },
      {
        id: "canvas:start-examination",
        name: "启动考察（直调，无 confirm）",
        callback: () => this.handleStartExaminationDirect(),
      },
      {
        id: "canvas:extract-concept",
        name: "提取概念",
        callback: () => {
          const editor = this.app.workspace.activeEditor?.editor;
          const selected = editor?.getSelection();
          if (!selected) {
            new Notice("请先选中文本再提取概念");
            return;
          }
          this.callBackend("/api/v1/wikilink/build", "提取概念", {
            text: selected,
          });
        },
      },
      {
        id: "canvas:quiz-from-callout",
        name: "批注考察",
        callback: () => this.handleStartExaminationDirect(),
      },
      {
        id: "canvas:open-dashboard",
        name: "打开 Dashboard.md",
        callback: () => this.handleOpenDashboard(),
      },
      {
        id: "canvas:open-review-queue",
        name: "打开复习队列（GET /review/schedule）",
        callback: () =>
          this.callBackend(
            "/api/v1/review/schedule?days=7",
            "打开复习队列",
            undefined,
            "GET",
          ),
      },
      {
        id: "canvas:annotate-callout",
        name: "批注为标注",
        callback: () => this.handleAnnotateCallout(),
      },
      {
        id: "canvas:ai-linked-doc",
        name: "AI 创建双链文档",
        callback: () => this.handleAILinkedDoc(),
      },
      {
        id: "canvas:configure-whiteboard",
        name: "建/配置原白板（v4 全 plugin 脚本）",
        callback: () => this.handleConfigureWhiteboard(),
      },
      {
        id: "canvas:append-note-to-board",
        name: "把当前笔记追加到已有原白板",
        callback: () => this.handleAppendNoteToBoard(),
      },
      {
        id: "canvas:start-examination-confirm",
        name: "启动考察（带 confirm 弹窗）",
        callback: () => this.handleStartExaminationConfirm(),
      },
      {
        id: "canvas:open-node-chat",
        name: "节点对话（注入上下文 + 切 Claudian）",
        callback: () => this.handleOpenNodeChat(),
      },
      {
        id: "canvas:chat-with-context",
        name: "AI 对话 v2（backend RAG 上下文增强 + 切 Claudian）",
        callback: () => this.handleChatWithContext(),
      },
      {
        id: "canvas:study-question",
        name: "解题深度模式（study-question · 30-45s 4 段结构化诊断）",
        callback: () => this.handleStudyQuestion(),
      },
      // Story 2.10 (2026-05-12) — global-search: 任意视图可触发的全局搜索。
      // 区别于 chat-with-context: 不依赖 active file 在 节点/ 路径下；Dashboard、教学
      // 笔记、设置 tab 等任意视图都可发起。delay 预算 8s（vs chat 3s）给 deep search 留余地。
      {
        id: "canvas:global-search",
        name: "全局搜索教学笔记 (Global Search,任意视图可触发)",
        callback: () => this.handleGlobalSearch(),
      },
      // Story 2.5.X (D15 用户主权 C+) — 错误候选 3 命令
      {
        id: "canvas:accept-error-candidate",
        name: "接受错误候选（移入正式 errors[] + Graphiti）",
        callback: () => this.handleAcceptErrorCandidate(),
      },
      {
        id: "canvas:dismiss-error-candidate",
        name: "标记错误候选为 AI 误判（dismiss）",
        callback: () => this.handleDismissErrorCandidate(),
      },
      {
        id: "canvas:dispute-error-candidate",
        name: "异议错误候选（写理由）",
        callback: () => this.handleDisputeErrorCandidate(),
      },
    ];

    for (const cmd of cmds) {
      const hotkeys = DEFAULT_HOTKEYS[cmd.id];
      this.addCommand({
        id: cmd.id,
        name: cmd.name,
        callback: cmd.callback,
        ...(hotkeys ? { hotkeys } : {}),
      });
    }
  }

  /**
   * Story 2.1 v1.0 — Backend RAG 上下文增强对话入口（路线 A 第 2 步）
   *
   * 区别于 canvas:open-node-chat（plugin 端纯本地 1-hop 邻居）：
   * - 调 backend POST /api/v1/chat/enrich-context
   * - backend 用 wikilink_graph_service 做 N-hop 遍历 + token 预算压缩 + LaTeX/代码块保护
   * - 降级处理：图未 build / 超时 / 异常 → backend 返回 degraded=True + 通知文本
   *
   * 流程：
   *   1. 检 active file 在 节点/ 路径
   *   2. 收集 current_note (path + 正文 + frontmatter)
   *   3. POST /chat/enrich-context（含 max_hops + token_budget）
   *   4. 拿 enriched_context（含降级通知 if any）
   *   5. 写剪贴板 + Notice + 切 Claudian sidebar
   *   6. 用户粘贴 → /chat-with-context Skill 接管对话（纯对话，不写文件）
   */
  private async handleChatWithContext() {
    console.log("[canvas:chat-with-context] triggered");
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }
    if (!isNodePath(activeFile.path, this.settings.nodePathPrefixes)) {
      new Notice(
        `对话仅在 节点/ 下的概念页可用（当前 path: ${activeFile.path}）`,
        5000,
      );
      return;
    }

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

    // Story 2.2 Phase A · Gap 1 fix: 取用户问题触发补充材料搜索
    // 优先级: editor selection > Modal 输入 > 留空跳过补充材料
    const editor = this.app.workspace.activeEditor?.editor;
    const selection = editor?.getSelection?.()?.trim() ?? "";
    let userQuestion = selection;
    if (!userQuestion) {
      userQuestion = await new Promise<string>((resolve) => {
        new UserQuestionModal(this.app, (q) => resolve(q ?? "")).open();
      });
    }

    const t0 = Date.now();
    const url = `${this.settings.backendUrl}/api/v1/chat/enrich-context`;
    // Multi-vault P0-1 (2026-05-10): vault_id 必填，防 5 vault 串库。
    // Backend 端 sanitize_vault_id 标准化（NFKC + casefold + Unicode \w）后
    // 调 build_vault_group_id → set_current_subject_id 注入 ContextVar。
    const payload: Record<string, unknown> = {
      node_path: activeFile.path,
      current_note_content: body,
      current_note_frontmatter: fmRaw,
      max_hops: 2,
      vault_id: inferVaultId(this.app.vault.getName()),
    };
    if (userQuestion) {
      payload.mode = "answer";
      payload.user_question = userQuestion;
    }
    // Story 2.2+2.9 T1 (2026-05-11) — AC #2: backend timeout 3000ms + 1-hop local fallback
    // AbortController 防 backend 无响应永久挂起; AbortError | TypeError(网络) 触发降级,
    // 等价 Cmd+Shift+C (handleOpenNodeChat) 的 1-hop local 路径, 但保留 /chat-with-context skill 前缀,
    // prompt 顶部加 Degradations marker 让 Skill 知道走的是降级路径。
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      CHAT_ENRICH_TIMEOUT_MS,
    );
    let resp: Response;
    try {
      // Wave-2 P0-1 (2026-05-12): 用 buildBackendHeaders() 注入 X-CLS-Internal-Key
      // 防 DEBUG=False + INTERNAL_API_KEY 配置时 backend middleware 拒收 (403)
      resp = await fetch(url, {
        method: "POST",
        headers: this.buildBackendHeaders(),
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const isAbort =
        err instanceof DOMException && err.name === "AbortError";
      const reason: ChatFallbackReason = isAbort
        ? "backend_timeout"
        : "backend_unreachable";
      const msg = err instanceof Error ? err.message : String(err);
      console.log(
        `[canvas:chat-with-context] fallback triggered: ${reason} (${msg})`,
      );
      await this.fallbackToLocalNeighbors(
        activeFile,
        body,
        fmRaw,
        userQuestion,
        reason,
        t0,
      );
      return;
    }

    let parsed: any;
    try {
      parsed = await resp.json();
    } catch {
      new Notice(`❌ backend 返回非 JSON（HTTP ${resp.status}）`, 6000);
      return;
    }
    if (!resp.ok) {
      const detail = parsed?.detail || `HTTP ${resp.status}`;
      new Notice(`❌ enrich-context 失败: ${detail}`, 6000);
      return;
    }

    const enrichedContext = parsed.enriched_context as string;
    const usedTokens = parsed.used_tokens as number;
    const budget = parsed.budget as number;
    const neighborsCount = parsed.neighbors_count as number;
    const degraded = parsed.degraded as boolean;
    const suppCount = (parsed.supplementary_count as number) ?? 0;
    const suppDegraded = (parsed.supplementary_degraded as boolean) ?? false;
    const suppReason = (parsed.supplementary_reason as string | null) ?? null;

    // Story 2.2 Phase A · RAG-as-tool 范式重构（2025 业界共识 — Anthropic Claude Code/
    // Cursor/Devin/Augment 全部抛弃 vector RAG-as-prompt-injection 改 grep+agent verify）:
    // 用户原话: "RAG 是辅助 claude code 用 grep 找得更准，把有用的材料都提供给我"
    // → supplementary = candidate generator (大召回)，Claude Read = verifier (真核实)
    const ANCHOR_INSTRUCTION =
      "⛔ 回答工作流（违反 = 答非所问 + 用户原痛点回归）：\n"
      + "(1) 收到 <supplementary_materials count=\"N\"> 时 N>0，**必须先用 Read tool 实际读 top 2-3 条 <source_path>** — snippet 仅是召回 hint，真 evidence 来自 Read 后的完整文件内容。\n"
      + "(2) Read 失败 / 文件空 / 路径错 → 跳过该条 + 在回答末尾标 `（rank=N 跳过：read_failed=<reason>）`，**禁止假装读过**。\n"
      + "(3) 至少 Read 2 条做多源交叉验证（防 ghost reference）。\n"
      + "(4) 主回答行文中必须含 ≥1 个 `[[file#具体heading]]` heading 级精度 wikilink（Read 后才知道有哪些 heading）— 不允许 `[[file]]` 全文模糊引用（等于没核实）。\n"
      + "(5) **禁止凭训练数据答 CS188/AIMA/Berkeley 课程教材类问题** — 用户 raw/CS188/ 已索引在 vault 内，找不到就 Read 邻居 + supplementary 实际内容确认。\n"
      + "(6) 仅当 Read 后全部 vault 段都无关时才允许通用知识 + 必须显式标 `（通用知识 — vault Read 后未找到相关）`。\n"
      + "(7) 末尾用 `---` 分隔后展示完整 supplementary 列表（title/wikilink/snippet/score）便于用户跳转。";
    const prompt = userQuestion
      ? `/chat-with-context\n\n${enrichedContext}\n\n---\n${ANCHOR_INSTRUCTION}\n\n问题：${userQuestion}`
      : `/chat-with-context\n\n${enrichedContext}\n\n---\n${ANCHOR_INSTRUCTION}\n\n问题：（在这里输入）`;

    try {
      await navigator.clipboard.writeText(prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.showRetryNotice(
        `❌ 剪贴板写入失败（${msg}），点重试`,
        () => void this.handleChatWithContext(),
      );
      return;
    }

    const elapsedMs = Date.now() - t0;
    const sizeKb = (new Blob([prompt]).size / 1024).toFixed(1);
    const degradeHint = degraded
      ? `（⚠ ${parsed.degraded_reason} — 仅当前笔记）`
      : "";
    // Story 2.2 Phase A: supplementary 信息可见化
    const suppHint = suppCount > 0
      ? ` + ${suppCount} 补充材料 ⭐`
      : userQuestion && suppDegraded
        ? `（补充材料降级: ${suppReason ?? "?"}）`
        : "";
    new Notice(
      `已组装 backend RAG 上下文 ${sizeKb}KB / ${neighborsCount} 邻居${suppHint} / ${usedTokens}/${budget} tokens${degradeHint}（${elapsedMs}ms）\n切到 Claudian 粘贴`,
      7000,
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
   * Story 2.3 v1.0 — Study-question 解题深度模式入口（Phase 1）
   *
   * 区别于 canvas:chat-with-context（Cmd+Shift+E 快问快答 5s 预算）：
   * - mode="deep" → backend supplementary 用 top_k_max=30 / hard_cap=20（vs 20/15）
   * - prompt 前缀 `/study-question` → 触发 study-question Skill 而非 chat-with-context
   * - ANCHOR_INSTRUCTION 加 5 阶段进度透明化 + 4 段结构化输出强制
   * - 用户预期等待 30-45s（vs 快问快答 5s）
   *
   * 用户场景：解题不解 / 知识点不懂时主动深化（不靠 hook auto 召回）
   */
  private async handleStudyQuestion() {
    console.log("[canvas:study-question] triggered");
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }
    if (!isNodePath(activeFile.path, this.settings.nodePathPrefixes)) {
      new Notice(
        `解题深度模式仅在 节点/ 下的概念页可用（当前 path: ${activeFile.path}）`,
        5000,
      );
      return;
    }

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

    // 优先级与 chat-with-context 一致：editor selection > Modal 输入 > 留空跳过
    const editor = this.app.workspace.activeEditor?.editor;
    const selection = editor?.getSelection?.()?.trim() ?? "";
    let userQuestion = selection;
    if (!userQuestion) {
      userQuestion = await new Promise<string>((resolve) => {
        new UserQuestionModal(this.app, (q) => resolve(q ?? "")).open();
      });
    }
    if (!userQuestion) {
      new Notice(
        "深度解题模式需要明确的问题（无法空查询）。请输入要解的题/概念，例如 \"什么是 admissibility\"",
        5000,
      );
      return;
    }

    const t0 = Date.now();
    const url = `${this.settings.backendUrl}/api/v1/chat/enrich-context`;
    // Multi-vault P0-1 (2026-05-10): vault_id 必填，深度模式同样防串库
    const payload: Record<string, unknown> = {
      node_path: activeFile.path,
      current_note_content: body,
      current_note_frontmatter: fmRaw,
      max_hops: 2,
      mode: "deep",
      user_question: userQuestion,
      vault_id: inferVaultId(this.app.vault.getName()),
    };
    let resp: Response;
    try {
      // Wave-2 P0-1 (2026-05-12): study-question deep 模式同样注入 X-CLS-Internal-Key
      resp = await fetch(url, {
        method: "POST",
        headers: this.buildBackendHeaders(),
        body: JSON.stringify(payload),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(
        `❌ backend 未连接（${msg}）\n请先 docker compose up 启动 Canvas 后端`,
        6000,
      );
      return;
    }

    let parsed: any;
    try {
      parsed = await resp.json();
    } catch {
      new Notice(`❌ backend 返回非 JSON（HTTP ${resp.status}）`, 6000);
      return;
    }
    if (!resp.ok) {
      const detail = parsed?.detail || `HTTP ${resp.status}`;
      new Notice(`❌ enrich-context (deep) 失败: ${detail}`, 6000);
      return;
    }

    const enrichedContext = parsed.enriched_context as string;
    const usedTokens = parsed.used_tokens as number;
    const budget = parsed.budget as number;
    const neighborsCount = parsed.neighbors_count as number;
    const degraded = parsed.degraded as boolean;
    const suppCount = (parsed.supplementary_count as number) ?? 0;
    const suppDegraded = (parsed.supplementary_degraded as boolean) ?? false;
    const suppReason = (parsed.supplementary_reason as string | null) ?? null;

    // Study-question 专属 ANCHOR_INSTRUCTION — 5 阶段进度 + 4 段结构化强制
    const DEEP_ANCHOR_INSTRUCTION =
      "⛔ 解题深度模式工作流（违反 = 退化为普通对话，浪费 30-45s 预算）：\n"
      + "(1) **先做 Query intent 分类**: Definition / Procedure / Causal / Comparison 四选一，分类前不答。规则关键词命中显示\"keyword=X 命中\"，规则全 miss 时显示\"Claude 推断\"。\n"
      + "(2) **5 阶段进度透明化**: 输出 `[1/5] intent` → `[2/5] 检索维度` → `[3/5] backend 召回 N 条` → `[4/5] Read 完整章节` → `[5/5] 合成中...`。每阶段一行，不空跑。\n"
      + "(3) **必须 Read top 3 完整章节**: <supplementary_materials> 的 score 顺序 Read top-3 的 <source_path> 完整内容（snippet 是 hint 不是答案）。N<3 时 Read 全部。Read 失败标 `（rank=N 跳过：read_failed=<reason>）`，禁假装读过。\n"
      + "(4) **必须 wikilink 2-hop 邻居扩展**: 1-hop 来自 <neighbor hop=\"1\">，2-hop 来自 <neighbor hop=\"2\">。优先级 [!error]+ > [!question]+ > [!tip]+ > 普通邻居。\n"
      + "(5) **强制 4 段输出结构**（按 intent 路由）：\n"
      + "    - Definition: ## 严格定义 / ## 直觉理解 / ## 1 个反例 / ## 联系节点\n"
      + "    - Procedure: ## 前提条件 / ## 执行步骤 / ## 完整例子 / ## 联系节点\n"
      + "    - Causal: ## 因果链 / ## 每步证据 / ## 误区 / ## 联系节点\n"
      + "    - Comparison: ## X 是什么 / ## Y 是什么 / ## 关键差异 / ## 何时选谁 / ## 共同祖先\n"
      + "(6) **inline wikilink heading 级精度**: 每个声明必带 `[[file#heading]]` 或 `[[file#^block]]`，禁 `[[file]]` 全文模糊引用。\n"
      + "(7) **Citation back-verification**: 生成后 self-check 每个 wikilink 是否真支持其所在声明；找不到证据的句子改 `（推论 — Read 章节中未找到直接证据）`。\n"
      + "(8) **末尾 `---` 分隔后展示完整 supplementary 列表**（rank/title/wikilink/snippet/score）。\n"
      + "(9) **禁止凭训练数据答课程材料类问题** — vault 已索引到的概念找不到就说\"vault 未索引到 X\"，禁止 fallback 训练数据。";

    const prompt = `/study-question\n\n${enrichedContext}\n\n---\n${DEEP_ANCHOR_INSTRUCTION}\n\n问题：${userQuestion}`;

    try {
      await navigator.clipboard.writeText(prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.showRetryNotice(
        `❌ 剪贴板写入失败（${msg}），点重试`,
        () => void this.handleStudyQuestion(),
      );
      return;
    }

    const elapsedMs = Date.now() - t0;
    const sizeKb = (new Blob([prompt]).size / 1024).toFixed(1);
    const degradeHint = degraded
      ? `（⚠ ${parsed.degraded_reason} — 仅当前笔记）`
      : "";
    const suppHint = suppCount > 0
      ? ` + ${suppCount} 补充材料 ⭐（deep 模式）`
      : suppDegraded
        ? `（补充材料降级: ${suppReason ?? "?"}）`
        : "";
    new Notice(
      `🧠 解题深度模式已就绪 ${sizeKb}KB / ${neighborsCount} 邻居${suppHint} / ${usedTokens}/${budget} tokens${degradeHint}（${elapsedMs}ms）\n切到 Claudian 粘贴 — 预计 30-45s 出 4 段结构化诊断`,
      8000,
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
   * Story 2.10 (2026-05-12) — Global Search 全局搜索教学笔记入口
   *
   * 区别于 canvas:chat-with-context（Cmd+Shift+E）:
   *   - 不要求 active file 在 节点/ 路径下 — Dashboard / 教学笔记 / 设置 tab 等任意视图都可触发
   *   - timeout 8000ms（vs 3000ms）给 backend 的 deep search 留预算
   *   - payload 不带 node_path / current_note_content — 纯 query-driven
   *   - subject_id=null 让 backend 按"一 vault 一学科"约定 fallback
   *
   * 流程:
   *   1. UserQuestionModal 取问题。空问题 → silently 退出
   *   2. POST {backendUrl}/api/v1/chat/global-search
   *   3. 成功 → 剪贴板写 enriched_context + Notice + 切 Claudian sidebar
   *   4. 失败（AbortError / TypeError / non-200）→ 友好 Notice，不 crash
   */
  private async handleGlobalSearch() {
    console.log("[canvas:global-search] triggered");

    // Step 1: 取用户问题（不依赖 editor selection — 任意视图触发时 editor 可能不存在）
    const userQuestion = await new Promise<string>((resolve) => {
      new UserQuestionModal(this.app, (q) => resolve(q ?? "")).open();
    });
    const trimmed = userQuestion.trim();
    if (!trimmed) {
      // 空问题 silently 退出（与 chat-with-context Modal "跳过补充材料" 习惯一致：但
      // 全局搜索没有 fallback context 可用，所以直接退）
      console.log("[canvas:global-search] empty question, silently abort");
      return;
    }

    const t0 = Date.now();
    const vaultId = inferVaultId(this.app.vault.getName());
    const payload = buildGlobalSearchPayload({
      userQuestion: trimmed,
      vaultId,
    });

    const url = `${this.settings.backendUrl}/api/v1/chat/global-search`;
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      GLOBAL_SEARCH_TIMEOUT_MS,
    );

    let resp: Response;
    try {
      // Wave-2 P0-1 (2026-05-12): global-search 也走 backend POST，同样需要 X-CLS-Internal-Key
      resp = await fetch(url, {
        method: "POST",
        headers: this.buildBackendHeaders(),
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const reason = classifyFetchFailure(err);
      const msg = err instanceof Error ? err.message : String(err);
      console.log(`[canvas:global-search] fetch failed: ${reason} (${msg})`);
      new Notice(buildFailureNoticeMessage(reason), 6000);
      return;
    }

    if (!resp.ok) {
      console.log(`[canvas:global-search] non-2xx status ${resp.status}`);
      new Notice(buildFailureNoticeMessage("backend_error"), 6000);
      return;
    }

    let parsed: GlobalSearchResponse;
    try {
      parsed = (await resp.json()) as GlobalSearchResponse;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.log(`[canvas:global-search] non-JSON response: ${msg}`);
      new Notice(buildFailureNoticeMessage("non_json_response"), 6000);
      return;
    }

    const enrichedContext = parsed.enriched_context;
    if (typeof enrichedContext !== "string" || enrichedContext.length === 0) {
      console.log("[canvas:global-search] empty enriched_context in response");
      new Notice(buildFailureNoticeMessage("backend_error"), 6000);
      return;
    }

    // 写剪贴板 — 仿 chat-with-context 用 /chat-with-context skill 前缀（global-search
    // 走的也是 backend RAG-as-tool 范式，Skill 端的工作流一致：Read top-3 supplementary
    // + heading 级 wikilink）。复用 ANCHOR_INSTRUCTION 思路防"假装读过"回归。
    const prompt = `/chat-with-context\n\n${enrichedContext}\n\n---\n问题：${trimmed}`;
    try {
      await navigator.clipboard.writeText(prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.showRetryNotice(
        `❌ 剪贴板写入失败（${msg}），点重试`,
        () => void this.handleGlobalSearch(),
      );
      return;
    }

    const elapsedMs = Date.now() - t0;
    new Notice(
      buildSuccessNoticeMessage({ response: parsed, elapsedMs }),
      7000,
    );

    const claudianCmd = (this.app as any).commands?.findCommand?.(
      "claudian:open-view",
    );
    if (!claudianCmd) {
      new Notice("未检测到 Claudian 插件，请先安装并登录 Claude Code", 5000);
      return;
    }
    (this.app as any).commands.executeCommandById("claudian:open-view");
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
    if (!isNodePath(activeFile.path, this.settings.nodePathPrefixes)) {
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
   * Story 2.2+2.9 T1 (2026-05-11) — handleChatWithContext backend 超时/不可达时的降级路径。
   *
   * 行为等价于 Cmd+Shift+C (handleOpenNodeChat) 的 1-hop local 邻居装载,
   * 但保留 /chat-with-context skill 前缀（用户视角连续）, 在 prompt 顶部加
   * Degradations marker 让 Skill 端知道走的是降级路径（邻居数量从 N-hop 降到 1-hop, supplementary=0）。
   *
   * 触发条件:
   *   - backend_timeout: AbortController abort (>3000ms)
   *   - backend_unreachable: fetch TypeError (docker 没启 / 网络断 / DNS fail)
   */
  private async fallbackToLocalNeighbors(
    activeFile: TFile,
    body: string,
    fmRaw: Record<string, unknown>,
    userQuestion: string,
    reason: ChatFallbackReason,
    t0: number,
  ): Promise<void> {
    const neighbors = await this.collectNodeNeighbors(activeFile.path, 5);
    const context: NodeChatContext = {
      nodePath: activeFile.path,
      nodeBasename: activeFile.basename,
      frontmatter: fmRaw,
      body,
      selection: userQuestion || undefined,
      neighbors,
    };
    const localResult = buildNodeChatPrompt(context);
    // 保留 /chat-with-context skill 入口（用户视角不变）；body 用 1-hop local 替代 backend RAG
    const prompt = buildChatWithContextFallbackPrompt({
      reason,
      localPrompt: localResult.prompt,
    });
    try {
      await navigator.clipboard.writeText(prompt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.showRetryNotice(
        `❌ 剪贴板写入失败（${msg}），点重试`,
        () => void this.handleChatWithContext(),
      );
      return;
    }
    const elapsedMs = Date.now() - t0;
    const sizeKb = (new Blob([prompt]).size / 1024).toFixed(1);
    const reasonText =
      reason === "backend_timeout" ? "backend 超时" : "backend 未连接";
    new Notice(
      `⚠️ ${reasonText}，已降级到本地 1-hop（${neighbors.length} 邻居 / ${sizeKb}KB / ${elapsedMs}ms）\n切到 Claudian 粘贴`,
      7000,
    );
    const claudianCmd = (this.app as any).commands?.findCommand?.(
      "claudian:open-view",
    );
    if (!claudianCmd) {
      new Notice("未检测到 Claudian 插件，请先安装并登录 Claude Code", 5000);
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
    const sourceInNodesPool = isNodePath(
      sourceFile.path,
      this.settings.nodePathPrefixes,
    );

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
    const inNodesPool = isNodePath(
      seedFile.path,
      this.settings.nodePathPrefixes,
    );

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
      // Wave-2 P0-1 (2026-05-12): callBackend 也走 backend (exam/start 等), 注入 X-CLS-Internal-Key
      // GET 请求不需要 Content-Type 但 X-CLS-Internal-Key 仍需带 (auth middleware 对所有 method 生效)
      const headers = body
        ? this.buildBackendHeaders()
        : (() => {
            const h: Record<string, string> = {};
            if (this.settings.internalApiKey && this.settings.internalApiKey.length > 0) {
              h["X-CLS-Internal-Key"] = this.settings.internalApiKey;
            }
            return h;
          })();
      const resp = await fetch(url, {
        method,
        headers,
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

  // ═══════════════════════════════════════════════════════════════════
  // Story 2.5.X (D15 用户主权 C+) — 错误候选 3 命令 handler
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Story 2.5.X Task 7 — 接受错误候选 (移入正式 errors[] + Graphiti).
   *
   * 流程:
   * 1. 检查 active file 是节点
   * 2. 读 frontmatter error_candidates[] 过滤 status=pending
   * 3. CandidateSuggestModal 让用户选条
   * 4. POST /api/v1/errors/accept-candidate
   * 5. Notice 反馈结果
   */
  private async handleAcceptErrorCandidate() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }

    const fm = (this.app.metadataCache.getFileCache(activeFile)?.frontmatter as
      | Record<string, unknown>
      | undefined) ?? {};
    const pending = filterPendingCandidates(fm.error_candidates);

    if (pending.length === 0) {
      new Notice("当前节点无待复盘错误候选 (error_candidates[] 为空)", 4000);
      return;
    }

    new CandidateSuggestModal(
      this.app,
      pending,
      "选择要接受的错误候选",
      async (cand) => {
        const vaultId = inferVaultId(this.app.vault.getName());
        await this.postErrorCandidateAction(
          "accept-candidate",
          buildAcceptPayload(cand.id, activeFile.path, { vaultId }),
          (result) => `✓ 已接受 → errors[] (Graphiti: ${result.graphiti_status})`,
        );
      },
    ).open();
  }

  private async handleDismissErrorCandidate() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }
    const fm = (this.app.metadataCache.getFileCache(activeFile)?.frontmatter as
      | Record<string, unknown>
      | undefined) ?? {};
    const pending = filterPendingCandidates(fm.error_candidates);
    if (pending.length === 0) {
      new Notice("当前节点无待复盘错误候选", 4000);
      return;
    }

    new CandidateSuggestModal(
      this.app,
      pending,
      "选择要标记为 AI 误判的候选 (dismiss)",
      async (cand) => {
        const vaultId = inferVaultId(this.app.vault.getName());
        await this.postErrorCandidateAction(
          "dismiss-candidate",
          buildDismissPayload(cand.id, activeFile.path, { vaultId }),
          () => "✗ 已标记为 AI 误判 (dismissed)",
        );
      },
    ).open();
  }

  private async handleDisputeErrorCandidate() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("请先打开 节点/<concept>.md 节点页", 3000);
      return;
    }
    const fm = (this.app.metadataCache.getFileCache(activeFile)?.frontmatter as
      | Record<string, unknown>
      | undefined) ?? {};
    const pending = filterPendingCandidates(fm.error_candidates);
    if (pending.length === 0) {
      new Notice("当前节点无待复盘错误候选", 4000);
      return;
    }

    new CandidateSuggestModal(
      this.app,
      pending,
      "选择要异议的候选",
      (cand) => {
        // 第 2 步: 弹 DisputeReasonModal 收集理由
        new DisputeReasonModal(this.app, async (reason) => {
          const validation = validateDisputeReason(reason);
          if (!validation.valid) {
            new Notice(`❌ ${validation.error}`, 4000);
            return;
          }
          const vaultId = inferVaultId(this.app.vault.getName());
          await this.postErrorCandidateAction(
            "dispute-candidate",
            buildDisputePayload(cand.id, activeFile.path, reason, { vaultId }),
            () => "⚠ 已标记 disputed + 写入理由",
          );
        }).open();
      },
    ).open();
  }

  /**
   * 共享 POST 路径 (3 命令复用) — fetch + Notice 反馈.
   */
  private async postErrorCandidateAction(
    endpoint: "accept-candidate" | "dismiss-candidate" | "dispute-candidate",
    payload: unknown,
    successMsg: (result: any) => string,
  ): Promise<void> {
    const url = `${this.settings.backendUrl}/api/v1/errors/${endpoint}`;
    let resp: Response;
    try {
      // Wave-2 P0-1 (2026-05-12): 错误候选 3 命令 POST，同样需 X-CLS-Internal-Key
      resp = await fetch(url, {
        method: "POST",
        headers: this.buildBackendHeaders(),
        body: JSON.stringify(payload),
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      new Notice(`❌ 后端未连接 (${msg})`, 6000);
      return;
    }

    let parsed: any;
    try {
      parsed = await resp.json();
    } catch {
      new Notice(`❌ 后端返回非 JSON (HTTP ${resp.status})`, 6000);
      return;
    }

    if (!resp.ok) {
      const detail = parsed?.detail || `HTTP ${resp.status}`;
      new Notice(`❌ 失败: ${detail}`, 6000);
      return;
    }

    new Notice(successMsg(parsed), 5000);
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

    ctaEl.empty();
    const fixBtn = ctaEl.createEl("button", { text: `让 Canvas 切换到「${localName}」` });
    fixBtn.style.cssText = "padding: 6px 14px; cursor: pointer;";
    fixBtn.onclick = () => void this.handleSwitchToCurrent(bodyEl, ctaEl, localName, fixBtn);
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

  private async handleSwitchToCurrent(
    bodyEl: HTMLElement,
    ctaEl: HTMLElement,
    localName: string,
    btn: HTMLButtonElement,
  ): Promise<void> {
    btn.disabled = true;
    btn.setText("切换中...");
    const adapter = this.app.vault.adapter as unknown as { getBasePath?: () => string };
    const basePath = typeof adapter.getBasePath === "function" ? adapter.getBasePath() : "";
    if (!basePath) {
      new Notice("❌ 无法获取当前 vault 路径", 4000);
      btn.disabled = false;
      btn.setText(`让 Canvas 切换到「${localName}」`);
      return;
    }

    try {
      const backendUrl = this.plugin.settings.backendUrl.replace(/\/$/, "");
      const switchResp = await requestUrl({
        url: `${backendUrl}/api/v1/vault/switch`,
        method: "POST",
        contentType: "application/json",
        body: JSON.stringify({ vault_path: basePath }),
        throw: false,
      });
      if (switchResp.status === 200) {
        new Notice(`✓ Canvas 已切换到「${localName}」`, 5000);
        bodyEl.setText("切换成功，正在刷新状态...");
        ctaEl.empty();
        await this.detectAndRender(bodyEl, ctaEl);
      } else {
        const errBody = switchResp.json as { detail?: { message?: string } };
        const msg = (errBody?.detail?.message) || `HTTP ${switchResp.status}`;
        new Notice(`❌ 切换失败：${msg}`, 6000);
        btn.disabled = false;
        btn.setText(`让 Canvas 切换到「${localName}」`);
      }
    } catch (e) {
      new Notice(`❌ 切换异常：${(e as Error).message}`, 6000);
      btn.disabled = false;
      btn.setText(`让 Canvas 切换到「${localName}」`);
    }
  }

  /**
   * 高级配置折叠段（默认收起）— 含 BackendURL / 节点前缀 / 显式 vault 选择 dropdown
   * 非技术用户无需展开；进阶用户可手动调整 BackendURL、切换到任意 vault、改节点池前缀
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
        + "Wave-2 P0-1 修复: 之前 4 命令 (chat / study / node-chat / global-search) 全部漏带此 header → 生产 403。",
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

    // 老 vault selector dropdown 留在折叠段，进阶用户切换到任意 backend 已知 vault
    this.renderVaultSelector(inner);
  }

  /**
   * Story 2.2 follow-up · vault selector (legacy dropdown, 移到高级折叠段)
   *
   * 异步从 backend /api/v1/vault/list 拿候选列表（VAULTS_ROOT 下含 .obsidian/ 的目录），
   * 渲染 dropdown 让用户切换 active vault；选中变化时 POST /api/v1/vault/switch 触发
   * backend reload_settings + vault_id 表名前缀切换。
   */
  private renderVaultSelector(container: HTMLElement): void {
    const setting = new Setting(container)
      .setName("当前挂载 Vault")
      .setDesc(
        "选择 backend 当前挂载的 vault。切换后 backend 自动 reload + LanceDB 表名前缀切到对应 vault_id。"
        + "下拉项来自 backend VAULTS_ROOT 扫描（仅含 .obsidian/ 子目录的目录）。",
      );
    const statusEl = container.createEl("p", {
      text: "正在加载 vault 列表...",
      cls: "setting-item-description",
    });

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
            `❌ 无法加载 vault 列表 (HTTP ${resp.status}). 请确认 backend 正在运行 + Backend URL 正确。`,
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
        statusEl.setText(
          `VAULTS_ROOT: ${data.vaults_root} · 候选 ${data.vaults.length} 个 · 当前: ${data.active_vault}`,
        );

        setting.addDropdown((dropdown) => {
          for (const v of data.vaults) {
            dropdown.addOption(v.path, `${v.name} (${v.vault_id})`);
          }
          // 选中当前 active vault（按 path 匹配，is_active 由 backend 标注）
          const active = data.vaults.find((v) => v.is_active);
          if (active) {
            dropdown.setValue(active.path);
          }
          dropdown.onChange(async (newPath) => {
            const target = data.vaults.find((v) => v.path === newPath);
            if (!target) {
              new Notice(`❌ 未识别的 vault path: ${newPath}`, 4000);
              return;
            }
            new Notice(`正在切换到 ${target.name}...`, 2000);
            try {
              const switchUrl = `${this.plugin.settings.backendUrl.replace(/\/$/, "")}/api/v1/vault/switch`;
              const switchResp = await requestUrl({
                url: switchUrl,
                method: "POST",
                contentType: "application/json",
                body: JSON.stringify({ vault_path: newPath }),
                throw: false,
              });
              if (switchResp.status === 200) {
                this.plugin.settings.activeVaultName = target.name;
                await this.plugin.saveSettings();
                new Notice(
                  `✓ Vault 已切换到 ${target.name}\n后续对话/搜索使用新 vault 的隔离索引`,
                  6000,
                );
              } else {
                const errBody = switchResp.json as { detail?: { message?: string } };
                const msg =
                  (errBody && errBody.detail && errBody.detail.message)
                  || `HTTP ${switchResp.status}`;
                new Notice(`❌ 切换失败：${msg}`, 6000);
                // dropdown 回滚到当前 active
                if (active) dropdown.setValue(active.path);
              }
            } catch (e) {
              new Notice(`❌ 切换异常：${(e as Error).message}`, 6000);
              if (active) dropdown.setValue(active.path);
            }
          });
        });
      } catch (e) {
        statusEl.setText(`❌ 加载 vault 列表异常：${(e as Error).message}`);
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
 * Story 2.2 Phase A · Gap 1 fix: 让 Cmd+Shift+E 真实触发 Phase A 补充材料搜索
 *
 * 用户原话："Phase A 的 LanceDB 设计是要实现回答我问题的时候可以精确返回我需要的笔记片段"
 * 但旧 plugin 路径不带 user_question → backend 默认 mode=preload → Phase A 不触发。
 * 本 Modal 在用户没选中文本时弹出，让 user 输入问题；提交后随 enrich-context 一起发送给
 * backend 触发 mode=answer + supplementary search。留空 → 跳过补充材料（兼容旧行为）。
 */
class UserQuestionModal extends Modal {
  constructor(
    app: App,
    private onSubmit: (question: string) => void,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.createEl("h3", { text: "💬 你想问什么？" });
    contentEl.createEl("p", {
      text:
        "AI 会基于当前节点 + 你的问题，从你笔记库里找出最相关的 2-5 条补充材料。"
        + " 留空 → 跳过补充材料，仅注入邻居上下文。",
      cls: "setting-item-description",
    });

    const inputEl = contentEl.createEl("textarea", {
      attr: {
        rows: "4",
        style:
          "width: 100%; padding: 8px; font-family: var(--font-text); "
          + "font-size: var(--font-ui-medium); border-radius: 4px;",
        placeholder:
          "例：alpha-beta pruning 怎么优化 minimax 搜索？\n\n"
          + "（留空提交 → 跳过补充材料）",
      },
    });
    inputEl.focus();

    const btnRow = contentEl.createDiv({
      attr: { style: "margin-top: 12px; text-align: right;" },
    });

    const skipBtn = btnRow.createEl("button", {
      text: "跳过补充材料",
      attr: { style: "margin-right: 8px;" },
    });
    skipBtn.onclick = () => {
      this.onSubmit("");
      this.close();
    };

    const submitBtn = btnRow.createEl("button", {
      text: "提问 (⌘+Enter)",
      cls: "mod-cta",
    });
    submitBtn.onclick = () => {
      this.onSubmit(inputEl.value.trim());
      this.close();
    };

    inputEl.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        submitBtn.click();
      }
    });
  }

  onClose() {
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

// ═══════════════════════════════════════════════════════════════════════════════
// Story 2.5.X (D15 用户主权 C+) — Candidate selection + Dispute reason Modals
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Story 2.5.X Task 7 — FuzzySuggestModal 显示 pending candidates 让用户选条.
 *
 * 显示格式: "🟢 描述 (pedagogy_type, conf=0.85, seen=2)"
 */
class CandidateSuggestModal extends FuzzySuggestModal<ErrorCandidate> {
  constructor(
    app: App,
    private candidates: ErrorCandidate[],
    placeholder: string,
    private onPicked: (cand: ErrorCandidate) => void | Promise<void>,
  ) {
    super(app);
    this.setPlaceholder(placeholder);
  }

  getItems(): ErrorCandidate[] {
    return this.candidates;
  }

  getItemText(item: ErrorCandidate): string {
    return formatCandidateLabel(item);
  }

  onChooseItem(item: ErrorCandidate) {
    void this.onPicked(item);
  }
}

/**
 * Story 2.5.X Task 7 — Modal 让用户输入 dispute_reason (必填).
 */
class DisputeReasonModal extends Modal {
  private reason = "";

  constructor(
    app: App,
    private onConfirm: (reason: string) => void | Promise<void>,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h2", { text: "异议错误候选 — 写下你的理由" });
    contentEl.createEl("p", {
      text: "请说明为何认为 AI 误判。这条理由会写入 candidate.dispute_reason 字段，未来用于训练 prompt。",
    });

    const textarea = contentEl.createEl("textarea", {
      attr: {
        placeholder: "例如: 我没把 X 当成 Y, 我只是问它们的关系",
        rows: 4,
      },
    });
    textarea.style.width = "100%";
    textarea.addEventListener("input", () => {
      this.reason = textarea.value;
    });

    const btnRow = contentEl.createEl("div", {
      attr: { style: "margin-top: 12px; display: flex; gap: 8px; justify-content: flex-end;" },
    });
    const cancelBtn = btnRow.createEl("button", { text: "❌ 取消 (Esc)" });
    cancelBtn.addEventListener("click", () => this.close());

    const confirmBtn = btnRow.createEl("button", { text: "✅ 提交异议", cls: "mod-cta" });
    confirmBtn.addEventListener("click", async () => {
      this.close();
      await this.onConfirm(this.reason);
    });

    setTimeout(() => textarea.focus(), 50);
  }

  onClose() {
    this.contentEl.empty();
  }
}

/**
 * Round-23 Phase B0.3 (2026-05-11) — VaultOnboardingModal
 *
 * 用户首次打开新 Canvas vault（无 .canvas-config.yaml）时弹出，
 * 收集 display name + subject，自动生成 vault_id 并写入 yaml。
 *
 * 设计哲学：让用户加新 vault 零代码（不用手动编辑 yaml），
 * 避免中文 vault 名字段缺失导致 backend sanitize 坍缩 default 表（数据泄漏）。
 */
class VaultOnboardingModal extends Modal {
  private displayName = "";
  private subject = "";

  constructor(
    app: App,
    private onSubmit: (input: { displayName: string; subject: string }) => void | Promise<void>,
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();

    contentEl.createEl("h2", { text: "🎓 欢迎使用 Canvas Learning System" });
    contentEl.createEl("p", {
      text: "检测到这是一个新的 Canvas vault（缺少 .canvas-config.yaml）。请填写基本信息：",
    });

    // Display name 输入
    const nameLabel = contentEl.createEl("label", {
      text: "Vault 显示名（如 \"CS 61B 数据结构\" / \"数学 101\"）：",
      attr: { style: "display: block; margin-top: 12px; font-weight: 600;" },
    });
    const nameInput = nameLabel.createEl("input", {
      type: "text",
      attr: {
        placeholder: "CS 61B 数据结构",
        style: "width: 100%; padding: 6px; margin-top: 4px;",
      },
    });
    nameInput.addEventListener("input", () => {
      this.displayName = nameInput.value;
    });

    // Subject 输入（可选）
    const subjLabel = contentEl.createEl("label", {
      text: "学科机器代码（lowercase + 数字 + 连字符，如 \"cs-61b\" / \"math-101\"，可留空走 general）：",
      attr: { style: "display: block; margin-top: 12px; font-weight: 600;" },
    });
    const subjInput = subjLabel.createEl("input", {
      type: "text",
      attr: {
        placeholder: "cs-61b",
        style: "width: 100%; padding: 6px; margin-top: 4px;",
      },
    });
    subjInput.addEventListener("input", () => {
      this.subject = subjInput.value.trim();
    });

    // 提示
    contentEl.createEl("p", {
      text: "ℹ️ vault_id 自动从 display name 生成（保留中文 / 数字 / 字母 / 连字符）",
      attr: { style: "margin-top: 12px; font-size: 12px; color: var(--text-muted);" },
    });

    // 按钮行
    const btnRow = contentEl.createEl("div", {
      attr: {
        style: "margin-top: 16px; display: flex; gap: 8px; justify-content: flex-end;",
      },
    });
    const skipBtn = btnRow.createEl("button", {
      text: "❌ 跳过（手动建 yaml）",
    });
    skipBtn.addEventListener("click", () => {
      new Notice(
        "已跳过 onboarding。Canvas Skill 将无法工作直到 .canvas-config.yaml 创建。\n"
          + "随时可用命令面板搜 'Canvas: 重新初始化 vault' 重新触发。",
        8000,
      );
      this.close();
    });

    const submitBtn = btnRow.createEl("button", {
      text: "✅ 创建配置",
      cls: "mod-cta",
    });
    submitBtn.addEventListener("click", async () => {
      if (!this.displayName.trim()) {
        new Notice("请填写 vault 显示名", 4000);
        return;
      }
      this.close();
      await this.onSubmit({
        displayName: this.displayName.trim(),
        subject: this.subject,
      });
    });

    setTimeout(() => nameInput.focus(), 50);
  }

  onClose() {
    this.contentEl.empty();
  }
}
