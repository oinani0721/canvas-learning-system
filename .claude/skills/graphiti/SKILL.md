---
name: graphiti
description: Graphiti temporal knowledge graph framework. Use for building time-aware knowledge graphs for AI agents, managing episodes and entities, performing hybrid semantic search, and integrating with MCP servers.
---

# Graphiti Skill

Comprehensive assistance with Graphiti development - the temporal knowledge graph framework for AI agents.

## When to Use This Skill

This skill should be triggered when:
- Building AI agents that need persistent memory across conversations
- Implementing Graph RAG (Retrieval-Augmented Generation) with temporal awareness
- Managing dynamic knowledge that changes over time (facts, relationships, entities)
- Setting up knowledge graphs for LLM applications
- Handling contradictory or evolving information with temporal tracking
- Integrating with Zep Cloud memory platform
- Configuring MCP servers for Claude Desktop or Cursor
- Working with episodic data from conversations, business systems, or documents
- Implementing hybrid search (semantic + keyword + graph traversal)
- Creating custom entity types for domain-specific knowledge representation

## Quick Reference

### Installation and Setup

**Installing Graphiti Core:**
```python
# Basic installation
pip install graphiti-core

# With Neo4j support (recommended)
pip install graphiti-core[neo4j]

# With AWS Neptune support
pip install graphiti-core[neptune]
```

**Basic Initialization with Neo4j:**
```python
from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver

# Initialize Neo4j driver
driver = Neo4jDriver(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_password"
)

# Create Graphiti instance
graphiti = Graphiti(driver)
```

### Adding Episodes (Core Operation)

**Adding Text Episodes:**
```python
from datetime import datetime

# Add a text episode
await graphiti.add_episode(
    name="user_conversation",
    episode_body="Kendra mentioned she loves Adidas shoes and runs marathons.",
    source_description="Chat conversation",
    reference_time=datetime.now()
)

# Graphiti automatically extracts:
# - Entities: "Kendra", "Adidas shoes", "marathons"
# - Relationships: "Kendra loves Adidas shoes", "Kendra runs marathons"
# - Temporal metadata: when facts became valid
```

**Adding JSON Episodes:**
```python
import json

# Add structured business data
customer_data = {
    "customer_id": "12345",
    "name": "Kendra Smith",
    "preferences": {
        "shoe_brand": "Adidas",
        "activity": "running"
    },
    "last_purchase": "2025-01-15"
}

await graphiti.add_episode(
    name="customer_profile",
    episode_body=json.dumps(customer_data),
    source_description="CRM system",
    reference_time=datetime.now(),
    episode_type="json"  # Specify JSON type
)
```

**Batch Processing Episodes:**
```python
# Add multiple episodes efficiently
episodes = [
    {
        "name": "interaction_1",
        "episode_body": "User asked about product features",
        "reference_time": datetime(2025, 1, 10)
    },
    {
        "name": "interaction_2",
        "episode_body": "User completed purchase of running shoes",
        "reference_time": datetime(2025, 1, 15)
    }
]

# Batch process (preserves chronological order)
for episode_data in episodes:
    await graphiti.add_episode(**episode_data)
```

### Searching the Graph

**Semantic Search:**
```python
# Search for relevant facts and entities
results = await graphiti.search(
    query="What are Kendra's preferences?",
    num_results=10,
    center_node_uuid=None  # Optional: search from specific node
)

# Results contain:
# - facts (edges with relationships)
# - entities (nodes)
# - episodes (original data sources)
# - scores (relevance rankings)

for edge in results.edges:
    print(f"Fact: {edge.fact}")
    print(f"Valid from: {edge.valid_at}")
    print(f"Invalid at: {edge.invalid_at if edge.invalid_at else 'Still valid'}")
```

