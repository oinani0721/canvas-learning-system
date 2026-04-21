export function buildAIDocPrompt(
  selected: string,
  sourcePath: string,
  activeBoard?: string,
): string {
  const activeBoardLine = activeBoard
    ? `活动白板: ${activeBoard}\n`
    : `活动白板: (Skill 会从 .canvas-config.yaml 或 AskUserQuestion 确定)\n`;

  return (
    `/ai-linked-doc\n` +
    `Please invoke the Skill tool with skill_name="ai-linked-doc" to handle this request.\n` +
    `Do NOT answer freely — follow the 8-step Skill flow strictly.\n` +
    `\n` +
    `选中文本:\n${selected}\n\n` +
    `源笔记路径: ${sourcePath}\n` +
    activeBoardLine +
    `\n` +
    `请为这段内容派生一个新概念节点（扁平架构：节点/<concept>.md + 更新 原白板/<active_board>.md 的 ## Concepts）。`
  );
}

export function isBoardsPath(sourcePath: string): boolean {
  return sourcePath !== "unknown" && sourcePath.startsWith("原白板/");
}

export function isNodesPath(sourcePath: string): boolean {
  return sourcePath !== "unknown" && sourcePath.startsWith("节点/");
}

export function isFlatArchPath(sourcePath: string): boolean {
  return isBoardsPath(sourcePath) || isNodesPath(sourcePath);
}

export function extractBoardNameFromPath(sourcePath: string): string | null {
  if (!isBoardsPath(sourcePath)) return null;
  const filename = sourcePath.substring("原白板/".length);
  return filename.endsWith(".md")
    ? filename.substring(0, filename.length - 3)
    : filename;
}
