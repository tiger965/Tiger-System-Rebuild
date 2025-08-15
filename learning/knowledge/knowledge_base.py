"""
知识库构建模块
构建和维护交易知识库
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from ..config.config import DATABASE_CONFIG, LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'knowledge_base.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class KnowledgeBase:
    """知识库系统"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG["knowledge"]["path"]
        self._init_database()
        logger.info("KnowledgeBase initialized")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 市场知识表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 交易规则表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                action TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 风险场景表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                description TEXT,
                indicators TEXT,
                mitigation TEXT,
                severity TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_market_knowledge(self, knowledge_type: str, title: str, content: str, tags: List[str] = None):
        """添加市场知识"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO market_knowledge 
            (knowledge_type, title, content, tags)
            VALUES (?, ?, ?, ?)
        ''', (knowledge_type, title, content, json.dumps(tags) if tags else None))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added market knowledge: {title}")
    
    def add_trading_rule(self, rule_name: str, rule_type: str, condition: str, action: str, priority: int = 0):
        """添加交易规则"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trading_rules
            (rule_name, rule_type, condition, action, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (rule_name, rule_type, condition, action, priority))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added trading rule: {rule_name}")
    
    def search_knowledge(self, query: str, knowledge_type: Optional[str] = None) -> List[Dict]:
        """搜索知识"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if knowledge_type:
            cursor.execute('''
                SELECT * FROM market_knowledge
                WHERE knowledge_type = ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY confidence DESC, usage_count DESC
            ''', (knowledge_type, f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT * FROM market_knowledge
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY confidence DESC, usage_count DESC
            ''', (f'%{query}%', f'%{query}%'))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # 更新使用次数
        for result in results:
            cursor.execute('''
                UPDATE market_knowledge
                SET usage_count = usage_count + 1
                WHERE id = ?
            ''', (result['id'],))
        
        conn.commit()
        conn.close()
        
        return results
    
    def get_applicable_rules(self, context: Dict) -> List[Dict]:
        """获取适用的规则"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trading_rules
            ORDER BY priority DESC, success_rate DESC
        ''')
        
        all_rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 筛选符合条件的规则
        applicable_rules = []
        for rule in all_rules:
            if self._evaluate_condition(rule['condition'], context):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """评估条件是否满足"""
        # 简单的条件评估逻辑
        try:
            # 将条件中的变量替换为实际值
            for key, value in context.items():
                condition = condition.replace(f'${key}', str(value))
            
            # 安全评估表达式
            return eval(condition, {"__builtins__": {}}, {})
        except:
            return False
    
    def cleanup(self):
        """清理资源"""
        logger.info("KnowledgeBase cleanup completed")