**Hybrid Search (Semantic + BM25 + Graph):**
```python
# Combine semantic, keyword, and graph traversal
results = await graphiti.search(
    query="running shoes purchases",
    num_results=20,
    center_node_uuid="kendra_node_uuid",  # Search from Kendra's perspective
    max_distance=2  # Maximum graph hops from center node
)

# Hybrid search uses:
# 1. Semantic similarity (embeddings)
# 2. BM25 keyword matching
# 3. Graph distance from center node
```

**Point-in-Time Queries:**
```python
from datetime import datetime, timedelta

# Query what was known at a specific time
past_date = datetime.now() - timedelta(days=30)

results = await graphiti.search(
    query="What was Kendra's shoe preference?",
    reference_time=past_date  # Query historical state
)

# Returns only facts that were valid at past_date
```

### Custom Entity Types

**Defining Domain-Specific Entities:**
```python
from graphiti_core.nodes import EntityNode
from pydantic import Field

# Define custom entity types for your domain
class CustomerEntity(EntityNode):
    """Customer entity with specific attributes"""
    entity_type: str = "Customer"
    customer_id: str = Field(..., description="Unique customer ID")
    subscription_tier: str = Field(default="free")
    lifetime_value: float = Field(default=0.0)

class ProductEntity(EntityNode):
    """Product entity"""
    entity_type: str = "Product"
    product_id: str = Field(..., description="Product SKU")
    category: str
    price: float

class PurchaseEdge(EntityEdge):
    """Purchase relationship"""
    relationship_type: str = "PURCHASED"
    purchase_date: datetime
    quantity: int
    total_amount: float

# Register custom types
graphiti.register_entity_types([CustomerEntity, ProductEntity])
graphiti.register_edge_types([PurchaseEdge])
```

**Using Custom Entities:**
```python
# Add episode with custom entity extraction
await graphiti.add_episode(
    name="purchase_event",
    episode_body="Customer C12345 purchased Product SKU-9876 on 2025-01-15 for $129.99",
    entity_types=[CustomerEntity, ProductEntity],
    edge_types=[PurchaseEdge]
)

# Graphiti extracts entities with custom attributes
# and creates typed relationships
```

### Temporal Fact Management

**How Graphiti Handles Changing Facts:**
```python
# Day 1: Add initial fact
await graphiti.add_episode(
    name="preference_v1",
    episode_body="Kendra loves Nike shoes",
    reference_time=datetime(2025, 1, 1)
)
# Creates edge: Kendra --[loves]--> Nike shoes
# valid_at: 2025-01-01, invalid_at: None

# Day 15: New contradictory information
await graphiti.add_episode(
    name="preference_v2",
    episode_body="Kendra now prefers Adidas shoes instead",
    reference_time=datetime(2025, 1, 15)
)
# Graphiti automatically:
# 1. Sets invalid_at=2025-01-15 on the Nike edge
# 2. Creates new edge: Kendra --[loves]--> Adidas shoes
#    valid_at: 2025-01-15, invalid_at: None

# Query current state (shows only valid facts)
current = await graphiti.search("Kendra shoe preference")
# Returns: "Kendra loves Adidas shoes" (valid)

# Query historical state
historical = await graphiti.search(
    "Kendra shoe preference",
    reference_time=datetime(2025, 1, 10)
)
# Returns: "Kendra loves Nike shoes" (was valid then)
```

### MCP Server Integration

**Setting Up for Claude Desktop:**
```bash
# Install Zep MCP server
claude mcp add zep-docs https://docs-mcp.getzep.com/mcp

# Or manual configuration in Claude config
```

**Claude Desktop Config (.claude.json):**
```json
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
```

**Cursor IDE Configuration (.cursor/mcp.json):**
```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Zep Cloud Integration

**Using Zep's Hosted Graphiti:**
```python
from zep_cloud import Zep

# Initialize Zep client
client = Zep(api_key="YOUR_ZEP_API_KEY")

# Add data to graph
client.graph.add(
    user_id="user_123",  # Or graph_id for non-user graphs
    data="User mentioned interest in cloud architecture and Kubernetes",
    type="text"
)

