# Semantic语义记忆 (业务层记忆 - 文档向量)

**职责范围**:
- ✅ 存储AI生成文档的向量表示（解释文档embeddings）
- ✅ 支持语义相似度检索（找相似解释）
- ✅ 支持文档推荐（"这个解释可能对你有帮助"）

**不存储**:
- ❌ Canvas节点内容（节点内容在Canvas文件中）
- ❌ 知识图谱（由Graphiti管理）

**数据示例**:
```json
{
  "document_id": "doc_逆否命题_口语化解释_20250115143025",
  "file_path": "Canvas/Math53/逆否命题-口语化解释-20250115143025.md",
  "embedding": [0.123, -0.456, ...],  // 1536维向量
  "metadata": {
    "concept": "逆否命题",
    "agent": "oral-explanation",
    "word_count": 950
  }
}
```

**何时调用**:
- `store_to_semantic_memory()`: 仅在生成解释文档后

---
