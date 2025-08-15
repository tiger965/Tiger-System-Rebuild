"""Opportunity Data Access Layer"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json
import logging
from .base_dal import BaseDAL

logger = logging.getLogger(__name__)

class OpportunityDAL(BaseDAL):
    """机会管理数据访问层"""
    
    def create_position(self, position_data: dict) -> Optional[str]:
        """创建机会仓位
        
        Args:
            position_data: 仓位数据
            
        Returns:
            仓位ID
        """
        query = """
            INSERT INTO opportunity_positions (
                timestamp, symbol, position_type, entry_price, 
                position_size, leverage, status, source, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            position_data.get('timestamp', datetime.now()),
            position_data['symbol'],
            position_data['position_type'],
            position_data['entry_price'],
            position_data['position_size'],
            position_data.get('leverage', 1.0),
            position_data.get('status', 'open'),
            position_data.get('source'),
            json.dumps(position_data.get('metadata', {}))
        )
        
        position_id = self.execute_insert(query, params)
        
        # 缓存仓位数据
        if position_id:
            cache_key = f"position:{position_id}"
            self.cache_set(cache_key, position_data, ttl=3600)
        
        return position_id
    
    def get_position(self, position_id: str) -> Optional[Dict]:
        """获取仓位信息
        
        Args:
            position_id: 仓位ID
            
        Returns:
            仓位信息
        """
        # 先查缓存
        cache_key = f"position:{position_id}"
        cached = self.cache_get(cache_key)
        if cached:
            return cached
        
        query = """
            SELECT * FROM opportunity_positions 
            WHERE id = %s
        """
        
        results = self.execute_query(query, (position_id,))
        if results:
            position = dict(results[0])
            # 转换Decimal为float
            for key in ['entry_price', 'current_price', 'target_price', 
                       'stop_loss', 'position_size', 'leverage', 
                       'unrealized_pnl', 'realized_pnl']:
                if position.get(key):
                    position[key] = float(position[key])
            
            # 缓存结果
            self.cache_set(cache_key, position, ttl=300)
            return position
        
        return None
    
    def update_position(self, position_id: str, updates: dict) -> bool:
        """更新仓位信息
        
        Args:
            position_id: 仓位ID
            updates: 更新数据
            
        Returns:
            是否成功
        """
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key in ['current_price', 'target_price', 'stop_loss', 
                      'unrealized_pnl', 'realized_pnl', 'risk_score', 
                      'opportunity_score', 'status']:
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = %s")
        params.append(datetime.now())
        params.append(position_id)
        
        query = f"""
            UPDATE opportunity_positions 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        affected = self.execute_update(query, tuple(params))
        
        # 清除缓存
        if affected > 0:
            cache_key = f"position:{position_id}"
            self.redis_conn.delete(cache_key)
        
        return affected > 0
    
    def get_open_positions(self, symbol: str = None) -> List[Dict]:
        """获取开放仓位
        
        Args:
            symbol: 交易对(可选)
            
        Returns:
            仓位列表
        """
        if symbol:
            query = """
                SELECT * FROM opportunity_positions 
                WHERE status = 'open' AND symbol = %s
                ORDER BY timestamp DESC
            """
            params = (symbol,)
        else:
            query = """
                SELECT * FROM opportunity_positions 
                WHERE status = 'open'
                ORDER BY timestamp DESC
            """
            params = None
        
        results = self.execute_query(query, params)
        
        # 转换Decimal
        positions = []
        for row in results:
            position = dict(row)
            for key in ['entry_price', 'current_price', 'position_size', 
                       'leverage', 'unrealized_pnl']:
                if position.get(key):
                    position[key] = float(position[key])
            positions.append(position)
        
        return positions
    
    def create_signal(self, signal_data: dict) -> Optional[str]:
        """创建机会信号
        
        Args:
            signal_data: 信号数据
            
        Returns:
            信号ID
        """
        query = """
            INSERT INTO opportunity_signals (
                timestamp, window_id, signal_type, symbol, 
                opportunity_type, confidence, expected_return,
                risk_level, time_horizon, trigger_conditions,
                action_params, expiry_time, status, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            signal_data.get('timestamp', datetime.now()),
            signal_data['window_id'],
            signal_data['signal_type'],
            signal_data['symbol'],
            signal_data.get('opportunity_type'),
            signal_data['confidence'],
            signal_data.get('expected_return'),
            signal_data.get('risk_level'),
            signal_data.get('time_horizon'),
            json.dumps(signal_data.get('trigger_conditions', {})),
            json.dumps(signal_data.get('action_params', {})),
            signal_data.get('expiry_time'),
            signal_data.get('status', 'pending'),
            json.dumps(signal_data.get('metadata', {}))
        )
        
        return self.execute_insert(query, params)
    
    def get_pending_signals(self, window_id: int = None) -> List[Dict]:
        """获取待处理信号
        
        Args:
            window_id: 窗口ID(可选)
            
        Returns:
            信号列表
        """
        if window_id:
            query = """
                SELECT * FROM opportunity_signals 
                WHERE status = 'pending' AND window_id = %s
                ORDER BY confidence DESC, timestamp DESC
            """
            params = (window_id,)
        else:
            query = """
                SELECT * FROM opportunity_signals 
                WHERE status = 'pending'
                ORDER BY confidence DESC, timestamp DESC
            """
            params = None
        
        results = self.execute_query(query, params)
        
        signals = []
        for row in results:
            signal = dict(row)
            if signal.get('confidence'):
                signal['confidence'] = float(signal['confidence'])
            if signal.get('expected_return'):
                signal['expected_return'] = float(signal['expected_return'])
            signals.append(signal)
        
        return signals
    
    def update_signal_status(self, signal_id: str, status: str, 
                           execution_result: dict = None) -> bool:
        """更新信号状态
        
        Args:
            signal_id: 信号ID
            status: 新状态
            execution_result: 执行结果
            
        Returns:
            是否成功
        """
        query = """
            UPDATE opportunity_signals 
            SET status = %s, execution_result = %s, updated_at = %s
            WHERE id = %s
        """
        
        params = (
            status,
            json.dumps(execution_result) if execution_result else None,
            datetime.now(),
            signal_id
        )
        
        affected = self.execute_update(query, params)
        return affected > 0
    
    def create_trade(self, trade_data: dict) -> Optional[str]:
        """创建机会交易
        
        Args:
            trade_data: 交易数据
            
        Returns:
            交易ID
        """
        query = """
            INSERT INTO opportunity_trades (
                timestamp, position_id, signal_id, trade_direction,
                trade_type, symbol, executed_price, executed_quantity,
                executed_value, commission, slippage, exchange,
                order_id, execution_time_ms, pnl, pnl_percentage,
                status, failure_reason, metadata, executed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                     %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            trade_data.get('timestamp', datetime.now()),
            trade_data.get('position_id'),
            trade_data.get('signal_id'),
            trade_data['trade_direction'],
            trade_data['trade_type'],
            trade_data['symbol'],
            trade_data['executed_price'],
            trade_data['executed_quantity'],
            trade_data['executed_value'],
            trade_data.get('commission'),
            trade_data.get('slippage'),
            trade_data.get('exchange'),
            trade_data.get('order_id'),
            trade_data.get('execution_time_ms'),
            trade_data.get('pnl'),
            trade_data.get('pnl_percentage'),
            trade_data['status'],
            trade_data.get('failure_reason'),
            json.dumps(trade_data.get('metadata', {})),
            trade_data.get('executed_at')
        )
        
        return self.execute_insert(query, params)
    
    def get_position_trades(self, position_id: str) -> List[Dict]:
        """获取仓位相关交易
        
        Args:
            position_id: 仓位ID
            
        Returns:
            交易列表
        """
        query = """
            SELECT * FROM opportunity_trades 
            WHERE position_id = %s
            ORDER BY timestamp DESC
        """
        
        results = self.execute_query(query, (position_id,))
        
        trades = []
        for row in results:
            trade = dict(row)
            # 转换Decimal
            for key in ['executed_price', 'executed_quantity', 
                       'executed_value', 'commission', 'pnl']:
                if trade.get(key):
                    trade[key] = float(trade[key])
            trades.append(trade)
        
        return trades
    
    def calculate_position_pnl(self, position_id: str, 
                              current_price: float) -> Dict[str, float]:
        """计算仓位盈亏
        
        Args:
            position_id: 仓位ID
            current_price: 当前价格
            
        Returns:
            盈亏信息
        """
        position = self.get_position(position_id)
        if not position:
            return None
        
        entry_price = position['entry_price']
        position_size = position['position_size']
        position_type = position['position_type']
        leverage = position.get('leverage', 1.0)
        
        # 计算未实现盈亏
        if position_type == 'long':
            unrealized_pnl = (current_price - entry_price) * position_size * leverage
            unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100 * leverage
        else:  # short
            unrealized_pnl = (entry_price - current_price) * position_size * leverage
            unrealized_pnl_pct = ((entry_price - current_price) / entry_price) * 100 * leverage
        
        # 更新数据库
        self.update_position(position_id, {
            'current_price': current_price,
            'unrealized_pnl': unrealized_pnl
        })
        
        return {
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_percentage': unrealized_pnl_pct,
            'current_price': current_price,
            'entry_price': entry_price,
            'position_size': position_size,
            'leverage': leverage
        }
    
    def close_position(self, position_id: str, close_price: float, 
                      close_reason: str = None) -> bool:
        """关闭仓位
        
        Args:
            position_id: 仓位ID
            close_price: 关闭价格
            close_reason: 关闭原因
            
        Returns:
            是否成功
        """
        # 计算最终盈亏
        pnl_info = self.calculate_position_pnl(position_id, close_price)
        if not pnl_info:
            return False
        
        # 更新仓位状态
        updates = {
            'status': 'closed',
            'current_price': close_price,
            'realized_pnl': pnl_info['unrealized_pnl'],
            'closed_at': datetime.now()
        }
        
        if close_reason:
            position = self.get_position(position_id)
            metadata = position.get('metadata', {})
            metadata['close_reason'] = close_reason
            updates['metadata'] = json.dumps(metadata)
        
        return self.update_position(position_id, updates)
    
    def get_performance_stats(self, start_time: datetime = None, 
                            end_time: datetime = None) -> Dict:
        """获取绩效统计
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息
        """
        if not start_time:
            start_time = datetime.now().replace(hour=0, minute=0, second=0)
        if not end_time:
            end_time = datetime.now()
        
        query = """
            SELECT 
                COUNT(*) as total_positions,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_positions,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_positions,
                SUM(CASE WHEN status = 'closed' THEN realized_pnl ELSE 0 END) as total_pnl,
                AVG(CASE WHEN status = 'closed' THEN realized_pnl ELSE NULL END) as avg_pnl,
                COUNT(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN status = 'closed' AND realized_pnl < 0 THEN 1 END) as losing_trades
            FROM opportunity_positions
            WHERE timestamp BETWEEN %s AND %s
        """
        
        results = self.execute_query(query, (start_time, end_time))
        
        if results:
            stats = dict(results[0])
            # 计算胜率
            total_closed = stats.get('closed_positions', 0)
            if total_closed > 0:
                stats['win_rate'] = stats.get('winning_trades', 0) / total_closed
            else:
                stats['win_rate'] = 0
            
            # 转换Decimal
            for key in ['total_pnl', 'avg_pnl']:
                if stats.get(key):
                    stats[key] = float(stats[key])
            
            return stats
        
        return {}