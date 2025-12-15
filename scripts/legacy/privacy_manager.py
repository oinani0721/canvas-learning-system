"""
隐私管理器

本模块实现隐私和安全保护功能，包括：
- 数据加密和匿名化
- 用户权限控制
- 数据导出和删除功能
- 隐私级别管理

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-25
"""

import json
import os
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# 尝试导入loguru用于企业级日志记录
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class PrivacySettings:
    """隐私设置数据模型"""
    user_id: str = ""
    data_classification: str = "personal_learning_data"
    encryption_status: str = "end_to_end_encrypted"
    access_permissions: Dict = field(default_factory=dict)
    retention_policy: Dict = field(default_factory=dict)
    user_controls: Dict = field(default_factory=dict)
    privacy_level: str = "standard"  # standard, enhanced, maximum
    consent_timestamp: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AccessLog:
    """访问日志数据模型"""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    access_type: str = ""  # read, write, delete, export
    resource_type: str = ""  # activities, patterns, insights
    resource_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    access_granted: bool = False
    ip_address: str = ""
    user_agent: str = ""
    purpose: str = ""


class PrivacyManager:
    """隐私管理器"""

    def __init__(self, config_path: str = "config/realtime_memory.yaml"):
        """初始化隐私管理器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path("data/realtime_memory/privacy_controls")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 加密密钥管理
        self.encryption_keys = self._load_or_generate_keys()

        # 隐私设置存储
        self.privacy_settings: Dict[str, PrivacySettings] = {}

        # 访问日志
        self.access_logs: List[AccessLog] = []

        # 匿名化映射表
        self.anonymization_mappings: Dict[str, str] = {}

        logger.info("PrivacyManager initialized")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'privacy_security': {
                'data_encryption': 'AES-256',
                'anonymization': {
                    'enabled': True,
                    'anonymize_identifiers': True,
                    'retain_patterns_only': True
                },
                'access_control': {
                    'user_access_only': True,
                    'system_access_logging': True,
                    'external_api_access': False
                },
                'retention_policy': {
                    'detailed_activities_days': 365,
                    'summarized_insights_years': 7,
                    'anonymized_patterns_years': 'indefinite'
                },
                'user_controls': {
                    'data_export': True,
                    'selective_deletion': True,
                    'privacy_levels': ['standard', 'enhanced', 'maximum'],
                    'consent_required': True
                }
            }
        }

    def _load_or_generate_keys(self) -> Dict[str, bytes]:
        """加载或生成加密密钥"""
        keys_file = self.data_dir / "encryption_keys.json"

        if keys_file.exists():
            try:
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys_data = json.load(f)
                    # 解码base64密钥
                    return {
                        'master_key': base64.b64decode(keys_data['master_key']),
                        'data_key': base64.b64decode(keys_data['data_key'])
                    }
            except Exception as e:
                logger.error(f"加载加密密钥失败: {e}，生成新密钥")

        # 生成新密钥
        master_key = Fernet.generate_key()
        data_key = Fernet.generate_key()

        # 保存密钥
        keys_data = {
            'master_key': base64.b64encode(master_key).decode(),
            'data_key': base64.b64encode(data_key).decode(),
            'created_at': datetime.now().isoformat()
        }

        try:
            with open(keys_file, 'w', encoding='utf-8') as f:
                json.dump(keys_data, f, indent=2)

            # 设置文件权限（仅所有者可读写）
            os.chmod(keys_file, 0o600)

        except Exception as e:
            logger.error(f"保存加密密钥失败: {e}")

        return {
            'master_key': master_key,
            'data_key': data_key
        }

    def encrypt_data(self, data: str, key_type: str = "data") -> str:
        """加密数据

        Args:
            data: 要加密的数据
            key_type: 密钥类型 (master/data)

        Returns:
            str: 加密后的数据（base64编码）
        """
        try:
            key = self.encryption_keys.get(f"{key_type}_key")
            if not key:
                raise ValueError(f"未找到{key_type}密钥")

            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, key_type: str = "data") -> str:
        """解密数据

        Args:
            encrypted_data: 加密的数据（base64编码）
            key_type: 密钥类型 (master/data)

        Returns:
            str: 解密后的数据
        """
        try:
            key = self.encryption_keys.get(f"{key_type}_key")
            if not key:
                raise ValueError(f"未找到{key_type}密钥")

            fernet = Fernet(key)
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')

        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            raise

    def anonymize_data(self, data: Dict, user_id: str) -> Dict:
        """匿名化数据

        Args:
            data: 要匿名化的数据
            user_id: 用户ID

        Returns:
            Dict: 匿名化后的数据
        """
        if not self.config.get('privacy_security', {}).get('anonymization', {}).get('enabled', True):
            return data

        anonymized = data.copy()

        # 获取或创建用户匿名ID
        anonymous_id = self._get_or_create_anonymous_id(user_id)

        # 匿名化用户ID
        if 'user_id' in anonymized:
            anonymized['user_id'] = anonymous_id

        # 匿名化敏感标识符
        sensitive_fields = ['canvas_path', 'session_id', 'activity_id', 'node_id']
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._anonymize_identifier(str(anonymized[field]))

        # 匿名化文本内容（保留模式）
        if 'input_text' in anonymized:
            anonymized['input_text'] = self._anonymize_text_content(anonymized['input_text'])

        # 移除直接标识符（如果配置要求）
        if self.config.get('privacy_security', {}).get('anonymization', {}).get('retain_patterns_only', False):
            anonymized = self._retain_patterns_only(anonymized)

        return anonymized

    def _get_or_create_anonymous_id(self, user_id: str) -> str:
        """获取或创建匿名ID"""
        if user_id in self.anonymization_mappings:
            return self.anonymization_mappings[user_id]

        # 创建新的匿名ID
        anonymous_id = f"user_{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"
        self.anonymization_mappings[user_id] = anonymous_id

        # 保存映射关系
        self._save_anonymization_mappings()

        return anonymous_id

    def _anonymize_identifier(self, identifier: str) -> str:
        """匿名化标识符"""
        # 使用HMAC生成一致的匿名标识符
        hmac_obj = hmac.new(
            self.encryption_keys['master_key'],
            identifier.encode(),
            hashlib.sha256
        )
        return f"anon_{hmac_obj.hexdigest()[:12]}"

    def _anonymize_text_content(self, text: str) -> str:
        """匿名化文本内容"""
        # 简化实现：移除可能的个人信息
        import re

        # 移除邮箱
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

        # 移除电话号码
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)

        # 移除常见姓名模式（简化）
        text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)

        # 保留长度信息但模糊化具体内容
        if len(text) > 50:
            return text[:20] + "..." + text[-10:] + f" (长度: {len(text)})"
        else:
            return f"[文本内容，长度: {len(text)}]"

    def _retain_patterns_only(self, data: Dict) -> Dict:
        """仅保留模式信息"""
        # 定义要保留的字段（仅包含模式信息）
        pattern_fields = {
            'activity_type', 'timestamp', 'learning_patterns',
            'behavior_patterns', 'progress_indicators', 'error_patterns'
        }

        return {k: v for k, v in data.items() if k in pattern_fields}

    def check_access_permission(self, user_id: str, resource_type: str,
                              action: str, resource_id: str = "") -> bool:
        """检查访问权限

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            action: 操作类型 (read, write, delete, export)
            resource_id: 资源ID

        Returns:
            bool: 是否有权限
        """
        # 记录访问尝试
        access_log = AccessLog(
            user_id=user_id,
            access_type=action,
            resource_type=resource_type,
            resource_id=resource_id
        )

        # 获取用户隐私设置
        privacy_settings = self._get_user_privacy_settings(user_id)

        # 检查基本权限
        if not privacy_settings:
            logger.warning(f"用户 {user_id} 没有隐私设置，拒绝访问")
            access_log.access_granted = False
            self._log_access(access_log)
            return False

        # 检查用户访问权限
        access_permissions = privacy_settings.access_permissions
        user_access = access_permissions.get('user_access', 'full')

        if user_access != 'full':
            # 限制性访问控制
            if action in ['write', 'delete']:
                access_log.access_granted = False
                self._log_access(access_log)
                return False

        # 检查数据导出权限
        if action == 'export':
            export_allowed = privacy_settings.user_controls.get('data_export', False)
            if not export_allowed:
                access_log.access_granted = False
                self._log_access(access_log)
                return False

        # 检查选择性删除权限
        if action == 'delete' and resource_id:
            selective_deletion = privacy_settings.user_controls.get('selective_deletion', False)
            if not selective_deletion:
                access_log.access_granted = False
                self._log_access(access_log)
                return False

        # 记录成功的访问
        access_log.access_granted = True
        self._log_access(access_log)

        return True

    def _log_access(self, access_log: AccessLog):
        """记录访问日志"""
        self.access_logs.append(access_log)

        # 保存到文件
        self._save_access_logs()

        # 清理旧日志（保留最近1000条）
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-1000:]

    def manage_privacy_settings(self, user_id: str, settings: Dict) -> bool:
        """管理隐私设置

        Args:
            user_id: 用户ID
            settings: 隐私设置

        Returns:
            bool: 是否成功设置
        """
        try:
            # 验证设置
            validated_settings = self._validate_privacy_settings(settings)

            # 获取现有设置或创建新设置
            if user_id in self.privacy_settings:
                privacy_settings = self.privacy_settings[user_id]
                privacy_settings.__dict__.update(validated_settings)
            else:
                privacy_settings = PrivacySettings(user_id=user_id, **validated_settings)
                self.privacy_settings[user_id] = privacy_settings

            # 更新时间戳
            privacy_settings.last_updated = datetime.now()

            # 保存设置
            self._save_privacy_settings()

            logger.info(f"用户 {user_id} 的隐私设置已更新")
            return True

        except Exception as e:
            logger.error(f"更新隐私设置失败: {user_id}, 错误: {e}")
            return False

    def _validate_privacy_settings(self, settings: Dict) -> Dict:
        """验证隐私设置"""
        validated = {}

        # 验证隐私级别
        valid_levels = ['standard', 'enhanced', 'maximum']
        privacy_level = settings.get('privacy_level', 'standard')
        if privacy_level in valid_levels:
            validated['privacy_level'] = privacy_level
        else:
            validated['privacy_level'] = 'standard'

        # 验证访问权限
        access_permissions = settings.get('access_permissions', {})
        validated['access_permissions'] = {
            'user_access': access_permissions.get('user_access', 'full'),
            'system_access': access_permissions.get('system_access', 'analysis_only'),
            'external_sharing': access_permissions.get('external_sharing', 'disabled')
        }

        # 验证保留策略
        retention_policy = settings.get('retention_policy', {})
        config_retention = self.config.get('privacy_security', {}).get('retention_policy', {})

        # 处理保留策略，确保类型一致性
        detailed_activities = retention_policy.get('detailed_activities', config_retention.get('detailed_activities_days', 365))
        if isinstance(detailed_activities, str) and detailed_activities.endswith('_days'):
            detailed_activities = int(detailed_activities[:-5])
        elif not isinstance(detailed_activities, int):
            detailed_activities = 365  # 默认值

        summarized_insights = retention_policy.get('summarized_insights', config_retention.get('summarized_insights_years', 7))
        if isinstance(summarized_insights, str) and summarized_insights.endswith('_years'):
            summarized_insights = int(summarized_insights[:-6])
        elif not isinstance(summarized_insights, int):
            summarized_insights = 7  # 默认值

        anonymized_patterns = retention_policy.get('anonymized_patterns', config_retention.get('anonymized_patterns_years', 'indefinite'))
        if isinstance(anonymized_patterns, str) and anonymized_patterns.endswith('_years'):
            anonymized_patterns = int(anonymized_patterns[:-6])
        elif anonymized_patterns != 'indefinite' and not isinstance(anonymized_patterns, int):
            anonymized_patterns = 'indefinite'  # 默认值

        validated['retention_policy'] = {
            'detailed_activities': detailed_activities,
            'summarized_insights': summarized_insights,
            'anonymized_patterns': anonymized_patterns
        }

        # 验证用户控制
        user_controls = settings.get('user_controls', {})
        validated['user_controls'] = {
            'data_export': user_controls.get('data_export', True),
            'selective_deletion': user_controls.get('selective_deletion', True),
            'memory_opt_out': user_controls.get('memory_opt_out', False)  # 核心功能不可退出
        }

        # 设置默认值
        validated.setdefault('data_classification', 'personal_learning_data')
        validated.setdefault('encryption_status', 'end_to_end_encrypted')

        return validated

    def _get_user_privacy_settings(self, user_id: str) -> Optional[PrivacySettings]:
        """获取用户隐私设置"""
        if user_id not in self.privacy_settings:
            # 创建默认设置
            default_settings = {
                'user_id': user_id,
                'privacy_level': 'standard'
            }
            self.manage_privacy_settings(user_id, default_settings)

        return self.privacy_settings.get(user_id)

    def export_user_data(self, user_id: str, export_format: str = "json") -> str:
        """导出用户数据

        Args:
            user_id: 用户ID
            export_format: 导出格式

        Returns:
            str: 导出文件路径
        """
        # 检查导出权限
        if not self.check_access_permission(user_id, "user_data", "export"):
            raise PermissionError("用户没有数据导出权限")

        try:
            # 收集用户数据
            user_data = self._collect_user_data(user_id)

            # 应用隐私设置
            privacy_settings = self._get_user_privacy_settings(user_id)
            if privacy_settings.privacy_level in ['enhanced', 'maximum']:
                user_data = self.anonymize_data(user_data, user_id)

            # 生成导出文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_data_export_{timestamp}.{export_format}"
            filepath = self.data_dir / filename

            if export_format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=2, default=str)
            elif export_format == "csv":
                self._export_to_csv(user_data, filepath)

            # 记录导出操作
            self.check_access_permission(user_id, "user_data", "export", str(filepath))

            logger.info(f"用户数据已导出: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"导出用户数据失败: {user_id}, 错误: {e}")
            raise

    def delete_user_data(self, user_id: str, data_type: str = "all",
                        specific_ids: List[str] = None) -> bool:
        """删除用户数据

        Args:
            user_id: 用户ID
            data_type: 数据类型 (all, activities, patterns, insights)
            specific_ids: 特定数据ID列表

        Returns:
            bool: 是否成功删除
        """
        # 检查删除权限
        if specific_ids:
            if not self.check_access_permission(user_id, data_type, "delete", ",".join(specific_ids)):
                raise PermissionError("用户没有选择性删除权限")
        else:
            if not self.check_access_permission(user_id, data_type, "delete"):
                raise PermissionError("用户没有数据删除权限")

        try:
            deleted_count = 0

            if data_type in ["all", "activities"] and not specific_ids:
                # 删除活动数据
                activities_file = self.data_dir.parent / "learning_activities" / f"{user_id}_activities.json"
                if activities_file.exists():
                    activities_file.unlink()
                    deleted_count += 1

            if data_type in ["all", "patterns"] and not specific_ids:
                # 删除模式数据
                pattern_files = list((self.data_dir.parent / "pattern_analysis").glob(f"{user_id}_pattern_*.json"))
                for file_path in pattern_files:
                    file_path.unlink()
                    deleted_count += 1

            if data_type in ["all", "insights"] and not specific_ids:
                # 删除洞察数据
                insight_files = list(self.data_dir.glob(f"{user_id}_insights_*.json"))
                for file_path in insight_files:
                    file_path.unlink()
                    deleted_count += 1

            # 删除匿名化映射
            if user_id in self.anonymization_mappings:
                del self.anonymization_mappings[user_id]
                self._save_anonymization_mappings()

            logger.info(f"用户数据删除完成: {user_id}, 删除了 {deleted_count} 个文件")
            return True

        except Exception as e:
            logger.error(f"删除用户数据失败: {user_id}, 错误: {e}")
            return False

    def _collect_user_data(self, user_id: str) -> Dict:
        """收集用户数据"""
        user_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "privacy_settings": {},
            "activities": [],
            "patterns": [],
            "insights": [],
            "access_logs": []
        }

        # 收集隐私设置
        if user_id in self.privacy_settings:
            settings = self.privacy_settings[user_id]
            user_data["privacy_settings"] = {
                "privacy_level": settings.privacy_level,
                "retention_policy": settings.retention_policy,
                "user_controls": settings.user_controls,
                "last_updated": settings.last_updated.isoformat()
            }

        # 收集活动数据
        activities_file = self.data_dir.parent / "learning_activities" / f"{user_id}_activities.json"
        if activities_file.exists():
            with open(activities_file, 'r', encoding='utf-8') as f:
                user_data["activities"] = json.load(f)

        # 收集模式数据
        pattern_files = list((self.data_dir.parent / "pattern_analysis").glob(f"{user_id}_pattern_*.json"))
        for pattern_file in pattern_files:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                user_data["patterns"].append(json.load(f))

        # 收集洞察数据
        insight_files = list(self.data_dir.glob(f"{user_id}_insights_*.json"))
        for insight_file in insight_files:
            with open(insight_file, 'r', encoding='utf-8') as f:
                user_data["insights"].append(json.load(f))

        # 收集访问日志（仅用户的）
        user_logs = [log for log in self.access_logs if log.user_id == user_id]
        user_data["access_logs"] = [
            {
                "access_type": log.access_type,
                "resource_type": log.resource_type,
                "timestamp": log.timestamp.isoformat(),
                "access_granted": log.access_granted,
                "purpose": log.purpose
            }
            for log in user_logs[-100:]  # 最近100条
        ]

        return user_data

    def _export_to_csv(self, data: Dict, filepath: Path):
        """导出为CSV格式"""
        import csv

        # 简化实现：导出活动数据为CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if 'activities' in data and data['activities']:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    'activity_id', 'timestamp', 'activity_type', 'user_id', 'canvas_path'
                ])
                writer.writeheader()

                for activity in data['activities']:
                    writer.writerow({
                        'activity_id': activity.get('activity_id', ''),
                        'timestamp': activity.get('timestamp', ''),
                        'activity_type': activity.get('activity_type', ''),
                        'user_id': activity.get('user_id', ''),
                        'canvas_path': activity.get('canvas_path', '')
                    })

    def _save_privacy_settings(self):
        """保存隐私设置"""
        try:
            settings_file = self.data_dir / "privacy_settings.json"

            settings_data = {}
            for user_id, settings in self.privacy_settings.items():
                settings_data[user_id] = {
                    "user_id": settings.user_id,
                    "data_classification": settings.data_classification,
                    "encryption_status": settings.encryption_status,
                    "access_permissions": settings.access_permissions,
                    "retention_policy": settings.retention_policy,
                    "user_controls": settings.user_controls,
                    "privacy_level": settings.privacy_level,
                    "consent_timestamp": settings.consent_timestamp.isoformat(),
                    "last_updated": settings.last_updated.isoformat()
                }

            # 加密保存敏感设置
            encrypted_data = self.encrypt_data(json.dumps(settings_data), "master")

            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)

            # 设置文件权限
            os.chmod(settings_file, 0o600)

        except Exception as e:
            logger.error(f"保存隐私设置失败: {e}")

    def _load_privacy_settings(self):
        """加载隐私设置"""
        try:
            settings_file = self.data_dir / "privacy_settings.json"

            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()

                decrypted_data = self.decrypt_data(encrypted_data, "master")
                settings_data = json.loads(decrypted_data)

                for user_id, settings_dict in settings_data.items():
                    privacy_settings = PrivacySettings(
                        user_id=settings_dict["user_id"],
                        data_classification=settings_dict["data_classification"],
                        encryption_status=settings_dict["encryption_status"],
                        access_permissions=settings_dict["access_permissions"],
                        retention_policy=settings_dict["retention_policy"],
                        user_controls=settings_dict["user_controls"],
                        privacy_level=settings_dict["privacy_level"],
                        consent_timestamp=datetime.fromisoformat(settings_dict["consent_timestamp"]),
                        last_updated=datetime.fromisoformat(settings_dict["last_updated"])
                    )
                    self.privacy_settings[user_id] = privacy_settings

        except Exception as e:
            logger.error(f"加载隐私设置失败: {e}")

    def _save_access_logs(self):
        """保存访问日志"""
        try:
            logs_file = self.data_dir / "access_logs.json"

            logs_data = [
                {
                    "log_id": log.log_id,
                    "user_id": log.user_id,
                    "access_type": log.access_type,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "timestamp": log.timestamp.isoformat(),
                    "access_granted": log.access_granted,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "purpose": log.purpose
                }
                for log in self.access_logs[-500:]  # 保存最近500条
            ]

            with open(logs_file, 'w', encoding='utf-8') as f:
                json.dump(logs_data, f, indent=2)

        except Exception as e:
            logger.error(f"保存访问日志失败: {e}")

    def _save_anonymization_mappings(self):
        """保存匿名化映射"""
        try:
            mappings_file = self.data_dir / "anonymization_mappings.json"

            with open(mappings_file, 'w', encoding='utf-8') as f:
                json.dump(self.anonymization_mappings, f, indent=2)

        except Exception as e:
            logger.error(f"保存匿名化映射失败: {e}")

    def get_privacy_dashboard(self, user_id: str) -> Dict:
        """获取隐私仪表板数据

        Args:
            user_id: 用户ID

        Returns:
            Dict: 隐私仪表板数据
        """
        privacy_settings = self._get_user_privacy_settings(user_id)

        # 统计数据
        user_logs = [log for log in self.access_logs if log.user_id == user_id]
        recent_logs = [log for log in user_logs if log.timestamp > datetime.now() - timedelta(days=30)]

        dashboard = {
            "privacy_level": privacy_settings.privacy_level,
            "data_classification": privacy_settings.data_classification,
            "encryption_status": privacy_settings.encryption_status,
            "user_controls": privacy_settings.user_controls,
            "retention_policy": privacy_settings.retention_policy,
            "last_updated": privacy_settings.last_updated.isoformat(),
            "access_statistics": {
                "total_access_requests": len(user_logs),
                "recent_access_requests": len(recent_logs),
                "successful_accesses": len([log for log in recent_logs if log.access_granted]),
                "denied_accesses": len([log for log in recent_logs if not log.access_granted])
            },
            "data_export_status": "enabled" if privacy_settings.user_controls.get('data_export', False) else "disabled",
            "selective_deletion_status": "enabled" if privacy_settings.user_controls.get('selective_deletion', False) else "disabled"
        }

        return dashboard

    def cleanup_expired_data(self):
        """清理过期数据"""
        try:
            cleaned_count = 0

            # 清理访问日志（保留1年）
            cutoff_date = datetime.now() - timedelta(days=365)
            original_count = len(self.access_logs)
            self.access_logs = [log for log in self.access_logs if log.timestamp > cutoff_date]
            cleaned_count += original_count - len(self.access_logs)

            # 清理匿名化映射（非活跃用户）
            inactive_users = []
            for user_id in self.anonymization_mappings.keys():
                user_logs = [log for log in self.access_logs if log.user_id == user_id]
                if not user_logs or max(log.timestamp for log in user_logs) < cutoff_date:
                    inactive_users.append(user_id)

            for user_id in inactive_users:
                del self.anonymization_mappings[user_id]
                cleaned_count += 1

            # 保存更新后的数据
            self._save_access_logs()
            self._save_anonymization_mappings()

            logger.info(f"数据清理完成，清理了 {cleaned_count} 条过期记录")

        except Exception as e:
            logger.error(f"数据清理失败: {e}")