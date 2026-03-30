# Canvas Learning System: Comprehensive Product Requirements Document for Phase 3 and Phase 4 Integration

The development of the Canvas Learning System has reached a critical inflection point. Following the successful execution of Phase 1 (Startup Verification) and Phase 2 (Core System and Graphiti Integration), the architectural foundation of the agentic Retrieval-Augmented Generation (RAG) system is now stabilized. Research suggests that the "bottom-up" (Path A) execution strategy effectively isolates technical debt, allowing for systematic remediation of the legacy pipeline before introducing frontend refinements. It seems likely that the forthcoming phases—Phase 3 (Pipeline Repair) and Phase 4 (User Interface Polish)—will heavily dictate the system's operational viability as a cohesive learning tool. This report synthesizes the current implementation status, meticulously analyzes the delta between existing source code and required capabilities, and provides an exhaustive Product Requirements Document (PRD) to guide the fulfillment of the Minimum Viable Product (MVP) objectives. 

The key points of the current system trajectory are as follows:
*   **Phase 1 and Phase 2 are fully complete**, meaning the core startup sequence, database topology (Neo4j port 7691), and Graphiti integrations are actively operational.
*   **Fourteen Essential MVP Items** govern the release criteria. While infrastructural elements (like Claude Code migration and basic frontend displays) are complete, critical connective tissues (such as precise note indexing, advanced dashboard routing, and externalized prompt management) remain strictly in the Phase 3 purview.
*   **Technical Pruning has been executed** to ensure system stability. Features such as the `CognitiveLoadTimer`, textbook cross-canvas search, and multi-vault mappings have been strategically deprecated to prioritize the fidelity of core learning loops.
*   **The priority for Profile functionality is asymmetrical**: Click-to-jump navigation holds the absolute highest priority, followed by the generation of new doubt nodes, while historical record tabulation is explicitly delayed.

This comprehensive document serves as the academic and engineering blueprint for finalizing the Canvas Learning System MVP.

---

## 1. Executive Summary and Implementation Status Analysis

The Canvas Learning System employs a highly advanced, multi-layered cognitive architecture designed to facilitate constructivist learning via an interactive, AI-mediated graph environment. The project is currently transitioning from backend algorithm stabilization (Phases 1 and 2) to pipeline remediation and user experience alignment (Phases 3 and 4) [cite: 1]. 

### 1.1 Retrospective: Phase 1 and Phase 2 Achievements

The strategic decision to adopt "Path A" (a bottom-up pipeline reconstruction) has yielded significant infrastructural dividends [cite: 1]. Phase 1 successfully established environmental reliability. Crucial configuration parameters were standardized, most notably the binding of the Neo4j instance to `bolt://localhost:7691` to separate learning environments from development endpoints [cite: 1]. Furthermore, Content Security Policy (CSP) configurations in the Tauri framework were adjusted (`csp: null` during development) to permit localhost and external API interactions without fatal browser-level blocking [cite: 1]. Approximately 5,090 lines of dead code were eliminated, exorcising ghost tables and neutralizing rollback vulnerabilities [cite: 1]. The `CognitiveLoadTimer`, previously identified as a source of architectural friction and UX misalignment, was permanently excised from the source tree, and a critical dual-sided scoring bug (frontend overflow and backend miscalculation) was successfully patched [cite: 1].

Phase 2 heralded the activation of the core AI memory and execution engines. The integration of `graphiti-core >= 0.28.2` replaced legacy JSON-fallback mocks with a genuine Neo4j-backed episodic memory system [cite: 1]. The `episode_worker.py` successfully implemented asynchronous event consumption for the Graphiti `add_episode` operations. Simultaneously, the Gemini-based multimodal RAG pipeline (encompassing LLM, Embedder, and Reranker functionalities) was verified, successfully replacing hardcoded stubs [cite: 1]. The transition from legacy conversational agents to a Claude Code migration paradigm has been marked as fully complete [cite: 1].

### 1.2 Status of the 14 MVP Essential Items

The MVP is strictly defined by 14 operational capabilities. Their current status dictates the roadmap for Phases 3 and 4:

