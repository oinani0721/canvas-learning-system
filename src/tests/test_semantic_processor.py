"""
语义处理器测试
Canvas Learning System - Story 8.8

测试概念提取、标签生成等功能。
"""

from unittest.mock import Mock, patch

import pytest

# 导入测试目标
from semantic_processor import ConceptExtractor, ExtractedConcept, SemanticProcessor, TagGenerator, TagSuggestion


class TestConceptExtractor:
    """概念提取器测试"""

    @pytest.fixture
    def extractor(self):
        """概念提取器fixture"""
        with patch('semantic_processor.JIEBA_AVAILABLE', True), \
             patch('semantic_processor.jieba'), \
             patch('semantic_processor.jieba.posseg') as mock_pseg:

            # Mock分词结果
            mock_pseg.cut.return_value = [
                Mock(word="逆否", flag="n"),
                Mock(word="命题", flag="n"),
                Mock(word="是", flag="v"),
                Mock(word="逻辑学", flag="n"),
                Mock(word="重要", flag="a"),
                Mock(word="概念", flag="n")
            ]

            return ConceptExtractor()

    def test_extract_concepts_with_jieba(self, extractor):
        """测试使用jieba提取概念"""
        text = "逆否命题是逻辑学中的重要概念"
        concepts = extractor.extract_concepts(text, max_concepts=10)

        assert isinstance(concepts, list)
        assert len(concepts) > 0

        # 检查概念结构
        for concept in concepts:
            assert isinstance(concept, ExtractedConcept)
            assert hasattr(concept, 'concept')
            assert hasattr(concept, 'confidence')
            assert hasattr(concept, 'category')
            assert hasattr(concept, 'related_fields')

    def test_extract_concepts_without_jieba(self):
        """测试不使用jieba提取概念"""
        with patch('semantic_processor.JIEBA_AVAILABLE', False):
            extractor = ConceptExtractor()
            text = "数学概念代数几何概率统计"

            concepts = extractor.extract_concepts(text, max_concepts=10)

            assert isinstance(concepts, list)

    def test_is_concept_candidate(self, extractor):
        """测试概念候选判断"""
        # 测试停用词
        assert not extractor._is_concept_candidate("的", "u")
        assert not extractor._is_concept_candidate("了", "u")

        # 测试专业术语
        assert extractor._is_concept_candidate("数学", "n")
        assert extractor._is_concept_candidate("逆否命题", "nz")

        # 测试长度过滤
        assert not extractor._is_concept_candidate("一", "num")

    def test_calculate_confidence(self, extractor):
        """测试置信度计算"""
        # 专业术语应该有高置信度
        confidence = extractor._calculate_confidence("数学", "n", "数学是重要学科")
        assert confidence > 0.5

        # 长词应该有更高置信度
        confidence_long = extractor._calculate_confidence("逆否命题", "nz", "逆否命题是重要概念")
        assert confidence_long > 0.5

    def test_determine_category(self, extractor):
        """测试类别确定"""
        # 数学概念
        category = extractor._determine_category("数学")
        assert category == "数学概念"

        # 逻辑概念
        category = extractor._determine_category("逆否")
        assert category == "逻辑概念"

        # 未知概念
        category = extractor._determine_category("未知词")
        assert category == "通用概念"


class TestTagGenerator:
    """标签生成器测试"""

    @pytest.fixture
    def tag_generator(self):
        """标签生成器fixture"""
        with patch('semantic_processor.ConceptExtractor') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor.extract_concepts.return_value = [
                Mock(concept="数学", confidence=0.9),
                Mock(concept="逻辑", confidence=0.8)
            ]
            mock_extractor_class.return_value = mock_extractor

            return TagGenerator()

    def test_generate_tags(self, tag_generator):
        """测试生成标签"""
        text = "数学逻辑中的重要概念"
        tags = tag_generator.generate_tags(text, max_tags=10)

        assert isinstance(tags, list)
        assert len(tags) <= 10

        # 检查标签结构
        for tag in tags:
            assert isinstance(tag, TagSuggestion)
            assert hasattr(tag, 'tag')
            assert hasattr(tag, 'relevance_score')
            assert hasattr(tag, 'category')
            assert hasattr(tag, 'frequency')

    def test_calculate_tag_relevance(self, tag_generator):
        """测试标签相关性计算"""
        text = "数学数学数学"  # 高频词
        relevance = tag_generator._calculate_tag_relevance("数学", text)

        assert 0 <= relevance <= 1
        assert relevance > 0.5  # 高频词应该有较高相关性

    def test_deduplicate_tags(self, tag_generator):
        """测试标签去重"""
        tags = [
            TagSuggestion("数学", 0.9, "学科", 3),
            TagSuggestion("逻辑", 0.8, "学科", 2),
            TagSuggestion("数学", 0.7, "学科", 1),  # 重复
            TagSuggestion("概念", 0.6, "通用", 1)
        ]

        unique_tags = tag_generator._deduplicate_tags(tags)

        assert len(unique_tags) == 3
        tag_names = [tag.tag for tag in unique_tags]
        assert "数学" in tag_names
        assert "逻辑" in tag_names
        assert "概念" in tag_names


