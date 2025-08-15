# -*- coding: utf-8 -*-
"""
Window 3 - 数据采集工具配置文件
集成所有API密钥和配置信息
"""

# WhaleAlert API配置（已付费）
WHALE_ALERT_CONFIG = {
    "api_key": "pGV9OtVnzgp0bTbUgU4aaWhVMVYfqPLU",
    "base_url": "https://api.whale-alert.io/v1",
    "endpoints": {
        "transactions": "/transactions",
        "status": "/status"
    },
    "rate_limit": 100  # 每分钟100次请求
}

# CryptoPanic API配置（已付费）
CRYPTOPANIC_CONFIG = {
    "api_key": "your_cryptopanic_api_key_here",  # 需要获取
    "base_url": "https://cryptopanic.com/api/v1",
    "endpoints": {
        "posts": "/posts/",
        "currencies": "/currencies/"
    }
}

# ValueScan配置（用户账号密码）
VALUESCAN_CONFIG = {
    "base_url": "https://www.valuescan.io",
    "username": "3205381503@qq.com",
    "password": "Yzh198796&",
    "session_timeout": 3600,
    "crawl_intervals": {
        "risk_alerts": 120,      # 2分钟
        "opportunities": 180,    # 3分钟
        "tracking_list": 300,    # 5分钟
        "end_tracking": 180      # 3分钟
    }
}

# Twitter API配置（需要申请）
TWITTER_CONFIG = {
    "bearer_token": "your_twitter_bearer_token_here",  # 需要申请
    "api_key": "your_twitter_api_key_here",
    "api_secret": "your_twitter_api_secret_here",
    "access_token": "your_twitter_access_token_here",
    "access_token_secret": "your_twitter_access_token_secret_here",
    "rate_limits": {
        "search": 300,      # 每15分钟300次
        "user_tweets": 900  # 每15分钟900次
    }
}

# Etherscan API配置
ETHERSCAN_CONFIG = {
    "api_key": "your_etherscan_api_key_here",  # 免费申请
    "base_url": "https://api.etherscan.io/api",
    "rate_limit": 5  # 每秒5次请求
}

# BSCScan API配置
BSCSCAN_CONFIG = {
    "api_key": "your_bscscan_api_key_here",  # 免费申请
    "base_url": "https://api.bscscan.com/api",
    "rate_limit": 5  # 每秒5次请求
}

# 监控配置
MONITORING_CONFIG = {
    "price_thresholds": {
        1: 0.003,  # 0.3% - 一级触发
        2: 0.005,  # 0.5% - 二级触发
        3: 0.010   # 1.0% - 三级触发
    },
    "volume_thresholds": {
        1: 0.5,    # 50%
        2: 1.0,    # 100%
        3: 2.0     # 200%
    },
    "whale_thresholds": {
        1: 50000,      # 5万美元
        2: 100000,     # 10万美元
        3: 1000000     # 100万美元
    },
    "vip_accounts": [
        "@elonmusk",
        "@cz_binance", 
        "@VitalikButerin",
        "@saylor",
        "@DocumentingBTC"
    ],
    "intervals": {
        "price_monitor": 5,     # 5秒
        "volume_monitor": 60,   # 60秒
        "whale_monitor": 30,    # 30秒
        "vip_monitor": 10,      # 10秒
        "news_monitor": 60      # 60秒
    }
}

# Redis配置（用于消息队列）
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
    "socket_timeout": 5,
    "health_check_interval": 30
}

# Window间通信配置
WINDOW_ENDPOINTS = {
    6: {  # Window 6 - AI决策大脑
        "http": "http://localhost:8006/api/trigger",
        "redis_queue": "window6_triggers",
        "priority": "HIGH"
    },
    7: {  # Window 7 - 风控执行
        "http": "http://localhost:8007/api/trigger",
        "redis_queue": "window7_triggers", 
        "priority": "CRITICAL"
    },
    8: {  # Window 8 - 通知系统
        "http": "http://localhost:8008/api/trigger",
        "redis_queue": "window8_triggers",
        "priority": "MEDIUM"
    },
    9: {  # Window 9 - 学习系统
        "http": "http://localhost:8009/api/trigger",
        "redis_queue": "window9_triggers",
        "priority": "LOW"
    }
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "filename": "/tmp/window3.log",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        },
        "console": {
            "stream": "ext://sys.stdout"
        }
    }
}

# 数据存储配置
STORAGE_CONFIG = {
    "base_dir": "/tmp/window3_data",
    "backup_dir": "/tmp/window3_backups",
    "cache_ttl": 300,  # 5分钟
    "max_cache_size": 1000,
    "cleanup_interval": 3600  # 1小时清理一次
}

# 反检测配置
ANTI_DETECTION_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ],
    "request_delays": {
        "min": 1.0,
        "max": 3.0
    },
    "retry_config": {
        "max_retries": 3,
        "backoff_factor": 2.0
    }
}

# 主要交易对配置
TRADING_PAIRS = [
    "BTC/USDT",
    "ETH/USDT", 
    "BNB/USDT",
    "SOL/USDT",
    "ADA/USDT",
    "DOT/USDT",
    "MATIC/USDT",
    "AVAX/USDT",
    "LINK/USDT",
    "UNI/USDT"
]

# 获取完整配置的函数
def get_config():
    """获取完整配置字典"""
    return {
        "whale_alert": WHALE_ALERT_CONFIG,
        "cryptopanic": CRYPTOPANIC_CONFIG,
        "valuescan": VALUESCAN_CONFIG,
        "twitter": TWITTER_CONFIG,
        "etherscan": ETHERSCAN_CONFIG,
        "bscscan": BSCSCAN_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "redis": REDIS_CONFIG,
        "windows": WINDOW_ENDPOINTS,
        "logging": LOGGING_CONFIG,
        "storage": STORAGE_CONFIG,
        "anti_detection": ANTI_DETECTION_CONFIG,
        "trading_pairs": TRADING_PAIRS
    }

# 验证配置完整性
def validate_config():
    """验证配置完整性"""
    required_keys = [
        "whale_alert.api_key",
        "valuescan.username", 
        "valuescan.password"
    ]
    
    config = get_config()
    missing_keys = []
    
    for key in required_keys:
        keys = key.split('.')
        value = config
        try:
            for k in keys:
                value = value[k]
            if not value or value.startswith("your_"):
                missing_keys.append(key)
        except KeyError:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"警告: 以下配置项缺失或需要设置: {missing_keys}")
        return False
    
    return True

if __name__ == "__main__":
    # 配置验证
    if validate_config():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败，请检查API密钥设置")