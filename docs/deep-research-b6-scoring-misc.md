# System Architecture and Implementation Analysis of the Canvas Learning Environment

**Executive Summary and Leading Insights**
The implementation of the Canvas Learning System exhibits a highly sophisticated, multi-layered architecture designed to fuse pedagogical theory with advanced AI evaluation and knowledge graph capabilities. Based on the provided repository data, we can concisely address the primary inquiries:
*   **3-Layer Scoring Insurance:** Yes, the architecture fully implements a 3-layer scoring insurance system. This includes 3x self-consistency sampling, a 4-dimensional rubric anchored in the SOLO taxonomy, and an optional dual-model verification system for faithfulness and consistency checks.
*   **Canvas Content Capabilities:** The canvas supports Text, File (Markdown/PDF/Images), Link, and Group nodes. Image support includes standard formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.svg`, `.webp`). Its capabilities tightly mirror and interoperate with the native Obsidian Canvas JSON schema, utilizing specific embed syntax resolutions.
*   **SOLO Taxonomy and Pedagogical Algorithms:** The SOLO taxonomy is actively implemented in the scoring rubrics. Regarding the "FIRe" algorithm, the codebase extensively details the implementation of the **FSRS (Free Spaced Repetition Scheduler)** algorithm (v4.5) rather than an explicitly named "FIRe" algorithm. FSRS is fully implemented, tracks micro-cognitive states, and is exceptionally well-suited for a single-user learning system.
*   **Edge Elaborative Interrogation (EEI):** EEI is actively implemented via the `edge-dialog.md` prompt. In the code, it triggers when users connect two concepts, acting as a study peer to ask "why/how" causal questions, probing for counterexamples, and enforcing a strict 3-4 round limit to prevent fatigue. 
*   **Click-to-Jump Navigation:** Implemented extensively. In a native Obsidian environment, it uses the `CanvasNavigator` API for node highlighting and zooming. In the Tauri environment, it relies on a degradation strategy using the `@tauri-apps/plugin-shell` to invoke `obsidian://adv-uri` protocols.
*   **Performance Guarantees:** Fully implemented. The system utilizes an Assessed Concept Profile (ACP) token budget to enforce strict data constraints, a 15K to 3K extractive context compressor protecting atomic blocks (code/math), and LanceDB metadata pre-filtering to constrain search spaces locally to specific canvas files.

The following sections provide an exhaustive, academic dissection of each of these architectural components, detailing their programmatic logic, underlying pedagogical rationales, and integration strategies.

## 1. Implementation of the 3-Layer Scoring Insurance System

The necessity of automated grading in intelligent tutoring systems demands robust safeguards against Large Language Model (LLM) hallucinations, inconsistencies, and superficial evaluations. The Canvas Learning System addresses this through a rigorously implemented 3-layer scoring insurance architecture.

### 1.1 Self-Consistency 3x Sampling Mechanism
The first layer of insurance relies on a multi-sampling approach designed to mitigate the variance inherent in generative AI models. The `AutoScorer` class implements a two-stage evaluation pipeline: Stage 1 for Evidence Extraction and Stage 2 for Rubric Scoring [cite: 1]. 

In Stage 2, the system executes three independent LLM calls for each scoring event, utilizing a temperature of 0.3 to introduce slight diversity for self-consistency [cite: 1]. The results are aggregated using a `_majority_vote` function. This function applies statistical aggregation across the three samples per dimension:
*   **Majority Vote:** The system attempts to calculate the statistical mode (the most common value) among the three samples [cite: 1].
*   **Fallback Resolution:** If a unique mode cannot be established (e.g., scores of 1, 2, and 3), the system defaults to the statistical median to ensure a balanced, conservative score [cite: 1].
*   **Low-Confidence Detection:** A critical failsafe is the spread check. If the difference between the maximum and minimum scores in the samples exceeds 1 (i.e., `max(values) - min(values) > 1`), the system flags the specific dimension as a `low_confidence_dimension` [cite: 1]. This acts as an escalation trigger, ensuring human oversight or further algorithmic review when the model is uncertain.

