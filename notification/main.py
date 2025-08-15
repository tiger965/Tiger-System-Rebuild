"""
Window 8 - 纯通知执行工具主程序
只负责执行Window 6的通知命令，不做任何判断
"""

import asyncio
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from telegram_notifier import TelegramNotifier
from email_notifier import EmailNotifier  
from terminal_display import TerminalDisplay
from report_generator_pure import ReportGenerator
from config_manager import ConfigManager


# 数据模型
class NotifyCommand(BaseModel):
    """通知命令模型"""
    action: str = "notify"
    channel: str  # telegram/email/terminal/all
    message: str
    format: str = "text"  # text/html/markdown
    attachments: Optional[List[str]] = []
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class ReportCommand(BaseModel):
    """报告生成命令模型"""
    action: str = "generate_report"
    report_type: str  # daily/trade/custom
    data: Dict[str, Any]
    format: str = "html"  # html/pdf/excel/json
    output_filename: Optional[str] = None


class BatchCommand(BaseModel):
    """批量命令模型"""
    action: str = "batch"
    commands: List[Dict[str, Any]]


# 主应用类
class Window8Notifier:
    """Window 8 纯通知执行工具"""
    
    def __init__(self, config_path: str = "config/window8.json"):
        """初始化通知系统"""
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # 初始化各个组件
        self.telegram = None
        self.email = None
        self.terminal = TerminalDisplay(
            use_color=self.config.get("terminal", {}).get("colored_output", True)
        )
        self.report_generator = ReportGenerator(
            output_dir=self.config.get("reports", {}).get("output_dir", "./reports")
        )
        
        # 初始化外部通知器
        self._init_notifiers()
        
        # 执行统计
        self.stats = {
            "total_commands": 0,
            "successful": 0,
            "failed": 0,
            "by_channel": {
                "telegram": 0,
                "email": 0,
                "terminal": 0,
                "all": 0
            },
            "by_type": {
                "notify": 0,
                "report": 0,
                "batch": 0
            }
        }
    
    def _init_notifiers(self):
        """初始化通知器"""
        try:
            # 初始化Telegram
            if self.config.get("channels", {}).get("telegram", {}).get("enabled"):
                telegram_config = self.config["channels"]["telegram"]
                self.telegram = TelegramNotifier(
                    bot_token=telegram_config["bot_token"],
                    chat_id=telegram_config["chat_id"]
                )
                self.logger.info("Telegram通知器初始化成功")
            
            # 初始化邮件
            if self.config.get("channels", {}).get("email", {}).get("enabled"):
                email_config = self.config["channels"]["email"]
                self.email = EmailNotifier(
                    smtp_server=email_config["smtp_server"],
                    smtp_port=email_config["port"],
                    username=email_config["username"],
                    password=email_config["password"],
                    use_tls=email_config.get("use_tls", True)
                )
                self.logger.info("邮件通知器初始化成功")
                
        except Exception as e:
            self.logger.error(f"初始化通知器失败: {e}")
    
    async def execute_notify(self, command: NotifyCommand) -> Dict[str, Any]:
        """
        执行通知命令（纯执行，不做判断）
        
        Args:
            command: 通知命令
            
        Returns:
            执行结果
        """
        results = []
        channel = command.channel.lower()
        
        try:
            if channel == "telegram" and self.telegram:
                if command.attachments:
                    # 有附件，判断类型
                    for attachment in command.attachments:
                        if attachment.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            result = await self.telegram.send_photo(
                                attachment, command.message
                            )
                        else:
                            result = await self.telegram.send_document(
                                attachment, command.message
                            )
                        results.append(result)
                else:
                    # 纯文本消息
                    parse_mode = "HTML" if command.format == "html" else "Markdown" if command.format == "markdown" else None
                    result = await self.telegram.send_message(
                        command.message, parse_mode=parse_mode
                    )
                    results.append(result)
                    
            elif channel == "email" and self.email:
                if command.format == "html":
                    result = await self.email.send_html_email(
                        to=self.config["channels"]["email"]["default_to"],
                        subject="通知",
                        html=command.message,
                        attachments=command.attachments
                    )
                else:
                    result = await self.email.send_email(
                        to=self.config["channels"]["email"]["default_to"],
                        subject="通知", 
                        body=command.message,
                        attachments=command.attachments
                    )
                results.append(result)
                
            elif channel == "terminal":
                result = self.terminal.print_message(command.message)
                results.append(result)
                
            elif channel == "all":
                # 发送到所有启用的渠道
                if self.telegram:
                    result = await self.telegram.send_message(command.message)
                    results.append(result)
                if self.email:
                    result = await self.email.send_email(
                        to=self.config["channels"]["email"]["default_to"],
                        subject="通知",
                        body=command.message
                    )
                    results.append(result)
                
                result = self.terminal.print_message(command.message)
                results.append(result)
            
            else:
                return {
                    "status": "failed",
                    "error": f"未知渠道或渠道未启用: {channel}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 更新统计
            self.stats["by_channel"][channel] += 1
            self.stats["by_type"]["notify"] += 1
            
            return {
                "status": "success",
                "channel": channel,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"执行通知失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_report(self, command: ReportCommand) -> Dict[str, Any]:
        """
        执行报告生成命令
        
        Args:
            command: 报告命令
            
        Returns:
            执行结果
        """
        try:
            report_type = command.report_type.lower()
            
            if report_type == "daily":
                result = self.report_generator.generate_daily_report(
                    data=command.data,
                    format=command.format
                )
            elif report_type == "trade":
                result = self.report_generator.generate_trade_report(
                    trades=command.data.get("trades", []),
                    format=command.format
                )
            elif report_type == "custom":
                output_filename = command.output_filename or f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{command.format}"
                result = self.report_generator.generate_custom_report(
                    template_name=command.data.get("template", "default"),
                    data=command.data,
                    output_filename=output_filename,
                    format=command.format
                )
            else:
                return {
                    "status": "failed",
                    "error": f"未知报告类型: {report_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 更新统计
            self.stats["by_type"]["report"] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行报告生成失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_batch(self, command: BatchCommand) -> List[Dict[str, Any]]:
        """
        执行批量命令
        
        Args:
            command: 批量命令
            
        Returns:
            执行结果列表
        """
        results = []
        
        for cmd_data in command.commands:
            try:
                cmd_type = cmd_data.get("action", "notify")
                
                if cmd_type == "notify":
                    cmd = NotifyCommand(**cmd_data)
                    result = await self.execute_notify(cmd)
                elif cmd_type == "generate_report":
                    cmd = ReportCommand(**cmd_data)
                    result = await self.execute_report(cmd)
                else:
                    result = {
                        "status": "failed",
                        "error": f"未知命令类型: {cmd_type}"
                    }
                
                results.append(result)
                
                # 避免过快发送
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results.append({
                    "status": "failed",
                    "error": str(e),
                    "command_index": len(results)
                })
        
        # 更新统计
        self.stats["by_type"]["batch"] += 1
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        component_stats = {
            "telegram": self.telegram.get_stats() if self.telegram else {},
            "email": self.email.get_stats() if self.email else {},
            "terminal": self.terminal.get_stats(),
            "report_generator": self.report_generator.get_stats()
        }
        
        return {
            "overall": self.stats,
            "components": component_stats,
            "uptime": datetime.now().isoformat()
        }


# FastAPI应用
app = FastAPI(
    title="Window 8 - 纯通知执行工具",
    description="只负责执行Window 6的通知命令，不做任何判断",
    version="8.1"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局通知器实例
notifier = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global notifier
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化通知器
    config_path = Path("config/window8.json")
    if not config_path.exists():
        # 创建默认配置
        config_path.parent.mkdir(exist_ok=True)
        default_config = {
            "channels": {
                "telegram": {
                    "enabled": False,
                    "bot_token": "YOUR_BOT_TOKEN",
                    "chat_id": "YOUR_CHAT_ID"
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "port": 587,
                    "username": "your_email@gmail.com",
                    "password": "your_password",
                    "use_tls": True,
                    "default_to": "recipient@gmail.com"
                },
                "terminal": {
                    "enabled": True,
                    "colored_output": True
                }
            },
            "reports": {
                "output_dir": "./reports",
                "cleanup_days": 7
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    notifier = Window8Notifier(str(config_path))
    logging.info("Window 8 通知系统启动完成")


@app.post("/notify")
async def notify_endpoint(command: NotifyCommand):
    """通知接口"""
    global notifier
    if not notifier:
        raise HTTPException(status_code=500, detail="通知器未初始化")
    
    notifier.stats["total_commands"] += 1
    
    result = await notifier.execute_notify(command)
    
    if result["status"] == "success":
        notifier.stats["successful"] += 1
    else:
        notifier.stats["failed"] += 1
    
    return result


@app.post("/generate_report")
async def report_endpoint(command: ReportCommand):
    """报告生成接口"""
    global notifier
    if not notifier:
        raise HTTPException(status_code=500, detail="通知器未初始化")
    
    notifier.stats["total_commands"] += 1
    
    result = await notifier.execute_report(command)
    
    if result["status"] == "success":
        notifier.stats["successful"] += 1
    else:
        notifier.stats["failed"] += 1
    
    return result


@app.post("/batch")
async def batch_endpoint(command: BatchCommand):
    """批量执行接口"""
    global notifier
    if not notifier:
        raise HTTPException(status_code=500, detail="通知器未初始化")
    
    notifier.stats["total_commands"] += 1
    
    results = await notifier.execute_batch(command)
    
    # 统计成功/失败
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    
    notifier.stats["successful"] += successful
    notifier.stats["failed"] += failed
    
    return {
        "status": "completed",
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "results": results
    }


@app.get("/stats")
async def stats_endpoint():
    """统计信息接口"""
    global notifier
    if not notifier:
        raise HTTPException(status_code=500, detail="通知器未初始化")
    
    return notifier.get_stats()


@app.get("/health")
async def health_endpoint():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "Window 8 Notifier",
        "version": "8.1",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # 直接运行服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )