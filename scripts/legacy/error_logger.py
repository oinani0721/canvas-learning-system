"""
错误日志和诊断系统 (Error Logger and Diagnostic System)

该模块负责实现结构化错误日志记录、错误分类和诊断报告生成。
"""

import asyncio
import json
import logging
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, TextIO
from pathlib import Path
import gzip
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import os

# 导入类型定义
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# 导入其他模块的类型
from error_isolation_manager import (
    ErrorInfo, ErrorCategory, ErrorSeverity,
    HealthCheckResult, FailurePattern
)
from retry_manager import RetryState, RetryAttempt
from graceful_degradation_manager import DegradationLevel, ErrorRecoveryResult


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DiagnosticLevel(Enum):
    """诊断级别"""
    BASIC = "basic"          # 基础诊断
    DETAILED = "detailed"    # 详细诊断
    COMPREHENSIVE = "comprehensive"  # 全面诊断


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    category: str
    message: str
    error_info: Optional[ErrorInfo] = None
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    correlation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.error_info:
            data['error_info'] = asdict(self.error_info)
            data['error_info']['timestamp'] = self.error_info.timestamp.isoformat()
        return data


@dataclass
class DiagnosticReport:
    """诊断报告"""
    report_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    diagnostic_level: DiagnosticLevel = DiagnosticLevel.BASIC
    time_range: Dict[str, datetime] = field(default_factory=dict)
    error_summary: Dict[str, Any] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    system_health: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        for key in ['start_time', 'end_time']:
            if key in data.get('time_range', {}):
                data['time_range'][key] = data['time_range'][key].isoformat()
        return data


@dataclass
class ErrorStatistics:
    """错误统计"""
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    errors_by_hour: Dict[str, int] = field(default_factory=dict)
    top_errors: List[Dict[str, Any]] = field(default_factory=list)
    error_rate: float = 0.0
    recovery_rate: float = 0.0


