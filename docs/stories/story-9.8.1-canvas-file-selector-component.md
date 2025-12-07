# Story 9.8.1: Canvas File Selector Component - Brownfield Addition

**Epic**: Epic 9 - Frontend Architecture Enhancement
**Story Type**: Brownfield Integration
**Estimated Effort**: 1-2 development sessions
**Priority**: High

---

## User Story

**As a Canvas user, I want to browse, select, and load local .canvas files through an intuitive file selector interface, so that I can easily manage and access my learning canvases without manually navigating through file directories.**

---

## Story Context

This story builds upon the existing Canvas v2.0 file management capabilities in `canvas_utils.py`. The system currently supports programmatic Canvas file operations, but lacks a user-friendly frontend interface for file browsing and selection. This component will integrate with:

- **Existing Backend**: `canvas_utils.py` Canvas file parsing and management
- **File System**: Local .canvas file storage in `笔记库/` directory structure
- **Canvas Management**: Integration with Canvas JSON operators from Layer 1 architecture

The component provides a frontend wrapper around existing backend functionality without modifying core file operations logic.

---

## Acceptance Criteria

### Functional Requirements

1. **File Browsing Interface**
   - Display a browsable directory tree showing all .canvas files in the `笔记库/` directory
   - Show subdirectory structure (e.g., `离散数学/`, `线性代数/`, `数学分析/`)
   - Display file metadata: name, modification date, file size, and node count
   - Support search/filter functionality by file name or directory

2. **File Selection and Loading**
   - Allow users to click and select a .canvas file from the browser
   - Display a preview panel showing basic canvas information:
     - Canvas title (if available in first node)
     - Total number of nodes by color (red, green, purple, yellow, blue)
     - Last modification timestamp
     - Brief content summary (first 3 nodes titles)
   - Provide "Load Canvas" button to open selected file for further operations

3. **Canvas File Operations**
   - Support loading selected canvas file using existing `canvas_utils.py` functions
   - Validate file format and display appropriate error messages for invalid files
   - Support selecting multiple files for batch operations (integration with Story 9.8.2)

### Integration Requirements

1. **Backend Integration**
   - Use existing `CanvasJSONOperator.read_canvas()` method for file reading
   - Utilize `find_nodes_by_color()` functions for metadata extraction
   - Integrate with existing file path handling and error management
   - Maintain compatibility with current Canvas file format

2. **Data Flow Integration**
   - Load canvas data into existing Canvas data structures
   - Pass selected canvas information to other frontend components
   - Support real-time file system updates when new files are created

3. **Error Handling Integration**
   - Reuse existing Canvas file validation logic
   - Display user-friendly error messages for corrupted/invalid files
   - Handle file system permissions and access issues gracefully

### Quality Requirements

1. **Performance**:
   - File listing should populate within 1 second for up to 100 canvas files
   - Preview generation should complete within 2 seconds per file

2. **Usability**:
   - Responsive interface that works on desktop and tablet viewports
   - Clear visual feedback for file selection state
   - Accessible navigation with keyboard support

3. **Compatibility**:
   - Support all existing Canvas file formats from v1.0 and v2.0
   - Maintain backward compatibility with current Canvas JSON structure

---

## Technical Notes

### Implementation Approach

1. **Frontend Framework**: Use lightweight HTML/JavaScript with minimal dependencies
2. **Backend API**: Create wrapper functions in `canvas_utils.py` for frontend consumption
3. **File System Access**: Use Python's `os` and `glob` modules with proper error handling
4. **Data Parsing**: Leverage existing `CanvasJSONOperator` class for Canvas file operations

### Existing Patterns to Follow

1. **Canvas File Structure**:
   ```python
   # Use existing Canvas reading pattern
   from canvas_utils import CanvasJSONOperator

   def get_canvas_metadata(filepath):
       operator = CanvasJSONOperator()
       canvas_data = operator.read_canvas(filepath)
       return {
           'node_count': len(canvas_data.get('nodes', [])),
           'colors': {color: len(find_nodes_by_color(canvas_data, color))
                    for color in ['1', '2', '3', '5', '6']},
           'last_modified': os.path.getmtime(filepath)
       }
   ```

