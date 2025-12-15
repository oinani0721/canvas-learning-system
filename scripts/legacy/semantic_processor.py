"""
语义处理器
Canvas Learning System - Story 8.8

提供文本语义分析、概念提取、自动标签生成等功能。
"""

import re
import json
import time
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
import logging

# 第三方库导入
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logging.warning("jieba not available. Install with: pip install jieba")

from mcp_memory_client import ConceptInfo

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedConcept:
    """提取的概念数据类"""
    concept: str
    confidence: float
    category: str
    pos_tag: str  # 词性标注
    context: str  # 上下文
    related_fields: List[str]


@dataclass
class TagSuggestion:
    """标签建议数据类"""
    tag: str
    relevance_score: float
    category: str
    frequency: int


class ConceptExtractor:
    """概念提取器"""

    def __init__(self):
        """初始化概念提取器"""
        if JIEBA_AVAILABLE:
            # 加载自定义词典
            self._load_custom_dictionary()

        # 定义概念类别映射
        self.concept_categories = {
            "数学概念": ["数学", "代数", "几何", "概率", "统计", "函数", "方程", "不等式", "集合", "极限", "导数", "积分"],
            "逻辑概念": ["逻辑", "命题", "逆否", "充分", "必要", "推理", "证明", "演绎", "归纳"],
            "计算机概念": ["算法", "数据结构", "程序", "编程", "代码", "函数", "变量", "循环", "条件", "类", "对象"],
            "语言概念": ["语法", "词汇", "句子", "段落", "文章", "修辞", "比喻", "拟人"],
            "物理概念": ["力", "运动", "能量", "质量", "速度", "加速度", "重力", "电", "磁", "光"],
            "化学概念": ["原子", "分子", "元素", "化合物", "反应", "酸", "碱", "盐", "氧化", "还原"]
        }

        # 专业术语词典
        self.technical_terms = set()
        for terms in self.concept_categories.values():
            self.technical_terms.update(terms)

    def _load_custom_dictionary(self):
        """加载自定义词典"""
        try:
            # 添加专业术语到jieba词典
            for category, terms in self.concept_categories.items():
                for term in terms:
                    jieba.add_word(term, freq=1000, tag='nz')  # nz: 其他专名
        except Exception as e:
            logger.warning(f"加载自定义词典失败: {e}")

    def extract_concepts(self, text: str, max_concepts: int = 20) -> List[ExtractedConcept]:
        """提取文本中的概念

        Args:
            text: 输入文本
            max_concepts: 最大提取数量

        Returns:
            List[ExtractedConcept]: 提取的概念列表
        """
        try:
            concepts = []

            if JIEBA_AVAILABLE:
                # 使用jieba进行分词和词性标注
                words = pseg.cut(text)
                word_list = []

                for word, flag in words:
                    if len(word.strip()) >= 2:  # 过滤单字符和空格
                        word_list.append((word.strip(), flag))

                # 识别概念
                for i, (word, flag) in enumerate(word_list):
                    if self._is_concept_candidate(word, flag):
                        concept = self._create_concept(
                            word, flag, text, word_list, i
                        )
                        if concept:
                            concepts.append(concept)

            else:
                # 如果没有jieba，使用简单的正则表达式提取
                concepts = self._extract_with_regex(text)

            # 按置信度排序并限制数量
            concepts.sort(key=lambda x: x.confidence, reverse=True)
            return concepts[:max_concepts]

        except Exception as e:
            logger.error(f"概念提取失败: {e}")
            return []

    def _is_concept_candidate(self, word: str, flag: str) -> bool:
        """判断是否为概念候选词"""
        # 过滤停用词
        stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "这", "那", "她", "他", "它", "们"}
        if word in stop_words or len(word) < 2:
            return False

        # 专业术语优先
        if word in self.technical_terms:
            return True

        # 名词、动词、形容词更可能是概念
        concept_pos_tags = {'n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'}
        return any(flag.startswith(tag) for tag in concept_pos_tags)

    def _create_concept(self, word: str, flag: str, text: str, word_list: List[Tuple[str, str]], index: int) -> ExtractedConcept:
        """创建概念对象"""
        try:
            # 计算置信度
            confidence = self._calculate_confidence(word, flag, text)

            # 确定类别
            category = self._determine_category(word)

            # 提取上下文
            context = self._extract_context(word, text, index, len(word_list))

            # 识别相关领域
            related_fields = self._identify_related_fields(word, category)

            return ExtractedConcept(
                concept=word,
                confidence=confidence,
                category=category,
                pos_tag=flag,
                context=context,
                related_fields=related_fields
            )
        except Exception as e:
            logger.warning(f"创建概念失败 {word}: {e}")
            return None

    def _calculate_confidence(self, word: str, flag: str, text: str) -> float:
        """计算概念置信度"""
        confidence = 0.5  # 基础置信度

        # 专业术语加分
        if word in self.technical_terms:
            confidence += 0.3

        # 词性加分
        if flag.startswith('n'):  # 名词
            confidence += 0.2
        elif flag in ['v', 'vn']:  # 动词
            confidence += 0.1
        elif flag.startswith('a'):  # 形容词
            confidence += 0.1

        # 长度加分
        if len(word) >= 4:
            confidence += 0.1
        elif len(word) >= 2:
            confidence += 0.05

        # 频率加分
        word_frequency = text.count(word)
        if word_frequency > 1:
            confidence += min(0.2, word_frequency * 0.05)

        return min(confidence, 1.0)

    def _determine_category(self, word: str) -> str:
        """确定概念类别"""
        for category, terms in self.concept_categories.items():
            if word in terms:
                return category
        return "通用概念"

    def _extract_context(self, word: str, text: str, index: int, total_words: int) -> str:
        """提取上下文"""
        # 简单的上下文提取：取前后各50个字符
        word_pos = text.find(word)
        if word_pos == -1:
            return ""

        start = max(0, word_pos - 50)
        end = min(len(text), word_pos + len(word) + 50)

        context = text[start:end]
        return f"...{context}..."

    def _identify_related_fields(self, word: str, category: str) -> List[str]:
        """识别相关领域"""
        related_fields = []

        # 基于类别推断相关领域
        field_mapping = {
            "数学概念": ["数学", "统计学", "物理学", "工程学"],
            "逻辑概念": ["哲学", "数学", "计算机科学", "法学"],
            "计算机概念": ["计算机科学", "软件工程", "信息技术"],
            "语言概念": ["文学", "语言学", "教育学"],
            "物理概念": ["物理学", "工程学", "天文学"],
            "化学概念": ["化学", "生物学", "医学", "材料科学"]
        }

        if category in field_mapping:
            related_fields = field_mapping[category]

        return related_fields

    def _extract_with_regex(self, text: str) -> List[ExtractedConcept]:
        """使用正则表达式提取概念（备用方法）"""
        concepts = []

        # 提取专业术语
        for category, terms in self.concept_categories.items():
            for term in terms:
                if term in text:
                    confidence = 0.7 if len(term) >= 4 else 0.6
                    concepts.append(ExtractedConcept(
                        concept=term,
                        confidence=confidence,
                        category=category,
                        pos_tag="nz",
                        context=f"...{term[:20]}..." if len(term) > 20 else term,
                        related_fields=self._identify_related_fields(term, category)
                    ))

        return concepts