# Add JSON business data
client.graph.add(
    user_id="user_123",
    data='{"event": "purchase", "item": "Pro subscription", "amount": 99}',
    type="json"
)

# Search the graph
results = client.graph.search(
    user_id="user_123",
    query="What are the user's technical interests?",
    limit=10
)

# Get user context for conversations
from zep_cloud.types import Message

# Add conversation message
client.thread.add_messages(
    thread_id="thread_456",
    messages=[
        Message(
            role="user",
            content="I'm interested in learning Kubernetes"
        )
    ]
)

# Retrieve context for next response
context = client.thread.get_user_context(thread_id="thread_456")
print(context.memory.context)  # Relevant facts + entities
```

### CrewAI Integration

**User Memory for Personal Context:**
```python
from zep_crewai import ZepUserStorage
from crewai import Agent, Task, Crew

# Setup Zep storage
storage = ZepUserStorage(
    client=zep_client,
    user_id="user_123",
    thread_id="conversation_1",
    mode="summary"  # or "basic" for faster retrieval
)

# Create agent with memory
agent = Agent(
    role="Personal Assistant",
    goal="Help user with personalized recommendations",
    backstory="AI assistant with memory of past interactions",
    verbose=True
)

# Create crew with external memory
crew = Crew(
    agents=[agent],
    tasks=[task],
    external_memory=storage  # Automatic context retrieval
)

# Run crew - memory handled automatically
result = crew.kickoff()
```

**Graph Memory for Shared Knowledge:**
```python
from zep_crewai import ZepGraphStorage

# Shared organizational knowledge
storage = ZepGraphStorage(
    client=zep_client,
    graph_id="company_knowledge",
    search_filters={"node_labels": ["Technology", "Process"]}
)

# Multiple agents share this knowledge base
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=tasks,
    external_memory=storage
)
```

## Key Concepts

### 1. Temporal Knowledge Graphs

Graphiti's core innovation is **bi-temporal tracking** - every fact has both:
- **Valid time**: When the fact was true in the real world
- **Transaction time**: When the fact was recorded in the system

This enables:
- Point-in-time queries ("What did we know about X on date Y?")
- Fact invalidation when new information supersedes old
- Historical reasoning and audit trails
- Handling contradictory information gracefully

**Example:**
```
Edge: "Kendra loves Nike shoes"
- valid_at: 2025-01-01
- invalid_at: 2025-01-15  (superseded by new preference)
- created_at: 2025-01-01  (transaction time)
```

### 2. Episodic Processing

**Episodes** are discrete units of data ingestion:
- Can be text (unstructured), JSON (structured), or messages (conversations)
- Maintain data provenance (where information came from)
- Allow incremental updates without full graph recomputation
- Preserve chronological order for temporal consistency

**Benefits:**
- Incremental knowledge building (no batch reprocessing)
- Clear audit trail (trace facts back to source episodes)
- Efficient updates (only process new data)

### 3. Hybrid Search

Graphiti combines three retrieval methods:

1. **Semantic Search**: Vector similarity using embeddings
2. **BM25 Full-Text**: Keyword matching for exact terms
3. **Graph Traversal**: Relationship-based search from a center node

**Reranking strategies:**
- `rrf`: Reciprocal Rank Fusion (balanced)
- `mmr`: Maximal Marginal Relevance (diversity)
- `node_distance`: Proximity to center node
- `cross_encoder`: Deep semantic reranking
- `episode_mentions`: Frequency in source data

### 4. Entity-Centric Design

Knowledge is organized around **entities** (nodes) and **relationships** (edges):

**9 Built-in Entity Types:**
1. Person
2. Organization
3. Location
4. Event
5. Concept
6. Object
7. Date
8. Quantity
9. Unknown (fallback)

**Custom Entity Types:**
- Define domain-specific entities with Pydantic-like classes
- Specify required attributes and validation rules
- Guide LLM extraction with structured schemas

### 5. Context Engineering

Graphiti is designed for **systematic context assembly**:

1. **Ingest diverse data**: Conversations, business systems, documents
2. **Automatic entity linking**: Deduplicate and merge related entities
3. **Fact extraction**: LLM-powered relationship identification
4. **Temporal tracking**: Maintain fact lifecycles
5. **Context block generation**: Prompt-ready summaries with relevant facts

**Context Block Example:**
```
Relevant Facts about Kendra:
- Kendra loves Adidas shoes (valid: 2025-01-15 - present)
- Kendra runs marathons (valid: 2025-01-10 - present)
- Kendra purchased Pro subscription (valid: 2025-01-20 - present)

