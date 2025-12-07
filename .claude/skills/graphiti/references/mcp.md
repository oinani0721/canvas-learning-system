# Graphiti - Mcp

**Pages:** 6

---

## Autogen memory integration

**URL:** llms-txt#autogen-memory-integration

**Contents:**
- Install dependencies
- Environment setup
- Memory types
- User memory
- Knowledge graph memory
- Tools integration
  - Tool function parameters
  - User graph tools

> Add persistent memory to Microsoft Autogen agents using the zep-autogen package.

The `zep-autogen` package provides seamless integration between Zep and Microsoft Autogen agents. Choose between [user-specific conversation memory](/users) or structured [knowledge graph memory](/graph-overview) for intelligent context retrieval.

## Install dependencies

Set your API keys as environment variables:

**User Memory**: Stores conversation history in [user threads](/users) with automatic context injection\
**Knowledge Graph Memory**: Maintains structured knowledge with [custom entity models](/customizing-graph-structure)

<Steps>
  ### Step 1: Setup required imports

### Step 2: Initialize client and create user

### Step 3: Create memory with configuration

### Step 4: Create agent with memory

### Step 5: Store messages and run conversations

<Callout intent="info">
  **Automatic Context Injection**: ZepUserMemory automatically injects relevant conversation history and context via the `update_context()` method. The agent receives up to 10 recent messages plus summarized context from Zep using the specified `thread_context_mode` ("basic" or "summary").
</Callout>

## Knowledge graph memory

<Steps>
  ### Step 1: Define custom entity models

### Step 2: Setup graph with ontology

### Step 3: Initialize graph memory with filters

### Step 4: Add data and wait for indexing

### Step 5: Create agent with graph memory

Zep tools allow agents to search and add data directly to memory storage with manual control and structured responses.

<Callout intent="warning">
  **Important**: Tools must be bound to either `graph_id` OR `user_id`, not both. This determines whether they operate on knowledge graphs or user graphs.
</Callout>

### Tool function parameters

**Search Tool Parameters**:

* `query`: str (required) - Search query text
* `limit`: int (optional, default 10) - Maximum results to return
* `scope`: str (optional, default "edges") - Search scope: "edges", "nodes", "episodes"

**Add Tool Parameters**:

* `data`: str (required) - Content to store
* `data_type`: str (optional, default "text") - Data type: "text", "json", "message"

```python
from zep_autogen import create_search_graph_tool, create_add_graph_data_tool

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeBlocks>

## Environment setup

Set your API keys as environment variables:
```

Example 4 (unknown):
```unknown
## Memory types

**User Memory**: Stores conversation history in [user threads](/users) with automatic context injection\
**Knowledge Graph Memory**: Maintains structured knowledge with [custom entity models](/customizing-graph-structure)

## User memory

<Steps>
  ### Step 1: Setup required imports
```

---

## AWS Neptune Configuration

**URL:** llms-txt#aws-neptune-configuration

**Contents:**
- Prerequisites
- Setup
- Configuration
- Installation
- Connection in Python

> Configure Amazon Neptune as the graph provider for Graphiti

Neptune DB is Amazon's fully managed graph database service that supports both property graph and RDF data models. Graphiti integrates with Neptune to provide scalable, cloud-native graph storage with automatic backups, encryption, and high availability.

Neptune DB integration requires both Neptune and Amazon OpenSearch Serverless (AOSS) services:

* **Neptune Service**: For graph data storage and Cypher query processing
* **OpenSearch Serverless**: For text search and hybrid retrieval functionality
* **AWS Credentials**: Configured via AWS CLI, environment variables, or IAM roles

For detailed setup instructions, see:

