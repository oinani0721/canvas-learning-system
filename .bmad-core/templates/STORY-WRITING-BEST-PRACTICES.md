# Story编写最佳实践 - 快速参考

**版本**: v3.0
**基于**: Story 10.9 UltraThink验证经验
**用途**: PM Agent和Story作者的快速参考

---

## 🎯 黄金法则

### 法则1: Epic优先
**永远先读Epic，再写Story**

```
❌ 错误流程:
   开始写Story → 猜测Epic内容 → 引用可能不存在的类

✅ 正确流程:
   阅读Epic → 理解Problem → 验证依赖 → 编写Story
```

### 法则2: 验证优先
**所有引用必须验证存在**

```
❌ 错误:
   "使用LearningSessionWrapper类..."（未验证）

✅ 正确:
   1. Grep搜索: class LearningSessionWrapper
   2. 确认存在: learning_session_wrapper.py:42
   3. 记录: "LearningSessionWrapper (learning_session_wrapper.py:42)"
```

### 法则3: 详细优先
**测试数据必须详细说明**

```
❌ 错误:
   - [ ] 创建测试文件 test.canvas

✅ 正确:
   - [ ] 创建测试文件 test.canvas
         - 内容规格: 3个红色节点
         - 节点内容: "什么是逆否命题?", "如何证明充要条件?", ...
```

### 法则4: 来源优先
**所有技术声明标注来源**

```
❌ 错误:
   系统使用三级记忆架构...

✅ 正确:
   系统使用三级记忆架构 [Source: docs/architecture/memory-system.md]
```

### 法则5: 依赖优先
**先完成依赖验证清单，再写任务**

```
正确顺序:
1. 填写"前置依赖验证"清单
2. 验证所有项目✓
3. 然后编写具体任务
```

---

## 📋 Story编写检查清单 (30秒版)

### 开始前 (5秒)
- [ ] ✅ 已阅读Epic文档
- [ ] ✅ 理解Epic的Problem 1, 2等
- [ ] ✅ 知道本Story在Epic中的作用

### Epic Context (5秒)
- [ ] ✅ 填写了"Epic背景与上下文"章节
- [ ] ✅ Epic文档链接有效
- [ ] ✅ Story依赖已列出

### AC和任务 (5秒)
- [ ] ✅ 所有AC都链接到Epic问题
- [ ] ✅ 所有任务都标注AC编号
- [ ] ✅ 测试数据有详细规格

### Dev Notes (10秒)
- [ ] ✅ "前置依赖验证"清单完整
- [ ] ✅ 所有类已验证存在
- [ ] ✅ "相关文档引用"章节完整

### 最终检查 (5秒)
- [ ] ✅ Story自包含（Dev Agent无需读Epic）
- [ ] ✅ 所有引用可验证
- [ ] ✅ 无幻觉内容

---

## 🚨 常见错误和避免方法

### 错误1: 孤立的Story
**问题**: Story没有Epic上下文，Dev Agent不知道为什么要做这个

**表现**:
```markdown
## Story
As a developer, I want to implement XYZ...
```

**修复**:
```markdown
## Epic背景与上下文
**所属Epic**: EPIC-010
**Epic核心问题**: Problem 1 - XYZ断层

## Story
As a developer, I want to fix Problem 1...
```

**影响**: 关键 - 可能导致Story方向错误

---

### 错误2: 未验证的类引用
**问题**: 引用了可能不存在的类

**表现**:
```markdown
使用LearningSessionWrapper类来启动会话...
```

**修复**:
```markdown
**前置依赖验证**:
- [ ] `LearningSessionWrapper`已验证存在: learning_session_wrapper.py:42

使用LearningSessionWrapper类 [Source: learning_session_wrapper.py]
```

**影响**: 关键 - 实施时ImportError

---

### 错误3: 模糊的测试数据
**问题**: 测试任务没说明数据内容

**表现**:
```markdown
- [ ] 创建测试Canvas文件
```

**修复**:
```markdown
- [ ] 创建测试Canvas文件 (tests/fixtures/test.canvas)
      - **内容规格**: 3个红色节点
      - 节点示例: "什么是逆否命题?"
      - JSON格式: 完整的nodes和edges结构
```

**影响**: 中等 - Dev Agent需要猜测内容

---

### 错误4: 缺失的Story依赖
**问题**: 任务依赖其他Story但没说明

**表现**:
```markdown
### 任务1: 测试Canvas集成 (AC: 1)
- [ ] 验证节点生成
```

**修复**:
```markdown
### 任务1: 测试Canvas集成 (AC: 1, Story 10.7验证)
- [ ] 验证节点生成
      - 验证Story 10.7的CanvasIntegrationCoordinator
```

**影响**: 中等 - 依赖不清晰

---

### 错误5: 零散的文档引用
**问题**: 文档链接散落在Dev Notes各处

**表现**:
```markdown
根据coding-standards.md...
参考epic-10.md的Problem 1...
类定义在file.py...
```

**修复**:
```markdown
### 🔗 相关文档引用

**Epic和Story文档**:
- [epic-10.md](./epic-10.md)

**架构文档**:
- [coding-standards.md](../architecture/coding-standards.md)

**源代码位置**:
- file.py - 类定义位置
```

**影响**: 低 - 但降低可读性

---

## 🎓 进阶技巧

### 技巧1: 使用验证注释

在代码示例中添加验证注释：

```python
# ========== Phase 1: 启动学习会话 ==========
# 验证 Problem 2修复: /learning真正启动服务
wrapper = LearningSessionWrapper()  # Story 10.8
session = await wrapper.start_session(...)

print(f"✅ Phase 1: 学习会话已启动")
print(f"   验证: Story 10.8 RealServiceLauncher工作正常")
```

