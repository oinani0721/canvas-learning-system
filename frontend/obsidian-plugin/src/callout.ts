export const TAG_OPTIONS = [
  { value: "tips", label: "💡 Tips", callout: "tips" },
  { value: "error", label: "❌ 错误", callout: "error" },
  { value: "question", label: "❓ 提问", callout: "question" },
  { value: "keypoint", label: "📌 关键点", callout: "keypoint" },
] as const;

export type TagOption = (typeof TAG_OPTIONS)[number];
export type TagValue = TagOption["value"];

export const UNDERSTANDING_OPTIONS = [
  { value: "understood", label: "✅ 已懂" },
  { value: "fuzzy", label: "🤔 模糊" },
  { value: "not-understood", label: "❌ 不懂" },
] as const;

export type UnderstandingOption = (typeof UNDERSTANDING_OPTIONS)[number];
export type UnderstandingValue = UnderstandingOption["value"];

/**
 * P0-6 (2026-05-14): callout 末尾追加一个空 "> " 行作为用户输入区。
 * UnderstandingModal.onChooseItem 会在 replaceSelection 后把光标停在这一行，
 * 让用户能直接继续输入自己对原文的理解 / 疑问 / 批注。
 *
 * 输出格式：
 *   > [!tips]+ 💡 Tips
 *   > - [ ] ✅ 已懂
 *   > - [x] 🤔 模糊
 *   > - [ ] ❌ 不懂
 *   >
 *   > {选中的原文}
 *   >
 *   > {光标停这里 ← 用户继续输入}
 */
// F1 (2026-05-14): v1 用空 "> " 但 Obsidian Live Preview 把纯空 callout 行
// 渲染为 0 高度结构装饰，用户看不到光标。v2 改成 visible 占位符 — Live Preview
// 必须渲染（含可见字符），占位符本身是 prompt 提示。
// 见 forum.obsidian.md/t/88607 + 5-14 4-agent 调研报告。
export const USER_INPUT_PROMPT = "> ✍️ 我的理解：";

// ═══════════════════════════════════════════════════════════════════════════════
// Story 2.4 Plan B Phase 1 (2026-05-14): Callout Parser + SHA256 dedup hash
//
// 用于 CalloutSyncDebouncer：监听 vault.on('modify') 后解析文件全部 callout，
// 用 content_hash 跟 backend 做幂等同步（同 hash 跳过，不同 hash 创建 v2 episode）。
// ═══════════════════════════════════════════════════════════════════════════════

export interface ParsedCallout {
  tag: string; // tips / error / question / keypoint
  tagLabel: string; // "💡 Tips" 等
  understanding: string; // understood / fuzzy / not-understood / ""
  content: string; // callout body（含用户输入的"我的理解"），已去掉 checkbox 行
  contentHash: string; // SHA256(node_id|tag|understanding|content)
  annotationId: string; // P0 (A+-prime): 稳定逻辑身份 cb-xxx, 无则 ""（历史批注回退首行）
}

// P0 (A+-prime 2026-06-26): 批注稳定身份标记。嵌在 callout 标题行
// "> [!tips]+ 💡 Tips %%cb-xxx%%" — %%%% 是 Obsidian 原生注释(阅读模式隐藏),
// 标题行是解析锚点且最不易被用户编辑。身份从"首行内容"迁到此 id →
// 改批注正文不再换身份(防孤儿)，同节点同一句原文的两条不同批注不再碰撞合并。
const ANNOTATION_ID_RE = /%%\s*(cb-[a-z0-9]+)\s*%%/i;

/**
 * 生成稳定批注 id（本地生成，不依赖后端回执；插入后永不改变）。
 * 格式 cb-<base36 时间><base36 随机> — 单用户场景碰撞安全 + 大致按时间可排序。
 */
export function generateAnnotationId(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 6);
  return `cb-${ts}${rand}`;
}

/**
 * 从文件内容提取所有 [!tag]+ callout（4 种类型：tips/error/question/keypoint）。
 *
 * 跳过：
 *   - 非 4-tag callout（如 [!tip] 单数 / [!note] / [!warning]）
 *   - 空 callout（无 body 内容）
 *
 * 返回：ParsedCallout[] — 包含 content_hash 用于 backend 幂等去重
 */
