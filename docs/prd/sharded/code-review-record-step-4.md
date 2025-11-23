# Code Review Record (Step 4)

**Reviewer**: {Agent Name}
**Review Date**: {timestamp}
**Review Status**: ✅ PASSED / ❌ REJECTED

### 标注覆盖率统计
- 技术代码总行数: {N}
- 已标注行数: {M}
- 覆盖率: {M/N * 100}%
- 状态: {≥80%为PASS, <80%为FAIL}

### 核心API验证
| API调用 | 文档来源 | 标注完整 | API正确 | 状态 |
|---------|---------|---------|---------|------|
| create_react_agent() | LangGraph Skill (SKILL.md:226-230) | ✅ | ✅ | PASS |
| Graphiti() | Graphiti Skill (SKILL.md:156-162) | ✅ | ✅ | PASS |
| fastapi.Depends() | Context7:FastAPI | ✅ | ✅ | PASS |

### 来源可追溯性抽查
- [ ] 抽查3个Skill来源 → 全部通过
- [ ] 抽查2个Context7来源 → 全部通过
- [ ] 无伪造或错误来源

### Code Review Checklist执行结果
- [ ] Section 1: 文档引用完整性 - PASSED
- [ ] Section 2: 来源可追溯性 - PASSED
- [ ] Section 3: API正确性 - PASSED
- [ ] Section 4: 违规处理 - N/A
- [ ] Section 5: 通过/失败示例 - 参考checklist

### 发现问题（如有）
[列出需要修复的问题]

### 审查结论
✅ 代码符合"零幻觉开发原则"，批准合并
或
❌ 存在{N}处违规，要求Dev Agent修复后重新提交
```

**拒绝合并场景**:

| 场景 | 标准 | 行动 |
|------|------|------|
| 缺失来源标注 | 任何技术代码无标注 | 要求Dev Agent补充标注 |
| 标注覆盖率不足 | <80%覆盖率 | 要求Dev Agent提升到≥80% |
| 核心API无标注 | Agent调用/Canvas操作/DB查询无标注 | 强制100%标注 |
| 来源不可追溯 | 标注的文档位置不存在 | 要求Dev Agent修正来源 |
| API不匹配 | 代码API与文档API不符 | 要求Dev Agent修正代码 |
| Checklist未执行 | 未提供Checklist结果 | 要求Code Reviewer执行检查清单 |

**通过合并后**:
- ✅ 将Code Review Record归档到Story文件
- ✅ 更新项目的文档覆盖率统计
- ✅ 为下一个Story提供参考标准



#### Documentation Quality Standards

每个Story必须包含：
- ✅ **Required Skills**: 列出需要激活的Skills
- ✅ **Context7 Queries**: 列出已查询的Library IDs
- ✅ **API Verification**: 关键API都有文档来源标注
- ✅ **Code Examples**: 复制官方示例并标注来源

**示例标注格式**:
```python