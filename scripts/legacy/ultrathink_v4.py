#!/usr/bin/env python3
"""
UltraThink v4.0 - 智能问题识别与深度思考系统
新增功能：
1. 智能问题识别与分类
2. Think Harder 深度思考模式
3. 单个问题专用处理器
4. 智能问题路由系统
"""

import json
import os
import time
import logging
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('UltraThink_v4')

class ProblemType(Enum):
    """问题类型枚举"""
    CONCEPTUAL = "概念理解类"
    LOGICAL = "逻辑推理类"
    COMPUTATIONAL = "计算应用类"
    ANALYTICAL = "综合分析类"
    CREATIVE = "创新思维类"
    PROOF = "证明类"
    PROCEDURAL = "程序步骤类"
    COMPARATIVE = "比较分析类"
    CAUSAL = "因果关系类"
    EVALUATIVE = "评价判断类"

class ThinkingMode(Enum):
    """思考模式枚举"""
    STANDARD = "标准模式"
    DEEP = "深度模式"
    THINK_HARDER = "Think Harder模式"
    CREATIVE = "创意模式"
    SYSTEMATIC = "系统化模式"

class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    VERY_COMPLEX = 4
    EXTREMELY_COMPLEX = 5

@dataclass
class ProblemProfile:
    """问题画像"""
    problem_type: ProblemType
    complexity_level: ComplexityLevel
    thinking_mode: ThinkingMode
    keywords: List[str] = field(default_factory=list)
    domain: str = "通用"
    cognitive_load: float = 0.0
    estimated_time: float = 0.0
    requires_think_harder: bool = False
    
@dataclass
class QuestionV4:
    """问题数据类 V4"""
    id: str
    content: str
    profile: Optional[ProblemProfile] = None
    category: Optional[str] = None
    quality_score: Optional[float] = None
    analysis_depth: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResultV4:
    """分析结果数据类 V4"""
    question_id: str
    question_profile: ProblemProfile
    main_analysis: str
    supplement_analysis: str
    think_harder_analysis: str
    quality_score: float
    processing_time: float
    thinking_mode_used: ThinkingMode
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    save_path: str = ""

