"""
配置管理器 - Window 8
管理通知系统的所有配置
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import os


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/window8.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config = {}
        self.last_modified = None
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if self.config_path.exists():
                # 检查文件是否有更新
                current_modified = self.config_path.stat().st_mtime
                if self.last_modified != current_modified:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                    self.last_modified = current_modified
                    self.logger.info(f"配置文件已加载: {self.config_path}")
            else:
                # 创建默认配置
                self._config = self._create_default_config()
                self.save_config()
                self.logger.info(f"已创建默认配置: {self.config_path}")
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self._config = self._create_default_config()
            return self._config
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            self.last_modified = self.config_path.stat().st_mtime
            self.logger.info(f"配置已保存: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        # 检查文件是否有更新
        if self.config_path.exists():
            current_modified = self.config_path.stat().st_mtime
            if self.last_modified != current_modified:
                self.load_config()
        
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            updates: 更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            self._deep_update(self._config, updates)
            return self.save_config()
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def get_channel_config(self, channel: str) -> Dict[str, Any]:
        """
        获取指定渠道的配置
        
        Args:
            channel: 渠道名称
            
        Returns:
            渠道配置
        """
        return self._config.get("channels", {}).get(channel, {})
    
    def is_channel_enabled(self, channel: str) -> bool:
        """
        检查渠道是否启用
        
        Args:
            channel: 渠道名称
            
        Returns:
            是否启用
        """
        channel_config = self.get_channel_config(channel)
        return channel_config.get("enabled", False)
    
    def set_channel_enabled(self, channel: str, enabled: bool) -> bool:
        """
        设置渠道启用状态
        
        Args:
            channel: 渠道名称
            enabled: 是否启用
            
        Returns:
            是否设置成功
        """
        if "channels" not in self._config:
            self._config["channels"] = {}
        if channel not in self._config["channels"]:
            self._config["channels"][channel] = {}
        
        self._config["channels"][channel]["enabled"] = enabled
        return self.save_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置完整性
        
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 检查必需的配置项
        required_sections = ["channels"]
        for section in required_sections:
            if section not in self._config:
                errors.append(f"缺少必需的配置节: {section}")
        
        # 检查渠道配置
        if "channels" in self._config:
            channels = self._config["channels"]
            
            # Telegram配置检查
            if channels.get("telegram", {}).get("enabled"):
                telegram = channels["telegram"]
                if not telegram.get("bot_token") or telegram["bot_token"] == "YOUR_BOT_TOKEN":
                    errors.append("Telegram bot_token 未配置")
                if not telegram.get("chat_id") or telegram["chat_id"] == "YOUR_CHAT_ID":
                    errors.append("Telegram chat_id 未配置")
            
            # 邮件配置检查
            if channels.get("email", {}).get("enabled"):
                email = channels["email"]
                required_email_fields = ["smtp_server", "port", "username", "password", "default_to"]
                for field in required_email_fields:
                    if not email.get(field):
                        errors.append(f"邮件配置缺少字段: {field}")
            
            # 如果所有渠道都未启用
            if not any(ch.get("enabled", False) for ch in channels.values()):
                warnings.append("没有启用任何通知渠道")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_to_default(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            是否重置成功
        """
        try:
            self._config = self._create_default_config()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
    
    def backup_config(self, backup_path: Optional[str] = None) -> str:
        """
        备份当前配置
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            备份文件路径
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.config_path.parent / f"window8_backup_{timestamp}.json")
        
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已备份到: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份配置失败: {e}")
            raise
    
    def restore_config(self, backup_path: str) -> bool:
        """
        从备份恢复配置
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            
            success = self.save_config()
            if success:
                self.logger.info(f"配置已从备份恢复: {backup_path}")
            return success
            
        except Exception as e:
            self.logger.error(f"恢复配置失败: {e}")
            return False
    
    def get_env_config(self) -> Dict[str, Any]:
        """
        从环境变量获取配置覆盖
        
        Returns:
            环境变量配置
        """
        env_config = {}
        
        # Telegram配置
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            env_config["channels"] = env_config.get("channels", {})
            env_config["channels"]["telegram"] = {
                "enabled": True,
                "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
                "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
            }
        
        # 邮件配置
        if os.getenv("EMAIL_SMTP_SERVER"):
            env_config["channels"] = env_config.get("channels", {})
            env_config["channels"]["email"] = {
                "enabled": True,
                "smtp_server": os.getenv("EMAIL_SMTP_SERVER"),
                "port": int(os.getenv("EMAIL_PORT", "587")),
                "username": os.getenv("EMAIL_USERNAME"),
                "password": os.getenv("EMAIL_PASSWORD"),
                "use_tls": os.getenv("EMAIL_USE_TLS", "true").lower() == "true",
                "default_to": os.getenv("EMAIL_DEFAULT_TO", "")
            }
        
        return env_config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "version": "8.1",
            "created_at": datetime.now().isoformat(),
            "channels": {
                "telegram": {
                    "enabled": False,
                    "bot_token": "YOUR_BOT_TOKEN",
                    "chat_id": "YOUR_CHAT_ID",
                    "timeout": 30,
                    "retry_count": 3
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "port": 587,
                    "username": "your_email@gmail.com",
                    "password": "your_password",
                    "use_tls": True,
                    "default_to": "recipient@gmail.com",
                    "timeout": 30
                },
                "terminal": {
                    "enabled": True,
                    "colored_output": True,
                    "width": None
                }
            },
            "reports": {
                "output_dir": "./reports",
                "cleanup_days": 7,
                "pdf_options": {
                    "page-size": "A4",
                    "margin-top": "0.75in",
                    "margin-right": "0.75in",
                    "margin-bottom": "0.75in",
                    "margin-left": "0.75in"
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8008,
                "cors_origins": ["*"],
                "log_level": "info"
            },
            "performance": {
                "max_concurrent_requests": 100,
                "request_timeout": 60,
                "batch_size_limit": 50
            }
        }
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def export_config(self, export_path: str = None) -> str:
        """
        导出配置为可共享格式（移除敏感信息）
        
        Args:
            export_path: 导出文件路径
            
        Returns:
            导出文件路径
        """
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = str(self.config_path.parent / f"window8_export_{timestamp}.json")
        
        # 创建配置副本并移除敏感信息
        export_config = self.get_config()
        
        # 移除敏感信息
        if "channels" in export_config:
            channels = export_config["channels"]
            
            if "telegram" in channels:
                channels["telegram"]["bot_token"] = "YOUR_BOT_TOKEN"
                channels["telegram"]["chat_id"] = "YOUR_CHAT_ID"
            
            if "email" in channels:
                channels["email"]["username"] = "your_email@gmail.com"
                channels["email"]["password"] = "your_password"
                channels["email"]["default_to"] = "recipient@gmail.com"
        
        # 添加导出信息
        export_config["export_info"] = {
            "exported_at": datetime.now().isoformat(),
            "note": "敏感信息已移除，需要重新配置"
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已导出到: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            raise