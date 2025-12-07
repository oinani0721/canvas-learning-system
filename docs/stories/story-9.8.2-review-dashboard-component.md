# Story 9.8.2: Review Dashboard Component - Brownfield Addition

**Epic**: Epic 9 - Frontend Architecture Enhancement
**Story Type**: Brownfield Integration
**Estimated Effort**: 1-2 development sessions
**Priority**: High

---

## User Story

**As a Canvas learner, I want to visualize my Ebbinghaus forgetting curve review tasks and memory analytics through an interactive dashboard, so that I can efficiently manage my daily review sessions and track my long-term learning progress.**

---

## Story Context

This story leverages the existing Ebbinghaus review system commands (`/review`, `/ebbinghaus`, `/memory-stats`) and visualizes their output in a comprehensive frontend dashboard. The Canvas v2.0 system already has a complete backend review infrastructure with:

- **Existing Review Commands**: `/review`, `/ebbinghaus`, `/memory-stats`, `/review-progress`
- **Memory Analytics**: Py-FSRS algorithm integration for spaced repetition scheduling
- **Graphiti Knowledge Graph**: Memory storage and retrieval system
- **Review Session Management**: Complete session tracking and completion logic

This component provides a frontend visualization layer that wraps existing CLI command functionality without modifying the underlying review algorithms or data structures.

---

## Acceptance Criteria

### Functional Requirements

1. **Today's Review Tasks Display**
   - Show all pending review tasks for current day from `/review show` command output
   - Display task priority based on forgetting curve algorithm (urgent, important, normal)
   - Show task metadata: concept name, Canvas source, time since last review, difficulty rating
   - Support task filtering by difficulty, Canvas source, or completion status
   - Enable task selection for immediate review session

2. **Memory Analytics Visualization**
   - Display memory analytics from `/memory-stats` command:
     - Total memory nodes (red, purple, yellow, green counts)
     - Review completion rates (daily, weekly, monthly)
     - Forgetting curve progress visualization
     - Memory retention percentage over time
   - Show learning streak and consistency metrics
   - Display memory strength distribution across different concepts

3. **Interactive Review Session Interface**
   - Start review sessions directly from dashboard using `/review session` integration
   - Show review progress with visual indicators (completed/remaining tasks)
   - Display review quality scoring interface for each task
   - Provide real-time feedback on memory performance
   - Support session pause/resume functionality

4. **Historical Review Progress**
   - Show review history from `/review-progress` command output
   - Display completion rates over time with trend analysis
   - Visualize concept mastery progression through color transitions
   - Show upcoming review schedule with calendar view
   - Display learning efficiency metrics and improvement areas

### Integration Requirements

1. **CLI Command Integration**
   - Wrap existing `/review` CLI commands with frontend interfaces
   - Parse and display `review show`, `review progress`, `memory-stats` command outputs
   - Maintain compatibility with existing CLI command parameters and flags
   - Support all existing review command variants and options

2. **Graphiti Memory System Integration**
   - Connect to existing `mcp__graphiti-memory` MCP services
   - Display memory node statistics from knowledge graph
   - Visualize memory relationships and concept connections
   - Support memory node creation and relationship management through UI

3. **Canvas File System Integration**
   - Link review tasks to source Canvas files from Story 9.8.1
   - Enable direct Canvas loading from review task items
   - Show Canvas-specific review statistics and progress
   - Support batch review operations for Canvas-based concepts

4. **Py-FSRS Algorithm Integration**
   - Display scheduling data from Py-FSRS spaced repetition algorithm
   - Show next review intervals and difficulty adjustments
   - Visualize forgetting curve predictions and memory decay
   - Support manual difficulty adjustment through UI controls

### Quality Requirements

1. **Performance**:
   - Dashboard should load within 2 seconds with up to 100 review tasks
   - Real-time updates should reflect within 500ms of command execution
   - Memory analytics calculations should complete within 3 seconds

2. **Usability**:
   - Responsive interface with clear visual hierarchy
   - Intuitive task prioritization and filtering
   - Accessible color coding following Canvas color system standards
   - Mobile-friendly interface for on-the-go reviewing

3. **Data Accuracy**:
   - Review task data must exactly match CLI command outputs
   - Memory analytics should reflect real-time Graphiti knowledge graph state
   - Review progress tracking must maintain 100% data consistency with backend

---

## Technical Notes

### Implementation Approach

1. **Frontend Framework**: Use existing web stack with minimal additional dependencies
2. **Backend Integration**: Create wrapper functions that call existing CLI commands and parse outputs
3. **Data Visualization**: Use lightweight charting libraries for memory analytics visualization
4. **Real-time Updates**: Implement WebSocket or polling mechanism for live dashboard updates

### Existing Patterns to Follow