2. **Error Handling Pattern**:
   ```python
   # Follow existing Canvas error handling
   try:
       canvas_data = operator.read_canvas(filepath)
       if not canvas_data or 'nodes' not in canvas_data:
           raise ValueError("Invalid Canvas file format")
   except Exception as e:
       logger.error(f"Canvas file loading error: {str(e)}")
       return {'error': f'Failed to load canvas: {str(e)}'}
   ```

3. **File Path Management**:
   ```python
   # Use existing path resolution pattern
   CANVAS_BASE_DIR = os.path.join(os.getcwd(), "笔记库")

   def get_canvas_files(directory=CANVAS_BASE_DIR):
       """Get all .canvas files recursively from base directory"""
       canvas_files = []
       for root, dirs, files in os.walk(directory):
           for file in files:
               if file.endswith('.canvas'):
                   canvas_files.append({
                       'path': os.path.join(root, file),
                       'relative_path': os.path.relpath(os.path.join(root, file), directory),
                       'name': file.replace('.canvas', '')
                   })
       return canvas_files
   ```

### Integration Points

1. **Canvas Utils Integration**:
   - Extend `canvas_utils.py` with frontend-specific utility functions
   - Use existing `CanvasJSONOperator` and `CanvasBusinessLogic` classes
   - Maintain current error handling and logging patterns

2. **File System Integration**:
   - Work within existing `笔记库/` directory structure
   - Respect current file naming conventions
   - Support existing subdirectory organization

3. **Data Structure Compatibility**:
   - Use existing Canvas node and edge data structures
   - Maintain current color coding system
   - Support existing metadata formats

---

## Definition of Done

### Functional Completion

- ✅ File browser displays all .canvas files in `笔记库/` directory tree
- ✅ File preview panel shows accurate metadata (node counts, colors, modification date)
- ✅ File selection functionality works with visual feedback
- ✅ Canvas loading successfully integrates with existing `canvas_utils.py`
- ✅ Error handling covers invalid files, permission issues, and malformed Canvas files
- ✅ Search/filter functionality works for file names and directories

### Integration Completion

- ✅ All file operations use existing Canvas backend functions
- ✅ No modifications to core Canvas file format or business logic
- ✅ Successful integration with existing `CanvasJSONOperator` class
- ✅ Compatible with current Canvas JSON structure and node formats
- ✅ Error messages align with existing Canvas error handling patterns

### Quality Completion

- ✅ Performance requirements met (1s file listing, 2s preview generation)
- ✅ Responsive design works on desktop and tablet viewports
- ✅ Keyboard navigation support implemented
- ✅ All existing Canvas file formats (v1.0, v2.0) supported
- ✅ Unit tests covering file selection, preview generation, and error scenarios
- ✅ Manual testing with sample Canvas files from `笔记库/` directory

### Documentation Completion

- ✅ API documentation for new frontend utility functions
- ✅ Integration guide for connecting with other frontend components
- ✅ User guide for file selector interface usage
- ✅ Technical notes section updated with implementation details

### Acceptance Testing

- ✅ User acceptance testing with real Canvas files from `笔记库/`
- ✅ Performance testing with 50+ Canvas files
- ✅ Error scenario testing (corrupted files, permission issues)
- ✅ Cross-browser compatibility testing
- ✅ Mobile/tablet responsiveness testing

**Success Criteria**: Users can successfully browse, preview, and load any Canvas file from the `笔记库/` directory structure using an intuitive interface, with all operations backed by existing Canvas v2.0 backend functionality.

---

## Dependencies

### Must-Have Dependencies
- Existing `canvas_utils.py` Canvas file management functions
- Current `CanvasJSONOperator` and `CanvasBusinessLogic` classes
- Existing Canvas file structure in `笔记库/` directory

### External Dependencies
- None (uses only existing system dependencies)

### Successor Stories
- Story 9.8.2: Canvas Batch Manager Component (depends on file selection)
- Story 9.8.3: Canvas File Preview Enhancement (extends preview functionality)

---

**Story Created**: 2025-10-26
**Acceptance Criteria Finalized**: 2025-10-26
**Technical Review**: Ready for development implementation
