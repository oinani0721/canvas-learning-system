"""
ChromaDB → LanceDB迁移工具测试
Canvas Learning System - Story 12.3

测试所有5个acceptance criteria (AC 3.1-3.5):
- AC 3.1: ChromaDB数据完整导出
- AC 3.2: LanceDB数据完整导入
- AC 3.3: 数据一致性校验
- AC 3.4: 双写模式运行
- AC 3.5: Rollback plan验证
"""

import pytest
import json
import tempfile
import os
import shutil
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 导入测试目标
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from migrate_chromadb_to_lancedb import (
    MigrationConfig,
    ChromaDBExporter,
    LanceDBImporter,
    DataConsistencyValidator,
    BackupManager,
    DualWriteAdapter,
    MigrationOrchestrator
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dirs():
    """创建临时目录结构"""
    temp_root = tempfile.mkdtemp()

    chroma_path = os.path.join(temp_root, "chroma_db")
    lance_path = os.path.join(temp_root, "lance_db")
    backup_dir = os.path.join(temp_root, "backups")
    export_file = os.path.join(temp_root, "export.jsonl")

    os.makedirs(chroma_path, exist_ok=True)
    os.makedirs(lance_path, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)

    yield {
        "root": temp_root,
        "chroma": chroma_path,
        "lance": lance_path,
        "backup": backup_dir,
        "export": export_file
    }

    # 清理
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)


@pytest.fixture
def migration_config(temp_dirs):
    """创建迁移配置"""
    return MigrationConfig(
        chromadb_path=temp_dirs["chroma"],
        lancedb_path=temp_dirs["lance"],
        export_file=temp_dirs["export"],
        backup_dir=temp_dirs["backup"],
        batch_size=100,
        validation_sample_size=10
    )


@pytest.fixture
def sample_documents():
    """生成样本文档数据"""
    np.random.seed(42)

    docs = []
    for i in range(50):
        embedding = np.random.rand(1536).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize

        docs.append({
            "doc_id": f"doc-{i:04d}",
            "content": f"这是测试文档 #{i}，用于验证迁移功能。",
            "metadata": {
                "canvas_file": f"test_canvas_{i % 5}.canvas",
                "node_id": f"node-{i}",
                "timestamp": datetime.now().isoformat()
            },
            "embedding": embedding.tolist()
        })

    return docs


# ============================================================================
# AC 3.1: ChromaDB数据完整导出
# ============================================================================

