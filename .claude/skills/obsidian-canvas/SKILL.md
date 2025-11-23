---
name: obsidian-canvas
description: Obsidian Canvas plugin development. Use for building Canvas plugins, working with Canvas API, JSON Canvas format, node manipulation, edge connections, and Canvas-related plugin features.
---

# Obsidian Canvas Plugin Development

Complete guide for building Obsidian plugins that interact with Canvas files.

## When to Use This Skill

This skill should be triggered when you need to:
- Build Obsidian plugins that work with Canvas (.canvas files)
- Understand the JSON Canvas file format specification
- Create, read, update, or delete Canvas nodes programmatically
- Manipulate Canvas edges and connections
- Implement mind mapping or visual diagramming features in Obsidian
- Auto-generate Canvas layouts from data
- Analyze Canvas structure and relationships
- Integrate with Obsidian's Vault API to work with Canvas files

## Quick Reference

### 1. Basic Canvas File Structure

```json
{
  "nodes": [
    {
      "id": "unique-node-id",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 250,
      "height": 60,
      "text": "# Heading\nContent with **markdown**"
    },
    {
      "id": "file-node-id",
      "type": "file",
      "x": 300,
      "y": 0,
      "width": 400,
      "height": 300,
      "file": "path/to/note.md",
      "subpath": "#Section"
    }
  ],
  "edges": [
    {
      "id": "edge-id",
      "fromNode": "unique-node-id",
      "toNode": "file-node-id",
      "fromSide": "right",
      "toSide": "left",
      "toEnd": "arrow"
    }
  ]
}
```

### 2. Reading a Canvas File

```typescript
import { TFile, Plugin } from 'obsidian';

export default class MyCanvasPlugin extends Plugin {
  async onload() {
    this.addCommand({
      id: 'read-canvas',
      name: 'Read Canvas File',
      callback: async () => {
        const file = this.app.workspace.getActiveFile();
        if (file && file.extension === 'canvas') {
          const canvasData = await this.readCanvas(file);
          console.log(`Nodes: ${canvasData.nodes.length}`);
          console.log(`Edges: ${canvasData.edges.length}`);
        }
      }
    });
  }

  async readCanvas(file: TFile) {
    const content = await this.app.vault.read(file);
    return JSON.parse(content);
  }
}
```

### 3. Creating Canvas Nodes

```typescript
// Generate unique ID
function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

// Create text node
function createTextNode(x: number, y: number, text: string) {
  return {
    id: generateId(),
    type: 'text',
    x,
    y,
    width: 250,
    height: 60,
    text
  };
}

// Create file node
function createFileNode(x: number, y: number, filePath: string) {
  return {
    id: generateId(),
    type: 'file',
    x,
    y,
    width: 400,
    height: 300,
    file: filePath
  };
}

// Create link node
function createLinkNode(x: number, y: number, url: string) {
  return {
    id: generateId(),
    type: 'link',
    x,
    y,
    width: 400,
    height: 300,
    url
  };
}

// Create group node
function createGroupNode(x: number, y: number, width: number, height: number, label: string) {
  return {
    id: generateId(),
    type: 'group',
    x,
    y,
    width,
    height,
    label
  };
}
```

### 4. Adding Nodes to Canvas

```typescript
async function addNodesToCanvas(
  app: App,
  canvasFile: TFile,
  newNodes: any[]
): Promise<void> {
  const content = await app.vault.read(canvasFile);
  const canvasData = JSON.parse(content);

  // Add new nodes
  canvasData.nodes.push(...newNodes);

  // Save back to file
  const newContent = JSON.stringify(canvasData, null, 2);
  await app.vault.modify(canvasFile, newContent);
}

// Usage
this.addCommand({
  id: 'add-node',
  name: 'Add Text Node',
  callback: async () => {
    const file = this.app.workspace.getActiveFile();
    if (file && file.extension === 'canvas') {
      const newNode = createTextNode(100, 100, "New idea!");
      await addNodesToCanvas(this.app, file, [newNode]);
    }
  }
});
```

### 5. Creating Edges (Connections)

