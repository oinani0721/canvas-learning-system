/**
 * MVP-α-3 (2026-05-14) — Quick Exam markdown UI.
 *
 * 用户体验 (来自 _bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md §1):
 *   T=4:00 Dashboard 点 "🎯 一键考察"
 *     → 反馈瞬间 #4: 后端 5s 内生成 1 道题, 引用用户批注原话
 *     → plugin 把题目写成 canvas-vault/节点/考察-{concept}-{date}.md
 *     → workspace.openLinkText 打开
 *   T=6:00 用户手写答案
 *   T=8:00 Cmd+S 保存
 *     → 反馈瞬间 #5: vault.on('modify') 监听 → POST /grade → 文件底部追加反馈
 *
 * Backend 接口 (协调文档 §5 锁定):
 *   POST /api/v1/exam/quick  body: {node_id, vault_id?}   resp: {question_id, question_text, generated_at?}
 *   POST /api/v1/exam/grade  body: {question_id, user_answer}  resp: {score, feedback, mastery_delta?}
 *
 * 设计:
 *   - 同 status-bar.ts: pure functions + thin Controller, 后者 wiring 在 main.ts
 *   - 答题文件在 节点/ 下 (spec 要求) — 用日期 + 重名递增 -1/-2 避免覆盖
 *   - vault.on('modify') 仅对已注册的考察文件 (Map<path, session>) 触发评分
 *   - "已评分" flag 防重复 grade (用户多次 Cmd+S 不应反复打分)
 *   - 静默失败回退 Notice 文案 (callBackend 已有失败 Notice, 不重复触发)
 */

import type { App, TFile, Vault } from "obsidian";

// ─────────────────────────────────────────────────────────────
// Pure functions (testable)
// ─────────────────────────────────────────────────────────────

/**
 * 构造考察文件路径.
 *
 *   buildExamFilePath("递归", "2026-05-14")         → "节点/考察-递归-2026-05-14.md"
 *   buildExamFilePath("递归", "2026-05-14", 1)      → "节点/考察-递归-2026-05-14-1.md"
 *
 * concept 内空白被替换成 - 防 wikilink 解析歧义.
 */
export function buildExamFilePath(
  concept: string,
  date: string,
  suffix?: number,
): string {
  const safeConcept = (concept || "unknown").trim().replace(/\s+/g, "-");
  const safeDate = (date || "").trim();
  const tail = suffix !== undefined && suffix > 0 ? `-${suffix}` : "";
  return `节点/考察-${safeConcept}-${safeDate}${tail}.md`;
}

/** 今日 YYYY-MM-DD (UTC+8 简化版 — 用 ISO date 取前 10 字符). */
export function todayDateStr(now: Date = new Date()): string {
  return now.toISOString().slice(0, 10);
}

/**
 * 构造考察文件 markdown body.
 *
 * 协议 (来自用户 prompt):
 *   # 考察: {concept}
 *   ## 题目
 *   {question_text}
 *   ## 你的回答
 *   [在此填写]
 *   ## 提交 (Cmd+S 自动触发评分)
 *
 * frontmatter 写入 question_id + source_concept, 让 vault.on('modify') 回调能从
 * 文件本身回查 backend session, 不依赖 in-memory map (插件 reload 后仍可继续答题).
 */
export function buildExamFileBody(input: {
  concept: string;
  questionId: string;
  questionText: string;
  generatedAt?: string;
}): string {
  const lines: string[] = [
    "---",
    `exam_question_id: ${input.questionId}`,
    `source_concept: ${input.concept}`,
    `generated_at: ${input.generatedAt ?? new Date().toISOString()}`,
    "exam_status: pending",
    "---",
    "",
    `# 考察: ${input.concept}`,
    "",
    "## 题目",
    "",
    input.questionText.trim(),
    "",
    "## 你的回答",
    "",
    "[在此填写]",
    "",
    "## 提交 (Cmd+S 自动触发评分)",
    "",
    "保存文件即自动调用后端评分, 评分结果会追加到文件底部 ## 反馈 段.",
    "",
  ];
  return lines.join("\n");
}

/**
 * 提取 "## 你的回答" 段的内容.
 *
 * - 起点: "## 你的回答" 之后第一行
 * - 终点: 下一个 "## " 标题 (不含) / 文件末尾
 * - 去掉占位符 "[在此填写]" — 如果用户没改这个文本, 视作未作答返回 null
 * - 去除前后空行后, 内容为空 → 返回 null (调用方判断是否触发 grade)
 */
