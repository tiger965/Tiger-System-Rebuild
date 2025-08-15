"""
Tiger AI Decision System - 智能决策核心
Window 6 - AI Strategy Officer & Decision Architect
"""

__version__ = "1.0.0"
__author__ = "Tiger System Window 6"

from .trigger.trigger_system import TriggerSystem
from .prompts.prompt_templates import PromptTemplates
from .claude_client import ClaudeClient
from .context_manager import ContextManager
from .decision_formatter import DecisionFormatter
from .strategy_weights import StrategyWeights

__all__ = [
    'TriggerSystem',
    'PromptTemplates', 
    'ClaudeClient',
    'ContextManager',
    'DecisionFormatter',
    'StrategyWeights'
]