import { query } from '@anthropic-ai/claude-agent-sdk';

const mcpServers = {
  canvas: { type: 'sse', url: 'http://localhost:8001/mcp' },
};

try {
  console.error('[test] Starting query with MCP server...');
  const result = query({
    prompt: 'Call the record_learning_memory tool with these exact arguments: node_id="test-sdk", entity_type="Misconception", concept="Binary Search", topic="Algorithms", details="Student confused about loop invariant"',
    options: {
      mcpServers,
      maxTurns: 3,
      effort: 'high',
      permissionMode: 'default',
      canUseTool: async (toolName, input, options) => {
        console.error(`[test] canUseTool: ${toolName}`);
        return { behavior: 'allow' };
      },
    },
  });

  for await (const msg of result) {
    if (msg.type === 'stream_event') {
      const event = msg.event;
      if (event?.type === 'content_block_delta' && event?.delta?.type === 'text_delta') {
        process.stderr.write(event.delta.text);
      }
      if (event?.type === 'content_block_start' && event?.content_block?.type === 'tool_use') {
        console.error(`\n[test] Tool use: ${event.content_block.name} ${JSON.stringify(event.content_block.input)}`);
      }
    }
    if (msg.type === 'assistant') {
      const content = msg.message?.content;
      if (Array.isArray(content)) {
        for (const block of content) {
          if (block.type === 'tool_use') {
            console.error(`[test] Assistant tool_use: ${block.name} ${JSON.stringify(block.input).slice(0, 200)}`);
          }
          if (block.type === 'tool_result') {
            console.error(`[test] Tool result: ${JSON.stringify(block.content).slice(0, 300)}`);
          }
        }
      }
    }
    if (msg.type === 'result') {
      console.error(`\n[test] Result subtype: ${msg.subtype}`);
      console.error(`[test] is_error: ${msg.is_error}`);
      console.error(`[test] session_id: ${msg.session_id}`);
      break;
    }
  }
} catch (err) {
  console.error(`[test] CAUGHT ERROR: ${err.message}`);
  console.error(`[test] Stack: ${err.stack?.slice(0, 500)}`);
}

process.exit(0);