```typescript
function createEdge(
  fromNodeId: string,
  toNodeId: string,
  options?: {
    fromSide?: 'top' | 'right' | 'bottom' | 'left';
    toSide?: 'top' | 'right' | 'bottom' | 'left';
    toEnd?: 'none' | 'arrow';
    label?: string;
    color?: string;
  }
) {
  return {
    id: generateId(),
    fromNode: fromNodeId,
    toNode: toNodeId,
    fromSide: options?.fromSide,
    toSide: options?.toSide,
    toEnd: options?.toEnd || 'arrow',
    label: options?.label,
    color: options?.color
  };
}

// Connect two nodes
async function connectNodes(
  app: App,
  canvasFile: TFile,
  fromId: string,
  toId: string
): Promise<void> {
  const content = await app.vault.read(canvasFile);
  const canvasData = JSON.parse(content);

  const edge = createEdge(fromId, toId, {
    fromSide: 'right',
    toSide: 'left',
    toEnd: 'arrow'
  });

  canvasData.edges.push(edge);

  const newContent = JSON.stringify(canvasData, null, 2);
  await app.vault.modify(canvasFile, newContent);
}
```

### 6. Canvas Color System

```typescript
// Two color formats supported:

// 1. Preset colors (strings "1" through "6")
const colors = {
  "1": "Red",
  "2": "Orange",
  "3": "Yellow",
  "4": "Green",
  "5": "Cyan",
  "6": "Purple"
};

// 2. Hex colors
const hexColor = "#FF5733";

// Apply color to node
const coloredNode = {
  id: generateId(),
  type: 'text',
  x: 0,
  y: 0,
  width: 250,
  height: 60,
  text: "Important!",
  color: "1"  // Red preset
};

// Apply color to edge
const coloredEdge = {
  id: generateId(),
  fromNode: "node1",
  toNode: "node2",
  color: "#00FF00"  // Green hex
};
```

### 7. Auto-Generate Mind Map

```typescript
async function createMindMap(
  app: App,
  canvasPath: string,
  centerIdea: string,
  branches: string[]
): Promise<void> {
  const canvasData = {
    nodes: [],
    edges: []
  };

  // Create center node
  const centerNode = createTextNode(400, 300, `# ${centerIdea}`);
  centerNode.color = "1";
  centerNode.width = 300;
  centerNode.height = 100;
  canvasData.nodes.push(centerNode);

  // Create branch nodes in a circle
  const radius = 300;
  const angleStep = (2 * Math.PI) / branches.length;

  branches.forEach((branch, index) => {
    const angle = index * angleStep;
    const x = 400 + radius * Math.cos(angle);
    const y = 300 + radius * Math.sin(angle);

    const branchNode = createTextNode(x, y, branch);
    branchNode.color = "4";
    canvasData.nodes.push(branchNode);

    // Connect to center
    const edge = createEdge(centerNode.id, branchNode.id, {
      toEnd: 'arrow',
      color: "2"
    });
    canvasData.edges.push(edge);
  });

  // Create canvas file
  const content = JSON.stringify(canvasData, null, 2);
  await app.vault.create(canvasPath, content);
}
```

### 8. Finding and Filtering Nodes

```typescript
// Get all text nodes
function getTextNodes(canvasData: any) {
  return canvasData.nodes.filter(node => node.type === 'text');
}

// Get all file nodes
function getFileNodes(canvasData: any) {
  return canvasData.nodes.filter(node => node.type === 'file');
}

// Find nodes by color
function getNodesByColor(canvasData: any, color: string) {
  return canvasData.nodes.filter(node => node.color === color);
}

// Find nodes in area
function getNodesInArea(
  canvasData: any,
  x: number,
  y: number,
  width: number,
  height: number
) {
  return canvasData.nodes.filter(node => {
    return (
      node.x >= x &&
      node.x <= x + width &&
      node.y >= y &&
      node.y <= y + height
    );
  });
}

// Get connected nodes
function getConnectedNodes(canvasData: any, nodeId: string) {
  const connectedIds = new Set();

  canvasData.edges.forEach(edge => {
    if (edge.fromNode === nodeId) connectedIds.add(edge.toNode);
    if (edge.toNode === nodeId) connectedIds.add(edge.fromNode);
  });

  return canvasData.nodes.filter(node => connectedIds.has(node.id));
}
```

### 9. Plugin Manifest Example

```json
{
  "id": "canvas-helper",
  "name": "Canvas Helper",
  "version": "1.0.0",
  "minAppVersion": "1.1.0",
  "description": "Tools for working with Canvas",
  "author": "Your Name",
  "authorUrl": "https://yoursite.com",
  "isDesktopOnly": false
}
```

### 10. Complete Plugin Template

```typescript
import { Plugin, TFile, Notice } from 'obsidian';

