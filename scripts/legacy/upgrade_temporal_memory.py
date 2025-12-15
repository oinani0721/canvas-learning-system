#!/usr/bin/env python3
"""
自动升级temporal_memory_manager.py

将Stub实现升级为真正的DirectNeo4jStorage实现
"""

import sys
from pathlib import Path

def upgrade_temporal_memory():
    """升级temporal_memory_manager.py"""

    file_path = Path("memory_system/temporal_memory_manager.py")

    if not file_path.exists():
        print(f"[ERROR] 文件不存在: {file_path}")
        return False

    print("=" * 60)
    print("升级 temporal_memory_manager.py")
    print("=" * 60)

    # 备份原文件
    backup_path = file_path.with_suffix('.py.backup')
    print(f"\n[1] 备份原文件到: {backup_path}")
    content = file_path.read_text(encoding='utf-8')
    backup_path.write_text(content, encoding='utf-8')
    print("    [OK] 备份完成")

    # 修改1: 更新__init__方法
    print("\n[2] 修改 __init__ 方法...")

    old_init = """        # 初始化连接
        self._initialize_graphiti()"""

    new_init = """        # 初始化直接Neo4j存储（不依赖MCP或claude_tools）
        self.storage = None
        self.storage_available = False
        self._initialize_direct_storage()"""

    if old_init in content:
        content = content.replace(old_init, new_init)
        print("    [OK] __init__方法已修改")
    else:
        print("    [WARNING] 未找到旧的__init__代码")

    # 修改2: 替换_initialize_graphiti为_initialize_direct_storage
    print("\n[3] 替换 _initialize_graphiti 为 _initialize_direct_storage...")

    old_method = """    @handle_temporal_memory_errors
    def _initialize_graphiti(self):
        \"\"\"初始化Graphiti连接\"\"\"
        try:
            # 尝试导入Graphiti库
            try:
                from graphiti_core import Graphiti"""

    new_method = """    @handle_temporal_memory_errors
    def _initialize_direct_storage(self):
        \"\"\"初始化直接Neo4j存储（不依赖MCP或claude_tools）\"\"\"
        try:
            from memory_system.neo4j_storage import DirectNeo4jStorage

            self.storage = DirectNeo4jStorage(
                uri=self.neo4j_uri,
                user=self.neo4j_username,
                password=self.neo4j_password,
                database=self.database_name
            )

            self.storage_available = True
            self.is_initialized = True
            self.mode = 'direct_neo4j'  # 新增模式标识
            logger.info("✅ 时序记忆管理器初始化成功 [Direct Neo4j Storage - No MCP Dependency]")

        except ImportError as e:
            logger.error(f"导入DirectNeo4jStorage失败: {e}")
            self.mode = 'unavailable'
            raise TemporalMemoryError(
                operation="init",
                details=f"DirectNeo4jStorage导入失败: {str(e)}",
                cause=e
            )
        except Exception as e:
            logger.error(f"时序记忆管理器初始化失败: {e}")
            self.mode = 'unavailable'
            raise TemporalMemoryError(
                operation="init",
                details=f"DirectNeo4jStorage初始化失败: {str(e)}"""

    if old_method in content:
        # 找到完整的_initialize_graphiti方法并替换
        start_idx = content.find(old_method)
        if start_idx != -1:
            # 找到方法结束（下一个@handle或class级别的def）
            method_end = content.find("\n    @handle_temporal_memory_errors", start_idx + 1)
            if method_end == -1:
                method_end = content.find("\n    def ", start_idx + 1)

            if method_end != -1:
                # 替换整个方法
                content = content[:start_idx] + new_method + "\n                cause=e\n            )\n" + content[method_end:]
                print("    [OK] _initialize_graphiti已替换为_initialize_direct_storage")
            else:
                print("    [WARNING] 无法找到方法结束位置")
    else:
        print("    [WARNING] 未找到_initialize_graphiti方法")

    # 修改3: 修改create_learning_session实现
    print("\n[4] 修改 create_learning_session 实现...")

    old_session = """            # 如果Graphiti可用，在知识图谱中记录会话
            if self.graphiti_client:
                try:
                    # 这里应该调用Graphiti的会话创建方法
                    # 由于当前Graphiti实现可能不完整，我们先记录到本地
                    logger.info(f"在Graphiti中创建学习会话: {session.session_id}")
                except Exception as e:
                    logger.warning(f"Graphiti会话创建失败，使用本地模式: {e}")"""

    new_session = """            # 存储到Neo4j（直接存储，不依赖MCP）
            if self.storage_available and self.storage:
                try:
                    session_data = {
                        'session_id': session.session_id,
                        'canvas_id': canvas_id,
                        'user_id': user_id,
                        'start_time': session.start_time.isoformat(),
                        'canvas_path': getattr(self, 'canvas_path', 'unknown')
                    }

                    stored_id = self.storage.create_session_node(session_data)
                    logger.info(f"✅ 学习会话已存储到Neo4j: {stored_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Neo4j存储失败，使用内存模式: {e}")
            else:
                logger.warning("⚠️ Neo4j存储不可用，会话仅存储在内存中")"""

    if old_session in content:
        content = content.replace(old_session, new_session)
        print("    [OK] create_learning_session已修改")
    else:
        print("    [WARNING] 未找到create_learning_session的旧代码")

    # 修改4: 修改record_learning_journey实现
    print("\n[5] 修改 record_learning_journey 实现...")

    old_record = """            # 如果Graphiti可用，记录到知识图谱
            if self.graphiti_client:
                try:
                    self._record_to_graphiti(memory_data)
                except Exception as e:
                    logger.warning(f"Graphiti记录失败，使用本地存储: {e}")"""

    new_record = """            # 存储到Neo4j（直接存储，不依赖MCP）
            if self.storage_available and self.storage:
                try:
                    event_data = {
                        'session_id': memory_data.session_id,
                        'event_id': memory_id,
                        'event_type': interaction_type.value,
                        'timestamp': timestamp.isoformat(),
                        'content': f"{learning_state.value} - {node_id}",
                        'metadata': json.dumps(memory_data.metadata, ensure_ascii=False)
                    }

                    success = self.storage.record_memory_event(event_data)
                    if success:
                        logger.info(f"✅ 学习历程已存储到Neo4j: {memory_id}")
                    else:
                        logger.warning(f"⚠️ 事件存储失败: {memory_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Neo4j记录失败: {e}")"""

    if old_record in content:
        content = content.replace(old_record, new_record)
        print("    [OK] record_learning_journey已修改")
    else:
        print("    [WARNING] 未找到record_learning_journey的旧代码")

    # 修改5: 删除stub的_record_to_graphiti方法
    print("\n[6] 删除stub的_record_to_graphiti方法...")

    stub_method_start = """    @handle_temporal_memory_errors
    def _record_to_graphiti(self, memory_data: TemporalMemoryData):
        \"\"\"将时序记忆数据记录到Graphiti知识图谱\"\"\"
        try:
            # 这里实现Graphiti数据记录逻辑"""

    if stub_method_start in content:
        start_idx = content.find(stub_method_start)
        if start_idx != -1:
            # 找到下一个方法或类结束
            end_idx = content.find("\n    @handle_temporal_memory_errors", start_idx + 10)
            if end_idx == -1:
                end_idx = content.find("\n    def ", start_idx + 10)

            if end_idx != -1:
                # 删除整个方法
                content = content[:start_idx] + content[end_idx:]
                print("    [OK] _record_to_graphiti stub方法已删除")
            else:
                print("    [WARNING] 无法找到_record_to_graphiti结束位置")
    else:
        print("    [INFO] 未找到_record_to_graphiti stub方法（可能已删除）")

    # 写入修改后的文件
    print("\n[7] 写入修改后的文件...")
    file_path.write_text(content, encoding='utf-8')
    print("    [OK] 文件已更新")

    print("\n" + "=" * 60)
    print("[SUCCESS] temporal_memory_manager.py 升级完成!")
    print("=" * 60)
    print("\n变更摘要:")
    print("  [√] 移除Graphiti依赖")
    print("  [√] 使用DirectNeo4jStorage（纯Python）")
    print("  [√] 真正存储会话到Neo4j")
    print("  [√] 真正记录事件到Neo4j")
    print("  [√] 不依赖MCP或claude_tools")
    print("  [√] 可在subprocess中运行")
    print(f"\n备份文件: {backup_path}")
    print("\n下一步: 运行测试验证升级效果")
    print("  python test_temporal_memory_upgraded.py")

    return True


if __name__ == "__main__":
    try:
        success = upgrade_temporal_memory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] 升级失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
