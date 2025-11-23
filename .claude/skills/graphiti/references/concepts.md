# Graphiti - Concepts

**Pages:** 2

---

## Key Concepts

**URL:** llms-txt#key-concepts

**Contents:**
- Concepts Table
- Use Cases Table
- What is Context Engineering?
- How Zep Fits Into Your Application
  - Context Block

> Understanding Zep's context engineering platform and temporal knowledge graphs.

<Tip>
  Looking to just get coding? Check out our [Quickstart](/quickstart).
</Tip>

Zep is a context engineering platform that systematically assembles personalized context—user preferences, traits, and business data—for reliable agent applications. Zep combines Graph RAG, agent memory, and context assembly capabilities to deliver comprehensive personalized context that reduces hallucinations and improves accuracy.

| Concept                                    | Description                                                                                                                                                                                                     | Docs                                                              |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Knowledge Graph                            | Zep's unified knowledge store for agents. Nodes represent entities, edges represent facts/relationships. The graph updates dynamically in response to new data.                                                 | [Docs](/understanding-the-graph)                                  |
| Zep's Context Block                        | Optimized string containing facts and entities from the knowledge graph most relevant to the current thread. Also contains dates when facts became valid and invalid. Provide this to your chatbot as "memory". | [Docs](/retrieving-memory#retrieving-zeps-context-block)          |
| Fact Invalidation                          | When new data invalidates a prior fact, the time the fact became invalid is stored on that fact's edge in the knowledge graph.                                                                                  | [Docs](/facts)                                                    |
| JSON/text/message                          | Types of data that can be ingested into the knowledge graph. Can represent business data, documents, chat messages, emails, etc.                                                                                | [Docs](/adding-data-to-the-graph)                                 |
| Custom Entity/Edge Types                   | Feature allowing use of Pydantic-like classes to customize creation/retrieval of entities and relations in the knowledge graph.                                                                                 | [Docs](/customizing-graph-structure#custom-entity-and-edge-types) |
| Graph                                      | Represents an arbitrary knowledge graph for storing up-to-date knowledge about an object or system. For storing up-to-date knowledge about a user, a user graph should be used.                                 | [Docs](/graph-overview)                                           |
| User Graph                                 | Special type of graph for storing personalized memory for a user of your application.                                                                                                                           | [Docs](/users)                                                    |
| User                                       | A user in Zep represents a user of your application, and has its own User Graph and thread history.                                                                                                             | [Docs](/users)                                                    |
| Threads                                    | Conversation threads of a user. By default, all messages added to any thread of that user are ingested into that user's graph.                                                                                  | [Docs](/threads)                                                  |
| `graph.add` & `thread.add_messages`        | Methods for adding data to a graph and user graph respectively.                                                                                                                                                 | [Docs](/adding-data-to-the-graph) [Docs](/memory#adding-memory)   |
| `graph.search` & `thread.get_user_context` | Low level and high level methods respectively for retrieving from the knowledge graph.                                                                                                                          | [Docs](/searching-the-graph) [Docs](/memory#retrieving-memory)    |
| User Summary Instructions                  | Customize how Zep generates entity summaries for users in their knowledge graph. Up to 5 custom instructions per user to guide summary generation.                                                              | [Docs](/users#user-summary-instructions)                          |
| Agentic Tool                               | Use Zep's memory retrieval methods as agentic tools, enabling your agent to query for relevant information from the user's knowledge graph.                                                                     | [Docs](/quickstart#use-zep-as-an-agentic-tool)                    |

| Use case          | Purpose                                                                  | Implementation                                                                                                                                                                                                                                                                              |
| ----------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dynamic Graph RAG | Provide your agent with up-to-date knowledge of an object/system         | Add/stream all relevant data to a Graph ([docs](/adding-data-to-the-graph)), chunking first if needed ([docs](/adding-data-to-the-graph#data-size-limit-and-chunking)), and retrieve from the graph by constructing a custom context block ([docs](/cookbook/customize-your-context-block)) |
| Agent memory      | Provide your agent with up-to-date knowledge of a user                   | Add/stream user messages and user business data to a User Graph ([docs](/adding-memory)), and retrieve user memory as the context block returned from `thread.get_user_context` ([docs](/retrieving-memory)), and provide this context block to your agent before responding                |
| Voice agents      | Provide up-to-date knowledge with extremely low latency to a voice agent | Similar to other implementations, except incorporating latency optimizations ([docs](/performance))                                                                                                                                                                                         |

## What is Context Engineering?

Context Engineering is the discipline of assembling all necessary information, instructions, and tools around a LLM to help it accomplish tasks reliably. Unlike simple prompt engineering, context engineering involves building dynamic systems that provide the right information in the right format so LLMs can perform consistently.

The core challenge: LLMs are stateless and only know what's in their immediate context window. Context engineering bridges this gap by systematically providing relevant background knowledge, user history, business data, and tool outputs.

Using [business data and/or user chat histories](#business-data-vs-chat-message-data), Zep automatically constructs a [temporal knowledge graph](/graph-overview) to reflect the state of an object/system or a user. The knowledge graph contains entities, relationships, and facts related to your object/system or user. As facts change or are superseded, [Zep updates the graph](#managing-changes-in-facts-over-time) to reflect their new state. Through systematic context engineering, Zep provides your agent with the comprehensive information needed to deliver personalized responses and solve problems. This reduces hallucinations, improves accuracy, and reduces the cost of LLM calls.

<lite-vimeo videoid="1021963693" />

## How Zep Fits Into Your Application

Your application sends Zep business data (JSON, unstructured text) and/or messages. Business data sources may include CRM applications, emails, billing data, or conversations on other communication platforms like Slack.

<Frame>
  <img src="file:a6a7437b-6e89-4e01-ba06-d7ee9bc1b78a" />
</Frame>

Zep automatically fuses this data together on a temporal knowledge graph, building a holistic view of the object/system or user and the relationships between entities. Zep offers a number of APIs for [adding and retrieving memory](#retrieving-memory). In addition to populating a prompt with Zep's engineered context, Zep's search APIs can be used to build [agentic tools](#using-zep-as-an-agentic-tool).

The example below shows Zep's `memory.context` field resulting from a call to `thread.get_user_context()`. This is Zep's engineered context block that can be added to your prompt and contains facts and graph entities relevant to the current conversation with a user. For more about the temporal context of facts, see [Managing changes in facts over time](#managing-changes-in-facts-over-time).

[Zep's Context Block](/retrieving-memory#retrieving-zeps-context-block) is Zep's engineered context string containing relevant facts and entities for the thread. It is always present in the result of `thread.get_user_context()`
call and can be optionally [received with the response of `thread.add_messages()` call](/docs/performance/performance-best-practices#get-the-context-block-string-sooner).

Zep's context block can either be in summarized or basic form (summarized by default). Retrieving basic results reduces latency (P95 \< 200 ms). Read more about Zep's Context Block [here](/retrieving-memory#retrieving-zeps-context-block).

<Tabs>
  <Tab title="Summary (default)">
    <CodeBlocks>

<Tab title="Basic (fast)">
    <CodeBlocks>

You can then include this context in your system prompt:

| MessageType | Content                                                |
| ----------- | ------------------------------------------------------ |
| `System`    | Your system prompt <br /> <br /> `{Zep context block}` |
| `Assistant` | An assistant message stored in Zep                     |
| `User`      | A user message stored in Zep                           |
| ...         | ...                                                    |
| `User`      | The latest user message                                |

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
```

Example 4 (unknown):
```unknown
</Tab>

  <Tab title="Basic (fast)">
    <CodeBlocks>
```

---

## Mem0 Migration

**URL:** llms-txt#mem0-migration

**Contents:**
- Zep's memory model in one minute
  - Unified customer record
  - Domain-depth ontology
  - Temporal facts
  - Hybrid & granular search
- How Zep differs from Mem0
- SDK support
- Migrating your code
  - Basic flows
  - Practical tips

> How to migrate from Mem0 to Zep

Zep is a memory layer for AI agents that unifies chat and business data into a dynamic [temporal knowledge graph](/v3/concepts#the-knowledge-graph) for each user. It tracks entities, relationships, and facts as they evolve, enabling you to build prompts with only the most relevant information—reducing hallucinations, improving recall, and lowering LLM costs.

Zep provides high-level APIs like `thread.get_user_context` and deep search with `graph.search`, supports custom entity/edge types, hybrid search, and granular graph updates. Mem0, by comparison, offers basic add/get/search APIs and an optional graph, but lacks built-in data unification, ontology customization, temporal fact management, and fine-grained graph control.

<Note>
  Got lots of data to migrate? [Contact us](mailto:sales@getzep.com) for a discount and increased API limits.
</Note>

## Zep's memory model in one minute

### Unified customer record

* Messages sent via [`thread.add_messages`](memory#adding-memory) go straight into the user's knowledge graph; business objects (JSON, docs, e-mails, CRM rows) flow in through [`graph.add`](/v3/adding-data-to-the-graph). Zep automatically deduplicates entities and keeps every fact's *valid* and *invalid* dates so you always see the latest truth.

### Domain-depth ontology

* You can define Pydantic-style **[custom entity and edge classes](/v3/customizing-graph-structure)** so the graph speaks your business language (Accounts, Policies, Devices, etc.).

* Every edge stores when a fact was created, became valid, was invalidated, and (optionally) expired.

### Hybrid & granular search

* [`graph.search`](/v3/searching-the-graph) supports [hybrid BM25 + semantic queries, graph search](/v3/searching-the-graph), with pluggable rerankers (RRF, MMR, cross-encoder) and can target nodes, edges, episodes, or everything at once.

## How Zep differs from Mem0

| Capability                          | **Zep**                                                                                                                                                        | **Mem0**                                                                                                   |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Business-data ingestion**         | Native via [`graph.add`](/v3/adding-data-to-the-graph) (JSON or text); [business facts merge with user graph](/v3/concepts#business-data-vs-chat-message-data) | No direct ingestion API; business data must be rewritten as "memories" or loaded into external graph store |
| **Knowledge-graph storage**         | Built-in [temporal graph](/v3/concepts#managing-changes-in-facts-over-time); zero infra for developers                                                         | Optional "Graph Memory" layer that *requires* Neo4j/Memgraph and extra config                              |
| **Custom ontology**                 | First-class [entity/edge type system](/v3/customizing-graph-structure)                                                                                         | Not exposed; relies on generic nodes/relationships                                                         |
| **Fact life-cycle (valid/invalid)** | [Automatic and queryable](/v3/concepts#managing-changes-in-facts-over-time)                                                                                    | Not documented / not supported                                                                             |
| **User summary customization**      | [User summary instructions](users.mdx#user-summary-instructions) customize entity summaries per user                                                           | Not available                                                                                              |
| **Search**                          | [Hybrid vector + graph search](/v3/searching-the-graph) with multiple rerankers                                                                                | Vector search with filters; basic Cypher queries if graph layer enabled                                    |
| **Graph CRUD**                      | Full [node/edge CRUD](/v3/deleting-data-from-the-graph) & [bulk episode ingest](/v3/adding-data-to-the-graph)                                                  | Add/Delete memories; no low-level edge ops                                                                 |
| **Context block**                   | [Auto-generated, temporal, prompt-ready](/retrieving-memory#retrieving-zeps-context-block)                                                                     | You assemble snippets manually from `search` output                                                        |
| **LLM integration**                 | Returns [ready-made `memory.context`](/retrieving-memory#retrieving-zeps-context-block); easily integrates with agentic tools                                  | Returns raw strings you must format                                                                        |

Zep offers Python, TypeScript, and Go SDKs. See [Installation Instructions](/v3/quickstart) for more details.

## Migrating your code

| **What you do in Mem0**                                           | **Do this in Zep**                                                                                                                                                                            |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `client.add(messages, user_id=ID)` → stores conversation snippets | `zep.thread.add_messages(thread_id, messages=[...])` – keeps chat sequence **and** updates graph                                                                                              |
| `client.add("json...", user_id=ID)` (not really supported)        | `zep.graph.add(user_id, data=<JSON>)` – drop raw business records right in                                                                                                                    |
| `client.search(query, user_id=ID)` – vector+filter search         | *Easy path*: `zep.thread.get_user_context(thread_id)` returns the `memory.context` + recent messages<br />*Deep path*: `zep.graph.search(user_id, query, reranker="rrf")`                     |
| `client.get_all(user_id=ID)` – list memories                      | `zep.graph.search(user_id, '')` or iterate `graph.get_nodes/edges` for full dump                                                                                                              |
| `client.update(memory_id, ...)` / `delete`                        | `zep.graph.edge.delete(uuid_="edge_uuid")` or `zep.graph.episode.delete(uuid_="episode_uuid")` for granular edits. Facts may not be updated directly; new data automatically invalidates old. |

* **Thread mapping:** Map Mem0's `user_id` → Zep `user_id`, and create `thread_id` per conversation thread.
* **Business objects:** Convert external records to JSON or text and feed them through `graph.add`; Zep will handle entity linking automatically.
* **Prompting:** Replace your custom "summary builder" with the `memory.context` string; it already embeds temporal ranges and entity summaries.
* **Summary customization:** Use [user summary instructions](users.mdx#user-summary-instructions) to guide how Zep generates entity summaries for each user, tailoring the context to your specific use case.
* **Search tuning:** Start with the default `rrf` reranker; switch to `mmr`, `node_distance`, `cross_encoder`, or `episode_mentions` when you need speed or precision tweaks.

## Side-by-side SDK cheat-sheet

| **Operation**            | Mem0 Method (Python)           | Zep Method (Python)                                  | Notes                                         |
| ------------------------ | ------------------------------ | ---------------------------------------------------- | --------------------------------------------- |
| Add chat messages        | `m.add(messages, user_id=...)` | `zep.thread.add_messages(thread_id, messages)`       | Zep expects *ordered* AI + user msgs per turn |
| Add business record      | *n/a* (work-around)            | `zep.graph.add(user_id, data)`                       | Direct ingestion of JSON/text                 |
| Retrieve context         | `m.search(query,... )`         | `zep.thread.get_user_context(thread_id)`             | Zep auto-selects facts; no prompt assembly    |
| Semantic / hybrid search | `m.search(query, ...)`         | `zep.graph.search(..., reranker=...)`                | Multiple rerankers, node/edge scopes          |
| List memories            | `m.get_all(user_id)`           | `zep.graph.search(user_id, '')`                      | Empty query lists entire graph                |
| Update fact              | `m.update(id, ...)`            | *Not directly supported* - add new data to supersede | Facts are temporal; new data invalidates old  |
| Delete fact              | `m.delete(id)`                 | `zep.graph.edge.delete(uuid_="edge_uuid")`           | Episode deletion removes associated edges     |
| Customize user summaries | *not supported*                | `zep.user.add_user_summary_instructions()`           | Up to 5 custom instructions per user          |

## Where to dig deeper

* [**Quickstart**](/v3/quickstart)
* [**Graph Search guide**](/v3/searching-the-graph)
* [**Entity / Edge customization**](/v3/customizing-graph-structure)
* [**User summary instructions**](users.mdx#user-summary-instructions)
* **Graph CRUD**: [Reading from the Graph](/v3/reading-data-from-the-graph) | [Adding to the Graph](/v3/adding-data-to-the-graph) | [Deleting from the Graph](/v3/deleting-data-from-the-graph)

For any questions, ping the Zep Discord or contact your account manager. Happy migrating!

---
