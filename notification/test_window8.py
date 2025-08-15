"""
Window 8 通知工具测试用例
测试所有组件的功能
"""

import asyncio
import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from telegram_notifier import TelegramNotifier
from email_notifier import EmailNotifier
from terminal_display import TerminalDisplay
from report_generator_pure import ReportGenerator
from config_manager import ConfigManager
from main import Window8Notifier


class TestTelegramNotifier:
    """测试Telegram通知器"""
    
    @pytest.fixture
    def notifier(self):
        return TelegramNotifier("test_token", "test_chat_id")
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, notifier):
        """测试发送消息成功"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                "ok": True,
                "result": {"message_id": 123}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await notifier.send_message("测试消息")
            
            assert result["status"] == "success"
            assert result["channel"] == "telegram"
            assert result["type"] == "message"
            assert "elapsed_ms" in result
    
    @pytest.mark.asyncio
    async def test_send_message_failed(self, notifier):
        """测试发送消息失败"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                "ok": False,
                "description": "Bad Request"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await notifier.send_message("测试消息")
            
            assert result["status"] == "failed"
            assert "Bad Request" in result["error"]
    
    @pytest.mark.asyncio
    async def test_send_photo(self, notifier):
        """测试发送图片"""
        # 创建临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b'fake image data')
            tmp_path = tmp_file.name
        
        try:
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = Mock()
                mock_response.json = AsyncMock(return_value={
                    "ok": True,
                    "result": {"message_id": 124}
                })
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await notifier.send_photo(tmp_path, "测试图片")
                
                assert result["status"] == "success"
                assert result["type"] == "photo"
        finally:
            Path(tmp_path).unlink()
    
    def test_get_stats(self, notifier):
        """测试获取统计"""
        stats = notifier.get_stats()
        
        assert "total_sent" in stats
        assert "messages" in stats
        assert "photos" in stats
        assert "documents" in stats
        assert "success_rate" in stats


class TestEmailNotifier:
    """测试邮件通知器"""
    
    @pytest.fixture
    def notifier(self):
        return EmailNotifier(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="password",
            use_tls=True
        )
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, notifier):
        """测试发送邮件成功"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await notifier.send_email(
                to="recipient@test.com",
                subject="测试邮件",
                body="这是测试邮件内容"
            )
            
            assert result["status"] == "success"
            assert result["channel"] == "email"
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_html_email(self, notifier):
        """测试发送HTML邮件"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await notifier.send_html_email(
                to="recipient@test.com",
                subject="测试HTML邮件",
                html="<h1>这是HTML邮件</h1>"
            )
            
            assert result["status"] == "success"
            assert result["type"] == "html"
    
    def test_get_stats(self, notifier):
        """测试获取统计"""
        stats = notifier.get_stats()
        
        assert "total_sent" in stats
        assert "plain_emails" in stats
        assert "html_emails" in stats
        assert "success_rate" in stats


class TestTerminalDisplay:
    """测试终端显示器"""
    
    @pytest.fixture
    def display(self):
        return TerminalDisplay(use_color=True)
    
    def test_print_message(self, display):
        """测试打印消息"""
        result = display.print_message("测试消息", color="blue")
        
        assert result["status"] == "success"
        assert result["channel"] == "terminal"
        assert result["type"] == "message"
    
    def test_print_table(self, display):
        """测试打印表格"""
        data = [
            {"姓名": "张三", "年龄": 25, "城市": "北京"},
            {"姓名": "李四", "年龄": 30, "城市": "上海"}
        ]
        
        result = display.print_table(data, title="用户信息表")
        
        assert result["status"] == "success"
        assert result["type"] == "table"
        assert result["rows"] == 2
        assert result["columns"] == 3
    
    def test_print_panel(self, display):
        """测试打印面板"""
        result = display.print_panel(
            "这是面板内容",
            title="测试面板",
            border_style="green"
        )
        
        assert result["status"] == "success"
        assert result["type"] == "panel"
    
    def test_print_chart(self, display):
        """测试打印图表"""
        data = [1.0, 2.5, 1.8, 3.2, 2.1, 4.0]
        
        result = display.print_chart(
            data,
            title="测试图表",
            chart_type="line"
        )
        
        assert result["status"] == "success"
        assert result["type"] == "chart"
        assert result["data_points"] == 6
    
    def test_get_stats(self, display):
        """测试获取统计"""
        stats = display.get_stats()
        
        assert "messages" in stats
        assert "tables" in stats
        assert "panels" in stats
        assert "charts" in stats


