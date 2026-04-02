# Architecting the B3 Graphiti Learning History System: Schema, Retrieval, and Agentic Integration

**Executive Summary & Key Insights**
*   **Schema & Storage:** It appears that the system models learning history through a unified entity naming convention, categorizing knowledge into conceptual and procedural types, while distinguishing specific events like `Misconception` and `LearningTip` via dedicated Pydantic schemas. Evidence suggests Neo4j relationships are utilized heavily to link concepts to their corresponding errors and annotations.
*   **Retrieval Mechanisms:** The system seems to rely on an Assessment Context Package (ACP) to aggregate student data. This package dynamically pulls 4-type error histories, edge reasoning, and mastery states to provide a holistic view of the learner prior to question generation.
*   **Prompt Design:** Research indicates the use of a sophisticated 5-layer prompt architecture inspired by Bloom's Taxonomy. It maps specific error types to targeted remediation strategies, dynamically injecting the student's Graphiti-retrieved history into the prompt while employing strict security boundaries against injection attacks.
*   **Noise & Decay Management:** As the graph expands, the system appears to mitigate noise through categorical `group_id` namespacing, token context budgets, and a bi-temporal FSRS-4.5 algorithmic decay model that calculates knowledge retrievability over time.
*   **K-RAG Implementation:** Evidence leans toward a partially implemented Knowledge-Enhanced RAG system. It features multi-source retrieval (LanceDB and Graphiti) and fallback mechanisms, though its full integration into the LangGraph framework remains an ongoing effort.
*   **Worker Status & Technical Debt:** While the `GraphitiEpisodeWorker` is designed with robust queuing and dead-letter stores, internal diagnostics reveal significant technical debt. It seems likely that many functions labeled as "Graphiti" are currently executing raw Neo4j Cypher queries, bypassing the official SDK. A major refactoring effort (Epic 3) is planned to resolve this facade.

**A Layman's Introduction to the Graphiti Memory System**
Imagine a highly intelligent filing cabinet that not only stores your study notes but also remembers *how* you struggled with them, *when* you made mistakes, and *why* two concepts are related in your mind. This is the goal of the B3 Graphiti Learning History system. Instead of treating learning as a flat list of test scores, it builds a "knowledge graph"—a web of concepts interconnected by your personal learning journey. 

If you misunderstand a math formula, the system records that specific "Misconception" and links it to the formula. When exam time comes, an AI tutor retrieves this web of memories, reviews your past mistakes, and tailors a brand new question specifically designed to test if you've overcome that exact hurdle. To prevent the system from getting overwhelmed by too many old, irrelevant notes, it uses an "forgetting curve" algorithm, gently fading out older memories unless they are proven to be highly important. While the theoretical design is exceptionally advanced, the system is currently under heavy construction, working to bridge its ambitious blueprints with stable, real-world code.

***

## 1. Entity and Relationship Schema in Graphiti/Neo4j

The foundation of the B3 learning architecture is its knowledge graph, which serves as a highly structured repository for tracking student progress, capturing nuanced learning behaviors, and maintaining historical context across disparate study sessions. The storage paradigm utilizes Neo4j as the underlying graph database, managed through a hybrid integration of direct Cypher queries and the Graphiti knowledge graph middleware [cite: 1].

### 1.1 Unified Entity Naming and Event Types

To maintain consistency across the knowledge graph, the system enforces a strict unified entity naming convention for nodes. According to the `GraphitiEpisodePayload` schema, the entity name format is structured as `"{KnowledgeType}:{EventType}:{concept_name}"` [cite: 1]. 

This ensures that nodes are easily searchable via Graphiti's `search_nodes` function without relying strictly on internal UUIDs. For example, if a student struggles with the logical concept of a contrapositive, the generated entity name would be `"conceptual:misconception:逆否命题"` [cite: 1]. 

