"""
AI提示词进化模块
负责优化和进化AI模型的提示词
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import random
import numpy as np
from collections import defaultdict

from ..config.config import PROMPT_CONFIG, DATABASE_CONFIG, LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'prompt_evolution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PromptEvolution:
    """提示词进化系统"""
    
    def __init__(self):
        self.config = PROMPT_CONFIG
        self.db_path = DATABASE_CONFIG["patterns"]["path"].parent / "prompts.db"
        
        # 进化参数
        self.mutation_rate = self.config["mutation_rate"]
        self.selection_pressure = self.config["selection_pressure"]
        self.population_size = self.config["population_size"]
        self.elite_size = self.config["elite_size"]
        
        # 初始化数据库
        self._init_database()
        
        # 提示词种群
        self.prompt_population = self._load_population()
        
        logger.info("PromptEvolution initialized")
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 提示词表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                prompt_id TEXT PRIMARY KEY,
                prompt_type TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                execution_rate REAL DEFAULT 0,
                generation INTEGER DEFAULT 0,
                parent_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT
            )
        ''')
        
        # 提示词性能记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT NOT NULL,
                execution_time REAL,
                confidence_score REAL,
                was_executed BOOLEAN,
                was_successful BOOLEAN,
                feedback TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_population(self) -> List[Dict]:
        """加载提示词种群"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prompts
            ORDER BY success_rate DESC
            LIMIT ?
        ''', (self.population_size,))
        
        population = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 如果种群不足，创建初始种群
        if len(population) < self.population_size:
            population.extend(self._create_initial_population(
                self.population_size - len(population)
            ))
        
        return population
    
    def _create_initial_population(self, size: int) -> List[Dict]:
        """创建初始种群"""
        initial_prompts = []
        
        # 基础提示词模板
        templates = {
            "market_analysis": [
                "分析当前{symbol}市场状况，关注{indicators}指标，判断{timeframe}内的趋势",
                "基于{data}数据，评估{symbol}的{action}时机，置信度需达到{threshold}",
                "综合{signals}信号，预测{symbol}在{period}内的价格走向"
            ],
            "risk_assessment": [
                "评估{position}仓位的风险，考虑{factors}因素，给出风险等级",
                "分析{event}事件对{portfolio}的影响，提供{action}建议",
                "计算{scenario}情况下的最大损失，制定{strategy}策略"
            ],
            "trade_decision": [
                "根据{analysis}分析，决定是否{action} {symbol}，仓位建议{size}",
                "当前{conditions}条件下，执行{strategy}策略的成功率评估",
                "综合{metrics}指标，给出{timeframe}内的交易建议"
            ]
        }
        
        for i in range(size):
            prompt_type = random.choice(list(templates.keys()))
            template = random.choice(templates[prompt_type])
            
            prompt = {
                "prompt_id": f"PROMPT_{datetime.now().strftime('%Y%m%d')}_{i:04d}",
                "prompt_type": prompt_type,
                "prompt_text": template,
                "usage_count": 0,
                "success_count": 0,
                "success_rate": 0.5,  # 初始成功率
                "avg_confidence": 0.5,
                "execution_rate": 0.5,
                "generation": 0,
                "parent_id": None
            }
            
            initial_prompts.append(prompt)
            self._save_prompt(prompt)
        
        return initial_prompts
    
    def record_usage(self,
                    prompt_id: str,
                    confidence_score: float,
                    was_executed: bool,
                    was_successful: Optional[bool] = None,
                    execution_time: Optional[float] = None):
        """记录提示词使用情况"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 记录性能
        cursor.execute('''
            INSERT INTO prompt_performance
            (prompt_id, execution_time, confidence_score, was_executed, was_successful)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt_id, execution_time, confidence_score, was_executed, was_successful))
        
        # 更新提示词统计
        cursor.execute('UPDATE prompts SET usage_count = usage_count + 1 WHERE prompt_id = ?', (prompt_id,))
        
        if was_successful is not None and was_successful:
            cursor.execute('UPDATE prompts SET success_count = success_count + 1 WHERE prompt_id = ?', (prompt_id,))
        
        # 更新成功率和其他指标
        cursor.execute('''
            UPDATE prompts SET
                success_rate = CAST(success_count AS REAL) / CAST(usage_count AS REAL),
                last_used = ?
            WHERE prompt_id = ? AND usage_count > 0
        ''', (datetime.now().isoformat(), prompt_id))
        
        # 更新平均置信度
        cursor.execute('''
            UPDATE prompts SET
                avg_confidence = (
                    SELECT AVG(confidence_score)
                    FROM prompt_performance
                    WHERE prompt_id = ?
                )
            WHERE prompt_id = ?
        ''', (prompt_id, prompt_id))
        
        # 更新执行率
        cursor.execute('''
            UPDATE prompts SET
                execution_rate = (
                    SELECT AVG(CASE WHEN was_executed THEN 1.0 ELSE 0.0 END)
                    FROM prompt_performance
                    WHERE prompt_id = ?
                )
            WHERE prompt_id = ?
        ''', (prompt_id, prompt_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded usage for prompt {prompt_id}")
    
    def mutate_prompt(self, prompt: Dict) -> Dict:
        """变异提示词"""
        new_prompt = prompt.copy()
        new_prompt["prompt_id"] = f"PROMPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        new_prompt["parent_id"] = prompt["prompt_id"]
        new_prompt["generation"] = prompt.get("generation", 0) + 1
        
        # 重置统计
        new_prompt["usage_count"] = 0
        new_prompt["success_count"] = 0
        
        # 变异操作
        mutation_type = random.choice(["add_context", "refine", "adjust_tone", "add_examples"])
        
        if mutation_type == "add_context":
            # 添加上下文
            additions = [
                "请特别关注市场情绪",
                "考虑最近的黑天鹅事件",
                "参考历史相似案例",
                "注意风险控制"
            ]
            new_prompt["prompt_text"] += f"。{random.choice(additions)}"
        
        elif mutation_type == "refine":
            # 优化指令
            refinements = {
                "分析": "深入分析",
                "评估": "全面评估",
                "判断": "准确判断",
                "预测": "精确预测"
            }
            for old, new in refinements.items():
                new_prompt["prompt_text"] = new_prompt["prompt_text"].replace(old, new)
        
        elif mutation_type == "adjust_tone":
            # 调整语气
            if "建议" in new_prompt["prompt_text"]:
                new_prompt["prompt_text"] = new_prompt["prompt_text"].replace("建议", "强烈建议")
            if "可能" in new_prompt["prompt_text"]:
                new_prompt["prompt_text"] = new_prompt["prompt_text"].replace("可能", "很可能")
        
        elif mutation_type == "add_examples":
            # 添加示例
            new_prompt["prompt_text"] += "。参考示例：成功案例包括[具体案例]"
        
        return new_prompt
    
    def crossover_prompts(self, parent1: Dict, parent2: Dict) -> Dict:
        """交叉提示词"""
        # 简单的交叉：组合两个提示词的部分
        child = {
            "prompt_id": f"PROMPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            "prompt_type": parent1["prompt_type"],
            "prompt_text": "",
            "usage_count": 0,
            "success_count": 0,
            "success_rate": (parent1["success_rate"] + parent2["success_rate"]) / 2,
            "avg_confidence": (parent1["avg_confidence"] + parent2["avg_confidence"]) / 2,
            "execution_rate": (parent1["execution_rate"] + parent2["execution_rate"]) / 2,
            "generation": max(parent1.get("generation", 0), parent2.get("generation", 0)) + 1,
            "parent_id": f"{parent1['prompt_id']}+{parent2['prompt_id']}"
        }
        
        # 组合文本
        parts1 = parent1["prompt_text"].split("，")
        parts2 = parent2["prompt_text"].split("，")
        
        # 随机选择部分
        combined_parts = []
        for i in range(max(len(parts1), len(parts2))):
            if i < len(parts1) and i < len(parts2):
                combined_parts.append(random.choice([parts1[i], parts2[i]]))
            elif i < len(parts1):
                combined_parts.append(parts1[i])
            elif i < len(parts2):
                combined_parts.append(parts2[i])
        
        child["prompt_text"] = "，".join(combined_parts)
        
        return child
    
    def evolve_population(self):
        """进化种群"""
        logger.info("Starting population evolution...")
        
        # 重新加载种群并排序
        self.prompt_population = self._load_population()
        
        # 计算适应度分数
        for prompt in self.prompt_population:
            prompt["fitness"] = self._calculate_fitness(prompt)
        
        # 排序
        self.prompt_population.sort(key=lambda x: x["fitness"], reverse=True)
        
        # 选择精英
        elite = self.prompt_population[:self.elite_size]
        
        # 生成新一代
        new_generation = elite.copy()
        
        while len(new_generation) < self.population_size:
            # 选择父母
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # 交叉或变异
            if random.random() < 0.7:  # 70%概率交叉
                child = self.crossover_prompts(parent1, parent2)
            else:  # 30%概率变异
                child = self.mutate_prompt(random.choice([parent1, parent2]))
            
            # 额外的变异机会
            if random.random() < self.mutation_rate:
                child = self.mutate_prompt(child)
            
            new_generation.append(child)
            self._save_prompt(child)
        
        # 更新种群
        self.prompt_population = new_generation[:self.population_size]
        
        logger.info(f"Evolution completed. New generation size: {len(self.prompt_population)}")
    
    def _calculate_fitness(self, prompt: Dict) -> float:
        """计算适应度"""
        # 考虑多个因素
        success_weight = 0.4
        confidence_weight = 0.3
        execution_weight = 0.2
        usage_weight = 0.1
        
        # 归一化使用次数（避免过度使用）
        normalized_usage = min(prompt.get("usage_count", 0) / 100, 1.0)
        
        fitness = (
            prompt.get("success_rate", 0) * success_weight +
            prompt.get("avg_confidence", 0) * confidence_weight +
            prompt.get("execution_rate", 0) * execution_weight +
            normalized_usage * usage_weight
        )
        
        return fitness
    
    def _tournament_selection(self, tournament_size: int = 3) -> Dict:
        """锦标赛选择"""
        tournament = random.sample(self.prompt_population, min(tournament_size, len(self.prompt_population)))
        return max(tournament, key=lambda x: x.get("fitness", 0))
    
    def get_best_prompt(self, prompt_type: str, context: Optional[Dict] = None) -> Dict:
        """获取最佳提示词"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取该类型的最佳提示词
        cursor.execute('''
            SELECT * FROM prompts
            WHERE prompt_type = ? AND usage_count >= ?
            ORDER BY success_rate DESC, avg_confidence DESC
            LIMIT 1
        ''', (prompt_type, self.config["min_usage_for_evaluation"]))
        
        result = cursor.fetchone()
        
        if result:
            prompt = dict(result)
        else:
            # 如果没有足够数据，返回默认提示词
            cursor.execute('''
                SELECT * FROM prompts
                WHERE prompt_type = ?
                ORDER BY generation DESC
                LIMIT 1
            ''', (prompt_type,))
            
            result = cursor.fetchone()
            prompt = dict(result) if result else self._create_default_prompt(prompt_type)
        
        conn.close()
        
        # 根据上下文填充变量
        if context and "{" in prompt["prompt_text"]:
            prompt["prompt_text"] = self._fill_template(prompt["prompt_text"], context)
        
        return prompt
    
    def _fill_template(self, template: str, context: Dict) -> str:
        """填充模板变量"""
        filled = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in filled:
                filled = filled.replace(placeholder, str(value))
        
        # 移除未填充的占位符
        import re
        filled = re.sub(r'\{[^}]+\}', '[待定]', filled)
        
        return filled
    
    def _create_default_prompt(self, prompt_type: str) -> Dict:
        """创建默认提示词"""
        defaults = {
            "market_analysis": "分析当前市场状况，给出专业判断",
            "risk_assessment": "评估当前风险，提供风险等级和建议",
            "trade_decision": "基于当前数据，给出交易决策建议"
        }
        
        prompt = {
            "prompt_id": f"DEFAULT_{prompt_type}",
            "prompt_type": prompt_type,
            "prompt_text": defaults.get(prompt_type, "请分析并提供建议"),
            "usage_count": 0,
            "success_count": 0,
            "success_rate": 0.5,
            "avg_confidence": 0.5,
            "execution_rate": 0.5,
            "generation": 0,
            "parent_id": None
        }
        
        return prompt
    
    def _save_prompt(self, prompt: Dict):
        """保存提示词"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO prompts
            (prompt_id, prompt_type, prompt_text, usage_count,
             success_count, success_rate, avg_confidence,
             execution_rate, generation, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prompt["prompt_id"],
            prompt["prompt_type"],
            prompt["prompt_text"],
            prompt.get("usage_count", 0),
            prompt.get("success_count", 0),
            prompt.get("success_rate", 0),
            prompt.get("avg_confidence", 0),
            prompt.get("execution_rate", 0),
            prompt.get("generation", 0),
            prompt.get("parent_id")
        ))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 总体统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total_prompts,
                AVG(success_rate) as avg_success_rate,
                AVG(avg_confidence) as avg_confidence,
                AVG(execution_rate) as avg_execution_rate,
                MAX(generation) as max_generation,
                SUM(usage_count) as total_usage
            FROM prompts
        ''')
        
        stats = dict(cursor.fetchone())
        
        # 按类型统计
        cursor.execute('''
            SELECT 
                prompt_type,
                COUNT(*) as count,
                AVG(success_rate) as avg_success_rate
            FROM prompts
            GROUP BY prompt_type
        ''')
        
        type_stats = {}
        for row in cursor.fetchall():
            type_stats[row[0]] = {
                "count": row[1],
                "avg_success_rate": row[2]
            }
        
        stats["type_statistics"] = type_stats
        
        conn.close()
        
        return stats
    
    def cleanup(self):
        """清理资源"""
        self.prompt_population.clear()
        logger.info("PromptEvolution cleanup completed")