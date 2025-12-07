"""
Canvas Learning System v2.0 - LocalSemanticCache单元测试
Story 10.11.3 - Task 8

测试semantic_fallback_cache.py的LocalSemanticCache类的所有功能。
"""

import sqlite3

# 导入被测试的类
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory_system.semantic_fallback_cache import LocalSemanticCache, create_local_semantic_cache


class TestLocalSemanticCacheInit:
    """测试LocalSemanticCache初始化"""

    def test_init_with_memory_database(self):
        """测试使用内存数据库初始化"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        assert cache.db_path == ':memory:'
        assert cache.db_path_full == ':memory:'
        assert cache.connection is not None
        assert cache.connection.row_factory == sqlite3.Row

        cache.close()

    def test_init_with_file_database(self, tmp_path):
        """测试使用文件数据库初始化"""
        db_file = tmp_path / "test_cache.db"
        cache = LocalSemanticCache({'fallback_db_path': str(db_file)})

        assert cache.connection is not None
        assert Path(cache.db_path_full).exists()

        cache.close()

    def test_init_creates_tables_and_indexes(self):
        """测试初始化是否创建了正确的表和索引"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})
        cursor = cache.connection.cursor()

        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='semantic_memories'
        """)
        assert cursor.fetchone() is not None

        # 检查索引是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_content'
        """)
        assert cursor.fetchone() is not None

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_created_at'
        """)
        assert cursor.fetchone() is not None

        cache.close()

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        cache = LocalSemanticCache()

        # 默认路径应该是项目根目录下的.semantic_cache.db
        assert '.semantic_cache.db' in cache.db_path_full
        assert cache.connection is not None

        cache.close()

        # 清理测试数据库文件
        if Path(cache.db_path_full).exists():
            Path(cache.db_path_full).unlink()


class TestLocalSemanticCacheAddMemory:
    """测试add_memory方法"""

    def test_add_memory_basic(self):
        """测试添加基本记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        content = "逆否命题是逻辑学中的重要概念"
        metadata = {"source": "test", "category": "logic"}

        memory_id = cache.add_memory(content, metadata)

        # 检查返回的memory_id格式
        assert memory_id.startswith("memory-")
        assert len(memory_id) == len("memory-") + 16  # UUID的前16个字符

        cache.close()

    def test_add_memory_without_metadata(self):
        """测试添加不带元数据的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        content = "测试内容"
        memory_id = cache.add_memory(content)

        assert memory_id is not None
        assert memory_id.startswith("memory-")

        # 验证记忆已存储
        memory = cache.get_memory(memory_id)
        assert memory is not None
        assert memory['content'] == content
        assert memory['metadata'] == {}

        cache.close()

    def test_add_memory_with_chinese_content(self):
        """测试添加中文内容"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        content = "Canvas学习系统使用费曼学习法进行深度学习"
        metadata = {"type": "learning", "tags": ["费曼学习法", "Canvas"]}

        memory_id = cache.add_memory(content, metadata)

        # 验证中文正确存储
        memory = cache.get_memory(memory_id)
        assert memory['content'] == content
        assert memory['metadata']['tags'] == ["费曼学习法", "Canvas"]

        cache.close()

    def test_add_multiple_memories(self):
        """测试添加多个记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        memory_ids = []
        for i in range(5):
            content = f"测试记忆 {i}"
            memory_id = cache.add_memory(content, {"index": i})
            memory_ids.append(memory_id)

        # 验证所有记忆都已添加
        assert len(memory_ids) == 5
        assert len(set(memory_ids)) == 5  # 所有ID都是唯一的
        assert cache.count_memories() == 5

        cache.close()


class TestLocalSemanticCacheSearchMemories:
    """测试search_memories方法"""

    def test_search_memories_basic(self):
        """测试基本搜索功能"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        # 添加测试数据
        cache.add_memory("逆否命题是逻辑学概念", {"category": "logic"})
        cache.add_memory("Canvas学习系统", {"category": "learning"})
        cache.add_memory("逆否命题的应用", {"category": "logic"})

        # 搜索"逆否命题"
        results = cache.search_memories("逆否命题", limit=10)

        assert len(results) == 2
        for result in results:
            assert "逆否命题" in result['content']
            assert result['similarity_score'] == 0.5  # 降级模式固定相似度
            assert 'memory_id' in result
            assert 'created_at' in result

        cache.close()

    def test_search_memories_with_limit(self):
        """测试搜索结果数量限制"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        # 添加5个包含"测试"的记忆
        for i in range(5):
            cache.add_memory(f"测试记忆 {i}")

        # 限制返回2条
        results = cache.search_memories("测试", limit=2)

        assert len(results) == 2

        cache.close()

    def test_search_memories_no_results(self):
        """测试搜索无结果的情况"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        cache.add_memory("逆否命题")

        results = cache.search_memories("不存在的内容XYZ123")

        assert len(results) == 0
        assert isinstance(results, list)

        cache.close()

    def test_search_memories_chinese_query(self):
        """测试中文查询"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        cache.add_memory("费曼学习法是一种高效的学习方法")
        cache.add_memory("Canvas白板用于可视化学习")
        cache.add_memory("费曼技巧通过输出倒逼输入")

        results = cache.search_memories("费曼", limit=10)

        assert len(results) == 2
        for result in results:
            assert "费曼" in result['content']

        cache.close()

    def test_search_memories_result_format(self):
        """测试搜索结果的格式"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        metadata = {"importance": 8, "tags": ["logic"]}
        cache.add_memory("逆否命题", metadata)

        results = cache.search_memories("逆否命题")

        assert len(results) == 1
        result = results[0]

        # 检查结果包含所有必需字段
        assert 'memory_id' in result
        assert 'content' in result
        assert 'metadata' in result
        assert 'created_at' in result
        assert 'similarity_score' in result

        # 检查字段值
        assert result['content'] == "逆否命题"
        assert result['metadata'] == metadata
        assert result['similarity_score'] == 0.5

        cache.close()


