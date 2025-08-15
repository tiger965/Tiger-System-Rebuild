#!/usr/bin/env python3
"""
Window 8 启动脚本
一键启动纯通知执行工具
"""

import sys
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config_manager import ConfigManager


def setup_logging():
    """设置日志"""
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"window8_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'fastapi', 'uvicorn', 'aiohttp', 'aiofiles', 
        'rich', 'jinja2', 'pandas', 'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def check_config():
    """检查配置文件"""
    config_path = current_dir / "config" / "window8.json"
    
    if not config_path.exists():
        print("📋 配置文件不存在，创建默认配置...")
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        print(f"✅ 已创建配置文件: {config_path}")
        print("📝 请根据需要修改配置文件中的设置")
        return True
    
    # 验证配置
    config_manager = ConfigManager(str(config_path))
    validation = config_manager.validate_config()
    
    if not validation["valid"]:
        print("❌ 配置文件验证失败:")
        for error in validation["errors"]:
            print(f"   - {error}")
        return False
    
    if validation["warnings"]:
        print("⚠️ 配置警告:")
        for warning in validation["warnings"]:
            print(f"   - {warning}")
    
    print("✅ 配置文件验证通过")
    return True


def check_external_tools():
    """检查外部工具"""
    print("🔧 检查外部工具依赖...")
    
    # 检查wkhtmltopdf（PDF生成需要）
    try:
        import pdfkit
        pdfkit.configuration()
        print("✅ PDF生成工具可用")
    except Exception as e:
        print("⚠️ PDF生成工具不可用，可能需要安装wkhtmltopdf")
        print("Ubuntu: sudo apt-get install wkhtmltopdf")
        print("macOS: brew install wkhtmltopdf")
        print("Windows: 从官网下载安装包")


async def test_basic_functions():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    try:
        # 测试终端显示
        from terminal_display import TerminalDisplay
        terminal = TerminalDisplay()
        result = terminal.print_message("Window 8 启动测试", color="green")
        if result["status"] == "success":
            print("✅ 终端显示功能正常")
        
        # 测试配置管理
        config_path = current_dir / "config" / "window8.json"
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        print(f"✅ 配置管理功能正常 ({len(config)} 个配置项)")
        
        # 测试报告生成
        import tempfile
        from report_generator_pure import ReportGenerator
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = ReportGenerator(tmp_dir)
            result = generator.generate_daily_report({"测试": "数据"})
            if result["status"] == "success":
                print("✅ 报告生成功能正常")
        
        print("🎉 基本功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False


def show_startup_info():
    """显示启动信息"""
    print("=" * 60)
    print("🚀 Window 8 - 纯通知执行工具")
    print("=" * 60)
    print("📌 核心功能:")
    print("   • Telegram消息发送")
    print("   • 邮件通知发送")
    print("   • 终端彩色显示")
    print("   • 报告生成 (HTML/PDF)")
    print("   • RESTful API接口")
    print("")
    print("🔗 API端点:")
    print("   • POST /notify - 发送通知")
    print("   • POST /generate_report - 生成报告")
    print("   • POST /batch - 批量执行")
    print("   • GET /stats - 获取统计")
    print("   • GET /health - 健康检查")
    print("")
    print("📖 文档: http://localhost:8008/docs")
    print("=" * 60)


def main():
    """主函数"""
    show_startup_info()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔍 环境检查...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    print(f"✅ Python版本: {sys.version}")
    
    # 检查依赖
    if not check_dependencies():
        return False
    print("✅ 依赖包检查完成")
    
    # 检查配置
    if not check_config():
        return False
    
    # 检查外部工具
    check_external_tools()
    
    # 测试基本功能
    if not asyncio.run(test_basic_functions()):
        print("❌ 基本功能测试失败")
        return False
    
    print("\n🎯 启动Window 8服务...")
    
    try:
        # 启动服务
        import uvicorn
        from main import app
        
        # 读取配置中的服务器设置
        config_path = current_dir / "config" / "window8.json"
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        
        api_config = config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8008)
        log_level = api_config.get("log_level", "info")
        
        logger.info(f"启动Window 8服务 - http://{host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=False  # 生产环境不启用重载
        )
        
    except KeyboardInterrupt:
        print("\n👋 Window 8服务已停止")
        logger.info("Window 8服务被用户中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        logger.error(f"启动Window 8服务失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)