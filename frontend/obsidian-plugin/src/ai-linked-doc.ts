export function buildAIDocPrompt(
  selected: string,
  sourcePath: string,
  subject: string,
): string {
  return (
    `/ai-linked-doc\n` +
    `选中文本:\n${selected}\n\n` +
    `源笔记路径: ${sourcePath}\n` +
    `学科: ${subject}\n\n` +
    `请为这段内容创建一个概念文档（三段式：## 核心概念 / ## 关键点 / ## 关联概念）。`
  );
}