**好处**: Dev Agent清楚知道每个步骤验证什么

---

### 技巧2: 创建Success Criteria Mapping表

```markdown
| AC | 实现任务 | 验证方法 | Story依赖 |
|----|---------|---------|----------|
| AC 1 | 任务1 | pytest test_x() | Story 10.7+10.8 |
| AC 2 | 任务2 | pytest test_y() | Story 10.7 |
```

**好处**: 一眼看清AC、任务、依赖的关系

---

### 技巧3: 模块级覆盖率目标

不要只说"覆盖率≥90%"，要细化：

```markdown
**模块级覆盖率目标**:
- canvas_integration_coordinator.py: ≥ 95%
- real_service_launcher.py: ≥ 95%
- learning_session_wrapper.py: ≥ 90%
```

**好处**: 更精细的质量控制

---

### 技巧4: Mock策略说明

如果依赖外部服务：

```markdown
**外部服务依赖**:
- Graphiti服务: docker-compose up -d graphiti
- 验证: curl http://localhost:8080/health

**Mock策略** (CI环境):
- 使用monkeypatch.setattr()
- Mock配置在conftest.py
```

**好处**: 测试可以在有/无外部服务环境运行

---

### 技巧5: 前后对比

在Change Log中说明重大修复：

```markdown
| 2025-10-29 | v2.0 | 🔥 UltraThink修复 | PM Agent |

**v2.0修复内容**:
- ✅ 添加Epic上下文 (+47行)
- ✅ 验证所有类依赖
- ✅ 详细说明测试数据规格
```

**好处**: 清楚看到修复了什么问题

---

## 📊 质量指标

### 优秀Story的特征

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| **实施准备度** | ≥ 9/10 | UltraThink验证 |
| **Epic关联度** | 100% | 所有AC都链接Epic |
| **依赖清晰度** | 100% | 所有依赖已验证 |
| **反幻觉评分** | ≥ 9/10 | 验证清单通过 |
| **自包含性** | ✅ | Dev Agent无需读Epic |

### 常见质量问题

| 问题 | 频率 | 修复成本 | 预防方法 |
|------|------|---------|---------|
| 缺少Epic上下文 | 高 | 2小时 | v3.0模板 |
| 未验证类引用 | 中 | 1小时 | 依赖验证清单 |
| 模糊测试数据 | 中 | 30分钟 | 详细规格要求 |
| 缺失Story依赖 | 低 | 1小时 | AC/任务增强 |

---

## 🚀 快速行动指南

### 我应该做什么？

**如果你是Story作者**:
1. ✅ 学习v3.0模板
2. ✅ 使用STORY-TEMPLATE-V3-GUIDE.md
3. ✅ 运行验证清单
4. ✅ 避免5个常见错误

**如果你是PM Agent**:
1. ✅ 审查Story时检查Epic上下文
2. ✅ 验证依赖清单完整性
3. ✅ 确保测试数据详细
4. ✅ 使用UltraThink验证重要Story

**如果你是Dev Agent**:
1. ✅ 优先阅读Epic Context章节
2. ✅ 检查依赖验证清单
3. ✅ 参考相关文档引用章节
4. ✅ 遇到问题先检查Story是否v3.0兼容

---

## 📚 相关资源

### 必读文档
1. **STORY-TEMPLATE-V3-GUIDE.md** - 完整使用指南 (本文档的详细版)
2. **story-tmpl-v3-enhanced.yaml** - YAML格式模板
3. **10.9-ULTRATHINK-VALIDATION-AND-FIX-REPORT.md** - Story 10.9修复案例

### 参考案例
- **Story 10.9 (修复后)** - v3.0标准示例
- **Epic 10** - Epic Context示例
- **Story 10.7, 10.8** - Story依赖示例

### 工具
- **validate-next-story.md** - Story验证流程
- **Glob工具** - 搜索文件
- **Grep工具** - 搜索代码

---

## ⚡ 30秒快速开始

```markdown
1. 读Epic → 理解Problem
2. 填Epic Context → 链接Epic
3. 列依赖验证 → 验证类存在
4. 写AC → 标注Epic关联
5. 写任务 → 标注AC和Story依赖
6. 加文档引用 → 集中链接
7. 运行清单 → 确保完整
```

---

## 💡 记住这个

**Story 10.9教训**:
```
缺少Epic上下文 → 引用不存在的类 → 实施准备度5/10 → 修复2小时

使用v3.0模板 → Epic优先 → 依赖验证 → 实施准备度9/10 → 节约时间
```

**投资回报**:
- 额外编写时间: +30分钟
- 避免修复时间: -2小时
- **净收益: +90分钟**

---

## 🎉 总结

**3个关键改变**:
1. ✅ **Epic Context必需** - 永远先读Epic
2. ✅ **依赖验证必需** - 所有引用先验证
3. ✅ **详细规格必需** - 测试数据要详细

**5秒记忆法**:
```
Epic → 验证 → 详细 → 来源 → 依赖
```

**立即行动**:
1. 收藏本文档
2. 下次编写Story时使用
3. 运行验证清单
4. 分享给团队

---

**版本**: v1.0
**最后更新**: 2025-10-29
**维护者**: PM Agent (Sarah)

**快速链接**:
- [完整指南](./STORY-TEMPLATE-V3-GUIDE.md)
- [YAML模板](./story-tmpl-v3-enhanced.yaml)
- [Story 10.9案例](../../docs/stories/10.9-ULTRATHINK-VALIDATION-AND-FIX-REPORT.md)
