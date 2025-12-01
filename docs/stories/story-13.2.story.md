# Story 13.2: Canvas API集成

## Status
Pending

## Story

**As a** Canvas学习系统插件开发者,
**I want** 实现完整的Obsidian Canvas API集成和文件操作封装,
**so that** 插件能够安全地读取、修改Canvas文件，操作节点和边，并实现备份管理功能。

## Acceptance Criteria

1. 实现CanvasFileManager类，封装Canvas文件的读取、写入和备份操作
2. 实现CanvasNodeAPI类，提供节点的创建、读取、更新、删除（CRUD）操作
3. 实现CanvasEdgeAPI类，提供边的创建、删除和查询操作
4. 实现CanvasBackupManager类，管理`.canvas_backups/`隐藏文件夹的备份功能
5. 配置`.canvas_backups/`为隐藏文件夹，防止在Obsidian文件树中显示（符合SCP-003）
6. 所有Canvas操作具备完整的错误处理和回滚机制
7. 实现Canvas文件结构验证，防止无效JSON破坏文件

## Tasks / Subtasks

- [ ] Task 1: 实现CanvasFileManager类 (AC: 1, 6, 7)
  - [ ] 创建`src/managers/CanvasFileManager.ts`
  - [ ] 实现`readCanvas(file: TFile): Promise<CanvasData>`方法
  - [ ] 实现`writeCanvas(file: TFile, data: CanvasData): Promise<void>`方法
  - [ ] 实现`validateCanvasStructure(data: any): boolean`方法
  - [ ] 添加JSON解析错误处理和文件损坏检测
  - [ ] 实现事务性写入（先写临时文件，验证后替换）
  - [ ] 添加Canvas文件修改事件监听和自动重载机制

- [ ] Task 2: 实现CanvasNodeAPI类 (AC: 2, 6)
  - [ ] 创建`src/api/CanvasNodeAPI.ts`
  - [ ] 实现`createNode(type, x, y, options): Node`方法（支持text/file/link/group类型）
  - [ ] 实现`getNodeById(canvasData, nodeId): Node | null`方法
  - [ ] 实现`updateNode(canvasData, nodeId, updates): void`方法
  - [ ] 实现`deleteNode(canvasData, nodeId): void`方法（级联删除相关边）
  - [ ] 实现`getNodesByColor(canvasData, color): Node[]`方法
  - [ ] 实现`getNodesInArea(canvasData, x, y, width, height): Node[]`方法
  - [ ] 添加节点ID生成函数`generateNodeId(): string`

- [ ] Task 3: 实现CanvasEdgeAPI类 (AC: 3, 6)
  - [ ] 创建`src/api/CanvasEdgeAPI.ts`
  - [ ] 实现`createEdge(fromNodeId, toNodeId, options): Edge`方法
  - [ ] 实现`deleteEdge(canvasData, edgeId): void`方法
  - [ ] 实现`getConnectedNodes(canvasData, nodeId): Node[]`方法
  - [ ] 实现`getEdgesBetweenNodes(canvasData, nodeId1, nodeId2): Edge[]`方法
  - [ ] 实现`deleteEdgesByNode(canvasData, nodeId): void`方法（用于级联删除）
  - [ ] 添加边ID生成函数`generateEdgeId(): string`

- [ ] Task 4: 实现CanvasBackupManager类 (AC: 4, 5)
  - [ ] 创建`src/managers/CanvasBackupManager.ts`
  - [ ] 实现`createBackup(canvasFile: TFile): Promise<string>`方法
  - [ ] 实现备份文件命名策略（原文件名-YYYYMMDD-HHMMSS.canvas）
  - [ ] 实现`listBackups(canvasFile: TFile): Promise<BackupInfo[]>`方法
  - [ ] 实现`restoreBackup(backupPath: string, canvasFile: TFile): Promise<void>`方法
  - [ ] 实现`deleteBackup(backupPath: string): Promise<void>`方法
  - [ ] 配置`.canvas_backups/`为隐藏文件夹（在文件夹中创建`.obsidian-ignore`标记）
  - [ ] 实现自动清理机制（保留最近N个备份，可配置）