1.  **Original Canvas Frontend**: **COMPLETE**. The ReactFlow-based JSON Canvas implementation supports CRUD operations, drag-and-drop, scaling, and edge drawing [cite: 1].
2.  **Exam Canvas Frontend**: **COMPLETE**. The dedicated examination space successfully instantiates dynamically generated assessment nodes [cite: 1].
3.  **Exam Prompts (Point-by-Point + Confusion + Transfer)**: **PARTIAL (Phase 3 target)**. The prompt engineering strategy is fully defined across 5 layers, but architectural rules dictate these *must* be externalized as Markdown files (`backend/prompts/exam/layer*.md`). Currently, layers 1, 2, 4, and 5 exist as files, while Layer 3 (Assemble Context Protocol - ACP) remains hardcoded and must be migrated [cite: 1].
4.  **Node AI Dialogue**: **PARTIAL (Phase 3 target)**. While the backend MCP server is operational, the Tauri sidecar IPC (Inter-Process Communication) requires rigorous Windows verification to ensure stable context streams [cite: 1].
5.  **Tips/Edge/Error/Question Write & Retrieve**: **PARTIAL (Phase 3 target)**. Inline annotations are correctly dual-written (localStorage and backend), but the retrieval formatting requires schema fixes (e.g., entity type PascalCase enforcement) [cite: 1].
6.  **Exam Canvas New Discovery Write**: **PENDING (Phase 3 target)**. Requires the stabilization of the Profile Loop to allow doubts generated in the Exam Canvas to instantiate as new learning nodes [cite: 1].
7.  **Dashboard (Canvas List + Exam List + 3 Action Buttons)**: **PARTIAL (Phase 3 target)**. The structural UI exists with three tabs (Whiteboard, Exam History, Review), but underlying data hydration for exam records and error history is missing or delayed [cite: 1].
8.  **Edge Dialogue**: **PENDING (Phase 3 target)**. The system must support a two-strategy dialogue mechanism (EI + SE) mapped to connection edges [cite: 1].
9.  **Agentic RAG L1 + L2**: **PARTIAL (Phase 3 target)**. Graphiti and LanceDB indices are working, but routing and pipeline consolidation are required following the pruning of legacy paths [cite: 1].
10. **Precise Note Search**: **PENDING (Phase 3 target)**. The indexing indicates success but routinely returns empty query sets. This requires a forced rebuild logic and `subject` parameter isolation [cite: 1].
11. **Basic Hybrid Search**: **PENDING (Phase 3 target)**. LanceDB Full-Text Search (FTS) currently fails on Chinese text due to default Tantivy tokenization. Integration of `jieba` tokenization is mandatory [cite: 1].
12. **Claude Code Migration**: **COMPLETE**. The backend effectively exposes algorithms via the Model Context Protocol (MCP) to the Agent CLI [cite: 1].
13. **Slash Command Prompt Templates**: **PENDING (Phase 4 target)**. Implementation of extensible commands (e.g., `/explain`) with specific execution constraints (e.g., not exposing direct answers during exams) [cite: 1].
14. **Dialogue Pull-Out Nodes**: **PENDING (Phase 3 target)**. High-priority Profile functionality to jump from annotations to source nodes [cite: 1].

---

## 2. Phase 3: Pipeline Repair and Integrity PRD

Phase 3 is the most technically dense segment of the remaining project lifecycle. It transitions the system from a state of "isolated components" to a "unified, reliable pipeline" [cite: 1]. The estimated effort spans 2 to 3 dedicated development sessions. The guiding architectural philosophy is Boris Tane's mode: code implementation strictly follows structural annotation and architectural alignment [cite: 1].

### 2.1 Sidecar Windows Verification and IPC Hardening

The frontend-to-backend communication relies on a Tauri sidecar pattern to bridge the React UI with the Python MCP backend. Currently, this connection requires rigorous verification specifically on Windows environments to satisfy MVP constraints #4 and #12 [cite: 1].

**Problem Statement:**
Windows-specific environmental nuances—such as Node.js PATH resolutions, Vault directory path escaping, and orphaned zombie processes upon application exit—pose severe stability risks to the sidecar model [cite: 1]. 