class TestLocalSemanticCacheGetMemory:
    """测试get_memory方法"""

    def test_get_memory_existing(self):
        """测试获取存在的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        content = "逆否命题"
        metadata = {"type": "concept"}
        memory_id = cache.add_memory(content, metadata)

        # 获取记忆
        memory = cache.get_memory(memory_id)

        assert memory is not None
        assert memory['memory_id'] == memory_id
        assert memory['content'] == content
        assert memory['metadata'] == metadata
        assert 'created_at' in memory

        cache.close()

    def test_get_memory_nonexistent(self):
        """测试获取不存在的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        memory = cache.get_memory("memory-nonexistent123")

        assert memory is None

        cache.close()

    def test_get_memory_with_invalid_metadata_json(self):
        """测试获取包含无效JSON元数据的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        # 手动插入无效JSON元数据
        cursor = cache.connection.cursor()
        cursor.execute("""
            INSERT INTO semantic_memories (id, content, metadata)
            VALUES (?, ?, ?)
        """, ("memory-test123", "测试内容", "invalid-json{{{"))
        cache.connection.commit()

        # 获取记忆（应该返回空字典作为metadata）
        memory = cache.get_memory("memory-test123")

        assert memory is not None
        assert memory['metadata'] == {}

        cache.close()


class TestLocalSemanticCacheDeleteMemory:
    """测试delete_memory方法"""

    def test_delete_memory_existing(self):
        """测试删除存在的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        memory_id = cache.add_memory("测试删除")

        # 删除前验证存在
        assert cache.get_memory(memory_id) is not None
        assert cache.count_memories() == 1

        # 删除
        result = cache.delete_memory(memory_id)

        assert result is True
        assert cache.get_memory(memory_id) is None
        assert cache.count_memories() == 0

        cache.close()

    def test_delete_memory_nonexistent(self):
        """测试删除不存在的记忆"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        result = cache.delete_memory("memory-nonexistent123")

        assert result is False

        cache.close()


class TestLocalSemanticCacheCountMemories:
    """测试count_memories方法"""

    def test_count_memories_empty(self):
        """测试空数据库的记忆计数"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        count = cache.count_memories()

        assert count == 0

        cache.close()

    def test_count_memories_with_data(self):
        """测试有数据时的记忆计数"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        for i in range(10):
            cache.add_memory(f"记忆 {i}")

        count = cache.count_memories()

        assert count == 10

        cache.close()

    def test_count_memories_after_deletion(self):
        """测试删除后的记忆计数"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        memory_ids = [cache.add_memory(f"记忆 {i}") for i in range(5)]

        assert cache.count_memories() == 5

        # 删除2个
        cache.delete_memory(memory_ids[0])
        cache.delete_memory(memory_ids[2])

        assert cache.count_memories() == 3

        cache.close()


class TestLocalSemanticCacheClearAll:
    """测试clear_all方法"""

    def test_clear_all_empty_database(self):
        """测试清空空数据库"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        result = cache.clear_all()

        assert result is True
        assert cache.count_memories() == 0

        cache.close()

    def test_clear_all_with_data(self):
        """测试清空有数据的数据库"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        for i in range(10):
            cache.add_memory(f"记忆 {i}")

        assert cache.count_memories() == 10

        result = cache.clear_all()

        assert result is True
        assert cache.count_memories() == 0

        cache.close()