export function extractAnswer(content: string): string | null {
  const lines = content.split("\n");
  const start = lines.findIndex((l) => l.trim().startsWith("## 你的回答"));
  if (start === -1) return null;

  const body: string[] = [];
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith("## ")) break;
    body.push(line);
  }

  const text = body.join("\n").trim();
  if (!text) return null;
  if (text === "[在此填写]") return null;
  // 用户保留占位符但加了内容 — 把占位符行剔除
  const cleaned = body
    .filter((l) => l.trim() !== "[在此填写]")
    .join("\n")
    .trim();
  return cleaned || null;
}

/**
 * 判断文件是否已经追加过 "## 反馈" 段 (防重复 grade).
 *
 * 注意: 中文字符在 JS regex 不算 \w, "反馈" 后的 \b 永远不匹配 → 不能用 \b
 * 把"## 反馈" 跟段标题锚定的责任交给 `^##\s*` 部分 (行首 + 两个 #),
 * 普通文本里的 "反馈" 不会以 ## 开头, 所以无需额外 word-boundary.
 */
export function hasFeedbackSection(content: string): boolean {
  return /^##\s*反馈/m.test(content);
}

/**
 * 构造追加到文件末尾的反馈区文本.
 *
 *   ## 反馈 (4/5)
 *
 *   你说对了核心,但 base case 写法可以更紧凑...
 *
 * 前置 \n\n 保证跟前文段隔行, 末尾 \n 让追加多次仍有换行.
 */
export function buildFeedbackAppend(input: {
  score: number;
  feedback: string;
}): string {
  const safeScore = Math.max(0, Math.min(5, Math.round(input.score)));
  const text = (input.feedback ?? "").trim() || "(后端未返回文字反馈)";
  return `\n\n## 反馈 (${safeScore}/5)\n\n${text}\n`;
}

// ─────────────────────────────────────────────────────────────
// Controller (thin wiring, depends on Obsidian runtime)
// ─────────────────────────────────────────────────────────────

/**
 * QuickExamController 需要的最小 plugin 接口.
 *
 * - app: Obsidian app (vault / workspace / metadataCache)
 * - callBackendJson: 发 backend 请求并返回 JSON (失败已自动 Notice, 失败时返回 null)
 * - inferVaultId: 当前 vault_id (用于 backend session 路由)
 */
export interface QuickExamPluginAPI {
  app: App;
  callBackendJson(
    endpoint: string,
    label: string,
    body: Record<string, unknown>,
    method?: "GET" | "POST",
  ): Promise<unknown | null>;
  inferCurrentVaultId(): string;
}

interface ExamSession {
  questionId: string;
  concept: string;
  filePath: string;
  graded: boolean;
}

export class QuickExamController {
  private sessions = new Map<string, ExamSession>();

  constructor(private plugin: QuickExamPluginAPI) {}

  /**
   * 命令面板入口 "canvas:start-quick-exam".
   *
   * 流程:
   *   1. active file 必须在 节点/ 下 → 取 basename 作为 concept
   *   2. Notice "🤔 正在生成题目..." (反馈瞬间 #4 开端)
   *   3. POST /api/v1/exam/quick → 拿 question_text
   *   4. 生成 节点/考察-{concept}-{date}.md (含 frontmatter exam_question_id)
   *   5. workspace.openLinkText 打开新文件 (新 tab)
   *   6. 注册 session 让 onFileModified 能识别这个文件
   *   7. Notice "📄 题目已生成"
   */
  async startExam(NoticeCtor: typeof import("obsidian").Notice): Promise<void> {
    const active = this.plugin.app.workspace.getActiveFile();
    if (!active) {
      new NoticeCtor("请先打开你想考察的节点 (节点/<concept>.md)", 5000);
      return;
    }
    if (!active.path.startsWith("节点/") || active.basename.startsWith("考察-")) {
      new NoticeCtor(
        "考察命令需在 节点/<concept>.md 上触发 (不要在考察文件本身或其他目录)",
        5000,
      );
      return;
    }

    const concept = active.basename;
    new NoticeCtor("🤔 正在生成题目...", 3000);

    const resp = await this.plugin.callBackendJson(
      "/api/v1/exam/quick",
      `生成 "${concept}" 的考察题`,
      {
        node_id: concept,
        vault_id: this.plugin.inferCurrentVaultId(),
      },
      "POST",
    );
    if (!resp) return; // callBackendJson 已发失败 Notice
    const r = resp as {
      question_id?: string;
      question_text?: string;
      generated_at?: string;
    };
    if (!r.question_id || !r.question_text) {
      new NoticeCtor(
        "后端返回数据缺 question_id / question_text — 接口契约未对齐",
        6000,
      );
      return;
    }

    const filePath = await this.resolveUniquePath(concept);
    const body = buildExamFileBody({
      concept,
      questionId: r.question_id,
      questionText: r.question_text,
      generatedAt: r.generated_at,
    });
    let file: TFile;
    try {
      file = await this.plugin.app.vault.create(filePath, body);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      new NoticeCtor(`❌ 创建考察文件失败: ${msg}`, 6000);
      return;
    }

    this.sessions.set(file.path, {
      questionId: r.question_id,
      concept,
      filePath: file.path,
      graded: false,
    });

    await this.plugin.app.workspace.openLinkText(file.path, "", true);
    new NoticeCtor(`📄 题目已生成: ${file.basename}`, 4000);
  }

