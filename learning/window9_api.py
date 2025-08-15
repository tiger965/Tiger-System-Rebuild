"""
Window 9 API接口 - 学习工具API服务
提供所有学习工具的HTTP API接口
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import uvicorn

from thinking_recorder import ThinkingRecorder
from external_signal_learning import ExternalSignalLearning
from black_swan_learning import BlackSwanLearning
from prompt_evolution import PromptEvolution
from decision_tracker import DecisionTracker


# 创建FastAPI应用
app = FastAPI(
    title="Window 9 Learning API",
    description="Tiger系统学习工具API接口",
    version="9.1"
)

# 初始化所有学习工具
thinking_recorder = ThinkingRecorder()
signal_learning = ExternalSignalLearning()
black_swan = BlackSwanLearning()
prompt_evolution = PromptEvolution()
decision_tracker = DecisionTracker()


# Pydantic模型定义
class ThinkingData(BaseModel):
    decision_id: str
    thinking_chain: List[Dict]


class SignalData(BaseModel):
    source: str
    type: str
    prediction: Dict
    confidence: float = 0.5
    symbol: str = ""
    timeframe: str = "1h"
    metadata: Dict = {}


class SignalOutcome(BaseModel):
    actual_direction: Optional[str] = None
    actual_price: Optional[float] = None
    actual_risk_realized: Optional[bool] = None


class DecisionData(BaseModel):
    symbol: str
    action: str
    confidence: float = 0.5
    position_size: float = 0
    entry_price: float = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: Dict = {}
    market_conditions: Dict = {}
    signals_used: List[str] = []
    metadata: Dict = {}


class DecisionResult(BaseModel):
    result: str
    exit_price: float = 0
    exit_time: Optional[str] = None


class PerformanceData(BaseModel):
    performance_data: Dict[str, Dict]


# 思考过程记录API
@app.post("/learn/record_thinking")
async def record_thinking(thinking_data: ThinkingData):
    """记录AI思考过程"""
    try:
        result = thinking_recorder.record_thinking_process(
            thinking_data.decision_id,
            thinking_data.thinking_chain
        )
        return {
            "success": True,
            "decision_id": result["decision_id"],
            "confidence": result["confidence"],
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/recent_thoughts")
async def get_recent_thoughts(limit: int = 10):
    """获取最近的思考记录"""
    try:
        records = thinking_recorder.get_recent_thoughts(limit)
        return {
            "success": True,
            "count": len(records),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/thinking_patterns")
async def get_thinking_patterns():
    """分析思考模式"""
    try:
        analysis = thinking_recorder.analyze_thinking_patterns()
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 外部信号学习API
@app.post("/learn/track_signal")
async def track_signal(signal_data: SignalData):
    """追踪外部信号"""
    try:
        signal_dict = signal_data.dict()
        signal_id = signal_learning.track_signal(signal_dict)
        return {
            "success": True,
            "signal_id": signal_id,
            "message": "信号追踪已开始"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn/update_signal_accuracy/{signal_id}")
async def update_signal_accuracy(signal_id: str, outcome: SignalOutcome):
    """更新信号准确率"""
    try:
        result = signal_learning.update_signal_outcome(signal_id, outcome.dict())
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/source_performance/{source}")
async def get_source_performance(source: str):
    """获取特定来源的表现"""
    try:
        performance = signal_learning.get_source_performance(source)
        return {
            "success": True,
            "performance": performance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/best_sources")
async def get_best_sources(min_signals: int = 10):
    """获取表现最好的信号源"""
    try:
        sources = signal_learning.get_best_performing_sources(min_signals)
        return {
            "success": True,
            "best_sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 黑天鹅分析API
@app.post("/learn/analyze_black_swan")
async def analyze_black_swan(current_signals: List[str]):
    """分析黑天鹅相似度"""
    try:
        similarities = black_swan.analyze_current_vs_historical(current_signals)
        return {
            "success": True,
            "similarities": similarities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn/generate_risk_report")
async def generate_risk_report(current_signals: List[str]):
    """生成风险报告"""
    try:
        report = black_swan.generate_risk_report(current_signals)
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn/add_black_swan_event")
async def add_black_swan_event(event_data: Dict):
    """添加新的黑天鹅事件"""
    try:
        success = black_swan.learn_from_new_event(event_data)
        return {
            "success": success,
            "message": "新事件已添加到学习库" if success else "添加失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 提示词进化API
@app.post("/learn/evolve_weights")
async def evolve_weights(performance_data: PerformanceData):
    """进化权重"""
    try:
        result = prompt_evolution.evolve_weights(performance_data.performance_data)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/get_evolved_weights")
async def get_evolved_weights():
    """获取进化后的权重"""
    try:
        weights = prompt_evolution.current_weights
        return {
            "success": True,
            "weights": weights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/generate_evolved_prompt")
async def generate_evolved_prompt():
    """生成进化后的提示词"""
    try:
        prompt = prompt_evolution.generate_evolved_prompt()
        return {
            "success": True,
            "prompt": prompt,
            "length": len(prompt)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/weight_recommendations")
async def get_weight_recommendations(market_condition: str = "normal"):
    """获取权重建议"""
    try:
        recommendations = prompt_evolution.get_weight_recommendations(market_condition)
        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/weight_analysis")
async def get_weight_analysis():
    """分析权重表现"""
    try:
        analysis = prompt_evolution.analyze_weight_performance()
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 决策追踪API
@app.post("/learn/record_decision")
async def record_decision(decision_data: DecisionData):
    """记录决策"""
    try:
        decision_dict = decision_data.dict()
        decision_id = decision_tracker.record_decision(decision_dict)
        return {
            "success": True,
            "decision_id": decision_id,
            "message": "决策记录已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/learn/update_decision/{decision_id}")
async def update_decision(decision_id: str, result: DecisionResult):
    """更新决策结果"""
    try:
        updated_decision = decision_tracker.update_decision_result(decision_id, result.dict())
        return {
            "success": True,
            "decision": updated_decision
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/success_patterns")
async def get_success_patterns():
    """获取成功模式分析"""
    try:
        analysis = decision_tracker.analyze_success_patterns()
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/failure_patterns")
async def get_failure_patterns():
    """获取失败模式分析"""
    try:
        analysis = decision_tracker.analyze_failure_patterns()
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/performance_metrics")
async def get_performance_metrics(period_days: int = 30):
    """获取性能指标"""
    try:
        metrics = decision_tracker.get_performance_metrics(period_days)
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 综合API
@app.get("/learn/learning_report")
async def get_learning_report():
    """生成综合学习报告"""
    try:
        # 收集各组件的数据
        thinking_analysis = thinking_recorder.analyze_thinking_patterns()
        signal_report = signal_learning.generate_learning_report()
        weight_analysis = prompt_evolution.analyze_weight_performance()
        success_patterns = decision_tracker.analyze_success_patterns()
        failure_patterns = decision_tracker.analyze_failure_patterns()
        performance_metrics = decision_tracker.get_performance_metrics(30)
        
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "sections": {
                "thinking_patterns": thinking_analysis,
                "signal_learning": signal_report,
                "weight_evolution": weight_analysis,
                "success_patterns": success_patterns,
                "failure_patterns": failure_patterns,
                "performance_metrics": performance_metrics
            },
            "summary": {
                "total_decisions": performance_metrics.get("total_decisions", 0),
                "success_rate": performance_metrics.get("success_rate", 0),
                "total_pnl": performance_metrics.get("total_pnl", 0),
                "avg_confidence": thinking_analysis.get("average_confidence", 0),
                "signals_tracked": signal_report.get("total_signals_tracked", 0)
            }
        }
        
        return {
            "success": True,
            "report": comprehensive_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/learn/status")
async def get_status():
    """获取系统状态"""
    try:
        status = {
            "service": "Window 9 Learning Tools",
            "version": "9.1",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "thinking_recorder": "active",
                "signal_learning": "active",
                "black_swan_analysis": "active",
                "prompt_evolution": "active",
                "decision_tracker": "active"
            }
        }
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Window 9 Learning Tools API",
        "version": "9.1",
        "description": "Tiger系统学习进化工具箱",
        "endpoints": [
            "/learn/record_thinking",
            "/learn/track_signal",
            "/learn/analyze_black_swan",
            "/learn/evolve_weights",
            "/learn/record_decision",
            "/learn/learning_report",
            "/learn/status",
            "/docs"
        ]
    }


if __name__ == "__main__":
    print("🚀 启动Window 9学习工具API服务...")
    print("📖 API文档地址: http://localhost:8090/docs")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8090,
        reload=True
    )