class ErrorLogger:
    """
    错误日志记录器

    负责记录和管理系统错误日志。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化错误日志记录器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.ErrorLogger")

        # 配置参数
        self.log_dir = Path(self.config.get('log_dir', 'logs/errors'))
        self.diagnostic_dir = Path(self.config.get('diagnostic_dir', 'logs/diagnostics'))
        self.max_log_size = self.config.get('max_log_size', 100 * 1024 * 1024)  # 100MB
        self.max_log_files = self.config.get('max_log_files', 10)
        self.compress_logs = self.config.get('compress_logs', True)
        self.async_logging = self.config.get('async_logging', True)

        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.diagnostic_dir.mkdir(parents=True, exist_ok=True)

        # 内部状态
        self._log_entries: List[LogEntry] = []
        self._error_index: Dict[str, List[str]] = {}  # 错误类型到日志ID的映射
        self._diagnostic_cache: Dict[str, DiagnosticReport] = {}

        # 线程安全
        self._lock = threading.RLock()

        # 异步日志队列
        if self.async_logging:
            self._log_queue = queue.Queue(maxsize=10000)
            self._queue_processor = threading.Thread(
                target=self._process_log_queue,
                daemon=True,
                name="ErrorLoggerQueueProcessor"
            )
            self._queue_processor.start()
        else:
            self._log_queue = None

        # 文件句柄管理
        self._file_handles: Dict[str, TextIO] = {}
        self._current_date = datetime.now().date()

        # 注册清理函数
        import atexit
        atexit.register(self.shutdown)

    def log_error(self,
                  error_info: ErrorInfo,
                  level: LogLevel = LogLevel.ERROR,
                  context: Optional[Dict[str, Any]] = None,
                  source: str = "system",
                  correlation_id: Optional[str] = None,
                  tags: Optional[List[str]] = None) -> str:
        """
        记录错误

        Args:
            error_info: 错误信息
            level: 日志级别
            context: 上下文信息
            source: 错误来源
            correlation_id: 关联ID
            tags: 标签列表

        Returns:
            str: 日志条目ID
        """
        entry_id = self._generate_entry_id(error_info)

        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=error_info.error_category.value,
            message=error_info.error_message,
            error_info=error_info,
            context=context or {},
            source=source,
            correlation_id=correlation_id,
            tags=tags or [],
            metadata={'entry_id': entry_id}
        )

        if self.async_logging:
            try:
                self._log_queue.put_nowait(log_entry)
            except queue.Full:
                self.logger.error("日志队列已满，丢弃日志条目")
        else:
            self._write_log_entry(log_entry)

        return entry_id

    def _generate_entry_id(self, error_info: ErrorInfo) -> str:
        """生成日志条目ID"""
        content = f"{error_info.timestamp.isoformat()}{error_info.error_code}{error_info.instance_id or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _process_log_queue(self) -> None:
        """处理日志队列"""
        while True:
            try:
                log_entry = self._log_queue.get(timeout=1)
                self._write_log_entry(log_entry)
                self._log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"处理日志队列错误: {str(e)}")

    def _write_log_entry(self, log_entry: LogEntry) -> None:
        """写入日志条目"""
        try:
            # 检查日期是否变化
            current_date = datetime.now().date()
            if current_date != self._current_date:
                self._rotate_daily_logs()
                self._current_date = current_date

            # 获取日志文件路径
            log_file_path = self._get_log_file_path(log_entry.category, log_entry.level)

            # 写入文件
            with self._lock:
                # 保存到内存
                self._log_entries.append(log_entry)

                # 更新索引
                category = log_entry.category
                if category not in self._error_index:
                    self._error_index[category] = []
                self._error_index[category].append(log_entry.metadata['entry_id'])

                # 写入文件
                self._write_to_file(log_file_path, log_entry)

                # 清理内存（保留最近10000条）
                if len(self._log_entries) > 10000:
                    self._log_entries = self._log_entries[-10000:]

        except Exception as e:
            self.logger.error(f"写入日志条目失败: {str(e)}")

    def _get_log_file_path(self, category: str, level: LogLevel) -> Path:
        """获取日志文件路径"""
        date_str = self._current_date.strftime('%Y-%m-%d')
        filename = f"{category}_{level.value}_{date_str}.log"
        return self.log_dir / filename

    def _write_to_file(self, file_path: Path, log_entry: LogEntry) -> None:
        """写入文件"""
        try:
            # 检查文件大小
            if file_path.exists() and file_path.stat().st_size > self.max_log_size:
                self._rotate_log_file(file_path)

            # 打开文件并写入
            with open(file_path, 'a', encoding='utf-8') as f:
                log_line = json.dumps(log_entry.to_dict(), ensure_ascii=False)
                f.write(log_line + '\n')

        except Exception as e:
            self.logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")

    def _rotate_daily_logs(self) -> None:
        """轮转日常日志"""
        try:
            # 压缩昨天的日志
            yesterday = self._current_date - timedelta(days=1)
            self._compress_date_logs(yesterday)

            # 清理过期日志
            self._cleanup_old_logs()

        except Exception as e:
            self.logger.error(f"轮转日常日志失败: {str(e)}")

    def _rotate_log_file(self, file_path: Path) -> None:
        """轮转日志文件"""
        try:
            # 重命名当前文件
            base_name = file_path.stem
            extension = file_path.suffix
            directory = file_path.parent

            for i in range(1, self.max_log_files + 1):
                new_name = f"{base_name}.{i}{extension}"
                new_path = directory / new_name
                if not new_path.exists():
                    file_path.rename(new_path)
                    break
            else:
                # 达到最大文件数，删除最旧的
                oldest_name = f"{base_name}.{self.max_log_files}{extension}"
                oldest_path = directory / oldest_name
                if oldest_path.exists():
                    oldest_path.unlink()
                file_path.rename(oldest_path)

            # 压缩轮转的文件
            if self.compress_logs:
                self._compress_rotated_files(directory, base_name, extension)

        except Exception as e:
            self.logger.error(f"轮转日志文件失败: {str(e)}")

    def _compress_date_logs(self, date: datetime.date) -> None:
        """压缩指定日期的日志"""
        if not self.compress_logs:
            return

        try:
            date_str = date.strftime('%Y-%m-%d')
            pattern = f"*_{date_str}.log"

            for log_file in self.log_dir.glob(pattern):
                compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                if not compressed_file.exists():
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    log_file.unlink()

        except Exception as e:
            self.logger.error(f"压缩日志失败: {str(e)}")

    def _compress_rotated_files(self, directory: Path, base_name: str, extension: str) -> None:
        """压缩轮转的文件"""
        if not self.compress_logs:
            return

        try:
            for i in range(1, self.max_log_files + 1):
                file_name = f"{base_name}.{i}{extension}"
                file_path = directory / file_name
                if file_path.exists():
                    compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                    if not compressed_path.exists():
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                f_out.writelines(f_in)
                        file_path.unlink()

        except Exception as e:
            self.logger.error(f"压缩轮转文件失败: {str(e)}")

    def _cleanup_old_logs(self) -> None:
        """清理过期日志"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=30)

            # 清理日志文件
            for log_file in self.log_dir.glob('*.log'):
                file_date = self._extract_date_from_filename(log_file.name)
                if file_date and file_date < cutoff_date:
                    log_file.unlink()

            # 清理压缩文件
            for gz_file in self.log_dir.glob('*.log.gz'):
                file_date = self._extract_date_from_filename(gz_file.name)
                if file_date and file_date < cutoff_date:
                    gz_file.unlink()

        except Exception as e:
            self.logger.error(f"清理过期日志失败: {str(e)}")

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime.date]:
        """从文件名提取日期"""
        try:
            # 文件名格式: category_level_YYYY-MM-DD.log
            parts = filename.split('_')
            if len(parts) >= 3:
                date_str = parts[-1].split('.')[0]
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            pass
        return None