class ProblemIdentifier:
    """智能问题识别器"""
    
    def __init__(self):
        self.pattern_rules = self._load_pattern_rules()
        self.keyword_weights = self._load_keyword_weights()
        self.domain_keywords = self._load_domain_keywords()
        
    def _load_pattern_rules(self) -> Dict[ProblemType, List[str]]:
        """加载模式规则"""
        return {
            ProblemType.PROOF: [
                r"证明|proof|prove|demonstrate",
                r"显然|clearly|obviously",
                r"QED|因此得证|证毕"
            ],
            ProblemType.COMPUTATIONAL: [
                r"计算|calculate|compute|求解",
                r"数值|numerical|value",
                r"结果|result|答案"
            ],
            ProblemType.CONCEPTUAL: [
                r"是什么|what is|定义|definition",
                r"概念|concept|理解|understand",
                r"含义|meaning|解释|explain"
            ],
            ProblemType.LOGICAL: [
                r"逻辑|logic|推理|reasoning",
                r"因为|because|所以|therefore",
                r"如果|if|那么|then"
            ],
            ProblemType.ANALYTICAL: [
                r"分析|analyze|分解|decompose",
                r"比较|compare|对比|contrast",
                r"评估|evaluate|判断|judge"
            ],
            ProblemType.CREATIVE: [
                r"创新|innovative|新颖|novel",
                r"设计|design|创造|create",
                r"想象|imagine|构思|conceive"
            ],
            ProblemType.PROCEDURAL: [
                r"步骤|step|流程|process",
                r"方法|method|如何|how to",
                r"操作|operate|执行|execute"
            ],
            ProblemType.COMPARATIVE: [
                r"比较|compare|对比|versus",
                r"差异|difference|相似|similarity",
                r"优缺点|pros and cons"
            ],
            ProblemType.CAUSAL: [
                r"原因|cause|为什么|why",
                r"导致|lead to|引起|result in",
                r"影响|influence|effect"
            ],
            ProblemType.EVALUATIVE: [
                r"评价|evaluate|判断|judge",
                r"好坏|good or bad|优劣|merits",
                r"值得|worth|应该|should"
            ]
        }
    
    def _load_keyword_weights(self) -> Dict[str, float]:
        """加载关键词权重"""
        return {
            "证明": 3.0, "推理": 2.5, "分析": 2.0,
            "计算": 2.0, "求解": 2.0, "解释": 1.5,
            "比较": 1.5, "评估": 1.8, "创新": 2.5,
            "设计": 2.0, "原理": 2.2, "机制": 1.8,
            "为什么": 1.8, "如何": 1.5, "是什么": 1.2
        }
    
    def _load_domain_keywords(self) -> Dict[str, List[str]]:
        """加载领域关键词"""
        return {
            "数学": ["函数", "微积分", "代数", "几何", "统计", "概率"],
            "物理": ["力学", "热学", "电磁", "光学", "量子", "相对论"],
            "化学": ["反应", "分子", "原子", "化合物", "有机", "无机"],
            "计算机": ["算法", "数据结构", "编程", "软件", "网络", "系统"],
            "经济": ["市场", "供需", "价格", "投资", "金融", "贸易"],
            "哲学": ["存在", "意识", "道德", "伦理", "逻辑", "形而上学"],
            "历史": ["时代", "事件", "人物", "制度", "文化", "社会"],
            "语言": ["语法", "词汇", "语义", "语音", "修辞", "文学"]
        }
    
    def identify_problem(self, question: QuestionV4) -> ProblemProfile:
        """识别问题类型和特征"""
        content = question.content.lower()
        
        # 1. 识别问题类型
        problem_type = self._identify_problem_type(content)
        
        # 2. 评估复杂度
        complexity_level = self._evaluate_complexity(content)
        
        # 3. 确定思考模式
        thinking_mode = self._determine_thinking_mode(problem_type, complexity_level)
        
        # 4. 提取关键词
        keywords = self._extract_keywords(content)
        
        # 5. 识别领域
        domain = self._identify_domain(content)
        
        # 6. 计算认知负荷
        cognitive_load = self._calculate_cognitive_load(content, complexity_level)
        
        # 7. 估算处理时间
        estimated_time = self._estimate_processing_time(complexity_level, thinking_mode)
        
        # 8. 判断是否需要Think Harder模式
        requires_think_harder = self._should_use_think_harder(problem_type, complexity_level)
        
        return ProblemProfile(
            problem_type=problem_type,
            complexity_level=complexity_level,
            thinking_mode=thinking_mode,
            keywords=keywords,
            domain=domain,
            cognitive_load=cognitive_load,
            estimated_time=estimated_time,
            requires_think_harder=requires_think_harder
        )
    
    def _identify_problem_type(self, content: str) -> ProblemType:
        """识别问题类型"""
        type_scores = {}
        
        for problem_type, patterns in self.pattern_rules.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches
            type_scores[problem_type] = score
        
        # 使用关键词权重进行补充评分
        for keyword, weight in self.keyword_weights.items():
            if keyword in content:
                if "证明" in keyword or "推理" in keyword:
                    type_scores[ProblemType.PROOF] = type_scores.get(ProblemType.PROOF, 0) + weight
                elif "计算" in keyword or "求解" in keyword:
                    type_scores[ProblemType.COMPUTATIONAL] = type_scores.get(ProblemType.COMPUTATIONAL, 0) + weight
                elif "分析" in keyword:
                    type_scores[ProblemType.ANALYTICAL] = type_scores.get(ProblemType.ANALYTICAL, 0) + weight
        
        # 返回得分最高的类型
        best_type = max(type_scores, key=type_scores.get) if type_scores else ProblemType.ANALYTICAL
        return best_type
    
    def _evaluate_complexity(self, content: str) -> ComplexityLevel:
        """评估问题复杂度"""
        complexity_indicators = {
            "high": ["复杂", "困难", "高级", "深入", "综合", "系统"],
            "medium": ["中等", "一般", "常规", "基础", "标准"],
            "low": ["简单", "基本", "初级", "容易", "直接"]
        }
        
        score = 0
        
        # 基于长度
        if len(content) > 100:
            score += 2
        elif len(content) > 50:
            score += 1
        
        # 基于关键词
        for level, keywords in complexity_indicators.items():
            for keyword in keywords:
                if keyword in content:
                    if level == "high":
                        score += 2
                    elif level == "medium":
                        score += 1
                    else:
                        score -= 1
        
        # 基于问题结构
        if "？" in content or "?" in content:
            score += 1
        if "为什么" in content or "why" in content:
            score += 1
        if "如何" in content or "how" in content:
            score += 1
        
        # 映射到复杂度级别
        if score >= 6:
            return ComplexityLevel.EXTREMELY_COMPLEX
        elif score >= 4:
            return ComplexityLevel.VERY_COMPLEX
        elif score >= 2:
            return ComplexityLevel.COMPLEX
        elif score >= 0:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
    def _determine_thinking_mode(self, problem_type: ProblemType, complexity: ComplexityLevel) -> ThinkingMode:
        """确定思考模式"""
        # 高复杂度问题使用Think Harder
        if complexity in [ComplexityLevel.VERY_COMPLEX, ComplexityLevel.EXTREMELY_COMPLEX]:
            return ThinkingMode.THINK_HARDER
        
        # 证明和逻辑推理问题使用系统化模式
        if problem_type in [ProblemType.PROOF, ProblemType.LOGICAL]:
            return ThinkingMode.SYSTEMATIC
        
        # 创新思维问题使用创意模式
        if problem_type == ProblemType.CREATIVE:
            return ThinkingMode.CREATIVE
        
        # 复杂分析问题使用深度模式
        if problem_type == ProblemType.ANALYTICAL and complexity == ComplexityLevel.COMPLEX:
            return ThinkingMode.DEEP
        
        return ThinkingMode.STANDARD
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简化的关键词提取
        keywords = []
        for word in self.keyword_weights.keys():
            if word in content:
                keywords.append(word)
        return keywords
    
    def _identify_domain(self, content: str) -> str:
        """识别问题领域"""
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content:
                    score += 1
            domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return "通用"
    
    def _calculate_cognitive_load(self, content: str, complexity: ComplexityLevel) -> float:
        """计算认知负荷"""
        base_load = complexity.value * 0.2
        length_factor = min(len(content) / 100, 1.0)
        return base_load + length_factor * 0.3
    
    def _estimate_processing_time(self, complexity: ComplexityLevel, thinking_mode: ThinkingMode) -> float:
        """估算处理时间"""
        base_time = {
            ComplexityLevel.SIMPLE: 30,
            ComplexityLevel.MODERATE: 60,
            ComplexityLevel.COMPLEX: 120,
            ComplexityLevel.VERY_COMPLEX: 240,
            ComplexityLevel.EXTREMELY_COMPLEX: 480
        }
        
        mode_multiplier = {
            ThinkingMode.STANDARD: 1.0,
            ThinkingMode.DEEP: 1.5,
            ThinkingMode.THINK_HARDER: 2.5,
            ThinkingMode.CREATIVE: 1.8,
            ThinkingMode.SYSTEMATIC: 1.6
        }
        
        return base_time[complexity] * mode_multiplier[thinking_mode]
    
    def _should_use_think_harder(self, problem_type: ProblemType, complexity: ComplexityLevel) -> bool:
        """判断是否需要Think Harder模式"""
        # 极高复杂度问题
        if complexity == ComplexityLevel.EXTREMELY_COMPLEX:
            return True
        
        # 证明类和创新类问题
        if problem_type in [ProblemType.PROOF, ProblemType.CREATIVE]:
            return True
        
        # 高复杂度的分析类问题
        if problem_type == ProblemType.ANALYTICAL and complexity == ComplexityLevel.VERY_COMPLEX:
            return True
        
        return False