export async function parseCalloutsFromContent(
  content: string,
  nodeId: string,
): Promise<ParsedCallout[]> {
  const callouts: ParsedCallout[] = [];
  const lines = content.split("\n");
  let i = 0;

  while (i < lines.length) {
    // Plan A v2 (2026-05-14): 严格协议 — 4 路 agent 对抗审查共识
    //
    // 双 telltale 防误识别:
    //   1. 仅 4 种复数 tag (tips/error/question/keypoint) — 对齐 plugin UI
    //      TAG_OPTIONS (line 2-7), 排除 [!tip] 单数 (Story 1.16 4-tag 决策更新版)
    //   2. +/- 后缀必填 — Story 2.4 spec AC#3 折叠/展开两态都要识别,
    //      模板 [!tip] 💬 (node-derivation.ts:218 自动生成) 无后缀, 双不匹配排除
    //
    // 协议规约 (用户 callout vs 模板 hint):
    //   - 用户 Cmd+Shift+A 写: [!tips]+ / [!error]+ / [!question]+ / [!keypoint]+
    //   - 模板/AI 自动写: [!tip] (单数无后缀) / [!quote]+ / [!relation/*]+ / [!info]+ 等
    //   - 4 个复数 tag 是 "用户保留" 命名空间, 模板不准用
    //
    // 见 _bmad-output/research/2026-05-14-plan-b-postmortem.md
    //
    // 实测修复 (2026-06-11, 与后端 F6 同款): 用户在列表项内批注时, Obsidian 写出
    // `* > [!tips]+` 带列表前缀 — 旧正则锚定 ^> 漏识别, 用户批注全部静默丢失。
    // 头部允许可选列表前缀 (*/+/- + 空格); body 续行同样兼容。
    const headerMatch = lines[i].match(
      /^(?:\s*[*+-]\s+)?>\s*\[!(tips|error|question|keypoint)\][+-]\s*(.*)$/i,
    );
    if (!headerMatch) {
      i++;
      continue;
    }
    const tag = headerMatch[1].toLowerCase();
    const rawLabel = headerMatch[2].trim();
    // P0: 从标题行提取稳定 id, 并从 label 剥离 %%cb-xxx%%
    const idMatch = rawLabel.match(ANNOTATION_ID_RE);
    const annotationId = idMatch ? idMatch[1] : "";
    const tagLabel = rawLabel.replace(ANNOTATION_ID_RE, "").trim();

    // 收集后续连续 `>` 开头的行作为 callout body
    const bodyLines: string[] = [];
    i++;
    while (i < lines.length && lines[i].startsWith(">")) {
      bodyLines.push(lines[i].replace(/^>\s?/, ""));
      i++;
    }

    // 从 body 提取 understanding（首个 [x] checkbox）
    let understanding = "";
    for (const bl of bodyLines) {
      const cbMatch = bl.match(/^-\s*\[x\]\s*(.*)$/);
      if (cbMatch) {
        const label = cbMatch[1];
        if (label.includes("已懂")) understanding = "understood";
        else if (label.includes("模糊")) understanding = "fuzzy";
        else if (label.includes("不懂")) understanding = "not-understood";
        break;
      }
    }

    // content = 去掉所有 checkbox 行 + 空行后剩余文本
    const contentLines = bodyLines.filter(
      (bl) => !bl.match(/^-\s*\[[ x]\]/) && bl.trim() !== "",
    );
    const calloutContent = contentLines.join("\n").trim();
    if (!calloutContent) continue; // 空 callout 跳过
    // MEDIUM-2 (Code-Review 2026-07-16): P7 直插后弃置的空疑问（内容只剩占位符）
    // 不入 sync 通道 — 它不是用户写下的疑问，收割进 Graphiti/归纳链是纯噪音。
    if (calloutContent === NEW_QUESTION_PLACEHOLDER) continue;

    const hash = await sha256Hex(
      `${nodeId}|${tag}|${understanding}|${calloutContent}`,
    );
    callouts.push({
      tag,
      tagLabel,
      understanding,
      content: calloutContent,
      contentHash: hash,
      annotationId,
    });
  }

  return callouts;
}