class TestReportGenerator:
    """测试报告生成器"""
    
    @pytest.fixture
    def generator(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield ReportGenerator(output_dir=tmp_dir)
    
    def test_generate_daily_report_html(self, generator):
        """测试生成HTML日报"""
        data = {
            "总览": {
                "总交易数": 25,
                "盈利交易": 15,
                "亏损交易": 10,
                "总盈亏": 1250.50
            },
            "市场数据": [
                {"交易对": "BTC/USDT", "价格": 45000, "涨跌": "+2.5%"},
                {"交易对": "ETH/USDT", "价格": 3200, "涨跌": "+1.8%"}
            ]
        }
        
        result = generator.generate_daily_report(data, format="html")
        
        assert result["status"] == "success"
        assert result["type"] == "daily_report"
        assert result["format"] == "html"
        assert Path(result["filepath"]).exists()
    
    def test_generate_trade_report(self, generator):
        """测试生成交易报告"""
        trades = [
            {
                "time": "2024-01-01 10:00:00",
                "symbol": "BTC/USDT",
                "side": "买入",
                "quantity": 0.1,
                "price": 45000,
                "profit": 100.50,
                "status": "已成交"
            },
            {
                "time": "2024-01-01 11:00:00", 
                "symbol": "ETH/USDT",
                "side": "卖出",
                "quantity": 1.0,
                "price": 3200,
                "profit": -50.25,
                "status": "已成交"
            }
        ]
        
        result = generator.generate_trade_report(trades, format="html")
        
        assert result["status"] == "success"
        assert result["type"] == "trade_report"
        assert result["trades_count"] == 2
        assert Path(result["filepath"]).exists()
    
    def test_get_stats(self, generator):
        """测试获取统计"""
        stats = generator.get_stats()
        
        assert "total_reports" in stats
        assert "daily_reports" in stats
        assert "trade_reports" in stats
        assert "success_rate" in stats


class TestConfigManager:
    """测试配置管理器"""
    
    @pytest.fixture
    def config_manager(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.json"
            yield ConfigManager(str(config_path))
    
    def test_load_default_config(self, config_manager):
        """测试加载默认配置"""
        config = config_manager.get_config()
        
        assert "version" in config
        assert "channels" in config
        assert "telegram" in config["channels"]
        assert "email" in config["channels"]
        assert "terminal" in config["channels"]
    
    def test_update_config(self, config_manager):
        """测试更新配置"""
        updates = {
            "channels": {
                "telegram": {
                    "enabled": True,
                    "bot_token": "new_token"
                }
            }
        }
        
        success = config_manager.update_config(updates)
        assert success
        
        config = config_manager.get_config()
        assert config["channels"]["telegram"]["enabled"] is True
        assert config["channels"]["telegram"]["bot_token"] == "new_token"
    
    def test_validate_config(self, config_manager):
        """测试配置验证"""
        result = config_manager.validate_config()
        
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_backup_and_restore(self, config_manager):
        """测试配置备份和恢复"""
        # 修改配置
        config_manager.update_config({"test_field": "test_value"})
        
        # 备份
        backup_path = config_manager.backup_config()
        assert Path(backup_path).exists()
        
        # 重置配置
        config_manager.reset_to_default()
        config = config_manager.get_config()
        assert "test_field" not in config
        
        # 恢复配置
        success = config_manager.restore_config(backup_path)
        assert success
        
        config = config_manager.get_config()
        assert config["test_field"] == "test_value"


class TestWindow8Integration:
    """测试Window 8集成"""
    
    @pytest.fixture
    async def window8(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.json"
            
            # 创建测试配置
            test_config = {
                "channels": {
                    "telegram": {"enabled": False},
                    "email": {"enabled": False},
                    "terminal": {"enabled": True, "colored_output": True}
                },
                "reports": {"output_dir": str(Path(tmp_dir) / "reports")}
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(test_config, f)
            
            notifier = Window8Notifier(str(config_path))
            yield notifier
    
    @pytest.mark.asyncio
    async def test_execute_terminal_notify(self, window8):
        """测试执行终端通知"""
        from main import NotifyCommand
        
        command = NotifyCommand(
            channel="terminal",
            message="这是测试通知消息"
        )
        
        result = await window8.execute_notify(command)
        
        assert result["status"] == "success"
        assert result["channel"] == "terminal"
        assert len(result["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_daily_report(self, window8):
        """测试执行日报生成"""
        from main import ReportCommand
        
        command = ReportCommand(
            report_type="daily",
            data={
                "交易概况": {"总交易": 10, "盈利": 6, "亏损": 4},
                "市场数据": [{"币种": "BTC", "价格": 45000}]
            },
            format="html"
        )
        
        result = await window8.execute_report(command)
        
        assert result["status"] == "success"
        assert result["type"] == "daily_report"
        assert Path(result["filepath"]).exists()
    
    @pytest.mark.asyncio
    async def test_execute_batch_commands(self, window8):
        """测试执行批量命令"""
        from main import BatchCommand
        
        commands = [
            {
                "action": "notify",
                "channel": "terminal",
                "message": "批量消息1"
            },
            {
                "action": "notify", 
                "channel": "terminal",
                "message": "批量消息2"
            }
        ]
        
        batch_command = BatchCommand(commands=commands)
        results = await window8.execute_batch(batch_command)
        
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)
    
    def test_get_stats(self, window8):
        """测试获取统计信息"""
        stats = window8.get_stats()
        
        assert "overall" in stats
        assert "components" in stats
        assert "uptime" in stats


def test_notification_flow():
    """测试完整通知流程"""
    
    async def run_test():
        # 创建临时配置
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "flow_test.json"
            
            test_config = {
                "channels": {
                    "terminal": {"enabled": True, "colored_output": True}
                },
                "reports": {"output_dir": str(Path(tmp_dir) / "reports")}
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(test_config, f)
            
            # 初始化Window 8
            window8 = Window8Notifier(str(config_path))
            
            # 测试通知
            from main import NotifyCommand
            notify_result = await window8.execute_notify(
                NotifyCommand(channel="terminal", message="流程测试消息")
            )
            assert notify_result["status"] == "success"
            
            # 测试报告
            from main import ReportCommand
            report_result = await window8.execute_report(
                ReportCommand(
                    report_type="daily",
                    data={"测试": "数据"},
                    format="html"
                )
            )
            assert report_result["status"] == "success"
            
            # 验证文件生成
            assert Path(report_result["filepath"]).exists()
            
            # 获取统计
            stats = window8.get_stats()
            assert stats["overall"]["total_commands"] == 0  # 因为这些不通过API计数
    
    asyncio.run(run_test())


if __name__ == "__main__":
    # 运行基本测试
    print("🧪 开始Window 8组件测试...")
    
    # 测试配置管理器
    print("📋 测试配置管理器...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test.json"
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        validation = config_manager.validate_config()
        print(f"   ✓ 配置加载: {len(config)} 个配置项")
        print(f"   ✓ 配置验证: {'有效' if validation['valid'] else '无效'}")
    
    # 测试终端显示
    print("🖥️  测试终端显示...")
    terminal = TerminalDisplay()
    result1 = terminal.print_message("测试消息", color="green")
    result2 = terminal.print_table([
        {"项目": "测试1", "状态": "成功"},
        {"项目": "测试2", "状态": "成功"}
    ], title="测试表格")
    print(f"   ✓ 消息打印: {result1['status']}")
    print(f"   ✓ 表格打印: {result2['status']}")
    
    # 测试报告生成
    print("📊 测试报告生成...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        generator = ReportGenerator(tmp_dir)
        result = generator.generate_daily_report({
            "测试数据": {"项目": "Window 8", "状态": "测试通过"}
        })
        print(f"   ✓ 日报生成: {result['status']}")
        if result["status"] == "success":
            print(f"   📄 报告文件: {Path(result['filepath']).name}")
    
    # 测试完整流程
    print("🔄 测试完整流程...")
    test_notification_flow()
    print("   ✓ 完整流程测试通过")
    
    print("\n🎉 所有测试完成！Window 8组件运行正常")
    print("\n📈 性能测试统计:")
    print(f"   📊 终端显示统计: {terminal.get_stats()}")
    
    print("\n✨ Window 8 - 纯通知执行工具测试完毕！")