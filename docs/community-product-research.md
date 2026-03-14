# Community Product Research: Node + Conversation + Knowledge Graph Pattern

**Date**: 2026-03-11
**Focus**: Concrete UX patterns and interaction designs for canvas-based learning tools

---

## Structured Comparison Table

| Feature | Heptabase | Scrintal | Logseq Whiteboards | Napkin.ai | RemNote | Muse | Kosmik | tldraw | Excalidraw |
|---|---|---|---|---|---|---|---|---|---|
| **Node/Card Canvas** | Yes - cards on infinite whiteboards | Yes - documents on infinite canvas | Yes - blocks on freeform whiteboard | Partial - text-to-visual, not card-centric | Partial - knowledge graph view, no spatial canvas editor | Yes - nested spatial boards | Yes - infinite canvas with mixed media | Yes - SDK for infinite canvas apps | Yes - infinite drawing canvas |
| **AI Chat Per Node** | Yes - hover card -> AI action; sidebar chat with card context | Yes - select doc -> send to AI; drag response to canvas | No native; plugin-based (e.g., GraphThulhu MCP) | No per-node chat; global text-to-visual AI | Yes - "Ask AI" queries knowledge base; AI flashcard generation | No AI features | Partial - AI auto-tags content, no per-node conversation | No native AI; extensible via SDK | Partial - text-to-diagram AI, not per-node chat |
| **Learning Relationships** | Visual arrows (non-, uni-, bi-directional); AI suggests related cards | Bi-directional links shown as visual lines; graph algorithm ranks connectivity | Bi-directional links + graph view; page references | AI resurfaces related old thoughts; auto-connects ideas | Hierarchical nesting = implicit links; backlinks; knowledge graph view | Linked references across boards; excerpts keep source context | AI auto-tag clusters; connector system for visual links | Arrows + bindings between shapes; workflow kit for node-wire graphs | Arrows with optional bindings between elements |
| **User Restructures Relationships** | Yes - drag cards, redraw arrows, multi-whiteboard placement | Yes - manual or algorithmic graph layout; nest boards/cards | Yes - drag blocks on whiteboard; restructure outline | Limited - rearrange generated visuals | Yes - reparent Rems; restructure hierarchy | Yes - drag anything; nested boards | Yes - drag-drop; connector system | Yes - full programmatic + manual control | Yes - manual drawing/connecting |
| **Data Model** | Cards in shared Card Library; whiteboards store spatial metadata (position, color, arrows); cards referenced not owned by whiteboards | Documents on canvas with bi-directional links; graph algorithm for layout; proprietary cloud storage | Markdown/Org-mode files (or DB graph in beta); blocks are atomic units; whiteboard stores spatial layout per block | Text -> AI-generated visuals (diagrams, flowcharts); no persistent node graph model | Rems (hierarchical tree); each Rem can become flashcard; bi-directional links via backlinks; knowledge graph derived from hierarchy | Nested boards (board-in-board); linked cards as references; local-first sync (CRDTs); stored on device | Infinite canvas with mixed media items; AI auto-tags as metadata; connectors between items; cloud storage | TLShape records in reactive Store; JSON objects with props; @tldraw/tlschema defines types; arrows use bindings system | JSON array of elements; each has type/id/x/y/width/height; arrows have fromNode/toNode bindings; .excalidraw files |
| **UX: Click Node ->** | Click card -> expands inline on whiteboard; or opens in **right side panel**; AI chat in right sidebar | Click document -> opens as **full-screen editor** or inline block; AI in floating panel | Click block on whiteboard -> opens as **inline editor**; sidebar for references | Click visual -> edit text source; no node-level interaction | Click Rem -> opens in **main editor pane**; sidebar for backlinks/graph | Tap card -> **zooms into nested board** (spatial zoom) | Click item -> **inline editing** on canvas | Click shape -> **selection handles** + property panel | Click element -> **selection handles** + top toolbar |
| **Open Source** | No (proprietary) | No (proprietary) | Yes (AGPL) | No (proprietary) | No (proprietary) | No (proprietary) | No (proprietary) | Yes (tldraw license) | Yes (MIT) |
| **Learning Progression** | No explicit tracking | No explicit tracking | Flashcard SRS via plugin | No | Yes - spaced repetition (SM-2 / FSRS); tracks review intervals | No | No | No (SDK, build your own) | No |

---

## Detailed Per-Product Findings

