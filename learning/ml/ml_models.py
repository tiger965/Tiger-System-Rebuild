"""
机器学习模型模块
实现各种预测和分类模型
"""

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from ..config.config import ML_CONFIG, MODEL_DIR, LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'ml_models.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MLModels:
    """机器学习模型管理器"""
    
    def __init__(self):
        self.config = ML_CONFIG
        self.models = {}
        self.scalers = {}
        self.model_dir = MODEL_DIR
        
        # 确保模型目录存在
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("MLModels initialized")
    
    def prepare_features(self, data: pd.DataFrame, feature_type: str) -> pd.DataFrame:
        """准备特征"""
        features = pd.DataFrame()
        
        if feature_type == "technical":
            # 技术指标特征
            if 'close' in data.columns:
                features['returns'] = data['close'].pct_change()
                features['ma_ratio'] = data['close'] / data['close'].rolling(20).mean()
                features['volatility'] = data['close'].rolling(20).std()
            
            if 'volume' in data.columns:
                features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        
        elif feature_type == "market":
            # 市场微观特征
            if 'bid' in data.columns and 'ask' in data.columns:
                features['spread'] = data['ask'] - data['bid']
                features['mid_price'] = (data['bid'] + data['ask']) / 2
        
        return features.dropna()
    
    def train_price_prediction(self, data: pd.DataFrame) -> Dict:
        """训练价格预测模型"""
        logger.info("Training price prediction model...")
        
        # 准备特征
        features = self.prepare_features(data, "technical")
        
        if len(features) < 100:
            logger.warning("Insufficient data for training")
            return {"status": "failed", "reason": "insufficient_data"}
        
        # 准备标签（预测下一个时间点的价格）
        y = data['close'].shift(-1).dropna()
        X = features[:-1]  # 对齐特征和标签
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config["training"]["test_split"],
            random_state=self.config["training"]["random_state"]
        )
        
        # 标准化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 训练模型
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # 评估
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        # 保存模型
        self.models['price_prediction'] = model
        self.scalers['price_prediction'] = scaler
        self._save_model('price_prediction', model, scaler)
        
        logger.info(f"Price prediction model trained. Test score: {test_score:.4f}")
        
        return {
            "status": "success",
            "train_score": train_score,
            "test_score": test_score,
            "feature_importance": dict(zip(X.columns, model.feature_importances_))
        }
    
    def train_trend_classification(self, data: pd.DataFrame) -> Dict:
        """训练趋势分类模型"""
        logger.info("Training trend classification model...")
        
        # 准备特征
        features = self.prepare_features(data, "technical")
        
        if len(features) < 100:
            return {"status": "failed", "reason": "insufficient_data"}
        
        # 创建标签（上涨/下跌/横盘）
        returns = data['close'].pct_change().shift(-1).dropna()
        y = pd.cut(returns, bins=[-np.inf, -0.01, 0.01, np.inf], labels=['down', 'neutral', 'up'])
        
        X = features[:-1]
        y = y[:-1]
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config["training"]["test_split"],
            random_state=self.config["training"]["random_state"]
        )
        
        # 标准化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 训练模型
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # 评估
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        # 保存模型
        self.models['trend_classification'] = model
        self.scalers['trend_classification'] = scaler
        self._save_model('trend_classification', model, scaler)
        
        logger.info(f"Trend classification model trained. Test score: {test_score:.4f}")
        
        return {
            "status": "success",
            "train_score": train_score,
            "test_score": test_score,
            "classes": model.classes_.tolist()
        }
    
    def predict(self, model_name: str, features: pd.DataFrame) -> np.ndarray:
        """使用模型预测"""
        if model_name not in self.models:
            # 尝试加载模型
            if not self._load_model(model_name):
                logger.error(f"Model {model_name} not found")
                return np.array([])
        
        model = self.models[model_name]
        scaler = self.scalers[model_name]
        
        # 标准化特征
        features_scaled = scaler.transform(features)
        
        # 预测
        predictions = model.predict(features_scaled)
        
        return predictions
    
    def predict_proba(self, model_name: str, features: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if model_name not in self.models:
            if not self._load_model(model_name):
                return np.array([])
        
        model = self.models[model_name]
        scaler = self.scalers[model_name]
        
        # 标准化特征
        features_scaled = scaler.transform(features)
        
        # 预测概率
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(features_scaled)
        else:
            # 对于回归模型，返回预测值
            probabilities = model.predict(features_scaled).reshape(-1, 1)
        
        return probabilities
    
    def evaluate_model(self, model_name: str, X_test: pd.DataFrame, y_test) -> Dict:
        """评估模型"""
        if model_name not in self.models:
            return {"error": "Model not found"}
        
        model = self.models[model_name]
        scaler = self.scalers[model_name]
        
        # 标准化特征
        X_test_scaled = scaler.transform(X_test)
        
        # 评分
        score = model.score(X_test_scaled, y_test)
        
        # 交叉验证
        cv_scores = cross_val_score(model, X_test_scaled, y_test, cv=5)
        
        return {
            "test_score": score,
            "cv_scores": cv_scores.tolist(),
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std()
        }
    
    def _save_model(self, model_name: str, model, scaler):
        """保存模型"""
        model_path = self.model_dir / f"{model_name}_model.pkl"
        scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        
        logger.info(f"Model {model_name} saved")
    
    def _load_model(self, model_name: str) -> bool:
        """加载模型"""
        model_path = self.model_dir / f"{model_name}_model.pkl"
        scaler_path = self.model_dir / f"{model_name}_scaler.pkl"
        
        if not model_path.exists() or not scaler_path.exists():
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.models[model_name] = pickle.load(f)
            
            with open(scaler_path, 'rb') as f:
                self.scalers[model_name] = pickle.load(f)
            
            logger.info(f"Model {model_name} loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict:
        """获取模型信息"""
        if model_name not in self.models:
            return {"error": "Model not found"}
        
        model = self.models[model_name]
        
        info = {
            "model_type": type(model).__name__,
            "n_features": model.n_features_in_ if hasattr(model, 'n_features_in_') else None
        }
        
        if hasattr(model, 'feature_importances_'):
            info["feature_importances"] = model.feature_importances_.tolist()
        
        if hasattr(model, 'classes_'):
            info["classes"] = model.classes_.tolist()
        
        return info
    
    def cleanup(self):
        """清理资源"""
        self.models.clear()
        self.scalers.clear()
        logger.info("MLModels cleanup completed")