**Requirements and Specifications:**
*   **Event Transmission Architecture (Decision GDR-P0-1):** The system must utilize a `stream-json` bridge. The Python sidecar will emit structured JSON streams which are intercepted by the Tauri Rust core via standard I/O channels, and subsequently broadcast to the React frontend via Tauri's IPC event system (`emit`/`listen`) [cite: 1].
*   **IPC Payload Constraints (Decision GDR-P1-4):** To prevent buffer overflow and UI thread blocking, single IPC payloads must not exceed 100KB. The backend must stream delta updates (token-by-token generation) rather than monolithic blocks [cite: 1].
*   **Fallback Mechanism (Decision GDR-P1-3):** If the Tauri Shell process instantiation fails or becomes unresponsive, the frontend must execute an `engine-fallback` protocol, gracefully degrading to direct HTTP calls to the backend API, utilizing the API key mode configuration [cite: 1].
*   **Tool Use State Machine (Decision GDR-P0-2):** The Claudian UI must reflect a deterministic 4-state lifecycle for MCP tool execution [cite: 1]:
    1.  `pending`: Tool call requested by LLM, awaiting execution slot.
    2.  `running`: Tool is actively executing in the Python backend.
    3.  `completed` / `error`: Tool execution finalized, returning output or stack trace.
    4.  `blocked`: A crucial security state indicating the tool (e.g., `record_learning_memory`) requires explicit user authorization before proceeding [cite: 1].

### 2.2 Note Indexing Engine and Chinese Hybrid Search (High Priority)

The retrieval augmentation pipeline relies on LanceDB for vector storage and Full-Text Search (FTS) [cite: 1]. Currently, MVP #10 (Precise Note Search) and #11 (Basic Hybrid Search) are critically impaired by an indexing anomaly and a tokenization incompatibility, respectively [cite: 1].

**Problem Statement 1: "Index Success but Return Empty"**
The `index_vault_notes` endpoint reports success, but retrieval yields zero vectors. This indicates an asynchronous race condition during LanceDB commit or a failure to properly partition the dataset [cite: 1]. 
*   **Resolution:** Implement a `force_rebuild` flag. Modify the indexing endpoint to mandate a `subject` parameter (Decision S27-GDA-3) to enforce strict disciplinary isolation [cite: 1]. A sub-investigation must be conducted regarding the Obsidian Advanced URI schema to determine if precision routing to specific note paragraphs/lines is viable [cite: 1].

**Problem Statement 2: Chinese Tokenization Failure in LanceDB (HIGH H1)**
LanceDB’s underlying FTS engine, Tantivy, defaults to an English-centric whitespace and stemming tokenizer. Consequently, contiguous Chinese characters (e.g., "贝叶斯定理") are hashed as single, monolithic tokens. A query for "贝叶斯" fails to yield a match [cite: 1].
*   **Resolution:** Prior to LanceDB ingestion, the text must be pre-processed using the `jieba` tokenization library [cite: 1].
*   **Implementation Strategy:** Utilize the precise cut mode (`jieba.cut(text, cut_all=False)`). The full mode introduces excessive FTS noise. The tokens must be concatenated with spaces before being passed to LanceDB, allowing Tantivy to process them as pseudo-English words. This fulfills FR-RET-P-02 requirements while remaining within the defined bounds (preventing DD-10 scope creep) [cite: 1].
*   **Search Mode Default:** Modify the global search configuration to default to `Hybrid` (Dense bge-m3 + FTS), reflecting the 11-16% recall improvement validated in standard benchmarks [cite: 1].

### 2.3 Externalized Prompt Architecture and Execution Constraints

Hardcoded prompts are strictly prohibited by the architectural guidelines (Decision S27-GDA-4) [cite: 1]. The exam generation pipeline relies on a sophisticated 5-layer prompt structure [cite: 1].

**Current State:** Layers 1, 2, 4, and 5 exist in the file system. Layer 3, the Assemble Context Protocol (ACP), remains hardcoded [cite: 1].