class TagGenerator:
    """标签生成器"""

    def __init__(self):
        """初始化标签生成器"""
        self.concept_extractor = ConceptExtractor()

        # 标签类别
        self.tag_categories = {
            "学科领域": ["数学", "物理", "化学", "生物", "计算机", "语言", "历史", "地理"],
            "学习目标": ["基础概念", "深入理解", "实际应用", "问题解决", "创新思维"],
            "难度级别": ["入门", "进阶", "高级", "专业"],
            "学习方式": ["理论学习", "实践练习", "概念理解", "记忆技巧"],
            "内容类型": ["概念定义", "原理解释", "例题分析", "方法总结"]
        }

    def generate_tags(self, text: str, max_tags: int = 10) -> List[TagSuggestion]:
        """生成内容标签

        Args:
            text: 输入文本
            max_tags: 最大标签数量

        Returns:
            List[TagSuggestion]: 生成的标签建议列表
        """
        try:
            tags = []

            # 1. 基于概念提取生成标签
            concepts = self.concept_extractor.extract_concepts(text)
            for concept in concepts:
                if concept.confidence >= 0.6:
                    tags.append(TagSuggestion(
                        tag=concept.concept,
                        relevance_score=concept.confidence,
                        category=concept.category,
                        frequency=text.count(concept.concept)
                    ))

            # 2. 基于预定义类别生成标签
            for category, tag_list in self.tag_categories.items():
                for tag in tag_list:
                    if tag in text:
                        relevance_score = self._calculate_tag_relevance(tag, text)
                        if relevance_score >= 0.3:
                            tags.append(TagSuggestion(
                                tag=tag,
                                relevance_score=relevance_score,
                                category=category,
                                frequency=text.count(tag)
                            ))

            # 3. 去重和排序
            unique_tags = self._deduplicate_tags(tags)
            unique_tags.sort(key=lambda x: (x.relevance_score, x.frequency), reverse=True)

            return unique_tags[:max_tags]

        except Exception as e:
            logger.error(f"标签生成失败: {e}")
            return []

    def _calculate_tag_relevance(self, tag: str, text: str) -> float:
        """计算标签相关性"""
        frequency = text.count(tag)
        text_length = len(text)

        # 基于频率的基础相关性
        base_relevance = min(frequency / (text_length / 1000), 1.0)

        # 长度加权
        length_weight = min(len(tag) / 10, 0.3)

        # 专业术语加权
        if tag in self.concept_extractor.technical_terms:
            professional_weight = 0.3
        else:
            professional_weight = 0.1

        relevance = base_relevance + length_weight + professional_weight
        return min(relevance, 1.0)

    def _deduplicate_tags(self, tags: List[TagSuggestion]) -> List[TagSuggestion]:
        """去重标签"""
        seen_tags = set()
        unique_tags = []

        for tag in tags:
            if tag.tag not in seen_tags:
                seen_tags.add(tag.tag)
                unique_tags.append(tag)

        return unique_tags