The data payload for a learning event includes the following critical fields [cite: 1]:
*   **`schema_version`**: Versioning for backward compatibility.
*   **`event_type`**: The specific trigger (e.g., misconception detected).
*   **`knowledge_type`**: Categorization into `CONCEPTUAL` or `PROCEDURAL`.
*   **`severity`**: A float indicating the critical nature of the event.
*   **`tags`**: A list of metadata strings (e.g., `["needs_review"]`).
*   **`content`**: The raw text or transcription of the event.
*   **`node_id`**: The UUID linking back to the original Canvas node.

### 1.2 Storage of Tips, Errors, and Confusion Points

The system explicitly defines schemas for different types of learning feedback, specifically `LearningTip` and `Misconception`. These are implemented as Pydantic models that are ultimately serialized into Graphiti entities.

#### The 4-Type Error Classification
A core innovation in the schema is the `ErrorType` enumeration, which categorizes conversation errors and confusion points into four distinct cognitive failures. This framework directly informs downstream remediation [cite: 1]:

| Error Type Key | Chinese Label | Description / Symptom |
| :--- | :--- | :--- |
| `PROBLEM_FRAMING` | 破题错误 | Errors in reading comprehension; missing conditions; framing failures. |
| `REASONING_FALLACY` | 推理谬误 | Logical leaps; reversing causality; inappropriate induction during problem-solving. |
| `KNOWLEDGE_GAP` | 知识点缺失 | Lack of prerequisite knowledge; foundational definitions are not understood. |
| `SUPERFICIAL` | 似懂非懂 | Surface-level understanding; the student can recite facts but fails at application. |

Older, legacy entity types are mapped to this new unified model via an `ENTITY_TYPE_TO_UNIFIED` dictionary. For instance, a legacy `ProblemTrap` is mapped to `PROCEDURAL` knowledge with a `PROBLEM_TRAP_DETECTED` event type and a default severity of 0.7 [cite: 1].

### 1.3 Neo4j Node and Edge Schema

While Graphiti abstracts some of the graph complexity, the underlying Neo4j schema is heavily customized for the learning context. 

**Nodes:**
*   **`CanvasNode`** / **`LearningNode`**: Represents a specific concept or document from the user's study canvas. It contains properties like `canvas_path`, `node_id`, and text content [cite: 1].
*   **`EpisodicNode`**: Graphiti's primary storage mechanism for chronological events. The `source_description` property is used to differentiate the type of episode, such as `'error_record'` or `'conversation_archive'` [cite: 1].
*   **`EntityNode`**: Extracted concepts labeled with `["Concept"]` that group related ideas via `group_id` parameters like `"canvas_concepts"` [cite: 1].

**Relationships (Edges):**
Edges in Neo4j represent the reasoning and historical linkage between concepts.
*   **Canvas Associations**: When a relationship is detected between two canvas nodes, an edge is created. The edge label is normalized (uppercase with underscores, e.g., `CONNECTED_TO` or `PREREQUISITE`) [cite: 1].
*   **Edge Reasoning (`rationale`)**: A critical feature is the storage of *why* an edge exists. The system stores this in a `rationale` property directly on the relationship (e.g., `(n:CanvasNode)-[r]->(m:CanvasNode)` where `r.rationale` is populated) [cite: 1].
*   **Feedback Edges**: Entities are linked using schemas such as `HAS_TIP` (linking a `ConceptNode` to a `LearningTip`) and `HAS_MISCONCEPTION` (linking a `ConceptNode` to a `Misconception`) [cite: 1].

***

## 2. Retrieval of Personal Learning History

To generate highly personalized exam questions, the system must retrieve a student's idiosyncratic learning history. This is achieved through the **Assessment Context Package (ACP)** pipeline, invoked primarily by the `assemble_acp` tool function [cite: 1].

### 2.1 The Assessment Context Package (ACP) Assembly

The `assemble_acp` method acts as an orchestrator, pulling multi-modal data from various microservices to build a comprehensive context object (`ACPData`). The token budget for this object is strictly capped at 3,000 tokens [cite: 1].