class DiagnosticCollector:
    """
    诊断收集器

    负责收集和分析错误信息，生成诊断报告。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化诊断收集器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.DiagnosticCollector")

        # 配置参数
        self.diagnostic_dir = Path(self.config.get('diagnostic_dir', 'logs/diagnostics'))
        self.analysis_window = self.config.get('analysis_window', 24)  # 小时
        self.max_reports = self.config.get('max_reports', 100)

        # 创建目录
        self.diagnostic_dir.mkdir(parents=True, exist_ok=True)

        # 依赖注入
        self.error_logger: Optional[ErrorLogger] = None

    def set_error_logger(self, error_logger: ErrorLogger) -> None:
        """设置错误日志记录器"""
        self.error_logger = error_logger

    async def generate_diagnostic_report(self,
                                       diagnostic_level: DiagnosticLevel = DiagnosticLevel.BASIC,
                                       time_range: Optional[Dict[str, datetime]] = None,
                                       filters: Optional[Dict[str, Any]] = None) -> DiagnosticReport:
        """
        生成诊断报告

        Args:
            diagnostic_level: 诊断级别
            time_range: 时间范围
            filters: 过滤条件

        Returns:
            DiagnosticReport: 诊断报告
        """
        report_id = f"diag_{datetime.now().strftime('%Y%m%d%H%M%S')}_{diagnostic_level.value}"

        try:
            # 设置时间范围
            if not time_range:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=self.analysis_window)
                time_range = {'start_time': start_time, 'end_time': end_time}

            # 收集错误数据
            error_data = await self._collect_error_data(time_range, filters)

            # 分析错误模式
            error_patterns = await self._analyze_error_patterns(error_data)

            # 计算系统健康度
            system_health = await self._calculate_system_health(error_data)

            # 生成建议
            recommendations = await self._generate_recommendations(
                error_patterns,
                system_health,
                diagnostic_level
            )

            # 详细分析
            detailed_analysis = {}
            if diagnostic_level in [DiagnosticLevel.DETAILED, DiagnosticLevel.COMPREHENSIVE]:
                detailed_analysis = await self._perform_detailed_analysis(error_data)

            # 计算指标
            metrics = self._calculate_metrics(error_data, time_range)

            # 创建报告
            report = DiagnosticReport(
                report_id=report_id,
                diagnostic_level=diagnostic_level,
                time_range=time_range,
                error_summary=self._create_error_summary(error_data),
                error_patterns=error_patterns,
                system_health=system_health,
                recommendations=recommendations,
                detailed_analysis=detailed_analysis,
                metrics=metrics
            )

            # 保存报告
            await self._save_diagnostic_report(report)

            self.logger.info(f"生成诊断报告: {report_id}, 级别: {diagnostic_level.value}")

            return report

        except Exception as e:
            self.logger.error(f"生成诊断报告失败: {str(e)}")
            raise

    async def _collect_error_data(self,
                                time_range: Dict[str, datetime],
                                filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """收集错误数据"""
        if not self.error_logger:
            return []

        # 从错误日志记录器获取数据
        with self.error_logger._lock:
            all_entries = self.error_logger._log_entries

        # 过滤时间范围
        filtered_entries = []
        for entry in all_entries:
            if time_range['start_time'] <= entry.timestamp <= time_range['end_time']:
                if self._matches_filters(entry, filters):
                    filtered_entries.append(entry.to_dict())

        return filtered_entries

    def _matches_filters(self, log_entry: LogEntry, filters: Optional[Dict[str, Any]]) -> bool:
        """检查日志条目是否匹配过滤条件"""
        if not filters:
            return True

        # 类别过滤
        if 'category' in filters:
            if log_entry.category != filters['category']:
                return False

        # 级别过滤
        if 'level' in filters:
            if log_entry.level != filters['level']:
                return False

        # 来源过滤
        if 'source' in filters:
            if log_entry.source != filters['source']:
                return False

        # 标签过滤
        if 'tags' in filters:
            required_tags = set(filters['tags'])
            if not required_tags.issubset(set(log_entry.tags)):
                return False

        return True

    async def _analyze_error_patterns(self, error_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析错误模式"""
        patterns = []

        # 按错误类型分组
        error_groups = {}
        for error in error_data:
            category = error.get('category', 'unknown')
            if category not in error_groups:
                error_groups[category] = []
            error_groups[category].append(error)

        # 分析每个错误组的模式
        for category, errors in error_groups.items():
            if len(errors) < 2:
                continue

            pattern = {
                'category': category,
                'count': len(errors),
                'frequency': len(errors) / 24,  # 每小时平均
                'time_pattern': self._detect_time_pattern(errors),
                'common_messages': self._get_common_messages(errors),
                'affected_sources': list(set(e.get('source', 'unknown') for e in errors)),
                'severity_distribution': self._calculate_severity_distribution(errors)
            }

            patterns.append(pattern)

        return sorted(patterns, key=lambda p: p['count'], reverse=True)

    def _detect_time_pattern(self, errors: List[Dict[str, Any]]) -> str:
        """检测时间模式"""
        if len(errors) < 3:
            return "insufficient_data"

        # 按小时分组
        hour_counts = {}
        for error in errors:
            timestamp = datetime.fromisoformat(error['timestamp'])
            hour = timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # 判断模式
        if len(hour_counts) <= 3:
            return "concentrated"
        elif max(hour_counts.values()) / sum(hour_counts.values()) > 0.5:
            return "peak_hours"
        else:
            return "distributed"

    def _get_common_messages(self, errors: List[Dict[str, Any]], top_n: int = 5) -> List[str]:
        """获取常见错误消息"""
        message_counts = {}
        for error in errors:
            message = error.get('message', '')
            # 简化消息，去除时间戳等变化部分
            simplified = self._simplify_error_message(message)
            message_counts[simplified] = message_counts.get(simplified, 0) + 1

        # 返回最常见的消息
        sorted_messages = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
        return [msg for msg, count in sorted_messages[:top_n]]

    def _simplify_error_message(self, message: str) -> str:
        """简化错误消息"""
        # 移除时间戳、ID等变化部分
        import re
        message = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '[timestamp]', message)
        message = re.sub(r'\b[0-9a-fA-F]{8,}\b', '[id]', message)
        message = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '[ip]', message)
        return message

    def _calculate_severity_distribution(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算严重程度分布"""
        distribution = {}
        for error in errors:
            if 'error_info' in error and error['error_info']:
                severity = error['error_info'].get('severity', 'unknown')
            else:
                level = error.get('level', 'unknown')
                severity = level

            distribution[severity] = distribution.get(severity, 0) + 1

        return distribution

    async def _calculate_system_health(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算系统健康度"""
        if not error_data:
            return {'score': 100, 'status': 'healthy'}

        # 计算健康度分数
        total_errors = len(error_data)
        critical_errors = sum(1 for e in error_data if e.get('level') == 'critical')
        error_rate = total_errors / 24  # 每小时错误数

        # 健康度评分
        score = 100
        if critical_errors > 0:
            score -= critical_errors * 20
        if error_rate > 10:
            score -= min(50, (error_rate - 10) * 2)

        score = max(0, score)

        # 健康状态
        if score >= 90:
            status = 'healthy'
        elif score >= 70:
            status = 'warning'
        elif score >= 50:
            status = 'degraded'
        else:
            status = 'critical'

        return {
            'score': score,
            'status': status,
            'total_errors': total_errors,
            'critical_errors': critical_errors,
            'error_rate_per_hour': error_rate
        }

    async def _generate_recommendations(self,
                                       error_patterns: List[Dict[str, Any]],
                                       system_health: Dict[str, Any],
                                       diagnostic_level: DiagnosticLevel) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于系统健康度的建议
        if system_health['status'] == 'critical':
            recommendations.append("系统处于关键状态，需要立即干预")
            recommendations.append("检查系统资源（CPU、内存、磁盘空间）")
        elif system_health['status'] == 'degraded':
            recommendations.append("系统性能下降，建议优化配置")
        elif system_health['status'] == 'warning':
            recommendations.append("监控错误趋势，预防问题扩大")

        # 基于错误模式的建议
        for pattern in error_patterns[:3]:  # 只处理前3个最常见的模式
            category = pattern['category']
            count = pattern['count']

            if category == 'network' and count > 5:
                recommendations.append("检查网络连接和防火墙设置")
            elif category == 'timeout' and count > 3:
                recommendations.append("调整超时设置或优化响应时间")
            elif category == 'memory_overflow' and count > 1:
                recommendations.append("优化内存使用或增加系统内存")
            elif category == 'api_limit' and count > 2:
                recommendations.append("检查API配额或实施限流策略")

        # 基于诊断级别的建议
        if diagnostic_level == DiagnosticLevel.COMPREHENSIVE:
            recommendations.append("定期进行全面的系统诊断")
            recommendations.append("建立自动化监控和告警机制")

        return list(set(recommendations))  # 去重

    async def _perform_detailed_analysis(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行详细分析"""
        analysis = {
            'correlation_analysis': self._analyze_correlations(error_data),
            'trend_analysis': self._analyze_trends(error_data),
            'impact_analysis': self._analyze_impact(error_data),
            'root_cause_analysis': self._analyze_root_causes(error_data)
        }

        return analysis

    def _analyze_correlations(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析错误关联性"""
        correlations = {}

        # 按关联ID分组
        correlation_groups = {}
        for error in error_data:
            correlation_id = error.get('correlation_id')
            if correlation_id:
                if correlation_id not in correlation_groups:
                    correlation_groups[correlation_id] = []
                correlation_groups[correlation_id].append(error)

        # 找出有关联的错误链
        error_chains = []
        for correlation_id, errors in correlation_groups.items():
            if len(errors) > 1:
                chain = {
                    'correlation_id': correlation_id,
                    'error_count': len(errors),
                    'duration': self._calculate_chain_duration(errors),
                    'categories': list(set(e.get('category') for e in errors))
                }
                error_chains.append(chain)

        correlations['error_chains'] = error_chains
        correlations['total_chains'] = len(error_chains)

        return correlations

    def _calculate_chain_duration(self, errors: List[Dict[str, Any]]) -> float:
        """计算错误链持续时间"""
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in errors]
        return (max(timestamps) - min(timestamps)).total_seconds()

    def _analyze_trends(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析趋势"""
        # 按小时统计
        hourly_counts = {}
        for error in error_data:
            timestamp = datetime.fromisoformat(error['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1

        # 计算趋势
        hours = sorted(hourly_counts.keys())
        if len(hours) < 2:
            return {'trend': 'insufficient_data'}

        recent_avg = sum(hourly_counts[h] for h in hours[-6:]) / min(6, len(hours))
        earlier_avg = sum(hourly_counts[h] for h in hours[:-6]) / max(1, len(hours) - 6)

        if recent_avg > earlier_avg * 1.2:
            trend = 'increasing'
        elif recent_avg < earlier_avg * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'hourly_distribution': hourly_counts,
            'peak_hour': max(hourly_counts, key=hourly_counts.get) if hourly_counts else None
        }

    def _analyze_impact(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析影响"""
        # 按来源统计
        source_counts = {}
        for error in error_data:
            source = error.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        # 找出最受影响的组件
        affected_components = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            'affected_sources': dict(source_counts),
            'most_affected': affected_components[:5] if affected_components else [],
            'total_affected_sources': len(source_counts)
        }

    def _analyze_root_causes(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析根本原因"""
        # 简单的根本原因分析
        root_causes = {}

        # 基于错误消息模式
        message_patterns = {}
        for error in error_data:
            pattern = self._simplify_error_message(error.get('message', ''))
            if pattern not in message_patterns:
                message_patterns[pattern] = {'count': 0, 'categories': set()}
            message_patterns[pattern]['count'] += 1
            message_patterns[pattern]['categories'].add(error.get('category'))

        # 提取可能的原因
        for pattern, info in message_patterns.items():
            if info['count'] > 2:  # 出现3次以上
                cause = self._infer_root_cause(pattern, info['categories'])
                root_causes[cause] = root_causes.get(cause, 0) + info['count']

        return {
            'potential_causes': root_causes,
            'most_likely': max(root_causes, key=root_causes.get) if root_causes else None
        }

    def _infer_root_cause(self, pattern: str, categories: set) -> str:
        """推断根本原因"""
        if 'connection' in pattern.lower() or 'network' in pattern.lower():
            return "网络连接问题"
        elif 'timeout' in pattern.lower():
            return "响应超时"
        elif 'permission' in pattern.lower() or 'access' in pattern.lower():
            return "权限问题"
        elif 'memory' in pattern.lower() or 'out of memory' in pattern.lower():
            return "内存不足"
        elif 'disk' in pattern.lower() or 'space' in pattern.lower():
            return "磁盘空间不足"
        else:
            return "应用程序错误"

    def _calculate_metrics(self, error_data: List[Dict[str, Any]], time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """计算指标"""
        if not error_data:
            return {}

        duration_hours = (time_range['end_time'] - time_range['start_time']).total_seconds() / 3600

        return {
            'total_errors': len(error_data),
            'errors_per_hour': len(error_data) / duration_hours if duration_hours > 0 else 0,
            'unique_categories': len(set(e.get('category') for e in error_data)),
            'unique_sources': len(set(e.get('source') for e in error_data)),
            'avg_errors_per_category': len(error_data) / len(set(e.get('category') for e in error_data)) if error_data else 0
        }

    def _create_error_summary(self, error_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建错误摘要"""
        if not error_data:
            return {}

        # 统计各类错误
        category_counts = {}
        severity_counts = {}
        source_counts = {}

        for error in error_data:
            # 类别统计
            category = error.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1

            # 严重程度统计
            level = error.get('level', 'unknown')
            severity_counts[level] = severity_counts.get(level, 0) + 1

            # 来源统计
            source = error.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            'total_errors': len(error_data),
            'by_category': category_counts,
            'by_severity': severity_counts,
            'by_source': source_counts,
            'most_common_category': max(category_counts, key=category_counts.get) if category_counts else None,
            'most_common_source': max(source_counts, key=source_counts.get) if source_counts else None
        }

    async def _save_diagnostic_report(self, report: DiagnosticReport) -> None:
        """保存诊断报告"""
        try:
            report_file = self.diagnostic_dir / f"{report.report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

            # 保留最新的报告
            self._cleanup_old_reports()

        except Exception as e:
            self.logger.error(f"保存诊断报告失败: {str(e)}")

    def _cleanup_old_reports(self) -> None:
        """清理旧报告"""
        try:
            reports = list(self.diagnostic_dir.glob('diag_*.json'))
            if len(reports) > self.max_reports:
                # 按创建时间排序，删除最旧的
                reports.sort(key=lambda p: p.stat().st_mtime)
                for report in reports[:-self.max_reports]:
                    report.unlink()

        except Exception as e:
            self.logger.error(f"清理旧报告失败: {str(e)}")

    def get_diagnostic_report(self, report_id: str) -> Optional[DiagnosticReport]:
        """
        获取诊断报告

        Args:
            report_id: 报告ID

        Returns:
            Optional[DiagnosticReport]: 诊断报告
        """
        report_file = self.diagnostic_dir / f"{report_id}.json"
        if not report_file.exists():
            return None

        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换为DiagnosticReport对象
            report = DiagnosticReport(
                report_id=data['report_id'],
                generated_at=datetime.fromisoformat(data['generated_at']),
                diagnostic_level=DiagnosticLevel(data['diagnostic_level']),
                time_range=data.get('time_range', {}),
                error_summary=data.get('error_summary', {}),
                error_patterns=data.get('error_patterns', []),
                system_health=data.get('system_health', {}),
                recommendations=data.get('recommendations', []),
                detailed_analysis=data.get('detailed_analysis', {}),
                metrics=data.get('metrics', {})
            )

            return report

        except Exception as e:
            self.logger.error(f"读取诊断报告失败: {str(e)}")
            return None

    def list_diagnostic_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        列出诊断报告

        Args:
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 报告列表
        """
        reports = []
        try:
            report_files = list(self.diagnostic_dir.glob('diag_*.json'))
            report_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            for report_file in report_files[:limit]:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                reports.append({
                    'report_id': data['report_id'],
                    'generated_at': data['generated_at'],
                    'diagnostic_level': data['diagnostic_level'],
                    'total_errors': data.get('error_summary', {}).get('total_errors', 0)
                })

        except Exception as e:
            self.logger.error(f"列出诊断报告失败: {str(e)}")

        return reports

    def shutdown(self) -> None:
        """关闭错误日志记录器"""
        try:
            # 停止队列处理器
            if self._log_queue and self._queue_processor and self._queue_processor.is_alive():
                self._log_queue.put(None)  # 发送停止信号
                self._queue_processor.join(timeout=5)

            # 关闭文件句柄
            with self._lock:
                for handle in self._file_handles.values():
                    try:
                        handle.close()
                    except:
                        pass
                self._file_handles.clear()

            # 清理状态
            self._log_entries.clear()
            self._error_index.clear()

            self.logger.info("错误日志记录器已关闭")

        except Exception as e:
            self.logger.error(f"关闭错误日志记录器时出错: {str(e)}")