**Requirements:**
*   **Migration:** Extract the Layer 3 ACP logic into `backend/prompts/exam/layer3.md` [cite: 1].
*   **Execution Rule Update (Decision S27-GDA-9):** Within Layer 4 (the operational constraints layer), explicit instructions must be added to handle slash commands during an active examination. If a user invokes `/explain` during a test, the AI must pivot to a Socratic guidance mode—facilitating conceptual reasoning without exposing the direct answer to the current test node [cite: 1].
*   **Node Epistemology (Decision S27-GDA-10):** A "Doubt Node" spawned during an exam must transition into a standard dialogue mode (learn-before-test paradigm). It becomes eligible for assessment only in subsequent examination cycles [cite: 1].

### 2.4 Profile Loop and Dashboard Data Hydration

The Dashboard currently presents an empty UI shell consisting of three tabs: Whiteboard, Exam History, and Review [cite: 1]. The Profile system requires data hydration, but with strictly enforced hierarchical priorities [cite: 1].

**Priority Matrix:**
1.  **Jump Highest (P0):** The ability to click a historical Tip or Error and jump directly to the original context [cite: 1].
2.  **Doubt Nodes (P1):** Spawning new whiteboard nodes from unresolved doubts.
3.  **Records/History (P3):** Compiling a tabular history of exam results is explicitly delayed to Phase 4 or beyond [cite: 1].

**Implementation of Click-to-Jump (Decision S27-GDA-6):**
*   **Data Layer Mutation:** The `TipItem` and `ErrorItem` schemas must be augmented to include `sourceSessionId`, `sourceCanvasId`, and `sourceExamId` [cite: 1].
*   **Frontend Routing:** The React application (`App.tsx`) must expose and trigger the existing `setSelectedNodeId()` and `goToCanvas()` functions upon user interaction with a Profile item, enabling seamless contextual switching [cite: 1].

**Data Schema Normalization:**
*   The `record_learning_memory` MCP tool currently generates `entity_type` strings with inconsistent casing. The backend validation layer must enforce PascalCase (e.g., `Misconception`, `ProblemTrap`) [cite: 1].
*   The metadata payload must be updated to capture and persist the aforementioned `source_session_id` and `source_canvas_id` [cite: 1].

### 2.5 Remedial Strategy Integration (GDA2-3 Finding)

A critical logical disconnect exists in the examination pipeline. While user errors are successfully classified and mapped by the system, the Question Generator algorithm fails to consume these remedial strategies during subsequent test creation [cite: 1].

**Resolution Workflow:**
*   **Context Injection:** The `QuestionGenerator` must interface with the newly externalized ACP Layer 3 prompt to inject the historical remedial strategy data [cite: 1].
*   **Adaptive Question Generation:** The generation prompt must dynamically pivot based on the specific error type retrieved from Graphiti. For example, if the error is categorized as a "Problem Trap," the system should generate a structurally identical but functionally novel question. If the error is a "Reasoning Fallacy," the system should generate a "find-the-error" question format [cite: 1].

### 2.6 RAG Pipeline Pruning and MCP Tool Migration

To ensure system maintainability, the RAG topology is being actively simplified (Decision S27-GDA-2) [cite: 1]. 

**Pruning:**
*   The pending `textbook_retriever` and `cross_canvas_retriever` channels are permanently cancelled [cite: 1].
*   The finalized four-channel architecture consists of: LanceDB, Vault Notes, Graphiti, and Multimodal (Gemini Vision) [cite: 1].
*   **Bug Fix (W1/W2/W5):** Resolve the dual-search anomaly where `vault_notes` was simultaneously queried via a dedicated node and the `DEFAULT_TABLES` array. `vault_notes` must be excised from `DEFAULT_TABLES` (`["canvas_explanations", "canvas_concepts", "canvas_nodes", "vault_notes"]`) [cite: 1].

