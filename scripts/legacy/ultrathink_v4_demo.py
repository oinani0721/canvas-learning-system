#!/usr/bin/env python3
"""
UltraThink v4.0 演示程序
展示新功能的使用方法和效果
"""

import asyncio
import time
import json
from ultrathink_v4 import (
    UltraThinkV4, QuestionV4, ProblemType, ThinkingMode, ComplexityLevel
)

class UltraThinkV4Demo:
    """UltraThink v4.0 演示类"""
    
    def __init__(self):
        self.ultrathink = UltraThinkV4()
        
    async def run_all_demos(self):
        """运行所有演示"""
        print("🚀 UltraThink v4.0 功能演示")
        print("=" * 60)
        
        # 1. 基础功能演示
        await self.demo_basic_features()
        
        # 2. Think Harder模式演示
        await self.demo_think_harder()
        
        # 3. 问题类型识别演示
        await self.demo_problem_identification()
        
        # 4. 智能路由演示
        await self.demo_smart_routing()
        
        # 5. 批量处理演示
        await self.demo_batch_processing()
        
        # 6. 统计信息演示
        await self.demo_statistics()
        
        print("\n✅ 所有演示完成！")
    
    async def demo_basic_features(self):
        """基础功能演示"""
        print("\n📝 1. 基础功能演示")
        print("-" * 40)
        
        # 创建简单问题
        question = QuestionV4("DEMO_01", "什么是人工智能？")
        
        print(f"问题: {question.content}")
        
        start_time = time.time()
        result = await self.ultrathink.analyze_question(question)
        end_time = time.time()
        
        print(f"✅ 分析完成 (用时: {end_time - start_time:.2f}秒)")
        print(f"📊 问题类型: {result.question_profile.problem_type.value}")
        print(f"📈 复杂度: {result.question_profile.complexity_level.name}")
        print(f"🧠 思考模式: {result.thinking_mode_used.value}")
        print(f"⭐ 质量分数: {result.quality_score:.1f}")
        
        if result.insights:
            print("💡 关键洞察:")
            for insight in result.insights:
                print(f"  • {insight}")
    
    async def demo_think_harder(self):
        """Think Harder模式演示"""
        print("\n🧠 2. Think Harder 深度思考演示")
        print("-" * 40)
        
        # 创建复杂问题，会自动触发Think Harder
        complex_question = QuestionV4(
            "DEMO_02",
            "设计一个能够理解人类情感、具备创造力并能够进行道德推理的通用人工智能系统，需要解决哪些核心技术和伦理问题？"
        )
        
        print(f"复杂问题: {complex_question.content[:50]}...")
        
        start_time = time.time()
        result = await self.ultrathink.analyze_question(complex_question)
        end_time = time.time()
        
        print(f"✅ Think Harder分析完成 (用时: {end_time - start_time:.2f}秒)")
        print(f"📊 问题类型: {result.question_profile.problem_type.value}")
        print(f"📈 复杂度: {result.question_profile.complexity_level.name}")
        print(f"🧠 思考模式: {result.thinking_mode_used.value}")
        print(f"⭐ 质量分数: {result.quality_score:.1f}")
        print(f"🔍 认知负荷: {result.question_profile.cognitive_load:.2f}")
        
        if result.thinking_mode_used == ThinkingMode.THINK_HARDER:
            print("🌟 已启用Think Harder深度思考模式！")
            print(f"📄 Think Harder分析长度: {len(result.think_harder_analysis)} 字符")
            print("🎯 Think Harder包含6个思考层次:")
            print("  1. 思维预热")
            print("  2. 多角度思考 (5个视角)")
            print("  3. 深度分析 (3层解构)")
            print("  4. 创新突破")
            print("  5. 综合整合")
            print("  6. 反思验证")
    
    async def demo_problem_identification(self):
        """问题类型识别演示"""
        print("\n🎯 3. 智能问题识别演示")
        print("-" * 40)
        
        # 不同类型的问题
        test_cases = [
            ("证明题", "证明勾股定理"),
            ("概念题", "什么是机器学习？"),
            ("计算题", "计算圆的面积，半径为5"),
            ("分析题", "分析深度学习的优缺点"),
            ("创新题", "设计一个革命性的教育系统"),
            ("比较题", "比较Python和Java的特点"),
            ("因果题", "为什么会发生经济危机？"),
            ("程序题", "如何学习编程？"),
            ("评价题", "评价人工智能的发展前景")
        ]
        
        print("🔍 问题类型识别测试:")
        for case_type, question_text in test_cases:
            question = QuestionV4(f"ID_{case_type}", question_text)
            result = await self.ultrathink.analyze_question(question)
            
            print(f"  {case_type:6} | {question_text:25} → {result.question_profile.problem_type.value}")
    
    async def demo_smart_routing(self):
        """智能路由演示"""
        print("\n🚦 4. 智能路由系统演示")
        print("-" * 40)
        
        # 不同复杂度的问题
        routing_cases = [
            ("简单", "1+1等于多少？"),
            ("中等", "解释函数的概念"),
            ("复杂", "分析量子计算对密码学的影响"),
            ("极复杂", "设计一个能够自我进化的人工智能系统架构")
        ]
        
        print("🧭 路由决策演示:")
        for complexity, question_text in routing_cases:
            question = QuestionV4(f"ROUTE_{complexity}", question_text)
            result = await self.ultrathink.analyze_question(question)
            
            thinking_mode = result.thinking_mode_used.value
            complexity_level = result.question_profile.complexity_level.name
            
            print(f"  {complexity:6} | {thinking_mode:15} | {complexity_level}")
    
    async def demo_batch_processing(self):
        """批量处理演示"""
        print("\n📦 5. 批量处理演示")
        print("-" * 40)
        
        # 创建多个问题
        batch_questions = [
            QuestionV4("B001", "什么是深度学习？"),
            QuestionV4("B002", "证明欧拉公式"),
            QuestionV4("B003", "如何解决气候变化问题？"),
            QuestionV4("B004", "比较不同排序算法的效率"),
            QuestionV4("B005", "设计未来的交通系统")
        ]
        
        print(f"📊 处理 {len(batch_questions)} 个问题...")
        
        start_time = time.time()
        results = []
        
        for i, question in enumerate(batch_questions, 1):
            result = await self.ultrathink.analyze_question(question)
            results.append(result)
            print(f"  进度: {i}/{len(batch_questions)} - {question.content[:30]}...")
        
        end_time = time.time()
        
        print(f"✅ 批量处理完成 (总用时: {end_time - start_time:.2f}秒)")
        print(f"📊 平均处理时间: {(end_time - start_time) / len(batch_questions):.2f}秒/问题")
        
        # 分析结果
        think_harder_count = sum(1 for r in results if r.thinking_mode_used == ThinkingMode.THINK_HARDER)
        avg_quality = sum(r.quality_score for r in results) / len(results)
        
        print(f"🧠 Think Harder使用次数: {think_harder_count}/{len(batch_questions)}")
        print(f"⭐ 平均质量分数: {avg_quality:.1f}")
    
    async def demo_statistics(self):
        """统计信息演示"""
        print("\n📊 6. 系统统计信息")
        print("-" * 40)
        
        stats = self.ultrathink.get_statistics()
        
        print(f"📈 总处理数量: {stats['total_processed']}")
        print(f"🧠 Think Harder使用次数: {stats['think_harder_used']}")
        
        if stats['total_processed'] > 0:
            think_harder_rate = stats['think_harder_used'] / stats['total_processed'] * 100
            print(f"📊 Think Harder使用率: {think_harder_rate:.1f}%")
        
        print("\n🎯 问题类型分布:")
        for ptype, count in stats['problem_types'].items():
            percentage = count / stats['total_processed'] * 100
            print(f"  {ptype:12}: {count:2} ({percentage:4.1f}%)")
        
        print("\n📈 复杂度分布:")
        for complexity, count in stats['complexity_distribution'].items():
            percentage = count / stats['total_processed'] * 100
            print(f"  {complexity:15}: {count:2} ({percentage:4.1f}%)")
    
    async def demo_advanced_features(self):
        """高级功能演示"""
        print("\n🔧 7. 高级功能演示")
        print("-" * 40)
        
        # 带元数据的问题
        advanced_question = QuestionV4(
            id="ADV_001",
            content="如何优化大规模机器学习模型的训练效率？",
            metadata={
                "domain": "machine_learning",
                "difficulty": "expert",
                "time_limit": 1800,
                "requires_innovation": True
            }
        )
        
        print(f"高级问题: {advanced_question.content}")
        print(f"元数据: {advanced_question.metadata}")
        
        result = await self.ultrathink.analyze_question(advanced_question)
        
        print(f"✅ 分析完成")
        print(f"📊 详细画像:")
        print(f"  类型: {result.question_profile.problem_type.value}")
        print(f"  复杂度: {result.question_profile.complexity_level.name}")
        print(f"  领域: {result.question_profile.domain}")
        print(f"  关键词: {', '.join(result.question_profile.keywords)}")
        print(f"  认知负荷: {result.question_profile.cognitive_load:.2f}")
        print(f"  预估时间: {result.question_profile.estimated_time:.0f}秒")
        
        print(f"\n💡 智能洞察 ({len(result.insights)} 条):")
        for insight in result.insights:
            print(f"  • {insight}")
        
        print(f"\n📝 智能建议 ({len(result.recommendations)} 条):")
        for recommendation in result.recommendations:
            print(f"  • {recommendation}")

async def main():
    """主演示程序"""
    demo = UltraThinkV4Demo()
    
    print("🎮 欢迎使用 UltraThink v4.0 演示程序")
    print("🚀 新功能预览:")
    print("  ✅ 智能问题识别 (10种类型)")
    print("  ✅ Think Harder深度思考")
    print("  ✅ 单问题专用处理器")
    print("  ✅ 智能路由系统")
    print("  ✅ 复杂度评估 (5个级别)")
    print("  ✅ 认知负荷计算")
    print("  ✅ 实时统计分析")
    
    try:
        await demo.run_all_demos()
        
        # 运行高级功能演示
        await demo.demo_advanced_features()
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        raise
    
    print("\n🎉 演示程序结束")
    print("💡 提示: 查看 ultrathink_v4_usage_guide.md 了解详细使用方法")

if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())