The retrieval follows a sequenced pattern:
1.  **Node Content Classification**: The target node's text is fetched and classified into declarative knowledge (`k_signals`) or procedural knowledge (`p_signals`) to determine the `node_type` [cite: 1].
2.  **Mastery State Extraction**: The system queries the mastery engine (which relies on FSRS) to fetch metrics including `p_mastery`, `retrievability`, `effective_proficiency`, and a human-readable `mastery_label` (e.g., "Not Assessed") [cite: 1].
3.  **Tips Retrieval**: The `_get_tips` function searches the Graphiti memory to find custom annotations the student has made [cite: 1].
4.  **Error History Retrieval**: The system queries Graphiti for the student's past mistakes on this specific node [cite: 1].
5.  **Edge Reasoning**: The `_get_edge_reasons` function pulls the `rationale` strings from relationships connected to the target node [cite: 1].
6.  **Conversation Summary**: Pulls a Tier 2 summary of past AI-student dialogue regarding the topic [cite: 1].

### 2.2 Cypher-Based Graph Retrieval

Despite the theoretical use of Graphiti SDKs, the raw source code reveals that retrieval relies heavily on direct Neo4j Cypher queries executed through the `Neo4jClient`. 

For example, to retrieve the 4-type error history, the system runs the following query [cite: 1]:
```cypher
MATCH (e:EpisodicNode)
WHERE e.source_description = 'error_record'
  AND e.node_id = $node_id
RETURN e.error_type AS error_type, e.description AS description
ORDER BY e.created_at DESC
LIMIT 4
```
This directly fetches the four most recent errors associated with the node, mapping them back into the `error_type` and `description` dictionaries required by the ACP [cite: 1].

Similarly, to retrieve edge reasoning (confusion points or logical linkages), the system queries the relationships between Canvas nodes [cite: 1]:
```cypher
MATCH (n:CanvasNode {uuid: $node_id})-[r]->(m:CanvasNode)
WHERE r.rationale IS NOT NULL
RETURN r.rationale AS rationale
LIMIT 5
```

### 2.3 Priority Scoring for Target Nodes

When selecting which node to test, the system does not pick randomly. It uses a mathematical prioritization function [cite: 1]:
\[ \text{Priority} = (W_{MASTERY} \times (1.0 - p_{mastery})) + (W_{RETRIEVABILITY} \times (1.0 - \text{retrievability})) + (W_{KG\_RELEVANCE} \times kg_{relevance}) \]
If a node has already been examined, its priority score is penalized (multiplied by 0.3) to ensure novelty in the question generation process [cite: 1].

***

## 3. Prompt Design and ACP Data Injection

Once the personal learning history is aggregated into the `ACPData` object, it must be safely and effectively injected into the Large Language Model (LLM) for question generation. The system employs a highly structured, 5-layer prompt design inspired by the Bloom's Taxonomy PS4 strategy (arXiv:2408.04394) [cite: 1].

### 3.1 The 5-Layer Prompt Architecture

The `build_5_layer_prompt` function constructs the prompt through the following isolated layers [cite: 1]:
1.  **Layer 1 (Static)**: Defines the AI's persona and examiner role.
2.  **Layer 2 (User-selected)**: Injects the specific exam mode parameters.
3.  **Layer 3 (Dynamic)**: The ACP student data payload (learning history, mastery levels).
4.  **Layer 4 (Static/Dynamic)**: Core question generation rules, heavily modified by the calculated **Remediation Strategy**.
5.  **Layer 5 (Static)**: Output formatting instructions (enforcing strict JSON output).

### 3.2 Dynamic Remediation Strategies

The prompt design is uniquely powerful because Layer 4 dynamically shifts based on the dominant error type found in the student's ACP data. The `_determine_remediation_strategy` function analyzes the `error_history` dictionary, identifies the most frequent error, and selects a targeted prompt injection [cite: 1]. 

The strategies injected into the prompt are defined as follows [cite: 1]:

*   **For `PROBLEM_FRAMING` (破题错误)**: 
    *"【补救策略：破题错误】 该学生存在破题错误——能记住解法但无法灵活应用。请出「同结构不同包装」的新题，验证破题能力而非记忆。例如：更换题目的表面情境但保持底层数学/逻辑结构不变。"*