**MCP Tool Graphiti Migration (Impact Analysis):**
The integration of Graphiti mandates the rewriting of six specific MCP tools to transition data flow from the legacy JSON fallback to the Neo4j instance [cite: 1]:
1.  `record_learning_memory`: Rerouted to trigger Graphiti's `add_episode` [cite: 1].
2.  `search_memories`: Upgraded from primitive string matching to a three-tier hierarchical search [cite: 1].
3.  `record_error`: Errors must be classified via an LLM sub-routine before Graphiti ingestion [cite: 1].
4.  `search_notes`: The Graphiti vector channel transitions from a dummy stub to an active database query [cite: 1].
5.  `archive_conversation`: Session transcripts are serialized and persisted into Graphiti [cite: 1].
6.  `generate_question`: ACP data aggregation pulls historical node performance directly from Graphiti trajectories [cite: 1].
*(Note: Tools such as `query_mastery`, `score_answer`, `request_hint`, etc., remain unaffected by this migration [cite: 1])*

---

## 3. Phase 4: User Interface Polish and Experience Alignment PRD

Phase 4, estimated to require 1 to 2 development sessions, shifts focus from backend algorithmic integrity to frontend ergonomics, LLM session management, and visual consistency [cite: 1].

### 3.1 Global Theming and Visual Aesthetics

The Canvas Learning System requires a unified aesthetic language that reduces cognitive fatigue during prolonged study sessions.
*   **Theme Selection (DD-05):** Following user validation of preliminary Pencil mockups, the frontend application will strictly adhere to the `Catppuccin Mocha` dark color palette [cite: 1]. 
*   **Node Color Management:** The system supports dynamic node colors (e.g., Red=1, Green=2, Purple=3, Blue=5, Yellow=6) [cite: 1]. However, an explicit architectural decision has been made: these colors are strictly for user-driven visual annotation. The backend will not sync, interpret, or alter node colors automatically. No additional synchronization logic is to be developed [cite: 1].

### 3.2 System Configuration and LLM Management Dashboard

In accordance with Decision S27-GDA-7, the Dashboard must provide a robust, transparent control panel for monitoring and modifying local and remote LLM integrations [cite: 1].

**Frontend Requirements (App.tsx / Settings Panel):**
*   **Embedded Model State (Task 5):** Implement a read-only header labeled "Embedded Model". This will display the active topology (e.g., `bge-m3 · Ollama · [Status]`), querying the `/api/v1/health` endpoint to reflect real-time daemon status [cite: 1].
*   **API Key Security (Task 6):** All API token inputs must utilize `type='password'` with a standard eye-icon toggle. Upon initial input, the application must invoke an Obsidian `Notice` component warning: *"Conversation content will be transmitted to the selected LLM API provider."* The `saveSettings()` lifecycle must be scrubbed of any `console.log` statements that might leak credentials into the Tauri developer console [cite: 1].
*   **Backend Connection UI (Task 7):** Provide input fields for the primary Backend API URL (default: `http://localhost:8001`) and the Neo4j Database URI (default: `bolt://localhost:7689` for dev, though the environment variables enforce 7691 for production) [cite: 1].
*   **Data Management Stubs (Task 8):** Render a "Data Management" section with placeholder buttons for "Manual Backup" and "Rebuild Index". Clicking these must trigger toast notifications indicating future story implementation (`Story 1.8` and `Story 2.7` respectively) [cite: 1].

**Backend Integration (LiteLLM Core):**
*   **Configuration Schema (Task 9):** Establish `backend/app/core/litellm_config.py`. Define Pydantic models: `ModelTaskConfig` (fields: `provider`, `model_name`, `api_key`) and `SystemModelConfig` (encapsulating configurations for three distinct tasks: `chat`, `scoring`, and `embedding`) [cite: 1].
*   **API Endpoints:**
    *   `POST /api/v1/system/config`: Receives the JSON payload from the frontend and mutates the active runtime configuration [cite: 1].
    *   `POST /api/v1/system/test-llm`: Triggers a lightweight completion request (e.g., "Hello") to validate the provided API key and provider routing [cite: 1].

### 3.3 Conversational Context and Session Management

The AI node dialogue system relies on sophisticated context window handling. Unlike traditional chat interfaces, context here is highly localized.

