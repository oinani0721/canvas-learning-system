"""
黄色节点理解分析器 - UltraThink智能策略系统核心组件

本模块分析原白板上用户填写的黄色理解节点内容，判定理解程度并推荐学习策略。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-16
"""

import io
import sys
from typing import Dict, List

# Note: encoding fix moved to main scripts to avoid import issues


class UnderstandingLevelAnalyzer:
    """理解程度分析器"""

    # 关键词权重表
    KEYWORDS = {
        # 完全不懂 (0-20%)
        "完全不懂": 0,
        "完全不理解": 0,
        "看不懂": 5,
        "一头雾水": 5,
        "没概念": 10,

        # 有点印象 (20-40%)
        "有点印象": 25,
        "听说过": 25,
        "模糊": 30,
        "不太清楚": 30,
        "有点概念": 35,

        # 似懂非懂 (40-60%)
        "好像懂了": 50,
        "不太确定": 45,
        "有点理解": 50,
        "大概知道": 50,
        "似懂非懂": 50,

        # 基本理解 (60-80%)
        "理解了定义": 65,
        "知道是什么": 65,
        "明白了": 70,
        "理解了": 70,
        "懂了": 70,

        # 修正词（降低分数）
        "但不会用": -10,
        "但不确定": -10,
        "但不知道": -10,

        # 完全理解 (80%+)
        "完全理解": 85,
        "很清楚": 85,
        "可以解释": 90
    }

    def analyze(self, yellow_text: str) -> Dict:
        """分析理解程度"""

        if not yellow_text or len(yellow_text.strip()) == 0:
            return {
                "understanding_percentage": 0,
                "matched_keywords": [],
                "confidence": 1.0,
                "recommended_strategy": "provide_explanation",
                "strategy_reason": "未填写理解，需要补充基础解释"
            }

        # 1. 关键词匹配
        score, matched_keywords = self._analyze_keywords(yellow_text)

        # 2. 文本特征调整
        score = self._adjust_by_text_features(score, yellow_text)

        # 3. 推荐策略
        strategy, reason = self._recommend_strategy(score, yellow_text)

        return {
            "understanding_percentage": score,
            "matched_keywords": matched_keywords,
            "confidence": 0.9 if matched_keywords else 0.5,
            "recommended_strategy": strategy,
            "strategy_reason": reason
        }

    def _analyze_keywords(self, text: str) -> tuple:
        """关键词匹配"""
        score = 50
        matched = []

        sorted_keywords = sorted(self.KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True)

        for keyword, weight in sorted_keywords:
            if keyword in text:
                matched.append(keyword)
                if weight >= 0:
                    score = weight
                else:
                    score += weight

        return max(0, min(100, score)), matched

    def _adjust_by_text_features(self, base_score: int, text: str) -> int:
        """根据文本特征调整分数"""
        adjusted = base_score

        if len(text) < 10:
            adjusted -= 10
        elif len(text) > 100:
            adjusted += 5

        if any(ex in text for ex in ["比如", "例如", "举例"]):
            adjusted += 10

        if '？' in text or '?' in text:
            adjusted -= 5

        return max(0, min(100, adjusted))

    def _recommend_strategy(self, score: int, text: str) -> tuple:
        """推荐策略"""

        if score <= 30:
            return ("provide_explanation",
                    f"理解程度{score}%，需要补充解释建立基础认识")
        elif score <= 70:
            return ("split_questions",
                    f"理解程度{score}%，拆分问题引导深化理解")
        else:
            return ("deep_verification",
                    f"理解程度{score}%，进行深度检验巩固掌握")


if __name__ == "__main__":
    analyzer = UnderstandingLevelAnalyzer()
    test_cases = [
        "完全不懂，看不懂",
        "好像懂了，但不确定应用场景",
        "理解了定义，可以解释"
    ]

    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"文本: {text}")
        print(f"理解程度: {result['understanding_percentage']}%")
        print(f"策略: {result['recommended_strategy']}")
        print()
