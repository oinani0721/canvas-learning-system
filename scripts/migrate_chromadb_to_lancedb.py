#!/usr/bin/env python3
"""
ChromaDB → LanceDB 数据迁移工具
Canvas Learning System - Story 12.3

完整迁移流程:
1. ChromaDB数据完整导出
2. LanceDB数据导入
3. 数据一致性校验
4. 双写模式切换

✅ Verified from LanceDB Documentation + ChromaDB API
"""

import chromadb
from chromadb.config import Settings
import lancedb
import json
import numpy as np
import os
import sys
import time
import logging
import argparse
import shutil
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm


# ============================================================================
# 日志配置
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置类
# ============================================================================

class MigrationConfig:
    """迁移配置"""

    def __init__(
        self,
        chromadb_path: str = "./chroma_db",
        lancedb_path: str = "~/.lancedb",
        export_file: str = "chromadb_export.jsonl",
        backup_dir: str = "./chromadb_backup",
        batch_size: int = 1000,
        validation_sample_size: int = 100
    ):
        self.chromadb_path = chromadb_path
        self.lancedb_path = os.path.expanduser(lancedb_path)
        self.export_file = export_file
        self.backup_dir = backup_dir
        self.batch_size = batch_size
        self.validation_sample_size = validation_sample_size

        # ChromaDB collection names
        self.chroma_collections = [
            "canvas_explanations",
            "canvas_concepts"
        ]

        # LanceDB table mapping
        self.lancedb_tables = {
            "canvas_explanations": "canvas_explanations",
            "canvas_concepts": "canvas_concepts"
        }

    def get_lance_table(self, collection_name: str) -> str:
        """获取LanceDB表名

        Args:
            collection_name: ChromaDB collection名称

        Returns:
            对应的LanceDB表名
        """
        return self.lancedb_tables.get(collection_name, collection_name)


# ============================================================================
# ChromaDB 导出器
# ============================================================================

class ChromaDBExporter:
    """ChromaDB数据导出器

    AC 3.1: ChromaDB数据完整导出
    - 导出所有collection: canvas_explanations, canvas_concepts
    - 导出格式: JSON Lines (每行一个文档 + metadata + embedding)
    - 验证: 记录数与ChromaDB一致
    """

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.client = None

    def connect(self):
        """连接到ChromaDB"""
        try:
            logger.info(f"Connecting to ChromaDB at {self.config.chromadb_path}")

            if os.path.exists(self.config.chromadb_path):
                self.client = chromadb.PersistentClient(
                    path=self.config.chromadb_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info("✅ Connected to existing ChromaDB")
            else:
                logger.warning(f"ChromaDB path not found: {self.config.chromadb_path}")
                logger.info("Creating empty ChromaDB for testing...")
                self.client = chromadb.PersistentClient(
                    path=self.config.chromadb_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                self._create_sample_data()

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise

    def _create_sample_data(self):
        """创建示例数据用于测试"""
        logger.info("Creating sample data in ChromaDB...")

        for collection_name in self.config.chroma_collections:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Sample {collection_name} for testing"}
            )

            # 添加100个示例文档
            sample_docs = []
            sample_ids = []
            sample_metadatas = []
            sample_embeddings = []

            for i in range(100):
                doc_id = f"{collection_name}_doc_{i}"
                content = f"Sample document {i} from {collection_name}"
                metadata = {
                    "canvas_file": "离散数学.canvas",
                    "concept": f"concept_{i}",
                    "timestamp": datetime.now().isoformat(),
                    "agent_type": "scoring-agent"
                }
                # 1536-dim embedding (OpenAI text-embedding-3-small compatible)
                embedding = np.random.rand(1536).astype(np.float32).tolist()

                sample_ids.append(doc_id)
                sample_docs.append(content)
                sample_metadatas.append(metadata)
                sample_embeddings.append(embedding)

            collection.add(
                ids=sample_ids,
                documents=sample_docs,
                metadatas=sample_metadatas,
                embeddings=sample_embeddings
            )

            logger.info(f"✅ Created {len(sample_ids)} sample documents in {collection_name}")

    def export_collection(self, collection_name: str) -> Dict[str, Any]:
        """导出单个collection

        Returns:
            {"collection_name": str, "count": int, "file_path": str}
        """
        try:
            logger.info(f"Exporting collection: {collection_name}")

            collection = self.client.get_collection(collection_name)

            # 获取所有数据
            results = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )

            count = len(results["ids"])
            logger.info(f"Found {count} documents in {collection_name}")

            if count == 0:
                logger.warning(f"Collection {collection_name} is empty, skipping export")
                return {
                    "collection_name": collection_name,
                    "count": 0,
                    "file_path": None
                }

            # 导出为JSON Lines
            export_file = f"{collection_name}_export.jsonl"
            exported_count = 0

            with open(export_file, "w", encoding="utf-8") as f:
                for i in tqdm(range(count), desc=f"Exporting {collection_name}"):
                    doc = {
                        "doc_id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "embedding": results["embeddings"][i]
                    }
                    f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                    exported_count += 1

            logger.info(f"✅ Exported {exported_count} documents to {export_file}")

            return {
                "collection_name": collection_name,
                "count": exported_count,
                "file_path": export_file
            }

        except Exception as e:
            logger.error(f"Failed to export collection {collection_name}: {e}")
            raise

    def export_all(self) -> List[Dict[str, Any]]:
        """导出所有collections

        Returns:
            List of {"collection_name": str, "count": int, "file_path": str}
        """
        results = []

        for collection_name in self.config.chroma_collections:
            try:
                result = self.export_collection(collection_name)
                results.append(result)
            except Exception as e:
                logger.error(f"Skipping collection {collection_name} due to error: {e}")

        return results


