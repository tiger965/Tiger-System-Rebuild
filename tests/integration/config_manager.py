#!/usr/bin/env python3
"""
Tiger系统 - 配置管理中心
10号窗口 - 统一配置管理
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件定义
        self.config_files = {
            "system": "system.yaml",
            "database": "database.yaml",
            "api_keys": "api_keys.yaml",
            "trading": "trading.yaml",
            "risk": "risk.yaml",
            "notification": "notification.yaml"
        }
        
        # 环境定义
        self.environments = {
            "development": "开发环境",
            "testing": "测试环境",
            "staging": "预发布环境",
            "production": "生产环境"
        }
        
        # 当前环境
        self.current_env = os.getenv("TIGER_ENV", "development")
        
        # 配置缓存
        self.config_cache = {}
        
        # 加密管理器（用于敏感信息）
        self.cipher = self._init_cipher()
        
        logger.info(f"配置管理器初始化 - 环境: {self.current_env}")
        
    def _init_cipher(self) -> Optional[Fernet]:
        """初始化加密器"""
        key_file = self.config_dir / ".secret_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # 生成新密钥
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 只有所有者可读写
            
        return Fernet(key)
        
    def load_config(self, config_name: str, reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_name: 配置名称
            reload: 是否强制重新加载
            
        Returns:
            配置字典
        """
        if not reload and config_name in self.config_cache:
            return self.config_cache[config_name]
            
        if config_name not in self.config_files:
            raise ValueError(f"未知的配置: {config_name}")
            
        config_file = self.config_dir / self.config_files[config_name]
        
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_file}")
            # 创建默认配置
            default_config = self._get_default_config(config_name)
            self.save_config(config_name, default_config)
            return default_config
            
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            
        # 解密敏感信息
        if config_name == "api_keys":
            config = self._decrypt_config(config)
            
        self.config_cache[config_name] = config
        return config
        
    def save_config(self, config_name: str, config: Dict[str, Any]):
        """
        保存配置文件
        
        Args:
            config_name: 配置名称
            config: 配置内容
        """
        if config_name not in self.config_files:
            raise ValueError(f"未知的配置: {config_name}")
            
        # 加密敏感信息
        if config_name == "api_keys":
            config = self._encrypt_config(config)
            
        config_file = self.config_dir / self.config_files[config_name]
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
        # 更新缓存
        self.config_cache[config_name] = config
        logger.info(f"配置已保存: {config_name}")
        
    def _encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """加密配置中的敏感信息"""
        encrypted = {}
        for key, value in config.items():
            if isinstance(value, str) and value:
                # 加密字符串值
                encrypted[key] = self.cipher.encrypt(value.encode()).decode()
            else:
                encrypted[key] = value
        return encrypted
        
    def _decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解密配置中的敏感信息"""
        decrypted = {}
        for key, value in config.items():
            if isinstance(value, str) and value:
                try:
                    # 尝试解密
                    decrypted[key] = self.cipher.decrypt(value.encode()).decode()
                except:
                    # 如果解密失败，可能是明文
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted
        
    def _get_default_config(self, config_name: str) -> Dict[str, Any]:
        """获取默认配置"""
        defaults = {
            "system": {
                "name": "Tiger智能交易分析系统",
                "version": "1.0.0",
                "environment": self.current_env,
                "debug": self.current_env == "development",
                "log_level": "INFO",
                "timezone": "Asia/Shanghai",
                "created_at": datetime.now().isoformat()
            },
            "database": {
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "tiger_system",
                "username": "tiger",
                "password": "",
                "pool_size": 10,
                "max_overflow": 20,
                "echo": False
            },
            "api_keys": {
                "binance_api_key": "",
                "binance_secret": "",
                "claude_api_key": "",
                "telegram_bot_token": "",
                "twitter_api_key": "",
                "coingecko_api_key": ""
            },
            "trading": {
                "symbols": ["BTC/USDT", "ETH/USDT"],
                "intervals": ["1m", "5m", "15m", "1h", "4h", "1d"],
                "max_position_size": 10000,
                "risk_per_trade": 0.02,
                "stop_loss": 0.05,
                "take_profit": 0.10,
                "trailing_stop": 0.03
            },
            "risk": {
                "max_drawdown": 0.20,
                "max_daily_loss": 0.05,
                "max_open_positions": 5,
                "risk_score_threshold": 70,
                "emergency_stop": True,
                "alert_levels": ["info", "warning", "critical", "emergency"]
            },
            "notification": {
                "enabled": True,
                "channels": ["telegram", "email", "webhook"],
                "telegram_chat_id": "",
                "email_recipients": [],
                "webhook_url": "",
                "alert_throttle": 60,
                "batch_notifications": True
            }
        }
        
        return defaults.get(config_name, {})
        
    def validate_config(self) -> Dict[str, Any]:
        """验证所有配置的完整性"""
        logger.info("开始验证配置...")
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checked_at": datetime.now().isoformat()
        }
        
        # 检查必需的配置文件
        for name in self.config_files:
            try:
                config = self.load_config(name)
                
                # 特定配置验证
                if name == "database":
                    if not config.get("host") or not config.get("database"):
                        validation_results["errors"].append(f"数据库配置不完整")
                        validation_results["valid"] = False
                        
                elif name == "api_keys":
                    # 检查关键API密钥
                    if not config.get("claude_api_key"):
                        validation_results["warnings"].append("Claude API密钥未配置")
                    if not config.get("binance_api_key"):
                        validation_results["warnings"].append("Binance API密钥未配置")
                        
                elif name == "risk":
                    if config.get("max_drawdown", 1) > 0.5:
                        validation_results["warnings"].append("最大回撤设置过高")
                        
            except Exception as e:
                validation_results["errors"].append(f"加载配置 {name} 失败: {e}")
                validation_results["valid"] = False
                
        # 输出验证结果
        if validation_results["valid"]:
            logger.info("  ✅ 配置验证通过")
        else:
            logger.error(f"  ❌ 配置验证失败")
            for error in validation_results["errors"]:
                logger.error(f"    - {error}")
                
        if validation_results["warnings"]:
            logger.warning("  ⚠️ 配置警告:")
            for warning in validation_results["warnings"]:
                logger.warning(f"    - {warning}")
                
        return validation_results
        
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        all_configs = {}
        for name in self.config_files:
            try:
                all_configs[name] = self.load_config(name)
            except Exception as e:
                logger.error(f"加载配置 {name} 失败: {e}")
                all_configs[name] = {}
        return all_configs
        
    def export_configs(self, export_file: str = "configs_export.json"):
        """导出所有配置（用于备份）"""
        all_configs = self.get_all_configs()
        
        # 添加元数据
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "environment": self.current_env,
                "version": "1.0.0"
            },
            "configs": all_configs
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"配置已导出到: {export_file}")
        
    def import_configs(self, import_file: str):
        """导入配置（用于恢复）"""
        with open(import_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
            
        configs = import_data.get("configs", {})
        
        for name, config in configs.items():
            if name in self.config_files:
                self.save_config(name, config)
                
        logger.info(f"配置已从 {import_file} 导入")


def create_initial_configs():
    """创建初始配置文件"""
    manager = ConfigManager()
    
    # 验证配置
    results = manager.validate_config()
    
    if results["valid"]:
        print("✅ 配置管理中心初始化成功")
    else:
        print("❌ 配置存在问题，请检查")
        
    return manager


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建初始配置
    manager = create_initial_configs()
    
    # 导出配置备份
    manager.export_configs("configs_backup.json")