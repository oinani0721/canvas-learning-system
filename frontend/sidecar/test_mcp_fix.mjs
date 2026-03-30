import { query } from '@anthropic-ai/claude-agent-sdk';

const mcpServers = {
  canvas: { type: 'sse', url: 'http://localhost:8001/mcp' },
};

try {
  console.error('[test] Starting query with FIXED canUseTool...');
  const result = query({
    prompt: 'Call the record_learning_memory MCP tool with: node_id="test-fix", entity_type="Misconception", concept="Binary Search", topic="Algorithms", details="Student confused about loop invariant". Report the exact result you get back.',
    options: {
      mcpServers,
      maxTurns: 5,
      effort: 'high',
      permissionMode: 'default',
      canUseTool: async (toolName, input, options) => {
        console.error(`[test] canUseTool: ${toolName}`);
        // FIX: Include updatedInput in the return value
        return { behavior: 'allow', updatedInput: input };
      },
    },
  });

  for await (const msg of result) {
    if (msg.type === 'stream_event') {
      const event = msg.event;
      if (event?.type === 'content_block_delta' && event?.delta?.type === 'text_delta') {
        process.stderr.write(event.delta.text);
      }
    }
    if (msg.type === 'user') {
      const content = msg.message?.content;
      if (Array.isArray(content)) {
        for (const block of content) {
          if (block.type === 'tool_result') {
            console.error(`\n[test] TOOL_RESULT: ${JSON.stringify(block.content).slice(0, 500)}`);
          }
        }
      }
    }
    if (msg.type === 'result') {
      console.error(`\n[test] RESULT: subtype=${msg.subtype} is_error=${msg.is_error}`);
      break;
    }
  }
} catch (err) {
  console.error(`\n[test] ERROR: ${err.message}`);
}

process.exit(0);
