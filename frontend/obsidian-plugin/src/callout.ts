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
  return `${header}\n${checkboxes}\n>\n${body}`;
}
