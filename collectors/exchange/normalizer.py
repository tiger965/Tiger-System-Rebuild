"""
数据标准化处理模块
统一不同交易所的数据格式
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DataNormalizer:
    """数据标准化器"""
    
    @staticmethod
    def normalize_ticker(data: Dict, source: str) -> Dict:
        """标准化行情数据"""
        try:
            if source == "OKX":
                return DataNormalizer._normalize_okx_ticker(data)
            elif source == "Binance":
                return DataNormalizer._normalize_binance_ticker(data)
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化行情数据失败: {e}")
            raise
    
    @staticmethod
    def _normalize_okx_ticker(data: Dict) -> Dict:
        """标准化OKX行情数据"""
        return {
            "symbol": data.get("instId", "").replace("-", ""),  # BTC-USDT -> BTCUSDT
            "last_price": float(data.get("last", 0)),
            "bid_price": float(data.get("bidPx", 0)),
            "bid_size": float(data.get("bidSz", 0)),
            "ask_price": float(data.get("askPx", 0)),
            "ask_size": float(data.get("askSz", 0)),
            "open_24h": float(data.get("open24h", 0)),
            "high_24h": float(data.get("high24h", 0)),
            "low_24h": float(data.get("low24h", 0)),
            "volume_24h": float(data.get("vol24h", 0)),
            "volume_quote_24h": float(data.get("volCcy24h", 0)),
            "timestamp": DataNormalizer._parse_timestamp(data.get("ts")),
            "source": "OKX"
        }
    
    @staticmethod
    def _normalize_binance_ticker(data: Dict) -> Dict:
        """标准化Binance行情数据"""
        return {
            "symbol": data.get("symbol", ""),
            "last_price": float(data.get("lastPrice", 0)),
            "bid_price": float(data.get("bidPrice", 0)),
            "bid_size": float(data.get("bidQty", 0)),
            "ask_price": float(data.get("askPrice", 0)),
            "ask_size": float(data.get("askQty", 0)),
            "open_24h": float(data.get("openPrice", 0)),
            "high_24h": float(data.get("highPrice", 0)),
            "low_24h": float(data.get("lowPrice", 0)),
            "volume_24h": float(data.get("volume", 0)),
            "volume_quote_24h": float(data.get("quoteVolume", 0)),
            "timestamp": DataNormalizer._parse_timestamp(data.get("closeTime")),
            "source": "Binance"
        }
    
    @staticmethod
    def normalize_depth(data: Dict, source: str, symbol: str = None) -> Dict:
        """标准化深度数据"""
        try:
            if source == "OKX":
                return DataNormalizer._normalize_okx_depth(data, symbol)
            elif source == "Binance":
                return DataNormalizer._normalize_binance_depth(data, symbol)
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化深度数据失败: {e}")
            raise
    
    @staticmethod
    def _normalize_okx_depth(data: Dict, symbol: str) -> Dict:
        """标准化OKX深度数据"""
        bids = []
        asks = []
        
        for bid in data.get("bids", []):
            bids.append({
                "price": float(bid[0]),
                "size": float(bid[1]),
                "orders": int(bid[3]) if len(bid) > 3 else 0
            })
        
        for ask in data.get("asks", []):
            asks.append({
                "price": float(ask[0]),
                "size": float(ask[1]),
                "orders": int(ask[3]) if len(ask) > 3 else 0
            })
        
        return {
            "symbol": symbol.replace("-", "") if symbol else "",
            "bids": bids,
            "asks": asks,
            "timestamp": DataNormalizer._parse_timestamp(data.get("ts")),
            "source": "OKX"
        }
    
    @staticmethod
    def _normalize_binance_depth(data: Dict, symbol: str) -> Dict:
        """标准化Binance深度数据"""
        bids = []
        asks = []
        
        for bid in data.get("bids", []):
            bids.append({
                "price": float(bid[0]),
                "size": float(bid[1]),
                "orders": 0  # Binance不提供订单数
            })
        
        for ask in data.get("asks", []):
            asks.append({
                "price": float(ask[0]),
                "size": float(ask[1]),
                "orders": 0
            })
        
        return {
            "symbol": symbol or "",
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now(timezone.utc),
            "update_id": data.get("lastUpdateId", 0),
            "source": "Binance"
        }
    
    @staticmethod
    def normalize_trade(data: Dict, source: str, symbol: str = None) -> Dict:
        """标准化成交数据"""
        try:
            if source == "OKX":
                return DataNormalizer._normalize_okx_trade(data, symbol)
            elif source == "Binance":
                return DataNormalizer._normalize_binance_trade(data, symbol)
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化成交数据失败: {e}")
            raise
    
    @staticmethod
    def _normalize_okx_trade(data: Dict, symbol: str) -> Dict:
        """标准化OKX成交数据"""
        return {
            "symbol": symbol.replace("-", "") if symbol else data.get("instId", "").replace("-", ""),
            "trade_id": data.get("tradeId", ""),
            "price": float(data.get("px", 0)),
            "size": float(data.get("sz", 0)),
            "side": data.get("side", "").lower(),  # buy/sell
            "timestamp": DataNormalizer._parse_timestamp(data.get("ts")),
            "source": "OKX"
        }
    
    @staticmethod
    def _normalize_binance_trade(data: Dict, symbol: str) -> Dict:
        """标准化Binance成交数据"""
        return {
            "symbol": symbol or data.get("s", ""),
            "trade_id": str(data.get("id", "") or data.get("a", "")),
            "price": float(data.get("price", 0) or data.get("p", 0)),
            "size": float(data.get("qty", 0) or data.get("q", 0)),
            "side": "sell" if data.get("isBuyerMaker") or data.get("m") else "buy",
            "timestamp": DataNormalizer._parse_timestamp(data.get("time") or data.get("T")),
            "source": "Binance"
        }
    
    @staticmethod
    def normalize_funding_rate(data: Dict, source: str) -> Dict:
        """标准化资金费率"""
        try:
            if source == "OKX":
                return {
                    "symbol": data.get("instId", "").replace("-", ""),
                    "funding_rate": float(data.get("fundingRate", 0)),
                    "next_funding_rate": float(data.get("nextFundingRate", 0)),
                    "funding_time": DataNormalizer._parse_timestamp(data.get("fundingTime")),
                    "source": "OKX"
                }
            elif source == "Binance":
                return {
                    "symbol": data.get("symbol", ""),
                    "funding_rate": float(data.get("fundingRate", 0)),
                    "next_funding_rate": float(data.get("fundingRate", 0)),  # Binance不提供下次费率
                    "funding_time": DataNormalizer._parse_timestamp(data.get("fundingTime")),
                    "source": "Binance"
                }
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化资金费率失败: {e}")
            raise
    
    @staticmethod
    def normalize_open_interest(data: Dict, source: str) -> Dict:
        """标准化持仓量"""
        try:
            if source == "OKX":
                return {
                    "symbol": data.get("instId", "").replace("-", ""),
                    "open_interest": float(data.get("oi", 0)),
                    "open_interest_value": float(data.get("oiCcy", 0)),
                    "timestamp": DataNormalizer._parse_timestamp(data.get("ts")),
                    "source": "OKX"
                }
            elif source == "Binance":
                return {
                    "symbol": data.get("symbol", ""),
                    "open_interest": float(data.get("openInterest", 0)),
                    "open_interest_value": 0,  # Binance不直接提供价值
                    "timestamp": DataNormalizer._parse_timestamp(data.get("time")),
                    "source": "Binance"
                }
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化持仓量失败: {e}")
            raise
    
    @staticmethod
    def normalize_liquidation(data: Dict, source: str) -> Dict:
        """标准化强平数据"""
        try:
            if source == "OKX":
                return {
                    "symbol": data.get("instId", "").replace("-", ""),
                    "side": data.get("side", "").lower(),
                    "price": float(data.get("px", 0)),
                    "size": float(data.get("sz", 0)),
                    "loss": float(data.get("loss", 0)),
                    "timestamp": DataNormalizer._parse_timestamp(data.get("ts")),
                    "source": "OKX"
                }
            elif source == "Binance":
                return {
                    "symbol": data.get("symbol", ""),
                    "side": data.get("side", "").lower(),
                    "price": float(data.get("price", 0)),
                    "size": float(data.get("origQty", 0)),
                    "loss": 0,  # Binance不提供损失金额
                    "timestamp": DataNormalizer._parse_timestamp(data.get("time")),
                    "source": "Binance"
                }
            else:
                raise ValueError(f"不支持的数据源: {source}")
        except Exception as e:
            logger.error(f"标准化强平数据失败: {e}")
            raise
    
    @staticmethod
    def _parse_timestamp(ts: Any) -> datetime:
        """解析时间戳"""
        if ts is None:
            return datetime.now(timezone.utc)
        
        try:
            # 如果是字符串，尝试转换为数字
            if isinstance(ts, str):
                ts = float(ts)
            
            # 如果是毫秒时间戳
            if ts > 1e10:
                return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            # 如果是秒时间戳
            else:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"解析时间戳失败: {e}, 使用当前时间")
            return datetime.now(timezone.utc)
    
    @staticmethod
    def convert_symbol(symbol: str, from_format: str, to_format: str) -> str:
        """转换交易对格式"""
        if from_format == "OKX" and to_format == "Binance":
            # BTC-USDT -> BTCUSDT
            return symbol.replace("-", "")
        elif from_format == "Binance" and to_format == "OKX":
            # BTCUSDT -> BTC-USDT
            # 简单处理，假设都是USDT交易对
            if "USDT" in symbol:
                base = symbol.replace("USDT", "")
                return f"{base}-USDT"
            elif "BTC" in symbol and symbol.endswith("BTC"):
                base = symbol.replace("BTC", "")
                return f"{base}-BTC"
            else:
                return symbol
        else:
            return symbol
    
    @staticmethod
    def batch_normalize(data_list: List[Dict], data_type: str, source: str) -> List[Dict]:
        """批量标准化数据"""
        normalized = []
        for data in data_list:
            try:
                if data_type == "ticker":
                    normalized.append(DataNormalizer.normalize_ticker(data, source))
                elif data_type == "trade":
                    normalized.append(DataNormalizer.normalize_trade(data, source))
                elif data_type == "funding_rate":
                    normalized.append(DataNormalizer.normalize_funding_rate(data, source))
                elif data_type == "open_interest":
                    normalized.append(DataNormalizer.normalize_open_interest(data, source))
                else:
                    logger.warning(f"未知的数据类型: {data_type}")
            except Exception as e:
                logger.error(f"标准化数据失败: {e}")
                continue
        
        return normalized


# 测试函数
def test_normalizer():
    """测试数据标准化"""
    normalizer = DataNormalizer()
    
    # 测试OKX数据
    okx_ticker = {
        "instId": "BTC-USDT",
        "last": "67500.5",
        "bidPx": "67500.0",
        "bidSz": "2.0",
        "askPx": "67501.0",
        "askSz": "1.5",
        "open24h": "67000.0",
        "high24h": "68000.0",
        "low24h": "66500.0",
        "vol24h": "5432.1",
        "volCcy24h": "365000000",
        "ts": "1704067200000"
    }
    
    normalized = normalizer.normalize_ticker(okx_ticker, "OKX")
    print(f"标准化OKX行情: {normalized}")
    
    # 测试Binance数据
    binance_ticker = {
        "symbol": "BTCUSDT",
        "lastPrice": "67500.50",
        "bidPrice": "67500.00",
        "bidQty": "2.00",
        "askPrice": "67501.00",
        "askQty": "1.50",
        "openPrice": "67000.00",
        "highPrice": "68000.00",
        "lowPrice": "66500.00",
        "volume": "5432.10",
        "quoteVolume": "365000000.00",
        "closeTime": 1704067200000
    }
    
    normalized = normalizer.normalize_ticker(binance_ticker, "Binance")
    print(f"标准化Binance行情: {normalized}")
    
    # 测试符号转换
    symbol = normalizer.convert_symbol("BTC-USDT", "OKX", "Binance")
    print(f"OKX到Binance符号转换: BTC-USDT -> {symbol}")
    
    symbol = normalizer.convert_symbol("BTCUSDT", "Binance", "OKX")
    print(f"Binance到OKX符号转换: BTCUSDT -> {symbol}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_normalizer()