# Epic 13: Obsidian Plugin核心功能

**版本**: 1.0 (从PRD v1.1.8提取)
**创建日期**: 2025-11-21
**Epic ID**: Epic 13
**优先级**: P0
**依赖**: Epic 11 (FastAPI后端), Epic 12 (LangGraph编排)

---

## Story序列

| Story ID | Story名称 | 优先级 |
|----------|----------|--------|
| Story 13.1 | Plugin项目初始化 | P0 |
| Story 13.2 | Canvas API集成 | P0 |
| Story 13.3 | API客户端实现 | P0 |
| Story 13.4 | 核心命令 (拆解、评分、解释) | P0 |
| Story 13.5 | 右键菜单和快捷键 | P1 |
| Story 13.6 | 设置面板 | P1 |
| Story 13.7 | 错误处理 | P1 |

---

## 技术验证要求

⚠️ 本Epic所有Stories必须遵守Section 1.X技术验证协议。

**强制文档来源**:
- Local Skill: `@obsidian-canvas` (Canvas API文档)

**验证检查点**:
- SM Agent必须激活Skills并记录查询结果
- Dev Agent必须在代码中添加Skill引用注释
- Code Review必须验证Obsidian API调用的正确性

---

## Story详细说明

### Story 13.1: Plugin项目初始化
- Obsidian Plugin开发环境搭建
- TypeScript配置
- 项目结构创建
- 构建脚本配置

### Story 13.2: Canvas API集成
- Obsidian Canvas API研究和集成
- Canvas文件读写封装
- 节点/边操作API
- **[SCP-003] 配置`.canvas_backups/`为隐藏文件夹**

### Story 13.3: API客户端实现
- FastAPI后端HTTP客户端
- 请求/响应类型定义
- 错误处理封装
- 重试机制

### Story 13.4: 核心命令实现
- 命令注册系统
- 基础拆解命令
- 深度拆解命令
- 评分命令
- 各类解释命令

### Story 13.5: 右键菜单和快捷键
- Canvas节点右键菜单注册
- 快捷键配置
- **[SCP-003] 右键菜单"保护此备份 🔒"选项**
- 用户自定义快捷键支持

### Story 13.6: 设置面板
- Plugin设置页面
- 后端URL配置
- 默认参数设置
- 主题和显示设置

### Story 13.7: 错误处理
- 全局错误捕获
- 用户友好的错误提示
- 错误日志记录
- 重试和恢复机制

---

## 相关SCP

- **SCP-003**: Canvas备份文件夹组织规范
  - Story 13.1: 在Obsidian Plugin中配置`.canvas_backups/`为隐藏文件夹
  - Story 13.5: 实现右键菜单"保护此备份"功能

---

**文档结束**

**提取来源**: PRD v1.1.8 (Lines 6103-6113)
**提取日期**: 2025-11-21
