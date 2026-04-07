## ADDED Requirements

### Requirement: Recommendation Feature Toggle in Settings

The frontend SHALL expose a user-controlled toggle in the Settings panel that enables or disables the concept-relation recommendation feature. The toggle state SHALL persist in `localStorage` under the existing `SETTINGS_KEY` alongside other settings. The default value SHALL be `false` (feature off by default) so that existing users do not experience behavior changes without opting in.

#### Scenario: User enables recommendations from Settings

- **GIVEN** a user with no prior recommendation setting
- **WHEN** the user opens Settings and toggles "概念关联推荐" to on
- **THEN** `localStorage[SETTINGS_KEY]` contains `enableRecommendations: true`
- **AND** the change takes effect without requiring a page reload
- **AND** subsequent canvas activity triggers the recommendation pipeline

#### Scenario: Default state is disabled

- **GIVEN** a fresh install or a user who has never interacted with recommendations
- **WHEN** the Settings panel first renders
- **THEN** the recommendation toggle is in the off position
- **AND** `useRecommendations` hook does not issue any backend request
- **AND** the `RecommendationBar` component is not rendered

### Requirement: Debounced Recommendation Trigger

When recommendations are enabled, the frontend SHALL debounce backend calls by 5 seconds after the most recent node or edge mutation. A backend request SHALL only fire when (1) the toggle is on, (2) a board is selected, (3) the canvas contains at least 5 nodes, and (4) at least one node has no connecting edges. These preconditions SHALL be checked on every dependency change before scheduling the debounced request.

#### Scenario: Debounce cancels on rapid edits

- **GIVEN** recommendations are enabled and the canvas has 10 nodes with 3 unconnected nodes
- **WHEN** the user creates a new node, waits 2 seconds, then creates another node
- **THEN** only one backend request fires, 5 seconds after the second node creation
- **AND** the first scheduled request is cancelled by the second mutation

#### Scenario: Insufficient nodes suppress request

- **GIVEN** recommendations are enabled but the canvas contains only 4 nodes
- **WHEN** the user edits a node title
- **THEN** no backend request is fired
- **AND** the RecommendationBar remains hidden

#### Scenario: All nodes connected suppress request

- **GIVEN** recommendations are enabled and the canvas has 6 nodes
- **AND** every node has at least one CANVAS_EDGE connection
- **WHEN** the user edits a node
- **THEN** no backend request is fired because `_get_unconnected_nodes` returns zero candidates

### Requirement: Recommendation Bar UI

When the backend returns at least one recommendation, the frontend SHALL display a `RecommendationBar` fixed to the bottom of the canvas area. Each recommendation card SHALL show the source and target node titles, a confidence percentage, and a human-readable reason. The bar SHALL offer two actions per card: "接受" (accept, which creates a CANVAS_EDGE via `canvas-store.addEdge`) and "忽略" (dismiss, which removes the card from the current session's view).

#### Scenario: Accept creates edge and removes card

- **GIVEN** the RecommendationBar shows a card for "线性代数 ↔ 矩阵运算" with confidence 82%
- **WHEN** the user clicks "接受连线"
- **THEN** a new edge is created in Dexie via `canvas-store.addEdge(source, target, suggestedLabel)`
- **AND** the edge appears on the canvas via the existing reactive subscription
- **AND** the recommendation card disappears from the bar
- **AND** the sync outbox receives an edge create entry for the new CANVAS_EDGE

#### Scenario: Dismiss removes card without creating edge

- **GIVEN** the RecommendationBar shows a card for "Python ↔ TensorFlow"
- **WHEN** the user clicks "忽略"
- **THEN** no edge is created on the canvas
- **AND** the card disappears from the bar
- **AND** the node pair is added to the in-memory `dismissedPairs` set
- **AND** subsequent backend requests within the same session include the dismissed pair as an exclusion

#### Scenario: Empty recommendations hide the bar entirely

- **GIVEN** the backend returns an empty recommendation list
- **WHEN** the hook receives the response
- **THEN** `RecommendationBar` is not rendered (or renders null)
- **AND** no UI chrome is visible at the bottom of the canvas

### Requirement: Recommendation Backend Pipeline (Two-Layer)

The backend `RecommendationService` SHALL implement a two-layer recommendation engine: (L1) bge-m3 text similarity with a cosine threshold of 0.6, (L2) Neo4j 2-hop neighbor co-occurrence over the `CANVAS_EDGE` relationship. The service SHALL return at most 5 recommendations per request, ordered by a combined confidence score, and SHALL exclude any pair present in the `dismissed_pairs` input. The entire analysis SHALL complete within 5 seconds; on timeout, the service SHALL return an empty list rather than raising an exception.

#### Scenario: Two-layer analysis returns combined candidates

- **GIVEN** a canvas with 10 nodes, of which 4 are unconnected
- **AND** nodes A and B share two 2-hop neighbors through CANVAS_EDGE
- **AND** nodes C and D have text cosine similarity 0.85 via bge-m3
- **WHEN** `generate_recommendations(canvas_id, dismissed_pairs=[])` is called
- **THEN** the response contains at least one recommendation for A↔B (graph_pattern source) and one for C↔D (text_similarity source)
- **AND** each recommendation carries a confidence value in [0, 1]
- **AND** the total count is capped at 5

#### Scenario: Dismissed pairs are filtered out

- **GIVEN** a canvas where nodes A and B are plausible recommendations
- **WHEN** the request includes `dismissed_pairs = [{node_id_a: A, node_id_b: B}]`
- **THEN** the response does not contain any recommendation for the A↔B pair regardless of its raw score

#### Scenario: Analysis timeout returns empty list

- **GIVEN** a canvas where either the L1 or L2 analysis would exceed 5 seconds
- **WHEN** `generate_recommendations` is called
- **THEN** `asyncio.wait_for` raises `TimeoutError` internally
- **AND** the method returns a `RecommendationResponse` with an empty `recommendations` list
- **AND** a warning is logged but no exception propagates to the caller

### Requirement: Session-Level Dismissal State

The frontend SHALL track dismissed recommendation pairs in hook-local state (`useState`) rather than in Dexie or a global store. Dismissal state SHALL persist across re-renders within the same session but SHALL reset on page reload. This is an intentional scope decision for the MVP; persistent dismissal across sessions is out of scope for this change and is tracked as a known limitation.

#### Scenario: Dismissed pair suppresses repeated recommendation in same session

- **GIVEN** a user dismisses the "A ↔ B" recommendation
- **WHEN** the 5s debounce fires again after another canvas edit
- **THEN** the new request includes "A ↔ B" in the `dismissed_pairs` payload
- **AND** the backend filters this pair out of the response

#### Scenario: Page reload clears dismissals

- **GIVEN** a user has dismissed three pairs during a session
- **WHEN** the user reloads the page
- **THEN** the `useRecommendations` hook starts with an empty `dismissedPairs` set
- **AND** previously dismissed pairs may reappear in the next recommendation response