1. **CLI Command Wrapping Pattern**:
   ```python
   # Follow existing CLI command execution pattern
   def execute_review_command(command, args=None):
       """Execute review CLI command and return parsed output"""
       full_command = f"/review {command}"
       if args:
           full_command += f" {args}"

       # Use existing command execution infrastructure
       result = SlashCommand(command=full_command)
       return parse_review_output(result)

   def parse_review_output(output):
       """Parse CLI output into structured data for frontend"""
       # Follow existing output parsing patterns
       return {
           'tasks': extract_tasks(output),
           'analytics': extract_analytics(output),
           'progress': extract_progress(output)
       }
   ```

2. **Memory System Integration Pattern**:
   ```python
   # Use existing Graphiti memory service pattern
   def get_memory_analytics():
       """Get memory statistics from Graphiti knowledge graph"""
       memories = mcp__graphiti-memory__list_memories()
       return {
           'total_count': len(memories),
           'color_distribution': count_by_color(memories),
           'retention_rate': calculate_retention(memories)
       }
   ```

3. **Review Session Management Pattern**:
   ```python
   # Follow existing review session logic
   def start_review_session(task_ids):
       """Start review session for selected tasks"""
       for task_id in task_ids:
           # Use existing review task processing logic
           result = process_review_task(task_id)
           update_dashboard_progress(result)
       return session_summary
   ```

### Integration Points

1. **Existing Review Commands**:
   - `/review show` - Display today's review tasks
   - `/review session` - Start interactive review session
   - `/review progress` - Show historical review completion
   - `/memory-stats` - Display memory analytics and statistics
   - `/ebbinghaus` - Show forgetting curve and review schedule

2. **Graphiti Knowledge Graph**:
   - `mcp__graphiti-memory__list_memories()` - Get all memory nodes
   - `mcp__graphiti-memory__search_memories()` - Search specific concepts
   - `mcp__graphiti-memory__add_memory()` - Add new memory nodes
   - Memory relationship management and visualization

3. **Canvas System Integration**:
   - Connect with Canvas file selector from Story 9.8.1
   - Link review tasks to source Canvas files
   - Display Canvas-specific review progress and statistics
   - Support direct Canvas loading from review dashboard

4. **Py-FSRS Algorithm**:
   - Access scheduling data for review task prioritization
   - Display next review intervals and difficulty progressions
   - Visualize memory strength and forgetting curve predictions
   - Support manual difficulty adjustments through UI

---

## Definition of Done

### Functional Completion

- ✅ Dashboard displays today's review tasks with accurate priority and metadata
- ✅ Memory analytics visualization shows real-time Graphiti knowledge graph statistics
- ✅ Interactive review sessions can be started and managed through dashboard
- ✅ Historical review progress displays accurate completion rates and trends
- ✅ Task filtering and sorting functionality works seamlessly
- ✅ Real-time dashboard updates reflect command execution results

### Integration Completion

- ✅ All `/review` CLI commands successfully wrapped with frontend interfaces
- ✅ Graphiti memory system integration provides accurate memory statistics
- ✅ Canvas file system integration links review tasks to source files
- ✅ Py-FSRS algorithm data properly visualized in scheduling and analytics
- ✅ No modifications to existing backend review logic or data structures

### Quality Completion

- ✅ Performance requirements met (2s dashboard load, 500ms real-time updates)
- ✅ Responsive design works on desktop, tablet, and mobile viewports
- ✅ Data accuracy verified against CLI command outputs
- ✅ Accessibility standards met for color contrast and keyboard navigation
- ✅ Error handling covers command failures and service unavailable scenarios

### Documentation Completion

- ✅ API documentation for review dashboard utility functions
- ✅ Integration guide for connecting with CLI commands and memory systems
- ✅ User guide for dashboard features and review session management
- ✅ Technical notes updated with implementation details and patterns

### Acceptance Testing

- ✅ Dashboard functionality tested with real review tasks from Canvas system
- ✅ Memory analytics accuracy verified against Graphiti knowledge graph
- ✅ Review session workflow tested end-to-end with Canvas file integration
- ✅ Performance testing with 100+ review tasks and complex memory graphs
- ✅ Cross-browser and device compatibility testing completed

**Success Criteria**: Users can efficiently manage their daily review sessions through an intuitive dashboard that accurately visualizes their Ebbinghaus review tasks, memory analytics, and learning progress, with all functionality seamlessly integrated with existing Canvas v2.0 backend systems.

---

## Dependencies

### Must-Have Dependencies
- Existing `/review` CLI command system and review session logic
- Graphiti knowledge graph memory services (`mcp__graphiti-memory`)
- Py-FSRS algorithm integration for spaced repetition scheduling
- Canvas file system integration (Story 9.8.1)

### External Dependencies
- Chart visualization library (e.g., Chart.js or similar lightweight library)
- WebSocket or polling library for real-time updates

### Successor Stories
- Story 9.8.5: Advanced Review Analytics (extends dashboard visualization)
- Story 9.8.6: Mobile Review Interface (extends mobile compatibility)

---

**Story Created**: 2025-10-26
**Acceptance Criteria Finalized**: 2025-10-26
**Technical Review**: Ready for development implementation