  /**
   * vault.on('modify') 回调.
   *
   * 仅当 file 在已注册 sessions 内且未评分时触发评分.
   * 评分成功后 graded=true, 用户继续编辑同文件不会反复 grade.
   *
   * 注意: 本方法被 Obsidian 高频触发 (用户每次按键 / autosave 都打), 必须先 fast
   * filter 排除非考察文件. 实际网络调用在 grade flag 守门后.
   */
  async onFileModified(
    file: TFile,
    NoticeCtor: typeof import("obsidian").Notice,
  ): Promise<void> {
    const session = this.sessions.get(file.path);
    if (!session || session.graded) return;

    const content = await this.plugin.app.vault.read(file);
    if (hasFeedbackSection(content)) {
      // 反馈已写但 session 标记仍 pending — 强制标 graded 防再次进入
      session.graded = true;
      return;
    }
    const answer = extractAnswer(content);
    if (!answer) return; // 用户还没填写

    // 防并发 grade (两次快速保存) — 提前标记
    session.graded = true;

    new NoticeCtor("⏳ 正在评分...", 3000);
    const resp = await this.plugin.callBackendJson(
      "/api/v1/exam/grade",
      `评分 "${session.concept}"`,
      {
        question_id: session.questionId,
        user_answer: answer,
      },
      "POST",
    );
    if (!resp) {
      // backend 调用失败 → 放回 ungraded 让用户改答案后再试
      session.graded = false;
      return;
    }
    const r = resp as { score?: number; feedback?: string };
    if (r.score === undefined || r.feedback === undefined) {
      session.graded = false;
      new NoticeCtor(
        "后端返回数据缺 score / feedback — 接口契约未对齐",
        6000,
      );
      return;
    }

    const appendText = buildFeedbackAppend({
      score: r.score,
      feedback: r.feedback,
    });
    // Obsidian 没有 vault.append, 用 process(file, fn) atomic read-modify-write.
    // process 会自动 dedupe 并发修改, 比 read+modify 安全.
    await this.plugin.app.vault.process(file, (current) => current + appendText);
    new NoticeCtor(`✅ 评分完成: ${r.score}/5`, 5000);
  }

  /**
   * 找一个不重名的 节点/考察-{concept}-{date}.md 路径.
   *
   * - 首选 suffix=undefined → "节点/考察-X-2026-05-14.md"
   * - 已存在则 -1, -2, -3... 上限 99 防爆
   */
  private async resolveUniquePath(concept: string): Promise<string> {
    const date = todayDateStr();
    const exists = (p: string) =>
      this.plugin.app.vault.getAbstractFileByPath(p) !== null;

    const primary = buildExamFilePath(concept, date);
    if (!exists(primary)) return primary;

    for (let n = 1; n < 100; n++) {
      const p = buildExamFilePath(concept, date, n);
      if (!exists(p)) return p;
    }
    // 极端情况: 一天里同一节点考察 100 次 — fallback timestamp
    return buildExamFilePath(concept, date, Date.now());
  }
}

/**
 * Vault append 兜底 — 老版本 Obsidian 没 vault.append, 这里 inline shim.
 *
 * 不导出, controller 通过 plugin.app.vault.append 调用 — modern Obsidian (1.0+)
 * 都支持. 若 build target 触及更老版本, 在 main.ts 用 vault.read + vault.modify
 * 重新实现.
 */
export type { Vault };