Key Entities:
- Kendra (Person): Marathon runner, Adidas enthusiast, Pro subscriber
- Adidas (Organization): Shoe brand preferred by Kendra
```

## Reference Files

This skill includes comprehensive documentation in `references/`:

- **getting_started.md** (12K, 5 pages) - Installation, core concepts, quick start
- **concepts.md** (22K, 2 pages) - Context engineering, graph structure, temporal facts
- **api.md** (154K, 49 pages) - Complete API reference with Python/TypeScript/Go examples
- **mcp.md** (19K, 6 pages) - MCP server setup, CrewAI/Autogen integrations
- **guides.md** - Detailed how-to guides and tutorials
- **llms-full.md** (776K) - Complete documentation dump for deep dives

Use the Read tool to access specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
1. Start with **getting_started.md** - understand episodes, entities, and basic operations
2. Review **Quick Reference > Installation and Setup** - get Graphiti running locally
3. Try **Quick Reference > Adding Episodes** - learn the core ingestion workflow
4. Experiment with **Quick Reference > Searching** - see how retrieval works

### For Intermediate Users
1. Explore **Key Concepts > Temporal Knowledge Graphs** - understand bi-temporal tracking
2. Study **Quick Reference > Custom Entity Types** - define domain-specific entities
3. Read **concepts.md** for context engineering patterns
4. Implement hybrid search with different reranking strategies

### For Advanced Users
1. Dive into **api.md** for complete API coverage (49 pages)
2. Design custom ontologies with entity/edge type hierarchies
3. Optimize search with filters, rerankers, and graph traversal parameters
4. Set up MCP servers for AI assistant integration
5. Implement multi-tenant systems with group IDs

### Integration Paths
- **Zep Cloud**: Use hosted Graphiti, no infrastructure needed
- **Self-hosted Neo4j**: Full control, use graphiti-core library
- **AWS Neptune**: Enterprise-scale deployment with OpenSearch
- **CrewAI/Autogen**: Agent framework integrations
- **MCP Servers**: Claude Desktop, Cursor IDE integrations

## Common Use Cases

### 1. AI Agent Memory

```python
# Agent that remembers user interactions
async def conversational_agent(user_message: str):
    # Add new interaction to graph
    await graphiti.add_episode(
        name=f"conversation_{datetime.now().isoformat()}",
        episode_body=f"User said: {user_message}",
        reference_time=datetime.now()
    )

    # Retrieve relevant context
    context = await graphiti.search(
        query=user_message,
        num_results=10
    )

    # Build prompt with context
    prompt = f"""
    Relevant facts from past conversations:
    {format_search_results(context)}

    User's current message: {user_message}
    """

    return generate_response(prompt)
```

### 2. Dynamic Graph RAG

```python
# Keep knowledge base up-to-date with changing docs
async def update_documentation_graph(doc_sections: list):
    for section in doc_sections:
        await graphiti.add_episode(
            name=f"docs_{section['id']}",
            episode_body=section['content'],
            source_description=f"Documentation v{section['version']}",
            reference_time=section['published_at']
        )

    # Old facts automatically invalidated by new versions
    # Query always returns current valid information

