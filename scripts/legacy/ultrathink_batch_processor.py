#!/usr/bin/env python3
"""
UltraThink v3.0 批处理管理器
支持大规模问题分析和智能调度
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
import logging
from dataclasses import asdict
import pandas as pd
from tqdm import tqdm
import argparse

# 导入主系统
from ultrathink_v3 import UltraThinkV3, Question, AnalysisResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultrathink_batch.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('UltraThink_BatchManager')


class UltraThinkBatchProcessor:
    """增强版批处理器"""
    
    def __init__(self, config_path: str = 'ultrathink_config.json'):
        """初始化批处理器"""
        self.ultrathink = UltraThinkV3(config_path)
        self.results_cache = {}
        self.statistics = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0,
            'quality_distribution': {}
        }
    
    async def process_file(self, input_file: str, output_dir: str = None) -> Dict:
        """处理输入文件中的问题"""
        logger.info(f"开始处理文件: {input_file}")
        
        # 读取问题列表
        questions = self._load_questions_from_file(input_file)
        logger.info(f"已加载 {len(questions)} 个问题")
        
        # 设置输出目录
        if output_dir is None:
            output_dir = f"./batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 批量处理
        start_time = time.time()
        results = await self._process_questions_with_progress(questions)
        total_time = time.time() - start_time
        
        # 生成报告
        report = self._generate_batch_report(results, total_time)
        
        # 保存结果
        self._save_batch_results(results, report, output_dir)
        
        logger.info(f"批处理完成！总用时: {total_time:.2f}秒")
        return report
    
    def _load_questions_from_file(self, file_path: str) -> List[Question]:
        """从文件加载问题"""
        questions = []
        
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict):
                        questions.append(Question(
                            id=str(item.get('id', len(questions) + 1)),
                            content=item['content'],
                            category=item.get('category')
                        ))
                    else:
                        questions.append(Question(
                            id=str(len(questions) + 1),
                            content=str(item)
                        ))
        
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line:
                        questions.append(Question(
                            id=str(i + 1).zfill(3),
                            content=line
                        ))
        
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            for i, row in df.iterrows():
                questions.append(Question(
                    id=str(row.get('id', i + 1)),
                    content=row['content'],
                    category=row.get('category')
                ))
        
        return questions
    
    async def _process_questions_with_progress(self, questions: List[Question]) -> List[AnalysisResult]:
        """带进度条的批量处理"""
        results = []
        
        # 创建进度条
        with tqdm(total=len(questions), desc="分析进度", unit="题") as pbar:
            # 分批处理
            batch_size = self.ultrathink.config['batch_settings']['batch_size']
            
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                
                # 异步处理当前批次
                tasks = []
                for q in batch:
                    task = self._process_single_question_safe(q)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks)
                
                # 更新结果和统计
                for result in batch_results:
                    if result:
                        results.append(result)
                        self.statistics['successful'] += 1
                        
                        # 更新质量分布
                        quality_level = self._get_quality_level(result.quality_score)
                        self.statistics['quality_distribution'][quality_level] = \
                            self.statistics['quality_distribution'].get(quality_level, 0) + 1
                    else:
                        self.statistics['failed'] += 1
                
                # 更新进度条
                pbar.update(len(batch))
                
                # 显示当前统计
                pbar.set_postfix({
                    '成功': self.statistics['successful'],
                    '失败': self.statistics['failed'],
                    '平均质量': self._calculate_average_quality(results)
                })
        
        self.statistics['total_processed'] = len(questions)
        return results
    
    async def _process_single_question_safe(self, question: Question) -> Optional[AnalysisResult]:
        """安全地处理单个问题（带错误处理）"""
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(question)
            if cache_key in self.results_cache:
                logger.debug(f"从缓存返回问题 {question.id}")
                return self.results_cache[cache_key]
            
            # 处理问题
            result = await self.ultrathink.analyze_question(question)
            
            # 缓存结果
            self.results_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"处理问题 {question.id} 时出错: {str(e)}")
            return None
    
    def _generate_cache_key(self, question: Question) -> str:
        """生成缓存键"""
        import hashlib
        content_hash = hashlib.md5(question.content.encode()).hexdigest()
        return f"{question.category}_{content_hash}"
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量级别"""
        if score >= 9:
            return "专家级"
        elif score >= 7:
            return "深度"
        elif score >= 5:
            return "标准"
        else:
            return "基础"
    
    def _calculate_average_quality(self, results: List[AnalysisResult]) -> float:
        """计算平均质量分数"""
        if not results:
            return 0.0
        total_score = sum(r.quality_score for r in results)
        return round(total_score / len(results), 2)
    
    def _generate_batch_report(self, results: List[AnalysisResult], total_time: float) -> Dict:
        """生成批处理报告"""
        report = {
            'summary': {
                'total_questions': self.statistics['total_processed'],
                'successful': self.statistics['successful'],
                'failed': self.statistics['failed'],
                'success_rate': f"{(self.statistics['successful'] / self.statistics['total_processed'] * 100):.1f}%",
                'total_time': f"{total_time:.2f}秒",
                'average_time_per_question': f"{total_time / self.statistics['total_processed']:.2f}秒"
            },
            'quality_analysis': {
                'average_score': self._calculate_average_quality(results),
                'distribution': self.statistics['quality_distribution'],
                'highest_score': max((r.quality_score for r in results), default=0),
                'lowest_score': min((r.quality_score for r in results), default=0)
            },
            'performance_metrics': {
                'questions_per_minute': round(self.statistics['total_processed'] / (total_time / 60), 2),
                'cache_hit_rate': f"{(len(self.results_cache) / self.statistics['total_processed'] * 100):.1f}%"
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _save_batch_results(self, results: List[AnalysisResult], report: Dict, output_dir: str):
        """保存批处理结果"""
        # 保存详细报告
        report_path = os.path.join(output_dir, 'batch_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存结果汇总
        summary_data = []
        for result in results:
            summary_data.append({
                'question_id': result.question_id,
                'quality_score': result.quality_score,
                'processing_time': result.processing_time,
                'save_path': result.save_path
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(os.path.join(output_dir, 'results_summary.csv'), index=False)
        
        # 生成HTML报告
        self._generate_html_report(report, results, output_dir)
        
        logger.info(f"结果已保存到: {output_dir}")
    
    def _generate_html_report(self, report: Dict, results: List[AnalysisResult], output_dir: str):
        """生成HTML格式的报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>UltraThink v3.0 批处理报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .quality-badge {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .quality-expert {{
            background-color: #28a745;
            color: white;
        }}
        .quality-deep {{
            background-color: #17a2b8;
            color: white;
        }}
        .quality-standard {{
            background-color: #ffc107;
            color: black;
        }}
        .quality-basic {{
            background-color: #6c757d;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 UltraThink v3.0 批处理报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 总体统计</h2>
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{report['summary']['total_questions']}</div>
                <div class="metric-label">总问题数</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['summary']['success_rate']}</div>
                <div class="metric-label">成功率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['quality_analysis']['average_score']:.1f}</div>
                <div class="metric-label">平均质量分</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report['performance_metrics']['questions_per_minute']}</div>
                <div class="metric-label">问题/分钟</div>
            </div>
        </div>
        
        <h2>📈 质量分布</h2>
        <table>
            <tr>
                <th>质量级别</th>
                <th>数量</th>
                <th>占比</th>
            </tr>
"""
        
        # 添加质量分布数据
        total = report['summary']['total_questions']
        for level, count in report['quality_analysis']['distribution'].items():
            percentage = (count / total * 100) if total > 0 else 0
            html_content += f"""
            <tr>
                <td><span class="quality-badge quality-{level.lower()}">{level}</span></td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
        
        html_content += """
        </table>
        
        <h2>📝 处理详情</h2>
        <table>
            <tr>
                <th>问题ID</th>
                <th>质量分数</th>
                <th>处理时间</th>
                <th>质量级别</th>
            </tr>
"""
        
        # 添加前20个结果的详情
        for result in results[:20]:
            quality_level = self._get_quality_level(result.quality_score)
            html_content += f"""
            <tr>
                <td>{result.question_id}</td>
                <td>{result.quality_score:.1f}</td>
                <td>{result.processing_time:.2f}秒</td>
                <td><span class="quality-badge quality-{quality_level.lower()}">{quality_level}</span></td>
            </tr>
"""
        
        if len(results) > 20:
            html_content += f"""
            <tr>
                <td colspan="4" style="text-align: center; padding: 20px;">
                    ... 还有 {len(results) - 20} 个结果，请查看完整CSV文件
                </td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
</body>
</html>
"""
        
        # 保存HTML文件
        html_path = os.path.join(output_dir, 'batch_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='UltraThink v3.0 批处理工具')
    parser.add_argument('input_file', help='输入文件路径 (支持.json, .txt, .csv)')
    parser.add_argument('-o', '--output', help='输出目录路径', default=None)
    parser.add_argument('-c', '--config', help='配置文件路径', default='ultrathink_config.json')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input_file):
        logger.error(f"输入文件不存在: {args.input_file}")
        return
    
    # 创建批处理器
    processor = UltraThinkBatchProcessor(args.config)
    
    # 处理文件
    try:
        report = await processor.process_file(args.input_file, args.output)
        
        # 打印摘要
        print("\n" + "="*50)
        print("批处理完成！")
        print(f"总问题数: {report['summary']['total_questions']}")
        print(f"成功率: {report['summary']['success_rate']}")
        print(f"平均质量分: {report['quality_analysis']['average_score']:.1f}")
        print(f"总用时: {report['summary']['total_time']}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"批处理失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())