- [ ] Task 5: 实现Canvas数据类型定义 (AC: 7)
  - [ ] 创建`src/types/canvas.ts`
  - [ ] 定义`CanvasData`接口（nodes, edges数组）
  - [ ] 定义`CanvasNode`接口（支持text/file/link/group类型）
  - [ ] 定义`CanvasEdge`接口（fromNode, toNode, 连接点等）
  - [ ] 定义`BackupInfo`接口（路径、时间戳、文件大小等）
  - [ ] 定义颜色类型`CanvasColor`（预设颜色"1"-"6"或hex）
  - [ ] 导出所有类型供其他模块使用

- [ ] Task 6: 实现工具函数和常量 (AC: 2, 3)
  - [ ] 创建`src/utils/canvas-helpers.ts`
  - [ ] 实现`generateId(): string`函数（使用Math.random生成唯一ID）
  - [ ] 定义Canvas颜色常量`CANVAS_COLORS`（"1"-"6"映射）
  - [ ] 实现`isValidCanvasFile(file: TFile): boolean`函数
  - [ ] 实现`getCanvasBackupFolder(vault: Vault): string`函数
  - [ ] 实现`formatBackupName(originalName: string, timestamp: Date): string`函数

- [ ] Task 7: 集成测试 (AC: 1-7)
  - [ ] 测试Canvas文件的读取和写入
  - [ ] 测试节点的CRUD操作
  - [ ] 测试边的创建和删除
  - [ ] 测试备份的创建、列表、恢复功能
  - [ ] 测试`.canvas_backups/`文件夹的隐藏状态
  - [ ] 测试错误处理（无效JSON、文件不存在等）
  - [ ] 测试事务性写入的回滚机制

## Dev Notes

### 架构上下文