async def answer_with_current_docs(question: str):
    # Search gets latest valid facts
    results = await graphiti.search(query=question)
    return generate_answer(question, results)
```

### 3. Customer 360 View

```python
# Unified customer profile from multiple sources
async def build_customer_profile(customer_id: str):
    # CRM data
    await graphiti.add_episode(
        name=f"crm_{customer_id}",
        episode_body=json.dumps(crm_data),
        episode_type="json",
        reference_time=datetime.now()
    )

    # Support tickets
    for ticket in support_tickets:
        await graphiti.add_episode(
            name=f"ticket_{ticket.id}",
            episode_body=ticket.description,
            reference_time=ticket.created_at
        )

    # Purchase history
    for purchase in purchases:
        await graphiti.add_episode(
            name=f"purchase_{purchase.id}",
            episode_body=json.dumps(purchase),
            episode_type="json",
            reference_time=purchase.date
        )

    # Get unified view
    profile = await graphiti.search(
        query=f"customer {customer_id} profile preferences issues",
        num_results=50
    )

    return profile  # Fused view from all sources
```

## Best Practices

### 1. Episode Design
- Keep episodes focused (one event, one topic)
- Include rich source descriptions for provenance
- Use appropriate episode types (text/json/message)
- Maintain chronological order for temporal consistency

### 2. Search Optimization
- Start with center_node_uuid for user-specific searches
- Use search filters to narrow results by entity type
- Experiment with rerankers based on use case:
  - `rrf` for balanced results (default)
  - `mmr` for diverse information
  - `node_distance` for relationship-focused queries
- Limit results appropriately (10-20 for prompts, 50+ for analysis)

### 3. Custom Entity Types
- Define types that match your domain language
- Use clear descriptions for LLM extraction guidance
- Add validation rules to ensure data quality
- Register types before processing episodes

### 4. Temporal Queries
- Use reference_time for historical analysis
- Don't manually update facts - add new episodes to supersede
- Query both current and historical states for comprehensive views
- Leverage fact lifecycles (valid_at, invalid_at) for audit trails

### 5. Performance
- Use batch operations for bulk imports
- Index entities and episodes for faster retrieval
- Monitor Neo4j/Neptune performance metrics
- Consider caching frequently accessed context blocks

## Troubleshooting

### Entities Not Linking
**Problem**: Related entities created as duplicates instead of linked

**Solution**:
- Ensure consistent entity names across episodes
- Use entity summaries to help LLM identify matches
- Consider manual entity merging for critical entities

### Slow Search
**Problem**: Graph searches taking too long

**Solution**:
- Add indexes on frequently queried properties
- Use tighter search filters (entity types, date ranges)
- Reduce num_results for initial queries
- Consider center_node_uuid to limit search space

### Facts Not Invalidating
**Problem**: Contradictory facts both showing as valid

**Solution**:
- Check reference_time ordering (must be chronological)
- Verify LLM is detecting contradictions
- Use explicit fact types to guide invalidation logic
- Review episode source_description for clarity

## Resources

### Official Documentation
- Main docs: https://help.getzep.com/graphiti/
- GitHub: https://github.com/getzep/graphiti
- Zep Cloud: https://www.getzep.com
- MCP Server README: https://github.com/getzep/graphiti/blob/main/mcp_server/README.md

### Integration Guides
- CrewAI examples: https://github.com/getzep/zep/tree/main/integrations/python/zep_crewai/examples
- Autogen integration: https://help.getzep.com/autogen-memory-integration
- MCP clients: Claude Desktop, Cursor IDE

### Community
- Discord: Zep community server
- Issues: GitHub issues for bug reports and feature requests

## Notes

- Graphiti is under active development - APIs may evolve
- MCP server is experimental (features subject to change)
- Requires Python 3.10+ for full feature support
- Neo4j 5.26+ recommended for self-hosted deployments
- Zep Cloud provides hosted Graphiti (no infrastructure needed)