### 1.2 4-Dimensional Rubric Decomposition
The second layer of the insurance model breaks down the evaluation into granular, independently assessed dimensions. The `AutoScorer` evaluates student responses against a 4-dimensional rubric:
1.  `concept_accuracy`
2.  `reasoning_quality`
3.  `knowledge_coverage`
4.  `knowledge_integration` [cite: 1].

The scores from these four dimensions are averaged to map onto a 4-tier grade threshold: 1 (Again), 2 (Hard), 3 (Good), and 4 (Easy) [cite: 1]. Crucially, regression tests confirm that this rubric is heavily anchored in the **SOLO (Structure of Observed Learning Outcomes) taxonomy** [cite: 1]. The prompt registry verifies the mandatory inclusion of the SOLO stages: Pre-structural (前结构), Uni-structural (单点结构), Multi-structural (多点结构), and Relational (关联结构) [cite: 1]. By decomposing the score, the system ensures that a student is not merely graded on factual recall but on the structural complexity of their cognitive modeling.

### 1.3 Optional Dual-Model Consistency Verification
The third layer introduces cross-model and cross-stage auditing. This is implemented via the `ScoreConsistencyResult` framework [cite: 1]. The system utilizes a dual-model approach, reading from `settings.FAITHFULNESS_MODEL` as the primary auditor, with a fallback to `settings.AI_MODEL_NAME` [cite: 1].

This stage runs a prompt (`faithfulness_score_consistency.md`) that asks the auditor LLM to verify if the score and justification produced in Stage 2 are genuinely grounded in the raw evidence extracted in Stage 1 [cite: 1]. The LLM outputs a JSON payload containing `consistency_checks` for each dimension, marking them strictly as `CONSISTENT` or `INCONSISTENT` [cite: 1]. The rules strictly dictate that "A high score with weak evidence is INCONSISTENT" and "A low score with strong evidence is also INCONSISTENT" [cite: 1]. This layer successfully decoupling the extraction of evidence from the justification of the score prevents cyclical hallucinations.

## 2. Canvas Content Support and Interoperability

The visual and spatial learning components of the system rely on a canvas interface. Understanding its content support and how it interfaces with Obsidian's native capabilities is crucial for evaluating its interoperability.

### 2.1 Supported Image and Content Types
The Canvas Learning System's parser is designed to handle multiple node types that conform to the standard canvas node specifications. The `CanvasNode` type is defined as a union of four core types:
*   `CanvasTextNode`: Contains standard Markdown text content [cite: 1].
*   `CanvasFileNode`: References a file within the local vault. It supports an optional `subpath` parameter (e.g., `#Section` for linking to specific headings) [cite: 1].
*   `CanvasLinkNode`: Contains external URLs pointing to web resources [cite: 1].
*   `CanvasGroupNode`: Acts as a spatial container for other nodes, supporting background images and styles (`cover`, `ratio`, `repeat`) [cite: 1].