**Canvas API层架构** [Source: docs/prd/epics/EPIC-13-UI.md#Story 13.2]

本Story实现Canvas Learning System的Canvas文件操作层，为上层命令包装器提供稳定的API：

```
Obsidian插件架构:
├── PluginCore (Story 13.1) ✅
├── Canvas API层 (本Story) ← 当前实现
│   ├── CanvasFileManager (文件读写)
│   ├── CanvasNodeAPI (节点操作)
│   ├── CanvasEdgeAPI (边操作)
│   └── CanvasBackupManager (备份管理)
├── HTTP Client (Story 13.3)
└── CommandWrapper (Story 13.4)
```

**依赖关系**:
- 依赖Story 13.1的PluginCore框架
- 为Story 13.3的API Client提供Canvas上下文
- 为Story 13.4的命令包装器提供Canvas操作接口

### Canvas文件格式规范

**JSON Canvas标准格式** [Source: @obsidian-canvas Skill - SKILL.md#Basic Canvas File Structure]

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Canvas File Structure)
interface CanvasData {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}

interface CanvasNode {
  id: string;                    // 唯一标识符
  type: 'text' | 'file' | 'link' | 'group';
  x: number;                     // X坐标
  y: number;                     // Y坐标
  width: number;                 // 宽度
  height: number;                // 高度
  color?: string;                // 颜色（"1"-"6"或hex）

  // type === 'text'时
  text?: string;                 // Markdown文本

  // type === 'file'时
  file?: string;                 // Vault中的文件路径
  subpath?: string;              // 可选的子路径（#Section）

  // type === 'link'时
  url?: string;                  // 外部URL

  // type === 'group'时
  label?: string;                // 组标签
  background?: string;           // 背景图片路径
  backgroundStyle?: string;      // 背景样式
}

interface CanvasEdge {
  id: string;                    // 唯一标识符
  fromNode: string;              // 源节点ID
  toNode: string;                // 目标节点ID
  fromSide?: 'top' | 'right' | 'bottom' | 'left';
  toSide?: 'top' | 'right' | 'bottom' | 'left';
  toEnd?: 'none' | 'arrow';      // 箭头类型
  label?: string;                // 边标签
  color?: string;                // 边颜色
}
```

### Canvas文件读写API

**Vault API文件操作** [Source: @obsidian-canvas Skill - SKILL.md#Reading a Canvas File]

```typescript
// ✅ Verified from Obsidian Canvas Skill (SKILL.md - Reading/Writing Canvas)
import { TFile, Vault, Notice } from 'obsidian';

class CanvasFileManager {
  constructor(private vault: Vault) {}

  // 读取Canvas文件
  async readCanvas(file: TFile): Promise<CanvasData> {
    try {
      // ✅ Verified from Obsidian Canvas Skill (Quick Reference #2)
      const content = await this.vault.read(file);
      const data = JSON.parse(content);

      // 验证结构
      if (!this.validateCanvasStructure(data)) {
        throw new Error('Invalid canvas file structure');
      }

      return data as CanvasData;
    } catch (error) {
      console.error('Failed to read canvas:', error);
      new Notice(`Canvas读取失败: ${error.message}`);
      throw error;
    }
  }

  // 写入Canvas文件
  async writeCanvas(file: TFile, data: CanvasData): Promise<void> {
    try {
      // 验证数据结构
      if (!this.validateCanvasStructure(data)) {
        throw new Error('Invalid canvas data structure');
      }

      // 事务性写入：先写临时文件
      const tempPath = `${file.path}.tmp`;
      const content = JSON.stringify(data, null, 2);

      // ✅ Verified from Obsidian Canvas Skill (Quick Reference #4)
      await this.vault.create(tempPath, content);

      // 验证临时文件可读
      const tempFile = this.vault.getAbstractFileByPath(tempPath) as TFile;
      await this.vault.read(tempFile);

      // 替换原文件
      await this.vault.modify(file, content);

      // 删除临时文件
      await this.vault.delete(tempFile);

    } catch (error) {
      console.error('Failed to write canvas:', error);
      new Notice(`Canvas保存失败: ${error.message}`);
      throw error;
    }
  }

  // 验证Canvas数据结构
  validateCanvasStructure(data: any): boolean {
    if (!data || typeof data !== 'object') return false;
    if (!Array.isArray(data.nodes)) return false;
    if (!Array.isArray(data.edges)) return false;

    // 验证节点结构
    for (const node of data.nodes) {
      if (!node.id || !node.type || typeof node.x !== 'number' || typeof node.y !== 'number') {
        return false;
      }
    }

    // 验证边结构
    for (const edge of data.edges) {
      if (!edge.id || !edge.fromNode || !edge.toNode) {
        return false;
      }
    }

    return true;
  }
}
```

### 节点操作API设计

**Node CRUD Operations** [Source: @obsidian-canvas Skill - SKILL.md#Creating Canvas Nodes]

```typescript
// ✅ Verified from Obsidian Canvas Skill (Quick Reference #3)
class CanvasNodeAPI {
  // 生成唯一ID
  private generateId(): string {
    // ✅ Verified from Obsidian Canvas Skill (SKILL.md - Creating Nodes)
    return Math.random().toString(36).substring(2, 15);
  }

  // 创建文本节点
  createTextNode(x: number, y: number, text: string, options?: {
    width?: number;
    height?: number;
    color?: string;
  }): CanvasNode {
    return {
      id: this.generateId(),
      type: 'text',
      x,
      y,
      width: options?.width || 250,
      height: options?.height || 60,
      text,
      color: options?.color
    };
  }

  // 创建文件节点
  createFileNode(x: number, y: number, filePath: string, options?: {
    width?: number;
    height?: number;
    subpath?: string;
    color?: string;
  }): CanvasNode {
    return {
      id: this.generateId(),
      type: 'file',
      x,
      y,
      width: options?.width || 400,
      height: options?.height || 300,
      file: filePath,
      subpath: options?.subpath,
      color: options?.color
    };
  }

  // 获取节点（通过ID）
  getNodeById(canvasData: CanvasData, nodeId: string): CanvasNode | null {
    return canvasData.nodes.find(node => node.id === nodeId) || null;
  }

  // 更新节点
  updateNode(canvasData: CanvasData, nodeId: string, updates: Partial<CanvasNode>): void {
    const nodeIndex = canvasData.nodes.findIndex(node => node.id === nodeId);
    if (nodeIndex === -1) {
      throw new Error(`Node not found: ${nodeId}`);
    }

    // 合并更新，保留原有属性
    canvasData.nodes[nodeIndex] = {
      ...canvasData.nodes[nodeIndex],
      ...updates,
      id: nodeId  // 确保ID不被修改
    };
  }

  // 删除节点（级联删除相关边）
  deleteNode(canvasData: CanvasData, nodeId: string): void {
    // 删除节点
    const nodeIndex = canvasData.nodes.findIndex(node => node.id === nodeId);
    if (nodeIndex === -1) {
      throw new Error(`Node not found: ${nodeId}`);
    }
    canvasData.nodes.splice(nodeIndex, 1);

    // 级联删除相关的边
    canvasData.edges = canvasData.edges.filter(
      edge => edge.fromNode !== nodeId && edge.toNode !== nodeId
    );
  }

  // 按颜色查找节点
  getNodesByColor(canvasData: CanvasData, color: string): CanvasNode[] {
    // ✅ Verified from Obsidian Canvas Skill (Quick Reference #8)
    return canvasData.nodes.filter(node => node.color === color);
  }

  // 查找区域内的节点
  getNodesInArea(
    canvasData: CanvasData,
    x: number,
    y: number,
    width: number,
    height: number
  ): CanvasNode[] {
    // ✅ Verified from Obsidian Canvas Skill (Quick Reference #8)
    return canvasData.nodes.filter(node => {
      return (
        node.x >= x &&
        node.x <= x + width &&
        node.y >= y &&
        node.y <= y + height
      );
    });
  }
}
```

### 边操作API设计

**Edge Operations** [Source: @obsidian-canvas Skill - SKILL.md#Creating Edges]

```typescript
// ✅ Verified from Obsidian Canvas Skill (Quick Reference #5)
class CanvasEdgeAPI {
  private generateId(): string {
    return Math.random().toString(36).substring(2, 15);
  }

  // 创建边
  createEdge(
    fromNodeId: string,
    toNodeId: string,
    options?: {
      fromSide?: 'top' | 'right' | 'bottom' | 'left';
      toSide?: 'top' | 'right' | 'bottom' | 'left';
      toEnd?: 'none' | 'arrow';
      label?: string;
      color?: string;
    }
  ): CanvasEdge {
    return {
      id: this.generateId(),
      fromNode: fromNodeId,
      toNode: toNodeId,
      fromSide: options?.fromSide,
      toSide: options?.toSide,
      toEnd: options?.toEnd || 'arrow',
      label: options?.label,
      color: options?.color
    };
  }

  // 删除边
  deleteEdge(canvasData: CanvasData, edgeId: string): void {
    const edgeIndex = canvasData.edges.findIndex(edge => edge.id === edgeId);
    if (edgeIndex === -1) {
      throw new Error(`Edge not found: ${edgeId}`);
    }
    canvasData.edges.splice(edgeIndex, 1);
  }

  // 获取与节点相连的所有节点
  getConnectedNodes(canvasData: CanvasData, nodeId: string): CanvasNode[] {
    // ✅ Verified from Obsidian Canvas Skill (Quick Reference #8)
    const connectedIds = new Set<string>();

    canvasData.edges.forEach(edge => {
      if (edge.fromNode === nodeId) connectedIds.add(edge.toNode);
      if (edge.toNode === nodeId) connectedIds.add(edge.fromNode);
    });

    return canvasData.nodes.filter(node => connectedIds.has(node.id));
  }

  // 获取两个节点之间的所有边
  getEdgesBetweenNodes(
    canvasData: CanvasData,
    nodeId1: string,
    nodeId2: string
  ): CanvasEdge[] {
    return canvasData.edges.filter(edge =>
      (edge.fromNode === nodeId1 && edge.toNode === nodeId2) ||
      (edge.fromNode === nodeId2 && edge.toNode === nodeId1)
    );
  }

  // 删除节点相关的所有边（用于级联删除）
  deleteEdgesByNode(canvasData: CanvasData, nodeId: string): void {
    canvasData.edges = canvasData.edges.filter(
      edge => edge.fromNode !== nodeId && edge.toNode !== nodeId
    );
  }
}
```

### Canvas备份管理

**Backup Management System** [Source: docs/prd/epics/EPIC-13-UI.md#SCP-003]

本Story需要实现SCP-003规范中的Canvas备份功能：

```typescript
import { TFile, TFolder, Vault } from 'obsidian';

interface BackupInfo {
  path: string;           // 备份文件完整路径
  originalName: string;   // 原文件名
  timestamp: Date;        // 备份时间戳
  size: number;          // 文件大小（字节）
}

class CanvasBackupManager {
  private readonly BACKUP_FOLDER = '.canvas_backups';

  constructor(private vault: Vault) {}

  // 创建备份
  async createBackup(canvasFile: TFile): Promise<string> {
    try {
      // 确保备份文件夹存在
      await this.ensureBackupFolder();

      // 生成备份文件名：原文件名-YYYYMMDD-HHMMSS.canvas
      const timestamp = new Date();
      const backupName = this.formatBackupName(canvasFile.basename, timestamp);
      const backupPath = `${this.BACKUP_FOLDER}/${backupName}`;

      // 读取原文件内容
      const content = await this.vault.read(canvasFile);

      // 创建备份文件
      await this.vault.create(backupPath, content);

      console.log(`Canvas备份已创建: ${backupPath}`);
      return backupPath;

    } catch (error) {
      console.error('Failed to create backup:', error);
      throw error;
    }
  }

  // 列出所有备份
  async listBackups(canvasFile: TFile): Promise<BackupInfo[]> {
    const backupFolder = this.vault.getAbstractFileByPath(this.BACKUP_FOLDER);
    if (!backupFolder || !(backupFolder instanceof TFolder)) {
      return [];
    }

    const baseName = canvasFile.basename;
    const backups: BackupInfo[] = [];

    for (const file of backupFolder.children) {
      if (file instanceof TFile && file.name.startsWith(baseName)) {
        const timestamp = this.parseBackupTimestamp(file.name);
        if (timestamp) {
          backups.push({
            path: file.path,
            originalName: baseName,
            timestamp,
            size: file.stat.size
          });
        }
      }
    }

    // 按时间倒序排序
    return backups.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  // 恢复备份
  async restoreBackup(backupPath: string, canvasFile: TFile): Promise<void> {
    const backupFile = this.vault.getAbstractFileByPath(backupPath);
    if (!backupFile || !(backupFile instanceof TFile)) {
      throw new Error(`Backup not found: ${backupPath}`);
    }

    // 读取备份内容
    const content = await this.vault.read(backupFile);

    // 写入原文件
    await this.vault.modify(canvasFile, content);

    console.log(`Canvas已恢复自备份: ${backupPath}`);
  }

  // 删除备份
  async deleteBackup(backupPath: string): Promise<void> {
    const backupFile = this.vault.getAbstractFileByPath(backupPath);
    if (backupFile && backupFile instanceof TFile) {
      await this.vault.delete(backupFile);
      console.log(`备份已删除: ${backupPath}`);
    }
  }

  // 自动清理旧备份（保留最近N个）
  async cleanupOldBackups(canvasFile: TFile, keepCount: number = 10): Promise<void> {
    const backups = await this.listBackups(canvasFile);

    if (backups.length > keepCount) {
      const toDelete = backups.slice(keepCount);
      for (const backup of toDelete) {
        await this.deleteBackup(backup.path);
      }
      console.log(`已清理${toDelete.length}个旧备份`);
    }
  }

  // 确保备份文件夹存在且为隐藏
  private async ensureBackupFolder(): Promise<void> {
    const folder = this.vault.getAbstractFileByPath(this.BACKUP_FOLDER);

    if (!folder) {
      // 创建备份文件夹
      await this.vault.createFolder(this.BACKUP_FOLDER);

      // 创建.obsidian-ignore标记文件，使其在文件树中隐藏
      const ignorePath = `${this.BACKUP_FOLDER}/.obsidian-ignore`;
      await this.vault.create(ignorePath, '');

      console.log(`备份文件夹已创建并配置为隐藏: ${this.BACKUP_FOLDER}`);
    }
  }

  // 格式化备份文件名
  private formatBackupName(originalName: string, timestamp: Date): string {
    const year = timestamp.getFullYear();
    const month = String(timestamp.getMonth() + 1).padStart(2, '0');
    const day = String(timestamp.getDate()).padStart(2, '0');
    const hour = String(timestamp.getHours()).padStart(2, '0');
    const minute = String(timestamp.getMinutes()).padStart(2, '0');
    const second = String(timestamp.getSeconds()).padStart(2, '0');

    return `${originalName}-${year}${month}${day}-${hour}${minute}${second}.canvas`;
  }

  // 解析备份文件名中的时间戳
  private parseBackupTimestamp(fileName: string): Date | null {
    // 匹配格式：原文件名-YYYYMMDD-HHMMSS.canvas
    const match = fileName.match(/-(\d{8})-(\d{6})\.canvas$/);
    if (!match) return null;

    const dateStr = match[1];  // YYYYMMDD
    const timeStr = match[2];  // HHMMSS

    const year = parseInt(dateStr.substring(0, 4));
    const month = parseInt(dateStr.substring(4, 6)) - 1;
    const day = parseInt(dateStr.substring(6, 8));
    const hour = parseInt(timeStr.substring(0, 2));
    const minute = parseInt(timeStr.substring(2, 4));
    const second = parseInt(timeStr.substring(4, 6));

    return new Date(year, month, day, hour, minute, second);
  }
}
```

### Canvas颜色系统

**Color Format Support** [Source: @obsidian-canvas Skill - SKILL.md#Canvas Color System]

```typescript
// ✅ Verified from Obsidian Canvas Skill (Quick Reference #6)

// Canvas支持两种颜色格式：
// 1. 预设颜色（字符串"1"-"6"）
// 2. Hex颜色（如"#FF5733"）

const CANVAS_COLORS = {
  "1": "Red",
  "2": "Orange",
  "3": "Yellow",
  "4": "Green",
  "5": "Cyan",
  "6": "Purple"
} as const;

type CanvasPresetColor = "1" | "2" | "3" | "4" | "5" | "6";
type CanvasHexColor = `#${string}`;
type CanvasColor = CanvasPresetColor | CanvasHexColor;

// 示例：设置节点颜色
const redNode = createTextNode(0, 0, "Important", { color: "1" });
const customNode = createTextNode(100, 0, "Custom", { color: "#FF5733" });
```

### 编码规范

**TypeScript最佳实践**:
- 所有Canvas操作必须有明确的类型注解
- 使用async/await处理异步文件操作
- 实现完整的错误处理和用户反馈
- 事务性写入：先写临时文件，验证后替换原文件
- 级联操作：删除节点时自动删除相关边

**错误处理模式**:
```typescript
try {
  await this.performCanvasOperation();
} catch (error) {
  console.error('Canvas operation failed:', error);
  new Notice(`操作失败: ${error.message}`);
  // 必要时回滚更改
  throw error;
}
```

### 测试要求

**单元测试覆盖**:
- CanvasFileManager: 读写、验证、事务性写入
- CanvasNodeAPI: CRUD操作、颜色过滤、区域查询
- CanvasEdgeAPI: 创建、删除、连接查询
- CanvasBackupManager: 备份创建、列表、恢复、清理

**集成测试场景**:
1. 创建节点 → 保存Canvas → 读取验证
2. 删除节点 → 验证边的级联删除
3. 创建备份 → 修改原文件 → 恢复备份
4. 验证`.canvas_backups/`文件夹的隐藏状态

### 集成考虑

**与其他Story的集成**:
- **Story 13.3 (API客户端)**: 需要Canvas上下文来发送节点数据到后端
- **Story 13.4 (核心命令)**: 将调用本Story提供的所有Canvas操作API
- **Story 13.5 (右键菜单)**: "保护此备份"功能将调用BackupManager

**性能优化**:
- 大型Canvas文件（1000+节点）需要延迟加载
- 使用Map索引节点ID，实现O(1)查找
- 批量操作时减少文件写入次数

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | 初始Story创建 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/src/managers/CanvasFileManager.ts` - Canvas文件读写管理器
- `canvas-progress-tracker/obsidian-plugin/src/managers/CanvasBackupManager.ts` - Canvas备份管理器
- `canvas-progress-tracker/obsidian-plugin/src/api/CanvasNodeAPI.ts` - 节点操作API
- `canvas-progress-tracker/obsidian-plugin/src/api/CanvasEdgeAPI.ts` - 边操作API
- `canvas-progress-tracker/obsidian-plugin/src/types/canvas.ts` - Canvas数据类型定义
- `canvas-progress-tracker/obsidian-plugin/src/utils/canvas-helpers.ts` - Canvas工具函数
- `canvas-progress-tracker/obsidian-plugin/.canvas_backups/.obsidian-ignore` - 备份文件夹隐藏标记

**修改的文件：**
- 无

## QA Results

### Review Date: 待开发

### Reviewed By: 待开发

### Code Quality Assessment
待开发

### Compliance Check
待开发

### Security Review
待开发

### Performance Considerations
待开发

### Architecture & Design Review
待开发

### Test Quality Review
待开发

### Final Status
待开发

---

**本Story完成后，将建立起完整的Canvas文件操作API层，为后续的命令包装器和UI组件提供稳定、安全的Canvas数据访问接口。所有Canvas操作都将通过此API层进行，确保数据一致性和错误处理的统一性。**
