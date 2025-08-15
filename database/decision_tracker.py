"""AI决策记录跟踪系统"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionStatus(Enum):
    """决策状态枚举"""
    PENDING = "pending"          # 待执行
    EXECUTING = "executing"       # 执行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消
    FAILED = "failed"            # 失败
    PARTIAL = "partial"          # 部分成交

class DecisionType(Enum):
    """决策类型枚举"""
    BUY = "buy"                  # 买入
    SELL = "sell"                # 卖出
    HOLD = "hold"                # 持有
    CLOSE = "close"              # 平仓
    STOP_LOSS = "stop_loss"      # 止损
    TAKE_PROFIT = "take_profit"  # 止盈
    HEDGE = "hedge"              # 对冲

class DecisionTracker:
    """AI决策记录跟踪器"""
    
    def __init__(self, dal=None):
        """初始化决策跟踪器
        
        Args:
            dal: 数据访问层实例
        """
        self.dal = dal
        self.decisions_cache = {}  # 决策缓存
        self.pending_decisions = []  # 待执行决策
        self.execution_history = []  # 执行历史
        
    async def record_decision(self, decision_data: Dict) -> Dict:
        """记录AI决策
        
        Args:
            decision_data: 决策数据
            
        Returns:
            记录结果
        """
        try:
            # 生成决策ID
            decision_id = decision_data.get('id', str(uuid.uuid4()))
            
            # 构建完整决策记录
            decision_record = {
                'id': decision_id,
                'timestamp': datetime.now().isoformat(),
                'type': decision_data.get('type', DecisionType.HOLD.value),
                'symbol': decision_data.get('symbol', 'BTCUSDT'),
                'side': decision_data.get('side', 'buy'),
                'price': decision_data.get('price', 0),
                'amount': decision_data.get('amount', 0),
                'reason': decision_data.get('reason', ''),
                'confidence': decision_data.get('confidence', 0.5),
                'status': DecisionStatus.PENDING.value,
                'source': decision_data.get('source', 'ai_engine'),
                'strategy': decision_data.get('strategy', 'default'),
                'risk_level': decision_data.get('risk_level', 0.3),
                'expected_profit': decision_data.get('expected_profit', 0),
                'stop_loss': decision_data.get('stop_loss', 0),
                'take_profit': decision_data.get('take_profit', 0),
                'metadata': decision_data.get('metadata', {}),
                'market_conditions': await self._get_market_conditions(
                    decision_data.get('symbol', 'BTCUSDT')
                ),
                'ai_analysis': decision_data.get('ai_analysis', {}),
                'execution_params': decision_data.get('execution_params', {})
            }
            
            # 验证决策
            validation_result = await self._validate_decision(decision_record)
            if not validation_result['valid']:
                logger.warning(f"决策验证失败: {validation_result['reason']}")
                decision_record['status'] = DecisionStatus.FAILED.value
                decision_record['failure_reason'] = validation_result['reason']
            
            # 存储到数据库
            await self._save_to_database(decision_record)
            
            # 添加到缓存
            self.decisions_cache[decision_id] = decision_record
            
            # 如果是待执行决策，添加到待执行队列
            if decision_record['status'] == DecisionStatus.PENDING.value:
                self.pending_decisions.append(decision_record)
            
            # 记录到执行历史
            self.execution_history.append({
                'decision_id': decision_id,
                'timestamp': datetime.now().isoformat(),
                'action': 'recorded',
                'status': decision_record['status']
            })
            
            logger.info(f"决策已记录: {decision_id}")
            
            return {
                'success': True,
                'decision_id': decision_id,
                'status': decision_record['status'],
                'message': '决策记录成功'
            }
            
        except Exception as e:
            logger.error(f"记录决策失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '决策记录失败'
            }
    
    async def get_decision(self, decision_id: str) -> Optional[Dict]:
        """获取决策详情
        
        Args:
            decision_id: 决策ID
            
        Returns:
            决策详情
        """
        try:
            # 从缓存获取
            if decision_id in self.decisions_cache:
                return self.decisions_cache[decision_id]
            
            # 从数据库获取
            if self.dal:
                query = "SELECT * FROM decisions WHERE id = %s"
                result = self.dal.execute_query(query, (decision_id,))
                if result:
                    decision = dict(result[0])
                    self.decisions_cache[decision_id] = decision
                    return decision
            
            return None
            
        except Exception as e:
            logger.error(f"获取决策失败: {e}")
            return None
    
    async def update_decision_status(self, decision_id: str, 
                                    status: str, 
                                    execution_result: Dict = None) -> bool:
        """更新决策状态
        
        Args:
            decision_id: 决策ID
            status: 新状态
            execution_result: 执行结果
            
        Returns:
            是否更新成功
        """
        try:
            # 获取决策
            decision = await self.get_decision(decision_id)
            if not decision:
                logger.warning(f"决策不存在: {decision_id}")
                return False
            
            # 更新状态
            old_status = decision['status']
            decision['status'] = status
            decision['updated_at'] = datetime.now().isoformat()
            
            # 添加执行结果
            if execution_result:
                decision['execution_result'] = execution_result
                decision['actual_price'] = execution_result.get('price', 0)
                decision['actual_amount'] = execution_result.get('amount', 0)
                decision['execution_time'] = execution_result.get('time', datetime.now().isoformat())
            
            # 更新数据库
            if self.dal:
                query = """
                    UPDATE decisions 
                    SET status = %s, updated_at = %s, execution_result = %s
                    WHERE id = %s
                """
                self.dal.execute_update(
                    query, 
                    (status, datetime.now(), json.dumps(execution_result), decision_id)
                )
            
            # 更新缓存
            self.decisions_cache[decision_id] = decision
            
            # 从待执行队列移除
            if status in [DecisionStatus.COMPLETED.value, 
                         DecisionStatus.FAILED.value, 
                         DecisionStatus.CANCELLED.value]:
                self.pending_decisions = [
                    d for d in self.pending_decisions 
                    if d['id'] != decision_id
                ]
            
            # 记录状态变更
            self.execution_history.append({
                'decision_id': decision_id,
                'timestamp': datetime.now().isoformat(),
                'action': 'status_update',
                'old_status': old_status,
                'new_status': status
            })
            
            logger.info(f"决策状态已更新: {decision_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"更新决策状态失败: {e}")
            return False
    
    async def get_pending_decisions(self) -> List[Dict]:
        """获取待执行决策列表
        
        Returns:
            待执行决策列表
        """
        try:
            # 从缓存返回
            if self.pending_decisions:
                return self.pending_decisions
            
            # 从数据库获取
            if self.dal:
                query = """
                    SELECT * FROM decisions 
                    WHERE status = %s
                    ORDER BY created_at DESC
                """
                results = self.dal.execute_query(query, (DecisionStatus.PENDING.value,))
                if results:
                    self.pending_decisions = [dict(r) for r in results]
                    return self.pending_decisions
            
            return []
            
        except Exception as e:
            logger.error(f"获取待执行决策失败: {e}")
            return []
    
    async def get_decision_history(self, 
                                  user_id: str = "default",
                                  days: int = 30,
                                  status: str = None) -> List[Dict]:
        """获取决策历史
        
        Args:
            user_id: 用户ID
            days: 历史天数
            status: 状态筛选
            
        Returns:
            决策历史列表
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            if self.dal:
                query = """
                    SELECT * FROM decisions 
                    WHERE created_at >= %s
                """
                params = [start_date]
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC"
                
                results = self.dal.execute_query(query, tuple(params))
                return [dict(r) for r in results] if results else []
            
            # 从缓存返回模拟数据
            return self._generate_mock_history()
            
        except Exception as e:
            logger.error(f"获取决策历史失败: {e}")
            return []
    
    async def get_decision_statistics(self, days: int = 30) -> Dict:
        """获取决策统计
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        try:
            history = await self.get_decision_history(days=days)
            
            if not history:
                return {
                    'total_decisions': 0,
                    'success_rate': 0.0,
                    'avg_confidence': 0.0,
                    'by_type': {},
                    'by_status': {}
                }
            
            # 统计各类数据
            total = len(history)
            completed = [d for d in history if d['status'] == DecisionStatus.COMPLETED.value]
            success_rate = len(completed) / total if total > 0 else 0
            
            # 按类型统计
            by_type = {}
            for decision in history:
                d_type = decision.get('type', 'unknown')
                by_type[d_type] = by_type.get(d_type, 0) + 1
            
            # 按状态统计
            by_status = {}
            for decision in history:
                status = decision.get('status', 'unknown')
                by_status[status] = by_status.get(status, 0) + 1
            
            # 计算平均置信度
            confidences = [d.get('confidence', 0) for d in history]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # 计算收益统计
            profits = []
            for decision in completed:
                if 'execution_result' in decision:
                    profit = decision['execution_result'].get('profit', 0)
                    profits.append(profit)
            
            return {
                'total_decisions': total,
                'success_rate': round(success_rate, 3),
                'avg_confidence': round(avg_confidence, 3),
                'by_type': by_type,
                'by_status': by_status,
                'completed_count': len(completed),
                'total_profit': sum(profits) if profits else 0,
                'avg_profit': sum(profits) / len(profits) if profits else 0,
                'win_rate': len([p for p in profits if p > 0]) / len(profits) if profits else 0
            }
            
        except Exception as e:
            logger.error(f"获取决策统计失败: {e}")
            return {
                'total_decisions': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0
            }
    
    async def _validate_decision(self, decision: Dict) -> Dict:
        """验证决策
        
        Args:
            decision: 决策数据
            
        Returns:
            验证结果
        """
        try:
            # 检查必要字段
            required_fields = ['symbol', 'type', 'price', 'amount']
            for field in required_fields:
                if field not in decision or not decision[field]:
                    return {
                        'valid': False,
                        'reason': f'缺少必要字段: {field}'
                    }
            
            # 检查价格合理性
            if decision['price'] <= 0:
                return {
                    'valid': False,
                    'reason': '价格必须大于0'
                }
            
            # 检查数量合理性
            if decision['amount'] <= 0:
                return {
                    'valid': False,
                    'reason': '数量必须大于0'
                }
            
            # 检查置信度
            confidence = decision.get('confidence', 0)
            if confidence < 0 or confidence > 1:
                return {
                    'valid': False,
                    'reason': '置信度必须在0-1之间'
                }
            
            # 检查风险等级
            risk_level = decision.get('risk_level', 0)
            if risk_level < 0 or risk_level > 1:
                return {
                    'valid': False,
                    'reason': '风险等级必须在0-1之间'
                }
            
            return {
                'valid': True,
                'reason': 'OK'
            }
            
        except Exception as e:
            logger.error(f"验证决策失败: {e}")
            return {
                'valid': False,
                'reason': str(e)
            }
    
    async def _get_market_conditions(self, symbol: str) -> Dict:
        """获取市场条件
        
        Args:
            symbol: 交易对
            
        Returns:
            市场条件
        """
        try:
            # 这里应该从市场数据获取实时信息
            # 现在返回模拟数据
            return {
                'trend': 'bullish',
                'volatility': 0.02,
                'volume': 1000000,
                'rsi': 65,
                'macd': 'positive',
                'support': 49000,
                'resistance': 52000
            }
            
        except Exception as e:
            logger.error(f"获取市场条件失败: {e}")
            return {}
    
    async def _save_to_database(self, decision: Dict):
        """保存决策到数据库
        
        Args:
            decision: 决策数据
        """
        try:
            if not self.dal:
                return
            
            query = """
                INSERT INTO decisions (
                    id, type, symbol, side, price, amount, 
                    reason, confidence, status, source, strategy,
                    risk_level, metadata, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                decision['id'],
                decision['type'],
                decision['symbol'],
                decision['side'],
                decision['price'],
                decision['amount'],
                decision['reason'],
                decision['confidence'],
                decision['status'],
                decision['source'],
                decision['strategy'],
                decision['risk_level'],
                json.dumps(decision.get('metadata', {})),
                datetime.now()
            )
            
            self.dal.execute_insert(query, params)
            logger.info(f"决策已保存到数据库: {decision['id']}")
            
        except Exception as e:
            logger.error(f"保存决策到数据库失败: {e}")
    
    def _generate_mock_history(self) -> List[Dict]:
        """生成模拟决策历史"""
        history = []
        for i in range(20):
            history.append({
                'id': f'decision_{i}',
                'type': DecisionType.BUY.value if i % 2 == 0 else DecisionType.SELL.value,
                'symbol': 'BTCUSDT',
                'price': 50000 + i * 100,
                'amount': 0.01,
                'confidence': 0.6 + (i % 4) * 0.1,
                'status': DecisionStatus.COMPLETED.value if i < 15 else DecisionStatus.PENDING.value,
                'created_at': (datetime.now() - timedelta(days=i)).isoformat()
            })
        return history
    
    async def cleanup_old_decisions(self, days: int = 90):
        """清理旧决策记录
        
        Args:
            days: 保留天数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if self.dal:
                query = "DELETE FROM decisions WHERE created_at < %s"
                deleted = self.dal.execute_update(query, (cutoff_date,))
                logger.info(f"已清理 {deleted} 条旧决策记录")
            
            # 清理缓存
            self.decisions_cache = {}
            self.pending_decisions = []
            
        except Exception as e:
            logger.error(f"清理旧决策失败: {e}")