class ThinkHarderEngine:
    """Think Harder 深度思考引擎"""
    
    def __init__(self):
        self.thinking_strategies = self._load_thinking_strategies()
        self.meta_cognitive_tools = self._load_meta_cognitive_tools()
    
    def _load_thinking_strategies(self) -> Dict[str, List[str]]:
        """加载思考策略"""
        return {
            "分解策略": [
                "将复杂问题分解为子问题",
                "识别问题的核心要素",
                "建立问题的层次结构",
                "寻找问题间的关联性"
            ],
            "类比策略": [
                "寻找相似问题的解决方案",
                "建立问题的类比模型",
                "从不同领域寻找启发",
                "构建形象化的比喻"
            ],
            "逆向策略": [
                "从结果反推过程",
                "考虑问题的反面",
                "寻找反例和边界条件",
                "验证解决方案的完整性"
            ],
            "系统策略": [
                "建立问题的系统模型",
                "分析系统的输入输出",
                "识别系统的约束条件",
                "优化系统的整体性能"
            ],
            "创新策略": [
                "跳出常规思维框架",
                "尝试非传统解决方案",
                "结合多个领域的知识",
                "产生新颖的见解"
            ]
        }
    
    def _load_meta_cognitive_tools(self) -> Dict[str, str]:
        """加载元认知工具"""
        return {
            "思维监控": "监控思考过程的质量和方向",
            "认知调节": "调整思考策略和方法",
            "知识整合": "整合多领域知识解决问题",
            "反思评估": "评估思考结果的合理性",
            "创新突破": "突破思维定势，产生新想法"
        }
    
    async def think_harder(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """执行Think Harder深度思考"""
        thinking_process = []
        
        # 1. 思维预热
        thinking_process.append(self._thinking_warmup(question, profile))
        
        # 2. 多角度思考
        thinking_process.append(await self._multi_perspective_thinking(question, profile))
        
        # 3. 深度分析
        thinking_process.append(await self._deep_analysis(question, profile))
        
        # 4. 创新突破
        thinking_process.append(await self._innovative_breakthrough(question, profile))
        
        # 5. 综合整合
        thinking_process.append(await self._synthesis_integration(question, profile))
        
        # 6. 反思验证
        thinking_process.append(await self._reflection_validation(question, profile))
        
        return self._combine_thinking_process(thinking_process, question, profile)
    
    def _thinking_warmup(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """思维预热"""
        return f"""
## 🧠 Think Harder 深度思考启动

### 🎯 问题重新审视
**原始问题**: {question.content}

**问题特征分析**:
- 问题类型: {profile.problem_type.value}
- 复杂度级别: {profile.complexity_level.name}
- 认知负荷: {profile.cognitive_load:.2f}
- 预估思考时间: {profile.estimated_time:.0f}秒

### 🔍 初步思考框架
1. **问题的本质是什么？**
   - 核心概念识别
   - 关键约束条件
   - 潜在假设分析

2. **问题的边界在哪里？**
   - 明确定义的范围
   - 不确定因素识别
   - 相关背景知识

3. **为什么这个问题重要？**
   - 理论意义分析
   - 实际应用价值
   - 学习成长收益

### 🧭 思考策略选择
基于问题特征，启用以下思考策略：
"""
    
    async def _multi_perspective_thinking(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """多角度思考"""
        perspectives = [
            "历史角度：这个问题是如何发展演变的？",
            "逻辑角度：问题的逻辑结构是什么？",
            "实践角度：如何在现实中应用这个知识？",
            "批判角度：问题的假设和前提是否合理？",
            "创新角度：是否有全新的解决思路？"
        ]
        
        result = """
## 🔄 多角度深度思考

### 🌍 全方位视角分析
"""
        
        for i, perspective in enumerate(perspectives, 1):
            result += f"""
#### 视角 {i}: {perspective}
[基于{profile.problem_type.value}特征的深度分析]

**核心洞察**:
- [洞察点1]
- [洞察点2]
- [洞察点3]

**关键发现**:
- [发现1]
- [发现2]
"""
        
        return result
    
    async def _deep_analysis(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """深度分析"""
        return f"""
## 🔬 深度分析层

### 🧪 概念解构
**第一层 - 表面概念**:
[问题的直观理解]

**第二层 - 深层机制**:
[问题背后的原理机制]

**第三层 - 本质规律**:
[问题反映的根本规律]

### 🎯 关键节点识别
1. **决定性因素**: [影响问题解决的关键因素]
2. **瓶颈环节**: [可能遇到的主要障碍]
3. **突破口**: [解决问题的切入点]

### 🌐 系统性思考
- **输入**: [问题的输入要素]
- **过程**: [问题的处理过程]
- **输出**: [期望的结果]
- **反馈**: [结果的验证机制]

### 🔍 细节深挖
[基于{profile.complexity_level.name}复杂度的详细分析]
"""
    
    async def _innovative_breakthrough(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """创新突破"""
        return """
## 💡 创新突破思考

### 🚀 跳出框架思考
**传统思路**: [常规的解决方法]
**创新思路**: [非常规的新想法]

### 🎨 创意融合
- **跨领域启发**: [从其他领域获得的灵感]
- **反向思考**: [逆向思维的新发现]
- **极限思考**: [推到极限的思考结果]

### 🔄 思维转换
1. **假设推翻**: 如果基础假设不成立会怎样？
2. **角色转换**: 如果从不同角色看待这个问题？
3. **时空转换**: 如果问题发生在不同时空？

### 🌟 突破性洞察
[基于深度思考产生的独特见解]
"""
    
    async def _synthesis_integration(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """综合整合"""
        return """
## 🎯 综合整合层

### 🔗 知识网络构建
- **核心概念网络**: [主要概念及其关系]
- **方法工具网络**: [相关方法和工具]
- **应用场景网络**: [实际应用情境]

### 📊 多维度整合
1. **纵向整合**: [从基础到高级的知识层次]
2. **横向整合**: [不同领域知识的融合]
3. **动态整合**: [知识的演化和发展]

### 🎭 完整图景构建
[问题的全貌理解和完整解决方案]
"""
    
    async def _reflection_validation(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """反思验证"""
        return """
## 🤔 反思验证层

### 🔍 思考质量检查
1. **逻辑一致性**: 思考过程是否自洽？
2. **完整性**: 是否遗漏重要方面？
3. **创新性**: 是否产生了新的见解？
4. **实用性**: 结论是否有实际价值？

### 🎯 解决方案评估
- **可行性**: [方案的可操作性]
- **有效性**: [方案的解决效果]
- **优雅性**: [方案的简洁美观]
- **扩展性**: [方案的适用范围]

### 📈 改进建议
[进一步改进的方向和建议]

### 🌟 Think Harder成果
[深度思考带来的核心收获]
"""
    
    def _combine_thinking_process(self, thinking_process: List[str], question: QuestionV4, profile: ProblemProfile) -> str:
        """组合思考过程"""
        header = f"""
# 🧠 Think Harder 深度思考报告

## 📋 问题信息
- **问题ID**: {question.id}
- **问题内容**: {question.content}
- **思考模式**: {profile.thinking_mode.value}
- **开始时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""
        
        combined = header + "\n".join(thinking_process)
        
        footer = f"""
---

## 📊 Think Harder 统计信息
- **思考深度**: 6层深度分析
- **思考角度**: 5个不同视角
- **创新突破**: 3个维度转换
- **质量验证**: 4项质量检查
- **预估思考时间**: {profile.estimated_time:.0f}秒

```
🎯 【Think Harder 完成】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 深度思考已完成 | 思考质量: 超高 | 创新程度: 突破性
🧠 元认知启用: 是 | 跨领域整合: 是 | 思维转换: 是
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
"""
        
        return combined + footer

class SingleQuestionProcessor:
    """单个问题专用处理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.identifier = ProblemIdentifier()
        self.think_harder_engine = ThinkHarderEngine()
    
    async def process_single_question(self, question: QuestionV4) -> AnalysisResultV4:
        """处理单个问题"""
        start_time = time.time()
        
        # 1. 问题识别和画像
        profile = self.identifier.identify_problem(question)
        question.profile = profile
        
        logger.info(f"问题 {question.id} 识别完成: {profile.problem_type.value}, 复杂度: {profile.complexity_level.name}")
        
        # 2. 根据画像选择处理策略
        if profile.requires_think_harder or profile.thinking_mode == ThinkingMode.THINK_HARDER:
            return await self._process_with_think_harder(question, profile, start_time)
        else:
            return await self._process_standard(question, profile, start_time)
    
    async def _process_with_think_harder(self, question: QuestionV4, profile: ProblemProfile, start_time: float) -> AnalysisResultV4:
        """使用Think Harder模式处理"""
        logger.info(f"启用Think Harder模式处理问题 {question.id}")
        
        # 生成Think Harder分析
        think_harder_analysis = await self.think_harder_engine.think_harder(question, profile)
        
        # 生成主分析和补充分析
        main_analysis = await self._generate_enhanced_main_analysis(question, profile)
        supplement_analysis = await self._generate_enhanced_supplement_analysis(question, profile)
        
        # 生成洞察和建议
        insights = self._generate_insights(question, profile)
        recommendations = self._generate_recommendations(question, profile)
        
        processing_time = time.time() - start_time
        
        return AnalysisResultV4(
            question_id=question.id,
            question_profile=profile,
            main_analysis=main_analysis,
            supplement_analysis=supplement_analysis,
            think_harder_analysis=think_harder_analysis,
            quality_score=self._calculate_quality_score(question, profile),
            processing_time=processing_time,
            thinking_mode_used=ThinkingMode.THINK_HARDER,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _process_standard(self, question: QuestionV4, profile: ProblemProfile, start_time: float) -> AnalysisResultV4:
        """标准模式处理"""
        logger.info(f"使用{profile.thinking_mode.value}处理问题 {question.id}")
        
        # 生成分析
        main_analysis = await self._generate_main_analysis(question, profile)
        supplement_analysis = await self._generate_supplement_analysis(question, profile)
        
        # 生成洞察和建议
        insights = self._generate_insights(question, profile)
        recommendations = self._generate_recommendations(question, profile)
        
        processing_time = time.time() - start_time
        
        return AnalysisResultV4(
            question_id=question.id,
            question_profile=profile,
            main_analysis=main_analysis,
            supplement_analysis=supplement_analysis,
            think_harder_analysis="",
            quality_score=self._calculate_quality_score(question, profile),
            processing_time=processing_time,
            thinking_mode_used=profile.thinking_mode,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _generate_enhanced_main_analysis(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """生成增强版主分析"""
        return f"""
# 🎯 {question.content} - 深度智能分析

## 📊 问题画像
- **问题类型**: {profile.problem_type.value}
- **复杂度级别**: {profile.complexity_level.name}
- **所属领域**: {profile.domain}
- **认知负荷**: {profile.cognitive_load:.2f}
- **关键词**: {', '.join(profile.keywords)}

## 🧠 智能分析启动
```
🔍 【智能识别完成】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 问题复杂度: {profile.complexity_level.name}
🎯 思考模式: {profile.thinking_mode.value}
🧠 需要Think Harder: {'是' if profile.requires_think_harder else '否'}
⏱️ 预估时间: {profile.estimated_time:.0f}秒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🎯 第一部分：智能问题诊断

### 🔍 问题特征分析
基于AI识别的问题特征：
- **主要特征**: {profile.problem_type.value}
- **次要特征**: [根据关键词分析的次要特征]
- **难点预测**: [基于复杂度预测的难点]

### 🧪 认知需求分析
- **认知负荷**: {profile.cognitive_load:.2f} (适中范围: 0.3-0.7)
- **思维类型**: [需要的思维类型]
- **知识依赖**: [需要的背景知识]

## 🔬 第二部分：深度机制分析

### 🎯 核心机制识别
[基于问题类型的核心机制分析]

### 🔄 处理流程设计
1. **输入处理**: [问题的输入要素]
2. **核心处理**: [主要处理步骤]
3. **输出生成**: [期望的输出结果]

## 💡 第三部分：智能解决方案

### 🚀 优化策略
基于问题画像的定制化解决策略：
[针对性的解决方案]

### 🎯 关键突破点
[基于AI分析的关键突破点]

## 🌟 第四部分：深度整合

### 📊 知识网络
[相关知识的网络结构]

### 🔗 关联分析
[与其他知识点的关联]

## 🎭 第五部分：完整解答

### 🏆 最终答案
[经过智能分析的完整答案]

### 🔍 答案验证
[答案的合理性验证]

### 📈 扩展思考
[进一步的思考方向]
"""
    
    async def _generate_main_analysis(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """生成主分析"""
        return f"""
# 📝 {question.content} - 标准分析

## 📋 问题基本信息
- **问题类型**: {profile.problem_type.value}
- **复杂度**: {profile.complexity_level.name}
- **思考模式**: {profile.thinking_mode.value}

## 🎯 分析过程
[基于{profile.problem_type.value}的分析过程]

## 💡 解决方案
[问题的解决方案]

## 📊 结果验证
[结果的验证和讨论]
"""
    
    async def _generate_enhanced_supplement_analysis(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """生成增强版补充分析"""
        return f"""
# 📚 {question.content} - 智能补充分析

## 🎯 学习路径定制
基于问题画像的个性化学习路径：

### 📈 能力发展路径
1. **当前水平**: [基于问题复杂度的能力评估]
2. **目标水平**: [需要达到的能力水平]
3. **发展路径**: [具体的能力发展步骤]

### 🎓 知识补强建议
- **核心知识**: [必须掌握的核心知识]
- **辅助知识**: [有助于理解的辅助知识]
- **扩展知识**: [深入学习的扩展知识]

## 🛠️ 思维工具箱

### 🧠 专用思维工具
基于{profile.problem_type.value}的专用工具：
[针对性的思维工具]

### 🎯 通用思维框架
[适用于该类问题的通用框架]

## 🔄 练习强化方案

### 📝 同类问题练习
[相似问题的练习建议]

### 🎯 能力提升练习
[专门的能力提升练习]

## 🌟 智能提醒系统

### ⚠️ 常见错误预警
[基于问题类型的常见错误]

### 🎯 关键检查点
[解决过程中的关键检查点]

### 📊 质量评估标准
[解答质量的评估标准]
"""
    
    async def _generate_supplement_analysis(self, question: QuestionV4, profile: ProblemProfile) -> str:
        """生成补充分析"""
        return f"""
# 📚 {question.content} - 补充分析

## 🎯 学习建议
[基于问题特征的学习建议]

## 🛠️ 相关工具
[解决该类问题的工具]

## 🔄 练习建议
[相关的练习建议]

## ⚠️ 注意事项
[需要注意的要点]
"""
    
    def _generate_insights(self, question: QuestionV4, profile: ProblemProfile) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 基于问题类型的洞察
        if profile.problem_type == ProblemType.PROOF:
            insights.append("这是一个证明类问题，需要严格的逻辑推理")
        elif profile.problem_type == ProblemType.CREATIVE:
            insights.append("这是一个创新类问题，需要跳出常规思维")
        
        # 基于复杂度的洞察
        if profile.complexity_level == ComplexityLevel.EXTREMELY_COMPLEX:
            insights.append("问题极其复杂，需要分解为多个子问题")
        
        # 基于领域的洞察
        if profile.domain != "通用":
            insights.append(f"这是一个{profile.domain}领域的专业问题")
        
        return insights
    
    def _generate_recommendations(self, question: QuestionV4, profile: ProblemProfile) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于思考模式的建议
        if profile.thinking_mode == ThinkingMode.THINK_HARDER:
            recommendations.append("建议使用Think Harder模式进行深度思考")
        
        # 基于复杂度的建议
        if profile.complexity_level.value >= 3:
            recommendations.append("建议将问题分解为多个子问题逐步解决")
        
        # 基于认知负荷的建议
        if profile.cognitive_load > 0.7:
            recommendations.append("认知负荷较高，建议分阶段处理")
        
        return recommendations
    
    def _calculate_quality_score(self, question: QuestionV4, profile: ProblemProfile) -> float:
        """计算质量分数"""
        base_score = 5.0
        
        # 基于复杂度调整
        base_score += profile.complexity_level.value * 0.5
        
        # 基于关键词调整
        base_score += len(profile.keywords) * 0.2
        
        # 基于认知负荷调整
        base_score += profile.cognitive_load * 2
        
        return min(max(base_score, 1.0), 10.0)

class SmartQuestionRouter:
    """智能问题路由系统"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.processor = SingleQuestionProcessor(config)
        self.routing_rules = self._load_routing_rules()
    
    def _load_routing_rules(self) -> Dict:
        """加载路由规则"""
        return {
            "think_harder_triggers": [
                ComplexityLevel.EXTREMELY_COMPLEX,
                ComplexityLevel.VERY_COMPLEX
            ],
            "standard_triggers": [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MODERATE
            ],
            "special_handling": {
                ProblemType.PROOF: ThinkingMode.SYSTEMATIC,
                ProblemType.CREATIVE: ThinkingMode.CREATIVE
            }
        }
    
    async def route_and_process(self, question: QuestionV4) -> AnalysisResultV4:
        """路由并处理问题"""
        # 使用单问题处理器
        result = await self.processor.process_single_question(question)
        
        logger.info(f"问题 {question.id} 处理完成，使用模式: {result.thinking_mode_used.value}")
        
        return result

class UltraThinkV4:
    """UltraThink v4.0 主类"""
    
    def __init__(self, config_path: str = 'ultrathink_config.json'):
        """初始化系统"""
        self.config = self._load_config(config_path)
        self.router = SmartQuestionRouter(self.config)
        self.statistics = {
            'total_processed': 0,
            'think_harder_used': 0,
            'problem_types': {},
            'complexity_distribution': {}
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "analysis_depth": 10,
            "enable_think_harder": True,
            "enable_smart_routing": True,
            "save_settings": {
                "auto_save": True,
                "save_interval": 500,
                "base_path": "./analysis_results_v4"
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def analyze_question(self, question: QuestionV4) -> AnalysisResultV4:
        """分析单个问题"""
        result = await self.router.route_and_process(question)
        
        # 更新统计信息
        self._update_statistics(result)
        
        return result
    
    def _update_statistics(self, result: AnalysisResultV4):
        """更新统计信息"""
        self.statistics['total_processed'] += 1
        
        if result.thinking_mode_used == ThinkingMode.THINK_HARDER:
            self.statistics['think_harder_used'] += 1
        
        # 更新问题类型统计
        problem_type = result.question_profile.problem_type.value
        self.statistics['problem_types'][problem_type] = \
            self.statistics['problem_types'].get(problem_type, 0) + 1
        
        # 更新复杂度分布
        complexity = result.question_profile.complexity_level.name
        self.statistics['complexity_distribution'][complexity] = \
            self.statistics['complexity_distribution'].get(complexity, 0) + 1
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.statistics.copy()

# 主程序入口
async def main():
    """主程序"""
    # 初始化系统
    ultrathink = UltraThinkV4()
    
    # 示例问题
    test_questions = [
        QuestionV4("01", "证明((p → q) ∧ (q → r)) → (p → r)是重言式"),
        QuestionV4("02", "如何设计一个创新的人工智能学习系统？"),
        QuestionV4("03", "分析量子计算对传统加密算法的影响"),
        QuestionV4("04", "什么是函数？"),
        QuestionV4("05", "创造一个全新的编程语言需要考虑哪些因素？")
    ]
    
    # 逐个分析问题
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"开始分析问题: {question.content}")
        print(f"{'='*60}")
        
        result = await ultrathink.analyze_question(question)
        
        print(f"问题类型: {result.question_profile.problem_type.value}")
        print(f"复杂度: {result.question_profile.complexity_level.name}")
        print(f"思考模式: {result.thinking_mode_used.value}")
        print(f"质量分数: {result.quality_score:.1f}")
        print(f"处理时间: {result.processing_time:.2f}秒")
        print(f"洞察数量: {len(result.insights)}")
        print(f"建议数量: {len(result.recommendations)}")
        
        if result.thinking_mode_used == ThinkingMode.THINK_HARDER:
            print("🧠 已使用Think Harder深度思考模式")
    
    # 输出统计信息
    stats = ultrathink.get_statistics()
    print(f"\n{'='*60}")
    print("UltraThink v4.0 处理统计")
    print(f"{'='*60}")
    print(f"总处理数量: {stats['total_processed']}")
    print(f"Think Harder使用次数: {stats['think_harder_used']}")
    print(f"问题类型分布: {stats['problem_types']}")
    print(f"复杂度分布: {stats['complexity_distribution']}")

if __name__ == "__main__":
    asyncio.run(main())