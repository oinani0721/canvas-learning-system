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
    const headerMatch = lines[i].match(
      /^>\s*\[!(tips|error|question|keypoint)\][+-]\s*(.*)$/i,
    );
    if (!headerMatch) {
      i++;
      continue;
    }
    const tag = headerMatch[1].toLowerCase();
    const tagLabel = headerMatch[2].trim();

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

    const hash = await sha256Hex(
      `${nodeId}|${tag}|${understanding}|${calloutContent}`,
    );
    callouts.push({
      tag,
      tagLabel,
      understanding,
      content: calloutContent,
      contentHash: hash,
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

export function wrapSelection(
  text: string,
  tag: TagOption,
  understanding: UnderstandingValue,
): string {
  const header = `> [!${tag.callout}]+ ${tag.label}`;
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