class SemanticProcessor:
    """语义处理器主类"""

    def __init__(self):
        """初始化语义处理器"""
        self.concept_extractor = ConceptExtractor()
        self.tag_generator = TagGenerator()
        logger.info("语义处理器初始化完成")

    def process_text(self, text: str, options: Dict = None) -> Dict:
        """处理文本语义信息

        Args:
            text: 输入文本
            options: 处理选项

        Returns:
            Dict: 处理结果
        """
        if options is None:
            options = {
                "extract_concepts": True,
                "generate_tags": True,
                "max_concepts": 20,
                "max_tags": 10,
                "concept_confidence_threshold": 0.5,
                "tag_relevance_threshold": 0.3
            }

        try:
            result = {
                "text_length": len(text),
                "word_count": len(text.split()),
                "processing_time": None,
                "concepts": [],
                "tags": [],
                "language": self._detect_language(text)
            }

            start_time = time.time()

            # 提取概念
            if options.get("extract_concepts", True):
                concepts = self.concept_extractor.extract_concepts(
                    text, options.get("max_concepts", 20)
                )
                # 过滤置信度
                threshold = options.get("concept_confidence_threshold", 0.5)
                result["concepts"] = [
                    {
                        "concept": concept.concept,
                        "confidence": concept.confidence,
                        "category": concept.category,
                        "related_fields": concept.related_fields
                    }
                    for concept in concepts if concept.confidence >= threshold
                ]

            # 生成标签
            if options.get("generate_tags", True):
                tags = self.tag_generator.generate_tags(
                    text, options.get("max_tags", 10)
                )
                # 过滤相关性
                threshold = options.get("tag_relevance_threshold", 0.3)
                result["tags"] = [
                    {
                        "tag": tag.tag,
                        "relevance_score": tag.relevance_score,
                        "category": tag.category,
                        "frequency": tag.frequency
                    }
                    for tag in tags if tag.relevance_score >= threshold
                ]

            end_time = time.time()
            result["processing_time"] = end_time - start_time

            logger.info(f"语义处理完成: {len(result['concepts'])} 个概念, {len(result['tags'])} 个标签")
            return result

        except Exception as e:
            logger.error(f"语义处理失败: {e}")
            return {
                "error": str(e),
                "concepts": [],
                "tags": []
            }

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.sub(r'\s', '', text))

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh"
        else:
            return "en"


if __name__ == "__main__":
    # 简单测试
    processor = SemanticProcessor()

    test_text = """
    逆否命题是逻辑学中的重要概念，它与原命题具有相同的真假性。
    在数学证明中，逆否命题经常被用来证明一些难以直接证明的命题。
    例如，要证明'如果P则Q'，可以证明它的逆否命题'如果非Q则非P'。
    """

    result = processor.process_text(test_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))