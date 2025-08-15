"""账户缓存系统 - 7天历史数据缓存"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from collections import deque
import pickle

logger = logging.getLogger(__name__)

class AccountCache:
    """7天账户缓存系统"""
    
    def __init__(self, dal=None):
        """初始化账户缓存
        
        Args:
            dal: 数据访问层实例
        """
        self.dal = dal
        self.cache_prefix = "account_cache:"
        self.cache_ttl = 7 * 24 * 3600  # 7天缓存
        self.memory_cache = {}  # 内存缓存
        self.cache_queue = deque(maxlen=10000)  # 缓存队列
        
    async def get_account_cache(self, user_id: str = "default") -> Dict:
        """获取7天账户缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            账户缓存数据
        """
        try:
            # 先从内存缓存获取
            cache_key = f"{self.cache_prefix}{user_id}"
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_data):
                    logger.info(f"从内存获取账户缓存: {user_id}")
                    return cache_data['data']
            
            # 从Redis获取
            if self.dal:
                redis_data = self.dal.cache_get(cache_key)
                if redis_data:
                    logger.info(f"从Redis获取账户缓存: {user_id}")
                    self.memory_cache[cache_key] = {
                        'data': redis_data,
                        'timestamp': datetime.now()
                    }
                    return redis_data
            
            # 从数据库构建缓存
            account_data = await self._build_account_cache(user_id)
            
            # 存储到缓存
            await self._save_cache(user_id, account_data)
            
            return account_data
            
        except Exception as e:
            logger.error(f"获取账户缓存失败: {e}")
            return self._get_default_account_data()
    
    async def _build_account_cache(self, user_id: str) -> Dict:
        """构建账户缓存数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            账户缓存数据
        """
        try:
            # 获取账户基本信息
            account_info = await self._get_account_info(user_id)
            
            # 获取7天交易历史
            seven_days_ago = datetime.now() - timedelta(days=7)
            trade_history = await self._get_trade_history(user_id, seven_days_ago)
            
            # 获取当前持仓
            positions = await self._get_positions(user_id)
            
            # 计算风险等级
            risk_level = await self._calculate_risk_level(
                account_info, positions, trade_history
            )
            
            # 计算账户统计
            statistics = await self._calculate_statistics(trade_history)
            
            return {
                "user_id": user_id,
                "total_balance": account_info.get('total_balance', 100000),
                "available": account_info.get('available', 70000),
                "frozen": account_info.get('frozen', 30000),
                "positions": positions,
                "last_7d_trades": trade_history,
                "risk_level": risk_level,
                "statistics": statistics,
                "update_time": datetime.now().isoformat(),
                "cache_version": "1.0"
            }
            
        except Exception as e:
            logger.error(f"构建账户缓存失败: {e}")
            return self._get_default_account_data()
    
    async def _get_account_info(self, user_id: str) -> Dict:
        """获取账户基本信息"""
        if not self.dal:
            return {
                'total_balance': 100000,
                'available': 70000,
                'frozen': 30000
            }
        
        try:
            query = """
                SELECT total_balance, available_balance, frozen_balance
                FROM accounts 
                WHERE user_id = %s
                ORDER BY created_at DESC 
                LIMIT 1
            """
            result = self.dal.execute_query(query, (user_id,))
            if result:
                return {
                    'total_balance': float(result[0].get('total_balance', 100000)),
                    'available': float(result[0].get('available_balance', 70000)),
                    'frozen': float(result[0].get('frozen_balance', 30000))
                }
        except:
            pass
            
        return {
            'total_balance': 100000,
            'available': 70000,
            'frozen': 30000
        }
    
    async def _get_trade_history(self, user_id: str, start_date: datetime) -> List[Dict]:
        """获取交易历史"""
        if not self.dal:
            return self._generate_mock_trades()
        
        try:
            query = """
                SELECT * FROM trades 
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at DESC
            """
            results = self.dal.execute_query(query, (user_id, start_date))
            return [dict(r) for r in results] if results else self._generate_mock_trades()
        except:
            return self._generate_mock_trades()
    
    async def _get_positions(self, user_id: str) -> List[Dict]:
        """获取当前持仓"""
        if not self.dal:
            return self._generate_mock_positions()
        
        try:
            query = """
                SELECT * FROM positions 
                WHERE user_id = %s AND status = 'open'
                ORDER BY created_at DESC
            """
            results = self.dal.execute_query(query, (user_id,))
            return [dict(r) for r in results] if results else self._generate_mock_positions()
        except:
            return self._generate_mock_positions()
    
    async def _calculate_risk_level(self, account_info: Dict, 
                                   positions: List[Dict], 
                                   trades: List[Dict]) -> float:
        """计算风险等级
        
        Returns:
            风险等级 (0-1)
        """
        try:
            # 仓位风险
            position_risk = 0.0
            if account_info['total_balance'] > 0:
                total_position_value = sum(
                    p.get('amount', 0) * p.get('current_price', 0) 
                    for p in positions
                )
                position_risk = min(total_position_value / account_info['total_balance'], 1.0)
            
            # 亏损风险
            loss_risk = 0.0
            if trades:
                losses = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]
                if losses:
                    total_loss = abs(sum(losses))
                    loss_risk = min(total_loss / account_info['total_balance'], 1.0)
            
            # 综合风险
            risk_level = position_risk * 0.6 + loss_risk * 0.4
            
            return round(risk_level, 3)
            
        except Exception as e:
            logger.error(f"计算风险等级失败: {e}")
            return 0.3
    
    async def _calculate_statistics(self, trades: List[Dict]) -> Dict:
        """计算账户统计信息"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_pnl': 0.0,
                    'max_win': 0.0,
                    'max_loss': 0.0
                }
            
            pnls = [t.get('pnl', 0) for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            
            return {
                'total_trades': len(trades),
                'win_rate': len(wins) / len(trades) if trades else 0,
                'total_pnl': sum(pnls),
                'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
                'max_win': max(wins) if wins else 0,
                'max_loss': min(losses) if losses else 0,
                'sharpe_ratio': self._calculate_sharpe_ratio(pnls),
                'max_drawdown': self._calculate_max_drawdown(pnls)
            }
            
        except Exception as e:
            logger.error(f"计算统计信息失败: {e}")
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0
            }
    
    def _calculate_sharpe_ratio(self, pnls: List[float]) -> float:
        """计算夏普比率"""
        if not pnls or len(pnls) < 2:
            return 0.0
        
        import numpy as np
        returns = np.array(pnls)
        if returns.std() == 0:
            return 0.0
        
        return round((returns.mean() / returns.std()) * np.sqrt(252), 3)
    
    def _calculate_max_drawdown(self, pnls: List[float]) -> float:
        """计算最大回撤"""
        if not pnls:
            return 0.0
        
        cumulative = []
        cum_sum = 0
        for pnl in pnls:
            cum_sum += pnl
            cumulative.append(cum_sum)
        
        if not cumulative:
            return 0.0
        
        peak = cumulative[0]
        max_dd = 0
        
        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak != 0 else 0
            max_dd = max(max_dd, dd)
        
        return round(max_dd, 4)
    
    async def _save_cache(self, user_id: str, data: Dict):
        """保存缓存"""
        try:
            cache_key = f"{self.cache_prefix}{user_id}"
            
            # 存储到内存
            self.memory_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            # 存储到Redis
            if self.dal:
                self.dal.cache_set(cache_key, data, self.cache_ttl)
            
            # 添加到缓存队列
            self.cache_queue.append({
                'key': cache_key,
                'timestamp': datetime.now()
            })
            
            logger.info(f"账户缓存已保存: {user_id}")
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    async def update_cache(self, user_id: str, update_data: Dict):
        """更新缓存
        
        Args:
            user_id: 用户ID
            update_data: 更新数据
        """
        try:
            # 获取现有缓存
            current_cache = await self.get_account_cache(user_id)
            
            # 合并更新
            current_cache.update(update_data)
            current_cache['update_time'] = datetime.now().isoformat()
            
            # 保存更新后的缓存
            await self._save_cache(user_id, current_cache)
            
            logger.info(f"账户缓存已更新: {user_id}")
            
        except Exception as e:
            logger.error(f"更新缓存失败: {e}")
    
    async def invalidate_cache(self, user_id: str):
        """失效缓存
        
        Args:
            user_id: 用户ID
        """
        try:
            cache_key = f"{self.cache_prefix}{user_id}"
            
            # 删除内存缓存
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # 删除Redis缓存
            if self.dal and self.dal.redis_conn:
                self.dal.redis_conn.delete(cache_key)
            
            logger.info(f"账户缓存已失效: {user_id}")
            
        except Exception as e:
            logger.error(f"失效缓存失败: {e}")
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_data or 'timestamp' not in cache_data:
            return False
        
        # 检查缓存时间
        cache_time = cache_data['timestamp']
        if isinstance(cache_time, str):
            cache_time = datetime.fromisoformat(cache_time)
        
        # 缓存超过1小时认为需要更新
        if datetime.now() - cache_time > timedelta(hours=1):
            return False
        
        return True
    
    def _get_default_account_data(self) -> Dict:
        """获取默认账户数据"""
        return {
            "user_id": "default",
            "total_balance": 100000,
            "available": 70000,
            "frozen": 30000,
            "positions": [],
            "last_7d_trades": [],
            "risk_level": 0.3,
            "statistics": {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0
            },
            "update_time": datetime.now().isoformat(),
            "cache_version": "1.0"
        }
    
    def _generate_mock_trades(self) -> List[Dict]:
        """生成模拟交易数据"""
        trades = []
        for i in range(10):
            trades.append({
                'id': f'trade_{i}',
                'symbol': 'BTCUSDT',
                'side': 'buy' if i % 2 == 0 else 'sell',
                'price': 50000 + i * 100,
                'amount': 0.01,
                'pnl': (i - 5) * 100,
                'created_at': (datetime.now() - timedelta(days=i)).isoformat()
            })
        return trades
    
    def _generate_mock_positions(self) -> List[Dict]:
        """生成模拟持仓数据"""
        return [
            {
                'id': 'pos_1',
                'symbol': 'BTCUSDT',
                'side': 'long',
                'amount': 0.1,
                'entry_price': 50000,
                'current_price': 51000,
                'pnl': 100,
                'status': 'open'
            },
            {
                'id': 'pos_2',
                'symbol': 'ETHUSDT',
                'side': 'long',
                'amount': 1.0,
                'entry_price': 3000,
                'current_price': 3050,
                'pnl': 50,
                'status': 'open'
            }
        ]
    
    async def cleanup_old_cache(self):
        """清理过期缓存"""
        try:
            logger.info("开始清理过期缓存")
            
            # 清理内存缓存
            expired_keys = []
            for key, data in self.memory_cache.items():
                if not self._is_cache_valid(data):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            logger.info(f"已清理 {len(expired_keys)} 个过期缓存")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")