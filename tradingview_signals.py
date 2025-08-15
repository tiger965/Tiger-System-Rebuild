#!/usr/bin/env python3
"""
TradingView信号集成方案
通过Webhook接收TradingView的交易信号和警报
"""

from flask import Flask, request, jsonify
import json
import yaml
from datetime import datetime
from pathlib import Path
import logging

class TradingViewSignalReceiver:
    """
    TradingView信号接收器
    
    TradingView能提供什么：
    1. Pine Script策略生成的交易信号
    2. 技术指标触发的警报
    3. 价格突破警报
    4. 自定义条件警报
    
    如何集成：
    - TradingView通过Webhook发送信号到我们的服务器
    - 我们接收并处理这些信号
    - 转换为系统可用的交易指令
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.signals = []
        self.setup_routes()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/tradingview_signals.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_routes(self):
        """设置Webhook接收路由"""
        
        @self.app.route('/webhook/tradingview', methods=['POST'])
        def receive_signal():
            """
            接收TradingView的Webhook信号
            
            TradingView警报消息格式：
            {
                "symbol": "BTCUSDT",
                "action": "buy/sell",
                "price": "43500",
                "strategy": "MA_Cross",
                "message": "Golden Cross detected",
                "time": "{{timenow}}"
            }
            """
            try:
                data = request.json
                
                # 解析信号
                signal = self.parse_signal(data)
                
                # 保存信号
                self.signals.append(signal)
                self.save_signal(signal)
                
                # 处理信号
                self.process_signal(signal)
                
                self.logger.info(f"收到信号: {signal}")
                
                return jsonify({'status': 'success'}), 200
                
            except Exception as e:
                self.logger.error(f"处理信号失败: {e}")
                return jsonify({'error': str(e)}), 400
    
    def parse_signal(self, data):
        """解析TradingView信号"""
        return {
            'timestamp': datetime.now().isoformat(),
            'symbol': data.get('symbol', 'BTCUSDT'),
            'action': data.get('action', 'alert'),
            'price': float(data.get('price', 0)),
            'strategy': data.get('strategy', 'unknown'),
            'message': data.get('message', ''),
            'raw_data': data
        }
    
    def process_signal(self, signal):
        """处理信号"""
        # 这里可以：
        # 1. 发送到Telegram通知
        # 2. 触发自动交易
        # 3. 更新数据库
        # 4. 执行风控检查
        
        if signal['action'] == 'buy':
            self.handle_buy_signal(signal)
        elif signal['action'] == 'sell':
            self.handle_sell_signal(signal)
        else:
            self.handle_alert(signal)
    
    def handle_buy_signal(self, signal):
        """处理买入信号"""
        print(f"🟢 买入信号: {signal['symbol']} @ ${signal['price']}")
        # TODO: 集成到交易系统
    
    def handle_sell_signal(self, signal):
        """处理卖出信号"""
        print(f"🔴 卖出信号: {signal['symbol']} @ ${signal['price']}")
        # TODO: 集成到交易系统
    
    def handle_alert(self, signal):
        """处理警报"""
        print(f"⚠️ 警报: {signal['message']}")
        # TODO: 发送通知
    
    def save_signal(self, signal):
        """保存信号到文件"""
        signals_dir = Path("data/signals")
        signals_dir.mkdir(parents=True, exist_ok=True)
        
        # 按日期保存
        date_str = datetime.now().strftime("%Y%m%d")
        filename = signals_dir / f"signals_{date_str}.json"
        
        # 追加到文件
        if filename.exists():
            with open(filename, 'r') as f:
                signals = json.load(f)
        else:
            signals = []
        
        signals.append(signal)
        
        with open(filename, 'w') as f:
            json.dump(signals, f, indent=2)
    
    def run(self, port=5000):
        """运行Webhook服务器"""
        print(f"🚀 TradingView信号接收器运行在 http://localhost:{port}")
        print(f"Webhook URL: http://your-server.com:5000/webhook/tradingview")
        self.app.run(host='0.0.0.0', port=port)


def setup_tradingview_alerts():
    """
    设置TradingView警报的说明
    """
    print("""
    ====================================================
    📊 TradingView信号集成指南
    ====================================================
    
    TradingView可以提供的信号：
    -----------------------------
    1. 📈 技术指标信号
       - RSI超买/超卖
       - MACD金叉/死叉
       - 布林带突破
       - 移动平均线交叉
    
    2. 📊 价格行为信号
       - 支撑/阻力突破
       - 趋势线突破
       - 图表形态完成
       - 关键价位触及
    
    3. 🤖 Pine Script策略信号
       - 自定义策略买卖点
       - 量化模型信号
       - 组合条件触发
    
    如何设置（需要Pro订阅 $14.95/月）：
    ------------------------------------
    1. 在TradingView图表上创建警报
    2. 设置条件（指标/价格/策略）
    3. 在"Webhook URL"中填入：
       http://你的服务器:5000/webhook/tradingview
    4. 设置消息格式（JSON）：
       {
         "symbol": "{{ticker}}",
         "action": "buy",
         "price": "{{close}}",
         "strategy": "MA_Cross",
         "message": "{{strategy.order.comment}}"
       }
    
    优势：
    -----
    ✅ 专业的技术分析
    ✅ 丰富的指标库
    ✅ 可视化策略回测
    ✅ 社区策略分享
    ✅ 多时间框架分析
    
    限制：
    -----
    ⚠️ 需要Pro订阅才能使用Webhook
    ⚠️ 每个订阅级别有警报数量限制
    ⚠️ 不能获取历史数据
    ⚠️ 只能发送信号，不能接收数据
    
    是否需要？
    ----------
    如果你：
    • 已经在用TradingView看盘 → 值得集成
    • 需要复杂的技术分析 → 值得集成
    • 只需要价格数据 → 不需要
    • 预算有限 → 可选
    
    替代方案：
    ---------
    我们系统已经实现了：
    • 技术指标计算（TA-Lib）
    • 价格监控（交易所API）
    • 自定义策略（Python）
    • 信号生成（AI模块）
    
    结论：
    -----
    TradingView信号是个"锦上添花"的功能，
    不是必需的，但如果你已经在用TradingView，
    集成它的信号可以增强系统的决策能力。
    """)

if __name__ == "__main__":
    # 显示设置说明
    setup_tradingview_alerts()
    
    # 询问是否启动接收器
    print("\n" + "="*50)
    start = input("是否启动信号接收器? (y/n): ")
    
    if start.lower() == 'y':
        # 检查Flask
        try:
            import flask
        except ImportError:
            print("需要安装Flask: pip install flask")
            exit(1)
        
        # 启动接收器
        receiver = TradingViewSignalReceiver()
        receiver.run()