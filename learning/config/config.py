"""
学习系统配置文件
"""

import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = BASE_DIR / "logs"

# 创建必要的目录
for dir_path in [DATA_DIR, MODEL_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 数据库配置
DATABASE_CONFIG = {
    "trade_records": {
        "path": DATA_DIR / "trade_records.db",
        "backup_path": DATA_DIR / "backups",
        "retention_days": 365 * 3  # 保留3年
    },
    "patterns": {
        "path": DATA_DIR / "patterns.db",
        "cache_size": 1000
    },
    "knowledge": {
        "path": DATA_DIR / "knowledge_base.db"
    }
}

# 机器学习配置
ML_CONFIG = {
    "models": {
        "price_prediction": {
            "type": "LSTM",
            "epochs": 100,
            "batch_size": 32,
            "learning_rate": 0.001
        },
        "trend_classification": {
            "type": "XGBoost",
            "n_estimators": 100,
            "max_depth": 6
        },
        "signal_quality": {
            "type": "RandomForest",
            "n_estimators": 200
        }
    },
    "training": {
        "test_split": 0.2,
        "validation_split": 0.1,
        "random_state": 42
    },
    "performance": {
        "min_accuracy": 0.7,
        "max_training_time": 3600,  # 1小时
        "prediction_latency": 0.1  # 100ms
    }
}

# 策略优化配置
OPTIMIZATION_CONFIG = {
    "methods": {
        "grid_search": {
            "enabled": True,
            "n_jobs": -1
        },
        "bayesian": {
            "enabled": True,
            "n_initial_points": 10,
            "n_calls": 50
        },
        "genetic": {
            "enabled": False,
            "population_size": 100,
            "generations": 50
        }
    },
    "ab_testing": {
        "min_sample_size": 100,
        "confidence_level": 0.95
    }
}

# 模式识别配置
PATTERN_CONFIG = {
    "clustering": {
        "algorithm": "kmeans",
        "n_clusters": 10,
        "max_iter": 300
    },
    "association": {
        "min_support": 0.1,
        "min_confidence": 0.6
    },
    "success_threshold": 0.6,  # 60%胜率以上算成功模式
    "failure_threshold": 0.4   # 40%胜率以下算失败模式
}

# 黑天鹅学习配置
BLACK_SWAN_CONFIG = {
    "historical_events": [
        "FTX_2022",
        "LUNA_2022",
        "312_2020",
        "SVB_2023"
    ],
    "alert_levels": {
        "level_1": {"threshold": 0.3, "action": "monitor"},
        "level_2": {"threshold": 0.6, "action": "reduce"},
        "level_3": {"threshold": 0.8, "action": "exit"}
    },
    "learning_rate": 0.1
}

# 提示词进化配置
PROMPT_CONFIG = {
    "mutation_rate": 0.1,
    "selection_pressure": 0.7,
    "population_size": 20,
    "elite_size": 5,
    "min_usage_for_evaluation": 10
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOG_DIR / "learning.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}