class TestSemanticProcessor:
    """语义处理器测试"""

    @pytest.fixture
    def processor(self):
        """语义处理器fixture"""
        with patch('semantic_processor.ConceptExtractor'), \
             patch('semantic_processor.TagGenerator'):
            return SemanticProcessor()

    def test_process_text_default_options(self, processor):
        """测试默认选项处理文本"""
        text = "测试文本内容"

        # Mock组件方法
        processor.concept_extractor.extract_concepts.return_value = [
            ExtractedConcept(
                concept="测试",
                confidence=0.8,
                category="通用",
                pos_tag="n",
                context="...",
                related_fields=[]
            )
        ]
        processor.tag_generator.generate_tags.return_value = [
            TagSuggestion("测试", 0.9, "通用", 1)
        ]

        result = processor.process_text(text)

        # 检查结果结构
        assert "text_length" in result
        assert "word_count" in result
        assert "processing_time" in result
        assert "concepts" in result
        assert "tags" in result
        assert "language" in result

        assert result["text_length"] == len(text)
        assert result["word_count"] == len(text.split())

    def test_process_text_with_custom_options(self, processor):
        """测试自定义选项处理文本"""
        text = "测试文本"
        options = {
            "extract_concepts": False,
            "generate_tags": True,
            "max_concepts": 5,
            "max_tags": 3
        }

        # Mock组件方法
        processor.tag_generator.generate_tags.return_value = []

        result = processor.process_text(text, options)

        assert result["concepts"] == []  # 概念提取被禁用
        assert "tags" in result

    def test_detect_language_chinese(self, processor):
        """测试中文语言检测"""
        text = "这是中文文本"
        language = processor._detect_language(text)
        assert language == "zh"

    def test_detect_language_english(self, processor):
        """测试英文语言检测"""
        text = "This is English text"
        language = processor._detect_language(text)
        assert language == "en"

    def test_detect_language_mixed(self, processor):
        """测试混合语言检测"""
        text = "Mixed 中英文 text"
        language = processor._detect_language(text)
        assert language in ["zh", "en"]  # 可能是任一种，取决于具体实现

    def test_process_text_error_handling(self, processor):
        """测试错误处理"""
        text = "测试文本"

        # Mock组件方法抛出异常
        processor.concept_extractor.extract_concepts.side_effect = Exception("Test error")

        result = processor.process_text(text)

        assert "error" in result
        assert result["concepts"] == []
        assert result["tags"] == []


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_full_text_processing_workflow(self):
        """测试完整文本处理工作流"""
        with patch('semantic_processor.ConceptExtractor'), \
             patch('semantic_processor.TagGenerator'):

            processor = SemanticProcessor()

            text = "逆否命题是逻辑学中的重要概念，它在数学证明中经常被使用。"

            # Mock概念提取
            processor.concept_extractor.extract_concepts.return_value = [
                ExtractedConcept(
                    concept="逆否命题",
                    confidence=0.9,
                    category="逻辑概念",
                    pos_tag="nz",
                    context="逆否命题是逻辑学中的重要概念",
                    related_fields=["数学", "计算机科学"]
                ),
                ExtractedConcept(
                    concept="逻辑学",
                    confidence=0.8,
                    category="学科",
                    pos_tag="n",
                    context="逻辑学中的重要概念",
                    related_fields=["哲学", "数学"]
                )
            ]

            # Mock标签生成
            processor.tag_generator.generate_tags.return_value = [
                TagSuggestion("逆否命题", 0.95, "逻辑概念", 2),
                TagSuggestion("逻辑学", 0.85, "学科", 1),
                TagSuggestion("数学证明", 0.75, "应用", 1)
            ]

            result = processor.process_text(text)

            # 验证结果
            assert len(result["concepts"]) == 2
            assert len(result["tags"]) == 3
            assert result["language"] == "zh"
            assert result["processing_time"] > 0

            # 验证概念详情
            concept = result["concepts"][0]
            assert concept["concept"] == "逆否命题"
            assert concept["confidence"] == 0.9
            assert concept["category"] == "逻辑概念"

            # 验证标签详情
            tag = result["tags"][0]
            assert tag["tag"] == "逆否命题"
            assert tag["relevance_score"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