*   **Per-Node Session Isolation:** Conversation history must be mapped uniquely to individual canvas nodes. The `sessionMap` will be persisted within the browser's `localStorage` [cite: 1].
*   **Uncompressed Frontend Display:** The React component rendering the chat panel must display the entire conversation history without aggressive truncation or summarization techniques, allowing the user to review the full Socratic dialogue [cite: 1].
*   **Backend Support:** Leverage the Claude SDK's 1-million token context window capabilities to ingest the prolonged histories seamlessly [cite: 1].
*   **Future Investigation:** While not strictly within the Phase 4 MVP constraint, technical debt tickets should be created to evaluate long-term session persistence strategies (moving off `localStorage`) and automated session naming conventions (referencing the Claudian session management paradigm) [cite: 1].

---

## 4. Technical Architecture and Code Delta Analysis

This section analyzes the precise gap between the existing codebase and the functional requirements defined in Phase 3 and Phase 4.

### 4.1 Backend Pipeline Deltas

**What Exists:**
*   FastAPI application scaffold with health endpoints [cite: 1].
*   Neo4j drivers configured to port 7691 [cite: 1].
*   Ollama containerized instance with `bge-m3` pulled [cite: 1].
*   15 Model Context Protocol (MCP) tools implemented with HMAC-SHA256 token verification mechanisms [cite: 1].
*   The `generate_question` -> `score_answer` -> `update_fsrs/bkt` evaluation chain [cite: 1].
*   Reranking algorithms defined but awaiting full pipeline binding (including RRF, Linear Combination, Cross-Encoder, and MMR) [cite: 1].

**What Must Be Built (The Delta):**
*   **MCP Hook Implementation:** The `PreToolUse` hook is currently missing. Consequently, all LLM tool calls execute instantaneously. This hook must be engineered to pause execution, transition the Tauri state machine to `blocked`, and await explicit React frontend permission for destructive or high-impact actions (e.g., committing memory to Graphiti) [cite: 1].
*   **Graphiti Data Schemas:** Refactoring Graphiti ingestion payloads. Specifically, transforming `entity_type` variables to enforce PascalCase constraints, and updating the metadata dictionaries to dynamically append `source_session_id` and `source_canvas_id` derived from the frontend invocation context [cite: 1].
*   **Hybrid Search Tokenizer:** Python backend implementation of `jieba`. 
    ```python
    import jieba
    def preprocess_for_tantivy(text: str) -> str:
        # Utilizing precise mode cut_all=False
        tokens = jieba.cut(text, cut_all=False)
        return " ".join(tokens)
    ```
    This function must intercept all document text before insertion into LanceDB, and similarly intercept all search queries before the `lancedb_client.py` executes the `.where()` clause [cite: 1].
*   **Tool Refactoring:** Modifying the internals of the 6 Graphiti-impacted tools (`record_learning_memory`, `search_memories`, `record_error`, `search_notes`, `archive_conversation`, `generate_question`) to replace `mock_json_db.insert()` calls with asynchronous Neo4j/Graphiti SDK driver calls [cite: 1].

### 4.2 Frontend Integration Deltas

**What Exists:**
*   Tauri shell with React + ReactFlow providing a stable 2D canvas [cite: 1].
*   Three core Dashboard view states and tab navigation components [cite: 1].
*   A functional Node Chat panel capable of rendering markdown [cite: 1].
*   Inline Annotation popups capable of writing to localStorage [cite: 1].

**What Must Be Built (The Delta):**
*   **IPC Listener and State Management:** The React application requires a dedicated global context (or Zustand store) to subscribe to the Tauri `stream-json` channel.
    ```typescript
    interface McpToolState {
      toolId: string;
      status: 'pending' | 'running' | 'completed' | 'error' | 'blocked';
      payload?: any;
    }
    // Listen for backend state emissions
    listen('mcp-tool-event', (event) => {
       updateMcpStore(event.payload);
    });
    ```
*   **Profile Navigation Logic:** Augmenting the Review tab UI. When a user clicks a historical tip or error, the UI must construct a navigation payload.
    ```typescript
    const handleProfileItemClick = (item: TipItem) => {
        if(item.sourceCanvasId && item.sourceNodeId) {
            goToCanvas(item.sourceCanvasId);
            setTimeout(() => {
                setSelectedNodeId(item.sourceNodeId);
                // Trigger camera pan to node
            }, 300); // Wait for canvas hydration
        }
    }
    ```