*   **For `REASONING_FALLACY` (推理谬误)**:
    *"【补救策略：推理谬误】... 请采用以下策略之一：1. 给出一段包含错误推理的过程，让学生找出错误并修正；2. 出反例题，要求学生判断某个看似正确的推理为何是错的。"*
*   **For `KNOWLEDGE_GAP` (知识点缺失)**:
    *"【补救策略：知识点缺失】... 请回退到定义级别的基础题，确认学生理解核心定义后再逐步升级难度。"*
*   **For `SUPERFICIAL` (似懂非懂)**:
    *"【补救策略：似懂非懂】... 请采用以下策略之一：1. 辨析题... 2. 反例题... 3. 迁移题..."*

### 3.3 Token Budgeting and Graceful Degradation

Because LLM context windows are finite and costly, the `_enforce_token_budget` method acts as a strict safeguard. The system calculates the total characters across the node content, conversation summary, tips, errors, and edge reasons [cite: 1]. 

If the combined size exceeds the `ACP_MAX_CHARS` limit, truncation occurs via a priority queue: the conversation summary is truncated first (to 500 characters), followed by the node content (to 800 characters), while ensuring that mathematical formulas (`$...$`) and code blocks are not split mid-token [cite: 1]. 

If the layer 3 external template file fails to load, the system relies on a programmatic fallback (graceful degradation) that manually stitches together `node_content`, `node_type`, `effective_proficiency`, and the dynamically appended `optional_sections` (tips, errors, edge reasons) [cite: 1].

### 3.4 Security and Injection Defense

Injecting user-generated content (like Canvas notes and chat histories) directly into a prompt presents a severe prompt injection vulnerability. To counter this, the `PromptTemplate` class enforces structural isolation using a `SYSTEM_BOUNDARY_MARKER` [cite: 1].

Furthermore, the system implements an exhaustive regex-based firewall to detect and neutralize adversarial data in the history payload [cite: 1]. Detected patterns include:
*   **Direct Injections**: `ignore\s+(all\s+)?previous\s+instructions`, `you\s+are\s+now\s+a`.
*   **Chinese Injections**: `(请|你)?忽略(之前|以前|上面)(的)?(所有)?指令`.
*   **Delimiter Spoofing**: `<\|system\|>`, `<\|assistant\|>`, `\[SYSTEM\s+OVERRIDE\]`.
*   **Indirect Manipulation**: `(this\s+)?(node|content|note).*?should\s+be\s+treated\s+as\s+(system\s+)?instructions?`.

***

## 4. Handling Noise and Relevance Decay

As the user's exam canvas usage grows, the knowledge graph inherently accumulates thousands of nodes, episodes, and edges. Left unchecked, this "graph bloat" would lead to catastrophic retrieval noise and LLM hallucination. The B3 architecture mitigates this through three distinct paradigms: Temporal FSRS decay, Categorical Namespacing, and Context Budgeting.

### 4.1 Temporal Memory and the FSRS-4.5 Algorithm

The system does not treat all memories equally; it employs a bi-temporal modeling engine backed by the Free Spaced Repetition Scheduler (FSRS v4.5) [cite: 1]. This acts as "Layer 3" of the memory system, tracked via asynchronous SQLite persistence (`aiosqlite`) and synchronized with the Graphiti graph [cite: 1].

The core decay mechanic calculates a knowledge retention score based on the formula [cite: 1]:
\[ R(t) = \left(1 + \frac{t}{S}\right)^{-\frac{1}{\text{decay}}} \]
Where \( S \) represents effective stability. The system modifies the base initial stability using multiple weights [cite: 1]:
*   **Difficulty Modifier**: `1 + difficultyWeight * (conceptDifficulty - 0.5)`
*   **Engagement Bonus**: `1 + 0.1 * docEngagement`
*   **Prerequisite Bonus**: `1 + 0.1 * prerequisiteReadiness`