* [AWS Neptune Developer Resources](https://aws.amazon.com/neptune/developer-resources/)
* [Neptune Database Documentation](https://docs.aws.amazon.com/neptune/latest/userguide/)
* [Neptune Analytics Documentation](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/)
* [OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)

1. Create a Neptune Database cluster in the AWS Console or via CloudFormation
2. Create an OpenSearch Serverless collection for text search
3. Configure VPC networking and security groups to allow communication between services
4. Note your Neptune cluster endpoint and OpenSearch collection endpoint

Set the following environment variables:

Install the required dependencies:

## Connection in Python

```python
import os
from graphiti_core import Graphiti
from graphiti_core.driver.neptune_driver import NeptuneDriver

**Examples:**

Example 1 (bash):
```bash
export NEPTUNE_HOST=your-neptune-cluster.cluster-xyz.us-west-2.neptune.amazonaws.com
export NEPTUNE_PORT=8182  # Optional, defaults to 8182
export AOSS_HOST=your-collection.us-west-2.aoss.amazonaws.com
```

Example 2 (bash):
```bash
pip install graphiti-core[neptune]
```

Example 3 (bash):
```bash
uv add graphiti-core[neptune]
```

---

## Coding with LLMs

**URL:** llms-txt#coding-with-llms

**Contents:**
- Docs MCP Server
  - Setting up the MCP server
  - Using the MCP server
- llms.txt
  - Accessing llms.txt

> Integrate Zep's documentation directly into your AI coding workflow using llms.txt and MCP.

Zep provides tools that give AI coding assistants direct access to Zep's documentation: a real-time MCP server and standardized llms.txt files for enhanced code generation and troubleshooting.

Zep's Docs MCP server gives AI assistants real-time access to search Zep's complete documentation.

* URL: `docs-mcp.getzep.com`
* Type: Search-based with HTTP transport
* Capabilities: Real-time documentation search and retrieval

<Callout intent="warning">
  The `/sse` endpoint is deprecated and will be removed soon. Please update to the new `/mcp` endpoint with HTTP transport.
</Callout>

### Setting up the MCP server

<Tabs>
  <Tab title="Claude Code">
    Add the HTTP server using the CLI:

<Tab title="Cursor">
    Create `.cursor/mcp.json` in your project or `~/.cursor/mcp.json` globally:

Enable MCP servers in Cursor settings, then add and enable the zep-docs server.
  </Tab>

<Tab title="Other MCP clients">
    Configure your MCP client with HTTP transport:

### Using the MCP server

Once configured, AI assistants can automatically:

* Search Zep concepts and features
* Find code examples and tutorials
* Access current API documentation
* Retrieve troubleshooting information

Zep publishes standardized `llms.txt` files containing essential information for AI coding assistants:

* Core concepts and architecture
* Usage patterns and examples
* API reference summaries
* Best practices and troubleshooting
* Framework integration examples

### Accessing llms.txt

Zep provides two versions of the llms.txt file:

**Standard version** (recommended for most use cases):

**Comprehensive version** (for advanced use cases):

The standard version contains curated essentials, while the comprehensive version includes complete documentation but is much larger. Most AI assistants work better with the standard version due to context limitations.

**Examples:**

Example 1 (bash):
```bash
claude mcp add zep-docs https://docs-mcp.getzep.com/mcp
```

Example 2 (json):
```json
{
      "mcpServers": {
        "zep-docs": {
          "url": "https://docs-mcp.getzep.com/mcp"
        }
      }
    }
```

Example 3 (unknown):
```unknown
URL: https://docs-mcp.getzep.com/mcp
```

Example 4 (unknown):
```unknown
https://help.getzep.com/llms.txt
```

---

## CrewAI integration

**URL:** llms-txt#crewai-integration

**Contents:**
- Core benefits
- How External Memory Works in CrewAI
  - Automatic Memory Operations
- Installation
- Storage types
  - User storage
  - Graph storage
- Tool integration
- Advanced patterns
  - Structured data with ontologies

> Add persistent memory and knowledge graphs to CrewAI agents

CrewAI agents equipped with Zep's memory platform can maintain context across conversations, access shared knowledge bases, and make more informed decisions. This integration provides persistent memory storage and intelligent knowledge retrieval for your CrewAI workflows.

* **Persistent Memory**: Conversations and knowledge persist across sessions
* **Context-Aware Agents**: Agents automatically retrieve relevant context during execution
* **Dual Storage**: User-specific memories and shared organizational knowledge
* **Intelligent Tools**: Search and data addition tools for dynamic knowledge management

## How External Memory Works in CrewAI

External memory in CrewAI operates automatically during crew execution, providing seamless context retrieval and persistence across tasks and executions.

### Automatic Memory Operations

| Operation        | When It Happens            | What Gets Stored/Retrieved                                       |
| ---------------- | -------------------------- | ---------------------------------------------------------------- |
| Memory Retrieval | At the start of each task  | Relevant context based on task description + accumulated context |
| Memory Storage   | After each task completion | Task output text + metadata (task description, messages)         |

* **Automatic Retrieval**: When an agent starts a task, CrewAI automatically queries external memory using the query "\{task.description} \{context}" to find relevant historical context
* **Automatic Storage**: When an agent completes a task, CrewAI automatically saves the task output to external memory (if external memory is configured)
* **Cross-Execution Persistence**: External memory persists between crew runs, enabling agents to learn from previous executions
* **Manual Operations**: Developers can also manually add data to external memory or query it directly using the storage interface

This automatic behavior means that once you configure Zep as your external memory provider, your CrewAI agents will seamlessly build context from past interactions and contribute new learnings without additional code.

<Callout intent="info">
  Requires Python 3.10+, Zep CrewAI >=1.1.1, CrewAI >=0.186.0, and a Zep Cloud API key. Get your API key from [app.getzep.com](https://app.getzep.com).
</Callout>

Set up your environment variables:

Use `ZepUserStorage` for personal context and conversation history:

<CodeBlocks>

</CodeBlocks>

User storage automatically routes data:

* **Messages** (`type: "message"`) → Thread API for conversation context
* **JSON/Text** (`type: "json"` or `type: "text"`) → User Graph for preferences

Use `ZepGraphStorage` for organizational knowledge that multiple agents can access:

<CodeBlocks>

</CodeBlocks>

Equip your agents with Zep tools for dynamic knowledge management:

<CodeBlocks>

</CodeBlocks>

* `query`: Natural language search query
* `limit`: Maximum results (default: 10)
* `scope`: Search scope - "edges", "nodes", "episodes", or "all"

* `data`: Content to store (text, JSON, or message)
* `data_type`: Explicit type - "text", "json", or "message"

### Structured data with ontologies

Define entity models for better knowledge organization:

<CodeBlocks>

</CodeBlocks>

### Multi-agent with mixed storage

Combine user and graph storage for comprehensive memory:

<CodeBlocks>

</CodeBlocks>

### Research and curation workflow

Agents can search existing knowledge and add new discoveries:

<CodeBlocks>

</CodeBlocks>

## Configuration options

### ZepUserStorage parameters

* `client`: Zep client instance (required)
* `user_id`: User identifier (required)
* `thread_id`: Thread identifier (optional, enables conversation context)
* `mode`: Context mode - "summary" or "basic" (default: "summary")
* `search_filters`: Filter search results by node labels or attributes
* `facts_limit`: Maximum facts for context (default: 20)
* `entity_limit`: Maximum entities for context (default: 5)

### ZepGraphStorage parameters

* `client`: Zep client instance (required)
* `graph_id`: Graph identifier (required)
* `search_filters`: Filter by node labels (e.g., `{"node_labels": ["Technology"]}`)
* `facts_limit`: Maximum facts for context (default: 20)
* `entity_limit`: Maximum entities for context (default: 5)

The integration automatically routes different data types to appropriate storage:

<CodeBlocks>

</CodeBlocks>

Here's a complete example showing personal assistance with conversation memory:

<CodeBlocks>

</CodeBlocks>

### Storage selection

* **Use ZepUserStorage** for personal preferences, conversation history, and user-specific context
* **Use ZepGraphStorage** for shared knowledge, organizational data, and collaborative information

### Memory management

* **Set up ontologies** for structured data organization
* **Use search filters** to target specific node types and improve relevance
* **Combine storage types** for comprehensive memory coverage

* **Bind tools** to specific users or graphs at creation time
* **Use search scope "all"** sparingly as it's more expensive
* **Add data with appropriate types** (message, json, text) for correct routing
* **Limit search results** appropriately to avoid context bloat

* Explore [customizing graph structure](/customizing-graph-structure) for advanced knowledge organization
* Learn about [searching the graph](/searching-the-graph) and how to search the graph
* See [code examples](https://github.com/getzep/zep/tree/main/integrations/python/zep_crewai/examples) for additional patterns

**Examples:**

Example 1 (bash):
```bash
pip install zep-crewai
```

Example 2 (bash):
```bash
export ZEP_API_KEY="your-zep-api-key"
```

Example 3 (unknown):
```unknown
</CodeBlocks>

User storage automatically routes data:

* **Messages** (`type: "message"`) → Thread API for conversation context
* **JSON/Text** (`type: "json"` or `type: "text"`) → User Graph for preferences

### Graph storage

Use `ZepGraphStorage` for organizational knowledge that multiple agents can access:

<CodeBlocks>
```

Example 4 (unknown):
```unknown
</CodeBlocks>

## Tool integration

Equip your agents with Zep tools for dynamic knowledge management:

<CodeBlocks>
```

---

## Knowledge Graph MCP Server

**URL:** llms-txt#knowledge-graph-mcp-server

**Contents:**
- Key Features
- Quick Start with OpenAI
  - Prerequisites
  - Installation
  - Configuration

> A Knowledge Graph MCP Server for AI Assistants

<Card title="What is the Graphiti MCP Server?" icon="duotone server">
  The Graphiti MCP Server is an experimental implementation that exposes Graphiti's key functionality through the Model Context Protocol (MCP). This enables AI assistants like Claude Desktop and Cursor to interact with Graphiti's knowledge graph capabilities, providing persistent memory and contextual awareness.
</Card>

The Graphiti MCP Server bridges AI assistants with Graphiti's temporally-aware knowledge graphs, allowing assistants to maintain persistent memory across conversations and sessions. By integrating through MCP, assistants can automatically store, retrieve, and reason with information from their interactions.

The MCP server exposes Graphiti's core capabilities:

* **Episode Management**: Add, retrieve, and delete episodes (text, messages, or JSON data)
* **Entity Management**: Search and manage entity nodes and relationships
* **Search Capabilities**: Semantic and hybrid search for facts and node summaries
* **Group Management**: Organize data with group\_id filtering for multi-user scenarios
* **Graph Maintenance**: Clear graphs and rebuild indices as needed

## Quick Start with OpenAI

<Note>
  This quick start assumes you have OpenAI API access. For other LLM providers and detailed configuration options, see the [MCP Server README](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md).
</Note>

Before getting started, ensure you have:

1. **Python 3.10+** installed on your system
2. **Neo4j database** (version 5.26 or later) running locally or accessible remotely
3. **OpenAI API key** for LLM operations and embeddings

1. Clone the Graphiti repository:

2. Navigate to the MCP server directory and install dependencies:

Set up your environment variables in a `.env` file:

**Examples:**

Example 1 (bash):
```bash
git clone https://github.com/getzep/graphiti.git
cd graphiti
```

Example 2 (bash):
```bash
cd mcp_server
uv sync
```

---

## Neo4j Configuration (adjust as needed)

**URL:** llms-txt#neo4j-configuration-(adjust-as-needed)

**Contents:**
  - Running the Server
- MCP Client Integration
  - Claude Desktop
  - Cursor IDE
- Available Tools
- Docker Deployment
- Next Steps

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
bash
uv run graphiti_mcp_server.py
bash
uv run graphiti_mcp_server.py --model gpt-4o-mini --transport sse --group-id my-project
json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "stdio",
      "command": "/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/path/to/graphiti/mcp_server",
        "graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "your_api_key",
        "MODEL_NAME": "gpt-4o-mini",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/sse"
    }
  }
}
bash
docker compose up
```

This starts both Neo4j and the MCP server with SSE transport enabled.

For comprehensive configuration options, advanced features, and troubleshooting:

* **Full Documentation**: See the complete [MCP Server README](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md)
* **Integration Examples**: Explore client-specific setup guides for Claude Desktop and Cursor
* **Custom Entity Types**: Configure domain-specific entity extraction
* **Multi-tenant Setup**: Use group IDs for organizing data across different contexts

<Warning>
  The MCP server is experimental and under active development. Features and APIs may change between releases.
</Warning>

**Examples:**

Example 1 (unknown):
```unknown
### Running the Server

Start the MCP server:
```

Example 2 (unknown):
```unknown
For development with custom options:
```

Example 3 (unknown):
```unknown
## MCP Client Integration

### Claude Desktop

Configure Claude Desktop to connect via the stdio transport:
```

Example 4 (unknown):
```unknown
### Cursor IDE

For Cursor, use the SSE transport configuration:
```

---
