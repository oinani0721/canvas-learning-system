"""
配置管理器 - Canvas学习系统

本模块实现性能配置管理功能，包括：
- 分层配置系统
- 配置验证和应用
- 配置档案管理
- 热更新支持

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Task 4
"""

import asyncio
import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import threading
import copy

# 配置数据模型


class ConfigurationScope(Enum):
    """配置作用域"""
    GLOBAL = "global"        # 全局默认配置
    USER = "user"           # 用户偏好配置
    SESSION = "session"     # 会话临时配置


class ConfigurationFormat(Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 实例管理
    max_concurrent_instances: int = 6
    min_instances: int = 1
    auto_scaling_enabled: bool = True
    scaling_threshold_cpu: float = 80.0
    scaling_threshold_memory: float = 85.0
    adjustment_cooldown_seconds: int = 60
    adjustment_strategy: str = "balanced"  # aggressive, conservative, balanced

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_max_size_mb: int = 500
    cache_max_entries: int = 10000
    cache_compression_enabled: bool = True
    cache_similarity_threshold: float = 0.8
    cache_eviction_policy: str = "lru_lfu"  # lru, lfu, lru_lfu, ttl

    # 性能监控
    monitoring_enabled: bool = True
    metrics_collection_interval_seconds: int = 30
    metrics_retention_days: int = 30
    alerts_enabled: bool = True
    slow_execution_threshold_seconds: int = 60
    memory_usage_alert_threshold_mb: int = 1024
    cpu_usage_alert_threshold_percent: int = 85

    # 基准测试
    benchmark_enabled: bool = True
    benchmark_auto_run: bool = False
    benchmark_interval_hours: int = 24
    target_efficiency_multiplier: float = 3.5  # 目标效率提升倍数

    # 调试和日志
    debug_mode: bool = False
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_performance_metrics: bool = True
    export_metrics: bool = False

    def validate(self) -> Tuple[bool, List[str]]:
        """验证配置有效性

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []

        # 验证实例配置
        if self.max_concurrent_instances < self.min_instances:
            errors.append("max_concurrent_instances must be >= min_instances")
        if self.max_concurrent_instances > 20:
            errors.append("max_concurrent_instances should not exceed 20")
        if self.min_instances < 0:
            errors.append("min_instances cannot be negative")

        # 验证阈值
        if not 0 <= self.scaling_threshold_cpu <= 100:
            errors.append("scaling_threshold_cpu must be between 0 and 100")
        if not 0 <= self.scaling_threshold_memory <= 100:
            errors.append("scaling_threshold_memory must be between 0 and 100")

        # 验证缓存配置
        if self.cache_max_size_mb < 1:
            errors.append("cache_max_size_mb must be at least 1")
        if self.cache_max_entries < 1:
            errors.append("cache_max_entries must be at least 1")
        if not 0 <= self.cache_similarity_threshold <= 1:
            errors.append("cache_similarity_threshold must be between 0 and 1")

        # 验证监控配置
        if self.metrics_collection_interval_seconds < 1:
            errors.append("metrics_collection_interval_seconds must be at least 1")
        if self.metrics_retention_days < 1:
            errors.append("metrics_retention_days must be at least 1")

        # 验证调整策略
        valid_strategies = ["aggressive", "conservative", "balanced"]
        if self.adjustment_strategy not in valid_strategies:
            errors.append(f"adjustment_strategy must be one of: {valid_strategies}")

        # 验证缓存策略
        valid_policies = ["lru", "lfu", "lru_lfu", "ttl"]
        if self.cache_eviction_policy not in valid_policies:
            errors.append(f"cache_eviction_policy must be one of: {valid_policies}")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """从字典创建配置"""
        return cls(**data)


@dataclass
class ConfigurationProfile:
    """配置档案"""
    profile_name: str
    description: str
    config: PerformanceConfig
    scope: ConfigurationScope = ConfigurationScope.USER
    is_default: bool = False
    is_readonly: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['config'] = self.config.to_dict()
        data['scope'] = self.scope.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationProfile':
        """从字典创建配置档案"""
        data = data.copy()
        data['config'] = PerformanceConfig.from_dict(data['config'])
        data['scope'] = ConfigurationScope(data['scope'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ConfigurationChange:
    """配置变更记录"""
    change_id: str
    profile_name: str
    field_path: str  # 字段路径，如 "cache.max_size"
    old_value: Any
    new_value: Any
    changed_at: datetime = field(default_factory=datetime.now)
    changed_by: str = "user"  # user, system, auto
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['changed_at'] = self.changed_at.isoformat()
        return data


class ConfigurationManager:
    """配置管理器

    提供分层配置管理、热更新、配置档案管理等功能。
    """

    def __init__(self, config_dir: str = "config"):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # 配置文件路径
        self.global_config_file = self.config_dir / "global_config.yaml"
        self.user_config_file = self.config_dir / "user_config.yaml"
        self.session_config_file = self.config_dir / "session_config.yaml"
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

        # 配置存储
        self.global_config: PerformanceConfig = PerformanceConfig()
        self.user_config: PerformanceConfig = PerformanceConfig()
        self.session_config: Optional[PerformanceConfig] = None
        self.current_config: PerformanceConfig = PerformanceConfig()

        # 配置档案
        self.profiles: Dict[str, ConfigurationProfile] = {}

        # 变更历史
        self.change_history: List[ConfigurationChange] = []
        self.max_history_size = 100

        # 监听器
        self.change_listeners: List[callable] = []

        # 线程锁
        self._lock = threading.RLock()

        # 初始化
        self._initialize_configs()
        self._load_profiles()

    def _initialize_configs(self) -> None:
        """初始化配置"""
        # 加载全局配置
        self.global_config = self._load_config_file(
            self.global_config_file,
            PerformanceConfig()
        )

        # 加载用户配置
        self.user_config = self._load_config_file(
            self.user_config_file,
            PerformanceConfig()
        )

        # 合并配置
        self._merge_configs()

        # 保存默认配置文件（如果不存在）
        self._save_default_configs()

    def _save_default_configs(self) -> None:
        """保存默认配置文件"""
        if not self.global_config_file.exists():
            self._save_config_file(self.global_config_file, self.global_config)

        if not self.user_config_file.exists():
            self._save_config_file(self.user_config_file, self.user_config)

    def _load_config_file(self, file_path: Path, default_config: PerformanceConfig) -> PerformanceConfig:
        """加载配置文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.suffix == '.json':
                        data = json.load(f)
                    else:  # YAML
                        data = yaml.safe_load(f)

                if data:
                    config = PerformanceConfig.from_dict(data)
                    # 验证配置
                    is_valid, errors = config.validate()
                    if not is_valid:
                        print(f"Invalid config in {file_path}: {errors}")
                        return default_config
                    return config

        except Exception as e:
            print(f"Failed to load config from {file_path}: {e}")

        return default_config

    def _save_config_file(self, file_path: Path, config: PerformanceConfig) -> bool:
        """保存配置文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
                else:  # YAML
                    yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)
            return True

        except Exception as e:
            print(f"Failed to save config to {file_path}: {e}")
            return False

    def _merge_configs(self) -> None:
        """合并配置（优先级: session > user > global）"""
        with self._lock:
            # 从全局配置开始
            merged = copy.deepcopy(self.global_config)

            # 应用用户配置
            user_dict = self.user_config.to_dict()
            self._deep_update(merged.to_dict(), user_dict)
            merged = PerformanceConfig.from_dict(merged.to_dict())

            # 应用会话配置
            if self.session_config:
                session_dict = self.session_config.to_dict()
                self._deep_update(merged.to_dict(), session_dict)
                merged = PerformanceConfig.from_dict(merged.to_dict())

            # 更新当前配置
            old_config = self.current_config
            self.current_config = merged

            # 触发变更事件
            self._notify_config_changed(old_config, merged)

    def _deep_update(self, target: Dict, source: Dict) -> None:
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    async def load_config(self, scope: ConfigurationScope = ConfigurationScope.USER) -> PerformanceConfig:
        """加载配置

        Args:
            scope: 配置作用域

        Returns:
            PerformanceConfig: 加载的配置
        """
        if scope == ConfigurationScope.GLOBAL:
            return self.global_config
        elif scope == ConfigurationScope.USER:
            return self.user_config
        elif scope == ConfigurationScope.SESSION:
            return self.session_config or PerformanceConfig()
        else:
            raise ValueError(f"Unknown scope: {scope}")

    async def save_config(self, config: PerformanceConfig, scope: ConfigurationScope = ConfigurationScope.USER) -> bool:
        """保存配置

        Args:
            config: 要保存的配置
            scope: 配置作用域

        Returns:
            bool: 是否成功
        """
        # 验证配置
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {errors}")

        with self._lock:
            # 保存到内存
            if scope == ConfigurationScope.GLOBAL:
                old_config = self.global_config
                self.global_config = config
                success = self._save_config_file(self.global_config_file, config)
            elif scope == ConfigurationScope.USER:
                old_config = self.user_config
                self.user_config = config
                success = self._save_config_file(self.user_config_file, config)
            elif scope == ConfigurationScope.SESSION:
                old_config = self.session_config
                self.session_config = config
                success = self._save_config_file(self.session_config_file, config)
            else:
                raise ValueError(f"Unknown scope: {scope}")

            if success:
                # 记录变更
                self._record_config_changes(old_config, config, scope.value)

                # 重新合并配置
                self._merge_configs()

        return success

    async def validate_config(self, config: PerformanceConfig) -> Tuple[bool, List[str]]:
        """验证配置有效性

        Args:
            config: 要验证的配置

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        return config.validate()

    async def apply_config_changes(self, changes: Dict[str, Any], scope: ConfigurationScope = ConfigurationScope.USER) -> bool:
        """应用配置变更

        Args:
            changes: 配置变更字典
            scope: 配置作用域

        Returns:
            bool: 是否成功
        """
        with self._lock:
            # 获取当前配置
            if scope == ConfigurationScope.GLOBAL:
                current_config = copy.deepcopy(self.global_config)
            elif scope == ConfigurationScope.USER:
                current_config = copy.deepcopy(self.user_config)
            elif scope == ConfigurationScope.SESSION:
                current_config = copy.deepcopy(self.session_config or PerformanceConfig())
            else:
                raise ValueError(f"Unknown scope: {scope}")

            # 应用变更
            config_dict = current_config.to_dict()
            self._deep_update(config_dict, changes)
            new_config = PerformanceConfig.from_dict(config_dict)

            # 保存配置
            return await self.save_config(new_config, scope)

    async def create_profile(self, profile: ConfigurationProfile) -> bool:
        """创建配置档案

        Args:
            profile: 配置档案

        Returns:
            bool: 是否成功
        """
        with self._lock:
            # 验证配置
            is_valid, errors = profile.config.validate()
            if not is_valid:
                raise ValueError(f"Invalid profile configuration: {errors}")

            # 检查是否已存在
            if profile.profile_name in self.profiles:
                return False

            # 保存档案
            profile.updated_at = datetime.now()
            self.profiles[profile.profile_name] = profile

            # 保存到文件
            profile_file = self.profiles_dir / f"{profile.profile_name}.yaml"
            success = self._save_profile_file(profile_file, profile)

            return success

    async def list_profiles(self) -> List[ConfigurationProfile]:
        """列出所有配置档案

        Returns:
            List[ConfigurationProfile]: 配置档案列表
        """
        with self._lock:
            return list(self.profiles.values())

    async def get_profile(self, profile_name: str) -> Optional[ConfigurationProfile]:
        """获取配置档案

        Args:
            profile_name: 档案名称

        Returns:
            Optional[ConfigurationProfile]: 配置档案
        """
        with self._lock:
            return self.profiles.get(profile_name)

    async def apply_profile(self, profile_name: str, scope: ConfigurationScope = ConfigurationScope.USER) -> bool:
        """应用配置档案

        Args:
            profile_name: 档案名称
            scope: 配置作用域

        Returns:
            bool: 是否成功
        """
        profile = await self.get_profile(profile_name)
        if not profile:
            return False

        # 更新使用次数
        profile.usage_count += 1
        profile.updated_at = datetime.now()

        # 保存档案
        profile_file = self.profiles_dir / f"{profile_name}.yaml"
        self._save_profile_file(profile_file, profile)

        # 应用配置
        success = await self.save_config(profile.config, scope)

        return success

    async def delete_profile(self, profile_name: str) -> bool:
        """删除配置档案

        Args:
            profile_name: 档案名称

        Returns:
            bool: 是否成功
        """
        with self._lock:
            if profile_name not in self.profiles:
                return False

            profile = self.profiles[profile_name]
            if profile.is_readonly:
                return False

            # 删除文件
            profile_file = self.profiles_dir / f"{profile_name}.yaml"
            if profile_file.exists():
                profile_file.unlink()

            # 从内存删除
            del self.profiles[profile_name]

            return True

    async def reset_to_default(self, scope: ConfigurationScope = ConfigurationScope.USER) -> bool:
        """重置为默认配置

        Args:
            scope: 配置作用域

        Returns:
            bool: 是否成功
        """
        default_config = PerformanceConfig()
        return await self.save_config(default_config, scope)

    async def export_config(self, file_path: str, include_profiles: bool = True) -> bool:
        """导出配置

        Args:
            file_path: 导出文件路径
            include_profiles: 是否包含档案

        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "global_config": self.global_config.to_dict(),
                "user_config": self.user_config.to_dict(),
                "current_config": self.current_config.to_dict(),
                "change_history": [c.to_dict() for c in self.change_history[-20:]]
            }

            if include_profiles:
                export_data["profiles"] = {
                    name: profile.to_dict()
                    for name, profile in self.profiles.items()
                }

            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)

            return True

        except Exception as e:
            print(f"Failed to export config: {e}")
            return False

    async def import_config(self, file_path: str, merge: bool = False) -> bool:
        """导入配置

        Args:
            file_path: 导入文件路径
            merge: 是否合并（True）或替换（False）

        Returns:
            bool: 是否成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            if merge:
                # 合并导入
                if 'user_config' in data:
                    await self.apply_config_changes(data['user_config'])
                if 'profiles' in data:
                    for name, profile_data in data['profiles'].items():
                        profile = ConfigurationProfile.from_dict(profile_data)
                        await self.create_profile(profile)
            else:
                # 替换导入
                if 'global_config' in data:
                    self.global_config = PerformanceConfig.from_dict(data['global_config'])
                    self._save_config_file(self.global_config_file, self.global_config)

                if 'user_config' in data:
                    self.user_config = PerformanceConfig.from_dict(data['user_config'])
                    self._save_config_file(self.user_config_file, self.user_config)

                self._merge_configs()

            return True

        except Exception as e:
            print(f"Failed to import config: {e}")
            return False

    def add_change_listener(self, listener: callable) -> None:
        """添加配置变更监听器

        Args:
            listener: 监听器函数
        """
        self.change_listeners.append(listener)

    def remove_change_listener(self, listener: callable) -> None:
        """移除配置变更监听器

        Args:
            listener: 监听器函数
        """
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)

    def _notify_config_changed(self, old_config: PerformanceConfig, new_config: PerformanceConfig) -> None:
        """通知配置变更"""
        for listener in self.change_listeners:
            try:
                listener(old_config, new_config)
            except Exception as e:
                print(f"Config change listener error: {e}")

    def _record_config_changes(self, old_config: PerformanceConfig, new_config: PerformanceConfig, scope: str) -> None:
        """记录配置变更"""
        old_dict = old_config.to_dict()
        new_dict = new_config.to_dict()

        # 查找变更的字段
        for key, new_value in new_dict.items():
            old_value = old_dict.get(key)
            if old_value != new_value:
                change = ConfigurationChange(
                    change_id=f"change-{int(datetime.now().timestamp() * 1000)}",
                    profile_name=scope,
                    field_path=key,
                    old_value=old_value,
                    new_value=new_value,
                    reason=f"Manual configuration update in {scope}"
                )
                self.change_history.append(change)

        # 限制历史记录大小
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]

    def _load_profiles(self) -> None:
        """加载配置档案"""
        for profile_file in self.profiles_dir.glob("*.yaml"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if data:
                    profile = ConfigurationProfile.from_dict(data)
                    self.profiles[profile.profile_name] = profile
            except Exception as e:
                print(f"Failed to load profile {profile_file}: {e}")

    def _save_profile_file(self, file_path: Path, profile: ConfigurationProfile) -> bool:
        """保存配置档案文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(profile.to_dict(), f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"Failed to save profile {file_path}: {e}")
            return False

    async def get_current_config(self) -> PerformanceConfig:
        """获取当前有效配置

        Returns:
            PerformanceConfig: 当前配置
        """
        return self.current_config

    async def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要

        Returns:
            Dict[str, Any]: 配置摘要
        """
        return {
            "config_sources": {
                "global": self.global_config_file.exists(),
                "user": self.user_config_file.exists(),
                "session": self.session_config_file.exists()
            },
            "current_config": {
                "max_instances": self.current_config.max_concurrent_instances,
                "auto_scaling": self.current_config.auto_scaling_enabled,
                "cache_enabled": self.current_config.cache_enabled,
                "monitoring_enabled": self.current_config.monitoring_enabled,
                "benchmark_enabled": self.current_config.benchmark_enabled
            },
            "profiles_count": len(self.profiles),
            "recent_changes": len([c for c in self.change_history
                                 if (datetime.now() - c.changed_at).total_seconds() < 86400])
        }