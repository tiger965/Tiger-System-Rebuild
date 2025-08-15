"""
Tiger System - Learning Evolution Module
学习进化系统 - 让系统越来越聪明
Author: Window-9
"""

__version__ = "1.0.0"
__author__ = "Window-9"

from .records.trade_recorder import TradeRecorder
from .patterns.pattern_learner import PatternLearner
from .optimizer.strategy_optimizer import StrategyOptimizer
from .prompts.prompt_evolution import PromptEvolution
from .knowledge.knowledge_base import KnowledgeBase
from .ml.ml_models import MLModels
from .black_swan.black_swan_learning import BlackSwanLearning

__all__ = [
    "TradeRecorder",
    "PatternLearner", 
    "StrategyOptimizer",
    "PromptEvolution",
    "KnowledgeBase",
    "MLModels",
    "BlackSwanLearning"
]