When retrieving nodes, a signal named `fsrs_retrievability` (weighted at 0.25) is evaluated [cite: 1]. If a concept's retrievability falls below the `shaky_threshold` (0.40), it is flagged as a weak concept and prioritized for retrieval and examination [cite: 1].

### 4.2 Categorical Namespacing and `group_id` 

A major root cause of retrieval noise in earlier iterations was the use of monolithic Graphiti `group_id`s. When all decisions and episodes are shoved into a single group, retrieval precision collapses [cite: 1].

Following community consensus and architectures similar to "GuardKit," the system has transitioned to per-category and per-feature namespacing. The `group_id` parameter acts as a multi-tenancy and graph isolation barrier [cite: 1]. For example:
*   `{project_id}__feature_specs`: Context strictly isolated for specific subjects or features.
*   `role_constraints`: System-wide constraints devoid of dynamic noise [cite: 1].

During a RAG retrieval process, the search is inherently scoped. For instance, the `retrieve_graphiti` function attempts to isolate searches using `scoped_canvas = build_group_id(subject, canvas_file)` before querying the graph [cite: 1].

### 4.3 Context Budgeting and Multi-Signal Relevance Tuning

Even with scoped queries, a retrieval might return too many matches. The system addresses this with the "Context Budget" pattern (FEAT-GR-006) [cite: 1]. Rather than pulling a flat list of top-K vectors, the retriever allocates strict percentage limits to categories. 

For a 5,000-token budget, the retriever might allocate [cite: 1]:
*   `feature_context`: 30% (1,500 tokens)
*   `architecture_context`: 20% (1,000 tokens)
*   `similar_outcomes` / `warnings`: 30% (1,500 tokens)
*   `domain_knowledge`: 20% (1,000 tokens)

If retrieved warnings exceed 1,500 tokens, the lowest-scoring nodes are aggressively truncated. Scoring is multi-signal, combining vector similarity with an "Importance Score" (0.0 to 1.0) applied at write-time, ensuring that critical historical corrections (e.g., weighted at 0.9) easily outrank older, trivial interactions [cite: 1]. Graphiti's bi-temporal tracking also ensures auto-invalidation; if a new fact contradicts an old one, the system marks the old edge with a `t_invalid` timestamp, allowing the Cypher query to filter out `DEPRECATED` nodes [cite: 1].

***

## 5. Implementation Status of K-RAG (Knowledge-Enhanced RAG)

K-RAG (Knowledge-Enhanced Retrieval-Augmented Generation), an architectural concept previously highlighted in Gemini research and Agentic RAG maturity models, is actively implemented in the system, though designed with "graceful degradation" pathways.

### 5.1 Multi-Source Fan-Out Retrieval

The implementation, bridged via LangGraph (Phase 2), does not rely solely on a single vector database [cite: 1]. The `RAGService` orchestrates parallel, concurrent queries to multiple data stores:
1.  **LanceDB Node (`retrieve_lancedb`)**: Executes L2 distance semantic searches against Markdown explanation documents. Distances are inverted to scores via `1 / (1 + distance)` [cite: 1]. Performance constraints require a P95 latency of < 400ms [cite: 1].
2.  **Graphiti Node (`retrieve_graphiti`)**: Connects to the Graphiti middleware to pull structural data (Nodes, Edges, and Episodes), normalizing the payload into a unified format with strict schema matching [cite: 1].

### 5.2 Fusion Strategies and Timeout Tolerance

Because multiple distinct search spaces return results, the system features a Fusion Node that aggregates data. The API endpoint accepts different fusion configurations: `rrf` (Reciprocal Rank Fusion), `weighted`, or `cascade` [cite: 1]. For the specific use case of "Review Canvases" (检验白板), the `weighted` strategy is defined as the default [cite: 1].

To accommodate the high-speed requirements of real-time AI agents, the K-RAG implementation is heavily gated by timeouts. The `get_rag_context_with_timeout` function imposes a hard limit of `RAG_TIMEOUT_SECONDS = 2.0` [cite: 1]. 

