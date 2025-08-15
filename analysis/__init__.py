"""
Window 4 - 计算工具
纯计算模块，不包含任何决策逻辑
"""

from .window4_technical.standard_indicators import StandardIndicators
from .window4_technical.tiger_custom import TigerCustomIndicators
from .window4_technical.pattern_recognition import PatternRecognition
from .window4_technical.mtf_analysis import MultiTimeframeAnalysis
from .window4_technical.kline_manager import KlineManager
from .window4_technical.batch_calculator import BatchCalculator

__all__ = [
    'StandardIndicators',
    'TigerCustomIndicators',
    'PatternRecognition',
    'MultiTimeframeAnalysis',
    'KlineManager',
    'BatchCalculator'
]

__version__ = '4.1'