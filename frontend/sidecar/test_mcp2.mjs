import { query } from '@anthropic-ai/claude-agent-sdk';

const mcpServers = {
  canvas: { type: 'sse', url: 'http://localhost:8001/mcp' },
};

try {
  console.error('[test] Starting query...');
  const result = query({
    prompt: 'Call the record_learning_memory MCP tool with: node_id="test-sdk-2", entity_type="Misconception", concept="Binary Search", topic="Algorithms", details="test details". Report the exact result you get back.',
    options: {
      mcpServers,
      maxTurns: 5,
      effort: 'high',
      permissionMode: 'default',
      canUseTool: async (toolName, input, options) => {
        console.error(`[test] canUseTool: ${toolName} input=${JSON.stringify(input).slice(0, 200)}`);
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
        const block = event.content_block;
        console.error(`\n[test] TOOL_USE_START: name=${block.name} input=${JSON.stringify(block.input)}`);
      }
    }
    if (msg.type === 'assistant') {
      const content = msg.message?.content;
      if (Array.isArray(content)) {
        for (const block of content) {
          if (block.type === 'tool_use') {
            console.error(`[test] TOOL_USE_COMPLETE: name=${block.name} input=${JSON.stringify(block.input).slice(0, 300)}`);
          }
          if (block.type === 'tool_result') {
            console.error(`[test] TOOL_RESULT: ${JSON.stringify(block.content).slice(0, 500)}`);
          }
        }
      }
    }
    if (msg.type === 'user') {
      // This is where tool results come back from SDK
      const content = msg.message?.content;
      if (Array.isArray(content)) {
        for (const block of content) {
          if (block.type === 'tool_result') {
            console.error(`[test] USER_TOOL_RESULT: tool_use_id=${block.tool_use_id} content=${JSON.stringify(block.content).slice(0, 500)}`);
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
  console.error(`\n[test] CAUGHT ERROR: ${err.message}`);
  console.error(`[test] Error name: ${err.name}`);
  console.error(`[test] Stack: ${err.stack?.slice(0, 1000)}`);
}

process.exit(0);