async function sha256Hex(text: string): Promise<string> {
  const enc = new TextEncoder();
  const buf = await crypto.subtle.digest("SHA-256", enc.encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// P7 (2026-07-16 UAT): 自发新疑问的可见输入占位符 — F1 教训同款（Live Preview
// 把纯空 "> " 行渲染成 0 高度，光标不可见，占位符必须含可见字符）。
export const NEW_QUESTION_PROMPT = "> ✍️ 我的疑问：";

// MEDIUM-2 (Code-Review 2026-07-16): 占位符裸内容（"> " 剥离后）。用户插入后
// 弃置不填时 callout 内容恰等于它 — parse 侧据此跳过，防止空疑问被 sync/归纳
// 链当成真疑问收割（wrapSelection 的占位符无此问题：其 callout 恒含选中原文）。
export const NEW_QUESTION_PLACEHOLDER = "✍️ 我的疑问：";

/**
 * P7 (2026-07-16): 直插时的隔离空行决策 — 并块防护的纯函数部分（可测）。
 * callout 上下紧邻 ">" 行会被 Obsidian 合并成同一个 callout，按需垫空行：
 *   - 锚点行非空 → lead "\n\n"（行尾另起空行再插）
 *   - 锚点行空但上一行有内容（可能是 ">" 行）→ lead "\n"（保留本空行作隔离）
 *   - 锚点行与上一行都空 → lead ""（原地起块）
 * lead 只含 "\n"，条数 = 锚点行之后新增的行数（handler 光标算术依赖此不变量）。
 * tail：下一行有内容时垫一空行防向下并块。
 */
export function computeInsertionSpacing(
  currentLine: string,
  prevLine: string,
  nextLine: string,
): { lead: string; tail: string } {
  let lead: string;
  if (currentLine.trim() !== "") {
    lead = "\n\n";
  } else if (prevLine.trim() !== "") {
    lead = "\n";
  } else {
    lead = "";
  }
  return { lead, tail: nextLine.trim() !== "" ? "\n" : "" };
}

/**
 * P7 (2026-07-16 UAT): 凭空直插一条空白 question callout（"自发写新疑问"场景，
 * 与选中式 wrapSelection 互补 — 后者硬要求已有文本）。
 *
 * 格式契约（三条下游链同时依赖，改动前必须核对）：
 *   - /quiz-answer 疑问归纳 Grep：`^>\s*\[!question\]\+`
 *   - /start-exam-board 安全抽取器：`>\s*\[!(question|error)\]\+`
 *   - parseCalloutsFromContent 双 telltale：4 复数 tag + [+-] 后缀
 * annotationId 同 wrapSelection 的 %%cb-xxx%% 稳定身份协议（A+-prime）。
 */
export function buildNewQuestionCallout(annotationId?: string): string {
  const question = TAG_OPTIONS.find((t) => t.value === "question")!;
  const idMarker = annotationId ? ` %%${annotationId}%%` : "";
  return `> [!${question.callout}]+ ${question.label}${idMarker}\n${NEW_QUESTION_PROMPT}`;
}

export function wrapSelection(
  text: string,
  tag: TagOption,
  understanding: UnderstandingValue,
  annotationId?: string,
): string {
  // P0: 稳定身份嵌入标题行(隐藏注释)。两条捕获通道(即时上报/停笔回填)
  // 解析同一文件 → 同 id → Graphiti 同一逻辑身份, 不再靠首行内容判定。
  const idMarker = annotationId ? ` %%${annotationId}%%` : "";
  const header = `> [!${tag.callout}]+ ${tag.label}${idMarker}`;
  const checkboxes = UNDERSTANDING_OPTIONS.map(
    (opt) => `> - [${opt.value === understanding ? "x" : " "}] ${opt.label}`,
  ).join("\n");
  const body = text
    .split("\n")
    .map((line) => `> ${line}`)
    .join("\n");
  // 末尾结构：[原文] → 空 ">" 分隔行 → "> " 用户输入区（带尾随空格，光标停这里）
  return `${header}\n${checkboxes}\n>\n${body}\n>\n${USER_INPUT_PROMPT}`;
}


/**
 * 块级插入包裹 (2026-07-25, UAT ⑧ 实操抓到的边界 bug):
 * callout 的 `>` 必须在行首才渲染为块 — 选区在行内时原地替换会把 callout
 * 粘进句子中间 → 渲染碎裂 + FrontmatterTipsSync 行首正则解析不到 (不入
 * tips[] 也不直连)。按选区前后文决定补换行。
 *
 * @param wrapped   wrapSelection 的输出
 * @param fromCh    选区起点列号 (>0 = 行内起点, 前面还有文字)
 * @param tailAfter 选区终点到行尾的剩余文本
 */
export function padBlockInsert(
  wrapped: string,
  fromCh: number,
  tailAfter: string,
): { text: string; leadingNewlines: number } {
  const needsLeading = fromCh > 0;
  const needsTrailing = tailAfter.trim().length > 0;
  return {
    text: (needsLeading ? "\n\n" : "") + wrapped + (needsTrailing ? "\n\n" : ""),
    leadingNewlines: needsLeading ? 2 : 0,
  };
}