### 1. Heptabase

**Architecture**: All cards live in a shared Card Library. Whiteboards do not own cards -- they store only spatial metadata (x/y position, shape, color, arrow connections). The same card can appear on multiple whiteboards simultaneously as references. This separation of content from layout is a key architectural insight.

**AI Interaction Pattern (2025)**:
- Hover any card on whiteboard -> pick an AI action (translate, summarize, mind-map)
- Custom AI actions can be saved and reused
- Right sidebar chat: select cards or whiteboard sections as context -> ask AI questions
- AI can search entire knowledge base (keyword + semantic search) and cite specific cards
- Multi-select whiteboard objects to add as chat context or start new chat
- AI suggests related cards via Card Library filter

**UX Pattern**: Card click -> expands inline on whiteboard OR opens in right side panel. AI chat lives in right sidebar. Cards are the atomic unit; whiteboards are spatial views.

**Data Storage**: Local database on device; optional AWS sync with AES-256 encryption.

**Key Insight**: The "cards as shared references, whiteboards as spatial views" model is the closest existing pattern to a node+conversation+graph system.

Sources:
- [Heptabase User Interface Logic](https://wiki.heptabase.com/user-interface-logic)
- [Heptabase Fundamental Elements](https://wiki.heptabase.com/fundamental-elements)
- [Heptabase AI Actions Newsletter](https://wiki.heptabase.com/newsletters/2025-12-30)
- [Heptabase AI Related Cards Newsletter](https://wiki.heptabase.com/newsletters/2025-11-06)

---

### 2. Scrintal

**Architecture**: Documents live on an infinite canvas with bi-directional links shown as visual lines. Supports nesting boards, cards, and weblinks. Graph algorithm can auto-organize layout by connectivity (most-linked element centered).

**AI Interaction Pattern**:
- Select any document or block -> send to AI for summarization/rewriting
- Send prompts to AI -> drag-and-drop responses onto canvas
- AI Research Assistant for enhanced note-taking
- AI acts as creative partner for brainstorming

**UX Pattern**: Documents can display as blocks, full-screen editor (for focus), or title-only (for overview). Click document -> opens inline or full-screen. Visual links between documents are always visible on canvas.

**Key Insight**: The "Organize" feature that activates a graph algorithm to auto-layout by connectivity is a useful UX pattern. Users can toggle between manual layout and algorithmic arrangement.

Sources:
- [Scrintal Knowledge Graph](https://scrintal.com/features/knowledge-graph)
- [Scrintal vs Heptabase](https://scrintal.com/comparisons/heptabase-alternative)
- [Scrintal Development Journey](https://blog.scrintal.com/how-we-developed-our-visual-knowledge-base-scrintal-update-2022-2023-1ed7efc31360)

---

### 3. Logseq Whiteboards

**Architecture**: Block-based outliner with Markdown/Org-mode files (or database graph in beta). Whiteboards add a freeform canvas layer where blocks can be placed spatially. Bidirectional links create an underlying knowledge graph visible in a dedicated graph view.

**AI Interaction Pattern**: No native AI. Third-party plugins like GraphThulhu MCP server provide AI access to the knowledge graph (37 tools for navigation, search, analysis, writing, flashcards, whiteboards).

**UX Pattern**: Click block on whiteboard -> inline editor. Separate graph view shows the full knowledge network. Whiteboard is limited compared to dedicated canvas tools (less flexible with visual links, media display).

**Data Model**: Blocks are atomic units stored in files. Whiteboard stores spatial layout per block. DB graph (beta) adds reliability and collaboration features.

**Key Insight**: The open-source nature and plugin ecosystem make it extensible, but the whiteboard feature is secondary to the outliner core.

Sources:
- [Logseq Official](https://logseq.com/)
- [Logseq Knowledge Graphs with DB Power](https://volodymyrpavlyshyn.medium.com/logseq-personal-knowledge-graphs-with-db-power-85687d17cc4a)
- [GraphThulhu MCP Server](https://github.com/skridlevsky/graphthulhu)

---

### 4. Napkin.ai

**Architecture**: NOT a node/card canvas tool. It's a text-to-visual generator. Users write text, AI generates diagrams, flowcharts, infographics, and mind maps from that text. No persistent node graph or knowledge model.

**AI Interaction Pattern**: Global AI -- paste text -> click spark icon -> AI generates visual options. Custom generation lets users specify visual types. AI resurfaces related old thoughts automatically. No per-node conversation.

**UX Pattern**: Write text -> AI generates visuals alongside. Click visual to edit. Team collaboration via shared "Teamspace" with real-time co-editing. 5M+ registered users as of Aug 2025.

**Key Insight**: The "smart idea resurfacing" feature (AI shows related past thoughts based on current thinking) is a relevant pattern for learning systems, even though Napkin itself is not a graph tool.

Sources:
- [Napkin AI Review 2025](https://aitoolinsight.com/napkin-ai-review/)
- [Napkin AI Official](https://www.napkin.ai/)

---

### 5. RemNote

**Architecture**: Hierarchical tree of "Rems" (atomic knowledge units). Each Rem can become a flashcard. Nesting creates implicit parent-child relationships. Backlinks create cross-cutting connections. Knowledge graph view visualizes all Rems and connections.

**AI Interaction Pattern**:
- "Ask AI" - conversational interface to query your entire knowledge base in natural language
- AI auto-generates flashcards from notes, PDFs, lecture transcripts
- AI retrieves relevant information and synthesizes across documents

**UX Pattern**: Click Rem -> opens in main editor pane. Sidebar shows backlinks and graph view. No spatial canvas -- primarily an outliner with graph visualization.

**Learning Progression**: The strongest learning-specific tool in this list. Uses SM-2 (Anki default) or FSRS algorithm for spaced repetition. Tracks review intervals and retention levels. FSRS reduces reviews by 20-30% vs SM-2 while maintaining retention.

**Key Insight**: The only product here with real learning progression tracking (spaced repetition). However, it lacks a spatial canvas -- knowledge is organized hierarchically, not spatially.

Sources:
- [RemNote Knowledge Graph](https://help.remnote.com/en/articles/8771354-knowledge-graph)
- [RemNote Official](https://www.remnote.com/)
- [RemNote Spaced Repetition](https://help.remnote.com/en/articles/9337171-understanding-spaced-repetition)

---

### 6. Muse

**Architecture**: Nested spatial boards (board-in-board-in-board). Content types: text blocks, handwritten scribbles, images, PDFs, web links, files. Linked cards reference boards from multiple places. Excerpts remix parts of PDFs/images while keeping source context.

**Status**: Leadership transition in 2024 (Adam Wiggins -> Adam Wulf). Still active, Muse 3 beta with live collaboration.

**AI Interaction Pattern**: No AI features.

**UX Pattern**: Tap card -> **spatial zoom into nested board** (the signature UX). This "zoom-in" interaction is unique -- you don't open a sidebar or modal, you navigate spatially into deeper layers. Local-first sync across iPad/Mac using CRDTs.

**Key Insight**: The nested-board spatial zoom is a powerful UX metaphor for "drilling into" a concept. No AI or learning features, but the spatial navigation pattern is highly relevant.

Sources:
- [Muse Official](https://museapp.com/)
- [Muse Retrospective](https://adamwiggins.com/muse-retrospective/)

---

### 7. Kosmik

**Architecture**: Infinite canvas with mixed media (text, images, videos, PDFs, web links). AI auto-tags content by colors, themes, subjects, visual elements. Connector system creates visual links between items.

**AI Interaction Pattern**: AI auto-tagging (July-Aug 2025) automatically categorizes content. AI finds similar images from web when you drop an image. AI universe creation generates workspaces from text prompts. AI web browser preview announced. No per-node conversational AI.

**UX Pattern**: Click item -> inline editing on canvas. Built-in browser and PDF reader (unique). Real-time collaboration.

**Key Insight**: The "AI universe creation" (generate entire workspace from text prompt) is an interesting onboarding pattern. Auto-tagging provides passive organization.

Sources:
- [Kosmik Official](https://www.kosmik.app/)
- [Kosmik AI Web Browser Preview](https://www.kosmik.app/blog/get-a-sneak-peek-at-kosmik-ai-web-browser)
- [Kosmik on TechCrunch](https://techcrunch.com/2023/12/21/meet-kosmik-a-visual-canvas-with-an-in-built-pdf-reader-and-a-web-browser/)

---

### 8. tldraw

**Architecture**: Open-source infinite canvas SDK (React/TypeScript, ~44k GitHub stars). TLShape is the base type for all shapes stored as JSON objects in a reactive Store. Shapes have props (geometric) and styles (visual). Arrows use a bindings system to connect shapes.

**Data Model**:
- `@tldraw/tlschema` defines record types (TLShape subtypes: arrow, geo, text, note, etc.)
- Store is reactive with atoms -- record queries auto-update on data change
- History tracking and change notifications built-in
- Schema validation and migrations supported

**SDK Capabilities**: The Workflow Starter Kit provides node-and-wire architecture (modeled after React Flow): node shapes, connection shapes, port-based bindings, graph execution engine, data flow between nodes. SDK 4.0 (2025) includes five starter kits.

**Key Insight**: As an SDK, tldraw is the most relevant for *building* a custom canvas learning system. The workflow kit's node-wire architecture directly maps to a "concept node + relationship edge" model. The reactive Store with history tracking could support conversation history per node.

Sources:
- [tldraw SDK](https://tldraw.dev/)
- [tldraw Shapes Documentation](https://tldraw.dev/docs/shapes)
- [tldraw Workflow Starter Kit](https://tldraw.dev/starter-kits/workflow)
- [tldraw GitHub](https://github.com/tldraw/tldraw)

---

### 9. Excalidraw

**Architecture**: Open-source drawing canvas (MIT license). Elements stored as JSON array in `.excalidraw` files. Each element has type, id, x, y, width, height, plus type-specific properties. Arrows have fromNode/toNode bindings for connections.

**Data Model**:
```json
{
  "type": "excalidraw",
  "version": 2,
  "elements": [
    { "type": "rectangle", "id": "...", "x": 0, "y": 0, ... },
    { "type": "arrow", "id": "...", "startBinding": {...}, "endBinding": {...}, ... }
  ],
  "appState": { ... },
  "files": { ... }
}
```
Elements render in array order. Arrows connect via binding references.

**AI Interaction Pattern**: AI text-to-diagram and wireframe-to-code (100 requests/day on Plus plan). MCP server ecosystem for AI integration. No per-node conversation.

**UX Pattern**: Click element -> selection handles + top toolbar. No sidebar or context panel for content. Focused on drawing, not knowledge management.

**Key Insight**: Simple, well-documented JSON format. Good for export/import interoperability but too drawing-focused for a learning system without significant extension.

Sources:
- [Excalidraw JSON Schema](https://docs.excalidraw.com/docs/codebase/json-schema)
- [Excalidraw Official](https://plus.excalidraw.com/)
- [Excalidraw GitHub](https://github.com/excalidraw/excalidraw)

---

## Emerging "AI Canvas + Conversation + Graph" Tools

These tools specifically combine infinite canvas with per-node AI conversations:

### Flowith

The closest existing product to a "conversational knowledge graph canvas."

- **Canvas**: Infinite 2D canvas where every AI conversation becomes a visual node
- **Per-Node Chat**: Yes -- each node is a conversation that can branch, merge, rearrange
- **Knowledge Graph**: "Knowledge Garden" atomizes documents into "Seeds" (discrete knowledge units); semantic connections between Seeds
- **Data Model**: Seeds are atomic knowledge units; AI draws from relevant Seeds via semantic search (not hallucinating)
- **Multi-Model**: 40+ AI models (GPT-5, Claude, DeepSeek); switch mid-conversation without losing context
- **Agent Neo**: Autonomous agent with 10M token context window, 1000+ inference steps, cloud-based async processing
- **UX Pattern**: Click node -> expands conversation inline on canvas; branch off into new nodes; compare side-by-side
- **Learning Progression**: No explicit tracking
- **Pricing**: Professional $14.92/mo (yearly); Ultimate $29.94/mo (yearly)

Sources:
- [Flowith Official Docs](https://doc.flowith.io)
- [Flowith Canvas Mode](https://skywork.ai/blog/ai-agent/function/flowith-os-canvas-mode-explained/)
- [Flowith Agent Neo](https://flowith.io/blog/meet-agent-neo/)

### RabbitHoles AI

- **Canvas**: Infinite canvas for branching AI conversations
- **Per-Node Chat**: Yes -- each node is a conversation with its own model/settings; branch into multiple paths
- **Knowledge Graph**: Attach PDFs, websites, images, YouTube, spreadsheets to canvas; link to chat nodes
- **Multi-Model**: OpenAI, Anthropic, Google, Perplexity, Ollama, custom LLMs; per-node model/temperature settings
- **RAG Mode**: Handles large files and many connected nodes exceeding context limits
- **Storage**: All local (privacy-first); export as JSON or Markdown
- **UX Pattern**: Click node -> opens conversation; branch creates new connected node; voice input supported
- **Unique**: Token count estimation per node; Persona Prompts Library for saved system prompts
- **Learning Progression**: No explicit tracking

Sources:
- [RabbitHoles AI Docs](https://www.rabbitholes.ai/docs)
- [RabbitHoles AI Review](https://siteefy.com/ai-tools/rabbitholes-ai/)

### Project Nodal

- **Canvas**: Local-first infinite canvas (IndexedDB in browser)
- **Per-Node Chat**: Yes -- spin off messages into new Notes; 5 simultaneous AI conversations
- **Spatial Context**: Context is spatial (not just last N messages); "Zones" for logical grouping
- **Storage**: IndexedDB; connect OpenAI key or local Ollama
- **UX Pattern**: Drag viewport, zoom in/out; create Zones; spin off conversation branches
- **Status**: Open source (GitHub: yibie/project-nodal); early stage

Sources:
- [Project Nodal GitHub](https://github.com/yibie/project-nodal)

### Knowing

- **Knowledge Model**: Based on Conceptual Spaces theory (Peter Gardenfors); geometric space with quality dimensions
- **Graph Features**: Dynamic visual layouts with hierarchical node arrangement; AI-enhanced graph expansion
- **AI**: Suggests and organizes connections; transforms fragmented info into multi-layered knowledge network
- **Collaboration**: Shared real-time graph building
- **Learning Focus**: Built on cognitive science principles for learning enhancement
- **Learning Progression**: Not explicitly tracked via SRS, but knowledge structure itself reflects learning depth

Sources:
- [Knowing Blog](https://blog.knowing.app/posts/top-graph-based-knowledge-management-tools-2025/)

---

## Key UX Pattern Summary

| Pattern | Products Using It | Description |
|---|---|---|
| **Right sidebar panel** | Heptabase, RemNote | Click node -> content/AI in right panel; main canvas stays visible |
| **Inline expansion** | Heptabase, Scrintal, Flowith, RabbitHoles | Click node -> expands on canvas; no context switch |
| **Spatial zoom (drill-in)** | Muse | Click node -> zoom into nested board; spatial metaphor for depth |
| **Full-screen editor** | Scrintal | Click node -> full-screen focus mode; canvas hidden |
| **Selection handles + toolbar** | tldraw, Excalidraw | Click shape -> resize/rotate handles; properties in floating bar |
| **Branch-and-explore** | Flowith, RabbitHoles, Project Nodal | Click conversation -> branch into new connected node |
| **Graph algorithm auto-layout** | Scrintal, RemNote | System auto-arranges nodes by connectivity/importance |

---

## Gap Analysis: What No Product Fully Delivers

No existing product combines ALL of the following:

1. **Infinite canvas with concept nodes** (Heptabase, Scrintal, Flowith have this)
2. **Per-node AI conversation history** (Flowith, RabbitHoles have this)
3. **Visual relationship graph between concepts** (Heptabase, Scrintal, Logseq have this)
4. **Learning progression tracking** (only RemNote has SRS)
5. **Knowledge graph as the data backbone** (only Knowing uses cognitive science-based graph model)

The closest combinations:
- **Flowith** = canvas + per-node AI + branching, but no learning tracking, no concept relationship graph
- **Heptabase** = canvas + cards + relationships + AI per card, but no conversation history per node, no learning tracking
- **RemNote** = learning tracking + knowledge graph + AI, but no spatial canvas

**This represents a clear product opportunity**: a system that merges Heptabase's card-reference architecture, Flowith's per-node conversation model, RemNote's spaced repetition, and a persistent knowledge graph backbone.

---

## Relevant Open Standards

| Standard | Spec | Use Case |
|---|---|---|
| **JSON Canvas** | [jsoncanvas.org](https://jsoncanvas.org/) | Open format for infinite canvas data (nodes + edges); created by Obsidian team |
| **Excalidraw JSON** | `.excalidraw` files | Simple element array with arrow bindings |
| **tldraw TLSchema** | `@tldraw/tlschema` npm | Typed record system with reactive store; migration support |

JSON Canvas is the most relevant open standard -- it already defines nodes (text, file, link, group) and edges (fromNode, toNode, label) in a simple JSON format.
