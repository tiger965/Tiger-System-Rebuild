#!/usr/bin/env python3
"""
Tiger系统 - 监控和运维系统
10号窗口 - 系统监控
"""

import psutil
import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.metrics_history = []
        self.alert_rules = self._init_alert_rules()
        self.alert_history = []
        self.monitoring = False
        
    def _init_alert_rules(self) -> Dict[str, Any]:
        """初始化告警规则"""
        return {
            "high_cpu": {
                "threshold": 80,
                "duration": 60,
                "level": "warning",
                "description": "CPU使用率超过80%"
            },
            "high_memory": {
                "threshold": 85,
                "duration": 60,
                "level": "warning",
                "description": "内存使用率超过85%"
            },
            "disk_space": {
                "threshold": 90,
                "duration": 0,
                "level": "critical",
                "description": "磁盘使用率超过90%"
            },
            "process_down": {
                "level": "critical",
                "description": "关键进程异常"
            },
            "api_failure": {
                "threshold": 5,
                "duration": 300,
                "level": "warning",
                "description": "API失败次数过多"
            }
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "process": {},
            "business": {}
        }
        
        # 系统指标
        metrics["system"]["cpu_percent"] = psutil.cpu_percent(interval=1)
        metrics["system"]["memory"] = {
            "percent": psutil.virtual_memory().percent,
            "used_gb": psutil.virtual_memory().used / (1024**3),
            "available_gb": psutil.virtual_memory().available / (1024**3)
        }
        metrics["system"]["disk"] = {
            "percent": psutil.disk_usage('/').percent,
            "used_gb": psutil.disk_usage('/').used / (1024**3),
            "free_gb": psutil.disk_usage('/').free / (1024**3)
        }
        
        # 网络指标
        net_io = psutil.net_io_counters()
        metrics["system"]["network"] = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
        
        # 进程指标
        current_process = psutil.Process()
        metrics["process"]["pid"] = current_process.pid
        metrics["process"]["cpu_percent"] = current_process.cpu_percent()
        metrics["process"]["memory_mb"] = current_process.memory_info().rss / (1024**2)
        metrics["process"]["num_threads"] = current_process.num_threads()
        
        return metrics
        
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查告警条件"""
        alerts = []
        
        # 检查CPU
        if metrics["system"]["cpu_percent"] > self.alert_rules["high_cpu"]["threshold"]:
            alerts.append({
                "type": "high_cpu",
                "level": self.alert_rules["high_cpu"]["level"],
                "message": f"CPU使用率: {metrics['system']['cpu_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
            
        # 检查内存
        if metrics["system"]["memory"]["percent"] > self.alert_rules["high_memory"]["threshold"]:
            alerts.append({
                "type": "high_memory",
                "level": self.alert_rules["high_memory"]["level"],
                "message": f"内存使用率: {metrics['system']['memory']['percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
            
        # 检查磁盘
        if metrics["system"]["disk"]["percent"] > self.alert_rules["disk_space"]["threshold"]:
            alerts.append({
                "type": "disk_space",
                "level": self.alert_rules["disk_space"]["level"],
                "message": f"磁盘使用率: {metrics['system']['disk']['percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
            
        return alerts
        
    async def monitor_loop(self, interval: int = 60):
        """监控循环"""
        self.monitoring = True
        logger.info("监控系统启动")
        
        while self.monitoring:
            try:
                # 获取指标
                metrics = self.get_system_metrics()
                self.metrics_history.append(metrics)
                
                # 保持历史记录在合理范围
                if len(self.metrics_history) > 1440:  # 保留最近24小时(每分钟一次)
                    self.metrics_history = self.metrics_history[-1440:]
                    
                # 检查告警
                alerts = self.check_alerts(metrics)
                if alerts:
                    for alert in alerts:
                        logger.warning(f"告警: {alert['message']}")
                        self.alert_history.append(alert)
                        
                # 等待下次检查
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控错误: {e}")
                await asyncio.sleep(interval)
                
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        logger.info("监控系统停止")
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics_history:
            return {}
            
        recent_metrics = self.metrics_history[-60:]  # 最近1小时
        
        cpu_values = [m["system"]["cpu_percent"] for m in recent_metrics]
        memory_values = [m["system"]["memory"]["percent"] for m in recent_metrics]
        
        summary = {
            "period": "last_hour",
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "alerts_count": len([a for a in self.alert_history 
                                if datetime.fromisoformat(a["timestamp"]) > 
                                datetime.now() - timedelta(hours=1)])
        }
        
        return summary


class BusinessMonitor:
    """业务监控器"""
    
    def __init__(self):
        """初始化业务监控器"""
        self.metrics = {
            "data_latency": [],
            "signal_count": 0,
            "api_calls": {},
            "error_count": 0,
            "success_rate": 100.0
        }
        
    def record_data_latency(self, latency_ms: float):
        """记录数据延迟"""
        self.metrics["data_latency"].append({
            "value": latency_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持最近1000条记录
        if len(self.metrics["data_latency"]) > 1000:
            self.metrics["data_latency"] = self.metrics["data_latency"][-1000:]
            
    def record_signal(self, signal_type: str):
        """记录信号"""
        self.metrics["signal_count"] += 1
        
    def record_api_call(self, api_name: str, success: bool, duration_ms: float):
        """记录API调用"""
        if api_name not in self.metrics["api_calls"]:
            self.metrics["api_calls"][api_name] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "avg_duration": 0
            }
            
        self.metrics["api_calls"][api_name]["total"] += 1
        if success:
            self.metrics["api_calls"][api_name]["success"] += 1
        else:
            self.metrics["api_calls"][api_name]["failed"] += 1
            self.metrics["error_count"] += 1
            
        # 更新平均响应时间
        current_avg = self.metrics["api_calls"][api_name]["avg_duration"]
        total = self.metrics["api_calls"][api_name]["total"]
        self.metrics["api_calls"][api_name]["avg_duration"] = \
            (current_avg * (total - 1) + duration_ms) / total
            
    def get_business_metrics(self) -> Dict[str, Any]:
        """获取业务指标"""
        # 计算成功率
        total_calls = sum(api["total"] for api in self.metrics["api_calls"].values())
        if total_calls > 0:
            success_calls = sum(api["success"] for api in self.metrics["api_calls"].values())
            self.metrics["success_rate"] = (success_calls / total_calls) * 100
            
        # 计算平均延迟
        if self.metrics["data_latency"]:
            latencies = [d["value"] for d in self.metrics["data_latency"][-100:]]
            avg_latency = sum(latencies) / len(latencies)
        else:
            avg_latency = 0
            
        return {
            "avg_latency_ms": avg_latency,
            "signal_count": self.metrics["signal_count"],
            "error_count": self.metrics["error_count"],
            "success_rate": self.metrics["success_rate"],
            "api_stats": self.metrics["api_calls"]
        }


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志管理器"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 配置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志配置"""
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "json": {
                    "format": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(self.log_dir / "tiger_system.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "standard"
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["file", "console"]
            }
        }
        
        import logging.config
        logging.config.dictConfig(log_config)
        
    def rotate_logs(self):
        """轮转日志"""
        # 获取所有日志文件
        log_files = list(self.log_dir.glob("*.log"))
        
        for log_file in log_files:
            # 检查文件大小
            if log_file.stat().st_size > 50 * 1024 * 1024:  # 50MB
                # 重命名为备份文件
                backup_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                log_file.rename(self.log_dir / backup_name)
                logger.info(f"日志文件轮转: {log_file} -> {backup_name}")
                
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for log_file in self.log_dir.glob("*.log*"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                log_file.unlink()
                logger.info(f"删除旧日志: {log_file}")


class MonitoringDashboard:
    """监控仪表板"""
    
    def __init__(self):
        """初始化仪表板"""
        self.system_monitor = SystemMonitor()
        self.business_monitor = BusinessMonitor()
        self.log_manager = LogManager()
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        # 获取当前指标
        system_metrics = self.system_monitor.get_system_metrics()
        business_metrics = self.business_monitor.get_business_metrics()
        metrics_summary = self.system_monitor.get_metrics_summary()
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": f"{system_metrics['system']['cpu_percent']:.1f}%",
                "memory": f"{system_metrics['system']['memory']['percent']:.1f}%",
                "disk": f"{system_metrics['system']['disk']['percent']:.1f}%"
            },
            "business": {
                "latency": f"{business_metrics['avg_latency_ms']:.2f}ms",
                "signals": business_metrics["signal_count"],
                "errors": business_metrics["error_count"],
                "success_rate": f"{business_metrics['success_rate']:.1f}%"
            },
            "summary": metrics_summary,
            "alerts": len(self.system_monitor.alert_history)
        }
        
        return dashboard
        
    def print_dashboard(self):
        """打印仪表板"""
        data = self.get_dashboard_data()
        
        print("\n" + "=" * 60)
        print("Tiger系统监控仪表板")
        print("=" * 60)
        print(f"时间: {data['timestamp']}")
        print("\n系统指标:")
        print(f"  CPU使用率: {data['system']['cpu']}")
        print(f"  内存使用率: {data['system']['memory']}")
        print(f"  磁盘使用率: {data['system']['disk']}")
        print("\n业务指标:")
        print(f"  平均延迟: {data['business']['latency']}")
        print(f"  信号数量: {data['business']['signals']}")
        print(f"  错误数量: {data['business']['errors']}")
        print(f"  成功率: {data['business']['success_rate']}")
        print(f"\n告警数量: {data['alerts']}")
        print("=" * 60)


async def main():
    """主函数"""
    # 创建监控仪表板
    dashboard = MonitoringDashboard()
    
    # 启动系统监控
    monitor_task = asyncio.create_task(
        dashboard.system_monitor.monitor_loop(interval=10)
    )
    
    try:
        # 模拟业务操作
        for i in range(5):
            # 记录一些业务指标
            dashboard.business_monitor.record_data_latency(50 + i * 10)
            dashboard.business_monitor.record_signal("test_signal")
            dashboard.business_monitor.record_api_call("test_api", True, 100 + i * 5)
            
            # 打印仪表板
            dashboard.print_dashboard()
            
            # 等待
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("收到退出信号")
    finally:
        # 停止监控
        dashboard.system_monitor.stop_monitoring()
        await monitor_task
        
        # 保存最终报告
        report = {
            "final_metrics": dashboard.get_dashboard_data(),
            "alert_history": dashboard.system_monitor.alert_history
        }
        
        with open("monitoring_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info("监控报告已保存")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行监控
    asyncio.run(main())