class TestLocalSemanticCacheGetStatistics:
    """测试get_statistics方法"""

    def test_get_statistics_memory_database(self):
        """测试内存数据库的统计信息"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        for i in range(5):
            cache.add_memory(f"记忆 {i}")

        stats = cache.get_statistics()

        assert stats['total_memories'] == 5
        assert stats['db_path'] == ':memory:'
        assert stats['db_size_bytes'] == 0  # 内存数据库没有文件大小

        cache.close()

    def test_get_statistics_file_database(self, tmp_path):
        """测试文件数据库的统计信息"""
        db_file = tmp_path / "test_stats.db"
        cache = LocalSemanticCache({'fallback_db_path': str(db_file)})

        for i in range(3):
            cache.add_memory(f"记忆 {i}")

        stats = cache.get_statistics()

        assert stats['total_memories'] == 3
        assert stats['db_path'] == str(db_file)
        assert stats['db_size_bytes'] > 0  # 文件数据库应该有文件大小

        cache.close()


class TestLocalSemanticCacheClose:
    """测试close方法"""

    def test_close_closes_connection(self):
        """测试close方法是否关闭数据库连接"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        assert cache.connection is not None

        cache.close()

        assert cache.connection is None

    def test_close_multiple_times(self):
        """测试多次调用close不会报错"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        cache.close()
        cache.close()  # 不应该抛出异常

        assert cache.connection is None

    def test_destructor_closes_connection(self):
        """测试析构函数是否自动关闭连接"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})
        connection = cache.connection

        del cache  # 触发__del__

        # 连接应该已关闭（无法直接验证，但不应抛出异常）


class TestLocalSemanticCacheEdgeCases:
    """测试边界情况和异常处理"""

    def test_empty_content(self):
        """测试添加空内容"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        memory_id = cache.add_memory("")

        assert memory_id is not None
        memory = cache.get_memory(memory_id)
        assert memory['content'] == ""

        cache.close()

    def test_very_long_content(self):
        """测试添加非常长的内容"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        long_content = "测试" * 10000  # 20000字符
        memory_id = cache.add_memory(long_content)

        memory = cache.get_memory(memory_id)
        assert memory['content'] == long_content

        cache.close()

    def test_special_characters_in_content(self):
        """测试内容中包含特殊字符"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        content = "特殊字符: 🔴 🟢 🟣 \n\t \" ' % _"
        memory_id = cache.add_memory(content)

        memory = cache.get_memory(memory_id)
        assert memory['content'] == content

        cache.close()

    def test_search_with_sql_injection_attempt(self):
        """测试搜索是否防止SQL注入"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        cache.add_memory("正常内容")

        # 尝试SQL注入（应该被参数化查询防止）
        results = cache.search_memories("' OR '1'='1", limit=10)

        # 不应该返回所有记录，应该当作普通字符串搜索
        assert len(results) == 0

        cache.close()

    def test_concurrent_operations(self):
        """测试并发操作（基本测试）"""
        cache = LocalSemanticCache({'fallback_db_path': ':memory:'})

        # 快速添加多个记忆（模拟并发）
        memory_ids = []
        for i in range(20):
            memory_id = cache.add_memory(f"并发记忆 {i}")
            memory_ids.append(memory_id)

        # 验证所有记忆都已添加
        assert cache.count_memories() == 20
        assert len(set(memory_ids)) == 20  # 所有ID唯一

        cache.close()


class TestCreateLocalSemanticCacheFunction:
    """测试create_local_semantic_cache便捷函数"""

    def test_create_local_semantic_cache_default(self):
        """测试使用默认配置创建缓存"""
        cache = create_local_semantic_cache()

        assert isinstance(cache, LocalSemanticCache)
        assert cache.connection is not None

        cache.close()

        # 清理
        if Path(cache.db_path_full).exists():
            Path(cache.db_path_full).unlink()

    def test_create_local_semantic_cache_with_config(self):
        """测试使用自定义配置创建缓存"""
        config = {'fallback_db_path': ':memory:'}
        cache = create_local_semantic_cache(config)

        assert isinstance(cache, LocalSemanticCache)
        assert cache.db_path == ':memory:'

        cache.close()


class TestLocalSemanticCachePersistence:
    """测试数据持久化"""

    def test_data_persists_across_connections(self, tmp_path):
        """测试数据在连接关闭和重新打开后是否持久化"""
        db_file = tmp_path / "persist_test.db"
        config = {'fallback_db_path': str(db_file)}

        # 第一次连接：添加数据
        cache1 = LocalSemanticCache(config)
        memory_id = cache1.add_memory("持久化测试内容", {"test": True})
        cache1.close()

        # 第二次连接：读取数据
        cache2 = LocalSemanticCache(config)
        memory = cache2.get_memory(memory_id)

        assert memory is not None
        assert memory['content'] == "持久化测试内容"
        assert memory['metadata']['test'] is True

        cache2.close()

    def test_database_file_created_in_correct_location(self, tmp_path):
        """测试数据库文件是否在正确位置创建"""
        db_file = tmp_path / "location_test.db"
        cache = LocalSemanticCache({'fallback_db_path': str(db_file)})

        cache.add_memory("测试")

        assert db_file.exists()
        assert db_file.is_file()

        cache.close()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
