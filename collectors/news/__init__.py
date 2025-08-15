"""
新闻数据采集模块
"""
from .news_collector import NewsCollector
from .news_analyzer import NewsAnalyzer

__all__ = [
    'NewsCollector',
    'NewsAnalyzer'
]