export default class CanvasHelperPlugin extends Plugin {
  async onload() {
    console.log('Loading Canvas Helper plugin');

    // Add ribbon icon
    this.addRibbonIcon('layout-grid', 'Canvas Helper', () => {
      new Notice('Canvas Helper active!');
    });

    // Add command to create mind map
    this.addCommand({
      id: 'create-mind-map',
      name: 'Create Mind Map',
      callback: async () => {
        await this.createDefaultMindMap();
      }
    });

    // Register event for canvas file changes
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (file instanceof TFile && file.extension === 'canvas') {
          console.log(`Canvas modified: ${file.path}`);
        }
      })
    );
  }

  async createDefaultMindMap() {
    const canvasData = {
      nodes: [
        createTextNode(400, 300, "# Main Idea"),
        createTextNode(600, 200, "Branch 1"),
        createTextNode(600, 400, "Branch 2")
      ],
      edges: [
        createEdge("node1", "node2"),
        createEdge("node1", "node3")
      ]
    };

    const content = JSON.stringify(canvasData, null, 2);
    await this.app.vault.create('MindMap.canvas', content);
    new Notice('Mind map created!');
  }

  onunload() {
    console.log('Unloading Canvas Helper plugin');
  }
}
```

## Reference Files

This skill includes comprehensive documentation in `references/`:

### README.md
Complete Obsidian Plugin API overview including:
- Plugin structure (manifest.json, main.js requirements)
- App architecture (App, Vault, Workspace, MetadataCache)
- Plugin class methods (addCommand, registerEvent, addRibbonIcon, etc.)
- Event registration patterns
- Best practices for plugin development

### CHANGELOG.md
Version history and API changes including:
- Canvas spec updates (v1.1.3+): Color format changes
- New plugin callbacks (onUserEnable, onExternalSettingsChange)
- Workspace changes (deferred views, ensureSideLeaf)
- Vault utility functions (getFileByPath, getFolderByPath)
- Breaking changes and migration guides

### file_structure.md
Repository structure of obsidian-api showing TypeScript type definitions organization

## Working with This Skill

### For Beginners
1. Read `references/README.md` for Obsidian plugin basics
2. Study the Quick Reference examples above
3. Create a simple plugin using the template in example #10
4. Test with a basic Canvas file

### For Intermediate Developers
1. Reference Quick Reference #2-5 for Canvas file manipulation
2. Use examples #6-8 for advanced features (colors, mind maps, filtering)
3. Check `references/CHANGELOG.md` for API updates
4. Implement error handling and validation

### For Advanced Developers
1. Build complex Canvas generation tools
2. Integrate with other Obsidian APIs (MetadataCache, Workspace)
3. Create custom Canvas visualizations
4. Optimize for large Canvas files (1000+ nodes)

## Key Concepts

### Canvas File Format
- **Format**: JSON file with `.canvas` extension
- **Structure**: Two main arrays - `nodes` and `edges`
- **Nodes**: Visual elements (text, file, link, group)
- **Edges**: Connections between nodes with optional arrows and labels

### Node Types
1. **Text Node** (`type: 'text'`): Contains Markdown text
2. **File Node** (`type: 'file'`): References vault file with optional subpath
3. **Link Node** (`type: 'link'`): Displays external URL
4. **Group Node** (`type: 'group'`): Container with optional background image

### Node Properties
- **Required**: id, type, x, y, width, height
- **Optional**: color (preset "1"-"6" or hex)
- **Type-specific**: text, file, url, label, background, etc.

### Edge System
- **Connections**: Link two nodes by their IDs
- **Sides**: Optional connection points (top, right, bottom, left)
- **Arrows**: Optional end styles (none, arrow)
- **Styling**: Optional color and label

### Color Formats
- **Preset Colors**: Strings "1" through "6" (themeable via CSS variables)
  - "1" = Red, "2" = Orange, "3" = Yellow
  - "4" = Green, "5" = Cyan, "6" = Purple
- **Hex Colors**: Standard format like "#FF0000"

### Z-Index Ordering
- Nodes are rendered in array order
- First node = lowest z-index (background)
- Last node = highest z-index (foreground)

## Plugin Development Best Practices

### File Operations
- Use `app.vault.read()` to read Canvas files
- Use `app.vault.modify()` to update existing Canvas files
- Use `app.vault.create()` to create new Canvas files
- Always validate JSON structure before parsing

### Event Handling
- Use `this.registerEvent()` for automatic cleanup
- Listen for `vault.on('modify')` to detect Canvas changes
- Check file extension before processing: `file.extension === 'canvas'`

### Performance
- Index nodes by ID for O(1) lookups: `Map<string, Node>`
- Lazy load content for large canvases
- Batch operations when modifying multiple nodes
- Validate Canvas structure before saving

### Error Handling
```typescript
async readCanvas(file: TFile) {
  try {
    const content = await this.app.vault.read(file);
    const data = JSON.parse(content);

    // Validate structure
    if (!data.nodes || !Array.isArray(data.nodes)) {
      throw new Error('Invalid canvas format');
    }

    return data;
  } catch (error) {
    new Notice(`Error reading canvas: ${error.message}`);
    return null;
  }
}
```

## Resources

### Official Documentation
- **Plugin API Docs**: https://docs.obsidian.md/
- **Sample Plugin**: https://github.com/obsidianmd/obsidian-sample-plugin
- **API Repository**: https://github.com/obsidianmd/obsidian-api
- **Developer Forum**: https://forum.obsidian.md/c/developers-api/14

### JSON Canvas Specification
- **Official Spec**: https://jsoncanvas.org/
- **GitHub**: https://github.com/obsidianmd/jsoncanvas

### Community
- **Discord**: Official Obsidian Discord server (#plugin-dev channel)
- **Forum**: Developer discussion and API requests
- **GitHub Discussions**: Feature requests and issues

## Common Use Cases

### 1. Auto-Link Related Notes
Create edges between Canvas file nodes based on vault links:
```typescript
async function autoLinkNotes(app: App, canvasFile: TFile) {
  const canvasData = await readCanvas(canvasFile);
  const fileNodes = canvasData.nodes.filter(n => n.type === 'file');

  for (let i = 0; i < fileNodes.length; i++) {
    for (let j = i + 1; j < fileNodes.length; j++) {
      const file1 = app.vault.getAbstractFileByPath(fileNodes[i].file);
      const file2 = app.vault.getAbstractFileByPath(fileNodes[j].file);

      if (file1 instanceof TFile && file2 instanceof TFile) {
        const content1 = await app.vault.read(file1);

        if (content1.includes(`[[${file2.basename}]]`)) {
          const edge = createEdge(fileNodes[i].id, fileNodes[j].id);
          canvasData.edges.push(edge);
        }
      }
    }
  }

  await saveCanvas(app, canvasFile, canvasData);
}
```

### 2. Batch Create File Nodes from Folder
```typescript
async function createNodesFromFolder(
  app: App,
  canvasPath: string,
  folderPath: string
) {
  const folder = app.vault.getAbstractFileByPath(folderPath);
  if (!folder || !(folder instanceof TFolder)) return;

  const files = folder.children.filter(
    f => f instanceof TFile && f.extension === 'md'
  );

  const canvasData = { nodes: [], edges: [] };
  const spacing = 450;
  const cols = Math.ceil(Math.sqrt(files.length));

  files.forEach((file, index) => {
    const row = Math.floor(index / cols);
    const col = index % cols;
    const node = createFileNode(col * spacing, row * spacing, file.path);
    canvasData.nodes.push(node);
  });

  const content = JSON.stringify(canvasData, null, 2);
  await app.vault.create(canvasPath, content);
}
```

### 3. Analyze Canvas Structure
```typescript
function analyzeCanvas(canvasData: any) {
  const nodeTypes = canvasData.nodes.reduce((acc, node) => {
    acc[node.type] = (acc[node.type] || 0) + 1;
    return acc;
  }, {});

  const nodesWithEdges = new Set();
  canvasData.edges.forEach(edge => {
    nodesWithEdges.add(edge.fromNode);
    nodesWithEdges.add(edge.toNode);
  });

  const isolatedNodes = canvasData.nodes.filter(
    node => !nodesWithEdges.has(node.id)
  );

  return {
    totalNodes: canvasData.nodes.length,
    totalEdges: canvasData.edges.length,
    nodeTypes,
    isolatedNodes: isolatedNodes.length,
    averageConnections: (canvasData.edges.length * 2) / canvasData.nodes.length
  };
}
```

## Notes

- This skill is based on the official Obsidian API repository
- Canvas support was added in Obsidian v1.1.0+
- Always test plugins with different Canvas file sizes
- Consider backwards compatibility when using new API features
- The Canvas format is designed to be extensible (additional properties are ignored)

---

**Based on official Obsidian API documentation** | Repository: obsidianmd/obsidian-api
