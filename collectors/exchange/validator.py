"""
数据验证模块
确保数据质量和完整性
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """数据验证器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.validation_stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "failures_by_type": {}
        }
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "max_price_deviation": 0.1,  # 最大价格偏差10%
            "max_time_delay": 5000,  # 最大时间延迟5秒
            "min_price": 0.00000001,  # 最小价格
            "max_price": 10000000,  # 最大价格
            "min_volume": 0,  # 最小成交量
            "max_volume": 1000000000,  # 最大成交量
            "required_ticker_fields": ["symbol", "last_price", "timestamp"],
            "required_depth_fields": ["symbol", "bids", "asks", "timestamp"],
            "required_trade_fields": ["symbol", "price", "size", "timestamp"]
        }
    
    def validate_ticker(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """验证行情数据"""
        try:
            # 检查必需字段
            for field in self.config["required_ticker_fields"]:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 验证价格范围
            price = data.get("last_price", 0)
            if not self._validate_price(price):
                return False, f"价格超出合理范围: {price}"
            
            # 验证时间戳
            if not self._validate_timestamp(data.get("timestamp")):
                return False, "时间戳无效或延迟过大"
            
            # 验证买卖价格逻辑
            bid_price = data.get("bid_price", 0)
            ask_price = data.get("ask_price", 0)
            
            if bid_price > 0 and ask_price > 0:
                if bid_price > ask_price:
                    return False, f"买价({bid_price})高于卖价({ask_price})"
                
                spread = (ask_price - bid_price) / bid_price if bid_price > 0 else 0
                if spread > 0.1:  # 价差超过10%
                    return False, f"买卖价差过大: {spread*100:.2f}%"
            
            # 验证成交量
            volume = data.get("volume_24h", 0)
            if not self._validate_volume(volume):
                return False, f"成交量超出合理范围: {volume}"
            
            self._record_validation(True, "ticker")
            return True, None
            
        except Exception as e:
            self._record_validation(False, "ticker")
            return False, f"验证异常: {str(e)}"
    
    def validate_depth(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """验证深度数据"""
        try:
            # 检查必需字段
            for field in self.config["required_depth_fields"]:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 验证时间戳
            if not self._validate_timestamp(data.get("timestamp")):
                return False, "时间戳无效或延迟过大"
            
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            
            # 验证深度数据不为空
            if not bids or not asks:
                return False, "深度数据为空"
            
            # 验证买单价格递减
            prev_price = float('inf')
            for bid in bids:
                price = bid.get("price", 0)
                if not self._validate_price(price):
                    return False, f"买单价格无效: {price}"
                if price >= prev_price:
                    return False, "买单价格未按递减排序"
                prev_price = price
            
            # 验证卖单价格递增
            prev_price = 0
            for ask in asks:
                price = ask.get("price", 0)
                if not self._validate_price(price):
                    return False, f"卖单价格无效: {price}"
                if price <= prev_price:
                    return False, "卖单价格未按递增排序"
                prev_price = price
            
            # 验证买一价低于卖一价
            best_bid = bids[0].get("price", 0)
            best_ask = asks[0].get("price", 0)
            
            if best_bid >= best_ask:
                return False, f"买一价({best_bid})不低于卖一价({best_ask})"
            
            self._record_validation(True, "depth")
            return True, None
            
        except Exception as e:
            self._record_validation(False, "depth")
            return False, f"验证异常: {str(e)}"
    
    def validate_trade(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """验证成交数据"""
        try:
            # 检查必需字段
            for field in self.config["required_trade_fields"]:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
            
            # 验证价格
            price = data.get("price", 0)
            if not self._validate_price(price):
                return False, f"价格超出合理范围: {price}"
            
            # 验证数量
            size = data.get("size", 0)
            if not self._validate_volume(size):
                return False, f"数量超出合理范围: {size}"
            
            # 验证时间戳
            if not self._validate_timestamp(data.get("timestamp")):
                return False, "时间戳无效或延迟过大"
            
            # 验证交易方向
            side = data.get("side", "").lower()
            if side not in ["buy", "sell", ""]:
                return False, f"无效的交易方向: {side}"
            
            self._record_validation(True, "trade")
            return True, None
            
        except Exception as e:
            self._record_validation(False, "trade")
            return False, f"验证异常: {str(e)}"
    
    def validate_funding_rate(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """验证资金费率"""
        try:
            # 检查必需字段
            if "funding_rate" not in data:
                return False, "缺少资金费率字段"
            
            funding_rate = data.get("funding_rate", 0)
            
            # 验证资金费率范围（通常在-0.01到0.01之间）
            if abs(funding_rate) > 0.01:
                return False, f"资金费率异常: {funding_rate}"
            
            # 验证时间戳
            funding_time = data.get("funding_time")
            if funding_time:
                if not isinstance(funding_time, datetime):
                    return False, "资金费率时间格式错误"
                
                # 验证资金费率时间（应该是8小时的倍数）
                hour = funding_time.hour
                if hour not in [0, 8, 16]:
                    logger.warning(f"资金费率时间不是标准时间: {hour}点")
            
            self._record_validation(True, "funding_rate")
            return True, None
            
        except Exception as e:
            self._record_validation(False, "funding_rate")
            return False, f"验证异常: {str(e)}"
    
    def validate_cross_exchange(self, okx_data: Dict, binance_data: Dict, 
                               max_deviation: float = None) -> Tuple[bool, Optional[str]]:
        """交叉验证不同交易所数据"""
        try:
            max_deviation = max_deviation or self.config["max_price_deviation"]
            
            # 获取价格
            okx_price = okx_data.get("last_price", 0)
            binance_price = binance_data.get("last_price", 0)
            
            if okx_price <= 0 or binance_price <= 0:
                return False, "价格数据无效"
            
            # 计算价差
            price_diff = abs(okx_price - binance_price)
            price_diff_percent = price_diff / min(okx_price, binance_price)
            
            # 验证价差
            if price_diff_percent > max_deviation:
                return False, f"交易所价差过大: {price_diff_percent*100:.2f}%"
            
            # 验证时间差
            okx_time = okx_data.get("timestamp")
            binance_time = binance_data.get("timestamp")
            
            if okx_time and binance_time:
                time_diff = abs((okx_time - binance_time).total_seconds())
                if time_diff > 10:  # 时间差超过10秒
                    return False, f"数据时间差过大: {time_diff}秒"
            
            self._record_validation(True, "cross_exchange")
            return True, None
            
        except Exception as e:
            self._record_validation(False, "cross_exchange")
            return False, f"交叉验证异常: {str(e)}"
    
    def validate_batch(self, data_list: List[Dict], data_type: str) -> List[Dict]:
        """批量验证数据"""
        results = []
        
        for data in data_list:
            if data_type == "ticker":
                valid, error = self.validate_ticker(data)
            elif data_type == "depth":
                valid, error = self.validate_depth(data)
            elif data_type == "trade":
                valid, error = self.validate_trade(data)
            elif data_type == "funding_rate":
                valid, error = self.validate_funding_rate(data)
            else:
                valid, error = False, f"未知的数据类型: {data_type}"
            
            results.append({
                "data": data,
                "valid": valid,
                "error": error
            })
        
        return results
    
    def _validate_price(self, price: float) -> bool:
        """验证价格合理性"""
        return self.config["min_price"] <= price <= self.config["max_price"]
    
    def _validate_volume(self, volume: float) -> bool:
        """验证成交量合理性"""
        return self.config["min_volume"] <= volume <= self.config["max_volume"]
    
    def _validate_timestamp(self, timestamp: Any) -> bool:
        """验证时间戳"""
        if timestamp is None:
            return False
        
        try:
            if isinstance(timestamp, datetime):
                ts = timestamp
            else:
                # 假设是毫秒时间戳
                ts = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            
            # 检查时间延迟
            now = datetime.now(timezone.utc)
            delay = abs((now - ts).total_seconds() * 1000)
            
            return delay <= self.config["max_time_delay"]
            
        except Exception:
            return False
    
    def _record_validation(self, success: bool, data_type: str):
        """记录验证统计"""
        self.validation_stats["total_validated"] += 1
        
        if success:
            self.validation_stats["passed"] += 1
        else:
            self.validation_stats["failed"] += 1
            
            if data_type not in self.validation_stats["failures_by_type"]:
                self.validation_stats["failures_by_type"][data_type] = 0
            self.validation_stats["failures_by_type"][data_type] += 1
    
    def get_stats(self) -> Dict:
        """获取验证统计"""
        stats = self.validation_stats.copy()
        
        if stats["total_validated"] > 0:
            stats["pass_rate"] = stats["passed"] / stats["total_validated"] * 100
            stats["fail_rate"] = stats["failed"] / stats["total_validated"] * 100
        else:
            stats["pass_rate"] = 0
            stats["fail_rate"] = 0
        
        return stats
    
    def reset_stats(self):
        """重置统计"""
        self.validation_stats = {
            "total_validated": 0,
            "passed": 0,
            "failed": 0,
            "failures_by_type": {}
        }


# 测试函数
def test_validator():
    """测试数据验证器"""
    validator = DataValidator()
    
    # 测试有效的行情数据
    print("测试行情数据验证...")
    ticker = {
        "symbol": "BTCUSDT",
        "last_price": 67500.5,
        "bid_price": 67500.0,
        "bid_size": 2.0,
        "ask_price": 67501.0,
        "ask_size": 1.5,
        "volume_24h": 5432.1,
        "timestamp": datetime.now(timezone.utc)
    }
    
    valid, error = validator.validate_ticker(ticker)
    print(f"行情数据验证: {'通过' if valid else '失败'}, 错误: {error}")
    
    # 测试无效的行情数据
    invalid_ticker = ticker.copy()
    invalid_ticker["bid_price"] = 68000  # 买价高于卖价
    
    valid, error = validator.validate_ticker(invalid_ticker)
    print(f"无效行情验证: {'通过' if valid else '失败'}, 错误: {error}")
    
    # 测试深度数据
    print("\n测试深度数据验证...")
    depth = {
        "symbol": "BTCUSDT",
        "bids": [
            {"price": 67500.0, "size": 2.0},
            {"price": 67499.0, "size": 1.8},
            {"price": 67498.0, "size": 3.2}
        ],
        "asks": [
            {"price": 67501.0, "size": 1.5},
            {"price": 67502.0, "size": 2.0},
            {"price": 67503.0, "size": 1.75}
        ],
        "timestamp": datetime.now(timezone.utc)
    }
    
    valid, error = validator.validate_depth(depth)
    print(f"深度数据验证: {'通过' if valid else '失败'}, 错误: {error}")
    
    # 测试成交数据
    print("\n测试成交数据验证...")
    trade = {
        "symbol": "BTCUSDT",
        "trade_id": "123456",
        "price": 67500.5,
        "size": 0.5,
        "side": "buy",
        "timestamp": datetime.now(timezone.utc)
    }
    
    valid, error = validator.validate_trade(trade)
    print(f"成交数据验证: {'通过' if valid else '失败'}, 错误: {error}")
    
    # 测试交叉验证
    print("\n测试交叉验证...")
    okx_data = {
        "last_price": 67500.0,
        "timestamp": datetime.now(timezone.utc)
    }
    binance_data = {
        "last_price": 67510.0,
        "timestamp": datetime.now(timezone.utc)
    }
    
    valid, error = validator.validate_cross_exchange(okx_data, binance_data)
    print(f"交叉验证: {'通过' if valid else '失败'}, 错误: {error}")
    
    # 获取统计信息
    stats = validator.get_stats()
    print(f"\n验证统计: {stats}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_validator()