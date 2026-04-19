export const CALLOUT_TYPES = [
  "question",
  "tip",
  "error",
  "hint",
  "note",
  "warning",
  "info",
] as const;

export type CalloutType = (typeof CALLOUT_TYPES)[number];

export function wrapSelection(text: string, type: CalloutType): string {
  const lines = text.split("\n").map((line) => `> ${line}`).join("\n");
  return `> [!${type}]\n${lines}`;
}