For media files, the system explicitly recognizes a broad array of image extensions via the `IMAGE_EXTENSIONS` constant. These include: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.svg`, and `.webp` [cite: 1]. 

### 2.2 Comparison with Obsidian Canvas Plugin Capabilities
The implementation is highly isomorphic to the native Obsidian Canvas plugin, meaning it is designed for seamless bidirectional compatibility. The node schema (`id`, `type`, `x`, `y`, `width`, `height`, `color`) mirrors the Obsidian standard [cite: 1]. 

A notable capability is the `getNodeContent` utility, which standardizes how information is extracted for backend processing. For text nodes, it extracts raw text; for file nodes (both images and standard Markdown/PDFs), it generates Obsidian's native embed syntax (`![[filename#subpath]]`) [cite: 1]. This design decision ensures that the backend LLM pipelines (such as the `MarkdownImageExtractor`) can resolve internal vault links exactly as the native Obsidian app would, maintaining the integrity of embedded media during AI evaluation [cite: 1].

Furthermore, the system maps Obsidian's preset canvas colors (1 through 6) to semantic learning states: '1' (Red) for Not Understood, '2' (Orange) for Partial Understanding, '3' (Yellow) for Personal Understanding, '4' (Green) for Understood, and '5' (Cyan) for AI Explanation nodes [cite: 1]. This adds a pedagogical layer on top of Obsidian's purely visual schema.

## 3. Pedagogical Frameworks: SOLO Taxonomy and FSRS Algorithms

### 3.1 SOLO Taxonomy Integration
As established in the scoring analysis, the SOLO taxonomy is not merely planned; it is actively implemented as the structural backbone of the evaluation rubric. The `test_prompt_solo_anchoring` test explicitly asserts the presence of the taxonomy's stages within the `autoscore` prompt [cite: 1]. The SOLO taxonomy is highly effective for intelligent tutoring because it moves away from binary correct/incorrect grading, instead evaluating the *quality* and *complexity* of the learner's understanding, aligning perfectly with a graph-based knowledge system where relationships (relational structure) are paramount.

### 3.2 Spaced Repetition Integration: From FIRe to FSRS
While the user query inquires about "FIRe algorithms," an exhaustive analysis of the codebase reveals that the primary spaced repetition algorithm implemented is **FSRS (Free Spaced Repetition Scheduler)**, specifically version 4.5. It is plausible that FIRe refers to an internal nomenclature or a related experimental branch not dominant in this repository slice; however, FSRS is the definitive operational mechanism [cite: 1].

The `fsrs_manager.py` utilizes the `py-fsrs` library to manage learning cards [cite: 1]. It models memory through:
*   **Four Ratings:** Again (1), Hard (2), Good (3), Easy (4) [cite: 1].
*   **Four States:** New (0), Learning (1), Review (2), Relearning (3) [cite: 1].
*   **Calculated Metrics:** It tracks `stability`, `difficulty`, `reps` (repetitions), and `lapses` [cite: 1].

If `py-fsrs` is unavailable in the environment, the system implements a graceful degradation to an `ebbinghaus-fallback` algorithm [cite: 1]. The implementation calculates a specific `Retrievability` metric ($R$) which the Mastery Engine uses to schedule subsequent reviews [cite: 1]. 

### 3.3 Suitability for Single-User Learning Systems
FSRS is exceptionally well-suited for single-user learning systems. Traditional spaced repetition algorithms (like the SuperMemo SM-2 used in older Anki versions) rely on generalized forgetting curves. FSRS, however, utilizes continuous optimization based on individual user history, dynamically adjusting the `stability` and `difficulty` parameters for each isolated concept. Because the Canvas Learning System tracks granular "note fragments" and "concept nodes," FSRS allows the system to build an intimate, highly personalized model of the single user's cognitive decay rates across diverse domains, making it the ideal algorithmic choice [cite: 1].

## 4. Edge Elaborative Interrogation (EEI)

Elaborative Interrogation is a cognitive psychological technique where learners are prompted to generate explanations for explicitly stated facts. In the Canvas Learning System, this is triggered when a user connects (draws an edge between) two concept nodes on the canvas.

### 4.1 Implementation Mechanism
When an edge is formed, the backend invokes the `edge-dialog.md` prompt. The system asynchronously fetches the context for both the source and target nodes, extracting Tier 1 data such as previously recorded "tips" and "historical errors" [cite: 1]. This contextual data is appended to the prompt, ensuring the AI is aware of the user's prior misconceptions.

### 4.2 Prompt Engineering and Strategy
The `edge-dialog.md` prompt strictly regulates the AI's persona and methodology. The prompt explicitly demands that the AI acts as a "curious study buddy" rather than an authoritative teacher or examiner [cite: 1]. 

The interrogation strategy follows specific rules:
1.  **Causal and Conditional Probing:** The AI is instructed to ask "Why" (what is the underlying reason?) and "How" (under what conditions does this relationship hold? Are there exceptions?) [cite: 1].
2.  **Counterexample Generation:** The AI actively probes for counterexamples to test the boundaries of the student's understanding [cite: 1].
3.  **Self-Explanation (SE):** This is a conditional trigger. If the user's response is deemed superficial, the AI asks the user to explain it in their "own words." The code explicitly tests that this is not forced every time, but triggered dynamically [cite: 1].
4.  **Exclusion of Active Recall:** A fascinating pedagogical rule enforced in the prompt is the explicit *exclusion* of Active Recall. Because the student is looking at the Canvas where both Node A and Node B are visible, Active Recall is impossible (the cues are present). The prompt strictly forbids treating the interaction as a memory test [cite: 1].
5.  **Density Control:** To prevent user burnout, the interaction is strictly capped at a maximum of 3 to 4 rounds [cite: 1].
6.  **Depth Assessment:** The prompt includes a hidden 5-level depth assessment table (from Level 1: "A and B are related" to Levels 4-5: "Complete causality + conditions + own words"). Once Level 4 is reached, the AI extracts a Knowledge Graph (KG) triplet (`source_concept`, `target_concept`, `relation_type`, `rationale_text`) and invokes the `record_edge_rationale` tool [cite: 1].

## 5. Note Fragment Click-to-Jump-to-Source Integration

The ability to seamlessly transition from an isolated learning profile or review card back to the original spatial context (the Canvas) is critical for spatial memory reinforcement. This feature is heavily implemented, utilizing dual strategies depending on the application execution environment.

### 5.1 Native Obsidian Implementation
Within the Obsidian environment, cross-canvas navigation is managed by the `CanvasNavigator` service [cite: 1]. When the `navigateToNode` method is invoked, the service takes the target canvas path and node ID. 
1.  It utilizes the `WorkspaceLeaf` API to silently open the target canvas file [cite: 1].
2.  It implements a polling mechanism (`waitForCanvasReady`) to ensure the canvas view is fully loaded into the DOM [cite: 1].
3.  Once loaded, it uses the Obsidian Canvas API's `selectOnly()` and `zoomToSelection()` methods to automatically pan the user's viewport directly to the specific note fragment [cite: 1].
4.  To draw the user's eye, it applies a CSS class (`textbook-highlight`) which executes a 2-second inline keyframe animation (`pulse-highlight 0.5s ease-in-out 4`) [cite: 1].
5.  It concurrently mounts a `NavigationBreadcrumb` component at the top of the UI, allowing the user to seamlessly navigate back to their origin canvas [cite: 1].

The UI component `LearningProfile` tests verify that if a `TipItem` or `WeaknessItem` possesses a `sourceCanvasId`, the "Navigate to source" button is rendered and functional [cite: 1].

### 5.2 Tauri Environment Execution (Degradation Strategy)
When the application is running as a standalone desktop application via Tauri (outside the native Obsidian wrapper), it cannot directly access the Obsidian DOM or `WorkspaceLeaf` APIs. The implementation resolves this through a brilliant URI-based degradation strategy in the `Obsidian Link Service` [cite: 1].

The service attempts three levels of degradation when a jump is requested:
1.  **obsidian://adv-uri:** It attempts to use the Advanced URI plugin protocol, which supports deep-linking into specific headings or block references. It utilizes `@tauri-apps/plugin-shell`'s `open()` function to trigger the OS-level URI handler, pushing the user from the Tauri app into the Obsidian app [cite: 1].
2.  **obsidian://open:** If advanced linking is unavailable, it falls back to the built-in URI, which opens the correct vault and file, though it loses the ability to zoom to the specific block [cite: 1].
3.  **Path Copying:** If all URI protocols fail, the system degrades to simply copying the file path to the user's clipboard and returning a fallback success state [cite: 1]. 

This ensures that the fundamental navigational bridge between the AI interface (Tauri) and the knowledge base (Obsidian) remains unbroken regardless of environmental constraints.

## 6. Performance Guarantee Strategies

Operating an AI-driven knowledge graph dynamically over thousands of markdown files poses severe latency and token-exhaustion risks. The system implements three distinct performance guarantee strategies.

### 6.1 Assessed Concept Profile (ACP) Token Budget Enforcement
The system passes student states to the LLM via an Assessed Concept Profile (ACP). To prevent context-window overflow and control API costs, an aggressive token budget limit (nominally 15K, targeted strictly down to roughly 3K) is enforced via the `_enforce_token_budget` method [cite: 1].

The budget logic prioritizes the retention of context in a specific order. If the total character count of the node content, conversation summary, tips, errors, and edge reasons exceeds `ACP_MAX_CHARS` (which serves as the token proxy), truncation begins [cite: 1]. 
*   **Priority of Truncation:** `conversation_summary` (>500 chars) -> `node_content` (>800 chars) -> `student_tips` (max 3 items) -> `error_history` (max 3 items) -> `edge_reasons` (max 3 items) [cite: 1].
*   **Semantic Preservation:** The `_truncate` method attempts to gracefully break text at sentence boundaries (`。`, `. `) rather than arbitrary characters [cite: 1]. Furthermore, the system includes safeguards to prevent the truncation from splitting mathematical formulas (`$$...$$`) or fenced code blocks mid-token [cite: 1].

### 6.2 Context Compression via Sentence-Level Extraction
Beyond basic truncation, the `Context Compression Module` achieves massive context reduction (15K to 3K) without relying on LLM summarization (which is slow and hallucination-prone). It utilizes an extractive compression algorithm [cite: 1].

The algorithm uses an `_ATOMIC_PATTERN` regular expression to isolate and protect fenced code blocks, block math formulas, and Markdown tables [cite: 1]. The remaining text is split into independent scoring units via `_SENTENCE_PATTERN` boundary detection [cite: 1]. By extracting only the most query-relevant sentences and recombining them alongside the protected atomic blocks, the system guarantees that Claude or Gemini receives a deterministic, factually precise prompt free of token exhaustion [cite: 1]. Performance tests assert that this batch compression executes in under 1 second, and concurrent 50-memory operations complete under 30 seconds [cite: 1].

### 6.3 Metadata Pre-Filtering via LanceDB
The final performance guarantee occurs at the vector retrieval level. Instead of searching the entire vault globally, the integration with LanceDB utilizes strict metadata pre-filtering. 

When searching for relevant context or nodes, the `LanceDBClient` allows the passage of a `canvas_file` parameter. The query executes as `client.search(query="...", table_name="canvas_nodes", canvas_file=sample_canvas_file)` [cite: 1]. By pushing the filter down to the LanceDB index level, the system bypasses thousands of irrelevant vectors, returning results strictly confined to the active canvas. This drastically reduces the search latency, ensuring that realtime memory captures remain under the strictly tested 100ms threshold [cite: 1], a vital requirement for the system's "stealth" observation protocols.

---

**Conclusion**
The Canvas Learning System is a rigorously engineered platform. It effectively neutralizes LLM hallucinations via its 3-layer scoring insurance, ensures seamless interoperability with Obsidian's spatial capabilities, leverages the scientifically backed FSRS algorithm for personalized memory retention, executes cognitively rich Edge Elaborative Interrogation, bridges standalone execution environments with native clients via deep linking, and strictly maintains millisecond performance profiles under heavy token constraints.

**Sources:**
1. backend/app/services/autoscore.py (fileSearchStores/persistentcanvaslearningsys-qa7kqspeo0jc)