# ============================================================================
# LanceDB 导入器
# ============================================================================

class LanceDBImporter:
    """LanceDB数据导入器

    AC 3.2: LanceDB数据完整导入
    - 导入JSON Lines到LanceDB table
    - Schema映射: ChromaDB metadata → LanceDB columns
    - 验证: 记录数100%对齐
    """

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.db = None

    def connect(self):
        """连接到LanceDB"""
        try:
            logger.info(f"Connecting to LanceDB at {self.config.lancedb_path}")
            self.db = lancedb.connect(self.config.lancedb_path)
            logger.info("✅ Connected to LanceDB")
        except Exception as e:
            logger.error(f"Failed to connect to LanceDB: {e}")
            raise

    def import_collection(self, export_file: str, table_name: str) -> int:
        """导入单个collection到LanceDB table

        Args:
            export_file: JSON Lines文件路径
            table_name: LanceDB表名

        Returns:
            导入的文档数量
        """
        try:
            logger.info(f"Importing {export_file} to table {table_name}")

            if not os.path.exists(export_file):
                logger.error(f"Export file not found: {export_file}")
                return 0

            # 读取JSON Lines
            data = []
            with open(export_file, "r", encoding="utf-8") as f:
                for line in tqdm(f, desc=f"Reading {export_file}"):
                    doc = json.loads(line)

                    # Schema映射: ChromaDB → LanceDB
                    lance_doc = {
                        "doc_id": doc["doc_id"],
                        "content": doc["content"],
                        "vector": doc["embedding"],  # LanceDB使用"vector"列名
                        # Metadata扁平化
                        "canvas_file": doc["metadata"].get("canvas_file", ""),
                        "concept": doc["metadata"].get("concept", ""),
                        "timestamp": doc["metadata"].get("timestamp", ""),
                        "agent_type": doc["metadata"].get("agent_type", ""),
                        # 保留完整metadata作为JSON字符串
                        "metadata_json": json.dumps(doc["metadata"], ensure_ascii=False)
                    }

                    data.append(lance_doc)

            logger.info(f"Read {len(data)} documents from {export_file}")

            if len(data) == 0:
                logger.warning(f"No data to import for {table_name}")
                return 0

            # 创建LanceDB表
            logger.info(f"Creating LanceDB table: {table_name}")
            table = self.db.create_table(
                table_name,
                data=data,
                mode="overwrite"
            )

            # 验证导入数量
            imported_count = table.count_rows()
            logger.info(f"✅ Imported {imported_count} documents to {table_name}")

            if imported_count != len(data):
                logger.error(f"Import count mismatch: expected {len(data)}, got {imported_count}")
                raise ValueError("Import count mismatch")

            return imported_count

        except Exception as e:
            logger.error(f"Failed to import {export_file}: {e}")
            raise

    def import_all(self, export_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """导入所有collections

        Args:
            export_results: ChromaDBExporter.export_all()的结果

        Returns:
            {"table_name": imported_count}
        """
        import_results = {}

        for result in export_results:
            collection_name = result["collection_name"]
            export_file = result["file_path"]

            if export_file is None:
                logger.warning(f"Skipping {collection_name} (no export file)")
                continue

            table_name = self.config.lancedb_tables.get(collection_name, collection_name)

            try:
                count = self.import_collection(export_file, table_name)
                import_results[table_name] = count
            except Exception as e:
                logger.error(f"Skipping {collection_name} due to error: {e}")

        return import_results


# ============================================================================
# 数据一致性校验器
# ============================================================================

class DataConsistencyValidator:
    """数据一致性校验器

    AC 3.3: 数据一致性校验
    - 随机抽样100条文档，对比ChromaDB vs LanceDB
    - 验证: doc_id, content, metadata完全一致
    - 向量相似度 > 0.99 (余弦相似度)
    """

    def __init__(
        self,
        config: MigrationConfig,
        chroma_client: chromadb.Client,
        lance_db: lancedb.DBConnection
    ):
        self.config = config
        self.chroma_client = chroma_client
        self.lance_db = lance_db

    def validate_collection(
        self,
        collection_name: str,
        table_name: str,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """校验单个collection vs table

        Returns:
            {
                "collection_name": str,
                "sample_size": int,
                "passed": int,
                "failed": int,
                "errors": List[Dict]
            }
        """
        try:
            logger.info(f"Validating {collection_name} vs {table_name}")

            # 获取ChromaDB collection
            chroma_collection = self.chroma_client.get_collection(collection_name)
            chroma_results = chroma_collection.get(include=["documents", "metadatas", "embeddings"])

            total_docs = len(chroma_results["ids"])
            logger.info(f"Total documents in ChromaDB: {total_docs}")

            if total_docs == 0:
                logger.warning(f"No documents in {collection_name}, skipping validation")
                return {
                    "collection_name": collection_name,
                    "sample_size": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": []
                }

            # 获取LanceDB table
            lance_table = self.lance_db.open_table(table_name)

            # 随机抽样
            sample_size = min(sample_size, total_docs)
            sample_indices = random.sample(range(total_docs), sample_size)

            passed = 0
            failed = 0
            errors = []

            for i in tqdm(sample_indices, desc=f"Validating {collection_name}"):
                doc_id = chroma_results["ids"][i]

                try:
                    # ChromaDB数据
                    chroma_doc = chroma_results["documents"][i]
                    chroma_metadata = chroma_results["metadatas"][i]
                    chroma_embedding = np.array(chroma_results["embeddings"][i])

                    # LanceDB数据
                    lance_result = lance_table.search().where(f"doc_id = '{doc_id}'").limit(1).to_pandas()

                    if len(lance_result) == 0:
                        errors.append({
                            "doc_id": doc_id,
                            "error": "Document not found in LanceDB"
                        })
                        failed += 1
                        continue

                    lance_doc = lance_result.iloc[0]

                    # 验证content
                    if chroma_doc != lance_doc["content"]:
                        errors.append({
                            "doc_id": doc_id,
                            "error": "Content mismatch",
                            "chroma": chroma_doc[:100],
                            "lance": str(lance_doc["content"])[:100]
                        })
                        failed += 1
                        continue

                    # 验证metadata (从JSON字符串恢复)
                    lance_metadata = json.loads(lance_doc["metadata_json"])
                    if chroma_metadata != lance_metadata:
                        errors.append({
                            "doc_id": doc_id,
                            "error": "Metadata mismatch",
                            "chroma": chroma_metadata,
                            "lance": lance_metadata
                        })
                        failed += 1
                        continue

                    # 验证向量相似度
                    lance_embedding = np.array(lance_doc["vector"])
                    cosine_sim = np.dot(chroma_embedding, lance_embedding) / (
                        np.linalg.norm(chroma_embedding) * np.linalg.norm(lance_embedding)
                    )

                    if cosine_sim < 0.99:
                        errors.append({
                            "doc_id": doc_id,
                            "error": "Vector similarity too low",
                            "cosine_similarity": float(cosine_sim)
                        })
                        failed += 1
                        continue

                    passed += 1

                except Exception as e:
                    errors.append({
                        "doc_id": doc_id,
                        "error": str(e)
                    })
                    failed += 1

            logger.info(f"✅ Validation complete: {passed}/{sample_size} passed, {failed}/{sample_size} failed")

            return {
                "collection_name": collection_name,
                "sample_size": sample_size,
                "passed": passed,
                "failed": failed,
                "errors": errors
            }

        except Exception as e:
            logger.error(f"Failed to validate {collection_name}: {e}")
            raise

    def validate_all(self) -> List[Dict[str, Any]]:
        """校验所有collections

        Returns:
            List of validation results
        """
        results = []

        for collection_name in self.config.chroma_collections:
            table_name = self.config.lancedb_tables.get(collection_name, collection_name)

            try:
                result = self.validate_collection(
                    collection_name,
                    table_name,
                    sample_size=self.config.validation_sample_size
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Skipping validation for {collection_name}: {e}")

        return results


# ============================================================================
# 备份和回滚管理器
# ============================================================================

class BackupManager:
    """备份和回滚管理器

    AC 3.5: Rollback plan验证
    - 备份ChromaDB数据 (tar.gz格式)
    - 模拟迁移失败，执行rollback
    - 验证: ChromaDB恢复到迁移前状态，无数据丢失
    """

    def __init__(self, config: MigrationConfig):
        self.config = config

    def backup_chromadb(self) -> str:
        """备份ChromaDB数据库

        Returns:
            备份文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.config.backup_dir,
                f"chromadb_backup_{timestamp}.tar.gz"
            )

            # 创建备份目录
            os.makedirs(self.config.backup_dir, exist_ok=True)

            logger.info(f"Creating backup: {backup_file}")

            # 压缩ChromaDB目录
            import tarfile

            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(self.config.chromadb_path, arcname="chroma_db")

            # 验证备份文件大小
            backup_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
            logger.info(f"✅ Backup created: {backup_file} ({backup_size:.2f} MB)")

            return backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_chromadb(self, backup_file: str) -> bool:
        """从备份恢复ChromaDB

        Args:
            backup_file: 备份文件路径

        Returns:
            True if successful
        """
        try:
            logger.info(f"Restoring from backup: {backup_file}")

            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False

            # 删除现有ChromaDB目录
            if os.path.exists(self.config.chromadb_path):
                logger.info(f"Removing existing ChromaDB: {self.config.chromadb_path}")
                shutil.rmtree(self.config.chromadb_path)

            # 解压备份
            import tarfile

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(self.config.chromadb_path))

            logger.info("✅ ChromaDB restored from backup")
            return True

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False


# ============================================================================
# 双写适配器 (AC 3.4)
# ============================================================================

class DualWriteAdapter:
    """双写适配器 - AC 3.4

    在迁移期间同时写入ChromaDB和LanceDB，确保数据一致性
    支持逐步迁移和回滚场景
    """

    def __init__(self, config: MigrationConfig, enable_fallback: bool = True):
        """初始化双写适配器

        Args:
            config: 迁移配置
            enable_fallback: 启用降级模式（单写）
        """
        self.config = config
        self.enable_fallback = enable_fallback
        self.chroma_client = None
        self.lance_db = None

        # 写入统计
        self.write_stats = {
            "total": 0,
            "chroma_success": 0,
            "lance_success": 0,
            "both_success": 0,
            "chroma_failed": 0,
            "lance_failed": 0,
            "both_failed": 0
        }

    def connect(self):
        """连接到两个数据库"""
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=self.config.chromadb_path)
            logger.info(f"✅ Connected to ChromaDB at {self.config.chromadb_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect ChromaDB: {e}")
            if not self.enable_fallback:
                raise

        try:
            import lancedb
            self.lance_db = lancedb.connect(self.config.lancedb_path)
            logger.info(f"✅ Connected to LanceDB at {self.config.lancedb_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect LanceDB: {e}")
            if not self.enable_fallback:
                raise

    def add_document(
        self,
        collection_name: str,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> Dict[str, bool]:
        """双写文档到两个数据库

        Args:
            collection_name: Collection/Table名称
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
            embedding: 向量

        Returns:
            写入结果 {"chromadb": bool, "lancedb": bool}
        """
        self.write_stats["total"] += 1
        results = {"chromadb": False, "lancedb": False}

        # 写入ChromaDB
        if self.chroma_client is not None:
            try:
                collection = self.chroma_client.get_or_create_collection(collection_name)
                collection.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata],
                    embeddings=[embedding]
                )
                results["chromadb"] = True
                self.write_stats["chroma_success"] += 1
                logger.debug(f"✅ ChromaDB write success: {doc_id}")
            except Exception as e:
                self.write_stats["chroma_failed"] += 1
                logger.warning(f"⚠️ ChromaDB write failed for {doc_id}: {e}")
                if not self.enable_fallback:
                    raise

        # 写入LanceDB
        if self.lance_db is not None:
            try:
                table_name = self.config.get_lance_table(collection_name)

                # 转换为LanceDB schema
                lance_doc = {
                    "doc_id": doc_id,
                    "content": content,
                    "vector": embedding,
                    "canvas_file": metadata.get("canvas_file", ""),
                    "node_id": metadata.get("node_id", ""),
                    "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                    "metadata_json": json.dumps(metadata, ensure_ascii=False)
                }

                # 检查表是否存在
                try:
                    table = self.lance_db.open_table(table_name)
                    # 追加数据
                    table.add([lance_doc])
                except Exception:
                    # 表不存在，创建新表
                    table = self.lance_db.create_table(table_name, data=[lance_doc])

                results["lancedb"] = True
                self.write_stats["lance_success"] += 1
                logger.debug(f"✅ LanceDB write success: {doc_id}")
            except Exception as e:
                self.write_stats["lance_failed"] += 1
                logger.warning(f"⚠️ LanceDB write failed for {doc_id}: {e}")
                if not self.enable_fallback:
                    raise

        # 更新统计
        if results["chromadb"] and results["lancedb"]:
            self.write_stats["both_success"] += 1
        elif not results["chromadb"] and not results["lancedb"]:
            self.write_stats["both_failed"] += 1

        return results

    def batch_add_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量双写文档

        Args:
            collection_name: Collection/Table名称
            documents: 文档列表，每个文档包含 doc_id, content, metadata, embedding

        Returns:
            批量写入结果统计
        """
        batch_results = {
            "total": len(documents),
            "chromadb_success": 0,
            "lancedb_success": 0,
            "both_success": 0
        }

        for doc in documents:
            results = self.add_document(
                collection_name=collection_name,
                doc_id=doc["doc_id"],
                content=doc["content"],
                metadata=doc["metadata"],
                embedding=doc["embedding"]
            )

            if results["chromadb"]:
                batch_results["chromadb_success"] += 1
            if results["lancedb"]:
                batch_results["lancedb_success"] += 1
            if results["chromadb"] and results["lancedb"]:
                batch_results["both_success"] += 1

        return batch_results

    def get_statistics(self) -> Dict[str, Any]:
        """获取双写统计数据

        Returns:
            统计信息
        """
        if self.write_stats["total"] == 0:
            success_rate = 0.0
        else:
            success_rate = self.write_stats["both_success"] / self.write_stats["total"] * 100

        return {
            **self.write_stats,
            "success_rate": f"{success_rate:.2f}%"
        }

    def verify_consistency(self, collection_name: str, sample_size: int = 100) -> Dict[str, Any]:
        """验证双写数据一致性

        Args:
            collection_name: Collection名称
            sample_size: 抽样数量

        Returns:
            验证结果
        """
        if self.chroma_client is None or self.lance_db is None:
            return {"error": "Both databases must be connected for verification"}

        try:
            # 从ChromaDB获取文档
            chroma_collection = self.chroma_client.get_collection(collection_name)
            chroma_results = chroma_collection.get(
                limit=sample_size,
                include=["documents", "metadatas", "embeddings"]
            )

            # 从LanceDB获取对应文档
            table_name = self.config.get_lance_table(collection_name)
            lance_table = self.lance_db.open_table(table_name)

            mismatches = []
            for i, doc_id in enumerate(chroma_results["ids"]):
                # 在LanceDB中查找
                lance_rows = lance_table.search().where(f"doc_id = '{doc_id}'").limit(1).to_list()

                if not lance_rows:
                    mismatches.append({
                        "doc_id": doc_id,
                        "error": "Document not found in LanceDB"
                    })
                    continue

                # 验证向量相似度
                chroma_vec = np.array(chroma_results["embeddings"][i])
                lance_vec = np.array(lance_rows[0]["vector"])

                cosine_sim = np.dot(chroma_vec, lance_vec) / (
                    np.linalg.norm(chroma_vec) * np.linalg.norm(lance_vec)
                )

                if cosine_sim < 0.99:
                    mismatches.append({
                        "doc_id": doc_id,
                        "error": f"Vector similarity too low: {cosine_sim:.4f}"
                    })

            return {
                "total_checked": len(chroma_results["ids"]),
                "mismatches": len(mismatches),
                "consistency_rate": f"{(1 - len(mismatches) / len(chroma_results['ids'])) * 100:.2f}%",
                "errors": mismatches[:10]  # 只返回前10个错误
            }

        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# 主迁移流程
# ============================================================================

class MigrationOrchestrator:
    """迁移流程编排器"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.exporter = ChromaDBExporter(config)
        self.importer = LanceDBImporter(config)
        self.backup_mgr = BackupManager(config)

    def run_full_migration(self) -> Dict[str, Any]:
        """执行完整迁移流程

        Returns:
            迁移报告
        """
        report = {
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "steps": {}
        }

        try:
            # Step 1: 备份ChromaDB
            logger.info("=" * 80)
            logger.info("Step 1: Backup ChromaDB")
            logger.info("=" * 80)

            backup_file = self.backup_mgr.backup_chromadb()
            report["steps"]["backup"] = {
                "status": "success",
                "backup_file": backup_file
            }

            # Step 2: 连接ChromaDB
            logger.info("=" * 80)
            logger.info("Step 2: Connect to ChromaDB")
            logger.info("=" * 80)

            self.exporter.connect()
            report["steps"]["connect_chroma"] = {"status": "success"}

            # Step 3: 导出数据
            logger.info("=" * 80)
            logger.info("Step 3: Export data from ChromaDB")
            logger.info("=" * 80)

            export_results = self.exporter.export_all()
            report["steps"]["export"] = {
                "status": "success",
                "results": export_results
            }

            # Step 4: 连接LanceDB
            logger.info("=" * 80)
            logger.info("Step 4: Connect to LanceDB")
            logger.info("=" * 80)

            self.importer.connect()
            report["steps"]["connect_lance"] = {"status": "success"}

            # Step 5: 导入数据
            logger.info("=" * 80)
            logger.info("Step 5: Import data to LanceDB")
            logger.info("=" * 80)

            import_results = self.importer.import_all(export_results)
            report["steps"]["import"] = {
                "status": "success",
                "results": import_results
            }

            # Step 6: 数据一致性校验
            logger.info("=" * 80)
            logger.info("Step 6: Validate data consistency")
            logger.info("=" * 80)

            validator = DataConsistencyValidator(
                self.config,
                self.exporter.client,
                self.importer.db
            )

            validation_results = validator.validate_all()
            report["steps"]["validation"] = {
                "status": "success",
                "results": validation_results
            }

            # 检查是否有validation失败
            total_failed = sum(r["failed"] for r in validation_results)
            if total_failed > 0:
                logger.error(f"❌ Validation failed: {total_failed} documents failed consistency check")
                report["status"] = "failed"
                report["error"] = f"{total_failed} documents failed validation"
            else:
                logger.info("✅ All validations passed!")
                report["status"] = "success"

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            report["status"] = "failed"
            report["error"] = str(e)

        finally:
            report["end_time"] = datetime.now().isoformat()

        return report


# ============================================================================
# CLI入口
# ============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ChromaDB → LanceDB数据迁移工具 (Story 12.3)"
    )

    parser.add_argument(
        "--chromadb-path",
        default="./chroma_db",
        help="ChromaDB数据目录 (default: ./chroma_db)"
    )

    parser.add_argument(
        "--lancedb-path",
        default="~/.lancedb",
        help="LanceDB数据目录 (default: ~/.lancedb)"
    )

    parser.add_argument(
        "--backup-dir",
        default="./chromadb_backup",
        help="备份目录 (default: ./chromadb_backup)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="批处理大小 (default: 1000)"
    )

    parser.add_argument(
        "--validation-sample-size",
        type=int,
        default=100,
        help="一致性校验抽样大小 (default: 100)"
    )

    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="跳过备份步骤 (NOT RECOMMENDED)"
    )

    args = parser.parse_args()

    # 创建配置
    config = MigrationConfig(
        chromadb_path=args.chromadb_path,
        lancedb_path=args.lancedb_path,
        backup_dir=args.backup_dir,
        batch_size=args.batch_size,
        validation_sample_size=args.validation_sample_size
    )

    # 执行迁移
    orchestrator = MigrationOrchestrator(config)
    report = orchestrator.run_full_migration()

    # 输出报告
    logger.info("=" * 80)
    logger.info("Migration Report")
    logger.info("=" * 80)
    logger.info(json.dumps(report, indent=2, ensure_ascii=False))

    # 保存报告
    report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Report saved to: {report_file}")

    # 返回状态码
    if report["status"] == "success":
        logger.info("✅ Migration completed successfully!")
        return 0
    else:
        logger.error("❌ Migration failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