class TestChromaDBExporter:
    """测试ChromaDB导出功能"""

    def test_create_sample_data(self, migration_config, sample_documents):
        """测试创建样本数据"""
        exporter = ChromaDBExporter(migration_config)

        # Mock ChromaDB client
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.create_collection.return_value = mock_collection

        exporter.client = mock_client

        # 调用创建样本数据
        exporter._create_sample_data("test_collection", num_docs=10)

        # 验证collection被创建
        mock_client.create_collection.assert_called_once_with("test_collection")

        # 验证文档被添加
        mock_collection.add.assert_called()
        call_args = mock_collection.add.call_args
        assert len(call_args[1]["ids"]) == 10
        assert len(call_args[1]["documents"]) == 10
        assert len(call_args[1]["embeddings"]) == 10

    def test_export_collection(self, migration_config, sample_documents, temp_dirs):
        """测试导出单个collection"""
        exporter = ChromaDBExporter(migration_config)

        # Mock ChromaDB collection
        mock_client = Mock()
        mock_collection = Mock()

        # 准备返回数据
        mock_collection.get.return_value = {
            "ids": [doc["doc_id"] for doc in sample_documents[:10]],
            "documents": [doc["content"] for doc in sample_documents[:10]],
            "metadatas": [doc["metadata"] for doc in sample_documents[:10]],
            "embeddings": [doc["embedding"] for doc in sample_documents[:10]]
        }
        mock_collection.count.return_value = 10

        mock_client.get_collection.return_value = mock_collection
        exporter.client = mock_client

        # 执行导出
        export_file = os.path.join(temp_dirs["root"], "test_export.jsonl")
        result = exporter.export_collection("test_collection", export_file)

        # 验证结果
        assert result["status"] == "success"
        assert result["total_docs"] == 10
        assert os.path.exists(export_file)

        # 验证文件内容
        with open(export_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 10

            # 验证第一条记录
            first_doc = json.loads(lines[0])
            assert "doc_id" in first_doc
            assert "content" in first_doc
            assert "metadata" in first_doc
            assert "embedding" in first_doc
            assert len(first_doc["embedding"]) == 1536


# ============================================================================
# AC 3.2: LanceDB数据完整导入
# ============================================================================

class TestLanceDBImporter:
    """测试LanceDB导入功能"""

    def test_import_collection(self, migration_config, sample_documents, temp_dirs):
        """测试导入数据到LanceDB"""
        # 创建导出文件
        export_file = os.path.join(temp_dirs["root"], "test_import.jsonl")
        with open(export_file, "w", encoding="utf-8") as f:
            for doc in sample_documents[:10]:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        importer = LanceDBImporter(migration_config)

        # Mock LanceDB
        mock_db = Mock()
        mock_table = Mock()
        mock_db.create_table.return_value = mock_table

        importer.db = mock_db

        # 执行导入
        imported_count = importer.import_collection(export_file, "test_table")

        # 验证结果
        assert imported_count == 10
        mock_db.create_table.assert_called_once()

        # 验证schema映射
        call_args = mock_db.create_table.call_args
        table_data = call_args[1]["data"]
        assert len(table_data) == 10

        # 验证第一条记录的schema
        first_record = table_data[0]
        assert "doc_id" in first_record
        assert "content" in first_record
        assert "vector" in first_record  # ChromaDB的"embedding"映射为"vector"
        assert "canvas_file" in first_record
        assert "metadata_json" in first_record
        assert len(first_record["vector"]) == 1536


# ============================================================================
# AC 3.3: 数据一致性校验
# ============================================================================

class TestDataConsistencyValidator:
    """测试数据一致性校验"""

    def test_validate_collection(self, migration_config, sample_documents):
        """测试一致性校验 - 100%一致"""
        validator = DataConsistencyValidator(migration_config)

        # Mock ChromaDB
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()

        sample_size = 5
        docs = sample_documents[:sample_size]

        mock_chroma_collection.get.return_value = {
            "ids": [doc["doc_id"] for doc in docs],
            "documents": [doc["content"] for doc in docs],
            "metadatas": [doc["metadata"] for doc in docs],
            "embeddings": [doc["embedding"] for doc in docs]
        }
        mock_chroma_client.get_collection.return_value = mock_chroma_collection

        # Mock LanceDB
        mock_lance_db = Mock()
        mock_lance_table = Mock()

        # 模拟LanceDB返回相同的数据
        def mock_search_where(query):
            doc_id = query.split("'")[1]
            for doc in docs:
                if doc["doc_id"] == doc_id:
                    return Mock(limit=lambda x: Mock(to_list=lambda: [{
                        "doc_id": doc["doc_id"],
                        "content": doc["content"],
                        "vector": doc["embedding"],
                        "metadata_json": json.dumps(doc["metadata"])
                    }]))
            return Mock(limit=lambda x: Mock(to_list=lambda: []))

        mock_lance_table.search.return_value.where = mock_search_where
        mock_lance_db.open_table.return_value = mock_lance_table

        validator.chroma_client = mock_chroma_client
        validator.lance_db = mock_lance_db

        # 执行校验
        result = validator.validate_collection("test_collection", "test_table", sample_size)

        # 验证结果
        assert result["total_validated"] == sample_size
        assert result["errors"] == 0
        assert result["consistency_rate"] == "100.00%"

    def test_validate_vector_similarity_threshold(self, migration_config):
        """测试向量相似度阈值检测"""
        validator = DataConsistencyValidator(migration_config)

        # 创建相似但不完全相同的向量
        np.random.seed(42)
        original_vec = np.random.rand(1536).astype(np.float32)
        original_vec = original_vec / np.linalg.norm(original_vec)

        # 创建稍微偏移的向量 (相似度约0.95)
        noise = np.random.rand(1536).astype(np.float32) * 0.1
        modified_vec = original_vec + noise
        modified_vec = modified_vec / np.linalg.norm(modified_vec)

        # Mock数据
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_collection.get.return_value = {
            "ids": ["doc-001"],
            "documents": ["test content"],
            "metadatas": [{"test": "metadata"}],
            "embeddings": [original_vec.tolist()]
        }
        mock_chroma_client.get_collection.return_value = mock_chroma_collection

        mock_lance_db = Mock()
        mock_lance_table = Mock()
        mock_lance_table.search.return_value.where.return_value.limit.return_value.to_list.return_value = [{
            "doc_id": "doc-001",
            "content": "test content",
            "vector": modified_vec.tolist(),
            "metadata_json": '{"test": "metadata"}'
        }]
        mock_lance_db.open_table.return_value = mock_lance_table

        validator.chroma_client = mock_chroma_client
        validator.lance_db = mock_lance_db

        # 执行校验
        result = validator.validate_collection("test_collection", "test_table", 1)

        # 应该检测到相似度低于0.99
        assert result["errors"] > 0


# ============================================================================
# AC 3.4: 双写模式运行
# ============================================================================

class TestDualWriteAdapter:
    """测试双写适配器"""

    def test_dual_write_success(self, migration_config, sample_documents):
        """测试双写成功场景"""
        adapter = DualWriteAdapter(migration_config, enable_fallback=True)

        # Mock ChromaDB
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection

        # Mock LanceDB
        mock_lance_db = Mock()
        mock_lance_table = Mock()
        mock_lance_db.open_table.return_value = mock_lance_table

        adapter.chroma_client = mock_chroma_client
        adapter.lance_db = mock_lance_db

        # 执行双写
        doc = sample_documents[0]
        result = adapter.add_document(
            collection_name="test_collection",
            doc_id=doc["doc_id"],
            content=doc["content"],
            metadata=doc["metadata"],
            embedding=doc["embedding"]
        )

        # 验证结果
        assert result["chromadb"] is True
        assert result["lancedb"] is True

        # 验证统计
        stats = adapter.get_statistics()
        assert stats["total"] == 1
        assert stats["both_success"] == 1
        assert stats["success_rate"] == "100.00%"

    def test_dual_write_fallback(self, migration_config, sample_documents):
        """测试降级模式（单写）"""
        adapter = DualWriteAdapter(migration_config, enable_fallback=True)

        # Mock ChromaDB - 成功
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection

        # Mock LanceDB - 失败
        mock_lance_db = Mock()
        mock_lance_db.open_table.side_effect = Exception("LanceDB connection failed")

        adapter.chroma_client = mock_chroma_client
        adapter.lance_db = mock_lance_db

        # 执行双写（应该降级到ChromaDB单写）
        doc = sample_documents[0]
        result = adapter.add_document(
            collection_name="test_collection",
            doc_id=doc["doc_id"],
            content=doc["content"],
            metadata=doc["metadata"],
            embedding=doc["embedding"]
        )

        # 验证结果
        assert result["chromadb"] is True
        assert result["lancedb"] is False

        # 验证统计
        stats = adapter.get_statistics()
        assert stats["chroma_success"] == 1
        assert stats["lance_failed"] == 1
        assert stats["both_success"] == 0

    def test_batch_dual_write(self, migration_config, sample_documents):
        """测试批量双写"""
        adapter = DualWriteAdapter(migration_config, enable_fallback=True)

        # Mock数据库
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection

        mock_lance_db = Mock()
        mock_lance_table = Mock()
        mock_lance_db.open_table.return_value = mock_lance_table

        adapter.chroma_client = mock_chroma_client
        adapter.lance_db = mock_lance_db

        # 执行批量双写
        batch_docs = sample_documents[:10]
        result = adapter.batch_add_documents("test_collection", batch_docs)

        # 验证结果
        assert result["total"] == 10
        assert result["both_success"] == 10
        assert result["chromadb_success"] == 10
        assert result["lancedb_success"] == 10


# ============================================================================
# AC 3.5: Rollback plan验证
# ============================================================================

class TestBackupManager:
    """测试备份和回滚管理"""

    def test_backup_chromadb(self, migration_config, temp_dirs):
        """测试ChromaDB备份"""
        # 创建一些测试文件在ChromaDB目录
        test_file = os.path.join(temp_dirs["chroma"], "test_data.db")
        with open(test_file, "w") as f:
            f.write("test data")

        backup_mgr = BackupManager(migration_config)

        # 执行备份
        backup_file = backup_mgr.backup_chromadb()

        # 验证备份文件存在
        assert os.path.exists(backup_file)
        assert backup_file.endswith(".tar.gz")

        # 验证备份文件不为空
        assert os.path.getsize(backup_file) > 0

    def test_restore_chromadb(self, migration_config, temp_dirs):
        """测试从备份恢复"""
        # 创建测试数据并备份
        test_file = os.path.join(temp_dirs["chroma"], "important_data.db")
        test_content = "critical data"

        with open(test_file, "w") as f:
            f.write(test_content)

        backup_mgr = BackupManager(migration_config)
        backup_file = backup_mgr.backup_chromadb()

        # 删除原始数据
        os.remove(test_file)
        assert not os.path.exists(test_file)

        # 执行恢复
        success = backup_mgr.restore_chromadb(backup_file)

        # 验证恢复成功
        assert success is True
        assert os.path.exists(test_file)

        # 验证数据完整性
        with open(test_file, "r") as f:
            restored_content = f.read()
            assert restored_content == test_content


# ============================================================================
# 集成测试
# ============================================================================

class TestMigrationOrchestrator:
    """测试完整迁移流程"""

    @patch('migrate_chromadb_to_lancedb.chromadb')
    @patch('migrate_chromadb_to_lancedb.lancedb')
    def test_full_migration_flow(self, mock_lancedb, mock_chromadb, migration_config, sample_documents, temp_dirs):
        """测试端到端迁移流程"""
        # Mock ChromaDB
        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()

        mock_chroma_collection.get.return_value = {
            "ids": [doc["doc_id"] for doc in sample_documents[:10]],
            "documents": [doc["content"] for doc in sample_documents[:10]],
            "metadatas": [doc["metadata"] for doc in sample_documents[:10]],
            "embeddings": [doc["embedding"] for doc in sample_documents[:10]]
        }
        mock_chroma_collection.count.return_value = 10

        mock_chroma_client.get_collection.return_value = mock_chroma_collection
        mock_chroma_client.list_collections.return_value = [Mock(name="canvas_nodes")]

        mock_chromadb.PersistentClient.return_value = mock_chroma_client

        # Mock LanceDB
        mock_lance_db_instance = Mock()
        mock_lance_table = Mock()
        mock_lance_db_instance.create_table.return_value = mock_lance_table
        mock_lance_db_instance.open_table.return_value = mock_lance_table

        mock_lancedb.connect.return_value = mock_lance_db_instance

        # 创建一些测试文件用于备份
        test_file = os.path.join(temp_dirs["chroma"], "test.db")
        with open(test_file, "w") as f:
            f.write("test")

        # 执行完整迁移
        orchestrator = MigrationOrchestrator(migration_config)
        report = orchestrator.run_full_migration()

        # 验证报告
        assert report["status"] == "success"
        assert "backup" in report["steps"]
        assert "export" in report["steps"]
        assert "import" in report["steps"]
        assert "validate" in report["steps"]

        assert report["steps"]["backup"]["status"] == "success"
        assert report["steps"]["export"]["status"] == "success"
        assert report["steps"]["import"]["status"] == "success"


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能和规模测试"""

    def test_large_batch_export(self, migration_config, temp_dirs):
        """测试大批量导出性能"""
        exporter = ChromaDBExporter(migration_config)

        # Mock大量数据
        large_batch_size = 1000

        mock_client = Mock()
        mock_collection = Mock()

        # 生成大批量mock数据
        np.random.seed(42)
        mock_collection.get.return_value = {
            "ids": [f"doc-{i:06d}" for i in range(large_batch_size)],
            "documents": [f"Document {i}" for i in range(large_batch_size)],
            "metadatas": [{"index": i} for i in range(large_batch_size)],
            "embeddings": [np.random.rand(1536).tolist() for _ in range(large_batch_size)]
        }
        mock_collection.count.return_value = large_batch_size

        mock_client.get_collection.return_value = mock_collection
        exporter.client = mock_client

        # 执行导出
        export_file = os.path.join(temp_dirs["root"], "large_export.jsonl")

        import time
        start_time = time.time()
        result = exporter.export_collection("test_collection", export_file)
        duration = time.time() - start_time

        # 验证结果
        assert result["status"] == "success"
        assert result["total_docs"] == large_batch_size

        # 性能断言：1000个文档应该在5秒内完成
        assert duration < 5.0, f"Export took {duration:.2f}s, expected < 5s"


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理和边界情况"""

    def test_export_nonexistent_collection(self, migration_config, temp_dirs):
        """测试导出不存在的collection"""
        exporter = ChromaDBExporter(migration_config)

        mock_client = Mock()
        mock_client.get_collection.side_effect = Exception("Collection not found")
        exporter.client = mock_client

        # 执行导出
        export_file = os.path.join(temp_dirs["root"], "test.jsonl")
        result = exporter.export_collection("nonexistent_collection", export_file)

        # 应该返回错误
        assert result["status"] == "error"
        assert "Collection not found" in result["error"]

    def test_restore_from_invalid_backup(self, migration_config, temp_dirs):
        """测试从无效备份恢复"""
        backup_mgr = BackupManager(migration_config)

        # 尝试从不存在的备份恢复
        success = backup_mgr.restore_chromadb("nonexistent_backup.tar.gz")

        # 应该返回False
        assert success is False


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
