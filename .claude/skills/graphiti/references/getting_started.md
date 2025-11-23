# Graphiti - Getting Started

**Pages:** 5

---

## Graph Overview

**URL:** llms-txt#graph-overview

**Contents:**
- Graph Data Structure
- Creating a Graph
- Working with the Graph

Zep's temporal knowledge graph powers its context engineering capabilities, including agent memory and Graph RAG. Zep's graph is built on [Graphiti](/graphiti/graphiti/overview), Zep's open-source temporal graph library, which is fully integrated into Zep. Developers do not need to interact directly with Graphiti or understand its underlying implementation.

<Card title="What is a Knowledge Graph?" icon="duotone chart-network">
  A knowledge graph is a network of interconnected facts, such as *"Kendra loves
  Adidas shoes."* Each fact is a *"triplet"* represented by two entities, or
  nodes (*"Kendra", "Adidas shoes"*), and their relationship, or edge
  (*"loves"*).

Knowledge Graphs have been explored extensively for information retrieval.
  What makes Zep unique is its ability to autonomously build temporal knowledge graphs
  while handling changing relationships and maintaining historical context.
</Card>

Zep automatically constructs a temporal knowledge graph for each of your users. The knowledge graph contains entities, relationships, and facts related to your user, while automatically handling changing relationships and facts over time.

Here's an example of how Zep might extract graph data from a chat message, and then update the graph once new information is available:

![graphiti intro slides](file:944922c0-87b1-4b85-8622-6254308407e5)

Each node and edge contains certain attributes - notably, a fact is always stored as an edge attribute. There are also datetime attributes for when the fact becomes valid and when it becomes invalid.

## Graph Data Structure

Zep's graph database stores data in three main types:

1. Entity edges (edges): Represent relationships between nodes and include semantic facts representing the relationship between the edge's nodes.
2. Entity nodes (nodes): Represent entities extracted from episodes, containing summaries of relevant information.
3. Episodic nodes (episodes): Represent raw data stored in Zep, either through chat history or the `graph.add` endpoint.

Before you can work with graph data, you need to create a graph. Each graph is identified by a unique `graph_id` and can optionally include a name and description:

## Working with the Graph

To learn more about interacting with Zep's graph, refer to the following sections:

* [Adding Data to the Graph](/v3/adding-data-to-the-graph): Learn how to add new data to the graph.
* [Reading Data from the Graph](/v3/reading-data-from-the-graph): Discover how to retrieve information from the graph.
* [Searching the Graph](/v3/searching-the-graph): Explore techniques for efficiently searching the graph.

These guides will help you leverage the full power of Zep's knowledge graph in your applications.

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown

