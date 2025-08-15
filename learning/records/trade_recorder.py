"""
交易记录管理模块
负责完整记录每笔交易，供学习分析使用
"""

import json
import sqlite3
import gzip
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
import pandas as pd

from ..config.config import DATABASE_CONFIG, LOG_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'trade_recorder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TradeEntry:
    """交易入场信息"""
    price: float
    reason: str
    indicators: Dict[str, Any]
    market_state: str
    ai_analysis: Dict[str, Any]
    timestamp: str


@dataclass
class TradeExit:
    """交易出场信息"""
    price: float
    reason: str
    duration: float  # 小时
    pnl: float  # 盈亏
    timestamp: str


@dataclass
class TradeContext:
    """交易上下文"""
    market_trend: str
    volatility: float
    news_events: List[str]
    trader_actions: List[str]


@dataclass
class TradeRecord:
    """完整交易记录"""
    id: str
    timestamp: str
    symbol: str
    direction: str  # long/short
    entry: TradeEntry
    exit: Optional[TradeExit]
    context: TradeContext
    status: str  # open/closed/cancelled


class TradeRecorder:
    """交易记录器"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG["trade_records"]["path"]
        self.backup_path = DATABASE_CONFIG["trade_records"]["backup_path"]
        self.retention_days = DATABASE_CONFIG["trade_records"]["retention_days"]
        
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        Path(self.backup_path).mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        logger.info(f"TradeRecorder initialized with db: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL,
                entry_reason TEXT,
                entry_indicators TEXT,
                entry_market_state TEXT,
                entry_ai_analysis TEXT,
                entry_timestamp TEXT,
                exit_price REAL,
                exit_reason TEXT,
                exit_duration REAL,
                exit_pnl REAL,
                exit_timestamp TEXT,
                context_market_trend TEXT,
                context_volatility REAL,
                context_news_events TEXT,
                context_trader_actions TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON trades(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pnl ON trades(exit_pnl)')
        
        conn.commit()
        conn.close()
    
    def record_trade_entry(self, 
                          symbol: str,
                          direction: str,
                          entry: TradeEntry,
                          context: TradeContext) -> str:
        """记录交易入场"""
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (
                id, timestamp, symbol, direction,
                entry_price, entry_reason, entry_indicators,
                entry_market_state, entry_ai_analysis, entry_timestamp,
                context_market_trend, context_volatility,
                context_news_events, context_trader_actions,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_id,
            datetime.now().isoformat(),
            symbol,
            direction,
            entry.price,
            entry.reason,
            json.dumps(entry.indicators),
            entry.market_state,
            json.dumps(entry.ai_analysis),
            entry.timestamp,
            context.market_trend,
            context.volatility,
            json.dumps(context.news_events),
            json.dumps(context.trader_actions),
            'open'
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded trade entry: {trade_id}")
        return trade_id
    
    def record_trade_exit(self,
                         trade_id: str,
                         exit_info: TradeExit):
        """记录交易出场"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trades SET
                exit_price = ?,
                exit_reason = ?,
                exit_duration = ?,
                exit_pnl = ?,
                exit_timestamp = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            exit_info.price,
            exit_info.reason,
            exit_info.duration,
            exit_info.pnl,
            exit_info.timestamp,
            'closed',
            datetime.now().isoformat(),
            trade_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded trade exit: {trade_id}, PnL: {exit_info.pnl}")
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict]:
        """根据ID获取交易记录"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_trades_by_symbol(self, 
                            symbol: str,
                            status: Optional[str] = None) -> List[Dict]:
        """获取指定币种的交易记录"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                'SELECT * FROM trades WHERE symbol = ? AND status = ? ORDER BY timestamp DESC',
                (symbol, status)
            )
        else:
            cursor.execute(
                'SELECT * FROM trades WHERE symbol = ? ORDER BY timestamp DESC',
                (symbol,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_trades(self, 
                         days: int = 7,
                         status: Optional[str] = None) -> List[Dict]:
        """获取最近的交易记录"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_date = datetime.now().isoformat()
        
        if status:
            cursor.execute('''
                SELECT * FROM trades 
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                AND status = ?
                ORDER BY timestamp DESC
            ''', (days, status))
        else:
            cursor.execute('''
                SELECT * FROM trades 
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            ''', (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def calculate_statistics(self, 
                            symbol: Optional[str] = None,
                            days: Optional[int] = None) -> Dict:
        """计算交易统计信息"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = ["status = 'closed'"]
        params = []
        
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)
        
        if days:
            conditions.append("datetime(timestamp) >= datetime('now', '-' || ? || ' days')")
            params.append(days)
        
        where_clause = " AND ".join(conditions)
        
        # 获取统计数据
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN exit_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN exit_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(exit_pnl) as total_pnl,
                AVG(exit_pnl) as avg_pnl,
                MAX(exit_pnl) as max_profit,
                MIN(exit_pnl) as max_loss,
                AVG(exit_duration) as avg_duration
            FROM trades
            WHERE {where_clause}
        ''', params)
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats[0] == 0:  # 没有交易记录
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "max_profit": 0,
                "max_loss": 0,
                "avg_duration": 0
            }
        
        win_rate = stats[1] / stats[0] if stats[0] > 0 else 0
        
        # 计算盈亏比
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT 
                SUM(CASE WHEN exit_pnl > 0 THEN exit_pnl ELSE 0 END) as total_profit,
                SUM(CASE WHEN exit_pnl < 0 THEN ABS(exit_pnl) ELSE 0 END) as total_loss
            FROM trades
            WHERE {where_clause}
        ''', params)
        
        pnl_stats = cursor.fetchone()
        conn.close()
        
        profit_factor = pnl_stats[0] / pnl_stats[1] if pnl_stats[1] > 0 else float('inf')
        
        return {
            "total_trades": stats[0],
            "winning_trades": stats[1],
            "losing_trades": stats[2],
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_pnl": stats[3],
            "avg_pnl": stats[4],
            "max_profit": stats[5],
            "max_loss": stats[6],
            "avg_duration": stats[7]
        }
    
    def export_to_parquet(self, output_path: Optional[Path] = None) -> Path:
        """导出交易记录到Parquet格式"""
        if output_path is None:
            output_path = self.backup_path / f"trades_{datetime.now().strftime('%Y%m%d')}.parquet"
        
        conn = sqlite3.connect(str(self.db_path))
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
        
        # 压缩并保存
        df.to_parquet(output_path, compression='gzip')
        logger.info(f"Exported {len(df)} trades to {output_path}")
        
        return output_path
    
    def archive_old_trades(self):
        """归档旧交易记录"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 导出旧数据
        cutoff_date = f"datetime('now', '-{self.retention_days} days')"
        
        # 先导出到备份
        old_trades = pd.read_sql_query(
            f"SELECT * FROM trades WHERE datetime(timestamp) < {cutoff_date}",
            conn
        )
        
        if len(old_trades) > 0:
            archive_path = self.backup_path / f"archive_{datetime.now().strftime('%Y%m%d')}.parquet.gz"
            old_trades.to_parquet(archive_path, compression='gzip')
            
            # 删除旧数据
            cursor.execute(f"DELETE FROM trades WHERE datetime(timestamp) < {cutoff_date}")
            conn.commit()
            
            logger.info(f"Archived {len(old_trades)} old trades to {archive_path}")
        
        conn.close()
    
    def cleanup(self):
        """清理资源"""
        logger.info("TradeRecorder cleanup completed")