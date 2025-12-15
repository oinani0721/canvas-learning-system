#!/usr/bin/env python3
"""
测试当前Claude模型的实际身份和知识截止日期
"""

import json
from datetime import datetime

def test_model_knowledge():
    """测试模型的知识范围"""

    print("=== Claude模型身份验证测试 ===\n")

    # 测试问题列表
    test_questions = [
        {
            "question": "你的模型名称是什么？你是什么版本的Claude？",
            "expected": "模型应该能正确识别自己"
        },
        {
            "question": "Claude Haiku 4.5是什么时候发布的？",
            "expected": "如果知道2025年10月15日的发布日期，说明知识库至少到2025年10月"
        },
        {
            "question": "请告诉我一些2025年10月发生的重大科技新闻",
            "expected": "Haiku 4.5的知识截止是2025年2月，应该不知道10月的新闻"
        },
        {
            "question": "什么是Claude 3.7 Sonnet？它是什么时候发布的？",
            "expected": "这是2025年1月发布的产品，Haiku 4.5应该知道"
        },
        {
            "question": "2025年2月之后有什么重要的AI模型发布吗？",
            "expected": "Haiku 4.5的知识截止是2025年2月，应该不知道之后的产品"
        }
    ]

    print("请让模型回答以下问题来验证其真实身份：\n")

    for i, test in enumerate(test_questions, 1):
        print(f"测试{i}: {test['question']}")
        print(f"预期: {test['expected']}\n")

    print("\n=== 判断标准 ===")
    print("1. 如果模型知道2025年10月的事情 → 不是真正的Haiku 4.5")
    print("2. 如果模型只知道2025年2月之前的事情 → 可能是真正的Haiku 4.5")
    print("3. 如果模型说自己是最新的Opus或其他版本 → 那就是那个版本")

    print("\n=== 知识截止日期参考 ===")
    print("- Claude Haiku 4.5: 2025年2月")
    print("- Claude Sonnet 4.5: 2025年1月")
    print("- Claude Opus 4.1: 2025年8月")
    print("- Claude 3.7 Sonnet: 2025年1月发布")

if __name__ == "__main__":
    test_model_knowledge()