*   **Dashboard Settings Screen:** Construction of the form components detailed in Section 3.2, bound to Axios calls targeting the `/api/v1/system/config` endpoint [cite: 1]. Implement the `Catppuccin Mocha` CSS custom properties globally [cite: 1].

### 4.3 Advanced Reranking and Context Assembly (Backend)

The agentic RAG system utilizes multiple reranking algorithms based on the context of the operation. While the theoretical models exist, their explicit parameterization must be finalized in Phase 3.

*   **RRF (Reciprocal Rank Fusion):** Designated as the default mechanism for standard hybrid queries [cite: 1]. Fuses the sparse dense arrays from `bge-m3` with the BM25 statistical scores from Tantivy.
*   **Cross-Encoder:** To be invoked strictly during the `selected_nodes_for_review_hybrid` sequence where absolute maximum precision is required to generate the examination board configuration. Expected latency is <500ms [cite: 1].
*   **MMR (Maximal Marginal Relevance):** Deployed when the LLM triggers the `analyze_learning_patterns_hybrid` tool. By prioritizing node diversity, MMR prevents the LLM context window from being flooded with near-identical node variations when analyzing the learning trajectory (the "color flow path") [cite: 1].
*   **Node Distance Reranker:** Applied specifically for bottleneck identification. When searching for "red/purple nodes" indicating learning difficulty, the reranker penalizes nodes physically distant in the JSON canvas graph from the currently active study node [cite: 1].

---

## 5. Acceptance Criteria and Success Metrics

To ensure the rigorous completion of the Canvas Learning System MVP, the following acceptance criteria (AC) establish objective exit conditions for Phases 3 and 4 [cite: 1].

### 5.1 Phase 3 Exit Conditions (Pipeline Repair)

1.  **Sidecar Stability:** Launching the system via `npm run tauri dev` on a Windows operating system successfully initializes the backend without PATH errors. Right-clicking a node and selecting "Chat" successfully returns a streamed AI response without UI freezing [cite: 1]. 
2.  **Tool State Reflection:** Executing an MCP tool visualizes the transition through `pending` -> `running` -> `completed` states on the frontend [cite: 1].
3.  **Indexing Integrity:** Executing the note indexer with a specific `subject` parameter yields retrievable dense vectors within LanceDB. Queries utilizing Chinese text successfully return relevant chunks via hybrid search [cite: 1].
4.  **Prompt Externalization:** The `backend/prompts/exam/layer3.md` file exists, is correctly formatted, and is dynamically loaded by the `generate_question` tool [cite: 1].
5.  **Profile Loop Integrity:** A user can create a Tip annotation on a test canvas. Returning to the Dashboard Review tab, clicking that specific Tip successfully routes the UI back to the original test canvas and highlights the source node [cite: 1].
6.  **Graphiti Writing:** Submitting a `POST /memory/episodes` payload results in successful enqueuing by the worker, and a subsequent `search_memories` call for a known topic (e.g., "Limit Definition") returns the newly created episode [cite: 1].

### 5.2 Phase 4 Exit Conditions (UI and Settings)

1.  **Theming:** The entire application renders cleanly utilizing the Catppuccin Mocha dark palette without contrast accessibility violations [cite: 1].
2.  **LLM Dashboard:** The Settings panel correctly displays the health status of Ollama components [cite: 1].
3.  **Configuration Security:** API Keys entered into the system are masked via password inputs, trigger an explicit security notification, and successfully persist to the backend `SystemModelConfig` via `POST /api/v1/system/config` without console leakage [cite: 1].
4.  **Context Persistence:** Closing a node chat panel, refreshing the application, and reopening the chat panel correctly hydrates the entire, uncompressed conversational history from `localStorage` [cite: 1].

By adhering strictly to this detailed PRD, the Canvas Learning System will successfully bridge the gap between a technologically complex prototype and a stable, unified Minimum Viable Product, ready for extensive personal constructivist learning sessions.

**Sources:**
1. _bmad-output/brainstorming/implementation-roadmap-2026-03-13.md (fileSearchStores/persistentcanvaslearningsys-z2njevmxp7md)
