# Story 23.1: LangGraph导入问题修复 - Import Tests
# ✅ Verified from docs/stories/23.1.story.md#Testing-Requirements
"""
Test agentic_rag module import functionality.

Story 23.1 Test Coverage:
- AC 1: agentic_rag模块导入成功
- AC 2: LANGGRAPH_AVAILABLE = True
- AC 3: 依赖版本验证
- AC 4: 诊断功能测试

[Source: docs/stories/23.1.story.md#Testing-Requirements]
"""

import sys
from pathlib import Path

import pytest

# ============================================================
# Path Setup (ensure src/ is in sys.path for tests)
# ============================================================

# Add src/ to path for imports
_src_path = str(Path(__file__).parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


# ============================================================
# AC 1: agentic_rag模块导入成功
# ============================================================


class TestAgenticRagImport:
    """Test AC 1: agentic_rag模块导入成功"""

    def test_agentic_rag_import_success(self):
        """
        测试agentic_rag模块导入成功

        AC 1: Given Python环境已配置所有依赖
              When 执行 from agentic_rag import ...
              Then 导入成功，无ImportError
        """
        # Should not raise ImportError
        from agentic_rag import (
            AGENTIC_RAG_AVAILABLE,
            CanvasRAGConfig,
            CanvasRAGState,
            canvas_agentic_rag,
        )

        # Verify imports are not None (when available)
        if AGENTIC_RAG_AVAILABLE:
            assert CanvasRAGState is not None, "CanvasRAGState should not be None"
            assert CanvasRAGConfig is not None, "CanvasRAGConfig should not be None"
            assert canvas_agentic_rag is not None, (
                "canvas_agentic_rag should not be None"
            )

    def test_state_import(self):
        """测试CanvasRAGState导入"""
        from agentic_rag import AGENTIC_RAG_AVAILABLE, CanvasRAGState

        if AGENTIC_RAG_AVAILABLE:
            assert CanvasRAGState is not None

    def test_config_import(self):
        """测试CanvasRAGConfig导入"""
        from agentic_rag import AGENTIC_RAG_AVAILABLE, CanvasRAGConfig

        if AGENTIC_RAG_AVAILABLE:
            assert CanvasRAGConfig is not None

    def test_stategraph_import(self):
        """测试canvas_agentic_rag导入"""
        from agentic_rag import AGENTIC_RAG_AVAILABLE, canvas_agentic_rag

        if AGENTIC_RAG_AVAILABLE:
            assert canvas_agentic_rag is not None


# ============================================================
# AC 1 Extension: StateGraph编译验证
# ============================================================


class TestStateGraphCompiled:
    """Test StateGraph is properly compiled"""

    def test_stategraph_has_invoke(self):
        """
        测试StateGraph已编译 - 有invoke方法

        AC 1 验证: 编译后的StateGraph应该有invoke方法
        """
        from agentic_rag import AGENTIC_RAG_AVAILABLE, canvas_agentic_rag

        if AGENTIC_RAG_AVAILABLE:
            assert hasattr(canvas_agentic_rag, "invoke"), (
                "Compiled StateGraph should have invoke method"
            )

    def test_stategraph_has_ainvoke(self):
        """
        测试StateGraph已编译 - 有ainvoke方法

        AC 1 验证: 编译后的StateGraph应该有ainvoke方法
        """
        from agentic_rag import AGENTIC_RAG_AVAILABLE, canvas_agentic_rag

        if AGENTIC_RAG_AVAILABLE:
            assert hasattr(canvas_agentic_rag, "ainvoke"), (
                "Compiled StateGraph should have ainvoke method"
            )

    def test_stategraph_type(self):
        """测试StateGraph类型"""
        from agentic_rag import AGENTIC_RAG_AVAILABLE, canvas_agentic_rag

        if AGENTIC_RAG_AVAILABLE:
            # Should be a CompiledStateGraph
            type_name = type(canvas_agentic_rag).__name__
            assert "CompiledStateGraph" in type_name or "CompiledGraph" in type_name, (
                f"Expected CompiledStateGraph, got {type_name}"
            )


# ============================================================
# AC 2: RAGService中LANGGRAPH_AVAILABLE为True
# ============================================================


class TestLangGraphAvailable:
    """Test AC 2: LANGGRAPH_AVAILABLE标志"""

    def test_agentic_rag_available_flag(self):
        """
        测试AGENTIC_RAG_AVAILABLE标志

        AC 2 验证: 模块级别的可用性标志
        """
        from agentic_rag import AGENTIC_RAG_AVAILABLE

        # Should be True if all dependencies installed
        assert AGENTIC_RAG_AVAILABLE is True, (
            "AGENTIC_RAG_AVAILABLE should be True when dependencies are installed"
        )

    def test_rag_service_langgraph_available(self):
        """
        测试RAGService中LANGGRAPH_AVAILABLE标志

        AC 2: Given AC 1已满足
              When 检查 rag_service.py 的 LANGGRAPH_AVAILABLE 变量
              Then LANGGRAPH_AVAILABLE = True
        """
        # Add backend to path
        _backend_path = str(Path(__file__).parent.parent.parent / "backend")
        if _backend_path not in sys.path:
            sys.path.insert(0, _backend_path)

        from app.services.rag_service import LANGGRAPH_AVAILABLE

        assert LANGGRAPH_AVAILABLE is True, (
            "LANGGRAPH_AVAILABLE should be True in rag_service"
        )

    def test_rag_service_singleton(self):
        """测试RAGService单例获取"""
        _backend_path = str(Path(__file__).parent.parent.parent / "backend")
        if _backend_path not in sys.path:
            sys.path.insert(0, _backend_path)

        from app.services.rag_service import RAGService, get_rag_service

        service = get_rag_service()
        assert isinstance(service, RAGService)
        assert service.is_available is True


# ============================================================
# AC 3: 依赖版本验证
# ============================================================


class TestDependencies:
    """Test AC 3: 所有依赖版本记录在requirements.txt"""

    def test_langgraph_installed(self):
        """测试langgraph已安装"""
        import langgraph

        assert langgraph is not None

    def test_langchain_core_installed(self):
        """测试langchain-core已安装"""
        import langchain_core

        assert langchain_core is not None

    def test_lancedb_installed(self):
        """测试lancedb已安装"""
        import lancedb

        assert lancedb is not None

    def test_neo4j_installed(self):
        """测试neo4j已安装"""
        import neo4j

        assert neo4j is not None

    def test_check_dependencies_function(self):
        """测试check_dependencies函数"""
        from agentic_rag import check_dependencies

        deps = check_dependencies()

        assert isinstance(deps, dict)
        assert "langgraph" in deps
        assert "langchain_core" in deps
        assert "lancedb" in deps
        assert "neo4j" in deps

        # All should be True if tests are running
        assert deps["langgraph"] is True
        assert deps["langchain_core"] is True
        assert deps["lancedb"] is True
        assert deps["neo4j"] is True


# ============================================================
# AC 4: 导入诊断日志
# ============================================================


class TestDiagnostics:
    """Test AC 4: 导入诊断功能"""

    def test_get_import_error_when_available(self):
        """测试get_import_error - 导入成功时返回None"""
        from agentic_rag import AGENTIC_RAG_AVAILABLE, get_import_error

        if AGENTIC_RAG_AVAILABLE:
            error = get_import_error()
            assert error is None, (
                f"get_import_error should return None when available, got: {error}"
            )

    def test_all_exports_present(self):
        """测试所有导出都存在"""
        from agentic_rag import __all__

        expected_exports = [
            "CanvasRAGState",
            "CanvasRAGConfig",
            "canvas_agentic_rag",
            "AGENTIC_RAG_AVAILABLE",
            "get_import_error",
            "check_dependencies",
        ]

        for export in expected_exports:
            assert export in __all__, f"Missing export: {export}"

    def test_version_string(self):
        """测试版本字符串"""
        from agentic_rag import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
        # Should be semver format
        parts = __version__.split(".")
        assert len(parts) >= 2, f"Version should be semver format, got: {__version__}"


# ============================================================
# Integration Tests
# ============================================================


class TestIntegration:
    """Integration tests for full import chain"""

    def test_full_import_chain(self):
        """测试完整导入链"""
        # Step 1: Import module
        import agentic_rag

        # Step 2: Check availability
        assert agentic_rag.AGENTIC_RAG_AVAILABLE is True

        # Step 3: Verify exports
        assert agentic_rag.CanvasRAGState is not None
        assert agentic_rag.CanvasRAGConfig is not None
        assert agentic_rag.canvas_agentic_rag is not None

        # Step 4: Verify StateGraph
        assert hasattr(agentic_rag.canvas_agentic_rag, "invoke")
        assert hasattr(agentic_rag.canvas_agentic_rag, "ainvoke")

    @pytest.mark.asyncio
    async def test_rag_service_initialize(self):
        """测试RAGService初始化"""
        _backend_path = str(Path(__file__).parent.parent.parent / "backend")
        if _backend_path not in sys.path:
            sys.path.insert(0, _backend_path)

        from app.services.rag_service import RAGService

        service = RAGService()
        assert service.is_available is True

        result = await service.initialize()
        assert result is True


# ============================================================
# Run tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