If the `RAGService` fails to import, crashes, or the 2-second timeout is breached, the system executes an AC5 Graceful Degradation protocol. It logs a warning (`"RAG query timeout (2.0s), continuing without RAG context"`) and proceeds without injecting the extended knowledge context, ensuring the core agentic loop does not block [cite: 1].

Results that successfully clear the fusion tier are formatted into distinct citations (e.g., `lecture 3.md:29-65 (## A* 搜索) [02:27-04:48]`) before being appended to the agent's prompt context [cite: 1].

***

## 6. Operational Status of the GraphitiEpisodeWorker

Question 7 asks if the `GraphitiEpisodeWorker` is actually working. The research data provides a nuanced answer: The worker infrastructure is highly robust and operational at the queuing level, but it suffers from severe underlying "technical debt" where its actual connection to the Graphiti Core SDK is either bypassed or simulated via raw Cypher.

### 6.1 Worker Architecture and Resilience

The `GraphitiEpisodeWorker` is designed as an asynchronous, queue-based background worker (`asyncio.Queue`) designed to serialize writes to the knowledge graph [cite: 1]. 
According to the codebase, the worker receives an `EpisodeTask` containing the `name`, `episode_body`, and `group_id` [cite: 1]. 

To handle transient failures (e.g., Neo4j connection drops), the worker implements:
*   **Exponential Backoff with Full Jitter**: Wait times are calculated as \( \min(2^{\text{retry\_count}}, 60) \) multiplied by a random jitter factor [cite: 1].
*   **Dead-Letter Store**: If an episode fails beyond its `max_retries` (default 3), or if the queue is shutting down, the task is appended to a local JSONL file (`data/dead_letter_episodes.jsonl`) with its full traceback, allowing for manual replay later [cite: 1].

During the FastAPI application lifespan, the worker is initialized via `initialize_graphiti` (which instantiates the Gemini Embedder and LLM model) and gracefully shutdown using `await worker.stop(timeout=30.0)` [cite: 1].

### 6.2 The "Fake Naming" Technical Debt (Epic 3)

Despite this robust outer shell, the internal execution of "Graphiti" events is currently a critical known issue flagged in the development sprints. 

A Root-Cause Analysis report explicitly identifies **42 instances of "fake naming"** within the system [cite: 1]. Specifically, the core client file `backend/app/clients/graphiti_client.py` has **zero `graphiti-core` SDK calls** [cite: 1]. The report notes: *"30+函数名含graphiti全是Neo4j Cypher. 根因: AI混淆写入Neo4j不等于写入Graphiti."* (30+ function names containing 'graphiti' are entirely Neo4j Cypher. Root cause: The AI confused writing to Neo4j with writing to Graphiti) [cite: 1].

To resolve this facade, "Epic 3: Graphiti 真实集成" (Graphiti Real Integration) has been planned [cite: 1]. The objectives include:
*   **S-7**: Renaming the misleading `graphiti_client.py` to `neo4j_learning_client.py` or properly implementing the SDK [cite: 1].
*   **S-8**: Ensuring that the `episode_worker.py` becomes the *only* authorized pathway for Graphiti writes, preventing other microservices from executing raw Cypher inserts that bypass the graph's indexing and temporal engines [cite: 1].

Therefore, while the worker *process* runs successfully, its current data insertion methodology relies heavily on legacy Neo4j logic, requiring immediate refactoring to realize the full potential of the Graphiti middleware.

***

## Conclusion

The B3 Graphiti Learning History system represents an ambitious fusion of semantic knowledge graphs, bi-temporal FSRS decay algorithms, and dynamic prompt engineering. By structuring errors and tips into a strict 4-type taxonomy and retrieving them via the 3,000-token ACP pipeline, the system allows Large Language Models to act as highly context-aware tutors. While the temporal tracking successfully manages relevance decay and mitigates context bloat, the architectural implementation of the `GraphitiEpisodeWorker` remains a work in progress, currently leaning heavily on direct Neo4j Cypher fallbacks to bridge the gap between design and production.

**Sources:**
1. backend/app/clients/neo4j_learning_base.py (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