```

---

## Install Ollama (visit https://ollama.ai for installation instructions)

**URL:** llms-txt#install-ollama-(visit-https://ollama.ai-for-installation-instructions)

---

## Overview

**URL:** llms-txt#overview

**Contents:**
- Graphiti and Zep Memory
- Why Graphiti?

> Temporal Knowledge Graphs for Agentic Applications

<Card title="What is a Knowledge Graph?" icon="duotone chart-network">
  Graphiti helps you create and query Knowledge Graphs that evolve over time. A
  knowledge graph is a network of interconnected facts, such as *“Kendra loves
  Adidas shoes.”* Each fact is a *“triplet”* represented by two entities, or
  nodes (*”Kendra”, “Adidas shoes”*), and their relationship, or edge
  (*”loves”*).

Knowledge Graphs have been explored extensively for information retrieval.
  What makes Graphiti unique is its ability to autonomously build a knowledge
  graph while handling changing relationships and maintaining historical
  context.
</Card>

![graphiti intro slides](file:944922c0-87b1-4b85-8622-6254308407e5)

Graphiti builds dynamic, temporally-aware knowledge graphs that represent complex, evolving relationships between entities over time. It ingests both unstructured and structured data, and the resulting graph may be queried using a fusion of time, full-text, semantic, and graph algorithm approaches.

With Graphiti, you can build LLM applications such as:

* Assistants that learn from user interactions, fusing personal knowledge with dynamic data from business systems like CRMs and billing platforms.
* Agents that autonomously execute complex tasks, reasoning with state changes from multiple dynamic sources.

Graphiti supports a wide range of applications in sales, customer service, health, finance, and more, enabling long-term recall and state-based reasoning for both assistants and agents.

## Graphiti and Zep Memory

Graphiti powers the core of [Zep's memory layer](https://www.getzep.com) for LLM-powered Assistants and Agents.

We're excited to open-source Graphiti, believing its potential reaches far beyond memory applications.

We were intrigued by Microsoft’s GraphRAG, which expanded on RAG text chunking by using a graph to better model a document corpus and making this representation available via semantic and graph search techniques. However, GraphRAG did not address our core problem: It's primarily designed for static documents and doesn't inherently handle temporal aspects of data.

Graphiti is designed from the ground up to handle constantly changing information, hybrid semantic and graph search, and scale:

* **Temporal Awareness:** Tracks changes in facts and relationships over time, enabling point-in-time queries. Graph edges include temporal metadata to record relationship lifecycles.
* **Episodic Processing:** Ingests data as discrete episodes, maintaining data provenance and allowing incremental entity and relationship extraction.
* **Custom Entity Types:** Supports defining domain-specific entity types, enabling more precise knowledge representation for specialized applications.
* **Hybrid Search:** Combines semantic and BM25 full-text search, with the ability to rerank results by distance from a central node e.g. "Kendra".
* **Scalable:** Designed for processing large datasets, with parallelization of LLM calls for bulk processing while preserving the chronology of events.
* **Supports Varied Sources:** Can ingest both unstructured text and structured JSON data.

| Aspect                     | GraphRAG                              | Graphiti                                         |
| -------------------------- | ------------------------------------- | ------------------------------------------------ |
| **Primary Use**            | Static document summarization         | Dynamic data management                          |
| **Data Handling**          | Batch-oriented processing             | Continuous, incremental updates                  |
| **Knowledge Structure**    | Entity clusters & community summaries | Episodic data, semantic entities, communities    |
| **Retrieval Method**       | Sequential LLM summarization          | Hybrid semantic, keyword, and graph-based search |
| **Adaptability**           | Low                                   | High                                             |
| **Temporal Handling**      | Basic timestamp tracking              | Explicit bi-temporal tracking                    |
| **Contradiction Handling** | LLM-driven summarization judgments    | Temporal edge invalidation                       |
| **Query Latency**          | Seconds to tens of seconds            | Typically sub-second latency                     |
| **Custom Entity Types**    | No                                    | Yes, customizable                                |
| **Scalability**            | Moderate                              | High, optimized for large datasets               |

Graphiti is specifically designed to address the challenges of dynamic and frequently updated datasets, making it particularly suitable for applications requiring real-time interaction and precise historical queries.

![graphiti demo slides](file:41430d15-808c-494c-be27-800489d33953)

---

## Welcome to Graphiti!

**URL:** llms-txt#welcome-to-graphiti!

<Tip>
  Want to use Graphiti with AI assistants like Claude Desktop or Cursor? Check out the [Knowledge Graph MCP Server](/graphiti/getting-started/mcp-server).
</Tip>

Graphiti is a Python framework for building temporally-aware knowledge graphs designed for AI agents. It enables real-time incremental updates to knowledge graphs without batch recomputation, making it suitable for dynamic environments where relationships and information evolve over time.

<CardGroup cols={3}>
  <Card title="Overview" icon="chart-network" href="/graphiti/getting-started/overview">
    Learn about Graphiti's core concepts and how temporal knowledge graphs work.
  </Card>

<Card title="Quick Start" icon="rocket" href="/graphiti/getting-started/quick-start">
    Get up and running with Graphiti in minutes including installation, episodes, search, and basic operations.
  </Card>

<Card title="Knowledge Graph MCP Server" icon="server" href="/graphiti/getting-started/mcp-server">
    Use Graphiti with AI assistants like Claude Desktop or Cursor.
  </Card>

<Card title="Adding Episodes" icon="file-plus" href="/graphiti/core-concepts/adding-episodes">
    Learn how to add text and JSON episodes to build your knowledge graph.
  </Card>

<Card title="Searching" icon="magnifying-glass" href="/graphiti/working-with-data/searching">
    Discover hybrid search capabilities combining semantic, keyword, and graph-based retrieval.
  </Card>

<Card title="Custom Entities" icon="shapes" href="/graphiti/core-concepts/custom-entity-and-edge-types">
    Define domain-specific entity types for more precise knowledge representation.
  </Card>
</CardGroup>

---

## Welcome to Zep!

**URL:** llms-txt#welcome-to-zep!

<Tip>
  Connect your <strong>AI coding assistant</strong> to Zep's docs: [MCP server & llms.txt](/coding-with-llms)
</Tip>

Zep is a context engineering platform that systematically assembles personalized context—user preferences, traits, and business data—for reliable agent applications. Zep combines agent memory, Graph RAG, and context assembly capabilities to deliver comprehensive personalized context that reduces hallucinations and improves accuracy.

<CardGroup cols={3}>
  <Card title="Key Concepts" icon="brain" href="/concepts">
    Learn about Zep's context engineering platform, temporal knowledge graphs, and agent memory capabilities.
  </Card>

<Card title="Quickstart" icon="rocket" href="/quickstart">
    Get up and running with Zep in minutes, whether you code in Python, TypeScript, or Go.
  </Card>

<Card title="Cookbooks" icon="book-open" href="/cookbook/customize-your-context-block">
    Discover practical recipes and patterns for common use cases with Zep.
  </Card>

<Card title="SDK Reference" icon="code" href="/sdk-reference">
    Comprehensive API documentation for Zep's SDKs in Python, TypeScript, and Go.
  </Card>

<Card title="Mem0 Migration" icon="fa-solid fa-arrows-rotate" href="/mem0-to-zep">
    Migrate from Mem0 to Zep in minutes.
  </Card>

<Card title="Graphiti" icon="fa-solid fa-chart-network" href="/graphiti/graphiti">
    Learn about Graphiti, Zep's open-source temporal knowledge graph framework.
  </Card>
</CardGroup>

---
